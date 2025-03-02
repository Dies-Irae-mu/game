"""
Staff commands for Dies Irae.
"""
from evennia.commands.default.muxcommand import MuxCommand
from commands.CmdSelfStat import CmdSelfStat
from world.wod20th.models import Stat

class CmdStaffStat(CmdSelfStat):
    """
    Staff command to set stats on players, bypassing normal restrictions.

    Usage:
      +staffstat <character>=<stat>[(<instance>)]/<category>:<value>
      +staffstat <character>=<stat>:<value>

    Examples:
      +staffstat Bob=Strength/Physical:3
      +staffstat Bob=Strength:3        (same as above)
      +staffstat Jane=Status(Camarilla)/Background:2
      +staffstat Mike=Path of Enlightenment:Road of Heaven
      +staffstat Sarah=Nature:Architect

    This command allows staff to set stats on other characters, bypassing normal
    restrictions like character approval status and validation limits.
    """

    key = "+staffstat"
    aliases = ["staffstat"]
    locks = "cmd:perm(Admin) or perm(Builder)"
    help_category = "Staff"

    def parse(self):
        """Parse the command arguments for staff usage."""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +staffstat <character>=<stat>[(<instance>)]/<category>:<value>")
            return

        try:
            # Split into character and stat parts
            character_name, stat_args = self.args.split("=", 1)
            self.target_name = character_name.strip()

            # Handle the colon syntax
            if ':' in stat_args:
                stat_part, value = stat_args.split(':', 1)
                # If there's a category specified
                if '/' in stat_part:
                    stat_name, category = stat_part.split('/', 1)
                    # Handle instance if present
                    if '(' in stat_name and ')' in stat_name:
                        base_name, instance = stat_name.split('(', 1)
                        self.stat_name = base_name.strip()
                        self.instance = instance.rstrip(')').strip()
                    else:
                        self.stat_name = stat_name.strip()
                        self.instance = None
                    self.category = category.strip()
                else:
                    # No category specified
                    if '(' in stat_part and ')' in stat_part:
                        base_name, instance = stat_part.split('(', 1)
                        self.stat_name = base_name.strip()
                        self.instance = instance.rstrip(')').strip()
                    else:
                        self.stat_name = stat_part.strip()
                        self.instance = None
                    self.category = None
                self.value_change = value.strip()

                # If no category was specified but we have a stat name, try to detect the category
                if self.stat_name and not self.category:
                    # Try to find the stat in the database
                    stat = Stat.objects.filter(name__iexact=self.stat_name).first()
                    if stat:
                        self.category = stat.category
                        self.stat_type = stat.stat_type
                    else:
                        # If not found in database, try to detect from common categories
                        if self.stat_name.lower() in ['strength', 'dexterity', 'stamina']:
                            self.category = 'attributes'
                            self.stat_type = 'physical'
                        elif self.stat_name.lower() in ['charisma', 'manipulation', 'appearance']:
                            self.category = 'attributes'
                            self.stat_type = 'social'
                        elif self.stat_name.lower() in ['perception', 'intelligence', 'wits']:
                            self.category = 'attributes'
                            self.stat_type = 'mental'

        except Exception as e:
            self.caller.msg(f"|rError parsing command: {str(e)}|n")
            self.stat_name = None

    def validate_stat_value(self, stat_name: str, value: str, category: str = None, stat_type: str = None) -> tuple:
        """Override validation to always return valid for staff."""
        # Return (is_valid, error_message, corrected_value)
        return True, "", value

    def func(self):
        """Execute the command with staff privileges."""
        if not self.args:
            self.caller.msg(self.__doc__)
            return

        # Search for target character
        target = self.caller.search(self.target_name, typeclass='typeclasses.characters.Character')
        if not target:
            return
        
        # Store the original caller
        original_caller = self.caller
        
        try:
            # Temporarily set the caller to the target for stat manipulation
            self.caller = target

            # Call parent's func() to handle the actual stat setting
            super().func()

            # Log the change and notify players
            if hasattr(self, 'stat_name') and self.stat_name:
                # Construct the stat description
                stat_desc = self.stat_name
                if hasattr(self, 'category') and self.category:
                    stat_desc += f" ({self.category}"
                    if hasattr(self, 'stat_type') and self.stat_type:
                        stat_desc += f".{self.stat_type}"
                    stat_desc += ")"

                # Log message for staff
                log_msg = f"{original_caller.name} set {target.name}'s {stat_desc}"
                if hasattr(self, 'value_change') and self.value_change:
                    log_msg += f" to {self.value_change}"
                original_caller.msg(f"|gSuccess: {log_msg}|n")

                # Notify the target player if they're connected
                if target.has_account and target.sessions.count():
                    target.msg(f"|w{original_caller.name} adjusted your {self.stat_name} to {self.value_change}.|n")

        finally:
            # Restore the original caller
            self.caller = original_caller 