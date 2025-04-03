from django.db import models
from evennia.utils.idmapper.models import SharedMemoryModel
from evennia.utils.logger import log_info

class EquipmentManager(models.Manager):
    """
    Custom manager for Equipment that adds methods to return specialized subtypes.
    """
    def get_real_instance(self, obj):
        """
        Return the real instance of obj (i.e., if obj is a proxy, return the real object).
        """
        if not isinstance(obj, Equipment):
            return obj
            
        # Get the model class corresponding to the category
        category_map = {
            'melee': MeleeWeapon,
            'ranged': RangedWeapon,
            'thrown': ThrownWeapon,
            'improvised': ImprovisedWeapon,
            'explosives': Explosive,
            'armor': Armor,
            'ammunition': Ammunition,
            'special_ammunition': SpecialAmmunition,
            'technocratic': TechnocraticDevice,
            'martial_arts': MartialArtsWeapon,
            'spying': SpyingDevice,
            'communications': CommunicationsDevice,
            'survival': SurvivalGear,
            'electronics': ElectronicDevice,
            'landcraft': Landcraft,
            'aircraft': Aircraft,
            'seacraft': Seacraft,
            'cycle': Cycle,
            'jetpack': Jetpack,
            'talisman': Talisman,
            'device': Device,
            'trinket': Trinket,
            'gadget': Gadget,
            'invention': Invention,
            'matrix': Matrix,
            'grimoire': Grimoire,
            'biotech': Biotech,
            'cybertech': Cybertech,
            'periapt': Periapt,
            'chimerical': Chimerical,
            'treasure': Treasure,
            'fetish': Fetish,
            'talen': Talen,
            'artifact': Artifact,
        }
        
        # If the category has a specialized model, try to get it
        model_class = category_map.get(obj.category)
        if model_class:
            try:
                # Attempt to fetch the specialized instance
                return model_class.objects.get(pk=obj.pk)
            except model_class.DoesNotExist:
                # If this fails, return the base equipment object
                pass
        
        # If no specialized model or fetching fails, return the original object
        return obj
    
    def get_real_instances(self, objs):
        """
        Return a list of the real instances of objs.
        """
        return [self.get_real_instance(obj) for obj in objs]
    
    def get_by_id(self, sequential_id):
        """
        Get an equipment item by its sequential ID and return the specialized model if available.
        """
        try:
            base_item = self.get(sequential_id=sequential_id)
            return self.get_real_instance(base_item)
        except Equipment.DoesNotExist:
            return None

class Equipment(SharedMemoryModel):
    sequential_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    resources = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()
    conceal = models.CharField(max_length=20)
    equipment_type = models.CharField(max_length=35, choices=[
        ('mundane', 'Mundane'),
        ('supernatural_consumable', 'Supernatural Consumable'),
        ('supernatural_unique', 'Supernatural Unique')
    ])
    category = models.CharField(max_length=50, choices=[
        # Mundane Categories
        ('ranged', 'Ranged'),
        ('melee', 'Melee'),
        ('improvised', 'Improvised'),
        ('thrown', 'Thrown'),
        ('explosives', 'Explosives'),
        ('ammunition', 'Ammunition'),
        ('technocratic', 'Technocratic'),
        ('martial_arts', 'Martial Arts'),
        ('spying', 'Spying'),
        ('communications', 'Communications'),
        ('survival', 'Survival'),
        ('electronics', 'Electronics'),
        ('aircraft', 'Aircraft'),
        ('landcraft', 'Landcraft'),
        ('seacraft', 'Seacraft'),
        # Supernatural Categories
        ('talisman', 'Talisman'),
        ('device', 'Device'),
        ('trinket', 'Trinket'),
        ('gadget', 'Gadget'),
        ('invention', 'Invention'),
        ('matrix', 'Matrix'),
        ('grimoire', 'Grimoire'),
        ('biotech', 'Biotech'),
        ('cybertech', 'Cybertech'),
        ('periapt', 'Periapt'),
        ('chimerical', 'Chimerical'),
        ('treasure', 'Treasure'),
        ('fetish', 'Fetish'),
        ('talen', 'Talen'),
        ('artifact', 'Artifact'),
    ])
    is_unique = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=False)
    
    # Add our custom manager
    objects = EquipmentManager()

    class Meta:
        ordering = ['sequential_id']  # Order by sequential_id by default

    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        """
        Override the save method to automatically set sequential_id if not provided.
        """
        if self.sequential_id is None:
            # Get the highest sequential ID from existing equipment
            highest_id = Equipment.objects.all().aggregate(models.Max('sequential_id'))['sequential_id__max']
            # Set the new ID to be one more than the highest existing ID (or 1 if no items exist)
            self.sequential_id = (highest_id or 0) + 1
        
        super().save(*args, **kwargs)
        
    @property
    def real_instance(self):
        """
        Return the most specific subclass instance of this model.
        """
        return Equipment.objects.get_real_instance(self)
        
    @property
    def specialized_details(self):
        """
        Returns specialized details for this equipment item based on its category.
        This is the new composition-based approach that fetches related specialized data.
        """
        category = self.category
        
        # Check for specialized data in the new composition-based tables
        if category == 'melee':
            try:
                return MeleeWeaponDetails.objects.get(equipment=self)
            except MeleeWeaponDetails.DoesNotExist:
                pass
                
        elif category == 'ranged':
            try:
                return RangedWeaponDetails.objects.get(equipment=self)
            except RangedWeaponDetails.DoesNotExist:
                pass
                
        elif category == 'thrown':
            try:
                return ThrownWeaponDetails.objects.get(equipment=self)
            except ThrownWeaponDetails.DoesNotExist:
                pass
                
        elif category == 'improvised':
            try:
                return ImprovisedWeaponDetails.objects.get(equipment=self)
            except ImprovisedWeaponDetails.DoesNotExist:
                pass
                
        elif category == 'explosives':
            try:
                return ExplosiveDetails.objects.get(equipment=self)
            except ExplosiveDetails.DoesNotExist:
                pass
                
        elif category == 'armor':
            try:
                return ArmorDetails.objects.get(equipment=self)
            except ArmorDetails.DoesNotExist:
                pass
                
        elif category == 'ammunition':
            try:
                return AmmunitionDetails.objects.get(equipment=self)
            except AmmunitionDetails.DoesNotExist:
                try:
                    return SpecialAmmunitionDetails.objects.get(equipment=self)
                except SpecialAmmunitionDetails.DoesNotExist:
                    pass
                    
        elif category == 'landcraft':
            try:
                return LandcraftDetails.objects.get(equipment=self)
            except LandcraftDetails.DoesNotExist:
                pass
                
        elif category == 'aircraft':
            try:
                return AircraftDetails.objects.get(equipment=self)
            except AircraftDetails.DoesNotExist:
                pass
                
        elif category == 'seacraft':
            try:
                return SeacraftDetails.objects.get(equipment=self)
            except SeacraftDetails.DoesNotExist:
                pass
                
        elif category == 'cycle':
            try:
                return CycleDetails.objects.get(equipment=self)
            except CycleDetails.DoesNotExist:
                pass
                
        elif category == 'jetpack':
            try:
                return JetpackDetails.objects.get(equipment=self)
            except JetpackDetails.DoesNotExist:
                pass
                
        # Add more category checks as needed
                
        # Return None if no specialized details found
        return None

class PlayerInventory(SharedMemoryModel):
    player = models.ForeignKey('accounts.AccountDB', on_delete=models.CASCADE)
    equipment = models.ManyToManyField(Equipment, through='InventoryItem')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.player}'s Inventory"

class InventoryItem(SharedMemoryModel):
    inventory = models.ForeignKey(PlayerInventory, on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    is_proven = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey('accounts.AccountDB', null=True, blank=True, on_delete=models.SET_NULL)
    approval_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.equipment.name} ({self.quantity}) in {self.inventory.player}'s inventory"

# Weapon Models
class MeleeWeapon(Equipment):
    damage = models.CharField(max_length=100)
    damage_type = models.CharField(max_length=100)
    difficulty = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class RangedWeapon(Equipment):
    damage = models.CharField(max_length=100)
    damage_type = models.CharField(max_length=100)
    range = models.CharField(max_length=100)
    rate = models.CharField(max_length=100)
    clip = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class ThrownWeapon(Equipment):
    damage = models.CharField(max_length=100)
    damage_type = models.CharField(max_length=100)
    range = models.CharField(max_length=100)
    difficulty = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class ImprovisedWeapon(Equipment):
    damage = models.CharField(max_length=100)
    damage_type = models.CharField(max_length=100)
    difficulty = models.PositiveIntegerField()
    break_chance = models.PositiveIntegerField(default=50)  # Percentage chance to break on use

    def __str__(self):
        return self.name

class Explosive(Equipment):
    blast_area = models.CharField(max_length=100)  # Area of effect
    blast_power = models.CharField(max_length=100)  # Damage dice
    burn = models.BooleanField(default=False)  # Whether it causes burning
    notes = models.TextField(blank=True)  # Special notes or effects

    def __str__(self):
        return self.name

class SpecialAmmunition(Equipment):
    damage = models.CharField(max_length=100)  # Damage value
    effects = models.TextField()  # Special effects
    compatible_weapons = models.ManyToManyField(RangedWeapon)  # Which weapons can use this ammo

    def __str__(self):
        return self.name

class Armor(Equipment):
    rating = models.PositiveIntegerField(default=0)  # Protection rating
    dexterity_penalty = models.IntegerField(default=0)  # Penalty to Dexterity rolls
    is_shield = models.BooleanField(default=False)  # Whether this is a shield
    shield_bonus = models.PositiveIntegerField(default=0)  # Additional bonus for shields

    def __str__(self):
        return self.name

class Ammunition(Equipment):
    caliber = models.CharField(max_length=50)
    damage_modifier = models.CharField(max_length=50)
    special_effects = models.TextField(blank=True)
    compatible_weapons = models.ManyToManyField(RangedWeapon)

    def __str__(self):
        return f"{self.caliber} Ammunition"

# Technocratic Equipment
class TechnocraticDevice(Equipment):
    power_source = models.CharField(max_length=100)
    power_level = models.PositiveIntegerField()
    maintenance_required = models.BooleanField(default=True)
    maintenance_interval = models.CharField(max_length=100)
    special_features = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Martial Arts Equipment
class MartialArtsWeapon(Equipment):
    damage = models.CharField(max_length=100)
    damage_type = models.CharField(max_length=100)
    difficulty = models.PositiveIntegerField()
    style_requirements = models.TextField(blank=True)
    special_techniques = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Spying Equipment
class SpyingDevice(Equipment):
    function = models.CharField(max_length=100)
    battery_life = models.CharField(max_length=100)
    range = models.CharField(max_length=100)
    stealth_rating = models.PositiveIntegerField()
    special_features = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Communications Equipment
class CommunicationsDevice(Equipment):
    range = models.CharField(max_length=100)
    encryption_level = models.PositiveIntegerField()
    battery_life = models.CharField(max_length=100)
    special_features = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Survival Equipment
class SurvivalGear(Equipment):
    durability = models.PositiveIntegerField()
    weather_resistance = models.CharField(max_length=100)
    special_features = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Electronics
class ElectronicDevice(Equipment):
    power_source = models.CharField(max_length=100)
    battery_life = models.CharField(max_length=100)
    special_features = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Vehicle Models
class Cycle(Equipment):
    safe_speed = models.CharField(max_length=100)  # Safe speed in mph or Strength multiplier
    max_speed = models.CharField(max_length=100)   # Maximum speed in mph or Strength multiplier
    maneuver = models.PositiveIntegerField()       # Maneuver rating
    crew = models.CharField(max_length=100)        # Crew size and passenger capacity
    durability = models.PositiveIntegerField()     # Durability rating
    structure = models.PositiveIntegerField()      # Structure rating
    weapons = models.CharField(max_length=100, blank=True)  # Weapon slots (e.g., "#1", "#2", "N/A")
    requires_skill = models.CharField(max_length=100, default="Drive")  # Required skill to operate

    def __str__(self):
        return self.name

class Landcraft(Equipment):
    safe_speed = models.PositiveIntegerField()     # Safe speed in mph
    max_speed = models.PositiveIntegerField()      # Maximum speed in mph
    maneuver = models.PositiveIntegerField()       # Maneuver rating
    crew = models.CharField(max_length=100)        # Crew size and passenger capacity
    durability = models.PositiveIntegerField()     # Durability rating
    structure = models.PositiveIntegerField()      # Structure rating
    weapons = models.CharField(max_length=100, blank=True)  # Weapon slots (e.g., "#1", "#2", "N/A")
    mass_damage = models.PositiveIntegerField(default=1)  # Additional damage dice from mass
    passenger_protection = models.PositiveIntegerField(default=0)  # Additional protection for passengers
    vehicle_type = models.CharField(max_length=50, choices=[
        ('car', 'Car'),
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('bus', 'Bus'),
        ('rv', 'RV'),
        ('limo', 'Limousine'),
        ('other', 'Other')
    ])
    requires_skill = models.CharField(max_length=100, default="Drive")  # Required skill to operate

    def __str__(self):
        return self.name

class Seacraft(Equipment):
    speed = models.CharField(max_length=100)
    range = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()
    special_features = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Supernatural Equipment Models
class Talisman(Equipment):
    power_level = models.PositiveIntegerField()
    activation_requirements = models.TextField()
    duration = models.CharField(max_length=100)
    special_effects = models.TextField()

    def __str__(self):
        return self.name

class Device(Equipment):
    power_level = models.PositiveIntegerField()
    activation_requirements = models.TextField()
    duration = models.CharField(max_length=100)
    special_effects = models.TextField()

    def __str__(self):
        return self.name

class Trinket(Equipment):
    power_level = models.PositiveIntegerField()
    activation_requirements = models.TextField()
    duration = models.CharField(max_length=100)
    special_effects = models.TextField()

    def __str__(self):
        return self.name

class Gadget(Equipment):
    power_level = models.PositiveIntegerField()
    activation_requirements = models.TextField()
    duration = models.CharField(max_length=100)
    special_effects = models.TextField()

    def __str__(self):
        return self.name

class Invention(Equipment):
    power_level = models.PositiveIntegerField()
    activation_requirements = models.TextField()
    duration = models.CharField(max_length=100)
    special_effects = models.TextField()

    def __str__(self):
        return self.name

class Matrix(Equipment):
    power_level = models.PositiveIntegerField()
    activation_requirements = models.TextField()
    duration = models.CharField(max_length=100)
    special_effects = models.TextField()

    def __str__(self):
        return self.name

class Grimoire(Equipment):
    power_level = models.PositiveIntegerField()
    activation_requirements = models.TextField()
    duration = models.CharField(max_length=100)
    special_effects = models.TextField()

    def __str__(self):
        return self.name

class Biotech(Equipment):
    power_level = models.PositiveIntegerField()
    activation_requirements = models.TextField()
    duration = models.CharField(max_length=100)
    special_effects = models.TextField()

    def __str__(self):
        return self.name

class Cybertech(Equipment):
    power_level = models.PositiveIntegerField()
    activation_requirements = models.TextField()
    duration = models.CharField(max_length=100)
    special_effects = models.TextField()

    def __str__(self):
        return self.name

class Periapt(Equipment):
    power_level = models.PositiveIntegerField()
    activation_requirements = models.TextField()
    duration = models.CharField(max_length=100)
    special_effects = models.TextField()

    def __str__(self):
        return self.name

class Chimerical(Equipment):
    power_level = models.PositiveIntegerField()
    activation_requirements = models.TextField()
    duration = models.CharField(max_length=100)
    special_effects = models.TextField()

    def __str__(self):
        return self.name

class Treasure(Equipment):
    power_level = models.PositiveIntegerField()
    activation_requirements = models.TextField()
    duration = models.CharField(max_length=100)
    special_effects = models.TextField()

    def __str__(self):
        return self.name

class Fetish(Equipment):
    power_level = models.PositiveIntegerField()
    activation_requirements = models.TextField()
    duration = models.CharField(max_length=100)
    special_effects = models.TextField()

    def __str__(self):
        return self.name

class Talen(Equipment):
    power_level = models.PositiveIntegerField()
    activation_requirements = models.TextField()
    duration = models.CharField(max_length=100)
    special_effects = models.TextField()

    def __str__(self):
        return self.name

class Artifact(Equipment):
    power_level = models.PositiveIntegerField()
    activation_requirements = models.TextField()
    duration = models.CharField(max_length=100)
    special_effects = models.TextField()

    def __str__(self):
        return self.name

class Jetpack(Equipment):
    safe_speed = models.PositiveIntegerField()     # Safe speed in mph
    max_speed = models.PositiveIntegerField()      # Maximum speed in mph
    maneuver = models.PositiveIntegerField()       # Maneuver rating
    durability = models.PositiveIntegerField()     # Durability rating
    structure = models.PositiveIntegerField()      # Structure rating
    requires_skill = models.CharField(max_length=100, default="Jetpack")  # Required skill to operate
    is_technomagickal = models.BooleanField(default=True)  # Is this a technomagickal vehicle?

    def __str__(self):
        return self.name

class Aircraft(Equipment):
    safe_speed = models.CharField(max_length=100)  # Safe speed in mph or "Wind" for balloons
    max_speed = models.CharField(max_length=100)   # Maximum speed in mph or "Wind" for balloons
    maneuver = models.PositiveIntegerField()       # Maneuver rating
    crew = models.CharField(max_length=100)        # Crew size and passenger capacity
    durability = models.PositiveIntegerField()     # Durability rating
    structure = models.PositiveIntegerField()      # Structure rating
    weapons = models.CharField(max_length=100, blank=True)  # Weapon slots (e.g., "!", "!!", "!!!!")
    aircraft_type = models.CharField(max_length=50, choices=[
        ('balloon', 'Hot Air Balloon'),
        ('helicopter', 'Helicopter'),
        ('prop_plane', 'Propeller Plane'),
        ('jet', 'Jet'),
        ('fighter', 'Fighter Jet'),
        ('other', 'Other')
    ])
    requires_specialty = models.BooleanField(default=False)  # Requires specialty skill
    specialty_type = models.CharField(max_length=50, blank=True, choices=[
        ('helicopter', 'Helicopter'),
        ('fighter_jet', 'Fighter Jet'),
        ('', 'None')
    ])
    passenger_protection = models.BooleanField(default=True)  # Whether durability protects passengers
    requires_skill = models.CharField(max_length=100, default="Pilot")  # Required skill to operate

    def __str__(self):
        return self.name

# New composition-based models for specialized equipment details

class MeleeWeaponDetails(SharedMemoryModel):
    """Specialized details for melee weapons using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='melee_details')
    damage = models.CharField(max_length=100)
    damage_type = models.CharField(max_length=100)
    difficulty = models.PositiveIntegerField()
    
    def __str__(self):
        return f"Details for {self.equipment.name}"

class RangedWeaponDetails(SharedMemoryModel):
    """Specialized details for ranged weapons using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='ranged_details')
    damage = models.CharField(max_length=100)
    damage_type = models.CharField(max_length=100)
    range = models.CharField(max_length=100)
    rate = models.CharField(max_length=100)
    clip = models.PositiveIntegerField()
    
    def __str__(self):
        return f"Details for {self.equipment.name}"
        
class ThrownWeaponDetails(SharedMemoryModel):
    """Specialized details for thrown weapons using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='thrown_details')
    damage = models.CharField(max_length=100)
    damage_type = models.CharField(max_length=100)
    range = models.CharField(max_length=100)
    difficulty = models.PositiveIntegerField()
    
    def __str__(self):
        return f"Details for {self.equipment.name}"

class ImprovisedWeaponDetails(SharedMemoryModel):
    """Specialized details for improvised weapons using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='improvised_details')
    damage = models.CharField(max_length=100)
    damage_type = models.CharField(max_length=100)
    difficulty = models.PositiveIntegerField()
    break_chance = models.PositiveIntegerField(default=50)  # Percentage chance to break on use
    
    def __str__(self):
        return f"Details for {self.equipment.name}"

class ExplosiveDetails(SharedMemoryModel):
    """Specialized details for explosives using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='explosive_details')
    blast_area = models.CharField(max_length=100)  # Area of effect
    blast_power = models.CharField(max_length=100)  # Damage dice
    burn = models.BooleanField(default=False)  # Whether it causes burning
    notes = models.TextField(blank=True)  # Special notes or effects
    
    def __str__(self):
        return f"Details for {self.equipment.name}"

class ArmorDetails(SharedMemoryModel):
    """Specialized details for armor using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='armor_details')
    rating = models.PositiveIntegerField(default=0)  # Protection rating
    dexterity_penalty = models.IntegerField(default=0)  # Penalty to Dexterity rolls
    is_shield = models.BooleanField(default=False)  # Whether this is a shield
    shield_bonus = models.PositiveIntegerField(default=0)  # Additional bonus for shields
    
    def __str__(self):
        return f"Details for {self.equipment.name}"

class AmmunitionDetails(SharedMemoryModel):
    """Specialized details for ammunition using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='ammo_details')
    caliber = models.CharField(max_length=50)
    damage_modifier = models.CharField(max_length=50)
    special_effects = models.TextField(blank=True)
    
    def __str__(self):
        return f"Details for {self.equipment.name}"

class SpecialAmmunitionDetails(SharedMemoryModel):
    """Specialized details for special ammunition using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='special_ammo_details')
    damage = models.CharField(max_length=100)  # Damage value
    effects = models.TextField()  # Special effects
    
    def __str__(self):
        return f"Details for {self.equipment.name}"

class TechnocraticDeviceDetails(SharedMemoryModel):
    """Specialized details for technocratic devices using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='technocratic_details')
    power_source = models.CharField(max_length=100)
    power_level = models.PositiveIntegerField()
    maintenance_required = models.BooleanField(default=True)
    maintenance_interval = models.CharField(max_length=100)
    special_features = models.TextField(blank=True)
    
    def __str__(self):
        return f"Details for {self.equipment.name}"

class MartialArtsWeaponDetails(SharedMemoryModel):
    """Specialized details for martial arts weapons using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='martial_arts_details')
    damage = models.CharField(max_length=100)
    damage_type = models.CharField(max_length=100)
    difficulty = models.PositiveIntegerField()
    style_requirements = models.TextField(blank=True)
    special_techniques = models.TextField(blank=True)
    
    def __str__(self):
        return f"Details for {self.equipment.name}"

class SpyingDeviceDetails(SharedMemoryModel):
    """Specialized details for spying devices using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='spying_details')
    function = models.CharField(max_length=100)
    battery_life = models.CharField(max_length=100)
    range = models.CharField(max_length=100)
    stealth_rating = models.PositiveIntegerField()
    special_features = models.TextField(blank=True)
    
    def __str__(self):
        return f"Details for {self.equipment.name}"

class CommunicationsDeviceDetails(SharedMemoryModel):
    """Specialized details for communications devices using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='communications_details')
    range = models.CharField(max_length=100)
    encryption_level = models.PositiveIntegerField()
    battery_life = models.CharField(max_length=100)
    special_features = models.TextField(blank=True)
    
    def __str__(self):
        return f"Details for {self.equipment.name}"

class SurvivalGearDetails(SharedMemoryModel):
    """Specialized details for survival gear using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='survival_details')
    durability = models.PositiveIntegerField()
    weather_resistance = models.CharField(max_length=100)
    special_features = models.TextField(blank=True)
    
    def __str__(self):
        return f"Details for {self.equipment.name}"

class ElectronicDeviceDetails(SharedMemoryModel):
    """Specialized details for electronic devices using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='electronic_details')
    power_source = models.CharField(max_length=100)
    battery_life = models.CharField(max_length=100)
    special_features = models.TextField(blank=True)
    
    def __str__(self):
        return f"Details for {self.equipment.name}"
        
class VehicleDetailsBase(SharedMemoryModel):
    """Base model for all vehicle details using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='vehicle_base_details')
    safe_speed = models.CharField(max_length=100, blank=True)
    max_speed = models.CharField(max_length=100, blank=True)
    maneuver = models.PositiveIntegerField(null=True, blank=True)
    crew = models.CharField(max_length=100, blank=True)
    durability = models.PositiveIntegerField(null=True, blank=True)
    structure = models.PositiveIntegerField(null=True, blank=True)
    weapons = models.CharField(max_length=100, blank=True)
    requires_skill = models.CharField(max_length=100, default="Drive")
    
    class Meta:
        abstract = True

class LandcraftDetails(VehicleDetailsBase):
    """Specialized details for land vehicles using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='landcraft_details')
    vehicle_type = models.CharField(max_length=50, choices=[
        ('truck', 'Truck'),
        ('car', 'Car'),
        ('suv', 'SUV'),
        ('bus', 'Bus'),
        ('tank', 'Tank'),
        ('other', 'Other')
    ])
    mass_damage = models.CharField(max_length=100, blank=True)
    passenger_protection = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"Details for {self.equipment.name}"

class AircraftDetails(VehicleDetailsBase):
    """Specialized details for aircraft using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='aircraft_details')
    aircraft_type = models.CharField(max_length=50, choices=[
        ('balloon', 'Hot Air Balloon'),
        ('helicopter', 'Helicopter'),
        ('prop_plane', 'Propeller Plane'),
        ('jet', 'Jet'),
        ('fighter', 'Fighter Jet'),
        ('other', 'Other')
    ])
    requires_specialty = models.BooleanField(default=False)
    specialty_type = models.CharField(max_length=50, blank=True)
    passenger_protection = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Details for {self.equipment.name}"

class SeacraftDetails(SharedMemoryModel):
    """Specialized details for seacraft using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='seacraft_details')
    speed = models.CharField(max_length=100)
    range = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()
    special_features = models.TextField(blank=True)
    
    def __str__(self):
        return f"Details for {self.equipment.name}"

class CycleDetails(VehicleDetailsBase):
    """Specialized details for cycles using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='cycle_details')
    
    def __str__(self):
        return f"Details for {self.equipment.name}"

class JetpackDetails(SharedMemoryModel):
    """Specialized details for jetpacks using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='jetpack_details')
    safe_speed = models.PositiveIntegerField()
    max_speed = models.PositiveIntegerField()
    maneuver = models.PositiveIntegerField()
    durability = models.PositiveIntegerField()
    structure = models.PositiveIntegerField()
    requires_skill = models.CharField(max_length=100, default="Jetpack")
    is_technomagickal = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Details for {self.equipment.name}"

class SupernaturalItemDetails(SharedMemoryModel):
    """Base model for supernatural items using composition pattern"""
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='supernatural_details')
    power_level = models.PositiveIntegerField()
    activation_requirements = models.TextField()
    duration = models.CharField(max_length=100)
    special_effects = models.TextField()
    
    def __str__(self):
        return f"Details for {self.equipment.name}"


