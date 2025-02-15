from evennia.commands.default.muxcommand import MuxCommand
from world.wod20th.utils.sheet_constants import (
    KITH, KNOWLEDGES, SECONDARY_KNOWLEDGES, SECONDARY_SKILLS, 
    SECONDARY_TALENTS, SKILLS, TALENTS, CLAN, BREED, GAROU_TRIBE,
    SEEMING, PATHS_OF_ENLIGHTENMENT, SECT, AFFILIATION, TRADITION,
    CONVENTION, NEPHANDI_FACTION
)
from world.wod20th.models import Stat
from world.wod20th.utils.vampire_utils import (
    calculate_blood_pool, initialize_vampire_stats, update_vampire_virtues_on_path_change, 
    CLAN_CHOICES, get_clan_disciplines, validate_vampire_stats
)
from world.wod20th.utils.mage_utils import (
    initialize_mage_stats, AFFILIATION, TRADITION, CONVENTION,
    TRADITION_SUBFACTION, METHODOLOGIES, NEPHANDI_FACTION, 
    MAGE_SPHERES, update_mage_pools_on_stat_change, validate_mage_stats
)
from world.wod20th.utils.shifter_utils import (
    initialize_shifter_type, SHIFTER_TYPE_CHOICES, BREED_CHOICES_DICT,
    AUSPICE_CHOICES, GAROU_TRIBE_CHOICES, BASTET_TRIBE_CHOICES, 
    update_shifter_pools_on_stat_change, SHIFTER_IDENTITY_STATS, 
    SHIFTER_RENOWN, BREED_CHOICES, ASPECT_CHOICES_DICT, AUSPICE_CHOICES_DICT,
    validate_shifter_stats
)
from world.wod20th.utils.changeling_utils import (
    initialize_changeling_stats, KITH, SEEMING, ARTS, REALMS,
    SEELIE_LEGACIES, UNSEELIE_LEGACIES, KINAIN_LEGACIES,
    validate_changeling_stats
)
from world.wod20th.utils.mortalplus_utils import (
    initialize_mortalplus_stats, MORTALPLUS_TYPE_CHOICES,
    MORTALPLUS_TYPES, MORTALPLUS_POOLS, MORTALPLUS_POWERS,
    validate_mortalplus_stats
)
from world.wod20th.utils.possessed_utils import (
    initialize_possessed_stats, POSSESSED_TYPE_CHOICES,
    POSSESSED_TYPES, POSSESSED_POWERS, validate_possessed_stats
)
from world.wod20th.utils.companion_utils import (
    initialize_companion_stats, COMPANION_TYPE_CHOICES,
    POWER_SOURCE_TYPES, COMPANION_POWERS, COMPANION_TYPE_ADVANTAGES,
    validate_companion_stats
)
from world.wod20th.utils.virtue_utils import (
    calculate_willpower, calculate_path, PATH_VIRTUES
)
from world.wod20th.utils.stat_mappings import (
    CATEGORIES, STAT_TYPES, STAT_TYPE_TO_CATEGORY,
    IDENTITY_STATS, SPLAT_STAT_OVERRIDES,
    POOL_TYPES, POWER_CATEGORIES, ABILITY_TYPES,
    ATTRIBUTE_CATEGORIES, SPECIAL_ADVANTAGES,
    STAT_VALIDATION, VALID_SPLATS, GENERATION_MAP,
    GENERATION_FLAWS, BLOOD_POOL_MAP, get_identity_stats,
    UNIVERSAL_BACKGROUNDS, VAMPIRE_BACKGROUNDS,
    CHANGELING_BACKGROUNDS, MAGE_BACKGROUNDS,
    TECHNOCRACY_BACKGROUNDS, TRADITIONS_BACKGROUNDS,
    NEPHANDI_BACKGROUNDS, SHIFTER_BACKGROUNDS,
    SORCERER_BACKGROUNDS, IDENTITY_PERSONAL, IDENTITY_LINEAGE,
    ARTS, REALMS, VALID_DATES
)
from world.wod20th.utils.stat_initialization import (
    find_similar_stats, check_stat_exists
)
from world.wod20th.utils.archetype_utils import (
    ARCHETYPES, validate_archetype, get_archetype_info
)
from world.wod20th.utils.banality import get_default_banality
import re

# Dictionary of valid archetypes and their willpower regain conditions


class CmdSelfStat(MuxCommand):
    """
    Usage:
      +selfstat <stat>[(<instance>)]/<category>=[+-]<value>
      +selfstat <stat>[(<instance>)]/<category>=

    Examples:
      +selfstat Strength/Physical=+1
      +selfstat Firearms/Skill=-1
      +selfstat Status(Ventrue)/Social=
      +selfstat Nature/Personal=Architect
      +selfstat Demeanor/Personal=Bon Vivant
    """

    key = "+selfstat"
    aliases = ["selfstat"]
    locks = "cmd:all()"  # All players can use this command
    help_category = "Character"

    # Helper Methods
    def _display_instance_requirement_message(self, stat_name: str) -> None:
        """Display message indicating an instance is required for a stat."""
        self.caller.msg(f"|rThe stat '{stat_name}' requires an instance. Use format: {stat_name}(instance)|n")

    def _validate_breed(self, shifter_type: str, value: str) -> tuple[bool, str, str]:
        """
        Validate breed value for a given shifter type.
        
        Args:
            shifter_type: The type of shifter
            value: The breed value to validate
            
        Returns:
            Tuple of (is_valid, matched_value, error_message)
        """
        valid_breeds = BREED_CHOICES_DICT.get(shifter_type, [])
        is_valid, matched_value = self.case_insensitive_in(value, set(valid_breeds))
        error_msg = f"|rInvalid breed for {shifter_type}. Valid breeds are: {', '.join(sorted(valid_breeds))}|n"
        return is_valid, matched_value, error_msg

    def _validate_splat_type(self, splat: str) -> tuple[bool, str]:
        """
        Validate a splat type.
        
        Args:
            splat: The splat type to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        valid_splats = {'Vampire', 'Mage', 'Shifter', 'Changeling', 'Mortal+', 'Possessed', 'Companion'}
        is_valid = splat.title() in valid_splats
        error_msg = f"|rInvalid splat type. Valid types are: {', '.join(sorted(valid_splats))}|n"
        return is_valid, error_msg

    def _validate_kith(self, value: str) -> tuple[bool, str, str]:
        """
        Validate a kith value.
        
        Args:
            value: The kith value to validate
            
        Returns:
            Tuple of (is_valid, matched_value, error_message)
        """
        is_valid, matched_value = self.case_insensitive_in(value, KITH)
        error_msg = f"|rInvalid kith. Valid kiths are: {', '.join(sorted(KITH))}|n"
        return is_valid, matched_value, error_msg

    @property
    def affiliation(self) -> str:
        """Get the character's affiliation."""
        return self.caller.get_stat('identity', 'lineage', 'Affiliation', temp=False)

    @property
    def character_type(self) -> str:
        """Get the character's type."""
        return self.caller.get_stat('identity', 'lineage', 'Type', temp=False)

    @property
    def splat(self) -> str:
        """Get the character's splat."""
        return self.caller.get_stat('identity', 'personal', 'Splat', temp=False)

    def case_insensitive_in(self, value: str, valid_set: set) -> tuple[bool, str]:
        """
        Check if a value exists in a set, ignoring case.
        Returns (bool, matched_value) where matched_value is the correctly-cased version if found.
        """
        if not value:
            return False, None
        # Try direct match first
        if value in valid_set:
            return True, value
        # Try title case
        if value.title() in valid_set:
            return True, value.title()
        # Try case-insensitive match
        value_lower = value.lower()
        for valid_value in valid_set:
            if valid_value.lower() == value_lower:
                return True, valid_value
        return False, None

    def case_insensitive_in_nested(self, value: str, nested_dict: dict, parent_value: str) -> tuple[bool, str]:
        """
        Check if a value exists in a nested dictionary's list, ignoring case.
        Returns (bool, matched_value) where matched_value is the correctly-cased version if found.
        """
        if not value or not parent_value:
            return False, None
        valid_values = nested_dict.get(parent_value, [])
        return self.case_insensitive_in(value, set(valid_values))

    def get_stat_category(self, stat_name: str, stat_type: str, splat: str = None) -> str:
        """
        Get the appropriate category for a stat based on stat type and splat.
        """
        # Check for splat-specific overrides first
        if splat and splat in SPLAT_STAT_OVERRIDES:
            if stat_name in SPLAT_STAT_OVERRIDES[splat]:
                return SPLAT_STAT_OVERRIDES[splat][stat_name][1]

        # Use the standard mapping
        return STAT_TYPE_TO_CATEGORY.get(stat_type, 'other')

    def get_background_splat_restriction(self, stat_name: str) -> tuple[bool, str, str]:
        """
        Check if a background is restricted to a specific splat type.
        Returns (is_restricted, splat_name, error_message).
        """
        # Convert stat name to title case for comparison
        stat_title = stat_name.title()
        
        # Check if this is a splat-specific background
        if stat_title in (bg.title() for bg in VAMPIRE_BACKGROUNDS):
            return True, "Vampire", f"The background '{stat_name}' is only available to Vampire characters."
        elif stat_title in (bg.title() for bg in CHANGELING_BACKGROUNDS):
            return True, "Changeling", f"The background '{stat_name}' is only available to Changeling characters."
        elif stat_title in (bg.title() for bg in MAGE_BACKGROUNDS + TECHNOCRACY_BACKGROUNDS + TRADITIONS_BACKGROUNDS + NEPHANDI_BACKGROUNDS):
            return True, "Mage", f"The background '{stat_name}' is only available to Mage characters."
        elif stat_title in (bg.title() for bg in SHIFTER_BACKGROUNDS):
            return True, "Shifter", f"The background '{stat_name}' is only available to Shifter characters."
        elif stat_title in (bg.title() for bg in SORCERER_BACKGROUNDS):
            return True, "Mortal+", f"The background '{stat_name}' is only available to Mortal+ characters."
            
        return False, "", ""

    def validate_stat_value(self, stat_name: str, value: str, category: str = None, stat_type: str = None) -> tuple:
        """
        Validate a stat value based on its type and category.
        Returns (is_valid, error_message)
        """
        # Get character's splat for validation
        splat = self.splat
        if not splat:
            return True, ""  # No validation needed if no splat set
            
        # Call appropriate validation function based on splat
        if splat == 'Vampire':
            return validate_vampire_stats(self.caller, stat_name, value, category, stat_type)
        elif splat == 'Mage':
            return validate_mage_stats(self.caller, stat_name, value, category, stat_type)
        elif splat == 'Shifter':
            return validate_shifter_stats(self.caller, stat_name, value, category, stat_type)
        elif splat == 'Changeling':
            return validate_changeling_stats(self.caller, stat_name, value, category, stat_type)
        elif splat == 'Mortal+':
            return validate_mortalplus_stats(self.caller, stat_name, value, category, stat_type)
        elif splat == 'Possessed':
            return validate_possessed_stats(self.caller, stat_name, value, category, stat_type)
        elif splat == 'Companion':
            return validate_companion_stats(self.caller, stat_name, value, category, stat_type)
        
        return True, ""

    def get_identity_category(self, stat_name: str) -> str:
        """
        Determine whether an identity stat belongs in personal or lineage.
        """
        # First check if it's in the direct mappings
        stat_name = stat_name.lower()
        if stat_name in IDENTITY_PERSONAL:
            return 'personal'
        elif stat_name in IDENTITY_LINEAGE:
            return 'lineage'
            
        # If not found in direct mappings, check if it's a valid identity stat for the character's splat
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
        if not splat:
            return None
            
        # Get subtype and affiliation if applicable
        subtype = None
        affiliation = None
        
        if splat.lower() == 'shifter':
            subtype = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
        elif splat.lower() == 'mage':
            affiliation = self.caller.get_stat('identity', 'lineage', 'Affiliation', temp=False)
        elif splat.lower() == 'changeling':
            subtype = self.caller.get_stat('identity', 'lineage', 'Kith', temp=False)
        elif splat.lower() == 'possessed':
            subtype = self.caller.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
        elif splat.lower() == 'mortal+':
            subtype = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
            
        valid_stats = get_identity_stats(splat, subtype, affiliation)
        
        # If the stat is in the valid stats list, determine its category
        if stat_name.title() in valid_stats:
            # Personal stats are typically the base stats and dates
            if any(word in stat_name for word in ['name', 'date', 'nature', 'demeanor', 'concept']):
                return 'personal'
            # Everything else is lineage
            return 'lineage'
            
        return None

    def _detect_identity_category(self, stat_name: str) -> tuple[str, str]:
        """
        Detect if a stat is an identity stat and which category it belongs to.
        
        Args:
            stat_name: The name of the stat to check
            
        Returns:
            Tuple of (category, type) or (None, None) if not an identity stat
        """
        # Convert to title case for consistent comparison
        stat_title = stat_name.title()
        stat_lower = stat_name.lower()

        # Handle date stats explicitly
        date_stats = {
            'date of birth',
            'date of embrace',
            'date of chrysalis',
            'date of awakening',
            'first change date',
            'date of possession'
        }
        if stat_lower in date_stats:
            return 'identity', 'personal'

        # First check direct mappings
        if stat_title in IDENTITY_PERSONAL:
            return 'identity', 'personal'
        elif stat_title in IDENTITY_LINEAGE:
            return 'identity', 'lineage'
            
        # If not in direct mappings, check if it's a valid identity stat for the character's splat
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
        if not splat:
            return None, None
            
        # Get subtype and affiliation if applicable
        subtype = None
        affiliation = None
        
        if splat.lower() == 'shifter':
            subtype = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
        elif splat.lower() == 'mage':
            affiliation = self.caller.get_stat('identity', 'lineage', 'Affiliation', temp=False)
        elif splat.lower() == 'changeling':
            subtype = self.caller.get_stat('identity', 'lineage', 'Kith', temp=False)
        elif splat.lower() == 'possessed':
            subtype = self.caller.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
        elif splat.lower() == 'mortal+':
            subtype = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
            
        valid_stats = get_identity_stats(splat, subtype, affiliation)
        
        # If the stat is in the valid stats list, determine its category
        if stat_title in valid_stats:
            # Personal stats are typically the base stats and dates
            if any(word.lower() in stat_lower for word in ['name', 'date', 'nature', 'demeanor', 'concept']):
                return 'identity', 'personal'
            # Everything else is lineage
            return 'identity', 'lineage'
            
        return None, None

    def parse(self):
        """Parse the arguments."""
        self.stat_name = ""
        self.instance = None
        self.category = None
        self.value_change = None
        self.temp = False
        self.stat_type = None 
        args = self.args.strip()
        if not args:
            return

        # Split into parts before and after =
        if '=' in args:
            first_part, self.value_change = args.split('=', 1)
            first_part = first_part.strip()
            self.value_change = self.value_change.strip()
        else:
            first_part = args
            self.value_change = None

        # Parse stat name, instance, and category/type
        try:
            # Get the stat definition first
            from world.wod20th.models import Stat
            stat = Stat.objects.filter(name__iexact=first_part.split('(')[0].strip()).first()
            
            if '(' in first_part and ')' in first_part:
                # Handle instance format: stat(instance)/category
                self.stat_name, instance_and_category = first_part.split('(', 1)
                instance_part, category_part = instance_and_category.split(')', 1)
                self.instance = instance_part.strip()
                
                # Check if instancing is explicitly disallowed
                if stat and stat.instanced is False:
                    self._display_instance_requirement_message(self.stat_name)
                    self.stat_name = None  # Set to None to indicate parsing failed
                    return
                    
                if '/' in category_part:
                    category_or_type = category_part.lstrip('/').strip()
                    # Map the user-provided category/type to the correct values
                    self.map_category_and_type(category_or_type)
            else:
                # Handle non-instance format: stat/category
                if '/' in first_part:
                    self.stat_name, category_or_type = first_part.split('/', 1)
                    # Map the user-provided category/type to the correct values
                    self.map_category_and_type(category_or_type.strip())
                else:
                    self.stat_name = first_part
                    self.category = None
                    self.stat_type = None
                    
                # Check if instancing is required
                if stat and stat.instanced is True:
                    self._display_instance_requirement_message(self.stat_name)
                    self.stat_name = None  # Set to None to indicate parsing failed
                    return
                
            self.stat_name = self.stat_name.strip()

            # Special handling for Nature and Time
            if not self.category:
                splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
                char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
                
                if self.stat_name.lower() == 'nature':
                    # For Changelings and Kinain, Nature is a realm power
                    if splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain'):
                        self.category = 'powers'
                        self.stat_type = 'realm'
                    else:
                        self.category = 'identity'
                        self.stat_type = 'personal'
                elif self.stat_name.lower() == 'demeanor':
                    self.category = 'identity'
                    self.stat_type = 'personal'
                elif self.stat_name.lower() == 'time':
                    if splat == 'Mage':
                        self.category = 'powers'
                        self.stat_type = 'sphere'
                    elif splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain'):
                        self.category = 'powers'
                        self.stat_type = 'realm'

        except ValueError as e:
            # If parsing fails, show the error message
            self.caller.msg(f"|r{str(e)}|n")
            self.stat_name = None  # Set to None to indicate parsing failed
            return
        except Exception:
            # If any other error occurs, just use the whole thing as stat name
            self.stat_name = first_part.strip()
            self.instance = None
            self.category = None
            self.stat_type = None

    def map_category_and_type(self, category_or_type: str):
        """Map user-provided category/type to correct internal values."""
        category_or_type = category_or_type.lower()
        
        # Direct category mappings
        category_map = {
            'ability': ('abilities', 'talent'),  # Default to talent, will be adjusted in validation
            'talent': ('abilities', 'talent'),
            'skill': ('abilities', 'skill'),
            'knowledge': ('abilities', 'knowledge'),
            'archetype': ('identity', 'personal'),
            'secondary_ability': ('secondary_abilities', 'secondary_talent'), # Default to talent, will be adjusted in validation
            'secondary_talent': ('secondary_abilities', 'secondary_talent'),
            'secondary_skill': ('secondary_abilities', 'secondary_skill'),
            'secondary_knowledge': ('secondary_abilities', 'secondary_knowledge'),
            'discipline': ('powers', 'discipline'),
            'gift': ('powers', 'gift'),
            'sphere': ('powers', 'sphere'),
            'realm': ('powers', 'realm'),
            'art': ('powers', 'art'),
            'blessing': ('powers', 'blessing'),
            'charm': ('powers', 'charm'),
            'special_advantage': ('powers', 'special_advantage'),
            'background': ('backgrounds', 'background'),
            'merit': ('merits', 'merit'),
            'flaw': ('flaws', 'flaw'),
            'willpower': ('pools', 'dual'),
            'rage': ('pools', 'dual'),
            'gnosis': ('pools', 'dual'),
            'glamour': ('pools', 'dual'),
            'banality': ('pools', 'dual'),
            'nightmare': ('pools', 'other'),
            'blood': ('pools', 'dual'),
            'quintessence': ('pools', 'dual'),
            'paradox': ('pools', 'dual'),
            'path': ('pools', 'moral'),# Alias for path
            'road': ('pools', 'moral'),  
            'arete': ('pools', 'advantage'),
            'enlightenment': ('pools', 'advantage'),
            'resonance': ('pools', 'resonance'),
            'conscience': ('virtues', 'moral'),
            'conviction': ('virtues', 'moral'),
            'self-control': ('virtues', 'moral'),
            'instinct': ('virtues', 'moral'),
            'courage': ('virtues', 'moral'),
            'dynamic': ('virtues', 'synergy'),  
            'static': ('virtues', 'synergy'),
            'entropic': ('virtues', 'synergy'),
            'date of birth': ('identity', 'personal'),
            'date of embrace': ('identity', 'personal'),
            'date of chrysalis': ('identity', 'personal'),
            'date of awakening': ('identity', 'personal'),
            'first change date': ('identity', 'personal'),
            'date of possession': ('identity', 'personal'),
            # Add some common aliases/variations
            'disciplines': ('powers', 'discipline'),
            'gifts': ('powers', 'gift'),
            'spheres': ('powers', 'sphere'),
            'realms': ('powers', 'realm'),
            'arts': ('powers', 'art'),
            'blessings': ('powers', 'blessing'),
            'charms': ('powers', 'charm'),
            'advantages': ('powers', 'special_advantage'),
            'backgrounds': ('backgrounds', 'background'),
            'merits': ('merits', 'merit'),
            'flaws': ('flaws', 'flaw'),
            'pools': ('pools', 'dual'),
            'virtues': ('virtues', 'moral'),
            'identity': ('identity', 'personal'),
            'personal': ('identity', 'personal'),
            'lineage': ('identity', 'lineage'),
            'patron totem': ('identity', 'lineage'),
            'totem': ('backgrounds', 'background'),
            'possessed wings': ('powers', 'blessing'),
            'companion wings': ('powers', 'special_advantage'),
            'possessed size': ('powers', 'blessing'),
            'companion size': ('powers', 'special_advantage'),
            'spirit type': ('identity', 'lineage'),
            'essence energy': ('pools', 'dual'),
            'organizational rank': ('backgrounds', 'background'),
            'jamak spirit': ('identity', 'lineage')
        }
        
        # Try exact match first
        if category_or_type in category_map:
            self.category, self.stat_type = category_map[category_or_type]
            return
            
        # Try case-insensitive match
        category_or_type_lower = category_or_type.lower()
        for key, value in category_map.items():
            if key.lower() == category_or_type_lower:
                self.category, self.stat_type = value
                return
                
        # If not found in map, set both and let validation handle errors
        self.category = category_or_type
        self.stat_type = category_or_type


    def detect_ability_category(self, stat_name: str) -> tuple[str, str]:
        """
        Detect the appropriate category and type for an ability or background.
        Returns (category, type) tuple.
        """
        # Convert stat name to title case for comparison
        stat_title = stat_name.title()

        # Special case for Generation
        if stat_title == 'Generation':
            return 'backgrounds', 'background'

        # Get the stat definition first
        from world.wod20th.models import Stat
        stat = Stat.objects.filter(name__iexact=stat_name).first()
        if stat:
            # Handle pool stats
            if stat.category == 'pools':
                return 'pools', stat.stat_type

            # Handle power types
            power_types = {
                'gift', 'charm', 'blessing', 'discipline', 'thaumaturgy',
                'thaum_ritual', 'hedge_ritual', 'necromancy_ritual', 'numina',
                'ritual', 'combodiscipline', 'faith', 'arcanos', 'special_advantage',
                'sphere', 'sorcery'  # Add sphere to power types
            }
            if stat.stat_type.lower() in power_types:
                return 'powers', stat.stat_type.lower()

        # Check identity stats first
        identity_cat = self._detect_identity_category(stat_name)
        if identity_cat:
            return identity_cat

        # Check if it's a sphere (from static mapping)
        if stat_title in MAGE_SPHERES:
            return 'powers', 'sphere'

        # Check if it's an attribute
        attribute_category = self._detect_attribute_category(stat_title)
        if attribute_category:
            return 'attributes', attribute_category

        # Check if it's a background
        if stat_title in (
            UNIVERSAL_BACKGROUNDS +
            VAMPIRE_BACKGROUNDS +
            CHANGELING_BACKGROUNDS +
            MAGE_BACKGROUNDS +
            TECHNOCRACY_BACKGROUNDS +
            TRADITIONS_BACKGROUNDS +
            NEPHANDI_BACKGROUNDS +
            SHIFTER_BACKGROUNDS +
            SORCERER_BACKGROUNDS
        ):
            return 'backgrounds', 'background'

        # Check if it's a Changeling Art
        if stat_title in ARTS:
            return 'powers', 'art'

        # Check if it's a Changeling Realm
        if stat_title in REALMS:
            return 'powers', 'realm'

        # Check standard abilities
        if stat_title in TALENTS:
            return 'abilities', 'talent'
        elif stat_title in SKILLS:
            return 'abilities', 'skill'
        elif stat_title in KNOWLEDGES:
            return 'abilities', 'knowledge'
        # Then check secondary abilities
        elif stat_title in SECONDARY_TALENTS:
            return 'secondary_abilities', 'secondary_talent'
        elif stat_title in SECONDARY_SKILLS:
            return 'secondary_abilities', 'secondary_skill'
        elif stat_title in SECONDARY_KNOWLEDGES:
            return 'secondary_abilities', 'secondary_knowledge'

        # Check pool stats that might not be in the database
        pool_stats = {
            'arete': ('pools', 'advantage'),
            'enlightenment': ('pools', 'advantage'),
            'willpower': ('pools', 'dual'),
            'rage': ('pools', 'dual'),
            'gnosis': ('pools', 'dual'),
            'blood': ('pools', 'dual'),
            'glamour': ('pools', 'dual'),
            'banality': ('pools', 'dual'),
            'quintessence': ('pools', 'dual'),
            'paradox': ('pools', 'dual'),
            'resonance': ('pools', 'resonance')
        }
        
        if stat_name.lower() in pool_stats:
            return pool_stats[stat_name.lower()]

        return None, None

    def _detect_attribute_category(self, stat_name: str) -> str:
        """
        Detect which attribute category a stat belongs to.
        
        Args:
            stat_name: The name of the stat to check
            
        Returns:
            The attribute category ('physical', 'social', 'mental') or None if not an attribute
        """
        # Check each attribute category
        for category, attributes in ATTRIBUTE_CATEGORIES.items():
            if stat_name in attributes:
                return category
        return None

    def func(self):
        """Execute the command."""
        # Check if character is approved
        if self.caller.db.approved:
            self.caller.msg("|rError: Approved characters cannot use chargen commands. Please contact staff for any needed changes.|n")
            return
            
        if not self.stat_name:
            self.caller.msg("|rUsage: +selfstat <stat>[(<instance>)]/[<category>]=[+-]<value>|n")
            return

        # Get character's splat type and character type first
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
        char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)

        # Special handling for Generation
        if self.stat_name.lower() == 'generation':
            try:
                gen_value = int(self.value_change)
                if gen_value < -2 or gen_value > 7:
                    self.caller.msg("|rGeneration background must be between -2 (15th) and 7 (6th).|n")
                    return
                
                # Convert background value to actual generation
                generation_map = {
                    -2: "15th", -1: "14th", 0: "13th",
                    1: "12th", 2: "11th", 3: "10th",
                    4: "9th", 5: "8th", 6: "7th",
                    7: "6th"
                }
                
                # Set the background value
                self.caller.set_stat('backgrounds', 'background', 'Generation', gen_value, temp=False)
                self.caller.set_stat('backgrounds', 'background', 'Generation', gen_value, temp=True)
                
                # Set the actual generation in identity/lineage
                generation = generation_map.get(gen_value, "13th")
                self.caller.set_stat('identity', 'lineage', 'Generation', generation, temp=False)
                self.caller.set_stat('identity', 'lineage', 'Generation', generation, temp=True)
                
                # Update blood pool based on generation
                blood_pool = calculate_blood_pool(gen_value)
                self.caller.set_stat('pools', 'dual', 'Blood', blood_pool, temp=False)
                self.caller.set_stat('pools', 'dual', 'Blood', blood_pool, temp=True)
                
                self.caller.msg(f"|gGeneration set to {generation} (Blood Pool: {blood_pool}).|n")
                return
            except ValueError:
                self.caller.msg("|rGeneration background must be a number.|n")
                return

        # If no category/type specified, try to determine it from the stat name
        if not self.category or not self.stat_type:
            # First try identity stats
            self.category, self.stat_type = self._detect_identity_category(self.stat_name)
            
            # If not an identity stat, try abilities and other categories
            if not self.category or not self.stat_type:
                self.category, self.stat_type = self.detect_ability_category(self.stat_name)

        # Special handling for Path of Enlightenment changes
        if self.stat_name.lower() == 'path of enlightenment':
            if splat and splat.lower() == 'vampire':
                from world.wod20th.utils.vampire_utils import update_vampire_virtues_on_path_change
                # Set the path in identity/personal
                self.caller.set_stat('identity', 'personal', 'Path of Enlightenment', self.value_change, temp=False)
                self.caller.set_stat('identity', 'personal', 'Path of Enlightenment', self.value_change, temp=True)
                # Update virtues based on the new path
                update_vampire_virtues_on_path_change(self.caller, self.value_change)
                return

        # Special handling for Affinity Realm
        if self.stat_name.lower() == 'affinity realm':
            self.stat_name = 'Affinity Realm'  # Ensure proper capitalization
            self.category = 'identity'
            self.stat_type = 'lineage'

        # When setting splat for the first time or resetting stats
        if self.stat_name.lower() == 'splat':
            if not self.value_change:
                self.caller.msg("You must specify a splat type.")
                return

            # Validate splat type (case-insensitive)
            if self.value_change.lower() not in [s.lower() for s in VALID_SPLATS]:
                self.caller.msg(f"|rInvalid splat type. Valid types are: {', '.join(VALID_SPLATS)}|n")
                return

            # Initialize the stats structure based on splat
            self.initialize_stats(self.caller, self.value_change.title())
            return

        # Special handling for type setting
        if self.stat_name.lower() in ['type', 'possessed type', 'mortal+ type']:
            # First check if this is a Mortal+ type
            if splat and splat.lower() == 'mortal+':
                # Get valid Mortal+ types
                valid_types = [t[1] for t in MORTALPLUS_TYPE_CHOICES if t[1] != 'None']
                mortalplus_type = next((t for t in valid_types if t.lower() == self.value_change.lower()), None)
                if not mortalplus_type:
                    self.caller.msg(f"|rInvalid Mortal+ type. Valid types are: {', '.join(sorted(valid_types))}|n")
                    return
                # Initialize mortal+-specific stats for the chosen type
                initialize_mortalplus_stats(self.caller, mortalplus_type)
                self.caller.msg(f"|gSet Mortal+ type to {mortalplus_type} and initialized appropriate stats.|n")
                return

        # Special handling for Nature/Demeanor
        elif self.stat_name.lower() in ['nature', 'demeanor']:
            # For Changelings/Kinain, Nature is a realm power
            if self.stat_name.lower() == 'nature' and (splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain')):
                try:
                    realm_value = int(self.value_change)
                    if realm_value < 0 or realm_value > 5:
                        self.caller.msg("|rNature realm must be between 0 and 5.|n")
                        return
                    category = 'powers'
                    stat_type = 'realm'
                except ValueError:
                    self.caller.msg("|rNature realm must be a number.|n")
                    return
            else:
                # For other splats or Demeanor, validate as archetype
                is_valid, error_msg = validate_archetype(str(self.value_change))
                if not is_valid:
                    self.caller.msg(f"|r{error_msg}|n")
                    return
                # Get full archetype info for success message
                archetype_info = get_archetype_info(str(self.value_change))
                if archetype_info:
                    self.value_change = archetype_info['name']  # Use proper case from definition
                    self.caller.msg(f"|gSet to {archetype_info['name']} - Willpower regain: {archetype_info['system']}|n")
                category = 'identity'
                stat_type = 'personal'

        # When setting type for the first time or resetting stats
        if self.stat_name.lower() in ['type', 'possessed type', 'mortal+ type']:
            # First check if this is a Mortal+ type
            if splat and splat.lower() == 'mortal+':
                # Get valid Mortal+ types
                valid_types = [t[1] for t in MORTALPLUS_TYPE_CHOICES if t[1] != 'None']
                mortalplus_type = next((t for t in valid_types if t.lower() == self.value_change.lower()), None)
                if not mortalplus_type:
                    self.caller.msg(f"|rInvalid Mortal+ type. Valid types are: {', '.join(sorted(valid_types))}|n")
                    return
                # Initialize mortal+-specific stats for the chosen type
                initialize_mortalplus_stats(self.caller, mortalplus_type)
                self.caller.msg(f"|gSet Mortal+ type to {mortalplus_type} and initialized appropriate stats.|n")
            elif splat and splat.lower() == 'possessed':
                # Convert tuple list to just the type names for validation
                valid_types = [t[0] for t in POSSESSED_TYPE_CHOICES if t[0] != 'None']
                if self.value_change.title() not in valid_types:
                    self.caller.msg(f"|rInvalid Possessed type. Valid types are: {', '.join(valid_types)}|n")
                    return
                # Set the type in identity/lineage
                self.caller.set_stat('identity', 'lineage', 'Possessed Type', self.value_change.title(), temp=False)
                self.caller.set_stat('identity', 'lineage', 'Possessed Type', self.value_change.title(), temp=True)
                # Initialize possessed-specific stats for the chosen type
                initialize_possessed_stats(self.caller, self.value_change.title())
                self.caller.msg(f"|gSet Possessed type to {self.value_change.title()} and initialized appropriate stats.|n")
                return
            elif splat and splat.lower() == 'shifter':
                # Convert tuple list to just the type names for validation
                valid_types = [t[1] for t in SHIFTER_TYPE_CHOICES if t[1] != 'None']
                if self.value_change.title() not in valid_types:
                    self.caller.msg(f"|rInvalid shifter type. Valid types are: {', '.join(valid_types)}|n")
                    return
                # Set the type in identity/lineage
                self.caller.set_stat('identity', 'lineage', 'Type', self.value_change.title(), temp=False)
                self.caller.set_stat('identity', 'lineage', 'Type', self.value_change.title(), temp=True)
                # Initialize shifter-specific stats for the chosen type
                initialize_shifter_type(self.caller, self.value_change.title())
                self.caller.msg(f"|gSet shifter type to {self.value_change.title()} and initialized appropriate stats.|n")
                return
        # Special handling for mage affiliation/tradition/convention setting
        if self.stat_name.lower() in ['affiliation', 'tradition', 'convention', 'nephandi faction']:
            if splat and splat.lower() == 'mage':
                # Handle affiliation setting
                if self.stat_name.lower() == 'affiliation':
                    is_valid, matched_value = self.case_insensitive_in(self.value_change, AFFILIATION)
                    if not is_valid:
                        self.caller.msg(f"|rInvalid affiliation. Valid affiliations are: {', '.join(sorted(AFFILIATION))}|n")
                        return
                    self.value_change = matched_value
                    # Initialize mage-specific stats for the chosen affiliation
                    initialize_mage_stats(self.caller, matched_value)
                    return ('identity', 'lineage')

                # Handle tradition/convention/faction based on affiliation
                if not self.affiliation:
                    self.caller.msg("|rError: Must set affiliation before setting tradition/convention/faction.|n")
                    return

                if self.affiliation == 'Traditions' and self.stat_name.lower() == 'tradition':
                    is_valid, matched_value = self.case_insensitive_in(self.value_change, TRADITION)
                    if not is_valid:
                        self.caller.msg(f"|rInvalid tradition. Valid traditions are: {', '.join(sorted(TRADITION))}|n")
                        return
                    self.value_change = matched_value
                
                elif self.affiliation == 'Technocracy' and self.stat_name.lower() == 'convention':
                    is_valid, matched_value = self.case_insensitive_in(self.value_change, CONVENTION)
                    if not is_valid:
                        self.caller.msg(f"|rInvalid convention. Valid conventions are: {', '.join(sorted(CONVENTION))}|n")
                        return
                    self.value_change = matched_value
                
                elif self.affiliation == 'Nephandi' and self.stat_name.lower() == 'nephandi faction':
                    is_valid, matched_value = self.case_insensitive_in(self.value_change, NEPHANDI_FACTION)
                    if not is_valid:
                        self.caller.msg(f"|rInvalid Nephandi faction. Valid factions are: {', '.join(sorted(NEPHANDI_FACTION))}|n")
                        return
                    self.value_change = matched_value

        # Special handling for mage subfaction/methodology setting
        if self.stat_name.lower() in ['traditions subfaction', 'methodology']:
            if splat and splat.lower() == 'mage':
                if self.affiliation == 'Traditions':
                    tradition = self.caller.get_stat('identity', 'lineage', 'Tradition', temp=False)
                    if not tradition:
                        self.caller.msg("|rError: Must set tradition before setting subfaction.|n")
                        return
                    is_valid, matched_value = self.case_insensitive_in_nested(self.value_change, TRADITION_SUBFACTION, tradition)
                    if not is_valid:
                        self.caller.msg(f"|rInvalid subfaction for {tradition}. Valid subfactions are: {', '.join(sorted(TRADITION_SUBFACTION.get(tradition, [])))}|n")
                        return
                    self.value_change = matched_value

                elif self.affiliation == 'Technocracy':
                    convention = self.caller.get_stat('identity', 'lineage', 'Convention', temp=False)
                    if not convention:
                        self.caller.msg("|rError: Must set convention before setting methodology.|n")
                        return
                    is_valid, matched_value = self.case_insensitive_in_nested(self.value_change, METHODOLOGIES, convention)
                    if not is_valid:
                        self.caller.msg(f"|rInvalid methodology for {convention}. Valid methodologies are: {', '.join(sorted(METHODOLOGIES.get(convention, [])))}|n")
                        return
                    self.value_change = matched_value

        # Special handling for shifter breed setting
        if self.stat_name.lower() == 'breed':
            if splat and splat.lower() == 'shifter' and self.character_type:
                is_valid, matched_value, error_msg = self._validate_breed(self.character_type, self.value_change)
                if not is_valid:
                    self.caller.msg(error_msg)
                    return
                self.value_change = matched_value

        # Special handling for changeling kith setting
        if self.stat_name.lower() == 'kith':
            if splat and splat.lower() == 'changeling':
                is_valid, matched_value, error_msg = self._validate_kith(self.value_change)
                if not is_valid:
                    self.caller.msg(error_msg)
                    return
                self.value_change = matched_value

        # When setting clan for vampires
        if self.stat_name.lower() == 'clan':
            splat = self.splat
            if splat and splat.lower() == 'vampire':
                is_valid, proper_clan, error_msg = self._validate_clan(self.value_change)
                if not is_valid:
                    self.caller.msg(error_msg)
                    return
                
                # Set the clan with proper case
                self.value_change = proper_clan
                
                # Update clan-specific stats
                self._update_clan_stats(proper_clan)
                
                # Set the clan in identity/lineage
                self._initialize_stat_structure('identity', 'lineage')
                self.caller.db.stats['identity']['lineage']['Clan'] = {'perm': proper_clan, 'temp': proper_clan}
                self.caller.msg(f"|gSet clan to {proper_clan}.|n")
                return

        # Special handling for Path of Enlightenment changes
        elif self.stat_name.lower() == 'path of enlightenment':
            splat = self.splat
            if splat and splat.lower() == 'vampire':
                is_valid, proper_path, error_msg = self._validate_path(self.value_change)
                if not is_valid:
                    self.caller.msg(error_msg)
                    return
                
                # Set the path in identity/personal
                self._initialize_stat_structure('identity', 'personal')
                self.caller.db.stats['identity']['personal']['Path of Enlightenment'] = {'perm': proper_path, 'temp': proper_path}
                
                # Update path-specific stats
                self._update_path_stats(proper_path)
                
                self.caller.msg(f"|gSet Path of Enlightenment to {proper_path}.|n")
                return

        # When setting Changeling-specific stats
        elif self.stat_name.lower() in ['kith', 'seeming', 'seelie legacy', 'unseelie legacy']:
            splat = self.caller.get_stat('identity', 'personal', 'Splat', temp=False)
            if splat and splat.lower() == 'changeling':
                if self.stat_name.lower() == 'kith':
                    is_valid, matched_value, error_msg = self._validate_kith(self.value_change)
                    if not is_valid:
                        self.caller.msg(error_msg)
                        return
                    self.value_change = matched_value
                    # Initialize changeling stats with the new kith
                    initialize_changeling_stats(self.caller, matched_value)
                    return ('identity', 'lineage')

                elif self.stat_name.lower() == 'seeming':
                    is_valid, matched_value = self.case_insensitive_in(self.value_change, SEEMING)
                    if not is_valid:
                        self.caller.msg(f"|rInvalid seeming. Valid seemings are: {', '.join(sorted(SEEMING))}|n")
                        return
                    self.value_change = matched_value
                    return ('identity', 'lineage')

                elif self.stat_name.lower() == 'seelie legacy':
                    is_valid, matched_value = self.case_insensitive_in(self.value_change, SEELIE_LEGACIES)
                    if not is_valid:
                        self.caller.msg(f"|rInvalid Seelie Legacy. Valid legacies are: {', '.join(sorted(SEELIE_LEGACIES))}|n")
                        return
                    self.value_change = matched_value
                    return ('identity', 'lineage')

                elif self.stat_name.lower() == 'unseelie legacy':
                    is_valid, matched_value = self.case_insensitive_in(self.value_change, UNSEELIE_LEGACIES)
                    if not is_valid:
                        self.caller.msg(f"|rInvalid Unseelie Legacy. Valid legacies are: {', '.join(sorted(UNSEELIE_LEGACIES))}|n")
                        return
                    self.value_change = matched_value
                    return ('identity', 'lineage')

        # When setting Arts and Realms
        elif self.stat_name.lower() in [art.lower() for art in ARTS] or self.stat_name.lower() in [realm.lower() for realm in REALMS]:
            splat = self.caller.get_stat('identity', 'personal', 'Splat', temp=False)
            char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
            
            # Check if character is Changeling or Kinain
            if splat and (splat.lower() == 'changeling' or (splat.lower() == 'mortal+' and char_type == 'Kinain')):
                try:
                    value = int(self.value_change)
                    max_rating = 3 if char_type == 'Kinain' else 5
                    if value < 0 or value > max_rating:
                        self.caller.msg(f"|r{self.stat_name} rating must be between 0 and {max_rating}.|n")
                        return
                    
                    # Determine if it's an Art or Realm
                    if self.stat_name.lower() in [art.lower() for art in ARTS]:
                        return ('powers', 'art')
                    else:
                        return ('powers', 'realm')
                except ValueError:
                    self.caller.msg(f"|r{self.stat_name} rating must be a number.|n")
                    return

        # When setting Kinain legacies
        elif self.stat_name.lower() in ['first legacy', 'second legacy']:
            splat = self.caller.get_stat('identity', 'personal', 'Splat', temp=False)
            char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
            
            if splat and splat.lower() == 'mortal+' and char_type == 'Kinain':
                is_valid, matched_value, error_msg = self._validate_splat_type(self.value_change)
                if not is_valid:
                    self.caller.msg(error_msg)
                    return
                self.value_change = matched_value
                return ('identity', 'lineage')

        # When setting Shifter-specific stats
        elif self.stat_name.lower() in ['breed', 'auspice', 'tribe', 'aspect']:
            splat = self.caller.get_stat('identity', 'personal', 'Splat', temp=False)
            shifter_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
            
            if splat and splat.lower() == 'shifter' and shifter_type:
                # Breed validation
                if self.stat_name.lower() == 'breed':
                    is_valid, matched_value, error_msg = self._validate_breed(shifter_type, self.value_change)
                    if not is_valid:
                        self.caller.msg(error_msg)
                        return
                    self.value_change = matched_value
                    # Update pools based on breed
                    update_shifter_pools_on_stat_change(self.caller, 'breed', matched_value)
                    return ('identity', 'lineage')

                # Auspice validation
                elif self.stat_name.lower() == 'auspice':
                    valid_auspices = AUSPICE_CHOICES_DICT.get(shifter_type, [])
                    is_valid, matched_value = self.case_insensitive_in(self.value_change, set(valid_auspices))
                    if not is_valid:
                        valid_auspices_str = ', '.join(sorted(valid_auspices))
                        self.caller.msg(f"|rInvalid auspice for {shifter_type}. Valid auspices are: {valid_auspices_str}|n")
                        return
                    self.value_change = matched_value
                    # Update pools based on auspice
                    update_shifter_pools_on_stat_change(self.caller, 'auspice', matched_value)
                    return ('identity', 'lineage')

                # Tribe validation for Garou
                elif self.stat_name.lower() == 'tribe' and shifter_type == 'Garou':
                    valid_tribes = [t[1] for t in GAROU_TRIBE_CHOICES if t[1] != 'None']
                    is_valid, matched_value = self.case_insensitive_in(self.value_change, set(valid_tribes))
                    if not is_valid:
                        valid_tribes_str = ', '.join(sorted(valid_tribes))
                        self.caller.msg(f"|rInvalid Garou tribe. Valid tribes are: {valid_tribes_str}|n")
                        return
                    self.value_change = matched_value
                    # Update pools based on tribe
                    update_shifter_pools_on_stat_change(self.caller, 'tribe', matched_value)
                    return ('identity', 'lineage')

                # Tribe validation for Bastet
                elif self.stat_name.lower() == 'tribe' and shifter_type == 'Bastet':
                    valid_tribes = [t[1] for t in BASTET_TRIBE_CHOICES if t[1] != 'None']
                    is_valid, matched_value = self.case_insensitive_in(self.value_change, set(valid_tribes))
                    if not is_valid:
                        valid_tribes_str = ', '.join(sorted(valid_tribes))
                        self.caller.msg(f"|rInvalid Bastet tribe. Valid tribes are: {valid_tribes_str}|n")
                        return
                    self.value_change = matched_value
                    # Update pools based on tribe
                    update_shifter_pools_on_stat_change(self.caller, 'tribe', matched_value)
                    return ('identity', 'lineage')

                # Aspect validation
                elif self.stat_name.lower() == 'aspect':
                    valid_aspects = ASPECT_CHOICES_DICT.get(shifter_type, [])
                    is_valid, matched_value = self.case_insensitive_in(self.value_change, set(valid_aspects))
                    if not is_valid:
                        valid_aspects_str = ', '.join(sorted(valid_aspects))
                        self.caller.msg(f"|rInvalid aspect for {shifter_type}. Valid aspects are: {valid_aspects_str}|n")
                        return
                    self.value_change = matched_value
                    # Update pools based on aspect
                    update_shifter_pools_on_stat_change(self.caller, 'aspect', matched_value)
                    return ('identity', 'lineage')

        # When setting Companion-specific stats
        elif self.stat_name.lower() == 'companion type':
            splat = self.caller.get_stat('identity', 'personal', 'Splat', temp=False)
            if splat and splat.lower() == 'companion':
                # Get valid companion types
                valid_types = [t[1] for t in COMPANION_TYPE_CHOICES if t[1] != 'None']
                is_valid, matched_value = self.case_insensitive_in(self.value_change, set(valid_types))
                if not is_valid:
                    self.caller.msg(f"|rInvalid companion type. Valid types are: {', '.join(sorted(valid_types))}|n")
                    return
                # Set the type with proper case
                self.value_change = matched_value
                # Initialize companion stats with the new type
                initialize_companion_stats(self.caller, matched_value)
                return ('identity', 'lineage')

        # When setting Companion special advantages
        elif self.stat_name.lower() in [adv.lower() for adv in SPECIAL_ADVANTAGES.keys()]:
            splat = self.caller.get_stat('identity', 'personal', 'Splat', temp=False)
            companion_type = self.caller.get_stat('identity', 'lineage', 'Companion Type', temp=False)
            
            if splat and splat.lower() == 'companion' and companion_type:
                # Check if this advantage is available for this companion type
                available_advantages = COMPANION_TYPE_ADVANTAGES.get(companion_type, [])
                if self.stat_name.lower() not in [adv.lower() for adv in available_advantages]:
                    self.caller.msg(f"|rThe special advantage '{self.stat_name}' is not available for {companion_type} companions.|n")
                    return

                # Get the advantage info
                advantage_info = next((adv for adv in SPECIAL_ADVANTAGES.items() if adv[0].lower() == self.stat_name.lower()), None)
                if not advantage_info:
                    self.caller.msg(f"|rInvalid special advantage: {self.stat_name}|n")
                    return

                try:
                    value = int(self.value_change)
                    if value not in advantage_info[1]['valid_values']:
                        valid_values_str = ', '.join(map(str, advantage_info[1]['valid_values']))
                        self.caller.msg(f"|rInvalid value for {self.stat_name}. Valid values are: {valid_values_str}|n")
                        return
                    return ('powers', 'special_advantage')
                except ValueError:
                    self.caller.msg("|rSpecial advantage value must be a number.|n")
                    return

        # When setting Possessed-specific stats
        elif self.stat_name.lower() == 'possessed type':
            splat = self.caller.get_stat('identity', 'personal', 'Splat', temp=False)
            if splat and splat.lower() == 'possessed':
                # Get valid possessed types
                valid_types = [t[1] for t in POSSESSED_TYPE_CHOICES if t[1] != 'None']
                is_valid, matched_value = self.case_insensitive_in(self.value_change, set(valid_types))
                if not is_valid:
                    self.caller.msg(f"|rInvalid possessed type. Valid types are: {', '.join(sorted(valid_types))}|n")
                    return
                # Set the type with proper case
                self.value_change = matched_value
                # Initialize possessed stats with the new type
                initialize_possessed_stats(self.caller, matched_value)
                return ('identity', 'lineage')

        # When setting Possessed powers (blessings and charms)
        elif self.stat_name.lower() in ['blessing', 'charm']:
            splat = self.caller.get_stat('identity', 'personal', 'Splat', temp=False)
            possessed_type = self.caller.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
            
            if splat and splat.lower() == 'possessed' and possessed_type:
                # Get available powers for this type
                available_powers = POSSESSED_POWERS.get(possessed_type, {})
                if not available_powers:
                    self.caller.msg(f"|rNo {self.stat_name}s available for {possessed_type}.|n")
                    return

                try:
                    value = int(self.value_change)
                    if value < 0 or value > 5:
                        self.caller.msg(f"|r{self.stat_name} rating must be between 0 and 5.|n")
                        return
                    return ('powers', self.stat_name.lower())
                except ValueError:
                    self.caller.msg(f"|r{self.stat_name} rating must be a number.|n")
                    return

        # Get the stat definition
        stat = Stat.objects.filter(name__iexact=self.stat_name).first()
        if not stat:
            # Special case for Path of Enlightenment
            if self.stat_name.lower() == 'path of enlightenment':
                self.stat_name = 'Path of Enlightenment'  # Use proper case
                splat = self.splat
                if splat and splat.lower() == 'vampire':
                    is_valid, proper_path, error_msg = self._validate_path(self.value_change)
                    if not is_valid:
                        self.caller.msg(error_msg)
                        return
                    
                    # Set the path in identity/personal
                    self._initialize_stat_structure('identity', 'personal')
                    self.caller.db.stats['identity']['personal']['Path of Enlightenment'] = {'perm': proper_path, 'temp': proper_path}
                    
                    # Update path-specific stats
                    self._update_path_stats(proper_path)
                    
                    self.caller.msg(f"|gSet Path of Enlightenment to {proper_path}.|n")
                    return
            
            # If not Path of Enlightenment, try case-insensitive contains search
            matching_stats = Stat.objects.filter(name__icontains=self.stat_name)
            if matching_stats.count() > 1:
                stat_names = [s.name for s in matching_stats]
                self.caller.msg(f"Multiple stats match '{self.stat_name}': {', '.join(stat_names)}. Please be more specific.")
                return
            stat = matching_stats.first()
            if not stat:
                self.caller.msg(f"Stat '{self.stat_name}' not found.")
                return

        # Use the canonical name from the database
        self.stat_name = stat.name
        
        # Handle instances for background stats
        if stat.instanced:
            if not self.instance:
                self._display_instance_requirement_message(self.stat_name)
                return
            full_stat_name = f"{self.stat_name}({self.instance})"
        else:
            if self.instance:
                self.caller.msg(f"|rThe stat '{self.stat_name}' does not support instances.|n")
                return
            full_stat_name = self.stat_name

        # Handle stat removal (empty value)
        if self.value_change == '':
            # For backgrounds, validate splat access even during removal
            if stat.stat_type == 'background':
                # Check splat-specific background restrictions
                is_restricted, required_splat, error_msg = self.get_background_splat_restriction(self.stat_name)
                if is_restricted and splat != required_splat:
                    self.caller.msg(error_msg)
                return

            # Regular stat removal handling
            if stat.category in self.caller.db.stats and stat.stat_type in self.caller.db.stats[stat.category]:
                if full_stat_name in self.caller.db.stats[stat.category][stat.stat_type]:
                    del self.caller.db.stats[stat.category][stat.stat_type][full_stat_name]
                    self.caller.msg(f"|gRemoved stat '{full_stat_name}'.|n")
                    return
            self.caller.msg(f"|rStat '{full_stat_name}' not found.|n")
            return

        # Validate the stat if it's being set (not removed)
        if self.value_change != '':
            is_valid, error_message = self.validate_stat_value(self.stat_name, self.value_change, self.category, self.stat_type)
            if not is_valid:
                self.caller.msg(f"|r{error_message}|n")
                return

        # Handle incremental changes and type conversion
        try:
            if isinstance(self.value_change, str):
                if self.value_change.startswith('+') or self.value_change.startswith('-'):
                    current_value = self.caller.get_stat(self.category, self.stat_type, self.stat_name)
                    if current_value is None:
                        current_value = 0
                    new_value = current_value + int(self.value_change)
                else:
                    try:
                        new_value = int(self.value_change)
                    except ValueError:
                        new_value = self.value_change
            else:
                new_value = self.value_change

            # Ensure proper category initialization for pools
            if self.category == 'pools':
                self._initialize_stat_structure('pools', 'dual')
                
                # Validate Banality value
                if self.stat_name.lower() == 'banality':
                    try:
                        banality_value = int(new_value)
                        if banality_value < 0 or banality_value > 10:
                            self.caller.msg("|rBanality must be between 0 and 10.|n")
                            return
                        new_value = banality_value
                    except ValueError:
                        self.caller.msg("|rBanality must be a number.|n")
                        return

        except (ValueError, TypeError) as e:
            self.caller.msg(f"|rError converting value: {str(e)}|n")
            return

        # Set the stat using set_stat method
        self.set_stat(self.stat_name, new_value, self.category, self.stat_type)

    def initialize_stats(self, character, splat):
        """Initialize the basic stats structure based on splat type."""
        # Convert input splat to title case for display but lowercase for comparison
        splat_title = splat.title()
        if splat_title == "Mortal+":  # Special case for Mortal+
            splat_title = "Mortal+"
        splat_lower = splat.lower()
        if splat_lower == "mortalplus":  # Handle alternative spelling
            splat_lower = "mortal+"
        
        # Get valid splats and convert to lowercase for comparison
        valid_splats = [s.lower() for s in VALID_SPLATS]
        
        if splat_lower not in valid_splats:
            self.caller.msg(f"|rInvalid splat type. Valid types are: {', '.join(VALID_SPLATS)}|n")
            return

        # Initialize base structure with all categories
        base_stats = {}
        for category, _ in CATEGORIES:
            base_stats[category] = {}

        # Set the splat using the title case version for display
        base_stats['other'] = {'splat': {'Splat': {'perm': splat_title, 'temp': splat_title}}}

        # Initialize the character's stats
        character.db.stats = base_stats

        # Initialize splat-specific stats using lowercase for comparison
        if splat_lower == 'vampire':
            initialize_vampire_stats(character, '')
            # Set default Banality for Vampires
            if 'pools' not in character.db.stats:
                character.db.stats['pools'] = {}
            if 'dual' not in character.db.stats['pools']:
                character.db.stats['pools']['dual'] = {}
            character.db.stats['pools']['dual']['Banality'] = {'perm': 5, 'temp': 5}
        elif splat_lower == 'mage':
            initialize_mage_stats(character, '')
            affiliation = character.get_stat('identity', 'lineage', 'Affiliation', temp=False)
            allowed_backgrounds = set(bg.title() for bg in MAGE_BACKGROUNDS)
            if affiliation == 'Technocracy':
                allowed_backgrounds.update(bg.title() for bg in TECHNOCRACY_BACKGROUNDS)
        elif splat_lower == 'shifter':
            initialize_shifter_type(character, '')
            # Initialize shifter-specific categories
            character.db.stats['powers']['gift'] = {}
            character.db.stats['powers']['rite'] = {}
            character.db.stats['advantages']['renown'] = {}
        elif splat_lower == 'changeling':
            initialize_changeling_stats(character, '')
        elif splat_lower == 'mortal+':
            initialize_mortalplus_stats(character, '')
        elif splat_lower == 'possessed':
            # Only initialize basic structure, type-specific initialization happens when type is set
            if 'powers' not in character.db.stats:
                character.db.stats['powers'] = {}
            if 'pools' not in character.db.stats:
                character.db.stats['pools'] = {}
            if 'dual' not in character.db.stats['pools']:
                character.db.stats['pools']['dual'] = {}
            if 'other' not in character.db.stats['pools']:
                character.db.stats['pools']['other'] = {}
            # Initialize power categories
            for category in ['blessing', 'charm', 'gift']:
                if category not in character.db.stats['powers']:
                    character.db.stats['powers'][category] = {}
        elif splat_lower == 'companion':
            initialize_companion_stats(character, '')

        # Set base attributes to 1
        for category, attributes in ATTRIBUTE_CATEGORIES.items():
            for attribute in attributes:
                character.set_stat('attributes', category, attribute, 1, temp=False)
                character.set_stat('attributes', category, attribute, 1, temp=True)

        self.caller.msg(f"|gInitialized {splat_title} character sheet.|n")

    def _initialize_stat_structure(self, category: str, stat_type: str) -> None:
        """
        Initialize the stat structure for a given category and type if it doesn't exist.
        
        Args:
            category: The stat category (e.g., 'attributes', 'abilities', 'powers')
            stat_type: The stat type within the category (e.g., 'physical', 'talent', 'discipline')
        """
        if not hasattr(self.caller, 'db') or not hasattr(self.caller.db, 'stats'):
            self.caller.db.stats = {}
            
        if category not in self.caller.db.stats:
            self.caller.db.stats[category] = {}
            
        if stat_type and stat_type not in self.caller.db.stats[category]:
            self.caller.db.stats[category][stat_type] = {}

    def _update_dependent_stats(self, stat_name: str, value: any) -> None:
        """
        Update any stats that depend on the changed stat.
        
        Args:
            stat_name: The name of the stat that was changed
            value: The new value of the stat
        """
        splat = self.splat
        if not splat:
            return

        # Update pools based on splat type
        if splat == 'Vampire':
            # Update blood pool if generation changes
            if stat_name.lower() == 'generation':
                try:
                    gen_value = int(value)
                    blood_pool = calculate_blood_pool(gen_value)
                    self.caller.set_stat('pools', 'dual', 'Blood', blood_pool, temp=False)
                    self.caller.set_stat('pools', 'dual', 'Blood', blood_pool, temp=True)
                except (ValueError, TypeError):
                    pass
                    
            # Update virtues if Path changes
            elif stat_name == 'Path of Enlightenment':
                update_vampire_virtues_on_path_change(self.caller, value)

        elif splat == 'Mage':
            # Update mage pools when relevant stats change
            update_mage_pools_on_stat_change(self.caller, stat_name, value)

        elif splat == 'Shifter':
            # Update shifter pools when relevant stats change
            if stat_name.lower() in ['breed', 'auspice', 'tribe', 'aspect']:
                update_shifter_pools_on_stat_change(self.caller, stat_name.lower(), value)

        # Update willpower for all splats if virtues change
        if stat_name.lower() in ['conscience', 'self-control', 'courage']:
            new_willpower = calculate_willpower(self.caller)
            if new_willpower is not None:
                self.caller.set_stat('pools', 'dual', 'Willpower', new_willpower, temp=False)
                self.caller.set_stat('pools', 'dual', 'Willpower', new_willpower, temp=True)

    def validate_archetype(self, archetype_name):
        """Validate that an archetype exists and is valid."""
        is_valid, error_msg = validate_archetype(archetype_name)
        if not is_valid:
            return False, error_msg
            
        # Get full archetype info
        archetype = get_archetype_info(archetype_name)
        if archetype:
            return True, f"Set to {archetype['name']} - Willpower regain: {archetype['system']}"
        return True, ""

    def set_stat(self, stat_name: str, value: str, category: str = None, stat_type: str = None) -> None:
        """
        Set a stat value after validation.
        """
        # Get character's splat and type
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
        char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
        
        # Define full_stat_name
        full_stat_name = stat_name
        
        try:
            # Handle incremental changes and type conversion
            if isinstance(value, str):
                if value.startswith('+') or value.startswith('-'):
                    current_value = self.caller.get_stat(category, stat_type, full_stat_name)
                    if current_value is None:
                        current_value = 0
                    new_value = current_value + int(value)
                else:
                    try:
                        new_value = int(value)
                    except ValueError:
                        new_value = value
            else:
                new_value = value

            # Special case handling first
            if stat_name.lower() == 'generation background':
                try:
                    gen_value = int(new_value)
                    if gen_value < -2 or gen_value > 7:
                        self.caller.msg("|rGeneration background must be between -2 (15th) and 7 (6th).|n")
                        return
                    
                    # Convert background value to actual generation
                    generation_map = {
                        -2: "15th", -1: "14th", 0: "13th",
                        1: "12th", 2: "11th", 3: "10th",
                        4: "9th", 5: "8th", 6: "7th",
                        7: "6th"
                    }
                    
                    # Set the background value
                    self.caller.set_stat('backgrounds', 'background', 'Generation', gen_value, temp=False)
                    self.caller.set_stat('backgrounds', 'background', 'Generation', gen_value, temp=True)
                    
                    # Set the actual generation in identity/lineage
                    generation = generation_map.get(gen_value, "13th")
                    self.caller.set_stat('identity', 'lineage', 'Generation', generation, temp=False)
                    self.caller.set_stat('identity', 'lineage', 'Generation', generation, temp=True)
                    
                    # Update blood pool based on generation
                    blood_pool = calculate_blood_pool(gen_value)
                    self.caller.set_stat('pools', 'dual', 'Blood', blood_pool, temp=False)
                    self.caller.set_stat('pools', 'dual', 'Blood', blood_pool, temp=True)
                    
                    self.caller.msg(f"|gGeneration set to {generation} (Blood Pool: {blood_pool}).|n")
                    return
                except ValueError:
                    self.caller.msg("|rGeneration background must be a number.|n")
                    return

            # If no category/type specified yet, try to determine it from the stat name
            if not category or not stat_type:
                category, stat_type = self.detect_ability_category(stat_name)

            # Initialize the category/type structure if needed
            self._initialize_stat_structure(category, stat_type)

            # Set the stat value
            self.caller.set_stat(category, stat_type, full_stat_name, new_value, temp=False)
            self.caller.set_stat(category, stat_type, full_stat_name, new_value, temp=True)

            # Update any dependent stats
            self._update_dependent_stats(stat_name, new_value)

            # For shifters, update pools when identity stats change
            if splat == 'Shifter' and category == 'identity' and stat_type == 'lineage':
                from world.wod20th.utils.shifter_utils import update_shifter_pools_on_stat_change
                update_shifter_pools_on_stat_change(self.caller, stat_name, new_value)

            self.caller.msg(f"|gSet {full_stat_name} to {new_value}.|n")

        except Exception as e:
            self.caller.msg(f"|rError setting stat: {str(e)}|n")
            return