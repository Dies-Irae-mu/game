from evennia.commands.command import Command

class CmdLanguage(Command):
    """
    Set your speaking language or view known languages.

    Usage:
      +language
      +language <language>
      +language none

    Examples:
      +language
      +language Spanish
      +language none
    """

    key = "+language"
    aliases = ["+lang"]
    locks = "cmd:all()"

    def func(self):
        if not self.args:
            languages = self.caller.get_languages()
            current = self.caller.get_speaking_language()
            self.caller.msg(f"|cLANGUAGE>|n Known languages: |w{', '.join(languages)}|n")
            self.caller.msg(f"|cLANGUAGE>|n Currently speaking: |w{current if current else 'None'}|n")
        elif self.args.lower() == "none":
            self.caller.set_speaking_language(None)
            self.caller.msg("|cLANGUAGE>|n You are no longer speaking in any specific language.")
        else:
            try:
                self.caller.set_speaking_language(self.args.lower().capitalize())
                self.caller.msg(f"|cLANGUAGE>|n Now speaking in |w{self.args.lower().capitalize()}|n.")
            except ValueError as e:
                self.caller.msg(str(e))
