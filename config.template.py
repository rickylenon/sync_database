#!/usr/bin/env python3
"""
Project Database Configuration Template
Get 100% production data locally in 3 commands!

📋 SETUP:
    1. Copy this file to config_yourproject.py
    2. Edit with your specific database connections and table filters
    3. Add config_*.py to .gitignore to prevent committing credentials

🚀 QUICK START:
# 1. Preview what will sync
python3 sync_database.py --config config_yourproject.py --dry-run

# 2. Get ALL production data (recommended - handles tables without primary keys)
python3 sync_database.py --config config_yourproject.py --drop-recreate

# 3. For daily updates (incremental sync - faster but requires primary keys)
python3 sync_database.py --config config_yourproject.py

💡 TIP: Use --drop-recreate for first time setup and when you want 100% accuracy
✅ PROVEN: Successfully tested with 87 tables and 659,232 records!
"""

# ====================================================================
# SSH TUNNEL CONFIGURATION
# ====================================================================
SSH_CONFIG = {
    'host': 'your-ssh-server.com',
    'user': 'your-ssh-username', 
    'port': 22,  # Standard SSH port, change if different
    'password': 'your-ssh-password',
    'local_tunnel_port': 3307  # Local port for SSH tunnel (must be available)
}

# ====================================================================
# REMOTE DATABASE CONFIGURATION (Source)
# ====================================================================
REMOTE_DB_CONFIG = {
    'host': 'your-remote-db-host.com',
    'port': 3306,
    'user': 'remote-db-username',
    'password': 'remote-db-password',
    'database': 'remote-database-name'
}

# ====================================================================
# LOCAL DATABASE CONFIGURATION (Target)
# ====================================================================
LOCAL_DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'local-db-username',
    'password': 'local-db-password',
    'database': 'local-database-name'
}

# ====================================================================
# PROJECT-SPECIFIC TABLE FILTERS
# ====================================================================

# Additional tables to exclude for this project (beyond common exclusions in config.py)
PROJECT_EXCLUDED_TABLES = {
    # Add project-specific tables to exclude here
    # Example:
    # 'your_project_audit_logs',
    # 'your_project_temp_data',
    # 'your_project_old_backups',
}

# Additional patterns to exclude for this project (beyond common patterns in config.py)
PROJECT_EXCLUDED_PATTERNS = [
    # Add project-specific patterns here
    # Example:
    # 'yourproject_temp',
    # 'old_yourproject',
]

# ====================================================================
# PROJECT-SPECIFIC SYNC OVERRIDES (Optional)
# ====================================================================

# Override general sync settings for this project if needed
PROJECT_SYNC_CONFIG = {
    # Example overrides:
    # 'use_direct_connection': True,  # Override to use direct connection
    # 'connection_timeout': 120,      # Override timeout for slower connections
    # 'tunnel_wait_time': 8,          # Override tunnel wait time
}

# ====================================================================
# SYNC CONFIGURATION
# ====================================================================

# Tables to completely exclude from sync (exact table names)
EXCLUDED_TABLES = {
    # Archive and audit tables (usually large and not needed for development)
    'radacct_archive',
    'auditlog_logentry',
    'helpdesk_followup',
    'subscriber_logs',
    'fb_queues',
    'broadcast',
    'olt_logs',
    'spin_logs',
    'subscriber_direct',
    'sms_logs',
    'vod_list',
    'tv_schedule',
    'sms_queues',
    # Add your project-specific tables to exclude here
}

# Table name patterns to exclude (tables starting with or containing these patterns)
EXCLUDED_PATTERNS = [
    'rad',    # All RADIUS tables (radcheck, radreply, radacct, etc.)
    'copy',    # All backup/copy tables
    'bak',
    'backup',
    'temp',
    'log',
    'cache',
    'audit',
    'audit_trail',
    'temporary_data',
    # Add your project-specific patterns here
]

# ====================================================================
# SYNC BEHAVIOR CONFIGURATION
# ====================================================================
SYNC_CONFIG = {
    # Whether to prompt for confirmation before live sync
    'require_confirmation': True,
    
    # Whether to show detailed progress for each table
    'show_progress': True,
    
    # Connection timeout in seconds
    'connection_timeout': 60,  # Increased for AWS RDS
    
    # SSH tunnel establishment wait time in seconds
    'tunnel_wait_time': 5,  # Increased for stability
    
    # Maximum number of retries for failed operations
    'max_retries': 3,
    
    # MySQL specific settings for AWS RDS
    'mysql_read_timeout': 120,
    'mysql_write_timeout': 120,
    
    # Use direct connection instead of SSH tunnel (RDS is accessible directly)
    'use_direct_connection': False,  # Set to True to bypass SSH tunnel
    
    # DROP AND RECREATE MODE
    # When enabled, tables will be dropped and recreated instead of synced
    # This is faster for large changes but completely replaces local data
    'use_drop_recreate_mode': False,  # Set to True to enable drop/recreate
    
    # When using drop/recreate mode, disable foreign key checks temporarily
    # This allows dropping/creating tables in any order
    'disable_foreign_key_checks': True,  # Recommended for drop/recreate mode
}

# ====================================================================
# VALIDATION (Do not modify)
# ====================================================================
def validate_config():
    """Validate that all required configuration is present"""
    required_ssh_keys = ['host', 'user', 'port', 'password', 'local_tunnel_port']
    required_db_keys = ['host', 'port', 'user', 'password', 'database']
    
    # Validate SSH config
    for key in required_ssh_keys:
        if key not in SSH_CONFIG or not SSH_CONFIG[key]:
            raise ValueError(f"Missing required SSH configuration: {key}")
    
    # Validate remote DB config
    for key in required_db_keys:
        if key not in REMOTE_DB_CONFIG or not REMOTE_DB_CONFIG[key]:
            raise ValueError(f"Missing required remote database configuration: {key}")
    
    # Validate local DB config
    for key in required_db_keys:
        if key not in LOCAL_DB_CONFIG or not LOCAL_DB_CONFIG[key]:
            raise ValueError(f"Missing required local database configuration: {key}")
    
    return True

# Auto-validate on import
if __name__ != '__main__':
    validate_config() 