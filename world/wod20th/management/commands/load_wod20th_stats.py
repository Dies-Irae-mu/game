import json
import os
import time
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Track failed files and stats
        self.failed_files = []
        self.failed_stats = []
        self.processed_files = 0
        self.processed_stats = 0
        self.failed_count = 0

    def add_arguments(self, parser):
        parser.add_argument('--dir', type=str, default='data', help='Directory containing JSON files')
        parser.add_argument('--file', type=str, help='Specific JSON file to load (optional)')
        parser.add_argument('--delay', type=int, default=5, help='Delay in seconds between processing files (default: 5)')

    def handle(self, *args, **options):
        data_dir = options['dir']
        specific_file = options['file']
        delay = options['delay']

        if specific_file:
            # Process single file
            file_path = os.path.join(data_dir, specific_file)
            self.process_file(file_path)
        else:
            # Process all JSON files in directory
            if not os.path.isdir(data_dir):
                self.stdout.write(self.style.ERROR(f'Directory not found: {data_dir}'))
                return

            self.stdout.write(self.style.NOTICE(f'Processing JSON files in {data_dir} with {delay} second delay between files...'))
            json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
            
            for i, filename in enumerate(json_files):
                file_path = os.path.join(data_dir, filename)
                self.process_file(file_path)
                
                # Add delay between files (except after the last file)
                if i < len(json_files) - 1 and delay > 0:
                    self.stdout.write(self.style.NOTICE(f'Waiting {delay} seconds before processing next file...'))
                    time.sleep(delay)

        # Display summary at the end
        self.display_summary()

    def display_summary(self):
        """Display a summary of the processing results"""
        self.stdout.write("\n=== Processing Summary ===")
        self.stdout.write(f"Total files processed: {self.processed_files}")
        self.stdout.write(f"Total stats processed: {self.processed_stats}")
        self.stdout.write(f"Total failures: {self.failed_count}")

        if self.failed_files:
            self.stdout.write("\nFailed Files:")
            for file_info in self.failed_files:
                self.stdout.write(self.style.ERROR(f"- {file_info['file']}: {file_info['error']}"))

        if self.failed_stats:
            self.stdout.write("\nFailed Stats:")
            for stat_info in self.failed_stats:
                self.stdout.write(self.style.ERROR(
                    f"- {stat_info['name']} (in {stat_info['file']}): {stat_info['error']}"
                ))

    def process_file(self, file_path):
        if not os.path.exists(file_path):
            self.failed_files.append({
                'file': file_path,
                'error': 'File not found'
            })
            self.failed_count += 1
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
                    self.process_stat(stat_data, file_path)
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
                                self.process_stat(ability_data, file_path)
                else:
                    # Handle regular dictionary of stats
                    for stat_name, stat_data in data.items():
                        if isinstance(stat_data, dict):
                            stat_data['name'] = stat_name
                            self.process_stat(stat_data, file_path)
                        else:
                            self.process_stat({
                                'name': stat_name,
                                'value': stat_data,
                                'category': 'other',
                                'stat_type': 'other'
                            }, file_path)

            self.processed_files += 1
            self.stdout.write(self.style.SUCCESS(f'Successfully loaded stats from {file_path}'))
        except json.JSONDecodeError:
            self.failed_files.append({
                'file': file_path,
                'error': 'Invalid JSON format'
            })
            self.failed_count += 1
            self.stdout.write(self.style.ERROR(f'Invalid JSON in file: {file_path}'))
        except Exception as e:
            self.failed_files.append({
                'file': file_path,
                'error': str(e)
            })
            self.failed_count += 1
            self.stdout.write(self.style.ERROR(f'Error processing {file_path}: {str(e)}'))

    def process_stat(self, stat_data, file_path):
        if not isinstance(stat_data, dict):
            self.failed_stats.append({
                'name': 'Unknown',
                'file': file_path,
                'error': f'Invalid stat data format: {stat_data}'
            })
            self.failed_count += 1
            self.stdout.write(self.style.ERROR(f'Invalid stat data format: {stat_data}'))
            return

        name = stat_data.get('name')
        if not name:
            self.failed_stats.append({
                'name': 'Unknown',
                'file': file_path,
                'error': 'Stat missing name'
            })
            self.failed_count += 1
            self.stdout.write(self.style.ERROR('Stat missing name'))
            return

        # Handle shifter_type for gifts and merits
        stat_type = stat_data.get('stat_type', 'other')
        if stat_type == 'gift' or (stat_type in ['physical', 'social', 'mental', 'supernatural'] and stat_data.get('category') == 'merits'):
            shifter_type = stat_data.get('shifter_type', [])
            if isinstance(shifter_type, str):
                shifter_type = [shifter_type]
            elif not isinstance(shifter_type, list):
                shifter_type = []
        else:
            shifter_type = None

        # Create or update the stat using both name and stat_type as unique identifiers
        try:
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
                    'prerequisites': stat_data.get('prerequisites', []),
                    'shifter_type': shifter_type,
                    'gift_alias': stat_data.get('gift_alias', []),
                    'tribe': stat_data.get('tribe', []),
                    'breed': stat_data.get('breed', ''),
                    'auspice': stat_data.get('auspice', ''),
                    'camp': stat_data.get('camp', ''),
                }
            )

            self.processed_stats += 1
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} stat: {name}'))
        except Exception as e:
            self.failed_stats.append({
                'name': name,
                'file': file_path,
                'error': str(e)
            })
            self.failed_count += 1
            self.stdout.write(self.style.ERROR(f'Error saving stat {name}: {str(e)}'))

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
        # Get shifter_type from the data, ensuring it's a list
        shifter_type = gift_data.get('shifter_type', [])
        if isinstance(shifter_type, str):
            shifter_type = [shifter_type]
        elif not isinstance(shifter_type, list):
            shifter_type = []

        # Handle tribe data similarly
        tribe_data = gift_data.get('tribe', [])
        if isinstance(tribe_data, str):
            tribe_data = [tribe_data]
        elif not isinstance(tribe_data, list):
            tribe_data = []

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
                'shifter_type': shifter_type,
                'splat': gift_data.get('splat', ''),
                'tribe': tribe_data,
                'camp': gift_data.get('camp', ''),
                'system': gift_data.get('system', ''),
                'gift_alias': gift_data.get('gift_alias', [])
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
            stat.shifter_type = shifter_type
            stat.splat = gift_data.get('splat', '')
            stat.tribe = tribe_data
            stat.camp = gift_data.get('camp', '')
            stat.system = gift_data.get('system', '')
            stat.gift_alias = gift_data.get('gift_alias', [])
            stat.save()