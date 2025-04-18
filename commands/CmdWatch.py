"""
Watch command - tracks login/logout of friends
"""
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.utils import make_iter
from utils.search_helpers import search_character
from evennia.server.sessionhandler import SESSIONS
from evennia.server.signals import SIGNAL_OBJECT_POST_PUPPET, SIGNAL_OBJECT_POST_UNPUPPET
from django.dispatch import receiver

# Function to notify watchers when someone logs in or out
def notify_watchers(character, is_connected):
    """
    Notify players when someone they're watching connects or disconnects.
    
    Args:
        character (Object): The character connecting or disconnecting
        is_connected (bool): True if connecting, False if disconnecting
    """
    # Skip notification if the character is hidden or doesn't exist
    if not character or character.attributes.get("watch_hidden", False):
        return
        
    # Get all possible watchers (all accounts with puppets)
    from evennia.accounts.models import AccountDB
    for account in AccountDB.objects.filter(db_is_connected=True):
        # Skip if no puppets
        if not account.puppet:
            continue
            
        puppet = account.puppet
        
        # Skip if the puppet is the character connecting/disconnecting
        if puppet == character:
            continue
            
        # Check if the character is on the puppet's watch list
        if not puppet.attributes.has("watch_list") and not puppet.attributes.get("watch_all", False):
            continue
            
        watch_list = puppet.attributes.get("watch_list", [])
        watch_active = puppet.attributes.get("watch_active", True)
        watch_all = puppet.attributes.get("watch_all", False)
        watch_permitted = puppet.attributes.get("watch_permitted", [])
        
        # Skip if the watch system is turned off
        if not watch_active:
            continue
            
        # Check if the character is on the puppet's watch list or if watching all
        is_watching = character.key in watch_list or watch_all
        
        # Check if the character has hidden themselves but permitted this watcher
        if character.attributes.get("watch_hidden", False) and character.key not in watch_permitted:
            continue
            
        # If the character is being watched, send a notification
        if is_watching:
            status = "connected" if is_connected else "disconnected"
            puppet.msg(f"|g[Watch]|n {character.key} has {status}.")

# Register signal handlers
@receiver(SIGNAL_OBJECT_POST_PUPPET)
def _on_puppet(sender, **kwargs):
    """Called when a character is puppeted"""
    character = sender
    notify_watchers(character, True)

@receiver(SIGNAL_OBJECT_POST_UNPUPPET)
def _on_unpuppet(sender, **kwargs):
    """Called when a character is un-puppeted"""
    character = sender
    notify_watchers(character, False)

# Connect notification function to the appropriate hooks
def at_server_reload():
    """
    This is called when the server reloads. We need to re-attach our 
    notification functions to the appropriate signals.
    """
    # Signals are already connected via @receiver decorators
    pass

def on_account_login(session, **kwargs):
    """Called when an account attaches to a session (logs in)"""
    if session.puppet:
        notify_watchers(session.puppet, True)

def on_account_logout(session, **kwargs):
    """Called when an account detaches from a session (logs out)"""
    if session.puppet:
        notify_watchers(session.puppet, False)

class CmdWatch(MuxCommand):
    """
    Track login/logouts of your friends

    Usage:
      +watch            -- shows you who is connected that you are watching.
      +watch/on         -- turns on the watch code after it has been turned off.
      +watch/off        -- turns off the Watch without removing your list.
      +watch/who        -- displays everyone on your watch list and connect status.
      +watch/hide       -- hides you from the +watch.
      +watch/unhide     -- allows others to watch your logins and disconnects.
      +watch/per <name> -- permits <name> to see you while hiding.
      +watch/rem <name> -- blocks <name> from watching you.
      +watch/unblock <name> -- removes block preventing <name> from watching you.
      +watch/add <name> -- adds <name> to your watch list.
      +watch/del <name> -- removes <name> from your watch list.
      +watch/page <message> -- sends <message> as a page to those on your watch list.
      +watch/all on     -- allows you to watch all logins and disconnects.
      +watch/all off    -- prevents you from watching all logins and disconnects.
    
    The +watch system allows you to be notified when friends log in and out.
    Staff members cannot be added to watch lists.
    
    Using +watch/rem on someone will block them from adding you to their watch list.
    Use +watch/unblock to remove the block if you change your mind.
    """
    key = "+watch"
    aliases = ["watch"]
    help_category = "Comms"
    switch_options = (
        "on", "off", "who", "hide", "unhide", "per", "rem", "unblock",
        "add", "del", "page", "all"
    )

    def func(self):
        """Implement the command"""
        caller = self.caller
        args = self.args.strip()

        # Initialize watch attributes if they don't exist
        if not caller.attributes.has("watch_list"):
            caller.attributes.add("watch_list", [])
        if not caller.attributes.has("watch_active"):
            caller.attributes.add("watch_active", True)
        if not caller.attributes.has("watch_hidden"):
            caller.attributes.add("watch_hidden", False)
        if not caller.attributes.has("watch_permitted"):
            caller.attributes.add("watch_permitted", [])
        if not caller.attributes.has("watch_all"):
            caller.attributes.add("watch_all", False)
        if not caller.attributes.has("watch_blocking"):
            caller.attributes.add("watch_blocking", [])  # People I'm blocking
        if not caller.attributes.has("watch_blocked_by"):
            caller.attributes.add("watch_blocked_by", [])  # People blocking me

        # Get the current attributes
        watch_list = caller.attributes.get("watch_list")
        watch_active = caller.attributes.get("watch_active")
        watch_hidden = caller.attributes.get("watch_hidden")
        watch_permitted = caller.attributes.get("watch_permitted")
        watch_all = caller.attributes.get("watch_all")
        watch_blocking = caller.attributes.get("watch_blocking")
        watch_blocked_by = caller.attributes.get("watch_blocked_by")

        # Default command - show connected people you're watching
        if not self.switches:
            if not watch_active:
                self.msg("Your watch system is currently deactivated.")
                return
                
            if not watch_list and not watch_all:
                self.msg("You are not watching anyone. Use +watch/add <name> to add someone.")
                return
                
            # Show connected people from watch list
            connected_watching = []
            session_list = SESSIONS.get_sessions()
            for session in session_list:
                if not session.logged_in:
                    continue
                account = session.get_account()
                puppet = session.get_puppet()
                if puppet and any(puppet.key.lower() == watched.lower() for watched in watch_list):
                    connected_watching.append(puppet.key)
            
            if connected_watching:
                self.msg(f"Currently connected people you're watching: {', '.join(connected_watching)}")
            else:
                self.msg("None of the people you're watching are currently connected.")
            
            # If watch_all is enabled, show that too
            if watch_all:
                self.msg("You are currently watching ALL login/logout activity.")
            
            return

        # Turn watch on or off
        if "on" in self.switches:
            caller.attributes.add("watch_active", True)
            self.msg("Watch system activated. You will now receive notifications.")
            return
            
        if "off" in self.switches:
            caller.attributes.add("watch_active", False)
            self.msg("Watch system deactivated. You will no longer receive notifications.")
            return
            
        # Show entire watch list
        if "who" in self.switches:
            if not watch_list:
                self.msg("You are not watching anyone. Use +watch/add <name> to add someone.")
                return
                
            # Get connected status for everyone on the list
            session_list = SESSIONS.get_sessions()
            connected_names = []
            for session in session_list:
                if session.logged_in and session.get_puppet():
                    connected_names.append(session.get_puppet().key.lower())
            
            status_list = []
            for name in watch_list:
                connected = name.lower() in connected_names
                status = "Connected" if connected else "Offline"
                status_list.append(f"{name} ({status})")
                
            self.msg(f"Your watch list: {', '.join(status_list)}")
            
            # Show blocking info
            if watch_blocking:
                self.msg(f"You are blocking: {', '.join(watch_blocking)}")
                
            # Show blocked by info
            if watch_blocked_by:
                self.msg(f"You are blocked by: {', '.join(watch_blocked_by)}")
            
            # If watch_all is enabled, show that too
            if watch_all:
                self.msg("You are currently watching ALL login/logout activity.")
            
            return
            
        # Hide or unhide from others' watch lists
        if "hide" in self.switches:
            caller.attributes.add("watch_hidden", True)
            self.msg("You are now hidden from others' watch lists, except for those you specifically permit.")
            return
            
        if "unhide" in self.switches:
            caller.attributes.add("watch_hidden", False)
            self.msg("You are now visible to others' watch lists.")
            return
            
        # Add or remove specific permissions
        if "per" in self.switches:
            if not args:
                self.msg("You must specify someone to permit.")
                return
                
            target = search_character(caller, args)
            if not target:
                return
                
            # Check if the target is already permitted
            if target.key in watch_permitted:
                self.msg(f"{target.key} is already permitted to see you.")
                return
                
            # Add the target to the permitted list
            watch_permitted.append(target.key)
            caller.attributes.add("watch_permitted", watch_permitted)
            self.msg(f"{target.key} is now permitted to see you even while you're hidden.")
            return
            
        # Block someone from watching you
        if "rem" in self.switches:
            if not args:
                self.msg("You must specify someone to block from watching you.")
                return
                
            target = search_character(caller, args)
            if not target:
                return
                
            # Check if already blocking
            if target.key in watch_blocking:
                self.msg(f"You are already blocking {target.key} from watching you.")
                return
                
            # First remove ourselves from their watch list if present
            if not target.attributes.has("watch_list"):
                target.attributes.add("watch_list", [])
                
            target_watch_list = list(target.attributes.get("watch_list"))
            
            # Remove me from their watch list (case-insensitive)
            for i, name in enumerate(target_watch_list[:]):
                if name.lower() == caller.key.lower():
                    target_watch_list.remove(name)
                    target.msg(f"{caller.key} has blocked you from watching them.")
                    target.msg(f"{caller.key} has been removed from your watch list.")
            
            # Update their watch list
            target.attributes.add("watch_list", target_watch_list)
            
            # Now add me to their blocked-by list
            if not target.attributes.has("watch_blocked_by"):
                target.attributes.add("watch_blocked_by", [])
                
            target_blocked_by = list(target.attributes.get("watch_blocked_by"))
            
            # Add me to their blocked-by list (avoid duplicates)
            if caller.key not in target_blocked_by:
                target_blocked_by.append(caller.key)
                target.attributes.add("watch_blocked_by", target_blocked_by)
            
            # Add them to my blocking list
            watch_blocking.append(target.key)
            caller.attributes.add("watch_blocking", watch_blocking)
            
            # Confirm the block
            self.msg(f"You are now blocking {target.key} from watching you.")
            return
            
        # Remove block from someone
        if "unblock" in self.switches:
            if not args:
                self.msg("You must specify someone to unblock.")
                return
                
            target = search_character(caller, args)
            if not target:
                return
                
            # Check if not blocking
            if target.key not in watch_blocking:
                self.msg(f"You are not blocking {target.key}.")
                return
                
            # Remove them from my blocking list
            watch_blocking.remove(target.key)
            caller.attributes.add("watch_blocking", watch_blocking)
            
            # Remove me from their blocked-by list
            if target.attributes.has("watch_blocked_by"):
                target_blocked_by = list(target.attributes.get("watch_blocked_by"))
                if caller.key in target_blocked_by:
                    target_blocked_by.remove(caller.key)
                    target.attributes.add("watch_blocked_by", target_blocked_by)
                    target.msg(f"{caller.key} has unblocked you. You can now watch them.")
            
            # Confirm the unblock
            self.msg(f"You are no longer blocking {target.key} from watching you.")
            return
            
        # Add or remove from watch list
        if "add" in self.switches:
            if not args:
                self.msg("You must specify someone to add to your watch list.")
                return
                
            target = search_character(caller, args)
            if not target:
                return
                
            # Prevent watching yourself
            if target == caller:
                self.msg("You cannot add yourself to your own watch list.")
                return
                
            # Check if the target is staff
            if target.account and (target.account.check_permstring("Developer") or target.account.check_permstring("Admin")):
                self.msg("You cannot add staff members to your watch list.")
                return
                
            # Check if blocked by target
            if not target.attributes.has("watch_blocking"):
                target.attributes.add("watch_blocking", [])
            
            target_blocking = target.attributes.get("watch_blocking")
            
            if caller.key in target_blocking:
                self.msg(f"{target.key} has blocked you from watching them.")
                return
                
            # Add them to my blocked-by list if needed
            if target.key not in watch_blocked_by and caller.key in target_blocking:
                watch_blocked_by.append(target.key)
                caller.attributes.add("watch_blocked_by", watch_blocked_by)
                
            # Check if the target is already in the watch list
            if target.key in watch_list:
                self.msg(f"{target.key} is already on your watch list.")
                return
                
            # Add the target to the watch list
            watch_list.append(target.key)
            caller.attributes.add("watch_list", watch_list)
            self.msg(f"{target.key} has been added to your watch list.")
            return
            
        if "del" in self.switches:
            if not args:
                self.msg("You must specify someone to remove from your watch list.")
                return
                
            # Find a case-insensitive match
            found = False
            for name in watch_list[:]:
                if name.lower() == args.lower():
                    watch_list.remove(name)
                    found = True
            
            if not found:
                self.msg(f"{args} is not on your watch list.")
                return
                
            # Update the watch list
            caller.attributes.add("watch_list", watch_list)
            self.msg(f"{args} has been removed from your watch list.")
            return
            
        # Page everyone on the watch list
        if "page" in self.switches:
            if not args:
                self.msg("You must specify a message to send.")
                return
                
            if not watch_list:
                self.msg("You are not watching anyone. Use +watch/add <name> to add someone.")
                return
                
            # Get connected characters from the watch list
            connected_characters = []
            session_list = SESSIONS.get_sessions()
            for session in session_list:
                if not session.logged_in:
                    continue
                puppet = session.get_puppet()
                if puppet and any(puppet.key.lower() == watched.lower() for watched in watch_list):
                    connected_characters.append(puppet.key)
                    
            if not connected_characters:
                self.msg("None of the people you're watching are currently connected.")
                return
                
            # Format the message for the page command
            page_cmd = f"page {','.join(connected_characters)}={args}"
            caller.execute_cmd(page_cmd)
            return
            
        # Watch all login/logout activity
        if "all" in self.switches:
            if not args or args.lower() not in ["on", "off"]:
                self.msg("You must specify 'on' or 'off' with the +watch/all switch.")
                return
                
            if args.lower() == "on":
                caller.attributes.add("watch_all", True)
                self.msg("You will now be notified of ALL login/logout activity.")
            else:
                caller.attributes.add("watch_all", False)
                self.msg("You will no longer be notified of ALL login/logout activity.")
            return
            
        # If we get here, it's an invalid switch
        self.msg("Unknown switch. Type 'help +watch' for valid switches.") 

# Make sure our hooks are connected when the module is loaded
at_server_reload() 