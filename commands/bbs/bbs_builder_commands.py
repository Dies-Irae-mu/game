#commands/bbs/bbs_builder_commands.py


from evennia import default_cmds
from evennia import create_object
from typeclasses.bbs_controller import BBSController

class CmdCreateBoard(default_cmds.MuxCommand):
    """
    Create a new board.

    Usage:
      +bbs/create <name> = <description> / public | private
    """
    key = "+bbs/create"
    locks = "cmd:perm(Builder)"
    help_category = "BBS"

    def func(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/create <name> = <description> / public | private")
            return
        name_desc, privacy = self.args.rsplit("/", 1)
        name, description = [arg.strip() for arg in name_desc.split("=", 1)]
        public = privacy.strip().lower() == "public"

        # Ensure BBSController exists
        try:
            controller = BBSController.objects.get(db_key="BBSController")
        except BBSController.DoesNotExist:
            controller = create_object(BBSController, key="BBSController")
            controller.db.boards = {}  # Initialize with an empty boards dictionary if needed
            self.caller.msg("BBSController created.")

        # Create the board
        controller.create_board(name, description, public)
        self.caller.msg(f"Board '{name}' created as {'public' if public else 'private'} with description: {description}")

class CmdDeleteBoard(default_cmds.MuxCommand):
    """
    Delete a board and all its posts.

    Usage:
      +bbs/deleteboard <board_name>
    """
    key = "+bbs/deleteboard"
    locks = "cmd:perm(Builder)"
    help_category = "BBS"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: +bbs/deleteboard <board_name>")
            return
        board_name = self.args.strip()

        controller = BBSController.objects.get(db_key="BBSController")
        if not controller:
            self.caller.msg("BBSController not found.")
            return

        board = controller.get_board(board_name)
        if not board:
            self.caller.msg(f"No board found with the name '{board_name}'.")
            return

        controller.delete_board(board_name)
        self.caller.msg(f"Board '{board_name}' and all its posts have been deleted.")

class CmdRevokeAccess(default_cmds.MuxCommand):
    """
    Revoke access to a private board.

    Usage:
      +bbs/revokeaccess <board_name> = <character_name>
    """
    key = "+bbs/revokeaccess"
    locks = "cmd:perm(Builder)"
    help_category = "BBS"

    def func(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/revokeaccess <board_name> = <character_name>")
            return
        board_name, character_name = [arg.strip() for arg in self.args.split("=", 1)]

        controller = BBSController.objects.get(db_key="BBSController")
        if not controller:
            self.caller.msg("BBSController not found.")
            return

        board = controller.get_board(board_name)
        if not board:
            self.caller.msg(f"No board found with the name '{board_name}'.")
            return
        if board['public']:
            self.caller.msg(f"Board '{board_name}' is public; access control is not required.")
            return
        if character_name not in board['access_list']:
            self.caller.msg(f"{character_name} does not have access to board '{board_name}'.")
            return
        controller.revoke_access(board_name, character_name)
        self.caller.msg(f"Access for {character_name} has been revoked from board '{board_name}'.")

class CmdListAccess(default_cmds.MuxCommand):
    """
    List all users who have access to a private board.

    Usage:
      +bbs/listaccess <board_name>
    """
    key = "+bbs/listaccess"
    locks = "cmd:perm(Builder)"
    help_category = "BBS"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: +bbs/listaccess <board_name>")
            return
        board_name = self.args.strip()

        controller = BBSController.objects.get(db_key="BBSController")
        if not controller:
            self.caller.msg("BBSController not found.")
            return

        board = controller.get_board(board_name)
        if not board:
            self.caller.msg(f"No board found with the name '{board_name}'.")
            return
        if board['public']:
            self.caller.msg(f"Board '{board_name}' is public; access list is not applicable.")
            return
        access_list = board.get('access_list', [])
        if not access_list:
            self.caller.msg(f"No users have access to the private board '{board_name}'.")
        else:
            self.caller.msg(f"Users with access to '{board_name}': {', '.join(access_list)}")

class CmdLockBoard(default_cmds.MuxCommand):
    """
    Lock a board to prevent new posts.

    Usage:
      +bbs/lockboard <board_name>
    """
    key = "+bbs/lockboard"
    locks = "cmd:perm(Builder)"
    help_category = "BBS"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: +bbs/lockboard <board_name>")
            return
        board_name = self.args.strip()

        controller = BBSController.objects.get(db_key="BBSController")
        if not controller:
            self.caller.msg("BBSController not found.")
            return

        board = controller.get_board(board_name)
        if not board:
            self.caller.msg(f"No board found with the name '{board_name}'.")
            return

        if board.get('locked', False):
            self.caller.msg(f"Board '{board_name}' is already locked.")
            return

        controller.lock_board(board_name)
        self.caller.msg(f"Board '{board_name}' has been locked. No new posts can be made.")

class CmdPinPost(default_cmds.MuxCommand):
    """
    Pin a post to the top of a board.

    Usage:
      +bbs/pinpost <board_name_or_number>/<post_number>
    """
    key = "+bbs/pinpost"
    locks = "cmd:perm(Builder)"
    help_category = "BBS"

    def func(self):
        if not self.args or "/" not in self.args:
            self.caller.msg("Usage: +bbs/pinpost <board_name_or_number>/<post_number>")
            return
        board_ref, post_number = [arg.strip() for arg in self.args.split("/", 1)]

        controller = BBSController.objects.get(db_key="BBSController")
        if not controller:
            self.caller.msg("BBSController not found.")
            return

        # Determine if board_ref is a name or a number
        try:
            board_ref = int(board_ref)
        except ValueError:
            pass

        board = controller.get_board(board_ref)
        if not board:
            self.caller.msg(f"No board found with the name or number '{board_ref}'.")
            return

        try:
            post_number = int(post_number)
        except ValueError:
            self.caller.msg("Post number must be an integer.")
            return
        posts = board['posts']
        if post_number < 1 or post_number > len(posts):
            self.caller.msg(f"Invalid post number. Board '{board['name']}' has {len(posts)} posts.")
            return

        controller.pin_post(board['id'], post_number - 1)
        self.caller.msg(f"Post {post_number} in board '{board['name']}' has been pinned to the top.")


class CmdUnpinPost(default_cmds.MuxCommand):
    """
    Unpin a pinned post from the top of a board.

    Usage:
      +bbs/unpinpost <board_name_or_number>/<post_number>
    """
    key = "+bbs/unpinpost"
    locks = "cmd:perm(Builder)"
    help_category = "BBS"

    def func(self):
        if not self.args or "/" not in self.args:
            self.caller.msg("Usage: +bbs/unpinpost <board_name_or_number>/<post_number>")
            return
        board_ref, post_number = [arg.strip() for arg in self.args.split("/", 1)]

        controller = BBSController.objects.get(db_key="BBSController")
        if not controller:
            self.caller.msg("BBSController not found.")
            return

        # Determine if board_ref is a name or a number
        try:
            board_ref = int(board_ref)
        except ValueError:
            pass

        board = controller.get_board(board_ref)
        if not board:
            self.caller.msg(f"No board found with the name or number '{board_ref}'.")
            return

        try:
            post_number = int(post_number)
        except ValueError:
            self.caller.msg("Post number must be an integer.")
            return
        posts = board['posts']
        if post_number < 1 or post_number > len(posts):
            self.caller.msg(f"Invalid post number. Board '{board['name']}' has {len(posts)} posts.")
            return

        controller.unpin_post(board['id'], post_number - 1)
        self.caller.msg(f"Post {post_number} in board '{board['name']}' has been unpinned.")


class CmdEditBoard(default_cmds.MuxCommand):
    """
    Edit the settings or description of a board.

    Usage:
      +bbs/editboard <board_name> = <field>, <new_value>

    Example:
      +bbs/editboard Announcements = description, A board for official announcements.
      +bbs/editboard Announcements = public, true
    """
    key = "+bbs/editboard"
    locks = "cmd:perm(Builder)"
    help_category = "BBS"

    def func(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/editboard <board_name> = <field>, <new_value>")
            return
        board_name, updates = [arg.strip() for arg in self.args.split("=", 1)]
        field, new_value = [arg.strip() for arg in updates.split(",", 1)]

        controller = BBSController.objects.get(db_key="BBSController")
        if not controller:
            self.caller.msg("BBSController not found.")
            return

        board = controller.get_board(board_name)
        if not board:
            self.caller.msg(f"No board found with the name '{board_name}'.")
            return

        if field == "description":
            board['description'] = new_value
        elif field == "public":
            board['public'] = new_value.lower() in ["true", "yes", "1"]
        else:
            self.caller.msg(f"Invalid field '{field}'. You can edit 'description' or 'public'.")
            return

        controller.save_board(board_name, board)
        self.caller.msg(f"Board '{board_name}' has been updated. {field.capitalize()} set to '{new_value}'.")


class CmdGrantAccess(default_cmds.MuxCommand):
    """
    Grant access to a private board.

    Usage:
      +bbs/grantaccess <board_name> = <character_name> [/readonly]

    This command grants full access to a character by default. If "/readonly" is specified,
    the character is granted read-only access instead.

    Examples:
      +bbs/grantaccess Announcements = John
      +bbs/grantaccess Announcements = John /readonly
    """
    key = "+bbs/grantaccess"
    locks = "cmd:perm(Builder)"
    help_category = "BBS"

    def func(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/grantaccess <board_name> = <character_name> [/readonly]")
            return
        board_name, args = [arg.strip() for arg in self.args.split("=", 1)]
        character_name, *options = [arg.strip() for arg in args.split(" ")]

        # Determine access level
        access_level = "read_only" if "/readonly" in options else "full_access"

        controller = BBSController.objects.get(db_key="BBSController")
        if not controller:
            self.caller.msg("BBSController not found.")
            return

        board = controller.get_board(board_name)
        if not board:
            self.caller.msg(f"No board found with the name '{board_name}'.")
            return

        controller.grant_access(board_name, character_name, access_level=access_level)
        access_type = "read-only" if access_level == "read_only" else "full access"
        self.caller.msg(f"Granted {access_type} to {character_name} for board '{board_name}'.")