from django.core.management.base import BaseCommand
from evennia.objects.models import ObjectDB
from typeclasses.rooms import RoomParent
import json

class Command(BaseCommand):
    help = 'Generates a JSON map of all rooms in the game'

    def handle(self, *args, **options):
        rooms = ObjectDB.objects.filter(db_typeclass_path__contains='rooms.RoomParent')
        room_map = {}

        for room in rooms:
            room_data = {
                'id': room.id,
                'name': room.name,
                'location_type': room.db.location_type,
                'exits': [],
                'contents': [],
            }

            # Add exits
            for exit in room.exits:
                if exit.destination:
                    room_data['exits'].append({
                        'name': exit.name,
                        'destination_id': exit.destination.id,
                    })

            # Add contents (excluding exits)
            for obj in room.contents:
                if not obj.destination:  # This excludes exits
                    room_data['contents'].append({
                        'id': obj.id,
                        'name': obj.name,
                        'typeclass': obj.typeclass_path,
                    })

            room_map[room.id] = room_data

        # Convert to JSON
        json_map = json.dumps(room_map, indent=2)

        # Save to file
        with open('room_map.json', 'w') as f:
            f.write(json_map)

        self.stdout.write(self.style.SUCCESS('Successfully generated room map'))