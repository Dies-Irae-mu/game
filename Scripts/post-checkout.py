#!/usr/bin/env python
import os
import shutil
import sys

def main():
    backup_dir = os.path.join('.git', 'sensitive_backups')
    
    # Files to protect
    sensitive_files = [
        ('server', 'conf', 'settings.py'),
        ('server', 'conf', 'secret_settings.py'),
        ('server', 'evennia.db3')
    ]

    # Restore each file if it doesn't exist
    for file_parts in sensitive_files:
        target_path = os.path.join(*file_parts)
        backup_path = os.path.join(backup_dir, os.path.basename(target_path) + '.backup')
        
        if not os.path.exists(target_path) and os.path.exists(backup_path):
            # Ensure target directory exists
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.copy2(backup_path, target_path)
            print(f"Restored {os.path.basename(target_path)} from backup")

if __name__ == '__main__':
    main() 