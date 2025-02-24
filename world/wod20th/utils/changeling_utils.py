"""
Utility functions for handling Changeling-specific character initialization and updates.
"""
from world.wod20th.utils.banality import get_default_banality
from world.wod20th.models import Stat
from world.wod20th.utils.stat_mappings import ARTS, REALMS
from typing import Dict, List, Set, Tuple

SEEMING = {'Childling', 'Wilder', 'Grump', 'Youngling', 'Brave', 'Elder'}

FAE_COURTS = {'Seelie Court', 'Unseelie Court'}

HOUSES = {
    "Beaumayn", "Dougal", "Eiluned", "Fiona", "Gwydion", "Liam", 
    "Scathach", "Aesin", "Ailil", "Balor", "Danaan", "Daireann", 
    "Leanhaun", "Varich"
}

KITH = {
    'Boggan', 'Clurichaun', 'Eshu', 'Nocker', 'Piskie', 'Pooka', 'Redcap', 'Satyr', 
    'Selkie', 'Arcadian Sidhe', 'Autumn Sidhe', 'Sluagh', 'Troll', 'Nunnehi', 'Inanimae',
    'Korred', 'River Hag', 'Swan Maiden', 'Encantado', 'Sachamama', 'Morganed', 'Alicanto',
    'Boraro', 'Llorona', 'Merfolk', 'Wichtel', 'Wolpertinger'
}

SEELIE_LEGACIES = {
    'Bumpkin', 'Courtier', 'Crafter', 'Dandy', 'Hermit', 'Orchid', 'Paladin', 'Panderer', 
    'Regent', 'Sage', 'Saint', 'Squire', 'Troubadour', 'Wayfarer'
}

UNSEELIE_LEGACIES = {
    'Beast', 'Fatalist', 'Fool', 'Grotesque', 'Knave', 'Outlaw', 'Pandora', 'Peacock', 'Rake', 'Riddler', 
    'Ringleader', 'Rogue', 'Savage', 'Wretch'
}

#Kinain use all legacies for their legacy 1 and legacy 2 stats regardless of court.
KINAIN_LEGACIES = {
    'Bumpkin', 'Courtier', 'Crafter', 'Dandy', 'Hermit', 'Orchid', 'Paladin', 'Panderer', 
    'Regent', 'Sage', 'Saint', 'Squire', 'Troubadour', 'Wayfarer', 'Beast', 'Fatalist', 
    'Fool', 'Grotesque', 'Knave', 'Outlaw', 'Pandora', 'Peacock', 'Rake', 'Riddler', 
    'Ringleader', 'Rogue', 'Savage', 'Wretch'
}

# Phyla (for Inanimae)
PHYLA = {
    'Kuberas', 'Ondines', 'Parosemes', 'Glomes', 'Solimonds', 'Mannikins'
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
NUNNEHI_SEEMING = {
    'Youngling', 'Brave', 'Elder'
}

NUNNEHI_CAMP = {
    'Winter People', 'Summer People', 'Midseason People'
}

NUNNEHI_FAMILY = {
    'Canotili',
    'Inuas',
    'Kachinas',
    'May-may-gwya-shi',
    "Numuzo'ho",
    'Rock giants',
    'Surems',
    'Water Babies',
    "Yunwi Amai'yine'hi",
    'Yunwi Tsundsi'
}

SUMMER_LEGACIES = {
    'Chief', 'Grower', 'Healer', 'Hunter', 'Maker', 'Scout', 'Spiritguide', 'Storyteller', 'Warrior', 'Wise One'
    }
MIDSEASON_LEGACIES = {
    'Trickster', 'Watcher'
}
WINTER_LEGACIES = {
    'Cannibal', 'Fool', 'Forked-Tongue', 'Hoarder', 'Outcast', 'Raider', 'Scalp-Taker', 'Spoiler', 'Troublemaker', 'Witch'
}

def get_changeling_identity_stats(kith: str = None) -> List[str]:
    """
    Get the list of identity stats for a changeling character.
    
    Args:
        kith: The character's kith, if known
        
    Returns:
        List of identity stats appropriate for the character's kith
    """
    # Base stats that all changelings have
    base_stats = [
        'Full Name',
        'Concept',
        'Date of Birth',
        'Date of Chrysalis',
        'Kith',
        'Seeming',
        'Fae Name'
    ]
    
    # Add kith-specific stats
    if kith:
        if kith.lower() == 'nunnehi':
            return base_stats + [
                'Summer Legacy',
                'Winter Legacy',
                'Nunnehi Seeming',
                'Nunnehi Camp',
                'Nunnehi Family',
                'Nunnehi Totem'
            ]
        elif kith.lower() == 'inanimae':
            return base_stats + [
                'Phyla',
                'Seelie Legacy',
                'Unseelie Legacy',
                'Fae Court'
            ]
    
    # Default stats for standard changelings
    return base_stats + [
        'House',
        'Fae Court',
        'Seelie Legacy',
        'Unseelie Legacy'
    ]

def initialize_glamour(seeming):
    """Calculate initial Glamour based on seeming."""
    seeming = seeming.lower() if seeming else ''
    if seeming == 'childling':
        return 5  # Base 4 + 1 for Childling
    elif seeming == 'wilder':
        return 4  # Base 4
    elif seeming == 'grump':
        return 4  # Base 4
    return 4  # Default value is 4

def adjust_pools_for_seeming(character, old_seeming, new_seeming):
    """
    Adjust Willpower and Glamour pools based on Seeming changes.
    
    Args:
        character: The character being modified
        old_seeming: The character's previous seeming (or None)
        new_seeming: The new seeming being set
    """
    # Handle Willpower adjustments for Grump
    current_willpower = character.get_stat('pools', 'dual', 'Willpower', temp=False) or 4
    
    # Remove Grump bonus if changing from Grump to something else
    if old_seeming and old_seeming.lower() == 'grump' and new_seeming.lower() != 'grump':
        # Only reduce if we previously added the bonus
        if current_willpower == 5:
            character.set_stat('pools', 'dual', 'Willpower', 4, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', 4, temp=True)
            character.msg("|yYour Willpower is set to base 4 as you are no longer a Grump.|n")
    
    # Add Grump bonus if changing to Grump
    elif new_seeming.lower() == 'grump' and (not old_seeming or old_seeming.lower() != 'grump'):
        character.set_stat('pools', 'dual', 'Willpower', 5, temp=False)
        character.set_stat('pools', 'dual', 'Willpower', 5, temp=True)
        character.msg("|gYour Willpower is set to 5 due to your Grump seeming.|n")
    
    # Handle Glamour adjustments for Childling
    current_glamour = character.get_stat('pools', 'dual', 'Glamour', temp=False) or 4
    
    # Remove Childling bonus if changing from Childling to something else
    if old_seeming and old_seeming.lower() == 'childling' and new_seeming.lower() != 'childling':
        # Only reduce if we previously added the bonus
        if current_glamour == 5:
            character.set_stat('pools', 'dual', 'Glamour', 4, temp=False)
            character.set_stat('pools', 'dual', 'Glamour', 4, temp=True)
            character.msg("|yYour Glamour is set to base 4 as you are no longer a Childling.|n")
    
    # Add Childling bonus if changing to Childling
    elif new_seeming.lower() == 'childling' and (not old_seeming or old_seeming.lower() != 'childling'):
        character.set_stat('pools', 'dual', 'Glamour', 5, temp=False)
        character.set_stat('pools', 'dual', 'Glamour', 5, temp=True)
        character.msg("|gYour Glamour is set to 5 due to your Childling seeming.|n")

def initialize_changeling_stats(character, kith):
    """Initialize specific stats for a changeling character."""
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
    
    # Add Arts and Realms categories
    character.db.stats['powers']['art'] = {}
    character.db.stats['powers']['realm'] = {}
    
    # Initialize all Arts to 0
    for art in ARTS:
        character.db.stats['powers']['art'][art] = {'perm': 0, 'temp': 0}
    
    # Initialize all Realms to 0
    for realm in REALMS:
        character.db.stats['powers']['realm'][realm] = {'perm': 0, 'temp': 0}
    
    # Initialize pools
    if 'pools' not in character.db.stats:
        character.db.stats['pools'] = {}
    if 'dual' not in character.db.stats['pools']:
        character.db.stats['pools']['dual'] = {}
    if 'other' not in character.db.stats['pools']:
        character.db.stats['pools']['other'] = {}
    
    # Set base pools
    character.db.stats['pools']['dual']['Willpower'] = {'perm': 4, 'temp': 4}
    character.db.stats['pools']['dual']['Glamour'] = {'perm': 4, 'temp': 4}
    
    # Set Nightmare and Willpower Imbalance in pools/other
    character.db.stats['pools']['other']['Nightmare'] = {'perm': 0, 'temp': 0}
    character.db.stats['pools']['other']['Willpower Imbalance'] = {'perm': 0, 'temp': 0}
    
    # Initialize merits and flaws categories
    if 'merits' not in character.db.stats:
        character.db.stats['merits'] = {}
    for category in ['physical', 'social', 'mental', 'supernatural']:
        if category not in character.db.stats['merits']:
            character.db.stats['merits'][category] = {}
            
    if 'flaws' not in character.db.stats:
        character.db.stats['flaws'] = {}
    for category in ['physical', 'social', 'mental', 'supernatural']:
        if category not in character.db.stats['flaws']:
            character.db.stats['flaws'][category] = {}
    
    # Set kith if provided
    if kith:
        # Store old seeming for pool adjustments
        old_seeming = character.get_stat('identity', 'lineage', 'Seeming', temp=False)
        
        character.set_stat('identity', 'lineage', 'Kith', kith, temp=False)
        character.set_stat('identity', 'lineage', 'Kith', kith, temp=True)
        
        # Special handling for Inanimae
        if kith.lower() == 'inanimae':
            # Initialize Inanimae-specific stats
            character.set_stat('identity', 'lineage', 'Phyla', '', temp=False)
            character.set_stat('identity', 'lineage', 'Phyla', '', temp=True)
            # Add Slivers category
            character.db.stats['powers']['sliver'] = {}
            
        # Special handling for Nunnehi
        elif kith.lower() == 'nunnehi':
            # Remove inappropriate stats
            for stat in ['Fae Court', 'House', 'Seelie Legacy', 'Unseelie Legacy']:
                if stat in character.db.stats['identity']['lineage']:
                    del character.db.stats['identity']['lineage'][stat]
                if stat in character.db.stats['identity']['legacy']:
                    del character.db.stats['identity']['legacy'][stat]
            
            # Initialize Nunnehi-specific stats
            lineage_stats = {
                'Nunnehi Seeming': '',
                'Nunnehi Camp': '',
                'Nunnehi Family': '',
                'Nunnehi Totem': ''
            }
            for stat, value in lineage_stats.items():
                character.set_stat('identity', 'lineage', stat, value, temp=False)
                character.set_stat('identity', 'lineage', stat, value, temp=True)
                
            # Initialize Nunnehi legacies in the correct category/type
            legacy_stats = {
                'Summer Legacy': '',
                'Winter Legacy': ''
            }
            for stat, value in legacy_stats.items():
                character.set_stat('identity', 'legacy', stat, value, temp=False)
                character.set_stat('identity', 'legacy', stat, value, temp=True)
        else:
            # For non-Nunnehi, initialize standard Changeling stats
            lineage_stats = {
                'House': '',
                'Fae Court': ''
            }
            for stat, value in lineage_stats.items():
                character.set_stat('identity', 'lineage', stat, value, temp=False)
                character.set_stat('identity', 'lineage', stat, value, temp=True)
                
            # Initialize standard legacies in the correct category/type
            legacy_stats = {
                'Seelie Legacy': '',
                'Unseelie Legacy': ''
            }
            for stat, value in legacy_stats.items():
                character.set_stat('identity', 'legacy', stat, value, temp=False)
                character.set_stat('identity', 'legacy', stat, value, temp=True)
    
    # Set default Banality based on kith - only set permanent value, temp starts at 0
    banality = get_default_banality('Changeling', subtype=kith)
    if banality:
        character.db.stats['pools']['dual']['Banality'] = {'perm': banality, 'temp': 0}
        character.msg(f"|gBanality set to {banality}.")
    else:
        banality = get_default_banality('Changeling', subtype=kith)
        character.set_stat('pools', 'dual', 'Banality', banality, temp=False)
        character.set_stat('pools', 'dual', 'Banality', banality, temp=True)
        character.msg(f"|gBanality set to {banality} (permanent) for {kith}.")
    
    # Initialize base pools based on seeming
    glamour = initialize_glamour(character.get_stat('identity', 'lineage', 'Seeming', temp=False))
    character.set_stat('pools', 'dual', 'Glamour', glamour, temp=False)
    character.set_stat('pools', 'dual', 'Glamour', glamour, temp=True)
    
    # Adjust pools based on seeming changes
    new_seeming = character.get_stat('identity', 'lineage', 'Seeming', temp=False)
    if new_seeming:
        adjust_pools_for_seeming(character, old_seeming, new_seeming)
    
    if kith.lower() == 'inanimae':
        initialize_inanimae_stats(character)
    else:
        initialize_standard_changeling_stats(character)

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

def validate_changeling_stats(character, stat_name: str, value: str, category: str = None, stat_type: str = None) -> tuple[bool, str]:
    """
    Validate changeling-specific stats.
    Returns (is_valid, error_message)
    """
    stat_name = stat_name.lower()
    
    # Get kith for context-specific validation
    kith = character.get_stat('identity', 'lineage', 'Kith', temp=False)
    
    # Validate kith
    if stat_name == 'kith':
        return validate_changeling_kith(value)
        
    # Validate seeming
    if stat_name == 'seeming':
        is_valid, error_msg = validate_changeling_seeming(character, value)
        if is_valid:
            # Store old seeming for pool adjustments
            old_seeming = character.get_stat('identity', 'lineage', 'Seeming', temp=False)
            # After validation passes, adjust pools based on seeming change
            adjust_pools_for_seeming(character, old_seeming, value)
        return is_valid, error_msg
        
    # Validate house (only for non-Nunnehi)
    if stat_name == 'house' and kith != 'Nunnehi':
        return validate_changeling_house(value)
        
    # Validate Nunnehi-specific stats
    if kith == 'Nunnehi':
        # Validate lineage stats
        if stat_name == 'nunnehi camp':
            if value.title() not in NUNNEHI_CAMP:
                return False, f"Invalid Nunnehi camp. Valid camps are: {', '.join(sorted(NUNNEHI_CAMP))}"
            return True, ""
            
        if stat_name == 'nunnehi family':
            if value.title() not in NUNNEHI_FAMILY:
                return False, f"Invalid Nunnehi family. Valid families are: {', '.join(sorted(NUNNEHI_FAMILY))}"
            return True, ""
            
        if stat_name == 'nunnehi seeming':
            if value.title() not in NUNNEHI_SEEMING:
                return False, f"Invalid Nunnehi seeming. Valid seemings are: {', '.join(sorted(NUNNEHI_SEEMING))}"
            return True, ""
            
        # Validate Nunnehi legacy stats
        if stat_name == 'summer legacy':
            if value.title() not in SUMMER_LEGACIES:
                return False, f"Invalid Summer Legacy. Valid legacies are: {', '.join(sorted(SUMMER_LEGACIES))}"
            return True, ""
            
        if stat_name == 'winter legacy':
            if value.title() not in WINTER_LEGACIES:
                return False, f"Invalid Winter Legacy. Valid legacies are: {', '.join(sorted(WINTER_LEGACIES))}"
            return True, ""
    else:
        # For non-Nunnehi, validate standard legacies
        if stat_name == 'seelie legacy':
            if value.title() not in SEELIE_LEGACIES:
                return False, f"Invalid Seelie Legacy. Valid legacies are: {', '.join(sorted(SEELIE_LEGACIES))}"
            return True, ""
        elif stat_name == 'unseelie legacy':
            if value.title() not in UNSEELIE_LEGACIES:
                return False, f"Invalid Unseelie Legacy. Valid legacies are: {', '.join(sorted(UNSEELIE_LEGACIES))}"
            return True, ""
        
    # Validate arts
    if category == 'powers' and stat_type == 'art':
        return validate_changeling_art(character, stat_name, value)
        
    # Validate realms
    if category == 'powers' and stat_type == 'realm':
        return validate_changeling_realm(character, stat_name, value)
        
    # Validate backgrounds
    if category == 'backgrounds' and stat_type == 'background':
        return validate_changeling_backgrounds(character, stat_name, value)
    
    return True, ""

def validate_changeling_kith(value: str) -> tuple[bool, str]:
    """Validate a changeling's kith."""
    if value.title() not in KITH:
        return False, f"Invalid kith. Valid kiths are: {', '.join(sorted(KITH))}"
    return True, ""

def validate_changeling_seeming(character, value: str) -> tuple[bool, str]:
    """Validate a changeling's seeming."""
    # Get kith for Nunnehi validation
    kith = character.get_stat('identity', 'lineage', 'Kith', temp=False)
    
    if kith == 'Nunnehi':
        valid_seemings = ["Youngling", "Brave", "Elder"]
    else:
        valid_seemings = ["Childling", "Wilder", "Grump"]
    
    if value.title() not in valid_seemings:
        return False, f"Invalid seeming. Valid seemings are: {', '.join(sorted(valid_seemings))}"
    return True, ""

def validate_changeling_camp(value: str) -> tuple[bool, str]:
    """Validate a changeling's camp."""
    if value.title() not in NUNNEHI_CAMP:
        return False, f"Invalid camp. Valid camps are: {', '.join(sorted(NUNNEHI_CAMP))}"
    return True, ""

def validate_changeling_family(value: str) -> tuple[bool, str]:
    """Validate a changeling's family."""
    if value.title() not in NUNNEHI_FAMILY:
        return False, f"Invalid family. Valid families are: {', '.join(sorted(NUNNEHI_FAMILY))}"
    return True, ""

def validate_changeling_house(value: str) -> tuple[bool, str]:
    """Validate a changeling's house."""
    valid_houses = [
        "Beaumayn", "Dougal", "Eiluned", "Fiona", "Gwydion", "Liam", 
        "Scathach", "Aesin", "Ailil", "Balor", "Danaan", "Daireann", 
        "Leanhaun", "Varich"
    ]
    if value.title() not in valid_houses:
        return False, f"Invalid house. Valid houses are: {', '.join(sorted(valid_houses))}"
    return True, ""

def validate_changeling_art(character, art_name: str, value: str) -> tuple[bool, str]:
    """Validate a changeling's art."""
    # Check if the art exists
    if art_name.title() not in ARTS:
        return False, f"Invalid art. Valid arts are: {', '.join(sorted(ARTS))}"
    
    # Validate value
    try:
        art_value = int(value)
        if art_value < 0 or art_value > 5:
            return False, "Art values must be between 0 and 5"
        return True, ""
    except ValueError:
        return False, "Art values must be numbers"

def validate_changeling_realm(character, realm_name: str, value: str) -> tuple[bool, str]:
    """Validate a changeling's realm."""
    # Check if the realm exists
    if realm_name.title() not in REALMS:
        return False, f"Invalid realm. Valid realms are: {', '.join(sorted(REALMS))}"
    
    # Validate value
    try:
        realm_value = int(value)
        if realm_value < 0 or realm_value > 5:
            return False, "Realm values must be between 0 and 5"
        return True, ""
    except ValueError:
        return False, "Realm values must be numbers"

def validate_changeling_backgrounds(character, background_name: str, value: str) -> tuple[bool, str]:
    """Validate changeling backgrounds."""
    # Get list of available backgrounds
    from world.wod20th.utils.stat_mappings import UNIVERSAL_BACKGROUNDS, CHANGELING_BACKGROUNDS
    available_backgrounds = set(bg.title() for bg in UNIVERSAL_BACKGROUNDS + CHANGELING_BACKGROUNDS)
    
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

def update_changeling_pools_on_stat_change(character, stat_name: str, new_value: str) -> None:
    """
    Update changeling pools when relevant stats change.
    Called by CmdSelfStat after setting stats.
    """
    stat_name = stat_name.lower()
    
    # Handle Seeming changes
    if stat_name == 'seeming':
        old_seeming = character.get_stat('identity', 'lineage', 'Seeming', temp=False)
        adjust_pools_for_seeming(character, old_seeming, new_value)
    
    # Handle Kith changes
    elif stat_name == 'kith':
        # Get default Banality based on kith
        banality = get_default_banality('Changeling', subtype=new_value)
        if banality:
            character.set_stat('pools', 'dual', 'Banality', banality, temp=False)
            character.set_stat('pools', 'dual', 'Banality', banality, temp=True)
            character.msg(f"|gBanality set to {banality} for {new_value}.|n")
    
    # Handle House changes for Kinain
    elif stat_name == 'house':
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        char_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
        if splat == 'Mortal+' and char_type == 'Kinain':
            # Kinain get Glamour 2 by default
            character.set_stat('pools', 'dual', 'Glamour', 2, temp=False)
            character.set_stat('pools', 'dual', 'Glamour', 2, temp=True)
            character.msg("|gGlamour set to 2 for Kinain.|n")