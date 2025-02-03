# world/wod20th/forms.py
from django import forms
from .models import Stat, ShapeshifterForm
from django.core.management.base import BaseCommand

class StatForm(forms.ModelForm):
    class Meta:
        model = Stat
        fields = ['name', 'description', 'game_line', 'category', 'stat_type', 'values']
        widgets = {
            'values': forms.Textarea(attrs={'rows': 3}),
        }

class Command(BaseCommand):
    help = 'Initialize shapeshifter forms in the database'

    def handle(self, *args, **options):
        create_shifter_forms()
        self.stdout.write(self.style.SUCCESS('Successfully initialized shapeshifter forms'))

def create_shifter_forms():
    forms_data = {
        'garou': {
            'Homid': {'stat_modifiers': {}, 'difficulty': 6, 'rage_cost': 0},
            'Glabro': {'stat_modifiers': {'Strength': 2, 'Stamina': 2, 'Manipulation': -1, 'Appearance': -1}, 'difficulty': 7, 'rage_cost': 1},
            'Crinos': {'stat_modifiers': {'Strength': 4, 'Dexterity': 1, 'Stamina': 3, 'Manipulation': -3}, 'difficulty': 6, 'rage_cost': 1},
            'Hispo': {'stat_modifiers': {'Strength': 3, 'Dexterity': 2, 'Stamina': 3, 'Manipulation': -3}, 'difficulty': 7, 'rage_cost': 1},
            'Lupus': {'stat_modifiers': {'Strength': 1, 'Dexterity': 2, 'Stamina': 2, 'Manipulation': -3}, 'difficulty': 6, 'rage_cost': 1}
        },
        'ajaba': {
            'Homid': {'stat_modifiers': {}, 'difficulty': 6, 'rage_cost': 0},
            'Anthros': {'stat_modifiers': {'Strength': 2, 'Stamina': 2, 'Manipulation': -1, 'Appearance': -1}, 'difficulty': 7, 'rage_cost': 1},
            'Crinos': {'stat_modifiers': {'Strength': 3, 'Dexterity': 2, 'Stamina': 4, 'Manipulation': -2}, 'difficulty': 6, 'rage_cost': 1},
            'Crocas': {'stat_modifiers': {'Strength': 2, 'Dexterity': 3, 'Stamina': 3, 'Manipulation': -2}, 'difficulty': 7, 'rage_cost': 1},
            'Hyaenid': {'stat_modifiers': {'Strength': 1, 'Dexterity': 2, 'Stamina': 2, 'Manipulation': -2}, 'difficulty': 6, 'rage_cost': 1}
        },
        'kitsune': {
            'Homid': {'stat_modifiers': {}, 'difficulty': 6, 'rage_cost': 0},
            'Sambuhenge': {'stat_modifiers': {'Dexterity': 1, 'Stamina': 1, 'Manipulation': -1}, 'difficulty': 7, 'rage_cost': 1},
            'Koto': {'stat_modifiers': {'Strength': 1, 'Dexterity': 2, 'Stamina': 2, 'Manipulation': -1, 'Perception': 1}, 'difficulty': 6, 'rage_cost': 1},
            'Juko': {'stat_modifiers': {'Dexterity': 3, 'Stamina': 3, 'Manipulation': -2, 'Perception': 1}, 'difficulty': 7, 'rage_cost': 1},
            'Kyubi': {'stat_modifiers': {'Dexterity': 4, 'Stamina': 2, 'Manipulation': -1, 'Perception': 2}, 'difficulty': 6, 'rage_cost': 1}
        },
        'gurahl': {
            'Homid': {'stat_modifiers': {}, 'difficulty': 6, 'rage_cost': 0},
            'Arthren': {'stat_modifiers': {'Strength': 3, 'Stamina': 3, 'Manipulation': -1, 'Appearance': -1}, 'difficulty': 7, 'rage_cost': 1},
            'Crinos': {'stat_modifiers': {'Strength': 5, 'Dexterity': -1, 'Stamina': 5, 'Manipulation': -3}, 'difficulty': 6, 'rage_cost': 1},
            'Bjornen': {'stat_modifiers': {'Strength': 4, 'Dexterity': -1, 'Stamina': 4, 'Manipulation': -3}, 'difficulty': 7, 'rage_cost': 1},
            'Ursus': {'stat_modifiers': {'Strength': 3, 'Dexterity': -1, 'Stamina': 3, 'Manipulation': -3}, 'difficulty': 6, 'rage_cost': 1}
        },
        'nuwisha': {
            'Homid': {'stat_modifiers': {}, 'difficulty': 6, 'rage_cost': 0},
            'Tsitsu': {'stat_modifiers': {'Strength': 1, 'Dexterity': 1, 'Stamina': 2, 'Manipulation': -1}, 'difficulty': 7, 'rage_cost': 1},
            'Manabozho': {'stat_modifiers': {'Strength': 2, 'Dexterity': 3, 'Stamina': 3, 'Manipulation': -2}, 'difficulty': 6, 'rage_cost': 1},
            'Sendeh': {'stat_modifiers': {'Strength': 2, 'Dexterity': 3, 'Stamina': 3, 'Manipulation': -3}, 'difficulty': 7, 'rage_cost': 1},
            'Latrani': {'stat_modifiers': {'Dexterity': 3, 'Stamina': 3, 'Manipulation': -3}, 'difficulty': 6, 'rage_cost': 1}
        },
        'bastet': {
            'Homid': {'stat_modifiers': {}, 'difficulty': 6, 'rage_cost': 0},
            'Sokto': {'stat_modifiers': {'Strength': 1, 'Dexterity': 2, 'Stamina': 1, 'Manipulation': -1, 'Appearance': -1}, 'difficulty': 7, 'rage_cost': 1},
            'Crinos': {'stat_modifiers': {'Strength': 2, 'Dexterity': 3, 'Stamina': 3, 'Manipulation': -3}, 'difficulty': 6, 'rage_cost': 1},
            'Chatro': {'stat_modifiers': {'Strength': 2, 'Dexterity': 4, 'Stamina': 2, 'Manipulation': -2}, 'difficulty': 7, 'rage_cost': 1},
            'Feline': {'stat_modifiers': {'Strength': 1, 'Dexterity': 4, 'Stamina': 1, 'Manipulation': -2}, 'difficulty': 6, 'rage_cost': 1}
        },
        'corax': {
            'Homid': {'stat_modifiers': {}, 'difficulty': 6, 'rage_cost': 0},
            'Crinos': {'stat_modifiers': {'Strength': 2, 'Dexterity': 2, 'Stamina': 2, 'Manipulation': -2}, 'difficulty': 6, 'rage_cost': 1},
            'Corvid': {'stat_modifiers': {'Strength': -1, 'Dexterity': 3, 'Stamina': -1, 'Manipulation': -2}, 'difficulty': 6, 'rage_cost': 1}
        },
        'ananasi': {
            'Homid': {'stat_modifiers': {}, 'difficulty': 6, 'rage_cost': 0},
            'Lilian': {'stat_modifiers': {'Strength': 2, 'Dexterity': 3, 'Stamina': 2, 'Manipulation': -1}, 'difficulty': 6, 'rage_cost': 1},
            'Pithus': {'stat_modifiers': {'Strength': 4, 'Dexterity': 1, 'Stamina': 3, 'Manipulation': -3}, 'difficulty': 6, 'rage_cost': 1},
            'Crawlerling': {'stat_modifiers': {'Strength': -5, 'Dexterity': 5, 'Stamina': -5, 'Manipulation': -5}, 'difficulty': 6, 'rage_cost': 1}
        },
        'mokole': {
            'Homid': {'stat_modifiers': {}, 'difficulty': 6, 'rage_cost': 0},
            'Archid': {'stat_modifiers': {'Strength': 4, 'Dexterity': -1, 'Stamina': 4, 'Manipulation': -3}, 'difficulty': 6, 'rage_cost': 1},
            'Suchid': {'stat_modifiers': {'Strength': -1, 'Dexterity': 0, 'Stamina': 1, 'Manipulation': -3}, 'difficulty': 7, 'rage_cost': 1}
        },
        'ratkin': {
            'Homid': {'stat_modifiers': {}, 'difficulty': 6, 'rage_cost': 0},
            'Crinos': {'stat_modifiers': {'Strength': 2, 'Dexterity': 3, 'Stamina': 2, 'Manipulation': -2}, 'difficulty': 6, 'rage_cost': 1},
            'Rodens': {'stat_modifiers': {'Strength': -1, 'Dexterity': 3, 'Stamina': -1, 'Manipulation': -2}, 'difficulty': 7, 'rage_cost': 1}
        },
        'nagah': {
            'Homid': {'stat_modifiers': {}, 'difficulty': 6, 'rage_cost': 0},
            'Silkaram': {'stat_modifiers': {'Strength': 2, 'Stamina': 2, 'Manipulation': -2, 'Appearance': -2}, 'difficulty': 7, 'rage_cost': 1},
            'Azhi': {'stat_modifiers': {'Strength': 3, 'Dexterity': 2, 'Stamina': 3, 'Manipulation': -3}, 'difficulty': 6, 'rage_cost': 1},
            'Kali': {'stat_modifiers': {'Strength': 2, 'Dexterity': 2, 'Stamina': 2, 'Manipulation': -3}, 'difficulty': 7, 'rage_cost': 1},
            'Vasuki': {'stat_modifiers': {'Strength': -1, 'Dexterity': 2, 'Stamina': 1, 'Manipulation': -5}, 'difficulty': 6, 'rage_cost': 1}
        },
        'rokea': {
            'Homid': {'stat_modifiers': {}, 'difficulty': 6, 'rage_cost': 0},
            'Glabrus': {'stat_modifiers': {'Strength': 2, 'Stamina': 2, 'Manipulation': -2, 'Appearance': -2}, 'difficulty': 7, 'rage_cost': 1},
            'Gladius': {'stat_modifiers': {'Strength': 3, 'Dexterity': -1, 'Stamina': 2, 'Manipulation': -4, 'Appearance': -5}, 'difficulty': 6, 'rage_cost': 1},
            'Chasmus': {'stat_modifiers': {'Strength': 4, 'Dexterity': 1, 'Stamina': 3, 'Manipulation': -4}, 'difficulty': 7, 'rage_cost': 1},
            'Squamus': {'stat_modifiers': {'Strength': 2, 'Dexterity': 3, 'Stamina': 2, 'Manipulation': -4}, 'difficulty': 6, 'rage_cost': 1}
        }
    }

    # Create forms for each shifter type
    for shifter_type, forms in forms_data.items():
        print(f"Creating forms for {shifter_type}...")
        for form_name, data in forms.items():
            try:
                form, created = ShapeshifterForm.objects.get_or_create(
                    name=form_name,
                    shifter_type=shifter_type,
                    defaults={
                        'description': f'{shifter_type.capitalize()} {form_name} form',
                        'stat_modifiers': data.get('stat_modifiers', {}),
                        'difficulty': data.get('difficulty', 6),
                        'rage_cost': data.get('rage_cost', 1),
                        'lock_string': 'examine:all();control:perm(Admin)'  # Default lock string
                    }
                )
                print(f"  {'Created' if created else 'Found'} form: {form_name}")
            except Exception as e:
                print(f"  Error creating {form_name}: {str(e)}")

    print("Shifter forms initialization complete.")