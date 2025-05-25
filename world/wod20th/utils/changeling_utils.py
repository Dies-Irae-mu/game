"""
Utility functions for handling Changeling-specific character initialization and updates.
"""
from world.wod20th.utils.banality import get_default_banality
from world.wod20th.models import Stat
from world.wod20th.utils.stat_mappings import ARTS, REALMS
from typing import Dict, List, Set, Tuple, Optional
from evennia.utils import logger

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
    'Kuberas', 'Ondine', 'Parosemes', 'Glome', 'Solimond', 'Mannikin'
}

# Powers available to each Inanimae phyla
INANIMAE_POWERS = {
    'Kuberas': ['Sliver'],
    'Ondine': ['Sliver'],
    'Parosemes': ['Sliver'],
    'Glome': ['Sliver'],
    'Solimond': ['Sliver'],
    'Mannikin': ['Art', 'Realm', 'Sliver']  # Mannikins get all three power types but limited to 4 dots
}

# Slivers
SLIVERS = {
    'kuberas': ['Verdage'],
    'ondine': ['Aquis'],
    'parosemes': ['Stratus'],
    'glome': ['Petros'],
    'solimond': ['Pyros'],
    'mannikin': []
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
                'Anchor',
                'Seelie Legacy',
                'Unseelie Legacy',
                'Court'
            ]
    
    # Default stats for standard changelings
    return base_stats + [
        'House',
        'Court',
        'Seelie Legacy',
        'Unseelie Legacy'
    ]

def adjust_pools_for_seeming(character, old_seeming, new_seeming):
    """
    Adjust Willpower and Glamour pools based on Seeming changes.
    
    Args:
        character: The character being modified
        old_seeming: The character's previous seeming (or None)
        new_seeming: The new seeming being set
    """
    if not new_seeming:
        return
        
    # Convert seemings to lowercase for case-insensitive comparison
    new_seeming_lower = new_seeming.lower()
    old_seeming_lower = old_seeming.lower() if old_seeming else None
    
    # Base pools are 4 for all changelings
    base_willpower = 4
    base_glamour = 4
    
    # Check if this is a seeming change
    is_seeming_change = old_seeming_lower and old_seeming_lower != new_seeming_lower
    
    # Debug information
    if is_seeming_change:
        character.msg(f"|cDEBUG: Changing seeming from {old_seeming_lower} to {new_seeming_lower}|n")
    
    # Always reset to baseline, regardless of old seeming
    # This ensures we don't retain previous boosts
    character.set_stat('pools', 'dual', 'Willpower', base_willpower, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', base_willpower, temp=True)
    character.set_stat('pools', 'dual', 'Glamour', base_glamour, temp=False)
    character.set_stat('pools', 'dual', 'Glamour', base_glamour, temp=True)
    
    # Notify about reset if changing seemings
    if is_seeming_change:
        character.msg("|yYour Willpower and Glamour are reset to base values (4) due to your seeming change.|n")
    
    # Apply the bonus for the new seeming
    if new_seeming_lower == 'childling':
        # Childlings get +1 Glamour
        character.set_stat('pools', 'dual', 'Glamour', base_glamour + 1, temp=False)
        character.set_stat('pools', 'dual', 'Glamour', base_glamour + 1, temp=True)
        character.msg("|gYour Glamour is set to 5 due to your Childling seeming.|n")
    
    elif new_seeming_lower == 'grump':
        # Grumps get +1 Willpower
        character.set_stat('pools', 'dual', 'Willpower', base_willpower + 1, temp=False)
        character.set_stat('pools', 'dual', 'Willpower', base_willpower + 1, temp=True)
        character.msg("|gYour Willpower is set to 5 due to your Grump seeming.|n")
    
    elif new_seeming_lower == 'wilder':
        # Wilders can choose +1 Glamour or +1 Willpower
        character.msg("|gAs a Wilder, you can choose to increase either your Glamour or your Willpower by 1.|n")
        character.msg("|gUse +selfstat Glamour/pools.dual=5 to increase Glamour or +selfstat Willpower/pools.dual=5 to increase Willpower.|n")

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
    
    # Only initialize Arts and Realms for non-Inanimae (Inanimae will be handled separately)
    if kith.lower() != 'inanimae':
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
            character.set_stat('identity', 'lineage', 'Anchor', '', temp=False)
            character.set_stat('identity', 'lineage', 'Anchor', '', temp=True)
            # Add Slivers category
            character.db.stats['powers']['sliver'] = {}
            
            # Initialize Inanimae stats (including pools)
            initialize_inanimae_stats(character)
            return  # Return early as pools are handled in initialize_inanimae_stats
            
        # Special handling for Nunnehi
        elif kith.lower() == 'nunnehi':
            # Remove inappropriate stats
            for stat in ['Court', 'House', 'Seelie Legacy', 'Unseelie Legacy']:
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
                'Court': ''
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
        character.set_stat('pools', 'dual', 'Banality', 0, temp=True)
        character.msg(f"|gBanality set to {banality} (permanent) for {kith}.")
    
    # Initialize base pools based on seeming
    # Always set base values first (4 for both pools)
    character.set_stat('pools', 'dual', 'Glamour', 4, temp=False)
    character.set_stat('pools', 'dual', 'Glamour', 4, temp=True)
    character.set_stat('pools', 'dual', 'Willpower', 4, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 4, temp=True)
    character.msg("|gBase Willpower and Glamour set to 4.|n")
    
    # Adjust pools based on seeming changes
    new_seeming = character.get_stat('identity', 'lineage', 'Seeming', temp=False)
    if new_seeming:
        adjust_pools_for_seeming(character, old_seeming, new_seeming)
    
    if kith.lower() != 'inanimae':
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
    
    if phyla:
        # Convert phyla to title case for consistent comparison
        phyla_title = phyla.title()
        if phyla_title in INANIMAE_POWERS:
            # Get the powers available to this phyla
            available_powers = INANIMAE_POWERS[phyla_title]
            
            # Initialize Arts if available
            if 'Art' in available_powers:
                # Initialize Arts category
                character.db.stats['powers']['art'] = {}
                for art in ARTS:
                    character.db.stats['powers']['art'][art] = {'perm': 0, 'temp': 0}
            
            # Initialize Realms if available
            if 'Realm' in available_powers:
                # Initialize Realms category
                character.db.stats['powers']['realm'] = {}
                for realm in REALMS:
                    character.db.stats['powers']['realm'][realm] = {'perm': 0, 'temp': 0}
            
            # Initialize Slivers if available
            if 'Sliver' in available_powers:
                # Initialize all slivers to 0
                for sliver_type in ['Verdage', 'Aquis', 'Stratus', 'Petros', 'Pyros']:
                    character.db.stats['powers']['sliver'][sliver_type] = {'perm': 0, 'temp': 0}
                
                # Set affinity sliver to 1 based on phyla
                if phyla.lower() == 'kuberas':
                    character.db.stats['powers']['sliver']['Verdage'] = {'perm': 1, 'temp': 1}
                elif phyla.lower() == 'ondine':
                    character.db.stats['powers']['sliver']['Aquis'] = {'perm': 1, 'temp': 1}
                elif phyla.lower() == 'parosemes':
                    character.db.stats['powers']['sliver']['Stratus'] = {'perm': 1, 'temp': 1}
                elif phyla.lower() == 'glome':
                    character.db.stats['powers']['sliver']['Petros'] = {'perm': 1, 'temp': 1}
                elif phyla.lower() == 'solimond':
                    character.db.stats['powers']['sliver']['Pyros'] = {'perm': 1, 'temp': 1}
                elif phyla.lower() == 'mannikin':
                    # Mannikins get a generic sliver with no free point
                    character.db.stats['powers']['sliver']['Sliver'] = {'perm': 0, 'temp': 0}

            # Set starting pool values based on phyla
            phyla_pools = {
                'Glome': {'Glamour': 6, 'Willpower': 5, 'Banality': 4},
                'Kuberas': {'Glamour': 6, 'Willpower': 3, 'Banality': 3},
                'Ondine': {'Glamour': 6, 'Willpower': 3, 'Banality': 4},
                'Parosemes': {'Glamour': 5, 'Willpower': 3, 'Banality': 2},
                'Solimond': {'Glamour': 6, 'Willpower': 3, 'Banality': 4},
                'Mannikin': {'Glamour': 6, 'Willpower': 4, 'Banality': 6}
            }

            # Set pools based on phyla
            if phyla_title in phyla_pools:
                pools = phyla_pools[phyla_title]
                for pool, value in pools.items():
                    if pool == 'Banality':
                        character.set_stat('pools', 'dual', pool, value, temp=False)
                        character.set_stat('pools', 'dual', pool, 0, temp=True)
                    else:
                        character.set_stat('pools', 'dual', pool, value, temp=False)
                        character.set_stat('pools', 'dual', pool, value, temp=True)
                character.msg(f"|gInitialized pools for {phyla_title} phyla: Glamour {pools['Glamour']}, Willpower {pools['Willpower']}, Banality {pools['Banality']}|n")
            
            # Send appropriate message for Mannikins
            if phyla.lower() == 'mannikin':
                character.msg("|gInitialized Arts, Realms, and Slivers for Mannikin phyla (limited to 4 dots).|n")
            else:
                character.msg(f"|gInitialized Slivers with free point in {SLIVERS[phyla.lower()][0]} for {phyla} phyla.|n")

def get_kith_arts(kith: str) -> List[str]:
    """Get the available arts for a specific kith."""
    # This is a placeholder - implement actual kith-art relationships
    return []

def get_phyla_powers(phyla: str) -> List[str]:
    """Get the available powers for a specific Inanimae phyla."""
    return INANIMAE_POWERS.get(phyla, []) 

def validate_changeling_phyla(value: str) -> tuple[bool, str]:
    """Validate a changeling's phyla."""
    if value.title() not in PHYLA:
        return False, f"Invalid phyla. Valid phyla are: {', '.join(sorted(PHYLA))}"
    return True, ""

def validate_changeling_stats(character, stat_name: str, value: str, category: str = None, stat_type: str = None) -> tuple[bool, str]:
    """
    Validate changeling-specific stats.
    Returns (is_valid, error_message)
    """
    stat_name = stat_name.title()  # Convert to title case for consistency
    
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
        
    # Validate arts
    if category == 'powers' and stat_type == 'art':
        # Check if art exists
        if stat_name not in ARTS:
            return False, f"Invalid art. Valid arts are: {', '.join(sorted(ARTS))}"
        
        # Validate value
        try:
            art_value = int(value)
            if art_value < 0 or art_value > 5:
                return False, "Art values must be between 0 and 5"
            return True, ""
        except ValueError:
            return False, "Art values must be numbers"
            
    # Validate realms
    if category == 'powers' and stat_type == 'realm':
        # Check if realm exists
        if stat_name not in REALMS:
            return False, f"Invalid realm. Valid realms are: {', '.join(sorted(REALMS))}"
        
        # Validate value
        try:
            realm_value = int(value)
            if realm_value < 0 or realm_value > 5:
                return False, "Realm values must be between 0 and 5"
            return True, ""
        except ValueError:
            return False, "Realm values must be numbers"
    
    # Validate phyla (for Inanimae)
    if stat_name == 'phyla':
        if kith != 'Inanimae':
            return False, "Only Inanimae can have a phyla."
        return validate_changeling_phyla(value)
        
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

def validate_changeling_sliver(character, sliver_name: str, value: str) -> tuple[bool, str]:
    """Validate a changeling's sliver."""
    # Check if character is Inanimae
    kith = character.get_stat('identity', 'lineage', 'Kith', temp=False)
    if not kith or kith.lower() != 'inanimae':
        return False, "Only Inanimae can have Slivers."
    
    # Get phyla
    phyla = character.get_stat('identity', 'lineage', 'Phyla', temp=False)
    if not phyla:
        return False, "Must have a phyla to have Slivers."
    
    phyla_lower = phyla.lower()
    
    # Special handling for Mannikins
    if phyla_lower == 'mannikin':
        if sliver_name.lower() != 'sliver':
            return False, "Mannikins can only have the generic 'Sliver' power."
    else:
        # For non-Mannikins, validate sliver exists
        valid_slivers = {'Verdage', 'Aquis', 'Stratus', 'Petros', 'Pyros'}
        if sliver_name.title() not in valid_slivers:
            return False, f"Invalid Sliver. Valid Slivers are: {', '.join(sorted(valid_slivers))}"
    
    # Validate value
    try:
        sliver_value = int(value)
        if sliver_value < 0:
            return False, "Sliver values must be positive numbers"
        # Check 4-dot limit for Mannikins
        if phyla_lower == 'mannikin' and sliver_value > 4:
            return False, "Mannikin Inanimae can only have up to 4 dots in Slivers"
        elif sliver_value > 5:
            return False, "Sliver values must be between 0 and 5"
        return True, ""
    except ValueError:
        return False, "Sliver values must be numbers"

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
    
    # Handle Phyla changes for Inanimae
    elif stat_name == 'phyla':
        kith = character.get_stat('identity', 'lineage', 'Kith', temp=False)
        if kith and kith.lower() == 'inanimae':
            # Set pools based on phyla
            phyla_pools = {
                'Glome': {'Glamour': 6, 'Willpower': 5, 'Banality': 4},
                'Kuberas': {'Glamour': 6, 'Willpower': 3, 'Banality': 3},
                'Ondine': {'Glamour': 6, 'Willpower': 3, 'Banality': 4},
                'Parosemes': {'Glamour': 5, 'Willpower': 3, 'Banality': 2},
                'Solimond': {'Glamour': 6, 'Willpower': 3, 'Banality': 4},
                'Mannikin': {'Glamour': 6, 'Willpower': 4, 'Banality': 6}
            }
            
            phyla_title = new_value.title()
            if phyla_title in phyla_pools:
                pools = phyla_pools[phyla_title]
                for pool, value in pools.items():
                    if pool == 'Banality':
                        character.set_stat('pools', 'dual', pool, value, temp=False)
                        character.set_stat('pools', 'dual', pool, 0, temp=True)
                    else:
                        character.set_stat('pools', 'dual', pool, value, temp=False)
                        character.set_stat('pools', 'dual', pool, value, temp=True)
                character.msg(f"|gSet pools for {phyla_title} phyla: Glamour {pools['Glamour']}, Willpower {pools['Willpower']}, Banality {pools['Banality']}|n")
    
    # Handle House changes for Kinain
    elif stat_name == 'house':
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        char_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
        if splat == 'Mortal+' and char_type == 'Kinain':
            # Kinain get Glamour 2 by default
            character.set_stat('pools', 'dual', 'Glamour', 2, temp=False)
            character.set_stat('pools', 'dual', 'Glamour', 2, temp=True)
            character.msg("|gGlamour set to 2 for Kinain.|n")

def calculate_art_cost(current_rating: int, new_rating: int) -> int:
    """Calculate XP cost for Arts."""
    total_cost = 0
    if current_rating == 0:
        total_cost = 7  # Initial cost
        current_rating = 1
    
    for rating in range(current_rating + 1, new_rating + 1):
        total_cost += (rating - 1) * 4  # Cost per additional dot
    
    return total_cost

def calculate_realm_cost(current_rating: int, new_rating: int) -> int:
    """Calculate XP cost for Realms."""
    total_cost = 0
    if current_rating == 0:
        total_cost = 5  # Initial cost
        current_rating = 1
    
    for rating in range(current_rating + 1, new_rating + 1):
        total_cost += (rating - 1) * 3  # Cost per additional dot
    
    return total_cost

def calculate_glamour_cost(current_rating: int, new_rating: int) -> int:
    """Calculate XP cost for Glamour."""
    total_cost = 0
    for rating in range(current_rating + 1, new_rating + 1):
        total_cost += rating * 3  # Current rating * 3 XP
    return total_cost

def validate_changeling_purchase(character, stat_name: str, new_rating: int, category: str, subcategory: str, is_staff_spend: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate if a changeling can purchase a stat increase.
    
    Args:
        character: The character object
        stat_name: Name of the stat
        new_rating: The new rating to increase to
        category: The stat category
        subcategory: The stat subcategory
        is_staff_spend: Whether this is a staff-approved spend
        
    Returns:
        tuple: (can_purchase, error_message)
    """
    # Staff spends bypass validation
    if is_staff_spend:
        return True, None
        
    # Arts above level 2 require staff approval
    if subcategory == 'art' and new_rating > 2:
        return False, "Arts above level 2 require staff approval. Please use +request to submit a request."
        
    # Realms above level 2 require staff approval
    if subcategory == 'realm' and new_rating > 2:
        return False, "Realms above level 2 require staff approval. Please use +request to submit a request."
        
    return True, None