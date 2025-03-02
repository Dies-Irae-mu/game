"""
Server startstop hooks

This module contains functions called by Evennia at various
points during its startup, reload and shutdown sequence.
"""

from evennia.utils import logger
from django.conf import settings
import os
import sys
import traceback
from evennia.utils.logger import log_info, log_err, log_trace
from evennia.utils.utils import class_from_module

def log_startup(msg):
    """Helper function to ensure startup messages are visible."""
    print(f"[STARTUP] {msg}")  # Direct print for immediate feedback
    log_info(msg)  # Also log to Evennia's system

def cleanup_scripts():
    """Helper function to clean up scripts."""
    from evennia.scripts.models import ScriptDB
    
    log_startup("Starting script cleanup...")
    
    try:
        # Clean up ALL server start scripts (both old and new paths)
        scripts_to_clean = ScriptDB.objects.filter(
            db_typeclass_path__contains="ServerStartScript"
        ) | ScriptDB.objects.filter(
            db_key="server_start_init"
        )
        
        if scripts_to_clean.exists():
            count = scripts_to_clean.count()
            scripts_to_clean.delete()
            log_startup(f"Cleaned up {count} server start scripts")

        # Clean up ALL weekly XP scripts
        xp_scripts_to_clean = ScriptDB.objects.filter(
            db_typeclass_path__contains="WeeklyXP"
        ) | ScriptDB.objects.filter(
            db_key__contains="weekly_xp"
        )
        
        if xp_scripts_to_clean.exists():
            count = xp_scripts_to_clean.count()
            xp_scripts_to_clean.delete()
            log_startup(f"Cleaned up {count} WeeklyXP scripts")

        # Clean up ALL puppet freeze scripts
        puppet_scripts_to_clean = ScriptDB.objects.filter(
            db_typeclass_path__contains="PuppetFreezeScript"
        ) | ScriptDB.objects.filter(
            db_key__contains="puppet_freeze"
        )
        
        if puppet_scripts_to_clean.exists():
            count = puppet_scripts_to_clean.count()
            puppet_scripts_to_clean.delete()
            log_startup(f"Cleaned up {count} Puppet Freeze scripts")
        
        log_startup("Script cleanup completed")
    except Exception as e:
        log_startup(f"Error during script cleanup: {e}")
        print(traceback.format_exc())
        return False
    return True

def initialize_systems():
    """Helper function to initialize game systems."""
    try:
        log_startup("Starting system initialization...")
        
        # Add the game directory to Python path if not already there
        game_dir = settings.GAME_DIR
        if game_dir not in sys.path:
            sys.path.insert(0, game_dir)
            log_startup(f"Added {game_dir} to Python path")
        
        # Try to import and verify script classes exist
        weekly_xp_path = "world.wod20th.scripts.weekly_xp.WeeklyXPScript"
        puppet_freeze_path = "world.wod20th.scripts.puppet_freeze.PuppetFreezeScript"
        
        try:
            WeeklyXPScript = class_from_module(weekly_xp_path)
            PuppetFreezeScript = class_from_module(puppet_freeze_path)
            log_startup("Successfully verified script classes")
        except Exception as e:
            log_startup(f"Failed to verify script classes: {e}")
            print(traceback.format_exc())
            return False
        
        from world.wod20th.forms import create_shifter_forms
        from world.wod20th.utils.init_db import load_stats
        from world.wod20th.locks import LOCK_FUNCS
        from evennia.locks import lockfuncs
        
        # Get the absolute path to the data directory
        data_dir = os.path.join(settings.GAME_DIR, 'data')
        
        create_shifter_forms()
        load_stats(data_dir)
        log_startup("Game data initialized successfully")

        # Register lock functions
        for name, func in LOCK_FUNCS.items():
            setattr(lockfuncs, name, func)
        log_startup("Lock functions registered")
        
        return True
        
    except Exception as e:
        log_startup(f"Failed to initialize game systems: {e}")
        print(traceback.format_exc())
        return False

def create_maintenance_scripts():
    """Helper function to create maintenance scripts."""
    from evennia import create_script
    from evennia.scripts.models import ScriptDB
    
    log_startup("Starting maintenance script creation...")
    
    try:
        # Create fresh WeeklyXP script
        log_startup("Creating WeeklyXP script...")
        script = create_script(
            "world.wod20th.scripts.weekly_xp.WeeklyXPScript",
            key="weekly_xp_awards",
            interval=604800,
            persistent=True,
            autostart=True,
            desc="Awards weekly XP to characters"
        )
        if not script:
            log_startup("Failed to create WeeklyXP script - script is None")
            return False
        if not script.is_active:
            log_startup("WeeklyXP script created but not active")
            return False
        log_startup("WeeklyXP script created successfully")

        # Create fresh Puppet Freeze script
        log_startup("Creating PuppetFreeze script...")
        script = create_script(
            "world.wod20th.scripts.puppet_freeze.PuppetFreezeScript",
            key="puppet_freeze_check",
            interval=86400,
            persistent=True,
            autostart=True,
            desc="Checks for and freezes inactive puppets"
        )
        if not script:
            log_startup("Failed to create PuppetFreeze script - script is None")
            return False
        if not script.is_active:
            log_startup("PuppetFreeze script created but not active")
            return False
        log_startup("PuppetFreeze script created successfully")
            
        log_startup("All maintenance scripts created successfully")
        return True
            
    except Exception as e:
        log_startup(f"Error creating maintenance scripts: {e}")
        print(traceback.format_exc())
        return False

def ensure_scripts_exist():
    """Ensure all required scripts exist and are running."""
    from evennia.scripts.models import ScriptDB
    
    log_startup("Checking for existing scripts...")
    
    try:
        # Check for required scripts
        weekly_xp = ScriptDB.objects.filter(db_key="weekly_xp_awards").first()
        puppet_freeze = ScriptDB.objects.filter(db_key="puppet_freeze_check").first()
        
        if not weekly_xp or not puppet_freeze:
            log_startup("Some required scripts are missing, creating them...")
            if not cleanup_scripts():  # Clean up any partial scripts first
                log_startup("Failed to clean up existing scripts")
                return False
            return create_maintenance_scripts()
        else:
            log_startup("All required scripts exist")
            return True
    except Exception as e:
        log_startup(f"Error ensuring scripts exist: {e}")
        print(traceback.format_exc())
        return False

def at_server_init():
    """
    This is called first as the server is starting up, regardless of how.
    """
    log_startup("=== Server initialization started ===")

def at_server_start():
    """
    This is called every time the server starts up, regardless of how it was shut down.
    """
    log_startup("=== Server start sequence initiated ===")
    if not initialize_systems():
        log_startup("Failed to initialize systems")
        return
    if not ensure_scripts_exist():
        log_startup("Failed to ensure scripts exist")
        return
    log_startup("=== Server start sequence completed ===")

def at_server_cold_start():
    """
    This is called only when the server starts "cold", i.e. after a shutdown or a reset.
    """
    log_startup("=== Cold start detected ===")
    # Cold start handled by at_server_start()

def at_server_stop():
    """
    This is called just before the server is shut down, regardless
    of it is for a reload, reset or shutdown.
    """
    log_startup("=== Server stopping... ===")

def at_server_reload_start():
    """
    This is called only when server starts back up after a reload.
    """
    log_startup("=== Server reload started ===")
    # Reload handled by at_server_start()

def at_server_reload_stop():
    """
    This is called only time the server stops before a reload.
    """
    log_startup("=== Server reload stopping... ===")

def at_server_cold_stop():
    """
    This is called only when the server goes down due to a shutdown or reset.
    """
    log_startup("=== Server cold stop... ===")
