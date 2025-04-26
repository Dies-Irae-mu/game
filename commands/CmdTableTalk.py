from evennia.commands.default.muxcommand import MuxCommand
from commands.CmdPose import PoseBreakMixin
import re

class CmdTableTalk(PoseBreakMixin, MuxCommand):
    """
    Talk to others at the same place.

    Usage:
      tt <message>       - Say something (like say command)
      tt :<message>      - Pose something (like pose command)
      tt \<message>      - Emit something (like @emit command)

    Only people at the same place as you can hear your table talk.
    You need to join a place first with the +place/join command.
    
    Language Features:
      - Use "~text" for speech in your set language
      - Example: tt Hello everyone! "~This part is in my set language."

    Examples:
      tt Hello everyone at this table.
      tt :nods and says, "~Hello my friends." Then switches to English, "How are you?"
      tt \A quiet conversation is happening here.
    
    Places:
      Use +place/create <name> to create a place
      Use +place/join <name> to join a place
      Use +place/list to see all places in the room
      Use +place/leave to leave your current place
    """

    key = "tt"
    aliases = ["tabletalk"]
    locks = "cmd:all()"
    help_category = "RP Commands"
    arg_regex = r"\s|$"

    def func(self):
        """Execute the command."""
        caller = self.caller
        args = self.args.strip()

        # Check if the caller is at a place
        if not caller.db.place:
            caller.msg("You must be at a place to use table talk. Use +place/join <name> to join a place.")
            return

        place_name = caller.db.place

        if not args:
            caller.msg("What do you want to say at this place?")
            return

        # Get everyone at the same place
        receivers = []
        for obj in caller.location.contents:
            if hasattr(obj, 'has_account') and obj.has_account and obj.db.place == place_name:
                receivers.append(obj)

        if not receivers:
            caller.msg("There's no one at this place to talk to.")
            return

        # Check the first character to determine the command type
        if args.startswith(':'):
            # Pose mode
            self._do_pose(caller, args[1:], place_name, receivers)
        elif args.startswith('\\'):
            # Emit mode 
            self._do_emit(caller, args[1:], place_name, receivers)
        else:
            # Say mode
            self._do_say(caller, args, place_name, receivers)

    def _do_say(self, caller, message, place_name, receivers):
        """Handle say-style messages."""
        if not message:
            caller.msg("What do you want to say?")
            return

        # Send pose break before the message
        self.send_pose_break(exclude=[r for r in receivers if r != caller])

        # Check if message starts with ~ for language-tagged speech
        is_language_tagged = message.startswith('~')
        if is_language_tagged:
            message = message[1:]  # Remove the ~ prefix

        # Get the initial message parameters to determine the language
        initial_msg_self, initial_msg_understand, initial_msg_not_understand, language = caller.prepare_say(message)

        # Format with place name and send to receivers
        for receiver in receivers:
            if receiver != caller:
                # Check for Universal Language merit
                has_universal = any(
                    merit.lower().replace(' ', '') == 'universallanguage'
                    for category in receiver.db.stats.get('merits', {}).values()
                    for merit in category.keys()
                )

                # Get the languages the receiver knows
                receiver_languages = receiver.get_languages()

                # If they have Universal Language, know the language, or it's not a language-tagged message
                if has_universal or not language or (language and language in receiver_languages):
                    # Receiver understands the language
                    _, msg_understand, _, _ = caller.prepare_say(message, viewer=receiver, skip_english=True)
                    receiver.msg(f"At {place_name}, {msg_understand}")
                else:
                    # Receiver doesn't understand - use the not_understand format which hides the actual text
                    if language:
                        # Format as "says something in [language]" when they don't understand
                        receiver.msg(f"At {place_name}, {caller.name} says something in {language}")
                    else:
                        # Fallback for unknown language cases
                        receiver.msg(f"At {place_name}, {caller.name} says something you don't understand")
            else:
                # The speaker always understands their own speech
                msg_self, _, _, _ = caller.prepare_say(message, viewer=receiver, skip_english=True)
                receiver.msg(f"At {place_name}, {msg_self}")

        # Record scene activity
        caller.record_scene_activity()

    def _do_pose(self, caller, message, place_name, receivers):
        """Handle pose-style messages."""
        if not message:
            caller.msg("What do you want to pose?")
            return

        # Send pose break
        self.send_pose_break(exclude=[r for r in receivers if r != caller])

        # Get the character's name to use
        poser_name = caller.attributes.get('gradient_name', default=caller.key)

        # Get the character's speaking language
        speaking_language = caller.get_speaking_language()
        
        # Check for language-tagged speech in the pose
        if "~" in message:
            # For each receiver, process language separately
            for receiver in receivers:
                parts = []
                current_pos = 0
                
                # Find language-tagged portions
                for match in re.finditer(r'"~([^"]+)"', message):
                    # Add text before the speech
                    parts.append(message[current_pos:match.start()])
                    
                    # Get the speech content
                    speech = match.group(1)
                    
                    # Check if the receiver understands the language
                    has_universal = any(
                        merit.lower().replace(' ', '') == 'universallanguage'
                        for category in receiver.db.stats.get('merits', {}).values()
                        for merit in category.keys()
                    )
                    
                    knows_language = (speaking_language in receiver.get_languages()) if speaking_language else True
                    
                    if receiver == caller or has_universal or knows_language:
                        # Receiver understands the language
                        parts.append(f'"{speech}"')
                    else:
                        # Receiver doesn't understand - replace with unknown language indicator
                        parts.append(f'"[foreign speech in {speaking_language}]"')
                    
                    current_pos = match.end()
                
                # Add any remaining text
                parts.append(message[current_pos:])
                
                # Construct final message with place name
                final_message = f"At {place_name}, {poser_name} {''.join(parts)}"
                receiver.msg(final_message)
        else:
            # No language-tagged speech, send normal pose with place name to all receivers
            for receiver in receivers:
                receiver.msg(f"At {place_name}, {poser_name} {message}")

        # Record scene activity
        caller.record_scene_activity()

    def _do_emit(self, caller, message, place_name, receivers):
        """Handle emit-style messages."""
        if not message:
            caller.msg("What do you want to emit?")
            return

        # Send pose break
        self.send_pose_break(exclude=[r for r in receivers if r != caller])

        # Get speaking language
        speaking_language = caller.get_speaking_language()
        
        # Check for language-tagged text
        if "~" in message:
            # For each receiver, process language separately
            for receiver in receivers:
                parts = []
                current_pos = 0
                
                # Find language-tagged portions
                for match in re.finditer(r'"~([^"]+)"', message):
                    # Add text before the speech
                    parts.append(message[current_pos:match.start()])
                    
                    # Get the speech content
                    speech = match.group(1)
                    
                    # Check if the receiver understands the language
                    has_universal = any(
                        merit.lower().replace(' ', '') == 'universallanguage'
                        for category in receiver.db.stats.get('merits', {}).values()
                        for merit in category.keys()
                    )
                    
                    knows_language = (speaking_language in receiver.get_languages()) if speaking_language else True
                    
                    if receiver == caller or has_universal or knows_language:
                        # Receiver understands the language
                        parts.append(f'"{speech}"')
                    else:
                        # Receiver doesn't understand - replace with unknown language indicator
                        parts.append(f'"[foreign speech in {speaking_language}]"')
                    
                    current_pos = match.end()
                
                # Add any remaining text
                parts.append(message[current_pos:])
                
                # Construct final message with place name
                final_message = f"At {place_name}, {''.join(parts)}"
                receiver.msg(final_message)
        else:
            # No language-tagged content, send as is with place prefix to all receivers
            for receiver in receivers:
                receiver.msg(f"At {place_name}, {message}")

        # Record scene activity
        caller.record_scene_activity()

    def send_pose_break(self, exclude=None):
        """
        Override the send_pose_break method to only send to people at the same place.
        """
        caller = self.caller
        place_name = caller.db.place
        
        if not place_name:
            return

        # Check if the room is an OOC Area
        if hasattr(caller.location, 'db') and caller.location.db.roomtype == 'OOC Area':
            return  # Don't send pose breaks in OOC Areas
            
        pose_break = f"\n|y{'=' * 30}> |w{caller.name}|n |y<{'=' * 30}|n"
        
        # Filter receivers to only include those at the same place
        for obj in caller.location.contents:
            if (hasattr(obj, 'has_account') and obj.has_account and 
                obj.db.place == place_name and
                obj != caller and
                (not exclude or obj not in exclude)):
                obj.msg(pose_break)
        
        # Always send the pose break to the caller
        caller.msg(pose_break) 