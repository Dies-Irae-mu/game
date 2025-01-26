from evennia import Command, create_object
from evennia.utils import search
from random import randint
from evennia.utils.utils import class_from_module
import random
from evennia.objects.models import ObjectDB
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils import evtable
from django.db.models import Q

class CmdRent(MuxCommand):
    """
    Rent a residence in this area.
    
    Usage:
        +rent               - List available residence types
        +rent/type         - Show detailed information about available types
        +rent <type>       - Rent specific residence type
        
    Example:
        +rent
        +rent/type         - Shows detailed info about available types
        +rent Studio
        +rent "Two-Bedroom"
        +rent House
    """
    
    key = "+rent"
    locks = "cmd:all()"
    help_category = "Housing"
    
    # Define residence types (moved to class level for easy reference)
    APARTMENT_TYPES = {
        "Studio": {
            "desc": "A cozy studio apartment with an open floor plan.",
            "rooms": 1,
            "resource_modifier": 0
        },
        "One-Bedroom": {
            "desc": "A comfortable one-bedroom apartment with a separate living area.",
            "rooms": 2,
            "resource_modifier": 1
        },
        "Two-Bedroom": {
            "desc": "A spacious two-bedroom apartment with a full living room.",
            "rooms": 3,
            "resource_modifier": 2
        },
        "Luxury Studio": {
            "desc": "An upscale studio apartment with premium finishes and city views.",
            "rooms": 1,
            "resource_modifier": 2
        },
        "Luxury One-Bedroom": {
            "desc": "A high-end one-bedroom apartment with designer fixtures and an open concept layout.",
            "rooms": 2,
            "resource_modifier": 3
        },
        "Luxury Two-Bedroom": {
            "desc": "An elegant two-bedroom apartment with premium amenities and panoramic views.",
            "rooms": 3,
            "resource_modifier": 4
        },
        "Penthouse": {
            "desc": "A luxurious penthouse suite with wraparound views and exclusive amenities.",
            "rooms": 4,
            "resource_modifier": 5
        },
        "Motel Room": {
            "desc": "A rundown motel room with a bed and a small desk.",
            "rooms": 1,
            "resource_modifier": -1
        },
        "Hotel Room": {
            "desc": "A well-appointed hotel room with daily housekeeping service.",
            "rooms": 1,
            "resource_modifier": 0
        },
        "Hotel Suite": {
            "desc": "A well-appointed hotel suite with daily housekeeping service.",
            "rooms": 1,
            "resource_modifier": 2
        },
        "Executive Suite": {
            "desc": "A premium hotel suite with separate living and sleeping areas.",
            "rooms": 2,
            "resource_modifier": 3
        }
    }
    
    RESIDENTIAL_TYPES = {
        "House": {
            "desc": "A modest single-family home with a small yard.",
            "rooms": 4,
            "resource_modifier": 2
        },
        "Townhouse": {
            "desc": "A multi-level townhouse with modern amenities.",
            "rooms": 3,
            "resource_modifier": 1
        },
        "Cottage": {
            "desc": "A charming cottage with a private garden.",
            "rooms": 2,
            "resource_modifier": 0
        },
        "Manor": {
            "desc": "A stately manor house with extensive grounds and luxury amenities.",
            "rooms": 6,
            "resource_modifier": 4
        },
        "Villa": {
            "desc": "An elegant villa with a private pool and landscaped gardens.",
            "rooms": 5,
            "resource_modifier": 3
        },
        "Estate": {
            "desc": "A grand estate with multiple buildings and extensive security.",
            "rooms": 8,
            "resource_modifier": 5
        }
    }

    def show_type_details(self, location):
        """Show detailed information about available residence types."""
        if not location.is_housing_area():
            self.caller.msg("This is not a residential area.")
            return
            
        available_types = location.get_available_housing_types()
        if not available_types:
            self.caller.msg("No housing types available in this area.")
            return
            
        from evennia.utils.evtable import EvTable
        table = EvTable(
            "|wType|n",
            "|wRooms|n",
            "|wCost|n",
            "|wDescription|n",
            border="table",
            table_width=78
        )
        
        # Configure column widths
        table.reformat_column(0, width=20)  # Type (increased width for longer names)
        table.reformat_column(1, width=7)   # Rooms
        table.reformat_column(2, width=6)   # Cost
        table.reformat_column(3, width=43)  # Description
        
        for rtype, data in available_types.items():
            cost = location.get_housing_cost(rtype)
            table.add_row(
                rtype,
                str(data['rooms']),
                str(cost),
                data['desc']
            )
            
        header = f"\n|wAvailable Housing Types in {location.get_display_name(self.caller)}:|n\n"
        self.caller.msg(header + str(table))

    def get_type_case_insensitive(self, type_str):
        """Helper method to find housing type case-insensitively"""
        type_str = type_str.strip()
        
        # Check apartment types
        for apt_type in self.APARTMENT_TYPES:
            if apt_type.lower() == type_str.lower():
                return apt_type
                
        # Check residential types
        for res_type in self.RESIDENTIAL_TYPES:
            if res_type.lower() == type_str.lower():
                return res_type
                
        return None

    def check_existing_residence(self):
        """
        Check if player already has a residence.
        
        Returns:
            tuple: (bool, str) - (has_residence, residence_info)
        """
        for room in ObjectDB.objects.filter(db_typeclass_path__contains="rooms.Room"):
            if room.is_housing_area():
                tenants = room.db.housing_data.get('current_tenants', {})
                for res_id, tenant_id in tenants.items():
                    if tenant_id == self.caller.id:
                        try:
                            residence = ObjectDB.objects.get(id=res_id)
                            area_name = room.get_display_name(self.caller)
                            res_name = residence.get_display_name(self.caller)
                            return True, f"You already have a residence: {res_name} in {area_name}"
                        except ObjectDB.DoesNotExist:
                            continue
        return False, ""

    def func(self):
        location = self.caller.location
        
        # Handle staff commands for managing available types
        if "addtype" in self.switches and self.caller.check_permstring("builders"):
            if not self.args:
                self.caller.msg("Usage: +rent/addtype <type>")
                return
                
            apt_type = self.get_type_case_insensitive(self.args)
            if not apt_type:
                all_types = list(self.APARTMENT_TYPES.keys()) + list(self.RESIDENTIAL_TYPES.keys())
                self.caller.msg(f"Invalid type. Available types: {', '.join(all_types)}")
                return
                
            housing_data = location.ensure_housing_data()
            if 'available_types' not in housing_data:
                housing_data['available_types'] = []
                
            if apt_type in housing_data['available_types']:
                self.caller.msg(f"{apt_type} is already available in this building.")
                return
                
            housing_data['available_types'].append(apt_type)
            self.caller.msg(f"Added {apt_type} to available types in {location.get_display_name(self.caller)}.")
            return
            
        elif "remtype" in self.switches and self.caller.check_permstring("builders"):
            if not self.args:
                self.caller.msg("Usage: +rent/remtype <type>")
                return
                
            apt_type = self.get_type_case_insensitive(self.args)
            housing_data = location.ensure_housing_data()
            
            if apt_type in housing_data.get('available_types', []):
                housing_data['available_types'].remove(apt_type)
                self.caller.msg(f"Removed {apt_type} from available types in {location.get_display_name(self.caller)}.")
            else:
                self.caller.msg(f"{apt_type} is not available in this building.")
            return
            
        elif "cleartype" in self.switches and self.caller.check_permstring("builders"):
            housing_data = location.ensure_housing_data()
            housing_data['available_types'] = []
            self.caller.msg(f"Cleared all available types from {location.get_display_name(self.caller)}.")
            return
            
        # Handle /type switch
        if "type" in self.switches:
            self.show_type_details(location)
            return
            
        if not location.is_housing_area():
            self.caller.msg("This is not a residential area.")
            return
            
        # Show available units if no type specified
        if not self.args:
            self.caller.msg(location.list_available_units())
            return
            
        # Check if player already has a residence
        has_residence, message = self.check_existing_residence()
        if has_residence:
            self.caller.msg(message)
            self.caller.msg("You must +vacate your current residence before renting a new one.")
            return
            
        # Get case-insensitive match for apartment type
        apt_type = self.get_type_case_insensitive(self.args)
        if not apt_type:
            available_types = location.get_available_housing_types()
            self.caller.msg(f"Invalid residence type. Available types: {', '.join(available_types.keys())}")
            return
            
        required_resources = location.get_housing_cost(apt_type)
        if not required_resources:
            available_types = location.get_available_housing_types()
            self.caller.msg(f"Invalid residence type. Available types: {', '.join(available_types.keys())}")
            return

        # Generate appropriate number based on building type
        is_apartment = location.is_apartment_building()
        residence_num = self.generate_residence_number(location, is_apartment)
        if not residence_num:
            self.caller.msg("Error generating residence number. Please contact staff.")
            return
            
        # Create the residence
        room_typeclass = class_from_module("typeclasses.rooms.Room")
        available_types = location.get_available_housing_types()
        
        if is_apartment:
            residence_name = f"Apartment {residence_num}"
            room_type = "apartment"
        else:
            residence_name = str(residence_num)  # Already includes street name
            if apt_type == "Townhouse":
                room_type = "townhouse"
            elif apt_type == "Cottage":
                room_type = "cottage"
            else:
                room_type = "house"
            
        # Create main residence
        residence = create_object(room_typeclass,
                               key=residence_name,
                               location=None)
        residence.db.desc = available_types[apt_type]['desc']
        # Set specific room type based on apartment/house type
        if is_apartment:
            residence.db.roomtype = f"{apt_type} Apartment"
        else:
            residence.db.roomtype = apt_type
        residence.db.owner = self.caller
        # Inherit resources from lobby
        residence.db.resources = location.db.resources
        residence.db.home_data = {
            'locked': False,
            'keyholders': set(),
            'owner': self.caller
        }
        
        # Create additional rooms
        num_rooms = available_types[apt_type]['rooms']
        child_rooms = []
        
        if num_rooms > 1:
            for i in range(2, num_rooms + 1):
                room_name = f"{residence_name} - Room {i}"
                child_room = create_object(room_typeclass,
                                       key=room_name,
                                       location=None)
                child_room.db.desc = f"Room {i} of {residence_name}."
                # Set proper room type for child rooms
                child_room.db.roomtype = f"{room_type}_room"
                child_room.db.parent_room = residence
                # Inherit resources from main residence
                child_room.db.resources = residence.db.resources
                child_rooms.append(child_room)
        
        residence.db.child_rooms = child_rooms
        
        # Create exits using ApartmentExit
        self.create_exits(location, residence, residence_name, child_rooms, is_apartment, residence_num)
        
        # Update housing data
        location.db.housing_data['current_tenants'][residence.id] = self.caller.id
        location.db.housing_data['apartment_numbers'].add(residence_num)
        
        # Set as home if needed
        if not self.caller.home:
            self.caller.home = residence
            self.caller.msg(f"This {apt_type} has been set as your home.")
        
        # Final message
        self.caller.msg(f"You have rented {residence_name}. Required Resources: {required_resources}")
        self.caller.move_to(residence)

    def create_exits(self, location, residence, residence_name, child_rooms, is_apartment, residence_num):
        """Helper method to create all necessary exits"""
        exit_typeclass = "typeclasses.exits.ApartmentExit"
        
        # Create entrance
        entrance = create_object(exit_typeclass,
                              key=residence_name,
                              location=location,
                              destination=residence)
        if is_apartment:
            # Add number as alias for apartments
            entrance.aliases.add(str(residence_num))
        else:
            # For houses, add the house number
            entrance.aliases.add(str(residence_num).split()[0])  # Just the number part
        
        # Create exit back to building/street
        back_exit = create_object(exit_typeclass,
                               key="Out",
                               location=residence,
                               destination=location)
        # Always add 'o' and 'out' as aliases for the exit
        back_exit.aliases.add("o")
        back_exit.aliases.add("out")
        back_exit.aliases.add("exit")
        
        # Create exits between rooms
        for i, room in enumerate(child_rooms, 2):
            # Create exit to child room
            to_room = create_object(exit_typeclass,
                                 key=f"Room {i}",
                                 location=residence,
                                 destination=room)
            to_room.aliases.add(str(i))
            
            # Create exit back to main room
            to_main = create_object(exit_typeclass,
                                 key="Out",
                                 location=room,
                                 destination=residence)
            # Add same aliases as main exit
            to_main.aliases.add("o")
            to_main.aliases.add("out")
            to_main.aliases.add("exit")

    def generate_residence_number(self, location, is_apartment):
        """
        Generate a unique residence number.
        
        Args:
            location (Room): The housing area
            is_apartment (bool): Whether this is an apartment building
            
        Returns:
            int or str: A unique residence number/address
        """
        try:
            # Get existing apartment numbers
            used_numbers = location.db.housing_data.get('apartment_numbers', set())
            
            if is_apartment:
                # For apartments, generate a number between 101 and 999
                attempts = 0
                while attempts < 100:  # Prevent infinite loop
                    # Generate floor number (1-9) and unit number (01-99)
                    floor = random.randint(1, 9)
                    unit = random.randint(1, 99)
                    number = (floor * 100) + unit
                    
                    if number not in used_numbers:
                        return number
                    attempts += 1
            else:
                # For houses, generate a street address
                street_name = location.get_display_name(self.caller).split('-')[0].strip()
                attempts = 0
                while attempts < 100:
                    number = random.randint(1, 9999)
                    address = f"{number} {street_name}"
                    
                    if address not in used_numbers:
                        return address
                    attempts += 1
                    
            # If we couldn't generate a unique number
            return None
            
        except Exception as e:
            self.caller.msg(f"Error generating residence number: {str(e)}")
            return None

class CmdVacate(MuxCommand):
    """
    Vacate your residence or force vacate another's residence (staff only).
    
    Usage:
        +vacate              - Vacate your residence in current building
        +vacate/all         - List all your residences
        +vacate <number>    - Vacate specific residence (if you own it)
        +vacate/force <number> - Force vacate a residence (staff only)
    """
    
    key = "+vacate"
    locks = "cmd:all()"
    help_category = "Housing"
    
    def find_residence(self, residence_number=None):
        """Helper method to find building containing player's residence."""
        # Search all rooms for housing data
        for room in ObjectDB.objects.filter(db_typeclass_path__contains="rooms.Room"):
            if room.is_housing_area():
                tenants = room.db.housing_data.get('current_tenants', {})
                for res_id, tenant_id in tenants.items():
                    if tenant_id == self.caller.id:
                        try:
                            residence = ObjectDB.objects.get(id=res_id)
                            if residence_number is None or residence.key.endswith(str(residence_number)):
                                return room, residence
                        except ObjectDB.DoesNotExist:
                            continue
        return None, None

    def func(self):
        if "all" in self.switches:
            # List all residences owned by player
            residences = []
            for room in ObjectDB.objects.filter(db_typeclass_path__contains="rooms.Room"):
                if room.is_housing_area():
                    tenants = room.db.housing_data.get('current_tenants', {})
                    for res_id, tenant_id in tenants.items():
                        if tenant_id == self.caller.id:
                            try:
                                residence = ObjectDB.objects.get(id=res_id)
                                residences.append((room, residence))
                            except ObjectDB.DoesNotExist:
                                continue
            
            if not residences:
                self.caller.msg("You don't own any residences.")
                return
                
            table = evtable.EvTable("|wResidence|n", "|wLocation|n", "|wType|n", border="table")
            for area, residence in residences:
                table.add_row(
                    residence.get_display_name(self.caller),
                    area.get_display_name(self.caller),
                    residence.db.roomtype.title()
                )
            self.caller.msg(table)
            return

        if "force" in self.switches:
            if not self.caller.check_permstring("builders"):
                self.caller.msg("You don't have permission to force vacate residences.")
                return
                
            if not self.args:
                self.caller.msg("Please specify a residence number to force vacate.")
                return
                
            building, residence = self.find_residence(self.args)
            if not residence:
                self.caller.msg("Residence not found.")
                return
        else:
            # Normal vacate
            if self.args:
                building, residence = self.find_residence(self.args)
                if not residence:
                    self.caller.msg("You don't own that residence.")
                    return
            else:
                # Try to vacate current location
                location = self.caller.location
                if not (location.db.roomtype in ["apartment", "house"] and location.db.owner == self.caller):
                    self.caller.msg("You must be in your residence to vacate it.")
                    return
                    
                # Find the building
                for exit in location.exits:
                    if exit.key == "Out":
                        building = exit.destination
                        residence = location
                        break
                else:
                    self.caller.msg("Error finding building. Please contact staff.")
                    return

        # Perform the vacate
        if residence.db.owner != self.caller and not self.caller.check_permstring("builders"):
            self.caller.msg("You don't own this residence.")
            return
            
        # Move any occupants to the building
        for obj in residence.contents:
            if obj.has_account:
                obj.msg("This residence is being vacated. You are being moved out.")
                obj.move_to(building)
                
        # Clean up child rooms if they exist
        if hasattr(residence.db, 'child_rooms'):
            for room in residence.db.child_rooms:
                if room:
                    for obj in room.contents:
                        if obj.has_account:
                            obj.move_to(building)
                    room.delete()

        # Update building data
        del building.db.housing_data['current_tenants'][residence.id]
        building.db.housing_data['apartment_numbers'].remove(int(residence.key.split()[-1]))
        
        # Clear home location if this was their home
        if self.caller.home == residence:
            self.caller.home = None
            self.caller.msg("Your home location has been cleared.")
            
        # Delete the residence
        residence.delete()
        self.caller.msg("You have vacated the residence.")

class CmdSetApartmentDesc(MuxCommand):
    """
    Set the description of your residence or its rooms.
    
    Usage:
        +adesc              - Show current room description
        +adesc <text>       - Set description for current room
        +adesc/room <num> = <text>  - Set description for specific room
        
    Example:
        +adesc This cozy studio has been decorated with vintage posters.
        +adesc/room 2 = This bedroom features a comfortable queen-sized bed.
    """
    
    key = "+adesc"
    aliases = ["+rdesc"]  # Added alias for residences
    locks = "cmd:all()"
    help_category = "Housing"
    
    def func(self):
        location = self.caller.location
        
        # Check if we're in a residence
        if location.db.roomtype not in ["apartment", "house", "apartment_room"]:
            self.caller.msg("This command can only be used inside residences.")
            return
            
        # Check ownership
        if location.db.owner != self.caller:
            if hasattr(location, 'db') and hasattr(location.db, 'parent_room'):
                if location.db.parent_room.db.owner != self.caller:
                    self.caller.msg("You don't own this residence.")
                    return
            else:
                self.caller.msg("You don't own this residence.")
                return

        if "room" in self.switches:
            if not self.rhs:
                self.caller.msg("Usage: +adesc/room <num> = <description>")
                return
                
            try:
                room_num = int(self.lhs)
            except ValueError:
                self.caller.msg("Please specify a valid room number.")
                return
                
            # Find the room
            if location.db.parent_room:
                main_room = location.db.parent_room
            else:
                main_room = location
                
            target_room = None
            if room_num == 1:
                target_room = main_room
            else:
                for room in main_room.db.child_rooms:
                    if room and room.key.endswith(f"Room {room_num}"):
                        target_room = room
                        break
                        
            if not target_room:
                self.caller.msg(f"Room {room_num} not found in your residence.")
                return
                
            target_room.db.desc = self.rhs
            self.caller.msg(f"Description set for Room {room_num}.")
            return

        # No switches - handle main room description
        if not self.args:
            self.caller.msg(location.db.desc)
            return
            
        # Set description for current room
        location.db.desc = self.args
        self.caller.msg("Description set.")

class CmdSetApartmentExit(MuxCommand):
    """
    Modify exits in your residence.
    
    Usage:
        +aexit <exit> = <new name>           - Rename an exit
        +aexit/alias <exit> = <alias>        - Add an alias to an exit
        +aexit/clear <exit>                  - Clear all aliases from an exit
        +aexit/remove <exit> = <alias>       - Remove specific alias from an exit
        
    Example:
        +aexit Room 2 = Bedroom
        +aexit/alias Bedroom = bed
        +aexit/clear Bedroom
        +aexit/remove Bedroom = bed
    """
    
    key = "+aexit"
    aliases = ["+rexit"]  # Added alias for residences
    locks = "cmd:all()"
    help_category = "Housing"
    
    def func(self):
        location = self.caller.location
        
        # Check if we're in a residence
        if location.db.roomtype not in ["apartment", "house", "apartment_room"]:
            self.caller.msg("This command can only be used inside residences.")
            return
            
        # Check ownership
        if location.db.owner != self.caller:
            if hasattr(location, 'db') and hasattr(location.db, 'parent_room'):
                if location.db.parent_room.db.owner != self.caller:
                    self.caller.msg("You don't own this residence.")
                    return
            else:
                self.caller.msg("You don't own this residence.")
                return

        if not self.args:
            # List current exits and their aliases
            exits = [ex for ex in self.caller.location.contents 
                    if ex.destination and ex.key != "Out"]  # Don't show Out exit
            if not exits:
                self.caller.msg("No customizable exits found.")
                return
                
            table = evtable.EvTable("|wExit Name|n", "|wAliases|n", border="table")
            for ex in exits:
                aliases = ", ".join(ex.aliases.all()) if ex.aliases.all() else "None"
                table.add_row(ex.name, aliases)
            self.caller.msg(table)
            return

        # Don't allow modifying the "Out" exit
        if self.lhs.lower() == "out" or (self.rhs and self.rhs.lower() == "out"):
            self.caller.msg("The 'Out' exit cannot be modified.")
            return

        if "alias" in self.switches:
            if not self.rhs or not self.lhs:
                self.caller.msg("Usage: +aexit/alias <exit> = <alias>")
                return
                
            exit = self.caller.search(self.lhs, location=self.caller.location, 
                                    typeclass="typeclasses.exits.ApartmentExit")
            if not exit:
                return
                
            exit.aliases.add(self.rhs)
            self.caller.msg(f"Added alias '{self.rhs}' to exit '{exit.name}'.")
            
        elif "clear" in self.switches:
            exit = self.caller.search(self.args, location=self.caller.location, 
                                    typeclass="typeclasses.exits.ApartmentExit")
            if not exit:
                return
                
            exit.aliases.clear()
            self.caller.msg(f"Cleared all aliases from exit '{exit.name}'.")
            
        elif "remove" in self.switches:
            if not self.rhs or not self.lhs:
                self.caller.msg("Usage: +aexit/remove <exit> = <alias>")
                return
                
            exit = self.caller.search(self.lhs, location=self.caller.location, 
                                    typeclass="typeclasses.exits.ApartmentExit")
            if not exit:
                return
                
            if self.rhs in exit.aliases.all():
                exit.aliases.remove(self.rhs)
                self.caller.msg(f"Removed alias '{self.rhs}' from exit '{exit.name}'.")
            else:
                self.caller.msg(f"Exit '{exit.name}' doesn't have alias '{self.rhs}'.")
            
        else:
            # Rename exit
            if not self.rhs or not self.lhs:
                self.caller.msg("Usage: +aexit <exit> = <new name>")
                return
                
            exit = self.caller.search(self.lhs, location=self.caller.location, 
                                    typeclass="typeclasses.exits.ApartmentExit")
            if not exit:
                return
                
            old_name = exit.name
            exit.name = self.rhs
            self.caller.msg(f"Renamed exit '{old_name}' to '{self.rhs}'.")

class CmdManageHome(MuxCommand):
    """
    Manage your auto-build home, including locks and keys.
    
    Usage:
        +home                 - Go to your home
        +home/set            - Set current apartment as your home
        +home/lock           - Lock your apartment
        +home/unlock         - Unlock your apartment
        +home/key <player>   - Give a key to another player
        +home/unkey <player> - Remove a key from a player
        +home/keys           - List who has keys to your apartment
        +home/status         - Show lock status of your apartment
        +home/find          - Show location of your apartment
    """
    
    key = "+home"
    aliases = ["home"]
    locks = "cmd:all()"
    help_category = "Housing"
    
    def init_home_data(self, location):
        """Initialize home data if it doesn't exist"""
        if not location.db.home_data:
            location.db.home_data = {
                'locked': False,
                'keyholders': set(),
                'owner': None
            }
        return location.db.home_data

    def find_player_apartment(self, player):
        """Find a player's apartment globally"""
        from evennia.objects.models import ObjectDB
        for room in ObjectDB.objects.filter(db_typeclass_path__contains="rooms.Room"):
            if (hasattr(room.db, 'roomtype') and 
                room.db.roomtype == "apartment" and 
                room.db.owner == player):
                return room
        return None

    def update_entrance_lock(self, apartment, home_data):
        """Helper method to update the entrance lock based on current keyholders"""
        # Find the entrance to this apartment from the parent room
        parent_room = None
        for exit in apartment.exits:
            if exit.key == "Out":
                parent_room = exit.destination
                break
                
        if parent_room:
            # Find the entrance in the parent room
            for exit in parent_room.contents:
                if (hasattr(exit, 'destination') and 
                    exit.destination == apartment):
                    # Make sure it's using the ApartmentExit typeclass
                    if not exit.is_typeclass("typeclasses.exits.ApartmentExit"):
                        exit.swap_typeclass("typeclasses.exits.ApartmentExit",
                                          clean_attributes=False)
                    # Clear any old lock strings
                    exit.locks.add("traverse:all()")
                    return True
        return False

    def func(self):
        # If no switches and no args, treat as "go home" command
        if not self.switches and not self.args:
            # Check if player has a home set
            if not self.caller.home:
                self.caller.msg("You haven't set a home yet.")
                return
                
            # Check if home still exists and is an apartment
            if not hasattr(self.caller.home.db, 'roomtype') or self.caller.home.db.roomtype != "apartment":
                self.caller.msg("Your home location seems to be invalid. Please set a new home.")
                return
                
            # Check if the home is locked and we don't have access
            if (self.caller.home.db.home_data.get('locked', False) and 
                self.caller.home.db.owner != self.caller and 
                self.caller.id not in self.caller.home.db.home_data.get('keyholders', set()) and
                not self.caller.check_permstring("builders")):
                self.caller.msg("Your home is currently locked and you don't have a key.")
                return
                
            # Try to go home
            self.caller.move_to(self.caller.home)
            return

        # Handle find switch
        if "find" in self.switches:
            apartment = self.find_player_apartment(self.caller)
            if not apartment:
                self.caller.msg("You don't own an apartment.")
                return
                
            # Find the parent room (floor)
            parent_room = None
            for exit in apartment.exits:
                if exit.key == "Out":
                    parent_room = exit.destination
                    break
                    
            if parent_room:
                self.caller.msg(f"Your apartment ({apartment.get_display_name(self.caller)}) "
                              f"is located on {parent_room.get_display_name(self.caller)}.")
            return

        # Handle key and unkey commands (can be used from anywhere)
        if "key" in self.switches or "unkey" in self.switches:
            apartment = self.find_player_apartment(self.caller)
            if not apartment:
                self.caller.msg("You don't own an apartment.")
                return

                
            if not self.args:
                self.caller.msg(f"Usage: +home/{self.switches[0]} <player>")
                return
                
            # Search for player account instead of character
            from evennia.accounts.models import AccountDB
            target_account = AccountDB.objects.filter(username__iexact=self.args).first()
            if not target_account:
                self.caller.msg(f"Player '{self.args}' not found.")
                return
                
            # Get their active character or most recent puppet
            target = target_account.puppet or target_account.db._last_puppet
            if not target:
                self.caller.msg(f"Could not find a character for {self.args}.")
                return
                
            home_data = self.init_home_data(apartment)
            
            if "key" in self.switches:
                if target.id in home_data['keyholders']:
                    self.caller.msg(f"{target.name} already has a key to your apartment.")
                    return
                    
                home_data['keyholders'].add(target.id)
                # Update the entrance lock
                self.update_entrance_lock(apartment, home_data)
                self.caller.msg(f"You have given {target.name} a key to your apartment.")
                if target.has_account:
                    target.msg(f"{self.caller.name} has given you a key to their apartment.")
                    
            else:  # unkey
                if target.id not in home_data['keyholders']:
                    self.caller.msg(f"{target.name} doesn't have a key to your apartment.")
                    return
                    
                home_data['keyholders'].remove(target.id)
                # Update the entrance lock
                self.update_entrance_lock(apartment, home_data)
                self.caller.msg(f"You have taken back {target.name}'s key to your apartment.")
                if target.has_account:
                    target.msg(f"{self.caller.name} has taken back your key to their apartment.")
            return
        
        # For other commands, we need to be in the apartment
        location = self.caller.location
        if not location.db.roomtype == "apartment":
            if "status" not in self.switches:
                self.caller.msg("This command can only be used inside apartments.")
                return

        # Initialize home data
        home_data = self.init_home_data(location)
            
        if "set" in self.switches:
            # Check ownership
            if location.db.owner != self.caller:
                self.caller.msg("You don't own this apartment.")
                return
                
            # Set as home
            self.caller.home = location
            home_data['owner'] = self.caller
            self.caller.msg("You have set this apartment as your home.")
            
        elif "lock" in self.switches:
            if location.db.owner != self.caller:
                self.caller.msg("You don't own this apartment.")
                return
                
            home_data['locked'] = True
            if self.update_entrance_lock(location, home_data):
                self.caller.msg("You have locked your apartment.")
            else:
                self.caller.msg("Error updating apartment lock. Please contact staff.")
            
        elif "unlock" in self.switches:
            if location.db.owner != self.caller:
                self.caller.msg("You don't own this apartment.")
                return
                
            home_data['locked'] = False
            if self.update_entrance_lock(location, home_data):
                self.caller.msg("You have unlocked your apartment.")
            else:
                self.caller.msg("Error updating apartment lock. Please contact staff.")
            
        elif "keys" in self.switches:
            if location.db.owner != self.caller:
                self.caller.msg("You don't own this apartment.")
                return
                
            keyholders = []
            for pid in home_data['keyholders']:
                char = self.caller.search(f"#{pid}")
                if char:
                    keyholders.append(char.name)
                    
            if keyholders:
                self.caller.msg("People with keys to your apartment:")
                self.caller.msg("\n".join(f"- {name}" for name in keyholders))
            else:
                self.caller.msg("Nobody else has keys to your apartment.")
                
        elif "status" in self.switches:
            # Find player's apartment
            home = self.caller.home
            if not home or not hasattr(home.db, 'roomtype') or home.db.roomtype != "apartment":
                self.caller.msg("You haven't set an apartment as your home.")
                return
                
            status = "locked" if home.db.home_data['locked'] else "unlocked"
            self.caller.msg(f"Your apartment ({home.get_display_name(self.caller)}) is currently {status}.")
            
            # Show keyholders if it's the caller's apartment
            if home.db.owner == self.caller:
                keyholders = []
                for pid in home.db.home_data['keyholders']:
                    char = self.caller.search(f"#{pid}")
                    if char:
                        keyholders.append(char.name)
                        
                if keyholders:
                    self.caller.msg("People with keys:")
                    self.caller.msg("\n".join(f"- {name}" for name in keyholders)) 

class CmdUpdateApartments(MuxCommand):
    """
    Update apartment exits to use the new system.
    
    Usage:
        +updateapts            - Update all apartment exits
        +updateapts <room>    - Update exits for specific apartment
        
    This command converts existing apartment exits to use the ApartmentExit
    typeclass and updates their permissions.
    """
    
    key = "+updateapts"
    locks = "cmd:perm(builders)"
    help_category = "Building and Housing"
    
    def func(self):
        from evennia.objects.models import ObjectDB
        from typeclasses.exits import ApartmentExit
        
        if self.args:
            # Update specific apartment
            target = self.caller.search(self.args)
            if not target:
                return
            apartments = [target]
        else:
            # Find all apartments
            apartments = ObjectDB.objects.filter(
                db_typeclass_path__contains="rooms.Room"
            ).filter(
                db_attributes__db_key="roomtype",
                db_attributes__db_value="apartment"
            )
        
        count = 0
        for apartment in apartments:
            try:
                # Initialize home_data if needed
                if not apartment.db.home_data:
                    apartment.db.home_data = {
                        'locked': False,
                        'keyholders': set(),
                        'owner': apartment.db.owner
                    }
                
                # Find and update the entrance
                parent_room = None
                for exit in apartment.exits:
                    if exit.key == "Out":
                        parent_room = exit.destination
                        break
                        
                if parent_room:
                    for exit in parent_room.contents:
                        if (hasattr(exit, 'destination') and 
                            exit.destination == apartment):
                            # Update entrance exit
                            exit.swap_typeclass("typeclasses.exits.ApartmentExit",
                                              clean_attributes=False)
                            # Clear old locks
                            exit.locks.add("traverse:all()")
                            count += 1
                
                # Update the "Out" exit
                for exit in apartment.exits:
                    if exit.key == "Out":
                        exit.swap_typeclass("typeclasses.exits.ApartmentExit",
                                          clean_attributes=False)
                        count += 1
                        
                # Update child room exits if they exist
                child_rooms = apartment.db.child_rooms
                if child_rooms:  # Only process if child_rooms exists and is not None
                    for child in child_rooms:
                        if child:  # Make sure child room exists
                            for exit in child.exits:
                                exit.swap_typeclass("typeclasses.exits.ApartmentExit",
                                                  clean_attributes=False)
                                count += 1
                
            except Exception as e:
                # Log any errors but continue processing other apartments
                self.caller.msg(f"Error processing {apartment.get_display_name(self.caller)}: {str(e)}")
                continue
        
        self.caller.msg(f"Updated {count} exits across {len(apartments)} apartments.") 

class CmdListApartments(MuxCommand):
    """
    List apartments owned by a player or all apartments.
    
    Usage:
        +apartments                  - List all apartments
        +apartments <player>         - List apartments owned by player
        +apartments/search <text>    - Search apartments by name/number
        +apartments/floor <floor>    - List apartments on a specific floor
        
    Shows apartment details including:
    - Location/floor
    - Owner
    - Lock status
    - Number of keyholders
    - Whether it's set as the owner's home
    """
    
    key = "+apartments"
    aliases = ["@apartments"]
    locks = "cmd:perm(builders)"
    help_category = "Building and Housing"
    
    def func(self):
        from evennia.objects.models import ObjectDB
        from evennia.accounts.models import AccountDB
        
        def format_apartment(apt):
            """Helper to format apartment info"""
            owner = apt.db.owner.name if apt.db.owner else "None"
            home_data = apt.db.home_data or {}
            locked = "Locked" if home_data.get('locked', False) else "Unlocked"
            keyholders = len(home_data.get('keyholders', set()))
            is_home = "Yes" if (apt.db.owner and apt.db.owner.home == apt) else "No"
            
            # Find parent room (floor)
            floor = "Unknown"
            for exit in apt.exits:
                if exit.key == "Out":
                    floor = exit.destination.get_display_name(self.caller)
                    break
                    
            return (
                f"|w{apt.get_display_name(self.caller)}|n on {floor}\n"
                f"Owner: {owner}, Status: {locked}, Keyholders: {keyholders}, Home: {is_home}"
            )
        
        if "search" in self.switches:
            if not self.args:
                self.caller.msg("Please provide a search term.")
                return
                
            # Search apartments by name/number
            apartments = ObjectDB.objects.filter(
                db_typeclass_path__contains="rooms.Room",
                db_key__icontains=self.args,
                db_attributes__db_key="roomtype",
                db_attributes__db_value="apartment"
            )
            
        elif "floor" in self.switches:
            if not self.args:
                self.caller.msg("Please specify a floor.")
                return
                
            # First find the floor room
            floor = self.caller.search(self.args)
            if not floor:
                return
                
            # Then find apartments that have exits leading to this floor
            apartments = []
            for exit in floor.contents:
                if (hasattr(exit, 'destination') and 
                    hasattr(exit.destination.db, 'roomtype') and
                    exit.destination.db.roomtype == "apartment"):
                    apartments.append(exit.destination)
            
        else:
            if self.args:
                # Find player's apartments
                target = self.caller.search(self.args)
                if not target:
                    return
                    
                # Use Q objects to combine attribute filters
                apartments = ObjectDB.objects.filter(
                    db_typeclass_path__contains="rooms.Room"
                ).filter(
                    Q(db_attributes__db_key="roomtype", db_attributes__db_value="apartment") &
                    Q(db_attributes__db_key="owner", db_attributes__db_value=target)
                ).distinct()
            else:
                # List all apartments
                apartments = ObjectDB.objects.filter(
                    db_typeclass_path__contains="rooms.Room",
                    db_attributes__db_key="roomtype",
                    db_attributes__db_value="apartment"
                ).distinct()
        
        if not apartments:
            self.caller.msg("No apartments found.")
            return
            
        # Sort apartments by name
        apartments = sorted(apartments, key=lambda x: x.key)
        
        # Format output
        output = ["|wApartments:|n"]
        for apt in apartments:
            output.append(format_apartment(apt))
            
        self.caller.msg("\n".join(output)) 

class CmdUpdateExits(MuxCommand):
    """
    Update all exits to use the new Exit system.
    
    Usage:
        +updateexits            - Update all exits
        +updateexits <room>    - Update exits in specific room
        +updateexits/area <area> - Update all exits in an area
        
    This command ensures all exits use the new Exit class that
    properly handles channel conflicts and aliases.
    """
    
    key = "+updateexits"
    locks = "cmd:perm(builders)"
    help_category = "Building and Housing"
    
    def func(self):
        from evennia.objects.models import ObjectDB
        from typeclasses.exits import Exit, ApartmentExit
        
        def update_room_exits(room):
            """Helper to update exits in a single room"""
            count = 0
            for exit in room.contents:
                if not hasattr(exit, 'destination'):
                    continue
                    
                # Skip if already using correct typeclass
                if exit.is_typeclass("typeclasses.exits.ApartmentExit"):
                    continue
                elif exit.is_typeclass("typeclasses.exits.Exit"):
                    continue
                    
                # Determine correct typeclass
                if (hasattr(exit.destination, 'db') and 
                    hasattr(exit.destination.db, 'roomtype') and 
                    exit.destination.db.roomtype == "apartment"):
                    new_typeclass = "typeclasses.exits.ApartmentExit"
                else:
                    new_typeclass = "typeclasses.exits.Exit"
                
                try:
                    # Store current aliases
                    old_aliases = exit.aliases.all()
                    
                    # Update typeclass
                    exit.swap_typeclass(new_typeclass, clean_attributes=False)
                    
                    # Ensure aliases are preserved
                    exit.aliases.clear()
                    for alias in old_aliases:
                        exit.aliases.add(alias)
                    
                    count += 1
                except Exception as e:
                    self.caller.msg(f"Error updating {exit.get_display_name(self.caller)}: {str(e)}")
            
            return count
        
        if "area" in self.switches:
            if not self.args:
                self.caller.msg("Please specify an area name.")
                return
                
            # Find all rooms in the area
            area_rooms = ObjectDB.objects.filter(
                db_typeclass_path__contains="rooms.Room",
                db_key__icontains=self.args
            )
            
            if not area_rooms:
                self.caller.msg("No rooms found in that area.")
                return
                
            total_count = 0
            for room in area_rooms:
                count = update_room_exits(room)
                total_count += count
                
            self.caller.msg(f"Updated {total_count} exits across {len(area_rooms)} rooms in {self.args}.")
            
        elif self.args:
            # Update specific room
            room = self.caller.search(self.args)
            if not room:
                return
                
            count = update_room_exits(room)
            self.caller.msg(f"Updated {count} exits in {room.get_display_name(self.caller)}.")
            
        else:
            # Update all rooms
            rooms = ObjectDB.objects.filter(db_typeclass_path__contains="rooms.Room")
            total_count = 0
            
            for room in rooms:
                count = update_room_exits(room)
                total_count += count
                
            self.caller.msg(f"Updated {total_count} exits across {len(rooms)} rooms.") 

class CmdSetHousing(MuxCommand):
    """
    Set up a room as a housing area.
    
    Usage:
        +sethousing/apartment <resources> [max_units]  - Set as apartment building
        +sethousing/condo <resources> [max_units]      - Set as condominium
        +sethousing/residential <resources> [max_units] - Set as residential area
        +sethousing/clear                              - Clear housing settings
        
    The resources value determines the base cost for units in this building.
    Higher resources mean more expensive/luxurious accommodations.
        
    Example:
        +sethousing/apartment 2 20    - Set up as apartment building with resource 2, 20 units
        +sethousing/residential 3 10  - Set up as residential area with resource 3, 10 houses
    """
    
    key = "+sethousing"
    locks = "cmd:perm(builders)"
    help_category = "Building and Housing"
    
    def func(self):
        location = self.caller.location
        
        # Handle clear switch first
        if "clear" in self.switches:
            # Clear housing data
            if hasattr(location.db, 'housing_data'):
                location.db.housing_data = {
                    'is_housing': False,
                    'max_apartments': 0,
                    'current_tenants': {},
                    'apartment_numbers': set(),
                    'required_resources': 0,
                    'building_zone': None,
                    'connected_rooms': set(),
                    'is_lobby': False
                }
            
            # Reset room attributes
            location.db.roomtype = "Room"
            location.db.resources = 0
            
            # Re-initialize home data
            location.db.home_data = {
                'locked': False,
                'keyholders': set(),
                'owner': None
            }
            
            # Force room appearance update
            location.at_object_creation()
            
            self.caller.msg("Cleared housing settings for this room.")
            return
            
        # If not clearing, we need a valid switch
        if not self.switches or not any(switch in self.switches for switch in ["apartment", "condo", "residential"]):
            self.caller.msg("Please specify the type: /apartment, /condo, or /residential")
            return
            
        # Parse arguments
        if not self.args:
            self.caller.msg("Usage: +sethousing/<type> <resources> [max_units]")
            return
            
        try:
            args = self.args.split()
            resources = int(args[0])
            max_units = int(args[1]) if len(args) > 1 else 20  # Default to 20 if not specified
            
            if resources < 0:
                self.caller.msg("Resources cannot be negative.")
                return
                
            if max_units < 1:
                self.caller.msg("Maximum units must be at least 1.")
                return
                
        except ValueError:
            self.caller.msg("Usage: +sethousing/<type> <resources> [max_units]\nBoth values must be numbers.")
            return
        
        # Set up housing based on switch
        if "apartment" in self.switches:
            location.setup_housing("Apartment Building", max_units)
            location.db.resources = resources
            self.caller.msg(f"Set up room as apartment building with {resources} resources and {max_units} maximum units.")
            
        elif "condo" in self.switches:
            location.setup_housing("Condominiums", max_units)
            location.db.resources = resources
            self.caller.msg(f"Set up room as condominium with {resources} resources and {max_units} maximum units.")
            
        elif "residential" in self.switches:
            location.setup_housing("Residential Area", max_units)
            location.db.resources = resources
            self.caller.msg(f"Set up room as residential area with {resources} resources and {max_units} maximum units.") 

class CmdSetLock(MuxCommand):
    """
    Set various types of locks on an exit or room.
    
    Usage:
        +lock <target>=<locktype>:<value>
        +lock/list <target>          - List current locks
        +lock/clear <target>         - Clear all locks
        
    Lock Types:
        splat:<type>      - Restrict to specific splat (Vampire, Werewolf, etc)
        talent:<name>     - Require specific talent
        skill:<name>      - Require specific skill
        knowledge:<name>  - Require specific knowledge
        merit:<name>      - Require specific merit
        shifter_type:<type> - Restrict to specific shifter type
        clan:<name>       - Restrict to specific vampire clan
        tribe:<name>      - Restrict to specific werewolf tribe
        auspice:<name>    - Restrict to specific werewolf auspice
        tradition:<name>  - Restrict to specific mage tradition
        
    Examples:
        +lock north=splat:Vampire
        +lock door=talent:Streetwise
        +lock gate=shifter_type:Ratkin
        +lock portal=splat:Mage
        +lock/list north
        +lock/clear door
    """
    
    key = "+lock"
    locks = "cmd:perm(builders)"
    help_category = "Building and Housing"
    
    def func(self):
        if not self.args:
            self.caller.msg("Usage: +lock <target>=<locktype>:<value>")
            return
            
        # Handle switches first
        if "list" in self.switches:
            target = self.caller.search(self.args, location=self.caller.location)
            if not target:
                return
                
            # Get current locks
            lock_types = target.locks.all()
            if not lock_types:
                self.caller.msg(f"No locks set on {target.get_display_name(self.caller)}.")
                return
                
            # Format and display locks
            table = evtable.EvTable("|wLock Type|n", "|wDefinition|n", border="table")
            for lock in lock_types:
                table.add_row(lock[0], lock[1])
            self.caller.msg(f"Locks on {target.get_display_name(self.caller)}:")
            self.caller.msg(table)
            return
            
        elif "clear" in self.switches:
            target = self.caller.search(self.args, location=self.caller.location)
            if not target:
                return
                
            # Clear all locks except system defaults
            target.locks.clear()
            # Re-add basic traverse lock
            if target.is_typeclass("typeclasses.exits.Exit") or target.is_typeclass("typeclasses.exits.ApartmentExit"):
                target.locks.add("traverse:all()")
            self.caller.msg(f"Cleared all locks from {target.get_display_name(self.caller)}.")
            return
            
        if not self.rhs:
            self.caller.msg("Usage: +lock <target>=<locktype>:<value>")
            return
            
        # Parse lock type and value
        try:
            locktype, value = self.rhs.split(":", 1)
        except ValueError:
            self.caller.msg("Invalid format. Use: +lock <target>=<locktype>:<value>")
            return
            
        # Find target
        target = self.caller.search(self.lhs, location=self.caller.location)
        if not target:
            return
            
        # Validate lock type
        valid_locktypes = {
            'splat': 'db.splat',
            'talent': 'db.talents',
            'skill': 'db.skills',
            'knowledge': 'db.knowledges',
            'merit': 'db.merits',
            'shifter_type': 'db.shifter_type',
            'clan': 'db.clan',
            'tribe': 'db.tribe',
            'auspice': 'db.auspice',
            'tradition': 'db.tradition'
        }
        
        if locktype not in valid_locktypes:
            self.caller.msg(f"Invalid lock type. Valid types: {', '.join(valid_locktypes.keys())}")
            return
            
        # Build the lock string
        if locktype == 'splat':
            # For splats, we want to check if the value matches exactly
            lock_str = f'attr({valid_locktypes[locktype]}) == "{value}"'
        elif locktype in ['talent', 'skill', 'knowledge', 'merit']:
            # For abilities and merits, we want to check if they have any dots in it
            lock_str = f'attr({valid_locktypes[locktype]}) ? "{value}"'
        else:
            # For other types, exact match
            lock_str = f'attr({valid_locktypes[locktype]}) == "{value}"'
            
        # Add the lock
        try:
            # Get existing traverse lock if it's an exit
            if target.is_typeclass("typeclasses.exits.Exit") or target.is_typeclass("typeclasses.exits.ApartmentExit"):
                current_traverse = target.locks.get("traverse")
                if current_traverse and current_traverse != "all()":
                    # Combine with OR operator
                    lock_str = f"{current_traverse} or {lock_str}"
                
            # Set the lock
            if target.is_typeclass("typeclasses.exits.Exit") or target.is_typeclass("typeclasses.exits.ApartmentExit"):
                target.locks.add(f"traverse:{lock_str}")
            else:
                target.locks.add(f"enter:{lock_str}")
                
            self.caller.msg(f"Added {locktype}:{value} lock to {target.get_display_name(self.caller)}.")
            
        except Exception as e:
            self.caller.msg(f"Error setting lock: {str(e)}") 