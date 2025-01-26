from evennia.commands.default.muxcommand import MuxCommand

class CmdShortDesc(MuxCommand):
    """
    shortdesc <text>

    Usage:
      shortdesc <text>
      shortdesc <character>=<text>
      shortdesc me=<text>

    Create or set a short description for your character. Builders+ can set the short description for others.

    Examples:
      shortdesc Tall and muscular
      shortdesc me=Tall and muscular
      shortdesc Bob=Short and stocky
    """
    key = "shortdesc"
    help_category = "Chargen & Character Info"

    def parse(self):
        """
        Custom parser to handle the possibility of targeting another character.
        """
        args = self.args.strip()
        if "=" in args:
            parts = args.split("=", 1)
            self.target_name = parts[0].strip()
            self.shortdesc = parts[1].strip()
        else:
            self.target_name = None
            self.shortdesc = args

    def func(self):
        "Implement the command"
        caller = self.caller

        if self.target_name:
            # Handle 'me' as a special case
            if self.target_name.lower() == "me":
                target = caller
            else:
                # Check if the caller has permission to set short descriptions for others
                if not caller.check_permstring("builders"):
                    caller.msg("|rYou don't have permission to set short descriptions for others.|n")
                    return

                # Find the target character
                target = caller.search(self.target_name)
                if not target:
                    return

            # Set the short description for the target
            target.db.shortdesc = self.shortdesc
            if target == caller:
                caller.msg(f"Your short description set to '|w{self.shortdesc}|n'.")
            else:
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
