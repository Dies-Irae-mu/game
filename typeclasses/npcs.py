# Diesirae/typeclasses/npcs.py
"""
NPCs for the World of Darkness 20th Edition.

NPCs are objects that can be accessed in the game world and are either created by the NPC generator as temporary
objects, or staff can create them as permanent objects. 

Players create temporary NPCs using the +init command, which is designed primarily to develop NPCs for 
combat or other short-term goals/plots. These NPCs have a lifespan of 48 hours, after which they will be 
automatically deleted.

Staff can create permanent NPCs using the +npc command, which is designed to create NPCs for the long-term.

NPCs do not have the same stat structure as players; if the NPC is created by the +init system or by staff using +npc/random
the NPC will be given a random stat block based on the difficulty setting. 

Staff (admin, builders, developer permissions) or player storytellers (Storyteller permissions) can "inhabit" NPCs, allowing the
player to control the NPC's actions, dialogue, rolls, and other aspects just as they would a player character.

Staff creating special NPCs for the game world can use the +staffstat command to set the NPC's stats. These sorts of characters are
intended to be major characters in the game, such as major antagonists, the Werewolf Sept Alpha, the Sabbat Archbishop, the Camarilla Prince,
etc.

They do not show up on the characters list on the wiki, and are not available for players to inhabit.

Temporary NPCs can be forced to roll or emit with the +npc command. Both commands creates an object in the gameworld which is stored in a specific
room, able to be viewed by players and staff.

"""
from datetime import datetime, timedelta
from evennia.objects.objects import DefaultCharacter
from evennia import create_script, utils
from evennia.locks.lockhandler import LockException
from evennia.utils.utils import inherits_from
import uuid
import random
from evennia.typeclasses.attributes import AttributeProperty


class NPC(DefaultCharacter):
    """
    A base class for all NPCs.
    """
    # Make is_npc a queryable property
    is_npc = AttributeProperty(True, autocreate=True)

    def at_object_creation(self):
        """
        Called when object is first created.
        """
        super().at_object_creation()
        
        # Initialize NPC properties
        self.db.is_npc = True
        self.db.is_temporary = False
        self.db.creator = None
        self.db.inhabited_by = None
        self.db.creation_time = datetime.now()
        self.db.expiration_time = None
        self.db.npc_number = None
        
        # Create a unique NPC ID using UUID - this will be consistent across restarts
        self.db.npc_id = str(uuid.uuid4())
        
        # Initialize tracking for which rooms this NPC is registered in
        self.db.registered_in_rooms = set()
        
        # Store the dbref as a string for easier reference - use a distinct format
        self.db.dbref_str = f"#NPC{self.id}"
        
        # Initialize basic stats as a mortal
        self.initialize_npc_stats("mortal", "LOW")
        
        # Set default lock for who can control this NPC
        self.locks.add("control:perm(Builder) or perm(Storyteller) or perm(Admin);call:all()")
        
        # Initialize speaking language to English
        self.db.speaking_language = "English"
        self.db.languages = ["English"]

        # Create database entry for this NPC
        self.create_db_model()

    def create_db_model(self):
        """
        Create a database model for this NPC.
        Called after the object is created to ensure it's registered in the database.
        """
        try:
            # Defer import to avoid circular import issues
            from evennia.utils.utils import lazy_import
            npc_manager_utils = lazy_import("world.npc_manager.utils")
            
            # Create the database entry
            npc_model, created = npc_manager_utils.get_or_create_npc_model(self)
            if created:
                pass  # Could log success here if needed
        except Exception as e:
            from evennia.utils import logger
            logger.log_err(f"Error creating database model for NPC {self.key}: {str(e)}")

    def at_cmdset_creation(self):
        """
        Override to prevent NPCs from inheriting character commands.
        This prevents command duplication in rooms with NPCs.
        """
        # Don't call super() to avoid inheriting player character commands
        # Any NPC-specific commands would be added here
        pass

    def initialize_npc_stats(self, splat_type="mortal", difficulty="LOW"):
        """
        Initialize NPC stats based on splat type and difficulty.
        
        Args:
            splat_type (str): Type of character (mortal, vampire, mage, shifter, etc.)
            difficulty (str): Difficulty level (LOW, MEDIUM, HIGH)
        """
        # Validate inputs
        splat_type = splat_type.lower()
        difficulty = difficulty.upper()
        
        # Default point allocations based on difficulty
        point_allocations = {
            "LOW": {
                "attributes": 15,
                "abilities": 20,
                "disciplines": 3,
                "gifts": 3,
                "spheres": 4,
                "numina": 5,
                "charms": 5,
                "willpower": 3,
                "rage": 2,
                "gnosis": 2,
            },
            "MEDIUM": {
                "attributes": 20,
                "abilities": 30,
                "disciplines": 4,
                "gifts": 4,
                "spheres": 5,
                "numina": 7,
                "charms": 7,
                "willpower": 5,
                "rage": 4,
                "gnosis": 4,
            },
            "HIGH": {
                "attributes": 30,
                "abilities": 50,
                "disciplines": 5,
                "gifts": 5,
                "spheres": 6,
                "numina": 9,
                "charms": 9,
                "willpower": 7,
                "rage": 6,
                "gnosis": 6,
            }
        }
        
        # Make sure we have a valid difficulty level
        if difficulty not in point_allocations:
            difficulty = "MEDIUM"
        
        # Get points based on difficulty
        points = point_allocations[difficulty]
        
        # Create base stats structure
        stats = {
            "splat": splat_type,
            "difficulty": difficulty,
            "attributes": {
                "physical": {},
                "social": {},
                "mental": {}
            },
            "abilities": {},
            "powers": {},
            "backgrounds": {},
            "health": {
                "bashing": 0,
                "lethal": 0,
                "aggravated": 0
            },
            "willpower": points["willpower"]
        }
        
        # Initialize attributes with balanced distribution
        self._init_attributes(stats, points["attributes"])
        
        # Initialize abilities appropriate for the splat type
        self._init_abilities(stats, points["abilities"])
        
        # Initialize powers based on splat type
        self._init_powers(stats, splat_type, points)
        
        # Set the stats
        self.db.stats = stats
        
        return stats

    def _init_attributes(self, stats, total_points):
        """
        Initialize attributes for the NPC with a balanced distribution.
        
        Args:
            stats (dict): The stats dictionary to update
            total_points (int): Total attribute points to distribute
        """
        # Define attribute categories
        categories = {
            "physical": ["strength", "dexterity", "stamina"],
            "social": ["charisma", "manipulation", "appearance"],
            "mental": ["perception", "intelligence", "wits"]
        }
        
        # Distribute points evenly among categories
        points_per_category = total_points // 3
        remainder = total_points % 3
        
        for category, attributes in categories.items():
            # Create category if it doesn't exist
            if category not in stats["attributes"]:
                stats["attributes"][category] = {}
            
            # Add extra point if there's a remainder
            category_points = points_per_category
            if remainder > 0:
                category_points += 1
                remainder -= 1
            
            # Distribute points within category
            for attr in attributes:
                # All attributes start at 1
                value = 1
                # Randomly distribute remaining points
                if category_points > 0:
                    # Minimum of 1, maximum of 5 for NPC attributes
                    attr_points = min(random.randint(0, category_points), 4)
                    value += attr_points
                    category_points -= attr_points
                
                stats["attributes"][category][attr] = value

    def _init_abilities(self, stats, total_points):
        """
        Initialize abilities for the NPC.
        
        Args:
            stats (dict): The stats dictionary to update
            total_points (int): Total ability points to distribute
        """
        # Define ability categories and abilities
        abilities = {
            "talents": [
                "alertness", "athletics", "awareness", "brawl", "empathy",
                "expression", "intimidation", "leadership", "streetwise", "subterfuge"
            ],
            "skills": [
                "animal_ken", "crafts", "drive", "etiquette", "firearms",
                "melee", "performance", "security", "stealth", "survival"
            ],
            "knowledges": [
                "academics", "computer", "finance", "investigation", "law",
                "medicine", "occult", "politics", "science", "technology"
            ]
        }
        
        # Create abilities structure
        stats["abilities"] = {
            "talents": {},
            "skills": {},
            "knowledges": {}
        }
        
        # Determine how many abilities to give the NPC
        num_abilities = min(total_points // 2, 15)  # Roughly 2 points per ability
        
        # Randomly select abilities from all categories
        all_abilities = []
        for category, ability_list in abilities.items():
            all_abilities.extend([(category, ability) for ability in ability_list])
        
        selected_abilities = random.sample(all_abilities, num_abilities)
        
        # Distribute points to selected abilities
        remaining_points = total_points
        for category, ability in selected_abilities:
            # Assign 1-3 points per ability
            if remaining_points <= 0:
                break
                
            value = min(random.randint(1, 3), remaining_points)
            stats["abilities"][category][ability] = value
            remaining_points -= value

    def _init_powers(self, stats, splat_type, points):
        """
        Initialize supernatural powers based on splat type.
        
        Args:
            stats (dict): The stats dictionary to update
            splat_type (str): The type of supernatural character
            points (dict): Points to allocate to powers
        """
        # Initialize powers structure
        stats["powers"] = {}
        
        # Handle different splat types
        if splat_type == "vampire":
            self._init_vampire_powers(stats, points)
        elif splat_type == "mage":
            self._init_mage_powers(stats, points)
        elif splat_type == "shifter":
            self._init_shifter_powers(stats, points)
        elif splat_type == "psychic":
            self._init_psychic_powers(stats, points)
        elif splat_type == "spirit":
            self._init_spirit_powers(stats, points)
        # Other splat types can be added as needed
        
        # Every supernatural gets the basics
        if splat_type != "mortal":
            # Add some basic backgrounds
            stats["backgrounds"] = {
                "allies": random.randint(0, 2),
                "contacts": random.randint(1, 3),
                "resources": random.randint(0, 2)
            }

    def _init_vampire_powers(self, stats, points):
        """Initialize vampire disciplines."""
        # Common disciplines
        disciplines = [
            "potence", "auspex", "celerity", "dominate", "fortitude",
            "presence", "obfuscate", "animalism", "protean"
        ]
        
        # Rare disciplines
        rare_disciplines = [
            "thaumaturgy", "necromancy", "dementation", "chimerstry", 
            "serpentis", "vicissitude", "obtenebration"
        ]
        
        # Create discipline structure
        stats["powers"]["discipline"] = {}
        
        # Determine how many disciplines to give
        num_disciplines = min(points["disciplines"], 5)
        
        # Select disciplines - bias toward common ones
        selected_disciplines = []
        # Always include 1-2 common disciplines
        selected_disciplines.extend(random.sample(disciplines, min(2, num_disciplines)))
        
        # If we need more, add a mix of common and rare
        remaining = num_disciplines - len(selected_disciplines)
        if remaining > 0:
            # Combine remaining disciplines
            remaining_disciplines = disciplines + rare_disciplines
            # Remove already selected ones
            for disc in selected_disciplines:
                if disc in remaining_disciplines:
                    remaining_disciplines.remove(disc)
            # Select additional disciplines
            selected_disciplines.extend(random.sample(remaining_disciplines, remaining))
        
        # Distribute points among disciplines
        discipline_points = points["disciplines"] * 2  # Multiply for more points
        remaining_points = discipline_points
        
        for discipline in selected_disciplines:
            if remaining_points <= 0:
                break
                
            value = min(random.randint(1, 3), remaining_points)
            stats["powers"]["discipline"][discipline] = value
            remaining_points -= value
        
        # Add vampire-specific traits
        stats["blood_pool"] = 10
        stats["generation"] = random.randint(8, 13)  # Typically 8-13th generation

    def _init_mage_powers(self, stats, points):
        """Initialize mage spheres."""
        # All spheres
        spheres = [
            "correspondence", "forces", "life", "matter", "entropy",
            "mind", "spirit", "prime", "time"
        ]
        
        # Create sphere structure
        stats["powers"]["sphere"] = {}
        
        # Determine how many spheres to give
        num_spheres = min(points["spheres"], 5)
        
        # Select spheres
        selected_spheres = random.sample(spheres, num_spheres)
        
        # Distribute points among spheres
        sphere_points = points["spheres"] * 1.5  # Adjust for more points
        remaining_points = int(sphere_points)
        
        for sphere in selected_spheres:
            if remaining_points <= 0:
                break
                
            value = min(random.randint(1, 3), remaining_points)
            stats["powers"]["sphere"][sphere] = value
            remaining_points -= value
        
        # Add mage-specific traits
        stats["arete"] = random.randint(2, 4)
        stats["quintessence"] = stats["arete"]
        stats["paradox"] = 0

    def _init_shifter_powers(self, stats, points):
        """Initialize shifter gifts and traits."""
        # Create gift structure
        stats["powers"]["gift"] = {}
        
        # Add a few generic gifts
        generic_gifts = [
            "Smell of Man", "Heightened Senses", "Sense Wyrm", 
            "Resist Pain", "Wolf Sense", "Silent Running"
        ]
        
        selected_gifts = random.sample(generic_gifts, min(points["gifts"], len(generic_gifts)))
        
        for gift in selected_gifts:
            stats["powers"]["gift"][gift] = 1
        
        # Add shifter-specific traits
        stats["rage"] = points["rage"]
        stats["gnosis"] = points["gnosis"]
        stats["glory"] = random.randint(0, 3)
        stats["honor"] = random.randint(0, 3)
        stats["wisdom"] = random.randint(0, 3)

    def _init_psychic_powers(self, stats, points):
        """Initialize psychic numina."""
        # List of numina
        numina = [
            "Telepathy", "Psychokinesis", "Pyrokinesis", "Clairvoyance",
            "Precognition", "Teleportation", "Healing", "Empathy",
            "Astral Projection", "Mind Control"
        ]
        
        # Create numina structure
        stats["powers"]["numina"] = {}
        
        # Determine how many numina to give
        num_numina = min(points["numina"] // 2, len(numina))
        
        # Select numina
        selected_numina = random.sample(numina, num_numina)
        
        # Distribute points among numina
        numina_points = points["numina"]
        remaining_points = numina_points
        
        for numen in selected_numina:
            if remaining_points <= 0:
                break
                
            value = min(random.randint(1, 3), remaining_points)
            stats["powers"]["numina"][numen] = value
            remaining_points -= value

    def _init_spirit_powers(self, stats, points):
        """Initialize spirit charms."""
        # List of common charms
        charms = [
            "Materialize", "Awe", "Fear", "Blast", "Armor",
            "Reform", "Peek", "Create Element", "Tracking",
            "Control Element", "Influence", "Possession"
        ]
        
        # Create charm structure
        stats["powers"]["charm"] = []
        
        # Determine how many charms to give
        num_charms = min(points["charms"], len(charms))
        
        # Always include Materialize for spirits
        selected_charms = ["Materialize"]
        
        # Add additional charms
        remaining_charms = [c for c in charms if c != "Materialize"]
        selected_charms.extend(random.sample(remaining_charms, num_charms - 1))
        
        # Store charms
        stats["powers"]["charm"] = selected_charms
        
        # Add spirit-specific traits
        stats["rank"] = random.randint(1, 3)
        stats["gnosis"] = points["gnosis"]
        stats["rage"] = points["rage"]
        stats["essence"] = random.randint(5, 15)

    def set_splat(self, splat_type, difficulty="MEDIUM"):
        """
        Change the NPC's splat type and reinitialize stats.
        
        Args:
            splat_type (str): The new splat type
            difficulty (str): The difficulty level
        
        Returns:
            bool: True if successful, False if invalid splat
        """
        valid_splats = ["mortal", "vampire", "mage", "shifter", "psychic", "spirit"]
        
        if splat_type.lower() not in valid_splats:
            return False
            
        # Reinitialize stats with new splat type
        self.initialize_npc_stats(splat_type, difficulty)
        
        # Update in all rooms where this NPC is registered
        self.update_stats_in_rooms()
        
        return True

    def update_stats_in_rooms(self):
        """Update stats in all rooms where this NPC is registered."""
        from evennia import search_object
        
        for room_dbref in self.db.registered_in_rooms:
            room = search_object(room_dbref)
            if room and len(room) > 0:
                room = room[0]
                if hasattr(room, "db_npcs") and self.key in room.db_npcs:
                    room.db_npcs[self.key]["stats"] = self.db.stats

    def set_as_temporary(self, creator, lifespan=48):
        """
        Set this NPC as temporary with specified lifespan.
        
        Args:
            creator (Object): The character who created this NPC
            lifespan (int): Lifespan in hours (default 48)
        """
        self.db.is_temporary = True
        self.db.creator = creator
        
        # Set expiration time
        expiration = datetime.now() + timedelta(hours=lifespan)
        self.db.expiration_time = expiration
        
        # Create a script to delete this NPC when expired
        create_script(
            "typeclasses.scripts.npc_scripts.NPCExpirationScript",
            key=f"npc_expiration_{self.id}",
            desc=f"Handles expiration of temporary NPC {self.name}",
            obj=self,
            interval=3600,  # Check every hour
            persistent=True,
            start_delay=True
        )
        
        # If this NPC is in a room, register it in the room's NPC tracker
        if self.location:
            self.register_in_room(self.location)
            
        return True

    def set_as_permanent(self):
        """Set this NPC as permanent (won't expire)."""
        self.db.is_temporary = False
        self.db.expiration_time = None
        
        # Stop any expiration scripts
        for script in self.scripts.get("NPCExpirationScript"):
            script.stop()
            
        return True
    
    def register_in_room(self, room):
        """
        Register this NPC in a room's NPC tracker.
        
        Args:
            room (Object): The room to register in
        """
        if not room:
            return False
            
        # Initialize room's NPC list if needed
        if not hasattr(room, "db_npcs"):
            room.db_npcs = {}
            
        # Initialize room's NPC counter if needed
        if not hasattr(room, "db_npc_counter"):
            room.db_npc_counter = 0
            
        # Only increment counter if this NPC isn't already registered
        if self.key not in room.db_npcs:
            room.db_npc_counter += 1
            npc_number = room.db_npc_counter
            self.db.npc_number = npc_number
            
            # Add to room's NPC database
            room.db_npcs[self.key] = {
                "modifier": 0,  # Default initiative modifier
                "health": self.db.stats["health"],
                "number": npc_number,
                "stats": self.db.stats,
                "is_temporary": self.db.is_temporary,
                "creator": self.db.creator.key if self.db.creator else None,
                "npc_object": self,
                "npc_id": self.db.npc_id,
                "dbref": self.db.dbref_str
            }
            
            # Add room to NPC's registered rooms
            self.db.registered_in_rooms.add(room.dbref)
            
            return True
        return False
    
    def unregister_from_room(self, room):
        """
        Unregister this NPC from a room's NPC tracker.
        
        Args:
            room (Object): The room to unregister from
        """
        if not room or not hasattr(room, "db_npcs"):
            return False
            
        # Remove from room's NPC list
        if self.key in room.db_npcs:
            del room.db_npcs[self.key]
            
            # Remove from NPC's registered rooms
            if room.dbref in self.db.registered_in_rooms:
                self.db.registered_in_rooms.remove(room.dbref)
                
            return True
        return False

    def at_post_move(self, source_location, **kwargs):
        """Called after the NPC moves to a new location."""
        # Call parent method first
        super().at_post_move(source_location, **kwargs)
        
        # Unregister from the source location if it exists
        if source_location:
            self.unregister_from_room(source_location)
            
        # Register in the new location if it exists
        if self.location:
            self.register_in_room(self.location)

    def is_expired(self):
        """Check if this NPC has expired."""
        if not self.db.is_temporary:
            return False
            
        now = datetime.now()
        expiration = self.db.expiration_time
        
        return expiration and now > expiration

    def can_be_controlled_by(self, controller):
        """
        Check if this NPC can be controlled by the given character.
        
        Args:
            controller (Object): The character trying to control this NPC
            
        Returns:
            bool: True if allowed, False otherwise
        """
        # Staff and Storytellers can control any NPC
        if controller.check_permstring("Admin") or controller.check_permstring("Builder") or controller.check_permstring("Storyteller"):
            return True
            
        # Creator can control their own temporary NPCs
        if self.db.is_temporary and self.db.creator == controller:
            return True
            
        # Check custom lock
        try:
            return self.locks.check(controller, "control")
        except LockException:
            return False

    def inhabit(self, controller):
        """
        Allow a character to "inhabit" and control this NPC.
        
        Args:
            controller (Object): The character who will control this NPC
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.can_be_controlled_by(controller):
            return False
            
        # Check if already inhabited
        if self.db.inhabited_by and self.db.inhabited_by != controller:
            return False
            
        self.db.inhabited_by = controller
        
        # Update this in all rooms where this NPC is registered
        self.update_inhabited_status_in_rooms()
        
        return True

    def uninhabit(self, controller=None):
        """
        Stop a character from inhabiting this NPC.
        
        Args:
            controller (Object): The character to check (if None, uninhabit regardless)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if controller and self.db.inhabited_by != controller:
            return False
            
        self.db.inhabited_by = None
        
        # Update this in all rooms where this NPC is registered
        self.update_inhabited_status_in_rooms()
        
        return True
    
    def update_inhabited_status_in_rooms(self):
        """Update the inhabited status in all rooms where this NPC is registered."""
        from evennia import search_object
        
        for room_dbref in self.db.registered_in_rooms:
            room = search_object(room_dbref)
            if room and len(room) > 0:
                room = room[0]
                if hasattr(room, "db_npcs") and self.key in room.db_npcs:
                    room.db_npcs[self.key]["inhabited_by"] = self.db.inhabited_by.key if self.db.inhabited_by else None

    def get_display_name(self, looker, **kwargs):
        """
        Get the display name of the NPC, showing NPC status to staff.
        """
        if not looker or not looker.check_permstring("Builder"):
            return self.key
            
        # Show NPC status to staff
        temp_status = " (Temp)" if self.db.is_temporary else ""
        inhabited = f" [Inhabited by {self.db.inhabited_by.key}]" if self.db.inhabited_by else ""
        id_display = f" (NPC#{self.db.npc_number})" if self.db.npc_number else ""
        
        return f"{self.key}{id_display}{temp_status}{inhabited}"

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
            
        # For staff, show NPC stats
        if looker.check_permstring("Builder"):
            string += "\n|yNPC Information:|n\n"
            string += f"  |wSplat:|n {self.db.stats.get('splat', 'unknown').title()}\n"
            string += f"  |wDifficulty:|n {self.db.stats.get('difficulty', 'MEDIUM')}\n"
            string += f"  |wNPC ID:|n {self.db.npc_id}\n"
            string += f"  |wDBRef:|n {self.db.dbref_str}\n"
            string += f"  |wCreator:|n {self.db.creator.key if self.db.creator else 'N/A'}\n"
            
            # Show some basic stats
            if "attributes" in self.db.stats:
                string += "  |wKey Attributes:|n "
                attrs = []
                for category in ["physical", "social", "mental"]:
                    if category in self.db.stats["attributes"]:
                        for attr, val in self.db.stats["attributes"][category].items():
                            if val >= 3:  # Only show high attributes
                                attrs.append(f"{attr.title()}: {val}")
                string += ", ".join(attrs[:5]) + "\n"  # Limit to 5 attributes
                
            # Show supernatural powers if any
            if "powers" in self.db.stats:
                for power_type, powers in self.db.stats["powers"].items():
                    if powers:
                        string += f"  |w{power_type.title()}s:|n "
                        if isinstance(powers, dict):
                            power_list = [f"{p.title()}: {v}" for p, v in powers.items()]
                            string += ", ".join(power_list) + "\n"
                        elif isinstance(powers, list):
                            string += ", ".join([p for p in powers]) + "\n"
            
            if self.db.is_temporary:
                expiration = self.db.expiration_time
                if expiration:
                    now = datetime.now()
                    time_left = expiration - now
                    hours_left = max(0, time_left.total_seconds() / 3600)
                    string += f"  |wExpires:|n In {hours_left:.1f} hours\n"

        return string

    def at_pre_puppet(self, puppeteer, **kwargs):
        """
        Called just before a puppeting attempt. Can be used to limit puppeting.
        """
        # NPCs cannot be logged into directly
        return False

    def at_init(self):
        """
        Called when the typeclass is cached from memory.
        """
        # Check for expiration if this is a temporary NPC
        if getattr(self.db, "is_temporary", False) and self.is_expired():
            # Schedule deletion to happen after init completes
            from evennia.scripts.taskhandler import TaskHandlerPool
            TaskHandlerPool.add_task(self.delete, (), {}, priority=10)

    def at_object_delete(self):
        """Called just before the NPC is deleted from the database."""
        # Unregister from all rooms
        from evennia import search_object
        
        try:
            # Clear all command sets to make sure nothing persists
            try:
                self.cmdset.clear()
                self.cmdset.remove_default()
                # Also force-deactivate any custom command sets
                for cmdset in self.cmdset.get():
                    self.cmdset.remove(cmdset)
            except Exception as e:
                from evennia.utils import logger
                logger.log_err(f"Error clearing command sets for NPC {self.key}: {e}")
            
            # Get a safe copy of registered rooms
            registered_rooms = set(self.db.registered_in_rooms) if hasattr(self.db, "registered_in_rooms") else set()
            
            # Clear the attribute first in case something fails
            self.attributes.remove("registered_in_rooms")
            
            # Now try to unregister from each room
            for room_dbref in registered_rooms:
                try:
                    room = search_object(room_dbref)
                    if room and len(room) > 0:
                        room = room[0]
                        if hasattr(room, "db_npcs") and self.key in room.db_npcs:
                            del room.db_npcs[self.key]
                except Exception as e:
                    from evennia.utils import logger
                    logger.log_err(f"Error unregistering NPC {self.key} from room {room_dbref}: {e}")
                    # Continue to next room even if there's an error
                
            # Call parent method
            super().at_object_delete()
        except Exception as e:
            from evennia.utils import logger
            logger.log_err(f"Error in at_object_delete for NPC {self.key}: {e}")
            # Even if there's an error, try to call the parent method
            super().at_object_delete()

    def get_health_status(self):
        """Get a text representation of health status."""
        health = self.db.stats.get("health", {"bashing": 0, "lethal": 0, "aggravated": 0})
        total_damage = health['bashing'] + health['lethal'] + health['aggravated']
        
        if total_damage == 0:
            return "Healthy"
        elif total_damage <= 1:
            return "Bruised"
        elif total_damage <= 2:
            return "Hurt"
        elif total_damage <= 3:
            return "Injured"
        elif total_damage <= 4:
            return "Wounded"
        elif total_damage <= 5:
            return "Mauled"
        elif total_damage <= 6:
            return "Crippled"
        else:
            return "Incapacitated"

    def apply_damage(self, damage_type, amount):
        """
        Apply damage to the NPC.
        
        Args:
            damage_type (str): "bashing", "lethal", or "aggravated"
            amount (int): Amount of damage to apply
            
        Returns:
            str: New health status after damage
        """
        if damage_type not in ["bashing", "lethal", "aggravated"]:
            return self.get_health_status()
            
        # Ensure health dict exists
        if not self.db.stats.get("health"):
            self.db.stats["health"] = {"bashing": 0, "lethal": 0, "aggravated": 0}
            
        # Apply damage
        self.db.stats["health"][damage_type] += amount
        
        # Update health in all rooms where this NPC is registered
        self.update_health_in_rooms()
        
        # Check if NPC should be deleted due to incapacitation
        if self.db.is_temporary and self.get_health_status() == "Incapacitated":
            # Schedule deletion with a slight delay
            from evennia.scripts.taskhandler import TaskHandlerPool
            TaskHandlerPool.add_task(self.delete, (), {}, priority=10, delay=60)
            
        return self.get_health_status()
    
    def update_health_in_rooms(self):
        """Update health status in all rooms where this NPC is registered."""
        from evennia import search_object
        
        for room_dbref in self.db.registered_in_rooms:
            room = search_object(room_dbref)
            if room and len(room) > 0:
                room = room[0]
                if hasattr(room, "db_npcs") and self.key in room.db_npcs:
                    room.db_npcs[self.key]["health"] = self.db.stats["health"]

    def heal_damage(self, damage_type, amount):
        """
        Heal damage from the NPC.
        
        Args:
            damage_type (str): "bashing", "lethal", or "aggravated"
            amount (int): Amount of damage to heal
            
        Returns:
            str: New health status after healing
        """
        if damage_type not in ["bashing", "lethal", "aggravated"]:
            return self.get_health_status()
            
        # Ensure health dict exists
        if not self.db.stats.get("health"):
            self.db.stats["health"] = {"bashing": 0, "lethal": 0, "aggravated": 0}
            
        # Apply healing (minimum 0)
        self.db.stats["health"][damage_type] = max(0, self.db.stats["health"][damage_type] - amount)
        
        # Update health in all rooms where this NPC is registered
        self.update_health_in_rooms()
        
        return self.get_health_status()

    def get_language(self):
        """Get the NPC's currently speaking language."""
        return self.db.speaking_language or "English"

    def set_language(self, language):
        """Set the NPC's speaking language."""
        # Add the language to known languages if not already there
        if language not in self.db.languages:
            self.db.languages.append(language)
        self.db.speaking_language = language

    def at_say(self, message, msg_self=None, msg_location=None, receivers=None, **kwargs):
        """
        Called when the NPC speaks.
        This will prepend the NPC's name to show they are speaking.
        """
        # Create appropriate say message
        language = self.get_language()
        if language and language != "English":
            say_msg = f"{self.key} says in {language}, \"{message}\""
        else:
            say_msg = f"{self.key} says, \"{message}\""
            
        # Send message to room
        if self.location:
            self.location.msg_contents(say_msg, exclude=[])

    def at_emote(self, message, **kwargs):
        """
        Called when NPC emotes.
        Prepends the NPC's name to the emote.
        """
        # Create appropriate emote message
        if message.startswith(":"):
            # If it starts with :, remove it
            emote_msg = f"{self.key} {message[1:].strip()}"
        elif message.startswith(";"):
            # If it starts with ;, it's a "send to self only" emote
            return
        elif self.key.lower() in message.lower():
            # If the name is already in the message, don't prepend it
            emote_msg = message
        else:
            # Otherwise prepend the name
            emote_msg = f"{self.key} {message}"
            
        # Send message to room
        if self.location:
            self.location.msg_contents(emote_msg, exclude=[])

    @classmethod
    def create(cls, *args, **kwargs):
        """Create a new NPC object with database entry."""
        new_npc = super(NPC, cls).create(*args, **kwargs)
        
        # Ensure the database model is created
        if new_npc:
            new_npc.create_db_model()
            
        return new_npc

    def at_post_puppet(self):
        """
        Called just after a player puppets this object.
        
        Since NPCs aren't meant to be puppeted, we'll add a warning.
        """
        self.msg_contents(f"{self.key} has been possessed by {self.account}.")
        self.account.msg("|rWarning:|n You have puppeted an NPC. This is usually not recommended.")
        super().at_post_puppet()

    def at_pre_unpuppet(self):
        """
        Called just before a player stops puppeting this object.
        """
        self.msg_contents(f"{self.key} has been released from {self.account}'s control.")
        super().at_pre_unpuppet()

    def at_heartbeat(self):
        """
        Called regularly by the server.
        
        We use this to check if temporary NPCs should be cleaned up.
        """
        # Check if this is a temporary NPC with expiration
        if self.db.is_temporary and self.db.expiration_time:
            now = datetime.now()
            if now >= self.db.expiration_time:
                self.delete()

