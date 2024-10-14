from evennia.commands.default.muxcommand import MuxCommand

class CmdSay(MuxCommand):
    """
    speak as your character

    Usage:
      say <message>
      say ~<message>     (to speak in your set language)
      "<message>
      '~<message>    (to speak in your set language)

    Talk to those in your current location.
    """

    key = "say"
    aliases = ['"', "'"]
    locks = "cmd:all()"
    help_category = "General"
    arg_regex = r""

    def func(self):
        """
        This is where the language handling happens.
        """
        caller = self.caller

        if not self.args:
            caller.msg("Say what?")
            return

        speech = self.args

        # Handle the case where the alias " or ' is used
        if self.cmdstring in ['"', "'"]:
            speech = speech
        else:
            # For the 'say' command, we need to preserve leading whitespace
            # to differentiate between 'say ~message' and 'say ~ message'
            speech = speech.rstrip()

        msg_self, msg_understand, msg_not_understand, language = caller.prepare_say(speech)

        # Send messages to receivers.  Filter out everything but connected players.
        receivers = [char for char in caller.location.contents if char.has_account]
        for receiver in receivers:
            if receiver != caller:
                if language and language in receiver.get_languages():
                    receiver.msg(msg_understand)
                else:
                    receiver.msg(msg_not_understand)
            else:
                receiver.msg(msg_self)

        # Call the at_say hook
        caller.at_say(speech)