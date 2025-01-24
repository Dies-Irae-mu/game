"""
Typeclass for hangout locations.
"""

from evennia.objects.objects import DefaultObject

HANGOUT_CATEGORIES = [
    "Art", "Business", "Government", "Club", "Education", 
    "Entertainment", "Gastronomy", "Health", "Landmarks",
    "Lodging", "Outdoors", "Religious", "Social", "Sports",
    "Store", "Transportation", "Faction", "Supernatural", "Vice"
]

class Hangout(DefaultObject):
    """
    A hangout location that can be listed in the directory.
    """
    
    def at_object_creation(self):
        """Called when object is first created."""
        super().at_object_creation()
        
        # Basic properties
        self.db.category = None  # One of HANGOUT_CATEGORIES
        self.db.district = None  # Geographic district/area name
        self.db.description = ""  # Short description for listings
        self.db.restricted = False  # Whether this is a restricted/hidden hangout
        self.db.required_splats = []  # List of splat types that can see this hangout
        self.db.required_merits = []  # List of merits required to see this hangout
        self.db.required_factions = []  # List of factions that can see this hangout
        self.db.active = True  # Whether this hangout is currently active/visible
        self.db.room = None  # The room this hangout represents
        
    def at_server_reload(self):
        """
        Called when server reloads. We need to handle this to properly
        restore the typeclass on existing objects.
        """
        return super().at_server_reload()
        
    def can_see(self, character):
        """
        Check if a character can see this hangout.
        
        Args:
            character: The character to check
            
        Returns:
            bool: Whether the character can see this hangout
        """
        if not self.db.restricted:
            return True
            
        if not character:
            return False
            
        # Check splat requirements
        if self.db.required_splats:
            char_splat = character.db.stats.get("splat") if hasattr(character.db, "stats") else None
            if not char_splat or char_splat not in self.db.required_splats:
                return False
                
        # Check merit requirements
        if self.db.required_merits:
            char_merits = character.db.stats.get("merits", []) if hasattr(character.db, "stats") else []
            if not any(merit in char_merits for merit in self.db.required_merits):
                return False
                
        # Check faction requirements
        if self.db.required_factions:
            char_faction = character.db.stats.get("faction") if hasattr(character.db, "stats") else None
            if not char_faction or char_faction not in self.db.required_factions:
                return False
                
        return True
        
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
            Hangout: The created hangout object
        """
        from evennia.utils.create import create_object
        
        hangout = create_object(
            cls,
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