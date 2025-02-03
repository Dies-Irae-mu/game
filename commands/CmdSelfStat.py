from evennia import Command, default_cmds
from world.wod20th.models import (Stat, SHIFTER_IDENTITY_STATS, SHIFTER_RENOWN, 
                                calculate_willpower, calculate_road, PHYLA, INANIMAE_POWERS)
from evennia.utils import search
from world.wod20th.utils.shifter_utils import initialize_shifter_type
import re
from commands.CmdLanguage import CmdLanguage
from world.wod20th.utils.banality import get_default_banality

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
      +selfstat/specialty <stat>=<specialty>

    Examples:
      +selfstat Strength/Physical=+1
      +selfstat Firearms/Skill=-1
      +selfstat Status(Ventrue)/Social=
      +selfstat/specialty Firearms=Sniping
    """

    key = "+selfstat"
    aliases = ["selfstat"]
    locks = "cmd:all()"  # All players can use this command
    help_category = "Chargen & Character Info"

    def __init__(self):
        """Initialize the command."""
        super().__init__()
        self.switches = []  # Initialize switches
        self.is_specialty = False
        self.stat_name = ""
        self.instance = None
        self.category = None
        self.value_change = None
        self.temp = False

    def parse(self):
        """
        Parse the arguments.
        """
        # Check for specialty switch
        if not self.args:
            self.caller.msg("Usage: +selfstat <stat>[(<instance>)]/<category>=[+-]<value>")
            return

        if self.switches and "specialty" in self.switches:
            self.is_specialty = True
            self.stat_name = ""
            self.specialty = ""

            try:
                args = self.args.strip()
                if '=' not in args:
                    self.caller.msg("Usage: +selfstat/specialty <stat>=<specialty>")
                    return
                self.stat_name, self.specialty = args.split('=', 1)
                self.stat_name = self.stat_name.strip()
                self.specialty = self.specialty.strip()
            except ValueError:
                self.stat_name = self.specialty = None
            return

        # Regular stat parsing
        self.is_specialty = False
        self.stat_name = ""
        self.instance = None
        self.category = None
        self.value_change = None
        self.temp = False

        try:
            args = self.args.strip()

            # Special handling for splat and type initialization
            if args.lower().startswith('splat=') or args.lower().startswith('type='):
                if '=' not in args:
                    self.stat_name = args.lower()
                    self.value_change = None
                    return

                self.stat_name, self.value_change = args.split('=', 1)
                self.stat_name = self.stat_name.strip().lower()
                self.value_change = self.value_change.strip()
                return

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
        """Initialize a new character's stats."""
        self.caller.db.languages = ["English"]
        self.caller.db.native_language = "English"
        self.caller.db.speaking_language = "English"
        # Create base stats structure
        base_stats = {
            'identity': {'personal': {}, 'lineage': {}},
            'abilities': {'talent': {}, 'skill': {}, 'knowledge': {}},
            'attributes': {
                'physical': {'Strength': {'perm': 1, 'temp': 1},
                           'Dexterity': {'perm': 1, 'temp': 1},
                           'Stamina': {'perm': 1, 'temp': 1}},
                'social': {'Charisma': {'perm': 1, 'temp': 1},
                         'Manipulation': {'perm': 1, 'temp': 1},
                         'Appearance': {'perm': 1, 'temp': 1}},
                'mental': {'Perception': {'perm': 1, 'temp': 1},
                         'Intelligence': {'perm': 1, 'temp': 1},
                         'Wits': {'perm': 1, 'temp': 1}}
            },
            'advantages': {'background': {}, 'renown': {}},
            'merits': {'merit': {}},
            'flaws': {'flaw': {}},
            'powers': {},
            'pools': {'dual': {}, 'moral': {}},
            'virtues': {'moral': {}},
            'archetype': {'personal': {'Nature': {'perm': '', 'temp': ''},
                                     'Demeanor': {'perm': '', 'temp': ''}}},
            'other': {'splat': {'Splat': {'perm': splat.title(), 'temp': splat.title()}}}
        }

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

        elif splat.lower() == 'vampire':
            base_stats['powers']['discipline'] = {}
            base_stats['pools']['dual']['Blood'] = {'perm': 10, 'temp': 10}
            base_stats['pools']['dual']['Willpower'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['dual']['Rage'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['moral']['Road'] = {'perm': 1, 'temp': 1}

        elif splat.lower() == 'mage':
            base_stats['powers']['sphere'] = {}
            base_stats['pools']['dual']['Arete'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['dual']['Quintessence'] = {'perm': 0, 'temp': 0}
            base_stats['pools']['dual']['Willpower'] = {'perm': 5, 'temp': 5}
            base_stats['pools']['resonance'] = {'Resonance': {'perm': 0, 'temp': 0}}
            base_stats['virtues']['synergy'] = {
                'Dynamic': {'perm': 0, 'temp': 0},
                'Entropic': {'perm': 0, 'temp': 0},
                'Static': {'perm': 0, 'temp': 0}
            }
            base_stats['pools']['resonance'] = {'Resonance': {'perm': 0, 'temp': 0}}
            base_stats['identity']['lineage']['Signature'] = {'perm': '', 'temp': ''}
            base_stats['identity']['lineage']['Affinity Sphere'] = {'perm': '', 'temp': ''}
            base_stats['identity']['lineage']['Essence'] = {'perm': '', 'temp': ''}
            base_stats['identity']['lineage']['Affiliation'] = {'perm': '', 'temp': ''}
            
            # Add secondary abilities
            base_stats['abilities']['talent']['Flying'] = {'perm': 0, 'temp': 0}
            base_stats['abilities']['talent']['Lucid Dreaming'] = {'perm': 0, 'temp': 0}
            base_stats['abilities']['skill']['Do'] = {'perm': 0, 'temp': 0}
            
            # Initialize all spheres to 0
            spheres = ['Correspondence', 'Data', 'Dimensional Science', 'Entropy', 'Forces', 'Life', 'Matter', 'Mind', 'Prime', 'Primal Utility', 'Spirit', 'Time']
            for sphere in spheres:
                base_stats['powers']['sphere'][sphere] = {'perm': 0, 'temp': 0}

        elif splat.lower() == 'possessed':
            base_stats['powers']['blessing'] = {}
            base_stats['powers']['charm'] = {}
            base_stats['powers']['gifts'] = {}
            base_stats['pools']['dual']['Willpower'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['dual']['Gnosis'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['dual']['Rage'] = {'perm': 1, 'temp': 1}

        elif splat.lower() == 'changeling':
            base_stats['powers']['art'] = {}
            base_stats['powers']['realm'] = {
                'Actor': {'perm': 0, 'temp': 0},
                'Fae': {'perm': 0, 'temp': 0},
                'Nature': {'perm': 0, 'temp': 0},
                'Prop': {'perm': 0, 'temp': 0},
                'Scene': {'perm': 0, 'temp': 0},
                'Time': {'perm': 0, 'temp': 0}
            }
            base_stats['pools']['dual']['Glamour'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['dual']['Willpower'] = {'perm': 1, 'temp': 1}
            base_stats['pools']['other'] = {
                'Nightmare': {'perm': 0, 'temp': 0},
                'Willpower Imbalance': {'perm': 0, 'temp': 0}
            }
            
            # Initialize Changeling-specific abilities
            base_stats['abilities']['talent']['Kenning'] = {'perm': 0, 'temp': 0}
            base_stats['abilities']['knowledge']['Gremayre'] = {'perm': 0, 'temp': 0}

        elif splat.lower() == 'mortal+':
            base_stats['powers'] = {
                'numina': {},
                'sorcery': {},
                'faith': {},
                'discipline': {},
                'gift': {},
                'art': {},
                'realm': {  # Initialize realms for Kinain
                    'Actor': {'perm': 0, 'temp': 0},
                    'Fae': {'perm': 0, 'temp': 0},
                    'Nature': {'perm': 0, 'temp': 0},
                    'Prop': {'perm': 0, 'temp': 0},
                    'Scene': {'perm': 0, 'temp': 0},
                    'Time': {'perm': 0, 'temp': 0}
                }
            }
            base_stats['pools']['dual']['Willpower'] = {'perm': 3, 'temp': 3}

        elif splat.lower() == 'companion':
            base_stats['powers'] = {
                'special_advantage': {},
                'charm': {}
            }
            base_stats['pools']['dual']['Willpower'] = {'perm': 3, 'temp': 3}
            base_stats['pools']['dual']['Essence'] = {'perm': 15, 'temp': 15}
            base_stats['pools']['dual']['Paradox'] = {'perm': 0, 'temp': 0}
            base_stats['pools']['dual']['Rage'] = {'perm': 0, 'temp': 0}  # Initialize Rage pool
            base_stats['identity']['lineage']['Companion Type'] = {'perm': '', 'temp': ''}
            base_stats['identity']['lineage']['Affiliation'] = {'perm': '', 'temp': ''}
            base_stats['identity']['personal']['Motivation'] = {'perm': '', 'temp': ''}
            base_stats['identity']['personal']['Form'] = {'perm': '', 'temp': ''}

        else:  # Mortal or other
            base_stats['pools']['dual']['Willpower'] = {'perm': 1, 'temp': 1}

        # Set initial base Banality value with all relevant parameters
        subtype = None
        affiliation = None
        tradition = None
        convention = None
        nephandi_faction = None

        if splat.lower() == 'vampire':
            subtype = base_stats.get('identity', {}).get('lineage', {}).get('Clan', {}).get('perm')
        elif splat.lower() == 'mage':
            affiliation = base_stats.get('identity', {}).get('lineage', {}).get('Affiliation', {}).get('perm')
            if affiliation == 'Traditions':
                tradition = base_stats.get('identity', {}).get('lineage', {}).get('Tradition', {}).get('perm')
            elif affiliation == 'Technocracy':
                convention = base_stats.get('identity', {}).get('lineage', {}).get('Convention', {}).get('perm')
            elif affiliation == 'Nephandi':
                nephandi_faction = base_stats.get('identity', {}).get('lineage', {}).get('Nephandi Faction', {}).get('perm')
        elif splat.lower() == 'mortal+':
            subtype = base_stats.get('identity', {}).get('lineage', {}).get('Mortal+ Type', {}).get('perm')
        elif splat.lower() == 'possessed':
            subtype = base_stats.get('identity', {}).get('lineage', {}).get('Possessed Type', {}).get('perm')
        elif splat.lower() == 'shifter':
            subtype = base_stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm')

        banality = get_default_banality(splat, subtype, affiliation, tradition, convention, nephandi_faction)
        base_stats['pools']['dual']['Banality'] = {'perm': banality, 'temp': banality}

        return base_stats

    def update_banality(self, character):
        """Update Banality based on character's current stats."""
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        if not splat:
            return

        # Get all the necessary values for Banality calculation
        subtype = None
        affiliation = None
        tradition = None
        convention = None
        nephandi_faction = None
        
        if splat.lower() == 'vampire':
            subtype = character.get_stat('identity', 'lineage', 'Clan', temp=False)
        elif splat.lower() == 'mage':
            affiliation = character.get_stat('identity', 'lineage', 'Affiliation', temp=False)
            if affiliation == 'Traditions':
                tradition = character.get_stat('identity', 'lineage', 'Tradition', temp=False)
            elif affiliation == 'Technocracy':
                convention = character.get_stat('identity', 'lineage', 'Convention', temp=False)
            elif affiliation == 'Nephandi':
                nephandi_faction = character.get_stat('identity', 'lineage', 'Nephandi Faction', temp=False)
        elif splat.lower() == 'mortal+':
            subtype = character.get_stat('identity', 'lineage', 'Mortal+ Type', temp=False)
        elif splat.lower() == 'possessed':
            subtype = character.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
        elif splat.lower() == 'shifter':
            subtype = character.get_stat('identity', 'lineage', 'Type', temp=False)

        # Calculate new Banality value
        banality = get_default_banality(splat, subtype, affiliation, tradition, convention, nephandi_faction)
        
        # Only update if the value has changed
        current_banality = character.get_stat('pools', 'dual', 'Banality', temp=False)
        if current_banality != banality:
            character.set_stat('pools', 'dual', 'Banality', banality, temp=False)
            character.set_stat('pools', 'dual', 'Banality', banality, temp=True)
            character.msg(f"Your Banality has been updated to {banality} based on your character type.")

    def update_companion_pools(self, character):
        """Update pools based on Companion powers."""
        if character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm') != 'Companion':
            return

        # Get special advantages
        special_advantages = character.db.stats.get('powers', {}).get('special_advantage', {})
        
        # Handle Ferocity
        ferocity = special_advantages.get('Ferocity', {}).get('perm', 0)
        if ferocity:
            rage_value = min(5, ferocity // 2)
            character.set_stat('pools', 'dual', 'Rage', rage_value, temp=False)
            character.set_stat('pools', 'dual', 'Rage', rage_value, temp=True)

        # Handle Feast of Nettles
        feast_level = special_advantages.get('Feast of Nettles', {}).get('perm', 0)
        paradox_values = {
            2: 3,   # 2 points -> 3 permanent
            3: 5,   # 3 points -> 5 permanent
            4: 10,  # 4 points -> 10 permanent
            5: 15,  # 5 points -> 15 permanent
            6: 20   # 6 points -> 20 permanent
        }
        if feast_level in paradox_values:
            character.set_stat('pools', 'dual', 'Paradox', paradox_values[feast_level], temp=False)
            character.set_stat('pools', 'dual', 'Paradox', 0, temp=True)

    def func(self):
        """
        This performs the actual command.
        """
        if not self.args:
            self.caller.msg("Usage: +selfstat <stat>[(<instance>)]/<category>=[+-]<value>")
            return

        # Special handling for splat and type initialization
        if self.stat_name.lower() == 'type' and self.caller.get_stat('other', 'splat', 'Splat') == 'Shifter':
            valid_types = ['Garou', 'Gurahl', 'Rokea', 'Ananasi', 'Ajaba', 'Bastet', 'Corax', 
                          'Kitsune', 'Mokole', 'Nagah', 'Nuwisha', 'Ratkin']
            
            if not self.value_change:
                type_list = ", ".join(valid_types)
                self.caller.msg(f"Valid Shifter types are: {type_list}")
                return
                
            if self.value_change.title() not in valid_types:
                self.caller.msg(f"Invalid Shifter type. Valid types are: {', '.join(valid_types)}")
                return
                
            # Set the type
            self.caller.set_stat('identity', 'lineage', 'Type', self.value_change.title(), temp=False)
            self.caller.msg(f"Successfully set Type to {self.value_change.title()}.")
            
            # Initialize shifter type stats
            from world.wod20th.utils.shifter_utils import initialize_shifter_type
            initialize_shifter_type(self.caller, self.value_change)
            return

        # Continue with regular stat handling
        if not self.stat_name:
            self.caller.msg("Error: No stat name provided. Use 'help selfstat' for correct usage.")
            return
        
        # Special handling for Nature and Demeanor
        stat_name_lower = self.stat_name.lower()
        if stat_name_lower in ['nature', 'demeanor']:
            proper_name = 'Nature' if stat_name_lower == 'nature' else 'Demeanor'
            
            if not self.value_change:
                # Show list of valid archetypes
                archetypes = Stat.objects.filter(stat_type='archetype').order_by('name')
                archetype_list = "\n".join([f"  - {a.name}" for a in archetypes])
                self.caller.msg(f"Please specify a valid archetype for {proper_name}:\n{archetype_list}")
                return
                
            # Validate the archetype
            if not self.validate_archetype(self.value_change):
                archetypes = Stat.objects.filter(stat_type='archetype').order_by('name')
                archetype_list = "\n".join([f"  - {a.name}" for a in archetypes])
                self.caller.msg(f"Invalid archetype '{self.value_change}'. Valid archetypes are:\n{archetype_list}")
                return
                
            # Set the archetype
            self.caller.set_stat('identity', 'personal', proper_name, self.value_change, temp=False)
            self.caller.set_stat('identity', 'personal', proper_name, self.value_change, temp=True)
            self.caller.msg(f"Successfully set {proper_name} to {self.value_change}.")
            return
        
        # Special handling for splat initialization
        if self.stat_name.lower() == 'splat':
            # If no value provided, show valid options
            if not self.value_change:
                valid_splats = ['changeling', 'vampire', 'shifter', 'companion', 'mage', 'mortal', 'mortal+']
                splat_list = "\n".join([f"  - splat={s.title()}" for s in valid_splats])
                self.caller.msg(f"Please specify a splat type using one of:\n{splat_list}")
                return

            try:
                # Validate splat type
                valid_splats = ['changeling', 'vampire', 'shifter', 'companion', 'mage', 'mortal', 'mortal+', 'possessed']
                if self.value_change.lower() not in valid_splats:
                    splat_list = "\n".join([f"  - splat={s.title()}" for s in valid_splats])
                    self.caller.msg(f"Error: Invalid splat type '{self.value_change}'. Must be one of:\n{splat_list}")
                    return

                # Initialize the stats structure based on splat
                self.caller.db.stats = self.initialize_stats(self.value_change)
                self.caller.msg(f"Successfully initialized character as a {self.value_change.title()}.")
                return
            except Exception as e:
                self.caller.msg("Error: Unable to set splat type. Please try again or contact an admin.")
                return

        # Special handling for type initialization
        if self.stat_name.lower() == 'type':
            if not self.caller.db.stats:
                self.caller.msg("Error: You must set your splat first using +selfstat splat=<type>")
                return

            try:
                splat = self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower()
                
                # Show valid types if no value provided
                if not self.value_change:
                    if splat == 'shifter':
                        valid_types = ['Garou', 'Bastet', 'Corax', 'Gurahl', 'Mokole', 'Nagah', 'Nuwisha', 'Ratkin', 'Rokea', 'Ananasi', 'Ajaba']
                    elif splat == 'mortal+':
                        valid_types = ['Ghoul', 'Kinfolk', 'Kinain', 'Sorcerer', 'Faithful', 'Psychic']
                    elif splat == 'possessed':
                        valid_types = ['Fomori', 'Kami']
                    else:
                        self.caller.msg(f"Error: Type setting not applicable for {splat.title()} characters.")
                        return

                    type_list = "\n".join([f"  - type={t}" for t in valid_types])
                    self.caller.msg(f"Please specify a type using one of:\n{type_list}")
                    return

                # Handle Type changes after Splat is set
                if splat.lower() == 'shifter':
                    valid_types = ['garou', 'bastet', 'corax', 'gurahl', 'mokole', 'nagah', 'nuwisha', 'ratkin', 'rokea', 'ananasi', 'ajaba']
                    if self.value_change.lower() not in valid_types:
                        type_list = "\n".join([f"  - type={t.title()}" for t in valid_types])
                        self.caller.msg(f"Error: Invalid shifter type '{self.value_change}'. Must be one of:\n{type_list}")
                        return

                    self.caller.set_stat('identity', 'lineage', 'Type', self.value_change, temp=False)
                    self.caller.set_stat('identity', 'lineage', 'Type', self.value_change, temp=True)
                    
                    # Initialize shifter type stats
                    from world.wod20th.utils.shifter_utils import initialize_shifter_type
                    initialize_shifter_type(self.caller, self.value_change)
                    
                    self.caller.msg(f"Successfully set character type to {self.value_change.title()}.")
                    return

                elif splat.lower() == 'mortal+':
                    valid_types = ['ghoul', 'kinfolk', 'kinain', 'sorcerer', 'faithful', 'psychic']
                    if self.value_change.lower() not in valid_types:
                        type_list = "\n".join([f"  - type={t.title()}" for t in valid_types])
                        self.caller.msg(f"Error: Invalid Mortal+ type '{self.value_change}'. Must be one of:\n{type_list}")
                        return

                    self.caller.set_stat('identity', 'lineage', 'Mortal+ Type', self.value_change.title(), temp=False)
                    self.caller.set_stat('identity', 'lineage', 'Mortal+ Type', self.value_change.title(), temp=True)
                    self.apply_mortalplus_stats(self.caller)
                    self.caller.msg(f"Successfully set character type to {self.value_change.title()}.")
                    return

                elif splat.lower() == 'possessed':
                    valid_types = ['fomori', 'kami']
                    if self.value_change.lower() not in valid_types:
                        type_list = "\n".join([f"  - type={t.title()}" for t in valid_types])
                        self.caller.msg(f"Error: Invalid possessed type '{self.value_change}'. Must be one of:\n{type_list}")
                        return

                    # Use 'Possessed Type' instead of 'Type'
                    self.caller.set_stat('identity', 'lineage', 'Possessed Type', self.value_change.title(), temp=True)
                    self.caller.set_stat('identity', 'lineage', 'Possessed Type', self.value_change.title(), temp=False)
                    self.apply_possessed_stats(self.caller)
                    self.caller.msg(f"Successfully set character type to {self.value_change.title()}.")
                    return

                else:
                    self.caller.msg(f"Error: Type setting not applicable for {splat.title()} characters.")
                    return

            except Exception as e:
                self.caller.msg("Error: Unable to set character type. Please try again or contact an admin.")
                return

        if not self.caller.db.stats:
            self.caller.msg("Error: You don't have any stats initialized. Please create a character first using +selfstat splat=<type>")
            return

        # Handle specialty switch
        if self.is_specialty:
            if not self.stat_name or not self.specialty:
                self.caller.msg("Usage: +selfstat/specialty <stat>=<specialty>")
                return
            # ... rest of specialty handling ...
            return

        # Special handling for Nature stat before stat lookup
        if self.stat_name.lower() == 'nature':
            try:
                splat = self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
                mortalplus_type = self.caller.db.stats.get('identity', {}).get('lineage', {}).get('Mortal+ Type', {}).get('perm', '')
                
                if splat == 'Changeling' or (splat == 'Mortal+' and mortalplus_type == 'Kinain'):
                    # For Changelings and Kinain, we need to ask which type they want to set
                    if not self.category:
                        # For Changelings, default to realm if no category specified
                        if splat == 'Changeling':
                            self.caller.set_stat('powers', 'realm', 'Nature', self.value_change, temp=False)
                            self.caller.set_stat('powers', 'realm', 'Nature', self.value_change, temp=True)
                            msg = f"Successfully set Nature realm to {self.value_change}."
                            self.caller.msg(msg)
                            return
                        # For Kinain, we still need to ask which type they want
                        else:
                            self.caller.msg("Please specify which type of Nature to set:\n  - Nature/realm (for Nature realm)\n  - Nature/personal (for Nature archetype)")
                            return
                    
                    if self.category.lower() == 'realm':
                        self.caller.set_stat('powers', 'realm', 'Nature', self.value_change, temp=False)
                        self.caller.set_stat('powers', 'realm', 'Nature', self.value_change, temp=True)
                        msg = f"Successfully set Nature realm to {self.value_change}."
                        self.caller.msg(msg)
                        return
                    elif self.category.lower() == 'personal':
                        self.caller.set_stat('identity', 'personal', 'Nature', self.value_change, temp=False)
                        self.caller.set_stat('identity', 'personal', 'Nature', self.value_change, temp=True)
                        msg = f"Successfully set Nature archetype to {self.value_change}."
                        self.caller.msg(msg)
                        return
                    else:
                        self.caller.msg("Invalid category. Please use:\n  - Nature/realm (for Nature realm)\n  - Nature/personal (for Nature archetype)")
                        return
                else:
                    # For non-Changelings/non-Kinain, update the Nature archetype
                    self.caller.set_stat('identity', 'archetype', 'Nature', self.value_change, temp=False)
                    self.caller.set_stat('identity', 'archetype', 'Nature', self.value_change, temp=True)
                
                self.caller.set_stat('archetype', 'personal', 'Nature', self.value_change, temp=False)
                self.caller.set_stat('archetype', 'personal', 'Nature', self.value_change, temp=True)
                
                msg = f"Successfully set Nature to {self.value_change}."
                self.caller.msg(msg)
                return
            except Exception as e:
                self.caller.msg("Error: Unable to process Nature stat. Please try again or contact an admin.")
                return

        # Get the character's splat
        try:
            splat = self.caller.db.stats['other']['splat']['Splat']['perm']
        except (KeyError, AttributeError):
            self.caller.msg("Error: Character splat not found. Please ensure your character is properly created.")
            return

        # Special handling for shifter stats that affect pools
        try:
            splat = self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            if splat == 'Shifter':
                shifter_type = self.caller.get_stat('identity', 'lineage', 'Type')
                
                # If setting breed, update Gnosis
                if self.stat_name.lower() == 'breed':
                    from world.wod20th.utils.shifter_utils import initialize_shifter_type
                    initialize_shifter_type(self.caller, shifter_type)
                    return
                
                # If setting auspice/aspect/path/tribe, update Rage/Willpower
                if self.stat_name.lower() in ['auspice', 'aspect', 'path', 'tribe', 'varna']:
                    from world.wod20th.utils.shifter_utils import initialize_shifter_type
                    initialize_shifter_type(self.caller, shifter_type)
                    return
        except Exception as e:
            self.caller.msg("Error: Unable to process shifter stat updates. Please try again or contact an admin.")
            return

        # Get all matching stats first
        try:
            matching_stats = Stat.objects.filter(name__iexact=self.stat_name)
            if not matching_stats.exists():
                # Special handling for Enlightenment for Technocrats
                if self.stat_name.lower() == 'enlightenment':
                    faction = self.caller.get_stat('identity', 'lineage', 'Affiliation')
                    if faction == 'Technocracy':
                        # Create a temporary stat object for Enlightenment pool
                        stat = Stat()
                        stat.name = 'Enlightenment'
                        stat.stat_type = 'dual'
                        stat.category = 'pools'
                        
                        # Validate the value
                        try:
                            new_value = int(self.value_change)
                            if new_value < 1 or new_value > 10:
                                self.caller.msg("Error: Enlightenment must be between 1 and 10.")
                                return
                            
                            # Update the stat
                            self.caller.set_stat('pools', 'dual', 'Enlightenment', new_value, temp=False)
                            self.caller.set_stat('pools', 'dual', 'Enlightenment', new_value, temp=True)
                            self.caller.msg(f"Successfully set Enlightenment to {new_value}.")
                            return
                        except ValueError:
                            self.caller.msg("Error: Enlightenment must be a number between 1 and 10.")
                            return
                
                # If exact match fails, try a case-insensitive contains search
                matching_stats = Stat.objects.filter(name__icontains=self.stat_name)
                if not matching_stats.exists():
                    self.caller.msg(f"Error: Stat '{self.stat_name}' not found. Use 'help selfstat' to see available stats.")
                    return

            # If only one stat found, use it regardless of category
            if matching_stats.count() == 1:
                stat = matching_stats.first()
                self.category = stat.stat_type  # Set the category to match the found stat
            # Special handling for Enlightenment to differentiate between pool and path
            elif self.stat_name.lower() == 'enlightenment':
                splat = self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
                
                if splat == 'Mage':
                    # For Mages, check if they're a Technocrat
                    if self.caller.get_stat('identity', 'lineage', 'Affiliation') == 'Technocracy':
                        # Create a temporary stat object for Enlightenment pool
                        stat = Stat()
                        stat.name = 'Enlightenment'
                        stat.stat_type = 'dual'
                        stat.category = 'pools'
                        
                        # Validate the value
                        try:
                            new_value = int(self.value_change)
                            if new_value < 1 or new_value > 10:
                                self.caller.msg("Error: Enlightenment must be between 1 and 10.")
                                return
                            
                            # Update the stat
                            self.caller.set_stat('pools', 'dual', 'Enlightenment', new_value, temp=False)
                            self.caller.set_stat('pools', 'dual', 'Enlightenment', new_value, temp=True)
                            self.caller.msg(f"Successfully set Enlightenment to {new_value}.")
                            return
                        except ValueError:
                            self.caller.msg("Error: Enlightenment must be a number between 1 and 10.")
                            return
                elif splat == 'Vampire':
                    # For Vampires, treat as a path
                    if self.value_change not in PATH_VIRTUES:
                        valid_paths = ", ".join(sorted(PATH_VIRTUES.keys()))
                        self.caller.msg(f"Error: Invalid Enlightenment path '{self.value_change}'. Valid paths are:\n{valid_paths}")
                        return
                    
                    # Create a temporary stat object for Vampire Enlightenment path
                    stat = Stat()
                    stat.name = 'Enlightenment'
                    stat.stat_type = 'lineage'
                    stat.category = 'identity'
                    
                    # Get the virtues for both old and new paths
                    old_path = self.caller.db.stats.get('identity', {}).get('lineage', {}).get('Enlightenment', {}).get('perm', 'Humanity')
                    old_virtues = PATH_VIRTUES.get(old_path, PATH_VIRTUES['Humanity'])
                    new_virtues = PATH_VIRTUES[self.value_change]
                    
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
                            if self.value_change != 'Humanity' and virtue in ['Conviction', 'Instinct']:
                                self.caller.set_stat('virtues', 'moral', virtue, 0, temp=False)
                                self.caller.set_stat('virtues', 'moral', virtue, 0, temp=True)
                            else:  # Conscience, Self-Control, and Courage always start at 1
                                self.caller.set_stat('virtues', 'moral', virtue, 1, temp=False)
                                self.caller.set_stat('virtues', 'moral', virtue, 1, temp=True)
                    
                    # Update the path
                    self.caller.set_stat('identity', 'lineage', 'Enlightenment', self.value_change, temp=False)
                    self.caller.set_stat('identity', 'lineage', 'Enlightenment', self.value_change, temp=True)
                    
                    self.caller.msg(f"Successfully changed Enlightenment path from {old_path} to {self.value_change} and initialized virtues.")
                    return
            # If multiple stats found and category specified, find the matching stat
            elif self.category:
                stat = matching_stats.filter(stat_type__iexact=self.category).first()
                if not stat:
                    categories = ", ".join(set(s.stat_type for s in matching_stats))
                    self.caller.msg(f"Error: No stat '{self.stat_name}' found with category '{self.category}'.\nAvailable categories for this stat: {categories}")
                    return
            # If multiple stats found and no category specified, show options
            else:
                # Group stats by category and stat_type
                stat_options = []
                for s in matching_stats:
                    stat_options.append(f"{s.name}/{s.stat_type}")
                
                options_str = "\n".join([f"  - {opt}" for opt in stat_options])
                self.caller.msg(f"Multiple versions of '{self.stat_name}' exist. Please specify one of:\n{options_str}")
                return

            if not stat:
                self.caller.msg(f"Error: Stat '{self.stat_name}' not found. Use 'help selfstat' to see available stats.")
                return

        except Exception as e:
            self.caller.msg(f"Error: Unable to search for stats. Please try again or contact an admin if the issue persists.")
            return

        # Now validate the category (which might have been auto-set above)
        valid_categories = ['physical', 'social', 'mental', 'talent', 'skill', 'knowledge', 'secondary_abilities',
                          'secondary_talent', 'secondary_skill', 'secondary_knowledge', 'advantage', 'advantages', 'splat',
                          'background', 'merit', 'merits', 'flaw', 'flaws', 'moral', 'dual', 'gift', 'discipline', 
                          'sphere', 'art', 'realm', 'power', 'numina', 'sliver', 'charm', 'sorcery', 'art', 'realm', 
                          'rote', 'edge', 'special_advantage', 'faith', 'sphere', 'rite', 'thaumaturgy', 'ritual', 'supernatural',
                          'combodiscipline', 'type', 'renown', 'lineage', 'identity', 'virtues', 'traits', 'other',
                          'generation', 'blessing', 'possessed_type', 'hedge_ritual', 'date_of_possession', 'spirit_name', 'personal',
                          'identity',  'phyla', 'archetype', 'legacy', 'unseelie_legacy', 'pryio', 'cabal', 'motley', #should be covered in lineage, but just in case because i can be a moron
                          'clan', 'tribe', 'affiliation', 'convention', 'tradition', 'nephandi_faction', 'coterie',  #should be covered in lineage, but just in case because i can be a moron
                          'pack', 'nest', 'varna', 'ananasi_faction', 'ananasi_cabal', 'aspect', 'auspice', 'crown', #should be covered in lineage, but just in case because i can be a moron
                          ]

        if self.category.lower() not in valid_categories:
            self.caller.msg(f"Error: Invalid category '{self.category}'. Valid categories are: {', '.join(valid_categories)}")
            return

        # Use the canonical name from the database
        self.stat_name = stat.name

        # Special handling for Mage Faction changes
        if self.stat_name == 'Affiliation' and self.value_change.lower() == 'technocracy':
            try:
                # Store the old value for comparison
                old_value = self.caller.get_stat('identity', 'lineage', 'Affiliation')
                
                # Set the new value
                self.caller.set_stat('identity', 'lineage', 'Affiliation', self.value_change, temp=False)
                
                # Only perform Technocracy conversion if this is a new Technocrat
                if old_value != 'Technocracy':
                    # Get current Arete value
                    arete_value = self.caller.get_stat('pools', 'dual', 'Arete') or 1
                    
                    # Remove Arete and add Enlightenment
                    if 'Arete' in self.caller.db.stats.get('pools', {}).get('dual', {}):
                        del self.caller.db.stats['pools']['dual']['Arete']
                    
                    # Initialize Enlightenment with the same value as Arete
                    self.caller.set_stat('pools', 'dual', 'Enlightenment', arete_value, temp=False)
                    self.caller.set_stat('pools', 'dual', 'Enlightenment', arete_value, temp=True)
                    
                    # Remove non-Technocracy spheres
                    spheres_to_remove = ['Spirit', 'Correspondence', 'Prime']
                    for sphere in spheres_to_remove:
                        if sphere in self.caller.db.stats.get('powers', {}).get('sphere', {}):
                            del self.caller.db.stats['powers']['sphere'][sphere]
                    
                    self.caller.msg(f"Successfully set Mage Faction to Technocracy and initialized Enlightenment to {arete_value}.")
                    return
            except Exception as e:
                self.caller.msg("Error: Unable to process Technocracy conversion. Please try again or contact an admin.")
                return

        # Special handling for Shifter Rank
        if stat.name == 'Rank':
            try:
                splat = self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
                if splat and splat == 'Shifter':
                    stat.category = 'identity'
                    stat.stat_type = 'lineage'
            except Exception as e:
                self.caller.msg("Error: Unable to process Shifter Rank. Please ensure your character is properly created.")
                return

        # Check if the character can have this ability
        if stat.stat_type == 'ability' and not self.caller.can_have_ability(stat.name):
            self.caller.msg(f"Error: Your character type cannot have the {stat.name} ability.")
            return

        # Handle instances for background stats
        if stat.instanced:
            if not self.instance:
                examples = "Examples:\n  - Status(Ventrue)\n  - Resources(Family)\n  - Allies(Police)"
                self.caller.msg(f"Error: The stat '{self.stat_name}' requires an instance. Use the format: {self.stat_name}(instance)\n{examples}")
                return
            full_stat_name = f"{self.stat_name}({self.instance})"
        else:
            if self.instance:
                self.caller.msg(f"Error: The stat '{self.stat_name}' does not support instances. Use just the stat name without parentheses.")
                return
            full_stat_name = self.stat_name

        # Handle stat removal (empty value)
        if self.value_change == '':
            try:
                if stat.category in self.caller.db.stats and stat.stat_type in self.caller.db.stats[stat.category]:
                    if full_stat_name in self.caller.db.stats[stat.category][stat.stat_type]:
                        # For language-related stats, pass 0 instead of removing directly
                        if (full_stat_name == 'Language' or 
                            full_stat_name.startswith('Language(') or 
                            full_stat_name == 'Natural Linguist'):
                            self.caller.set_stat(stat.category, stat.stat_type, full_stat_name, 0)
                        else:
                            del self.caller.db.stats[stat.category][stat.stat_type][full_stat_name]
                        self.caller.msg(f"Successfully removed stat '{full_stat_name}'.")
                        return
                    else:
                        self.caller.msg(f"Error: Stat '{full_stat_name}' not found on your character.")
                        return
            except Exception as e:
                self.caller.msg(f"Error: Unable to remove stat. Please try again or contact an admin if the issue persists.")
                return

        # Special handling for Appearance stat
        if stat.name == 'Appearance':
            try:
                splat = self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
                clan = self.caller.db.stats.get('identity', {}).get('lineage', {}).get('Clan', {}).get('perm', '')
                
                if splat and splat == 'Vampire' and clan in ['Nosferatu', 'Samedi']:
                    self.caller.msg("Note: Nosferatu and Samedi vampires always have Appearance 0.")
                    return
                
                if splat and splat == 'Shifter':
                    form = self.caller.db.stats.get('other', {}).get('form', {}).get('Form', {}).get('temp', '')
                    if form == 'Crinos':
                        self.caller.msg("Note: Characters in Crinos form always have Appearance 0.")
                        return
            except Exception as e:
                self.caller.msg("Error: Unable to process Appearance stat. Please try again or contact an admin.")
                return

            if self.value_change.startswith('+') or self.value_change.startswith('-'):
                current_value = self.caller.get_stat(stat.category, stat.stat_type, full_stat_name)
                if current_value is None:
                    current_value = 0
                new_value = current_value + int(self.value_change)
            else:
                new_value = int(self.value_change) if self.value_change.isdigit() else self.value_change
                
            return

        # Special handling for Enlightenment changes
        if stat.name == 'Enlightenment':
            try:
                old_path = self.caller.db.stats.get('identity', {}).get('lineage', {}).get('Enlightenment', {}).get('perm', 'Humanity')
                
                # Get the virtues for both old and new paths
                old_virtues = PATH_VIRTUES.get(old_path, PATH_VIRTUES['Humanity'])
                new_virtues = PATH_VIRTUES.get(new_value, PATH_VIRTUES['Humanity'])
                
                if new_value not in PATH_VIRTUES:
                    valid_paths = ", ".join(sorted(PATH_VIRTUES.keys()))
                    self.caller.msg(f"Error: Invalid Enlightenment path '{new_value}'. Valid paths are:\n{valid_paths}")
                    return

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
                
                # Update the Enlightenment path in lineage
                self.caller.set_stat('identity', 'lineage', 'Enlightenment', new_value, temp=False)
                self.caller.set_stat('identity', 'lineage', 'Enlightenment', new_value, temp=True)
                
                self.caller.msg(f"Successfully changed Enlightenment path from {old_path} to {new_value}.")
            except Exception as e:
                self.caller.msg("Error: Unable to process Enlightenment change. Please try again or contact an admin.")
                return

        # Special handling for Kith changes for Inanimae
        if stat.name == 'Kith' and new_value.lower() == 'inanimae':
            try:
                # Initialize Phyla field if it doesn't exist
                if 'identity' not in self.caller.db.stats:
                    self.caller.db.stats['identity'] = {}
                if 'lineage' not in self.caller.db.stats['identity']:
                    self.caller.db.stats['identity']['lineage'] = {}
                
                # Add Phyla field in lineage
                self.caller.set_stat('identity', 'lineage', 'Phyla', '', temp=False)
                self.caller.set_stat('identity', 'lineage', 'Phyla', '', temp=True)
                
                # Initialize powers structure for Slivers if it doesn't exist
                if 'powers' not in self.caller.db.stats:
                    self.caller.db.stats['powers'] = {}
                if 'sliver' not in self.caller.db.stats['powers']:
                    self.caller.db.stats['powers']['sliver'] = {}
                
                self.caller.msg("Successfully set Kith to Inanimae. Please set your Phyla next using +selfstat Phyla/lineage=<phyla>")
            except Exception as e:
                self.caller.msg("Error: Unable to process Inanimae Kith change. Please try again or contact an admin.")
                return

        # Special handling for Phyla changes
        if stat.name == 'Phyla':
            try:
                if new_value not in PHYLA:
                    valid_phyla = ", ".join(sorted(PHYLA))
                    self.caller.msg(f"Error: Invalid Phyla '{new_value}'. Valid options are:\n{valid_phyla}")
                    return

                # Validate that character is an Inanimae
                kith = self.caller.get_stat('identity', 'lineage', 'Kith')
                if kith != 'Inanimae':
                    self.caller.msg("Error: Only Inanimae characters can have a Phyla. Set your Kith to Inanimae first.")
                    return

                # Set up appropriate powers based on Phyla
                if new_value in INANIMAE_POWERS:
                    # Clear existing powers first
                    if 'powers' in self.caller.db.stats:
                        if 'sliver' in self.caller.db.stats['powers']:
                            self.caller.db.stats['powers']['sliver'] = {}
                        # Only initialize art category for Mannikins
                        if new_value == 'Mannikins':
                            if 'art' not in self.caller.db.stats['powers']:
                                self.caller.db.stats['powers']['art'] = {}
                        # Remove art category for non-Mannikins
                        elif 'art' in self.caller.db.stats['powers']:
                            del self.caller.db.stats['powers']['art']

                    # Set Phyla in lineage
                    self.caller.set_stat('identity', 'lineage', 'Phyla', new_value, temp=False)
                    self.caller.set_stat('identity', 'lineage', 'Phyla', new_value, temp=True)
                    
                    # Remove old Phyla location if it exists
                    if 'phyla' in self.caller.db.stats.get('identity', {}):
                        del self.caller.db.stats['identity']['phyla']
                    
                    self.caller.msg(f"Successfully set Phyla to {new_value}.")
            except Exception as e:
                self.caller.msg("Error: Unable to process Phyla change. Please try again or contact an admin.")
                return

        # Validate stat value
        try:
            if isinstance(new_value, (int, float)):
                # Special validation for specific stats
                if stat.name == 'Generation' and stat.category == 'identity' and isinstance(new_value, (int, float)):
                    if new_value < 4 or new_value > 15:
                        self.caller.msg("Error: Your generation must be between 4th and 15th.")
                        return
                elif stat.name == 'Generation' and stat.category == 'background' and isinstance(new_value, (int, float)):
                    if new_value < 0 or new_value > 5:
                        self.caller.msg("Error: Generation background must be between 0 and 5.")
                        return

            # Update the stat
            try:
                # Always set both permanent and temporary stats
                self.caller.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=False)
                self.caller.set_stat(stat.category, stat.stat_type, full_stat_name, new_value, temp=True)
                
                # Update Banality if relevant stats changed
                if (stat.name in ['Clan', 'Affiliation', 'Tradition', 'Convention', 'Nephandi Faction', 
                                'Mortal+ Type', 'Possessed Type', 'Type'] or 
                    full_stat_name in ['Clan', 'Affiliation', 'Tradition', 'Convention', 'Nephandi Faction',
                                     'Mortal+ Type', 'Possessed Type', 'Type']):
                    self.update_banality(self.caller)
                
                # Special handling for Techne background updates for Sorcerers
                if (stat.name == 'Techne' and stat.stat_type == 'background' and 
                    self.caller.get_stat('identity', 'lineage', 'Mortal+ Type') == 'Sorcerer'):
                    # Update Mana pool to match new Techne value
                    self.caller.set_stat('pools', 'dual', 'Mana', new_value, temp=False)
                    self.caller.set_stat('pools', 'dual', 'Mana', new_value, temp=True)
                    msg = f"Successfully set {full_stat_name} to {new_value} and updated Mana pool to match."
                else:
                    # Format success message
                    if isinstance(new_value, (int, float)):
                        msg = f"Successfully set {full_stat_name} to {new_value}."
                    else:
                        msg = f"Successfully set {full_stat_name} to '{new_value}'."
                
                self.caller.msg(msg)

            except Exception as e:
                self.caller.msg(f"Error: Unable to update {full_stat_name}. Please try again or contact an admin.")
                return

        except Exception as e:
            self.caller.msg("Error: An unexpected error occurred. Please try again or contact an admin if the issue persists.")
            return

        # Special handling for Nightmare to ensure it stays in the dictionary
        if self.stat_name == 'Nightmare':
            try:
                value = int(self.value_change)
                # Ensure pools/other structure exists
                if 'pools' not in self.caller.db.stats:
                    self.caller.db.stats['pools'] = {}
                if 'other' not in self.caller.db.stats['pools']:
                    self.caller.db.stats['pools']['other'] = {}
                if 'Nightmare' not in self.caller.db.stats['pools']['other']:
                    self.caller.db.stats['pools']['other']['Nightmare'] = {}
                
                # Set both temp and perm values
                self.caller.db.stats['pools']['other']['Nightmare']['temp'] = value
                self.caller.db.stats['pools']['other']['Nightmare']['perm'] = value
                
                return
            except ValueError:
                self.caller.msg("Error: Nightmare value must be a number.")
                return

        # After the stat value is set, check if we need to adjust pools
        try:
            if stat.stat_type in ['blessing', 'special_advantage']:
                self.apply_power_based_pools(self.caller, stat.stat_type, full_stat_name, new_value)
                # For Companions, update all pools after any special advantage change
                if self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm') == 'Companion':
                    self.update_companion_pools(self.caller)
        except Exception as e:
            self.caller.msg("Error: Unable to process power-based pool adjustments. Please try again or contact an admin.")
            return

        # Special handling for Banality
        if self.stat_name.lower() == 'banality':
            try:
                new_value = int(self.value_change)
                if 0 <= new_value <= 10:  # Banality ranges from 0 to 10
                    self.caller.set_stat('pools', 'dual', 'Banality', new_value, temp=False)
                    self.caller.set_stat('pools', 'dual', 'Banality', new_value, temp=True)
                    self.caller.msg(f"Set Banality to {new_value}.")
                else:
                    self.caller.msg("Error: Banality must be between 0 and 10.")
                return
            except ValueError:
                self.caller.msg("Error: Banality must be a number between 0 and 10.")
                return

    def apply_power_based_pools(self, character, power_type, power_name, value):
        """Adjust pools based on specific powers."""
        # Handle Possessed blessings
        if power_type == 'blessing':
            if power_name == 'Berserker':
                # Set Rage to 5 for characters with Berserker blessing
                character.set_stat('pools', 'dual', 'Rage', 5, temp=False)
                character.set_stat('pools', 'dual', 'Rage', 5, temp=True)
            elif power_name == 'Spirit Ties':
                # Set Gnosis equal to Spirit Ties level
                character.set_stat('pools', 'dual', 'Gnosis', value, temp=False)
                character.set_stat('pools', 'dual', 'Gnosis', value, temp=True)

        # Handle Companion special advantages
        elif power_type == 'special_advantage':
            if power_name == 'Ferocity':
                # Calculate Rage based on Ferocity (1 Rage per 2 points, max 5)
                rage_value = min(5, value // 2)
                # Set both permanent and temporary values
                character.set_stat('pools', 'dual', 'Rage', rage_value, temp=False)
                character.set_stat('pools', 'dual', 'Rage', rage_value, temp=True)
            elif power_name == 'Feast of Nettles':
                # Set Paradox pool based on Feast of Nettles level
                paradox_values = {
                    2: 3,   # 2 points -> 3 permanent
                    3: 5,   # 3 points -> 5 permanent
                    4: 10,  # 4 points -> 10 permanent
                    5: 15,  # 5 points -> 15 permanent
                    6: 20   # 6 points -> 20 permanent
                }
                if value in paradox_values:
                    # Set both permanent and temporary values
                    character.set_stat('pools', 'dual', 'Paradox', paradox_values[value], temp=False)
                    character.set_stat('pools', 'dual', 'Paradox', paradox_values[value], temp=True)
                    # Then set temporary to 0 after ensuring the pool exists
                    character.set_stat('pools', 'dual', 'Paradox', 0, temp=True)

    def apply_mortalplus_stats(self, character):
        """Apply specific stats based on Mortal+ subtype."""
        subtype = character.get_stat('identity', 'lineage', 'Mortal+ Type')
        
        if subtype == 'Ghoul':
            # Set Blood Pool for Ghouls
            character.set_stat('pools', 'dual', 'Blood', 3, temp=False)
            character.set_stat('pools', 'dual', 'Blood', 3, temp=True)
            character.set_stat('pools', 'dual', 'Banality', 6, temp=False)
            character.set_stat('pools', 'dual', 'Banality', 6, temp=True)
            
        elif subtype == 'Kinfolk':
            # Set Gnosis for Kinfolk
            character.set_stat('pools', 'dual', 'Gnosis', 0, temp=False)
            character.set_stat('pools', 'dual', 'Gnosis', 0, temp=True)
            character.set_stat('pools', 'dual', 'Banality', 5, temp=False)
            character.set_stat('pools', 'dual', 'Banality', 5, temp=True)
            
        elif subtype == 'Kinain':
            # Set Glamour for Kinain
            character.set_stat('pools', 'dual', 'Glamour', 2, temp=False)
            character.set_stat('pools', 'dual', 'Glamour', 2, temp=True)
            character.set_stat('pools', 'dual', 'Banality', 3, temp=False)
            character.set_stat('pools', 'dual', 'Banality', 3, temp=True)
            
        elif subtype == 'Sorcerer':
            # Initialize Mana pool based on Techne background
            techne = character.get_stat('advantages', 'background', 'Techne') or 0
            character.set_stat('pools', 'dual', 'Mana', techne, temp=False)
            character.set_stat('pools', 'dual', 'Mana', techne, temp=True)
            character.set_stat('pools', 'dual', 'Banality', 5, temp=False)
            character.set_stat('pools', 'dual', 'Banality', 5, temp=True)
        elif subtype == 'Psychic':
            character.set_stat('pools', 'dual', 'Banality', 5, temp=False)
            character.set_stat('pools', 'dual', 'Banality', 5, temp=True)

        elif subtype == 'Faithful':
            character.set_stat('pools', 'dual', 'Banality', 6, temp=False)
            character.set_stat('pools', 'dual', 'Banality', 6, temp=True)

        # Set base Willpower for all types
        if not character.get_stat('pools', 'dual', 'Willpower', temp=False):
            character.set_stat('pools', 'dual', 'Willpower', 1, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', 1, temp=True)

    def apply_possessed_stats(self, character):
        """Apply specific stats for Possessed characters."""
        # Use 'Possessed Type' instead of 'Type'
        subtype = character.get_stat('identity', 'lineage', 'Possessed Type')
        
        # Ensure powers sections exist and are initialized
        if 'powers' not in character.db.stats:
            character.db.stats['powers'] = {}
        
        # Initialize power sections with empty dictionaries
        character.db.stats['powers']['blessing'] = {}
        character.db.stats['powers']['charm'] = {}
        character.db.stats['powers']['gifts'] = {}
        
        # Ensure pools section exists
        if 'pools' not in character.db.stats:
            character.db.stats['pools'] = {'dual': {}}
        elif 'dual' not in character.db.stats['pools']:
            character.db.stats['pools']['dual'] = {}
        
        # Ensure identity section exists
        if 'identity' not in character.db.stats:
            character.db.stats['identity'] = {'lineage': {}}
        elif 'lineage' not in character.db.stats['identity']:
            character.db.stats['identity']['lineage'] = {}
        
        # Initialize additional Possessed-specific identity stats
        identity_stats = [
            'Date of Possession', 
            'Spirit Name'
        ]
        
        # Subtype-specific stats
        if subtype == 'Fomori':
            identity_stats.append('Bane Type')
        elif subtype == 'Kami':
            identity_stats.append('Gaian Spirit')
        
        # Set empty values for these stats
        for stat in identity_stats:
            character.set_stat('identity', 'lineage', stat, '', temp=False)
            character.set_stat('identity', 'lineage', stat, '', temp=True)
        
        # Set pools based on type
        if subtype == 'Fomori':
            # Set Willpower for Fomori based on Wyrm corruption
            character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
            character.set_stat('pools', 'dual', 'Banality', 7, temp=False)
            character.set_stat('pools', 'dual', 'Banality', 7, temp=True)
            
            # Set Gnosis and Rage for Fomori
            character.set_stat('pools', 'dual', 'Gnosis', 0, temp=False)
            character.set_stat('pools', 'dual', 'Gnosis', 0, temp=True)
            character.set_stat('pools', 'dual', 'Rage', 1, temp=False)
            character.set_stat('pools', 'dual', 'Rage', 1, temp=True)
            
        elif subtype == 'Kami':
            character.set_stat('pools', 'dual', 'Banality', 4, temp=False)
            character.set_stat('pools', 'dual', 'Banality', 4, temp=True)
            # Set Willpower for Kami based on Gaia connection
            character.set_stat('pools', 'dual', 'Willpower', 4, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', 4, temp=True)
            
            # Set Gnosis and Rage for Kami
            character.set_stat('pools', 'dual', 'Gnosis', 1, temp=False)
            character.set_stat('pools', 'dual', 'Gnosis', 1, temp=True)
            character.set_stat('pools', 'dual', 'Rage', 0, temp=False)
            character.set_stat('pools', 'dual', 'Rage', 0, temp=True)
        
        # Fallback: Ensure minimum Willpower
        if not character.get_stat('pools', 'dual', 'Willpower', temp=False):
            character.set_stat('pools', 'dual', 'Willpower', 1, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', 1, temp=True)
        
        # Ensure Gnosis and Rage are always present
        if not character.get_stat('pools', 'dual', 'Gnosis', temp=False):
            character.set_stat('pools', 'dual', 'Gnosis', 0, temp=False)
            character.set_stat('pools', 'dual', 'Gnosis', 0, temp=True)
        
        if not character.get_stat('pools', 'dual', 'Rage', temp=False):
            character.set_stat('pools', 'dual', 'Rage', 0, temp=False)
            character.set_stat('pools', 'dual', 'Rage', 0, temp=True)

    def initialize_possessed_stats(self, character, possessed_type=None):
        """Initialize stats specific to Possessed types."""
        if possessed_type is None:
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

        # Set the final pool values
        character.set_stat('pools', 'dual', 'Gnosis', base_gnosis, temp=False)
        character.set_stat('pools', 'dual', 'Gnosis', base_gnosis, temp=True)
        character.set_stat('pools', 'dual', 'Willpower', base_willpower, temp=False)
        character.set_stat('pools', 'dual', 'Willpower', base_willpower, temp=True)
        character.set_stat('pools', 'dual', 'Rage', base_rage, temp=False)
        character.set_stat('pools', 'dual', 'Rage', base_rage, temp=True)

        # Initialize powers categories if they don't exist
        if 'powers' not in character.db.stats:
            character.db.stats['powers'] = {}
        if 'blessing' not in character.db.stats['powers']:
            character.db.stats['powers']['blessing'] = {}
        if 'charm' not in character.db.stats['powers']:
            character.db.stats['powers']['charm'] = {}
        if 'gifts' not in character.db.stats['powers']:
            character.db.stats['powers']['gifts'] = {}

    def validate_archetype(self, archetype_name):
        """
        Validate if the given archetype exists in the database.
        
        Args:
            archetype_name (str): The name of the archetype to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        return Stat.objects.filter(
            stat_type='archetype',
            name__iexact=archetype_name
        ).exists()
