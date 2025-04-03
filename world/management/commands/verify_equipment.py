from django.core.management.base import BaseCommand
from world.equipment.verify_equipment import verify_equipment

class Command(BaseCommand):
    help = 'Verifies all equipment in the database'

    def handle(self, *args, **options):
        verify_equipment() 