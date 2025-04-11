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
    SORCERER_BACKGROUNDS, KINAIN_BACKGROUNDS
)

from world.wod20th.utils.xp_costs import (
    calculate_attribute_cost, calculate_ability_cost, calculate_discipline_cost,
    calculate_background_cost, calculate_willpower_cost, calculate_virtue_cost,
    calculate_thaumaturgy_path_cost, calculate_ritual_cost, calculate_path_cost,
    calculate_rage_cost, calculate_gnosis_cost, calculate_rite_cost,
    calculate_sphere_cost as base_sphere_cost, calculate_arete_cost, calculate_avatar_cost,
    calculate_art_cost, calculate_realm_cost, calculate_glamour_cost,
    calculate_special_advantage_cost, calculate_charm_cost, calculate_sorcerous_path_cost,
    calculate_numina_cost, calculate_blessing_cost, calculate_arcanos_cost, 
    calculate_faith_cost, calculate_sorcerous_ritual_cost
)

# Do not import shifter_utils functions here to avoid circular imports
# They will be imported within the functions that need them

from decimal import Decimal
from django.db.models import Q
from evennia.utils import logger

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


# Constants
# Removed duplicate PURCHASABLE_DISCIPLINES list since we're using the one from vampire_utils.py

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
            'Rising Sun Striking': True,
            'Noonday Sun Unshading': True,
            'Setting Sun Warding': True,
            'Shrouded Sun Concealing': True,
            'Midnight Sun Shining': True,
            'Decorated Suns Gathering': True,
            'Solar Eclipse Crowning': True
        },
        'auspice_mappings': {
            'Tung Chun': 'Setting Sun Warding',
            'Nam Nsai': 'Noonday Sun Unshading',
            'Sai Chau': 'Solar Eclipse Crowning',
            'Pei Tung': 'Midnight Sun Shining'
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


# Clan-specific disciplines mapping
def _is_discipline_in_clan(discipline, clan):
    """Helper method to check if a discipline is in-clan."""
    # clan-specific disciplines
    clan_disciplines = {
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
    
    # Check if discipline is in clan's discipline list
    return clan in clan_disciplines and discipline in clan_disciplines[clan]

def get_stat_model():
    """Get the Stat model lazily to avoid circular imports."""
    from world.wod20th.models import Stat
    return Stat

def calculate_xp_cost(character, stat_name, new_rating, category=None, subcategory=None, current_rating=None, is_staff_spend=False):
    """
    Calculate XP cost for increasing a stat.
    
    Args:
        character: The character object
        stat_name: The name of the stat to increase
        new_rating: The desired new rating
        category: The stat category
        subcategory: The stat subcategory
        current_rating: The current rating of the stat
        is_staff_spend: Whether this is a staff-approved purchase
        
    Returns:
        tuple: (cost, requires_approval)
    """
    try:
        # Convert new_rating to integer
        try:
            new_rating = int(new_rating)
        except (ValueError, TypeError):
            return (0, False)
        
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

        # Get current rating if not provided
        if current_rating is None:
            current_rating = character.get_stat(category, subcategory, stat_name) or 0

        # Initialize cost and requires_approval
        total_cost = 0
        requires_approval = False

        # Handle attributes
        if category == 'attributes':
            total_cost = 0
            for rating in range(current_rating + 1, new_rating + 1):
                if rating == 2:
                    total_cost += 8  # Going from 1 to 2 specifically costs 8
                else:
                    total_cost += rating * 4  # Current rating × 4
            requires_approval = new_rating > 3
            return total_cost, requires_approval

        # Handle abilities
        elif category in ['abilities', 'secondary_abilities']:
            if subcategory in ['talent', 'skill', 'knowledge', 'secondary_talent', 'secondary_skill', 'secondary_knowledge']:
                total_cost = 0
                for rating in range(current_rating + 1, new_rating + 1):
                    if rating == 1:
                        total_cost += 3  # First dot costs 3
                    else:
                        total_cost += rating * 2  # Current rating × 2
                requires_approval = new_rating > 3
                return total_cost, requires_approval

        # Handle backgrounds
        elif category == 'backgrounds':
            total_cost = (new_rating - current_rating) * 5  # Each dot costs 5 XP
            requires_approval = new_rating > 3
            return total_cost, requires_approval

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
            return total_cost, requires_approval

        # Handle disciplines
        elif category == 'powers' and subcategory == 'discipline':
            if splat == 'Vampire':
                clan = character.db.stats.get('identity', {}).get('lineage', {}).get('Clan', {}).get('perm', '')
                from world.wod20th.utils.vampire_utils import _is_discipline_in_clan
                is_in_clan = _is_discipline_in_clan(stat_name, clan)
                total_cost = 0
                for rating in range(current_rating + 1, new_rating + 1):
                    if rating == 1:
                        total_cost += 10  # First dot always costs 10
                    else:
                        if is_in_clan:
                            total_cost += rating * 5  # Current rating × 5
                        else:
                            total_cost += rating * 7  # Current rating × 7
                requires_approval = new_rating > 2
            elif splat == 'Mortal+' and mortal_type == 'Ghoul':
                from world.wod20th.utils.mortalplus_utils import calculate_ghoul_discipline_cost
                clan = character.db.stats.get('identity', {}).get('lineage', {}).get('Family', {}).get('perm', '')
                from world.wod20th.utils.vampire_utils import _is_discipline_in_clan
                is_in_clan = _is_discipline_in_clan(stat_name, clan)
                total_cost = calculate_ghoul_discipline_cost(current_rating, new_rating, is_in_clan)
                requires_approval = new_rating > 1
            return total_cost, requires_approval

        # Handle spheres
        elif category == 'powers' and subcategory == 'sphere':
            from world.wod20th.utils.mage_utils import calculate_sphere_cost
            total_cost, requires_approval, _ = calculate_sphere_cost(character, stat_name, new_rating, current_rating, is_staff_spend)
            return total_cost, requires_approval

        # Handle arts and realms
        elif category == 'powers' and subcategory in ['art', 'realm']:
            if splat == 'Changeling':
                from world.wod20th.utils.changeling_utils import calculate_art_cost, calculate_realm_cost
                if subcategory == 'art':
                    total_cost = calculate_art_cost(current_rating, new_rating)
                else:  # realm
                    total_cost = calculate_realm_cost(current_rating, new_rating)
                requires_approval = new_rating > 2
            elif splat == 'Mortal+' and mortal_type == 'Kinain':
                from world.wod20th.utils.mortalplus_utils import calculate_kinain_art_cost, calculate_kinain_realm_cost
                if subcategory == 'art':
                    total_cost = calculate_kinain_art_cost(current_rating, new_rating)
                else:  # realm
                    total_cost = calculate_kinain_realm_cost(current_rating, new_rating)
                requires_approval = new_rating > 2
            return total_cost, requires_approval

        # Handle pools
        elif category == 'pools' and subcategory == 'dual':
            if stat_name == 'Willpower':
                total_cost = sum(i * 2 for i in range(current_rating + 1, new_rating + 1))  # Current rating × 2
                requires_approval = new_rating > 5
            elif stat_name == 'Rage':
                total_cost = sum(i for i in range(current_rating + 1, new_rating + 1))  # Current rating
                requires_approval = new_rating > 5
            elif stat_name == 'Gnosis':
                total_cost = sum(i * 2 for i in range(current_rating + 1, new_rating + 1))  # Current rating × 2
                requires_approval = new_rating > 5
            elif stat_name == 'Glamour':
                total_cost = sum(i * 3 for i in range(current_rating + 1, new_rating + 1))  # Current rating × 3
                requires_approval = new_rating > 5
            elif stat_name in ['Arete', 'Enlightenment']:
                total_cost = sum(i * 8 for i in range(current_rating + 1, new_rating + 1))  # Current rating × 8
                requires_approval = new_rating > 1
            return total_cost, requires_approval

        # Handle special advantages for companions
        elif category == 'powers' and subcategory == 'special_advantage':
            from world.wod20th.utils.companion_utils import calculate_special_advantage_cost
            total_cost = calculate_special_advantage_cost(current_rating, new_rating)
            requires_approval = True  # Special advantages always require approval
            return total_cost, requires_approval

        # Handle charms
        elif category == 'powers' and subcategory == 'charm':
            if splat in ['Companion', 'Possessed']:
                from world.wod20th.utils.companion_utils import calculate_charm_cost
                total_cost = calculate_charm_cost(current_rating, new_rating)
                requires_approval = new_rating > 2
                return total_cost, requires_approval

        # Handle blessings
        elif category == 'powers' and subcategory == 'blessing':
            from world.wod20th.utils.possessed_utils import calculate_blessing_cost
            total_cost = calculate_blessing_cost(current_rating, new_rating)
            requires_approval = True  # Blessings always require approval
            return total_cost, requires_approval

        # Handle Mortal+ specific powers
        elif splat == 'Mortal+':
            if subcategory == 'sorcery':
                from world.wod20th.utils.mortalplus_utils import calculate_sorcery_path_cost
                total_cost = calculate_sorcery_path_cost(current_rating, new_rating)
                requires_approval = new_rating > 2
            elif subcategory == 'hedge_ritual':
                from world.wod20th.utils.mortalplus_utils import calculate_hedge_ritual_cost
                total_cost = calculate_hedge_ritual_cost(current_rating, new_rating)
                requires_approval = new_rating > 1
            elif subcategory == 'numina':
                from world.wod20th.utils.mortalplus_utils import calculate_numina_cost
                total_cost = calculate_numina_cost(current_rating, new_rating)
                requires_approval = new_rating > 2
            return total_cost, requires_approval

        return total_cost, requires_approval

    except Exception as e:
        return 0, False

def validate_xp_purchase(character, stat_name, new_rating, category=None, subcategory=None, is_staff_spend=False):
    """
    Validate if a character can purchase a stat increase.
    Returns (can_purchase, error_message)
    """
    # Get character's splat
    splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
    if not splat:
        return False, "Character splat not set"

    # If category and subcategory aren't provided, try to determine them
    if not category or not subcategory:
        from world.wod20th.utils.xp_utils import _determine_stat_category
        category, subcategory = _determine_stat_category(stat_name)
        if not category or not subcategory:
            return False, f"Could not determine category for {stat_name}"

    # Early check for merits and flaws - these always require staff approval
    if category in ['merits', 'flaws'] and not is_staff_spend:
        return False, f"{category.title()} require staff approval"

    # If not a staff spend, check auto-spend limits first
    if not is_staff_spend:
        # Define auto-spend limits
        AUTO_SPEND_LIMITS = {
            'attributes': 3,  # All attributes up to 3
            'abilities': 3,   # All abilities up to 3
            'backgrounds': {
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
                'Dreamers': 2
            },
            'pools': {
                'Willpower': 5
            },
            'powers': {
                'discipline': {
                    'max_level': 2,
                    'allowed': ['Potence', 'Fortitude', 'Celerity', 'Auspex', 'Obfuscate']
                },
                'sphere': 2,  # All spheres up to 2
                'art': 2,     # All arts up to 2
                'realm': 2,   # All realms up to 2
                'gift': 1     # All non-special gifts up to 1
            }
        }

        # Check if the purchase is within auto-spend limits
        if category == 'attributes' and new_rating > AUTO_SPEND_LIMITS['attributes']:
            return False, f"Staff approval required for {stat_name} above {AUTO_SPEND_LIMITS['attributes']}"

        elif category == 'abilities' and new_rating > AUTO_SPEND_LIMITS['abilities']:
            return False, f"Staff approval required for {stat_name} above {AUTO_SPEND_LIMITS['abilities']}"

        elif category == 'backgrounds':
            max_level = AUTO_SPEND_LIMITS['backgrounds'].get(stat_name)
            if max_level is None:
                return False, f"Staff approval required for {stat_name} background"
            if new_rating > max_level:
                return False, f"Staff approval required for {stat_name} above {max_level}"

        elif category == 'pools':
            if stat_name == 'Willpower':
                if new_rating > AUTO_SPEND_LIMITS['pools']['Willpower']:
                    return False, f"Staff approval required for Willpower above {AUTO_SPEND_LIMITS['pools']['Willpower']}"

        elif category == 'powers':
            if subcategory == 'discipline':
                power_limits = AUTO_SPEND_LIMITS['powers']['discipline']
                if stat_name not in power_limits['allowed']:
                    return False, f"Staff approval required for {stat_name}"
                if new_rating > power_limits['max_level']:
                    return False, f"Staff approval required for {stat_name} above {power_limits['max_level']}"

            elif subcategory in ['sphere', 'art', 'realm']:
                max_level = AUTO_SPEND_LIMITS['powers'].get(subcategory)
                if new_rating > max_level:
                    return False, f"Staff approval required for {stat_name} above {max_level}"

            elif subcategory == 'gift':
                # Check if it's a special gift (Planetary, Ju-Fu, or Camp gift)
                from world.wod20th.models import Stat
                gift = Stat.objects.filter(
                    name__iexact=stat_name,
                    category='powers',
                    stat_type='gift'
                ).first()

                if gift:
                    # Check for special gifts that always require approval
                    if gift.tribe:
                        tribes = gift.tribe if isinstance(gift.tribe, list) else [gift.tribe]
                        if any(t.lower() in ['croatan', 'planetary', 'ju-fu'] for t in tribes):
                            return False, "Staff approval required for Planetary gifts"

                    if gift.camp:
                        return False, "Staff approval required for Camp gifts"

                if new_rating > AUTO_SPEND_LIMITS['powers']['gift']:
                    return False, f"Staff approval required for gifts above level {AUTO_SPEND_LIMITS['powers']['gift']}"

            # These subcategories always require staff approval for players
            elif subcategory in ['thaumaturgy', 'necromancy', 'thaum_ritual', 'necromancy_ritual']:
                return False, f"Staff approval required for {subcategory}"

    # If it's a discipline, check if it's in the allowed list for player purchases
    if category == 'powers' and subcategory == 'discipline':
        if stat_name in ['Thaumaturgy', 'Necromancy']:
            return False, f"{stat_name} requires staff approval to purchase"
        elif stat_name not in PURCHASABLE_DISCIPLINES:
            return False, f"Discipline {stat_name} requires staff approval to purchase"
        
    # Special handling for Thaumaturgy and Necromancy paths
    if category == 'powers' and subcategory in ['thaumaturgy', 'necromancy']:
        # Check if character has the required discipline
        discipline_name = 'Thaumaturgy' if subcategory == 'thaumaturgy' else 'Necromancy'
        discipline_rating = character.db.stats.get('powers', {}).get('discipline', {}).get(discipline_name, {}).get('perm', 0)
        
        if discipline_rating == 0:
            return False, f"Must have {discipline_name} discipline to purchase {subcategory.title()} paths"

        # Get primary path
        if subcategory == 'thaumaturgy':
            primary_path = _get_primary_thaumaturgy_path(character)
        else:  # necromancy
            primary_path = _get_primary_necromancy_path(character)

        # If this is not the primary path, check level restriction
        if stat_name != primary_path:
            primary_path_rating = character.db.stats.get('powers', {}).get(subcategory, {}).get(primary_path, {}).get('perm', 0)
            if new_rating > primary_path_rating:
                return False, f"Secondary {subcategory.title()} paths cannot exceed primary path rating ({primary_path_rating})"

    # Special handling for Thaumaturgy and Necromancy rituals
    if category == 'powers' and subcategory in ['thaum_ritual', 'necromancy_ritual']:
        # Check if character has the required discipline
        discipline_name = 'Thaumaturgy' if subcategory == 'thaum_ritual' else 'Necromancy'
        discipline_rating = character.db.stats.get('powers', {}).get('discipline', {}).get(discipline_name, {}).get('perm', 0)
        
        if discipline_rating == 0:
            return False, f"Must have {discipline_name} discipline to purchase rituals"
            
        # Cannot learn rituals higher than discipline rating
        if new_rating > discipline_rating:
            return False, f"Cannot learn level {new_rating} rituals without {discipline_name} {new_rating}"

    # Handle pools (Willpower, Rage, Gnosis, Glamour)
    if category == 'pools' and subcategory == 'dual':
        # Get current rating
        current_rating = character.db.stats.get('pools', {}).get('dual', {}).get(stat_name, {}).get('perm', 0)
        
        # Check if new rating is actually an increase
        if new_rating <= current_rating:
            return False, "New rating must be higher than current rating"

        if not is_staff_spend:  # Only apply these restrictions for non-staff spends
            if stat_name == 'Rage' and new_rating > 5:
                return False, "Rage above 5 requires staff approval"
            elif stat_name == 'Glamour' and new_rating > 5:
                return False, "Glamour above 5 requires staff approval"
            elif stat_name == 'Gnosis':
                char_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
                if splat == 'Mortal+' and char_type == 'Kinfolk':
                    return False, "Kinfolk must purchase the Gnosis merit instead of directly increasing Gnosis pool"
                if new_rating > 5:
                    return False, "Gnosis above 5 requires staff approval"
            elif stat_name in ['Arete', 'Enlightenment'] and new_rating > 1:
                return False, f"{stat_name} above 1 requires staff approval"

    # Handle merits and flaws
    if category == 'merits':
        # Check if it's a valid merit
        merit_found = False
        for merit_type, merits in MERIT_CATEGORIES.items():
            if stat_name in merits:
                merit_found = True
                subcategory = merit_type
                break
            # Try case-insensitive match
            stat_lower = stat_name.lower()
            for merit in merits:
                if merit.lower() == stat_lower:
                    merit_found = True
                    subcategory = merit_type
                    break
            if merit_found:
                break
                
        if not merit_found:
            return False, f"{stat_name} is not a valid merit"
            
        # Check if the merit value is valid
        if stat_name in MERIT_VALUES:
            valid_values = MERIT_VALUES[stat_name]
            if new_rating not in valid_values:
                return False, f"Invalid rating for {stat_name}. Valid values are: {valid_values}"

        # Check if the character already has this merit
        current_rating = character.db.stats.get('merits', {}).get(subcategory, {}).get(stat_name, {}).get('perm', 0)
        if current_rating > 0:
            return False, f"Character already has the merit {stat_name}"

        if not is_staff_spend:
            return False, "Merits require staff approval"

    elif category == 'flaws':
        # Check if it's a valid flaw
        flaw_found = False
        for flaw_type, flaws in FLAW_CATEGORIES.items():
            stat_title_words = ' '.join(word.title() for word in stat_name.split())
            if stat_title_words in flaws or stat_name in flaws:
                flaw_found = True
                break
            # Try case-insensitive match
            stat_lower = stat_name.lower()
            for flaw in flaws:
                if flaw.lower() == stat_lower:
                    flaw_found = True
                    break
            if flaw_found:
                break
                
        if not flaw_found:
            return False, f"{stat_name} is not a valid flaw"
            
        # Flaws can only be bought off through staffspend
        if not is_staff_spend:
            return False, "Flaws can only be bought off through staffspend"

    # Validate blessings and charms
    if category == 'powers':
        if subcategory == 'blessing':
            if stat_name not in BLESSINGS:
                return False, f"{stat_name} is not a valid blessing"
            if not is_staff_spend and new_rating > 2:
                return False, "Blessings above rating 2 require staff approval"
        elif subcategory == 'charm':
            if stat_name not in CHARMS:
                return False, f"{stat_name} is not a valid charm"
            if not is_staff_spend and new_rating > 0:
                return False, "Charms require staff approval"

    return True, ""

def process_xp_purchase(character, stat_name, new_rating, category, subcategory, reason="", current_rating=None, pre_calculated_cost=None):
    """
    Process an XP purchase.
    
    Args:
        character: The character object
        stat_name: The name of the stat to increase
        new_rating: The desired new rating
        category: The stat category
        subcategory: The stat subcategory
        reason: The reason for the spend
        current_rating: The current rating (if pre-determined)
        pre_calculated_cost: The pre-calculated cost (if provided)
        
    Returns:
        tuple: (success, message)
    """
    try:
        # If current_rating not provided, get it from the character
        if current_rating is None:
            current_rating = character.get_stat(category, subcategory, stat_name, temp=False) or 0
        
        # Calculate cost if not provided
        if pre_calculated_cost is None:
            from world.wod20th.utils.xp_costs import (
                calculate_attribute_cost, calculate_ability_cost, 
                calculate_background_cost, calculate_merit_cost,
                calculate_flaw_cost, calculate_willpower_cost
            )
            
            if category == 'attributes':
                cost = calculate_attribute_cost(current_rating, new_rating)
            elif category == 'abilities' or category == 'secondary_abilities':
                cost = calculate_ability_cost(current_rating, new_rating)
            elif category == 'backgrounds':
                cost = calculate_background_cost(current_rating, new_rating)
            elif category == 'merits':
                cost = calculate_merit_cost(current_rating, new_rating)
            elif category == 'flaws':
                cost = calculate_flaw_cost(current_rating, new_rating)
            elif category == 'pools' and subcategory == 'dual' and stat_name.lower() == 'willpower':
                cost = calculate_willpower_cost(current_rating, new_rating)
            else:
                # Default to standard ability cost if no specific handler
                cost = calculate_ability_cost(current_rating, new_rating)
        else:
            cost = pre_calculated_cost
            
        # Ensure cost is not 0 (except for flaws, which can be 0 when removed)
        if cost == 0 and category != 'flaws':
            return False, "Cost calculation returned zero. This may indicate a stat category error."
            
        # Convert cost to Decimal for precise calculations
        cost_decimal = Decimal(str(cost)).quantize(Decimal('0.01'))
        
        # Check if character has enough XP
        if character.db.xp['current'] < cost_decimal:
            return False, f"Not enough XP. Cost: {cost_decimal}, Available: {character.db.xp['current']}"

        # Update the stat based on category
        if category == 'powers':
            # Initialize powers category if needed
            if 'powers' not in character.db.stats:
                character.db.stats['powers'] = {}
                
            # Handle different power types
            if subcategory in ['thaumaturgy', 'necromancy']:
                success = _handle_path_disciplines(character, stat_name, new_rating, current_rating, subcategory)
                if not success:
                    return False, f"Failed to update {subcategory} path"
            elif subcategory == 'blessing':
                success, error = _handle_blessing_updates(character, stat_name, new_rating)
                if not success:
                    return False, error
            elif subcategory == 'special_advantage':
                success, error = _handle_special_advantage_updates(character, stat_name, new_rating)
                if not success:
                    return False, error
            elif subcategory == 'gift':
                # Special handling for gifts to store original name as alias
                if subcategory not in character.db.stats['powers']:
                    character.db.stats['powers'][subcategory] = {}
                
                # Get the canonical name from the database to ensure we're using the exact name
                from world.wod20th.models import Stat
                from django.db.models import Q
                
                gift = Stat.objects.filter(
                    Q(name__iexact=stat_name) | Q(gift_alias__icontains=stat_name),
                    category='powers',
                    stat_type='gift'
                ).first()
                
                # Use canonical name if found, otherwise use the provided stat_name
                canonical_name = gift.name if gift else stat_name
                
                # Store the gift with its canonical name
                character.db.stats['powers'][subcategory][canonical_name] = {
                    'perm': new_rating,
                    'temp': new_rating
                }
                
                # Store the alias if original stat_name differs from canonical name
                if hasattr(character, 'set_gift_alias') and stat_name.lower() != canonical_name.lower():
                    logger.log_info(f"Storing gift alias: {stat_name} -> {canonical_name}")
                    # Ensure the alias is a string, not a list
                    alias_to_use = stat_name
                    if isinstance(stat_name, list):
                        # If it's a list, use the first element or a joined string
                        if stat_name:
                            alias_to_use = stat_name[0] if len(stat_name) == 1 else " ".join(stat_name)
                        else:
                            alias_to_use = canonical_name  # Fallback if empty list
                    
                    character.set_gift_alias(canonical_name, alias_to_use, new_rating)
                
                logger.log_info(f"Updated gift {canonical_name} to {new_rating}")
            else:
                # Handle other powers normally
                if subcategory not in character.db.stats['powers']:
                    character.db.stats['powers'][subcategory] = {}
                character.db.stats['powers'][subcategory][stat_name] = {
                    'perm': new_rating,
                    'temp': new_rating
                }
                logger.log_info(f"Updated power {stat_name} ({subcategory}) to {new_rating}")  
        # Special handling for merits and flaws
        elif category in ['merits', 'flaws']:
            # Initialize category and subcategory structures if needed
            if category not in character.db.stats:
                character.db.stats[category] = {}
            if subcategory not in character.db.stats[category]:
                character.db.stats[category][subcategory] = {}
                
            # Add or update the merit/flaw
            character.db.stats[category][subcategory][stat_name] = {
                'perm': new_rating,
                'temp': new_rating
            }
            logger.log_info(f"Updated {category} {stat_name} to {new_rating}")
            
            # Special case for Kinfolk with Gnosis merit
            if (category == 'merits' and subcategory == 'supernatural' and
                stat_name.lower() == 'gnosis' and 
                character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '') == 'Mortal+' and 
                character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '') == 'Kinfolk'):
                from world.wod20th.utils.mortalplus_utils import handle_kinfolk_gnosis
                gnosis_value = handle_kinfolk_gnosis(character, new_rating)
                logger.log_info(f"Updated Kinfolk Gnosis pool to {gnosis_value} based on merit rating {new_rating}")
        else:
            # For all other stats, use the character's set_stat method
            character.set_stat(category, subcategory, stat_name, new_rating, temp=False)
            character.set_stat(category, subcategory, stat_name, new_rating, temp=True)
            logger.log_info(f"Updated stat {stat_name} ({category}/{subcategory}) to {new_rating}")

        # Deduct XP - Convert to Decimal for precise calculation
        try:
            current_xp = Decimal(str(character.db.xp['current']))
            spent_xp = Decimal(str(character.db.xp['spent']))
            
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

            # Log the spend
            spend_entry = {
                'type': 'spend',
                'amount': float(cost_decimal),
                'stat_name': stat_name,
                'previous_rating': current_rating,
                'new_rating': new_rating,
                'reason': reason,
                'staff_name': reason.replace('Staff Spend: ', '') if 'Staff Spend: ' in reason else None,
                'timestamp': datetime.now().isoformat()
            }

            if 'spends' not in character.db.xp:
                character.db.xp['spends'] = []
            character.db.xp['spends'].insert(0, spend_entry)

            # Final verification
            logger.log_info(f"Final XP state - Current: {new_current}, Spent: {new_spent}")
            return True, f"Successfully increased {stat_name} from {current_rating} to {new_rating} (Cost: {cost_decimal} XP)"

        except Exception as e:
            logger.log_err(f"Error during XP deduction: {str(e)}")
            return False, f"Error processing XP deduction: {str(e)}"

    except Exception as e:
        logger.log_err(f"Error in process_xp_purchase: {str(e)}")
        return False, f"Error: {str(e)}"

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
        # Get character's splat
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        shifter_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
        
        # Fix case-sensitivity: Get proper case for the stat name if the character has the method
        if hasattr(character, 'get_proper_stat_name'):
            proper_name = character.get_proper_stat_name(category, subcategory, stat_name)
            if proper_name != stat_name:
                logger.log_info(f"Found proper stat name: {proper_name} (was: {stat_name})")
                stat_name = proper_name
        
        # Get current rating with better logging
        logger.log_info(f"Getting current rating for {stat_name} ({category}/{subcategory})")

        # Check current rating based on category 
        current_rating = None
        
        # Exception for abilities/secondary abilities
        if category in ['abilities', 'secondary_abilities']:
            # Find existing stat regardless of case
            if subcategory in character.db.stats.get(category, {}):
                for existing_stat, stat_values in character.db.stats[category][subcategory].items():
                    if existing_stat.lower() == stat_name.lower():
                        current_rating = stat_values.get('perm', 0)
                        logger.log_info(f"Current rating for {existing_stat}: {current_rating}")
                        break
                        
            # If not found, default to 0
            if current_rating is None:
                current_rating = 0
        elif category == 'attributes':
            current_rating = character.db.stats.get('attributes', {}).get(subcategory, {}).get(stat_name, {}).get('perm', 0)
        elif category == 'backgrounds':
            current_rating = character.db.stats.get('backgrounds', {}).get(subcategory, {}).get(stat_name, {}).get('perm', 0)
        elif category == 'merits':
            current_rating = character.db.stats.get('merits', {}).get(subcategory, {}).get(stat_name, {}).get('perm', 0)
        elif category == 'flaws':
            current_rating = character.db.stats.get('flaws', {}).get(subcategory, {}).get(stat_name, {}).get('perm', 0)
        elif category == 'pools':
            current_rating = character.db.stats.get('pools', {}).get(subcategory, {}).get(stat_name, {}).get('perm', 0)
            # Also check advantages for some pool stats
            if current_rating == 0 and subcategory == 'advantage':
                current_rating = character.db.stats.get('advantages', {}).get(stat_name, {}).get('perm', 0)
        elif category == 'powers':
            if subcategory == 'discipline':
                current_rating = character.db.stats.get('powers', {}).get('discipline', {}).get(stat_name, {}).get('perm', 0)
            else:
                current_rating = character.db.stats.get('powers', {}).get(subcategory, {}).get(stat_name, {}).get('perm', 0)
        else:
            current_rating = character.get_stat(category, subcategory, stat_name, temp=False) or 0
            logger.log_info(f"Current rating for {stat_name}: {current_rating}")

        # Validate that new rating is higher than current
        if new_rating <= current_rating:
            return False, "New rating must be higher than current rating", 0

        # Handle attributes
        if category == 'attributes':
            # Calculate attribute cost
            total_cost = calculate_attribute_cost(current_rating, new_rating)
            
            # Check if character has enough XP
            cost_decimal = Decimal(str(total_cost)).quantize(Decimal('0.01'))
            if character.db.xp['current'] < cost_decimal:
                return False, f"Not enough XP. Cost: {cost_decimal}, Available: {character.db.xp['current']}", cost_decimal
                
            # Process the purchase with the pre-calculated cost
            success, message = process_xp_purchase(
                character, stat_name, new_rating, category, subcategory, 
                reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
            )
            
            if success:
                return True, message, total_cost
            else:
                return False, "Failed to process purchase", total_cost

        # Handle abilities (both standard and secondary)
        elif category == 'abilities' or category == 'secondary_abilities':
            total_cost = calculate_ability_cost(current_rating, new_rating)
            
            # Check if character has enough XP
            cost_decimal = Decimal(str(total_cost)).quantize(Decimal('0.01'))
            if character.db.xp['current'] < cost_decimal:
                return False, f"Not enough XP. Cost: {cost_decimal}, Available: {character.db.xp['current']}", cost_decimal
                
            # Process the purchase with the pre-calculated cost
            success, message = process_xp_purchase(
                character, stat_name, new_rating, category, subcategory, 
                reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
            )
            
            if success:
                return True, message, total_cost
            else:
                return False, "Failed to process purchase", total_cost

        # Special handling for Changeling arts and realms
        elif splat == 'Changeling':
            if category == 'powers' and subcategory == 'art':
                total_cost = calculate_art_cost(current_rating, new_rating)
                
                # Check if character has enough XP
                cost_decimal = Decimal(str(total_cost)).quantize(Decimal('0.01'))
                if character.db.xp['current'] < cost_decimal:
                    return False, f"Not enough XP. Cost: {cost_decimal}, Available: {character.db.xp['current']}", cost_decimal
                
                # Process the purchase with the pre-calculated cost
                success, message = process_xp_purchase(
                    character, stat_name, new_rating, category, subcategory, 
                    reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                )
                
                if success:
                    return True, message, total_cost
                else:
                    return False, "Failed to process purchase", total_cost
                    
            elif category == 'powers' and subcategory == 'realm':
                total_cost = calculate_realm_cost(current_rating, new_rating)
                
                # Check if character has enough XP
                cost_decimal = Decimal(str(total_cost)).quantize(Decimal('0.01'))
                if character.db.xp['current'] < cost_decimal:
                    return False, f"Not enough XP. Cost: {cost_decimal}, Available: {character.db.xp['current']}", cost_decimal
                
                # Process the purchase with the pre-calculated cost
                success, message = process_xp_purchase(
                    character, stat_name, new_rating, category, subcategory, 
                    reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                )
                
                if success:
                    return True, message, total_cost
                else:
                    return False, "Failed to process purchase", total_cost

        # Handle backgrounds
        elif category == 'backgrounds':
            total_cost = calculate_background_cost(current_rating, new_rating)
            # Check auto-approve limits
            if stat_name in AUTO_APPROVE['all']['backgrounds']:
                max_auto = AUTO_APPROVE['all']['backgrounds'][stat_name]
                requires_approval = new_rating > max_auto and not is_staff_spend
            else:
                requires_approval = True and not is_staff_spend
            
            # If staff spend or doesn't require approval, proceed with purchase
            if is_staff_spend or not requires_approval:
                success, message = process_xp_purchase(
                    character, stat_name, new_rating, category, subcategory, 
                    reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                )
                return success, message, total_cost
            else:
                return False, f"Staff approval required for {stat_name} background", total_cost

        # Handle willpower
        elif category == 'pools' and subcategory == 'dual' and stat_name.lower() == 'willpower':
            total_cost = calculate_willpower_cost(current_rating, new_rating)
            requires_approval = new_rating > 5 and not is_staff_spend
            
            # If staff spend or doesn't require approval, proceed with purchase
            if is_staff_spend or not requires_approval:
                success, message = process_xp_purchase(
                    character, stat_name, new_rating, category, subcategory, 
                    reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                )
                return success, message, total_cost
            else:
                return False, f"Staff approval required for Willpower above 5", total_cost

        # Special handling for Vampire and Ghoul disciplines
        elif category == 'powers' and subcategory == 'discipline':
            # Check if character is a ghoul
            is_ghoul = (splat == 'Mortal+' and shifter_type == 'Ghoul')
            
            # For vampires
            if splat == 'Vampire':
                clan = character.get_stat('identity', 'lineage', 'Clan', temp=False)
                if clan and clan.lower() == 'caitiff':
                    total_cost = calculate_discipline_cost(current_rating, new_rating, 'caitiff')
                else:
                    # Check if discipline is in-clan
                    from world.wod20th.utils.vampire_utils import is_discipline_in_clan
                    is_in_clan = is_discipline_in_clan(stat_name, clan)
                    total_cost = calculate_discipline_cost(current_rating, new_rating, 'in_clan' if is_in_clan else 'out_clan')
                
                requires_approval = new_rating > 2 and not is_staff_spend
                
                # If staff spend or doesn't require approval, proceed with purchase
                if is_staff_spend or not requires_approval:
                    success, message = process_xp_purchase(
                        character, stat_name, new_rating, category, subcategory, 
                        reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                    )
                    return success, message, total_cost
                else:
                    return False, f"Staff approval required for {stat_name} above level 2", total_cost
            
            # For ghouls
            elif is_ghoul:
                family = character.get_stat('identity', 'lineage', 'Family', temp=False)
                # Determine if discipline is in-clan based on ghoul's family
                is_clan = False
                if family:
                    from world.wod20th.utils.vampire_utils import get_clan_disciplines
                    clan_disciplines = get_clan_disciplines(family)
                    is_clan = stat_name in clan_disciplines
                total_cost = calculate_ghoul_discipline_cost(current_rating, new_rating, is_clan)
                
                requires_approval = new_rating > 1 and not is_staff_spend
                
                # If staff spend or doesn't require approval, proceed with purchase
                if is_staff_spend or not requires_approval:
                    success, message = process_xp_purchase(
                        character, stat_name, new_rating, category, subcategory, 
                        reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                    )
                    return success, message, total_cost
                else:
                    return False, f"Staff approval required for ghoul {stat_name} above level 1", total_cost

        # Handle merits and flaws
        elif category in ['merits', 'flaws']:
            if category == 'merits':
                total_cost = calculate_merit_cost(current_rating, new_rating)
            else:  # flaws
                total_cost = calculate_flaw_cost(current_rating, new_rating)
            
            # These always require approval unless staff spending
            if is_staff_spend:
                success, message = process_xp_purchase(
                    character, stat_name, new_rating, category, subcategory, 
                    reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                )
                return success, message, total_cost
            else:
                return False, f"{category.title()} require staff approval", total_cost

        # Special handling for Mage spheres
        elif category == 'powers' and subcategory == 'sphere' and splat == 'Mage':
            # Check if it's an affinity sphere
            from world.wod20th.utils.mage_utils import is_affinity_sphere
            is_affinity = is_affinity_sphere(character, stat_name)
            
            # Use the corrected function to calculate the cost
            from world.wod20th.utils.xp_costs import calculate_sphere_cost
            total_cost = calculate_sphere_cost(current_rating, new_rating, is_affinity)
            
            # Check if character has enough XP
            cost_decimal = Decimal(str(total_cost)).quantize(Decimal('0.01'))
            if character.db.xp['current'] < cost_decimal:
                return False, f"Not enough XP. Cost: {cost_decimal}, Available: {character.db.xp['current']}", cost_decimal
            
            # Process the purchase with the pre-calculated cost
            success, message = process_xp_purchase(
                character, stat_name, new_rating, category, subcategory, 
                reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
            )
            
            if success:
                return True, message, total_cost
            else:
                return False, "Failed to process purchase", total_cost
            
        # Special handling for Arete
        elif category == 'pools' and subcategory == 'advantage' and stat_name.lower() == 'arete':
            total_cost = calculate_arete_cost(current_rating, new_rating)
            # Arete increases always require approval unless staff spend
            if is_staff_spend:
                success, message = process_xp_purchase(
                    character, stat_name, new_rating, category, subcategory, 
                    reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                )
                return success, message, total_cost
            else:
                return False, "Arete increases require staff approval", total_cost
            
        # Special handling for Avatar
        elif category == 'pools' and subcategory == 'advantage' and stat_name.lower() == 'avatar':
            total_cost = calculate_avatar_cost(current_rating, new_rating)
            # Avatar increases always require approval unless staff spend
            if is_staff_spend:
                success, message = process_xp_purchase(
                    character, stat_name, new_rating, category, subcategory, 
                    reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                )
                return success, message, total_cost
            else:
                return False, "Avatar increases require staff approval", total_cost
            
        # Special handling for Mortal+ types - Kinain arts and realms
        elif splat == 'Mortal+':
            # Kinain arts and realms
            if shifter_type == 'Kinain':
                if category == 'powers' and subcategory == 'art':
                    total_cost = calculate_kinain_art_cost(current_rating, new_rating)
                    requires_approval = new_rating > 2 and not is_staff_spend
                    
                    if is_staff_spend or not requires_approval:
                        success, message = process_xp_purchase(
                            character, stat_name, new_rating, category, subcategory, 
                            reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                        )
                        return success, message, total_cost
                    else:
                        return False, f"Staff approval required for Kinain Arts above level 2", total_cost
                        
                elif category == 'powers' and subcategory == 'realm':
                    total_cost = calculate_kinain_realm_cost(current_rating, new_rating)
                    requires_approval = new_rating > 2 and not is_staff_spend
                    
                    if is_staff_spend or not requires_approval:
                        success, message = process_xp_purchase(
                            character, stat_name, new_rating, category, subcategory, 
                            reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                        )
                        return success, message, total_cost
                    else:
                        return False, f"Staff approval required for Kinain Realms above level 2", total_cost

        # Special handling for Companions
        elif splat == 'Companion':
            if category == 'powers' and subcategory == 'special_advantage':
                total_cost = calculate_special_advantage_cost(current_rating, new_rating)
                # Special advantages always require approval
                if is_staff_spend:
                    success, message = process_xp_purchase(
                        character, stat_name, new_rating, category, subcategory, 
                        reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                    )
                    return success, message, total_cost
                else:
                    return False, "Special advantages require staff approval", total_cost
            elif category == 'powers' and subcategory == 'charm':
                total_cost = calculate_charm_cost(current_rating, new_rating)
                requires_approval = new_rating > 2 and not is_staff_spend
                
                if is_staff_spend or not requires_approval:
                    success, message = process_xp_purchase(
                        character, stat_name, new_rating, category, subcategory, 
                        reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                    )
                    return success, message, total_cost
                else:
                    return False, f"Staff approval required for Charms above level 2", total_cost
                
        # Special handling for Possessed
        elif splat == 'Possessed':
            if category == 'powers' and subcategory == 'blessing':
                total_cost = calculate_blessing_cost(current_rating, new_rating)
                # Blessings always require approval
                if is_staff_spend:
                    success, message = process_xp_purchase(
                        character, stat_name, new_rating, category, subcategory, 
                        reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                    )
                    return success, message, total_cost
                else:
                    return False, "Blessings require staff approval", total_cost
            elif category == 'powers' and subcategory == 'gift':
                total_cost = calculate_possessed_gift_cost(current_rating, new_rating)
                requires_approval = new_rating > 2 and not is_staff_spend
                
                if is_staff_spend or not requires_approval:
                    success, message = process_xp_purchase(
                        character, stat_name, new_rating, category, subcategory, 
                        reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                    )
                    return success, message, total_cost
                else:
                    return False, f"Staff approval required for Possessed gifts above level 2", total_cost
            elif category == 'powers' and subcategory == 'charm':
                total_cost = calculate_charm_cost(current_rating, new_rating)
                requires_approval = new_rating > 2 and not is_staff_spend
                
                if is_staff_spend or not requires_approval:
                    success, message = process_xp_purchase(
                        character, stat_name, new_rating, category, subcategory, 
                        reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                    )
                    return success, message, total_cost
                else:
                    return False, f"Staff approval required for Charms above level 2", total_cost

        # Special handling for Kinfolk gifts (Mortal+ type = Kinfolk)
        elif category == 'powers' and subcategory == 'gift' and splat == 'Mortal+' and shifter_type == 'Kinfolk':
            # Find the gift in database
            from world.wod20th.models import Stat
            from django.db.models import Q
            
            gift = Stat.objects.filter(
                Q(name__iexact=stat_name) | Q(gift_alias__icontains=stat_name),
                category='powers',
                stat_type='gift'
            ).first()
            
            if gift:
                # Get breed and tribe for matching
                breed = character.get_stat('identity', 'lineage', 'Kinfolk Breed', temp=False)
                tribe = character.get_stat('identity', 'lineage', 'Tribe', temp=False)
                
                # Check if it's a homid or tribe gift
                is_homid_gift = False
                is_tribe_gift = False
                
                # Check for homid gifts
                if gift.breed:
                    breeds = gift.breed if isinstance(gift.breed, list) else [gift.breed]
                    is_homid_gift = any(b.lower() == 'homid' for b in breeds)
                
                # Check for tribe gift
                if gift.tribe and tribe:
                    tribes = gift.tribe if isinstance(gift.tribe, list) else [gift.tribe]
                    is_tribe_gift = tribe.lower() in [t.lower() for t in tribes]
                
                # Kinfolk can only purchase homid gifts or gifts from their tribe
                if not (is_homid_gift or is_tribe_gift):
                    return False, f"Kinfolk can only learn Homid gifts or gifts of their tribe ({tribe})", 0
                
                # Determine gift type for cost calculation
                gift_type = 'breed_tribe' if (is_homid_gift or is_tribe_gift) else 'outside'
                
                # Import the Kinfolk gift cost calculator
                from world.wod20th.utils.mortalplus_utils import calculate_kinfolk_gift_cost
                total_cost = calculate_kinfolk_gift_cost(
                    current_rating=current_rating,
                    new_rating=new_rating,
                    gift_type=gift_type
                )
                
                # Check if Kinfolk has Gnosis Merit for level 2 gifts
                if new_rating > 1:
                    gnosis_merit = next((value.get('perm', 0) for merit, value in character.db.stats.get('merits', {}).get('supernatural', {}).items() 
                                      if merit.lower() == 'gnosis'), 0)
                    if not gnosis_merit:
                        return False, "Must have the Gnosis Merit to learn level 2 gifts", total_cost
                
                # Process the purchase
                requires_approval = new_rating > 2 and not is_staff_spend
                if is_staff_spend or not requires_approval:
                    success, message = process_xp_purchase(
                        character, stat_name, new_rating, category, subcategory, 
                        reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                    )
                    return success, message, total_cost
                else:
                    return False, "Kinfolk cannot learn gifts above level 2", total_cost

        # Handle Gifts for Shifters
        if category == 'powers' and subcategory == 'gift':
            # First check if this is a Kinfolk character
            is_kinfolk = (splat == 'Mortal+' and 
                         character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '') == 'Kinfolk')
            
            # Special handling for Kinfolk characters
            if is_kinfolk:
                logger.log_info(f"Character {character.name} is a Kinfolk, using special handler")
                from world.wod20th.utils.mortalplus_utils import handle_kinfolk_gift_cost
                total_cost, error_msg, requires_approval = handle_kinfolk_gift_cost(
                    character=character,
                    stat_name=stat_name,
                    new_rating=new_rating,
                    current_rating=current_rating
                )
                
                if error_msg:
                    return False, error_msg, total_cost
                
                if requires_approval and not is_staff_spend:
                    return False, "Kinfolk gifts above level 2 require staff approval", total_cost
                
                # Process the purchase
                success, message = process_xp_purchase(
                    character, stat_name, new_rating, category, subcategory, 
                    reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                )
                return success, message, total_cost
                
            # Regular Shifter gift handling
            elif splat == 'Shifter':
                # Find the gift in database
                from world.wod20th.models import Stat
                from django.db.models import Q
                
                gift = Stat.objects.filter(
                    Q(name__iexact=stat_name) | Q(gift_alias__icontains=stat_name),
                    category='powers',
                    stat_type='gift'
                ).first()
                
                if gift:
                    # Determine gift type
                    shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
                    breed = character.get_stat('identity', 'lineage', 'Breed', temp=False)
                    auspice = character.get_stat('identity', 'lineage', 'Auspice', temp=False)
                    tribe = character.get_stat('identity', 'lineage', 'Tribe', temp=False)
                    aspect = character.get_stat('identity', 'lineage', 'Aspect', temp=False)
                    
                    # Check if it's a breed, auspice, or tribe gift
                    from world.wod20th.utils.shifter_utils import _check_shifter_gift_match as shifter_check_gift_match
                    is_breed_gift, is_auspice_gift, is_tribe_gift = shifter_check_gift_match(
                        character=character, 
                        gift_data={
                            'name': gift.name,
                            'breed': gift.breed,
                            'auspice': gift.auspice,
                            'tribe': gift.tribe
                        }, 
                        shifter_type=shifter_type
                    )
                    
                    # Check for special gifts
                    is_special = False
                    if gift.tribe:
                        tribes = gift.tribe if isinstance(gift.tribe, list) else [gift.tribe]
                        is_special = any(t.lower() in ['croatan', 'planetary', 'ju-fu'] for t in tribes)
                    
                    # Determine gift type for cost calculation
                    if is_special:
                        gift_type = 'special'
                    elif is_breed_gift or is_auspice_gift or is_tribe_gift:
                        gift_type = 'breed_tribe_auspice'
                    else:
                        gift_type = 'outside'
                    
                    # Calculate cost
                    from world.wod20th.utils.shifter_utils import calculate_gift_cost as shifter_calculate_gift_cost
                    total_cost = shifter_calculate_gift_cost(
                        character=character,
                        gift_name=gift.name,
                        new_rating=new_rating,
                        current_rating=current_rating
                    )
                    requires_approval = new_rating > (1 if gift_type != 'special' else 0) and not is_staff_spend
                    
                    if is_staff_spend or not requires_approval:
                        success, message = process_xp_purchase(
                            character, stat_name, new_rating, category, subcategory, 
                            reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
                        )
                        return success, message, total_cost
                    else:
                        approval_msg = "Special gifts always require staff approval" if is_special else f"Gifts above level 1 require staff approval"
                        return False, approval_msg, total_cost

        # Special handling for Kinfolk attempting to buy Gnosis directly
        if (category == 'pools' and subcategory == 'dual' and 
            stat_name.lower() == 'gnosis' and 
            splat == 'Mortal+' and 
            character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '') == 'Kinfolk'):
            
            logger.log_info(f"Character is a Kinfolk trying to buy Gnosis as a pool - redirecting to merit")
            
            # For Kinfolk, Gnosis is bought as a merit, so convert to proper category/subcategory
            category = 'merits'
            subcategory = 'supernatural'
            
            # Get current merit rating
            current_rating = character.get_stat(category, subcategory, stat_name, temp=False) or 0
            
            # Calculate cost using merit cost formula: (new_rating - current_rating) * 5
            total_cost = (new_rating - current_rating) * 5
            
            logger.log_info(f"Calculated Kinfolk Gnosis merit cost: {total_cost}")
            
            # Check if they can afford it
            current_xp = character.db.xp.get('current', 0)
            if current_xp < total_cost:
                return False, f"Not enough XP. Kinfolk Gnosis costs {total_cost}XP ({new_rating - current_rating} dots at 5XP each), but you only have {current_xp}XP.", total_cost
            
            # Kinfolk can only have Gnosis up to 3
            if new_rating > 3:
                return False, "Kinfolk can only have up to 3 dots in Gnosis.", total_cost
            
            # Staff approval required for Gnosis
            return False, "Buying Gnosis as a Kinfolk requires staff approval. Please use +request.", total_cost

        # Default to basic ability cost if no other rules apply
        logger.log_info(f"No specific cost rule found for {stat_name} ({category}/{subcategory}), using default ability cost")
        total_cost = calculate_ability_cost(current_rating, new_rating)
        requires_approval = new_rating > 3 and not is_staff_spend

        if is_staff_spend or not requires_approval:
            success, message = process_xp_purchase(
                character, stat_name, new_rating, category, subcategory, 
                reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
            )
            return success, message, total_cost
        else:
            return False, f"Staff approval required for {stat_name} above level 3", total_cost

    except Exception as e:
        logger.log_err(f"Error in process_xp_spend: {str(e)}")
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

def buy_stat(self, stat_name, new_rating, category=None, subcategory=None, reason="", current_rating=None):
    """Buy or increase a stat with XP."""
    try:
        # Preserve original case of stat_name
        original_stat_name = stat_name
        
        # Fix any power issues before proceeding
        if category == 'powers':
            self.fix_powers()
            # After fixing, ensure we're using the correct subcategory
            if subcategory in ['sphere', 'art', 'realm', 'discipline', 'gift', 'charm', 'blessing', 'rite', 'sorcery', 'thaumaturgy', 'necromancy', 'necromancy_ritual', 'thaum_ritual', 'hedge_ritual', 'numina', 'faith']:
                # Convert to singular form
                subcategory = subcategory.rstrip('s')
                if subcategory == 'advantage':
                    subcategory = 'special_advantage'

        # For secondary abilities, ensure proper case
        if category == 'secondary_abilities':
            stat_name = ' '.join(word.title() for word in stat_name.split())
            original_stat_name = stat_name  # Update original_stat_name to match proper case

        # Ensure proper structure exists
        self.ensure_stat_structure(category, subcategory)
        
        # Get character's splat
        splat = self.get_stat('other', 'splat', 'Splat', temp=False)
        if not splat:
            return False, "Character splat not set"

        # Get current form for shifters
        current_form = self.db.current_form if hasattr(self.db, 'current_form') else None
        form_modifier = 0
        
        if splat == 'Shifter' and current_form and current_form.lower() != 'homid':
            try:
                from world.wod20th.models import ShapeshifterForm
                # Get character's shifter type
                shifter_type = self.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '').lower()
                
                # Query form by both name and shifter type
                form = ShapeshifterForm.objects.get(
                    name__iexact=current_form,
                    shifter_type=shifter_type
                )
                form_modifier = form.stat_modifiers.get(stat_name.lower(), 0)
                
                # Special handling for stats that should be set to 0 in certain forms
                zero_appearance_forms = [
                    'crinos',      # All shapeshifters
                    'anthros',     # Ajaba war form
                    'arthren',     # Gurahl war form
                    'sokto',       # Bastet war form
                    'chatro'       # Bastet battle form
                ]
                if (stat_name.lower() == 'appearance' and 
                    current_form.lower() in zero_appearance_forms):
                    form_modifier = -999  # Force to 0
                elif (stat_name.lower() == 'manipulation' and 
                        current_form.lower() == 'crinos'):
                    form_modifier = -2  # Crinos form penalty
                
            except (ShapeshifterForm.DoesNotExist, AttributeError) as e:
                print(f"DEBUG: Form lookup error - {str(e)}")
                form_modifier = 0

        # If current_rating wasn't provided, get it
        if current_rating is None:
            current_rating = self.get_stat(category, subcategory, stat_name, temp=False) or 0

        # Calculate cost
        cost, requires_approval = self.calculate_xp_cost(
            stat_name=stat_name,
            new_rating=new_rating,
            category=category,
            subcategory=subcategory,
            current_rating=current_rating
        )

        if cost == 0:
            return False, "Cost returned as 0. This usually indicates an error with the stat name, rating, or you already have the stat at that rating."

        if requires_approval:
            return False, "This purchase requires staff approval"

        # Check if we have enough XP
        if self.db.xp['current'] < cost:
            return False, f"Not enough XP. Cost: {cost}, Available: {self.db.xp['current']}"

        # Validate the purchase
        can_purchase, error_msg = self.validate_xp_purchase(
            stat_name, new_rating,
            category=category, subcategory=subcategory
        )

        if not can_purchase:
            return False, error_msg

        # All checks passed, make the purchase
        try:
            # For secondary abilities, use the original case
            if category == 'secondary_abilities':
                stat_name = original_stat_name
            
            # Update the stat with form handling
            if category and subcategory:
                # Special handling for secondary abilities
                if category == 'secondary_abilities':
                    # Ensure the secondary_abilities structure exists
                    if 'secondary_abilities' not in self.db.stats:
                        self.db.stats['secondary_abilities'] = {}
                    if subcategory not in self.db.stats['secondary_abilities']:
                        self.db.stats['secondary_abilities'][subcategory] = {}
                    
                    # Store the secondary ability in the correct location
                    self.db.stats['secondary_abilities'][subcategory][stat_name] = {
                        'perm': new_rating,
                        'temp': new_rating
                    }
                else:
                    if stat_name not in self.db.stats[category][subcategory]:
                        self.db.stats[category][subcategory][stat_name] = {}
                    
                    # Set the permanent value
                    self.db.stats[category][subcategory][stat_name]['perm'] = new_rating
                    
                    # Calculate temporary value with form modifier
                    if form_modifier == -999:  # Special case for forced 0
                        temp_value = 0
                    else:
                        temp_value = max(0, new_rating + form_modifier)  # Ensure non-negative
                    
                    self.db.stats[category][subcategory][stat_name]['temp'] = temp_value
            else:
                # Use set_stat for non-form-modified stats
                self.set_stat(category, subcategory, stat_name, new_rating, temp=False)
                self.set_stat(category, subcategory, stat_name, new_rating, temp=True)

            # Deduct XP
            self.db.xp['current'] -= Decimal(str(cost))
            self.db.xp['spent'] += Decimal(str(cost))

            # Log the spend
            spend_entry = {
                'type': 'spend',
                'amount': float(cost),
                'stat_name': stat_name,
                'previous_rating': current_rating,
                'new_rating': new_rating,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }

            if 'spends' not in self.db.xp:
                self.db.xp['spends'] = []
            self.db.xp['spends'].insert(0, spend_entry)

            return True, f"Successfully increased {stat_name} from {current_rating} to {new_rating} (Cost: {cost} XP)"

        except Exception as e:
            return False, f"Error processing purchase: {str(e)}"

    except Exception as e:
        return False, f"Error: {str(e)}"

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
    for bg in all_backgrounds:
        if isinstance(bg, str) and bg.lower() == base_name_lower:
            logger.log_info(f"Found case-insensitive background match: {bg}")
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

    # Check if it's a merit
    for merit_type, merits in MERIT_CATEGORIES.items():
        # Try exact match first
        if stat_name in merits:
            return ('merits', merit_type)
        # Try case-insensitive match
        stat_lower = stat_name.lower()
        for merit in merits:
            if merit.lower() == stat_lower:
                return ('merits', merit_type)

    # Check if it's a flaw
    for flaw_type, flaws in FLAW_CATEGORIES.items():
        # Try exact match first
        if stat_name in flaws:
            return ('flaws', flaw_type)
        # Try case-insensitive match
        stat_lower = stat_name.lower()
        for flaw in flaws:
            if flaw.lower() == stat_lower:
                return ('flaws', flaw_type)

    # Check if it's a blessing
    if stat_name in BLESSINGS:
        return ('powers', 'blessing')

    # Check if it's a charm
    if stat_name in CHARMS:
        return ('powers', 'charm')

    # Check if it's a special advantage
    if stat_name.lower() in SPECIAL_ADVANTAGES or stat_name.lower() in COMBAT_SPECIAL_ADVANTAGES:
        return ('powers', 'special_advantage')

    # Define a complete list of disciplines for better matching
    ALL_DISCIPLINES = [
        'Potence', 'Celerity', 'Fortitude', 'Obfuscate', 'Auspex', 'Dominate', 
        'Presence', 'Animalism', 'Protean', 'Serpentis', 'Necromancy', 
        'Thaumaturgy', 'Dementation', 'Obtenebration', 'Quietus', 'Chimerstry',
        'Vicissitude', 'Mortis', 'Thanatosis', 'Melpominee', 'Mytherceria',
        'Visceratika', 'Daimoinon', 'Spiritus', 'Sanguinus', 'Kai', 'Bardo',
        'Deimos', 'Temporis', 'Ogham', 'Obeah', 'Abombwe', 'Valeren'
    ]

    ALL_THAUMATURGY = [
        'Path of Blood',
        'Elemental Mastery',
        'Movement of the Mind',
        'Lure of Flames',
        'Weather Control',
        'The Green Path',
        'The Path of Conjuring',
        'Hands of Destruction',
        'Neptune\'s Might',
        'Path of Mars',
        'Technomancy',
        'Path of Corruption',
        'Path of the Father\'s Vengeance'
    ]

    ALL_NECROMANCY = [
        'Sepulchre Path',
        'Bone Path',
        'Ash Path',
        'Vitreous Path',
        'Cenotaph Path',
        'Path of Abombo',
        'Path of Woe',
        'Nightshade Path',
        'Path of Haunting',
        'Grave\'s Decay',
        'Path of Skulls',
        'Twilight Garden',
        'Corpse in the Monster',
    ]

    # Check if it's a sphere
    if stat_name in MAGE_SPHERES:
        return ('powers', 'sphere')

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
    if base_name in PURCHASABLE_DISCIPLINES or base_name in ALL_DISCIPLINES:
        return ('powers', 'discipline')
        
    # Case-insensitive check for disciplines
    base_name_lower = base_name.lower()
    for disc in ALL_DISCIPLINES:
        if disc.lower() == base_name_lower:
            return ('powers', 'discipline')

    # Check if it's a thaumaturgy path
    if base_name in ALL_THAUMATURGY:
        return ('powers', 'thaumaturgy')
    base_name_lower = base_name.lower()
    for thaum in ALL_THAUMATURGY:
        if thaum.lower() == base_name_lower:
            return ('powers', 'thaumaturgy')

    # Check if it's a necromancy path
    if base_name in ALL_NECROMANCY:
        return ('powers', 'necromancy')
    base_name_lower = base_name.lower()
    for necromancy in ALL_NECROMANCY:
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
    Spend XP on a stat with staff approval.
    """
    caller = self.caller
    
    # If no category/subcategory provided, try to determine them
    if not category or not subcategory:
        from world.wod20th.utils.xp_utils import _determine_stat_category
        category, subcategory = _determine_stat_category(stat_name)
        
    target = self.target
    if not target:
        caller.msg("No target set.")
        return
        
    # Perform specialized processing
    from world.wod20th.utils.shifter_utils import _check_shifter_gift_match as shifter_gift_match
    from world.wod20th.utils.shifter_utils import calculate_gift_cost as shifter_calculate_gift_cost
   
    current_rating = 0
    
    # Get current rating with better logging
    logger.log_info(f"Getting current rating for {stat_name} ({category}/{subcategory})")
    
    # Handle case-insensitive matching
    if category in ['abilities', 'secondary_abilities']:
        stat_name_lower = stat_name.lower()
        stats_dict = target.db.stats.get(category, {}).get(subcategory, {})
        for existing_name, values in stats_dict.items():
            if existing_name.lower() == stat_name_lower:
                current_rating = values.get('perm', 0)
                # Use the properly cased name from this point on
                stat_name = existing_name
                break
        if current_rating is None:
            current_rating = 0
    elif category == 'powers' and subcategory in ['discipline', 'gift', 'sphere', 'art', 'realm', 'thaumaturgy', 'sorcery', 'numina', 'blessing', 'special_advantage', 'charm', 'necromancy', 'thaum_ritual', 'necromancy_ritual', 'faith', 'arcanos', 'hedge_ritual']:
        # Special handling for powers with case sensitivity issues
        stat_name_lower = stat_name.lower()
        stats_dict = target.db.stats.get('powers', {}).get(subcategory, {})
        for existing_name, values in stats_dict.items():
            if existing_name.lower() == stat_name_lower:
                current_rating = values.get('perm', 0)
                # Use the properly cased name from this point on
                stat_name = existing_name
                break
        if current_rating is None:
            current_rating = 0
    else:
        current_rating = target.get_stat(category, subcategory, stat_name, temp=False) or 0
        
    logger.log_info(f"Current rating for {stat_name}: {current_rating}")
    
    # Calculate cost - this is a staff spend, so we manually calculate cost
    if category == 'powers' and subcategory == 'discipline':
        total_cost = calculate_discipline_cost(current_rating, new_rating)
    elif category == 'powers' and subcategory == 'gift':
        # Get character's splat
        splat = target.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        
        if splat == 'Shifter':
            # Import locally to avoid circular import
            from world.wod20th.utils.shifter_utils import calculate_gift_cost as shifter_gift_cost
            # Use named parameters to avoid confusion
            total_cost = shifter_gift_cost(
                character=target,
                gift_name=stat_name,
                new_rating=new_rating,
                current_rating=current_rating
            )
        elif splat == 'Mortal+' and target.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '') == 'Kinfolk':
            from world.wod20th.utils.mortalplus_utils import calculate_kinfolk_gift_cost
            total_cost = calculate_kinfolk_gift_cost(current_rating, new_rating)
        elif splat == 'Possessed':
            from world.wod20th.utils.possessed_utils import calculate_possessed_gift_cost
            total_cost = calculate_possessed_gift_cost(current_rating, new_rating)
        else:
            # Default to standard gift cost
            from world.wod20th.utils.xp_costs import calculate_gift_cost as standard_gift_cost
            total_cost = standard_gift_cost(current_rating, new_rating)
    elif category == 'powers' and subcategory == 'sphere':
        total_cost = calculate_sphere_cost(current_rating, new_rating)
    elif category == 'powers' and subcategory == 'art':
        total_cost = calculate_art_cost(current_rating, new_rating)
    elif category == 'powers' and subcategory == 'realm':
        total_cost = calculate_realm_cost(current_rating, new_rating)
    elif category == 'powers' and subcategory == 'dual':
        if stat_name == 'Willpower':
            total_cost = calculate_willpower_cost(current_rating, new_rating)
        elif stat_name == 'Rage':
            total_cost = calculate_rage_cost(current_rating, new_rating)
        elif stat_name == 'Gnosis':
            total_cost = calculate_gnosis_cost(current_rating, new_rating)
        elif stat_name == 'Glamour':
            total_cost = calculate_glamour_cost(current_rating, new_rating)
    elif category == 'powers' and subcategory == 'special_advantage':
        total_cost = calculate_special_advantage_cost(current_rating, new_rating)
    elif category == 'powers' and subcategory == 'charm':
        total_cost = calculate_charm_cost(current_rating, new_rating)
    elif category == 'powers' and subcategory == 'blessing':
        total_cost = calculate_blessing_cost(current_rating, new_rating)
    elif category == 'powers' and subcategory == 'necromancy':
        total_cost = calculate_thaumaturgy_path_cost(current_rating, new_rating)
    elif category == 'powers' and subcategory == 'sorcery':
        total_cost = calculate_sorcerous_path_cost(current_rating, new_rating)
    elif category == 'powers' and subcategory == 'numina':
        total_cost = calculate_numina_cost(current_rating, new_rating)
    elif category == 'powers' and subcategory == 'faith':
        total_cost = calculate_faith_cost(current_rating, new_rating)
    elif category == 'powers' and subcategory == 'arcanos':
        total_cost = calculate_arcanos_cost(current_rating, new_rating)
    elif category == 'powers' and subcategory == 'hedge_ritual':
        total_cost = calculate_sorcerous_ritual_cost(current_rating, new_rating)
    elif category == 'powers' and subcategory == 'thaum_ritual':
        total_cost = calculate_ritual_cost(current_rating, new_rating)
    elif category == 'powers' and subcategory == 'necromancy_ritual':
        total_cost = calculate_ritual_cost(current_rating, new_rating)
    else:
        total_cost = calculate_xp_cost(current_rating, new_rating)
    
    # Process the purchase
    success, message = process_xp_purchase(
        target, stat_name, new_rating, category, subcategory, 
        reason=reason, current_rating=current_rating, pre_calculated_cost=total_cost
    )
    
    return success, message, total_cost

def proper_title_case(text):
    """
    Convert text to proper title case, keeping certain words lowercase.
    
    Args:
        text (str): The text to convert
        
    Returns:
        str: The properly title-cased text
    """
    if not text:
        return text
        
    # List of words that should be lowercase in titles
    lowercase_words = ['a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 
                      'on', 'at', 'to', 'from', 'by', 'of', 'in', 'with']
    
    # Split the text into words
    words = text.split()
    
    # Always capitalize the first word
    if words:
        words[0] = words[0].capitalize()
    
    # Process the remaining words
    for i in range(1, len(words)):
        if words[i].lower() in lowercase_words:
            words[i] = words[i].lower()
        else:
            words[i] = words[i].capitalize()
    
    # Join the words back together
    return ' '.join(words)