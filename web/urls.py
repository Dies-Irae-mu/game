"""
This is the starting point when a user enters a url in their web browser.

The urls is matched (by regex) and mapped to a 'view' - a Python function or
callable class that in turn (usually) makes use of a 'template' (a html file
with slots that can be replaced by dynamic content) in order to render a HTML
page to show the user.

This file includes the urls in website, webclient and admin. To override you
should modify urls.py in those sub directories.

Search the Django documentation for "URL dispatcher" for more help.

"""

from django.urls import include, path
from django.shortcuts import redirect
from . import views
from django.conf import settings
from django.conf.urls.static import static

def redirect_to_wiki(request):
    return redirect('wiki:page_list')

# Custom URL patterns that should take precedence
custom_patterns = [
    # Add this at the top of your urlpatterns
    path('', redirect_to_wiki, name='index'),
    
    # Character URLs
    path('characters/', views.character_list, name='character-list'),
    path('characters/<str:key>/<int:dbref>/', views.sheet, name='character-detail'),
    path('characters/detail/<str:key>/<int:dbref>/', views.sheet, name='character-sheet'),
    path('characters/update/<str:key>/<int:dbref>/', views.update_character_field, name='character-update'),
    path('characters/upload/<str:key>/<int:dbref>/', views.upload_character_image, name='character-upload-image'),
    path('characters/set-primary-image/<str:key>/<int:dbref>/<int:image_id>/', views.set_primary_image, name='character-set-primary-image'),
    path('characters/delete-image/<str:key>/<int:dbref>/<int:image_id>/', views.delete_character_image, name='character-delete-image'),
    
    # Channel URLs
    path('channels/', views.channel_list, name='channel-list'),
    path('channels/<str:channel_name>/', views.channel_detail, name='channel-detail'),
    
    # Help system URLs
    path('help/', views.help_index, name='help-index'),
    path('help/<str:category>/', views.help_category, name='help-category'),
    path('help/topic/<str:category>/<path:topic>/', views.help_topic, name='help-topic'),
    
    # Wiki URLs
    path('wiki/', include('wiki.urls', namespace='wiki')),
    
    # Equipment URLs
    path('equipment/', include('world.equipment.urls', namespace='equipment')),
]

# Default Evennia patterns
from evennia.web.urls import urlpatterns as evennia_default_urlpatterns

# Filter out any character-related patterns from default patterns
filtered_default_patterns = [
    pattern for pattern in evennia_default_urlpatterns 
    if not any(x in str(pattern.pattern) for x in ['characters', 'character', 'channels', 'help'])
]

# Combine patterns, ensuring custom patterns take precedence
urlpatterns = custom_patterns + [
    # website
    path("", include("web.website.urls")),
    # webclient
    path("webclient/", include("web.webclient.urls")),
    # web admin
    path("admin/", include("web.admin.urls")),
] + filtered_default_patterns

# Add this at the end of the file, after urlpatterns definition
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Add the new markdown rendering URL
urlpatterns.append(path('characters/render-markdown/<str:key>/<str:dbref>/', views.render_markdown, name='character-render-markdown'))
