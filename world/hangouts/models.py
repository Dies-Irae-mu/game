"""
Hangouts system for listing and managing hangout locations.
Provides utility functions for managing and querying hangouts.
"""

from evennia.objects.models import ObjectDB

# Categories for hangout locations
HANGOUT_CATEGORIES = [
    "Art", "Business", "Government", "Club", "Education", 
    "Entertainment", "Gastronomy", "Health", "Landmarks",
    "Lodging", "Outdoors", "Religious", "Social", "Sports",
    "Store", "Transportation", "Faction", "Supernatural", "Vice"
]

class HangoutDB(ObjectDB):
    """
    Database model for hangout locations.
    """
    class Meta:
        proxy = True

    @classmethod
    def _get_next_hangout_id(cls):
        """
        Get the next available hangout ID.
        """
        hangouts = cls.get_all_hangouts()
        if not hangouts:
            return 1
        
        # Get all hangout_ids, including None values
        existing_ids = [h.db.hangout_id for h in hangouts]
        # Filter out None values and get max
        valid_ids = [id for id in existing_ids if id is not None]
        if not valid_ids:
            return 1
            
        return max(valid_ids) + 1

    @classmethod
    def create(cls, key, room, category, district, description, restricted=False, 
              required_splats=None, required_merits=None, required_factions=None):
        """
        Create a new hangout entry.
        
        Args:
            key (str): Name of the hangout
            room (Room): The room object this hangout represents
            category (str): Category from HANGOUT_CATEGORIES
            district (str): District/area name
            description (str): Short description for listings
            restricted (bool): Whether this is a restricted hangout
            required_splats (list): List of splat types that can see this
            required_merits (list): List of merits required
            required_factions (list): List of factions that can see this
            
        Returns:
            HangoutDB: The created hangout object
        """
        # Import create utility here to avoid circular imports
        from evennia.utils import create
        
        # Get the next available hangout ID
        next_id = cls._get_next_hangout_id()
        
        hangout = create.create_object(
            typeclass="typeclasses.hangouts.Hangout",
            key=key,
            attributes=[
                ("hangout_id", next_id),  # Store our custom sequential ID
                ("category", category),
                ("district", district),
                ("description", description),
                ("restricted", restricted),
                ("required_splats", required_splats or []),
                ("required_merits", required_merits or []),
                ("required_factions", required_factions or []),
                ("room", room),
                ("active", True)
            ]
        )
        return hangout

    def get_display_entry(self, show_restricted=False):
        """
        Get the display entry for this hangout.
        
        Args:
            show_restricted (bool): Whether to show the restricted marker
            
        Returns:
            tuple: (number, info_line, description_line)
        """
        # Ensure we have a hangout_id
        if self.db.hangout_id is None:
            self._migrate_to_hangout_id()
        
        # Get the hangout_id (this should never be None now)
        hangout_id = self.db.hangout_id
        
        restricted_marker = "*" if self.db.restricted and show_restricted else " "
        name = self.key
        
        # Count players in location
        location = self.db.room
        if location:
            player_count = len([obj for obj in location.contents if obj.has_account])
        else:
            player_count = 0
            
        info_line = f"{restricted_marker}{name}".ljust(55) + str(player_count)
        desc_line = f"    {self.db.description}"
        
        return (hangout_id, info_line, desc_line)

    @classmethod
    def get_all_hangouts(cls):
        """
        Get all hangout objects in the game.
        
        Returns:
            QuerySet: QuerySet of all Hangout objects
        """
        return cls.objects.filter(db_typeclass_path="typeclasses.hangouts.Hangout")

    def _migrate_to_hangout_id(self):
        """
        Migrate this hangout to use the new hangout_id system if it doesn't already.
        """
        if self.db.hangout_id is None:
            self.db.hangout_id = self._get_next_hangout_id()

    @classmethod
    def migrate_old_hangouts(cls):
        """
        Migrate existing hangouts to use the new typeclass and ID system.
        This should be run once after setting up the new system.
        Forces reassignment of all hangout IDs to ensure sequential ordering.
        """
        # First update typeclass paths
        old_hangouts = ObjectDB.objects.filter(db_typeclass_path__contains="hangouts")
        count = old_hangouts.update(db_typeclass_path="typeclasses.hangouts.Hangout")
        
        # Get all hangouts and sort by their current ID to maintain relative ordering
        all_hangouts = sorted(cls.get_all_hangouts(), key=lambda x: x.id)
        current_id = 1
        
        # Force reassign all IDs sequentially
        for hangout in all_hangouts:
            hangout.attributes.add("hangout_id", current_id)
            current_id += 1
        
        return len(all_hangouts)  # Return total number of hangouts processed

    @classmethod
    def get_by_hangout_id(cls, hangout_id):
        """
        Get a hangout by its hangout_id.
        
        Args:
            hangout_id (int): The hangout ID to look for
            
        Returns:
            HangoutDB: The hangout object or None if not found
        """
        try:
            hangout_id = int(hangout_id)
            hangouts = cls.get_all_hangouts()
            return next((h for h in hangouts if h.db.hangout_id == hangout_id), None)
        except (ValueError, TypeError):
            return None

    @classmethod
    def get_visible_hangouts(cls, character=None):
        """
        Get all hangouts visible to a specific character.
        
        Args:
            character: The character to check visibility for
            
        Returns:
            list: List of Hangout objects visible to the character
        """
        all_hangouts = cls.get_all_hangouts()
        
        # Filter hangouts based on visibility
        visible_hangouts = []
        for hangout in all_hangouts:
            # Skip inactive hangouts
            if not hangout.db.active:
                continue
                
            # If no character is checking, only show unrestricted hangouts
            if not character and not hangout.db.restricted:
                visible_hangouts.append(hangout)
                continue
                
            # If character is checking, check their permissions
            if character:
                # Staff can see all hangouts
                if character.check_permstring("builders") or character.check_permstring("wizards"):
                    visible_hangouts.append(hangout)
                    continue
                    
                # For restricted hangouts, check if character meets requirements
                if hangout.db.restricted:
                    # Check splat requirements
                    if hangout.db.required_splats:
                        char_splat = character.db.splat if hasattr(character.db, 'splat') else None
                        if not char_splat or char_splat not in hangout.db.required_splats:
                            continue
                            
                    # Check merit requirements
                    if hangout.db.required_merits:
                        char_merits = character.db.merits if hasattr(character.db, 'merits') else []
                        if not any(merit in char_merits for merit in hangout.db.required_merits):
                            continue
                            
                    # Check faction requirements
                    if hangout.db.required_factions:
                        char_faction = character.db.faction if hasattr(character.db, 'faction') else None
                        if not char_faction or char_faction not in hangout.db.required_factions:
                            continue
                
                # If we got here, the character can see this hangout
                visible_hangouts.append(hangout)
                
        # Sort by hangout_id
        return sorted(visible_hangouts, key=lambda x: x.db.hangout_id or 0)

    @classmethod
    def get_hangouts_by_category(cls, category, character=None):
        """
        Get all hangouts in a specific category visible to a character.
        
        Args:
            category (str): One of HANGOUT_CATEGORIES
            character: The character to check visibility for
            
        Returns:
            list: List of Hangout objects in the category visible to the character
        """
        if category not in HANGOUT_CATEGORIES:
            raise ValueError(f"Invalid category: {category}")
            
        visible_hangouts = cls.get_visible_hangouts(character)
        return [h for h in visible_hangouts if h.db.category == category] 