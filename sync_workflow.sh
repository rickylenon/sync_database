#!/bin/bash

# Database Sync Workflow Script
# Combines schema sync and data sync for optimal results

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

print_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

print_header() {
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}============================================================${NC}"
}

# Check if config file is provided
if [ $# -eq 0 ]; then
    print_error "No configuration file specified"
    echo ""
    echo "Usage: $0 CONFIG_FILE [OPTIONS]"
    echo ""
    echo "Workflow Options:"
    echo "  --validate-only     # Only analyze schemas and preview changes"
    echo "  --dry-run          # Preview all changes (schema + data)"
    echo "  --schema-only      # Only sync schemas"
    echo "  --data-only        # Only sync data (assumes schemas are correct)"
    echo "  --fix-schemas      # Fix schema issues and sync data"
    echo ""
    echo "Examples:"
    echo "  $0 config_midas.py --validate-only    # Analyze current state"
    echo "  $0 config_midas.py --dry-run         # Preview all changes"
    echo "  $0 config_midas.py --fix-schemas     # Fix schemas and sync data"
    echo "  $0 config_midas.py                   # Full sync (schema + data)"
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

# Parse workflow options
VALIDATE_ONLY=false
DRY_RUN=false
SCHEMA_ONLY=false
DATA_ONLY=false
FIX_SCHEMAS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --validate-only)
            VALIDATE_ONLY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --schema-only)
            SCHEMA_ONLY=true
            shift
            ;;
        --data-only)
            DATA_ONLY=true
            shift
            ;;
        --fix-schemas)
            FIX_SCHEMAS=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

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

# Function to run schema sync
run_schema_sync() {
    local mode="$1"
    print_step "Running schema sync ($mode)..."
    
    if [ "$mode" = "validate" ]; then
        ./sync_schema.sh "$CONFIG_FILE" --validate-only
    elif [ "$mode" = "dry-run" ]; then
        ./sync_schema.sh "$CONFIG_FILE" --dry-run
    elif [ "$mode" = "fix" ]; then
        ./sync_schema.sh "$CONFIG_FILE" --fix-mismatches
    else
        ./sync_schema.sh "$CONFIG_FILE"
    fi
    
    if [ $? -eq 0 ]; then
        print_success "Schema sync completed successfully"
        return 0
    else
        print_error "Schema sync failed"
        return 1
    fi
}

# Function to run data sync
run_data_sync() {
    local mode="$1"
    print_step "Running data sync ($mode)..."
    
    if [ "$mode" = "dry-run" ]; then
        ./sync_database.sh "$CONFIG_FILE" --dry-run
    else
        ./sync_database.sh "$CONFIG_FILE"
    fi
    
    if [ $? -eq 0 ]; then
        print_success "Data sync completed successfully"
        return 0
    else
        print_error "Data sync failed"
        return 1
    fi
}

# Main workflow logic
print_header "Database Sync Workflow"
print_status "Configuration: $CONFIG_FILE"

if [ "$VALIDATE_ONLY" = true ]; then
    print_header "VALIDATION MODE - Analyzing Current State"
    print_status "This will analyze schemas and preview changes without making any modifications"
    
    run_schema_sync "validate"
    if [ $? -eq 0 ]; then
        echo ""
        print_success "Validation completed successfully!"
        print_status "Review the schema analysis report above to understand current state"
        print_status "Run with --dry-run to preview actual changes"
    else
        print_error "Validation failed!"
        exit 1
    fi

elif [ "$DRY_RUN" = true ]; then
    print_header "DRY RUN MODE - Previewing All Changes"
    print_status "This will preview both schema and data changes without making modifications"
    
    run_schema_sync "dry-run"
    if [ $? -eq 0 ]; then
        echo ""
        run_data_sync "dry-run"
        if [ $? -eq 0 ]; then
            echo ""
            print_success "Dry run completed successfully!"
            print_status "Review the changes above. If everything looks good, run without --dry-run"
        else
            print_error "Data sync dry run failed!"
            exit 1
        fi
    else
        print_error "Schema sync dry run failed!"
        exit 1
    fi

elif [ "$SCHEMA_ONLY" = true ]; then
    print_header "SCHEMA ONLY MODE - Syncing Schemas Only"
    print_status "This will sync table structures without syncing data"
    
    run_schema_sync "fix"
    if [ $? -eq 0 ]; then
        echo ""
        print_success "Schema sync completed successfully!"
        print_status "Table structures are now synchronized"
        print_status "Run data sync separately when ready"
    else
        print_error "Schema sync failed!"
        exit 1
    fi

elif [ "$DATA_ONLY" = true ]; then
    print_header "DATA ONLY MODE - Syncing Data Only"
    print_status "This will sync data assuming schemas are already correct"
    
    run_data_sync "normal"
    if [ $? -eq 0 ]; then
        echo ""
        print_success "Data sync completed successfully!"
        print_status "Data is now synchronized"
    else
        print_error "Data sync failed!"
        exit 1
    fi

elif [ "$FIX_SCHEMAS" = true ]; then
    print_header "FIX SCHEMAS MODE - Fix Schemas and Sync Data"
    print_status "This will fix schema issues and then sync data"
    
    print_step "Step 1: Fixing schema mismatches..."
    run_schema_sync "fix"
    if [ $? -eq 0 ]; then
        echo ""
        print_step "Step 2: Syncing data with corrected schemas..."
        run_data_sync "normal"
        if [ $? -eq 0 ]; then
            echo ""
            print_success "Complete sync completed successfully!"
            print_status "Both schemas and data are now synchronized"
        else
            print_error "Data sync failed after schema fix!"
            exit 1
        fi
    else
        print_error "Schema fix failed!"
        exit 1
    fi

else
    print_header "FULL SYNC MODE - Complete Synchronization"
    print_status "This will perform a complete sync (schema + data)"
    
    print_step "Step 1: Analyzing and fixing schemas..."
    run_schema_sync "fix"
    if [ $? -eq 0 ]; then
        echo ""
        print_step "Step 2: Syncing data with corrected schemas..."
        run_data_sync "normal"
        if [ $? -eq 0 ]; then
            echo ""
            print_success "Complete sync completed successfully!"
            print_status "Database is now fully synchronized"
        else
            print_error "Data sync failed after schema fix!"
            exit 1
        fi
    else
        print_error "Schema sync failed!"
        exit 1
    fi
fi

echo ""
print_header "Workflow Summary"
print_success "All operations completed successfully!"
print_status "Your database is now synchronized with the remote source" 