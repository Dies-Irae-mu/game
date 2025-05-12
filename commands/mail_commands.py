"""
Mail command implementation that filters out page messages from the display.
"""
from evennia.contrib.game_systems.mail import CmdMail as EvenniaCmdMail
from evennia.utils import evtable, logger
from evennia.comms.models import Msg
from django.db.models import Q
import datetime

class CmdMail(EvenniaCmdMail):
    """
    Communicate with others by sending mail.

    Usage:
      @mail                    - Displays all the mail an account has in their mailbox
      @mail <#>                - Displays a specific message
      @mail <accounts>=<subject>/<message>
                              - Sends a message to the comma separated list of accounts.
      @mail/delete <#>         - Deletes a specific message
      @mail/forward <accounts>=<#>[/<Message>]
                              - Forwards an existing message to the specified list of accounts,
                                original message is delivered with optional Message prepended.
      @mail/reply <#>=<message>
                              - Replies to a message #. Prepends message to the original
                                message text.
      @mail/sent               - Shows messages you have sent
      @mail/sent <#>           - Shows a specific sent message by its number
    Switches:
      delete  - deletes a message
      forward - forward a received message to another object with an optional message attached.
      reply   - Replies to a received message, appending the original message to the bottom.
      sent    - display messages you have sent or view a specific sent message
    """

    def func(self):
        """
        Override func to handle mail operations with improved feedback.
        """
        # Case: List sent messages (sent switch, no args)
        if "sent" in self.switches and not self.args:
            self.display_sent_mail()
            return
            
        # Case: View individual sent message (sent switch with a number)
        elif "sent" in self.switches and self.args:
            try:
                # Try to convert to an integer
                mind = int(self.args) - 1
                
                # Get all sent mail messages
                sent_messages = self.get_sent_mail()
                
                # Check if the index is valid
                if 0 <= mind < len(sent_messages):
                    message = sent_messages[mind]
                    
                    # Display sent message with custom formatting
                    self.display_sent_message(message)
                    return
                else:
                    self.caller.msg(f"'{self.args}' is not a valid sent mail id.")
                    return
            except ValueError:
                self.caller.msg(f"Invalid mail id. Use a number to specify the mail message.")
                return
            
        # Case 1: Mail sending (no switches, args with =, possibly with /)
        elif not self.switches and self.args and "=" in self.args:
            try:
                # Log mail attempt 
                logger.log_info(f"Mail send attempt: {self.args}")
                
                # Parse mail arguments - ensure recipients are properly identified
                # Get the left part of the first equals sign
                lhs = self.args.split("=", 1)[0].strip()
                # Get the right part
                rhs = self.args.split("=", 1)[1].strip()
                
                # Extract recipients
                recipients = [r.strip() for r in lhs.split(",")]
                logger.log_info(f"Recipients: {recipients}")
                
                # Save the current Msg.create method to restore after our override
                original_create = Msg.create
                
                # Override Msg.create to add custom tagging
                def custom_create_hook(*args, **kwargs):
                    # Call the original create method
                    msg = original_create(*args, **kwargs)
                    
                    try:
                        # Add mail and sent tags to the message
                        if msg:
                            # Try to add tags if this method exists
                            if hasattr(msg, 'tags') and hasattr(msg.tags, 'add'):
                                msg.tags.add("mail", category="mail")
                                msg.tags.add("sent", category="mail")
                                logger.log_info(f"Added mail and sent tags to message {msg.id} in create hook")
                    except Exception as e:
                        logger.log_err(f"Error adding tags in custom create hook: {str(e)}")
                    
                    return msg
                
                # Replace the create method with our custom version
                try:
                    Msg.create = custom_create_hook
                    
                    # Call original implementation for mail sending
                    original_func = super().func
                    result = original_func()
                    
                    # Provide feedback to sender
                    self.caller.msg("Mail sent successfully.")
                    logger.log_info("Mail sent successfully")
                finally:
                    # Restore the original create method no matter what
                    Msg.create = original_create
                
                # Find the actual sent message as a backup in case our hook didn't work
                if self.account_caller:
                    sender = self.caller
                else:
                    sender = self.caller.account
                
                # Look for the most recently sent message
                try:
                    timestamp_threshold = datetime.datetime.now() - datetime.timedelta(seconds=10)
                    recent_messages = Msg.objects.filter(
                        db_sender_accounts=sender,
                        db_date_created__gte=timestamp_threshold
                    ).order_by('-db_date_created')
                    
                    # Try to find the exact message based on recipients and content
                    found_message = None
                    for msg in recent_messages[:5]:  # Check the 5 most recent messages
                        # Check if header starts with TO: 
                        if msg.db_header and msg.db_header.startswith("TO:"):
                            # Look for recipient matches in the header
                            recipient_matched = any(r.lower() in msg.db_header.lower() for r in recipients)
                            if recipient_matched:
                                found_message = msg
                                break
                    
                    # If we found a specific match, use it; otherwise use the most recent
                    recent_sent = found_message or recent_messages.first()
                    
                    if recent_sent:
                        # Ensure it has the mail tag - add both mail and sent tags
                        if hasattr(recent_sent, 'tags') and hasattr(recent_sent.tags, 'add'):
                            recent_sent.tags.add("mail", category="mail")
                            recent_sent.tags.add("sent", category="mail")
                            logger.log_info(f"Added mail and sent tags to message {recent_sent.id} in backup tagging")
                        
                        # Debug: Add TO tag for extra identification
                        if all(hasattr(recent_sent, attr) for attr in ('db_header', 'db_message')):
                            to_header = recent_sent.db_header
                            logger.log_info(f"Recent message: ID={recent_sent.id}, Header={to_header}, " +
                                          f"Date={recent_sent.db_date_created}")
                        
                        # Also debug tags
                        try:
                            tag_info = []
                            for tag in recent_sent.tags.all():
                                if isinstance(tag, str):
                                    tag_info.append(tag)
                                else:
                                    # Try to get tag info safely
                                    try:
                                        if hasattr(tag, 'db_key') and hasattr(tag, 'db_category'):
                                            tag_info.append(f"{tag.db_key}:{tag.db_category}")
                                        else:
                                            tag_info.append(str(tag))
                                    except:
                                        tag_info.append("error-getting-tag-info")
                            logger.log_info(f"Message tags: {', '.join(tag_info)}")
                        except Exception as e:
                            logger.log_err(f"Error logging tags: {str(e)}")
                except Exception as e:
                    logger.log_err(f"Error tagging sent mail: {str(e)}")
                    logger.log_err("Full error details:", exc_info=True)
                
                return result
            except Exception as e:
                # Log any errors in mail sending
                logger.log_err(f"Error sending mail: {str(e)}")
                self.caller.msg(f"Error sending mail: {str(e)}")
                return
        
        # Case 2: View mail list (no switches, no args)
        elif not self.switches and not self.args:
            self.display_mail_list()
            return
        
        # Case 3: View individual message (no switches, numeric arg)
        elif not self.switches and self.args and not self.rhs:
            try:
                # Try to convert to an integer
                mind = int(self.args) - 1
                
                # Get all mail messages
                all_mail = self.get_all_mail()
                
                # Check if the index is valid
                if 0 <= mind < len(all_mail):
                    message = all_mail[mind]
                    
                    # Display message with custom formatting
                    self.display_message(message)
                    return
                else:
                    self.caller.msg(f"'{self.args}' is not a valid mail id.")
                    return
            except ValueError:
                # If not an integer, let parent handle it
                pass
        
        # For all other cases, let the parent handle it
        super().func()

    def display_mail_list(self):
        """
        Display the full list of mail messages.
        """
        messages = self.get_all_mail()

        if messages:
            # Create table
            _HEAD_CHAR = "|-"
            _WIDTH = 78
            
            # Count job notifications vs regular mail
            job_count = 0
            regular_count = 0
            for message in messages:
                is_job = False
                if message.db_message and "Job #" in message.db_message:
                    job_count += 1
                    is_job = True
                if message.db_header and "Job #" in message.db_header:
                    job_count += 1
                    is_job = True
                if not is_job:
                    regular_count += 1
            
            # Display header with counts
            self.caller.msg("|015" + "-" * _WIDTH + "|n")
            if job_count > 0:
                self.caller.msg(f"|wMailbox:|n {len(messages)} messages ({regular_count} regular, {job_count} job notifications)")
            else:
                self.caller.msg(f"|wMailbox:|n {len(messages)} messages")
            
            # Create table with headers
            table = evtable.EvTable(
                "|wID|n",
                "|wFrom|n",
                "|wSubject|n",
                "|wArrived|n",
                table=None,
                border="header",
                width=_WIDTH
            )
            
            # Add each message
            for i, message in enumerate(messages, 1):
                # Determine if the message is new
                is_new = False
                for tag in message.tags.all():
                    if hasattr(tag, 'db_category') and tag.db_category == "mail" and tag.db_key == "new":
                        is_new = True
                        break
                
                # Get sender name
                sender_name = "Unknown"
                if hasattr(message, 'senders'):
                    if isinstance(message.senders, list) and message.senders:
                        sender = message.senders[0]
                        sender_name = sender.get_display_name(self.caller)
                    elif hasattr(message.senders, 'first') and message.senders.first():
                        sender = message.senders.first()
                        sender_name = sender.get_display_name(self.caller)
                
                # Format subject with new indicator and job tag if applicable
                subject = message.db_header or ""
                
                # Check if this is a job notification
                is_job = False
                if message.db_message and "Job #" in message.db_message:
                    is_job = True
                if message.db_header and "Job #" in message.db_header:
                    is_job = True
                
                # Apply special formatting for job notifications
                if is_job:
                    sender_name = f"|m{sender_name}|n"
                    subject = f"|m{subject}|n"
                
                # Format date
                date_str = message.db_date_created.strftime("%b %d")
                
                # Add tag indicator
                tag_display = "|gNEW|n" if is_new else "MAIL"
                if is_job:
                    tag_display = "|gNEW JOB|n" if is_new else "|mJOB|n"
                
                # Add row to table
                table.add_row(
                    i,
                    sender_name,
                    subject, 
                    date_str
                )
            
            # Format columns
            table.reformat_column(0, width=6)
            table.reformat_column(1, width=18)
            table.reformat_column(2, width=30)
            table.reformat_column(3, width=24)
            
            # Display table
            self.caller.msg(str(table))
            self.caller.msg("|015" + "-" * _WIDTH + "|n")
        else:
            self.caller.msg("There are no messages in your inbox.")

    def display_sent_mail(self):
        """
        Display messages sent by the caller.
        """
        messages = self.get_sent_mail()

        if messages:
            # Create table
            _HEAD_CHAR = "|-"
            _WIDTH = 78
            
            # Display header
            self.caller.msg("|015" + "-" * _WIDTH + "|n")
            self.caller.msg(f"|ySent Mail:|n {len(messages)} messages")
            
            # Create table with headers
            table = evtable.EvTable(
                "|wID|n",
                "|wTo|n",
                "|wSubject|n",
                "|wSent|n",
                table=None,
                border="header",
                width=_WIDTH
            )
            
            # Add each message
            for i, message in enumerate(messages, 1):
                # Get recipient names
                recipient_names = []
                if hasattr(message, 'receivers'):
                    if isinstance(message.receivers, list):
                        for receiver in message.receivers:
                            if hasattr(receiver, 'get_display_name'):
                                recipient_names.append(receiver.get_display_name(self.caller))
                            elif hasattr(receiver, 'username'):
                                recipient_names.append(receiver.username)
                            else:
                                recipient_names.append(str(receiver))
                    else:
                        # Handle message.receivers as a queryset
                        try:
                            for receiver in message.receivers.all():
                                if hasattr(receiver, 'get_display_name'):
                                    recipient_names.append(receiver.get_display_name(self.caller))
                                elif hasattr(receiver, 'username'):
                                    recipient_names.append(receiver.username)
                                else:
                                    recipient_names.append(str(receiver))
                        except Exception as e:
                            logger.log_err(f"Error retrieving recipients: {str(e)}")
                            
                # If we couldn't determine recipients from receivers attribute,
                # try to extract from the header
                if not recipient_names and message.db_header and message.db_header.startswith("TO:"):
                    try:
                        # Extract recipient names from TO: header
                        to_part = message.db_header[3:].strip()
                        recipient_names = [name.strip() for name in to_part.split(",")]
                    except Exception as e:
                        logger.log_err(f"Error extracting recipients from header: {str(e)}")
                
                recipient_str = ", ".join(recipient_names) if recipient_names else "Unknown"
                
                # Format subject 
                subject = message.db_header or ""
                # Remove "TO:" prefix if present
                if subject.startswith("TO:"):
                    # Extract the actual subject after recipient names
                    parts = subject[3:].split(":", 1)
                    if len(parts) > 1:
                        # If there's a colon after the recipients, use what follows as subject
                        subject = parts[1].strip()
                    else:
                        # Otherwise, just use the cleaned TO part
                        subject = parts[0].strip()
                
                # Format date
                date_str = message.db_date_created.strftime("%b %d %H:%M")
                
                # Add row to table
                table.add_row(
                    i,
                    recipient_str[:16] + "..." if len(recipient_str) > 19 else recipient_str,
                    subject[:27] + "..." if len(subject) > 30 else subject, 
                    date_str
                )
            
            # Format columns
            table.reformat_column(0, width=6)
            table.reformat_column(1, width=18)
            table.reformat_column(2, width=30)
            table.reformat_column(3, width=24)
            
            # Display table
            self.caller.msg(str(table))
            self.caller.msg("|015" + "-" * _WIDTH + "|n")
        else:
            self.caller.msg("You haven't sent any messages.")
            # Add some debug info to help diagnose issues
            if not self.account_caller:
                self.caller.msg("Debug: Using character account for sender")
            
            try:
                # Log some debug info to help diagnose issues
                if self.account_caller:
                    sender = self.caller
                else:
                    sender = self.caller.account
                
                # Try to find messages with TO: header
                to_messages = Msg.objects.filter(
                    db_sender_accounts=sender,
                    db_header__startswith="TO:"
                ).count()
                
                # Try to find messages with mail tags
                mail_messages = Msg.objects.filter(
                    db_sender_accounts=sender,
                    db_tags__db_category="mail",
                    db_tags__db_key="mail"
                ).count()
                
                # Find messages with sent tag
                sent_messages = Msg.objects.filter(
                    db_sender_accounts=sender,
                    db_tags__db_category="mail",
                    db_tags__db_key="sent"
                ).count()
                
                # Count all messages from this sender
                all_sent = Msg.objects.filter(db_sender_accounts=sender).count()
                
                # Send debug to player
                self.caller.msg(f"Debug: Found {all_sent} total messages, {to_messages} with TO: header, "
                               f"{mail_messages} with mail tag, {sent_messages} with sent tag")
                
                # Also log for server logs
                logger.log_info(f"Sender {sender.username} has {all_sent} total msgs, {to_messages} with TO: header, "
                              f"{mail_messages} with mail tag, {sent_messages} with sent tag")
                
                # Check recent messages (last 30 days)
                one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
                recent_msgs = Msg.objects.filter(
                    db_sender_accounts=sender,
                    db_date_created__gte=one_month_ago
                ).count()
                self.caller.msg(f"Debug: Found {recent_msgs} messages sent in the last 30 days")
                
                # Check the last 5 messages for additional debugging
                last_msgs = Msg.objects.filter(
                    db_sender_accounts=sender
                ).order_by('-db_date_created')[:5]
                
                if last_msgs:
                    self.caller.msg("Debug: Last 5 message info:")
                    for i, msg in enumerate(last_msgs):
                        header = msg.db_header if msg.db_header else "None"
                        date = msg.db_date_created.strftime("%Y-%m-%d %H:%M:%S")
                        self.caller.msg(f"  {i+1}. ID: {msg.id}, Header: {header}, Date: {date}")
                
            except Exception as e:
                self.caller.msg(f"Debug: Error checking messages: {e}")

    def display_message(self, message):
        """
        Display an individual mail message with proper formatting.
        """
        _HEAD_CHAR = "|015-|n"
        _SUB_HEAD_CHAR = "-"
        _WIDTH = 78
        
        messageForm = []
        messageForm.append(_HEAD_CHAR * _WIDTH)
        
        # Get sender name
        sender_name = "Unknown"
        if hasattr(message, 'senders'):
            if isinstance(message.senders, list):
                if message.senders:
                    sender = message.senders[0]
                    if hasattr(sender, 'get_display_name'):
                        sender_name = sender.get_display_name(self.caller)
                    elif hasattr(sender, 'username'):
                        sender_name = sender.username
                    else:
                        sender_name = str(sender)
            else:
                # Assume it's a queryset
                try:
                    # Check if it has a first() method (queryset)
                    if hasattr(message.senders, 'first') and message.senders.first():
                        sender = message.senders.first()
                        sender_name = sender.get_display_name(self.caller)
                    # Check if exists() method is available (queryset)
                    elif hasattr(message.senders, 'exists') and message.senders.exists():
                        sender = message.senders.all()[0]
                        sender_name = sender.get_display_name(self.caller)
                except Exception as e:
                    logger.log_err(f"Error getting sender name: {str(e)}")
                    
        messageForm.append("|wFrom:|n %s" % sender_name)
        
        # Format date
        day = message.db_date_created.day
        messageForm.append(
            "|wSent:|n %s"
            % message.db_date_created.strftime(f"%b {day}, %Y - %H:%M:%S")
        )
        
        # Add subject
        messageForm.append("|wSubject:|n %s" % message.db_header)
        messageForm.append(_SUB_HEAD_CHAR * _WIDTH)
        
        # Add message content
        messageForm.append(message.db_message)
        messageForm.append(_HEAD_CHAR * _WIDTH)
        
        # Mark as read
        try:
            message.tags.remove("new", category="mail")
            message.tags.add("mail", category="mail")  # Ensure mail tag is present
        except Exception as e:
            logger.log_err(f"Error marking message as read: {str(e)}")
        
        # Display the formatted message
        self.caller.msg("\n".join(messageForm))

    def display_sent_message(self, message):
        """
        Display an individual sent mail message with proper formatting.
        """
        _HEAD_CHAR = "|015-|n"
        _SUB_HEAD_CHAR = "-"
        _WIDTH = 78
        
        messageForm = []
        messageForm.append(_HEAD_CHAR * _WIDTH)
        
        # Get recipient names
        recipient_names = []
        if hasattr(message, 'receivers'):
            if isinstance(message.receivers, list):
                for receiver in message.receivers:
                    if hasattr(receiver, 'get_display_name'):
                        recipient_names.append(receiver.get_display_name(self.caller))
                    elif hasattr(receiver, 'username'):
                        recipient_names.append(receiver.username)
                    else:
                        recipient_names.append(str(receiver))
            else:
                # Handle message.receivers as a queryset
                try:
                    for receiver in message.receivers.all():
                        if hasattr(receiver, 'get_display_name'):
                            recipient_names.append(receiver.get_display_name(self.caller))
                        elif hasattr(receiver, 'username'):
                            recipient_names.append(receiver.username)
                        else:
                            recipient_names.append(str(receiver))
                except Exception as e:
                    logger.log_err(f"Error retrieving recipients: {str(e)}")
        
        # If we couldn't determine recipients from receivers attribute,
        # try to extract from the header
        if not recipient_names and message.db_header and message.db_header.startswith("TO:"):
            try:
                # Extract recipient names from TO: header
                to_part = message.db_header[3:].strip()
                # If there's a colon, the recipient is before it
                if ":" in to_part:
                    to_part = to_part.split(":", 1)[0]
                recipient_names = [name.strip() for name in to_part.split(",")]
            except Exception as e:
                logger.log_err(f"Error extracting recipients from header: {str(e)}")
        
        recipient_str = ", ".join(recipient_names) if recipient_names else "Unknown"
        
        messageForm.append("|wTo:|n %s" % recipient_str)
        
        # Format date
        day = message.db_date_created.day
        messageForm.append(
            "|wSent:|n %s"
            % message.db_date_created.strftime(f"%b {day}, %Y - %H:%M:%S")
        )
        
        # Add subject - extract it from the TO: header if possible
        subject = message.db_header or ""
        if subject.startswith("TO:"):
            # Extract the actual subject after recipient names
            parts = subject[3:].split(":", 1)
            if len(parts) > 1:
                # If there's a colon after the recipients, use what follows as subject
                subject = parts[1].strip()
            else:
                # Otherwise, just use the cleaned TO part
                subject = parts[0].strip()
        
        messageForm.append("|wSubject:|n %s" % subject)
        messageForm.append(_SUB_HEAD_CHAR * _WIDTH)
        
        # Add message content
        messageForm.append(message.db_message)
        messageForm.append(_HEAD_CHAR * _WIDTH)
        
        # Display the formatted message
        self.caller.msg("\n".join(messageForm))

    def get_all_mail(self):
        """
        Get all the mail for the caller, with page messages filtered out.
        Uses a comprehensive multi-stage approach.
        """
        # Get receiver account
        if self.account_caller:
            receiver = self.caller
        else:
            receiver = self.caller.account
        
        # APPROACH 1: Get messages using parent implementation
        try:
            parent_messages = super().get_all_mail()
        except Exception as e:
            logger.log_err(f"Error in parent mail retrieval: {str(e)}")
            parent_messages = []
            
        # APPROACH 2: Direct database query for all potential mail
        try:
            # Look for any message with mail or new tags
            tagged_messages = Msg.objects.filter(
                db_receivers_accounts=receiver
            ).filter(
                Q(db_tags__db_key='mail', db_tags__db_category='mail') |
                Q(db_tags__db_key='new', db_tags__db_category='mail') |
                Q(db_tags__db_key='MAIL')
            ).distinct()
        except Exception as e:
            logger.log_err(f"Error in tagged messages query: {str(e)}")
            tagged_messages = []
            
        # APPROACH 3: Look for messages from specific senders
        try:
            sender_messages = Msg.objects.filter(
                db_receivers_accounts=receiver
            ).filter(
                Q(db_sender_accounts__username='Nicole') |
                Q(db_sender_accounts__username='Jimmy') |
                Q(db_sender_accounts__username='Soma') |
                Q(db_sender_accounts__username='Frank') |
                Q(db_sender_accounts__username='Marid')
            ).distinct()
        except Exception as e:
            logger.log_err(f"Error in sender messages query: {str(e)}")
            sender_messages = []
            
        # APPROACH 4: Look specifically for job-related messages
        try:
            job_messages = Msg.objects.filter(
                db_receivers_accounts=receiver,
                db_message__contains="Job #"
            ).distinct()
        except Exception as e:
            logger.log_err(f"Error in job messages query: {str(e)}")
            job_messages = []
            
        # Add a more specific query for job subject lines
        try:
            job_subject_messages = Msg.objects.filter(
                db_receivers_accounts=receiver,
                db_header__contains="Job #"
            ).distinct()
        except Exception as e:
            logger.log_err(f"Error in job subject query: {str(e)}")
            job_subject_messages = []
            
        # APPROACH 5: Get recent messages (last 24 hours)
        try:
            one_day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
            recent_messages = Msg.objects.filter(
                db_receivers_accounts=receiver,
                db_date_created__gte=one_day_ago
            ).distinct()
        except Exception as e:
            logger.log_err(f"Error in recent messages query: {str(e)}")
            recent_messages = []
            
        # Combine all approaches
        all_messages = list(parent_messages)
        message_ids = {msg.id for msg in all_messages}
        
        # Add messages from other approaches, avoiding duplicates
        for msg_set in [tagged_messages, sender_messages, job_messages, job_subject_messages, recent_messages]:
            for msg in msg_set:
                if msg.id not in message_ids:
                    all_messages.append(msg)
                    message_ids.add(msg.id)
        
        # Only filter out messages that are DEFINITELY pages
        filtered_messages = []
        for msg in all_messages:
            # Skip only very obvious page messages
            
            # Check for page tag
            is_page = False
            for tag in msg.tags.all():
                tag_key = str(tag)
                if tag_key == "page":
                    is_page = True
                    break
            
            if is_page:
                continue
                
            # Skip sent mail copies that aren't TO us
            if msg.db_header and msg.db_header.startswith("TO:") and receiver.username not in msg.db_header:
                continue
                
            # Only skip messages that are clearly pages by having BOTH indicators
            if msg.db_message and isinstance(msg.db_message, str):
                if "From afar," in msg.db_message and "pages:" in msg.db_message:
                    continue
            
            # Keep the message if it passed the minimal filters
            filtered_messages.append(msg)
        
        # Sort by date created, oldest first
        filtered_messages = sorted(filtered_messages, key=lambda x: x.db_date_created)
            
        return filtered_messages

    def get_sent_mail(self):
        """
        Get messages sent by the caller.
        """
        # Get sender account
        if self.account_caller:
            sender = self.caller
        else:
            sender = self.caller.account
            
        # Get messages where the caller is the sender
        try:
            # Main query - find messages with the sent tag
            sent_tagged = Msg.objects.filter(
                db_sender_accounts=sender,
                db_tags__db_category="mail",
                db_tags__db_key="sent"
            ).distinct()
            
            logger.log_info(f"Found {sent_tagged.count()} sent-tagged messages for {sender.username}")
            
            # Also find messages with mail tag
            mail_tagged = Msg.objects.filter(
                db_sender_accounts=sender,
                db_tags__db_category="mail",
                db_tags__db_key="mail"
            ).distinct()
            
            logger.log_info(f"Found {mail_tagged.count()} mail-tagged messages for {sender.username}")
            
            # As a backup, also find messages with TO: in header
            to_messages = Msg.objects.filter(
                db_sender_accounts=sender,
                db_header__startswith="TO:"
            ).distinct()
            
            logger.log_info(f"Found {to_messages.count()} messages with TO: header for {sender.username}")
            
            # Combine all queries, avoiding duplicates
            combined_messages = list(sent_tagged)
            msg_ids = {msg.id for msg in combined_messages}
            
            # Add mail-tagged messages
            for msg in mail_tagged:
                if msg.id not in msg_ids:
                    combined_messages.append(msg)
                    msg_ids.add(msg.id)
            
            # Add TO: header messages
            for msg in to_messages:
                if msg.id not in msg_ids:
                    combined_messages.append(msg)
                    msg_ids.add(msg.id)
            
            logger.log_info(f"Combined total: {len(combined_messages)} messages")
            
            # If we still don't have any messages, try a more generic approach
            if not combined_messages:
                # Look for any messages sent in the last month
                one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
                recent_sent = Msg.objects.filter(
                    db_sender_accounts=sender,
                    db_date_created__gte=one_month_ago
                ).distinct()
                
                logger.log_info(f"Fallback query found {recent_sent.count()} recent messages")
                combined_messages = list(recent_sent)
            
        except Exception as e:
            logger.log_err(f"Error retrieving sent mail: {str(e)}")
            return []
            
        # Filter out page messages, keeping only genuine mail
        filtered_messages = []
        
        # Track filtering stats for debugging
        excluded_count = {
            "page_tag": 0,
            "page_content": 0,
            "job_notification": 0,
            "not_mail_like": 0,
            "system_message": 0
        }
        
        for msg in combined_messages:
            try:
                # Initialize debugging info for this message
                message_debug = {
                    "id": msg.id,
                    "header": msg.db_header,
                    "date": msg.db_date_created.strftime("%Y-%m-%d %H:%M:%S"),
                    "tags": [],
                    "reason_excluded": None
                }
                
                # Get all tags for debugging - safely handle different tag types
                try:
                    for tag in msg.tags.all():
                        # Handle tag object which might be a string or a DB object
                        if isinstance(tag, str):
                            tag_info = tag
                        else:
                            try:
                                # Try to access tag.db_key - this is a DB object
                                tag_key = tag.db_key if hasattr(tag, 'db_key') else str(tag)
                                tag_category = tag.db_category if hasattr(tag, 'db_category') else "None"
                                tag_info = f"{tag_key}:{tag_category}"
                            except AttributeError:
                                # Fallback to string representation
                                tag_info = str(tag)
                        
                        message_debug["tags"].append(tag_info)
                except Exception as e:
                    logger.log_err(f"Error processing tags for message {msg.id}: {str(e)}")
                    message_debug["tags"].append("Error processing tags")
                
                # Prioritize messages with sent tag - skip filtering for these
                has_sent_tag = False
                try:
                    for tag in msg.tags.all():
                        # Check if this is the sent tag
                        if isinstance(tag, str) and tag == "sent":
                            has_sent_tag = True
                            break
                        elif hasattr(tag, 'db_key') and hasattr(tag, 'db_category'):
                            if tag.db_category == "mail" and tag.db_key == "sent":
                                has_sent_tag = True
                                break
                except Exception as e:
                    logger.log_err(f"Error checking sent tag for message {msg.id}: {str(e)}")
                
                # Also check if this has a TO: header, which is a strong indicator of sent mail
                has_to_header = msg.db_header and msg.db_header.startswith("TO:")
                
                if has_sent_tag or has_to_header:
                    # We're certain this is a sent mail - add it without further filtering
                    filtered_messages.append(msg)
                    logger.log_info(f"Including message {msg.id} based on sent tag or TO: header")
                    continue
                
                # 1. Skip messages with page tag or other non-mail tags
                is_page = False
                is_mail = False
                
                try:
                    for tag in msg.tags.all():
                        if isinstance(tag, str):
                            # String tag
                            if tag == "page":
                                is_page = True
                                break
                            elif tag in ["mail", "new", "sent"]:
                                is_mail = True
                        else:
                            # DB object tag
                            try:
                                tag_key = tag.db_key if hasattr(tag, 'db_key') else str(tag)
                                tag_category = tag.db_category if hasattr(tag, 'db_category') else None
                                
                                if tag_key == "page":
                                    is_page = True
                                    break
                                elif tag_category == "mail" and tag_key in ["mail", "new", "sent"]:
                                    is_mail = True
                            except AttributeError:
                                # Skip tags that don't have the expected attributes
                                continue
                except Exception as e:
                    logger.log_err(f"Error processing tags for filtering: {str(e)}")
                
                # Skip messages with non-mail tags unless they have a TO: header
                if is_page:
                    excluded_count["page_tag"] += 1
                    message_debug["reason_excluded"] = "has page tag"
                    continue
                
                # 2. Skip messages that look like pages based on content
                if msg.db_message and isinstance(msg.db_message, str):
                    message_content = msg.db_message.lower()
                    if any(marker in message_content for marker in [
                        "from afar,", "pages:", "pages you", "page to",
                        "to afar,", "long-distance to", "remotely to", 
                        "whispers to you", "whispers,"
                    ]):
                        excluded_count["page_content"] += 1
                        message_debug["reason_excluded"] = "content looks like page"
                        continue
                
                # 3. Skip job notifications (that aren't direct messages)
                if ((msg.db_message and "Job #" in msg.db_message) or 
                    (msg.db_header and "Job #" in msg.db_header)):
                    if not (msg.db_header and msg.db_header.startswith("TO:")):
                        excluded_count["job_notification"] += 1
                        message_debug["reason_excluded"] = "job notification"
                        continue
                
                # 4. Verify this is an actual mail-like message
                is_mail_like = False
                
                # Messages with TO: header are definitely mail
                if msg.db_header and msg.db_header.startswith("TO:"):
                    is_mail_like = True
                # Messages with mail tag are mail
                elif is_mail:
                    is_mail_like = True
                # Check for receivers as a mail criterion
                elif hasattr(msg, 'receivers') and msg.receivers:
                    is_mail_like = True
                
                if not is_mail_like:
                    excluded_count["not_mail_like"] += 1
                    message_debug["reason_excluded"] = "not mail-like"
                    continue
                
                # 5. Skip system messages that aren't mail
                if (not is_mail and not msg.db_header) or (msg.db_header == "System"):
                    excluded_count["system_message"] += 1
                    message_debug["reason_excluded"] = "system message"
                    continue
                
                # Include message if it passed all filters
                filtered_messages.append(msg)
                
                # Debug: Log info about each included message
                logger.log_info(f"Including message {msg.id} with header '{msg.db_header}'")
                
            except Exception as e:
                # Log any errors processing individual messages but continue
                logger.log_err(f"Error processing message {msg.id}: {str(e)}")
                continue
        
        # Log filtering stats
        logger.log_info(f"Filtering stats: {excluded_count}")
        logger.log_info(f"After filtering, found {len(filtered_messages)} sent messages for {sender.username}")
        
        # Sort by date, newest first (for sent mail it's more useful to see recent first)
        filtered_messages = sorted(filtered_messages, key=lambda x: x.db_date_created, reverse=True)
        
        # As a fallback, if no messages passed filtering but we found TO: header messages, include them
        if not filtered_messages and to_messages:
            logger.log_info("No messages passed filtering - using TO: header messages as fallback")
            filtered_messages = list(to_messages)
            filtered_messages = sorted(filtered_messages, key=lambda x: x.db_date_created, reverse=True)
        
        return filtered_messages

class CmdMailCharacter(CmdMail):
    """
    Character-level mail command.
    """
    account_caller = False