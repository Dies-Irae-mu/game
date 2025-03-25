from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.ansi import ANSIString
from evennia.utils.utils import crop, time_format
from world.wod20th.utils.formatting import header, footer, divider
from world.wod20th.utils.time_utils import TIME_MANAGER
from evennia.utils.search import search_object
from time import time
import datetime
import re
from typeclasses.characters import Character
import pytz

class CmdFinger(MuxCommand):
    """
    View or set finger information about a character.
    
    Usage:
      +finger <character>
      +finger/set <field>=<value>
    
    The +finger command displays public information about a character,
    including their RP preferences, online times, and other IC/OOC details.
    
    Standard information shown includes:
    - Character's full name and current activity status
    - Player status (approved/unapproved) and alias
    - Online times and pronouns
    - RP preferences
    - Character page information (played by, apparent age, RP hooks, soundtrack)
    - Wiki page URL
    
    To set your own finger information, use +finger/set:
      +finger/set rp_preferences=Anything goes, but prefer dark themes
      +finger/set online_times=8:30 or 9pm PDT Sunday-Saturday
      +finger/set pronouns=She/They
      +finger/set alias=Nic
      +finger/set rumors=Apparently has connections to the Prince
      +finger/set ic_job=Owner of The Lost and Found
      
    Timezone Settings:
      You can set your timezone using common abbreviations or location codes:
      +finger/set timezone=PST     (Pacific Standard Time)
      +finger/set timezone=EST     (Eastern Standard Time)
      +finger/set timezone=GMT     (Greenwich Mean Time)
      +finger/set timezone=UTC     (Coordinated Universal Time)
      
      Or use location codes:
      +finger/set timezone=US-East
      +finger/set timezone=EU-Central
      +finger/set timezone=Japan
    
    You can create any custom field by using +finger/set <fieldname>=<value>.
    Set a field to @@ to hide it.
    
    Note: Some information like the wiki URL, played by, apparent age, RP hooks,
    and soundtrack are automatically pulled from your character's page and cannot
    be set using +finger/set.
    """
    
    key = "+finger"
    aliases = ["finger", "&finger_*"]
    locks = "cmd:all()"
    help_category = "Chargen & Character Info"

    def format_soundtrack(self, text):
        """
        Format soundtrack entries to preserve links and text.
        
        Args:
            text (str): Text containing HTML links
            
        Returns:
            str: Formatted text with URLs and their descriptions
        """
        if not text:
            return ""
            
        # Split into lines to handle multiple entries
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Extract URL and text from <a> tags
            link_match = re.search(r'<a href="([^"]+)"[^>]*>(.*?)</a>', line)
            if link_match:
                url = link_match.group(1)
                # Extract text and clean any remaining HTML tags
                content = re.sub(r'<[^>]+>', '', link_match.group(2))
                formatted_lines.append(f"{url} {content}")
            else:
                # If no link found, just clean the HTML
                cleaned = re.sub(r'<[^>]+>', '', line)
                if cleaned.strip():
                    formatted_lines.append(cleaned)
        
        return '\n'.join(formatted_lines)

    def strip_html(self, text):
        """
        Strip HTML tags from text while preserving line breaks and meaningful content.
        
        Args:
            text (str): Text to clean
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
            
        # Convert <br> and </p> to newlines
        text = re.sub(r'<br\s*/?>|</p>', '\n', text)
        
        # Remove all HTML tags but preserve their content
        text = re.sub(r'<[^>]+>', '', text)
        
        # Fix any excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Strip leading/trailing whitespace
        return text.strip()

    def get_idle_time(self, target):
        """
        Calculate idle time in seconds. Returns None if offline.
        """
        # Check if account is connected
        if not target.sessions.count():
            return None
            
        session = target.sessions.all()[0]
        if not session:
            return None
            
        current_time = time()
        last_cmd_time = session.cmd_last_visible
        if last_cmd_time:
            return int(current_time - last_cmd_time)
        return None

    def get_last_online(self, target):
        """
        Get the last time the character was online.
        Returns None if the character is currently online or the
        information is not available.
        """
        # If the character is online, return None
        if target.sessions.count():
            return None
            
        # Get the last_disconnect attribute
        last_disconnect = target.attributes.get("last_disconnect", None)
        return last_disconnect

    def format_idle_time(self, seconds):
        """Format idle time into a readable string."""
        if seconds is None:
            return "OFFLINE"
            
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return f"{seconds}s"

    def format_last_online(self, timestamp, target):
        """Format last online time into a readable string.
        
        Args:
            timestamp (float): The timestamp to format
            target (Character): The character being fingered (not used for timezone)
        """
        if timestamp is None:
            return "OFFLINE"
            
        # Create datetime in UTC
        utc_dt = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
        
        # Get the caller's timezone
        caller_tz_name = self.caller.attributes.get("timezone", "UTC")
        try:
            # Try to get the timezone from pytz
            tz = pytz.timezone(TIME_MANAGER.normalize_timezone_name(caller_tz_name))
            # Convert to the caller's timezone
            local_dt = utc_dt.astimezone(tz)
            # Format without timezone indicator
            time_str = local_dt.strftime("%Y-%m-%d %H:%M")
        except (pytz.exceptions.UnknownTimeZoneError, AttributeError, ValueError):
            # Fallback to UTC if there's any error
            time_str = utc_dt.strftime("%Y-%m-%d %H:%M")
            
        return f"OFFLINE (Last: {time_str})"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: +finger <character> or +finger/set <field>=<value>")
            return

        # Handle setting finger information
        if self.switches and "set" in self.switches:
            if "=" not in self.args:
                self.caller.msg("Usage: +finger/set <field>=<value>")
                return
                
            field, value = self.args.split("=", 1)
            field = field.strip().lower()
            value = value.strip()
            
            # Special handling for timezone setting
            if field == "timezone":
                # Try to validate the timezone
                normalized_tz = TIME_MANAGER.normalize_timezone_name(value)
                if not normalized_tz:
                    self.caller.msg(f"Invalid timezone: {value}. Please use a valid timezone abbreviation (PST, EST, GMT, etc.) or location code (US-East, EU-Central, etc.)")
                    return
                try:
                    # Test if it's a valid timezone
                    pytz.timezone(normalized_tz)
                    # Store both the user's input and the normalized version
                    self.caller.attributes.add("timezone", value.upper())  # Store original input
                    self.caller.msg(f"Set timezone to: {value.upper()}")
                    return
                except pytz.exceptions.UnknownTimeZoneError:
                    self.caller.msg(f"Invalid timezone: {value}. Please use a valid timezone abbreviation (PST, EST, GMT, etc.) or location code (US-East, EU-Central, etc.)")
                    return
            
            # If value is empty or @@, remove the attribute
            if not value or value == "@@":
                self.caller.attributes.remove(f"finger_{field}")
                self.caller.msg(f"Removed finger_{field}")
            else:
                # Set the attribute
                self.caller.attributes.add(f"finger_{field}", value)
                self.caller.msg(f"Set finger_{field} to: {value}")
            return

        # Handle old &finger_ syntax for backward compatibility
        if self.raw_string.startswith("&finger_"):
            if "=" not in self.raw_string:
                self.caller.msg("Usage: +finger/set <field>=<value>")
                return
                
            field = self.raw_string[7:].split(" ")[0]
            _, value = self.raw_string.split("=", 1)
            value = value.strip()
            
            # If value is empty or @@, remove the attribute
            if not value or value == "@@":
                self.caller.attributes.remove(f"finger_{field.lower()}")
                self.caller.msg(f"Removed finger_{field}")
            else:
                # Set the attribute
                self.caller.attributes.add(f"finger_{field.lower()}", value)
                self.caller.msg(f"Set finger_{field} to: {value}")
            return

        # Handle '+finger me'
        if self.args.lower().strip() == "me":
            target = self.caller
        else:
            # Clean up the search term by removing quotes
            search_term = self.args.strip("'\"").strip()
            
            # First try direct name match, restricting to Character typeclass
            target = self.caller.search(search_term, global_search=True, typeclass=Character)
            
            # If no direct match or search failed, try alias
            if not target:
                target = Character.get_by_alias(search_term.lower())

            if not target:
                self.caller.msg(f"Could not find a character named '{search_term}'.")
                return
            
            # Double check that we have a Character
            if not isinstance(target, Character):
                self.caller.msg(f"'{search_term}' is not a valid character.")
                return

        # Get basic character info - modified to handle None case
        try:
            full_name = target.db.stats.get('identity', {}).get('personal', {}).get('Full Name', {}).get('perm', target.key)
            if full_name is None:
                full_name = target.key
        except AttributeError:
            full_name = target.key
        
        # Calculate idle time
        idle_seconds = self.get_idle_time(target)
        
        # Get either idle time or last online time if offline
        if idle_seconds is not None:
            idle_str = self.format_idle_time(idle_seconds)
        else:
            last_online = self.get_last_online(target)
            idle_str = self.format_last_online(last_online, target)
        
        # Start building the display with blue dashes
        string = ANSIString("|b=|n" * 78 + "\n")
        
        # Header line with name and idle time
        name_display = f"{target.get_display_name(self.caller)}'s +finger"
        string += f"|y{name_display:^78}|n\n"
        
        # Full name and idle time line
        string += f"|wFull Name|n: {full_name:<20} | |wActivity|n: {idle_str}\n"
        
        # Red divider line
        string += ANSIString("|b=|n" * 78 + "\n")
        
        # Status and Alias line
        status = "Approved Player" if target.db.approved else "Unapproved Player"
        alias = target.attributes.get("alias", "")
        string += f"|wStatus|n: {status:<23} | |wAlias|n: {alias}\n"
        
        string += ANSIString("|b=|n" * 78 + "\n")
        
        # Standard fields
        fields = [
            ('Online Times', target.attributes.get("finger_online_times", "")),
            ('Pronouns', target.attributes.get("finger_pronouns", "")),
            ('RP Preferences', target.attributes.get("finger_rp_preferences", "")),
            # Character page attributes
            ('Played By', target.attributes.get("appears_as", "")),
            ('Apparent Age', target.attributes.get("apparent_age", "")),
            ('RP Hooks', self.strip_html(target.attributes.get("rp_hooks", ""))),
            ('Soundtrack', self.format_soundtrack(target.attributes.get("soundtrack", ""))),
            # Wiki URL
            ('Wiki', f"https://diesiraemu.com/characters/detail/{target.id}/{target.id}/"),
        ]
        
        for field, value in fields:
            if value:  # Only display fields that have values
                # Format multi-line fields appropriately
                if isinstance(value, str) and '\n' in value:
                    string += f"|w{field}|n:\n{value}\n"
                else:
                    string += f"|w{field}|n: {value}\n"
        
        # Get remaining custom fields
        custom_fields = {}
        for attr in target.attributes.all():
            if (attr.key.startswith("finger_") and 
                attr.key[7:] not in ['alias', 'online_times', 'pronouns', 'rp_preferences'] and 
                attr.value != "@@"):
                custom_fields[attr.key[7:]] = self.strip_html(attr.value)
        
        # Add custom fields if they exist
        if custom_fields:
            string += "\n"  # Add blank line before custom fields
            for field, value in sorted(custom_fields.items()):
                field_name = field.replace('_', ' ').title()
                string += f"|w{field_name}|n: {value}\n"
        
        # Bottom border
        string += ANSIString("|b=|n" * 78 + "\n")
        
        self.caller.msg(string)

    def at_pre_cmd(self):
        """Handle the &finger_<field> me=<value> syntax"""
        if self.raw_string.startswith("&finger_"):
            try:
                field = self.raw_string[7:].split(" ")[0]
                if "=" not in self.raw_string:
                    self.caller.msg("Usage: &finger_<field> me=<value>")
                    return True
                
                target, value = self.raw_string.split("=", 1)
                target = target.split(" ")[-1].strip()
                
                if target.lower() != "me":
                    self.caller.msg("You can only set your own finger information.")
                    return True
                
                self.caller.attributes.add(f"finger_{field.lower()}", value.strip())
                self.caller.msg(f"Set finger_{field} to: {value.strip()}")
                return True
                
            except Exception as e:
                self.caller.msg(f"Error setting finger field: {str(e)}")
                return True
        
        return False 