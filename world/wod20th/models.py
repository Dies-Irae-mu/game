# mygame/server/conf/models.py
from django.db import models
from django.db.models import JSONField  # Use the built-in JSONField
from evennia.locks.lockhandler import LockHandler

# Define predefined categories and extended stat types
CATEGORIES = [
    ('attributes', 'Attributes'),
    ('abilities', 'Abilities'),
    ('advantages', 'Advantages'),
    ('backgrounds', 'Backgrounds'),
    ('powers', 'Powers'),
    ('merits', 'Merits'),
    ('flaws', 'Flaws'),
    ('traits', 'Traits'),
    ('identity', 'Identity'),
    ('virtues', 'Virtues'),
    ('pools', 'Pools'),
    ('other', 'Other')
]

STAT_TYPES = [
    ('attribute', 'Attribute'),
    ('ability', 'Ability'),
    ('advantage', 'Advantage'),
    ('background', 'Background'),
    ('lineage', 'Lineage'),
    ('discipline', 'Discipline'),
    ('gift', 'Gift'),
    ('sphere', 'Sphere'),
    ('rote', 'Rote'),
    ('art', 'Art'),
    ('splat', 'Splat'),
    ('edge', 'Edge'),
    ('discipline', 'Discipline'),
    ('path', 'Path'),
    ('power', 'Power'),
    ('other', 'Other'),
    ('virtue', 'Virtue'),
    ('vice', 'Vice'),
    ('merit', 'Merit'),
    ('flaw', 'Flaw'),
    ('trait', 'Trait'),
    ('skill', 'Skill'),
    ('knowledge', 'Knowledge'),
    ('knowlege-secondary', 'Secondary Knowledge'),
    ('telent-secondary', 'Secondary Talent'),
    ('skill-secondary', 'Secondary Skill'),
    ('talent', 'Talent'),
    ('specialty', 'Specialty'),
    ('other', 'Other'),
    ('physical', 'Physical'),
    ('social', 'Social'),
    ('mental', 'Mental'),
    ('personal', 'Personal'),
    ('supernatural', 'Supernatural'),
    ('moral', 'Moral'),
    ('inhuman', 'Inhuman'),
    ('temporary', 'Temporary'),
    ('other', 'Other')
]

class Stat(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(default='')  # Changed to non-nullable with default empty string
    game_line = models.CharField(max_length=100)
    category = models.CharField(max_length=100, choices=CATEGORIES)
    stat_type = models.CharField(max_length=100, choices=STAT_TYPES)
    values = JSONField(default=list, blank=True, null=True)
    lock_string = models.CharField(max_length=255, blank=True, null=True)
    splat = models.CharField(max_length=100, blank=True, null=True, default=None)
    hidden = models.BooleanField(default=False)
    locked = models.BooleanField(default=False)
    instanced = models.BooleanField(default=False, null=True)

    
    def __str__(self):
        return self.name

    @property
    def lock_storage(self):
        """
        Mimics the lock_storage attribute expected by LockHandler.
        """
        return self.lock_string or ""

    def can_access(self, accessing_obj, access_type):
        """
        Check if the accessing_obj can access this Stat based on the lock_string.
        """
        # Create a temporary lock handler to handle the lock check
        temp_lock_handler = LockHandler(self)
        
        # Perform the access check
        return temp_lock_handler.check(accessing_obj, access_type)
    