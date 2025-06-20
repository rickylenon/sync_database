# Database Sync - Portable Script

**For local development use** - Configurable database synchronization script that can be copied and used across different projects.

## ✅ **PORTABLE SOLUTION**

The script is now fully configurable and can be easily adapted for different projects:

- **Configuration-driven:** All credentials and settings in `config.py` ✅
- **Template-based:** Copy `config.template.py` to customize for your project ✅
- **Portable:** Copy the entire folder to any project and configure ✅
- **Secure:** Configuration can be excluded from git commits ✅

## 🚀 **Quick Setup**

### 1. Copy to Your Project
```bash
# Copy the sync_database folder to your project
cp -r /path/to/original/sync_database /your/project/directory/
cd /your/project/directory/sync_database
```

### 2. Configure for Your Project
```bash
# Copy the template and customize it
cp config.template.py config.py

# Edit config.py with your specific settings
# - SSH server details
# - Database connections
# - Tables to exclude
# - Sync behavior
```

### 3. Add to .gitignore
```bash
# Add to your project's .gitignore
echo "sync_database/config.py" >> ../.gitignore
```

### 4. Run the Sync
```bash
# Preview what would be changed (recommended first)
python sync_database.py --dry-run

# Actually perform the sync
python sync_database.py

# Or use the shell wrapper
./sync_database.sh --dry-run
./sync_database.sh
```

## 📋 **Configuration Options**

### SSH Tunnel Settings
```python
SSH_CONFIG = {
    'host': 'your-ssh-server.com',
    'user': 'your-ssh-username', 
    'port': 22,
    'password': 'your-ssh-password',
    'local_tunnel_port': 3307
}
```

### Database Connections
```python
# Remote database (source)
REMOTE_DB_CONFIG = {
    'host': 'remote-db-host.com',
    'port': 3306,
    'user': 'remote-user',
    'password': 'remote-password',
    'database': 'remote-database'
}

# Local database (target)
LOCAL_DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'local-user',
    'password': 'local-password',
    'database': 'local-database'
}
```

### Table Exclusions
```python
# Exclude specific tables
EXCLUDED_TABLES = {
    'logs',
    'audit_trail',
    'temporary_data',
    'your_large_table'
}

# Exclude by pattern
EXCLUDED_PATTERNS = [
    'temp',    # All tables starting with 'temp'
    'log',     # All tables starting with 'log'
    'cache',   # All tables starting with 'cache'
    'copy'     # All tables containing 'copy'
]
```

### Sync Behavior
```python
SYNC_CONFIG = {
    'require_confirmation': True,    # Prompt before live sync
    'show_progress': True,          # Show detailed progress
    'connection_timeout': 30,       # Connection timeout
    'tunnel_wait_time': 3,          # SSH tunnel wait time
    'max_retries': 3               # Max retry attempts
}
```

## 📊 **What It Does**

The script performs **one-way synchronization** from remote → local:

- **INSERT** new records that exist in remote but not in local
- **UPDATE** existing records with data from remote  
- **DELETE** records that exist in local but not in remote

## 🔧 **Requirements**

```bash
# Install Python dependencies
pip install pymysql

# Install sshpass (for SSH tunnel)
# macOS:
brew install sshpass

# Linux:
sudo apt-get install sshpass
```

## 🛡️ **Safety Features**

1. **Configuration Validation** - Validates config on startup
2. **Dry Run Mode** - Always test first with `--dry-run`
3. **Confirmation Prompt** - Asks before making live changes (configurable)
4. **Transaction Safety** - Each table wrapped in transaction
5. **Detailed Logging** - Shows exactly what's happening
6. **Error Handling** - Graceful failure with rollback
7. **Foreign Key Handling** - Skips FK constraint errors gracefully

## 📁 **File Structure**

```
sync_database/
├── config.py              # Your project configuration (don't commit)
├── config.template.py     # Template to copy and customize
├── sync_database.py       # Main sync script
├── sync_database.sh       # Shell wrapper
└── sync_database.md       # This documentation
```

## 🔍 **Example Output**

```
🚀 Database Sync - Portable Version
============================================================
Configuration loaded: myproject@remote-server.com -> myproject@localhost
⚠️  LIVE SYNC MODE - Changes will be applied to local database
Continue? (y/N): y

[08:43:23] INFO: Creating SSH tunnel...
   🔗 SSH: user@ssh-server.com:22
   🚇 Tunnel: localhost:3307 -> remote-db.com:3306
[08:43:26] SUCCESS: SSH tunnel established successfully
[08:43:27] INFO: Testing database connections...
[08:43:27] INFO: ✅ Local database: 95 tables
[08:43:27] INFO: ✅ Remote database: 98 tables, MySQL 8.0.42
[08:43:27] INFO: 📊 Found 78 tables to sync (20 excluded)

[08:43:27] INFO: Starting table synchronization...

🔄 Progress: 1/78 - users
📋 users: Insert=5, Update=12, Delete=2
🔄 Progress: 2/78 - products
🔄 Progress: 3/78 - orders
📋 orders: Insert=23, Update=8, Delete=0
...

============================================================
[08:43:54] SUCCESS: Synchronization completed!
📊 Final Statistics:
   Tables processed: 78
   Tables synced: 65
   Tables skipped: 3
   Records inserted: 1,234
   Records updated: 567
   Records deleted: 89
   Errors: 0

✅ Database sync completed successfully!
```

## 🔧 **Customization Examples**

### Different Database Names
```python
# In config.py
LOCAL_DB_CONFIG['database'] = 'myproject_dev'
REMOTE_DB_CONFIG['database'] = 'myproject_prod'
```

### Project-Specific Exclusions
```python
# In config.py
EXCLUDED_TABLES.update([
    'user_sessions',
    'cache_entries', 
    'temporary_uploads'
])

EXCLUDED_PATTERNS.extend([
    'test',    # Exclude test tables
    'staging'  # Exclude staging tables
])
```

### Different SSH Configuration
```python
# In config.py
SSH_CONFIG.update({
    'host': 'myproject-ssh.company.com',
    'port': 2022,
    'user': 'myproject-user'
})
```

## ⚠️ **Important Notes**

- **Development use only** - Configure credentials in `config.py`
- **One-way sync** - Remote overwrites local data
- **Always dry-run first** - Preview changes before applying
- **Backup recommended** - Consider backing up local DB first
- **Git exclude** - Add `config.py` to `.gitignore`
- **Network required** - Needs SSH access to remote servers

## 🆘 **Troubleshooting**

**Missing Configuration:**
```bash
❌ Error: config.py not found!
# Copy the template and customize it
cp config.template.py config.py
```

**Connection Issues:**
```bash
# Check if sshpass is installed
sshpass -V

# Check if PyMySQL is installed  
python -c "import pymysql; print('OK')"

# Test local MySQL connection
mysql -u root -p -h localhost your_database
```

**Permission Issues:**
```bash
# Make shell script executable
chmod +x sync_database.sh
```

**Configuration Validation:**
```python
# Test your configuration
python -c "from config import validate_config; validate_config(); print('Config OK')"
```

## 🎯 **Best Practices**

1. **Always start with dry-run** to preview changes
2. **Keep config.py out of version control** with `.gitignore`
3. **Use descriptive database names** for different environments
4. **Exclude large/unnecessary tables** to speed up sync
5. **Test connection settings** before running full sync
6. **Backup local database** before major syncs
7. **Document your exclusions** with comments in config

That's it! 🎉 Now you can easily copy this to any project and configure it for your specific needs. 