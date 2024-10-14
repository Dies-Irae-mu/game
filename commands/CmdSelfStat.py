from evennia import default_cmds
from world.wod20th.models import Stat, SHIFTER_IDENTITY_STATS, SHIFTER_RENOWN, calculate_willpower, calculate_road
from evennia.utils import search

class CmdSelfStat(default_cmds.MuxCommand):
    """
    Usage:
      +selfstat <stat>[(<instance>)]/<category>=[+-]<value>
      +selfstat <stat>[(<instance>)]/<category>=

    Examples:
      +selfstat Strength/Physical=+1
      +selfstat Firearms/Skill=-1
      +selfstat Status(Ventrue)/Social=
    """

    key = "+selfstat"
    aliases = ["selfstat"]
    locks = "cmd:all()"  # All players can use this command
    help_category = "Character"

    def parse(self):
        """
        Parse the arguments.
        """
        self.stat_name = ""
        self.instance = None
        self.category = None
        self.value_change = None
        self.temp = False

        try:
            args = self.args.strip()

            if '=' in args:
                first_part, second_part = args.split('=', 1)
                self.value_change = second_part.strip()
            else:
                first_part = args

            try:
                if '(' in first_part and ')' in first_part:
                    self.stat_name, instance_and_category = first_part.split('(', 1)
                    self.instance, self.category = instance_and_category.split(')', 1)
                    self.category = self.category.lstrip('/').strip() if '/' in self.category else None
                else:
                    parts = first_part.split('/')
                    if len(parts) == 2:
                        self.stat_name, self.category = parts
                    else:
                        self.stat_name = parts[0]

                self.stat_name = self.stat_name.strip()
                self.instance = self.instance.strip() if self.instance else None
                self.category = self.category.strip() if self.category else None

            except ValueError:
                self.stat_name = first_part.strip()

        except ValueError:
            self.stat_name = self.value_change = self.instance = self.category = None

    def func(self):
        """Implement the command"""
        character = self.caller

        if not self.stat_name:
            self.caller.msg("|rUsage: +selfstat <stat>[(<instance>)]/[<category>]=[+-]<value>|n")
            return

        # Fetch the stat definition from the database
        try:
            matching_stats = Stat.objects.filter(name__iexact=self.stat_name.strip())
            
            if not matching_stats.exists():
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
                self.caller.msg(f"|rYou do not have permission to modify the stat '{full_stat_name}'.|n")
                return
        except AttributeError:
            pass

        # Determine if the stat should be removed
        if self.value_change == '':
            current_stats = character.db.stats.get(stat.category, {}).get(stat.stat_type, {})
            if full_stat_name in current_stats:
                del current_stats[full_stat_name]
                character.db.stats[stat.category][stat.stat_type] = current_stats
                self.caller.msg(f"|gRemoved stat '{full_stat_name}'.|n")
            else:
                self.caller.msg(f"|rStat '{full_stat_name}' not found.|n")
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

        # Convert value to integer for virtues
        if full_stat_name in ['Courage', 'Self-Control', 'Conscience', 'Conviction', 'Instinct']:
            try:
                new_value = int(new_value)
            except ValueError:
                self.caller.msg(f"|rInvalid value for {full_stat_name}. Please provide an integer.|n")
                return

        # Update the stat
        character.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=False)
        
        # If the stat is in the 'pools' category or has a 'dual' stat_type, update the temporary value as well
        if stat.category == 'pools' or stat.stat_type == 'dual':
            character.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=True)
            self.caller.msg(f"|gUpdated {full_stat_name} to {new_value} (both permanent and temporary).|n")
        else:
            self.caller.msg(f"|gUpdated {full_stat_name} to {new_value}.|n")

        # After setting a stat, recalculate Willpower and Road
        if full_stat_name in ['Courage', 'Self-Control', 'Conscience', 'Conviction', 'Instinct']:
            new_willpower = calculate_willpower(character)
            character.set_stat('pools', 'dual', 'Willpower', new_willpower, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', new_willpower, temp=True)
            self.caller.msg(f"|gRecalculated Willpower to {new_willpower}.|n")

            new_road = calculate_road(character)
            character.set_stat('pools', 'moral', 'Road', new_road, temp=False)
            self.caller.msg(f"|gRecalculated Road to {new_road}.|n")