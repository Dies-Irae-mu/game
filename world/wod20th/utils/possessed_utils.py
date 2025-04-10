"""
Utility functions for handling Possessed-specific character initialization and updates.
"""
from world.wod20th.utils.stat_mappings import POSSESSED_TYPES, POSSESSED_POOLS
from world.wod20th.utils.banality import get_default_banality
from typing import Dict, List, Set, Tuple, Optional
from evennia.utils import logger
from django.db.models import Q

# Valid possessed types
POSSESSED_TYPES = {
    'Fomori': 'Fomori',
    'Kami': 'Kami'
}

# Choices tuple for form fields and validation
POSSESSED_TYPE_CHOICES = tuple((key, value) for key, value in POSSESSED_TYPES.items())

# Base pools for each possessed type
POSSESSED_POOLS = {
    'Fomori': {
        'Willpower': {'default': 3, 'max': 10},
        'Rage': {'default': 0, 'max': 10},
        'Gnosis': {'default': 0, 'max': 10},
    },
    'Kami': {
        'Willpower': {'default': 4, 'max': 10},
        'Gnosis': {'default': 1, 'max': 10},
        'Rage': {'default': 0, 'max': 10},
    }
}

# Available powers for possessed types
POSSESSED_POWERS = {
    'Fomori': {
        'blessing': [
            # General blessings
            'Animal Control', 'Armored Hide', 'Armored Skin', 'Berserker',
            'Darksight', 'Extra Speed', 'Footpads', 'Homogeneity', 
            'Immunity to the Delirium', 'Mega-Attribute', 'Nimbleness', 
            'Sense the Unnatural', 'Possessed Size', 'Size Shift', 'Spirit Charm',
            'Spirit Ties', 'Umbral Passage', 'Wall Walking', 'Water Breathing',
            'Webbing', 'Possessed Wings',
            # Fomori-specific blessings
            'Bestial Mutation', 'Body-Barbs', 'Body Expansion', 'Brain Eating',
            'Cancerous Carapace', 'Cause Insanity', 'Chameleon Coloration',
            'Claws and Fangs', 'Deception', 'Dentata Orifice', 'Echoes of Wrath',
            'Ectoplasmic Extrusion', 'Exoskeleton', 'Extra Limbs', 'Eyes of the Wyrm',
            'Fiery Discharge', 'Frog Tongue', 'Fungal Touch', 'Fungal Udder',
            'Gaseous Form', 'Gifted Fomor', 'Hazardous Breath', 'Hazardous Heave',
            "Hell's Hide", 'Infectious Touch', 'Invisibility', 'Lashing Tail',
            'Malleate', 'Maw of the Wyrm', 'Mind Blast', 'Molecular Weakening',
            'Noxious Breath', 'Noxious Miasma', 'Numbing', 'Phoenix Form',
            'Poison Tumors', 'Rat Head', 'Regeneration', 'Roar of the Wyrm',
            'Sense Gaia', 'Shadowplay', 'Skittersight', 'Slither Skin',
            'Slobbersnot', 'Stomach Pumper', 'Tar Skin', 'Toxic Secretions',
            'Triatic Mask', 'Twisted Senses', 'Unnatural Strength', 'Venomous Bite',
            'Viscous Form', 'Voice of the Wyrm', 'Wrathful Invective'
        ],
        'charm': [
            'Airt Sense', 'Appear', 'Blast', 'Blighted Touch', 'Brand',
            'Break Reality', 'Calcify', 'Call for Aid', 'Cleanse the Blight',
            'Cling Charm', 'Control Electrical Systems', 'Corruption', 'Create Fire Charm',
            'Create Wind Charm', 'Death Fertility', 'Digital Disruption', 'Disable',
            'Disorient', 'Dream Journey', 'Ease Pain', 'Element Sense',
            'Feedback', 'Flee', 'Flood', 'Freeze', 'Healing Charm', 'Illuminate',
            'Influence', 'Inhabit', 'Insight Charm', 'Iron Will Charm', 'Lightning Bolt',
            'Materialize', 'Meld', 'Mind Speech Charm', 'Open Moon Bridge Charm', 'Peek',
            'Possession', 'Quake', 'Re-form', 'Shapeshift', 'Short Out',
            'Shatter Glass', 'Solidify Reality', 'Spirit Away', 'Spirit Static',
            'Swift Flight', 'System Havoc', 'Terror', 'Track', 'Umbral Storm',
            'Umbraquake', 'Updraft', 'Waves'
        ]
    },
    'Kami': {
        'blessing': [
            # General blessings
            'Animal Control', 'Armored Hide', 'Armored Skin', 'Berserker',
            'Darksight', 'Extra Speed', 'Footpads', 'Homogeneity', 
            'Immunity to the Delirium', 'Mega-Attribute', 'Nimbleness', 
            'Sense the Unnatural', 'Size', 'Size Shift', 'Spirit Charm',
            'Spirit Ties', 'Umbral Passage', 'Wall Walking', 'Water Breathing',
            'Webbing', 'Wings',
            # Kami-specific blessings
            'Aura of Tranquility', 'Beast of Burden', 'Curse of Gaia',
            'Elemental Resistance', 'Gifted Kami', 'Heart Sense', 'Longevity',
            'Mercy', 'Piercing Gaze', 'Plant Animation', 'Plant Kinship',
            'Ritekeeper', "Season's Blessing", 'Spirit Awakening', 'Spirit Kinship',
            'Spirit Sense', 'Transformation', 'Triatic Sense', 'Universal Tongue'
        ],
        'charm': [
            'Airt Sense', 'Appear', 'Blast', 'Blighted Touch', 'Brand',
            'Break Reality', 'Calcify', 'Call for Aid', 'Cleanse the Blight',
            'Cling', 'Control Electrical Systems', 'Corruption', 'Create Fire',
            'Create Wind', 'Death Fertility', 'Digital Disruption', 'Disable',
            'Disorient', 'Dream Journey', 'Ease Pain', 'Element Sense',
            'Feedback', 'Flee', 'Flood', 'Freeze', 'Healing', 'Illuminate',
            'Influence', 'Inhabit', 'Insight', 'Iron Will', 'Lightning Bolt',
            'Materialize', 'Meld', 'Mind Speech', 'Open Moon Bridge', 'Peek',
            'Possession', 'Quake', 'Re-form', 'Shapeshift', 'Short Out',
            'Shatter Glass', 'Solidify Reality', 'Spirit Away', 'Spirit Static',
            'Swift Flight', 'System Havoc', 'Terror', 'Track', 'Umbral Storm',
            'Umbraquake', 'Updraft', 'Waves'
        ]
    }
}

def initialize_possessed_stats(character, possessed_type):
    """Initialize stats for a possessed character."""
    # Initialize basic stats structure
    if 'identity' not in character.db.stats:
        character.db.stats['identity'] = {}
    if 'personal' not in character.db.stats['identity']:
        character.db.stats['identity']['personal'] = {}
    if 'lineage' not in character.db.stats['identity']:
        character.db.stats['identity']['lineage'] = {}
    
    # Initialize identity stats
    identity_stats = {
        'personal': [
            'Full Name', 'Concept', 'Date of Birth', 'Date of Possession',
            'Nature', 'Demeanor'
        ],
        'lineage': [
            'Possessed Type', 'Spirit Name', 'Spirit Type'
        ]
    }
    
    # Set default values for personal stats
    for stat in identity_stats['personal']:
        if stat not in character.db.stats['identity']['personal']:
            character.db.stats['identity']['personal'][stat] = {'perm': '', 'temp': ''}
    
    # Set default values for lineage stats
    for stat in identity_stats['lineage']:
        if stat not in character.db.stats['identity']['lineage']:
            character.db.stats['identity']['lineage'][stat] = {'perm': '', 'temp': ''}
    
    # Initialize powers category if it doesn't exist
    if 'powers' not in character.db.stats:
        character.db.stats['powers'] = {}
        
    # Initialize pools structure
    if 'pools' not in character.db.stats:
        character.db.stats['pools'] = {}
    if 'dual' not in character.db.stats['pools']:
        character.db.stats['pools']['dual'] = {}
    if 'other' not in character.db.stats['pools']:
        character.db.stats['pools']['other'] = {}
    
    # Initialize power categories
    power_categories = ['blessing', 'charm', 'gift']
    for category in power_categories:
        if category not in character.db.stats['powers']:
            character.db.stats['powers'][category] = {}

    # If possessed_type is empty, we're just doing basic initialization
    if not possessed_type:
        return
        
    # Convert possessed_type to proper case using POSSESSED_TYPE_CHOICES
    proper_type = next((t[0] for t in POSSESSED_TYPE_CHOICES if t[0].lower() == possessed_type.lower()), None)
    if proper_type:
        # Set the possessed type
        character.set_stat('identity', 'lineage', 'Possessed Type', proper_type, temp=False)
        character.set_stat('identity', 'lineage', 'Possessed Type', proper_type, temp=True)

        # Set base pools based on type
        if proper_type in POSSESSED_POOLS:
            pools = POSSESSED_POOLS[proper_type]
            
            # Initialize all pools to 0 first
            for pool_name in ['Willpower', 'Rage', 'Gnosis']:
                if pool_name not in character.db.stats['pools']['dual']:
                    character.db.stats['pools']['dual'][pool_name] = {'perm': 0, 'temp': 0}
            
            # Now set the proper values
            for pool_name, pool_data in pools.items():
                # Skip Willpower if it's already set to a non-zero value
                if pool_name == 'Willpower' and character.get_stat('pools', 'dual', 'Willpower', temp=False) > 0:
                    continue
                    
                # Set both permanent and temporary values
                character.db.stats['pools']['dual'][pool_name] = {
                    'perm': pool_data['default'],
                    'temp': pool_data['default']
                }
                character.msg(f"|g{pool_name} set to {pool_data['default']} for {proper_type}.")

        # Set default Banality based on possessed type
        banality = get_default_banality('Possessed', subtype=proper_type)
        if banality:
            character.db.stats['pools']['dual']['Banality'] = {'perm': banality, 'temp': banality}
            character.msg(f"|gBanality set to {banality} (permanent).")

        # Initialize available powers for the type
        if proper_type in POSSESSED_POWERS:
            for category in power_categories:
                if category in POSSESSED_POWERS[proper_type]:
                    for power in POSSESSED_POWERS[proper_type][category]:
                        if power not in character.db.stats['powers'][category]:
                            character.db.stats['powers'][category][power] = {'perm': 0, 'temp': 0}

def validate_possessed_powers(character, power_type, power_name, value):
    """
    Validate power selections for Possessed characters.
    Returns (bool, str, str) tuple - (is_valid, error_message, corrected_value)
    """
    possessed_type = character.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
    if not possessed_type:
        return False, "Character is not a Possessed type", None

    # Validate Gifts
    if power_type.lower() == 'gift':
        # Get Stat model lazily to avoid circular imports
        Stat = get_stat_model()
        # Check if the Gift exists in the database
        gift_exists = Stat.objects.filter(
            name__iexact=power_name,
            category='powers',
            stat_type='gift'
        ).exists()
        if not gift_exists:
            return False, f"'{power_name}' is not a valid Gift", None
        try:
            gift_value = int(value)
            if gift_value < 0 or gift_value > 5:
                return False, "Gift values must be between 0 and 5", None
            return True, "", str(gift_value)
        except ValueError:
            return False, "Gift value must be a number", None

    # Validate Blessings
    elif power_type.lower() == 'blessing':
        if possessed_type not in POSSESSED_POWERS:
            return False, f"Invalid Possessed type: {possessed_type}", None
        
        available_blessings = POSSESSED_POWERS[possessed_type].get('blessing', [])
        if power_name not in available_blessings:
            return False, f"'{power_name}' is not a valid Blessing for {possessed_type}", None
        try:
            blessing_value = int(value)
            if blessing_value < 0 or blessing_value > 5:
                return False, "Blessing values must be between 0 and 5", None
            return True, "", str(blessing_value)
        except ValueError:
            return False, "Blessing value must be a number", None

    # Validate Charms
    elif power_type.lower() == 'charm':
        if possessed_type not in POSSESSED_POWERS:
            return False, f"Invalid Possessed type: {possessed_type}", None
        
        available_charms = POSSESSED_POWERS[possessed_type].get('charm', [])
        if power_name not in available_charms:
            return False, f"'{power_name}' is not a valid Charm for {possessed_type}", None
        try:
            charm_value = int(value)
            if charm_value < 0 or charm_value > 5:
                return False, "Charm values must be between 0 and 5", None
            return True, "", str(charm_value)
        except ValueError:
            return False, "Charm value must be a number", None

    return True, "", value

def validate_possessed_stats(character, stat_name: str, value: str, category: str = None, stat_type: str = None) -> tuple[bool, str, str]:
    """
    Validate possessed-specific stats.
    Returns (is_valid, error_message, corrected_value)
    """
    stat_name = stat_name.lower()
    
    # Get character info
    splat = character.get_stat('other', 'splat', 'Splat', temp=False)
    possessed_type = character.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
    
    # Special handling for Berserker
    if stat_name == 'berserker':
        # For Possessed, Berserker is a blessing
        if splat == 'Possessed':
            try:
                blessing_value = int(value)
                if blessing_value < 0 or blessing_value > 5:
                    return False, "Berserker blessing must be between 0 and 5", None
                
                # Set up powers.blessing structure if needed
                if 'powers' not in character.db.stats:
                    character.db.stats['powers'] = {}
                if 'blessing' not in character.db.stats['powers']:
                    character.db.stats['powers']['blessing'] = {}
                
                # Set the blessing
                character.db.stats['powers']['blessing']['Berserker'] = {'perm': blessing_value, 'temp': blessing_value}
                
                # If Berserker is taken, set Rage pool to 5
                if blessing_value > 0:
                    if 'pools' not in character.db.stats:
                        character.db.stats['pools'] = {}
                    if 'dual' not in character.db.stats['pools']:
                        character.db.stats['pools']['dual'] = {}
                    character.db.stats['pools']['dual']['Rage'] = {'perm': 5, 'temp': 5}
                    character.msg("|gBerserker blessing grants Rage pool of 5.|n")
                
                return True, "", str(blessing_value)
            except ValueError:
                return False, "Blessing value must be a number", None
    
    # Special handling for Spirit Ties
    if stat_name == 'spirit ties':
        # For Possessed, Spirit Ties affects Gnosis
        if splat == 'Possessed':
            if not possessed_type:
                return False, "Character must have a possessed type set", None
                
            # Spirit Ties can be purchased up to 5 dots for all Possessed types
            max_value = 5
                
            try:
                blessing_value = int(value)
                if blessing_value < 0:
                    return False, "Spirit Ties value must be positive", None
                elif blessing_value > max_value:
                    return False, f"Spirit Ties maximum is {max_value} dots", None
                
                return True, "", str(blessing_value)
            except ValueError:
                return False, "Spirit Ties value must be a number", None
    
    # Handle other blessings if this is a blessing stat
    if category == 'powers' and stat_type == 'blessing' and stat_name not in ['berserker', 'spirit ties']:
        # Call blessing validation
        is_valid, error_msg = validate_possessed_blessing(character, stat_name, value)
        return is_valid, error_msg, value if is_valid else None
    
    # Handle charm validation
    if category == 'powers' and stat_type == 'charm':
        is_valid, error_msg = validate_possessed_charm(character, stat_name, value)
        return is_valid, error_msg, value if is_valid else None
    
    # Handle gift validation
    if category == 'powers' and stat_type == 'gift':
        is_valid, error_msg = validate_possessed_gift(character, stat_name, value)
        return is_valid, error_msg, value if is_valid else None
    
    return True, "", value

def validate_possessed_type(value: str) -> tuple[bool, str]:
    """Validate a possessed type."""
    if value not in POSSESSED_TYPES:
        return False, f"Invalid possessed type. Valid types are: {', '.join(sorted(POSSESSED_TYPES))}"
    return True, ""

def validate_possessed_blessing(character, blessing_name: str, value: str) -> tuple[bool, str]:
    """Validate a possessed blessing."""
    # Get character's possessed type
    possessed_type = character.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
    print(f"\nValidating blessing:")
    print(f"blessing_name: {blessing_name}")
    print(f"value: {value}")
    print(f"possessed_type: {possessed_type}")
    
    if not possessed_type:
        return False, "Character must have a possessed type set"
    
    # Get available blessings
    available_blessings = POSSESSED_POWERS.get(possessed_type, {}).get('blessing', [])
    print(f"available_blessings: {available_blessings}")
    
    if not available_blessings:
        return False, f"No blessings found for {possessed_type}"
    
    if blessing_name not in available_blessings:
        return False, f"Invalid blessing for {possessed_type}. Valid blessings are: {', '.join(sorted(available_blessings))}"
    
    # Special validation for Spirit Ties
    if blessing_name.lower() == 'spirit ties':
        try:
            blessing_value = int(value)
            # Spirit Ties can be purchased up to 5 dots for all Possessed types
            max_value = 5
                
            if blessing_value < 0:
                return False, "Blessing values must be positive"
            elif blessing_value > max_value:
                return False, f"Spirit Ties maximum is {max_value} dots"
            return True, ""
        except ValueError:
            return False, "Blessing values must be numbers"
    
    # Validate value for other blessings
    try:
        blessing_value = int(value)
        if blessing_value < 0 or blessing_value > 5:
            return False, "Blessing values must be between 0 and 5"
        return True, ""
    except ValueError:
        return False, "Blessing values must be numbers"

def validate_possessed_charm(character, charm_name: str, value: str) -> tuple[bool, str]:
    """Validate a possessed charm."""
    # Get character's possessed type
    possessed_type = character.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
    if not possessed_type:
        return False, "Character must have a possessed type set"
    
    # Get available charms
    available_charms = POSSESSED_POWERS.get(possessed_type, {}).get('charm', [])
    if not available_charms:
        return False, f"No charms found for {possessed_type}"
    
    if charm_name not in available_charms:
        return False, f"Invalid charm for {possessed_type}. Valid charms are: {', '.join(sorted(available_charms))}"
    
    # Validate value
    try:
        charm_value = int(value)
        if charm_value < 0 or charm_value > 5:
            return False, "Charm values must be between 0 and 5"
        return True, ""
    except ValueError:
        return False, "Charm values must be numbers"

def get_stat_model():
    """Get the Stat model lazily to avoid circular imports."""
    from world.wod20th.models import Stat
    return Stat

def validate_possessed_gift(character, gift_name: str, value: str) -> tuple[bool, str]:
    """Validate a possessed gift."""
    # Check if the gift exists in the database
    Stat = get_stat_model()
    from django.db.models import Q
    
    gift = Stat.objects.filter(
        Q(name__iexact=gift_name) |
        Q(gift_alias__icontains=gift_name),  # Check aliases
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

def update_possessed_pools_on_stat_change(character, stat_name: str, new_value: str) -> None:
    """
    Update possessed pools when relevant stats change.
    Called by CmdSelfStat after setting stats.
    """
    stat_name = stat_name.lower()
    
    # Handle Possessed Type changes
    if stat_name == 'possessed type':
        # Get default Banality based on possessed type
        banality = get_default_banality('Possessed', subtype=new_value)
        if banality:
            character.set_stat('pools', 'dual', 'Banality', banality, temp=False)
            character.set_stat('pools', 'dual', 'Banality', banality, temp=True)
            character.msg(f"|gBanality set to {banality} for {new_value}.|n")
        
        # Set base pools based on type
        if new_value in POSSESSED_POOLS:
            pools = POSSESSED_POOLS[new_value]
            for pool_name, pool_data in pools.items():
                # Skip Willpower if it's already set to a non-zero value
                if pool_name == 'Willpower' and character.get_stat('pools', 'dual', 'Willpower', temp=False) > 0:
                    continue
                
                # Set both permanent and temporary values
                character.set_stat('pools', 'dual', pool_name, pool_data['default'], temp=False)
                character.set_stat('pools', 'dual', pool_name, pool_data['default'], temp=True)
                character.msg(f"|g{pool_name} set to {pool_data['default']} for {new_value}.|n")
    
    # Handle Berserker blessing
    elif stat_name == 'berserker':
        try:
            blessing_value = int(new_value)
            if blessing_value > 0:
                # If Berserker is taken, set Rage pool to 5
                character.set_stat('pools', 'dual', 'Rage', 5, temp=False)
                character.set_stat('pools', 'dual', 'Rage', 5, temp=True)
                character.msg("|gRage set to 5 due to Berserker blessing.|n")
        except (ValueError, TypeError):
            character.msg("|rError updating Rage pool - invalid Berserker value.|n")
            return
            
    # Handle Spirit Ties blessing - updates Gnosis
    elif stat_name == 'spirit ties':
        try:
            # Get character's possessed type to determine base Gnosis
            possessed_type = character.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
            if not possessed_type:
                character.msg("|rError: Cannot set Spirit Ties without a Possessed Type.|n")
                return
                
            # Get the base Gnosis value from possessed type
            base_gnosis = 0  # Default for Fomori
            max_gnosis = 5   # Maximum total Gnosis
            
            if possessed_type.lower() == 'kami':
                base_gnosis = 1  # Kami start with Gnosis 1
                max_gnosis = 6   # Kami can have a maximum of 6 Gnosis
                
            # Get the Spirit Ties blessing value
            blessing_value = int(new_value)
            
            # If the blessing is taken, update Gnosis accordingly
            if blessing_value > 0:
                # Calculate new Gnosis as base + Spirit Ties value (capped at maximum)
                new_gnosis = min(base_gnosis + blessing_value, max_gnosis)
                
                # Set Gnosis pool
                character.set_stat('pools', 'dual', 'Gnosis', new_gnosis, temp=False)
                character.set_stat('pools', 'dual', 'Gnosis', new_gnosis, temp=True)
                
                # Explain the calculation to the user
                if possessed_type.lower() == 'kami':
                    character.msg(f"|gGnosis set to {new_gnosis} (1 base + {blessing_value} from Spirit Ties, maximum 6 total) for {possessed_type}.|n")
                else:
                    character.msg(f"|gGnosis set to {new_gnosis} ({blessing_value} from Spirit Ties, maximum 5 total) for {possessed_type}.|n")
            # If the blessing is removed, reset to base Gnosis
            else:
                character.set_stat('pools', 'dual', 'Gnosis', base_gnosis, temp=False)
                character.set_stat('pools', 'dual', 'Gnosis', base_gnosis, temp=True)
                character.msg(f"|gGnosis reset to base value of {base_gnosis} for {possessed_type}.|n")
        except (ValueError, TypeError):
            character.msg("|rError updating Gnosis pool - invalid Spirit Ties value.|n")
            return

def calculate_blessing_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Blessings.
    Cost is new rating x 4 XP.
    """
    # Blessings use flat costs based on new_rating
    return new_rating * 4

def calculate_possessed_gift_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Gifts.
    Cost is new rating x 7 XP.
    
    NOTE: This function can be called in two ways:
    1. calculate_possessed_gift_cost(current_rating, new_rating)
    2. calculate_possessed_gift_cost(character, gift_name, new_rating, current_rating)
    
    If first argument is a character object, we're in pattern #2.
    """
    # Check if first parameter is a character object (has db attribute)
    if hasattr(current_rating, 'db'):
        # Function was called as (character, gift_name, new_rating, current_rating)
        character = current_rating
        gift_name = new_rating
        new_rating = new_rating  # Should be fixed to the right parameter
        
        # Extract the actual new_rating and current_rating from the params
        if isinstance(new_rating, tuple) and len(new_rating) >= 2:
            current_rating = new_rating[1] if new_rating[1] is not None else 0
            new_rating = new_rating[0]
        else:
            # If we can't extract properly, use default values
            current_rating = 0
            # Try to get the new_rating as the third parameter
            if isinstance(gift_name, int):
                new_rating = gift_name
        
        logger.log_info(f"Possessed gift cost called with character object. Using gift_name={gift_name}, new_rating={new_rating}, current_rating={current_rating}")
    
    # Gifts use flat costs based on new_rating
    total_cost = new_rating * 7
    
    logger.log_info(f"Possessed gift cost calculation: {total_cost} XP")
    return total_cost

def calculate_possessed_charm_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Charms.
    Cost is 5 XP per level.
    """
    # For charms, use absolute difference cost (5 XP per dot)
    return (new_rating - current_rating) * 5

def validate_possessed_purchase(character, stat_name: str, new_rating: int, category: str, subcategory: str, is_staff_spend: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate if a possessed character can purchase a stat increase.
    
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
        
    # Blessings require staff approval
    if subcategory == 'blessing':
        return False, "Blessings require staff approval. Please use +request to submit a request."
        
    # Gifts above level 2 require staff approval
    if subcategory == 'gift' and new_rating > 2:
        return False, "Gifts above level 2 require staff approval. Please use +request to submit a request."
        
    # Charms above level 2 require staff approval
    if subcategory == 'charm' and new_rating > 2:
        return False, "Charms above level 2 require staff approval. Please use +request to submit a request."
        
    return True, None
