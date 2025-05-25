"""
Utility functions for searching and validating characters.
"""
from evennia.utils.search import search_object
from typeclasses.characters import Character

def search_character(searcher, search_string, global_search=True, quiet=False):
    """
    Search for a character, ensuring only Character objects are returned.
    
    Args:
        searcher (Object): The object performing the search
        search_string (str): The string to search for
        global_search (bool): Whether to search globally or just in the current location
        quiet (bool): Whether to suppress error messages
        
    Returns:
        Character or None: The found character object, or None if not found
    """
    # First try exact match with Character typeclass
    matches = search_object(search_string, typeclass=Character, exact=True)
    
    if matches:
        return matches[0]
        
    # If no exact match, try case-insensitive search
    chars = search_object(search_string, typeclass=Character)
    matching_chars = [char for char in chars if char.key.lower() == search_string.lower()]
    if matching_chars:
        return matching_chars[0]
        
    # If still no match, try alias as last resort
    # First try using the Character's class method
    target = Character.get_by_alias(search_string.lower())
    if target:
        return target
        
    # If that doesn't work, fallback to direct attribute search
    alias_matches = search_object(
        search_string,
        typeclass=Character,
        attribute_name="alias", 
        attribute_value=search_string
    )
    if alias_matches:
        return alias_matches[0]
        
    # Also try case-insensitive attribute search as a last resort
    all_chars = search_object("*", typeclass=Character)
    for char in all_chars:
        if hasattr(char, 'attributes') and char.attributes.has('alias'):
            alias = char.attributes.get('alias')
            if alias and alias.lower() == search_string.lower():
                return char
        
    # If we get here, no valid character was found
    if not quiet:
        searcher.msg(f"Could not find a character named '{search_string}'.")
    return None 