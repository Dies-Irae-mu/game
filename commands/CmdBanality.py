"""
Command for Changelings to modify their Banality rating.
"""
from evennia import Command
from evennia.utils import evtable

class CmdBanality(Command):
    """
    Set your character's Banality rating.
    
    Usage:
        +banality <value>
    
    Sets your character's Banality to the specified value (0-10).
    This command is only available to Changeling characters.
    """
    
    key = "+banality"
    locks = "cmd:attr(db.stats.other.splat.Splat.perm, 'Changeling')"
    help_category = "Changeling"
    
    def func(self):
        """Execute the command"""
        if not self.args:
            current = self.caller.get_stat('pools', 'dual', 'Banality', temp=False)
            self.caller.msg(f"Your current Banality rating is {current}.")
            return
            
        try:
            new_value = int(self.args.strip())
            if 0 <= new_value <= 10:
                # Initialize pools if needed
                if 'pools' not in self.caller.db.stats:
                    self.caller.db.stats['pools'] = {}
                if 'dual' not in self.caller.db.stats['pools']:
                    self.caller.db.stats['pools']['dual'] = {}
                
                self.caller.set_stat('pools', 'dual', 'Banality', new_value, temp=False)
                self.caller.set_stat('pools', 'dual', 'Banality', new_value, temp=True)
                self.caller.msg(f"Set Banality to {new_value}.")
            else:
                self.caller.msg("Error: Banality must be between 0 and 10.")
        except ValueError:
            self.caller.msg("Error: Please provide a number between 0 and 10.") 