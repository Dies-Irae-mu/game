from evennia import default_cmds
from world.wod20th.models import Stat
from world.wod20th.utils.shifter_utils import (
    SHIFTER_IDENTITY_STATS, SHIFTER_RENOWN, SHIFTER_TYPE_CHOICES,
    AUSPICE_CHOICES, BASTET_TRIBE_CHOICES, BREED_CHOICES,
    GAROU_TRIBE_CHOICES
)
from world.wod20th.utils.changeling_utils import PHYLA, INANIMAE_POWERS
from world.wod20th.utils.virtue_utils import calculate_willpower, calculate_road, PATH_VIRTUES
from evennia.utils import search
from evennia.utils.search import search_object
from typeclasses.characters import Character

class CmdStats(default_cmds.MuxCommand):
    """
    Usage:
      +stats <character>/<stat>[(<instance>)]/<category>=[+-]<value>
      +stats me/<stat>[(<instance>)]/<category>=[+-]<value>
      +stats <character>=reset
      +stats me=reset
      +stats/specialty <character>/<stat>=<specialty>
      +stats me/specialty <stat>=<specialty>

    Examples:
      +stats Bob/Strength/Physical=+2
      +stats Alice/Firearms/Skill=-1
      +stats John/Status(Ventrue)/Social=3
      +stats me=reset
      +stats me/Nature=Curmudgeon
      +stats Bob/Demeanor=Visionary
      +stats me/specialty Firearms=Sniping
      +stats Bob/specialty Melee=Swords

    This is the staff version of +selfstat with the same functionality
    but can be used on any character.
    """

    key = "+stats"
    aliases = ["stats", "+setstats", "setstats"]
    locks = "cmd:perm(Builder)"
    help_category = "Staff"

    def parse(self):
        """
        Parse the arguments.
        """
        # Check for specialty switch
        if self.switches and "specialty" in self.switches:
            self.is_specialty = True
            try:
                char_and_stat, self.specialty = self.args.split('=', 1)
                if '/' in char_and_stat:
                    self.char_name, self.stat_name = char_and_stat.split('/', 1)
                else:
                    self.char_name = char_and_stat
                    self.stat_name = None
                self.char_name = self.char_name.strip()
                self.stat_name = self.stat_name.strip() if self.stat_name else None
                self.specialty = self.specialty.strip()
            except ValueError:
                self.char_name = self.stat_name = self.specialty = None
            return

        # Regular stat parsing
        self.is_specialty = False
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
                self.value_change = second_part.strip()  # Keep the raw value_change string
            else:
                first_part = args

            if '/' in first_part:
                self.character_name, stat_part = first_part.split('/', 1)
            else:
                self.character_name = first_part
                stat_part = ''

            # Clean up character name
            self.character_name = self.character_name.strip()

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
        """Execute the command."""
        # Handle specialty command
        if self.is_specialty:
            if not self.char_name or not self.stat_name or not self.specialty:
                self.caller.msg("|rUsage: +stats[/specialty] <character>/<stat>=<specialty>|n")
                return

            # Get the target character
            if self.char_name.lower() == "me":
                character = self.caller
            else:
                character = self.caller.search(self.char_name)
                if not character:
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

            self.caller.msg(f"|gAdded specialty '{self.specialty}' to {stat_name} for {character.name}.|n")
            return

        if not self.character_name:
            self.caller.msg("|rUsage: +stats <character>/<stat>[(<instance>)]/[<category>]=[+-]<value>|n")
            return

        if self.character_name.lower().strip() == 'me':
            character = self.caller
        else:
            # First try exact match
            character = None
            # Search for both online and offline characters
            matches = search_object(self.character_name, 
                                 typeclass='typeclasses.characters.Character',
                                 exact=True)
            
            if not matches:
                # If no exact match, try case-insensitive
                matches = search_object(self.character_name, 
                                     typeclass='typeclasses.characters.Character')
                matches = [obj for obj in matches if obj.key.lower() == self.character_name.lower()]
            
            if matches:
                character = matches[0]
            
            # If still no match, try alias
            if not character:
                character = Character.get_by_alias(self.character_name.lower())

            if not character:
                self.caller.msg(f"|rCharacter '{self.character_name}' not found.|n")
                return

        # When setting splat for the first time or resetting stats
        if self.stat_name and self.stat_name.lower() == 'splat':
            if not self.value_change:
                self.caller.msg("You must specify a splat type.")
                return
            
            # Initialize the stats structure based on splat
            self.initialize_stats(character, self.value_change)
            return

        # Handle the reset command
        if self.stat_name and self.stat_name.lower() == 'reset':
            if not self.value_change:
                character.db.stats = {}
                self.caller.msg(f"|gReset all stats for {character.name}.|n")
                character.msg(f"|y{self.caller.name}|n |greset all your stats.|n")
                return
            elif self.value_change.lower() == 'splat':
                # Get current splat if it exists
                current_splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm')
                if current_splat:
                    # Reinitialize with current splat
                    self.initialize_stats(character, current_splat)
                else:
                    self.caller.msg(f"|rNo splat found for {character.name}. Please set a splat first.|n")
                return

        if not self.stat_name:
            self.caller.msg("|rUsage: +stats <character>/<stat>[(<instance>)]/[<category>]=[+-]<value>|n")
            return

        # Get all matching stats
        matching_stats = Stat.objects.filter(name__iexact=self.stat_name)
        if not matching_stats.exists():
            # If exact match fails, try a case-insensitive contains search
            matching_stats = Stat.objects.filter(name__icontains=self.stat_name)
            if not matching_stats.exists():
                self.caller.msg(f"|rStat '{self.stat_name}' not found.|n")
                return

        # If multiple stats found and no category specified, show options
        if matching_stats.count() > 1 and not self.category:
            # Group stats by category and stat_type
            stat_options = []
            for s in matching_stats:
                stat_options.append(f"{s.name}/{s.stat_type}")
            
            options_str = ", or ".join([", ".join(stat_options[:-1]), stat_options[-1]] if len(stat_options) > 2 else stat_options)
            self.caller.msg(f"|rMultiple versions of this stat exist. Did you mean {options_str}?|n")
            return

        # If category is specified, find the matching stat
        if self.category:
            stat = matching_stats.filter(stat_type__iexact=self.category).first()
            if not stat:
                self.caller.msg(f"|rNo stat '{self.stat_name}' found with category '{self.category}'.|n")
                return
        else:
            # If only one stat found, use it
            stat = matching_stats.first()

        # Use the canonical name from the database
        self.stat_name = stat.name

        # Special handling for Shifter Rank
        if stat.name == 'Rank':
            splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            if splat and splat == 'Shifter':
                stat.category = 'identity'
                stat.stat_type = 'lineage'

        # Check if the character can have this ability
        if stat.stat_type == 'ability' and not character.can_have_ability(stat.name):
            self.caller.msg(f"|rCharacter cannot have the {stat.name} ability.|n")
            return

        full_stat_name = stat.name

        # Handle instances for background stats
        if stat.instanced:
            if not self.instance:
                self.caller.msg(f"|rThe stat '{full_stat_name}' requires an instance. Use the format: {full_stat_name}(instance)|n")
                return
            full_stat_name = f"{full_stat_name}({self.instance})"
        elif self.instance:
            self.caller.msg(f"|rThe stat '{full_stat_name}' does not support instances.|n")
            return

        # Handle stat removal (empty value) - Move this before validation

        if not self.value_change:
            if stat.category in character.db.stats and stat.stat_type in character.db.stats[stat.category]:
                if full_stat_name in character.db.stats[stat.category][stat.stat_type]:
                    del character.db.stats[stat.category][stat.stat_type][full_stat_name]
                    self.caller.msg(f"|gRemoved stat '{full_stat_name}' from {character.name}.|n")
                    character.msg(f"|y{self.caller.name}|n |rremoved your stat|n '|y{full_stat_name}|n'.")
                    
                    # Check if we need to update languages after merit removal
                    if (stat.category == 'merits' and 
                        (stat.name == 'Language' or stat.name == 'Natural Linguist')):
                        character.handle_language_merit_change()

                    return
                else:
                    self.caller.msg(f"|rStat '{full_stat_name}' not found on {character.name}.|n")
                    return

        # Check if the character passes the stat's lock_string
        try:
            if stat.lockstring and not character.locks.check_lockstring(character, stat.lockstring):
                self.caller.msg(f"|rYou do not have permission to modify the stat '{full_stat_name}' for {character.name}.|n")
                return
        except AttributeError:
            pass
        
        # Check if the stat being set is an identity stat for a shifter
        current_splat = character.get_stat('other', 'splat', 'Splat')
        if current_splat and current_splat.lower() == 'shifter' and stat.category == 'identity':
            shifter_type = character.get_stat('identity', 'lineage', 'Type')
            if shifter_type and full_stat_name != 'Type':
                # Special handling for Camp/Lodge
                if shifter_type.lower() == 'garou':
                    tribe = character.get_stat('identity', 'lineage', 'Tribe')
                    if tribe and tribe.lower() == 'silver fangs':
                        if full_stat_name not in ['Lodge', 'Fang House'] + SHIFTER_IDENTITY_STATS.get(shifter_type, []):
                            self.caller.msg(f"|rThe stat '{full_stat_name}' is not valid for Silver Fangs characters.|n")
                            return
                    else:
                        if full_stat_name not in ['Camp'] + SHIFTER_IDENTITY_STATS.get(shifter_type, []):
                            self.caller.msg(f"|rThe stat '{full_stat_name}' is not valid for {shifter_type} characters.|n")
                            return
                else:
                    allowed_stats = SHIFTER_IDENTITY_STATS.get(shifter_type, [])
                    if full_stat_name not in allowed_stats:
                        self.caller.msg(f"|rThe stat '{full_stat_name}' is not valid for {shifter_type} characters.|n")
                        return

        # Add this check before updating the stat
        if stat.category == 'pools':
            splat = character.get_stat('other', 'splat', 'Splat')
            valid_pools = ['Willpower']
            if splat and splat.lower() == 'vampire':
                valid_pools.extend(['Blood', 'Road'])
            elif splat and splat.lower() == 'shifter':
                valid_pools.extend(['Gnosis', 'Rage'])
            
            if full_stat_name not in valid_pools:
                self.caller.msg(f"|rThe pool '{full_stat_name}' is not valid for {splat}.|n")
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
        if stat.stat_type == 'dual':
            if isinstance(stat.values, dict):
                # For dual stats, validate against the 'perm' values list
                if 'perm' in stat.values and new_value not in stat.values['perm']:
                    try:
                        new_value = int(new_value)  # Convert to int for comparison
                        if new_value not in stat.values['perm']:
                            self.caller.msg(f"|rValue '{new_value}' is not valid for permanent {full_stat_name}. Valid values are: {stat.values['perm']}|n")
                            return
                    except ValueError:
                        self.caller.msg(f"|rValue '{new_value}' is not valid for permanent {full_stat_name}. Valid values are: {stat.values['perm']}|n")
                        return
                
                # Set both permanent and temporary values
                character.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=False)
                character.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=True)
                self.caller.msg(f"|gUpdated {character.name}'s {full_stat_name} to {new_value} (both permanent and temporary).|n")
                character.msg(f"|y{self.caller.name}|n |gset your {full_stat_name} to {new_value} (both permanent and temporary).|n")
                return
        elif hasattr(stat, 'values') and stat.values and new_value not in stat.values:
            self.caller.msg(f"|rValue '{new_value}' is not valid for stat '{full_stat_name}'. Valid values are: {stat.values}|n")
            return

        # Convert value to integer for virtues
        if full_stat_name in ['Courage', 'Self-Control', 'Conscience', 'Conviction', 'Instinct']:
            try:
                new_value = int(new_value)
            except ValueError:
                self.caller.msg(f"|rInvalid value for {full_stat_name}. Please provide an integer.|n")
                return

        # During character generation (when character is not approved), 
        # or for specific stat types, always set temp value equal to permanent value
        if not character.db.approved or stat.stat_type in ['knowledge', 'attribute', 'ability', 'talent', 'skill']:
            # Set both permanent and temporary values
            character.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=False)
            character.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=True)
            self.caller.msg(f"|gUpdated {character.name}'s {full_stat_name} to {new_value} (both permanent and temporary).|n")
            character.msg(f"|y{self.caller.name}|n |gset your {full_stat_name} to {new_value} (both permanent and temporary).|n")
            return
        elif stat.stat_type == 'dual':
            # For dual stats, we need to set both permanent and temporary values
            if isinstance(stat.values, dict):
                # Validate against permanent value range
                if 'perm' in stat.values and new_value not in stat.values['perm']:
                    self.caller.msg(f"|rValue '{new_value}' is not valid for permanent {full_stat_name}. Valid values are: {stat.values['perm']}|n")
                    return
                
                # Set both permanent and temporary values
                character.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=False)
                character.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=True)
                self.caller.msg(f"|gUpdated {character.name}'s {full_stat_name} to {new_value} (both permanent and temporary).|n")
                character.msg(f"|y{self.caller.name}|n |gset your {full_stat_name} to {new_value} (both permanent and temporary).|n")
                return

        # Update the stat
        character.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=False)
        
        # During character generation (when character is not approved), 
        # always set temp value equal to permanent value
        if not character.db.approved:
            character.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=True)
            self.caller.msg(f"|gUpdated {character.name}'s {full_stat_name} to {new_value} (both permanent and temporary).|n")
            character.msg(f"|y{self.caller.name}|n |gset your {full_stat_name} to {new_value} (both permanent and temporary).|n")
        # If already approved, only update temp for pools and dual stats
        elif stat.category == 'pools' or stat.stat_type == 'dual':
            character.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=True)
            self.caller.msg(f"|gUpdated {character.name}'s {full_stat_name} to {new_value} (both permanent and temporary).|n")
            character.msg(f"|y{self.caller.name}|n |gset your {full_stat_name} to {new_value} (both permanent and temporary).|n")
        else:
            self.caller.msg(f"|gUpdated {character.name}'s {full_stat_name} to {new_value}.|n")
            character.msg(f"|y{self.caller.name}|n |gset your {full_stat_name} to {new_value}.|n")

        # If the stat is 'Type' for a Shifter, apply the correct pools and renown
        current_splat = character.get_stat('other', 'splat', 'Splat')
        if full_stat_name == 'Type' and current_splat and current_splat.lower() == 'shifter':
            self.apply_shifter_pools(character, new_value)

        # If the stat is Willpower, update the temporary Willpower pool to match the permanent value
        if full_stat_name == 'Willpower':
            character.set_stat('pools', 'temporary', 'Willpower', new_value, temp=True)
            self.caller.msg(f"|gAlso updated {character.name}'s temporary Willpower pool to {new_value}.|n")
            character.msg(f"|gYour temporary Willpower pool has also been set to {new_value}.|n")

        # If the stat is 'Splat', apply the correct pools and bio stats
        if full_stat_name == 'Splat':
            self.apply_splat_pools(character, new_value)

        # If the stat is 'Mage Faction', apply the correct subfaction stats
        if full_stat_name == 'Mage Faction':
            self.apply_affiliation_stats(character, new_value)

        # After setting a stat, recalculate Willpower and Road
        if full_stat_name in ['Courage', 'Self-Control', 'Conscience', 'Conviction', 'Instinct']:
            new_willpower = calculate_willpower(character)
            # Set both permanent and temporary values for Willpower
            character.set_stat('pools', 'dual', 'Willpower', new_willpower, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', new_willpower, temp=True)
            self.caller.msg(f"|gRecalculated Willpower to {new_willpower}.|n")

            new_road = calculate_road(character)
            character.set_stat('pools', 'moral', 'Road', new_road, temp=False)
            self.caller.msg(f"|gRecalculated Road to {new_road}.|n")

        # When setting a stat value:
        if stat.stat_type == 'knowledge':
            # Set both permanent and temporary values
            character.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=False)
            # Also set the temporary value if it's not already set
            if not character.get_stat(stat.category, stat.stat_type, full_stat_name, temp=True):
                character.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=True)

        # Check if this is a dual-type stat (pools, renown, etc)
        dual_stat_types = ['dual', 'renown', 'pool']  # Add any other dual-type categories
        
        if stat.stat_type in dual_stat_types:
            if isinstance(stat.values, dict):
                # For dual stats, validate against the 'perm' values list
                if 'perm' in stat.values and new_value not in stat.values['perm']:
                    try:
                        new_value = int(new_value)  # Convert to int for comparison
                        if new_value not in stat.values['perm']:
                            self.caller.msg(f"|rValue '{new_value}' is not valid for permanent {full_stat_name}. Valid values are: {stat.values['perm']}|n")
                            return
                    except ValueError:
                        self.caller.msg(f"|rValue '{new_value}' is not valid for permanent {full_stat_name}. Valid values are: {stat.values['perm']}|n")
                        return
                
                # Set both permanent and temporary values
                character.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=False)
                character.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=True)
                self.caller.msg(f"|gUpdated {character.name}'s {full_stat_name} to {new_value} (both permanent and temporary).|n")
                character.msg(f"|y{self.caller.name}|n |gset your {full_stat_name} to {new_value} (both permanent and temporary).|n")
                return
        # After merit changes, check if we need to update languages
        if (stat.category == 'merits' and 
            (stat.name == 'Language' or stat.name == 'Natural Linguist')):
            character.handle_language_merit_change()

        # Special handling for Shifter Rank
        if stat.name == 'Rank':
            splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            if splat and splat == 'Shifter':
                stat.category = 'identity'
                stat.stat_type = 'lineage'

        # Check if the character can have this ability
        if stat.stat_type == 'ability' and not character.can_have_ability(stat.name):
            self.caller.msg(f"Your character cannot have the {stat.name} ability.")
            return

        # Special handling for Appearance stat
        if stat.name == 'Appearance':
            splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            clan = character.db.stats.get('identity', {}).get('lineage', {}).get('Clan', {}).get('perm', '')
            
            if splat and splat == 'Vampire' and clan in ['Nosferatu', 'Samedi']:
                self.caller.msg("Nosferatu and Samedi vampires always have Appearance 0.")
                return
            
            if splat and splat == 'Shifter':
                form = character.db.stats.get('other', {}).get('form', {}).get('Form', {}).get('temp', '')
                if form == 'Crinos':
                    self.caller.msg("Characters in Crinos form always have Appearance 0.")
                    return

        try:
            # Store old values for comparison
            old_type = character.get_stat('identity', 'lineage', 'Type')
            old_aspect = character.get_stat('identity', 'lineage', 'Aspect')
            
            # Set the stat
            character.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=False)
            
            # If character is not approved, set temp value equal to permanent value
            if not character.db.approved:
                character.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=True)
                
                # Check if we're setting Type or Aspect for a Shifter
                splat = character.get_stat('other', 'splat', 'Splat')
                current_type = character.get_stat('identity', 'lineage', 'Type')
                
                if splat == 'Shifter':
                    # If Type changed or Aspect changed for an Ajaba
                    if (stat.name == 'Type' and old_type != current_type) or \
                       (stat.name == 'Aspect' and old_aspect != self.value_change and current_type == 'Ajaba'):
                        self.caller.msg("Debug: Applying shifter stats after Type/Aspect change...")
                        self.apply_shifter_stats(character)

                self.caller.msg(f"|gUpdated {full_stat_name} to {new_value} (both permanent and temporary).|n")
            
        except ValueError as e:
            self.caller.msg(str(e))

        # Inside func() method, when handling the 'Type' stat:
        if stat.name == 'Type':
            splat = character.get_stat('other', 'splat', 'Splat')
            if splat:
                splat = splat.lower()
                
                if splat == 'shifter':
                    # Set shifter type
                    character.set_stat('identity', 'lineage', 'Type', new_value, temp=False)
                    character.set_stat('identity', 'lineage', 'Type', new_value, temp=True)
                    # Initialize shifter-specific stats
                    self.apply_shifter_stats(character)
                    
                elif splat == 'mortal+':
                    # Set mortal+ type
                    character.set_stat('identity', 'lineage', 'Mortal+ Type', new_value, temp=False)
                    character.set_stat('identity', 'lineage', 'Mortal+ Type', new_value, temp=True)
                    # Initialize mortal+-specific stats
                    self.apply_mortalplus_stats(character)
                    
                else:
                    self.caller.msg(f"|rType setting not applicable for {splat} characters.|n")
                    return

        # After setting virtues, update Willpower and Road/Humanity
        if self.stat_name in ['Courage', 'Self-Control', 'Conscience', 'Conviction', 'Instinct']:
            splat = character.get_stat('other', 'splat', 'Splat', temp=False)
            if splat and splat.lower() == 'vampire':
                # Set Willpower equal to Courage
                courage = character.get_stat('virtues', 'moral', 'Courage', temp=False) or 0
                character.set_stat('pools', 'dual', 'Willpower', courage, temp=False)
                character.set_stat('pools', 'dual', 'Willpower', courage, temp=True)
                
                # Calculate Road based on Path
                enlightenment = character.get_stat('identity', 'personal', 'Enlightenment', temp=False)
                if enlightenment in PATH_VIRTUES:
                    virtue1, virtue2 = PATH_VIRTUES[enlightenment]
                    value1 = character.get_stat('virtues', 'moral', virtue1, temp=False) or 0
                    value2 = character.get_stat('virtues', 'moral', virtue2, temp=False) or 0
                    road = value1 + value2
                    character.set_stat('pools', 'moral', 'Road', road, temp=False)
                    character.set_stat('pools', 'moral', 'Road', road, temp=True)
                    self.caller.msg(f"|gRecalculated Willpower to {courage} and Road to {road}.|n")
                    character.msg(f"|gYour Willpower has been set to {courage} and Road to {road}.|n")
                    
            elif splat and splat.lower() in ['mortal', 'mortal+']:
                # Original Humanity calculation for mortals
                courage = character.get_stat('virtues', 'moral', 'Courage', temp=False) or 0
                character.set_stat('pools', 'dual', 'Willpower', courage, temp=False)
                character.set_stat('pools', 'dual', 'Willpower', courage, temp=True)
                
                conscience = character.get_stat('virtues', 'moral', 'Conscience', temp=False) or 0
                self_control = character.get_stat('virtues', 'moral', 'Self-Control', temp=False) or 0
                humanity = conscience + self_control
                character.set_stat('virtues', 'moral', 'Humanity', humanity, temp=False)
                character.set_stat('virtues', 'moral', 'Humanity', humanity, temp=True)
                
                self.caller.msg(f"|gRecalculated Willpower to {courage} and Humanity to {humanity}.|n")
                character.msg(f"|gYour Willpower has been set to {courage} and Humanity to {humanity}.|n")

        # After setting a stat, check if we need to update shifter stats
        if character.get_stat('other', 'splat', 'Splat', temp=False) == 'Shifter':
            shifter_type = character.get_stat('identity', 'lineage', 'Type')
            if shifter_type:
                # List of stats that should trigger a shifter stats update
                shifter_trigger_stats = ['Breed', 'Tribe', 'Aspect', 'Path', 'Auspice', 'Varna']
                if stat.name in shifter_trigger_stats:
                    self.caller.msg(f"Debug: Updating shifter stats after {stat.name} change...")
                    self.apply_shifter_stats(character)

    def update_virtues_for_enlightenment(self, character):
        """Update virtues based on enlightenment path"""
        # Initialize virtues if they don't exist
        if 'virtues' not in character.db.stats:
            character.db.stats['virtues'] = {'moral': {}}
        
        # Get or set default enlightenment
        enlightenment = character.get_stat('identity', 'personal', 'Enlightenment', temp=False)
        if not enlightenment:
            enlightenment = 'Humanity'
            character.set_stat('identity', 'personal', 'Enlightenment', enlightenment)
        
        # Define virtue mappings
        path_virtues = {
            'Humanity': ['Conscience', 'Self-Control', 'Courage'],
            'Night': ['Conviction', 'Instinct', 'Courage'],
            'Beast': ['Conviction', 'Instinct', 'Courage'],
            'Harmony': ['Conscience', 'Instinct', 'Courage'],
            'Evil Revelations': ['Conviction', 'Self-Control', 'Courage'],
            'Self-Focus': ['Conviction', 'Instinct', 'Courage'],
            'Scorched Heart': ['Conviction', 'Self-Control', 'Courage'],
            'Entelechy': ['Conviction', 'Self-Control', 'Courage'],
            'Sharia El-Sama': ['Conscience', 'Self-Control', 'Courage'],
            'Asakku': ['Conviction', 'Instinct', 'Courage'],
            'Death and the Soul': ['Conviction', 'Self-Control', 'Courage'],
            'Honorable Accord': ['Conscience', 'Self-Control', 'Courage'],
            'Feral Heart': ['Conviction', 'Instinct', 'Courage'],
            'Orion': ['Conviction', 'Instinct', 'Courage'],
            'Power and the Inner Voice': ['Conviction', 'Instinct', 'Courage'],
            'Lilith': ['Conviction', 'Instinct', 'Courage'],
            'Caine': ['Conviction', 'Instinct', 'Courage'],
            'Cathari': ['Conviction', 'Instinct', 'Courage'],
            'Redemption': ['Conscience', 'Self-Control', 'Courage'],
            'Bones': ['Conviction', 'Self-Control', 'Courage'],
            'Typhon': ['Conviction', 'Self-Control', 'Courage'],
            'Paradox': ['Conviction', 'Self-Control', 'Courage'],
            'Blood': ['Conviction', 'Self-Control', 'Courage'],
            'Hive': ['Conviction', 'Instinct', 'Courage']
        }
        
        # Get the appropriate virtues for the path
        virtues = path_virtues.get(enlightenment, ['Conscience', 'Self-Control', 'Courage'])
        
        # Remove any existing virtues that aren't in the new set
        current_virtues = list(character.db.stats['virtues']['moral'].keys())
        for virtue in current_virtues:
            if virtue not in virtues:
                del character.db.stats['virtues']['moral'][virtue]
        
        # Set default values for new virtues
        for virtue in virtues:
            if virtue not in character.db.stats['virtues']['moral']:
                character.db.stats['virtues']['moral'][virtue] = {'perm': 1, 'temp': 1}

    def apply_splat_pools(self, character, splat):
        """Apply the correct pools and bio stats based on the character's splat."""
        # Store existing Willpower values if they exist
        willpower_perm = character.get_stat('pools', 'dual', 'Willpower', temp=False)
        willpower_temp = character.get_stat('pools', 'dual', 'Willpower', temp=True)
        
        # Remove all existing pools except Willpower
        character.db.stats['pools'] = {k: v for k, v in character.db.stats.get('pools', {}).items() if k == 'Willpower'}

        # Add Willpower for all characters if it doesn't exist, preserving existing values
        if 'Willpower' not in character.db.stats['pools']:
            # Only set to 1 if no previous value exists
            willpower_perm = willpower_perm if willpower_perm is not None else 1
            willpower_temp = willpower_temp if willpower_temp is not None else 1
            character.set_stat('pools', 'dual', 'Willpower', willpower_perm, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', willpower_temp, temp=True)

        if splat.lower() == 'vampire':
            self.apply_vampire_stats(character)
        elif splat.lower() == 'shifter':
            self.apply_shifter_stats(character)
        elif splat.lower() == 'mage':
            self.apply_mage_stats(character)
        elif splat.lower() == 'changeling':
            self.apply_changeling_stats(character)
        elif splat.lower() == 'companion':
            self.apply_companion_stats(character)
            # Restore Willpower values for companions since apply_companion_stats overwrites them
            character.set_stat('pools', 'dual', 'Willpower', willpower_perm, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', willpower_temp, temp=True)

        self.caller.msg(f"|gApplied default stats for {splat} to {character.name}.|n")
        character.msg(f"|gYour default stats for {splat} have been applied.|n")

    def apply_vampire_stats(self, character):
        """Apply vampire-specific stats"""
        # Set Blood pool
        character.set_stat('pools', 'dual', 'Blood', 10, temp=True)
        character.set_stat('pools', 'dual', 'Blood', 10, temp=False)
        
        # Set default Enlightenment and virtues
        if not character.get_stat('identity', 'personal', 'Enlightenment', temp=False):
            character.set_stat('identity', 'personal', 'Enlightenment', 'Humanity')
        self.update_virtues_for_enlightenment(character)

    def apply_shifter_stats(self, character):
        """Apply the correct stats for a shifter character."""
        shifter_type = character.get_stat('identity', 'lineage', 'Type')
        if not shifter_type:
            self.caller.msg("|rNo shifter type set. Please set a type first.|n")
            return
        
        # Initialize powers category if it doesn't exist
        if 'powers' not in character.db.stats:
            character.db.stats['powers'] = {}

        # Add Gifts and Rites categories
        character.db.stats['powers']['gift'] = {}
        character.db.stats['powers']['rite'] = {}

        # Add Renown category
        if 'advantages' not in character.db.stats:
            character.db.stats['advantages'] = {}
        if 'renown' not in character.db.stats['advantages']:
            character.db.stats['advantages']['renown'] = {}

        # Use the new shifter_utils module to initialize stats
        initialize_shifter_type(character, shifter_type)
        self.caller.msg(f"|gApplied {shifter_type} stats.|n")

    def apply_mage_stats(self, character):
        # Add Mage-specific pools
        character.set_stat('pools', 'dual', 'Quintessence', 1, temp=False)
        character.set_stat('pools', 'dual', 'Quintessence', 1, temp=True)
        character.set_stat('pools', 'dual', 'Paradox', 0, temp=False)
        character.set_stat('pools', 'dual', 'Paradox', 0, temp=True)
        character.set_stat('other', 'advantage', 'Arete', 1, temp=False)

        # Add Mage-specific bio stats
        character.set_stat('identity', 'lineage', 'Essence', '')
        character.set_stat('identity', 'lineage', 'Mage Faction', '')

    def apply_changeling_stats(self, character):
        # Add Changeling-specific pools
        character.set_stat('pools', 'dual', 'Glamour', 1, temp=False)
        character.set_stat('pools', 'dual', 'Glamour', 1, temp=True)
        character.set_stat('pools', 'dual', 'Banality', 5, temp=False)
        character.set_stat('pools', 'dual', 'Banality', 5, temp=True)

        # Add Changeling-specific bio stats
        character.set_stat('identity', 'lineage', 'Kith', '')
        character.set_stat('identity', 'lineage', 'Seeming', '')
        character.set_stat('identity', 'lineage', 'House', '')
        character.set_stat('identity', 'lineage', 'Seelie Legacy', '')
        character.set_stat('identity', 'lineage', 'Unseelie Legacy', '')

        # Remove the generic 'Legacy' stat if it exists
        if 'Legacy' in character.db.stats.get('identity', {}).get('lineage', {}):
            del character.db.stats['identity']['lineage']['Legacy']

        # Ensure these stats are added to the database if they don't exist
        for stat_name in ['Kith', 'Seeming', 'House', 'Seelie Legacy', 'Unseelie Legacy']:
            stat, created = Stat.objects.get_or_create(
                name=stat_name,
                defaults={
                    'description': f'{stat_name} for Changelings',
                    'game_line': 'Changeling: The Dreaming',
                    'category': 'identity',
                    'stat_type': 'lineage',
                    'splat': 'Changeling'
                }
            )
            if created:
                self.caller.msg(f"|gCreated new stat: {stat_name}|n")

        self.caller.msg(f"|gApplied Changeling-specific stats to {character.name}.|n")
        character.msg(f"|gYour Changeling-specific stats have been applied.|n")

    def apply_affiliation_stats(self, character, faction):
        if faction.lower() == 'traditions':
            character.set_stat('identity', 'lineage', 'Tradition', '')
            character.set_stat('identity', 'lineage', 'Traditions Subfaction', '')
        elif faction.lower() == 'technocracy':
            character.set_stat('identity', 'lineage', 'Convention', '')
            character.set_stat('identity', 'lineage', 'Methodology', '')
        elif faction.lower() == 'nephandi':
            character.set_stat('identity', 'lineage', 'Nephandi Faction', '')

        # Remove any stats that don't apply to the new faction
        for stat in ['Tradition', 'Traditions Subfaction', 'Convention', 'Methodology', 'Nephandi Faction']:
            if stat not in character.db.stats.get('identity', {}).get('lineage', {}):
                character.db.stats['identity']['lineage'].pop(stat, None)

        self.caller.msg(f"|gApplied {faction} specific stats to {character.name}.|n")
        character.msg(f"|gYour {faction} specific stats have been applied.|n")

    def apply_shifter_pools(self, character, shifter_type):
        """Apply the correct pools and renown based on the Shifter's type."""
        # Ensure Willpower exists
        if 'Willpower' not in character.db.stats.get('pools', {}):
            character.set_stat('pools', 'dual', 'Willpower', 1, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', 1, temp=True)

        # Set Gnosis for all Shifter types
        character.set_stat('pools', 'dual', 'Gnosis', 1, temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', 1, temp=True)

        if shifter_type == 'Ananasi':
            # Remove Rage if it exists
            if 'Rage' in character.db.stats.get('pools', {}):
                del character.db.stats['pools']['Rage']
            # Add Blood
            character.set_stat('pools', 'dual', 'Blood', 10, temp=False)
            character.set_stat('pools', 'dual', 'Blood', 10, temp=True)
        else:
            # Remove Blood if it exists
            if 'Blood' in character.db.stats.get('pools', {}):
                del character.db.stats['pools']['Blood']
            # Add Rage
            character.set_stat('pools', 'dual', 'Rage', 1, temp=False)
            character.set_stat('pools', 'dual', 'Rage', 1, temp=True)

        # Set Renown
        renown_types = SHIFTER_RENOWN.get(shifter_type, [])
        for renown_type in renown_types:
            character.set_stat('advantages', 'renown', renown_type, 0, temp=False)

        self.caller.msg(f"|gApplied specific pools and renown for {shifter_type} to {character.name}.|n")
        character.msg(f"|gYour specific pools and renown for {shifter_type} have been applied.|n")

    def set_stat(self, target, category, stat_type, stat_name, value, temp=False):
        """Set a stat value."""
        # Get the stat definition
        stat = Stat.objects.filter(name=stat_name).first()
        if not stat:
            self.caller.msg(f"Stat '{stat_name}' not found.")
            return False

        # Handle stats with perm/temp values
        if hasattr(stat, 'values') and isinstance(stat.values, dict) and 'perm' in stat.values:
            valid_values = stat.values['temp'] if temp else stat.values['perm']
            if value not in valid_values:
                self.caller.msg(f"Value '{value}' is not valid for stat '{stat_name}'. Valid values are: {valid_values}")
                return False
        # Handle stats with simple value lists
        elif hasattr(stat, 'values') and isinstance(stat.values, list):
            if value not in stat.values:
                self.caller.msg(f"Value '{value}' is not valid for stat '{stat_name}'. Valid values are: {stat.values}")
                return False

        # Set the stat value
        target.set_stat(category, stat_type, stat_name, value, temp=temp)
        return True

    def initialize_stats(self, character, splat):
        """Initialize the basic stats structure based on splat type."""
        # Base structure common to all splats
        base_stats = {
            'other': {'splat': {'Splat': {'perm': splat, 'temp': splat}}},
            'identity': {'personal': {}, 'lineage': {}},
            'abilities': {'ability': {}},
            'attributes': {'physical': {}, 'social': {}, 'mental': {}},
            'backgrounds': {'background': {}},
            'merits': {},
            'flaws': {},
            'powers': {},  # Initialize empty powers dict for all splats
            'pools': {'dual': {}, 'moral': {}},
            'virtues': {'moral': {}},
            'archetype': {'personal': {}}  # For Nature/Demeanor
        }

        # Splat-specific additions
        if splat.lower() == 'vampire':
            base_stats['powers']['discipline'] = {}
            base_stats['pools']['dual']['Blood'] = {'perm': 10, 'temp': 10}  # Default to 13th generation
            base_stats['pools']['dual']['Willpower'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['moral']['Road'] = {'perm': 1, 'temp': 1}
            
        elif splat.lower() == 'mage':
            base_stats['powers']['sphere'] = {}
            base_stats['pools']['dual']['Arete'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['dual']['Quintessence'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['dual']['Willpower'] = {'perm': 1, 'temp': 1}
            
        elif splat.lower() == 'shifter':
            base_stats['powers']['gift'] = {}
            base_stats['powers']['rite'] = {}
            base_stats['pools']['dual']['Rage'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['dual']['Gnosis'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['dual']['Willpower'] = {'perm': 1, 'temp': 1}
            base_stats['advantages'] = {'renown': {}}
            
        elif splat.lower() == 'changeling':
            base_stats['powers']['art'] = {}
            base_stats['powers']['realm'] = {}
            base_stats['pools']['dual']['Glamour'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['dual']['Banality'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['dual']['Willpower'] = {'perm': 1, 'temp': 1}
        
        elif splat.lower() == 'companion':
            base_stats['powers']['special_advantage'] = {}
            base_stats['powers']['charm'] = {}
            base_stats['pools']['dual']['Essence'] = {'perm': 10, 'temp': 10}
            base_stats['pools']['dual']['Willpower'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['dual']['Paradox'] = {'perm': 0, 'temp': 0}
            base_stats['identity']['lineage']['Companion Type'] = {'perm': '', 'temp': ''}
            base_stats['identity']['lineage']['Mage Faction'] = {'perm': '', 'temp': ''}
            base_stats['identity']['personal']['Motivation'] = {'perm': '', 'temp': ''}

        else:  # Mortal or other
            base_stats['pools']['dual']['Willpower'] = {'perm': 1, 'temp': 1}

    def apply_companion_stats(self, character):
        """Apply Companion-specific stats"""
        # Set base pools
        character.set_stat('pools', 'dual', 'Essence', 10, temp=False)
        character.set_stat('pools', 'dual', 'Essence', 10, temp=True)
        character.set_stat('pools', 'dual', 'Paradox', 0, temp=False)
        character.set_stat('pools', 'dual', 'Paradox', 0, temp=True)

        # Add required flaw based on type
        companion_type = character.get_stat('identity', 'lineage', 'Companion Type', '').lower()
        if companion_type in ['construct', 'object', 'robot']:
            character.set_stat('flaws', 'flaw', 'Power Source', 1, temp=False)
        else:
            character.set_stat('flaws', 'flaw', 'Thaumivore', 1, temp=False)

        # Initialize basic attributes with default value of 1
        for category in ['physical', 'social', 'mental']:
            if category == 'physical':
                attrs = ['Strength', 'Dexterity', 'Stamina']
            elif category == 'social':
                attrs = ['Charisma', 'Manipulation', 'Appearance']
            else:  # mental
                attrs = ['Perception', 'Intelligence', 'Wits']
            


from evennia.commands.default.muxcommand import MuxCommand
from world.wod20th.models import Stat
from evennia.utils import search

class CmdSpecialty(MuxCommand):
    """
    Usage:
      +stats/specialty <character>/<stat>=<specialty>
      +stats me/<stat>=<specialty>

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
            # First try exact match
            character = None
            # Search for both online and offline characters
            matches = search_object(self.character_name, 
                                 typeclass='typeclasses.characters.Character',
                                 exact=True)
            
            if not matches:
                # If no exact match, try case-insensitive
                matches = search_object(self.character_name, 
                                     typeclass='typeclasses.characters.Character')
                matches = [obj for obj in matches if obj.key.lower() == self.character_name.lower()]
            
            if matches:
                character = matches[0]
            
            # If still no match, try alias
            if not character:
                character = Character.get_by_alias(self.character_name.lower())

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

        self.caller.msg(f"|gAdded specialty '{self.specialty}' to {stat_name} for {character.name}.|n")
        character.msg(f"|y{self.caller.name}|n |gadded the specialty|n '|y{self.specialty}|n' |gto your {stat_name}.|n")

    def initialize_possessed_stats(self, character):
        """Initialize or ensure proper stats for Possessed characters."""
        possessed_type = character.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
        
        # Get base pools based on type
        if possessed_type == 'Kami':
            base_gnosis = 1
            base_willpower = 4
            base_rage = 0
        elif possessed_type == 'Fomori':
            base_gnosis = 0
            base_willpower = 3
            base_rage = 0
        else:
            return  # Invalid type

        # Initialize powers category if it doesn't exist
        if 'powers' not in character.db.stats:
            character.db.stats['powers'] = {}
            
        # Initialize blessings, gifts, and charms categories
        character.db.stats['powers']['blessing'] = {}
        character.db.stats['powers']['gift'] = {}
        character.db.stats['powers']['charm'] = {}

        # Check for Berserker blessing
        blessings = character.db.stats.get('powers', {}).get('blessing', {})
        has_berserker = any(name.lower() == 'berserker' and values.get('perm', 0) > 0 
                           for name, values in blessings.items())
        if has_berserker:
            base_rage = 5

        # Check for Spirit Ties blessing and adjust Gnosis
        spirit_ties_value = next((values.get('perm', 0) for name, values in blessings.items() 
                                if name.lower() == 'spirit ties'), 0)
        if spirit_ties_value > 0:
            base_gnosis = min(5, base_gnosis + spirit_ties_value)  # Cap at 5

        # Set the final pool values
        self.set_stat_both(character, 'pools', 'dual', 'Gnosis', base_gnosis)
        self.set_stat_both(character, 'pools', 'dual', 'Willpower', base_willpower)
        self.set_stat_both(character, 'pools', 'dual', 'Rage', base_rage)

