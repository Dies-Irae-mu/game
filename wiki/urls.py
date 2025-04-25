from django.urls import path
from . import views

app_name = 'wiki'

urlpatterns = [
    path('', views.page_list, name='page_list'),
    path('search/', views.search_wiki, name='search'),
    
    # Group pages
    path('groups/', views.groups_index, name='groups_index'),
    path('groups/create/', views.create_group, name='create_group'),
    path('groups/<slug:slug>/', views.group_detail, name='group_detail'),
    path('groups/<slug:slug>/edit/', views.edit_group, name='edit_group'),
    
    # Plot pages
    path('plots/', views.plots_index, name='plots_index'),
    path('plots/create/', views.create_plot, name='create_plot'),
    path('plots/<slug:slug>/', views.plot_detail, name='plot_detail'),
    path('plots/<slug:slug>/edit/', views.edit_plot, name='edit_plot'),
    
    # Edit pages
    path('create/', views.create_page, name='create_page'),
    path('<slug:slug>/edit/', views.edit_page, name='edit_page'),
    
    # Preview functionality
    path('preview/', views.preview_markdown, name='preview'),
    
    # Default page views - these should be last as they're most general
    path('<slug:slug>/', views.page_detail, name='page_detail'),
    path('<slug:slug>/history/', views.page_history, name='page_history'),
]
