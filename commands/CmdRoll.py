from evennia import default_cmds
from evennia.utils.ansi import ANSIString
from evennia.utils import inherits_from
from world.wod20th.models import Stat
from world.wod20th.utils.dice_rolls import roll_dice, interpret_roll_results
from world.jobs.models import Job
from django.utils import timezone
import re
from difflib import get_close_matches
from datetime import datetime
from random import randint
from evennia.utils import logger

class CmdRoll(default_cmds.MuxCommand):
    """
    Roll dice for World of Darkness 20th Anniversary Edition.

    Usage (aliases are after the pipe symbol):
      +roll <expression> [vs <difficulty>] [--job <id>]
          Note that you must put a space between the stat name and the + or - operator,
          otherwise it will be interpreted as part of the stat name (like a hyphen).
      +roll/log|l - This will display the last 10 rolls made in this location.
      +roll/specialty|spec|s <expression> [vs <difficulty>] [--job <id>]
          This will count any 10s rolled as 2 successes. You can also use this as an
          additional switch on top of another roll, such as +roll/10/specialty 
          or +roll/reflexive/specialty.
          Aliases are +roll/spec, +roll/s.
      +roll/10|10s|tens|ten <expression> [vs <difficulty>] [--job <id>]
          This will use the "exploding 10s" rule, where any 10 rolled will generate
          an additional die roll. If that roll is also a 10, it explodes again, and
          so on until no more 10s are rolled.
      +roll/reflexive|ref|r <expression> [vs <difficulty>] [--job <id>]
          This will roll for a reflexive action, which does not apply health penalties.

      Changling-specific Command:    
      +roll/nightmare|night|n/[<number>] <expression> [vs <difficulty>] [--job <id>]
          You can use this in two ways: if you specify a positive number it will use that many
          Nightmare dice, otherwise it will use the character's current Nightmare rating.

    Examples:
      +roll strength + dexterity + 3 - 2
      +roll stre + dex + 3- 2 vs 7
      +roll/specialty dexterity + brawl vs 6
      +roll/10/specialty strength + melee vs 6
      +roll/nightmare Legerdemain + Prop vs 6
      +roll/nightmare/3 Legerdemain + Prop vs 6
      +roll/log
      +roll/ref/specialty Stamina + Primal-Urge vs 6
      +roll strength + brawl vs 7 --job 42

    This command allows you to roll dice based on your character's stats
    and any modifiers. You can specify stats by their full name or abbreviation.
    The difficulty is optional and defaults to 6 if not specified.
    Stats that don't exist or have non-numeric values are treated as 0.

    The --job option allows you to submit the roll result as a comment to a job.
    You must have permission to comment on the specified job.
    """

    key = "+roll"
    aliases = ["roll"]
    locks = "cmd:all()"
    help_category = "RP Commands"

    def func(self):
        if self.switches and "log" in self.switches:
            self.display_roll_log()
            return

        # Check for job option at the end of the command
        job_id = None
        args = self.args.strip()
        rolling_to_job = False
        
        # Look for --job at the end of the command
        if args.endswith('--job'):
            self.caller.msg("Usage: +roll <expression> [vs <difficulty>] [--job <id>]")
            return
            
        job_parts = args.split(' --job ')
        if len(job_parts) > 1:
            args = job_parts[0].strip()
            rolling_to_job = True
            try:
                job_id = int(job_parts[1].strip())
                
                # Verify job exists and user has permission
                try:
                    job = Job.objects.get(id=job_id)
                    if not (job.requester == self.caller.account or 
                            job.participants.filter(id=self.caller.account.id).exists() or 
                            self.caller.check_permstring("Admin")):
                        self.caller.msg("You don't have permission to comment on this job.")
                        return
                except Job.DoesNotExist:
                    self.caller.msg(f"Job #{job_id} not found.")
                    return
                    
            except ValueError:
                self.caller.msg("Invalid job ID. Must be a number.")
                return
            except IndexError:
                self.caller.msg("Usage: +roll <expression> [vs <difficulty>] [--job <id>]")
                return

        # Check if in a Quiet Room - only allow with job option
        if (hasattr(self.caller.location, 'db') and 
            hasattr(self.caller.location.db, 'roomtype') and
            self.caller.location.db.roomtype == 'Quiet Room' and
            not rolling_to_job):
            # Only allow rolls in Quiet Rooms with the --job option
            self.caller.msg("|rYou are in a Quiet Room. You can only roll with the --job option.|n")
            return

        # Store original args and restore after job check
        self.args = args

        # Define valid switches
        valid_switches = [
            '10', '10s', 'tens', 'ten',           # Exploding 10s (unsure if this is used often in wod20th; here for completion)
            'specialty', 'spec', 's',             # Specialty (double 10s)
            'reflexive', 'ref', 'reflex', 'r',    # Reflexive (no health penalty)
            'nightmare', 'night', 'n',            # Nightmare (Changeling only)
            'log', 'l'                             # Roll log
        ]
        
        # Check for invalid switches
        if self.switches:
            # Look for numeric nightmare dice specification (e.g., nightmare/3)
            nightmare_number_switch = False
            if len(self.switches) >= 2 and self.switches[0] in ['nightmare', 'night', 'n']:
                try:
                    int(self.switches[1])  # Just try to convert to int to verify it's a number
                    nightmare_number_switch = True
                except ValueError:
                    pass
            
            # Check each switch to see if it's valid
            invalid_switches = []
            for switch in self.switches:
                # Skip the numeric part of nightmare/N
                if nightmare_number_switch and self.switches[0] in ['nightmare', 'night', 'n'] and self.switches.index(switch) == 1:
                    if not switch.isdigit():
                        invalid_switches.append(switch)
                # Check all other switches
                elif switch not in valid_switches:
                    invalid_switches.append(switch)
            
            # If there are invalid switches, show an error
            if invalid_switches:
                self.caller.msg(f"|rError: Invalid switch(es): {', '.join(invalid_switches)}|n")
                self.caller.msg("Valid switches are: log, specialty (spec, s), 10 (10s, tens, ten), reflexive (ref, reflex, r), nightmare (night, n)")
                return

        # Check for various switches
        use_10s = any(s in ['10', '10s', 'tens', 'ten'] for s in self.switches) if self.switches else False
        use_specialty = any(s in ['specialty', 'spec', 's'] for s in self.switches) if self.switches else False
        use_reflexive = any(s in ['reflexive', 'ref', 'reflex', 'r'] for s in self.switches) if self.switches else False

        # Handle Nightmare dice
        nightmare_dice = 0
        force_nightmare_dice = None
        if self.switches and any(s in ['nightmare', 'night', 'n'] for s in self.switches):
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
            if len(self.switches) >= 2 and self.switches[0] in ['nightmare', 'night', 'n']:
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
                    nightmare_rating = self.caller.db.stats['pools']['other']['Nightmare'].get('perm', 0)
                    
                    if any(s in ['nightmare', 'night', 'n'] for s in self.switches):
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

        # Process the expression by properly handling standalone + and - operators
        components = []
        
        # Manually separate components with a simpler approach
        # First split by + operator
        # This assumes + and - are used as standalone operators, not within stat names
        plus_parts = re.split(r'(?<!\w)\+(?!\w)', expression)
        
        for plus_index, plus_part in enumerate(plus_parts):
            # Split each part by - operator
            minus_parts = re.split(r'(?<!\w)-(?!\w)', plus_part)
            
            # Process the first part with + operator (or implicit + if it's the first part)
            if minus_parts[0].strip():
                components.append(('+', minus_parts[0].strip()))
            
            # Process subsequent parts with - operator
            for minus_part in minus_parts[1:]:
                if minus_part.strip():
                    components.append(('-', minus_part.strip()))
        
        # If the components are empty, something went wrong
        if not components:
            self.caller.msg("Could not parse roll expression. Try a simpler format like 'stat1 + stat2'.")
            return
        
        dice_pool = 0
        description = []
        detailed_description = []
        warnings = []

        for i, (sign, value) in enumerate(components):
            # Remove quotes if present
            value = value.strip().strip('"\'').strip()
            
            if value.replace('-', '').isdigit():  # Handle negative numbers in value
                try:
                    modifier = int(value)
                    dice_pool += modifier if sign == '+' else -modifier
                    # Only add sign for components after the first one
                    if i == 0:
                        description.append(f"|w{abs(modifier)}|n")
                        detailed_description.append(f"|w{abs(modifier)}|n")
                    else:
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
                    # Only add sign for components after the first one
                    if i == 0:
                        description.append(f"|w{full_name}|n")
                        detailed_description.append(f"|w{full_name} ({stat_value})|n")
                    else:
                        description.append(f"{sign} |w{full_name}|n")
                        detailed_description.append(f"{sign} |w{full_name} ({stat_value})|n")
                elif stat_value == 0 and full_name:
                    # Only add sign for components after the first one
                    if i == 0:
                        description.append(f"|w{full_name}|n")
                        detailed_description.append(f"|w{full_name} (0)|n")
                    else:
                        description.append(f"{sign} |w{full_name}|n")
                        detailed_description.append(f"{sign} |w{full_name} (0)|n")
                    warnings.append(f"|rWarning: Stat '{full_name}' not found or has no value. Treating as 0.|n")
                else:
                    # Only add sign for components after the first one
                    if i == 0:
                        description.append(f"|h|x{full_name}|n")
                        detailed_description.append(f"|h|x{full_name} (0)|n")
                    else:
                        description.append(f"{sign} |h|x{full_name}|n")
                        detailed_description.append(f"{sign} |h|x{full_name} (0)|n")
                    warnings.append(f"|rWarning: Stat '{full_name}' not found or has no value. Treating as 0.|n")

        # Apply health penalties
        health_penalty = self.get_health_penalty(self.caller)
        
        # For reflexive actions, ignore health penalties completely
        if use_reflexive:
            # Don't apply the health penalty
            health_penalty_description = f"|c(Reflexive: Ignoring health penalty of {health_penalty})|n"
            if health_penalty > 0:
                description.append(health_penalty_description)
                detailed_description.append(health_penalty_description)
            # Reset health_penalty to 0 for reflexive actions
            health_penalty = 0
        elif health_penalty > 0:
            original_pool = dice_pool
            dice_pool = max(0, dice_pool - health_penalty)
            description.append(f"-|r{health_penalty}|n |w(Health Penalty)|n")
            detailed_description.append(f"-|r{health_penalty}|n |w(Health Penalty)|n")
            # Only add a warning about reduced dice pool if it's reduced to zero
            if dice_pool == 0 and original_pool > 0:
                warnings.append("|rWarning: Health penalties have reduced your dice pool to 0.|n")

        # After calculating dice_pool, adjust nightmare dice if needed
        if nightmare_dice > 0:
            # Get current Nightmare rating for reference
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
                    current_imbalance = self.caller.db.stats.get('pools', {}).get('other', {}).get('Willpower Imbalance', {}).get('perm', 0)
                    
                    new_imbalance = min(10, current_imbalance + 1)
                    
                    if 'Willpower Imbalance' not in self.caller.db.stats['pools']['other']:
                        self.caller.db.stats['pools']['other']['Willpower Imbalance'] = {}
                    self.caller.db.stats['pools']['other']['Willpower Imbalance']['temp'] = new_imbalance
                    self.caller.db.stats['pools']['other']['Willpower Imbalance']['perm'] = new_imbalance
                    
                    # Add one point of Glamour
                    if 'pools' in self.caller.db.stats and 'dual' in self.caller.db.stats['pools']:
                        glamour_data = self.caller.db.stats['pools']['dual'].get('Glamour', {})
                        current_glamour = glamour_data.get('temp', 0)
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
            # For 10s/exploding dice and specialty rolls
            if use_10s and use_specialty:
                # Handle combined 10s and specialty
                all_rolls = []
                extra_rolls = []
                extra_successes = 0
                specialty_bonus = 0
                
                # Initial roll
                initial_rolls, initial_successes, initial_ones = roll_dice(dice_pool, difficulty)
                all_rolls.extend(initial_rolls)
                
                # Count 10s for specialty bonus
                tens_count = sum(1 for roll in initial_rolls if roll == 10)
                specialty_bonus = tens_count
                
                # Add specialty bonus
                successes = initial_successes + specialty_bonus
                ones = initial_ones
                
                # Handle exploding 10s - reroll any 10s
                tens_to_reroll = [i for i, roll in enumerate(initial_rolls) if roll == 10]
                reroll_generation = 1
                
                while tens_to_reroll:
                    current_rerolls = []
                    for _ in tens_to_reroll:
                        roll = randint(1, 10)
                        current_rerolls.append(roll)
                        if roll >= difficulty:
                            extra_successes += 1
                            successes += 1
                        # Don't count 1s from rerolls against successes
                        # Rerolled 1s don't cancel successes in exploding 10s
                        # Also count 10s in rerolls for specialty
                        if roll == 10 and use_specialty:
                            specialty_bonus += 1
                            successes += 1
                    
                    # Add this generation's rolls to the extras
                    extra_rolls.append(current_rerolls)
                    
                    # Check for new 10s to reroll
                    tens_to_reroll = [i for i, roll in enumerate(current_rerolls) if roll == 10]
                    reroll_generation += 1
                
                # Format rolls for display
                rolls = initial_rolls
                
                # Add exploding 10s info to descriptions
                if extra_rolls:
                    flattened_extras = [roll for generation in extra_rolls for roll in generation]
                    description.append(f"|c(Exploding 10s: +{extra_successes} from rerolls)|n")
                    detailed_description.append(f"|c(Exploding 10s: {extra_successes} extra successes from {flattened_extras})|n")
                
                # Add specialty info to descriptions
                if specialty_bonus > 0:
                    description.append(f"|m(Specialty: +{specialty_bonus} from 10s)|n")
                    detailed_description.append(f"|m(Specialty: {specialty_bonus} extra successes from {tens_count} 10s)|n")
                                        
            elif use_10s:
                all_rolls = []
                extra_rolls = []
                extra_successes = 0
                
                # Initial roll
                initial_rolls, initial_successes, initial_ones = roll_dice(dice_pool, difficulty)
                all_rolls.extend(initial_rolls)
                successes = initial_successes
                ones = initial_ones
                
                # Handle exploding 10s - reroll any 10s
                tens_to_reroll = [i for i, roll in enumerate(initial_rolls) if roll == 10]
                reroll_generation = 1
                
                while tens_to_reroll:
                    current_rerolls = []
                    for _ in tens_to_reroll:
                        roll = randint(1, 10)
                        current_rerolls.append(roll)
                        if roll >= difficulty:
                            extra_successes += 1
                            successes += 1
                        # Don't count 1s from rerolls against successes
                        # Rerolled 1s don't cancel successes in exploding 10s
                    
                    # Add this generation's rolls to the extras
                    extra_rolls.append(current_rerolls)
                    
                    # Check for new 10s to reroll
                    tens_to_reroll = [i for i, roll in enumerate(current_rerolls) if roll == 10]
                    reroll_generation += 1
                
                # Format rolls for display
                rolls = initial_rolls
                
                # Add exploding 10s info to descriptions
                if extra_rolls:
                    flattened_extras = [roll for generation in extra_rolls for roll in generation]
                    description.append(f"|c(Exploding 10s: +{extra_successes} from rerolls)|n")
                    detailed_description.append(f"|c(Exploding 10s: {extra_successes} extra successes from {flattened_extras})|n")
            
            elif use_specialty:
                # Regular roll with specialty (10s count as 2 successes)
                rolls, base_successes, ones = roll_dice(dice_pool, difficulty)
                
                # Count how many 10s were rolled
                tens_count = sum(1 for roll in rolls if roll == 10)
                specialty_bonus = tens_count
                
                # Add the specialty bonus to successes
                successes = base_successes + specialty_bonus
                
                # Add specialty info to descriptions
                if specialty_bonus > 0:
                    description.append(f"|m(Specialty: +{specialty_bonus} from 10s)|n")
                    detailed_description.append(f"|m(Specialty: {specialty_bonus} extra successes from {tens_count} 10s)|n")
            else:
                # Regular roll without Nightmare dice or specialty
                rolls, successes, ones = roll_dice(dice_pool, difficulty)
            
            nightmare_dice = 0  # Ensure nightmare_dice is defined for non-nightmare rolls

        # Interpret the results
        result = interpret_roll_results(successes, ones, rolls=rolls, diff=difficulty, nightmare_dice=nightmare_dice)

        # Format the outputs
        public_description = " ".join(description)
        private_description = " ".join(detailed_description)
        
        # For exploding 10s, add the rerolled dice to the result display
        if use_10s and 'extra_rolls' in locals() and extra_rolls:
            # Format each generation of rerolls
            reroll_generations = []
            for i, gen_rolls in enumerate(extra_rolls):
                if gen_rolls:  # Only add non-empty generations
                    reroll_generations.append(f"Roll {i+1}: [{' '.join(str(r) for r in gen_rolls)}]")
            
            if reroll_generations:
                reroll_display = f" -> {' -> '.join(reroll_generations)}"
            else:
                reroll_display = ""
        else:
            reroll_display = ""
            
        public_output = f"|rRoll>|n {self.caller.db.gradient_name or self.caller.key} |yrolls |n{public_description} |yvs {difficulty} |r=>|n {result}"
        private_output = f"|rRoll> |yYou roll |n{private_description} |yvs {difficulty} |r=>|n {result}{reroll_display}"
        builder_output = f"|rRoll> |n{self.caller.db.gradient_name or self.caller.key} rolls {private_description} |yvs {difficulty}|r =>|n {result}{reroll_display}"

        # Always send the result to the roller
        self.caller.msg(private_output)
        if warnings:
            # Filter out health penalty warnings when this is a reflexive action
            if use_reflexive:
                filtered_warnings = [w for w in warnings if "health penalties" not in w.lower()]
                if filtered_warnings:
                    self.caller.msg("\n".join(filtered_warnings))
            else:
                self.caller.msg("\n".join(warnings))

        # Handle job comment if needed
        if job_id is not None:
            try:
                job = Job.objects.get(id=job_id)
                # Format the roll result as a comment
                comment_text = f"Roll Result: {private_description} vs {difficulty} => {result}"
                if warnings:
                    comment_text += "\nWarnings:\n" + "\n".join(warnings)
                
                # Add the comment to the job
                new_comment = {
                    "author": self.caller.account.username,
                    "text": comment_text,
                    "created_at": timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                if not job.comments:
                    job.comments = []
                job.comments.append(new_comment)
                job.save()

                # Only send the roll result to the caller when rolling to a job
                self.caller.msg(f"Roll result added as comment to job #{job_id}.")
                
                # Post to the jobs channel
                self.post_to_jobs_channel(self.caller.name, job_id, "added a roll to")
                
                # Send mail notification to all participants about the roll
                self.send_mail_to_all_participants(job, f"{self.caller.name} has added a roll to Job #{job_id}: {comment_text}")
                
                # Log the roll but don't announce it to the room when --job is used
                try:
                    # Format the log description to include total dice count
                    log_description = f"Rolling {dice_pool} dice vs {difficulty} (to job #{job_id})"
                    # Initialize roll_log if it doesn't exist
                    if not hasattr(self.caller.location.db, 'roll_log') or self.caller.location.db.roll_log is None:
                        self.caller.location.db.roll_log = []
                    self.caller.location.log_roll(self.caller.key, log_description, result)
                except Exception as e:
                    # Log the error but don't let it interrupt the roll command
                    self.caller.msg("|rWarning: Could not log roll.|n")
                    print(f"Roll logging error: {e}")
                
                # Return early to prevent room announcement
                return
                
            except Job.DoesNotExist:
                self.caller.msg(f"Error: Job #{job_id} not found.")
            except Exception as e:
                self.caller.msg(f"|rError adding comment to job: {str(e)}|n")

        # Only send to the room if not rolling to a job
        # Send builder view to builders, and public view to everyone else
        for obj in self.caller.location.contents:
            if inherits_from(obj, "typeclasses.characters.Character") and obj != self.caller:
                if obj.locks.check_lockstring(obj, "perm(Builder)"):
                    obj.msg(builder_output)
                else:
                    obj.msg(public_output)

        # Log the room roll
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
            
    def send_mail_to_all_participants(self, job, message):
        """Send a mail notification to all participants in a job."""
        from evennia.utils import logger
        
        # Collect all unique accounts involved with the job
        participants = set()
        staff_participants = set()
        
        # Add requester if exists
        if job.requester:
            try:
                if job.requester.check_permstring("Admin"):
                    staff_participants.add(job.requester)
                else:
                    participants.add(job.requester)
            except Exception as e:
                logger.log_err(f"Error checking requester permission: {str(e)}")
            
        # Add assignee if exists
        if job.assignee:
            try:
                if job.assignee.check_permstring("Admin"):
                    staff_participants.add(job.assignee)
                else:
                    participants.add(job.assignee)
            except Exception as e:
                logger.log_err(f"Error checking assignee permission: {str(e)}")
            
        # Add all participants - use try/except to handle potential errors
        try:
            for participant in job.participants.all():
                try:
                    if participant.check_permstring("Admin"):
                        staff_participants.add(participant)
                    else:
                        participants.add(participant)
                except Exception as e:
                    # If we can't check permissions, default to treating as regular participant
                    participants.add(participant)
                    logger.log_err(f"Error checking participant permission: {str(e)}")
        except Exception as e:
            logger.log_err(f"Error accessing job participants: {str(e)}")
            
        # Remove the caller to avoid self-notification
        try:
            if self.caller.account in participants:
                participants.remove(self.caller.account)
        except Exception as e:
            logger.log_err(f"Error removing caller from participants: {str(e)}")
        
        try:
            if self.caller.account in staff_participants:
                staff_participants.remove(self.caller.account)
        except Exception as e:
            logger.log_err(f"Error removing caller from staff participants: {str(e)}")
            
        # First handle staff notifications (direct message, no mail)
        for staff in staff_participants:
            try:
                if staff.is_connected:
                    # Send a direct notification about the job update
                    action_by = self.caller.name if hasattr(self.caller, 'name') else self.caller.key
                    for session in staff.sessions.all():
                        session.msg(f"|yA roll has been posted by {action_by} on Job #{job.id}.|n")
            except Exception as e:
                logger.log_err(f"Error sending staff notification: {str(e)}")
            
        # If we don't have any non-staff recipients, return early
        if not participants:
            return
            
        # Send mail to non-staff participants using the proper mail API
        try:
            subject = f"Job #{job.id} Update"
            mail_body = f"Job #{job.id}: {job.title}\n\n{message}"
            
            from evennia.utils import create
            
            # Create and send mail to each participant
            participant_names = []
            success_count = 0
            
            for participant in participants:
                if not participant.username:
                    logger.log_err(f"Participant has no username, skipping")
                    continue
                
                try:
                    # Create a mail message
                    new_mail = create.create_message(
                        self.caller.account,  # sender
                        mail_body,            # message
                        receivers=participant, # receiver
                        header=subject        # subject
                    )
                    
                    if not new_mail:
                        logger.log_err(f"Failed to create message for {participant.username}")
                        continue
                        
                    # Tag it as new
                    new_mail.tags.add("new", category="mail")
                    
                    participant_names.append(participant.username)
                    success_count += 1
                    
                    # If participant is online, notify them directly
                    if participant.is_connected:
                        # Notify the connected player directly that they have mail
                        for session in participant.sessions.all():
                            session.msg(f"|yYou have received new mail about job #{job.id}. Type '@mail' to view.|n")
                    
                except Exception as e:
                    logger.log_err(f"Error sending to {participant.username}: {str(e)}")
            
            if participant_names:
                self.caller.msg(f"Roll notification sent to: {', '.join(participant_names)}")
            
        except Exception as e:
            logger.log_err(f"Failed to send job notifications: {str(e)}")
            self.caller.msg(f"Failed to send notifications: {str(e)}")

    def get_stat_value_and_name(self, stat_name):
        """
        Retrieve the value and full name of a stat for the character by searching the character's stats.
        Uses fuzzy matching to handle abbreviations and partial matches.
        Always uses 'temp' value if available, otherwise uses 'perm'.
        For pools, always use 'perm' value.
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

        # Properly capitalize hyphenated names for lookup
        def capitalize_hyphenated(name):
            """Capitalize each part of a hyphenated name"""
            parts = name.split('-')
            return '-'.join(p.capitalize() for p in parts)
        
        # Create capitalized versions for exact matching
        capitalized_name = capitalize_hyphenated(stat_name)

        # First try exact match with properly capitalized name
        if 'abilities' in character_stats:
            for ability_type, abilities in character_stats['abilities'].items():
                if capitalized_name in abilities:
                    stat_data = abilities[capitalized_name]
                    if 'temp' in stat_data and stat_data['temp'] != 0:
                        return stat_data['temp'], capitalized_name
                    return stat_data.get('perm', 0), capitalized_name

        # Check if this is a pool stat - for pools, always use 'perm' value
        is_pool = False
        
        # Check in dual pools
        if 'pools' in character_stats and 'dual' in character_stats['pools'] and capitalized_name in character_stats['pools']['dual']:
            is_pool = True
            pool_data = character_stats['pools']['dual'][capitalized_name]
            return pool_data.get('perm', 0), capitalized_name
            
        # Check in other pools
        if 'pools' in character_stats and 'other' in character_stats['pools'] and capitalized_name in character_stats['pools']['other']:
            is_pool = True
            pool_data = character_stats['pools']['other'][capitalized_name]
            return pool_data.get('perm', 0), capitalized_name

        # First try exact match in the most relevant category based on splat
        if splat.lower() == 'changeling':
            # For Changelings, check Arts first
            art_value = self.caller.db.stats.get('powers', {}).get('art', {}).get(capitalized_name, {}).get('temp', None)
            if art_value is not None:
                return art_value, capitalized_name
            
            # Then check Realms
            realm_value = self.caller.db.stats.get('powers', {}).get('realm', {}).get(capitalized_name, {}).get('temp', None)
            if realm_value is not None:
                return realm_value, capitalized_name

        elif splat.lower() == 'shifter':
            # For Shifters, prioritize Gifts over other stats
            gift_value = self.caller.db.stats.get('powers', {}).get('gift', {}).get(capitalized_name, {}).get('temp', None)
            if gift_value is not None:
                return gift_value, capitalized_name

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

        # Check for secondary abilities with hyphens - use capitalized name
        for category in ['secondary_knowledge', 'secondary_talent', 'secondary_skill']:
            if 'secondary_abilities' in character_stats and category in character_stats['secondary_abilities']:
                for stat, stat_data in character_stats['secondary_abilities'][category].items():
                    # Try exact match with properly capitalized name
                    if stat == capitalized_name:
                        if 'temp' in stat_data and stat_data['temp'] != 0:
                            return stat_data['temp'], stat
                        return stat_data.get('perm', 0), stat
                    
                    # Try case-insensitive match
                    if stat.lower() == normalized_input:
                        if 'temp' in stat_data and stat_data['temp'] != 0:
                            return stat_data['temp'], stat
                        return stat_data.get('perm', 0), stat
                    
                    # Check with hyphen replaced by space
                    if stat.lower().replace('-', ' ') == normalized_input.replace('-', ' '):
                        if 'temp' in stat_data and stat_data['temp'] != 0:
                            return stat_data['temp'], stat
                        return stat_data.get('perm', 0), stat
                    
                    # Check without spaces and hyphens
                    if stat.lower().replace('-', '').replace(' ', '') == normalized_nospace:
                        if 'temp' in stat_data and stat_data['temp'] != 0:
                            return stat_data['temp'], stat
                        return stat_data.get('perm', 0), stat

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
                    # Skip pools as we already handled them separately
                    if category == 'pools':
                        continue
                        
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

        # Try checking for pools again by prefix matching
        if 'pools' in character_stats:
            for pool_type in ['dual', 'other']:
                if pool_type in character_stats['pools']:
                    for pool_name, pool_data in character_stats['pools'][pool_type].items():
                        pool_normalized = pool_name.lower()
                        pool_normalized_nospace = pool_normalized.replace('-', '').replace(' ', '')
                        
                        if pool_normalized == normalized_input or pool_normalized_nospace == normalized_nospace:
                            return pool_data.get('perm', 0), pool_name
                        
                        if pool_normalized.startswith(normalized_input) or pool_normalized_nospace.startswith(normalized_nospace):
                            return pool_data.get('perm', 0), pool_name

        # If still no match, return with proper capitalization
        return 0, capitalized_name

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
        bashing = character.db.bashing or 0
        lethal = character.db.lethal or 0
        aggravated = character.db.agg or 0
        
        # Calculate total damage
        total_damage = bashing + lethal + aggravated
        
        # Calculate total health levels including bonuses
        from world.wod20th.utils.damage import calculate_total_health_levels
        bonus_health = calculate_total_health_levels(character)
        total_health = 7 + bonus_health  # 7 is the base health level count
        
        # Get the current injury level
        injury_level = character.db.injury_level or "Healthy"
        
        # Note: We'll handle reflexive actions in the main func method
        # so that the penalty calculation is available but we can choose
        # not to apply it
                
        # Apply penalty based on injury level
        if injury_level == "Healthy" or injury_level == "Bruised":
            return 0
        elif injury_level == "Hurt" or injury_level == "Injured":
            return 1
        elif injury_level == "Wounded" or injury_level == "Mauled":
            return 2
        elif injury_level == "Crippled":
            return 5
        elif injury_level == "Incapacitated" or injury_level == "Dead" or injury_level == "Torpor":
            return total_health  # Effectively prevents any dice rolling
        
        return 0

    def post_to_jobs_channel(self, player_name, job_id, action):
        """Post a message to the Jobs channel for admin visibility."""
        from evennia.comms.models import ChannelDB
        from evennia.utils import create
        from evennia.utils import logger
        
        channel_names = ["Jobs", "Requests", "Req"]
        channel = None

        for name in channel_names:
            found_channel = ChannelDB.objects.channel_search(name)
            if found_channel:
                # Check if the channel has the correct locks for admin-only viewing
                if found_channel[0].locks.check_lockstring(found_channel[0], "listen:perm(Admin)"):
                    channel = found_channel[0]
                    break
                else:
                    # Update locks to ensure admin-only access
                    found_channel[0].locks.add("listen:perm(Admin)")
                    channel = found_channel[0]
                    break

        if not channel:
            # Create channel with admin-only permissions
            channel = create.create_channel(
                "Jobs",
                typeclass="typeclasses.channels.Channel",
                locks="control:perm(Admin);listen:perm(Admin);send:perm(Admin)"
            )
            # Subscribe the creator after channel is created
            channel.connect(self.caller)

        message = f"{player_name} {action} Job #{job_id}"
        channel.msg(f"[Job System] {message}")