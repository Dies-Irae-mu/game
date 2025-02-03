from django.urls import path
from . import views

app_name = 'wiki'

urlpatterns = [
    path('', views.page_list, name='page_list'),
    path('search/', views.search_wiki, name='search'),
    path('<slug:slug>/', views.page_detail, name='page_detail'),
    path('<slug:slug>/history/', views.page_history, name='page_history'),
]
