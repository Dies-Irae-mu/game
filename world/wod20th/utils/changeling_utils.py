"""
Utility functions for handling Changeling-specific character initialization and updates.
"""
from world.wod20th.utils.banality import get_default_banality
from world.wod20th.models import Stat
from world.wod20th.utils.stat_mappings import ARTS, REALMS
from typing import Dict, List, Set

# Valid seemings
SEEMING = {'Childing', 'Wilder', 'Grump'}

# Valid kiths
KITH = {
    'Boggan', 'Clurichaun', 'Eshu', 'Nocker', 'Piskie', 'Pooka', 'Redcap', 'Satyr', 
    'Selkie', 'Arcadian Sidhe', 'Autumn Sidhe', 'Sluagh', 'Troll', 'Inanimae'
}

# Seelie legacies
SEELIE_LEGACIES = {
    'Bumpkin', 'Courtier', 'Crafter', 'Dandy', 'Hermit', 'Orchid', 'Paladin', 'Panderer', 
    'Regent', 'Sage', 'Saint', 'Squire', 'Troubadour', 'Wayfarer'
}

# Unseelie legacies
UNSEELIE_LEGACIES = {
    'Beast', 'Fatalist', 'Fool', 'Grotesque', 'Knave', 'Outlaw', 'Pandora', 'Peacock', 'Rake', 'Riddler', 
    'Ringleader', 'Rogue', 'Savage', 'Wretch'
}

# Phyla (for Inanimae)
PHYLA = {
    'Kuberas': 'Earth',
    'Ondines': 'Water',
    'Parosemes': 'Air',
    'Glomes': 'Stone',
    'Solimonds': 'Fire',
    'Mannikins': 'Artificial'
}

# Powers available to each Inanimae phyla
INANIMAE_POWERS = {
    'Kuberas': ['Sliver', 'Art'],
    'Ondines': ['Sliver', 'Art'],
    'Parosemes': ['Sliver', 'Art'],
    'Glomes': ['Sliver', 'Art'],
    'Solimonds': ['Sliver', 'Art'],
    'Mannikins': ['Sliver', 'Art']
}

# Slivers
SLIVERS = {
    'verdage': ['Verdage'],
    'aquis': ['Aquis'],
    'stratus': ['Stratus'],
    'petros': ['Petros'],
    'pyros': ['Pyros']
}

def initialize_changeling_stats(character, kith, seeming):
    """Initialize specific stats for a changeling character."""
    # Initialize basic stats structure
    if 'identity' not in character.db.stats:
        character.db.stats['identity'] = {}
    if 'lineage' not in character.db.stats['identity']:
        character.db.stats['identity']['lineage'] = {}
    
    # Initialize powers category if it doesn't exist
    if 'powers' not in character.db.stats:
        character.db.stats['powers'] = {}
    
    # Add Arts category
    character.db.stats['powers']['art'] = {}
    
    # Add Realms category
    character.db.stats['powers']['realm'] = {}
    
    # Set default Banality based on kith
    banality = get_default_banality('Changeling', subtype=kith)
    character.set_stat('pools', 'dual', 'Banality', banality, temp=False)
    character.set_stat('pools', 'dual', 'Banality', banality, temp=True)
    
    # Initialize base pools based on seeming
    glamour = initialize_glamour(seeming)
    character.set_stat('pools', 'dual', 'Glamour', glamour, temp=False)
    character.set_stat('pools', 'dual', 'Glamour', glamour, temp=True)
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
    
    # Initialize Nightmare and Willpower Imbalance
    character.set_stat('pools', 'other', 'Nightmare', 0, temp=False)
    character.set_stat('pools', 'other', 'Nightmare', 0, temp=True)
    character.set_stat('pools', 'other', 'Willpower Imbalance', 0, temp=False)
    character.set_stat('pools', 'other', 'Willpower Imbalance', 0, temp=True)
    
    # Initialize all Arts to 0
    for art in ARTS:
        if art not in character.db.stats['powers']['art']:
            character.db.stats['powers']['art'][art] = {'perm': 0, 'temp': 0}
    
    # Initialize all Realms to 0
    for realm in REALMS:
        if realm not in character.db.stats['powers']['realm']:
            character.db.stats['powers']['realm'][realm] = {'perm': 0, 'temp': 0}

    if kith.lower() == 'inanimae':
        initialize_inanimae_stats(character)
    else:
        initialize_standard_changeling_stats(character)

def initialize_glamour(seeming):
    """Calculate initial Glamour based on seeming."""
    seeming = seeming.lower() if seeming else ''
    if seeming == 'childing':
        return 5
    elif seeming == 'wilder':
        return 4
    elif seeming == 'grump':
        return 3
    return 3  # Default value

def initialize_standard_changeling_stats(character):
    """Initialize stats for standard changelings."""
    # Add Arts category
    character.db.stats['powers']['art'] = {}
    
    # Add Realms category
    character.db.stats['powers']['realm'] = {}
    
    # Initialize all Arts to 0
    for art in ARTS:
        if art not in character.db.stats['powers']['art']:
            character.db.stats['powers']['art'][art] = {'perm': 0, 'temp': 0}
    
    # Initialize all Realms to 0
    for realm in REALMS:
        if realm not in character.db.stats['powers']['realm']:
            character.db.stats['powers']['realm'][realm] = {'perm': 0, 'temp': 0}

def initialize_inanimae_stats(character):
    """Initialize stats specific to Inanimae changelings."""
    # Add Slivers category
    character.db.stats['powers']['sliver'] = {}
    
    # Get character's phyla
    phyla = character.get_stat('identity', 'lineage', 'Phyla', temp=False)
    
    if phyla and phyla in INANIMAE_POWERS:
        # Initialize Slivers based on phyla
        for power_type in INANIMAE_POWERS[phyla]:
            if power_type == 'Sliver':
                # Initialize slivers based on phyla type
                if phyla.lower() == 'kuberas':
                    character.db.stats['powers']['sliver']['Verdage'] = {'perm': 0, 'temp': 0}
                elif phyla.lower() == 'ondines':
                    character.db.stats['powers']['sliver']['Aquis'] = {'perm': 0, 'temp': 0}
                elif phyla.lower() == 'parosemes':
                    character.db.stats['powers']['sliver']['Stratus'] = {'perm': 0, 'temp': 0}
                elif phyla.lower() == 'glomes':
                    character.db.stats['powers']['sliver']['Petros'] = {'perm': 0, 'temp': 0}
                elif phyla.lower() == 'solimonds':
                    character.db.stats['powers']['sliver']['Pyros'] = {'perm': 0, 'temp': 0}
            elif power_type == 'Art' and phyla.lower() == 'mannikins':
                # Mannikins also get Arts
                character.db.stats['powers']['art'] = {}
                for art in ARTS:
                    if art not in character.db.stats['powers']['art']:
                        character.db.stats['powers']['art'][art] = {'perm': 0, 'temp': 0}

def get_kith_arts(kith: str) -> List[str]:
    """Get the available arts for a specific kith."""
    # This is a placeholder - implement actual kith-art relationships
    return []

def get_phyla_powers(phyla: str) -> List[str]:
    """Get the available powers for a specific Inanimae phyla."""
    return INANIMAE_POWERS.get(phyla, []) 