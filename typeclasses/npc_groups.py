"""
NPC Groups for the World of Darkness 20th Edition.

This module contains the NPCGroup typeclass which represents collections of NPCs
that form organizations like gangs, cabals, coteries, packs, etc.

NPCGroup objects store references to multiple NPCs and provide utilities for
managing and interacting with these NPCs as a cohesive unit.
"""

from evennia.objects.objects import DefaultObject
from typeclasses.npcs import NPC
import random
import uuid
from datetime import datetime

class NPCGroup(DefaultObject):
    """
    An object representing a group of NPCs such as a gang, cabal, coterie, etc.
    
    This object stores references to multiple NPCs and provides functionality
    for managing them as a group. NPCs can be created directly from this group
    or existing NPCs can be added to it.
    
    The group maintains metadata about its overall structure, hierarchy, and
    purpose, allowing storytellers to easily deploy pre-made groups of antagonists
    or allies for scenes.
    """
    
    def at_object_creation(self):
        """Called when the object is first created."""
        super().at_object_creation()
        
        # Initialize basic properties
        self.db.group_id = str(uuid.uuid4())  # Unique ID for this group
        self.db.creation_time = datetime.now()
        self.db.creator = None
        self.db.group_type = "Generic"  # e.g., Gang, Cabal, Coterie, Pack
        self.db.splat = "mortal"  # Default splat type for NPCs in this group
        self.db.difficulty = "MEDIUM"  # Default difficulty for NPCs
        
        # Group info
        self.db.description = ""  # Group description
        self.db.territory = ""  # Territory or domain
        self.db.resources = 0  # Resources level (0-5)
        self.db.influence = 0  # Influence level (0-5)
        self.db.goals = []  # List of group goals
        
        # NPC storage
        self.db.npcs = {}  # Map of NPC IDs to NPC objects
        self.db.hierarchy = {}  # Map of positions to NPC IDs
        self.db.npc_counter = 0  # Counter for assigning group member numbers
        
        # Lock settings
        self.locks.add("control:perm(Builder) or perm(Storyteller) or perm(Admin);examine:perm(Builder) or perm(Storyteller) or perm(Admin);edit:perm(Builder) or perm(Storyteller) or perm(Admin)")
        
        # Create database entry
        self.create_db_model()

    def create_db_model(self):
        """
        Create a database model for this NPC group.
        Called after the object is created to ensure it's registered in the database.
        """
        try:
            # Defer import to avoid circular import issues
            from evennia.utils.utils import lazy_import
            npc_manager_utils = lazy_import("world.npc_manager.utils")
            
            # Create the database entry
            group_model, created = npc_manager_utils.get_or_create_group_model(self)
            if created:
                pass  # Could log success here if needed
        except Exception as e:
            from evennia.utils import logger
            logger.log_err(f"Error creating database model for NPC group {self.key}: {str(e)}")
    
    # Override the default create method to ensure database entry is created
    @classmethod
    def create(cls, *args, **kwargs):
        """Create a new NPC Group object with database entry."""
        new_group = super(NPCGroup, cls).create(*args, **kwargs)
        
        # Ensure the database model is created
        if new_group:
            new_group.create_db_model()
            
        return new_group
        
    def add_npc(self, npc, position=None):
        """
        Add an existing NPC to the group.
        
        Args:
            npc (NPC): The NPC object to add to the group
            position (str, optional): The position/role in the group hierarchy
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        if not npc or not hasattr(npc, 'db') or not hasattr(npc, 'is_npc') or not npc.is_npc:
            return False
            
        # Add to group's NPC registry
        self.db.npc_counter += 1
        npc.db.group_number = self.db.npc_counter
        
        # Store NPC in our registry
        self.db.npcs[str(npc.id)] = {
            'object': npc,
            'position': position,
            'group_number': self.db.npc_counter,
            'added_time': datetime.now()
        }
        
        # Set NPC's group reference
        npc.db.npc_group = self
        npc.db.npc_group_id = self.db.group_id
        
        # Add to hierarchy if position specified
        if position:
            if position not in self.db.hierarchy:
                self.db.hierarchy[position] = []
            self.db.hierarchy[position].append(str(npc.id))
        
        # Update database model if it exists
        try:
            # Defer import to avoid circular import issues
            from evennia.utils.utils import lazy_import
            npc_manager_utils = lazy_import("world.npc_manager.utils")
            
            # Ensure NPC has a database entry
            npc_model, _ = npc_manager_utils.get_or_create_npc_model(npc)
        except Exception:
            pass
            
        return True
    
    def remove_npc(self, npc_id):
        """
        Remove an NPC from the group.
        
        Args:
            npc_id: The ID (as string) or the NPC object to remove
            
        Returns:
            bool: True if removed successfully, False otherwise
        """
        # Convert NPC object to ID string if needed
        if hasattr(npc_id, 'id'):
            npc_id = str(npc_id.id)
            
        # Check if NPC exists in group
        if npc_id not in self.db.npcs:
            return False
            
        # Get NPC data and object
        npc_data = self.db.npcs[npc_id]
        npc = npc_data.get('object')
        position = npc_data.get('position')
        
        # Remove from hierarchy
        if position and position in self.db.hierarchy:
            if npc_id in self.db.hierarchy[position]:
                self.db.hierarchy[position].remove(npc_id)
            # Clean up empty positions
            if not self.db.hierarchy[position]:
                del self.db.hierarchy[position]
        
        # Remove from NPC registry
        del self.db.npcs[npc_id]
        
        # Remove group reference from NPC if it still exists
        if npc and hasattr(npc, 'db'):
            npc.db.npc_group = None
            npc.db.npc_group_id = None
            
        return True
    
    def create_npc(self, name=None, splat=None, difficulty=None, position=None):
        """
        Create a new NPC and add to the group.
        
        Args:
            name (str, optional): The name for the NPC
            splat (str, optional): The splat type, defaults to group's splat
            difficulty (str, optional): Difficulty level, defaults to group's
            position (str, optional): Position in the group
            
        Returns:
            NPC: The created NPC object, or None if creation failed
        """
        try:
            # Use group defaults if not specified
            if not splat:
                splat = self.db.splat
            if not difficulty:
                difficulty = self.db.difficulty
                
            # Create the NPC
            from typeclasses.npcs import NPC
            
            # If no name is provided, we'll generate a random one
            if not name:
                # Name generation logic would go here
                # For now, just use a placeholder
                name = f"{self.key} Member #{self.db.npc_counter+1}"
            
            # Create the NPC in the same location as the group
            npc = NPC.create(
                key=name,
                location=self.location,
                attributes=[
                    ("desc", f"A {splat} NPC member of {self.key}."),
                ],
            )
            
            # Initialize with specified splat and difficulty
            npc.initialize_npc_stats(splat, difficulty)
            
            # Set as permanent NPC and set creator
            npc.db.is_temporary = False
            npc.db.creator = self.db.creator
            
            # Add to this group
            self.add_npc(npc, position)
            
            return npc
            
        except Exception as e:
            from evennia.utils import logger
            logger.log_err(f"Error creating NPC for group {self.key}: {str(e)}")
            return None
    
    def create_npcs_batch(self, count, splat=None, difficulty=None, prefix=None, positions=None):
        """
        Create multiple NPCs at once.
        
        Args:
            count (int): Number of NPCs to create
            splat (str, optional): Splat type for all NPCs
            difficulty (str, optional): Difficulty level
            prefix (str, optional): Name prefix for generated NPCs
            positions (list, optional): List of positions to assign in order
            
        Returns:
            list: List of created NPC objects
        """
        npcs = []
        
        for i in range(count):
            position = None
            if positions and i < len(positions):
                position = positions[i]
                
            # Create name with prefix if provided
            if prefix:
                name = f"{prefix} {i+1}"
            else:
                name = None
                
            npc = self.create_npc(name, splat, difficulty, position)
            if npc:
                npcs.append(npc)
                
        return npcs
    
    def get_npc_by_position(self, position):
        """
        Get all NPCs with a specific position.
        
        Args:
            position (str): The position to search for
            
        Returns:
            list: List of NPC objects with that position
        """
        npcs = []
        if position in self.db.hierarchy:
            for npc_id in self.db.hierarchy[position]:
                npc_data = self.db.npcs.get(npc_id)
                if npc_data and npc_data.get('object'):
                    npcs.append(npc_data['object'])
        return npcs
    
    def get_npc_by_name(self, name):
        """
        Find an NPC in the group by name (partial match).
        
        Args:
            name (str): Full or partial name to search for
            
        Returns:
            NPC or None: Matching NPC object if found
        """
        name = name.lower()
        for npc_id, npc_data in self.db.npcs.items():
            npc = npc_data.get('object')
            if npc and hasattr(npc, 'key') and name in npc.key.lower():
                return npc
        return None
    
    def get_npc_by_group_number(self, group_number):
        """
        Find an NPC by their group member number.
        
        Args:
            group_number (int): The member number to search for
            
        Returns:
            NPC or None: Matching NPC object if found
        """
        try:
            group_number = int(group_number)
            for npc_id, npc_data in self.db.npcs.items():
                if npc_data.get('group_number') == group_number:
                    return npc_data.get('object')
        except ValueError:
            pass
        return None
    
    def get_all_npcs(self):
        """
        Get all NPCs in this group.
        
        Returns:
            list: List of all NPC objects in the group
        """
        return [data.get('object') for data in self.db.npcs.values() 
                if data.get('object')]
    
    def bring_to_location(self, location):
        """
        Move all NPCs in the group to a specific location.
        
        Args:
            location: The location to move NPCs to
            
        Returns:
            int: Number of NPCs successfully moved
        """
        count = 0
        for npc in self.get_all_npcs():
            if npc.move_to(location, quiet=True):
                count += 1
        return count
    
    def return_appearance(self, looker, **kwargs):
        """
        This formats a description. It is the hook a 'look' command
        should call.
        """
        if not looker:
            return ""
            
        # Start with the name
        string = f"|c{self.get_display_name(looker)}|n\n"

        # Get and format the description
        desc = self.db.desc
        if desc:
            string += f"{desc}\n"
            
        # Basic group info
        string += f"\n|wGroup Type:|n {self.db.group_type}\n"
        string += f"|wSplat:|n {self.db.splat.capitalize()}\n"
        string += f"|wTerritory:|n {self.db.territory or 'None'}\n"
        string += f"|wResources:|n {'●' * self.db.resources}\n"
        string += f"|wInfluence:|n {'●' * self.db.influence}\n"
        
        # Show goals if any
        if self.db.goals:
            string += "\n|wGoals:|n\n"
            for i, goal in enumerate(self.db.goals, 1):
                string += f"{i}. {goal}\n"
        
        # Show hierarchy
        if self.db.hierarchy:
            string += "\n|wHierarchy:|n\n"
            for position, members in self.db.hierarchy.items():
                string += f"|c{position}:|n "
                names = []
                for npc_id in members:
                    npc_data = self.db.npcs.get(npc_id)
                    if npc_data and npc_data.get('object'):
                        names.append(npc_data['object'].key)
                string += ", ".join(names) + "\n"
        
        # Show NPCs in the group
        npcs = self.get_all_npcs()
        if npcs:
            string += f"\n|wMembers ({len(npcs)}):|n\n"
            for npc in npcs:
                position = ""
                for pos, members in self.db.hierarchy.items():
                    if str(npc.id) in members:
                        position = f" - {pos}"
                        break
                string += f"  |w{npc.key}|n{position}\n"
                
        return string 