"""
Utility functions for handling Vampire-specific character initialization and updates.
"""
from world.wod20th.utils.banality import get_default_banality
from world.wod20th.utils.stat_mappings import BLOOD_POOL_MAP, UNIVERSAL_BACKGROUNDS, VAMPIRE_BACKGROUNDS
from world.wod20th.utils.virtue_utils import PATH_VIRTUES, calculate_willpower, calculate_path
from world.wod20th.utils.sheet_constants import PATHS_OF_ENLIGHTENMENT
from typing import Dict, List, Optional, Tuple, Set

# Valid vampire clans
CLAN_CHOICES: List[Tuple[str, str]] = [
    ('brujah', 'Brujah'),
    ('brujah antitribu', 'Brujah Antitribu'),
    ('gangrel', 'Gangrel'),
    ('city gangrel', 'City Gangrel'),
    ('country gangrel', 'Country Gangrel'),
    ('malkavian', 'Malkavian'),
    ('malkavian antitribu', 'Malkavian Antitribu'),
    ('nosferatu', 'Nosferatu'),
    ('nosferatu antitribu', 'Nosferatu Antitribu'),
    ('toreador', 'Toreador'),
    ('toreador antitribu', 'Toreador Antitribu'),
    ('tremere', 'Tremere'),
    ('tremere antitribu', 'Tremere Antitribu'),
    ('ventrue', 'Ventrue'),
    ('ventrue antitribu', 'Ventrue Antitribu'),
    ('lasombra', 'Lasombra'),
    ('lasombra antitribu', 'Lasombra Antitribu'),
    ('tzimisce', 'Tzimisce'),
    ('old clan tzimisce', 'Old Clan Tzimisce'),
    ('assamite', 'Assamite'),
    ('assamite antitribu', 'Assamite Antitribu'),
    ('followers of set', 'Followers of Set'),
    ('serpents of light', 'Serpents of Light'),
    ('ravnos', 'Ravnos'),
    ('ravnos antitribu', 'Ravnos Antitribu'),
    ('baali', 'Baali'),
    ('giovanni', 'Giovanni'),
    ('blood brothers', 'Blood Brothers'),
    ('daughters of cacophony', 'Daughters of Cacophony'),
    ('cappadocians', 'Cappadocians'),
    ('children of osiris', 'Children of Osiris'),
    ('panders', 'Panders'),
    ('laibon', 'Laibon'),
    ('lamia', 'Lamia'),
    ('bushi', 'Bushi'),
    ('ahrimanes', 'Ahrimanes'),
    ('caitiff', 'Caitiff'),
    ('gargoyles', 'Gargoyles'),
    ('kiasyd', 'Kiasyd'),
    ('nagaraja', 'Nagaraja'),
    ('salubri', 'Salubri'),
    ('samedi', 'Samedi'),
    ('harbingers of skulls', 'Harbingers of Skulls'),
    ('true brujah', 'True Brujah'),
    ('none', 'None')
]

# Keep the set for easy lookups
CLAN: Set[str] = {t[1] for t in CLAN_CHOICES if t[1] != 'None'}

__all__ = [
    'CLAN_CHOICES',
    'get_clan_disciplines',
    'get_path_virtues',
    'initialize_vampire_stats',
    'update_vampire_virtues_on_path_change',
    'update_vampire_pools_on_stat_change'
]

def get_clan_disciplines(clan):
    """Helper function to get clan disciplines."""
    CLAN_DISCIPLINES = {
        'Ahrimanes': ['Animalism', 'Presence', 'Spiritus'],
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

def get_vampire_identity_stats() -> List[str]:
    """Get the list of identity stats for a vampire character."""
    return [
        'Full Name',
        'Nature',
        'Demeanor', 
        'Concept',
        'Date of Birth',
        'Date of Embrace',
        'Generation',
        'Clan',
        'Sire',
        'Path of Enlightenment'
    ]

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
    if clan and clan.lower() in ['tremere', 'tremere antitribu']:
        character.db.stats['powers']['thaumaturgy'] = {}
    
    if clan and clan.lower() in ['giovanni', 'nagaraja', 'samedi']:
        character.db.stats['powers']['necromancy'] = {}

    # Initialize pools category if it doesn't exist
    if 'pools' not in character.db.stats:
        character.db.stats['pools'] = {}
    if 'dual' not in character.db.stats['pools']:
        character.db.stats['pools']['dual'] = {}

    # Set default Banality based on clan
    if clan:
        # Convert clan to proper case using CLAN_CHOICES
        clan_key = clan.lower() if clan else None
        proper_clan = next((t[1] for t in CLAN_CHOICES if t[0] == clan_key), None)
        
        if proper_clan:
            banality = get_default_banality('Vampire', subtype=proper_clan)
            if banality:
                character.set_stat('pools', 'dual', 'Banality', banality, temp=False)
                character.set_stat('pools', 'dual', 'Banality', banality, temp=True)
                character.msg(f"|gBanality set to {banality} for {proper_clan}.")
        else:
            valid_clans = [t[1] for t in CLAN_CHOICES if t[1] != 'None']
            character.msg(f"|rWarning: {clan} is not a valid clan. Please choose from: {', '.join(sorted(valid_clans))}|n")
            # Set default vampire banality
            banality = get_default_banality('Vampire')
            character.set_stat('pools', 'dual', 'Banality', banality, temp=False)
            character.set_stat('pools', 'dual', 'Banality', banality, temp=True)
            character.msg(f"|gDefault vampire Banality set to {banality}.")
    else:
        # Set default vampire banality even if no clan is provided
        banality = get_default_banality('Vampire')
        character.set_stat('pools', 'dual', 'Banality', banality, temp=False)
        character.set_stat('pools', 'dual', 'Banality', banality, temp=True)
        character.msg(f"|gDefault vampire Banality set to {banality}.")
    
    # Ensure default generation is set (13th)
    if 'Generation' not in character.db.stats['identity']['lineage']:
        character.db.stats['identity']['lineage']['Generation'] = {'perm': '13th', 'temp': '13th'}
    
    # Initialize backgrounds category if it doesn't exist
    if 'backgrounds' not in character.db.stats:
        character.db.stats['backgrounds'] = {}
    if 'background' not in character.db.stats['backgrounds']:
        character.db.stats['backgrounds']['background'] = {}
        
    if 'Generation' not in character.db.stats['backgrounds']['background']:
        character.db.stats['backgrounds']['background']['Generation'] = {'perm': 0, 'temp': 0}
    
    # Set blood pool based on generation background value
    gen_background = character.get_stat('backgrounds', 'background', 'Generation', temp=False) or 0
    blood_pool = calculate_blood_pool(gen_background)
    character.set_stat('pools', 'dual', 'Blood', blood_pool, temp=False)
    character.set_stat('pools', 'dual', 'Blood', blood_pool, temp=True)
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 1, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 1, temp=True)
    
    # Initialize virtues
    if 'virtues' not in character.db.stats:
        character.db.stats['virtues'] = {}
    if 'moral' not in character.db.stats['virtues']:
        character.db.stats['virtues']['moral'] = {}
    
    # Get path of enlightenment
    path = character.get_stat('identity', 'personal', 'Path of Enlightenment', temp=False) or 'Humanity'
    
    # Set appropriate virtues based on path
    if path in PATH_VIRTUES:
        virtue1, virtue2 = PATH_VIRTUES[path]
        # Initialize both virtues to 1
        character.set_stat('virtues', 'moral', virtue1, 1, temp=False)
        character.set_stat('virtues', 'moral', virtue2, 1, temp=False)
        character.set_stat('virtues', 'moral', virtue1, 1, temp=True)
        character.set_stat('virtues', 'moral', virtue2, 1, temp=True)
    else:
        # Default to Humanity virtues
        character.set_stat('virtues', 'moral', 'Conscience', 1, temp=False)
        character.set_stat('virtues', 'moral', 'Self-Control', 1, temp=False)
        character.set_stat('virtues', 'moral', 'Conscience', 1, temp=True)
        character.set_stat('virtues', 'moral', 'Self-Control', 1, temp=True)
    
    # Always set Courage
    character.set_stat('virtues', 'moral', 'Courage', 1, temp=False)
    character.set_stat('virtues', 'moral', 'Courage', 1, temp=True)
    
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

def update_vampire_virtues_on_path_change(character, new_path):
    """Update virtues when a vampire's path changes."""
    if new_path in PATH_VIRTUES:
        # Get the virtues for the new path
        virtue1, virtue2 = PATH_VIRTUES[new_path]
        
        # Initialize the new virtues if they don't exist
        if virtue1 not in character.db.stats.get('virtues', {}).get('moral', {}):
            character.set_stat('virtues', 'moral', virtue1, 1, temp=False)
            character.set_stat('virtues', 'moral', virtue1, 1, temp=True)
        if virtue2 not in character.db.stats.get('virtues', {}).get('moral', {}):
            character.set_stat('virtues', 'moral', virtue2, 1, temp=False)
            character.set_stat('virtues', 'moral', virtue2, 1, temp=True)
        
        # Remove old virtues that aren't used by the new path
        old_virtues = set(character.db.stats.get('virtues', {}).get('moral', {}).keys())
        path_virtues = {virtue1, virtue2, 'Courage'}  # Keep Courage
        virtues_to_remove = old_virtues - path_virtues
        
        for virtue in virtues_to_remove:
            if virtue in character.db.stats['virtues']['moral']:
                del character.db.stats['virtues']['moral'][virtue]
        
        character.msg(f"|gVirtues updated for {new_path}.|n")
    else:
        # Default to Humanity virtues
        character.set_stat('virtues', 'moral', 'Conscience', 1, temp=False)
        character.set_stat('virtues', 'moral', 'Self-Control', 1, temp=False)
        character.set_stat('virtues', 'moral', 'Conscience', 1, temp=True)
        character.set_stat('virtues', 'moral', 'Self-Control', 1, temp=True)
        character.msg("|gVirtues reset to Humanity defaults.|n") 

def update_vampire_pools_on_stat_change(character, stat_name: str, new_value: str) -> None:
    """Update vampire pools when relevant stats change."""
    stat_name = stat_name.lower()
    
    # Update blood pool when generation changes
    if stat_name == 'generation':
        try:
            gen_value = int(new_value)
            blood_pool = BLOOD_POOL_MAP.get(gen_value, 10)  # Default to 10 for unknown generations
            character.set_stat('pools', 'dual', 'Blood', blood_pool, temp=False)
            character.set_stat('pools', 'dual', 'Blood', blood_pool, temp=True)
            character.msg(f"|gBlood pool set to {blood_pool} based on generation {new_value}.|n")
        except ValueError:
            character.msg("|rError updating blood pool - invalid generation value.|n")
            return
    
    # Update virtues when path changes
    elif stat_name == 'path of enlightenment':
        if new_value in PATH_VIRTUES:
            virtue1, virtue2 = PATH_VIRTUES[new_value]
            # Initialize the new virtues if they don't exist
            if virtue1 not in character.db.stats.get('virtues', {}).get('moral', {}):
                character.set_stat('virtues', 'moral', virtue1, 1, temp=False)
                character.set_stat('virtues', 'moral', virtue1, 1, temp=True)
            if virtue2 not in character.db.stats.get('virtues', {}).get('moral', {}):
                character.set_stat('virtues', 'moral', virtue2, 1, temp=False)
                character.set_stat('virtues', 'moral', virtue2, 1, temp=True)
            
            # Remove old virtues that aren't used by the new path
            old_virtues = set(character.db.stats.get('virtues', {}).get('moral', {}).keys())
            path_virtues = {virtue1, virtue2, 'Courage'}  # Keep Courage
            virtues_to_remove = old_virtues - path_virtues
            
            for virtue in virtues_to_remove:
                if virtue in character.db.stats['virtues']['moral']:
                    del character.db.stats['virtues']['moral'][virtue]
            
            character.msg(f"|gVirtues updated for {new_value}.|n")
        else:
            # Default to Humanity virtues
            character.set_stat('virtues', 'moral', 'Conscience', 1, temp=False)
            character.set_stat('virtues', 'moral', 'Self-Control', 1, temp=False)
            character.set_stat('virtues', 'moral', 'Conscience', 1, temp=True)
            character.set_stat('virtues', 'moral', 'Self-Control', 1, temp=True)
            character.msg("|gVirtues reset to Humanity defaults.|n")

def validate_vampire_stats(character, stat_name: str, value: str, category: str = None, stat_type: str = None) -> tuple[bool, str]:
    """
    Validate vampire-specific stats.
    Returns (is_valid, error_message)
    """
    stat_name = stat_name.lower()
    
    # Validate clan
    if stat_name == 'clan':
        return validate_vampire_clan(value)
        
    # Validate generation
    elif stat_name == 'generation':
        return validate_vampire_generation(value)
        
    # Validate disciplines
    elif category == 'powers' and stat_type == 'discipline':
        return validate_vampire_discipline(character, stat_name, value)
        
    # Validate backgrounds
    elif category == 'backgrounds' and stat_type == 'background':
        return validate_vampire_background(stat_name, value)
    
    # Validate path of enlightenment
    elif (stat_name == 'path of enlightenment' or 
          (stat_name == 'path' and stat_type == 'enlightenment') or 
          (stat_name == 'path' and category == 'identity' and stat_type == 'personal') or
          (stat_name == 'path' and category == 'identity' and stat_type == 'enlightenment')):
        # Special case for Humanity
        if value and value.title() == 'Humanity':
            return True, ""
        # Check both formats - with and without "Path of" prefix
        value_title = value.title() if value else ''
        full_path = f"Path of {value_title}" if not value_title.startswith('Path of') else value_title
        short_path = value_title.replace('Path of ', '') if value_title.startswith('Path of') else value_title
        
        # Check against both PATH_VIRTUES and PATHS_OF_ENLIGHTENMENT
        if (short_path in PATH_VIRTUES or 
            full_path in PATHS_OF_ENLIGHTENMENT.values() or 
            short_path in PATHS_OF_ENLIGHTENMENT.values()):
            return True, ""
        
        # Get all valid paths
        valid_paths = set(PATH_VIRTUES.keys()) | set(PATHS_OF_ENLIGHTENMENT.values())
        error_msg = f"Invalid path. Valid paths are: {', '.join(sorted(valid_paths))}"
        return False, error_msg
    
    # Return True for any other stats
    return True, ""

def validate_vampire_clan(value: str) -> tuple[bool, str]:
    """Validate a vampire clan."""
    value = value.title()
    if value not in CLAN:
        return False, f"Invalid clan. Valid clans are: {', '.join(sorted(CLAN))}"
    return True, ""

def validate_vampire_generation(value: str) -> tuple[bool, str]:
    """Validate a vampire's generation."""
    try:
        gen_value = int(value)
        if gen_value < 6 or gen_value > 15:
            return False, "Generation must be between 6 and 15"
        return True, ""
    except ValueError:
        return False, "Generation must be a number"

def validate_vampire_discipline(character, discipline_name: str, value: str) -> tuple[bool, str]:
    """Validate vampire disciplines."""
    # Get character's clan
    clan = character.get_stat('identity', 'lineage', 'Clan', temp=False)
    if not clan:
        return False, "Character must have a clan set to learn disciplines"
    
    # Get clan disciplines
    clan_disciplines = get_clan_disciplines(clan)
    if not clan_disciplines:
        return False, f"No disciplines found for clan {clan}"
    
    # Check if discipline is available to clan (case-sensitive)
    if discipline_name not in clan_disciplines:
        # Try case-insensitive match
        discipline_lower = discipline_name.lower()
        clan_disciplines_lower = [d.lower() for d in clan_disciplines]
        if discipline_lower in clan_disciplines_lower:
            # Find the correctly cased version
            index = clan_disciplines_lower.index(discipline_lower)
            discipline_name = clan_disciplines[index]
        else:
            return False, f"'{discipline_name}' is not available to {clan}. Available disciplines: {', '.join(clan_disciplines)}"
    
    # Validate value
    try:
        disc_value = int(value)
        if disc_value < 0 or disc_value > 5:
            return False, "Discipline values must be between 0 and 5"
        return True, ""
    except ValueError:
        return False, "Discipline values must be numbers"

def validate_vampire_background(background_name: str, value: str) -> tuple[bool, str]:
    """Validate vampire backgrounds."""
    # Get list of available backgrounds
    available_backgrounds = set(bg.title() for bg in UNIVERSAL_BACKGROUNDS + VAMPIRE_BACKGROUNDS)
    
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

def validate_vampire_gift(character, gift_name: str, value: str) -> tuple[bool, str]:
    """Validate a vampire gift."""
    # Import Stat here to avoid circular import
    from world.wod20th.models import Stat
    
    # Check if the gift exists in the database
    gift = Stat.objects.filter(
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

def validate_vampire_path(value: str) -> tuple[bool, str]:
    """Validate a vampire's path of enlightenment."""
    # Convert value to title case for comparison
    value = value.title() if value else ''  # Convert empty string to empty string
    print(f"\nValidating vampire path: {value}")
    print(f"PATH_VIRTUES keys: {sorted(PATH_VIRTUES.keys())}")
    print(f"PATHS_OF_ENLIGHTENMENT values: {sorted(PATHS_OF_ENLIGHTENMENT.values())}")
    
    # Empty path is invalid
    if not value:
        return False, "Path cannot be empty"
    
    # Special case for Humanity
    if value == 'Humanity':
        return True, ""
    
    # Check both formats - with and without "Path of" prefix
    full_path = f"Path of {value}" if not value.startswith('Path of') else value
    short_path = value.replace('Path of ', '') if value.startswith('Path of') else value
    
    # Check against both PATH_VIRTUES and PATHS_OF_ENLIGHTENMENT
    if (short_path in PATH_VIRTUES or 
        full_path in PATHS_OF_ENLIGHTENMENT.values() or 
        short_path in PATHS_OF_ENLIGHTENMENT.values()):
        print(f"Path {value} is valid")
        return True, ""
    
    # Get all valid paths
    valid_paths = set(PATH_VIRTUES.keys()) | set(PATHS_OF_ENLIGHTENMENT.values())
    error_msg = f"Invalid path. Valid paths are: {', '.join(sorted(valid_paths))}"
    print(f"Path {value} is invalid. {error_msg}")
    return False, error_msg 