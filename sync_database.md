# Database Sync - Complete Technical Reference

**Get 100% of your production data locally** - Complete technical documentation for the database synchronization tool.

## ✅ **PROVEN SUCCESS**

This tool has been successfully tested and proven to work with:
- ✅ **87 tables synced** with 659,232 records
- ✅ **Tables without primary keys** (updatebalance, updatecontract, updatemobile, updatecheckaccount)
- ✅ **Complex foreign key relationships** (50+ FK dependencies)
- ✅ **Large datasets** (130K+ records per table)
- ✅ **Zero errors** in production sync

## 🔥 **Drop/Recreate Mode** (Recommended)

The `--drop-recreate` flag solves the major sync challenges:

- ✅ **Tables without primary keys** - No longer an issue
- ✅ **Schema mismatches** - Creates tables with exact remote schema
- ✅ **Foreign key constraints** - Temporarily disables FK checks
- ✅ **Missing columns** - Recreates with complete remote structure
- ✅ **Data type differences** - Uses exact remote table definition
- ✅ **Complex dependencies** - Handles automatically with FK disabled

## 🚀 **Quick Start**

### 1. Set Up Configuration
```bash
# Interactive setup (easiest)
python3 setup.py

# Or manually copy template
cp config.template.py config_yourproject.py
# Edit with your database settings
```

### 2. Test Connection
```bash
# Preview what will sync (always do this first!)
python3 sync_database.py --config config_yourproject.py --dry-run
```

### 3. Get Your Data
```bash
# Drop/recreate mode (recommended - handles all table types)
python3 sync_database.py --config config_yourproject.py --drop-recreate

# OR incremental mode (faster, but requires primary keys)
python3 sync_database.py --config config_yourproject.py
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

### 🔥 **Drop/Recreate Mode** (`--drop-recreate`)
- **Drops each table** completely from local database
- **Recreates table** with exact remote schema
- **Copies all data** from remote to local
- **Handles tables without primary keys** ✅
- **Disables foreign key checks** during operation ✅
- **100% data accuracy guarantee** ✅

### 🔄 **Incremental Mode** (default)
- **INSERT** new records that exist in remote but not in local
- **UPDATE** existing records with data from remote  
- **DELETE** records that exist in local but not in remote
- **Requires primary keys** for comparison
- **Faster for small changes**
- **May fail on schema mismatches** - Use drop/recreate if tables differ

## 🔧 **Schema Handling**

### Automatic Schema Sync (Drop/Recreate Mode)
When using `--drop-recreate`, schema synchronization is automatic:

1. **Drops local table** completely
2. **Recreates with remote schema** (exact structure)
3. **Handles all schema differences** automatically:
   - Missing columns ✅
   - Extra columns ✅  
   - Data type differences ✅
   - Primary key differences ✅
   - Foreign key differences ✅
   - Index differences ✅

### Manual Schema Management (Incremental Mode)
For incremental sync, ensure schemas match:
- Local and remote tables must have identical structures
- All tables must have primary keys
- Foreign key relationships must be consistent

**Tip**: If you get schema errors, use `--drop-recreate` mode instead.

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
├── README.md              # 🎯 Quick start guide
├── sync_database.md       # 📚 Complete technical reference (this file)  
├── sync_database.py       # ⚡ Main sync script (use this!)
├── sync_database.sh       # 🔧 Shell wrapper (optional)
├── setup.py               # 🛠️ Interactive configuration setup
├── config.template.py     # 📋 Template for new projects
├── config_*.py            # 🔒 Your project configs (don't commit!)
└── config.py              # ⚙️ General settings
```

**Essential files**: `sync_database.py` and your `config_*.py` - that's all you need!

## 🔍 **Example Output** 

### Drop/Recreate Mode Success
```
🚀 Database Sync - Portable Version
🔥 DROP/RECREATE MODE ENABLED via command line
============================================================
Configuration loaded: rbcsystem@online-payment.rbccable.com.ph -> rbcsystem@localhost
⚠️  LIVE SYNC MODE - Changes will be applied to local database
Continue? (y/N): y

[09:41:35] INFO: Starting table synchronization...
[09:41:35] INFO: 🔄 admin_interface_theme: Will drop/recreate with 1 records
[09:41:35] INFO:   ✅ Dropped table admin_interface_theme
[09:41:35] INFO:   ✅ Created table admin_interface_theme
[09:41:35] INFO:   ✅ Inserted 1 records into admin_interface_theme

...continuing for all 87 tables...

[09:42:25] INFO: 🔄 updatebalance: Will drop/recreate with 2,717 records
[09:42:25] INFO:   ✅ Dropped table updatebalance
[09:42:25] INFO:   ✅ Created table updatebalance
[09:42:25] INFO:   ✅ Inserted 2,717 records into updatebalance

============================================================
[09:42:26] SUCCESS: Synchronization completed!
📊 Final Statistics:
   Tables processed: 87
   Tables synced: 87
   Tables skipped: 0
   Tables dropped: 87
   Tables created: 87
   Records inserted: 659,232
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

## 🎯 **When to Use Each Mode**

### Use Drop/Recreate Mode When:
- ✅ **First time setup** - Getting production data initially
- ✅ **Tables without primary keys** - Cannot use incremental sync
- ✅ **Foreign key issues** - Complex relationships causing errors
- ✅ **Want 100% accuracy** - Exact copy of production data
- ✅ **Schema mismatches** - Local and remote structures differ

### Use Incremental Mode When:
- ✅ **Daily updates** - Small changes to existing data
- ✅ **All tables have primary keys** - Required for comparison
- ✅ **Speed is important** - Faster than drop/recreate
- ✅ **Large databases** - Where dropping/recreating takes too long

## ⚠️ **Important Notes**

- **Development use only** - Never run on production databases
- **One-way sync** - Remote overwrites local data
- **Always dry-run first** - Preview changes before applying
- **Config security** - Add `config_*.py` to `.gitignore`
- **Backup recommended** - Consider backing up local DB first

## 🆘 **Troubleshooting**

### **Tables Being Skipped?**
```bash
# Problem: "Skipping table: No primary key found"
# Solution: Use drop/recreate mode
python3 sync_database.py --config config_yourproject.py --drop-recreate
```

### **Schema/Column Errors?**
```bash
# Problem: "Unknown column in field list" or schema mismatches
# Solution: Use drop/recreate mode (recreates with exact remote schema)
python3 sync_database.py --config config_yourproject.py --drop-recreate
```

### **Foreign Key Errors?**
```bash
# Problem: "Foreign key constraint fails"
# Solution: Use drop/recreate mode (disables FK checks during sync)
python3 sync_database.py --config config_yourproject.py --drop-recreate
```

### **Want 100% Accuracy?**
```bash
# Solution: Always use drop/recreate for complete data replacement
python3 sync_database.py --config config_yourproject.py --drop-recreate
```

### **Connection Issues:**
```bash
# Check dependencies
python3 -c "import pymysql; print('PyMySQL OK')"
sshpass -V  # For SSH connections

# Test local database
mysql -u root -p -h localhost your_database
```

### **Configuration Issues:**
```bash
# Missing config file
cp config.template.py config_yourproject.py
# Edit with your database settings

# Test configuration
python3 sync_database.py --config config_yourproject.py --dry-run
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