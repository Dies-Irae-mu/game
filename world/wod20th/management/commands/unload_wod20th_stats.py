import evennia
evennia._init()

import django
django.setup()

from django.core.management.base import BaseCommand
from world.wod20th.models import Stat

class Command(BaseCommand):
    help = 'Unload all WoD20th stats from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion without confirmation',
        )

    def handle(self, *args, **options):
        stat_count = Stat.objects.count()
        
        if stat_count == 0:
            self.stdout.write(self.style.SUCCESS("No stats found in the database. Nothing to unload."))
            return

        if not options['force']:
            confirm = input(f"Are you sure you want to delete all {stat_count} stats? This action cannot be undone. (y/N): ")
            if confirm.lower() != 'y':
                self.stdout.write(self.style.WARNING("Operation cancelled."))
                return

        Stat.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"Successfully deleted all {stat_count} stats from the database."))