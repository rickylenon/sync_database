# Database Schema Sync - Documentation

**For local development use** - Schema synchronization script that handles database structure synchronization separately from data syncing.

## ✅ **FEATURES**

The schema sync script provides comprehensive schema analysis and synchronization:

- **Schema Analysis**: Compare remote and local table structures
- **Dependency Analysis**: Analyze foreign key relationships
- **Schema Validation**: Detect and report schema mismatches
- **Safe Operations**: Schema changes with rollback capability
- **Detailed Reporting**: Comprehensive schema analysis reports

## 🚀 **Quick Start**

### 1. Run Schema Analysis Only
```bash
# Analyze schemas without making changes
./sync_schema.sh config_midas.py --validate-only
```

### 2. Preview Schema Changes
```bash
# See what schema changes would be made
./sync_schema.sh config_midas.py --dry-run
```

### 3. Fix Schema Mismatches
```bash
# Fix schema mismatches automatically
./sync_schema.sh config_midas.py --fix-mismatches
```

## 📊 **What It Does**

The schema sync script performs **schema analysis and synchronization**:

### Schema Analysis
- **Compare table structures** between remote and local databases
- **Detect missing tables** that exist remotely but not locally
- **Identify schema mismatches** (missing columns, type differences, etc.)
- **Analyze foreign key dependencies** to understand table relationships

### Schema Synchronization
- **Create missing tables** with remote schema
- **Add missing columns** to existing tables
- **Fix data type mismatches** where possible
- **Handle foreign key constraints** safely

## 🔍 **Schema Analysis Report**

The script generates detailed reports showing:

```
📊 SCHEMA ANALYSIS REPORT
============================================================
📋 Tables analyzed: 208
🔧 Schema mismatches found: 5
🔗 Foreign key dependencies analyzed: 45
❌ Errors: 0
⏭️  Skipped: 3

📋 Missing tables (2):
   - new_feature_table
   - updated_module_table

🔧 Schema mismatches (3):
   📋 live_channel_info_model:
      Missing columns: 1
      Type mismatches: 0
   📋 subscriber_accounts:
      Missing columns: 2
      Type mismatches: 1
   📋 user_preferences:
      Primary key differences

🔗 Foreign key dependencies:
   subscriber_subscription depends on: subscriber_accounts, auth_user
   job_orders depends on: auth_user, client_accounts
   helpdesk_ticket depends on: auth_user, subscriber_accounts

💡 Recommendations:
   - Create missing tables from remote schema
   - Fix schema mismatches by adding missing columns
   - Consider sync order based on foreign key dependencies
```

## 🛠️ **Usage Options**

### Command Line Options

```bash
# Basic schema analysis
./sync_schema.sh config_midas.py

# Validate schemas only (no changes)
./sync_schema.sh config_midas.py --validate-only

# Preview changes (dry run)
./sync_schema.sh config_midas.py --dry-run

# Fix schema mismatches
./sync_schema.sh config_midas.py --fix-mismatches
```

### Python Script Direct Usage

```bash
# Direct Python usage
python3 sync_database_schema.py --config config_midas.py --validate-only
python3 sync_database_schema.py --config config_midas.py --dry-run
python3 sync_database_schema.py --config config_midas.py --fix-mismatches
```

## 🔧 **Configuration**

The schema sync uses the same configuration files as the data sync:

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

### Schema Sync Configuration
```python
PROJECT_SYNC_CONFIG = {
    'use_direct_connection': True,
    'connection_timeout': 90,
    
    # Schema-specific options
    'enable_schema_validation': True,
    'auto_fix_schema_mismatches': True,
    'validate_schema_before_sync': True,
}
```

## 🛡️ **Safety Features**

1. **Validation Mode** - Analyze schemas without making changes
2. **Dry Run Mode** - Preview all schema changes before applying
3. **Detailed Logging** - Shows exactly what schema differences are found
4. **Error Handling** - Graceful failure with detailed error messages
5. **Transaction Safety** - Schema changes wrapped in transactions
6. **Foreign Key Awareness** - Handles FK constraints safely

## 📋 **Schema Analysis Details**

### What Gets Analyzed

1. **Table Existence**
   - Tables that exist remotely but not locally
   - Tables that exist locally but not remotely

2. **Column Analysis**
   - Missing columns in local tables
   - Extra columns in local tables
   - Data type mismatches
   - NULL/NOT NULL differences
   - Default value differences

3. **Key Analysis**
   - Primary key differences
   - Foreign key relationship differences
   - Index differences

4. **Dependency Analysis**
   - Foreign key dependency chains
   - Circular dependency detection
   - Optimal sync order recommendations

### Schema Mismatch Types

```
🔧 Schema Mismatches Found:
   📋 table_name:
      Missing columns: 3
      Type mismatches: 1
      Primary key differences: 1
      Foreign key differences: 2
```

## 🔄 **Workflow Integration**

### Recommended Workflow

1. **First**: Run schema analysis to understand differences
   ```bash
   ./sync_schema.sh config_midas.py --validate-only
   ```

2. **Second**: Preview schema changes
   ```bash
   ./sync_schema.sh config_midas.py --dry-run
   ```

3. **Third**: Fix schema mismatches
   ```bash
   ./sync_schema.sh config_midas.py --fix-mismatches
   ```

4. **Finally**: Run data sync with clean schemas
   ```bash
   ./sync_database.sh config_midas.py
   ```

### Integration with Data Sync

The schema sync script is designed to work alongside the data sync script:

- **Schema sync first**: Ensure table structures match
- **Data sync second**: Sync actual data with proper schemas
- **Better accuracy**: Reduced foreign key and schema errors
- **Cleaner process**: Separate concerns for easier debugging

## 🚨 **Common Issues & Solutions**

### Issue: "Unknown column in field list"
**Solution**: Run schema sync first to fix column mismatches

### Issue: Foreign key constraint errors
**Solution**: Use schema analysis to understand dependencies and sync order

### Issue: Schema validation failures
**Solution**: Check if local database has the correct table structures

### Issue: Connection timeouts
**Solution**: Increase timeout values in configuration

## 📁 **File Structure**

```
sync_database/
├── sync_database_schema.py    # Schema sync script
├── sync_schema.sh            # Schema sync wrapper script
├── sync_schema.md            # This documentation
├── config_midas.py           # Project configuration
├── config.py                 # General configuration
└── sync_database.py          # Data sync script
```

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

## 📊 **Statistics Tracking**

The schema sync tracks detailed statistics:

- **Tables analyzed**: Number of tables processed
- **Schema mismatches**: Tables with structural differences
- **Foreign keys analyzed**: Tables with FK relationships
- **Missing tables**: Tables that need to be created
- **Columns added**: Number of columns added to existing tables
- **Errors**: Number of errors encountered
- **Skipped**: Tables skipped due to issues

## 💡 **Best Practices**

1. **Always validate first**: Use `--validate-only` to understand differences
2. **Preview changes**: Use `--dry-run` before making actual changes
3. **Check dependencies**: Review foreign key relationships in the report
4. **Backup local data**: Always backup before schema changes
5. **Test in staging**: Test schema changes in a staging environment first
6. **Review recommendations**: Follow the generated recommendations

## 🆘 **Troubleshooting**

### Schema Analysis Fails
- Check database connections
- Verify SSH tunnel (if using)
- Ensure proper permissions on databases

### Schema Changes Fail
- Check if local database is read-only
- Verify user has ALTER TABLE permissions
- Review foreign key constraints

### Foreign Key Issues
- Use dependency analysis to understand relationships
- Consider disabling FK checks temporarily
- Review the sync order recommendations

## 📞 **Support**

For issues or questions:
1. Check the schema analysis report for specific issues
2. Review the recommendations in the report
3. Use `--validate-only` to understand the current state
4. Use `--dry-run` to preview changes before applying them 