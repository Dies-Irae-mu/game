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
from evennia.utils.ansi import ANSIString
from world.wod20th.utils.formatting import header, footer, divider, format_stat

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

class CmdRoom(MuxCommand):
    """
    Set various room attributes and properties.

    Usage:
      +room/res <room dbref or here>=<value>      - Set room resources
      +room/type <room dbref or here>=<type>      - Set room type
      +room/umbradesc <room dbref or here>=<desc> - Set Umbra description
      +room/gauntlet <room dbref or here>=<rating> - Set Gauntlet rating
      +room/unfindable <room dbref or here>=<on/off> - Set room findability
      +room/faedesc <room dbref or here>=<desc>   - Set Fae description
      +room/faedesc <room dbref or here>          - View Fae description
      +room/faedesc/clear <room dbref or here>    - Clear Fae description

    Examples:
      +room/res here=4                - Set current room's resources to 4
      +room/type #123=Beach Town     - Set room #123's type to Beach Town
      +room/umbradesc here=The spirit world here shimmers with ethereal light.
      +room/gauntlet here=7          - Set current room's Gauntlet rating to 7
      +room/unfindable here=on       - Make current room unfindable
      +room/faedesc here=The walls are thickly coated with faerie magic.
    """

    key = "+room"
    locks = "cmd:perm(Builder)"
    help_category = "Building and Housing"

    def get_target_room(self, args):
        """Helper method to get target room from args."""
        if not args:
            return self.caller.location
        
        target = args.strip().lower()
        if target == "here":
            return self.caller.location
            
        room = self.caller.search(target)
        if not room:
            return None
            
        # Verify the target is actually a room
        if not room.is_typeclass("typeclasses.rooms.Room") and not room.is_typeclass("typeclasses.rooms.RoomParent"):
            self.caller.msg("That is not a room.")
            return None
            
        return room

    def func(self):
        if not self.switches:
            self.caller.msg("Usage: +room/<switch> [<room>]=<value>")
            return

        switch = self.switches[0]

        # Handle switches that don't require a value
        if switch == "faedesc" and not self.rhs:
            room = self.get_target_room(self.lhs)
            if not room:
                return

            if "clear" in self.switches:
                room.db.fae_desc = ""
                self.caller.msg("Room's Fae description cleared.")
                return

            # View room's Fae description
            fae_desc = room.db.fae_desc
            if fae_desc:
                self.caller.msg("|mRoom's Fae Description:|n\n%s" % fae_desc)
            else:
                self.caller.msg("This room has no special Fae aspect set.")
            return

        # All other switches require a value
        if not self.rhs:
            self.caller.msg(f"Usage: +room/{switch} [<room>]=<value>")
            return

        # Get target room
        room = self.get_target_room(self.lhs)
        if not room:
            return

        # Handle each switch type
        if switch == "res":
            try:
                value = int(self.rhs)
                room.db.resources = value
                self.caller.msg(f"Set resources to {value} for {room.get_display_name(self.caller)}.")
            except ValueError:
                self.caller.msg("The resources value must be an integer.")

        elif switch == "type":
            room.db.roomtype = self.rhs
            self.caller.msg(f"Set room type to '{self.rhs}' for {room.get_display_name(self.caller)}.")

        elif switch == "umbradesc":
            room.db.umbra_desc = self.rhs
            self.caller.msg(f"Umbra description set for {room.get_display_name(self.caller)}.")

        elif switch == "gauntlet":
            try:
                rating = int(self.rhs)
                if 1 <= rating <= 10:
                    room.db.gauntlet_difficulty = rating
                    self.caller.msg(f"Gauntlet rating for {room.get_display_name(self.caller)} set to {rating}.")
                else:
                    self.caller.msg("The Gauntlet rating should be between 1 and 10.")
            except ValueError:
                self.caller.msg("Please provide a valid number for the Gauntlet rating.")

        elif switch == "unfindable":
            setting = self.rhs.lower()
            if setting not in ["on", "off"]:
                self.caller.msg("Please specify either 'on' or 'off'.")
                return
                
            room.db.unfindable = (setting == "on")
            self.caller.msg(f"{room.get_display_name(self.caller)} is now {'unfindable' if setting == 'on' else 'findable'}.")

        elif switch == "faedesc":
            room.db.fae_desc = self.rhs
            self.caller.msg("Room's Fae description set.")

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
    Handle places in a room.
    
    Usage:
        +place/create <name>
        +place/delete <name>
        +place/list
        +place/sit <name>
        +place/leave
    """
    
    key = "+place"
    aliases = ["place"]
    locks = "cmd:all()"
    help_category = "Building and Housing"
    
    def _leave_place(self, quiet=False):
        """Leave current place."""
        if not self.caller.db.place:
            if not quiet:
                self.caller.msg("You are not at any place.")
            return
            
        place = self.caller.db.place
        if not quiet:
            self.caller.msg(f"You leave {place}.")
            self.caller.location.msg_contents(
                f"{self.caller.name} leaves {place}.",
                exclude=[self.caller]
            )
        self.caller.db.place = None
        
    def func(self):
        """Execute command."""
        if not self.switches:
            self.caller.msg("Usage: +place/<switch>")
            return
            
        switch = self.switches[0]
        location = self.caller.location
        
        if not hasattr(location.db, 'places'):
            location.db.places = {}
            
        if switch == "create":
            if not self.args:
                self.caller.msg("Usage: +place/create <name>")
                return
                
            name = self.args.strip()
            if name in location.db.places:
                self.caller.msg(f"Place '{name}' already exists.")
                return
                
            location.db.places[name] = []
            self.caller.msg(f"Created place '{name}'.")
            
        elif switch == "delete":
            if not self.args:
                self.caller.msg("Usage: +place/delete <name>")
                return
                
            name = self.args.strip()
            if name not in location.db.places:
                self.caller.msg(f"Place '{name}' not found.")
                return
                
            # Move any occupants out
            for occupant in location.db.places[name]:
                if occupant.db.place == name:
                    occupant.db.place = None
                    occupant.msg(f"Place '{name}' has been deleted.")
                    
            del location.db.places[name]
            self.caller.msg(f"Deleted place '{name}'.")
            
        elif switch == "list":
            if not location.db.places:
                self.caller.msg("No places found in this room.")
                return
                
            from evennia.utils.evtable import EvTable
            table = EvTable("|wPlace|n", "|wOccupants|n", border="table")
            for place, occupants in location.db.places.items():
                # Clean up stale occupants
                valid_occupants = []
                for occ in occupants:
                    if (occ and occ.location == location and 
                        occ.db.place == place):
                        valid_occupants.append(occ)
                location.db.places[place] = valid_occupants
                
                # Add to table
                table.add_row(
                    place,
                    ", ".join(o.name for o in valid_occupants) or "Empty"
                )
            self.caller.msg(table)
            
        elif switch == "sit":
            if not self.args:
                self.caller.msg("Usage: +place/sit <name>")
                return
                
            target = self.args.strip()
            
            try:
                place_num = int(target) - 1
                place_name = list(location.db.places.keys())[place_num]
            except (ValueError, IndexError):
                place_name = target
                
            if place_name not in location.db.places:
                self.caller.msg(f"Place '{target}' not found.")
                return
                
            if self.caller.db.place:
                if self.caller.db.place == place_name:
                    self.caller.msg(f"You are already at {place_name}.")
                    return
                self._leave_place(quiet=True)
                
            location.db.places[place_name].append(self.caller)
            self.caller.db.place = place_name
            self.caller.msg(f"You sit at {place_name}.")
            self.caller.location.msg_contents(
                f"{self.caller.name} sits at {place_name}.",
                exclude=[self.caller]
            )
            
        elif switch == "leave":
            self._leave_place()

class CmdManageBuilding(MuxCommand):
    """
    Manage apartment building zones.
    
    Usage:
        +manage/setlobby          - Sets current room as building lobby
        +manage/addroom           - Adds current room to building zone
        +manage/removeroom        - Removes current room from building zone
        +manage/info              - Shows building zone information
        +manage/clear             - Clears all building zone data
        +manage/types             - Lists available apartment types
        +manage/addtype <type>    - Add an apartment type to this building
        +manage/remtype <type>    - Remove an apartment type from this building
        
        +manage/updateapts         - Update all apartment exits in building
        +manage/updateapts <room>  - Update apartment exits in specific room
        
        +manage/apartments         - List all apartments in current building
        +manage/apartments <player>  - List apartments owned by player
        +manage/apartments/search=<text>  - Search apartments by name/desc
        +manage/apartments/floor=<number>  - List apartments on specific floor
        
        +manage/splats            - Show allowed splats for current building
        +manage/splats <splat1>,<splat2>,...  - Set allowed splats
        +manage/splats/clear  - Clear all allowed splats

        +manage/sethousing/apartment <resources> [max_units] - Apartment building
        +manage/sethousing/motel <resources> [max_units]    - Motel
        +manage/sethousing/residential <resources> [max_units] - Residential area
        +manage/sethousing/splat [max_units]  - Splat-specific housing (free)
        +manage/sethousing/clear              - Clear housing settings
        
    Example:
        +manage/setlobby
        +manage/addtype Studio
        +manage/addtype "Two-Bedroom"
        +manage/splats Vampire,Werewolf,Mage
        +manage/sethousing/apartment 2 20
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
                'available_types': [],
                'allowed_splats': set()  # Added for splat restrictions
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
        if switch in ["setlobby", "clear", "info", "sethousing"]:
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
                from evennia.utils.evtable import EvTable
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
                
                # Build the display using our custom formatting
                output = []
                output.append(header("Building Information"))
                
                # Building Lobby
                output.append(format_stat("Building Lobby", location.get_display_name(self.caller), width=78))
                
                # Connected Rooms
                if rooms:
                    room_list = "\n".join(r.get_display_name(self.caller) for r in rooms)
                    output.append(divider("Connected Rooms"))
                    output.append(room_list)
                else:
                    output.append(divider("Connected Rooms"))
                    output.append("None")
                
                # Building Stats
                output.append(divider("Building Stats"))
                output.append(format_stat("Max Units", location.db.housing_data.get('max_apartments', 0), width=78))
                output.append(format_stat("Resources", location.db.resources, width=78))
                
                # Available Types
                types = location.db.housing_data.get('available_types', [])
                output.append(divider("Available Types"))
                if types:
                    output.append(", ".join(types))
                else:
                    output.append("None")
                
                # Allowed Splats
                splats = sorted(location.db.housing_data.get('allowed_splats', set()))
                output.append(divider("Allowed Splats"))
                if splats:
                    output.append(", ".join(splats))
                else:
                    output.append("None")
                
                output.append(footer())
                
                # Send the formatted output to the caller
                self.caller.msg("\n".join(output))
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

        elif switch == "updateapts":
            # Get the target building
            target = None
            if self.args:
                target = self.caller.search(self.args)
                if not target:
                    return
            else:
                target = location

            # Find the lobby if we're not in it
            if not target.db.housing_data.get('is_lobby'):
                lobby = self.find_lobby(target)
                if not lobby:
                    self.caller.msg("You must be in a building lobby or specify a valid building.")
                    return
                target = lobby

            # Update all apartments in the building
            updated = 0
            for room_id in target.db.housing_data.get('connected_rooms', set()):
                room = self.caller.search(f"#{room_id}")
                if room and room.db.housing_data:
                    # Update room properties from the lobby
                    room.db.housing_data.update({
                        'max_apartments': target.db.housing_data.get('max_apartments', 20),
                        'available_types': target.db.housing_data.get('available_types', []),
                        'allowed_splats': target.db.housing_data.get('allowed_splats', set())
                    })
                    updated += 1

            self.caller.msg(f"Updated {updated} rooms in {target.get_display_name(self.caller)}.")

        elif switch == "apartments":
            # Get the target building
            building = None
            if not location.db.housing_data.get('is_lobby'):
                building = self.find_lobby(location)
                if not building:
                    self.caller.msg("You must be in a building lobby.")
                    return
            else:
                building = location

            # Initialize variables for filtering
            target_player = None
            search_text = None
            floor_number = None

            # Parse arguments and switches
            if self.args and "=" not in self.args:
                # Looking for a specific player's apartments
                from evennia.accounts.models import AccountDB
                target_account = AccountDB.objects.filter(username__iexact=self.args).first()
                if target_account:
                    target_player = target_account.puppet or target_account.db._last_puppet
                else:
                    self.caller.msg(f"Player '{self.args}' not found.")
                    return
            elif "search" in self.switches and self.rhs:
                search_text = self.rhs.lower()
            elif "floor" in self.switches and self.rhs:
                try:
                    floor_number = int(self.rhs)
                except ValueError:
                    self.caller.msg("Please specify a valid floor number.")
                    return

            # Get all apartments in the building
            apartments = []
            for room_id in building.db.housing_data.get('connected_rooms', set()):
                room = self.caller.search(f"#{room_id}")
                if room and room.db.housing_data:
                    # Filter based on criteria
                    if target_player:
                        # Check if player owns this apartment
                        if not self.is_owner(room, target_player):
                            continue
                    elif search_text:
                        # Check if search text matches name or description
                        if (search_text not in room.key.lower() and 
                            (not room.db.desc or search_text not in room.db.desc.lower())):
                            continue
                    elif floor_number is not None:
                        # Check if apartment is on the specified floor
                        try:
                            room_floor = int(room.key.split()[1])  # Assumes format "Apartment X-Y"
                            if room_floor != floor_number:
                                continue
                        except (IndexError, ValueError):
                            continue

                    apartments.append(room)

            if not apartments:
                if target_player:
                    self.caller.msg(f"{target_player.name} doesn't own any apartments in this building.")
                elif search_text:
                    self.caller.msg(f"No apartments found matching '{search_text}'.")
                elif floor_number is not None:
                    self.caller.msg(f"No apartments found on floor {floor_number}.")
                else:
                    self.caller.msg("No apartments found in this building.")
                return

            # Display results
            from evennia.utils.evtable import EvTable
            table = EvTable("|wApartment|n", "|wOwner|n", "|wType|n", "|wStatus|n", border="table")
            for apt in apartments:
                owner = "None"
                if apt.db.housing_data and 'owner' in apt.db.housing_data:
                    owner_char = self.caller.search(f"#{apt.db.housing_data['owner']}")
                    if owner_char:
                        owner = owner_char.name
                apt_type = apt.db.roomtype if apt.db.roomtype else "Unknown"
                status = "Locked" if apt.db.housing_data.get('locked', False) else "Unlocked"
                table.add_row(
                    apt.get_display_name(self.caller),
                    owner,
                    apt_type,
                    status
                )
            self.caller.msg(table)

        elif switch == "splats":
            if not location.db.housing_data.get('is_lobby'):
                lobby = self.find_lobby(location)
                if not lobby:
                    self.caller.msg("You must be in a building lobby.")
                    return
                location = lobby

            if "add" in self.switches:
                if not self.rhs:
                    self.caller.msg("Usage: +manage/splats/add=<splat>")
                    return
                splat = self.rhs.strip().title()
                if 'allowed_splats' not in location.db.housing_data:
                    location.db.housing_data['allowed_splats'] = set()
                location.db.housing_data['allowed_splats'].add(splat)
                self.caller.msg(f"Added {splat} to allowed splats.")

            elif "remove" in self.switches:
                if not self.rhs:
                    self.caller.msg("Usage: +manage/splats/remove=<splat>")
                    return
                splat = self.rhs.strip().title()
                if splat in location.db.housing_data.get('allowed_splats', set()):
                    location.db.housing_data['allowed_splats'].remove(splat)
                    self.caller.msg(f"Removed {splat} from allowed splats.")
                else:
                    self.caller.msg(f"{splat} is not in the allowed splats list.")

            elif "clear" in self.switches:
                location.db.housing_data['allowed_splats'] = set()
                self.caller.msg("Cleared all allowed splats.")

            elif self.args and "=" not in self.args:
                # Set entire list of splats
                splats = {s.strip().title() for s in self.args.split(',')}
                location.db.housing_data['allowed_splats'] = splats
                self.caller.msg(f"Set allowed splats to: {', '.join(sorted(splats))}")

            else:
                # Show current allowed splats
                splats = location.db.housing_data.get('allowed_splats', set())
                if splats:
                    self.caller.msg("Allowed splats in this building:")
                    self.caller.msg(", ".join(sorted(splats)))
                else:
                    self.caller.msg("No splat restrictions set for this building.")

        elif switch == "sethousing":
            # Handle sethousing functionality
            if not self.switches[1:]:  # No sub-switch provided
                self.caller.msg("Please specify the type: /apartment, /motel, /residential, /splat, or /clear")
                return

            sub_switch = self.switches[1]
            location = self.caller.location

            # Handle clear switch first
            if sub_switch == "clear":
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

            # Special handling for splat housing which doesn't need resources
            if sub_switch == "splat":
                try:
                    if self.args:
                        max_units = int(self.args)
                    else:
                        max_units = 20  # Default to 20 if not specified
                    
                    if max_units < 1:
                        self.caller.msg("Maximum units must be at least 1.")
                        return
                        
                except ValueError:
                    self.caller.msg("Usage: +manage/sethousing/splat [max_units]")
                    return
                    
                # Set up basic room configuration first
                location.db.roomtype = "Splat Housing"
                location.db.resources = 0  # Splat housing is free
                
                # Set up housing data directly
                housing_data = {
                    'is_housing': True,
                    'max_apartments': max_units,
                    'current_tenants': {},
                    'apartment_numbers': set(),
                    'required_resources': 0,
                    'building_zone': location.dbref,
                    'connected_rooms': {location.dbref},
                    'is_lobby': True,
                    'available_types': ["Splat Housing"]
                }
                
                # Set the housing data directly
                location.db.housing_data = housing_data
                
                # Force a save by accessing the attribute again
                _ = location.db.housing_data
                
                self.caller.msg(f"Set up room as free splat-specific housing with {max_units} maximum units. Room is automatically set as a lobby.")
                return

            # Parse arguments for non-splat housing
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
                self.caller.msg("Usage: +manage/sethousing/<type> <resources> [max_units]")
                return
            
            # Initialize housing data first
            housing_data = self.initialize_housing_data(location)
            
            # Set up housing based on sub-switch
            if sub_switch == "apartment":
                location.db.roomtype = "Apartment Building"
                location.db.resources = resources
                
                # Set up housing data
                housing_data.update({
                    'is_housing': True,
                    'max_apartments': max_units,
                    'current_tenants': {},
                    'apartment_numbers': set(),
                    'required_resources': resources,
                    'building_zone': location.dbref,
                    'connected_rooms': {location.dbref},
                    'is_lobby': True,
                    'available_types': []
                })
                
                self.caller.msg(f"Set up room as apartment building with {resources} resources and {max_units} maximum units.")
                
            elif sub_switch == "motel":
                location.db.roomtype = "Motel"
                location.db.resources = resources
                
                # Set up housing data
                housing_data.update({
                    'is_housing': True,
                    'max_apartments': max_units,
                    'current_tenants': {},
                    'apartment_numbers': set(),
                    'required_resources': resources,
                    'building_zone': location.dbref,
                    'connected_rooms': {location.dbref},
                    'is_lobby': True,
                    'available_types': []
                })
                
                self.caller.msg(f"Set up room as motel with {resources} resources and {max_units} maximum units.")
                
            elif sub_switch == "residential":
                location.db.roomtype = "Residential Area"
                location.db.resources = resources
                
                # Set up housing data
                housing_data.update({
                    'is_housing': True,
                    'max_apartments': max_units,
                    'current_tenants': {},
                    'apartment_numbers': set(),
                    'required_resources': resources,
                    'building_zone': location.dbref,
                    'connected_rooms': {location.dbref},
                    'is_lobby': True,
                    'available_types': []
                })
                
                self.caller.msg(f"Set up room as residential area with {resources} resources and {max_units} maximum units.")
            else:
                self.caller.msg("Invalid housing type. Use /apartment, /motel, /residential, /splat, or /clear")

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
            
            # Check current_tenants - handle both string and integer keys
            if housing_data.get('current_tenants'):
                # Check both string and integer versions of the room ID
                str_id = str(room.id)
                int_id = room.id
                is_tenant = (
                    (str_id in housing_data['current_tenants'] and housing_data['current_tenants'][str_id] == player.id) or
                    (int_id in housing_data['current_tenants'] and housing_data['current_tenants'][int_id] == player.id)
                )
                if is_tenant:
                    return True
            
        # Finally check legacy owner
        if hasattr(room.db, 'owner') and room.db.owner:
            is_legacy_owner = room.db.owner.id == player.id
            if is_legacy_owner:
                return True
            
        return False

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

class BuildingCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.priority = 1  # Override default commands
        self.add(CmdRoom())  # Add the new unified room command
        self.add(CmdManageBuilding())  # Includes +manage/updateapts, +manage/apartments, +manage/splats
        self.add(CmdSetLock())
        self.add(CmdDesc())
        self.add(CmdView())
        self.add(CmdPlaces())
        self.add(CmdUmbraInfo())
