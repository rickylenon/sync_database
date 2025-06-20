#!/usr/bin/env python3
"""
Database Sync Setup Script
Helps initialize configuration for new projects
"""

import os
import sys
import shutil
from pathlib import Path

def print_info(message):
    print(f"✅ {message}")

def print_warning(message):
    print(f"⚠️  {message}")

def print_error(message):
    print(f"❌ {message}")

def main():
    print("🚀 Database Sync Setup")
    print("=" * 50)
    
    # Check if template exists
    if not os.path.exists('config.template.py'):
        print_error("config.template.py not found!")
        print("This script should be run from the sync_database directory.")
        sys.exit(1)
    
    # Ask user for project name (config_*.py is required format)
    print("\nThis tool creates configuration files in the required 'config_*.py' format.")
    print("Examples: config_midas.py, config_nexportal.py, config_myproject.py")
    print()
    
    project_name = input("Enter project name for config_<PROJECT>.py: ").strip()
    if not project_name:
        print_error("Project name cannot be empty")
        sys.exit(1)
    
    # Validate project name (basic cleanup)
    project_name = project_name.lower().replace(' ', '_').replace('-', '_')
    config_file = f"config_{project_name}.py"
    
    # Check if config file already exists
    if os.path.exists(config_file):
        overwrite = input(f"\n{config_file} already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("Setup cancelled.")
            sys.exit(0)
    
    # Copy template to config file
    try:
        shutil.copy2('config.template.py', config_file)
        print_info(f"Created {config_file} from template")
    except Exception as e:
        print_error(f"Failed to create config file: {e}")
        sys.exit(1)
    
    # Show next steps
    print("\n" + "=" * 50)
    print("🎉 Setup complete! Next steps:")
    print(f"1. Edit {config_file} with your database settings:")
    print(f"   - SSH server details")
    print(f"   - Remote database connection")
    print(f"   - Local database connection")
    print(f"   - Tables to exclude")
    
    print(f"\n2. Add {config_file} to .gitignore:")
    print(f"   echo '{config_file}' >> .gitignore")
    
    print(f"\n3. Test your configuration:")
    print(f"   python sync_database.py --config {config_file} --dry-run")
    
    print(f"\n4. Run the actual sync when ready:")
    print(f"   python sync_database.py --config {config_file}")
    
    print(f"\n📝 Configuration file: {config_file}")
    print("🔒 Remember to never commit configuration files with credentials!")

if __name__ == "__main__":
    main() 