"""
Fixed mail command that properly displays message status
"""
from evennia.contrib.game_systems.mail import CmdMail as EvenniaCmdMail
from evennia.utils import evtable

class CmdMail(EvenniaCmdMail):
    """
    Communicate with others by sending mail.

    Usage:
      @mail       - Displays all the mail an account has in their mailbox
      @mail <#>   - Displays a specific message
      @mail <accounts>=<subject>/<message>
              - Sends a message to the comma separated list of accounts.
      @mail/delete <#> - Deletes a specific message
      @mail/forward <account list>=<#>[/<Message>]
              - Forwards an existing message to the specified list of accounts,
                original message is delivered with optional Message prepended.
      @mail/reply <#>=<message>
              - Replies to a message #. Prepends message to the original
                message text.
    Switches:
      delete  - deletes a message
      forward - forward a received message to another object with an optional message attached.
      reply   - Replies to a received message, appending the original message to the bottom.
    Examples:
      @mail 2
      @mail Griatch=New mail/Hey man, I am sending you a message!
      @mail/delete 6
      @mail/forward feend78 Griatch=4/You guys should read this.
      @mail/reply 9=Thanks for the info!
    """

    def get_all_mail(self):
        """
        Overridden get_all_mail method to ensure proper ordering and retrieval
        of all mail messages.
        """
        from evennia.utils import logger
        
        # Get the mail messages using the parent class implementation
        # The original EvenniaCmdMail.get_all_mail() method
        from evennia.utils.utils import make_iter
        from evennia.comms.models import Msg
        
        # This is how Evennia's mail command gets messages
        if self.account_caller:
            receiver = self.caller
        else:
            receiver = self.caller.account
        
        # Get all messages where this account is a receiver
        messages = Msg.objects.get_by_tag(category="mail").filter(db_receivers_accounts=receiver)
        
        # Safety check for messages directly
        direct_messages = Msg.objects.filter(db_receivers_accounts=receiver)
        if direct_messages.exists():
            # Check each message to ensure it has proper mail tags
            for msg in direct_messages:
                # If message doesn't have mail tag, add it
                if not msg.tags.get(category='mail'):
                    msg.tags.add("mail", category="mail")
                
                # Check if it's new (for display purposes)
                is_new = False
                for tag in msg.tags.all():
                    if hasattr(tag, 'db_category') and tag.db_category == "mail" and tag.db_key == "new":
                        is_new = True
                        break
        
        # Order by oldest first (ascending) so new messages appear at the bottom
        messages = sorted(messages, key=lambda x: x.db_date_created)
        
        return messages

    def func(self):
        """
        Overridden func method to fix status display.
        """
        from evennia.utils import logger
        
        if not self.switches and not self.args:
            # List messages - this is the part we're overriding
            messages = self.get_all_mail()

            if messages:
                # Create table without the extra empty column header
                _HEAD_CHAR = "|015-|n"
                _SUB_HEAD_CHAR = "-"
                _WIDTH = 78
                
                table = evtable.EvTable(
                    "|wID|n",
                    "|wFrom|n",
                    "|wSubject|n",
                    "|wArrived|n",
                    table=None,
                    border="header",
                    header_line_char=_SUB_HEAD_CHAR,
                    width=_WIDTH,
                )
                index = 1
                for message in messages:
                    # Get the "new" status of the message
                    is_new = False
                    for tag in message.tags.all():
                        if hasattr(tag, 'db_category') and tag.db_category == "mail" and tag.db_key == "new":
                            is_new = True
                            break
                    
                    status_marker = " *" if is_new else ""
                    
                    # Add safety check for empty senders list
                    sender_name = "Unknown"
                    # Handle senders being either a list or a queryset
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
                    
                    # Include NEW marker in subject for new messages
                    subject = f"{message.header}{status_marker}"
                    
                    # Add row without the extra status column
                    table.add_row(
                        index,
                        sender_name,
                        subject,
                        message.db_date_created.strftime("%b %d"),
                    )
                    index += 1

                # Format columns with widths that sum to 78
                table.reformat_column(0, width=6)
                table.reformat_column(1, width=18)
                table.reformat_column(2, width=41)  # Increased from 34 to make total width 78
                table.reformat_column(3, width=13)

                self.caller.msg(_HEAD_CHAR * _WIDTH)
                self.caller.msg(str(table))
                self.caller.msg(_HEAD_CHAR * _WIDTH)
            else:
                self.caller.msg("There are no messages in your inbox.")
        elif not self.switches and self.args and not self.rhs:
            # Viewing a specific message by ID
            all_mail = self.get_all_mail()
            
            # Make sure we have messages
            if not all_mail:
                self.caller.msg("You have no messages.")
                return
                
            # Convert all_mail to a list if it's not already
            all_mail = list(all_mail)
            
            # Validate the message ID
            try:
                mind = int(self.lhs) - 1  # Convert to 0-based index
                # Ensure index is within valid range
                if mind < 0 or mind >= len(all_mail):
                    self.caller.msg(f"'{self.lhs}' is not a valid mail id.")
                    return
                    
                message = all_mail[mind]
            except (ValueError, IndexError) as e:
                self.caller.msg(f"'{self.lhs}' is not a valid mail id.")
                return

            messageForm = []
            if message:
                _HEAD_CHAR = "|015-|n"
                _SUB_HEAD_CHAR = "-"
                _WIDTH = 78
                
                messageForm.append(_HEAD_CHAR * _WIDTH)
                # Add safety check for empty senders list
                sender_name = "Unknown"
                # Handle senders being either a list or a queryset
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
                # note that we cannot use %-d format here since Windows does not support it
                day = message.db_date_created.day
                messageForm.append(
                    "|wSent:|n %s"
                    % message.db_date_created.strftime(f"%b {day}, %Y - %H:%M:%S")
                )
                messageForm.append("|wSubject:|n %s" % message.header)
                messageForm.append(_SUB_HEAD_CHAR * _WIDTH)
                messageForm.append(message.message)
                messageForm.append(_HEAD_CHAR * _WIDTH)
                
                # Mark as read
                try:
                    message.tags.remove("new", category="mail")
                    message.tags.add("mail", category="mail")  # Ensure mail tag is present
                except Exception as e:
                    logger.log_err(f"Error marking message as read: {str(e)}")
                
            self.caller.msg("\n".join(messageForm))
        else:
            # call the original method for all other cases
            super().func()

class CmdMailCharacter(CmdMail):
    account_caller = False 