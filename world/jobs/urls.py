from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    # Job views
    path('', views.job_list, name='job_list'),
    path('create/', views.job_create, name='job_create'),
    path('<int:pk>/', views.job_detail, name='job_detail'),
    path('<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('<int:pk>/claim/', views.job_claim, name='job_claim'),
    path('<int:pk>/close/', views.job_close, name='job_close'),
    
    # Archive views
    path('archive/', views.job_archive, name='job_archive'),
    path('archive/<int:pk>/', views.job_archive_detail, name='job_archive_detail'),
    
    # Queue views
    path('queues/', views.queue_list, name='queue_list'),
    path('queues/create/', views.queue_create, name='queue_create'),
    path('queues/<int:pk>/edit/', views.queue_edit, name='queue_edit'),
    
    # Template views
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
    
    # AJAX endpoints
    path('search-objects/', views.search_objects, name='search_objects'),
] 