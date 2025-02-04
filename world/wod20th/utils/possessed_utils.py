"""
Utility functions for handling Possessed-specific character initialization and updates.
"""
from world.wod20th.models import Stat
from world.wod20th.utils.stat_mappings import POSSESSED_TYPES, POSSESSED_POOLS
from world.wod20th.utils.banality import get_default_banality
from typing import Dict, List, Set, Tuple

# Valid possessed types
POSSESSED_TYPES = {
    'Fomori': 'Bane-possessed',
    'Kami': 'Spirit-possessed'
}

# Choices tuple for form fields and validation
POSSESSED_TYPE_CHOICES = tuple((key, value) for key, value in POSSESSED_TYPES.items())

# Base pools for each possessed type
POSSESSED_POOLS = {
    'Fomori': {
        'Willpower': {'default': 3, 'max': 10},
        'Rage': {'default': 0, 'max': 10},
        'Gnosis': {'default': 0, 'max': 10},
        'Banality': {'default': 7, 'max': 10}
    },
    'Kami': {
        'Willpower': {'default': 4, 'max': 10},
        'Gnosis': {'default': 1, 'max': 10},
        'Rage': {'default': 0, 'max': 10},
        'Banality': {'default': 4, 'max': 10}
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
            'Sense the Unnatural', 'Size', 'Size Shift', 'Spirit Charm',
            'Spirit Ties', 'Umbral Passage', 'Wall Walking', 'Water Breathing',
            'Webbing', 'Wings',
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
    """Initialize specific stats for a possessed character."""
    # Initialize basic stats structure
    if 'identity' not in character.db.stats:
        character.db.stats['identity'] = {}
    if 'lineage' not in character.db.stats['identity']:
        character.db.stats['identity']['lineage'] = {}
    
    # Initialize powers category if it doesn't exist
    if 'powers' not in character.db.stats:
        character.db.stats['powers'] = {}
    
    # Convert possessed_type to proper case using POSSESSED_TYPE_CHOICES
    proper_type = next((t[0] for t in POSSESSED_TYPE_CHOICES if t[0].lower() == possessed_type.lower()), None)
    if not proper_type:
        return
    
    # Initialize power categories
    power_categories = ['blessing', 'charm', 'gift']
    for category in power_categories:
        if category not in character.db.stats['powers']:
            character.db.stats['powers'][category] = {}
        
        # Initialize available powers for the type
        if proper_type in POSSESSED_POWERS and category in POSSESSED_POWERS[proper_type]:
            for power in POSSESSED_POWERS[proper_type][category]:
                if power not in character.db.stats['powers'][category]:
                    character.db.stats['powers'][category][power] = {'perm': 0, 'temp': 0}
    
    # Set base pools based on type
    if proper_type in POSSESSED_POOLS:
        pools = POSSESSED_POOLS[proper_type]
        for pool_name, pool_data in pools.items():
            character.set_stat('pools', 'dual', pool_name, pool_data['default'], temp=False)
            character.set_stat('pools', 'dual', pool_name, pool_data['default'], temp=True)
            if pool_name != 'Banality':  # Don't announce Banality changes here
                character.msg(f"Set {pool_name} to {pool_data['default']}.")
    
    # Set the type in identity/lineage
    character.set_stat('identity', 'lineage', 'Possessed Type', proper_type, temp=False)
    character.set_stat('identity', 'lineage', 'Possessed Type', proper_type, temp=True)

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
