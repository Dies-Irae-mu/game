from evennia import CmdSet


from commands.bbs.bbs_admin_commands import CmdResetBBS

from commands.bbs.bbs_all_commands import (
    CmdBBS
)

from commands.bbs.bbs_builder_commands import (
    CmdCreateBoard,CmdDeleteBoard, CmdRevokeAccess, CmdListAccess, 
    CmdLockBoard, CmdPinPost, CmdUnpinPost, CmdEditBoard, CmdGrantAccess
)



class BBSCmdSet(CmdSet):
    """
    This cmdset includes all BBS-related commands.
    """
    key = "BBS"
    priority = 1

    def at_cmdset_creation(self):
        # Add BBS commands
        self.add(CmdCreateBoard())
        self.add(CmdBBS())
        self.add(CmdDeleteBoard())
        self.add(CmdRevokeAccess())
        self.add(CmdListAccess())
        self.add(CmdLockBoard())
        self.add(CmdPinPost())
        self.add(CmdUnpinPost())
        self.add(CmdEditBoard())
        self.add(CmdResetBBS())
        self.add(CmdGrantAccess())