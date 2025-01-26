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
    
    def func(self):
        location = self.caller.location
        
        # Handle clear switch first
        if "clear" in self.switches:
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
            location.db.roomtype = "Room"
            location.db.resources = 0
            self.caller.msg("Housing settings cleared.")
            return
            
        # Check for valid switch
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
        
        # Set up housing based on switch
        if "apartment" in self.switches:
            location.setup_housing("Apartment Building", max_units)
            location.db.resources = resources
            location.db.housing_data['max_apartments'] = max_units  # Explicitly set max_apartments
            self.caller.msg(f"Set up room as apartment building with {resources} resources and {max_units} maximum units.")
            
        elif "condo" in self.switches:
            location.setup_housing("Condominiums", max_units)
            location.db.resources = resources
            location.db.housing_data['max_apartments'] = max_units  # Explicitly set max_apartments
            self.caller.msg(f"Set up room as condominium with {resources} resources and {max_units} maximum units.")
            
        elif "residential" in self.switches:
            location.setup_housing("Residential Area", max_units)
            location.db.resources = resources
            location.db.housing_data['max_apartments'] = max_units  # Explicitly set max_apartments
            self.caller.msg(f"Set up room as residential area with {resources} resources and {max_units} maximum units.")

class CmdManageBuilding(MuxCommand):
    """
    Manage apartment building zones.
    
    Usage:
        +building/setlobby            - Sets current room as building lobby
        +building/addroom            - Adds current room to building zone
        +building/removeroom         - Removes current room from building zone
        +building/info               - Shows building zone information
        +building/clear              - Clears all building zone data
        +building/types             - Lists available apartment types
        +building/addtype <type>    - Add an apartment type to this building
        +building/remtype <type>    - Remove an apartment type from this building
        
    Example:
        +building/setlobby
        +building/addtype Studio
        +building/addtype "Two-Bedroom"
    """
    
    key = "+building"
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
                
        self.caller.msg("You must set up this room as a lobby first using +building/setlobby")
        return False

    def func(self):
        if not self.switches:
            self.caller.msg("Usage: +building/<switch>")
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
                self.caller.msg("Usage: +building/addtype <type>")
                return
                
            try:
                from commands.housing import CmdRent
                apt_type = self.args.strip()
                if apt_type not in CmdRent.APARTMENT_TYPES and apt_type not in CmdRent.RESIDENTIAL_TYPES:
                    self.caller.msg(f"Invalid type. Use +building/types to see available types.")
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
        +lock <target>=<locktype>:<value>[,<locktype>:<value>...]
        +lock/view <target>=<locktype>:<value>[,<locktype>:<value>...]
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
        mage_faction:<name> - Restrict to specific mage faction
        convention:<name> - Restrict to specific Technocratic convention
        nephandi_faction:<name> - Restrict to specific Nephandi faction
        court:<name>      - Restrict to specific changeling court
        kith:<name>       - Restrict to specific changeling kith
    """
    
    key = "+lock"
    aliases = ["+locks"]
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
        if not self.args:
            self.caller.msg("Usage: +lock <target>=<locktype>:<value>[,<locktype>:<value>...]")
            return
            
        # Handle switches first
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

        if not self.rhs:
            self.caller.msg("Usage: +lock <target>=<locktype>:<value>[,<locktype>:<value>...]")
            return
            
        target = self.caller.search(self.lhs, location=self.caller.location)
        if not target:
            return
            
        # Split multiple lock definitions
        lock_defs = []
        for lock_part in self.rhs.split(','):
            try:
                locktype, value = lock_part.strip().split(':', 1)
                locktype = locktype.strip().lower()
                
                # Create the appropriate lock string based on type
                if locktype == "splat":
                    lock_str = f'has_splat({value.strip()})'
                elif locktype == "type":
                    lock_str = f'has_type({value.strip()})'
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
                elif locktype in ["clan", "tribe", "auspice", "tradition", "mage_faction", "kith", "court"]:
                    lock_str = f'has_{locktype}({value.strip()})'
                else:
                    self.caller.msg(f"Invalid lock type.")
                    return
                    
                lock_defs.append(lock_str)
                
            except ValueError:
                self.caller.msg(f"Invalid lock format: {lock_part}")
                return
                
        # Combine all lock definitions with AND
        final_lock_def = " and ".join(lock_defs)
        
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
      desc <description>
      desc <obj> = <description>
      @desc/edit [<obj>]        - Edit description in a line editor

    Sets the "desc" attribute on an object. If no object is given,
    describe yourself. You can always describe yourself, but need
    appropriate permissions to describe other objects.

    Special characters:
      %r or %R - New line
      %t or %T - Tab
    """

    key = "@desc"
    aliases = ["@desc/edit"]
    switch_options = ("edit",)
    locks = "cmd:perm(desc) or perm(Builder) or self()"
    help_category = "Building and Housing"

    def edit_handler(self):
        if self.rhs:
            self.msg("|rYou may specify a value, or use the edit switch, but not both.|n")
            return
        if self.args:
            obj = self.caller.search(self.args)
        else:
            obj = self.caller.location or self.msg("|rYou can't describe oblivion.|n")
        if not obj:
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
            caller.msg("Usage: desc [<obj> =] <description>")
            return

        if "edit" in self.switches:
            self.edit_handler()
            return

        if "=" in self.args:
            # We have an =
            obj = caller.search(self.lhs)
            if not obj:
                return
            desc = self.rhs or ""
        else:
            # No = means we're trying to desc ourselves
            obj = caller
            desc = self.args
            
        if obj == caller or obj.access(self.caller, "control") or obj.access(self.caller, "edit"):
            obj.db.desc = desc
            caller.msg(f"The description was set on {obj.get_display_name(caller)}.")
        else:
            caller.msg(f"You don't have permission to edit the description of {obj.key}.")

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