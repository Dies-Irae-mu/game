"""
One-time script to clean up and re-initialize the watch_notifier script.

This script deletes any existing watch_notifier scripts to ensure a clean slate.
Run this with:
    evennia run utils.cleanup_watch_script
"""

from evennia.scripts.models import ScriptDB
from evennia import DefaultScript

def cleanup_watch_system():
    """Clean up all watch_notifier scripts"""
    print("Cleaning up watch_notifier scripts...")
    
    # Find and delete all watch_notifier scripts
    scripts = ScriptDB.objects.filter(db_key="watch_notifier")
    count = scripts.count()
    if count > 0:
        scripts.delete()
        print(f"Deleted {count} watch_notifier scripts.")
    else:
        print("No watch_notifier scripts found.")
    
    print("Cleanup complete. You should now restart the server.")
    print("After restarting, run 'evennia run utils.init_watch_system' to initialize the watch system.")

def main():
    cleanup_watch_system()

if __name__ == "__main__":
    main() 