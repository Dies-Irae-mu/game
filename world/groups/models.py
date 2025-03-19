from django.db import models
from evennia.utils.idmapper.models import SharedMemoryModel
from evennia.typeclasses.models import TypedObject
from evennia.utils import logger
from world.wod20th.models import CharacterSheet, Roster

class Group(SharedMemoryModel):
    """
    Model for storing in-game group information.
    Groups can represent factions, covens, packs, or any other character organization.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    ic_description = models.TextField(blank=True)
    leader = models.ForeignKey(CharacterSheet, on_delete=models.SET_NULL, null=True, related_name='led_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    website = models.URLField(blank=True)
    is_public = models.BooleanField(default=True, help_text="If True, group will be visible in the public group list")
    roster = models.ForeignKey(Roster, on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_groups')
    group_id = models.PositiveIntegerField(unique=True, null=True, help_text="Sequential ID number for the group")
    notes = models.TextField(blank=True, help_text="Private notes visible only to staff and group members")
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Override save to handle group ID assignment.
        """
        logger.log_info(f"Saving Group: {self.name}")
        logger.log_info(f"Current leader: {self.leader}")
        
        # If group_id is not set, find the next available ID
        if self.group_id is None:
            # Get all existing group IDs
            used_ids = list(Group.objects.exclude(id=self.id).values_list('group_id', flat=True))
            used_ids = [id for id in used_ids if id is not None]
            
            if used_ids:
                # Find the smallest unused ID (including gaps)
                all_ids = set(range(1, max(used_ids) + 2))
                available_ids = all_ids - set(used_ids)
                if available_ids:
                    self.group_id = min(available_ids)
            else:
                # No existing groups with IDs, start with 1
                self.group_id = 1
        
        super().save(*args, **kwargs)
        logger.log_info(f"Group saved. Leader after save: {self.leader}. Group ID: {self.group_id}")

    @property
    def leader_object(self):
        """Returns the leader's db_object if it exists, otherwise None."""
        return self.leader.db_object if self.leader else None
    
    @property
    def channel_name(self):
        """Returns the channel name for this group."""
        # Remove spaces and special characters
        return ''.join(c for c in self.name if c.isalnum())

class GroupRole(SharedMemoryModel):
    name = models.CharField(max_length=50)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='roles')
    can_invite = models.BooleanField(default=False)
    can_kick = models.BooleanField(default=False)
    can_promote = models.BooleanField(default=False)
    can_edit_info = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.group.name}"

class GroupMembership(SharedMemoryModel):
    character = models.ForeignKey(CharacterSheet, on_delete=models.CASCADE, related_name='group_memberships')
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    role = models.ForeignKey(GroupRole, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=100, blank=True, help_text="Character's title in the group")

    class Meta:
        unique_together = ('character', 'group')

    def __str__(self):
        title_str = f" ({self.title})" if self.title else ""
        role_str = f" - {self.role.name}" if self.role else ""
        return f"{self.character.full_name}{title_str} - {self.group.name}{role_str}"

class GroupJoinRequest(SharedMemoryModel):
    character = models.ForeignKey(CharacterSheet, on_delete=models.CASCADE, related_name='join_requests')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='join_requests')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('character', 'group')

    def __str__(self):
        return f"{self.character.full_name} - {self.group.name}"

class CharacterGroupInfo(TypedObject):
    """
    This model stores additional group and faction information for characters.
    This is separate from GroupMembership and represents custom character-specific
    group information that doesn't fit in the standard group system.
    """
    db_character = models.OneToOneField('objects.ObjectDB', related_name='group_info', on_delete=models.CASCADE)
    db_group_description = models.TextField(blank=True, default="", help_text="Character's personal group information")
    db_faction_description = models.TextField(blank=True, default="", help_text="Character's faction information")

    class Meta:
        verbose_name = "Character Group Info"
        verbose_name_plural = "Character Group Data"

    def __str__(self):
        return f"Group Info for {self.db_character}"