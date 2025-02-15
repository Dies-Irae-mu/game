"""
Utility functions for handling Banality ratings and messages.
"""
from world.wod20th.utils.sheet_constants import CLAN
from world.wod20th.utils.stat_mappings import VALID_MORTALPLUS_TYPES

def get_banality_message(banality_rating):
    """
    Get the appropriate message for a given Banality rating.
    
    Args:
        banality_rating (int): The target's Banality rating
        
    Returns:
        str: A message describing how a Changeling perceives the target's Banality
    """
    if banality_rating <= 2:
        return "There is a dangerous sense of Glamour about this person, almost as if their soul exists outside of reality as humans know it. So deep you could fall in."
    elif banality_rating <= 4:
        return "You sense a rare warmth from this person - their soul seems remarkably untainted by Banality. Such dreamers are precious and rare in this modern age."
    elif banality_rating == 5:
        return "You sense a creative spark in this one - while not free from Banality's touch, their imagination still burns bright."
    elif banality_rating == 6:
        return "You sense the weight of the mundane world upon this one's shoulders, though they still struggle against its grip."
    elif banality_rating == 7:
        return "You sense the heavy chains of Banality binding this one's dreams - they seem beaten down by the mundane world."
    elif banality_rating == 8:
        return "You feel a chill as you look at this person - their Banality is strong enough to be actively dangerous to your fae nature."
    else:  # 9-10
        return "You recoil instinctively - this person's Banality is overwhelming, a choking cloud of hopelessness that threatens to snuff out your very essence."

def get_default_banality(splat, subtype=None, affiliation=None, tradition=None, convention=None, nephandi_faction=None):
    """
    Get the default banality rating based on splat type and various subtypes.
    
    Args:
        splat (str): The main splat type (Vampire, Mage, etc)
        subtype (str, optional): Clan, Shifter Type, Mortal+ Type, etc
        affiliation (str, optional): Mage affiliation (Traditions, Technocracy, Nephandi)
        tradition (str, optional): Specific tradition for Traditional mages
        convention (str, optional): Specific convention for Technocrats
        nephandi_faction (str, optional): Specific Nephandi faction
        
    Returns:
        int: The default banality rating
    """
    # Handle empty or None values
    splat = splat.lower() if splat else 'mortal'
    subtype = subtype.lower() if subtype else None
    affiliation = affiliation.lower() if affiliation else None
    tradition = tradition.lower() if tradition else None
    convention = convention.lower() if convention else None
    nephandi_faction = nephandi_faction.lower() if nephandi_faction else None

    # Base cases by splat
    if splat == 'changeling':
        return 3  # Default Changeling Banality if no kith specified
    elif splat == 'mortal':
        return 6
    
    # Vampire cases - all vampires have Banality 5 except specific clans
    elif splat == 'vampire':
        if subtype:
            subtype = subtype.lower()
            if subtype in ['malkavian', 'malkavian antitribu']:
                return 3
            elif subtype == 'daughters of cacophony':
                return 4
        return 5  # Default vampire banality
    
    # Mage cases
    elif splat == 'mage':
        if affiliation == 'traditions':
            if tradition in ['dreamspeakers', 'cult of ecstasy']:
                return 4
            elif tradition in ['virtual adepts', 'order of hermes']:
                return 6
            return 5  # Default tradition banality
        elif affiliation == 'technocracy':
            if convention == 'iteration x':
                return 8
            elif convention == 'progenitors':
                return 7
            elif convention == 'void engineers':
                return 5
            return 7  # Default technocracy banality
        elif affiliation == 'nephandi':
            if nephandi_faction == "k'llashaa":
                return 3
            elif nephandi_faction == 'baphies':
                return 4
            elif nephandi_faction == 'ironhands':
                return 8
            return 5  # Default nephandi banality
        return 5  # Default mage banality
    
    # Shifter cases
    elif splat == 'shifter':
        if subtype:
            subtype = subtype.lower()
            if subtype == 'ratkin':
                return 3
            elif subtype in ['gurahl', 'mokole', 'corax', 'nuwisha', 'kitsune']:
                return 4
            elif subtype in ['garou', 'rokea', 'bastet']:
                return 5
            elif subtype == 'nagah':
                return 6
            elif subtype == 'ananasi':
                return 7
        return 5  # Default shifter banality
    
    # Mortal+ cases
    elif splat == 'mortal+':
        if subtype:
            subtype = subtype.lower()
            if subtype == 'kinain':
                return 3
            elif subtype in ['sorcerer', 'kinfolk', 'psychic']:
                return 5
            elif subtype in ['ghoul', 'faithful']:
                return 6
        return 6  # Default mortal+ banality
    
    # Companion cases
    elif splat == 'companion':
        if subtype:
            subtype = subtype.lower()
            if subtype == 'spirit':
                return 4
            elif subtype == 'construct':
                return 7
            elif subtype == 'robot':
                return 8
            elif subtype == 'alien':
                return 3
            elif subtype == 'bygone':
                return 4
            elif subtype == 'familiar':
                return 4
        return 6  # Default companion banality
    
    # Possessed cases
    elif splat == 'possessed':
        if subtype == 'kami':
            return 4
        elif subtype == 'fomori':
            return 7
        return 6  # Default possessed banality
    
    # Default case for unknown splats
    return 6 