"""
Extended mail commands for diesirae
"""

import re
from evennia.comms.models import Msg
from evennia.utils import evtable, create, datetime_format
from evennia.utils.logger import log_info, log_err
from evennia.contrib.game_systems.mail.mail import CmdMail, CmdMailCharacter
from commands.mail_folders import CmdMailFolder
from typeclasses.characters import Character

"""
Mail extension for Dies Irae.

This module extends the Evennia mail system to store sent messages and
allow viewing them with the /sent switch, as well as organizing mail into folders.
"""

from evennia.contrib.game_systems.mail.mail import CmdMail, CmdMailCharacter
from evennia.utils import create, evtable, datetime_format
from evennia.utils.logger import log_info, log_err

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

      |wFolder commands are not currently supported.|n
      @mail/folder <name> - View messages in the specified folder (see 'help folder' for more info)
      @mail/folder <name>=<#>  - View a specific message in a folder

    Switches:
      delete  - deletes a message
      forward - forward a received message to another object with an optional message attached.
      reply   - Replies to a received message, appending the original message to the bottom.
      sent    - View messages you've sent
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
                
                # Initialize sent folder if needed
                if not hasattr(caller, 'db') or not caller.db.mail_folders:
                    caller.db.mail_folders = ["Incoming", "Sent"]
                
                caller.msg("You sent your message. It's stored in your sent folder.")
                log_info(f"{caller} sent mail to {', '.join(recipient_names)}")
                return True
            else:
                caller.msg("No valid target(s) found. Cannot send message.")
                return False
        except Exception as e:
            log_err(f"Error in send_mail: {e}")
            caller.msg(f"An error occurred while sending mail: {e}")
            return False

    def get_all_mail(self):
        """Returns a list of all the messages received by the caller."""
        try:
            from evennia.comms.models import Msg
            log_info(f"Getting mail for {self.caller}")
            
            # Determine if we're dealing with an account or a character
            account_receiver = None
            object_receiver = None
            
            if self.caller_is_account:
                account_receiver = self.caller
                log_info(f"Caller is an account, searching with account receiver {account_receiver}")
            else:
                object_receiver = self.caller
                log_info(f"Caller is an object, searching with object receiver {object_receiver}")
                
                # Also get the account if available for better coverage
                if hasattr(self.caller, 'account') and self.caller.account:
                    account_receiver = self.caller.account
                    log_info(f"Also using account {account_receiver} for character")
                    
            # Start with basic query for messages where the caller is a receiver
            if account_receiver:
                messages = list(Msg.objects.filter(db_receivers_accounts=account_receiver))
                log_info(f"Found {len(messages)} messages for account {account_receiver}")
            else:
                messages = list(Msg.objects.filter(db_receivers_objects=object_receiver))
                log_info(f"Found {len(messages)} messages for object {object_receiver}")
            
            # For new mail system (post-fix), return all messages since they are properly identified by tags
            log_info(f"Returning all {len(messages)} messages for {self.caller}")
            return messages
            
        except Exception as e:
            log_err(f"Error in get_all_mail: {e}")
            return []

    def get_sent_mail(self):
        """Returns a list of all the messages sent by the caller."""
        try:
            log_info(f"Getting sent mail for {self.caller}")
            
            # Use direct database queries to find all sent messages
            from evennia.comms.models import Msg
            
            sent_messages = []
            
            # Start with account and character sender checks
            if self.caller_is_account:
                # Get messages sent by this account
                sent_db_msgs = Msg.objects.filter(db_sender_accounts=self.caller)
                sent_messages = list(sent_db_msgs)
                log_info(f"Found {len(sent_messages)} messages with account as sender")
            else:
                # Try account first if available
                if hasattr(self.caller, 'account') and self.caller.account:
                    sent_db_msgs = Msg.objects.filter(db_sender_accounts=self.caller.account)
                    sent_messages.extend(list(sent_db_msgs))
                    log_info(f"Found {len(sent_db_msgs)} messages with associated account as sender")
                
                # Also try character as sender
                char_msgs = Msg.objects.filter(db_sender_objects=self.caller)
                if char_msgs:
                    # Add only unique messages not already in the list
                    existing_ids = set(msg.id for msg in sent_messages)
                    for msg in char_msgs:
                        if msg.id not in existing_ids:
                            sent_messages.append(msg)
                    log_info(f"Found {char_msgs.count()} messages with character as sender")
            
            # If we found any sent messages, make sure they have sent tags
            if sent_messages:
                # Add 'sent' tags to make them easier to find in the future
                for msg in sent_messages:
                    has_sent_tag = False
                    for tag in msg.tags.all():
                        if (isinstance(tag, str) and tag == "sent") or \
                           (hasattr(tag, 'db_key') and hasattr(tag, 'db_category') and 
                            tag.db_category == "mail" and tag.db_key == "sent"):
                            has_sent_tag = True
                            break
                    if not has_sent_tag:
                        msg.tags.add("sent", category="mail")
                        msg.tags.add("mail", category="mail")
                        log_info(f"Added 'sent' tag to message {msg.id}")
                
                # Sort messages by date (newest first)
                sent_messages.sort(key=lambda x: x.db_date_created, reverse=True)
                return sent_messages
            
            # If direct DB search found nothing, try finding messages with 'sent' tag
            all_mail = self.get_all_mail()
            sent_by_tag = []
            
            for msg in all_mail:
                has_sent_tag = False
                for tag in msg.tags.all():
                    if (isinstance(tag, str) and tag == "sent") or \
                       (hasattr(tag, 'db_key') and hasattr(tag, 'db_category') and 
                        tag.db_category == "mail" and tag.db_key == "sent"):
                        has_sent_tag = True
                        sent_by_tag.append(msg)
                        break
                    
            log_info(f"Found {len(sent_by_tag)} messages with 'sent' tag")
            
            # Sort messages by date (newest first)
            sent_by_tag.sort(key=lambda x: x.db_date_created, reverse=True)
            
            # Return what we found, preferring DB sender search over tag search
            return sent_messages or sent_by_tag
            
        except Exception as e:
            log_err(f"Error in get_sent_mail: {e}")
            import traceback
            log_err(traceback.format_exc())
            return []

    def func(self):
        """Extends the mail functionality with sent mailbox and folders"""
        try:
            # Always log command details when mail is run
            log_info(f"Mail command executed by {self.caller}")
            log_info(f"- Args: '{self.args}'")
            log_info(f"- Switches: {self.switches}")
            log_info(f"- LHS: '{self.lhs}'")
            log_info(f"- RHS: '{self.rhs}'")
            
            # Initialize folders if they don't exist
            if not hasattr(self.caller, 'db') or not self.caller.db.mail_folders:
                self.caller.db.mail_folders = ["Incoming", "Sent"]
            
            # Handle folder switch
            if "folder" in self.switches:
                return self.handle_folder_switch()
            
            # If the sent switch is active, show only sent messages
            if "sent" in self.switches:
                log_info(f"Processing mail/sent for {self.caller}")
                
                # Get sent messages for this caller
                sent_mail = self.get_sent_mail()
                log_info(f"Found {len(sent_mail)} sent messages for {self.caller}")
                
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
                                    log_info(f"Found recipients in message attributes: {recipients}")
                            
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
                            
                            # Log what we found
                            log_info(f"Message {message.id}: To={recipients}, Subject={subject}")
                            
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

                        self.caller.msg("-" * 78)
                        self.caller.msg("|wSent Messages:|n")
                        self.caller.msg(str(table))
                        self.caller.msg("-" * 78)
                    else:
                        self.caller.msg("You haven't sent any messages.")
                else:
                    # Display a specific sent message
                    try:
                        if not sent_mail:
                            self.caller.msg("You haven't sent any messages.")
                            return
                            
                        mind_max = max(0, len(sent_mail) - 1)
                        mind = max(0, min(mind_max, int(self.args) - 1))
                        message = sent_mail[mind]
                        
                        if message:
                            # Format the message display
                            messageForm = []
                            messageForm.append("-" * 78)
                            
                            # Try to extract recipient info in various ways
                            header = message.header or "None"
                            subject = header
                            recipients = "Unknown"
                            
                            # First check if we have recipients stored in message attributes
                            if hasattr(message, 'db') and hasattr(message.db, 'mail_recipients'):
                                if message.db.mail_recipients:
                                    recipients = ", ".join(message.db.mail_recipients)
                                    log_info(f"Found recipients in message attributes: {recipients}")
                            
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
                            messageForm.append("-" * 78)
                            messageForm.append(message.message)
                            messageForm.append("-" * 78)
                            
                            self.caller.msg("\n".join(messageForm))
                        else:
                            raise IndexError
                    except (ValueError, IndexError):
                        self.caller.msg("That message does not exist.")
                return
                
            # Handle simple @mail with no args - list all mail
            elif not self.args and not self.switches:
                log_info(f"Listing mail messages for {self.caller}")
                messages = self.get_all_mail()
                log_info(f"Found {len(messages)} mail messages for {self.caller}")
                
                if messages:
                    # Format and show messages
                    table = evtable.EvTable(
                        "|wID|n",
                        "|wFrom|n",
                        "|wSubject|n",
                        "|wArrived|n",
                        "",
                        table=None,
                        border="header",
                        header_line_char="-",
                        width=78,
                    )
                    index = 1
                    for message in messages:
                        # Skip sent messages in the normal inbox view
                        try:
                            # Check if message has a 'sent' tag, handling both object tags and string tags
                            all_tags = message.tags.all()
                            has_sent = False
                            for tag in all_tags:
                                # Check if tag is a string or has db_category/db_key attributes
                                if isinstance(tag, str):
                                    if tag == "sent":
                                        has_sent = True
                                        break
                                elif hasattr(tag, 'db_category') and hasattr(tag, 'db_key'):
                                    if tag.db_category == "mail" and tag.db_key == "sent":
                                        has_sent = True
                                        break
                            
                            # Skip messages that have a folder tag other than Incoming
                            has_folder = False
                            for tag in all_tags:
                                if isinstance(tag, str) and tag.startswith("folder_"):
                                    # Skip if it's not explicitly in Incoming
                                    if tag != "folder_Incoming":
                                        has_folder = True
                                        break
                                elif hasattr(tag, 'db_key') and hasattr(tag, 'db_category'):
                                    if tag.db_category == "mail" and tag.db_key.startswith("folder_"):
                                        # Skip if it's not explicitly in Incoming
                                        if tag.db_key != "folder_Incoming":
                                            has_folder = True
                                            break
                            
                            if has_sent or has_folder:
                                continue
                                
                            # Check for NEW status
                            status = ""
                            for tag in all_tags:
                                if isinstance(tag, str):
                                    if tag.upper() == "NEW":
                                        status = "|gNEW|n"
                                        break
                                elif hasattr(tag, 'db_category') and hasattr(tag, 'db_key'):
                                    if tag.db_category == "mail" and tag.db_key == "new":
                                        status = "|gNEW|n"
                                        break
                        except Exception as e:
                            log_err(f"Error checking mail tags: {e}")
                            continue
                            
                        sender_name = "Unknown"
                        if hasattr(message, 'senders') and message.senders:
                            sender_name = message.senders[0].get_display_name(self.caller)

                        table.add_row(
                            index,
                            sender_name,
                            message.header,
                            datetime_format(message.db_date_created),
                            status,
                        )
                        index += 1

                    if index > 1:  # Only display if there are non-sent messages
                        table.reformat_column(0, width=6)
                        table.reformat_column(1, width=18)
                        table.reformat_column(2, width=34)
                        table.reformat_column(3, width=13)
                        table.reformat_column(4, width=7)

                        self.caller.msg("-" * 78)
                        self.caller.msg("|wIncoming Mail (Inbox):|n")
                        self.caller.msg(str(table))
                        self.caller.msg("-" * 78)
                    else:
                        self.caller.msg("There are no messages in your inbox.")
                else:
                    self.caller.msg("There are no messages in your inbox.")
                return
                
            # Handle @mail <#> - viewing a specific message
            elif self.args and not self.switches and not self.rhs:
                try:
                    log_info(f"Viewing specific mail {self.args} for {self.caller}")
                    all_mail = self.get_all_mail()
                    # Filter out sent messages for normal viewing
                    inbox_mail = []
                    for msg in all_mail:
                        try:
                            # Check if message has a 'sent' tag
                            all_tags = msg.tags.all()
                            has_sent = False
                            for tag in all_tags:
                                # Check if tag is a string or has db_category/db_key attributes
                                if isinstance(tag, str):
                                    if tag == "sent":
                                        has_sent = True
                                        break
                                elif hasattr(tag, 'db_category') and hasattr(tag, 'db_key'):
                                    if tag.db_category == "mail" and tag.db_key == "sent":
                                        has_sent = True
                                        break
                                        
                            # Also filter out messages that have a folder tag that isn't Incoming
                            has_folder = False
                            for tag in all_tags:
                                if isinstance(tag, str) and tag.startswith("folder_"):
                                    # Skip if it's not explicitly in Incoming
                                    if tag != "folder_Incoming":
                                        has_folder = True
                                        break
                                elif hasattr(tag, 'db_key') and hasattr(tag, 'db_category'):
                                    if tag.db_category == "mail" and tag.db_key.startswith("folder_"):
                                        # Skip if it's not explicitly in Incoming
                                        if tag.db_key != "folder_Incoming":
                                            has_folder = True
                                            break
                            
                            if not has_sent and not has_folder:
                                inbox_mail.append(msg)
                        except Exception as e:
                            log_err(f"Error checking mail tags: {e}")
                            continue
                    
                    mind_max = max(0, len(inbox_mail) - 1)
                    try:
                        mind = max(0, min(mind_max, int(self.args) - 1))
                    except ValueError:
                        self.caller.msg(f"'{self.args}' is not a valid mail id.")
                        return
                        
                    if mind_max < 0:
                        self.caller.msg("There are no messages in your inbox.")
                        return
                        
                    message = inbox_mail[mind]
                    
                    if message:
                        messageForm = []
                        messageForm.append("-" * 78)
                        # Add safety check for empty senders list
                        sender_name = "Unknown"
                        if hasattr(message, 'senders') and message.senders:
                            sender_name = message.senders[0].get_display_name(self.caller)
                        messageForm.append("|wFrom:|n %s" % sender_name)
                        # note that we cannot use %-d format here since Windows does not support it
                        day = message.db_date_created.day
                        messageForm.append(
                            "|wSent:|n %s"
                            % message.db_date_created.strftime(f"%b {day}, %Y - %H:%M:%S")
                        )
                        messageForm.append("|wSubject:|n %s" % message.header)
                        messageForm.append("-" * 78)
                        messageForm.append(message.message)
                        messageForm.append("-" * 78)
                        self.caller.msg("\n".join(messageForm))
                        
                        # Mark as read by removing new tag and adding - tag
                        try:
                            # Check if message has a 'new' tag
                            all_tags = message.tags.all()
                            has_new = False
                            for tag in all_tags:
                                # Check if tag is a string or has db_category/db_key attributes
                                if isinstance(tag, str):
                                    if tag.upper() == "NEW":
                                        has_new = True
                                        break
                                elif hasattr(tag, 'db_category') and hasattr(tag, 'db_key'):
                                    if tag.db_category == "mail" and tag.db_key == "new":
                                        has_new = True
                                        break
                                        
                            if has_new:
                                message.tags.remove("new", category="mail")
                                message.tags.add("-", category="mail")
                        except Exception as e:
                            log_err(f"Error updating message read status: {e}")
                            pass
                except Exception as e:
                    log_err(f"Error viewing mail: {e}")
                    self.caller.msg(f"Error viewing mail: {e}")
                return
                
            # Handle sending mail: @mail <name>=<subject>/<message>
            elif self.lhs and self.rhs:
                log_info(f"Sending mail: LHS={self.lhs}, RHS={self.rhs}")
                try:
                    # Parse out the recipients
                    recipients = self.search_targets(self.lhslist)
                    log_info(f"Found recipients: {recipients}")
                    
                    if not recipients:
                        self.caller.msg("No valid recipients found.")
                        return
                    
                    # Parse the subject and message
                    if "/" in self.rhs:
                        subject, body = self.rhs.split("/", 1)
                    else:
                        subject = ""
                        body = self.rhs
                    
                    log_info(f"Sending mail with subject: '{subject}', body length: {len(body)}")
                    
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
                log_info(f"Using parent mail implementation for {self.caller}")
                super().func()
        except Exception as e:
            log_err(f"Error in CmdMailExtended.func: {e}")
            self.caller.msg(f"An error occurred with the mail command: {e}")
            import traceback
            log_err(traceback.format_exc())

    def handle_folder_switch(self):
        """Handle mail/folder command"""
        caller = self.caller
        log_info(f"Processing mail/folder for {caller} with args: {self.args}")
        
        if not self.args:
            caller.msg("You must specify a folder name. Use 'folder' to list available folders.")
            return
            
        # Handle folder=number syntax
        if "=" in self.args:
            folder_name, message_num = self.args.split("=", 1)
            folder_name = folder_name.strip()
            
            # Make sure folders exist
            if not hasattr(caller, 'db') or not caller.db.mail_folders:
                caller.db.mail_folders = ["Incoming", "Sent"]
                
            # Check if folder exists (case-insensitive)
            folder_exists = False
            real_folder_name = folder_name  # Use this to preserve case
            for f in caller.db.mail_folders:
                if f.lower() == folder_name.lower():
                    folder_exists = True
                    real_folder_name = f  # Use the actual case from the folder list
                    break
                    
            if not folder_exists:
                caller.msg(f"Folder '{folder_name}' doesn't exist.")
                return
                
            try:
                message_num = int(message_num.strip())
            except ValueError:
                caller.msg("Message number must be a number.")
                return
                
            # Get all mail messages
            all_mail = self.get_all_mail()
            
            # Debug: log message IDs and their tags
            for i, msg in enumerate(all_mail):
                tag_info = []
                for tag in msg.tags.all():
                    if isinstance(tag, str):
                        tag_info.append(f"str:{tag}")
                    elif hasattr(tag, 'db_key') and hasattr(tag, 'db_category'):
                        tag_info.append(f"obj:{tag.db_key}(cat:{tag.db_category})")
                log_info(f"Message ID {msg.id} #{i+1} tags: {tag_info}")
                
            # Filter messages by folder
            folder_contents = []
            
            # For default folders (Incoming, Sent)
            if real_folder_name.lower() == "incoming":
                # Include messages without folder tags and not in Sent
                for msg in all_mail:
                    has_folder = False
                    is_sent = False
                    
                    for tag in msg.tags.all():
                        if isinstance(tag, str):
                            if tag.startswith("folder_"):
                                has_folder = True
                                break
                            elif tag == "sent":
                                is_sent = True
                        elif hasattr(tag, 'db_key'):
                            if tag.db_key.startswith("folder_"):
                                has_folder = True
                                break
                            elif tag.db_key == "sent":
                                is_sent = True
                        elif hasattr(tag, 'db_category') and hasattr(tag, 'db_key') and tag.db_category == "mail" and tag.db_key == "sent":
                            is_sent = True
                                
                    if not has_folder and not is_sent:
                        folder_contents.append(msg)
                        
            elif real_folder_name.lower() == "sent":
                # Use get_sent_mail to find sent messages
                folder_contents = self.get_sent_mail()
                log_info(f"Got {len(folder_contents)} sent messages using get_sent_mail")
            else:
                # Custom folder - look for folder tag
                folder_tag = f"folder_{real_folder_name}"
                log_info(f"Looking for messages with folder tag: {folder_tag}")
                
                for msg in all_mail:
                    # Debug output to see tag information
                    tag_info = []
                    for tag in msg.tags.all():
                        if isinstance(tag, str):
                            tag_info.append(f"str:{tag}")
                        elif hasattr(tag, 'db_key') and hasattr(tag, 'db_category'):
                            tag_info.append(f"obj:{tag.db_key}(cat:{tag.db_category})")
                    log_info(f"Message ID {msg.id} tags: {tag_info}")
                    
                    found_in_folder = False
                    for tag in msg.tags.all():
                        if isinstance(tag, str) and tag == folder_tag:
                            log_info(f"Found message with string tag {tag}")
                            found_in_folder = True
                            break
                        elif hasattr(tag, 'db_key') and hasattr(tag, 'db_category'):
                            if tag.db_category == "mail" and tag.db_key == folder_tag:
                                log_info(f"Found message with object tag {tag.db_key} (category: {tag.db_category})")
                                found_in_folder = True
                                break
                            elif tag.db_category == "mail" and tag.db_key.lower() == folder_tag.lower():
                                log_info(f"Found message with case-insensitive tag match: {tag.db_key}")
                                found_in_folder = True
                                break
                    
                    if found_in_folder:
                        folder_contents.append(msg)
                        log_info(f"Added message ID {msg.id} to folder contents")

            # Display the specific message
            if not folder_contents:
                caller.msg(f"No messages found in folder '{folder_name}'.")
                return
                
            if 1 <= message_num <= len(folder_contents):
                message = folder_contents[message_num - 1]
                
                messageForm = []
                messageForm.append("-" * 78)
                # Add safety check for empty senders list
                sender_name = "Unknown"
                if hasattr(message, 'senders') and message.senders:
                    sender_name = message.senders[0].get_display_name(caller)
                messageForm.append("|wFrom:|n %s" % sender_name)
                # note that we cannot use %-d format here since Windows does not support it
                day = message.db_date_created.day
                messageForm.append(
                    "|wSent:|n %s"
                    % message.db_date_created.strftime(f"%b {day}, %Y - %H:%M:%S")
                )
                messageForm.append("|wSubject:|n %s" % message.header)
                messageForm.append("|wFolder:|n %s" % folder_name)
                messageForm.append("-" * 78)
                messageForm.append(message.message)
                messageForm.append("-" * 78)
                caller.msg("\n".join(messageForm))
                
                # Mark as read by removing new tag and adding - tag
                try:
                    # Check if message has a 'new' tag
                    all_tags = message.tags.all()
                    has_new = False
                    for tag in all_tags:
                        # Check if tag is a string or has db_category/db_key attributes
                        if isinstance(tag, str):
                            if tag.upper() == "NEW":
                                has_new = True
                                break
                        elif hasattr(tag, 'db_category') and hasattr(tag, 'db_key'):
                            if tag.db_category == "mail" and tag.db_key == "new":
                                has_new = True
                                break
                                
                    if has_new:
                        message.tags.remove("new", category="mail")
                        message.tags.add("-", category="mail")
                except Exception as e:
                    log_err(f"Error updating message read status: {e}")
                    pass
            else:
                caller.msg(f"Message {message_num} not found in folder '{folder_name}'.")
            return
                
        # Just show folder contents
        folder_name = self.args.strip()
        
        # Make sure folders exist
        if not hasattr(caller, 'db') or not caller.db.mail_folders:
            caller.db.mail_folders = ["Incoming", "Sent"]
            
        # Check if folder exists (case-insensitive)
        folder_exists = False
        real_folder_name = folder_name  # Use this to preserve case
        for f in caller.db.mail_folders:
            if f.lower() == folder_name.lower():
                folder_exists = True
                real_folder_name = f  # Use the actual case from the folder list
                break
                
        if not folder_exists:
            caller.msg(f"Folder '{folder_name}' doesn't exist.")
            return
            
        try:
            # Get all mail messages
            all_mail = self.get_all_mail()
                
            # Filter messages by folder
            folder_contents = []
            
            # For default folders (Incoming, Sent)
            if real_folder_name.lower() == "incoming":
                # Include messages without folder tags and not in Sent
                for msg in all_mail:
                    has_folder = False
                    is_sent = False
                    
                    for tag in msg.tags.all():
                        if isinstance(tag, str):
                            if tag.startswith("folder_"):
                                has_folder = True
                                break
                            elif tag == "sent":
                                is_sent = True
                        elif hasattr(tag, 'db_key'):
                            if tag.db_key.startswith("folder_"):
                                has_folder = True
                                break
                            elif tag.db_key == "sent":
                                is_sent = True
                        elif hasattr(tag, 'db_category') and hasattr(tag, 'db_key') and tag.db_category == "mail" and tag.db_key == "sent":
                            is_sent = True
                                
                    if not has_folder and not is_sent:
                        folder_contents.append(msg)
                        
            elif real_folder_name.lower() == "sent":
                # Use get_sent_mail to find sent messages
                folder_contents = self.get_sent_mail()
                log_info(f"Got {len(folder_contents)} sent messages using get_sent_mail")
            else:
                # Custom folder - look for folder tag
                folder_tag = f"folder_{real_folder_name}"
                log_info(f"Looking for messages with folder tag: {folder_tag}")
                
                for msg in all_mail:
                    # Check each tag for a match
                    found_in_folder = False
                    for tag in msg.tags.all():
                        # For string tags (direct comparison)
                        if isinstance(tag, str) and tag == folder_tag:
                            log_info(f"Found message with string tag {tag}")
                            found_in_folder = True
                            break
                        # For object tags (with db_key and db_category)
                        elif hasattr(tag, 'db_key') and hasattr(tag, 'db_category'):
                            # Try exact match first
                            if tag.db_category == "mail" and tag.db_key == folder_tag:
                                log_info(f"Found message with object tag {tag.db_key} (category: {tag.db_category})")
                                found_in_folder = True
                                break
                            # Then try case-insensitive match
                            elif tag.db_category == "mail" and tag.db_key.lower() == folder_tag.lower():
                                log_info(f"Found message with case-insensitive tag match: {tag.db_key}")
                                found_in_folder = True
                                break
                    
                    if found_in_folder:
                        folder_contents.append(msg)
                        log_info(f"Added message {msg.id} to folder contents")

            # Display folder contents
            if folder_contents:
                # Format and show messages
                table = evtable.EvTable(
                    "|wID|n",
                    "|wFrom|n",
                    "|wSubject|n",
                    "|wArrived|n",
                    "",
                    table=None,
                    border="header",
                    header_line_char="-",
                    width=78,
                )
                
                for i, message in enumerate(folder_contents, start=1):
                    status = ""
                    for tag in message.tags.all():
                        if isinstance(tag, str) and tag.upper() == "NEW":
                            status = "|gNEW|n"
                            break
                        elif hasattr(tag, 'db_key') and tag.db_key.upper() == "NEW":
                            status = "|gNEW|n"
                            break

                    sender_name = "Unknown"
                    if hasattr(message, 'senders') and message.senders:
                        sender_name = message.senders[0].get_display_name(caller)

                    table.add_row(
                        i,
                        sender_name,
                        message.header,
                        message.db_date_created.strftime("%b %d, %Y"),
                        status,
                    )

                table.reformat_column(0, width=6)
                table.reformat_column(1, width=18)
                table.reformat_column(2, width=34)
                table.reformat_column(3, width=13)
                table.reformat_column(4, width=7)

                caller.msg("-" * 78)
                caller.msg(f"|wFolder: {folder_name}|n")
                caller.msg(str(table))
                caller.msg("-" * 78)
            else:
                caller.msg(f"Folder '{folder_name}' is empty.")
                
        except Exception as e:
            log_err(f"Error showing folder contents: {e}")
            caller.msg(f"Error showing folder contents: {e}")

    def search_targets(self, namelist):
        """
        Search a list of targets of the same type as caller.

        Args:
            namelist (list): List of strings for objects to search for.

        Returns:
            list: Any target matches.
        """
        from evennia.utils.logger import log_info, log_err
        try:
            log_info(f"Searching for targets: {namelist}")
            
            # Use direct code instead of regex for simpler debugging
            if not namelist:
                return []
                
            matches = []
            
            # Process each name in the list
            for name in namelist:
                name = name.strip()
                if not name:
                    continue
                    
                log_info(f"Searching for target: '{name}'")
                
                # Search for account first
                from evennia.accounts.models import AccountDB
                account_matches = AccountDB.objects.filter(username__iexact=name)
                
                if account_matches:
                    log_info(f"Found account match: {account_matches[0]}")
                    matches.append(account_matches[0])
                    continue
                    
                # If no account match, try character
                from evennia.objects.models import ObjectDB
                character_matches = ObjectDB.objects.filter(db_key__iexact=name, db_typeclass_path__contains="character")
                
                if character_matches:
                    log_info(f"Found character match: {character_matches[0]}")
                    matches.append(character_matches[0])
                    continue
                    
                log_info(f"No matches found for: '{name}'")
                
            log_info(f"Final matches: {matches}")
            return matches
            
        except Exception as e:
            log_err(f"Error in search_targets: {e}")
            return []

class CmdMailCharacterExtended(CmdMailCharacter, CmdMailExtended):
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

      |wFolder commands are not currently supported.|n
      @mail/folder <name> - View messages in the specified folder (see 'help folder' for more info)
      @mail/folder <name>=<#>  - View a specific message in a folder

    Switches:
      delete  - deletes a message
      forward - forward a received message to another object with an optional message attached.
      reply   - Replies to a received message, appending the original message to the bottom.
      sent    - View messages you've sent
    """
    account_caller = False 