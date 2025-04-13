#!/usr/bin/env python
import os
import shutil
import sys
import subprocess

def get_staged_deletions():
    """Get list of files that are staged for deletion."""
    result = subprocess.run(['git', 'diff', '--cached', '--name-only', '--diff-filter=D'], 
                          capture_output=True, text=True)
    return result.stdout.strip().split('\n') if result.stdout.strip() else []

def main():
    # Create backup directory if it doesn't exist
    backup_dir = os.path.join('.git', 'sensitive_backups')
    os.makedirs(backup_dir, exist_ok=True)

    # Files to protect
    sensitive_files = [
        'server/conf/settings.py',
        'server/conf/secret_settings.py',
        'server/evennia.db3'
    ]

    # Check for staged deletions of sensitive files
    staged_deletions = get_staged_deletions()
    protected_deletions = [f for f in staged_deletions if f in sensitive_files]
    
    if protected_deletions:
        print("Error: Cannot commit deletion of sensitive files:")
        for file in protected_deletions:
            print(f"  - {file}")
        print("\nThese files are protected and cannot be deleted.")
        sys.exit(1)

    # Backup each file if it exists
    for file_path in sensitive_files:
        if os.path.exists(file_path):
            backup_path = os.path.join(backup_dir, os.path.basename(file_path) + '.backup')
            shutil.copy2(file_path, backup_path)
            print(f"Backed up {os.path.basename(file_path)}")

if __name__ == '__main__':
    main() 