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
    ATTRIBUTE_CATEGORIES, SPECIAL_ADVANTAGES, COMBAT_SPECIAL_ADVANTAGES,
    STAT_VALIDATION, VALID_SPLATS, GENERATION_MAP,
    GENERATION_FLAWS, BLOOD_POOL_MAP, get_identity_stats,
    UNIVERSAL_BACKGROUNDS, VAMPIRE_BACKGROUNDS,
    CHANGELING_BACKGROUNDS, MAGE_BACKGROUNDS,
    TECHNOCRACY_BACKGROUNDS, TRADITIONS_BACKGROUNDS,
    NEPHANDI_BACKGROUNDS, SHIFTER_BACKGROUNDS,
    SORCERER_BACKGROUNDS, IDENTITY_PERSONAL, IDENTITY_LINEAGE,
    ARTS, REALMS, VALID_DATES, MERIT_VALUES, FLAW_VALUES,
    MERIT_CATEGORIES, FLAW_CATEGORIES, MERIT_SPLAT_RESTRICTIONS,
    FLAW_SPLAT_RESTRICTIONS, ARTS, REALMS, ALL_MERITS, ALL_FLAWS,
    KINFOLK_BREED_CHOICES
)
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
    SHIFTER_RENOWN, initialize_shifter_type, SHIFTER_TYPE_CHOICES, BREED_CHOICES_DICT,
    AUSPICE_CHOICES, GAROU_TRIBE_CHOICES, BASTET_TRIBE_CHOICES, 
    update_shifter_pools_on_stat_change, SHIFTER_IDENTITY_STATS, 
    BREED_CHOICES, ASPECT_CHOICES_DICT, AUSPICE_CHOICES_DICT,
    validate_shifter_stats
)
from world.wod20th.utils.changeling_utils import (
    FAE_COURTS, HOUSES, PHYLA, initialize_changeling_stats, KITH, SEEMING,
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
from evennia.utils.search import search_object

REQUIRED_INSTANCES = ['Library', 'Status', 'Influence', 'Wonder', 'Secret Weapon', 'Companion', 
                      'Familiar', 'Enhancement', 'Laboratory', 'Favor', 'Acute Senses', 
                      'Enchanting Feature', 'Secret Code Language', 'Hideaway', 'Safehouse', 
                      'Sphere Natural', 'Phobia', 'Addiction', 'Allies', 'Contacts', 'Caretaker',
                      'Alternate Identity', 'Equipment', 'Professional Certification', 'Allergic',
                      'Impediment', 'Enemy', 'Mentor', 'Old Flame', 'Additional Discipline', 
                      'Totem', 'Boon', 'Treasure', 'Geas', 'Fetish', 'Chimerical Item', 'Chimerical Companion',
                      'Dreamers', 'Digital Dreamers', 'Addiction', 'Phobia', 'Derangement',
                      'Obsession', 'Compulsion', 'Bigot', 'Ability Deficit', 'Sect Enmity', 'Camp Enmity',
                      'Retainers', 'Sphere Inept', 'Art Affinity', 'Immunity'
                     ] 

# Add the REQUIRED_SPECIALTIES constant
REQUIRED_SPECIALTIES = {
    'Crafts': 'mechanics, blacksmithing, woodworking, etc.',
    'Artistry': 'painting, sculpture, graphic design, etc.',
    'Pilot': 'boat, plane, tank, etc.',
    'Area Knowledge': 'an area of San Diego',
    'Martial Arts': 'requires a style',
    'Performance': 'singing, dancing, guitar, etc.',
    'Fencing': 'western or kenjutsu',
    'Science': 'biology, chemistry, physics, etc.',
    'Hypertech': 'electronics, computers, robotics, etc.'
}

class CmdSelfStat(MuxCommand):
    """
    Usage:
      +selfstat <stat>[(<instance>)]/<type>=[+-]<value>
      +selfstat <stat>[(<instance>)]/<type>=

    Examples:
      +selfstat Strength/Physical=+1
      +selfstat Firearms/Skill=-1
      +selfstat Status(Ventrue)/Social= (removes the stat)
      +selfstat Nature/Personal=Architect
      +selfstat Demeanor/Personal=Bon Vivant

    Staff command:
      +staffstat <character>=<stat>[(<instance>)]/<type>=[+-]<value>
      +staffstat <character>=<stat>[(<instance>)]/<type>=
      +staffstat <character>=<stat>=<value>

    Examples:
      +staffstat Bob=Strength/Physical:3
      +staffstat Bob=Strength:3        (same as above)
      +staffstat Jane=Status(Camarilla):2
      +staffstat Mike=Path of Enlightenment:Night
      +staffstat Sarah=Nature/Personal:Architect

    This version of the selfstat command allows staff to set stats on other characters, 
    bypassing normal restrictions like character approval status and validation limits.
    """

    key = "+selfstat"
    aliases = ["selfstat"]
    locks = "cmd:all()"  # All players can use this command
    help_category = "Chargen & Character Info"
    def __init__(self):
        """Initialize the command."""
        super().__init__()
        self.switches = []
        self.is_specialty = False  # Add this line
        self.specialty = None      # Add this line
        self.stat_name = ""
        self.instance = None
        self.category = None
        self.value_change = None
        self.stat_type = None
        
    # Helper Methods
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
        self.caller.msg(f"|yUsage: +selfstat <stat>[(<instance>)]/[<category>]=[+-]<value>|n")
		
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
        valid_splats = {'Vampire', 'Mage', 'Shifter', 'Changeling', 'Mortal+', 'Possessed', 'Companion', 'Mortal'}
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
        Check if a value exists in a set while ignoring case.
        Returns (bool, matched_value) where matched_value is the correctly-cased version if found.
        """
        if not value:
            return False, None
            
        # Try title case
        if value.title() in valid_set:
            return True, value.title()
            
        # Try case-insensitive match
        value_lower = value.lower()
        for valid_value in valid_set:
            if valid_value.lower() == value_lower:
                return True, valid_value
            
        # If no match found, suggest similar values
        similar_values = []
        for valid_value in valid_set:
            # Check if the input is a substring of any valid value
            if value_lower in valid_value.lower():
                similar_values.append(valid_value)
            # Check if input matches the beginning of any word in the valid value
            elif any(word.lower().startswith(value_lower) 
                    for word in valid_value.split()):
                similar_values.append(valid_value)
                
        if similar_values:
            return False, f"Invalid value. Did you mean one of these?: {', '.join(sorted(similar_values))}"
        else:
            return False, f"Invalid value. Valid options are: {', '.join(sorted(valid_set))}"

    def case_insensitive_in_nested(self, value: str, nested_dict: dict, parent_value: str) -> tuple[bool, str]:
        """
        Check if a value exists in a nested dictionary's list, ignoring case.
        Returns (bool, matched_value) where matched_value is the correctly-cased version if found.
        """
        if not value or not parent_value:
            return False, None
            
        # Get valid values for this parent
        valid_values = nested_dict.get(parent_value, [])
        if not valid_values:
            # If no values found for this parent, check all values
            all_values = set()
            for values in nested_dict.values():
                all_values.update(values)
            # Try to find similar values across all categories
            similar_values = []
            value_lower = value.lower()
            for valid_value in all_values:
                if value_lower in valid_value.lower() or any(word.lower().startswith(value_lower) for word in valid_value.split()):
                    similar_values.append(valid_value)
            if similar_values:
                return False, f"Invalid value. Similar values found in other categories: {', '.join(sorted(similar_values))}"
            return False, f"Invalid value. No valid options found for {parent_value}"
            
        # Try direct match first
        is_valid, matched_value = self.case_insensitive_in(value, set(valid_values))
        if is_valid:
            return True, matched_value
            
        # If no match, suggest similar values for this parent
        value_lower = value.lower()
        similar_values = []
        for valid_value in valid_values:
            if value_lower in valid_value.lower() or any(word.lower().startswith(value_lower) for word in valid_value.split()):
                similar_values.append(valid_value)
                
        if similar_values:
            return False, f"Invalid value for {parent_value}. Did you mean one of these?: {', '.join(sorted(similar_values))}"
        else:
            return False, f"Invalid value for {parent_value}. Valid options are: {', '.join(sorted(valid_values))}"

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

    def _validate_kinfolk_gift(self, gift, value=None) -> tuple[bool, str, str]:
        """
        Validate if a Kinfolk can learn a specific gift.
        
        Args:
            gift: The gift object to validate
            value: Optional value to validate for the gift level
            
        Returns:
            Tuple of (is_valid, error_message, corrected_value)
        """
        # Get kinfolk's tribe
        kinfolk_tribe = self.caller.get_stat('identity', 'lineage', 'Tribe', temp=False)
        if not kinfolk_tribe:
            return False, "Must set tribe before learning gifts", None
        
        # If value provided, validate gift level (Kinfolk can only learn level 1-2)
        if value is not None:
            try:
                gift_value = int(value)
                if gift_value > 2:
                    return False, "Kinfolk can only learn level 1-2 gifts", None
            except ValueError:
                return False, "Gift value must be a number", None
        
        # Check if it's a homid gift
        if gift.shifter_type:
            allowed_types = gift.shifter_type if isinstance(gift.shifter_type, list) else [gift.shifter_type]
            if 'homid' in [t.lower() for t in allowed_types]:
                return True, "", gift.name
        
        # Check if it's a tribal gift
        if gift.tribe:
            # Handle both string and list cases for tribe
            if isinstance(gift.tribe, str):
                if gift.tribe.lower() == kinfolk_tribe.lower():
                    return True, "", gift.name
            else:
                # Handle list case
                allowed_tribes = gift.tribe if isinstance(gift.tribe, list) else [gift.tribe]
                if kinfolk_tribe.lower() in [t.lower() for t in allowed_tribes]:
                    return True, "", gift.name
        
        return False, f"Kinfolk can only learn Homid gifts or gifts from their tribe ({kinfolk_tribe})", None

    def _check_gift_alias(self, gift_name: str) -> tuple[bool, str]:
        """
        Check if a gift name is an alias and return the canonical name.
        
        Args:
            gift_name: The name of the gift to check
            
        Returns:
            Tuple of (is_alias, canonical_name)
        """
        # Get character's splat and type
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
        char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
        
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
                # Validate Kinfolk gift access
                is_valid, error_msg, canonical_name = self._validate_kinfolk_gift(gift)
                if not is_valid:
                    self.caller.msg(f"|r{error_msg}|n")
                    return False, None
                return True, canonical_name
            return True, gift.name  # Found exact match
         
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
            
            # Find which alias matched
            matched_alias = None
            if gift.gift_alias:
                for alias in gift.gift_alias:
                    if alias.lower() == gift_name.lower():
                        matched_alias = alias
                        break
            
            if matched_alias:
                # Store the original input name as the alias_used before it gets changed
                self.alias_used = matched_alias  # Use the exact alias from the database
                
                # Customize message based on character type
                if splat == 'Shifter':
                    if char_type == 'Garou':
                        self.caller.msg(f"|rPlease use the Garou name '{gift.name}' instead of '{gift_name}'.|n")
                        return False, None
                    else:
                        self.caller.msg(f"|y'{matched_alias}' is the {char_type} name for the Garou gift '{gift.name}'. Setting '{gift.name}' to {self.value_change}.|n")
                else:
                    self.caller.msg(f"|y'{matched_alias}' is also known as '{gift.name}'. Setting '{gift.name}' to {self.value_change}.|n")
                
                # Return after setting the message
                return True, gift.name
                
            # If we found a match but no matching alias (unusual case), still return the gift name
            return True, gift.name
            
        # If no match was found at all
        return False, None

    def validate_stat_value(self, stat_name: str, value: str, category: str = None, stat_type: str = None) -> tuple:
        """
        Validate a stat value based on its type and category.
        Returns (is_valid, error_message, corrected_value)
        """
        # Check for None values in all parameters
        if stat_name is None:
            return False, "Stat name cannot be None", None
        if value is None:
            return False, f"Value cannot be None for {stat_name}", None
        if category is None:
            # This is expected in some cases when auto-detecting the category
            pass
        if stat_type is None:
            # This is expected in some cases when auto-detecting the stat_type
            pass
            
        # Special handling for hedge rituals
        if category == 'powers' and stat_type == 'hedge_ritual':
            try:
                ritual_value = int(value)
                if ritual_value < 0 or ritual_value > 5:
                    return False, f"Hedge ritual level must be between 0 and 5", None
                return True, "", str(ritual_value)
            except ValueError:
                return False, "Hedge ritual level must be a number", None
            
        # Get character's splat and type - try direct access first
        splat = None
        if (hasattr(self.caller, 'db') and 
            hasattr(self.caller.db, 'stats') and 
            'other' in self.caller.db.stats and 
            'splat' in self.caller.db.stats['other'] and 
            'Splat' in self.caller.db.stats['other']['splat']):
            splat = self.caller.db.stats['other']['splat']['Splat'].get('perm')
        
        # If direct access failed, try get_stat
        if not splat:
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            
        char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)

        # Only allow Mortals to set Occupation
        if stat_name.lower() == 'occupation' and splat != 'Mortal':
            return False, "Only Mortals can set an Occupation.", None

        # Special handling for Arcane
        if stat_name.lower() == 'arcane':
            try:
                value_int = int(value)
                if value_int < 0 or value_int > 5:
                    return False, f"Arcane must be between 0 and 5", None
                
                # For Vampires, validate as a merit
                if splat == 'Vampire':
                    if category != 'merits' or stat_type != 'social':
                        return False, "For Vampires, Arcane must be set as a social merit", None
                # For non-Vampires, validate as a background
                else:
                    if category != 'backgrounds' or stat_type != 'background':
                        return False, "For non-Vampires, Arcane must be set as a background", None
                return True, "", str(value_int)
            except ValueError:
                return False, "Arcane value must be a number", None

        # Get the stat definition from the database
        from world.wod20th.models import Stat
        stat = Stat.objects.filter(name__iexact=stat_name).first()
        
        # Check if this stat requires an instance
        if self._requires_instance(stat_name, category) and not self.instance:
            self._display_instance_requirement_message(stat_name)
            return False, "", None
        
        if stat and stat.category == 'backgrounds':
            # For backgrounds, validate the value is numeric and in range
            try:
                bg_value = int(value)
                if bg_value < 0 or bg_value > 10:
                    return False, f"{stat_name} must be between 0 and 10", None
                return True, "", str(bg_value)
            except ValueError:
                return False, f"{stat_name} value must be a number", None

        # Special handling for merits
        if category == 'merits':
            # Get character's splat type if needed for restriction checks
            char_type = None
            if splat == 'Shifter':
                char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
            elif splat == 'Mortal+':
                char_type = self.caller.get_stat('identity', 'lineage', 'MortalPlus Type', temp=False)
            elif splat == 'Companion':
                char_type = self.caller.get_stat('identity', 'lineage', 'Companion Type', temp=False)
            elif splat == 'Possessed':
                char_type = self.caller.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
                
            # Get the merit from the database
            from world.wod20th.models import Stat
            merit = Stat.objects.filter(
                name__iexact=stat_name,
                category='merits',
                stat_type=stat_type
            ).first()
            
            if merit:
                # Update stat_name to use proper case from database
                self.stat_name = merit.name
                
                # Check if this is a shifter-specific merit
                if merit.shifter_type:
                    if splat != 'Shifter':
                        # Remove the stat if it was set
                        if category in self.caller.db.stats and stat_type in self.caller.db.stats[category]:
                            if self.stat_name in self.caller.db.stats[category][stat_type]:
                                del self.caller.db.stats[category][stat_type][self.stat_name]
                        return False, f"The merit '{merit.name}' is only available to Shifter characters.", None
                    
                    # Handle shifter_type the same way as gifts
                    allowed_types = []
                    if isinstance(merit.shifter_type, list):
                        # Handle negation cases (e.g., "!Ananasi")
                        for t in merit.shifter_type:
                            if isinstance(t, str):
                                if t.startswith('!'):
                                    if char_type.lower() == t[1:].lower():
                                        # Remove the stat if it was set
                                        if category in self.caller.db.stats and stat_type in self.caller.db.stats[category]:
                                            if self.stat_name in self.caller.db.stats[category][stat_type]:
                                                del self.caller.db.stats[category][stat_type][self.stat_name]
                                        return False, f"The merit '{merit.name}' is not available to {char_type} characters.", None
                                else:
                                    allowed_types.append(t.lower())
                    else:
                        allowed_types = [merit.shifter_type.lower()]
                    
                    # Check if character's type is allowed
                    if allowed_types and char_type.lower() not in allowed_types:
                        # Check if they already have this merit
                        current_value = self.caller.get_stat('merits', stat_type, merit.name, temp=False)
                        if current_value is None:  # Only block if they don't already have it
                            # Format the list of types nicely
                            type_list = [t.title() for t in allowed_types]
                            if len(type_list) == 1:
                                type_str = type_list[0]
                            elif len(type_list) == 2:
                                type_str = f"{type_list[0]} and {type_list[1]}"
                            else:
                                type_str = f"{', '.join(type_list[:-1])}, and {type_list[-1]}"
                            # Remove the stat if it was set
                            if category in self.caller.db.stats and stat_type in self.caller.db.stats[category]:
                                if self.stat_name in self.caller.db.stats[category][stat_type]:
                                    del self.caller.db.stats[category][stat_type][self.stat_name]
                            return False, f"The merit '{merit.name}' is only available to {type_str} characters.", None
                
                # Validate merit value
                try:
                    merit_value = int(value)
                    if merit_value not in merit.values:
                        # Remove the stat if it was set
                        if category in self.caller.db.stats and stat_type in self.caller.db.stats[category]:
                            if self.stat_name in self.caller.db.stats[category][stat_type]:
                                del self.caller.db.stats[category][stat_type][self.stat_name]
                        return False, f"Invalid value for merit {merit.name}. Valid values are: {', '.join(map(str, merit.values))}", None
                    return True, "", str(merit_value)
                except ValueError:
                    # Remove the stat if it was set
                    if category in self.caller.db.stats and stat_type in self.caller.db.stats[category]:
                        if self.stat_name in self.caller.db.stats[category][stat_type]:
                            del self.caller.db.stats[category][stat_type][self.stat_name]
                    return False, "Merit value must be a number", None

        # Special handling for Companions' special advantages
        if splat == 'Companion' and (category == 'powers' and stat_type == 'special_advantage'):
            # Get proper case name from SPECIAL_ADVANTAGES
            proper_name = next((name for name in SPECIAL_ADVANTAGES.keys() if name.lower() == stat_name.lower()), 
                              next((name for name in COMBAT_SPECIAL_ADVANTAGES.keys() if name.lower() == stat_name.lower()), None))
            if not proper_name:
                return False, f"'{stat_name}' is not a valid special advantage", None

            # Check if this advantage requires an instance
            if self._requires_instance(proper_name):
                if not self.instance:
                    # This will be handled earlier in the command flow
                    return False, f"'{proper_name}' requires an instance", None
                # When we have an instance, use it as part of the stat name
                proper_name = f"{proper_name}({self.instance})"

            # Get the advantage info
            advantage_key = proper_name
            advantage_info = SPECIAL_ADVANTAGES.get(advantage_key, COMBAT_SPECIAL_ADVANTAGES.get(advantage_key))
            if not advantage_info:
                return False, f"No information found for {proper_name}", None
                
            try:
                advantage_value = int(value)
                if 'valid_values' not in advantage_info:
                    return False, f"No valid values defined for {proper_name}", None
                if advantage_value not in advantage_info['valid_values']:
                    valid_values_str = ', '.join(map(str, advantage_info['valid_values']))
                    return False, f"Invalid value for {proper_name}. Valid values are: {valid_values_str}", None
                
                # Update stat_name to proper case
                self.stat_name = proper_name
                return True, "", str(advantage_value)
            except ValueError:
                return False, "Special advantage value must be a number", None

        # Special handling for gifts
        if category == 'powers' and stat_type == 'gift':
            # Check if character can use gifts
            can_use_gifts = (
                splat == 'Shifter' or 
                splat == 'Possessed' or 
                (splat == 'Mortal+' and char_type == 'Kinfolk')
            )
            
            if not can_use_gifts:
                return False, "Only Shifters, Possessed, and Kinfolk can have gifts", None
                
            # Check for gift aliases first
            is_alias, canonical_name = self._check_gift_alias(stat_name)
            if is_alias:
                # Only set alias_used if it wasn't already set in _check_gift_alias
                if not hasattr(self, 'alias_used'):
                    self.alias_used = stat_name
                # Update stat_name to canonical name
                stat_name = canonical_name
                self.stat_name = canonical_name
            
            if not canonical_name:
                return False, f"Could not find a valid gift name for '{stat_name}'", None
            
            # Get the gift from the database
            from world.wod20th.models import Stat
            gift = Stat.objects.filter(
                name__iexact=stat_name,
                category='powers',
                stat_type='gift'
            ).first()
            
            if not gift:
                return False, f"'{stat_name}' is not a valid gift", None
                
            # For Shifters, check shifter_type
            if splat == 'Shifter' and gift.shifter_type:
                allowed_types = []
                if isinstance(gift.shifter_type, list):
                    allowed_types = [t.lower() for t in gift.shifter_type]
                else:
                    allowed_types = [gift.shifter_type.lower()]
                
                if char_type.lower() not in allowed_types:
                    # Only display the error message once here, not in _check_gift_alias
                    return False, f"The gift '{gift.name}' is not available to {char_type}. Available to: {', '.join(t.title() for t in allowed_types)}", None
                
            elif splat == 'Mortal+' and char_type == 'Kinfolk':
                # Validate Kinfolk gift access and level
                is_valid, error_msg, canonical_name = self._validate_kinfolk_gift(gift, value)
                if not is_valid:
                    return False, error_msg, None
                return True, "", value
            
            # Validate the gift value
            try:
                gift_value = int(value)
                # First check if the gift has specific valid values
                if gift.values:
                    valid_values = gift.values if isinstance(gift.values, list) else [gift.values]
                    if gift_value not in valid_values:
                        return False, f"Invalid value for {gift.name}. Valid values are: {', '.join(map(str, valid_values))}", None
                # If no specific values defined, use default range check
                elif gift_value < 0 or gift_value > 5:
                    return False, "Gift values must be between 0 and 5", None
                # Return the canonical name and the original alias
                return True, "", str(gift_value)
            except ValueError:
                return False, "Gift value must be a number", None

        if not splat:
            return False, "Character must have a splat set", None

        # Special handling for Ferocity based on splat
        if stat_name.lower() == 'ferocity':
            if splat == 'Shifter':
                # Get shifter type
                shifter_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
                if not shifter_type:
                    return False, "Must set shifter type before setting Ferocity.", None
                
                # Check if this shifter type has access to Ferocity renown
                valid_renown = SHIFTER_RENOWN.get(shifter_type, [])
                if 'Ferocity' not in valid_renown:
                    return False, f"{shifter_type} characters do not have access to Ferocity renown.", None
                
                # For Shifters, Ferocity is a Renown type
                try:
                    ferocity_value = int(value)
                    if ferocity_value < 0 or ferocity_value > 10:
                        return False, "Ferocity renown must be between 0 and 10", None
                    self.category = 'advantages'
                    self.stat_type = 'renown'
                    return True, "", str(ferocity_value)
                except ValueError:
                    return False, "Ferocity renown value must be a number", None
            elif splat == 'Companion':
                # For Companions, Ferocity is a special advantage
                self.category = 'powers'
                self.stat_type = 'special_advantage'
                # Let companion validation handle it
                result = validate_companion_stats(self.caller, stat_name, value, self.category, self.stat_type)
                if len(result) == 3:
                    is_valid, error_msg, proper_value = result
                    if proper_value and stat_name.lower() == 'elemental affinity':
                        # For elemental affinity, use the proper_value as the actual value to set
                        return is_valid, error_msg, proper_value
                    return is_valid, error_msg, str(proper_value) if proper_value else None
                return False, "Invalid value for Ferocity", None
        
        # Special handling for Obedience based on splat
        if stat_name.lower() == 'obedience':
            if splat == 'Shifter':
                # Get shifter type
                shifter_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
                if not shifter_type:
                    return False, "Must set shifter type before setting Obedience.", None
                
                # Check if this shifter type has access to Obedience renown
                valid_renown = SHIFTER_RENOWN.get(shifter_type, [])
                if 'Obedience' not in valid_renown:
                    return False, f"{shifter_type} characters do not have access to Obedience renown.", None
                
                # For Shifters, Obedience is a Renown type
                try:
                    obedience_value = int(value)
                    if obedience_value < 0 or obedience_value > 10:
                        return False, "Obedience renown must be between 0 and 10", None
                    self.category = 'advantages'
                    self.stat_type = 'renown'
                    return True, "", str(obedience_value)
                except ValueError:
                    return False, "Obedience renown value must be a number", None

        # Special handling for Path of Enlightenment and Enlightenment
        if stat_name.lower() in ['path of enlightenment', 'enlightenment']:
            # For Vampires and Ghouls
            if splat == 'Vampire' or (splat == 'Mortal+' and char_type == 'Ghoul'):
                # Always use Path of Enlightenment in identity.personal
                self.stat_name = 'Path of Enlightenment'
                self.category = 'identity'
                self.stat_type = 'personal'
                
                # Validate the path value
                from world.wod20th.utils.vampire_utils import validate_vampire_path
                is_valid, error_msg = validate_vampire_path(value)
                if not is_valid:
                    return False, error_msg, None
                
                # If valid, return success
                return True, "", value
            
            # For Technocracy Mages
            elif splat == 'Mage':
                affiliation = self.caller.get_stat('identity', 'lineage', 'Affiliation', temp=False)
                if affiliation == 'Technocracy':
                    try:
                        val = int(value)
                        if val < 1 or val > 10:
                            return False, "Enlightenment must be between 1 and 10 for Technocracy mages", None
                        # Set in pools/advantage
                        self.category = 'pools'
                        self.stat_type = 'advantage'
                        return True, "", str(val)
                    except ValueError:
                        return False, "Enlightenment must be a number", None
                else:
                    return False, "Only Technocracy mages can have Enlightenment", None
            
            else:
                return False, "Only Technocracy mages, Vampires, and Ghouls can have Enlightenment", None

        # Special handling for Berserker
        if stat_name.lower() == 'berserker':
            # For Possessed characters, always handle as blessing regardless of category
            if splat == 'Possessed':
                # Call possessed_utils validation directly
                result = validate_possessed_stats(self.caller, stat_name, value, 'powers', 'blessing')
                if result[0]:  # If validation was successful
                    self.category = 'powers'  # Set the correct category
                    self.stat_type = 'blessing'  # Set the correct stat type
                return result  # Return early after validation
            
            # For Shifter characters, always handle as merit
            elif splat == 'Shifter':
                self.category = 'merits'
                self.stat_type = 'mental'
                try:
                    val = int(value)
                    if val != 2:
                        return False, "Berserker merit must be 2 points for Shifters", None
                    return True, "", str(val)
                except ValueError:
                    return False, "Merit value must be a number", None
            
            # For other splats, reject
            else:
                return False, "Berserker is only available to Possessed (as a blessing) or Shifters (as a merit)", None

        # Define categories that must be numeric
        numeric_categories = {
            'attributes': True,
            'abilities': True,
            'backgrounds': True,
            'powers': True,
            'merits': True,
            'flaws': True,
            'virtues': True,
            'pools': True
        }

        # Check if this stat belongs to a numeric category
        if category in numeric_categories:
            # Special case for charms, which are powers but not numeric
            if stat_type == 'charm':
                return True, "", value
                
            try:
                numeric_value = int(value)
                # Add range validation based on category
                if category == 'attributes':
                    if numeric_value < 1 or numeric_value > 10:
                        return False, f"{stat_name} must be between 1 and 10", None
                elif category in ['abilities', 'powers', 'virtues']:
                    if numeric_value < 0 or numeric_value > 5:
                        return False, f"{stat_name} must be between 0 and 5", None
                elif category == 'backgrounds':
                    if numeric_value < 0 or numeric_value > 10:
                        return False, f"{stat_name} must be between 0 and 10", None
                elif category == 'pools':
                    if numeric_value < 0 or numeric_value > 10:
                        return False, f"{stat_name} must be between 0 and 10", None
                return True, "", str(numeric_value)
            except ValueError:
                return False, f"{stat_name} must be a number", None

        # Handle Shifter-specific validation
        if splat == 'Shifter':
            from world.wod20th.utils.shifter_utils import validate_shifter_stats
            result = validate_shifter_stats(self.caller, stat_name, value, category, stat_type)
            if len(result) == 2:
                is_valid, error_msg = result
                return is_valid, error_msg, value if is_valid else None
            return result
            
        # Call appropriate validation function based on splat
        if splat == 'Vampire':
            result = validate_vampire_stats(self.caller, stat_name, value, category, stat_type)
            if len(result) == 2:
                is_valid, error_msg = result
                return is_valid, error_msg, value if is_valid else None
            return result
        elif splat == 'Mage':
            result = validate_mage_stats(self.caller, stat_name, value, category, stat_type)
            if len(result) == 2:
                is_valid, error_msg = result
                return is_valid, error_msg, value if is_valid else None
            return result
        elif splat == 'Changeling':
            result = validate_changeling_stats(self.caller, stat_name, value, category, stat_type)
            if len(result) == 2:
                is_valid, error_msg = result
                return is_valid, error_msg, value if is_valid else None
            return result
        elif splat == 'Mortal+':
            result = validate_mortalplus_stats(self.caller, stat_name, value, category, stat_type)
            if len(result) == 2:
                is_valid, error_msg = result
                return is_valid, error_msg, value if is_valid else None
            return result
        elif splat == 'Possessed':
            result = validate_possessed_stats(self.caller, stat_name, value, category, stat_type)
            # Remove the length check since we know it's always a 3-tuple
            is_valid, error_msg, corrected_value = result
            return is_valid, error_msg, corrected_value
        elif splat == 'Companion':
            result = validate_companion_stats(self.caller, stat_name, value, category, stat_type)
            if len(result) == 3:
                is_valid, error_msg, proper_value = result
                if proper_value and stat_name.lower() == 'elemental affinity':
                    # For elemental affinity, use the proper_value as the actual value to set
                    return is_valid, error_msg, proper_value
                elif proper_value:  # For other stats, use the proper_value as the stat name
                    self.stat_name = proper_value
                return is_valid, error_msg, value if is_valid else None
            return result
        
        return True, "", value

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

        # Special handling for Rank
        if stat_lower == 'rank':
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
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
                          'Type', 'Tribe', 'Breed', 'Kinfolk Breed', 'Auspice', 'Clan', 'Generation', 'Affiliation',
                          'Tradition', 'Convention', 'Methodology', 'Traditions Subfaction',
                          'Nephandi Faction', 'Possessed Type', 'Companion Type', 'Pryio', 'Lodge',
                          'Camp', 'Fang House', 'Crown', 'Plague', 'Ananasi Faction', 'Ananasi Cabal',
                          'Kitsune Path', 'Kitsune Faction', 'Ajaba Faction', 'Rokea Faction',
                          'Stream', 'Varna', 'Deed Name', 'Aspect', 'Jamak Spirit', 'Rank', 'Elemental Affinity', 'Fuel', 'Sect']:
            return 'identity', 'lineage'
        elif stat_title in ['Full Name', 'Concept', 'Date of Birth', 'Date of Chrysalis', 'Date of Awakening',
                          'First Change Date', 'Date of Embrace', 'Date of Possession', 'Nature', 'Demeanor',
                          'Path of Enlightenment', 'Fae Name', 'Tribal Name', 'Occupation']:
            return 'identity', 'personal'
            
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
        self.is_specialty = False
        self.specialty = None
        
        args = self.args.strip()
        if not args:
            return

        # Split into parts before and after =
        if '=' in args:
            first_part, self.value_change = args.split('=', 1)
            first_part = first_part.strip()
            self.value_change = self.value_change.strip()
            
            # Handle special case for stats with colon in their values
            # Check if this might be a stat that allows colons in the value
            special_colon_stats = ['elemental affinity']
            potential_stat_name = first_part.lower()
            
            # If the original stat name is a known special case and the value contains a colon
            if potential_stat_name in special_colon_stats and ':' in self.value_change:
                # Keep the value with the colon as is - don't try to parse it further
                self.stat_name = first_part.strip()
                # Don't modify the value, let the validation handle it
                return
        else:
            first_part = args
            self.value_change = None

        try:
            # Check for specialty syntax first: ability[specialty]
            if '[' in first_part and ']' in first_part:
                ability_part, specialty = first_part.split('[', 1)
                if not specialty.endswith(']'):
                    raise ValueError("Malformed specialty syntax. Use: ability[specialty]")
                specialty = specialty[:-1].strip()  # Remove the closing bracket
                self.stat_name = ability_part.strip()
                self.is_specialty = True
                self.specialty = specialty
                return  # Exit early for specialty handling

            # Handle instance format: stat(instance)/category
            if '(' in first_part and ')' in first_part:
                # Extract stat name and everything after the opening parenthesis
                parts = first_part.split('(', 1)
                self.stat_name = parts[0].strip()
                
                # Extract instance and category
                instance_and_rest = parts[1]
                if ')' not in instance_and_rest:
                    raise ValueError("Malformed instance syntax. Missing closing parenthesis. Use: stat(instance)/category")
                
                # Split at the closing parenthesis
                instance_parts = instance_and_rest.split(')', 1)
                self.instance = instance_parts[0].strip()
                
                # Check if there's a category specified after the instance
                if len(instance_parts) > 1 and '/' in instance_parts[1]:
                    category_part = instance_parts[1].split('/', 1)[1].strip()
                    
                    # Handle explicit category.type notation
                    if '.' in category_part:
                        cat_parts = category_part.split('.', 1)
                        self.category = cat_parts[0].strip()
                        self.stat_type = cat_parts[1].strip()
                    else:
                        # Use the standard mapping for other formats
                        self.map_category_and_type(category_part)
                    
                    # If category mapping failed, exit early
                    if not self.category or not self.stat_type:
                        return
                else:
                    # No category specified, detect based on stat name
                    self.detect_category_and_type()
            else:
                # Handle non-instance format: stat/category
                if '/' in first_part:
                    parts = first_part.split('/', 1)
                    self.stat_name = parts[0].strip()
                    category_part = parts[1].strip()
                    
                    # Handle explicit category.type notation
                    if '.' in category_part:
                        cat_parts = category_part.split('.', 1)
                        self.category = cat_parts[0].strip()
                        self.stat_type = cat_parts[1].strip()
                    else:
                        # Use the standard mapping for other formats
                        self.map_category_and_type(category_part)
                    
                    # If category mapping failed, exit early
                    if not self.category or not self.stat_type:
                        return
                else:
                    self.stat_name = first_part.strip()
                    # No category specified, detect based on stat name
                    self.detect_category_and_type()
                
                # Check if this stat requires an instance
                if self._requires_instance(self.stat_name, self.category):
                    self._display_instance_requirement_message(self.stat_name)
                    self.stat_name = None  # Set to None to indicate parsing failed
                    return
                
                # Special handling for Gnosis
                if self.stat_name.lower() == 'gnosis':
                    splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
                    char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
                    
                    if splat and splat.lower() in ['shifter', 'possessed']:
                        self.category = 'pools'
                        self.stat_type = 'dual'
                    elif splat and splat.lower() == 'mortal+' and char_type and char_type.lower() == 'kinfolk':
                        self.category = 'merits'
                        self.stat_type = 'supernatural'
            
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
                    else:
                        self.category = 'attributes'
                        self.stat_type = 'physical'
            
        except Exception as e:
            self.caller.msg(f"|rError parsing command: {str(e)}|n")
            self.stat_name = None  # Set to None to indicate parsing failed

    def map_category_and_type(self, category_or_type: str):
        """Map user-provided category/type to correct internal values."""
        # Convert to title case for consistent comparison
        stat_title = self.stat_name.title()
        stat_lower = self.stat_name.lower()

        # Special handling for Rank vs Organizational Rank
        if stat_lower == 'rank':
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            if splat and splat.lower() == 'shifter':
                self.category = 'identity'
                self.stat_type = 'lineage'
                return
            # If not a shifter, treat as Organizational Rank background
            self.stat_name = 'Organizational Rank'
            self.category = 'backgrounds'
            self.stat_type = 'background'
            return

        category_or_type = category_or_type.lower()
        
        # Direct category mappings based on STAT_TYPE_TO_CATEGORY structure
        category_map = {
            # Attributes
            'physical': ('attributes', 'physical'),
            'social': ('attributes', 'social'),
            'mental': ('attributes', 'mental'),
            
            # Abilities
            'ability': ('abilities', 'talent'),  # Default to talent, will be adjusted in validation
            'talent': ('abilities', 'talent'),
            'skill': ('abilities', 'skill'),
            'knowledge': ('abilities', 'knowledge'),
            'secondary_talent': ('secondary_abilities', 'secondary_talent'),
            'secondary_skill': ('secondary_abilities', 'secondary_skill'),
            'secondary_knowledge': ('secondary_abilities', 'secondary_knowledge'),
            
            # Identity
            'personal': ('identity', 'personal'),
            'lineage': ('identity', 'lineage'),
            'identity': ('identity', 'identity'),
            'archetype': ('identity', 'personal'),
            
            # Powers
            'discipline': ('powers', 'discipline'),
            'combodiscipline': ('powers', 'combodiscipline'),
            'thaumaturgy': ('powers', 'thaumaturgy'),
            'gift': ('powers', 'gift'),
            'rite': ('powers', 'rite'),
            'sphere': ('powers', 'sphere'),
            'rote': ('powers', 'rote'),
            'art': ('powers', 'art'),
            'realm': ('powers', 'realm'),
            'blessing': ('powers', 'blessing'),
            'charm': ('powers', 'charm'),
            'sorcery': ('powers', 'sorcery'),
            'faith': ('powers', 'faith'),
            'numina': ('powers', 'numina'),
            'hedge_ritual': ('powers', 'hedge_ritual'),
            'special_advantage': ('powers', 'special_advantage'),
            
            # Merits and Flaws
            'physical_merit': ('merits', 'physical'),
            'social_merit': ('merits', 'social'),
            'mental_merit': ('merits', 'mental'),
            'supernatural_merit': ('merits', 'supernatural'),
            'physical_flaw': ('flaws', 'physical'),
            'social_flaw': ('flaws', 'social'),
            'mental_flaw': ('flaws', 'mental'),
            'supernatural_flaw': ('flaws', 'supernatural'),
            
            # Virtues
            'virtue': ('virtues', 'moral'),
            'conscience': ('virtues', 'moral'),
            'conviction': ('virtues', 'moral'),
            'self-control': ('virtues', 'moral'),
            'instinct': ('virtues', 'moral'),
            'courage': ('virtues', 'moral'),
            
            # Backgrounds
            'background': ('backgrounds', 'background'),
            
            # Advantages
            'renown': ('advantages', 'renown'),
            
            # Pools
            'willpower': ('pools', 'dual'),
            'rage': ('pools', 'dual'),
            'gnosis': ('pools', 'dual'),
            'glamour': ('pools', 'dual'),
            'banality': ('pools', 'dual'),
            'blood': ('pools', 'dual'),
            'quintessence': ('pools', 'dual'),
            'paradox': ('pools', 'dual'),
            'essence energy': ('pools', 'dual'),
            'path': ('pools', 'moral'),
            'road': ('pools', 'moral'),
            'arete': ('pools', 'advantage'),
            'enlightenment': ('pools', 'advantage'),
            'resonance': ('pools', 'resonance'),
            'dynamic': ('virtues', 'synergy'),
            'static': ('virtues', 'synergy'),
            'entropic': ('virtues', 'synergy'),
            
            # Common aliases
            'disciplines': ('powers', 'discipline'),
            'gifts': ('powers', 'gift'),
            'spheres': ('powers', 'sphere'),
            'realms': ('powers', 'realm'),
            'arts': ('powers', 'art'),
            'blessings': ('powers', 'blessing'),
            'charms': ('powers', 'charm'),
            'advantages': ('powers', 'special_advantage'),
            'backgrounds': ('backgrounds', 'background'),
            'pools': ('pools', 'dual'),
            'virtues': ('virtues', 'moral'),
            
            # Special cases
            'date of birth': ('identity', 'personal'),
            'date of embrace': ('identity', 'personal'),
            'date of chrysalis': ('identity', 'personal'),
            'date of awakening': ('identity', 'personal'),
            'first change date': ('identity', 'personal'),
            'date of possession': ('identity', 'personal'),
            'occupation': ('identity', 'personal'),
            'patron totem': ('identity', 'lineage'),
            'totem': ('backgrounds', 'background'),
            'possessed wings': ('powers', 'blessing'),
            'companion wings': ('powers', 'special_advantage'),
            'possessed size': ('powers', 'blessing'),
            'companion size': ('powers', 'special_advantage'),
            'spirit type': ('identity', 'lineage'),
            'anchor': ('identity', 'lineage'),
            'essence energy': ('pools', 'dual'),
            'organizational rank': ('backgrounds', 'background'),
            'jamak spirit': ('identity', 'lineage'),
            'fuel': ('identity', 'lineage'),
            'elemental affinity': ('identity', 'lineage'),
            'element': ('identity', 'lineage') #alias for elemental affinity
        }
        
        # Try exact match first
        if category_or_type in category_map:
            self.category, self.stat_type = category_map[category_or_type]
            
            # Validate that the stat belongs in this category
            if not self._validate_stat_in_category(self.stat_name, self.category, self.stat_type):
                # Don't set category/type to None here - let _validate_stat_in_category handle redirection
                return
            return
            
        # Try case-insensitive match
        category_or_type_lower = category_or_type.lower()
        for key, value in category_map.items():
            if key.lower() == category_or_type_lower:
                self.category, self.stat_type = value
                
                # Validate that the stat belongs in this category
                if not self._validate_stat_in_category(self.stat_name, self.category, self.stat_type):
                    # Don't set category/type to None here - let _validate_stat_in_category handle redirection
                    return
                return
                
        # If still not found, set both and let validation handle errors
        if '.' in category_or_type:
            parts = category_or_type.split('.', 1)
            self.category = parts[0]
            self.stat_type = parts[1]
        else:
            self.category = category_or_type
            self.stat_type = category_or_type

    def _validate_stat_in_category(self, stat_name: str, category: str, stat_type: str) -> bool:
        """
        Validate that a stat belongs in the specified category and type.
        
        Args:
            stat_name: The name of the stat to check
            category: The category to check against
            stat_type: The stat type to check against
            
        Returns:
            bool: True if the stat belongs in the category/type, False otherwise
        """
        # Convert to title case for consistent comparison
        stat_title = stat_name.title()
        stat_lower = stat_name.lower()

        # Special handling for Obedience stat
        if stat_lower == 'obedience':
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            if splat == 'Shifter':
                # Get shifter type
                shifter_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
                if shifter_type == 'Ananasi':
                    # For Ananasi, Obedience is a renown stat
                    if category == 'advantages' and stat_type == 'renown':
                        return True
                    self.caller.msg(f"|rFor Ananasi characters, Obedience is a renown stat and cannot be set as a {category}.{stat_type}.|n")
                    self.category = 'advantages'
                    self.stat_type = 'renown'
                    self.caller.msg(f"|yAutomatically redirecting to correct category. Setting 'Obedience' as a advantages.renown instead.|n")
                    return True
                else:
                    # For other shifter types that can use the Gift, allow it as a gift
                    if category == 'powers' and stat_type == 'gift':
                        return True
            return True

        # First check if this stat exists in multiple categories (including the provided one)
        from world.wod20th.models import Stat
        possible_stats = Stat.objects.filter(name__iexact=stat_name)
        
        if possible_stats.count() > 1:
            # Check if the provided category/type is one of the valid ones
            valid_pairs = [(stat.category, stat.stat_type) for stat in possible_stats]
            if (category, stat_type) in valid_pairs:
                return True
        
        # Special handling for Ferocity stat
        if stat_lower == 'ferocity':
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            if splat == 'Shifter':
                # Get shifter type
                shifter_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
                if shifter_type:
                    # Check if this shifter type has access to Ferocity renown
                    valid_renown = SHIFTER_RENOWN.get(shifter_type, [])
                    if 'Ferocity' in valid_renown:
                        if category == 'advantages' and stat_type == 'renown':
                            return True
                        self.caller.msg(f"|rFor {shifter_type} characters, Ferocity is a renown stat and cannot be set as a {category}.{stat_type}.|n")
                        self.category = 'advantages'
                        self.stat_type = 'renown'
                        self.caller.msg(f"|yAutomatically redirecting to correct category. Setting 'Ferocity' as a advantages.renown instead.|n")
                        return True
            elif splat == 'Companion':
                if category == 'powers' and stat_type == 'special_advantage':
                    return True
                self.caller.msg("|rFor Companions, Ferocity is a special advantage and cannot be set as a {category}.{stat_type}.|n")
                self.category = 'powers'
                self.stat_type = 'special_advantage'
                self.caller.msg("|yAutomatically redirecting to correct category. Setting 'Ferocity' as a powers.special_advantage instead.|n")
                return True
            return False

        # Special handling for Arcane stat
        if stat_lower == 'arcane':
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            
            if splat == 'Vampire':
                if category == 'merits' and stat_type == 'social':
                    return True
                self.caller.msg(f"|rFor Vampires, Arcane is a social merit and cannot be set as a {category}.{stat_type}.|n")
                self.category = 'merits'
                self.stat_type = 'social'
                self.caller.msg(f"|yAutomatically redirecting to correct category. Setting '{stat_name}' as a merits.social instead.|n")
                return True
            else:
                if category == 'backgrounds' and stat_type == 'background':
                    return True
                self.caller.msg(f"|rFor non-Vampires, Arcane is a background and cannot be set as a {category}.{stat_type}.|n")
                self.category = 'backgrounds'
                self.stat_type = 'background'
                self.caller.msg(f"|yAutomatically redirecting to correct category. Setting '{stat_name}' as a backgrounds.background instead.|n")
                return True

        # Special handling for Time stat
        if stat_lower == 'time':
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
            
            if splat == 'Mage':
                if category == 'powers' and stat_type == 'sphere':
                    return True
                self.caller.msg(f"|rFor Mages, Time is a Sphere and cannot be set as a {category}.{stat_type}.|n")
                self.category = 'powers'
                self.stat_type = 'sphere'
                self.caller.msg(f"|yAutomatically redirecting to correct category. Setting '{stat_name}' as a powers.sphere instead.|n")
                return True
            elif splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain'):
                if category == 'powers' and stat_type == 'realm':
                    return True
                self.caller.msg(f"|rFor Changelings and Kinain, Time is a Realm and cannot be set as a {category}.{stat_type}.|n")
                self.category = 'powers'
                self.stat_type = 'realm'
                self.caller.msg(f"|yAutomatically redirecting to correct category. Setting '{stat_name}' as a powers.realm instead.|n")
                return True
            else:
                if category == 'attributes' and stat_type == 'physical':
                    return True
                self.caller.msg(f"|rFor other characters, Time is a physical attribute.|n")
                self.category = 'attributes'
                self.stat_type = 'physical'
                self.caller.msg(f"|yAutomatically redirecting to correct category. Setting '{stat_name}' as a attributes.physical instead.|n")
                return True

        # First check the database for an exact match
        from world.wod20th.models import Stat
        stat = Stat.objects.filter(name__iexact=stat_name).first()
        if stat:
            # If we find the stat in the database, check if it matches the specified category/type
            if stat.category == category and stat.stat_type == stat_type:
                return True
            elif stat.category and stat.stat_type:
                # Special handling for Nature - should only be a realm power for Changelings and Kinain
                if stat_name.lower() == 'nature':
                    splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
                    char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
                    
                    # For Changelings and Kinain, Nature is a realm power
                    if (splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain')):
                        if category == 'powers' and stat_type == 'realm':
                            return True
                        elif category == 'identity' and stat_type == 'personal':
                            self.caller.msg(f"|rFor {splat} characters, Nature is a realm power, not an identity stat.|n")
                            self.category = 'powers'
                            self.stat_type = 'realm'
                            self.caller.msg(f"|yAutomatically redirecting to correct category. Setting 'Nature' as a powers.realm instead.|n")
                            return True
                    # For all other character types, Nature is an identity stat
                    else:
                        if category == 'identity' and stat_type == 'personal':
                            return True
                        elif category == 'powers' and stat_type == 'realm':
                            self.caller.msg(f"|rFor {splat} characters, Nature is an identity stat, not a realm power.|n")
                            self.category = 'identity'
                            self.stat_type = 'personal'
                            self.caller.msg(f"|yAutomatically redirecting to correct category. Setting 'Nature' as a identity.personal instead.|n")
                            return True

        # Check specific categories
        if category == 'attributes':
            # Check if it's a valid attribute for the specified type
            for attr_type, attributes in ATTRIBUTE_CATEGORIES.items():
                if stat_title in attributes:
                    if attr_type == stat_type:
                        return True
                    else:
                        self.caller.msg(f"|rAttribute '{stat_name}' belongs in type '{attr_type}', not '{stat_type}'.|n")
                        return False
            self.caller.msg(f"|r'{stat_name}' is not a valid attribute.|n")
            return False
            
        elif category == 'abilities':
            # Check standard abilities
            if stat_type == 'talent' and stat_title in TALENTS:
                return True
            elif stat_type == 'skill' and stat_title in SKILLS:
                return True
            elif stat_type == 'knowledge' and stat_title in KNOWLEDGES:
                return True
            # Check secondary abilities - these should be in secondary_abilities category
            elif stat_type in ['secondary_talent', 'secondary_skill', 'secondary_knowledge']:
                # Redirect to secondary_abilities category
                if stat_type == 'secondary_talent' and stat_title in SECONDARY_TALENTS:
                    self.caller.msg(f"|rSecondary ability '{stat_name}' belongs in category 'secondary_abilities', not 'abilities'.|n")
                    self.category = 'secondary_abilities'
                    self.caller.msg(f"|yAutomatically redirecting to correct category. Setting '{stat_name}' as a secondary_abilities.{stat_type} instead.|n")
                    return True
                elif stat_type == 'secondary_skill' and stat_title in SECONDARY_SKILLS:
                    self.caller.msg(f"|rSecondary ability '{stat_name}' belongs in category 'secondary_abilities', not 'abilities'.|n")
                    self.category = 'secondary_abilities'
                    self.caller.msg(f"|yAutomatically redirecting to correct category. Setting '{stat_name}' as a secondary_abilities.{stat_type} instead.|n")
                    return True
                elif stat_type == 'secondary_knowledge' and stat_title in SECONDARY_KNOWLEDGES:
                    self.caller.msg(f"|rSecondary ability '{stat_name}' belongs in category 'secondary_abilities', not 'abilities'.|n")
                    self.category = 'secondary_abilities'
                    self.caller.msg(f"|yAutomatically redirecting to correct category. Setting '{stat_name}' as a secondary_abilities.{stat_type} instead.|n")
                    return True
                
            # If not found in any ability list, suggest the correct category
            for ability_type, abilities in [('talent', TALENTS), ('skill', SKILLS), ('knowledge', KNOWLEDGES)]:
                if stat_title in abilities:
                    self.caller.msg(f"|rAbility '{stat_name}' belongs in type '{ability_type}', not '{stat_type}'.|n")
                    return False
                    
            # Check if it's a merit or flaw that was mistakenly categorized as an ability
            for merit_type, merits in MERIT_CATEGORIES.items():
                if stat_title in merits:
                    self.caller.msg(f"|r'{stat_name}' is a merit in category 'merits' with type '{merit_type}', not an ability.|n")
                    return False
                    
            for flaw_type, flaws in FLAW_CATEGORIES.items():
                if stat_title in flaws:
                    self.caller.msg(f"|r'{stat_name}' is a flaw in category 'flaws' with type '{flaw_type}', not an ability.|n")
                    return False
                    
            # Check if it's a discipline or other power
            if stat_title in ['Animalism', 'Auspex', 'Celerity', 'Chimerstry', 'Dementation', 
                            'Dominate', 'Fortitude', 'Necromancy', 'Obfuscate', 'Obtenebration', 
                            'Potence', 'Presence', 'Protean', 'Quietus', 'Serpentis', 'Thaumaturgy', 
                            'Vicissitude', 'Temporis', 'Daimoinon', 'Sanguinus', 'Melpominee', 
                            'Mytherceria', 'Obeah', 'Thanatosis', 'Valeren', 'Spiritus']:
                self.caller.msg(f"|r'{stat_name}' is a discipline in category 'powers' with type 'discipline', not an ability.|n")
                return False
                
            self.caller.msg(f"|r'{stat_name}' is not a valid ability.|n")
            return False
            
        elif category == 'virtues':
            # Check if it's a valid virtue
            if stat_type == 'moral' and stat_title in ['Conscience', 'Self-Control', 'Courage', 'Conviction', 'Instinct']:
                return True
            elif stat_type == 'synergy' and stat_title in ['Dynamic', 'Static', 'Entropic']:
                return True
                
            # If not a virtue, check if it's a discipline or other power
            if stat_title in ['Animalism', 'Auspex', 'Celerity', 'Chimerstry', 'Dementation', 
                            'Dominate', 'Fortitude', 'Necromancy', 'Obfuscate', 'Obtenebration', 
                            'Potence', 'Presence', 'Protean', 'Quietus', 'Serpentis', 'Thaumaturgy', 
                            'Vicissitude', 'Temporis', 'Daimoinon', 'Sanguinus', 'Melpominee', 
                            'Mytherceria', 'Obeah', 'Thanatosis', 'Valeren', 'Spiritus']:
                self.caller.msg(f"|r'{stat_name}' is a discipline in category 'powers' with type 'discipline', not a virtue.|n")
                return False
                
            self.caller.msg(f"|r'{stat_name}' is not a valid virtue.|n")
            return False
            
        elif category == 'powers':
            # Check if it's a valid power for the specified type
            if stat_type == 'discipline' and stat_title in ['Animalism', 'Auspex', 'Celerity', 'Chimerstry', 'Dementation', 
                                                         'Dominate', 'Fortitude', 'Necromancy', 'Obfuscate', 'Obtenebration', 
                                                         'Potence', 'Presence', 'Protean', 'Quietus', 'Serpentis', 'Thaumaturgy', 
                                                         'Vicissitude', 'Temporis', 'Daimoinon', 'Sanguinus', 'Melpominee', 
                                                         'Mytherceria', 'Obeah', 'Thanatosis', 'Valeren', 'Spiritus']:
                return True
            elif stat_type == 'thaumaturgy' and stat_title in ['Path of Blood', 'Lure of Flames', 'Movement of the Mind', 
                                                            'Path of Conjuring', 'Path of Corruption', 'Path of Mars', 
                                                            'Hands of Destruction', 'Neptune\'s Might', 'Path of Technomancy', 
                                                            'Path of the Father\'s Vengeance', 'Green Path', 'Elemental Mastery', 
                                                            'Weather Control', 'Gift of Morpheus', 'Oneiromancy', 'Path of Mercury', 
                                                            'Spirit Manipulation', 'Two Centimes Path', 'Path of Transmutation', 
                                                            'Path of Warding', 'Countermagic', 'Thaumaturgical Countermagic']:
                return True
            elif stat_type == 'necromancy' and stat_title in ['Sepulchre Path', 'Bone Path', 'Ash Path', 'Cenotaph Path', 
                                                          'Vitreous Path', 'Mortis Path', 'Grave\'s Decay']:
                return True
            elif stat_type == 'sphere' and stat_title in MAGE_SPHERES:
                return True
            elif stat_type == 'art' and stat_title in ARTS:
                return True
            elif stat_type == 'realm' and stat_title in REALMS:
                return True
            elif stat_type == 'gift':
                # Check if it's a valid gift in the database
                from world.wod20th.models import Stat
                gift = Stat.objects.filter(
                    name__iexact=stat_name,
                    category='powers',
                    stat_type='gift'
                ).first()
                if gift:
                    return True
                    
                # Check if it's a gift alias
                all_gifts = Stat.objects.filter(
                    category='powers',
                    stat_type='gift'
                )
                for g in all_gifts:
                    if g.gift_alias and any(alias.lower() == stat_lower for alias in g.gift_alias):
                        return True
                        
                self.caller.msg(f"|r'{stat_name}' is not a valid gift.|n")
                return False
                
            # If not found in any power list, suggest the correct category
            for power_type in ['discipline', 'thaumaturgy', 'necromancy', 'sphere', 'art', 'realm', 'gift']:
                # Check the database for this power type
                from world.wod20th.models import Stat
                power = Stat.objects.filter(
                    name__iexact=stat_name,
                    category='powers',
                    stat_type=power_type
                ).first()
                if power:
                    self.caller.msg(f"|rPower '{stat_name}' belongs in type '{power_type}', not '{stat_type}'.|n")
                    return False
                    
            self.caller.msg(f"|r'{stat_name}' is not a valid power for type '{stat_type}'.|n")
            return False
            
        elif category == 'merits':
            # Check if it's a valid merit for the specified type
            for merit_type, merits in MERIT_CATEGORIES.items():
                if stat_title in merits:
                    if merit_type == stat_type:
                        return True
                    else:
                        self.caller.msg(f"|rMerit '{stat_name}' belongs in type '{merit_type}', not '{stat_type}'.|n")
                        return False
                        
            self.caller.msg(f"|r'{stat_name}' is not a valid merit.|n")
            return False
            
        elif category == 'flaws':
            # Check if it's a valid flaw for the specified type
            for flaw_type, flaws in FLAW_CATEGORIES.items():
                if stat_title in flaws:
                    if flaw_type == stat_type:
                        return True
                    else:
                        self.caller.msg(f"|rFlaw '{stat_name}' belongs in type '{flaw_type}', not '{stat_type}'.|n")
                        return False
                        
            self.caller.msg(f"|r'{stat_name}' is not a valid flaw.|n")
            return False
            
        elif category == 'backgrounds':
            # Check if it's a valid background
            if stat_type == 'background' and stat_title in (
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
                return True
                
            self.caller.msg(f"|r'{stat_name}' is not a valid background.|n")
            return False
            
        elif category == 'pools':
            # Check if it's a valid pool
            if stat_type == 'dual' and stat_title in POOL_TYPES['dual'].keys():
                return True
            elif stat_type == 'moral' and stat_title in POOL_TYPES['moral'].keys():
                return True
            elif stat_type == 'advantage' and stat_title in POOL_TYPES['advantage'].keys():
                return True
            elif stat_type == 'resonance' and stat_title == 'Resonance':
                return True
                
            self.caller.msg(f"|r'{stat_name}' is not a valid pool for type '{stat_type}'.|n")
            return False
            
        elif category == 'secondary_abilities':
            # Check secondary abilities
            if stat_type == 'secondary_talent' and stat_title in SECONDARY_TALENTS:
                return True
            elif stat_type == 'secondary_skill' and stat_title in SECONDARY_SKILLS:
                return True
            elif stat_type == 'secondary_knowledge' and stat_title in SECONDARY_KNOWLEDGES:
                return True
            
            # If not found in any secondary ability list, suggest the correct category
            for ability_type, abilities in [('secondary_talent', SECONDARY_TALENTS), 
                                          ('secondary_skill', SECONDARY_SKILLS), 
                                          ('secondary_knowledge', SECONDARY_KNOWLEDGES)]:
                if stat_title in abilities:
                    self.caller.msg(f"|rSecondary ability '{stat_name}' belongs in type '{ability_type}', not '{stat_type}'.|n")
                    return False
                    
            # Check if it's a standard ability that was mistakenly categorized as a secondary ability
            for ability_type, abilities in [('talent', TALENTS), ('skill', SKILLS), ('knowledge', KNOWLEDGES)]:
                if stat_title in abilities:
                    self.caller.msg(f"|r'{stat_name}' is a standard ability in category 'abilities' with type '{ability_type}', not a secondary ability.|n")
                    return False
                    
            self.caller.msg(f"|r'{stat_name}' is not a valid secondary ability.|n")
            return False
            
        # For other categories, allow it for now (identity, advantages, etc.)
        return True

    def get_proper_special_advantage_name(self, stat_name: str) -> str:
        """Get the proper case name for a special advantage."""
   
        # Remove "Companion" prefix if present
        clean_name = stat_name.lower().replace('companion ', '')
        
        for advantage_name in SPECIAL_ADVANTAGES.keys():
            if advantage_name.lower() == clean_name:
                return advantage_name
                
        return None

    def detect_ability_category(self, stat_name: str) -> tuple[str, str]:
        """
        Detect the category and type of an ability stat based on its name.
        Returns a tuple of (category, type) or (None, None) if not found.
        """
        # Get the standardized title-case version of the stat name for exact matching
        stat_title = stat_name.title()
        stat_lower = stat_name.lower()

        # Check attributes first
        for category, attributes in ATTRIBUTE_CATEGORIES.items():
            if stat_title in attributes:
                return 'attributes', category

        # Check standard abilities next
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

        # Check virtues since they're specific
        if stat_title in ['Conscience', 'Self-Control', 'Courage', 'Conviction', 'Instinct']:
            return 'virtues', 'moral'

        # Check pools 
        if stat_title in POOL_TYPES['dual'].keys():
            return 'pools', 'dual'
        elif stat_title in ['Dynamic', 'Static', 'Entropic']:
            return 'virtues', 'synergy'
        elif stat_title == 'Resonance':
            return 'pools', 'resonance'
        elif stat_title in POOL_TYPES['moral'].keys():
            return 'pools', 'moral'
        elif stat_title in POOL_TYPES['advantage'].keys():
            return 'pools', 'advantage'

        # Check backgrounds
        if stat_title in (UNIVERSAL_BACKGROUNDS + VAMPIRE_BACKGROUNDS + CHANGELING_BACKGROUNDS + 
                         MAGE_BACKGROUNDS + TECHNOCRACY_BACKGROUNDS + TRADITIONS_BACKGROUNDS + 
                         NEPHANDI_BACKGROUNDS + SHIFTER_BACKGROUNDS + SORCERER_BACKGROUNDS):
            # Special handling for Rank vs Organizational Rank
            if stat_title.lower() == 'rank':
                splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
                if splat and splat.lower() == 'shifter':
                    return 'identity', 'lineage'
                self.stat_name = 'Organizational Rank'
            return 'backgrounds', 'background'

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

        # Now get character's splat and type for the rest of the checks
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
        char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
        
        # Special handling for Obedience which could be both a gift and a renown type
        if stat_name.lower() == 'obedience':
            # For Ananasi, prioritize renown over gift
            if char_type == 'Ananasi':
                return 'advantages', 'renown'

        # Check if character can use gifts
        can_use_gifts = (
            splat == 'Shifter' or 
            splat == 'Possessed' or 
            (splat == 'Mortal+' and char_type == 'Kinfolk')
        )

        # Check if this is a gift in the database
        if can_use_gifts:
            from world.wod20th.models import Stat
            gift = Stat.objects.filter(
                name__iexact=stat_name,
                category='powers',
                stat_type='gift'
            ).first()
            
            if not gift:
                # Try to find it by alias
                all_gifts = Stat.objects.filter(
                    category='powers',
                    stat_type='gift'
                )
                for g in all_gifts:
                    if g.gift_alias and any(alias.lower() == stat_name.lower() for alias in g.gift_alias):
                        gift = g
                        break

        # Check if it's a sliver for Inanimae
        if stat_title in {'Verdage', 'Aquis', 'Stratus', 'Petros', 'Pyros', 'Sliver'}:
            kith = self.caller.get_stat('identity', 'lineage', 'Kith', temp=False)
            if kith and kith.lower() == 'inanimae':
                return 'powers', 'sliver'

        # Check if it's a special advantage for Companions
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
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
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
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
                    if not hasattr(self, 'alias_used'):
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
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
        if splat and splat.lower() == 'vampire':
            # Get the stat definition from the database
            from world.wod20th.utils.vampire_utils import get_clan_disciplines
            
            # Check if it's a base discipline
            if stat_title in ['Animalism', 'Auspex', 'Celerity', 'Chimerstry', 'Dementation', 
                            'Dominate', 'Fortitude', 'Necromancy', 'Obfuscate', 'Obtenebration', 
                            'Potence', 'Presence', 'Protean', 'Quietus', 'Serpentis', 'Thaumaturgy', 
                            'Vicissitude', 'Temporis', 'Daimoinon', 'Sanguinus', 'Melpominee', 
                            'Mytherceria', 'Obeah', 'Thanatosis', 'Valeren', 'Spiritus']:
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
                splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
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

    def func(self):
        """Execute the command."""
        if not self.args:
            self.caller.msg("|rUsage: +selfstat <stat>[(<instance>)]/[<category>]=[+-]<value>|n")
            return

        if not self.stat_name:
            self.caller.msg("|rUsage: +selfstat <stat>[(<instance>)]/[<category>]=[+-]<value>|n")
            return

        # Check if character is approved
        if self.caller.db.approved:
            self.caller.msg("|rError: Approved characters cannot use chargen commands. Please contact staff for any needed changes.|n")
            return

        # Fix any incorrectly stored Necromancy paths
        self._fix_necromancy_paths()

        # Fix incorrectly stored Ferocity for Shifters
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
        shifter_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
        if splat == 'Shifter' and shifter_type:
            valid_renown = SHIFTER_RENOWN.get(shifter_type, [])
            if 'Ferocity' in valid_renown:
                # Check if Ferocity is incorrectly stored in powers.special_advantage
                if ('powers' in self.caller.db.stats and 
                    'special_advantage' in self.caller.db.stats['powers'] and 
                    'Ferocity' in self.caller.db.stats['powers']['special_advantage']):
                    # Get the value
                    ferocity_value = self.caller.db.stats['powers']['special_advantage']['Ferocity']['perm']
                    # Move it to advantages.renown
                    if 'advantages' not in self.caller.db.stats:
                        self.caller.db.stats['advantages'] = {}
                    if 'renown' not in self.caller.db.stats['advantages']:
                        self.caller.db.stats['advantages']['renown'] = {}
                    self.caller.db.stats['advantages']['renown']['Ferocity'] = {
                        'perm': ferocity_value,
                        'temp': ferocity_value
                    }
                    # Remove from powers.special_advantage
                    del self.caller.db.stats['powers']['special_advantage']['Ferocity']
                    self.caller.msg("|yFixed: Moved Ferocity from powers.special_advantage to advantages.renown.|n")

        # Check if this stat requires an instance
        if self._requires_instance(self.stat_name, self.category) and not self.instance:
            self._display_instance_requirement_message(self.stat_name)
            return

        # Normalize the stat name case before proceeding
        self.stat_name = self._get_canonical_stat_name(self.stat_name)

        # Get character's splat type and character type 
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
        char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)

        # If no category/type specified, try to determine it from the stat name
        if not self.category or not self.stat_type:
            # Check secondary abilities first - these are high priority matches
            if self.stat_name in SECONDARY_TALENTS:
                self.category = 'abilities'
                self.stat_type = 'secondary_talent'
            elif self.stat_name in SECONDARY_SKILLS:
                self.category = 'abilities'
                self.stat_type = 'secondary_skill'
            elif self.stat_name in SECONDARY_KNOWLEDGES:
                self.category = 'abilities'
                self.stat_type = 'secondary_knowledge'
            else:
                # try identity stats
                self.category, self.stat_type = self._detect_identity_category(self.stat_name)
                
                # If not an identity stat, try abilities and other categories
                if not self.category or not self.stat_type:
                    self.category, self.stat_type = self.detect_ability_category(self.stat_name)

        # Always check for multiple categories that match the stat name
        from world.wod20th.models import Stat
        
        # First try exact case-insensitive match
        possible_matches = Stat.objects.filter(name__iexact=self.stat_name)
        
        # If no exact matches, try partial matches
        if not possible_matches.exists():
            possible_matches = Stat.objects.filter(name__icontains=self.stat_name)

        # Handle multiple matches
        if possible_matches.count() > 1:
            # If we have a category/type, filter by those
            if self.category and self.stat_type:
                possible_matches = possible_matches.filter(
                    category=self.category,
                    stat_type=self.stat_type
                )
            
            # If still multiple matches after filtering
            if possible_matches.count() > 1:
                stat_options = [f"{s.name}/{s.stat_type}" for s in possible_matches]
                options_str = ", or ".join([", ".join(stat_options[:-1]), stat_options[-1]] if len(stat_options) > 2 else stat_options)
                self.caller.msg(f"|rMultiple versions of this stat exist. Did you mean {options_str}?|n")
                return
            elif possible_matches.count() == 0:
                self.caller.msg(f"|rNo stat '{self.stat_name}' found with category '{self.category}'.|n")
                return

        # Get the single match if we have one
        stat = possible_matches.first() if possible_matches.exists() else None

        # Fix any incorrectly stored Ferocity for Shifters
        if splat == 'Shifter' and char_type:
            valid_renown = SHIFTER_RENOWN.get(char_type, [])
            if 'Ferocity' in valid_renown:
                # Check if Ferocity is incorrectly stored in powers.special_advantage
                if ('powers' in self.caller.db.stats and 
                    'special_advantage' in self.caller.db.stats['powers'] and 
                    'Ferocity' in self.caller.db.stats['powers']['special_advantage']):
                    # Get the value
                    ferocity_value = self.caller.db.stats['powers']['special_advantage']['Ferocity']['perm']
                    # Move it to advantages.renown
                    if 'advantages' not in self.caller.db.stats:
                        self.caller.db.stats['advantages'] = {}
                    if 'renown' not in self.caller.db.stats['advantages']:
                        self.caller.db.stats['advantages']['renown'] = {}
                    self.caller.db.stats['advantages']['renown']['Ferocity'] = {
                        'perm': ferocity_value,
                        'temp': ferocity_value
                    }
                    # Remove from powers.special_advantage
                    del self.caller.db.stats['powers']['special_advantage']['Ferocity']
                    self.caller.msg("|yFixed: Moved Ferocity from powers.special_advantage to advantages.renown.|n")

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
            self.initialize_stats(self.value_change.title())
            return

        # Special handling for type setting
        if self.stat_name.lower() in ['type', 'possessed type', 'mortal+ type']:
            # Check if this is a Mortal+ type
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
                
        # Special handling for Elemental Affinity
        elif self.stat_name.lower() == 'elemental affinity':
            # For companions, validate elemental affinity
            if splat and splat.lower() == 'companion':
                from world.wod20th.utils.companion_utils import validate_elemental_affinity
                is_valid, error_msg, proper_value = validate_elemental_affinity(self.value_change)
                if not is_valid:
                    self.caller.msg(f"|r{error_msg}|n")
                    return
                if proper_value:
                    self.value_change = proper_value
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
        if self.stat_name.lower() in ['traditions subfaction', 'methodology', 'nephandi faction']:
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
                elif self.affiliation == 'Nephandi':
                    is_valid, matched_value = self.case_insensitive_in(self.value_change, NEPHANDI_FACTION)
                    if not is_valid:
                        self.caller.msg(f"|rInvalid Nephandi faction. Valid factions are: {', '.join(sorted(NEPHANDI_FACTION))}|n")
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

        # When setting Changeling-specific stats
        elif self.stat_name.lower() in ['kith', 'seeming', 'seelie legacy', 'unseelie legacy', 'fae name', 'phyla']:
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

                elif self.stat_name.lower() == 'phyla':
                    kith = self.caller.get_stat('identity', 'lineage', 'Kith', temp=False)
                    if kith and kith.lower() == 'inanimae':
                        is_valid, matched_value = self.case_insensitive_in(self.value_change, PHYLA)
                        if not is_valid:
                            self.caller.msg(f"|rInvalid phyla. Valid phyla are: {', '.join(sorted(PHYLA))}|n")
                            return
                        self.value_change = matched_value
                        return ('identity', 'lineage')
                    else:
                        self.caller.msg("|rOnly Inanimae can set their Phyla.|n")
                        return

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
                elif self.stat_name.lower() == 'fae court':
                    is_valid, matched_value = self.case_insensitive_in(self.value_change, UNSEELIE_LEGACIES)
                    if not is_valid:
                        self.caller.msg(f"|rInvalid Fae Court. Valid courts are: {', '.join(sorted(FAE_COURTS))}|n")
                        return
                    self.value_change = matched_value
                    return ('identity', 'lineage')
                elif self.stat_name.lower() == 'house':
                    is_valid, matched_value = self.case_insensitive_in(self.value_change, HOUSES)
                    if not is_valid:
                        self.caller.msg(f"|rInvalid House. Valid houses are: {', '.join(sorted(HOUSES))}|n")
                        return
                    self.value_change = matched_value
                    self.category = 'identity'
                    self.stat_type = 'lineage'
                    self.caller.set_stat('identity', 'lineage', 'House', matched_value, temp=False)
                    self.caller.set_stat('identity', 'lineage', 'House', matched_value, temp=True)
                    self.caller.msg(f"|gSet House to {matched_value}.|n")
                    return

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
        elif self.stat_name.lower() in ['breed', 'auspice', 'tribe', 'aspect', 'rank']:
            splat = self.caller.get_stat('identity', 'personal', 'Splat', temp=False)
            shifter_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
            
            if splat and splat.lower() == 'shifter' and shifter_type:
                # Handle Rank
                if self.stat_name.lower() == 'rank':
                    try:
                        rank_value = int(self.value_change)
                        if rank_value < 0 or rank_value > 5:
                            self.caller.msg("|rRank must be between 0 and 5.|n")
                            return
                        self.value_change = rank_value
                        return ('identity', 'lineage')
                    except ValueError:
                        self.caller.msg("|rRank must be a number.|n")
                        return
                # Breed validation
                if self.stat_name.lower() == 'breed':
                    is_valid, matched_value, error_msg = self._validate_breed(shifter_type, self.value_change)
                    if not is_valid:
                        self.caller.msg(error_msg)
                        return
                    self.value_change = matched_value
                    # Set the breed first
                    self.caller.set_stat('identity', 'lineage', 'Breed', matched_value, temp=False)
                    self.caller.set_stat('identity', 'lineage', 'Breed', matched_value, temp=True)
                    # Then update pools based on breed
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

        # Special handling for Kinfolk Breed
        elif self.stat_name.lower() == 'kinfolk breed':
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            # Get character type directly from stats dictionary
            char_type = None
            if ('identity' in self.caller.db.stats and 
                'lineage' in self.caller.db.stats['identity'] and 
                'Type' in self.caller.db.stats['identity']['lineage']):
                char_type = self.caller.db.stats['identity']['lineage']['Type'].get('perm')
            
            if splat and splat.lower() == 'mortal+' and char_type == 'Kinfolk':
                # Get valid breed types from KINFOLK_BREED_CHOICES
                valid_breeds = [breed[1] for breed in KINFOLK_BREED_CHOICES]
                is_valid, matched_value = self.case_insensitive_in(self.value_change, set(valid_breeds))
                if not is_valid:
                    self.caller.msg(f"|rInvalid Kinfolk breed. Valid breeds are: {', '.join(sorted(valid_breeds))}|n")
                    return
                
                self.value_change = matched_value
                # Set the breed in identity/lineage
                self.caller.set_stat('identity', 'lineage', 'Kinfolk Breed', matched_value, temp=False)
                self.caller.set_stat('identity', 'lineage', 'Kinfolk Breed', matched_value, temp=True)
                self.caller.msg(f"|gSet Kinfolk Breed to {matched_value}.|n")
                return ('identity', 'lineage')
            else:
                # Add debug information
                self.caller.msg(f"|rOnly Mortal+ Kinfolk characters can set Kinfolk Breed. Current splat: {splat}, Type: {char_type}|n")
                return

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
        elif self.stat_name.lower() in [adv.lower() for adv in SPECIAL_ADVANTAGES.keys()] or self.stat_name.lower() in [adv.lower() for adv in COMBAT_SPECIAL_ADVANTAGES.keys()]:
            splat = self.caller.get_stat('identity', 'personal', 'Splat', temp=False)
            companion_type = self.caller.get_stat('identity', 'lineage', 'Companion Type', temp=False)
            
            if splat and splat.lower() == 'companion' and companion_type:
                # Check if this advantage requires an instance
                proper_name = next((name for name in SPECIAL_ADVANTAGES.keys() if name.lower() == self.stat_name.lower()),
                                  next((name for name in COMBAT_SPECIAL_ADVANTAGES.keys() if name.lower() == self.stat_name.lower()), None))
                if not proper_name:
                    self.caller.msg(f"|rInvalid special advantage: {self.stat_name}|n")
                    return
                
                # Check if this advantage requires an instance
                if self._requires_instance(proper_name):
                    if not self.instance:
                        self.caller.msg(f"|rThe special advantage '{proper_name}' requires an instance. Use format: {proper_name}(instance)/special_advantage=value|n")
                        self.caller.msg(f"|yFor example: {proper_name}(poison)/special_advantage=5|n")
                        self.caller.msg(f"|yUsage: +selfstat <stat>[(<instance>)]/[<category>]=[+-]<value>|n")
                        return
                    # When we have an instance, use it as part of the stat name
                    proper_name = f"{proper_name}({self.instance})"
                
                # Get the advantage info - this is now a lowercase key
                advantage_key = next((key for key in SPECIAL_ADVANTAGES.keys() if key.lower() == self.stat_name.lower()), 
                                   next((key for key in COMBAT_SPECIAL_ADVANTAGES.keys() if key.lower() == self.stat_name.lower()), None))
                if not advantage_key:
                    self.caller.msg(f"|rInvalid special advantage key: {self.stat_name}|n")
                    return
                    
                advantage_info = SPECIAL_ADVANTAGES.get(advantage_key, COMBAT_SPECIAL_ADVANTAGES.get(advantage_key))
                if not advantage_info:
                    self.caller.msg(f"|rNo information found for {proper_name}|n")
                    return
                
                try:
                    value = int(self.value_change)
                    if value not in advantage_info['valid_values']:
                        valid_values_str = ', '.join(map(str, advantage_info['valid_values']))
                        self.caller.msg(f"|rInvalid value for {proper_name}. Valid values are: {valid_values_str}|n")
                        return
                    
                    # Set the proper name for storage
                    self.stat_name = proper_name
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
            
            # Try partial name matching for ambiguous stat names
            partial_matches = Stat.objects.filter(name__icontains=self.stat_name)
            if partial_matches.exists():
                # Build a list of possible stats
                valid_categories = []
                for stat in partial_matches:
                    valid_categories.append((stat.category, stat.stat_type, stat.name))
                
                # Create header with dashes
                header = f" Multiple matches found for '{self.stat_name}' "
                total_width = 78
                dash_count = (total_width - len(header)) // 2
                self.caller.msg("\n" + "|b-|n" * dash_count + header + "|b-|n" * (total_width - len(header) - dash_count))
                
                # Column headers
                self.caller.msg("|wNumber    Category          Type              Stat Name|n")
                self.caller.msg("|b" + "-" * total_width + "|n")
                
                # Sort categories for consistent display
                sorted_categories = sorted(valid_categories)
                
                # Show each valid category with example usage
                for i, (cat, type_, name) in enumerate(sorted_categories, 1):
                    example = f"{name}"
                    # Format each column to specific widths
                    self.caller.msg(f"|w{i:<9}|n {cat:<18}{type_:<18}{example}")

                self.caller.msg(f"\n|rPlease specify a complete stat name or provide more specific search criteria.|n")
                return
            
            self.caller.msg(f"|rStat '{self.stat_name}' not found.|n")
            return
            
        # Handle instances for background stats
        if self._should_support_instance(self.stat_name, stat.category):
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
            if stat and stat.stat_type == 'background':
                # Check splat-specific background restrictions
                is_restricted, required_splat, error_msg = self.get_background_splat_restriction(self.stat_name)
                if is_restricted and splat != required_splat:
                    self.caller.msg(error_msg)
                    return
            # Get the canonical name for the stat
            canonical_name = self._get_canonical_stat_name(self.stat_name)
            
            # Try to find and remove the stat using the canonical name
            if self.category and canonical_name in self.caller.db.stats.get(self.category, {}).get(self.stat_type, {}):
                del self.caller.db.stats[self.category][self.stat_type][canonical_name]
                self.caller.msg(f"Removed stat '{canonical_name}'.")
                return
            
            # If not found with explicit category/type, try to find it in all categories
            for category in self.caller.db.stats:
                for stat_type in self.caller.db.stats[category]:
                    if canonical_name in self.caller.db.stats[category][stat_type]:
                        del self.caller.db.stats[category][stat_type][canonical_name]
                        self.caller.msg(f"Removed stat '{canonical_name}'.")
                        return
            
            # If we get here, the stat wasn't found
            self.caller.msg(f"Stat '{canonical_name}' not found.")
            
            # Special handling for special advantages during removal
            if 'powers' in self.caller.db.stats and 'special_advantage' in self.caller.db.stats['powers']:
                # Case-insensitive search for special advantages, using full_stat_name to include instances
                search_name = full_stat_name.lower()
                for advantage_name in list(self.caller.db.stats['powers']['special_advantage'].keys()):
                    if advantage_name.lower() == search_name:
                        del self.caller.db.stats['powers']['special_advantage'][advantage_name]
                        self.caller.msg(f"|gRemoved special advantage '{advantage_name}'.|n")
                        return
                    # Also check without instance if we have one
                    elif self.instance and self.stat_name.lower() == advantage_name.lower():
                        del self.caller.db.stats['powers']['special_advantage'][advantage_name]
                        self.caller.msg(f"|gRemoved special advantage '{advantage_name}'.|n")
                        return
                    # Additionally, check if the advantage with instance matches just the base name
                    # This allows +selfstat Immunity= to remove Immunity(fire)
                    elif '(' in advantage_name and ')' in advantage_name:
                        base_name = advantage_name.split('(')[0].lower()
                        if base_name == self.stat_name.lower():
                            del self.caller.db.stats['powers']['special_advantage'][advantage_name]
                            self.caller.msg(f"|gRemoved special advantage '{advantage_name}'.|n")
                            return

            # Regular stat removal handling
            if stat and stat.category in self.caller.db.stats:
                # Special handling for secondary abilities
                if stat.category == 'secondary_abilities':
                    if stat.stat_type in self.caller.db.stats['secondary_abilities']:
                        if full_stat_name in self.caller.db.stats['secondary_abilities'][stat.stat_type]:
                            del self.caller.db.stats['secondary_abilities'][stat.stat_type][full_stat_name]
                            self.caller.msg(f"|gRemoved stat '{full_stat_name}'.|n")
                            # Update any dependent stats after removal
                            self._update_dependent_stats(full_stat_name, None)
                            return
                # Handle regular stats
                elif stat.stat_type in self.caller.db.stats[stat.category]:
                    if full_stat_name in self.caller.db.stats[stat.category][stat.stat_type]:
                        # If this is a gift, remove its alias
                        if stat.category == 'powers' and stat.stat_type == 'gift':
                            # Remove the alias using the new method
                            if self.caller.remove_gift_alias(full_stat_name):
                                self.caller.msg(f"|yRemoved alias for gift '{full_stat_name}'|n")
                        
                        del self.caller.db.stats[stat.category][stat.stat_type][full_stat_name]
                        self.caller.msg(f"|gRemoved stat '{full_stat_name}'.|n")
                        # Update any dependent stats after removal
                        self._update_dependent_stats(full_stat_name, None)
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
                
            is_valid, error_message, corrected_value = self.validate_stat_value(self.stat_name, self.value_change, self.category, self.stat_type)
            if not is_valid:
                self.caller.msg(f"|r{error_message}|n")
                return
            
            # Update the value to the corrected value if provided
            if corrected_value is not None:
                self.value_change = corrected_value

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

            # Special handling for Gnosis (can be both merit and pool)
            if self.stat_name.lower() == 'gnosis':
                try:
                    value_int = int(self.value_change)
                    # Get character's splat and type
                    char_splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
                    char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
                    
                    # For Shifters and Possessed, handle Gnosis as a pool
                    if char_splat and char_splat.lower() in ['shifter', 'possessed']:
                        if value_int < 0 or value_int > 10:
                            self.caller.msg("|rGnosis pool must be between 0 and 10.|n")
                            return
                        # Set explicit category and type to avoid any fallback to merit logic
                        self.category = 'pools'
                        self.stat_type = 'dual'
                        
                        # Set the pool value directly
                        self.caller.set_stat('pools', 'dual', 'Gnosis', value_int, temp=False)
                        self.caller.set_stat('pools', 'dual', 'Gnosis', value_int, temp=True)
                        
                        # Log the change and return immediately to prevent further processing
                        self.caller.msg(f"|gSet Gnosis pool to {value_int} for {char_splat}.|n")
                        # This return is critical - it stops any further processing that might categorize Gnosis as a merit
                        return
                    
                    # For Kinfolk, handle Gnosis as a merit
                    elif char_splat and char_splat.lower() == 'mortal+' and char_type and char_type.lower() == 'kinfolk':
                        if value_int not in [5, 6, 7]:
                            self.caller.msg("|rKinfolk can only take Gnosis as a merit (values 5-7).|n")
                            return
                        self.category = 'merits'
                        self.stat_type = 'supernatural'
                        # Calculate and set Gnosis pool (Merit rating - 4 = Gnosis pool)
                        gnosis_pool = value_int - 4
                        # Set the merit first
                        self.caller.set_stat('merits', 'supernatural', 'Gnosis', value_int, temp=False)
                        self.caller.set_stat('merits', 'supernatural', 'Gnosis', value_int, temp=True)
                        # Then set the pool
                        self.caller.set_stat('pools', 'dual', 'Gnosis', gnosis_pool, temp=False)
                        self.caller.set_stat('pools', 'dual', 'Gnosis', gnosis_pool, temp=True)
                        self.caller.msg(f"|gSet Gnosis merit to {value_int} and Gnosis pool to {gnosis_pool}.|n")
                        return
                    
                    # For other splats, don't allow setting Gnosis
                    else:
                        self.caller.msg("|rOnly Shifters, Possessed, and Kinfolk characters can have Gnosis.|n")
                        return
                except ValueError:
                    self.caller.msg("|rGnosis value must be a number.|n")
                    return

            # Special handling for other pool stats
            elif self.stat_name.lower() in ['willpower', 'rage', 'glamour', 'banality', 'essence energy']:
                try:
                    pool_value = int(self.value_change)
                    if pool_value < 0 or pool_value > 10:
                        self.caller.msg(f"|r{self.stat_name} pool must be between 0 and 10.|n")
                        return
                    self.category = 'pools'
                    self.stat_type = 'dual'
                    new_value = pool_value
                except ValueError:
                    self.caller.msg(f"|r{self.stat_name} pool must be a number.|n")
                    return
            # Special handling for Blood, Quintessence, and Paradox
            elif self.stat_name.lower() in ['blood', 'quintessence', 'paradox']:
                try:
                    pool_value = int(self.value_change)
                    if pool_value < 0 or pool_value > 20:
                        self.caller.msg(f"|r{self.stat_name} pool must be between 0 and 20.|n")
                        return
                    self.category = 'pools'
                    self.stat_type = 'dual'
                    new_value = pool_value
                except ValueError:
                    self.caller.msg(f"|r{self.stat_name} pool must be a number.|n")
                    return
            # Special handling for resonance pools
            elif self.stat_name.lower() in ['dynamic', 'static', 'entropic']:
                try:
                    pool_value = int(self.value_change)
                    if pool_value < 0 or pool_value > 5:  # Changed from 10 to 5 since these are virtues
                        self.caller.msg(f"|r{self.stat_name} virtue must be between 0 and 5.|n")
                        return
                    self.category = 'virtues'  # Changed from 'advantage' to 'virtues'
                    self.stat_type = 'synergy'  # Changed from 'resonance' to 'synergy'
                    new_value = pool_value
                except ValueError:
                    self.caller.msg(f"|r{self.stat_name} virtue must be a number.|n")
                    return

            # Special handling for advantage pools
            elif self.stat_name.lower() in ['arete']:
                try:
                    pool_value = int(self.value_change)
                    if pool_value < 0 or pool_value > 10:
                        self.caller.msg(f"|r{self.stat_name} pool must be between 0 and 10.|n")
                        return
                    self.category = 'pools'
                    self.stat_type = 'advantage'
                    new_value = pool_value
                except ValueError:
                    self.caller.msg(f"|r{self.stat_name} pool must be a number.|n")
                    return

        except (ValueError, TypeError) as e:
            self.caller.msg(f"|rError converting value: {str(e)}|n")
            return

        # Set the stat using set_stat method
        self.set_stat(self.stat_name, new_value, self.category, self.stat_type)

        # Update dependent stats for Mages specifically for backgrounds
        if splat == 'Mage' and self.category == 'backgrounds' and self.stat_type == 'background':
            from world.wod20th.utils.mage_utils import update_mage_pools_on_stat_change
            update_mage_pools_on_stat_change(self.caller, self.stat_name, new_value)

    def initialize_stats(self, splat):
        """Initialize the basic stats structure based on splat type."""
        # Clear gift_aliases when changing splat
        if hasattr(self.caller.db, 'gift_aliases'):
            self.caller.db.gift_aliases = {}
            
        # Clear specialties when changing splat
        if hasattr(self.caller.db, 'specialties'):
            self.caller.db.specialties = {}
            
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
            'talent': {}
        }
        
        # Initialize secondary abilities as a separate top-level category
        base_stats['secondary_abilities'] = {
            'secondary_knowledge': {},
            'secondary_talent': {},
            'secondary_skill': {}
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
        
        # Initialize hedge_ritual
        if 'hedge_ritual' not in base_stats['powers']:
            base_stats['powers']['hedge_ritual'] = {}
        
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

        # Set base attributes to 1 directly in the attributes structure
        for category in ['physical', 'social', 'mental']:
            for attribute in ATTRIBUTE_CATEGORIES[category]:
                base_stats['attributes'][category][attribute] = {'perm': 1, 'temp': 1}

        # Initialize splat-specific stats
        if splat_lower == 'vampire':
            initialize_vampire_stats(self.caller, '')
            # Set default Banality for Vampires
            self.caller.db.stats['pools']['dual']['Banality'] = {'perm': 5, 'temp': 5}
        elif splat_lower == 'mage':
            initialize_mage_stats(self.caller, '')
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
        elif splat_lower == 'mortal':
            # Initialize virtues for mortals
            if 'virtues' not in self.caller.db.stats:
                self.caller.db.stats['virtues'] = {'moral': {}}
            if 'moral' not in self.caller.db.stats['virtues']:
                self.caller.db.stats['virtues']['moral'] = {}
            
            # Set default virtues to 1
            for virtue in ['Conscience', 'Self-Control', 'Courage']:
                self.caller.db.stats['virtues']['moral'][virtue] = {'perm': 1, 'temp': 1}
            
            # Initialize pools
            if 'pools' not in self.caller.db.stats:
                self.caller.db.stats['pools'] = {'dual': {}, 'moral': {}}
            if 'dual' not in self.caller.db.stats['pools']:
                self.caller.db.stats['pools']['dual'] = {}
            if 'moral' not in self.caller.db.stats['pools']:
                self.caller.db.stats['pools']['moral'] = {}
            
            # Set Willpower equal to Courage
            self.caller.db.stats['pools']['dual']['Willpower'] = {'perm': 1, 'temp': 1}
            
            # Set default Banality
            self.caller.db.stats['pools']['dual']['Banality'] = {'perm': 6, 'temp': 6}
            
            # Initialize identity structure for Path of Enlightenment
            if 'identity' not in self.caller.db.stats:
                self.caller.db.stats['identity'] = {'personal': {}, 'lineage': {}}
            if 'personal' not in self.caller.db.stats['identity']:
                self.caller.db.stats['identity']['personal'] = {}
                
            # Set Path of Enlightenment to Humanity
            self.caller.db.stats['identity']['personal']['Path of Enlightenment'] = {'perm': 'Humanity', 'temp': 'Humanity'}
            
            # Calculate initial Path rating using virtue_utils
            from world.wod20th.utils.virtue_utils import calculate_path
            path_rating = calculate_path(self.caller)
            
            # Set initial Path rating
            self.caller.db.stats['pools']['moral']['Path'] = {'perm': path_rating, 'temp': path_rating}
            
            # Get virtue values for feedback message
            conscience = self.caller.db.stats['virtues']['moral']['Conscience']['perm']
            self_control = self.caller.db.stats['virtues']['moral']['Self-Control']['perm']
            self.caller.msg(f"|gInitialized Mortal character with Humanity (Path rating: {path_rating} = Conscience {conscience} + Self-Control {self_control}).|n")

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
            
        # Special handling for secondary abilities
        if category == 'secondary_abilities':
            if 'secondary_abilities' not in self.caller.db.stats:
                self.caller.db.stats['secondary_abilities'] = {}
            if stat_type not in self.caller.db.stats['secondary_abilities']:
                self.caller.db.stats['secondary_abilities'][stat_type] = {}
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
        """Set a stat value."""
        # Capitalize the stat name properly
        if stat_name:
            # Special handling for multi-word stats
            if '(' in stat_name:
                # Handle stats with instances
                base_name, instance = stat_name.split('(', 1)
                # Special handling for 'of' in base name
                words = base_name.split()
                capitalized_words = []
                for word in words:
                    if word.lower() == 'of':
                        capitalized_words.append('of')
                    else:
                        # Custom capitalization to handle apostrophes
                        if "'" in word:
                            # Split by apostrophe, capitalize first part, keep rest lowercase
                            parts = word.split("'", 1)
                            capitalized_words.append(parts[0].capitalize() + "'" + parts[1].lower())
                        else:
                            capitalized_words.append(word.capitalize())
                stat_name = ' '.join(capitalized_words) + '(' + instance
            else:
                # Regular stats - capitalize each word except 'of'
                words = stat_name.split()
                capitalized_words = []
                for word in words:
                    if word.lower() == 'of':
                        capitalized_words.append('of')
                    else:
                        # Custom capitalization to handle apostrophes
                        if "'" in word:
                            # Split by apostrophe, capitalize first part, keep rest lowercase
                            parts = word.split("'", 1)
                            capitalized_words.append(parts[0].capitalize() + "'" + parts[1].lower())
                        else:
                            capitalized_words.append(word.capitalize())
                stat_name = ' '.join(capitalized_words)

        # Get character's splat
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)

        # If category or stat_type is None, try to detect them
        if not category or not stat_type:
            detected = self.detect_ability_category(stat_name)
            if detected and detected[0] and detected[1]:
                category, stat_type = detected
                self.caller.msg(f"|yAutodetected category '{category}' and type '{stat_type}' for {stat_name}.|n")
            else:
                # Try to find possible categories for this stat in the database
                from world.wod20th.models import Stat
                possible_stats = Stat.objects.filter(name__iexact=stat_name)
                
                if possible_stats.exists():
                    # Build a list of possible categories
                    valid_categories = []
                    for stat in possible_stats:
                        valid_categories.append((stat.category, stat.stat_type))
                    
                    # Special case for psychic abilities
                    if stat_name.lower() in ['telepathy', 'clairvoyance', 'medium', 'precognition', 'psychometry', 'psychokinesis']:
                        if ('powers', 'numina') not in valid_categories:
                            valid_categories.append(('powers', 'numina'))
                        if ('powers', 'special_advantage') not in valid_categories:
                            valid_categories.append(('powers', 'special_advantage'))
                    
                    # If we found multiple valid categories and no specific category/type provided
                    # or if the provided category/type isn't in the valid ones
                    if len(valid_categories) > 1 and ((not category or not stat_type) or (category, stat_type) not in valid_categories):
                        # Create header with dashes
                        header = f" Multiple categories found for '{stat_name}' "
                        total_width = 78
                        dash_count = (total_width - len(header)) // 2
                        self.caller.msg("\n" + "|b-|n" * dash_count + header + "|b-|n" * (total_width - len(header) - dash_count))
                        
                        # Column headers
                        self.caller.msg("|w#    Category    Type           Example Usage|n")
                        self.caller.msg("|b" + "-" * total_width + "|n")
                        
                        # Sort categories for consistent display
                        sorted_categories = sorted(valid_categories)
                        
                        # Show each valid category with example usage
                        for i, (cat, type_) in enumerate(sorted_categories, 1):
                            example = f"+selfstat {stat_name}/{cat}.{type_}="
                            # Format each column to specific widths
                            self.caller.msg(f"|w{i:<5}|n {cat:<10}{type_:<14}{example}")

                        # Format all categories as a string for the error message too
                        categories_str = ', '.join([f"{cat}.{type_}" for cat, type_ in valid_categories])
                        self.caller.msg(f"\n|rPlease specify which category to use for '{stat_name}'.|n")
                        return
                    else:
                        # Format the error message with available categories
                        categories_str = ', '.join([f"{cat}.{type_}" for cat, type_ in valid_categories])
                        self.caller.msg(f"|rError: '{stat_name}' exists in the following categories: {categories_str}. Please set this stat using the following syntax: +selfstat {stat_name}/<category>=<value>|n")
                else:
                    self.caller.msg(f"|rError: Could not determine where to store stat '{stat_name}'.|n")
                return

        # Validate that the stat belongs in the specified category
        # Note: _validate_stat_in_category may update self.category and self.stat_type
        if not self._validate_stat_in_category(stat_name, category, stat_type):
            return
        
        # Use the potentially updated category and stat_type
        category = self.category
        stat_type = self.stat_type

        # Check for stats with the same name in other categories (cleanup)
        categories_to_check = ['attributes', 'abilities', 'identity', 'powers', 'merits', 
                             'flaws', 'virtues', 'backgrounds', 'advantages', 'pools']
        
        found_duplicates = []
        
        # Only look for duplicates within the SAME category but different types
        if category in self.caller.db.stats:
            for type_key, type_dict in self.caller.db.stats[category].items():
                if type_key != stat_type and stat_name in type_dict:
                    found_duplicates.append((category, type_key))
        
        # If we found duplicates within the same category, warn the user and remove them
        if found_duplicates:
            for cat, type_key in found_duplicates:
                self.caller.msg(f"|rFound duplicate stat '{stat_name}' in {cat}.{type_key} - removing.|n")
                del self.caller.db.stats[cat][type_key][stat_name]
        
        # We no longer check for or remove duplicates across different categories
        # This allows the same stat name to exist in different categories
        # which is needed for stats like "ward" that can legitimately exist in multiple categories

        # If this is a stat with an instance, combine them for storage
        if self.instance and self._should_support_instance(stat_name, category):
            stat_name = f"{stat_name}({self.instance})"

        # Special handling for virtues
        if stat_name.title() in ['Conscience', 'Self-Control', 'Courage', 'Conviction', 'Instinct']:
            try:
                virtue_value = int(value)
                if virtue_value < 1 or virtue_value > 5:
                    self.caller.msg(f"|r{stat_name} must be between 1 and 5.|n")
                    return

                # Initialize virtues structure if needed
                if 'virtues' not in self.caller.db.stats:
                    self.caller.db.stats['virtues'] = {'moral': {}}
                if 'moral' not in self.caller.db.stats['virtues']:
                    self.caller.db.stats['virtues']['moral'] = {}

                # Store the virtue value
                self.caller.db.stats['virtues']['moral'][stat_name.title()] = {
                    'perm': virtue_value,
                    'temp': virtue_value
                }

                # Update Path rating for vampires when virtues change
                if stat_name.title() in ['Conscience', 'Self-Control', 'Conviction', 'Instinct'] and splat == 'Vampire':
                    from world.wod20th.utils.virtue_utils import calculate_path
                    path_rating = calculate_path(self.caller)
                    if 'pools' not in self.caller.db.stats:
                        self.caller.db.stats['pools'] = {'moral': {}}
                    if 'moral' not in self.caller.db.stats['pools']:
                        self.caller.db.stats['pools']['moral'] = {}
                    self.caller.db.stats['pools']['moral']['Path'] = {
                        'perm': path_rating,
                        'temp': path_rating
                    }
                    self.caller.msg(f"|gCalculated new Path rating: {path_rating}|n")

                # Update Willpower when Courage changes
                if stat_name.title() == 'Courage':
                    if splat and splat.lower() in ['vampire', 'mortal', 'mortal+']:
                        if 'pools' not in self.caller.db.stats:
                            self.caller.db.stats['pools'] = {'dual': {}}
                        if 'dual' not in self.caller.db.stats['pools']:
                            self.caller.db.stats['pools']['dual'] = {}
                        self.caller.db.stats['pools']['dual']['Willpower'] = {
                            'perm': virtue_value,
                            'temp': virtue_value
                        }
                        self.caller.msg(f"|gWillpower set to match Courage: {virtue_value}|n")

                self.caller.msg(f"|gSet {stat_name} to {virtue_value}.|n")
                return
            except ValueError:
                self.caller.msg("|rVirtue value must be a number.|n")
                return

        # Set the stat using the caller's set_stat method
        self.caller.set_stat(category, stat_type, stat_name, value, temp=False)
        self.caller.set_stat(category, stat_type, stat_name, value, temp=True)
        
        # Update pools based on splat type
        if splat == 'Shifter':
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

        # Special handling for merits
        if stat_name.title() in MERIT_VALUES:
            # Skip merit validation if we've already determined this is a blessing for Possessed
            if not (splat == 'Possessed' and category == 'powers' and stat_type == 'blessing'):
                # Get character's splat type if needed for restriction checks
                char_type = None
                if splat == 'Shifter':
                    char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
                elif splat == 'Mortal+':
                    char_type = self.caller.get_stat('identity', 'lineage', 'MortalPlus Type', temp=False)
                elif splat == 'Companion':
                    char_type = self.caller.get_stat('identity', 'lineage', 'Companion Type', temp=False)
                elif splat == 'Possessed':
                    char_type = self.caller.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
                
                try:
                    merit_value = int(value)
                    valid_values = MERIT_VALUES[stat_name.title()]
                    if merit_value not in valid_values:
                        self.caller.msg(f"|rInvalid value for merit {stat_name}. Valid values are: {', '.join(map(str, valid_values))}|n")
                        return

                    # Check splat restrictions
                    if stat_name.title() in MERIT_SPLAT_RESTRICTIONS:
                        restriction = MERIT_SPLAT_RESTRICTIONS[stat_name.title()]
                        if restriction['splat']:
                            allowed_splats = restriction['splat'] if isinstance(restriction['splat'], list) else [restriction['splat']]
                            if splat.lower() not in [s.lower() for s in allowed_splats]:
                                self.caller.msg(f"|rThe merit '{stat_name}' is only available to {', '.join(allowed_splats)} characters.|n")
                                return
                        if restriction['splat_type'] and char_type and restriction['splat_type'].lower() != char_type.lower():
                            self.caller.msg(f"|rThe merit '{stat_name}' is only available to {restriction['splat_type']} characters.|n")
                            return

                    # Find the merit type and store the merit
                    for merit_type, merits in MERIT_CATEGORIES.items():
                        if stat_name.title() in merits:
                            if 'merits' not in self.caller.db.stats:
                                self.caller.db.stats['merits'] = {}
                            if merit_type not in self.caller.db.stats['merits']:
                                self.caller.db.stats['merits'][merit_type] = {}
                            self.caller.db.stats['merits'][merit_type][stat_name.title()] = {
                                'perm': merit_value,
                                'temp': merit_value
                            }
                            self.caller.msg(f"|gSet merit {stat_name} to {merit_value}.|n")
                            return
                except ValueError:
                    self.caller.msg(f"|rMerit value must be a number.|n")
                    return

        # Special handling for flaws
        if stat_name.title() in FLAW_VALUES:
            # Skip flaw validation if we've already determined this is a specific type
            if not ((splat == 'Possessed' and category == 'powers' and stat_type == 'curse') or
                    (splat == 'Shifter' and category == 'flaws' and stat_type == 'spiritual')):
                
                # Get character's splat type if needed for restriction checks
                char_type = None
                if splat == 'Shifter':
                    char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
                elif splat == 'Mortal+':
                    char_type = self.caller.get_stat('identity', 'lineage', 'MortalPlus Type', temp=False)
                elif splat == 'Companion':
                    char_type = self.caller.get_stat('identity', 'lineage', 'Companion Type', temp=False)
                elif splat == 'Possessed':
                    char_type = self.caller.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
                    
                # Only validate flaw values if this is actually being set as a flaw
                if category == 'flaws':
                    try:
                        flaw_value = int(value)
                        valid_values = FLAW_VALUES[stat_name.title()]
                        
                        if flaw_value not in valid_values:
                            self.caller.msg(f"|rInvalid value for flaw {stat_name}. Valid values are: {', '.join(map(str, valid_values))}|n")
                            return
                    except ValueError:
                        self.caller.msg(f"|rInvalid value for flaw {stat_name}. Valid values are: {', '.join(map(str, FLAW_VALUES[stat_name.title()]))}|n")
                        return

                    # Check splat restrictions
                    if stat_name.title() in FLAW_SPLAT_RESTRICTIONS:
                        restriction = FLAW_SPLAT_RESTRICTIONS[stat_name.title()]
                        if restriction['splat']:
                            allowed_splats = restriction['splat'] if isinstance(restriction['splat'], list) else [restriction['splat']]
                            if splat.lower() not in [s.lower() for s in allowed_splats]:
                                self.caller.msg(f"|rThe flaw '{stat_name}' is only available to {', '.join(allowed_splats)} characters.|n")
                                return
                        if restriction['splat_type'] and char_type and restriction['splat_type'].lower() != char_type.lower():
                            self.caller.msg(f"|rThe flaw '{stat_name}' is only available to {restriction['splat_type']} characters.|n")
                            return

                    # Find the flaw type and store the flaw
                    for flaw_type, flaws in FLAW_CATEGORIES.items():
                        if stat_name.title() in flaws:
                            if 'flaws' not in self.caller.db.stats:
                                self.caller.db.stats['flaws'] = {}
                            if flaw_type not in self.caller.db.stats['flaws']:
                                self.caller.db.stats['flaws'][flaw_type] = {}
                            self.caller.db.stats['flaws'][flaw_type][stat_name.title()] = {
                                'perm': flaw_value,
                                'temp': flaw_value
                            }
                            self.caller.msg(f"|gSet flaw {stat_name} to {flaw_value}.|n")
                            return

        # Special handling for identity stats
        if category == 'identity':
            if 'identity' not in self.caller.db.stats:
                self.caller.db.stats['identity'] = {}
            if stat_type not in self.caller.db.stats['identity']:
                self.caller.db.stats['identity'][stat_type] = {}
            self.caller.db.stats['identity'][stat_type][stat_name] = {
                'perm': value,
                'temp': value
            }

        # Special handling for pools
        if category == 'pools':
            if 'pools' not in self.caller.db.stats:
                self.caller.db.stats['pools'] = {}
            if stat_type not in self.caller.db.stats['pools']:
                self.caller.db.stats['pools'][stat_type] = {}
            try:
                pool_value = int(value)
                self.caller.db.stats['pools'][stat_type][stat_name] = {
                    'perm': pool_value,
                    'temp': pool_value
                }
                self.caller.msg(f"|gSet {stat_name} pool to {pool_value}.|n")
                return
            except ValueError:
                self.caller.msg(f"|r{stat_name} pool value must be a number.|n")
                return

        # Special handling for gifts to store the alias used
        if category == 'powers' and stat_type == 'gift' and hasattr(self, 'alias_used'):
            # Initialize powers.gift if needed
            if 'powers' not in self.caller.db.stats:
                self.caller.db.stats['powers'] = {}
            if 'gift' not in self.caller.db.stats['powers']:
                self.caller.db.stats['powers']['gift'] = {}
            
            # Store the gift with its value
            try:
                gift_value = int(value)
                self.caller.db.stats['powers']['gift'][stat_name] = {
                    'perm': gift_value,
                    'temp': gift_value
                }
                
                # Store the alias using the new method
                self.caller.set_gift_alias(stat_name, self.alias_used, gift_value)
                
                self.caller.msg(f"|gSet gift {stat_name} to {gift_value}.|n")
            except ValueError:
                self.caller.msg("|rGift value must be a number.|n")
            return

        # Handle all other stats normally
        try:
            # Ensure category and stat_type are strings before proceeding
            if not isinstance(category, str) or not isinstance(stat_type, str):
                self.caller.msg(f"|rError: Invalid category or stat_type. Category: {category}, Type: {stat_type}|n")
                return
                
            # Initialize the stat structure if needed
            self._initialize_stat_structure(category, stat_type)

            # For secondary abilities, ensure proper structure
            if category == 'secondary_abilities' and stat_type in ['secondary_talent', 'secondary_skill', 'secondary_knowledge']:
                # Initialize secondary_abilities if needed
                if 'secondary_abilities' not in self.caller.db.stats:
                    self.caller.db.stats['secondary_abilities'] = {}
                # Initialize the specific secondary ability type if needed
                if stat_type not in self.caller.db.stats['secondary_abilities']:
                    self.caller.db.stats['secondary_abilities'][stat_type] = {}
                
                # Store the secondary ability
                self.caller.db.stats['secondary_abilities'][stat_type][stat_name] = {
                    'perm': value,
                    'temp': value
                }
                # Update category for feedback message
                category = 'secondary_abilities'
            elif category == 'abilities' and stat_type in ['secondary_talent', 'secondary_skill', 'secondary_knowledge']:
                # Handle case where category is incorrectly set to 'abilities' but stat_type indicates a secondary ability
                # Redirect to secondary_abilities category
                if 'secondary_abilities' not in self.caller.db.stats:
                    self.caller.db.stats['secondary_abilities'] = {}
                if stat_type not in self.caller.db.stats['secondary_abilities']:
                    self.caller.db.stats['secondary_abilities'][stat_type] = {}
                
                # Store the secondary ability in the correct location
                self.caller.db.stats['secondary_abilities'][stat_type][stat_name] = {
                    'perm': value,
                    'temp': value
                }
                # Update category for feedback message
                category = 'secondary_abilities'
            else:
                # Regular stat storage
                self.caller.db.stats[category][stat_type][stat_name] = {
                    'perm': value,
                    'temp': value
                }
            
            # Store gift alias if this is a gift
            if category == 'powers' and stat_type == 'gift':
                # Get the canonical name (in this case, stat_name is the canonical name)
                canonical_name = stat_name
                # Get the alias (the original input from the user, without the value part)
                alias = self.args.split('=')[0].split('/')[0].strip()
                # Store the alias mapping
                self.caller.set_gift_alias(canonical_name, alias, value)
                # Success message for gifts
                self.caller.msg(f"|gSet {alias} to {value}.|n")
        except Exception as e:
            self.caller.msg(f"|rError processing stat value: {str(e)}|n")
            return

        # Special handling for gifts to store the alias used
        if category == 'powers' and stat_type == 'gift' and hasattr(self, 'alias_used'):
            # Store the alias using the new method
            self.caller.set_gift_alias(stat_name, self.alias_used, value)

        # Provide feedback with category information
        self.caller.msg(f"|gSet {stat_name} to {value} as a {category}.{stat_type}.|n")

        # Update Path rating when virtues change for Mortals
        if splat == 'Mortal' and category == 'virtues' and stat_type == 'moral' and stat_name.title() in ['Conscience', 'Self-Control']:
            # Store the virtue value first
            if 'virtues' not in self.caller.db.stats:
                self.caller.db.stats['virtues'] = {'moral': {}}
            if 'moral' not in self.caller.db.stats['virtues']:
                self.caller.db.stats['virtues']['moral'] = {}
            self.caller.db.stats['virtues']['moral'][stat_name.title()] = {'perm': value, 'temp': value}
            
            # Ensure Path of Enlightenment is set to Humanity
            if 'identity' not in self.caller.db.stats:
                self.caller.db.stats['identity'] = {'personal': {}, 'lineage': {}}
            if 'personal' not in self.caller.db.stats['identity']:
                self.caller.db.stats['identity']['personal'] = {}
            self.caller.db.stats['identity']['personal']['Path of Enlightenment'] = {'perm': 'Humanity', 'temp': 'Humanity'}
            
            # Calculate new path rating using virtue_utils
            path_rating = calculate_path(self.caller)
            
            # Ensure pools structure exists
            if 'pools' not in self.caller.db.stats:
                self.caller.db.stats['pools'] = {'dual': {}, 'moral': {}}
            if 'moral' not in self.caller.db.stats['pools']:
                self.caller.db.stats['pools']['moral'] = {}
                
            # Update path rating
            self.caller.db.stats['pools']['moral']['Path'] = {'perm': path_rating, 'temp': path_rating}
            
            # Get current virtue values for feedback message
            conscience = self.caller.db.stats.get('virtues', {}).get('moral', {}).get('Conscience', {}).get('perm', 0)
            self_control = self.caller.db.stats.get('virtues', {}).get('moral', {}).get('Self-Control', {}).get('perm', 0)
            self.caller.msg(f"|gPath rating recalculated to {path_rating} (Conscience {conscience} + Self-Control {self_control}).|n")

        # Special handling for gifts to store the alias used
        if category == 'powers' and stat_type == 'gift' and hasattr(self, 'alias_used'):
            # Store the alias using the new method
            self.caller.set_gift_alias(stat_name, self.alias_used, value)

        # Update pools based on splat type
        if splat == 'Shifter':
            from world.wod20th.utils.shifter_utils import update_shifter_pools_on_stat_change
            update_shifter_pools_on_stat_change(self.caller, stat_name, value)

    def detect_category_and_type(self):
        """Detect the category and type of a stat based on its name."""
        # First check if it's a background
        if self.stat_name.lower() in [bg.lower() for bg in (UNIVERSAL_BACKGROUNDS + 
                                                           VAMPIRE_BACKGROUNDS + 
                                                           CHANGELING_BACKGROUNDS + 
                                                           MAGE_BACKGROUNDS + 
                                                           TECHNOCRACY_BACKGROUNDS + 
                                                           TRADITIONS_BACKGROUNDS + 
                                                           NEPHANDI_BACKGROUNDS + 
                                                           SHIFTER_BACKGROUNDS + 
                                                           SORCERER_BACKGROUNDS)]:
            self.category = 'backgrounds'
            self.stat_type = 'background'
            return

        # Check if it's an identity stat
        if self.stat_name.lower() in [stat.lower() for stat in IDENTITY_PERSONAL]:
            self.category = 'identity'
            self.stat_type = 'personal'
            return
        elif self.stat_name.lower() in [stat.lower() for stat in IDENTITY_LINEAGE]:
            self.category = 'identity'
            self.stat_type = 'lineage'
            return

        # Handle 'element' alias for elemental affinity
        if self.stat_name.lower() == 'element':
            self.stat_name = 'Elemental Affinity'
            self.category = 'identity'
            self.stat_type = 'lineage'
            return

            
        # Special handling for Nature - should only be a realm power for Changelings and Kinain
        if self.stat_name.lower() == 'nature':
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
            
            # For Changelings and Kinain, Nature is a realm power
            if (splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain')):
                self.category = 'powers'
                self.stat_type = 'realm'
            # For all other character types, Nature is an identity stat
            else:
                self.category = 'identity'
                self.stat_type = 'personal'
            return
            
        # Check for secondary abilities with case-insensitive comparison
        stat_lower = self.stat_name.lower()
        for talent in SECONDARY_TALENTS:
            if talent.lower() == stat_lower:
                self.category = 'secondary_abilities'
                self.stat_type = 'secondary_talent'
                # Update stat_name to use proper case from constant
                self.stat_name = talent
                return
        for skill in SECONDARY_SKILLS:
            if skill.lower() == stat_lower:
                self.category = 'secondary_abilities'
                self.stat_type = 'secondary_skill'
                # Update stat_name to use proper case from constant
                self.stat_name = skill
                return
        for knowledge in SECONDARY_KNOWLEDGES:
            if knowledge.lower() == stat_lower:
                self.category = 'secondary_abilities'
                self.stat_type = 'secondary_knowledge'
                # Update stat_name to use proper case from constant
                self.stat_name = knowledge
                return

        # Check if it's a merit
        if self.stat_name.lower() in [m.lower() for m in MERIT_VALUES.keys()]:
            self.category = 'merits'
            # Try to detect merit type
            for merit_type, merits in MERIT_CATEGORIES.items():
                if self.stat_name.lower() in [m.lower() for m in merits]:
                    self.stat_type = merit_type
                    break
            # If type not found, default to physical
            if not self.stat_type:
                self.stat_type = 'physical'
                
        # Check if it's a secondary ability
        elif self.stat_name.lower() in [talent.lower() for talent in SECONDARY_TALENTS]:
            self.category = 'secondary_abilities'
            self.stat_type = 'secondary_talent'
        elif self.stat_name.lower() in [skill.lower() for skill in SECONDARY_SKILLS]:
            self.category = 'secondary_abilities'
            self.stat_type = 'secondary_skill'
        elif self.stat_name.lower() in [knowledge.lower() for knowledge in SECONDARY_KNOWLEDGES]:
            self.category = 'secondary_abilities'
            self.stat_type = 'secondary_knowledge'
                
        # Check if it's a flaw
        elif self.stat_name.lower() in [f.lower() for f in FLAW_VALUES.keys()]:
            self.category = 'flaws'
            # Try to detect flaw type
            for flaw_type, flaws in FLAW_CATEGORIES.items():
                if self.stat_name.lower() in [f.lower() for f in flaws]:
                    self.stat_type = flaw_type
                    break
            # If type not found, default to physical
            if not self.stat_type:
                self.stat_type = 'physical'

        # Check if it's a background
        elif self.stat_name.lower() in [bg.lower() for bg in (UNIVERSAL_BACKGROUNDS + 
                                                           VAMPIRE_BACKGROUNDS + 
                                                           CHANGELING_BACKGROUNDS + 
                                                           MAGE_BACKGROUNDS + 
                                                           TECHNOCRACY_BACKGROUNDS + 
                                                           TRADITIONS_BACKGROUNDS + 
                                                           NEPHANDI_BACKGROUNDS + 
                                                           SHIFTER_BACKGROUNDS + 
                                                           SORCERER_BACKGROUNDS)]:
            self.category = 'backgrounds'
            self.stat_type = 'background'
            
        # If still not found, try to detect using the more comprehensive method
        elif not self.category or not self.stat_type:
            category_type_tuple = self.detect_ability_category(self.stat_name)
            if category_type_tuple:
                self.category, self.stat_type = category_type_tuple

    def _requires_instance(self, stat_name: str, category: str = None) -> bool:
        """
        Check if a stat MUST have an instance.
        """
        # Handle None or empty values
        if not stat_name:
            return False
            
        # Stats in REQUIRED_INSTANCES must have instances (case-insensitive)
        if any(stat_name.lower() == required.lower() for required in REQUIRED_INSTANCES):
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

    def _get_canonical_stat_name(self, stat_name: str) -> str:
        """
        Get the canonical (proper case) version of a stat name.
        
        Args:
            stat_name: The stat name to normalize
            
        Returns:
            The canonical stat name with proper case, or the original if no match found
        """
        # Handle None or empty values
        if not stat_name:
            return ""
            
        from world.wod20th.models import Stat
        
        # First try exact case-insensitive match
        stat = Stat.objects.filter(name__iexact=stat_name).first()
        if stat:
            return stat.name
            
        # Try special case mappings (like those in CmdPump)
        STAT_CASES = {
            'primal-urge': 'Primal-Urge',
            'animal ken': 'Animal Ken',
            'privacy obsession': 'Privacy Obsession',
            'resources': 'Resources',
            'professional certification': 'Professional Certification',
            'strength': 'Strength',
            'dexterity': 'Dexterity',
            'stamina': 'Stamina',
            'charisma': 'Charisma',
            'manipulation': 'Manipulation',
            'appearance': 'Appearance',
            'intelligence': 'Intelligence',
            'wits': 'Wits',
            'perception': 'Perception',
            'athletics': 'Athletics',
            'brawl': 'Brawl',
            'dodge': 'Dodge',
            'intimidation': 'Intimidation',
            'leadership': 'Leadership',
            'streetwise': 'Streetwise',
            'subterfuge': 'Subterfuge',
            'crafts': 'Crafts',
            'drive': 'Drive',
            'etiquette': 'Etiquette',
            'firearms': 'Firearms',
            'melee': 'Melee',
            'performance': 'Performance',
            'security': 'Security',
            'stealth': 'Stealth',
            'survival': 'Survival',
            'academics': 'Academics',
            'computer': 'Computer',
            'enigmas': 'Enigmas',
            'investigation': 'Investigation',
            'law': 'Law',
            'medicine': 'Medicine',
            'occult': 'Occult',
            'politics': 'Politics',
            'rituals': 'Rituals',
            'science': 'Science',
            'technology': 'Technology',
            'rage': 'Rage',
            'gnosis': 'Gnosis',
            'willpower': 'Willpower',
            'path of enlightenment': 'Path of Enlightenment',
            'organizational rank': 'Organizational Rank',
            'date of birth': 'Date of Birth',
            'date of embrace': 'Date of Embrace',
            'date of chrysalis': 'Date of Chrysalis',
            'date of awakening': 'Date of Awakening',
            'first change date': 'First Change Date',
            'date of possession': 'Date of Possession'
        }
        if stat_name.lower() in STAT_CASES:
            return STAT_CASES[stat_name.lower()]
            
        # For compound words (e.g., "Animal Ken"), preserve existing case
        if ' ' in stat_name:
            return ' '.join(word.capitalize() for word in stat_name.split())
            
        # Default to simple title case
        return stat_name.title()

    def _validate_path(self, path_name: str) -> tuple[bool, str, str]:
        """
        Validate a Path of Enlightenment name.
        
        Args:
            path_name: The name of the path to validate
            
        Returns:
            tuple: (is_valid, proper_path_name, error_message)
        """
        from world.wod20th.utils.vampire_utils import validate_vampire_path
        is_valid, result = validate_vampire_path(path_name)
        if is_valid:
            return True, result, ""  # result contains the proper path name
        return False, "", result  # result contains the error message