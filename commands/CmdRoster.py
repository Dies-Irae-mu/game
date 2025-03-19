"""
Roster Commands
"""
from django.conf import settings
from django.utils import timezone
from evennia import default_cmds
from evennia.utils import evtable
from evennia.utils.utils import time_format
from evennia.utils.search import search_object
from world.wod20th.models import Roster, RosterMember
from world.hangouts.models import HangoutDB
from evennia.utils.ansi import ANSIString
from utils.search_helpers import search_character
import time

def format_idle_time(sessions):
    """Format idle time for display."""
    if not sessions:
        return "OFF"
    
    # Get the most recent idle time from all sessions
    idle_times = []
    current_time = time.time()  # Get current Unix timestamp
    
    for session in sessions:
        if session.cmd_last_visible:
            # Calculate idle time in seconds using Unix timestamps
            idle_secs = current_time - session.cmd_last_visible
            idle_times.append(idle_secs)
    
    if not idle_times:
        return "ON"
        
    # Get the shortest idle time
    idle_secs = min(idle_times)
    idle_secs = int(idle_secs)  # Convert to int for display
    
    # Format the idle time with color coding
    if idle_secs < 60:  # Less than a minute
        time_str = f"{idle_secs}s"
    elif idle_secs < 3600:  # Less than an hour
        time_str = f"{idle_secs // 60}m"
    else:  # Hours
        time_str = f"{idle_secs // 3600}h"

    # Color code based on idle time intervals
    if idle_secs < 900:  # less than 15 minutes
        return ANSIString(f"|g{time_str}|n")  # green
    elif idle_secs < 1800:  # 15-30 minutes
        return ANSIString(f"|y{time_str}|n")  # yellow
    elif idle_secs < 2700:  # 30-45 minutes
        return ANSIString(f"|r{time_str}|n")  # orange (using red)
    elif idle_secs < 3600:  # 45-60 minutes
        return ANSIString(f"|R{time_str}|n")  # bright red
    else:  # more than an hour
        return ANSIString(f"|x{time_str}|n")  # grey

class CmdRoster(default_cmds.MuxCommand):
    """
    View and manage character rosters.

    Usage:
        +roster                    - See what rosters you belong to
        +roster <#>               - See the list of players in a roster
        +roster/who <#>           - See the list of online players in a roster
        +roster/info <#>          - Show additional info about a roster
        +roster/list              - List all existing rosters
        
    Staff/Admin/Manager commands:
        +roster/create <name>=<desc>   - Create a new roster
        +roster/delete <#>             - Delete a roster
        +roster/add <#>=<character>    - Add a character to a roster
        +roster/remove <#>=<character> - Remove a character from a roster
        +roster/approve <#>=<character> - Approve a character in a roster
        +roster/title <#>/<char>=<title> - Set character's title in roster
        +roster/website <#>=<url>      - Set roster's website
        +roster/desc <#>=<desc>        - Set roster's description
        +roster/sphere <#>=<sphere>    - Set roster's sphere (Mage/Shifter/etc)
        +roster/hangouts <#>=<id1,id2> - Set roster's associated hangouts
        +roster/manager <#>=<player>   - Add a player as manager of roster
        +roster/manager/remove <#>=<player> - Remove a player as manager
        +roster/admin <#>=<player>     - Add a player as admin of roster
        +roster/admin/remove <#>=<player> - Remove a player as admin

    Rosters are a way for Directors to manage groups of players. These can be
    faction-wide rosters, subgroup-rosters or even rosters cobbled together
    from various players cross-sphere.

    The /hangouts switch allows you to associate one or more hangouts with a roster.
    These hangouts will be displayed in the roster info and serve as the primary
    gathering places for the roster's members. Use comma-separated hangout IDs
    to specify multiple hangouts (e.g., +roster/hangouts 2=1,3,5).
    """

    key = "+roster"
    aliases = ["roster"]
    locks = "cmd:all()"
    help_category = "General"

    def get_roster_list(self):
        """Show list of rosters the character belongs to."""
        rosters = Roster.objects.filter(
            members__character=self.caller,
            members__approved=True
        ).distinct()

        if not rosters.exists():
            self.caller.msg("You don't belong to any rosters.")
            return

        # Format header
        title = " |yRosters|b "
        header = f"|b{title.center(82, '=')}|n"
        
        # Column headers
        col_headers = f"|y{'#':3s}|n |y{'Name/Description':60s}|n |y{'Members':10s}|n"
        separator = "|w-|n" * 78
        double_separator = "|b=|n" * 78
        
        # Format each roster row
        roster_rows = []
        for roster in rosters:
            member_count = roster.get_members().count()
            desc = roster.description.split('\n')[0][:50] + "..." if roster.description else ""
            
            # Format the name and description with dots
            name_desc = f"{roster.name}\n{desc}".ljust(70, '.')
            
            # Format the row with proper spacing
            roster_rows.append(f"{roster.id:3d} {name_desc} {member_count:3d}")

        # Join all components
        output = [
            "",  # Empty line before header
            header,
            double_separator,
            col_headers,
            double_separator,
            *roster_rows,  # Unpack all roster rows
            "",  # Empty line before footer
            "|b" + ("=" * 78) + "|n"  # Footer
        ]

        # Send the complete formatted output
        self.caller.msg("\n".join(output))

    def get_roster_members(self, roster_id, online_only=False):
        """Show members of a specific roster."""
        try:
            roster = Roster.objects.get(id=roster_id)
        except Roster.DoesNotExist:
            self.caller.msg(f"Roster #{roster_id} not found.")
            return

        # Check if caller has access
        if not (
            self.caller.check_permstring("Developer") or 
            self.caller.check_permstring("Admin") or 
            RosterMember.objects.filter(
                roster=roster,
                character=self.caller,
                approved=True
            ).exists()
        ):
            self.caller.msg("You don't have access to that roster.")
            return

        members = roster.get_online_members() if online_only else roster.get_members()
        
        if not members and not online_only:
            self.caller.msg("No members found in this roster.")
            return

        # Format header
        title = f" |yRoster {roster_id}: {roster.name} |b"
        header = f"|b{title.center(82, '-')}|n"
        
        # Column headers with fixed widths
        col_headers = f"|yName|n{' ' * 16}|yTitle|n{' ' * 40}|yIdle|n"
        separator = f"|b{'-' * 78}|n"
        
        # Format each member row
        member_rows = []
        for member in members:
            char = member.character
            sessions = char.sessions.all() if char else []
            idle_time = format_idle_time(sessions)
            
            # Format each column with fixed width
            name = char.name[:20]
            title = member.title[:45] if member.title else ""
            
            # Format the row with proper spacing for column alignment
            member_rows.append(f"{name.ljust(20)}{title.ljust(45)}{idle_time}")

        # Join all components
        output = [
            header,
            separator,
            col_headers,
            separator,
        ]
        
        # Add member rows if any exist
        if member_rows:
            output.extend(member_rows)
        elif online_only:
            output.append("No members are currently online.")

        # Add linked groups section if any exist
        from world.groups.models import Group
        linked_groups = Group.objects.filter(roster=roster).order_by('group_id')
        if linked_groups.exists():
            output.extend([
                "",  # Empty line before groups
                f"|b{' |yLinked Groups|b '.center(82, '-')}",
                f"|yID#|n  |yGroup Name|n{' ' * 28}|yMembers|n  |yLeader|n"
            ])
            
            # Add a divider of tildes for the linked groups section
            output.append(f"|b{'~' * 78}|n")
            
            for group in linked_groups:
                # Get member count
                member_count = group.groupmembership_set.count()
                # Get leader name
                leader_name = "None"
                if group.leader and hasattr(group.leader, 'db_object'):
                    leader_name = group.leader.db_object.name
                # Format group info
                name = group.name
                # Add the group entry with proper spacing
                output.append(f"{group.group_id:<3d} | {name.ljust(40)}{str(member_count).center(8)}{leader_name}")

        # Add website section if it exists
        if roster.website:
            output.extend([
                "",  # Empty line before notes
                " Notes ".center(78, "-"),
                f"Website\n{roster.website}"
            ])

        # Add hangouts section if any exist
        if roster.hangouts.exists():
            output.extend([
                "",  # Empty line before hangouts
                f"|b{' Hangouts '.center(78, '-')}|n",
                f"|yID#|n  |yHangout Name|n{' ' * 35}|yPlayers|n"
            ])
            for hangout in roster.hangouts.all():
                # Format hangout name and truncate if needed
                name = hangout.key[:47] + "..." if len(hangout.key) > 47 else hangout.key
                # Get player count for this hangout
                player_count = len(hangout.db.players) if hasattr(hangout.db, 'players') and hangout.db.players else 0
                output.append(f"{hangout.db.hangout_id:3d} | {name.ljust(47)} {player_count:>3d}")
                
                # Format description if it exists
                if hangout.db.description:
                    desc = hangout.db.description.split('\n')[0]  # Get first line
                    if len(desc) > 67:  # Account for "    | " prefix (5 chars)
                        desc = desc[:67] + "..."
                    output.append(f"    | {desc}")

        # Add footer
        output.append(f"|b{'-' * 78}|n")

        # Send the complete formatted output
        self.caller.msg("\n".join(output))

    def get_roster_info(self, roster_id):
        """Show detailed information about a roster."""
        try:
            roster = Roster.objects.get(id=roster_id)
        except Roster.DoesNotExist:
            self.caller.msg(f"Roster #{roster_id} not found.")
            return

        # Check if caller has access
        if not (
            self.caller.check_permstring("Developer") or 
            self.caller.check_permstring("Admin") or 
            RosterMember.objects.filter(
                roster=roster,
                character=self.caller,
                approved=True
            ).exists()
        ):
            self.caller.msg("You don't have access to that roster.")
            return

        title = f"|yRoster {roster_id}: {roster.name} Info|n|b"
        header = f"|b{title.center(84, '=')}|n"
        info = f"\nDescription:\n{roster.description}\n\n"
        
        # Add linked groups information
        from world.groups.models import Group
        linked_groups = Group.objects.filter(roster=roster).order_by('group_id')
        if linked_groups.exists():
            info += "|yLinked Groups:|n\n"
            for group in linked_groups:
                member_count = group.groupmembership_set.count()
                leader_name = "None"
                if group.leader and hasattr(group.leader, 'db_object'):
                    leader_name = group.leader.db_object.name
                info += f"- {group.name} (#{group.group_id}) - Members: {member_count}, Leader: {leader_name}\n"
            info += "\n"
            
        if roster.admins.exists():
            info += "|yAdministrators:|n\n"
            for admin in roster.admins.all():
                info += f"- {admin.username}\n"
            info += "\n"
            
        if roster.managers.exists():
            info += "|yManagers:|n\n"
            for manager in roster.managers.all():
                info += f"- {manager.username}\n"
            info += "\n"

        if roster.hangouts.exists():
            info += "|yHangouts:|n\n"
            for hangout in roster.hangouts.all():
                info += f"- {hangout.key} (#{hangout.db.hangout_id})"
                if hangout.db.description:
                    info += f"\n  {hangout.db.description}"
                info += "\n"

        footer = "|b" + ("=" * 78) + "|n"
        self.caller.msg(f"{header}\n{info}\n{footer}")

    def create_roster(self, name, desc=""):
        """Create a new roster."""
        if not self.caller.check_permstring("Builder") and not self.caller.check_permstring("Developer") and not self.caller.check_permstring("Admin"):
            self.caller.msg("You don't have permission to create rosters.")
            return

        # Default sphere to match the roster name, with consistent capitalization
        sphere = name.split()[0].capitalize()  # Take first word of name and capitalize it
        
        # Find the lowest available ID
        existing_ids = set(Roster.objects.values_list('id', flat=True))
        new_id = 1
        while new_id in existing_ids:
            new_id += 1
            
        # Create roster with specific ID
        roster = Roster.objects.create(
            id=new_id,
            name=name,
            description=desc,
            sphere=sphere
        )
        self.caller.msg(f"Created roster #{roster.id}: {roster.name} (Sphere: {sphere})")

    def delete_roster(self, roster_id):
        """Delete a roster."""
        if not (self.caller.check_permstring("Developer") or self.caller.check_permstring("Admin")):
            self.caller.msg("You don't have permission to delete rosters.")
            return

        try:
            roster = Roster.objects.get(id=roster_id)
            name = roster.name
            roster.delete()
            self.caller.msg(f"Deleted roster: {name}")
        except Roster.DoesNotExist:
            self.caller.msg(f"Roster #{roster_id} not found.")

    def add_character(self, roster_id, character_name):
        """Add a character to a roster."""
        try:
            roster = Roster.objects.get(id=roster_id)
        except Roster.DoesNotExist:
            self.caller.msg(f"Roster #{roster_id} not found.")
            return

        if not (self.caller.check_permstring("Developer") or 
                self.caller.check_permstring("Admin") or 
                roster.can_manage(self.caller.account)):
            self.caller.msg("You don't have permission to add characters to this roster.")
            return

        # Search for character using our helper
        char = search_character(self.caller, character_name)
        if not char:
            return  # Error message already handled by search_character

        # Check if already in roster
        if RosterMember.objects.filter(roster=roster, character=char).exists():
            self.caller.msg(f"{char.name} is already in roster {roster.name}.")
            return

        # Add to roster with approved=True by default
        RosterMember.objects.create(
            roster=roster,
            character=char,
            approved=True,
            approved_by=self.caller.account,
            approved_date=timezone.now()
        )
        self.caller.msg(f"Added {char.name} to roster {roster.name}.")

    def remove_character(self, roster_id, character_name):
        """Remove a character from a roster."""
        try:
            roster = Roster.objects.get(id=roster_id)
        except Roster.DoesNotExist:
            self.caller.msg(f"Roster #{roster_id} not found.")
            return

        if not (self.caller.check_permstring("Developer") or 
                self.caller.check_permstring("Admin") or 
                roster.can_manage(self.caller.account)):
            self.caller.msg("You don't have permission to remove characters from this roster.")
            return

        # Search for character using our helper
        char = search_character(self.caller, character_name)
        if not char:
            return  # Error message already handled by search_character

        # Remove from roster
        try:
            member = RosterMember.objects.get(roster=roster, character=char)
            member.delete()
            self.caller.msg(f"Removed {char.name} from roster {roster.name}.")
        except RosterMember.DoesNotExist:
            self.caller.msg(f"{char.name} is not in roster {roster.name}.")

    def approve_character(self, roster_id, character_name):
        """Approve a character in a roster."""
        try:
            roster = Roster.objects.get(id=roster_id)
        except Roster.DoesNotExist:
            self.caller.msg(f"Roster #{roster_id} not found.")
            return

        if not (self.caller.check_permstring("Developer") or 
                self.caller.check_permstring("Admin") or 
                roster.can_manage(self.caller.account)):
            self.caller.msg("You don't have permission to approve characters in this roster.")
            return

        # Search for character using our helper
        char = search_character(self.caller, character_name)
        if not char:
            return  # Error message already handled by search_character

        try:
            member = RosterMember.objects.get(roster=roster, character=char)
            member.approved = True
            member.approved_by = self.caller.account
            member.approved_date = timezone.now()
            member.save()
            self.caller.msg(f"Approved {char.name} in roster {roster.name}.")

            # Get character's splat from their stats
            char_stats = char.db.stats if hasattr(char.db, 'stats') else None
            char_splat = char_stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm') if char_stats else None
            
            if char_splat:
                # Try to find the main roster for this splat
                main_spheres = {
                    "Mage": "Mage",
                    "Shifter": "Shifter",
                    "Vampire": "Vampire",
                    "Changeling": "Changeling",
                    "Possessed": "Possessed",
                    "Companion": "Companion",
                    "Mortal": "Mortal",
                    "Mortal+": "Mortal"
                }
                
                if char_splat in main_spheres:
                    try:
                        # Find the main roster for this splat
                        main_roster = Roster.objects.filter(
                            name__iexact=main_spheres[char_splat]
                        ).first()
                        
                        if main_roster and main_roster.id != roster_id:  # Don't double-add if already approving for main roster
                            # Check if character is already in the main roster
                            if not RosterMember.objects.filter(roster=main_roster, character=char).exists():
                                # Add to main roster automatically
                                RosterMember.objects.create(
                                    roster=main_roster,
                                    character=char,
                                    approved=True,
                                    approved_by=self.caller.account,
                                    approved_date=timezone.now()
                                )
                                self.caller.msg(f"Also added {char.name} to the {main_spheres[char_splat]} roster automatically.")
                    except Exception as e:
                        self.caller.msg(f"Note: Could not automatically add to main {char_splat} roster: {e}")

        except RosterMember.DoesNotExist:
            self.caller.msg(f"{char.name} is not in roster {roster.name}.")

    def set_title(self, roster_id, character_name, title):
        """Set a character's title in a roster."""
        try:
            roster = Roster.objects.get(id=roster_id)
        except Roster.DoesNotExist:
            self.caller.msg(f"Roster #{roster_id} not found.")
            return

        if not (self.caller.check_permstring("Developer") or 
                self.caller.check_permstring("Admin") or 
                roster.can_manage(self.caller.account)):
            self.caller.msg("You don't have permission to set titles in this roster.")
            return

        # Search for character using our helper
        char = search_character(self.caller, character_name)
        if not char:
            return  # Error message already handled by search_character

        try:
            member = RosterMember.objects.get(roster=roster, character=char)
            member.title = title
            member.save()
            self.caller.msg(f"Set {char.name}'s title in roster {roster.name} to: {title}")
        except RosterMember.DoesNotExist:
            self.caller.msg(f"{char.name} is not in roster {roster.name}.")

    def set_website(self, roster_id, website):
        """Set a roster's website."""
        try:
            roster = Roster.objects.get(id=roster_id)
        except Roster.DoesNotExist:
            self.caller.msg(f"Roster #{roster_id} not found.")
            return

        if not (self.caller.check_permstring("Developer") or 
                self.caller.check_permstring("Admin") or 
                roster.can_manage(self.caller.account)):
            self.caller.msg("You don't have permission to set the website for this roster.")
            return

        roster.website = website
        roster.save()
        self.caller.msg(f"Set website for roster {roster.name} to: {website}")

    def set_description(self, roster_id, description):
        """Set a roster's description."""
        try:
            roster = Roster.objects.get(id=roster_id)
        except Roster.DoesNotExist:
            self.caller.msg(f"Roster #{roster_id} not found.")
            return

        if not (self.caller.check_permstring("Developer") or 
                self.caller.check_permstring("Admin") or 
                roster.can_manage(self.caller.account)):
            self.caller.msg("You don't have permission to set the description for this roster.")
            return

        roster.description = description
        roster.save()
        self.caller.msg(f"Updated description for roster {roster.name}.")

    def set_sphere(self, roster_id, sphere):
        """Set a roster's sphere."""
        try:
            roster = Roster.objects.get(id=roster_id)
        except Roster.DoesNotExist:
            self.caller.msg(f"Roster #{roster_id} not found.")
            return

        if not (self.caller.check_permstring("Developer") or 
                self.caller.check_permstring("Admin") or 
                roster.can_manage(self.caller.account)):
            self.caller.msg("You don't have permission to set the sphere for this roster.")
            return

        # Validate and normalize sphere name
        valid_spheres = ["Mage", "Shifter", "Vampire", "Changeling", "Possessed", "Companion", "Mortal"]
        sphere = sphere.capitalize()
        if sphere not in valid_spheres:
            self.caller.msg(f"Invalid sphere. Valid options are: {', '.join(valid_spheres)}")
            return

        roster.sphere = sphere
        roster.save()
        self.caller.msg(f"Set sphere for roster {roster.name} to: {sphere}")

    def list_rosters(self):
        """Show list of all existing rosters."""
        rosters = Roster.objects.all().order_by('id')

        if not rosters.exists():
            self.caller.msg("No rosters exist yet.")
            return

        # Format header with proper ANSI handling
        self.caller.msg("|b" + ("=" * 78) + "|n")
        self.caller.msg(" " * 30 + "|yAll Rosters|n")
        self.caller.msg("|b" + ("=" * 78) + "|n")
        
        # Column headers with fixed widths
        col_headers = f"|y{'#Num':4s} {'Name':17s} {'Sphere':12s} {'Members':10s} {'Description':33s}|n"
        separator = "|w" + ("-" * 76) + "|n"
        
        # Format each roster row
        roster_rows = []
        for roster in rosters:
            member_count = roster.get_members().count()
            desc = roster.description.split('\n')[0] if roster.description else ""
            sphere = roster.sphere if hasattr(roster, 'sphere') else "N/A"
            
            # Format each column with fixed width and truncation
            num = f"{roster.id:2d}".ljust(4)
            
            # Truncate name if too long (accounting for "...")
            if len(roster.name) > 14:
                name = roster.name[:11] + "..."
            else:
                name = roster.name
            name = name.ljust(17)
            
            # Truncate sphere if too long
            sphere = sphere[:17] + "..." if len(sphere) > 17 else sphere
            sphere = sphere.ljust(17)
            
            # Truncate description to a single line with ellipsis
            if len(desc) > 27:
                desc = desc[:30] + "..."
            
            # Format members count with right alignment
            members = f"{member_count:3d}".rjust(1)
            
            # Add 4 characters of left padding to description
            padded_desc = "    " + desc
            
            # Combine all fields into a single line
            roster_rows.append(f"{num}{name}{sphere}{members} {padded_desc}")

        # Join all components
        output = [
            col_headers,
            separator,
            *roster_rows,  # Unpack all roster rows
            "",  # Empty line before footer
            "|b" + ("=" * 78) + "|n"  # Footer
        ]

        # Send the complete formatted output
        self.caller.msg("\n".join(output))

    def set_manager(self, roster_id, player_name, remove=False):
        """Add or remove a manager from a roster."""
        try:
            roster = Roster.objects.get(id=roster_id)
        except Roster.DoesNotExist:
            self.caller.msg(f"Roster #{roster_id} not found.")
            return

        if not (self.caller.check_permstring("Developer") or self.caller.check_permstring("Admin")):
            self.caller.msg("You don't have permission to manage roster managers.")
            return

        # Find the player account
        from evennia.accounts.models import AccountDB
        player = AccountDB.objects.filter(username__iexact=player_name).first()
        if not player:
            self.caller.msg(f"Player '{player_name}' not found.")
            return

        if remove:
            if player in roster.managers.all():
                roster.managers.remove(player)
                self.caller.msg(f"Removed {player.username} as manager of roster {roster.name}.")
            else:
                self.caller.msg(f"{player.username} is not a manager of roster {roster.name}.")
        else:
            if player in roster.managers.all():
                self.caller.msg(f"{player.username} is already a manager of roster {roster.name}.")
            else:
                roster.managers.add(player)
                self.caller.msg(f"Added {player.username} as manager of roster {roster.name}.")

    def set_admin(self, roster_id, player_name, remove=False):
        """Add or remove an admin from a roster."""
        try:
            roster = Roster.objects.get(id=roster_id)
        except Roster.DoesNotExist:
            self.caller.msg(f"Roster #{roster_id} not found.")
            return

        if not (self.caller.check_permstring("Developer") or self.caller.check_permstring("Admin")):
            self.caller.msg("You don't have permission to manage roster administrators.")
            return

        # Find the player account
        from evennia.accounts.models import AccountDB
        player = AccountDB.objects.filter(username__iexact=player_name).first()
        if not player:
            self.caller.msg(f"Player '{player_name}' not found.")
            return

        if remove:
            if player in roster.admins.all():
                roster.admins.remove(player)
                self.caller.msg(f"Removed {player.username} as admin of roster {roster.name}.")
            else:
                self.caller.msg(f"{player.username} is not an admin of roster {roster.name}.")
        else:
            if player in roster.admins.all():
                self.caller.msg(f"{player.username} is already an admin of roster {roster.name}.")
            else:
                roster.admins.add(player)
                self.caller.msg(f"Added {player.username} as admin of roster {roster.name}.")

    def set_hangouts(self, roster_id, hangout_ids_str):
        """Set hangouts for a roster.
        
        Args:
            roster_id (int): The roster ID
            hangout_ids_str (str): Comma-separated list of hangout IDs
        """
        try:
            roster = Roster.objects.get(id=roster_id)
        except Roster.DoesNotExist:
            self.caller.msg(f"Roster #{roster_id} not found.")
            return

        if not (self.caller.check_permstring("Developer") or 
                self.caller.check_permstring("Admin") or 
                roster.can_manage(self.caller.account)):
            self.caller.msg("You don't have permission to set hangouts for this roster.")
            return

        # Parse hangout IDs
        try:
            hangout_ids = [int(id.strip()) for id in hangout_ids_str.split(',')]
        except ValueError:
            self.caller.msg("Please provide valid hangout IDs as a comma-separated list.")
            return

        # Verify all hangouts exist
        hangouts = []
        for hangout_id in hangout_ids:
            hangout = HangoutDB.get_by_hangout_id(hangout_id)
            if not hangout:
                self.caller.msg(f"Hangout #{hangout_id} not found.")
                return
            hangouts.append(hangout)

        # Set the hangouts
        roster.hangouts.clear()  # Remove existing hangouts
        for hangout in hangouts:
            roster.hangouts.add(hangout)

        # Confirmation message
        hangout_names = ", ".join(h.key for h in hangouts)
        self.caller.msg(f"Set hangouts for roster {roster.name} to: {hangout_names}")

    def func(self):
        """Execute command."""
        if not self.args and not self.switches:
            # Show rosters the character belongs to
            self.get_roster_list()
            return

        if "list" in self.switches:
            self.list_rosters()
            return

        if "create" in self.switches:
            if "=" not in self.args:
                self.caller.msg("Usage: +roster/create <name>=<description>")
                return
            name, desc = self.args.split("=", 1)
            self.create_roster(name.strip(), desc.strip())
            return

        if "delete" in self.switches:
            try:
                roster_id = int(self.args.strip())
                self.delete_roster(roster_id)
            except ValueError:
                self.caller.msg("Please provide a valid roster number.")
            return

        if "add" in self.switches:
            if "=" not in self.args:
                self.caller.msg("Usage: +roster/add <#>=<character>")
                return
            try:
                roster_id, char_name = self.args.split("=", 1)
                self.add_character(int(roster_id.strip()), char_name.strip())
            except ValueError:
                self.caller.msg("Please provide a valid roster number.")
            return

        if "remove" in self.switches:
            if "=" not in self.args:
                self.caller.msg("Usage: +roster/remove <#>=<character>")
                return
            try:
                roster_id, char_name = self.args.split("=", 1)
                self.remove_character(int(roster_id.strip()), char_name.strip())
            except ValueError:
                self.caller.msg("Please provide a valid roster number.")
            return

        if "approve" in self.switches:
            if "=" not in self.args:
                self.caller.msg("Usage: +roster/approve <#>=<character>")
                return
            try:
                roster_id, char_name = self.args.split("=", 1)
                self.approve_character(int(roster_id.strip()), char_name.strip())
            except ValueError:
                self.caller.msg("Please provide a valid roster number.")
            return

        if "title" in self.switches:
            if "/" not in self.args or "=" not in self.args:
                self.caller.msg("Usage: +roster/title <#>/<character>=<title>")
                return
            try:
                roster_char, title = self.args.split("=", 1)
                roster_id, char_name = roster_char.split("/", 1)
                self.set_title(int(roster_id.strip()), char_name.strip(), title.strip())
            except ValueError:
                self.caller.msg("Please provide a valid roster number.")
            return

        if "website" in self.switches:
            if "=" not in self.args:
                self.caller.msg("Usage: +roster/website <#>=<url>")
                return
            try:
                roster_id, website = self.args.split("=", 1)
                self.set_website(int(roster_id.strip()), website.strip())
            except ValueError:
                self.caller.msg("Please provide a valid roster number.")
            return

        if "desc" in self.switches:
            if "=" not in self.args:
                self.caller.msg("Usage: +roster/desc <#>=<description>")
                return
            try:
                roster_id, desc = self.args.split("=", 1)
                self.set_description(int(roster_id.strip()), desc.strip())
            except ValueError:
                self.caller.msg("Please provide a valid roster number.")
            return

        if "info" in self.switches:
            try:
                roster_id = int(self.args.strip())
                self.get_roster_info(roster_id)
            except ValueError:
                self.caller.msg("Please provide a valid roster number.")
            return

        if "who" in self.switches:
            try:
                roster_id = int(self.args.strip())
                self.get_roster_members(roster_id, online_only=True)
            except ValueError:
                self.caller.msg("Please provide a valid roster number.")
            return

        if "sphere" in self.switches:
            if "=" not in self.args:
                self.caller.msg("Usage: +roster/sphere <#>=<sphere>")
                return
            try:
                roster_id, sphere = self.args.split("=", 1)
                self.set_sphere(int(roster_id.strip()), sphere.strip())
            except ValueError:
                self.caller.msg("Please provide a valid roster number.")
            return

        if "hangouts" in self.switches:
            if "=" not in self.args:
                self.caller.msg("Usage: +roster/hangouts <#>=<hangout_id1,hangout_id2,...>")
                return
            try:
                roster_id, hangout_ids = self.args.split("=", 1)
                self.set_hangouts(int(roster_id.strip()), hangout_ids.strip())
            except ValueError:
                self.caller.msg("Please provide a valid roster number.")
            return

        # Add new manager commands
        if "manager" in self.switches:
            if "remove" in self.switches:
                if "=" not in self.args:
                    self.caller.msg("Usage: +roster/manager/remove <#>=<player>")
                    return
                try:
                    roster_id, player_name = self.args.split("=", 1)
                    self.set_manager(int(roster_id.strip()), player_name.strip(), remove=True)
                except ValueError:
                    self.caller.msg("Please provide a valid roster number.")
                return
            else:
                if "=" not in self.args:
                    self.caller.msg("Usage: +roster/manager <#>=<player>")
                    return
                try:
                    roster_id, player_name = self.args.split("=", 1)
                    self.set_manager(int(roster_id.strip()), player_name.strip())
                except ValueError:
                    self.caller.msg("Please provide a valid roster number.")
                return

        # Add new admin commands
        if "admin" in self.switches:
            if "remove" in self.switches:
                if "=" not in self.args:
                    self.caller.msg("Usage: +roster/admin/remove <#>=<player>")
                    return
                try:
                    roster_id, player_name = self.args.split("=", 1)
                    self.set_admin(int(roster_id.strip()), player_name.strip(), remove=True)
                except ValueError:
                    self.caller.msg("Please provide a valid roster number.")
                return
            else:
                if "=" not in self.args:
                    self.caller.msg("Usage: +roster/admin <#>=<player>")
                    return
                try:
                    roster_id, player_name = self.args.split("=", 1)
                    self.set_admin(int(roster_id.strip()), player_name.strip())
                except ValueError:
                    self.caller.msg("Please provide a valid roster number.")
                return

        # Default to showing all members
        try:
            roster_id = int(self.args.strip())
            self.get_roster_members(roster_id)
        except ValueError:
            self.caller.msg("Please provide a valid roster number.") 