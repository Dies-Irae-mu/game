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

# Valid power source types
POWER_SOURCE_TYPES: Set[str] = {'Construct', 'Object', 'Robot'}

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

# Define which special advantages are available to each companion type
COMPANION_TYPE_ADVANTAGES = {
    'Alien': [
        'armor', 'aura', 'blending', 'chameleon coloration', 'claws, fangs, or horns',
        'enhancement', 'extra heads', 'extra limbs', 'ghost form', 'immunity',
        'needleteeth', 'nightsight', 'rapid healing', 'regrowth', 'shapechanger',
        'size', 'soak lethal damage', 'soak aggravated damage', 'spirit vision',
        'universal translator', 'venom', 'wall-crawling', 'water breathing'
    ],
    'Animal': [
        'acute smell', 'armor', 'aww!', 'blending', 'chameleon coloration',
        'claws, fangs, or horns', 'enhancement', 'ferocity', 'immunity',
        'musk', 'needleteeth', 'nightsight', 'quills', 'rapid healing',
        'size', 'soak lethal damage', 'venom', 'wall-crawling',
        'water breathing', 'webbing', 'wings'
    ],
    'Bygone': [
        'armor', 'blending', 'chameleon coloration', 'claws, fangs, or horns',
        'enhancement', 'extra heads', 'extra limbs', 'feast of nettles',
        'ferocity', 'immunity', 'needleteeth', 'nightsight', 'quills',
        'rapid healing', 'regrowth', 'size', 'soak lethal damage',
        'soak aggravated damage', 'venom', 'wall-crawling', 'water breathing',
        'webbing', 'wings'
    ],
    'Construct': [
        'armor', 'enhancement', 'extra limbs', 'immunity', 'rapid healing',
        'size', 'soak lethal damage', 'soak aggravated damage'
    ],
    'Familiar': [
        'acute smell', 'armor', 'aww!', 'blending', 'bond-sharing',
        'chameleon coloration', 'claws, fangs, or horns', 'enhancement',
        'ferocity', 'immunity', 'needleteeth', 'nightsight', 'quills',
        'rapid healing', 'shared knowledge', 'size', 'soak lethal damage',
        'spirit vision', 'venom', 'wall-crawling', 'water breathing',
        'webbing', 'wings'
    ],
    'Object': [
        'armor', 'enhancement', 'immunity', 'size', 'soak lethal damage',
        'soak aggravated damage'
    ],
    'Reanimate': [
        'armor', 'claws, fangs, or horns', 'deadly demise', 'enhancement',
        'extra limbs', 'immunity', 'needleteeth', 'rapid healing', 'regrowth',
        'size', 'soak lethal damage', 'soak aggravated damage', 'unaging'
    ],
    'Robot': [
        'armor', 'enhancement', 'extra limbs', 'immunity', 'rapid healing',
        'size', 'soak lethal damage', 'soak aggravated damage'
    ],
    'Spirit': [
        'armor', 'aura', 'bioluminescence', 'blending', 'cause insanity',
        'chameleon coloration', 'claws, fangs, or horns', 'dominance',
        'earthbond', 'elemental touch', 'empathic bond', 'enhancement',
        'ferocity', 'ghost form', 'immunity', 'mesmerism', 'musical influence',
        'mystic shield', 'nightsight', 'rapid healing', 'size',
        'soak lethal damage', 'soak aggravated damage', 'soul-sense',
        'spirit travel', 'spirit vision', 'universal translator'
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
        initialize_spirit_companion_stats(character)
    elif companion_type == 'Bygone':
        initialize_bygone_companion_stats(character)
    elif companion_type in POWER_SOURCE_TYPES:
        initialize_power_source_companion_stats(character)
    else:
        initialize_standard_companion_stats(character)

def initialize_base_pools(character, companion_type=None):
    """Initialize base pools for all companions."""
    # Set base Essence
    character.set_stat('pools', 'dual', 'Essence', 10, temp=False)
    character.set_stat('pools', 'dual', 'Essence', 10, temp=True)
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
    
    # Initialize Special Advantages category
    if 'special_advantage' not in character.db.stats['powers']:
        character.db.stats['powers']['special_advantage'] = {}
    
    # Initialize available special advantages for the companion type
    if companion_type and companion_type in COMPANION_TYPE_ADVANTAGES:
        for advantage in COMPANION_TYPE_ADVANTAGES[companion_type]:
            if advantage not in character.db.stats['powers']['special_advantage']:
                character.db.stats['powers']['special_advantage'][advantage] = {'perm': 0, 'temp': 0}
                
    # Initialize Charms category
    if 'charm' not in character.db.stats['powers']:
        character.db.stats['powers']['charm'] = {}

def initialize_spirit_companion_stats(character):
    """Initialize Spirit-specific companion stats."""
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

def initialize_power_source_companion_stats(character):
    """Initialize stats for Construct, Object, and Robot companions."""
    # These companions might have special initialization needs
    # For now, they just use the base initialization
    pass

def initialize_standard_companion_stats(character):
    """Initialize stats for standard companions."""
    # Standard companions just use the base initialization
    pass 

def validate_companion_advantage(character, advantage_name: str, value: int) -> Tuple[bool, str]:
    """
    Validate a special advantage for a companion.
    Returns (is_valid, error_message)
    """
    # Get companion type
    companion_type = character.get_stat('identity', 'lineage', 'Companion Type', temp=False)
    if not companion_type:
        return False, "Character must have a Companion Type set"
    
    # Check if advantage is available for this companion type
    if companion_type not in COMPANION_TYPE_ADVANTAGES:
        return False, f"Invalid companion type: {companion_type}"
    
    available_advantages = COMPANION_TYPE_ADVANTAGES[companion_type]
    if advantage_name.lower() not in [adv.lower() for adv in available_advantages]:
        return False, f"'{advantage_name}' is not available for {companion_type} companions"
    
    # Validate value against SPECIAL_ADVANTAGES
    advantage_info = SPECIAL_ADVANTAGES.get(advantage_name.lower())
    if not advantage_info:
        return False, f"'{advantage_name}' is not a valid special advantage"
    
    valid_values = advantage_info['valid_values']
    if value not in valid_values:
        return False, f"Invalid value for {advantage_name}. Must be one of: {', '.join(map(str, valid_values))}"
    
    return True, "" 

def validate_companion_stats(character, stat_name: str, value: str, category: str = None, stat_type: str = None) -> tuple[bool, str]:
    """
    Validate companion-specific stats.
    Returns (is_valid, error_message)
    """
    stat_name = stat_name.lower()
    
    # Get companion type
    companion_type = character.get_stat('identity', 'lineage', 'Companion Type', temp=False)
    
    # Validate type
    if stat_name == 'companion type':
        return validate_companion_type(value)
        
    # Validate special advantages
    if category == 'powers' and stat_type == 'special_advantage':
        try:
            int_value = int(value)
            return validate_companion_advantage(character, stat_name.title(), int_value)
        except ValueError:
            return False, "Special advantage values must be numbers"
        
    # Validate charms
    if category == 'powers' and stat_type == 'charm':
        return validate_companion_charm(character, stat_name.title(), value)
    
    return True, ""

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