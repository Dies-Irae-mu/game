"""
This reroutes from an URL to a python view-function/class.

The main web/urls.py includes these routes for all urls (the root of the url)
so it can reroute to all website pages.

"""

from django.urls import path
from web.views import sheet, update_character_field

from evennia.web.website.urls import urlpatterns as evennia_website_urlpatterns

# Filter out any character-related patterns from default patterns
filtered_website_patterns = [
    pattern for pattern in evennia_website_urlpatterns 
    if not any(x in str(pattern.pattern) for x in ['characters', 'character'])
]

# add patterns here
urlpatterns = [
    # Character sheet URL
    path('characters/detail/<str:key>/<str:dbref>/', sheet, name='character_sheet'),
    path('characters/update/<str:key>/<str:dbref>/', update_character_field, name='update_character_field'),
]

# read by Django
urlpatterns = urlpatterns + filtered_website_patterns
