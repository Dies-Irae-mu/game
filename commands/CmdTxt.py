"""
Text messaging command - allows IC text messaging between characters
"""
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils import create
from evennia.comms.models import Msg
from utils.search_helpers import search_character
from typeclasses.characters import Character

class CmdText(MuxCommand):
    """
    Send an in-character text message to other characters.

    Usage:
      +txt <character1> [<character2> ...] = <message>
      +txt/pic <character1> [<character2> ...] = <description>
      +txt/opt-in
      +txt/opt-out
      +txt <number>
      
    Switches:
      pic     - Send a picture instead of text
      opt-in  - Opt in to the texting system
      opt-out - Opt out of the texting system
      
    Examples:
      +txt John = Hey, are you coming to the party?
      +txt Jane Bob = Meet me at the park in 10 minutes
      +txt/pic Jane = A selfie of me at the beach
      +txt/opt-in
      +txt 5

    Characters must be opted in to the texting system to send or receive texts.
    Viewing a number shows your recent text history.
    """
    key = "+txt"
    aliases = ["+text", "+sms"]
    locks = "cmd:all()"
    help_category = "Comms"
    switch_options = ("pic", "opt-in", "opt-out")

    def func(self):
        """Implement the text command functionality"""
        caller = self.caller

        # Handle opt-in/opt-out
        if "opt-in" in self.switches:
            caller.db.text_enabled = True
            caller.msg("You have opted into the texting system. Your character can now send and receive texts.")
            return
            
        if "opt-out" in self.switches:
            caller.db.text_enabled = False
            caller.msg("You have opted out of the texting system. Your character can no longer send or receive texts.")
            return
            
        # Check if the caller is opted in
        if not caller.db.text_enabled:
            caller.msg("You have not opted into the texting system. Use '+txt/opt-in' to enable texting.")
            return
            
        # Get text messages we've sent
        texts_we_sent = Msg.objects.get_messages_by_sender(caller).filter(
            db_tags__db_key="text").order_by("-db_date_created")
            
        # Handle message history display
        if self.args and "=" not in self.args:
            if self.args.isdigit():
                # Show message history
                number = int(self.args)
                texts = texts_we_sent[:number]
                if texts:
                    try:
                        formatted_texts = []
                        for msg in texts:
                            try:
                                receivers = ", ".join(obj.key for obj in msg.receivers)
                            except AttributeError:
                                receivers = ", ".join(str(obj) for obj in msg.receivers)
                            formatted_texts.append(
                                "|w%s|n |c%s|n: %s" % (
                                    msg.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                                    receivers,
                                    msg.message
                                )
                            )
                        text_history = "\n".join(formatted_texts)
                        self.msg(f"Your last {len(texts)} texts:\n{text_history}\nEnd of text history.")
                    except Exception as e:
                        self.msg(f"Error displaying text history: {str(e)}")
                else:
                    self.msg("You haven't sent any texts yet.")
                return
                
        # Parse the message for new texts
        if "=" not in self.args:
            self.msg("Usage: +txt <character>[,<character2>,...]=<message>")
            return
            
        targets, message = self.args.split("=", 1)
        message = message.strip()
        
        # Split recipients by spaces
        recipient_list = [r.strip() for r in targets.split()]
        
        # Process the recipients
        character_recipients = []
        offline_recipients = []
        not_opted_in = []
        failed_recipients = []
        
        for recipient in recipient_list:
            # Search for the target character
            target = search_character(self.caller, recipient, quiet=True)
            
            if target:
                # Check if character has opted into texting
                if not target.db.text_enabled:
                    not_opted_in.append(target.name)
                    continue
                    
                # Check if character is online
                if not target.has_account or not target.sessions.count():
                    offline_recipients.append(target.name)
                    
                # Valid recipient
                character_recipients.append(target)
                continue
                
            # Couldn't find recipient
            failed_recipients.append(recipient)
            
        if not character_recipients:
            # No valid recipients found
            if failed_recipients:
                self.msg(f"Could not find: {', '.join(failed_recipients)}")
            if not_opted_in:
                self.msg(f"Not opted into texting: {', '.join(not_opted_in)}")
            if offline_recipients:
                self.msg(f"Currently offline: {', '.join(offline_recipients)}")
            return
            
        # Format recipient list for messages
        if len(character_recipients) == 1:
            recipient_names = character_recipients[0].name
        elif len(character_recipients) == 2:
            recipient_names = f"{character_recipients[0].name} and {character_recipients[1].name}"
        else:
            recipient_names = ", ".join(r.name for r in character_recipients[:-1])
            recipient_names += f", and {character_recipients[-1].name}"
            
        # Send messages based on switch
        is_picture = "pic" in self.switches
        is_group = len(character_recipients) > 1
        
        # Message to sender
        if is_picture:
            if is_group:
                sender_msg = f"In a text group chat, you send the following picture: {message}"
            else:
                sender_msg = f"You send the following picture to {recipient_names}: {message}"
        else:
            if is_group:
                sender_msg = f"In a text group chat, you text, \"{message}\" to {recipient_names}."
            else:
                sender_msg = f"You text, \"{message}\" to {recipient_names}."
                
        self.caller.msg(sender_msg)
        
        # Send to recipients
        for target in character_recipients:
            if is_picture:
                if is_group:
                    target_msg = f"In a group chat, you receive an image from {caller.name}: {message}"
                else:
                    target_msg = f"You receive a picture via text from {caller.name}: {message}"
            else:
                if is_group:
                    target_msg = f"In a text group chat, {caller.name} texts, \"{message}\""
                else:
                    target_msg = f"{caller.name} sends you a text that reads, \"{message}.\""
                    
            target.msg(target_msg)
            
        # Report any offline/not-opted-in users
        if offline_recipients:
            self.msg(f"Currently offline (message still sent): {', '.join(offline_recipients)}")
        if not_opted_in:
            self.msg(f"Not opted into texting: {', '.join(not_opted_in)}")
        if failed_recipients:
            self.msg(f"Could not find: {', '.join(failed_recipients)}")
            
        # Create persistent message object for history
        target_perms = " or ".join([f"id({target.id})" for target in character_recipients + [caller]])
        create.create_message(
            caller,
            message,
            receivers=character_recipients,
            locks=(
                f"read:{target_perms} or perm(Admin);"
                f"delete:id({caller.id}) or perm(Admin);"
                f"edit:id({caller.id}) or perm(Admin)"
            ),
            tags=[("text", "comms")],
        ) 