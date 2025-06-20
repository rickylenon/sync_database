#!/bin/bash

# Database Sync - Portable Wrapper
# Usage: ./sync_database.sh [--dry-run]

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_select() {
    echo -e "${BLUE}[SELECT]${NC} $1"
}

# Function to select config file interactively
select_config_file() {
    print_info "No --config parameter provided. Available configuration files:"
    echo ""
    
    # Collect available config files
    config_files=()
    counter=1
    
    for config_file in config_*.py; do
        if [[ -f "$config_file" ]]; then
            config_files+=("$config_file")
            echo "  $counter) $config_file"
            ((counter++))
        fi
    done
    
    if [[ ${#config_files[@]} -eq 0 ]]; then
        print_error "No config_*.py files found."
        print_info "Create one by:"
        print_info "  1. Copy: cp config.template.py config_yourproject.py"
        print_info "  2. Edit config_yourproject.py with your database settings"
        print_info "  3. Add config_*.py to .gitignore"
        exit 1
    fi
    
    echo ""
    print_select "Enter the number of the config file to use (1-${#config_files[@]}):"
    read -r choice
    
    # Validate choice
    if [[ ! "$choice" =~ ^[0-9]+$ ]] || [[ "$choice" -lt 1 ]] || [[ "$choice" -gt ${#config_files[@]} ]]; then
        print_error "Invalid choice. Please enter a number between 1 and ${#config_files[@]}"
        exit 1
    fi
    
    # Get selected config file
    SELECTED_CONFIG_FILE="${config_files[$((choice-1))]}"
    print_info "Selected configuration: $SELECTED_CONFIG_FILE"
    echo ""
}

# Check if help is requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Database Sync - Portable Wrapper"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --dry-run, -d           Preview changes without applying them"
    echo "  --drop-recreate         Use drop/recreate mode (WARNING: replaces all data)"
    echo "  --config CONFIG_FILE    Use specific configuration file"
    echo "  --test-connection       Test database connections only"
    echo "  --help, -h              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --dry-run                        # Preview with default config.py"
    echo "  $0 --config config_midas.py         # Use specific config file"
    echo "  $0 --config config_nexportal.py --dry-run  # Preview with specific config"
    echo ""
    echo "Configuration Setup:"
    echo "  1. Copy config.template.py to config.py (or use specific config file)"
    echo "  2. Edit the config file with your database settings"
    echo "  3. Add config files to .gitignore to prevent committing credentials"
    echo "  4. Run: $0 --dry-run"
    exit 0
fi

# Check if Python script exists
if [[ ! -f "sync_database.py" ]]; then
    print_error "sync_database.py not found in current directory"
    print_info "Make sure you're running this from the sync_database directory"
    exit 1
fi

# Check if --config parameter is provided
config_specified=false

for arg in "$@"; do
    if [[ "$arg" == "--config" ]]; then
        config_specified=true
        break
    fi
done

if [[ "$config_specified" == false ]]; then
    select_config_file "$@"
    # Add the selected config to the arguments
    set -- "--config" "$SELECTED_CONFIG_FILE" "$@"
fi

# Check dependencies
if ! command -v sshpass &> /dev/null; then
    print_error "sshpass not found"
    print_info "Install with: brew install sshpass (macOS) or apt-get install sshpass (Linux)"
    exit 1
fi

if ! python3 -c "import pymysql" 2>/dev/null; then
    print_error "PyMySQL not found"
    print_info "Install with: pip install pymysql"
    exit 1
fi

# Using global/host python3 as configured
print_info "Using global python3 installation"

# Pass all arguments to the Python script
print_info "Running Database Sync..."
python3 sync_database.py "$@"

# Check exit status
if [[ $? -eq 0 ]]; then
    print_info "Sync completed successfully!"
else
    print_error "Sync failed!"
    exit 1
fi 