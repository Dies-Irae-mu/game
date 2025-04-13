from evennia import Command, create_object
from evennia.utils import search
from random import randint
from evennia.utils.utils import class_from_module
import random
from evennia.objects.models import ObjectDB
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils import evtable
from django.db.models import Q
import string

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
        +rent Apartment
        +rent House
        +rent Encampment
    """
    
    key = "+rent"
    locks = "cmd:all()"
    help_category = "Building and Housing"
    
    # Define residence types (moved to class level for easy reference)
    APARTMENT_TYPES = {
        "Studio": {
            "desc": "A cozy studio apartment with an open floor plan.",
            "rooms": 1,
            "resource_modifier": -1
        },
        "Apartment": {
            "desc": "A comfortable one-bedroom apartment with a separate living area.",
            "rooms": 2,
            "resource_modifier": 0
        },
        "Motel Room": {
            "desc": "A rundown motel room with a bed and a small desk.",
            "rooms": 1,
            "resource_modifier": -1
        },
        "Splat Housing": {
            "desc": "Housing for your specific splat, either in a Chantry, Freehold, Sept, or other type.",
            "rooms": 1,
            "resource_modifier": -5
        }
    }
    
    RESIDENTIAL_TYPES = {
        "House": {
            "desc": "A modest single-family home with a small yard.",
            "rooms": 4,
            "resource_modifier": 0
        },
        "Encampment": {
            "desc": "A temporary shelter in a tent or similar structure.",
            "rooms": 1,
            "resource_modifier": -2
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

        # For Splat Housing, check if character's splat is allowed
        if apt_type == "Splat Housing":
            # Get character's splat
            char_splat = self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            if not char_splat:
                self.caller.msg("You must have a splat type set to rent splat housing.")
                return

            # Check if location allows this splat
            allowed_splats = location.db.housing_data.get('allowed_splats', set())
            if not allowed_splats:
                self.caller.msg("This location is not set up for any splat types.")
                return
                
            if char_splat not in allowed_splats:
                self.caller.msg(f"This location does not allow {char_splat}s to rent here.")
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
        
        # Set the residence name based on type
        if apt_type == "Splat Housing":
            residence_name = f"{self.caller.name}'s Room"
            room_type = "splat_housing"
        elif apt_type == "Motel Room":
            residence_name = f"Room {residence_num}"  # residence_num for motels goes like: "1A", "2B", etc.
            room_type = "motel_room"
        elif apt_type == "Encampment":
            residence_name = str(residence_num)  # residence_num is already "Tent X"
            room_type = "encampment"
        elif is_apartment:
            residence_name = f"Apartment {residence_num}"
            if apt_type == "Studio":
                room_type = "studio_apartment"
            else:
                room_type = "apartment"
        else:
            residence_name = str(residence_num)  # includes street name
            if apt_type == "Townhouse": #these are outdated, but still in the database
                room_type = "townhouse"
            elif apt_type == "Cottage": #these are outdated, but still in the database
                room_type = "cottage"
            else:
                room_type = "house"
            
        # Create main residence
        residence = create_object(room_typeclass,
                               key=residence_name,
                               location=None)
        residence.db.desc = available_types[apt_type]['desc']
        # Set owner first
        residence.db.owner = self.caller

        # Initialize home_data
        residence.db.home_data = {
            'locked': False,
            'keyholders': set(),
            'owner': self.caller,
            'co_owners': set()
        }

        # Set room type and housing data based on type
        if apt_type == "Splat Housing":
            # Set specific room type for splat housing
            residence.db.roomtype = f"{self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')} Room"
            
            # Set housing data specific to splat housing
            residence.db.housing_data = {
                'is_housing': True,
                'is_residence': True,
                'max_apartments': 1,
                'current_tenants': {str(residence.id): self.caller.id},
                'apartment_numbers': set(),
                'required_resources': 0,  # Splat housing is free
                'building_zone': location.dbref,
                'connected_rooms': {location.dbref, residence.dbref},
                'available_types': ["Splat Housing"]
            }
        elif apt_type == "Motel Room":
            residence.db.roomtype = "Motel Room"
            # Set housing data for motel room
            residence.db.housing_data = {
                'is_housing': True,
                'is_residence': True,
                'max_apartments': 1,
                'current_tenants': {str(residence.id): self.caller.id},
                'apartment_numbers': set(),
                'required_resources': location.get_housing_cost(apt_type),
                'building_zone': location.dbref,
                'connected_rooms': {location.dbref, residence.dbref},
                'available_types': ["Motel Room"]
            }
        elif apt_type == "Studio":
            residence.db.roomtype = "Studio Apartment"
            # Set standard housing data
            residence.db.housing_data = {
                'is_housing': True,
                'is_residence': True,
                'max_apartments': 1,
                'current_tenants': {str(residence.id): self.caller.id},
                'apartment_numbers': set(),
                'required_resources': location.get_housing_cost(apt_type),
                'building_zone': location.dbref,
                'connected_rooms': {location.dbref, residence.dbref},
                'available_types': [apt_type]
            }
        else:
            # Set room type for regular apartments/houses
            residence.db.roomtype = "Apartment" if is_apartment else apt_type
            # Set standard housing data
            residence.db.housing_data = {
                'is_housing': True,
                'is_residence': True,
                'max_apartments': 1,
                'current_tenants': {str(residence.id): self.caller.id},
                'apartment_numbers': set(),
                'required_resources': location.get_housing_cost(apt_type),
                'building_zone': location.dbref,
                'connected_rooms': {location.dbref, residence.dbref},
                'available_types': [apt_type]
            }

        # Inherit resources from lobby
        residence.db.resources = location.db.resources
        
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
                
                # Set up proper housing data for child room
                child_room.db.housing_data = {
                    'is_housing': True,
                    'is_residence': True,
                    'building_zone': residence.db.housing_data.get('building_zone'),
                    'owner': self.caller,
                    'current_tenants': {str(child_room.id): self.caller.id},
                    'apartment_numbers': set(),
                    'required_resources': residence.db.housing_data.get('required_resources', 0),
                    'connected_rooms': residence.db.housing_data.get('connected_rooms', set())
                }
                
                # Set up proper home data for child room
                child_room.db.home_data = {
                    'locked': False,
                    'keyholders': set(),
                    'owner': self.caller,
                    'co_owners': set()
                }
                
                # Set owner directly as well for compatibility
                child_room.db.owner = self.caller
                
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
        from evennia.utils.create import create_object
        
        exit_typeclass = "typeclasses.exits.ApartmentExit"
        
        # Create entrance from lobby to residence
        if location.db.roomtype == "Splat Housing":
            # For splat housing, use full name as key and initials as alias
            initials = ''.join(word[0].lower() for word in residence_name.split()).upper()
            entrance = create_object(
                exit_typeclass,
                key=residence_name,
                location=location,
                destination=residence,
                aliases=[initials.lower()]
            )
        elif location.db.roomtype == "Encampment":
            # For encampments, use the tent number as both key and just the number as alias
            tent_number = residence_name.split()[-1]  # Get just the number from "Tent X"
            entrance = create_object(
                exit_typeclass,
                key=residence_name,  # "Tent X"
                location=location,
                destination=residence,
                aliases=[tent_number]  # Just the number as alias
            )
        else:
            alias = str(residence_num) if is_apartment else str(residence_num).split()[0]
            entrance = create_object(
                exit_typeclass,
                key=residence_name,
                location=location,
                destination=residence,
                aliases=[alias]
            )

        # Set ownership and permissions for entrance
        entrance.locks.add(f"control:id({self.caller.id}) or perm(Admin);delete:id({self.caller.id}) or perm(Admin)")
        entrance.db.owner = self.caller

        # Create exit back to building/street
        back_exit = create_object(
            exit_typeclass,
            key="Out",
            location=residence,
            destination=location,
            aliases=["o", "out", "exit", "leave"]
        )
        
        # Set ownership and permissions for back exit
        back_exit.locks.add(f"control:id({self.caller.id}) or perm(Admin);delete:id({self.caller.id}) or perm(Admin)")
        back_exit.db.owner = self.caller
        
        # Create exits between rooms if there are child rooms
        if child_rooms:
            for i, room in enumerate(child_rooms, 2):
                # Create exit to child room
                to_room = create_object(
                    exit_typeclass,
                    key=f"Room {i}",
                    location=residence,
                    destination=room,
                    aliases=[str(i)]
                )
                
                # Set ownership and permissions for room exit
                to_room.locks.add(f"control:id({self.caller.id}) or perm(Admin);delete:id({self.caller.id}) or perm(Admin)")
                to_room.db.owner = self.caller

                # Create exit back to main room
                to_main = create_object(
                    exit_typeclass,
                    key="Out",
                    location=room,
                    destination=residence,
                    aliases=["o", "out", "exit", "leave"]
                )
                
                # Set ownership and permissions for back exit
                to_main.locks.add(f"control:id({self.caller.id}) or perm(Admin);delete:id({self.caller.id}) or perm(Admin)")
                to_main.db.owner = self.caller

        # Set proper traverse permissions for all exits
        for exit in residence.exits:
            exit.locks.add("traverse:all()")
            
        # Set proper traverse permissions for entrance
        entrance.locks.add("traverse:all()")
        
        # For child rooms
        if child_rooms:
            for room in child_rooms:
                for exit in room.exits:
                    exit.locks.add("traverse:all()")

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
            
            # For motel rooms, generate a number (1-9) followed by a letter (A-Z)
            if location.db.roomtype in ["Motel", "Motel Room"]:  # Check for both possible types
                import string
                letters = list(string.ascii_uppercase)  # A through Z
                numbers = list(range(1, 10))  # 1 through 9
                
                attempts = 0
                while attempts < 100:  # Prevent infinite loop
                    number = random.choice(numbers)
                    letter = random.choice(letters)
                    room_code = f"{number}{letter}"
                    
                    if room_code not in used_numbers:
                        return room_code
                    attempts += 1
            elif location.db.roomtype == "Encampment":
                # For encampments, just generate a tent number
                attempts = 0
                while attempts < 100:  # Prevent infinite loop
                    number = random.randint(1, 99)
                    tent_number = f"Tent {number}"
                    if tent_number not in used_numbers:
                        return tent_number
                    attempts += 1
            elif is_apartment:
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

    def is_valid_residence(self, room):
        """
        Check if a room is a valid residence.
        
        Args:
            room (Object): The room to check
            
        Returns:
            bool: True if this is a valid residence, False otherwise
        """
        if not room or not hasattr(room, 'db'):
            return False
            
        # Debug output
        roomtype = room.db.roomtype if hasattr(room.db, 'roomtype') else None
        
        # Check for housing data
        home_data = room.db.home_data if hasattr(room.db, 'home_data') else None
        housing_data = room.db.housing_data if hasattr(room.db, 'housing_data') else None
        
        # Valid room types for residences
        valid_types = [
            "apartment", "house", "splat_housing", "encampment",
            "mortal_room", "mortal_plus_room", "mortal+_room", "possessed_room",
            "mage_room", "vampire_room", "changeling_room", 
            "motel_room", "apartment_room", "house_room", "studio",
            "studio apartment", "shifter_room", "companion_room"
        ]
        
        # Check if room type is valid
        has_valid_type = False
        if roomtype:
            roomtype_lower = roomtype.lower()
            has_valid_type = (
                roomtype_lower in [t.lower() for t in valid_types] or
                roomtype_lower.endswith("room")
            )
        
        # Check both roomtype and housing data
        has_housing_data = (
            (home_data is not None and home_data.get('owner')) or
            (housing_data is not None and housing_data.get('is_residence')) or
            hasattr(room.db, 'owner')  # Legacy check
        )
        
        return has_valid_type and has_housing_data

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
    help_category = "Building and Housing"
    
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
                if not (location.db.roomtype and 
                        any(rtype.lower() in location.db.roomtype.lower() 
                            for rtype in ["apartment", "house", "splat_housing", "studio", "room", "encampment"]) and 
                        self.is_owner(location, self.caller)):
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
                    # Delete all exits in the child room
                    for exit in room.exits:
                        exit.delete()
                    room.delete()

        # Update building data
        if building and building.db.housing_data:
            if residence.id in building.db.housing_data['current_tenants']:
                del building.db.housing_data['current_tenants'][residence.id]
            # Handle apartment numbers for both numeric and string values
            try:
                number = int(residence.key.split()[-1])
                if number in building.db.housing_data['apartment_numbers']:
                    building.db.housing_data['apartment_numbers'].remove(number)
            except (ValueError, IndexError):
                # If it's not a numeric apartment number, try to remove the full name
                if residence.key in building.db.housing_data['apartment_numbers']:
                    building.db.housing_data['apartment_numbers'].remove(residence.key)
        
        # Clear home location if this was their home
        if self.caller.home == residence:
            self.caller.home = None
            self.caller.msg("Your home location has been cleared.")
            
        # Delete all exits in the main residence
        for exit in residence.exits:
            exit.delete()
            
        # Delete the entrance exit from the building
        for exit in building.contents:
            if (hasattr(exit, 'destination') and 
                exit.destination == residence):
                exit.delete()
            
        # Delete the residence
        residence.delete()
        self.caller.msg("You have vacated the residence.")

class CmdManageHome(MuxCommand):
    """
    Manage your auto-build home, including locks, keys, descriptions, exits, and co-owners.
    
    Usage:
        +home                - Go to your home
        +home/set            - Set current residence as your home
        +home/lock           - Lock your residence
        +home/unlock         - Unlock your residence
        +home/key <player>   - Give a key to another player
        +home/unkey <player> - Remove a key from a player
        +home/keys           - List who has keys to your residence
        +home/status         - Show lock status of your residence
        +home/find           - Show location of your residence
        +home/unfindable <on/off> - Set whether your residence can be found
        +home/dig <roomname>[;alias;alias...] [= <exit_to_there>[;alias], <exit_to_here>[;alias]] 
                            - Create a new room connected to your current room (max 2 extra rooms)
        +home/destroy [obj, obj2, obj3|here] - Destroy rooms or exits in your residence
        
        +home/desc              - Show current room description
        +home/desc <text>       - Set description for current room
        +home/desc <num> = <text>  - Set description for specific room
        
        +home/exit <exit> = <new name>      - Rename an exit
        +home/exit/alias <exit> = <alias>   - Add an alias to an exit
        +home/exit/clear <exit>             - Clear all aliases from an exit
        +home/exit/remove <exit> = <alias>  - Remove specific alias from an exit
        
        +home/coowner                    - List current co-owners
        +home/coowner <player1,player2>  - Add co-owner(s)
        +home/coowner/remove <player>    - Remove a co-owner
        
        +home/vacate              - Vacate your residence in current building
        +home/vacate/all         - List all your residences
        +home/vacate <number>    - Vacate specific residence

        +home/view               - List all views in your residence
        +home/view <viewname>    - Show specific view
        +home/view set/<viewname>=<text>  - Set a view
        +home/view del/<viewname>  - Delete a view

    Examples:
        +home/dig kitchen = north;n, south;s
        +home/dig bedroom = east;e, west;w
        +home/dig "Master Bedroom" = up;u, down;d
        +home/destroy north, south, door
        +home/destroy here
        +home/view set/window=Through the window you see a beautiful garden
        +home/view del/window
    """
    
    key = "+home"
    aliases = ["home"]
    locks = "cmd:all()"
    help_category = "Building and Housing"
    
    def init_home_data(self, location):
        """Initialize home data if it doesn't exist"""
        if not location.db.home_data:
            location.db.home_data = {
                'locked': False,
                'keyholders': set(),
                'owner': location.db.owner if hasattr(location.db, 'owner') else None,
                'co_owners': set()
            }
        elif location.db.home_data.get('owner') is None and hasattr(location.db, 'owner'):
            location.db.home_data['owner'] = location.db.owner
        return location.db.home_data

    def find_player_residence(self, player):
        """
        Find a player's residence globally.
        
        Args:
            player (Object): The player to search for
            
        Returns:
            Object or None: The player's residence if found, None otherwise
        """
        from evennia.objects.models import ObjectDB
        
        
        for room in ObjectDB.objects.filter(db_typeclass_path__contains="rooms.Room"):
            if not hasattr(room, 'db'):
                continue
                
            # Debug room info
            if hasattr(room.db, 'roomtype'):
                roomtype = room.db.roomtype
            else:
                roomtype = None
            # Check if this is a valid residence first
            is_valid = self.is_valid_residence(room)
            
            if not is_valid:
                continue
                
            # Now check if the player owns it
            is_owner = self.is_owner(room, player)

            if is_owner:
                return room
        return None

    def is_valid_residence(self, room):
        """
        Check if a room is a valid residence.
        
        Args:
            room (Object): The room to check
            
        Returns:
            bool: True if this is a valid residence, False otherwise
        """
        if not room or not hasattr(room, 'db'):
            return False
            
        # Debug output
        roomtype = room.db.roomtype if hasattr(room.db, 'roomtype') else None
        
        # Check for housing data
        home_data = room.db.home_data if hasattr(room.db, 'home_data') else None
        housing_data = room.db.housing_data if hasattr(room.db, 'housing_data') else None
        
        # Valid room types for residences
        valid_types = [
            "apartment", "house", "splat_housing", "encampment",
            "mortal_room", "mortal_plus_room", "mortal+_room", "possessed_room",
            "mage_room", "vampire_room", "changeling_room", 
            "motel_room", "apartment_room", "house_room", "studio",
            "studio apartment", "shifter_room", "companion_room"
        ]
        
        # Check if room type is valid
        has_valid_type = False
        if roomtype:
            roomtype_lower = roomtype.lower()
            has_valid_type = (
                roomtype_lower in [t.lower() for t in valid_types] or
                roomtype_lower.endswith("room")
            )
        
        # Check both roomtype and housing data
        has_housing_data = (
            (home_data is not None and home_data.get('owner')) or
            (housing_data is not None and housing_data.get('is_residence')) or
            hasattr(room.db, 'owner')  # Legacy check
        )
        return has_valid_type and has_housing_data

    def is_owner(self, room, player):
        """
        Check if a player owns a residence.
        
        Args:
            room (Object): The room to check
            player (Object): The player to check ownership for
            
        Returns:
            bool: True if the player owns the residence, False otherwise
        """
        if not room or not player or not hasattr(room, 'db'):
            return False

        # Check home_data first
        home_data = room.db.home_data if hasattr(room.db, 'home_data') else None
        if home_data:
            # Check primary owner
            if home_data.get('owner') and home_data['owner'].id == player.id:
                return True
            # Check co-owners
            if player.id in home_data.get('co_owners', set()):
                return True
            
        # Check housing_data next
        housing_data = room.db.housing_data if hasattr(room.db, 'housing_data') else None
        if housing_data:
            # Check owner field
            if housing_data.get('owner'):
                is_housing_owner = housing_data['owner'].id == player.id
                if is_housing_owner:
                    return True
            
            # Check current_tenants
            if housing_data.get('current_tenants'):
                is_tenant = str(room.id) in housing_data['current_tenants'] and housing_data['current_tenants'][str(room.id)] == player.id
                if is_tenant:
                    return True
            
        # Finally check legacy owner
        if hasattr(room.db, 'owner') and room.db.owner:
            is_legacy_owner = room.db.owner.id == player.id
            if is_legacy_owner:
                return True
            
        return False

    def update_entrance_lock(self, residence, home_data):
        """Helper method to update the entrance lock based on current keyholders"""
        # Find the entrance to this residence from the parent room
        parent_room = None
        for exit in residence.exits:
            if exit.key == "Out":
                parent_room = exit.destination
                break
                
        if parent_room:
            # Find the entrance in the parent room
            for exit in parent_room.contents:
                if (hasattr(exit, 'destination') and 
                    exit.destination == residence):
                    # Make sure it's using the ApartmentExit typeclass
                    if not exit.is_typeclass("typeclasses.exits.ApartmentExit"):
                        exit.swap_typeclass("typeclasses.exits.ApartmentExit",
                                          clean_attributes=False)
                    # Update lock string
                    lockstring = "view:all()"
                    if home_data['locked']:
                        # When locked, only owner, keyholders, and staff can enter
                        keyholders = ",".join([f"id({pid})" for pid in home_data['keyholders']])
                        if home_data.get('owner'):
                            lockstring += f";traverse:id({home_data['owner'].id})"
                            if keyholders:
                                lockstring += f" or {keyholders}"
                        lockstring += " or perm(Admin) or perm(Builder) or perm(Staff)"
                    else:
                        # When unlocked, anyone can enter
                        lockstring += ";traverse:all()"
                    exit.locks.add(lockstring)
                    return True
        return False

    def _destroy_room(self, room, main_room):
        """Helper method to properly destroy a room and relocate all occupants"""
        # Move any occupants to the main room
        for obj in room.contents:
            if obj.has_account:
                obj.msg("This room is being destroyed. You are being moved out.")
                
                # Ensure we're not leaving a ghost character behind
                if hasattr(obj, 'sessions'):
                    for session in obj.sessions.all():
                        if hasattr(session, 'puppet') and session.puppet == obj:
                            # Make sure the session knows we're moving
                            session.msg(text=f"Being moved out as this room is being destroyed...")
                            
                obj.move_to(main_room)

        # Remove from child rooms list
        if room in main_room.db.child_rooms:
            main_room.db.child_rooms.remove(room)

        # Delete all exits in the room
        for exit in room.exits:
            exit.delete()
            
        # Delete all exits to this room
        for exit in main_room.exits:
            if hasattr(exit, 'destination') and exit.destination == room:
                exit.delete()
                
        # Delete the room itself
        room.delete()
        
        return True

    def func(self):
        # If no switches and no args, treat as "go home" command
        if not self.switches and not self.args:
            # Check if player has a home set
            if not self.caller.home:
                self.caller.msg("You haven't set a home yet.")
                return
                
            # Check if home still exists and is a valid residence
            if not self.is_valid_residence(self.caller.home):
                self.caller.msg("Your home location seems to be invalid. Please set a new home.")
                return
                
            # Initialize home data if needed
            home_data = self.init_home_data(self.caller.home)
                
            # Check if the home is locked and we don't have access
            if (home_data['locked'] and 
                not self.is_owner(self.caller.home, self.caller) and 
                self.caller.id not in home_data['keyholders'] and
                not self.caller.check_permstring("builders")):
                self.caller.msg("Your home is currently locked and you don't have a key.")
                return
                
            # Store old location for announcements
            old_location = self.caller.location
                
            # Announce departure
            if old_location:
                old_location.msg_contents(f"{self.caller.name} has left to go home.", exclude=self.caller)
                
            # Ensure we're not leaving a ghost character behind by clearing any session references
            # to the old location
            for session in self.caller.sessions.all():
                if hasattr(session, 'puppet') and session.puppet == self.caller:
                    # Make sure the session knows we're moving
                    session.msg(text="Moving to your home...")
                
            # Try to go home
            self.caller.move_to(self.caller.home)
            self.caller.home.msg_contents(f"{self.caller.name} arrives home.", exclude=self.caller)
            return

        # Handle find switch
        if "find" in self.switches:
            residence = self.find_player_residence(self.caller)
            if not residence:
                self.caller.msg("You don't own a residence.")
                return
                
            # Find the parent room (floor)
            parent_room = None
            for exit in residence.exits:
                if exit.key == "Out":
                    parent_room = exit.destination
                    break
                    
            if parent_room:
                self.caller.msg(f"Your residence ({residence.get_display_name(self.caller)}) "
                              f"is located in {parent_room.get_display_name(self.caller)}.")
            return

        # Handle key and unkey commands (can be used from anywhere)
        if "key" in self.switches or "unkey" in self.switches:
            residence = self.find_player_residence(self.caller)
            if not residence:
                self.caller.msg("You don't own a residence.")
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
                
            home_data = self.init_home_data(residence)
            
            if "key" in self.switches:
                if target.id in home_data['keyholders']:
                    self.caller.msg(f"{target.name} already has a key to your residence.")
                    return
                    
                home_data['keyholders'].add(target.id)
                # Update the entrance lock
                self.update_entrance_lock(residence, home_data)
                self.caller.msg(f"You have given {target.name} a key to your residence.")
                if target.has_account:
                    target.msg(f"{self.caller.name} has given you a key to their residence.")
                    
            else:  # unkey
                if target.id not in home_data['keyholders']:
                    self.caller.msg(f"{target.name} doesn't have a key to your residence.")
                    return
                    
                home_data['keyholders'].remove(target.id)
                # Update the entrance lock
                self.update_entrance_lock(residence, home_data)
                self.caller.msg(f"You have taken back {target.name}'s key to your residence.")
                if target.has_account:
                    target.msg(f"{self.caller.name} has taken back your key to their residence.")
            return
        
        # For other commands, we need to be in a residence
        location = self.caller.location
        if not self.is_valid_residence(location):
            self.caller.msg("This command can only be used inside residences.")
            return

        # Initialize home data
        home_data = self.init_home_data(location)
            
        if "set" in self.switches:
            # Check ownership
            if not self.is_owner(location, self.caller):
                self.caller.msg("You don't own this residence.")
                return
                
            # Set as home
            self.caller.home = location
            self.caller.msg("You have set this residence as your home.")
            
        elif "lock" in self.switches:
            if not self.is_owner(location, self.caller):
                self.caller.msg("You don't own this residence.")
                return
                
            # Ensure owner is set
            if not home_data.get('owner'):
                home_data['owner'] = self.caller
                
            home_data['locked'] = True
            if self.update_entrance_lock(location, home_data):
                self.caller.msg("You have locked your residence.")
            else:
                self.caller.msg("Error updating residence lock. Please contact staff.")
            
        elif "unlock" in self.switches:
            if not self.is_owner(location, self.caller):
                self.caller.msg("You don't own this residence.")
                return
                
            home_data['locked'] = False
            if self.update_entrance_lock(location, home_data):
                self.caller.msg("You have unlocked your residence.")
            else:
                self.caller.msg("Error updating residence lock. Please contact staff.")
            
        elif "keys" in self.switches:
            if not self.is_owner(location, self.caller):
                self.caller.msg("You don't own this residence.")
                return
                
            keyholders = []
            for pid in home_data['keyholders']:
                char = self.caller.search(f"#{pid}")
                if char:
                    keyholders.append(char.name)
                    
            if keyholders:
                self.caller.msg("People with keys to your residence:")
                self.caller.msg("\n".join(f"- {name}" for name in keyholders))
            else:
                self.caller.msg("Nobody else has keys to your residence.")
                
        elif "status" in self.switches:
            # Find player's residence
            home = self.caller.home
            if not home or not self.is_valid_residence(home):
                self.caller.msg("You haven't set a residence as your home.")
                return
                
            home_data = self.init_home_data(home)
            status = "locked" if home_data['locked'] else "unlocked"
            self.caller.msg(f"Your residence ({home.get_display_name(self.caller)}) is currently {status}.")
            
            # Show keyholders if it's the caller's residence
            if self.is_owner(home, self.caller) and 'keyholders' in home_data and home_data['keyholders']:
                keyholders = []
                for pid in home_data['keyholders']:
                    char = self.caller.search(f"#{pid}")
                    if char:
                        keyholders.append(char.name)
                        
                if keyholders:
                    self.caller.msg("People with keys:")
                    self.caller.msg("\n".join(f"- {name}" for name in keyholders))

        # Handle description commands
        elif "desc" in self.switches:
            if not self.is_owner(location, self.caller):
                self.caller.msg("You don't own this residence.")
                return

            if not self.args:
                # Show current description
                self.caller.msg(location.db.desc)
                return

            if "=" in self.args:
                # Setting description for specific room
                room_num, desc = self.args.split("=", 1)
                try:
                    room_num = int(room_num.strip())
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

                target_room.db.desc = desc.strip()
                self.caller.msg(f"Description set for Room {room_num}.")
            else:
                # Set description for current room
                location.db.desc = self.args
                self.caller.msg("Description set.")

        # Handle exit commands
        elif "exit" in self.switches:
            if not self.is_owner(location, self.caller):
                self.caller.msg("You don't own this residence.")
                return

            if not self.args:
                # List current exits and their aliases
                exits = [ex for ex in location.contents 
                        if ex.destination and ex.key != "Out"]
                if not exits:
                    self.caller.msg("No customizable exits found.")
                    return

                from evennia.utils.evtable import EvTable
                table = EvTable("|wExit Name|n", "|wAliases|n", border="table")
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
                    self.caller.msg("Usage: +home/aexit/alias <exit> = <alias>")
                    return

                exit = self.caller.search(self.lhs, location=location, 
                                        typeclass="typeclasses.exits.ApartmentExit")
                if not exit:
                    return

                exit.aliases.add(self.rhs)
                self.caller.msg(f"Added alias '{self.rhs}' to exit '{exit.name}'.")

            elif "clear" in self.switches:
                exit = self.caller.search(self.args, location=location, 
                                        typeclass="typeclasses.exits.ApartmentExit")
                if not exit:
                    return

                exit.aliases.clear()
                self.caller.msg(f"Cleared all aliases from exit '{exit.name}'.")

            elif "remove" in self.switches:
                if not self.rhs or not self.lhs:
                    self.caller.msg("Usage: +home/aexit/remove <exit> = <alias>")
                    return

                exit = self.caller.search(self.lhs, location=location, 
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
                    self.caller.msg("Usage: +home/aexit <exit> = <new name>")
                    return

                exit = self.caller.search(self.lhs, location=location, 
                                        typeclass="typeclasses.exits.ApartmentExit")
                if not exit:
                    return

                old_name = exit.name
                exit.name = self.rhs
                self.caller.msg(f"Renamed exit '{old_name}' to '{self.rhs}'.")

        # Handle co-owner commands
        elif "coowner" in self.switches:
            if not self.is_owner(location, self.caller):
                self.caller.msg("You don't own this residence.")
                return

            if "remove" in self.switches:
                if not self.args:
                    self.caller.msg("Usage: +home/coowner/remove <player>")
                    return

                # Search for player account
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

                if target.id not in home_data.get('co_owners', set()):
                    self.caller.msg(f"{target.name} is not a co-owner of your residence.")
                    return

                home_data['co_owners'].remove(target.id)
                self.caller.msg(f"Removed {target.name} as a co-owner of your residence.")
                if target.has_account:
                    target.msg(f"{self.caller.name} has removed you as a co-owner of their residence.")

            elif not self.args:
                # List co-owners
                co_owners = []
                for pid in home_data.get('co_owners', set()):
                    char = self.caller.search(f"#{pid}")
                    if char:
                        co_owners.append(char.name)

                if co_owners:
                    self.caller.msg("Co-owners of your residence:")
                    self.caller.msg("\n".join(f"- {name}" for name in co_owners))
                else:
                    self.caller.msg("Your residence has no co-owners.")

            else:
                # Add co-owner(s)
                from evennia.accounts.models import AccountDB
                for player_name in self.args.split(','):
                    player_name = player_name.strip()
                    target_account = AccountDB.objects.filter(username__iexact=player_name).first()
                    if not target_account:
                        self.caller.msg(f"Player '{player_name}' not found.")
                        continue

                    target = target_account.puppet or target_account.db._last_puppet
                    if not target:
                        self.caller.msg(f"Could not find a character for {player_name}.")
                        continue

                    if target.id in home_data.get('co_owners', set()):
                        self.caller.msg(f"{target.name} is already a co-owner.")
                        continue

                    if 'co_owners' not in home_data:
                        home_data['co_owners'] = set()
                    home_data['co_owners'].add(target.id)
                    self.caller.msg(f"Added {target.name} as a co-owner of your residence.")
                    if target.has_account:
                        target.msg(f"{self.caller.name} has made you a co-owner of their residence.")

        # Handle vacate commands
        elif "vacate" in self.switches:
            # Check if we're in a child room first
            if hasattr(location.db, 'parent_room') and location.db.parent_room:
                self.caller.msg("You must be in your main room to vacate your residence.")
                return
            if "all" in self.switches:
                # List all residences owned by player
                residences = []
                from evennia.objects.models import ObjectDB
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

                from evennia.utils.evtable import EvTable
                table = EvTable("|wResidence|n", "|wLocation|n", "|wType|n", border="table")
                for area, residence in residences:
                    table.add_row(
                        residence.get_display_name(self.caller),
                        area.get_display_name(self.caller),
                        residence.db.roomtype.title()
                    )
                self.caller.msg(table)
                return

            # Find the residence to vacate
            building = None
            residence = None

            if self.args:
                # Try to find specific residence by number
                from evennia.objects.models import ObjectDB
                for room in ObjectDB.objects.filter(db_typeclass_path__contains="rooms.Room"):
                    if room.is_housing_area():
                        tenants = room.db.housing_data.get('current_tenants', {})
                        for res_id, tenant_id in tenants.items():
                            if tenant_id == self.caller.id:
                                try:
                                    res = ObjectDB.objects.get(id=res_id)
                                    if res.key.endswith(str(self.args)):
                                        building = room
                                        residence = res
                                        break
                                except ObjectDB.DoesNotExist:
                                    continue
                if not residence:
                    self.caller.msg("You don't own that residence.")
                    return
            else:
                # Try to vacate current location
                location = self.caller.location
                if not (location.db.roomtype and 
                        any(rtype.lower() in location.db.roomtype.lower() 
                            for rtype in ["apartment", "house", "splat_housing", "studio", "room", "encampment"]) and 
                        self.is_owner(location, self.caller)):
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
            if not self.is_owner(residence, self.caller):
                self.caller.msg("You don't own this residence.")
                return

            # Move any occupants to the building
            for obj in residence.contents:
                if obj.has_account:
                    obj.msg("This residence is being vacated. You are being moved out.")
                    
                    # Ensure we're not leaving a ghost character behind
                    if hasattr(obj, 'sessions'):
                        for session in obj.sessions.all():
                            if hasattr(session, 'puppet') and session.puppet == obj:
                                # Make sure the session knows we're moving
                                session.msg(text=f"Being moved out as residence is being vacated...")
                                
                    obj.move_to(building)

            # Clean up child rooms if they exist
            if hasattr(residence.db, 'child_rooms'):
                for room in residence.db.child_rooms:
                    if room:
                        for obj in room.contents:
                            if obj.has_account:
                                # Ensure we're not leaving a ghost character behind
                                if hasattr(obj, 'sessions'):
                                    for session in obj.sessions.all():
                                        if hasattr(session, 'puppet') and session.puppet == obj:
                                            # Make sure the session knows we're moving
                                            session.msg(text=f"Being moved out as residence is being vacated...")
                                            
                                obj.move_to(building)
                        # Delete all exits in the child room
                        for exit in room.exits:
                            exit.delete()
                        room.delete()

            # Update building data
            if building and building.db.housing_data:
                if str(residence.id) in building.db.housing_data['current_tenants']:
                    del building.db.housing_data['current_tenants'][str(residence.id)]
                # Handle apartment numbers for both numeric and string values
                try:
                    number = int(residence.key.split()[-1])
                    if number in building.db.housing_data['apartment_numbers']:
                        building.db.housing_data['apartment_numbers'].remove(number)
                except (ValueError, IndexError):
                    # If it's not a numeric apartment number, try to remove the full name
                    if residence.key in building.db.housing_data['apartment_numbers']:
                        building.db.housing_data['apartment_numbers'].remove(residence.key)

            # Clear home location if this was their home
            if self.caller.home == residence:
                self.caller.home = None
                self.caller.msg("Your home location has been cleared.")

            # Delete all exits in the main residence
            for exit in residence.exits:
                exit.delete()

            # Delete the entrance exit from the building
            for exit in building.contents:
                if (hasattr(exit, 'destination') and 
                    exit.destination == residence):
                    exit.delete()

            # Delete the residence
            residence.delete()
            self.caller.msg("You have vacated the residence.")

        elif "unfindable" in self.switches:
            if not self.is_owner(location, self.caller):
                self.caller.msg("You don't own this residence.")
                return
                
            if not self.args:
                self.caller.msg("Usage: +home/unfindable <on/off>")
                return
                
            setting = self.args.strip().lower()
            if setting not in ["on", "off"]:
                self.caller.msg("Please specify either 'on' or 'off'.")
                return
                
            location.db.unfindable = (setting == "on")
            self.caller.msg(f"Your residence is now {'unfindable' if setting == 'on' else 'findable'}.")

        elif "dig" in self.switches:
            # Check if we're in a valid residence
            if not self.is_valid_residence(location):
                self.caller.msg("This command can only be used inside residences.")
                return

            # Check ownership
            if not self.is_owner(location, self.caller):
                self.caller.msg("You don't own this residence.")
                return

            # Get the main residence room (in case we're in a child room)
            main_room = None
            if hasattr(location.db, 'parent_room') and location.db.parent_room:
                main_room = location.db.parent_room
            else:
                main_room = location

            # Check if this is a motel room, splat housing, or studio
            is_restricted = False
            # Check room type directly
            if main_room.db.roomtype in ["Motel Room", "Splat Housing", "Studio", "Studio Apartment", "Mage Room", "Shifter Room", "Vampire Room", "Mortal+ Room", "Mortal Room", "Changeling Room", "Companion Room", "Possessed Room", "Encampment"]:
                is_restricted = True
            # Also check available types from housing data
            elif main_room.db.housing_data and main_room.db.housing_data.get('available_types'):
                available_types = main_room.db.housing_data.get('available_types', [])
                if "Splat Housing" in available_types or "Studio" in available_types or "Encampment" in available_types:
                    is_restricted = True

            if is_restricted:
                self.caller.msg(f"{main_room.db.roomtype}s cannot be expanded with additional rooms.")
                return

            # Initialize child_rooms if needed
            if not hasattr(main_room.db, 'child_rooms'):
                main_room.db.child_rooms = []
            elif main_room.db.child_rooms is None:
                main_room.db.child_rooms = []

            # Clean up any None values in child_rooms list
            main_room.db.child_rooms = [room for room in main_room.db.child_rooms if room]

            # Get the residence type and its base number of rooms
            apt_type = None
            if main_room.db.housing_data and main_room.db.housing_data.get('available_types'):
                apt_type = main_room.db.housing_data['available_types'][0]

            if apt_type:
                from commands.housing import CmdRent
                # Check residential types first since houses have more rooms
                base_rooms = CmdRent.RESIDENTIAL_TYPES.get(apt_type, {}).get('rooms', 0)
                if not base_rooms:
                    # If not found in residential types, check apartment types
                    base_rooms = CmdRent.APARTMENT_TYPES.get(apt_type, {}).get('rooms', 1)
            else:
                # Default to 1 if no type is found
                base_rooms = 1

            # Calculate how many additional rooms the player can create
            # They can create up to 2 rooms beyond their base room count
            base_child_rooms = max(0, base_rooms - 1)  # Subtract 1 for the main room
            current_extra_rooms = len([room for room in main_room.db.child_rooms if room]) - base_child_rooms
            max_extra_rooms = 2  # Maximum number of additional rooms beyond base

            if current_extra_rooms >= max_extra_rooms:
                self.caller.msg(f"You can only create up to {max_extra_rooms} additional rooms beyond your base {base_rooms} room{'s' if base_rooms > 1 else ''}.")
                return

            if not self.args:
                self.caller.msg("Usage: +home/dig <roomname>[;alias;alias...] [= <exit_to_there>[;alias], <exit_to_here>[;alias]]")
                return

            # Split args into room name and exits
            if "=" in self.args:
                roomname, exits = self.args.split("=", 1)
                exits = exits.strip()
            else:
                roomname = self.args
                exits = None

            # Handle room aliases
            if ";" in roomname:
                roomname, *aliases = roomname.split(";")
            else:
                aliases = []
            roomname = roomname.strip()

            # Create the new room with the same typeclass as the main room
            room_typeclass = main_room.typeclass_path
            try:
                # Get the main residence's prefix (address/name)
                main_prefix = " - ".join(main_room.key.split(" - ")[:-1]) if " - " in main_room.key else main_room.key
                full_room_name = f"{main_prefix} - {roomname}"
                
                new_room = create_object(
                    room_typeclass,
                    key=full_room_name,
                    aliases=aliases,
                    location=None  # Rooms should have no location
                )
                
                # Set room type based on parent room's base type
                base_roomtype = main_room.db.roomtype
                if base_roomtype:
                    # Handle special cases for splat housing
                    if "Room" in base_roomtype:
                        # If it's already a "Room" type (like "Mage Room"), use it as is
                        new_room.db.roomtype = base_roomtype
                    else:
                        # For other types, append "_room" if it's not already there
                        if not base_roomtype.endswith(" room"):
                            new_room.db.roomtype = f"{base_roomtype} room"
                        else:
                            new_room.db.roomtype = base_roomtype
                else:
                    # Fallback to a generic room type
                    new_room.db.roomtype = "Room"
                
                # Copy relevant attributes from main room
                new_room.db.resources = main_room.db.resources
                new_room.db.unfindable = main_room.db.unfindable
                
                # Set up housing data
                new_room.db.housing_data = {
                    'is_housing': True,
                    'is_residence': True,
                    'building_zone': main_room.db.housing_data.get('building_zone'),
                    'owner': self.caller,
                    'current_tenants': {},
                    'apartment_numbers': set(),
                    'required_resources': main_room.db.housing_data.get('required_resources', 0),
                    'connected_rooms': main_room.db.housing_data.get('connected_rooms', set()),
                    'allowed_splats': main_room.db.housing_data.get('allowed_splats', set()),
                    'available_types': main_room.db.housing_data.get('available_types', [])
                }
                
                # Set up home data
                new_room.db.home_data = {
                    'locked': False,
                    'keyholders': set(),
                    'owner': self.caller,
                    'co_owners': set()
                }
                
                # Set parent room reference
                new_room.db.parent_room = main_room
                
                # Add to child rooms list
                main_room.db.child_rooms.append(new_room)

                # Handle exit creation if specified
                if exits:
                    try:
                        exit_to_there, exit_to_here = map(str.strip, exits.split(","))
                    except ValueError:
                        exit_to_there = exits.strip()
                        exit_to_here = None

                    # Create exit to the new room
                    if exit_to_there:
                        if ";" in exit_to_there:
                            exit_name, *exit_aliases = exit_to_there.split(";")
                        else:
                            exit_name, exit_aliases = exit_to_there, []
                            
                        # Create the exit using ApartmentExit typeclass
                        exit_to = create_object(
                            "typeclasses.exits.ApartmentExit",
                            key=exit_name.strip(),
                            aliases=exit_aliases,
                            location=location,
                            destination=new_room
                        )
                        exit_to.locks.add("traverse:all()")
                        exit_to.db.owner = self.caller

                    # Create return exit if specified
                    if exit_to_here:
                        if ";" in exit_to_here:
                            exit_name, *exit_aliases = exit_to_here.split(";")
                        else:
                            exit_name, exit_aliases = exit_to_here, []
                            
                        # Create the return exit using ApartmentExit typeclass
                        exit_from = create_object(
                            "typeclasses.exits.ApartmentExit",
                            key=exit_name.strip(),
                            aliases=exit_aliases,
                            location=new_room,
                            destination=location
                        )
                        exit_from.locks.add("traverse:all()")
                        exit_from.db.owner = self.caller

                self.caller.msg(f"Created new room '{full_room_name}' with appropriate exits.")

            except Exception as e:
                self.caller.msg(f"Error creating room: {str(e)}")
                # Clean up if something went wrong
                if 'new_room' in locals():
                    new_room.delete()
                return

        elif "destroy" in self.switches:
            # Check if we're in a valid residence
            if not self.is_valid_residence(location):
                self.caller.msg("This command can only be used inside residences.")
                return

            # Get the main residence room (in case we're in a child room)
            main_room = None
            if hasattr(location.db, 'parent_room') and location.db.parent_room:
                main_room = location.db.parent_room
            else:
                main_room = location

            # Check ownership of the main residence
            if not self.is_owner(main_room, self.caller):
                self.caller.msg("You don't own this residence.")
                return

            # Handle 'here' case
            if not self.args or self.args.strip().lower() == "here":
                # Can't destroy the main room
                if location == main_room:
                    self.caller.msg("You cannot destroy your main room. Use +home/vacate to remove your entire residence.")
                    return

                # Verify this is a child room
                if location not in main_room.db.child_rooms:
                    self.caller.msg("This room is not part of your residence.")
                    return

                # Ask for confirmation
                self.caller.msg(f"|rAre you sure you want to destroy {location.get_display_name(self.caller)}?|n")
                self.caller.msg("This will delete the room and all its exits. Type '+home/destroy here/yes' to confirm.")
                return

            # Handle confirmation for 'here'
            if self.args.strip().lower() == "here/yes":
                if location == main_room:
                    self.caller.msg("You cannot destroy your main room. Use +home/vacate to remove your entire residence.")
                    return

                if location not in main_room.db.child_rooms:
                    self.caller.msg("This room is not part of your residence.")
                    return

                # Use the helper method to destroy the room
                if self._destroy_room(location, main_room):
                    self.caller.msg("Room destroyed.")
                return

            # Handle object list case
            if "," in self.args:
                targets = [obj.strip() for obj in self.args.split(",")]
            else:
                targets = [self.args.strip()]

            # Process each target
            for target in targets:
                obj = self.caller.search(target, location=location)
                if not obj:
                    continue

                # Only allow destroying exits and rooms
                if not (obj.is_typeclass("typeclasses.exits.ApartmentExit") or 
                       obj.is_typeclass("typeclasses.rooms.Room")):
                    self.caller.msg(f"You can only destroy exits and rooms, not {obj.get_display_name(self.caller)}.")
                    continue

                # For rooms, verify it's a child room
                if obj.is_typeclass("typeclasses.rooms.Room"):
                    if obj == main_room:
                        self.caller.msg("You cannot destroy your main room. Use +home/vacate to remove your entire residence.")
                        continue
                    if obj not in main_room.db.child_rooms:
                        self.caller.msg(f"{obj.get_display_name(self.caller)} is not part of your residence.")
                        continue

                # For exits, verify they're in your residence
                if obj.is_typeclass("typeclasses.exits.ApartmentExit"):
                    if not (obj.location == location or 
                           (obj.destination and obj.destination in main_room.db.child_rooms)):
                        self.caller.msg(f"{obj.get_display_name(self.caller)} is not part of your residence.")
                        continue

                # Ask for confirmation
                self.caller.msg(f"|rAre you sure you want to destroy {obj.get_display_name(self.caller)}?|n")
                self.caller.msg(f"Type '+home/destroy {target}/yes' to confirm.")
                continue

            # Handle confirmation for specific objects
            if self.args.strip().lower().endswith("/yes"):
                target = self.args[:-4].strip()  # Remove '/yes'
                obj = self.caller.search(target, location=location)
                if not obj:
                    return

                # Verify the same conditions as above
                if obj.is_typeclass("typeclasses.rooms.Room"):
                    if obj == main_room:
                        self.caller.msg("You cannot destroy your main room. Use +home/vacate to remove your entire residence.")
                        return
                    if obj not in main_room.db.child_rooms:
                        self.caller.msg(f"{obj.get_display_name(self.caller)} is not part of your residence.")
                        return

                    # For rooms, use the helper method to destroy it
                    if self._destroy_room(obj, main_room):
                        self.caller.msg(f"{target} destroyed.")
                        
                elif obj.is_typeclass("typeclasses.exits.ApartmentExit"):
                    if not (obj.location == location or 
                           (obj.destination and obj.destination in main_room.db.child_rooms)):
                        self.caller.msg(f"{obj.get_display_name(self.caller)} is not part of your residence.")
                        return

                    # For exits, also delete the return exit if it exists
                    if obj.destination:
                        for exit in obj.destination.exits:
                            if exit.destination == obj.location:
                                exit.delete()
                    
                    # Delete the exit
                    obj.delete()
                    self.caller.msg(f"{target} destroyed.")

        elif "view" in self.switches:
            # Check if we're in a valid residence
            if not self.is_valid_residence(location):
                self.caller.msg("This command can only be used inside residences.")
                return

            # Check ownership
            if not self.is_owner(location, self.caller):
                self.caller.msg("You don't own this residence.")
                return

            # Initialize views dict if it doesn't exist
            if not hasattr(location.db, 'views') or location.db.views is None:
                location.db.views = {}

            # Handle setting a view
            if "set" in self.switches or "view/set" in self.switches:
                if not self.args or "=" not in self.args:
                    self.caller.msg("Usage: +home/view/set <viewname>=<text>")
                    return

                try:
                    viewname, text = self.args.split("=", 1)
                    viewname = viewname.strip()
                    text = text.strip()
                except ValueError:
                    self.caller.msg("Usage: +home/view/set <viewname>=<text>")
                    return

                # Additional validation
                if not viewname or not text:
                    self.caller.msg("You must provide both a view name and description.")
                    return

                location.db.views[viewname] = text
                self.caller.msg(f"Added view '{viewname}' to your residence.")
                return

            # Handle deleting a view
            elif "del" in self.switches or "view/del" in self.switches:
                if not self.args:
                    self.caller.msg("Usage: +home/view/del <viewname>")
                    return

                viewname = self.args.strip()
                if viewname in location.db.views:
                    del location.db.views[viewname]
                    self.caller.msg(f"Removed view '{viewname}' from your residence.")
                else:
                    self.caller.msg(f"No view named '{viewname}' found in your residence.")
                return

            # If no valid switch, show usage
            self.caller.msg("Usage: +home/view/set <viewname>=<text> or +home/view/del <viewname>")
            self.caller.msg("Use +view to look at views.")
            return

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
        sect:<name>       - Restrict to specific vampire sect
        affiliation:<name> - Restrict to specific affiliation
        convention:<name> - Restrict to specific convention
        kith:<name>       - Restrict to specific kith
        tradition:<name>  - Restrict to specific tradition
        nephandi_faction:<name> - Restrict to specific nephandi faction

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
        target = self.caller.search(self.lhs, location=self.caller.location, 
                                typeclass="typeclasses.exits.ApartmentExit")
        if not target:
            return
            
        # Validate lock type
        valid_locktypes = {
            'splat': 'db.splat',
            'talent': 'db.talents',
            'skill': 'db.skills',
            'knowledge': 'db.knowledges',
            'merit': 'db.merits',
            'type': 'db.type',
            'clan': 'db.clan',
            'tribe': 'db.tribe',
            'auspice': 'db.auspice',
            'tradition': 'db.tradition',
            'affiliation': 'db.affiliation',
            'convention': 'db.convention',
            'kith': 'db.kith',
            'tradition': 'db.tradition',
            'nephandi_faction': 'db.nephandi_faction',
            'sect': 'db.sect'
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


"""
Antiquated commands

class CmdSetApartmentDesc(MuxCommand):

    #Set the description of your residence or its rooms.
    
    #Usage:
    #    +adesc              - Show current room description
    #    +adesc <text>       - Set description for current room
    #    +adesc/room <num> = <text>  - Set description for specific room
        
    #Example:
    #    +adesc This cozy studio has been decorated with vintage posters.
    #    +adesc/room 2 = This bedroom features a comfortable queen-sized bed.
    
    key = "+adesc"
    aliases = ["+rdesc"]  # Added alias for residences
    locks = "cmd:all()"
    help_category = "Building and Housing"
    
    def func(self):
        location = self.caller.location
        
        # Check if we're in a residence
        if not (location.db.roomtype in ["apartment", "house", "apartment_room", "shifter_room", 
                                       "mage_room", "vampire_room", "possessed_room", "mortal_room", 
                                       "motel_room", "mortal+_room", "changeling_room"] or
                "Room" in location.db.roomtype):  # This catches "Mage Room", "Vampire Room", etc.
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

    #Modify exits in your residence.
    
    #Usage:
    #    +aexit <exit> = <new name>           - Rename an exit
    #    +aexit/alias <exit> = <alias>        - Add an alias to an exit
    #    +aexit/clear <exit>                  - Clear all aliases from an exit
    #    +aexit/remove <exit> = <alias>       - Remove specific alias from an exit
        
    #Example:
    #    +aexit Room 2 = Bedroom
    #    +aexit/alias Bedroom = bed
    #    +aexit/clear Bedroom
    #    +aexit/remove Bedroom = bed

    
    key = "+aexit"
    aliases = ["+rexit"]  # Added alias for residences
    locks = "cmd:all()"
    help_category = "Housing"
    
    def func(self):
        location = self.caller.location
        
        # Check if we're in a residence
        if location.db.roomtype not in ["apartment", "house", "apartment_room", "shifter_room", 
                                        "mage_room", "vampire_room", "possessed_room", 
                                        "mortal_room", "motel_room", "mortal+_room", 
                                        "changeling_room"]:
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

class CmdCoOwner(MuxCommand):

    Manage co-owners of your residence.
    
    Usage:
        +coowner                    - List current co-owners
        +coowner <player>          - Add a co-owner
        +coowner/remove <player>   - Remove a co-owner
        
    Co-owners have the same access rights as the owner, including:
    - Can enter when locked
    - Can modify room descriptions
    - Can give out and revoke keys
    - Can lock/unlock the residence
    
    You cannot remove the primary owner using this command.

    
    key = "+coowner"
    aliases = ["@coowner"]
    locks = "cmd:all()"
    help_category = "Housing"
    
    def func(self):
        location = self.caller.location
        
        # First check if we're in a valid residence
        if not location.is_valid_residence():
            self.caller.msg("This command can only be used inside residences.")
            return
            
        # Check ownership
        if not location.db.home_data or location.db.home_data.get('owner') != self.caller:
            self.caller.msg("You don't own this residence.")
            return
            
        # Initialize co-owners set if it doesn't exist
        if 'co_owners' not in location.db.home_data:
            location.db.home_data['co_owners'] = set()
            
        # List co-owners if no arguments
        if not self.args:
            co_owners = location.db.home_data['co_owners']
            if not co_owners:
                self.caller.msg("This residence has no co-owners.")
                return
                
            co_owner_names = []
            for co_owner_id in co_owners:
                char = self.caller.search(f"#{co_owner_id}")
                if char:
                    co_owner_names.append(char.name)
            
            if co_owner_names:
                self.caller.msg("Current co-owners:")
                self.caller.msg("\n".join(f"- {name}" for name in co_owner_names))
            else:
                self.caller.msg("This residence has no valid co-owners.")
            return
            
        # Handle removal
        if "remove" in self.switches:
            # Find the target player
            target = self.caller.search(self.args)
            if not target:
                return
                
            if target.id not in location.db.home_data['co_owners']:
                self.caller.msg(f"{target.name} is not a co-owner of this residence.")
                return
                
            location.db.home_data['co_owners'].remove(target.id)
            self.caller.msg(f"Removed {target.name} as a co-owner.")
            if target.has_account:
                target.msg(f"{self.caller.name} has removed you as a co-owner of their residence.")
            return
            
        # Add new co-owner
        target = self.caller.search(self.args)
        if not target:
            return
            
        # Don't allow adding self as co-owner
        if target == self.caller:
            self.caller.msg("You are already the owner of this residence.")
            return
            
        # Don't allow adding someone who is already a co-owner
        if target.id in location.db.home_data['co_owners']:
            self.caller.msg(f"{target.name} is already a co-owner of this residence.")
            return
            
        location.db.home_data['co_owners'].add(target.id)
        self.caller.msg(f"Added {target.name} as a co-owner.")
        if target.has_account:
            target.msg(f"{self.caller.name} has made you a co-owner of their residence at {location.get_display_name(target)}.")

class CmdUpdateApartments(MuxCommand):

    Update apartment exits to use the new system.
    
    Usage:
        +updateapts            - Update all apartment exits
        +updateapts <room>    - Update exits for specific apartment
        
    This command converts existing apartment exits to use the ApartmentExit
    typeclass and updates their permissions.

    
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

    
    key = "+apartments"
    aliases = ["@apartments"]
    locks = "cmd:perm(builders)"
    help_category = "Building and Housing"
    
    def func(self):
        from evennia.objects.models import ObjectDB
        from evennia.accounts.models import AccountDB
        
        def format_apartment(apt):
            #Helper to format apartment info
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

class CmdSetHousing(MuxCommand):
    Set up a room as a housing area.
    
    Usage:
        +sethousing/apartment <resources> [max_units]  - Set as apartment building
        +sethousing/motel <resources> [max_units]      - Set as motel
        +sethousing/residential <resources> [max_units] - Set as residential area
        +sethousing/clear                              - Clear housing settings
        
    The resources value determines the base cost for units in this building.
    Higher resources mean more expensive/luxurious accommodations.
        
    Example:
        +sethousing/apartment 2 20    - Set up as apartment building with resource 2, 20 units
        +sethousing/residential 3 10  - Set up as residential area with resource 3, 10 houses
        
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
            
        elif "motel" in self.switches:
            location.setup_housing("Motel", max_units)
            location.db.resources = resources
            self.caller.msg(f"Set up room as motel with {resources} resources and {max_units} maximum units.")
            
        elif "residential" in self.switches:
            location.setup_housing("Residential Area", max_units)
            location.db.resources = resources
            self.caller.msg(f"Set up room as residential area with {resources} resources and {max_units} maximum units.") 


class CmdSetAllowedSplats(MuxCommand):
    #Set which splats are allowed to rent in a housing area.
    
    #Usage:
    #    +allowedsplats <splat1>,<splat2>,...  - Set allowed splats
    #    +allowedsplats/add <splat>            - Add a splat to allowed list
    #    +allowedsplats/remove <splat>         - Remove a splat from allowed list
    #    +allowedsplats/clear                  - Clear all allowed splats
    #    +allowedsplats/show                   - Show current allowed splats
        
    #Examples:
    #    +allowedsplats Mage,Vampire,Changeling,Possessed
    #    +allowedsplats/add Shifter
    #    +allowedsplats/remove Vampire
    #    +allowedsplats/clear
    #    +allowedsplats/show
    
    key = "+allowedsplats"
    aliases = ["+setsplats"]
    locks = "cmd:perm(builders)"
    help_category = "Building and Housing"
    
    # Valid splat types
    VALID_SPLATS = [
        "Mage", "Vampire", "Werewolf", "Changeling", "Mortal+",
        "Shifter", "Possessed", "Companion"
    ]
    
    def func(self):
        location = self.caller.location
        
        # Initialize allowed_splats if it doesn't exist
        if not hasattr(location.db, 'allowed_splats'):
            location.db.allowed_splats = []
            
        if "show" in self.switches or not self.args:
            if location.db.allowed_splats:
                self.caller.msg(f"Allowed splats in this area: {', '.join(location.db.allowed_splats)}")
            else:
                self.caller.msg("No splats are currently allowed in this area.")
            return
            
        if "clear" in self.switches:
            location.db.allowed_splats = []
            self.caller.msg("Cleared all allowed splats from this area.")
            return
            
        if "add" in self.switches:
            splat = self.args.strip()
            if splat not in self.VALID_SPLATS:
                self.caller.msg(f"Invalid splat type. Valid types: {', '.join(self.VALID_SPLATS)}")
                return
                
            if splat not in location.db.allowed_splats:
                location.db.allowed_splats.append(splat)
                self.caller.msg(f"Added {splat} to allowed splats.")
            return
            
        if "remove" in self.switches:
            splat = self.args.strip()
            if splat in location.db.allowed_splats:
                location.db.allowed_splats.remove(splat)
                self.caller.msg(f"Removed {splat} from allowed splats.")
            else:
                self.caller.msg(f"{splat} is not in the allowed splats list.")
            return
            
        # No switch - set entire list
        splats = [s.strip() for s in self.args.split(',')]
        invalid_splats = [s for s in splats if s not in self.VALID_SPLATS]
        
        if invalid_splats:
            self.caller.msg(f"Invalid splat types: {', '.join(invalid_splats)}\nValid types: {', '.join(self.VALID_SPLATS)}")
            return
            
        location.db.allowed_splats = splats
        self.caller.msg(f"Set allowed splats to: {', '.join(splats)}")
"""