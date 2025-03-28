"""
Command for setting and viewing Fae descriptions of characters.
"""
from evennia.commands.default.muxcommand import MuxCommand

class CmdFaeDesc(MuxCommand):
    """
    Set or view your own Fae description.
    Only Changelings and Kinain can use this command.

    Usage:
      +faedesc                - View your Fae description
      +faedesc <description> - Set your Fae description
      +faedesc/clear         - Clear your Fae description

    Examples:
      +faedesc A shimmer of fae glamour surrounds your form.
      +faedesc/clear
    """

    key = "+faedesc"
    aliases = ["+fdesc"]
    locks = "cmd:all()"
    help_category = "Changeling"

    def can_perceive_fae(self, character):
        """
        Check if a character can perceive the Dreaming.
        """
        if not character:
            return False
            
        # Check if the character has stats
        if not hasattr(character, 'db') or not character.db.stats:
            return False

        # Get the character's splat
        splat = (character.db.stats.get('other', {})
                              .get('splat', {})
                              .get('Splat', {})
                              .get('perm', ''))
                
        # Check if the character is a Changeling
        if splat == "Changeling":
            return True
            
        # Check if the character is Kinain
        if (splat == "Mortal+" and 
            character.db.stats.get('identity', {})
                          .get('lineage', {})
                          .get('Mortal+ Type', {})
                          .get('perm', '') == "Kinain"):
            return True
            
        return False

    def func(self):
        """Execute command."""
        caller = self.caller

        # Check if the user is a Changeling or Kinain
        if not self.can_perceive_fae(caller):
            caller.msg("Only those with Fae blood can perceive or set Fae descriptions.")
            return

        # Handle clearing description
        if "clear" in self.switches:
            if hasattr(caller, 'db'):
                caller.db.fae_desc = ""
                caller.msg("Your Fae description cleared.")
            return

        if not self.args:
            # View own Fae description
            if hasattr(caller, 'db') and caller.db.fae_desc:
                caller.msg("|mYour Fae Description:|n\n%s" % caller.db.fae_desc)
            else:
                caller.msg("You have no special Fae aspect set.")
            return

        # Set own Fae description
        if hasattr(caller, 'db'):
            caller.db.fae_desc = self.args
            caller.msg("Your Fae description set.")