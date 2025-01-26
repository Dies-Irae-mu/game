"""
Page command - allows paging by both account and character name
"""
from evennia.commands.default.comms import CmdPage as DefaultCmdPage
from evennia import search_object, search_account
from evennia.utils import create
from evennia.utils.utils import make_iter
from evennia.comms.models import Msg
from evennia.utils.search import search_object
from typeclasses.characters import Character
from django.contrib.auth.models import User as AccountDB

class CmdPage(DefaultCmdPage):
    """
    send a private message to another account

    Usage:
      page[/switches] [<account/character>,<account/character>,... = <message>]
      tell        ''
      page <number>

    Switch:
      last - shows who you last messaged
      list - show your last <number> of tells/pages (default)

    Send a message to target user (if online). If no
    argument is given, you will get a list of your latest messages.
    You can page either by account name or by character name.
    """
    key = "page"
    aliases = ["tell", "p"]
    help_category = "Communications"

    def func(self):
        """Implement function using the parent"""
        caller = self.caller

        # Get the messages we've sent (not to channels)
        pages_we_sent = Msg.objects.get_messages_by_sender(caller).exclude(
            db_receivers_accounts__in=[caller]).order_by("-db_date_created")

        if "last" in self.switches:
            if pages_we_sent:
                recv = ",".join(obj.key for obj in pages_we_sent[0].receivers)
                self.msg(f"You last paged |c{recv}|n:{pages_we_sent[0].message}")
                return
            else:
                self.msg("You haven't paged anyone yet.")
                return

        # Handle message history display
        if self.args and "=" not in self.args:
            if self.args.isdigit():
                # Show message history
                number = int(self.args)
                pages = pages_we_sent[:number]
                if pages:
                    msg = "\n".join(
                        "|w%s|n |c%s|n: %s"
                        % (
                            msg.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                            ",".join(obj.key for obj in msg.receivers),
                            msg.message,
                        )
                        for msg in pages
                    )
                    self.msg("Your last %i pages:\n%s" % (len(pages), msg))
                else:
                    self.msg("You haven't paged anyone yet.")
                return
            else:
                # No = sign, just a message - send to last person paged
                if pages_we_sent:
                    # Get the last recipient and construct the command
                    last_recipient = pages_we_sent[0].receivers[0]
                    recipient_name = last_recipient.puppet.name if hasattr(last_recipient, 'puppet') and last_recipient.puppet else last_recipient.key
                    # Recursively call the command with the properly formatted string
                    self.caller.execute_cmd(f"page {recipient_name}={self.args}")
                    return
                else:
                    self.msg("You haven't paged anyone yet.")
                    return

        # Parse the message for new pages
        if "=" not in self.args:
            self.msg("Usage: page <character>[,<character2>,...]=<message>")
            return
            
        targets, message = self.args.split("=", 1)
        message = message.strip()
        
        # Split recipients by spaces or commas
        recipient_list = [r.strip() for r in targets.replace(",", " ").split()]
        
        # Process the recipients
        account_recipients = []
        offline_recipients = []
        failed_recipients = []
        
        for recipient in recipient_list:
            target_obj = None
            # First try direct character search using evennia's search_object
            chars = search_object(recipient, typeclass=Character, exact=True)
            
            if chars:
                target_obj = chars[0]  # Take the first exact match
            else:
                # If no exact match, try case-insensitive search
                chars = search_object(recipient, typeclass=Character)
                matching_chars = [char for char in chars if char.key.lower() == recipient.lower()]
                if matching_chars:
                    target_obj = matching_chars[0]
                else:
                    # If still no match, try alias as last resort
                    target_obj = Character.get_by_alias(recipient.lower())

            if target_obj:
                # Try to get the account through different methods
                account = None
                if hasattr(target_obj, 'account') and target_obj.account:
                    account = target_obj.account
                elif hasattr(target_obj, 'player'):  # Some systems use 'player' instead of 'account'
                    account = target_obj.player
                
                if not account:
                    offline_recipients.append(target_obj.name)
                    continue
                    
                # Check if the account is actually connected
                if not account.sessions.count():
                    offline_recipients.append(target_obj.name)
                    continue
                    
                # If we get here, the character has a valid, connected account
                account_recipients.append(account)
                continue

            # If we get here, we couldn't find the recipient
            failed_recipients.append(recipient)

        if not account_recipients and (offline_recipients or failed_recipients):
            # No valid online recipients found
            if failed_recipients:
                self.msg(f"Could not find: {', '.join(failed_recipients)}")
            if offline_recipients:
                self.msg(f"Currently offline: {', '.join(offline_recipients)}")
            return

        # Get caller's character name if available
        caller_name = caller.name

        # Tell the accounts they got a message
        received = []
        for target in account_recipients:
            if not target.access(caller, "msg"):
                self.msg(f"You are not allowed to page {target}.")
                continue
            
            # Get the character name if available
            char_name = target.puppet.name if target.puppet else target.name
            
            # Format recipients list for header
            other_recipients = [
                t.puppet.name if t.puppet else t.name 
                for t in account_recipients
                if t != target
            ]
            
            # Format the header
            if other_recipients:
                others = f"{', '.join(other_recipients[:-1])} and {other_recipients[-1]}" if len(other_recipients) > 1 else other_recipients[0]
                header = f"(To: {char_name} and {others}) From afar,"
            else:
                header = f"(To: {char_name}) From afar,"
            
            # Format and send the message
            if message.startswith(":"):
                formatted_message = f"From afar, {caller_name} {message[1:].strip()}"
            else:
                formatted_message = f"{caller_name} pages: {message}"
                
            target.msg(formatted_message)
            received.append(f"|c{char_name}|n")

        # Format the confirmation message
        if received:
            if len(received) == 1:
                if message.startswith(":"):
                    self.msg(f"Long distance to {received[0]}: {caller_name} {message[1:].strip()}")
                else:
                    # Get the character name for the confirmation message
                    char_name = account_recipients[0].puppet.name if account_recipients[0].puppet else account_recipients[0].name
                    self.msg(f"You paged {char_name} with: '{message}'")
            else:
                # Get character names for all recipients
                char_names = [t.puppet.name if t.puppet else t.name for t in account_recipients]
                if message.startswith(":"):
                    self.msg(f"To ({', '.join(char_names)}): {caller_name} {message[1:].strip()}")
                else:
                    self.msg(f"To ({', '.join(char_names)}) you paged: '{message}'")

        # Report any offline/not-found users
        if offline_recipients:
            self.msg(f"Currently offline: {', '.join(offline_recipients)}")
        if failed_recipients:
            self.msg(f"Could not find: {', '.join(failed_recipients)}")

        # Create persistent message object for history
        if account_recipients:
            target_perms = " or ".join([f"id({target.id})" for target in account_recipients + [caller]])
            create.create_message(
                caller,
                message,
                receivers=account_recipients,
                locks=(
                    f"read:{target_perms} or perm(Admin);"
                    f"delete:id({caller.id}) or perm(Admin);"
                    f"edit:id({caller.id}) or perm(Admin)"
                ),
                tags=[("page", "comms")],
            )