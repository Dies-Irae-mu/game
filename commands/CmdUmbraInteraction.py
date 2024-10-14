from evennia.commands.default.muxcommand import MuxCommand

class CmdUmbraInteraction(MuxCommand):
    """
    Interact with the Umbra.

    Usage:
      +step
      +peek

    +step: Attempt to step sideways into or out of the Umbra.
    +peek: Look across the Gauntlet without entering the Umbra.
    """

    key = "+step"
    aliases = ["+peek"]
    locks = "cmd:all()"
    help_category = "Werewolf"

    def func(self):
        """Execute command."""
        if self.cmdstring == "+step":
            self.do_step()
        elif self.cmdstring == "+peek":
            self.do_peek()

    def do_step(self):
        """Handle stepping into or out of the Umbra."""
        if self.caller.tags.get("in_umbra", category="state"):
            if self.caller.location.return_from_umbra(self.caller):
                self.caller.msg("You have returned to the material world.")
            else:
                self.caller.msg("You failed to return from the Umbra.")
        else:
            if self.caller.location.step_sideways(self.caller):
                self.caller.msg("You have stepped sideways into the Umbra.")
            else:
                self.caller.msg("You failed to step sideways into the Umbra.")

    def do_peek(self):
        """Handle peeking across the Gauntlet."""
        if self.caller.tags.get("in_umbra", category="state"):
            self.caller.msg("You're already in the Umbra. Use +step to return to the material world.")
        else:
            result = self.caller.location.peek_umbra(self.caller)
            self.caller.msg(result)
