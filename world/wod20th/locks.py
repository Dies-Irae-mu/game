"""
Lock functions for World of Darkness 20th Anniversary Edition
"""
from evennia.utils import logger

# Dictionary of lock functions that will be registered
LOCK_FUNCS = {}

def has_talent(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has a specific talent at optional minimum level."""
    if not args:
        return False
        
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        stats = accessing_obj.db.stats
        if not stats:
            return False
            
        talent_name = args[0].strip()
        required_level = 1  # Default minimum level
        
        if len(args) > 1:
            try:
                required_level = int(args[1])
            except ValueError:
                return False
        
        talent_value = stats.get('abilities', {}) \
                           .get('talent', {}) \
                           .get(talent_name, {}) \
                           .get('temp', stats.get('abilities', {}) \
                                            .get('talent', {}) \
                                            .get(talent_name, {}) \
                                            .get('perm', 0))
        
        try:
            talent_value = int(talent_value)
            return talent_value >= required_level
        except (ValueError, TypeError):
            return False
            
    except Exception:
        return False

def has_skill(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has a specific skill at optional minimum level."""
    if not args:
        return False
        
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        stats = accessing_obj.db.stats
        if not stats:
            return False
            
        skill_name = args[0].strip()
        required_level = 1
        
        if len(args) > 1:
            try:
                required_level = int(args[1])
            except ValueError:
                return False
        
        skill_value = stats.get('abilities', {}) \
                          .get('skill', {}) \
                          .get(skill_name, {}) \
                          .get('temp', stats.get('abilities', {}) \
                                           .get('skill', {}) \
                                           .get(skill_name, {}) \
                                           .get('perm', 0))
        
        try:
            skill_value = int(skill_value)
            return skill_value >= required_level
        except (ValueError, TypeError):
            return False
            
    except Exception:
        return False

def has_knowledge(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has a specific knowledge at optional minimum level."""
    if not args:
        return False
        
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        stats = accessing_obj.db.stats
        if not stats:
            return False
            
        knowledge_name = args[0].strip()
        required_level = 1
        
        if len(args) > 1:
            try:
                required_level = int(args[1])
            except ValueError:
                return False
        
        knowledge_value = stats.get('abilities', {}) \
                             .get('knowledge', {}) \
                             .get(knowledge_name, {}) \
                             .get('temp', stats.get('abilities', {}) \
                                              .get('knowledge', {}) \
                                              .get(knowledge_name, {}) \
                                              .get('perm', 0))
        
        try:
            knowledge_value = int(knowledge_value)
            return knowledge_value >= required_level
        except (ValueError, TypeError):
            return False
            
    except Exception:
        return False

def has_secondary_talent(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has a specific secondary talent at optional minimum level."""
    if not args:
        return False
        
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        stats = accessing_obj.db.stats
        if not stats:
            return False
            
        talent_name = args[0].strip()
        required_level = 1
        
        if len(args) > 1:
            try:
                required_level = int(args[1])
            except ValueError:
                return False
        
        talent_value = stats.get('secondary_abilities', {}) \
                           .get('talent', {}) \
                           .get(talent_name, {}) \
                           .get('temp', stats.get('secondary_abilities', {}) \
                                            .get('talent', {}) \
                                            .get(talent_name, {}) \
                                            .get('perm', 0))
        
        try:
            talent_value = int(talent_value)
            return talent_value >= required_level
        except (ValueError, TypeError):
            return False
            
    except Exception:
        return False

def has_secondary_skill(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has a specific secondary skill at optional minimum level."""
    if not args:
        return False
        
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        stats = accessing_obj.db.stats
        if not stats:
            return False
            
        skill_name = args[0].strip()
        required_level = 1
        
        if len(args) > 1:
            try:
                required_level = int(args[1])
            except ValueError:
                return False
        
        skill_value = stats.get('secondary_abilities', {}) \
                          .get('skill', {}) \
                          .get(skill_name, {}) \
                          .get('temp', stats.get('secondary_abilities', {}) \
                                           .get('skill', {}) \
                                           .get(skill_name, {}) \
                                           .get('perm', 0))
        
        try:
            skill_value = int(skill_value)
            return skill_value >= required_level
        except (ValueError, TypeError):
            return False
            
    except Exception:
        return False

def has_secondary_knowledge(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has a specific secondary knowledge at optional minimum level."""
    if not args:
        return False
        
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        stats = accessing_obj.db.stats
        if not stats:
            return False
            
        knowledge_name = args[0].strip()
        required_level = 1
        
        if len(args) > 1:
            try:
                required_level = int(args[1])
            except ValueError:
                return False
        
        knowledge_value = stats.get('secondary_abilities', {}) \
                             .get('knowledge', {}) \
                             .get(knowledge_name, {}) \
                             .get('temp', stats.get('secondary_abilities', {}) \
                                              .get('knowledge', {}) \
                                              .get(knowledge_name, {}) \
                                              .get('perm', 0))
        
        try:
            knowledge_value = int(knowledge_value)
            return knowledge_value >= required_level
        except (ValueError, TypeError):
            return False
            
    except Exception:
        return False

def has_merit(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has a specific merit at optional minimum level."""
    if not args:
        return False
        
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        stats = accessing_obj.db.stats
        if not stats:
            return False
            
        merit_name = args[0].strip()
        required_level = 1
        
        if len(args) > 1:
            try:
                required_level = int(args[1])
            except ValueError:
                return False
        
        merit_value = stats.get('merits', {}) \
                          .get('merit', {}) \
                          .get(merit_name, {}) \
                          .get('temp', stats.get('merits', {}) \
                                           .get('merit', {}) \
                                           .get(merit_name, {}) \
                                           .get('perm', 0))
        
        try:
            merit_value = int(merit_value)
            return merit_value >= required_level
        except (ValueError, TypeError):
            return False
            
    except Exception:
        return False

def has_clan(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has a specific clan."""
    if not args:
        return False
        
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        stats = accessing_obj.db.stats
        if not stats:
            return False
            
        clan = stats.get('identity', {}) \
                   .get('lineage', {}) \
                   .get('Clan', {}) \
                   .get('perm')
                    
        required_clan = ' '.join(args) if len(args) > 1 else args[0]
        return str(clan).strip().lower() == str(required_clan).strip().lower()
    except Exception:
        return False

def has_tribe(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has a specific tribe."""
    if not args:
        return False
        
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        stats = accessing_obj.db.stats
        if not stats:
            return False
            
        tribe = stats.get('identity', {}) \
                    .get('lineage', {}) \
                    .get('Tribe', {}) \
                    .get('perm')
                    
        required_tribe = ' '.join(args) if len(args) > 1 else args[0]
        return str(tribe).strip().lower() == str(required_tribe).strip().lower()
    except Exception:
        return False

def has_auspice(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has a specific auspice."""
    if not args:
        return False
        
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        stats = accessing_obj.db.stats
        if not stats:
            return False
            
        auspice = stats.get('identity', {}) \
                      .get('lineage', {}) \
                      .get('Auspice', {}) \
                      .get('perm')
                    
        required_auspice = ' '.join(args) if len(args) > 1 else args[0]
        return str(auspice).strip().lower() == str(required_auspice).strip().lower()
    except Exception:
        return False

def has_type(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has a specific type."""
    if not args:
        return False
        
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        stats = accessing_obj.db.stats
        if not stats:
            return False
            
        char_type = stats.get('identity', {}) \
                        .get('lineage', {}) \
                        .get('Type', {}) \
                        .get('perm')
                    
        required_type = ' '.join(args) if len(args) > 1 else args[0]
        return str(char_type).strip().lower() == str(required_type).strip().lower()
    except Exception:
        return False

def has_splat(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has a specific splat."""
    if not args:
        return False
        
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        stats = accessing_obj.db.stats
        if not stats:
            return False
            
        splat = stats.get('other', {}) \
                    .get('splat', {}) \
                    .get('Splat', {}) \
                    .get('perm')
                    
        required_splat = ' '.join(args) if len(args) > 1 else args[0]
        return str(splat).strip().lower() == str(required_splat).strip().lower()
    except Exception:
        return False

def has_tradition(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has a specific tradition."""
    if not args:
        return False
        
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        stats = accessing_obj.db.stats
        if not stats:
            return False
            
        tradition = stats.get('identity', {}) \
                        .get('lineage', {}) \
                        .get('Tradition', {}) \
                        .get('perm')
                    
        required_tradition = ' '.join(args) if len(args) > 1 else args[0]
        return str(tradition).strip().lower() == str(required_tradition).strip().lower()
    except Exception:
        return False

def has_affiliation(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has a specific mage faction."""
    if not args:
        return False
        
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        stats = accessing_obj.db.stats
        if not stats:
            return False
            
        faction = stats.get('identity', {}) \
                      .get('lineage', {}) \
                      .get('Mage Faction', {}) \
                      .get('temp', stats.get('identity', {}) \
                                     .get('lineage', {}) \
                                     .get('Mage Faction', {}) \
                                     .get('perm'))
                    
        required_faction = ' '.join(args) if len(args) > 1 else args[0]
        return str(faction).strip().lower() == str(required_faction).strip().lower()
    except Exception:
        return False

def has_court(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has a specific court."""
    if not args:
        return False
        
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        stats = accessing_obj.db.stats
        if not stats:
            return False
            
        court = stats.get('identity', {}) \
                    .get('lineage', {}) \
                    .get('Court', {}) \
                    .get('perm')
                    
        required_court = ' '.join(args) if len(args) > 1 else args[0]
        return str(court).strip().lower() == str(required_court).strip().lower()
    except Exception:
        return False

def has_kith(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has a specific kith."""
    if not args:
        return False
        
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        stats = accessing_obj.db.stats
        if not stats:
            return False
            
        kith = stats.get('identity', {}) \
                   .get('lineage', {}) \
                   .get('Kith', {}) \
                   .get('perm')
                    
        required_kith = ' '.join(args) if len(args) > 1 else args[0]
        return str(kith).strip().lower() == str(required_kith).strip().lower()
    except Exception:
        return False

def has_convention(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has a specific Technocratic convention."""
    if not args:
        return False
        
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        stats = accessing_obj.db.stats
        if not stats:
            return False
            
        convention = stats.get('identity', {}) \
                         .get('lineage', {}) \
                         .get('Convention', {}) \
                         .get('perm')
                    
        required_convention = ' '.join(args) if len(args) > 1 else args[0]
        return str(convention).strip().lower() == str(required_convention).strip().lower()
    except Exception:
        return False

def has_nephandi_faction(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has a specific Nephandi faction."""
    if not args:
        return False
        
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        stats = accessing_obj.db.stats
        if not stats:
            return False
            
        nephandi_faction = stats.get('identity', {}) \
                               .get('lineage', {}) \
                               .get('Nephandi Faction', {}) \
                               .get('perm')
                    
        required_faction = ' '.join(args) if len(args) > 1 else args[0]
        return str(nephandi_faction).strip().lower() == str(required_faction).strip().lower()
    except Exception:
        return False

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
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
        
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

def has_wyrm_taint(accessing_obj, accessed_obj, *args, **kwargs):
    """Check if character has the is_wyrm tag."""
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    try:
        return accessing_obj.tags.get("is_wyrm", category="wyrm_taint")
    except Exception:
        return False

# Register all lock functions
LOCK_FUNCS.update({
    "has_talent": has_talent,
    "has_skill": has_skill,
    "has_knowledge": has_knowledge,
    "has_secondary_talent": has_secondary_talent,
    "has_secondary_skill": has_secondary_skill,
    "has_secondary_knowledge": has_secondary_knowledge,
    "has_merit": has_merit,
    "has_clan": has_clan,
    "has_tribe": has_tribe,
    "has_auspice": has_auspice,
    "has_type": has_type,
    "has_splat": has_splat,
    "has_tradition": has_tradition,
    "has_affiliation": has_affiliation,
    "has_court": has_court,
    "has_kith": has_kith,
    "has_convention": has_convention,
    "has_nephandi_faction": has_nephandi_faction,
    "subscribed": subscribed,
    "tenant": tenant,
    "has_wyrm_taint": has_wyrm_taint
})

def is_in_group(accessing_obj, accessed_obj, *args, **kwargs):
    """
    Check if the accessing character is a member of the specified group.
    
    Args:
        accessing_obj (Object): The character trying to access
        accessed_obj (Object): The object being accessed
        args (list): The first argument should be the group ID or name
        
    Returns:
        bool: True if the character is a member of the group
    """
    if not args:
        return False
    
    # Get the real character if this is an Account
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    # Try to get the character sheet
    try:
        from world.wod20th.models import CharacterSheet
        from world.groups.models import Group, GroupMembership
        
        # Get character sheet
        try:
            if not hasattr(accessing_obj, 'character_sheet'):
                return False
            char_sheet = accessing_obj.character_sheet
        except Exception:
            return False
        
        # Try to find the group by ID first
        group_identifier = args[0].strip()
        
        try:
            # If it's a number, try it as an ID
            group_id = int(group_identifier)
            group = Group.objects.filter(group_id=group_id).first()
        except ValueError:
            # If it's not a number, search by name
            group = Group.objects.filter(name__iexact=group_identifier).first()
        
        if not group:
            return False
        
        # Check if the character is a member of the group
        return GroupMembership.objects.filter(group=group, character=char_sheet).exists()
        
    except Exception:
        return False

def is_group_leader(accessing_obj, accessed_obj, *args, **kwargs):
    """
    Check if the accessing character is the leader of the specified group.
    
    Args:
        accessing_obj (Object): The character trying to access
        accessed_obj (Object): The object being accessed
        args (list): The first argument should be the group ID or name
        
    Returns:
        bool: True if the character is the leader of the group
    """
    if not args:
        return False
    
    # Get the real character if this is an Account
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    # Try to get the character sheet
    try:
        from world.wod20th.models import CharacterSheet
        from world.groups.models import Group
        
        # Get character sheet
        try:
            if not hasattr(accessing_obj, 'character_sheet'):
                return False
            char_sheet = accessing_obj.character_sheet
        except Exception:
            return False
        
        # Try to find the group by ID first
        group_identifier = args[0].strip()
        
        try:
            # If it's a number, try it as an ID
            group_id = int(group_identifier)
            group = Group.objects.filter(group_id=group_id).first()
        except ValueError:
            # If it's not a number, search by name
            group = Group.objects.filter(name__iexact=group_identifier).first()
        
        if not group:
            return False
        
        # Check if the character is the leader of the group
        return group.leader and group.leader.id == char_sheet.id
        
    except Exception:
        return False

def has_group_role(accessing_obj, accessed_obj, *args, **kwargs):
    """
    Check if the accessing character has a specific role in the specified group.
    
    Args:
        accessing_obj (Object): The character trying to access
        accessed_obj (Object): The object being accessed
        args (list): First arg is group ID/name, second arg is role name
        
    Returns:
        bool: True if the character has the specified role in the group
    """
    if len(args) < 2:
        return False
    
    # Get the real character if this is an Account
    if hasattr(accessing_obj, 'character'):
        accessing_obj = accessing_obj.character
    
    # Try to get the character sheet
    try:
        from world.wod20th.models import CharacterSheet
        from world.groups.models import Group, GroupMembership, GroupRole
        
        # Get character sheet
        try:
            if not hasattr(accessing_obj, 'character_sheet'):
                return False
            char_sheet = accessing_obj.character_sheet
        except Exception:
            return False
        
        # Try to find the group by ID first
        group_identifier = args[0].strip()
        role_name = args[1].strip()
        
        try:
            # If it's a number, try it as an ID
            group_id = int(group_identifier)
            group = Group.objects.filter(group_id=group_id).first()
        except ValueError:
            # If it's not a number, search by name
            group = Group.objects.filter(name__iexact=group_identifier).first()
        
        if not group:
            return False
        
        # Check if the character has the specified role in the group
        membership = GroupMembership.objects.filter(group=group, character=char_sheet).first()
        if not membership or not membership.role:
            return False
            
        return membership.role.name.lower() == role_name.lower()
        
    except Exception:
        return False

# Add the new group lock functions to the registry
LOCK_FUNCS.update({
    "is_in_group": is_in_group,
    "is_group_leader": is_group_leader,
    "has_group_role": has_group_role,
})

def _get_lock_functions():
    """Return the lock functions for this module."""
    return LOCK_FUNCS