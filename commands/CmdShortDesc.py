from evennia.commands.default.muxcommand import MuxCommand
class CmdShortDesc(MuxCommand):
    """
    shortdesc <text>

    Usage:
      shortdesc <text>
      shortdesc <character>=<text>

    Create or set a short description for your character. Builders+ can set the short description for others.

    Examples:
      shortdesc Tall and muscular
      shortdesc Bob=Short and stocky
    """
    key = "shortdesc"
    help_category = "General"

    def parse(self):
        """
        Custom parser to handle the possibility of targeting another character.
        """
        args = self.args.strip()
        if "=" in args:
            self.target_name, self.shortdesc = [part.strip() for part in args.split("=", 1)].strip()
        else:
            self.target_name = None
            self.shortdesc = args.strip()

    def func(self):
        "Implement the command"
        caller = self.caller

        if self.target_name:
            # Check if the caller has permission to set short descriptions for others
            if not caller.check_permstring("builders"):
                caller.msg("|rYou don't have permission to set short descriptions for others.|n")
                return

            # Find the target character
            target = caller.search(self.target_name)
            if not target:
                caller.msg(f"|rCharacter '{self.target_name}' not found.|n")
                return

            # Set the short description for the target
            target.db.shortdesc = self.shortdesc
            caller.msg(f"Short description for {target.name} set to '|w{self.shortdesc}|n'.")
            target.msg(f"Your short description has been set to '|w{self.shortdesc}|n' by {caller.name}.")
        else:
            # Set the short description for the caller
            if not self.shortdesc:
                # remove the shortdesc
                caller.db.shortdesc = ""
                caller.msg("Short description removed.")
                return

            caller.db.shortdesc = self.shortdesc
            caller.msg("Short description set to '|w%s|n'." % self.shortdesc)
