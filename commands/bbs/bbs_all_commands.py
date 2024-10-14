#commands/bbs/bbs_all_commands.py

from evennia import default_cmds
from evennia import create_object
from typeclasses.bbs_controller import BBSController
from world.wod20th.utils.bbs_utils import get_or_create_bbs_controller
class CmdPost(default_cmds.MuxCommand):
    """
    Post a message on a board.

    Usage:
      +bbs/post <board_name_or_number>/<title> = <content>
    """
    key = "+bbs/post"
    locks = "cmd:all()"
    help_category = "BBS"

    def func(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/post <board_name_or_number>/<title> = <content>")
            return
        board_ref, post_data = [arg.strip() for arg in self.args.split("/", 1)]
        title, content = [arg.strip() for arg in post_data.split("=", 1)]

        # Try to get the BBSController, create it if it doesn't exist
        try:
            controller = BBSController.objects.get(db_key="BBSController")
        except BBSController.DoesNotExist:
            controller = create_object(BBSController, key="BBSController")
            controller.db.boards = {}  # Initialize with an empty boards dictionary
            self.caller.msg("BBSController created.")

        try:
            board_ref = int(board_ref)  # Try converting to an integer
        except ValueError:
            pass

        board = controller.get_board(board_ref)
        if not board:
            self.caller.msg(f"No board found with the name or number '{board_ref}'.")
            return
        if board.get('locked', False):
            self.caller.msg(f"The board '{board['name']}' is locked. No new posts can be made.")
            return
        if not controller.has_write_access(board_ref, self.caller.key):
            self.caller.msg(f"You do not have write access to post on the board '{board['name']}'.")
            return
        controller.create_post(board_ref, title, content, self.caller.key)
        self.caller.msg(f"Post '{title}' added to board '{board['name']}'.")

class CmdReadBBS(default_cmds.MuxCommand):
    """
    List all boards or posts in a board, or read a specific post.

    Usage:
      +bbs
      +bbs <board_name_or_number>
      +bbs <board_number>/<post_number>
    """
    key = "+bbs"
    locks = "cmd:all()"
    help_category = "BBS"

    def func(self):
        controller = get_or_create_bbs_controller()

        if not self.args:
            self.list_boards(controller)
        else:
            arg = self.args.strip()
            if "/" in arg:
                # Handle reading a specific post: +bbs <board_id>/<post_id>
                board_ref, post_number = arg.split("/", 1)
                try:
                    board_ref = int(board_ref)
                    post_number = int(post_number)
                    self.read_post(controller, board_ref, post_number)
                except ValueError:
                    self.caller.msg("Usage: +bbs <board_id>/<post_id> where both are numbers.")
            else:
                # List posts in a board
                try:
                    board_ref = int(arg)
                except ValueError:
                    board_ref = arg

                self.list_posts(controller, board_ref)

    def list_boards(self, controller):
        """List all available boards."""
        boards = controller.db.boards
        if not boards:
            self.caller.msg("No boards available.")
            return

        # Table Header
        output = []
        output.append("=" * 78)
        output.append("{:<5} {:<10} {:<30} {:<20} {:<15}".format("ID", "Access", "Group Name", "Last Post", "# of messages"))
        output.append("-" * 78)

        for board_id, board in boards.items():
            access_type = "Private" if not board['public'] else "Public"
            read_only = "*" if controller.has_access(board_id, self.caller.key) and not controller.has_write_access(board_id, self.caller.key) else " "
            last_post = max((post['created_at'] for post in board['posts']), default="No posts")
            num_posts = len(board['posts'])
            output.append(f"{board_id:<5} {access_type:<10} {read_only} {board['name']:<30} {last_post:<20} {num_posts:<15}")

        # Table Footer
        output.append("-" * 78)
        output.append("* = read only")
        output.append("=" * 78)

        self.caller.msg("\n".join(output))

    def list_posts(self, controller, board_ref):
        """List all posts in the specified board."""
        board = controller.get_board(board_ref)
        if not board:
            self.caller.msg(f"No board found with the name or number '{board_ref}'.")
            return
        if not controller.has_access(board_ref, self.caller.key):
            self.caller.msg(f"You do not have access to view posts on the board '{board['name']}'.")
            return

        posts = board['posts']
        pinned_posts = [post for post in posts if post.get('pinned', False)]
        unpinned_posts = [post for post in posts if not post.get('pinned', False)]

        # Table Header
        output = []
        output.append("=" * 78)
        output.append(f"{'*' * 20} {board['name']} {'*' * 20}")
        output.append("{:<5} {:<40} {:<20} {:<15}".format("ID", "Message", "Posted", "By"))
        output.append("-" * 78)

        # List pinned posts first with correct IDs
        for i, post in enumerate(pinned_posts):
            post_id = posts.index(post) + 1
            output.append(f"{board['id']}/{post_id:<5} [Pinned] {post['title']:<40} {post['created_at']:<20} {post['author']}")

        # List unpinned posts with correct IDs
        for post in unpinned_posts:
            post_id = posts.index(post) + 1
            output.append(f"{board['id']}/{post_id:<5} {post['title']:<40} {post['created_at']:<20} {post['author']}")

        # Table Footer
        output.append("=" * 78)

        self.caller.msg("\n".join(output))

    def read_post(self, controller, board_ref, post_number):
        """Read a specific post in a board."""
        board = controller.get_board(board_ref)
        if not board:
            self.caller.msg(f"No board found with the name or number '{board_ref}'.")
            return
        if not controller.has_access(board_ref, self.caller.key):
            self.caller.msg(f"You do not have access to view posts on the board '{board['name']}'.")
            return
        posts = board['posts']
        if post_number < 1 or post_number > len(posts):
            self.caller.msg(f"Invalid post number. Board '{board['name']}' has {len(posts)} posts.")
            return
        post = posts[post_number - 1]
        edit_info = f"(edited on {post['edited_at']})" if post['edited_at'] else ""

        self.caller.msg(f"{'-'*40}")
        self.caller.msg(f"Title: {post['title']}")
        self.caller.msg(f"Author: {post['author']}")
        self.caller.msg(f"Date: {post['created_at']} {edit_info}")
        self.caller.msg(f"{'-'*40}")
        self.caller.msg(f"{post['content']}")
        self.caller.msg(f"{'-'*40}")

class CmdEditPost(default_cmds.MuxCommand):
    """
    Edit a post in a board.

    Usage:
      +bbs/editpost <board_name>/<post_number> = <new_content>
    """
    key = "+bbs/editpost"
    locks = "cmd:all()"
    help_category = "BBS"

    def func(self):
        if not self.args or "/" not in self.args:
            self.caller.msg("Usage: +bbs/editpost <board_name>/<post_number> = <new_content>")
            return
        board_name, post_data = [arg.strip() for arg in self.args.split("/", 1)]
        post_number, new_content = [arg.strip() for arg in post_data.split("=", 1)]

        controller = BBSController.objects.get(db_key="BBSController")
        if not controller:
            self.caller.msg("BBSController not found.")
            return

        board = controller.get_board(board_name)
        if not board:
            self.caller.msg(f"No board found with the name '{board_name}'.")
            return
        if board.get('locked', False):
            self.caller.msg(f"The board '{board_name}' is locked. No edits can be made.")
            return
        if not controller.has_write_access(board_name, self.caller.key):
            self.caller.msg(f"You do not have write access to edit posts on the board '{board_name}'.")
            return
        try:
            post_number = int(post_number)
        except ValueError:
            self.caller.msg("Post number must be an integer.")
            return
        posts = board['posts']
        if post_number < 1 or post_number > len(posts):
            self.caller.msg(f"Invalid post number. Board '{board_name}' has {len(posts)} posts.")
            return
        post = posts[post_number - 1]

        if self.caller.is_superuser:
            controller.edit_post(board_name, post_number - 1, new_content)
            self.caller.msg(f"SuperUser: Post {post_number} in board '{board_name}' has been updated.")

        if not (self.caller.key == post['author']):
            self.caller.msg("You do not have permission to edit this post.")
            return

        controller.edit_post(board_name, post_number - 1, new_content)
        self.caller.msg(f"Author: Post {post_number} in board '{board_name}' has been updated.")


class CmdDeletePost(default_cmds.MuxCommand):
    """
    Delete a post from a board.

    Usage:
      +bbs/deletepost <board_name>/<post_number>
    """
    key = "+bbs/deletepost"
    locks = "cmd:all()"
    help_category = "BBS"

    def func(self):
        if not self.args or "/" not in self.args:
            self.caller.msg("Usage: +bbs/deletepost <board_name>/<post_number>")
            return

        board_name, post_number = [arg.strip() for arg in self.args.split("/", 1)]

        controller = BBSController.objects.get(db_key="BBSController")
        if not controller:
            self.caller.msg("BBSController not found.")
            return

        board = controller.get_board(board_name)
        if not board:
            self.caller.msg(f"No board found with the name '{board_name}'.")
            return
        try:
            post_number = int(post_number)
        except ValueError:
            self.caller.msg("Post number must be an integer.")
            return
        posts = board['posts']
        if post_number < 1 or post_number > len(posts):
            self.caller.msg(f"Invalid post number. Board '{board_name}' has {len(posts)} posts.")
            return
        post = posts[post_number - 1]

        if self.caller.is_superuser:
            controller.delete_post(board_name, post_number - 1)
            self.caller.msg(f"SuperUser: Post {post_number} has been deleted from board '{board_name}'.")
        elif not (self.caller.key == post['author']):
            self.caller.msg("You do not have permission to delete this post.")
        else:
            controller.delete_post(board_name, post_number - 1)
            self.caller.msg(f"Author: Post {post_number} has been deleted from board '{board_name}'.")

        







