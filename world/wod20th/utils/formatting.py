from evennia.utils.ansi import ANSIString
from collections import defaultdict
from world.wod20th.models import Stat

def format_stat(name: str, value: int, default: int = 0, tempvalue: int = None, width: int = 25, allow_zero: bool = False) -> str:
    """
    Format a stat for display on a character sheet.
    
    Args:
        name: The name of the stat
        value: The permanent value of the stat
        default: The default value if none is set
        tempvalue: The temporary value of the stat (if different from permanent)
        width: The width to pad the output to
        allow_zero: Whether to allow zero values (default False)
        
    Returns:
        A formatted string representing the stat
    """
    # Handle None values
    if value is None:
        value = default
    if tempvalue is None:
        tempvalue = value

    # Format the value part
    if not allow_zero and value == 0:
        value_str = "0"
    else:
        value_str = str(value)

    # If temporary value differs from permanent, show both
    if tempvalue != value:
        value_str = f"{value}({tempvalue})"

    # Format the full string with padding
    return f" {name}{'.' * (width - len(name) - len(value_str) - 2)} {value_str}"

def header(title, width=78, color="|y", fillchar="-", bcolor="|b"):
    """Create a header with consistent width."""
    # Ensure the title has proper spacing
    title = f" {title} "
    left_dashes = bcolor + fillchar * ((width - len(ANSIString(title).clean()) - 2) // 2) + "|n"
    right_dashes = bcolor + fillchar * (width - len(ANSIString(title).clean()) - 2 - len(ANSIString(left_dashes).clean())) + "|n"
    return f"{left_dashes}{color}{title}|n{right_dashes}\n"

def footer(width=78, fillchar="-"):
    """Create a footer with consistent width."""
    return "|b" + fillchar * width + "|n\n"

def divider(title, width=78, fillchar="-", color="|b", text_color="|y"):
    """Create a divider with consistent width."""
    if isinstance(fillchar, ANSIString):
        fillchar = fillchar[0]
    else:
        fillchar = fillchar[0]

    if title:
        # Calculate the width of the title text without color codes
        title_width = len(ANSIString(title).clean())
        
        # For column headers, center the title
        if width <= 25:  # Column headers
            padding = (width - title_width) // 2
            title_str = title.center(width)
            return f"{color}{title_str}|n"
        else:  # Full-width dividers
            # Calculate padding on each side of the title
            padding = (width - title_width - 2) // 2  # -2 for spaces around the title
            
            # Create the divider with title
            left_part = color + fillchar * padding + "|n"
            right_part = color + fillchar * (width - padding - title_width - 2) + "|n"
            return f"{left_part} {text_color}{title}|n {right_part}"
    else:
        # If no title, just create a line of fillchars
        return color + fillchar * width + "|n"

def format_abilities(character):
    """Format abilities section of character sheet."""
    # Base abilities for all characters
    base_abilities = {
        'Talents': ['Alertness', 'Athletics', 'Awareness', 'Brawl', 'Empathy', 
                   'Expression', 'Intimidation', 'Leadership', 'Streetwise', 'Subterfuge'],
        'Skills': ['Animal Ken', 'Crafts', 'Drive', 'Etiquette', 'Firearms', 
                  'Larceny', 'Melee', 'Performance', 'Stealth', 'Survival', 'Technology'],
        'Knowledges': ['Academics', 'Computer', 'Cosmology', 'Enigmas', 'Finance', 'Investigation', 
                      'Law', 'Medicine', 'Occult', 'Politics', 'Science']
    }

    # Get character's splat and type
    splat = character.get_stat('other', 'splat', 'Splat', temp=False)
    char_type = character.get_stat('identity', 'lineage', 'Type', temp=False)

    # Add splat-specific abilities
    if splat == 'Shifter':
        base_abilities['Talents'].append('Primal-Urge')
        if char_type in ['Corax', 'Camazotz', 'Mokole']:
            base_abilities['Talents'].append('Flight')
        base_abilities['Knowledges'].append('Rituals')
    elif splat == 'Vampire' and char_type == 'Gargoyle':
        base_abilities['Talents'].append('Flight')
    elif splat == 'Changeling':
        base_abilities['Talents'].append('Kenning')
        base_abilities['Knowledges'].append('Gremayre')
    elif splat == 'Companion':
        base_abilities['Talents'].append('Flight')
    # Format each category
    formatted_abilities = []
    for category in ['Talents', 'Skills', 'Knowledges']:
        abilities = base_abilities[category]
        for ability in sorted(abilities):
            value = character.get_stat('abilities', category.lower()[:-1], ability, temp=False) or 0
            formatted_abilities.append(format_stat(ability, value, width=25))

    return formatted_abilities

def format_secondary_abilities(character):
    """Format secondary abilities section of character sheet."""
    # Base secondary abilities
    base_secondary = {
        'Talents': ['Artistry', 'Carousing', 'Diplomacy', 'Intrigue', 'Lucid Dreaming', 'Mimicry', 
                   'Scrounging', 'Seduction', 'Style'],
        'Skills': ['Archery', 'Fencing', 'Fortune-Telling', 'Gambling', 'Jury-Rigging', 
                  'Pilot', 'Torture'],
        'Knowledges': ['Area Knowledge', 'Cultural Savvy', 'Demolitions', 'Herbalism', 
                      'Media', 'Power-Brokering', 'Vice']
    }

    # Get character's splat
    splat = character.get_stat('other', 'splat', 'Splat', temp=False)

    # Add splat-specific secondary abilities
    if splat == 'Mage':
        base_secondary['Talents'].extend(['Blatancy', 'Flying', 'High Ritual'])
        base_secondary['Skills'].extend(['Biotech', 'Do', 'Energy Weapons', 'Helmsman', 'Microgravity Ops'])
        base_secondary['Knowledges'].extend(['Cybernetics', 'Hypertech', 'Paraphysics', 'Xenobiology'])

    # Format each category
    formatted_abilities = []
    for category in ['Talents', 'Skills', 'Knowledges']:
        abilities = base_secondary[category]
        for ability in sorted(abilities):
            value = character.get_stat('abilities', f'secondary_{category.lower()[:-1]}', ability, temp=False) or 0
            formatted_abilities.append(format_stat(ability, value, width=25))

    return formatted_abilities
