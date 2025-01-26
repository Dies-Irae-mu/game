from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.utils import time_format

class CmdUmbraInteraction(MuxCommand):
    """
    Interact with the Umbra.

    Usage:
      +step [modifier]
      +peek
      +gauntlet/check

    +step: Attempt to step sideways into or out of the Umbra.
           Optional modifier (e.g. +step -2) for temporary difficulty adjustment
    +peek: Look across the Gauntlet without entering the Umbra.
           (Shifters only)
    +gauntlet/check: Check current Gauntlet difficulty
    """

    key = "+step"
    aliases = ["+peek", "+gauntlet"]
    locks = "cmd:all()"
    help_category = "Shifter"

    def func(self):
        """Execute command."""
        if not self.switches:
            if self.cmdstring == "+step":
                self.do_step()
            elif self.cmdstring == "+peek":
                # Check if the character is a Shifter before allowing peek
                if not hasattr(self.caller, 'is_shifter') or not self.caller.is_shifter():
                    self.caller.msg("Only Shifters can peek across the Gauntlet.")
                    return
                self.do_peek()
            return
            
        if "check" in self.switches:
            self.do_check_gauntlet()
            return

    def do_step(self):
        """Handle stepping into or out of the Umbra."""
        # If already in Umbra, just return to material world
        if self.caller.tags.get("in_umbra", category="state"):
            if self.caller.location.return_from_umbra(self.caller):
                self.caller.tags.remove("in_umbra", category="state")
                self.caller.tags.add("in_material", category="state")
                self.caller.msg("You have returned to the material world.")
            else:
                self.caller.msg("You failed to return from the Umbra.")
            return

        # Parse any modifier from the args
        temp_modifier = 0
        if self.args:
            try:
                temp_modifier = int(self.args.strip())
            except ValueError:
                self.caller.msg("Invalid modifier. Must be a number (e.g. +step -2)")
                return

        # Store current gauntlet modifier
        room = self.caller.location
        original_modifier = room.db.temp_gauntlet_modifier

        try:
            # Apply temporary modifier just for this attempt
            room.modify_gauntlet(temp_modifier)
            
            # Attempt to step sideways
            if room.step_sideways(self.caller):
                self.caller.tags.remove("in_material", category="state")
                self.caller.tags.add("in_umbra", category="state")
                self.caller.msg("You have stepped sideways into the Umbra.")
            else:
                self.caller.msg("You failed to step sideways into the Umbra.")
        finally:
            # Restore original modifier
            room.modify_gauntlet(original_modifier or 0)

    def do_peek(self):
        """Handle peeking across the Gauntlet."""
        if self.caller.tags.get("in_umbra", category="state"):
            self.caller.msg("You're already in the Umbra. Use +step to return to the material world.")
        else:
            # Get the peek result and handle any line breaks
            result = self.caller.location.peek_umbra(self.caller)
            if result:
                result = result.replace("%r", "\n").replace("\n\n", "\n")
            self.caller.msg(result)

    def do_check_gauntlet(self):
        """Check current Gauntlet difficulty."""
        room = self.caller.location
        current_difficulty = room.get_gauntlet_difficulty()
        msg = f"Current Gauntlet difficulty: {current_difficulty}"
        self.caller.msg(msg)
