from evennia.utils.ansi import ANSI_REPLACEMENTS

# Add custom replacements for newline and tab
ANSI_REPLACEMENTS.update({
    '|r': '\n',  # Carriage return (newline)
    '|t': '\t'   # Tab
})
