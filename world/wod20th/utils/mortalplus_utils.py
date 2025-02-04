"""
Utility functions for handling Mortal+-specific character initialization and updates.
"""
from world.wod20th.utils.vampire_utils import get_clan_disciplines
from world.wod20th.utils.banality import get_default_banality
from typing import Dict, List, Tuple

# Valid Mortal+ types
MORTALPLUS_TYPE_CHOICES: List[Tuple[str, str]] = [
    ('ghoul', 'Ghoul'),
    ('kinfolk', 'Kinfolk'),
    ('kinain', 'Kinain'),
    ('sorcerer', 'Sorcerer'),
    ('psychic', 'Psychic'),
    ('faithful', 'Faithful'),
    ('none', 'None')
]

# Mortal+ pools
MORTALPLUS_POOLS: Dict[str, Dict[str, Dict[str, int]]] = {
    'Ghoul': {
        'Blood': {'default': 3, 'max': 3}
    },
    'Kinfolk': {
        'Gnosis': {'default': 0, 'max': 3}
    },
    'Kinain': {
        'Glamour': {'default': 2, 'max': 2}
    },
    'Sorcerer': {
        'Quintessence': {'default': 0, 'max': 10}
    },
    'Psychic': {
        'Willpower': {'default': 3, 'max': 10},
    }
}

# Mortal+ power types
MORTALPLUS_TYPES: Dict[str, List[str]] = {
    'Ghoul': ['Disciplines'],
    'Kinfolk': ['Gifts'],
    'Sorcerer': ['Sorcery'],
    'Psychic': ['Numina'],
    'Faithful': ['Faith'],
    'Kinain': ['Arts', 'Realms']
}

# Mortal+ available powers
MORTALPLUS_POWERS: Dict[str, Dict[str, List[str]]] = {
    'Ghoul': {
        'Disciplines': ['Potence', 'Fortitude', 'Celerity', 'Animalism', 'Auspex', 'Dominate', 
                       'Presence', 'Obfuscate', 'Protean']
    },
    'Kinfolk': {
        'Gifts': []
    },
    'Sorcerer': {
        'Sorcery': []
    },
    'Psychic': {
        'Numina': []
    },
    'Faithful': {
        'Faith': []
    },
    'Kinain': {
        'Arts': [],
        'Realms': []
    }
}

def initialize_mortalplus_stats(character, mortalplus_type):
    """Initialize specific stats for a Mortal+ character."""
    # Initialize basic stats structure
    if 'identity' not in character.db.stats:
        character.db.stats['identity'] = {}
    if 'lineage' not in character.db.stats['identity']:
        character.db.stats['identity']['lineage'] = {}
    
    # Initialize powers category if it doesn't exist
    if 'powers' not in character.db.stats:
        character.db.stats['powers'] = {}
    
    # Convert mortalplus_type to proper case using MORTALPLUS_TYPE_CHOICES
    proper_type = next((t[1] for t in MORTALPLUS_TYPE_CHOICES if t[0].lower() == mortalplus_type.lower()), None)
    if not proper_type:
        return
        
    # Set default Banality based on type
    banality = get_default_banality('Mortal+', subtype=proper_type)
    character.set_stat('pools', 'dual', 'Banality', banality, temp=False)
    character.set_stat('pools', 'dual', 'Banality', banality, temp=True)
    
    # Set base Willpower for all types
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
    
    # Initialize pools from MORTALPLUS_POOLS
    if proper_type in MORTALPLUS_POOLS:
        for pool_name, pool_data in MORTALPLUS_POOLS[proper_type].items():
            character.set_stat('pools', 'dual', pool_name, pool_data['default'], temp=False)
            character.set_stat('pools', 'dual', pool_name, pool_data['default'], temp=True)
    
    # Initialize power categories from MORTALPLUS_TYPES
    if proper_type in MORTALPLUS_TYPES:
        for power_type in MORTALPLUS_TYPES[proper_type]:
            power_type_lower = power_type.lower()
            if power_type_lower not in character.db.stats['powers']:
                character.db.stats['powers'][power_type_lower] = {}
            
            # Initialize available powers from MORTALPLUS_POWERS
            if proper_type in MORTALPLUS_POWERS and power_type in MORTALPLUS_POWERS[proper_type]:
                for power in MORTALPLUS_POWERS[proper_type][power_type]:
                    if power not in character.db.stats['powers'][power_type_lower]:
                        character.db.stats['powers'][power_type_lower][power] = {'perm': 0, 'temp': 0}
    
    # Set the type in identity/lineage
    character.set_stat('identity', 'lineage', 'Type', proper_type, temp=False)
    character.set_stat('identity', 'lineage', 'Type', proper_type, temp=True)
    
    # Initialize type-specific stats
    if proper_type == 'Ghoul':
        initialize_ghoul_stats(character)
    elif proper_type == 'Kinfolk':
        initialize_kinfolk_stats(character)
    elif proper_type == 'Kinain':
        initialize_kinain_stats(character)
    elif proper_type == 'Sorcerer':
        initialize_sorcerer_stats(character)
    elif proper_type == 'Psychic':
        initialize_psychic_stats(character)
    elif proper_type == 'Faithful':
        initialize_faithful_stats(character)

def initialize_ghoul_stats(character):
    """Initialize Ghoul-specific stats."""
    # Set Blood pool
    character.set_stat('pools', 'dual', 'Blood', 3, temp=False)
    character.set_stat('pools', 'dual', 'Blood', 3, temp=True)
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
    
    # Initialize Disciplines category
    character.db.stats['powers']['discipline'] = {}
    
    # Initialize basic disciplines available to ghouls
    basic_disciplines = ['Potence', 'Fortitude', 'Celerity']
    for discipline in basic_disciplines:
        if discipline not in character.db.stats['powers']['discipline']:
            character.db.stats['powers']['discipline'][discipline] = {'perm': 0, 'temp': 0}

def initialize_kinfolk_stats(character):
    """Initialize Kinfolk-specific stats."""
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
    
    # Initialize Gifts category
    character.db.stats['powers']['gift'] = {}
    
    # Check for Gnosis Merit
    merits = character.db.stats.get('merits', {}).get('merit', {})
    gnosis_merit = next((value.get('perm', 0) for merit, value in merits.items() 
                        if merit.lower() == 'gnosis'), 0)
    if gnosis_merit >= 5:
        gnosis_value = min(3, max(1, gnosis_merit - 4))  # 5->1, 6->2, 7->3
        character.set_stat('pools', 'dual', 'Gnosis', gnosis_value, temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', gnosis_value, temp=True)

def initialize_kinain_stats(character):
    """Initialize Kinain-specific stats."""
    # Set base Glamour
    character.set_stat('pools', 'dual', 'Glamour', 2, temp=False)
    character.set_stat('pools', 'dual', 'Glamour', 2, temp=True)
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
    
    # Initialize Arts and Realms categories
    character.db.stats['powers']['art'] = {}
    character.db.stats['powers']['realm'] = {}

def initialize_sorcerer_stats(character):
    """Initialize Sorcerer-specific stats."""
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
    
    # Set base Mana
    character.set_stat('pools', 'dual', 'Mana', 3, temp=False)
    character.set_stat('pools', 'dual', 'Mana', 3, temp=True)
    
    # Initialize Sorcery and Hedge Ritual categories
    character.db.stats['powers']['sorcery'] = {}
    character.db.stats['powers']['hedge_ritual'] = {}

def initialize_psychic_stats(character):
    """Initialize Psychic-specific stats."""
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
    
    # Initialize Numina category
    character.db.stats['powers']['numina'] = {}

def initialize_faithful_stats(character):
    """Initialize Faithful-specific stats."""
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
    
    # Initialize Faith category
    character.db.stats['powers']['faith'] = {}

def validate_mortalplus_powers(character, power_type, value):
    """
    Validate power selections for Mortal+ characters.
    Returns (bool, str) tuple - (is_valid, error_message)
    """
    mortalplus_type = character.get_stat('identity', 'personal', 'Mortal Plus Type')
    if not mortalplus_type:
        return False, "Character is not a Mortal+ type"

    # Validate Ghoul powers
    if mortalplus_type == 'Ghoul':
        if power_type == 'Disciplines':
            domitor = character.get_stat('identity', 'personal', 'Domitor')
            if not domitor:
                return False, "Ghouls must have a domitor set to learn disciplines"
            
            # Get domitor's clan disciplines
            clan_disciplines = get_clan_disciplines(domitor.get_stat('identity', 'personal', 'Clan'))
            if value not in clan_disciplines:
                return False, f"Ghouls can only learn disciplines from their domitor's clan: {', '.join(clan_disciplines)}"

    # Validate Kinfolk powers
    elif mortalplus_type == 'Kinfolk':
        if power_type == 'Gifts':
            # Check for Gift Merit
            merits = character.db.stats.get('merits', {}).get('merit', {})
            has_gift_merit = any(merit.lower() == 'gift of the spirits' 
                               for merit in merits.keys())
            if not has_gift_merit:
                return False, "Kinfolk must have the 'Gift of the Spirits' Merit to learn Gifts"

        if power_type == 'Gnosis':
            # Check for Gnosis Merit level
            merits = character.db.stats.get('merits', {}).get('merit', {})
            gnosis_merit = next((merit_value.get('perm', 0) 
                               for merit, merit_value in merits.items() 
                               if merit.lower() == 'gnosis'), 0)
            
            max_gnosis = (gnosis_merit - 4) if gnosis_merit >= 5 else 0
            if int(value) > max_gnosis:
                return False, f"Character can only have up to {max_gnosis} Gnosis with current Merit level"

    # Validate Kinain powers
    elif mortalplus_type == 'Kinain':
        if power_type in ['Arts', 'Realms']:
            # Get Kinain Merit level
            merits = character.db.stats.get('merits', {}).get('merit', {})
            kinain_merit = next((merit_value.get('perm', 0) 
                               for merit, merit_value in merits.items() 
                               if merit.lower() == 'fae blood'), 0)
            
            # Calculate maximums based on Merit level
            max_arts = kinain_merit // 2
            max_art_dots = min(3, kinain_merit // 2)
            
            if power_type == 'Arts' and len(character.get_all_powers('Arts')) >= max_arts:
                return False, f"Kinain can only learn {max_arts} Arts with current Merit level"
            
            if int(value) > max_art_dots:
                return False, f"Kinain can only have up to {max_art_dots} dots in {power_type}"

    return True, ""

def can_learn_power(character, power_category, power_name, value):
    """
    Check if a character can learn or increase a power.
    Returns (bool, str) tuple - (can_learn, reason)
    """
    # Get character's splat type
    splat = character.get_stat('identity', 'personal', 'Splat')
    
    # Handle Mortal+ validation
    if splat == 'Mortal Plus':
        return validate_mortalplus_powers(character, power_category, value)
        
    return True, "" 