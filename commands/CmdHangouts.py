"""
Hangouts system for listing and managing hangout locations.
"""

from evennia import Command, CmdSet
from evennia.utils.evtable import EvTable
from evennia.utils.utils import list_to_string
from world.hangouts.models import HangoutDB, HANGOUT_CATEGORIES
from evennia.commands.default.muxcommand import MuxCommand

class CmdHangout(MuxCommand):
    """
    View and manage hangout locations.
    
    Usage:
        +hangout[/all]
        +hangout/occupied
        +hangout/type
        +hangout/type <category>
        +hangout <number>
        +hangout[/jump /tel /join /visit] <number>
        +hangout/create <category>=<description>  (builders only)
        +hangout/desc <number>=<description>  (builders only)
        
    The +hangout command allows you to view a list of hangout spots and landmarks
    in the reality your character is currently in - usually the Los Angeles grid.
    
    Switches:
        /all        - Show all hangouts (same as default)
        /occupied   - Show only hangouts with current visitors
        /type       - List categories or show hangouts of a specific category
        /jump       - Teleport to the hangout (OOC convenience)
        /tel        - Alias for /jump
        /join       - Alias for /jump
        /visit      - Alias for /jump
        /create     - Create a hangout in current room (builders only)
        /desc       - Update a hangout's description (builders only)
        
    Examples:
        +hangout
        +hangout/all
        +hangout/type Club
        +hangout 265
        +hangout/jump 265
        +hangout/create Club=A trendy nightclub in downtown San Diego
        +hangout/desc 265=A cozy jazz club with live music every night
    """
    
    key = "+hangout"
    aliases = ["+hangouts", "+hideout", "+hideouts", "+hotspot", "+hotspots",
              "+dir", "+directory", "+yp", "+yellowpages"]
    help_category = "RP Commands"
    
    def get_hangouts_by_district(self, character, show_occupied=False):
        """Get all visible hangouts grouped by district."""
        hangouts = {}
        
        # Get all hangouts of our typeclass
        all_hangouts = HangoutDB.objects.all()
                                            
        for hangout in all_hangouts:
            # Skip if not active
            if not hangout.db.active:
                continue
                
            # Skip if character can't see it
            if not hangout.can_see(character):
                continue
                
            # If show_occupied is True, skip empty locations
            if show_occupied:
                location = hangout.db.room
                if not location or not [obj for obj in location.contents if obj.has_account]:
                    continue
                    
            district = hangout.db.district or "Uncategorized"
            if district not in hangouts:
                hangouts[district] = []
            hangouts[district].append(hangout)
            
        return hangouts
        
    def get_hangouts_by_category(self, character, category=None):
        """Get all visible hangouts of a specific category."""
        hangouts = {}
        
        # Get all active hangouts
        all_hangouts = HangoutDB.objects.filter(db_attributes__key="active", 
                                            db_attributes__value=True)
                                            
        for hangout in all_hangouts:
            # Skip if character can't see it
            if not hangout.can_see(character):
                continue
                
            hangout_category = hangout.db.category
            if category and hangout_category != category:
                continue
                
            if hangout_category not in hangouts:
                hangouts[hangout_category] = []
            hangouts[hangout_category].append(hangout)
            
        return hangouts
        
    def display_hangout_list(self, hangouts_by_group, show_restricted=False):
        """Format and display the hangout list."""
        output = [
            "|b=|n" * 33 + "|b<|n |yHangouts|n |b>|n" + "|b=|n" * 33 + "\n"
        ]
        
        if not any(hangouts_by_group.values()):
            output.append("\nNo hangouts found.\n")
        else:
            for category in sorted(hangouts_by_group.keys()):
                if not hangouts_by_group[category]:
                    continue
                    
                # Add category header
                header = f"|b==>|n |y{category}|n |b<|n"
                padding = 78 - len(category) - 7  # 7 is length of "==> " and " <"
                output.append(f"\n{header}{'|b=|n' * padding}\n")
                
                # Group hangouts into rows of 3
                hangouts = sorted(hangouts_by_group[category], key=lambda x: x.pk)
                row = []
                for hangout in hangouts:
                    restricted_marker = "*" if hangout.db.restricted and show_restricted else ""
                    entry = f" {hangout.key} - ID#{hangout.pk}{restricted_marker}"
                    row.append(entry.ljust(25))
                    
                    if len(row) == 3:
                        output.append("".join(row) + "\n")
                        row = []
                        
                # Add any remaining hangouts
                if row:
                    output.append("".join(row) + "\n")
                    
        # Add footer
        output.extend([
            "\n" + "|b=|n" * 78 + "\n",
            "       |y*|n = Hidden Hangout\n",
            "       |w+hangouts/all|n - show all hangouts\n",
            "       |w+hangouts/type <category>|n - show all hangouts of a certain category\n",
            "       |w+hangouts/type|n - show all hangouts separated by category\n",
            "\n" + "|b=|n" * 78
        ])
        
        return "".join(output)
        
    def display_single_hangout(self, hangout, show_restricted=False):
        """Display detailed information about a single hangout."""
        if not hangout:
            return "Hangout not found."
            
        # Calculate header padding for exact 78 character width
        title_padding = (78 - 11) // 2  # 11 is length of "< Hangout >"
        output = [
            "|b=|n" * title_padding + "|b<|n |yHangout|n |b>|n" + "|b=|n" * (78 - title_padding - 11) + "\n\n"
        ]
        
        restricted_marker = "*" if hangout.db.restricted and show_restricted else ""
        
        # Calculate header components
        prefix = "|b==>|n "
        name_part = f"|w{hangout.key}|n"
        id_part = f" - ID#{hangout.pk}{restricted_marker}"
        suffix = " |b<|n"
        
        # Calculate remaining space for filler characters
        used_space = len(prefix.replace("|b", "").replace("|n", "").replace("|w", "")) + \
                    len(hangout.key) + \
                    len(id_part) + \
                    len(suffix.replace("|b", "").replace("|n", ""))
        filler_count = 78 - used_space
        
        # Construct header with calculated filler
        header = f"{prefix}{name_part}{id_part}{suffix}{'|b=|n' * filler_count}"
        output.append(f"{header}\n")
        
        if hangout.db.description:
            output.append(f" {hangout.db.description}\n")
        
        details_header = "|b==>|n |yDetails|n |b<|n"
        output.append(f"\n{details_header}{'|b=|n' * (78 - len('==> Details <'))}\n")
        output.append(f" |wDistrict:|n {hangout.db.district or 'None'}\n")
        output.append(f" |wCategory:|n {hangout.db.category or 'None'}\n")
        
        if show_restricted and hangout.db.restricted:
            reqs_header = "|b==>|n |yRequirements|n |b<|n"
            output.append(f"\n{reqs_header}{'|b=|n' * (78 - len('==> Requirements <'))}\n")
            if hangout.db.required_splats:
                output.append(f" |wSplats:|n {', '.join(hangout.db.required_splats)}\n")
            if hangout.db.required_merits:
                output.append(f" |wMerits:|n {', '.join(hangout.db.required_merits)}\n")
            if hangout.db.required_factions:
                output.append(f" |wFactions:|n {', '.join(hangout.db.required_factions)}\n")
                
        output.append("\n" + "|b=|n" * 78)
        
        return "".join(output)
        
    def func(self):
        """Execute command."""
        if "create" in self.switches:
            if not self.caller.check_permstring("builders"):
                self.caller.msg("You must be a builder to create hangouts.")
                return
                
            if not self.rhs:
                self.caller.msg("Usage: +hangout/create <category>=<description>")
                return
                
            category = self.lhs.strip().title()
            if category not in HANGOUT_CATEGORIES:
                self.caller.msg(f"Invalid category. Valid categories are: {', '.join(HANGOUT_CATEGORIES)}")
                return
                
            # Get the current room's district
            room = self.caller.location
            district = room.db.district or "Uncategorized"
                
            # Create the hangout
            hangout = HangoutDB.create(
                key=room.key,
                room=room,
                category=category,
                district=district,
                description=self.rhs.strip()
            )
            
            # Verify the attributes were set
            if not hangout.db.category or not hangout.db.description:
                hangout.db.category = category
                hangout.db.description = self.rhs.strip()
                hangout.db.district = district
                hangout.db.room = room
                hangout.db.active = True
            
            self.caller.msg(f"Created hangout {hangout.pk}: {room.key}")
            # Show the newly created hangout
            self.caller.msg(self.display_single_hangout(hangout, show_restricted=True))
            return
            
        if "desc" in self.switches:
            if not self.caller.check_permstring("builders"):
                self.caller.msg("You must be a builder to modify hangouts.")
                return
                
            if not self.rhs:
                self.caller.msg("Usage: +hangout/desc <number>=<description>")
                return
                
            try:
                # Clean up the hangout number by removing # and ID# prefixes
                hangout_num = self.lhs.strip().replace("#", "").replace("ID", "")
                hangout_num = int(hangout_num)
            except ValueError:
                self.caller.msg("Please specify a valid hangout number.")
                return
                
            hangout = HangoutDB.objects.filter(id=hangout_num).first()
            if not hangout:
                self.caller.msg("Hangout not found.")
                return
                
            hangout.db.description = self.rhs.strip()
            self.caller.msg(f"Updated description for hangout {hangout_num}.")
            self.caller.msg(self.display_single_hangout(hangout, show_restricted=True))
            return
            
        if not self.args and "type" not in self.switches:
            # Basic hangout list
            hangouts = self.get_hangouts_by_district(self.caller, show_occupied="occupied" in self.switches)
            self.caller.msg(self.display_hangout_list(hangouts, show_restricted=True))
            return
            
        if "type" in self.switches:
            if not self.args:
                # Show category list
                self.caller.msg("Available categories:\n" + ", ".join(sorted(HANGOUT_CATEGORIES)))
                return
                
            category = self.args.strip().title()
            if category not in HANGOUT_CATEGORIES:
                self.caller.msg(f"Invalid category. Valid categories are: {', '.join(HANGOUT_CATEGORIES)}")
                return
                
            hangouts = self.get_hangouts_by_category(self.caller, category)
            self.caller.msg(self.display_hangout_list(hangouts, show_restricted=True))
            return
            
        # Handle viewing or jumping to specific hangout
        try:
            hangout_num = int(self.args)
        except ValueError:
            self.caller.msg("Please specify a valid hangout number.")
            return
            
        # Find the hangout
        hangout = HangoutDB.objects.filter(id=hangout_num).first()
        if not hangout or not hangout.can_see(self.caller):
            self.caller.msg("Hangout not found.")
            return
            
        if any(switch in self.switches for switch in ["jump", "tel", "join", "visit"]):
            # Teleport to hangout
            room = hangout.db.room
            if not room:
                self.caller.msg("That hangout's location is not set.")
                return
                
            self.caller.move_to(room, quiet=True)
            self.caller.msg(f"You jump to {hangout.key}.")
            room.msg_contents(f"{self.caller.name} appears.", exclude=[self.caller])
        else:
            # Display hangout details
            self.caller.msg(self.display_single_hangout(hangout, show_restricted=True))

class CmdSetHangout(MuxCommand):
    """
    Create or modify a hangout location.
    
    Usage:
        +sethangout <room> = <name>;<category>;<district>;<description>
        +sethangout/delete <number>
        +sethangout/restrict <number> = <splat,merit,faction>
        +sethangout/unrestrict <number>
        
    Creates or modifies a hangout entry for the specified room.
    The room can be specified by name or #dbref.
    
    Examples:
        +sethangout here = The Red Castle;Club;Hollywood;A laid back indie rock venue
        +sethangout/restrict 200 = Vampire,Status (Camarilla)
        +sethangout/unrestrict 200
        +sethangout/delete 200
    """
    
    key = "+sethangout"
    locks = "cmd:perm(Builder)"
    help_category = "Building and Housing"
    
    def func(self):
        """Execute command."""
        if not self.args:
            self.caller.msg("Usage: +sethangout <room> = <name>;<category>;<district>;<description>")
            return
            
        if "delete" in self.switches:
            try:
                hangout_num = int(self.args)
                hangout = HangoutDB.objects.filter(id=hangout_num).first()
                if not hangout:
                    self.caller.msg("Hangout not found.")
                    return
                    
                hangout.delete()
                self.caller.msg(f"Deleted hangout {hangout_num}.")
                return
            except ValueError:
                self.caller.msg("Please specify a valid hangout number.")
                return
                
        if "restrict" in self.switches:
            if not self.rhs:
                self.caller.msg("Usage: +sethangout/restrict <number> = <splat,merit,faction>")
                return
                
            try:
                hangout_num = int(self.lhs)
                hangout = HangoutDB.objects.filter(id=hangout_num).first()
                if not hangout:
                    self.caller.msg("Hangout not found.")
                    return
                    
                requirements = [r.strip() for r in self.rhs.split(",")]
                splats = []
                merits = []
                factions = []
                
                for req in requirements:
                    if req.lower().startswith(("vampire", "werewolf", "mage")):
                        splats.append(req)
                    elif req.lower().startswith("status"):
                        merits.append(req)
                    else:
                        factions.append(req)
                        
                hangout.db.restricted = True
                hangout.db.required_splats = splats
                hangout.db.required_merits = merits
                hangout.db.required_factions = factions
                
                self.caller.msg(f"Set restrictions for hangout {hangout_num}.")
                return
            except ValueError:
                self.caller.msg("Please specify a valid hangout number.")
                return
                
        if "unrestrict" in self.switches:
            try:
                hangout_num = int(self.args)
                hangout = HangoutDB.objects.filter(id=hangout_num).first()
                if not hangout:
                    self.caller.msg("Hangout not found.")
                    return
                    
                hangout.db.restricted = False
                hangout.db.required_splats = []
                hangout.db.required_merits = []
                hangout.db.required_factions = []
                
                self.caller.msg(f"Removed restrictions from hangout {hangout_num}.")
                return
            except ValueError:
                self.caller.msg("Please specify a valid hangout number.")
                return
                
        if not self.rhs:
            self.caller.msg("Usage: +sethangout <room> = <name>;<category>;<district>;<description>")
            return
            
        # Parse room
        if self.lhs.lower() == "here":
            room = self.caller.location
        else:
            room = self.caller.search(self.lhs)
        if not room:
            return
            
        # Parse hangout details
        try:
            name, category, district, description = [part.strip() for part in self.rhs.split(";")]
        except ValueError:
            self.caller.msg("Usage: +sethangout <room> = <name>;<category>;<district>;<description>")
            return
            
        # Validate category
        category = category.title()
        if category not in HANGOUT_CATEGORIES:
            self.caller.msg(f"Invalid category. Valid categories are: {', '.join(HANGOUT_CATEGORIES)}")
            return
            
        # Create or update hangout
        hangout = HangoutDB.create(
            key=name,
            room=room,
            category=category,
            district=district,
            description=description
        )
        
        self.caller.msg(f"Created hangout {hangout.id}: {name}")

class HangoutCmdSet(CmdSet):
    """
    Cmdset for hangout system.
    """
    
    def at_cmdset_creation(self):
        """Initialize command set."""
        self.add(CmdHangout())
        self.add(CmdSetHangout()) 