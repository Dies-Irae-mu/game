"""
Utility functions for handling Shifter-specific character initialization and updates.
"""
from world.wod20th.utils.banality import get_default_banality
from world.wod20th.utils.stat_mappings import SHIFTER_BACKGROUNDS
from typing import Dict, Union, List, Tuple, Set

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

# Valid Garou tribes
GAROU_TRIBE_CHOICES: List[Tuple[str, str]] = [
    ('none', 'None'),
    ('black_furies', 'Black Furies'),
    ('bone_gnawers', 'Bone Gnawers'),
    ('children_of_gaia', 'Children of Gaia'),
    ('fianna', 'Fianna'),
    ('get_of_fenris', 'Get of Fenris'),
    ('glass_walkers', 'Glass Walkers'),
    ('red_talons', 'Red Talons'),
    ('shadow_lords', 'Shadow Lords'),
    ('silent_striders', 'Silent Striders'),
    ('silver_fangs', 'Silver Fangs'),
    ('stargazers', 'Stargazers'),
    ('uktena', 'Uktena'),
    ('wendigo', 'Wendigo'),
    ('black_spiral_dancers', 'Black Spiral Dancers')
]

# Valid auspices as a dictionary for game logic
AUSPICE_CHOICES_DICT: Dict[str, List[str]] = {
    'Garou': ['Ragabash', 'Theurge', 'Philodox', 'Galliard', 'Ahroun'],
    'Rokea': ['Brightwater', 'Dimwater', 'Darkwater'],
    'Nagah': ['Kamakshi', 'Kartikeya', 'Kamsa', 'Kali'],
    'Mokole': ['Rising Sun', 'Noonday Sun', 'Shrouded Sun', 'Midnight Sun', 
               'Decorated Sun', 'Solar Eclipse']
}

ASPECT_CHOICES_DICT: Dict[str, List[str]] = {
    'Ajaba': ['Dawn', 'Midnight', 'Dusk'],
    'Ananasi': ['Night', 'Daylight', 'Twilight'],
    'Ratkin.1': ['Night', 'Daylight', 'Twilight'],
    'Mokole': ['Rising Sun', 'Noonday Sun', 'Shrouded Sun', 'Midnight Sun', 
               'Decorated Sun', 'Solar Eclipse']
}

# Valid auspices as a list of tuples for Django model choices
AUSPICE_CHOICES: List[Tuple[str, str]] = [
    ('none', 'None'),
    ('ragabash', 'Ragabash'),
    ('theurge', 'Theurge'),
    ('philodox', 'Philodox'),
    ('galliard', 'Galliard'),
    ('ahroun', 'Ahroun'),
    ('brightwater', 'Brightwater'),
    ('dimwater', 'Dimwater'),
    ('darkwater', 'Darkwater'),
    ('kamakshi', 'Kamakshi'),
    ('kartikeya', 'Kartikeya'),
    ('kamsa', 'Kamsa'),
    ('kali', 'Kali'),
    ('rising_sun', 'Rising Sun'),
    ('noonday_sun', 'Noonday Sun'),
    ('shrouded_sun', 'Shrouded Sun'),
    ('midnight_sun', 'Midnight Sun'),
    ('decorated_sun', 'Decorated Sun'),
    ('solar_eclipse', 'Solar Eclipse')
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

# Valid Gurahl tribes
GURAHL_TRIBE_CHOICES: List[Tuple[str, str]] = [
    ('forest_walkers', 'Forest Walkers'),
    ('ice_stalkers', 'Ice Stalkers'),
    ('river_keepers', 'River Keepers'),
    ('mountain_guardians', 'Mountain Guardians'),
    ('okuma', 'Okuma'),
    ('none', 'None')
]


# Valid breeds as a dictionary for game logic
BREED_CHOICES_DICT: Dict[str, List[str]] = {
    'Garou': ['Homid', 'Metis', 'Lupus'],
    'Bastet': ['Homid', 'Metis', 'Feline'],
    'Rokea': ['Homid', 'Squamus'],
    'Gurahl': ['Homid', 'Ursine'],
    'Nuwisha': ['Homid', 'Latrani'],
    'Ratkin': ['Homid', 'Metis', 'Rodens'],
    'Corax': ['Homid', 'Corvid'],
    'Nagah': ['Balaram', 'Vasuki', 'Ahi'],
    'Ananasi': ['Homid', 'Arachnid'],
    'Kitsune': ['Kojin', 'Shinju', 'Roko'],
    'Mokole': ['Homid', 'Suchid']
}

# Valid breeds as a list of tuples for Django model choices
BREED_CHOICES: List[Tuple[str, str]] = [
    ('none', 'None'),
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
    ('vasuki', 'Vasuki'),
    ('ahi', 'Ahi'),
    ('arachnid', 'Arachnid'),
    ('kojin', 'Kojin'),
    ('shinju', 'Shinju'),
    ('roko', 'Roko'),
    ('suchid', 'Suchid')
]
# First, create a dictionary for personal identity stats that all characters should have
PERSONAL_IDENTITY_STATS = [
    'Full Name', 'Nature', 'Demeanor', 'Concept', 'Date of Birth'
]

# Shifter identity stats for each type
SHIFTER_IDENTITY_STATS = {
    'Ajaba': ['Rank', 'First Change Date', 'Type', 'Breed', 'Aspect', 'Deed Name'],
    'Ananasi': ['Rank', 'First Change Date', 'Type', 'Breed', 'Aspect', 'Deed Name', 'Ananasi Faction', 'Ananasi Cabal'],
    'Bastet': ['Rank', 'First Change Date', 'Type', 'Breed', 'Tribe', 'Deed Name', 'Pryio', 'Jamak Spirit'],
    'Corax': ['Rank', 'First Change Date', 'Type', 'Breed', 'Deed Name'],
    'Garou': ['Rank', 'First Change Date', 'Type', 'Breed', 'Auspice', 'Tribe', 'Camp', 'Deed Name', 'Lodge', 'Fang House'],
    'Gurahl': ['Rank', 'First Change Date', 'Type', 'Breed', 'Auspice', 'Deed Name', 'Tribe'],
    'Kitsune': ['Rank', 'First Change Date', 'Type', 'Breed', 'Kitsune Path', 'Kitsune Faction', 'Deed Name'],
    'Mokole': ['Rank', 'First Change Date', 'Type', 'Breed', 'Auspice', 'Deed Name', 'Varna', 'Stream'],
    'Nagah': ['Rank', 'First Change Date', 'Type', 'Breed', 'Auspice', 'Deed Name', 'Crown'],
    'Nuwisha': ['Rank', 'First Change Date', 'Type', 'Breed', 'Deed Name'],
    'Ratkin': ['Rank', 'First Change Date', 'Type', 'Breed', 'Aspect', 'Deed Name', 'Plague'],
    'Rokea': ['Rank', 'First Change Date', 'Type', 'Breed', 'Auspice', 'Deed Name', 'Rokea Faction'],
    'Camazotz': ['Rank', 'First Change Date', 'Type', 'Breed', 'Aspect', 'Deed Name']
}

# Common Breed-based Gnosis values used across multiple shifter types
COMMON_BREED_GNOSIS = {
    'homid': 1,
    'metis': 3,
    'animal-born': 5
}

# Renown types for each shifter type
SHIFTER_RENOWN: Dict[str, Union[List[str], Dict[str, List[str]]]] = {
    "Ajaba": ["Cunning", "Ferocity", "Obligation"],
    "Ananasi": ["Cunning", "Obedience", "Wisdom"],
    "Bastet": ["Cunning", "Ferocity", "Honor"],
    "Corax": ["Glory", "Honor", "Wisdom"],
    "Garou": {
        "default": ["Glory", "Honor", "Wisdom"],
        "Black Spiral Dancers": ["Power", "Infamy", "Cunning"]
    },
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
    
    # Initialize/preserve personal stats
    for stat in PERSONAL_IDENTITY_STATS:
        # Only initialize if it doesn't exist
        if stat not in character.db.stats['identity']['personal']:
            character.set_stat('identity', 'personal', stat, '', temp=False)
            character.set_stat('identity', 'personal', stat, '', temp=True)
    
    # Set the shifter type in identity/lineage
    character.set_stat('identity', 'lineage', 'Type', shifter_type, temp=False)
    character.set_stat('identity', 'lineage', 'Type', shifter_type, temp=True)
    
    # Initialize Rank for all shifter types
    character.set_stat('identity', 'lineage', 'Rank', 0, temp=False)
    character.set_stat('identity', 'lineage', 'Rank', 0, temp=True)
    
    # Initialize all identity stats for the shifter type
    if shifter_type in SHIFTER_IDENTITY_STATS:
        for stat in SHIFTER_IDENTITY_STATS[shifter_type]:
            if stat not in ['Type', 'Rank']:  # Skip Type and Rank since we already set them
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

    # Set renown types based on shifter type and tribe for Garou
    renown_message = None
    if shifter_type == 'Garou':
        tribe = character.get_stat('identity', 'lineage', 'Tribe', temp=False)
        if tribe and tribe.lower() == 'black spiral dancers':
            renown_types = SHIFTER_RENOWN['Garou']['Black Spiral Dancers']
        else:
            renown_types = SHIFTER_RENOWN['Garou']['default']
    else:
        renown_types = SHIFTER_RENOWN.get(shifter_type, [])
        
    if renown_types:
        # Clear any existing renown
        character.db.stats['advantages']['renown'] = {}
        # Add new renown types
        for renown_type in renown_types:
            character.db.stats['advantages']['renown'][renown_type] = {'perm': 0, 'temp': 0}
        renown_message = f"Set Renown to {', '.join(renown_types)}."

    # Initialize type-specific stats first
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

    # Set default Banality based on shifter type
    banality = get_default_banality('Shifter', subtype=shifter_type)
    if banality:
        character.db.stats['pools']['dual']['Banality'] = {'perm': banality, 'temp': banality}
        character.msg(f"|gBanality set to {banality} (permanent).")

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
    character.msg(f"|gWillpower set to 3 for Ajaba.")
    if aspect in AJABA_ASPECT_STATS:
        stats = AJABA_ASPECT_STATS[aspect]
        # Set Rage
        character.set_stat('pools', 'dual', 'Rage', stats['rage'], temp=False)
        character.set_stat('pools', 'dual', 'Rage', stats['rage'], temp=True)
        # Set Gnosis
        character.set_stat('pools', 'dual', 'Gnosis', stats['gnosis'], temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', stats['gnosis'], temp=True)
        character.msg(f"|gRage and Gnosis set to {stats['rage']} and {stats['gnosis']} for {aspect} aspect.")

def initialize_ananasi(character, breed):
    """Initialize Ananasi-specific stats."""
    # Remove Rage if it exists
    if 'Rage' in character.db.stats.get('pools', {}):
        del character.db.stats['pools']['Rage']
    # Set Blood pool
    character.set_stat('pools', 'dual', 'Blood', 10, temp=False)
    character.set_stat('pools', 'dual', 'Blood', 10, temp=True)
    character.msg(f"|gBlood pool set to 10 for Ananasi.")
    # Set breed-based stats
    if breed == 'homid':

        character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
        character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
        character.set_stat('pools', 'dual', 'Gnosis', 1, temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', 1, temp=True)
        character.msg(f"|gWillpower and Gnosis set to 3 and 1 for homid breed.")
    elif breed in ['arachnid', 'animal-born']:
        character.set_stat('pools', 'dual', 'Willpower', 4, temp=False)
        character.set_stat('pools', 'dual', 'Willpower', 4, temp=True)
        character.set_stat('pools', 'dual', 'Gnosis', 5, temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', 5, temp=True)
        character.msg(f"|gWillpower and Gnosis set to 4 and 5 for arachnid breed.")

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
        character.msg(f"|gRage and Willpower set to {stats['rage']} and {stats['willpower']} for {tribe} tribe.")
    if breed == 'homid':
        character.set_stat('pools', 'dual', 'Gnosis', 1, temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', 1, temp=True)
        character.msg(f"|gGnosis set to 1 for {breed} breed.")
    elif breed == 'metis':
        character.set_stat('pools', 'dual', 'Gnosis', 3, temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', 3, temp=True)
        character.msg(f"|gGnosis set to 3 for {breed} breed.")
    elif breed == 'feline' or breed == 'animal-born':
        character.set_stat('pools', 'dual', 'Gnosis', 5, temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', 5, temp=True)
        character.msg(f"|gGnosis set to 5 for {breed} breed.")

def initialize_corax(character):
    """Initialize Corax-specific stats."""
    character.set_stat('pools', 'dual', 'Rage', 1, temp=False)
    character.set_stat('pools', 'dual', 'Rage', 1, temp=True)
    character.set_stat('pools', 'dual', 'Gnosis', 6, temp=False)
    character.set_stat('pools', 'dual', 'Gnosis', 6, temp=True)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
    character.msg(f"|gRage, Willpower, and Gnosis set for Corax.\nRage: 1, Willpower: 3, Gnosis: 6|n")

def initialize_gurahl(character, breed):
    """Initialize Gurahl-specific stats."""
    character.set_stat('pools', 'dual', 'Willpower', 6, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 6, temp=True)
    character.msg(f"|gWillpower set to 6 for Gurahl.")
    if breed == 'homid':
        character.set_stat('pools', 'dual', 'Rage', 3, temp=False)
        character.set_stat('pools', 'dual', 'Rage', 3, temp=True)
        character.set_stat('pools', 'dual', 'Gnosis', 4, temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', 4, temp=True)
        character.msg(f"|gRage and Gnosis set to 3 and 4 for homid breed.")
    elif breed in ['ursine', 'animal-born']:    
        character.set_stat('pools', 'dual', 'Rage', 4, temp=False)
        character.set_stat('pools', 'dual', 'Rage', 4, temp=True)
        character.set_stat('pools', 'dual', 'Gnosis', 5, temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', 5, temp=True)
        character.msg(f"|gRage and Gnosis set to 4 and 5 for ursine breed.")     


def initialize_kitsune(character, breed):
    """Initialize Kitsune-specific stats."""
    path = character.get_stat('identity', 'lineage', 'Kitsune Path', '').title()  # Use title() for consistency
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 5, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 5, temp=True)
    character.msg(f"|gWillpower set to 5 for Kitsune.")

    # Set Path-based Rage
    KITSUNE_PATH_RAGE = {
        'Kataribe': 2,
        'Gukutsushi': 2,
        'Doshi': 3,
        'Eji': 4
    }
    if path in KITSUNE_PATH_RAGE:
        rage = KITSUNE_PATH_RAGE[path]
        character.set_stat('pools', 'dual', 'Rage', rage, temp=False)
        character.set_stat('pools', 'dual', 'Rage', rage, temp=True)
        character.msg(f"|gRage set to {rage} for {path} path.")

    # Set Breed-based Gnosis
    KITSUNE_BREED_GNOSIS = {
        'Kojin': 3,
        'Homid': 3,
        'Roko': 5,
        'Animal-Born': 5,
        'Shinju': 4,
        'Metis': 4
    }
    breed = breed.title()  # Convert breed to title case
    if breed in KITSUNE_BREED_GNOSIS:
        gnosis = KITSUNE_BREED_GNOSIS[breed]
        character.set_stat('pools', 'dual', 'Gnosis', gnosis, temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', gnosis, temp=True)
        character.msg(f"|gGnosis set to {gnosis} for {breed} breed.")

def initialize_mokole(character, breed):
    """Initialize Mokole-specific stats."""
    auspice = character.get_stat('identity', 'lineage', 'Auspice', '').title()  # Use title() for consistency
    varna = character.get_stat('identity', 'lineage', 'Varna', '').title()  # Use title() for consistency
    
    # Set Breed-based Gnosis
    MOKOLE_BREED_GNOSIS = {
        'Homid': 2,
        'Animal-Born': 4,
        'Suchid': 4  # Alternative name for animal-born
    }
    breed = breed.title()  # Convert breed to title case
    if breed in MOKOLE_BREED_GNOSIS:
        character.set_stat('pools', 'dual', 'Gnosis', MOKOLE_BREED_GNOSIS[breed], temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', MOKOLE_BREED_GNOSIS[breed], temp=True)
        character.msg(f"|gGnosis set to {MOKOLE_BREED_GNOSIS[breed]} for {breed} breed.")

    # Set Auspice-based Willpower
    MOKOLE_AUSPICE_WILLPOWER = {
        'Rising Sun': 3,
        'Noonday Sun': 5,
        'Setting Sun': 3,
        'Shrouded Sun': 4,
        'Midnight Sun': 4,
        'Decorated Sun': 5,
        'Solar Eclipse': 5
    }
    if auspice in MOKOLE_AUSPICE_WILLPOWER:
        willpower = MOKOLE_AUSPICE_WILLPOWER[auspice]
        character.set_stat('pools', 'dual', 'Willpower', willpower, temp=False)
        character.set_stat('pools', 'dual', 'Willpower', willpower, temp=True)
        character.msg(f"|gWillpower set to {willpower} for {auspice} auspice.")

    # Set Varna-based Rage
    MOKOLE_VARNA_RAGE = {
        'Champsa': 3,
        'Gharial': 4,
        'Halpatee': 4,
        'Karna': 3,
        'Makara': 3,
        'Ora': 5,
        'Piasa': 4,
        'Syrta': 4,
        'Unktehi': 5
    }
    if varna in MOKOLE_VARNA_RAGE:
        rage = MOKOLE_VARNA_RAGE[varna]
        character.set_stat('pools', 'dual', 'Rage', rage, temp=False)
        character.set_stat('pools', 'dual', 'Rage', rage, temp=True)
        character.msg(f"|gRage set to {rage} for {varna} varna.")

def initialize_nagah(character, breed):
    """Initialize Nagah-specific stats."""
    auspice = character.get_stat('identity', 'lineage', 'Auspice', '').title()  # Use title() for consistency
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 4, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 4, temp=True)
    character.msg(f"|gWillpower set to 4 for Nagah.")

    # Set Breed-based Gnosis
    NAGAH_BREED_GNOSIS = {
        'Balaram': 1,  # specific homid name
        'Homid': 1,    # homid
        'Ahi': 1,      # metis
        'Vasuki': 5    # animal-born specific name for nagah
    }
    breed = breed.title()  # Convert breed to title case
    if breed in NAGAH_BREED_GNOSIS:
        character.set_stat('pools', 'dual', 'Gnosis', NAGAH_BREED_GNOSIS[breed], temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', NAGAH_BREED_GNOSIS[breed], temp=True)
        character.msg(f"|gGnosis set to {NAGAH_BREED_GNOSIS[breed]} for {breed} breed.")

    # Set Auspice-based Rage
    NAGAH_AUSPICE_RAGE = {
        'Kamakshi': 3,
        'Kartikeya': 4,
        'Kamsa': 3,
        'Kali': 4
    }
    if auspice in NAGAH_AUSPICE_RAGE:
        rage = NAGAH_AUSPICE_RAGE[auspice]
        character.set_stat('pools', 'dual', 'Rage', rage, temp=False)
        character.set_stat('pools', 'dual', 'Rage', rage, temp=True)
        character.msg(f"|gRage set to {rage} for {auspice} auspice.")

def initialize_nuwisha(character, breed):
    """Initialize Nuwisha-specific stats."""
    # Remove Rage if it exists
    if 'Rage' in character.db.stats.get('pools', {}):

        del character.db.stats['pools']['Rage']
    character.msg(f"|gRage removed for Nuwisha.")
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 4, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 4, temp=True)
    character.msg(f"|gWillpower set to 4 for Nuwisha.")

    # Set Breed-based Gnosis
    NUWISHA_BREED_GNOSIS = {
        'homid': 1,
        'animal-born': 5,
        'latrani': 5  # Alternative name for animal-born
    }
    if breed in NUWISHA_BREED_GNOSIS:
        character.set_stat('pools', 'dual', 'Gnosis', NUWISHA_BREED_GNOSIS[breed], temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', NUWISHA_BREED_GNOSIS[breed], temp=True)
        character.msg(f"|gGnosis set to {NUWISHA_BREED_GNOSIS[breed]} for {breed} breed.")

def initialize_ratkin(character, breed):
    """Initialize Ratkin-specific stats."""
    aspect = character.get_stat('identity', 'lineage', 'Aspect')
    aspect = aspect.lower() if aspect else ''

    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
    character.msg(f"|gWillpower set to 3 for Ratkin.")

    # Set Breed-based Gnosis
    if breed == 'homid':
        character.set_stat('pools', 'dual', 'Gnosis', 1, temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', 1, temp=True)
        character.msg(f"|gGnosis set to 1 for homid breed.")
    elif breed == 'metis':
        character.set_stat('pools', 'dual', 'Gnosis', 3, temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', 3, temp=True)
        character.msg(f"|gGnosis set to 3 for metis breed.")
    elif breed == 'rodens' or breed == 'animal-born':
        character.set_stat('pools', 'dual', 'Gnosis', 5, temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', 5, temp=True)
        character.msg(f"|gGnosis set to 5 for rodens or animal-born breed.")
    
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
        character.msg(f"|gRage set to {RATKIN_ASPECT_RAGE[aspect]} for {aspect} aspect.")
def initialize_rokea(character, breed):
    """Initialize Rokea-specific stats."""
    auspice = character.get_stat('identity', 'lineage', 'Auspice')
    auspice = auspice.lower() if auspice else ''
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 4, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 4, temp=True)
    character.msg(f"|gWillpower set to 4 for Rokea.")
    # Set Breed-based Gnosis
    ROKEA_BREED_GNOSIS = {
        'homid': 1,
        'animal-born': 5,
        'squamus': 5  # Alternative name for animal-born
    }
    if breed in ROKEA_BREED_GNOSIS:
        character.set_stat('pools', 'dual', 'Gnosis', ROKEA_BREED_GNOSIS[breed], temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', ROKEA_BREED_GNOSIS[breed], temp=True)
        character.msg(f"|gGnosis set to {ROKEA_BREED_GNOSIS[breed]} for {breed} breed.")
    # Set Auspice-based Rage
    ROKEA_AUSPICE_RAGE = {
        'brightwater': 5,
        'dimwater': 4,
        'darkwater': 3
    }
    if auspice in ROKEA_AUSPICE_RAGE:
        character.set_stat('pools', 'dual', 'Rage', ROKEA_AUSPICE_RAGE[auspice], temp=False)
        character.set_stat('pools', 'dual', 'Rage', ROKEA_AUSPICE_RAGE[auspice], temp=True)
        character.msg(f"|gRage set to {ROKEA_AUSPICE_RAGE[auspice]} for {auspice} auspice.")
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
        character.msg(f"|gRage set to {GAROU_AUSPICE_RAGE[auspice]} for {auspice} auspice.")
    # Set Breed-based Gnosis
    if breed in COMMON_BREED_GNOSIS:
        character.set_stat('pools', 'dual', 'Gnosis', COMMON_BREED_GNOSIS[breed], temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', COMMON_BREED_GNOSIS[breed], temp=True)
        character.msg(f"|gGnosis set to {COMMON_BREED_GNOSIS[breed]} for {breed} breed.")
    # Set Tribe-based Willpower
    GAROU_TRIBE_WILLPOWER = {
        'black furies': 3,
        'black spiral dancers': 3,
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
        character.msg(f"|gWillpower set to {GAROU_TRIBE_WILLPOWER[tribe]} for {tribe} tribe.")

def get_shifter_identity_stats(shifter_type: str) -> List[str]:
    """Get the identity stats for a specific shifter type."""
    return SHIFTER_IDENTITY_STATS.get(shifter_type, [])

def get_shifter_renown(shifter_type: str) -> List[str]:
    """Get the renown types for a specific shifter type."""
    return SHIFTER_RENOWN.get(shifter_type, [])

def update_shifter_pools_on_stat_change(character, stat_name, new_value):
    """
    Update shifter pools when a relevant stat changes.
    Called by CmdSelfStat after setting identity stats.
    """
    # Get character's shifter type
    shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
    if not shifter_type:
        return
        
    # Convert to lowercase for comparison
    stat_name = stat_name.lower()
    shifter_type = shifter_type.lower()
    new_value = new_value.lower() if isinstance(new_value, str) else new_value

    if stat_name == 'type':
        # When shifter type is set/changed, call the appropriate initialize function
        initialize_shifter_type(character, new_value)
    elif stat_name == 'breed':
        update_breed_stats(character, new_value, shifter_type)
    elif stat_name == 'aspect':
        update_aspect_stats(character, new_value, shifter_type)
    elif stat_name == 'auspice':
        update_auspice_stats(character, new_value, shifter_type)
    elif stat_name == 'tribe':
        update_tribe_stats(character, new_value, shifter_type)
    elif stat_name == 'kitsune path':
        KITSUNE_PATH_RAGE = {
            'kataribe': 2,
            'gukutsushi': 2,
            'doshi': 3,
            'eji': 4
        }
        new_value = new_value.lower()
        if new_value in KITSUNE_PATH_RAGE:
            rage = KITSUNE_PATH_RAGE[new_value]
            character.set_stat('pools', 'dual', 'Rage', rage, temp=False)
            character.set_stat('pools', 'dual', 'Rage', rage, temp=True)
            character.msg(f"|gRage set to {rage} for {new_value} path.")
    elif stat_name == 'varna' and shifter_type == 'mokole':
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
        new_value = new_value.lower()
        if new_value in MOKOLE_VARNA_RAGE:
            rage = MOKOLE_VARNA_RAGE[new_value]
            character.set_stat('pools', 'dual', 'Rage', rage, temp=False)
            character.set_stat('pools', 'dual', 'Rage', rage, temp=True)
            character.msg(f"|gRage set to {rage} for {new_value} varna.")

def update_breed_stats(character, breed, shifter_type):
    """Update stats based on breed."""
    breed = breed.lower()  # Convert breed to lowercase for comparison
    
    if shifter_type == 'nagah':
        # Handle Nagah breeds specifically
        NAGAH_BREED_GNOSIS = {
            'balaram': 1,  # specific homid name
            'homid': 1,    # homid
            'ahi': 3,      # metis
            'vasuki': 5    # animal-born specific name for nagah
        }
        if breed in NAGAH_BREED_GNOSIS:
            gnosis = NAGAH_BREED_GNOSIS[breed]
            character.set_stat('pools', 'dual', 'Gnosis', gnosis, temp=False)
            character.set_stat('pools', 'dual', 'Gnosis', gnosis, temp=True)
            character.msg(f"|gGnosis set to {gnosis} for {breed} breed.")
            
    elif shifter_type in ['ajaba', 'ratkin', 'rokea', 'garou', 'bastet', 'gurahl', 'kitsune', 'mokole', 'camazotz']:
        gnosis_value = None
        if breed in ['homid']:
            gnosis_value = 1
        elif breed in ['balaram']:
            gnosis_value = 1
        elif breed in ['kojin']:
            gnosis_value = 3
        elif breed in ['metis', 'ahi']:
            gnosis_value = 3
        elif breed in ['shinju']:
            gnosis_value = 4
        elif breed in ['lupus', 'feline', 'suchid', 'ursine', 'squamus', 'roko', 'rodens', 'vasuki', 'chiropter', 'animal-born']:
            gnosis_value = 5
            
        if gnosis_value is not None:
            character.set_stat('pools', 'dual', 'Gnosis', gnosis_value, temp=False)
            character.set_stat('pools', 'dual', 'Gnosis', gnosis_value, temp=True)
            character.msg(f"|gGnosis set to {gnosis_value} for {breed} breed.")
            
    elif shifter_type == 'ananasi':
        gnosis_value = None
        willpower_value = None
        
        if breed == 'homid':
            gnosis_value = 1
            willpower_value = 3
        elif breed in ['arachnid', 'animal-born']:
            gnosis_value = 5
            willpower_value = 4
            
        if gnosis_value is not None and willpower_value is not None:
            character.set_stat('pools', 'dual', 'Gnosis', gnosis_value, temp=False)
            character.set_stat('pools', 'dual', 'Gnosis', gnosis_value, temp=True)
            character.set_stat('pools', 'dual', 'Willpower', willpower_value, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', willpower_value, temp=True)
            character.msg(f"|gGnosis and Willpower set to {gnosis_value} and {willpower_value} for {breed} breed.")
            
        # Ensure Blood pool is set and Rage is removed
        character.set_stat('pools', 'dual', 'Blood', 10, temp=False)
        character.set_stat('pools', 'dual', 'Blood', 10, temp=True)
        character.msg(f"|gBlood set to 10 for ananasi.")
        if 'Rage' in character.db.stats.get('pools', {}).get('dual', {}):
            del character.db.stats['pools']['dual']['Rage']
            character.msg(f"|gRage removed for Ananasi. Blood set to 10.")

    elif shifter_type == 'nuwisha':
        gnosis_value = None
        if breed in ['homid']:
            gnosis_value = 1
        elif breed in ['latrani', 'animal-born']:
            gnosis_value = 5
            
        if gnosis_value is not None:
            character.set_stat('pools', 'dual', 'Gnosis', gnosis_value, temp=False)
            character.set_stat('pools', 'dual', 'Gnosis', gnosis_value, temp=True)
            character.msg(f"|gGnosis set to {gnosis_value} for {breed} breed.")
            
        # Remove Rage
        if 'Rage' in character.db.stats.get('pools', {}).get('dual', {}):
            del character.db.stats['pools']['dual']['Rage']
            character.msg(f"|gRage removed for {breed} breed.")

def update_aspect_stats(character, aspect, shifter_type):
    """Update stats based on aspect."""
    if shifter_type == 'ajaba':
        AJABA_ASPECT_STATS = {
            'dawn': {'rage': 5, 'gnosis': 1},
            'midnight': {'rage': 3, 'gnosis': 3},
            'dusk': {'rage': 1, 'gnosis': 5}
        }
        if aspect in AJABA_ASPECT_STATS:
            stats = AJABA_ASPECT_STATS[aspect]
            character.set_stat('pools', 'dual', 'Rage', stats['rage'], temp=False)
            character.set_stat('pools', 'dual', 'Rage', stats['rage'], temp=True)
            character.set_stat('pools', 'dual', 'Gnosis', stats['gnosis'], temp=False)
            character.set_stat('pools', 'dual', 'Gnosis', stats['gnosis'], temp=True)
            character.msg(f"|gRage set to {stats['rage']} and Gnosis set to {stats['gnosis']} for {aspect} aspect.")
    elif shifter_type == 'ratkin':
        RATKIN_ASPECT_RAGE = {
            'tunnel runner': 1, 'shadow seer': 2, 'knife skulker': 3,
            'warrior': 5, 'engineer': 2, 'plague lord': 3,
            'munchmausen': 4, 'twitcher': 5
        }
        if aspect in RATKIN_ASPECT_RAGE:
            character.set_stat('pools', 'dual', 'Rage', RATKIN_ASPECT_RAGE[aspect], temp=False)
            character.set_stat('pools', 'dual', 'Rage', RATKIN_ASPECT_RAGE[aspect], temp=True)
            character.msg(f"|gRage set to {RATKIN_ASPECT_RAGE[aspect]} for {aspect} aspect.")
def update_auspice_stats(character, auspice, shifter_type):
    """Update stats based on auspice."""
    auspice = auspice.lower()  # Convert to lowercase for comparison
    
    if shifter_type == 'garou':
        GAROU_AUSPICE_RAGE = {
            'ahroun': 5, 'galliard': 4, 'philodox': 3,
            'theurge': 2, 'ragabash': 1
        }
        if auspice in GAROU_AUSPICE_RAGE:
            character.set_stat('pools', 'dual', 'Rage', GAROU_AUSPICE_RAGE[auspice], temp=False)
            character.set_stat('pools', 'dual', 'Rage', GAROU_AUSPICE_RAGE[auspice], temp=True)
            character.msg(f"|gRage set to {GAROU_AUSPICE_RAGE[auspice]} for {auspice} auspice.")
    
    elif shifter_type == 'rokea':
        ROKEA_AUSPICE_RAGE = {
            'brightwater': 5, 'dimwater': 4, 'darkwater': 3
        }
        if auspice in ROKEA_AUSPICE_RAGE:
            character.set_stat('pools', 'dual', 'Rage', ROKEA_AUSPICE_RAGE[auspice], temp=False)
            character.set_stat('pools', 'dual', 'Rage', ROKEA_AUSPICE_RAGE[auspice], temp=True)
            character.msg(f"|gRage set to {ROKEA_AUSPICE_RAGE[auspice]} for {auspice} auspice.")
    
    elif shifter_type == 'nagah':
        NAGAH_AUSPICE_RAGE = {
            'kamakshi': 3,
            'kartikeya': 4,
            'kamsa': 3,
            'kali': 4
        }
        if auspice in NAGAH_AUSPICE_RAGE:
            rage = NAGAH_AUSPICE_RAGE[auspice]
            character.set_stat('pools', 'dual', 'Rage', rage, temp=False)
            character.set_stat('pools', 'dual', 'Rage', rage, temp=True)
            character.msg(f"|gRage set to {rage} for {auspice} auspice.")
    
    elif shifter_type == 'mokole':
        MOKOLE_AUSPICE_WILLPOWER = {
            'rising sun': 3,
            'noonday sun': 5,
            'setting sun': 3,
            'shrouded sun': 4,
            'midnight sun': 4,
            'decorated sun': 5,
            'solar eclipse': 5
        }
        if auspice in MOKOLE_AUSPICE_WILLPOWER:
            willpower = MOKOLE_AUSPICE_WILLPOWER[auspice]
            character.set_stat('pools', 'dual', 'Willpower', willpower, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', willpower, temp=True)
            character.msg(f"|gWillpower set to {willpower} for {auspice} auspice.")
    
    elif shifter_type == 'gurahl':
        GURAHL_AUSPICE_STATS = {
            'arcas': {'rage': 4, 'willpower': 3},
            'uzmati': {'rage': 3, 'willpower': 4},
            'kojubat': {'rage': 2, 'willpower': 5},
            'kieh': {'rage': 1, 'willpower': 6},
            'rishi': {'rage': 5, 'willpower': 2}
        }
        if auspice in GURAHL_AUSPICE_STATS:
            stats = GURAHL_AUSPICE_STATS[auspice]
            character.set_stat('pools', 'dual', 'Rage', stats['rage'], temp=False)
            character.set_stat('pools', 'dual', 'Rage', stats['rage'], temp=True)
            character.set_stat('pools', 'dual', 'Willpower', stats['willpower'], temp=False)
            character.set_stat('pools', 'dual', 'Willpower', stats['willpower'], temp=True)
            character.msg(f"|gRage set to {stats['rage']} and Willpower set to {stats['willpower']} for {auspice} auspice.")
            
def update_tribe_stats(character, tribe, shifter_type):
    """Update stats based on tribe."""
    tribe = tribe.lower() if tribe else ''
    
    if shifter_type == 'garou':
        # Handle Black Spiral Dancer special renown
        if tribe == 'black spiral dancers':
            # Clear existing renown
            if 'advantages' in character.db.stats and 'renown' in character.db.stats['advantages']:
                character.db.stats['advantages']['renown'] = {}
            # Set BSD renown types
            bsd_renown = {'Power': {'perm': 0, 'temp': 0},
                         'Infamy': {'perm': 0, 'temp': 0},
                         'Cunning': {'perm': 0, 'temp': 0}}
            character.db.stats['advantages']['renown'] = bsd_renown
            character.msg("|gRenown set to Power, Infamy, and Cunning for Black Spiral Dancers.")
        else:
            # Reset to standard Garou renown if changing from BSD
            if 'advantages' in character.db.stats and 'renown' in character.db.stats['advantages']:
                # Only reset if current renown is BSD renown
                current_renown = set(character.db.stats['advantages']['renown'].keys())
                if current_renown == {'Power', 'Infamy', 'Cunning'}:
                    character.db.stats['advantages']['renown'] = {
                        'Glory': {'perm': 0, 'temp': 0},
                        'Honor': {'perm': 0, 'temp': 0},
                        'Wisdom': {'perm': 0, 'temp': 0}
                    }
                    character.msg("|gRenown reset to Glory, Honor, and Wisdom for standard Garou.")
        
        # Set Willpower based on tribe
        GAROU_TRIBE_WILLPOWER = {
            'black furies': 3, 'bone gnawers': 4, 'children of gaia': 4,
            'fianna': 3, 'get of fenris': 3, 'glass walkers': 3,
            'red talons': 3, 'shadow lords': 3, 'silent striders': 3,
            'silver fangs': 3, 'stargazers': 4, 'uktena': 3, 'wendigo': 4,
            'black spiral dancers': 3  # Added BSD willpower
        }
        if tribe in GAROU_TRIBE_WILLPOWER:
            character.set_stat('pools', 'dual', 'Willpower', GAROU_TRIBE_WILLPOWER[tribe], temp=False)
            character.set_stat('pools', 'dual', 'Willpower', GAROU_TRIBE_WILLPOWER[tribe], temp=True)
            character.msg(f"|gWillpower set to {GAROU_TRIBE_WILLPOWER[tribe]} for {tribe} tribe.")
    
    elif shifter_type == 'bastet':
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
            character.msg(f"|gRage set to {stats['rage']} and Willpower set to {stats['willpower']} for {tribe} tribe.")

def validate_shifter_stats(character, stat_name: str, value: str, category: str = None, stat_type: str = None) -> tuple[bool, str, str]:
    """
    Validate shifter-specific stats.
    Returns (is_valid, error_message, corrected_value)
    """
    stat_name = stat_name.lower()
    
    # Get shifter type
    shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
    if not shifter_type:
        return False, "Character must have a shifter type set", None
    
    # Validate type
    if stat_name == 'type':
        return validate_shifter_type(value)
        
    # Validate breed
    if stat_name == 'breed':
        return validate_shifter_breed(shifter_type, value)
        
    # Validate auspice
    if stat_name == 'auspice':
        return validate_shifter_auspice(shifter_type, value)
        
    # Validate tribe
    if stat_name == 'tribe':
        return validate_shifter_tribe(shifter_type, value)
        
    # Validate aspect
    if stat_name == 'aspect':
        return validate_shifter_aspect(shifter_type, value)
        
    # Validate gifts
    if category == 'powers' and stat_type == 'gift':
        return validate_shifter_gift(character, stat_name, value)
        
    # Validate backgrounds
    if category == 'backgrounds' and stat_type == 'background':
        return validate_shifter_backgrounds(character, stat_name, value)
    
    return True, "", value

def validate_shifter_type(value: str) -> tuple[bool, str, str]:
    """Validate a shifter type."""
    valid_types = [t[1] for t in SHIFTER_TYPE_CHOICES if t[1] != 'None']
    value_title = value.title()
    if value_title in valid_types:
        return True, "", value_title
    return False, f"Invalid shifter type. Valid types are: {', '.join(sorted(valid_types))}", None

def validate_shifter_breed(shifter_type: str, value: str) -> tuple[bool, str, str]:
    """Validate a shifter's breed based on their type."""
    valid_breeds = BREED_CHOICES_DICT.get(shifter_type, [])
    if not valid_breeds:
        return False, f"No valid breeds found for {shifter_type}", None
    
    # Try title case and case-insensitive match
    value_title = value.title()
    if value_title in valid_breeds:
        return True, "", value_title
        
    value_lower = value.lower()
    for breed in valid_breeds:
        if breed.lower() == value_lower:
            return True, "", breed
            
    # If no match found, return full list of valid breeds
    return False, f"Invalid breed for {shifter_type}. Valid breeds are: {', '.join(sorted(valid_breeds))}", None

def validate_shifter_auspice(shifter_type: str, value: str) -> tuple[bool, str, str]:
    """Validate a shifter's auspice based on their type."""
    valid_auspices = AUSPICE_CHOICES_DICT.get(shifter_type, [])
    if not valid_auspices:
        return False, f"{shifter_type} characters do not have auspices", None
    
    # Try title case and case-insensitive match
    value_title = value.title()
    if value_title in valid_auspices:
        return True, "", value_title
        
    value_lower = value.lower()
    for auspice in valid_auspices:
        if auspice.lower() == value_lower:
            return True, "", auspice
            
    # If no match found, return full list of valid auspices
    return False, f"Invalid auspice for {shifter_type}. Valid auspices are: {', '.join(sorted(valid_auspices))}", None

def validate_shifter_tribe(shifter_type: str, value: str) -> tuple[bool, str, str]:
    """Validate a shifter's tribe based on their type."""
    if shifter_type == 'Garou':
        valid_tribes = [t[1] for t in GAROU_TRIBE_CHOICES if t[1] != 'None']
    elif shifter_type == 'Bastet':
        valid_tribes = [t[1] for t in BASTET_TRIBE_CHOICES if t[1] != 'None']
    elif shifter_type == 'Gurahl':
        valid_tribes = [t[1] for t in GURAHL_TRIBE_CHOICES if t[1] != 'None']
    else:
        return False, f"{shifter_type} characters do not have tribes", None
    
    # Try title case and case-insensitive match
    value_title = value.title()
    if value_title in valid_tribes:
        return True, "", value_title
        
    value_lower = value.lower()
    for tribe in valid_tribes:
        if tribe.lower() == value_lower:
            return True, "", tribe
            
    # If no match found, return full list of valid tribes
    return False, f"Invalid tribe for {shifter_type}. Valid tribes are: {', '.join(sorted(valid_tribes))}", None

def validate_shifter_aspect(shifter_type: str, value: str) -> tuple[bool, str, str]:
    """Validate a shifter's aspect based on their type."""
    valid_aspects = ASPECT_CHOICES_DICT.get(shifter_type, [])
    if not valid_aspects:
        return False, f"{shifter_type} characters do not have aspects", None
    
    # Try title case and case-insensitive match
    value_title = value.title()
    if value_title in valid_aspects:
        return True, "", value_title
        
    value_lower = value.lower()
    for aspect in valid_aspects:
        if aspect.lower() == value_lower:
            return True, "", aspect
            
    # If no match found, return full list of valid aspects
    return False, f"Invalid aspect for {shifter_type}. Valid aspects are: {', '.join(sorted(valid_aspects))}", None

def validate_shifter_gift(character, gift_name: str, value: str) -> tuple[bool, str, str]:
    """Validate a shifter gift."""
    # Import Stat here to avoid circular import
    from world.wod20th.models import Stat
    
    # Get character's type and other relevant attributes
    shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
    
    # Validate value first
    try:
        gift_value = int(value)
        if gift_value < 0 or gift_value > 5:
            return False, "Gift values must be between 0 and 5", None
    except ValueError:
        return False, "Gift values must be numbers", None
    
    # Check if the gift exists in the database
    gift = Stat.objects.filter(
        name__iexact=gift_name,
        category='powers',
        stat_type='gift'
    ).first()
    
    if not gift:
        return False, f"'{gift_name}' is not a valid gift", None
        
    # If the gift exists but has a specific shifter_type requirement,
    # validate that the character can use it
    if gift.shifter_type and gift.shifter_type != shifter_type:
        return False, f"'{gift_name}' is not available to {shifter_type}", None
        
    return True, "", value

def validate_shifter_backgrounds(character, background_name: str, value: str) -> tuple[bool, str, str]:
    """Validate shifter backgrounds."""
    # Get list of available backgrounds
    from world.wod20th.utils.stat_mappings import UNIVERSAL_BACKGROUNDS, SHIFTER_BACKGROUNDS
    available_backgrounds = set(bg.title() for bg in UNIVERSAL_BACKGROUNDS + SHIFTER_BACKGROUNDS)
    
    if background_name.title() not in available_backgrounds:
        return False, f"Invalid background '{background_name}'. Available backgrounds: {', '.join(sorted(available_backgrounds))}", None
    
    # Validate value
    try:
        bg_value = int(value)
        if bg_value < 0 or bg_value > 5:
            return False, "Background values must be between 0 and 5", None
        return True, "", value
    except ValueError:
        return False, "Background values must be numbers", None