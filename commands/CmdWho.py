from datetime import datetime, timedelta
import pytz
import ephem
from evennia.utils.ansi import ANSIString
from evennia import default_cmds
from world.wod20th.utils import ansi_utils
import time
from evennia import SESSION_HANDLER as evennia
from evennia.utils import utils
from world.wod20th.utils.formatting import header, footer, divider
from evennia.utils.utils import class_from_module
from evennia.utils.ansi import strip_ansi
from django.conf import settings
from world.wod20th.utils.vampire_utils import CLAN_CHOICES
from world.wod20th.utils.mage_utils import TRADITION, CONVENTION, NEPHANDI_FACTION
from world.wod20th.utils.shifter_utils import GAROU_TRIBE_CHOICES
from world.wod20th.utils.changeling_utils import KITH
from world.wod20th.utils.mortalplus_utils import MORTALPLUS_TYPE_CHOICES

COMMAND_DEFAULT_CLASS = class_from_module(settings.COMMAND_DEFAULT_CLASS)

class CmdWho(COMMAND_DEFAULT_CLASS):
    """
    list who is currently online, showing character names

    Usage:
      who
      doing

    Shows who is currently online using character names instead of account names.
    'doing' is an alias that limits info also for those with all permissions.
    """

    key = "who"
    aliases = ["doing"]
    locks = "cmd:all()"
    account_caller = False  # important for Account commands
    help_category = "Game Info"

    def format_name(self, puppet, account):
        """Helper function to format character names consistently"""
        if puppet:
            # Get display name but strip any existing ANSI formatting
            display_name = puppet.get_display_name(account)
            clean_name = strip_ansi(display_name)
            
            # Add indicators using tags
            name_suffix = ""
            if puppet.check_permstring("builders"):
                name_suffix += f"*{name_suffix}"
            if puppet.tags.has("in_umbra", category="state"):
                name_suffix = f"@{name_suffix}"
            if puppet.db.lfrp:
                name_suffix = f"${name_suffix}"
            
            # For debugging
            # self.msg(f"Tags for {puppet.key}: {puppet.tags.all()}")
            
            # If no prefix, add a space to maintain alignment
            name_suffix = name_suffix or " "
            
            # Add the dbref
            name = f"{name_suffix}{clean_name}"
            return utils.crop(name, width=17)
        return "None".ljust(17)

    def get_location_display(self, puppet, account):
        """Helper function to format location display, respecting unfindable status"""
        if not puppet or not puppet.location:
            return "None"
            
        # Check if character is unfindable
        if hasattr(puppet, 'db') and puppet.db.unfindable and not account.check_permstring("Builder"):
            return "(Hidden)"
            
        # Staff can always see room names
        if account.check_permstring("Builder"):
            return puppet.location.key
            
        # Check if room is unfindable
        if hasattr(puppet.location, 'db') and puppet.location.db.unfindable:
            return "(Hidden)"
            
        return puppet.location.key

    def func(self):
        """
        Get all connected accounts by polling session.
        """
        account = self.account
        session_list = evennia.get_sessions()
        is_staff = account.check_permstring("builders")  # Check if viewer is staff

        session_list = sorted(session_list, key=lambda o: o.get_puppet().key if o.get_puppet() else o.account.key)

        if self.cmdstring == "doing":
            show_session_data = False
        else:
            show_session_data = account.check_permstring("Developer") or account.check_permstring(
                "Admins"
            )

        naccounts = evennia.account_count()
        if show_session_data:
            # privileged info
            string = header("Online Characters", width=78) + "\n"
            string += "|wName              On       Idle     Account     Room            Cmds  Host|n\n"
            string += "|r" + "-" * 78 + "|n\n"
            
            for session in session_list:
                if not session.logged_in:
                    continue
                delta_cmd = time.time() - session.cmd_last_visible
                delta_conn = time.time() - session.conn_time
                session_account = session.get_account()
                puppet = session.get_puppet()
                
                # Skip if in dark mode (unless it's the viewer or both are staff)
                if puppet and puppet != self.caller:
                    is_dark = (session_account.tags.get("dark_mode", category="staff_status") or 
                             (puppet and puppet.tags.get("dark_mode", category="staff_status")))
                    target_is_staff = (session_account.tags.get("staff", category="role") or 
                                     (puppet and puppet.tags.get("staff", category="role")))
                    if is_dark and not (is_staff and target_is_staff):
                        continue
                
                location = self.get_location_display(puppet, account)
                
                string += " %-17s %-8s %-8s %-10s %-15s %-5s %s\n" % (
                    self.format_name(puppet, account),
                    utils.time_format(delta_conn, 0),
                    utils.time_format(delta_cmd, 1),
                    utils.crop(session_account.get_display_name(account), width=10),
                    utils.crop(location, width=15),
                    str(session.cmd_total).ljust(5),
                    isinstance(session.address, tuple) and session.address[0] or session.address
                )
        else:
            # unprivileged
            string = header("Online Characters", width=78) + "\n"
            string += "|wName              On       Idle     Room|n\n"
            string += "|r" + "-" * 78 + "|n\n"
            
            for session in session_list:
                if not session.logged_in:
                    continue
                delta_cmd = time.time() - session.cmd_last_visible
                delta_conn = time.time() - session.conn_time
                puppet = session.get_puppet()
                session_account = session.get_account()
                
                # Skip if in dark mode (unless it's the viewer or both are staff)
                if puppet and puppet != self.caller:
                    is_dark = (session_account.tags.get("dark_mode", category="staff_status") or 
                             (puppet and puppet.tags.get("dark_mode", category="staff_status")))
                    target_is_staff = (session_account.tags.get("staff", category="role") or 
                                     (puppet and puppet.tags.get("staff", category="role")))
                    if is_dark and not (is_staff and target_is_staff):
                        continue
                
                location = self.get_location_display(puppet, account)
                
                string += " %-17s %-8s %-8s %s\n" % (
                    self.format_name(puppet, account),
                    utils.time_format(delta_conn, 0),
                    utils.time_format(delta_cmd, 1),
                    utils.crop(location, width=25)
                )

        is_one = naccounts == 1
        string += "|r" + "-" * 78 + "|n\n"
        string += f"{naccounts} unique account{'s' if not is_one else ''} logged in.\n"
        string += "|r" + "-" * 78 + "|n\n"
        string += "|yLegend: * = Staff, $ = Looking for RP, @ = In Umbra|n\n"  # Fixed legend formatting
        string += "|r" + "-" * 78 + "|n\n"
        string += footer(width=78)
        
        self.msg(string)

class CmdCensus(COMMAND_DEFAULT_CLASS):
    """
    Show a census of the current population in the game.
    +census will show a list of different splats and their counts.
    +census/<splat> will show a list of clans, traditions, tribes, etc. from that splat.
    +census/<stat_category> will show a list of how many players have a particular stat in a category.

    Usage:
      +census           
      +census/vampire - Shows a list of vampire clans and their player counts.
      +census/shifter - Shows a list of shifter types and their player counts.
      +census/garou - Shows a list of Garou tribes and their player counts.
      +census/mage - Shows a list of Mage traditions, affiliations, and their player counts.
      +census/mortal+ - Shows a list of Mortal+ types (sorcerer, kinfolk, psychic, etc.) and their player counts.
      +census/changeling - shows a list of Changeling kiths, courts, and their player counts.
      +census/discipline - Shows a list of Vampire disciplines and their player counts.
      +census/spheres - Shows a list of Mage spheres and their player counts.
    """
    key = "+census"
    aliases = ["census"]
    locks = "cmd:all()"
    help_category = "Game Info"

    def get_splat_counts(self):
        """Get counts of approved characters by splat type."""
        from evennia.objects.models import ObjectDB
        from collections import defaultdict
        
        VALID_SPLATS = {
            'vampire': 'Vampire',
            'mage': 'Mage',
            'shifter': 'Shifter',
            'changeling': 'Changeling',
            'mortal+': 'Mortal+',
            'mortal': 'Mortal',
            'companion': 'Companion',
            'possessed': 'Possessed'
        }
        
        splat_counts = defaultdict(int)
        characters = ObjectDB.objects.filter(
            db_typeclass_path__contains='typeclasses.characters.Character'
        )
        
        for char in characters:
            if not hasattr(char, 'db') or not char.db.stats or not char.db.approved:
                continue
                
            splat = char.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            if not splat or splat.lower() in ['none', 'unknown']:
                continue
                
            normalized_splat = VALID_SPLATS.get(splat.lower(), splat)
            splat_counts[normalized_splat] += 1
                
        return dict(splat_counts)

    def get_mage_counts(self):
        """Get counts of approved mage characters by tradition."""
        from evennia.objects.models import ObjectDB
        from collections import defaultdict
        
        VALID_AFFILIATIONS = {}
        for tradition in TRADITION:
            VALID_AFFILIATIONS[tradition.lower()] = tradition
        for convention in CONVENTION:
            VALID_AFFILIATIONS[convention.lower()] = convention
        for faction in NEPHANDI_FACTION:
            VALID_AFFILIATIONS[faction.lower()] = faction
        
        mage_counts = defaultdict(int)
        mages = ObjectDB.objects.filter(
            db_typeclass_path__contains='typeclasses.characters.Character'
        )
        
        for char in mages:
            if not hasattr(char, 'db') or not char.db.stats or not char.db.approved:
                continue
                
            splat = char.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            if splat == 'Mage':
                tradition = char.db.stats.get('identity', {}).get('lineage', {}).get('Tradition', {}).get('perm', '')
                if not tradition or tradition.lower() in ['none', 'unknown']:
                    continue
                
                normalized_trad = VALID_AFFILIATIONS.get(tradition.lower(), tradition)
                mage_counts[normalized_trad] += 1
                    
        return dict(mage_counts)

    def get_mortal_counts(self):
        """Get counts of approved mortal+ characters by type."""
        from evennia.objects.models import ObjectDB
        from collections import defaultdict
        
        VALID_TYPES = {choice[0].lower(): choice[1] for choice in MORTALPLUS_TYPE_CHOICES}
        
        mortal_counts = defaultdict(int)
        mortals = ObjectDB.objects.filter(
            db_typeclass_path__contains='typeclasses.characters.Character'
        )
        
        for char in mortals:
            if not hasattr(char, 'db') or not char.db.stats or not char.db.approved:
                continue
                
            splat = char.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            if splat == 'Mortal+':
                type = char.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
                if not type or type.lower() in ['none', 'unknown']:
                    continue
                
                normalized_type = VALID_TYPES.get(type.lower(), type)
                mortal_counts[normalized_type] += 1
                    
        return dict(mortal_counts)

    def get_changeling_counts(self):
        """Get counts of approved changeling characters by kith."""
        from evennia.objects.models import ObjectDB
        from collections import defaultdict
        
        VALID_KITHS = {kith.lower(): kith for kith in KITH}
        
        changeling_counts = defaultdict(int)
        changelings = ObjectDB.objects.filter(
            db_typeclass_path__contains='typeclasses.characters.Character'
        )
        
        for char in changelings:
            if not hasattr(char, 'db') or not char.db.stats or not char.db.approved:
                continue
                
            splat = char.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            if splat == 'Changeling':
                kith = char.db.stats.get('identity', {}).get('lineage', {}).get('Kith', {}).get('perm', '')
                if not kith or kith.lower() in ['none', 'unknown']:
                    continue
                
                normalized_kith = VALID_KITHS.get(kith.lower(), kith)
                changeling_counts[normalized_kith] += 1
                    
        return dict(changeling_counts)

    def get_vampire_clans(self):
        """Get counts of approved vampire characters by clan."""
        from evennia.objects.models import ObjectDB
        from collections import defaultdict
        
        VALID_CLANS = {choice[0].lower(): choice[1] for choice in CLAN_CHOICES}
        
        clan_counts = defaultdict(int)
        vampires = ObjectDB.objects.filter(
            db_typeclass_path__contains='typeclasses.characters.Character'
        )
        
        for char in vampires:
            if not hasattr(char, 'db') or not char.db.stats or not char.db.approved:
                continue
                
            splat = char.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            if splat == 'Vampire':
                clan = char.db.stats.get('identity', {}).get('lineage', {}).get('Clan', {}).get('perm', '')
                if not clan or clan.lower() in ['none', 'unknown']:
                    continue
                
                normalized_clan = VALID_CLANS.get(clan.lower(), clan)
                clan_counts[normalized_clan] += 1
                    
        return dict(clan_counts)

    def get_shifter_types(self):
        """Get counts of approved shifter characters by type."""
        from evennia.objects.models import ObjectDB
        from collections import defaultdict
        
        type_counts = defaultdict(int)
        shifters = ObjectDB.objects.filter(
            db_typeclass_path__contains='typeclasses.characters.Character'
        )
        
        for char in shifters:
            if not hasattr(char, 'db') or not char.db.stats or not char.db.approved:
                continue
                
            splat = char.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            if splat == 'Shifter':
                shifter_type = char.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', 'Unknown')
                type_counts[shifter_type] += 1
                    
        return dict(type_counts)

    def get_garou_tribes(self):
        """Get counts of approved Garou characters by tribe."""
        from evennia.objects.models import ObjectDB
        from collections import defaultdict
        
        VALID_TRIBES = {choice[0].lower(): choice[1] for choice in GAROU_TRIBE_CHOICES}
        
        tribe_counts = defaultdict(int)
        shifters = ObjectDB.objects.filter(
            db_typeclass_path__contains='typeclasses.characters.Character'
        )
        
        for char in shifters:
            if not hasattr(char, 'db') or not char.db.stats or not char.db.approved:
                continue
                
            splat = char.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            if splat != 'Shifter':
                continue
                
            shifter_type = char.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
            if shifter_type != 'Garou':
                continue
                
            tribe = char.db.stats.get('identity', {}).get('lineage', {}).get('Tribe', {}).get('perm', '')
            if not tribe or tribe.lower() in ['none', 'unknown']:
                continue
                
            normalized_tribe = VALID_TRIBES.get(tribe.lower(), tribe)
            tribe_counts[normalized_tribe] += 1
                    
        return dict(tribe_counts)

    def get_discipline_counts(self):
        """Get counts of approved characters with each discipline."""
        from evennia.objects.models import ObjectDB
        from collections import defaultdict
        
        discipline_counts = defaultdict(int)
        vampires = ObjectDB.objects.filter(
            db_typeclass_path__contains='typeclasses.characters.Character'
        )
        
        for char in vampires:
            if not hasattr(char, 'db') or not char.db.stats or not char.db.approved:
                continue
                
            splat = char.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            if splat in ['Vampire', 'Mortal+']:  # Include ghouls
                disciplines = char.db.stats.get('powers', {}).get('discipline', {})
                for discipline, value in disciplines.items():
                    if value.get('perm', 0) > 0:
                        discipline_counts[discipline] += 1
                    
        return dict(discipline_counts)

    def get_merit_counts(self):
        """Get counts of approved characters with each merit."""
        from evennia.objects.models import ObjectDB
        from collections import defaultdict
        
        merit_counts = defaultdict(int)
        characters = ObjectDB.objects.filter(
            db_typeclass_path__contains='typeclasses.characters.Character'
        )
        
        for char in characters:
            if not hasattr(char, 'db') or not char.db.stats or not char.db.approved:
                continue
                
            merits = char.db.stats.get('merits', {}).get('merit', {})
            for merit, value in merits.items():
                if value.get('perm', 0) > 0:
                    merit_counts[merit] += 1
                    
        return dict(merit_counts)

    def get_sphere_counts(self):
        """Get counts of approved mages with each sphere."""
        from evennia.objects.models import ObjectDB
        from collections import defaultdict
        
        sphere_counts = defaultdict(int)
        mages = ObjectDB.objects.filter(
            db_typeclass_path__contains='typeclasses.characters.Character'
        )
        
        for char in mages:
            if not hasattr(char, 'db') or not char.db.stats or not char.db.approved:
                continue
                
            splat = char.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            if splat == 'Mage':
                spheres = char.db.stats.get('powers', {}).get('sphere', {})
                for sphere, value in spheres.items():
                    if value.get('perm', 0) > 0:
                        sphere_counts[sphere] += 1
                    
        return dict(sphere_counts)

    def format_counts(self, counts, title):
        """Format the counts into a nice table with either 2 or 3 columns based on content."""
        if not counts:
            return f"No {title} found."
            
        # Sort by count (descending) then name
        sorted_items = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        
        # Calculate column widths
        name_width = max(len(str(name)) for name, _ in sorted_items)
        count_width = max(len(str(count)) for _, count in sorted_items)
        # Make sure we have minimum widths
        name_width = max(name_width, 10)
        count_width = max(count_width, 5)
        
        # Determine if we should use 2 or 3 columns based on the title
        use_two_columns = any(word.lower() in title.lower() for word in 
            ['vampire', 'shifter', 'garou', 'mage', 'changeling', 'mortal+'])
        
        # Calculate total width for each column (name + count + spacing)
        if use_two_columns:
            col_width = name_width + count_width + 2
        else:
            col_width = name_width + count_width + 2
        
        # Create the table
        table = [header(f"{title}", width=78)]
        
        # Split items into rows
        rows = []
        current_row = []
        max_cols = 2 if use_two_columns else 3
        
        for item in sorted_items:
            current_row.append(item)
            if len(current_row) == max_cols:
                rows.append(current_row)
                current_row = []
        
        # Add any remaining items
        if current_row:
            rows.append(current_row)
        
        # Format and add each row
        for row in rows:
            line = ""
            for i, (name, count) in enumerate(row):
                # Format each column with proper padding
                column = f"{str(name):<{name_width}} {count:>{count_width}}"
                # Add pipe after column unless it's the last column in the row
                if i < len(row) - 1:
                    line += f"{column} | "
                else:
                    # For last column in row, add pipe only if it's not a full row
                    line += f"{column}{' ' * (3 if len(row) == max_cols else 2) + ('|' if len(row) < max_cols else '')}"
            table.append(line.rstrip())
            
        # Add dividers
        table.insert(1, "|r" + "-" * 78 + "|n")
        table.append("|r" + "-" * 78 + "|n")
        table.append(footer(width=78))
        
        return "\n".join(table)

    def func(self):
        """Execute the census command."""
        if not self.switches:
            # Show overall population by splat
            counts = self.get_splat_counts()
            self.msg(self.format_counts(counts, "Character Types"))
            return
            
        switch = self.switches[0].lower()
        
        if switch == "vampire":
            counts = self.get_vampire_clans()
            self.msg(self.format_counts(counts, "Vampire Census"))
            
        elif switch == "shifter":
            counts = self.get_shifter_types()
            self.msg(self.format_counts(counts, "Shifter Census"))
            
        elif switch == "garou":
            counts = self.get_garou_tribes()
            self.msg(self.format_counts(counts, "Garou Census"))

        elif switch == "changeling":
            counts = self.get_changeling_counts()
            self.msg(self.format_counts(counts, "Changeling Census"))
            
        elif switch == "discipline":
            counts = self.get_discipline_counts()
            self.msg(self.format_counts(counts, "Disciplines"))
            
        elif switch == "merits":
            counts = self.get_merit_counts()
            self.msg(self.format_counts(counts, "Character Merits"))
            
        elif switch == "spheres":
            counts = self.get_sphere_counts()
            self.msg(self.format_counts(counts, "Mage Spheres"))

        elif switch == "mage":
            counts = self.get_mage_counts()
            self.msg(self.format_counts(counts, "Mage Census"))
            
        elif switch == "mortal+":
            counts = self.get_mortal_counts()
            self.msg(self.format_counts(counts, "Mortal+ Census"))
        else:
            self.msg("Invalid census type. Valid types are: vampire, shifter, garou, discipline, merits, spheres, changeling")
    
