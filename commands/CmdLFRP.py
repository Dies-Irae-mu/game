from evennia import default_cmds

class CmdLFRP(default_cmds.MuxCommand):
    """
    Mark yourself as looking for roleplay opportunities.
    
    Usage:
      +lfrp         - Toggle your LFRP status
      +lfrp on      - Mark yourself as looking for RP
      +lfrp off     - Remove your LFRP status
    """
    
    key = "+lfrp"
    aliases = ["lfrp"]
    locks = "cmd:all()"
    help_category = "RP Commands"
    
    def func(self):
        if not self.args:
            # Toggle current status
            self.caller.db.lfrp = not self.caller.db.lfrp
        elif self.args.lower() == "on":
            self.caller.db.lfrp = True
        elif self.args.lower() == "off":
            self.caller.db.lfrp = False
        else:
            self.caller.msg("Usage: +lfrp [on|off]")
            return
            
        if self.caller.db.lfrp:
            self.caller.msg("You are now marked as looking for RP.")
        else:
            self.caller.msg("You are no longer marked as looking for RP.") 