from django.core.management.base import BaseCommand
from world.wod20th.models import Stat

class Command(BaseCommand):
    help = 'Clears all WoD20th stats from the database'

    def handle(self, *args, **options):
        count = Stat.objects.all().count()
        Stat.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} stats.'))