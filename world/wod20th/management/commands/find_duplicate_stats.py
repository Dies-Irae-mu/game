from django.core.management.base import BaseCommand
from world.wod20th.models import Stat
from django.db.models import Count

class Command(BaseCommand):
    help = 'Find duplicate stats based on name and stat_type'

    def handle(self, *args, **options):
        # Find duplicates
        duplicates = (
            Stat.objects.values('name', 'stat_type')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )

        if not duplicates:
            self.stdout.write(self.style.SUCCESS('No duplicates found!'))
            return

        self.stdout.write(self.style.WARNING('Found the following duplicates:'))
        
        for dup in duplicates:
            self.stdout.write(self.style.WARNING(
                f"\nName: {dup['name']}, Type: {dup['stat_type']}, Count: {dup['count']}"
            ))
            
            # Show details of each duplicate
            stats = Stat.objects.filter(
                name=dup['name'],
                stat_type=dup['stat_type']
            )
            
            for stat in stats:
                self.stdout.write(
                    f"  ID: {stat.id}\n"
                    f"  Description: {stat.description}\n"
                    f"  Game Line: {stat.game_line}\n"
                    f"  Category: {stat.category}\n"
                    f"  Values: {stat.values}\n"
                    f"  Splat: {stat.splat}\n"
                    f"  Hidden: {stat.hidden}\n"
                    f"  Locked: {stat.locked}\n"
                    "  " + "-"*40
                ) 