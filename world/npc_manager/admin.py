"""
Django admin configuration for NPC models.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.apps import apps

# Get models by string reference
NPCPosition = apps.get_model('npc_manager', 'NPCPosition')
NPC = apps.get_model('npc_manager', 'NPC')
NPCGroup = apps.get_model('npc_manager', 'NPCGroup')

class NPCGoalInline(admin.TabularInline):
    """Inline admin for NPC Goals."""
    model = None  # Will be set later
    extra = 1
    fields = ['db_text', 'db_order', 'db_completed']

class NPCPositionInline(admin.TabularInline):
    """Inline admin for NPC Positions."""
    model = None  # Will be set later
    extra = 1
    fields = ['npc', 'db_title', 'db_order']

class NPCInline(admin.TabularInline):
    """Inline admin for NPCs."""
    model = None  # Will be set later
    extra = 1
    fields = ['db_key', 'db_splat', 'db_difficulty', 'db_is_temporary']
    readonly_fields = ['db_key']
    # We don't want to edit NPCs directly from the group, just show them
    can_delete = False
    show_change_link = True
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(NPCGroup)
class NPCGroupAdmin(admin.ModelAdmin):
    """Admin interface for NPC Groups."""
    list_display = ['db_key', 'db_group_type', 'db_splat', 'db_difficulty', 
                    'npcs_count', 'object_link', 'db_date_created']
    list_filter = ['db_group_type', 'db_splat', 'db_difficulty']
    search_fields = ['db_key', 'db_description', 'db_territory']
    fieldsets = [
        ('Basic Information', {
            'fields': [
                'db_key', 'db_group_type', 'db_description',
                ('db_splat', 'db_difficulty')
            ]
        }),
        ('Group Details', {
            'fields': ['db_territory', 'db_resources', 'db_influence']
        }),
        ('System Fields', {
            'classes': ['collapse'],
            'fields': ['db_object', 'db_creator']
        }),
    ]
    inlines = []  # Will be set later
    
    def npcs_count(self, obj):
        """Display the number of NPCs in the group."""
        count = obj.npcs.count()
        return format_html('<span style="font-weight:bold">{}</span>', count)
    npcs_count.short_description = "NPCs"
    
    def object_link(self, obj):
        """Display a link to the in-game object."""
        if obj.db_object:
            return format_html('<a href="/admin/objects/objectdb/{}/change/">#{}</a>',
                              obj.db_object.id, obj.db_object.id)
        return "Not created"
    object_link.short_description = "Game Object"
    
    actions = ['create_in_game_objects']
    
    def create_in_game_objects(self, request, queryset):
        """Admin action to create in-game objects for selected groups."""
        created = 0
        for group in queryset:
            if not group.db_object:
                group.create_in_game_group()
                created += 1
        
        self.message_user(
            request, 
            f"Created {created} in-game NPCGroup objects."
        )
    create_in_game_objects.short_description = "Create in-game objects for selected groups"

@admin.register(NPC)
class NPCAdmin(admin.ModelAdmin):
    """Admin interface for NPCs."""
    list_display = ['db_key', 'db_group', 'db_splat', 'db_difficulty', 
                    'db_is_temporary', 'positions_display', 'object_link']
    list_filter = ['db_group', 'db_splat', 'db_difficulty', 'db_is_temporary']
    search_fields = ['db_key', 'db_description']
    fieldsets = [
        ('Basic Information', {
            'fields': [
                'db_key', 'db_description', 
                ('db_splat', 'db_difficulty')
            ]
        }),
        ('Status', {
            'fields': ['db_is_temporary', 'db_expiration_time']
        }),
        ('Group Membership', {
            'fields': ['db_group', 'db_group_number']
        }),
        ('System Fields', {
            'classes': ['collapse'],
            'fields': ['db_object', 'db_creator']
        }),
    ]
    inlines = []  # Will be set later
    
    def positions_display(self, obj):
        """Display positions in a compact format."""
        # Import inside the method to avoid circular imports
        from .models import NPCPosition
        positions = NPCPosition.objects.filter(npc=obj)
        if not positions:
            return "-"
        
        return ", ".join(p.db_title for p in positions[:3]) + \
               ("..." if positions.count() > 3 else "")
    positions_display.short_description = "Positions"
    
    def object_link(self, obj):
        """Display a link to the in-game object."""
        if obj.db_object:
            return format_html('<a href="/admin/objects/objectdb/{}/change/">#{}</a>',
                              obj.db_object.id, obj.db_object.id)
        return "Not created"
    object_link.short_description = "Game Object"
    
    actions = ['create_in_game_objects']
    
    def create_in_game_objects(self, request, queryset):
        """Admin action to create in-game objects for selected NPCs."""
        created = 0
        for npc in queryset:
            if not npc.db_object:
                npc.create_in_game_npc()
                created += 1
        
        self.message_user(
            request, 
            f"Created {created} in-game NPC objects."
        )
    create_in_game_objects.short_description = "Create in-game objects for selected NPCs"

# Import models after admin classes are defined to avoid circular imports
from .models import NPC, NPCGroup, NPCGoal, NPCPosition

# Set the models for inline classes
NPCGoalInline.model = NPCGoal
NPCPositionInline.model = NPCPosition
NPCInline.model = NPC

# Add inlines to admin classes
NPCGroupAdmin.inlines = [NPCGoalInline, NPCInline]
NPCAdmin.inlines = [NPCPositionInline]

# Register any remaining models
admin.site.register(NPCGoal)
admin.site.register(NPCPosition)