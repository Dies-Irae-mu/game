"""
Custom channel command for Dies Irae.
"""
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.ansi import strip_ansi
from evennia.comms.models import ChannelDB
from evennia.utils.evtable import EvTable
from evennia.utils.utils import make_iter, class_from_module
from evennia.utils.logger import log_trace, log_err
from evennia.locks.lockhandler import LockException
from django.conf import settings
from evennia.utils import create

CHANNEL_DEFAULT_TYPECLASS = settings.BASE_CHANNEL_TYPECLASS

class CustomCmdChannel(MuxCommand):
    """
    channel[/switches] [channel] [= message]
    The commands to join and leave a channel are:
    channel/sub [channel] = [alias]. Note that you MUST put in an alias.
    channel/unsub [channel]

    switches:
      /list       - show all channels you are subscribed to
      /all        - show all available channels
      /sub        - subscribe to channel(s)
      /unsub      - unsubscribe from channel(s)
      /alias      - set alias(es) for a channel
      /unalias    - remove an alias
      /who        - show who is subscribed to a channel
      /history    - show channel history
      /mute       - mute a channel
      /unmute     - unmute a channel
      /create     - create a new channel (staff only)
      /destroy    - remove a channel (staff only)
      /desc       - set channel description (staff only)
      /lock       - add lock strings to a channel (staff only)
      /unlock     - remove lock strings from a channel (staff only)
      /ban       - ban user from channel (staff only)
      /unban     - remove ban from user (staff only)
      /boot      - remove user from channel (staff only)
      /view       - show detailed channel information (staff only)
      /purge      - purge all channel aliases

    Example:
      pub Hello!                  (using an alias)
      channel/sub public = pub    (set alias)
      channel/unsub public        (unsubscribe)
      channel/alias pub = public  (set alias)
      channel/unalias pub         (remove alias)
      channel/who public          (show subscribers)
      channel/history public      (show history)
      channel/mute public         (mute channel)
    """
    key = "channel"
    aliases = ["chan"]
    switch_options = ("list", "all", "sub", "unsub", "alias", "unalias", "who", 
                     "history", "mute", "unmute", "create", "destroy", "desc", 
                     "lock", "unlock", "ban", "unban", "boot", "purge", "view")
    channel_class = ChannelDB
    help_category = "Communications"

    def add_channel_alias(self, caller, channel, aliases):
        """Helper method to add channel aliases."""
        aliases = [alias.strip() for alias in aliases.split(';') if alias.strip()]
        added_aliases = []
        for alias in aliases:
            # Add the command substitution using the correct nick template format
            # Format: "alias $1" = "channel channelname = $1"
            caller.nicks.add(f"{alias} $1", f"channel {channel.key} = $1", category="inputline")
            added_aliases.append(alias)
        return added_aliases
    
    def remove_channel_alias(self, caller, alias):
        """Helper method to remove a specific channel alias."""
        # Remove both the simple and template formats
        caller.nicks.remove(f"{alias} $1", category="inputline")
        caller.nicks.remove(alias, category="channel")  # Clean up any old format aliases
    
    def remove_channel_aliases(self, caller, channel):
        """Helper method to remove all aliases for a channel."""
        nicks = caller.nicks.get(category="inputline")
        if nicks:
            for nick in nicks:
                try:
                    # Check if this nick is for our channel
                    if f"channel {channel.key} =" in nick[1]:  # nick[1] is the template
                        # Get the base alias from the pattern
                        alias = nick[0].split()[0]  # Get base alias without $1
                        self.remove_channel_alias(caller, alias)
                except (IndexError, TypeError):
                    continue
    
    def create_channel(self, channelname, typeclass=None, description=None):
        """Create a new channel."""
        typeclass = typeclass or CHANNEL_DEFAULT_TYPECLASS
        try:
            # Validate channel name
            if not channelname or not channelname.strip():
                raise ValueError("Channel name cannot be empty")
                
            # Check if channel already exists
            existing = self.channel_class.objects.filter(db_key__iexact=channelname.strip()).first()
            if existing:
                raise ValueError(f"Channel '{channelname}' already exists")
                
            # Create the channel using the correct method
            channel = create.create_channel(channelname.strip(), typeclass=typeclass, desc=description)
                
            if not channel:
                raise RuntimeError(f"Failed to create channel '{channelname}'")
                
            return channel, None
            
        except ValueError as ve:
            log_err(f"Channel creation error: {str(ve)}")
            return None, str(ve)
        except Exception as e:
            log_trace(f"Unexpected error creating channel '{channelname}': {str(e)}")
            return None, f"Unexpected error creating channel: {str(e)}"
    
    def handle_history(self, channel, index=None):
        """Show channel history."""
        history = channel.db.history or []
        if not history:
            self.msg(f"No history available for channel {channel.key}.")
            return
        
        if index is not None:
            try:
                index = int(index)
                if 0 <= index < len(history):
                    msg = history[index]
                    self.msg(f"History entry {index} for {channel.key}:\n{msg}")
                else:
                    self.msg(f"Index {index} is out of range for channel history.")
            except ValueError:
                self.msg("History index must be a number.")
        else:
            # Show last 20 messages by default
            self.msg(f"\nLast {min(20, len(history))} messages in {channel.key}:")
            for i, msg in enumerate(history[-20:]):
                self.msg(f"{len(history)-20+i}: {msg}")
    
    def handle_mute(self, channels, mute=True):
        """Mute or unmute channels."""
        caller = self.caller
        result = []
        for channel in channels:
            if not channel.subscriptions.has(caller):
                result.append(f"You are not subscribed to {channel.key}.")
                continue
            
            if mute:
                if channel.db.muted and caller in channel.db.muted:
                    result.append(f"You have already muted {channel.key}.")
                else:
                    if not channel.db.muted:
                        channel.db.muted = []
                    channel.db.muted.append(caller)
                    result.append(f"You have muted {channel.key}.")
            else:
                if not channel.db.muted or caller not in channel.db.muted:
                    result.append(f"You haven't muted {channel.key}.")
                else:
                    channel.db.muted.remove(caller)
                    result.append(f"You have unmuted {channel.key}.")
        
        self.msg("\n".join(result))
    
    def handle_ban(self, channels, target, reason=None, quiet=False, unban=False):
        """Ban or unban a user from channels."""
        caller = self.caller
        result = []
        
        for channel in channels:
            if not channel.access(caller, "control"):
                result.append(f"You don't have permission to ban from {channel.key}.")
                continue
            
            if unban:
                if target not in channel.banlist:
                    result.append(f"{target.key} is not banned from {channel.key}.")
                else:
                    channel.unban(target)
                    if not quiet:
                        channel.msg(f"{target.key} was unbanned from {channel.key} by {caller.key}.")
                    result.append(f"Unbanned {target.key} from {channel.key}.")
            else:
                if target in channel.banlist:
                    result.append(f"{target.key} is already banned from {channel.key}.")
                else:
                    channel.ban(target)
                    if not quiet:
                        msg = f"{target.key} was banned from {channel.key} by {caller.key}"
                        if reason:
                            msg += f" (reason: {reason})"
                        channel.msg(msg)
                    result.append(f"Banned {target.key} from {channel.key}.")
        
        self.msg("\n".join(result))
    
    def handle_boot(self, channels, target, reason=None, quiet=False):
        """Boot a user from channels."""
        caller = self.caller
        result = []
        
        for channel in channels:
            if not channel.access(caller, "control"):
                result.append(f"You don't have permission to boot from {channel.key}.")
                continue
            
            if not channel.subscriptions.has(target):
                result.append(f"{target.key} is not subscribed to {channel.key}.")
                continue
            
            channel.subscriptions.remove(target)
            if not quiet:
                msg = f"{target.key} was booted from {channel.key} by {caller.key}"
                if reason:
                    msg += f" (reason: {reason})"
                channel.msg(msg)
            result.append(f"Booted {target.key} from {channel.key}.")
        
        self.msg("\n".join(result))

    def search_channel(self, channelname, exact=False, handle_errors=True):
        """
        Search for a channel without checking permissions.
        
        Args:
            channelname (str): Name to search for.
            exact (bool, optional): Require exact name match.
            handle_errors (bool, optional): Show error messages.
            
        Returns:
            list: List of matching channels.
        """
        channelname = channelname.strip()
        
        # First try exact match
        channels = list(self.channel_class.objects.filter(db_key__iexact=channelname))
        if channels:
            return channels
            
        if not exact:
            # Try inexact match
            channels = list(self.channel_class.objects.filter(db_key__icontains=channelname))
            if channels:
                return channels
            
            # Try aliases
            channels = list(self.channel_class.objects.filter(
                db_tags__db_key__iexact=channelname,
                db_tags__db_tagtype__iexact="alias"
            ))
            if channels:
                return channels
            
        if handle_errors:
            self.msg(f"No channel found matching '{channelname}'.")
        return []

    def parse(self):
        """
        Custom parsing to handle channel aliases.
        """
        super().parse()
        
        # If this is called via an alias, treat it as a message
        if not self.switches and self.args:
            # Check if this is a channel alias
            nicks = self.caller.nicks.get(category="inputline")
            if nicks:
                for nick in nicks:
                    try:
                        alias = nick[0].split()[0]  # Get base alias without $1
                        if alias.lower() == self.cmdname.lower():
                            # Get channel name from template
                            channel_name = nick[1].split()[1]  # "channel Public = $1" -> "Public"
                            # Convert alias format to channel message format
                            self.lhs = channel_name
                            self.rhs = self.args.strip()
                            self.args = f"{self.lhs}={self.rhs}"
                            self.switches = []  # Clear any switches
                            return
                    except (IndexError, AttributeError):
                        continue

    def list_channels(self, all_channels=False):
        """List channels available to the caller."""
        caller = self.caller
        channels = self.channel_class.objects.all()
        
        if not all_channels:
            # Only show subscribed channels
            channels = [chan for chan in channels if chan.subscriptions.has(caller)]
            if not channels:
                self.msg("You are not subscribed to any channels. Use |wchannel/all|n to see all available channels.")
                return
        else:
            # When showing all channels, filter by those the caller can access via listen lock
            channels = [chan for chan in channels if chan.access(caller, "listen")]
            if not channels:
                self.msg("No channels available.")
                return
        
        # Check if caller is staff
        is_staff = caller.check_permstring("Developer") or caller.check_permstring("Admin")
        
        if is_staff:
            table = EvTable(
                "|C#|n",
                "|wSub|n",
                "|wChannel|n",
                "|wID|n",
                "|wLocks|n",
                "|wAliases|n",
                "|wDesc|n",
                table=None,
                border="header",
                width=78,
                pad_width=0
            )
            # Set individual column widths for staff view
            table.reformat_column(0, width=3)  # Index
            table.reformat_column(1, width=4)  # Sub
            table.reformat_column(2, width=15)  # Channel name
            table.reformat_column(3, width=6)  # ID
            table.reformat_column(4, width=15)  # Locks
            table.reformat_column(5, width=12)  # Aliases
            table.reformat_column(6, width=23)  # Description
        else:
            table = EvTable(
                "|C#|n",
                "|wSub|n",
                "|wChannel|n",
                "|wAliases|n",
                "|wDesc|n",
                table=None,
                border="header",
                width=78,
                pad_width=0
            )
            # Set individual column widths for regular view
            table.reformat_column(0, width=3)  # Index
            table.reformat_column(1, width=4)  # Sub
            table.reformat_column(2, width=20)  # Channel name
            table.reformat_column(3, width=15)  # Aliases
            table.reformat_column(4, width=36)  # Description
        
        for i, chan in enumerate(channels, 1):
            subscribed = "|gY|n" if chan.subscriptions.has(caller) else "|rN|n"
            aliases = [alias.strip() for alias in chan.aliases.all()]
            alias_str = ",".join(aliases) if aliases else ""
            
            # Truncate description and add ellipsis if too long
            desc = chan.db.desc or ""
            if len(desc) > 20:
                desc = desc[:17] + "..."
            
            if is_staff:
                # Format locks string to be more concise
                locks_str = str(chan.locks)
                if len(locks_str) > 12:
                    locks_str = locks_str[:9] + "..."
                
                table.add_row(
                    f"|C{i}|n",
                    subscribed,
                    f"|w{chan.key}|n",
                    f"|c#{chan.id}|n",
                    f"|y{locks_str}|n",
                    f"|b{alias_str}|n",
                    desc
                )
            else:
                table.add_row(
                    f"|C{i}|n",
                    subscribed,
                    f"|w{chan.key}|n",
                    f"|b{alias_str}|n",
                    desc
                )
        
        header = "|wAvailable Channels|n" if all_channels else "|wYour Channel Subscriptions|n"
        if is_staff:
            header += " |y(Staff View)|n"
        
        self.msg(f"\n{header}:")
        self.msg("-" * 78)
        self.msg(table)
        self.msg("-" * 78)

    def purge_all_channel_aliases(self, caller):
        """THE PURGE"""
        # get every nick
        all_nicks = caller.nicks.all()
        
        # remove those nicks
        for nick in all_nicks:
            try:
                if nick.db_category in ("channel", "inputline", "inputcmd"):
                    # Remove the nick using the handler to ensure proper cleanup
                    caller.nicks.remove(nick.db_key, category=nick.db_category)
            except Exception:
                continue
        
        # where all my nicks at
        caller.nicks.get(return_obj=True)
    
    def func(self):
        """
        Main function for channel command.
        """
        caller = self.caller
        args = self.args.strip() if self.args else ""

        if not args and not self.switches:
            # No args, no switches - show help
            caller.msg(self.__doc__)
            return

        # Staff-only switches check
        staff_switches = ["create", "destroy", "desc", "lock", "unlock", "ban", "unban", "boot", "view"]
        if any(switch in self.switches for switch in staff_switches):
            if not caller.check_permstring("Builder"):
                caller.msg("You must have |wBuilder|n or higher permission to use this command.")
                return

        if "create" in self.switches:
            # Create a new channel
            if not args:
                caller.msg("Usage: channel/create <channelname>[;alias;alias...] [= description]")
                return
                
            if not caller.check_permstring("Developer") and not caller.check_permstring("Admin"):
                caller.msg("You don't have permission to create channels.")
                return

            typeclass = CHANNEL_DEFAULT_TYPECLASS
            if "=" in args:
                channeldef, description = [part.strip() for part in args.split("=", 1)]
            else:
                channeldef, description = args, ""
                
            # Handle multiple channel definitions (with aliases)
            if channeldef:
                channelname, *aliases = channeldef.split(";")
                channel, error = self.create_channel(channelname.strip(), typeclass, description)
                
                if channel:
                    # Add any aliases
                    if aliases:
                        added = self.add_channel_alias(caller, channel, ";".join(aliases))
                        if added:
                            caller.msg(f"Added aliases for {channel.key}: {', '.join(added)}")
                    caller.msg(f"Created channel {channel.key}")
                else:
                    caller.msg(f"Could not create channel {channelname}: {error}")
                return
                
            caller.msg("You must supply a valid channel name.")
            return

        if not self.args and not self.switches:
            # No args - show channels you are subscribed to
            self.list_channels()
            return

        if "sub" in self.switches:
            if not self.args:
                self.msg("Usage: channel/sub <channel> [= alias[;alias...]]")
                return
            channels = self.search_channel(self.lhs, exact=False)
            if not channels:
                return
            channel = channels[0]
            
            # Check listen lock before allowing subscription
            if not channel.access(caller, "listen"):
                self.msg(f"You don't have permission to subscribe to {channel.key}.")
                return
            
            was_subscribed = channel.subscriptions.has(caller)
            if not was_subscribed:
                channel.subscriptions.add(caller)
            
            # Always set aliases, even if already subscribed
            # First remove any existing aliases for this channel
            self.remove_channel_aliases(caller, channel)
            
            # Add aliases if provided, otherwise use default
            if self.rhs:
                aliases = self.add_channel_alias(caller, channel, self.rhs)
                alias_msg = f"Aliases set: {', '.join(aliases)}"
            else:
                alias = channel.key[:3].lower()
                self.add_channel_alias(caller, channel, alias)
                alias_msg = f"Default alias '{alias}' was set"
            
            if was_subscribed:
                self.msg(f"Already subscribed to {channel.key}. {alias_msg}.")
            else:
                self.msg(f"Subscribed to {channel.key}. {alias_msg}.")
            return

        # Handle message sending
        if not self.switches and self.lhs and self.rhs:
            channels = self.search_channel(self.lhs, exact=False)
            if not channels:
                return
            channel = channels[0]
            
            # Check both subscription and send permission
            if not channel.subscriptions.has(caller):
                self.msg(f"You are not subscribed to {channel.key}. Use channel/sub {channel.key} to subscribe.")
                return
                
            # Check send lock
            if not channel.access(caller, "send"):
                self.msg(f"You don't have permission to send messages to {channel.key}.")
                return
            
            # Send the message
            message = self.rhs
            if message:
                channel.msg(message, senders=caller)
                
                # Store in history if enabled
                if hasattr(channel, 'db') and channel.db.history is not None:
                    if not channel.db.history:
                        channel.db.history = []
                    channel.db.history.append(f"[{channel.key}] {caller.key}: {message}")
                    # Keep only last 50 messages
                    channel.db.history = channel.db.history[-50:]
            return

        if self.switches:
            switch = self.switches[0].lower()
            
            if switch in ("list", "all"):
                self.list_channels(all_channels=(switch == "all"))
                return
            
            elif switch == "destroy":
                if not self.lhs:
                    self.msg("Usage: channel/destroy channelname [= reason]")
                    return
                channels = self.search_channel(self.lhs)
                if not channels:
                    return
                channel = channels[0]
                
                if not channel.access(caller, "control"):
                    self.msg("You don't have permission to destroy this channel.")
                    return
                
                reason = self.rhs if self.rhs else "Channel destroyed."
                channel.msg(reason)
                channel.delete()
                self.msg(f"Channel {channel.key} was destroyed.")
                return
            
            elif switch == "desc":
                if not self.rhs:
                    self.msg("Usage: channel/desc channelname = description")
                    return
                channels = self.search_channel(self.lhs)
                if not channels:
                    return
                channel = channels[0]
                
                if not channel.access(caller, "control"):
                    self.msg("You don't have permission to modify this channel.")
                    return
                
                channel.db.desc = self.rhs
                self.msg(f"Description of channel {channel.key} set to: {self.rhs}")
                return
            
            elif switch in ("lock", "unlock"):
                if not self.rhs:
                    self.msg(f"Usage: channel/{switch} channelname = lockstring")
                    return
                channels = self.search_channel(self.lhs)
                if not channels:
                    return
                channel = channels[0]
                
                if not channel.access(caller, "control"):
                    self.msg("You don't have permission to modify this channel.")
                    return
                
                try:
                    if switch == "lock":
                        channel.locks.add(self.rhs)
                        self.msg(f"Added lock {self.rhs} to channel {channel.key}")
                    else:
                        channel.locks.remove(self.rhs)
                        self.msg(f"Removed lock {self.rhs} from channel {channel.key}")
                except LockException as e:
                    self.msg(str(e))
                return
            
            elif switch == "unalias":
                if not self.args:
                    self.msg("Usage: channel/unalias <alias>")
                    return
                self.remove_channel_alias(caller, self.args)
                self.msg(f"Removed alias '{self.args}' if it existed.")
                return
            
            elif switch == "history":
                if not self.lhs:
                    self.msg("Usage: channel/history channelname [= index]")
                    return
                channels = self.search_channel(self.lhs)
                if not channels:
                    return
                channel = channels[0]
                
                if not channel.access(caller, "listen"):
                    self.msg("You don't have permission to view this channel's history.")
                    return
                
                self.handle_history(channel, self.rhs)
                return
            
            elif switch in ("mute", "unmute"):
                if not self.args:
                    self.msg(f"Usage: channel/{switch} channelname[,channelname,...]")
                    return
                
                channel_names = [name.strip() for name in self.args.split(",")]
                channels = []
                for name in channel_names:
                    found = self.search_channel(name)
                    if found:
                        channels.extend(found)
                
                if channels:
                    self.handle_mute(channels, mute=(switch == "mute"))
                return
            
            elif switch in ("ban", "unban"):
                if not self.rhs:
                    if switch == "ban" and self.lhs:
                        # Show ban list for channel
                        channels = self.search_channel(self.lhs)
                        if not channels:
                            return
                        channel = channels[0]
                        if not channel.access(caller, "control"):
                            self.msg("You don't have permission to view bans.")
                            return
                        banlist = channel.banlist
                        if banlist:
                            self.msg(f"Bans for {channel.key}:")
                            for banned in banlist:
                                self.msg(f"- {banned.key}")
                        else:
                            self.msg(f"No bans on {channel.key}")
                        return
                    self.msg(f"Usage: channel/{switch} channelname[,channelname,...] = target [: reason]")
                    return
                
                channel_names = [name.strip() for name in self.lhs.split(",")]
                channels = []
                for name in channel_names:
                    found = self.search_channel(name)
                    if found:
                        channels.extend(found)
                
                if not channels:
                    return
                
                target_name = self.rhs
                reason = None
                if ":" in target_name:
                    target_name, reason = [part.strip() for part in target_name.split(":", 1)]
                
                target = caller.search(target_name)
                if not target:
                    return
                
                quiet = "quiet" in self.switches
                self.handle_ban(channels, target, reason, quiet, unban=(switch == "unban"))
                return
            
            elif switch == "boot":
                if not self.rhs:
                    self.msg("Usage: channel/boot channelname[,channelname,...] = target [: reason]")
                    return
                
                channel_names = [name.strip() for name in self.lhs.split(",")]
                channels = []
                for name in channel_names:
                    found = self.search_channel(name)
                    if found:
                        channels.extend(found)
                
                if not channels:
                    return
                
                target_name = self.rhs
                reason = None
                if ":" in target_name:
                    target_name, reason = [part.strip() for part in target_name.split(":", 1)]
                
                target = caller.search(target_name)
                if not target:
                    return
                
                quiet = "quiet" in self.switches
                self.handle_boot(channels, target, reason, quiet)
                return
            
            elif switch == "who":
                if not self.lhs:
                    self.msg("Usage: channel/who <channel>")
                    return
                channels = self.search_channel(self.lhs, exact=False)
                if not channels:
                    return
                channel = channels[0]
                who_list = [sub.key for sub in channel.subscriptions.all()]
                if who_list:
                    self.msg(f"Subscribers on channel {channel.key}:")
                    self.msg("\n".join(f"  {subscriber}" for subscriber in who_list))
                else:
                    self.msg(f"No subscribers on channel {channel.key}.")
                return
                
            elif switch == "alias":
                if not self.rhs:
                    self.msg("Usage: channel/alias <channel>=<alias>[;<alias>...]")
                    return
                channels = self.search_channel(self.lhs, exact=False)
                if not channels:
                    return
                channel = channels[0]
                if not channel.subscriptions.has(caller):
                    self.msg(f"You are not subscribed to channel {channel.key}. Use channel/sub {channel.key} to subscribe.")
                    return
                # Add the aliases
                aliases = self.add_channel_alias(caller, channel, self.rhs)
                self.msg(f"Channel aliases set: {', '.join(aliases)} now point to channel {channel.key}")
                return
                
            elif switch == "unsub":
                if not self.args:
                    self.msg("Usage: channel/unsub channelname[,channelname,...]")
                    return
                
                channel_names = [name.strip() for name in self.args.split(",")]
                result = []
                
                for name in channel_names:
                    channels = self.search_channel(name)
                    if not channels:
                        result.append(f"No channel found matching '{name}'.")
                        continue
                    
                    channel = channels[0]
                    if not channel.subscriptions.has(caller):
                        result.append(f"You are not subscribed to {channel.key}.")
                        continue
                    
                    # First remove aliases, then remove subscription
                    self.remove_channel_aliases(caller, channel)
                    channel.subscriptions.remove(caller)
                    result.append(f"Unsubscribed from {channel.key}.")
                
                self.msg("\n".join(result))
                return
            
            elif switch == "purge":
                # New command to purge all channel aliases
                self.purge_all_channel_aliases(caller)
                self.msg("Purged all channel aliases.")
                return

            elif switch == "view":
                if not self.lhs:
                    self.msg("Usage: channel/view channelname")
                    return
                self.handle_view(self.lhs)
                return

    def handle_view(self, channelname):
        """Show detailed channel information for staff."""
        caller = self.caller
        
        # Check staff permissions
        if not caller.check_permstring("Developer") and not caller.check_permstring("Admin"):
            caller.msg("You don't have permission to view detailed channel information.")
            return
            
        # Try to find by ID first if it starts with #
        if channelname.startswith('#'):
            try:
                chan_id = int(channelname[1:])
                channel = self.channel_class.objects.filter(id=chan_id).first()
            except ValueError:
                channel = None
        else:
            # Otherwise search by name
            channels = self.search_channel(channelname, exact=False)
            channel = channels[0] if channels else None
            
        if not channel:
            caller.msg(f"No channel found matching '{channelname}'.")
            return
            
        # Build detailed view
        header = f"|wDetailed Information for Channel: |c{channel.key}|n (|y#{channel.id}|n)"
        caller.msg("\n" + header)
        caller.msg("-" * 78)
        
        # Basic Info
        caller.msg(f"|wDescription:|n {channel.db.desc or 'No description set.'}")
        
        # Locks
        caller.msg(f"\n|wLock Strings:|n")
        lock_definition = str(channel.locks)
        if lock_definition:
            # Split the lock string into individual locks
            lock_list = lock_definition.split(';')
            for lock in lock_list:
                if ':' in lock:
                    locktype, lockstr = lock.split(':', 1)
                    caller.msg(f"  |y{locktype.strip()}:|n {lockstr.strip()}")
                else:
                    caller.msg(f"  {lock.strip()}")
            
            # Show available WoD lock functions
            caller.msg("\n|wAvailable WoD Lock Functions:|n")
            caller.msg("  |yCharacter Type:|n has_type(type)")
            caller.msg("  |yVampire:|n has_clan(clan)")
            caller.msg("  |yWerewolf:|n has_tribe(tribe), has_auspice(auspice)")
            caller.msg("  |yMage:|n has_tradition(tradition), has_convention(convention)")
            caller.msg("  |yChangeling:|n has_kith(kith), has_court(court)")
            caller.msg("  |yGeneral:|n has_splat(splat)")
            caller.msg("\n|wExample Lock String:|n")
            caller.msg("  listen:has_type(Vampire) and has_clan(Ventrue)")
        else:
            caller.msg("  No locks set")
        
        # Aliases
        aliases = [alias.strip() for alias in channel.aliases.all()]
        alias_str = ", ".join(aliases) if aliases else "None"
        caller.msg(f"\n|wAliases:|n {alias_str}")
        
        # Subscription Info
        subs = channel.subscriptions.all()
        sub_count = len(subs)
        caller.msg(f"\n|wSubscribers:|n {sub_count} total")
        
        # Show online/offline status for subscribers
        online_subs = [sub for sub in subs if sub.sessions.count()]
        offline_subs = [sub for sub in subs if not sub.sessions.count()]
        
        if online_subs:
            caller.msg("|wOnline:|n")
            for sub in online_subs:
                caller.msg(f"  |g{sub.key}|n")
        
        if offline_subs:
            caller.msg("|wOffline:|n")
            for sub in offline_subs:
                caller.msg(f"  |r{sub.key}|n")
        
        # Muted Users
        if hasattr(channel, 'db') and channel.db.muted:
            muted = channel.db.muted
            if muted:
                caller.msg(f"\n|wMuted Users:|n")
                for user in muted:
                    caller.msg(f"  |r{user.key}|n")
        
        # Ban List
        if hasattr(channel, 'banlist') and channel.banlist:
            caller.msg(f"\n|wBanned Users:|n")
            for banned in channel.banlist:
                caller.msg(f"  |r{banned.key}|n")
        
        caller.msg("-" * 78)

class CmdNotifications(MuxCommand):
    """
    Manage your login notification preferences.
    
    Usage:
        @notifications          - Show current notification settings
        @notifications/on      - Enable all notifications
        @notifications/off     - Disable all notifications
        @notifications <type> on|off  - Toggle specific notification type
        
    Available notification types: mail, jobs, bbs
    
    Examples:
        @notifications         - View current settings
        @notifications/off     - Disable all notifications
        @notifications mail off - Disable only mail notifications
        @notifications jobs on  - Enable job notifications
    """
    
    key = "@notifications"
    aliases = ["@notify"]
    locks = "cmd:all()"
    help_category = "Settings"
    
    def func(self):
        """Handle the command."""
        if not self.args and not self.switches:
            # Display current settings
            settings = self.caller.notification_settings
            status = []
            for ntype in ["mail", "jobs", "bbs"]:
                enabled = "✓" if settings[ntype] else "✗"
                status.append(f"{ntype.capitalize()}: {enabled}")
            
            if settings["all"]:
                self.caller.msg("|wAll notifications are currently disabled.|n")
            else:
                self.caller.msg("|wNotification Settings:|n\n" + "\n".join(status))
            return
            
        if "on" in self.switches:
            # Enable all notifications by setting "all" to False
            self.caller.set_notification_pref("all", False)
            # Then explicitly enable each notification type
            for ntype in ["mail", "jobs", "bbs"]:
                self.caller.set_notification_pref(ntype, True)
            self.caller.msg("|gAll notifications enabled.|n")
            return
            
        if "off" in self.switches:
            self.caller.set_notification_pref("all", True)
            self.caller.msg("|rAll notifications disabled.|n")
            return
            
        if self.args:
            args = self.args.strip().lower().split()
            if len(args) != 2:
                self.caller.msg("Usage: @notifications <type> on|off")
                return
                
            ntype, setting = args
            if ntype not in ["mail", "jobs", "bbs"]:
                self.caller.msg("Invalid notification type. Choose from: mail, jobs, bbs")
                return
                
            if setting not in ["on", "off"]:
                self.caller.msg("Setting must be either 'on' or 'off'")
                return
                
            enabled = (setting == "on")
            self.caller.set_notification_pref(ntype, enabled)
            status = "enabled" if enabled else "disabled"
            self.caller.msg(f"|w{ntype.capitalize()} notifications {status}.|n") 