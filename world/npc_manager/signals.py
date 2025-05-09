"""
Signals for NPC Manager app.

These signals help keep the database models and in-game objects synchronized.
"""

from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from evennia.objects.models import ObjectDB


@receiver(post_save, sender=ObjectDB)
def handle_npc_object_save(sender, instance, created, **kwargs):
    """
    When an NPC object is saved, update its database model if one exists.
    """
    # Import model classes inside the handler to avoid circular imports
    from .models import NPCGroup, NPC
    
    # Check if this is an NPC object
    if hasattr(instance, 'is_npc') and instance.is_npc:
        # Look for a linked NPC model
        try:
            npc = NPC.objects.get(db_object=instance)
            
            # Update key and description
            if npc.db_key != instance.key:
                npc.db_key = instance.key
                npc.save(update_fields=['db_key'])
                
            # Update other fields as needed
            if hasattr(instance.db, 'desc') and npc.db_description != instance.db.desc:
                npc.db_description = instance.db.desc
                npc.save(update_fields=['db_description'])
                
            # Update temporary status
            if hasattr(instance.db, 'is_temporary') and npc.db_is_temporary != instance.db.is_temporary:
                npc.db_is_temporary = instance.db.is_temporary
                npc.save(update_fields=['db_is_temporary'])
                
            # Update expiration time
            if hasattr(instance.db, 'expiration_time') and npc.db_expiration_time != instance.db.expiration_time:
                npc.db_expiration_time = instance.db.expiration_time
                npc.save(update_fields=['db_expiration_time'])
                
        except NPC.DoesNotExist:
            # No linked model found
            pass
            
    # Check if this is an NPCGroup object
    if hasattr(instance, 'db') and hasattr(instance.db, 'group_id'):
        # Look for a linked NPCGroup model
        try:
            npc_group = NPCGroup.objects.get(db_object=instance)
            
            # Update key and description
            if npc_group.db_key != instance.key:
                npc_group.db_key = instance.key
                npc_group.save(update_fields=['db_key'])
                
            # Update other fields as needed
            if hasattr(instance.db, 'desc') and npc_group.db_description != instance.db.desc:
                npc_group.db_description = instance.db.desc
                npc_group.save(update_fields=['db_description'])
                
            # Update territory
            if hasattr(instance.db, 'territory') and npc_group.db_territory != instance.db.territory:
                npc_group.db_territory = instance.db.territory
                npc_group.save(update_fields=['db_territory'])
                
            # Update resources
            if hasattr(instance.db, 'resources') and npc_group.db_resources != instance.db.resources:
                npc_group.db_resources = instance.db.resources
                npc_group.save(update_fields=['db_resources'])
                
            # Update influence
            if hasattr(instance.db, 'influence') and npc_group.db_influence != instance.db.influence:
                npc_group.db_influence = instance.db.influence
                npc_group.save(update_fields=['db_influence'])
                
        except NPCGroup.DoesNotExist:
            # No linked model found
            pass


@receiver(post_save, sender='npc_manager.NPC')
def sync_npc_to_game(sender, instance, created, **kwargs):
    """
    When an NPC model is saved, update the in-game object if it exists.
    """
    # Skip signal processing during sync from in-game object
    if kwargs.get('update_fields') == ['db_key'] or kwargs.get('update_fields') == ['db_description']:
        return
        
    # If we have a linked in-game object, update it
    if instance.db_object:
        obj = instance.db_object
        
        # Update object name if different
        if obj.key != instance.db_key:
            obj.key = instance.db_key
            
        # Update description
        if hasattr(obj.db, 'desc') and obj.db.desc != instance.db_description:
            obj.db.desc = instance.db_description
            
        # Update temporary status
        if hasattr(obj.db, 'is_temporary') and obj.db.is_temporary != instance.db_is_temporary:
            obj.db.is_temporary = instance.db_is_temporary
            
        # Update expiration time
        if hasattr(obj.db, 'expiration_time') and obj.db.expiration_time != instance.db_expiration_time:
            obj.db.expiration_time = instance.db_expiration_time


@receiver(post_save, sender='npc_manager.NPCGroup')
def sync_npc_group_to_game(sender, instance, created, **kwargs):
    """
    When an NPCGroup model is saved, update the in-game object if it exists.
    """
    # Skip signal processing during sync from in-game object
    if kwargs.get('update_fields') == ['db_key'] or kwargs.get('update_fields') == ['db_description']:
        return
        
    # If we have a linked in-game object, update it
    if instance.db_object:
        obj = instance.db_object
        
        # Update object name if different
        if obj.key != instance.db_key:
            obj.key = instance.db_key
            
        # Update description
        if hasattr(obj.db, 'desc') and obj.db.desc != instance.db_description:
            obj.db.desc = instance.db_description
            
        # Update group type
        if hasattr(obj.db, 'group_type') and obj.db.group_type != instance.db_group_type:
            obj.db.group_type = instance.db_group_type
            
        # Update territory
        if hasattr(obj.db, 'territory') and obj.db.territory != instance.db_territory:
            obj.db.territory = instance.db_territory
            
        # Update resources
        if hasattr(obj.db, 'resources') and obj.db.resources != instance.db_resources:
            obj.db.resources = instance.db_resources
            
        # Update influence
        if hasattr(obj.db, 'influence') and obj.db.influence != instance.db_influence:
            obj.db.influence = instance.db_influence


@receiver(post_save, sender='npc_manager.NPCGoal')
def sync_goal_to_game(sender, instance, created, **kwargs):
    """
    When an NPCGoal is saved, update the linked group's goals list.
    """
    # Get the group and its in-game object
    npc_group = instance.npc_group
    obj = npc_group.db_object
    
    if obj:
        # Update goals in the in-game object
        if not hasattr(obj.db, 'goals') or not obj.db.goals:
            obj.db.goals = []
            
        # Rebuild the goals list from the database
        # Import the model class inside the handler to avoid circular imports
        from .models import NPCGoal
        goals = list(npc_group.get_goals().values_list('db_text', flat=True))
        obj.db.goals = goals


@receiver(post_delete, sender='npc_manager.NPCGoal')
def handle_goal_delete(sender, instance, **kwargs):
    """
    When an NPCGoal is deleted, update the linked group's goals list.
    """
    # Get the group and its in-game object
    npc_group = instance.npc_group
    obj = npc_group.db_object
    
    if obj:
        # Update goals in the in-game object
        if hasattr(obj.db, 'goals'):
            # Rebuild the goals list from the database
            goals = list(npc_group.get_goals().values_list('db_text', flat=True))
            obj.db.goals = goals


@receiver(post_save, sender='npc_manager.NPCPosition')
def sync_position_to_game(sender, instance, created, **kwargs):
    """
    When an NPCPosition is saved, update the linked group's hierarchy.
    """
    # Import the model class inside the handler to avoid circular imports
    from .models import NPCPosition
    
    # Get the group and its in-game object
    npc_group = instance.npc_group
    obj = npc_group.db_object
    
    if obj and hasattr(obj.db, 'hierarchy'):
        # Get all positions for this group
        positions = NPCPosition.objects.filter(npc_group=npc_group)
        
        # Rebuild the hierarchy
        hierarchy = {}
        for pos in positions:
            if pos.db_title not in hierarchy:
                hierarchy[pos.db_title] = []
                
            # Add NPC to this position if there's a linked in-game NPC
            if pos.npc.db_object:
                npc_id = str(pos.npc.db_object.id)
                if npc_id not in hierarchy[pos.db_title]:
                    hierarchy[pos.db_title].append(npc_id)
                    
        # Update the hierarchy
        obj.db.hierarchy = hierarchy


@receiver(post_delete, sender='npc_manager.NPCPosition')
def handle_position_delete(sender, instance, **kwargs):
    """
    When an NPCPosition is deleted, update the linked group's hierarchy.
    """
    # Same as sync_position_to_game, since we need to rebuild the hierarchy
    sync_position_to_game(sender, instance, False, **kwargs) 