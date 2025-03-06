from evennia import default_cmds
from evennia.utils.ansi import ANSIString
from evennia.utils import inherits_from
from world.wod20th.models import Stat
from world.wod20th.utils.dice_rolls import roll_dice, interpret_roll_results
import re
from difflib import get_close_matches
from datetime import datetime
from random import randint

class CmdRoll(default_cmds.MuxCommand):
    """
    Roll dice for World of Darkness 20th Anniversary Edition.

    Usage:
      +roll <expression> [vs <difficulty>]
      +roll/nightmare [<number>] <expression> [vs <difficulty>]
      +roll/log

    Examples:
      +roll strength+dexterity+3-2
      +roll stre+dex+3-2 vs 7
      +roll/nightmare Legerdemain+Prop vs 6
      +roll/nightmare/3 Legerdemain+Prop vs 6
      +roll/log

    This command allows you to roll dice based on your character's stats
    and any modifiers. You can specify stats by their full name or abbreviation.
    The difficulty is optional and defaults to 6 if not specified.
    Stats that don't exist or have non-numeric values are treated as 0.

    The /nightmare switch is used for Changeling characters to replace regular
    dice with Nightmare dice. The number of Nightmare dice can be specified
    after the switch, or it will default to the character's current Nightmare rating.

    Use +roll/log to view the last 10 rolls made in the current location.
    """

    key = "+roll"
    aliases = ["roll"]
    locks = "cmd:all()"
    help_category = "RP Commands"

    def func(self):
        if self.switches and "log" in self.switches:
            self.display_roll_log()
            return

        # Handle Nightmare dice
        nightmare_dice = 0
        force_nightmare_dice = None
        if self.switches and any(s.startswith('nightmare') for s in self.switches):
            # Check if character is a Changeling
            if not self.caller.db.stats:
                self.caller.msg("Error: Character has no stats.")
                return
                
            # Check if character is a Changeling by checking splat
            splat = self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('temp', '')
            if not splat:
                splat = self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            
            if splat != 'Changeling':
                self.caller.msg("Error: Only Changelings can use Nightmare dice.")
                return

            # Parse the input to check for Arts and Realms
            match = re.match(r'(.*?)(?:\s+vs\s+(\d+))?$', self.args.strip(), re.IGNORECASE)
            if not match:
                self.caller.msg("Invalid roll format. Use: +roll <expression> [vs <difficulty>]")
                return

            expression = match.group(1)
            components = re.split(r'[+-]', expression)
            components = [c.strip().strip('"\'').strip() for c in components if c.strip()]

            # Check if any component is an Art or Realm
            has_art_or_realm = False
            for component in components:
                art_value = self.caller.db.stats.get('powers', {}).get('art', {}).get(component.title(), {}).get('temp', None)
                realm_value = self.caller.db.stats.get('powers', {}).get('realm', {}).get(component.title(), {}).get('temp', None)
                if art_value is not None or realm_value is not None:
                    has_art_or_realm = True
                    break

            if not has_art_or_realm:
                self.caller.msg("Error: Nightmare dice can only be used when rolling Arts + Realms.")
                return

            # First check for forced nightmare dice
            has_forced_dice = False
            if len(self.switches) >= 2 and self.switches[0] == 'nightmare':
                try:
                    force_nightmare_dice = int(self.switches[1])
                    has_forced_dice = True
                    nightmare_dice = force_nightmare_dice
                except ValueError:
                    self.caller.msg("Invalid number of Nightmare dice specified.")
                    return

            # If no forced dice, check if we should use Nightmare rating
            if not has_forced_dice:
                # Check if Nightmare exists in stats
                nightmare_exists = ('Nightmare' in self.caller.db.stats.get('pools', {}).get('other', {}))
                if nightmare_exists:
                    # Get the rating (which might be 0)
                    nightmare_rating = self.caller.db.stats['pools']['other']['Nightmare'].get('temp', 0)
                    if not nightmare_rating:
                        nightmare_rating = self.caller.db.stats['pools']['other']['Nightmare'].get('perm', 0)
                    
                    if 'nightmare' in self.switches:
                        if nightmare_rating > 0:
                            nightmare_dice = nightmare_rating
                        else:
                            nightmare_dice = 0

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
        # First split by operators while preserving them
        components = []
        current = ''
        in_quotes = False
        quote_char = None
        
        for char in expression:
            if char in '"\'':
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                    current += char
                elif char == quote_char:
                    in_quotes = False
                    current += char
                else:
                    current += char
            elif char in '+-' and not in_quotes:
                if current:
                    components.append(('+' if not current.startswith('-') else '-', current.strip('+-')))
                    current = char
                else:
                    current = char
            else:
                current += char
        
        if current:
            components.append(('+' if not current.startswith('-') else '-', current.strip('+-')))

        dice_pool = 0
        description = []
        detailed_description = []
        warnings = []

        for sign, value in components:
            # Remove quotes if present
            value = value.strip().strip('"\'').strip()
            
            if value.replace('-', '').isdigit():  # Handle negative numbers in value
                try:
                    modifier = int(value)
                    dice_pool += modifier if sign == '+' else -modifier
                    description.append(f"{sign} |w{abs(modifier)}|n")
                    detailed_description.append(f"{sign} |w{abs(modifier)}|n")
                except ValueError:
                    warnings.append(f"|rWarning: Invalid number '{value}'.|n")
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

        # Apply health penalties
        health_penalty = self.get_health_penalty(self.caller)
        if health_penalty > 0:
            original_pool = dice_pool
            dice_pool = max(0, dice_pool - health_penalty)
            description.append(f"-|r{health_penalty}|n |w(Health Penalty)|n")
            detailed_description.append(f"-|r{health_penalty}|n |w(Health Penalty)|n")
            if dice_pool == 0 and original_pool > 0:
                warnings.append("|rWarning: Health penalties have reduced your dice pool to 0.|n")

        # After calculating dice_pool, adjust nightmare dice if needed
        if nightmare_dice > 0:
            # Get current Nightmare rating for reference
            current_nightmare = self.caller.db.stats.get('pools', {}).get('other', {}).get('Nightmare', {}).get('temp', 0)
            if not current_nightmare:
                current_nightmare = self.caller.db.stats.get('pools', {}).get('other', {}).get('Nightmare', {}).get('perm', 0)

            # If using forced dice, add them to current rating
            if has_forced_dice:
                nightmare_dice = min(current_nightmare + force_nightmare_dice, dice_pool)
            else:
                nightmare_dice = min(nightmare_dice, dice_pool)

            # Roll dice
            regular_dice = dice_pool - nightmare_dice
            regular_rolls = []
            nightmare_rolls = []
            
            # Roll regular dice
            if regular_dice > 0:
                regular_rolls, regular_successes, regular_ones = roll_dice(regular_dice, difficulty)
            else:
                regular_successes = regular_ones = 0
            
            # Roll nightmare dice
            nightmare_successes = 0
            nightmare_ones = 0
            nightmare_tens = 0
            
            for _ in range(nightmare_dice):
                roll = randint(1, 10)
                nightmare_rolls.append(roll)
                if roll >= difficulty:
                    nightmare_successes += 1
                if roll == 1:
                    nightmare_ones += 1
                if roll == 10:
                    nightmare_tens += 1
            
            # Combine results
            rolls = regular_rolls + nightmare_rolls
            successes = regular_successes + nightmare_successes
            ones = regular_ones + nightmare_ones
            
            # Update nightmare pool if 10s were rolled
            if nightmare_tens > 0:
                current_nightmare = self.caller.db.stats.get('pools', {}).get('other', {}).get('Nightmare', {}).get('temp', 0)
                if not current_nightmare:
                    current_nightmare = self.caller.db.stats.get('pools', {}).get('other', {}).get('Nightmare', {}).get('perm', 0)
                new_nightmare = min(10, current_nightmare + nightmare_tens)
                
                # Ensure the stats structure exists
                if 'pools' not in self.caller.db.stats:
                    self.caller.db.stats['pools'] = {}
                if 'other' not in self.caller.db.stats['pools']:
                    self.caller.db.stats['pools']['other'] = {}
                if 'Nightmare' not in self.caller.db.stats['pools']['other']:
                    self.caller.db.stats['pools']['other']['Nightmare'] = {}
                
                # Update both temp and perm values
                self.caller.db.stats['pools']['other']['Nightmare']['temp'] = new_nightmare
                self.caller.db.stats['pools']['other']['Nightmare']['perm'] = new_nightmare
                
                # Check for Imbalance
                if new_nightmare >= 10:
                    # Reset Nightmare to 0
                    self.caller.db.stats['pools']['other']['Nightmare']['temp'] = 0
                    self.caller.db.stats['pools']['other']['Nightmare']['perm'] = 0
                    
                    # Add Willpower Imbalance
                    current_imbalance = self.caller.db.stats.get('pools', {}).get('other', {}).get('Willpower Imbalance', {}).get('temp', 0)
                    if not current_imbalance:
                        current_imbalance = self.caller.db.stats.get('pools', {}).get('other', {}).get('Willpower Imbalance', {}).get('perm', 0)
                    
                    new_imbalance = min(10, current_imbalance + 1)
                    
                    if 'Willpower Imbalance' not in self.caller.db.stats['pools']['other']:
                        self.caller.db.stats['pools']['other']['Willpower Imbalance'] = {}
                    self.caller.db.stats['pools']['other']['Willpower Imbalance']['temp'] = new_imbalance
                    self.caller.db.stats['pools']['other']['Willpower Imbalance']['perm'] = new_imbalance
                    
                    # Add one point of Glamour
                    if 'pools' in self.caller.db.stats and 'dual' in self.caller.db.stats['pools']:
                        glamour_data = self.caller.db.stats['pools']['dual'].get('Glamour', {})
                        current_glamour = glamour_data.get('temp', glamour_data.get('perm', 0))
                        max_glamour = glamour_data.get('perm', 0)
                        if current_glamour < max_glamour:
                            self.caller.db.stats['pools']['dual']['Glamour']['temp'] = current_glamour + 1
                    
                    warnings.append("|rNightmare has reached 10! Marking Willpower Imbalance and resetting Nightmare to 0.|n")
                    warnings.append("|gGained 1 point of Glamour from Imbalance.|n")
                
                elif nightmare_tens > 0:
                    warnings.append(f"|rGained {nightmare_tens} Nightmare from rolling 10s on Nightmare dice (new total: {new_nightmare}).|n")
            
            # Add Nightmare dice info to descriptions
            if nightmare_dice > 0:
                description.append(f"|r({nightmare_dice} Nightmare dice)|n")
                detailed_description.append(f"|r({nightmare_dice} Nightmare dice - {nightmare_rolls})|n")
        else:
            # Regular roll without Nightmare dice
            rolls, successes, ones = roll_dice(dice_pool, difficulty)
            nightmare_dice = 0  # Ensure nightmare_dice is defined for non-nightmare rolls

        # Interpret the results
        result = interpret_roll_results(successes, ones, rolls=rolls, diff=difficulty, nightmare_dice=nightmare_dice)

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

        # After processing the roll, log it
        try:
            # Format the log description to include total dice count
            log_description = f"Rolling {dice_pool} dice vs {difficulty}"
            # Initialize roll_log if it doesn't exist
            if not hasattr(self.caller.location.db, 'roll_log') or self.caller.location.db.roll_log is None:
                self.caller.location.db.roll_log = []
            self.caller.location.log_roll(self.caller.key, log_description, result)
        except Exception as e:
            # Log the error but don't let it interrupt the roll command
            self.caller.msg("|rWarning: Could not log roll.|n")
            print(f"Roll logging error: {e}")

    def get_stat_value_and_name(self, stat_name):
        """
        Retrieve the value and full name of a stat for the character by searching the character's stats.
        Uses fuzzy matching to handle abbreviations and partial matches.
        Always uses 'temp' value if available, otherwise uses 'perm'.
        """
        if not inherits_from(self.caller, "typeclasses.characters.Character"):
            self.caller.msg("Error: This command can only be used by characters.")
            return 0, stat_name.capitalize()

        character_stats = self.caller.db.stats or {}
        
        # Normalize input but preserve spaces for exact matching
        normalized_input = stat_name.lower().strip()
        normalized_nospace = normalized_input.replace('-', '').replace(' ', '')

        # Get character's splat for context-aware matching
        splat = self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('temp', '')
        if not splat:
            splat = self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')

        # First try exact match in the most relevant category based on splat
        if splat.lower() == 'changeling':
            # For Changelings, check Arts first
            art_value = self.caller.db.stats.get('powers', {}).get('art', {}).get(stat_name.title(), {}).get('temp', None)
            if art_value is not None:
                return art_value, stat_name.title()
            
            # Then check Realms
            realm_value = self.caller.db.stats.get('powers', {}).get('realm', {}).get(stat_name.title(), {}).get('temp', None)
            if realm_value is not None:
                return realm_value, stat_name.title()

        elif splat.lower() == 'shifter':
            # For Shifters, prioritize Gifts over other stats
            gift_value = self.caller.db.stats.get('powers', {}).get('gift', {}).get(stat_name.title(), {}).get('temp', None)
            if gift_value is not None:
                return gift_value, stat_name.title()

            # Special case for Primal-Urge
            if normalized_nospace in ['primalurge', 'primal']:
                if 'abilities' in character_stats and 'talent' in character_stats['abilities']:
                    stat_data = character_stats['abilities']['talent'].get('Primal-Urge', {})
                    if stat_data:
                        if 'temp' in stat_data and stat_data['temp'] != 0:
                            return stat_data['temp'], 'Primal-Urge'
                        return stat_data.get('perm', 0), 'Primal-Urge'
                return 0, 'Primal-Urge'

        # Common abbreviations mapping
        abbreviations = {
            'str': 'strength',
            'dex': 'dexterity',
            'sta': 'stamina',
            'cha': 'charisma',
            'man': 'manipulation',
            'app': 'appearance',
            'per': 'perception',
            'int': 'intelligence',
            'wit': 'wits'
        }

        # Check if input is a common abbreviation
        if normalized_nospace in abbreviations:
            normalized_input = abbreviations[normalized_nospace]
            normalized_nospace = normalized_input

        # Direct check for secondary abilities
        if 'secondary_abilities' in character_stats:
            for ability_type, abilities in character_stats['secondary_abilities'].items():
                for stat, stat_data in abilities.items():
                    if stat.lower() == normalized_input:
                        if 'temp' in stat_data and stat_data['temp'] != 0:
                            return stat_data['temp'], stat
                        return stat_data.get('perm', 0), stat

        # Gather all stats with their full paths
        all_stats = []
        
        # Check regular stats
        for category, cat_stats in character_stats.items():
            if category == 'secondary_abilities':
                continue  # Skip here, we already handled secondary abilities
            for stat_type, stats in cat_stats.items():
                for stat, stat_data in stats.items():
                    normalized_name = stat.lower()
                    normalized_nospace_name = normalized_name.replace('-', '').replace(' ', '')
                    all_stats.append((normalized_name, normalized_nospace_name, stat, category, stat_type, stat_data))

        # First try exact matches with spaces
        exact_matches = [s for s in all_stats if s[0] == normalized_input]
        if exact_matches:
            _, _, full_name, category, stat_type, stat_data = exact_matches[0]
            if 'temp' in stat_data:
                return stat_data['temp'], full_name
            return stat_data.get('perm', 0), full_name

        # Try without spaces
        exact_matches = [s for s in all_stats if s[1] == normalized_nospace]
        if exact_matches:
            _, _, full_name, category, stat_type, stat_data = exact_matches[0]
            if 'temp' in stat_data:
                return stat_data['temp'], full_name
            return stat_data.get('perm', 0), full_name

        # If no exact match, try prefix matching
        prefix_matches = [s for s in all_stats if s[0].startswith(normalized_input) or s[1].startswith(normalized_nospace)]
        if prefix_matches:
            prefix_matches.sort(key=lambda x: len(x[0]))  # Sort by length to get shortest match
            _, _, full_name, category, stat_type, stat_data = prefix_matches[0]
            if 'temp' in stat_data:
                return stat_data['temp'], full_name
            return stat_data.get('perm', 0), full_name

        return 0, stat_name.capitalize()

    def display_roll_log(self):
        """
        Display the roll log for the current room.
        """
        room = self.caller.location
        # Initialize roll_log if it doesn't exist
        if not hasattr(room.db, 'roll_log') or room.db.roll_log is None:
            room.db.roll_log = []
        roll_log = room.get_roll_log()

        if not roll_log:
            self.caller.msg("No rolls have been logged in this location yet.")
            return

        header = "|yRecent rolls in this location:|n"
        log_entries = []
        for entry in roll_log:
            timestamp = entry['timestamp']
            if isinstance(timestamp, datetime):
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                # Assume it's already a string or has a string representation
                timestamp_str = str(timestamp)
            log_entries.append(f"{timestamp_str} - {entry['roller']}: {entry['description']} => {entry['result']}")

        self.caller.msg(header + "\n" + "\n".join(log_entries))

    def get_stat_value(self, character, stat_name):
        temp_value = character.get_stat(category='abilities', stat_type='knowledge', name=stat_name, temp=True)
        if not temp_value:
            # Fall back to permanent value if temp is 0 or None
            temp_value = character.get_stat(category='abilities', stat_type='knowledge', name=stat_name, temp=False)
        return temp_value or 0

    def get_health_penalty(self, character):
        """
        Calculate dice penalty based on character's health levels.
        Returns the number of dice to subtract from the pool.
        """
        # Get current damage levels
        bashing = character.db.bash or 0
        lethal = character.db.leth or 0
        aggravated = character.db.agg or 0
        
        # Calculate total damage
        total_damage = bashing + lethal + aggravated
        
        # Get base health levels (7) plus any bonuses
        base_health = 7
        
        # Check for Huge Size merit
        huge_size = character.get_stat('merits', 'physical', 'Huge Size', temp=False)
        if not huge_size:
            huge_size = character.get_stat('merits', 'merit', 'Huge Size', temp=False)
        if huge_size:
            base_health += 1
        
        # Check for Glome phyla
        glome_phyla = character.get_stat('identity', 'lineage', 'Phyla') == 'Glome'
        if not glome_phyla:
            glome_phyla = character.get_stat('identity', 'phyla', 'Phyla') == 'Glome'
        if glome_phyla:
            base_health += 2
        
        # Check for Troll kith
        if character.get_stat('identity', 'lineage', 'Kith') == 'Troll':
            base_health += 1

        # Calculate penalty based on damage relative to total health
        if total_damage <= 2:  # First two health levels (Bruised)
            return 0
        elif total_damage <= 4:  # Hurt/Injured (-1)
            return 1
        elif total_damage <= 6:  # Wounded/Mauled (-2)
            return 2
        elif total_damage <= base_health - 2:  # Crippled (-5)
            return 5
        
        return 0
