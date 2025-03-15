from evennia import DefaultRoom
from evennia.utils.utils import make_iter, justify
from evennia.utils.ansi import ANSIString
from evennia.utils import ansi
from world.wod20th.utils.ansi_utils import wrap_ansi
from world.wod20th.utils.formatting import header, footer, divider
from datetime import datetime
import random
from evennia.utils.search import search_channel
import re

class RoomParent(DefaultRoom):

 
    def get_display_name(self, looker, **kwargs):
        """
        Get the name to display for the room.
        
        Args:
            looker (Object or str): The object or string looking at this room.
            **kwargs: Arbitrary keyword arguments.
            
        Returns:
            str: The display name of the room.
        """
        name = self.key
        
        if self.db.gradient_name:
            name = ANSIString(self.db.gradient_name)
            if hasattr(looker, 'check_permstring') and looker.check_permstring("builders"):
                name += f"({self.dbref})"
            return name
        
        # If the looker is builder+ show the dbref
        if hasattr(looker, 'check_permstring') and looker.check_permstring("builders"):
            name += f"({self.dbref})"

        # Add indicators for special realm rooms
        if self.db.umbra_only:
            name = f"|B[Umbral Realm]|n {name}"
        elif self.db.fae_only:
            name = f"|m[Dreaming]|n {name}"

        return name

    def can_perceive_fae(self, looker):
        """
        Check if a character can perceive the Dreaming.
        
        Args:
            looker (Object): The character attempting to perceive the room.
            
        Returns:
            bool: True if the character can perceive Dreaming, False otherwise.
        """
        if not looker:
            return False
            
        # Check if the character has stats
        if not hasattr(looker, 'db') or not looker.db.stats:
            return False

        # Get the character's splat
        splat = (looker.db.stats.get('other', {})
                              .get('splat', {})
                              .get('Splat', {})
                              .get('perm', ''))
                
        # Check if the character is a Changeling
        if splat == "Changeling":
            return True
            
        # Check if the character is Kinain
        if (splat == "Mortal+" and 
            looker.db.stats.get('identity', {})
                          .get('lineage', {})
                          .get('Mortal+ Type', {})
                          .get('perm', '') == "Kinain"):
            return True
            
        return False

    def return_appearance(self, looker, **kwargs):
        if not looker:
            return ""

        # Handle special realm rooms
        if self.db.umbra_only and not looker.tags.get("in_umbra", category="state"):
            return "This place exists only in the Umbra. You cannot perceive it from the material world."
        elif self.db.fae_only and not self.can_perceive_fae(looker):
            return "This place exists only in the Dreaming. You cannot perceive it with mortal eyes."

        name = self.get_display_name(looker, **kwargs)
        
        # Check if the looker is in the Umbra or peeking into it
        in_umbra = looker.tags.get("in_umbra", category="state")
        peeking_umbra = kwargs.get("peek_umbra", False)
        
        # Set color scheme based on realm type and state
        if self.db.fae_only:
            border_color = "|m"  # Magenta for Dreaming
        else:
            border_color = "|B" if (in_umbra or peeking_umbra) else "|r"
        
        # Choose the appropriate description
        if (in_umbra or peeking_umbra) and self.db.umbra_desc:
            desc = self.db.umbra_desc
        elif looker.tags.get("in_dreaming", category="state") and self.db.fae_desc:
            desc = self.db.fae_desc
        else:
            desc = self.db.desc

        # Update all dividers to use the new color scheme
        string = header(name, width=78, bcolor=border_color, fillchar=ANSIString(f"{border_color}-|n")) + "\n"
        
        # Process room description
        if desc:
            # Use format_description to handle the formatting
            formatted_desc = self.format_description(desc)
            if formatted_desc:
                string += formatted_desc + "\n"

        # List all characters in the room
        characters = []
        for obj in self.contents:
            if obj.has_account:
                # Check if they share the same reality layer
                if ((looker.tags.get("in_umbra", category="state") and obj.tags.get("in_umbra", category="state")) or
                    (looker.tags.get("in_material", category="state") and obj.tags.get("in_material", category="state")) or
                    (looker.tags.get("in_dreaming", category="state") and obj.tags.get("in_dreaming", category="state"))):
                    characters.append(obj)

        if characters:
            string += divider("Characters", width=78, fillchar=ANSIString(f"{border_color}-|n")) + "\n"
            for character in characters:
                idle_time = self.idle_time_display(character.idle_time)

                shortdesc = character.db.shortdesc
                if shortdesc:
                    shortdesc_str = f"{shortdesc}"
                else:
                    shortdesc_str = "|h|xType '+shortdesc <desc>' to set a short description.|n"

                # Format name and idle time with fixed widths
                name_part = ANSIString(f" {character.get_display_name(looker)}").ljust(20)
                idle_part = ANSIString(idle_time).rjust(4)
                
                # Ensure shortdesc doesn't exceed remaining space
                max_shortdesc_length = 52  # 78 - 20 (name) - 4 (idle) - 2 (spaces)
                if len(ANSIString(shortdesc_str)) > max_shortdesc_length:
                    shortdesc_str = ANSIString(shortdesc_str)[:max_shortdesc_length-3] + "..."
                
                # Combine all parts with proper spacing
                string += f"{name_part}{idle_part} {ANSIString(shortdesc_str)}\n"

        # List all objects in the room that are in the same reality layer
        objects = []
        for obj in self.contents:
            if not obj.has_account and not obj.destination:
                # Check if object is visible in current reality layer
                # If object has no reality layer tags, assume it's in material plane
                is_in_material = not (obj.tags.get("in_umbra", category="state") or 
                                    obj.tags.get("in_dreaming", category="state"))
                
                if ((looker.tags.get("in_umbra", category="state") and obj.tags.get("in_umbra", category="state")) or
                    (looker.tags.get("in_material", category="state") and (obj.tags.get("in_material", category="state") or is_in_material)) or
                    (looker.tags.get("in_dreaming", category="state") and obj.tags.get("in_dreaming", category="state"))):
                    objects.append(obj)

        if objects:
            string += divider("Objects", width=78, fillchar=ANSIString(f"{border_color}-|n")) + "\n"
            for obj in objects:
                if obj.db.shortdesc:
                    shortdesc = obj.db.shortdesc
                else:
                    shortdesc = ""
                string += " " + ANSIString(f"{obj.get_display_name(looker)}").ljust(25) + ANSIString(f"{shortdesc}").ljust(53, ' ') + "\n"

        # List all exits that are accessible in the current reality layer
        exits = []
        for ex in self.contents:
            if ex.destination and ex.access(looker, "view"):
                # Add logging to help diagnose visibility
                exits.append(ex)

        if exits:
            direction_strings = []
            exit_strings = []
            for exit in exits:
                aliases = exit.aliases.all() or []
                exit_name = exit.get_display_name(looker)
                short = min(aliases, key=len) if aliases else ""
                
                exit_string = ANSIString(f" <|y{short.upper()}|n> {exit_name}")
                
                if any(word in exit_name for word in ['Sector', 'District', 'Neighborhood']):
                    direction_strings.append(exit_string)
                else:
                    exit_strings.append(exit_string)

            # Display Directions
            if direction_strings:
                string += divider("Directions", width=78, fillchar=ANSIString(f"{border_color}-|n")) + "\n"
                string += self.format_exit_columns(direction_strings)

            # Display Exits
            if exit_strings:
                string += divider("Exits", width=78, fillchar=ANSIString(f"{border_color}-|n")) + "\n"
                string += self.format_exit_columns(exit_strings)

        # Get room type and resources
        room_type = self.db.roomtype or "Unknown"
        resources = self.db.resources
        resources_str = f"Res:{resources}" if resources is not None else ""

        # Create the footer with room type and resources
        footer_text = f"{resources_str}, {room_type}".strip(", ")
        
        # Add indicators for views and places if available
        indicators = []
        if hasattr(self.db, 'views') and self.db.views:
            indicators.append("+views set")
        if hasattr(self.db, 'places') and self.db.places:
            indicators.append("+places set")
            
        if indicators:
            footer_text += f" [{', '.join(indicators)}]"
            
        footer_length = len(ANSIString(footer_text))
        padding = 78 - footer_length - 2  # -2 for the brackets

        string += ANSIString(f"{border_color}{'-' * padding}[|c{footer_text}{border_color}]|n")

        # Add freezer warning if applicable
        if self.db.roomtype == "freezer":
            warning = "\n|r[FROZEN ROOM - No Speaking or Movement Allowed]|n\n"
            # Insert warning after the room name but before description
            lines = string.split('\n')
            lines.insert(2, warning)  # Insert after header
            string = '\n'.join(lines)

        return string

    def format_exit_columns(self, exit_strings):
        # Split into two columns
        half = (len(exit_strings) + 1) // 2
        col1 = exit_strings[:half]
        col2 = exit_strings[half:]

        # Create two-column format
        formatted_string = ""
        for i in range(max(len(col1), len(col2))):
            col1_str = col1[i] if i < len(col1) else ANSIString("")
            col2_str = col2[i] if i < len(col2) else ANSIString("")
            formatted_string += f"{col1_str.ljust(38)} {col2_str}\n"
        
        return formatted_string

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
            return ANSIString(f"|g{time_str}|n")  # green
        elif idle_time < 1800:  # 15-30 minutes
            return ANSIString(f"|y{time_str}|n")  # yellow
        elif idle_time < 2700:  # 30-45 minutes
            return ANSIString(f"|r{time_str}|n")  # orange (using red instead)
        elif idle_time < 3600:
            return ANSIString(f"|R{time_str}|n")  # bright red
        else:
            return ANSIString(f"|x{time_str}|n")  # grey

    def get_gauntlet_difficulty(self):
        """
        Returns the Gauntlet difficulty for this room, including any temporary modifiers.
        Takes into account character merits that affect the Gauntlet.
        """
        base_difficulty = self.db.gauntlet_difficulty or 6  # Default difficulty
        temp_modifier = self.db.temp_gauntlet_modifier or 0
        
        # Get the expiry time for the modifier
        modifier_expiry = self.db.temp_gauntlet_expiry or 0
        
        # Check if the modifier has expired
        if modifier_expiry and datetime.now().timestamp() > modifier_expiry:
            # Clear expired modifier
            self.db.temp_gauntlet_modifier = 0
            self.db.temp_gauntlet_expiry = None
            return base_difficulty
        
        # Calculate final difficulty
        final_difficulty = base_difficulty + temp_modifier
        
        # If this is being called in the context of a character's action,
        # check for Natural Channel merit and Ananasi form
        if hasattr(self, 'ndb') and self.ndb.current_stepper:
            character = self.ndb.current_stepper
            if (hasattr(character, 'db') and 
                character.db.stats):
                
                # Check for Natural Channel merit
                if ('merits' in character.db.stats and 
                    'supernatural' in character.db.stats['merits'] and
                    'Natural Channel' in character.db.stats['merits']['supernatural']):
                    final_difficulty -= 1
                
                # Check for Ananasi in Crawlerling form
                shifter_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
                if (shifter_type == "Ananasi" and
                    character.db.current_form == "Crawlerling"):
                    # Invert difficulty (2->10, 3->9, 4->8, etc.)
                    final_difficulty = 12 - final_difficulty
        
        # Ensure difficulty stays within valid range (1-10)
        return max(1, min(10, final_difficulty))

    def modify_gauntlet(self, modifier, duration=0):
        """
        Temporarily modifies the Gauntlet difficulty of the room.
        
        Args:
            modifier (int): The amount to modify the Gauntlet by (negative numbers lower it)
            duration (int): How long in seconds the modification should last (0 for permanent)
        """
        self.db.temp_gauntlet_modifier = modifier
        
        if duration > 0:
            self.db.temp_gauntlet_expiry = datetime.now().timestamp() + duration
        else:
            self.db.temp_gauntlet_expiry = None
        
        # Announce the change if it's significant
        if modifier < 0:
            self.msg_contents("The Gauntlet seems to thin in this area...")
        elif modifier > 0:
            self.msg_contents("The Gauntlet seems to thicken in this area...")

    def peek_umbra(self, looker):
        """Allow a character to peek into the Umbra version of the room."""
        # Use the same return_appearance method but with peek_umbra flag
        appearance = self.return_appearance(looker, peek_umbra=True)
        
        # Extract just the description part (between header and first divider)
        lines = appearance.split('\n')
        desc_lines = []
        for line in lines[2:]:  # Skip header lines
            if line.startswith('---'):  # Stop at first divider
                break
            desc_lines.append(line)
        
        header = "-" * 30 + "<  Umbra Vision >" + "-" * 31
        footer = "-" * 78
        
        return f"\n{header}\n\n{''.join(desc_lines)}\n{footer}"

    def format_description(self, desc):
        """
        Format the description with proper paragraph handling and indentation.
        """
        if not desc:
            return ""
            
        # First normalize all line breaks and tabs
        desc = desc.replace('%T', '%t')
        desc = desc.replace('%R%R', '\n\n')  # Double line breaks first
        desc = desc.replace('%r%r', '\n\n')
        desc = desc.replace('%R', '\n')
        desc = desc.replace('%r', '\n')
        
        # Process each paragraph
        paragraphs = []
        for paragraph in desc.split('\n'):
            # Skip completely empty paragraphs
            if not paragraph.strip():
                paragraphs.append('')
                continue
                
            # Handle tabs at start of paragraph
            tab_count = 0
            working_paragraph = paragraph
            while working_paragraph.startswith('%t'):
                tab_count += 1
                working_paragraph = working_paragraph[2:]  # Remove just the %t
            
            # Apply indentation and handle the rest of the paragraph
            if tab_count > 0:
                working_paragraph = '    ' * tab_count + working_paragraph
            
            # Wrap the paragraph while preserving ANSI codes
            wrapped = wrap_ansi(working_paragraph, width=76)
            paragraphs.append(wrapped)
        
        # Clean up multiple consecutive empty lines
        result = []
        last_empty = False
        for p in paragraphs:
            if not p:
                if not last_empty:
                    result.append(p)
                last_empty = True
            else:
                result.append(p)
                last_empty = False
        
        return '\n'.join(result)

    def msg_contents(self, text=None, exclude=None, from_obj=None, mapping=None, **kwargs):
        """
        Send a message to all objects inside the room, excluding the sender and those in a different plane.
        """
        if from_obj and hasattr(from_obj, "location"):
            if from_obj.location.db.roomtype == "freezer":
                if from_obj.has_account:  # Only block player characters
                    from_obj.msg("|rYou are frozen and cannot speak.|n")
                    return
        
        contents = self.contents
        if exclude:
            exclude = make_iter(exclude)
            contents = [obj for obj in contents if obj not in exclude]

        for obj in contents:
            if hasattr(obj, 'is_character') and obj.is_character:
                # Check if the character is in the same plane (Umbra or material)
                if from_obj and hasattr(from_obj, 'tags'):
                    sender_in_umbra = from_obj.tags.get("in_umbra", category="state")
                    receiver_in_umbra = obj.tags.get("in_umbra", category="state")
                    
                    if sender_in_umbra != receiver_in_umbra:
                        continue  # Skip this character if they're in a different plane

            obj.msg(text=text, from_obj=from_obj, mapping=mapping, **kwargs)

    def can_step_sideways(self, character):
        """
        Check if a character can step sideways based on their type and conditions.
        Returns (bool, str) tuple: (can_step, reason)
        """
        # Get character's splat and type
        stats = character.db.stats
        if not stats or 'other' not in stats or 'splat' not in stats['other']:
            return False, "Error: Character splat not found."

        splat = stats['other']['splat'].get('Splat', {}).get('perm', '')
        shifter_type = stats['other'].get('type', {}).get('Type', {}).get('perm', '')
        
        # Check if character has Step Sideways merit
        has_step_sideways = (
            stats.get('merits', {}).get('supernatural', {}).get('Step Sideways', {}).get('perm', 0) > 0
        )

        # If they have Step Sideways merit, they can always step sideways
        if has_step_sideways:
            return True, ""

        # Only allow Shifters to step sideways
        if splat != "Shifter":
            return False, "Only Shifters can step sideways."

        # Check specific Fera restrictions
        if shifter_type == "Ananasi":
            # Check if in Crawlerling form
            current_form = character.db.current_form
            if current_form != "Crawlerling":
                return False, "You must be in Crawlerling form to step sideways."
            return True, ""

        elif shifter_type == "Bastet":
            # Check for Walking Between Worlds gift
            has_wbw = (
                stats.get('powers', {}).get('gift', {}).get('Walking Between Worlds', {}).get('perm', 0) > 0
            )
            if has_wbw:
                return True, ""
            # Check if in Den-Realm
            if self.db.roomtype != "Den-Realm":
                return False, "You can only step sideways within your Den-Realm or with the Walking Between Worlds gift."
            return True, ""

        elif shifter_type == "Gurahl":
            # Check if in Umbral Glen
            if self.db.roomtype != "Umbral-Glen":
                return False, "You can only step sideways from within an Umbral Glen or via the Rite of Rending the Gauntlet."
            return True, ""

        elif shifter_type == "Mokolé":
            # Check for Walking Between Worlds gift
            has_wbw = (
                stats.get('powers', {}).get('gift', {}).get('Walking Between Worlds', {}).get('perm', 0) > 0
            )
            if not has_wbw:
                return False, "You require the Walking Between Worlds gift to enter the Umbra."
            return True, ""

        elif shifter_type == "Nagah":
            # Check if within an Ananta
            if self.db.roomtype != "Ananta":
                return False, "You can only step sideways within an Ananta."
            # Check if it's the character's attuned Ananta
            if character.db.attuned_ananta != self.key:
                return False, "You can only step sideways within your attuned Ananta."
            return True, ""

        elif shifter_type == "Ratkin":
            # Check if alone or only with spirits/Ratkin
            others_present = False
            for obj in self.contents:
                if obj != character and obj.has_account:
                    if not hasattr(obj, 'db') or not obj.db.stats:
                        others_present = True
                        break
                    other_splat = obj.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
                    other_type = obj.db.stats.get('other', {}).get('type', {}).get('Type', {}).get('perm', '')
                    if other_splat != "Shifter" or other_type != "Ratkin":
                        if not obj.tags.get("spirit"):
                            others_present = True
                            break
            if others_present:
                return False, "You can only step sideways when alone or in the presence of spirits or fellow Ratkin."
            return True, ""

        elif shifter_type == "Rokea":
            # Check for Swim Sideways merit, Enter Sea's Soul gift, or Rite of Passing the Net
            has_swim = (
                stats.get('merits', {}).get('supernatural', {}).get('Swim Sideways', {}).get('perm', 0) > 0
            )
            has_ess = (
                stats.get('powers', {}).get('gift', {}).get("Enter Sea's Soul", {}).get('perm', 0) > 0
            )
            has_rite = (
                stats.get('powers', {}).get('rite', {}).get('Rite of the Passing Net', {}).get('perm', 0) > 0
            )
            if not (has_swim or has_ess or has_rite):
                return False, "You require the Swim Sideways merit, Enter Sea's Soul gift, or Rite of Passing the Net to swim sideways."
            return True, ""

        # Default case - any shifter type without special restrictions can step sideways like Garou
        return True, ""

    def return_from_umbra(self, character):
        """
        Allows a character to return from the Umbra to the material world.
        """
        # Check if Ananasi needs to be in Crawlerling form
        stats = character.db.stats
        if stats:
            shifter_type = stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
            if shifter_type == "Ananasi" and character.db.current_form != "Crawlerling":
                character.msg("You must be in Crawlerling form to cross the Gauntlet.")
                return False

        # Store the character temporarily for difficulty calculation
        self.ndb.current_stepper = character
        try:
            difficulty = self.get_gauntlet_difficulty()
            successes, ones = self.roll_gnosis(character, difficulty)
            
            if successes > 0:
                character.tags.remove("in_umbra", category="state")
                character.tags.add("in_material", category="state")
                character.msg("You step back into the material world.")
                self.msg_contents(f"{character.name} shimmers into view as they return from the Umbra.", exclude=character, from_obj=character)
                return True
            elif successes == 0 and ones > 0:
                # Botch
                character.msg("You catastrophically fail to return from the Umbra.")
                
                # Announce the botch on the mudinfo channel
                mudinfo = search_channel("mudinfo")
                if mudinfo:
                    mudinfo[0].msg(f"|rBOTCH!!!|n {character.name} botched their attempt to return from the Umbra in {self.name}.")
                
                return False
            else:
                character.msg("You fail to return from the Umbra.")
                return False
        finally:
            # Clean up the temporary character reference
            self.ndb.current_stepper = None

    def step_sideways(self, character):
        """
        Allows a character to step sideways into the Umbra.
        """
        # Check if character can step sideways
        can_step, reason = self.can_step_sideways(character)
        if not can_step:
            character.msg(reason)
            return False

        # Store the character temporarily for difficulty calculation
        self.ndb.current_stepper = character
        try:
            difficulty = self.get_gauntlet_difficulty()
            successes, ones = self.roll_gnosis(character, difficulty)
            
            if successes > 0:
                character.tags.remove("in_material", category="state")
                character.tags.add("in_umbra", category="state")
                character.msg("You successfully step sideways into the Umbra.")
                self.msg_contents(f"{character.name} shimmers and fades from view as they step into the Umbra.", exclude=character, from_obj=character)
                return True
            elif successes == 0 and ones > 0:
                # Botch
                character.msg("You catastrophically fail to step sideways into the Umbra.")
                self.msg_contents(f"{character.name} seems to flicker for a moment, but remains in place.", exclude=character, from_obj=character)
                
                # Announce the botch on the mudinfo channel
                mudinfo = search_channel("mudinfo")
                if mudinfo:
                    mudinfo[0].msg(f"|rBOTCH!!!|n {character.name} botched their attempt to step sideways in {self.name}.")
                
                return False
            else:
                character.msg("You fail to step sideways into the Umbra.")
                return False
        finally:
            # Clean up the temporary character reference
            self.ndb.current_stepper = None

    def roll_gnosis(self, character, difficulty):
        """
        Simulates a Gnosis roll for the character.
        Returns a tuple of (successes, ones).
        """
        stats = character.db.stats
        if not stats or 'pools' not in stats or 'dual' not in stats['pools'] or 'Gnosis' not in stats['pools']['dual']:
            character.msg("Error: Gnosis attribute not found. Please contact an admin.")
            return 0, 0
        
        gnosis = stats['pools']['dual']['Gnosis']['perm']
        if gnosis is None:
            character.msg("Error: Permanent Gnosis value is None. Please contact an admin.")
            return 0, 0
        
        # Convert gnosis to an integer if it's stored as a string
        if isinstance(gnosis, str):
            try:
                gnosis = int(gnosis)
            except ValueError:
                character.msg("Error: Invalid Gnosis value. Please contact an admin.")
                return 0, 0
        
        successes = 0
        ones = 0
        for _ in range(gnosis):
            roll = random.randint(1, 10)
            if roll >= difficulty:
                successes += 1
            elif roll == 1:
                ones += 1
        
        character.msg(f"Gnosis Roll: {successes} successes against difficulty {difficulty}")
        return successes, ones
    
    def initialize(self):
        """Initialize default attributes."""
        if not self.attributes.has("initialized"):
            # Initialize attributes
            self.db.location_type = None  # "District", "Sector", "Neighborhood", or "Site"
            self.db.order = 0
            self.db.infrastructure = 0
            self.db.resolve = 0
            self.db.resources = {}  # Empty dict for resources
            self.db.owners = []
            self.db.sub_locations = []
            self.db.roll_log = []  # Initialize an empty list for roll logs
            self.db.initialized = True  # Mark this room as initialized
            self.save()  # Save immediately to avoid ID-related issues
            
            # Initialize housing data with proper structure
            self.db.housing_data = {
                'is_housing': False,
                'max_apartments': 0,
                'current_tenants': {},
                'apartment_numbers': set(),
                'required_resources': 0,
                'building_zone': None,
                'connected_rooms': set(),
                'is_lobby': False
            }
            
            # Initialize home data
            self.db.home_data = {
                'locked': False,
                'keyholders': set(),
                'owner': None
            }
            
            # Set resources as integer instead of dict
            self.db.resources = 0
            
            self.db.initialized = True
        else:
            # Ensure roll_log exists even for previously initialized rooms
            if not hasattr(self.db, 'roll_log'):
                self.db.roll_log = []

    def at_object_creation(self):
        """Called when the room is first created."""
        super().at_object_creation()
        
        # Initialize scene tracking with proper structure
        self.db.scene_data = {
            'start_time': None,
            'participants': set(),
            'last_activity': None,
            'completed': False
        }
        
        self.db.unfindable = False
        self.db.fae_desc = ""
        self.db.roll_log = []  # Initialize empty roll log
        self.db.umbra_only = False  # Attribute for Umbra-only rooms
        self.db.fae_only = False   # New attribute for Fae-only rooms
        self.db.home_data = {
            'locked': False,
            'keyholders': set(),
            'owner': None
        }
        # Initialize housing data
        self.db.housing_data = {
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

    def set_as_district(self):
        self.initialize()
        self.db.location_type = "District"

    def set_as_sector(self):
        self.initialize()
        self.db.location_type = "Sector"

    def set_as_neighborhood(self):
        self.initialize()
        self.db.location_type = "Neighborhood"
        self.db.order = 5
        self.db.infrastructure = 5
        self.db.resolve = 5

    def set_as_site(self):
        self.initialize()
        self.db.location_type = "Site"

    def add_sub_location(self, sub_location):
        """
        Add a sub-location to this room. Automatically sets the type of the sub-location.
        """
        self.initialize()
        sub_location.initialize()

        if self.db.location_type == "District":
            sub_location.set_as_sector()
        elif self.db.location_type == "Sector":
            sub_location.set_as_neighborhood()
        elif self.db.location_type == "Neighborhood":
            sub_location.set_as_site()

        self.db.sub_locations.append(sub_location)
        sub_location.db.parent_location = self
        self.save()  # Ensure changes are saved

    def remove_sub_location(self, sub_location):
        """
        Remove a sub-location from this room.
        """
        self.initialize()
        sub_location.initialize()
        if sub_location in self.db.sub_locations:
            self.db.sub_locations.remove(sub_location)
            sub_location.db.parent_location = None
            self.save()  # Ensure changes are saved

    def get_sub_locations(self):
        self.initialize()
        return self.db.sub_locations

    def update_values(self):
        """
        Update the Order, Infrastructure, and Resolve values based on the averages of sub-locations.
        Only applies if this room is a District or Sector.
        """
        self.initialize()
        if self.db.location_type in ["District", "Sector"]:
            sub_locations = self.get_sub_locations()
            if sub_locations:
                averages = {
                    "avg_order": sum(loc.db.order for loc in sub_locations) / len(sub_locations),
                    "avg_infrastructure": sum(loc.db.infrastructure for loc in sub_locations) / len(sub_locations),
                    "avg_resolve": sum(loc.db.resolve for loc in sub_locations) / len(sub_locations),
                }
                self.db.order = averages['avg_order']
                self.db.infrastructure = averages['avg_infrastructure']
                self.db.resolve = averages['avg_resolve']
            else:
                self.db.order = 0
                self.db.infrastructure = 0
                self.db.resolve = 0
            self.save()

    def save(self, *args, **kwargs):
        """
        Overriding save to ensure initialization happens after the object is fully created.
        """
        super().save(*args, **kwargs)
        self.initialize()
        if self.db.location_type in ["Sector", "Neighborhood"] and hasattr(self.db, "parent_location"):
            self.db.parent_location.update_values()

    def increase_order(self, amount=1):
        self.db.order += amount
        self.save()

    def decrease_order(self, amount=1):
        self.db.order = max(0, self.db.order - amount)
        self.save()

    def set_order(self, value):
        self.db.order = value
        self.save()

    def increase_infrastructure(self, amount=1):
        self.db.infrastructure += amount
        self.save()

    def decrease_infrastructure(self, amount=1):
        self.db.infrastructure = max(0, self.db.infrastructure - amount)
        self.save()

    def set_infrastructure(self, value):
        self.db.infrastructure = value
        self.save()

    def increase_resolve(self, amount=1):
        self.db.resolve += amount
        self.save()

    def decrease_resolve(self, amount=1):
        self.db.resolve = max(0, self.db.resolve - amount)
        self.save()

    def set_resolve(self, value):
        self.db.resolve = value
        self.save()

    def add_owner(self, owner):
        self.initialize()
        if owner not in self.db.owners:
            self.db.owners.append(owner)
            self.save()

    def remove_owner(self, owner):
        self.initialize()
        if owner in self.db.owners:
            self.db.owners.remove(owner)
            self.save()

    def display_hierarchy(self, depth=0):
        """
        Display the hierarchy of locations.
        """
        self.initialize()
        indent = "  " * depth
        self.msg(f"{indent}- {self.key} ({self.db.location_type})")
        for sub_loc in self.get_sub_locations():
            sub_loc.display_hierarchy(depth + 1)

    def log_roll(self, roller, description, result):
        """
        Log a dice roll in this room.
        
        Args:
            roller (str): Name of the character making the roll
            description (str): Description of the roll
            result (str): Result of the roll
        """
        if not hasattr(self.db, 'roll_log') or self.db.roll_log is None:
            self.db.roll_log = []
        
        # Extract just the total number of dice from the description
        # Remove detailed stat information and keep only the total
        dice_match = re.search(r'Rolling (\d+) dice', description)
        if dice_match:
            total_dice = dice_match.group(1)
            simplified_desc = f"Rolling {total_dice} dice"
            if "vs" in description:
                difficulty = description.split("vs")[-1].strip()
                simplified_desc += f" vs {difficulty}"
        else:
            simplified_desc = description  # Fallback to original if pattern not found
        
        log_entry = {
            'timestamp': datetime.now(),
            'roller': roller,
            'description': simplified_desc,
            'result': result
        }
        
        self.db.roll_log.append(log_entry)
        # Keep only the last 10 rolls
        if len(self.db.roll_log) > 10:
            self.db.roll_log = self.db.roll_log[-10:]

    def get_roll_log(self):
        """
        Get the roll log for this room.
        
        Returns:
            list: List of roll log entries
        """
        if not hasattr(self.db, 'roll_log') or self.db.roll_log is None:
            self.db.roll_log = []
        return self.db.roll_log

    def get_fae_description(self):
        """Get the fae description of the room."""
        return self.db.fae_desc or "This place has no special fae aspect."

    def set_fae_description(self, description):
        """Set the fae description of the room."""
        self.db.fae_desc = description

    def ensure_housing_data(self):
        """Ensure housing data exists and is properly initialized."""
        if not self.db.housing_data:
            self.db.housing_data = {
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
        return self.db.housing_data

    def is_housing_area(self):
        """Check if this is a housing area."""
        self.ensure_housing_data()  # Ensure housing data exists
        return (hasattr(self.db, 'roomtype') and 
                self.db.roomtype in [
                    "Apartment Building", "Apartments", 
                    "Condos", "Condominiums",
                    "Residential Area", "Residential Neighborhood", 
                    "Neighborhood", "Splat Housing", "Motel"
                ])

    def is_apartment_building(self):
        """Check if this is an apartment building."""
        self.ensure_housing_data()
        return (hasattr(self.db, 'roomtype') and 
                self.db.roomtype in [
                    "Apartment Building", "Apartments", 
                    "Condos", "Condominiums",
                    "Splat Housing"  # Add Splat Housing to apartment-style buildings
                ])

    def is_residential_area(self):
        """Check if this is a residential neighborhood."""
        self.ensure_housing_data()
        return (hasattr(self.db, 'roomtype') and 
                self.db.roomtype in [
                    "Residential Area", "Residential Neighborhood", 
                    "Neighborhood"
                ])

    def update_splat_room(self, splat_type=None, lobby=None):
        """
        Update an existing room's splat housing configuration.
        If splat_type is not provided, will attempt to determine from room name.
        If lobby is not provided, will attempt to find from existing connections.
        """
        # If no splat type provided, try to determine from room name
        if not splat_type:
            room_name = self.key.lower()
            if "mage" in room_name:
                splat_type = "Mage"
            elif "vampire" in room_name:
                splat_type = "Vampire"
            elif "werewolf" in room_name:
                splat_type = "Werewolf"
            elif "changeling" in room_name:
                splat_type = "Changeling"
            else:
                splat_type = "Splat"  # Generic if can't determine

        # If no lobby provided, try to find from existing connections
        if not lobby and self.db.housing_data and self.db.housing_data.get('building_zone'):
            from evennia import search_object
            possible_lobby = search_object(self.db.housing_data['building_zone'])
            if possible_lobby:
                lobby = possible_lobby[0]

        # Now set up the room with the determined parameters
        self.setup_splat_room(splat_type, lobby)
        return True

    def setup_splat_room(self, splat_type, lobby):
        """Set up a room as a splat-specific residence."""
        # Store original description if it exists and isn't the default
        original_desc = None
        default_desc = "Housing for your specific splat, either in a Chantry, Freehold, Sept, or other type."
        if self.db.desc and self.db.desc != default_desc:
            original_desc = self.db.desc

        self.db.roomtype = f"{splat_type} Room"
        
        # Initialize housing data
        housing_data = self.ensure_housing_data()
        housing_data.update({
            'is_housing': True,
            'is_residence': True,
            'building_zone': lobby.dbref if lobby else None,
            'connected_rooms': {self.dbref, lobby.dbref} if lobby else {self.dbref},
            'available_types': ["Splat Housing"],
            'max_apartments': 1,  # Individual room
            'current_tenants': {},
            'apartment_numbers': set()
        })
        
        # Restore original description or set default if none exists
        if original_desc:
            self.db.desc = original_desc
        elif not self.db.desc:
            self.db.desc = default_desc

    def setup_housing(self, housing_type="Apartment Building", max_units=20):
        """Set up room as a housing area."""
        # Set room type
        self.db.roomtype = housing_type
        
        # Initialize housing data
        housing_data = self.ensure_housing_data()
        
        # Set initial available types based on housing type
        initial_types = []
        if housing_type == "Splat Housing":
            initial_types = ["Splat Housing"]
        elif housing_type == "Motel":
            initial_types = ["Motel Room"]
        
        housing_data.update({
            'is_housing': True,
            'max_apartments': max_units,
            'current_tenants': {},
            'apartment_numbers': set(),
            'is_lobby': True,
            'available_types': initial_types,
            'building_zone': self.dbref,  # Set building zone to self
            'connected_rooms': {self.dbref}  # Initialize connected rooms with self
        })

        # For splat housing, modify any existing exits to use initials
        if housing_type == "Splat Housing":
            for exit in self.exits:
                if exit.destination:
                    # Get the destination room's name and create initials
                    room_name = exit.destination.key
                    # Split on spaces and get first letter of each word
                    initials = ''.join(word[0].lower() for word in room_name.split())
                    # Update exit key and add original name as alias
                    original_key = exit.key
                    exit.key = initials
                    if original_key != initials:
                        exit.aliases.add(original_key)
                    
                    # Set up the destination room as a splat residence
                    dest = exit.destination
                    if dest:
                        # Determine splat type from room name if possible
                        room_name = dest.key.lower()
                        if "mage" in room_name:
                            splat_type = "Mage"
                        elif "vampire" in room_name:
                            splat_type = "Vampire"
                        elif "werewolf" in room_name:
                            splat_type = "Werewolf"
                        elif "changeling" in room_name:
                            splat_type = "Changeling"
                        else:
                            splat_type = "Splat"  # Generic if can't determine
                            
                        dest.setup_splat_room(splat_type, self)
        
        # Force room appearance update
        self.at_object_creation()

    def get_available_housing_types(self):
        """Get available housing types based on area type."""
        self.ensure_housing_data()  # Ensure housing data exists
        from commands.housing import CmdRent
        if self.db.roomtype == "Motel":
            return {"Motel Room": CmdRent.APARTMENT_TYPES["Motel Room"]}
        elif self.is_apartment_building():
            return CmdRent.APARTMENT_TYPES
        elif self.is_residential_area():
            return CmdRent.RESIDENTIAL_TYPES
        return {}

    def get_housing_cost(self, unit_type):
        """Calculate housing cost based on area resources and unit type."""
        self.ensure_housing_data()
        housing_types = self.get_available_housing_types()
        if unit_type in housing_types:
            base_resources = self.db.resources or 0
            return max(1, base_resources + housing_types[unit_type]['resource_modifier'])
        return 0

    def list_available_units(self):
        """Return formatted list of available units and their costs."""
        self.ensure_housing_data()
        if not self.is_housing_area():
            return "This is not a housing area."
            
        housing_types = self.get_available_housing_types()
        if not housing_types:
            return "No housing types available."
            
        from evennia.utils import evtable
        table = evtable.EvTable(
            "|wType|n", 
            "|wRooms|n", 
            "|wRequired Resources|n", 
            border="table"
        )
        
        for rtype, data in housing_types.items():
            cost = self.get_housing_cost(rtype)
            table.add_row(rtype, data['rooms'], cost)
            
        return str(table)

    def at_object_receive(self, moved_obj, source_location, **kwargs):
        """Called when an object enters the room."""
        super().at_object_receive(moved_obj, source_location, **kwargs)
        
        # If this is a freezer room, notify the character
        if self.db.roomtype == "freezer" and moved_obj.has_account:
            moved_obj.msg("|rYou have been frozen and cannot leave this room or speak.|n")
            moved_obj.msg("Contact staff if you believe this is in error.")

    def prevent_exit_use(self, exit_obj, character):
        """
        Called by exits to check if character can use them.
        Returns True if exit use should be prevented.
        """
        if self.db.roomtype == "freezer":
            character.msg("|rYou are frozen and cannot leave this room.|n")
            return True
        
        # Prevent non-Fae from using exits in Dreaming
        if self.db.fae_only and not self.can_perceive_fae(character):
            character.msg("|mYou cannot interact with the paths of the Dreaming.|n")
            return True
            
        return False

    def set_as_umbral_realm(self):
        """Set this room as an Umbra-only location."""
        self.db.umbra_only = True
        self.db.roomtype = "Umbral Realm"
        # Ensure the room has an Umbral description
        if not self.db.desc:
            self.db.desc = "This is a realm that exists only in the Umbra."

    def set_as_fae_realm(self):
        """Set this room as a Fae-only location."""
        self.db.fae_only = True
        self.db.roomtype = "Dreaming"
        # Ensure the room has a Fae description
        if not self.db.desc:
            self.db.desc = "This is a realm that exists only in the world of the Fae."

    def is_residence(self):
        """Check if this room is a residence."""
        self.ensure_housing_data()
        return (hasattr(self.db, 'roomtype') and 
                (self.db.roomtype == "Residence" or
                 "Room" in self.db.roomtype or  # Check for "Mage Room", "Vampire Room", etc.
                 self.db.housing_data.get('is_residence', False)))

    def is_valid_residence(self):
        """
        Check if this room is a valid residence that can be used with home commands.
        
        Returns:
            bool: True if this is a valid residence, False otherwise
        """
        if not hasattr(self, 'db'):
            return False
            
        # Check for housing data
        home_data = self.db.home_data if hasattr(self.db, 'home_data') else None
        housing_data = self.db.housing_data if hasattr(self.db, 'housing_data') else None
        
        # Valid room types for residences
        valid_types = [
            "apartment", "house", "splat_housing",
            "mortal_room", "mortal_plus_room", "possessed_room",
            "mage_room", "vampire_room", "changeling_room", 
            "motel_room", "apartment_room", "house_room", "studio",
            "studio apartment"
        ]
        
        # Check if room type is valid
        has_valid_type = False
        roomtype = self.db.roomtype if hasattr(self.db, 'roomtype') else None
        if roomtype:
            roomtype_lower = roomtype.lower()
            has_valid_type = (
                roomtype_lower in [t.lower() for t in valid_types] or
                roomtype_lower.endswith("room")
            )
        
        # Check both roomtype and housing data
        has_housing_data = (
            (home_data is not None and (home_data.get('owner') or home_data.get('co_owners'))) or
            (housing_data is not None and housing_data.get('is_residence')) or
            hasattr(self.db, 'owner')  # Legacy check
        )
        
        return has_valid_type and has_housing_data

    def start_scene(self, character):
        """
        Start a new scene in this room.
        
        Args:
            character (Object): The character starting the scene
        """
        now = datetime.now()
        
        # Initialize scene data if needed
        if not hasattr(self.db, 'scene_data') or not isinstance(self.db.scene_data, dict):
            self.db.scene_data = {
                'start_time': now,
                'participants': {character.key},
                'last_activity': now,
                'completed': False
            }
        else:
            # If no active scene, start one
            if not self.db.scene_data.get('start_time'):
                self.db.scene_data.update({
                    'start_time': now,
                    'participants': {character.key},
                    'last_activity': now,
                    'completed': False
                })

    def end_scene(self):
        """End the current scene in this room."""
        if not hasattr(self.db, 'scene_data') or not self.db.scene_data.get('start_time'):
            return
            
        # Mark scene as completed
        self.db.scene_data.update({
            'start_time': None,
            'participants': set(),
            'last_activity': None,
            'completed': True
        })

    def add_scene_participant(self, character):
        """
        Add a character as a participant in the current scene.
        
        Args:
            character (Object): The character to add
        """
        if not hasattr(self.db, 'scene_data'):
            self.start_scene(character)
            return
            
        # Initialize participants as a set if needed
        if not isinstance(self.db.scene_data.get('participants'), set):
            self.db.scene_data['participants'] = set()
            
        # Add the character
        self.db.scene_data['participants'].add(character.key)
        self.db.scene_data['last_activity'] = datetime.now()

    def remove_scene_participant(self, character):
        """
        Remove a character from the current scene.
        
        Args:
            character (Object): The character to remove
        """
        if not hasattr(self.db, 'scene_data') or not isinstance(self.db.scene_data.get('participants'), set):
            return
            
        # Remove the character
        self.db.scene_data['participants'].discard(character.key)
        
        # If no participants left, end the scene
        if not self.db.scene_data['participants']:
            self.end_scene()

    def get_scene_participants(self):
        """
        Get all current scene participants.
        
        Returns:
            set: Set of character keys participating in the scene
        """
        if not hasattr(self.db, 'scene_data'):
            return set()
        return self.db.scene_data.get('participants', set())

    def record_scene_activity(self, character):
        """
        Record activity in the current scene.
        
        Args:
            character (Object): The character performing the activity
        """
        now = datetime.now()
        
        # Ensure scene_data exists and has proper structure
        if not hasattr(self.db, 'scene_data') or not isinstance(self.db.scene_data, dict):
            self.db.scene_data = {
                'start_time': now,
                'participants': set(),
                'last_activity': now,
                'completed': False
            }
        
        # Initialize participants as a set if needed
        if not isinstance(self.db.scene_data.get('participants'), set):
            self.db.scene_data['participants'] = set()
        
        # Add character as participant and update activity time
        self.db.scene_data['participants'].add(character.key)
        self.db.scene_data['last_activity'] = now
        
        # If no active scene, start one
        if not self.db.scene_data.get('start_time'):
            self.db.scene_data['start_time'] = now

    def is_valid_scene_location(self):
        """
        Check if this room is valid for scene tracking.
        
        Returns:
            bool: True if valid scene location, False otherwise
        """
        # Must be IC room
        if getattr(self.db, 'roomtype', None) == 'OOC Area':
            return False
            
        # Must have at least two characters present
        character_count = sum(
            1 for obj in self.contents 
            if hasattr(obj, 'has_account') and obj.has_account
        )
        
        return character_count >= 2

    def get_scene_duration(self):
        """
        Get the duration of the current scene in minutes.
        
        Returns:
            float: Duration in minutes, or 0 if no scene
        """
        if not hasattr(self.db, 'scene_data') or not self.db.scene_data.get('start_time'):
            return 0
            
        start_time = self.db.scene_data['start_time']
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
            
        return (datetime.now() - start_time).total_seconds() / 60

    def cleanup_inactive_scenes(self, timeout_minutes=60):
        """
        Clean up scenes that have been inactive for too long.
        
        Args:
            timeout_minutes (int): Minutes of inactivity before cleanup
        """
        if not hasattr(self.db, 'scene_data') or not self.db.scene_data.get('last_activity'):
            return
            
        last_activity = self.db.scene_data['last_activity']
        if isinstance(last_activity, str):
            last_activity = datetime.fromisoformat(last_activity)
            
        # If scene has been inactive for too long, end it
        if (datetime.now() - last_activity).total_seconds() / 60 > timeout_minutes:
            self.end_scene()

class Room(RoomParent):
    pass

