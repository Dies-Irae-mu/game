from evennia import default_cmds
from world.wod20th.models import Stat
from evennia.locks.lockhandler import LockHandler

class CmdStats(default_cmds.MuxCommand):
    """
    Usage:
      +stats <character>/<stat>[(<instance>)]/<category>=[+-]<value>
      +stats me/<stat>[(<instance>)]/<category>=[+-]<value>
      +stats <character>=reset
      +stats me=reset

    Examples:
      +stats Bob/Strength/Physical=+2
      +stats Alice/Firearms/Skill=-1
      +stats John/Status(Ventrue)/Social=
      +stats me=reset
      +stats me/Strength=3
    """

    key = "stats"
    aliases = ["stat"]
    locks = "cmd:perm(Builder)"  # Only Builders and above can use this command
    help_category = "Chargen & Character Info"

    def parse(self):
        """
        Parse the arguments.
        """
        self.character_name = ""
        self.stat_name = ""
        self.instance = None
        self.category = None
        self.value_change = None
        self.temp = False

        try:
            args = self.args.strip()

            if '=' in args:
                first_part, second_part = args.split('=', 1)
                if second_part.lower().strip() == 'reset':
                    self.character_name = first_part.strip()
                    self.stat_name = 'reset'
                    return
                self.value_change = second_part.strip()
            else:
                first_part = args

            if '/' in first_part:
                self.character_name, stat_part = first_part.split('/', 1)
            else:
                self.character_name = first_part
                stat_part = ''

            try:
                if '(' in stat_part and ')' in stat_part:
                    self.stat_name, instance_and_category = stat_part.split('(', 1)
                    self.instance, self.category = instance_and_category.split(')', 1)
                    self.category = self.category.lstrip('/').strip() if '/' in self.category else None
                else:
                    parts = stat_part.split('/')
                    if len(parts) == 3:
                        self.stat_name, self.instance, self.category = parts
                    elif len(parts) == 2:
                        self.stat_name, self.category = parts
                    else:
                        self.stat_name = parts[0]

                    self.stat_name = self.stat_name.strip()
                    self.instance = self.instance.strip() if self.instance else None
                    self.category = self.category.strip() if self.category else None

            except ValueError:
                self.stat_name = stat_part.strip()
            except UnboundLocalError:
                self.stat_name = stat_part.strip()

        except ValueError:
            self.character_name = self.stat_name = self.value_change = self.instance = self.category = None

    def func(self):
        """Implement the command"""

        if not self.character_name:
            self.caller.msg("|rUsage: +stats <character>/<stat>[(<instance>)]/[<category>]=[+-]<value>|n")
            return

        if self.character_name.lower().strip() == 'me':
            character = self.caller
        else:
            character = self.caller.search(self.character_name)

        if not character:
            self.caller.msg(f"|rCharacter '{self.character_name}' not found.|n")
            return

        # Handle the reset command
        if self.stat_name and self.stat_name.lower() == 'reset':
            character.db.stats = {}
            self.caller.msg(f"|gReset all stats for {character.name}.|n")
            character.msg(f"|y{self.caller.name}|n |greset all your stats.|n")
            return

        if not self.stat_name:
            self.caller.msg("|rUsage: +stats <character>/<stat>[(<instance>)]/[<category>]=[+-]<value>|n")
            return

        # Fetch the stat definition from the database
        try:
            if self.category:
                matching_stats = Stat.objects.filter(name__icontains=self.stat_name.strip(), category__iexact=self.category.strip())
            else:
                matching_stats = Stat.objects.filter(name__icontains=self.stat_name.strip())
        except Exception as e:
            self.caller.msg(f"|rError fetching stats: {e}|n")
            return

        if not matching_stats.exists():
            self.caller.msg(f"|rNo stats matching '{self.stat_name}' found in the database.|n")
            return

        if len(matching_stats) > 1:
            self.caller.msg(f"|rMultiple stats matching '{self.stat_name}' found: {[stat.name for stat in matching_stats]}. Please be more specific.|n")
            return

        stat = matching_stats.first()
        full_stat_name = stat.name

        # Check if the stat is instanced and handle accordingly
        if stat.instanced:
            if not self.instance:
                self.caller.msg(f"|rThe stat '{full_stat_name}' requires an instance. Use the format: {full_stat_name}(instance)|n")
                return
            full_stat_name = f"{full_stat_name}({self.instance})"
        elif self.instance:
            self.caller.msg(f"|rThe stat '{full_stat_name}' does not support instances.|n")
            return

        # Check if the character passes the stat's lock_string
        try:
            if stat.lockstring and not character.locks.check_lockstring(character, stat.lockstring):
                self.caller.msg(f"|rYou do not have permission to modify the stat '{full_stat_name}' for {character.name}.|n")
                return
        except AttributeError:
            pass
        
        # Determine if the stat should be removed
        if self.value_change == '':
            current_stats = character.db.stats.get(stat.category, {}).get(stat.stat_type, {})
            if full_stat_name in current_stats:
                del current_stats[full_stat_name]
                character.db.stats[stat.category][stat.stat_type] = current_stats
                self.caller.msg(f"|gRemoved stat '{full_stat_name}' from {character.name}.|n")
                character.msg(f"|y{self.caller.name}|n |rremoved your stat|n '|y{full_stat_name}|n'.")
            else:
                self.caller.msg(f"|rStat '{full_stat_name}' not found on {character.name}.|n")
            return

        # Determine if the stat value should be treated as a number or a string
        try:
            value_change = int(self.value_change)
            is_number = True
        except (ValueError, TypeError):
            value_change = self.value_change
            is_number = False

        # Check if the stat exists for the character and get the current value
        if not hasattr(character.db, "stats"):
            character.db.stats = {}

        current_value = character.get_stat(stat.category, stat.stat_type, full_stat_name, temp=self.temp)
        if current_value is None:
            # Initialize the stat if it doesn't exist
            current_value = 0 if is_number else ''

        if self.value_change and (self.value_change.startswith('+') or self.value_change.startswith('-')):
            if is_number:
                new_value = current_value + value_change
            else:
                self.caller.msg(f"|rIncrement/decrement values must be integers.|n")
                return
        else:
            new_value = value_change

        # Validate the new value against the stat's valid values
        valid_values = stat.values
        if valid_values and new_value not in valid_values and valid_values != []:
            self.caller.msg(f"|rValue '{new_value}' is not valid for stat '{full_stat_name}'. Valid values are: {valid_values}|n")
            return

        # Update the stat
        character.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=self.temp)

        self.caller.msg(f"|gUpdated {character.name}'s {full_stat_name} to {new_value}.|n")
        character.msg(f"|y{self.caller.name}|n |gupdated your|n '|y{full_stat_name}|n' |gto|n '|y{new_value}|n'.")



from evennia.commands.default.muxcommand import MuxCommand
from world.wod20th.models import Stat
from evennia.utils import search

class CmdSpecialty(MuxCommand):
    """
    Usage:
      +stats/specialty <character>/<stat>=<specialty>
      +stats/specialty me/<stat>=<specialty>

    Examples:
      +stats/specialty Bob/Firearms=Sniping
      +stats/specialty me/Firearms=Sniping
    """

    key = "+stats/specialty"
    aliases = ["stat/specialty","specialty", "spec"]
    locks = "cmd:perm(Builder)"  # Only Builders and above can use this command
    help_category = "Chargen & Character Info"

    def parse(self):
        """
        Parse the arguments.
        """
        self.character_name = ""
        self.stat_name = ""
        self.specialty = ""

        try:
            args = self.args.strip()
            first_part, self.specialty = args.split('=', 1)

            if '/' in first_part:
                self.character_name, self.stat_name = first_part.split('/', 1)
            else:
                self.character_name = first_part

            self.character_name = self.character_name.strip()
            self.stat_name = self.stat_name.strip()
            self.specialty = self.specialty.strip()

        except ValueError:
            self.character_name = self.stat_name = self.specialty = None

    def func(self):
        """Implement the command"""

        if not self.character_name or not self.stat_name or not self.specialty:
            self.caller.msg("|rUsage: +stats/specialty <character>/<stat>=<specialty>|n")
            return

        if self.character_name.lower().strip() == 'me':
            character = self.caller
        else:
            character = self.caller.search(self.character_name)

        if not character:
            self.caller.msg(f"|rCharacter '{self.character_name}' not found.|n")
            return

        # Fetch the stat definition from the database
        try:
            matching_stats = Stat.objects.filter(name__icontains=self.stat_name.strip())
        except Exception as e:
            self.caller.msg(f"|rError fetching stats: {e}|n")
            return

        if not matching_stats.exists():
            self.caller.msg(f"|rNo stats matching '{self.stat_name}' found in the database.|n")
            return

        if len(matching_stats) > 1:
            self.caller.msg(f"|rMultiple stats matching '{self.stat_name}' found: {[stat.name for stat in matching_stats]}. Please be more specific.|n")
            return

        stat = matching_stats.first()
        stat_name = stat.name

        specialties = character.db.specialties or {}
        if not specialties.get(stat_name):
            specialties[stat_name] = []
        specialties[stat_name].append(self.specialty)
        character.db.specialties = specialties

        self.caller.msg(f"|gAdded specialty '{self.specialty}' to {character.name}'s {stat_name}.|n")
        character.msg(f"|y{self.caller.name}|n |gadded the specialty|n '|y{self.specialty}|n' |gto your {stat_name}.|n")
