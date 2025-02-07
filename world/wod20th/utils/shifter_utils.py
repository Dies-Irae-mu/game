"""
Utility functions for handling Shifter-specific character initialization and updates.
"""
from world.wod20th.utils.banality import get_default_banality
from typing import Dict, Union, List, Tuple

# Valid shifter types
SHIFTER_TYPE_CHOICES: List[Tuple[str, str]] = [
    ('garou', 'Garou'),
    ('gurahl', 'Gurahl'),
    ('rokea', 'Rokea'),
    ('ananasi', 'Ananasi'),
    ('ajaba', 'Ajaba'),
    ('bastet', 'Bastet'),
    ('corax', 'Corax'),
    ('kitsune', 'Kitsune'),
    ('mokole', 'Mokole'),
    ('nagah', 'Nagah'),
    ('nuwisha', 'Nuwisha'),
    ('ratkin', 'Ratkin'),
    ('none', 'None')
]

# Valid auspices
AUSPICE_CHOICES: List[Tuple[str, str]] = [
    ('ragabash', 'Ragabash'),
    ('theurge', 'Theurge'),
    ('philodox', 'Philodox'),
    ('galliard', 'Galliard'),
    ('ahroun', 'Ahroun'),
    ('brightwater', 'Brightwater'),
    ('dimwater', 'Dimwater'),
    ('darkwater', 'Darkwater'), 
    ('arcas', 'Arcas'),
    ('uzmati', 'Uzmati'),
    ('kojubat', 'Kojubat'),
    ('kieh', 'Kieh'),
    ('rishi', 'Rishi'),
    ('rising sun', 'Rising Sun'),
    ('noonday sun', 'Noonday Sun'),
    ('shrouded sun', 'Shrouded Sun'),
    ('midnight sun', 'Midnight Sun'),
    ('decorated sun', 'Decorated Sun'),
    ('solar eclipse', 'Solar Eclipse'),
    ('kamakshi', 'Kamakshi'),
    ('kartikeya', 'Kartikeya'),
    ('kamsa', 'Kamsa'),
    ('kali', 'Kali'),
    ('none', 'None')
]

# Valid Bastet tribes
BASTET_TRIBE_CHOICES: List[Tuple[str, str]] = [
    ('qualmi', 'Qualmi'),
    ('swara', 'Swara'),
    ('khan', 'Khan'),
    ('simba', 'Simba'),
    ('pumonca', 'Pumonca'),
    ('balam', 'Balam'),
    ('bubasti', 'Bubasti'),
    ('ceilican', 'Ceilican'),
    ('bagheera', 'Bagheera'),
    ('none', 'None')
]

# Valid breeds
BREED_CHOICES: List[Tuple[str, str]] = [
    ('homid', 'Homid'),
    ('metis', 'Metis'),
    ('lupus', 'Lupus'),
    ('feline', 'Feline'),
    ('squamus', 'Squamus'),
    ('ursine', 'Ursine'),
    ('latrani', 'Latrani'),
    ('rodens', 'Rodens'),
    ('corvid', 'Corvid'),
    ('balaram', 'Balaram'),
    ('suchid', 'Suchid'),
    ('ahi', 'Ahi'),
    ('arachnid', 'Arachnid'),
    ('kojin', 'Kojin'),
    ('roko', 'Roko'),
    ('shinju', 'Shinju'),
    ('animal-born', 'Animal-Born'),
    ('none', 'None')


]

# Valid Garou tribes
GAROU_TRIBE_CHOICES: List[Tuple[str, str]] = [
    ('black fury', 'Black Fury'),
    ('bone gnawer', 'Bone Gnawer'),
    ('child of gaia', 'Child of Gaia'),
    ('fianna', 'Fianna'),
    ('glass walker', 'Glass Walker'),
    ('red talon', 'Red Talon'),
    ('shadow lord', 'Shadow Lord'),
    ('silent strider', 'Silent Strider'),
    ('silver fang', 'Silver Fang'),
    ('stargazer', 'Stargazer'),
    ('uktena', 'Uktena'),
    ('wendigo', 'Wendigo'),
    ('none', 'None')
]

# Shifter identity stats for each type
SHIFTER_IDENTITY_STATS = {
    'Ajaba': ['Breed', 'Aspect', 'Deed Name'],
    'Ananasi': ['Breed', 'Aspect', 'Deed Name'],
    'Bastet': ['Breed', 'Tribe', 'Deed Name'],
    'Corax': ['Breed', 'Deed Name'],
    'Garou': ['Breed', 'Auspice', 'Tribe', 'Camp', 'Deed Name'],
    'Gurahl': ['Breed', 'Auspice', 'Deed Name'],
    'Kitsune': ['Breed', 'Path', 'Deed Name'],
    'Mokole': ['Breed', 'Auspice', 'Stream', 'Varna', 'Deed Name'],
    'Nagah': ['Breed', 'Auspice', 'Deed Name', 'Crown'],
    'Nuwisha': ['Breed', 'Deed Name'],
    'Ratkin': ['Breed', 'Aspect', 'Deed Name'],
    'Rokea': ['Breed', 'Auspice', 'Deed Name']
}

# Common Breed-based Gnosis values used across multiple shifter types
COMMON_BREED_GNOSIS = {
    'homid': 1,
    'metis': 3,
    'lupus': 5,  # Animal-Born
    'animal-born': 5
}

# Renown types for each shifter type
SHIFTER_RENOWN: Dict[str, Union[List[str], Dict[str, Dict[str, List[int]]]]] = {
    "Ajaba": ["Cunning", "Ferocity", "Obligation"],
    "Ananasi": ["Cunning", "Obedience", "Wisdom"],
    "Bastet": ["Cunning", "Ferocity", "Honor"],
    "Corax": ["Glory", "Honor", "Wisdom"],
    "Garou": ["Glory", "Honor", "Wisdom"],
    "Gurahl": ["Honor", "Succor", "Wisdom"],
    "Kitsune": ["Cunning", "Honor", "Glory"],
    "Mokole": ["Glory", "Honor", "Wisdom"],
    "Nagah": [],  # Nagah don't use Renown
    "Nuwisha": ["Humor", "Glory", "Cunning"],
    "Ratkin": ["Infamy", "Obligation", "Cunning"],
    "Rokea": ["Valor", "Harmony", "Innovation"]
}

def initialize_shifter_type(character, shifter_type):
    """Initialize specific stats for a given shifter type."""
    # Initialize basic stats structure
    if 'identity' not in character.db.stats:
        character.db.stats['identity'] = {}
    if 'lineage' not in character.db.stats['identity']:
        character.db.stats['identity']['lineage'] = {}
    
    # Initialize all identity stats for the shifter type
    if shifter_type in SHIFTER_IDENTITY_STATS:
        for stat in SHIFTER_IDENTITY_STATS[shifter_type]:
            character.set_stat('identity', 'lineage', stat, '', temp=False)
            character.set_stat('identity', 'lineage', stat, '', temp=True)
    
    # Get breed safely with a default value
    breed = character.get_stat('identity', 'lineage', 'Breed')
    breed = breed.lower() if breed else ''
    
    # Initialize powers category if it doesn't exist
    if 'powers' not in character.db.stats:
        character.db.stats['powers'] = {}

    # Add Gifts and Rites categories
    character.db.stats['powers']['gift'] = {}
    character.db.stats['powers']['rite'] = {}

    # Add Renown category
    if 'advantages' not in character.db.stats:
        character.db.stats['advantages'] = {}
    if 'renown' not in character.db.stats['advantages']:
        character.db.stats['advantages']['renown'] = {}

    # Set renown types based on shifter type
    renown_types = SHIFTER_RENOWN.get(shifter_type, [])
    renown_message = None
    if renown_types:
        for renown_type in renown_types:
            if renown_type not in character.db.stats['advantages']['renown']:
                character.db.stats['advantages']['renown'][renown_type] = {'perm': 0, 'temp': 0}
        renown_message = f"Set Renown to {', '.join(renown_types)}."

    # Set default Banality based on shifter type
    banality = get_default_banality('Shifter', subtype=shifter_type)
    character.set_stat('pools', 'dual', 'Banality', banality, temp=False)
    character.set_stat('pools', 'dual', 'Banality', banality, temp=True)

    if shifter_type == 'Ajaba':
        initialize_ajaba(character, breed)
    elif shifter_type == 'Ananasi':
        initialize_ananasi(character, breed)
    elif shifter_type == 'Bastet':
        initialize_bastet(character, breed)
    elif shifter_type == 'Corax':
        initialize_corax(character)
    elif shifter_type == 'Gurahl':
        initialize_gurahl(character, breed)
    elif shifter_type == 'Kitsune':
        initialize_kitsune(character, breed)
    elif shifter_type == 'Mokole':
        initialize_mokole(character, breed)
    elif shifter_type == 'Nagah':
        initialize_nagah(character, breed)
    elif shifter_type == 'Nuwisha':
        initialize_nuwisha(character, breed)
    elif shifter_type == 'Ratkin':
        initialize_ratkin(character, breed)
    elif shifter_type == 'Rokea':
        initialize_rokea(character, breed)
    elif shifter_type == 'Garou':
        initialize_garou(character, breed)

    return renown_message

def initialize_ajaba(character, breed):
    """Initialize Ajaba-specific stats."""
    aspect = character.get_stat('identity', 'lineage', 'Aspect', '').lower()
    AJABA_ASPECT_STATS = {
        'dawn': {'rage': 5, 'gnosis': 1},
        'midnight': {'rage': 3, 'gnosis': 3},
        'dusk': {'rage': 1, 'gnosis': 5}
    }
    
    # Set base Willpower for all Ajaba
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
    
    if aspect in AJABA_ASPECT_STATS:
        stats = AJABA_ASPECT_STATS[aspect]
        # Set Rage
        character.set_stat('pools', 'dual', 'Rage', stats['rage'], temp=False)
        character.set_stat('pools', 'dual', 'Rage', stats['rage'], temp=True)
        # Set Gnosis
        character.set_stat('pools', 'dual', 'Gnosis', stats['gnosis'], temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', stats['gnosis'], temp=True)

def initialize_ananasi(character, breed):
    """Initialize Ananasi-specific stats."""
    # Remove Rage if it exists
    if 'Rage' in character.db.stats.get('pools', {}):
        del character.db.stats['pools']['Rage']
    # Set Blood pool
    character.set_stat('pools', 'dual', 'Blood', 10, temp=False)
    character.set_stat('pools', 'dual', 'Blood', 10, temp=True)
    # Set breed-based stats
    if breed == 'homid':
        character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
        character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
        character.set_stat('pools', 'dual', 'Gnosis', 1, temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', 1, temp=True)
    elif breed in ['arachnid', 'animal-born']:
        character.set_stat('pools', 'dual', 'Willpower', 4, temp=False)
        character.set_stat('pools', 'dual', 'Willpower', 4, temp=True)
        character.set_stat('pools', 'dual', 'Gnosis', 5, temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', 5, temp=True)

def initialize_bastet(character, breed):
    """Initialize Bastet-specific stats."""
    tribe = character.get_stat('identity', 'lineage', 'Tribe', '').lower()
    BASTET_TRIBE_STATS = {
        'balam': {'rage': 4, 'willpower': 3},
        'bubasti': {'rage': 1, 'willpower': 5},
        'ceilican': {'rage': 3, 'willpower': 3},
        'khan': {'rage': 5, 'willpower': 2},
        'pumonca': {'rage': 4, 'willpower': 4},
        'qualmi': {'rage': 2, 'willpower': 5},
        'simba': {'rage': 5, 'willpower': 2},
        'swara': {'rage': 2, 'willpower': 4}
    }
    if tribe in BASTET_TRIBE_STATS:
        stats = BASTET_TRIBE_STATS[tribe]
        character.set_stat('pools', 'dual', 'Rage', stats['rage'], temp=False)
        character.set_stat('pools', 'dual', 'Rage', stats['rage'], temp=True)
        character.set_stat('pools', 'dual', 'Willpower', stats['willpower'], temp=False)
        character.set_stat('pools', 'dual', 'Willpower', stats['willpower'], temp=True)
    if breed in COMMON_BREED_GNOSIS:
        character.set_stat('pools', 'dual', 'Gnosis', COMMON_BREED_GNOSIS[breed], temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', COMMON_BREED_GNOSIS[breed], temp=True)

def initialize_corax(character):
    """Initialize Corax-specific stats."""
    character.set_stat('pools', 'dual', 'Rage', 1, temp=False)
    character.set_stat('pools', 'dual', 'Rage', 1, temp=True)
    character.set_stat('pools', 'dual', 'Gnosis', 6, temp=False)
    character.set_stat('pools', 'dual', 'Gnosis', 6, temp=True)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)

def initialize_gurahl(character, breed):
    """Initialize Gurahl-specific stats."""
    character.set_stat('pools', 'dual', 'Willpower', 6, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 6, temp=True)
    if breed == 'homid':
        character.set_stat('pools', 'dual', 'Rage', 3, temp=False)
        character.set_stat('pools', 'dual', 'Rage', 3, temp=True)
        character.set_stat('pools', 'dual', 'Gnosis', 4, temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', 4, temp=True)
    elif breed in ['lupus', 'animal-born']:
        character.set_stat('pools', 'dual', 'Rage', 4, temp=False)
        character.set_stat('pools', 'dual', 'Rage', 4, temp=True)
        character.set_stat('pools', 'dual', 'Gnosis', 5, temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', 5, temp=True)

def initialize_kitsune(character, breed):
    """Initialize Kitsune-specific stats."""
    path = character.get_stat('identity', 'lineage', 'Path', '').lower()
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 5, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 5, temp=True)
    
    # Set Path-based Rage
    KITSUNE_PATH_RAGE = {
        'kataribe': 2,
        'gukutsushi': 2,
        'doshi': 3,
        'eji': 4
    }
    if path in KITSUNE_PATH_RAGE:
        character.set_stat('pools', 'dual', 'Rage', KITSUNE_PATH_RAGE[path], temp=False)
        character.set_stat('pools', 'dual', 'Rage', KITSUNE_PATH_RAGE[path], temp=True)
    
    # Set Breed-based Gnosis
    KITSUNE_BREED_GNOSIS = {
        'kojin': 3,
        'homid': 3,
        'roko': 5,
        'animal-born': 5,
        'shinju': 4,
        'metis': 4
    }
    if breed in KITSUNE_BREED_GNOSIS:
        character.set_stat('pools', 'dual', 'Gnosis', KITSUNE_BREED_GNOSIS[breed], temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', KITSUNE_BREED_GNOSIS[breed], temp=True)

def initialize_mokole(character, breed):
    """Initialize Mokole-specific stats."""
    auspice = character.get_stat('identity', 'lineage', 'Auspice', '').lower()
    varna = character.get_stat('identity', 'lineage', 'Varna', '').lower()
    
    # Set Breed-based Gnosis
    MOKOLE_BREED_GNOSIS = {
        'homid': 2,
        'animal-born': 4,
        'suchid': 4  # Alternative name for animal-born
    }
    if breed in MOKOLE_BREED_GNOSIS:
        character.set_stat('pools', 'dual', 'Gnosis', MOKOLE_BREED_GNOSIS[breed], temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', MOKOLE_BREED_GNOSIS[breed], temp=True)
    
    # Set Auspice-based Willpower
    MOKOLE_AUSPICE_WILLPOWER = {
        'rising sun striking': 3,
        'noonday sun unshading': 5,
        'setting sun warding': 3,
        'shrouded sun concealing': 4,
        'midnight sun shining': 4,
        'decorated suns gathering': 5,
        'solar eclipse crowning': 5,
        'hemanta': 2,
        'zarad': 3,
        'grisma': 4,
        'vasanta': 5
    }
    if auspice in MOKOLE_AUSPICE_WILLPOWER:
        character.set_stat('pools', 'dual', 'Willpower', MOKOLE_AUSPICE_WILLPOWER[auspice], temp=False)
        character.set_stat('pools', 'dual', 'Willpower', MOKOLE_AUSPICE_WILLPOWER[auspice], temp=True)
    
    # Set Varna-based Rage
    MOKOLE_VARNA_RAGE = {
        'champsa': 3,
        'gharial': 4,
        'halpatee': 4,
        'karna': 3,
        'makara': 3,
        'ora': 5,
        'piasa': 4,
        'syrta': 4,
        'unktehi': 5
    }
    if varna in MOKOLE_VARNA_RAGE:
        character.set_stat('pools', 'dual', 'Rage', MOKOLE_VARNA_RAGE[varna], temp=False)
        character.set_stat('pools', 'dual', 'Rage', MOKOLE_VARNA_RAGE[varna], temp=True)

def initialize_nagah(character, breed):
    """Initialize Nagah-specific stats."""
    auspice = character.get_stat('identity', 'lineage', 'Auspice')
    auspice = auspice.lower() if auspice else ''
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 4, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 4, temp=True)
    
    # Set Breed-based Gnosis
    NAGAH_BREED_GNOSIS = {
        'balaram': 1,  # specific homid name
        'homid': 1,    # homid
        'metis': 1,    # metis
        'animal-born': 5,
        'vasuki': 5    # animal-born specific name for nagah
    }
    if breed in NAGAH_BREED_GNOSIS:
        character.set_stat('pools', 'dual', 'Gnosis', NAGAH_BREED_GNOSIS[breed], temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', NAGAH_BREED_GNOSIS[breed], temp=True)
    
    # Set Auspice-based Rage
    NAGAH_AUSPICE_RAGE = {
        'kamakshi': 3,
        'kartikeya': 4,
        'kamsa': 3,
        'kali': 4
    }
    if auspice in NAGAH_AUSPICE_RAGE:
        character.set_stat('pools', 'dual', 'Rage', NAGAH_AUSPICE_RAGE[auspice], temp=False)
        character.set_stat('pools', 'dual', 'Rage', NAGAH_AUSPICE_RAGE[auspice], temp=True)

def initialize_nuwisha(character, breed):
    """Initialize Nuwisha-specific stats."""
    # Remove Rage if it exists
    if 'Rage' in character.db.stats.get('pools', {}):
        del character.db.stats['pools']['Rage']
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 4, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 4, temp=True)
    
    # Set Breed-based Gnosis
    NUWISHA_BREED_GNOSIS = {
        'homid': 1,
        'animal-born': 5,
        'latrani': 5  # Alternative name for animal-born
    }
    if breed in NUWISHA_BREED_GNOSIS:
        character.set_stat('pools', 'dual', 'Gnosis', NUWISHA_BREED_GNOSIS[breed], temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', NUWISHA_BREED_GNOSIS[breed], temp=True)

def initialize_ratkin(character, breed):
    """Initialize Ratkin-specific stats."""
    aspect = character.get_stat('identity', 'lineage', 'Aspect')
    aspect = aspect.lower() if aspect else ''
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
    
    # Set Breed-based Gnosis
    if breed in COMMON_BREED_GNOSIS:
        character.set_stat('pools', 'dual', 'Gnosis', COMMON_BREED_GNOSIS[breed], temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', COMMON_BREED_GNOSIS[breed], temp=True)
    
    # Set Aspect-based Rage
    RATKIN_ASPECT_RAGE = {
        'tunnel runner': 1,
        'shadow seer': 2,
        'knife skulker': 3,
        'warrior': 5,
        'engineer': 2,
        'plague lord': 3,
        'munchmausen': 4,
        'twitcher': 5
    }
    if aspect in RATKIN_ASPECT_RAGE:
        character.set_stat('pools', 'dual', 'Rage', RATKIN_ASPECT_RAGE[aspect], temp=False)
        character.set_stat('pools', 'dual', 'Rage', RATKIN_ASPECT_RAGE[aspect], temp=True)

def initialize_rokea(character, breed):
    """Initialize Rokea-specific stats."""
    auspice = character.get_stat('identity', 'lineage', 'Auspice')
    auspice = auspice.lower() if auspice else ''
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 4, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 4, temp=True)
    
    # Set Breed-based Gnosis
    ROKEA_BREED_GNOSIS = {
        'homid': 1,
        'animal-born': 5,
        'squamus': 5  # Alternative name for animal-born
    }
    if breed in ROKEA_BREED_GNOSIS:
        character.set_stat('pools', 'dual', 'Gnosis', ROKEA_BREED_GNOSIS[breed], temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', ROKEA_BREED_GNOSIS[breed], temp=True)
    
    # Set Auspice-based Rage
    ROKEA_AUSPICE_RAGE = {
        'brightwater': 5,
        'dimwater': 4,
        'darkwater': 3
    }
    if auspice in ROKEA_AUSPICE_RAGE:
        character.set_stat('pools', 'dual', 'Rage', ROKEA_AUSPICE_RAGE[auspice], temp=False)
        character.set_stat('pools', 'dual', 'Rage', ROKEA_AUSPICE_RAGE[auspice], temp=True)

def initialize_garou(character, breed):
    """Initialize Garou-specific stats."""
    auspice = character.get_stat('identity', 'lineage', 'Auspice')
    auspice = auspice.lower() if auspice else ''
    tribe = character.get_stat('identity', 'lineage', 'Tribe')
    tribe = tribe.lower() if tribe else ''
    
    # Set Auspice-based Rage
    GAROU_AUSPICE_RAGE = {
        'ahroun': 5,
        'galliard': 4,
        'philodox': 3,
        'theurge': 2,
        'ragabash': 1
    }
    if auspice in GAROU_AUSPICE_RAGE:
        character.set_stat('pools', 'dual', 'Rage', GAROU_AUSPICE_RAGE[auspice], temp=False)
        character.set_stat('pools', 'dual', 'Rage', GAROU_AUSPICE_RAGE[auspice], temp=True)
    
    # Set Breed-based Gnosis
    if breed in COMMON_BREED_GNOSIS:
        character.set_stat('pools', 'dual', 'Gnosis', COMMON_BREED_GNOSIS[breed], temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', COMMON_BREED_GNOSIS[breed], temp=True)
    
    # Set Tribe-based Willpower
    GAROU_TRIBE_WILLPOWER = {
        'black furies': 3,
        'bone gnawers': 4,
        'children of gaia': 4,
        'fianna': 3,
        'get of fenris': 3,
        'glass walkers': 3,
        'red talons': 3,
        'shadow lords': 3,
        'silent striders': 3,
        'silver fangs': 3,
        'stargazers': 4,
        'uktena': 3,
        'wendigo': 4
    }
    if tribe in GAROU_TRIBE_WILLPOWER:
        character.set_stat('pools', 'dual', 'Willpower', GAROU_TRIBE_WILLPOWER[tribe], temp=False)
        character.set_stat('pools', 'dual', 'Willpower', GAROU_TRIBE_WILLPOWER[tribe], temp=True) 

def get_shifter_identity_stats(shifter_type: str) -> List[str]:
    """Get the identity stats for a specific shifter type."""
    return SHIFTER_IDENTITY_STATS.get(shifter_type, [])

def get_shifter_renown(shifter_type: str) -> List[str]:
    """Get the renown types for a specific shifter type."""
    return SHIFTER_RENOWN.get(shifter_type, []) 