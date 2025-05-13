"""
Mail command implementation that filters out page messages from the display.
"""
from evennia.contrib.game_systems.mail import CmdMail as EvenniaCmdMail
from evennia.utils import evtable, logger
from evennia.comms.models import Msg
from django.db.models import Q
import datetime
from django.utils import timezone
from evennia.accounts.models import AccountDB

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
    Switches:
      delete  - deletes a message
      forward - forward a received message to another object with an optional message attached.
      reply   - Replies to a received message, appending the original message to the bottom.
    """

    def func(self):
        """
        Override func to handle mail operations with improved feedback.
        """
        # Case 1: Mail sending (no switches, args with =, possibly with /)
        if not self.switches and self.args and "=" in self.args:
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
                
                # Parse subject and message if the / is present
                subject = ""
                message = rhs
                if "/" in rhs:
                    parts = rhs.split("/", 1)
                    subject = parts[0].strip()
                    message = parts[1].strip()
                    logger.log_info(f"Subject: {subject}, Message length: {len(message)}")
                    
                    # Let's explicitly log the full subject for debugging
                    logger.log_info(f"Full subject extracted: '{subject}'")
                
                # Store target recipients explicitly for later verification
                target_recipients = [r.lower().strip() for r in lhs.split(",")]
                logger.log_info(f"Target recipients (normalized): {target_recipients}")
                
                # Instead of trying to override Msg.create which may not exist,
                # we'll call the parent implementation and then tag the message afterward
                
                # Call original implementation for mail sending
                original_func = super().func
                result = original_func()
                
                # Find the actual sent message and ensure recipients have it tagged as 'new'
                if self.account_caller:
                    sender = self.caller
                else:
                    sender = self.caller.account
                
                # Look for the most recently sent message
                try:
                    timestamp_threshold = timezone.now() - datetime.timedelta(seconds=10)
                    recent_messages = Msg.objects.filter(
                        db_sender_accounts=sender,
                        db_date_created__gte=timestamp_threshold
                    ).order_by('-db_date_created')
                    
                    # If we found a message, ensure it's tagged as 'new' for recipients
                    if recent_messages.exists():
                        recent_msg = recent_messages.first()
                        logger.log_info(f"Ensuring message {recent_msg.id} is tagged as new for recipients")
                        
                        # Ensure 'new' tag is set for recipients
                        if hasattr(recent_msg, 'tags') and hasattr(recent_msg.tags, 'add'):
                            try:
                                # Add 'new' tag for recipients
                                recent_msg.tags.add("new", category="mail")
                                logger.log_info(f"Added 'new' tag to message {recent_msg.id}")
                            except Exception as e:
                                logger.log_err(f"Error adding 'new' tag: {str(e)}")
                except Exception as e:
                    logger.log_err(f"Error ensuring message is marked as new: {str(e)}")
                
                # Find the actual sent message
                if self.account_caller:
                    sender = self.caller
                else:
                    sender = self.caller.account
                
                # Look for the most recently sent message
                try:
                    timestamp_threshold = timezone.now() - datetime.timedelta(seconds=10)
                    recent_messages = Msg.objects.filter(
                        db_sender_accounts=sender,
                        db_date_created__gte=timestamp_threshold
                    ).order_by('-db_date_created')
                    
                    # Log all recent messages for debugging
                    logger.log_info(f"Found {recent_messages.count()} messages in last 10 seconds")
                    for idx, msg in enumerate(recent_messages[:5]):
                        header = msg.db_header or "No header"
                        msg_content = msg.db_message[:30] + "..." if msg.db_message and len(msg.db_message) > 30 else msg.db_message
                        logger.log_info(f"Message {idx+1}: ID={msg.id}, Header='{header}', Content='{msg_content}'")
                        
                        # Log receivers if possible
                        if hasattr(msg, 'receivers'):
                            try:
                                if isinstance(msg.receivers, list):
                                    receiver_list = [r.username if hasattr(r, 'username') else str(r) for r in msg.receivers]
                                else:
                                    receiver_list = [r.username if hasattr(r, 'username') else str(r) for r in msg.receivers.all()]
                                logger.log_info(f"  Receivers: {receiver_list}")
                            except Exception as e:
                                logger.log_info(f"  Error getting receivers: {str(e)}")
                    
                    # SIMPLIFIED APPROACH: Just use the most recent message
                    # This is more reliable than trying complex matching which might fail
                    if recent_messages.exists():
                        recent_sent = recent_messages.first()
                        logger.log_info(f"Using most recent message {recent_sent.id}")
                    else:
                        recent_sent = None
                        logger.log_info("No recent messages found")
                    
                    if recent_sent:
                        # Store the original header for logging
                        original_header = recent_sent.db_header
                        
                        # Before modifying, explicitly store recipients (only if attributes are supported)
                        if hasattr(recent_sent, 'attributes') and hasattr(recent_sent.attributes, 'add'):
                            try:
                                recent_sent.attributes.add("mail_recipients", target_recipients)
                                logger.log_info(f"Stored original recipients: {target_recipients}")
                            except Exception as e:
                                logger.log_err(f"Error storing recipients: {str(e)}")
                        
                        # Ensure it has the mail tag - add both mail and sent tags
                        if hasattr(recent_sent, 'tags') and hasattr(recent_sent.tags, 'add'):
                            # First clear any existing tags to avoid duplicates
                            try:
                                recent_sent.tags.clear(category="mail")
                                # Add our tags
                                recent_sent.tags.add("mail", category="mail")
                                recent_sent.tags.add("sent", category="mail")
                                logger.log_info(f"Added mail and sent tags to message {recent_sent.id}")
                                
                                # Add a special tag to make sure we can find it in get_sent_mail
                                recent_sent.tags.add("recent_sent", category="mail")
                                logger.log_info(f"Added recent_sent tag for easy retrieval")
                            except Exception as e:
                                logger.log_err(f"Error managing tags: {str(e)}")
                        
                        # Special handling for subject
                        # Always set the subject if we have one, regardless of current header format
                        if subject:
                            if recent_sent.db_header and recent_sent.db_header.startswith("TO:"):
                                # Format as "TO: recipient: subject"
                                header_parts = recent_sent.db_header.split(":", 2)
                                if len(header_parts) >= 2:
                                    # Construct new header with subject
                                    new_header = f"{header_parts[0]}:{header_parts[1]}: {subject}"
                                    recent_sent.db_header = new_header
                                    recent_sent.save()
                                    logger.log_info(f"Updated header from '{original_header}' to '{new_header}'")
                            else:
                                # For non-standard headers, add subject if possible
                                new_header = f"{recent_sent.db_header or 'Subject'}: {subject}"
                                recent_sent.db_header = new_header
                                recent_sent.save()
                                logger.log_info(f"Set non-standard header from '{original_header}' to '{new_header}'")
                                
                            # Also store subject in an attribute (only if attributes are supported)
                            if hasattr(recent_sent, 'attributes') and hasattr(recent_sent.attributes, 'add'):
                                try:
                                    recent_sent.attributes.add("mail_subject", subject)
                                    logger.log_info(f"Added mail_subject attribute: {subject}")
                                except Exception as e:
                                    logger.log_err(f"Error adding subject attribute: {str(e)}")
                            
                        # Force refresh our in-memory reference to ensure changes are visible
                        try:
                            recent_sent = Msg.objects.get(id=recent_sent.id)
                        except Exception as e:
                            logger.log_err(f"Error refreshing message: {str(e)}")
                        
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
                
                # Provide feedback to sender
                self.caller.msg("Mail sent successfully.")
                logger.log_info("Mail sent successfully")
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
                    elif isinstance(tag, str) and tag == "new":
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
                
                # Add row to table with unread indicator
                if is_new:
                    # Highlight unread messages
                    row_id = f"|g{i}|n"
                    row_sender = f"|g{sender_name}|n"
                    row_subject = subject if is_job else f"|g{subject}|n"
                    row_date = f"|g{date_str}|n"
                    
                    # Add STATUS indicator for unread
                    row_subject = f"|g[UNREAD]|n {row_subject}"
                else:
                    # Regular formatting for read messages 
                    row_id = str(i)
                    row_sender = sender_name
                    row_subject = subject
                    row_date = date_str
                
                table.add_row(
                    row_id,
                    row_sender,
                    row_subject, 
                    row_date
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
        
        # Mark as read by removing 'new' tag and ensuring 'mail' tag is present
        try:
            has_new_tag = False
            
            # Check if message has 'new' tag
            for tag in message.tags.all():
                if (hasattr(tag, 'db_category') and hasattr(tag, 'db_key') and 
                    tag.db_category == "mail" and tag.db_key == "new"):
                    has_new_tag = True
                    break
                elif isinstance(tag, str) and tag == "new":
                    has_new_tag = True
                    break
            
            # If message was new, remove 'new' tag and add tracking for this read
            if has_new_tag:
                logger.log_info(f"Marking message {message.id} as read")
                
                # Try different ways to remove the tag since 'new' might be stored differently
                try:
                    message.tags.remove("new", category="mail")
                except Exception as e:
                    logger.log_err(f"Error removing new tag (first attempt): {str(e)}")
                    
                    # Second attempt - try without category
                    try:
                        message.tags.remove("new")
                    except Exception as e2:
                        logger.log_err(f"Error removing new tag (second attempt): {str(e2)}")
                        
                        # Last attempt - try to clear all 'new' tags
                        try:
                            # Find and remove any tag with db_key='new'
                            for tag in message.tags.all():
                                if hasattr(tag, 'db_key') and tag.db_key == "new":
                                    message.tags.remove(tag)
                        except Exception as e3:
                            logger.log_err(f"Error removing new tag (final attempt): {str(e3)}")
                
                # Add a read timestamp attribute if possible
                if hasattr(message, 'attributes') and hasattr(message.attributes, 'add'):
                    try:
                        read_time = timezone.now()
                        message.attributes.add("read_at", read_time)
                        logger.log_info(f"Added read timestamp: {read_time}")
                    except Exception as e:
                        logger.log_err(f"Error adding read timestamp: {str(e)}")
            
            # Always ensure 'mail' tag is present
            try:
                message.tags.add("mail", category="mail")
            except Exception as e:
                logger.log_err(f"Error ensuring mail tag: {str(e)}")
                
        except Exception as e:
            logger.log_err(f"Error marking message as read: {str(e)}")
        
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
            one_day_ago = timezone.now() - datetime.timedelta(days=1)
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

class CmdMailCharacter(CmdMail):
    """
    Character-level mail command.
    """
    account_caller = False