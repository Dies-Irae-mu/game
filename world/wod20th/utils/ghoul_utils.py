"""
Utility functions for ghouls in World of Darkness 20th Anniversary Edition.
"""

def calculate_discipline_cost(current_rating: int, new_rating: int, is_family: bool = True) -> int:
    """
    Calculate XP cost for Ghoul disciplines.
    Cost is 20 XP then Current Rating x 15 XP (family) or x 25 XP (non-family).
    
    Args:
        current_rating: Current rating of the discipline
        new_rating: Desired new rating
        is_family: Whether the discipline is a family/clan discipline
        
    Returns:
        int: Total XP cost
        
    Example:
        Family/Clan: 20 then 15, 30, 45, 60 XP
        Non-Family/Clan: 20 then 25, 50, 75, 100 XP
    """
    total_cost = 0
    for rating in range(current_rating + 1, new_rating + 1):
        if rating == 1:
            total_cost += 20  # First dot costs 20xp for ghouls
        else:
            multiplier = 15 if is_family else 25
            total_cost += rating * multiplier  # Current rating × multiplier
    return total_cost

def is_family_discipline(character, discipline: str) -> bool:
    """
    Check if a discipline is a family discipline for a ghoul.
    
    Args:
        character: The character object
        discipline: The discipline name to check
        
    Returns:
        bool: True if the discipline is a family discipline
    """
    # Get the character's family/clan from their stats
    family = character.db.stats.get('identity', {}).get('lineage', {}).get('Clan', {}).get('perm', '')
    
    # Get family disciplines based on the family/clan
    family_discs = get_family_disciplines(family)
    
    return discipline in family_discs
    
def get_family_disciplines(family: str) -> list:
    """
    Get the list of family disciplines for a given family/clan.
    
    Args:
        family: The name of the family/clan
        
    Returns:
        list: List of family disciplines
    """
    # Define family disciplines mapping
    family_disciplines = {
        'Assamite': ['Celerity', 'Obfuscate', 'Quietus'],
        'Brujah': ['Celerity', 'Potence', 'Presence'],
        'Followers of Set': ['Obfuscate', 'Presence', 'Serpentis'],
        'Gangrel': ['Animalism', 'Fortitude', 'Protean'],
        'Giovanni': ['Dominate', 'Necromancy', 'Potence'],
        'Lasombra': ['Dominate', 'Obtenebration', 'Potence'],
        'Malkavian': ['Auspex', 'Dementation', 'Obfuscate'],
        'Nosferatu': ['Animalism', 'Obfuscate', 'Potence'],
        'Ravnos': ['Animalism', 'Chimerstry', 'Fortitude'],
        'Toreador': ['Auspex', 'Celerity', 'Presence'],
        'Tremere': ['Auspex', 'Dominate', 'Thaumaturgy'],
        'Tzimisce': ['Animalism', 'Auspex', 'Vicissitude'],
        'Ventrue': ['Dominate', 'Fortitude', 'Presence'],
    }
    
    return family_disciplines.get(family, []) 