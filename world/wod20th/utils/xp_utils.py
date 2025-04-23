"""
Utility functions for XP management.
"""
from world.wod20th.utils.sheet_constants import (
    TALENTS, SKILLS, KNOWLEDGES,
    SECONDARY_TALENTS, SECONDARY_SKILLS, SECONDARY_KNOWLEDGES,
    BACKGROUNDS, BLESSINGS, CHARMS
)
from world.wod20th.utils.stat_mappings import (
    MAGE_SPHERES, ARTS, REALMS, SPECIAL_ADVANTAGES, COMBAT_SPECIAL_ADVANTAGES,
    MERIT_CATEGORIES, FLAW_CATEGORIES, MERIT_VALUES, FLAW_VALUES, UNIVERSAL_BACKGROUNDS, VAMPIRE_BACKGROUNDS, CHANGELING_BACKGROUNDS, MAGE_BACKGROUNDS,
    TECHNOCRACY_BACKGROUNDS, TRADITIONS_BACKGROUNDS, NEPHANDI_BACKGROUNDS, SHIFTER_BACKGROUNDS,
    SORCERER_BACKGROUNDS, KINAIN_BACKGROUNDS, THAUMATURGY_PATHS, NECROMANCY_PATHS
)
from world.wod20th.utils.vampire_utils import CLAN_DISCIPLINES

# Do not import shifter_utils functions here to avoid circular imports
# They will be imported within the functions that need them

from decimal import Decimal, ROUND_DOWN
from django.db.models import Q
from evennia.utils import logger
import re 
import logging

from world.wod20th.utils.vampire_utils import validate_discipline_purchase, PURCHASABLE_DISCIPLINES, is_discipline_in_clan
from world.wod20th.utils.mortalplus_utils import calculate_kinfolk_gift_cost
from world.wod20th.utils.possessed_utils import calculate_possessed_gift_cost

from world.wod20th.utils.ritual_data import THAUMATURGY_RITUALS, NECROMANCY_RITUALS

from world.wod20th.utils.xp_costs import (
    # General costs
    calculate_arcanos_cost,
    calculate_attribute_cost,
    calculate_ability_cost,
    calculate_faith_cost,
    calculate_willpower_cost,
    calculate_background_cost,
    calculate_merit_cost,
    calculate_flaw_cost,
    
    # Vampire costs
    calculate_discipline_cost,
    calculate_virtue_cost,
    calculate_path_cost,
    calculate_thaumaturgy_path_cost,
    calculate_ritual_cost,
    
    # Werewolf costs
    calculate_gift_cost,
    calculate_rage_cost,
    calculate_gnosis_cost,
    calculate_rite_cost,
    
    # Mage costs
    calculate_sphere_cost,
    calculate_arete_cost,
    calculate_avatar_cost,
    
    # Changeling costs
    calculate_art_cost,
    calculate_realm_cost,
    calculate_glamour_cost,
    
    # Companion costs
    calculate_special_advantage_cost,
    calculate_charm_cost,
    
    # Sorcerer costs
    calculate_sorcerous_path_cost,
    calculate_sorcerous_ritual_cost,
    
    # Psychic costs
    calculate_numina_cost,
    
    # Possessed costs
    calculate_blessing_cost,
    calculate_possessed_gift_cost,
    
    # Kinain costs
    calculate_kinain_art_cost,
    calculate_kinain_realm_cost,
    
    # Kinfolk costs
    calculate_kinfolk_gift_cost,
    
    # Ghoul costs
    calculate_ghoul_discipline_cost
)

from evennia.objects.models import ObjectDB
from evennia.utils import logger
from datetime import datetime, timedelta
import ast
from typing import Dict, List, Tuple, Optional
import re
import logging

# Auto-approve rules
AUTO_APPROVE = {
    'all': {
        'attributes': 3,  # All attributes up to 3
        'abilities': 3,   # All abilities up to 3
        'backgrounds': {   # Specific backgrounds up to 2
            'Resources': 2,
            'Contacts': 2,
            'Allies': 2,
            'Backup': 2,
            'Herd': 2,
            'Library': 2,
            'Kinfolk': 2,
            'Spirit Heritage': 2,
            'Paranormal Tools': 2,
            'Servants': 2,
            'Armory': 2,
            'Retinue': 2,
            'Spies': 2,
            'Professional Certification': 1,
            'Past Lives': 2,
            'Dreamers': 2,
        },
        'pools': {
            'max': 5,
            'types': ['Willpower', 'Rage', 'Gnosis', 'Glamour']
        },
        'advantages': {
            'max': 1,
            'types': ['Arete', 'Enlightenment']
        }
    },
    'Vampire': {
        'powers': {        # Disciplines up to 2
            'max': 2,
            'types': ['discipline']
        }
    },
    'Mage': {
        'powers': {        # Spheres up to 2
            'max': 2,
            'types': ['sphere']
        }
    },
    'Changeling': {
        'powers': {        # Arts and Realms up to 2
            'max': 2,
            'types': ['art', 'realm']
        }
    },
    'Shifter': {
        'powers': {        # Level 1 Gifts only
            'max': 1,
            'types': ['gift']
        }
    },
    'Mortal+': {
        'powers': {        # Level 1 Gifts for Kinfolk
            'max': 1,
            'types': ['gift']
        }
    }
}

# Shifter type mappings for gifts
SHIFTER_MAPPINGS = {
    'Ajaba': {
        'aspects_to_auspices': {
            'Dawn': True,
            'Midnight': True,
            'Dusk': True
        },
        'breed_mappings': {
            'Homid': 'homid',
            'Metis': 'metis',
            'Hyaenid': 'lupus'
        }
    },
    'Ananasi': {
        'aspects_to_tribes': {
            'Tenere': True,
            'Hatar': True,
            'Kumoti': True,
            'Kumo': True
        },
        'factions_to_auspices': {
            'Myrmidon': True,
            'Viskr': True,
            'Wyrsta': True
        },
        'breed_mappings': {
            'Homid': 'homid',
            'Crawlerling': 'lupus'
        }
    },
    'Bastet': {
        'tribes': {
            'bagheera': True,  # Add lowercase versions
            'balam': True,
            'bubasti': True,
            'ceilican': True,
            'khan': True,
            'pumonca': True,
            'qualmi': True,
            'simba': True,
            'swara': True,
            'Bagheera': True,  # Keep original case versions
            'Balam': True,
            'Bubasti': True,
            'Ceilican': True,
            'Khan': True,
            'Pumonca': True,
            'Qualmi': True,
            'Simba': True,
            'Swara': True
        },
        'breed_mappings': {
            'Homid': 'homid',
            'Metis': 'metis',
            'Feline': 'lupus'
        }
    },
    'Corax': {
        'all_gifts_in_tribe': True,
        'breed_mappings': {
            'Homid': 'homid',
            'Corvid': 'lupus'
        }
    },
    'Gurahl': {
        'auspices': {
            'Arcas': True,
            'Uzami': True,
            'Kojubat': True,
            'Kieh': True,
            'Rishi': True
        },
        'breed_mappings': {
            'Homid': 'homid',
            'Ursine': 'lupus'
        }
    },
    'Kitsune': {
        'paths_to_auspices': {
            'Kataribe': True,
            'Gukutsushi': True,
            'Doshi': True,
            'Eji': True
        },
        'breed_mappings': {
            'Kojin': 'homid',
            'Roko': 'lupus',
            'Shinju': 'metis'
        },
        'special_gifts': {
            'ju-fu': True
        }
    },
    'Mokole': {
        'auspices': {
            'Rising Sun': True,
            'Noonday Sun': True,
            'Setting Sun': True,
            'Shrouded Sun': True,
            'Midnight Sun': True,
            'Decorated Suns': True,
            'Solar Eclipse': True
        },
        'auspice_mappings': {
            'Tung Chun': 'Setting Sun',
            'Nam Nsai': 'Noonday Sun',
            'Sai Chau': 'Solar Eclipse',
            'Pei Tung': 'Midnight Sun'
        },
        'breed_mappings': {
            'Homid': 'homid',
            'Suchid': 'lupus'
        }
    },
    'Nagah': {
        'auspices': {
            'Kamakshi': True,
            'Kartikeya': True,
            'Kamsa': True,
            'Kali': True
        },
        'breed_mappings': {
            'Balaram': 'homid',
            'Ahi': 'metis',
            'Vasuki': 'lupus'
        },
        'special_breed_gifts': {
            'Balaram': True,
            'Ahi': True,
            'Vasuki': True
        }
    },
    'Nuwisha': {
        'all_gifts_in_tribe': True,
        'breed_mappings': {
            'Homid': 'homid',
            'Latrani': 'lupus'
        }
    },
    'Ratkin': {
        'aspects_to_auspices': {
            'Tunnel Runner': True,
            'Shadow Seer': True,
            'Knife Skulker': True,
            'Warrior': True,
            'Engineer': True,
            'Plague Lord': True,
            'Munchmausen': True,
            'Twitcher': True
        },
        'breed_mappings': {
            'Homid': 'homid',
            'Metis': 'metis',
            'Rodens': 'lupus'
        },
        'special_breed_gifts': {
            'Homid': True,
            'Metis': True,
            'Rodens': True
        }
    },
    'Rokea': {
        'auspices': {
            'Brightwater': True,
            'Dimwater': True,
            'Darkwater': True
        },
        'breed_mappings': {
            'Homid': 'homid',
            'Squamus': 'lupus'
        }
    }
}

def _get_primary_thaumaturgy_path(character):
    """Get the primary thaumaturgy path for a character. This is the first path purchased and the one that is the highest rating. 
    if there are multiple paths at the same rating, use 'Path of Blood'."""
    paths = character.db.stats.get('powers', {}).get('thaumaturgy', {})
    highest_rating = 0
    primary_path = 'Path of Blood'  # Default to Path of Blood if multiple at same rating
    
    # Go through all paths to find highest rating
    for path_name, path_data in paths.items():
        rating = path_data.get('perm', 0)
        if rating > highest_rating:
            highest_rating = rating
            primary_path = path_name
        elif rating == highest_rating and path_name == 'Path of Blood':
            # If same rating and it's Path of Blood, prefer it
            primary_path = path_name
            
    return primary_path

def _get_primary_necromancy_path(character):
    """Get the primary necromancy path for a character. This is the first path purchased and the one that is the highest rating. 
    if there are multiple paths at the same rating, use 'Sepulchre Path'."""
    paths = character.db.stats.get('powers', {}).get('necromancy', {})
    highest_rating = 0
    primary_path = 'Sepulchre Path'  # Default to Sepulchre Path if multiple at same rating
    
    # Go through all paths to find highest rating
    for path_name, path_data in paths.items():
        rating = path_data.get('perm', 0)
        if rating > highest_rating:
            highest_rating = rating
            primary_path = path_name
        elif rating == highest_rating and path_name == 'Sepulchre Path':
            # If same rating and it's Sepulchre Path, prefer it
            primary_path = path_name
            
    return primary_path


def get_stat_model():
    """Get the Stat model lazily to avoid circular imports."""
    from world.wod20th.models import Stat
    return Stat

def calculate_xp_cost(character, is_staff_spend: bool, stat_name: str, category: str = None, subcategory: str = None, current_rating: int = 0, new_rating: int = 0) -> tuple:
    """
    Calculate the XP cost to raise a stat from current_rating to new_rating.
    
    Args:
        character: The character object
        is_staff_spend: Whether this is a staff-approved spend
        stat_name: The name of the stat being raised
        category: The category of the stat (e.g., 'attributes', 'abilities', 'backgrounds', 'powers')
        subcategory: The subcategory of the stat (e.g., 'talents', 'skills', 'knowledges')
        current_rating: The current rating of the stat
        new_rating: The new rating to raise the stat to
        
    Returns:
        tuple: A tuple containing (cost, requires_approval).
            - cost (int): The XP cost to raise the stat.
            - requires_approval (bool): Whether the stat raise requires staff approval.
    """
    # Get character's splat and type
    splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
    mortal_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')

    # Special handling for Time based on splat
    if stat_name == 'Time':
        if splat == 'Mage':
            category = 'powers'
            subcategory = 'sphere'
        elif splat == 'Changeling' or (splat == 'Mortal+' and mortal_type == 'Kinain'):
            category = 'powers'
            subcategory = 'realm'

    # Normalize the stat name (handle case sensitivity)
    normalized_stat_name = stat_name.strip()
    
    # For instanced backgrounds, extract the base name
    base_stat_name = normalized_stat_name
    if "(" in normalized_stat_name and ")" in normalized_stat_name:
        base_stat_name = normalized_stat_name.split("(")[0].strip()
    
    # Default values
    cost = 0
    requires_approval = False
    
    # Calculate cost based on category
    if category == 'attributes':
        cost = calculate_attribute_cost(current_rating, new_rating)
        requires_approval = new_rating > 4
    
    elif category in ['abilities', 'secondary_abilities']:
        if subcategory in ['talent', 'skill', 'knowledge', 'secondary_talent', 'secondary_skill', 'secondary_knowledge']:
            total_cost = calculate_ability_cost(current_rating, new_rating)
            requires_approval = new_rating > 3
            return total_cost, requires_approval
        
        requires_approval = new_rating > 4
    
    elif category == 'backgrounds':
        cost = calculate_background_cost(current_rating, new_rating)
        
        # Check if the background requires approval
        AUTO_SPEND_BACKGROUNDS = ["allies", "contacts", "resources", "fame"]
        if base_stat_name.lower() not in AUTO_SPEND_BACKGROUNDS:
            requires_approval = True
        else:
            # These backgrounds can be auto-approved up to rating 2
            requires_approval = new_rating > 2
    
    # Handle gifts for different character types
    elif category == 'powers' and subcategory == 'gift':
        if splat == 'Shifter':
            from world.wod20th.utils.shifter_utils import calculate_gift_cost
            total_cost = calculate_gift_cost(character, stat_name, new_rating, current_rating)
            requires_approval = new_rating > 1
        elif splat == 'Mortal+' and mortal_type == 'Kinfolk':
            from world.wod20th.utils.mortalplus_utils import calculate_kinfolk_gift_cost
            total_cost = calculate_kinfolk_gift_cost(current_rating, new_rating)
            requires_approval = new_rating > 1
        elif splat == 'Possessed':
            from world.wod20th.utils.possessed_utils import calculate_possessed_gift_cost
            total_cost = calculate_possessed_gift_cost(current_rating, new_rating)
            requires_approval = new_rating > 2
        else:
            total_cost = calculate_ability_cost(current_rating, new_rating)
            requires_approval = new_rating > 2
        return total_cost, requires_approval

    # Handle disciplines
    elif category == 'powers' and subcategory == 'discipline':
        if splat == 'Vampire':
            clan = character.db.stats.get('identity', {}).get('lineage', {}).get('Clan', {}).get('perm', '')
            is_in_clan = is_discipline_in_clan(stat_name, clan)
            if clan and clan.lower() == 'caitiff':
                total_cost = calculate_discipline_cost(current_rating, new_rating, 'caitiff')
            else:
                total_cost = calculate_discipline_cost(current_rating, new_rating, 'in_clan' if is_in_clan else 'out_clan')
            requires_approval = new_rating > 2
        elif splat == 'Mortal+' and mortal_type == 'Ghoul':
            clan = character.db.stats.get('identity', {}).get('lineage', {}).get('Family', {}).get('perm', '')
            is_in_clan = is_discipline_in_clan(stat_name, clan)
            total_cost = calculate_ghoul_discipline_cost(current_rating, new_rating, is_in_clan)
            requires_approval = new_rating > 1
        else:
            total_cost = calculate_ability_cost(current_rating, new_rating)
            requires_approval = new_rating > 2
        return total_cost, requires_approval

    # Handle spheres
    elif category == 'powers' and subcategory == 'sphere':
        from world.wod20th.utils.mage_utils import calculate_sphere_cost
        total_cost, requires_approval, _ = calculate_sphere_cost(character, stat_name, new_rating, current_rating, is_staff_spend)
        return total_cost, requires_approval

    # Handle arts and realms
    elif category == 'powers' and subcategory in ['art', 'realm']:
        if splat == 'Changeling':
            if subcategory == 'art':
                total_cost = calculate_art_cost(current_rating, new_rating)
            else:  # realm
                total_cost = calculate_realm_cost(current_rating, new_rating)
            requires_approval = new_rating > 2
        elif splat == 'Mortal+' and mortal_type == 'Kinain':
            if subcategory == 'art':
                total_cost = calculate_kinain_art_cost(current_rating, new_rating)
            else:  # realm
                total_cost = calculate_kinain_realm_cost(current_rating, new_rating)
            requires_approval = new_rating > 2
        return total_cost, requires_approval
    
    # Handle special advantages for companions
    elif category == 'powers' and subcategory == 'special_advantage':
        total_cost = calculate_special_advantage_cost(current_rating, new_rating)
        requires_approval = True  # Special advantages always require approval
        return total_cost, requires_approval

    # Handle charms
    elif category == 'powers' and subcategory == 'charm':
        if splat in ['Companion', 'Possessed']:
            total_cost = calculate_charm_cost(current_rating, new_rating)
            requires_approval = new_rating > 2
            return total_cost, requires_approval

    # Handle blessings
    elif category == 'powers' and subcategory == 'blessing':
        total_cost = calculate_blessing_cost(current_rating, new_rating)
        requires_approval = True  # Blessings always require approval
        return total_cost, requires_approval

    # Handle Mortal+ specific powers
    elif splat == 'Mortal+':
        if subcategory == 'sorcery':
            total_cost = calculate_sorcerous_path_cost(current_rating, new_rating)
            requires_approval = new_rating > 2
        elif subcategory == 'hedge_ritual':
            total_cost = calculate_sorcerous_ritual_cost(current_rating, new_rating)
            requires_approval = new_rating > 1
        elif subcategory == 'numina':
            total_cost = calculate_numina_cost(current_rating, new_rating)
            requires_approval = new_rating > 2
        return total_cost, requires_approval
    
    # Handle pools
    elif category == 'pools' and subcategory == 'dual':
        if stat_name == 'Willpower':
            total_cost = calculate_willpower_cost(current_rating, new_rating)
            requires_approval = new_rating > 6
        elif stat_name == 'Rage':
            total_cost = calculate_rage_cost(current_rating, new_rating)
            requires_approval = new_rating > 6
        elif stat_name == 'Gnosis':
            total_cost = calculate_gnosis_cost(current_rating, new_rating)
            requires_approval = new_rating > 3
        elif stat_name == 'Glamour':
            total_cost = calculate_glamour_cost(current_rating, new_rating)
            requires_approval = new_rating > 5
        else:
            total_cost = calculate_willpower_cost(current_rating, new_rating)
            requires_approval = new_rating > 5
        return total_cost, requires_approval
    
    # handle arete/enlightenment
    elif category == 'pools' and subcategory == 'advantage':
        if stat_name in ['Arete', 'Enlightenment']:
            total_cost = calculate_arete_cost(current_rating, new_rating)
            requires_approval = new_rating > 1
        else:
            total_cost = calculate_ability_cost(current_rating, new_rating)
            requires_approval = True
        return total_cost, requires_approval

    elif category == 'virtues':
        cost = calculate_virtue_cost(current_rating, new_rating)
        requires_approval = False
        return cost, requires_approval
    
    else:
        # Default to ability cost for anything not specifically handled
        cost = calculate_ability_cost(current_rating, new_rating)
        requires_approval = new_rating > 3
    
    return cost, requires_approval

def validate_xp_purchase(self_or_character, stat_name, new_rating, category=None, subcategory=None, is_staff_spend=False):
    """
    Validate if a character can purchase a stat increase.
    
    This function supports two calling conventions:
    1. As a method: self.validate_xp_purchase(stat_name, new_rating, ...)
    2. As a function: validate_xp_purchase(character, stat_name, new_rating, ...)
    
    Args:
        self_or_character: Either self (when called as a method) or character object
        stat_name (str): The name of the stat to upgrade
        new_rating (int): The new rating the character wishes to purchase
        category (str, optional): The category of the stat
        subcategory (str, optional): The subcategory of the stat
        is_staff_spend (bool, optional): Whether this is a staff-approved spend
        
    Returns:
        tuple: (success (bool), message (str), cost_if_successful (int))
    """
    # Determine if this is being called as a method or function
    if hasattr(self_or_character, 'db') and hasattr(self_or_character.db, 'stats'):
        # Called as function with character as first parameter
        character = self_or_character
    else:
        # Called as method with self as first parameter
        character = self_or_character
    
    # If category and subcategory aren't provided, try to determine them
    if not category or not subcategory:
        cat_subcat = _determine_stat_category(stat_name)
        if cat_subcat:
            category, subcategory = cat_subcat
        else:
            return False, f"Could not determine category for {stat_name}", 0
    
    # Get character's splat
    splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
    char_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
    
    if not splat:
        return False, "Character splat not set", 0
    
    # Normalize stat name
    normalized_stat_name = normalize_stat_name(stat_name, category, subcategory)
    
    # Get current rating
    current_rating = get_current_rating(character, category, subcategory, stat_name, temp=False)
    
    # Check if new rating is higher than current
    if new_rating <= current_rating:
        return False, f"New rating must be higher than current rating ({current_rating}).", 0
    
    # Early validation for merits and flaws
    if category in ['merits', 'flaws'] and not is_staff_spend:
        return False, f"{category.title()} require staff approval", 0
    
    # Verify requirements for specific stats
    is_valid, message, _ = validate_stat_requirements(character, normalized_stat_name, category, subcategory, new_rating, is_staff_spend)
    if not is_valid:
        return False, message, 0
    
    # Calculate cost
    cost, requires_approval = calculate_xp_cost(
        character, is_staff_spend, normalized_stat_name, category, subcategory, current_rating, new_rating
    )
    
    # Check approval requirements if this is not a staff spend
    if requires_approval and not is_staff_spend:
        return False, f"{normalized_stat_name} purchases at this level require staff approval.", cost
    
    # Check if character has enough XP
    available_xp = character.db.xp.get("current", 0)
    if available_xp < cost:
        return False, f"Not enough XP. Cost: {cost}, Available: {available_xp}.", cost
    
    return True, f"You can purchase {normalized_stat_name} at a cost of {cost} XP.", cost

def process_xp_purchase(character, stat_name, new_rating, category=None, subcategory=None, is_staff_spend=False, reason="", current_rating=None, pre_calculated_cost=None):
    """
    Process an XP purchase.
    
    Args:
        character: The character object
        stat_name: The name of the stat to increase
        new_rating: The desired new rating
        category: The stat category (optional)
        subcategory: The stat subcategory (optional)
        is_staff_spend: Whether this is a staff-approved spend (default: False)
        reason: The reason for the spend (default: "")
        current_rating: The current rating (if pre-determined)
        pre_calculated_cost: The pre-calculated cost (if provided)
        
    Returns:
        tuple: (success, message, cost) where:
            - success: Boolean indicating if purchase was successful
            - message: The success or error message
            - cost: The cost of the purchase (if applicable)
    """
    try:
        # Validate inputs
        if not category or not subcategory:
            cat_subcat = _determine_stat_category(stat_name)
            if cat_subcat:
                category, subcategory = cat_subcat
            else:
                return False, f"Could not determine category for {stat_name}", 0
        
        # Get current rating if not provided
        if current_rating is None:
            current_rating = get_current_rating(character, category, subcategory, stat_name, temp=False)
        
        # Check basic requirements
        is_valid, message, _ = validate_stat_requirements(character, stat_name, category, subcategory, new_rating, is_staff_spend)
        if not is_valid and 'higher than current rating' not in message:  # Allow if just current/new rating mismatch
            return False, message, 0
        
        # Calculate cost if not provided
        if pre_calculated_cost is None:
            if category == 'attributes':
                cost = calculate_attribute_cost(current_rating, new_rating)
            elif category in ['abilities', 'secondary_abilities']:
                cost = calculate_ability_cost(current_rating, new_rating)
            elif category == 'backgrounds':
                cost = calculate_background_cost(current_rating, new_rating)
            elif category == 'merits':
                cost = calculate_merit_cost(current_rating, new_rating)
            elif category == 'flaws':
                cost = calculate_flaw_cost(current_rating, new_rating)
            elif category == 'pools' and subcategory == 'dual' and stat_name.lower() == 'willpower':
                cost = calculate_willpower_cost(current_rating, new_rating)
            elif category == 'powers':
                # This will be handled by specific handlers
                cost = calculate_ability_cost(current_rating, new_rating)  # Default
            else:
                # Default to standard ability cost if no specific handler
                cost = calculate_ability_cost(current_rating, new_rating)
        else:
            cost = pre_calculated_cost
            
        # Ensure cost is not 0 (except for flaws, which can be 0 when removed)
        if cost == 0 and category != 'flaws':
            return False, "Cost calculation returned zero. This may indicate a stat category error.", 0
        
        # Convert cost to Decimal for precise calculations
        cost_decimal = Decimal(str(cost)).quantize(Decimal('0.01'))
        
        # Check if character has enough XP
        if character.db.xp.get('current', 0) < cost_decimal:
            return False, f"Not enough XP. Cost: {cost_decimal}, Available: {character.db.xp.get('current', 0)}", cost_decimal

        # Handle special power types
        if category == 'powers':
            if subcategory in ['thaumaturgy', 'necromancy']:
                success = _handle_path_disciplines(character, stat_name, new_rating, current_rating, subcategory)
                if not success:
                    return False, f"Failed to update {subcategory} path", cost_decimal
            elif subcategory == 'blessing':
                success, error = _handle_blessing_updates(character, stat_name, new_rating)
                if not success:
                    return False, error, cost_decimal
            elif subcategory == 'special_advantage':
                success, error = _handle_special_advantage_updates(character, stat_name, new_rating)
                if not success:
                    return False, error, cost_decimal
            elif subcategory == 'gift':
                # Special handling for gifts with canonical names
                from world.wod20th.models import Stat
                from django.db.models import Q
                
                # More flexible search for special characters like apostrophes
                # First try for exact or partial match on canonical name
                gift = Stat.objects.filter(
                    name__iexact=stat_name,
                    category='powers',
                    stat_type='gift'
                ).first()
                
                # If not found by exact match, try a similar name search
                if not gift and len(stat_name) > 3:
                    import difflib
                    
                    # Get possible matches
                    potential_matches = Stat.objects.filter(
                        category='powers',
                        stat_type='gift'
                    )
                    
                    # Find the best match using similarity ratio
                    best_match = None
                    best_score = 0.7  # Minimum 70% similarity required
                    
                    for potential in potential_matches:
                        similarity = difflib.SequenceMatcher(None, stat_name.lower(), potential.name.lower()).ratio()
                        if similarity > best_score:
                            best_score = similarity
                            best_match = potential
                    
                    if best_match:
                        gift = best_match
                
                # If not found, try aliases with better matching
                if not gift:
                    import difflib
                    
                    # Search for gifts with matching alias
                    all_gifts = Stat.objects.filter(
                        category='powers',
                        stat_type='gift'
                    )
                    
                    # First check for exact alias matches
                    for g in all_gifts:
                        if g.gift_alias and any(alias.lower() == stat_name.lower() for alias in g.gift_alias):
                            gift = g
                            break
                    
                    # If still not found and search term is substantial, try similarity matching
                    if not gift and len(stat_name) > 3:
                        best_match = None
                        best_score = 0.7  # Minimum similarity threshold
                        
                        for g in all_gifts:
                            if g.gift_alias:
                                for alias in g.gift_alias:
                                    similarity = difflib.SequenceMatcher(None, stat_name.lower(), alias.lower()).ratio()
                                    if similarity > best_score:
                                        best_score = similarity
                                        best_match = g
                        
                        if best_match:
                            gift = best_match
                
                canonical_name = gift.name if gift else stat_name
                logger.log_info(f"XP purchase: Found gift {'via alias' if gift and gift.name.lower() != stat_name.lower() else 'directly'}: {stat_name} -> {canonical_name}")
                
                # Update the stat
                logger.log_info(f"XP purchase: Updating gift with canonical name: {canonical_name}")
                success = update_stat(character, category, subcategory, canonical_name, new_rating, temp=True, form_modifier=0)
                if not success:
                    return False, f"Failed to update gift {canonical_name}", cost_decimal
                
                # Store alias if needed - use original stat_name as alias for canonical_name
                if hasattr(character, 'set_gift_alias') and gift and stat_name.lower() != canonical_name.lower():
                    logger.log_info(f"XP purchase: Calling set_gift_alias({canonical_name}, {stat_name}, {new_rating})")
                    alias_to_use = stat_name
                    if isinstance(stat_name, list):
                        alias_to_use = stat_name[0] if len(stat_name) == 1 else " ".join(stat_name)
                    character.set_gift_alias(canonical_name, alias_to_use, new_rating)
                elif not hasattr(character, 'set_gift_alias'):
                    logger.log_err(f"XP purchase: Character {character.name} does not have set_gift_alias method")
                elif not gift or stat_name.lower() == canonical_name.lower():
                    logger.log_info(f"XP purchase: No need to set gift alias for {stat_name}")
                else:
                    logger.log_info(f"XP purchase: Unknown reason for not setting gift alias")
            else:
                # Regular power update
                success = update_stat(character, category, subcategory, stat_name, new_rating, temp=True, form_modifier=0)
                if not success:
                    return False, f"Failed to update {subcategory} {stat_name}", cost_decimal
        
        # Handle backgrounds with instances
        elif category == 'backgrounds' and '(' in stat_name and ')' in stat_name:
            success = update_stat(character, category, subcategory, stat_name, new_rating, temp=True, form_modifier=0)
            if not success:
                return False, f"Failed to update background {stat_name}", cost_decimal
        
        # Handle merits and flaws with special processing
        elif category in ['merits', 'flaws']:
            # Update the merit/flaw
            success = update_stat(character, category, subcategory, stat_name, new_rating, temp=True, form_modifier=0)
            if not success:
                return False, f"Failed to update {category} {stat_name}", cost_decimal
                
            # Special case for Kinfolk with Gnosis merit
            if (category == 'merits' and subcategory == 'supernatural' and
                stat_name.lower() == 'gnosis' and 
                character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '') == 'Mortal+' and 
                character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '') == 'Kinfolk'):
                from world.wod20th.utils.mortalplus_utils import handle_kinfolk_gnosis
                gnosis_value = handle_kinfolk_gnosis(character, new_rating)
                logger.log_info(f"Updated Kinfolk Gnosis pool to {gnosis_value} based on merit rating {new_rating}")
        
        # For all other stats
        else:
            success = update_stat(character, category, subcategory, stat_name, new_rating, temp=True, form_modifier=0)
            if not success:
                return False, f"Failed to update {stat_name}", cost_decimal

        # Deduct XP and log the spend
        success, message = deduct_xp_and_log(
            character, cost_decimal, stat_name, current_rating, new_rating, reason
        )
        if not success:
            return False, message, cost_decimal

        return True, f"Successfully increased {stat_name} from {current_rating} to {new_rating} (Cost: {cost_decimal} XP)", cost_decimal

    except Exception as e:
        logger.log_err(f"Error in process_xp_purchase: {str(e)}")
        return False, f"Error: {str(e)}", 0

def get_power_type(stat_name):
    """Determine power type from name."""
    # Get the stat from the database using lazy loading
    from world.wod20th.models import Stat
    stat = Stat.objects.filter(name=stat_name).first()
    if stat:
        return stat.stat_type
    return None

def can_buy_stat(self, stat_name, new_rating, category=None):
    """Check if a stat can be bought without staff approval."""
    # Get character's splat
    splat = self.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
    if not splat:
        return (False, "Character splat not set")

    # Basic validation
    if category == 'abilities':
        # For abilities, we need to determine the subcategory (talent/skill/knowledge)
        for subcat in ['talent', 'skill', 'knowledge']:
            current_rating = (self.db.stats.get('abilities', {})
                            .get(subcat, {})
                            .get(stat_name, {})
                            .get('perm', 0))
            if current_rating:  # Found the ability
                break
    else:
        current_rating = self.get_stat(category, None, stat_name) or 0

    if new_rating <= current_rating:
        return (False, "New rating must be higher than current rating")

    # Auto-approve list for each splat
    AUTO_APPROVE = {
        'all': {
            'attributes': 3,  # All attributes up to 3
            'abilities': 3,   # All abilities up to 3
            'backgrounds': {   # Specific backgrounds up to 2
                'Resources': 2,
                'Contacts': 2,
                'Allies': 2,
                'Backup': 2,
                'Herd': 2,
                'Library': 2,
                'Kinfolk': 2,
                'Spirit Heritage': 2,
                'Paranormal Tools': 2,
                'Servants': 2,
                'Armory': 2,
                'Retinue': 2,
                'Spies': 2,
                'Professional Certification': 1,
                'Past Lives': 2,
                'Dreamers': 2,
            },
        },
        'pools': {
            'max': 5,
            'types': ['Willpower', 'Rage', 'Gnosis', 'Glamour']
        },
        'Vampire': {
            'powers': {        # Disciplines up to 2
                'max': 2,
                'types': ['discipline', 'thaumaturgy', 'necromancy', 'thaum_ritual', 'necromancy_ritual']
            }
        },
        'Mage': {
            'powers': {        # Spheres up to 2
                'max': 2,
                'types': ['sphere']
            }
        },
        'Changeling': {
            'powers': {        # Arts and Realms up to 2
                'max': 2,
                'types': ['art', 'realm']
            }
        },
        'Shifter': {
            'powers': {        # Level 1 Gifts only
                'max': 1,
                'types': ['gift']
            }
        },
        'Mortal+': {
            'powers': {        
                'max': 1,
                'types': ['gift', 'art', 'realm', 'sorcery', 'numina', 'faith', 'discipline']
            }
        }
    }

    # Check category-specific limits
    if category == 'attributes' and new_rating <= AUTO_APPROVE['all']['attributes']:
        return (True, None)
        
    if category == 'abilities' and new_rating <= AUTO_APPROVE['all']['abilities']:
        return (True, None)
        
    if category == 'backgrounds':
        max_rating = AUTO_APPROVE['all']['backgrounds'].get(stat_name)
        if max_rating and new_rating <= max_rating:
            return (True, None)
            
    if stat_name == 'Willpower':
        max_willpower = AUTO_APPROVE['all']['willpower'].get(splat, 
                        AUTO_APPROVE['all']['willpower']['default'])
        if new_rating <= max_willpower:
            return (True, None)
            
    if category == 'powers' and splat in AUTO_APPROVE:
        power_rules = AUTO_APPROVE[splat]['powers']
        # Check if it's the right type of power for the splat
        power_type = self._get_power_type(stat_name)
        if (power_type in power_rules['types'] and 
            new_rating <= power_rules['max']):
            return (True, None)

    return (False, "Requires staff approval")

def _get_power_type(self, stat_name):
    """Helper method to determine power type from name."""
    # Get the stat from the database
    from world.wod20th.models import Stat
    stat = Stat.objects.filter(name=stat_name).first()
    if stat:
        return stat.stat_type
    return None

def ensure_stat_structure(self, category, subcategory):
    """Ensure the proper nested structure exists for stats."""
    if not hasattr(self.db, 'stats'):
        self.db.stats = {}
    
    if category not in self.db.stats:
        self.db.stats[category] = {}
    
    if subcategory and subcategory not in self.db.stats[category]:
        self.db.stats[category][subcategory] = {}
    
    return True

def buy_stat(self, stat_name, new_rating, category=None, subcategory=None, reason="", is_staff_spend=False):
    """
    Method wrapper for process_xp_purchase that handles the character instance automatically.
    
    Args:
        stat_name: The name of the stat to increase
        new_rating: The desired new rating
        category: The stat category (optional)
        subcategory: The stat subcategory (optional)
        reason: The reason for the spend (default: "")
        is_staff_spend: Whether this is staff-approved (default: False)
        
    Returns:
        tuple: (success, message) indicating result
    """
    character = self  # 'self' is the character when called as a method
    
    # Preserve original case of stat_name for special handling if needed
    original_stat_name = stat_name
    
    # Fix any power issues before proceeding
    if category == 'powers' and hasattr(self, 'fix_powers'):
        self.fix_powers()
        
        # After fixing, ensure we're using the correct subcategory
        if subcategory in ['sphere', 'art', 'realm', 'discipline', 'gift', 'charm', 'blessing', 
                          'rite', 'sorcery', 'thaumaturgy', 'necromancy', 'necromancy_ritual', 
                          'thaum_ritual', 'hedge_ritual', 'numina', 'faith']:
            # Convert to singular form
            subcategory = subcategory.rstrip('s')
            if subcategory == 'advantage':
                subcategory = 'special_advantage'
    
    # Special handling for secondary abilities original case
    if category == 'secondary_abilities':
        special_case_name = original_stat_name
        return process_xp_purchase(
            character=character,
            stat_name=special_case_name,
            new_rating=new_rating,
            category=category,
            subcategory=subcategory,
            reason=reason,
            is_staff_spend=is_staff_spend
        )
    
    # Get form modifier for shifters - this value will be used during the update_stat call
    form_modifier = 0
    if (character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '') == 'Shifter' and 
        hasattr(character.db, 'current_form') and character.db.current_form and 
        character.db.current_form.lower() != 'homid'):
        try:
            from world.wod20th.models import ShapeshifterForm
            shifter_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '').lower()
            
            # Calculate form modifier for temporary stat values
            form = ShapeshifterForm.objects.get(
                name__iexact=character.db.current_form,
                shifter_type=shifter_type
            )
            form_modifier = form.stat_modifiers.get(stat_name.lower(), 0)
            
            # Handle special cases for appearance and manipulation in certain forms
            zero_appearance_forms = [
                'crinos', 'anthros', 'arthren', 'sokto', 'chatro'
            ]
            
            if (stat_name.lower() == 'appearance' and 
                character.db.current_form.lower() in zero_appearance_forms):
                form_modifier = -999  # Force to 0
            elif (stat_name.lower() == 'manipulation' and 
                  character.db.current_form.lower() == 'crinos'):
                form_modifier = -2  # Crinos form penalty
                
        except (ShapeshifterForm.DoesNotExist, AttributeError) as e:
            logger.log_err(f"Form lookup error for {character.db.current_form}: {str(e)}")
    
    # Standard case - call process_xp_purchase
    success, message, cost = process_xp_purchase(
        character=character,
        stat_name=stat_name,
        new_rating=new_rating,
        category=category,
        subcategory=subcategory,
        reason=reason,
        is_staff_spend=is_staff_spend
    )
    
    # Apply form modifier if needed and purchase was successful
    if success and form_modifier != 0 and category and subcategory:
        try:
            # Calculate temporary value with form modifier
            if form_modifier == -999:  # Special case for forced 0
                temp_value = 0
            else:
                temp_value = max(0, new_rating + form_modifier)  # Ensure non-negative
                
            # Update just the temp value
            character.db.stats[category][subcategory][stat_name]['temp'] = temp_value
            logger.log_info(f"Applied form modifier {form_modifier} to {stat_name}, new temp value: {temp_value}")
        except Exception as e:
            logger.log_err(f"Error applying form modifier: {str(e)}")
    
    return success, message

def _determine_stat_category(stat_name):
    """
    Determine the category and type of a stat based on its name.
    """
    logger.log_info(f"Determining category for stat: {stat_name}")

    # Check for rituals first - case insensitive
    stat_name_lower = stat_name.lower()
    
    # Check Thaumaturgy rituals
    for ritual_name in THAUMATURGY_RITUALS:
        if ritual_name.lower() == stat_name_lower:
            logger.log_info(f"Found thaumaturgy ritual match: {ritual_name}")
            return ('powers', 'thaum_ritual')
            
    # Check Necromancy rituals
    for ritual_name in NECROMANCY_RITUALS:
        if ritual_name.lower() == stat_name_lower:
            logger.log_info(f"Found necromancy ritual match: {ritual_name}")
            return ('powers', 'necromancy_ritual')

    # Handle instanced stats - extract base name
    base_name = stat_name
    if '(' in stat_name and ')' in stat_name:
        base_name = stat_name[:stat_name.find('(')].strip()
        instance = stat_name[stat_name.find('(')+1:stat_name.find(')')].strip()
        logger.log_info(f"Extracted base name from instanced stat: {base_name}")

    # Check if it's a merit
    from world.wod20th.utils.stat_mappings import MERIT_VALUES
    for merit_category, merits in MERIT_VALUES.items():
        # Try exact match first
        if stat_name in merits:
            logger.log_info(f"Found merit match: {stat_name} in category {merit_category}")
            return ('merits', merit_category)
        # Try case-insensitive match
        stat_lower = stat_name.lower()
        for merit in merits:
            if isinstance(merit, str) and merit.lower() == stat_lower:
                logger.log_info(f"Found case-insensitive merit match: {merit}")
                return ('merits', merit_category)

    # Check if it's a flaw
    from world.wod20th.utils.stat_mappings import FLAW_VALUES
    for flaw_category, flaws in FLAW_VALUES.items():
        # Try exact match first
        if stat_name in flaws:
            logger.log_info(f"Found flaw match: {stat_name} in category {flaw_category}")
            return ('flaws', flaw_category)
        # Try case-insensitive match
        stat_lower = stat_name.lower()
        for flaw in flaws:
            if isinstance(flaw, str) and flaw.lower() == stat_lower:
                logger.log_info(f"Found case-insensitive flaw match: {flaw}")
                return ('flaws', flaw_category)

    # Check if it's a background (case-insensitive)
    all_backgrounds = (UNIVERSAL_BACKGROUNDS + VAMPIRE_BACKGROUNDS + 
                      CHANGELING_BACKGROUNDS + MAGE_BACKGROUNDS + 
                      TECHNOCRACY_BACKGROUNDS + TRADITIONS_BACKGROUNDS + 
                      NEPHANDI_BACKGROUNDS + SHIFTER_BACKGROUNDS + 
                      SORCERER_BACKGROUNDS + KINAIN_BACKGROUNDS)

    # Debug log all backgrounds
    logger.log_info(f"Available backgrounds: {all_backgrounds}")
    
    # Check for exact match first
    if base_name in all_backgrounds:
        logger.log_info(f"Found exact background match: {base_name}")
        return ('backgrounds', 'background')
        
    # Then try case-insensitive match
    base_name_lower = base_name.lower()
    
    # Create hyphenated and space-separated versions for more flexible matching
    base_name_with_hyphen = base_name_lower.replace(' ', '-')
    base_name_with_spaces = base_name_lower.replace('-', ' ')
    
    # Special mapping for commonly mistyped backgrounds
    background_mapping = {
        'professional certification': ('backgrounds', 'background', 'Professional Certification'),
        'professional-certification': ('backgrounds', 'background', 'Professional Certification'),
        'area knowledge': ('secondary_abilities', 'secondary_knowledge', 'Area Knowledge'),
        'area-knowledge': ('secondary_abilities', 'secondary_knowledge', 'Area Knowledge'),
        'cultural savvy': ('secondary_abilities', 'secondary_knowledge', 'Cultural Savvy'),
        'cultural-savvy': ('secondary_abilities', 'secondary_knowledge', 'Cultural Savvy'),
        'power-brokering': ('secondary_abilities', 'secondary_knowledge', 'Power-Brokering'),
        'power brokering': ('secondary_abilities', 'secondary_knowledge', 'Power-Brokering'),
        'primal-urge': ('abilities', 'talent', 'Primal-Urge'),
        'primal urge': ('abilities', 'talent', 'Primal-Urge'),
        'organizational rank': ('backgrounds', 'background', 'Organizational Rank'),
        'organizational-rank': ('backgrounds', 'background', 'Organizational Rank'),
        'paranormal tools': ('backgrounds', 'background', 'Paranormal Tools'),
        'paranormal-tools': ('backgrounds', 'background', 'Paranormal Tools')
    }
    
    # Check in the special mapping first
    if base_name_lower in background_mapping:
        mapping_info = background_mapping[base_name_lower]
        logger.log_info(f"Found special mapping match: {mapping_info}")
        return (mapping_info[0], mapping_info[1])  # Return category and subcategory
    
    if base_name_with_hyphen in background_mapping:
        mapping_info = background_mapping[base_name_with_hyphen]
        logger.log_info(f"Found special mapping match (hyphenated): {mapping_info}")
        return (mapping_info[0], mapping_info[1])  # Return category and subcategory
    
    if base_name_with_spaces in background_mapping:
        mapping_info = background_mapping[base_name_with_spaces]
        logger.log_info(f"Found special mapping match (with spaces): {mapping_info}")
        return (mapping_info[0], mapping_info[1])  # Return category and subcategory
    
    # Then check all backgrounds with more flexible matching
    for bg in all_backgrounds:
        if isinstance(bg, str):
            bg_lower = bg.lower()
            # Try hyphen and space variations
            if (bg_lower == base_name_lower or 
                bg_lower.replace('-', ' ') == base_name_lower or
                bg_lower.replace(' ', '-') == base_name_lower or
                bg_lower == base_name_with_hyphen or
                bg_lower == base_name_with_spaces):
                logger.log_info(f"Found flexible background match: {bg}")
                return ('backgrounds', 'background')

    logger.log_info(f"No background match found for: {base_name}")

    # Convert to proper title case for comparison
    stat_name = proper_title_case(stat_name)

    # Special case for pool stats (Willpower, Rage, Gnosis, Glamour)
    if stat_name in ['Willpower', 'Rage', 'Gnosis', 'Glamour']:
        return ('pools', 'dual')

    # Special case for pool stats (Arete, Enlightenment)
    if stat_name in ['Arete', 'Enlightenment']:
        return ('pools', 'advantage')

    # Define attributes first - these take precedence over other categories
    physical_attrs = ['Strength', 'Dexterity', 'Stamina']
    social_attrs = ['Charisma', 'Manipulation', 'Appearance']
    mental_attrs = ['Perception', 'Intelligence', 'Wits']

    # Check attributes first
    if stat_name in physical_attrs:
        return ('attributes', 'physical')
    elif stat_name in social_attrs:
        return ('attributes', 'social')
    elif stat_name in mental_attrs:
        return ('attributes', 'mental')

    # Check standard abilities
    if stat_name in TALENTS:
        return ('abilities', 'talent')
    elif stat_name in SKILLS:
        return ('abilities', 'skill')
    elif stat_name in KNOWLEDGES:
        return ('abilities', 'knowledge')

    # Check secondary abilities
    if stat_name in SECONDARY_TALENTS:
        return ('secondary_abilities', 'secondary_talent')
    elif stat_name in SECONDARY_SKILLS:
        return ('secondary_abilities', 'secondary_skill')
    elif stat_name in SECONDARY_KNOWLEDGES:
        return ('secondary_abilities', 'secondary_knowledge')
        
    # Additional check for secondary abilities with case insensitivity and hyphen/space variations
    stat_name_lower = stat_name.lower()
    # Try different formats (with hyphens or spaces)
    stat_with_hyphen = stat_name_lower.replace(' ', '-')
    stat_with_spaces = stat_name_lower.replace('-', ' ')
    
    # Special mappings for commonly used secondary abilities
    secondary_ability_mapping = {
        'power-brokering': ('secondary_abilities', 'secondary_knowledge'),
        'power brokering': ('secondary_abilities', 'secondary_knowledge'),
        'area knowledge': ('secondary_abilities', 'secondary_knowledge'),
        'area-knowledge': ('secondary_abilities', 'secondary_knowledge'),
        'cultural savvy': ('secondary_abilities', 'secondary_knowledge'),
        'cultural-savvy': ('secondary_abilities', 'secondary_knowledge'),
        'privacy obsession': ('secondary_abilities', 'secondary_knowledge'),
        'privacy-obsession': ('secondary_abilities', 'secondary_knowledge'),
    }
    
    # Check direct mapping first
    if stat_name_lower in secondary_ability_mapping:
        return secondary_ability_mapping[stat_name_lower]
    if stat_with_hyphen in secondary_ability_mapping:
        return secondary_ability_mapping[stat_with_hyphen]
    if stat_with_spaces in secondary_ability_mapping:
        return secondary_ability_mapping[stat_with_spaces]
    
    # Check secondary talents with flexible matching
    for talent in SECONDARY_TALENTS:
        talent_lower = talent.lower()
        if (talent_lower == stat_name_lower or 
            talent_lower.replace('-', ' ') == stat_name_lower or
            talent_lower.replace(' ', '-') == stat_name_lower or
            talent_lower == stat_with_hyphen or 
            talent_lower == stat_with_spaces):
            return ('secondary_abilities', 'secondary_talent')
            
    # Check secondary skills with flexible matching
    for skill in SECONDARY_SKILLS:
        skill_lower = skill.lower()
        if (skill_lower == stat_name_lower or 
            skill_lower.replace('-', ' ') == stat_name_lower or
            skill_lower.replace(' ', '-') == stat_name_lower or
            skill_lower == stat_with_hyphen or 
            skill_lower == stat_with_spaces):
            return ('secondary_abilities', 'secondary_skill')
            
    # Check secondary knowledges with flexible matching
    for knowledge in SECONDARY_KNOWLEDGES:
        knowledge_lower = knowledge.lower()
        if (knowledge_lower == stat_name_lower or 
            knowledge_lower.replace('-', ' ') == stat_name_lower or
            knowledge_lower.replace(' ', '-') == stat_name_lower or
            knowledge_lower == stat_with_hyphen or 
            knowledge_lower == stat_with_spaces):
            return ('secondary_abilities', 'secondary_knowledge')

    # Handle instanced stats - extract base name
    base_name = stat_name
    instance = None
    if '(' in stat_name and ')' in stat_name:
        base_name = stat_name[:stat_name.find('(')].strip()
        instance = stat_name[stat_name.find('(')+1:stat_name.find(')')].strip()
        
        # Check if base_name is a background
        if base_name.lower() in [bg.lower() for bg in BACKGROUNDS]:
            # It's an instanced background
            return ('backgrounds', 'background')

    # Check if it's a discipline - check both PURCHASABLE_DISCIPLINES and ALL_DISCIPLINES
    if base_name in PURCHASABLE_DISCIPLINES or base_name in CLAN_DISCIPLINES:
        return ('powers', 'discipline')
        
    # Case-insensitive check for disciplines
    base_name_lower = base_name.lower()
    for disc in CLAN_DISCIPLINES:
        if disc.lower() == base_name_lower:
            return ('powers', 'discipline')

    # Check if it's a thaumaturgy path
    if base_name in THAUMATURGY_PATHS:
        return ('powers', 'thaumaturgy')
    base_name_lower = base_name.lower()
    for thaum in THAUMATURGY_PATHS:
        if thaum.lower() == base_name_lower:
            return ('powers', 'thaumaturgy')

    # Check if it's a necromancy path
    if base_name in NECROMANCY_PATHS:
        return ('powers', 'necromancy')
    base_name_lower = base_name.lower()
    for necromancy in NECROMANCY_PATHS:
        if necromancy.lower() == base_name_lower:
            return ('powers', 'necromancy')
    # Check if it's a sphere
    if stat_name in MAGE_SPHERES:
        return ('powers', 'sphere')
    
    # Check the database for a gift with this name
    from world.wod20th.models import Stat
    from django.db.models import Q
    
    # Check for Changeling Arts first (to take precedence over gifts with similar names)
    CHANGELING_ARTS = ['Autumn', 'Chicanery', 'Chronos', 'Contract', "Dragon's Ire", 'Legerdemain', 'Metamorphosis', 'Naming', 
                       'Oneiromancy', 'Primal', 'Pyretics', 'Skycraft', 'Soothsay', 'Sovereign', 'Spring', 'Summer', 'Wayfare', 'Winter',
                       'Infusion', 'Kryos', 'Storm Craft']
    if stat_name in CHANGELING_ARTS or stat_name.lower() in [art.lower() for art in CHANGELING_ARTS]:
        return ('powers', 'art')
    
    # Special handling for Mother's Touch - it's always a gift
    if stat_name.lower() == "mother's touch":
        return ('powers', 'gift')
        
    # Check for gifts in database
    gift = Stat.objects.filter(
        (Q(name__iexact=stat_name) | Q(gift_alias__icontains=stat_name)),
        category='powers',
        stat_type='gift'
    ).first()
    
    # If not found by exact name, check aliases but be more precise
    if not gift:
        # For aliases, we need to be careful not to match partial words
        gifts = Stat.objects.filter(
            category='powers',
            stat_type='gift'
        )
        
        # Manual check for better alias matching
        for potential_gift in gifts:
            if potential_gift.gift_alias:
                try:
                    # Skip if not a string
                    if not isinstance(potential_gift.gift_alias, str):
                        continue
                        
                    # Compare case-insensitive
                    stat_lower = stat_name.lower()
                    
                    # Check the entire alias or if the stat is contained in the alias with word boundaries
                    if (stat_lower == potential_gift.gift_alias.lower() or 
                        f" {stat_lower} " in f" {potential_gift.gift_alias.lower()} "):
                        gift = potential_gift
                        break
                except:
                    continue
                    
            if gift:
                break
    
    if gift:
        return ('powers', 'gift')
        
    # Check if this is an Art (for Changeling)
    try:
        if stat_name.lower() == 'primal':
            return ('powers', 'art')
            
        if isinstance(ARTS, set):
            if stat_name in ARTS:
                return ('powers', 'art')
                
            stat_lower = stat_name.lower()
            for art in ARTS:
                if isinstance(art, str) and art.lower() == stat_lower:
                    return ('powers', 'art')
    except:
        pass
    
    # Check if it's a Realm (for Changeling)
    try:
        # Special case for 'nature' to match 'Nature' in REALMS
        if stat_name.lower() == 'nature':
            return ('powers', 'realm')
            
        if isinstance(REALMS, set):
            if stat_name in REALMS:
                return ('powers', 'realm')
                
            stat_lower = stat_name.lower()
            for realm in REALMS:
                if isinstance(realm, str) and realm.lower() == stat_lower:
                    return ('powers', 'realm')
    except:
        pass

    # Special handling for Time and Nature
    if base_name.lower() in ['time', 'nature']:
        from evennia import search_object
        from typeclasses.characters import Character
        from evennia.commands.default.muxcommand import MuxCommand
        from evennia import Command
        
        # Get the current command instance
        import inspect
        frame = inspect.currentframe()
        while frame:
            if 'self' in frame.f_locals:
                cmd_instance = frame.f_locals['self']
                if isinstance(cmd_instance, (Command, MuxCommand)):
                    break
            frame = frame.f_back
        
        if frame and 'self' in frame.f_locals:
            cmd = frame.f_locals['self']
            if hasattr(cmd, 'caller'):
                char = cmd.caller
                if cmd.switches and 'staffspend' in cmd.switches and cmd.args:
                    target_name = cmd.args.split('/')[0].strip()
                    target = search_object(target_name, typeclass=Character)
                    if target:
                        char = target[0]
                
                if char:
                    splat = char.get_stat('other', 'splat', 'Splat', temp=False)
                    char_type = char.get_stat('identity', 'lineage', 'Type', temp=False)
                    
                    if base_name.lower() == 'time':
                        if splat == 'Mage':
                            return ('powers', 'sphere')
                        elif splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain'):
                            return ('powers', 'realm')
                    elif base_name.lower() == 'nature':
                        if splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain'):
                            return ('powers', 'realm')
                        else:
                            return ('identity', 'personal')

    # Do a final check for merits and flaws from MERIT_VALUES and FLAW_VALUES
    # This is a fallback just in case the earlier search didn't catch these
    from world.wod20th.utils.stat_mappings import MERIT_VALUES, FLAW_VALUES
    
    for merit_category, merits in MERIT_VALUES.items():
        for merit in merits:
            if isinstance(merit, str) and (merit.lower() == stat_name.lower() or 
                                          merit.lower() == base_name_lower):
                logger.log_info(f"Found merit match (fallback): {merit}")
                return ('merits', merit_category)
    
    for flaw_category, flaws in FLAW_VALUES.items():
        for flaw in flaws:
            if isinstance(flaw, str) and (flaw.lower() == stat_name.lower() or 
                                         flaw.lower() == base_name_lower):
                logger.log_info(f"Found flaw match (fallback): {flaw}")
                return ('flaws', flaw_category)

    # If no match found
    return None, None

def _is_affinity_sphere(self, sphere):
    """Helper method to check if a sphere is an affinity sphere."""
    # Check in identity.lineage first (this seems to be where it's actually stored)
    affinity_sphere = self.db.stats.get('identity', {}).get('lineage', {}).get('Affinity Sphere', {}).get('perm', '')
    
    # If not found, check identity.personal as fallback
    if not affinity_sphere:
        affinity_sphere = self.db.stats.get('identity', {}).get('personal', {}).get('Affinity Sphere', {}).get('perm', '')
    
    return sphere == affinity_sphere
    
def calculate_gift_cost(character, gift_name, new_rating, current_rating=None):
    """Calculate the XP cost for a gift."""
    try:
        # Get character's shifter type and aspect
        shifter_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
        logger.log_info(f"Calculating gift cost for {shifter_type} character")

        # For Ajaba, get their aspect
        aspect = None
        if shifter_type == 'Ajaba':
            aspect = character.db.stats.get('identity', {}).get('lineage', {}).get('Aspect', {}).get('perm', '')
            logger.log_info(f"Ajaba character with aspect: {aspect}")

        # Get the gift details from the database
        from world.wod20th.models import Stat
        from django.db.models import Q
        
        gift = Stat.objects.filter(
            Q(name__iexact=gift_name) | Q(gift_alias__icontains=gift_name),
            category='powers',
            stat_type='gift'
        ).first()
        
        if gift:
            logger.log_info(f"Found gift in database: {gift.name}")
            
            # For Ajaba, check if the gift matches their aspect
            if shifter_type == 'Ajaba':
                if gift.auspice:
                    auspices = gift.auspice if isinstance(gift.auspice, list) else [gift.auspice]
                    is_aspect_gift = aspect and aspect.lower() in [a.lower() for a in auspices]
                    logger.log_info(f"Checking aspect gift - Character aspect: {aspect}, Gift auspices: {auspices}, Is aspect gift: {is_aspect_gift}")
                    
                    # For Ajaba, aspect gifts cost 3 XP per level
                    if is_aspect_gift:
                        cost = new_rating * 3
                        logger.log_info(f"Aspect gift cost for Ajaba: {cost}")
                        return cost
                
                # Non-aspect gifts cost 5 XP per level for Ajaba
                cost = new_rating * 5
                logger.log_info(f"Non-aspect gift cost for Ajaba: {cost}")
                return cost
            
            # For other shifter types, use their specific cost structure
            elif shifter_type and shifter_type.lower() != 'garou':
                # Check if this is a gift available to their shifter type
                if gift.shifter_type:
                    allowed_types = gift.shifter_type if isinstance(gift.shifter_type, list) else [gift.shifter_type]
                    if shifter_type.lower() in [t.lower() for t in allowed_types]:
                        # Base cost of 3 XP per level for gifts available to their type
                        cost = new_rating * 3
                        logger.log_info(f"Shifter type gift cost for {shifter_type}: {cost}")
                        return cost
                    else:
                        # Higher cost (5 XP per level) for gifts not native to their type
                        cost = new_rating * 5
                        logger.log_info(f"Non-native gift cost for {shifter_type}: {cost}")
                        return cost
                
                # Default cost if shifter_type not specified in gift
                cost = new_rating * 3
                logger.log_info(f"Default gift cost for {shifter_type}: {cost}")
                return cost
            
            # For Garou, check if it's a breed, auspice, or tribe gift
            breed = character.get_stat('identity', 'lineage', 'Breed', temp=False)
            auspice = character.get_stat('identity', 'lineage', 'Auspice', temp=False)
            tribe = character.get_stat('identity', 'lineage', 'Tribe', temp=False)
            
            logger.log_info(f"Character details - Breed: {breed}, Auspice: {auspice}, Tribe: {tribe}, Type: {shifter_type}")
            
            is_breed_gift = False
            is_auspice_gift = False
            is_tribe_gift = False
            is_special = False
            
            # Check breed gifts
            if gift.shifter_type:
                allowed_types = gift.shifter_type if isinstance(gift.shifter_type, list) else [gift.shifter_type]
                is_breed_gift = breed and breed.lower() in [t.lower() for t in allowed_types]
            
            # Check auspice gifts
            if gift.auspice:
                allowed_auspices = gift.auspice if isinstance(gift.auspice, list) else [gift.auspice]
                is_auspice_gift = auspice and auspice.lower() in [a.lower() for a in allowed_auspices]
                logger.log_info(f"Checking auspice gift - Character auspice: {auspice}, Gift auspices: {allowed_auspices}, Is auspice gift: {is_auspice_gift}")
            
            # Check tribe gifts and special gifts
            if gift.tribe:
                tribes = gift.tribe if isinstance(gift.tribe, list) else [gift.tribe]
                logger.log_info(f"Gift data - tribe: {tribes}, type: {type(tribes)}")
                is_tribe_gift = tribe and tribe.lower() in [t.lower() for t in tribes]
                is_special = any(t.lower() in ['croatan', 'planetary', 'ju-fu'] for t in tribes)
                logger.log_info(f"Tribe check details - Character tribe: {tribe}, Gift tribes: {tribes}")
            
            logger.log_info(f"Gift type checks - Breed: {is_breed_gift}, Auspice: {is_auspice_gift}, Tribe: {is_tribe_gift}, Special: {is_special}")
            
            # Calculate cost based on gift type
            if is_special:
                cost = new_rating * 7  # Croatan/Planetary gifts cost 7 XP per level
                logger.log_info(f"Special gift cost: {cost}")
            elif is_breed_gift or is_auspice_gift or is_tribe_gift:
                cost = new_rating * 3  # Breed/Auspice/Tribe gifts cost 3 XP per level
                logger.log_info(f"Breed/Auspice/Tribe gift cost: {cost}")
            else:
                cost = new_rating * 5  # Other gifts cost 5 XP per level
                logger.log_info(f"Other gift cost: {cost}")
            
            return cost
        
        # If gift not found in database, use base cost
        cost = new_rating * 3  # Base cost of 3 XP per level
        logger.log_info(f"Default cost for gift not found in database: {cost}")
        return cost
        
    except Exception as e:
        logger.log_err(f"Error calculating gift cost: {str(e)}")
        return 0
    
def check_weekly_xp_eligibility():
    """
    Check all characters for weekly XP eligibility.
    Returns a tuple of (eligible_count, total_xp_to_award, detailed_report)
    """
    # Find all character objects
    characters = ObjectDB.objects.filter(
        db_typeclass_path__contains='typeclasses.characters.Character'
    )
    
    report_lines = []
    report_lines.append(f"\nChecking {len(characters)} characters for weekly XP eligibility...")
    report_lines.append("=" * 60)
    
    eligible_count = 0
    error_count = 0
    base_xp = Decimal('4.00')
    
    # Track characters with data issues
    data_issues = []
    
    for char in characters:
        try:
            # Skip if character is staff
            if hasattr(char, 'check_permstring') and char.check_permstring("builders"):
                continue
                
            # Get character's XP data
            xp_data = None
            if hasattr(char, 'db') and hasattr(char.db, 'xp'):
                xp_data = char.db.xp
            if not xp_data:
                xp_data = char.attributes.get('xp')
                
            if not xp_data:
                report_lines.append(f"{char.key}: No XP data found")
                data_issues.append((char.key, "No XP data found"))
                continue
                
            # Handle string XP data
            if isinstance(xp_data, str):
                try:
                    # First try to clean up the string for evaluation
                    cleaned_str = xp_data.replace("Decimal('", "'")
                    cleaned_str = cleaned_str.replace("')", "'")
                    
                    # Try to parse the cleaned string
                    parsed_data = ast.literal_eval(cleaned_str)
                    
                    # Convert string values back to Decimal objects
                    if isinstance(parsed_data, dict):
                        for key in ['total', 'current', 'spent', 'ic_xp', 'monthly_spent']:
                            if key in parsed_data and isinstance(parsed_data[key], str):
                                parsed_data[key] = Decimal(parsed_data[key])
                        xp_data = parsed_data
                    else:
                        raise ValueError("Parsed data is not a dictionary")
                except Exception as e:
                    error_msg = f"Invalid XP data format: {str(e)}"
                    report_lines.append(f"{char.key}: {error_msg}")
                    data_issues.append((char.key, error_msg))
                    error_count += 1
                    continue
            
            # Check scenes this week
            scenes_this_week = xp_data.get('scenes_this_week', 0)
            
            # Get last scene time
            last_scene = None
            if xp_data.get('last_scene'):
                try:
                    last_scene = datetime.fromisoformat(xp_data['last_scene'])
                except (ValueError, TypeError):
                    last_scene = None
            
            # Add character status to report
            report_lines.append(f"\nCharacter: {char.key}")
            report_lines.append(f"Scenes this week: {scenes_this_week}")
            report_lines.append(f"Last scene: {last_scene.strftime('%Y-%m-%d %H:%M') if last_scene else 'Never'}")
            
            # Check eligibility
            if scenes_this_week > 0:
                eligible_count += 1
                report_lines.append(f"Status: ELIGIBLE for {base_xp} XP")
                
                # Calculate what their new totals would be
                try:
                    current = Decimal(str(xp_data.get('current', '0.00')))
                    total = Decimal(str(xp_data.get('total', '0.00')))
                    ic_xp = Decimal(str(xp_data.get('ic_xp', '0.00')))
                    
                    report_lines.append(f"Current XP: {current}")
                    report_lines.append(f"Would receive: +{base_xp} XP")
                    report_lines.append(f"New total would be: {current + base_xp}")
                except Exception as e:
                    error_msg = f"Error calculating XP totals: {str(e)}"
                    report_lines.append(error_msg)
                    data_issues.append((char.key, error_msg))
            else:
                report_lines.append("Status: NOT ELIGIBLE - No scenes this week")
                
        except Exception as e:
            error_msg = f"Unexpected error processing character: {str(e)}"
            report_lines.append(f"{char.key}: {error_msg}")
            data_issues.append((char.key, error_msg))
            error_count += 1
    
    # Add data issues summary to report
    if data_issues:
        report_lines.append("\n" + "=" * 60)
        report_lines.append("Characters with Data Issues:")
        for char_name, issue in data_issues:
            report_lines.append(f"- {char_name}: {issue}")
    
    report_lines.append("\n" + "=" * 60)
    report_lines.append(f"Summary:")
    report_lines.append(f"- {eligible_count} characters eligible for weekly XP")
    report_lines.append(f"- {error_count} characters with data issues")
    report_lines.append(f"- Total XP that would be awarded: {base_xp * eligible_count}")
    
    return eligible_count, base_xp * eligible_count, "\n".join(report_lines)

def _check_shifter_gift_match(character, gift_data, shifter_type):
    """Helper function to check if a gift matches a shifter's breed/auspice/tribe.
    
    Args:
        character: The character object
        gift_data: Dictionary containing gift data (name, shifter_type, tribe, auspice, breed, etc.)
        shifter_type: The character's shifter type (Garou, Ananasi, etc.)
        
    Returns:
        tuple: (is_breed_gift, is_auspice_gift, is_tribe_gift)
    """
    logger.log_info(f"Checking gift match for {shifter_type} - Gift data: {gift_data}")
    
    if not shifter_type or shifter_type not in SHIFTER_MAPPINGS:
        return False, False, False

    mapping = SHIFTER_MAPPINGS[shifter_type]
    
    # Get character's details
    breed = character.get_stat('identity', 'lineage', 'Breed', temp=False)
    aspect = character.get_stat('identity', 'lineage', 'Aspect', temp=False)
    auspice = character.get_stat('identity', 'lineage', 'Auspice', temp=False)
    tribe = character.get_stat('identity', 'lineage', 'Tribe', temp=False)
    faction = character.get_stat('identity', 'lineage', 'Faction', temp=False)
    path = character.get_stat('identity', 'lineage', 'Kitsune Path', temp=False)
    
    logger.log_info(f"Character details - Breed: {breed}, Aspect: {aspect}, Auspice: {auspice}, Tribe: {tribe}, Faction: {faction}, Path: {path}")

    # Special case for Corax and Nuwisha - all non-breed gifts are considered in-tribe
    if mapping.get('all_gifts_in_tribe'):
        is_breed_gift = False
        if gift_data.get('breed'):
            allowed_breeds = gift_data['breed'] if isinstance(gift_data['breed'], list) else [gift_data['breed']]
            mapped_breed = mapping['breed_mappings'].get(breed)
            is_breed_gift = mapped_breed and mapped_breed.lower() in [b.lower() for b in allowed_breeds]
            # Also check if the actual breed name is in the allowed breeds
            is_breed_gift = is_breed_gift or breed.lower() in [b.lower() for b in allowed_breeds]
        return is_breed_gift, True, True

    # Check breed gifts
    is_breed_gift = False
    if gift_data.get('breed') and breed:
        allowed_breeds = gift_data['breed'] if isinstance(gift_data['breed'], list) else [gift_data['breed']]
        mapped_breed = mapping['breed_mappings'].get(breed)
        
        # Check both mapped breed and actual breed name
        is_breed_gift = mapped_breed and mapped_breed.lower() in [b.lower() for b in allowed_breeds]
        is_breed_gift = is_breed_gift or breed.lower() in [b.lower() for b in allowed_breeds]
        
        # Check for special breed-specific gifts
        if mapping.get('special_breed_gifts', {}).get(breed):
            is_breed_gift = is_breed_gift or breed.lower() in [b.lower() for b in allowed_breeds]
        
        logger.log_info(f"Breed gift check - Mapped breed: {mapped_breed}, Is breed gift: {is_breed_gift}")

    # Check auspice/aspect/path gifts
    is_auspice_gift = False
    if gift_data.get('auspice'):
        allowed_auspices = gift_data['auspice'] if isinstance(gift_data['auspice'], list) else [gift_data['auspice']]
        logger.log_info(f"Checking auspice gift - Allowed auspices: {allowed_auspices}")
        
        # Handle different auspice-like attributes based on shifter type
        if mapping.get('aspects_to_auspices') and aspect:
            is_auspice_gift = aspect in mapping['aspects_to_auspices']
            logger.log_info(f"Checking aspect as auspice - Aspect: {aspect}, Is auspice gift: {is_auspice_gift}")
            
        elif mapping.get('factions_to_auspices') and faction:
            is_auspice_gift = faction in mapping['factions_to_auspices']
            logger.log_info(f"Checking faction as auspice - Faction: {faction}, Is auspice gift: {is_auspice_gift}")
            
        elif mapping.get('paths_to_auspices') and path:
            is_auspice_gift = path in mapping['paths_to_auspices']
            logger.log_info(f"Checking path as auspice - Path: {path}, Is auspice gift: {is_auspice_gift}")
            
        elif mapping.get('auspices') and auspice:
            # Handle direct auspice matches and mappings
            if auspice in mapping['auspices']:
                is_auspice_gift = auspice.lower() in [a.lower() for a in allowed_auspices]
            elif mapping.get('auspice_mappings', {}).get(auspice):
                mapped_auspice = mapping['auspice_mappings'][auspice]
                is_auspice_gift = mapped_auspice.lower() in [a.lower() for a in allowed_auspices]
            logger.log_info(f"Checking direct auspice - Auspice: {auspice}, Mapped: {mapping.get('auspice_mappings', {}).get(auspice)}, Is auspice gift: {is_auspice_gift}")

    # Check tribe/aspect gifts
    is_tribe_gift = False
    if gift_data.get('tribe') and tribe:
        allowed_tribes = gift_data['tribe'] if isinstance(gift_data['tribe'], list) else [gift_data['tribe']]
        logger.log_info(f"Checking tribe gift - Allowed tribes: {allowed_tribes}, Character tribe: {tribe}")
        
        # Special handling for Bastet tribes
        if shifter_type == 'Bastet':
            # Convert tribe names to lowercase for comparison
            tribe_lower = tribe.lower()
            allowed_tribes_lower = [t.lower() for t in allowed_tribes]
            
            # Check if the tribe is in the allowed tribes list
            is_tribe_gift = tribe_lower in allowed_tribes_lower
            
            logger.log_info(f"Bastet tribe check - Tribe: {tribe_lower}, Allowed tribes: {allowed_tribes_lower}, Is tribe gift: {is_tribe_gift}")
        else:
            # Handle different tribe-like attributes
            if mapping.get('aspects_to_tribes') and aspect:
                is_tribe_gift = aspect in mapping['aspects_to_tribes'] and aspect.lower() in [t.lower() for t in allowed_tribes]
                logger.log_info(f"Checking aspect as tribe - Aspect: {aspect}, Is tribe gift: {is_tribe_gift}")
            elif mapping.get('tribes'):
                # For other shifters with direct tribe matches
                is_tribe_gift = tribe.lower() in [t.lower() for t in allowed_tribes]
                logger.log_info(f"Checking direct tribe - Tribe: {tribe}, Allowed tribes: {allowed_tribes}, Is tribe gift: {is_tribe_gift}")

    # Special case for Kitsune ju-fu gifts
    if shifter_type == 'Kitsune' and mapping.get('special_gifts', {}).get('ju-fu'):
        if gift_data.get('gift_type') == 'ju-fu':
            logger.log_info("Found Kitsune ju-fu gift")
            return False, False, True  # Return special flag for ju-fu gifts

    logger.log_info(f"Final gift match results for {shifter_type}:")
    logger.log_info(f"- Breed gift: {is_breed_gift}")
    logger.log_info(f"- Auspice gift: {is_auspice_gift}")
    logger.log_info(f"- Tribe gift: {is_tribe_gift}")
    logger.log_info(f"- Gift data: {gift_data}")
    logger.log_info(f"- Character tribe: {tribe}")

    return is_breed_gift, is_auspice_gift, is_tribe_gift

def _handle_path_disciplines(character, stat_name, new_rating, current_rating, subcategory):
    """Handle Thaumaturgy and Necromancy path updates."""
    if subcategory == 'thaumaturgy':
        if 'thaumaturgy' not in character.db.stats['powers']:
            character.db.stats['powers']['thaumaturgy'] = {}
        # Normalize path name to title case with 'of' lowercase
        normalized_name = ' '.join(word.title() if word.lower() != 'of' else 'of' 
                                for word in stat_name.split())
        # Remove any existing path with different case
        for existing_path in list(character.db.stats['powers']['thaumaturgy'].keys()):
            if existing_path.lower() == normalized_name.lower():
                if existing_path != normalized_name:
                    # Transfer the existing rating to the normalized name
                    existing_rating = character.db.stats['powers']['thaumaturgy'][existing_path]
                    del character.db.stats['powers']['thaumaturgy'][existing_path]
                    character.db.stats['powers']['thaumaturgy'][normalized_name] = existing_rating
                    logger.log_info(f"Normalized path name from {existing_path} to {normalized_name}")
        # Set the new rating
        character.db.stats['powers']['thaumaturgy'][normalized_name] = {
            'perm': new_rating,
            'temp': new_rating
        }
        logger.log_info(f"Updated thaumaturgy path {normalized_name} to {new_rating}")
        return True
    elif subcategory == 'necromancy':
        if 'necromancy' not in character.db.stats['powers']:
            character.db.stats['powers']['necromancy'] = {}
        character.db.stats['powers']['necromancy'][stat_name] = {
            'perm': new_rating,
            'temp': new_rating
        }
        return True
    return False

def _handle_blessing_updates(character, stat_name, new_rating):
    """Handle special cases for blessings that modify other stats."""
    if 'blessing' not in character.db.stats['powers']:
        character.db.stats['powers']['blessing'] = {}
    # Validate against BLESSINGS list
    if stat_name not in BLESSINGS:
        return False, f"{stat_name} is not a valid blessing"
    character.db.stats['powers']['blessing'][stat_name] = {
        'perm': new_rating,
        'temp': new_rating
    }
    
    # Handle special cases for blessings that modify other stats
    splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
    if splat == 'Possessed':
        if stat_name == 'Spirit Ties':
            # Spirit Ties adds to Gnosis pool
            gnosis_pool = character.db.stats.get('pools', {}).get('dual', {}).get('Gnosis', {})
            if gnosis_pool:
                base_gnosis = 1  # Base Gnosis for Possessed
                new_gnosis = base_gnosis + new_rating
                gnosis_pool['perm'] = new_gnosis
                gnosis_pool['temp'] = new_gnosis
                logger.log_info(f"Updated Gnosis to {new_gnosis} based on Spirit Ties rating {new_rating}")
        elif stat_name == 'Berserker':
            # Berserker sets Rage pool to 5
            rage_pool = character.db.stats.get('pools', {}).get('dual', {}).get('Rage', {})
            if rage_pool:
                rage_pool['perm'] = 5
                rage_pool['temp'] = 5
                logger.log_info("Set Rage pool to 5 based on Berserker blessing")
    return True, None

def _handle_special_advantage_updates(character, stat_name, new_rating):
    """Handle special advantage updates including Ferocity."""
    if 'special_advantage' not in character.db.stats['powers']:
        character.db.stats['powers']['special_advantage'] = {}

    # Special handling for Ferocity by name
    is_ferocity = stat_name.lower() == 'ferocity'
        
    # Check if it's in SPECIAL_ADVANTAGES
    if stat_name.lower() in SPECIAL_ADVANTAGES:
        advantage_info = SPECIAL_ADVANTAGES[stat_name.lower()]
        if new_rating in advantage_info['valid_values']:
            # Set the special advantage
            character.db.stats['powers']['special_advantage'][stat_name.lower()] = {
                'perm': new_rating,
                'temp': new_rating
            }
            logger.log_info(f"Updated special advantage {stat_name} to {new_rating}")
            
            # Handle Ferocity special case - update Rage
            if is_ferocity:
                _update_ferocity_rage(character, new_rating)
            return True, None
        else:
            return False, f"Invalid rating for {stat_name}. Valid values are: {advantage_info['valid_values']}"
    # Check if it's in COMBAT_SPECIAL_ADVANTAGES
    elif stat_name.lower() in COMBAT_SPECIAL_ADVANTAGES:
        advantage_info = COMBAT_SPECIAL_ADVANTAGES[stat_name.lower()]
        if new_rating in advantage_info['valid_values']:
            character.db.stats['powers']['special_advantage'][stat_name.lower()] = {
                'perm': new_rating,
                'temp': new_rating
            }
            logger.log_info(f"Updated combat special advantage {stat_name} to {new_rating}")
            return True, None
        else:
            return False, f"Invalid rating for {stat_name}. Valid values are: {advantage_info['valid_values']}"
    return False, f"{stat_name} is not a valid special advantage"

def _update_ferocity_rage(character, ferocity_rating):
    """Update Rage pool based on Ferocity rating."""
    # Initialize pools structure if it doesn't exist
    if 'pools' not in character.db.stats:
        character.db.stats['pools'] = {}
    if 'dual' not in character.db.stats['pools']:
        character.db.stats['pools']['dual'] = {}
    
    # Calculate Rage based on Ferocity level
    rage_value = ferocity_rating // 2
    
    # Create Rage pool if it doesn't exist
    if 'Rage' not in character.db.stats['pools']['dual']:
        character.db.stats['pools']['dual']['Rage'] = {}
        
    # Explicitly set both permanent and temporary values
    character.db.stats['pools']['dual']['Rage']['perm'] = rage_value
    character.db.stats['pools']['dual']['Rage']['temp'] = rage_value
    
    logger.log_info(f"Set Rage pool to {rage_value} based on Ferocity {ferocity_rating}")

def _handle_kinfolk_gnosis(character, new_rating):
    """Handle Gnosis merit updates for Kinfolk characters."""
    # Initialize pools structure if it doesn't exist
    if 'pools' not in character.db.stats:
        character.db.stats['pools'] = {}
    if 'dual' not in character.db.stats['pools']:
        character.db.stats['pools']['dual'] = {}
    
    # Calculate Gnosis based on the merit level
    # The Gnosis merit at 7 = Gnosis 3, 6 = Gnosis 2, 5 = Gnosis 1
    if new_rating == 5:
        gnosis_value = 1
    elif new_rating == 6:
        gnosis_value = 2
    elif new_rating == 7:
        gnosis_value = 3
    else:
        gnosis_value = 0  # Invalid merit rating
    
    # Create or update Gnosis pool
    if 'Gnosis' not in character.db.stats['pools']['dual']:
        character.db.stats['pools']['dual']['Gnosis'] = {}
    
    # Set both permanent and temporary values
    character.db.stats['pools']['dual']['Gnosis']['perm'] = gnosis_value
    character.db.stats['pools']['dual']['Gnosis']['temp'] = gnosis_value
    
    logger.log_info(f"Set Gnosis pool to {gnosis_value} based on Gnosis merit level {new_rating} for Kinfolk character")

def calculate_sphere_cost(character, sphere_name: str, new_rating: int, current_rating: int, is_staff_spend: bool = False) -> tuple:
    """
    Calculate the XP cost for increasing a Mage sphere.
    
    Args:
        character: The character object
        sphere_name: Name of the sphere
        new_rating: The new rating to increase to
        current_rating: The current rating of the sphere
        is_staff_spend: Whether this is a staff-approved spend
        
    Returns:
        tuple: (cost, requires_approval, error_message)
    """
    from world.wod20th.utils.mage_utils import is_affinity_sphere
    from world.wod20th.utils.xp_costs import calculate_sphere_cost as calculate_sphere_cost_imported
    from evennia.utils import logger
    
    logger.log_trace(f"Processing Mage sphere")
    logger.log_trace(f"Current sphere rating: {current_rating}")
    
    # Validate inputs
    if new_rating <= current_rating:
        return 0, False, "No increase needed"
    
    # Check if this is an affinity sphere
    is_affinity = is_affinity_sphere(character, sphere_name)
    logger.log_trace(f"Is {sphere_name} an affinity sphere? {is_affinity}")
    
    # Calculate cost using the imported function
    total_cost = calculate_sphere_cost_imported(current_rating, new_rating, is_affinity)
    
    # Check if approval is required (spheres above 1 require approval unless staff spend)
    requires_approval = new_rating > 1 and not is_staff_spend
    
    logger.log_trace(f"Calculated sphere cost: {total_cost}, requires approval: {requires_approval}, error: None")
    return total_cost, requires_approval, None

def get_stat(self, category, subcategory, stat_name, temp=True):
    """
    Get a stat, handling nested dictionaries properly.
    
    Args:
        category (str): The top-level category (e.g., 'attributes', 'abilities')
        subcategory (str): The subcategory (e.g., 'physical', 'mental')
        stat_name (str): The name of the stat
        temp (bool): Whether to get the temporary value (default) or permanent value
        
    Returns:
        The stat value, or None if not found
    """
    try:
        if not hasattr(self, 'db') or not hasattr(self.db, 'stats'):
            return None
        
        if category not in self.db.stats:
            return None
        
        if subcategory not in self.db.stats[category]:
            return None
        
        # Special handling for case-insensitive stat names (especially for abilities)
        if category in ['abilities', 'secondary_abilities']:
            # Try to find the stat with case-insensitive matching
            stat_name_lower = stat_name.lower()
            for existing_name, values in self.db.stats[category][subcategory].items():
                if existing_name.lower() == stat_name_lower:
                    # Return permanent or temporary value as requested
                    if isinstance(values, dict):
                        return values.get('perm' if not temp else 'temp', 0)
                    return values
            # If not found with case-insensitive matching, proceed with normal lookup
        
        # Normal stat lookup
        if stat_name not in self.db.stats[category][subcategory]:
            return None
        
        stat_data = self.db.stats[category][subcategory][stat_name]
        if isinstance(stat_data, dict):
            key = 'temp' if temp else 'perm'
            return stat_data.get(key, None)
        return stat_data
    except Exception as e:
        return None

def staff_spend(self, stat_name, new_rating, category=None, subcategory=None, reason=""):
    """
    Wrapper for process_xp_purchase with staff approval.
    
    Args:
        stat_name: The name of the stat to increase
        new_rating: The desired new rating
        category: The stat category (optional)
        subcategory: The stat subcategory (optional)
        reason: The reason for the staff spend (default: "")
        
    Returns:
        tuple: (success, message, cost) indicating result
    """
    caller = self.caller
    target = self.target
    
    if not target:
        caller.msg("No target set.")
        return False, "No target set.", 0
        
    # If no category/subcategory provided, try to determine them
    if not category or not subcategory:
        cat_subcat = _determine_stat_category(stat_name)
        if cat_subcat:
            category, subcategory = cat_subcat
        else:
            return False, f"Could not determine category for {stat_name}", 0
    
    # Process the purchase as a staff spend
    return process_xp_purchase(
        character=target,
        stat_name=stat_name,
        new_rating=new_rating,
        category=category,
        subcategory=subcategory,
        reason=f"Staff Spend: {reason}",
        is_staff_spend=True
    )

def proper_title_case(text):
    """
    Convert text to proper title case, handling hyphenated words and keeping certain words lowercase.
    
    Args:
        text (str): The text to convert
        
    Returns:
        str: The properly title-cased text
    """
    if not text:
        return text
        
    # List of words that should remain lowercase (unless at beginning or end)
    lowercase_words = {'of', 'the', 'and', 'in', 'for', 'from', 'with', 'to', 'a', 'an'}
    
    # Handle hyphenated words first
    if '-' in text:
        parts = text.split('-')
        # Capitalize each part after hyphen
        return '-'.join(proper_title_case(part) for part in parts)
    
    # Split by spaces for normal title casing
    words = text.split()
    result = []
    
    for i, word in enumerate(words):
        # Always capitalize first and last word
        if i == 0 or i == len(words) - 1:
            # Handle apostrophes like "Mother's"
            if "'" in word:
                parts = word.split("'", 1)
                result.append(parts[0].capitalize() + "'" + parts[1].lower())
            else:
                result.append(word.capitalize())
        # Keep lowercase words lowercase
        elif word.lower() in lowercase_words:
            result.append(word.lower())
        # Handle apostrophes
        elif "'" in word:
            parts = word.split("'", 1)
            result.append(parts[0].capitalize() + "'" + parts[1].lower())
        # Regular capitalization
        else:
            result.append(word.capitalize())
            
    return ' '.join(result)

def normalize_stat_name(stat_name, category, subcategory):
    """
    Normalize a stat name to ensure proper capitalization.
    
    Args:
        stat_name (str): The stat name to normalize
        category (str): The stat category
        subcategory (str): The stat subcategory
        
    Returns:
        str: The normalized stat name
    """
    if not stat_name:
        return stat_name
        
    # Convert to string if it's not already
    stat_name = str(stat_name)
    stat_name_lower = stat_name.lower()
    
    # Apply proper title case to the stat name
    normalized_name = proper_title_case(stat_name)
    
    # Special cases for specific stats
    if category == 'backgrounds':
        # For backgrounds, all words should be capitalized
        if '(' in normalized_name and ')' in normalized_name:
            # Handle instanced backgrounds (e.g., "Allies(Police)")
            base_name, instance = normalized_name.split('(', 1)
            instance = instance.rstrip(')')
            normalized_name = f"{base_name.strip()}({proper_title_case(instance)})"
        return normalized_name
        
    # For attributes, abilities, etc. use proper title case
    return normalized_name

def process_xp_spend(character, stat_name, new_rating, category, subcategory, reason="", is_staff_spend=False):
    """
    Process an XP spend request.
    
    Args:
        character: The character object
        stat_name: The name of the stat to increase
        new_rating: The desired new rating
        category: The stat category
        subcategory: The stat subcategory
        reason: The reason for the spend
        is_staff_spend: Whether this is a staff-approved purchase
        
    Returns:
        tuple: (success, message, cost)
    """
    try:
        # Store the original stat name for later use with gift aliases
        original_stat_name = stat_name
        
        # Determine category and subcategory if not provided
        if not category or not subcategory:
            cat_subcat = _determine_stat_category(stat_name)
            if cat_subcat:
                category, subcategory = cat_subcat
            else:
                # Try to check if it's a merit or flaw before giving up
                from world.wod20th.utils.stat_mappings import MERIT_VALUES, FLAW_VALUES
                
                # Check merit categories
                for merit_category, merits in MERIT_VALUES.items():
                    if stat_name in merits or stat_name.lower() in [m.lower() for m in merits]:
                        logger.log_info(f"Found merit match: {stat_name} in category {merit_category}")
                        category = 'merits'
                        subcategory = merit_category
                        break
                
                # Check flaw categories
                if not category:
                    for flaw_category, flaws in FLAW_VALUES.items():
                        if stat_name in flaws or stat_name.lower() in [f.lower() for f in flaws]:
                            logger.log_info(f"Found flaw match: {stat_name} in category {flaw_category}")
                            category = 'flaws'
                            subcategory = flaw_category
                            break
                
                # If still not found
                if not category:
                    return False, f"Could not determine category for {stat_name}", 0

        # Get character's splat and type
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        char_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
        
        if not splat:
            return False, "Character splat not set", 0
        
        # Store the original stat name before normalization
        original_stat_name = stat_name
        
        # Normalize the stat name
        normalized_stat_name = normalize_stat_name(stat_name, category, subcategory)
        
        # Update the stat_name with the normalized version but preserve original for alias purposes
        stat_name = normalized_stat_name
        
        # Log the normalization
        if stat_name != original_stat_name:
            logger.log_info(f"Normalized stat name: '{original_stat_name}' -> '{stat_name}'")
        
        # Special handling for gifts - check if this is an alias
        canonical_gift_name = None
        if category == 'powers' and subcategory == 'gift':
            from world.wod20th.models import Stat
            from django.db.models import Q
            
            # Try to find the gift by name or alias
            gift = Stat.objects.filter(
                Q(name__iexact=stat_name) | Q(gift_alias__icontains=stat_name),
                category='powers',
                stat_type='gift'
            ).first()
            
            if gift and gift.name.lower() != stat_name.lower():
                # We found a gift by alias
                canonical_gift_name = gift.name
                logger.log_info(f"Found gift by alias: {stat_name} -> {canonical_gift_name}")
        
        # Get current rating
        current_rating = get_current_rating(character, category, subcategory, canonical_gift_name or stat_name, temp=False)
        
        # Validate that new rating is higher than current
        if new_rating <= current_rating:
            return False, f"New rating ({new_rating}) must be higher than current rating ({current_rating})", 0
        
        # Calculate cost based on the category
        logger.log_info(f"Calculating cost for {canonical_gift_name or stat_name}, category: {category}, subcategory: {subcategory}")
        
        if category == 'merits':
            # Ensure proper merit cost calculation (5 XP per dot)
            from world.wod20th.utils.xp_costs import calculate_merit_cost
            cost = calculate_merit_cost(current_rating, new_rating)
            logger.log_info(f"Merit cost for {stat_name}: {cost} XP")
        elif category == 'flaws':
            # Flaw costs for buying off
            from world.wod20th.utils.xp_costs import calculate_flaw_cost
            cost = calculate_flaw_cost(current_rating, new_rating)
            logger.log_info(f"Flaw buyoff cost for {stat_name}: {cost} XP")
        else:
            # Regular cost calculation
            cost, requires_approval = calculate_xp_cost(
                character, is_staff_spend, canonical_gift_name or stat_name, category, subcategory, current_rating, new_rating
            )
            
            # Skip approval check for staff spends
            if requires_approval and not is_staff_spend:
                return False, f"Staff approval required for {canonical_gift_name or stat_name} at this level", cost
        
        # Check if character has enough XP
        current_xp = character.db.xp.get('current', 0)
        if current_xp < cost:
            return False, f"Not enough XP. Cost: {cost}, Available: {current_xp}", cost
        
        # Special case for Kinfolk attempting to buy Gnosis directly
        if (category == 'pools' and subcategory == 'dual' and 
            stat_name.lower() == 'gnosis' and 
            splat == 'Mortal+' and char_type == 'Kinfolk'):
            if not is_staff_spend:
                return False, "Kinfolk must purchase the Gnosis merit instead of directly increasing Gnosis pool", cost
        
        # If we get here, all validation passed
        
        # Process the purchase
        if category == 'powers' and subcategory == 'gift' and canonical_gift_name:
            # Use canonical name for the gift in the character's stats
            logger.log_info(f"XP spend: Storing gift with canonical name: {canonical_gift_name} (from alias: {original_stat_name})")
            success = update_stat(character, category, subcategory, canonical_gift_name, new_rating, temp=True, form_modifier=0)
            if not success:
                return False, f"Failed to update gift {canonical_gift_name}", cost
                
            # Store the alias mapping if original_stat_name is different from canonical_gift_name
            if hasattr(character, 'set_gift_alias') and original_stat_name.lower() != canonical_gift_name.lower():
                logger.log_info(f"XP spend: Calling set_gift_alias({canonical_gift_name}, {original_stat_name}, {new_rating})")
                character.set_gift_alias(canonical_gift_name, original_stat_name, new_rating)
            else:
                if not hasattr(character, 'set_gift_alias'):
                    logger.log_err(f"XP spend: Character {character.name} does not have set_gift_alias method")
                else:
                    logger.log_info(f"XP spend: No need to set alias as names match: {original_stat_name} = {canonical_gift_name}")
        else:
            # Regular update
            logger.log_info(f"XP spend: Standard stat update for {stat_name}")
            success = update_stat(character, category, subcategory, stat_name, new_rating, temp=True, form_modifier=0)
            if not success:
                return False, f"Failed to update {stat_name}", cost
        
        # Special case for Kinfolk with Gnosis merit
        if (category == 'merits' and subcategory == 'supernatural' and
            stat_name.lower() == 'gnosis' and 
            splat == 'Mortal+' and char_type == 'Kinfolk'):
            from world.wod20th.utils.mortalplus_utils import handle_kinfolk_gnosis
            gnosis_value = handle_kinfolk_gnosis(character, new_rating)
            logger.log_info(f"Updated Kinfolk Gnosis pool to {gnosis_value} based on merit rating {new_rating}")
        
        # Deduct XP and log the spend
        success, message = deduct_xp_and_log(
            character, cost, stat_name, current_rating, new_rating, reason, is_staff_spend
        )
        if not success:
            return False, message, cost
            
        return True, f"Successfully increased {stat_name} from {current_rating} to {new_rating} (Cost: {cost} XP)", cost
    
    except Exception as e:
        logger.log_err(f"Error in process_xp_spend: {str(e)}")
        return False, f"Error: {str(e)}", 0

def get_canonical_stat_name(self, stat_name: str) -> str:
    """
    Get the canonical name of a stat from the database.
    
    Args:
        stat_name: The name to check
        
    Returns:
        str: The canonical name with proper case
    """
    try:
        from world.wod20th.models import Stat
        from django.db.models import Q
        
        # Handle instance part
        instance = None
        base_name = stat_name
        
        if '(' in stat_name and ')' in stat_name:
            base_name = stat_name.split('(', 1)[0].strip()
            instance = stat_name.split('(', 1)[1].split(')', 1)[0].strip()
        
        # First try direct exact match
        stat = Stat.objects.filter(name__iexact=base_name).first()
        
        # If not found, try partial match
        if not stat:
            stats = Stat.objects.filter(
                Q(name__icontains=base_name) | 
                Q(gift_alias__icontains=base_name)
            ).order_by('name')
            
            if stats.exists():
                # If only one match, use it
                if stats.count() == 1:
                    stat = stats.first()
                else:
                    # Find the closest match by similarity
                    import difflib
                    similarities = [(s, difflib.SequenceMatcher(None, s.name.lower(), base_name.lower()).ratio()) 
                                   for s in stats]
                    # Sort by similarity (highest first)
                    similarities.sort(key=lambda x: x[1], reverse=True)
                    if similarities[0][1] > 0.5:  # Use a threshold to ensure it's reasonably similar
                        stat = similarities[0][0]
        
        if stat:
            # Reconstruct with instance if needed
            if instance:
                return f"{stat.name}({instance})"
            return stat.name
            
        # If we make it here, no match was found in the database
        # Just return the input with proper title case
        proper_name = proper_title_case(base_name)
        if instance:
            return f"{proper_name}({instance})"
        return proper_name
    except Exception as e:
        return stat_name  # Return original on error

def get_proper_stat_name(stat_name, category=None, subcategory=None, character=None):
    """
    Get the proper case-sensitive name for a stat based on category and subcategory.
    This function provides more context-aware naming than get_canonical_stat_name.
    
    Args:
        stat_name: The stat name to normalize
        category: Optional category of the stat (e.g., 'abilities', 'powers')
        subcategory: Optional subcategory (e.g., 'talent', 'discipline')
        character: Optional character object for character-specific context
        
    Returns:
        The proper case-sensitive name for the stat
    """
    # Store the original stat name for reference (especially for gift aliases)
    original_stat_name = stat_name

    # Handle None or empty values
    if not stat_name:
        return ""
        
    # Ensure stat_name is a string
    if isinstance(stat_name, list):
        if stat_name:
            stat_name = stat_name[0] if len(stat_name) == 1 else " ".join(stat_name)
        else:
            stat_name = ""
            
    # Import necessary mappings
    from world.wod20th.utils.stat_mappings import (
        TALENTS, SKILLS, KNOWLEDGES,
        SECONDARY_TALENTS, SECONDARY_SKILLS, SECONDARY_KNOWLEDGES,
        UNIVERSAL_BACKGROUNDS, VAMPIRE_BACKGROUNDS, CHANGELING_BACKGROUNDS,
        MAGE_BACKGROUNDS, TECHNOCRACY_BACKGROUNDS, TRADITIONS_BACKGROUNDS,
        NEPHANDI_BACKGROUNDS, SHIFTER_BACKGROUNDS, SORCERER_BACKGROUNDS,
        KINAIN_BACKGROUNDS, MERIT_VALUES, RITE_VALUES, FLAW_VALUES, ARTS, REALMS
    )
    from world.wod20th.utils.sheet_constants import POWERS
    
    # Check for special handling of gift "Mother's Touch"
    if category == 'powers' and subcategory == 'gift' and stat_name.lower() == "mother's touch":
        return "Mother's Touch"
    
    # Handle stats based on their category
    if category == 'abilities':
        if subcategory == 'talent':
            for talent in TALENTS:
                if talent.lower() == stat_name.lower():
                    return talent
        elif subcategory == 'skill':
            for skill in SKILLS:
                if skill.lower() == stat_name.lower():
                    return skill
        elif subcategory == 'knowledge':
            for knowledge in KNOWLEDGES:
                if knowledge.lower() == stat_name.lower():
                    return knowledge
    elif category == 'secondary_abilities':
        if subcategory == 'secondary_talent':
            for talent in SECONDARY_TALENTS:
                if talent.lower() == stat_name.lower():
                    return talent
        elif subcategory == 'secondary_skill':
            for skill in SECONDARY_SKILLS:
                if skill.lower() == stat_name.lower():
                    return skill
        elif subcategory == 'secondary_knowledge':
            for knowledge in SECONDARY_KNOWLEDGES:
                if knowledge.lower() == stat_name.lower():
                    return knowledge
    elif category == 'backgrounds':
        for background in UNIVERSAL_BACKGROUNDS:
            if background.lower() == stat_name.lower():
                return background
                
        # If not in universal backgrounds, check splat-specific backgrounds
        splat = None
        
        # Try to get splat information from character
        if character:
            try:
                splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            except (KeyError, AttributeError):
                pass
                
        # Check splat-specific backgrounds
        if splat:
            if splat == 'Vampire':
                for background in VAMPIRE_BACKGROUNDS:
                    if background.lower() == stat_name.lower():
                        return background
            elif splat == 'Changeling':
                for background in CHANGELING_BACKGROUNDS:
                    if background.lower() == stat_name.lower():
                        return background
            elif splat == 'Mage':
                # Get tradition or convention
                tradition = None
                try:
                    tradition = character.db.stats.get('identity', {}).get('tradition', {}).get('Tradition', {}).get('perm', '')
                except (KeyError, AttributeError):
                    pass
                    
                if tradition:
                    if tradition in ['Dreamspeaker', 'Verbena', 'Virtual Adept', 'Order of Hermes', 'Celestial Chorus', 'Akashic Brotherhood', 'Cult of Ecstasy', 'Euthanatos', 'Sons of Ether', 'Hollow Ones']:
                        for background in TRADITIONS_BACKGROUNDS:
                            if background.lower() == stat_name.lower():
                                return background
                    elif tradition in ["Nephandi"]:
                        for background in NEPHANDI_BACKGROUNDS:
                            if background.lower() == stat_name.lower():
                                return background
                    elif tradition in ['Iteration X', 'New World Order', 'Progenitors', 'Syndicate', 'Void Engineers']:
                        for background in TECHNOCRACY_BACKGROUNDS:
                            if background.lower() == stat_name.lower():
                                return background
            elif splat == 'Shifter':
                for background in SHIFTER_BACKGROUNDS:
                    if background.lower() == stat_name.lower():
                        return background
            elif splat == 'Mortal+':
                # Get sub-type for Mortal+
                mortalplus_type = None
                try:
                    mortalplus_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
                except (KeyError, AttributeError):
                    pass
                    
                if mortalplus_type:
                    if mortalplus_type in ['Sorcerer', 'Numina', 'Psychic']:
                        for background in SORCERER_BACKGROUNDS:
                            if background.lower() == stat_name.lower():
                                return background
                    elif mortalplus_type in ['Kinain']:
                        for background in KINAIN_BACKGROUNDS:
                            if background.lower() == stat_name.lower():
                                return background
                                
    elif category == 'merits':
        # Check if stat exists in our MERIT_VALUES mapping
        for merit_category, merits in MERIT_VALUES.items():
            if subcategory.lower() == merit_category.lower():
                for merit, values in merits.items():
                    if merit.lower() == stat_name.lower():
                        return merit
                                
    elif category == 'flaws':
        # Check if stat exists in our FLAW_VALUES mapping
        for flaw_category, flaws in FLAW_VALUES.items():
            if subcategory.lower() == flaw_category.lower():
                for flaw, values in flaws.items():
                    if flaw.lower() == stat_name.lower():
                        return flaw
                                
    elif category == 'powers':
        if subcategory == 'gift':
            # For gifts, we need to check the database
            # Convert stat_name to string if it's a list
            if isinstance(stat_name, list):
                if stat_name:
                    stat_name = stat_name[0] if len(stat_name) == 1 else " ".join(stat_name)
                else:
                    stat_name = ""
            
            # Use the database to validate and get the proper case
            from world.wod20th.models import Stat
            from django.db.models import Q
            
            # Check for an exact match first
            exact_match = Stat.objects.filter(
                name__iexact=stat_name,
                category='powers',
                stat_type='gift'
            ).first()
            
            if exact_match:
                return exact_match.name
                
            # If no exact match, try alias matching
            alias_match = Stat.objects.filter(
                gift_alias__icontains=stat_name,
                category='powers',
                stat_type='gift'
            ).first()
            
            if alias_match:
                return alias_match.name
                
            # If still no match, continue to general handling
            
        # Check if it's an Art
        if subcategory == 'art':
            # Try to find the proper case in ARTS
            for art in ARTS:
                if art.lower() == stat_name.lower():
                    return art
        elif subcategory == 'realm':
            # Check if the realm exists in our REALMS mapping
            for realm in REALMS:
                if realm.lower() == stat_name.lower():
                    return realm

        # Define power type mappings
        power_mappings = {
            'sphere': [
                'Correspondence', 'Entropy', 'Forces', 'Life', 'Matter',
                'Mind', 'Prime', 'Spirit', 'Time', 'Dimensional Science',
                'Primal Utility', 'Data'
            ],
            'art': ARTS,
            'realm': REALMS,
            'discipline': POWERS.get('discipline', []),
            'numina': POWERS.get('numina', []),
            'charm': POWERS.get('charm', []),
            'blessing': POWERS.get('blessing', [])
        }
        
        # Check other power types
        if subcategory in power_mappings:
            # Find the proper case-sensitive name from the list
            for proper_name in power_mappings[subcategory]:
                if proper_name.lower() == stat_name.lower():
                    return proper_name

    # Add pool stats to proper name lookup
    pool_stats = {
        'willpower': 'Willpower',
        'gnosis': 'Gnosis',
        'glamour': 'Glamour',
        'arete': 'Arete',
        'enlightenment': 'Enlightenment',
        'rage': 'Rage'
    }

    # Check pools
    if category == 'pools':
        stat_name_lower = stat_name.lower()
        if stat_name_lower in pool_stats:
            return pool_stats[stat_name_lower]
        # Check if it matches any pool stat case-insensitively
        for proper_name in pool_stats.values():
            if proper_name.lower() == stat_name_lower:
                return proper_name
    elif category == 'secondary_abilities':
        # Add special handling for common hyphenated secondary abilities
        special_secondary = {
            'power-brokering': 'Power-Brokering',
            'power brokering': 'Power-Brokering',
            'area knowledge': 'Area Knowledge',
            'area-knowledge': 'Area Knowledge',
            'cultural savvy': 'Cultural Savvy',
            'cultural-savvy': 'Cultural Savvy',
            'privacy obsession': 'Privacy Obsession',
            'privacy-obsession': 'Privacy Obsession',
        }
        
        # Check for these special cases first
        stat_lower = stat_name.lower()
        if stat_lower in special_secondary:
            return special_secondary[stat_lower]
        
        # Check with hyphen/space variations
        stat_with_hyphen = stat_lower.replace(' ', '-')
        stat_with_spaces = stat_lower.replace('-', ' ')
        
        if stat_with_hyphen in special_secondary:
            return special_secondary[stat_with_hyphen]
        if stat_with_spaces in special_secondary:
            return special_secondary[stat_with_spaces]
        
        # Standard checks with more flexible matching for subcategories
        if subcategory == 'secondary_talent':
            for talent in SECONDARY_TALENTS:
                if talent.lower() == stat_lower or talent.lower().replace('-', ' ') == stat_lower or talent.lower().replace(' ', '-') == stat_lower:
                    return talent
        elif subcategory == 'secondary_skill':
            for skill in SECONDARY_SKILLS:
                if skill.lower() == stat_lower or skill.lower().replace('-', ' ') == stat_lower or skill.lower().replace(' ', '-') == stat_lower:
                    return skill
        elif subcategory == 'secondary_knowledge':
            for knowledge in SECONDARY_KNOWLEDGES:
                if knowledge.lower() == stat_lower or knowledge.lower().replace('-', ' ') == stat_lower or knowledge.lower().replace(' ', '-') == stat_lower:
                    return knowledge

    # If no match found in category-specific logic, use the canonical name function
    return get_canonical_stat_name(None, stat_name)

def get_current_rating(character, category, subcategory, stat_name, temp=False):
    """
    Get the current rating of a stat, handling special cases and case-insensitivity.
    
    Args:
        character: The character object
        category: The stat category (e.g., 'attributes', 'abilities')
        subcategory: The stat subcategory (e.g., 'physical', 'talent')
        stat_name: The name of the stat to check
        temp: Whether to get temporary (True) or permanent (False) value
        
    Returns:
        int: The current rating, or 0 if not found
    """
    # Handle None values
    if not category or not subcategory or not stat_name:
        return 0
        
    stat_name_lower = stat_name.lower()
    
    # Special handling for case-insensitivity, especially for abilities
    if category in ['abilities', 'secondary_abilities']:
        if subcategory in character.db.stats.get(category, {}):
            for existing_name, values in character.db.stats[category][subcategory].items():
                if existing_name.lower() == stat_name_lower:
                    return values.get('temp' if temp else 'perm', 0)
        return 0
        
    # Handle instanced backgrounds - e.g. "Allies(Police)"
    elif category == "backgrounds" and "(" in stat_name and ")" in stat_name:
        # Extract the base name and instance
        base_name = stat_name[:stat_name.find('(')].strip()
        instance = stat_name[stat_name.find('(')+1:stat_name.find(')')].strip()
        
        # Look for direct match first
        if stat_name in character.db.stats.get('backgrounds', {}).get('background', {}):
            return character.db.stats['backgrounds']['background'][stat_name].get('temp' if temp else 'perm', 0)
        
        # Get the current rating for instanced backgrounds
        backgrounds = character.db.stats.get("backgrounds", {}).get("background", {})
        background_data = backgrounds.get(base_name.lower(), {})
        instances = background_data.get("instances", {})
        return instances.get(instance, {}).get('temp' if temp else 'perm', 0)
        
    # Special handling for powers with case sensitivity issues
    elif category == 'powers':
        if subcategory in character.db.stats.get('powers', {}):
            for existing_name, values in character.db.stats['powers'][subcategory].items():
                if existing_name.lower() == stat_name_lower:
                    return values.get('temp' if temp else 'perm', 0)
        return 0
        
    # Standard path lookup
    try:
        value = character.db.stats.get(category, {}).get(subcategory, {}).get(stat_name, {}).get('temp' if temp else 'perm', 0)
        return value or 0
    except (AttributeError, KeyError, TypeError):
        return 0

def update_stat(character, category, subcategory, stat_name, new_rating, temp=True, form_modifier=0):
    """
    Update a stat with proper structure handling and special case management.
    
    Args:
        character: The character object
        category: The stat category
        subcategory: The stat subcategory
        stat_name: The name of the stat to update
        new_rating: The new rating to set
        temp: Whether to update the temporary value too (default: True)
        form_modifier: Modifier to apply to temporary value (for shifters in different forms)
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        # Ensure proper structure exists
        if not hasattr(character.db, 'stats'):
            character.db.stats = {}
            
        if category not in character.db.stats:
            character.db.stats[category] = {}
            
        if subcategory and subcategory not in character.db.stats[category]:
            character.db.stats[category][subcategory] = {}
        
        # Handle different categories
        if category == 'powers':
            # Make sure powers subcategory exists
            if subcategory not in character.db.stats['powers']:
                character.db.stats['powers'][subcategory] = {}
                
            # Store the stat with proper structure
            character.db.stats['powers'][subcategory][stat_name] = {
                'perm': new_rating
            }
            
            # Calculate temporary value with form modifier
            if form_modifier == -999:  # Special case for forced 0
                temp_value = 0
            else:
                temp_value = max(0, new_rating + form_modifier)  # Ensure non-negative
                
            character.db.stats['powers'][subcategory][stat_name]['temp'] = temp_value
            
        # Special handling for backgrounds with instances
        elif category == 'backgrounds' and '(' in stat_name and ')' in stat_name:
            if 'background' not in character.db.stats['backgrounds']:
                character.db.stats['backgrounds']['background'] = {}
                
            # Store directly with the full name
            character.db.stats['backgrounds']['background'][stat_name] = {
                'perm': new_rating,
                'temp': new_rating
            }
            
        # Default handling for other stats
        else:
            # For nested dict structure
            if subcategory:
                if stat_name not in character.db.stats[category][subcategory]:
                    character.db.stats[category][subcategory][stat_name] = {}
                
                character.db.stats[category][subcategory][stat_name]['perm'] = new_rating
                
                if temp:
                    # Calculate temporary value with form modifier
                    if form_modifier == -999:  # Special case for forced 0
                        temp_value = 0
                    else:
                        temp_value = max(0, new_rating + form_modifier)  # Ensure non-negative
                        
                    character.db.stats[category][subcategory][stat_name]['temp'] = temp_value
            # For non-nested structure (rare)
            else:
                character.db.stats[category][stat_name] = new_rating
        
        return True
    except Exception as e:
        logger.log_err(f"Error updating stat {stat_name}: {str(e)}")
        return False

def deduct_xp_and_log(character, cost, stat_name, current_rating, new_rating, reason="", staff_spend=False):
    """
    Deduct XP from a character and log the spend.
    
    Args:
        character: The character object
        cost: The cost to deduct
        stat_name: The name of the stat being purchased
        current_rating: The previous rating
        new_rating: The new rating
        reason: The reason for the spend
        staff_spend: Whether this is a staff-approved spend
        
    Returns:
        tuple: (success, message)
    """
    try:
        # Convert to Decimal for precise calculation
        cost_decimal = Decimal(str(cost)).quantize(Decimal('0.01'))
        current_xp = Decimal(str(character.db.xp.get('current', 0)))
        spent_xp = Decimal(str(character.db.xp.get('spent', 0)))
        
        # Check if character has enough XP
        if current_xp < cost_decimal:
            return False, f"Not enough XP. Cost: {cost_decimal}, Available: {current_xp}"
            
        logger.log_info(f"XP Deduction - Current XP (before): {current_xp}")
        logger.log_info(f"XP Deduction - Cost to deduct: {cost_decimal}")
        
        # Perform the deduction
        new_current = current_xp - cost_decimal
        new_spent = spent_xp + cost_decimal
        
        # Update the character's XP values
        character.db.xp['current'] = new_current
        character.db.xp['spent'] = new_spent
        
        logger.log_info(f"XP Deduction - New current XP (after): {new_current}")
        logger.log_info(f"XP Deduction - New spent XP (after): {new_spent}")
        
        # Create the spend entry
        spend_entry = {
            'type': 'spend',
            'amount': float(cost_decimal),
            'stat_name': stat_name,
            'previous_rating': current_rating,
            'new_rating': new_rating,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add staff name if this is a staff spend
        if staff_spend or 'Staff Spend: ' in reason:
            spend_entry['staff_name'] = reason.replace('Staff Spend: ', '') if 'Staff Spend: ' in reason else "Staff"
            
        # Initialize spends list if it doesn't exist
        if 'spends' not in character.db.xp:
            character.db.xp['spends'] = []
            
        # Add the spend to the log
        character.db.xp['spends'].insert(0, spend_entry)
        
        return True, f"Successfully deducted {cost_decimal} XP for {stat_name}"
        
    except Exception as e:
        logger.log_err(f"Error during XP deduction: {str(e)}")
        return False, f"Error processing XP deduction: {str(e)}"

def validate_stat_requirements(character, stat_name, category, subcategory, new_rating, is_staff_spend=False):
    """
    Validate that a character meets requirements to purchase or increase a stat.
    
    Args:
        character: The character object
        stat_name: The name of the stat to validate
        category: The category of the stat
        subcategory: The subcategory of the stat
        new_rating: The new rating to validate
        is_staff_spend: Whether this is a staff-approved spend
        
    Returns:
        tuple: (is_valid, message, current_rating)
    """
    splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
    char_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
    
    if not splat:
        return False, "Character splat not set", 0
    
    # Get current rating
    current_rating = get_current_rating(character, category, subcategory, stat_name, temp=False)
    
    # Check if new rating is higher than current
    if new_rating <= current_rating:
        return False, f"New rating ({new_rating}) must be higher than current rating ({current_rating})", current_rating
    
    # Early validation for merits and flaws
    if category in ['merits', 'flaws'] and not is_staff_spend:
        return False, f"{category.title()} require staff approval", current_rating
    
    # Special validation for specific categories
    if category == 'powers':
        # Validate disciplines
        if subcategory == 'discipline':
            if stat_name in ['Thaumaturgy', 'Necromancy'] and not is_staff_spend:
                return False, f"{stat_name} requires staff approval to purchase", current_rating
            
            if not is_staff_spend and stat_name not in PURCHASABLE_DISCIPLINES:
                return False, f"Discipline {stat_name} requires staff approval to purchase", current_rating
                
        # Validate thaumaturgy/necromancy paths
        elif subcategory in ['thaumaturgy', 'necromancy']:
            # Check if character has the required discipline
            discipline_name = 'Thaumaturgy' if subcategory == 'thaumaturgy' else 'Necromancy'
            discipline_rating = character.db.stats.get('powers', {}).get('discipline', {}).get(discipline_name, {}).get('perm', 0)
            
            if discipline_rating == 0:
                return False, f"Must have {discipline_name} discipline to purchase {subcategory.title()} paths", current_rating
                
            # Get primary path
            if subcategory == 'thaumaturgy':
                primary_path = _get_primary_thaumaturgy_path(character)
            else:  # necromancy
                primary_path = _get_primary_necromancy_path(character)
                
            # If this is not the primary path, check level restriction
            if stat_name != primary_path:
                primary_path_rating = character.db.stats.get('powers', {}).get(subcategory, {}).get(primary_path, {}).get('perm', 0)
                if new_rating > primary_path_rating:
                    return False, f"Secondary {subcategory.title()} paths cannot exceed primary path rating ({primary_path_rating})", current_rating
                    
        # Validate rituals
        elif subcategory in ['thaum_ritual', 'necromancy_ritual']:
            # Check if character has the required discipline
            discipline_name = 'Thaumaturgy' if subcategory == 'thaum_ritual' else 'Necromancy'
            discipline_rating = character.db.stats.get('powers', {}).get('discipline', {}).get(discipline_name, {}).get('perm', 0)
            
            if discipline_rating == 0:
                return False, f"Must have {discipline_name} discipline to purchase rituals", current_rating
                
            # Cannot learn rituals higher than discipline rating
            if new_rating > discipline_rating:
                return False, f"Cannot learn level {new_rating} rituals without {discipline_name} {new_rating}", current_rating
    
    # Validate pools
    elif category == 'pools' and subcategory == 'dual':
        if not is_staff_spend:  # Only apply these restrictions for non-staff spends
            if stat_name == 'Rage' and new_rating > 5:
                return False, "Rage above 5 requires staff approval", current_rating
            elif stat_name == 'Glamour' and new_rating > 5:
                return False, "Glamour above 5 requires staff approval", current_rating
            elif stat_name == 'Gnosis':
                if splat == 'Mortal+' and char_type == 'Kinfolk':
                    return False, "Kinfolk must purchase or increase the Gnosis merit instead of directly increasing Gnosis pool", current_rating
                if new_rating > 5:
                    return False, "Gnosis above 5 requires staff approval", current_rating
    
    # Validate Kinfolk attempting to buy Gnosis directly
    if (category == 'pools' and subcategory == 'dual' and 
        stat_name.lower() == 'gnosis' and 
        splat == 'Mortal+' and char_type == 'Kinfolk'):
        return False, "Kinfolk must purchase or increase the Gnosis merit instead of directly increasing Gnosis pool", current_rating
    
    return True, "Validation passed", current_rating
