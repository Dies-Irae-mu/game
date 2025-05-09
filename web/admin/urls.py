"""
This reroutes from an URL to a python view-function/class.

The main web/urls.py includes these routes for all urls starting with `admin/`
(the `admin/` part should not be included again here).

"""

from django.urls import path, include
from django.contrib import admin
from evennia.web.admin.urls import urlpatterns as evennia_admin_urlpatterns

# Register NPC admin models
admin.autodiscover()

# add patterns here
urlpatterns = [
    # Custom NPC admin links
    path('npcs/', include('world.npc_manager.urls')),
]

# read by Django
urlpatterns = urlpatterns + evennia_admin_urlpatterns
