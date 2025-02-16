"""
Package initialization for wod20th scripts.

This module handles the initialization of all maintenance scripts when the server starts.
"""
from evennia.scripts.scripts import DefaultScript
from evennia import logger, create_script
from world.wod20th.forms import create_shifter_forms
from world.wod20th.scripts.weekly_xp import WeeklyXPScript, start_xp_monitor
from world.wod20th.scripts.puppet_freeze import start_puppet_freeze_script

class ServerStartScript(DefaultScript):
    """Script to initialize all maintenance scripts when the server starts."""
    
    def at_script_creation(self):
        """Set up the initialization script."""
        self.key = "server_start_init"
        self.desc = "Initializes maintenance scripts and systems"
        self.persistent = False
        
    def at_start(self):
        """
        Called when script starts running.
        Initializes all necessary game systems and scripts.
        """
        try:
            logger.info("Initializing game systems...")
            
            # Initialize shifter forms
            try:
                create_shifter_forms()
                logger.info("Shifter forms initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing shifter forms: {e}")

            # Start XP monitoring system
            try:
                xp_monitor = start_xp_monitor()
                logger.info("XP monitor started successfully")
            except Exception as e:
                logger.error(f"Error starting XP monitor: {e}")

            # Start puppet freeze checking
            try:
                success, message = start_puppet_freeze_script()
                if success:
                    logger.info(message)
                else:
                    logger.warning(message)
            except Exception as e:
                logger.error(f"Error starting puppet freeze script: {e}")

            logger.info("Server initialization completed")

        except Exception as e:
            logger.error(f"Critical error during server initialization: {e}")
        finally:
            # This script only needs to run once at server start
            self.stop()

def start_all_scripts():
    """
    Function to be called from server config to start all scripts.
    This can be added to your server.conf or settings.py
    """
    try:
        create_script("world.wod20th.scripts.ServerStartScript")
    except Exception as e:
        logger.error(f"Error starting server initialization script: {e}")

# Auto-start all scripts when this module is imported
start_all_scripts() 