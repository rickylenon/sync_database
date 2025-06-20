# Database Replicator - Development Tool

🔧 **Replicate Production Data Locally for Development & Debugging**

## 🎯 Why Use This Tool?

As a developer, you've probably faced these scenarios:

- **🐛 Debugging production issues**: "It works on my machine" - but you need real data to reproduce the bug
- **🔄 Testing migrations**: Ensure your database changes work with actual production data structure and volume
- **📊 Data analysis**: Need to query production data without affecting the live system
- **🧪 Feature development**: Build and test features with realistic data sets
- **🔍 Performance testing**: Test queries against production-sized datasets locally

**This tool safely replicates your remote/production database to your local development environment.**

## ⚡ Quick Start

```bash
# 1. Setup configuration for your project
python3 setup.py

# 2. Configure your connections in config_yourproject.py
# - SSH tunnel to production server
# - Remote database credentials  
# - Local database settings
# - Tables to exclude (logs, cache, etc.)

# 3. Test the replication first (--config is REQUIRED)
python3 sync_database.py --config config_yourproject.py --dry-run

# 4. Run the actual data replication
python3 sync_database.py --config config_yourproject.py

# Using existing project configurations:
python3 sync_database.py --config config_midas.py --dry-run
python3 sync_database.py --config config_nexportal.py
```

## 🚀 Key Features

### 🔄 **Smart Data Replication**
- **Complete data copy**: Replicates tables, data, and structure from remote to local
- **Incremental updates**: Option to sync only changed data (faster subsequent runs)
- **Full replacement**: Option to drop and recreate for clean slate testing

### 🛠️ **Auto-Schema Management**
- **Auto-creates missing tables**: New tables in production automatically appear locally
- **Schema synchronization**: Ensures local structure matches production
- **Safe exclusions**: Respects table exclusion rules (won't create excluded tables)

### 🎯 **Developer-Friendly**
- **Dry-run mode**: See what changes will be made before executing
- **Selective table replication**: Exclude logs, cache, and sensitive tables
- **SSH tunnel support**: Secure connections to production servers
- **Multiple project configs**: Manage different environments easily

## 💡 Common Use Cases

### 🐛 **Bug Investigation**
```bash
# Replicate production data to investigate a specific issue
python3 sync_database.py --config config_production.py --dry-run
python3 sync_database.py --config config_production.py

# Now debug locally with real production data
```

### 🔄 **Migration Testing**
```bash
# Get fresh production data
python3 sync_database.py --config config_staging.py

# Test your migration scripts locally
python3 manage.py migrate --settings=local_settings

# Verify migration worked with production-like data
```

### 📊 **Data Analysis & Performance Testing**
```bash
# Replicate for analysis without impacting production
python3 sync_database.py --config config_analytics.py

# Run heavy queries locally
SELECT COUNT(*) FROM large_production_table WHERE complex_conditions;
```

## 📁 Project Structure

- **`config.py`** - General app settings (connection timeouts, global exclusions)
- **`config.template.py`** - Template for creating project-specific configs
- **`config_*.py`** - Your project configurations *(keep these private!)*
- **`sync_database.py`** - Main replication script
- **`sync_database.sh`** - Shell wrapper with dependency validation
- **`setup.py`** - Interactive configuration setup
- **`sync_database.md`** - Complete technical documentation

## 🔧 Configuration System

### Two-Layer Configuration Approach

#### 1. **Global Settings** (`config.py`)
- Connection timeouts and retry logic
- Common table exclusions (logs, sessions, cache)
- Default connection templates
- Shared across all projects

#### 2. **Project-Specific Settings** (`config_*.py`)
- Database connection details
- SSH tunnel configuration
- Project-specific table exclusions
- Custom replication behavior

### Setting Up a New Project
```bash
# Interactive setup (recommended)
python3 setup.py
# Follow prompts to create config_yourproject.py

# Manual setup
cp config.template.py config_yourproject.py
# Edit with your specific settings
```

### Configuration Example Structure
```
config.py                    # Global settings (safe to commit)
├── Timeouts & retry logic
├── Common excluded tables
└── Default connection templates

config_yourproject.py        # Project settings (DON'T commit!)
├── SSH_CONFIG               # SSH tunnel to production
├── REMOTE_DB_CONFIG         # Production database details
├── LOCAL_DB_CONFIG          # Local development database
└── PROJECT_EXCLUDED_TABLES  # Tables to skip (logs, cache, etc.)
```

## 🔧 Installation & Dependencies

This tool uses your system's Python installation:

```bash
# Install required Python packages
pip3 install pymysql

# Install SSH password support (for automated connections)
brew install sshpass  # macOS
# or
sudo apt install sshpass  # Linux
```

## ⚠️ Security & Best Practices

### 🔒 **Security**
- **Never commit `config_*.py` files** - they contain production credentials
- **Add `config_*.py` to `.gitignore**
- **Use read-only database users** when possible
- **Limit SSH access** to development machines only

### 🛡️ **Safe Usage**
- **Always test with `--dry-run` first**
- **Exclude sensitive tables** (user passwords, tokens, logs)
- **Use separate local databases** - never overwrite important local data
- **Development environments only** - not for production use

### 📋 **Recommended Workflow**
```bash
# 1. Test what will happen
python3 sync_database.py --config config_myproject.py --dry-run

# 2. Review the planned changes
# 3. Run the actual replication
python3 sync_database.py --config config_myproject.py

# 4. Verify your local database has the expected data
```

## 🔗 Need More Details?

See `sync_database.md` for complete technical documentation, advanced configuration options, and troubleshooting guides.

---

**Happy debugging with real data! 🚀** 