"""
Models for the World of Darkness 20th Anniversary Edition game.
"""
import re
from django.db import models
from django.db.models import JSONField  # Use the built-in JSONField
from django.forms import ValidationError
from evennia.locks.lockhandler import LockHandler
from django.conf import settings
from evennia.accounts.models import AccountDB
from evennia.objects.models import ObjectDB
from evennia.utils.idmapper.models import SharedMemoryModel
from typing import Dict, List, Union, Optional, Any

from world.wod20th.utils.stat_mappings import CATEGORIES, STAT_TYPES
from world.wod20th.utils.shifter_utils import (
    SHIFTER_RENOWN, SHIFTER_TYPE_CHOICES, AUSPICE_CHOICES,
    BASTET_TRIBE_CHOICES, BREED_CHOICES, GAROU_TRIBE_CHOICES
)
from world.wod20th.utils.vampire_utils import get_clan_disciplines
from world.wod20th.utils.mortalplus_utils import (
    MORTALPLUS_TYPE_CHOICES, validate_mortalplus_powers, can_learn_power
)
from world.wod20th.utils.asset_utils import Asset, ActionTemplate, Action

def get_character_models():
    """Get the CharacterSheet and CharacterImage models lazily."""
    return CharacterSheet, CharacterImage

class Stat(models.Model):
    """Model for storing game statistics."""
    name = models.CharField(max_length=100)
    description = models.TextField(default='')  # Changed to non-nullable with default empty string
    game_line = models.CharField(max_length=100)
    category = models.CharField(max_length=100, choices=CATEGORIES)
    stat_type = models.CharField(max_length=100, choices=STAT_TYPES)
    values = JSONField(default=list, blank=True, null=True)
    lock_string = models.CharField(max_length=255, blank=True, null=True)
    splat = models.CharField(max_length=100, blank=True, null=True, default=None)
    xp_cost = models.IntegerField(default=0, blank=True, null=True)
    prerequisites = models.CharField(max_length=100, blank=True, null=True)
    notes = models.CharField(max_length=100, blank=True, null=True)
    shifter_type = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="List of shifter types that can learn this gift"
    )
    gift_alias = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="List of alternative names for this gift"
    )
    hidden = models.BooleanField(default=False)
    locked = models.BooleanField(default=False)
    instanced = models.BooleanField(default=None, null=True, help_text="If True, requires an instance. If False, disallows instances. If null, instances are optional.")
    default = models.CharField(max_length=100, blank=True, null=True, default=None)
    auspice = models.CharField(
        max_length=100,
        choices=AUSPICE_CHOICES,
        default='none',
        blank=True
    )
    breed = models.CharField(
        max_length=100,
        choices=BREED_CHOICES,
        default='none',
        blank=True
    )
    tribe = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="List of tribes that can learn this gift"
    )
    camp = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Specific camp that can learn this gift"
    )
    source = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Source book reference"
    )
    system = models.TextField(
        blank=True,
        null=True,
        help_text="Game mechanics description"
    )
    mortalplus_type = models.CharField(
        max_length=100,
        choices=MORTALPLUS_TYPE_CHOICES,
        default='none',
        blank=True,
        help_text="Type of Mortal+ character"
    )
    guildmarks = models.CharField(
        max_length=200,
        default='none',
        blank=True,
        null=True,
        help_text="Type of guildmarks"
    )
    
    class Meta:
        app_label = 'wod20th'
        unique_together = ('name', 'category', 'stat_type', 'splat')
        
    def __str__(self):
        return f"{self.name} ({self.category}/{self.stat_type})"

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

    def save(self, *args, **kwargs):
        if self.stat_type == 'renown':
            # Ensure renown stats use the dual value structure
            if self.name in SHIFTER_RENOWN:
                self.values = SHIFTER_RENOWN[self.name]
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        # Get the splat type
        splat = self.splat.lower() if self.splat else None
        
        # Validate type field based on splat
        if splat == 'shifter' and self.shifter_type:
            if not isinstance(self.shifter_type, list):
                raise ValidationError({'shifter_type': 'Must be a list'})
            valid_types = [choice[0] for choice in SHIFTER_TYPE_CHOICES]
            for type in self.shifter_type:
                if type.lower() not in valid_types and type.lower() != 'none':
                    raise ValidationError({'shifter_type': f'Invalid shifter type: {type}'})
                
        elif splat == 'mortal+' and self.mortalplus_type:
            if not isinstance(self.mortalplus_type, str):
                raise ValidationError({'mortalplus_type': 'Must be a string'})
            valid_types = [choice[0] for choice in MORTALPLUS_TYPE_CHOICES]
            if self.mortalplus_type.lower() not in valid_types and self.mortalplus_type.lower() != 'none':
                raise ValidationError({'mortalplus_type': f'Invalid Mortal+ type: {self.mortalplus_type}'})

        # Validate tribe field contains valid choices if present
        if self.tribe:
            if not isinstance(self.tribe, (list, str)):
                raise ValidationError({'tribe': 'Must be a list or string'})
            if isinstance(self.tribe, str):
                self.tribe = [self.tribe]
            valid_tribes = [choice[0] for choice in GAROU_TRIBE_CHOICES]
            for tribe in self.tribe:
                if tribe.lower() not in valid_tribes and tribe.lower() != 'none':
                    raise ValidationError({'tribe': f'Invalid tribe: {tribe}'})

class CharacterSheet(SharedMemoryModel):
    """Model for storing character sheets."""
    account = models.OneToOneField(AccountDB, related_name='character_sheet', on_delete=models.CASCADE, null=True)
    character = models.OneToOneField(ObjectDB, related_name='character_sheet', on_delete=models.CASCADE, null=True, unique=True)
    db_object = models.OneToOneField('objects.ObjectDB', related_name='db_character_sheet', on_delete=models.CASCADE, null=True)

    class Meta:
        app_label = 'wod20th'

    def get_stat(self, category: str, stat_type: str, stat_name: str, temp: bool = False) -> Optional[Any]:
        """Get a stat value from the character's stats."""
        try:
            if not hasattr(self.character, 'db') or not hasattr(self.character.db, 'stats'):
                return None
            
            stat_dict = self.character.db.stats.get(category, {}).get(stat_type, {})
            if not stat_dict:
                return None
            
            stat_value = stat_dict.get(stat_name, {})
            if isinstance(stat_value, dict) and 'temp' in stat_value and 'perm' in stat_value:
                return stat_value['temp'] if temp else stat_value['perm']
            return stat_value
        except (AttributeError, KeyError):
            return None

    def set_stat(self, category: str, stat_type: str, stat_name: str, value: Any, temp: bool = False) -> None:
        """Set a stat value in the character's stats."""
        if not hasattr(self.character, 'db') or not hasattr(self.character.db, 'stats'):
            self.character.db.stats = {}
        
        if category not in self.character.db.stats:
            self.character.db.stats[category] = {}
        if stat_type not in self.character.db.stats[category]:
            self.character.db.stats[category][stat_type] = {}
            
        current_value = self.character.db.stats[category][stat_type].get(stat_name, {})
        if isinstance(current_value, dict) and ('temp' in current_value or 'perm' in current_value):
            if temp:
                current_value['temp'] = value
            else:
                current_value['perm'] = value
                if 'temp' not in current_value:
                    current_value['temp'] = value
            self.character.db.stats[category][stat_type][stat_name] = current_value
        else:
            if temp:
                self.character.db.stats[category][stat_type][stat_name] = {'perm': current_value, 'temp': value}
            else:
                self.character.db.stats[category][stat_type][stat_name] = value

    def get_all_stats(self, category: Optional[str] = None, stat_type: Optional[str] = None) -> Dict[str, Any]:
        """Get all stats for a category and/or type."""
        if not hasattr(self.character, 'db') or not hasattr(self.character.db, 'stats'):
            return {}
        
        if category and stat_type:
            return self.character.db.stats.get(category, {}).get(stat_type, {})
        elif category:
            return self.character.db.stats.get(category, {})
        return self.character.db.stats

def calculate_willpower(character):
    """Calculate Willpower based on virtues."""
    try:
        # Get the character's virtues
        virtues = character.db.stats.get('virtues', {}).get('moral', {})
        
        # Get Courage value (common to all paths)
        courage = virtues.get('Courage', {}).get('perm', 0)
        
        # Get the other relevant virtue based on path
        enlightenment = character.get_stat('identity', 'personal', 'Enlightenment')
        
        if enlightenment and enlightenment != 'Humanity':
            # For most non-Humanity paths
            conviction = virtues.get('Conviction', {}).get('perm', 0)
            willpower = courage + conviction
        else:
            # For Humanity and paths using Conscience
            conscience = virtues.get('Conscience', {}).get('perm', 0)
            willpower = courage + conscience
            
        return willpower if willpower > 0 else 1
        
    except (AttributeError, KeyError):
        return 1

def calculate_road(character):
    """Calculate Road value based on virtues."""
    enlightenment = character.get_stat('identity', 'personal', 'Enlightenment', temp=False)
    virtues = character.db.stats.get('virtues', {}).get('moral', {})

    path_virtues = {
        'Humanity': ('Conscience', 'Self-Control'),
        'Night': ('Conviction', 'Instinct'),
        'Beast': ('Conviction', 'Instinct'),
        'Harmony': ('Conscience', 'Instinct'),
        'Evil Revelations': ('Conviction', 'Self-Control'),
        'Self-Focus': ('Conviction', 'Instinct'),
        'Scorched Heart': ('Conviction', 'Self-Control'),
        'Entelechy': ('Conviction', 'Self-Control'),
        'Sharia El-Sama': ('Conscience', 'Self-Control'),
        'Asakku': ('Conviction', 'Instinct'),
        'Death and the Soul': ('Conviction', 'Self-Control'),
        'Honorable Accord': ('Conscience', 'Self-Control'),
        'Feral Heart': ('Conviction', 'Instinct'),
        'Orion': ('Conviction', 'Instinct'),
        'Power and the Inner Voice': ('Conviction', 'Instinct'),
        'Lilith': ('Conviction', 'Instinct'),
        'Caine': ('Conviction', 'Instinct'),
        'Cathari': ('Conviction', 'Instinct'),
        'Redemption': ('Conscience', 'Self-Control'),
        'Metamorphosis': ('Conviction', 'Instinct'),
        'Bones': ('Conviction', 'Self-Control'),
        'Typhon': ('Conviction', 'Self-Control'),
        'Paradox': ('Conviction', 'Self-Control'),
        'Blood': ('Conviction', 'Self-Control'),
        'Hive': ('Conviction', 'Instinct')
    }

    if enlightenment in path_virtues:
        virtue1, virtue2 = path_virtues[enlightenment]
        value1 = virtues.get(virtue1, {}).get('perm', 0)
        value2 = virtues.get(virtue2, {}).get('perm', 0)
        return value1 + value2
    else:
        # If the enlightenment is not recognized, return 0 or a default value
        return 0

class ShapeshifterForm(models.Model):
    """Model for storing shapeshifter forms."""
    name = models.CharField(max_length=50)
    shifter_type = models.CharField(max_length=50)
    description = models.TextField()
    stat_modifiers = models.JSONField(default=dict)
    rage_cost = models.IntegerField(default=0)
    difficulty = models.IntegerField(default=6)
    lock_string = models.CharField(max_length=255, default='examine:all();control:perm(Admin)')

    class Meta:
        app_label = 'wod20th'
        unique_together = ('name', 'shifter_type')

    def __str__(self):
        return f"{self.shifter_type.capitalize()} - {self.name}"

    def clean(self):
        # Validate stat_modifiers
        if not isinstance(self.stat_modifiers, dict):
            raise ValidationError({'stat_modifiers': 'Must be a dictionary'})
        for key, value in self.stat_modifiers.items():
            if not isinstance(key, str) or not isinstance(value, int):
                raise ValidationError({'stat_modifiers': 'Keys must be strings and values must be integers'})

        # Validate difficulty
        if self.difficulty < 1 or self.difficulty > 10:
            raise ValidationError({'difficulty': 'Difficulty must be between 1 and 10'})

        # Allow underscores in form names
        if not re.match(r'^[\w\s_-]+$', self.name):
            raise ValidationError({'name': 'Form name can only contain letters, numbers, spaces, underscores, and hyphens'})

    def save(self, *args, **kwargs):
        self.clean()
        self.shifter_type = self.sanitize_shifter_type(self.shifter_type)
        super().save(*args, **kwargs)

    @staticmethod
    def sanitize_shifter_type(shifter_type):
        # Convert to lowercase and remove any non-alphanumeric characters except spaces and underscores
        sanitized = re.sub(r'[^\w\s_]', '', shifter_type.lower())
        # Replace spaces with underscores
        return re.sub(r'\s+', '_', sanitized)

class CharacterImage(SharedMemoryModel):
    """Model for storing character images."""
    character = models.ForeignKey('objects.ObjectDB', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='character_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        app_label = 'wod20th'
        ordering = ['-is_primary', '-uploaded_at']

    def save(self, *args, **kwargs):
        """Ensure only one primary image per character."""
        if self.is_primary:
            # Set all other images of this character to not primary
            CharacterImage.objects.filter(
                character=self.character,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Clean up the image file when deleting the model."""
        self.image.delete(save=False)
        super().delete(*args, **kwargs)

class MokoleArchidTrait(models.Model):
    """Model for storing Mokolé Archid form traits."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    can_stack = models.BooleanField(default=False)  # For traits that can be taken multiple times
    stat_modifiers = models.JSONField(default=dict)  # For storing stat modifications
    special_rules = models.TextField(blank=True, null=True)  # For any special rules or mechanics
    
    class Meta:
        app_label = 'wod20th'
        ordering = ['name']

    def __str__(self):
        return self.name

    @classmethod
    def initialize_default_traits(cls):
        """Initialize the default Archid traits."""
        default_traits = {
            'Armored Scales': {
                'description': '+2 Soak.',
                'can_stack': True,
                'stat_modifiers': {'soak': 2},
            },
            'Behemoth': {
                'description': 'Body mass doubles, height remains same. Stamina +1, +2 damage to Body Slam or Tackle attempts.',
                'can_stack': True,
                'stat_modifiers': {'stamina': 1},
                'special_rules': '+2 damage to Body Slam or Tackle attempts'
            },
            'Binocular Vision': {
                'description': '+2 on all visual-based Perception rolls. -2 to opponents attempts to surprise.',
                'can_stack': False,
                'stat_modifiers': {'perception': 2},
                'special_rules': '+2 visual Perception, -2 to surprise'
            },
            'Bladed Tail': {
                'description': 'Gains a tail lash maneuver (Str +2 aggravated damage, difficulty 7).',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': 'Tail lash: Str +2 aggravated, diff 7'
            },
            'Color Change': {
                'description': '+1 difficulty to spot the Mokolé while hiding.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': '+1 difficulty to spot while hiding'
            },
            'Constricting Coils': {
                'description': '+3 dice to attempts to immobilize target.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': '+3 dice to immobilize'
            },
            'Deep Lung': {
                'description': 'Can swim underwater for up to an hour or hold breath up to 5 minutes in combat.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': 'Extended underwater breathing'
            },
            'Fiery Pearl': {
                'description': '+3 to Intimidate versus vampires and wyrm creatures.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': '+3 Intimidate vs vampires/wyrm'
            },
            'Fins': {
                'description': 'Double swimming speed.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': 'Double swim speed'
            },
            'Fire Breath': {
                'description': 'Can breathe fire (or corrosive aerosol) once per day. Fire has soak difficulty 7, damage 2 per turn, extends (Rage) yards.',
                'can_stack': True,
                'stat_modifiers': {},
                'special_rules': 'Fire breath: diff 7 soak, 2 damage/turn'
            },
            'Gills': {
                'description': 'Fully amphibious.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': 'Can breathe underwater'
            },
            'Grasping Hands': {
                'description': 'Normal manual dexterity in Archid form.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': 'Full manual dexterity'
            },
            'Hinged Jaw': {
                'description': 'May extend jaw to swallow (non-resisting) objects up to Archid form\'s Size.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': 'Can swallow large objects'
            },
            'Hollow Bones': {
                'description': 'Bones are hollow but strong. +3 to Dexterity for movement, may soar effortlessly for hours with Wings.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': '+3 Dexterity for movement'
            },
            'Horn': {
                'description': 'Gains a gore maneuver (Str +2 aggravated damage, difficulty 7).',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': 'Gore: Str +2 aggravated, diff 7'
            },
            'Long Neck': {
                'description': 'Can attack targets up to 10 feet away with Bite attack.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': 'Extended bite range'
            },
            'Long Teeth': {
                'description': 'Bite damage is increased to Strength +3.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': 'Bite damage Str +3'
            },
            'Long Tongue': {
                'description': 'Tongue is as long as Archid body, has Strength 1 and Dexterity equal to Mokolé\'s Dexterity.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': 'Prehensile tongue'
            },
            'Poison Sacs': {
                'description': 'May inject poison once per day. On successful bite, victim must soak four additional dice of poison damage.',
                'can_stack': True,
                'stat_modifiers': {},
                'special_rules': 'Poison: +4 damage dice on bite'
            },
            'Predator\'s Roar': {
                'description': 'Gains roar attack usable once per scene. All characters within close combat range must roll Willpower (difficulty equal to Mokolé\'s Rage) or flee.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': 'Fear-inducing roar'
            },
            'Prehensile Tail': {
                'description': 'May use as if it was a hand, including wielding a weapon. Normal attack limits apply.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': 'Tail can be used as hand'
            },
            'Resplendent Crest': {
                'description': '+3 appearance and +1 charisma in Archid form.',
                'can_stack': False,
                'stat_modifiers': {'appearance': 3, 'charisma': 1},
                'special_rules': '+3 appearance, +1 charisma'
            },
            'Royal Crest': {
                'description': '+2 to Social rolls involving Nagah or any Mokolé stream.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': '+2 Social with Nagah/Mokole'
            },
            'Sickening Slime': {
                'description': 'Any opponent that bites you loses their next full turn retching. -2 to non-Mokolé Social interactions.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': 'Bite causes retching, -2 Social'
            },
            'Tall': {
                'description': 'Body mass and height doubles, +1 Stamina. Can reach/see over obstacles more easily. +2 to Perception when appropriate.',
                'can_stack': True,
                'stat_modifiers': {'stamina': 1},
                'special_rules': '+2 Perception for height'
            },
            'Terrible Claws': {
                'description': 'Claw damage increases to Strength +3.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': 'Claw damage Str +3'
            },
            'Tongue Flick': {
                'description': '+2 to tracking rolls involving scent.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': '+2 scent tracking'
            },
            'Upright Walking': {
                'description': 'Frees up forelimbs when walking.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': 'Bipedal movement'
            },
            'Webbed Feet': {
                'description': 'May swim at 150% speed and walk without trouble on soft surfaces.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': '150% swim speed'
            },
            'Wings': {
                'description': 'Can fly at 20mph for 1 hour per point of Stamina, then must rest for 8 hours.',
                'can_stack': False,
                'stat_modifiers': {},
                'special_rules': 'Flight capability'
            }
        }
        
        for name, data in default_traits.items():
            cls.objects.get_or_create(
                name=name,
                defaults={
                    'description': data['description'],
                    'can_stack': data['can_stack'],
                    'stat_modifiers': data.get('stat_modifiers', {}),
                    'special_rules': data.get('special_rules', '')
                }
            )

class CharacterArchidTrait(models.Model):
    """Model for tracking which Archid traits a character has."""
    character = models.ForeignKey('objects.ObjectDB', on_delete=models.CASCADE, related_name='archid_traits')
    trait = models.ForeignKey(MokoleArchidTrait, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=1)  # For stacking traits
    approved = models.BooleanField(default=False)  # For tracking approval status
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_archid_traits'
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        app_label = 'wod20th'
        unique_together = ('character', 'trait')
        ordering = ['trait__name']

    def __str__(self):
        return f"{self.character.name}'s {self.trait.name} ({self.count})"

    def save(self, *args, **kwargs):
        # Get total traits count (both approved and unapproved)
        total_traits = sum(
            ct.count for ct in CharacterArchidTrait.objects.filter(
                character=self.character
            ).exclude(id=self.id)
        ) + self.count
            
        # Get character's permanent Gnosis
        try:
            gnosis = self.character.db.stats['pools']['dual']['Gnosis']['perm']
        except (AttributeError, KeyError):
            gnosis = 0
                
        if total_traits > gnosis:
            raise ValidationError(f"Cannot exceed Gnosis limit ({gnosis}) for Archid traits. Current total would be {total_traits}.")
        
        super().save(*args, **kwargs) 

from django.contrib.auth.models import User
from django.db import models
from django.conf import settings

class Roster(models.Model):
    """Model for managing character rosters."""
    SPHERE_CHOICES = [
        ('mage', 'Mage'),
        ('vampire', 'Vampire'),
        ('werewolf', 'Werewolf'),
        ('changeling', 'Changeling'),
        ('hunter', 'Hunter'),
        ('wraith', 'Wraith'),
        ('demon', 'Demon'),
        ('mortal', 'Mortal'),
        ('other', 'Other')
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    sphere = models.CharField(max_length=50, choices=SPHERE_CHOICES, default='other')
    website = models.URLField(blank=True)
    admins = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='administered_rosters',
        blank=True
    )
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='managed_rosters',
        blank=True
    )
    hangouts = models.ManyToManyField(
        'objects.ObjectDB',
        related_name='roster_hangouts',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'wod20th'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_members(self):
        """Get all approved members of this roster."""
        return self.members.filter(approved=True)

    def get_online_members(self):
        """Get all online approved members of this roster."""
        return self.members.filter(
            approved=True,
            character__db_account__db_is_connected=True
        )

    def can_manage(self, account):
        """Check if an account can manage this roster."""
        if not account:
            return False
        return (
            account.is_staff or 
            self.admins.filter(id=account.id).exists() or 
            self.managers.filter(id=account.id).exists()
        )

class RosterMember(models.Model):
    """Model for tracking character membership in rosters."""
    roster = models.ForeignKey(
        Roster,
        on_delete=models.CASCADE,
        related_name='members'
    )
    character = models.ForeignKey(
        'objects.ObjectDB',
        on_delete=models.CASCADE,
        related_name='roster_memberships'
    )
    title = models.CharField(max_length=255, blank=True)
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_roster_members'
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'wod20th'
        unique_together = ('roster', 'character')
        ordering = ['character__db_key']

    def __str__(self):
        return f"{self.character} in {self.roster}" 