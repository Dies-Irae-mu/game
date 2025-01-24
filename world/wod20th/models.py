# mygame/server/conf/models.py
import re
from django.db import models
from django.db.models import JSONField  # Use the built-in JSONField
from django.forms import ValidationError
from evennia.locks.lockhandler import LockHandler
from django.conf import settings
from evennia.accounts.models import AccountDB
from evennia.objects.models import ObjectDB
from evennia.utils.idmapper.models import SharedMemoryModel
from typing import Dict, List, Union

# Define predefined categories and extended stat types
CATEGORIES = [
    ('attributes', 'Attributes'),
    ('abilities', 'Abilities'),
    ('secondary_abilities', 'Secondary Abilities'),
    ('advantages', 'Advantages'),
    ('backgrounds', 'Backgrounds'),
    ('powers', 'Powers'),
    ('merits', 'Merits'),
    ('flaws', 'Flaws'),
    ('traits', 'Traits'),
    ('identity', 'Identity'),
    ('archetype', 'Archetype'),
    ('virtues', 'Virtues'),
    ('legacy', 'Legacy'),
    ('pools', 'Pools'),
    ('other', 'Other')
]

STAT_TYPES = [
    ('attribute', 'Attribute'),
    ('ability', 'Ability'),
    ('secondary_ability', 'Secondary Ability'),
    ('advantage', 'Advantage'),
    ('background', 'Background'),
    ('lineage', 'Lineage'),
    ('discipline', 'Discipline'),
    ('combodiscipline', 'Combo Discipline'),
    ('thaumaturgy', 'Thaumaturgy'),
    ('gift', 'Gift'),
    ('rite', 'Rite'),
    ('sphere', 'Sphere'),
    ('rote', 'Rote'),
    ('art', 'Art'),
    ('splat', 'Splat'),
    ('edge', 'Edge'),
    ('bygone_power', 'Bygone Power'),
    ('discipline', 'Discipline'),
    ('realm', 'Realm'),
    ('sphere', 'Sphere'),
    ('art', 'Art'),
    ('path', 'Path'),
    ('sorcery', 'Sorcery'),
    ('faith', 'Faith'),
    ('numina', 'Numina'),
    ('enlightenment', 'Enlightenment'),
    ('power', 'Power'),
    ('other', 'Other'),
    ('virtue', 'Virtue'),
    ('vice', 'Vice'),
    ('merit', 'Merit'),
    ('flaw', 'Flaw'),
    ('trait', 'Trait'),
    ('skill', 'Skill'),
    ('knowledge', 'Knowledge'),
    ('talent', 'Talent'),
    ('secondary_knowledge', 'Secondary Knowledge'),
    ('secondary_talent', 'Secondary Talent'),
    ('secondary_skill', 'Secondary Skill'),
    ('specialty', 'Specialty'),
    ('other', 'Other'),
    ('physical', 'Physical'),
    ('social', 'Social'),
    ('mental', 'Mental'),
    ('personal', 'Personal'),
    ('supernatural', 'Supernatural'),
    ('moral', 'Moral'),
    ('temporary', 'Temporary'),
    ('dual', 'Dual'),
    ('renown', 'Renown'),
    ('arete', 'Arete'),
    ('banality', 'Banality'),
    ('glamour', 'Glamour'),
    ('essence', 'Essence'),
    ('quintessence', 'Quintessence'),
    ('blood', 'Blood'),
    ('rage', 'Rage'),
    ('gnosis', 'Gnosis'),
    ('willpower', 'Willpower'),
    ('resonance', 'Resonance'),
    ('synergy', 'Synergy'),
    ('paradox', 'Paradox'),
    ('kith', 'Kith'),
    ('seeming', 'Seeming'),
    ('house', 'House'),
    ('seelie-legacy', 'Seelie Legacy'),
    ('unseelie-legacy', 'Unseelie Legacy'),
    ('court', 'Court'),
    ('mortalplus_type', 'Mortal+ Type'),
    ('varna', 'Varna'),
]

SHIFTER_TYPE_CHOICES = [
    ('garou', 'Garou'),
    ('gurahl', 'Gurahl'),
    ('rokea', 'Rokea'),
    ('ananasi', 'Ananasi'),
    ('ajaba', 'Ajaba'),
    ('bastet', 'Bastet'),
    ('corax', 'Corax'),
    ('kitsune', 'Kitsune'),
    ('mokole', 'Mokole'),
    ('nagah', 'Nagah'),
    ('nuwisha', 'Nuwisha'),
    ('ratkin', 'Ratkin'),
    ('none', 'None')
]

AUSPICE_CHOICES = [
    ('ragabash', 'Ragabash'),
    ('theurge', 'Theurge'),
    ('philodox', 'Philodox'),
    ('galliard', 'Galliard'),
    ('ahroun', 'Ahroun'),
    ('brightwater', 'Brightwater'),
    ('dimwater', 'Dimwater'),
    ('darkwater', 'Darkwater'), 
    ('arcas', 'Arcas'),
    ('uzmati', 'Uzmati'),
    ('kojubat', 'Kojubat'),
    ('kieh', 'Kieh'),
    ('rishi', 'Rishi'),
    ('rising sun', 'Rising Sun'),
    ('noonday sun', 'Noonday Sun'),
    ('shrouded sun', 'Shrouded Sun'),
    ('midnight sun', 'Midnight Sun'),
    ('decorated sun', 'Decorated Sun'),
    ('solar eclipse', 'Solar Eclipse'),
    ('kamakshi', 'Kamakshi'),
    ('kartikeya', 'Kartikeya'),
    ('kamsa', 'Kamsa'),
    ('kali', 'Kali'),
    ('none', 'None')
]

BASTET_TRIBE_CHOICES = [
    ('qualmi', 'Qualmi'),
    ('swara', 'Swara'),
    ('khan', 'Khan'),
    ('simba', 'Simba'),
    ('pumonca', 'Pumonca'),
    ('balam', 'Balam'),
    ('bubasti', 'Bubasti'),
    ('ceilican', 'Ceilican'),
    ('bagheera', 'Bagheera'),
    ('none', 'None')
]

BREED_CHOICES = [
    ('homid', 'Homid'),
    ('metis', 'Metis'),
    ('lupus', 'Lupus'),
    ('feline', 'Feline'),
    ('squamus', 'Squamus'),
    ('ursa', 'Ursa'),
    ('animal-born', 'Animal-Born'),
    ('none', 'None')
]

GAROU_TRIBE_CHOICES = [
    ('black fury', 'Black Fury'),
    ('bone gnawer', 'Bone Gnawer'),
    ('children of gaia', 'Children of Gaia'),
    ('fianna', 'Fianna'),
    ('glass walker', 'Glass Walker'),
    ('red talon', 'Red Talon'),
    ('shadow lord', 'Shadow Lord'),
    ('silent strider', 'Silent Strider'),
    ('silver fang', 'Silver Fang'),
    ('stargazer', 'Stargazer'),
    ('uktena', 'Uktena'),
    ('wendigo', 'Wendigo'),
    ('none', 'None')
]

MORTALPLUS_TYPE_CHOICES = [
    ('ghoul', 'Ghoul'),
    ('kinfolk', 'Kinfolk'),
    ('kinain', 'Kinain'),
    ('sorcerer', 'Sorcerer'),
    ('psychic', 'Psychic'),
    ('faithful', 'Faithful'),
    ('none', 'None')
]
MORTALPLUS_POOLS = {
    'Ghoul': {
        'Blood': {'default': 3, 'max': 3}
    },
    'Kinfolk': {
        'Gnosis': {'default': 0, 'max': 3}
    },
    'Kinain': {
        'Glamour': {'default': 2, 'max': 2}
    },
    'Sorcerer': {
        'Quintessence': {'default': 0, 'max': 10}
    },
}
class Stat(models.Model):
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
    shifter_type = models.CharField(
        max_length=100, 
        choices=SHIFTER_TYPE_CHOICES,
        default='none',
        blank=True
    )    
    hidden = models.BooleanField(default=False)
    locked = models.BooleanField(default=False)
    instanced = models.BooleanField(default=False, null=True)
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
            if not isinstance(self.shifter_type, str):
                raise ValidationError({'shifter_type': 'Must be a string'})
            valid_types = [choice[0] for choice in SHIFTER_TYPE_CHOICES]
            if self.shifter_type.lower() not in valid_types and self.shifter_type.lower() != 'none':
                raise ValidationError({'shifter_type': f'Invalid shifter type: {self.shifter_type}'})
                
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

    class Meta:
        app_label = 'wod20th'
        unique_together = ('name', 'stat_type')

class CharacterSheet(SharedMemoryModel):
    account = models.OneToOneField(AccountDB, related_name='character_sheet', on_delete=models.CASCADE, null=True)
    character = models.OneToOneField(ObjectDB, related_name='character_sheet', on_delete=models.CASCADE, null=True, unique=True)
    db_object = models.OneToOneField('objects.ObjectDB', related_name='db_character_sheet', on_delete=models.CASCADE, null=True)

    class Meta:
        app_label = 'wod20th'


from django.db import models
from evennia.utils.idmapper.models import SharedMemoryModel

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

class Asset(models.Model):
    ASSET_TYPES = [
        ('retainer', 'Retainer'),
        ('haven', 'Haven'),
        ('territory', 'Territory'),
        ('contact', 'Contact'),
    ]

    name = models.CharField(max_length=100, unique=True)
    asset_type = models.CharField(max_length=50, choices=ASSET_TYPES)
    description = models.TextField(blank=True, null=True)
    value = models.IntegerField(default=0)
    owner_id = models.IntegerField()  # Store the owner's ID instead of a ForeignKey
    status = models.CharField(max_length=50, default='Active')
    traits = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):  
        return f"{self.name} ({self.get_asset_type_display()})"

    class Meta:
        app_label = 'wod20th'

    @property
    def owner(self):
        from typeclasses.characters import Character  # Local import
        try:
            return Character.objects.get(id=self.owner_id)
        except Character.DoesNotExist:
            return None


class ActionTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    downtime_cost = models.IntegerField(default=0)  # Cost in downtime hours
    requires_target = models.BooleanField(default=False)
    category = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'wod20th'   

class Action(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    template = models.ForeignKey(ActionTemplate, on_delete=models.CASCADE)
    character_id = models.IntegerField()  # Store the character's ID instead of a ForeignKey
    target_asset = models.ForeignKey(Asset, null=True, blank=True, on_delete=models.SET_NULL, related_name='targeted_by_actions')
    downtime_spent = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    result = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.character_id} - {self.template.name} targeting {self.target_asset} ({self.get_status_display()})"

    class Meta:
        app_label = 'wod20th'

    @property
    def character(self):
        from typeclasses.characters import Character  # Local import
        try:
            return Character.objects.get(id=self.character_id)
        except Character.DoesNotExist:
            return None

    def perform_action(self):
        if self.status == 'pending':
            # Implement the logic to resolve the action
            self.status = 'completed'
            self.result = "Action completed successfully."
            self.save()

SHIFTER_IDENTITY_STATS = {
    "Garou": ["Tribe", "Breed", "Auspice", "Rank", "Deed Name"],
    "Gurahl": ["Tribe", "Breed", "Auspice", "Rank", "Deed Name"],
    "Rokea": ["Tribe", "Breed", "Auspice", "Rank", "Deed Name"],
    "Ananasi": ["Aspect", "Ananasi Faction", "Breed", "Ananasi Cabal", "Rank", "Deed Name"],
    "Ajaba": ["Aspect", "Breed", "Rank", "Deed Name"],
    "Bastet": ["Tribe", "Breed", "Rank", "Deed Name"],
    "Corax": ["Breed", "Rank", "Deed Name"],
    "Kitsune": ["Kitsune Path", "Kitsune Faction", "Breed", "Rank", "Deed Name"],
    "Mokole": ["Varna", "Stream", "Breed", "Rank", "Deed Name"],
    "Nagah": ["Crown", "Breed", "Auspice", "Rank", "Deed Name"],
    "Nuwisha": ["Breed", "Rank", "Deed Name"],
    "Ratkin": ["Aspect", "Plague", "Breed", "Rank", "Deed Name"]
}
SHIFTER_RENOWN: Dict[str, Union[List[str], Dict[str, Dict[str, List[int]]]]] = {
    "Ajaba": ["Cunning", "Ferocity", "Obligation"],
    "Ananasi": ["Cunning", "Obedience", "Wisdom"],
    "Bastet": ["Cunning", "Ferocity", "Honor"],
    "Corax": ["Glory", "Honor", "Wisdom"],
    "Garou": ["Glory", "Honor", "Wisdom"],
    "Gurahl": ["Honor", "Succor", "Wisdom"],
    "Kitsune": ["Cunning", "Honor", "Glory"],
    "Mokole": ["Glory", "Honor", "Wisdom"],
    "Nagah": [],  # Nagah don't use Renown
    "Nuwisha": ["Humor", "Glory", "Cunning"],
    "Ratkin": ["Infamy", "Obligation", "Cunning"],
    "Rokea": ["Valor", "Harmony", "Innovation"]
}

CLAN = {
    'Brujah', 'Gangrel', 'Malkavian', 'Nosferatu', 'Toreador', 'Tremere', 'Ventrue', 'Lasombra', 
    'Tzimisce', 'Assamite', 'Followers of Set', 'Hecata', 'Ravnos', 'Baali', 'Blood Brothers', 
    'Daughters of Cacophony', 'Gargoyles', 'Kiasyd', 'Nagaraja', 'Salubri', 'Samedi', 'True Brujah'
}

MAGE_FACTION = {
    'Traditions', 'Technocracy', 'Nephandi'
}

MAGE_SPHERES = {
    'Correspondence', 'Entropy', 'Forces', 'Life', 'Matter', 'Mind', 'Prime', 'Spirit', 'Time'
}

TRADITION = {
    'Cultists of Ecstasy', 'Euthanatos', 'Celestial Chorus', 'Akashic Brotherhood',
    'Dreamspeakers', 'Virtual Adepts', 'Order of Hermes', 'Verbena',
    'Sons of Ether'
}

TRADITION_SUBFACTION = {
    'Akashic Brotherhood': [
        'Chabnagpa', 'Lin Shen', 'Wu Shan', 'Yamabushi', 'Jina', 'Karmachakra', 'Shaolin', 'Blue Skins',
        'Mo-Tzu Fa', "Roda d'Oro", 'Gam Lung', 'Han Fei Tzu Academy', 'Kaizankai', 'Banner of the Ebon Dragon', 
        'Sulsa', 'Tenshi Arashi Ryu', 'Wu Lung'
    ],
    'Celestial Chorus': [
        'Brothers of St. Christopher', 'Chevra Kedisha', 'Knights of St. George', 'Order of St. Michael', 
        'Poor Knights of the Temple of Solomon', 'Sisters of Gabrielle', 'Alexandrian Society', 'Anchorite',
        'Children of Albi', 'Latitudinarian', 'Monist', 'Nashimite', 'Septarian', 'Hare Krishna', 'Hindu',
        'Jain', 'Son of Mithras', 'Rastafarian', 'Sikh', 'Sufi', 'Bat Binah', 'Song of the Ancients'
    ],
    'Cultists of Ecstasy': [
        'Erzuli Jingo', 'Kiss of Astarte', 'Maenad', "K'an Lu", 'Vratyas', 'Aghoris', 'Acharne', 'Freyji',
        'Sons of Wotan', 'Sutr', 'Joybringers', 'Dissonance Society', 'Klubwerks', "Children's Crusade",
        'Cult of Acceptance', 'Silver Bridges', 'Los Sabios Locos', "Ka'a", 'Khlysty Flagellants', 
        "Bongo's Rangers", 'Dervish', 'Confrerie Chango', 'Roda do Jogo', 'Los Sangradores', 'Studiosi',
        'Umilyenye'
    ],
    'Euthanatos': [
        'Aided', 'Devasu', 'Lhakmist', 'Natatapa', 'Knight of Radamanthys', 'Pomegranate Deme', "N'anga",
        'Ta Kiti', 'Albireo', 'Chakramuni', 'Golden Chalice', 'Pallottino', 'Scholars of the Wheel', "Yggdrasil's Keepers",
        'Yum Cimil'
    ],
    'Dreamspeakers': [
        'Balomb', 'Baruti', 'Contrary', 'Four Winds', 'Ghost Wheel Society', 'Keeper of the Sacred Fire', 
        'Kopa Loei', 'Red Spear Society', 'Sheikha', 'Solitaries', 'Spirit Smith', 'Uzoma'
    ],
    'Order of Hermes': [
        'House Bonisagus', 'House Flambeau', 'House Fortunae', 'House Quaesitori', 'House Shaea', 'House Tytalus',
        'House Verditius', 'House Criamon', 'House Jerbiton', 'House Merinita', 'House Skopos', 'House Xaos'
    ],
    'Verbena': [
        'Gardeners of the Tree', 'Lifeweavers', 'Moon-Seekers', 'Twisters of Fate', 'Techno-Pagans', 'Fairy Folk', 'New Age'
    ],
    'Sons of Ether': [
        'Ethernauts', 'Cybernauts', 'Utopians', 'Adventurers', 'Mad Scientists', 'Progressivists', 'Aquanauts'
    ],
    'Virtual Adepts': [
        'Chaoticians', 'Cyberpunk', 'Cypherpunks', 'Nexplorers', 'Reality Coders'
    ]
}

CONVENTION = {
    'Iteration X', 'New World Order', 'Progenitor', 'Syndicate', 'Void Engineer'
}

METHODOLOGIES = {
    'Iteration X': [
        'BioMechanics', 'Macrotechnicians', 'Statisticians', 'Time-Motion Managers'
    ],
    'New World Order': [
        'Ivory Tower', 'Operatives', 'Watchers', 'The Feed', 'Q Division', 'Agronomists'
    ],
    'Progenitors': [
        'Applied Sciences', 'Deviancy Scene investigators', 'Médecins Sans Superstition',
        'Biosphere Explorers', 'Damage Control', 'Ethical Compliance', 'FACADE Engineers',
        'Genegineers', 'Pharmacopoeists', 'Preservationists', 'Psychopharmacopoeists', 
        'Shalihotran Society'
    ],
    'Syndicate': [
        'Disbursements', 'Assessment Division', 'Reorganization Division', 'Procurements Division',
        'Extraction Division', 'Enforcers (Hollow Men)', 'Legal Division', 'Extralegal Division',
        'Extranational Division', 'Information Specialists', 'Special Information Security Division',
        'Financiers', 'Acquisitions Division', 'Entrepreneurship Division', 'Liquidation Division',
        'Media Control', 'Effects Division', 'Spin Division', 'Marketing Division', 'Special Projects Division'
    ],
    'Void Engineer': [
        'Border Corps Division', 'Earth Frontier Division', 'Aquatic Exploration Teams',
        'Cryoregional Specialists', 'Hydrothermal Botanical Mosaic Analysts', 'Inaccessible High Elevation Exploration Teams',
        'Subterranean Exploration Corps', 'Neutralization Specialist Corps', 'Neutralization Specialists', 
        'Enforcement Training and Conditioning Agency', 'Department of Psychological Evaluation and Maintenance', 'Pan-Dimensional Corps', 
        'Deep Exploration Teams', 'Solar Exploration Teams', 'Cybernauts', 'Chrononauts', 'Research & Execution'
    ]
}

NEPHANDI_FACTION = {
    'Herald of the Basilisk', 'Obliviate', 'Malfean', 'Baphie', 
    'Infernalist', 'Ironhand', 'Mammonite', "K'llashaa"
}

SEEMING = {
    'Childing', 'Wilder', 'Grump'
}

KITH = {
    'Boggan', 'Clurichaun', 'Eshu', 'Nocker', 'Piskie', 'Pooka', 'Redcap', 'Satyr', 
    'Selkie', 'Arcadian Sidhe', 'Autumn Sidhe', 'Sluagh', 'Troll'
}

SEELIE_LEGACIES = {
    'Bumpkin', 'Courtier', 'Crafter', 'Dandy', 'Hermit', 'Orchid', 'Paladin', 'Panderer', 
    'Regent', 'Sage', 'Saint', 'Squire', 'Troubadour', 'Wayfarer'
}

UNSEELIE_LEGACIES = {
    'Beast', 'Fatalist', 'Fool', 'Grotesque', 'Knave', 'Outlaw', 'Pandora', 'Peacock', 'Rake', 'Riddler', 
    'Ringleader', 'Rogue', 'Savage', 'Wretch'
}

ARTS = {
    'Autumn', 'Chicanery', 'Chronos', 'Contract', 'Dragon’s Ire', 'Legerdemain', 'Metamorphosis', 'Naming', 
    'Oneiromancy', 'Primal', 'Pyretics', 'Skycraft', 'Soothsay', 'Sovereign', 'Spring', 'Summer', 'Wayfare', 'Winter'
}

REALMS = {
    'Actor', 'Fae', 'Nature', 'Prop', 'Scene', 'Time'
}

MORTALPLUS_TYPES = {
    'Ghoul': ['Disciplines'],
    'Kinfolk': ['Gifts'],
    'Sorcerer': ['Sorcery'],
    'Psychic': ['Numina'],
    'Faithful': ['Faith'],
    'Kinain': ['Arts', 'Realms']
}

MORTALPLUS_POWERS = {
    'Ghoul': {
        'Disciplines': ['Potence', 'Fortitude', 'Celerity', 'Animalism', 'Auspex', 'Dominate', 
                       'Presence', 'Obfuscate', 'Protean']
    },
    'Kinfolk': {
        'Gifts': []
    },
    'Sorcerer': {
        'Sorcery': []
    },
    'Psychic': {
        'Numina': []
    },
    'Faithful': {
        'Faith': []
    },
    'Kinain': {
        'Arts': [],
        'Realms': []
    }
}

def validate_mortalplus_powers(character, power_type, value):
    """
    Validate power selections for Mortal+ characters.
    Returns (bool, str) tuple - (is_valid, error_message)
    """
    mortalplus_type = character.get_stat('identity', 'personal', 'Mortal Plus Type')
    if not mortalplus_type:
        return False, "Character is not a Mortal+ type"

    # Validate Ghoul powers
    if mortalplus_type == 'Ghoul':
        if power_type == 'Disciplines':
            domitor = character.get_stat('identity', 'personal', 'Domitor')
            if not domitor:
                return False, "Ghouls must have a domitor set to learn disciplines"
            
            # Get domitor's clan disciplines
            clan_disciplines = get_clan_disciplines(domitor.get_stat('identity', 'personal', 'Clan'))
            if value not in clan_disciplines:
                return False, f"Ghouls can only learn disciplines from their domitor's clan: {', '.join(clan_disciplines)}"

    # Validate Kinfolk powers
    elif mortalplus_type == 'Kinfolk':
        if power_type == 'Gifts':
            # Check for Gift Merit
            merits = character.db.stats.get('merits', {}).get('merit', {})
            has_gift_merit = any(merit.lower() == 'gift of the spirits' 
                               for merit in merits.keys())
            if not has_gift_merit:
                return False, "Kinfolk must have the 'Gift of the Spirits' Merit to learn Gifts"

        if power_type == 'Gnosis':
            # Check for Gnosis Merit level
            merits = character.db.stats.get('merits', {}).get('merit', {})
            gnosis_merit = next((merit_value.get('perm', 0) 
                               for merit, merit_value in merits.items() 
                               if merit.lower() == 'gnosis'), 0)
            
            max_gnosis = (gnosis_merit - 4) if gnosis_merit >= 5 else 0
            if int(value) > max_gnosis:
                return False, f"Character can only have up to {max_gnosis} Gnosis with current Merit level"

    # Validate Kinain powers
    elif mortalplus_type == 'Kinain':
        if power_type in ['Arts', 'Realms']:
            # Get Kinain Merit level
            merits = character.db.stats.get('merits', {}).get('merit', {})
            kinain_merit = next((merit_value.get('perm', 0) 
                               for merit, merit_value in merits.items() 
                               if merit.lower() == 'fae blood'), 0)
            
            # Calculate maximums based on Merit level
            max_arts = kinain_merit // 2
            max_art_dots = min(3, kinain_merit // 2)
            
            if power_type == 'Arts' and len(character.get_all_powers('Arts')) >= max_arts:
                return False, f"Kinain can only learn {max_arts} Arts with current Merit level"
            
            if int(value) > max_art_dots:
                return False, f"Kinain can only have up to {max_art_dots} dots in {power_type}"

    return True, ""

def get_clan_disciplines(clan):
    """Helper function to get clan disciplines."""
    CLAN_DISCIPLINES = {
        'Ahrimes': ['Animalism', 'Presence', 'Spiritus'],
        'Assamite': ['Celerity', 'Obfuscate', 'Quietus'],
        'Assamite Antitribu': ['Celerity', 'Obfuscate', 'Quietus'],
        'Baali': ['Daimoinon', 'Obfuscate', 'Presence'],
        'Blood Brothers': ['Celerity', 'Potence', 'Sanguinus'],
        'Brujah': ['Celerity', 'Potence', 'Presence'],
        'Brujah Antitribu': ['Celerity', 'Potence', 'Presence'],
        'Bushi': ['Celerity', 'Kai', 'Presence'],
        'Caitiff': [],
        'Cappadocians': ['Auspex', 'Fortitude', 'Mortis'],
        'Children of Osiris': ['Bardo'],
        'Harbingers of Skulls': ['Auspex', 'Fortitude', 'Necromancy'],
        'Daughters of Cacophony': ['Fortitude', 'Melpominee', 'Presence'],
        'Followers of Set': ['Obfuscate', 'Presence', 'Serpentis'],
        'Gangrel': ['Animalism', 'Fortitude', 'Protean'],
        'City Gangrel': ['Celerity', 'Obfuscate', 'Protean'],
        'Country Gangrel': ['Animalism', 'Fortitude', 'Protean'],
        'Gargoyles': ['Fortitude', 'Potence', 'Visceratika'],
        'Giovanni': ['Dominate', 'Necromancy', 'Potence'],
        'Kiasyd': ['Mytherceria', 'Dominate', 'Obtenebration'],
        'Laibon': ['Abombwe', 'Animalism', 'Fortitude'],
        'Lamia': ['Deimos', 'Necromancy', 'Potence'],
        'Lasombra': ['Dominate', 'Obtenebration', 'Potence'],
        'Lasombra Antitribu': ['Dominate', 'Obtenebration', 'Potence'],
        'Lhiannan': ['Animalism', 'Ogham', 'Presence'],
        'Malkavian': ['Auspex', 'Dominate', 'Obfuscate'],
        'Malkavian Antitribu': ['Auspex', 'Dementation', 'Obfuscate'],
        'Nagaraja': ['Auspex', 'Necromancy', 'Dominate'],
        'Nosferatu': ['Animalism', 'Obfuscate', 'Potence'],
        'Nosferatu Antitribu': ['Animalism', 'Obfuscate', 'Potence'],
        'Old Clan Tzimisce': ['Animalism', 'Auspex', 'Dominate'],
        'Panders': [],
        'Ravnos': ['Animalism', 'Chimerstry', 'Fortitude'],
        'Ravnos Antitribu': ['Animalism', 'Chimerstry', 'Fortitude'],
        'Salubri': ['Auspex', 'Fortitude', 'Obeah'],
        'Samedi': ['Necromancy', 'Obfuscate', 'Thanatosis'],
        'Serpents of the Light': ['Obfuscate', 'Presence', 'Serpentis'],
        'Toreador': ['Auspex', 'Celerity', 'Presence'],
        'Toreador Antitribu': ['Auspex', 'Celerity', 'Presence'],
        'Tremere': ['Auspex', 'Dominate', 'Thaumaturgy'],
        'Tremere Antitribu': ['Auspex', 'Dominate', 'Thaumaturgy'],
        'True Brujah': ['Potence', 'Presence', 'Temporis'],
        'Tzimisce': ['Animalism', 'Auspex', 'Vicissitude'],
        'Ventrue': ['Dominate', 'Fortitude', 'Presence'],
        'Ventrue Antitribu': ['Auspex', 'Dominate', 'Fortitude'],
    }
    return CLAN_DISCIPLINES.get(clan, [])

def can_learn_power(character, power_category, power_name, value):
    """
    Check if a character can learn or increase a power.
    Returns (bool, str) tuple - (can_learn, reason)
    """
    # Get character's splat type
    splat = character.get_stat('identity', 'personal', 'Splat')
    
    # Handle Mortal+ validation
    if splat == 'Mortal Plus':
        return validate_mortalplus_powers(character, power_category, value)
        
    return True, ""

class CharacterImage(SharedMemoryModel):
    """Model for storing character images."""
    character = models.ForeignKey('objects.ObjectDB', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='character_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
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