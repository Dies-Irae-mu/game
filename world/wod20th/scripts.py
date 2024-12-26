from evennia import DefaultScript
from world.wod20th.forms import create_shifter_forms

class InitShifterFormsScript(DefaultScript):
    """
    Script to initialize shifter forms when the server starts.
    """
    def at_script_creation(self):
        self.key = "init_shifter_forms"
        self.desc = "Initializes shifter forms in the database"
        self.persistent = False  # Only runs once when server starts

    def at_start(self):
        """Called when script starts running."""
        create_shifter_forms()
        self.stop()  # Stop the script after running 