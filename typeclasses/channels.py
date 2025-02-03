"""
Custom channel class for Dies Irae.
"""
from evennia.comms.comms import DefaultChannel
from evennia.utils.ansi import strip_ansi
from evennia.utils.utils import make_iter, logger
from evennia.comms.models import ChannelDB

class Channel(DefaultChannel):
    """
    Custom channel class that handles ANSI-colored channel names better.
    """
    
    @classmethod
    def search_channel(cls, searchdata, exact=True, ignore_perms=True):
        """
        Search for a channel, stripping ANSI codes from the search.
        
        Args:
            searchdata (str): Search criterion - the key to search for.
            exact (bool, optional): Require exact name match. Defaults to True.
            ignore_perms (bool, optional): Whether to ignore permissions during search.
                                         Defaults to True.
            
        Returns:
            matches (list): List of found channel matches
        """
        # Strip ANSI from searchdata and make it case-insensitive
        searchdata = strip_ansi(searchdata).strip()
        
        # Debug output
        print(f"Searching for channel: '{searchdata}'")
        
        try:
            # Try direct lookup first
            chan = ChannelDB.objects.get(db_key__iexact=searchdata)
            print(f"Found channel by direct lookup: {chan.key}")
            return [chan]
        except ChannelDB.DoesNotExist:
            print(f"No exact match found for '{searchdata}'")
            
            # Try searching by alias
            alias_matches = ChannelDB.objects.filter(db_tags__db_key__iexact=searchdata, 
                                                   db_tags__db_tagtype__iexact="alias")
            if alias_matches:
                print(f"Found matches by alias: {[c.key for c in alias_matches]}")
                return alias_matches
                
            if not exact:
                # Try partial matches
                partial_matches = ChannelDB.objects.filter(db_key__icontains=searchdata)
                if partial_matches:
                    print(f"Found partial matches: {[c.key for c in partial_matches]}")
                    return partial_matches
                    
                # Try partial alias matches
                alias_partial = ChannelDB.objects.filter(db_tags__db_key__icontains=searchdata,
                                                       db_tags__db_tagtype__iexact="alias")
                if alias_partial:
                    print(f"Found partial alias matches: {[c.key for c in alias_partial]}")
                    return alias_partial
            
            print("No channel found matching '{}'".format(searchdata))
            return []

    def msg(self, message, senders=None, bypass_mute=False, **kwargs):
        """
        Send message to channel, causing it to be distributed to all non-muted
        subscribed users of that channel who have permission to listen.

        Args:
            message (str): The message to send.
            senders (Object, Account or list, optional): If not given, there is
                no way to associate one or more senders with the message.
            bypass_mute (bool, optional): If set, always send, regardless of
                individual mute-state of subscriber.
            **kwargs (any): This will be passed on to all hooks.
        """
        senders = make_iter(senders) if senders else []
        if self.send_to_online_only:
            receivers = self.subscriptions.online()
        else:
            receivers = self.subscriptions.all()
            
        # Filter receivers based on permissions and mute status, ensuring uniqueness
        seen_receivers = set()
        filtered_receivers = []
        for receiver in receivers:
            # Skip if we've already processed this receiver
            if receiver.id in seen_receivers:
                continue
                
            if ((bypass_mute or receiver not in self.mutelist)
                and self.access(receiver, "listen")):
                filtered_receivers.append(receiver)
                seen_receivers.add(receiver.id)

        send_kwargs = {"senders": senders, "bypass_mute": bypass_mute, **kwargs}

        # pre-send hook
        message = self.at_pre_msg(message, **send_kwargs)
        if message in (None, False):
            return

        for receiver in filtered_receivers:
            try:
                recv_message = receiver.at_pre_channel_msg(message, self, **send_kwargs)
                if recv_message in (None, False):
                    continue

                receiver.channel_msg(recv_message, self, **send_kwargs)
                receiver.at_post_channel_msg(recv_message, self, **send_kwargs)

            except Exception:
                logger.log_trace(f"Error sending channel message to {receiver}.")

        # post-send hook
        self.at_post_msg(message, **send_kwargs) 