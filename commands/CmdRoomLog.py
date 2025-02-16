"""
Command to log all room information to a file.
"""
from evennia import Command
from evennia.utils.search import search_object
from evennia.utils.utils import make_iter
import os
import datetime

class CmdRoomLog(Command):
    """
    Creates a log file containing information about all rooms in the game.

    Usage:
        +roomlog

    This command will create a log file in the game's directory containing
    information about all rooms, including their names, descriptions,
    and exits.
    """

    key = "+roomlog"
    locks = "cmd:perm(Admin)"
    help_category = "Admin"

    def func(self):
        """Execute command."""
        # Search for both Room and RoomParent objects
        rooms_parent = list(search_object("", typeclass="typeclasses.rooms.RoomParent"))
        rooms = list(search_object("", typeclass="typeclasses.rooms.Room"))
        
        # Combine the results
        all_rooms = rooms_parent + rooms
        
        if not all_rooms:
            self.caller.msg("No rooms found.")
            return

        # Get the game directory path
        game_dir = self.caller.sessions.current_session.server.game_directory
        
        # Create filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"room_log_{timestamp}.txt"
        filepath = os.path.join(game_dir, filename)

        # Open file for writing
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("ROOM LOG\n")
            f.write("=" * 80 + "\n\n")
            
            # Process each room
            for room in all_rooms:
                # Write room name/key and typeclass
                f.write(f"Name/key: {room.get_display_name(self.caller)} ({room.dbref})\n")
                f.write(f"Typeclass: {room.typename}\n")
                
                # Write description
                f.write("Description:\n")
                if room.db.desc:
                    f.write(room.db.desc + "\n")
                else:
                    f.write("No description set.\n")
                
                # Write exits
                f.write("Exits:\n")
                exits = [exit for exit in room.contents if exit.destination]
                if exits:
                    for exit in exits:
                        f.write(f"  {exit.name} ({exit.dbref}) -> {exit.destination.name} ({exit.destination.dbref})\n")
                else:
                    f.write("  No exits.\n")
                
                # Add separator between rooms
                f.write("\n" + "=" * 80 + "\n\n")

        self.caller.msg(f"Room log has been created: {filename}")