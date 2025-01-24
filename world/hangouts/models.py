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
        
        hangout = create.create_object(
            typeclass="typeclasses.hangouts.Hangout",
            key=key,
            attributes=[
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

    @classmethod
    def migrate_old_hangouts(cls):
        """
        Migrate existing hangouts to use the new typeclass.
        This should be run once after setting up the new typeclass system.
        """
        # Find all objects that were using the old model
        old_hangouts = ObjectDB.objects.filter(db_typeclass_path__contains="hangouts")
        
        # Update them to use the new typeclass
        count = old_hangouts.update(db_typeclass_path="typeclasses.hangouts.Hangout")
        
        return count

    def get_display_entry(self, show_restricted=False):
        """
        Get the display entry for this hangout.
        
        Args:
            show_restricted (bool): Whether to show the restricted marker
            
        Returns:
            tuple: (number, info_line, description_line)
        """
        number = self.id
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
        
        return (number, info_line, desc_line)

    @classmethod
    def get_all_hangouts(cls):
        """
        Get all hangout objects in the game.
        
        Returns:
            QuerySet: QuerySet of all Hangout objects
        """
        return cls.objects.filter(db_typeclass_path="typeclasses.hangouts.Hangout")

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
        if not character:
            return [h for h in all_hangouts if not h.db.restricted and h.db.active]
        return [h for h in all_hangouts if h.can_see(character) and h.db.active]

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