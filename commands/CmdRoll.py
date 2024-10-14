from evennia import default_cmds
from evennia.utils.ansi import ANSIString
from evennia.utils import inherits_from
from world.wod20th.models import Stat
from world.wod20th.utils.dice_rolls import roll_dice, interpret_roll_results
import re
from difflib import get_close_matches

class CmdRoll(default_cmds.MuxCommand):
    """
    Roll dice for World of Darkness 20th Anniversary Edition.

    Usage:
      +roll <expression> [vs <difficulty>]

    Examples:
      +roll strength+dexterity+3-2
      +roll stre+dex+3-2 vs 7

    This command allows you to roll dice based on your character's stats
    and any modifiers. You can specify stats by their full name or abbreviation.
    The difficulty is optional and defaults to 6 if not specified.
    Stats that don't exist or have non-numeric values are treated as 0.
    """

    key = "+roll"
    aliases = ["roll"]
    locks = "cmd:all()"
    help_category = "Game"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: +roll <expression> [vs <difficulty>]")
            return

        # Parse the input
        match = re.match(r'(.*?)(?:\s+vs\s+(\d+))?$', self.args.strip(), re.IGNORECASE)
        if not match:
            self.caller.msg("Invalid roll format. Use: +roll <expression> [vs <difficulty>]")
            return

        expression, difficulty = match.groups()
        difficulty = int(difficulty) if difficulty else 6

        # Process the expression
        components = re.findall(r'([+-])?\s*(\w+|\d+)', expression)
        dice_pool = 0
        description = []
        detailed_description = []
        warnings = []

        for sign, value in components:
            sign = sign or '+'  # Default to '+' if no sign is given
            if value.isdigit():
                modifier = int(value)
                dice_pool += modifier if sign == '+' else -modifier
                description.append(f"{sign} |w{value}|n")
                detailed_description.append(f"{sign} |w{value}|n")
            else:
                try:
                    stat_value, full_name = self.get_stat_value_and_name(value)
                except AttributeError:
                    stat_value, full_name = 0, value
                    
                if stat_value > 0:
                    dice_pool += stat_value if sign == '+' else -stat_value
                    description.append(f"{sign}|n |w{full_name}|n")
                    detailed_description.append(f"{sign} |w{full_name} ({stat_value})|n")
                elif stat_value == 0 and full_name:
                    description.append(f"{sign} |w{full_name}|n")
                    detailed_description.append(f"{sign} |w{full_name} (0)|n")
                    warnings.append(f"|rWarning: Stat '{full_name}' not found or has no value. Treating as 0.|n")
                else:
                    description.append(f"{sign} |h|x{full_name}|n")
                    detailed_description.append(f"{sign} |h|x{full_name} (0)|n")
                    warnings.append(f"|rWarning: Stat '{full_name}' not found or has no value. Treating as 0.|n")

        # Roll the dice using our utility function
        rolls, successes, ones = roll_dice(dice_pool, difficulty)
        
        # Interpret the results
        result = interpret_roll_results(successes, ones, rolls=rolls, diff=difficulty)

        # Format the outputs
        public_description = " ".join(description)
        private_description = " ".join(detailed_description)
        
        public_output = f"|rRoll>|n {self.caller.db.gradient_name or self.caller.key} |yrolls |n{public_description} |yvs {difficulty} |r=>|n {result}"
        private_output = f"|rRoll> |yYou roll |n{private_description} |yvs {difficulty} |r=>|n {result}"
        builder_output = f"|rRoll> |n{self.caller.db.gradient_name or self.caller.key} rolls {private_description} |yvs {difficulty}|r =>|n {result}"

        # Send outputs
        self.caller.msg(private_output)
        if warnings:
            self.caller.msg("\n".join(warnings))

        # Send builder to builders, and public to everyone else
        for obj in self.caller.location.contents:
            if inherits_from(obj, "typeclasses.characters.Character") and obj != self.caller:
                if obj.locks.check_lockstring(obj, "perm(Builder)"):
                    obj.msg(builder_output)
                else:
                    obj.msg(public_output)

    def get_stat_value_and_name(self, stat_name):
        """
        Retrieve the value and full name of a stat for the character by searching the character's stats.
        Returns the closest matching stat if an exact match is not found.
        Uses 'temp' value if available and non-zero, otherwise uses 'perm'.
        """
        if not inherits_from(self.caller, "typeclasses.characters.Character"):
            self.caller.msg("Error: This command can only be used by characters.")
            return 0, stat_name.capitalize()

        character_stats = self.caller.db.stats or {}
        all_stats = []

        # Flatten the nested dictionary structure
        for category in character_stats.values():
            for stat_type in category.values():
                all_stats.extend(stat_type.keys())

        # Find the closest matching stat name
        closest_matches = get_close_matches(stat_name.lower(), [s.lower() for s in all_stats], n=1, cutoff=0.6)
        
        if closest_matches:
            closest_match = next(s for s in all_stats if s.lower() == closest_matches[0])
            
            # Find the category and stat_type for the matched stat
            for category, cat_stats in character_stats.items():
                for stat_type, stats in cat_stats.items():
                    if closest_match in stats:
                        stat_data = stats[closest_match]
                        temp_value = stat_data.get('temp', 0)
                        perm_value = stat_data.get('perm', 0)
                        
                        # Use temp value if it's non-zero, otherwise use perm value
                        value = temp_value if temp_value != 0 else perm_value
                        
                        try:
                            return int(value), closest_match
                        except ValueError:
                            return 0, closest_match

        # If no matching stat is found, return 0 and the capitalized input
        return 0, stat_name.capitalize()