"""
Utility functions for XP management.
"""
from world.wod20th.utils.sheet_constants import (
    TALENTS, SKILLS, KNOWLEDGES,
    SECONDARY_TALENTS, SECONDARY_SKILLS, SECONDARY_KNOWLEDGES,
    POWERS, BACKGROUNDS, MERITS, FLAWS, HEALTH, RENOWN,
    SHIFTER_TYPE, KITH, CLAN, BREED, GAROU_TRIBE,
    ATTRIBUTES, ABILITIES, ADVANTAGES, BLESSINGS, CHARMS
)
from world.wod20th.utils.stat_mappings import (
    MAGE_SPHERES, ARTS, REALMS, VALID_MORTALPLUS_TYPES,
    VALID_POSSESSED_TYPES, VALID_SHIFTER_TYPES, VALID_SPLATS,
    REQUIRED_INSTANCES, KINFOLK_BREED_CHOICES, SPECIAL_ADVANTAGES, COMBAT_SPECIAL_ADVANTAGES,
    MERIT_CATEGORIES, FLAW_CATEGORIES, MERIT_VALUES, FLAW_VALUES, UNIVERSAL_BACKGROUNDS, VAMPIRE_BACKGROUNDS, CHANGELING_BACKGROUNDS, MAGE_BACKGROUNDS,
    TECHNOCRACY_BACKGROUNDS, TRADITIONS_BACKGROUNDS, NEPHANDI_BACKGROUNDS, SHIFTER_BACKGROUNDS,
    SORCERER_BACKGROUNDS, KINAIN_BACKGROUNDS
)
from world.wod20th.utils.ritual_data import THAUMATURGY_RITUALS, NECROMANCY_RITUALS

from evennia.objects.models import ObjectDB
from evennia.utils import logger
from decimal import Decimal
from datetime import datetime, timedelta
import ast
from world.wod20th.models import Stat
from django.db.models import Q
from commands.CmdSelfStat import REQUIRED_SPECIALTIES

# Constants
PURCHASABLE_DISCIPLINES = ['Potence', 'Celerity', 'Fortitude', 'Obfuscate', 'Auspex']

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

def free_specialty_check(character):
    """Check if the character has free specialty slots."""
    # Check if the character is in chargen
    if character.db.is_approved:
        return False
    
    # Check for high-level abilities and attributes (4+)
    # Check abilities
    for category in ['talent', 'skill', 'knowledge']:
        abilities = character.db.stats.get('abilities', {}).get(category, {})
        for ability_name, ability_data in abilities.items():
            if ability_data.get('perm', 0) >= 4:
                return True
                
            # Check for required specialties (case-insensitive matching)
            for req_ability in REQUIRED_SPECIALTIES:
                if ability_name.lower() == req_ability.lower() and ability_data.get('perm', 0) > 0:
                    return True
    
    # Check secondary abilities
    for category in ['secondary_talent', 'secondary_skill', 'secondary_knowledge']:
        abilities = character.db.stats.get('secondary_abilities', {}).get(category, {})
        for ability_name, ability_data in abilities.items():
            if ability_data.get('perm', 0) >= 4:
                return True
                
            # Check for required specialties (case-insensitive matching)
            for req_ability in REQUIRED_SPECIALTIES:
                if ability_name.lower() == req_ability.lower() and ability_data.get('perm', 0) > 0:
                    return True
    
    # Check attributes
    for category in ['physical', 'social', 'mental']:
        attributes = character.db.stats.get('attributes', {}).get(category, {})
        for attribute_name, attribute_data in attributes.items():
            if attribute_data.get('perm', 0) >= 4:
                return True
    
    return False

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

def calculate_xp_cost(character, stat_name, new_rating, category=None, subcategory=None, current_rating=None):
    """Calculate XP cost for increasing a stat."""
    try:
        # Convert new_rating to integer
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

    # Normalize subcategory for disciplines
    if category == 'powers' and subcategory == 'disciplines':
        subcategory = 'discipline'

    # Handle instanced backgrounds
    base_stat_name = stat_name
    if '(' in stat_name and ')' in stat_name:
        # Extract the base name without the instance
        base_stat_name = stat_name[:stat_name.find('(')].strip()
    
    # Get current rating if not provided
    if current_rating is None:
        if category == 'powers':
            if subcategory == 'discipline':
                current_rating = character.db.stats.get('powers', {}).get('discipline', {}).get(stat_name, {}).get('perm', 0)
            elif subcategory in ['thaumaturgy', 'necromancy']:
                current_rating = character.db.stats.get('powers', {}).get(subcategory, {}).get(stat_name, {}).get('perm', 0)
            else:
                current_rating = character.db.stats.get('powers', {}).get(subcategory, {}).get(stat_name, {}).get('perm', 0)
        elif category == 'backgrounds' and '(' in stat_name and ')' in stat_name:
            # Look up the specific instanced background
            current_rating = character.db.stats.get(category, {}).get(subcategory, {}).get(stat_name, {}).get('perm', 0)
        elif category == 'pools' and subcategory == 'dual':
            # Get current pool rating
            current_rating = character.db.stats.get('pools', {}).get('dual', {}).get(stat_name, {}).get('perm', 0)
        else:
            current_rating = character.get_stat(category, subcategory, stat_name) or 0

    # Initialize cost and requires_approval
    total_cost = 0
    requires_approval = False

    # Special handling for Thaumaturgy and Necromancy paths
    if category == 'powers' and subcategory in ['thaumaturgy', 'necromancy']:
        # Get primary path
        if subcategory == 'thaumaturgy':
            primary_path = _get_primary_thaumaturgy_path(character)
        else:  # necromancy
            primary_path = _get_primary_necromancy_path(character)

        # Check discipline rating
        discipline_name = 'Thaumaturgy' if subcategory == 'thaumaturgy' else 'Necromancy'
        discipline_rating = character.db.stats.get('powers', {}).get('discipline', {}).get(discipline_name, {}).get('perm', 0)
        
        # Cannot exceed discipline rating
        if new_rating > discipline_rating:
            return (0, False)
            
        # Calculate cost based on whether this is primary or secondary path
        if stat_name == primary_path:
            # Primary path costs 5 XP per level
            total_cost = sum(5 for i in range(current_rating + 1, new_rating + 1))
        else:
            # Secondary path costs 7 for first level, then current rating × 4
            if current_rating == 0:
                total_cost = 7  # First dot always costs 7
                if new_rating > 1:  # If buying multiple levels
                    # For each additional level, cost is previous rating × 4
                    for i in range(1, new_rating):
                        total_cost += i * 4
            else:
                # Cost is current rating × 4
                total_cost = current_rating * 4
                
        requires_approval = True  # Always require staff approval
        return (total_cost, requires_approval)

    # Special handling for Thaumaturgy and Necromancy disciplines
    if category == 'powers' and subcategory == 'discipline' and stat_name in ['Thaumaturgy', 'Necromancy']:
        # Check if it's an in-clan discipline
        clan = character.db.stats.get('identity', {}).get('lineage', {}).get('Clan', {}).get('perm', '')
        is_in_clan = _is_discipline_in_clan(stat_name, clan)
        
        # Calculate discipline cost
        total_cost = 0
        for rating in range(current_rating + 1, new_rating + 1):
            if rating == 1:
                total_cost += 10  # First dot always costs 10
            else:
                if is_in_clan:
                    total_cost += (rating - 1) * 5  # Previous rating × 5
                else:
                    total_cost += (rating - 1) * 7  # Previous rating × 7
        
        requires_approval = True  # Always require staff approval
        return (total_cost, requires_approval)

    # Special handling for blessings and charms
    if category == 'powers':
        if subcategory == 'blessing':
            # Validate against BLESSINGS list
            if stat_name not in BLESSINGS:
                return (0, False)
            # Blessings cost New Rating x 4 XP
            total_cost = new_rating * 4
            requires_approval = new_rating > 3
            return (total_cost, requires_approval)
        elif subcategory == 'charm':
            # Charms are flat 5 XP per purchase
            total_cost = 5
            requires_approval = False
            return (total_cost, requires_approval)
        elif subcategory == 'special_advantage':
            # Check against SPECIAL_ADVANTAGES dictionary
            if stat_name.lower() in SPECIAL_ADVANTAGES:
                advantage_info = SPECIAL_ADVANTAGES[stat_name.lower()]
                if new_rating in advantage_info['valid_values']:
                    total_cost = new_rating * 1  # Cost is rating × 1
                    requires_approval = new_rating > 5
                    return (total_cost, requires_approval)
            elif stat_name.lower() in COMBAT_SPECIAL_ADVANTAGES:
                advantage_info = COMBAT_SPECIAL_ADVANTAGES[stat_name.lower()]
                if new_rating in advantage_info['valid_values']:
                    total_cost = new_rating * 2  # Cost is rating × 2
                    requires_approval = new_rating > 5
                    return (total_cost, requires_approval)
            return (0, False)  # Invalid special advantage or rating
    
    # Handle pools (Willpower, Rage, Gnosis)
    if category == 'pools' and subcategory == 'dual':
        # Different costs based on pool type
        if stat_name == 'Willpower':
            # Willpower costs Current Rating * 2 XP
            total_cost = sum(i * 2 for i in range(current_rating + 1, new_rating + 1))
            requires_approval = new_rating > 5
        elif stat_name == 'Rage':
            # Rage costs Current Rating XP
            total_cost = sum(i for i in range(current_rating + 1, new_rating + 1))
            requires_approval = new_rating > 5
        elif stat_name == 'Gnosis':
            # Gnosis costs Current Rating * 2 XP
            total_cost = sum(i * 2 for i in range(current_rating + 1, new_rating + 1))
            requires_approval = new_rating > 5
        elif stat_name == 'Glamour':
            # Glamour costs Current Rating * 3 XP
            total_cost = sum(i * 3 for i in range(current_rating + 1, new_rating + 1))
            requires_approval = new_rating > 5
        elif stat_name in ['Arete', 'Enlightenment']:
            # Arete and Enlightenment cost Current Rating * 8 XP
            total_cost = sum(i * 8 for i in range(current_rating + 1, new_rating + 1))
            requires_approval = new_rating > 1 # Arete and Enlightenment are always 1 or higher and always require staff approval for raising.
        return (total_cost, requires_approval)

    # Special handling for Thaumaturgy and Necromancy rituals
    if category == 'powers' and subcategory in ['thaum_ritual', 'necromancy_ritual']:
        # Check if the corresponding discipline is in-clan
        clan = character.db.stats.get('identity', {}).get('lineage', {}).get('Clan', {}).get('perm', '')
        discipline_name = 'Thaumaturgy' if subcategory == 'thaum_ritual' else 'Necromancy'
        is_in_clan = _is_discipline_in_clan(discipline_name, clan)
        
        # Check if character has the required discipline rating
        discipline_rating = character.db.stats.get('powers', {}).get('discipline', {}).get(discipline_name, {}).get('perm', 0)
        
        # Get ritual level from the appropriate dictionary
        ritual_dict = THAUMATURGY_RITUALS if subcategory == 'thaum_ritual' else NECROMANCY_RITUALS
        ritual_level = None
        
        # Case-insensitive lookup
        for ritual_name, level in ritual_dict.items():
            if ritual_name.lower() == stat_name.lower():
                ritual_level = level
                break
                
        if ritual_level is None:
            return (0, False)  # Invalid ritual
        
        # Cannot learn rituals higher than discipline rating
        if ritual_level > discipline_rating:
            return (0, False)
            
        # Calculate cost based on in-clan status
        if is_in_clan:
            total_cost = ritual_level * 2  # Level x 2 XP for in-clan
        else:
            total_cost = ritual_level * 3  # Level x 3 XP for out-of-clan
            
        requires_approval = True  # Always require staff approval for rituals
        return (total_cost, requires_approval)

    # Calculate cost for each dot being purchased
    for rating in range(current_rating + 1, new_rating + 1):
        dot_cost = 0
        
        # Calculate base cost based on stat type
        if category == 'attributes':
            # First dot (0->1) should be free during character creation
            # Second dot (1->2) costs 8
            # Each subsequent dot costs current rating × 4
            if rating == 2:
                dot_cost = 8  # Going from 1 to 2 specifically costs 8
            else:
                dot_cost = (rating - 1) * 4  # For rating 3+, use previous rating × 4
            requires_approval = rating > 3

        elif category in ['abilities', 'secondary_abilities']:
            if subcategory in ['talent', 'skill', 'knowledge', 'secondary_talent', 'secondary_skill', 'secondary_knowledge']:
                if rating == 1:
                    dot_cost = 3  # First dot always costs 3
                else:
                    dot_cost = (rating - 1) * 2  # Each subsequent dot costs previous rating × 2
                requires_approval = rating > 3

        elif category == 'backgrounds':
            dot_cost = 5  # Each dot costs 5 XP
            requires_approval = rating > 3

        elif category == 'specialties':
            dot_cost = 2  # Each dot costs 2 XP

        # Calculate costs for Changeling/Kinain arts and realms
        elif category == 'powers' and (splat == 'Changeling' or (splat == 'Mortal+' and mortal_type == 'Kinain')):
            # Handle arts
            if subcategory == 'art':
                if rating == 1:
                    dot_cost = 7  # First dot costs 7
                else:
                    dot_cost = (rating - 1) * 4  # Each subsequent dot costs previous rating × 4
                requires_approval = rating > 2
            
            # Handle realms
            elif subcategory == 'realm':
                if rating == 1:
                    dot_cost = 5  # First dot costs 5
                else:
                    dot_cost = (rating - 1) * 3  # Each subsequent dot costs previous rating × 3
                requires_approval = rating > 2

        # Calculate costs for Mage spheres
        elif category == 'powers' and splat == 'Mage' and subcategory == 'sphere':
            is_affinity = character._is_affinity_sphere(stat_name)
            if rating == 1:
                dot_cost = 10  # First dot always costs 10
            else:
                if is_affinity:
                    dot_cost = (rating - 1) * 7  # Previous rating × 7
                else:
                    dot_cost = (rating - 1) * 8  # Previous rating × 8
            requires_approval = rating > 2

        elif category == 'powers':
            # Adjust costs based on splat and power type
            if splat == 'Vampire':
                if subcategory == 'discipline':
                    # Check if it's an in-clan discipline
                    clan = character.db.stats.get('identity', {}).get('lineage', {}).get('Clan', {}).get('perm', '')
                    is_in_clan = _is_discipline_in_clan(stat_name, clan)
                    
                    if rating == 1:
                        dot_cost = 10  # First dot always costs 10
                    else:
                        if is_in_clan:
                            dot_cost = (rating - 1) * 5  # Previous rating × 5
                        else:
                            dot_cost = (rating - 1) * 7  # Previous rating × 7
                    requires_approval = rating > 2

            elif splat == 'Mage':
                # Check if it's an affinity sphere
                is_affinity = character._is_affinity_sphere(stat_name)
                
                if rating == 1:
                    dot_cost = 10  # First dot always costs 10
                else:
                    if is_affinity:
                        dot_cost = (rating - 1) * 7
                    else:
                        dot_cost = (rating - 1) * 8
                
                requires_approval = rating > 2

            # Handle Kinfolk gifts
            elif splat == 'Mortal+' and mortal_type == 'Kinfolk' and subcategory == 'gift':
                # Log information about the gift calculation
                logger.log_info(f"Calculating XP cost for {stat_name} - Kinfolk gift")
                
                # Get the gift details from the database
                gift = Stat.objects.filter(
                    Q(name__iexact=stat_name) | Q(gift_alias__icontains=stat_name),
                    category='powers',
                    stat_type='gift'
                ).first()
                
                if gift:
                    # For Kinfolk, breed is always Homid
                    is_homid = False
                    if gift.shifter_type:
                        allowed_types = gift.shifter_type if isinstance(gift.shifter_type, list) else [gift.shifter_type]
                        is_homid = 'homid' in [t.lower() for t in allowed_types]
                        logger.log_info(f"Gift {stat_name} is homid: {is_homid}")
                        
                    # Check if it's a tribal gift
                    is_tribal = False
                    kinfolk_tribe = character.db.stats.get('identity', {}).get('lineage', {}).get('Tribe', {}).get('perm', '')
                    if gift.tribe and kinfolk_tribe:
                        allowed_tribes = gift.tribe if isinstance(gift.tribe, list) else [gift.tribe]
                        is_tribal = kinfolk_tribe.lower() in [t.lower() for t in allowed_tribes]
                        logger.log_info(f"Gift {stat_name} is tribal ({kinfolk_tribe}): {is_tribal}")
                        
                    # Check if it's a Croatan or Planetary gift
                    is_special = gift.tribe and any(tribe.lower() in ['croatan', 'planetary'] 
                                                  for tribe in (gift.tribe if isinstance(gift.tribe, list) else [gift.tribe]))
                    logger.log_info(f"Gift {stat_name} is special (Croatan/Planetary): {is_special}")
                    
                    # Calculate cost based on gift type
                    if is_homid or is_tribal:
                        dot_cost = rating * 6  # Breed/tribe gifts cost 6 XP per level
                        logger.log_info(f"Gift {stat_name} cost (breed/tribal): {dot_cost}")
                    elif is_special:
                        dot_cost = rating * 14  # Croatan/Planetary gifts cost 14 XP per level
                        logger.log_info(f"Gift {stat_name} cost (special): {dot_cost}")
                    else:
                        dot_cost = rating * 10  # Other gifts cost 10 XP per level
                        logger.log_info(f"Gift {stat_name} cost (other): {dot_cost}")
                    
                    # Level 2 gifts require the Gnosis merit and staff approval
                    if rating > 1:
                        # Check for Gnosis merit
                        gnosis_merit = next((value.get('perm', 0) for merit, value in character.db.stats.get('merits', {}).get('merit', {}).items() 
                                            if merit.lower() == 'gnosis'), 0)
                        if not gnosis_merit:
                            logger.log_info(f"Cannot buy level 2 gift without Gnosis merit")
                            return (0, False)  # Can't buy level 2 gifts without Gnosis merit
                        requires_approval = True  # Level 2 gifts always require staff approval
                else:
                    logger.log_info(f"Gift {stat_name} not found in database")
                    return (0, False)  # Gift not found in database

        total_cost += dot_cost

    return (total_cost, requires_approval)

def validate_xp_purchase(character, stat_name, new_rating, category=None, subcategory=None):
    """
    Validate if a character can purchase a stat increase.
    
    Args:
        character: The character object
        stat_name (str): Name of the stat being increased
        new_rating (int): Target rating
        category (str): Stat category
        subcategory (str): Stat subcategory
        
    Returns:
        tuple: (can_purchase, error_message)
    """
    # Get character's splat
    splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
    if not splat:
        return False, "Character splat not set"

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

        # These paths always require staff approval
        return False, f"{subcategory.title()} paths require staff approval"

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
            
        # Rituals always require staff approval
        return False, f"{discipline_name} rituals require staff approval"

    # Handle pools (Willpower, Rage, Gnosis, Glamour)
    if category == 'pools' and subcategory == 'dual':
        # Get current rating
        current_rating = character.db.stats.get('pools', {}).get('dual', {}).get(stat_name, {}).get('perm', 0)
        
        # Check if new rating is actually an increase
        if new_rating <= current_rating:
            return False, "New rating must be higher than current rating"
            
        # Apply approval thresholds based on pool type
        if stat_name == 'Willpower':
            # Willpower above 5 requires staff approval
            if new_rating > 5:
                return False, "Willpower above 5 requires staff approval"
        elif stat_name == 'Rage':
            # Rage above 5 requires staff approval
            if new_rating > 5:
                return False, "Rage above 5 requires staff approval"
        elif stat_name == 'Glamour':
            # Glamour above 5 requires staff approval
            if new_rating > 5:
                return False, "Glamour above 5 requires staff approval"
        elif stat_name == 'Gnosis':
            # For Shifters, Gnosis is a pool stat
            char_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
            
            # Special check for Kinfolk (they should use the merit instead)
            if splat == 'Mortal+' and char_type == 'Kinfolk':
                return False, "Kinfolk must purchase the Gnosis merit instead of directly increasing Gnosis pool"
                
            # Gnosis above 5 requires staff approval for Shifters
            if new_rating > 5:
                return False, "Gnosis above 5 requires staff approval"
        elif stat_name in ['Arete', 'Enlightenment']:
            # Arete/Enlightenment above 1 requires staff approval
            if new_rating > 1:
                return False, f"{stat_name} above 1 requires staff approval"
                
        return True, ""

    # Handle merits and flaws
    if category == 'merits':
        # Check if it's a valid merit
        merit_found = False
        for merit_type, merits in MERIT_CATEGORIES.items():
            # Try exact match first
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
        return False, "Flaws can only be bought off through staffspend"

    # Validate blessings against the BLESSINGS list
    if category == 'powers' and subcategory == 'blessing':
        if stat_name not in BLESSINGS:
            return False, f"{stat_name} is not a valid blessing"
        # Blessings can be purchased up to rating 2 without approval
        if new_rating > 2:
            return False, "Blessings above rating 2 require staff approval"

    # Validate charms against the CHARMS list
    if category == 'powers' and subcategory == 'charm':
        if stat_name not in CHARMS:
            return False, f"{stat_name} is not a valid charm"
        # Charms can be purchased up to rating 2 without approval
        if new_rating > 0:
            return False, "Charms require staff approval"

    # Get current rating based on category
    if category == 'powers' and subcategory == 'discipline':
        current_rating = character.db.stats.get('powers', {}).get('discipline', {}).get(stat_name, {}).get('perm', 0)
    elif category == 'powers':
        current_rating = character.db.stats.get('powers', {}).get(subcategory, {}).get(stat_name, {}).get('perm', 0)
    else:
        current_rating = character.db.stats.get(category, {}).get(subcategory, {}).get(stat_name, {}).get('perm', 0)

    # Basic validation
    if new_rating <= current_rating:
        return False, "New rating must be higher than current rating"

    # Check auto-approval rules
    if category == 'attributes':
        if new_rating > AUTO_APPROVE['all']['attributes']:
            return False, "Attributes above 3 require staff approval"
    elif category in ['abilities', 'secondary_abilities']:
        if new_rating > AUTO_APPROVE['all']['abilities']:
            return False, "Abilities above 3 require staff approval"
    elif category == 'backgrounds':
        max_rating = AUTO_APPROVE['all']['backgrounds'].get(stat_name, 2)
        if new_rating > max_rating:
            return False, f"Background {stat_name} above {max_rating} requires staff approval"
    elif category == 'powers':
        # Get splat-specific power rules
        power_rules = AUTO_APPROVE.get(splat, {}).get('powers', {})
        max_rating = power_rules.get('max', 2)
        allowed_types = power_rules.get('types', [])
        
        # Special handling for Kinfolk characters and gifts
        char_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
        if splat == 'Mortal+' and char_type == 'Kinfolk' and subcategory == 'gift':
            # Kinfolk can buy gifts up to level 1 without approval
            if new_rating <= 1:
                return True, ""
            else:
                return False, f"Kinfolk can only purchase gifts up to level 1 without staff approval"
        
        if subcategory not in allowed_types:
            return False, f"{subcategory} cannot be purchased with XP"
            
        if new_rating > max_rating:
            return False, f"{subcategory} above {max_rating} requires staff approval"
            
        # Special handling for vampire disciplines
        if splat == 'Vampire' and subcategory == 'discipline':
            if stat_name not in PURCHASABLE_DISCIPLINES:
                return False, f"{stat_name} cannot be purchased with XP"

        if splat == 'Vampire' and subcategory == 'necromancy':
            return False, f"Necromancy paths require staff approval."
            
        if splat == 'Vampire' and subcategory == 'thaumaturgy':
            return False, f"Thaumaturgical paths require staff approval."
    return True, ""

def process_xp_purchase(character, stat_name, new_rating, category, subcategory, reason="", current_rating=None, pre_calculated_cost=None):
    """
    Process an XP purchase for a character.
    
    Args:
        character: The character object
        stat_name (str): Name of the stat being increased
        new_rating (int): Target rating
        category (str): Stat category
        subcategory (str): Stat subcategory
        reason (str): Reason for the purchase
        current_rating (int, optional): Current rating of the stat
        pre_calculated_cost (int, optional): Pre-calculated XP cost
        
    Returns:
        tuple: (success, message)
    """
    try:
        # Calculate cost if not provided
        if pre_calculated_cost is None:
            cost, requires_approval = calculate_xp_cost(
                character, stat_name, new_rating, category, subcategory, current_rating
            )
        else:
            cost = pre_calculated_cost
            requires_approval = False

        if cost == 0:
            return False, "Invalid stat or no increase needed"

        # Check if character has enough XP
        if character.db.xp['current'] < cost:
            return False, f"Not enough XP. Cost: {cost}, Available: {character.db.xp['current']}"

        # Update the stat
        if category == 'secondary_abilities':
            if 'secondary_abilities' not in character.db.stats:
                character.db.stats['secondary_abilities'] = {}
            if subcategory not in character.db.stats['secondary_abilities']:
                character.db.stats['secondary_abilities'][subcategory] = {}
            character.db.stats['secondary_abilities'][subcategory][stat_name] = {
                'perm': new_rating,
                'temp': new_rating
            }
        else:
            character.set_stat(category, subcategory, stat_name, new_rating, temp=False)
            character.set_stat(category, subcategory, stat_name, new_rating, temp=True)

        # Deduct XP
        character.db.xp['current'] -= Decimal(str(cost))
        character.db.xp['spent'] += Decimal(str(cost))

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

        if 'spends' not in character.db.xp:
            character.db.xp['spends'] = []
        character.db.xp['spends'].insert(0, spend_entry)

        return True, f"Successfully increased {stat_name} from {current_rating} to {new_rating} (Cost: {cost} XP)"

    except Exception as e:
        logger.log_err(f"Error processing XP purchase: {str(e)}")
        return False, f"Error: {str(e)}"

def process_xp_spend(character, stat_name, new_rating, category=None, subcategory=None, reason="", is_staff_spend=False):
    """
    Process an XP spend request from start to finish.
    """
    try:
        # Special handling for Thaumaturgy and Necromancy discipline increases
        if category == 'powers' and subcategory == 'discipline' and stat_name in ['Thaumaturgy', 'Necromancy']:
            # Get current discipline rating
            current_rating = character.db.stats.get('powers', {}).get('discipline', {}).get(stat_name, {}).get('perm', 0)
            
            # Calculate discipline cost first
            clan = character.db.stats.get('identity', {}).get('lineage', {}).get('Clan', {}).get('perm', '')
            is_in_clan = _is_discipline_in_clan(stat_name, clan)
            
            # Calculate base discipline cost
            discipline_cost = 0
            for rating in range(current_rating + 1, new_rating + 1):
                if rating == 1:
                    discipline_cost += 10  # First dot always costs 10
                else:
                    if is_in_clan:
                        discipline_cost += (rating - 1) * 5  # Previous rating × 5
                    else:
                        discipline_cost += (rating - 1) * 7  # Previous rating × 7
            
            # Check if character has enough XP
            if character.db.xp['current'] < discipline_cost:
                return False, f"Not enough XP. Cost: {discipline_cost}, Available: {character.db.xp['current']}", discipline_cost
            
            # Process the discipline increase
            success, message = process_xp_purchase(character, stat_name, new_rating, category, subcategory, reason, current_rating, discipline_cost)
            if not success:
                return False, message, discipline_cost
            
            # If this is the first dot AND they have no existing paths, set up the primary path
            path_subcategory = stat_name.lower()
            existing_paths = character.db.stats.get('powers', {}).get(path_subcategory, {})
            
            if current_rating == 0 and not existing_paths:
                # Initialize path structure if needed
                if 'powers' not in character.db.stats:
                    character.db.stats['powers'] = {}
                if path_subcategory not in character.db.stats['powers']:
                    character.db.stats['powers'][path_subcategory] = {}
                
                # Calculate path cost
                path_cost = 5  # First dot in primary path costs 5
                total_cost = discipline_cost + path_cost
                
                # Check if character has enough XP
                if character.db.xp['current'] < total_cost:
                    return False, f"Not enough XP. Cost: {total_cost} (Discipline: {discipline_cost}, Path: {path_cost}), Available: {character.db.xp['current']}", total_cost
                
                # Process the discipline increase
                success, message = process_xp_purchase(character, stat_name, new_rating, category, subcategory, reason, current_rating, discipline_cost)
                if not success:
                    return False, message, total_cost
                
                # Set up default primary path at rating 1
                default_path = 'Path of Blood' if stat_name == 'Thaumaturgy' else 'Sepulchre Path'
                character.db.stats['powers'][path_subcategory][default_path] = {
                    'perm': 1,
                    'temp': 1
                }
                
                # Process the path increase separately
                success, message = process_xp_purchase(character, default_path, 1, 'powers', path_subcategory, f"Initial {default_path}", 0, path_cost)
                if not success:
                    return False, message, total_cost
                
                return True, f"Successfully increased {stat_name} to {new_rating} and set up {default_path} at 1", total_cost
            
            # For subsequent increases, just process the discipline increase
            else:
                # Check if character has enough XP
                if character.db.xp['current'] < discipline_cost:
                    return False, f"Not enough XP. Cost: {discipline_cost}, Available: {character.db.xp['current']}", discipline_cost
                
                # Process the discipline increase
                success, message = process_xp_purchase(character, stat_name, new_rating, category, subcategory, reason, current_rating, discipline_cost)
                if not success:
                    return False, message, discipline_cost
                
                return True, f"Successfully increased {stat_name} to {new_rating}", discipline_cost
                       
        # Special handling for Gnosis - differentiate between Kinfolk (merit) and Shifters (pool)
        if stat_name.lower() == 'gnosis':
            splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            mortal_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
            
            # For Kinfolk, Gnosis should be processed as a merit
            if splat == 'Mortal+' and mortal_type == 'Kinfolk':
                category = 'merits'
                subcategory = 'supernatural'
                logger.log_info(f"Processing Gnosis as a merit for Kinfolk character")
            # For Shifters, Gnosis should be processed as a pool
            elif splat == 'Shifter':
                category = 'pools'
                subcategory = 'dual'
                logger.log_info(f"Processing Gnosis as a pool for Shifter character")
        
        # Get current rating with better logging
        logger.log_info(f"Getting current rating for {stat_name} ({category}/{subcategory})")
        
        # Special handling for secondary abilities - force title case
        if category == 'secondary_abilities':
            stat_name = ' '.join(word.title() for word in stat_name.split())
            logger.log_info(f"Formatted secondary ability name to: {stat_name}")
            current_rating = character.db.stats.get('secondary_abilities', {}).get(subcategory, {}).get(stat_name, {}).get('perm', 0)
            logger.log_info(f"Getting secondary ability rating: {current_rating}")
        elif category == 'powers':
            if subcategory == 'discipline':
                current_rating = character.db.stats.get('powers', {}).get('discipline', {}).get(stat_name, {}).get('perm', 0)
                logger.log_info(f"Getting discipline rating: {current_rating} for {stat_name}")
                
                # Initialize discipline if it doesn't exist
                if 'powers' not in character.db.stats:
                    character.db.stats['powers'] = {}
                if 'discipline' not in character.db.stats['powers']:
                    character.db.stats['powers']['discipline'] = {}
                if stat_name not in character.db.stats['powers']['discipline']:
                    character.db.stats['powers']['discipline'][stat_name] = {'perm': 0, 'temp': 0}
                    current_rating = 0
                    logger.log_info(f"Initialized discipline {stat_name} with rating 0")
            else:
                current_rating = character.db.stats.get('powers', {}).get(subcategory, {}).get(stat_name, {}).get('perm', 0)
                logger.log_info(f"Getting other power rating: {current_rating}")
        elif category in ['merits', 'flaws']:
            current_rating = character.db.stats.get(category, {}).get(subcategory, {}).get(stat_name, {}).get('perm', 0)
            logger.log_info(f"Getting {category} rating: {current_rating}")
        else:
            current_rating = character.db.stats.get(category, {}).get(subcategory, {}).get(stat_name, {}).get('perm', 0)
            logger.log_info(f"Getting general stat rating: {current_rating}")

        # Check if new rating is actually an increase
        if new_rating <= current_rating and not (category == 'flaws' and 'flaw buyoff' in reason.lower()):
            return False, "New rating must be higher than current rating. Reach out to staff if this is in error.", 0

        # Calculate cost
        if category in ['merits', 'flaws']:
            # For flaws being bought off, use current rating to calculate cost
            if category == 'flaws' and 'flaw buyoff' in reason.lower():
                cost = current_rating * 5
            else:
                cost = new_rating * 5
            requires_approval = False
            cost_decimal = Decimal(str(cost))
            logger.log_info(f"Calculating {category} cost: {cost} XP for {stat_name}")
            
            # Validate against MERIT_VALUES/FLAW_VALUES
            if category == 'merits' and stat_name in MERIT_VALUES:
                if new_rating not in MERIT_VALUES[stat_name]:
                    return False, f"Invalid rating for {stat_name}. Valid values are: {MERIT_VALUES[stat_name]}", 0
            elif category == 'flaws' and stat_name in FLAW_VALUES:
                if new_rating not in FLAW_VALUES[stat_name]:
                    return False, f"Invalid rating for {stat_name}. Valid values are: {FLAW_VALUES[stat_name]}", 0
        else:
            # Normal cost calculation
            cost, requires_approval = calculate_xp_cost(
                character, stat_name, new_rating, category, subcategory, current_rating
            )
            cost_decimal = Decimal(str(cost))

        # Check if we have enough XP
        if character.db.xp['current'] < cost_decimal:
            return False, f"Not enough XP. Cost: {cost_decimal}, Available: {character.db.xp['current']}", cost_decimal

        # Log XP state before changes
        logger.log_info(f"Before XP update - Current: {character.db.xp['current']}, Spent: {character.db.xp['spent']}")
        logger.log_info(f"Cost to be deducted: {cost_decimal}")
        # For staff spends on disciplines not in the purchasable list, calculate a cost manually
        if is_staff_spend and category == 'powers' and subcategory == 'discipline' and stat_name not in PURCHASABLE_DISCIPLINES:
            logger.log_info(f"Staff spend on non-purchasable discipline: {stat_name}")
            
            # Set a default cost based on standard discipline progression
            splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            clan = character.db.stats.get('identity', {}).get('lineage', {}).get('Clan', {}).get('perm', '')
            
            # Check if it's an in-clan discipline by looking at clan disciplines
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
            
            if clan in clan_disciplines:
                is_in_clan = stat_name in clan_disciplines[clan]
            else:
                is_in_clan = False
            
            # Calculate cost based on rating
            total_cost = 0
            for rating in range(current_rating + 1, new_rating + 1):
                if rating == 1:
                    dot_cost = 10  # First dot always costs 10
                else:
                    if is_in_clan:
                        dot_cost = (rating - 1) * 5  # Previous rating × 5 for in-clan
                    else:
                        dot_cost = (rating - 1) * 7  # Previous rating × 7 for out-of-clan
                total_cost += dot_cost
            
            cost_decimal = Decimal(str(total_cost))
            requires_approval = False
            logger.log_info(f"Staff spend: calculated cost for {stat_name} to rating {new_rating}: {cost_decimal} XP")

        # Handle zero cost (invalid calculation)
        if cost_decimal == 0 and category not in ['merits', 'flaws']:
            if is_staff_spend and category == 'powers' and subcategory == 'discipline':
                # For staff spends on disciplines, use a default cost formula
                if new_rating == 1:
                    cost = 10  # First dot costs 10
                else:
                    cost = (new_rating - 1) * 6  # Subsequent dots cost previous rating × 6 (average)
                cost_decimal = Decimal(str(cost))
                logger.log_info(f"Staff spend on discipline: Setting default cost to {cost_decimal} XP for {stat_name}")
            elif category == 'powers' and subcategory == 'blessing':
                # Special handling for Blessings
                if stat_name not in BLESSINGS:
                    return False, f"{stat_name} is not a valid blessing", 0
                cost_decimal = Decimal(str(new_rating * 4))  # New Rating x 4 XP
                logger.log_info(f"Blessing cost calculation: {cost_decimal} XP for {stat_name}")
            elif category == 'powers' and subcategory == 'charm':
                # Special handling for Charms
                if stat_name not in CHARMS:
                    return False, f"{stat_name} is not a valid charm", 0
                cost_decimal = Decimal('5')  # Flat 5 XP per charm
                logger.log_info(f"Charm cost calculation: {cost_decimal} XP for {stat_name}")
            else:
                return False, "Cost calculation returned zero. Reach out to staff if this is in error.", 0

        # Staff spends bypass validation
        if not is_staff_spend:
            # Validate the purchase
            can_purchase, error_msg = validate_xp_purchase(
                character, stat_name, new_rating, category, subcategory
            )
            if not can_purchase:
                return False, error_msg, cost_decimal

            if requires_approval:
                return False, "This purchase requires staff approval", cost_decimal

        # Update the stat
        if category == 'secondary_abilities':
            if 'secondary_abilities' not in character.db.stats:
                character.db.stats['secondary_abilities'] = {}
            if subcategory not in character.db.stats['secondary_abilities']:
                character.db.stats['secondary_abilities'][subcategory] = {}
            # Store with title case
            character.db.stats['secondary_abilities'][subcategory][stat_name] = {
                'perm': new_rating,
                'temp': new_rating
            }
        elif category == 'powers':
            # Ensure powers category exists
            if 'powers' not in character.db.stats:
                character.db.stats['powers'] = {}
                
            # Handle different power types
            if subcategory == 'discipline':
                if 'discipline' not in character.db.stats['powers']:
                    character.db.stats['powers']['discipline'] = {}
                character.db.stats['powers']['discipline'][stat_name] = {
                    'perm': new_rating,
                    'temp': new_rating
                }
            elif subcategory == 'thaumaturgy':
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
            elif subcategory == 'necromancy':
                if 'necromancy' not in character.db.stats['powers']:
                    character.db.stats['powers']['necromancy'] = {}
                character.db.stats['powers']['necromancy'][stat_name] = {
                    'perm': new_rating,
                    'temp': new_rating
                }
            elif subcategory == 'blessing':
                if 'blessing' not in character.db.stats['powers']:
                    character.db.stats['powers']['blessing'] = {}
                # Validate against BLESSINGS list
                if stat_name not in BLESSINGS:
                    return False, f"{stat_name} is not a valid blessing", 0
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
            elif subcategory == 'charm':
                if 'charm' not in character.db.stats['powers']:
                    character.db.stats['powers']['charm'] = {}
                # Validate against CHARMS list
                if stat_name not in CHARMS:
                    return False, f"{stat_name} is not a valid charm", 0
                character.db.stats['powers']['charm'][stat_name] = {
                    'perm': new_rating,
                    'temp': new_rating
                }
            elif subcategory == 'special_advantage':
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
                    else:
                        return False, f"Invalid rating for {stat_name}. Valid values are: {advantage_info['valid_values']}", 0
                # Check if it's in COMBAT_SPECIAL_ADVANTAGES
                elif stat_name.lower() in COMBAT_SPECIAL_ADVANTAGES:
                    advantage_info = COMBAT_SPECIAL_ADVANTAGES[stat_name.lower()]
                    if new_rating in advantage_info['valid_values']:
                        character.db.stats['powers']['special_advantage'][stat_name.lower()] = {
                            'perm': new_rating,
                            'temp': new_rating
                        }
                        logger.log_info(f"Updated combat special advantage {stat_name} to {new_rating}")
                    else:
                        return False, f"Invalid rating for {stat_name}. Valid values are: {advantage_info['valid_values']}", 0
                else:
                    return False, f"{stat_name} is not a valid special advantage", 0
                    
                # Handle Ferocity special case - update Rage regardless of which dictionary it's in
                if is_ferocity:
                    # Initialize pools structure if it doesn't exist
                    if 'pools' not in character.db.stats:
                        character.db.stats['pools'] = {}
                    if 'dual' not in character.db.stats['pools']:
                        character.db.stats['pools']['dual'] = {}
                    
                    # Calculate Rage based on Ferocity level
                    rage_value = new_rating // 2
                    
                    # Create Rage pool if it doesn't exist
                    if 'Rage' not in character.db.stats['pools']['dual']:
                        character.db.stats['pools']['dual']['Rage'] = {}
                        
                    # Explicitly set both permanent and temporary values
                    character.db.stats['pools']['dual']['Rage']['perm'] = rage_value
                    character.db.stats['pools']['dual']['Rage']['temp'] = rage_value
                    
                    logger.log_info(f"Set Rage pool to {rage_value} based on Ferocity {new_rating}")
            else:
                if subcategory not in character.db.stats['powers']:
                    character.db.stats['powers'][subcategory] = {}
                character.db.stats['powers'][subcategory][stat_name] = {
                    'perm': new_rating,
                    'temp': new_rating
                }
                logger.log_info(f"Updated power {stat_name} ({subcategory}) to {new_rating}")

        elif category in ['merits', 'flaws']:
            # Ensure category exists
            if category not in character.db.stats:
                character.db.stats[category] = {}
            if subcategory not in character.db.stats[category]:
                character.db.stats[category][subcategory] = {}
                
            # For flaws, check if this is a buyoff
            if category == 'flaws' and 'flaw buyoff' in reason.lower():
                # Remove the flaw
                if stat_name in character.db.stats[category][subcategory]:
                    del character.db.stats[category][subcategory][stat_name]
                    logger.log_info(f"Removed flaw {stat_name} as part of buyoff")
            else:
                # Add or update the merit/flaw
                character.db.stats[category][subcategory][stat_name] = {
                    'perm': new_rating,
                    'temp': new_rating
                }
                logger.log_info(f"Updated {category} {stat_name} to {new_rating}")
                
                # Special case for Kinfolk with Gnosis merit
                splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
                mortal_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
                
                if (category == 'merits' and 
                    stat_name.lower() == 'gnosis' and 
                    splat == 'Mortal+' and 
                    mortal_type == 'Kinfolk'):
                    
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

        elif category == 'pools' and subcategory == 'dual':
            # Handle pool stats (Willpower, Rage, Gnosis)
            # Initialize pools structure if it doesn't exist
            if 'pools' not in character.db.stats:
                character.db.stats['pools'] = {}
            if 'dual' not in character.db.stats['pools']:
                character.db.stats['pools']['dual'] = {}
            
            # Create stat if it doesn't exist
            if stat_name not in character.db.stats['pools']['dual']:
                character.db.stats['pools']['dual'][stat_name] = {}
            
            # Set both permanent and temporary values
            character.db.stats['pools']['dual'][stat_name]['perm'] = new_rating
            character.db.stats['pools']['dual'][stat_name]['temp'] = new_rating
            
            logger.log_info(f"Updated pool stat {stat_name} to {new_rating}")
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
                'staff_name': reason.replace('Staff Spend: ', '') if is_staff_spend else None,
                'timestamp': datetime.now().isoformat()
            }

            if 'spends' not in character.db.xp:
                character.db.xp['spends'] = []
            character.db.xp['spends'].insert(0, spend_entry)

            # Final verification
            logger.log_info(f"Final XP state - Current: {new_current}, Spent: {new_spent}")
            return True, f"Successfully increased {stat_name} from {current_rating} to {new_rating} (Cost: {cost_decimal} XP)", cost_decimal

        except Exception as e:
            logger.log_err(f"Error during XP deduction: {str(e)}")
            return False, f"Error processing XP deduction: {str(e)}", cost_decimal

    except Exception as e:
        logger.log_err(f"Error processing XP spend: {str(e)}")
        return False, f"Error: {str(e)}", 0

def get_power_type(stat_name):
    """Determine power type from name."""
    # Get the stat from the database
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
            return False, "Invalid stat or no increase needed"

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

    # Convert to title case for comparison
    stat_name = stat_name.title()

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
    
def calculate_gift_cost(character, gift_name, new_rating, current_rating):
    """Calculate the XP cost for a gift purchase."""
    try:
        logger.log_info(f"Calculating gift cost for {gift_name} {new_rating}")
        
        # Get character's splat and type
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        char_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
        logger.log_info(f"Character splat: {splat}, type: {char_type}")
        
        # Find the gift in the database
        gift = Stat.objects.filter(
            Q(name__iexact=gift_name) | Q(gift_alias__icontains=gift_name),
            category='powers',
            stat_type='gift'
        ).first()
        
        if not gift:
            logger.log_info(f"Gift {gift_name} not found in database")
            return 0
            
        total_cost = 0
        
        # Calculate cost based on character type
        if splat == 'Mortal+' and char_type == 'Kinfolk':
            logger.log_info("Processing Kinfolk gift cost")
            # Check if it's a breed gift (homid) or tribal gift
            is_homid = False
            is_tribal = False
            
            if gift.shifter_type:
                is_homid = 'homid' in [t.lower() for t in (gift.shifter_type if isinstance(gift.shifter_type, list) else [gift.shifter_type])]
                
            if gift.tribe:
                kinfolk_tribe = character.db.stats.get('identity', {}).get('lineage', {}).get('Tribe', {}).get('perm', '')
                if kinfolk_tribe:
                    allowed_tribes = gift.tribe if isinstance(gift.tribe, list) else [gift.tribe]
                    is_tribal = kinfolk_tribe.lower() in [t.lower() for t in allowed_tribes]
            
            logger.log_info(f"Kinfolk gift checks - Homid: {is_homid}, Tribal: {is_tribal}")
            
            if is_homid or is_tribal:
                total_cost = new_rating * 6  # Breed/Tribe gifts
            else:
                total_cost = new_rating * 10  # Other gifts
                
        elif splat == 'Shifter':
            logger.log_info("Processing Shifter gift cost")
            # Get character's breed, auspice, and tribe
            breed = character.db.stats.get('identity', {}).get('lineage', {}).get('Breed', {}).get('perm', '')
            auspice = character.db.stats.get('identity', {}).get('lineage', {}).get('Auspice', {}).get('perm', '')
            tribe = character.db.stats.get('identity', {}).get('lineage', {}).get('Tribe', {}).get('perm', '')
            logger.log_info(f"Shifter details - Breed: {breed}, Auspice: {auspice}, Tribe: {tribe}")
            
            # Check gift type
            is_breed_gift = False
            is_auspice_gift = False
            is_tribe_gift = False
            is_special = False
            
            if gift.shifter_type:
                is_breed_gift = breed and breed.lower() in [t.lower() for t in (gift.shifter_type if isinstance(gift.shifter_type, list) else [gift.shifter_type])]
                
            if gift.auspice:
                is_auspice_gift = auspice and auspice.lower() in [a.lower() for a in (gift.auspice if isinstance(gift.auspice, list) else [gift.auspice])]
                
            if gift.tribe:
                tribes = gift.tribe if isinstance(gift.tribe, list) else [gift.tribe]
                is_tribe_gift = tribe and tribe.lower() in [t.lower() for t in tribes]
                is_special = any(t.lower() in ['croatan', 'planetary'] for t in tribes)
            
            logger.log_info(f"Gift type checks - Breed: {is_breed_gift}, Auspice: {is_auspice_gift}, Tribe: {is_tribe_gift}, Special: {is_special}")
            
            if is_special:
                total_cost = new_rating * 7  # Croatan/Planetary gifts
            elif is_breed_gift or is_auspice_gift or is_tribe_gift:
                total_cost = new_rating * 3  # Breed/Auspice/Tribe gifts
            else:
                total_cost = new_rating * 5  # Other gifts
        
        logger.log_info(f"Final gift cost: {total_cost}")
        return total_cost
        
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
