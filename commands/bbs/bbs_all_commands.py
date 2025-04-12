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
            elif switch == "scan":
                self.do_scan()
            
            # Admin/Builder commands
            elif switch in ["create", "editboard", "editboard/rosters", "addroster", "removeroster", "listrosters", "lock", "pin", "unpin", "deleteboard", "readonly"]:
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
        output.append("-" * 78)
        output.append("Unread Postings on the Global Bulletin Board")
        output.append("-" * 78)

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
            if not board['public']:
                access_type = "*"  # restricted
            elif not controller.has_write_access(board_id, self.caller.key):
                if board['public']:
                    access_type = "-"  # read only
                else:
                    access_type = "(-)"  # read only but can write

            # Format board name with access type
            board_name = f"{board['name']} {access_type}"
            
            output.append(f"{board_name} (#{board_id}): {len(unread_posts)} unread ({unread_str})")

        # Add footer with capacity information
        output.append("-" * 78)
        if total_unread > 0:
            capacity = (total_unread / sum(len(b['posts']) for b in boards.values())) * 100

        self.caller.msg("\n".join(output))

    def list_boards(self, controller):
        """List all available boards."""
        boards = controller.db.boards
        if not boards:
            self.caller.msg("No boards have been created yet.")
            return

        # Get unread counts for all boards
        unread_counts = {}
        for board_id in boards:
            unread_posts = controller.get_unread_posts(board_id, self.caller.key)
            unread_counts[board_id] = len(unread_posts) if unread_posts else 0

        # Sort boards by ID
        sorted_boards = sorted(boards.items(), key=lambda x: x[0])
        
        table = self.styled_table(
            "|wID|n",
            "|wU|n",  # Unread column
            "|wName|n",
            "|wDescription|n",
            "|wPosts|n"
        )
        
        for board_id, board in sorted_boards:
            if not controller.has_access(board_id, self.caller.key):
                continue
                
            # Format board name with read-only and roster indicators
            name = board['name']
            if board.get('read_only', False):
                name = "* " + name
            if board.get('roster_names', []):
                name = name + "*"
                
            # Get unread count for this board
            unread = unread_counts.get(board_id, 0)
            unread_display = f"|r{unread}|n" if unread > 0 else "-"
                
            table.add_row(
                str(board_id),
                unread_display,
                name,
                board.get('description', ''),
                str(len(board['posts']))
            )
            
        self.caller.msg(str(table))
        
        # Show legend if needed
        has_readonly = any(board.get('read_only', False) for board in boards.values())
        has_roster = any(board.get('roster_names', []) for board in boards.values())
        
        if has_readonly or has_roster:
            legend = []
            if has_readonly:
                legend.append("* before name = Read Only")
            if has_roster:
                legend.append("* after name = Roster Restricted")
            self.caller.msg("\n" + ", ".join(legend))

    def list_posts(self, controller, board_ref):
        """List all posts in a board."""
        board = controller.get_board(board_ref)
        if not board:
            self.caller.msg(f"No board found with the name or number '{board_ref}'.")
            return
            
        if not controller.has_access(board['id'], self.caller.key):
            self.caller.msg("You don't have permission to read this board.")
            return
            
        posts = board['posts']
        if not posts:
            self.caller.msg(f"No posts on board '{board['name']}'.")
            return
            
        # Sort posts with pinned posts first, then by date
        sorted_posts = sorted(enumerate(posts), key=lambda x: (not x[1].get('pinned', False), x[1]['created_at']))
            
        table = self.styled_table(
            "|w#|n",
            "|wU|n",  # Unread column
            "|wTitle|n",
            "|wAuthor|n",
            "|wDate|n"
        )
        
        for post_index, post in sorted_posts:
            # Check if post is unread
            is_unread = controller.is_post_unread(board['id'], post_index, self.caller.key)
            unread_display = "|rU|n" if is_unread else "-"
            
            # Format title with pin indicator
            title = post['title']
            if post.get('pinned', False):
                title = "^" + title
                
            # Format date in user's timezone
            date = self.format_datetime(post['created_at'])
                
            table.add_row(
                str(post_index + 1),
                unread_display,
                title,
                post['author'],
                date
            )
            
        self.caller.msg(str(table))
        
        # Show legend if needed
        has_pinned = any(post.get('pinned', False) for post in posts)
        has_unread = any(controller.is_post_unread(board['id'], i, self.caller.key) for i, _ in enumerate(posts))
        
        if has_pinned or has_unread:
            legend = []
            if has_pinned:
                legend.append("^ = Pinned Post")
            if has_unread:
                legend.append("U = Unread Post")
            self.caller.msg("\n" + ", ".join(legend))

    def read_post(self, controller, board_ref, post_number):
        """Read a specific post."""
        board = controller.get_board(board_ref)
        if not board:
            self.caller.msg(f"No board found with the name or number '{board_ref}'.")
            return
            
        if not controller.has_access(board['id'], self.caller.key):
            self.caller.msg("You don't have permission to read this board.")
            return
            
        try:
            post_index = post_number - 1  # Convert to 0-based index
            post = board['posts'][post_index]
        except (IndexError, ValueError):
            self.caller.msg(f"No post #{post_number} on board '{board['name']}'.")
            return
            
        # Mark the post as read
        controller.mark_post_read(board['id'], post_index, self.caller.key)
            
        # Format the post header
        header = f"|w{'=' * 78}|n\n"
        header += f"|wBoard:|n {board['name']} (#{board['id']})\n"
        header += f"|wPost:|n #{post_number}{' |w[Pinned]|n' if post.get('pinned', False) else ''}\n"
        header += f"|wTitle:|n {post['title']}\n"
        header += f"|wAuthor:|n {post['author']}\n"
        header += f"|wDate:|n {self.format_datetime(post['created_at'])}\n"
        if post.get('edited_at'):
            header += f"|wEdited:|n {self.format_datetime(post['edited_at'])}\n"
        header += f"|w{'-' * 78}|n\n"
        
        # Format the post content
        content = post['content']
        
        # Format the footer
        footer = f"\n|w{'=' * 78}|n"
        
        # Send the formatted post
        self.caller.msg(header + content + footer)