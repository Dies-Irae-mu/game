from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils import evtable
from evennia.utils.ansi import ANSIString
from evennia.comms.models import ChannelDB
from evennia.utils import create
from world.groups.models import Group, GroupMembership
from world.wod20th.models import Roster
from utils.search_helpers import search_character
from django.db.models import Q
from evennia.objects.models import ObjectDB
from world.wod20th.utils.formatting import header, footer, divider


class CmdGroups(MuxCommand):
    """
    Commands to create and manage player and NPC groups.

    Usage:
        +groups                    - List all public groups
        +group <id>                - View detailed information about a group
        +group/create <name>       - Create a new group (staff only)
        +group/destroy <id>        - Destroy a group (staff only)
        +group/leader <id>=<char>  - Set the leader of a group (staff only)
        +group/roster <id>=<#>     - Link a group to a roster (staff only)
        +group/desc <id>=<text>    - Set a group's description (staff or leader)
        +group/website <id>=<url>  - Set a group's website (staff or leader)
        +group/note <id>=<text>    - Set a group's private notes (staff or leader)
        +group/title <id>/<char>=<title> - Set a character's title in the group
        +group/add <id>=<char>     - Add a character to a group (staff or leader)
        +group/remove <id>=<char>  - Remove a character from a group (staff or leader)
        +group/private <id>        - Set a group as private (staff or leader)
        +group/public <id>         - Set a group as public (staff or leader)

    When a group is created, a matching channel will be automatically created
    for members of that group. The channel name will be the name of the group
    with all spaces removed.

    Groups can be linked to rosters using +group/roster.
    """

    key = "+group"
    aliases = ["+groups"]
    locks = "cmd:all()"
    help_category = "Social"

    def list_groups(self):
        """List all public groups."""
        groups = Group.objects.filter(is_public=True).order_by('group_id')
        
        if not groups:
            self.caller.msg("No groups have been created yet.")
            return
        
        # Create the output
        output = []
        
        # Add the header
        groups_header = header("Groups", width=78, color="|y", fillchar="-", bcolor="|b")
        output.append(groups_header.rstrip())
        
        # Create the column headers
        output.append("\n |wID|n                |wName|n                 |wMembers|n             |wLeader|n            ")
        output.append("|b" + "~" * 78 + "|n")
        
        # Add each group as a row in the table
        for group in groups:
            # Count the number of members
            member_count = GroupMembership.objects.filter(group=group).count()
            
            # Get the leader's name
            leader_name = "None" if not group.leader else self.get_character_name(group.leader)
            
            # Format the row with proper spacing
            id_col = f" {group.group_id}"
            name_col = group.name
            members_col = str(member_count)
            leader_col = leader_name
            
            # Pad each column to ensure alignment
            id_col = id_col.ljust(18)
            name_col = name_col.ljust(20)
            members_col = members_col.ljust(20)
            
            # Add the row to the output
            output.append(f" {id_col}{name_col}{members_col}{leader_col}")
        
        # Add the footer
        output.append(footer(width=78).rstrip())
        
        # Send the output to the caller
        self.caller.msg("\n".join(output))
    
    def view_group(self, group_id):
        """View detailed information about a group."""
        try:
            # Try to get the group by ID
            group = Group.objects.get(group_id=group_id)
        except Group.DoesNotExist:
            self.caller.msg(f"Group #{group_id} does not exist.")
            return
        
        # Check if the group is private and if the caller has access
        is_staff = self.caller.check_permstring("Admin") or self.caller.check_permstring("Builder")
        is_member = GroupMembership.objects.filter(
            group=group, 
            character__db_object=self.caller
        ).exists()
        is_leader = group.leader and group.leader.db_object == self.caller
        
        if not group.is_public and not is_staff and not is_member:
            self.caller.msg(f"Group #{group_id} is private and you don't have access to view it.")
            return
        
        # Create the output
        output = []
        
        # Add the header
        group_header = header(group.name, width=78, color="|y", fillchar="-", bcolor="|b")
        output.append(group_header.rstrip())  # Remove trailing newline
        
        # Add the description section if it exists
        if group.description:
            desc_header = divider("Description", width=78, fillchar="-", color="|b", text_color="|y")
            output.append(desc_header)
            output.append(group.description)
        
        # Get all members and their titles
        memberships = GroupMembership.objects.filter(group=group).order_by('title')
        
        if memberships:
            members_header = divider("Members", width=78, fillchar="-", color="|b", text_color="|y")
            output.append(members_header)
            
            # Format the members list
            members_list = []
            
            for membership in memberships:
                # Get character name safely
                char_name = self.get_character_name(membership.character)
                title = membership.title if membership.title else ""
                
                # Format based on whether this is the leader
                if group.leader and group.leader.id == membership.character.id:
                    members_list.append(f"{title}: {char_name} |y(leader)|n")
                else:
                    members_list.append(f"{title}: {char_name}")
            
            output.extend(members_list)
        
        # Add contact information
        if group.leader:
            output.append("")
            # Get leader name safely
            leader_name = self.get_character_name(group.leader)
            output.append(f"Contact for information: {leader_name} (leader)")
        
        # Add website information if it exists
        if group.website:
            output.append("")
            website_header = divider("Website Information", width=78, fillchar="-", color="|b", text_color="|y")
            output.append(website_header)
            output.append(group.website)
        
        # Add the roster information if it exists
        if group.roster:
            output.append("")
            output.append(f"This group is linked to the {group.roster.name} roster (ID: {group.roster.id}).")
        
        # Add private notes if they exist and user has access
        if group.notes and (is_staff or is_member):
            output.append("")
            notes_header = divider("Private Notes", width=78, fillchar="-", color="|b", text_color="|y")
            output.append(notes_header)
            output.append(group.notes)
        
        # Add the footer
        footer_line = footer(width=78)
        output.append(footer_line.rstrip())  # Remove trailing newline
        
        # Send the output to the caller
        self.caller.msg("\n".join(output))
    
    def get_character_name(self, char_sheet):
        """
        Get a character's name from their character sheet safely.
        
        Args:
            char_sheet: CharacterSheet object
            
        Returns:
            String containing the character's name
        """
        # Method 1: Try to get character name from the related object
        if hasattr(char_sheet, 'character') and char_sheet.character:
            return char_sheet.character.name
            
        # Method 2: Try to get from db_object
        if hasattr(char_sheet, 'db_object') and char_sheet.db_object:
            return char_sheet.db_object.name
            
        # Method 3: Check if there's stats info with a name
        if hasattr(char_sheet, 'db_object') and char_sheet.db_object and hasattr(char_sheet.db_object, 'db'):
            obj = char_sheet.db_object
            if hasattr(obj.db, 'stats') and obj.db.stats:
                # Look for Full Name in identity/personal
                try:
                    full_name = obj.db.stats.get('identity', {}).get('personal', {}).get('Full Name', {})
                    if isinstance(full_name, dict):
                        return full_name.get('perm', obj.name)
                    elif full_name:
                        return full_name
                except (KeyError, AttributeError):
                    pass
                    
        # Fallback - return "Unknown Character"
        return "Unknown Character"
    
    def create_group(self, name):
        """Create a new group."""
        # Check if the caller has permission
        if not (self.caller.check_permstring("Admin") or self.caller.check_permstring("Builder")):
            self.caller.msg("You don't have permission to create groups.")
            return
        
        # Check if a group with this name already exists
        if Group.objects.filter(name=name).exists():
            self.caller.msg(f"A group named '{name}' already exists.")
            return
        
        # Create the group
        group = Group.objects.create(name=name)
        
        # Create a channel for the group
        channel_name = group.channel_name
        
        # Check if a channel with this name already exists
        if ChannelDB.objects.filter(db_key=channel_name).exists():
            self.caller.msg(f"Note: A channel named '{channel_name}' already exists and will be used for this group.")
            channel = ChannelDB.objects.get(db_key=channel_name)
            
            # Update the channel locks to match the group
            lock_string = (
                f"control:id({self.caller.id}) or perm(Admin);"
                f"listen:is_in_group({group.group_id}) or perm(Admin) or perm(Builder);"
                f"send:is_in_group({group.group_id}) or perm(Admin) or perm(Builder)"
            )
            channel.locks.add(lock_string)
            self.caller.msg(f"Updated channel '{channel_name}' locks to restrict access to group members.")
        else:
            # Create the channel with the appropriate locks
            lock_string = (
                f"control:id({self.caller.id}) or perm(Admin);"
                f"listen:is_in_group({group.group_id}) or perm(Admin) or perm(Builder);"
                f"send:is_in_group({group.group_id}) or perm(Admin) or perm(Builder)"
            )
            
            channel = create.create_channel(
                channel_name,
                typeclass="typeclasses.channels.Channel",
                desc=f"Group channel for {name}",
                locks=lock_string
            )
            self.caller.msg(f"Created channel '{channel_name}' for group '{name}' with restricted access.")
        
        self.caller.msg(f"Created group '{name}' with ID #{group.group_id}.")
    
    def destroy_group(self, group_id):
        """Destroy a group."""
        # Check if the caller has permission
        if not (self.caller.check_permstring("Admin") or self.caller.check_permstring("Builder")):
            self.caller.msg("You don't have permission to destroy groups.")
            return
        
        try:
            # Try to get the group
            group = Group.objects.get(group_id=group_id)
        except Group.DoesNotExist:
            self.caller.msg(f"Group #{group_id} does not exist.")
            return
        
        # Store info before deletion
        group_name = group.name
        channel_name = group.channel_name
        roster = group.roster

        # Remove all memberships first
        memberships = GroupMembership.objects.filter(group=group)
        if memberships.exists():
            # Get a count for the message
            count = memberships.count()
            # Delete all memberships
            memberships.delete()
            self.caller.msg(f"Removed {count} members from group '{group_name}'.")
        
        # Remove all roles
        roles = group.roles.all()
        if roles.exists():
            # Get a count for the message
            count = roles.count()
            # Delete all roles
            roles.delete()
            self.caller.msg(f"Removed {count} roles from group '{group_name}'.")
        
        # Get the channel before deleting the group
        channel = ChannelDB.objects.filter(db_key=channel_name).first()
        
        # Notify about roster removal if applicable
        if roster:
            self.caller.msg(f"Removed group '{group_name}' from roster '{roster.name}'.")
            
        # Delete the group
        group.delete()
        self.caller.msg(f"Destroyed group '{group_name}' (ID #{group_id}).")
        
        # Delete the channel if it exists
        if channel:
            # Make sure we're deleting the right channel
            if channel.db_key == channel_name:
                # Get all subscribers to notify them
                subscribers = list(channel.subscriptions.all())
                
                # Disconnect all subscribers first
                for subscriber in subscribers:
                    channel.disconnect(subscriber)
                
                # Delete the channel
                channel.delete()
                self.caller.msg(f"Deleted channel '{channel_name}' and removed {len(subscribers)} subscribers.")
        else:
            self.caller.msg(f"No channel named '{channel_name}' found to delete.")
    
    def get_character_sheet(self, character):
        """
        Safely get a character's sheet using multiple approaches.
        
        Args:
            character: The character object to get a sheet for
            
        Returns:
            The character sheet or None if not found
        """
        char_sheet = None
        
        # Method 1: Direct attribute access
        if hasattr(character, 'character_sheet'):
            try:
                char_sheet = character.character_sheet
                if char_sheet:
                    return char_sheet
            except Exception:
                pass
        
        # Method 2: Check if there's a db attribute pointing to a sheet
        if hasattr(character, 'db') and hasattr(character.db, 'character_sheet'):
            char_sheet = character.db.character_sheet
            if char_sheet:
                return char_sheet
        
        # Method 3: Direct database lookup
        try:
            from world.wod20th.models import CharacterSheet
            char_sheet = CharacterSheet.objects.filter(db_object=character).first()
            if char_sheet:
                return char_sheet
        except Exception:
            pass
            
        # Method 4: Check if character IS a sheet (unlikely but possible)
        try:
            from world.wod20th.models import CharacterSheet
            if isinstance(character, CharacterSheet):
                return character
        except Exception:
            pass
            
        # Method 5: Check if the character has stats but no sheet, and create one if needed
        if hasattr(character, 'db') and hasattr(character.db, 'stats'):
            try:
                from world.wod20th.models import CharacterSheet
                from django.db import transaction
                
                # Check if character has stats (this is the important part)
                if character.db.stats:
                    # This is a character with stats but no sheet - create one
                    self.caller.msg(f"Character {character.name} has stats but no character sheet. Creating one...")
                    
                    # Use a transaction to ensure we don't get half-created objects
                    with transaction.atomic():
                        # Create the sheet and link it to the character
                        char_sheet = CharacterSheet.objects.create(
                            db_object=character,
                            character=character
                        )
                        
                        # Set up character's full name if available in stats
                        try:
                            stats = character.db.stats
                            identity = stats.get('identity', {})
                            personal = identity.get('personal', {})
                            full_name_data = personal.get('Full Name', {})
                            
                            if isinstance(full_name_data, dict) and 'perm' in full_name_data:
                                char_sheet.db_title = full_name_data['perm']
                                char_sheet.save()
                        except Exception as e:
                            self.caller.msg(f"Note: Could not set full name for {character.name}: {e}")
                        
                    self.caller.msg(f"Successfully created character sheet for {character.name}")
                    return char_sheet
            except Exception as e:
                self.caller.msg(f"Error creating character sheet for {character.name}: {e}")
                pass
            
        # Failed to find a character sheet
        return None
    
    def set_leader(self, group_id, character_name):
        """Set the leader of a group."""
        # Check if the caller has permission
        if not (self.caller.check_permstring("Admin") or self.caller.check_permstring("Builder")):
            self.caller.msg("You don't have permission to set group leaders.")
            return
        
        try:
            # Try to get the group
            group = Group.objects.get(group_id=group_id)
        except Group.DoesNotExist:
            self.caller.msg(f"Group #{group_id} does not exist.")
            return
        
        # Find the character
        character = search_character(self.caller, character_name)
        if not character:
            return
        
        # Get the character sheet using our improved method
        char_sheet = self.get_character_sheet(character)
        
        if not char_sheet:
            self.caller.msg(f"Could not find a character sheet for {character.name}. A sheet is required for group membership.")
            return
        
        # Set the leader
        old_leader = group.leader.character.name if group.leader else "None"
        group.leader = char_sheet
        group.save()
        
        # Ensure the leader is a member of the group
        if not GroupMembership.objects.filter(group=group, character=char_sheet).exists():
            GroupMembership.objects.create(group=group, character=char_sheet)
            self.caller.msg(f"Added {character.name} to group '{group.name}' as a member.")
        
        self.caller.msg(f"Set {character.name} as the leader of group '{group.name}' (was {old_leader}).")
    
    def link_to_roster(self, group_id, roster_id):
        """Link a group to a roster."""
        # Check if the caller has permission
        if not (self.caller.check_permstring("Admin") or self.caller.check_permstring("Builder")):
            self.caller.msg("You don't have permission to link groups to rosters.")
            return
        
        try:
            # Try to get the group
            group = Group.objects.get(group_id=group_id)
        except Group.DoesNotExist:
            self.caller.msg(f"Group #{group_id} does not exist.")
            return
        
        try:
            # Try to get the roster
            roster = Roster.objects.get(id=roster_id)
        except Roster.DoesNotExist:
            self.caller.msg(f"Roster #{roster_id} does not exist.")
            return
        
        # Link the group to the roster
        old_roster = group.roster.name if group.roster else "None"
        group.roster = roster
        group.save()
        
        self.caller.msg(f"Linked group '{group.name}' to roster '{roster.name}' (was {old_roster}).")
    
    def set_description(self, group_id, description):
        """Set a group's description."""
        try:
            # Try to get the group
            group = Group.objects.get(group_id=group_id)
        except Group.DoesNotExist:
            self.caller.msg(f"Group #{group_id} does not exist.")
            return
        
        # Check if the caller has permission
        is_staff = self.caller.check_permstring("Admin") or self.caller.check_permstring("Builder")
        is_leader = group.leader and group.leader.db_object == self.caller
        
        if not is_staff and not is_leader:
            self.caller.msg("You don't have permission to set group descriptions.")
            return
        
        # Set the description
        group.description = description
        group.save()
        
        self.caller.msg(f"Set description for group '{group.name}'.")
    
    def set_website(self, group_id, website):
        """Set a group's website."""
        try:
            # Try to get the group
            group = Group.objects.get(group_id=group_id)
        except Group.DoesNotExist:
            self.caller.msg(f"Group #{group_id} does not exist.")
            return
        
        # Check if the caller has permission
        is_staff = self.caller.check_permstring("Admin") or self.caller.check_permstring("Builder")
        is_leader = group.leader and group.leader.db_object == self.caller
        
        if not is_staff and not is_leader:
            self.caller.msg("You don't have permission to set group websites.")
            return
        
        # Set the website
        group.website = website
        group.save()
        
        self.caller.msg(f"Set website for group '{group.name}'.")
    
    def set_title(self, group_id, character_name, title):
        """Set a character's title in a group."""
        try:
            # Try to get the group
            group = Group.objects.get(group_id=group_id)
        except Group.DoesNotExist:
            self.caller.msg(f"Group #{group_id} does not exist.")
            return
        
        # Check if the caller has permission
        is_staff = self.caller.check_permstring("Admin") or self.caller.check_permstring("Builder")
        is_leader = group.leader and group.leader.db_object == self.caller
        
        if not is_staff and not is_leader:
            self.caller.msg("You don't have permission to set member titles.")
            return
        
        # Find the character
        character = search_character(self.caller, character_name)
        if not character:
            return
        
        # Get the character sheet using our improved method
        char_sheet = self.get_character_sheet(character)
        
        if not char_sheet:
            self.caller.msg(f"Could not find a character sheet for {character.name}. A sheet is required for group membership.")
            return
        
        # Check if the character is a member of the group
        try:
            membership = GroupMembership.objects.get(group=group, character=char_sheet)
        except GroupMembership.DoesNotExist:
            self.caller.msg(f"{character.name} is not a member of group '{group.name}'.")
            return
        
        # Set the title
        old_title = membership.title or "None"
        membership.title = title
        membership.save()
        
        self.caller.msg(f"Set title for {character.name} in group '{group.name}' to '{title}' (was '{old_title}').")
    
    def add_character(self, group_id, character_name):
        """Add a character to a group."""
        try:
            # Try to get the group
            group = Group.objects.get(group_id=group_id)
        except Group.DoesNotExist:
            self.caller.msg(f"Group #{group_id} does not exist.")
            return
        
        # Check if the caller has permission
        is_staff = self.caller.check_permstring("Admin") or self.caller.check_permstring("Builder")
        is_leader = group.leader and group.leader.db_object == self.caller
        
        if not is_staff and not is_leader:
            self.caller.msg("You don't have permission to add members to this group.")
            return
        
        # Find the character
        character = search_character(self.caller, character_name)
        if not character:
            return
        
        # Get the character sheet using our improved method
        char_sheet = self.get_character_sheet(character)
        
        if not char_sheet:
            self.caller.msg(f"Could not find a character sheet for {character.name}. A sheet is required for group membership.")
            return
        
        # Check if the character is already a member of the group
        if GroupMembership.objects.filter(group=group, character=char_sheet).exists():
            self.caller.msg(f"{character.name} is already a member of group '{group.name}'.")
            return
        
        # Add the character to the group
        GroupMembership.objects.create(group=group, character=char_sheet)
        
        # Add character to the group's channel
        channel_name = group.channel_name
        channel = ChannelDB.objects.filter(db_key=channel_name).first()
        
        if channel:
            # Connect the character to the channel
            channel.connect(character)
            
            # Make sure the channel has the right locks
            lock_string = (
                f"control:id({self.caller.id}) or perm(Admin);"
                f"listen:is_in_group({group.group_id}) or perm(Admin) or perm(Builder);"
                f"send:is_in_group({group.group_id}) or perm(Admin) or perm(Builder)"
            )
            channel.locks.add(lock_string)
            
            self.caller.msg(f"Added {character.name} to channel '{channel_name}'.")
        
        self.caller.msg(f"Added {character.name} to group '{group.name}'.")
    
    def remove_character(self, group_id, character_name):
        """Remove a character from a group."""
        try:
            # Try to get the group
            group = Group.objects.get(group_id=group_id)
        except Group.DoesNotExist:
            self.caller.msg(f"Group #{group_id} does not exist.")
            return
        
        # Check if the caller has permission
        is_staff = self.caller.check_permstring("Admin") or self.caller.check_permstring("Builder")
        is_leader = group.leader and group.leader.db_object == self.caller
        
        if not is_staff and not is_leader:
            self.caller.msg("You don't have permission to remove members from this group.")
            return
        
        # Find the character
        character = search_character(self.caller, character_name)
        if not character:
            return
        
        # Get the character sheet using our improved method
        char_sheet = self.get_character_sheet(character)
        
        if not char_sheet:
            self.caller.msg(f"Could not find a character sheet for {character.name}. A sheet is required for group membership.")
            return
        
        # Check if the character is a member of the group
        try:
            membership = GroupMembership.objects.get(group=group, character=char_sheet)
        except GroupMembership.DoesNotExist:
            self.caller.msg(f"{character.name} is not a member of group '{group.name}'.")
            return
        
        # Check if the character is the leader of the group
        if group.leader and group.leader.id == char_sheet.id:
            self.caller.msg(f"{character.name} is the leader of group '{group.name}'. Please set a new leader first.")
            return
        
        # Remove the character from the group
        membership.delete()
        
        # Remove character from the group's channel
        channel_name = group.channel_name
        channel = ChannelDB.objects.filter(db_key=channel_name).first()
        
        if channel:
            channel.disconnect(character)
            self.caller.msg(f"Removed {character.name} from channel '{channel_name}'.")
        
        self.caller.msg(f"Removed {character.name} from group '{group.name}'.")
    
    def set_privacy(self, group_id, is_public):
        """Set a group as public or private."""
        try:
            # Try to get the group
            group = Group.objects.get(group_id=group_id)
        except Group.DoesNotExist:
            self.caller.msg(f"Group #{group_id} does not exist.")
            return
        
        # Check if the caller has permission
        is_staff = self.caller.check_permstring("Admin") or self.caller.check_permstring("Builder")
        is_leader = group.leader and group.leader.db_object == self.caller
        
        if not is_staff and not is_leader:
            self.caller.msg("You don't have permission to change group privacy settings.")
            return
        
        # Set the privacy
        if group.is_public == is_public:
            self.caller.msg(f"Group '{group.name}' is already {'public' if is_public else 'private'}.")
            return
        
        group.is_public = is_public
        group.save()
        
        self.caller.msg(f"Set group '{group.name}' to {'public' if is_public else 'private'}.")
    
    def set_notes(self, group_id, notes):
        """Set a group's private notes."""
        try:
            # Try to get the group
            group = Group.objects.get(group_id=group_id)
        except Group.DoesNotExist:
            self.caller.msg(f"Group #{group_id} does not exist.")
            return
        
        # Check if the caller has permission
        is_staff = self.caller.check_permstring("Admin") or self.caller.check_permstring("Builder")
        is_leader = group.leader and group.leader.db_object == self.caller
        
        if not is_staff and not is_leader:
            self.caller.msg("You don't have permission to set group notes.")
            return
        
        # Set the notes
        group.notes = notes
        group.save()
        
        self.caller.msg(f"Set private notes for group '{group.name}'.")
    
    def func(self):
        """Execute the command."""
        if not self.args:
            # Display list of public groups
            if self.cmdstring == "+groups":
                self.list_groups()
                return
            
            self.caller.msg("Usage: +group <id> or +groups")
            return
        
        # Parse the command
        if self.switches:
            switch = self.switches[0]
            
            # Create a group
            if switch == "create":
                self.create_group(self.args.strip())
                return
            
            # Handle destroy switch specifically (doesn't need equals sign)
            if switch == "destroy":
                try:
                    group_id = int(self.args.strip())
                    self.destroy_group(group_id)
                    return
                except ValueError:
                    self.caller.msg("Group ID must be a number.")
                    return
            
            # Handle private/public switches (don't need equals sign)
            if switch in ["private", "public"]:
                try:
                    group_id = int(self.args.strip())
                    self.set_privacy(group_id, switch == "public")
                    return
                except ValueError:
                    self.caller.msg("Group ID must be a number.")
                    return
            
            # Handle the title switch (format: <id>/<char>=<title>)
            if switch == "title":
                # Check if the format contains both a slash and an equals sign
                if "/" in self.args and "=" in self.args:
                    # Split on the equals sign first to separate title from the rest
                    group_char, title = self.args.split("=", 1)
                    
                    # Now split the first part on the slash to get group_id and character_name
                    parts = group_char.split("/", 1)
                    
                    # Verify we got the expected format
                    if len(parts) == 2:
                        group_id, character_name = parts
                        
                        group_id = group_id.strip()
                        character_name = character_name.strip()
                        title = title.strip()
                        
                        # Try to convert group_id to an integer
                        try:
                            group_id = int(group_id)
                            self.set_title(group_id, character_name, title)
                            return
                        except ValueError:
                            self.caller.msg("Group ID must be a number.")
                            return
                
                # If we get here, the format was wrong
                self.caller.msg("Usage: +group/title <id>/<char>=<title>")
                return
            
            # Commands that require a group ID with equals sign
            if "=" in self.args:
                # Format: <id>=<value>
                group_id, value = self.args.split("=", 1)
                group_id = group_id.strip()
                value = value.strip()
                
                # Try to convert group_id to an integer
                try:
                    group_id = int(group_id)
                except ValueError:
                    self.caller.msg("Group ID must be a number.")
                    return
                
                # Process the command based on the switch
                if switch == "leader":
                    self.set_leader(group_id, value)
                elif switch == "roster":
                    # Try to convert roster_id to an integer
                    try:
                        roster_id = int(value)
                    except ValueError:
                        self.caller.msg("Roster ID must be a number.")
                        return
                    
                    self.link_to_roster(group_id, roster_id)
                elif switch == "desc":
                    self.set_description(group_id, value)
                elif switch == "website":
                    self.set_website(group_id, value)
                elif switch == "note":
                    self.set_notes(group_id, value)
                elif switch == "add":
                    self.add_character(group_id, value)
                elif switch == "remove":
                    self.remove_character(group_id, value)
                else:
                    self.caller.msg(f"Unknown switch: {switch}")
                
                return
            
            # If we get here, the command format is invalid
            self.caller.msg(f"Invalid command format for switch '{switch}'.")
            return
        
        # View a group
        try:
            group_id = int(self.args.strip())
        except ValueError:
            self.caller.msg("Group ID must be a number.")
            return
        
        self.view_group(group_id)


# Add the command to the default command set 