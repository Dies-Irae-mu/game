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
        if splat in ['Mortal', 'Mortal Plus']:
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
    """
    Calculate path rating based on virtues.
    
    This is used by both Mortals/Mortal+ and Vampires:
    - Mortals/Mortal+ always use Humanity (Conscience + Self-Control)
    - Vampires use either Humanity or another path with its associated virtues
    """
    # Get the character's splat
    splat = character.get_stat('other', 'splat', 'Splat', temp=False)
    virtues = character.db.stats.get('virtues', {}).get('moral', {})

    # For Mortals and Mortal+, always use Humanity virtues
    if splat in ['Mortal', 'Mortal Plus']:
        virtue1, virtue2 = PATH_VIRTUES['Humanity']
    else:
        # For Vampires, check their path
        enlightenment = character.get_stat('identity', 'personal', 'Path of Enlightenment', temp=False)
        if not enlightenment or enlightenment not in PATH_VIRTUES:
            # Default to Humanity if path not recognized
            virtue1, virtue2 = PATH_VIRTUES['Humanity']
        else:
            virtue1, virtue2 = PATH_VIRTUES[enlightenment]

    # Get the values for both virtues, defaulting to 0 if not found
    value1 = virtues.get(virtue1, {}).get('perm', 0)
    value2 = virtues.get(virtue2, {}).get('perm', 0)

    # Debug output
    #character.msg(f"|wDEBUG: Path calculation - {virtue1}={value1} + {virtue2}={value2} = {value1 + value2}|n")

    # Simply add the two values together
    return value1 + value2