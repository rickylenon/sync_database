# Database Sync - Get Production Data Locally

🚀 **Get 100% of your production data locally in 3 simple commands**

## ⚡ Quick Start (What Actually Works)

```bash
# 1. Set up your configuration
python3 setup.py

# 2. Test it works (preview changes)
python3 sync_database.py --config config_yourproject.py --dry-run

# 3. Get ALL your production data (handles ALL table types)
python3 sync_database.py --config config_yourproject.py --drop-recreate
```

✅ **Done!** You now have 100% of your production data locally, including tables without primary keys.

## 🎯 Why This Works

- **🔥 Drop/Recreate Mode**: Handles tables without primary keys perfectly
- **🔗 Foreign Key Smart**: Temporarily disables FK checks during sync
- **📊 Complete Data**: Gets every record from every table (659K+ records in minutes)
- **🛡️ Safe**: Dry-run mode shows exactly what will happen first

## 🚀 Two Sync Modes

### 🔄 **Incremental Sync** (default - fast updates)
```bash
python3 sync_database.py --config config_yourproject.py
```
- Updates only changed records
- Fast for regular updates
- Requires tables to have primary keys

### 🔥 **Drop/Recreate Mode** (complete replacement)
```bash
python3 sync_database.py --config config_yourproject.py --drop-recreate
```
- ✅ **Handles tables without primary keys**
- ✅ **Handles complex foreign key relationships** 
- ✅ **100% data accuracy guarantee**
- ✅ **Perfect for initial setup or when you need everything**

## 💡 Real-World Examples

### 🐛 **Debug Production Issues**
```bash
# Get complete production data for debugging
python3 sync_database.py --config config_production.py --drop-recreate

# Now debug locally with exact production data
```

### 🔄 **Test Database Changes**
```bash
# Get fresh production data
python3 sync_database.py --config config_staging.py --drop-recreate

# Test your changes safely on real data
```

### ⚡ **Daily Development Updates**
```bash
# Quick incremental updates for daily development
python3 sync_database.py --config config_dev.py --dry-run
python3 sync_database.py --config config_dev.py
```

## 📁 Key Files

- **`config_*.py`** - Your project configurations *(keep these private!)*
- **`sync_database.py`** - Main sync script (use this!)
- **`setup.py`** - Interactive configuration setup
- **`config.template.py`** - Template for new projects

## 🔧 Configuration

### Quick Setup
```bash
# Interactive setup (easiest)
python3 setup.py

# Follow prompts to create config_yourproject.py
```

### Configuration Structure
```
config_yourproject.py        # Your project settings (DON'T commit!)
├── SSH_CONFIG               # SSH tunnel to production
├── REMOTE_DB_CONFIG         # Production database details  
├── LOCAL_DB_CONFIG          # Local development database
└── EXCLUDED_TABLES          # Tables to skip (logs, cache, etc.)
```

### Example Configuration
```python
# SSH tunnel to production
SSH_CONFIG = {
    'host': 'your-server.com',
    'user': 'username',
    'port': 22,
    'password': 'password'
}

# Production database
REMOTE_DB_CONFIG = {
    'host': 'prod-db.com',
    'user': 'readonly_user', 
    'password': 'password',
    'database': 'production_db'
}

# Your local database
LOCAL_DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'rootpass',
    'database': 'local_dev_db'
}
```

## 🔧 Installation

```bash
# Install required packages
pip3 install pymysql

# For SSH connections (if needed)
brew install sshpass  # macOS
sudo apt install sshpass  # Linux
```

## ⚠️ Best Practices

### 🔒 **Security**
- **Never commit `config_*.py` files** - add to `.gitignore`
- **Use read-only database users** for production access
- **Test with `--dry-run` first** - always preview changes

### 🛡️ **Safe Usage**
```bash
# Always preview first
python3 sync_database.py --config config_myproject.py --dry-run

# Then run for real
python3 sync_database.py --config config_myproject.py --drop-recreate
```

### 🎯 **When to Use Each Mode**
- **Drop/Recreate**: First time setup, tables without primary keys, want 100% accuracy
- **Incremental**: Daily updates, have primary keys, want speed

## 🆘 **Troubleshooting**

**Tables being skipped?** → Use `--drop-recreate` mode
**Foreign key errors?** → Use `--drop-recreate` mode  
**Want 100% accuracy?** → Use `--drop-recreate` mode

## 📚 **More Info**

See `sync_database.md` for complete technical reference and advanced options.

---

**🎉 Get your production data in 3 commands!** 