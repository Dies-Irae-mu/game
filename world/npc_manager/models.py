"""
Database models for NPCs and NPC Groups.

These models store persistent data for NPCs and NPC Groups, complementing
the typeclasses that handle in-game behavior.
"""

from django.db import models
from django.conf import settings
from evennia.utils.idmapper.models import SharedMemoryModel
from evennia.typeclasses.models import TypedObject
from evennia.objects.models import ObjectDB
import uuid
from datetime import datetime

# Difficulty choices
DIFFICULTY_CHOICES = (
    ('LOW', 'Low'),
    ('MEDIUM', 'Medium'),
    ('HIGH', 'High'),
)

# Splat choices
SPLAT_CHOICES = (
    ('mortal', 'Mortal'),
    ('vampire', 'Vampire'),
    ('mage', 'Mage'),
    ('shifter', 'Shifter'),
    ('changeling', 'Changeling'),
    ('hunter', 'Hunter'),
    ('demon', 'Demon'),
    ('wraith', 'Wraith'),
    ('mummy', 'Mummy'),
    ('psychic', 'Psychic'),
    ('mortal+', 'Mortal+'),
    ('spirit', 'Spirit'),
)


class NPCGroup(SharedMemoryModel):
    """
    Model for storing NPC Group data.
    
    This model stores the static data for an NPC Group, while the NPCGroup
    typeclass handles the in-game behavior.
    """
    # Basic information
    db_key = models.CharField(max_length=255, verbose_name="Name")
    db_group_type = models.CharField(max_length=100, default="Generic", verbose_name="Group Type")
    db_splat = models.CharField(max_length=20, choices=SPLAT_CHOICES, default="mortal", verbose_name="Default Splat")
    db_difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default="MEDIUM", verbose_name="Default Difficulty")
    db_description = models.TextField(blank=True, verbose_name="Description")
    
    # Group details
    db_territory = models.CharField(max_length=255, blank=True, verbose_name="Territory")
    db_resources = models.PositiveSmallIntegerField(default=0, verbose_name="Resources")
    db_influence = models.PositiveSmallIntegerField(default=0, verbose_name="Influence")
    
    # Linking fields
    db_object = models.OneToOneField(
        ObjectDB, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        verbose_name="Game Object"
    )
    db_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Meta fields
    db_date_created = models.DateTimeField(auto_now_add=True)
    db_last_modified = models.DateTimeField(auto_now=True)
    db_creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_npc_groups",
        verbose_name="Creator"
    )
    
    class Meta:
        """Define Django meta options."""
        verbose_name = "NPC Group"
        verbose_name_plural = "NPC Groups"
        ordering = ["db_key"]
    
    def __str__(self):
        return f"{self.db_key} ({self.db_group_type})"
    
    @property
    def object(self):
        """Get the in-game object (NPCGroup typeclass)."""
        return self.db_object
    
    @property
    def typeclass(self):
        """Return typeclass if it exists, or None."""
        if self.db_object:
            return self.db_object
        return None
        
    def create_in_game_group(self, location=None):
        """
        Create an in-game NPCGroup object linked to this model.
        
        Args:
            location: Optional location for the NPCGroup object
        
        Returns:
            The created NPCGroup object
        """
        if self.db_object:
            return self.db_object
            
        # Import create here to avoid circular imports
        from evennia.utils import create
            
        # Create the NPCGroup object
        from typeclasses.npc_groups import NPCGroup
        group = create.create_object(
            NPCGroup,
            key=self.db_key,
            location=location,
            attributes=[
                ("group_id", str(self.db_uuid)),
                ("group_type", self.db_group_type),
                ("splat", self.db_splat),
                ("difficulty", self.db_difficulty),
                ("desc", self.db_description),
                ("territory", self.db_territory),
                ("resources", self.db_resources),
                ("influence", self.db_influence),
            ],
        )
        
        # Link back to this model
        self.db_object = group
        self.save()
        
        return group
    
    def get_goals(self):
        """Get the group's goals."""
        return NPCGoal.objects.filter(npc_group=self).order_by('db_order')
    
    def get_npcs(self):
        """Get all NPCs in this group."""
        return NPC.objects.filter(db_group=self)
    
    def get_hierarchy(self):
        """Get the group hierarchy structure."""
        return NPCPosition.objects.filter(npc_group=self).select_related('npc')


class NPCGoal(SharedMemoryModel):
    """
    Goals for NPC Groups.
    """
    npc_group = models.ForeignKey(
        NPCGroup, 
        on_delete=models.CASCADE, 
        related_name='goals',
        verbose_name="NPC Group"
    )
    db_text = models.TextField(verbose_name="Goal Text")
    db_order = models.PositiveSmallIntegerField(default=0, verbose_name="Order")
    db_completed = models.BooleanField(default=False, verbose_name="Completed")
    
    class Meta:
        """Define Django meta options."""
        verbose_name = "NPC Goal"
        verbose_name_plural = "NPC Goals"
        ordering = ["npc_group", "db_order"]
    
    def __str__(self):
        return f"{self.npc_group.db_key}: {self.db_text[:30]}..."


class NPC(SharedMemoryModel):
    """
    Model for storing NPC data.
    
    This model stores the static data for an NPC, while the NPC
    typeclass handles the in-game behavior.
    """
    # Basic information
    db_key = models.CharField(max_length=255, verbose_name="Name")
    db_splat = models.CharField(max_length=20, choices=SPLAT_CHOICES, default="mortal", verbose_name="Splat")
    db_difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default="MEDIUM", verbose_name="Difficulty")
    db_description = models.TextField(blank=True, verbose_name="Description")
    
    # NPC Status
    db_is_temporary = models.BooleanField(default=False, verbose_name="Temporary")
    db_expiration_time = models.DateTimeField(null=True, blank=True, verbose_name="Expiration Time")
    
    # Group membership
    db_group = models.ForeignKey(
        NPCGroup, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='npcs',
        verbose_name="NPC Group"
    )
    db_group_number = models.PositiveIntegerField(null=True, blank=True, verbose_name="Group Number")
    
    # Linking fields
    db_object = models.OneToOneField(
        ObjectDB, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        verbose_name="Game Object"
    )
    db_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Meta fields
    db_date_created = models.DateTimeField(auto_now_add=True)
    db_last_modified = models.DateTimeField(auto_now=True)
    db_creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_npcs",
        verbose_name="Creator"
    )
    
    class Meta:
        """Define Django meta options."""
        verbose_name = "NPC"
        verbose_name_plural = "NPCs"
        ordering = ["db_key"]
    
    def __str__(self):
        """String representation."""
        status = " (Temp)" if self.db_is_temporary else ""
        if self.db_group:
            return f"{self.db_key} - {self.db_group.db_key}{status}"
        return f"{self.db_key}{status}"
    
    @property
    def object(self):
        """Get the in-game object (NPC typeclass)."""
        return self.db_object
    
    @property
    def typeclass(self):
        """Return typeclass if it exists, or None."""
        if self.db_object:
            return self.db_object
        return None
        
    def create_in_game_npc(self, location=None):
        """
        Create an in-game NPC object linked to this model.
        
        Args:
            location: Optional location for the NPC object
        
        Returns:
            The created NPC object
        """
        if self.db_object:
            return self.db_object
            
        # Import create here to avoid circular imports
        from evennia.utils import create
            
        # Create the NPC object
        from typeclasses.npcs import NPC
        npc = create.create_object(
            NPC,
            key=self.db_key,
            location=location,
            attributes=[
                ("npc_id", str(self.db_uuid)),
                ("is_temporary", self.db_is_temporary),
                ("desc", self.db_description),
                ("expiration_time", self.db_expiration_time),
            ],
        )
        
        # Initialize stats
        npc.initialize_npc_stats(self.db_splat, self.db_difficulty)
        
        # Link back to this model
        self.db_object = npc
        self.save()
        
        # Link to group if specified
        if self.db_group and self.db_group.object:
            self.db_group.object.add_npc(npc)
        
        return npc


class NPCPosition(SharedMemoryModel):
    """
    Positions/roles within an NPC Group hierarchy.
    """
    npc_group = models.ForeignKey(
        NPCGroup, 
        on_delete=models.CASCADE, 
        related_name='positions',
        verbose_name="NPC Group"
    )
    npc = models.ForeignKey(
        NPC,
        on_delete=models.CASCADE,
        related_name='positions',
        verbose_name="NPC"
    )
    db_title = models.CharField(max_length=100, verbose_name="Position Title")
    db_description = models.TextField(blank=True, verbose_name="Position Description")
    db_order = models.PositiveSmallIntegerField(default=0, verbose_name="Hierarchy Order")
    
    class Meta:
        """Define Django meta options."""
        verbose_name = "NPC Position"
        verbose_name_plural = "NPC Positions"
        ordering = ["npc_group", "db_order", "db_title"]
        unique_together = [['npc_group', 'npc']]
    
    def __str__(self):
        return f"{self.npc.db_key}: {self.db_title} ({self.npc_group.db_key})" 