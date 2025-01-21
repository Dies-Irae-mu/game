import json
import os
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.db import transaction, connection, IntegrityError

# Import Evennia and initialize it
import evennia
evennia._init()

# Ensure Django settings are configured
import django
django.setup()

# Import the Stat model
from world.wod20th.models import Stat, CATEGORIES, STAT_TYPES

class Command(BaseCommand):
    help = 'Load WoD20th stats from JSON files in a directory'

    def add_arguments(self, parser):
        parser.add_argument('--dir', type=str, default='data', help='Directory containing JSON files')
        parser.add_argument('--file', type=str, help='Specific JSON file to load (optional)')

    def handle(self, *args, **options):
        data_dir = options['dir']
        specific_file = options['file']

        if specific_file:
            # Process single file
            file_path = os.path.join(data_dir, specific_file)
            self.process_file(file_path)
        else:
            # Process all JSON files in directory
            if not os.path.isdir(data_dir):
                self.stdout.write(self.style.ERROR(f'Directory not found: {data_dir}'))
                return

            self.stdout.write(self.style.NOTICE(f'Processing JSON files in {data_dir}...'))
            for filename in os.listdir(data_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(data_dir, filename)
                    self.process_file(file_path)

    def process_file(self, file_path):
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        try:
            self.stdout.write(self.style.NOTICE(f'Processing {file_path}...'))
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle different data structures
            if isinstance(data, list):
                # Handle flat array of stats
                for stat_data in data:
                    self.process_stat(stat_data)
            elif isinstance(data, dict):
                # Check if this is a splat-specific abilities file
                if any(isinstance(v, dict) and any(k in ['talents', 'skills', 'knowledges'] for k in v.keys()) for v in data.values()):
                    # Process splat-specific abilities
                    for splat, categories in data.items():
                        for category_type, abilities in categories.items():
                            for ability_name, ability_data in abilities.items():
                                # Ensure the ability data has the splat information
                                ability_data['splat'] = splat
                                ability_data['name'] = ability_name
                                self.process_stat(ability_data)
                else:
                    # Handle regular dictionary of stats
                    for stat_name, stat_data in data.items():
                        if isinstance(stat_data, dict):
                            stat_data['name'] = stat_name
                            self.process_stat(stat_data)
                        else:
                            self.process_stat({
                                'name': stat_name,
                                'value': stat_data,
                                'category': 'other',
                                'stat_type': 'other'
                            })

            self.stdout.write(self.style.SUCCESS(f'Successfully loaded stats from {file_path}'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Invalid JSON in file: {file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing {file_path}: {str(e)}'))

    def process_stat(self, stat_data):
        if not isinstance(stat_data, dict):
            self.stdout.write(self.style.ERROR(f'Invalid stat data format: {stat_data}'))
            return

        name = stat_data.get('name')
        if not name:
            self.stdout.write(self.style.ERROR('Stat missing name'))
            return

        # Create or update the stat using both name and stat_type as unique identifiers
        try:
            stat_type = stat_data.get('stat_type', 'other')
            stat, created = Stat.objects.update_or_create(
                name=name,
                stat_type=stat_type,  # Add stat_type to unique identifier
                defaults={
                    'description': stat_data.get('description', ''),
                    'game_line': stat_data.get('game_line', 'general'),
                    'category': stat_data.get('category', 'other'),
                    'values': stat_data.get('values', []),
                    'system': stat_data.get('system', ''),
                    'splat': stat_data.get('splat'),
                    'notes': stat_data.get('notes', ''),
                    'hidden': stat_data.get('hidden', False),
                    'locked': stat_data.get('locked', False),
                    'instanced': stat_data.get('instanced', False),
                    'default': stat_data.get('default'),
                    'xp_cost': stat_data.get('xp_cost', 0),
                    'prerequisites': stat_data.get('prerequisites', [])
                }
            )

            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} stat: {name} ({stat_type})'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating/updating stat {name}: {str(e)}'))

    def handle_ability(self, ability_data):
        """Handle loading an ability stat"""
        stat, created = Stat.objects.get_or_create(
            name=ability_data['name'],
            defaults={
                'description': ability_data.get('description', ''),
                'game_line': ability_data.get('game_line', 'Various'),
                'category': ability_data.get('category', 'abilities'),
                'stat_type': ability_data.get('stat_type', 'ability'),
                'values': ability_data.get('values', {}),
                'system': ability_data.get('system', ''),
                'splat_specific': ability_data.get('splat_specific', False),
                'allowed_splats': ability_data.get('allowed_splats', {})
            }
        )
        if not created:
            # Update existing stat with new data
            stat.description = ability_data.get('description', '')
            stat.game_line = ability_data.get('game_line', 'Various')
            stat.category = ability_data.get('category', 'abilities')
            stat.stat_type = ability_data.get('stat_type', 'ability')
            stat.values = ability_data.get('values', {})
            stat.splat_specific = ability_data.get('splat_specific', False)
            stat.allowed_splats = ability_data.get('allowed_splats', {})
            stat.system = ability_data.get('system', '')
            stat.save()

    def handle_gift(self, gift_data):
        """Handle loading a gift stat"""
        stat, created = Stat.objects.get_or_create(
            name=gift_data['name'],
            defaults={
                'description': gift_data.get('description', ''),
                'game_line': gift_data.get('game_line', 'Various'),
                'category': gift_data.get('category', 'gifts'),
                'stat_type': gift_data.get('stat_type', 'gift'),
                'values': gift_data.get('values', {}),
                'splat_specific': gift_data.get('splat_specific', False),
                'allowed_splats': gift_data.get('allowed_splats', {}),
                'shifter_type': gift_data.get('shifter_type', ''),
                'splat': gift_data.get('splat', ''),
                'tribe': gift_data.get('tribe', ''),
                'camp': gift_data.get('camp', ''),
                'system': gift_data.get('system','')
            }
        )
        
        if not created:
            # Update existing stat with new data
            stat.description = gift_data.get('description', '')
            stat.game_line = gift_data.get('game_line', 'Various')
            stat.category = gift_data.get('category', 'gifts')
            stat.stat_type = gift_data.get('stat_type', 'gift')
            stat.values = gift_data.get('values', {})
            stat.splat_specific = gift_data.get('splat_specific', False)
            stat.allowed_splats = gift_data.get('allowed_splats', {})
            stat.shifter_type = gift_data.get('shifter_type', '')
            stat.splat = gift_data.get('splat', '')
            stat.tribe = gift_data.get('tribe', '')
            stat.camp = gift_data.get('camp', '')
            stat.system = gift_data.get('system', '')
            stat.save()