from evennia import Command, default_cmds
from django.db import models
from typing import Dict, List, Union
import re

# Import models
from world.wod20th.models import Stat

# Import utility functions and constants
from world.wod20th.utils.stat_mappings import (
    UNIVERSAL_BACKGROUNDS, VALID_MORTALPLUS_TYPES, VALID_POSSESSED_TYPES,
    GENERATION_FLAWS, GENERATION_MAP, VAMPIRE_BACKGROUNDS, CHANGELING_BACKGROUNDS,
    MAGE_BACKGROUNDS, TECHNOCRACY_BACKGROUNDS, TRADITIONS_BACKGROUNDS, NEPHANDI_BACKGROUNDS,
    SHIFTER_BACKGROUNDS, STAT_TYPE_TO_CATEGORY, IDENTITY_STATS, SPLAT_STAT_OVERRIDES,
    ARTS, REALMS, MAGE_SPHERES
)
from world.wod20th.utils.shifter_utils import (
    SHIFTER_TYPE_CHOICES, AUSPICE_CHOICES, BASTET_TRIBE_CHOICES,
    BREED_CHOICES, GAROU_TRIBE_CHOICES, initialize_shifter_type
)
from world.wod20th.utils.vampire_utils import (
    CLAN, get_clan_disciplines, calculate_blood_pool,
    
)
from world.wod20th.utils.mortalplus_utils import (
    MORTALPLUS_POOLS,
    MORTALPLUS_POWERS, validate_mortalplus_powers, can_learn_power,
    
)
from world.wod20th.utils.possessed_utils import (
    POSSESSED_POOLS
)
from world.wod20th.utils.companion_utils import (
    COMPANION_TYPES, POWER_SOURCE_TYPES, COMPANION_POWERS
)
from world.wod20th.utils.virtue_utils import PATH_VIRTUES, calculate_willpower
from world.wod20th.utils.banality import get_default_banality

from commands.CmdLanguage import CmdLanguage

# Changeling Legacy Constants
SEELIE_LEGACIES = ["Bumpkin", "Courtier", "Crafter", "Dandy", "Hermit", "Orchid", "Paladin", 
                   "Panderer", "Regent", "Sage", "Saint", "Squire", "Troubadour", "Wayfarer"]
UNSEELIE_LEGACIES = ["Beast", "Fatalist", "Fool", "Grotesque", "Knave", "Outlaw", "Pandora", 
                     "Peacock", "Rake", "Riddler", "Ringleader", "Rogue", "Savage", "Wretch"]

class CmdSelfStat(default_cmds.MuxCommand):
    """
    Usage:
      +selfstat <stat>[/type]=<value>
      +selfstat/specialty <stat>=<specialty>

    Examples:
      +selfstat Strength/physical=+1
      +selfstat Firearms/skill=-1
      +selfstat Status(Ventrue)/background=
      +selfstat/specialty Firearms=Sniping

    The stat_type specifies what kind of stat this is (physical, social, mental,
    skill, talent, knowledge, background, discipline, etc). This helps distinguish
    between stats that might have the same name but are different types.

    For a list of valid stat types, use '+info stat_types'
    """

    key = "+selfstat"
    aliases = ["selfstat"]
    locks = "cmd:all()"  # All players can use this command
    help_category = "Chargen & Character Info"

    def __init__(self):
        """Initialize the command."""
        super().__init__()
        self.switches = []
        self.is_specialty = False
        self.stat_name = ""
        self.instance = None
        self.category = None
        self.value_change = None
        self.stat_type = None
        self.is_removal = False

    def initialize_stats(self, splat):
        """Initialize the basic stats structure based on splat type."""
        # Reset languages to just English
        self.caller.db.languages = ["English"]
        self.caller.db.native_language = "English"
        self.caller.db.speaking_language = "English"
        
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
            'advantages': {'background': {}, 'renown': {}},
            'merits': {'merit': {}},
            'flaws': {'flaw': {}},
            'powers': {
                'gift': {},
                'rite': {},
                'discipline': {},
                'sphere': {},
                'art': {},
                'realm': {},
                'blessing': {},
                'charm': {},
                'sorcery': {},
                'numina': {},
                'ritual': {},
                'faith': {},
                'hedge_ritual': {},
                'combodiscipline': {},
            },
            'pools': {
                'dual': {},
                'moral': {},
                'advantage': {},
                'resonance': {}
            },
            'virtues': {'moral': {}},
            'archetype': {
                'personal': {
                    'Nature': {'perm': '', 'temp': ''},
                    'Demeanor': {'perm': '', 'temp': ''}
                }
            }
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

        # Set base Willpower for all splats
        base_stats['pools']['dual']['Willpower'] = {'perm': 3, 'temp': 3}

        # Set the base stats
        self.caller.db.stats = base_stats

        # Initialize splat-specific stats using the appropriate utility functions
        if splat.lower() == 'vampire':
            # Initialize vampire stats with default clan (can be changed later)
            from world.wod20th.utils.vampire_utils import initialize_vampire_stats
            initialize_vampire_stats(self.caller, '')
            
            # Set default virtues for vampires
            self.caller.db.stats['virtues']['moral'].update({
                'Conscience': {'perm': 1, 'temp': 1},
                'Self-Control': {'perm': 1, 'temp': 1},
                'Courage': {'perm': 1, 'temp': 1}
            })
            self.caller.db.stats['pools']['moral']['Road'] = {'perm': 3, 'temp': 3}

        elif splat.lower() == 'mage':
            # Initialize mage stats (affiliation can be set later)
            from world.wod20th.utils.mage_utils import initialize_mage_stats
            initialize_mage_stats(self.caller, '')
            
            # Set up mage-specific pools
            self.caller.db.stats['pools']['advantage']['Arete'] = {'perm': 1, 'temp': 1}
            self.caller.db.stats['pools']['dual']['Quintessence'] = {'perm': 1, 'temp': 1}
            self.caller.db.stats['pools']['dual']['Paradox'] = {'perm': 0, 'temp': 0}
            self.caller.db.stats['pools']['resonance']['Resonance'] = {'perm': 0, 'temp': 0}
            
            # Set up synergy virtues with starting values
            self.caller.db.stats['virtues']['synergy'] = {
                'Dynamic': {'perm': 0, 'temp': 0},
                'Entropic': {'perm': 0, 'temp': 0},
                'Static': {'perm': 0, 'temp': 0}
            }

        elif splat.lower() == 'changeling':
            # Initialize changeling stats (kith and seeming can be set later)
            from world.wod20th.utils.changeling_utils import initialize_changeling_stats
            initialize_changeling_stats(self.caller, '', '')

        elif splat.lower() == 'shifter':
            # Initialize shifter stats (type can be set later)
            from world.wod20th.utils.shifter_utils import initialize_shifter_type
            initialize_shifter_type(self.caller, '')

        elif splat.lower() == 'mortal+':
            # Initialize mortal+ stats (type can be set later)
            from world.wod20th.utils.mortalplus_utils import initialize_mortalplus_stats
            initialize_mortalplus_stats(self.caller, '')

        elif splat.lower() == 'possessed':
            # Initialize possessed stats (type can be set later)
            from world.wod20th.utils.possessed_utils import initialize_possessed_stats
            initialize_possessed_stats(self.caller, '')

        elif splat.lower() == 'companion':
            # Initialize companion stats (type can be set later)
            from world.wod20th.utils.companion_utils import initialize_companion_stats
            initialize_companion_stats(self.caller, '')

        # Initialize basic stats from the database
        from world.wod20th.utils.stat_initialization import initialize_basic_stats
        initialize_basic_stats()

        # Set initialized flag
        self.caller.db.stats['initialized'] = True

        return self.caller.db.stats

    def update_banality(self, character):
        """Update Banality based on character's current stats."""
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        if not splat:
            return

        # Calculate new Banality value
        banality = get_default_banality(
            splat,
            character.get_stat('identity', 'lineage', 'Type', temp=False),
            character.get_stat('identity', 'lineage', 'Affiliation', temp=False),
            character.get_stat('identity', 'lineage', 'Tradition', temp=False) if character.get_stat('identity', 'lineage', 'Affiliation', temp=False) == 'Traditions' else None,
            character.get_stat('identity', 'lineage', 'Convention', temp=False) if character.get_stat('identity', 'lineage', 'Affiliation', temp=False) == 'Technocracy' else None,
            character.get_stat('identity', 'lineage', 'Nephandi Faction', temp=False) if character.get_stat('identity', 'lineage', 'Affiliation', temp=False) == 'Nephandi' else None
        )
        
        # Only update if the value has changed
        if character.get_stat('pools', 'dual', 'Banality', temp=False) != banality:
            character.set_stat('pools', 'dual', 'Banality', banality, temp=False)
            character.set_stat('pools', 'dual', 'Banality', banality, temp=True)
            self.caller.msg(f"Your Banality has been updated to {banality} based on your character type.")

    def update_companion_pools(self, character):
        """Update pools based on Companion powers."""
        if character.get_stat('other', 'splat', 'Splat', temp=False) != 'Companion':
            return

        # Update Rage based on Ferocity
        if ferocity := character.get_stat('powers', 'special_advantage', 'Ferocity', temp=False):
            rage_value = min(5, ferocity // 2)
            character.set_stat('pools', 'dual', 'Rage', rage_value, temp=False)
            character.set_stat('pools', 'dual', 'Rage', rage_value, temp=True)

        # Update Essence for Familiar type
        if character.get_stat('identity', 'lineage', 'Type', temp=False).lower() == 'familiar':
            character.set_stat('pools', 'dual', 'Essence', 10, temp=False)
            character.set_stat('pools', 'dual', 'Essence', 10, temp=True)

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

    def parse(self):
        """Parse the arguments."""
        super().parse()

        if not self.args:
            self.caller.msg("Usage: +selfstat <stat>[/<type>]=<value>")
            return

        if "specialty" in self.switches:
            self.is_specialty = True
            try:
                if '=' not in self.args:
                    self.caller.msg("Usage: +selfstat/specialty <stat>=<specialty>")
                    return
                self.stat_name, self.specialty = [part.strip() for part in self.args.split('=', 1)]
                # Handle empty specialty for removal
                if not self.specialty:
                    self.is_removal = True
                else:
                    self.is_removal = False
            except ValueError:
                self.stat_name = self.specialty = None
            return

        # Regular stat parsing
        self.is_specialty = False
        try:
            if '=' not in self.args:
                self.caller.msg("Usage: +selfstat <stat>[/<type>]=<value>")
                self.stat_name = self.value_change = self.instance = None
                return
                
            # Split on the last occurrence of '=' to handle stat names with '=' in them
            stat_part, self.value_change = self.args.rsplit('=', 1)
            stat_part = stat_part.strip()
            self.value_change = self.value_change.strip()
            
            # Set removal flag if value is empty
            self.is_removal = not bool(self.value_change)

            # Handle both prefix format (category: name) and type format (name/type)
            if ":" in stat_part:
                category_prefix, stat_name = stat_part.split(":", 1)
                category_prefix = category_prefix.strip().lower()
                self.stat_name = stat_name.strip()
                
                # Special handling for disciplines
                if category_prefix == 'discipline':
                    self.stat_type = 'discipline'
                    self.category = 'powers'
                else:
                    # Let detect_stat_category handle the category and type
                    self.category = None
                    self.stat_type = None
                
            elif "/" in stat_part:
                # Keep the old format for backward compatibility
                self.stat_name, self.stat_type = stat_part.split("/", 1)
                self.stat_name = self.stat_name.strip()
                self.stat_type = self.stat_type.strip().lower()
                
                # Special handling for disciplines
                if self.stat_type == 'discipline':
                    self.category = 'powers'
                else:
                    # Let detect_stat_category handle the category and type
                    self.category = None
                
            else:
                self.stat_name = stat_part
                self.stat_type = None
                self.category = None
            
            # Check for instance in parentheses
            if self.stat_name:  # Only check for instance if we have a stat name
                instance_match = re.match(r"(.*?)\((.*?)\)", self.stat_name)
                if instance_match:
                    self.stat_name = instance_match.group(1).strip()
                    self.instance = instance_match.group(2).strip()
                else:
                    self.instance = None

            # Let detect_stat_category determine the category and type if not already set
            if self.stat_name and not (self.category and self.stat_type):
                stat_info = self.detect_stat_category(self.stat_name)
                if stat_info:
                    self.category, self.stat_type = stat_info
                else:
                    # Error message already shown by detect_stat_category
                    self.stat_name = self.value_change = self.instance = None
                    return
                    
        except ValueError as e:
            self.caller.msg(f"Error parsing command: {str(e)}")
            self.stat_name = self.value_change = self.instance = None

    def detect_stat_category(self, stat_name):
        """Detect the category and type for a stat."""
        possible_matches = []
        stat_name_lower = stat_name.lower()
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)

        # Handle Nature/Demeanor special cases first
        if stat_name_lower in ['nature', 'demeanor']:
            # For Changelings and Kinain, Nature and Demeanor are realms
            if splat and splat.lower() == 'changeling':
                return ('powers', 'realm')
            elif (splat and splat.lower() == 'mortal+' and 
                  self.caller.get_stat('identity', 'lineage', 'Type', temp=False) == 'Kinain'):
                return ('powers', 'realm')
            else:
                # For all other splats, Nature and Demeanor are personal archetypes
                return ('archetype', 'personal')

        # Handle Mage-specific stats
        if splat and splat.lower() == 'mage':
            if stat_name_lower == 'resonance':
                return ('pools', 'resonance')
            elif stat_name_lower in ['dynamic', 'static', 'entropic']:
                return ('virtues', 'synergy')
            elif stat_name_lower == 'essence':
                return ('identity', 'lineage')

        # Handle pools first since they're common across splats
        pool_stats = {
            'willpower': ('pools', 'dual'),
            'rage': ('pools', 'dual'),
            'gnosis': ('pools', 'dual'),
            'glamour': ('pools', 'dual'),
            'banality': ('pools', 'dual'),
            'nightmare': ('pools', 'other'),
            'blood': ('pools', 'dual'),
            'quintessence': ('pools', 'dual'),
            'paradox': ('pools', 'dual'),
            'road': ('pools', 'moral'),
            'arete': ('pools', 'advantage'),
            'enlightenment': ('pools', 'advantage'),
            'resonance': ('pools', 'resonance')  
        }
        if stat_name_lower in pool_stats:
            possible_matches.append((pool_stats[stat_name_lower], 'pool'))

        # Handle virtues including Mage synergy virtues
        virtue_stats = {
            'conscience': ('virtues', 'moral'),
            'conviction': ('virtues', 'moral'),
            'self-control': ('virtues', 'moral'),
            'instinct': ('virtues', 'moral'),
            'courage': ('virtues', 'moral'),
            'dynamic': ('virtues', 'synergy'),  
            'static': ('virtues', 'synergy'),
            'entropic': ('virtues', 'synergy')
        }
        if stat_name_lower in virtue_stats:
            possible_matches.append((virtue_stats[stat_name_lower], 'virtue'))

        # Handle special advantages for Companions first
        if self.caller.get_stat('other', 'splat', 'Splat', temp=False) == 'Companion':
            valid_advantages = {
                'acute smell': {'valid_values': [2, 3], 'desc': "Adds dice to Perception rolls involving scent"},
                'alacrity': {'valid_values': [2, 4, 6], 'desc': "Allows extra actions with Willpower expenditure"},
                'armor': {'valid_values': [1, 2, 3, 4, 5], 'desc': "Provides innate protection, each point adds one soak die"},
                'aura': {'valid_values': [3], 'desc': "Opponents suffer +3 difficulty on rolls against you"},
                'aww!': {'valid_values': [1, 2, 3, 4], 'desc': "Adds dice to Social rolls based on cuteness"},
                'bare necessities': {'valid_values': [1, 3], 'desc': "Retain items when shapeshifting"},
                'bioluminescence': {'valid_values': [1, 2, 3], 'desc': "Body can glow at will"},
                'blending': {'valid_values': [1], 'desc': "Can alter appearance to match surroundings"},
                'bond-sharing': {'valid_values': [4, 5, 6], 'desc': "Creates mystical bond to share abilities"},
                'cause insanity': {'valid_values': [2, 4, 6, 8, 10], 'desc': "Can provoke temporary fits of madness"},
                'chameleon coloration': {'valid_values': [4, 6, 8], 'desc': "Ability to change coloration for camouflage"},
                'claws, fangs, or horns': {'valid_values': [3, 5, 7], 'desc': "Natural weaponry that inflicts lethal damage"},
                'deadly demise': {'valid_values': [2, 4, 6], 'desc': "Upon death, inflicts damage to nearby enemies"},
                'dominance': {'valid_values': [1], 'desc': "Naturally commanding demeanor within specific groups"},
                'earthbond': {'valid_values': [2], 'desc': "Mystical connection to perceive threats"},
                'elemental touch': {'valid_values': [3, 5, 7, 10, 15], 'desc': "Control over a single element"},
                'empathic bond': {'valid_values': [2], 'desc': "Ability to sense and influence emotions"},
                'enhancement': {'valid_values': [5, 10, 15], 'desc': "Superior physical or mental attributes"},
                'extra heads': {'valid_values': [2, 4, 6, 8], 'desc': "Additional heads with perception bonuses"},
                'extra limbs': {'valid_values': [2, 4, 6, 8], 'desc': "Additional prehensile limbs"},
                'feast of nettles': {'valid_values': [2, 3, 4, 5, 6], 'desc': "Ability to absorb and nullify Paradox"},
                'ferocity': {'valid_values': [2, 4, 6, 8, 10], 'desc': "Grants Rage points equal to half rating"},
                'ghost form': {'valid_values': [8, 10], 'desc': "Become invisible or incorporeal"},
                'hibernation': {'valid_values': [2], 'desc': "Can enter voluntary hibernation state"},
                'human guise': {'valid_values': [1, 2, 3], 'desc': "Ability to appear human"},
                'immunity': {'valid_values': [2, 5, 10, 15], 'desc': "Immunity to specific harmful effects"},
                'mesmerism': {'valid_values': [3, 6], 'desc': "Hypnotic gaze abilities"},
                'musical influence': {'valid_values': [6], 'desc': "Affect emotions through music"},
                'musk': {'valid_values': [3], 'desc': "Emit powerful stench affecting rolls"},
                'mystic shield': {'valid_values': [2, 4, 6, 8, 10], 'desc': "Resistance to magic"},
                'needleteeth': {'valid_values': [3], 'desc': "Sharp teeth bypass armor"},
                'nightsight': {'valid_values': [3], 'desc': "Clear vision in low light conditions"},
                'omega status': {'valid_values': [4], 'desc': "Power in being overlooked"},
                'paradox nullification': {'valid_values': [2, 3, 4, 5, 6], 'desc': "Ability to consume Paradox energies"},
                'quills': {'valid_values': [2, 4], 'desc': "Sharp defensive spines"},
                'rapid healing': {'valid_values': [2, 4, 6, 8], 'desc': "Accelerated recovery from injuries"},
                'razorskin': {'valid_values': [3], 'desc': "Skin that shreds on contact"},
                'read and write': {'valid_values': [1], 'desc': "Ability to read and write human languages"},
                'regrowth': {'valid_values': [2, 4, 6], 'desc': "Regenerative capabilities"},
                'shapechanger': {'valid_values': [3, 5, 8], 'desc': "Ability to assume different forms"},
                'shared knowledge': {'valid_values': [5, 7], 'desc': "Mystic bond allowing shared understanding"},
                'size': {'valid_values': [3, 5, 8, 10], 'desc': "Significantly larger or smaller than human norm"},
                'soak lethal damage': {'valid_values': [3], 'desc': "Natural ability to soak lethal damage"},
                'soak aggravated damage': {'valid_values': [5], 'desc': "Can soak aggravated damage"},
                'soul-sense': {'valid_values': [2, 3], 'desc': "Ability to sense spirits and impending death"},
                'spirit travel': {'valid_values': [8, 10, 15], 'desc': "Ability to cross into Umbral realms"},
                'spirit vision': {'valid_values': [3], 'desc': "Ability to perceive the Penumbra"},
                'tunneling': {'valid_values': [3], 'desc': "Can create tunnels through earth"},
                'unaging': {'valid_values': [5], 'desc': "Immunity to natural aging process"},
                'universal translator': {'valid_values': [5], 'desc': "Ability to understand languages"},
                'venom': {'valid_values': [3, 6, 9, 12, 15], 'desc': "Poisonous attack capability"},
                'wall-crawling': {'valid_values': [4], 'desc': "Ability to climb sheer surfaces easily"},
                'water breathing': {'valid_values': [2, 5], 'desc': "Can breathe underwater"},
                'webbing': {'valid_values': [5], 'desc': "Can spin webs with various uses"},
                'wings': {'valid_values': [3, 5], 'desc': "Wings 3 grants Flight 2, Wings 5 grants Flight 4"}
            } 
            
            if stat_name_lower in valid_advantages:
                return ('powers', 'special_advantage')

        # Handle splat setting first
        if stat_name_lower == 'splat':
            valid_splats = ['Vampire', 'Mage', 'Changeling', 'Shifter', 'Mortal+', 'Possessed', 'Companion', 'Mortal']
            if self.value_change not in valid_splats:
                self.caller.msg(f"Error: Invalid splat. Must be one of: {', '.join(valid_splats)}")
                return None
            return ('other', 'splat')

        # Get splat and handle None or non-string values
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
        if not splat or not isinstance(splat, str):
            return None

        # Handle date-related stats first
        date_stats = {
            'date of birth': ('identity', 'personal'),
            'date of embrace': ('identity', 'personal'),
            'date of chrysalis': ('identity', 'personal'),
            'date of awakening': ('identity', 'personal'),
            'first change date': ('identity', 'personal'),
            'date of possession': ('identity', 'personal')
        }
        
        if stat_name_lower in date_stats:
            # Validate that the stat is appropriate for the character's splat
            valid_dates = {
                'vampire': ['date of birth', 'date of embrace'],
                'changeling': ['date of birth', 'date of chrysalis'],
                'mage': ['date of birth', 'date of awakening'],
                'shifter': ['date of birth', 'first change date'],
                'possessed': ['date of birth', 'date of possession'],
                'mortal+': ['date of birth'],
                'companion': ['date of birth'],
                'mortal': ['date of birth']
            }
            
            if splat.lower() in valid_dates and stat_name_lower in valid_dates[splat.lower()]:
                return date_stats[stat_name_lower]
            else:
                self.caller.msg(f"Error: {stat_name} is not a valid stat for {splat}.")
                return None

        # Special handling for Changeling stats
        if splat.lower() == 'changeling':
            # Get current kith for validation
            current_kith = self.caller.get_stat('identity', 'lineage', 'Kith', temp=False)

            # Handle Kith validation
            if stat_name_lower == 'kith':
                valid_kiths = ["Boggan", "Clurichan", "Eshu", "Nocker", "Piskey", "Pooka", 
                             "Redcap", "Satyr", "Selkie", "Autumn Sidhe", "Arcadian Sidhe", 
                             "Sluagh", "Troll", "Inanimae", "Hsien", "Nunnehi"]
                if self.value_change not in valid_kiths:
                    self.caller.msg(f"Error: Invalid Kith. Must be one of: {', '.join(valid_kiths)}")
                    return None
                return ('identity', 'lineage')

            # Handle Seeming validation (different for Nunnehi)
            elif stat_name_lower == 'seeming':
                if current_kith == 'Nunnehi':
                    valid_seemings = ["Youngling", "Brave", "Elder"]
                else:
                    valid_seemings = ["Childing", "Wilder", "Grump"]
                if self.value_change not in valid_seemings:
                    self.caller.msg(f"Error: Invalid Seeming. Must be one of: {', '.join(valid_seemings)}")
                    return None
                return ('identity', 'lineage')

            # Handle House validation
            elif stat_name_lower == 'house':
                valid_houses = ["Beaumayn", "Dougal", "Eiluned", "Fiona", "Gwydion", "Liam", 
                              "Scathach", "Aesin", "Ailil", "Balor", "Danaan", "Daireann", 
                              "Leanhaun", "Varich"]
                if self.value_change not in valid_houses:
                    self.caller.msg(f"Error: Invalid House. Must be one of: {', '.join(valid_houses)}")
                    return None
                return ('identity', 'lineage')

            # Handle Fae Court validation
            elif stat_name_lower == 'fae court':
                valid_courts = ["Seelie Court", "Unseelie Court", "Shadow Court"]
                if self.value_change not in valid_courts:
                    self.caller.msg(f"Error: Invalid Court. Must be one of: {', '.join(valid_courts)}")
                    return None
                return ('identity', 'lineage')

            # Handle Phyla (only for Inanimae)
            elif stat_name_lower == 'phyla':
                if current_kith != 'Inanimae':
                    self.caller.msg("Error: Only Inanimae can have a Phyla.")
                    return None
                valid_phyla = ["Kubera", "Glome", "Ondine", "Paroseme", "Solimond", "Mannikin"]
                if self.value_change not in valid_phyla:
                    self.caller.msg(f"Error: Invalid Phyla. Must be one of: {', '.join(valid_phyla)}")
                    return None
                return ('identity', 'phyla')

            # Handle Nunnehi-specific stats
            elif stat_name_lower in ['nunnehi camp', 'nunnehi seeming', 'nunnehi family', 'nunnehi totem']:
                if current_kith != 'Nunnehi':
                    self.caller.msg("Error: Only Nunnehi can have Nunnehi-specific stats.")
                    return None
                
                if stat_name_lower == 'nunnehi camp':
                    valid_camps = ["Winter People", "Summer People", "Midseason People"]
                    if self.value_change not in valid_camps:
                        self.caller.msg(f"Error: Invalid Nunnehi Camp. Must be one of: {', '.join(valid_camps)}")
                        return None
                elif stat_name_lower == 'nunnehi seeming':
                    valid_seemings = ["Youngling", "Brave", "Elder"]
                    if self.value_change not in valid_seemings:
                        self.caller.msg(f"Error: Invalid Nunnehi Seeming. Must be one of: {', '.join(valid_seemings)}")
                        return None
                elif stat_name_lower == 'nunnehi family':
                    valid_families = ["Canotili", "Inuas", "Kachinas", "May-may-gwya-shi", "Nanehi", 
                                    "Numuzo'ho", "Pu'gwis", "Rock giants", "Surems", "Thought-crafters", 
                                    "Tunghat", "Water babies", "Yunwi Amai'yine'hi", "Yunwi Tsundsi"]
                    if self.value_change not in valid_families:
                        self.caller.msg(f"Error: Invalid Nunnehi Family. Must be one of: {', '.join(valid_families)}")
                        return None
                # Nunnehi Totem has no validation as it's free-form
                return ('identity', 'lineage')

            # Handle Fae Name and Date of Chrysalis (free-form text fields)
            elif stat_name_lower in ['fae name', 'date of chrysalis']:
                return ('identity', 'personal')

            # Handle Seelie and Unseelie Legacies
            elif stat_name_lower == 'seelie legacy':
                if self.value_change not in SEELIE_LEGACIES:
                    self.caller.msg(f"Error: Invalid Seelie Legacy. Must be one of: {', '.join(SEELIE_LEGACIES)}")
                    return None
                return ('identity', 'legacy')
            elif stat_name_lower == 'unseelie legacy':
                if self.value_change not in UNSEELIE_LEGACIES:
                    self.caller.msg(f"Error: Invalid Unseelie Legacy. Must be one of: {', '.join(UNSEELIE_LEGACIES)}")
                    return None
                return ('identity', 'legacy')

        # Special handling for Type to route to appropriate type based on splat
        if stat_name_lower == 'type':
            if splat:
                splat_lower = splat.lower()
                if splat_lower == 'shifter':
                    # Validate Shifter Type
                    valid_types = dict(SHIFTER_TYPE_CHOICES)
                    if self.value_change.lower() not in valid_types:
                        self.caller.msg(f"Error: Invalid shifter type. Must be one of: {', '.join(valid_types.values())}")
                        return None
                    # Get the properly cased version
                    proper_type = valid_types[self.value_change.lower()]
                    self.value_change = proper_type
                    return ('identity', 'lineage')
                elif splat_lower == 'mortal+':
                    # Return category without validation (validation happens in func)
                    return ('identity', 'lineage')
                elif splat_lower == 'companion':
                    # Validate Companion Type
                    valid_types = ["Alien", "Animal", "Bygone", "Construct", "Familiar", 
                                 "Object", "Reanimate", "Robot", "Spirit"]
                    if self.value_change not in valid_types:
                        self.caller.msg(f"Error: Invalid companion type. Must be one of: {', '.join(valid_types)}")
                        return None
                    return ('identity', 'lineage')

        # Special handling for Gnosis
        if stat_name_lower == 'gnosis':
            # Check if character is a Kinfolk
            is_kinfolk = (splat == 'mortal+' and 
                         self.caller.get_stat('identity', 'lineage', 'Type', temp=False).lower() == 'kinfolk')
            
            if is_kinfolk:
                # For Kinfolk, Gnosis is a supernatural merit
                return ('merits', 'supernatural')
            else:
                # For everyone else, Gnosis is a dual pool
                return ('pools', 'dual')

        # Special handling for Arete/Enlightenment
        if stat_name_lower == 'arete' and splat == 'mage':
            return ('pools', 'advantage')
        if stat_name_lower == 'enlightenment' and splat == 'mage':
            return ('pools', 'advantage')

        # GIFTS FIRST UGH
        # Get all gifts first
        all_gifts = Stat.objects.filter(
            category='powers',
            stat_type='gift'
        ).values_list('name', flat=True)
        # Find closest match
        closest_match = None
        for gift_name in all_gifts:
            if gift_name.lower().startswith(stat_name_lower):
                closest_match = gift_name
                break
            elif stat_name_lower in gift_name.lower():
                closest_match = gift_name
                break
        
        if closest_match:
            # Set stat_type to 'gift' since we found one
            self.stat_type = 'gift'
            # Set the stat_name to the exact matched name
            self.stat_name = closest_match
            
            # Simple validation for splat and kinfolk
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            if splat.lower() == 'mortal+':
                # Check if they're Kinfolk
                char_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
                if char_type.lower() != 'kinfolk':
                    self.caller.msg("Only Shifters, Possessed, and Kinfolk can learn Gifts.")
                    return None
            elif splat.lower() not in ['shifter', 'possessed']:
                self.caller.msg("Only Shifters, Possessed, and Kinfolk can learn Gifts.")
                return None
            
            return ('powers', 'gift')

        # Handle abilities only if not explicitly looking for a Gift
        if not (self.stat_type and self.stat_type.lower() == 'gift'):
            ability_categories = {
                'talent': ['alertness', 'athletics', 'brawl', 'empathy', 'expression', 'intimidation', 'leadership', 'streetwise', 'subterfuge'],
                'skill': ['animal ken', 'crafts', 'drive', 'etiquette', 'firearms', 'melee', 'performance', 'security', 'stealth', 'survival'],
                'knowledge': ['academics', 'computer', 'enigmas', 'finance', 'investigation', 'law', 'medicine', 'occult', 'politics', 'science']
            }
            
            for ability_type, abilities in ability_categories.items():
                if stat_name_lower in abilities:
                    return ('abilities', ability_type)

        # Handle attributes
        attribute_categories = {
            'physical': ['strength', 'dexterity', 'stamina'],
            'social': ['charisma', 'manipulation', 'appearance'],
            'mental': ['perception', 'intelligence', 'wits']
        }
        
        for attr_type, attrs in attribute_categories.items():
            if stat_name_lower in attrs:
                return ('attributes', attr_type)

        # Special handling for Enlightenment based on splat
        if stat_name_lower == 'enlightenment':
            if splat == 'vampire':
                return ('identity', 'personal')
            elif splat == 'mage':
                return ('pools', 'advantage')
            elif splat == 'mortal+':
                return ('identity', 'personal')

        # Special handling for Essence based on splat and type
        if stat_name_lower == 'essence':
            if splat == 'mage':
                # For Mages, Essence is a lineage identity stat
                return ('identity', 'lineage')
            elif splat == 'companion':
                # For Companions, check if they are a Familiar
                companion_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
                if companion_type == 'Familiar':
                    # For Familiars, Essence is a dual pool
                    return ('pools', 'dual')
            # Default to not found if neither condition is met
            return None

        # Keep track of all possible matches
        possible_matches = []

        # Handle backgrounds first since they're common across splats
        # Check if the stat is a background
        if stat_name_lower in [bg.lower() for bg in UNIVERSAL_BACKGROUNDS]:
            return ('backgrounds', 'background')
        elif splat == 'vampire' and stat_name_lower in [bg.lower() for bg in VAMPIRE_BACKGROUNDS]:
            return ('backgrounds', 'background')
        elif splat == 'mage' and stat_name_lower in [bg.lower() for bg in MAGE_BACKGROUNDS]:
            return ('backgrounds', 'background')
        elif splat == 'changeling' and stat_name_lower in [bg.lower() for bg in CHANGELING_BACKGROUNDS]:
            return ('backgrounds', 'background')
        elif splat == 'shifter' and stat_name_lower in [bg.lower() for bg in SHIFTER_BACKGROUNDS]:
            return ('backgrounds', 'background')
        elif splat == 'mage':
            affiliation = self.caller.get_stat('identity', 'lineage', 'Affiliation', temp=False)
            if affiliation:
                affiliation = affiliation.lower()
                if affiliation == 'technocracy' and stat_name_lower in [bg.lower() for bg in TECHNOCRACY_BACKGROUNDS]:
                    return ('backgrounds', 'background')
                elif affiliation == 'traditions' and stat_name_lower in [bg.lower() for bg in TRADITIONS_BACKGROUNDS]:
                    return ('backgrounds', 'background')
                elif affiliation == 'nephandi' and stat_name_lower in [bg.lower() for bg in NEPHANDI_BACKGROUNDS]:
                    return ('backgrounds', 'background')

        # Try to find the stat in the database
        matching_stats = Stat.objects.filter(name__iexact=stat_name)
        if matching_stats.exists():
            for stat in matching_stats:
                if stat.category == 'backgrounds':
                    return ('backgrounds', 'background')
                elif stat.category == 'merits':
                    possible_matches.append((('merits', stat.stat_type), 'merit'))
                elif stat.category == 'flaws':
                    possible_matches.append((('flaws', stat.stat_type), 'flaw'))
                else:
                    category = STAT_TYPE_TO_CATEGORY.get(stat.stat_type)
                    if category:
                        possible_matches.append(((category, stat.stat_type), 'ability'))

        # Handle pools first since they're common across splats
        pool_stats = {
            'willpower': ('pools', 'dual'),
            'rage': ('pools', 'dual'),
            'gnosis': ('pools', 'dual'),
            'glamour': ('pools', 'dual'),
            'banality': ('pools', 'dual'),
            'nightmare': ('pools', 'other'),
            'blood': ('pools', 'dual'),
            'quintessence': ('pools', 'dual'),
            'paradox': ('pools', 'dual'),
            'road': ('pools', 'moral'),
            'arete': ('pools', 'advantage'),
            'essence': ('pools', 'dual'),
            'enlightenment': ('pools', 'advantage'),
            'resonance': ('pools', 'resonance')  
        }
        if stat_name_lower in pool_stats:
            possible_matches.append((pool_stats[stat_name_lower], 'pool'))

        # Handle virtues
        virtue_stats = {
            'conscience': ('virtues', 'moral'),
            'conviction': ('virtues', 'moral'),
            'self-control': ('virtues', 'moral'),
            'instinct': ('virtues', 'moral'),
            'courage': ('virtues', 'moral')
        }
        if stat_name_lower in virtue_stats:
            possible_matches.append((virtue_stats[stat_name_lower], 'virtue'))

        # Special case handling
        if stat_name_lower in ['nature']:
            # For Changelings and Kinain, Nature and Demeanor are realms
            if splat == 'changeling' or (splat == 'mortal+' and self.caller.get_stat('identity', 'lineage', 'Type', temp=False) == 'Kinain'):
                possible_matches = [((('powers', 'realm'), 'realm'))]
            else:
                # For all other splats, Nature and Demeanor are personal archetypes
                possible_matches = [((('archetype', 'personal'), 'personal'))]
            return possible_matches[0][0]
            
        if stat_name_lower == 'generation':
            if self.value_change and self.value_change.isdigit():
                possible_matches.append((('advantages', 'background'), 'background'))
            else:
                possible_matches.append((('identity', 'lineage'), 'identity'))

        # Check for splat-specific overrides
        if splat and splat in SPLAT_STAT_OVERRIDES:
            for stat, (stat_type, category) in SPLAT_STAT_OVERRIDES[splat].items():
                if stat_name_lower == stat.lower():
                    possible_matches.append(((category, stat_type), 'override'))

        # Check identity stats
        for stat_type, stats in IDENTITY_STATS.items():
            if stat_name in stats:
                possible_matches.append((('identity', stat_type), 'identity'))

        # Handle attributes
        attribute_categories = {
            'physical': ['strength', 'dexterity', 'stamina'],
            'social': ['charisma', 'manipulation', 'appearance'],
            'mental': ['perception', 'intelligence', 'wits']
        }
        
        for stat_type, stats in attribute_categories.items():
            if stat_name_lower in stats:
                possible_matches.append((('attributes', stat_type), 'attribute'))

        # Handle powers based on splat
        if splat:
            # Check for powers
            if splat == 'changeling':
                if stat_name_lower in {art.lower() for art in ARTS}:
                    possible_matches.append((('powers', 'art'), 'power'))
                if stat_name_lower in {realm.lower() for realm in REALMS}:
                    possible_matches.append((('powers', 'realm'), 'power'))
            elif splat == 'mage':
                # Create a mapping of lowercase sphere names to proper case
                sphere_mapping = {sphere.lower(): sphere for sphere in MAGE_SPHERES}
                if stat_name_lower in sphere_mapping:
                    # Store the proper case name for later use
                    self.stat_name = sphere_mapping[stat_name_lower]
                    possible_matches.append((('powers', 'sphere'), 'power'))
            elif splat == 'vampire':
                vampire_disciplines = {
                    'potence', 'obtenebration', 'obfuscate', 'fortitude', 'dominate', 
                    'presence', 'auspex', 'celerity', 'thaumaturgy', 'necromancy', 
                    'serpentis', 'protean', 'dementation', 'quietus', 'vicissitude', 
                    'chimerstry'
                }
                # Clean up the stat name by removing any prefixes
                clean_name = stat_name_lower
                for prefix in ['path:', 'ritual:', 'combo:', 'discipline:']:
                    if clean_name.startswith(prefix):
                        clean_name = clean_name.replace(prefix, '').strip()
                        break

                # Check if it's a discipline
                if clean_name in vampire_disciplines:
                    possible_matches.append((('powers', 'discipline'), 'power'))
                # Handle thaumaturgy paths
                elif self.stat_type == 'thaumaturgy' or stat_name_lower.startswith('path:'):
                    possible_matches.append((('powers', 'thaumaturgy'), 'power'))
                # Handle thaumaturgy rituals
                elif self.stat_type == 'thaum_ritual' or stat_name_lower.startswith('ritual:'):
                    possible_matches.append((('powers', 'thaum_ritual'), 'power'))
                # Handle combo disciplines
                elif self.stat_type == 'combodiscipline' or stat_name_lower.startswith('combo:'):
                    possible_matches.append((('powers', 'combodiscipline'), 'power'))
                # Check database for thaumaturgy paths and rituals
                else:
                    # Check if it's a thaumaturgy path
                    path_exists = Stat.objects.filter(
                        name__iexact=clean_name,
                        category='powers',
                        stat_type='thaumaturgy'
                    ).exists()
                    if path_exists:
                        possible_matches.append((('powers', 'thaumaturgy'), 'power'))
                        
                    # Check if it's a ritual
                    ritual_exists = Stat.objects.filter(
                        name__iexact=clean_name,
                        category='powers',
                        stat_type='thaum_ritual'
                    ).exists()
                    if ritual_exists:
                        possible_matches.append((('powers', 'thaum_ritual'), 'power'))
                        
                    # Check if it's a combo discipline
                    combo_exists = Stat.objects.filter(
                        name__iexact=clean_name,
                        category='powers',
                        stat_type='combodiscipline'
                    ).exists()
                    if combo_exists:
                        possible_matches.append((('powers', 'combodiscipline'), 'power'))
            elif splat == 'shifter':
                if stat_name_lower.startswith('gift:'):
                    possible_matches.append((('powers', 'gift'), 'power'))
                if stat_name_lower.startswith('rite:'):
                    possible_matches.append((('powers', 'rite'), 'power'))
            elif splat == 'possessed':
                # Handle blessings
                if stat_name_lower.startswith('blessing:') or (self.stat_type and self.stat_type.lower() == 'blessing'):
                    clean_name = stat_name_lower.replace('blessing:', '').strip()
                    blessing_exists = Stat.objects.filter(
                        name__iexact=clean_name,
                        category='powers',
                        stat_type='blessing'
                    ).exists()
                    if blessing_exists:
                        possible_matches.append((('powers', 'blessing'), 'power'))
                
                # Handle charms - first check if it's a direct charm name
                clean_name = stat_name_lower.strip()
                charm_exists = Stat.objects.filter(
                    name__iexact=clean_name,
                    category='powers',
                    stat_type='charm'
                ).exists()
                if charm_exists:
                    possible_matches.append((('powers', 'charm'), 'power'))
                # Then check if it's using the charm: prefix
                elif stat_name_lower.startswith('charm:') or (self.stat_type and self.stat_type.lower() == 'charm'):
                    clean_name = stat_name_lower.replace('charm:', '').strip()
                    charm_exists = Stat.objects.filter(
                        name__iexact=clean_name,
                        category='powers',
                        stat_type='charm'
                    ).exists()
                    if charm_exists:
                        possible_matches.append((('powers', 'charm'), 'power'))
                
                # Handle gifts (Possessed can learn gifts)
                if stat_name_lower.startswith('gift:') or (self.stat_type and self.stat_type.lower() == 'gift'):
                    clean_name = stat_name_lower.replace('gift:', '').strip()
                    gift_exists = Stat.objects.filter(
                        name__iexact=clean_name,
                        category='powers',
                        stat_type='gift'
                    ).exists()
                    if gift_exists:
                        possible_matches.append((('powers', 'gift'), 'power'))

        # If we have multiple matches and no stat_type specified, return None and provide guidance
        if len(possible_matches) > 1 and not self.stat_type:
            # Get unique combinations of category and type
            unique_types = {(match[0][0], match[0][1]) for match in possible_matches}
            
            # If all matches are for the same category/type combination, just use that
            if len(unique_types) == 1:
                return possible_matches[0][0]
                
            # Otherwise, show the ambiguity message
            stat_types = sorted(set(f"{match[0][1]}" for match in possible_matches))
            self.caller.msg(f"The stat '{stat_name}' is ambiguous. Please specify the type using: +selfstat {stat_name}/<type>=<value>")
            self.caller.msg(f"Possible types are: {', '.join(stat_types)}")
            return None
        
        # If we have exactly one match or a matching stat_type, return it
        if len(possible_matches) == 1:
            return possible_matches[0][0]
        elif self.stat_type:
            matching_types = [match[0] for match in possible_matches if match[0][1] == self.stat_type]
            if matching_types:
                return matching_types[0]
            else:
                self.caller.msg(f"Invalid stat type '{self.stat_type}' for stat '{stat_name}'.")
                stat_types = sorted(set(f"{match[0][1]}" for match in possible_matches))
                if stat_types:
                    self.caller.msg(f"Valid types are: {', '.join(stat_types)}")
                return None

    def validate_stat_exists(self, stat_name, category=None, stat_type=None):
        """
        Validate if a stat exists and suggest similar stats if it doesn't.
        Returns (exists, suggestions) tuple.
        """
        from world.wod20th.models import Stat
        
        # Build the query
        query = Stat.objects.all()
        if category:
            query = query.filter(category=category)
        if stat_type:
            query = query.filter(stat_type=stat_type)
            
        # Check for exact match
        if query.filter(name__iexact=stat_name).exists():
            return True, []
            
        # If no exact match, find similar stats
        all_stats = query.values_list('name', flat=True)
        similar_stats = []
        stat_lower = stat_name.lower()
        
        for existing_stat in all_stats:
            existing_lower = existing_stat.lower()
            # Check for substring matches
            if stat_lower in existing_lower or existing_lower in stat_lower:
                similar_stats.append(existing_stat)
            # Check for similar spellings (simple Levenshtein-like check)
            elif len(stat_lower) > 3 and sum(1 for a, b in zip(stat_lower[:len(existing_lower)], existing_lower[:len(stat_lower)]) if a != b) <= 2:
                similar_stats.append(existing_stat)
        
        # Build error message
        error_msg = f"|rThe stat '{stat_name}' doesn't exist in the system."
        if category and stat_type:
            error_msg += f" (looking in category: {category}, type: {stat_type})"
        elif category:
            error_msg += f" (looking in category: {category})"
        elif stat_type:
            error_msg += f" (looking in type: {stat_type})"
        error_msg += "|n"
        
        # Add suggestions if any were found
        if similar_stats:
            error_msg += f"\n|yDid you mean one of these?: {', '.join(similar_stats)}|n"
        
        return False, error_msg

    def func(self):
        """Execute the command."""
        if not self.args or not self.stat_name:
            return
            
        # Handle stat removal if value is empty
        if self.is_removal:
            if self.is_specialty:
                # Handle specialty removal
                self.caller.del_stat(self.category, self.stat_type, self.stat_name.title(), 
                                   temp=False, specialty=True)
                self.caller.del_stat(self.category, self.stat_type, self.stat_name.title(), 
                                   temp=True, specialty=True)
                self.caller.msg(f"Removed specialty for {self.stat_name.title()}.")
            else:
                # Handle regular stat removal
                self.caller.del_stat(self.category, self.stat_type, self.stat_name.title(), temp=False)
                self.caller.del_stat(self.category, self.stat_type, self.stat_name.title(), temp=True)
                self.caller.msg(f"Removed {self.stat_name.title()}.")
            return

        if not self.args:
            self.caller.msg("Usage: +selfstat <stat>[/<type>]=<value>")
            return

        # Get character's splat
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)

        # Validate Resonance and Synergy for Mages
        if splat and splat.lower() == 'mage':
            if self.stat_name.lower() == 'resonance':
                try:
                    value = int(self.value_change)
                    if value < 0 or value > 5:
                        self.caller.msg("Error: Resonance must be between 0 and 5.")
                        return
                except ValueError:
                    self.caller.msg("Error: Resonance must be a number.")
                    return

            if self.stat_name.lower() in ['dynamic', 'static', 'entropic']:
                try:
                    value = int(self.value_change)
                    if value < 0 or value > 5:
                        self.caller.msg("Error: Synergy must be between 0 and 5.")
                        return
                except ValueError:
                    self.caller.msg("Error: Synergy must be a number.")
                    return
        # Parse the input first
        stat_name = self.lhs.strip() if self.lhs else None
        new_value = self.rhs.strip() if self.rhs else None

        # Early return if we don't have both stat name and value
        if not stat_name or new_value is None:
            self.caller.msg("Usage: +selfstat <stat>=<value>")
            return

        # Get category and type if not already set
        if not (self.category and self.stat_type):
            stat_info = self.detect_stat_category(stat_name)
            if not stat_info:
                # Check if the stat exists at all before giving up
                exists, message = self.validate_stat_exists(stat_name)
                if not exists:
                    self.caller.msg(message)
                return
            self.category, self.stat_type = stat_info

        # Handle setting the gift if that's what we detected
        if self.category == 'powers' and self.stat_type == 'gift':
            try:
                value = int(self.value_change)
                if value < 0 or value > 5:
                    self.caller.msg("Gift rating must be between 0 and 5.")
                    return
                self.caller.set_stat('powers', 'gift', self.stat_name, value, temp=False)
                self.caller.set_stat('powers', 'gift', self.stat_name, value, temp=True)
                self.caller.msg(f"Set Gift: {self.stat_name} to {value}")
                return
            except ValueError:
                self.caller.msg("Gift rating must be a number between 0 and 5.")
                return

        # Validate that the stat exists in the specified category/type
        exists, message = self.validate_stat_exists(stat_name, self.category, self.stat_type)
        if not exists:
            self.caller.msg(message)
            return

        # Special handling for Changeling stats
        if self.caller.get_stat('other', 'splat', 'Splat', temp=False) == 'Changeling':
            stat_name_lower = stat_name.lower()
            
            # Handle Fae Name and Date of Chrysalis
            if stat_name_lower in ['fae name', 'date of chrysalis']:
                self.caller.set_stat('identity', 'personal', stat_name.title(), new_value, temp=False)
                self.caller.set_stat('identity', 'personal', stat_name.title(), new_value, temp=True)
                self.caller.msg(f"Set {stat_name.title()} to {new_value}.")
                
                # Send any pending messages that were stored during validation
                if hasattr(self, 'pending_messages') and self.pending_messages:
                    for msg in self.pending_messages:
                        self.caller.msg(msg)
                    # Clear the messages after sending
                    self.pending_messages = []
                return

            # Handle Fae Court
            elif stat_name_lower == 'fae court':
                valid_courts = ["Seelie Court", "Unseelie Court", "Shadow Court"]
                if new_value not in valid_courts:
                    self.caller.msg(f"Error: Invalid Court. Must be one of: {', '.join(valid_courts)}")
                    return
                self.caller.set_stat('identity', 'lineage', 'Fae Court', new_value, temp=False)
                self.caller.set_stat('identity', 'lineage', 'Fae Court', new_value, temp=True)
                self.caller.msg(f"Set Fae Court to {new_value}.")
                
                # Send any pending messages that were stored during validation
                if hasattr(self, 'pending_messages') and self.pending_messages:
                    for msg in self.pending_messages:
                        self.caller.msg(msg)
                    # Clear the messages after sending
                    self.pending_messages = []
                return

            # Handle Nunnehi-specific stats
            elif stat_name_lower in ['nunnehi seeming', 'nunnehi camp', 'nunnehi family', 'nunnehi totem']:
                current_kith = self.caller.get_stat('identity', 'lineage', 'Kith', temp=False)
                if current_kith != 'Nunnehi':
                    self.caller.msg("Error: Only Nunnehi can have Nunnehi-specific stats.")
                    return

                if stat_name_lower == 'nunnehi seeming':
                    valid_seemings = ["Youngling", "Brave", "Elder"]
                    if new_value not in valid_seemings:
                        self.caller.msg(f"Error: Invalid Nunnehi Seeming. Must be one of: {', '.join(valid_seemings)}")
                        return
                elif stat_name_lower == 'nunnehi camp':
                    valid_camps = ["Winter People", "Summer People", "Midseason People"]
                    if new_value not in valid_camps:
                        self.caller.msg(f"Error: Invalid Nunnehi Camp. Must be one of: {', '.join(valid_camps)}")
                        return
                elif stat_name_lower == 'nunnehi family':
                    valid_families = ["Canotili", "Inuas", "Kachinas", "May-may-gwya-shi", "Nanehi", 
                                    "Numuzo'ho", "Pu'gwis", "Rock giants", "Surems", "Thought-crafters", 
                                    "Tunghat", "Water babies", "Yunwi Amai'yine'hi", "Yunwi Tsundsi"]
                    if new_value not in valid_families:
                        self.caller.msg(f"Error: Invalid Nunnehi Family. Must be one of: {', '.join(valid_families)}")
                        return

                self.caller.set_stat('identity', 'lineage', stat_name.title(), new_value, temp=False)
                self.caller.set_stat('identity', 'lineage', stat_name.title(), new_value, temp=True)
                self.caller.msg(f"Set {stat_name.title()} to {new_value}.")
                
                # Send any pending messages that were stored during validation
                if hasattr(self, 'pending_messages') and self.pending_messages:
                    for msg in self.pending_messages:
                        self.caller.msg(msg)
                    # Clear the messages after sending
                    self.pending_messages = []

                # If this is a Mokole stream, send the stream info immediately
                if (stat_name.lower() == 'stream' and 
                    self.caller.get_stat('identity', 'lineage', 'Type', temp=False) == 'Mokole'):
                    stream_info = {
                        "gumagan": {
                            "desc": "Rainbow Serpent dreamers of the islands",
                            "region": "Australia and Pacific Islands"
                        },
                        "mokole-mbembe": {
                            "desc": "Ancient guardians of African waters",
                            "region": "Africa"
                        },
                        "zhong lung": {
                            "desc": "Dragon-kings of Asian tradition",
                            "region": "Asia"
                        },
                        "makara": {
                            "desc": "Sacred crocodiles of ancient rivers",
                            "region": "India and Southeast Asia"
                        }
                    }
                    
                    stream_lower = new_value.lower()
                    if stream_lower in stream_info:
                        info = stream_info[stream_lower]
                        self.caller.msg(f"|y{new_value}: {info['desc']} (Region: {info['region']})|n")
                    
                    breed = self.caller.get_stat('identity', 'lineage', 'Breed', temp=False)
                    if breed and breed.lower() == "homid":
                        self.caller.msg("|bGame:|n|r Warning: Homid Mokole are extremely rare.|n")
                        if new_value == "Zhong Lung":
                            self.caller.msg("|bGame:|n|y Note: Zhong Lung are slightly more accepting of Homid breed.|n")

                return

        # Special handling for Changeling legacies
        if self.category == 'identity' and self.stat_type == 'legacy':
            # Set the legacy value
            self.caller.set_stat('identity', 'legacy', stat_name.title(), new_value, temp=False)
            self.caller.set_stat('identity', 'legacy', stat_name.title(), new_value, temp=True)
            self.caller.msg(f"Set {stat_name.title()} to {new_value}.")
            
            # Send any pending messages that were stored during validation
            if hasattr(self, 'pending_messages') and self.pending_messages:
                for msg in self.pending_messages:
                    self.caller.msg(msg)
                # Clear the messages after sending
                self.pending_messages = []
            return

        # Special handling for splat initialization - handle this first
        if stat_name.lower() == 'splat':
            # Validate splat type
            valid_splats = ['changeling', 'vampire', 'shifter', 'companion', 'mage', 'mortal', 'mortal+', 'possessed']
            if new_value.lower() not in [s.lower() for s in valid_splats]:
                splat_list = "\n".join([f"  - splat={s}" for s in valid_splats])
                self.caller.msg(f"Error: Invalid splat type '{new_value}'. Must be one of:\n{splat_list}")
                return
                
            # Initialize the stats structure based on splat
            self.initialize_stats(new_value)
            self.caller.msg(f"Successfully initialized character as a {new_value}.")
            
            # Get and set default banality
            new_banality = get_default_banality(new_value)
            self.caller.msg(f"|yBanality set to {new_banality} based on your splat type.|n")
            return

        # Handle renown setting
        if self.category == 'advantages' and self.stat_type == 'renown':
            try:
                value = int(new_value)
                if value < 0 or value > 10:
                    self.caller.msg("Renown must be between 0 and 10.")
                    return
                
                # Get shifter type and valid renown
                shifter_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
                from world.wod20th.utils.shifter_utils import SHIFTER_RENOWN
                valid_renown = SHIFTER_RENOWN.get(shifter_type, [])
                
                # Check if this is a valid renown type for this shifter
                if stat_name.title() not in valid_renown:
                    self.caller.msg(f"Error: {stat_name.title()} is not a valid Renown type for {shifter_type}. Valid types are: {', '.join(valid_renown)}")
                    return
                
                # Ensure the renown category exists
                if 'advantages' not in self.caller.db.stats:
                    self.caller.db.stats['advantages'] = {}
                if 'renown' not in self.caller.db.stats['advantages']:
                    self.caller.db.stats['advantages']['renown'] = {}
                
                # Set the permanent renown value
                self.caller.set_stat('advantages', 'renown', stat_name.title(), value, temp=False)
                
                # Initialize temporary value at 0 if it doesn't exist
                temp_value = self.caller.get_stat('advantages', 'renown', stat_name.title(), temp=True)
                if temp_value is None:
                    self.caller.set_stat('advantages', 'renown', stat_name.title(), 0, temp=True)
                
                self.caller.msg(f"Set permanent {stat_name.title()} Renown to {value}. Temporary Renown can be set with +selfstat temp_{stat_name}=<value>")
                return
            except ValueError:
                self.caller.msg("Renown value must be a number between 0 and 10.")
                return

        # Handle temporary renown setting
        if stat_name.lower().startswith('temp_') and self.category == 'advantages' and self.stat_type == 'renown':
            try:
                value = int(new_value)
                if value < 0:
                    self.caller.msg("Temporary Renown cannot be negative.")
                    return
                
                # Get the actual renown name without the temp_ prefix
                actual_renown = stat_name[5:].title()
                
                # Get shifter type and valid renown
                shifter_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
                from world.wod20th.utils.shifter_utils import SHIFTER_RENOWN
                valid_renown = SHIFTER_RENOWN.get(shifter_type, [])
                
                # Check if this is a valid renown type for this shifter
                if actual_renown not in valid_renown:
                    self.caller.msg(f"Error: {actual_renown} is not a valid Renown type for {shifter_type}. Valid types are: {', '.join(valid_renown)}")
                    return
                
                # Set the temporary renown value
                self.caller.set_stat('advantages', 'renown', actual_renown, value, temp=True)
                self.caller.msg(f"Set temporary {actual_renown} Renown to {value}.")
                return
            except ValueError:
                self.caller.msg("Temporary Renown value must be a number.")
                return

        # Try to handle as a special advantage
        success, message = self.validate_special_advantage(stat_name, new_value)
        if success:
            self.caller.msg(message)
            return
        elif "Invalid special advantage" not in message and "Only Companions" not in message:
            self.caller.msg(message)
            return

        # Validate stat exists (before the value validation)
        exists, suggestions = self.validate_stat_exists(stat_name, self.category, self.stat_type)
        if not exists:
            suggestion_msg = f"\nDid you mean one of these: {', '.join(suggestions)}" if suggestions else ""
            self.caller.msg(f"Error: Stat '{stat_name}' doesn't exist.{suggestion_msg}")
            return

        # Get allowed values for validation
        allowed_values = self.get_allowed_values(self.stat_name, self.caller)
        if allowed_values:
            is_valid, message = self.validate_stat_value(self.stat_name, self.value_change, allowed_values)
            if not is_valid:
                self.caller.msg(message)
                return
            self.value_change = message  # Use the properly cased version

        # Handle special cases based on what's being set
        if self.stat_name.lower() == 'companion type':
            self.initialize_companion_type(self.caller, self.value_change)
        elif self.stat_name.lower() == 'type':
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            if splat.lower() == 'shifter':
                self.initialize_shifter_type(self.caller, self.value_change)
            elif splat.lower() == 'mortal+':
                self.initialize_mortalplus_pools(self.caller, self.value_change)

        # Handle special advantages
        if self.category == 'powers' and self.stat_type == 'special_advantage':
            self.handle_special_advantages(self.caller, self.stat_name, self.value_change)

        # Handle stat removal (empty value)
        if self.value_change == '':
            # Get the category and type
            if not (self.category and self.stat_type):
                stat_info = self.detect_stat_category(self.stat_name)
                if not stat_info:
                    return
                self.category, self.stat_type = stat_info

            # Special handling for Nature
            if stat_name.lower() in ['nature']:
                splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
                if splat and splat.lower() == 'changeling':
                    self.caller.set_stat('powers', 'realm', stat_name.title(), '', temp=False)
                    self.caller.set_stat('powers', 'realm', stat_name.title(), '', temp=True)
                elif splat and splat.lower() == 'mortal+' and self.caller.get_stat('identity', 'lineage', 'Type', temp=False) == 'Kinain':
                    self.caller.set_stat('powers', 'realm', stat_name.title(), '', temp=False)
                    self.caller.set_stat('powers', 'realm', stat_name.title(), '', temp=True)
                else:
                    self.caller.set_stat('archetype', 'personal', stat_name.title(), '', temp=False)
                    self.caller.set_stat('archetype', 'personal', stat_name.title(), '', temp=True)
                self.caller.msg(f"Removed {stat_name.title()}.")
                return

            # Remove the stat
            self.caller.set_stat(self.category, self.stat_type, self.stat_name.title(), '', temp=False)
            self.caller.set_stat(self.category, self.stat_type, self.stat_name.title(), '', temp=True)
            self.caller.msg(f"Removed {self.stat_name.title()}.")
            return

        # Special handling for Nature and Demeanor
        if stat_name.lower() in ['nature', 'demeanor']:
            if self.handle_special_cases(stat_name, new_value):
                self.caller.msg(f"Set {stat_name.title()} to {new_value}.")
            return

        # Special handling for Essence
        if stat_name.lower() == 'essence':
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            if splat == 'mage':
                # For Mages, Essence is a lineage identity stat with specific valid values
                valid_essence = ['Questing', 'Dynamic', 'Static', 'Primordial']
                if new_value not in valid_essence:
                    self.caller.msg(f"Invalid Essence type. Must be one of: {', '.join(valid_essence)}")
                    return
                self.caller.set_stat('identity', 'lineage', 'Essence', new_value, temp=False)
                self.caller.set_stat('identity', 'lineage', 'Essence', new_value, temp=True)
                return
            elif splat == 'companion':
                companion_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
                if companion_type == 'Familiar':
                    # For Familiars, Essence is a dual pool with numeric values
                    try:
                        value = int(new_value)
                        if value < 0 or value > 20:
                            self.caller.msg("Essence must be between 0 and 20.")
                            return
                        self.caller.set_stat('pools', 'dual', 'Essence', value, temp=False)
                        self.caller.set_stat('pools', 'dual', 'Essence', value, temp=True)
                        return
                    except ValueError:
                        self.caller.msg("Essence value must be a number between 0 and 20.")
                        return

        # Special handling for affiliation (mainly for mages)
        if stat_name.lower() == 'affiliation':
            # Set the affiliation
            self.caller.set_stat('identity', 'lineage', 'Affiliation', new_value, temp=False)
            self.caller.set_stat('identity', 'lineage', 'Affiliation', new_value, temp=True)
            self.caller.msg(f"Set Affiliation to {new_value}.")
            
            # Update banality based on new affiliation
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            new_banality = get_default_banality(
                splat, 
                affiliation=new_value,
                tradition=self.caller.get_stat('identity', 'lineage', 'Tradition', temp=False),
                convention=self.caller.get_stat('identity', 'lineage', 'Convention', temp=False),
                nephandi_faction=self.caller.get_stat('identity', 'lineage', 'Nephandi Faction', temp=False)
            )
            self.caller.set_stat('pools', 'dual', 'Banality', new_banality, temp=False)
            self.caller.set_stat('pools', 'dual', 'Banality', new_banality, temp=True)
            self.caller.msg(f"|yBanality adjusted to {new_banality} based on your affiliation.|n")
            return

        # Special handling for Type to ensure it's set in identity/lineage
        stat_name_lower = stat_name.lower()
        if stat_name_lower == 'type':
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            if splat:
                splat_lower = splat.lower()
                if splat_lower == 'shifter':
                    # Validate and set Shifter Type
                    valid_types = dict(SHIFTER_TYPE_CHOICES)
                    if new_value.lower() not in valid_types:
                        self.caller.msg(f"Error: Invalid shifter type. Must be one of: {', '.join(valid_types.values())}")
                        return
                    # Get the properly cased version
                    proper_type = valid_types[new_value.lower()]
                    # Store current Willpower values
                    willpower_perm = self.caller.get_stat('pools', 'dual', 'Willpower', temp=False)
                    willpower_temp = self.caller.get_stat('pools', 'dual', 'Willpower', temp=True)
                    # Set the type and initialize
                    self.caller.set_stat('identity', 'lineage', 'Type', proper_type, temp=False)
                    self.caller.set_stat('identity', 'lineage', 'Type', proper_type, temp=True)
                    self.initialize_shifter_type(self.caller, proper_type)
                    # Restore Willpower values
                    self.caller.set_stat('pools', 'dual', 'Willpower', willpower_perm, temp=False)
                    self.caller.set_stat('pools', 'dual', 'Willpower', willpower_temp, temp=True)
                    self.caller.msg(f"Set Shifter Type to {proper_type}.")
                    if proper_type == 'Ananasi':
                        self.caller.msg("Set Blood Pool to 10 for Ananasi.")
                    return
                elif splat_lower == 'mortal+':
                    # Validate and set Mortal+ Type
                    if new_value not in VALID_MORTALPLUS_TYPES:
                        self.caller.msg(f"Error: Invalid mortal+ type. Must be one of: {', '.join(VALID_MORTALPLUS_TYPES)}")
                        return
                    # Store current Willpower values
                    willpower_perm = self.caller.get_stat('pools', 'dual', 'Willpower', temp=False)
                    willpower_temp = self.caller.get_stat('pools', 'dual', 'Willpower', temp=True)
                    # Set the type and initialize
                    self.caller.set_stat('identity', 'lineage', 'Type', new_value, temp=False)
                    self.caller.set_stat('identity', 'lineage', 'Type', new_value, temp=True)
                    self.initialize_mortalplus_pools(self.caller, new_value)
                    # Restore Willpower values
                    self.caller.set_stat('pools', 'dual', 'Willpower', willpower_perm, temp=False)
                    self.caller.set_stat('pools', 'dual', 'Willpower', willpower_temp, temp=True)
                    self.caller.msg(f"Set Mortal+ Type to {new_value}.")
                    return
                elif splat_lower == 'companion':
                    # Validate and set Companion Type
                    valid_types = ["Alien", "Animal", "Bygone", "Construct", "Familiar", 
                                 "Object", "Reanimate", "Robot", "Spirit"]
                    if new_value not in valid_types:
                        self.caller.msg(f"Error: Invalid companion type. Must be one of: {', '.join(valid_types)}")
                        return
                    # Store current Willpower values
                    willpower_perm = self.caller.get_stat('pools', 'dual', 'Willpower', temp=False)
                    willpower_temp = self.caller.get_stat('pools', 'dual', 'Willpower', temp=True)
                    # Set the type and initialize
                    self.caller.set_stat('identity', 'lineage', 'Companion Type', new_value, temp=False)
                    self.caller.set_stat('identity', 'lineage', 'Companion Type', new_value, temp=True)
                    self.initialize_companion_type(self.caller, new_value)
                    # Restore Willpower values
                    self.caller.set_stat('pools', 'dual', 'Willpower', willpower_perm, temp=False)
                    self.caller.set_stat('pools', 'dual', 'Willpower', willpower_temp, temp=True)
                    self.caller.msg(f"Set Companion Type to {new_value}.")
                    return
                elif splat_lower == 'possessed':
                    # Validate and set Possessed Type
                    if new_value not in VALID_POSSESSED_TYPES:
                        self.caller.msg(f"Error: Invalid possessed type. Must be one of: {', '.join(VALID_POSSESSED_TYPES)}")
                        return
                    # Store current Willpower values
                    willpower_perm = self.caller.get_stat('pools', 'dual', 'Willpower', temp=False)
                    willpower_temp = self.caller.get_stat('pools', 'dual', 'Willpower', temp=True)
                    # Set the type and initialize
                    self.caller.set_stat('identity', 'lineage', 'Possessed Type', new_value, temp=False)
                    self.caller.set_stat('identity', 'lineage', 'Possessed Type', new_value, temp=True)
                    from world.wod20th.utils.possessed_utils import initialize_possessed_stats
                    initialize_possessed_stats(self.caller, new_value)
                    # Update banality based on new type
                    new_banality = get_default_banality(splat, subtype=new_value)
                    self.caller.set_stat('pools', 'dual', 'Banality', new_banality, temp=False)
                    self.caller.set_stat('pools', 'dual', 'Banality', new_banality, temp=True)
                    # Restore Willpower values
                    self.caller.set_stat('pools', 'dual', 'Willpower', willpower_perm, temp=False)
                    self.caller.set_stat('pools', 'dual', 'Willpower', willpower_temp, temp=True)
                    self.caller.msg(f"|ySet Possessed Type to {new_value} and adjusted Banality to {new_banality}.|n")
                    return

            # Set Type in identity/lineage for all other cases
            self.caller.set_stat('identity', 'lineage', 'Type', new_value, temp=False)
            self.caller.set_stat('identity', 'lineage', 'Type', new_value, temp=True)
            self.caller.msg(f"Set Type to {new_value}.")
            
        # Handle Possessed Type setting
        if stat_name_lower in ['possessed type', 'type'] and self.caller.get_stat('other', 'splat', 'Splat', temp=False) == 'Possessed':
            # Validate the type
            valid_types = ['Fomori', 'Kami']  # Define valid types with proper casing
            new_value_title = new_value.title()  # Convert to title case for consistency
            
            if new_value_title not in valid_types:
                self.caller.msg(f"Error: Invalid possessed type. Must be one of: {', '.join(valid_types).lower()}")
                return
            
            # Set the type
            self.caller.set_stat('identity', 'lineage', 'Type', new_value_title, temp=False)
            self.caller.set_stat('identity', 'lineage', 'Type', new_value_title, temp=True)
            
            # Initialize type-specific stats
            from world.wod20th.utils.possessed_utils import initialize_possessed_stats
            initialize_possessed_stats(self.caller, new_value_title)
            
            # Update banality based on new type
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            new_banality = get_default_banality(splat, subtype=new_value_title)
            self.caller.set_stat('pools', 'dual', 'Banality', new_banality, temp=False)
            self.caller.set_stat('pools', 'dual', 'Banality', new_banality, temp=True)
            
            self.caller.msg(f"|ySet Possessed Type to {new_value_title} and adjusted Banality to {new_banality}.|n")
            return

    def calculate_road(self, character):
        """Calculate Road value based on virtues."""
        enlightenment = character.get_stat('identity', 'personal', 'Enlightenment', temp=False)
        virtues = character.db.stats.get('virtues', {}).get('moral', {})

        path_virtues = {
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

        if enlightenment in path_virtues:
            virtue1, virtue2 = path_virtues[enlightenment]
            value1 = virtues.get(virtue1, {}).get('perm', 0)
            value2 = virtues.get(virtue2, {}).get('perm', 0)
            return value1 + value2
        else:
            # Default to Humanity if no enlightenment is set
            value1 = virtues.get('Conscience', {}).get('perm', 0)
            value2 = virtues.get('Self-Control', {}).get('perm', 0)
            return value1 + value2

    def handle_special_cases(self, stat_name, new_value):
        """Handle special cases and updates for the given stat."""
        stat_name_lower = stat_name.lower()
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)

        # Handle Mage-specific stats
        if splat and splat.lower() == 'mage':
            if stat_name_lower == 'resonance':
                try:
                    value = int(new_value)
                    if value < 0 or value > 5:
                        self.caller.msg("|rResonance must be between 0 and 5.|n")
                        return False
                    self.caller.set_stat('pools', 'resonance', 'Resonance', value, temp=False)
                    self.caller.set_stat('pools', 'resonance', 'Resonance', value, temp=True)
                    self.caller.msg(f"|yThis represents your magical signature's strength.|n")
                    return True
                except ValueError:
                    self.caller.msg("|rResonance value must be a number between 0 and 5.|n")
                    return False

            if stat_name_lower in ['dynamic', 'static', 'entropic']:
                try:
                    value = int(new_value)
                    if value < 0 or value > 5:
                        self.caller.msg(f"{stat_name} must be between 0 and 5.")
                        return False
                    self.caller.set_stat('virtues', 'synergy', stat_name.title(), value, temp=False)
                    self.caller.set_stat('virtues', 'synergy', stat_name.title(), value, temp=True)
                    virtue_desc = {
                        'dynamic': "Dynamic synergy represents your connection to universal forces of change and motion",
                        'static': "Static synergy represents your connection to universal forces of stability and order",
                        'entropic': "Entropic synergy represents your connection to universal forces of decay and chaos"
                    }
                    self.caller.msg(f"|y{virtue_desc[stat_name_lower]}|n")
                    return True
                except ValueError:
                    self.caller.msg(f"{stat_name} value must be a number between 0 and 5.")
                    return False

            if stat_name_lower == 'essence':
                valid_essence = ['Questing', 'Dynamic', 'Static', 'Primordial']
                if new_value not in valid_essence:
                    self.caller.msg(f"Invalid Essence type. Must be one of: {', '.join(valid_essence)}")
                    return False
                self.caller.set_stat('identity', 'lineage', 'Essence', new_value, temp=False)
                self.caller.set_stat('identity', 'lineage', 'Essence', new_value, temp=True)
                return True

        # Check for tribe-breed combinations whenever either is set
        if stat_name_lower in ['tribe', 'breed'] and self.caller.get_stat('identity', 'lineage', 'Type', temp=False) == 'Garou':
            breed = self.caller.get_stat('identity', 'lineage', 'Breed', temp=False)
            tribe = self.caller.get_stat('identity', 'lineage', 'Tribe', temp=False)
            
            # Update the current value based on what's being set
            if stat_name_lower == 'breed':
                breed = new_value
            else:  # tribe
                tribe = new_value
            
            # If we have both breed and tribe, check the combinations
            if breed and tribe:
                breed_lower = breed.lower()
                tribe_lower = tribe.lower()
                
                # Only show the relevant warning for the current combination
                if tribe_lower == "red talon" and breed_lower != "lupus":
                    self.caller.msg("|bGame:|n|r Red Talons only accept Lupus breed.|n")
                
                elif tribe_lower == "silver fang":
                    pure_breed = self.caller.get_stat('backgrounds', 'background', 'Pure Breed', temp=False)
                    self.caller.msg(f"Debug: Pure Breed value is: {pure_breed}")  # Debug message
                    if not pure_breed or pure_breed < 3:
                        self.caller.msg("|bGame:|n|r Silver Fangs traditionally require at least Pure Breed 3.|n")
                
                elif tribe_lower == "get of fenris" and breed_lower == "metis":
                    self.caller.msg("|bGame:|n|r Get of Fenris are particularly harsh toward Metis to the extent of killing them or exiling them.|n")
                
                elif tribe_lower == "shadow lord" and breed_lower == "metis":
                    self.caller.msg("|bGame:|n|y Shadow Lords often use Metis as expendable assets.|n")
                
                elif tribe_lower == "child of gaia":
                    self.caller.msg("|bGame:|n|y Children of Gaia accept all breeds equally.|n")
                
                elif tribe_lower in ["glass walker", "bone gnawer"] and breed_lower == "lupus":
                    self.caller.msg("|bGame:|n|r Glass Walkers and Bone Gnawers rarely contain Lupus breed.|n")
                
                elif tribe_lower == "black fury" and breed_lower != "metis":
                    self.caller.msg("|bGame:|n|r Black Furies are traditionally female-only (except for Metis).|n")

        # Handle Nature and Demeanor validation
        if stat_name_lower in ['nature', 'demeanor']:
            # Get list of valid archetypes from the database
            valid_archetypes = Stat.objects.filter(
                category='identity',
                stat_type='archetype'
            ).values_list('name', flat=True)

            # Convert to lowercase for case-insensitive comparison
            valid_archetypes_lower = [arch.lower() for arch in valid_archetypes]
            
            if new_value and new_value.lower() not in valid_archetypes_lower:
                self.caller.msg(f"Error: '{new_value}' is not a valid archetype. Valid archetypes are: {', '.join(sorted(valid_archetypes))}")
                return False

            # Get the proper case version of the archetype
            proper_case = next(arch for arch in valid_archetypes if arch.lower() == new_value.lower())
            
            # Set the value with proper case
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            if splat and splat.lower() == 'changeling':
                return ('powers', 'realm')
            elif (splat and splat.lower() == 'mortal+' and 
                  self.caller.get_stat('identity', 'lineage', 'Type', temp=False) == 'Kinain'):
                return ('powers', 'realm')
            else:
                self.caller.set_stat('archetype', 'personal', stat_name.title(), proper_case, temp=False)
                self.caller.set_stat('archetype', 'personal', stat_name.title(), proper_case, temp=True)
            return True

        # Handle Avatar/Genius setting Quintessence for Mages
        if stat_name_lower in ['avatar', 'genius']:
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            if splat and splat.lower() == 'mage':
                try:
                    new_value_int = int(new_value)
                    self.caller.set_stat('pools', 'dual', 'Quintessence', new_value_int, temp=False)
                    self.caller.set_stat('pools', 'dual', 'Quintessence', new_value_int, temp=True)
                    self.caller.msg(f"|yPermanent Quintessence set to {new_value_int} based on your {stat_name} rating.|n")
                except ValueError:
                    pass

        # Handle Enlightenment path changes
        if stat_name_lower == 'enlightenment':
            # Get the virtues for the path
            if new_value in PATH_VIRTUES:
                virtue1, virtue2 = PATH_VIRTUES[new_value]
                # Set default values for the virtues if they don't exist
                if 'virtues' not in self.caller.db.stats:
                    self.caller.db.stats['virtues'] = {}
                if 'moral' not in self.caller.db.stats['virtues']:
                    self.caller.db.stats['virtues']['moral'] = {}
                
                # Initialize or update the virtues
                self.caller.db.stats['virtues']['moral'][virtue1] = {'perm': 1, 'temp': 1}
                self.caller.db.stats['virtues']['moral'][virtue2] = {'perm': 1, 'temp': 1}
                
                # Remove old virtues that aren't used by the new path
                old_virtues = set(self.caller.db.stats['virtues']['moral'].keys())
                for virtue in old_virtues:
                    if virtue not in [virtue1, virtue2, 'Courage']:
                        del self.caller.db.stats['virtues']['moral'][virtue]
                
                self.caller.msg(f"|yVirtues set to {virtue1} and {virtue2}.|n")

        # Update Road value when virtues change
        if stat_name_lower in ['conscience', 'self-control', 'conviction', 'instinct']:
            road_value = self.calculate_road(self.caller)
            self.caller.set_stat('pools', 'moral', 'Road', road_value, temp=False)
            self.caller.set_stat('pools', 'moral', 'Road', road_value, temp=True)
            self.caller.msg(f"Updated Road to {road_value} based on virtues.")

        # Update Willpower when Courage changes
        if stat_name_lower == 'courage':
            splat = self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm')
            # Only update Willpower for splats that use Courage-based calculation
            if splat in ['Vampire', 'Mortal', 'Mortal+', 'Possessed']:
                willpower = calculate_willpower(self.caller)
                self.caller.set_stat('pools', 'dual', 'Willpower', willpower, temp=False)
                self.caller.set_stat('pools', 'dual', 'Willpower', willpower, temp=True)
                self.caller.msg(f"Updated Willpower to {willpower} based on virtues.")

        # Handle affiliation changes for Technocracy
        if stat_name_lower == 'affiliation' and new_value == 'Technocracy':
            # Get current Arete value and convert to Enlightenment
            arete_value = self.caller.get_stat('pools', 'advantage', 'Arete', temp=False)
            if arete_value is not None:
                # Remove Arete
                self.caller.del_stat('pools', 'advantage', 'Arete', temp=False)
                self.caller.del_stat('pools', 'advantage', 'Arete', temp=True)
                # Set Enlightenment to the same value
                self.caller.set_stat('pools', 'advantage', 'Enlightenment', arete_value, temp=False)
                self.caller.set_stat('pools', 'advantage', 'Enlightenment', arete_value, temp=True)
                self.caller.msg("Converted Arete to Enlightenment.")

            # Convert Tradition spheres to Technocratic spheres
            sphere_conversions = {
                'Correspondence': 'Data',
                'Prime': 'Primal Utility',
                'Spirit': 'Dimensional Science'
            }

            for old_sphere, new_sphere in sphere_conversions.items():
                # Get the rating of the old sphere if it exists
                sphere_value = self.caller.get_stat('powers', 'sphere', old_sphere, temp=False)
                if sphere_value is not None:
                    # Remove old sphere
                    self.caller.del_stat('powers', 'sphere', old_sphere, temp=False)
                    self.caller.del_stat('powers', 'sphere', old_sphere, temp=True)
                    # Add new sphere with same rating
                    self.caller.set_stat('powers', 'sphere', new_sphere, sphere_value, temp=False)
                    self.caller.set_stat('powers', 'sphere', new_sphere, sphere_value, temp=True)
                    self.caller.msg(f"Converted {old_sphere} to {new_sphere}.")

        elif stat_name_lower == 'possessed type':
            # Set the type
            self.caller.set_stat('identity', 'lineage', 'Possessed Type', new_value, temp=False)
            self.caller.set_stat('identity', 'lineage', 'Possessed Type', new_value, temp=True)
            self.caller.msg(f"Set Possessed Type to {new_value}.")
            
            # Initialize type-specific stats
            from world.wod20th.utils.possessed_utils import initialize_possessed_stats
            initialize_possessed_stats(self.caller, new_value)
            
            # Update banality based on new type
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            new_banality = get_default_banality(splat, subtype=new_value)
            self.caller.set_stat('pools', 'dual', 'Banality', new_banality, temp=False)
            self.caller.set_stat('pools', 'dual', 'Banality', new_banality, temp=True)
            self.caller.msg(f"|yBanality adjusted to {new_banality} based on your type.|n")
            return

        elif stat_name_lower == 'affiliation' and new_value != 'Technocracy':
            # Convert from Technocracy back to traditional spheres
            enlightenment_value = self.caller.get_stat('pools', 'advantage', 'Enlightenment', temp=False)
            if enlightenment_value is not None:
                # Remove Enlightenment
                self.caller.del_stat('pools', 'advantage', 'Enlightenment', temp=False)
                self.caller.del_stat('pools', 'advantage', 'Enlightenment', temp=True)
                # Set Arete to the same value
                self.caller.set_stat('pools', 'advantage', 'Arete', enlightenment_value, temp=False)
                self.caller.set_stat('pools', 'advantage', 'Arete', enlightenment_value, temp=True)
                self.caller.msg("Converted Enlightenment to Arete.")

            # Convert Technocratic methodologies back to traditional spheres
            methodology_conversions = {
                'Data': 'Correspondence',
                'Primal Utility': 'Prime',
                'Dimensional Science': 'Spirit'
            }

            for old_method, new_sphere in methodology_conversions.items():
                # Get the rating of the old methodology if it exists
                method_value = self.caller.get_stat('powers', 'sphere', old_method, temp=False)
                if method_value is not None:
                    # Remove old methodology
                    self.caller.del_stat('powers', 'sphere', old_method, temp=False)
                    self.caller.del_stat('powers', 'sphere', old_method, temp=True)
                    # Add new sphere with same rating
                    self.caller.set_stat('powers', 'sphere', new_sphere, method_value, temp=False)
                    self.caller.set_stat('powers', 'sphere', new_sphere, method_value, temp=True)
                    self.caller.msg(f"Converted {old_method} to {new_sphere}.")

        # Handle Techne to Mana conversion
        elif stat_name_lower == 'techne':
            self.caller.set_stat('pools', 'dual', 'Mana', new_value, temp=False)
            self.caller.set_stat('pools', 'dual', 'Mana', new_value, temp=True)

        # update pools for certain powers and other stats
        if self.category in ['blessing', 'special_advantage']:
            self.apply_power_based_pools(self.caller, self.category, stat_name.title(), new_value)

        elif stat_name_lower == 'breed':
            # Get shifter type
            shifter_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
            if shifter_type:
                # Common breed-based Gnosis values
                common_breed_gnosis = {
                    'homid': 1,
                    'metis': 3,
                    'lupus': 5,
                    'animal-born': 5,
                    'feline': 5,  # bastet animal-born
                    'squamus': 5,  # rokea animal-born
                    'ursine': 5,  # gurahl animal-born
                    'latrani': 5,  # nuwisha animal-born
                    'rodens': 5,  # ratkin animal-born
                    'corvid': 5,  # corax animal-born
                    'balaram': 1,  # nagah homid
                    'suchid': 4,  # mokole animal-born
                    'ahi': 5,  # nagah animal-born
                    'arachnid': 5,  # Ananasi animal-born
                    'kojin': 3,  # kitsune homid
                    'roko': 5,  # kitsune animal-born
                    'shinju': 4  # kitsune metis
                }

                # set Gnosis based on breed
                breed_lower = new_value.lower()
                if breed_lower in common_breed_gnosis:
                    self.caller.set_stat('pools', 'dual', 'Gnosis', common_breed_gnosis[breed_lower], temp=False)
                    self.caller.set_stat('pools', 'dual', 'Gnosis', common_breed_gnosis[breed_lower], temp=True)
                    self.caller.msg(f"Set Gnosis to {common_breed_gnosis[breed_lower]} based on breed.")

        # handle bastet tribe-based stats
        elif stat_name_lower == 'tribe' and self.caller.get_stat('identity', 'lineage', 'Type', temp=False) == 'Bastet':
            # Bastet tribe-based stats
            bastet_tribe_stats = {
                'balam': {'rage': 4, 'willpower': 3},
                'bubasti': {'rage': 1, 'willpower': 5},
                'ceilican': {'rage': 3, 'willpower': 3},
                'khan': {'rage': 5, 'willpower': 2},
                'pumonca': {'rage': 4, 'willpower': 4},
                'qualmi': {'rage': 2, 'willpower': 5},
                'simba': {'rage': 5, 'willpower': 2},
                'swara': {'rage': 2, 'willpower': 4}
            }
            
            tribe_lower = new_value.lower()
            if tribe_lower in bastet_tribe_stats:
                stats = bastet_tribe_stats[tribe_lower]
                self.caller.set_stat('pools', 'dual', 'Rage', stats['rage'], temp=False)
                self.caller.set_stat('pools', 'dual', 'Rage', stats['rage'], temp=True)
                self.caller.set_stat('pools', 'dual', 'Willpower', stats['willpower'], temp=False)
                self.caller.set_stat('pools', 'dual', 'Willpower', stats['willpower'], temp=True)
                self.caller.msg(f"Set Rage to {stats['rage']} and Willpower to {stats['willpower']} based on tribe.")

        # Handle garou tribe-based Willpower
        elif stat_name_lower == 'tribe' and self.caller.get_stat('identity', 'lineage', 'Type', temp=False) == 'Garou':
            garou_tribe_willpower = {
                'black fury': 3,
                'bone gnawer': 4,
                'child of gaia': 4,
                'fianna': 3,
                'get of fenris': 3,
                'glass walker': 3,
                'red talon': 3,
                'shadow lord': 3,
                'silent strider': 3,
                'silver fang': 3,
                'stargazer': 4,
                'uktena': 3,
                'wendigo': 4
            }
            
            tribe_lower = new_value.lower()
            if tribe_lower in garou_tribe_willpower:
                willpower = garou_tribe_willpower[tribe_lower]
                self.caller.set_stat('pools', 'dual', 'Willpower', willpower, temp=False)
                self.caller.set_stat('pools', 'dual', 'Willpower', willpower, temp=True)
                self.caller.msg(f"Set Willpower to {willpower} based on tribe.")
                return  # Add return here to prevent duplicate message

        # Handle auspice-based stats
        elif stat_name_lower == 'auspice':
            shifter_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
            auspice_lower = new_value.lower()
            
            if shifter_type == 'Garou':
                # Garou auspice-based Rage
                garou_auspice_rage = {
                    'ahroun': 5,
                    'galliard': 4,
                    'philodox': 3,
                    'theurge': 2,
                    'ragabash': 1
                }
                if auspice_lower in garou_auspice_rage:
                    rage = garou_auspice_rage[auspice_lower]
                    self.caller.set_stat('pools', 'dual', 'Rage', rage, temp=False)
                    self.caller.set_stat('pools', 'dual', 'Rage', rage, temp=True)
                    self.caller.msg(f"Set Rage to {rage} based on auspice.")
                    
            elif shifter_type == 'Rokea':
                # Rokea auspice-based Rage
                rokea_auspice_rage = {
                    'brightwater': 5,
                    'dimwater': 4,
                    'darkwater': 3
                }
                if auspice_lower in rokea_auspice_rage:
                    rage = rokea_auspice_rage[auspice_lower]
                    self.caller.set_stat('pools', 'dual', 'Rage', rage, temp=False)
                    self.caller.set_stat('pools', 'dual', 'Rage', rage, temp=True)
                    self.caller.msg(f"Set Rage to {rage} based on auspice.")
                    
            elif shifter_type == 'Nagah':
                # Nagah auspice-based Rage
                nagah_auspice_rage = {
                    'kamakshi': 3,
                    'kartikeya': 4,
                    'kamsa': 3,
                    'kali': 4
                }
                if auspice_lower in nagah_auspice_rage:
                    rage = nagah_auspice_rage[auspice_lower]
                    self.caller.set_stat('pools', 'dual', 'Rage', rage, temp=False)
                    self.caller.set_stat('pools', 'dual', 'Rage', rage, temp=True)
                    self.caller.msg(f"Set Rage to {rage} based on auspice.")

        # Handle aspect-based stats
        elif stat_name_lower == 'aspect':
            shifter_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
            aspect_lower = new_value.lower()
            
            if shifter_type == 'Ajaba':
                # Ajaba aspect-based stats
                ajaba_aspect_stats = {
                    'dawn': {'rage': 5, 'gnosis': 1},
                    'midnight': {'rage': 3, 'gnosis': 3},
                    'dusk': {'rage': 1, 'gnosis': 5}
                }
                if aspect_lower in ajaba_aspect_stats:
                    stats = ajaba_aspect_stats[aspect_lower]
                    self.caller.set_stat('pools', 'dual', 'Rage', stats['rage'], temp=False)
                    self.caller.set_stat('pools', 'dual', 'Rage', stats['rage'], temp=True)
                    self.caller.set_stat('pools', 'dual', 'Gnosis', stats['gnosis'], temp=False)
                    self.caller.set_stat('pools', 'dual', 'Gnosis', stats['gnosis'], temp=True)
                    self.caller.msg(f"Set Rage to {stats['rage']} and Gnosis to {stats['gnosis']} based on aspect.")
                    
            elif shifter_type == 'Ratkin':
                # Ratkin aspect-based Rage
                ratkin_aspect_rage = {
                    'tunnel runner': 1,
                    'shadow seer': 2,
                    'knife skulker': 3,
                    'warrior': 5,
                    'engineer': 2,
                    'plague lord': 3,
                    'munchmausen': 4,
                    'twitcher': 5
                }
                if aspect_lower in ratkin_aspect_rage:
                    rage = ratkin_aspect_rage[aspect_lower]
                    self.caller.set_stat('pools', 'dual', 'Rage', rage, temp=False)
                    self.caller.set_stat('pools', 'dual', 'Rage', rage, temp=True)
                    self.caller.msg(f"Set Rage to {rage} based on aspect.")

        # Handle Kitsune path-based Rage
        elif stat_name_lower == 'path' and self.caller.get_stat('identity', 'lineage', 'Type', temp=False) == 'Kitsune':
            kitsune_path_rage = {
                'kataribe': 2,
                'gukutsushi': 2,
                'doshi': 3,
                'eji': 4
            }
            path_lower = new_value.lower()
            if path_lower in kitsune_path_rage:
                rage = kitsune_path_rage[path_lower]
                self.caller.set_stat('pools', 'dual', 'Rage', rage, temp=False)
                self.caller.set_stat('pools', 'dual', 'Rage', rage, temp=True)
                self.caller.msg(f"Set Rage to {rage} based on path.")

        # Handle Mokole varna-based Rage
        elif stat_name_lower == 'varna' and self.caller.get_stat('identity', 'lineage', 'Type', temp=False) == 'Mokole':
            mokole_varna_rage = {
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
            varna_lower = new_value.lower()
            if varna_lower in mokole_varna_rage:
                rage = mokole_varna_rage[varna_lower]
                self.caller.set_stat('pools', 'dual', 'Rage', rage, temp=False)
                self.caller.set_stat('pools', 'dual', 'Rage', rage, temp=True)
                self.caller.msg(f"Set Rage to {rage} based on varna.")

        # Handle power-based pool updates
        if self.category in ['blessing', 'special_advantage']:
            self.apply_power_based_pools(self.caller, self.category, stat_name.title(), new_value)

        # Handle Silver Fang tribe initialization
        if stat_name_lower == 'tribe' and new_value.lower() == 'silver fang':
            # Initialize Silver Fang specific stats
            self.caller.set_stat('identity', 'lineage', 'Fang House', '', temp=False)
            self.caller.set_stat('identity', 'lineage', 'Fang House', '', temp=True)
            self.caller.set_stat('identity', 'lineage', 'Lodge', '', temp=False)
            self.caller.set_stat('identity', 'lineage', 'Lodge', '', temp=True)
            # Note: Camp will only be shown if it has data, handled by the display method

        # Handle Ananasi faction and cabal setting
        elif stat_name_lower == 'ananasi faction':
            aspect = self.caller.get_stat('identity', 'lineage', 'Aspect', temp=False)
            if aspect and new_value:
                aspect_lower = aspect.lower()
                faction_lower = new_value.lower()
                
                # Show faction description
                faction_desc = {
                    "myrmidon": "Warriors of Queen Ananasa, Myrmidons seek to understand the universe's pattern by analyzing the details around them.",
                    "viskr": "Shamans of Queen Ananasa, Viskr use powers to exert perfect control of their life, and to bring precise order to the world around them.",
                    "wyrsta": "Counter-spinners and challengers of order, Wyrsta question the interconnectedness of things by amassing extensive collections of subjects."
                }
                if faction_lower in faction_desc:
                    self.caller.msg(f"|bGame:|n|y {faction_desc[faction_lower]}|n")
                
                # Set the faction
                self.caller.set_stat('identity', 'lineage', 'Ananasi Faction', new_value, temp=False)
                self.caller.set_stat('identity', 'lineage', 'Ananasi Faction', new_value, temp=True)
                
                # Cabal matrix based on Aspect + Faction
                cabal_matrix = {
                    ('tenere', 'myrmidon'): {
                        'name': "Secean",
                        'desc': "Warriors of the Weaver, Secean seek to understand the universe's pattern by analyzing the details around them."
                    },
                    ('tenere', 'viskr'): {
                        'name': "Plicare",
                        'desc': "Shamans of the Weaver, Plicare use powers to exert a perfect control of their life, and to bring precise order to the world around them."
                    },
                    ('tenere', 'wyrsta'): {
                        'name': "Gaderin",
                        'desc': "Counter-spinners and challengers of order, Gaderin question the interconnectedness of things by amassing extensive collections of subjects."
                    },
                    ('hatar', 'myrmidon'): {
                        'name': "Agere",
                        'desc': "Destroyers sworn to the Balance Wyrm's purpose, Agere move quietly and surgically from one target to the next."
                    },
                    ('hatar', 'viskr'): {
                        'name': "Anomia",
                        'desc': "Balancers of the lost Balance, Anomia fulfill the Wyrm's role of destroyer by manipulation mortals into doing their work for them."
                    },
                    ('hatar', 'wyrsta'): {
                        'name': "Malum",
                        'desc': "Questioners of the Wyrm's faction and disdain corruption, Malum anguish in pursuit of pure, undiluted destruction and entropy."
                    },
                    ('kumoti', 'myrmidon'): {
                        'name': "Kar",
                        'desc': "Warriors of the Wyld, Kar manipulate their environment by working changes on the smallest levels."
                    },
                    ('kumoti', 'viskr'): {
                        'name': "Amari Aliquid",
                        'desc': "Sorcerers of chaos and creativity, Amari Aliquid fulfill the Wyld's mandate of constant change with persistent motion and action."
                    },
                    ('kumoti', 'wyrsta'): {
                        'name': "Chymos",
                        'desc': "Counter-dancers in the Wyld's name, Chymos undercut and fight against the minions of each Triatic spirit as necessary to further their plans for the Wyld."
                    }
                }
                
                # Set the cabal based on the combination
                if (aspect_lower, faction_lower) in cabal_matrix:
                    cabal_info = cabal_matrix[(aspect_lower, faction_lower)]
                    cabal = cabal_info['name']
                    self.caller.set_stat('identity', 'lineage', 'Cabal', cabal, temp=False)
                    self.caller.set_stat('identity', 'lineage', 'Cabal', cabal, temp=True)
                    self.caller.msg(f"|bGame:|n|yYour Ananasi Cabal has been automatically set to {cabal} based on your Aspect and Faction:|n")
                    self.caller.msg(f"|y{cabal_info['desc']}|n")

        # Handle aspect setting and description
        elif stat_name_lower == 'aspect':
            aspect_desc = {
                "tenere": "Warriors of the Weaver, Tenere seek to understand the universe's pattern by analyzing the details around them.",
                "hatar": "Servants of the Wyrm, Hatar fulfill the role of destroyer through manipulation and corruption.",
                "kumoti": "Children of the Wyld, Kumoti embrace chaos and constant change."
            }
            
            aspect_lower = new_value.lower()
            if aspect_lower in aspect_desc:
                self.caller.msg(f"|bGame:|n|y {aspect_desc[aspect_lower]}|n")
                
            # Set the aspect
            self.caller.set_stat('identity', 'lineage', 'Aspect', new_value, temp=False)
            self.caller.set_stat('identity', 'lineage', 'Aspect', new_value, temp=True)

        # Handle Wings special advantage
        if stat_name == 'Wings' and self.category == 'powers' and self.stat_type == 'special_advantage':
            # Set Flight talent based on Wings rating
            flight_value = 2 if int(new_value) == 3 else 4 if int(new_value) == 5 else 0
            if flight_value > 0:
                # Ensure abilities category exists
                if 'abilities' not in self.caller.db.stats:
                    self.caller.db.stats['abilities'] = {}
                if 'talent' not in self.caller.db.stats['abilities']:
                    self.caller.db.stats['abilities']['talent'] = {}
                
                # Set the Flight ability
                self.caller.db.stats['abilities']['talent']['Flight'] = {'perm': flight_value, 'temp': flight_value}
                self.caller.msg(f"|bGame:|n|y Flight {flight_value} added for winged companions.|n")
            else:
                # Remove Flight if Wings value doesn't grant it
                if 'abilities' in self.caller.db.stats and 'talent' in self.caller.db.stats['abilities']:
                    if 'Flight' in self.caller.db.stats['abilities']['talent']:
                        del self.caller.db.stats['abilities']['talent']['Flight']
                        self.caller.msg("|bGame:|n|r Flight ability removed.|n")

        # Add success messages for Mage stats
        if splat and splat.lower() == 'mage':
            if self.stat_name.lower() == 'resonance':
                self.caller.msg(f"Set Resonance to {self.value_change}. This represents your magical signature's strength.")
                return True
            elif self.stat_name.lower() in ['dynamic', 'static', 'entropic']:
                virtue_desc = {
                    'dynamic': "Dynamic synergy representing your connection to universal forces of change and motion",
                    'static': "Static synergy representing your connection to universal forces of stability and order",
                    'entropic': "Entropic synergy representing your connection to universal forces of decay and chaos"
                }
                self.caller.msg(f"{virtue_desc[self.stat_name.lower()]}.")
                return True
            elif self.stat_name.lower() == 'essence':
                self.caller.msg(f"Set Quintessence to {self.value_change}. This represents your store of magical energy.")
                return True

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

    def validate_stat_value(self, stat_name, value, allowed_values=None):
        """Validate a stat value against its allowed values and suggest matches if invalid."""
        if not allowed_values:
            return True, None

        # Convert everything to lowercase for case-insensitive comparison
        value_lower = value.lower()
        allowed_lower = [v.lower() for v in allowed_values]

        # Exact match
        if value_lower in allowed_lower:
            # Return the properly cased version
            return True, allowed_values[allowed_lower.index(value_lower)]

        # Find close matches
        close_matches = []
        for allowed, original in zip(allowed_lower, allowed_values):
            # Check if value is a substring of allowed value
            if value_lower in allowed:
                close_matches.append(original)
            # Check if allowed value is a substring of value
            elif allowed in value_lower:
                close_matches.append(original)
            # Check for similar spellings
            elif sum(1 for a, b in zip(value_lower, allowed) if a != b) <= 1:
                close_matches.append(original)

        if close_matches:
            matches_str = ", ".join(close_matches)
            return False, f"Invalid value. Did you mean one of these: {matches_str}?"
        else:
            values_str = ", ".join(allowed_values)
            return False, f"Invalid value. Must be one of: {values_str}"

    def get_allowed_values(self, stat_name, character):
        """Get the allowed values for a specific stat based on character type."""
        # Handle case where character is None
        if not character:
            return None
            
        # Get splat and handle None or non-string values
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        if not splat or not isinstance(splat, str):
            return None
            
        # Now we can safely use splat.lower()
        if splat.lower() == 'shifter':
            shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
            
            # Define valid breeds for each shifter type
            valid_breeds = {
                'garou': ["Homid", "Metis", "Lupus"],
                'bastet': ["Homid", "Metis", "Feline"],
                'corax': ["Homid", "Metis", "Corvid"],
                'gurahl': ["Homid", "Metis", "Ursine"],
                'mokole': ["Homid", "Metis", "Suchid"],
                'nagah': ["Balaram", "Metis", "Ahi"],
                'nuwisha': ["Homid", "Latrani"],  # Nuwisha don't have metis
                'ratkin': ["Homid", "Metis", "Rodens"],
                'rokea': ["Homid", "Metis", "Squamus"],
                'ananasi': ["Homid", "Metis", "Arachnid"],
                'kitsune': ["Kojin", "Shinju", "Roko"],  # Using their specific breed names
                'ajaba': ["Homid", "Metis", "Animal-Born"]
            }
            
            # Check for breed validation
            if stat_name.lower() == 'breed':
                if shifter_type and shifter_type.lower() in valid_breeds:
                    return valid_breeds[shifter_type.lower()]
                else:
                    self.caller.msg("You must set your shifter type before selecting a breed.")
                    return None
            
            # Validate tribe/auspice combinations
            if shifter_type and isinstance(shifter_type, str):
                # Special handling for Black Spiral Dancers
                if stat_name.lower() == 'tribe' and shifter_type.lower() == 'garou':
                    breed = character.get_stat('identity', 'lineage', 'Breed', temp=False)
                    auspice = character.get_stat('identity', 'lineage', 'Auspice', temp=False)
                    
                    # If they're trying to be a Black Spiral Dancer
                    if character.get_stat('identity', 'lineage', 'Tribe', temp=False) == 'Black Spiral Dancer':
                        self.caller.msg("|bGame:|n|r Black Spiral Dancers are corrupted Garou and considered Wyrm-based characters; see Wyrm staff for more information.|n")
                
                # Handle each shifter type's specific validations
                if shifter_type.lower() == 'garou':
                    if stat_name.lower() == 'auspice':
                        auspices = ["Ragabash", "Theurge", "Philodox", "Galliard", "Ahroun"]
                        return auspices
                        
                    elif stat_name.lower() == 'tribe':
                        tribes = ["Silver Fang", "Black Fury", "Red Talon", "Child of Gaia", 
                                "Bone Gnawer", "Shadow Lord", "Silent Strider", "Glass Walker", 
                                "Uktena", "Wendigo", "Stargazer", "Get of Fenris", "Fianna", "Black Spiral Dancer"]
                                                
                        # Only show Black Spiral Dancer warning here
                        if self.value_change and self.value_change.lower() == "black spiral dancer":
                            self.caller.msg("|bGame:|n|r Black Spiral Dancers are corrupted Garou and considered Wyrm-based characters; see Wyrm staff for more information.|n")
                        
                        return tribes

                elif shifter_type.lower() == 'ananasi':
                    if stat_name.lower() == 'aspect':
                        aspects = ["Tenere", "Hatar", "Kumoti"]
                        breed = character.get_stat('identity', 'lineage', 'Breed', temp=False)
                        
                        # Show description for selected aspect
                        if self.value_change:
                            aspect_desc = {
                                "tenere": "Warriors of the Weaver, Tenere seek to understand the universe's pattern by analyzing the details around them.",
                                "hatar": "Servants of the Wyrm, Hatar fulfill the role of destroyer through manipulation and corruption.",
                                "kumoti": "Children of the Wyld, Kumoti embrace chaos and constant change."
                            }
                            
                            aspect_lower = self.value_change.lower()
                            if aspect_lower in aspect_desc:
                                character.msg(f"|bGame:|n|y {aspect_desc[aspect_lower]}|n")
                        
                        if breed:
                            breed_lower = breed.lower()
                            if breed_lower == "homid":
                                character.msg("|bGame:|n|y While any aspect is possible, Homid Ananasi often favor the Kumoti aspect.|n")
                            elif breed_lower == "arachnid":
                                character.msg("|bGame:|n|y While any aspect is possible, Arachnid-born Ananasi often favor the Tenere aspect.|n")
                        
                        return aspects
                        
                    elif stat_name.lower() == 'ananasi faction':
                        factions = ["Myrmidon", "Viskr", "Wyrsta"]
                        return factions
                        
                    elif stat_name.lower() == 'cabal':
                        # Cabal is automatically set and shouldn't be manually changed
                        self.caller.msg("|bGame:|n|r Ananasi Cabal is automatically determined by your Aspect and Faction combination.|n")
                        
                        # Special notes about restricted Cabals
                        self.caller.msg("|bGame:|n|r Kumo and Antara are Wyrm-aligned Cabals requiring Hatar aspect and staff approval.|n")
                        self.caller.msg("|bGame:|n|r Kumatai and Padrone are outcast Cabals that are not available for player characters:|n")
                        self.caller.msg("  |bGame:|n|r- Kumatai: Ananasi who allow themselves to be worshipped by humans|n")
                        self.caller.msg("  |bGame:|n|r- Padrone: Misshapen monsters who hunt and consume other Ananasi|n")
                        
                        return None

                elif shifter_type.lower() == 'ajaba':
                    if stat_name.lower() == 'aspect':
                        return ["Dawn", "Midnight", "Dusk"]

                elif shifter_type.lower() == 'ratkin':
                    if stat_name.lower() == 'aspect':
                        aspects = ["Knife Skulkers", "Shadow Seers", "Tunnel Runners", "Warriors"]
                        breed = character.get_stat('identity', 'lineage', 'Breed', temp=False)
                        plague = character.get_stat('identity', 'lineage', 'Plague', temp=False)
                        
                        # Only show description for selected aspect
                        if self.value_change:
                            aspect_desc = {
                                "knife skulkers": "Assassins and spies, knife skulkers strike from the shadows",
                                "shadow seers": "Shadow Seers are mystics and prophets who interpret omens and commune with rat spirits",
                                "tunnel runners": "Tunnel Runners are scouts and messengers who maintain the underground network",
                                "warriors": "Warriors are front-line fighters who defend Ratkin territory"
                            }
                            
                            if self.value_change.lower() in aspect_desc:
                                self.caller.msg(f"|y {aspect_desc[self.value_change.lower()]}|n")
                        
                        if breed:
                            breed_lower = breed.lower()
                            if breed_lower == "homid":
                                self.caller.msg("|bGame:|n |yHomid Ratkin are generally treated more poorly by Ratkin than other species.|n")
                            elif breed_lower == "rodens":
                                self.caller.msg("|bGame:|n |yRodens-born often favor Tunnel Runner or Warrior aspects.|n")
                            elif breed_lower == "metis":
                                self.caller.msg("|bGame:|n |yMetis Ratkin face less prejudice than other shifter Metis and can excel in any aspect.|n")
                        
                        if plague:
                            plague_lower = plague.lower()
                            # Plague-specific aspect preferences
                            plague_aspects = {
                                "borrachon wererats": ["Warriors", "Tunnel Runners"],
                                "de la poer's disciples": ["Shadow Seers"],
                                "nezumi": ["Knife Skulkers", "Shadow Seers"],
                                "rattus typhus": ["Warriors"],
                                "thuggees": ["Knife Skulkers"]
                            }
                            if plague_lower in plague_aspects:
                                preferred = plague_aspects[plague_lower]
                                self.caller.msg(f"|bGame:|n|y {plague} traditionally favor the {' and '.join(preferred)} aspects.|n")
                        
                        return aspects
                        
                    elif stat_name.lower() == 'plague':
                        plagues = ["Borrachon Wererats", "De La Poer's Disciples", "Gamine", "Horde", 
                                    "Nezumi", "Ratkin Ronin", "Rat Race", "Rattus Typhus", "Thuggees"]
                        breed = character.get_stat('identity', 'lineage', 'Breed', temp=False)
                        aspect = character.get_stat('identity', 'lineage', 'Aspect', temp=False)
                        
                        # Only show description for selected plague
                        if self.value_change:
                            plague_info = {
                                "borrachon wererats": {
                                    "desc": "Urban warriors who protect their territory through force",
                                    "region": "Latin America"
                                },
                                "de la poer's disciples": {
                                    "desc": "Mystics and scholars obsessed with ancient knowledge",
                                    "region": "Europe"
                                },
                                "gamine": {
                                    "desc": "Street children and urban survivors",
                                    "region": "Urban centers worldwide"
                                },
                                "horde": {
                                    "desc": "Nomadic raiders and survivors",
                                    "region": "Asia"
                                },
                                "nezumi": {
                                    "desc": "Traditional Japanese Ratkin who maintain ancient ways",
                                    "region": "Japan"
                                },
                                "ratkin ronin": {
                                    "desc": "Wanderers who have left their original plagues",
                                    "region": "Worldwide"
                                },
                                "rat race": {
                                    "desc": "Corporate infiltrators and manipulators",
                                    "region": "Urban centers worldwide"
                                },
                                "rattus typhus": {
                                    "desc": "Militant extremists focused on human population reduction",
                                    "region": "Worldwide"
                                },
                                "thuggees": {
                                    "desc": "Assassins and death cultists",
                                    "region": "India and Southeast Asia"
                                }
                            }
                            
                            plague_lower = self.value_change.lower()
                            if plague_lower in plague_info:
                                info = plague_info[plague_lower]
                                self.caller.msg(f"|y{self.value_change}: {info['desc']} (Region: {info['region']})|n")
                        
                        if breed:
                            breed_lower = breed.lower()
                            if breed_lower == "homid":
                                self.caller.msg("|bGame:|n|y Homid Ratkin often join urban plagues like Rat Race or Gamine.|n")
                            elif breed_lower == "rodens":
                                self.caller.msg("|bGame:|n|y Rodens-born are common in any plague.|n")
                            elif breed_lower == "metis":
                                self.caller.msg("|bGame:|n|y Metis Ratkin are often found among the Ratkin Ronin. They are deformed and shamed by their parents.|n")
                        
                        if aspect:
                            aspect_lower = aspect.lower()
                            # Aspect-specific plague preferences
                            if aspect_lower == "shadow seers":
                                self.caller.msg("|bGame:|n|y Shadow Seers are particularly valued among De La Poer's Disciples and Nezumi.|n")
                            elif aspect_lower == "warriors":
                                self.caller.msg("|bGame:|n|y Warriors are common among Borrachon Wererats and Rattus Typhus.|n")
                            elif aspect_lower == "knife skulkers":
                                self.caller.msg("|bGame:|n|y Knife Skulkers are particularly valued among Thuggees and Rat Race.|n")
                            elif aspect_lower == "tunnel runners":
                                self.caller.msg("|bGame:|n|y Tunnel Runners are essential to all plagues but particularly valued by the Horde.|n")
                        
                        return plagues

                elif shifter_type.lower() == 'bastet':
                    if stat_name.lower() == 'tribe':
                        tribes = ["Balam", "Bubasti", "Ceilican", "Khan", "Pumonca", 
                                "Qualmi", "Simba", "Swara"]                        
                        # Only show description for selected tribe
                        if self.value_change:
                            tribe_regions = {
                                "balam": {
                                    "desc": "Jaguar-warriors of the rainforest",
                                    "region": "South and Central America"
                                },
                                "bubasti": {
                                    "desc": "Mystic guardians of ancient secrets",
                                    "region": "North Africa and Middle East"
                                },
                                "ceilican": {
                                    "desc": "Celtic shapeshifters and lorekeepers",
                                    "region": "Western Europe"
                                },
                                "khan": {
                                    "desc": "Tiger-warriors and noble hunters",
                                    "region": "Central and Eastern Asia"
                                },
                                "pumonca": {
                                    "desc": "Mountain lion warriors of the west",
                                    "region": "Western North America"
                                },
                                "qualmi": {
                                    "desc": "Snow leopard mystics of the mountains",
                                    "region": "Central Asia"
                                },
                                "simba": {
                                    "desc": "Lion kings of the savannah",
                                    "region": "Africa"
                                },
                                "swara": {
                                    "desc": "Tiger-judges of the ancient courts",
                                    "region": "India and Southeast Asia"
                                }
                            }
                            
                            tribe_lower = self.value_change.lower()
                            if tribe_lower in tribe_regions:
                                info = tribe_regions[tribe_lower]
                                self.caller.msg(f"|y{self.value_change}: {info['desc']} (Region: {info['region']})|n")
                        
                        return tribes

                elif shifter_type.lower() == 'mokole':
                    if stat_name.lower() == 'stream':
                        streams = ["Gumagan", "Mokole-mbembe", "Zhong Lung", "Makara"]
                        breed = character.get_stat('identity', 'lineage', 'Breed', temp=False)
                        
                        # Store stream info for later use when actually setting the value
                        stream_info = {
                            "gumagan": {
                                "desc": "Rainbow Serpent dreamers of the islands",
                                "region": "Australia and Pacific Islands"
                            },
                            "mokole-mbembe": {
                                "desc": "Ancient guardians of African waters",
                                "region": "Africa"
                            },
                            "zhong lung": {
                                "desc": "Dragon-kings of Asian tradition",
                                "region": "Asia"
                            },
                            "makara": {
                                "desc": "Sacred crocodiles of ancient rivers",
                                "region": "India and Southeast Asia"
                            }
                        }
                        
                        # Store messages for later instead of sending them now
                        messages = []
                        if self.value_change:
                            stream_lower = self.value_change.lower()
                            if stream_lower in stream_info:
                                info = stream_info[stream_lower]
                                messages.append(f"|y{self.value_change}: {info['desc']} (Region: {info['region']})|n")
                        
                        if breed:
                            breed_lower = breed.lower()
                            if breed_lower == "homid":
                                messages.append("|bGame:|n|r Warning: Homid Mokole are extremely rare.|n")
                                if "Zhong Lung" in streams:
                                    messages.append("|bGame:|n|y Note: Zhong Lung are slightly more accepting of Homid breed.|n")
                        
                        # Store messages in a class variable for use when setting the value
                        self.pending_messages = messages
                        return streams
                                
                    elif stat_name.lower() == 'varna':
                        stream = character.get_stat('identity', 'lineage', 'Stream', temp=False)
                        varnas = ["Champsa", "Gharial", "Halpatee", "Karna", "Makara", 
                                "Ora", "Piasa", "Syrta", "Unktehi"]
                        
                        messages = []
                        # Only show description for selected varna
                        if self.value_change:
                            varna_desc = {
                                "champsa": "Crocodilian warriors of the rivers",
                                "gharial": "Swift hunters of the waterways",
                                "halpatee": "Gentle giants of coastal waters",
                                "karna": "Dragon-scholars of ancient lore",
                                "makara": "Sacred guardians of temple waters",
                                "ora": "Mighty dragons of the outback",
                                "piasa": "Thunder-lizards of native legend",
                                "syrta": "Sea-serpents of the deep",
                                "unktehi": "Water spirits of the great lakes"
                            }
                            
                            varna_lower = self.value_change.lower()
                            if varna_lower in varna_desc:
                                messages.append(f"|y{self.value_change}: {varna_desc[varna_lower]}|n")
                        
                        # Stream-specific varna preferences
                        stream_varnas = {
                            "Gumagan": ["Ora", "Piasa"],
                            "Mokole-mbembe": ["Champsa", "Gharial"],
                            "Zhong Lung": ["Karna", "Makara"],
                            "Makara": ["Halpatee", "Syrta"]
                        }
                        
                        if stream and stream in stream_varnas:
                            preferred = stream_varnas[stream]
                            messages.append(f"|bGame:|n|y {stream} traditionally favor the {' and '.join(preferred)} varnas.|n")
                            
                            # Some varnas are extremely rare outside their traditional streams
                            available_varnas = []
                            for varna in varnas:
                                if varna in preferred:
                                    available_varnas.append(varna)
                                elif stream == "Zhong Lung":  # Zhong Lung are more flexible
                                    available_varnas.append(varna)
                                    messages.append(f"|bGame:|n|y {varna} is uncommon among {stream}.|n")
                                else:
                                    messages.append(f"|bGame:|n|r {varna} is extremely rare among {stream}.|n")
                            
                            self.pending_messages = messages
                            return available_varnas
                        
                        self.pending_messages = messages
                        return varnas
                        
                    elif stat_name.lower() == 'auspice':
                        stream = character.get_stat('identity', 'lineage', 'Stream', temp=False)
                        auspices = ["Rising Sun", "Noonday Sun", "Shrouded Sun", "Midnight Sun", 
                                    "Decorated Sun", "Solar Eclipse"]
                        
                        messages = []
                        # Only show description for selected auspice
                        if self.value_change:
                            auspice_desc = {
                                "rising sun": "Dawn-born leaders and innovators",
                                "noonday sun": "Mighty warriors of the brightest hour",
                                "shrouded sun": "Mystics of the clouded sky",
                                "midnight sun": "Guardians of ancient secrets",
                                "decorated sun": "Keepers of tradition and ceremony",
                                "solar eclipse": "Rare births of great power and destiny",
                                # Regional variants
                                "tung chun": "Eastern dawn-born leaders (Zhong Lung)",
                                "nam hsia": "Southern summer warriors (Zhong Lung)",
                                "sai chau": "Western twilight mystics (Zhong Lung)",
                                "pei tung": "Northern midnight judges (Zhong Lung)",
                                "hemanta": "Winter-born leaders (Makara)",
                                "zarad": "Summer warriors (Makara)",
                                "grisma": "Spring mystics (Makara)",
                                "vasanta": "Autumn judges (Makara)"
                            }
                            
                            auspice_lower = self.value_change.lower()
                            if auspice_lower in auspice_desc:
                                messages.append(f"|bGame:|n|y {self.value_change}: {auspice_desc[auspice_lower]}|n")
                        
                        # Add regional auspices based on stream
                        if stream:
                            if stream == "Zhong Lung":
                                auspices.extend(["Tung Chun", "Nam Hsia", "Sai Chau", "Pei Tung"])
                                messages.append("|bGame:|n|y Zhong Lung use their own auspice names which are Tung Chun, Nam Hsia, Sai Chau, and Pei Tung.|n")
                            elif stream == "Makara":
                                auspices.extend(["Hemanta", "Zarad", "Grisma", "Vasanta"])
                                messages.append("|bGame:|n|y Makara use their own auspice names which are Hemanta, Zarad, Grisma, and Vasanta.|n")
                        
                        self.pending_messages = messages
                        return auspices

                elif shifter_type.lower() == 'kitsune':
                    if stat_name.lower() == 'path':
                        paths = ["Eji", "Doshi", "Gukutsushi", "Kataribe"]
                        breed = character.get_stat('identity', 'lineage', 'Breed', temp=False)
                        faction = character.get_stat('identity', 'lineage', 'Faction', temp=False)
                        
                        # Only show description for selected path
                        if self.value_change:
                            path_desc = {
                                "eji": "Warriors and protectors of the Kitsune",
                                "doshi": "Mystics and spiritual leaders",
                                "gukutsushi": "Shapeshifting masters and tricksters",
                                "kataribe": "Storytellers and keepers of tradition"
                            }
                            
                            path_lower = self.value_change.lower()
                            if path_lower in path_desc:
                                self.caller.msg(f"|y{self.value_change}: {path_desc[path_lower]}|n")
                        
                        if breed:
                            breed_lower = breed.lower()
                            # Specific path preferences
                            if breed_lower == "roko":  # Animal-born
                                self.caller.msg("|bGame:|n|y Roko (Animal-born) Kitsune often favor the Gukutsushi path.|n")
                            elif breed_lower == "kojin":  # Human-born
                                self.caller.msg("|bGame:|n|y Kojin (Human-born) Kitsune often favor the Doshi or Kataribe paths.|n")
                            elif breed_lower == "shinju":  # Metis
                                self.caller.msg("|bGame:|n|r Shinju (Metis) Kitsune face some prejudice but are accepted in all paths.|n")
                        
                        if faction:
                            faction_lower = faction.lower()
                            if faction_lower == "emerald courts":
                                self.caller.msg("|bGame:|n|y The Emerald Courts particularly value the Doshi path.|n")
                            elif faction_lower == "western courts":
                                self.caller.msg("|bGame:|n|y The Western Courts are more accepting of all paths.|n")
                        
                        return paths
                        
                    elif stat_name.lower() == 'faction':
                        factions = ["Emerald Courts", "Western Courts"]
                        breed = character.get_stat('identity', 'lineage', 'Breed', temp=False)
                        path = character.get_stat('identity', 'lineage', 'Path', temp=False)
                        
                        # Only show description for selected faction
                        if self.value_change:
                            faction_desc = {
                                "emerald courts": "Traditional Asian courts maintaining ancient ways",
                                "western courts": "Modern courts adapting to Western culture using the Ahadi system of the African fera"
                            }
                            
                            faction_lower = self.value_change.lower()
                            if faction_lower in faction_desc:
                                self.caller.msg(f"|bGame:|n|y {self.value_change}: {faction_desc[faction_lower]}|n")
                        
                        # Regional/cultural notes
                        self.caller.msg("|bGame:|n|y Emerald Courts are traditionally Asian, while Western Courts are found elsewhere.|n")
                        
                        if breed:
                            breed_lower = breed.lower()
                            if breed_lower == "shinju":
                                self.caller.msg("|bGame:|n|r Shinju (Metis) face more prejudice in the Emerald Courts.|n")
                            elif breed_lower == "kojin":
                                self.caller.msg("|bGame:|n|y Kojin (Human-born) are more common in the Western Courts.|n")
                            elif breed_lower == "roko":
                                self.caller.msg("|bGame:|n|y Roko (Animal-born) are more common in the Emerald Courts.|n")
                        
                        if path:
                            path_lower = path.lower()
                            if path_lower == "doshi":
                                self.caller.msg("|bGame:|n|y Doshi are particularly respected in the Emerald Courts.|n")
                            elif path_lower == "kataribe":
                                self.caller.msg("|bGame:|n|y Kataribe are valued in both courts for their knowledge.|n")
                            elif path_lower == "gukutsushi":
                                self.caller.msg("|bGame:|n|y Gukutsushi are more common in the Emerald Courts.|n")
                            elif path_lower == "eji":
                                self.caller.msg("|bGame:|n|y Eji are equally respected in both courts.|n")
                        
                        return factions

                elif shifter_type.lower() == 'nagah':
                    if stat_name.lower() == 'auspice':
                        auspices = ["Kamakshi", "Kartikeya", "Kamsa", "Kali"]
                        breed = character.get_stat('identity', 'lineage', 'Breed', temp=False)
                        
                        # Only show description for selected auspice
                        if self.value_change:
                            auspice_desc = {
                                "kamakshi": "Judges and mediators of the Nagah",
                                "kartikeya": "Warriors and protectors",
                                "kamsa": "Mystics and healers",
                                "kali": "Executioners and avengers"
                            }
                            
                            auspice_lower = self.value_change.lower()
                            if auspice_lower in auspice_desc:
                                self.caller.msg(f"|y{self.value_change}: {auspice_desc[auspice_lower]}|n")
                        
                        if breed:
                            breed_lower = breed.lower()
                            if breed_lower == "balaram":  # Homid
                                self.caller.msg("|bGame:|n|y Balaram (Homid) Nagah often excel as Kamakshi or Kamsa.|n")
                            elif breed_lower == "ahi":  # Animal-born
                                self.caller.msg("|bGame:|n|y Ahi (Snake-born) Nagah often excel as Kartikeya or Kali.|n")
                            elif breed_lower == "metis":
                                self.caller.msg("|bGame:|n|r Metis Nagah are cherished by their kind and seen as a blessing. They excel in all auspices.|n")
                        
                        return auspices
                        
                    elif stat_name.lower() == 'crown':
                        crowns = ["Ananta", "Vasuki", "Takshaka", "Kulika"]
                        breed = character.get_stat('identity', 'lineage', 'Breed', temp=False)
                        auspice = character.get_stat('identity', 'lineage', 'Auspice', temp=False)
                        
                        # Only show description for selected crown
                        if self.value_change:
                            crown_desc = {
                                "ananta": "Keepers of wisdom and tradition",
                                "vasuki": "Masters of poison and healing",
                                "takshaka": "Warriors and protectors",
                                "kulika": "Mystics and seers"
                            }
                            
                            crown_lower = self.value_change.lower()
                            if crown_lower in crown_desc:
                                self.caller.msg(f"|y{self.value_change}: {crown_desc[crown_lower]}|n")
                        
                        if breed:
                            breed_lower = breed.lower()
                            if breed_lower == "balaram":
                                self.caller.msg("|bGame:|n|y Balaram (Homid) Nagah often join Ananta or Kulika crowns.|n")
                            elif breed_lower == "ahi":
                                self.caller.msg("|bGame:|n|y Ahi (Snake-born) Nagah often join Vasuki or Takshaka crowns.|n")
                        
                        if auspice:
                            auspice_lower = auspice.lower()
                            # Auspice-specific crown preferences
                            if auspice_lower == "kamakshi":
                                self.caller.msg("|bGame:|n|y Kamakshi often join the Ananta crown.|n")
                            elif auspice_lower == "kartikeya":
                                self.caller.msg("|bGame:|n|y Kartikeya often join the Takshaka crown.|n")
                            elif auspice_lower == "kamsa":
                                self.caller.msg("|bGame:|n|y Kamsa often join the Vasuki crown.|n")
                            elif auspice_lower == "kali":
                                self.caller.msg("|bGame:|n|y Kali often join the Kulika crown.|n")
                        
                        return crowns

                elif shifter_type.lower() == 'rokea':
                    if stat_name.lower() == 'auspice':
                        auspices = ["Brightwater", "Dimwater", "Darkwater"]
                        breed = character.get_stat('identity', 'lineage', 'Breed', temp=False)
                        
                        # Only show description for selected auspice
                        if self.value_change:
                            auspice_desc = {
                                "brightwater": "Surface hunters and warriors",
                                "dimwater": "Travelers and diplomats",
                                "darkwater": "Deep sea mystics and lore keepers"
                            }
                            
                            auspice_lower = self.value_change.lower()
                            if auspice_lower in auspice_desc:
                                self.caller.msg(f"|y{self.value_change}: {auspice_desc[auspice_lower]}|n")
                        
                        if breed:
                            breed_lower = breed.lower()
                            if breed_lower == "homid":
                                self.caller.msg("|bGame:|n|r Homid Rokea are extremely rare, even among the Same-Bito.|n")
                            elif breed_lower == "squamus":
                                self.caller.msg("|bGame:|n|y Squamus (Shark-born) Rokea are the most common and numerous Rokea.|n")
                        return auspices

                elif shifter_type.lower() == 'nuwisha':
                    if stat_name.lower() == 'breed':
                        breeds = ["Homid", "Latrani"]  # Nuwisha don't have Metis
                        
                        # Only show description for selected breed
                        if self.value_change:
                            breed_desc = {
                                "homid": "Born to human parents, masters of human society",
                                "latrani": "Born to coyote parents, naturally attuned to Gaia"
                            }
                            
                            breed_lower = self.value_change.lower()
                            if breed_lower in breed_desc:
                                self.caller.msg(f"|bGame:|n|y {self.value_change}: {breed_desc[breed_lower]}|n")
                        
                        return breeds

        elif splat.lower() == 'companion':
            if stat_name.lower() == 'companion type':
                return ["Alien", "Animal", "Bygone", "Construct", "Familiar", 
                       "Object", "Reanimate", "Robot", "Spirit"]
        return None

    def initialize_companion_type(self, character, companion_type):
        """Initialize stats when companion type is set."""
        # Validate companion type
        valid_types = ["Alien", "Animal", "Bygone", "Construct", "Familiar", 
                      "Object", "Reanimate", "Robot", "Spirit"]
        if companion_type not in valid_types:
            self.caller.msg(f"Error: Invalid companion type. Must be one of: {', '.join(valid_types)}")
            return

        # Set Banality based on companion type
        banality_values = {
            'Alien': 6,
            'Animal': 5,
            'Bygone': 3,
            'Construct': 5,
            'Familiar': 4,
            'Object': 3,
            'Reanimate': 7,
            'Robot': 7,
            'Spirit': 4
        }
        banality = banality_values[companion_type]
        character.set_stat('pools', 'dual', 'Banality', banality, temp=False)
        character.set_stat('pools', 'dual', 'Banality', banality, temp=True)
        self.caller.msg(f"Set Banality to {banality} based on companion type.")

        # Initialize Essence for Familiar type
        if companion_type == 'Familiar':
            character.set_stat('pools', 'dual', 'Essence', 10, temp=False)
            character.set_stat('pools', 'dual', 'Essence', 10, temp=True)
            self.caller.msg("Set Essence pool to 10 for Familiar type.")

    def initialize_shifter_type(self, character, shifter_type):
        """Initialize stats when shifter type is set."""
        if shifter_type.lower() == 'ananasi':
            # Initialize Ananasi blood pool at 10
            character.set_stat('pools', 'dual', 'Blood', 10, temp=False)
            character.set_stat('pools', 'dual', 'Blood', 10, temp=True)

            # Initialize Ananasi-specific stats
            character.set_stat('identity', 'lineage', 'Cabal', '', temp=False)
            character.set_stat('identity', 'lineage', 'Cabal', '', temp=True)
            character.set_stat('identity', 'lineage', 'Faction', '', temp=False)
            character.set_stat('identity', 'lineage', 'Faction', '', temp=True)

    def initialize_mortalplus_pools(self, character, mortalplus_type):
        """Initialize pools for Mortal+ characters."""
        # Store current Willpower value BEFORE any other initialization
        willpower_perm = character.get_stat('pools', 'dual', 'Willpower', temp=False) or 3
        willpower_temp = character.get_stat('pools', 'dual', 'Willpower', temp=True) or 3

        # First call the mortalplus_utils initialization
        from world.wod20th.utils.mortalplus_utils import initialize_mortalplus_stats
        initialize_mortalplus_stats(character, mortalplus_type)

        # Then set type-specific pools
        if mortalplus_type.lower() == 'ghoul':
            # Ghouls get 3 blood points
            character.set_stat('pools', 'dual', 'Blood', 3, temp=False)
            character.set_stat('pools', 'dual', 'Blood', 3, temp=True)
            self.caller.msg("|ySet Blood Pool to 3 for Ghoul.|n")
        elif mortalplus_type.lower() == 'kinain':
            # Kinain get 2 glamour points
            character.set_stat('pools', 'dual', 'Glamour', 2, temp=False)
            character.set_stat('pools', 'dual', 'Glamour', 2, temp=True)
            self.caller.msg("|ySet Glamour Pool to 2 for Kinain.|n")
        elif mortalplus_type.lower() == 'kinfolk':
            # Initialize Gnosis at 0 (will be set by merit)
            character.set_stat('pools', 'dual', 'Gnosis', 0, temp=False)
            character.set_stat('pools', 'dual', 'Gnosis', 0, temp=True)
            self.caller.msg("|ySet Gnosis Pool to 0 for Kinfolk. Please set Gnosis using the 'Gnosis' merit if you wish.|n")
        elif mortalplus_type.lower() == 'sorcerer':
            # Initialize Mana at 3 (will be updated by Techne)
            character.set_stat('pools', 'dual', 'Mana', 0, temp=False)
            character.set_stat('pools', 'dual', 'Mana', 0, temp=True)
            character.set_stat('pools', 'dual', 'Willpower', 5, temp=False)
            character.set_stat('pools', 'dual', 'Willpower', 5, temp=True)
            self.caller.msg("|yInitialized Mana Pool to 0 and set Willpower Pool to 5 for Sorcerer. Please set Techne background to increase Mana pool.|n")
        # Finally restore Willpower values AFTER all other initialization
        character.set_stat('pools', 'dual', 'Willpower', willpower_perm, temp=False)
        character.set_stat('pools', 'dual', 'Willpower', willpower_temp, temp=True)

    def handle_special_advantages(self, character, advantage_name, value):
        """Handle special effects of advantages."""
        if advantage_name == 'Wings':
            # Set Flight talent based on Wings rating
            # Wings 3 grants Flight 2, Wings 5 grants Flight 4
            flight_value = 2 if int(value) == 3 else 4 if int(value) == 5 else 0
            character.set_stat('abilities', 'talent', 'Flight', flight_value, temp=False)
            character.set_stat('abilities', 'talent', 'Flight', flight_value, temp=True)
            self.caller.msg(f"Added Flight talent at rating {flight_value} based on Wings rating.")

    def validate_special_advantage(self, advantage_name, value):
        """Validate and set a companion special advantage."""
        # Return early if advantage_name is None
        if not advantage_name:
            return False, "Invalid special advantage"
            
        if self.caller.get_stat('other', 'splat', 'Splat', temp=False) != 'Companion':
            return False, "Only Companions can have special advantages."
            
        valid_advantages = {
            'acute smell': {'valid_values': [2, 3], 'desc': "Adds dice to Perception rolls involving scent"},
            'alacrity': {'valid_values': [2, 4, 6], 'desc': "Allows extra actions with Willpower expenditure"},
            'armor': {'valid_values': [1, 2, 3, 4, 5], 'desc': "Provides innate protection, each point adds one soak die"},
            'aura': {'valid_values': [3], 'desc': "Opponents suffer +3 difficulty on rolls against you"},
            'aww!': {'valid_values': [1, 2, 3, 4], 'desc': "Adds dice to Social rolls based on cuteness"},
            'bare necessities': {'valid_values': [1, 3], 'desc': "Retain items when shapeshifting"},
            'bioluminescence': {'valid_values': [1, 2, 3], 'desc': "Body can glow at will"},
            'blending': {'valid_values': [1], 'desc': "Can alter appearance to match surroundings"},
            'bond-sharing': {'valid_values': [4, 5, 6], 'desc': "Creates mystical bond to share abilities"},
            'cause insanity': {'valid_values': [2, 4, 6, 8, 10], 'desc': "Can provoke temporary fits of madness"},
            'chameleon coloration': {'valid_values': [4, 6, 8], 'desc': "Ability to change coloration for camouflage"},
            'claws, fangs, or horns': {'valid_values': [3, 5, 7], 'desc': "Natural weaponry that inflicts lethal damage"},
            'deadly demise': {'valid_values': [2, 4, 6], 'desc': "Upon death, inflicts damage to nearby enemies"},
            'dominance': {'valid_values': [1], 'desc': "Naturally commanding demeanor within specific groups"},
            'earthbond': {'valid_values': [2], 'desc': "Mystical connection to perceive threats"},
            'elemental touch': {'valid_values': [3, 5, 7, 10, 15], 'desc': "Control over a single element"},
            'empathic bond': {'valid_values': [2], 'desc': "Ability to sense and influence emotions"},
            'enhancement': {'valid_values': [5, 10, 15], 'desc': "Superior physical or mental attributes"},
            'extra heads': {'valid_values': [2, 4, 6, 8], 'desc': "Additional heads with perception bonuses"},
            'extra limbs': {'valid_values': [2, 4, 6, 8], 'desc': "Additional prehensile limbs"},
            'feast of nettles': {'valid_values': [2, 3, 4, 5, 6], 'desc': "Ability to absorb and nullify Paradox"},
            'ferocity': {'valid_values': [2, 4, 6, 8, 10], 'desc': "Grants Rage points equal to half rating"},
            'ghost form': {'valid_values': [8, 10], 'desc': "Become invisible or incorporeal"},
            'hibernation': {'valid_values': [2], 'desc': "Can enter voluntary hibernation state"},
            'human guise': {'valid_values': [1, 2, 3], 'desc': "Ability to appear human"},
            'immunity': {'valid_values': [2, 5, 10, 15], 'desc': "Immunity to specific harmful effects"},
            'mesmerism': {'valid_values': [3, 6], 'desc': "Hypnotic gaze abilities"},
            'musical influence': {'valid_values': [6], 'desc': "Affect emotions through music"},
            'musk': {'valid_values': [3], 'desc': "Emit powerful stench affecting rolls"},
            'mystic shield': {'valid_values': [2, 4, 6, 8, 10], 'desc': "Resistance to magic"},
            'needleteeth': {'valid_values': [3], 'desc': "Sharp teeth bypass armor"},
            'nightsight': {'valid_values': [3], 'desc': "Clear vision in low light conditions"},
            'omega status': {'valid_values': [4], 'desc': "Power in being overlooked"},
            'paradox nullification': {'valid_values': [2, 3, 4, 5, 6], 'desc': "Ability to consume Paradox energies"},
            'quills': {'valid_values': [2, 4], 'desc': "Sharp defensive spines"},
            'rapid healing': {'valid_values': [2, 4, 6, 8], 'desc': "Accelerated recovery from injuries"},
            'razorskin': {'valid_values': [3], 'desc': "Skin that shreds on contact"},
            'read and write': {'valid_values': [1], 'desc': "Ability to read and write human languages"},
            'regrowth': {'valid_values': [2, 4, 6], 'desc': "Regenerative capabilities"},
            'shapechanger': {'valid_values': [3, 5, 8], 'desc': "Ability to assume different forms"},
            'shared knowledge': {'valid_values': [5, 7], 'desc': "Mystic bond allowing shared understanding"},
            'size': {'valid_values': [3, 5, 8, 10], 'desc': "Significantly larger or smaller than human norm"},
            'soak lethal damage': {'valid_values': [3], 'desc': "Natural ability to soak lethal damage"},
            'soak aggravated damage': {'valid_values': [5], 'desc': "Can soak aggravated damage"},
            'soul-sense': {'valid_values': [2, 3], 'desc': "Ability to sense spirits and impending death"},
            'spirit travel': {'valid_values': [8, 10, 15], 'desc': "Ability to cross into Umbral realms"},
            'spirit vision': {'valid_values': [3], 'desc': "Ability to perceive the Penumbra"},
            'tunneling': {'valid_values': [3], 'desc': "Can create tunnels through earth"},
            'unaging': {'valid_values': [5], 'desc': "Immunity to natural aging process"},
            'universal translator': {'valid_values': [5], 'desc': "Ability to understand languages"},
            'venom': {'valid_values': [3, 6, 9, 12, 15], 'desc': "Poisonous attack capability"},
            'wall-crawling': {'valid_values': [4], 'desc': "Ability to climb sheer surfaces easily"},
            'water breathing': {'valid_values': [2, 5], 'desc': "Can breathe underwater"},
            'webbing': {'valid_values': [5], 'desc': "Can spin webs with various uses"},
            'wings': {'valid_values': [3, 5], 'desc': "Wings 3 grants Flight 2, Wings 5 grants Flight 4"}
        } 
        
        advantage_lower = advantage_name.lower()
        if advantage_lower not in valid_advantages:
            return False, f"Invalid special advantage. Valid options are: {', '.join(valid_advantages.keys())}"
            
        try:
            value = int(value)
            advantage_info = valid_advantages[advantage_lower]
            
            if value not in advantage_info['valid_values']:
                return False, f"Invalid value for {advantage_name}. Valid values are: {', '.join(map(str, advantage_info['valid_values']))}. {advantage_info['desc']}"
                
            # Set the advantage
            proper_name = advantage_name.title()
            self.caller.set_stat('powers', 'special_advantage', proper_name, value, temp=False)
            self.caller.set_stat('powers', 'special_advantage', proper_name, value, temp=True)
            
            # Handle Flight for Wings
            if advantage_lower == 'wings':
                flight_value = 2 if value == 3 else 4 if value == 5 else 0
                if flight_value > 0:
                    self.caller.set_stat('abilities', 'talent', 'Flight', flight_value, temp=False)
                    self.caller.set_stat('abilities', 'talent', 'Flight', flight_value, temp=True)
                    return True, f"{proper_name} {value} adds the Flight talent at rating {flight_value} for free."
                    
            return True, f"Set {proper_name} to {value}"
            
        except (ValueError, TypeError):
            return False, "Value must be a number"
