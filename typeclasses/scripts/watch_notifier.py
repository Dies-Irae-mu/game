"""
Watch Notification Script

This script hooks into the connection and disconnection events to notify people
who are watching the connecting/disconnecting character.
"""
from evennia import DefaultScript
from evennia.utils.utils import connected_players


class WatchNotifier(DefaultScript):
    """
    This script handles notifications for the +watch system.
    It should be set to run globally at server start.
    """
    def at_script_creation(self):
        """Set up the script"""
        self.key = "watch_notifier"
        self.desc = "Handles notifications for the +watch system"
        self.interval = None  # Not a timed script
        self.persistent = True

    def at_server_reload(self):
        """After a reload, make sure we're still subscribed to events"""
        self.subscribe_to_events()

    def at_server_start(self):
        """Subscribe to the connection events when the server starts"""
        self.subscribe_to_events()

#    def subscribe_to_events(self):
#        """Subscribe to connection and disconnection events"""
#        from evennia.server.sessionhandler import SESSIONS
#        SESSIONS.account_sessions.add_callback(
#            "session_connect", self.at_account_connect
#        )
#        SESSIONS.account_sessions.add_callback(
#            "session_disconnect", self.at_account_disconnect
#        )

    def at_account_connect(self, session, **kwargs):
        """
        Called when an account connects to the game.
        We need to notify anyone watching this character.
        """
        # First check if the session has a valid account and puppet
        account = session.account
        if not account or not account.puppet:
            return
            
        character = account.puppet
        
        # Check if the character is hidden
        if character.attributes.get("watch_hidden", False):
            # Get who is permitted to receive notifications despite hiding
            permitted = character.attributes.get("watch_permitted", [])
            
            # Only send notifications to those with permission
            self.notify_watchers(character, is_connecting=True, only_permitted=permitted)
        else:
            # Send notifications to all watchers
            self.notify_watchers(character, is_connecting=True)

    def at_account_disconnect(self, session, **kwargs):
        """
        Called when an account disconnects from the game.
        We need to notify anyone watching this character.
        """
        # First check if the session has a valid account and puppet
        account = session.account
        if not account or not account.puppet:
            return
            
        character = account.puppet
        
        # Check if the character is hidden
        if character.attributes.get("watch_hidden", False):
            # Get who is permitted to receive notifications despite hiding
            permitted = character.attributes.get("watch_permitted", [])
            
            # Only send notifications to those with permission
            self.notify_watchers(character, is_connecting=False, only_permitted=permitted)
        else:
            # Send notifications to all watchers
            self.notify_watchers(character, is_connecting=False)

    def notify_watchers(self, character, is_connecting=True, only_permitted=None):
        """
        Send notification to watchers about a character connection/disconnection.
        
        Args:
            character (Object): The character who connected/disconnected
            is_connecting (bool): True if connecting, False if disconnecting
            only_permitted (list): Optional list of character names who are permitted to
                                   receive notifications despite hiding
        """
        # Get the status message
        status = "connected to" if is_connecting else "disconnected from"
        
        # Iterate through all connected players to find watchers
        for account in connected_players():
            # Skip if no valid puppet or account
            if not account or not account.puppet:
                continue
                
            watcher = account.puppet
            
            # Skip if it's the same character
            if watcher == character:
                continue
                
            # Skip if watch system is deactivated
            if not watcher.attributes.get("watch_active", True):
                continue
                
            should_notify = False
            
            # Check if this watcher is watching all connections
            if watcher.attributes.get("watch_all", False):
                should_notify = True
            
            # Check if this character is on the watcher's watch list
            watch_list = watcher.attributes.get("watch_list", [])
            if character.key in watch_list:
                should_notify = True
                
            # If we're only notifying permitted watchers, check if this watcher is permitted
            if only_permitted is not None and watcher.key not in only_permitted:
                should_notify = False
                
            # Notify the watcher if appropriate
            if should_notify:
                watcher.msg(f"{character.key} has {status} the game.") 