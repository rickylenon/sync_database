#!/bin/bash

# Database Schema Sync Script Wrapper
# Makes it easier to run schema synchronization

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if config file is provided
if [ $# -eq 0 ]; then
    print_error "No configuration file specified"
    echo ""
    echo "Usage: $0 CONFIG_FILE [OPTIONS]"
    echo ""
    echo "Examples:"
    echo "  $0 config_midas.py --dry-run        # Preview schema changes"
    echo "  $0 config_midas.py                  # Perform schema sync"
    echo "  $0 config_midas.py --validate-only  # Only validate schemas"
    echo "  $0 config_midas.py --fix-mismatches # Fix schema mismatches"
    echo ""
    echo "Available config files:"
    if ls config_*.py 1> /dev/null 2>&1; then
        for file in config_*.py; do
            echo "  - $file"
        done
    else
        echo "  No config_*.py files found"
        echo "  Copy config.template.py to config_yourproject.py and customize it"
    fi
    exit 1
fi

CONFIG_FILE="$1"
shift

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    print_error "Configuration file '$CONFIG_FILE' not found"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if required Python packages are installed
print_status "Checking Python dependencies..."
if ! python3 -c "import pymysql" 2>/dev/null; then
    print_error "PyMySQL is not installed. Install with: pip install pymysql"
    exit 1
fi

print_success "All dependencies available"

# Run the schema sync script
print_status "Running schema sync with config: $CONFIG_FILE"
echo ""

python3 sync_database_schema.py --config "$CONFIG_FILE" "$@"

# Check exit code
if [ $? -eq 0 ]; then
    print_success "Schema sync completed successfully"
else
    print_error "Schema sync failed"
    exit 1
fi 