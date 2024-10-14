from evennia import default_cmds
import re

class PoseBreakMixin:
    """
    A mixin to add pose breaks before commands.
    """
    def send_pose_break(self, exclude=None):
        pose_break = f"\n|y{'=' * 30}> |w{self.caller.name}|n |y<{'=' * 30}|n"
        self.caller.location.msg_contents(pose_break, exclude=exclude)

    def msg_contents(self, message, exclude=None, from_obj=None, **kwargs):
        """
        Custom msg_contents that adds a pose break before the message.
        """
        # Add the pose break
        self.send_pose_break(exclude=exclude)

        # Call the original msg_contents (pose/emit/say)
        super().msg_contents(message, exclude=exclude, from_obj=from_obj, **kwargs)

class CmdPose(PoseBreakMixin, default_cmds.MuxCommand):
    """
    Pose an action to the room, with support for mixed content and language tags.
    Usage:
      :pose text
      ;pose text
      pose text

    Use "~text" for language-tagged speech.
    
    Example:
      :waves and says "~Hello!" in French, then "Hello" in English.
      ;grins and whispers, "~We meet again!"
      pose This is a regular pose with "~tagged speech" and "untagged speech".
    """

    key = "pose"
    aliases = [";", ":"]
    locks = "cmd:all()"
    arg_regex = None

    def parse(self):
        """
        Custom parsing to handle different pose prefixes.
        """
        super().parse()
        
        if self.cmdstring == ":":
            # Add a space after colon if not present
            self.args = " " + self.args.lstrip()
        elif self.cmdstring == ";":
            # Remove space after semicolon if present
            self.args = self.args.lstrip()

    def process_special_characters(self, message):
        """
        Process %r and %t in the message, replacing them with appropriate ANSI codes.
        """
        message = message.replace('%r', '|/').replace('%t', '|-')
        return message

    def func(self):
        "Perform the pose"
        if not self.args:
            self.caller.msg("Pose what?")
            return

        # Send pose break before processing the message
        self.send_pose_break()

        # Process special characters in the message
        processed_args = self.process_special_characters(self.args)

        # Determine the name to use
        poser_name = self.caller.attributes.get('gradient_name', default=self.caller.key)

        # Get the character's speaking language
        speaking_language = self.caller.get_speaking_language()

        def process_speech(match):
            content = match.group(1)
            if content.startswith('~'):
                content = content[1:]  # Remove the tilde
                msg_self, msg_understand, msg_not_understand, _ = self.caller.prepare_say(content, language_only=True)
                return f'"{msg_understand}"', f'"{msg_not_understand}"'
            else:
                return f'"{content}"', f'"{content}"'

        # Process the pose message
        pose_parts_understand = []
        pose_parts_not_understand = []
        last_end = 0
        for match in re.finditer(r'"(.*?)"', processed_args):
            pose_parts_understand.append(processed_args[last_end:match.start()])
            pose_parts_not_understand.append(processed_args[last_end:match.start()])
            
            understand, not_understand = process_speech(match)
            pose_parts_understand.append(understand)
            pose_parts_not_understand.append(not_understand)
            
            last_end = match.end()
        
        pose_parts_understand.append(processed_args[last_end:])
        pose_parts_not_understand.append(processed_args[last_end:])

        pose_understand = "".join(pose_parts_understand)
        pose_not_understand = "".join(pose_parts_not_understand)

        # Construct the final pose messages
        pose_self = f"{poser_name}{pose_understand}"
        pose_understand = f"{poser_name}{pose_understand}"
        pose_not_understand = f"{poser_name}{pose_not_understand}"

        # Announce the pose to the room
        for receiver in [char for char in self.caller.location.contents if char.has_account]:
            if receiver != self.caller:
                if speaking_language and speaking_language in receiver.get_languages():
                    receiver.msg(pose_understand)
                else:
                    receiver.msg(pose_not_understand)
            else:
                receiver.msg(pose_self)
