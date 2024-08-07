import textwrap
from evennia.utils.ansi import strip_raw_ansi, ANSIString

def wrap_ansi(text, width, left_padding=0, right_padding=0):
    """
    Wraps a string to the specified width, preserving ANSI codes, with optional left and right padding.

    Args:
        text (str): The text to wrap.
        width (int): The width to wrap the text to, including padding.
        left_padding (int): The amount of padding to add to the left side.
        right_padding (int): The amount of padding to add to the right side.

    Returns:
        str: The wrapped text with padding.
    """
    if left_padding + right_padding >= width:
        raise ValueError("Combined padding is too large for the given width.")

    text = ANSIString(text)
    raw_text = strip_raw_ansi(text)
    
    # Adjust the width for the padding
    wrap_width = width - left_padding - right_padding

    wrapped_text = textwrap.fill(
        raw_text, 
        width=wrap_width, 
        break_long_words=False, 
        break_on_hyphens=False
    )

    # Add padding to each line
    padded_lines = [
        " " * left_padding + line + " " * right_padding
        for line in wrapped_text.split('\n')
    ]

    return "\n".join(padded_lines)
