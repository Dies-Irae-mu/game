#commands/bbs/bbs_all_commands.py

# Standard Library Imports
from datetime import datetime

# Django Imports
from django.utils import timezone

# Evennia Imports
from evennia import default_cmds
from evennia import create_object
from evennia.server.sessionhandler import SESSION_HANDLER

# Local Imports
from typeclasses.bbs_controller import BBSController
from world.wod20th.utils.bbs_utils import get_or_create_bbs_controller
from world.wod20th.models import Roster
import pytz
from world.wod20th.utils.time_utils import TIME_MANAGER

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
      +bbs/scan                  - Show unread posts on all accessible boards
      +bbs/readall <board>       - Mark all posts in a board as read
      
    Admin/Builder commands:
      +bbs/create <name> = <description>[/roster=<roster1>,<roster2>...]
                                - Create a new board
                                - Optional roster restrictions can be specified
      +bbs/editboard <board> = <field>, <value>
                                - Edit board settings (description)
      +bbs/editboard/rosters <board> = <roster1>[,<roster2>...]
                                - Set roster restrictions for a board
                                - Use empty value to clear all restrictions
      +bbs/addroster <board> = <roster>
                                - Add a roster restriction to a board
      +bbs/removeroster <board> = <roster>
                                - Remove a roster restriction
      +bbs/listrosters <board>  - List all rosters on a board
      +bbs/lock <board>         - Lock a board to prevent new posts
      +bbs/pin <board>/<post>   - Pin a post to the top
      +bbs/unpin <board>/<post> - Unpin a post
      +bbs/deleteboard <board>  - Delete an entire board
      +bbs/readonly <board>     - Toggle read-only mode for a board
      +bbs/viewas <board> = <player>
                                - View a board as if you were another player
                                - Useful for verifying permissions
      
    Admin options:
      --asPlayer=<player>        - View boards/posts as if you were another player
                                - Can be used with any read-based command
                                - Example: +bbs --asPlayer=JohnDoe
                                - Example: +bbs announcements --asPlayer=JohnDoe
      
    Board Permissions:
      Boards can have multiple permission settings that interact:
      
      1. Roster Restrictions:
         - When a board has roster restrictions:
           * Only members of the specified rosters can see and post
           * This is indicated by a * after the board name
           * Admins/Builders can always see and post
      
      2. Read-Only Mode:
         - When a board is read-only:
           * Only Admins/Builders can post/edit/delete
           * Everyone else can still read the board
           * This is indicated by a * before the board name
      
      Examples:
        - A board with roster restrictions:
          * Only roster members can see and post
          * Admins/Builders have full access
          * Shows as "BoardName*" in listings
      
        - A read-only board:
          * Everyone can read
          * Only Admins/Builders can post
          * Shows as "* BoardName" in listings
      
        - A read-only board with roster restrictions:
          * Only roster members can read
          * Only Admins/Builders can post
          * Shows as "* BoardName*" in listings
      
    Examples:
      +bbs
      +bbs announcements
      +bbs 1/1
      +bbs/post announcements/Welcome! = Hello everyone!
      +bbs/edit 1/1 = This is the corrected message.
      +bbs/delete 1/1
      +bbs/create Staff = Staff Discussion
      +bbs/create IC = In Character/roster=Vampire,Werewolf
      +bbs/editboard/rosters IC = Vampire,Werewolf,Mage
      +bbs/addroster IC = Hunter
      +bbs/removeroster IC = Vampire
      +bbs/readonly Announcements
    """
    key = "+bbs"
    aliases = ["bbs", "@bbs", "bb", "+bb"]
    locks = "cmd:all()"
    help_category = "Event & Bulletin Board"

    def check_admin_access(self):
        """Check if the caller has admin access."""
        return self.caller.locks.check_lockstring(self.caller, "perm(Admin)")

    def check_builder_access(self):
        """Check if the caller has builder access."""
        return self.caller.locks.check_lockstring(self.caller, "perm(Builder)")

    def send_bbs_notification(self, board, message, exclude_char=None):
        """
        Send a notification about BBS activity to all eligible online users.
        
        Args:
            board (dict): The board dictionary containing board information
            message (str): The notification message to send
            exclude_char (Character, optional): Character to exclude from notification
        """
        session_list = SESSION_HANDLER.get_sessions()
        controller = get_or_create_bbs_controller()
        
        for session in session_list:
            if not session.logged_in:
                continue
            puppet = session.get_puppet()
            if not puppet or (exclude_char and puppet == exclude_char):
                continue
            if controller.has_access(board['id'], puppet.key):
                puppet.msg(f"|w{message}|n")

    def format_datetime(self, dt_str, target_char=None):
        """Format datetime string in the user's timezone."""
        if not target_char:
            target_char = self.caller
            
        try:
            # Parse the datetime string to a datetime object
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            dt = dt.replace(tzinfo=timezone.utc)
            
            # Get the caller's timezone
            tz_name = target_char.attributes.get("timezone", "UTC")
            try:
                # Try to get the timezone from pytz
                tz = pytz.timezone(TIME_MANAGER.normalize_timezone_name(tz_name))
                # Convert to the caller's timezone
                local_dt = dt.astimezone(tz)
                # Format without timezone indicator
                return local_dt.strftime("%Y-%m-%d %H:%M")
            except (pytz.exceptions.UnknownTimeZoneError, AttributeError, ValueError):
                # Fallback to UTC if there's any error
                return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            # If we can't parse the datetime string, return it as is
            return dt_str

    def func(self):
        # Check for --asPlayer option
        as_player = None
        if "--asPlayer=" in self.args:
            parts = self.args.split("--asPlayer=", 1)
            self.args = parts[0].strip()
            player_name = parts[1].strip()
            
            # Find the player
            from evennia.utils import search
            players = search.search_object_by_keyclass(player_name, "typeclasses.characters.Character")
            
            if not players:
                self.caller.msg(f"No player found with the name '{player_name}'.")
                return
                
            as_player = players[0]
            
            # Only admins and builders can use this option
            if not (self.check_admin_access() or self.check_builder_access()):
                self.caller.msg("You don't have permission to use the --asPlayer option.")
                return
                
            self.caller.msg(f"Viewing as {as_player.key}...")

        if not self.args and not self.switches:
            # Just +bbs - list all boards
            controller = get_or_create_bbs_controller()
            if as_player:
                self.list_boards_as_player(controller, as_player)
            else:
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
            elif switch == "scan":
                if as_player:
                    self.do_scan_as_player(as_player)
                else:
                    self.do_scan()
            elif switch == "readall":
                if as_player:
                    self.do_readall_as_player(as_player)
                else:
                    self.do_readall()
            
            # Admin/Builder commands
            elif switch in ["create", "editboard", "editboard/rosters", "addroster", "removeroster", "listrosters", "lock", "pin", "unpin", "deleteboard", "readonly", "viewas"]:
                if not (self.check_admin_access() or self.check_builder_access()):
                    self.caller.msg("You don't have permission to use this command.")
                    return
                    
                if switch == "create":
                    self.do_create()
                elif switch == "editboard":
                    self.do_editboard()
                elif switch == "editboard/rosters":
                    self.do_editboard_rosters()
                elif switch == "addroster":
                    self.do_addroster()
                elif switch == "removeroster":
                    self.do_removeroster()
                elif switch == "listrosters":
                    self.do_listrosters()
                elif switch == "lock":
                    self.do_lock()
                elif switch == "pin":
                    self.do_pin()
                elif switch == "unpin":
                    self.do_unpin()
                elif switch == "deleteboard":
                    self.do_deleteboard()
                elif switch == "readonly":
                    self.do_readonly()
                elif switch == "viewas":
                    self.do_viewas()
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
                if as_player:
                    self.read_post_as_player(controller, board_ref, post_number, as_player)
                else:
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
            if as_player:
                self.list_posts_as_player(controller, board_ref, as_player)
            else:
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
        board = controller.get_board(board_ref)
        if not board:
            self.caller.msg(f"No board found with the name or number '{board_ref}'.")
            return
        if board.get('locked', False) and not (self.check_admin_access() or self.check_builder_access()):
            self.caller.msg(f"The board '{board['name']}' is locked. No new posts can be made.")
            return
        if not controller.has_write_access(board['id'], self.caller.key):
            self.caller.msg(f"You do not have write access to post on the board '{board['name']}'.")
            return
            
        post_number = len(board['posts']) + 1
        controller.create_post(board['id'], title, content, self.caller.key)
        
        self.caller.msg(f"Post '{title}' added to board '{board['name']}'.")
        
        # Notify online users about the new post
        message = f"New post on {board['name']} (+bb {board['id']}/{post_number}) by {self.caller.key}: {title}"
        self.send_bbs_notification(board, message, exclude_char=self.caller)

    def do_edit(self):
        """Handle the edit switch"""
        if not self.args or "/" not in self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/edit <board_name_or_number>/<post> = <new_content>")
            return
            
        board_ref, post_data = [arg.strip() for arg in self.args.split("/", 1)]
        post_number, new_content = [arg.strip() for arg in post_data.split("=", 1)]

        controller = get_or_create_bbs_controller()
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
            
        post = posts[post_number - 1]
        is_author = self.caller.key == post['author']
        is_admin = self.check_admin_access() or self.check_builder_access()
        
        # Check if board is locked
        if board.get('locked', False):
            if is_admin:
                # Admins/Builders can still edit on locked boards
                controller.edit_post(board['id'], post_number - 1, new_content)
                self.caller.msg(f"Post {post_number} in board '{board['name']}' has been updated (admin override on locked board).")
            else:
                self.caller.msg(f"The board '{board['name']}' is locked. No edits can be made.")
            return
            
        # Not locked, check permissions
        if is_admin or is_author:
            controller.edit_post(board['id'], post_number - 1, new_content)
            self.caller.msg(f"Post {post_number} in board '{board['name']}' has been updated.")
        else:
            self.caller.msg("You do not have permission to edit this post.")

    def do_delete(self):
        """Handle the delete switch"""
        if not self.args or "/" not in self.args:
            self.caller.msg("Usage: +bbs/delete <board_name_or_number>/<post>")
            return
            
        board_ref, post_number = [arg.strip() for arg in self.args.split("/", 1)]

        controller = get_or_create_bbs_controller()
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
            
        post = posts[post_number - 1]
        if self.check_admin_access() or self.check_builder_access() or self.caller.key == post['author']:
            controller.delete_post(board['id'], post_number - 1)
            self.caller.msg(f"Post {post_number} has been deleted from board '{board['name']}'.")
        else:
            self.caller.msg("You do not have permission to delete this post.")

    def do_create(self):
        """Handle the create switch"""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/create <name> = <description>[/roster=<roster1>,<roster2>...]")
            return
            
        # Split into name_desc and description/roster parts
        name_desc, remainder = self.args.split("=", 1)
        parts = remainder.split("/")
        
        if len(parts) < 1:
            self.caller.msg("Usage: +bbs/create <name> = <description>[/roster=<roster1>,<roster2>...]")
            return
            
        description = parts[0].strip()
        
        # Check for roster specification
        roster_names = []
        if len(parts) > 1:
            for part in parts[1:]:
                if part.strip().lower().startswith("roster="):
                    roster_list = part.split("=")[1].strip()
                    roster_names = [r.strip() for r in roster_list.split(",")]
                    
                    # Verify all rosters exist
                    for roster_name in roster_names:
                        try:
                            Roster.objects.get(name=roster_name)
                        except Roster.DoesNotExist:
                            self.caller.msg(f"Error: Roster '{roster_name}' does not exist.")
                            return

        name = name_desc.strip()
        controller = get_or_create_bbs_controller()
        controller.create_board(name, description, roster_names=roster_names)
        
        msg = f"Board '{name}' created"
        if roster_names:
            msg += f" (restricted to rosters: {', '.join(roster_names)})"
        msg += f" with description: {description}"
        self.caller.msg(msg)

    def do_editboard(self):
        """Handle the editboard switch"""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/editboard <board> = <field>, <value>")
            return
            
        board_name, field_value = self.args.split("=", 1)
        field, value = [arg.strip() for arg in field_value.split(",", 1)]

        controller = get_or_create_bbs_controller()
        board = controller.get_board(board_name)
        if not board:
            self.caller.msg(f"No board found with the name '{board_name}'.")
            return
            
        if field not in ["description"]:
            self.caller.msg("Invalid field. Use 'description'.")
            return
            
        if value not in ["true", "false"]:
            self.caller.msg("Invalid value. Use 'true' or 'false'.")
            return
            
        controller.edit_board(board_name, field, value)
        self.caller.msg(f"Board '{board_name}' has been updated. {field} set to {value}.")

    def do_editboard_rosters(self):
        """Handle the editboard/rosters switch"""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/editboard/rosters <board> = <roster1>[,<roster2>...]")
            return
            
        board_name, rosters = self.args.split("=", 1)
        roster_list = [arg.strip() for arg in rosters.split(",")]

        controller = get_or_create_bbs_controller()
        board = controller.get_board(board_name)
        if not board:
            self.caller.msg(f"No board found with the name '{board_name}'.")
            return
            
        controller.edit_board_rosters(board_name, roster_list)
        self.caller.msg(f"Roster restrictions for board '{board_name}' have been updated.")

    def do_addroster(self):
        """Handle the addroster switch"""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/addroster <board> = <roster>")
            return
            
        board_name, roster = self.args.split("=", 1)
        controller = get_or_create_bbs_controller()
        board = controller.get_board(board_name)
        if not board:
            self.caller.msg(f"No board found with the name '{board_name}'.")
            return
            
        result = controller.add_roster_to_board(board_name, roster)
        self.caller.msg(result)

    def do_removeroster(self):
        """Handle the removeroster switch"""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/removeroster <board> = <roster>")
            return
            
        board_name, roster = self.args.split("=", 1)
        controller = get_or_create_bbs_controller()
        board = controller.get_board(board_name)
        if not board:
            self.caller.msg(f"No board found with the name '{board_name}'.")
            return
            
        controller.remove_roster(board_name, roster)
        self.caller.msg(f"Roster restriction '{roster}' removed from board '{board_name}'.")

    def do_listrosters(self):
        """Handle the listrosters switch"""
        if not self.args:
            self.caller.msg("Usage: +bbs/listrosters <board>")
            return
            
        board_name = self.args.strip()
        controller = get_or_create_bbs_controller()
        board = controller.get_board(board_name)
        if not board:
            self.caller.msg(f"No board found with the name '{board_name}'.")
            return
            
        roster_names = board.get('roster_names', [])
        if not roster_names:
            self.caller.msg(f"Board '{board_name}' has no roster restrictions.")
            return
            
        self.caller.msg(f"Rosters on board '{board_name}':")
        for roster_name in roster_names:
            try:
                roster = Roster.objects.get(name=roster_name)
                member_count = roster.get_members().count()
                self.caller.msg(f"- {roster_name} ({member_count} approved members)")
            except Roster.DoesNotExist:
                self.caller.msg(f"- {roster_name} (WARNING: Roster no longer exists!)")

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
        board = controller.get_board(board_ref)
        if not board:
            self.caller.msg(f"No board found with the name or number '{board_ref}'.")
            return
            
        try:
            post_number = int(post_number)
        except ValueError:
            self.caller.msg("Post number must be an integer.")
            return
            
        result = controller.pin_post(board['id'], post_number - 1)
        self.caller.msg(result)

    def do_unpin(self):
        """Handle the unpin switch"""
        if not self.args or "/" not in self.args:
            self.caller.msg("Usage: +bbs/unpin <board>/<post>")
            return
            
        board_ref, post_number = [arg.strip() for arg in self.args.split("/", 1)]
        controller = get_or_create_bbs_controller()
        board = controller.get_board(board_ref)
        if not board:
            self.caller.msg(f"No board found with the name or number '{board_ref}'.")
            return
            
        try:
            post_number = int(post_number)
        except ValueError:
            self.caller.msg("Post number must be an integer.")
            return
            
        result = controller.unpin_post(board['id'], post_number - 1)
        self.caller.msg(result)

    def do_deleteboard(self):
        """Handle the deleteboard switch"""
        if not self.args:
            self.caller.msg("Usage: +bbs/deleteboard <board>")
            return
            
        board_name = self.args.strip()
        controller = get_or_create_bbs_controller()
        result = controller.delete_board(board_name)
        self.caller.msg(result)

    def do_readonly(self):
        """Handle the readonly switch"""
        if not self.args:
            self.caller.msg("Usage: +bbs/readonly <board>")
            return
            
        board_ref = self.args.strip()
        controller = get_or_create_bbs_controller()
        board = controller.get_board(board_ref)
        if not board:
            self.caller.msg(f"No board found with the name or number '{board_ref}'.")
            return
            
        # Toggle read-only status
        current_status = board.get('read_only', False)
        result = controller.set_read_only(board['id'], not current_status)
        self.caller.msg(result)

    def do_scan(self):
        """Handle the scan switch - show unread posts on all accessible boards."""
        controller = get_or_create_bbs_controller()
        boards = controller.db.boards
        if not boards:
            self.caller.msg("No boards available.")
            return

        # Count total unread posts
        total_unread = 0
        unread_boards = []

        # Sort boards by ID
        sorted_boards = sorted(boards.items(), key=lambda x: x[0])

        for board_id, board in sorted_boards:
            if not controller.has_access(board_id, self.caller.key):
                continue

            unread_posts = controller.get_unread_posts(board_id, self.caller.key)
            if not unread_posts:
                continue

            total_unread += len(unread_posts)
            unread_boards.append((board['name'], len(unread_posts)))

        # If this is a login notification (no explicit command), show concise output
        if not hasattr(self, 'session') or not self.session:
            if total_unread > 0:
                board_summary = ", ".join(f"{name}: {count}" for name, count in unread_boards)
                self.caller.msg(f"|wYou have {total_unread} unread post{'s' if total_unread != 1 else ''} "
                              f"on the bulletin board ({board_summary}).|n")
            return

        # Otherwise show detailed scan output
        # Table Header
        output = []
        output.append("=" * 120)
        output.append("Unread Postings on the Global Bulletin Board")
        output.append("-" * 120)

        for board_id, board in sorted_boards:
            if not controller.has_access(board_id, self.caller.key):
                continue

            unread_posts = controller.get_unread_posts(board_id, self.caller.key)
            if not unread_posts:
                continue

            # Format unread posts numbers
            unread_str = ", ".join(str(x) for x in unread_posts)
            
            # Get board access type indicators
            access_type = ""
            if board.get('roster_names'):  # If board has roster restrictions
                access_type = "*"  # restricted
            elif not controller.has_write_access(board_id, self.caller.key):
                access_type = "-"  # read only

            # Format board name with access type
            board_name = f"{board['name']} {access_type}"
            
            output.append(f"{board_name} (#{board_id}): {len(unread_posts)} unread ({unread_str})")

        # Add footer with capacity information
        output.append("-" * 120)
        if total_unread > 0:
            total_posts = sum(len(b['posts']) for b in boards.values())
            if total_posts > 0:  # Avoid division by zero
                capacity = (total_unread / total_posts) * 100
                output.append(f"Total unread posts: {total_unread} ({capacity:.1f}% of all posts)")
        output.append("=" * 120)

        self.caller.msg("\n".join(output))

    def do_readall(self):
        """Mark all posts in a board as read.
        
        This command marks all posts in the specified board as read for the current user.
        This is useful when you want to clear all unread flags from a board at once.
        
        Usage:
            +bbs/readall <board>
            
        Example:
            +bbs/readall announcements
        """
        if not self.args:
            self.caller.msg("Usage: +bbs/readall <board>")
            return
            
        board_ref = self.args.strip()
        controller = get_or_create_bbs_controller()
        board = controller.get_board(board_ref)
        if not board:
            self.caller.msg(f"No board found with the name or number '{board_ref}'.")
            return
            
        if not (controller.has_access(board_ref, self.caller.key) or 
                self.check_admin_access() or 
                self.check_builder_access()):
            self.caller.msg(f"You do not have access to view posts on the board '{board['name']}'.")
            return
            
        # Mark all posts as read
        for i in range(len(board['posts'])):
            controller.mark_post_read(board_ref, i, self.caller.key)
            
        self.caller.msg(f"All posts in board '{board['name']}' have been marked as read.")

    def list_boards(self, controller):
        """List all available boards."""
        boards = controller.db.boards
        if not boards:
            self.caller.msg("No boards available.")
            return

        # Table Header
        output = []
        output.append("=" * 120)
        output.append("{:<5} {:<10} {:<40} {:<20} {:<15} {:<10}".format("ID", "Access", "Name", "Last Post", "# of messages", "Unread"))
        output.append("-" * 120)

        # Sort boards by ID and convert to list of tuples
        sorted_boards = sorted(boards.items(), key=lambda x: x[0])

        for board_id, board in sorted_boards:
            # Skip boards the character doesn't have access to
            if not controller.has_access(board_id, self.caller.key):
                # Only admins and builders can see boards they don't have access to
                if not (self.check_admin_access() or self.check_builder_access()):
                    continue

            # Check if user has write access, considering admin/builder status
            has_write = controller.has_write_access(board_id, self.caller.key) or self.check_admin_access() or self.check_builder_access()
            read_only = "*" if not has_write else " "
            
            # Determine access type
            if board.get('roster_names'):
                access_type = "Roster"
            elif not board.get('public', True):  # Default to public if not specified
                access_type = "Private"
            else:
                access_type = "Public"
            
            # Get last post time, ensuring it's a date/time string
            last_post = "No posts"
            if board['posts']:
                last_post = max((post['created_at'] for post in board['posts']), default="No posts")
                if last_post != "No posts":
                    last_post = self.format_datetime(last_post)

            num_posts = len(board['posts'])
            
            # Get unread post count
            unread_posts = controller.get_unread_posts(board_id, self.caller.key)
            unread_count = len(unread_posts)
            unread_display = str(unread_count) if unread_count > 0 else "-"

            output.append(f"{board_id:<5} {access_type:<10} {read_only} {board['name']:<40} {last_post:<20} {num_posts:<15} {unread_display:<10}")

        # Table Footer
        output.append("-" * 120)
        output.append("* = read only")
        output.append("=" * 120)

        self.caller.msg("\n".join(output))

    def list_posts(self, controller, board_ref):
        """List all posts in the specified board."""
        board = controller.get_board(board_ref)
        if not board:
            self.caller.msg(f"No board found with the name or number '{board_ref}'.")
            return
        if not (controller.has_access(board_ref, self.caller.key) or 
                self.check_admin_access() or 
                self.check_builder_access()):
            self.caller.msg(f"You do not have access to view posts on the board '{board['name']}'.")
            return

        posts = board['posts']
        pinned_posts = [post for post in posts if post.get('pinned', False)]
        unpinned_posts = [post for post in posts if not post.get('pinned', False)]

        # Table Header
        output = []
        output.append("=" * 120)
        output.append(f"{'*' * 20} {board['name']} {'*' * 20}")
        
        # Add roster information if any, but only for admins and builders
        roster_names = board.get('roster_names', [])
        if roster_names and (self.check_admin_access() or self.check_builder_access()):
            output.append("Restricted to rosters:")
            for roster_name in roster_names:
                try:
                    roster = Roster.objects.get(name=roster_name)
                    member_count = roster.get_members().count()
                    output.append(f"- {roster_name}(ref: {roster.id}, members: {member_count})")
                except Roster.DoesNotExist:
                    output.append(f"- {roster_name} (WARNING: Roster no longer exists!)")

        # Add board access information
        if not board.get('public', True):
            output.append("|rThis is a private board|n")
        elif roster_names:
            output.append("|yThis board is restricted to specific rosters|n")

        output.append("{:<5} {:<1} {:<40} {:<20} {:<15}".format("ID", "", "Message", "Posted", "By"))
        output.append("-" * 120)

        # List pinned posts first with correct IDs
        for i, post in enumerate(pinned_posts):
            post_id = posts.index(post) + 1
            formatted_time = self.format_datetime(post['created_at'])
            is_unread = controller.is_post_unread(board['id'], post_id - 1, self.caller.key)
            unread_flag = "|rU|n" if is_unread else " "
            output.append(f"{board['id']}/{post_id:<5} {unread_flag:<1} [Pinned] {post['title']:<40} {formatted_time:<20} {post['author']}")

        # List unpinned posts with correct IDs
        for post in unpinned_posts:
            post_id = posts.index(post) + 1
            formatted_time = self.format_datetime(post['created_at'])
            is_unread = controller.is_post_unread(board['id'], post_id - 1, self.caller.key)
            unread_flag = "|rU|n" if is_unread else " "
            output.append(f"{board['id']}/{post_id:<5} {unread_flag:<1} {post['title']:<40} {formatted_time:<20} {post['author']}")

        # Table Footer
        output.append("=" * 120)

        self.caller.msg("\n".join(output))

    def read_post(self, controller, board_ref, post_number):
        """Read a specific post in a board."""
        board = controller.get_board(board_ref)
        if not board:
            self.caller.msg(f"No board found with the name or number '{board_ref}'.")
            return
        if not (controller.has_access(board_ref, self.caller.key) or 
                self.check_admin_access() or 
                self.check_builder_access()):
            self.caller.msg(f"You do not have access to view posts on the board '{board['name']}'.")
            return

        posts = board['posts']
        if post_number < 1 or post_number > len(posts):
            self.caller.msg(f"Invalid post number. Board '{board['name']}' has {len(posts)} posts.")
            return

        post = posts[post_number - 1]
        edit_info = f"(edited on {self.format_datetime(post['edited_at'])})" if post['edited_at'] else ""
        
        # Mark the post as read
        controller.mark_post_read(board_ref, post_number - 1, self.caller.key)
        
        self.caller.msg(f"{'='*120}")
        self.caller.msg(f"{'*' * 20} {board['name']} {'*' * 20}")
        self.caller.msg(f"Title: {post['title']}")
        self.caller.msg(f"Author: {post['author']}")
        self.caller.msg(f"Date: {self.format_datetime(post['created_at'])} {edit_info}")
        self.caller.msg(f"{'-'*120}")
        self.caller.msg(f"{post['content']}")
        self.caller.msg(f"{'='*120}")

    def do_viewas(self):
        """View a board as if you were another player.
        
        This command allows admins to view a board from the perspective of another player,
        which is useful for verifying permissions and troubleshooting access issues.
        
        Usage:
            +bbs/viewas <board> = <player>
            
        Example:
            +bbs/viewas announcements = JohnDoe
        """
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/viewas <board> = <player>")
            return
            
        board_ref, player_name = [arg.strip() for arg in self.args.split("=", 1)]
        
        # Find the player
        from evennia.utils import search
        players = search.search_object_by_keyclass(player_name, "typeclasses.characters.Character")
        
        if not players:
            self.caller.msg(f"No player found with the name '{player_name}'.")
            return
            
        target_player = players[0]
        
        # Get the board
        controller = get_or_create_bbs_controller()
        board = controller.get_board(board_ref)
        if not board:
            self.caller.msg(f"No board found with the name or number '{board_ref}'.")
            return
            
        # Check if the target player has access to the board
        has_access = controller.has_access(board_ref, target_player.key)
        has_write = controller.has_write_access(board_ref, target_player.key)
        
        # Display access information
        self.caller.msg(f"{'='*120}")
        self.caller.msg(f"Viewing board '{board['name']}' (#{board['id']}) as {target_player.key}")
        self.caller.msg(f"{'-'*120}")
        self.caller.msg(f"Access: {'|gYes|n' if has_access else '|rNo|n'}")
        self.caller.msg(f"Write Access: {'|gYes|n' if has_write else '|rNo|n'}")
        
        # Check roster access if applicable
        roster_names = board.get('roster_names', [])
        if roster_names:
            self.caller.msg(f"Roster Restrictions: {', '.join(roster_names)}")
            roster_access = False
            for roster_name in roster_names:
                try:
                    roster = Roster.objects.get(name=roster_name)
                    if roster.is_member(target_player):
                        roster_access = True
                        self.caller.msg(f"|gPlayer is a member of roster: {roster_name}|n")
                    else:
                        self.caller.msg(f"|rPlayer is NOT a member of roster: {roster_name}|n")
                except Roster.DoesNotExist:
                    self.caller.msg(f"|yWARNING: Roster '{roster_name}' no longer exists!|n")
            
            if not roster_access and roster_names:
                self.caller.msg("|rPlayer is not a member of any required roster|n")
        
        # Check public/private status
        if not board.get('public', True):
            self.caller.msg("|yThis is a private board|n")
        
        # Check read-only status
        if not has_write and has_access:
            self.caller.msg("|yThis board is read-only for this player|n")
            
        self.caller.msg(f"{'-'*120}")
        
        # If the player has access, show the board content
        if has_access:
            self.caller.msg("Board content as seen by this player:")
            self.list_posts_as_player(controller, board_ref, target_player)
        else:
            self.caller.msg("|rThis player cannot see this board's content|n")
            
        self.caller.msg(f"{'='*120}")
        
    def list_posts_as_player(self, controller, board_ref, target_player):
        """List all posts in the specified board as if viewed by the target player."""
        board = controller.get_board(board_ref)
        if not board:
            return

        posts = board['posts']
        pinned_posts = [post for post in posts if post.get('pinned', False)]
        unpinned_posts = [post for post in posts if not post.get('pinned', False)]

        # Table Header
        output = []
        output.append(f"{'*' * 20} {board['name']} {'*' * 20}")
        
        # Add board access information
        if not board.get('public', True):
            output.append("|rThis is a private board|n")
        elif board.get('roster_names'):
            output.append("|yThis board is restricted to specific rosters|n")

        output.append("{:<5} {:<1} {:<40} {:<20} {:<15}".format("ID", "", "Message", "Posted", "By"))
        output.append("-" * 120)

        # List pinned posts first with correct IDs
        for i, post in enumerate(pinned_posts):
            post_id = posts.index(post) + 1
            formatted_time = self.format_datetime(post['created_at'], target_player)
            is_unread = controller.is_post_unread(board['id'], post_id - 1, target_player.key)
            unread_flag = "|rU|n" if is_unread else " "
            output.append(f"{board['id']}/{post_id:<5} {unread_flag:<1} [Pinned] {post['title']:<40} {formatted_time:<20} {post['author']}")

        # List unpinned posts with correct IDs
        for post in unpinned_posts:
            post_id = posts.index(post) + 1
            formatted_time = self.format_datetime(post['created_at'], target_player)
            is_unread = controller.is_post_unread(board['id'], post_id - 1, target_player.key)
            unread_flag = "|rU|n" if is_unread else " "
            output.append(f"{board['id']}/{post_id:<5} {unread_flag:<1} {post['title']:<40} {formatted_time:<20} {post['author']}")

        # Table Footer
        output.append("=" * 120)

        self.caller.msg("\n".join(output))

    def list_boards_as_player(self, controller, target_player):
        """List all available boards as if viewed by the target player."""
        boards = controller.db.boards
        if not boards:
            self.caller.msg("No boards available.")
            return

        # Table Header
        output = []
        output.append("=" * 120)
        output.append(f"Boards visible to {target_player.key}:")
        output.append("{:<5} {:<10} {:<40} {:<20} {:<15} {:<10}".format("ID", "Access", "Name", "Last Post", "# of messages", "Unread"))
        output.append("-" * 120)

        # Sort boards by ID and convert to list of tuples
        sorted_boards = sorted(boards.items(), key=lambda x: x[0])

        for board_id, board in sorted_boards:
            # Skip boards the character doesn't have access to
            if not controller.has_access(board_id, target_player.key):
                continue

            # Check if user has write access
            has_write = controller.has_write_access(board_id, target_player.key)
            read_only = "*" if not has_write else " "
            
            # Determine access type
            if board.get('roster_names'):
                access_type = "Roster"
            elif not board.get('public', True):  # Default to public if not specified
                access_type = "Private"
            else:
                access_type = "Public"
            
            # Get last post time, ensuring it's a date/time string
            last_post = "No posts"
            if board['posts']:
                last_post = max((post['created_at'] for post in board['posts']), default="No posts")
                if last_post != "No posts":
                    last_post = self.format_datetime(last_post, target_player)

            num_posts = len(board['posts'])
            
            # Get unread post count
            unread_posts = controller.get_unread_posts(board_id, target_player.key)
            unread_count = len(unread_posts)
            unread_display = str(unread_count) if unread_count > 0 else "-"

            output.append(f"{board_id:<5} {access_type:<10} {read_only} {board['name']:<40} {last_post:<20} {num_posts:<15} {unread_display:<10}")

        # Table Footer
        output.append("-" * 120)
        output.append("* = read only")
        output.append("=" * 120)

        self.caller.msg("\n".join(output))

    def do_scan_as_player(self, target_player):
        """Handle the scan switch - show unread posts on all accessible boards as if viewed by the target player."""
        controller = get_or_create_bbs_controller()
        boards = controller.db.boards
        if not boards:
            self.caller.msg("No boards available.")
            return

        # Count total unread posts
        total_unread = 0
        unread_boards = []

        # Sort boards by ID
        sorted_boards = sorted(boards.items(), key=lambda x: x[0])

        for board_id, board in sorted_boards:
            if not controller.has_access(board_id, target_player.key):
                continue

            unread_posts = controller.get_unread_posts(board_id, target_player.key)
            if not unread_posts:
                continue

            total_unread += len(unread_posts)
            unread_boards.append((board['name'], len(unread_posts)))

        # If this is a login notification (no explicit command), show concise output
        if not hasattr(self, 'session') or not self.session:
            if total_unread > 0:
                board_summary = ", ".join(f"{name}: {count}" for name, count in unread_boards)
                self.caller.msg(f"|w{target_player.key} has {total_unread} unread post{'s' if total_unread != 1 else ''} "
                              f"on the bulletin board ({board_summary}).|n")
            return

        # Otherwise show detailed scan output
        # Table Header
        output = []
        output.append("=" * 120)
        output.append(f"Unread Postings on the Global Bulletin Board (as {target_player.key})")
        output.append("-" * 120)

        for board_id, board in sorted_boards:
            if not controller.has_access(board_id, target_player.key):
                continue

            unread_posts = controller.get_unread_posts(board_id, target_player.key)
            if not unread_posts:
                continue

            # Format unread posts numbers
            unread_str = ", ".join(str(x) for x in unread_posts)
            
            # Get board access type indicators
            access_type = ""
            if board.get('roster_names'):  # If board has roster restrictions
                access_type = "*"  # restricted
            elif not controller.has_write_access(board_id, target_player.key):
                access_type = "-"  # read only

            # Format board name with access type
            board_name = f"{board['name']} {access_type}"
            
            output.append(f"{board_name} (#{board_id}): {len(unread_posts)} unread ({unread_str})")

        # Add footer with capacity information
        output.append("-" * 120)
        if total_unread > 0:
            total_posts = sum(len(b['posts']) for b in boards.values())
            if total_posts > 0:  # Avoid division by zero
                capacity = (total_unread / total_posts) * 100
                output.append(f"Total unread posts: {total_unread} ({capacity:.1f}% of all posts)")
        output.append("=" * 120)

        self.caller.msg("\n".join(output))

    def do_readall_as_player(self, target_player):
        """Mark all posts in a board as read for the target player."""
        if not self.args:
            self.caller.msg("Usage: +bbs/readall <board>")
            return
            
        board_ref = self.args.strip()
        controller = get_or_create_bbs_controller()
        board = controller.get_board(board_ref)
        if not board:
            self.caller.msg(f"No board found with the name or number '{board_ref}'.")
            return
            
        if not controller.has_access(board_ref, target_player.key):
            self.caller.msg(f"{target_player.key} does not have access to view posts on the board '{board['name']}'.")
            return
            
        # Mark all posts as read
        for i in range(len(board['posts'])):
            controller.mark_post_read(board_ref, i, target_player.key)
            
        self.caller.msg(f"All posts in board '{board['name']}' have been marked as read for {target_player.key}.")

    def read_post_as_player(self, controller, board_ref, post_number, target_player):
        """Read a specific post in a board as if viewed by the target player."""
        board = controller.get_board(board_ref)
        if not board:
            self.caller.msg(f"No board found with the name or number '{board_ref}'.")
            return
        if not controller.has_access(board_ref, target_player.key):
            self.caller.msg(f"{target_player.key} does not have access to view posts on the board '{board['name']}'.")
            return

        posts = board['posts']
        if post_number < 1 or post_number > len(posts):
            self.caller.msg(f"Invalid post number. Board '{board['name']}' has {len(posts)} posts.")
            return

        post = posts[post_number - 1]
        edit_info = f"(edited on {self.format_datetime(post['edited_at'], target_player)})" if post['edited_at'] else ""
        
        # Mark the post as read
        controller.mark_post_read(board_ref, post_number - 1, target_player.key)
        
        self.caller.msg(f"{'='*120}")
        self.caller.msg(f"{'*' * 20} {board['name']} {'*' * 20} (as {target_player.key})")
        self.caller.msg(f"Title: {post['title']}")
        self.caller.msg(f"Author: {post['author']}")
        self.caller.msg(f"Date: {self.format_datetime(post['created_at'], target_player)} {edit_info}")
        self.caller.msg(f"{'-'*120}")
        self.caller.msg(f"{post['content']}")
        self.caller.msg(f"{'='*120}")