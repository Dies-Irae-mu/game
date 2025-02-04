from evennia import Command, default_cmds
from django.db import models
from typing import Dict, List, Union
import re

# Import models
from world.wod20th.models import Stat

# Import utility functions and constants
from world.wod20th.utils.stat_mappings import (
    CATEGORIES, STAT_TYPES, 
    UNIVERSAL_BACKGROUNDS, IDENTITY_PERSONAL, IDENTITY_LINEAGE, SPECIAL_STATS,
    SECONDARY_TALENTS, SECONDARY_SKILLS, SECONDARY_KNOWLEDGES, VALID_SPLATS,
    VALID_SHIFTER_TYPES, VALID_MORTALPLUS_TYPES, VALID_POSSESSED_TYPES,
    GENERATION_FLAWS, GENERATION_MAP, VAMPIRE_BACKGROUNDS, CHANGELING_BACKGROUNDS,
    MAGE_BACKGROUNDS, TECHNOCRACY_BACKGROUNDS, TRADITIONS_BACKGROUNDS, NEPHANDI_BACKGROUNDS,
    SORCERER_BACKGROUNDS, SHIFTER_BACKGROUNDS, GENERATION_MAP, GENERATION_FLAWS,
    STAT_TYPE_TO_CATEGORY, IDENTITY_STATS, SPLAT_STAT_OVERRIDES,
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
from world.wod20th.utils.virtue_utils import PATH_VIRTUES
from world.wod20th.utils.banality import get_default_banality

from commands.CmdLanguage import CmdLanguage

class CmdSelfStat(default_cmds.MuxCommand):
    """
    Usage:
      +selfstat <stat>[(<instance>)]/<stat_type>=<value>
      +selfstat <stat>[(<instance>)]/<stat_type>=
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
            'advantages': {'background': {}},
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
            
            # Set up synergy virtues
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
            character.msg(f"Your Banality has been updated to {banality} based on your character type.")

    def update_companion_pools(self, character):
        """Update pools based on Companion powers."""
        if character.get_stat('other', 'splat', 'Splat', temp=False) != 'Companion':
            return

        # Update Rage based on Ferocity
        if ferocity := character.get_stat('powers', 'special_advantage', 'Ferocity', temp=False):
            rage_value = min(5, ferocity // 2)
            character.set_stat('pools', 'dual', 'Rage', rage_value, temp=False)
            character.set_stat('pools', 'dual', 'Rage', rage_value, temp=True)

        # Update Paradox based on Feast of Nettles
        if feast_level := character.get_stat('powers', 'special_advantage', 'Feast of Nettles', temp=False):
            paradox_values = {2: 3, 3: 5, 4: 10, 5: 15, 6: 20}
            if feast_level in paradox_values:
                character.set_stat('pools', 'dual', 'Paradox', paradox_values[feast_level], temp=False)
                character.set_stat('pools', 'dual', 'Paradox', 0, temp=True)

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
            return

        if "specialty" in self.switches:
            self.is_specialty = True
            try:
                if '=' not in self.args:
                    self.caller.msg("Usage: +selfstat/specialty <stat>=<specialty>")
                    return
                self.stat_name, self.specialty = self.args.split('=', 1)
                self.stat_name = self.stat_name.strip()
                self.specialty = self.specialty.strip()
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
                
            # Parse stat part for category and instance
            stat_part, self.value_change = self.args.split('=', 1)
            stat_part = stat_part.strip()
            self.value_change = self.value_change.strip()
            
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
        """
        Automatically detect the correct stat type and category for a given stat.
        Returns tuple of (category, stat_type) or a list of possible matches if ambiguous.
        """
        splat = self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower() if self.caller and hasattr(self.caller, 'db') else None
        if not stat_name:
            return None
        stat_name_lower = stat_name.lower()

        # Special handling for Nature and Demeanor archetypes
        if stat_name_lower in ['nature', 'demeanor']:
            # For Changelings, Nature and Demeanor are realms
            if splat == 'changeling':
                return ('powers', 'realm')
            else:
                # For all other splats, Nature and Demeanor are personal archetypes
                return ('archetype', 'personal')

        # Special handling for Arete/Enlightenment
        if stat_name_lower == 'arete' and splat == 'mage':
            return ('pools', 'advantage')
        if stat_name_lower == 'enlightenment' and splat == 'mage':
            return ('pools', 'advantage')

        # GIFTS FIRST UGH
        if stat_name_lower.startswith('gift:') or (self.stat_type and self.stat_type.lower() == 'gift'):
            # does this start with gift? 
            clean_name = stat_name_lower.replace('gift:', '').strip()
            
            # oh, so it did start with gift. let's clean up the name!
            search_name = clean_name if stat_name_lower.startswith('gift:') else stat_name_lower
            
            # are you sure you can use this one? let's check the database!
            gift_stat = Stat.objects.filter(
                name__iexact=search_name,
                category='powers',
                stat_type='gift'
            ).first()
            
            if gift_stat:
                # rule 1: you must be a shifter, possessed, or kinfolk to learn Gifts
                if splat != 'shifter' and splat != 'possessed' and splat != 'kinfolk':
                    self.caller.msg("Only Shifters, Possessed, and Kinfolk can learn Gifts.")
                    return None
                    
                # rule 2: you gotta set your Shifter Type first
                char_type = self.caller.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm')
                if not char_type:
                    self.caller.msg("You must set your Shifter Type before learning Gifts.")
                    return None

                # rule 2.5: you gotta be the right kind of shifter to learn this Gift
                if gift_stat.shifter_type and gift_stat.shifter_type.lower() not in ['', 'none']:
                    if isinstance(gift_stat.shifter_type, list):
                        if char_type.lower() not in [t.lower() for t in gift_stat.shifter_type]:
                            self.caller.msg(f"This Gift is only available to {', '.join(gift_stat.shifter_type)}s.")
                            return None
                    elif char_type.lower() != gift_stat.shifter_type.lower():
                        self.caller.msg(f"This Gift is only available to {gift_stat.shifter_type}s.")
                        return None

                # rule 3: what's your tribe?
                if gift_stat.tribe and gift_stat.tribe not in [[], None, ['none'], 'none']:
                    char_tribe = self.caller.db.stats.get('identity', {}).get('lineage', {}).get('Tribe', {}).get('perm')
                    if not char_tribe:
                        self.caller.msg("You must set your Tribe before learning tribal Gifts.")
                        return None
                    
                    # rule 3.5: oh god so many tribes
                    if isinstance(gift_stat.tribe, list):
                        if char_tribe.lower() not in [t.lower() for t in gift_stat.tribe]:
                            self.caller.msg(f"This Gift is only available to {', '.join(gift_stat.tribe)} tribes.")
                            return None
                    elif char_tribe.lower() != gift_stat.tribe.lower():
                        self.caller.msg(f"This Gift is only available to {gift_stat.tribe} tribe.")
                        return None

                # rule 4: what's your breed? are you breedable?
                if gift_stat.breed and gift_stat.breed.lower() not in ['', 'none']:
                    char_breed = self.caller.db.stats.get('identity', {}).get('lineage', {}).get('Breed', {}).get('perm')
                    if not char_breed:
                        self.caller.msg("You must set your Breed before learning breed Gifts.")
                        return None
                    
                    # i wish white wolf had just used 'metis', 'homid', and animal', across the board.
                    if isinstance(gift_stat.breed, list):
                        if char_breed.lower() not in [b.lower() for b in gift_stat.breed]:
                            self.caller.msg(f"This Gift is only available to {', '.join(gift_stat.breed)} breeds.")
                            return None
                    elif char_breed.lower() != gift_stat.breed.lower():
                        self.caller.msg(f"This Gift is only available to {gift_stat.breed} breed.")
                        return None

                # rule 5: what's your auspice?
                if gift_stat.auspice and gift_stat.auspice.lower() not in ['', 'none']:
                    char_auspice = self.caller.db.stats.get('identity', {}).get('lineage', {}).get('Auspice', {}).get('perm')
                    if not char_auspice:
                        self.caller.msg("You must set your Auspice before learning auspice Gifts.")
                        return None
                    
                    # rule 5.5: everyone's gotta be special apparently, check for different auspices since multiple groups use auspice.
                    # also consider adding aspect for later (ajaba, ratkin, etc)
                    if isinstance(gift_stat.auspice, list):
                        if char_auspice.lower() not in [a.lower() for a in gift_stat.auspice]:
                            self.caller.msg(f"This Gift is only available to {', '.join(gift_stat.auspice)} auspices.")
                            return None
                    elif char_auspice.lower() != gift_stat.auspice.lower():
                        self.caller.msg(f"This Gift is only available to {gift_stat.auspice} auspice.")
                        return None
                    
                return ('powers', 'gift')
            else:
                # *clippy voice* did u meaaaan?
                similar_gifts = Stat.objects.filter(
                    category='powers',
                    stat_type='gift'
                ).values_list('name', flat=True)
                similar_names = [name for name in similar_gifts if name.lower().startswith(search_name[0:3])]
                if similar_names:
                    self.caller.msg(f"Gift not found. Did you mean one of these? {', '.join(similar_names)}")
                return None

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
            'enlightenment': ('pools', 'advantage')
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
        if stat_name_lower in ['nature', 'demeanor']:
            # For Changelings, Nature and Demeanor are realms
            if splat == 'changeling':
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

        # If we get here, we found no matches
        return None

    def func(self):
        """This performs the actual command."""
        if not self.args:
            return self.display_stats()

        if not self.args.strip():
            self.caller.msg("Usage: +selfstat <stat>=<value>")
            return

        stat_name = self.lhs.strip()
        new_value = self.rhs.strip() if self.rhs else None

        # Handle stat removal (empty value)
        if new_value == '':
            # Get the category and type
            if not (self.category and self.stat_type):
                stat_info = self.detect_stat_category(stat_name)
                if not stat_info:
                    return
                self.category, self.stat_type = stat_info

            # Special handling for Nature and Demeanor
            if stat_name.lower() in ['nature', 'demeanor']:
                splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
                if splat and splat.lower() == 'changeling':
                    self.caller.set_stat('powers', 'realm', stat_name.title(), '', temp=False)
                    self.caller.set_stat('powers', 'realm', stat_name.title(), '', temp=True)
                else:
                    self.caller.set_stat('archetype', 'personal', stat_name.title(), '', temp=False)
                    self.caller.set_stat('archetype', 'personal', stat_name.title(), '', temp=True)
                self.caller.msg(f"Removed {stat_name.title()}.")
                return

            # Remove the stat
            self.caller.set_stat(self.category, self.stat_type, stat_name.title(), '', temp=False)
            self.caller.set_stat(self.category, self.stat_type, stat_name.title(), '', temp=True)
            self.caller.msg(f"Removed {stat_name.title()}.")
            return

        # Special handling for Nature and Demeanor
        if stat_name.lower() in ['nature', 'demeanor']:
            if self.handle_special_cases(stat_name, new_value):
                self.caller.msg(f"Set {stat_name.title()} to {new_value}.")
            return

        # Special handling for splat initialization
        if stat_name.lower() == 'splat':
            if not new_value:
                valid_splats = ['changeling', 'vampire', 'shifter', 'companion', 'mage', 'mortal', 'mortal+', 'possessed']
                splat_list = "\n".join([f"  - splat={s}" for s in valid_splats])
                self.caller.msg(f"Please specify a splat type using one of:\n{splat_list}")
                return
            
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

        # Special handling for Type (shifters, mortal+, possessed)
        if stat_name.lower() == 'type':
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            
            # Set the type
            self.caller.set_stat('identity', 'lineage', 'Type', new_value, temp=False)
            self.caller.set_stat('identity', 'lineage', 'Type', new_value, temp=True)
            self.caller.msg(f"Set Type to {new_value}.")
            
            # Initialize type-specific stats for Mortal+
            if splat and splat.lower() == 'mortal+':
                from world.wod20th.utils.mortalplus_utils import initialize_mortalplus_stats
                initialize_mortalplus_stats(self.caller, new_value)
            
            # Update banality based on new type
            splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
            new_banality = get_default_banality(splat, subtype=new_value)
            self.caller.set_stat('pools', 'dual', 'Banality', new_banality, temp=False)
            self.caller.set_stat('pools', 'dual', 'Banality', new_banality, temp=True)
            self.caller.msg(f"|yBanality adjusted to {new_banality} based on your type.|n")
            return

        if not self.caller.db.stats and stat_name.lower() != 'splat':
            self.caller.msg("Error: You don't have any stats initialized. Please create a character first using +selfstat splat=<type>")
            return

        # Let detect_stat_category determine the category and type
        stat_info = self.detect_stat_category(self.stat_name)
        if not stat_info:
            # Error message already shown by detect_stat_category
            return
        self.category, self.stat_type = stat_info

        # Handle Gifts first
        if self.category == 'powers' and self.stat_type == 'gift':
            # Get the Gift from the database
            gift_stat = Stat.objects.filter(
                name__iexact=self.stat_name,
                category='powers',
                stat_type='gift'
            ).first()
            
            if gift_stat:
                # validate me
                try:
                    value = int(new_value)
                    if not gift_stat.values or value not in gift_stat.values:
                        valid_values = ', '.join(str(v) for v in gift_stat.values)
                        self.caller.msg(f"Invalid value for {gift_stat.name}. Valid values are: {valid_values}")
                        return
                except ValueError:
                    self.caller.msg(f"Gift value must be a number. Got: {new_value}")
                    return
                
                # oh god you're gonna make me gift
                self.caller.set_stat('powers', 'gift', gift_stat.name, value, temp=False)
                self.caller.set_stat('powers', 'gift', gift_stat.name, value, temp=True)
                self.caller.msg(f"Set Gift: {gift_stat.name} to {value}.")

                return

        # Special handling for Generation which exists as both background and identity
        if self.stat_name.lower() == 'generation':
            splat = self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            if splat.lower() == 'vampire':
                # Check if character has a generation-affecting flaw
                for flaw_name, gen_value in GENERATION_FLAWS.items():
                    if self.caller.get_stat('flaws', 'flaw', flaw_name.title(), temp=False):
                        self.caller.msg(f"You cannot change your Generation while you have the {flaw_name.title()} flaw.")
                        return

                try:
                    # If it's a number, treat it as background points
                    gen_value = int(self.value_change)
                    if gen_value < 0 or gen_value > 7:
                        self.caller.msg("Generation background must be between 0 (13th gen) and 7 (6th gen).")
                        return
                    
                    # Set the background value
                    self.caller.set_stat('advantages', 'background', 'Generation', gen_value, temp=False)
                    self.caller.set_stat('advantages', 'background', 'Generation', gen_value, temp=True)
                    
                    # Set the identity value
                    gen_string = GENERATION_MAP[gen_value]
                    self.caller.set_stat('identity', 'lineage', 'Generation', gen_string, temp=False)
                    self.caller.set_stat('identity', 'lineage', 'Generation', gen_string, temp=True)
                    
                    # Update blood pool based on generation
                    blood_pool = calculate_blood_pool(gen_value)
                    self.caller.set_stat('pools', 'dual', 'Blood', blood_pool, temp=False)
                    self.caller.set_stat('pools', 'dual', 'Blood', blood_pool, temp=True)
                    
                    self.caller.msg(f"Set Generation background to {gen_value} ({gen_string}) and adjusted blood pool to {blood_pool}.")
                    return
                    
                except ValueError:
                    # If it's a string (like "8th"), validate it's a proper generation
                    gen_string = self.value_change.lower().strip()
                    if gen_string not in [v.lower() for v in GENERATION_MAP.values()]:
                        self.caller.msg("Invalid generation format. Must be a number 0-7 or a valid generation (6th-13th).")
                        return
                    
                    # Find the background value from the generation string
                    gen_value = [k for k, v in GENERATION_MAP.items() if v.lower() == gen_string][0]
                    
                    # Set both values
                    self.caller.set_stat('advantages', 'background', 'Generation', gen_value, temp=False)
                    self.caller.set_stat('advantages', 'background', 'Generation', gen_value, temp=True)
                    self.caller.set_stat('identity', 'lineage', 'Generation', gen_string.title(), temp=False)
                    self.caller.set_stat('identity', 'lineage', 'Generation', gen_string.title(), temp=True)
                    
                    # Update blood pool
                    blood_pool = calculate_blood_pool(gen_value)
                    self.caller.set_stat('pools', 'dual', 'Blood', blood_pool, temp=False)
                    self.caller.set_stat('pools', 'dual', 'Blood', blood_pool, temp=True)
                    
                    self.caller.msg(f"Set Generation to {gen_string.title()} (background value: {gen_value}) and adjusted blood pool to {blood_pool}.")
                    return

        # Convert value to integer if it's a numeric stat
        try:
            if isinstance(self.value_change, str):
                if self.value_change.startswith(('+', '-')):
                    current_value = self.caller.get_stat(self.category, self.stat_type, self.stat_name.title(), temp=False) or 0
                    new_value = current_value + int(self.value_change)
                else:
                    new_value = int(self.value_change) if self.value_change.isdigit() else self.value_change
            elif isinstance(self.value_change, (int, float)):
                new_value = int(self.value_change)
            else:
                new_value = self.value_change
        except (ValueError, TypeError):
            new_value = self.value_change

        # Check if the stat exists in the database
        from world.wod20th.utils.stat_initialization import check_stat_exists
        exists, similar_stats = check_stat_exists(self.stat_name, self.category, self.stat_type)
        if not exists:
            suggestions = f"\nDid you mean: {', '.join(similar_stats)}" if similar_stats else ""
            self.caller.msg(f"Error: Stat '{self.stat_name}' doesn't exist in the database.{suggestions}")
            return

        # Validate sphere access based on affiliation
        if self.category == 'powers' and self.stat_type == 'sphere':
            affiliation = self.caller.get_stat('identity', 'lineage', 'Affiliation', temp=False)
            
            # Define available spheres based on affiliation
            tradition_spheres = {
                'Correspondence', 'Entropy', 'Life', 'Matter', 'Time', 
                'Forces', 'Spirit', 'Prime', 'Mind'
            }
            technocracy_spheres = {
                'Data', 'Entropy', 'Life', 'Matter', 'Time',
                'Forces', 'Dimensional Science', 'Primal Utility', 'Mind'
            }
            
            if affiliation == 'Technocracy':
                if self.stat_name not in technocracy_spheres:
                    self.caller.msg(f"Error: {self.stat_name} is not a valid Technocratic methodology.")
                    return
            elif affiliation in ['Traditions', 'Nephandi', 'Orphan']:
                if self.stat_name not in tradition_spheres:
                    self.caller.msg(f"Error: {self.stat_name} is not a valid Sphere for {affiliation}.")
                    return

            # Validate sphere rating
            try:
                sphere_rating = int(new_value)
                if sphere_rating < 0 or sphere_rating > 5:
                    self.caller.msg("Error: Sphere ratings must be between 0 and 5.")
                    return
                
                # Check Arete limit
                arete = self.caller.get_stat('pools', 'advantage', 'Arete', temp=False) or 0
                if sphere_rating > arete:
                    self.caller.msg(f"Error: Cannot set {self.stat_name} higher than your Arete rating ({arete}).")
                    return
            except ValueError:
                self.caller.msg("Error: Sphere rating must be a number between 0 and 5.")
                return

        # Special handling for Type to ensure it's set in identity/lineage
        stat_name_lower = stat_name.lower()
        if stat_name_lower == 'type' and self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm') == 'Shifter':
            # Ensure the identity/lineage structure exists
            if 'identity' not in self.caller.db.stats:
                self.caller.db.stats['identity'] = {}
            if 'lineage' not in self.caller.db.stats['identity']:
                self.caller.db.stats['identity']['lineage'] = {}
            
            # Set Type in identity/lineage
            if 'Type' not in self.caller.db.stats['identity']['lineage']:
                self.caller.db.stats['identity']['lineage']['Type'] = {}
            
            # Store the Type value
            self.caller.db.stats['identity']['lineage']['Type'] = {'perm': new_value, 'temp': new_value}
            
            # Initialize identity stats based on type
            shifter_identity_stats = {
                'Garou': {
                    'lineage': ['Breed', 'Auspice', 'Tribe', 'Camp', 'Deed Name'],
                    'personal': ['Totem']
                },
                'Rokea': {
                    'lineage': ['Breed', 'Auspice', 'Tribe', 'Deed Name'],
                    'personal': ['Totem']
                },
                'Ajaba': {
                    'lineage': ['Breed', 'Aspect', 'Faction', 'Deed Name'],
                    'personal': ['Totem']
                },
                'Ananasi': {
                    'lineage': ['Breed', 'Aspect', 'Faction', 'Cabal', 'Deed Name'],
                    'personal': ['Totem']
                },
                'Gurahl': {
                    'lineage': ['Breed', 'Auspice', 'Tribe', 'Deed Name'],
                    'personal': ['Totem']
                },
                'Kitsune': {
                    'lineage': ['Breed', 'Path', 'Faction', 'Deed Name'],
                    'personal': ['Totem']
                },
                'Mokole': {
                    'lineage': ['Breed', 'Auspice', 'Stream', 'Varna', 'Deed Name'],
                    'personal': ['Totem']
                },
                'Ratkin': {
                    'lineage': ['Breed', 'Aspect', 'Plague', 'Deed Name'],
                    'personal': ['Totem']
                },
                'Nagah': {
                    'lineage': ['Breed', 'Auspice', 'Crown', 'Deed Name'],
                    'personal': ['Totem']
                },
                'Bastet': {
                    'lineage': ['Breed', 'Tribe', 'Deed Name'],
                    'personal': ['Totem']
                },
                'Nuwisha': {
                    'lineage': ['Breed', 'Deed Name'],
                    'personal': ['Totem']
                },
                'Corax': {
                    'lineage': ['Breed', 'Deed Name'],
                    'personal': ['Totem']
                }
            }

            if new_value in shifter_identity_stats:
                stats = shifter_identity_stats[new_value]
                # Initialize lineage stats
                for stat in stats.get('lineage', []):
                    self.caller.set_stat('identity', 'lineage', stat, '', temp=False)
                    self.caller.set_stat('identity', 'lineage', stat, '', temp=True)
                # Initialize personal stats
                for stat in stats.get('personal', []):
                    self.caller.set_stat('identity', 'personal', stat, '', temp=False)
                    self.caller.set_stat('identity', 'personal', stat, '', temp=True)

            # Initialize renown based on shifter type
            shifter_renown = {
                "Ajaba": ["Cunning", "Ferocity", "Obligation"],
                "Ananasi": ["Cunning", "Obedience", "Wisdom"],
                "Bastet": ["Cunning", "Ferocity", "Honor"],
                "Corax": ["Glory", "Honor", "Wisdom"],
                "Garou": ["Glory", "Honor", "Wisdom"],
                "Gurahl": ["Honor", "Succor", "Wisdom"],
                "Kitsune": ["Cunning", "Honor", "Glory"],
                "Mokole": ["Glory", "Honor", "Wisdom"],
                "Nagah": [],  # Nagah don't use Renown
                "Nuwisha": ["Humor", "Glory", "Cunning"],
                "Ratkin": ["Infamy", "Obligation", "Cunning"],
                "Rokea": ["Valor", "Harmony", "Innovation"]
            }

            # Clear existing renown
            if 'advantages' in self.caller.db.stats and 'renown' in self.caller.db.stats['advantages']:
                self.caller.db.stats['advantages']['renown'] = {}

            # Set new renown types
            if new_value in shifter_renown:
                for renown_type in shifter_renown[new_value]:
                    self.caller.set_stat('advantages', 'renown', renown_type, 0, temp=False)
                    self.caller.set_stat('advantages', 'renown', renown_type, 0, temp=True)

            # Set default pools based on type
            default_pools = {
                'Ajaba': {'willpower': 3},
                'Ananasi': {'willpower': 3, 'gnosis': 1},  # Breed will modify these
                'Bastet': {'willpower': 3},  # Tribe will modify these
                'Corax': {'willpower': 3, 'rage': 1, 'gnosis': 6},
                'Garou': {'willpower': 3},  # Tribe/Auspice/Breed will modify these
                'Gurahl': {'willpower': 6},  # Breed will modify others
                'Kitsune': {'willpower': 5},  # Path/Breed will modify others
                'Mokole': {'willpower': 3},  # Auspice/Breed/Varna will modify these
                'Nagah': {'willpower': 4},  # Breed/Auspice will modify others
                'Nuwisha': {'willpower': 4, 'gnosis': 1},  # Breed will modify these
                'Ratkin': {'willpower': 3},  # Aspect/Breed will modify others
                'Rokea': {'willpower': 4}  # Auspice/Breed will modify others
            }

            if new_value in default_pools:
                pools = default_pools[new_value]
                for pool_name, value in pools.items():
                    self.caller.set_stat('pools', 'dual', pool_name.title(), value, temp=False)
                    self.caller.set_stat('pools', 'dual', pool_name.title(), value, temp=True)
                    self.caller.msg(f"Set {pool_name.title()} to {value}.")

                # Special handling for Ananasi blood pool
                if new_value == 'Ananasi':
                    self.caller.set_stat('pools', 'dual', 'Blood', 10, temp=False)
                    self.caller.set_stat('pools', 'dual', 'Blood', 10, temp=True)
                    self.caller.msg("Set Blood Pool to 10.")
            return
        
        # Set the stat normally
        self.caller.set_stat(self.category, self.stat_type, self.stat_name.title(), new_value, temp=False)
        self.caller.set_stat(self.category, self.stat_type, self.stat_name.title(), new_value, temp=True)
        
        # Show message for the stat change
        self.caller.msg(f"Set {self.stat_name.title()} to {new_value}.")

        # Handle special cases and updates
        self.handle_special_cases(self.stat_name, new_value)

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
                self.caller.set_stat('powers', 'realm', stat_name.title(), proper_case, temp=False)
                self.caller.set_stat('powers', 'realm', stat_name.title(), proper_case, temp=True)
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
            if splat in ['Vampire', 'Mortal', 'Mortal+']:
                courage_value = int(new_value)
                self.caller.set_stat('pools', 'dual', 'Willpower', courage_value, temp=False)
                self.caller.set_stat('pools', 'dual', 'Willpower', courage_value, temp=True)
                self.caller.msg(f"Updated Willpower to {courage_value} based on Courage.")

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

        # Update pools for certain powers
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
                    'feline': 5,  # Bastet animal-born
                    'squamus': 5,  # Rokea animal-born
                    'ursine': 5,  # Gurahl animal-born
                    'latrani': 5,  # Nuwisha animal-born
                    'rodens': 5,  # Ratkin animal-born
                    'corvid': 5,  # Corax animal-born
                    'balaram': 1,  # Nagah homid
                    'suchid': 4,  # Mokole animal-born
                    'ahi': 5,  # Nagah animal-born
                    'arachnid': 5,  # Ananasi animal-born
                    'kojin': 3,  # Kitsune homid
                    'roko': 5,  # Kitsune animal-born
                    'shinju': 4  # Kitsune metis
                }

                # Set Gnosis based on breed
                breed_lower = new_value.lower()
                if breed_lower in common_breed_gnosis:
                    self.caller.set_stat('pools', 'dual', 'Gnosis', common_breed_gnosis[breed_lower], temp=False)
                    self.caller.set_stat('pools', 'dual', 'Gnosis', common_breed_gnosis[breed_lower], temp=True)
                    self.caller.msg(f"Set Gnosis to {common_breed_gnosis[breed_lower]} based on breed.")

        # Handle Bastet tribe-based stats
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

        # Handle Garou tribe-based Willpower
        elif stat_name_lower == 'tribe' and self.caller.get_stat('identity', 'lineage', 'Type', temp=False) == 'Garou':
            garou_tribe_willpower = {
                'black furies': 3,
                'bone gnawers': 4,
                'children of gaia': 4,
                'fianna': 3,
                'get of fenris': 3,
                'glass walkers': 3,
                'red talons': 3,
                'shadow lords': 3,
                'silent striders': 3,
                'silver fangs': 3,
                'stargazers': 4,
                'uktena': 3,
                'wendigo': 4
            }
            
            tribe_lower = new_value.lower()
            if tribe_lower in garou_tribe_willpower:
                willpower = garou_tribe_willpower[tribe_lower]
                self.caller.set_stat('pools', 'dual', 'Willpower', willpower, temp=False)
                self.caller.set_stat('pools', 'dual', 'Willpower', willpower, temp=True)
                self.caller.msg(f"Set Willpower to {willpower} based on tribe.")

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
