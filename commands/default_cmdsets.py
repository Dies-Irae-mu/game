"""
Command sets

All commands in the game must be grouped in a cmdset.  A given command
can be part of any number of cmdsets and cmdsets can be added/removed
and merged onto entities at runtime.

To create new commands to populate the cmdset, see
`commands/command.py`.

This module wraps the default command sets of Evennia; overloads them
to add/remove commands from the default lineup. You can create your
own cmdsets by inheriting from them or directly from `evennia.CmdSet`.

"""

from evennia import default_cmds
from commands.CmdGradient import CmdGradientName
from commands.CmdShortDesc import CmdShortDesc
from commands.CmdPose import CmdPose
from commands.CmdSetStats import CmdStats, CmdSpecialty
from commands.CmdSheet import CmdSheet
from commands.CmdHurt import CmdHurt
from commands.CmdHeal import CmdHeal
from commands.CmdLanguage import CmdLanguage
import evennia.contrib.game_systems.mail as mail
from  commands.CmdRoll import CmdRoll
from commands.CmdSay import CmdSay
from commands.CmdEmit import CmdEmit
from commands.CmdNotes import CmdNotes
from commands.bbs.bbs_cmdset import BBSCmdSet
from commands.building import CmdSetRoomResources, CmdSetRoomType, CmdSetUmbraDesc, CmdSetGauntlet, CmdUmbraInfo
from commands.requests import CmdRequests
from commands.CmdUmbraInteraction import CmdUmbraInteraction
from commands.communication import CmdMeet, CmdPlusIc, CmdPlusOoc, CmdOOC, CmdSummon, CmdJoin
from commands.admin import CmdApprove, CmdUnapprove
from commands.CmdPump import CmdPump
from commands.CmdSpendGain import CmdSpendGain
from commands.where import CmdWhere
from commands.chargen import CmdCharGen
from commands.CmdSelfStat import CmdSelfStat
from commands.CmdShift import CmdShift

from commands.bbs.bbs_cmdset import BBSCmdSet
from commands.oss.oss_cmdset import OssCmdSet

class CharacterCmdSet(default_cmds.CharacterCmdSet):
    """
    The `CharacterCmdSet` contains general in-game commands like `look`,
    `get`, etc available on in-game Character objects. It is merged with
    the `AccountCmdSet` when an Account puppets a Character.
    """

    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #
        self.add(CmdGradientName())
        self.add(CmdShortDesc())
        self.add(CmdPose())
        self.add(CmdStats())
        self.add(CmdEmit())
        self.add(BBSCmdSet)
        self.add(OssCmdSet)

        self.add(CmdSpecialty())
        self.add(CmdSheet())
        self.add(CmdHurt())
        self.add(CmdHeal())
        self.add(mail.CmdMail())
        self.add(mail.CmdMailCharacter())
        self.add(CmdRoll())
        self.add(CmdShift())

        self.add(CmdUmbraInteraction())
        self.add(CmdMeet())
        self.add(CmdPlusIc())
        self.add(CmdPlusOoc())
        self.add(CmdOOC())
        self.add(CmdPump())
        self.add(CmdSpendGain())
        self.add(CmdWhere())
        self.add(CmdCharGen())
        self.add(CmdSelfStat())
class AccountCmdSet(default_cmds.AccountCmdSet):
    """
    This is the cmdset available to the Account at all times. It is
    combined with the `CharacterCmdSet` when the Account puppets a
    Character. It holds game-account-specific commands, channel
    commands, etc.
    """

    key = "DefaultAccount"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #
        self.add(CmdSetRoomResources())
        self.add(CmdSetRoomType())
        self.add(CmdSetUmbraDesc())
        self.add(CmdSetGauntlet())
        self.add(CmdUmbraInfo())
        self.add(CmdLanguage())
        self.add(CmdSay())
        self.add(CmdNotes())
        self.add(CmdRequests())
        self.add(CmdSummon())
        self.add(CmdJoin())
        self.add(CmdApprove())
        self.add(CmdUnapprove())

class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    """
    Command set available to the Session before being logged in.  This
    holds commands like creating a new account, logging in, etc.
    """

    key = "DefaultUnloggedin"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #


class SessionCmdSet(default_cmds.SessionCmdSet):
    """
    This cmdset is made available on Session level once logged in. It
    is empty by default.
    """

    key = "DefaultSession"

    def at_cmdset_creation(self):
        """
        This is the only method defined in a cmdset, called during
        its creation. It should populate the set with command instances.

        As and example we just add the empty base `Command` object.
        It prints some info.
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #
class CmdTab(default_cmds.MuxCommand):
    key = "|-"
    aliases = ["^t"]
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        caller = self.caller
        # Insert the command logic that |- would perform
        caller.msg("Executing the |- command logic.")

# In your default cmdset
from evennia import CmdSet

class DefaultCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdCustom())

# Add or update the command alias mapping in the settings file
from evennia import Command

class CmdRet(default_cmds.MuxCommand):
    key = "|/"
    aliases = ["^r"]
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        caller = self.caller
        message = self.args.strip()
        if not message:
            caller.msg("Say what?")
            return
        caller.msg(f'You say, "{message}"')
        caller.location.msg_contents(f'{caller.name} says, "{message}"', exclude=caller)

# In your default cmdset
from evennia import CmdSet

class DefaultCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdSay())
