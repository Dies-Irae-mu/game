from world.equipment.models import Equipment
from world.equipment.forms import EquipmentForm
from django.contrib import admin
from django.utils.html import format_html

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    form = EquipmentForm
    list_display = ('sequential_id', 'name', 'category_display', 'resources', 'is_unique', 'requires_approval', 'view_equipment')
    list_filter = ('equipment_type', 'category', 'is_unique', 'requires_approval')
    search_fields = ('name', 'description', 'sequential_id')
    ordering = ('sequential_id',)
    readonly_fields = ('sequential_id',)
    
    fieldsets = (
        (None, {
            'fields': ('sequential_id', 'name', 'description', 'equipment_type', 'category', 'resources', 
                     'quantity', 'conceal', 'is_unique', 'requires_approval'),
        }),
        ('Weapon Details', {
            'classes': ('ranged-fields', 'melee-fields', 'thrown-fields', 'improvised-fields', 'martial_arts-fields',),
            'fields': ('damage', 'damage_type', 'range', 'rate', 'clip', 'difficulty', 'break_chance', 
                      'style_requirements', 'special_techniques'),
        }),
        ('Explosive Details', {
            'classes': ('explosives-fields',),
            'fields': ('blast_area', 'blast_power', 'burn', 'notes'),
        }),
        ('Protection Details', {
            'classes': ('armor-fields',),
            'fields': ('rating', 'dexterity_penalty', 'is_shield', 'shield_bonus'),
        }),
        ('Ammunition Details', {
            'classes': ('ammunition-fields', 'special_ammunition-fields'),
            'fields': ('caliber', 'damage_modifier', 'special_effects', 'effects'),
        }),
        ('Vehicle Details', {
            'classes': ('landcraft-fields', 'aircraft-fields', 'seacraft-fields', 'cycle-fields', 'jetpack-fields'),
            'fields': ('safe_speed', 'max_speed', 'maneuver', 'crew', 'structure', 'weapons', 
                      'requires_skill', 'vehicle_type', 'mass_damage', 'passenger_protection', 
                      'aircraft_type', 'requires_specialty', 'specialty_type', 'capacity', 
                      'is_technomagickal'),
        }),
        ('Technical Details', {
            'classes': ('technocratic-fields', 'spying-fields', 'communications-fields', 'survival-fields', 'electronics-fields'),
            'fields': ('power_source', 'power_level', 'maintenance_required', 'maintenance_interval',
                      'function', 'stealth_rating', 'battery_life', 'encryption_level', 'weather_resistance'),
        }),
        ('Supernatural Details', {
            'classes': ('talisman-fields', 'device-fields', 'trinket-fields', 'gadget-fields', 'invention-fields',
                     'matrix-fields', 'grimoire-fields', 'biotech-fields', 'cybertech-fields', 'periapt-fields',
                     'chimerical-fields', 'treasure-fields', 'fetish-fields', 'talen-fields', 'artifact-fields'),
            'fields': ('activation_requirements', 'duration'),
        }),
    )
    
    def category_display(self, obj):
        """Display category with color-coding."""
        category_colors = {
            'ranged': 'red',
            'melee': 'orange',
            'thrown': 'brown',
            'improvised': 'purple',
            'explosives': 'darkred',
            'armor': 'blue',
            'ammunition': 'gray',
            'special_ammunition': 'darkgray',
            'landcraft': 'green',
            'aircraft': 'lightblue',
            'seacraft': 'navy',
        }
        color = category_colors.get(obj.category, 'black')
        return format_html('<span style="color: {};">{}</span>', color, obj.category.title())
    category_display.short_description = 'Category'
    
    def view_equipment(self, obj):
        """Provide a link to view the equipment in the web interface."""
        url = f'/admin/equipment/equipment/{obj.id}/change/'
        return format_html('<a href="{}" class="button">Edit Details</a>', url)
    view_equipment.short_description = 'Actions'

    def get_fieldsets(self, request, obj=None):
        """
        Hook for specifying fieldsets for the add/edit form.
        """
        return self.fieldsets