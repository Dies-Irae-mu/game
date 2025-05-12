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

    def func(self):
        """
        Overridden func method to fix status display.
        """
        if not self.switches and not self.args:
            # list messages - this is the part we're overriding
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
                    
                    status = "|gNEW|n" if is_new else ""
                    
                    # Add safety check for empty senders list
                    sender_name = "Unknown"
                    if message.senders:
                        sender_name = message.senders[0].get_display_name(self.caller)

                    # Add row without the extra status column
                    table.add_row(
                        index,
                        sender_name,
                        message.header,
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
            mind_max = max(0, all_mail.count() - 1)
            try:
                mind = max(0, min(mind_max, int(self.lhs) - 1))
                message = all_mail[mind]
            except (ValueError, IndexError):
                self.caller.msg("'%s' is not a valid mail id." % self.lhs)
                return

            messageForm = []
            if message:
                _HEAD_CHAR = "|015-|n"
                _SUB_HEAD_CHAR = "-"
                _WIDTH = 78
                
                messageForm.append(_HEAD_CHAR * _WIDTH)
                # Add safety check for empty senders list
                sender_name = "Unknown"
                if message.senders:
                    sender_name = message.senders[0].get_display_name(self.caller)
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
            self.caller.msg("\n".join(messageForm))
            message.tags.remove("new", category="mail")
            message.tags.add("-", category="mail")
        else:
            # call the original method for all other cases
            super().func()

class CmdMailCharacter(CmdMail):
    account_caller = False 