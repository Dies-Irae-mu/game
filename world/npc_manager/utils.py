"""
Utility functions for working with NPCs.
"""

from typeclasses.npcs import NPC
from typeclasses.npc_groups import NPCGroup as NPCGroupTypeclass
from evennia.utils.search import search_object
from django.db.models import Q
import uuid


def get_or_create_npc_model(npc_object):
    """
    Get or create a database model for an existing NPC object.
    
    Args:
        npc_object: The NPC typeclass instance
        
    Returns:
        tuple: (npc_model, created) - The NPC model and whether it was created
    """
    # Import models here to avoid circular imports
    from .models import NPC as NPCModel, NPCGroup
    
    if not npc_object or not hasattr(npc_object, 'is_npc') or not npc_object.is_npc:
        return None, False
        
    # Try to find a model linked to this object
    try:
        return NPCModel.objects.get(db_object=npc_object), False
    except NPCModel.DoesNotExist:
        pass
        
    # Try to find by UUID if the object has one
    if hasattr(npc_object.db, 'npc_id'):
        try:
            return NPCModel.objects.get(db_uuid=npc_object.db.npc_id), False
        except (NPCModel.DoesNotExist, ValueError):
            pass
            
    # Create a new model
    npc_model = NPCModel(
        db_key=npc_object.key,
        db_description=npc_object.db.desc if hasattr(npc_object.db, 'desc') else "",
        db_object=npc_object,
        db_uuid=npc_object.db.npc_id if hasattr(npc_object.db, 'npc_id') else uuid.uuid4()
    )
    
    # Copy additional attributes from the object
    if hasattr(npc_object.db, 'splat'):
        npc_model.db_splat = npc_object.db.splat
        
    if hasattr(npc_object.db, 'stats') and 'difficulty' in npc_object.db.stats:
        npc_model.db_difficulty = npc_object.db.stats['difficulty']
        
    if hasattr(npc_object.db, 'is_temporary'):
        npc_model.db_is_temporary = npc_object.db.is_temporary
        
    if hasattr(npc_object.db, 'expiration_time'):
        npc_model.db_expiration_time = npc_object.db.expiration_time
        
    if hasattr(npc_object.db, 'creator') and npc_object.db.creator:
        if hasattr(npc_object.db.creator, 'account'):
            npc_model.db_creator = npc_object.db.creator.account
            
    # Save the model
    npc_model.save()
    
    # Link to group if present
    if hasattr(npc_object.db, 'npc_group_id'):
        try:
            group_model = NPCGroup.objects.get(db_uuid=npc_object.db.npc_group_id)
            npc_model.db_group = group_model
            npc_model.save()
        except NPCGroup.DoesNotExist:
            pass
            
    return npc_model, True


def get_or_create_group_model(group_object):
    """
    Get or create a database model for an existing NPCGroup object.
    
    Args:
        group_object: The NPCGroup typeclass instance
        
    Returns:
        tuple: (group_model, created) - The NPCGroup model and whether it was created
    """
    # Import models here to avoid circular imports
    from .models import NPC as NPCModel, NPCGroup, NPCGoal, NPCPosition
    
    if not group_object or not isinstance(group_object, NPCGroupTypeclass):
        return None, False
        
    # Try to find a model linked to this object
    try:
        return NPCGroup.objects.get(db_object=group_object), False
    except NPCGroup.DoesNotExist:
        pass
        
    # Try to find by UUID if the object has one
    if hasattr(group_object.db, 'group_id'):
        try:
            return NPCGroup.objects.get(db_uuid=group_object.db.group_id), False
        except (NPCGroup.DoesNotExist, ValueError):
            pass
            
    # Create a new model
    group_model = NPCGroup(
        db_key=group_object.key,
        db_description=group_object.db.desc if hasattr(group_object.db, 'desc') else "",
        db_object=group_object,
        db_uuid=group_object.db.group_id if hasattr(group_object.db, 'group_id') else uuid.uuid4()
    )
    
    # Copy additional attributes from the object
    if hasattr(group_object.db, 'group_type'):
        group_model.db_group_type = group_object.db.group_type
        
    if hasattr(group_object.db, 'splat'):
        group_model.db_splat = group_object.db.splat
        
    if hasattr(group_object.db, 'difficulty'):
        group_model.db_difficulty = group_object.db.difficulty
        
    if hasattr(group_object.db, 'territory'):
        group_model.db_territory = group_object.db.territory
        
    if hasattr(group_object.db, 'resources'):
        group_model.db_resources = group_object.db.resources
        
    if hasattr(group_object.db, 'influence'):
        group_model.db_influence = group_object.db.influence
        
    if hasattr(group_object.db, 'creator') and group_object.db.creator:
        if hasattr(group_object.db.creator, 'account'):
            group_model.db_creator = group_object.db.creator.account
            
    # Save the model
    group_model.save()
    
    # Import goals if any
    if hasattr(group_object.db, 'goals') and group_object.db.goals:
        for i, goal_text in enumerate(group_object.db.goals):
            NPCGoal.objects.create(
                npc_group=group_model,
                db_text=goal_text,
                db_order=i
            )
            
    # Import NPCs and hierarchy
    if hasattr(group_object.db, 'npcs') and group_object.db.npcs:
        for npc_id, npc_data in group_object.db.npcs.items():
            # Get the NPC object
            npc_obj = npc_data.get('object')
            if npc_obj:
                # Create or get the NPC model
                npc_model, _ = get_or_create_npc_model(npc_obj)
                if npc_model:
                    # Update group reference
                    npc_model.db_group = group_model
                    npc_model.db_group_number = npc_data.get('group_number')
                    npc_model.save()
                    
                    # Add position if any
                    position = npc_data.get('position')
                    if position:
                        NPCPosition.objects.create(
                            npc_group=group_model,
                            npc=npc_model,
                            db_title=position,
                            db_order=0
                        )
                        
    return group_model, True


def sync_all_npcs():
    """
    Synchronize all in-game NPCs with the database.
    
    Returns:
        tuple: (npcs_created, npcs_updated) - Counts of created and updated NPCs
    """
    # Find all NPC objects
    npc_objects = search_object(None, typeclass="typeclasses.npcs.NPC")
    
    created = 0
    updated = 0
    
    for npc_obj in npc_objects:
        # Get or create the model
        npc_model, is_new = get_or_create_npc_model(npc_obj)
        if is_new:
            created += 1
        else:
            updated += 1
            
    return created, updated


def sync_all_groups():
    """
    Synchronize all in-game NPC Groups with the database.
    
    Returns:
        tuple: (groups_created, groups_updated) - Counts of created and updated groups
    """
    # Find all NPCGroup objects
    group_objects = search_object(None, typeclass="typeclasses.npc_groups.NPCGroup")
    
    created = 0
    updated = 0
    
    for group_obj in group_objects:
        # Get or create the model
        group_model, is_new = get_or_create_group_model(group_obj)
        if is_new:
            created += 1
        else:
            updated += 1
            
    return created, updated


def search_npcs(query=None, splat=None, is_temporary=None, group=None):
    """
    Search for NPCs with various filters.
    
    Args:
        query (str, optional): Text to search in name and description
        splat (str, optional): Filter by splat type
        is_temporary (bool, optional): Filter by temporary status
        group (NPCGroup or str, optional): Filter by group (object or name)
        
    Returns:
        QuerySet: Filtered NPCs
    """
    # Import models here to avoid circular imports
    from .models import NPC as NPCModel, NPCGroup
    
    # Start with all NPCs
    npcs = NPCModel.objects.all()
    
    # Apply text search if provided
    if query:
        npcs = npcs.filter(
            Q(db_key__icontains=query) | 
            Q(db_description__icontains=query)
        )
        
    # Filter by splat if provided
    if splat:
        npcs = npcs.filter(db_splat=splat)
        
    # Filter by temporary status if provided
    if is_temporary is not None:
        npcs = npcs.filter(db_is_temporary=is_temporary)
        
    # Filter by group if provided
    if group:
        if isinstance(group, NPCGroup):
            npcs = npcs.filter(db_group=group)
        elif isinstance(group, str):
            npcs = npcs.filter(db_group__db_key__icontains=group)
            
    return npcs


def search_groups(query=None, group_type=None, splat=None):
    """
    Search for NPC Groups with various filters.
    
    Args:
        query (str, optional): Text to search in name and description
        group_type (str, optional): Filter by group type
        splat (str, optional): Filter by splat type
        
    Returns:
        QuerySet: Filtered NPC Groups
    """
    # Import models here to avoid circular imports
    from .models import NPCGroup
    
    # Start with all groups
    groups = NPCGroup.objects.all()
    
    # Apply text search if provided
    if query:
        groups = groups.filter(
            Q(db_key__icontains=query) | 
            Q(db_description__icontains=query) |
            Q(db_territory__icontains=query)
        )
        
    # Filter by group type if provided
    if group_type:
        groups = groups.filter(db_group_type__icontains=group_type)
        
    # Filter by splat if provided
    if splat:
        groups = groups.filter(db_splat=splat)
            
    return groups 