from django.urls import path
from . import views

app_name = 'equipment'

urlpatterns = [
    path('', views.equipment_list, name='equipment_list'),
    path('add/', views.add_equipment, name='add_equipment'),
    path('edit/<int:pk>/', views.edit_equipment, name='edit_equipment'),
    path('delete/<int:pk>/', views.delete_equipment, name='delete_equipment'),
] 