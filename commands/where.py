from evennia import default_cmds
from evennia.server.sessionhandler import SESSIONS
from evennia.utils.ansi import ANSIString
from world.wod20th.utils.formatting import header, footer, divider
from evennia.utils.evtable import EvTable
from collections import defaultdict

import time

class CmdWhere(default_cmds.MuxCommand):
    """
    Displays a list of online players and their locations.

    Usage:
        +where

    Shows all online players organized by location area, with idle times.
    Unfindable characters and those in unfindable rooms are hidden from non-staff.
    """

    key = "+where"
    aliases = ["where"]
    locks = "cmd:all()"
    help_category = "Game Info"

    def format_idle_time(self, idle_seconds):
        """Format idle time into a compact string."""
        if not idle_seconds:
            return "0s"
        if idle_seconds < 60:
            return f"{int(idle_seconds)}s"
        elif idle_seconds < 3600:
            return f"{int(idle_seconds/60)}m"
        elif idle_seconds < 86400:
            return f"{int(idle_seconds/3600)}h"
        elif idle_seconds < 604800:
            return f"{int(idle_seconds/86400)}d"
        else:
            return f"{int(idle_seconds/604800)}w"

    def get_idle_time(self, session):
        """Get idle time in seconds."""
        if not session:
            return 0
        return time.time() - session.cmd_last_visible

    def clean_area_name(self, name):
        """Clean up area name for display."""
        # Remove dbref if present
        if '(#' in name:
            name = name.split('(#')[0].strip()
        return name

    def get_area_name(self, location):
        """Extract area name from location."""
        if not location:
            return "Unknown"
            
        # First try to get the area from the room's attributes
        area = location.db.area
        if area:
            return self.clean_area_name(area)
            
        # If no area is set, try to get it from the room's zone
        if hasattr(location, 'zone') and location.zone:
            return self.clean_area_name(location.zone)
            
        # If it's Limbo, return Limbo
        if location.key == "Limbo":
            return "Limbo"
            
        # If no area/zone is set, use the room's full name
        if hasattr(location, 'key'):
            return self.clean_area_name(location.key)
            
        # Last resort
        return "Unknown"

    def format_name(self, puppet, session):
        """Helper function to consistently format names"""
        name = puppet.name
        
        # Add state indicators
        if puppet.tags.has("in_umbra", category="state"):
            name = f"@{name}"
        if puppet.db.lfrp:
            name = f"${name}"
        if puppet.check_permstring("builders"):
            name = f"*{name}"
        if puppet.db.afk:
            name = f"^{name}"
            
        # Apply colors
        if puppet.tags.has("in_umbra", category="state"):
            name = f"|b{name}|n"
        if puppet.db.lfrp:
            name = f"|y{name}|n"
            
        return name

    def func(self):
        """Implement the command"""
        caller = self.caller
        session_list = SESSIONS.get_sessions()
        is_staff = caller.check_permstring("builders")
        
        # Group characters by area
        areas = defaultdict(list)
        unfindable_chars = []
        
        # Build the output
        string = header("Player Locations", width=78) + "\n"
        string += "Parentheses indicate idle time.\n"
        string += "|r" + "-" * 78 + "|n\n"

        # Sort sessions by account name
        session_list = sorted(session_list, key=lambda o: o.account.key if o.account else "")

        # Collect character information
        for session in session_list:
            if not session.logged_in:
                continue
            
            puppet = session.get_puppet()
            if not puppet:
                continue

            # Skip if in dark mode (unless it's the viewer or both are staff)
            if puppet != caller:
                account = session.get_account()
                is_dark = (account.tags.get("dark_mode", category="staff_status") or 
                          puppet.tags.get("dark_mode", category="staff_status"))
                target_is_staff = (account.tags.get("staff", category="role") or 
                                 puppet.tags.get("staff", category="role"))
                if is_dark and not (is_staff and target_is_staff):
                    continue

            # Handle unfindable characters for everyone
            if puppet.db.unfindable:
                formatted_name = self.format_name(puppet, session)
                idle_str = self.format_idle_time(self.get_idle_time(session))
                unfindable_chars.append((formatted_name, idle_str))
                continue

            location = puppet.location
            if not location or (location.db.unfindable and not is_staff):
                continue

            area = self.get_area_name(location)
            idle_str = self.format_idle_time(self.get_idle_time(session))
            formatted_name = self.format_name(puppet, session)
            areas[area].append((formatted_name, idle_str))

        # Output characters by area
        for area in sorted(areas.keys()):
            if areas[area]:  # Only show areas with characters in them
                string += f"|c---< {area} >{'-' * (70 - len(area))}|n\n"
                # Format all players in this area as a comma-separated list
                players = [f"{name} ({idle})" for name, idle in sorted(areas[area])]
                string += "  " + ", ".join(players) + "\n"

        # Output unfindable characters section
        if unfindable_chars:
            string += f"\n|c---< Unfindable Characters >{'-' * (70 - len('Unfindable Characters'))}|n\n"
            players = [f"{name} ({idle})" for name, idle in sorted(unfindable_chars)]
            string += "  " + ", ".join(players) + "\n"

        # Legend
        string += "\n|r" + "-" * 78 + "|n"
        string += "\n|yLegend: ^ = AFK, * = Staff, |yYellow/$ = Looking for RP|n, |bBlue/@ = In Umbra|n"
        string += "\n|r" + "-" * 78 + "|n\n"

        string += footer(width=78)
        caller.msg(string)

