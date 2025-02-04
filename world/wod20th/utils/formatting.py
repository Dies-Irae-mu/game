from evennia.utils.ansi import ANSIString
from collections import defaultdict
from world.wod20th.models import Stat

def format_stat(stat, value, width=25, default=None, tempvalue=None, allow_zero=False):
    """Format a stat for display with proper spacing and temporary values."""
    if default is not None and (value is None or (not allow_zero and value == 0) or value == ""):
        value = default
        tempvalue = default  # Also set tempvalue to default if value is defaulted

    # Don't add leading space here anymore
    stat_str = stat
    
    if stat == "Paradox":
        # For Paradox, only show the temporary value
        value_str = str(tempvalue) if tempvalue is not None else "None"
    elif stat == "Arete":
        # For Arete, don't show temporary value
        value_str = str(value)
    elif tempvalue is not None and int(tempvalue) != int(value):  # Convert to int for comparison
        if not allow_zero and tempvalue == 0:
            tempvalue = 1
        # Only show temporary value if it's numerically different
        value_str = f"{value}({tempvalue})"
    else:
        # Just show permanent value if temporary is same or not set
        value_str = str(value)

    # Truncate the stat name if it's too long
    max_stat_length = width - len(value_str) - 4  # 4 for the dots and spaces
    if len(stat_str) > max_stat_length:
        stat_str = stat_str[:max_stat_length-3] + "..."

    # Calculate dots needed for spacing
    dots = "." * (width - len(stat_str) - len(value_str) - 2)  # -2 for the spaces we'll add
    # Add highlight black to dots and consistent spacing
    return f" {stat_str}|x{dots}|n {value_str}"

def header(title, width=78,  color="|y", fillchar=ANSIString("|b-|n"), bcolor="|b"):
    return ANSIString.center(ANSIString(f"{bcolor}<|n {color} {title} |n{bcolor}>|n"), width=width, fillchar=ANSIString(fillchar)) + "\n"

def footer(width=78, fillchar=ANSIString("|b-|n")):
    return ANSIString(fillchar) * width + "\n"


def divider(title, width=78, fillchar="-", color="|r", text_color="|n"):
    """
    Create a divider with a title.

    Args:
        title (str): The title to display in the divider.
        width (int): The total width of the divider.
        fillchar (str): The character to use for filling.
        color (str): The color code for the divider line.
        text_color (str): The color code for the title text.

    Returns:
        ANSIString: The formatted divider.
    """
    if isinstance(fillchar, ANSIString):
        fillchar = fillchar[0]
    else:
        fillchar = fillchar[0]

    colored_fillchar = f"{color}{fillchar}"
    
    if title:
        # Calculate the width of the title text without color codes
        title_width = len(ANSIString(title).clean())
        
        # Calculate padding on each side of the title
        padding = (width - title_width - 2) // 2  # -2 for spaces around the title
        
        # Create the divider with title
        left_part = colored_fillchar * padding
        right_part = colored_fillchar * (width - padding - title_width - 2)
        inner_content = f"{left_part} {text_color}{title}|n {right_part}"
    else:
        # If no title, just create a line of fillchars
        inner_content = colored_fillchar * width

    # Remove any trailing whitespace and add the color terminator
    return ANSIString(f"{inner_content.rstrip()}|n")

def format_abilities(character):
    """Format abilities section of character sheet."""
    abilities = defaultdict(dict)
    
    # Get all standard abilities
    for stat in Stat.objects.filter(stat_type__in=['talent', 'skill', 'knowledge']):
        value = character.get_stat('abilities', stat.stat_type, stat.name)
        if value is not None:
            abilities[stat.category][stat.name] = value

    # Get splat-specific abilities
    for stat in Stat.objects.filter(stat_type='ability'):
        if character.can_have_ability(stat.name):
            value = character.get_stat('abilities', 'ability', stat.name)
            if value is not None:
                # Add to appropriate category based on the ability's category
                abilities[stat.category][stat.name] = value
    
    # Format output
    output = []
    for category in ['Talents', 'Skills', 'Knowledges']:
        if abilities[category]:
            output.append(f"{category:^20}")
            for name, value in sorted(abilities[category].items()):
                if value is not None:
                    output.append(f"{name:.<20}{value}")
            
    return "\n".join(output)
