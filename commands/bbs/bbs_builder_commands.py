#commands/bbs/bbs_builder_commands.py


from evennia import default_cmds
from evennia import create_object
from typeclasses.bbs_controller import BBSController
from world.wod20th.models import Roster, RosterMember

class CmdCreateBoard(default_cmds.MuxCommand):
    """
    Create a new board.

    Usage:
      +bbs/create <name> = <description> / public | private [/roster=<roster_name1>,<roster_name2>...]
      
    Examples:
      +bbs/create Announcements = Game announcements / public
      +bbs/create Supernatural = Supernatural discussion / private /roster=Vampire,Werewolf
    """
    key = "+bbs/create"
    locks = "cmd:perm(Builder)"
    help_category = "Event & Bulletin Board"

    def func(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/create <name> = <description> / public | private [/roster=<roster_name1>,<roster_name2>...]")
            return

        # Split into name_desc and privacy/roster parts
        name_desc, remainder = self.args.split("=", 1)
        parts = remainder.split("/")
        
        if len(parts) < 2:
            self.caller.msg("Usage: +bbs/create <name> = <description> / public | private [/roster=<roster_name1>,<roster_name2>...]")
            return
            
        description = parts[0].strip()
        privacy = parts[1].strip().lower()
        public = privacy == "public"
        
        # Check for roster specification
        roster_names = []
        if len(parts) > 2:
            for part in parts[2:]:
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

        # Ensure BBSController exists
        try:
            controller = BBSController.objects.get(db_key="BBSController")
        except BBSController.DoesNotExist:
            controller = create_object(BBSController, key="BBSController")
            controller.db.boards = {}  # Initialize with an empty boards dictionary if needed
            self.caller.msg("BBSController created.")

        # Create the board
        controller.create_board(name, description, public, roster_names=roster_names)
        msg = f"Board '{name}' created as {'public' if public else 'private'}"
        if roster_names:
            msg += f" (restricted to rosters: {', '.join(roster_names)})"
        msg += f" with description: {description}"
        self.caller.msg(msg)

class CmdDeleteBoard(default_cmds.MuxCommand):
    """
    Delete a board and all its posts.

    Usage:
      +bbs/deleteboard <board_name>
    """
    key = "+bbs/deleteboard"
    locks = "cmd:perm(Builder)"
    help_category = "Event & Bulletin Board"

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
    help_category = "Event & Bulletin Board"

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
    help_category = "Event & Bulletin Board"

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
            
        output = []
        
        # Show roster restrictions if any
        roster_names = board.get('roster_names', [])
        if roster_names:
            output.append(f"Board '{board_name}' is restricted to members of the following rosters:")
            
            # Get current roster members for each roster
            for roster_name in roster_names:
                output.append(f"\nRoster: {roster_name}")
                try:
                    roster = Roster.objects.get(name=roster_name)
                    members = roster.get_members()
                    if members:
                        output.append("Current roster members with access:")
                        for member in members:
                            output.append(f"- {member.character.db_key}")
                    else:
                        output.append("No approved members in this roster.")
                except Roster.DoesNotExist:
                    output.append(f"Warning: Roster '{roster_name}' no longer exists!")
        
        # Show individual access list
        if board['public']:
            output.append(f"\nBoard '{board_name}' is public; individual access list is not applicable.")
        else:
            access_list = board.get('access_list', {})
            if not access_list:
                output.append(f"\nNo users have individual access to the private board '{board_name}'.")
            else:
                output.append("\nUsers with individual access:")
                for user, access_type in access_list.items():
                    output.append(f"- {user} ({access_type})")
        
        self.caller.msg("\n".join(output))

class CmdLockBoard(default_cmds.MuxCommand):
    """
    Lock a board to prevent new posts.

    Usage:
      +bbs/lockboard <board_name>
    """
    key = "+bbs/lockboard"
    locks = "cmd:perm(Builder)"
    help_category = "Event & Bulletin Board"

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
    help_category = "Event & Bulletin Board"

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
    help_category = "Event & Bulletin Board"

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

    Fields:
      description - Change the board's description
      public - Set to true/false to change board visibility

    Example:
      +bbs/editboard Announcements = description, A board for official announcements.
      +bbs/editboard Announcements = public, true
    """
    key = "+bbs/editboard"
    locks = "cmd:perm(Builder)"
    help_category = "Event & Bulletin Board"

    def func(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/editboard <board_name> = <field>, <new_value>")
            return
        board_name, updates = [arg.strip() for arg in self.args.split("=", 1)]
        field, new_value = [arg.strip() for arg in updates.split(",", 1)]
        field = field.lower()

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
            msg = f"Description set to '{new_value}'"
        elif field == "public":
            board['public'] = new_value.lower() in ["true", "yes", "1"]
            msg = f"Public status set to {board['public']}"
        else:
            self.caller.msg(f"Invalid field '{field}'. You can edit 'description' or 'public'.")
            return

        controller.save_board(board_name, board)
        self.caller.msg(f"Board '{board_name}' has been updated. {msg}.")

class CmdEditBoardRosters(default_cmds.MuxCommand):
    """
    Edit the roster restrictions of a board.

    Usage:
      +bbs/editboard/rosters <board_name> = <roster_name1> [,<roster_name2>...]
      +bbs/editboard/rosters <board_name> =    # Clear all roster restrictions

    Examples:
      +bbs/editboard/rosters Supernatural = Vampire,Werewolf,Mage
      +bbs/editboard/rosters Supernatural =    # Remove all roster restrictions
    """
    key = "+bbs/editboard/rosters"
    locks = "cmd:perm(Builder)"
    help_category = "Event & Bulletin Board"

    def func(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/editboard/rosters <board_name> = <roster_name1> [,<roster_name2>...]")
            return

        board_name, roster_list = [arg.strip() for arg in self.args.split("=", 1)]
        
        controller = BBSController.objects.get(db_key="BBSController")
        if not controller:
            self.caller.msg("BBSController not found.")
            return

        board = controller.get_board(board_name)
        if not board:
            self.caller.msg(f"No board found with the name '{board_name}'.")
            return

        # Handle empty value to clear roster restrictions
        if not roster_list:
            board['roster_names'] = []
            controller.save_board(board_name, board)
            self.caller.msg(f"Cleared all roster restrictions from board '{board_name}'.")
            return

        # Process roster list
        roster_names = [r.strip() for r in roster_list.split(",") if r.strip()]
        
        # Verify all rosters exist
        for roster_name in roster_names:
            try:
                Roster.objects.get(name=roster_name)
            except Roster.DoesNotExist:
                self.caller.msg(f"Error: Roster '{roster_name}' does not exist.")
                return

        # Update board with new roster list
        board['roster_names'] = roster_names
        controller.save_board(board_name, board)
        self.caller.msg(f"Updated roster restrictions for board '{board_name}' to: {', '.join(roster_names)}")

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
    help_category = "Event & Bulletin Board"

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

class CmdAddRoster(default_cmds.MuxCommand):
    """
    Add a roster restriction to a board.

    Usage:
      +bbs/addroster <board_name> = <roster_name>
    """
    key = "+bbs/addroster"
    locks = "cmd:perm(Builder)"
    help_category = "Event & Bulletin Board"

    def func(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/addroster <board_name> = <roster_name>")
            return
            
        board_name, roster_name = [arg.strip() for arg in self.args.split("=", 1)]
        
        controller = BBSController.objects.get(db_key="BBSController")
        if not controller:
            self.caller.msg("BBSController not found.")
            return
            
        result = controller.add_roster_to_board(board_name, roster_name)
        self.caller.msg(result)

class CmdRemoveRoster(default_cmds.MuxCommand):
    """
    Remove a roster restriction from a board.

    Usage:
      +bbs/removeroster <board_name> = <roster_name>
    """
    key = "+bbs/removeroster"
    locks = "cmd:perm(Builder)"
    help_category = "Event & Bulletin Board"

    def func(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +bbs/removeroster <board_name> = <roster_name>")
            return
            
        board_name, roster_name = [arg.strip() for arg in self.args.split("=", 1)]
        
        controller = BBSController.objects.get(db_key="BBSController")
        if not controller:
            self.caller.msg("BBSController not found.")
            return
            
        result = controller.remove_roster_from_board(board_name, roster_name)
        self.caller.msg(result)

class CmdListRosters(default_cmds.MuxCommand):
    """
    List all rosters associated with a board.

    Usage:
      +bbs/listrosters <board_name>
    """
    key = "+bbs/listrosters"
    locks = "cmd:perm(Builder)"
    help_category = "Event & Bulletin Board"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: +bbs/listrosters <board_name>")
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
            
        roster_names = controller.get_board_rosters(board_name)
        if not roster_names:
            self.caller.msg(f"Board '{board_name}' has no roster restrictions.")
        else:
            self.caller.msg(f"Board '{board_name}' is restricted to the following rosters:")
            for roster_name in roster_names:
                try:
                    roster = Roster.objects.get(name=roster_name)
                    member_count = roster.get_members().count()
                    self.caller.msg(f"- {roster_name} ({member_count} approved members)")
                except Roster.DoesNotExist:
                    self.caller.msg(f"- {roster_name} (WARNING: Roster no longer exists!)")