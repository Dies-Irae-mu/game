from django.core.management.base import BaseCommand
from world.wod20th.models import Stat
from django.db.models import Count

class Command(BaseCommand):
    help = 'Fix duplicate stats by keeping the most complete record'

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

        total_fixed = 0
        for dup in duplicates:
            self.stdout.write(f"\nProcessing duplicates for {dup['name']} ({dup['stat_type']})...")
            
            # Get all duplicates for this name/type
            stats = list(Stat.objects.filter(
                name=dup['name'],
                stat_type=dup['stat_type']
            ).order_by('id'))
            
            if not stats:
                continue

            # Keep the first record (oldest) as base
            keep = stats[0]
            
            # Merge data from other records into the first one
            for stat in stats[1:]:
                # Update non-null fields if the base record has null/empty values
                if not keep.description and stat.description:
                    keep.description = stat.description
                if not keep.game_line and stat.game_line:
                    keep.game_line = stat.game_line
                if not keep.values and stat.values:
                    keep.values = stat.values
                if not keep.splat and stat.splat:
                    keep.splat = stat.splat
                if not keep.lock_string and stat.lock_string:
                    keep.lock_string = stat.lock_string
                
                # Delete the duplicate
                self.stdout.write(f"  Deleting duplicate ID: {stat.id}")
                stat.delete()
                total_fixed += 1
            
            # Save the merged record
            keep.save()

        if total_fixed:
            self.stdout.write(self.style.SUCCESS(f'\nFixed {total_fixed} duplicate records'))
        else:
            self.stdout.write(self.style.SUCCESS('\nNo duplicates needed fixing')) 