from evennia import Command, default_cmds
from world.wod20th.models import Stat, SHIFTER_IDENTITY_STATS, SHIFTER_RENOWN, calculate_willpower, calculate_road
from evennia.utils import search
import re
from commands.CmdLanguage import CmdLanguage

PATH_VIRTUES = {
    'Humanity': ('Conscience', 'Self-Control'),
    'Night': ('Conviction', 'Instinct'),
    'Beast': ('Conviction', 'Instinct'),
    'Harmony': ('Conscience', 'Instinct'),
    'Evil Revelations': ('Conviction', 'Self-Control'),
    'Self-Focus': ('Conviction', 'Instinct'),
    'Scorched Heart': ('Conviction', 'Self-Control'),
    'Entelechy': ('Conviction', 'Self-Control'),
    'Sharia El-Sama': ('Conscience', 'Self-Control'),
    'Asakku': ('Conviction', 'Instinct'),
    'Death and the Soul': ('Conviction', 'Self-Control'),
    'Honorable Accord': ('Conscience', 'Self-Control'),
    'Feral Heart': ('Conviction', 'Instinct'),
    'Orion': ('Conviction', 'Instinct'),
    'Power and the Inner Voice': ('Conviction', 'Instinct'),
    'Lilith': ('Conviction', 'Instinct'),
    'Caine': ('Conviction', 'Instinct'),
    'Cathari': ('Conviction', 'Instinct'),
    'Redemption': ('Conscience', 'Self-Control'),
    'Metamorphosis': ('Conviction', 'Instinct'),
    'Bones': ('Conviction', 'Self-Control'),
    'Typhon': ('Conviction', 'Self-Control'),
    'Paradox': ('Conviction', 'Self-Control'),
    'Blood': ('Conviction', 'Self-Control'),
    'Hive': ('Conviction', 'Instinct')
}

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

    def initialize_stats(self, splat):
        """Initialize the basic stats structure based on splat type."""
        # Base structure common to all splats
        base_stats = {
            'other': {'splat': {'Splat': {'perm': splat, 'temp': splat}}},
            'identity': {'personal': {}, 'lineage': {}},
            'abilities': {
                'talent': {},
                'skill': {},
                'knowledge': {}
            },
            'attributes': {
                'physical': {},
                'social': {},
                'mental': {}
            },
            'advantages': {'background': {}},
            'merits': {'merit': {}},
            'flaws': {'flaw': {}},
            'powers': {},
            'pools': {'dual': {}, 'moral': {}},
            'virtues': {'moral': {}}
        }

        # Initialize basic attributes with default value of 1
        for category in ['physical', 'social', 'mental']:
            if category == 'physical':
                attrs = ['Strength', 'Dexterity', 'Stamina']
            elif category == 'social':
                attrs = ['Charisma', 'Manipulation', 'Appearance']
            else:  # mental
                attrs = ['Perception', 'Intelligence', 'Wits']
            
            for attr in attrs:
                base_stats['attributes'][category][attr] = {'perm': 1, 'temp': 1}

        # Initialize virtues for vampires with default values
        if splat.lower() == 'vampire':
            # Initialize with Humanity virtues by default
            base_stats['virtues']['moral'] = {
                'Conscience': {'perm': 1, 'temp': 1},
                'Self-Control': {'perm': 1, 'temp': 1},
                'Courage': {'perm': 1, 'temp': 1}
            }
            base_stats['pools']['moral']['Road'] = {'perm': 3, 'temp': 3}  # Sum of starting virtues

        # Splat-specific additions
        if splat.lower() == 'shifter':
            base_stats['powers']['gift'] = {}
            base_stats['powers']['rite'] = {}
            base_stats['pools']['dual']['Willpower'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['dual']['Rage'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['dual']['Gnosis'] = {'perm': 1, 'temp': 1}
            base_stats['advantages']['renown'] = {}
            # Note: The actual values for Rage, Gnosis, and Willpower will be set 
            # by apply_shifter_stats after the breed/auspice/tribe are chosen

        elif splat.lower() == 'vampire':
            base_stats['powers']['discipline'] = {}
            base_stats['pools']['dual']['Blood'] = {'perm': 10, 'temp': 10}
            base_stats['pools']['dual']['Willpower'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['moral']['Road'] = {'perm': 1, 'temp': 1}

        elif splat.lower() == 'mage':
            base_stats['powers']['sphere'] = {}
            base_stats['pools']['dual']['Arete'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['dual']['Willpower'] = {'perm': 5, 'temp': 5}
            base_stats['pools']['dual']['Quintessence'] = {'perm': 0, 'temp': 0}
            base_stats['virtues']['synergy'] = {
                'Dynamic': {'perm': 0, 'temp': 0},
                'Entropic': {'perm': 0, 'temp': 0},
                'Static': {'perm': 0, 'temp': 0}
            }
            base_stats['pools']['resonance'] = {'Resonance': {'perm': 0, 'temp': 0}}
            base_stats['identity']['lineage']['Signature'] = {'perm': '', 'temp': ''}
            base_stats['identity']['lineage']['Affinity Sphere'] = {'perm': '', 'temp': ''}
            
            # Initialize all spheres to 0
            technocracy_spheres = ['Data', 'Primal Utility', 'Dimensional Science', 'Forces', 'Life', 'Matter', 'Mind', 'Time']
            tradition_spheres = ['Correspondence', 'Entropy', 'Forces', 'Life', 'Matter', 'Mind', 'Prime', 'Spirit', 'Time']
            
            # Initialize all possible spheres to 0
            for sphere in set(technocracy_spheres + tradition_spheres):
                base_stats['powers']['sphere'][sphere] = {'perm': 0, 'temp': 0}

        elif splat.lower() == 'changeling':
            base_stats['powers']['art'] = {}
            base_stats['powers']['realm'] = {}
            base_stats['pools']['dual']['Glamour'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['dual']['Banality'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['dual']['Willpower'] = {'perm': 1, 'temp': 1}

        elif splat.lower() == 'mortal+':
            base_stats['powers'] = {
                'numina': {},
                'sorcery': {},
                'faith': {},
                'discipline': {},
                'gift': {},
                'arts': {},
                'realms': {}
            }
            base_stats['pools']['dual']['Willpower'] = {'perm': 3, 'temp': 3}
            
            # Additional pools based on subtype will be set in apply_mortalplus_stats
            
            return base_stats

        else:  # Mortal or other
            base_stats['pools']['dual']['Willpower'] = {'perm': 1, 'temp': 1}

        return base_stats

    def func(self):
        """Execute the command."""
        # Check if character is approved
        if self.caller.db.approved:
            self.caller.msg("|rError: Approved characters cannot use chargen commands. Please contact staff for any needed changes.|n")
            return

        if not self.stat_name:
            self.caller.msg("|rUsage: +selfstat <stat>[(<instance>)]/[<category>]=[+-]<value>|n")
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
            splat = self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            if splat and splat == 'Shifter':
                stat.category = 'identity'
                stat.stat_type = 'lineage'

        # Check if the character can have this ability
        if stat.stat_type == 'ability' and not self.caller.can_have_ability(stat.name):
            self.caller.msg(f"|rYour character cannot have the {stat.name} ability.|n")
            return

        # Handle instances for background stats
        if stat.instanced:
            if not self.instance:
                self.caller.msg(f"The stat '{self.stat_name}' requires an instance. Use the format: {self.stat_name}(instance)")
                return
            full_stat_name = f"{self.stat_name}({self.instance})"
        else:
            if self.instance:
                self.caller.msg(f"The stat '{self.stat_name}' does not support instances.")
                return
            full_stat_name = self.stat_name

        # Handle stat removal (empty value)
        if self.value_change == '':
            if stat.category in self.caller.db.stats and stat.stat_type in self.caller.db.stats[stat.category]:
                if full_stat_name in self.caller.db.stats[stat.category][stat.stat_type]:
                    # For language-related stats, pass 0 instead of removing directly
                    if (full_stat_name == 'Language' or 
                        full_stat_name.startswith('Language(') or 
                        full_stat_name == 'Natural Linguist'):
                        self.caller.set_stat(stat.category, stat.stat_type, full_stat_name, 0)
                    else:
                        del self.caller.db.stats[stat.category][stat.stat_type][full_stat_name]
                    self.caller.msg(f"|gRemoved stat '{full_stat_name}'.|n")
                    return
                else:
                    self.caller.msg(f"|rStat '{full_stat_name}' not found.|n")
                    return

        # Special handling for Appearance stat
        if stat.name == 'Appearance':
            splat = self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            clan = self.caller.db.stats.get('identity', {}).get('lineage', {}).get('Clan', {}).get('perm', '')
            
            if splat and splat == 'Vampire' and clan in ['Nosferatu', 'Samedi']:
                self.caller.msg("Nosferatu and Samedi vampires always have Appearance 0.")
                return
            
            if splat and splat == 'Shifter':
                form = self.caller.db.stats.get('other', {}).get('form', {}).get('Form', {}).get('temp', '')
                if form == 'Crinos':
                    self.caller.msg("Characters in Crinos form always have Appearance 0.")
                    return

        # Handle incremental changes
        try:
            if self.value_change.startswith('+') or self.value_change.startswith('-'):
                current_value = self.caller.get_stat(stat.category, stat.stat_type, full_stat_name)
                if current_value is None:
                    current_value = 0
                new_value = current_value + int(self.value_change)
            else:
                new_value = int(self.value_change) if self.value_change.isdigit() else self.value_change
        except (ValueError, TypeError):
            new_value = self.value_change

        # Special handling for Enlightenment changes
        if stat.name == 'Enlightenment':
            old_path = self.caller.db.stats.get('identity', {}).get('personal', {}).get('Enlightenment', {}).get('perm', 'Humanity')
            
            # Get the virtues for both old and new paths
            old_virtues = PATH_VIRTUES.get(old_path, PATH_VIRTUES['Humanity'])
            new_virtues = PATH_VIRTUES.get(new_value, PATH_VIRTUES['Humanity'])
            
            # Remove old virtues that aren't in the new path
            for virtue in old_virtues:
                if virtue not in new_virtues:
                    if 'virtues' in self.caller.db.stats and 'moral' in self.caller.db.stats['virtues']:
                        if virtue in self.caller.db.stats['virtues']['moral']:
                            del self.caller.db.stats['virtues']['moral'][virtue]
            
            # Initialize new virtues
            for virtue in new_virtues:
                if virtue not in old_virtues:
                    # Conviction and Instinct start at 0 for non-Humanity paths
                    if new_value != 'Humanity' and virtue in ['Conviction', 'Instinct']:
                        self.caller.set_stat('virtues', 'moral', virtue, 0, temp=False)
                        self.caller.set_stat('virtues', 'moral', virtue, 0, temp=True)
                    else:  # Conscience, Self-Control, and Courage always start at 1
                        self.caller.set_stat('virtues', 'moral', virtue, 1, temp=False)
                        self.caller.set_stat('virtues', 'moral', virtue, 1, temp=True)

        # Update the stat
        try:
            # When setting splat for the first time
            if self.stat_name.lower() == 'splat':
                if not self.value_change:
                    self.caller.msg("You must specify a splat type.")
                    return
                
                # Validate splat type
                valid_splats = ['changeling', 'vampire', 'shifter', 'mage', 'mortal', 'mortal+']
                if self.value_change.lower() not in valid_splats:
                    self.caller.msg(f"|rInvalid splat type. Must be one of: {', '.join(valid_splats).title()}|n")
                    return
                
                # Initialize the stats structure based on splat
                self.caller.db.stats = self.initialize_stats(self.value_change)
                self.caller.msg(f"|gInitialized character as {self.value_change} with basic stats.|n")
                return
            
            # Handle Type changes after Splat is set
            if stat.name == 'Type':
                splat = self.caller.get_stat('other', 'splat', 'Splat')
                if splat:
                    splat = splat.lower()
                    
                    if splat == 'shifter':
                        self.caller.set_stat('identity', 'lineage', 'Type', new_value, temp=False)
                        self.caller.set_stat('identity', 'lineage', 'Type', new_value, temp=True)
                        self.apply_shifter_stats(self.caller)
                        
                    elif splat == 'mortal+':
                        self.caller.set_stat('identity', 'lineage', 'Mortal+ Type', new_value, temp=False)
                        self.caller.set_stat('identity', 'lineage', 'Mortal+ Type', new_value, temp=True)
                        self.apply_mortalplus_stats(self.caller)
                        
                    else:
                        self.caller.msg(f"|rType setting not applicable for {splat} characters.|n")
                        return
            
            # Set the stat
            self.caller.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=False)
            self.caller.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=True)
            
            self.caller.msg(f"|gUpdated {full_stat_name} to {new_value} (both permanent and temporary).|n")

            # After setting a stat, check if we need to update shifter stats
            if self.caller.get_stat('other', 'splat', 'Splat', temp=False) == 'Shifter':
                shifter_type = self.caller.get_stat('identity', 'lineage', 'Type')
                if shifter_type:
                    # List of stats that should trigger a shifter stats update
                    shifter_trigger_stats = ['Breed', 'Tribe', 'Aspect', 'Path', 'Auspice', 'Varna', 'Varnas', 'Kitsune Path']
                    if stat.name in shifter_trigger_stats:
                        self.apply_shifter_stats(self.caller)

        except ValueError as e:
            self.caller.msg(str(e))

        # After setting virtues, update Willpower and Road/Humanity
        if self.stat_name in ['Courage', 'Self-Control', 'Conscience', 'Conviction', 'Instinct']:
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            
            # Only update Willpower based on Courage for these splats
            if splat and splat.lower() in ['vampire', 'mortal', 'mortal+']:
                # Set Willpower equal to Courage
                courage = self.caller.get_stat('virtues', 'moral', 'Courage', temp=False) or 0
                self.caller.set_stat('pools', 'dual', 'Willpower', courage, temp=False)
                self.caller.set_stat('pools', 'dual', 'Willpower', courage, temp=True)
                
                if splat.lower() == 'vampire':
                    # Calculate Road based on Path's virtues
                    enlightenment = self.caller.get_stat('identity', 'personal', 'Enlightenment', temp=False)
                    if enlightenment in PATH_VIRTUES:
                        virtue1, virtue2 = PATH_VIRTUES[enlightenment]
                        value1 = self.caller.get_stat('virtues', 'moral', virtue1, temp=False) or 0
                        value2 = self.caller.get_stat('virtues', 'moral', virtue2, temp=False) or 0
                        road = value1 + value2
                        self.caller.set_stat('pools', 'moral', 'Road', road, temp=False)
                        self.caller.set_stat('pools', 'moral', 'Road', road, temp=True)
                        self.caller.msg(f"|gRecalculated Willpower to {courage} and Road to {road}.|n")
                else:  # mortal or mortal+
                    # Calculate Humanity
                    conscience = self.caller.get_stat('virtues', 'moral', 'Conscience', temp=False) or 0
                    self_control = self.caller.get_stat('virtues', 'moral', 'Self-Control', temp=False) or 0
                    humanity = conscience + self_control
                    self.caller.set_stat('virtues', 'moral', 'Humanity', humanity, temp=False)
                    self.caller.set_stat('virtues', 'moral', 'Humanity', humanity, temp=True)
                    self.caller.msg(f"|gRecalculated Willpower to {courage} and Humanity to {humanity}.|n")

    def apply_shifter_stats(self, character):
        """Apply shifter-specific stats"""
        shifter_type = character.get_stat('identity', 'lineage', 'Type')
        breed = character.get_stat('identity', 'lineage', 'Breed') or ''
        breed = breed.lower()
        
        # Common Breed-based Gnosis values
        COMMON_BREED_GNOSIS = {
            'homid': 1,
            'metis': 3,
            'lupus': 5,  # Animal-Born
            'animal-born': 5
        }

        if shifter_type == 'Garou':
            auspice = character.get_stat('identity', 'lineage', 'Auspice')
            auspice = auspice.lower()
            tribe = character.get_stat('identity', 'lineage', 'Tribe')
            tribe = tribe.lower()
            
            # Set Auspice-based Rage
            GAROU_AUSPICE_RAGE = {
                'ahroun': 5,
                'galliard': 4,
                'philodox': 3,
                'theurge': 2,
                'ragabash': 1
            }
            if auspice in GAROU_AUSPICE_RAGE:
                character.set_stat('pools', 'dual', 'Rage', GAROU_AUSPICE_RAGE[auspice], temp=False)
                character.set_stat('pools', 'dual', 'Rage', GAROU_AUSPICE_RAGE[auspice], temp=True)
            
            # Set Breed-based Gnosis
            if breed in COMMON_BREED_GNOSIS:
                character.set_stat('pools', 'dual', 'Gnosis', COMMON_BREED_GNOSIS[breed], temp=False)
                character.set_stat('pools', 'dual', 'Gnosis', COMMON_BREED_GNOSIS[breed], temp=True)
            
            # Set Tribe-based Willpower
            GAROU_TRIBE_WILLPOWER = {
                'black furies': 3,
                'black fury': 3,
                'bone gnawers': 4,
                'bone gnawer': 4,
                'children of gaia': 4,
                'fianna': 3,
                'get of fenris': 3,
                'glass walkers': 3,
                'glass walker': 3,
                'red talons': 3,
                'red talon': 3,
                'shadow lords': 3,
                'shadow lord': 3,
                'silent striders': 3,
                'silent strider': 3,
                'silver fangs': 3,
                'silver fang': 3,
                'stargazers': 4,
                'stargazer': 4,
                'uktena': 3,
                'wendigo': 4
            }
            if tribe in GAROU_TRIBE_WILLPOWER:
                character.set_stat('pools', 'dual', 'Willpower', GAROU_TRIBE_WILLPOWER[tribe], temp=False)
                character.set_stat('pools', 'dual', 'Willpower', GAROU_TRIBE_WILLPOWER[tribe], temp=True)

            
        elif shifter_type == 'Ajaba':
            aspect = character.get_stat('identity', 'lineage', 'Aspect')
            
            AJABA_ASPECT_STATS = {
                'dawn': {'rage': 5, 'gnosis': 1},
                'midnight': {'rage': 3, 'gnosis': 3},
                'dusk': {'rage': 1, 'gnosis': 5}
            }
            
            # Set base Willpower for all Ajaba
            character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
            
            if aspect in AJABA_ASPECT_STATS:
                stats = AJABA_ASPECT_STATS[aspect]
                # Set Rage
                character.set_stat('pools', 'dual', 'Rage', stats['rage'], temp=False)
                character.set_stat('pools', 'dual', 'Rage', stats['rage'], temp=True)
                # Set Gnosis
                character.set_stat('pools', 'dual', 'Gnosis', stats['gnosis'], temp=False)
                character.set_stat('pools', 'dual', 'Gnosis', stats['gnosis'], temp=True)

        elif shifter_type == 'Ananasi':
            breed = character.get_stat('identity', 'lineage', 'Breed')
            # Remove Rage if it exists
            if 'Rage' in character.db.stats.get('pools', {}).get('dual', {}):
                del character.db.stats['pools']['dual']['Rage']
            # Set Blood pool
            character.set_stat('pools', 'dual', 'Blood', 10, temp=False)
            character.set_stat('pools', 'dual', 'Blood', 10, temp=True)
            
            if breed == 'homid':
                character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
                character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
                character.set_stat('pools', 'dual', 'Gnosis', 1, temp=False)
                character.set_stat('pools', 'dual', 'Gnosis', 1, temp=True)
            elif breed in ['lupus', 'animal-born']:
                character.set_stat('pools', 'dual', 'Willpower', 4, temp=False)
                character.set_stat('pools', 'dual', 'Willpower', 4, temp=True)
                character.set_stat('pools', 'dual', 'Gnosis', 5, temp=False)
                character.set_stat('pools', 'dual', 'Gnosis', 5, temp=True)

        elif shifter_type == 'Bastet':
            breed = character.get_stat('identity', 'lineage', 'Breed')
            tribe = character.get_stat('identity', 'lineage', 'Tribe')
            
            # Convert tribe to lowercase for case-insensitive comparison
            tribe = tribe.lower() if tribe else ''
            
            BASTET_TRIBE_STATS = {
                'balam': {'rage': 4, 'willpower': 3},
                'bubasti': {'rage': 1, 'willpower': 5},
                'ceilican': {'rage': 3, 'willpower': 3},
                'khan': {'rage': 5, 'willpower': 2},
                'pumonca': {'rage': 4, 'willpower': 4},
                'qualmi': {'rage': 2, 'willpower': 5},
                'simba': {'rage': 5, 'willpower': 2},
                'swara': {'rage': 2, 'willpower': 4}
            }
            
            # Set tribe-based stats
            if tribe in BASTET_TRIBE_STATS:
                stats = BASTET_TRIBE_STATS[tribe]
                character.set_stat('pools', 'dual', 'Rage', stats['rage'], temp=False)
                character.set_stat('pools', 'dual', 'Rage', stats['rage'], temp=True)
                character.set_stat('pools', 'dual', 'Willpower', stats['willpower'], temp=False)
                character.set_stat('pools', 'dual', 'Willpower', stats['willpower'], temp=True)
            
            # Set breed-based Gnosis
            breed = breed.lower() if breed else ''
            COMMON_BREED_GNOSIS = {
                'homid': 1,
                'metis': 3,
                'lupus': 5,
                'animal-born': 5
            }
            
            if breed in COMMON_BREED_GNOSIS:
                gnosis = COMMON_BREED_GNOSIS[breed]
                character.set_stat('pools', 'dual', 'Gnosis', gnosis, temp=False)
                character.set_stat('pools', 'dual', 'Gnosis', gnosis, temp=True)
            
            # Initialize Renown
            if 'advantages' not in character.db.stats:
                character.db.stats['advantages'] = {}
            if 'renown' not in character.db.stats['advantages']:
                character.db.stats['advantages']['renown'] = {}
            
            for renown in ['Cunning', 'Ferocity', 'Honor']:
                character.set_stat('advantages', 'renown', renown, 0, temp=False)
                character.set_stat('advantages', 'renown', renown, 0, temp=True)

        elif shifter_type == 'Corax':
            character.set_stat('pools', 'dual', 'Rage', 1, temp=False)
            character.set_stat('pools', 'dual', 'Rage', 1, temp=True)
            character.set_stat('pools', 'dual', 'Gnosis', 6, temp=False)
            character.set_stat('pools', 'dual', 'Gnosis', 6, temp=True)
            character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)

        elif shifter_type == 'Gurahl':
            breed = character.get_stat('identity', 'lineage', 'Breed')
            character.set_stat('pools', 'dual', 'Willpower', 6, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', 6, temp=True)
            
            if breed == 'homid':
                character.set_stat('pools', 'dual', 'Rage', 3, temp=False)
                character.set_stat('pools', 'dual', 'Rage', 3, temp=True)
                character.set_stat('pools', 'dual', 'Gnosis', 4, temp=False)
                character.set_stat('pools', 'dual', 'Gnosis', 4, temp=True)
            elif breed in ['lupus', 'animal-born']:
                character.set_stat('pools', 'dual', 'Rage', 4, temp=False)
                character.set_stat('pools', 'dual', 'Rage', 4, temp=True)
                character.set_stat('pools', 'dual', 'Gnosis', 5, temp=False)
                character.set_stat('pools', 'dual', 'Gnosis', 5, temp=True)

        elif shifter_type == 'Kitsune':
            breed = character.get_stat('identity', 'lineage', 'Breed')
            path = character.get_stat('identity', 'lineage', 'Kitsune Path')
            
            # Convert to lowercase for case-insensitive comparison
            breed = breed.lower() if breed else ''
            path = path.lower() if path else ''
            
            # Set base Willpower
            character.set_stat('pools', 'dual', 'Willpower', 5, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', 5, temp=True)
            
            KITSUNE_PATH_RAGE = {
                'kataribe': 2,
                'gukutsushi': 2,
                'doshi': 3,
                'eji': 4
            }
            
            KITSUNE_BREED_GNOSIS = {
                'kojin': 3,
                'roko': 5,
                'shinju': 4
            }
            
            if path in KITSUNE_PATH_RAGE:
                character.set_stat('pools', 'dual', 'Rage', KITSUNE_PATH_RAGE[path], temp=False)
                character.set_stat('pools', 'dual', 'Rage', KITSUNE_PATH_RAGE[path], temp=True)
                
            if breed in KITSUNE_BREED_GNOSIS:
                character.set_stat('pools', 'dual', 'Gnosis', KITSUNE_BREED_GNOSIS[breed], temp=False)
                character.set_stat('pools', 'dual', 'Gnosis', KITSUNE_BREED_GNOSIS[breed], temp=True)
            
            # Initialize Renown
            if 'advantages' not in character.db.stats:
                character.db.stats['advantages'] = {}
            if 'renown' not in character.db.stats['advantages']:
                character.db.stats['advantages']['renown'] = {}
            
            for renown in ['Glory', 'Honor', 'Wisdom']:
                character.set_stat('advantages', 'renown', renown, 0, temp=False)
                character.set_stat('advantages', 'renown', renown, 0, temp=True)

        elif shifter_type == 'Mokole':
            breed = character.get_stat('identity', 'lineage', 'Breed')
            auspice = character.get_stat('identity', 'lineage', 'Auspice')
            # Try both 'Varna' and 'Varnas' before lowercasing
            varna = character.get_stat('identity', 'lineage', 'Varnas')  # Try Varnas first since that's what's being used
            if not varna:
                varna = character.get_stat('identity', 'lineage', 'Varna')
            
            # Convert to lowercase for case-insensitive comparison
            breed = breed.lower() if breed else ''
            auspice = auspice.lower() if auspice else ''
            varna = varna.lower() if varna else ''
            
            # Set Breed-based Gnosis
            MOKOLE_BREED_GNOSIS = {
                'homid': 2,
                'animal-born': 4,
                'suchid': 4  # Alternative name for animal-born
            }
            if breed in MOKOLE_BREED_GNOSIS:
                character.set_stat('pools', 'dual', 'Gnosis', MOKOLE_BREED_GNOSIS[breed], temp=False)
                character.set_stat('pools', 'dual', 'Gnosis', MOKOLE_BREED_GNOSIS[breed], temp=True)
            
            # Set Auspice-based Willpower
            MOKOLE_AUSPICE_WILLPOWER = {
                'rising sun striking': 3,
                'noonday sun unshading': 5,
                'setting sun warding': 3,
                'shrouded sun concealing': 4,
                'midnight sun shining': 4,
                'decorated suns gathering': 5,
                'solar eclipse crowning': 5,
                'hemanta': 2,
                'zarad': 3,
                'grisma': 4,
                'vasanta': 5
            }
            if auspice in MOKOLE_AUSPICE_WILLPOWER:
                character.set_stat('pools', 'dual', 'Willpower', MOKOLE_AUSPICE_WILLPOWER[auspice], temp=False)
                character.set_stat('pools', 'dual', 'Willpower', MOKOLE_AUSPICE_WILLPOWER[auspice], temp=True)
            
            # Set Varna-based Rage
            MOKOLE_VARNA_RAGE = {
                'champsa': 3,
                'gharial': 4,
                'halpatee': 4,
                'karna': 3,
                'makara': 3,
                'ora': 5,
                'piasa': 4,
                'syrta': 4,
                'unktehi': 5
            }
            if varna in MOKOLE_VARNA_RAGE:
                character.set_stat('pools', 'dual', 'Rage', MOKOLE_VARNA_RAGE[varna], temp=False)
                character.set_stat('pools', 'dual', 'Rage', MOKOLE_VARNA_RAGE[varna], temp=True)
            
            # Initialize Renown
            if 'advantages' not in character.db.stats:
                character.db.stats['advantages'] = {}
            if 'renown' not in character.db.stats['advantages']:
                character.db.stats['advantages']['renown'] = {}
            
            for renown in ['Glory', 'Honor', 'Wisdom']:
                character.set_stat('advantages', 'renown', renown, 0, temp=False)
                character.set_stat('advantages', 'renown', renown, 0, temp=True)

        elif shifter_type == 'Nagah':
            breed = character.get_stat('identity', 'lineage', 'Breed')
            auspice = character.get_stat('identity', 'lineage', 'Auspice')
            
            # Set base Willpower
            character.set_stat('pools', 'dual', 'Willpower', 4, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', 4, temp=True)
            
            # Set Breed-based Gnosis
            NAGAH_BREED_GNOSIS = {
                'balaram': 1,  # specific homid name
                'homid': 1,  # homid
                'ahi': 3,  # specific metis name
                'metis': 3,
                'animal-born': 5,
                'vasuki': 5    # animal-born specific name for nagah
            }
            if breed in NAGAH_BREED_GNOSIS:
                character.set_stat('pools', 'dual', 'Gnosis', NAGAH_BREED_GNOSIS[breed], temp=False)
                character.set_stat('pools', 'dual', 'Gnosis', NAGAH_BREED_GNOSIS[breed], temp=True)
            
            # Set Auspice-based Rage
            NAGAH_AUSPICE_RAGE = {
                'kamakshi': 3,
                'kartikeya': 4,
                'kamsa': 3,
                'kali': 4
            }
            if auspice in NAGAH_AUSPICE_RAGE:
                character.set_stat('pools', 'dual', 'Rage', NAGAH_AUSPICE_RAGE[auspice], temp=False)
                character.set_stat('pools', 'dual', 'Rage', NAGAH_AUSPICE_RAGE[auspice], temp=True)

        elif shifter_type == 'Nuwisha':
            breed = character.get_stat('identity', 'lineage', 'Breed')
            
            # Remove Rage if it exists
            if 'Rage' in character.db.stats.get('pools', {}).get('dual', {}):
                del character.db.stats['pools']['dual']['Rage']
            
            # Set base Willpower
            character.set_stat('pools', 'dual', 'Willpower', 4, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', 4, temp=True)
            
            # Set Breed-based Gnosis
            NUWISHA_BREED_GNOSIS = {
                'homid': 1,
                'animal-born': 5,
                'latrani': 5  # Alternative name for animal-born
            }
            if breed in NUWISHA_BREED_GNOSIS:
                character.set_stat('pools', 'dual', 'Gnosis', NUWISHA_BREED_GNOSIS[breed], temp=False)
                character.set_stat('pools', 'dual', 'Gnosis', NUWISHA_BREED_GNOSIS[breed], temp=True)

        elif shifter_type == 'Ratkin':
            breed = character.get_stat('identity', 'lineage', 'Breed')
            aspect = character.get_stat('identity', 'lineage', 'Aspect')
            
            # Set base Willpower
            character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
            
            # Set Breed-based Gnosis
            if breed in COMMON_BREED_GNOSIS:
                character.set_stat('pools', 'dual', 'Gnosis', COMMON_BREED_GNOSIS[breed], temp=False)
                character.set_stat('pools', 'dual', 'Gnosis', COMMON_BREED_GNOSIS[breed], temp=True)
            
            # Set Aspect-based Rage
            RATKIN_ASPECT_RAGE = {
                'tunnel runner': 1,
                'shadow seer': 2,
                'knife skulker': 3,
                'warrior': 5,
                'engineer': 2,
                'plague lord': 3,
                'munchmausen': 4,
                'twitcher': 5
            }
            if aspect in RATKIN_ASPECT_RAGE:
                character.set_stat('pools', 'dual', 'Rage', RATKIN_ASPECT_RAGE[aspect], temp=False)
                character.set_stat('pools', 'dual', 'Rage', RATKIN_ASPECT_RAGE[aspect], temp=True)

        elif shifter_type == 'Rokea':
            breed = character.get_stat('identity', 'lineage', 'Breed')
            auspice = character.get_stat('identity', 'lineage', 'Auspice')
            
            # Set base Willpower
            character.set_stat('pools', 'dual', 'Willpower', 4, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', 4, temp=True)
            
            # Set Breed-based Gnosis
            ROKEA_BREED_GNOSIS = {
                'homid': 1,
                'animal-born': 5,
                'squamus': 5  # Alternative name for animal-born
            }
            if breed in ROKEA_BREED_GNOSIS:
                character.set_stat('pools', 'dual', 'Gnosis', ROKEA_BREED_GNOSIS[breed], temp=False)
                character.set_stat('pools', 'dual', 'Gnosis', ROKEA_BREED_GNOSIS[breed], temp=True)
            
            # Set Auspice-based Rage
            ROKEA_AUSPICE_RAGE = {
                'brightwater': 5,
                'dimwater': 4,
                'darkwater': 3
            }
            if auspice in ROKEA_AUSPICE_RAGE:
                character.set_stat('pools', 'dual', 'Rage', ROKEA_AUSPICE_RAGE[auspice], temp=False)
                character.set_stat('pools', 'dual', 'Rage', ROKEA_AUSPICE_RAGE[auspice], temp=True)

        elif shifter_type == 'Garou':
            breed = character.get_stat('identity', 'lineage', 'Breed')
            auspice = character.get_stat('identity', 'lineage', 'Auspice')
            tribe = character.get_stat('identity', 'lineage', 'Tribe')

            # Initialize the stats structure based on splat
            self.caller.db.stats = self.initialize_stats(self.value_change)
            self.caller.msg(f"|gInitialized character as {self.value_change} with basic stats.|n")
            return

    def apply_mortalplus_stats(self, character):
        """Apply specific stats based on Mortal+ subtype."""
        subtype = character.get_stat('identity', 'lineage', 'Mortal+ Type')
        
        if subtype == 'Ghoul':
            # Set Blood Pool for Ghouls
            character.set_stat('pools', 'dual', 'Blood', 1, temp=False)
            character.set_stat('pools', 'dual', 'Blood', 1, temp=True)
            
        elif subtype == 'Kinfolk':
            # Set Gnosis for Kinfolk
            character.set_stat('pools', 'dual', 'Gnosis', 1, temp=False)
            character.set_stat('pools', 'dual', 'Gnosis', 1, temp=True)
            
        elif subtype == 'Kinain':
            # Set Glamour for Kinain
            character.set_stat('pools', 'dual', 'Glamour', 1, temp=False)
            character.set_stat('pools', 'dual', 'Glamour', 1, temp=True)
            
        # Set base Willpower for all types
        character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
        character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)