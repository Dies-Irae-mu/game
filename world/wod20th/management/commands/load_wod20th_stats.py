import json
import os
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.db import connection

# Import Evennia and initialize it
import evennia
evennia._init()

# Ensure Django settings are configured
import django
django.setup()

# Import the Stat model
from world.wod20th.models import Stat

class Command(BaseCommand):
    help = 'Load WoD20th stats from a folder containing JSON files'

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
                    with open(file_path, 'r') as file:
                        stats_data = json.load(file)
                        self.stdout.write(self.style.SUCCESS(f'Successfully loaded JSON data from {file_path}'))
                except FileNotFoundError:
                    self.stdout.write(self.style.ERROR(f'File {file_path} not found.'))
                    continue
                except json.JSONDecodeError:
                    self.stdout.write(self.style.ERROR(f'Error decoding JSON from file {file_path}.'))
                    continue
                
                for stat_data in stats_data:
                    self.stdout.write(self.style.NOTICE(f'Processing stat data: {stat_data}'))
                    
                    name = stat_data.get('name')
                    if not name:
                        self.stdout.write(self.style.ERROR('Missing stat name in data. Skipping entry.'))
                        continue
                    
                    description = stat_data.get('description', '')
                    game_line = stat_data.get('game_line')
                    category = stat_data.get('category')
                    stat_type = stat_data.get('stat_type')
                    values = stat_data.get('values', [])
                    lock_string = stat_data.get('lock_string', '')

                    # Data validation
                    if not game_line or not category or not stat_type:
                        self.stdout.write(self.style.ERROR(f'Invalid data for stat {name}. Skipping entry.'))
                        continue

                    # Ensure values are a list
                    if not isinstance(values, list):
                        self.stdout.write(self.style.ERROR(f'Invalid values for stat {name}. Values must be a list. Skipping entry.'))
                        continue

                    # Check if stat already exists
                    existing_stat = Stat.objects.filter(name=name, game_line=game_line, category=category, stat_type=stat_type).first()
                    if existing_stat:
                        self.stdout.write(self.style.WARNING(f'Stat {name} already exists. Skipping entry.'))
                        continue
                    
                    # Create new stat
                    stat = Stat(
                        name=name,
                        description=description,
                        game_line=game_line,
                        category=category,
                        stat_type=stat_type,
                        values=values,
                        lock_string=lock_string
                    )

                    try:
                        # Validate the model before saving
                        stat.full_clean()
                        stat.save()
                        self.stdout.write(self.style.SUCCESS(f'Successfully created stat: {stat.name}'))
                    except ValidationError as e:
                        self.stdout.write(self.style.ERROR(f'Validation error for stat {stat.name}: {e}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error saving stat {stat.name}: {e}'))
                        self.stdout.write(self.style.ERROR(f'Stat object: {stat.__dict__}'))
                        if connection.queries:
                            last_query = connection.queries[-1]
                            self.stdout.write(self.style.ERROR(f'SQL: {last_query.get("sql", "N/A")}'))
                            self.stdout.write(self.style.ERROR(f'SQL params: {last_query.get("params", "N/A")}'))
                        else:
                            self.stdout.write(self.style.ERROR('No SQL queries recorded.'))

        self.stdout.write(self.style.SUCCESS('Finished processing all files.'))
