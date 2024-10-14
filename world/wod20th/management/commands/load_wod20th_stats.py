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
    help = 'Load or update WoD20th stats from a folder containing JSON files'

    def add_arguments(self, parser):
        parser.add_argument('json_folder', type=str, help='Path to the folder containing JSON files with stats')

    def handle(self, *args, **kwargs):
        json_folder = kwargs['json_folder']
        
        if not os.path.isdir(json_folder):
            self.stdout.write(self.style.ERROR(f'Folder {json_folder} not found.'))
            return

        self.stdout.write(self.style.NOTICE(f'Starting to process files in folder: {json_folder}'))

        for filename in os.listdir(json_folder):
            if filename.endswith('.json'):
                file_path = os.path.join(json_folder, filename)
                self.stdout.write(self.style.NOTICE(f'Processing file: {file_path}'))
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        stats_data = json.load(file)
                except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
                    self.stdout.write(self.style.ERROR(f'Error reading file {filename}: {str(e)}'))
                    continue
                
                for stat_data in stats_data:
                    self.process_stat(stat_data)

        self.stdout.write(self.style.SUCCESS('Finished processing all files.'))

    def process_stat(self, stat_data):
        name = stat_data.get('name')
        if not name:
            self.stdout.write(self.style.ERROR('Missing stat name in data. Skipping entry.'))
            return

        # Extract other fields...
        description = stat_data.get('description', '')
        game_line = stat_data.get('game_line')
        category = stat_data.get('category', 'other')
        stat_type = stat_data.get('stat_type', 'other')
        values = self.process_values(stat_data.get('values', []))
        lock_string = stat_data.get('lock_string', '')
        default = stat_data.get('default', '')
        instanced = stat_data.get('instanced', False)
        splat = stat_data.get('splat')
        hidden = stat_data.get('hidden', False)
        locked = stat_data.get('locked', False)

        # Validate data...
        if not game_line:
            self.stdout.write(self.style.ERROR(f'Missing game_line for stat {name}. Skipping entry.'))
            return

        # Ensure category and stat_type are valid
        category = category if category in dict(CATEGORIES) else 'other'
        stat_type = stat_type if stat_type in dict(STAT_TYPES) else 'other'

        # Try to get existing stat or create a new one
        stat, created = Stat.objects.get_or_create(
            name=name,
            game_line=game_line,
            defaults={
                'description': description,
                'category': category,
                'stat_type': stat_type,
                'values': values,
                'lock_string': lock_string,
                'default': default,
                'instanced': instanced,
                'splat': splat,
                'hidden': hidden,
                'locked': locked
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created new stat: {name}'))
        else:
            # Update existing stat if any fields have changed
            updated = False
            for field, value in stat_data.items():
                if field == 'values':
                    value = self.process_values(value)
                if getattr(stat, field) != value:
                    setattr(stat, field, value)
                    updated = True
            
            if updated:
                stat.save()
                self.stdout.write(self.style.SUCCESS(f'Updated existing stat: {name}'))
            else:
                self.stdout.write(self.style.NOTICE(f'No changes for existing stat: {name}'))

    def process_values(self, values):
        if isinstance(values, dict):
            values_list = []
            for key in ['permanent', 'temporary', 'perm', 'temp']:
                if key in values:
                    values_list.extend(values[key])
            return values_list
        elif isinstance(values, list):
            return values
        else:
            return []
