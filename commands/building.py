"""
Building commands for World of Darkness 20th Anniversary Edition
"""
from evennia import CmdSet
from evennia.commands.default.building import ObjManipCommand
from evennia import Command
from evennia.utils.evtable import EvTable
from evennia import CmdSet, Command, logger
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.eveditor import EvEditor

def _desc_load(caller):
    """Return the description."""
    return caller.db.evmenu_target.db.desc or ""

def _desc_save(caller, buf):
    """Save the description."""
    caller.db.evmenu_target.db.desc = buf
    caller.msg("Description saved.")
    return True

def _desc_quit(caller):
    """Called when the editor exits."""
    caller.msg("Exiting editor.")
    del caller.db.evmenu_target

class CmdSetRoomResources(ObjManipCommand):
    """
    Set the resources value for a room.

    Usage:
      +res [<room>] = <value>

    Sets the 'resources' attribute of a room to the specified integer value.
    If no room is specified, it sets the attribute for the current room.

    Example:
      +res = 4
      +res Temple of Doom = 5
    """

    key = "+res"
    locks = "cmd:perm(Builder)"
    help_category = "Building and Housing"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: +res [<room>] = <value>")
            return

        if self.rhs is None:
            self.caller.msg("You must specify a value. Usage: +res [<room>] = <value>")
            return

        try:
            value = int(self.rhs)
        except ValueError:
            self.caller.msg("The resources value must be an integer.")
            return

        if self.lhs:
            obj = self.caller.search(self.lhs, global_search=True)
        else:
            obj = self.caller.location

        if not obj:
            return

        if not obj.is_typeclass("typeclasses.rooms.RoomParent"):
            self.caller.msg("You can only set resources on rooms.")
            return

        obj.db.resources = value
        self.caller.msg(f"Set resources to {value} for {obj.get_display_name(self.caller)}.")

class CmdSetRoomType(ObjManipCommand):
    """
    Set the room type for a room.

    Usage:
      +roomtype [<room>] = <type>

    Sets the 'roomtype' attribute of a room to the specified string value.
    If no room is specified, it sets the attribute for the current room.

    Example:
      +roomtype = Beach Town
      +roomtype Evil Lair = Villain Hideout
    """

    key = "+roomtype"
    locks = "cmd:perm(Builder)"
    help_category = "Building and Housing"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: +roomtype [<room>] = <type>")
            return

        if self.rhs is None:
            self.caller.msg("You must specify a room type. Usage: +roomtype [<room>] = <type>")
            return

        if self.lhs:
            obj = self.caller.search(self.lhs, global_search=True)
        else:
            obj = self.caller.location

        if not obj:
            return

        if not obj.is_typeclass("typeclasses.rooms.RoomParent"):
            self.caller.msg("You can only set room types on rooms.")
            return

        obj.db.roomtype = self.rhs
        self.caller.msg(f"Set room type to '{self.rhs}' for {obj.get_display_name(self.caller)}.")

class CmdSetUmbraDesc(Command):
    """
    Set the Umbra description for a room.

    Usage:
      @umbradesc <description>

    This command sets the Umbra description for the current room.
    The description will be shown when characters peek into or
    enter the Umbra version of this room.
    """

    key = "@umbradesc"
    locks = "cmd:perm(Builders)"
    help_category = "Building and Housing"

    def func(self):
        """Execute command."""
        caller = self.caller
        location = caller.location

        if not self.args:
            caller.msg("Usage: @umbradesc <description>")
            return

        # Preserve exact formatting by not stripping
        location.db.umbra_desc = self.args
        caller.msg(f"Umbra description set for {location.get_display_name(caller)}.")

class CmdSetGauntlet(Command):
    """
    Set the Gauntlet rating for a room.

    Usage:
      @setgauntlet <rating>

    This command sets the Gauntlet rating for the current room.
    The rating should be a number, typically between 3 and 9.
    This affects the difficulty of peeking into or entering the Umbra.
    """

    key = "@setgauntlet"
    locks = "cmd:perm(Builders)"
    help_category = "Building and Housing"

    def func(self):
        """Execute command."""
        caller = self.caller
        location = caller.location

        if not self.args:
            caller.msg("Usage: @setgauntlet <rating>")
            return

        try:
            rating = int(self.args)
            if 1 <= rating <= 10:
                location.db.gauntlet_difficulty = rating
                caller.msg(f"Gauntlet rating for {location.get_display_name(caller)} set to {rating}.")
            else:
                caller.msg("The Gauntlet rating should be between 1 and 10.")
        except ValueError:
            caller.msg("Please provide a valid number for the Gauntlet rating.")

class CmdUmbraInfo(Command):
    """
    Display Umbra-related information for a room.

    Usage:
      @umbrainfo

    This command shows the current Umbra description and Gauntlet
    rating for the current room.
    """

    key = "@umbrainfo"
    locks = "cmd:perm(Builders)"
    help_category = "Building and Housing"

    def func(self):
        """Execute command."""
        caller = self.caller
        location = caller.location

        umbra_desc = location.db.umbra_desc or "Not set"
        gauntlet_rating = location.db.gauntlet_difficulty or "Default (6)"

        table = EvTable(border="table")
        table.add_row("|wRoom|n", location.get_display_name(caller))
        table.add_row("|wUmbra Description|n", umbra_desc)
        table.add_row("|wGauntlet Rating|n", gauntlet_rating)

        caller.msg(table)

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
    
    def initialize_housing_data(self, location):
        """Helper method to initialize housing data"""
        if not hasattr(location.db, 'housing_data') or not location.db.housing_data:
            location.db.housing_data = {
                'is_housing': False,
                'max_apartments': 0,
                'current_tenants': {},
                'apartment_numbers': set(),
                'required_resources': 0,
                'building_zone': None,
                'connected_rooms': set(),
                'is_lobby': False,
                'available_types': []
            }
        return location.db.housing_data

    def find_lobby(self, location):
        """Helper method to find the connected lobby"""
        # First check if this room is a lobby
        if location.db.housing_data and location.db.housing_data.get('is_lobby'):
            return location
            
        # Then check all connected exits
        for exit in location.exits:
            if not exit.destination:
                continue
                
            # Check if this exit leads to lobby (by name or alias)
            exit_names = [exit.key.lower()]
            if exit.aliases:
                exit_names.extend([alias.lower() for alias in exit.aliases.all()])
            
            if any(name in ['lobby', 'l'] for name in exit_names):
                dest = exit.destination
                if (hasattr(dest, 'db') and 
                    hasattr(dest.db, 'housing_data') and 
                    dest.db.housing_data and 
                    dest.db.housing_data.get('is_lobby')):
                    return dest
                    
            # Check the destination directly
            dest = exit.destination
            if (hasattr(dest, 'db') and 
                hasattr(dest.db, 'housing_data') and 
                dest.db.housing_data and 
                dest.db.housing_data.get('is_lobby')):
                return dest
                
            # Also check if the destination has exits leading to a lobby
            if hasattr(dest, 'exits'):
                for other_exit in dest.exits:
                    if not other_exit.destination:
                        continue
                    
                    other_dest = other_exit.destination
                    if (hasattr(other_dest, 'db') and 
                        hasattr(other_dest.db, 'housing_data') and 
                        other_dest.db.housing_data and 
                        other_dest.db.housing_data.get('is_lobby')):
                        return other_dest
        
        return None

    def check_lobby_required(self, location, switch):
        """Check if command requires an active lobby setup"""
        # These commands can be used without a lobby
        if switch in ["setlobby", "clear", "info"]:
            return True
            
        # For other commands, check if this is a lobby or connected to one
        if location.db.housing_data.get('is_lobby'):
            return True
            
        # Try to find a connected lobby
        lobby = self.find_lobby(location)
        if lobby:
            return True
                
        self.caller.msg("You must set up this room as a lobby first using +manage/setlobby")
        return False

    def func(self):
        if not self.switches:
            self.caller.msg("Usage: +sethousing/<switch>")
            return
            
        switch = self.switches[0]
        location = self.caller.location
        
        # Store existing exits before modifying
        existing_exits = [
            (exit.key, exit.aliases.all(), exit.destination) 
            for exit in location.exits
        ]
        
        # Initialize housing data for all commands
        self.initialize_housing_data(location)

        # Check if command requires lobby setup
        if not self.check_lobby_required(location, switch):
            return

        if not self.switches or not any(switch in self.switches for switch in ["apartment", "condo", "residential"]):
            self.caller.msg("Please specify the type: /apartment, /condo, or /residential")
            return
            
        # Parse arguments
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
                
        except (ValueError, IndexError):
            self.caller.msg("Usage: +sethousing/<type> <resources> [max_units]")
            return
        
        # Restore exits after housing setup
        def restore_exits():
            from evennia import create_object
            from typeclasses.exits import Exit
            
            for exit_key, exit_aliases, exit_dest in existing_exits:
                if exit_dest:  # Only restore exits with a destination
                    new_exit = create_object(Exit, 
                                             key=exit_key, 
                                             location=location, 
                                             destination=exit_dest)
                    # Restore aliases
                    for alias in exit_aliases:
                        new_exit.aliases.add(alias)
        
        # Set up housing based on switch
        if "apartment" in self.switches:
            location.setup_housing("Apartment Building", max_units)
            location.db.resources = resources
            location.db.housing_data['max_apartments'] = max_units
            restore_exits()
            self.caller.msg(f"Set up room as apartment building with {resources} resources and {max_units} maximum units.")
            
        elif "condo" in self.switches:
            location.setup_housing("Condominiums", max_units)
            location.db.resources = resources
            location.db.housing_data['max_apartments'] = max_units
            restore_exits()
            self.caller.msg(f"Set up room as condominium with {resources} resources and {max_units} maximum units.")
            
        elif "residential" in self.switches:
            location.setup_housing("Residential Area", max_units)
            location.db.resources = resources
            location.db.housing_data['max_apartments'] = max_units
            restore_exits()
            self.caller.msg(f"Set up room as residential area with {resources} resources and {max_units} maximum units.")

class CmdManageBuilding(MuxCommand):
    """
    Manage apartment building zones.
    
    Usage:
        +manage/setlobby            - Sets current room as building lobby
        +manage/addroom            - Adds current room to building zone
        +manage/removeroom         - Removes current room from building zone
        +manage/info               - Shows building zone information
        +manage/clear              - Clears all building zone data
        +manage/types             - Lists available apartment types
        +manage/addtype <type>    - Add an apartment type to this building
        +manage/remtype <type>    - Remove an apartment type from this building
        
    Example:
        +manage/setlobby
        +manage/addtype Studio
        +manage/addtype "Two-Bedroom"
    """
    
    key = "+manage"
    locks = "cmd:perm(builders)"
    help_category = "Building and Housing"
    
    def initialize_housing_data(self, location):
        """Helper method to initialize housing data"""
        if not hasattr(location.db, 'housing_data') or not location.db.housing_data:
            location.db.housing_data = {
                'is_housing': False,
                'max_apartments': 0,
                'current_tenants': {},
                'apartment_numbers': set(),
                'required_resources': 0,
                'building_zone': None,
                'connected_rooms': set(),
                'is_lobby': False,
                'available_types': []
            }
        return location.db.housing_data

    def find_lobby(self, location):
        """Helper method to find the connected lobby"""
        # First check if this room is a lobby
        if location.db.housing_data and location.db.housing_data.get('is_lobby'):
            return location
            
        # Then check all connected exits
        for exit in location.exits:
            if not exit.destination:
                continue
                
            # Check if this exit leads to lobby (by name or alias)
            exit_names = [exit.key.lower()]
            if exit.aliases:
                exit_names.extend([alias.lower() for alias in exit.aliases.all()])
            
            if any(name in ['lobby', 'l'] for name in exit_names):
                dest = exit.destination
                if (hasattr(dest, 'db') and 
                    hasattr(dest.db, 'housing_data') and 
                    dest.db.housing_data and 
                    dest.db.housing_data.get('is_lobby')):
                    return dest
                    
            # Check the destination directly
            dest = exit.destination
            if (hasattr(dest, 'db') and 
                hasattr(dest.db, 'housing_data') and 
                dest.db.housing_data and 
                dest.db.housing_data.get('is_lobby')):
                return dest
                
            # Also check if the destination has exits leading to a lobby
            if hasattr(dest, 'exits'):
                for other_exit in dest.exits:
                    if not other_exit.destination:
                        continue
                    
                    other_dest = other_exit.destination
                    if (hasattr(other_dest, 'db') and 
                        hasattr(other_dest.db, 'housing_data') and 
                        other_dest.db.housing_data and 
                        other_dest.db.housing_data.get('is_lobby')):
                        return other_dest
        
        return None

    def check_lobby_required(self, location, switch):
        """Check if command requires an active lobby setup"""
        # These commands can be used without a lobby
        if switch in ["setlobby", "clear", "info"]:
            return True
            
        # For other commands, check if this is a lobby or connected to one
        if location.db.housing_data.get('is_lobby'):
            return True
            
        # Try to find a connected lobby
        lobby = self.find_lobby(location)
        if lobby:
            return True
                
        self.caller.msg("You must set up this room as a lobby first using +manage/setlobby")
        return False

    def func(self):
        if not self.switches:
            self.caller.msg("Usage: +manage/<switch>")
            return
            
        switch = self.switches[0]
        location = self.caller.location
        
        # Initialize housing data for all commands
        self.initialize_housing_data(location)

        # Check if command requires lobby setup
        if not self.check_lobby_required(location, switch):
            return

        if switch == "types":
            try:
                # Show available apartment types from CmdRent
                from commands.housing import CmdRent
                table = EvTable(
                    "|wType|n",
                    "|wRooms|n",
                    "|wModifier|n",
                    "|wDescription|n",
                    border="table",
                    table_width=78
                )
                
                # Configure column widths
                table.reformat_column(0, width=12)  # Type
                table.reformat_column(1, width=7)   # Rooms
                table.reformat_column(2, width=10)  # Modifier
                table.reformat_column(3, width=45)  # Description
                
                # Show apartment types
                for apt_type, data in CmdRent.APARTMENT_TYPES.items():
                    table.add_row(
                        apt_type,
                        str(data['rooms']),
                        str(data['resource_modifier']),
                        data['desc']
                    )
                
                # Show residential types
                for res_type, data in CmdRent.RESIDENTIAL_TYPES.items():
                    table.add_row(
                        res_type,
                        str(data['rooms']),
                        str(data['resource_modifier']),
                        data['desc']
                    )
                
                self.caller.msg(table)
                
                if location.db.housing_data.get('available_types', []):
                    self.caller.msg("\nTypes available in this building:")
                    available = location.db.housing_data['available_types']
                    # Wrap the available types list
                    from textwrap import wrap
                    wrapped = wrap(", ".join(available), width=76)  # 76 to account for margins
                    for line in wrapped:
                        self.caller.msg(line)
            except Exception as e:
                self.caller.msg("Error displaying housing types. Please contact an admin.")
                
        elif switch == "addtype":
            if not self.args:
                self.caller.msg("Usage: +manage/addtype <type>")
                return
                
            try:
                from commands.housing import CmdRent
                apt_type = self.args.strip()
                if apt_type not in CmdRent.APARTMENT_TYPES and apt_type not in CmdRent.RESIDENTIAL_TYPES:
                    self.caller.msg(f"Invalid type. Use +manage/types to see available types.")
                    return
                    
                if 'available_types' not in location.db.housing_data:
                    location.db.housing_data['available_types'] = []
                    
                if apt_type not in location.db.housing_data['available_types']:
                    location.db.housing_data['available_types'].append(apt_type)
                    self.caller.msg(f"Added {apt_type} to available types.")
                else:
                    self.caller.msg(f"{apt_type} is already available in this building.")
            except Exception as e:
                self.caller.msg("Error adding housing type. Please contact an admin.")

        elif switch == "setlobby":
            # Set this room as the lobby
            location.db.housing_data['is_lobby'] = True
            location.db.housing_data['building_zone'] = location.dbref
            if 'connected_rooms' not in location.db.housing_data:
                location.db.housing_data['connected_rooms'] = set()
            location.db.housing_data['connected_rooms'].add(location.dbref)
            
            # Ensure room type and max_apartments are set
            if not location.db.roomtype or location.db.roomtype == "Unknown":
                location.db.roomtype = "Apartment Building"
                location.db.housing_data['max_apartments'] = 20  # Default value if not set
            
            # Ensure max_apartments exists
            if 'max_apartments' not in location.db.housing_data:
                location.db.housing_data['max_apartments'] = 20  # Default value
            
            self.caller.msg(f"Set {location.get_display_name(self.caller)} as building lobby.")
            
        elif switch == "addroom":
            # Find the lobby this room should connect to
            lobby = self.find_lobby(location)
                    
            if not lobby:
                self.caller.msg("Could not find a lobby connected to this room.")
                return
            
            # Initialize housing data for this room if needed
            self.initialize_housing_data(location)
            
            # Copy relevant data from lobby
            location.db.roomtype = lobby.db.roomtype
            location.db.resources = lobby.db.resources
            
            # Add this room to the building zone
            location.db.housing_data.update({
                'building_zone': lobby.dbref,
                'is_housing': True,
                'max_apartments': lobby.db.housing_data.get('max_apartments', 20),
                'available_types': lobby.db.housing_data.get('available_types', [])
            })
            
            # Update lobby's connected rooms
            if 'connected_rooms' not in lobby.db.housing_data:
                lobby.db.housing_data['connected_rooms'] = set()
            lobby.db.housing_data['connected_rooms'].add(location.dbref)
            
            self.caller.msg(f"Added {location.get_display_name(self.caller)} to building zone.")
            
        elif switch == "removeroom":
            if not location.db.housing_data.get('building_zone'):
                self.caller.msg("This room is not part of a building zone.")
                return
                
            # Get the lobby
            lobby = self.caller.search(location.db.housing_data['building_zone'])
            
            if lobby and 'connected_rooms' in lobby.db.housing_data and location.dbref in lobby.db.housing_data['connected_rooms']:
                lobby.db.housing_data['connected_rooms'].remove(location.dbref)
                
            # Reset room data
            location.db.housing_data['building_zone'] = None
            location.db.housing_data['is_housing'] = False
            location.db.roomtype = "Room"
            location.db.resources = 0
            
            self.caller.msg(f"Removed {location.get_display_name(self.caller)} from building zone.")
            
        elif switch == "info":
            if location.db.housing_data.get('is_lobby'):
                if 'connected_rooms' not in location.db.housing_data:
                    location.db.housing_data['connected_rooms'] = set()
                    
                connected = location.db.housing_data['connected_rooms']
                rooms = []
                for room_dbref in connected:
                    room = self.caller.search(room_dbref)
                    if room and room != location:
                        rooms.append(room)
                
                table = EvTable(border="table")
                table.add_row("|wBuilding Lobby|n", location.get_display_name(self.caller))
                if rooms:
                    table.add_row("|wConnected Rooms|n", "\n".join(r.get_display_name(self.caller) for r in rooms))
                else:
                    table.add_row("|wConnected Rooms|n", "None")
                table.add_row("|wMax Units|n", location.db.housing_data.get('max_apartments', 0))
                table.add_row("|wResources|n", location.db.resources)
                table.add_row("|wAvailable Types|n", ", ".join(location.db.housing_data.get('available_types', [])))
                
                self.caller.msg(table)
            else:
                lobby_dbref = location.db.housing_data.get('building_zone')
                if lobby_dbref:
                    lobby = self.caller.search(lobby_dbref)
                    if lobby:
                        self.caller.msg(f"This room is part of {lobby.get_display_name(self.caller)}'s building zone.")
                    else:
                        self.caller.msg("Error: Building lobby not found.")
                else:
                    self.caller.msg("This room is not part of any building zone.")
                    
        elif switch == "clear":
            if location.db.housing_data.get('is_lobby'):
                # Clear all connected rooms
                if 'connected_rooms' in location.db.housing_data:
                    for dbref in location.db.housing_data['connected_rooms']:
                        room = self.caller.search(dbref)
                        if room:
                            room.db.housing_data['building_zone'] = None
                            room.db.housing_data['is_housing'] = False
                            room.db.roomtype = "Room"
                            room.db.resources = 0
                            
            # Reset housing data
            self.initialize_housing_data(location)
            location.db.roomtype = "Room"
            location.db.resources = 0
            self.caller.msg("Cleared building zone data.")

class CmdSetLock(MuxCommand):
    """
    Set various types of locks on an exit or room.
    
    Usage:
        +setlock <target>=<locktype>:<value>[,<locktype>:<value>...]
        +setlock/view <target>=<locktype>:<value>[,<locktype>:<value>...]
        +setlock/list <target>          - List current locks
        +setlock/clear <target>         - Clear all locks
        
    Lock Types:
        splat:<type>      - Restrict to specific splat (Vampire, Werewolf, etc)
        type:<type>       - Restrict to specific type (Garou, Kinfolk, Familiar, Fomori, etc)
        talent:<name>     - Require specific talent
        skill:<name>      - Require specific skill
        knowledge:<name>  - Require specific knowledge
        merit:<name>      - Require specific merit
        clan:<name>       - Restrict to specific vampire clan
        tribe:<name>      - Restrict to specific werewolf tribe
        auspice:<name>    - Restrict to specific werewolf auspice
        tradition:<name>  - Restrict to specific mage tradition
        affiliation:<name> - Restrict to specific mage faction
        convention:<name> - Restrict to specific Technocratic convention
        nephandi_faction:<name> - Restrict to specific Nephandi faction
        court:<name>      - Restrict to specific changeling court
        kith:<name>       - Restrict to specific changeling kith
        wyrm:<on/off>     - Restrict based on wyrm taint status

    Examples:
        +setlock door=type:Garou                    - Only Garou can pass
        +setlock door=type:Garou,type:Kinfolk      - Both Garou AND Kinfolk must pass
        +setlock door=type:Garou;type:Kinfolk      - Either Garou OR Kinfolk can pass
        +setlock/view door=type:Garou;type:Kinfolk - Either Garou OR Kinfolk can view
        +setlock door=wyrm:on                       - Only wyrm-tainted beings can pass
    """
    
    key = "+setlock"
    aliases = ["+lock", "+locks", "+setlocks"]
    locks = "cmd:perm(builders)"
    help_category = "Building and Housing"
    
    def format_lock_table(self, target):
        """Helper method to format lock table consistently"""
        table = EvTable("|wLock Type|n", "|wDefinition|n", border="table")
        for lockstring in target.locks.all():
            try:
                locktype, definition = lockstring.split(":", 1)
                table.add_row(locktype, definition)
            except ValueError:
                table.add_row("unknown", lockstring)
        return table
    
    def func(self):
        # Handle clear switch first
        if "clear" in self.switches:
            if not self.args:
                self.caller.msg("Usage: +setlock/clear <target>")
                return
                
            target = self.caller.search(self.args, location=self.caller.location)
            if not target:
                return
                
            # Clear all locks
            target.locks.clear()
            
            # Re-add basic locks for exits
            if target.is_typeclass("typeclasses.exits.Exit") or target.is_typeclass("typeclasses.exits.ApartmentExit"):
                # Add standard exit locks
                standard_locks = {
                    "call": "true()",
                    "control": "id(1) or perm(Admin)",
                    "delete": "id(1) or perm(Admin)",
                    "drop": "holds()",
                    "edit": "id(1) or perm(Admin)",
                    "examine": "perm(Builder)",
                    "get": "false()",
                    "puppet": "false()",
                    "teleport": "false()",
                    "teleport_here": "false()",
                    "tell": "perm(Admin)",
                    "traverse": "all()"
                }
                
                for lock_type, lock_def in standard_locks.items():
                    target.locks.add(f"{lock_type}:{lock_def}")
            
            self.caller.msg(f"Cleared all locks from {target.get_display_name(self.caller)}.")
            return

        # Validate base arguments
        if not self.args:
            self.caller.msg("Usage: +setlock <target>=<locktype>:<value>[,<locktype>:<value>...]")
            return
            
        # Handle list switch
        if "list" in self.switches:
            target = self.caller.search(self.lhs, location=self.caller.location)
            if not target:
                return
                
            if not target.locks.all():
                self.caller.msg(f"No locks set on {target.get_display_name(self.caller)}.")
                return
                
            table = self.format_lock_table(target)
            self.caller.msg(f"Locks on {target.get_display_name(self.caller)}:")
            self.caller.msg(table)
            return

        # Validate lock definition
        if not self.rhs:
            self.caller.msg("Usage: +setlock <target>=<locktype>:<value>[,<locktype>:<value>...]")
            return
            
        target = self.caller.search(self.lhs, location=self.caller.location)
        if not target:
            return
            
        # Split OR conditions first (separated by ;)
        or_parts = self.rhs.split(';')
        or_lock_defs = []
        
        for or_part in or_parts:
            # Split AND conditions (separated by ,)
            and_parts = or_part.split(',')
            and_lock_defs = []
            
            for lock_part in and_parts:
                try:
                    locktype, value = lock_part.strip().split(':', 1)
                    locktype = locktype.strip().lower()
                    value = value.strip().lower()
                    
                    # Create the appropriate lock string based on type
                    if locktype == "splat":
                        lock_str = f'has_splat({value.strip()})'
                    elif locktype == "type":
                        lock_str = f'has_type({value.strip()})'
                    elif locktype == "wyrm":
                        if value not in ("on", "off"):
                            self.caller.msg("Wyrm lock value must be either 'on' or 'off'.")
                            return
                        lock_str = f'has_wyrm_taint()' if value == "on" else f'not has_wyrm_taint()'
                    elif locktype in ["talent", "skill", "knowledge", "secondary_talent", "secondary_skill", "secondary_knowledge"]:
                        if ">" in value:
                            ability, level = value.split(">")
                            lock_str = f"has_{locktype}({ability.strip()}, {level.strip()})"
                        else:
                            lock_str = f"has_{locktype}({value.strip()})"
                    elif locktype == "merit":
                        if ">" in value:
                            merit, level = value.split(">")
                            lock_str = f'has_merit({merit.strip()}, {level.strip()})'
                        else:
                            lock_str = f'has_merit({value.strip()})'
                    elif locktype in ["clan", "tribe", "auspice", "tradition", "convention","affiliation", "kith", "court"]:
                        lock_str = f'has_{locktype}({value.strip()})'
                    else:
                        self.caller.msg(f"Invalid lock type.")
                        return
                        
                    and_lock_defs.append(lock_str)
                    
                except ValueError:
                    self.caller.msg(f"Invalid lock format: {lock_part}")
                    return
            
            # Combine AND conditions
            if and_lock_defs:
                or_lock_defs.append(" and ".join(and_lock_defs))
        
        # Combine OR conditions
        final_lock_def = " or ".join(or_lock_defs)
        
        try:
            if target.is_typeclass("typeclasses.exits.Exit") or target.is_typeclass("typeclasses.exits.ApartmentExit"):
                # Get all current locks
                current_locks = []
                for lockstring in target.locks.all():
                    try:
                        lock_type, definition = lockstring.split(":", 1)
                        if lock_type != ("traverse" if "view" not in self.switches else "view"):
                            current_locks.append((lock_type, definition))
                    except ValueError:
                        continue
                
                # Clear and restore locks
                target.locks.clear()
                for lock_type, lock_def in current_locks:
                    target.locks.add(f"{lock_type}:{lock_def}")
                    
                # Add standard exit locks
                standard_locks = {
                    "call": "true()",
                    "control": "id(1) or perm(Admin)",
                    "delete": "id(1) or perm(Admin)",
                    "drop": "holds()",
                    "edit": "id(1) or perm(Admin)",
                    "examine": "perm(Builder)",
                    "get": "false()",
                    "puppet": "false()",
                    "teleport": "false()",
                    "teleport_here": "false()",
                    "tell": "perm(Admin)",
                }
                
                for lock_type, lock_def in standard_locks.items():
                    if not any(l.startswith(f"{lock_type}:") for l in target.locks.all()):
                        target.locks.add(f"{lock_type}:{lock_def}")
                
                # Add new lock
                lock_type = "view" if "view" in self.switches else "traverse"
                target.locks.add(f"{lock_type}:{final_lock_def}")
                target.locks.cache_lock_bypass(target)
                
                self.caller.msg(f"Added {lock_type} lock to {target.get_display_name(self.caller)}.")
            else:
                target.locks.add(f"view:{final_lock_def}")
                self.caller.msg(f"Added view lock to {target.get_display_name(self.caller)}.")
            
        except Exception as e:
            self.caller.msg(f"Error setting lock: {str(e)}")

class CmdDesc(MuxCommand):
    """
    describe yourself or another object

    Usage:
      @desc <description>
      @desc me=<description>
      @desc here=<description>
      @desc <obj> = <description>
      @desc/edit [<obj>]        - Edit description in a line editor

    Sets the "desc" attribute on an object. If no object is given,
    describe yourself. You can always describe yourself, but need
    appropriate permissions to describe other objects.

    Special characters:
      %r or %R - New line
      %t or %T - Tab
    """

    key = "@desc"
    aliases = ["@desc/edit", "desc", "@describe", "describe"]
    switch_options = ("edit",)
    locks = "cmd:all()" 
    help_category = "Building and Housing"
    account_caller = True  # This ensures it works at account level

    def parse(self):
        """
        Handle parsing of the command
        """
        super().parse()
        self.target_is_self = False
        if self.args:
            if self.lhs and self.lhs.lower() in ["me", "here"]:
                self.target_is_self = True
            elif not "=" in self.args:
                self.target_is_self = True

    def access(self, srcobj, access_type="cmd", default=False):
        """
        Override the access check. Allow if:
        1) They have general command access (cmd:all())
        2) They are trying to describe themselves
        """
        if access_type != "cmd":
            return super().access(srcobj, access_type, default)
            
        # Always allow access - we'll do specific permission checks in func()
        return True

    def edit_handler(self):
        if self.rhs:
            self.msg("|rYou may specify a value, or use the edit switch, but not both.|n")
            return

        # Get the current puppet
        puppet = None
        if self.session:
            puppet = self.caller.get_puppet(self.session)
        if not puppet:
            puppet = self.caller.puppet

        if not puppet:
            self.caller.msg("You must have a character puppet to edit descriptions.")
            return

        if self.args:
            obj = self.caller.search(self.args)
        else:
            obj = puppet.location or self.msg("|rYou can't describe oblivion.|n")
        if not obj:
            return

        # Check if object is a room - require builder permissions
        if obj.is_typeclass("typeclasses.rooms.Room") or obj.is_typeclass("typeclasses.rooms.RoomParent"):
            if not self.caller.check_permstring("Builder"):
                self.msg("You must be a Builder or higher to edit room descriptions.")
                return

        if not (obj.access(self.caller, "control") or obj.access(self.caller, "edit")):
            self.msg(f"You don't have permission to edit the description of {obj.key}.")
            return

        self.caller.db.evmenu_target = obj
        # launch the editor
        EvEditor(
            self.caller,
            loadfunc=_desc_load,
            savefunc=_desc_save,
            quitfunc=_desc_quit,
            key="desc",
            persistent=True,
        )
        return

    def func(self):
        """Define command"""
        caller = self.caller
        
        if not self.args and "edit" not in self.switches:
            caller.msg("Usage: @desc [<obj> =] <description>")
            return

        if "edit" in self.switches:
            self.edit_handler()
            return

        # Get the current puppet
        puppet = None
        if self.session:
            puppet = caller.get_puppet(self.session)
        if not puppet:
            puppet = caller.puppet

        if not puppet:
            caller.msg("You must have a character puppet to set descriptions.")
            return

        if "=" in self.args:
            # We have an =
            obj_name = self.lhs.strip().lower()
            # Handle special keywords
            if obj_name == "me":
                if puppet:
                    obj = puppet
                else:
                    caller.msg("You must have a character puppet to set its description.")
                    return
            elif obj_name == "here":
                obj = puppet.location
                if not obj:
                    caller.msg("You don't have a location to describe.")
                    return
            else:
                obj = caller.search(self.lhs)
            if not obj:
                return
            desc = self.rhs or ""
        else:
            # No = means we're trying to desc ourselves
            if puppet:
                obj = puppet
            else:
                caller.msg("You must have a character puppet to set its description.")
                return
            desc = self.args
            
        # Process special characters
        desc = desc.replace("%r", "\n").replace("%R", "\n")
        desc = desc.replace("%t", "\t").replace("%T", "\t")
            
        # Check if object is a room - require builder permissions
        if obj.is_typeclass("typeclasses.rooms.Room") or obj.is_typeclass("typeclasses.rooms.RoomParent"):
            if not caller.check_permstring("Builder"):
                caller.msg("You must be a Builder or higher to edit room descriptions.")
                return
            # If they are a builder, allow them to edit the room
            obj.db.desc = desc
            caller.msg(f"The description was set on {obj.get_display_name(caller)}.")
            return
                
        # For non-room objects, use standard permission checks
        if obj == puppet or obj.access(caller, "control") or obj.access(caller, "edit"):
            obj.db.desc = desc
            caller.msg(f"The description was set on {obj.get_display_name(caller)}.")
        else:
            caller.msg(f"You don't have permission to edit the description of {obj.key}.")

class CmdView(MuxCommand):
    """
    View additional details about objects, rooms, and characters.

    Usage:
      +view                           - List all views in current location
      +view <target>                 - List all views on a specific target
      +view <target>/<viewname>      - Show specific view on target
      +view/set <viewname>/<target>=<text>  - Set a view
      +view/del <viewname>/<target>  - Delete a view

    Views are a way to add detail to items or locations without cluttering
    the main description. Views can be set on any object, character, or room.

    Examples:
      +view                  - Shows all views in current room
      +view here            - Same as above
      +view sword           - Lists all views on the sword
      +view sword/hilt      - Shows the 'hilt' view of the sword
      +view/set window/here=Through the window you see a beautiful garden
      +view/del window/here - Removes the 'window' view from current room
    """

    key = "+view"
    aliases = ["view"]
    locks = "cmd:all()"
    help_category = "Building and Housing"

    def func(self):
        caller = self.caller
        location = caller.location

        if not self.args and not self.switches:
            # Show all views in current location
            self._list_views(location)
            return

        if "set" in self.switches:
            # Setting a new view
            if not self.rhs:
                caller.msg("Usage: +view/set <viewname>/<target>=<description>")
                return

            try:
                viewname, target = self.lhs.split("/", 1)
                viewname = viewname.strip().lower()
                target = target.strip().lower()
            except ValueError:
                caller.msg("Usage: +view/set <viewname>/<target>=<description>")
                return

            # Find the target object
            if target == "here":
                target_obj = location
            else:
                target_obj = caller.search(target)
                if not target_obj:
                    return

            # Check permissions
            if not (target_obj.access(caller, "control") or target_obj.access(caller, "edit")):
                caller.msg(f"You don't have permission to add views to {target_obj.get_display_name(caller)}.")
                return

            # Initialize views dict if it doesn't exist
            if not target_obj.db.views:
                target_obj.db.views = {}

            # Store the view
            target_obj.db.views[viewname] = self.rhs
            caller.msg(f"Added view '{viewname}' to {target_obj.get_display_name(caller)}.")
            return

        if "del" in self.switches:
            # Deleting a view
            if not self.args:
                caller.msg("Usage: +view/del <viewname>/<target>")
                return

            try:
                viewname, target = self.args.split("/", 1)
                viewname = viewname.strip().lower()
                target = target.strip().lower()
            except ValueError:
                caller.msg("Usage: +view/del <viewname>/<target>")
                return

            # Find the target object
            if target == "here":
                target_obj = location
            else:
                target_obj = caller.search(target)
                if not target_obj:
                    return

            # Check permissions
            if not (target_obj.access(caller, "control") or target_obj.access(caller, "edit")):
                caller.msg(f"You don't have permission to remove views from {target_obj.get_display_name(caller)}.")
                return

            # Remove the view
            if target_obj.db.views and viewname in target_obj.db.views:
                del target_obj.db.views[viewname]
                caller.msg(f"Removed view '{viewname}' from {target_obj.get_display_name(caller)}.")
            else:
                caller.msg(f"No view named '{viewname}' found on {target_obj.get_display_name(caller)}.")
            return

        # Handle viewing
        if "/" in self.args:
            # View specific detail
            try:
                target, viewname = self.args.split("/", 1)
                viewname = viewname.strip().lower()
            except ValueError:
                caller.msg("Usage: +view <target>/<viewname>")
                return

            # Find the target object
            if target.lower() == "here":
                target_obj = location
            else:
                target_obj = caller.search(target)
                if not target_obj:
                    return

            # Show the view if it exists
            if target_obj.db.views and viewname in target_obj.db.views:
                caller.msg(target_obj.db.views[viewname])
            else:
                caller.msg(f"No view named '{viewname}' found on {target_obj.get_display_name(caller)}.")
        else:
            # List all views on target
            if self.args.lower() == "here":
                target_obj = location
            else:
                target_obj = caller.search(self.args)
                if not target_obj:
                    return

            self._list_views(target_obj)

    def _list_views(self, target):
        """Helper method to list all views on a target."""
        if not target.db.views or not target.db.views.keys():
            self.caller.msg(f"No views found on {target.get_display_name(self.caller)}.")
            return

        table = EvTable("|wView Name|n", border="table")
        for view in sorted(target.db.views.keys()):
            table.add_row(view)
        
        self.caller.msg(f"|wViews available on {target.get_display_name(self.caller)}:|n")
        self.caller.msg(table)

class CmdPlaces(MuxCommand):
    """
    Handle places in a room for player gatherings.

    Usage:
      +places                    - List all places in current location
      +places/create <name>     - Create a new place
      +places/rename <newname>  - Rename your current place
      +places/join <player>     - Join someone's place
      +places/leave            - Leave your current place
      +places/clean           - Remove all empty places
      tt <message>           - Say/pose/emit at your place
      ttemit <message>      - Emit at your place
      ttooc <message>       - OOC message at your place

    Aliases:
      +place, tt
      ttcreate     -> +places/create
      ttrename     -> +places/rename
      ttjoin       -> +places/join
      ttleave      -> +places/leave
      ttclean      -> +places/clean

    Places are dynamic gathering spots that players can create and join.
    They automatically clean up when everyone leaves. Use : or ; at the
    start of tt messages for poses, and | for emits.
    """

    key = "+places"
    aliases = ["+place", "tt", "ttcreate", "ttrename", "ttjoin", "ttleave", "ttclean", "ttemit", "ttooc"]
    locks = "cmd:all()"
    help_category = "Social"

    def _init_place(self, location):
        """Initialize places storage on a location if needed."""
        if not location.db.places:
            location.db.places = {}

    def _get_place_members(self, place_data):
        """Get list of online and offline members at a place."""
        online = []
        offline = []
        for occupant in place_data.get('occupants', []):
            if occupant.has_account and occupant.sessions.count():
                online.append(occupant)
            else:
                offline.append(occupant)
        return online, offline

    def _format_place_name(self, name, members):
        """Format place name with member count."""
        count = len(members[0]) + len(members[1])  # online + offline
        return f"{name} ({count})"

    def _list_places(self):
        """List all places in the room."""
        location = self.caller.location
        if not location.db.places:
            self.caller.msg("No places exist in this room.")
            return

        table = EvTable("|wPlace|n", "|wOccupants|n", border="table")
        for place_name, place_data in location.db.places.items():
            online, offline = self._get_place_members(place_data)
            occupants = []
            for member in online:
                occupants.append(member.get_display_name(self.caller))
            for member in offline:
                occupants.append(f"|w{member.get_display_name(self.caller)}|n")
            
            table.add_row(
                self._format_place_name(place_name, (online, offline)),
                ", ".join(occupants) if occupants else "Empty"
            )
        
        self.caller.msg("|wPlaces in this room:|n")
        self.caller.msg(table)

    def _clean_places(self, location):
        """Remove empty places."""
        if not location.db.places:
            return 0

        count = 0
        for place_name, place_data in list(location.db.places.items()):
            if not place_data.get('occupants', []):
                del location.db.places[place_name]
                count += 1
        return count

    def _create_place(self, name):
        """Create a new place."""
        location = self.caller.location
        self._init_place(location)

        if name in location.db.places:
            self.caller.msg(f"A place named '{name}' already exists here.")
            return

        # Leave current place if in one
        self._leave_place(quiet=True)

        location.db.places[name] = {
            'occupants': [self.caller]
        }
        location.msg_contents(f"|w{self.caller.name}|n creates a new place: {name}")

    def _join_place(self, target):
        """Join a place by player or place name."""
        location = self.caller.location
        if not location.db.places:
            self.caller.msg("No places exist in this room.")
            return

        # First try to find by player
        for place_name, place_data in location.db.places.items():
            if target in place_data.get('occupants', []):
                self._leave_place(quiet=True)
                place_data['occupants'].append(self.caller)
                location.msg_contents(
                    f"|w{self.caller.name}|n joins {place_name} "
                    f"with |w{target.name}|n"
                )
                return

        # Then try by place number or name
        try:
            place_num = int(target) - 1
            place_name = list(location.db.places.keys())[place_num]
        except (ValueError, IndexError):
            place_name = target

        if place_name in location.db.places:
            self._leave_place(quiet=True)
            location.db.places[place_name]['occupants'].append(self.caller)
            location.msg_contents(f"|w{self.caller.name}|n joins {place_name}")
        else:
            self.caller.msg(f"Could not find place '{target}'.")

    def _leave_place(self, quiet=False):
        """Leave current place."""
        location = self.caller.location
        if not location.db.places:
            return False

        for place_name, place_data in list(location.db.places.items()):
            if self.caller in place_data.get('occupants', []):
                place_data['occupants'].remove(self.caller)
                if not quiet:
                    location.msg_contents(f"|w{self.caller.name}|n leaves {place_name}")
                
                # Clean up empty place
                if not place_data['occupants']:
                    del location.db.places[place_name]
                return True
        return False

    def _rename_place(self, new_name):
        """Rename current place."""
        location = self.caller.location
        if not location.db.places:
            self.caller.msg("No places exist in this room.")
            return

        # Find caller's current place
        for old_name, place_data in list(location.db.places.items()):
            if self.caller in place_data.get('occupants', []):
                if new_name in location.db.places:
                    self.caller.msg(f"A place named '{new_name}' already exists.")
                    return
                    
                location.db.places[new_name] = place_data
                del location.db.places[old_name]
                location.msg_contents(
                    f"|w{self.caller.name}|n renames {old_name} to {new_name}"
                )
                return
                
        self.caller.msg("You are not at any place.")

    def _get_current_place(self):
        """Get the caller's current place name and data."""
        location = self.caller.location
        if not location.db.places:
            return None, None

        for place_name, place_data in location.db.places.items():
            if self.caller in place_data.get('occupants', []):
                return place_name, place_data
        return None, None

    def _handle_message(self, message, msg_type="say"):
        """Handle different types of messages at a place."""
        place_name, place_data = self._get_current_place()
        if not place_name:
            self.caller.msg("You are not at any place.")
            return

        if msg_type == "emit":
            self.caller.location.msg_contents(
                f"At {place_name}: {message}"
            )
        elif msg_type == "ooc":
            self.caller.location.msg_contents(
                f"[OOC] At {place_name}: {self.caller.name} {message}"
            )
        else:  # Regular say/pose
            if message.startswith(":"):
                message = f"{self.caller.name} {message[1:]}"
            elif message.startswith(";"):
                message = f"{self.caller.name}{message[1:]}"
            elif message.startswith("|"):
                message = message[1:]
            else:
                message = f"{self.caller.name} says, '{message}'"
            
            self.caller.location.msg_contents(
                f"At {place_name}: {message}"
            )

    def func(self):
        """Execute command."""
        if not self.caller.location:
            self.caller.msg("You have no location to create or join places.")
            return

        # Handle aliases first
        cmd = self.cmdstring.lower()
        if cmd == "tt" and self.args:
            self._handle_message(self.args)
            return
        elif cmd == "ttemit" and self.args:
            self._handle_message(self.args, "emit")
            return
        elif cmd == "ttooc" and self.args:
            self._handle_message(self.args, "ooc")
            return
        elif cmd == "ttcreate" and self.args:
            self._create_place(self.args)
            return
        elif cmd == "ttrename" and self.args:
            self._rename_place(self.args)
            return
        elif cmd == "ttjoin" and self.args:
            target = self.caller.search(self.args)
            if target:
                self._join_place(target)
            return
        elif cmd == "ttleave":
            self._leave_place()
            return
        elif cmd == "ttclean":
            count = self._clean_places(self.caller.location)
            self.caller.msg(f"Cleaned up {count} empty places.")
            return

        # Handle main command and switches
        if "create" in self.switches:
            if not self.args:
                self.caller.msg("Usage: +places/create <name>")
                return
            self._create_place(self.args)
        elif "rename" in self.switches:
            if not self.args:
                self.caller.msg("Usage: +places/rename <new name>")
                return
            self._rename_place(self.args)
        elif "join" in self.switches:
            if not self.args:
                self.caller.msg("Usage: +places/join <player or number>")
                return
            target = self.caller.search(self.args)
            if target:
                self._join_place(target)
        elif "leave" in self.switches:
            self._leave_place()
        elif "clean" in self.switches:
            count = self._clean_places(self.caller.location)
            self.caller.msg(f"Cleaned up {count} empty places.")
        else:
            self._list_places()

class CmdRoomUnfindable(MuxCommand):
    """
    Set a room as unfindable or findable.

    Usage:
      +roomunfind [<room>] [on|off]

    When set to 'on', the room won't appear in room listing commands.
    When set to 'off', the room will appear as normal.
    Using the command without an on/off argument will toggle the current state.
    If no room is specified, affects the current room.

    Examples:
      +roomunfind on           - Makes current room unfindable
      +roomunfind off          - Makes current room findable
      +roomunfind tavern on   - Makes the tavern unfindable
      +roomunfind tavern off  - Makes the tavern findable
    """

    key = "+roomunfind"
    aliases = ["roomunfind"]
    locks = "cmd:perm(Builder)"
    help_category = "Building and Housing"

    def func(self):
        caller = self.caller
        
        # Parse arguments
        args = self.args.strip() if self.args else ""
        room = None
        setting = None
        
        if args:
            if args.lower() in ["on", "off"]:
                room = caller.location
                setting = args.lower()
            else:
                # Try to split into room name and setting
                parts = args.rsplit(" ", 1)
                if len(parts) == 2 and parts[1].lower() in ["on", "off"]:
                    room_name = parts[0]
                    setting = parts[1].lower()
                    room = caller.search(room_name)
                    if not room:
                        return
                else:
                    # Just a room name, toggle mode
                    room = caller.search(args)
                    if not room:
                        return
        else:
            room = caller.location
            
        if not room:
            caller.msg("You must specify a valid room.")
            return
            
        # Verify the target is actually a room
        if not room.is_typeclass("typeclasses.rooms.Room") and not room.is_typeclass("typeclasses.rooms.RoomParent"):
            caller.msg("That is not a room.")
            return
            
        # Toggle or set the unfindable state
        if setting == "on":
            room.db.unfindable = True
        elif setting == "off":
            room.db.unfindable = False
        else:
            # Toggle current state
            room.db.unfindable = not room.db.unfindable
            
        if room.db.unfindable:
            caller.msg(f"{room.get_display_name(caller)} is now unfindable.")
        else:
            caller.msg(f"{room.get_display_name(caller)} is now findable.")

"""
Command for setting and viewing Fae descriptions of rooms.
"""
from evennia.commands.default.muxcommand import MuxCommand

class CmdRoomFaeDesc(MuxCommand):
    """
    Set or view a room's Fae description.
    Restricted to builders and higher.

    Usage:
      +roomfaedesc                - View room's Fae description
      +roomfaedesc <description> - Set room's Fae description
      +roomfaedesc/clear         - Clear room's Fae description

    Examples:
      +roomfaedesc The walls pulse with ancient faerie magic.
      +roomfaedesc/clear
    """

    key = "+roomfaedesc"
    aliases = ["+rfaedesc"]
    locks = "cmd:perm(Builder)"
    help_category = "Building and Housing"

    def func(self):
        """Execute command."""
        caller = self.caller

        if "clear" in self.switches:
            self.caller.location.db.fae_desc = ""
            caller.msg("Room's Fae description cleared.")
            return

        if not self.args:
            # View room's Fae description
            fae_desc = self.caller.location.db.fae_desc
            if fae_desc:
                caller.msg("|mRoom's Fae Description:|n\n%s" % fae_desc)
            else:
                caller.msg("This room has no special Fae aspect set.")
            return

        # Set room's Fae description
        self.caller.location.db.fae_desc = self.args
        caller.msg("Room's Fae description set.") 

class CmdSetAllowedSplats(MuxCommand):
    """
    Set which splats are allowed to rent in a housing area.
    
    Usage:
        +allowedsplats <splat1>,<splat2>,...  - Set allowed splats
        +allowedsplats/add <splat>            - Add a splat to allowed list
        +allowedsplats/remove <splat>         - Remove a splat from allowed list
        +allowedsplats/clear                  - Clear all allowed splats
        +allowedsplats/show                   - Show current allowed splats
        
    Examples:
        +allowedsplats Mage,Vampire,Changeling
        +allowedsplats/add Werewolf
        +allowedsplats/remove Vampire
        +allowedsplats/clear
        +allowedsplats/show
    """
    
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
            else:
                self.caller.msg(f"{splat} is already allowed in this area.")
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
        splats = [s.strip() for s in self.args.split(",")]
        invalid_splats = [s for s in splats if s not in self.VALID_SPLATS]
        
        if invalid_splats:
            self.caller.msg(f"Invalid splat types: {', '.join(invalid_splats)}\nValid types: {', '.join(self.VALID_SPLATS)}")
            return
            
        location.db.allowed_splats = splats
        self.caller.msg(f"Set allowed splats to: {', '.join(splats)}")

class BuildingCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.priority = 1 #fuck them og commands
        self.add(CmdSetRoomResources())
        self.add(CmdSetRoomType())
        self.add(CmdSetUmbraDesc())
        self.add(CmdSetGauntlet())
        self.add(CmdUmbraInfo())
        self.add(CmdSetHousing())
        self.add(CmdManageBuilding())
        self.add(CmdSetLock())
        self.add(CmdDesc())
        self.add(CmdView())
        self.add(CmdPlaces())
        self.add(CmdRoomUnfindable())
        self.add(CmdRoomFaeDesc())
        self.add(CmdSetAllowedSplats())