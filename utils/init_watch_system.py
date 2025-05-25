"""
One-time initialization script for the watch system.

This script can be run once to initialize the watch_notifier script
and set up default watch attributes for all existing characters.

Run this with:
    evennia shell
    
And then:
    from utils import init_watch_system
    init_watch_system.main()
"""
from evennia import DefaultScript
from evennia.objects.models import ObjectDB
from evennia.scripts.models import ScriptDB
from evennia.utils.search import search_object
from typeclasses.characters import Character
import logging

# Initialize logger properly
log = logging.getLogger('evennia')

# Modified import path to use Evennia's import system
from evennia.utils.utils import class_from_module

def cleanup_watch_scripts():
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
    
    print("Cleanup complete.")

def init_watch_system():
    """Initialize the watch system for all existing characters."""
    print("Initializing watch system...")
    
    # First clean up any existing watch_notifier scripts
    cleanup_watch_scripts()
    
    # Get the WatchNotifier class dynamically
    try:
        WatchNotifier = class_from_module("typeclasses.scripts.watch_notifier.WatchNotifier")
    except Exception as e:
        print(f"Error importing WatchNotifier: {e}")
        return
    
    # Create the watch_notifier script
    try:
        print("Creating WatchNotifier script...")
        notifier = WatchNotifier.create(key="watch_notifier")
        notifier.start()
        print("WatchNotifier script created and started.")
    except Exception as e:
        print(f"Error creating WatchNotifier script: {e}")
        log.error(f"Error creating WatchNotifier script: {e}")
        return
    
    # Initialize default watch attributes for all characters
    try:
        characters = search_object(typeclass=Character)
        print(f"Initializing {len(characters)} characters...")
        
        for character in characters:
            # Skip non-character objects
            if not isinstance(character, Character):
                continue
                
            # Set default attributes if they don't exist
            if not character.attributes.has("watch_list"):
                character.attributes.add("watch_list", [])
                
            if not character.attributes.has("watch_active"):
                character.attributes.add("watch_active", True)
                
            if not character.attributes.has("watch_hidden"):
                character.attributes.add("watch_hidden", False)
                
            if not character.attributes.has("watch_permitted"):
                character.attributes.add("watch_permitted", [])
                
            if not character.attributes.has("watch_all"):
                character.attributes.add("watch_all", False)
                
            if not character.attributes.has("watch_blocking"):
                character.attributes.add("watch_blocking", [])
                
            if not character.attributes.has("watch_blocked_by"):
                character.attributes.add("watch_blocked_by", [])
                
            # Fix any existing watch data for consistency
            watch_list = character.attributes.get("watch_list")
            if watch_list:
                # Remove any duplicates and ensure list contains strings
                clean_list = []
                for entry in watch_list:
                    if isinstance(entry, str) and entry not in clean_list:
                        clean_list.append(entry)
                character.attributes.add("watch_list", clean_list)
        
        print("Watch system initialization complete.")
        print("Restart the server to ensure the watch notifier is working correctly.")
    except Exception as e:
        print(f"Error initializing characters: {e}")
        log.error(f"Error initializing characters: {e}")

# Entry point for evennia run
def main():
    init_watch_system()

if __name__ == "__main__":
    main() 