# world/wod20th/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('stats/', views.stat_list, name='stat_list'),
    path('stats/add/', views.add_stat, name='add_stat'),
]
