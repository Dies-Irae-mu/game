#!/usr/bin/env python
"""
Script to update Mokolé shapeshifter forms in the database.
Run this script directly with: python update_mokole_forms.py
"""
import os
import sys
import django

# Set up Django environment
os.environ['DJANGO_SETTINGS_MODULE'] = 'server.conf.settings'
django.setup()

from django.db import transaction
from world.wod20th.models import ShapeshifterForm

def update_mokole_forms():
    """Update Mokolé shapeshifter forms."""
    # Dictionary of all shapeshifter forms
    forms_data = {
        'mokole': {
            'Homid': {'stat_modifiers': {}, 'difficulty': 6, 'rage_cost': 0},
            'Archid': {'stat_modifiers': {'Strength': 4, 'Dexterity': -1, 'Stamina': 4, 'Manipulation': -3}, 'difficulty': 6, 'rage_cost': 1},
            'Suchid': {
                'varna_modifiers': {
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
        }
    }

    try:
        # Use a transaction to ensure database consistency
        with transaction.atomic():
            # Create Mokolé forms
            for form_name, form_data in forms_data['mokole'].items():
                # For Suchid form, use Makara as default stats
                if form_name == 'Suchid':
                    # Use Makara stats as default stat_modifiers
                    makara_stats = form_data['varna_modifiers']['Makara']
                    stat_modifiers = {
                        'Strength': makara_stats['Strength'],
                        'Dexterity': makara_stats['Dexterity'],
                        'Stamina': makara_stats['Stamina'],
                        'Manipulation': makara_stats['Manipulation']
                    }
                    # Store Varna-specific modifiers in description
                    description = f"Mokolé {form_name} form\nVarna-specific modifiers:\n"
                    for varna, mods in form_data['varna_modifiers'].items():
                        description += f"\n{varna}:\n"
                        for stat, mod in mods.items():
                            description += f"  {stat}: {mod:+d}\n"
                else:
                    stat_modifiers = form_data['stat_modifiers']
                    description = f'Mokolé {form_name} form'

                try:
                    form, created = ShapeshifterForm.objects.update_or_create(
                        name=form_name,
                        shifter_type='mokole',
                        defaults={
                            'description': description,
                            'stat_modifiers': stat_modifiers,
                            'difficulty': form_data['difficulty'],
                            'rage_cost': form_data['rage_cost'],
                            'lock_string': 'examine:all();control:perm(Admin)'
                        }
                    )

                    if created:
                        print(f'Created {form_name} form')
                    else:
                        print(f'Updated {form_name} form')

                except Exception as e:
                    print(f'Error creating/updating {form_name} form: {str(e)}')
                    continue

            print('Successfully initialized Mokolé forms')

    except Exception as e:
        print(f'Error initializing forms: {str(e)}')
        raise

if __name__ == '__main__':
    # Add the parent directory to sys.path
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    sys.path.append(parent_dir)
    
    update_mokole_forms() 