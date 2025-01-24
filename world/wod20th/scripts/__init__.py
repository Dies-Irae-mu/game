"""
Package initialization for wod20th scripts.
"""
from evennia.scripts.scripts import DefaultScript
from world.wod20th.forms import create_shifter_forms

class InitShifterFormsScript(DefaultScript):
    """Script to initialize shifter forms when the server starts."""
    def at_script_creation(self):
        self.key = "init_shifter_forms"
        self.desc = "Initializes shifter forms in the database"
        self.persistent = False
        
    def at_start(self):
        """Called when script starts running."""
        try:
            create_shifter_forms()
        except Exception as e:
            print(f"Error initializing shifter forms: {e}")
        finally:
            self.stop() 