from evennia import default_cmds, search_channel

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
        # Get the LookingForRP channel with ANSI codes
        channels = search_channel("|035LookingForRP|n")
        if not channels:
            self.caller.msg("Error: LookingForRP channel not found.")
            return
            
        # Get the first channel from the QuerySet
        rp_channel = channels[0]
            
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
            # Add to channel if not already subscribed
            if not rp_channel.subscriptions.has(self.caller):
                rp_channel.connect(self.caller)
                # Set up the 'rp' alias for the channel
                self.caller.execute_cmd('channel/alias |035LookingForRP|n = rp')
            self.caller.msg("You are now marked as looking for RP and have joined the LookingForRP channel (use 'rp' to chat).")
        else:
            # Remove from channel if subscribed
            if rp_channel.subscriptions.has(self.caller):
                # Remove the 'rp' alias
                self.caller.execute_cmd('channel/unalias rp')
                rp_channel.disconnect(self.caller)
            self.caller.msg("You are no longer marked as looking for RP and have left the LookingForRP channel.") 