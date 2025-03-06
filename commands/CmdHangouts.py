"""
Hangouts system for listing and managing hangout locations.
"""

from evennia import Command, CmdSet
from evennia.utils.evtable import EvTable
from evennia.utils.utils import list_to_string
from world.hangouts.models import HangoutDB, HANGOUT_CATEGORIES
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils import search

class CmdHangout(MuxCommand):
    """
    View and manage hangout locations.

    Usage:
        +hangout[/all]
        +hangout/type [<category>]
        +hangout <number>
        +hangout[/jump /tel /join /visit] <number>

        Staff/Builder Commands:
        +hangout/create <name>
        +hangout/setroom <#>=<room dbref or 'here'>
        +hangout/setdesc <#>=<description>
        +hangout/settype <#>=<category>
        +hangout/setdistrict <#>=<district name>
        +hangout/setsplat <#>=<splat type>
        +hangout/delete <#>
        +hangout/restrict <#>=<yes/no>

    The +hangout command allows you to view a list of hangout spots and landmarks 
    in the reality your character is currently in.

    Switches:
        /all        - Show all hangouts, including those with no visitors
        /type       - List hangouts by category or show available categories
        /jump       - Teleport to the specified hangout (OOC convenience)
        /tel        - Alias for /jump
        /join       - Alias for /jump
        /visit      - Alias for /jump

        Staff Only:
        /create     - Create a new hangout
        /setroom    - Set the room location for a hangout
        /setdesc    - Set the description for a hangout
        /settype    - Set the category for a hangout
        /setdistrict - Set the district for a hangout
        /setsplat   - Set splat requirements for a hangout
        /delete     - Delete a hangout
        /restrict   - Set whether the hangout is restricted

    Examples:
        +hangout            - Show hangouts with active visitors
        +hangout/all       - Show all hangouts
        +hangout/type      - List all available categories
        +hangout/type Club - Show all Club category hangouts
        +hangout 42        - View detailed info about hangout #42
        +hangout/jump 42   - Teleport to hangout #42
        
        Staff Examples:
        +hangout/create The Perils
        +hangout/setroom 42=here
        +hangout/setdesc 42=A dark and moody fetish club.
        +hangout/settype 42=Club
        +hangout/setdistrict 42=Downtown
        +hangout/setsplat 42=Mage
        +hangout/restrict 42=yes
    """
    
    key = "+hangout"
    aliases = ["+hangouts", "+hotspot", "+hotspots",
              "+dir", "+directory", "+yp", "+yellowpages"]
    help_category = "RP Commands"
    
    def _check_staff_perms(self):
        """Check if the caller has staff permissions."""
        return self.caller.check_permstring("builders") or self.caller.check_permstring("wizards")

    def _get_hangout_by_id(self, hangout_id):
        """Get a hangout by ID, with staff override for visibility."""
        try:
            hangout_id = int(hangout_id)
            if self._check_staff_perms():
                return HangoutDB.get_by_hangout_id(hangout_id)
            else:
                hangouts = HangoutDB.get_visible_hangouts(self.caller)
                return next((h for h in hangouts if h.db.hangout_id == hangout_id), None)
        except (ValueError, TypeError):
            return None

    def _format_header(self, text):
        """Format a header with custom borders."""
        width = 78
        return f"{'|b=|n' * width}\n {text}\n{'|b=|n' * width}"

    def _format_separator(self):
        """Format a section separator."""
        return "|b-|n" * 78

    def _display_hangout_details(self, hangout):
        """Create a detailed display for a single hangout."""
        if not hangout:
            self.caller.msg("Hangout not found.")
            return

        # Get access requirements
        access_tags = []
        if hangout.db.required_splats:
            access_tags.extend(hangout.db.required_splats)
        if hangout.db.required_merits:
            access_tags.extend(hangout.db.required_merits)
        if hangout.db.required_factions:
            access_tags.extend(hangout.db.required_factions)
        
        access_display = "All" if not access_tags else ", ".join(access_tags)

        # Header
        self.caller.msg(self._format_header(f"Hangout {hangout.db.hangout_id}"))
        
        # Info section with custom formatting
        self.caller.msg("|wName:|n " + hangout.key)
        self.caller.msg("|wDistrict:|n " + hangout.db.district)
        self.caller.msg("|wCategory:|n " + hangout.db.category)
        self.caller.msg("|wAccess Tags:|n " + access_display)
        
        # Description section
        self.caller.msg(self._format_separator())
        self.caller.msg("|yDescription|n")
        self.caller.msg(hangout.db.description)
        self.caller.msg(self._format_separator())

    def _display_hangout_list(self, hangouts, show_all=False):
        """Create a formatted list of hangouts."""
        if not hangouts:
            self.caller.msg("No hangouts found.")
            return

        # Group hangouts by district
        district_groups = {}
        for h in hangouts:
            # Ensure hangout has an ID before displaying
            if h.db.hangout_id is None:
                h.attributes.add("hangout_id", HangoutDB._get_next_hangout_id())
            
            district = h.db.district or "Uncategorized"
            if district not in district_groups:
                district_groups[district] = []
            district_groups[district].append(h)

        # Header
        self.caller.msg(self._format_header("Hangouts"))
        
        # Header row - custom formatting
        self.caller.msg("|w  # | Info" + "Players".rjust(55) + "|n")

        # Display each district group
        for district in sorted(district_groups.keys()):
            # District separator
            self.caller.msg(self._format_separator())
            self.caller.msg(f"|w{district}|n")
            
            # Display hangouts in this district, sorted by hangout_id
            district_hangouts = sorted(district_groups[district], key=lambda x: x.db.hangout_id)
            for hangout in district_hangouts:
                number, info_line, desc_line = hangout.get_display_entry(show_restricted=True)
                
                # Only show hangouts with players unless /all is used
                room = hangout.db.room
                if room:
                    player_count = len([obj for obj in room.contents if obj.has_account])
                else:
                    player_count = 0
                    
                if show_all or player_count > 0:
                    # Format the hangout ID to be right-aligned in 3 spaces
                    formatted_id = str(hangout.db.hangout_id).rjust(3)
                    self.caller.msg(f"{formatted_id} | {info_line}")
                    self.caller.msg(desc_line)

        # Footer with help text
        self.caller.msg(self._format_separator())
        self.caller.msg("|w* = Hidden Hangout|n")
        self.caller.msg("|y+hangouts/all - show all hangouts|n")
        self.caller.msg("|y+hangouts/type <category> - show all hangouts of a certain category|n")
        self.caller.msg("|y+hangouts/type - show all hangouts separated by category|n")
        self.caller.msg(self._format_separator())
        # Add categories list
        self.caller.msg("|yCategories are:|n " + ", ".join(sorted(HANGOUT_CATEGORIES)))
        self.caller.msg("|b=" * 78)

    def func(self):
        """Execute the hangout command."""
        
        # Basic +hangout command - show active hangouts
        if not self.args and not self.switches:
            hangouts = HangoutDB.get_visible_hangouts(self.caller)
            self._display_hangout_list(hangouts, show_all=False)
            return

        # Handle non-staff switches first
        if "all" in self.switches:
            # Show all hangouts, including empty ones
            hangouts = HangoutDB.get_visible_hangouts(self.caller)
            self._display_hangout_list(hangouts, show_all=True)
            return

        if "type" in self.switches:
            if not self.args:
                # Display available categories
                self.caller.msg("Available Categories:")
                self.caller.msg(", ".join(sorted(HANGOUT_CATEGORIES)))
                return
                
            category = self.args.strip().title()
            if category not in HANGOUT_CATEGORIES:
                self.caller.msg(f"Invalid category. Valid categories are: {', '.join(HANGOUT_CATEGORIES)}")
                return
                
            hangouts = HangoutDB.get_hangouts_by_category(category, self.caller)
            self._display_hangout_list(hangouts, show_all=True)
            return

        # Handle teleport switches
        if any(switch in ["jump", "tel", "join", "visit"] for switch in self.switches):
            try:
                hangout_id = int(self.args)
                hangouts = HangoutDB.get_visible_hangouts(self.caller)
                hangout = next((h for h in hangouts if h.db.hangout_id == hangout_id), None)
                
                if not hangout:
                    self.caller.msg("That hangout was not found or is not accessible.")
                    return
                    
                room = hangout.db.room
                if not room:
                    self.caller.msg("That hangout's location is not properly set up.")
                    return
                    
                self.caller.move_to(room, quiet=True)
                self.caller.msg(f"You teleport to {hangout.key}.")
                return
                
            except ValueError:
                self.caller.msg("Please specify a valid hangout number.")
                return
        
        # Staff/Builder commands
        if self.switches and self._check_staff_perms():
            if "create" in self.switches:
                if not self.args:
                    self.caller.msg("Usage: +hangout/create <name>")
                    return
                    
                name = self.args.strip()
                hangout = HangoutDB.create(
                    key=name,
                    room=None,
                    category="Uncategorized",
                    district="Unassigned",
                    description="No description set."
                )
                self.caller.msg(f"Created hangout #{hangout.db.hangout_id}: {name}")
                return

            # All other staff commands require a hangout ID
            if not self.args or "=" not in self.args:
                self.caller.msg("Usage: +hangout/<switch> <#>=<value>")
                return

            hangout_id, value = self.args.split("=", 1)
            hangout = self._get_hangout_by_id(hangout_id)
            
            if not hangout:
                self.caller.msg("Invalid hangout ID.")
                return

            if "setroom" in self.switches:
                if value.lower() == "here":
                    room = self.caller.location
                else:
                    room = search.search_object(value)
                    if not room or len(room) != 1:
                        self.caller.msg("Room not found.")
                        return
                    room = room[0]
                
                hangout.db.room = room
                self.caller.msg(f"Set room for hangout #{hangout.db.hangout_id} to {room}")
                
            elif "setdesc" in self.switches:
                hangout.db.description = value
                self.caller.msg(f"Updated description for hangout #{hangout.db.hangout_id}")
                
            elif "settype" in self.switches:
                category = value.strip().title()
                if category not in HANGOUT_CATEGORIES:
                    self.caller.msg(f"Invalid category. Valid categories are: {', '.join(HANGOUT_CATEGORIES)}")
                    return
                    
                hangout.db.category = category
                self.caller.msg(f"Set category for hangout #{hangout.db.hangout_id} to {category}")
                
            elif "setdistrict" in self.switches:
                hangout.db.district = value.strip()
                self.caller.msg(f"Set district for hangout #{hangout.db.hangout_id} to {value}")
                
            elif "setsplat" in self.switches:
                hangout.db.required_splats = [value.strip()]
                self.caller.msg(f"Set splat requirement for hangout #{hangout.db.hangout_id} to {value}")
                
            elif "restrict" in self.switches:
                restricted = value.lower() in ("yes", "true", "1")
                hangout.db.restricted = restricted
                self.caller.msg(f"Set restricted status for hangout #{hangout.db.hangout_id} to {restricted}")
                
            elif "delete" in self.switches:
                if value.lower() != "yes":
                    self.caller.msg("To delete, use: +hangout/delete <#>=yes")
                    return
                    
                name = hangout.key
                hangout.delete()
                self.caller.msg(f"Deleted hangout: {name}")
                
            return

        # Handle viewing a specific hangout (no switches)
        try:
            hangout_id = int(self.args)
            hangouts = HangoutDB.get_visible_hangouts(self.caller)
            hangout = next((h for h in hangouts if h.db.hangout_id == hangout_id), None)
            
            if not hangout:
                self.caller.msg("That hangout was not found or is not accessible.")
                return
                
            self._display_hangout_details(hangout)
            
        except ValueError:
            self.caller.msg("Please specify a valid hangout number.")
    