"""
XP cost calculation functions for World of Darkness 20th Anniversary Edition.
"""
from typing import Optional
from . import ghoul_utils

def calculate_attribute_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for attributes.
    Cost is Current Rating x 4 XP, with first dot free and double cost from 1 to 2.
    
    Args:
        current_rating (int): Current attribute rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        First dot is free, 8 (1->2), 8 (2->3), 12 (3->4), 16 (4->5) XP
    """
    total_cost = 0
    for rating in range(current_rating, new_rating):
        if rating == 1:  # Going from 1 to 2 is special case
            total_cost += 8
        else:
            total_cost += rating * 4  # Current rating x 4
    return total_cost

def calculate_ability_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for abilities (both Abilities and Secondary Abilities).
    Cost is 3 XP then Current Rating x 2 XP.
    
    Args:
        current_rating (int): Current ability rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        3 XP then 2, 4, 6, 8 XP
    """
    total_cost = 0
    if current_rating == 0:
        total_cost = 3  # Initial cost
        current_rating = 1
    
    for rating in range(current_rating, new_rating):
        total_cost += rating * 2  # Current rating x 2
    return total_cost

def calculate_discipline_cost(current_rating: int, new_rating: int, discipline_type: str = 'in_clan') -> int:
    """
    Calculate XP cost for Vampire disciplines.
    
    Args:
        current_rating (int): Current discipline rating
        new_rating (int): Desired new rating
        discipline_type (str): One of 'in_clan', 'out_clan', or 'caitiff'
        
    Returns:
        int: Total XP cost
        
    Example:
        In-Clan: 10 for first dot, then 5 (1->2), 10 (2->3), 15 (3->4), 20 (4->5) XP
        Out-of-Clan: 10 for first dot, then 7 (1->2), 14 (2->3), 21 (3->4), 28 (4->5) XP
        Caitiff: 10 for first dot, then 6 (1->2), 12 (2->3), 18 (3->4), 24 (4->5) XP
    """
    total_cost = 0
    if current_rating == 0:
        total_cost = 10  # Initial cost for first dot
        current_rating = 1
    
    multiplier = {
        'in_clan': 5,
        'out_clan': 7,
        'caitiff': 6
    }.get(discipline_type, 7)  # Default to out-clan cost
    
    for rating in range(current_rating, new_rating):
        total_cost += rating * multiplier
    return total_cost

def calculate_thaumaturgy_path_cost(current_rating: int, new_rating: int, is_secondary: bool = True) -> int:
    """
    Calculate XP cost for Thaumaturgy/Necromancy paths.
    Secondary paths cost New Path 7 then Current x 4 XP.
    
    Args:
        current_rating (int): Current path rating
        new_rating (int): Desired new rating
        is_secondary (bool): Whether this is a secondary path
        
    Returns:
        int: Total XP cost
        
    Example:
        7 then 4, 8, 12, 16 XP
    """
    if not is_secondary:
        return calculate_discipline_cost(current_rating, new_rating, 'in_clan')
    
    total_cost = 0
    if current_rating == 0:
        total_cost = 7  # Initial cost for secondary path
        current_rating = 1
    
    for rating in range(current_rating, new_rating):
        total_cost += rating * 4  # Current rating x 4
    return total_cost

def calculate_ritual_cost(ritual_level: int, is_in_clan: bool = True) -> int:
    """
    Calculate XP cost for Thaumaturgy/Necromancy rituals.
    
    Args:
        ritual_level (int): Level of the ritual
        is_in_clan (bool): Whether this is in-clan
        
    Returns:
        int: XP cost
        
    Example:
        In-Clan: 2, 4, 6, 8, 10 XP
        Out-of-Clan: 3, 6, 9, 12, 15 XP
    """
    # Rituals use flat costs based on level
    multiplier = 2 if is_in_clan else 3
    return ritual_level * multiplier

def calculate_background_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for backgrounds.
    Cost is Rating x 5 XP.
    
    Args:
        current_rating (int): Current background rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        5, 10, 15, 20, 25 XP
    """
    # For backgrounds, use absolute cost (non-iterative)
    # For example, going from 0 to 3 costs 15 XP (5 * 3), not 30 XP (5 + 10 + 15)
    return (new_rating - current_rating) * 5

def calculate_willpower_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Willpower.
    Cost is Current Rating x 2 XP.
    
    Args:
        current_rating (int): Current willpower rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        2, 4, 6, 8, 10 XP
    """
    total_cost = 0
    for rating in range(current_rating, new_rating):
        total_cost += rating * 2  # Current rating x 2
    return total_cost

def calculate_merit_flaw_cost(rating: int) -> int:
    """
    Calculate XP cost for merits/flaws.
    Cost is Rating x 5 XP.
    
    Args:
        rating (int): Merit/Flaw rating
        
    Returns:
        int: XP cost
    """
    return abs(rating) * 5

def calculate_specialty_cost() -> int:
    """
    Calculate XP cost for extra specialties.
    Cost is 4 XP per specialty past your free one.
    
    Returns:
        int: XP cost (always 4)
    """
    return 4

def calculate_virtue_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for virtues.
    Cost is Current Rating x 2 XP.
    
    Args:
        current_rating (int): Current virtue rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        2, 4, 6, 8, 10 XP
    """
    total_cost = 0
    for rating in range(current_rating, new_rating):
        total_cost += rating * 2  # Current rating x 2
    return total_cost

def calculate_path_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Path rating.
    Cost is Current Rating x 2 XP.
    
    Args:
        current_rating (int): Current path rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        If it's 5 and you want 6, it's 10 XP
    """
    total_cost = 0
    for rating in range(current_rating, new_rating):
        total_cost += rating * 2
    return total_cost

def calculate_gift_cost(current_rating: int, new_rating: int, gift_type: str = 'breed_tribe_auspice') -> int:
    """
    Calculate XP cost for Werewolf gifts.
    
    Args:
        current_rating (int): Current gift rating
        new_rating (int): Desired new rating
        gift_type (str): One of 'breed_tribe_auspice', 'outside', or 'special'
        
    Returns:
        int: Total XP cost
        
    Example:
        Breed/Tribe/Auspice: 3, 6, 9, 12, 15 XP
        Outside: 5, 10, 15, 20, 25 XP
        Special (Croatan, Planetary, Ju-Fu): 7, 14, 21, 28, 35 XP
    """
    multiplier = {
        'breed_tribe_auspice': 3,
        'outside': 5,
        'special': 7
    }.get(gift_type, 3)
    
    # Gifts use flat costs based on new rating (non-iterative)
    return new_rating * multiplier

def calculate_rage_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Rage.
    Cost is Current Rating XP.
    
    Args:
        current_rating (int): Current Rage rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9 XP
    """
    total_cost = 0
    for rating in range(current_rating, new_rating):
        total_cost += rating
    return total_cost

def calculate_gnosis_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Gnosis.
    Cost is Current Rating * 2 XP.
    
    Args:
        current_rating (int): Current Gnosis rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        0, 2, 4, 6, 8, 10, 12, 14, 16, 18 XP
    """
    total_cost = 0
    for rating in range(current_rating, new_rating):
        total_cost += rating * 2
    return total_cost

def calculate_rite_cost(rite_level: int, is_minor: bool = False) -> int:
    """
    Calculate XP cost for Rites.
    
    Args:
        rite_level (int): Level of the rite
        is_minor (bool): Whether this is a minor rite
        
    Returns:
        int: XP cost
        
    Example:
        Standard: Rating * 3 XP
        Minor (level 0): 1.5 XP
    """
    # Rites use flat costs based on level
    multiplier = 1.5 if is_minor else 3
    return int(rite_level * multiplier)

def calculate_sphere_cost(current_rating: int, new_rating: int, is_affinity: bool = False) -> int:
    """
    Calculate XP cost for Mage spheres.
    
    Args:
        current_rating (int): Current sphere rating
        new_rating (int): Desired new rating
        is_affinity (bool): Whether this is an affinity sphere
        
    Returns:
        int: Total XP cost
        
    Example:
        First dot always costs 10, then:
        Affinity: 7 (1->2), 14 (2->3), 21 (3->4), 28 (4->5) XP
        Non-Affinity: 8 (1->2), 16 (2->3), 24 (3->4), 32 (4->5) XP
    """
    total_cost = 0
    if current_rating == 0:
        total_cost = 10  # Initial cost for first dot
        current_rating = 1
    
    multiplier = 7 if is_affinity else 8
    for rating in range(current_rating, new_rating):
        total_cost += rating * multiplier
    return total_cost

def calculate_arete_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Arete.
    Cost is Current Rating * 8 XP.
    
    Args:
        current_rating (int): Current Arete rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        0 (free), 8 (2), 16 (3), 24 (4), 32 (5) XP
    """
    total_cost = 0
    for rating in range(current_rating, new_rating):
        total_cost += rating * 8
    return total_cost

def calculate_avatar_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Avatar.
    Cost is Current Rating * 7 XP.
    
    Args:
        current_rating (int): Current Avatar rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        0 (free), 7 (2), 14 (3), 21 (4), 28 (5) XP
    """
    total_cost = 0
    for rating in range(current_rating, new_rating):
        total_cost += rating * 7
    return total_cost

def calculate_art_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Changeling arts.
    Cost is 7 XP then Current Rating * 4 XP.
    
    Args:
        current_rating (int): Current art rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        7 for first dot, then 4 (1->2), 8 (2->3), 12 (3->4), 16 (4->5) XP
    """
    total_cost = 0
    if current_rating == 0:
        total_cost = 7  # Initial cost for first dot
        current_rating = 1
    
    for rating in range(current_rating, new_rating):
        total_cost += rating * 4
    return total_cost

def calculate_realm_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Changeling realms.
    Cost is 5 XP then Current Rating * 3 XP.
    
    Args:
        current_rating (int): Current realm rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        5 for first dot, then 3 (1->2), 6 (2->3), 9 (3->4), 12 (4->5) XP
    """
    total_cost = 0
    if current_rating == 0:
        total_cost = 5  # Initial cost for first dot
        current_rating = 1
    
    for rating in range(current_rating, new_rating):
        total_cost += rating * 3
    return total_cost

def calculate_glamour_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Glamour.
    Cost is Current Rating * 3 XP.
    
    Args:
        current_rating (int): Current Glamour rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        0, 3, 6, 9, 12, 15, 18, 21, 24, 26 XP
    """
    total_cost = 0
    for rating in range(current_rating + 1, new_rating + 1):
        total_cost += rating * 3
    return total_cost

def calculate_special_advantage_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Companion special advantages.
    Cost is 1 XP Per Dot.
    
    Args:
        current_rating (int): Current advantage rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        1, 1, 1, 1, 1 XP
    """
    return new_rating - current_rating

def calculate_charm_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Companion charms.
    Cost is 5 XP per level.
    
    Args:
        current_rating (int): Current charm rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        5, 10, 15, etc. XP
    """
    return (new_rating - current_rating) * 5

def calculate_sorcerous_path_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Sorcerous paths.
    Cost is New Rating x 7 XP.
    
    Args:
        current_rating (int): Current path rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        7XP for rating 1, 14XP for rating 2, 21XP for rating 3, etc.
    """
    # Sorcery uses new_rating for calculation (non-standard)
    return new_rating * 7

def calculate_arcanos_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Wraithly Arcanoi.
    New Arcanos 7
    Arcanos Current rating x3
    """
    total_cost = 0
    if current_rating == 0: 
        total_cost = 7  # Initial cost
        current_rating = 1
    
    for rating in range(current_rating, new_rating):
        total_cost += rating * 3
    return total_cost

def calculate_faith_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for faith paths.
    Cost is New Rating x 7 XP.
    
    Args:
        current_rating (int): Current path rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        7XP for rating 1, 14XP for rating 2, 21XP for rating 3, etc.
    """
    # Faith uses new_rating for calculation (non-standard)
    return new_rating * 7

def calculate_sorcerous_ritual_cost(ritual_level: int) -> int:
    """
    Calculate XP cost for Sorcerous rituals.
    Cost is Rating of Ritual.
    
    Args:
        ritual_level (int): Level of the ritual
        
    Returns:
        int: XP cost
        
    Example:
        1 XP for level 1, 2 XP for level 2, etc.
    """
    # Rituals use flat costs based on level
    return ritual_level

def calculate_numina_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Numina.
    Cost is New Rating x 7 XP.
    
    Args:
        current_rating (int): Current numina rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        7XP for rating 1, 14XP for rating 2, 21XP for rating 3, etc.
    """
    # Numina uses new_rating for calculation (non-standard)
    return new_rating * 7

def calculate_blessing_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Possessed blessings.
    Cost is Rating x 4 XP.
    
    Args:
        current_rating (int): Current blessing rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        4XP then 8, 12, 16, 20
    """
    total_cost = 0
    for rating in range(current_rating, new_rating):
        total_cost += rating * 4
    return total_cost

def calculate_possessed_gift_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Possessed gifts.
    Cost is Rating x 7 XP.
    
    Args:
        current_rating (int): Current gift rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        7XP then 14, 21, 28, 35 XP
    """
    total_cost = 0
    for rating in range(current_rating, new_rating):
        total_cost += rating * 7
    return total_cost

def calculate_kinain_art_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Kinain arts.
    Cost is 3 XP then Current Rating * 4 XP.
    
    Args:
        current_rating (int): Current art rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        3 for first dot, then 4 (1->2), 8 (2->3), 12 (3->4), 16 (4->5) XP
    """
    total_cost = 0
    if current_rating == 0:
        total_cost = 3  # Initial cost for first dot
        current_rating = 1
    
    for rating in range(current_rating, new_rating):
        total_cost += rating * 4
    return total_cost

def calculate_kinain_realm_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for Kinain realms.
    Cost is 5 XP then Current Rating * 3 XP.
    
    Args:
        current_rating (int): Current realm rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        5 for first dot, then 3 (1->2), 6 (2->3), 9 (3->4), 12 (4->5) XP
    """
    total_cost = 0
    if current_rating == 0:
        total_cost = 5  # Initial cost for first dot
        current_rating = 1
    
    for rating in range(current_rating, new_rating):
        total_cost += rating * 3
    return total_cost

def calculate_kinfolk_gift_cost(current_rating: int, new_rating: int, gift_type: str = 'breed_tribe') -> int:
    """
    Calculate XP cost for Kinfolk gifts.
    
    Args:
        current_rating (int): Current gift rating
        new_rating (int): Desired new rating
        gift_type (str): One of 'breed_tribe', 'outside', or 'special'
        
    Returns:
        int: Total XP cost
        
    Example:
        Breed/Tribe: 6, 12 XP
        Outside: 10, 20 XP
        Special (Croatan, Planetary, Ju-Fu): 14, 28 XP
    """
    multiplier = {
        'breed_tribe': 6,
        'outside': 10,
        'special': 14
    }.get(gift_type, 6)
    
    total_cost = 0
    for rating in range(current_rating, new_rating):
        total_cost += rating * multiplier
    return total_cost

def calculate_ghoul_discipline_cost(current_rating: int, new_rating: int, is_clan: bool = True) -> int:
    """
    Calculate XP cost for Ghoul disciplines.
    
    Args:
        current_rating (int): Current discipline rating
        new_rating (int): Desired new rating
        is_clan (bool): Whether this is a clan/family discipline
        
    Returns:
        int: Total XP cost
        
    Example:
        Clan/Family: 20 for first dot, then 15 (1->2), 30 (2->3), 45 (3->4), 60 (4->5) XP
        Out of Clan/Family: 20 for first dot, then 25 (1->2), 50 (2->3), 75 (3->4), 100 (4->5) XP
    """
    total_cost = 0
    if current_rating == 0:
        total_cost = 20  # Initial cost for first dot
        current_rating = 1
    
    multiplier = 15 if is_clan else 25
    for rating in range(current_rating, new_rating):
        total_cost += rating * multiplier
    return total_cost

def calculate_merit_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for merits.
    Cost is 5 XP per dot, based on absolute rating.
    
    Args:
        current_rating (int): Current merit rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        Dark Fate (5) costs 25 XP to remove
    """
    # For merits, use absolute cost (non-iterative)
    return abs(new_rating - current_rating) * 5

def calculate_flaw_cost(current_rating: int, new_rating: int) -> int:
    """
    Calculate XP cost for flaws.
    Cost is 5 XP per dot, based on absolute rating.
    
    Args:
        current_rating (int): Current flaw rating
        new_rating (int): Desired new rating
        
    Returns:
        int: Total XP cost
        
    Example:
        Dark Fate (5) costs 25 XP to remove
    """
    # For flaws, use absolute cost (non-iterative)
    return abs(new_rating - current_rating) * 5 