from evennia import default_cmds

class CmdUnfindable(default_cmds.MuxCommand):
    """
    Set yourself as unfindable or findable.

    Usage:
      +unfindable [on|off]

    When set to 'on', you won't appear in the regular +where list.
    When set to 'off', you'll appear as normal.
    Using the command without an argument will toggle your current state.
    """

    key = "+unfindable"
    aliases = ["unfindable"]
    locks = "cmd:all()"
    help_category = "Utility Commands"

    def func(self):
        if not self.args:
            # Toggle current state
            self.caller.db.unfindable = not self.caller.db.unfindable
        elif self.args.lower() == "on":
            self.caller.db.unfindable = True
        elif self.args.lower() == "off":
            self.caller.db.unfindable = False
        else:
            self.caller.msg("Usage: unfindable [on|off]")
            return

        if self.caller.db.unfindable:
            self.caller.msg("You are now unfindable.")
        else:
            self.caller.msg("You are now findable.")