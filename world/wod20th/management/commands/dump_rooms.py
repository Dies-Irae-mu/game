"""
Management command to dump all room information to a file.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from datetime import datetime
import os

class Command(BaseCommand):
    """
    Dumps all room information to a file.
    """
    help = "Creates a log file containing information about all rooms in the game."

    def handle(self, *args, **options):
        """
        Implements the command.
        """
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"room_log_{timestamp}.txt"

        # Direct SQL query to get rooms
        with connection.cursor() as cursor:
            # Get all rooms
            cursor.execute("""
                SELECT 
                    o.id,
                    o.db_key,
                    o.db_typeclass_path,
                    a.db_value as description
                FROM 
                    objects_objectdb o
                LEFT JOIN 
                    objects_objectattribute a 
                    ON o.id = a.db_object_id 
                    AND a.db_key = 'desc'
                WHERE 
                    o.db_typeclass_path IN (
                        'typeclasses.rooms.Room',
                        'typeclasses.rooms.RoomParent'
                    )
                ORDER BY 
                    o.id;
            """)
            rooms = cursor.fetchall()

            if not rooms:
                self.stdout.write(self.style.ERROR("No rooms found in the database."))
                return

            # Open file for writing
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("ROOM LOG\n")
                f.write("=" * 80 + "\n\n")
                
                # Process each room
                for room_id, name, typeclass, desc in rooms:
                    try:
                        # Write room name/key and typeclass
                        f.write(f"Name/key: {name} (#{room_id})\n")
                        f.write(f"Typeclass: {typeclass}\n")
                        
                        # Write description
                        f.write("Description:\n")
                        if desc:
                            f.write(str(desc) + "\n")
                        else:
                            f.write("No description set.\n")
                        
                        # Get exits for this room
                        cursor.execute("""
                            SELECT 
                                o.id,
                                o.db_key,
                                o.db_destination_id,
                                d.db_key as dest_name,
                                d.id as dest_id
                            FROM 
                                objects_objectdb o
                            LEFT JOIN 
                                objects_objectdb d ON o.db_destination_id = d.id
                            WHERE 
                                o.db_location_id = %s
                                AND o.db_typeclass_path IN (
                                    'typeclasses.exits.Exit',
                                    'evennia.objects.objects.DefaultExit',
                                    'typeclasses.exits.ApartmentExit'
                                );
                        """, [room_id])
                        exits = cursor.fetchall()
                        
                        # Write exits
                        f.write("Exits:\n")
                        if exits:
                            for exit_id, exit_name, dest_id, dest_name, dest_dbref in exits:
                                if dest_name and dest_dbref:
                                    f.write(f"  {exit_name} (#{exit_id}) -> {dest_name} (#{dest_dbref})\n")
                        else:
                            f.write("  No exits.\n")
                        
                        # Add separator between rooms
                        f.write("\n" + "=" * 80 + "\n\n")
                    except Exception as e:
                        f.write(f"Error processing room #{room_id}: {str(e)}\n")
                        f.write("=" * 80 + "\n\n")
                        self.stdout.write(self.style.WARNING(f"Error processing room #{room_id}: {str(e)}"))
                        continue

        self.stdout.write(
            self.style.SUCCESS(f"Room log has been created: {filename}")
        ) 