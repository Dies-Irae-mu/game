from evennia import Command, default_cmds
from world.wod20th.utils.sheet_constants import KITH, KNOWLEDGES, SECONDARY_KNOWLEDGES, SECONDARY_SKILLS, SECONDARY_TALENTS, SKILLS, TALENTS
from world.wod20th.models import Stat
from world.wod20th.utils.vampire_utils import initialize_vampire_stats
from world.wod20th.utils.mage_utils import (
    initialize_mage_stats, AFFILIATION, TRADITION, CONVENTION,
    TRADITION_SUBFACTION, METHODOLOGIES, NEPHANDI_FACTION, MAGE_SPHERES
)
from world.wod20th.utils.shifter_utils import (
    initialize_shifter_type, SHIFTER_TYPE_CHOICES, BREED_CHOICES,
    AUSPICE_CHOICES, GAROU_TRIBE_CHOICES, BASTET_TRIBE_CHOICES
)
from world.wod20th.utils.changeling_utils import initialize_changeling_stats
from world.wod20th.utils.mortalplus_utils import (
    initialize_mortalplus_stats, MORTALPLUS_TYPE_CHOICES,
    MORTALPLUS_TYPES, MORTALPLUS_POOLS, MORTALPLUS_POWERS
)
from world.wod20th.utils.possessed_utils import (
    initialize_possessed_stats, POSSESSED_TYPE_CHOICES,
    POSSESSED_TYPES, POSSESSED_POWERS
)
from world.wod20th.utils.companion_utils import (
    initialize_companion_stats, COMPANION_TYPES,
    COMPANION_POWERS
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
    GENERATION_FLAWS, BLOOD_POOL_MAP, get_identity_stats, IDENTITY_PERSONAL, IDENTITY_LINEAGE
)
from world.wod20th.utils.stat_initialization import (
    find_similar_stats, check_stat_exists
)
from world.wod20th.utils.archetype_utils import (
    ARCHETYPES, validate_archetype, get_archetype_info
)
import re

class CmdStats(default_cmds.MuxCommand):
    """
    Usage:
      +stats <character>/<stat>[(<instance>)]/<category>=[+-]<value>
      +stats me/<stat>[(<instance>)]/<category>=[+-]<value>
      +stats <character>=reset
      +stats me=reset
      +stats/specialty <character>/<stat>=<specialty>
      +stats me/specialty <stat>=<specialty>

    Examples:
      +stats Bob/Strength/Physical=+2
      +stats Alice/Firearms/Skill=-1
      +stats John/Status(Ventrue)/Social=3
      +stats me=reset
      +stats me/Nature=Curmudgeon
      +stats Bob/Demeanor=Visionary
      +stats me/specialty Firearms=Sniping
      +stats Bob/specialty Melee=Swords

    This is the staff version of +selfstat with the same functionality
    but can be used on any character.
    """

    key = "+stats"
    aliases = ["stats", "+setstats", "setstats"]
    locks = "cmd:perm(Builder)"
    help_category = "Staff"

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

    def validate_stat_value(self, stat_name: str, value: str, category: str = None, stat_type: str = None) -> tuple:
        """
        Validate a stat value based on its type and category.
        Returns (is_valid, error_message)
        """
        # Get character's splat for validation
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
        char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)

        # Get the stat definition from the database
        stat = Stat.objects.filter(name__iexact=stat_name).first()
        if not stat:
            return False, f"Stat '{stat_name}' not found in database"

        # First validate that the stat can be set in the requested category/type
        if category and stat_type:
            # Special handling for stats that can exist in multiple forms
            if stat_name.lower() in ['empathy', 'seduction', 'time', 'nature', 'wings']:
                # These are handled in their specific sections below
                pass
            else:
                # For all other stats, they must match their database category/type
                if category != stat.category or stat_type != stat.stat_type:
                    return False, f"{stat_name} cannot be set as a {category}.{stat_type}"

        # Special handling for Empathy and Seduction
        if stat_name.lower() in ['empathy', 'seduction']:
            # Check if character can have gifts
            can_have_gifts = (
                splat == 'Shifter' or 
                splat == 'Possessed' or 
                (splat == 'Mortal+' and char_type == 'Kinfolk')
            )
            
            try:
                val = int(value)
                if val < 0 or val > 5:
                    return False, "Values must be between 0 and 5"
            except ValueError:
                return False, "Value must be a number"

            # If explicitly trying to set as a gift
            if category == 'powers' and stat_type == 'gift':
                if not can_have_gifts:
                    return False, f"Only Shifters, Kinfolk, and Possessed can have {stat_name} as a Gift"
                return True, ""

            # If explicitly setting as an ability
            if stat_name.lower() == 'empathy':
                if category == 'abilities' and stat_type == 'talent':
                    return True, ""
            else:  # seduction
                if category == 'secondary_abilities' and stat_type == 'secondary_talent':
                    return True, ""

            # If no category specified, default to ability
            if not category:
                if stat_name.lower() == 'empathy':
                    self.category = 'abilities'
                    self.stat_type = 'talent'
                else:  # seduction
                    self.category = 'secondary_abilities'
                    self.stat_type = 'secondary_talent'
                return True, ""

            # If trying to set in any other category/type
            return False, f"{stat_name} must be set as either an ability or a gift"

        # Special handling for Time based on splat
        if stat_name.lower() == 'time':
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
            
            if splat == 'Mage':
                if stat_type == 'realm':
                    return False, "For Mages, Time is a Sphere and cannot be set as a Realm"
                self.category = 'powers'
                self.stat_type = 'sphere'
                # Remove from realm if it exists
                if 'powers' in self.caller.db.stats and 'realm' in self.caller.db.stats['powers']:
                    if 'Time' in self.caller.db.stats['powers']['realm']:
                        del self.caller.db.stats['powers']['realm']['Time']
            elif splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain'):
                if stat_type == 'sphere':
                    return False, "For Changelings and Kinain, Time is a Realm and cannot be set as a Sphere"
                self.category = 'powers'
                self.stat_type = 'realm'
                # Remove from sphere if it exists
                if 'powers' in self.caller.db.stats and 'sphere' in self.caller.db.stats['powers']:
                    if 'Time' in self.caller.db.stats['powers']['sphere']:
                        del self.caller.db.stats['powers']['sphere']['Time']
            
            try:
                val = int(value)
                if val < 0 or val > 5:
                    return False, "Power values must be between 0 and 5"
                return True, ""
            except ValueError:
                return False, "Power values must be numbers"

        # Handle Nature validation first
        if stat_name in ['Nature', 'Demeanor']:
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
            
            # For Changelings and Kinain, Nature can only be a realm power
            if splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain'):
                if stat_name == 'Nature':
                    if category == 'identity' or stat_type == 'personal':
                        return False, "Changelings and Kinain can only set Nature as a Realm power"
                    if category == 'powers' and stat_type == 'realm':
                        try:
                            val = int(value)
                            if val < 0 or val > 5:
                                return False, "Realm values must be between 0 and 5"
                            return True, ""
                        except ValueError:
                            return False, "Realm values must be numbers"
                    return False, "Nature must be set as a Realm power for Changelings and Kinain"
                else:  # Demeanor
                    return False, "Changelings and Kinain use Legacies instead of Nature/Demeanor"
            
            # For all other splats, Nature/Demeanor are identity stats
            else:
                # If it's being set as a realm power (which it shouldn't be)
                if category == 'powers' and stat_type == 'realm':
                    return False, "Only Changelings and Kinain can have Nature as a realm"
                # If it's being set as an identity stat
                if category == 'identity' and stat_type == 'personal':
                    is_valid, error = validate_archetype(value)
                    if not is_valid:
                        return False, error
                # If no category/type specified, treat as identity.personal
                elif not category and not stat_type:
                    is_valid, error = validate_archetype(value)
                    if not is_valid:
                        return False, error
                    # Set category and type for identity.personal
                    self.category = 'identity'
                    self.stat_type = 'personal'

        # Handle pool validation
        if category == 'pools' and stat_type in POOL_TYPES:
            try:
                val = int(value)
                pool_limits = POOL_TYPES[stat_type].get(stat_name, {})
                if val < pool_limits.get('min', 0) or val > pool_limits.get('max', 10):
                    return False, f"Value must be between {pool_limits['min']} and {pool_limits['max']}"
            except ValueError:
                return False, "Pool values must be numbers"

        # Handle power validation
        if category == 'powers' and stat_type in POWER_CATEGORIES:
            try:
                val = int(value)
                if val < 0 or val > 5:  # Most powers are capped at 5
                    return False, "Power values must be between 0 and 5"
            except ValueError:
                return False, "Power values must be numbers"

        # Handle attribute validation
        if category == 'attributes' and stat_name in sum(ATTRIBUTE_CATEGORIES.values(), []):
            try:
                val = int(value)
                if val < 1 or val > 5:
                    return False, "Attribute values must be between 1 and 5"
            except ValueError:
                return False, "Attribute values must be numbers"

        # Handle ability validation
        if category == 'abilities' and stat_type in ABILITY_TYPES:
            try:
                val = int(value)
                if val < 0 or val > 5:
                    return False, "Ability values must be between 0 and 5"
            except ValueError:
                return False, "Ability values must be numbers"
        # Handle ability category validation
        if category == 'abilities':
            # Check if it's a primary ability
            if stat_name in TALENTS:
                self.stat_type = 'talent'
            elif stat_name in SKILLS:
                self.stat_type = 'skill'
            elif stat_name in KNOWLEDGES:
                self.stat_type = 'knowledge'
            else:
                return False, f"{stat_name} is not a valid primary ability"

        # Handle secondary ability validation
        if category == 'secondary_abilities':
            try:
                val = int(value)
                if val < 0 or val > 5:
                    return False, "Secondary ability values must be between 0 and 5"
            except ValueError:
                return False, "Secondary ability values must be numbers"
            
            # Check if it's a secondary ability
            if stat_name in SECONDARY_TALENTS:
                self.stat_type = 'secondary_talent'
            elif stat_name in SECONDARY_SKILLS:
                self.stat_type = 'secondary_skill'
            elif stat_name in SECONDARY_KNOWLEDGES:
                self.stat_type = 'secondary_knowledge'
            else:
                return False, f"{stat_name} is not a valid secondary ability"

        # Handle realm validation
        if stat_type == 'realm':
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
            if splat != 'Changeling' and (splat != 'Mortal+' or char_type != 'Kinain'):
                return False, "Only Changelings and Kinain can have Realms"

        # Handle special advantage validation
        if stat_type == 'special_advantage':
            if stat_name in SPECIAL_ADVANTAGES:
                advantage = SPECIAL_ADVANTAGES[stat_name]
                try:
                    val = int(value)
                    if val < advantage['min'] or val > advantage['max']:
                        return False, f"Value must be between {advantage['min']} and {advantage['max']}"
                except ValueError:
                    return False, "Special advantage values must be numbers"

        # Special handling for stats that exist in multiple forms
        # TODO: Add more multi-form stat validations here as they are discovered
        # Current implementations:
        # - Wings (Possessed Blessing vs Companion Special Advantage)
        # - Empathy (Ability vs Gift)
        # - Seduction (Secondary Ability vs Gift)
        # - Time (Mage Sphere vs Changeling/Kinain Realm)
        # - Nature (Identity vs Changeling/Kinain Realm)
        if stat_name.lower() == 'wings':
            # Get character's splat and type
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            
            # Check if character can have each version
            can_have_blessing = (splat == 'Possessed')
            can_have_special_advantage = (splat == 'Companion')
            
            # If no category specified and character could potentially have multiple versions
            if not category and (can_have_blessing or can_have_special_advantage):
                options = []
                if can_have_blessing:
                    options.append(f"  - {stat_name}/blessing (Possessed Wings)")
                if can_have_special_advantage:
                    options.append(f"  - {stat_name}/special_advantage (Companion Wings)")
                return False, f"Multiple versions of '{stat_name}' exist. Please specify one of:\n" + "\n".join(options)
            
            # Validate based on category and character type
            if category == 'powers' and stat_type == 'blessing':
                if not can_have_blessing:
                    return False, f"Only Possessed characters can have {stat_name} as a Blessing"
                try:
                    val = int(value)
                    if val != 1:  # Blessing version only has value 1
                        return False, "Blessing values must be 1"
                    return True, ""
                except ValueError:
                    return False, "Blessing values must be numbers"
                    
            elif category == 'powers' and stat_type == 'special_advantage':
                if not can_have_special_advantage:
                    return False, f"Only Companions can have {stat_name} as a Special Advantage"
                try:
                    val = int(value)
                    if val not in [3, 5]:  # Special Advantage version only allows 3 or 5
                        return False, "Special Advantage values must be 3 or 5"
                    return True, ""
                except ValueError:
                    return False, "Special Advantage values must be numbers"

        if stat_name.lower() == 'size':
            # Get character's splat and type
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            
            # Check if character can have each version
            can_have_possessed_size = (splat == 'Possessed')
            can_have_companion_size = (splat == 'Companion')
            
            # If no category specified and character could potentially have multiple versions
            if not category and (can_have_possessed_size or can_have_companion_size):
                options = []
                if can_have_possessed_size:
                    options.append(f"  - {stat_name}/blessing (Possessed Size)")
                if can_have_companion_size:
                    options.append(f"  - {stat_name}/special_advantage (Companion Size)")
                return False, f"Multiple versions of '{stat_name}' exist. Please specify one of:\n" + "\n".join(options)

        if stat_name.lower() == 'totem':
            # This is the background stat - no special handling needed
            # It's already mapped to ('backgrounds', 'background') in category_map
            pass

        if stat_name.lower() == 'patron totem':
            # Get character's splat and type
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            shifter_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
            
            if splat != 'Shifter':
                return False, "Only Shifters can have Patron Totem"
            
            if shifter_type == 'Bastet':
                return False, "Bastet use Jamak Spirit instead of Patron Totem"
            
            if category != 'identity' or stat_type != 'lineage':
                return False, "Patron Totem must be set using +selfstat Patron Totem/lineage=<totem name>"

        if stat_name.lower() == 'jamak spirit':
            # Get character's splat and type
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            shifter_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
            
            if splat != 'Shifter' or shifter_type != 'Bastet':
                return False, "Only Bastet can have Jamak Spirit"
            
            if category != 'identity' or stat_type != 'lineage':
                return False, "Jamak Spirit must be set using +selfstat Jamak Spirit/lineage=<spirit name>"

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

    def parse(self):
        """Parse the arguments."""
        self.target = None
        self.stat_name = ""
        self.instance = None
        self.category = None
        self.value_change = None
        self.temp = False
        self.stat_type = None 
        
        args = self.args.strip()
        if not args:
            self.caller.msg("Usage: +stats <character>/<stat>[(<instance>)]/<category>=[+-]<value>")
            return

        # First split on = to separate value
        if '=' in args:
            left, self.value_change = args.split('=', 1)
            left = left.strip()
            self.value_change = self.value_change.strip()
        else:
            left = args
            self.value_change = None

        # Split left side on first / to get character and rest
        if '/' in left:
            char_name, rest = left.split('/', 1)
            # Use global search for finding characters
            self.target = self.caller.search(char_name.strip(), global_search=True)
            if not self.target:
                return
            # Continue parsing rest as before for stat/category
            self.parse_stat_and_category(rest)
        else:
            # Handle case where only character name is provided (for reset)
            # Use global search here too
            self.target = self.caller.search(left, global_search=True)
            return

    def parse_stat_and_category(self, stat_string):
        """Parse the stat and category portion of the command."""
        # Handle instance format: stat(instance)/category
        if '(' in stat_string and ')' in stat_string:
            self.stat_name, instance_and_category = stat_string.split('(', 1)
            instance_part, category_part = instance_and_category.split(')', 1)
            self.instance = instance_part.strip()
            if '/' in category_part:
                category_or_type = category_part.lstrip('/').strip()
                # Map the user-provided category/type to the correct values
                self.map_category_and_type(category_or_type)
        else:
            # Handle non-instance format: stat/category
            if '/' in stat_string:
                self.stat_name, category_or_type = stat_string.split('/', 1)
                # Map the user-provided category/type to the correct values
                self.map_category_and_type(category_or_type.strip())
            else:
                self.stat_name = stat_string
                self.category = None
                self.stat_type = None
            
        self.stat_name = self.stat_name.strip()

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

    def func(self):
        """Execute the command."""
        # Check staff permissions
        if not self.caller.check_permstring("Builder"):
            self.caller.msg("You do not have permission to use this command.")
            return

        # Ensure we have a target
        if not self.target:
            self.caller.msg("You must specify a target character!")
            return

        # Check if target character is approved
        if self.target.db.approved:
            self.caller.msg("|rError: Approved characters cannot use chargen commands. Please contact staff for any needed changes.|n")
            return

        # Get character's splat type first
        splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)

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
            self.initialize_stats(self.target, self.value_change.title())
            return

        # Special handling for type setting
        if self.stat_name.lower() == 'type':
            if splat and splat.lower() == 'shifter':
                # Convert tuple list to just the type names for validation
                valid_types = [t[1] for t in SHIFTER_TYPE_CHOICES if t[1] != 'None']
                if self.value_change.title() not in valid_types:
                    self.caller.msg(f"|rInvalid shifter type. Valid types are: {', '.join(valid_types)}|n")
                    return
                # Set the type in identity/lineage
                self.target.set_stat('identity', 'lineage', 'Type', self.value_change.title(), temp=False)
                self.target.set_stat('identity', 'lineage', 'Type', self.value_change.title(), temp=True)
                # Initialize shifter-specific stats for the chosen type
                initialize_shifter_type(self.target, self.value_change.title())
                self.caller.msg(f"|gSet shifter type to {self.value_change.title()} and initialized appropriate stats.|n")
                return
            elif splat and splat.lower() == 'mortal+':
                # Convert tuple list to just the type names for validation
                valid_types = [t[1] for t in MORTALPLUS_TYPE_CHOICES if t[1] != 'None']
                if self.value_change.title() not in valid_types:
                    self.caller.msg(f"|rInvalid Mortal+ type. Valid types are: {', '.join(valid_types)}|n")
                    return
                # Set the type in identity/lineage
                self.target.set_stat('identity', 'lineage', 'Mortal+ Type', self.value_change.title(), temp=False)
                self.target.set_stat('identity', 'lineage', 'Mortal+ Type', self.value_change.title(), temp=True)
                # Initialize mortal+-specific stats for the chosen type
                initialize_mortalplus_stats(self.target, self.value_change.title())
                self.caller.msg(f"|gSet Mortal+ type to {self.value_change.title()} and initialized appropriate stats.|n")
                return
            elif splat and splat.lower() == 'possessed':
                # Convert tuple list to just the type names for validation
                valid_types = [t[1] for t in POSSESSED_TYPE_CHOICES if t[1] != 'None']
                if self.value_change.title() not in valid_types:
                    self.caller.msg(f"|rInvalid Possessed type. Valid types are: {', '.join(valid_types)}|n")
                    return
                # Set the type in identity/lineage
                self.target.set_stat('identity', 'lineage', 'Possessed Type', self.value_change.title(), temp=False)
                self.target.set_stat('identity', 'lineage', 'Possessed Type', self.value_change.title(), temp=True)
                # Initialize possessed-specific stats for the chosen type
                initialize_possessed_stats(self.target, self.value_change.title())
                self.caller.msg(f"|gSet Possessed type to {self.value_change.title()} and initialized appropriate stats.|n")
                return

        # Special handling for mage affiliation/tradition/convention setting
        if self.stat_name.lower() in ['affiliation', 'tradition', 'convention', 'nephandi faction']:
            splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
            affiliation = self.target.get_stat('identity', 'lineage', 'Affiliation', temp=False)
            
            if splat and splat.lower() == 'mage':
                # Handle affiliation setting
                if self.stat_name.lower() == 'affiliation':
                    is_valid, matched_value = self.case_insensitive_in(self.value_change, AFFILIATION)
                    if not is_valid:
                        self.caller.msg(f"|rInvalid affiliation. Valid affiliations are: {', '.join(sorted(AFFILIATION))}|n")
                        return
                    self.value_change = matched_value
                    # Initialize mage-specific stats for the chosen affiliation
                    initialize_mage_stats(self.target, matched_value)
                    self.caller.msg(f"|gSet mage affiliation to {matched_value} and initialized appropriate stats.|n")
                    return

                # Handle tradition/convention/faction based on affiliation
                if not affiliation:
                    self.caller.msg("|rError: Must set affiliation before setting tradition/convention/faction.|n")
                    return

                if affiliation == 'Traditions' and self.stat_name.lower() == 'tradition':
                    is_valid, matched_value = self.case_insensitive_in(self.value_change, TRADITION)
                    if not is_valid:
                        self.caller.msg(f"|rInvalid tradition. Valid traditions are: {', '.join(sorted(TRADITION))}|n")
                        return
                    self.value_change = matched_value
                
                elif affiliation == 'Technocracy' and self.stat_name.lower() == 'convention':
                    is_valid, matched_value = self.case_insensitive_in(self.value_change, CONVENTION)
                    if not is_valid:
                        self.caller.msg(f"|rInvalid convention. Valid conventions are: {', '.join(sorted(CONVENTION))}|n")
                        return
                    self.value_change = matched_value
                
                elif affiliation == 'Nephandi' and self.stat_name.lower() == 'nephandi faction':
                    is_valid, matched_value = self.case_insensitive_in(self.value_change, NEPHANDI_FACTION)
                    if not is_valid:
                        self.caller.msg(f"|rInvalid Nephandi faction. Valid factions are: {', '.join(sorted(NEPHANDI_FACTION))}|n")
                        return
                    self.value_change = matched_value

        # Special handling for mage subfaction/methodology setting
        if self.stat_name.lower() in ['traditions subfaction', 'methodology']:
            splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
            affiliation = self.target.get_stat('identity', 'lineage', 'Affiliation', temp=False)
            if splat and splat.lower() == 'mage':
                if affiliation == 'Traditions':
                    tradition = self.target.get_stat('identity', 'lineage', 'Tradition', temp=False)
                    if not tradition:
                        self.caller.msg("|rError: Must set tradition before setting subfaction.|n")
                        return
                    is_valid, matched_value = self.case_insensitive_in_nested(self.value_change, TRADITION_SUBFACTION, tradition)
                    if not is_valid:
                        self.caller.msg(f"|rInvalid subfaction for {tradition}. Valid subfactions are: {', '.join(sorted(TRADITION_SUBFACTION.get(tradition, [])))}|n")
                        return
                    self.value_change = matched_value

                elif affiliation == 'Technocracy':
                    convention = self.target.get_stat('identity', 'lineage', 'Convention', temp=False)
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
            splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
            shifter_type = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
            if splat and splat.lower() == 'shifter' and shifter_type:
                valid_breeds = BREED_CHOICES.get(shifter_type, [])
                is_valid, matched_value = self.case_insensitive_in(self.value_change, set(valid_breeds))
                if not is_valid:
                    self.caller.msg(f"|rInvalid breed for {shifter_type}. Valid breeds are: {', '.join(sorted(valid_breeds))}|n")
                    return
                self.value_change = matched_value

        # Special handling for changeling kith setting
        if self.stat_name.lower() == 'kith':
            splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
            if splat and splat.lower() == 'changeling':
                is_valid, matched_value = self.case_insensitive_in(self.value_change, KITH)
                if not is_valid:
                    self.caller.msg(f"|rInvalid kith. Valid kiths are: {', '.join(sorted(KITH))}|n")
                    return
                self.value_change = matched_value

        # Get the stat definition
        stat = Stat.objects.filter(name__iexact=self.stat_name).first()
        if not stat:
            # If exact match fails, try a case-insensitive contains search
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
                self.caller.msg(f"The stat '{self.stat_name}' requires an instance. Use the format: {self.stat_name}(instance)")
                return
            full_stat_name = f"{self.stat_name}({self.instance})"
        else:
            if self.instance:
                self.caller.msg(f"The stat '{self.stat_name}' does not support instances.")
                return
            full_stat_name = self.stat_name

        # Handle stat removal (empty value)
        if self.value_change == '':
            # Special handling for Empathy and Seduction removal
            if self.stat_name.lower() in ['empathy', 'seduction']:
                removed = False
                if self.stat_name.lower() == 'empathy':
                    # Try to remove from abilities.talent
                    if ('abilities' in self.target.db.stats and 
                        'talent' in self.target.db.stats['abilities'] and 
                        'Empathy' in self.target.db.stats['abilities']['talent']):
                        del self.target.db.stats['abilities']['talent']['Empathy']
                        removed = True
                    # Try to remove from powers.gift
                    if ('powers' in self.target.db.stats and 
                        'gift' in self.target.db.stats['powers'] and 
                        'Empathy' in self.target.db.stats['powers']['gift']):
                        del self.target.db.stats['powers']['gift']['Empathy']
                        removed = True
                else:  # seduction
                    # Try to remove from secondary_abilities.secondary_talent
                    if ('secondary_abilities' in self.target.db.stats and 
                        'secondary_talent' in self.target.db.stats['secondary_abilities'] and 
                        'Seduction' in self.target.db.stats['secondary_abilities']['secondary_talent']):
                        del self.target.db.stats['secondary_abilities']['secondary_talent']['Seduction']
                        removed = True
                    # Try to remove from powers.gift
                    if ('powers' in self.target.db.stats and 
                        'gift' in self.target.db.stats['powers'] and 
                        'Seduction' in self.target.db.stats['powers']['gift']):
                        del self.target.db.stats['powers']['gift']['Seduction']
                        removed = True
                
                if removed:
                    self.caller.msg(f"|gRemoved stat '{self.target.name}'s {full_stat_name}.|n")
                    return
                self.caller.msg(f"|rStat '{full_stat_name}' not found.|n")
                return

            # Regular stat removal handling
            if stat.category in self.target.db.stats and stat.stat_type in self.target.db.stats[stat.category]:
                if full_stat_name in self.target.db.stats[stat.category][stat.stat_type]:
                    del self.target.db.stats[stat.category][stat.stat_type][full_stat_name]
                    self.caller.msg(f"|gRemoved stat '{self.target.name}'s {full_stat_name}.|n")
                    return
            self.caller.msg(f"|rStat '{full_stat_name}' not found.|n")
            return

        # Validate the stat if it's being set (not removed)
        if self.value_change != '':
            is_valid, error_message = self.validate_stat_value(self.stat_name, self.value_change, self.category, self.stat_type)
            if not is_valid:
                self.caller.msg(f"|r{error_message}|n")
                return

        # Handle incremental changes
        try:
            if self.value_change.startswith('+') or self.value_change.startswith('-'):
                current_value = self.target.get_stat(stat.category, stat.stat_type, full_stat_name)
                if current_value is None:
                    current_value = 0
                new_value = current_value + int(self.value_change)
            else:
                new_value = int(self.value_change) if self.value_change.isdigit() else self.value_change
        except (ValueError, TypeError):
            new_value = self.value_change

        # Update the stat
        try:
            # Special handling for Empathy and Seduction to ensure they're stored correctly
            if self.stat_name.lower() in ['empathy', 'seduction']:
                splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
                char_type = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
                
                # Check if character can have gifts
                can_have_gifts = (
                    splat == 'Shifter' or 
                    splat == 'Possessed' or 
                    (splat == 'Mortal+' and char_type == 'Kinfolk')
                )
                
                # If explicitly setting as a gift and character can have gifts
                if self.category == 'powers' and self.stat_type == 'gift' and can_have_gifts:
                    # Ensure powers category exists
                    if 'powers' not in self.target.db.stats:
                        self.target.db.stats['powers'] = {}
                    if 'gift' not in self.target.db.stats['powers']:
                        self.target.db.stats['powers']['gift'] = {}
                    
                    # Set as gift
                    self.target.set_stat('powers', 'gift', self.stat_name, new_value, temp=False)
                    self.target.set_stat('powers', 'gift', self.stat_name, new_value, temp=True)
                    self.caller.msg(f"|gUpdated {self.target.name}'s {full_stat_name} Gift to {new_value}.|n")
                    return
                
                # If explicitly setting as an ability
                if self.stat_name.lower() == 'empathy':
                    # Ensure abilities category exists
                    if 'abilities' not in self.target.db.stats:
                        self.target.db.stats['abilities'] = {}
                    if 'talent' not in self.target.db.stats['abilities']:
                        self.target.db.stats['abilities']['talent'] = {}
                    
                    self.target.set_stat('abilities', 'talent', self.stat_name, new_value, temp=False)
                    self.target.set_stat('abilities', 'talent', self.stat_name, new_value, temp=True)
                    self.caller.msg(f"|gUpdated {self.target.name}'s {full_stat_name} Ability to {new_value}.|n")
                else:  # seduction
                    # Ensure secondary_abilities category exists
                    if 'secondary_abilities' not in self.target.db.stats:
                        self.target.db.stats['secondary_abilities'] = {}
                    if 'secondary_talent' not in self.target.db.stats['secondary_abilities']:
                        self.target.db.stats['secondary_abilities']['secondary_talent'] = {}
                    
                    self.target.set_stat('secondary_abilities', 'secondary_talent', self.stat_name, new_value, temp=False)
                    self.target.set_stat('secondary_abilities', 'secondary_talent', self.stat_name, new_value, temp=True)
                    self.caller.msg(f"|gUpdated {self.target.name}'s {full_stat_name} Ability to {new_value}.|n")
                return

            # Special handling for Time based on splat
            if self.stat_name.lower() == 'time':
                splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
                char_type = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
                
                if splat == 'Mage':
                    # For Mages, Time is a sphere
                    self.category = 'powers'
                    self.stat_type = 'sphere'
                    # Remove from realm if it exists
                    if 'powers' in self.target.db.stats and 'realm' in self.target.db.stats['powers']:
                        if 'Time' in self.target.db.stats['powers']['realm']:
                            del self.target.db.stats['powers']['realm']['Time']
                    # Set in sphere
                    self.target.set_stat('powers', 'sphere', 'Time', new_value, temp=False)
                    self.target.set_stat('powers', 'sphere', 'Time', new_value, temp=True)
                elif splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain'):
                    # For Changelings/Kinain, Time is a realm
                    self.category = 'powers'
                    self.stat_type = 'realm'
                    # Remove from sphere if it exists
                    if 'powers' in self.target.db.stats and 'sphere' in self.target.db.stats['powers']:
                        if 'Time' in self.target.db.stats['powers']['sphere']:
                            del self.target.db.stats['powers']['sphere']['Time']
                    # Set in realm
                    self.target.set_stat('powers', 'realm', 'Time', new_value, temp=False)
                    self.target.set_stat('powers', 'realm', 'Time', new_value, temp=True)
                
                self.caller.msg(f"|gUpdated {self.target.name}'s Time to {new_value} (both permanent and temporary).|n")
                return

            # Special handling for Nature to ensure it's stored in identity.personal
            if self.stat_name == 'Nature':
                # Ensure identity.personal exists
                if 'identity' not in self.target.db.stats:
                    self.target.db.stats['identity'] = {}
                if 'personal' not in self.target.db.stats['identity']:
                    self.target.db.stats['identity']['personal'] = {}
                # Remove any existing Nature from powers.realm
                if 'powers' in self.target.db.stats and 'realm' in self.target.db.stats['powers']:
                    if 'Nature' in self.target.db.stats['powers']['realm']:
                        del self.target.db.stats['powers']['realm']['Nature']
                # Set Nature in identity.personal
                self.target.db.stats['identity']['personal']['Nature'] = {'perm': new_value, 'temp': new_value}
                self.caller.msg(f"|gUpdated {self.target.name}'s Nature to {new_value} (both permanent and temporary).|n")
                return

            self.target.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=False)
            
            # Special handling for Generation background
            if stat.stat_type == 'background' and full_stat_name == 'Generation':
                # Update character's generation in lineage
                generation_str = GENERATION_MAP.get(new_value, "13th")  # Default to 13th if not found
                self.target.set_stat('identity', 'lineage', 'Generation', generation_str, temp=False)
                self.target.set_stat('identity', 'lineage', 'Generation', generation_str, temp=True)
                
                # Update blood pool based on generation
                blood_pool = BLOOD_POOL_MAP.get(new_value, 10)  # Default to 10 if not found
                self.target.set_stat('pools', 'dual', 'Blood', blood_pool, temp=False)
                self.target.set_stat('pools', 'dual', 'Blood', blood_pool, temp=True)
                
                self.caller.msg(f"|gUpdated {self.target.name}'s Generation to {generation_str} and Blood Pool to {blood_pool}.|n")

            # Special handling for Generation flaws
            elif stat.stat_type == 'flaw' and full_stat_name.lower() in ['14th generation', '15th generation']:
                # Get the generation modifier from the flaw
                gen_modifier = GENERATION_FLAWS.get(full_stat_name.lower(), 0)
                
                # Update Generation background
                self.target.set_stat('advantages', 'background', 'Generation', gen_modifier, temp=False)
                self.target.set_stat('advantages', 'background', 'Generation', gen_modifier, temp=True)
                
                # Update character's generation in lineage
                generation_str = GENERATION_MAP.get(gen_modifier, "13th")  # Default to 13th if not found
                self.target.set_stat('identity', 'lineage', 'Generation', generation_str, temp=False)
                self.target.set_stat('identity', 'lineage', 'Generation', generation_str, temp=True)
                
                # Update blood pool based on generation
                blood_pool = BLOOD_POOL_MAP.get(gen_modifier, 10)  # Default to 10 if not found
                self.target.set_stat('pools', 'dual', 'Blood', blood_pool, temp=False)
                self.target.set_stat('pools', 'dual', 'Blood', blood_pool, temp=True)
                
                self.caller.msg(f"|gAdded {full_stat_name} flaw and updated Generation to {generation_str} and Blood Pool to {blood_pool}.|n")
            
            # During character generation (when character is not approved), 
            # always set temp value equal to permanent value
            if not self.target.db.approved:
                self.target.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=True)
                self.caller.msg(f"|gUpdated {self.target.name}'s {full_stat_name} to {new_value} (both permanent and temporary).|n")
            # If already approved, only update temp for pools and dual stats
            elif stat.category == 'pools' or stat.stat_type == 'dual':
                self.target.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=True)
                self.caller.msg(f"|gUpdated {self.target.name}'s {full_stat_name} to {new_value} (both permanent and temporary).|n")
            else:
                self.caller.msg(f"|gUpdated {self.target.name}'s {full_stat_name} to {new_value}.|n")

            # After setting a stat, recalculate Willpower and path
            if full_stat_name in ['Courage', 'Self-Control', 'Conscience', 'Conviction', 'Instinct']:
                # Get splat type
                splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
                
                if splat and splat.lower() == 'vampire':
                    # For vampires, calculate path based on Path
                    path = calculate_path(self.target)
                    self.target.set_stat('pools', 'moral', 'path', path, temp=False)
                    self.target.set_stat('pools', 'moral', 'path', path, temp=True)
                    self.caller.msg(f"|gRecalculated path to {path}.|n")
                
                # Calculate Willpower for all types
                willpower = calculate_willpower(self.target)
                self.target.set_stat('pools', 'dual', 'Willpower', willpower, temp=False)
                self.target.set_stat('pools', 'dual', 'Willpower', willpower, temp=True)
                self.caller.msg(f"|gRecalculated Willpower to {willpower}.|n")

        except ValueError as e:
            self.caller.msg(str(e))

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
        elif splat_lower == 'mage':
            initialize_mage_stats(character, '')
        elif splat_lower == 'shifter':
            initialize_shifter_type(character, '')
            # Initialize shifter-specific categories
            character.db.stats['powers']['gift'] = {}
            character.db.stats['powers']['rite'] = {}
            character.db.stats['advantages']['renown'] = {}
        elif splat_lower == 'changeling':
            initialize_changeling_stats(character, '', '')
        elif splat_lower == 'mortal+':
            initialize_mortalplus_stats(character, '')
        elif splat_lower == 'possessed':
            initialize_possessed_stats(character, '')
        elif splat_lower == 'companion':
            initialize_companion_stats(character, '')

        # Set base attributes to 1
        for category, attributes in ATTRIBUTE_CATEGORIES.items():
            for attribute in attributes:
                character.set_stat('attributes', category, attribute, 1, temp=False)
                character.set_stat('attributes', category, attribute, 1, temp=True)

        self.caller.msg(f"|gInitialized {splat_title} character sheet.|n")

    def validate_archetype(self, archetype_name):
        """Validate that an archetype exists and is valid."""
        archetype_name = archetype_name.lower()
        if archetype_name not in ARCHETYPES:
            valid_archetypes = ', '.join(sorted([a['name'] for a in ARCHETYPES.values()]))
            return False, f"Invalid archetype. Valid archetypes are: {valid_archetypes}"
        return True, ""