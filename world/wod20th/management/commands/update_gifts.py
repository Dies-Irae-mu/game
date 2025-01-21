from django.core.management.base import BaseCommand
from world.wod20th.models import Stat
import json
import os

class Command(BaseCommand):
    help = "Updates gift JSON files with shifter types"

    def handle(self, *args, **options):
        # Dictionary mapping file names to shifter types and splats
        GIFT_FILES = {
            'ananasi_gifts.json': ('ananasi', 'Fera'),
            'gurahl_gifts.json': ('gurahl', 'Fera'),
            'corax_gifts.json': ('corax', 'Fera'),
            'ajaba_gifts.json': ('ajaba', 'Fera'),
            'shifter_gifts.json': ('garou', 'Garou')
        }

        # Get the directory where the data files are located
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        data_dir = os.path.join(base_dir, 'data')

        # First, update all existing gifts in database to have correct shifter type based on splat
        gifts = Stat.objects.filter(stat_type='gift')
        for gift in gifts:
            if gift.splat == 'Garou':
                gift.shifter_type = 'garou'
            elif gift.splat == 'Fera':
                # Try to determine Fera type from the gift's traits or description
                if 'Ananasi' in gift.description:
                    gift.shifter_type = 'ananasi'
                elif 'Gurahl' in gift.description:
                    gift.shifter_type = 'gurahl'
                elif 'Corax' in gift.description:
                    gift.shifter_type = 'corax'
                elif 'Ajaba' in gift.description:
                    gift.shifter_type = 'ajaba'
            gift.save()
            self.stdout.write(f"Updated {gift.name} with shifter_type: {gift.shifter_type}")

        # Then process any new gifts from files
        for filename, (shifter_type, splat) in GIFT_FILES.items():
            file_path = os.path.join(data_dir, filename)
            
            try:
                # Read the existing JSON file
                with open(file_path, 'r', encoding='utf-8') as f:
                    gifts = json.load(f)

                # Update each gift with the shifter_type and splat
                for gift_data in gifts:
                    gift, created = Stat.objects.update_or_create(
                        name=gift_data['name'],
                        stat_type='gift',
                        defaults={
                            'shifter_type': shifter_type,
                            'splat': splat,
                            'description': gift_data.get('description', ''),
                            'values': gift_data.get('values', [])
                        }
                    )
                    self.stdout.write(f"{'Created' if created else 'Updated'} {gift.name} with shifter_type: {gift.shifter_type}")

                self.stdout.write(self.style.SUCCESS(f"Successfully processed {filename}"))

            except FileNotFoundError:
                self.stdout.write(self.style.WARNING(f"Warning: {filename} not found in {data_dir}"))
            except json.JSONDecodeError:
                self.stdout.write(self.style.ERROR(f"Error: {filename} contains invalid JSON"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing {filename}: {str(e)}"))