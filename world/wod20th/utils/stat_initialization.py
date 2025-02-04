"""
Functions for initializing basic stats in the database.
"""
from world.wod20th.models import Stat
from world.wod20th.sheet_defaults import ATTRIBUTES, ABILITIES, ADVANTAGES
from typing import List, Tuple
from django.db.models import Q

def find_similar_stats(stat_name: str) -> List[str]:
    """Find similar stat names in the database."""
    # Convert to lowercase for case-insensitive comparison
    stat_name_lower = stat_name.lower()
    
    # Get all stats
    all_stats = Stat.objects.all()
    
    # Find similar stats using basic string matching
    similar_stats = []
    for stat in all_stats:
        # Exact match ignoring case
        if stat.name.lower() == stat_name_lower:
            similar_stats.append(stat.name)
            continue
            
        # Contains the search term
        if stat_name_lower in stat.name.lower():
            similar_stats.append(stat.name)
            continue
            
        # Simple Levenshtein distance (for typos)
        if len(stat_name) > 3:  # Only for longer names to avoid false positives
            distance = 0
            shorter = stat_name_lower if len(stat_name_lower) < len(stat.name.lower()) else stat.name.lower()
            longer = stat_name_lower if len(stat_name_lower) >= len(stat.name.lower()) else stat.name.lower()
            
            for i in range(len(shorter)):
                if shorter[i] != longer[i]:
                    distance += 1
            
            if distance <= 2:  # Allow up to 2 character differences
                similar_stats.append(stat.name)
    
    return similar_stats

def check_stat_exists(stat_name: str, category: str = None, stat_type: str = None) -> Tuple[bool, List[str]]:
    """
    Check if a stat exists in the database.
    Returns (exists, similar_stats) tuple.
    """
    # Build query
    query = Q(name__iexact=stat_name)
    if category:
        query &= Q(category__iexact=category)
    if stat_type:
        query &= Q(stat_type__iexact=stat_type)
    
    # Check if stat exists
    exists = Stat.objects.filter(query).exists()
    
    # Find similar stats if it doesn't exist
    similar_stats = find_similar_stats(stat_name) if not exists else []
    
    return exists, similar_stats

def initialize_basic_stats():
    """Initialize basic stats in the database."""
    # Initialize backgrounds first
    from world.wod20th.utils.background_initialization import initialize_backgrounds
    initialize_backgrounds()

    # Initialize Attributes
    for attr_name in ATTRIBUTES:
        exists, similar_stats = check_stat_exists(attr_name, 'attributes', 'attribute')
        if not exists:
            suggestions = f"Did you mean: {', '.join(similar_stats)}" if similar_stats else "No similar stats found."
            print(f"Error: Attribute '{attr_name}' doesn't exist in the database. {suggestions}")
            continue

    # Initialize Abilities
    for ability_category, abilities in ABILITIES.items():
        for ability_name in abilities:
            exists, similar_stats = check_stat_exists(ability_name, 'abilities', ability_category.lower())
            if not exists:
                suggestions = f"Did you mean: {', '.join(similar_stats)}" if similar_stats else "No similar stats found."
                print(f"Error: Ability '{ability_name}' doesn't exist in the database. {suggestions}")
                continue

    # Initialize Advantages
    for advantage_category, advantages in ADVANTAGES.items():
        if isinstance(advantages, dict):
            for advantage_name, advantage_value in advantages.items():
                exists, similar_stats = check_stat_exists(advantage_name, 'advantages', advantage_category.lower())
                if not exists:
                    suggestions = f"Did you mean: {', '.join(similar_stats)}" if similar_stats else "No similar stats found."
                    print(f"Error: Advantage '{advantage_name}' doesn't exist in the database. {suggestions}")
                    continue
        else:
            # Handle non-dict advantages (like Willpower)
            exists, similar_stats = check_stat_exists(advantage_category, 'advantages', 'advantage')
            if not exists:
                suggestions = f"Did you mean: {', '.join(similar_stats)}" if similar_stats else "No similar stats found."
                print(f"Error: Advantage '{advantage_category}' doesn't exist in the database. {suggestions}")
                continue

    print("Basic stats check completed.") 