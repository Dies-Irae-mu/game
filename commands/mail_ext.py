"""
Extended mail commands for diesirae
"""

import re
from evennia.comms.models import Msg
from evennia.utils import evtable, create, datetime_format, make_iter
from evennia.utils.logger import log_err
from evennia.contrib.game_systems.mail.mail import CmdMail, CmdMailCharacter
from typeclasses.characters import Character
from evennia import AccountDB, ObjectDB, default_cmds

"""
Mail extension for Dies Irae.

This module extends the Evennia mail system to store sent messages and
allow viewing them with the /sent switch.
"""

class CmdMailExtended(CmdMail):
    """
    Communicate with others by sending mail.

    Usage:
      @mail                - Displays all the mail an account has in their inbox
      @mail <#>           - Displays a specific message
      @mail <accounts>=<subject>/<message>
              - Sends a message to the comma separated list of accounts.
      @mail/delete <#>    - Deletes a specific message
      @mail/forward <account list>=<#>[/<Message>]
              - Forwards an existing message to the specified list of accounts,
                original message is delivered with optional Message prepended.
      @mail/reply <#>=<message>
              - Replies to a message #. Prepends message to the original
                message text.
      @mail/sent          - Shows all messages you've sent
      @mail/sent <#>      - Shows a specific sent message
      @mail/debug         - Shows detailed debugging information about all messages

    Switches:
      delete  - deletes a message
      forward - forward a received message to another object with an optional message attached.
      reply   - Replies to a received message, appending the original message to the bottom.
      sent    - View messages you've sent
      debug   - Show detailed message debugging information
    """

    def send_mail(self, recipients, subject, message, caller):
        """
        Override the send_mail method to also save a copy to the sender with a 'sent' tag.

        Args:
            recipients (list): List of Account or Character objects to receive the mail.
            subject (str): The header/subject of the message.
            message (str): The body of the message.
            caller (obj): The sender of the message.
        """
        try:
            # First, perform the original send_mail functionality
            # This is critical to maintain compatibility with the original mail system
            for recipient in recipients:
                recipient.msg("You have received a new @mail from %s" % caller)
                new_message = create.create_message(
                    caller, message, receivers=recipient, header=subject
                )
                # Add explicit mail tag along with new tag
                new_message.tags.add("mail", category="mail")
                new_message.tags.add("new", category="mail")
            
            # Then, create a copy for the sender with a 'sent' tag
            if recipients:
                # Get recipient names for the display in sent mail
                recipient_names = [r.key for r in recipients]
                
                # Create a sent message copy that only goes to the sender
                sent_header = f"TO: {', '.join(recipient_names)} - {subject}"
                sent_message = create.create_message(
                    caller, message, receivers=caller, header=sent_header
                )
                
                # Store the real recipients in message attributes for future lookups
                if hasattr(sent_message, 'db'):
                    # Store the recipient list in message attributes
                    sent_message.db.mail_recipients = recipient_names
                
                # Add 'mail' tag and 'sent' tag so we can identify it later
                sent_message.tags.add("mail", category="mail")
                sent_message.tags.add("sent", category="mail")
                
                caller.msg("You sent your message. It's stored in your sent folder.")
                return True
            else:
                caller.msg("No valid target(s) found. Cannot send message.")
                return False
        except Exception as e:
            log_err(f"Error in send_mail: {e}")
            caller.msg(f"An error occurred while sending mail: {e}")
            return False

    def search_targets(self, namelist):
        """
        Search a list of targets of the same type as caller.

        Args:
            namelist (list): List of strings for objects to search for.

        Returns:
            list: Any target matches.
        """
        try:
            # Use direct code instead of regex for simpler debugging
            if not namelist:
                return []
                
            matches = []
            
            # Process each name in the list
            for name in namelist:
                name = name.strip()
                if not name:
                    continue
                
                # Search for account first
                from evennia.accounts.models import AccountDB
                account_matches = AccountDB.objects.filter(username__iexact=name)
                
                if account_matches:
                    matches.append(account_matches[0])
                    continue
                    
                # If no account match, try character
                from evennia.objects.models import ObjectDB
                character_matches = ObjectDB.objects.filter(db_key__iexact=name, db_typeclass_path__contains="character")
                
                if character_matches:
                    matches.append(character_matches[0])
                    continue
                
            return matches
            
        except Exception as e:
            log_err(f"Error in search_targets: {e}")
            return []

    def get_all_mail(self):
        """
        Returns a list of all the messages where the caller is a recipient. These
            are all messages tagged with tags of the `mail` category.

        Returns:
            messages (QuerySet): Matching Msg objects.

        """
        try:
            # Get all messages with mail category that are received by caller
            # This matches the original Evennia mail command's behavior exactly
            mail_messages = []
            
            if self.caller_is_account:
                messages = list(Msg.objects.get_by_tag(category="mail").filter(db_receivers_accounts=self.caller))
                mail_messages.extend(messages)
            else:
                messages = list(Msg.objects.get_by_tag(category="mail").filter(db_receivers_objects=self.caller))
                mail_messages.extend(messages)
                
                # If the character has an account, also check messages for that account
                if hasattr(self.caller, 'account') and self.caller.account:
                    account_messages = list(Msg.objects.get_by_tag(category="mail").filter(db_receivers_accounts=self.caller.account))
                    
                    # Add unique messages only
                    existing_ids = {msg.id for msg in mail_messages}
                    for msg in account_messages:
                        if msg.id not in existing_ids:
                            mail_messages.append(msg)
                            existing_ids.add(msg.id)
                            
            # Aggressive filtering to catch all page messages
            filtered_mail = []
            for msg in mail_messages:
                # First check - messages with comms category tag
                has_comms_tag = False
                for tag in msg.tags.all():
                    if hasattr(tag, 'db_category') and tag.db_category == "comms":
                        has_comms_tag = True
                        break
                    # Also check for page tags in any form
                    if isinstance(tag, str) and tag == "page":
                        has_comms_tag = True
                        break
                    elif hasattr(tag, 'db_key') and tag.db_key == "page":
                        has_comms_tag = True
                        break
                
                if has_comms_tag:
                    continue
                    
                # Second check - skip sent mail copies (we'll display these separately)
                header = msg.header or ""
                if header.startswith("TO:"):
                    continue
                
                # Third check - empty or None subjects (common in page messages)
                if not header or header == "None":
                    # Skip messages with empty subjects only if they don't have job updates
                    if "job" not in msg.message.lower() and "update" not in msg.message.lower():
                        continue
                
                # Fourth check - messages that start with typical page format 
                if msg.message and hasattr(msg, 'senders') and msg.senders and msg.message.startswith(msg.senders[0].key) and (" " in msg.message[:20]):
                    continue
                    
                # If passed all filters, add to final list
                filtered_mail.append(msg)
                
            # Sort messages by date (oldest first)
            filtered_mail.sort(key=lambda x: x.db_date_created)
            return filtered_mail
            
        except Exception as e:
            log_err(f"Error in get_all_mail: {e}")
            import traceback
            log_err(traceback.format_exc())
            return []

    def get_sent_mail(self):
        """Returns a list of all the messages sent by the caller."""
        try:
            # We need to find messages that were actually SENT by this caller,
            # not just messages with a 'sent' tag that were received by the caller
            
            from evennia.comms.models import Msg
            sent_messages = []
            
            # Check if caller is an account or character
            if self.caller_is_account:
                # Get messages where caller is the sender account
                sent_msgs = Msg.objects.get_by_tag(category="mail", db_key="sent").filter(
                    db_sender_accounts=self.caller
                )
                sent_messages.extend(sent_msgs)
            else:
                # Get messages where caller is the sender object
                sent_msgs = Msg.objects.get_by_tag(category="mail", db_key="sent").filter(
                    db_sender_objects=self.caller
                )
                sent_messages.extend(sent_msgs)
                
                # If character has an account, also check for messages sent by that account
                if hasattr(self.caller, 'account') and self.caller.account:
                    account_sent_msgs = Msg.objects.get_by_tag(category="mail", db_key="sent").filter(
                        db_sender_accounts=self.caller.account
                    )
                    
                    # Avoid duplicates by checking IDs
                    existing_ids = {msg.id for msg in sent_messages}
                    for msg in account_sent_msgs:
                        if msg.id not in existing_ids:
                            sent_messages.append(msg)
            
            # Aggressive filtering for production environment to catch all page messages
            filtered_sent = []
            for msg in sent_messages:
                # First check - messages with comms category tag
                has_comms_tag = False
                for tag in msg.tags.all():
                    if hasattr(tag, 'db_category') and tag.db_category == "comms":
                        has_comms_tag = True
                        break
                    # Also check for page tags in any form
                    if isinstance(tag, str) and tag == "page":
                        has_comms_tag = True
                        break
                    elif hasattr(tag, 'db_key') and tag.db_key == "page":
                        has_comms_tag = True
                        break
                
                if has_comms_tag:
                    continue
                
                # Second check - empty or None subjects (common in page messages)
                if not msg.header or msg.header == "None":
                    # Skip messages with empty subjects only if they don't have job updates
                    if "job" not in msg.message.lower() and "update" not in msg.message.lower():
                        continue
                
                # Third check - messages that start with typical page format
                if msg.message and msg.message.startswith(self.caller.key) and (" " in msg.message[:20]):
                    continue
                    
                # If passed all filters, add to final list
                filtered_sent.append(msg)
            
            # Sort messages by date (oldest first)
            filtered_sent.sort(key=lambda x: x.db_date_created)
            return filtered_sent
            
        except Exception as e:
            log_err(f"Error in get_sent_mail: {e}")
            import traceback
            log_err(traceback.format_exc())
            return []

    def func(self):
        """Main mail functionality without folder support"""
        try:
            # Make sure Msg is available throughout this method
            from evennia.comms.models import Msg
            
            # If the sent switch is active, show only sent messages
            if "sent" in self.switches:
                # Get sent messages for this caller
                sent_mail = self.get_sent_mail()
                
                if not self.args:
                    # Display list of sent messages
                    if sent_mail:
                        table = evtable.EvTable(
                            "|wID|n",
                            "|wTo|n",
                            "|wSubject|n",
                            "|wSent|n",
                            table=None,
                            border="header",
                            header_line_char="-",
                            width=78,
                        )
                        index = 1
                        for message in sent_mail:
                            # Try to extract recipient info in various ways
                            header = message.header or "None"
                            subject = header
                            recipients = "Unknown"
                            
                            # First check if we have recipients stored in message attributes
                            if hasattr(message, 'db') and hasattr(message.db, 'mail_recipients'):
                                if message.db.mail_recipients:
                                    recipients = ", ".join(message.db.mail_recipients)
                            
                            # If still unknown, check if there are specific receivers in the message
                            if recipients == "Unknown" and hasattr(message, 'receivers') and message.receivers:
                                # Get receiver names
                                recipient_names = []
                                for receiver in message.receivers:
                                    if hasattr(receiver, 'key'):
                                        recipient_names.append(receiver.key)
                                    elif hasattr(receiver, 'name'):
                                        recipient_names.append(receiver.name)
                                if recipient_names:
                                    recipients = ", ".join(recipient_names)
                                    
                            # If we still don't have recipients, try to extract from header
                            if recipients == "Unknown" and header.startswith("TO: "):
                                header_parts = header.split(" - ", 1)
                                recipients = header_parts[0][4:] 
                                if len(header_parts) > 1:
                                    subject = header_parts[1]
                                    
                            # For messages where no TO: prefix exists but we have a - delimiter
                            elif " - " in header and recipients == "Unknown":
                                header_parts = header.split(" - ", 1)
                                # The first part might be the recipient
                                if not header_parts[0].startswith("TO:"):
                                    recipients = header_parts[0]
                                subject = header_parts[1] if len(header_parts) > 1 else header
                            
                            table.add_row(
                                index,
                                recipients,
                                subject,
                                datetime_format(message.db_date_created)
                            )
                            index += 1

                        table.reformat_column(0, width=6)
                        table.reformat_column(1, width=20)
                        table.reformat_column(2, width=34)
                        table.reformat_column(3, width=18)

                        self.caller.msg("|b-|n" * 78)
                        self.caller.msg("|wSent Messages:|n")
                        self.caller.msg(str(table))
                        self.caller.msg("|b-|n" * 78)
                    else:
                        self.caller.msg("You haven't sent any messages.")
                else:
                    # Display a specific sent message
                    try:
                        if not sent_mail:
                            self.caller.msg("You haven't sent any messages.")
                            return
                            
                        try:
                            msg_num = int(self.args)
                        except ValueError:
                            self.caller.msg(f"'{self.args}' is not a valid mail id.")
                            return
                            
                        # Check if the message number is valid
                        if msg_num < 1 or msg_num > len(sent_mail):
                            self.caller.msg(f"Message {msg_num} not found.")
                            return
                            
                        # Get the specific message
                        message = sent_mail[msg_num - 1]
                        
                        if message:
                            # Format the message display
                            messageForm = []
                            messageForm.append("|b-|n" * 78)
                            
                            # Try to extract recipient info in various ways
                            header = message.header or "None"
                            subject = header
                            recipients = "Unknown"
                            
                            # First check if we have recipients stored in message attributes
                            if hasattr(message, 'db') and hasattr(message.db, 'mail_recipients'):
                                if message.db.mail_recipients:
                                    recipients = ", ".join(message.db.mail_recipients)
                            
                            # If still unknown, check if there are specific receivers in the message
                            if recipients == "Unknown" and hasattr(message, 'receivers') and message.receivers:
                                # Get receiver names
                                recipient_names = []
                                for receiver in message.receivers:
                                    if hasattr(receiver, 'key'):
                                        recipient_names.append(receiver.key)
                                    elif hasattr(receiver, 'name'):
                                        recipient_names.append(receiver.name)
                                if recipient_names:
                                    recipients = ", ".join(recipient_names)
                                    
                            # If we still don't have recipients, try to extract from header
                            if recipients == "Unknown" and header.startswith("TO: "):
                                header_parts = header.split(" - ", 1)
                                recipients = header_parts[0][4:] 
                                if len(header_parts) > 1:
                                    subject = header_parts[1]
                                    
                            # For messages where no TO: prefix exists but we have a - delimiter
                            elif " - " in header and recipients == "Unknown":
                                header_parts = header.split(" - ", 1)
                                # The first part might be the recipient
                                if not header_parts[0].startswith("TO:"):
                                    recipients = header_parts[0]
                                subject = header_parts[1] if len(header_parts) > 1 else header
                            
                            messageForm.append(f"|wTo:|n {recipients}")
                            day = message.db_date_created.day
                            messageForm.append(
                                "|wSent:|n %s"
                                % message.db_date_created.strftime(f"%b {day}, %Y - %H:%M:%S")
                            )
                            messageForm.append(f"|wSubject:|n {subject}")
                            messageForm.append("|b-|n" * 78)
                            messageForm.append(message.message)
                            messageForm.append("|b-|n" * 78)
                            
                            self.caller.msg("\n".join(messageForm))
                        else:
                            raise IndexError
                    except (ValueError, IndexError):
                        self.caller.msg("That message does not exist.")
                return
                
            # Debug command to show detailed info about all messages
            elif "debug" in self.switches:
                # Direct database queries to analyze message status
                
                # Get all messages directly from database
                if self.caller_is_account:
                    # Messages where the account is a receiver
                    receiver_msgs = list(Msg.objects.filter(db_receivers_accounts=self.caller))
                    # Messages where the account is a sender
                    sender_msgs = list(Msg.objects.filter(db_sender_accounts=self.caller))
                else:
                    # Messages where the character is a receiver
                    receiver_msgs = list(Msg.objects.filter(db_receivers_objects=self.caller))
                    # Messages where the character is a sender
                    sender_msgs = list(Msg.objects.filter(db_sender_objects=self.caller))
                    
                    # If character has an account, also check account messages
                    if hasattr(self.caller, 'account') and self.caller.account:
                        account_receiver_msgs = list(Msg.objects.filter(db_receivers_accounts=self.caller.account))
                        account_sender_msgs = list(Msg.objects.filter(db_sender_accounts=self.caller.account))
                        
                        # Add unique messages only
                        existing_ids = {msg.id for msg in receiver_msgs}
                        for msg in account_receiver_msgs:
                            if msg.id not in existing_ids:
                                receiver_msgs.append(msg)
                                existing_ids.add(msg.id)
                                
                        existing_ids = {msg.id for msg in sender_msgs}
                        for msg in account_sender_msgs:
                            if msg.id not in existing_ids:
                                sender_msgs.append(msg)
                                existing_ids.add(msg.id)
                
                # Create sets of message IDs for quick lookup
                received_ids = {msg.id for msg in receiver_msgs}
                sent_ids = {msg.id for msg in sender_msgs}
                
                # Get all messages with mail category tags
                mail_tagged_msgs = list(Msg.objects.get_by_tag(category="mail"))
                mail_tagged_ids = {msg.id for msg in mail_tagged_msgs}
                
                # Get messages with 'mail' tag
                mail_key_msgs = list(Msg.objects.get_by_tag(category="mail", db_key="mail"))
                mail_key_ids = {msg.id for msg in mail_key_msgs}
                
                # Get messages with 'sent' tag
                sent_tag_msgs = list(Msg.objects.get_by_tag(category="mail", db_key="sent"))
                sent_tag_ids = {msg.id for msg in sent_tag_msgs}
                
                # Get messages with 'new' tag
                new_tag_msgs = list(Msg.objects.get_by_tag(category="mail", db_key="new"))
                new_tag_ids = {msg.id for msg in new_tag_msgs}
                
                # Display summary information
                self.caller.msg("|b-|n" * 78)
                self.caller.msg("|wMail System Debug Information:|n")
                self.caller.msg("|b-|n" * 78)
                self.caller.msg(f"|wTotal messages where you are a receiver:|n {len(receiver_msgs)}")
                self.caller.msg(f"|wTotal messages where you are a sender:|n {len(sender_msgs)}")
                self.caller.msg(f"|wTotal messages with any 'mail' category tag:|n {len(mail_tagged_msgs)}")
                self.caller.msg(f"|wMessages with 'mail' tag (key):|n {len(mail_key_msgs)}")
                self.caller.msg(f"|wMessages with 'sent' tag:|n {len(sent_tag_msgs)}")
                self.caller.msg(f"|wMessages with 'new' tag:|n {len(new_tag_msgs)}")
                self.caller.msg("|b-|n" * 78)
                
                # Create a detailed table of messages
                table = evtable.EvTable(
                    "|wID|n",
                    "|wReceiver?|n",
                    "|wSender?|n",
                    "|wMail Tag|n",
                    "|wSent Tag|n",
                    "|wNew Tag|n",
                    "|wFrom|n", 
                    "|wSubject|n",
                    "|wDate|n",
                    table=None,
                    border="header",
                    header_line_char="-",
                )
                
                # Collect all unique message IDs
                all_ids = received_ids.union(sent_ids).union(mail_tagged_ids)
                all_msgs = []
                
                # Retrieve all unique messages
                for msg_id in all_ids:
                    try:
                        msg = Msg.objects.get(id=msg_id)
                        all_msgs.append(msg)
                    except Msg.DoesNotExist:
                        continue
                
                # Sort by date (oldest first)
                all_msgs.sort(key=lambda x: x.db_date_created)
                
                # Add each message to the table
                for msg in all_msgs:
                    # Get sender name
                    sender_name = "Unknown"
                    if msg.senders:
                        sender_name = msg.senders[0].key
                    
                    # Check flags for this message
                    is_receiver = "Yes" if msg.id in received_ids else "No"
                    is_sender = "Yes" if msg.id in sent_ids else "No"
                    has_mail_tag = "Yes" if msg.id in mail_key_ids else "No"
                    has_sent_tag = "Yes" if msg.id in sent_tag_ids else "No"
                    has_new_tag = "Yes" if msg.id in new_tag_ids else "No"
                    
                    # Add row to table
                    table.add_row(
                        msg.id,
                        is_receiver,
                        is_sender,
                        has_mail_tag,
                        has_sent_tag,
                        has_new_tag,
                        sender_name,
                        msg.header,
                        datetime_format(msg.db_date_created),
                    )
                
                # Format the table
                table.reformat_column(0, width=5)
                table.reformat_column(1, width=9)
                table.reformat_column(2, width=8)
                table.reformat_column(3, width=9)
                table.reformat_column(4, width=9)
                table.reformat_column(5, width=8)
                table.reformat_column(6, width=12)
                table.reformat_column(7, width=30)
                table.reformat_column(8, width=12)
                
                # Display the table
                self.caller.msg(str(table))
                self.caller.msg("|b-|n" * 78)
                self.caller.msg("This information should help diagnose mail system issues.")
                return
                
            # Handle simple @mail with no args - list all mail
            elif not self.args and not self.switches:
                # SIMPLIFIED APPROACH: Get all messages directly from the database where caller is a receiver
                # This matches the debug table's "Receiver? = Yes" entries
                if self.caller_is_account:
                    # Messages where the account is a receiver
                    inbox_messages = list(Msg.objects.get_by_tag(category="mail").filter(db_receivers_accounts=self.caller))
                else:
                    # Messages where the character is a receiver
                    inbox_messages = list(Msg.objects.get_by_tag(category="mail").filter(db_receivers_objects=self.caller))
                    
                    # If character has an account, also check account messages
                    if hasattr(self.caller, 'account') and self.caller.account:
                        account_receiver_msgs = list(Msg.objects.get_by_tag(category="mail").filter(db_receivers_accounts=self.caller.account))
                        
                        # Add unique messages only
                        existing_ids = {msg.id for msg in inbox_messages}
                        for msg in account_receiver_msgs:
                            if msg.id not in existing_ids:
                                inbox_messages.append(msg)
                                existing_ids.add(msg.id)
                
                # Filter out messages with subjects starting with "TO:" - these are sent mail copies
                filtered_inbox = []
                for msg in inbox_messages:
                    header = msg.header or ""
                    if header.startswith("TO:"):
                        continue
                    
                    # Also explicitly filter out any messages with 'comms' category
                    # This ensures page messages don't show up in mail
                    has_comms_tag = False
                    for tag in msg.tags.all():
                        if hasattr(tag, 'db_category') and tag.db_category == "comms":
                            has_comms_tag = True
                            break
                    
                    if not has_comms_tag:
                        filtered_inbox.append(msg)
                
                # Sort messages by date (oldest first)
                filtered_inbox.sort(key=lambda x: x.db_date_created)
                
                # Now display the messages
                if filtered_inbox:
                    # Format the table
                    table = evtable.EvTable(
                        "|wID|n",
                        "|wFrom|n",
                        "|wSubject|n",
                        "|wArrived|n",
                        "|wStatus|n",  # Explicitly name the column
                        table=None,
                        border="header",
                        header_line_char="-",
                        width=78,
                    )
                    
                    # Add each message as a row
                    for i, msg in enumerate(filtered_inbox, start=1):
                        # Get sender name
                        sender_name = "Unknown"
                        if msg.senders:
                            sender_name = msg.senders[0].get_display_name(self.caller)
                        
                        # Get arrival time
                        arrival = datetime_format(msg.db_date_created)
                        
                        # Check if message is new
                        is_new = False
                        for tag in msg.tags.all():
                            tag_key = tag if isinstance(tag, str) else tag.db_key
                            if tag_key == "new":
                                is_new = True
                                break
                        
                        status = "|gNEW|n" if is_new else ""
                        
                        # Add the row to the table
                        table.add_row(i, sender_name, msg.header, arrival, status)
                    
                    # Format the columns
                    table.reformat_column(0, width=6)
                    table.reformat_column(1, width=18)
                    table.reformat_column(2, width=34)
                    table.reformat_column(3, width=13)
                    table.reformat_column(4, width=7)
                    
                    # Display the table
                    self.caller.msg("|b-|n" * 78)
                    self.caller.msg("|wIncoming Mail (Inbox):|n")
                    self.caller.msg(str(table))
                    self.caller.msg("|b-|n" * 78)
                else:
                    self.caller.msg("There are no messages in your inbox.")
                return
                
            # Handle @mail <#> - viewing a specific message
            elif self.args and not self.switches and not self.rhs:
                try:
                    # SIMPLIFIED APPROACH: Get all messages directly from the database where caller is a receiver
                    # This matches the debug table's "Receiver? = Yes" entries
                    if self.caller_is_account:
                        # Messages where the account is a receiver
                        inbox_messages = list(Msg.objects.filter(db_receivers_accounts=self.caller))
                    else:
                        # Messages where the character is a receiver
                        inbox_messages = list(Msg.objects.filter(db_receivers_objects=self.caller))
                        
                        # If character has an account, also check account messages
                        if hasattr(self.caller, 'account') and self.caller.account:
                            account_receiver_msgs = list(Msg.objects.filter(db_receivers_accounts=self.caller.account))
                            
                            # Add unique messages only
                            existing_ids = {msg.id for msg in inbox_messages}
                            for msg in account_receiver_msgs:
                                if msg.id not in existing_ids:
                                    inbox_messages.append(msg)
                                    existing_ids.add(msg.id)
                    
                    # Sort messages by date (oldest first)
                    inbox_messages.sort(key=lambda x: x.db_date_created)
                    
                    # Filter out messages with subjects starting with "TO:" - these are sent mail copies
                    filtered_inbox = []
                    for msg in inbox_messages:
                        header = msg.header or ""
                        if header.startswith("TO:"):
                            continue
                        filtered_inbox.append(msg)
                    
                    # Make sure we have messages
                    if not filtered_inbox:
                        self.caller.msg("There are no messages in your inbox.")
                        return
                        
                    # Get the message number from the user's input
                    try:
                        msg_num = int(self.args)
                    except ValueError:
                        self.caller.msg(f"'{self.args}' is not a valid mail id.")
                        return
                        
                    # Check if the message number is valid
                    if msg_num < 1 or msg_num > len(filtered_inbox):
                        self.caller.msg(f"Message {msg_num} not found.")
                        return
                        
                    # Get the specific message
                    message = filtered_inbox[msg_num - 1]
                    
                    # Format the message for display
                    messageForm = []
                    messageForm.append("|b-|n" * 78)
                    
                    # Add sender info
                    sender_name = "Unknown"
                    if hasattr(message, 'senders') and message.senders:
                        sender_name = message.senders[0].get_display_name(self.caller)
                    messageForm.append(f"|wFrom:|n {sender_name}")
                    
                    # Add date
                    day = message.db_date_created.day
                    messageForm.append(
                        f"|wSent:|n {message.db_date_created.strftime(f'%b {day}, %Y - %H:%M:%S')}"
                    )
                    
                    # Add subject
                    messageForm.append(f"|wSubject:|n {message.header}")
                    
                    # Add body
                    messageForm.append("|b-|n" * 78)
                    messageForm.append(message.message)
                    messageForm.append("|b-|n" * 78)
                    
                    # Send the formatted message to the player
                    self.caller.msg("\n".join(messageForm))
                    
                    # Mark as read by removing new tag and adding - tag
                    message.tags.remove("new", category="mail")
                    message.tags.add("-", category="mail")
                except Exception as e:
                    log_err(f"Error viewing mail: {e}")
                    self.caller.msg(f"Error viewing mail: {e}")
                return
                
            # Handle sending mail: @mail <n>=<subject>/<message>
            elif self.lhs and self.rhs:
                try:
                    # Parse out the recipients
                    recipients = self.search_targets(self.lhslist)
                    
                    if not recipients:
                        self.caller.msg("No valid recipients found.")
                        return
                    
                    # Parse the subject and message
                    if "/" in self.rhs:
                        subject, body = self.rhs.split("/", 1)
                    else:
                        subject = ""
                        body = self.rhs
                    
                    # Use our send_mail method
                    success = self.send_mail(recipients, subject, body, self.caller)
                    if not success:
                        log_err("Failed to send mail")
                        self.caller.msg("Failed to send mail. Check the logs for details.")
                except Exception as e:
                    log_err(f"Error sending mail: {e}")
                    self.caller.msg(f"Error sending mail: {e}")
                return
                
            # For other mail functionality, use the parent implementation
            else:
                super().func()
        except Exception as e:
            log_err(f"Error in CmdMailExtended.func: {e}")
            self.caller.msg(f"An error occurred with the mail command: {e}")
            import traceback
            log_err(traceback.format_exc())

# character - level version of the command
class CmdMailCharacterExtended(CmdMailExtended):
    account_caller = False 