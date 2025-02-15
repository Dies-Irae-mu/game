from evennia import default_cmds
from evennia.utils import utils
from world.wod20th.models import Stat

class CmdPump(default_cmds.MuxCommand):
    """
    Boost physical attributes using blood points.

    Usage:
      +pump <attribute>=<amount>

    Examples:
      +pump strength=2
      +pump dexterity=1
      +pump stamina=3

    This command allows vampires to temporarily boost their physical attributes
    (Strength, Dexterity, or Stamina) by spending blood points. Each point of
    blood increases the chosen attribute by one, up to a maximum of 10.

    The boost lasts for one hour of in-game time.
    """

    key = "+pump"
    aliases = ["pump"]
    locks = "cmd:all()"
    help_category = "Vampire"

    def func(self):
        caller = self.caller

        # Check if the character is a vampire
        splat = caller.get_stat('other', 'splat', 'Splat', temp=False)
        if splat != 'Vampire':
            caller.msg("Only vampires can use this power.")
            return

        if not self.args or "=" not in self.args:
            caller.msg("Usage: +pump <attribute>=<amount>")
            return

        attribute, amount = self.args.split("=")
        attribute = attribute.strip().lower()
        amount = amount.strip()

        valid_attributes = ["strength", "dexterity", "stamina"]
        if attribute not in valid_attributes:
            caller.msg(f"Invalid attribute. Choose from: {', '.join(valid_attributes)}")
            return

        try:
            amount = int(amount)
        except ValueError:
            caller.msg("The amount must be a number.")
            return

        if amount <= 0:
            caller.msg("The amount must be a positive number.")
            return

        # Get the current blood pool value
        current_blood = caller.get_stat('pools', 'dual', 'Blood', temp=True)
        if current_blood < amount:
            caller.msg(f"You don't have enough blood. Current blood: {current_blood}")
            return

        # Get current attribute value
        current_value = caller.get_stat('attributes', 'physical', attribute.capitalize(), temp=True)
        if current_value is None:
            caller.msg(f"Error: Could not find {attribute} value.")
            return

        try:
            current_value = int(current_value)
        except ValueError:
            caller.msg(f"Error: Current {attribute} value is not a number.")
            return

        # Calculate new value, capped at 10
        new_value = min(current_value + amount, 10)
        actual_increase = new_value - current_value

        if actual_increase == 0:
            caller.msg(f"Your {attribute.capitalize()} is already at maximum (10).")
            return

        # Decrease blood pool
        new_blood = current_blood - actual_increase
        caller.set_stat('pools', 'dual', 'Blood', new_blood, temp=True)

        # Increase attribute (temporary value only)
        caller.set_stat('attributes', 'physical', attribute.capitalize(), new_value, temp=True)

        # Schedule the attribute to return to normal after 1 hour
        utils.delay(3600, self._remove_boost, attribute, actual_increase)

        caller.msg(f"You spend {actual_increase} blood point{'s' if actual_increase > 1 else ''} to boost your {attribute.capitalize()} to {new_value} for one hour.")

    def _remove_boost(self, attribute, amount):
        """Remove the attribute boost after the duration."""
        # Get current temporary value
        current_value = self.caller.get_stat('attributes', 'physical', attribute.capitalize(), temp=True)
        if current_value is None:
            return

        # Get permanent value
        perm_value = self.caller.get_stat('attributes', 'physical', attribute.capitalize(), temp=False)
        if perm_value is None:
            return

        # Calculate new value, ensuring it doesn't go below permanent value
        new_value = max(current_value - amount, perm_value)
        
        # Set new temporary value
        self.caller.set_stat('attributes', 'physical', attribute.capitalize(), new_value, temp=True)
        self.caller.msg(f"Your {attribute.capitalize()} returns to normal ({new_value}).")