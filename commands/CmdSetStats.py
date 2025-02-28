from evennia.commands.default.muxcommand import MuxCommand
from world.wod20th.utils.sheet_constants import (
    KITH, KNOWLEDGES, SECONDARY_KNOWLEDGES, SECONDARY_SKILLS, 
    SECONDARY_TALENTS, SKILLS, TALENTS, CLAN, BREED, GAROU_TRIBE,
    SEEMING, PATHS_OF_ENLIGHTENMENT, SECT, AFFILIATION, TRADITION,
    CONVENTION, NEPHANDI_FACTION
)
from world.wod20th.utils.stat_mappings import (
    ALL_RITES, CATEGORIES, KINAIN_BACKGROUNDS, STAT_TYPES, STAT_TYPE_TO_CATEGORY,
    IDENTITY_STATS, SPLAT_STAT_OVERRIDES, ALL_RITES,
    POOL_TYPES, POWER_CATEGORIES, ABILITY_TYPES,
    ATTRIBUTE_CATEGORIES, SPECIAL_ADVANTAGES,
    STAT_VALIDATION, VALID_SPLATS, GENERATION_MAP,
    GENERATION_FLAWS, BLOOD_POOL_MAP, get_identity_stats,
    UNIVERSAL_BACKGROUNDS, VAMPIRE_BACKGROUNDS,
    CHANGELING_BACKGROUNDS, MAGE_BACKGROUNDS,
    TECHNOCRACY_BACKGROUNDS, TRADITIONS_BACKGROUNDS,
    NEPHANDI_BACKGROUNDS, SHIFTER_BACKGROUNDS,
    SORCERER_BACKGROUNDS, IDENTITY_PERSONAL, IDENTITY_LINEAGE,
    ARTS, REALMS, VALID_DATES, MERIT_VALUES, FLAW_VALUES,
    MERIT_CATEGORIES, FLAW_CATEGORIES, MERIT_SPLAT_RESTRICTIONS,
    FLAW_SPLAT_RESTRICTIONS
)
from world.wod20th.models import Stat
from world.wod20th.utils.vampire_utils import (
    calculate_blood_pool, initialize_vampire_stats, update_vampire_virtues_on_path_change, 
    CLAN_CHOICES, get_clan_disciplines, validate_vampire_stats, validate_vampire_path
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
    FAE_COURTS, HOUSES, initialize_changeling_stats, KITH, SEEMING, ARTS, REALMS,
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
    COMPANION_POWERS, validate_companion_stats
)
from world.wod20th.utils.virtue_utils import (
    calculate_willpower, calculate_path, PATH_VIRTUES
)
from world.wod20th.utils.stat_initialization import (
    find_similar_stats, check_stat_exists
)
from world.wod20th.utils.archetype_utils import (
    ARCHETYPES, validate_archetype, get_archetype_info
)
from world.wod20th.utils.banality import get_default_banality
import re

REQUIRED_INSTANCES = ['Library', 'Status', 'Influence', 'Wonder', 'Secret Weapon', 'Companion', 
                      'Familiar', 'Enhancement', 'Laboratory', 'Favor', 'Acute Senses', 
                      'Enchanting Feature', 'Secret Code Language', 'Hideaway', 'Safehouse', 
                      'Sphere Natural', 'Phobia', 'Addiction', 'Allies', 'Contacts', 'Caretaker',
                      'Alternate Identity', 'Equipment', 'Professional Certification', 'Allergic',
                      'Impediment', 'Enemy', 'Mentor', 'Old Flame', 'Additional Discipline', 
                      'Totem', 'Boon', 'Treasure', 'Geas', 'Fetish']

class CmdStats(MuxCommand):
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

    @property
    def splat(self) -> str:
        """Get the character's splat type."""
        return self.caller.get_stat('other', 'splat', 'Splat', temp=False)

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
        splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
        char_type = self.target.get_stat('identity', 'lineage', 'Type', temp=False)

        # Get the stat definition from the database
        from world.wod20th.models import Stat
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
            splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
            char_type = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
            
            if splat == 'Mage':
                if stat_type == 'realm':
                    return False, "For Mages, Time is a Sphere and cannot be set as a Realm"
                self.category = 'powers'
                self.stat_type = 'sphere'
                # Remove from realm if it exists
                if 'powers' in self.target.db.stats and 'realm' in self.target.db.stats['powers']:
                    if 'Time' in self.target.db.stats['powers']['realm']:
                        del self.target.db.stats['powers']['realm']['Time']
            elif splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain'):
                if stat_type == 'sphere':
                    return False, "For Changelings and Kinain, Time is a Realm and cannot be set as a Sphere"
                self.category = 'powers'
                self.stat_type = 'realm'
                # Remove from sphere if it exists
                if 'powers' in self.target.db.stats and 'sphere' in self.target.db.stats['powers']:
                    if 'Time' in self.target.db.stats['powers']['sphere']:
                        del self.target.db.stats['powers']['sphere']['Time']
            
            try:
                val = int(value)
                if val < 0 or val > 5:
                    return False, "Power values must be between 0 and 5"
                return True, ""
            except ValueError:
                return False, "Power values must be numbers"

        # Handle Nature validation first
        if stat_name in ['Nature', 'Demeanor']:
            splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
            char_type = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
            
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

        # Special handling for gifts
        if category == 'powers' and stat_type == 'gift':
            # Check if character can use gifts
            can_use_gifts = (
                splat == 'Shifter' or 
                splat == 'Possessed' or 
                (splat == 'Mortal+' and char_type == 'Kinfolk')
            )
            
            if not can_use_gifts:
                return False, "Only Shifters, Possessed, and Kinfolk can have gifts"
                
            # Get the gift from the database
            from world.wod20th.models import Stat
            gift = Stat.objects.filter(
                name__iexact=stat_name,
                category='powers',
                stat_type='gift'
            ).first()
            
            if not gift:
                return False, f"'{stat_name}' is not a valid gift"
                
            # For Shifters, check shifter_type
            if splat == 'Shifter' and gift.shifter_type:
                allowed_types = []
                if isinstance(gift.shifter_type, list):
                    allowed_types = [t.lower() for t in gift.shifter_type]
                else:
                    allowed_types = [gift.shifter_type.lower()]
                
                if char_type.lower() not in allowed_types:
                    # Only display the error message once here, not in detect_ability_category
                    return False, f"The gift '{gift.name}' is not available to {char_type}. Available to: {', '.join(t.title() for t in allowed_types)}"
            
            # For Kinfolk, check if they have the Gifted Kinfolk merit
            elif splat == 'Mortal+' and char_type == 'Kinfolk':
                merit_value = self.target.get_stat('merits', 'supernatural', 'Gifted Kinfolk', temp=False)
                if not merit_value:
                    return False, "Kinfolk must have the 'Gifted Kinfolk' Merit to use gifts"
            
            # Validate gift value
            try:
                val = int(value)
                if val < 0 or val > 5:
                    return False, "Gift rating must be between 0 and 5"
            except ValueError:
                return False, "Gift rating must be a number"

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
            splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
            char_type = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
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
            splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
            
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
            splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
            
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
            splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
            shifter_type = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
            
            if splat != 'Shifter':
                return False, "Only Shifters can have Patron Totem"
            
            if shifter_type == 'Bastet':
                return False, "Bastet use Jamak Spirit instead of Patron Totem"
            
            if category != 'identity' or stat_type != 'lineage':
                return False, "Patron Totem must be set using +selfstat Patron Totem/lineage=<totem name>"

        if stat_name.lower() == 'jamak spirit':
            # Get character's splat and type
            splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
            shifter_type = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
            
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
        splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
        if not splat:
            return None
            
        # Get subtype and affiliation if applicable
        subtype = None
        affiliation = None
        
        if splat.lower() == 'shifter':
            subtype = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
        elif splat.lower() == 'mage':
            affiliation = self.target.get_stat('identity', 'lineage', 'Affiliation', temp=False)
        elif splat.lower() == 'changeling':
            subtype = self.target.get_stat('identity', 'lineage', 'Kith', temp=False)
        elif splat.lower() == 'possessed':
            subtype = self.target.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
        elif splat.lower() == 'mortal+':
            subtype = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
            
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
        self.is_specialty = False
        self.specialty = None
        
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

        # Store the original caller for logging purposes
        original_caller = self.caller

        # Temporarily set caller to target for stat operations
        self.caller = self.target

        # Fix any incorrectly stored Necromancy paths
        self._fix_necromancy_paths()

        if not self.stat_name:
            self.caller.msg("|rUsage: +stats <character>/<stat>[(<instance>)]/[<category>]=[+-]<value>|n")
            return

        # Get character's splat type and character type 
        splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
        char_type = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
        
        # Special handling for setting splat
        if self.stat_name.lower() == 'splat':
            if not self.value_change:
                self.caller.msg("You must specify a splat type.")
                return
            
            # Validate splat type (case-insensitive)
            if self.value_change.lower() not in [s.lower() for s in VALID_SPLATS]:
                self.caller.msg(f"|rInvalid splat type. Valid types are: {', '.join(VALID_SPLATS)}|n")
                return

            # Initialize the stats structure based on splat
            self.initialize_stats(self.value_change.title())
            return

        # Special case for gifts: check if it's an alias first
        if splat == 'Shifter':
            # Instead of hardcoding gift aliases, check the database
            from world.wod20th.models import Stat
            
            # First check if this stat name exactly matches a gift
            gift = Stat.objects.filter(
                name__iexact=self.stat_name,
                category='powers',
                stat_type='gift'
            ).first()
            
            if not gift:
                # If not an exact match, check if it's an alias
                gifts_with_aliases = Stat.objects.filter(
                    category='powers',
                    stat_type='gift'
                ).exclude(gift_alias__isnull=True)
                
                for g in gifts_with_aliases:
                    if g.gift_alias and any(alias.lower() == self.stat_name.lower() for alias in g.gift_alias):
                        # Set the category and type for gift validation
                        if not self.category or not self.stat_type:
                            self.category = 'powers'
                            self.stat_type = 'gift'
                            
                        # Store the original name for later reference
                        original_name = self.stat_name
                        # Update to canonical name
                        self.stat_name = g.name
                        self.alias_used = original_name  # This is correctly storing the original alias
                        # Notify about the alias
                        original_caller.msg(f"|y'{original_name}' is an alias for the gift '{g.name}'.|n")
                        break

        # Check background restrictions before any stat setting
        if (self.category == 'backgrounds' and self.stat_type == 'background') or \
            (self.stat_name.lower() in [bg.lower() for bg in (UNIVERSAL_BACKGROUNDS + 
                                                           VAMPIRE_BACKGROUNDS + 
                                                           CHANGELING_BACKGROUNDS + 
                                                           MAGE_BACKGROUNDS + 
                                                           TECHNOCRACY_BACKGROUNDS + 
                                                           TRADITIONS_BACKGROUNDS + 
                                                           NEPHANDI_BACKGROUNDS + 
                                                           SHIFTER_BACKGROUNDS + 
                                                           SORCERER_BACKGROUNDS)]):
             # Check splat-specific background restrictions
             if self.stat_name.title() in VAMPIRE_BACKGROUNDS and splat != 'Vampire':
                 self.caller.msg(f"|rThe background '{self.stat_name}' is only available to Vampire characters.|n")
                 return
             elif self.stat_name.title() in CHANGELING_BACKGROUNDS and splat != 'Changeling':
                 self.caller.msg(f"|rThe background '{self.stat_name}' is only available to Changeling characters.|n")
                 return
             elif self.stat_name.title() in SHIFTER_BACKGROUNDS and splat != 'Shifter':
                 self.caller.msg(f"|rThe background '{self.stat_name}' is only available to Shifter characters.|n")
                 return
             elif self.stat_name.title() in SORCERER_BACKGROUNDS and splat != 'Mortal+':
                 self.caller.msg(f"|rThe background '{self.stat_name}' is only available to Mortal+ characters.|n")
                 return
             elif self.stat_name.title() in (MAGE_BACKGROUNDS + TECHNOCRACY_BACKGROUNDS + TRADITIONS_BACKGROUNDS + NEPHANDI_BACKGROUNDS) and splat != 'Mage' and splat != 'Companion':
                 self.caller.msg(f"|rThe background '{self.stat_name}' is only available to Mage or Companion characters.|n")
                 return
             elif self.stat_name.title() in KINAIN_BACKGROUNDS:
                 if splat != 'Mortal+' or char_type != 'Kinain':
                     self.caller.msg(f"|rThe background '{self.stat_name}' is only available to Kinain characters.|n")
                     return

        # If no category/type specified, try to determine it from the stat name
        if not self.category or not self.stat_type:
            # Check if this might be a gift alias for shifters
            if splat == 'Shifter':
                is_alias, canonical_name = self._check_gift_alias(self.stat_name)
                if is_alias:
                    # Found it as a gift alias, set category and type
                    self.stat_name = canonical_name
                    self.category = 'powers'
                    self.stat_type = 'gift'
                    
            # If still no category, try identity stats
            if not self.category or not self.stat_type:
                self.category, self.stat_type = self._detect_identity_category(self.stat_name)
                
                # If not an identity stat, try abilities and other categories
                if not self.category or not self.stat_type:
                    self.category, self.stat_type = self.detect_ability_category(self.stat_name)

        # Special case for gifts: check for aliases
        if self.category == 'powers' and self.stat_type == 'gift' and splat == 'Shifter':
            is_alias, canonical_name = self._check_gift_alias(self.stat_name)
            if is_alias:
                self.stat_name = canonical_name
        
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

        # Special handling for Generation
        if self.stat_name.lower() == 'generation':
            if splat != 'Vampire':
                self.caller.msg("|rOnly Vampire characters can have Generation.|n")
                return
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

        # Special handling for Affinity Realm
        if self.stat_name.lower() == 'affinity realm':
            self.stat_name = 'Affinity Realm'  # Ensure proper capitalization
            self.category = 'identity'
            self.stat_type = 'lineage'

        # When setting type for the first time or resetting stats
        if self.stat_name.lower() in ['type', 'possessed type', 'mortal+ type']:
            # First check if this is a Mortal+ type
            if splat and splat.lower() == 'mortal+':
                # Get valid Mortal+ types
                valid_types = [t[1] for t in MORTALPLUS_TYPE_CHOICES if t[1] != 'None']
                mortalplus_type = next((t for t in valid_types if t.lower() == self.value_change.lower()), None)
                if not mortalplus_type:
                    self.caller.msg(f"|rInvalid Mortal+ type. Valid types are: {', '.join(sorted(valid_types))}|n")
                    self.caller = original_caller  # Restore original caller
                    return
                # Initialize mortal+-specific stats for the chosen type
                initialize_mortalplus_stats(self.target, mortalplus_type)
                self.caller.msg(f"|gSet {self.target.name}'s Mortal+ type to {mortalplus_type} and initialized appropriate stats.|n")
                self.caller = original_caller  # Restore original caller
                return
            elif splat and splat.lower() == 'possessed':
                # Convert tuple list to just the type names for validation
                valid_types = [t[0] for t in POSSESSED_TYPE_CHOICES if t[0] != 'None']
                if self.value_change.title() not in valid_types:
                    self.caller.msg(f"|rInvalid Possessed type. Valid types are: {', '.join(valid_types)}|n")
                    self.caller = original_caller  # Restore original caller
                    return
                # Set the type in identity/lineage
                self.target.set_stat('identity', 'lineage', 'Possessed Type', self.value_change.title(), temp=False)
                self.target.set_stat('identity', 'lineage', 'Possessed Type', self.value_change.title(), temp=True)
                # Initialize possessed-specific stats for the chosen type
                initialize_possessed_stats(self.target, self.value_change.title())
                self.caller.msg(f"|gSet {self.target.name}'s Possessed type to {self.value_change.title()} and initialized appropriate stats.|n")
                self.caller = original_caller  # Restore original caller
                return
            elif splat and splat.lower() == 'shifter':
                # Convert tuple list to just the type names for validation
                valid_types = [t[1] for t in SHIFTER_TYPE_CHOICES if t[1] != 'None']
                if self.value_change.title() not in valid_types:
                    self.caller.msg(f"|rInvalid shifter type. Valid types are: {', '.join(valid_types)}|n")
                    self.caller = original_caller  # Restore original caller
                    return
                # Set the type in identity/lineage
                self.target.set_stat('identity', 'lineage', 'Type', self.value_change.title(), temp=False)
                self.target.set_stat('identity', 'lineage', 'Type', self.value_change.title(), temp=True)
                # Initialize shifter-specific stats for the chosen type
                initialize_shifter_type(self.target, self.value_change.title())
                self.caller.msg(f"|gSet {self.target.name}'s shifter type to {self.value_change.title()} and initialized appropriate stats.|n")
                self.caller = original_caller  # Restore original caller
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
            # For gifts, we need to ensure category and stat_type are set properly
            if self.stat_name.lower() in ['scent of the true form', 'sight of the true form'] and splat == 'Shifter':
                # Explicitly set these for proper gift validation
                self.category = 'powers'
                self.stat_type = 'gift'
                
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

        # Restore original caller
        self.caller = original_caller

    def initialize_stats(self, splat):
        """Initialize the basic stats structure based on splat type."""
        # Store original caller
        original_caller = self.caller
        
        # Set caller to target temporarily
        self.caller = self.target
        
        # Clear gift_aliases when changing splat
        if hasattr(self.caller.db, 'gift_aliases'):
            self.caller.db.gift_aliases = {}
            
        # Initialize basic stats structure
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

        # Initialize base structure according to STAT_TYPE_TO_CATEGORY
        base_stats = {}
        
        # Initialize attributes with categories
        base_stats['attributes'] = {
            'physical': {},
            'social': {},
            'mental': {}
        }
        
        # Initialize abilities with categories
        base_stats['abilities'] = {
            'skill': {},
            'knowledge': {},
            'talent': {},
            'secondary_abilities': {
                'secondary_knowledge': {},
                'secondary_talent': {},
                'secondary_skill': {}
            }
        }
        
        # Initialize identity categories
        base_stats['identity'] = {
            'personal': {},
            'lineage': {},
            'identity': {}
        }
        
        # Initialize powers categories
        base_stats['powers'] = {}
        for power_type in POWER_CATEGORIES:
            base_stats['powers'][power_type] = {}
        
        # Initialize merits and flaws with their categories
        base_stats['merits'] = {
            'physical': {},
            'social': {},
            'mental': {},
            'supernatural': {}
        }
        base_stats['flaws'] = {
            'physical': {},
            'social': {},
            'mental': {},
            'supernatural': {}
        }
        
        # Initialize virtues
        base_stats['virtues'] = {
            'moral': {},
            'advantage': {},
        }
        
        # Initialize backgrounds
        base_stats['backgrounds'] = {
            'background': {}
        }
        
        # Initialize advantages
        base_stats['advantages'] = {
            'renown': {}
        }
        
        # Initialize pools with their types
        base_stats['pools'] = {
            'dual': {},
            'moral': {},
            'advantage': {},
            'resonance': {}
        }

        # Set the splat using the title case version for display
        base_stats['other'] = {'splat': {'Splat': {'perm': splat_title, 'temp': splat_title}}}

        # Initialize the character's stats
        self.caller.db.stats = base_stats

        # Initialize splat-specific stats using lowercase for comparison
        if splat_lower == 'vampire':
            initialize_vampire_stats(self.caller, '')
            # Set default Banality for Vampires
            self.caller.db.stats['pools']['dual']['Banality'] = {'perm': 5, 'temp': 5}
        elif splat_lower == 'mage':
            initialize_mage_stats(self.caller, '')
            affiliation = self.caller.get_stat('identity', 'lineage', 'Affiliation', temp=False)
            allowed_backgrounds = set(bg.title() for bg in MAGE_BACKGROUNDS)
            if affiliation == 'Technocracy':
                allowed_backgrounds.update(bg.title() for bg in TECHNOCRACY_BACKGROUNDS)
        elif splat_lower == 'shifter':
            initialize_shifter_type(self.caller, '')
        elif splat_lower == 'changeling':
            initialize_changeling_stats(self.caller, '')
        elif splat_lower == 'mortal+':
            initialize_mortalplus_stats(self.caller, '')
        elif splat_lower == 'possessed':
            # Initialize power categories
            for category in ['blessing', 'charm', 'gift']:
                if category not in self.caller.db.stats['powers']:
                    self.caller.db.stats['powers'][category] = {}
        elif splat_lower == 'companion':
            initialize_companion_stats(self.caller, '')

        # Set base attributes to 1
        for category, attributes in ATTRIBUTE_CATEGORIES.items():
            for attribute in attributes:
                self.caller.set_stat('attributes', category, attribute, 1, temp=False)
                self.caller.set_stat('attributes', category, attribute, 1, temp=True)

        # Restore original caller
        self.caller = original_caller
        
        # Notify both staff and target
        self.caller.msg(f"|g{original_caller.name} initialized your character sheet as {splat_title}.|n")
        original_caller.msg(f"|gInitialized {splat_title} character sheet for {self.target.name}.|n")

    def validate_archetype(self, archetype_name):
        """Validate that an archetype exists and is valid."""
        archetype_name = archetype_name.lower()
        if archetype_name not in ARCHETYPES:
            valid_archetypes = ', '.join(sorted([a['name'] for a in ARCHETYPES.values()]))
            return False, f"Invalid archetype. Valid archetypes are: {valid_archetypes}"
        return True, ""

    def _fix_necromancy_paths(self):
        """Fix incorrectly stored Necromancy paths by moving them to powers.necromancy."""
        if 'necromancy' in self.caller.db.stats and 'necromancy' in self.caller.db.stats['necromancy']:
            # Initialize powers.necromancy if it doesn't exist
            if 'powers' not in self.caller.db.stats:
                self.caller.db.stats['powers'] = {}
            if 'necromancy' not in self.caller.db.stats['powers']:
                self.caller.db.stats['powers']['necromancy'] = {}
            
            # Move each Necromancy path to powers.necromancy
            for path, values in self.caller.db.stats['necromancy']['necromancy'].items():
                self.caller.db.stats['powers']['necromancy'][path] = values
            
            # Delete the old necromancy category
            del self.caller.db.stats['necromancy']
            self.caller.msg("|gFixed Necromancy paths storage location.|n")

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
            
        # Special handling for secondary abilities
        if category == 'abilities' and stat_type.startswith('secondary_'):
            if 'secondary_abilities' not in self.caller.db.stats['abilities']:
                self.caller.db.stats['abilities']['secondary_abilities'] = {}
            if stat_type not in self.caller.db.stats['abilities']['secondary_abilities']:
                self.caller.db.stats['abilities']['secondary_abilities'][stat_type] = {}
        else:
            # Regular stat initialization
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
            from world.wod20th.utils.vampire_utils import update_vampire_pools_on_stat_change
            update_vampire_pools_on_stat_change(self.caller, stat_name, value)

        elif splat == 'Mage':
            from world.wod20th.utils.mage_utils import update_mage_pools_on_stat_change
            update_mage_pools_on_stat_change(self.caller, stat_name, value)

        elif splat == 'Shifter':
            from world.wod20th.utils.shifter_utils import update_shifter_pools_on_stat_change
            update_shifter_pools_on_stat_change(self.caller, stat_name, value)

        elif splat == 'Changeling':
            from world.wod20th.utils.changeling_utils import update_changeling_pools_on_stat_change
            update_changeling_pools_on_stat_change(self.caller, stat_name, value)

        elif splat == 'Companion':
            from world.wod20th.utils.companion_utils import update_companion_pools_on_stat_change
            update_companion_pools_on_stat_change(self.caller, stat_name, value)

        elif splat == 'Possessed':
            from world.wod20th.utils.possessed_utils import update_possessed_pools_on_stat_change
            update_possessed_pools_on_stat_change(self.caller, stat_name, value)

        elif splat == 'Mortal+':
            from world.wod20th.utils.mortalplus_utils import update_mortalplus_pools_on_stat_change
            update_mortalplus_pools_on_stat_change(self.caller, stat_name, value)

        # Update willpower for all splats if virtues change
        if stat_name.lower() in ['conscience', 'self-control', 'courage', 'conviction', 'instinct']:
            from world.wod20th.utils.virtue_utils import calculate_willpower, calculate_path
            
            # Calculate new willpower
            new_willpower = calculate_willpower(self.caller)
            if new_willpower is not None:
                self.caller.set_stat('pools', 'dual', 'Willpower', new_willpower, temp=False)
                self.caller.set_stat('pools', 'dual', 'Willpower', new_willpower, temp=True)
                self.caller.msg(f"|gWillpower recalculated to {new_willpower}.|n")
            
            # For vampires, also update path rating
            if splat == 'Vampire':
                new_path = calculate_path(self.caller)
                if new_path is not None:
                    self.caller.set_stat('pools', 'moral', 'Path', new_path, temp=False)
                    self.caller.set_stat('pools', 'moral', 'Path', new_path, temp=True)
                    self.caller.msg(f"|gPath rating recalculated to {new_path}.|n")

    def _requires_instance(self, stat_name: str, category: str = None) -> bool:
        """
        Check if a stat MUST have an instance.
        
        Args:
            stat_name (str): The name of the stat to check
            category (str, optional): The category of the stat
            
        Returns:
            bool: True if the stat requires an instance, False otherwise
        """
        # Stats in REQUIRED_INSTANCES must have instances
        if stat_name in REQUIRED_INSTANCES:
            return True
            
        # Check database for required instance flag
        from world.wod20th.models import Stat
        stat = Stat.objects.filter(name__iexact=stat_name).first()
        
        if stat and stat.instanced:
            return True
            
        return False
        
    def _should_support_instance(self, stat_name: str, category: str = None) -> bool:
        """
        Check if a stat CAN have an instance.
        
        Args:
            stat_name (str): The name of the stat to check
            category (str, optional): The category of the stat
            
        Returns:
            bool: True if the stat can have an instance, False otherwise
        """
        # If it requires an instance, it can have one
        if self._requires_instance(stat_name, category):
            return True
            
        return False

    def _display_instance_requirement_message(self, stat_name: str) -> None:
        """Display message indicating an instance is required for a stat."""
        from world.wod20th.models import Stat
        stat = Stat.objects.filter(name__iexact=stat_name).first()
        
        # Get the category and type if available
        category = stat.category if stat else self.category
        stat_type = stat.stat_type if stat else self.stat_type
        
        # Provide more specific guidance based on the stat type
        if category == 'merits':
            self.caller.msg(f"|rThe merit '{stat_name}' requires an instance. Use format: {stat_name}(instance)/{stat_type}=value|n")
            self.caller.msg(f"|yFor example: {stat_name}(Sabbat)/{stat_type}=3|n")
            self.caller.msg(f"|yThe category is '{category}' and the stat type is one of: 'physical', 'social', 'mental', or 'supernatural'.|n")
        elif category == 'flaws':
            self.caller.msg(f"|rThe flaw '{stat_name}' requires an instance. Use format: {stat_name}(instance)/{stat_type}=value|n")
            self.caller.msg(f"|yFor example: {stat_name}(Sabbat)/{stat_type}=3|n")
            self.caller.msg(f"|yThe category is '{category}' and the stat type is one of: 'physical', 'social', 'mental', or 'supernatural'.|n")
        elif category == 'backgrounds':
            self.caller.msg(f"|rThe background '{stat_name}' requires an instance. Use format: {stat_name}(instance)/background=value|n")
            self.caller.msg(f"|yFor example: {stat_name}(Camarilla)/background=3|n")
        else:
            self.caller.msg(f"|rThe stat '{stat_name}' requires an instance. Use format: {stat_name}(instance)=value|n")
            self.caller.msg(f"|yFor example: {stat_name}(Specific)/category=value|n")
        
        # Add usage information
        self.caller.msg(f"|yUsage: +stats <character>/<stat>[(<instance>)]/[<category>]=[+-]<value>|n")

    def set_stat(self, stat_name: str, value: str, category: str = None, stat_type: str = None) -> None:
        """
        Set a stat to a specific value, handling incrementing/decrementing.
        
        Args:
            stat_name: The name of the stat to set
            value: The value to set it to (can include +/- for increments)
            category: Optional category override
            stat_type: Optional stat type override
        """
        # Store original caller for notifications
        original_caller = self.caller
        
        # Define full_stat_name based on instance (we'll update this if needed)
        full_stat_name = f"{stat_name}({self.instance})" if hasattr(self, 'instance') and self.instance else stat_name

        try:
            # Get character's splat and type
            splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
            char_type = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
            
            # Make sure the value is legal
            if not value:
                self.caller.msg("|rYou must specify a value.|n")
                return
            
            # If this is a stat with an instance, combine them for storage
            if hasattr(self, 'instance') and self.instance and self._should_support_instance(stat_name, category):
                full_stat_name = f"{stat_name}({self.instance})"
            else:
                full_stat_name = stat_name
            
            # Handle increment/decrement
            if isinstance(value, str) and (value.startswith('+') or value.startswith('-')):
                # Get current value
                current_value = self.target.get_stat(category, stat_type, stat_name, temp=False)
                if current_value is None:
                    current_value = 0
                try:
                    # Parse the increment (e.g., +2, -1)
                    increment = int(value)
                    value = str(current_value + increment)
                except ValueError:
                    self.caller.msg(f"|rInvalid increment value: {value}|n")
                    return
            elif not isinstance(value, str):
                # Convert value to string if it's not already
                value = str(value)
            
            # Special handling for virtues
            if stat_name.title() in ['Conscience', 'Self-Control', 'Courage', 'Conviction', 'Instinct']:
                try:
                    virtue_value = int(value)
                    if virtue_value < 1 or virtue_value > 5:
                        self.caller.msg(f"|r{stat_name} must be between 1 and 5.|n")
                        return

                    # Initialize virtues structure if needed
                    if 'virtues' not in self.target.db.stats:
                        self.target.db.stats['virtues'] = {'moral': {}}
                    if 'moral' not in self.target.db.stats['virtues']:
                        self.target.db.stats['virtues']['moral'] = {}

                    # Store the virtue value
                    self.target.db.stats['virtues']['moral'][stat_name.title()] = {
                        'perm': virtue_value,
                        'temp': virtue_value
                    }

                    # Update Path rating for vampires when virtues change
                    if stat_name.title() in ['Conscience', 'Self-Control', 'Conviction', 'Instinct'] and splat == 'Vampire':
                        path_rating = calculate_path(self.target)
                        if 'pools' not in self.target.db.stats:
                            self.target.db.stats['pools'] = {'moral': {}}
                        if 'moral' not in self.target.db.stats['pools']:
                            self.target.db.stats['pools']['moral'] = {}
                        self.target.db.stats['pools']['moral']['Path'] = {
                            'perm': path_rating,
                            'temp': path_rating
                        }
                        # Notify both staff and target
                        self.caller.msg(f"|gCalculated new Path rating for {self.target.name}: {path_rating}|n")
                        if self.target != self.caller:
                            self.target.msg(f"|g{self.caller.name} calculated your new Path rating: {path_rating}|n")

                    # Update Willpower when Courage changes
                    if stat_name.title() == 'Courage':
                        if splat and splat.lower() in ['vampire', 'mortal', 'mortal+']:
                            if 'pools' not in self.target.db.stats:
                                self.target.db.stats['pools'] = {'dual': {}}
                            if 'dual' not in self.target.db.stats['pools']:
                                self.target.db.stats['pools']['dual'] = {}
                            self.target.db.stats['pools']['dual']['Willpower'] = {
                                'perm': virtue_value,
                                'temp': virtue_value
                            }
                            # Notify both staff and target
                            self.caller.msg(f"|gWillpower set to match Courage for {self.target.name}: {virtue_value}|n")
                            if self.target != self.caller:
                                self.target.msg(f"|g{self.caller.name} set your Willpower to match Courage: {virtue_value}|n")

                    # Notify both staff and target
                    self.caller.msg(f"|gSet {stat_name} to {virtue_value} for {self.target.name}.|n")
                    # Add standard update message
                    original_caller.msg(f"|gUpdated {self.target.name}'s {stat_name} to {virtue_value}.|n")
                    if self.target != self.caller:
                        self.target.msg(f"|g{self.caller.name} set your {stat_name} to {virtue_value}.|n")
                    return
                except ValueError:
                    self.caller.msg("|rVirtue value must be a number.|n")
                    return
            
            # Check background restrictions
            if category == 'backgrounds' and stat_type == 'background':
                # Check splat-specific background restrictions
                if stat_name.title() in VAMPIRE_BACKGROUNDS and splat != 'Vampire':
                    self.caller.msg(f"|rThe background '{stat_name}' is only available to Vampire characters.|n")
                    # Remove the background if it exists
                    if 'backgrounds' in self.target.db.stats and 'background' in self.target.db.stats['backgrounds']:
                        if stat_name.title() in self.target.db.stats['backgrounds']['background']:
                            del self.target.db.stats['backgrounds']['background'][stat_name.title()]
                    return
                elif stat_name.title() in CHANGELING_BACKGROUNDS and splat != 'Changeling':
                    self.caller.msg(f"|rThe background '{stat_name}' is only available to Changeling characters.|n")
                    # Remove the background if it exists
                    if 'backgrounds' in self.target.db.stats and 'background' in self.target.db.stats['backgrounds']:
                        if stat_name.title() in self.target.db.stats['backgrounds']['background']:
                            del self.target.db.stats['backgrounds']['background'][stat_name.title()]
                    return
                elif stat_name.title() in SHIFTER_BACKGROUNDS and splat != 'Shifter':
                    self.caller.msg(f"|rThe background '{stat_name}' is only available to Shifter characters.|n")
                    # Remove the background if it exists
                    if 'backgrounds' in self.target.db.stats and 'background' in self.target.db.stats['backgrounds']:
                        if stat_name.title() in self.target.db.stats['backgrounds']['background']:
                            del self.target.db.stats['backgrounds']['background'][stat_name.title()]
                    return
                elif stat_name.title() in SORCERER_BACKGROUNDS and splat != 'Mortal+':
                    self.caller.msg(f"|rThe background '{stat_name}' is only available to Mortal+ characters.|n")
                    # Remove the background if it exists
                    if 'backgrounds' in self.target.db.stats and 'background' in self.target.db.stats['backgrounds']:
                        if stat_name.title() in self.target.db.stats['backgrounds']['background']:
                            del self.target.db.stats['backgrounds']['background'][stat_name.title()]
                    return
                elif stat_name.title() in (MAGE_BACKGROUNDS + TECHNOCRACY_BACKGROUNDS + TRADITIONS_BACKGROUNDS + NEPHANDI_BACKGROUNDS) and splat != 'Mage':
                    self.caller.msg(f"|rThe background '{stat_name}' is only available to Mage characters.|n")
                    # Remove the background if it exists
                    if 'backgrounds' in self.target.db.stats and 'background' in self.target.db.stats['backgrounds']:
                        if stat_name.title() in self.target.db.stats['backgrounds']['background']:
                            del self.target.db.stats['backgrounds']['background'][stat_name.title()]
                    return
                elif stat_name.title() in KINAIN_BACKGROUNDS:
                    if splat != 'Mortal+' or char_type != 'Kinain':
                        self.caller.msg(f"|rThe background '{stat_name}' is only available to Kinain characters.|n")
                        # Remove the background if it exists
                        if 'backgrounds' in self.target.db.stats and 'background' in self.target.db.stats['backgrounds']:
                            if stat_name.title() in self.target.db.stats['backgrounds']['background']:
                                del self.target.db.stats['backgrounds']['background'][stat_name.title()]
                        return
            
            # Special handling for gifts to store the alias used
            if category == 'powers' and stat_type == 'gift' and hasattr(self, 'alias_used'):
                # Initialize powers.gift if needed
                if 'powers' not in self.target.db.stats:
                    self.target.db.stats['powers'] = {}
                if 'gift' not in self.target.db.stats['powers']:
                    self.target.db.stats['powers']['gift'] = {}
                
                # Store the gift with its value
                try:
                    gift_value = int(value)
                    self.target.db.stats['powers']['gift'][stat_name] = {
                        'perm': gift_value,
                        'temp': gift_value
                    }
                    
                    # Store the alias using the new method
                    self.target.set_gift_alias(stat_name, self.alias_used, gift_value)
                    
                    # Send message to staff (original caller)
                    original_caller.msg(f"|gSet gift {stat_name} to {gift_value} for {self.target.name}.|n")
                    # Send message to target mentioning the staff member's name
                    self.target.msg(f"|g{original_caller.name} set your gift {stat_name} to {gift_value}.|n")
                except ValueError:
                    self.caller.msg("|rGift value must be a number.|n")
                    
                return
                        
            # Regular gift (no alias)
            if category == 'powers' and stat_type == 'gift' and not hasattr(self, 'alias_used'):
                # Initialize powers.gift if needed
                if 'powers' not in self.target.db.stats:
                    self.target.db.stats['powers'] = {}
                if 'gift' not in self.target.db.stats['powers']:
                    self.target.db.stats['powers']['gift'] = {}
                
                # Store the gift with its value
                try:
                    gift_value = int(value)
                    self.target.db.stats['powers']['gift'][stat_name] = {
                        'perm': gift_value,
                        'temp': gift_value
                    }
                    
                    # Store the canonical name as its own alias in the gift_aliases attribute
                    self.target.set_gift_alias(stat_name, stat_name, gift_value)
                    
                    # Notify both staff and target
                    original_caller.msg(f"|gSet gift {stat_name} to {gift_value} for {self.target.name}.|n")
                    # Add standard update message
                    original_caller.msg(f"|gUpdated {self.target.name}'s gift '{stat_name}' to {gift_value}.|n")
                    # Message to target
                    self.target.msg(f"|g{original_caller.name} set your gift {stat_name} to {gift_value}.|n")
                except ValueError:
                    self.caller.msg("|rGift value must be a number.|n")
                return
            
            # Set the main stat values, then handle special cases
            self.target.set_stat(category, stat_type, stat_name, value, temp=False)
            self.target.set_stat(category, stat_type, stat_name, value, temp=True)
            
            # If this was a gift alias and we've already handled the database storage, make sure the gift_aliases attribute is set correctly
            if category == 'powers' and stat_type == 'gift' and hasattr(self, 'alias_used') and self.alias_used:
                # Initialize gift_aliases attribute if it doesn't exist
                if not self.target.attributes.has('gift_aliases'):
                    self.target.db.gift_aliases = {}
                    
                # Store the alias mapping
                self.target.db.gift_aliases[stat_name] = {
                    'alias': self.alias_used,
                    'value': value
                }
            
            # Update pools based on splat type
            if splat == 'Shifter':
                from world.wod20th.utils.shifter_utils import update_shifter_pools_on_stat_change
                update_shifter_pools_on_stat_change(self.target, stat_name, value)
            elif splat == 'Changeling':
                from world.wod20th.utils.changeling_utils import update_changeling_pools_on_stat_change
                update_changeling_pools_on_stat_change(self.target, stat_name, value)
            elif splat == 'Companion':
                from world.wod20th.utils.companion_utils import update_companion_pools_on_stat_change
                update_companion_pools_on_stat_change(self.target, stat_name, value)
            elif splat == 'Possessed':
                from world.wod20th.utils.possessed_utils import update_possessed_pools_on_stat_change
                update_possessed_pools_on_stat_change(self.target, stat_name, value)
            elif splat == 'Mortal+':
                from world.wod20th.utils.mortalplus_utils import update_mortalplus_pools_on_stat_change
                update_mortalplus_pools_on_stat_change(self.target, stat_name, value)
            
            # Special handling for merits
            if stat_name.title() in MERIT_VALUES:
                # Skip merit validation if we've already determined this is a blessing for Possessed
                if not (splat == 'Possessed' and category == 'powers' and stat_type == 'blessing'):
                    try:
                        merit_value = int(value)
                        valid_values = MERIT_VALUES[stat_name.title()]
                        if merit_value not in valid_values:
                            self.caller.msg(f"|rInvalid value for merit {stat_name}. Valid values are: {', '.join(map(str, valid_values))}|n")
                            return

                        # Find the merit type first
                        merit_type = None
                        for m_type, merits in MERIT_CATEGORIES.items():
                            if stat_name.title() in merits:
                                merit_type = m_type
                                break
                        
                        if not merit_type:
                            self.caller.msg(f"|rCould not determine type for merit {stat_name}.|n")
                            return

                        # Check splat restrictions
                        if stat_name.title() in MERIT_SPLAT_RESTRICTIONS:
                            restriction = MERIT_SPLAT_RESTRICTIONS[stat_name.title()]
                            if restriction['splat']:
                                allowed_splats = restriction['splat'] if isinstance(restriction['splat'], list) else [restriction['splat']]
                                if splat not in allowed_splats:
                                    self.caller.msg(f"|rThe merit '{stat_name}' is only available to {', '.join(allowed_splats)} characters.|n")
                                    # Remove the merit if it exists
                                    if 'merits' in self.target.db.stats and merit_type in self.target.db.stats['merits']:
                                        if stat_name.title() in self.target.db.stats['merits'][merit_type]:
                                            del self.target.db.stats['merits'][merit_type][stat_name.title()]
                                    return
                            if restriction['splat_type'] and restriction['splat_type'] != char_type:
                                self.caller.msg(f"|rThe merit '{stat_name}' is only available to {restriction['splat_type']} characters.|n")
                                # Remove the merit if it exists
                                if 'merits' in self.target.db.stats and merit_type in self.target.db.stats['merits']:
                                    if stat_name.title() in self.target.db.stats['merits'][merit_type]:
                                        del self.target.db.stats['merits'][merit_type][stat_name.title()]
                                return

                        # Store the merit
                        if 'merits' not in self.target.db.stats:
                            self.target.db.stats['merits'] = {}
                        if merit_type not in self.target.db.stats['merits']:
                            self.target.db.stats['merits'][merit_type] = {}
                        self.target.db.stats['merits'][merit_type][stat_name.title()] = {
                            'perm': merit_value,
                            'temp': merit_value
                        }
                        
                        # Notify both staff and target
                        self.caller.msg(f"|gSet merit {stat_name} to {merit_value} for {self.target.name}.|n")
                        # Add standard update message
                        original_caller.msg(f"|gUpdated {self.target.name}'s merit '{stat_name}' to {merit_value}.|n")
                        if self.target != self.caller:
                            self.target.msg(f"|g{self.caller.name} set your merit {stat_name} to {merit_value}.|n")
                        return
                    except ValueError:
                        self.caller.msg(f"|rMerit value must be a number.|n")
                        return

            # Special handling for flaws
            if stat_name.title() in FLAW_VALUES:
                try:
                    flaw_value = int(value)
                    valid_values = FLAW_VALUES[stat_name.title()]
                    if flaw_value not in valid_values:
                        self.caller.msg(f"|rInvalid value for flaw {stat_name}. Valid values are: {', '.join(map(str, valid_values))}|n")
                        return

                    # Find the flaw type first
                    flaw_type = None
                    for f_type, flaws in FLAW_CATEGORIES.items():
                        if stat_name.title() in flaws:
                            flaw_type = f_type
                            break
                    
                    if not flaw_type:
                        self.caller.msg(f"|rCould not determine type for flaw {stat_name}.|n")
                        return

                    # Check splat restrictions
                    if stat_name.title() in FLAW_SPLAT_RESTRICTIONS:
                        restriction = FLAW_SPLAT_RESTRICTIONS[stat_name.title()]
                        if restriction['splat']:
                            allowed_splats = restriction['splat'] if isinstance(restriction['splat'], list) else [restriction['splat']]
                            if splat not in allowed_splats:
                                self.caller.msg(f"|rThe flaw '{stat_name}' is only available to {', '.join(allowed_splats)} characters.|n")
                                # Remove the flaw if it exists
                                if 'flaws' in self.target.db.stats and flaw_type in self.target.db.stats['flaws']:
                                    if stat_name.title() in self.target.db.stats['flaws'][flaw_type]:
                                        del self.target.db.stats['flaws'][flaw_type][stat_name.title()]
                                return
                        if restriction['splat_type'] and restriction['splat_type'] != char_type:
                            self.caller.msg(f"|rThe flaw '{stat_name}' is only available to {restriction['splat_type']} characters.|n")
                            # Remove the flaw if it exists
                            if 'flaws' in self.target.db.stats and flaw_type in self.target.db.stats['flaws']:
                                if stat_name.title() in self.target.db.stats['flaws'][flaw_type]:
                                    del self.target.db.stats['flaws'][flaw_type][stat_name.title()]
                            return

                    # Store the flaw
                    if 'flaws' not in self.target.db.stats:
                        self.target.db.stats['flaws'] = {}
                    if flaw_type not in self.target.db.stats['flaws']:
                        self.target.db.stats['flaws'][flaw_type] = {}
                    self.target.db.stats['flaws'][flaw_type][stat_name.title()] = {
                        'perm': flaw_value,
                        'temp': flaw_value
                    }
                    
                    # Notify both staff and target
                    self.caller.msg(f"|gSet flaw {stat_name} to {flaw_value} for {self.target.name}.|n")
                    # Add standard update message
                    original_caller.msg(f"|gUpdated {self.target.name}'s flaw '{stat_name}' to {flaw_value}.|n")
                    if self.target != self.caller:
                        self.target.msg(f"|g{self.caller.name} set your flaw {stat_name} to {flaw_value}.|n")
                    return
                except ValueError:
                    self.caller.msg(f"|rFlaw value must be a number.|n")
                    return
            
            # Special handling for identity stats
            if category == 'identity':
                if 'identity' not in self.target.db.stats:
                    self.target.db.stats['identity'] = {}
                if stat_type not in self.target.db.stats['identity']:
                    self.target.db.stats['identity'][stat_type] = {}
                self.target.db.stats['identity'][stat_type][stat_name] = {
                    'perm': value,
                    'temp': value
                }
                
                # Notify both staff and target
                self.caller.msg(f"|gSet {stat_name} to {value} for {self.target.name}.|n")
                # Add standard update message
                original_caller.msg(f"|gUpdated {self.target.name}'s {stat_name} to {value}.|n")
                if self.target != self.caller:
                    self.target.msg(f"|g{self.caller.name} set your {stat_name} to {value}.|n")
                return

            # Special handling for pools
            if category == 'pools':
                if 'pools' not in self.target.db.stats:
                    self.target.db.stats['pools'] = {}
                if stat_type not in self.target.db.stats['pools']:
                    self.target.db.stats['pools'][stat_type] = {}
                try:
                    pool_value = int(value)
                    self.target.db.stats['pools'][stat_type][stat_name] = {
                        'perm': pool_value,
                        'temp': pool_value
                    }
                    
                    # Notify both staff and target
                    self.caller.msg(f"|gSet {stat_name} pool to {pool_value} for {self.target.name}.|n")
                    # Add standard update message
                    original_caller.msg(f"|gUpdated {self.target.name}'s {stat_name} pool to {pool_value}.|n")
                    if self.target != self.caller:
                        self.target.msg(f"|g{self.caller.name} set your {stat_name} pool to {pool_value}.|n")
                    return
                except ValueError:
                    self.caller.msg(f"|r{stat_name} pool value must be a number.|n")
                    return
            
            # Default message for regular stats
            self.caller.msg(f"|gSet {stat_name} to {value} for {self.target.name}.|n")
            # Add standard update message
            original_caller.msg(f"|gUpdated {self.target.name}'s {category}.{stat_type}.{stat_name} to {value}.|n")
            if self.target != self.caller:
                self.target.msg(f"|g{self.caller.name} set your {stat_name} to {value}.|n")
            
        except Exception as e:
            self.caller.msg(f"|rError processing stat value: {str(e)}|n")
            # Reset caller to original
            self.caller = original_caller
            return

        # Set the stat in the character's stats dict
        self.caller.set_stat(self.category, self.stat_type, self.stat_name, value, temp=False)
        self.caller.set_stat(self.category, self.stat_type, self.stat_name, value, temp=True)
        
        # If this was a gift alias, save it in the character's gift_aliases attribute
        if self.category == 'powers' and self.stat_type == 'gift' and hasattr(self, 'alias_used') and self.alias_used:
            # Store the alias using the set_gift_alias method
            self.target.set_gift_alias(self.stat_name, self.alias_used, value)
            
            # Make sure the message shows both original and canonical names
            original_caller.msg(f"|gSet gift {self.stat_name} to {value}.|n")
            # Add standard update message
            original_caller.msg(f"|gUpdated {self.target.name}'s gift '{self.stat_name}' to {value}.|n")
            # Add message to target
            self.target.msg(f"|g{original_caller.name} set your gift {self.stat_name} to {value}.|n")
            return
        
        # Update any related stats
        self._update_dependent_stats(self.stat_name, value)
        
        # Show success message
        if full_stat_name != self.stat_name:
            self.caller.msg(f"|gSet {full_stat_name} to {value}.|n")
            # Add standard update message
            original_caller.msg(f"|gUpdated {self.target.name}'s {full_stat_name} to {value}.|n")
        else:
            self.caller.msg(f"|gSet {self.category}.{self.stat_type}.{self.stat_name} to {value}.|n")
            # Add standard update message
            original_caller.msg(f"|gUpdated {self.target.name}'s {self.stat_name} to {value}.|n")

    def detect_ability_category(self, stat_name: str) -> tuple[str, str]:
        """
        Detect the appropriate category and type for an ability or background.
        Returns (category, type) tuple.
        """
        # Convert to title case for consistent comparison
        stat_title = stat_name.title()
        stat_lower = stat_name.lower()
        
        # Special case for Gnosis - check splat first
        if stat_lower == 'gnosis':
            splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
            if splat and splat.lower() in ['shifter', 'possessed']:
                return 'pools', 'dual'

        # Check if it's a special advantage for Companions
        splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
        if splat == 'Companion':
            # First try exact match
            if stat_name in SPECIAL_ADVANTAGES:
                self.stat_name = stat_name  # Keep original case
                return 'powers', 'special_advantage'
            
            # Then try title case
            if stat_title in SPECIAL_ADVANTAGES:
                self.stat_name = stat_title
                return 'powers', 'special_advantage'
            
            # Finally try case-insensitive match
            proper_name = next((name for name in SPECIAL_ADVANTAGES.keys() if name.lower() == stat_lower), None)
            if proper_name:
                self.stat_name = proper_name  # Use the proper case name
                return 'powers', 'special_advantage'

        # Check if it's a gift or gift alias
        from world.wod20th.models import Stat
        
        # First check for exact match
        gift = Stat.objects.filter(
            name__iexact=stat_name,
            category='powers',
            stat_type='gift'
        ).first()
        
        if not gift:
            # Get all gifts and check their aliases
            all_gifts = Stat.objects.filter(
                category='powers',
                stat_type='gift'
            )
            for g in all_gifts:
                if g.gift_alias:  # Check if gift has aliases
                    if any(alias.lower() == stat_name.lower() for alias in g.gift_alias):
                        gift = g
                        break
        
        if gift:
            # Check if character can use gifts
            splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
            char_type = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
            can_use_gifts = (
                splat == 'Shifter' or 
                splat == 'Possessed' or 
                (splat == 'Mortal+' and char_type == 'Kinfolk')
            )
            
            if can_use_gifts:
                # For Shifters, check shifter_type
                if splat == 'Shifter' and gift.shifter_type:
                    allowed_types = []
                    if isinstance(gift.shifter_type, list):
                        allowed_types = [t.lower() for t in gift.shifter_type]
                    else:
                        allowed_types = [gift.shifter_type.lower()]
                    
                    # For Garou, check if they're trying to use an alias
                    if char_type == 'Garou' and gift.gift_alias:
                        # Check if the input name matches any alias
                        if any(alias.lower() == stat_name.lower() for alias in gift.gift_alias):
                            self.caller.msg(f"|rPlease use the Garou name '{gift.name}' instead of '{stat_name}'.|n")
                            return None, None
                    
                    if char_type.lower() not in allowed_types:
                        # Instead of showing the message here, just return the category so validation can handle it
                        return 'powers', 'gift'
                # For Kinfolk, check if they have the Gifted Kinfolk merit
                elif splat == 'Mortal+' and char_type == 'Kinfolk':
                    merit_value = self.target.get_stat('merits', 'supernatural', 'Gifted Kinfolk', temp=False)
                    if not merit_value:
                        self.caller.msg("|rMust have the 'Gifted Kinfolk' Merit to use gifts.|n")
                        return None, None
                
                # If we found it through an alias, update the stat name and show message
                if gift.name.lower() != stat_name.lower():
                    self.stat_name = gift.name
                    # Find which alias matched for the message
                    matched_alias = None
                    if gift.gift_alias:
                        for alias in gift.gift_alias:
                            if alias.lower() == stat_name.lower():
                                matched_alias = alias
                                break
                    if matched_alias:
                        if splat == 'Shifter':
                            if char_type == 'Garou':
                                self.caller.msg(f"|rPlease use the Garou name '{gift.name}' instead of '{stat_name}'.|n")
                                return None, None
                            else:
                                self.caller.msg(f"|y'{matched_alias}' is the {char_type} name for the Garou gift '{gift.name}'. Setting '{gift.name}' to {self.value_change}.|n")
                        else:
                            self.caller.msg(f"|y'{matched_alias}' is also known as '{gift.name}'. Setting '{gift.name}' to {self.value_change}.|n")
                    # Store the original alias for later use
                    self.alias_used = stat_name
                
                return 'powers', 'gift'
            else:
                self.caller.msg("|rOnly Shifters, Possessed, and Kinfolk can have gifts.|n")
                return None, None

        # Check identity stats
        if stat_title in IDENTITY_PERSONAL:
            return 'identity', 'personal'
        elif stat_title in IDENTITY_LINEAGE:
            return 'identity', 'lineage'
        elif stat_title in ['House', 'Fae Court', 'Kith', 'Seeming', 'Seelie Legacy', 'Unseelie Legacy',
                          'Type', 'Tribe', 'Breed', 'Auspice', 'Clan', 'Generation', 'Affiliation',
                          'Tradition', 'Convention', 'Methodology', 'Traditions Subfaction',
                          'Nephandi Faction', 'Possessed Type', 'Companion Type', 'Pryio', 'Lodge',
                          'Camp', 'Fang House', 'Crown', 'Plague', 'Ananasi Faction', 'Ananasi Cabal',
                          'Kitsune Path', 'Kitsune Faction', 'Ajaba Faction', 'Rokea Faction',
                          'Stream', 'Varna', 'Deed Name', 'Aspect', 'Jamak Spirit', 'Rank']:
            return 'identity', 'lineage'
        elif stat_title in ['Full Name', 'Concept', 'Date of Birth', 'Date of Chrysalis', 'Date of Awakening',
                          'First Change Date', 'Date of Embrace', 'Date of Possession', 'Nature', 'Demeanor',
                          'Path of Enlightenment', 'Fae Name', 'Tribal Name']:
            return 'identity', 'personal'

        # Check virtues since they're specific
        if stat_title in ['Conscience', 'Self-Control', 'Courage', 'Conviction', 'Instinct']:
            return 'virtues', 'moral'

        # Check vampire powers since they're most specific
        splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
        if splat and splat.lower() == 'vampire':
            # Get the stat definition from the database
            from world.wod20th.utils.vampire_utils import get_clan_disciplines
            
            # Check if it's a base discipline
            if stat_title in ['Animalism', 'Auspex', 'Celerity', 'Chimerstry', 'Dementation', 
                            'Dominate', 'Fortitude', 'Necromancy', 'Obfuscate', 'Obtenebration', 
                            'Potence', 'Presence', 'Protean', 'Quietus', 'Serpentis', 'Thaumaturgy', 
                            'Vicissitude', 'Temporis', 'Daimoinon', 'Sanguinus', 'Melpominee', 
                            'Mytherceria', 'Obeah', 'Thanatosis', 'Valeren', 'Spiritus', ]:
                return 'powers', 'discipline'
                
            # Check if it's a Thaumaturgy path
            if stat_title in ['Path of Blood', 'Lure of Flames', 'Movement of the Mind', 
                            'Path of Conjuring', 'Path of Corruption', 'Path of Mars', 
                            'Hands of Destruction', 'Neptune\'s Might', 'Path of Technomancy', 
                            'Path of the Father\'s Vengeance', 'Green Path', 'Elemental Mastery', 
                            'Weather Control', 'Gift of Morpheus', 'Oneiromancy', 'Path of Mercury', 
                            'Spirit Manipulation', 'Two Centimes Path', 'Path of Transmutation', 
                            'Path of Warding', 'Countermagic', 'Thaumaturgical Countermagic']:
                return 'powers', 'thaumaturgy'
                
            # Check if it's a Necromancy path
            if stat_title in ['Sepulchre Path', 'Bone Path', 'Ash Path', 'Cenotaph Path', 
                            'Vitreous Path', 'Mortis Path', 'Grave\'s Decay']:
                self.category = 'powers'
                self.stat_type = 'necromancy'
                return 'powers', 'necromancy'
                
            # Check if it's a ritual
            from world.wod20th.models import Stat
            stat = Stat.objects.filter(name__iexact=stat_name).first()
            if stat:
                if stat.stat_type in ['discipline', 'combodiscipline', 'thaumaturgy', 'thaum_ritual', 'necromancy', 'necromancy_ritual']:
                    return 'powers', stat.stat_type.lower()

        # Check pools 
        stat_title = stat_name.title()
        
        # Check dual pools
        if stat_title in POOL_TYPES['dual'].keys():
            return 'pools', 'dual'
            
        # Check resonance pools
        if stat_title in ['Dynamic', 'Static', 'Entropic']:
            return 'virtues', 'synergy'
        elif stat_title == 'Resonance':  # Add explicit handling for Resonance
            return 'pools', 'resonance'
            
        # Check moral pools
        if stat_title in POOL_TYPES['moral'].keys():
            return 'pools', 'moral'
            
        # Check advantage pools
        if stat_title in POOL_TYPES['advantage'].keys():
            return 'pools', 'advantage'

        # Check renown stats
        if stat_title in ['Glory', 'Honor', 'Wisdom', 'Cunning', 'Ferocity', 'Obligation', 'Obedience', 
                         'Humor', 'Infamy', 'Valor', 'Harmony', 'Innovation', 'Power']:
            return 'advantages', 'renown'

        # Check attributes
        for category, attributes in ATTRIBUTE_CATEGORIES.items():
            if stat_title in attributes:
                return 'attributes', category

        # Check standard abilities
        if stat_title in TALENTS:
            return 'abilities', 'talent'
        elif stat_title in SKILLS:
            return 'abilities', 'skill'
        elif stat_title in KNOWLEDGES:
            return 'abilities', 'knowledge'

        # Check secondary abilities
        if stat_title in SECONDARY_TALENTS:
            return 'secondary_abilities', 'secondary_talent'
        elif stat_title in SECONDARY_SKILLS:
            return 'secondary_abilities', 'secondary_skill'
        elif stat_title in SECONDARY_KNOWLEDGES:
            return 'secondary_abilities', 'secondary_knowledge'

        # Check merits
        for merit_type, merits in MERIT_CATEGORIES.items():
            # Convert stat_name to title case for each word and also try exact case
            stat_title_words = ' '.join(word.title() for word in stat_name.split())
            if stat_title_words in merits or stat_name in merits:
                return 'merits', merit_type
            # Try case-insensitive match
            stat_lower = stat_name.lower()
            for merit in merits:
                if merit.lower() == stat_lower:
                    return 'merits', merit_type

        # Check flaws
        for flaw_type, flaws in FLAW_CATEGORIES.items():
            # Convert stat_name to title case for each word and also try exact case
            stat_title_words = ' '.join(word.title() for word in stat_name.split())
            if stat_title_words in flaws or stat_name in flaws:
                return 'flaws', flaw_type
            # Try case-insensitive match
            stat_lower = stat_name.lower()
            for flaw in flaws:
                if flaw.lower() == stat_lower:
                    return 'flaws', flaw_type

        # Check backgrounds
        if stat_title in (
            UNIVERSAL_BACKGROUNDS +
            VAMPIRE_BACKGROUNDS +
            CHANGELING_BACKGROUNDS +
            MAGE_BACKGROUNDS +
            TECHNOCRACY_BACKGROUNDS +
            TRADITIONS_BACKGROUNDS + 
            NEPHANDI_BACKGROUNDS +
            SHIFTER_BACKGROUNDS +
            SORCERER_BACKGROUNDS +
            KINAIN_BACKGROUNDS
        ):
            # Special handling for Rank vs Organizational Rank
            if stat_title.lower() == 'rank':
                splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
                if splat and splat.lower() == 'shifter':
                    return 'identity', 'lineage'
                # If not a shifter, treat as Organizational Rank background
                self.stat_name = 'Organizational Rank'
            return 'backgrounds', 'background'

        # Check powers
        if stat_title in POWER_CATEGORIES:
            return 'powers', stat_title.lower()

        # Check if it's a sphere (from static mapping)
        if stat_title in MAGE_SPHERES:
            return 'powers', 'sphere'

        # Check if it's a Rite
        if any(rite['name'].lower() == stat_title.lower() for rite in ALL_RITES):
            return 'powers', 'rite'

        # Check if it's a Changeling Art
        if stat_title in ARTS:
            return 'powers', 'art'

        # Check if it's a Changeling Realm
        if stat_title in REALMS:
            return 'powers', 'realm'

        # Check identity stats
        identity_cat = self._detect_identity_category(stat_name)
        if identity_cat:
            return identity_cat

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
            'resonance': ('pools', 'resonance'),
            'essence energy': ('pools', 'dual')
        }
        
        if stat_name.lower() in pool_stats:
            return pool_stats[stat_name.lower()]

        # Get the stat definition from the database as a last resort
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
                'rite', 'combodiscipline', 'faith', 'arcanos', 'special_advantage',
                'sphere', 'sorcery', 'sliver', 'art', 'realm', 'necromancy'
            }
            if stat.stat_type.lower() in power_types:
                return 'powers', stat.stat_type.lower()

        return None, None

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

        # Special handling for Rank
        if stat_lower == 'rank':
            splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
            if splat and splat.lower() == 'shifter':
                return 'identity', 'lineage'
            return None, None

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

        # Check direct mappings
        if stat_title in IDENTITY_PERSONAL:
            return 'identity', 'personal'
        elif stat_title in IDENTITY_LINEAGE:
            return 'identity', 'lineage'
        elif stat_title in ['House', 'Fae Court', 'Kith', 'Seeming', 'Seelie Legacy', 'Unseelie Legacy',
                          'Type', 'Tribe', 'Breed', 'Auspice', 'Clan', 'Generation', 'Affiliation',
                          'Tradition', 'Convention', 'Methodology', 'Traditions Subfaction',
                          'Nephandi Faction', 'Possessed Type', 'Companion Type', 'Pryio', 'Lodge',
                          'Camp', 'Fang House', 'Crown', 'Plague', 'Ananasi Faction', 'Ananasi Cabal',
                          'Kitsune Path', 'Kitsune Faction', 'Ajaba Faction', 'Rokea Faction',
                          'Stream', 'Varna', 'Deed Name', 'Aspect', 'Jamak Spirit', 'Rank', 'Elemental Affinity', 'Fuel']:
            return 'identity', 'lineage'
        elif stat_title in ['Full Name', 'Concept', 'Date of Birth', 'Date of Chrysalis', 'Date of Awakening',
                          'First Change Date', 'Date of Embrace', 'Date of Possession', 'Nature', 'Demeanor',
                          'Path of Enlightenment', 'Fae Name', 'Tribal Name']:
            return 'identity', 'personal'
            
        # If not in direct mappings, check if it's a valid identity stat for the character's splat
        splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
        if not splat:
            return None, None
            
        # Get subtype and affiliation if applicable
        subtype = None
        affiliation = None
        
        if splat.lower() == 'shifter':
            subtype = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
        elif splat.lower() == 'mage':
            affiliation = self.target.get_stat('identity', 'lineage', 'Affiliation', temp=False)
        elif splat.lower() == 'changeling':
            subtype = self.target.get_stat('identity', 'lineage', 'Kith', temp=False)
        elif splat.lower() == 'possessed':
            subtype = self.target.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
        elif splat.lower() == 'mortal+':
            subtype = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
            
        valid_stats = get_identity_stats(splat, subtype, affiliation)
        
        # If the stat is in the valid stats list, determine its category
        if stat_title in valid_stats:
            # Personal stats are typically the base stats and dates
            if any(word.lower() in stat_lower for word in ['name', 'date', 'nature', 'demeanor', 'concept']):
                return 'identity', 'personal'
            # Everything else is lineage
            return 'identity', 'lineage'
            
        return None, None

    def _validate_path(self, path_name: str) -> tuple[bool, str, str]:
        """
        Validate a Path of Enlightenment name.
        
        Args:
            path_name: The name of the path to validate
            
        Returns:
            tuple: (is_valid, proper_path_name, error_message)
        """
        from world.wod20th.utils.vampire_utils import validate_vampire_path
        return validate_vampire_path(path_name)

    def _update_path_stats(self, path_name: str) -> None:
        """
        Update virtues and other stats based on Path of Enlightenment.
        
        Args:
            path_name: The name of the path to use for updates
        """
        from world.wod20th.utils.vampire_utils import update_vampire_virtues_on_path_change
        update_vampire_virtues_on_path_change(self.caller, path_name)

    def _check_gift_alias(self, gift_name: str) -> tuple[bool, str]:
        """
        Check if a gift name is an alias and return the canonical name.
        
        Args:
            gift_name: The name of the gift to check
            
        Returns:
            Tuple of (is_alias, canonical_name)
        """
        # Get character's splat and type
        splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
        char_type = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
        
        # Check if character can use gifts
        can_use_gifts = (
            splat == 'Shifter' or 
            splat == 'Possessed' or 
            (splat == 'Mortal+' and char_type == 'Kinfolk')
        )
        
        if not can_use_gifts:
            return False, None
            
        # Check if the gift exists in the database
        from world.wod20th.models import Stat
        gift = Stat.objects.filter(
            name__iexact=gift_name,
            category='powers',
            stat_type='gift'
        ).first()
        
        if gift:
            # Check if this character type can use this gift
            if splat == 'Shifter' and gift.shifter_type:
                allowed_types = []
                if isinstance(gift.shifter_type, list):
                    allowed_types = [t.lower() for t in gift.shifter_type]
                else:
                    allowed_types = [gift.shifter_type.lower()]
                
                # For Garou, check if they're trying to use an alias
                if char_type == 'Garou' and gift.gift_alias:
                    # Check if the input name matches any alias
                    if any(alias.lower() == gift_name.lower() for alias in gift.gift_alias):
                        self.caller.msg(f"|rPlease use the Garou name '{gift.name}' instead of '{gift_name}'.|n")
                        return False, None
                
                if char_type.lower() not in allowed_types:
                    # Return false but include the gift name for validation
                    return False, gift.name
            elif splat == 'Mortal+' and char_type == 'Kinfolk':
                # For Kinfolk, check if they have the Gifted Kinfolk merit
                merit_value = self.target.get_stat('merits', 'supernatural', 'Gifted Kinfolk', temp=False)
                if not merit_value:
                    self.caller.msg("|rMust have the 'Gifted Kinfolk' Merit to use gifts.|n")
                    return None, None
            return False, gift.name  # Found exact match, no need to check aliases
            
        # Get all gifts and check their aliases
        all_gifts = Stat.objects.filter(
            category='powers',
            stat_type='gift'
        )
        matched_gift = None
        for g in all_gifts:
            if g.gift_alias and any(alias.lower() == gift_name.lower() for alias in g.gift_alias):
                matched_gift = g
                break
        
        if matched_gift:
            gift = matched_gift
            # Check if this character type can use this gift
            if splat == 'Shifter':
                if gift.shifter_type:
                    allowed_types = []
                    # For Garou, prevent using non-Garou names
                    if char_type == 'Garou':
                        self.caller.msg(f"|rPlease use the Garou name '{gift.name}' instead of '{gift_name}'.|n")
                        return False, None
                    elif isinstance(gift.shifter_type, list):
                        allowed_types = [t.lower() for t in gift.shifter_type]
                    else:
                        allowed_types = [gift.shifter_type.lower()]
                    if char_type.lower() not in allowed_types:
                        # Return false but include the gift name for validation
                        return False, gift.name
            elif splat == 'Mortal+' and char_type == 'Kinfolk':
                # For Kinfolk, check if they have the Gifted Kinfolk merit
                merit_value = self.target.get_stat('merits', 'supernatural', 'Gifted Kinfolk', temp=False)
                if not merit_value:
                    self.caller.msg("|rMust have the 'Gifted Kinfolk' Merit to use gifts.|n")
                    return None, None
            
            # Find which alias matched
            matched_alias = None
            if gift.gift_alias:
                for alias in gift.gift_alias:
                    if alias.lower() == gift_name.lower():
                        matched_alias = alias
                        break
            
            if matched_alias:
                # Customize message based on character type
                if splat == 'Shifter':
                    if char_type == 'Garou':
                        self.caller.msg(f"|rPlease use the Garou name '{gift.name}' instead of '{gift_name}'.|n")
                        return False, None
                    else:
                        self.caller.msg(f"|y'{matched_alias}' is the {char_type} name for the Garou gift '{gift.name}'. Setting '{gift.name}' to {self.value_change}.|n")
                        
                        # Use set_gift_alias method for consistent handling
                        # Important: Use the ORIGINAL gift name that was entered by the user
                        self.target.set_gift_alias(gift.name, gift_name, self.value_change)
                else:
                    self.caller.msg(f"|y'{matched_alias}' is also known as '{gift.name}'. Setting '{gift.name}' to {self.value_change}.|n")
                    
                    # Use set_gift_alias method for consistent handling
                    # Important: Use the ORIGINAL gift name that was entered by the user
                    self.target.set_gift_alias(gift.name, gift_name, self.value_change)
            return True, gift.name
            
        return False, None

    def validate_merit(self, merit_name: str, value: str, category: str = None) -> tuple[bool, str]:
        """
        Validate a merit's name, value, and category.
        
        Args:
            merit_name: The name of the merit to validate
            value: The merit value to validate
            category: The merit category (physical, social, mental, supernatural)
            
        Returns:
            tuple: (is_valid, error_message)
        """
        # Validate the merit value
        try:
            merit_value = int(value)
            if merit_value not in MERIT_VALUES:
                return False, f"Merit values must be one of: {', '.join(map(str, sorted(MERIT_VALUES)))}"
        except ValueError:
            return False, "Merit value must be a number"
            
        # Get character's splat and type for restriction checking
        splat = self.splat
        char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
        
        # Check splat restrictions if this merit is restricted
        if merit_name in MERIT_SPLAT_RESTRICTIONS:
            allowed_splats = MERIT_SPLAT_RESTRICTIONS[merit_name]
            if splat not in allowed_splats:
                return False, f"The merit '{merit_name}' is only available to {', '.join(allowed_splats)} characters."
                
        # If category is provided, validate it
        if category:
            if category.lower() not in [c.lower() for c in MERIT_CATEGORIES]:
                return False, f"Invalid merit category. Must be one of: {', '.join(MERIT_CATEGORIES)}"
                
        return True, ""
        
    def validate_flaw(self, flaw_name: str, value: str, category: str = None) -> tuple[bool, str]:
        """
        Validate a flaw's name, value, and category.
        
        Args:
            flaw_name: The name of the flaw to validate
            value: The flaw value to validate
            category: The flaw category (physical, social, mental, supernatural)
            
        Returns:
            tuple: (is_valid, error_message)
        """
        # Validate the flaw value
        try:
            flaw_value = int(value)
            if flaw_value not in FLAW_VALUES:
                return False, f"Flaw values must be one of: {', '.join(map(str, sorted(FLAW_VALUES)))}"
        except ValueError:
            return False, "Flaw value must be a number"
            
        # Get character's splat and type for restriction checking
        splat = self.splat
        char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
        
        # Check splat restrictions if this flaw is restricted
        if flaw_name in FLAW_SPLAT_RESTRICTIONS:
            allowed_splats = FLAW_SPLAT_RESTRICTIONS[flaw_name]
            if splat not in allowed_splats:
                return False, f"The flaw '{flaw_name}' is only available to {', '.join(allowed_splats)} characters."
                
        # If category is provided, validate it
        if category:
            if category.lower() not in [c.lower() for c in FLAW_CATEGORIES]:
                return False, f"Invalid flaw category. Must be one of: {', '.join(FLAW_CATEGORIES)}"
                
        return True, ""