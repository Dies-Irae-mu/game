"""
Utility functions for handling virtue calculations across different character types.
"""
from typing import Dict, Tuple

# Mapping of paths to their associated virtues
PATH_VIRTUES = {
    # Mortal/Mortal+ and default vampire path
    'Humanity': ('Conscience', 'Self-Control'),
    
    # Vampire-specific paths
    'Night': ('Conviction', 'Instinct'),
    'Beast': ('Conviction', 'Instinct'),
    'Harmony': ('Conscience', 'Instinct'),
    'Evil Revelations': ('Conviction', 'Self-Control'),
    'Self-Focus': ('Conviction', 'Instinct'),
    'Scorched Heart': ('Conviction', 'Self-Control'),
    'Entelechy': ('Conviction', 'Self-Control'),
    'Sharia El-Sama': ('Conscience', 'Self-Control'),
    'Asakku': ('Conviction', 'Instinct'),
    'Death and the Soul': ('Conviction', 'Self-Control'),
    'Honorable Accord': ('Conscience', 'Self-Control'),
    'Feral Heart': ('Conviction', 'Instinct'),
    'Orion': ('Conviction', 'Instinct'),
    'Power and the Inner Voice': ('Conviction', 'Instinct'),
    'Lilith': ('Conviction', 'Instinct'),
    'Caine': ('Conviction', 'Instinct'),
    'Cathari': ('Conviction', 'Instinct'),
    'Redemption': ('Conscience', 'Self-Control'),
    'Metamorphosis': ('Conviction', 'Instinct'),
    'Bones': ('Conviction', 'Self-Control'),
    'Typhon': ('Conviction', 'Self-Control'),
    'Paradox': ('Conviction', 'Self-Control'),
    'Blood': ('Conviction', 'Self-Control'),
    'Hive': ('Conviction', 'Instinct')
}

def calculate_willpower(character):
    """
    Calculate Willpower based on virtues.
    
    This is used by both Mortals/Mortal+ and Vampires:
    - Mortals/Mortal+ always use Conscience + Courage
    - Vampires use either Conscience + Courage (for Humanity)
      or Conviction + Courage (for other paths)
    """
    try:
        # Get the character's virtues
        virtues = character.db.stats.get('virtues', {}).get('moral', {})
        
        # Get Courage value (common to all paths)
        courage = virtues.get('Courage', {}).get('perm', 0)
        
        # Get the character's splat
        splat = character.get_stat('identity', 'personal', 'Splat')
        
        # For Mortals and Mortal+, always use Conscience
        if splat in ['Mortal', 'Mortal+']:
            conscience = virtues.get('Conscience', {}).get('perm', 0)
            willpower = courage + conscience
        else:
            # For Vampires, check the path
            enlightenment = character.get_stat('identity', 'personal', 'Enlightenment')
            
            if enlightenment and enlightenment != 'Humanity':
                # For most non-Humanity paths
                conviction = virtues.get('Conviction', {}).get('perm', 0)
                willpower = courage + conviction
            else:
                # For Humanity and paths using Conscience
                conscience = virtues.get('Conscience', {}).get('perm', 0)
                willpower = courage + conscience
            
        return willpower if willpower > 0 else 1
        
    except (AttributeError, KeyError):
        return 1

def calculate_path(character):
    """Calculate a character's Path rating based on their virtues."""
    # Debug output at start of function
    
    # Get character's splat
    splat = character.get_stat('other', 'splat', 'Splat', temp=False)
    
    # Get character's virtues
    virtues = character.db.stats.get('virtues', {}).get('moral', {})
    
    # For Mortals and Mortal+, use Conscience + Self-Control
    if splat in ['Mortal', 'Mortal+']:
        conscience = virtues.get('Conscience', {}).get('perm', 0)
        self_control = virtues.get('Self-Control', {}).get('perm', 0)
        path_rating = conscience + self_control
        return path_rating
    
    # For Vampires, check Path of Enlightenment
    elif splat == 'Vampire':
        path = character.get_stat('identity', 'personal', 'Path of Enlightenment', temp=False)
        
        # Get the appropriate virtues based on the path
        path_virtues = PATH_VIRTUES.get(path, PATH_VIRTUES['Humanity'])
        
        # Calculate path rating
        virtue1 = virtues.get(path_virtues[0], {}).get('perm', 0)
        virtue2 = virtues.get(path_virtues[1], {}).get('perm', 0)
        path_rating = virtue1 + virtue2
        return path_rating
    
    # For other splats, return None
    return None