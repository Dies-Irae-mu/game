#commands/bbs/bbs_admin_commands.py

from evennia import default_cmds
from evennia import create_object
from typeclasses.bbs_controller import BBSController

class CmdResetBBS(default_cmds.MuxCommand):
    """
    Reinitialize the BBSController, wiping away all boards and posts.

    Usage:
      +bbs/reset

    This command will delete all existing boards and their posts,
    effectively resetting the BBS system. Use with caution.
    """
    key = "+bbs/reset"
    locks = "cmd:perm(Admin)"
    help_category = "Event & Bulletin Board"

    def func(self):
        # Confirm the user's intention
        confirmation = self.caller.ndb.confirmation if hasattr(self.caller, 'ndb') else None
        if not confirmation or confirmation != "yes":
            self.caller.msg("This will wipe all boards and posts. Type '+bbs/reset yes' to confirm.")
            self.caller.ndb.confirmation = "yes"
            return

        # Reset the confirmation
        self.caller.ndb.confirmation = None

        # Find or create the BBSController
        try:
            controller = BBSController.objects.get(db_key="BBSController")
        except BBSController.DoesNotExist:
            controller = create_object(BBSController, key="BBSController")
            self.caller.msg("BBSController created.")

        # Reset the boards and initialize next_board_id
        controller.db.boards = {}
        controller.db.next_board_id = 1  # Initialize next_board_id to 1
        self.caller.msg("BBSController has been reset. All boards and posts have been deleted.")