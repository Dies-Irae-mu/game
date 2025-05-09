"""
URL patterns for the NPC Manager app.
"""
from django.urls import path
from . import views

app_name = 'npc_manager'

urlpatterns = [
    path('', views.index, name='index'),
    path('npcs/', views.npc_list, name='npc_list'),
    path('npcs/<int:npc_id>/', views.npc_detail, name='npc_detail'),
    path('groups/', views.group_list, name='group_list'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),
    path('sync/', views.sync_npcs, name='sync_npcs'),
] 