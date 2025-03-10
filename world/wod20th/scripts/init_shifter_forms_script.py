"""
Script to initialize shapeshifter forms in the database.
"""
from evennia import DefaultScript
from evennia.utils import logger
from world.wod20th.forms import create_shifter_forms

class InitShifterFormsScript(DefaultScript):
    """A script to initialize shapeshifter forms."""

    def at_script_creation(self):
        """Called when script is first created."""
        self.key = "init_shifter_forms"
        self.desc = "Initializes shapeshifter forms in the database"
        self.persistent = False

    def at_start(self):
        """Called when script starts running."""
        try:
            # Call the existing create_shifter_forms function
            create_shifter_forms()
            logger.log_info('Successfully initialized all shifter forms')
        except Exception as e:
            logger.log_err(f'Error initializing forms: {str(e)}')
            raise
        finally:
            # Always stop the script after running
            self.stop() 