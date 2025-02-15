"""
Utility functions for handling Mortal-specific character initialization and updates.
"""
from world.wod20th.utils.banality import get_default_banality
from typing import Dict, List, Tuple

def initialize_mortal_stats(character):
    """Initialize specific stats for a mortal character."""
    # Initialize basic stats structure
    if 'identity' not in character.db.stats:
        character.db.stats['identity'] = {}
    if 'lineage' not in character.db.stats['identity']:
        character.db.stats['identity']['lineage'] = {}
    
    # Set base Willpower
    character.set_stat('pools', 'dual', 'Willpower', 1, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 1, temp=True)
    # Set virtues
    character.set_stat('pools', 'moral', 'Humanity', 2, temp=False)
    character.set_stat('pools', 'moral', 'Humanity', 2, temp=True)
    character.set_stat('virtues', 'moral', 'Conscience', 1, temp=False)
    character.set_stat('virtues', 'moral', 'Conscience', 1, temp=True)
    character.set_stat('virtues', 'moral', 'Self-Control', 1, temp=False)
    character.set_stat('virtues', 'moral', 'Self-Control', 1, temp=True)
    character.set_stat('virtues', 'moral', 'Courage', 1, temp=False)
    character.set_stat('virtues', 'moral', 'Courage', 1, temp=True)
    # Set default Banality for mortals (always 6)
    banality = get_default_banality('Mortal')
    if banality:
        character.db.stats['pools']['dual']['Banality'] = {'perm': banality, 'temp': banality}
        character.msg(f"|gBanality set to {banality} (permanent) for Mortal.") 