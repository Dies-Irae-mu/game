"""
Utility functions for handling Possessed-specific character initialization and updates.
"""
from world.wod20th.models import Stat
from world.wod20th.utils.stat_mappings import POSSESSED_TYPES, POSSESSED_POOLS
from world.wod20th.utils.banality import get_default_banality
from typing import Dict, List, Set, Tuple

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
    Returns (bool, str) tuple - (is_valid, error_message)
    """
    possessed_type = character.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
    if not possessed_type:
        return False, "Character is not a Possessed type"

    # Validate Gifts
    if power_type.lower() == 'gift':
        # Check if the Gift exists in the database
        gift_exists = Stat.objects.filter(
            name__iexact=power_name,
            category='powers',
            stat_type='gift'
        ).exists()
        if not gift_exists:
            return False, f"'{power_name}' is not a valid Gift"

    # Validate Blessings
    elif power_type.lower() == 'blessing':
        if possessed_type not in POSSESSED_POWERS:
            return False, f"Invalid Possessed type: {possessed_type}"
        
        available_blessings = POSSESSED_POWERS[possessed_type].get('blessing', [])
        if power_name not in available_blessings:
            return False, f"'{power_name}' is not a valid Blessing for {possessed_type}"

    # Validate Charms
    elif power_type.lower() == 'charm':
        if possessed_type not in POSSESSED_POWERS:
            return False, f"Invalid Possessed type: {possessed_type}"
        
        available_charms = POSSESSED_POWERS[possessed_type].get('charm', [])
        if power_name not in available_charms:
            return False, f"'{power_name}' is not a valid Charm for {possessed_type}"

    return True, ""

def validate_possessed_stats(character, stat_name: str, value: str, category: str = None, stat_type: str = None) -> tuple[bool, str]:
    """
    Validate possessed-specific stats.
    Returns (is_valid, error_message)
    """
    stat_name = stat_name.lower()
    
    # Get possessed type
    possessed_type = character.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
    print(f"\nValidating possessed stats:")
    print(f"stat_name: {stat_name}")
    print(f"value: {value}")
    print(f"category: {category}")
    print(f"stat_type: {stat_type}")
    print(f"possessed_type: {possessed_type}")
    
    # Validate type
    if stat_name == 'possessed type':
        return validate_possessed_type(value)
        
    # Validate powers
    if category == 'powers':
        if stat_type == 'blessing':
            result = validate_possessed_blessing(character, stat_name.title(), value)
            print(f"Blessing validation result: {result}")
            return result
        elif stat_type == 'charm':
            result = validate_possessed_charm(character, stat_name.title(), value)
            print(f"Charm validation result: {result}")
            return result
        elif stat_type == 'gift':
            result = validate_possessed_gift(character, stat_name.title(), value)
            print(f"Gift validation result: {result}")
            return result
    
    return True, ""

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
    
    # Validate value
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

def validate_possessed_gift(character, gift_name: str, value: str) -> tuple[bool, str]:
    """Validate a possessed gift."""
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
