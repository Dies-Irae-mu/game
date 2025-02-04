"""
Utility functions for handling Vampire-specific character initialization and updates.
"""
from world.wod20th.utils.banality import get_default_banality
from world.wod20th.utils.stat_mappings import BLOOD_POOL_MAP
from world.wod20th.utils.virtue_utils import calculate_willpower, calculate_road
from typing import Dict, List, Optional

# Valid vampire clans
CLAN = {
    'Brujah', 'Gangrel', 'Malkavian', 'Nosferatu', 'Toreador', 'Tremere', 'Ventrue', 'Lasombra', 
    'Tzimisce', 'Assamite', 'Followers of Set', 'Hecata', 'Ravnos', 'Baali', 'Blood Brothers', 
    'Daughters of Cacophony', 'Gargoyles', 'Kiasyd', 'Nagaraja', 'Salubri', 'Samedi', 'True Brujah'
}
def get_clan_disciplines(clan):
    """Helper function to get clan disciplines."""
    CLAN_DISCIPLINES = {
        'Ahrimes': ['Animalism', 'Presence', 'Spiritus'],
        'Assamite': ['Celerity', 'Obfuscate', 'Quietus'],
        'Assamite Antitribu': ['Celerity', 'Obfuscate', 'Quietus'],
        'Baali': ['Daimoinon', 'Obfuscate', 'Presence'],
        'Blood Brothers': ['Celerity', 'Potence', 'Sanguinus'],
        'Brujah': ['Celerity', 'Potence', 'Presence'],
        'Brujah Antitribu': ['Celerity', 'Potence', 'Presence'],
        'Bushi': ['Celerity', 'Kai', 'Presence'],
        'Caitiff': [],
        'Cappadocians': ['Auspex', 'Fortitude', 'Mortis'],
        'Children of Osiris': ['Bardo'],
        'Harbingers of Skulls': ['Auspex', 'Fortitude', 'Necromancy'],
        'Daughters of Cacophony': ['Fortitude', 'Melpominee', 'Presence'],
        'Followers of Set': ['Obfuscate', 'Presence', 'Serpentis'],
        'Gangrel': ['Animalism', 'Fortitude', 'Protean'],
        'City Gangrel': ['Celerity', 'Obfuscate', 'Protean'],
        'Country Gangrel': ['Animalism', 'Fortitude', 'Protean'],
        'Gargoyles': ['Fortitude', 'Potence', 'Visceratika'],
        'Giovanni': ['Dominate', 'Necromancy', 'Potence'],
        'Kiasyd': ['Mytherceria', 'Dominate', 'Obtenebration'],
        'Laibon': ['Abombwe', 'Animalism', 'Fortitude'],
        'Lamia': ['Deimos', 'Necromancy', 'Potence'],
        'Lasombra': ['Dominate', 'Obtenebration', 'Potence'],
        'Lasombra Antitribu': ['Dominate', 'Obtenebration', 'Potence'],
        'Lhiannan': ['Animalism', 'Ogham', 'Presence'],
        'Malkavian': ['Auspex', 'Dominate', 'Obfuscate'],
        'Malkavian Antitribu': ['Auspex', 'Dementation', 'Obfuscate'],
        'Nagaraja': ['Auspex', 'Necromancy', 'Dominate'],
        'Nosferatu': ['Animalism', 'Obfuscate', 'Potence'],
        'Nosferatu Antitribu': ['Animalism', 'Obfuscate', 'Potence'],
        'Old Clan Tzimisce': ['Animalism', 'Auspex', 'Dominate'],
        'Panders': [],
        'Ravnos': ['Animalism', 'Chimerstry', 'Fortitude'],
        'Ravnos Antitribu': ['Animalism', 'Chimerstry', 'Fortitude'],
        'Salubri': ['Auspex', 'Fortitude', 'Obeah'],
        'Samedi': ['Necromancy', 'Obfuscate', 'Thanatosis'],
        'Serpents of the Light': ['Obfuscate', 'Presence', 'Serpentis'],
        'Toreador': ['Auspex', 'Celerity', 'Presence'],
        'Toreador Antitribu': ['Auspex', 'Celerity', 'Presence'],
        'Tremere': ['Auspex', 'Dominate', 'Thaumaturgy'],
        'Tremere Antitribu': ['Auspex', 'Dominate', 'Thaumaturgy'],
        'True Brujah': ['Potence', 'Presence', 'Temporis'],
        'Tzimisce': ['Animalism', 'Auspex', 'Vicissitude'],
        'Ventrue': ['Dominate', 'Fortitude', 'Presence'],
        'Ventrue Antitribu': ['Auspex', 'Dominate', 'Fortitude'],
    }
    return CLAN_DISCIPLINES.get(clan, [])

def initialize_vampire_stats(character, clan):
    """Initialize specific stats for a vampire character."""
    # Initialize basic stats structure
    if 'identity' not in character.db.stats:
        character.db.stats['identity'] = {}
    if 'lineage' not in character.db.stats['identity']:
        character.db.stats['identity']['lineage'] = {}
    
    # Initialize powers category if it doesn't exist
    if 'powers' not in character.db.stats:
        character.db.stats['powers'] = {}
    
    # Add Disciplines category
    character.db.stats['powers']['discipline'] = {}
    
    # Add Thaumaturgy category for Tremere and others with blood magic
    if clan.lower() in ['tremere', 'tremere antitribu', 'giovanni', 'nagaraja', 'samedi']:
        character.db.stats['powers']['thaumaturgy'] = {}
    
    # Set default Banality based on clan
    banality = get_default_banality('Vampire', subtype=clan)
    character.set_stat('pools', 'dual', 'Banality', banality, temp=False)
    character.set_stat('pools', 'dual', 'Banality', banality, temp=True)
    
    # Ensure default generation is set (13th)
    if 'Generation' not in character.db.stats['identity']['lineage']:
        character.db.stats['identity']['lineage']['Generation'] = {'perm': '13th', 'temp': '13th'}
    if 'Generation' not in character.db.stats['advantages']['background']:
        character.db.stats['advantages']['background']['Generation'] = {'perm': 0, 'temp': 0}
    
    # Set blood pool based on generation background value
    gen_background = character.get_stat('advantages', 'background', 'Generation', temp=False) or 0
    blood_pool = calculate_blood_pool(gen_background)
    character.set_stat('pools', 'dual', 'Blood', blood_pool, temp=False)
    character.set_stat('pools', 'dual', 'Blood', blood_pool, temp=True)
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
    
    # Initialize clan disciplines
    clan_disciplines = get_clan_disciplines(clan)
    for discipline in clan_disciplines:
        if discipline not in character.db.stats['powers']['discipline']:
            character.db.stats['powers']['discipline'][discipline] = {'perm': 0, 'temp': 0}

def calculate_blood_pool(generation_background):
    """
    Calculate blood pool based on generation background value.
    
    Args:
        generation_background (int): The value of the Generation background
        
    Returns:
        int: The maximum blood pool for that generation
    """
    return BLOOD_POOL_MAP.get(generation_background, 10)  # Default to 10 for 13th generation (0 background) 