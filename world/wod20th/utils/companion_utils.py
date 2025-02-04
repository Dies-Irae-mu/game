"""
Utility functions for handling Companion-specific character initialization and updates.
"""
from world.wod20th.utils.banality import get_default_banality
from typing import Dict, List, Set

# Valid companion types
COMPANION_TYPES: Set[str] = {
    'Alien', 'Animal', 'Bygone', 'Construct', 'Familiar', 
    'Object', 'Reanimate', 'Robot', 'Spirit'
}

# Valid power source types
POWER_SOURCE_TYPES: Set[str] = {'Construct', 'Object', 'Robot'}

# Available companion powers
COMPANION_POWERS: Dict[str, List[str]] = {
    'special_advantage': ['Alacrity', 'Human Guise'],
    'charm': ['Blast']
}

def initialize_companion_stats(character, companion_type):
    """Initialize specific stats for a Companion character."""
    # Initialize basic stats structure
    if 'identity' not in character.db.stats:
        character.db.stats['identity'] = {}
    if 'lineage' not in character.db.stats['identity']:
        character.db.stats['identity']['lineage'] = {}
    
    # Initialize powers category if it doesn't exist
    if 'powers' not in character.db.stats:
        character.db.stats['powers'] = {}
    
    # Set default Banality based on type
    banality = get_default_banality('Companion', subtype=companion_type)
    character.set_stat('pools', 'dual', 'Banality', banality, temp=False)
    character.set_stat('pools', 'dual', 'Banality', banality, temp=True)
    
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

def initialize_base_pools(character, companion_type):
    """Initialize base pools for all companions."""
    # Set base Essence
    character.set_stat('pools', 'dual', 'Essence', 10, temp=False)
    character.set_stat('pools', 'dual', 'Essence', 10, temp=True)
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
    
    # Initialize Special Advantages category
    character.db.stats['powers']['special_advantage'] = {}
    
    # Initialize all special advantages to 0
    for advantage in COMPANION_POWERS.get('special_advantage', []):
        if advantage not in character.db.stats['powers']['special_advantage']:
            character.db.stats['powers']['special_advantage'][advantage] = {'perm': 0, 'temp': 0}
    
    # Initialize Charms category
    character.db.stats['powers']['charm'] = {}
    
    # Initialize all charms to 0
    for charm in COMPANION_POWERS.get('charm', []):
        if charm not in character.db.stats['powers']['charm']:
            character.db.stats['powers']['charm'][charm] = {'perm': 0, 'temp': 0}

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