"""
Utility functions for handling Mortal+-specific character initialization and updates.
"""
from world.wod20th.utils.stat_mappings import ARTS, REALMS
from world.wod20th.utils.vampire_utils import get_clan_disciplines
from world.wod20th.utils.banality import get_default_banality
from typing import Dict, List, Tuple

def get_stat_model():
    """Get the Stat model lazily to avoid circular imports."""
    from world.wod20th.models import Stat
    return Stat

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

# Keep the set for easy lookups
MORTALPLUS_TYPES_SET = {t[1] for t in MORTALPLUS_TYPE_CHOICES if t[1] != 'None'}

# Mock ARTS and REALMS for testing if not defined
if 'ARTS' not in globals():
    ARTS = {'Chicanery', 'Primal', 'Wayfare'}
if 'REALMS' not in globals():
    REALMS = {'Actor', 'Fae', 'Nature', 'Prop', 'Scene', 'Time'}

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
        'Disciplines': ['Dominate', 'Presence', 'Obfuscate', 'Protean', 'Thaumaturgy', 'Viscissitude', 
                       'Celerity', 'Obfuscate', 'Quietus', 'Potence', 'Presence', 'Animalism', 
                       'Protean', 'Fortitude', 'Serpentis', 'Necromancy', 'Obtenebration', 
                       'Auspex', 'Dementation', 'Chimerstry', 'Thaumaturgy', 'Vicissitude']
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
    if 'personal' not in character.db.stats['identity']:
        character.db.stats['identity']['personal'] = {}
    if 'lineage' not in character.db.stats['identity']:
        character.db.stats['identity']['lineage'] = {}
    if 'legacy' not in character.db.stats['identity']:
        character.db.stats['identity']['legacy'] = {}
    
    # Initialize powers category if it doesn't exist
    if 'powers' not in character.db.stats:
        character.db.stats['powers'] = {}
    
    # Initialize pools
    if 'pools' not in character.db.stats:
        character.db.stats['pools'] = {}
    if 'dual' not in character.db.stats['pools']:
        character.db.stats['pools']['dual'] = {}
    if 'other' not in character.db.stats['pools']:
        character.db.stats['pools']['other'] = {}
    
    # Set the type in identity/lineage
    character.set_stat('identity', 'lineage', 'Type', mortalplus_type, temp=False)
    character.set_stat('identity', 'lineage', 'Type', mortalplus_type, temp=True)
    
    # Initialize type-specific stats
    if mortalplus_type == 'Ghoul':
        # Initialize disciplines category
        character.db.stats['powers']['discipline'] = {}
        # Set blood pool
        character.set_stat('pools', 'dual', 'Blood', 3, temp=False)
        character.set_stat('pools', 'dual', 'Blood', 3, temp=True)
        
    elif mortalplus_type == 'Kinain':
        # Initialize arts and realms categories
        character.db.stats['powers']['art'] = {}
        character.db.stats['powers']['realm'] = {}
        
        # Set base Glamour and Banality
        character.set_stat('pools', 'dual', 'Glamour', 2, temp=False)
        character.set_stat('pools', 'dual', 'Glamour', 2, temp=True)
        character.set_stat('pools', 'dual', 'Banality', 3, temp=False)
        character.set_stat('pools', 'dual', 'Banality', 0, temp=True)
        
        # Initialize House and Legacy fields
        character.set_stat('identity', 'lineage', 'House', '', temp=False)
        character.set_stat('identity', 'lineage', 'House', '', temp=True)
        character.set_stat('identity', 'lineage', 'First Legacy', '', temp=False)
        character.set_stat('identity', 'lineage', 'First Legacy', '', temp=True)
        character.set_stat('identity', 'lineage', 'Second Legacy', '', temp=False)
        character.set_stat('identity', 'lineage', 'Second Legacy', '', temp=True)
        character.set_stat('identity', 'lineage', 'Affinity Realm', '', temp=False)
        character.set_stat('identity', 'lineage', 'Affinity Realm', '', temp=True)
        
    elif mortalplus_type == 'Sorcerer':
        # Initialize sorcery and hedge ritual categories
        character.db.stats['powers']['sorcery'] = {}
        character.db.stats['powers']['hedge_ritual'] = {}
        
    elif mortalplus_type == 'Psychic':
        # Initialize numina category
        character.db.stats['powers']['numina'] = {}
        
    elif mortalplus_type == 'Faithful':
        # Initialize faith category
        character.db.stats['powers']['faith'] = {}
        
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)

def initialize_ghoul_stats(character):
    """Initialize Ghoul-specific stats."""
    # Initialize powers categories if they don't exist
    if 'powers' not in character.db.stats:
        character.db.stats['powers'] = {}
    if 'discipline' not in character.db.stats['powers']:
        character.db.stats['powers']['discipline'] = {}
    
    # Set base Blood Pool and Willpower
    character.set_stat('pools', 'dual', 'Blood', 3, temp=False)
    character.set_stat('pools', 'dual', 'Blood', 3, temp=True)
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)

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

def get_kinain_identity_stats() -> List[str]:
    """Get the list of identity stats for a Kinain character."""
    return [
        'Full Name',
        'Concept',
        'Date of Birth',
        'Fae Name',
        'First Legacy',
        'Second Legacy',
        'Affinity Realm'
    ]

def get_mortalplus_identity_stats(mortalplus_type: str) -> List[str]:
    """Get the list of identity stats for a Mortal+ character based on type."""
    base_stats = [
        'Full Name',
        'Nature',
        'Demeanor',
        'Concept',
        'Date of Birth'
    ]
    
    if mortalplus_type == 'Ghoul':
        return base_stats + [
            'Domitor',
            'Path of Enlightenment',
        ]
    elif mortalplus_type == 'Kinain':
        return base_stats + [
            'Fae Name',
            'First Legacy',
            'Second Legacy',
            'Affinity Realm'
        ]
    elif mortalplus_type == 'Kinfolk':
        return base_stats + [
            'Tribe',
            'Pack',
            'Patron Totem'
        ]
    elif mortalplus_type == 'Sorcerer':
        return base_stats + [
            'Society',
            'Order',
            'Coven'
        ]
    elif mortalplus_type == 'Psychic':
        return base_stats + [
            'Society'
        ]
    elif mortalplus_type == 'Faithful':
        return base_stats + [
            'Order'
        ]
    
    return base_stats

def initialize_kinain_stats(character):
    """Initialize Kinain-specific stats."""
    # Initialize identity categories if they don't exist
    if 'identity' not in character.db.stats:
        character.db.stats['identity'] = {}
    if 'personal' not in character.db.stats['identity']:
        character.db.stats['identity']['personal'] = {}
    if 'legacy' not in character.db.stats['identity']:
        character.db.stats['identity']['legacy'] = {}
    
    # Set base Glamour
    character.set_stat('pools', 'dual', 'Glamour', 2, temp=False)
    character.set_stat('pools', 'dual', 'Glamour', 2, temp=True)
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
    
    # Initialize Arts and Realms categories (empty until Fae Blood Merit)
    if 'powers' not in character.db.stats:
        character.db.stats['powers'] = {}
    if 'art' not in character.db.stats['powers']:
        character.db.stats['powers']['art'] = {}
    if 'realm' not in character.db.stats['powers']:
        character.db.stats['powers']['realm'] = {}
    
    # Initialize Affinity Realm in identity/lineage
    if 'identity' not in character.db.stats:
        character.db.stats['identity'] = {}
    if 'lineage' not in character.db.stats['identity']:
        character.db.stats['identity']['lineage'] = {}
    character.set_stat('identity', 'lineage', 'Affinity Realm', '', temp=False)
    character.set_stat('identity', 'lineage', 'Affinity Realm', '', temp=True)

def initialize_sorcerer_stats(character):
    """Initialize Sorcerer-specific stats."""
    # Initialize powers categories if they don't exist
    if 'powers' not in character.db.stats:
        character.db.stats['powers'] = {}
    if 'sorcery' not in character.db.stats['powers']:
        character.db.stats['powers']['sorcery'] = {}
    if 'hedge_ritual' not in character.db.stats['powers']:
        character.db.stats['powers']['hedge_ritual'] = {}
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 5, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 5, temp=True)
    
    # Set base Mana
    character.set_stat('pools', 'dual', 'Mana', 0, temp=False)
    character.set_stat('pools', 'dual', 'Mana', 0, temp=True)

def initialize_psychic_stats(character):
    """Initialize Psychic-specific stats."""
    # Initialize powers categories if they don't exist
    if 'powers' not in character.db.stats:
        character.db.stats['powers'] = {}
    if 'numina' not in character.db.stats['powers']:
        character.db.stats['powers']['numina'] = {}
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 5, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 5, temp=True)

def initialize_faithful_stats(character):
    """Initialize Faithful-specific stats."""
    # Initialize powers categories if they don't exist
    if 'powers' not in character.db.stats:
        character.db.stats['powers'] = {}
    if 'faith' not in character.db.stats['powers']:
        character.db.stats['powers']['faith'] = {}
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 5, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 5, temp=True)

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
            has_gift_merit = any(merit.lower() == 'gifted kinfolk' 
                               for merit in merits.keys())
            if not has_gift_merit:
                return False, "Kinfolk must have the 'Gifted Kinfolk' Merit to learn Gifts"

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
            backgrounds = character.db.stats.get('backgrounds', {}).get('background', {})
            kinain_background = next((background_value.get('perm', 0) 
                             for background, background_value in backgrounds.items() 
                               if background.lower() == 'faerie blood'), 0)
            
            # Calculate maximums based on Merit level
            max_arts = kinain_background
            
            if power_type == 'Arts' and len(character.get_all_powers('Arts')) >= max_arts:
                return False, f"Kinain can only learn {max_arts} Arts with current Faerie Blood background level"

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

def validate_mortalplus_type(value: str) -> tuple[bool, str]:
    """Validate a mortal+ type."""
    if value.title() not in MORTALPLUS_TYPES_SET:
        return False, f"Invalid mortal+ type. Valid types are: {', '.join(sorted(MORTALPLUS_TYPES_SET))}"
    return True, ""

def validate_mortalplus_stats(character, stat_name: str, value: str, category: str = None, stat_type: str = None) -> tuple[bool, str]:
    """
    Validate mortal+-specific stats.
    Returns (is_valid, error_message)
    """
    stat_name = stat_name.lower()
    
    # Get mortal+ type
    mortalplus_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
    
    # Validate type
    if stat_name == 'type':
        return validate_mortalplus_type(value)
        
    # Special handling for Path of Enlightenment/Enlightenment for Ghouls
    if mortalplus_type == 'Ghoul' and stat_name in ['path of enlightenment', 'enlightenment']:
        from world.wod20th.utils.vampire_utils import validate_vampire_path
        return validate_vampire_path(value)
        
    # Validate powers
    if category == 'powers':
        if mortalplus_type == 'Ghoul':
            if stat_type == 'discipline':
                return validate_ghoul_disciplines(character, stat_name, value)
        elif mortalplus_type == 'Kinfolk':
            if stat_type == 'gift':
                return validate_kinfolk_gifts(character, stat_name, value)
        elif mortalplus_type == 'Kinain':
            if stat_type in ['art', 'realm']:
                return validate_kinain_powers(character, stat_name, value, stat_type)
        elif mortalplus_type == 'Sorcerer':
            if stat_type == 'sorcery':
                return validate_sorcerer_powers(character, stat_name, value)
        elif mortalplus_type == 'Psychic':
            if stat_type == 'numina':
                return validate_psychic_powers(character, stat_name, value)
        elif mortalplus_type == 'Faithful':
            if stat_type == 'faith':
                return validate_faithful_powers(character, stat_name, value)
    
    # Validate backgrounds
    if category == 'backgrounds' and stat_type == 'background':
        return validate_mortalplus_backgrounds(character, stat_name, value)
    
    return True, ""

def validate_ghoul_disciplines(character, discipline_name: str, value: str) -> tuple[bool, str]:
    """Validate a ghoul's disciplines."""
    # Get character's domitor
    domitor = character.get_stat('identity', 'personal', 'Domitor', temp=False)
    if not domitor:
        return False, "Ghouls must have a domitor set to learn disciplines"
    
    # Get domitor's clan
    clan = character.get_stat('identity', 'lineage', 'Clan', temp=False)
    if not clan:
        return False, "Ghoul's clan must be set to learn disciplines"
    
    # Get clan disciplines
    clan_disciplines = get_clan_disciplines(clan)
    if not clan_disciplines:
        return False, f"No disciplines found for clan {clan}"
    
    # Case-insensitive comparison
    discipline_name = discipline_name.title()
    if discipline_name not in clan_disciplines:
        return False, f"'{discipline_name}' is not available to {clan} ghouls. Available disciplines: {', '.join(clan_disciplines)}"
    
    # Validate value
    try:
        disc_value = int(value)
        if disc_value < 0 or disc_value > 5:
            return False, "Discipline values must be between 0 and 5"
        return True, ""
    except ValueError:
        return False, "Discipline values must be numbers"

def validate_kinfolk_gifts(character, gift_name: str, value: str) -> tuple[bool, str]:
    """Validate a kinfolk's gifts."""
    # Check for Gift Merit
    merit_value = character.get_stat('merits', 'merit', 'Gifted Kinfolk', temp=False)
    if not merit_value or not isinstance(merit_value, dict):
        return False, "Kinfolk must have the 'Gifted Kinfolk' Merit to learn Gifts"
    
    # Check if the gift exists in the database
    gift = get_stat_model().objects.filter(
        name__iexact=gift_name,
        category='powers',
        stat_type='gift'
    ).first()
    
    if not gift:
        return False, f"'{gift_name}' is not a valid gift"
    
    # Validate value
    try:
        gift_value = int(value)
        if gift_value < 0 or gift_value > 5:
            return False, "Gift values must be between 0 and 5"
        return True, ""
    except ValueError:
        return False, "Gift values must be numbers"

def validate_kinain_powers(character, power_name: str, value: str, power_type: str) -> tuple[bool, str]:
    """Validate a kinain's arts and realms."""
    # Get Faerie Blood background level
    faerie_blood = character.get_stat('backgrounds', 'background', 'Faerie Blood', temp=False) or 0
    
    # Calculate maximums based on Faerie Blood level
    max_arts = {
        0: 1,  # Can take 1 Art at Faerie Blood 0
        1: 2,  # Can take 2 Arts at Faerie Blood 1
        2: 3,  # Can take 3 Arts at Faerie Blood 2
        3: 4,  # Can take 4 Arts at Faerie Blood 3
        4: 5,  # Can take 5 Arts at Faerie Blood 4
        5: 6   # Can take 6 Arts at Faerie Blood 5
    }[faerie_blood]
    
    max_art_dots = 5  # Kinain are limited to 5 dots in any Art
    
    if power_type == 'art':
        # Check if art exists
        if power_name not in ARTS:
            return False, f"Invalid art. Valid arts are: {', '.join(sorted(ARTS))}"
        
        # Check number of arts
        current_arts = len([art for art, values in character.get_stat('powers', 'art', None, temp=False).items() 
                          if values.get('perm', 0) > 0])
        
        # If this is a new art (value > 0 and not currently known)
        current_art_value = character.get_stat('powers', 'art', power_name, temp=False) or 0
        if int(value) > 0 and current_art_value == 0:
            if current_arts >= max_arts:
                return False, f"Kinain with Faerie Blood {faerie_blood} can only learn {max_arts} Arts"
        
        # Validate value
        try:
            art_value = int(value)
            if art_value < 0 or art_value > max_art_dots:
                return False, f"Art values for Kinain must be between 0 and {max_art_dots}"
            return True, ""
        except ValueError:
            return False, "Art values must be numbers"
            
    elif power_type == 'realm':
        # Check if realm exists
        if power_name not in REALMS:
            return False, f"Invalid realm. Valid realms are: {', '.join(sorted(REALMS))}"
        
        # Validate value
        try:
            realm_value = int(value)
            if realm_value < 0 or realm_value > max_art_dots:
                return False, f"Realm values for Kinain must be between 0 and {max_art_dots}"
            return True, ""
        except ValueError:
            return False, "Realm values must be numbers"
    
    return False, f"Invalid power type: {power_type}"

def validate_sorcerer_powers(character, power_name: str, value: str) -> tuple[bool, str]:
    """Validate a sorcerer's powers."""
    # Check if the power exists in the database
    power = get_stat_model().objects.filter(
        name__iexact=power_name,
        category='powers',
        stat_type='sorcery'
    ).first()
    
    if not power:
        return False, f"'{power_name}' is not a valid sorcery power"
    
    # Validate value
    try:
        power_value = int(value)
        if power_value < 0 or power_value > 5:
            return False, "Sorcery values must be between 0 and 5"
        return True, ""
    except ValueError:
        return False, "Sorcery values must be numbers"

def validate_psychic_powers(character, power_name: str, value: str) -> tuple[bool, str]:
    """Validate a psychic's powers."""
    # Check if the power exists in the database
    power = get_stat_model().objects.filter(
        name__iexact=power_name,
        category='powers',
        stat_type='numina'
    ).first()
    
    if not power:
        return False, f"'{power_name}' is not a valid numina"
    
    # Validate value
    try:
        power_value = int(value)
        if power_value < 0 or power_value > 5:
            return False, "Numina values must be between 0 and 5"
        return True, ""
    except ValueError:
        return False, "Numina values must be numbers"

def validate_faithful_powers(character, power_name: str, value: str) -> tuple[bool, str]:
    """Validate a faithful's powers."""
    # Check if the power exists in the database
    power = get_stat_model().objects.filter(
        name__iexact=power_name,
        category='powers',
        stat_type='faith'
    ).first()
    
    if not power:
        return False, f"'{power_name}' is not a valid faith power"
    
    # Validate value
    try:
        power_value = int(value)
        if power_value < 0 or power_value > 5:
            return False, "Faith values must be between 0 and 5"
        return True, ""
    except ValueError:
        return False, "Faith values must be numbers"

def validate_mortalplus_backgrounds(character, background_name: str, value: str) -> tuple[bool, str]:
    """Validate mortal+ backgrounds."""
    # Get character's type
    mortalplus_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
    
    # Get list of available backgrounds
    from world.wod20th.utils.stat_mappings import UNIVERSAL_BACKGROUNDS
    available_backgrounds = set(bg.title() for bg in UNIVERSAL_BACKGROUNDS)
    
    # Add type-specific backgrounds
    if mortalplus_type == 'Sorcerer':
        from world.wod20th.utils.stat_mappings import SORCERER_BACKGROUNDS
        available_backgrounds.update(bg.title() for bg in SORCERER_BACKGROUNDS)
    
    if background_name.title() not in available_backgrounds:
        return False, f"Invalid background '{background_name}'. Available backgrounds: {', '.join(sorted(available_backgrounds))}"
    
    # Validate value
    try:
        bg_value = int(value)
        if bg_value < 0 or bg_value > 5:
            return False, "Background values must be between 0 and 5"
        return True, ""
    except ValueError:
        return False, "Background values must be numbers"

def update_mortalplus_pools_on_stat_change(character, stat_name: str, new_value: str) -> None:
    """
    Update mortal+ pools when relevant stats change.
    Called by CmdSelfStat after setting stats.
    """
    stat_name = stat_name.lower()
    
    # Get character's mortal+ type
    mortalplus_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
    if not mortalplus_type:
        return
    
    # Handle Type changes
    if stat_name == 'type':
        # Get default Banality based on mortal+ type
        banality = get_default_banality('Mortal+', subtype=new_value)
        if banality:
            character.set_stat('pools', 'dual', 'Banality', banality, temp=False)
            character.set_stat('pools', 'dual', 'Banality', banality, temp=True)
            character.msg(f"|gBanality set to {banality} for {new_value}.|n")
        
        # Set type-specific pools
        if new_value in MORTALPLUS_POOLS:
            pools = MORTALPLUS_POOLS[new_value]
            for pool_name, pool_data in pools.items():
                # Skip Willpower if it's already set to a non-zero value
                if pool_name == 'Willpower' and character.get_stat('pools', 'dual', 'Willpower', temp=False) > 0:
                    continue
                
                # Set both permanent and temporary values
                character.set_stat('pools', 'dual', pool_name, pool_data['default'], temp=False)
                character.set_stat('pools', 'dual', pool_name, pool_data['default'], temp=True)
                character.msg(f"|g{pool_name} set to {pool_data['default']} for {new_value}.|n")
    
    # Handle Gnosis Merit for Kinfolk
    elif stat_name == 'gnosis' and mortalplus_type == 'Kinfolk':
        try:
            merit_value = int(new_value)
            if merit_value >= 5:
                gnosis_value = min(3, max(1, merit_value - 4))  # 5->1, 6->2, 7->3
                character.set_stat('pools', 'dual', 'Gnosis', gnosis_value, temp=False)
                character.set_stat('pools', 'dual', 'Gnosis', gnosis_value, temp=True)
                character.msg(f"|gGnosis set to {gnosis_value} based on Merit value {merit_value}.|n")
        except (ValueError, TypeError):
            character.msg("|rError updating Gnosis pool - invalid Merit value.|n")
            return
    
    # Handle Fae Blood background for Kinain
    elif stat_name == 'faerie blood' and mortalplus_type == 'Kinain':
        try:
            bg_value = int(new_value)
            # Always set Glamour to 2 for Kinain (their maximum)
            character.set_stat('pools', 'dual', 'Glamour', 2, temp=False)
            character.set_stat('pools', 'dual', 'Glamour', 2, temp=True)
            character.msg("|gGlamour set to 2 (maximum for Kinain).|n")
            
            # Calculate maximum allowed Arts
            max_arts = {
                0: 1,  # Can take 1 Art at Faerie Blood 0
                1: 2,  # Can take 2 Arts at Faerie Blood 1
                2: 3,  # Can take 3 Arts at Faerie Blood 2
                3: 4,  # Can take 4 Arts at Faerie Blood 3
                4: 5,  # Can take 5 Arts at Faerie Blood 4
                5: 6   # Can take 6 Arts at Faerie Blood 5
            }[bg_value]
            
            character.msg(f"|gWith Faerie Blood {bg_value}, you can learn up to {max_arts} Arts at maximum rating 3.|n")
        except (ValueError, TypeError):
            character.msg("|rError updating pools - invalid Faerie Blood value.|n")
            return 