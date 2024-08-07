from evennia import Command as BaseCommand
from evennia import default_cmds

class CmdEmote(default_cmds.MuxCommand):
    """
    Emote something
    Usage:
      emote <message>
    """

    key = "emote"
    aliases = ["em", "@emit"]
    locks = "cmd:all()"
    arg_regex = r"\s|$"

    def func(self):
        "Perform the emote"

        if not self.args:
            self.caller.msg("Emote what?")
            return

        # Determine the name to use
        emoter_name = self.caller.attributes.get('gradient_name', default=self.caller.key)

        # Construct the emote message
        emote_message = f"{emoter_name} {self.args}"

        # Announce the emote to the room
        self.caller.location.msg_contents(emote_message, exclude=self.caller)
        self.caller.msg(f"{emote_message}")

# Add the command to your Command set
class CharacterCmdSet(default_cmds.CharacterCmdSet):
    def at_cmdset_creation(self):
        "Populate the cmdset"
        self.add(CmdEmote())
