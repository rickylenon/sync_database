#!/usr/bin/env python3
"""
Database Sync Script - Portable Version
Performs one-way sync: Remote -> Local 

✨ NEW: Automatically creates tables that exist remotely but not locally!

Sync Modes:
    INCREMENTAL (default): INSERT new, UPDATE changed, DELETE removed records
                          + CREATE missing tables from remote schema
    DROP/RECREATE: Drop tables and recreate with fresh data (faster for large changes)

For local development use only - not intended for production deployment

Usage:
    python3 sync_database.py --config CONFIG_FILE [OPTIONS]
    
    Examples:
    python3 sync_database.py --config config_midas.py --dry-run        # Preview changes
    python3 sync_database.py --config config_midas.py                  # Perform incremental sync
    python3 sync_database.py --config config_midas.py --drop-recreate  # Use drop/recreate mode
    python3 sync_database.py --config config_nexportal.py --dry-run    # Preview with different config

Configuration:
    1. Copy config.template.py to config_yourproject.py
    2. Edit config_yourproject.py to customize database connections, SSH settings, excluded tables, and sync mode
    3. Add config_*.py to .gitignore to prevent committing credentials
    4. Always specify config file with --config parameter
"""

import subprocess
import time
import sys
import signal
import pymysql
import os
from datetime import datetime

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
        print("❌ Error: Configuration file must be specified!")
        print("")
        print("Usage: python sync_database.py --config CONFIG_FILE [OPTIONS]")
        print("")
        
        # Look for available config files
        import glob
        config_files = glob.glob('config_*.py')
        if config_files:
            print("Available configuration files:")
            for cf in sorted(config_files):
                print(f"  python sync_database.py --config {cf} --dry-run")
        else:
            print("No config_*.py files found. Create one by:")
            print("  1. Copy config.template.py to config_yourproject.py")
            print("  2. Edit config_yourproject.py with your database settings")
            print("  3. Run: python sync_database.py --config config_yourproject.py --dry-run")
        
        print("")
        print("Examples:")
        print("  python sync_database.py --config config_midas.py --dry-run")
        print("  python sync_database.py --config config_nexportal.py --dry-run")
        sys.exit(1)
    
    # Validate config file name format
    if not config_file.startswith('config_'):
        print(f"❌ Error: Configuration file must follow 'config_*.py' naming pattern")
        print(f"   Given: {config_file}.py")
        print(f"   Expected: config_yourproject.py")
        print("")
        print("Examples of valid config files:")
        print("  config_midas.py")
        print("  config_nexportal.py") 
        print("  config_myproject.py")
        sys.exit(1)
    
    # Load general configuration
    try:
        general_config = __import__('config')
        print(f"✅ General configuration loaded from: config.py")
    except ImportError as e:
        print(f"❌ Error: Could not load general configuration file 'config.py'")
        print(f"   Import error: {e}")
        print("")
        print("Make sure config.py exists with general application settings.")
        sys.exit(1)
    
    # Load project-specific configuration
    try:
        project_config = __import__(config_file)
        print(f"✅ Project configuration loaded from: {config_file}.py")
    except ImportError as e:
        print(f"❌ Error: Could not load project configuration file '{config_file}.py'")
        print(f"   Import error: {e}")
        print("")
        print("Make sure the file exists and contains valid Python configuration.")
        print("You can create it by copying config.template.py:")
        print(f"   cp config.template.py {config_file}.py")
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

class DatabaseSync:
    def __init__(self):
        print("🚀 Database Sync - Portable Version")
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
        self.excluded_tables = EXCLUDED_TABLES.copy()  # Create a copy to allow modifications
        self.excluded_patterns = EXCLUDED_PATTERNS.copy()
        self.tunnel_process = None
        
        # Statistics tracking
        self.stats = {
            'tables_synced': 0,
            'tables_dropped': 0,
            'tables_created': 0,
            'records_inserted': 0,
            'records_updated': 0,
            'records_deleted': 0,
            'errors': 0,
            'skipped': 0
        }
        
        # Print configuration summary
        self.log(f"Configuration loaded: {self.remote_db_name}@{self.remote_db_host} -> {self.local_db_name}@{self.local_db_host}")
        
    def log(self, message, level="INFO"):
        """Log message with timestamp and color"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "\033[0;32m",    # Green
            "WARNING": "\033[1;33m", # Yellow
            "ERROR": "\033[0;31m",   # Red
            "SUCCESS": "\033[1;32m"  # Bright Green
        }
        color = colors.get(level, "\033[0m")
        reset = "\033[0m"
        print(f"{color}[{timestamp}] {level}: {message}{reset}")
        
    def check_dependencies(self):
        """Check if required dependencies are available"""
        try:
            import pymysql
        except ImportError:
            self.log("PyMySQL not found. Install with: pip install pymysql", "ERROR")
            return False
            
        # Check if sshpass is available
        try:
            subprocess.run(["sshpass", "-V"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("sshpass not found. Install with: brew install sshpass (macOS) or apt-get install sshpass (Linux)", "ERROR")
            return False
            
        return True
        
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
    
    def test_connections_method(self, use_direct=False):
        """Test both local and remote database connections with specified method"""
        self.log("Testing database connections...")
        
        # Test local connection
        try:
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
            
        except Exception as e:
            self.log(f"❌ Local database connection failed: {e}", "ERROR")
            return False
        
        # Test remote connection
        try:
            if use_direct:
                remote_conn = pymysql.connect(
                    host=self.remote_db_host, port=self.remote_db_port,
                    user=self.remote_db_user, password=self.remote_db_password,
                    database=self.remote_db_name, charset='utf8mb4',
                    connect_timeout=SYNC_CONFIG.get('connection_timeout', 60),
                    read_timeout=SYNC_CONFIG.get('mysql_read_timeout', 120),
                    write_timeout=SYNC_CONFIG.get('mysql_write_timeout', 120),
                    autocommit=False
                )
            else:
                remote_conn = pymysql.connect(
                    host='localhost', port=self.local_tunnel_port,
                    user=self.remote_db_user, password=self.remote_db_password,
                    database=self.remote_db_name, charset='utf8mb4',
                    connect_timeout=SYNC_CONFIG.get('connection_timeout', 60),
                    read_timeout=SYNC_CONFIG.get('mysql_read_timeout', 120),
                    write_timeout=SYNC_CONFIG.get('mysql_write_timeout', 120),
                    autocommit=False
                )
            
            with remote_conn.cursor() as cursor:
                # Test basic connection
                self.log(f"Testing remote connection to {self.remote_db_name}...")
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                
                # Test database access
                cursor.execute("SELECT DATABASE()")
                current_db = cursor.fetchone()[0]
                self.log(f"Connected to database: {current_db}")
                
                # Count tables with timeout protection
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s", (self.remote_db_name,))
                remote_tables = cursor.fetchone()[0]
            
            remote_conn.close()
            connection_type = "Direct" if use_direct else "Tunnel"
            self.log(f"✅ Remote database ({connection_type}): {remote_tables} tables, MySQL {version}")
            
            return True
            
        except Exception as e:
            connection_type = "Direct" if use_direct else "Tunnel"
            self.log(f"❌ Remote database connection ({connection_type}) failed: {e}", "ERROR")
            return False

    def get_sync_tables_method(self, use_direct=False):
        """Get list of tables to sync with specified connection method"""
        try:
            if use_direct:
                remote_conn = pymysql.connect(
                    host=self.remote_db_host, port=self.remote_db_port,
                    user=self.remote_db_user, password=self.remote_db_password,
                    database=self.remote_db_name, charset='utf8mb4',
                    connect_timeout=SYNC_CONFIG.get('connection_timeout', 60),
                    read_timeout=SYNC_CONFIG.get('mysql_read_timeout', 120),
                    write_timeout=SYNC_CONFIG.get('mysql_write_timeout', 120)
                )
            else:
                remote_conn = pymysql.connect(
                    host='localhost', port=self.local_tunnel_port,
                    user=self.remote_db_user, password=self.remote_db_password,
                    database=self.remote_db_name, charset='utf8mb4',
                    connect_timeout=SYNC_CONFIG.get('connection_timeout', 60),
                    read_timeout=SYNC_CONFIG.get('mysql_read_timeout', 120),
                    write_timeout=SYNC_CONFIG.get('mysql_write_timeout', 120)
                )
            
            with remote_conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                all_tables = [row[0] for row in cursor.fetchall()]
            
            remote_conn.close()
            
            # Filter out excluded tables
            sync_tables = []
            excluded_count = 0
            
            for table in all_tables:
                # Skip if in excluded list
                if table in self.excluded_tables:
                    excluded_count += 1
                    continue
                
                # Skip if starts with excluded pattern or contains 'copy'
                if any(table.startswith(pattern) for pattern in self.excluded_patterns if pattern != 'copy'):
                    excluded_count += 1
                    continue
                
                # Skip if contains 'copy' anywhere in the name
                if 'copy' in table.lower():
                    excluded_count += 1
                    continue
                
                sync_tables.append(table)
            
            self.log(f"📊 Found {len(sync_tables)} tables to sync ({excluded_count} excluded)")
            return sync_tables
            
        except Exception as e:
            self.log(f"Failed to get table list: {e}", "ERROR")
            return []
    
    def get_table_primary_key(self, table_name, connection):
        """Get primary key columns for a table"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                    WHERE TABLE_SCHEMA = '{self.remote_db_name}' 
                    AND TABLE_NAME = '{table_name}' 
                    AND CONSTRAINT_NAME = 'PRIMARY'
                    ORDER BY ORDINAL_POSITION
                """)
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.log(f"Failed to get primary key for {table_name}: {e}", "ERROR")
            return []
    
    def get_table_create_statement(self, table_name, connection):
        """Get CREATE TABLE statement for a table from remote database"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
                result = cursor.fetchone()
                if result:
                    return result[1]  # The CREATE TABLE statement
                return None
        except Exception as e:
            self.log(f"Failed to get CREATE statement for {table_name}: {e}", "ERROR")
            return None
    
    def table_exists_locally(self, table_name, local_conn):
        """Check if a table exists in the local database"""
        try:
            with local_conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = %s
                """, (self.local_db_name, table_name))
                return cursor.fetchone()[0] > 0
        except Exception as e:
            self.log(f"Failed to check if table {table_name} exists locally: {e}", "ERROR")
            return False
    
    def create_table_from_remote(self, table_name, local_conn, remote_conn, dry_run=False):
        """Create a table in local database using schema from remote"""
        try:
            # Get the CREATE TABLE statement from remote
            create_statement = self.get_table_create_statement(table_name, remote_conn)
            if not create_statement:
                self.log(f"⚠️  Cannot create {table_name}: Could not get CREATE statement from remote", "WARNING")
                return False
            
            # Get record count from remote for logging
            with remote_conn.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                remote_count = cursor.fetchone()[0]
            
            self.log(f"🆕 {table_name}: Creating new table (will contain {remote_count:,} records)")
            
            if dry_run:
                return True
            
            with local_conn.cursor() as cursor:
                # Create table with remote structure
                cursor.execute(create_statement)
                self.log(f"  ✅ Created table {table_name} with remote schema")
                self.stats['tables_created'] += 1
                
            local_conn.commit()
            return True
            
        except Exception as e:
            self.log(f"❌ Error creating table {table_name}: {e}", "ERROR")
            self.stats['errors'] += 1
            if not dry_run:
                local_conn.rollback()
            return False
    
    def drop_recreate_table(self, table_name, local_conn, remote_conn, dry_run=False):
        """Drop and recreate a table with fresh data from remote"""
        try:
            # Get the CREATE TABLE statement from remote
            create_statement = self.get_table_create_statement(table_name, remote_conn)
            if not create_statement:
                self.log(f"⚠️  Skipping {table_name}: Could not get CREATE statement", "WARNING")
                self.stats['skipped'] += 1
                return
            
            # Get record count from remote
            with remote_conn.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                remote_count = cursor.fetchone()[0]
            
            self.log(f"🔄 {table_name}: Will drop/recreate with {remote_count:,} records")
            
            if dry_run:
                return
            
            with local_conn.cursor() as cursor:
                # Disable foreign key checks if configured
                if SYNC_CONFIG.get('disable_foreign_key_checks', True):
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                
                # Drop table if it exists
                cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
                self.log(f"  ✅ Dropped table {table_name}")
                self.stats['tables_dropped'] += 1
                
                # Create table with remote structure
                cursor.execute(create_statement)
                self.log(f"  ✅ Created table {table_name}")
                self.stats['tables_created'] += 1
                
                # Copy all data from remote if there are records
                if remote_count > 0:
                    # Get all data from remote
                    with remote_conn.cursor() as remote_cursor:
                        remote_cursor.execute(f"SELECT * FROM `{table_name}`")
                        
                        # Process in batches for large tables
                        batch_size = 1000
                        inserted_count = 0
                        
                        while True:
                            rows = remote_cursor.fetchmany(batch_size)
                            if not rows:
                                break
                            
                            # Get column names from first row
                            if inserted_count == 0:
                                # Get column names from the remote cursor description
                                columns = [desc[0] for desc in remote_cursor.description]
                                placeholders = ", ".join(["%s"] * len(columns))
                                column_names = ", ".join([f"`{col}`" for col in columns])
                                insert_sql = f"INSERT INTO `{table_name}` ({column_names}) VALUES ({placeholders})"
                            
                            # Insert batch
                            cursor.executemany(insert_sql, rows)
                            inserted_count += len(rows)
                            
                            # Show progress for large tables
                            if inserted_count % 10000 == 0:
                                print(f"    📝 Inserted {inserted_count:,} records...")
                    
                    self.stats['records_inserted'] += inserted_count
                    self.log(f"  ✅ Inserted {inserted_count:,} records into {table_name}")
                else:
                    self.log(f"  ℹ️  {table_name} is empty (no records to copy)")
                
                # Re-enable foreign key checks if they were disabled
                if SYNC_CONFIG.get('disable_foreign_key_checks', True):
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            
            local_conn.commit()
            self.stats['tables_synced'] += 1
            
        except Exception as e:
            self.log(f"❌ Error drop/recreating {table_name}: {e}", "ERROR")
            self.stats['errors'] += 1
            if not dry_run:
                local_conn.rollback()
                # Re-enable foreign key checks on error
                try:
                    with local_conn.cursor() as cursor:
                        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                    local_conn.commit()
                except:
                    pass
    
    def sync_table(self, table_name, local_conn, remote_conn, dry_run=False):
        """Sync a single table using either incremental sync or drop/recreate mode"""
        
        # Check if drop/recreate mode is enabled
        use_drop_recreate = SYNC_CONFIG.get('use_drop_recreate_mode', False)
        
        if use_drop_recreate:
            return self.drop_recreate_table(table_name, local_conn, remote_conn, dry_run)
        
        # Original incremental sync logic
        try:
            # Check if table exists locally - if not, create it
            if not self.table_exists_locally(table_name, local_conn):
                self.log(f"📋 {table_name}: Table doesn't exist locally, creating from remote schema...")
                if not self.create_table_from_remote(table_name, local_conn, remote_conn, dry_run):
                    return  # Skip this table if creation failed
                
                # If dry run, we can't continue with sync since table doesn't actually exist yet
                if dry_run:
                    return
            
            # Get primary key
            pk_columns = self.get_table_primary_key(table_name, remote_conn)
            if not pk_columns:
                self.log(f"⚠️  Skipping {table_name}: No primary key found", "WARNING")
                self.stats['skipped'] += 1
                return
            
            # Get all records from both databases
            with remote_conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(f"SELECT * FROM `{table_name}`")
                remote_records = cursor.fetchall()
            
            with local_conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(f"SELECT * FROM `{table_name}`")
                local_records = cursor.fetchall()
            
            # Create lookup dictionaries using primary key
            def make_key(record, pk_cols):
                if len(pk_cols) == 1:
                    return record[pk_cols[0]]
                return tuple(record[col] for col in pk_cols)
            
            remote_dict = {make_key(r, pk_columns): r for r in remote_records}
            local_dict = {make_key(r, pk_columns): r for r in local_records}
            
            # Find differences
            remote_keys = set(remote_dict.keys())
            local_keys = set(local_dict.keys())
            
            to_insert = remote_keys - local_keys
            to_delete = local_keys - remote_keys
            to_update = []
            
            # Check for updates
            for key in remote_keys & local_keys:
                if remote_dict[key] != local_dict[key]:
                    to_update.append(key)
            
            # Log what would be done
            if to_insert or to_update or to_delete:
                self.log(f"📋 {table_name}: Insert={len(to_insert)}, Update={len(to_update)}, Delete={len(to_delete)}")
            
            if dry_run:
                return
            
            # Perform actual sync operations
            if to_insert or to_update or to_delete:
                with local_conn.cursor() as cursor:
                    # INSERT new records (with foreign key error handling)
                    insert_success = 0
                    for key in to_insert:
                        try:
                            record = remote_dict[key]
                            columns = list(record.keys())
                            values = list(record.values())
                            
                            placeholders = ", ".join(["%s"] * len(values))
                            column_names = ", ".join([f"`{col}`" for col in columns])
                            
                            sql = f"INSERT INTO `{table_name}` ({column_names}) VALUES ({placeholders})"
                            cursor.execute(sql, values)
                            insert_success += 1
                            self.stats['records_inserted'] += 1
                        except Exception as e:
                            if "foreign key constraint" in str(e).lower() or "duplicate entry" in str(e).lower():
                                # Skip foreign key constraint and duplicate key errors but continue
                                continue
                            else:
                                # Re-raise other errors
                                raise e
                    
                    # UPDATE existing records (with foreign key error handling)
                    update_success = 0
                    for key in to_update:
                        try:
                            record = remote_dict[key]
                            
                            # Build SET clause (exclude primary key columns)
                            set_clauses = []
                            values = []
                            for col, val in record.items():
                                if col not in pk_columns:
                                    set_clauses.append(f"`{col}` = %s")
                                    values.append(val)
                            
                            # Build WHERE clause
                            where_clauses = []
                            for col in pk_columns:
                                where_clauses.append(f"`{col}` = %s")
                                values.append(record[col])
                            
                            if set_clauses:  # Only update if there are non-PK columns
                                sql = f"UPDATE `{table_name}` SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
                                cursor.execute(sql, values)
                                update_success += 1
                                self.stats['records_updated'] += 1
                        except Exception as e:
                            if "foreign key constraint" in str(e).lower() or "duplicate entry" in str(e).lower():
                                # Skip foreign key constraint and duplicate key errors but continue
                                continue
                            else:
                                # Re-raise other errors
                                raise e
                    
                    # DELETE removed records (skip if foreign key errors)
                    delete_success = 0
                    delete_skipped = 0
                    for key in to_delete:
                        try:
                            where_clauses = []
                            values = []
                            
                            if isinstance(key, tuple):
                                for i, col in enumerate(pk_columns):
                                    where_clauses.append(f"`{col}` = %s")
                                    values.append(key[i])
                            else:
                                where_clauses.append(f"`{pk_columns[0]}` = %s")
                                values.append(key)
                            
                            sql = f"DELETE FROM `{table_name}` WHERE {' AND '.join(where_clauses)}"
                            cursor.execute(sql, values)
                            delete_success += 1
                            self.stats['records_deleted'] += 1
                        except Exception as e:
                            if "foreign key constraint" in str(e).lower():
                                # Skip foreign key constraint errors for deletions
                                delete_skipped += 1
                                continue
                            else:
                                # Re-raise other errors
                                raise e
                    
                    # Log detailed results for tables with foreign key issues
                    if delete_skipped > 0:
                        self.log(f"  ⚠️  {table_name}: Skipped {delete_skipped} deletions (foreign key constraints)")
                
                local_conn.commit()
                self.stats['tables_synced'] += 1
            
        except Exception as e:
            self.log(f"❌ Error syncing {table_name}: {e}", "ERROR")
            self.stats['errors'] += 1
            if not dry_run:
                local_conn.rollback()
    
    def run_sync(self, dry_run=False):
        """Run the complete sync process"""
        if dry_run:
            print("🧪 DRY RUN MODE - No changes will be made")
        else:
            print("⚠️  LIVE SYNC MODE - Changes will be applied to local database")
        
        print()
        
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
        if not self.test_connections_method(use_direct):
            return False
        
        # Get sync information before asking for confirmation
        sync_tables = self.get_sync_tables_method(use_direct)
        if not sync_tables:
            self.log("No tables to sync", "WARNING")
            return False
        
        # Show detailed sync plan
        connection_method = "Direct RDS" if use_direct else "SSH Tunnel"
        sync_mode = "DROP/RECREATE" if SYNC_CONFIG.get('use_drop_recreate_mode', False) else "INCREMENTAL"
        
        print(f"\n📊 Sync Plan Summary:")
        print(f"   🔗 Connection: {connection_method}")
        if not use_direct:
            print(f"   🚇 SSH Tunnel: {self.ssh_user}@{self.ssh_host}:{self.ssh_port}")
        print(f"   📍 Remote: {self.remote_db_name}@{self.remote_db_host}:{self.remote_db_port}")
        print(f"   📍 Local:  {self.local_db_name}@{self.local_db_host}:{self.local_db_port}")
        print(f"   🔄 Sync Mode: {sync_mode}")
        if sync_mode == "DROP/RECREATE":
            print(f"   ⚠️  WARNING: All local table data will be completely replaced!")
            if SYNC_CONFIG.get('disable_foreign_key_checks', True):
                print(f"   🔧 Foreign key checks will be temporarily disabled")
        print(f"   📋 Tables to sync: {len(sync_tables)}")
        print(f"   🚫 Tables excluded: {len(self.excluded_tables)} explicit + patterns: {self.excluded_patterns}")
        
        # Show excluded tables summary
        if self.excluded_tables:
            excluded_sample = list(self.excluded_tables)[:5]
            if len(self.excluded_tables) <= 5:
                print(f"   🚫 Excluded by name: {', '.join(sorted(excluded_sample))}")
            else:
                print(f"   🚫 Excluded by name: {', '.join(sorted(excluded_sample))}... (+{len(self.excluded_tables)-5} more)")
        
        if len(sync_tables) <= 20:
            # Show table list if not too many
            print(f"   📝 Table list: {', '.join(sorted(sync_tables))}")
        else:
            # Show sample if many tables
            sample_tables = sorted(sync_tables)[:10]
            print(f"   📝 Sample tables: {', '.join(sample_tables)}... (+{len(sync_tables)-10} more)")
        
        # Ask for confirmation AFTER showing all the details
        if not dry_run and SYNC_CONFIG.get('require_confirmation', True):
            print(f"\n⚠️  Ready to sync {len(sync_tables)} tables from remote to local database")
            if SYNC_CONFIG.get('use_drop_recreate_mode', False):
                print("   This will DROP each table and recreate it with fresh data from remote")
                print("   🚨 ALL EXISTING LOCAL DATA IN THESE TABLES WILL BE LOST!")
            else:
                print("   This will INSERT new records, UPDATE existing records, and DELETE removed records")
            response = input("Continue? (y/N): ")
            if response.lower() != 'y':
                print("Sync cancelled by user")
                if not use_direct:
                    self.close_tunnel()
                return False
        
        try:
            # Get database connections
            self.log("Establishing database connections...")
            local_conn = pymysql.connect(
                host=self.local_db_host, port=self.local_db_port,
                user=self.local_db_user, password=self.local_db_password,
                database=self.local_db_name, charset='utf8mb4',
                autocommit=False
            )
            
            if use_direct:
                remote_conn = pymysql.connect(
                    host=self.remote_db_host, port=self.remote_db_port,
                    user=self.remote_db_user, password=self.remote_db_password,
                    database=self.remote_db_name, charset='utf8mb4',
                    connect_timeout=SYNC_CONFIG.get('connection_timeout', 60),
                    read_timeout=SYNC_CONFIG.get('mysql_read_timeout', 120),
                    write_timeout=SYNC_CONFIG.get('mysql_write_timeout', 120),
                    autocommit=False
                )
            else:
                remote_conn = pymysql.connect(
                    host='localhost', port=self.local_tunnel_port,
                    user=self.remote_db_user, password=self.remote_db_password,
                    database=self.remote_db_name, charset='utf8mb4',
                    connect_timeout=SYNC_CONFIG.get('connection_timeout', 60),
                    read_timeout=SYNC_CONFIG.get('mysql_read_timeout', 120),
                    write_timeout=SYNC_CONFIG.get('mysql_write_timeout', 120),
                    autocommit=False
                )
            
            self.log("✅ Database connections established")
            print()
            self.log("Starting table synchronization...")
            
            # Sync each table
            for i, table in enumerate(sync_tables, 1):
                print(f"\n🔄 Progress: {i}/{len(sync_tables)} - {table}")
                self.sync_table(table, local_conn, remote_conn, dry_run)
            
            # Close connections
            local_conn.close()
            remote_conn.close()
            
            # Print final statistics
            print("\n" + "="*60)
            self.log("Synchronization completed!", "SUCCESS")
            print(f"📊 Final Statistics:")
            print(f"   Tables processed: {len(sync_tables)}")
            print(f"   Tables synced: {self.stats['tables_synced']}")
            print(f"   Tables skipped: {self.stats['skipped']}")
            
            # Show drop/recreate specific stats if used
            if SYNC_CONFIG.get('use_drop_recreate_mode', False):
                print(f"   Tables dropped: {self.stats['tables_dropped']}")
                print(f"   Tables created: {self.stats['tables_created']}")
            
            print(f"   Records inserted: {self.stats['records_inserted']}")
            if not SYNC_CONFIG.get('use_drop_recreate_mode', False):
                print(f"   Records updated: {self.stats['records_updated']}")
                print(f"   Records deleted: {self.stats['records_deleted']}")
            print(f"   Errors: {self.stats['errors']}")
            
            return self.stats['errors'] == 0
            
        except Exception as e:
            self.log(f"Sync failed: {e}", "ERROR")
            return False
        finally:
            if not use_direct:
                self.close_tunnel()
    
    def close_tunnel(self):
        """Close SSH tunnel"""
        if self.tunnel_process:
            self.tunnel_process.terminate()
            try:
                self.tunnel_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.tunnel_process.kill()
            self.tunnel_process = None

def main():
    """Main function"""
    sync = DatabaseSync()
    
    def signal_handler(sig, frame):
        print("\n\n⚠️  Interrupted by user")
        sync.close_tunnel()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check for test connection argument
    test_only = "--test-connection" in sys.argv or "--test" in sys.argv
    
    # Check for dry run argument
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    
    # Check for drop/recreate mode argument
    if "--drop-recreate" in sys.argv:
        SYNC_CONFIG['use_drop_recreate_mode'] = True
        print("🔥 DROP/RECREATE MODE ENABLED via command line")
    
    # Show help
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        print("\nAdditional options:")
        print("  --test-connection    Test database connections only (no sync)")
        print("  --drop-recreate      Use drop/recreate mode instead of incremental sync")
        print("                       WARNING: This will completely replace local table data!")
        print("  --config CONFIG_FILE Specify configuration file (REQUIRED)")
        print("                       Must use config_*.py naming pattern")
        print("                       Example: --config config_midas.py")
        print("\nConfiguration setup:")
        print("  1. Copy config.template.py to config_yourproject.py")
        print("  2. Edit config_yourproject.py with your database settings")
        print("  3. Add config_*.py to .gitignore")
        return
    
    try:
        if test_only:
            # Test connections only
            print("🧪 CONNECTION TEST MODE - Testing database connections only\n")
            
            # Check dependencies
            if not sync.check_dependencies():
                sys.exit(1)
            
            # Create SSH tunnel
            if not sync.create_ssh_tunnel():
                sys.exit(1)
            
            # Test connections
            if sync.test_connections_method(False):
                print("\n✅ All connections working successfully!")
                print("You can now run the actual sync with: python sync_database.py --dry-run")
            else:
                print("\n❌ Connection test failed!")
                sys.exit(1)
        else:
            success = sync.run_sync(dry_run=dry_run)
            if success:
                print("\n✅ Database sync completed successfully!")
            else:
                print("\n❌ Database sync failed!")
                sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 