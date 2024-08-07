from evennia import Command as BaseCommand
from evennia import default_cmds

class CmdPose(default_cmds.MuxCommand):
    """
    Pose an action to the room.
    Usage:
      pose <message>
    Example:
      pose looks around suspiciously.
    """

    key = "pose"
    aliases = [";", ":"]
    locks = "cmd:all()"
    arg_regex = ""

    arg_regex = None
    def func(self):
        "Perform the pose"

        if not self.args:
            self.caller.msg("Pose what?")
            return

        # Determine the name to use
        poser_name = self.caller.attributes.get('gradient_name', default=self.caller.key)

        # Construct the pose message
        pose_message = f"{poser_name} {self.args}"

        # Announce the pose to the room
        self.caller.location.msg_contents(pose_message, exclude=self.caller)
        self.caller.msg(f"{pose_message}")

# Add the command to your Command set
class CharacterCmdSet(default_cmds.CharacterCmdSet):
    def at_cmdset_creation(self):
        "Populate the cmdset"
        self.add(CmdPose())

