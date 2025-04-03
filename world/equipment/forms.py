from django import forms
from .models import (
    Equipment, MeleeWeaponDetails, RangedWeaponDetails, ThrownWeaponDetails,
    ImprovisedWeaponDetails, ExplosiveDetails, ArmorDetails, AmmunitionDetails,
    SpecialAmmunitionDetails, TechnocraticDeviceDetails, MartialArtsWeaponDetails,
    SpyingDeviceDetails, CommunicationsDeviceDetails, SurvivalGearDetails,
    ElectronicDeviceDetails, LandcraftDetails, AircraftDetails, SeacraftDetails,
    CycleDetails, JetpackDetails, SupernaturalItemDetails
)

class EquipmentForm(forms.ModelForm):
    # These fields are specific to different equipment categories
    # Ranged Weapon fields
    damage = forms.CharField(max_length=100, required=False, help_text="Damage dealt by the weapon")
    damage_type = forms.CharField(max_length=100, required=False, help_text="Type of damage (e.g. Bashing, Lethal)")
    range = forms.CharField(max_length=100, required=False, help_text="Range of the weapon")
    rate = forms.CharField(max_length=100, required=False, help_text="Rate of fire")
    clip = forms.IntegerField(required=False, help_text="Ammunition capacity")
    
    # Melee/Thrown/Improvised fields
    difficulty = forms.IntegerField(required=False, help_text="Difficulty to use the weapon")
    break_chance = forms.IntegerField(required=False, help_text="Percentage chance to break on use (improvised weapons)")
    
    # Explosive fields
    blast_area = forms.CharField(max_length=100, required=False, help_text="Area of effect")
    blast_power = forms.CharField(max_length=100, required=False, help_text="Damage dice")
    burn = forms.BooleanField(required=False, help_text="Whether it causes burning")
    notes = forms.CharField(required=False, widget=forms.Textarea, help_text="Special notes or effects")
    
    # Armor fields
    rating = forms.IntegerField(required=False, help_text="Protection rating")
    dexterity_penalty = forms.IntegerField(required=False, help_text="Penalty to Dexterity rolls")
    is_shield = forms.BooleanField(required=False, help_text="Whether this is a shield")
    shield_bonus = forms.IntegerField(required=False, help_text="Additional bonus for shields")
    
    # Ammunition fields
    caliber = forms.CharField(max_length=50, required=False, help_text="Caliber of ammunition")
    damage_modifier = forms.CharField(max_length=50, required=False, help_text="Damage modifier")
    special_effects = forms.CharField(required=False, widget=forms.Textarea, help_text="Special effects")
    effects = forms.CharField(required=False, widget=forms.Textarea, help_text="Effects for special ammunition")
    
    # Technocratic Device fields
    power_source = forms.CharField(max_length=100, required=False, help_text="Power source")
    power_level = forms.IntegerField(required=False, help_text="Power level")
    maintenance_required = forms.BooleanField(required=False, help_text="Whether maintenance is required")
    maintenance_interval = forms.CharField(max_length=100, required=False, help_text="Maintenance interval")
    
    # Martial Arts Weapon fields
    style_requirements = forms.CharField(required=False, widget=forms.Textarea, help_text="Style requirements")
    special_techniques = forms.CharField(required=False, widget=forms.Textarea, help_text="Special techniques")
    
    # Spying Device fields
    function = forms.CharField(max_length=100, required=False, help_text="Function of the device")
    stealth_rating = forms.IntegerField(required=False, help_text="Stealth rating")
    
    # Communication Device fields
    encryption_level = forms.IntegerField(required=False, help_text="Encryption level")
    
    # Survival Gear fields
    durability = forms.IntegerField(required=False, help_text="Durability rating")
    weather_resistance = forms.CharField(max_length=100, required=False, help_text="Weather resistance")
    
    # Electronic Device fields
    battery_life = forms.CharField(max_length=100, required=False, help_text="Battery life")
    
    # Vehicle fields (shared)
    safe_speed = forms.CharField(max_length=100, required=False, help_text="Safe speed")
    max_speed = forms.CharField(max_length=100, required=False, help_text="Maximum speed")
    maneuver = forms.IntegerField(required=False, help_text="Maneuver rating")
    crew = forms.CharField(max_length=100, required=False, help_text="Crew size and passenger capacity")
    structure = forms.IntegerField(required=False, help_text="Structure rating")
    weapons = forms.CharField(max_length=100, required=False, help_text="Weapon slots")
    requires_skill = forms.CharField(max_length=100, required=False, help_text="Required skill to operate")
    
    # Landcraft specific
    vehicle_type = forms.ChoiceField(choices=[
        ('', '---------'),
        ('truck', 'Truck'),
        ('car', 'Car'),
        ('suv', 'SUV'),
        ('bus', 'Bus'),
        ('tank', 'Tank'),
        ('other', 'Other')
    ], required=False, help_text="Type of land vehicle")
    mass_damage = forms.CharField(max_length=100, required=False, help_text="Additional damage dice from mass")
    passenger_protection = forms.CharField(max_length=100, required=False, help_text="Additional protection for passengers")
    
    # Aircraft specific
    aircraft_type = forms.ChoiceField(choices=[
        ('', '---------'),
        ('balloon', 'Hot Air Balloon'),
        ('helicopter', 'Helicopter'),
        ('prop_plane', 'Propeller Plane'),
        ('jet', 'Jet'),
        ('fighter', 'Fighter Jet'),
        ('other', 'Other')
    ], required=False, help_text="Type of aircraft")
    requires_specialty = forms.BooleanField(required=False, help_text="Requires specialty skill")
    specialty_type = forms.CharField(max_length=50, required=False, help_text="Type of specialty required")
    
    # Seacraft specific
    speed = forms.CharField(max_length=100, required=False, help_text="Speed of the seacraft")
    capacity = forms.IntegerField(required=False, help_text="Passenger capacity")
    
    # Jetpack specific
    is_technomagickal = forms.BooleanField(required=False, help_text="Is this a technomagickal vehicle?")
    
    # Supernatural item fields
    activation_requirements = forms.CharField(required=False, widget=forms.Textarea, help_text="Requirements to activate")
    duration = forms.CharField(max_length=100, required=False, help_text="Duration of effects")
    
    class Meta:
        model = Equipment
        fields = ['name', 'description', 'equipment_type', 'category', 'resources', 
                 'quantity', 'conceal', 'is_unique', 'requires_approval']
        exclude = ['sequential_id']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        
        if instance:
            # If editing an existing equipment, populate the category-specific fields
            category = instance.category
            details = instance.specialized_details
            
            if details:
                if category == 'ranged':
                    self.fields['damage'].initial = details.damage
                    self.fields['damage_type'].initial = details.damage_type
                    self.fields['range'].initial = details.range
                    self.fields['rate'].initial = details.rate
                    self.fields['clip'].initial = details.clip
                elif category == 'melee':
                    self.fields['damage'].initial = details.damage
                    self.fields['damage_type'].initial = details.damage_type
                    self.fields['difficulty'].initial = details.difficulty
                elif category == 'thrown':
                    self.fields['damage'].initial = details.damage
                    self.fields['damage_type'].initial = details.damage_type
                    self.fields['range'].initial = details.range
                    self.fields['difficulty'].initial = details.difficulty
                elif category == 'improvised':
                    self.fields['damage'].initial = details.damage
                    self.fields['damage_type'].initial = details.damage_type
                    self.fields['difficulty'].initial = details.difficulty
                    self.fields['break_chance'].initial = details.break_chance
                elif category == 'explosives':
                    self.fields['blast_area'].initial = details.blast_area
                    self.fields['blast_power'].initial = details.blast_power
                    self.fields['burn'].initial = details.burn
                    self.fields['notes'].initial = details.notes
                elif category == 'armor':
                    self.fields['rating'].initial = details.rating
                    self.fields['dexterity_penalty'].initial = details.dexterity_penalty
                    self.fields['is_shield'].initial = details.is_shield
                    self.fields['shield_bonus'].initial = details.shield_bonus
                elif category == 'ammunition':
                    self.fields['caliber'].initial = details.caliber
                    self.fields['damage_modifier'].initial = details.damage_modifier
                    self.fields['special_effects'].initial = details.special_effects
                elif category == 'special_ammunition':
                    self.fields['damage'].initial = details.damage
                    self.fields['effects'].initial = details.effects
                # Add other categories as needed
    
    def clean(self):
        """
        Validate that required fields for the selected category are provided.
        """
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        
        if category:
            # Define required fields for each category
            category_required_fields = {
                'ranged': ['damage', 'damage_type', 'range', 'rate', 'clip'],
                'melee': ['damage', 'damage_type', 'difficulty'],
                'thrown': ['damage', 'damage_type', 'range', 'difficulty'],
                'improvised': ['damage', 'damage_type', 'difficulty', 'break_chance'],
                'explosives': ['blast_area', 'blast_power'],
                'armor': ['rating', 'dexterity_penalty'],
                'ammunition': ['caliber', 'damage_modifier'],
                'special_ammunition': ['damage', 'effects'],
                # Add other categories as needed
            }
            
            # Check if the category has required fields
            if category in category_required_fields:
                for field_name in category_required_fields[category]:
                    value = cleaned_data.get(field_name)
                    if not value and value != 0:  # Allow zero as a valid value for numeric fields
                        self.add_error(field_name, f"This field is required for {category} equipment.")
        
        return cleaned_data
    
    def save(self, commit=True):
        # Save the base Equipment model
        equipment = super().save(commit=commit)
        
        if commit:
            # Save category-specific details
            category = equipment.category
            
            if category == 'ranged':
                # Get or create the RangedWeaponDetails
                details, created = RangedWeaponDetails.objects.get_or_create(equipment=equipment)
                details.damage = self.cleaned_data.get('damage', '')
                details.damage_type = self.cleaned_data.get('damage_type', '')
                details.range = self.cleaned_data.get('range', '')
                details.rate = self.cleaned_data.get('rate', '')
                details.clip = self.cleaned_data.get('clip') or 0
                details.save()
            elif category == 'melee':
                details, created = MeleeWeaponDetails.objects.get_or_create(equipment=equipment)
                details.damage = self.cleaned_data.get('damage', '')
                details.damage_type = self.cleaned_data.get('damage_type', '')
                details.difficulty = self.cleaned_data.get('difficulty') or 0
                details.save()
            elif category == 'thrown':
                details, created = ThrownWeaponDetails.objects.get_or_create(equipment=equipment)
                details.damage = self.cleaned_data.get('damage', '')
                details.damage_type = self.cleaned_data.get('damage_type', '')
                details.range = self.cleaned_data.get('range', '')
                details.difficulty = self.cleaned_data.get('difficulty') or 0
                details.save()
            elif category == 'improvised':
                details, created = ImprovisedWeaponDetails.objects.get_or_create(equipment=equipment)
                details.damage = self.cleaned_data.get('damage', '')
                details.damage_type = self.cleaned_data.get('damage_type', '')
                details.difficulty = self.cleaned_data.get('difficulty') or 0
                details.break_chance = self.cleaned_data.get('break_chance') or 50
                details.save()
            elif category == 'explosives':
                details, created = ExplosiveDetails.objects.get_or_create(equipment=equipment)
                details.blast_area = self.cleaned_data.get('blast_area', '')
                details.blast_power = self.cleaned_data.get('blast_power', '')
                details.burn = self.cleaned_data.get('burn', False)
                details.notes = self.cleaned_data.get('notes', '')
                details.save()
            elif category == 'armor':
                details, created = ArmorDetails.objects.get_or_create(equipment=equipment)
                details.rating = self.cleaned_data.get('rating') or 0
                details.dexterity_penalty = self.cleaned_data.get('dexterity_penalty') or 0
                details.is_shield = self.cleaned_data.get('is_shield', False)
                details.shield_bonus = self.cleaned_data.get('shield_bonus') or 0
                details.save()
            elif category == 'ammunition':
                details, created = AmmunitionDetails.objects.get_or_create(equipment=equipment)
                details.caliber = self.cleaned_data.get('caliber', '')
                details.damage_modifier = self.cleaned_data.get('damage_modifier', '')
                details.special_effects = self.cleaned_data.get('special_effects', '')
                details.save()
            elif category == 'special_ammunition':
                details, created = SpecialAmmunitionDetails.objects.get_or_create(equipment=equipment)
                details.damage = self.cleaned_data.get('damage', '')
                details.effects = self.cleaned_data.get('effects', '')
                details.save()
            # Add cases for other categories as needed
        
        return equipment 