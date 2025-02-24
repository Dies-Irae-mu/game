"""
Utility functions for handling Companion-specific character initialization and updates.
"""
from world.wod20th.utils.banality import get_default_banality
from world.wod20th.models import Stat
from typing import Dict, List, Set, Tuple
from world.wod20th.utils.stat_mappings import SPECIAL_ADVANTAGES

# Valid companion types
COMPANION_TYPE_CHOICES: List[Tuple[str, str]] = [
    ('alien', 'Alien'),
    ('animal', 'Animal'),
    ('bygone', 'Bygone'),
    ('construct', 'Construct'),
    ('familiar', 'Familiar'),
    ('object', 'Object'),
    ('reanimate', 'Reanimate'),
    ('robot', 'Robot'),
    ('spirit', 'Spirit'),
    ('none', 'None')
]

# Keep the set for easy lookups
COMPANION_TYPES: Set[str] = {t[1] for t in COMPANION_TYPE_CHOICES if t[1] != 'None'}

COMPANION_POWERS = {
    'special_advantage': [],
    'charm': [
        'Airt Sense', 'Appear', 'Blast', 'Blighted Touch', 'Brand',
        'Break Reality', 'Calcify', 'Call for Aid', 'Cleanse the Blight',
        'Cling', 'Control Electrical Systems', 'Corruption', 'Create Fire',
        'Create Wind', 'Death Fertility', 'Digital Disruption', 'Disable',
        'Disorient', 'Dream Journey', 'Ease Pain', 'Element Sense',
        'Feedback', 'Flee', 'Flood', 'Freeze', 'Healing', 'Illuminate',
        'Influence', 'Inhabit', 'Insight', 'Iron Will', 'Lightning Bolt',
        'Materialize', 'Meld', 'Mind Speech', 'Open Moon Bridge', 'Peek',
        'Possession', 'Quake', 'Re-form', 'Shapeshift', 'Short Out',
        'Shatter Glass', 'Solidify Reality', 'Spirit Away', 'Spirit Static',
        'Swift Flight', 'System Havoc', 'Terror', 'Track', 'Umbral Storm',
        'Umbraquake', 'Updraft', 'Waves'
    ]
}

def initialize_companion_stats(character, companion_type):
    """Initialize specific stats for a Companion character."""
    """Initialize specific stats for a mage character."""
    # Initialize basic stats structure
    if 'identity' not in character.db.stats:
        character.db.stats['identity'] = {}
    if 'personal' not in character.db.stats['identity']:
        character.db.stats['identity']['personal'] = {}
    if 'lineage' not in character.db.stats['identity']:
        character.db.stats['identity']['lineage'] = {}
    
    # Initialize pools structure
    if 'pools' not in character.db.stats:
        character.db.stats['pools'] = {}
    if 'dual' not in character.db.stats['pools']:
        character.db.stats['pools']['dual'] = {}
    if 'other' not in character.db.stats['pools']:
        character.db.stats['pools']['other'] = {}
    
    # Initialize powers category if it doesn't exist
    if 'powers' not in character.db.stats:
        character.db.stats['powers'] = {}
    
    # Set default Banality based on companion type
    banality = get_default_banality('Companion', subtype=companion_type)
    if banality:
        character.db.stats['pools']['dual']['Banality'] = {'perm': banality, 'temp': banality}
        character.msg(f"|gBanality set to {banality} (permanent).")
    
    # Initialize base pools
    initialize_base_pools(character, companion_type)
    
    # Initialize type-specific stats
    if companion_type == 'Spirit':
        initialize_ferocity_companion_stats(character)
    elif companion_type == 'Bygone':
        initialize_bygone_companion_stats(character)
    elif companion_type == 'Familiar':
        initialize_familiar_companion_stats(character)
    else:
        initialize_standard_companion_stats(character)

def initialize_base_pools(character, companion_type=None):
    """Initialize base pools for all companions."""
    # Initialize pools structure if needed
    if 'pools' not in character.db.stats:
        character.db.stats['pools'] = {}
    if 'dual' not in character.db.stats['pools']:
        character.db.stats['pools']['dual'] = {}

    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
    
    # Initialize Rage pool to 0
    character.db.stats['pools']['dual']['Rage'] = {'perm': 0, 'temp': 0}
    
    # Initialize Special Advantages category
    if 'special_advantage' not in character.db.stats['powers']:
        character.db.stats['powers']['special_advantage'] = {}
    
    # Initialize all special advantages from SPECIAL_ADVANTAGES dictionary
    for advantage_name in SPECIAL_ADVANTAGES.keys():
        if advantage_name not in character.db.stats['powers']['special_advantage']:
            character.db.stats['powers']['special_advantage'][advantage_name] = {'perm': 0, 'temp': 0}
                
    # Initialize Charms category
    if 'charm' not in character.db.stats['powers']:
        character.db.stats['powers']['charm'] = {}

def initialize_ferocity_companion_stats(character):
    """Initialize Ferocity-specific companion stats."""
    # Add Rage pool if character has Ferocity
    special_advantages = character.db.stats.get('powers', {}).get('special_advantage', {})
    has_ferocity = any(name.lower() == 'ferocity' and values.get('perm', 0) > 0 
                      for name, values in special_advantages.items())
    if has_ferocity:
        character.set_stat('pools', 'dual', 'Rage', 1, temp=False)
        character.set_stat('pools', 'dual', 'Rage', 1, temp=True)

def initialize_bygone_companion_stats(character):
    """Initialize Bygone-specific companion stats."""
    # Add Paradox pool if character has Feast of Nettles
    special_advantages = character.db.stats.get('powers', {}).get('special_advantage', {})
    has_feast_of_nettles = any(name.lower() == 'feast of nettles' and values.get('perm', 0) > 0 
                              for name, values in special_advantages.items())
    if has_feast_of_nettles:
        character.set_stat('pools', 'dual', 'Paradox', 1, temp=False)
        character.set_stat('pools', 'dual', 'Paradox', 1, temp=True)

def initialize_familiar_companion_stats(character):
    """Initialize Familiar-specific companion stats."""
    # Set base Essence Energy
    character.set_stat('pools', 'dual', 'Essence Energy', 10, temp=False)
    character.set_stat('pools', 'dual', 'Essence Energy', 10, temp=True)

def initialize_standard_companion_stats(character):
    """Initialize stats for standard companions."""
    # Standard companions just use the base initialization
    pass 

def validate_companion_advantage(character, advantage_name: str, value: int) -> Tuple[bool, str]:
    """
    Validate a special advantage for a companion.
    Returns (is_valid, error_message)
    """
    # Get the advantage info from SPECIAL_ADVANTAGES
    advantage_info = SPECIAL_ADVANTAGES.get(advantage_name.lower())
    if not advantage_info:
        return False, f"'{advantage_name}' is not a valid special advantage"
    
    # Validate value against valid_values
    if value not in advantage_info['valid_values']:
        valid_values_str = ', '.join(map(str, advantage_info['valid_values']))
        return False, f"Invalid value for {advantage_name}. Valid values are: {valid_values_str}"
    
    return True, ""

def update_rage_from_ferocity(character):
    """Update Rage pool based on current Ferocity value."""
    
    # Initialize pools structure if needed
    if 'pools' not in character.db.stats:
        character.db.stats['pools'] = {}
    if 'dual' not in character.db.stats['pools']:
        character.db.stats['pools']['dual'] = {}
    if 'Rage' not in character.db.stats['pools']['dual']:
        character.db.stats['pools']['dual']['Rage'] = {'perm': 0, 'temp': 0}

    ferocity_value = character.db.stats.get('powers', {}).get('special_advantage', {}).get('Ferocity', {}).get('perm', 0)
    
    if ferocity_value > 0:
        rage_value = min(5, ferocity_value // 2)
        character.db.stats['pools']['dual']['Rage'] = {'perm': rage_value, 'temp': rage_value}

def validate_companion_stats(character, stat_name: str, value: str, category: str = None, stat_type: str = None) -> tuple[bool, str, str]:
    """
    Validate companion-specific stats.
    Returns (is_valid, error_message, proper_case_name)
    """
    stat_name = stat_name.lower()
    
    # Get companion type and splat
    companion_type = character.get_stat('identity', 'lineage', 'Companion Type', temp=False)
    splat = character.get_stat('other', 'splat', 'Splat', temp=False)
    
    # Validate type
    if stat_name == 'companion type':
        is_valid, error_msg = validate_companion_type(value)
        return is_valid, error_msg, None
        
    # Special handling for Ferocity based on splat
    if stat_name == 'ferocity':
        if splat == 'Shifter':
            # For Shifters, Ferocity is a Renown type
            try:
                ferocity_value = int(value)
                if ferocity_value < 0 or ferocity_value > 10:
                    return False, "Ferocity renown must be between 0 and 10", None
                return True, "", "Ferocity"
            except ValueError:
                return False, "Ferocity renown value must be a number", None
        else:
            # For Companions, Ferocity is a special advantage
            # Find proper case name from SPECIAL_ADVANTAGES
            proper_name = next((name for name in SPECIAL_ADVANTAGES.keys() if name.lower() == stat_name), None)
            if not proper_name:
                return False, f"'{stat_name}' is not a valid special advantage", None
                
            try:
                int_value = int(value)
                is_valid, error_msg = validate_companion_advantage(character, proper_name, int_value)
                if is_valid:
                    # Set Ferocity value first
                    if 'powers' not in character.db.stats:
                        character.db.stats['powers'] = {}
                    if 'special_advantage' not in character.db.stats['powers']:
                        character.db.stats['powers']['special_advantage'] = {}
                    character.db.stats['powers']['special_advantage']['Ferocity'] = {'perm': int_value, 'temp': int_value}
                    
                    # Then update Rage pool
                    update_rage_from_ferocity(character)
                return is_valid, error_msg, proper_name
            except ValueError:
                return False, "Special advantage values must be numbers", None
        
    # Validate special advantages
    if category == 'powers' and stat_type == 'special_advantage':
        # Find proper case name from SPECIAL_ADVANTAGES
        proper_name = next((name for name in SPECIAL_ADVANTAGES.keys() if name.lower() == stat_name), None)
        if not proper_name:
            return False, f"'{stat_name}' is not a valid special advantage", None
            
        try:
            int_value = int(value)
            is_valid, error_msg = validate_companion_advantage(character, proper_name, int_value)
            
            # Update Rage pool if this is Ferocity
            if is_valid and proper_name == 'Ferocity':
                # Set Ferocity value first
                if 'powers' not in character.db.stats:
                    character.db.stats['powers'] = {}
                if 'special_advantage' not in character.db.stats['powers']:
                    character.db.stats['powers']['special_advantage'] = {}
                character.db.stats['powers']['special_advantage']['Ferocity'] = {'perm': int_value, 'temp': int_value}
                
                # Then update Rage pool
                update_rage_from_ferocity(character)
                
            return is_valid, error_msg, proper_name
        except ValueError:
            return False, "Special advantage values must be numbers", None
        
    # Validate charms
    if category == 'powers' and stat_type == 'charm':
        is_valid, error_msg = validate_companion_charm(character, stat_name.title(), value)
        return is_valid, error_msg, None
    
    return True, "", None

def validate_companion_type(value: str) -> tuple[bool, str]:
    """Validate a companion type."""
    if value not in COMPANION_TYPES:
        return False, f"Invalid companion type. Valid types are: {', '.join(sorted(COMPANION_TYPES))}"
    return True, ""

def validate_companion_charm(character, charm_name: str, value: str) -> tuple[bool, str]:
    """Validate a companion's charm."""
    # Get companion type
    companion_type = character.get_stat('identity', 'lineage', 'Companion Type', temp=False)
    if not companion_type:
        return False, "Character must have a companion type set"
    
    # Get available charms
    available_charms = COMPANION_POWERS.get('charm', [])
    if not available_charms:
        return False, f"No charms found for companions"
    
    if charm_name not in available_charms:
        return False, f"Invalid charm. Valid charms are: {', '.join(sorted(available_charms))}"
    
    # Validate value
    try:
        charm_value = int(value)
        if charm_value < 0 or charm_value > 5:
            return False, "Charm values must be between 0 and 5"
        return True, ""
    except ValueError:
        return False, "Charm values must be numbers"

def update_companion_pools_on_stat_change(character, stat_name: str, new_value: str) -> None:
    """
    Update companion pools when relevant stats change.
    Called by CmdSelfStat after setting stats.
    """
    stat_name = stat_name.lower()
    
    # Handle Companion Type changes
    if stat_name == 'companion type':
        # Get default Banality based on companion type
        banality = get_default_banality('Companion', subtype=new_value)
        if banality:
            character.set_stat('pools', 'dual', 'Banality', banality, temp=False)
            character.set_stat('pools', 'dual', 'Banality', banality, temp=True)
            character.msg(f"|gBanality set to {banality} for {new_value}.|n")
        
        # Handle special cases for different companion types
        if new_value == 'Familiar':
            # Familiars get Essence Energy pool
            character.set_stat('pools', 'dual', 'Essence Energy', 10, temp=False)
            character.set_stat('pools', 'dual', 'Essence Energy', 10, temp=True)
            character.msg("|gEssence Energy pool set to 10 for Familiar.|n")
    
    # Handle Ferocity special advantage
    elif stat_name == 'ferocity':
        try:
            ferocity_value = int(new_value)
            if ferocity_value > 0:
                # Rage is half of Ferocity (rounded down)
                rage_value = ferocity_value // 2
                character.set_stat('pools', 'dual', 'Rage', rage_value, temp=False)
                character.set_stat('pools', 'dual', 'Rage', rage_value, temp=True)
                character.msg(f"|gRage set to {rage_value} based on Ferocity {ferocity_value}.|n")
        except (ValueError, TypeError):
            character.msg("|rError updating Rage pool - invalid Ferocity value.|n")
            return
