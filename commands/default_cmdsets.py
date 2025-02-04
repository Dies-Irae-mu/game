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
from commands.CmdSetStats import CmdStats
from commands.CmdSheet import CmdSheet
from commands.CmdInfo import CmdInfo
from commands.CmdHurt import CmdHurt
from commands.CmdHeal import CmdHeal
from commands.CmdLanguage import CmdLanguage
import evennia.contrib.game_systems.mail as mail
from commands.CmdRoll import CmdRoll
from commands.CmdSay import CmdSay
from commands.CmdEmit import CmdEmit
from commands.CmdNotes import CmdNotes
from commands.building import (
    CmdSetRoomResources, CmdSetRoomType, CmdSetUmbraDesc, 
    CmdSetGauntlet, CmdUmbraInfo, CmdSetHousing, CmdManageBuilding, 
    CmdSetLock
)
from commands.CmdInit import CmdInit

from commands.CmdUmbraInteraction import CmdUmbraInteraction
from commands.communication import CmdMeet, CmdPlusIc, CmdPlusOoc, CmdOOC, CmdSummon, CmdJoin
from commands.admin import CmdApprove, CmdUnapprove, CmdAdminLook, CmdTestLock, CmdPuppetFreeze
from commands.CmdPump import CmdPump
from commands.CmdSpendGain import CmdSpendGain
from commands.where import CmdWhere
from commands.chargen import CmdSubmit
from commands.CmdSelfStat import CmdSelfStat
from commands.CmdShift import CmdShift
from commands.CmdStaff import CmdStaff, CmdPST
from commands.unfindable import CmdUnfindable
from commands.CmdChangelingInteraction import CmdChangelingInteraction
from commands.CmdBanality import CmdBanality

from commands.bbs.bbs_all_commands import CmdBBS
from commands.bbs.bbs_admin_commands import CmdResetBBS
from commands.oss.oss_cmdset import OssCmdSet

from commands.CmdWeather import CmdWeather
from commands.CmdFaeDesc import CmdFaeDesc
from commands.CmdEvents import CmdEvents
from commands.jobs.jobs_cmdset import JobSystemCmdSet
from commands.CmdUnpuppet import CmdUnpuppet
from commands.CmdPage import CmdPage
from commands.CmdFinger import CmdFinger
from commands.CmdAlias import CmdAlias
from commands.CmdLFRP import CmdLFRP
from evennia.commands.default import cmdset_character, cmdset_account
from commands.CmdXP import CmdXP
from commands.CmdXPCost import CmdXPCost
from commands.CmdWho import CmdWho
from commands.housing import CmdRent, CmdVacate, CmdSetApartmentDesc, CmdSetApartmentExit, CmdManageHome, CmdUpdateApartments, CmdListApartments, CmdUpdateExits
from commands.comms import CustomCmdChannel
from commands.CmdCheck import CmdCheck
from commands.CmdPlots import CmdPlots
from commands.CmdHangouts import CmdHangout, CmdSetHangout
from commands.CmdNPC import CmdNPC


class CharacterCmdSet(cmdset_character.CharacterCmdSet):
    """
    The `CharacterCmdSet` contains general in-game commands like `look`,
    `get`, etc available on in-game Character objects. It is merged with
    the `AccountCmdSet` when an Account puppets a Character.
    """

    key = "DefaultCharacter"
    priority = 1
    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #
        self.add(CustomCmdChannel())
        
        self.add(CmdGradientName())
        self.add(CmdBBS())
        self.add(OssCmdSet)
        self.add(CmdFaeDesc())
        self.add(CmdStats())
        self.add(CmdPST())
        
        self.add(CmdSheet())
        self.add(CmdInfo())
        self.add(CmdHurt())
        self.add(CmdHeal())
        self.add(CmdEvents())
        self.add(mail.CmdMail())
        self.add(mail.CmdMailCharacter())
        self.add(CmdRoll())
        self.add(CmdShift())
        self.add(CmdWeather())
        self.add(CmdChangelingInteraction())
        self.add(CmdAdminLook())
        self.add(CmdInfo())
        self.add(CmdSubmit())
        self.add(CmdAlias())
        self.add(CmdLFRP())
        self.add(CmdStaff())
        self.add(CmdUnfindable())
        self.add(JobSystemCmdSet)
        self.add(CmdBanality())
        self.add(CmdUmbraInteraction())
        self.add(CmdMeet())
        self.add(CmdPlusIc())
        self.add(CmdPlusOoc())
        self.add(CmdOOC())
        self.add(CmdPump())
        self.add(CmdSpendGain())
        self.add(CmdWhere())
        self.add(CmdShortDesc())
        self.add(CmdPose())
        self.add(CmdEmit())
        self.add(CmdSay())
        self.add(CmdLanguage())
        self.add(CmdPage())
        self.add(CmdFinger())
        self.add(CmdSelfStat())
        self.add(CmdXP())
        self.add(CmdXPCost())
        self.add(CmdWho())
        self.add(CmdRent())
        self.add(CmdVacate())
        self.add(CmdSetApartmentDesc())
        self.add(CmdSetApartmentExit())
        self.add(CmdManageHome())
        self.add(CmdSetLock())
        self.add(CmdPuppetFreeze())
        self.add(CmdCheck())
        self.add(CmdPlots())
        self.add(CmdInit())
        self.add(CmdHangout())
        self.add(CmdSetHangout())

class AccountCmdSet(cmdset_account.AccountCmdSet):
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
        
        # Add our custom channel command
        self.add(CustomCmdChannel())
        
        self.add(CmdSetRoomResources())
        self.add(CmdSetRoomType())
        self.add(CmdSetUmbraDesc())
        self.add(CmdSetGauntlet())
        self.add(CmdUmbraInfo())
        self.add(CmdNotes())
        self.add(CmdSummon())
        self.add(CmdJoin())
        self.add(CmdApprove())
        self.add(CmdUnapprove())
        self.add(CmdUnpuppet())
        self.add(CmdSetHousing())
        self.add(CmdManageBuilding())
        self.add(CmdUpdateApartments())
        self.add(CmdListApartments())
        self.add(CmdUpdateExits())
        self.add(CmdTestLock())
        self.add(CmdResetBBS())
        self.add(CmdNPC())
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
