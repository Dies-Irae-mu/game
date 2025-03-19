"""
URL patterns for the situations app.
"""

from django.urls import path
from world.situations import views

app_name = 'situations'

urlpatterns = [
    # Situation URLs
    path('', views.SituationListView.as_view(), name='list'),
    path('<int:pk>/', views.SituationDetailView.as_view(), name='detail'),
    path('create/', views.SituationCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.SituationUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.SituationDeleteView.as_view(), name='delete'),
    
    # Detail URLs
    path('<int:situation_pk>/detail/create/', views.DetailCreateView.as_view(), name='detail_create'),
    path('detail/<int:pk>/edit/', views.DetailUpdateView.as_view(), name='detail_edit'),
    path('detail/<int:pk>/delete/', views.DetailDeleteView.as_view(), name='detail_delete'),
    
    # Development URLs
    path('<int:situation_pk>/development/create/', views.DevelopmentCreateView.as_view(), name='development_create'),
    path('development/<int:pk>/edit/', views.DevelopmentUpdateView.as_view(), name='development_edit'),
    path('development/<int:pk>/delete/', views.DevelopmentDeleteView.as_view(), name='development_delete'),
] 