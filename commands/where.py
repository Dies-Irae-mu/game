from evennia import default_cmds
from evennia.server.sessionhandler import SESSIONS
from evennia.utils.ansi import ANSIString
from world.wod20th.utils.formatting import header
import time

class CmdWhere(default_cmds.MuxCommand):
    """
    Displays a list of online players and their locations.

    Usage:
        +where

    Shows all online players, their idle time, and their current location.
    """

    key = "+where"
    aliases = ["where"]
    locks = "cmd:all()"
    help_category = "General"

    def format_idle_time(self, idle_seconds):
        """
        Formats the idle time into human-readable format.
        """
        if idle_seconds < 60:
            return f"{int(idle_seconds)}s"
        elif idle_seconds < 3600:
            return f"{int(idle_seconds / 60)}m"
        elif idle_seconds < 86400:
            return f"{int(idle_seconds / 3600)}h"
        elif idle_seconds < 604800:
            return f"{int(idle_seconds / 86400)}d"
        else:
            return f"{int(idle_seconds / 604800)}w"

    def get_idle_time(self, character):
        """
        Get the idle time for a character.
        """
        if not character.sessions.count():
            return 0
        sessions = character.sessions.all()
        if sessions:
            # Get the most recent cmd_last_visible from all sessions
            return time.time() - max(session.cmd_last_visible for session in sessions)
        return 0

    def func(self):
        """
        Implement the command.
        """
        # Get all sessions
        sessions = SESSIONS.get_sessions()
        players = []
        unfindable = []

        for session in sessions:
            account = session.account
            if not account:
                continue
            character = session.puppet
            if character:
                idle_time = self.format_idle_time(self.get_idle_time(character))
                if character.location:
                    location = character.location.get_display_name(self.caller)
                    # Trim location name if too long
                    location = location[:46]
                    players.append({
                        'name': character.get_display_name(self.caller),
                        'idle': idle_time,
                        'location': location,
                        'is_builder': account.check_permstring("Builder"),
                    })
                else:
                    unfindable.append({
                        'name': character.get_display_name(self.caller),
                        'idle': idle_time,
                        'is_builder': account.check_permstring("Builder"),
                    })
            else:
                # Unfindable players (players without a character)
                unfindable.append({
                    'name': character.get_display_name(self.caller),
                    'idle': "N/A",
                    'is_builder': account.check_permstring("Builder"),
                })

        # Sort players
        players.sort(key=lambda x: x['name'].lower())
        unfindable.sort(key=lambda x: x['name'].lower())

        # Build the output
        output = ""
        output += header("+where", width=78, bcolor="|r", fillchar="|r-|n")
        output += ANSIString(" |wPLAYER|n").ljust(30) + ANSIString("|wIDLE|n").rjust(5) + "    " + ANSIString("|wLOCATION|n\n")
        output += "|r-|n" * 78 + "\n"
        # List of findable players
        for p in players:
            name = p['name'].ljust(28)
            idle = p['idle'].rjust(5) + "   "
            location = p['location']
            output += f" {name} {idle} {location}\n"

        output += "|r-|n" * 78 + "\n"

        # Unfindable players
        if unfindable:
            output += " Unfindable players:\n"
            # Group unfindable players into groups of four per line
            line = ""
            count = 0
            for p in unfindable:
                name = p['name']
                idle = p['idle']
                entry = f"{name} {idle}".ljust(18)
                line += entry
                count += 1
                if count % 4 == 0:
                    output += line.rstrip() + "\n"
                    line = ""
            if line:
                output += line.rstrip() + "\n"

        total_players = len(players) + len(unfindable)
        if len(unfindable) > 0:
            output += "|r-|n" * 78 + "\n"

        output += f"                          There are |y{total_players}|n players online.\n"
        output += "|r=|n" * 78 + "\n"

        # Send output to caller
        self.caller.msg(output)