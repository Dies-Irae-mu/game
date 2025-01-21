from evennia import default_cmds
from evennia.accounts.accounts import AccountDB
from evennia.utils.ansi import ANSIString
from evennia.utils import ansi
from evennia import Command
from evennia.utils import search

class CmdStaff(default_cmds.MuxCommand):
    """
    List and manage staff members.

    Usage:
      +staff
      +staff/position <account> = <position>
      +staff/add <account>
      +staff/remove <account>

    Switches:
      /position - Set the position of a staff member
      /add      - Add an account to staff
      /remove   - Remove an account from staff

    Examples:
      +staff
      +staff/position Wizard = Head Admin
      +staff/add NewStaff
      +staff/remove FormerStaff
    """

    key = "+staff"
    aliases = ["staff"]
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        if not self.args and not self.switches:
            # Display staff list
            self.list_staff()
        elif "position" in self.switches:
            # Set staff position (admin only)
            if self.caller.check_permstring("Admin"):
                self.set_position()
            else:
                self.caller.msg("You don't have permission to set staff positions.")
        elif "add" in self.switches:
            # Add staff (admin only)
            if self.caller.check_permstring("Admin"):
                self.add_staff()
            else:
                self.caller.msg("You don't have permission to add staff.")
        elif "remove" in self.switches:
            # Remove staff (admin only)
            if self.caller.check_permstring("Admin"):
                self.remove_staff()
            else:
                self.caller.msg("You don't have permission to remove staff.")
        else:
            self.caller.msg("Invalid switch. See help +staff for usage.")

    def list_staff(self):
        all_accounts = AccountDB.objects.all()
        staff = []
        
        for account in all_accounts:
            character = account.db._playable_characters[0] if account.db._playable_characters else None
            
            # Check if either account or character is staff
            is_staff = (account.tags.get("staff", category="role") or 
                       (character and character.tags.get("staff", category="role")))
            
            if is_staff:
                staff.append((account, character))

        string = self.format_header("Dies Irae Staff", width=78)
        string += self.format_columns(["Name", "Position", "Status"], color="|w")
        string += "|r=|n" * 78 + "\n"

        if staff:
            for account, character in staff:
                # Check for gradient name in persistent attributes
                if character:
                    gradient_name = character.db.gradient_name
                    if gradient_name:
                        name = ANSIString(gradient_name)
                    else:
                        name = character.key.strip()
                else:
                    name = account.key.strip()

                position = self.get_position(account, character)
                status = "|gOnline|n" if account.is_connected else "|rOffline|n"
                string += self.format_staff_row(name, position, status)
        else:
            string += "No staff members found.\n"

        string += self.format_footer(width=78)
        self.caller.msg(string)

    def format_header(self, text, width=78):
        return f"|r{'=' * 5}< |w{text}|r >{'=' * (width - len(text) - 9)}|n\n"

    def format_footer(self, width=78):
        return f"|r{'=' * width}|n\n"

    def format_columns(self, columns, color="|w"):
        return "".join([f"{color}{col:<25}|n" for col in columns]) + "\n"

    def format_staff_row(self, name, position, status):
        name_col = ANSIString(name).ljust(25)
        position_col = ANSIString(position).ljust(25)
        status_col = ANSIString(status)
        return f"{name_col}{position_col}{status_col}\n"

    def get_position(self, account, character):
        # First, check for custom position on the character
        if character and character.db.position:
            return character.db.position
        
        # Then, check for custom position on the account
        if account.db.position:
            return account.db.position
        
        # Default position for staff
        return "Staff"

    def set_position(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +staff/position <account> = <position>")
            return
        
        account_name, position = self.args.split("=", 1)
        account_name = account_name.strip()
        position = position.strip()

        account = self.caller.search(account_name, global_search=True)
        if not account:
            return

        account.db.position = position
        self.caller.msg(f"Set {account.key}'s position to: {position}")
        self.list_staff()  # Show updated staff list

    def add_staff(self):
        if not self.args:
            self.caller.msg("Usage: +staff/add <account>")
            return

        account = self.caller.search(self.args, global_search=True)
        if not account:
            return

        # Check both account and character for staff tag
        char = account.db._playable_characters[0] if account.db._playable_characters else None
        is_staff = (account.tags.get("staff", category="role") or 
                   (char and char.tags.get("staff", category="role")))
        
        if is_staff:
            self.caller.msg(f"{account.key} is already staff.")
        else:
            # Add tag to both account and character if it exists
            account.tags.add("staff", category="role")
            if account.db._playable_characters:
                char = account.db._playable_characters[0]
                char.tags.add("staff", category="role")
            self.caller.msg(f"Successfully added {account.key} as staff.")
        
        self.list_staff()

    def remove_staff(self):
        if not self.args:
            self.caller.msg("Usage: +staff/remove <account>")
            return

        account = self.caller.search(self.args, global_search=True)
        if not account:
            return

        # Check both account and character for staff tag
        char = account.db._playable_characters[0] if account.db._playable_characters else None
        is_staff = (account.tags.get("staff", category="role") or 
                   (char and char.tags.get("staff", category="role")))

        if not is_staff:
            self.caller.msg(f"{account.key} is not staff.")
        else:
            # Remove tag from both account and character
            account.tags.remove("staff", category="role")
            if char:
                char.tags.remove("staff", category="role")
            self.caller.msg(f"Removed {account.key} from staff.")
        self.list_staff()


class CmdPST(default_cmds.MuxCommand):
    """
    List and manage player storytellers.

    Usage:
      +pst
      +pst/position <account> = <position>
      +pst/add <account>
      +pst/remove <account>
      +pst/claim <account>     - Claim a PST position
      +pst/unclaim <account>   - Unclaim a PST position

    Switches:
      /position - Set the position of a player storyteller
      /add      - Add an account as player storyteller
      /remove   - Remove an account from player storytellers
      /claim    - Claim a PST position
      /unclaim  - Unclaim a PST position

    Examples:
      +pst
      +pst/position PST = Garou PST
      +pst/add NewPST
      +pst/remove FormerPST
      +pst/claim NewPST
      +pst/unclaim FormerPST
    """

    key = "+pst"
    aliases = ["pst"]
    locks = "cmd:all()"
    help_category = "General"

    def format_header(self, text, width=78):
        return f"|r{'=' * 5}< |w{text}|r >{'=' * (width - len(text) - 9)}|n\n"

    def format_footer(self, width=78):
        return f"|r{'=' * width}|n\n"

    def format_columns(self, columns, color="|w"):
        return "".join([f"{color}{col:<20}|n" for col in columns]) + "\n"

    def format_pst_row(self, name, position, status, claimed):
        name_col = ANSIString(name).ljust(15)
        position_col = ANSIString(position).ljust(25)
        status_col = ANSIString(status).ljust(25)
        claimed_col = ANSIString(claimed)
        return f"{name_col}{position_col}{status_col}{claimed_col}\n"

    def func(self):
        if not self.args and not self.switches:
            # Display PST list
            self.list_pst()
        elif "position" in self.switches:
            # Set PST position (admin only)
            if self.caller.check_permstring("Admin"):
                self.set_position()
            else:
                self.caller.msg("You don't have permission to set PST positions.")
        elif "add" in self.switches:
            # Add PST (admin only)
            if self.caller.check_permstring("Admin"):
                self.add_pst()
            else:
                self.caller.msg("You don't have permission to add PSTs.")
        elif "remove" in self.switches:
            # Remove PST (admin only)
            if self.caller.check_permstring("Admin"):
                self.remove_pst()
            else:
                self.caller.msg("You don't have permission to remove PSTs.")
        elif "claim" in self.switches:
            # Claim PST position (admin only)
            if self.caller.check_permstring("Admin"):
                self.claim_pst()
            else:
                self.caller.msg("You don't have permission to claim PST positions.")
        elif "unclaim" in self.switches:
            # Unclaim PST position (admin only)
            if self.caller.check_permstring("Admin"):
                self.unclaim_pst()
            else:
                self.caller.msg("You don't have permission to unclaim PST positions.")
        else:
            self.caller.msg("Invalid switch. See help +pst for usage.")

    def list_pst(self):
        player_storytellers = []
        
        # Check all accounts first
        for account in AccountDB.objects.all():
            character = account.db._playable_characters[0] if account.db._playable_characters else None
            
            # Check if either account or character is PST
            is_pst = (account.tags.get("pst", category="role") or 
                     (character and character.tags.get("pst", category="role")))
            
            if is_pst:
                player_storytellers.append((account, character))

        # Now check for characters that might be PSTs without accounts (roster characters)
        from evennia.objects.models import ObjectDB
        for obj in ObjectDB.objects.filter(db_typeclass_path__contains='characters'):
            if obj.tags.get("pst", category="role"):
                # Only add if not already in the list
                if not any(pst for pst in player_storytellers if pst[1] == obj):
                    player_storytellers.append((None, obj))

        string = self.format_header("Dies Irae Player Storytellers", width=78)
        string += self.format_columns(["Name", "Position", "Status", "Claimed"], color="|w")
        string += "|r=|n" * 78 + "\n"

        if player_storytellers:
            for account, character in player_storytellers:
                # Get name (prefer character's name)
                if character:
                    gradient_name = character.db.gradient_name
                    if gradient_name:
                        name = ANSIString(gradient_name)
                    else:
                        name = character.key.strip()
                else:
                    name = account.key.strip()

                # Get position
                position = self.get_position(account, character)
                
                # Get status - if no account, character is always "Offline"
                if account:
                    status = "|gOnline|n" if account.is_connected else "|rOffline|n"
                else:
                    status = "|rOffline|n"
                
                claimed = "|gYes|n" if self.is_claimed(account, character) else "|rNo|n"
                string += self.format_pst_row(name, position, status, claimed)
        else:
            string += "No player storytellers found.\n"

        string += self.format_footer(width=78)
        self.caller.msg(string)

    def is_claimed(self, account, character):
        # Check both account and character for claimed status
        return ((account and account.tags.get("claimed_pst", category="role")) or 
                (character and character.tags.get("claimed_pst", category="role")))

    def claim_pst(self):
        if not self.args:
            self.caller.msg("Usage: +pst/claim <account>")
            return

        account = self.caller.search(self.args, global_search=True)
        if not account:
            return

        # Check if they're a PST first
        char = account.db._playable_characters[0] if account.db._playable_characters else None
        is_pst = (account.tags.get("pst", category="role") or 
                 (char and char.tags.get("pst", category="role")))

        if not is_pst:
            self.caller.msg(f"{account.key} is not a player storyteller.")
            return

        # Check if already claimed
        if self.is_claimed(account, char):
            self.caller.msg(f"{account.key}'s PST position is already claimed.")
            return

        # Add claimed tag to both account and character
        account.tags.add("claimed_pst", category="role")
        if char:
            char.tags.add("claimed_pst", category="role")
        self.caller.msg(f"Claimed {account.key}'s PST position.")
        self.list_pst()

    def unclaim_pst(self):
        if not self.args:
            self.caller.msg("Usage: +pst/unclaim <account>")
            return

        account = self.caller.search(self.args, global_search=True)
        if not account:
            return

        # Check if they're a PST first
        char = account.db._playable_characters[0] if account.db._playable_characters else None
        is_pst = (account.tags.get("pst", category="role") or 
                 (char and char.tags.get("pst", category="role")))

        if not is_pst:
            self.caller.msg(f"{account.key} is not a player storyteller.")
            return

        # Check if actually claimed
        if not self.is_claimed(account, char):
            self.caller.msg(f"{account.key}'s PST position is not claimed.")
            return

        # Remove claimed tag from both account and character
        account.tags.remove("claimed_pst", category="role")
        if char:
            char.tags.remove("claimed_pst", category="role")
        self.caller.msg(f"Unclaimed {account.key}'s PST position.")
        self.list_pst()

    def get_position(self, account, character):
        # First, check for custom position on the character
        if character and character.db.position:
            return character.db.position
        
        # Then, check for custom position on the account
        if account and account.db.position:
            return account.db.position
        
        # Default position for PSTs
        return "Player Storyteller"

    def set_position(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +pst/position <account> = <position>")
            return
        
        account_name, position = self.args.split("=", 1)
        account_name = account_name.strip()
        position = position.strip()

        account = self.caller.search(account_name, global_search=True)
        if not account:
            return

        account.db.position = position
        self.caller.msg(f"Set {account.key}'s position to: {position}")
        self.list_pst()

    def add_pst(self):
        if not self.args:
            self.caller.msg("Usage: +pst/add <account/character>")
            return

        # Try to find either an account or character
        target = self.caller.search(self.args, global_search=True)
        if not target:
            return

        # Determine if we found a character or account
        if hasattr(target, 'character_type'):  # It's a character
            char = target
            account = char.account
        else:  # It's an account
            account = target
            char = account.db._playable_characters[0] if account.db._playable_characters else None

        # Check if either is already a PST
        is_pst = ((account and account.tags.get("pst", category="role")) or 
                 (char and char.tags.get("pst", category="role")))

        if is_pst:
            self.caller.msg(f"{target.key} is already a player storyteller.")
        else:
            # Add PST tag
            if account:
                account.tags.add("pst", category="role")
            if char:
                char.tags.add("pst", category="role")
                # Set default position if none exists
                if not (char.db.position or (account and account.db.position)):
                    if account:
                        account.db.position = "Player Storyteller"
                    else:
                        char.db.position = "Player Storyteller"
            
            self.caller.msg(f"Added {target.key} as a player storyteller.")
        self.list_pst()

    def remove_pst(self):
        if not self.args:
            self.caller.msg("Usage: +pst/remove <account>")
            return

        account = self.caller.search(self.args, global_search=True)
        if not account:
            return

        # Check both account and character for PST tag
        char = account.db._playable_characters[0] if account.db._playable_characters else None
        is_pst = (account.tags.get("pst", category="role") or 
                 (char and char.tags.get("pst", category="role")))

        if not is_pst:
            self.caller.msg(f"{account.key} is not a player storyteller.")
        else:
            # Remove tag from both account and character
            account.tags.remove("pst", category="role")
            if char:
                char.tags.remove("pst", category="role")
            self.caller.msg(f"Removed {account.key} from player storytellers.")
        self.list_pst()



