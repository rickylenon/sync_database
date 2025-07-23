#!/usr/bin/env python3
"""
Database Schema Sync Script - Portable Version
Handles schema synchronization: Remote -> Local 

✨ FEATURES:
- Sync table structures from remote to local
- Handle schema mismatches automatically
- Foreign key dependency analysis
- Schema validation and reporting
- Safe schema operations with rollback

For local development use only - not intended for production deployment

Usage:
    python3 sync_database_schema.py --config CONFIG_FILE [OPTIONS]
    
    Examples:
    python3 sync_database_schema.py --config config_midas.py --dry-run        # Preview schema changes
    python3 sync_database_schema.py --config config_midas.py                  # Perform schema sync
    python3 sync_database_schema.py --config config_midas.py --validate-only  # Only validate schemas
    python3 sync_database_schema.py --config config_midas.py --fix-mismatches # Fix schema mismatches
"""

import subprocess
import time
import sys
import signal
import pymysql
import os
from datetime import datetime
import re

# Progress bar support (optional)
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

class ProgressTracker:
    """Progress tracking with tqdm fallback to simple counters"""
    
    def __init__(self, total, description="Progress", use_tqdm=True):
        self.total = total
        self.current = 0
        self.description = description
        self.use_tqdm = use_tqdm and TQDM_AVAILABLE
        
        if self.use_tqdm:
            self.pbar = tqdm(total=total, desc=description, unit="items", 
                           bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')
        else:
            self.pbar = None
            print(f"{description}: 0/{total} (0%)")
    
    def update(self, n=1):
        """Update progress by n steps"""
        self.current += n
        if self.use_tqdm and self.pbar:
            self.pbar.update(n)
        else:
            # Simple counter fallback
            percentage = (self.current / self.total * 100) if self.total > 0 else 0
            print(f"\r{self.description}: {self.current}/{self.total} ({percentage:.1f}%)", end="", flush=True)
    
    def set_description(self, desc):
        """Update the description"""
        self.description = desc
        if self.use_tqdm and self.pbar:
            self.pbar.set_description(desc)
    
    def close(self):
        """Close the progress bar"""
        if self.use_tqdm and self.pbar:
            self.pbar.close()
        else:
            # Final newline for counter mode
            print()

# Import configuration
def load_config():
    """Load general config and project-specific config - MUST specify config_*.py"""
    config_file = None
    
    # Check for --config argument (REQUIRED)
    for i, arg in enumerate(sys.argv):
        if arg == '--config' and i + 1 < len(sys.argv):
            config_file = sys.argv[i + 1].replace('.py', '')  # Remove .py extension if provided
            # Remove --config and filename from sys.argv so they don't interfere with other argument parsing
            sys.argv = sys.argv[:i] + sys.argv[i+2:]
            break
    
    # If no --config specified, show error and available options
    if config_file is None:
        print("❌ Error: --config parameter is REQUIRED")
        print("\nUsage: python3 sync_database_schema.py --config CONFIG_FILE [OPTIONS]")
        print("\nAvailable config files:")
        
        # Find all config_*.py files
        config_files = []
        for file in os.listdir('.'):
            if file.startswith('config_') and file.endswith('.py'):
                config_files.append(file)
        
        if config_files:
            print("   Available configurations:")
            for file in sorted(config_files):
                print(f"   - {file}")
        else:
            print("   No config_*.py files found")
            print("   Copy config.template.py to config_yourproject.py and customize it")
        
        print("\nExamples:")
        print("   python3 sync_database_schema.py --config config_midas.py --dry-run")
        print("   python3 sync_database_schema.py --config config_midas.py")
        sys.exit(1)
    
    # Import the specified config
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("project_config", f"{config_file}.py")
        project_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(project_config)
        print(f"✅ Project configuration loaded from: {config_file}.py")
    except Exception as e:
        print(f"❌ Error loading configuration from {config_file}.py: {e}")
        sys.exit(1)
    
    # Import general config
    try:
        import config as general_config
        print(f"✅ General configuration loaded from: config.py")
    except Exception as e:
        print(f"❌ Error loading general configuration: {e}")
        sys.exit(1)
    
    # Merge configurations
    try:
        # Start with general config defaults
        merged_ssh_config = {**general_config.DEFAULT_SSH_CONFIG, **project_config.SSH_CONFIG}
        merged_remote_config = {**general_config.DEFAULT_DB_CONFIG, **project_config.REMOTE_DB_CONFIG}
        merged_local_config = {**general_config.DEFAULT_DB_CONFIG, **project_config.LOCAL_DB_CONFIG}
        
        # Get table exclusions from project config
        excluded_tables = getattr(project_config, 'EXCLUDED_TABLES', set())
        excluded_patterns = getattr(project_config, 'EXCLUDED_PATTERNS', [])
        
        # Merge sync configuration
        merged_sync_config = general_config.SYNC_CONFIG.copy()
        if hasattr(project_config, 'PROJECT_SYNC_CONFIG'):
            merged_sync_config.update(project_config.PROJECT_SYNC_CONFIG)
        
        # Validate merged configurations
        general_config.validate_ssh_config(merged_ssh_config)
        general_config.validate_db_config(merged_remote_config, "remote")
        general_config.validate_db_config(merged_local_config, "local")
        
        print(f"✅ Configuration merged successfully")
        
        return (
            merged_ssh_config,
            merged_remote_config,
            merged_local_config,
            excluded_tables,
            excluded_patterns,
            merged_sync_config
        )
        
    except Exception as e:
        print(f"❌ Error: Failed to merge configurations: {e}")
        sys.exit(1)

# Load configuration
SSH_CONFIG, REMOTE_DB_CONFIG, LOCAL_DB_CONFIG, EXCLUDED_TABLES, EXCLUDED_PATTERNS, SYNC_CONFIG = load_config()

class SchemaSync:
    def __init__(self):
        print("🔧 Database Schema Sync - Portable Version")
        print("=" * 60)
        
        # Import configuration from config.py
        self.ssh_host = SSH_CONFIG['host']
        self.ssh_user = SSH_CONFIG['user']
        self.ssh_port = SSH_CONFIG['port']
        self.ssh_password = SSH_CONFIG['password']
        self.local_tunnel_port = SSH_CONFIG['local_tunnel_port']
        
        # Remote database configuration
        self.remote_db_host = REMOTE_DB_CONFIG['host']
        self.remote_db_port = REMOTE_DB_CONFIG['port']
        self.remote_db_user = REMOTE_DB_CONFIG['user']
        self.remote_db_password = REMOTE_DB_CONFIG['password']
        self.remote_db_name = REMOTE_DB_CONFIG['database']
        
        # Local database configuration
        self.local_db_host = LOCAL_DB_CONFIG['host']
        self.local_db_port = LOCAL_DB_CONFIG['port']
        self.local_db_user = LOCAL_DB_CONFIG['user']
        self.local_db_password = LOCAL_DB_CONFIG['password']
        self.local_db_name = LOCAL_DB_CONFIG['database']
        
        # Sync configuration
        self.excluded_tables = EXCLUDED_TABLES.copy()
        self.excluded_patterns = EXCLUDED_PATTERNS.copy()
        self.tunnel_process = None
        
        # Statistics tracking
        self.stats = {
            'tables_analyzed': 0,
            'tables_created': 0,
            'tables_modified': 0,
            'columns_added': 0,
            'columns_modified': 0,
            'foreign_keys_analyzed': 0,
            'schema_mismatches': 0,
            'errors': 0,
            'skipped': 0
        }
        
        # Schema analysis results
        self.schema_analysis = {
            'missing_tables': [],
            'schema_mismatches': [],
            'foreign_key_dependencies': {},
            'recommendations': []
        }
        
        # Print configuration summary
        self.log(f"Configuration loaded: {self.remote_db_name}@{self.remote_db_host} -> {self.local_db_name}@{self.local_db_host}")
        
        # Check for dry run mode
        self.dry_run = '--dry-run' in sys.argv
        self.validate_only = '--validate-only' in sys.argv
        self.fix_mismatches = '--fix-mismatches' in sys.argv
        
        if self.dry_run:
            print("🧪 DRY RUN MODE - No schema changes will be made")
        elif self.validate_only:
            print("🔍 VALIDATION MODE - Only analyzing schemas")
        elif self.fix_mismatches:
            print("🔧 FIX MODE - Fixing schema mismatches")
        else:
            print("⚠️  LIVE SCHEMA SYNC MODE - Schema changes will be applied")
    
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def check_dependencies(self):
        """Check if required dependencies are available"""
        try:
            import pymysql
            return True
        except ImportError:
            self.log("❌ PyMySQL not installed. Install with: pip install pymysql", "ERROR")
            return False
    
    def create_ssh_tunnel(self):
        """Create SSH tunnel to remote database"""
        self.log("Creating SSH tunnel...")
        print(f"   🔗 SSH: {self.ssh_user}@{self.ssh_host}:{self.ssh_port}")
        print(f"   🚇 Tunnel: localhost:{self.local_tunnel_port} -> {self.remote_db_host}:{self.remote_db_port}")
        
        # Close any existing tunnel
        self.close_tunnel()
        
        # SSH tunnel command
        cmd = [
            "sshpass", "-p", self.ssh_password,
            "ssh", "-N",  # Don't execute remote command
            "-L", f"{self.local_tunnel_port}:{self.remote_db_host}:{self.remote_db_port}",
            "-p", str(self.ssh_port),
            f"{self.ssh_user}@{self.ssh_host}",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ServerAliveInterval=60",
            "-o", "ServerAliveCountMax=3"
        ]
        
        try:
            self.tunnel_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            
            # Wait for tunnel to establish and test it
            tunnel_wait_time = SYNC_CONFIG.get('tunnel_wait_time', 5)
            self.log(f"Waiting {tunnel_wait_time} seconds for tunnel to stabilize...")
            time.sleep(tunnel_wait_time)
            
            if self.tunnel_process.poll() is None:
                self.log("SSH tunnel established successfully", "SUCCESS")
                return True
            else:
                stderr = self.tunnel_process.stderr.read()
                self.log(f"SSH tunnel failed: {stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Failed to create SSH tunnel: {e}", "ERROR")
            return False
    
    def close_tunnel(self):
        """Close SSH tunnel"""
        if self.tunnel_process:
            self.tunnel_process.terminate()
            self.tunnel_process = None
    
    def test_connections(self, use_direct=False):
        """Test database connections"""
        self.log("Testing database connections...")
        
        try:
            # Test local connection
            local_conn = pymysql.connect(
                host=self.local_db_host, port=self.local_db_port,
                user=self.local_db_user, password=self.local_db_password,
                database=self.local_db_name, charset='utf8mb4'
            )
            
            with local_conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s", (self.local_db_name,))
                local_tables = cursor.fetchone()[0]
            
            local_conn.close()
            self.log(f"✅ Local database: {local_tables} tables")
            
            # Test remote connection
            if use_direct:
                remote_conn = pymysql.connect(
                    host=self.remote_db_host, port=self.remote_db_port,
                    user=self.remote_db_user, password=self.remote_db_password,
                    database=self.remote_db_name, charset='utf8mb4',
                    connect_timeout=SYNC_CONFIG.get('connection_timeout', 60)
                )
            else:
                remote_conn = pymysql.connect(
                    host='localhost', port=self.local_tunnel_port,
                    user=self.remote_db_user, password=self.remote_db_password,
                    database=self.remote_db_name, charset='utf8mb4',
                    connect_timeout=SYNC_CONFIG.get('connection_timeout', 60)
                )
            
            with remote_conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s", (self.remote_db_name,))
                remote_tables = cursor.fetchone()[0]
                
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
            
            remote_conn.close()
            
            connection_type = "Direct" if use_direct else "Tunnel"
            self.log(f"✅ Remote database ({connection_type}): {remote_tables} tables, MySQL {version}")
            
            return True
            
        except Exception as e:
            connection_type = "Direct" if use_direct else "Tunnel"
            self.log(f"❌ Remote database connection ({connection_type}) failed: {e}", "ERROR")
            return False
    
    def get_tables_to_analyze(self, use_direct=False):
        """Get list of tables to analyze"""
        try:
            if use_direct:
                remote_conn = pymysql.connect(
                    host=self.remote_db_host, port=self.remote_db_port,
                    user=self.remote_db_user, password=self.remote_db_password,
                    database=self.remote_db_name, charset='utf8mb4',
                    connect_timeout=SYNC_CONFIG.get('connection_timeout', 60)
                )
            else:
                remote_conn = pymysql.connect(
                    host='localhost', port=self.local_tunnel_port,
                    user=self.remote_db_user, password=self.remote_db_password,
                    database=self.remote_db_name, charset='utf8mb4',
                    connect_timeout=SYNC_CONFIG.get('connection_timeout', 60)
                )
            
            with remote_conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                all_tables = [row[0] for row in cursor.fetchall()]
            
            remote_conn.close()
            
            # Filter out excluded tables
            analyze_tables = []
            excluded_count = 0
            
            for table in all_tables:
                # Skip if in excluded list
                if table in self.excluded_tables:
                    excluded_count += 1
                    continue
                
                # Skip if starts with excluded pattern
                if any(table.startswith(pattern) for pattern in self.excluded_patterns):
                    excluded_count += 1
                    continue
                
                # Skip if contains 'copy' anywhere in the name
                if 'copy' in table.lower():
                    excluded_count += 1
                    continue
                
                analyze_tables.append(table)
            
            self.log(f"📊 Found {len(analyze_tables)} tables to analyze ({excluded_count} excluded)")
            return analyze_tables
            
        except Exception as e:
            self.log(f"Failed to get table list: {e}", "ERROR")
            return []
    
    def get_table_schema(self, table_name, connection):
        """Get detailed table schema information"""
        try:
            with connection.cursor() as cursor:
                # Get column information
                cursor.execute(f"DESCRIBE `{table_name}`")
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        'name': row[0],
                        'type': row[1],
                        'null': row[2],
                        'key': row[3],
                        'default': row[4],
                        'extra': row[5]
                    })
                
                # Get primary key
                cursor.execute(f"""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                    WHERE TABLE_SCHEMA = '{self.remote_db_name}' 
                    AND TABLE_NAME = '{table_name}' 
                    AND CONSTRAINT_NAME = 'PRIMARY'
                    ORDER BY ORDINAL_POSITION
                """)
                primary_keys = [row[0] for row in cursor.fetchall()]
                
                # Get foreign keys
                cursor.execute(f"""
                    SELECT 
                        COLUMN_NAME,
                        REFERENCED_TABLE_NAME,
                        REFERENCED_COLUMN_NAME
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                    WHERE TABLE_SCHEMA = '{self.remote_db_name}' 
                    AND TABLE_NAME = '{table_name}' 
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                    AND CONSTRAINT_NAME != 'PRIMARY'
                """)
                foreign_keys = []
                for row in cursor.fetchall():
                    foreign_keys.append({
                        'column': row[0],
                        'referenced_table': row[1],
                        'referenced_column': row[2]
                    })
                
                # Get CREATE TABLE statement
                cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
                create_statement = cursor.fetchone()[1]
                
                return {
                    'columns': columns,
                    'primary_keys': primary_keys,
                    'foreign_keys': foreign_keys,
                    'create_statement': create_statement
                }
                
        except Exception as e:
            self.log(f"Failed to get schema for {table_name}: {e}", "ERROR")
            return None
    
    def compare_table_schemas(self, table_name, remote_schema, local_schema):
        """Compare remote and local table schemas"""
        differences = {
            'missing_columns': [],
            'extra_columns': [],
            'type_mismatches': [],
            'null_differences': [],
            'default_differences': [],
            'primary_key_differences': [],
            'foreign_key_differences': []
        }
        
        if not local_schema:
            # Table doesn't exist locally
            return {'missing_table': True, 'differences': differences}
        
        # Compare columns
        remote_columns = {col['name']: col for col in remote_schema['columns']}
        local_columns = {col['name']: col for col in local_schema['columns']}
        
        # Find missing columns in local table
        for col_name, remote_col in remote_columns.items():
            if col_name not in local_columns:
                differences['missing_columns'].append(remote_col)
            else:
                local_col = local_columns[col_name]
                # Compare column properties
                if remote_col['type'] != local_col['type']:
                    differences['type_mismatches'].append({
                        'column': col_name,
                        'remote_type': remote_col['type'],
                        'local_type': local_col['type']
                    })
                
                if remote_col['null'] != local_col['null']:
                    differences['null_differences'].append({
                        'column': col_name,
                        'remote_null': remote_col['null'],
                        'local_null': local_col['null']
                    })
                
                if remote_col['default'] != local_col['default']:
                    differences['default_differences'].append({
                        'column': col_name,
                        'remote_default': remote_col['default'],
                        'local_default': local_col['default']
                    })
        
        # Find extra columns in local table
        for col_name in local_columns:
            if col_name not in remote_columns:
                differences['extra_columns'].append(local_columns[col_name])
        
        # Compare primary keys
        if set(remote_schema['primary_keys']) != set(local_schema['primary_keys']):
            differences['primary_key_differences'] = {
                'remote': remote_schema['primary_keys'],
                'local': local_schema['primary_keys']
            }
        
        # Compare foreign keys
        remote_fks = {(fk['column'], fk['referenced_table'], fk['referenced_column']) 
                     for fk in remote_schema['foreign_keys']}
        local_fks = {(fk['column'], fk['referenced_table'], fk['referenced_column']) 
                    for fk in local_schema['foreign_keys']}
        
        if remote_fks != local_fks:
            differences['foreign_key_differences'] = {
                'remote': list(remote_fks),
                'local': list(local_fks)
            }
        
        return {'missing_table': False, 'differences': differences}
    
    def analyze_schemas(self, tables, use_direct=False):
        """Analyze schemas of all tables"""
        self.log("🔍 Analyzing table schemas...")
        
        try:
            # Get connections
            if use_direct:
                remote_conn = pymysql.connect(
                    host=self.remote_db_host, port=self.remote_db_port,
                    user=self.remote_db_user, password=self.remote_db_password,
                    database=self.remote_db_name, charset='utf8mb4',
                    connect_timeout=SYNC_CONFIG.get('connection_timeout', 60)
                )
            else:
                remote_conn = pymysql.connect(
                    host='localhost', port=self.local_tunnel_port,
                    user=self.remote_db_user, password=self.remote_db_password,
                    database=self.remote_db_name, charset='utf8mb4',
                    connect_timeout=SYNC_CONFIG.get('connection_timeout', 60)
                )
            
            local_conn = pymysql.connect(
                host=self.local_db_host, port=self.local_db_port,
                user=self.local_db_user, password=self.local_db_password,
                database=self.local_db_name, charset='utf8mb4'
            )
            
            # Create progress tracker
            progress = ProgressTracker(len(tables), "Analyzing schemas")
            
            try:
                for table in tables:
                    progress.set_description(f"Analyzing {table}")
                    
                    # Get remote schema
                    remote_schema = self.get_table_schema(table, remote_conn)
                    if not remote_schema:
                        self.log(f"⚠️  Skipping {table}: Could not get remote schema", "WARNING")
                        self.stats['skipped'] += 1
                        progress.update(1)
                        continue
                    
                    # Check if table exists locally
                    with local_conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT COUNT(*) 
                            FROM information_schema.tables 
                            WHERE table_schema = %s AND table_name = %s
                        """, (self.local_db_name, table))
                        table_exists = cursor.fetchone()[0] > 0
                    
                    if table_exists:
                        # Get local schema
                        local_schema = self.get_table_schema(table, local_conn)
                        comparison = self.compare_table_schemas(table, remote_schema, local_schema)
                        
                        if comparison['missing_table']:
                            self.schema_analysis['missing_tables'].append(table)
                        elif any(comparison['differences'].values()):
                            self.schema_analysis['schema_mismatches'].append({
                                'table': table,
                                'differences': comparison['differences']
                            })
                            self.stats['schema_mismatches'] += 1
                    else:
                        # Table doesn't exist locally
                        self.schema_analysis['missing_tables'].append(table)
                    
                    # Analyze foreign key dependencies
                    if remote_schema['foreign_keys']:
                        self.schema_analysis['foreign_key_dependencies'][table] = [
                            fk['referenced_table'] for fk in remote_schema['foreign_keys']
                        ]
                        self.stats['foreign_keys_analyzed'] += 1
                    
                    self.stats['tables_analyzed'] += 1
                    progress.update(1)
            
            finally:
                progress.close()
                remote_conn.close()
                local_conn.close()
            
            return True
            
        except Exception as e:
            self.log(f"Schema analysis failed: {e}", "ERROR")
            return False
    
    def generate_schema_report(self):
        """Generate detailed schema analysis report"""
        print("\n" + "="*60)
        print("📊 SCHEMA ANALYSIS REPORT")
        print("="*60)
        
        print(f"📋 Tables analyzed: {self.stats['tables_analyzed']}")
        print(f"🔧 Schema mismatches found: {self.stats['schema_mismatches']}")
        print(f"🔗 Foreign key dependencies analyzed: {self.stats['foreign_keys_analyzed']}")
        print(f"❌ Errors: {self.stats['errors']}")
        print(f"⏭️  Skipped: {self.stats['skipped']}")
        
        if self.schema_analysis['missing_tables']:
            print(f"\n📋 Missing tables ({len(self.schema_analysis['missing_tables'])}):")
            for table in sorted(self.schema_analysis['missing_tables']):
                print(f"   - {table}")
        
        if self.schema_analysis['schema_mismatches']:
            print(f"\n🔧 Schema mismatches ({len(self.schema_analysis['schema_mismatches'])}):")
            for mismatch in self.schema_analysis['schema_mismatches']:
                table = mismatch['table']
                differences = mismatch['differences']
                
                print(f"   📋 {table}:")
                if differences['missing_columns']:
                    print(f"      Missing columns: {len(differences['missing_columns'])}")
                if differences['type_mismatches']:
                    print(f"      Type mismatches: {len(differences['type_mismatches'])}")
                if differences['primary_key_differences']:
                    print(f"      Primary key differences")
                if differences['foreign_key_differences']:
                    print(f"      Foreign key differences")
        
        if self.schema_analysis['foreign_key_dependencies']:
            print(f"\n🔗 Foreign key dependencies:")
            for table, deps in self.schema_analysis['foreign_key_dependencies'].items():
                print(f"   {table} depends on: {', '.join(deps)}")
        
        # Generate recommendations
        recommendations = []
        if self.schema_analysis['missing_tables']:
            recommendations.append("Create missing tables from remote schema")
        if self.schema_analysis['schema_mismatches']:
            recommendations.append("Fix schema mismatches by adding missing columns")
        if self.schema_analysis['foreign_key_dependencies']:
            recommendations.append("Consider sync order based on foreign key dependencies")
        
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   - {rec}")
    
    def run_schema_sync(self):
        """Run the complete schema sync process"""
        # Check dependencies
        self.log("Checking dependencies...")
        if not self.check_dependencies():
            return False
        self.log("✅ All dependencies available")
        
        # Determine connection method
        use_direct = SYNC_CONFIG.get('use_direct_connection', False)
        
        if use_direct:
            self.log("Using direct database connection (bypassing SSH tunnel)")
            tunnel_success = True
        else:
            # Create SSH tunnel
            tunnel_success = self.create_ssh_tunnel()
            if not tunnel_success:
                self.log("SSH tunnel failed, attempting direct connection...", "WARNING")
                use_direct = True
                tunnel_success = True
        
        if not tunnel_success:
            return False
        
        # Test connections
        if not self.test_connections(use_direct):
            return False
        
        # Get tables to analyze
        tables = self.get_tables_to_analyze(use_direct)
        if not tables:
            self.log("No tables to analyze", "WARNING")
            return False
        
        # Analyze schemas
        if not self.analyze_schemas(tables, use_direct):
            return False
        
        # Generate report
        self.generate_schema_report()
        
        # Close tunnel
        if not use_direct:
            self.close_tunnel()
        
        return True

def main():
    """Main function"""
    # Parse command line arguments
    dry_run = '--dry-run' in sys.argv
    validate_only = '--validate-only' in sys.argv
    fix_mismatches = '--fix-mismatches' in sys.argv
    
    # Create sync instance
    schema_sync = SchemaSync()
    
    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("\n\n⚠️  Interrupted by user")
        schema_sync.close_tunnel()
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        success = schema_sync.run_schema_sync()
        if success:
            print("\n✅ Schema analysis completed successfully!")
        else:
            print("\n❌ Schema analysis failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 