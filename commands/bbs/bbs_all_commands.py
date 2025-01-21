#commands/bbs/bbs_all_commands.py

from evennia import default_cmds
from evennia import create_object
from typeclasses.bbs_controller import BBSController
from world.wod20th.utils.bbs_utils import get_or_create_bbs_controller

class CmdBBS(default_cmds.MuxCommand):
    """
    Access the bulletin board system.
    
    Usage:
      +bbs                        - List all available boards
      +bbs <board>               - List all posts on a board
      +bbs <board>/<post>        - Read a specific post
      +bbs/post <board>/<title> = <message>
                                - Post a new message
      +bbs/edit <board>/<post> = <new message>
                                - Edit one of your posts
      +bbs/delete <board>/<post> - Delete one of your posts
      
    Admin/Builder commands:
      +bbs/create <name> = <description>/<access>
                                - Create a new board (access: public/private)
      +bbs/lock <board>         - Lock a board to prevent new posts
      +bbs/pin <board>/<post>   - Pin a post to the top
      +bbs/unpin <board>/<post> - Unpin a post
      +bbs/grant <board> = <player>[/readonly]
                                - Grant access to a private board
      +bbs/revoke <board> = <player>
                                - Revoke access from a private board
      +bbs/deleteboard <board>  - Delete an entire board
      
    Examples:
      +bbs
      +bbs announcements
      +bbs 1/1
      +bbs/post announcements/Welcome! = Hello everyone!
      +bbs/edit 1/1 = This is the corrected message.
      +bbs/delete 1/1
      +bbs/create Staff = Staff Discussion/private
      +bbs/grant staff = Bob/readonly
    """
    key = "+bbs"
    aliases = ["@bbs", "bbs"]
    locks = "cmd:all()"
    help_category = "BBS"

    def check_admin_access(self):
        """Check if the caller has admin access."""
        return self.caller.locks.check_lockstring(self.caller, "perm(Admin)")

    def check_builder_access(self):
        """Check if the caller has builder access."""
        return self.caller.locks.check_lockstring(self.caller, "perm(Builder)")

    def func(self):
        if not self.args and not self.switches:
            # Just +bbs - list all boards
            controller = get_or_create_bbs_controller()
            self.list_boards(controller)
            return

        # Handle switches
        if self.switches:
            switch = self.switches[0].lower()
            
            # User commands
            if switch == "post":
                self.do_post()
            elif switch == "edit":
                self.do_edit()
            elif switch == "delete":
                self.do_delete()
            
            # Admin/Builder commands
            elif switch in ["create", "lock", "pin", "unpin", "grant", "revoke", "deleteboard"]:
                if not (self.check_admin_access() or self.check_builder_access()):
                    self.caller.msg("You don't have permission to use this command.")
                    return
                    
                if switch == "create":
                    self.do_create()
                elif switch == "lock":
                    self.do_lock()
                elif switch == "pin":
                    self.do_pin()
                elif switch == "unpin":
                    self.do_unpin()
                elif switch == "grant":
                    self.do_grant()
                elif switch == "revoke":
                    self.do_revoke()
                elif switch == "deleteboard":
                    self.do_deleteboard()
            else:
                self.caller.msg("Invalid switch or insufficient permissions.")
            return

        # No switch - handle reading posts
        if "/" in self.args:
            # Reading specific post
            board_ref, post_number = self.args.split("/", 1)
            try:
                board_ref = int(board_ref)
                post_number = int(post_number)
                controller = get_or_create_bbs_controller()
                self.read_post(controller, board_ref, post_number)
            except ValueError:
                self.caller.msg("Usage: +bbs <board_number>/<post_number> where both are numbers.")
        else:
            # Listing posts in a board
            try:
                board_ref = int(self.args)
            except ValueError:
                board_ref = self.args
            controller = get_or_create_bbs_controller()
            self.list_posts(controller, board_ref)

    def do_post(self):
        """Handle the post switch"""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/post <board>/<title> = <content>")
            return
        if "/" not in self.args.split("=")[0]:
            self.caller.msg("Usage: +bbs/post <board>/<title> = <content>")
            return
            
        board_ref, post_data = [arg.strip() for arg in self.args.split("/", 1)]
        title, content = [arg.strip() for arg in post_data.split("=", 1)]

        controller = get_or_create_bbs_controller()
        try:
            board_ref = int(board_ref)
        except ValueError:
            pass

        board = controller.get_board(board_ref)
        if not board:
            self.caller.msg(f"No board found with the name or number '{board_ref}'.")
            return
        if board.get('locked', False) and not (self.check_admin_access() or self.check_builder_access()):
            self.caller.msg(f"The board '{board['name']}' is locked. No new posts can be made.")
            return
        if not controller.has_write_access(board_ref, self.caller.key):
            self.caller.msg(f"You do not have write access to post on the board '{board['name']}'.")
            return
            
        controller.create_post(board_ref, title, content, self.caller.key)
        self.caller.msg(f"Post '{title}' added to board '{board['name']}'.")

    def do_edit(self):
        """Handle the edit switch"""
        if not self.args or "/" not in self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/edit <board>/<post> = <new_content>")
            return
            
        board_name, post_data = [arg.strip() for arg in self.args.split("/", 1)]
        post_number, new_content = [arg.strip() for arg in post_data.split("=", 1)]

        controller = get_or_create_bbs_controller()
        board = controller.get_board(board_name)
        if not board:
            self.caller.msg(f"No board found with the name '{board_name}'.")
            return
        if board.get('locked', False) and not (self.check_admin_access() or self.check_builder_access()):
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
        if self.check_admin_access() or self.check_builder_access() or self.caller.key == post['author']:
            controller.edit_post(board_name, post_number - 1, new_content)
            self.caller.msg(f"Post {post_number} in board '{board_name}' has been updated.")
        else:
            self.caller.msg("You do not have permission to edit this post.")

    def do_delete(self):
        """Handle the delete switch"""
        if not self.args or "/" not in self.args:
            self.caller.msg("Usage: +bbs/delete <board>/<post>")
            return
            
        board_name, post_number = [arg.strip() for arg in self.args.split("/", 1)]

        controller = get_or_create_bbs_controller()
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
        if self.check_admin_access() or self.check_builder_access() or self.caller.key == post['author']:
            controller.delete_post(board_name, post_number - 1)
            self.caller.msg(f"Post {post_number} has been deleted from board '{board_name}'.")
        else:
            self.caller.msg("You do not have permission to delete this post.")

    def do_create(self):
        """Handle the create switch"""
        if not self.args or "=" not in self.args or "/" not in self.args.split("=")[1]:
            self.caller.msg("Usage: +bbs/create <name> = <description>/public|private")
            return
            
        name_desc, privacy = self.args.rsplit("/", 1)
        name, description = [arg.strip() for arg in name_desc.split("=", 1)]
        public = privacy.strip().lower() == "public"

        controller = get_or_create_bbs_controller()
        controller.create_board(name, description, public)
        self.caller.msg(f"Board '{name}' created as {'public' if public else 'private'} with description: {description}")

    def do_lock(self):
        """Handle the lock switch"""
        if not self.args:
            self.caller.msg("Usage: +bbs/lock <board>")
            return
            
        board_name = self.args.strip()
        controller = get_or_create_bbs_controller()
        result = controller.lock_board(board_name)
        self.caller.msg(result)

    def do_pin(self):
        """Handle the pin switch"""
        if not self.args or "/" not in self.args:
            self.caller.msg("Usage: +bbs/pin <board>/<post>")
            return
            
        board_ref, post_number = [arg.strip() for arg in self.args.split("/", 1)]
        controller = get_or_create_bbs_controller()
        
        try:
            post_number = int(post_number)
        except ValueError:
            self.caller.msg("Post number must be an integer.")
            return
            
        result = controller.pin_post(board_ref, post_number - 1)
        self.caller.msg(result)

    def do_unpin(self):
        """Handle the unpin switch"""
        if not self.args or "/" not in self.args:
            self.caller.msg("Usage: +bbs/unpin <board>/<post>")
            return
            
        board_ref, post_number = [arg.strip() for arg in self.args.split("/", 1)]
        controller = get_or_create_bbs_controller()
        
        try:
            post_number = int(post_number)
        except ValueError:
            self.caller.msg("Post number must be an integer.")
            return
            
        result = controller.unpin_post(board_ref, post_number - 1)
        self.caller.msg(result)

    def do_grant(self):
        """Handle the grant switch"""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/grant <board> = <character>[/readonly]")
            return
            
        board_name, args = [arg.strip() for arg in self.args.split("=", 1)]
        character_name, *options = [arg.strip() for arg in args.split(" ")]
        access_level = "read_only" if "/readonly" in options else "full_access"

        controller = get_or_create_bbs_controller()
        board = controller.get_board(board_name)
        if not board:
            self.caller.msg(f"No board found with the name '{board_name}'.")
            return

        controller.grant_access(board_name, character_name, access_level=access_level)
        access_type = "read-only" if access_level == "read_only" else "full access"
        self.caller.msg(f"Granted {access_type} to {character_name} for board '{board_name}'.")

    def do_revoke(self):
        """Handle the revoke switch"""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/revoke <board> = <character>")
            return
            
        board_name, character_name = [arg.strip() for arg in self.args.split("=", 1)]

        controller = get_or_create_bbs_controller()
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

    def do_deleteboard(self):
        """Handle the deleteboard switch"""
        if not self.args:
            self.caller.msg("Usage: +bbs/deleteboard <board>")
            return
            
        board_name = self.args.strip()
        controller = get_or_create_bbs_controller()
        result = controller.delete_board(board_name)
        self.caller.msg(result)

    # Keep the existing list_boards, list_posts, and read_post methods
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

        # Sort boards by ID and convert to list of tuples
        sorted_boards = sorted(boards.items(), key=lambda x: x[0])

        for board_id, board in sorted_boards:
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

        







