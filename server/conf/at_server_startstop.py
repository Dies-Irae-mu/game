"""
Server startstop hooks

This module contains functions called by Evennia at various
points during its startup, reload and shutdown sequence.
"""

from evennia.utils import logger
from django.conf import settings
import os

def at_server_init():
    """
    This is called first as the server is starting up, regardless of how.
    """
    logger.log_info("Server initialization started")

def cleanup_scripts():
    """Helper function to clean up scripts."""
    from evennia.scripts.models import ScriptDB
    
    # Clean up ALL server start scripts (both old and new paths)
    scripts_to_clean = ScriptDB.objects.filter(
        db_typeclass_path__contains="ServerStartScript"
    ) | ScriptDB.objects.filter(
        db_key="server_start_init"
    )
    
    if scripts_to_clean.exists():
        count = scripts_to_clean.count()
        scripts_to_clean.delete()
        logger.log_info(f"Cleaned up {count} server start scripts")

    # Clean up ALL weekly XP scripts
    xp_scripts_to_clean = ScriptDB.objects.filter(
        db_typeclass_path__contains="WeeklyXP"
    ) | ScriptDB.objects.filter(
        db_key__contains="weekly_xp"
    )
    
    if xp_scripts_to_clean.exists():
        count = xp_scripts_to_clean.count()
        xp_scripts_to_clean.delete()
        logger.log_info(f"Cleaned up {count} WeeklyXP scripts")

    # Clean up ALL puppet freeze scripts
    puppet_scripts_to_clean = ScriptDB.objects.filter(
        db_typeclass_path__contains="PuppetFreezeScript"
    ) | ScriptDB.objects.filter(
        db_key__contains="puppet_freeze"
    )
    
    if puppet_scripts_to_clean.exists():
        count = puppet_scripts_to_clean.count()
        puppet_scripts_to_clean.delete()
        logger.log_info(f"Cleaned up {count} Puppet Freeze scripts")

def initialize_systems():
    """Helper function to initialize game systems."""
    try:
        from world.wod20th.forms import create_shifter_forms
        from world.wod20th.utils.init_db import load_stats
        from world.wod20th.locks import LOCK_FUNCS
        from evennia.locks import lockfuncs
        
        # Get the absolute path to the data directory
        data_dir = os.path.join(settings.GAME_DIR, 'data')
        
        create_shifter_forms()
        load_stats(data_dir)
        logger.log_info("Game data initialized successfully")

        # Register lock functions
        for name, func in LOCK_FUNCS.items():
            setattr(lockfuncs, name, func)
        logger.log_info("Lock functions registered")
        
    except ImportError as e:
        logger.log_err(f"Failed to initialize game systems: {e}")
        return False
    return True

def create_maintenance_scripts():
    """Helper function to create maintenance scripts."""
    from evennia import create_script
    
    try:
        # Create fresh WeeklyXP script
        script = create_script(
            "world.wod20th.scripts.weekly_xp.WeeklyXPScript",
            key="weekly_xp_awards",
            interval=604800,
            persistent=True,
            autostart=True,
            desc="Awards weekly XP to characters"
        )
        if script and script.is_active:
            logger.log_info("Created and started new WeeklyXP script")
        else:
            logger.log_err("Failed to create WeeklyXP script")

        # Create fresh Puppet Freeze script
        script = create_script(
            "world.wod20th.scripts.puppet_freeze.PuppetFreezeScript",
            key="puppet_freeze_check",
            interval=86400,
            persistent=True,
            autostart=True,
            desc="Checks for and freezes inactive puppets"
        )
        if script and script.is_active:
            logger.log_info("Created and started new Puppet Freeze script")
        else:
            logger.log_err("Failed to create Puppet Freeze script")
            
    except Exception as e:
        logger.log_err(f"Error creating maintenance scripts: {e}")
        return False
    return True

def at_server_start():
    """
    This is called every time the server starts up, regardless of how it was shut down.
    For reload/reset cases, we only clean up scripts here.
    """
    logger.log_info("Server start sequence initiated")
    cleanup_scripts()
    logger.log_info("Server start sequence completed")

def at_server_cold_start():
    """
    This is called only when the server starts "cold", i.e. after a shutdown or a reset.
    This is where we initialize systems and create scripts.
    """
    logger.log_info("Cold start sequence initiated")
    
    # Clean up any existing scripts first
    cleanup_scripts()
    
    # Initialize game systems
    if initialize_systems():
        # Only create scripts if initialization was successful
        create_maintenance_scripts()
    
    logger.log_info("Cold start sequence completed")

def at_server_stop():
    """
    This is called just before the server is shut down, regardless
    of it is for a reload, reset or shutdown.
    """
    logger.log_info("Server stopping...")

def at_server_reload_start():
    """
    This is called only when server starts back up after a reload.
    """
    logger.log_info("Server reloading...")

def at_server_reload_stop():
    """
    This is called only time the server stops before a reload.
    """
    pass

def at_server_cold_stop():
    """
    This is called only when the server goes down due to a shutdown or reset.
    """
    pass
