"""
Command for setting and viewing Fae descriptions of rooms.
"""
from evennia.commands.default.muxcommand import MuxCommand

class CmdRoomFaeDesc(MuxCommand):
    """
    Set or view a room's Fae description.
    Restricted to builders and higher.

    Usage:
      +roomfaedesc                - View room's Fae description
      +roomfaedesc <description> - Set room's Fae description
      +roomfaedesc/clear         - Clear room's Fae description

    Examples:
      +roomfaedesc The walls pulse with ancient faerie magic.
      +roomfaedesc/clear
    """

    key = "+roomfaedesc"
    aliases = ["+rfaedesc"]
    locks = "cmd:perm(Builder)"
    help_category = "Building and Housing"

    def func(self):
        """Execute command."""
        caller = self.caller

        if "clear" in self.switches:
            self.caller.location.db.fae_desc = ""
            caller.msg("Room's Fae description cleared.")
            return

        if not self.args:
            # View room's Fae description
            fae_desc = self.caller.location.db.fae_desc
            if fae_desc:
                caller.msg("|mRoom's Fae Description:|n\n%s" % fae_desc)
            else:
                caller.msg("This room has no special Fae aspect set.")
            return

        # Set room's Fae description
        self.caller.location.db.fae_desc = self.args
        caller.msg("Room's Fae description set.") 