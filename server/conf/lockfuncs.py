"""
Custom lock functions for Dies Irae.
"""
from evennia.locks.lockfuncs import *

def subscribed(accessing_obj, accessed_obj, *args, **kwargs):
    """
    Check if the accessing object is subscribed to the channel.
    
    Args:
        accessing_obj (Object): The object trying to access
        accessed_obj (Channel): The channel being accessed
        
    Returns:
        bool: True if the object is subscribed to the channel
    """
    if hasattr(accessed_obj, 'has_connection'):
        return accessed_obj.has_connection(accessing_obj)
    return False

def tenant(accessing_obj, accessed_obj, *args, **kwargs):
    """
    Check if the accessing object is a tenant of the apartment.
    
    Args:
        accessing_obj (Object): The character trying to access
        accessed_obj (Exit): The apartment exit being accessed
        
    Returns:
        bool: True if the character is a tenant of the apartment
    """
    # Get the destination room (the apartment)
    if not accessed_obj.destination:
        return False
        
    # Check if the destination has housing data
    if not hasattr(accessed_obj.destination.db, 'housing_data'):
        return False
        
    housing_data = accessed_obj.destination.db.housing_data
    if not housing_data:
        return False
        
    # Check if the character is in the current_tenants list
    current_tenants = housing_data.get('current_tenants', {})
    return str(accessing_obj.id) in current_tenants
