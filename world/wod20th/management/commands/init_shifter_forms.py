"""
Initialize shapeshifter forms in the database.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from evennia.utils import logger

class Command(BaseCommand):
    help = 'Initialize shapeshifter forms in the database'

    def handle(self, *args, **options):
        """
        Initialize all shapeshifter forms in the database.
        """
        try:
            # Import here to avoid circular imports
            from world.wod20th.models import ShapeshifterForm
            
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
                },
                'bastet': {
                    'Homid': {'stat_modifiers': {}, 'difficulty': 6, 'rage_cost': 0},
                    'Sokto': {
                        'tribe_modifiers': {
                            'bagheera': {'Strength': 1, 'Dexterity': 1, 'Stamina': 2, 'Manipulation': -1, 'Appearance': -1},
                            'balam': {'Strength': 2, 'Dexterity': 1, 'Stamina': 2, 'Manipulation': -1, 'Appearance': -1},
                            'bubasti': {'Strength': 0, 'Dexterity': 1, 'Stamina': 0, 'Manipulation': 0, 'Appearance': 1},
                            'ceilican': {'Strength': 0, 'Dexterity': 2, 'Stamina': 1, 'Manipulation': 0, 'Appearance': 1},
                            'khan': {'Strength': 2, 'Dexterity': 1, 'Stamina': 2, 'Manipulation': -1, 'Appearance': -1},
                            'pumonca': {'Strength': 1, 'Dexterity': 2, 'Stamina': 2, 'Manipulation': -1, 'Appearance': 0},
                            'qualmi': {'Strength': 0, 'Dexterity': 2, 'Stamina': 0, 'Manipulation': 0, 'Appearance': 1},
                            'simba': {'Strength': 2, 'Dexterity': 1, 'Stamina': 2, 'Manipulation': -1, 'Appearance': 1},
                            'swara': {'Strength': 1, 'Dexterity': 2, 'Stamina': 1, 'Manipulation': -1, 'Appearance': 0}
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
                            'balam': {'Strength': 3, 'Dexterity': 2, 'Stamina': 3, 'Manipulation': -4, 'Appearance': 0},
                            'bubasti': {'Strength': 2, 'Dexterity': 4, 'Stamina': 1, 'Manipulation': -2, 'Appearance': 0},
                            'ceilican': {'Strength': 0, 'Dexterity': 4, 'Stamina': 1, 'Manipulation': -2, 'Appearance': -2},
                            'khan': {'Strength': 4, 'Dexterity': 2, 'Stamina': 3, 'Manipulation': -3, 'Appearance': 0},
                            'pumonca': {'Strength': 3, 'Dexterity': 3, 'Stamina': 3, 'Manipulation': -3, 'Appearance': 0},
                            'qualmi': {'Strength': 1, 'Dexterity': 4, 'Stamina': 1, 'Manipulation': -2, 'Appearance': 0},
                            'simba': {'Strength': 3, 'Dexterity': 4, 'Stamina': 2, 'Manipulation': -2, 'Appearance': 0},
                            'swara': {'Strength': 2, 'Dexterity': 4, 'Stamina': 3, 'Manipulation': -3, 'Appearance': 0}
                        },
                        'difficulty': 7,
                        'rage_cost': 1
                    },
                    'Feline': {
                        'tribe_modifiers': {
                            'bagheera': {'Strength': 1, 'Dexterity': 3, 'Stamina': 2, 'Manipulation': -3},
                            'balam': {'Strength': 2, 'Dexterity': 3, 'Stamina': 2, 'Manipulation': -3},
                            'bubasti': {'Strength': -1, 'Dexterity': 4, 'Stamina': 1, 'Manipulation': 0},
                            'ceilican': {'Strength': -1, 'Dexterity': 4, 'Stamina': 0, 'Manipulation': -2},
                            'khan': {'Strength': 3, 'Dexterity': 2, 'Stamina': 3, 'Manipulation': -3},
                            'pumonca': {'Strength': 2, 'Dexterity': 3, 'Stamina': 3, 'Manipulation': 0},
                            'qualmi': {'Strength': 0, 'Dexterity': 4, 'Stamina': 0, 'Manipulation': -2},
                            'simba': {'Strength': 3, 'Dexterity': 3, 'Stamina': 2, 'Manipulation': -1},
                            'swara': {'Strength': 1, 'Dexterity': 4, 'Stamina': 2, 'Manipulation': -3}
                        },
                        'difficulty': 6,
                        'rage_cost': 1
                    }
                }
            }

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
                            logger.log_info(f'Created {form_name} form')
                            self.stdout.write(self.style.SUCCESS(f'Created {form_name} form'))
                        else:
                            logger.log_info(f'Updated {form_name} form')
                            self.stdout.write(self.style.SUCCESS(f'Updated {form_name} form'))

                    except Exception as e:
                        logger.log_err(f'Error creating/updating {form_name} form: {str(e)}')
                        self.stdout.write(self.style.ERROR(f'Error creating/updating {form_name} form: {str(e)}'))
                        continue

                # Create Bastet forms
                for form_name, form_data in forms_data['bastet'].items():
                    if 'tribe_modifiers' in form_data:
                        # Use Simba stats as default stat_modifiers (as they are often considered the "standard" Bastet)
                        simba_stats = form_data['tribe_modifiers']['simba']
                        stat_modifiers = simba_stats.copy()
                        
                        # Store tribe-specific modifiers in description
                        description = f"Bastet {form_name} form\nTribe-specific modifiers:\n"
                        for tribe, mods in form_data['tribe_modifiers'].items():
                            description += f"\n{tribe.title()}:\n"
                            for stat, mod in mods.items():
                                description += f"  {stat}: {mod:+d}\n"
                    else:
                        stat_modifiers = form_data['stat_modifiers']
                        description = f'Bastet {form_name} form'

                    try:
                        form, created = ShapeshifterForm.objects.update_or_create(
                            name=form_name,
                            shifter_type='bastet',
                            defaults={
                                'description': description,
                                'stat_modifiers': stat_modifiers,
                                'difficulty': form_data['difficulty'],
                                'rage_cost': form_data['rage_cost'],
                                'lock_string': 'examine:all();control:perm(Admin)'
                            }
                        )

                        if created:
                            logger.log_info(f'Created Bastet {form_name} form')
                            self.stdout.write(self.style.SUCCESS(f'Created Bastet {form_name} form'))
                        else:
                            logger.log_info(f'Updated Bastet {form_name} form')
                            self.stdout.write(self.style.SUCCESS(f'Updated Bastet {form_name} form'))

                    except Exception as e:
                        logger.log_err(f'Error creating/updating Bastet {form_name} form: {str(e)}')
                        self.stdout.write(self.style.ERROR(f'Error creating/updating Bastet {form_name} form: {str(e)}'))
                        continue

            logger.log_info('Successfully initialized Mokolé and Bastet forms')
            self.stdout.write(self.style.SUCCESS('Successfully initialized Mokolé and Bastet forms'))

        except Exception as e:
            logger.log_err(f'Error initializing forms: {str(e)}')
            self.stdout.write(self.style.ERROR(f'Error initializing forms: {str(e)}'))
            raise