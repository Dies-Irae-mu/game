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

# Define forms_data at module level for import
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
        'Sokto': {
            'tribe_modifiers': {
                'bagheera': {'Strength': 1, 'Dexterity': 1, 'Stamina': 2, 'Manipulation': -1, 'Appearance': -1},
                'balam': {'Strength': 2, 'Dexterity': 1, 'Stamina': 2, 'Manipulation': -1, 'Appearance': -1},
                'bubasti': {'Dexterity': 1, 'Appearance': 1},
                'ceilican': {'Dexterity': 2, 'Stamina': 1, 'Appearance': 1},
                'khan': {'Strength': 2, 'Dexterity': 1, 'Stamina': 2, 'Manipulation': -1, 'Appearance': -1},
                'pumonca': {'Strength': 1, 'Dexterity': 2, 'Stamina': 2, 'Manipulation': -1},
                'qualmi': {'Dexterity': 2, 'Appearance': 1},
                'simba': {'Strength': 2, 'Dexterity': 1, 'Stamina': 2, 'Manipulation': -1, 'Appearance': 1},
                'swara': {'Strength': 1, 'Dexterity': 2, 'Stamina': 1, 'Manipulation': -1}
            },
            'difficulty': 7,
            'rage_cost': 1
        },
        'Crinos': {
            'tribe_modifiers': {
                'bagheera': {'Strength': 3, 'Dexterity': 3, 'Stamina': 3, 'Manipulation': -3, 'Appearance': 0},
                'balam': {'Strength': 3, 'Dexterity': 3, 'Stamina': 3, 'Manipulation': -4, 'Appearance': 0},
                'bubasti': {'Strength': 1, 'Dexterity': 3, 'Stamina': 1, 'Manipulation': -2, 'Appearance': -3},
                'ceilican': {'Strength': 1, 'Dexterity': 3, 'Stamina': 1, 'Manipulation': 0, 'Appearance': -2},
                'khan': {'Strength': 5, 'Dexterity': 2, 'Stamina': 3, 'Manipulation': -3, 'Appearance': 0},
                'pumonca': {'Strength': 3, 'Dexterity': 3, 'Stamina': 4, 'Manipulation': -3, 'Appearance': 0},
                'qualmi': {'Strength': 1, 'Dexterity': 3, 'Stamina': 1, 'Manipulation': -2, 'Appearance': 0},
                'simba': {'Strength': 4, 'Dexterity': 2, 'Stamina': 3, 'Manipulation': -2, 'Appearance': 0},
                'swara': {'Strength': 2, 'Dexterity': 4, 'Stamina': 3, 'Manipulation': -3, 'Appearance': 0}
            },
            'difficulty': 6,
            'rage_cost': 1
        },
        'Chatro': {
            'tribe_modifiers': {
                'bagheera': {'Strength': 2, 'Dexterity': 3, 'Stamina': 3, 'Manipulation': -3, 'Appearance': -2},
                'balam': {'Strength': 3, 'Dexterity': 2, 'Stamina': 3, 'Manipulation': -4},
                'bubasti': {'Strength': 2, 'Dexterity': 4, 'Stamina': 1, 'Manipulation': -2},
                'ceilican': {'Dexterity': 4, 'Stamina': 1, 'Manipulation': -2, 'Appearance': -2},
                'khan': {'Strength': 4, 'Dexterity': 2, 'Stamina': 3, 'Manipulation': -3},
                'pumonca': {'Strength': 3, 'Dexterity': 3, 'Stamina': 3, 'Manipulation': -3},
                'qualmi': {'Strength': 1, 'Dexterity': 4, 'Stamina': 1, 'Manipulation': -2},
                'simba': {'Strength': 3, 'Dexterity': 4, 'Stamina': 2, 'Manipulation': -2},
                'swara': {'Strength': 2, 'Dexterity': 4, 'Stamina': 3, 'Manipulation': -3}
            },
            'difficulty': 7,
            'rage_cost': 1
        },
        'Feline': {
            'tribe_modifiers': {
                'bagheera': {'Strength': 1, 'Dexterity': 3, 'Stamina': 2, 'Manipulation': -3},
                'balam': {'Strength': 2, 'Dexterity': 3, 'Stamina': 2, 'Manipulation': -3},
                'bubasti': {'Strength': -1, 'Dexterity': 4, 'Stamina': 1},
                'ceilican': {'Strength': -1, 'Dexterity': 4, 'Manipulation': -2},
                'khan': {'Strength': 3, 'Dexterity': 2, 'Stamina': 3, 'Manipulation': -3},
                'pumonca': {'Strength': 2, 'Dexterity': 3, 'Stamina': 3},
                'qualmi': {'Dexterity': 4, 'Manipulation': -2},
                'simba': {'Strength': 3, 'Dexterity': 3, 'Stamina': 2, 'Manipulation': -1},
                'swara': {'Strength': 1, 'Dexterity': 4, 'Stamina': 2, 'Manipulation': -3}
            },
            'difficulty': 6,
            'rage_cost': 1
        }
    },
    'corax': {
        'Homid': {'stat_modifiers': {}, 'difficulty': 6, 'rage_cost': 0},
        'Crinos': {'stat_modifiers': {'Strength': 2, 'Dexterity': 2, 'Stamina': 2, 'Manipulation': -2, 'Perception': 3, 'Appearance': 0}, 'difficulty': 6, 'rage_cost': 1},
        'Corvid': {'stat_modifiers': {'Strength': -1, 'Dexterity': 3, 'Stamina': -1, 'Manipulation': -2, 'Perception': 4}, 'difficulty': 6, 'rage_cost': 1}
    },
    'ananasi': {
        'Homid': {'stat_modifiers': {}, 'difficulty': 6, 'rage_cost': 0},
        'Lilian': {'stat_modifiers': {'Strength': 2, 'Dexterity': 3, 'Stamina': 2, 'Manipulation': -1}, 'difficulty': 6, 'rage_cost': 1},
        'Pithus': {'stat_modifiers': {'Strength': 4, 'Dexterity': 1, 'Stamina': 3, 'Manipulation': -3}, 'difficulty': 6, 'rage_cost': 1},
        'Crawlerling': {'stat_modifiers': {'Strength': 0, 'Dexterity': 5, 'Stamina': 0, 'Manipulation': 0}, 'difficulty': 6, 'rage_cost': 1}
    },
    'mokole': {
        'Homid': {'stat_modifiers': {}, 'difficulty': 6, 'rage_cost': 0},
        'Archid': {'stat_modifiers': {'Strength': 4, 'Dexterity': -1, 'Stamina': 4, 'Manipulation': -3}, 'difficulty': 6, 'rage_cost': 1},
        'Suchid': {
            'stat_modifiers': {
                'Champsa': {'Strength': 3, 'Dexterity': -2, 'Stamina': 3, 'Manipulation': -4},  # Nile crocodile
                'Gharial': {'Strength': 1, 'Dexterity': -1, 'Stamina': 3, 'Manipulation': -4},  # Gavails
                'Halpatee': {'Strength': 2, 'Dexterity': -1, 'Stamina': 3, 'Manipulation': -2},  # American alligator
                'Karna': {'Strength': 3, 'Dexterity': -2, 'Stamina': 3, 'Manipulation': -4},  # Saltwater Crocodile
                'Makara': {'Strength': 1, 'Dexterity': 0, 'Stamina': 2, 'Manipulation': -3},  # Mugger crocodile, Chinese alligator
                'Ora': {'Strength': 0, 'Dexterity': 0, 'Stamina': 2, 'Manipulation': -4},  # Monitor lizards
                'Piasa': {'Strength': 2, 'Dexterity': -1, 'Stamina': 3, 'Manipulation': -2},  # American crocodile
                'Syrta': {'Strength': 1, 'Dexterity': -1, 'Stamina': 3, 'Manipulation': -4},  # Caimans
                'Unktehi': {'Strength': -1, 'Dexterity': 0, 'Stamina': 1, 'Manipulation': -3}  # Gila monster
            },
            'difficulty': 7,
            'rage_cost': 1
        }
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

class Command(BaseCommand):
    help = 'Initialize shapeshifter forms in the database'

    def handle(self, *args, **options):
        create_shifter_forms()
        self.stdout.write(self.style.SUCCESS('Successfully initialized shapeshifter forms'))

def create_shifter_forms():
    # Create forms for each shifter type
    for shifter_type, forms in forms_data.items():
        print(f"Creating forms for {shifter_type}...")
        for form_name, data in forms.items():
            try:
                # Special handling for forms with variant modifiers (Mokole Suchid and Bastet forms)
                if shifter_type == 'mokole' and form_name == 'Suchid':
                    # Use Makara stats as default
                    makara_stats = data['stat_modifiers']['Makara']
                    stat_modifiers = makara_stats.copy()
                    description = f"Mokolé {form_name} form\nVarna-specific modifiers:\n"
                    for varna, mods in data['stat_modifiers'].items():
                        description += f"\n{varna}:\n"
                        for stat, mod in mods.items():
                            description += f"  {stat}: {mod:+d}\n"
                elif shifter_type == 'bastet' and 'tribe_modifiers' in data:
                    # Use Simba stats as default for Bastet forms
                    simba_stats = data['tribe_modifiers']['simba']
                    stat_modifiers = simba_stats.copy()
                    description = f"Bastet {form_name} form\nTribe-specific modifiers:\n"
                    for tribe, mods in data['tribe_modifiers'].items():
                        description += f"\n{tribe.title()}:\n"
                        for stat, mod in mods.items():
                            description += f"  {stat}: {mod:+d}\n"
                else:
                    stat_modifiers = data['stat_modifiers']
                    description = f'{shifter_type.capitalize()} {form_name} form'

                # Update or create the form
                form, created = ShapeshifterForm.objects.update_or_create(
                    name=form_name,
                    shifter_type=shifter_type,
                    defaults={
                        'description': description,
                        'stat_modifiers': stat_modifiers,
                        'difficulty': data.get('difficulty', 6),
                        'rage_cost': data.get('rage_cost', 1),
                        'lock_string': 'examine:all();control:perm(Admin)'
                    }
                )
                print(f"  {'Created' if created else 'Updated'} form: {form_name}")
            except Exception as e:
                print(f"  Error creating {form_name}: {str(e)}")

    print("Shifter forms initialization complete.")

    # Run this script to reset forms and reinitialize them in the shell:
    # from world.wod20th.models import ShapeshifterForm; ShapeshifterForm.objects.all().delete(); from world.wod20th.forms import create_shifter_forms; create_shifter_forms()