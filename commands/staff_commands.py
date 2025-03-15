"""
Staff commands for Dies Irae.
"""
from evennia.commands.default.muxcommand import MuxCommand
from commands.CmdSelfStat import CmdSelfStat
from world.wod20th.models import Stat
from world.wod20th.utils.sheet_constants import (
    KITH, KNOWLEDGES, SECONDARY_KNOWLEDGES, SECONDARY_SKILLS, 
    SECONDARY_TALENTS, SKILLS, TALENTS, CLAN, BREED, GAROU_TRIBE,
    SEEMING, PATHS_OF_ENLIGHTENMENT, SECT, AFFILIATION, TRADITION,
    CONVENTION, NEPHANDI_FACTION
)
from utils.search_helpers import search_character

REQUIRED_INSTANCES = ['Library', 'Status', 'Influence', 'Wonder', 'Secret Weapon', 'Companion', 
                      'Familiar', 'Enhancement', 'Laboratory', 'Favor', 'Acute Senses', 
                      'Enchanting Feature', 'Secret Code Language', 'Hideaway', 'Safehouse', 
                      'Sphere Natural', 'Phobia', 'Addiction', 'Allies', 'Contacts', 'Caretaker',
                      'Alternate Identity', 'Equipment', 'Professional Certification', 'Allergic',
                      'Impediment', 'Enemy', 'Mentor', 'Old Flame', 'Additional Discipline', 
                      'Totem', 'Boon', 'Treasure', 'Geas', 'Fetish', 'Chimerical Item', 'Chimerical Companion',
                      'Dreamers', 'Digital Dreamers', 'Addiction', 'Phobia', 'Derangement',
                      'Obsession', 'Compulsion', 'Bigot', 'Ability Deficit', 'Sect Enmity', 'Camp Enmity',
                      'Retainers'
                     ] 

class CmdStaffStat(CmdSelfStat):
    """
    Staff command to set stats on players, bypassing normal restrictions.

    Usage:
      +staffstat <character>=<stat>[(<instance>)]/<category>:<value>
      +staffstat <character>=<stat>:<value>

    Examples:
      +staffstat Bob=Strength/Physical:3
      +staffstat Bob=Strength:3        (same as above)
      +staffstat Jane=Status(Camarilla)/Background:2
      +staffstat Mike=Path of Enlightenment:Road of Heaven
      +staffstat Sarah=Nature:Architect

    This command allows staff to set stats on other characters, bypassing normal
    restrictions like character approval status and validation limits.
    """

    key = "+staffstat"
    aliases = ["staffstat"]
    locks = "cmd:perm(Admin) or perm(Builder)"
    help_category = "Staff"

    def parse(self):
        """Parse the command arguments for staff usage."""
        if not self.args or "=" not in self.args:
            self.target = None
            self.stat_name = None
            self.instance = None
            self.category = None
            self.value_change = None
            return

        try:
            # Split into character and stat parts
            target_name, stat_args = self.args.split("=", 1)
            
            # Find the target character
            self.target = search_character(self.caller, target_name.strip())
            if not self.target:
                return

            # Handle the colon syntax
            if ':' in stat_args:
                stat_part, value = stat_args.split(':', 1)
                # If there's a category specified
                if '/' in stat_part:
                    stat_name, category = stat_part.split('/', 1)
                    # Handle instance if present
                    if '(' in stat_name and ')' in stat_name:
                        base_name, instance = stat_name.split('(', 1)
                        self.stat_name = base_name.strip()
                        self.instance = instance.rstrip(')').strip()
                    else:
                        self.stat_name = stat_name.strip()
                        self.instance = None
                    self.category = category.strip()
                else:
                    # No category specified
                    if '(' in stat_part and ')' in stat_part:
                        base_name, instance = stat_part.split('(', 1)
                        self.stat_name = base_name.strip()
                        self.instance = instance.rstrip(')').strip()
                    else:
                        self.stat_name = stat_part.strip()
                        self.instance = None
                    self.category = None
                self.value_change = value.strip()

            # Remove any "Gift:" prefix if present
            if self.stat_name and self.stat_name.startswith('Gift:'):
                self.stat_name = self.stat_name[5:].strip()

            # If no category was specified but we have a stat name, try to detect the category
            if self.stat_name and not self.category:
                # Try to find the stat in the database
                stat = Stat.objects.filter(name__iexact=self.stat_name).first()
                if stat:
                    self.category = stat.category
                    self.stat_type = stat.stat_type
                else:
                    # If not found in database, try to detect from common categories
                    if self.stat_name.lower() in ['strength', 'dexterity', 'stamina']:
                        self.category = 'attributes'
                        self.stat_type = 'physical'
                    elif self.stat_name.lower() in ['charisma', 'manipulation', 'appearance']:
                        self.category = 'attributes'
                        self.stat_type = 'social'
                    elif self.stat_name.lower() in ['perception', 'intelligence', 'wits']:
                        self.category = 'attributes'
                        self.stat_type = 'mental'
                    # Check if it's a background that requires an instance
                    elif self.stat_name in REQUIRED_INSTANCES:
                        self.category = 'backgrounds'
                        self.stat_type = 'background'

            # Get the stat definition from the database for instance checking
            stat = Stat.objects.filter(name__iexact=self.stat_name).first()

            # Store the original stat name for gift aliases
            if self.category == 'powers' and self.stat_type == 'gift':
                self.alias_used = self.stat_name

            # Special handling for Gnosis
            if self.stat_name and self.stat_name.lower() == 'gnosis':
                splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
                char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
                
                if splat and splat.lower() in ['shifter', 'possessed']:
                    self.category = 'pools'
                    self.stat_type = 'dual'
                elif splat and splat.lower() == 'mortal+' and char_type and char_type.lower() == 'kinfolk':
                    self.category = 'merits'
                    self.stat_type = 'supernatural'

            # Handle instance requirements
            requires_instance = self._requires_instance(self.stat_name, self.category)
            should_support = self._should_support_instance(self.stat_name, self.category)

            # If the stat requires an instance
            if self.stat_name and requires_instance:
                if not self.instance:
                    self._display_instance_requirement_message(self.stat_name)
                    self.stat_name = None
                    return
                # If no category specified for an instanced stat, default to backgrounds
                if not self.category:
                    self.category = 'backgrounds'
                    self.stat_type = 'background'
            # Only check for unsupported instances if the stat doesn't require one
            elif self.instance and not requires_instance:
                self.caller.msg(f"|rThe stat '{self.stat_name}' does not support instances.|n")
                self.stat_name = None
                return
        
            # Special handling for Nature and Time
            if not self.category:
                splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
                char_type = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
                
                if self.stat_name.lower() == 'nature':
                    # For Changelings and Kinain, Nature is a realm power
                    if splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain'):
                        self.category = 'powers'
                        self.stat_type = 'realm'
                    else:
                        self.category = 'identity'
                        self.stat_type = 'personal'
                elif self.stat_name.lower() == 'demeanor':
                    self.category = 'identity'
                    self.stat_type = 'personal'
                elif self.stat_name.lower() == 'time':
                    if splat == 'Mage':
                        self.category = 'powers'
                        self.stat_type = 'sphere'
                    else:
                        self.category = 'attributes'
                        self.stat_type = 'physical'

        except Exception as e:
            self.caller.msg(f"|rError parsing command: {str(e)}|n")
            self.target = None
            self.stat_name = None
            self.instance = None
            self.category = None
            self.value_change = None

    def _requires_instance(self, stat_name: str, category: str = None) -> bool:
        """
        Check if a stat MUST have an instance.
        """
        # Stats in REQUIRED_INSTANCES must have instances (case-insensitive)
        if any(stat_name.lower() == required.lower() for required in REQUIRED_INSTANCES):
            return True
            
        # Check database for required instance flag
        from world.wod20th.models import Stat
        stat = Stat.objects.filter(name__iexact=stat_name).first()
        
        if stat and stat.instanced:
            return True
            
        return False
        
    def _should_support_instance(self, stat_name: str, category: str = None) -> bool:
        """
        Check if a stat CAN have an instance.
        
        Args:
            stat_name (str): The name of the stat to check
            category (str, optional): The category of the stat
            
        Returns:
            bool: True if the stat can have an instance, False otherwise
        """
        # If it requires an instance, it can have one
        if self._requires_instance(stat_name, category):
            return True
            
        return False

    def validate_stat_value(self, stat_name: str, value: str, category: str = None, stat_type: str = None) -> tuple:
        """Override validation to handle type conversion while still allowing staff to bypass normal validation rules."""
        # Define categories that must be numeric
        numeric_categories = {
            'attributes': True,
            'abilities': True,
            'backgrounds': True,
            'powers': True,
            'merits': True,
            'flaws': True,
            'virtues': True,
            'pools': True
        }

        # Special handling for Nature and Demeanor
        if stat_name.lower() in ['nature', 'demeanor']:
            # Check the target character's splat type
            splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
            char_type = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
            
            # For Changelings and Kinain, Nature is a realm power and should be numeric
            if splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain'):
                try:
                    numeric_value = int(value)
                    return True, "", numeric_value
                except ValueError:
                    return False, f"{stat_name} must be a number for Changelings", None
            # For all other splat types, Nature and Demeanor should be strings
            else:
                return True, "", value
        
        # Special handling for Time when it's a sphere for Mages
        if stat_name.lower() == 'time' and category == 'powers' and stat_type == 'sphere':
            try:
                numeric_value = int(value)
                return True, "", numeric_value
            except ValueError:
                return False, f"{stat_name} must be a number", None

        # Check if this stat belongs to a numeric category
        if category in numeric_categories:
            try:
                numeric_value = int(value)
                return True, "", numeric_value
            except ValueError:
                return False, f"{stat_name} must be a number", None

        # For non-numeric stats, return as is
        return True, "", value

    def func(self):
        """Execute the command with staff privileges."""
        if not self.args:
            self.caller.msg(self.__doc__)
            return

        if not self.target or not self.stat_name:
            self.caller.msg("|rUsage: +staffstat <character>=<stat>[(<instance>)]/<category>:<value>|n")
            return

        try:
            # Basic validation
            if not self.stat_name:
                self.caller.msg("|rUsage: +staffstat <character>=<stat>[(<instance>)]/<category>:<value>|n")
                return

            # Get character's splat type and character type 
            splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
            char_type = self.target.get_stat('identity', 'lineage', 'Type', temp=False)

            # If no category/type specified, try to determine it from the stat name
            if not self.category or not hasattr(self, 'stat_type'):
                # Check secondary abilities first - these are high priority matches
                if self.stat_name in SECONDARY_TALENTS:
                    self.category = 'abilities'
                    self.stat_type = 'secondary_talent'
                elif self.stat_name in SECONDARY_SKILLS:
                    self.category = 'abilities'
                    self.stat_type = 'secondary_skill'
                elif self.stat_name in SECONDARY_KNOWLEDGES:
                    self.category = 'abilities'
                    self.stat_type = 'secondary_knowledge'
                else:
                    # try identity stats
                    self.category, self.stat_type = self._detect_identity_category(self.stat_name)
                    
                    # If not an identity stat, try abilities and other categories
                    if not self.category or not self.stat_type:
                        self.category, self.stat_type = self.detect_ability_category(self.stat_name)

            # Get the stat definition from the database
            stat = Stat.objects.filter(name__iexact=self.stat_name).first()
            if not stat:
                # Try case-insensitive contains search
                matching_stats = Stat.objects.filter(name__icontains=self.stat_name)
                if matching_stats.count() > 1:
                    stat_names = [s.name for s in matching_stats]
                    self.caller.msg(f"Multiple stats match '{self.stat_name}': {', '.join(stat_names)}. Please be more specific.")
                    return
                stat = matching_stats.first()
                if not stat:
                    self.caller.msg(f"Stat '{self.stat_name}' not found.")
                    return

            # Use the canonical name from the database
            self.stat_name = stat.name

            # Special handling for Nature based on character's splat type
            if self.stat_name.lower() == 'nature':
                splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
                char_type = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
                
                # For Changelings and Kinain, Nature is a realm power
                if splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain'):
                    stat.category = 'powers'
                    stat.stat_type = 'realm'
                    self.category = 'powers'
                    self.stat_type = 'realm'
                else:
                    stat.category = 'identity'
                    stat.stat_type = 'personal'
                    self.category = 'identity'
                    self.stat_type = 'personal'
            
            # Special handling for Time based on character's splat type
            elif self.stat_name.lower() == 'time':
                splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
                
                # For Mages, Time is a sphere power
                if splat == 'Mage':
                    stat.category = 'powers'
                    stat.stat_type = 'sphere'
                    self.category = 'powers'
                    self.stat_type = 'sphere'
                else:
                    stat.category = 'attributes'
                    stat.stat_type = 'physical'
                    self.category = 'attributes'
                    self.stat_type = 'physical'

            # Handle instances for background stats
            requires_instance = self._requires_instance(self.stat_name, self.category)
            if requires_instance:
                if not self.instance:
                    self._display_instance_requirement_message(self.stat_name)
                    return
                full_stat_name = f"{self.stat_name}({self.instance})"
            else:
                if self.instance:
                    self.caller.msg(f"|rThe stat '{self.stat_name}' does not support instances.|n")
                    return
                full_stat_name = self.stat_name

            # Handle stat removal (empty value)
            if self.value_change == '':
                if stat.category in self.target.db.stats and stat.stat_type in self.target.db.stats[stat.category]:
                    if full_stat_name in self.target.db.stats[stat.category][stat.stat_type]:
                        del self.target.db.stats[stat.category][stat.stat_type][full_stat_name]
                        self.caller.msg(f"|gRemoved stat '{full_stat_name}'.|n")
                        return
                self.caller.msg(f"|rStat '{full_stat_name}' not found.|n")
                return

            # Initialize the stat structure if needed
            if stat.category not in self.target.db.stats:
                self.target.db.stats[stat.category] = {}
            if stat.stat_type not in self.target.db.stats[stat.category]:
                self.target.db.stats[stat.category][stat.stat_type] = {}

            # Clean up any duplicate flaw entries
            if stat.category == 'flaws':
                # Remove from flaw.flaw if it exists
                if 'flaw' in self.target.db.stats and 'flaw' in self.target.db.stats['flaw']:
                    if full_stat_name in self.target.db.stats['flaw']['flaw']:
                        del self.target.db.stats['flaw']['flaw'][full_stat_name]
                        # Clean up empty categories
                        if not self.target.db.stats['flaw']['flaw']:
                            del self.target.db.stats['flaw']['flaw']
                        if not self.target.db.stats['flaw']:
                            del self.target.db.stats['flaw']

            # Set the stat value
            try:
                # Special handling for Splat changes
                if stat.name == 'Splat' and stat.category == 'other':
                    # Convert splat value to title case
                    new_value = self.value_change.title()
                    
                    # Reset character's stats before setting new splat
                    self.target.db.stats = {
                        'other': {
                            'splat': {
                                'Splat': {
                                    'perm': new_value,
                                    'temp': new_value
                                }
                            }
                        }
                    }
                    
                    # Initialize basic stats based on splat type
                    if new_value == 'Shifter':
                        from world.wod20th.utils.shifter_utils import initialize_shifter_type
                        initialize_shifter_type(self.target, None)  # Initialize with no type yet
                    elif new_value == 'Changeling':
                        from world.wod20th.utils.changeling_utils import initialize_changeling_stats
                        initialize_changeling_stats(self.target)
                    elif new_value == 'Vampire':
                        from world.wod20th.utils.vampire_utils import initialize_vampire_stats
                        initialize_vampire_stats(self.target, None)  # Initialize with no clan yet
                    elif new_value == 'Mage':
                        from world.wod20th.utils.mage_utils import initialize_mage_stats
                        initialize_mage_stats(self.target)
                    elif new_value == 'Mortal+':
                        from world.wod20th.utils.mortalplus_utils import initialize_mortalplus_stats
                        initialize_mortalplus_stats(self.target, None)  # Initialize with no type yet
                    elif new_value == 'Possessed':
                        from world.wod20th.utils.possessed_utils import initialize_possessed_stats
                        initialize_possessed_stats(self.target, None)  # Initialize with no type yet
                    elif new_value == 'Companion':
                        from world.wod20th.utils.companion_utils import initialize_companion_stats
                        initialize_companion_stats(self.target)
                else:
                    # Normal stat handling
                    # Validate and convert the value
                    is_valid, error_msg, new_value = self.validate_stat_value(stat.name, self.value_change, stat.category, stat.stat_type)
                    if not is_valid:
                        self.caller.msg(f"|r{error_msg}|n")
                        return

                    # Special handling for Type changes - initialize appropriate stats
                    if stat.name == 'Type' and stat.category == 'identity':
                        old_type = self.target.get_stat('identity', 'lineage', 'Type', temp=False)
                        
                        # Set the new type first
                        self.target.db.stats[stat.category][stat.stat_type][full_stat_name] = {
                            'perm': new_value,
                            'temp': new_value
                        }
                        
                        # Get the character's splat
                        splat = self.target.get_stat('other', 'splat', 'Splat', temp=False)
                        
                        # Initialize stats based on splat and type
                        if splat == 'Shifter':
                            from world.wod20th.utils.shifter_utils import initialize_shifter_type
                            initialize_shifter_type(self.target, new_value)
                        elif splat == 'Changeling':
                            from world.wod20th.utils.changeling_utils import initialize_changeling_stats
                            initialize_changeling_stats(self.target)
                        elif splat == 'Vampire':
                            from world.wod20th.utils.vampire_utils import initialize_vampire_stats
                            initialize_vampire_stats(self.target, None)  # Initialize with no clan yet
                        elif splat == 'Mage':
                            from world.wod20th.utils.mage_utils import initialize_mage_stats
                            initialize_mage_stats(self.target)
                        elif splat == 'Mortal+':
                            from world.wod20th.utils.mortalplus_utils import initialize_mortalplus_stats
                            initialize_mortalplus_stats(self.target, new_value)
                        elif splat == 'Possessed':
                            from world.wod20th.utils.possessed_utils import initialize_possessed_stats
                            initialize_possessed_stats(self.target, new_value)
                        elif splat == 'Companion':
                            from world.wod20th.utils.companion_utils import initialize_companion_stats
                            initialize_companion_stats(self.target)
                    else:
                        # Normal stat setting
                        self.target.db.stats[stat.category][stat.stat_type][full_stat_name] = {
                            'perm': new_value,
                            'temp': new_value
                        }

                # Update any dependent stats (like willpower, path rating, etc.)
                self._update_dependent_stats(full_stat_name, new_value)

                # Log message for staff
                log_msg = f"{self.caller.name} set {self.target.name}'s {full_stat_name}"
                if hasattr(self, 'value_change') and self.value_change:
                    log_msg += f" to {self.value_change}"
                self.caller.msg(f"|gSuccess: {log_msg}|n")

                # Notify the target player if they're connected
                if self.target.has_account and self.target.sessions.count():
                    self.target.msg(f"|w{self.caller.name} adjusted your {self.stat_name} to {self.value_change}.|n")

            except Exception as e:
                self.caller.msg(f"|rError setting stat: {str(e)}|n")
                return

        except Exception as e:
            self.caller.msg(f"|rError: {str(e)}|n")
            return

class CmdFixStats(MuxCommand):
    """
    Fix character stats by converting string numbers to integers
    and cleaning up duplicate flaw entries.

    Usage:
      +fixstats [<character>]

    If no character is specified, fixes stats for all characters.
    This command will:
    1. Convert string numbers to integers for numeric stats
    2. Clean up duplicate flaw entries
    3. Move flaws to their proper categories
    """

    key = "+fixstats"
    aliases = ["fixstats"]
    locks = "cmd:perm(Admin) or perm(Builder)"
    help_category = "Staff"

    def func(self):
        """Execute the command."""
        from world.wod20th.management.commands.fix_stats import do_fix_stats
        do_fix_stats(self.caller, self.args.strip())

class CmdSetWyrmTaint(MuxCommand):
    """
    Set or remove wyrm taint on a character.

    Usage:
        +wyrm <character> = <on|off>

    Sets or removes the wyrm taint status on a character. This represents
    corruption by the Wyrm and can be used for various game mechanics.
    Only staff members can use this command.

    The character can be anywhere in the game - you don't need to be in 
    the same location.
    """

    key = "+wyrm"
    aliases = ["+wyrmtaint"]
    locks = "cmd:perm(Admin)"
    help_category = "Staff"

    def func(self):
        """Execute command."""
        caller = self.caller

        if not self.args or not self.rhs:
            caller.msg("Usage: +wyrm <character> = <on|off>")
            return

        # Use global search to find the target
        target = caller.search(self.lhs, global_search=True)
        if not target:
            return

        # If target is an account, get their character
        if hasattr(target, 'character'):
            target = target.character

        option = self.rhs.lower()
        if option not in ("on", "off"):
            caller.msg("The option must be either 'on' or 'off'.")
            return

        if option == "on":
            target.tags.add("is_wyrm", category="wyrm_taint")
            caller.msg(f"Added wyrm taint to {target.name}.")
            target.msg("You have been set as part of the Wyrm sphere.")
        else:
            target.tags.remove("is_wyrm", category="wyrm_taint")
            caller.msg(f"Removed wyrm taint from {target.name}.")
            target.msg("You are no longer part of the Wyrm sphere.") 
            