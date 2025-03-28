from evennia.commands.default.account import MuxAccountLookCommand
from django.conf import settings

class CmdUnpuppet(MuxAccountLookCommand):
    """
    stop puppeting and go ooc

    Usage:
      ooc

    Go out-of-character (OOC).

    This will leave your current character and put you in a incorporeal OOC state.
    """

    key = "unpuppet"
    locks = "cmd:pperm(Player)"
    help_category = "Utility Commands"

    # this is used by the parent
    account_caller = True

    def func(self):
        """Implement function"""

        account = self.account
        session = self.session

        old_char = account.get_puppet(session)
        if not old_char:
            string = "You are already OOC."
            self.msg(string)
            return

        account.db._last_puppet = old_char

        # disconnect
        try:
            account.unpuppet_object(session)
            self.msg("\n|GYou go OOC.|n\n")

            if settings.AUTO_PUPPET_ON_LOGIN and settings.MAX_NR_CHARACTERS == 1 and self.playable:
                # only one character exists and is allowed - simplify
                self.msg("You are out-of-character (OOC).\nUse |wic|n to get back into the game.")
                return

            self.msg(account.at_look(target=self.playable, session=session))

        except RuntimeError as exc:
            self.msg(f"|rCould not unpuppet from |c{old_char}|n: {exc}")