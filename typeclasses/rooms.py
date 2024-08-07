from evennia import DefaultRoom
from evennia.utils.ansi import ANSIString
from world.wod20th.utils.ansi_utils import wrap_ansi
from world.wod20th.utils.formatting import header, footer, divider

class RoomParent(DefaultRoom):

    def get_display_name(self, looker, **kwargs):
        """
        Get the name to display for the character.
        """
        
        name = self.key
        
        if self.db.gradient_name:
            name = ANSIString(self.db.gradient_name)
            if looker.check_permstring("builders"):
                name += f"({self.dbref})"
            return name
        
        # If the looker is builder+ show the dbref
        if looker.check_permstring("builders"):
            name += f"({self.dbref})"

        return name

    def return_appearance(self, looker, **kwargs):
        if not looker:
            return ""

        name = self.get_display_name(looker, **kwargs)
        desc = self.db.desc

        # Header with room name
        
        string = header(name, width=78, bcolor="|r", fillchar=ANSIString("|r-|n")) + "\n"
        
        # Optional: add custom room description here if available
        if desc:
            string += wrap_ansi(desc, 78, left_padding=1) + "\n\n"

        # List all characters in the room
        characters = [obj for obj in self.contents if obj.has_account]
        if characters:
            string += divider("Characters", width=78, fillchar=ANSIString("|r-|n")) + "\n"
            for character in characters:
                idle_time = self.idle_time_display(character.idle_time)
                if character == looker:
                    idle_time = self.idle_time_display(0)

                shortdesc = character.db.shortdesc
                if shortdesc:
                    shortdesc_str = f"{shortdesc}"
                else:
                    shortdesc_str ="|h|xType '|n+shortdesc <desc>|h|x' to set a short description.|n"

                if len(ANSIString(shortdesc_str).strip()) > 43:
                    shortdesc_str = ANSIString(shortdesc_str)[:43]
                    shortdesc_str = ANSIString(shortdesc_str[:-3] + "...|n")
                else:
                    shortdesc_str = ANSIString(shortdesc_str).ljust(43, ' ')
                
                string += ANSIString(f" {character.get_display_name(looker).ljust(25)} {ANSIString(idle_time).rjust(7)}|n {shortdesc_str}\n")

        # List all objects in the room
        objects = [obj for obj in self.contents if not obj.has_account and not obj.destination]
        if objects:
            string += divider("Objects", width=78, fillchar=ANSIString("|r-|n")) + "\n"
            
            # get shordesc or dhoe s blsnk string
            for obj in objects:
                if obj.db.shortdesc:
                    shortdesc = obj.db.shortdesc
                else:
                    shortdesc = ""


            # if looker builder+ show dbref.

                string +=" "+  ANSIString(f"{obj.get_display_name(looker)}").ljust(25) + ANSIString(f"{shortdesc}") .ljust(53, ' ') + "\n"

        # List all exits
        exits = [ex for ex in self.contents if ex.destination]
        if exits:
            string += divider("Exits", width=78, fillchar=ANSIString("|r-|n")) + "\n"
            exit_strings = []
            for exit in exits:
                aliases = exit.aliases.all()
                exit_name = exit.get_display_name(looker)
                exit_strings.append(ANSIString(f" <|y{aliases[0].upper()}|n> {exit_name}"))

            # Split into two columns
            half = (len(exit_strings) + 1) // 2
            col1 = exit_strings[:half]
            col2 = exit_strings[half:]

            # Create two-column format
            for i in range(max(len(col1), len(col2))):
                col1_str = col1[i] if i < len(col1) else ANSIString("")
                col2_str = col2[i] if i < len(col2) else ANSIString("")
                string += f"{col1_str.ljust(38)} {col2_str}\n"

        string += footer(width=78, fillchar=ANSIString("|r-|n"))

        return string

    def idle_time_display(self, idle_time):
        """
        Formats the idle time display.
        """
        idle_time = int(idle_time)  # Convert to int
        if idle_time < 60:
            time_str = f"{idle_time}s"
        elif idle_time < 3600:
            time_str = f"{idle_time // 60}m"
        else:
            time_str = f"{idle_time // 3600}h"

        # Color code based on idle time intervals
        if idle_time < 900:  # less than 15 minutes
            color = "|g"  # green
        elif idle_time < 1800:  # 15-30 minutes
            color = "|y"  # yellow
        elif idle_time < 2700:  # 30-45 minutes
            color = "|o"  # orange
        elif idle_time < 3600:
            color = "|r"  # red
        else:
            color = "|h|x"
        

        return f"{color}{time_str}|n"
