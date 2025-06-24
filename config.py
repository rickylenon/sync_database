#!/usr/bin/env python3
"""
General Database Sync Configuration
Contains application-wide settings, common exclusions, and defaults.
No sensitive information - safe to commit to version control.

Project-specific configs (config_*.py) contain credentials and should not be committed.
"""

# ====================================================================
# DEFAULT CONFIGURATIONS (Base templates)
# ====================================================================

# Default SSH configuration template
DEFAULT_SSH_CONFIG = {
    'host': '',
    'user': '',
    'port': 22,
    'password': '',
    'local_tunnel_port': 3307
}

# Default database configuration template
DEFAULT_DB_CONFIG = {
    'host': '',
    'port': 3306,
    'user': '',
    'password': '',
    'database': ''
}

# ====================================================================
# GENERAL SYNC BEHAVIOR CONFIGURATION
# ====================================================================

SYNC_CONFIG = {
    # Whether to prompt for confirmation before live sync
    'require_confirmation': True,
    
    # Whether to show detailed progress for each table
    'show_progress': True,
    
    # Connection timeout in seconds
    'connection_timeout': 60,
    
    # SSH tunnel establishment wait time in seconds
    'tunnel_wait_time': 5,
    
    # Maximum number of retries for failed operations
    'max_retries': 3,
    
    # MySQL specific settings
    'mysql_read_timeout': 120,
    'mysql_write_timeout': 120,
    
    # Use direct connection instead of SSH tunnel
    'use_direct_connection': False,
    
    # DROP AND RECREATE MODE
    # When enabled, tables will be dropped and recreated instead of synced
    # This is faster for large changes but completely replaces local data
    'use_drop_recreate_mode': False,
    
    # When using drop/recreate mode, disable foreign key checks temporarily
    # This allows dropping/creating tables in any order
    'disable_foreign_key_checks': True,
}

# ====================================================================
# VALIDATION FUNCTIONS
# ====================================================================

def validate_ssh_config(ssh_config):
    """Validate SSH configuration"""
    required_keys = ['host', 'user', 'port', 'password', 'local_tunnel_port']
    
    for key in required_keys:
        if key not in ssh_config or not ssh_config[key]:
            raise ValueError(f"Missing required SSH configuration: {key}")
    
    # Validate port numbers
    if not isinstance(ssh_config['port'], int) or ssh_config['port'] <= 0:
        raise ValueError("SSH port must be a positive integer")
    
    if not isinstance(ssh_config['local_tunnel_port'], int) or ssh_config['local_tunnel_port'] <= 0:
        raise ValueError("Local tunnel port must be a positive integer")
    
    return True

def validate_db_config(db_config, config_type="database"):
    """Validate database configuration"""
    required_keys = ['host', 'port', 'user', 'password', 'database']
    
    for key in required_keys:
        if key not in db_config or not db_config[key]:
            raise ValueError(f"Missing required {config_type} database configuration: {key}")
    
    # Validate port number
    if not isinstance(db_config['port'], int) or db_config['port'] <= 0:
        raise ValueError(f"{config_type} database port must be a positive integer")
    
    return True

# ====================================================================
# APPLICATION INFO
# ====================================================================

APP_INFO = {
    'name': 'Database Sync Tool',
    'version': '2.0.0',
    'description': 'Portable database synchronization script for development environments',
    'author': 'Development Team',
}

def get_app_info():
    """Get application information"""
    return APP_INFO.copy()

def print_version():
    """Print application version information"""
    info = get_app_info()
    print(f"{info['name']} v{info['version']}")
    print(info['description'])
