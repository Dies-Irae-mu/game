from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import WikiPage, WikiRevision, FeaturedImage

# Register your models here.

class FeaturedImageInline(admin.StackedInline):
    model = FeaturedImage
    can_delete = True
    max_num = 1
    
    class Media:
        js = ('wiki/js/featured-image-component.js',)
        css = {
            'all': ('wiki/css/admin.css',)
        }
    
    def get_fields(self, request, obj=None):
        fields = ['image', 'banner', 'show_texture']
        return fields

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name in ['image', 'banner']:
            formfield.widget.template_name = 'wiki/admin/image_input.html'
        return formfield

@admin.register(WikiPage)
class WikiPageAdmin(admin.ModelAdmin):
    """Admin interface for wiki pages."""
    
    list_display = ('title', 'page_type', 'creator', 'created_at', 'last_editor', 'updated_at', 'is_featured', 'featured_order', 'published', 'formatted_lock_settings')
    list_filter = ('page_type', 'created_at', 'updated_at', 'is_featured', 'is_index', 'published')
    search_fields = ('title', 'content', 'brief_description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [FeaturedImageInline]
    filter_horizontal = ('related_to',)
    list_editable = ('is_featured', 'featured_order', 'published')
    ordering = ('featured_order', 'title')
    
    class Media:
        js = ('wiki/js/admin-page-type.js',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'page_type', 'brief_description', 'content', 'right_content')
        }),
        ('Access Restrictions', {
            'fields': ('lock_settings',),
            'description': 'Define who can access this page based on character attributes. The lock settings are stored as a JSON object where keys are lock types (e.g., has_splat, has_clan) and values are the specific criteria (e.g., Vampire, Brujah).'
        }),
        ('Options', {
            'fields': ('is_featured', 'is_index', 'related_to'),
            'classes': ('collapse',)
        })
    )

    def formatted_lock_settings(self, obj):
        """Format lock settings for display in admin list view."""
        if not obj.lock_settings:
            return "No restrictions"
            
        formatted = []
        for lock_type, value in obj.lock_settings.items():
            # Format the lock type for display
            display_name = lock_type.replace('_', ' ').replace('has ', 'Has ').title()
            formatted.append(f"{display_name}: {value}")
            
        return format_html("<br>".join(formatted))
        
    formatted_lock_settings.short_description = "Access Restrictions"

    def save_model(self, request, obj, form, change):
        """Override save_model to pass the current user to the model's save method."""
        obj.save(current_user=request.user)

    def save_related(self, request, form, formsets, change):
        """Override save_related to ensure related objects are saved after the main object."""
        super().save_related(request, form, formsets, change)
        # Update last_editor after related objects are saved
        form.instance.last_editor = request.user
        form.instance.save(current_user=request.user)

    def view_on_site(self, obj):
        return obj.get_absolute_url()


@admin.register(WikiRevision)
class WikiRevisionAdmin(admin.ModelAdmin):
    """Admin interface for wiki revisions."""
    
    list_display = ('page', 'editor', 'edited_at', 'comment')
    list_filter = ('edited_at', 'editor')
    search_fields = ('page__title', 'content', 'comment')
    readonly_fields = ('edited_at',)
    
    fieldsets = (
        (None, {
            'fields': ('page', 'content', 'comment')
        }),
        ('Metadata', {
            'fields': ('editor', 'edited_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(FeaturedImage)
class FeaturedImageAdmin(admin.ModelAdmin):
    list_display = ('page', 'show_texture')
    list_filter = ('show_texture',)
