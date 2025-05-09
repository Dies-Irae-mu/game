"""
Commands for managing groups of NPCs.

This module contains commands for creating and managing groups of NPCs
like gangs, cabals, coteries, and other organizations.
"""

from evennia import default_cmds
from typeclasses.npc_groups import NPCGroup
from evennia.utils import evtable
import re

class CmdOrganization(default_cmds.MuxCommand):
    """
    Manage groups of NPCs such as gangs, cabals, and coteries.
    
    Aliases: +organization, +npcgroup, +org

    Usage:
      +organization/create <name>[=<group_type>]    - Create a new NPC group
      +organization/list                          - List all NPC groups
      +organization/info <group>                  - View group details
      +organization/delete <group>                - Delete a group
      
      +organization/set <group>/<field>=<value>   - Set group properties
        Fields: type, splat, difficulty, territory, desc, resources, influence
      
      +organization/addnpc <group>=<name>[,<position>] - Add a new NPC to group
      +organization/addnpcs <group>=<count>[,<prefix>,<pos1,pos2,...>] - Add multiple NPCs
      +organization/removenpc <group>=<name or #num>   - Remove NPC from group
      +organization/position <group>/<npc>=<position>  - Set NPC's position in group
      
      +organization/addgoal <group>=<goal text>   - Add a goal to the group
      +organization/remgoal <group>=<goal number> - Remove a goal
      
      +organization/summon <group>                - Bring all group NPCs to your location
      +organization/recall <group>                - Move all group NPCs back to group location
      
    Examples:
      +organization/create Red Talons=Pack
      +organization/set Red Talons/type=Werewolf Pack
      +organization/set Red Talons/splat=shifter
      +organization/set Red Talons/difficulty=HIGH
      +organization/set Red Talons/territory=North Woods
      +organization/set Red Talons/desc=A vicious pack of Red Talon werewolves
      +organization/set Red Talons/resources=2
      +organization/set Red Talons/influence=3
      +organization/addnpc Red Talons=Shadow Hunter,Alpha
      +organization/addnpcs Red Talons=3,Pack Member,Beta,Warrior,Scout
      +organization/addgoal Red Talons=Drive humans from their territory
      +organization/summon Red Talons
    """
    
    key = "+organization"
    aliases = ["+npcgroup", "org", "+org"]
    locks = "cmd:perm(Builder) or perm(Storyteller) or perm(Admin)"
    help_category = "NPC Commands"
    
    def func(self):
        """Implement the command"""
        caller = self.caller
        
        if not self.switches:
            # Default to showing help
            caller.msg(self.__doc__)
            return
            
        switch = self.switches[0]
        
        if switch == "create":
            self.create_group()
        elif switch == "list":
            self.list_groups()
        elif switch == "info":
            self.show_group_info()
        elif switch == "delete":
            self.delete_group()
        elif switch == "set":
            self.set_group_property()
        elif switch == "addnpc":
            self.add_npc()
        elif switch == "addnpcs":
            self.add_npcs_batch()
        elif switch == "removenpc":
            self.remove_npc()
        elif switch == "position":
            self.set_npc_position()
        elif switch == "addgoal":
            self.add_goal()
        elif switch == "remgoal":
            self.remove_goal()
        elif switch == "summon":
            self.summon_group()
        elif switch == "recall":
            self.recall_group()
        else:
            caller.msg(f"Unknown switch: {switch}")
            caller.msg(self.__doc__)
    
    def create_group(self):
        """Create a new NPC group"""
        args = self.args.strip()
        
        if not args:
            self.caller.msg("Usage: +organization/create <name>[=<group_type>]")
            return
            
        # Split name and type if provided
        if "=" in args:
            name, group_type = args.split("=", 1)
            name = name.strip()
            group_type = group_type.strip()
        else:
            name = args
            group_type = "Generic"
            
        # Check if a group with this name already exists
        existing = self.caller.search(name, global_search=True, quiet=True)
        if existing and any(isinstance(obj, NPCGroup) for obj in existing):
            self.caller.msg(f"An NPC group named '{name}' already exists.")
            return
            
        # Create the group
        try:
            # Create at caller's location
            group = NPCGroup.create(
                key=name,
                location=self.caller.location,
                attributes=[
                    ("desc", f"A group of {group_type}s."),
                    ("group_type", group_type),
                    ("creator", self.caller),
                ],
            )
            
            self.caller.msg(f"Created new NPC group: {name} (Type: {group_type})")
            
        except Exception as e:
            self.caller.msg(f"Error creating NPC group: {e}")
    
    def list_groups(self):
        """List all NPC groups"""
        from evennia.utils.search import search_object
        
        # Search for all NPCGroup objects
        groups = search_object(None, typeclass="typeclasses.npc_groups.NPCGroup")
        
        if not groups:
            self.caller.msg("No NPC groups found.")
            return
            
        # Create table
        table = evtable.EvTable(
            "|wGroup Name|n",
            "|wType|n",
            "|wLocation|n",
            "|wNPCs|n",
            border="table",
            width=78
        )
        
        for group in sorted(groups, key=lambda x: x.key):
            npcs_count = len(group.get_all_npcs()) if hasattr(group, 'get_all_npcs') else 0
            location = group.location.key if group.location else "None"
            
            table.add_row(
                group.key,
                group.db.group_type,
                location,
                npcs_count
            )
            
        self.caller.msg(table)
    
    def show_group_info(self):
        """Show detailed information about a group"""
        if not self.args:
            self.caller.msg("Usage: +organization/info <group>")
            return
            
        # Search for the group
        group = self.caller.search(self.args, global_search=True)
        if not group or not isinstance(group, NPCGroup):
            self.caller.msg(f"'{self.args}' is not a valid NPC group.")
            return
            
        # Use the group's appearance method to show detailed info
        self.caller.msg(group.return_appearance(self.caller))
    
    def delete_group(self):
        """Delete an NPC group"""
        if not self.args:
            self.caller.msg("Usage: +organization/delete <group>")
            return
            
        # Search for the group
        group = self.caller.search(self.args, global_search=True)
        if not group or not isinstance(group, NPCGroup):
            self.caller.msg(f"'{self.args}' is not a valid NPC group.")
            return
            
        # Confirm deletion
        self.caller.msg(f"Are you sure you want to delete the NPC group '{group.key}'?")
        self.caller.msg("This will not delete the NPCs in the group, only their organization.")
        
        # Define a callback for the confirmation
        def confirm_delete(caller, prompt, result):
            if result.lower() in ("y", "yes"):
                # Get all NPCs in the group before deleting
                npcs = group.get_all_npcs()
                
                # Remove group references from NPCs
                for npc in npcs:
                    if hasattr(npc, 'db'):
                        npc.db.npc_group = None
                        npc.db.npc_group_id = None
                
                # Delete the group
                group_name = group.key
                group.delete()
                caller.msg(f"NPC group '{group_name}' has been deleted.")
            else:
                caller.msg("Deletion canceled.")
                
        # Ask for confirmation
        get_input = self.caller.msg_input
        get_input("Type 'yes' to confirm deletion: ", confirm_delete)
    
    def set_group_property(self):
        """Set a property on an NPC group"""
        args = self.args.strip()
        
        if not args or "/" not in args or "=" not in args:
            self.caller.msg("Usage: +organization/set <group>/<field>=<value>")
            return
            
        # Parse arguments
        try:
            group_and_field, value = args.split("=", 1)
            group_name, field = group_and_field.split("/", 1)
            
            group_name = group_name.strip()
            field = field.strip().lower()
            value = value.strip()
        except ValueError:
            self.caller.msg("Invalid format. Use: +organization/set <group>/<field>=<value>")
            return
            
        # Search for the group
        group = self.caller.search(group_name, global_search=True)
        if not group or not isinstance(group, NPCGroup):
            self.caller.msg(f"'{group_name}' is not a valid NPC group.")
            return
            
        # Handle different fields
        if field in ("type", "group_type"):
            group.db.group_type = value
            self.caller.msg(f"Set {group.key}'s type to: {value}")
            
        elif field == "splat":
            group.db.splat = value.lower()
            self.caller.msg(f"Set {group.key}'s splat to: {value}")
            
        elif field == "difficulty":
            # Normalize difficulty value
            difficulty = value.upper()
            if difficulty not in ("LOW", "MEDIUM", "HIGH"):
                self.caller.msg("Difficulty must be LOW, MEDIUM, or HIGH.")
                return
                
            group.db.difficulty = difficulty
            self.caller.msg(f"Set {group.key}'s difficulty to: {difficulty}")
            
        elif field == "territory":
            group.db.territory = value
            self.caller.msg(f"Set {group.key}'s territory to: {value}")
            
        elif field in ("desc", "description"):
            group.db.desc = value
            self.caller.msg(f"Set {group.key}'s description.")
            
        elif field == "resources":
            try:
                resources = int(value)
                if resources < 0 or resources > 5:
                    self.caller.msg("Resources must be between 0 and 5.")
                    return
                    
                group.db.resources = resources
                self.caller.msg(f"Set {group.key}'s resources to: {resources}")
            except ValueError:
                self.caller.msg("Resources must be a number between 0 and 5.")
                
        elif field == "influence":
            try:
                influence = int(value)
                if influence < 0 or influence > 5:
                    self.caller.msg("Influence must be between 0 and 5.")
                    return
                    
                group.db.influence = influence
                self.caller.msg(f"Set {group.key}'s influence to: {influence}")
            except ValueError:
                self.caller.msg("Influence must be a number between 0 and 5.")
                
        else:
            self.caller.msg(f"Unknown field: {field}")
            self.caller.msg("Valid fields: type, splat, difficulty, territory, desc, resources, influence")
    
    def add_npc(self):
        """Add a new NPC to a group"""
        args = self.args.strip()
        
        if not args or "=" not in args:
            self.caller.msg("Usage: +organization/addnpc <group>=<name>[,<position>]")
            return
            
        # Parse arguments
        group_name, npc_info = args.split("=", 1)
        group_name = group_name.strip()
        
        # Parse NPC info
        if "," in npc_info:
            name, position = npc_info.split(",", 1)
            name = name.strip()
            position = position.strip()
        else:
            name = npc_info.strip()
            position = None
            
        # Search for the group
        group = self.caller.search(group_name, global_search=True)
        if not group or not isinstance(group, NPCGroup):
            self.caller.msg(f"'{group_name}' is not a valid NPC group.")
            return
            
        # Create and add the NPC
        npc = group.create_npc(name, position=position)
        
        if npc:
            self.caller.msg(f"Added new NPC '{npc.key}' to group '{group.key}'")
            if position:
                self.caller.msg(f"Position: {position}")
        else:
            self.caller.msg(f"Error creating NPC for group '{group.key}'")
    
    def add_npcs_batch(self):
        """Add multiple NPCs to a group at once"""
        args = self.args.strip()
        
        if not args or "=" not in args:
            self.caller.msg("Usage: +organization/addnpcs <group>=<count>[,<prefix>,<pos1,pos2,...>]")
            return
            
        # Parse arguments
        group_name, batch_info = args.split("=", 1)
        group_name = group_name.strip()
        
        # Parse batch info
        parts = batch_info.split(",")
        if not parts:
            self.caller.msg("You must specify at least the number of NPCs to create.")
            return
            
        try:
            count = int(parts[0])
            if count <= 0:
                self.caller.msg("Count must be a positive number.")
                return
        except ValueError:
            self.caller.msg("Count must be a number.")
            return
            
        # Get optional prefix and positions
        prefix = parts[1].strip() if len(parts) > 1 else None
        positions = [p.strip() for p in parts[2:]] if len(parts) > 2 else None
        
        # Search for the group
        group = self.caller.search(group_name, global_search=True)
        if not group or not isinstance(group, NPCGroup):
            self.caller.msg(f"'{group_name}' is not a valid NPC group.")
            return
            
        # Create the batch of NPCs
        npcs = group.create_npcs_batch(count, prefix=prefix, positions=positions)
        
        if npcs:
            self.caller.msg(f"Added {len(npcs)} NPCs to group '{group.key}'")
            # Show the names
            if len(npcs) <= 10:  # Only show names if not too many
                for npc in npcs:
                    self.caller.msg(f"- {npc.key}")
            else:
                self.caller.msg(f"First NPC: {npcs[0].key}, Last NPC: {npcs[-1].key}")
        else:
            self.caller.msg(f"Error creating NPCs for group '{group.key}'")
    
    def remove_npc(self):
        """Remove an NPC from a group"""
        args = self.args.strip()
        
        if not args or "=" not in args:
            self.caller.msg("Usage: +organization/removenpc <group>=<name or #num>")
            return
            
        # Parse arguments
        group_name, npc_ref = args.split("=", 1)
        group_name = group_name.strip()
        npc_ref = npc_ref.strip()
        
        # Search for the group
        group = self.caller.search(group_name, global_search=True)
        if not group or not isinstance(group, NPCGroup):
            self.caller.msg(f"'{group_name}' is not a valid organization.")
            return
            
        # Find the NPC
        npc = None
        if npc_ref.startswith("#"):
            try:
                group_number = int(npc_ref[1:])
                npc = group.get_npc_by_group_number(group_number)
            except ValueError:
                pass
        else:
            npc = group.get_npc_by_name(npc_ref)
            
        if not npc:
            self.caller.msg(f"No NPC matching '{npc_ref}' found in organization '{group.key}'.")
            return
            
        # Store the NPC name for message
        npc_name = npc.key
        
        # Confirm removal
        self.caller.msg(f"Are you sure you want to remove '{npc_name}' from organization '{group.key}'?")
        self.caller.msg("This will only remove the NPC from the organization, not delete it.")
        
        # Define a callback for the confirmation
        def confirm_remove(caller, prompt, result):
            if result.lower() in ("y", "yes"):
                if group.remove_npc(npc):
                    caller.msg(f"Removed NPC '{npc_name}' from organization '{group.key}'.")
                else:
                    caller.msg(f"Error removing NPC from organization.")
            else:
                caller.msg("Removal canceled.")
                
        # Ask for confirmation
        get_input = self.caller.msg_input
        get_input("Type 'yes' to confirm removal: ", confirm_remove)
    
    def set_npc_position(self):
        """Set an NPC's position in the group"""
        args = self.args.strip()
        
        if not args or "/" not in args or "=" not in args:
            self.caller.msg("Usage: +organization/position <group>/<npc>=<position>")
            return
            
        # Parse arguments
        try:
            group_and_npc, position = args.split("=", 1)
            group_name, npc_ref = group_and_npc.split("/", 1)
            
            group_name = group_name.strip()
            npc_ref = npc_ref.strip()
            position = position.strip()
        except ValueError:
            self.caller.msg("Invalid format. Use: +organization/position <group>/<npc>=<position>")
            return
            
        # Search for the group
        group = self.caller.search(group_name, global_search=True)
        if not group or not isinstance(group, NPCGroup):
            self.caller.msg(f"'{group_name}' is not a valid NPC group.")
            return
            
        # Find the NPC
        npc = None
        if npc_ref.startswith("#"):
            try:
                group_number = int(npc_ref[1:])
                npc = group.get_npc_by_group_number(group_number)
            except ValueError:
                pass
        else:
            npc = group.get_npc_by_name(npc_ref)
            
        if not npc:
            self.caller.msg(f"No NPC matching '{npc_ref}' found in organization '{group.key}'.")
            return
            
        # First remove from current position
        for current_pos, members in group.db.hierarchy.items():
            if str(npc.id) in members:
                members.remove(str(npc.id))
                # Remove empty positions
                if not members:
                    del group.db.hierarchy[current_pos]
                break
                
        # Now add to new position
        if position:
            if position not in group.db.hierarchy:
                group.db.hierarchy[position] = []
            group.db.hierarchy[position].append(str(npc.id))
            
            # Update the position in the NPC data
            group.db.npcs[str(npc.id)]['position'] = position
            
            self.caller.msg(f"Set {npc.key}'s position in {group.key} to: {position}")
        else:
            # If position is empty, just remove from hierarchy
            if 'position' in group.db.npcs[str(npc.id)]:
                del group.db.npcs[str(npc.id)]['position']
                
            self.caller.msg(f"Removed {npc.key}'s position in {group.key}.")
    
    def add_goal(self):
        """Add a goal to a group"""
        args = self.args.strip()
        
        if not args or "=" not in args:
            self.caller.msg("Usage: +organization/addgoal <group>=<goal text>")
            return
            
        # Parse arguments
        group_name, goal_text = args.split("=", 1)
        group_name = group_name.strip()
        goal_text = goal_text.strip()
        
        if not goal_text:
            self.caller.msg("Goal text cannot be empty.")
            return
            
        # Search for the group
        group = self.caller.search(group_name, global_search=True)
        if not group or not isinstance(group, NPCGroup):
            self.caller.msg(f"'{group_name}' is not a valid NPC group.")
            return
            
        # Initialize goals list if needed
        if not group.db.goals:
            group.db.goals = []
            
        # Add the goal
        group.db.goals.append(goal_text)
        
        self.caller.msg(f"Added goal to {group.key}: {goal_text}")
    
    def remove_goal(self):
        """Remove a goal from a group"""
        args = self.args.strip()
        
        if not args or "=" not in args:
            self.caller.msg("Usage: +organization/remgoal <group>=<goal number>")
            return
            
        # Parse arguments
        group_name, goal_num_str = args.split("=", 1)
        group_name = group_name.strip()
        
        try:
            goal_num = int(goal_num_str.strip())
        except ValueError:
            self.caller.msg("Goal number must be a number.")
            return
            
        # Search for the group
        group = self.caller.search(group_name, global_search=True)
        if not group or not isinstance(group, NPCGroup):
            self.caller.msg(f"'{group_name}' is not a valid NPC group.")
            return
            
        # Check if goals exist
        if not group.db.goals:
            self.caller.msg(f"{group.key} has no goals.")
            return
            
        # Validate goal number
        if goal_num < 1 or goal_num > len(group.db.goals):
            self.caller.msg(f"Invalid goal number. {group.key} has {len(group.db.goals)} goals.")
            return
            
        # Remove the goal
        removed_goal = group.db.goals.pop(goal_num - 1)
        
        self.caller.msg(f"Removed goal from {group.key}: {removed_goal}")
    
    def summon_group(self):
        """Bring all group NPCs to the caller's location"""
        if not self.args:
            self.caller.msg("Usage: +organization/summon <group>")
            return
            
        # Search for the group
        group = self.caller.search(self.args, global_search=True)
        if not group or not isinstance(group, NPCGroup):
            self.caller.msg(f"'{self.args}' is not a valid NPC group.")
            return
            
        # Get NPCs in the group
        npcs = group.get_all_npcs()
        if not npcs:
            self.caller.msg(f"{group.key} has no NPCs.")
            return
            
        # Move NPCs to the caller's location
        count = 0
        for npc in npcs:
            if npc.move_to(self.caller.location, quiet=True):
                count += 1
                
        if count:
            self.caller.msg(f"Summoned {count} NPCs from {group.key} to your location.")
            
            # Announce to the room
            self.caller.location.msg_contents(
                f"{self.caller.name} has summoned {count} NPCs from {group.key}.",
                exclude=[self.caller]
            )
        else:
            self.caller.msg(f"Failed to summon NPCs from {group.key}.")
    
    def recall_group(self):
        """Move all group NPCs back to the group's location"""
        if not self.args:
            self.caller.msg("Usage: +organization/recall <group>")
            return
            
        # Search for the group
        group = self.caller.search(self.args, global_search=True)
        if not group or not isinstance(group, NPCGroup):
            self.caller.msg(f"'{self.args}' is not a valid NPC group.")
            return
            
        # Verify group has a location
        if not group.location:
            self.caller.msg(f"{group.key} has no location to recall NPCs to.")
            return
            
        # Get NPCs in the group
        npcs = group.get_all_npcs()
        if not npcs:
            self.caller.msg(f"{group.key} has no NPCs.")
            return
            
        # Move NPCs to the group's location
        count = 0
        for npc in npcs:
            if npc.move_to(group.location, quiet=True):
                count += 1
                
        if count:
            self.caller.msg(f"Recalled {count} NPCs from {group.key} to {group.location.name}.")
            
            # Announce to the room if needed
            if self.caller.location != group.location:
                self.caller.location.msg_contents(
                    f"{self.caller.name} has recalled {count} NPCs from {group.key}.",
                    exclude=[self.caller]
                )
        else:
            self.caller.msg(f"Failed to recall NPCs from {group.key}.") 