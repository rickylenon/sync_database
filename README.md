# Database Sync - Portable Version

🚀 **Quick Setup for Any Project**

## 📋 What You Need

1. **Copy this folder** to your project
2. **Configure** for your environment  
3. **Run the sync**

## ⚡ Quick Start

```bash
# 1. Setup configuration (creates config_yourproject.py)
python3 setup.py

# 2. Edit config_yourproject.py with your settings
# - SSH server details
# - Database connections  
# - Tables to exclude

# 3. Test first (--config is REQUIRED)
python3 sync_database.py --config config_yourproject.py --dry-run

# 4. Run actual sync
python3 sync_database.py --config config_yourproject.py

# Or use existing project configs:
python3 sync_database.py --config config_midas.py --dry-run
python3 sync_database.py --config config_nexportal.py
```

## ✨ **New Feature: Auto-Create Missing Tables**

The sync script now **automatically creates tables** that exist in the remote database but not in your local database! This means:

- **New tables** in remote will be created locally with the exact same schema
- **All exclusion rules** are still respected (excluded tables won't be created)
- **Works in both sync modes** (incremental and drop/recreate)
- **Safe with dry-run** - shows you what tables would be created

## 📁 Files

- **`config.py`** - General application configuration (shared settings)
- **`config.template.py`** - Template for creating project configs
- **`config_midas.py`** - Example: Midas project configuration *(don't commit)*
- **`config_nexportal.py`** - Example: NexPortal project configuration *(don't commit)*
- **`sync_database.py`** - Main sync script
- **`sync_database.sh`** - Shell wrapper with dependency checks
- **`setup.py`** - Quick setup helper
- **`sync_database.md`** - Full documentation

## 🔧 Configuration System

The script uses a **two-tier configuration system**:

### 1. General Configuration (`config.py`)
- **Sync behavior** - timeouts, retry logic, connection settings
- **Common table exclusions** - patterns shared across all projects
- **Default connection templates** - base settings for SSH and database configs

### 2. Project-Specific Configuration (`config_*.py`)
- **Database connections** - SSH, remote DB, local DB settings
- **Project table filters** - additional exclusions specific to each project
- **Sync overrides** - project-specific behavior overrides

### Usage Format
```bash
# All config files must follow the config_*.py naming pattern
python3 sync_database.py --config config_midas.py --dry-run
python3 sync_database.py --config config_nexportal.py --dry-run
python3 sync_database.py --config config_yourproject.py --dry-run
```

### Creating Configuration Files
```bash
# Option 1: Use the setup script (recommended)
python3 setup.py

# Option 2: Manual setup
cp config.template.py config_yourproject.py
# Edit config_yourproject.py with your connections and filters
```

### Configuration Structure
```
config.py                    # General app configuration
├── SYNC_CONFIG              # Global sync behavior
├── COMMON_EXCLUDED_TABLES   # Tables excluded for all projects
├── COMMON_EXCLUDED_PATTERNS # Patterns excluded for all projects
└── DEFAULT_*_CONFIG         # Default connection templates

config_midas.py              # Midas project configuration
├── SSH_CONFIG               # Midas SSH connection
├── REMOTE_DB_CONFIG         # Midas remote database
├── LOCAL_DB_CONFIG          # Midas local database
├── PROJECT_EXCLUDED_TABLES  # Midas-specific exclusions
└── PROJECT_SYNC_CONFIG      # Midas-specific overrides
```

## 🔧 Dependencies

**Uses global/host python3 installation**

```bash
pip3 install pymysql
brew install sshpass  # macOS
# or
sudo apt install sshpass  # Linux
```

## ⚠️ Important

- **Add project configs to `.gitignore`** (config_*.py - contains credentials)
- **Keep `config.py` in version control** (general settings, no credentials)
- **Always test with `--dry-run` first**
- **Development use only** - not for production
- **Never commit project configuration files** - they contain sensitive credentials

For full documentation, see `sync_database.md` 