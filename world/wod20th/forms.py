# world/wod20th/forms.py
from django import forms
from .models import Stat

class StatForm(forms.ModelForm):
    class Meta:
        model = Stat
        fields = ['name', 'description', 'game_line', 'category', 'stat_type', 'values']
        widgets = {
            'values': forms.Textarea(attrs={'rows': 3}),
        }