from django.urls import path
from web.character.views import sheet

app_name = 'character'

urlpatterns = [
    path('sheet/<int:dbref>/', sheet, name='sheet'),
] 
