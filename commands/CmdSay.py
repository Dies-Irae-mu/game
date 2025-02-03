from evennia.commands.default.muxcommand import MuxCommand
from commands.CmdPose import PoseBreakMixin

class CmdSay(PoseBreakMixin, MuxCommand):
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
    help_category = "RP Commands"
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

        # Send pose break before the message
        self.send_pose_break()

        # Prepare the say messages
        msg_self, msg_understand, msg_not_understand, language = caller.prepare_say(speech)

        # Filter receivers based on reality layers
        filtered_receivers = []
        for obj in caller.location.contents:
            if not obj.has_account:
                continue
            
            # Check if they share the same reality layer
            if (caller.tags.get("in_umbra", category="state") and obj.tags.get("in_umbra", category="state")) or \
               (caller.tags.get("in_material", category="state") and obj.tags.get("in_material", category="state")) or \
               (caller.tags.get("in_dreaming", category="state") and obj.tags.get("in_dreaming", category="state")):
                filtered_receivers.append(obj)

        # Send messages to receivers
        for receiver in filtered_receivers:
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
                    _, msg_understand, _, _ = caller.prepare_say(speech, viewer=receiver, skip_english=True)
                    receiver.msg(msg_understand)
                else:
                    _, _, msg_not_understand, _ = caller.prepare_say(speech, viewer=receiver, skip_english=True)
                    receiver.msg(msg_not_understand)
            else:
                # The speaker always understands their own speech
                msg_self, _, _, _ = caller.prepare_say(speech, viewer=receiver, skip_english=True)
                receiver.msg(msg_self)

        # Add this at the end of the func method
        try:
            self.caller.record_scene_activity()
        except KeyError:
            # Initialize scene data if it doesn't exist
            if not self.caller.db.scene_data:
                self.caller.db.scene_data = {}
            self.caller.db.scene_data['last_weekly_reset'] = None
            self.caller.record_scene_activity()

