from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.search import search_object
from django.db import models
from typing import Dict, List, Union
from itertools import zip_longest

# Import models
from world.wod20th.models import Stat, CharacterSheet, CharacterImage
from typeclasses.characters import Character

# Import utility functions and constants
from world.wod20th.utils.stat_mappings import CATEGORIES, STAT_TYPES
from world.wod20th.utils.shifter_utils import (
    SHIFTER_IDENTITY_STATS, SHIFTER_RENOWN, SHIFTER_TYPE_CHOICES, AUSPICE_CHOICES,
    BASTET_TRIBE_CHOICES, BREED_CHOICES, GAROU_TRIBE_CHOICES,
    initialize_shifter_type
)
from world.wod20th.utils.vampire_utils import (
    CLAN, get_clan_disciplines, initialize_vampire_stats, calculate_blood_pool
)
from world.wod20th.utils.mage_utils import (
    AFFILIATION, MAGE_SPHERES, TRADITION, TRADITION_SUBFACTION,
    CONVENTION, METHODOLOGIES, NEPHANDI_FACTION, initialize_mage_stats
)
from world.wod20th.utils.changeling_utils import (
    SEEMING, KITH, SEELIE_LEGACIES, UNSEELIE_LEGACIES,
    ARTS, REALMS, initialize_changeling_stats
)
from world.wod20th.utils.mortalplus_utils import (
    MORTALPLUS_TYPE_CHOICES, MORTALPLUS_TYPES, MORTALPLUS_POOLS,
    MORTALPLUS_POWERS, initialize_mortalplus_stats,
    validate_mortalplus_powers, can_learn_power
)
from world.wod20th.utils.possessed_utils import (
    POSSESSED_TYPE_CHOICES, POSSESSED_TYPES, POSSESSED_POOLS,
    initialize_possessed_stats
)
from world.wod20th.utils.companion_utils import (
    COMPANION_TYPES, POWER_SOURCE_TYPES, COMPANION_POWERS,
    initialize_companion_stats
)
from world.wod20th.utils.virtue_utils import (
    calculate_willpower, calculate_road, PATH_VIRTUES
)
from world.wod20th.utils.damage import (
    format_damage, format_status, format_damage_stacked, 
    calculate_total_health_levels
)
from world.wod20th.utils.formatting import (
    format_stat, header, footer, divider
)

class CmdSheet(MuxCommand):
    """
    Show a sheet of the character.
    """
    key = "sheet"
    aliases = ["sh"]
    help_category = "Chargen & Character Info"

    def __init__(self):
        """Initialize command."""
        super().__init__()
        self.advantages_list = []
        self.pools_list = []
        self.powers_list = []
        self.virtues_list = []

    def set_stat_both(self, character, category, stat_type, stat_name, value):
        """Set both permanent and temporary values for a stat."""
        character.set_stat(category, stat_type, stat_name, value, temp=False)
        character.set_stat(category, stat_type, stat_name, value, temp=True)

    def initialize_mortalplus_stats(self, character, mortalplus_type):
        """Initialize stats specific to Mortal+ types."""
        if not mortalplus_type:
            return []  # Return empty list instead of undefined powers
            
        powers = []  # Initialize powers list
        
        # Set the type properly
        self.set_stat_both(character, 'identity', 'lineage', 'Mortal+ Type', mortalplus_type)
            
        # Initialize powers category if it doesn't exist
        if 'powers' not in character.db.stats:
            character.db.stats['powers'] = {}
            
        # Initialize pools
        if mortalplus_type in MORTALPLUS_POOLS:
            for pool_name, pool_data in MORTALPLUS_POOLS[mortalplus_type].items():
                self.set_stat_both(character, 'pools', 'dual', pool_name, pool_data['default'])

        mortalplus_type = character.get_stat('identity', 'lineage', 'Mortal+ Type', temp=False)
        if not mortalplus_type:
            return powers

        # Add powers section based on type
        if mortalplus_type in MORTALPLUS_TYPES:
            power_types = MORTALPLUS_TYPES[mortalplus_type]
            for power_type in power_types:
                power_type_lower = power_type.lower()
                powers.append(divider(power_type, width=38, color="|b"))
                
                # Get the powers from the correct location in the stats dictionary
                powers_dict = character.db.stats.get('powers', {}).get(power_type_lower, {})
                if powers_dict:
                    for power, values in sorted(powers_dict.items()):
                        power_value = values.get('perm', 0)
                        powers.append(format_stat(power, power_value, default=0, width=38))
                else:
                    powers.append(" None".ljust(38))

            # Special handling for Sorcerer hedge rituals
            if mortalplus_type == 'Sorcerer':
                powers.append(divider("Hedge Rituals", width=38, color="|b"))
                hedge_rituals = character.db.stats.get('powers', {}).get('hedge_ritual', {})
                if hedge_rituals:
                    for ritual, values in sorted(hedge_rituals.items()):
                        ritual_value = values.get('perm', 0)
                        powers.append(format_stat(ritual, ritual_value, default=0, width=38))
                else:
                    powers.append(" None".ljust(38))

        return powers

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

    def calculate_health_bonuses(self, character):
        """Calculate bonus health levels for a character."""
        # Use the centralized health calculation from damage.py
        return calculate_total_health_levels(character)

    def func(self):
        """Execute the command."""
        # Initialize lists at the start of the function
        self.pools_list = [divider("Pools", width=25, fillchar=" ")]
        self.virtues_list = [divider("Virtues", width=25, fillchar=" ")]
        self.status_list = [divider("Health & Status", width=25, fillchar=" ")]
        powers = []

        name = self.args.strip()
        if not name:
            name = self.caller.key

        # First try direct name match (with quiet=True to suppress error message)
        chars = self.caller.search(name, global_search=True,
                                 typeclass='typeclasses.characters.Character',
                                 quiet=True)

        # Handle if search returns a list
        character = chars[0] if isinstance(chars, list) else chars

        # If no direct match, try alias
        if not character:
            character = Character.get_by_alias(name.lower())

        if not character:
            self.caller.msg(f"Character '{name}' not found.")
            return

        # Modify permission check - allow builders/admins to view any sheet
        if not (self.caller.check_permstring("builders") or self.caller.check_permstring("storyteller")):
            if self.caller != character:
                self.caller.msg(f"|rYou can't see the sheet of {character.key}.|n")
                return

        # Check if character has stats and splat initialized
        if not character.db.stats or not character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm'):
            self.caller.msg("|rYou must set a splat to initialize your sheet. Use +selfstat splat=<Splat> or ask staff to set it.|n")
            return

        try:
            splat = character.get_stat('other', 'splat', 'Splat')
        except AttributeError:
            self.caller.msg("|rError accessing character stats. Please contact staff.|n")
            return

        if not splat:
            splat = "Mortal"

        # Start building the character sheet
        string = header(f"Character Sheet for:|n {character.get_display_name(self.caller)}")

        # Add Identity section
        string += self.format_identity_section(character, splat)

        # Add Attributes section
        string += self.format_attributes_section(character)

        # Add Abilities section
        string += self.format_abilities_section(character)

        # Add Secondary Abilities section
        string += self.format_secondary_abilities_section(character)

        # Process powers and advantages in two columns
        string += header("Advantages", width=78, color="|y")
        
        powers = []
        left_column = []

        # Process backgrounds
        left_column.append(divider("Backgrounds", width=38, color="|b"))
        char_backgrounds = character.db.stats.get('backgrounds', {}).get('background', {})
        for background, values in sorted(char_backgrounds.items()):
            background_value = values.get('perm', 0)
            left_column.append(format_stat(background, background_value, width=38))

        # Add a blank line between sections
        left_column.append(" " * 38)

        # Process merits
        left_column.append(divider("Merits", width=38, color="|b"))
        merits = character.db.stats.get('merits', {})
        for merit_type, merit_dict in sorted(merits.items()):
            for merit, values in sorted(merit_dict.items()):
                merit_value = values.get('perm', 0)
                left_column.append(format_stat(merit, merit_value, width=38))

        # Add a blank line between sections
        left_column.append(" " * 38)

        # Process flaws
        left_column.append(divider("Flaws", width=38, color="|b"))
        flaws = character.db.stats.get('flaws', {})
        for flaw_type, flaw_dict in sorted(flaws.items()):
            for flaw, values in sorted(flaw_dict.items()):
                flaw_value = values.get('perm', 0)
                left_column.append(format_stat(flaw, flaw_value, width=38))

        # Process powers based on character splat
        character_splat = character.get_stat('other', 'splat', 'Splat', temp=False)

        # Process powers based on splat type
        if character_splat == 'Mage':
            powers = self.process_mage_powers(character, powers)
        elif character_splat == 'Vampire':
            powers = self.process_vampire_powers(character, powers)
        elif character_splat == 'Changeling':
            powers = self.process_changeling_powers(character, powers)
        elif character_splat == 'Possessed':
            powers = self.process_possessed_powers(character, powers)
        elif character_splat == 'Shifter':
            powers = self.process_shifter_powers(character, powers)
        elif character_splat == 'Companion':
            powers = self.process_companion_powers(character, powers)
        else:  # Mortal, Mortal+, or any other splat
            powers = self.process_powers(character, powers)

        # Ensure both columns have the same number of rows
        max_len = max(len(powers), len(left_column))
        powers.extend([""] * (max_len - len(powers)))
        left_column.extend([""] * (max_len - len(left_column)))

        # Combine columns with new widths (38+38 = 76 total width with 2 spaces between)
        for left, power in zip(left_column, powers):
            # Don't strip ANSI-formatted strings
            if isinstance(left, str) and ("|x" in left or "|n" in left):
                left_part = left
            else:
                left_part = left.strip().ljust(38)
                
            if isinstance(power, str) and ("|x" in power or "|n" in power):
                right_part = power
            else:
                right_part = power.strip().ljust(38)
                
            string += f"{left_part}  {right_part}\n"

        # Display Pools, Virtues & Status
        string += header("Pools, Virtues & Status", width=78, color="|y")

        # Process pools
        self.process_pools(character)

        # Calculate health bonuses before getting health status
        bonus_health = self.calculate_health_bonuses(character)

        # Add health status to status_list without extra padding
        health_status = format_damage_stacked(character)
        self.status_list.extend(health_status)

        # Handle virtues
        self.process_virtues(character, character_splat)

        # Ensure all columns have the same number of rows
        max_len = max(len(self.pools_list), len(self.virtues_list), len(self.status_list))
        self.pools_list.extend(["".ljust(25)] * (max_len - len(self.pools_list)))
        self.virtues_list.extend(["".ljust(25)] * (max_len - len(self.virtues_list)))
        self.status_list.extend(["".ljust(25)] * (max_len - len(self.status_list)))

        # Display the pools, virtues and status in columns with adjusted spacing
        for pool, virtue, status in zip(self.pools_list, self.virtues_list, self.status_list):
            string += f"{pool:<25}  {virtue:>25}  {status}\n"

        # Check approval status and add it at the end
        if character.db.approved:
            string += header("Approved Character", width=78, fillchar="-")
        else:
            string += header("Unapproved Character", width=78, fillchar="-")

        # Send the complete sheet to the caller
        self.caller.msg(string)

    def process_vampire_powers(self, character, powers):
        """Process powers section for Vampire characters."""
        # Process all standard power types first
        powers = self.process_powers(character, powers)
        
        # Add Disciplines section
        powers.append(divider("Disciplines", width=38, color="|b"))
        disciplines = character.db.stats.get('powers', {}).get('discipline', {})
        for discipline, values in sorted(disciplines.items()):
            discipline_value = values.get('perm', 0)
            powers.append(format_stat(discipline, discipline_value, default=0, width=38))
        
        # Add Combo Disciplines section if they exist
        combo_disciplines = character.db.stats.get('powers', {}).get('combodiscipline', {})
        if combo_disciplines:
            powers.append(" " * 38)  # Add spacing
            powers.append(divider("Combo Disciplines", width=38, color="|b"))
            for combo, values in sorted(combo_disciplines.items()):
                combo_value = values.get('perm', 0)
                powers.append(format_stat(combo, combo_value, default=0, width=38))
        
        # Add Thaumaturgy Paths section if they exist
        thaumaturgy = character.db.stats.get('powers', {}).get('thaumaturgy', {})
        if thaumaturgy:
            powers.append(" " * 38)  # Add spacing
            powers.append(divider("Thaumaturgy Paths", width=38, color="|b"))
            for path, values in sorted(thaumaturgy.items()):
                path_value = values.get('perm', 0)
                powers.append(format_stat(path, path_value, default=0, width=38))
        
        # Add Thaumaturgy Rituals section if they exist
        rituals = character.db.stats.get('powers', {}).get('thaum_ritual', {})
        if rituals:
            powers.append(" " * 38)  # Add spacing
            powers.append(divider("Thaumaturgy Rituals", width=38, color="|b"))
            for ritual, values in sorted(rituals.items()):
                ritual_value = values.get('perm', 0)
                powers.append(format_stat(ritual, ritual_value, default=0, width=38))
        
        return powers

    def process_changeling_powers(self, character, powers):
        """Process powers section for Changeling characters."""
        # Process all standard power types first
        powers = self.process_powers(character, powers)
        
        # Get character's kith and phyla
        kith = character.get_stat('identity', 'lineage', 'Kith', temp=False)
        phyla = character.get_stat('identity', 'lineage', 'Phyla', temp=False)
        
        if kith == 'Inanimae':
            # Add Slivers section for all Inanimae
            powers.append(divider("Slivers", width=38, color="|b"))
            slivers = character.db.stats.get('powers', {}).get('sliver', {})
            if slivers:
                has_slivers = False
                for sliver, values in sorted(slivers.items()):
                    sliver_value = values.get('perm', 0)
                    if sliver_value > 0:
                        has_slivers = True
                        powers.append(format_stat(sliver, sliver_value, default=0, width=38))
                if not has_slivers:
                    powers.append(" None".ljust(38))
            else:
                powers.append(" None".ljust(38))
            
            # Add Arts section ONLY for Mannikins
            if phyla == 'Mannikins':
                powers.append(divider("Arts", width=38, color="|b"))
                arts = character.db.stats.get('powers', {}).get('art', {})
                if arts:
                    has_arts = False
                    for art, values in sorted(arts.items()):
                        art_value = values.get('perm', 0)
                        if art_value > 0:
                            has_arts = True
                            powers.append(format_stat(art, art_value, default=0, width=38))
                    if not has_arts:
                        powers.append(" None".ljust(38))
                else:
                    powers.append(" None".ljust(38))
        else:
            # Regular Changeling powers
            powers.append(divider("Arts", width=38, color="|b"))
            arts = character.db.stats.get('powers', {}).get('art', {})
            has_arts = False
            for art, values in sorted(arts.items()):
                art_value = values.get('perm', 0)
                if art_value > 0:
                    has_arts = True
                    powers.append(format_stat(art, art_value, default=0, width=38))
            if not has_arts:
                powers.append(" None".ljust(38))
            
            powers.append(divider("Realms", width=38, color="|b"))
            realms = character.db.stats.get('powers', {}).get('realm', {})
            has_realms = False
            for realm, values in sorted(realms.items()):
                realm_value = values.get('perm', 0)
                if realm_value > 0:
                    has_realms = True
                    powers.append(format_stat(realm, realm_value, default=0, width=38))
            if not has_realms:
                powers.append(" None".ljust(38))
        
        return powers

    def process_shifter_powers(self, character, powers):
        """Process powers section for Shifter characters."""
        # Process all standard power types first
        powers = self.process_powers(character, powers)
        
        # Add any additional shifter-specific powers here if needed
        return powers

    def process_mage_powers(self, character, powers):
        """Process powers section for Mage characters."""
        # Process all standard power types first
        powers = self.process_powers(character, powers)
        
        # Add Spheres section
        powers.append(divider("Spheres", width=38, color="|b"))
        spheres = character.db.stats.get('powers', {}).get('sphere', {})
        for sphere, values in sorted(spheres.items()):
            sphere_value = values.get('perm', 0)
            powers.append(format_stat(sphere, sphere_value, default=0, width=38))
        
        return powers

    def process_possessed_powers(self, character, powers):
        """Process powers section for Possessed characters."""
        # Process all standard power types first
        powers = self.process_powers(character, powers)
        
        # Add any additional possessed-specific powers here if needed
        return powers

    def process_companion_powers(self, character, powers):
        """Process powers section for Companion characters."""
        # Process all standard power types first
        powers = self.process_powers(character, powers)
        
        # Add any additional companion-specific powers here if needed
        return powers

    def process_virtues(self, character, character_splat):
        """Process virtues section for character display."""
        if character_splat.lower() == 'shifter':
            # Get shifter type
            shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
            if shifter_type:
                # Define renown types for each shifter type
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

                # Get renown types for this shifter type
                renown_types = shifter_renown.get(shifter_type, [])
                
                # Display each renown type
                for renown in renown_types:
                    renown_value = character.get_stat('advantages', 'renown', renown, temp=False) or 0
                    self.virtues_list.append(format_stat(renown, renown_value, width=25))

        elif character_splat.lower() == 'mage':
            # Handle mage virtues (synergy)
            synergy_virtues = ['Dynamic', 'Entropic', 'Static']
            for virtue in synergy_virtues:
                virtue_value = character.get_stat('virtues', 'synergy', virtue, temp=False) or 0
                self.virtues_list.append(format_stat(virtue, virtue_value, width=25))
            
            # Add Resonance
            resonance_value = character.get_stat('pools', 'resonance', 'Resonance', temp=False) or 0
            self.virtues_list.append(format_stat('Resonance', resonance_value, width=25))

        elif character_splat.lower() == 'changeling':
            # Get Nightmare and Willpower Imbalance from pools.other
            nightmare = character.get_stat('pools', 'other', 'Nightmare', temp=False)
            if nightmare is None:
                nightmare = 0
            willpower_imbalance = character.get_stat('pools', 'other', 'Willpower Imbalance', temp=False)
            if willpower_imbalance is None:
                willpower_imbalance = 0
            
            # Add Nightmare and Willpower Imbalance to virtues section
            self.virtues_list.extend([
                format_stat('Nightmare', str(nightmare), width=25),
                format_stat('Willpower Imbalance', str(willpower_imbalance), width=25)
            ])

        else:  # Vampire, Mortal, Mortal+, etc.
            # Get the character's path/road value
            if character_splat.lower() == 'vampire':
                road_value = calculate_road(character)
                self.virtues_list.append(format_stat('Road', road_value, width=25))

            # Get the character's virtues based on path
            path = character.get_stat('identity', 'personal', 'Enlightenment')
            if path not in PATH_VIRTUES:
                path = 'Humanity'  # Default to Humanity virtues
            
            virtue1, virtue2 = PATH_VIRTUES[path]
            virtues = character.db.stats.get('virtues', {}).get('moral', {})
            
            # Display virtues in order: first two virtues from path, then Courage
            for virtue in [virtue1, virtue2, 'Courage']:
                virtue_value = virtues.get(virtue, {}).get('perm', 0)
                self.virtues_list.append(format_stat(virtue, virtue_value, width=25))

            # Calculate and update Willpower if needed
            willpower = calculate_willpower(character)
            if willpower != character.get_stat('pools', 'dual', 'Willpower', temp=False):
                character.set_stat('pools', 'dual', 'Willpower', willpower, temp=False)
                character.set_stat('pools', 'dual', 'Willpower', willpower, temp=True)

    def process_powers(self, character, powers):
        """Process all power types for the character."""
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        if not splat:
            return

        # Process powers based on splat
        if splat.lower() == 'vampire':
            # Process disciplines
            disciplines = character.db.stats.get('powers', {}).get('discipline', {})
            if disciplines:
                powers.append(divider("Disciplines", width=38, color="|b"))
                for discipline, values in sorted(disciplines.items()):
                    discipline_value = values.get('perm', 0)
                    powers.append(format_stat(discipline, discipline_value, default=0, width=38))

        elif splat.lower() == 'mage':
            # Process spheres
            spheres = character.db.stats.get('powers', {}).get('sphere', {})
            if spheres:
                powers.append(divider("Spheres", width=38, color="|b"))
                for sphere, values in sorted(spheres.items()):
                    sphere_value = values.get('perm', 0)
                    powers.append(format_stat(sphere, sphere_value, default=0, width=38))

        elif splat.lower() == 'changeling':
            # Process arts
            arts = character.db.stats.get('powers', {}).get('art', {})
            if arts:
                powers.append(divider("Arts", width=38, color="|b"))
                for art, values in sorted(arts.items()):
                    art_value = values.get('perm', 0)
                    powers.append(format_stat(art, art_value, default=0, width=38))

            # Process realms
            realms = character.db.stats.get('powers', {}).get('realm', {})
            if realms:
                powers.append(divider("Realms", width=38, color="|b"))
                for realm, values in sorted(realms.items()):
                    realm_value = values.get('perm', 0)
                    powers.append(format_stat(realm, realm_value, default=0, width=38))

        elif splat.lower() == 'possessed':
            # Process blessings
            blessings = character.db.stats.get('powers', {}).get('blessing', {})
            if blessings:
                powers.append(divider("Blessings", width=38, color="|b"))
                for blessing, values in sorted(blessings.items()):
                    blessing_value = values.get('perm', 0)
                    powers.append(format_stat(blessing, blessing_value, default=0, width=38))

            # Process charms
            charms = character.db.stats.get('powers', {}).get('charm', {})
            if charms:
                powers.append(divider("Charms", width=38, color="|b"))
                for charm, values in sorted(charms.items()):
                    charm_value = values.get('perm', 0)
                    powers.append(format_stat(charm, charm_value, default=0, width=38))

            # Process gifts
            gifts = character.db.stats.get('powers', {}).get('gift', {})
            if gifts:
                powers.append(divider("Gifts", width=38, color="|b"))
                for gift, values in sorted(gifts.items()):
                    gift_value = values.get('perm', 0)
                    powers.append(format_stat(gift, gift_value, default=0, width=38))

        elif splat.lower() == 'mortal+':
            mortalplus_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
            if mortalplus_type:
                if mortalplus_type.lower() == 'ghoul':
                    # Process disciplines
                    disciplines = character.db.stats.get('powers', {}).get('discipline', {})
                    if disciplines:
                        powers.append(divider("Disciplines", width=38, color="|b"))
                        for discipline, values in sorted(disciplines.items()):
                            discipline_value = values.get('perm', 0)
                            powers.append(format_stat(discipline, discipline_value, default=0, width=38))

                elif mortalplus_type.lower() == 'kinfolk':
                    # Process gifts
                    gifts = character.db.stats.get('powers', {}).get('gift', {})
                    if gifts:
                        powers.append(divider("Gifts", width=38, color="|b"))
                        for gift, values in sorted(gifts.items()):
                            gift_value = values.get('perm', 0)
                            powers.append(format_stat(gift, gift_value, default=0, width=38))

                elif mortalplus_type.lower() == 'kinain':
                    # Process arts
                    arts = character.db.stats.get('powers', {}).get('art', {})
                    if arts:
                        powers.append(divider("Arts", width=38, color="|b"))
                        for art, values in sorted(arts.items()):
                            art_value = values.get('perm', 0)
                            powers.append(format_stat(art, art_value, default=0, width=38))

                        # Process realms
                        realms = character.db.stats.get('powers', {}).get('realm', {})
                        if realms:
                            powers.append(divider("Realms", width=38, color="|b"))
                            for realm, values in sorted(realms.items()):
                                realm_value = values.get('perm', 0)
                                powers.append(format_stat(realm, realm_value, default=0, width=38))

                elif mortalplus_type.lower() == 'sorcerer':
                    # Process sorcery
                    sorcery = character.db.stats.get('powers', {}).get('sorcery', {})
                    if sorcery:
                        powers.append(divider("Sorcery", width=38, color="|b"))
                        for power, values in sorted(sorcery.items()):
                            power_value = values.get('perm', 0)
                            powers.append(format_stat(power, power_value, default=0, width=38))

                    # Process hedge rituals
                    hedge_rituals = character.db.stats.get('powers', {}).get('hedge_ritual', {})
                    if hedge_rituals:
                        powers.append(divider("Hedge Rituals", width=38, color="|b"))
                        for ritual, values in sorted(hedge_rituals.items()):
                            ritual_value = values.get('perm', 0)
                            powers.append(format_stat(ritual, ritual_value, default=0, width=38))

                elif mortalplus_type.lower() == 'psychic':
                    # Process numina
                    numina = character.db.stats.get('powers', {}).get('numina', {})
                    if numina:
                        powers.append(divider("Numina", width=38, color="|b"))
                        for power, values in sorted(numina.items()):
                            power_value = values.get('perm', 0)
                            powers.append(format_stat(power, power_value, default=0, width=38))

                elif mortalplus_type.lower() == 'faithful':
                    # Process faith
                    faith = character.db.stats.get('powers', {}).get('faith', {})
                    if faith:
                        powers.append(divider("Faith", width=38, color="|b"))
                        for power, values in sorted(faith.items()):
                            power_value = values.get('perm', 0)
                            powers.append(format_stat(power, power_value, default=0, width=38))

        elif splat == 'companion':
            # Process special advantages
            special_advantages = character.db.stats.get('powers', {}).get('special_advantage', {})
            if special_advantages:
                powers.append(divider("Special Advantages", width=38, color="|b"))
                for advantage, values in sorted(special_advantages.items()):
                    advantage_value = values.get('perm', 0)
                    powers.append(format_stat(advantage, advantage_value, default=0, width=38))

        return powers


    def get_identity_stats(self, character, splat):
        """Get the list of identity stats to display based on splat."""
        # Base stats for all splats
        base_stats = ['Full Name', 'Concept']

        # Add splat-specific stats
        if splat.lower() == 'vampire':
            stats = base_stats + [
                'Nature', 'Demeanor',
                'Date of Birth', 'Date of Embrace',
                'Generation', 'Sire',
                'Clan', 'Enlightenment'
            ]
        elif splat.lower() == 'changeling':
            stats = base_stats + [
                'Seelie Legacy', 'Unseelie Legacy',
                'Kith'
            ]
            # Add Phyla for Inanimae after Kith
            kith = character.get_stat('identity', 'lineage', 'Kith', temp=False)
            if kith == 'Inanimae':
                stats.append('Phyla')
            stats.extend(['Seeming', 'House'])

        elif splat.lower() == 'mage':
            stats = base_stats + [
                'Nature', 'Demeanor',
                'Essence', 'Signature',
                'Affinity Sphere', 'Affiliation'
            ]
            # Add affiliation-specific stats
            affiliation = character.get_stat('identity', 'lineage', 'Affiliation', temp=False)
            if affiliation:
                if affiliation.lower() == 'traditions':
                    stats.extend(['Tradition', 'Traditions Subfaction'])
                elif affiliation.lower() == 'technocracy':
                    stats.extend(['Convention', 'Methodology'])
                elif affiliation.lower() == 'nephandi':
                    stats.append('Nephandi Faction')

        elif splat.lower() == 'shifter':
            stats = base_stats + [
                'Nature', 'Demeanor',
                'Type'
            ]
            # Add type-specific stats
            shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
            if shifter_type:
                stats.append('Breed')  # Common to all shifters
                if shifter_type == 'Garou':
                    stats.extend(['Auspice', 'Tribe', 'Camp', 'Deed Name'])
                elif shifter_type == 'Rokea':
                    stats.extend(['Auspice', 'Tribe', 'Deed Name'])
                elif shifter_type == 'Ajaba':
                    stats.extend(['Aspect', 'Faction', 'Deed Name'])
                elif shifter_type == 'Ananasi':
                    stats.extend(['Aspect', 'Faction', 'Cabal', 'Deed Name'])
                elif shifter_type == 'Gurahl':
                    stats.extend(['Auspice', 'Tribe', 'Deed Name'])
                elif shifter_type == 'Kitsune':
                    stats.extend(['Path', 'Faction', 'Deed Name'])
                elif shifter_type == 'Mokole':
                    stats.extend(['Auspice', 'Stream', 'Varna', 'Deed Name'])
                elif shifter_type == 'Ratkin':
                    stats.extend(['Aspect', 'Plague', 'Deed Name'])
                elif shifter_type == 'Nagah':
                    stats.extend(['Auspice', 'Crown', 'Deed Name'])
                elif shifter_type == 'Bastet':
                    stats.extend(['Tribe', 'Deed Name'])
                elif shifter_type in ['Nuwisha', 'Corax']:
                    stats.append('Deed Name')

        elif splat.lower() == 'mortal+':
            stats = base_stats + [
                'Nature', 'Demeanor',
                'Date of Birth', 'Type'
            ]
            # Add type-specific stats
            mortalplus_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
            if mortalplus_type:
                if mortalplus_type.lower() == 'ghoul':
                    stats.extend(['Domitor', 'Clan'])
                elif mortalplus_type.lower() == 'kinfolk':
                    stats.append('Tribe')
                elif mortalplus_type.lower() == 'kinain':
                    stats.extend(['House', 'Kith'])
                elif mortalplus_type.lower() == 'sorcerer':
                    stats.extend(['Fellowship'])
                elif mortalplus_type.lower() == 'psychic':
                    stats.extend(['Fellowship'])

        elif splat.lower() == 'possessed':
            stats = base_stats + [
                'Nature', 'Demeanor',
                'Date of Birth', 'Type'
            ]
            # Add type-specific stats
            possessed_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
            if possessed_type:
                if possessed_type.lower() == 'fomori':
                    stats.append('Bane Type')
                elif possessed_type.lower() == 'kami':
                    stats.append('Gaian Spirit')
                stats.extend(['Date of Possession', 'Spirit Name'])

        elif splat.lower() == 'companion':
            stats = base_stats + [
                'Nature', 'Demeanor',
                'Companion Type', 'Affiliation', 'Motivation'
            ]

        else:  # Mortal or other
            stats = base_stats + [
                'Nature', 'Demeanor',
                'Date of Birth'
            ]

        # Add Splat at the end
        stats.append('Splat')

        return stats

    def get_stat_value(self, character, stat):
        """Get the value of a stat from the appropriate location."""
        # Special handling for Type
        if stat == 'Type':
            value = character.get_stat('identity', 'lineage', 'Type', temp=False)
            if isinstance(value, dict):
                return value.get('perm', '')
            return value or ''
            
        # Check personal stats first
        value = character.get_stat('identity', 'personal', stat, temp=False)
        
        # For Phyla, check both locations
        if not value and stat == 'Phyla':
            value = (character.get_stat('identity', 'phyla', 'Phyla', temp=False) or 
                    character.get_stat('identity', 'lineage', 'Phyla', temp=False))
        
        # For Legacies, check legacy location
        elif stat in ['Seelie Legacy', 'Unseelie Legacy']:
            value = character.get_stat('identity', 'legacy', stat, temp=False)
        
        # Check lineage stats
        if not value:
            value = character.get_stat('identity', 'lineage', stat, temp=False)
            
        # Special handling for Rank
        if not value and stat == 'Rank':
            value = '0'
            
        # Check other stats
        if not value:
            value = character.get_stat('identity', 'other', stat, temp=False)
            
        # Check splat
        if not value and stat == 'Splat':
            value = character.get_stat('other', 'splat', 'Splat', temp=False)
            
        # Check Nature and Demeanor
        if not value and stat == 'Nature':
            value = (character.get_stat('archetype', 'personal', 'Nature', temp=False) or
                    character.get_stat('archetype', 'personal', 'Nature', temp=True))
        elif not value and stat == 'Demeanor':
            value = (character.get_stat('archetype', 'personal', 'Demeanor', temp=False) or
                    character.get_stat('archetype', 'personal', 'Demeanor', temp=True))
            
        return value

    def format_stat_with_dots(self, stat, value, width=38):
        """Format a stat with dots for display."""
        display_stat = 'Subfaction' if stat == 'Traditions Subfaction' else stat
        display_stat = 'Possessed Type' if stat == 'possessed_type' else display_stat
        stat_str = f" {display_stat}"

        # Handle dictionary values
        if isinstance(value, dict):
            # Handle nested dictionaries (e.g., {'Splat': {'perm': 'Vampire', 'temp': 'Vampire'}})
            if any(isinstance(v, dict) for v in value.values()):
                for key, val in value.items():
                    if isinstance(val, dict) and 'perm' in val:
                        value = val.get('perm', '')
                        break
            else:
                # Handle simple dictionaries (e.g., {'perm': 'Vampire', 'temp': 'Vampire'})
                value = value.get('perm', '')

        # Handle empty/None/zero values for identity stats
        if value is None or value == '' or (isinstance(value, (int, float)) and value == 0):
            if stat == 'Rank':  # Special case for Rank
                value_str = '0'
            elif stat in ['Full Name', 'Date of Birth', 'Date of Embrace', 'Concept', 'Nature', 'Demeanor', 
                         'Clan', 'Generation', 'Sire', 'Enlightenment', 'Kith', 'Seeming', 'House', 
                         'Seelie Legacy', 'Unseelie Legacy', 'Type', 'Tribe', 'Breed', 'Auspice', 
                         'Tradition', 'Convention', 'Affiliation', 'Phyla', 'Traditions Subfaction', 'Methodology',
                         'Spirit Name', 'Domitor', 'Society', 'Order', 'Coven', 'Cabal', 'Plague', 'Crown', 
                         'Bane Type', 'Gaian Spirit', 'Stream', 'Path', 'Varna', 'Deed Name', 'Motivation',
                         'Possessed Type', 'Date of Possession', 'Companion Type']:
                value_str = 'None'
            else:
                value_str = ''
        else:
            value_str = str(value)

        # Calculate dots needed for spacing
        dots = "." * (width - len(stat_str) - len(value_str))    
        return f"{stat_str}|x{dots}|n{value_str}"

    def format_identity_section(self, character, splat):
        """Format the identity section of the character sheet."""
        string = header("Identity", width=78, color="|y")
        all_stats = self.get_identity_stats(character, splat)

        # Format stats in two columns
        for i in range(0, len(all_stats), 2):
            left_stat = all_stats[i]
            right_stat = all_stats[i+1] if i+1 < len(all_stats) else None

            left_value = self.get_stat_value(character, left_stat)
            left_formatted = self.format_stat_with_dots(left_stat, left_value)

            if right_stat:
                right_value = self.get_stat_value(character, right_stat)
                right_formatted = self.format_stat_with_dots(right_stat, right_value)
                string += f"{left_formatted}  {right_formatted}\n"
            else:
                string += f"{left_formatted}\n"

        return string

    def format_attributes_section(self, character):
        """Format the attributes section of the character sheet."""
        string = header("Attributes", width=78, color="|y")
        string += " " + divider("Physical", width=25, fillchar=" ") + " "
        string += divider("Social", width=25, fillchar=" ") + " "
        string += divider("Mental", width=25, fillchar=" ") + "\n"

        # Format each row of attributes
        rows = [
            (
                ('Strength', 'physical'), 
                ('Charisma', 'social'), 
                ('Perception', 'mental')
            ),
            (
                ('Dexterity', 'physical'), 
                ('Manipulation', 'social'), 
                ('Intelligence', 'mental')
            ),
            (
                ('Stamina', 'physical'), 
                ('Appearance', 'social'), 
                ('Wits', 'mental')
            )
        ]

        # Special handling for Appearance
        zero_appearance_clans = ['nosferatu', 'samedi']
        clan = character.get_stat('identity', 'lineage', 'Clan', temp=False) or ''
        is_zero_appearance_clan = clan.lower() in zero_appearance_clans

        current_form = character.db.current_form if hasattr(character.db, 'current_form') else None
        zero_appearance_forms = ['crinos', 'anthros', 'arthren', 'sokto', 'chatro']
        is_zero_appearance_form = current_form and current_form.lower() in zero_appearance_forms

        for row in rows:
            row_string = ""
            for attr, category in row:
                if attr == 'Appearance' and (is_zero_appearance_clan or is_zero_appearance_form):
                    row_string += format_stat(attr, 0, default=0, tempvalue=0, allow_zero=True, width=25)
                else:
                    value = character.db.stats.get('attributes', {}).get(category, {}).get(attr, {}).get('perm', 1)
                    temp_value = character.db.stats.get('attributes', {}).get(category, {}).get(attr, {}).get('temp', value)
                    row_string += format_stat(attr, value, default=1, tempvalue=temp_value, width=25)
                
                # Add padding for mental attributes
                if category == 'mental':
                    row_string = row_string.ljust(len(row_string) + 1)
                else:
                    row_string += " "
            string += row_string + "\n"

        return string

    def format_ability(self, character, ability, category):
        """Format a single ability with appropriate padding."""
        value = character.get_stat('abilities', category, ability.name)
        formatted = format_stat(ability.name, value, default=0)
        if category in ['knowledge']:
            return " " * 1 + formatted.ljust(22)
        return formatted.ljust(25)

    def get_abilities_for_splat(self, character, stat_type):
        """Get abilities for a specific splat and stat type."""
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
        clan = character.get_stat('identity', 'lineage', 'Clan', temp=False)

        # Define base abilities for each category
        BASE_ABILITIES = {
            'talent': ['Alertness', 'Athletics', 'Awareness', 'Brawl', 'Empathy', 
                      'Expression', 'Intimidation', 'Leadership', 'Streetwise', 'Subterfuge'],
            'skill': ['Animal Ken', 'Crafts', 'Drive', 'Etiquette', 'Firearms', 
                     'Larceny', 'Melee', 'Performance', 'Stealth', 'Survival', 'Technology'],
            'knowledge': ['Academics', 'Computer', 'Cosmology', 'Enigmas', 'Finance', 'Investigation', 
                        'Law', 'Medicine', 'Occult', 'Politics', 'Science']
        }
        
        # Get base abilities first
        abilities = list(Stat.objects.filter(
            category='abilities',
            stat_type=stat_type,
            name__in=BASE_ABILITIES[stat_type]
        ).order_by('name'))
        
        # Add splat-specific abilities
        if splat == 'Shifter':
            if stat_type == 'talent':
                # Add Primal-Urge for all shifters
                primal_urge = Stat.objects.filter(name='Primal-Urge').first()
                if primal_urge:
                    # Insert Primal-Urge in alphabetical order
                    insert_index = next((i for i, ability in enumerate(abilities) 
                                       if ability.name > 'Primal-Urge'), len(abilities))
                    abilities.insert(insert_index, primal_urge)
                
                # Add Flight ONLY for specific shifter types
                if shifter_type and shifter_type.strip() in ['Corax', 'Camazotz', 'Mokole']:
                    flight = Stat.objects.filter(name='Flight').first()
                    if flight:
                        # Insert Flight in alphabetical order
                        insert_index = next((i for i, ability in enumerate(abilities) 
                                           if ability.name > 'Flight'), len(abilities))
                        abilities.insert(insert_index, flight)
            
            elif stat_type == 'knowledge':
                # Add Rituals for all shifters
                rituals = Stat.objects.filter(name='Rituals').first()
                if rituals:
                    # Insert Rituals in alphabetical order
                    insert_index = next((i for i, ability in enumerate(abilities) 
                                       if ability.name > 'Rituals'), len(abilities))
                    abilities.insert(insert_index, rituals)
        
        # Add Flight for Gargoyle vampires
        elif splat == 'Vampire' and clan and clan.strip() == 'Gargoyle' and stat_type == 'talent':
            flight = Stat.objects.filter(name='Flight').first()
            if flight:
                # Insert Flight in alphabetical order
                insert_index = next((i for i, ability in enumerate(abilities) 
                                   if ability.name > 'Flight'), len(abilities))
                abilities.insert(insert_index, flight)
        
        elif splat == 'Companion' and stat_type == 'special_advantage':
            # Check if the companion has Wings special advantage
            wings_value = character.get_stat('powers', 'special_advantage', 'Wings', temp=False)
            if wings_value > 0:
                # Add Flight ability for winged companions
                flight = Stat.objects.filter(name='Flight').first()
                if flight:
                    # Insert Flight in alphabetical order
                    insert_index = next((i for i, ability in enumerate(abilities) 
                                       if ability.name > 'Flight'), len(abilities))
                    abilities.insert(insert_index, flight)
            
            # Add base Companion ability
            companion = Stat.objects.filter(name='Companion').first()
            if companion:
                abilities.append(companion)

        elif splat == 'Changeling':
            if stat_type == 'talent':
                # Add Kenning for Changelings
                kenning = Stat.objects.filter(name='Kenning').first()
                if kenning:
                    # Insert Kenning in alphabetical order
                    insert_index = next((i for i, ability in enumerate(abilities) 
                                       if ability.name > 'Kenning'), len(abilities))
                    abilities.insert(insert_index, kenning)
            elif stat_type == 'knowledge':
                # Add Gremayre for Changelings
                gremayre = Stat.objects.filter(name='Gremayre').first()
                if gremayre:
                    # Insert Gremayre in alphabetical order
                    insert_index = next((i for i, ability in enumerate(abilities) 
                                       if ability.name > 'Gremayre'), len(abilities))
                    abilities.insert(insert_index, gremayre)

        return abilities

    def format_abilities_section(self, character):
        """Format the abilities section of the character sheet."""
        string = header("Abilities", width=78, color="|y")
        string += " " + divider("Talents", width=25, fillchar=" ") + " "
        string += divider("Skills", width=25, fillchar=" ") + " "
        string += divider("Knowledges", width=25, fillchar=" ") + "\n"

        # Get abilities for each category
        talents = self.get_abilities_for_splat(character, 'talent')
        skills = self.get_abilities_for_splat(character, 'skill')
        knowledges = self.get_abilities_for_splat(character, 'knowledge')

        # Format abilities with padding for skills and knowledges
        formatted_talents = [self.format_ability(character, talent, 'talent') for talent in talents]
        formatted_skills = [self.format_ability(character, skill, 'skill') for skill in skills]
        formatted_knowledges = [self.format_ability(character, knowledge, 'knowledge') for knowledge in knowledges]

        # Add specialties
        ability_lists = [
            (formatted_talents, talents, 'talent'),
            (formatted_skills, skills, 'skill'),
            (formatted_knowledges, knowledges, 'knowledge')
        ]

        for formatted_list, ability_list, ability_type in ability_lists:
            for ability in ability_list:
                if character.db.specialties and ability.name in character.db.specialties:
                    for specialty in character.db.specialties[ability.name]:
                        formatted_list.append(self.format_ability(character, Stat(name=f"`{specialty}"), ability_type))

        # Ensure all columns have the same length
        max_len = max(len(formatted_talents), len(formatted_skills), len(formatted_knowledges))
        formatted_talents.extend([" " * 25] * (max_len - len(formatted_talents)))
        formatted_skills.extend([" " * 25] * (max_len - len(formatted_skills)))
        formatted_knowledges.extend([" " * 25] * (max_len - len(formatted_knowledges)))

        # Combine columns
        for talent, skill, knowledge in zip(formatted_talents, formatted_skills, formatted_knowledges):
            string += f"{talent}{skill}{knowledge}\n"

        return string

    def format_secondary_abilities_section(self, character):
        """Format the secondary abilities section of the character sheet."""
        string = header("Secondary Abilities", width=78, color="|y")
        string += " " + divider("Talents", width=25, fillchar=" ") + " "
        string += divider("Skills", width=25, fillchar=" ") + " "
        string += divider("Knowledges", width=25, fillchar=" ") + "\n"

        # Base secondary abilities for all characters
        base_secondary_talents = ['Artistry', 'Carousing', 'Diplomacy', 'Intrigue', 'Mimicry', 'Scrounging', 'Seduction', 'Style']
        base_secondary_skills = ['Archery', 'Fencing', 'Fortune-Telling', 'Gambling', 'Jury-Rigging', 'Pilot', 'Torture']
        base_secondary_knowledges = ['Area Knowledge', 'Cultural Savvy', 'Demolitions', 'Herbalism', 'Media', 'Power-Brokering', 'Vice']

        # Get splat-specific secondary abilities
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        if splat in ['Mage', 'mage']:
            base_secondary_talents.extend(['Blatancy', 'Flying', 'High Ritual', 'Lucid Dreaming'])
            base_secondary_skills.extend(['Biotech', 'Do', 'Energy Weapons', 'Helmsman', 'Microgravity Ops'])
            base_secondary_knowledges.extend(['Cybernetics', 'Hypertech', 'Paraphysics', 'Xenobiology'])

        # Format abilities with values from character stats
        formatted_secondary_talents = []
        formatted_secondary_skills = []
        formatted_secondary_knowledges = []

        # Get the secondary abilities from the character's stats
        secondary_abilities = character.db.stats.get('secondary_abilities', {})
        none_category = character.db.stats.get(None, {})

        # Process talents
        for talent in sorted(base_secondary_talents):
            value = 0
            # Check in secondary_abilities first
            if 'secondary_talent' in secondary_abilities:
                value = secondary_abilities['secondary_talent'].get(talent, {}).get('perm', 0)
            # If not found and exists in None category, use that value
            if value == 0 and 'secondary_talent' in none_category:
                value = none_category['secondary_talent'].get(talent, {}).get('perm', 0)
            formatted_secondary_talents.append(format_stat(talent, value, default=0, width=25))

        # Process skills
        for skill in sorted(base_secondary_skills):
            value = 0
            if 'secondary_skill' in secondary_abilities:
                value = secondary_abilities['secondary_skill'].get(skill, {}).get('perm', 0)
            if value == 0 and 'secondary_skill' in none_category:
                value = none_category['secondary_skill'].get(skill, {}).get('perm', 0)
            formatted_secondary_skills.append(format_stat(skill, value, default=0, width=25))

        # Process knowledges
        for knowledge in sorted(base_secondary_knowledges):
            value = 0
            if 'secondary_knowledge' in secondary_abilities:
                value = secondary_abilities['secondary_knowledge'].get(knowledge, {}).get('perm', 0)
            if value == 0 and 'secondary_knowledge' in none_category:
                value = none_category['secondary_knowledge'].get(knowledge, {}).get('perm', 0)
            formatted_secondary_knowledges.append(format_stat(knowledge, value, default=0, width=25))

        # Ensure all columns have the same length
        max_len = max(len(formatted_secondary_talents), len(formatted_secondary_skills), len(formatted_secondary_knowledges))
        formatted_secondary_talents.extend([" " * 25] * (max_len - len(formatted_secondary_talents)))
        formatted_secondary_skills.extend([" " * 25] * (max_len - len(formatted_secondary_skills)))
        formatted_secondary_knowledges.extend([" " * 25] * (max_len - len(formatted_secondary_knowledges)))

        # Combine columns
        for talent, skill, knowledge in zip(formatted_secondary_talents, formatted_secondary_skills, formatted_secondary_knowledges):
            string += f"{talent}{skill}{knowledge}\n"

        return string

    def process_changeling_pools_and_virtues(self, character):
        """Process pools and virtues section for Changeling characters."""
        # Add standard pools
        self.pools_list.extend([
            format_stat('Willpower', format_pool_value(character, 'Willpower'), width=25),
            format_stat('Glamour', format_pool_value(character, 'Glamour'), width=25),
            format_stat('Banality', format_pool_value(character, 'Banality'), width=25)
        ])
        
        # Note: Virtues (Nightmare and Willpower Imbalance) are now handled in process_virtues

    def process_shifter_pools_and_virtues(self, character):
        """Process pools and virtues section for Shifter characters."""
        shifter_type = character.get_stat('identity', 'lineage', 'Type')
        
        # Handle Ananasi differently
        if shifter_type == 'Ananasi':
            self.pools_list.extend([
                format_stat('Blood', format_pool_value(character, 'Blood'), width=25),
                format_stat('Gnosis', format_pool_value(character, 'Gnosis'), width=25),
                format_stat('Willpower', format_pool_value(character, 'Willpower'), width=25)
            ])
        else:
            # Standard shifter pools
            self.pools_list.extend([
                format_stat('Rage', format_pool_value(character, 'Rage'), width=25),
                format_stat('Gnosis', format_pool_value(character, 'Gnosis'), width=25),
                format_stat('Willpower', format_pool_value(character, 'Willpower'), width=25)
            ])
        
        # Add Banality if it exists
        banality = character.get_stat('pools', 'dual', 'Banality', temp=False)
        if banality is not None:
            self.pools_list.append(format_stat('Banality', format_pool_value(character, 'Banality'), width=25))
        
        # Handle Renown based on shifter type
        shifter_type = character.get_stat('identity', 'lineage', 'Type')
        if shifter_type in SHIFTER_RENOWN:
            for renown in SHIFTER_RENOWN[shifter_type]:
                renown_value = character.get_stat('advantages', 'renown', renown, temp=False) or 0
                dots = "." * (19 - len(renown))
                self.virtues_list.append(f" {renown}{dots}{renown_value}".ljust(25))
        else:
            # Default to Garou renown if type not found or not set
            default_renown = ['Glory', 'Honor', 'Wisdom']
            for renown in default_renown:
                renown_value = character.get_stat('advantages', 'renown', renown, temp=False) or 0
                dots = "." * (19 - len(renown))
                self.virtues_list.append(f" {renown}{dots}{renown_value}".ljust(25))

    def process_mage_pools_and_virtues(self, character):
        """Process pools and virtues section for Mage characters."""
        # Get Avatar/Genius rating and set Quintessence accordingly
        avatar_value = character.get_stat('backgrounds', 'background', 'Avatar', temp=False) or \
                      character.get_stat('backgrounds', 'background', 'Genius', temp=False) or 0
        
        # Set Quintessence to match Avatar rating
        character.set_stat('pools', 'dual', 'Quintessence', avatar_value, temp=False)
        character.set_stat('pools', 'dual', 'Quintessence', avatar_value, temp=True)

        # Check if character is a Technocrat
        affiliation = character.get_stat('identity', 'lineage', 'Affiliation', temp=False)
        if affiliation == 'Technocracy' or affiliation == 'technocracy':
            self.pools_list.extend([
                format_stat('Enlightenment', format_pool_value(character, 'Enlightenment'), width=25),
                format_stat('Quintessence', format_pool_value(character, 'Quintessence'), width=25),
                format_stat('Willpower', format_pool_value(character, 'Willpower'), width=25)
            ])
        else:
            # Use Arete for non-Technocrats
            self.pools_list.extend([
                format_stat('Arete', format_pool_value(character, 'Arete'), width=25),
                format_stat('Quintessence', format_pool_value(character, 'Quintessence'), width=25),
                format_stat('Willpower', format_pool_value(character, 'Willpower'), width=25)
            ])

        # Add Banality if it exists
        banality = character.get_stat('pools', 'dual', 'Banality', temp=False)
        if banality is not None:
            self.pools_list.append(format_stat('Banality', format_pool_value(character, 'Banality'), width=25))

        # Add virtues
        synergy_virtues = ['Dynamic', 'Entropic', 'Static']
        for virtue in synergy_virtues:
            virtue_value = character.get_stat('virtues', 'synergy', virtue, temp=False) or 0
            dots = "." * (19 - len(virtue))
            self.virtues_list.append(f" {virtue}{dots}{virtue_value}".ljust(25))
        
        # Add Resonance
        resonance_value = character.get_stat('pools', 'resonance', 'Resonance', temp=False) or 0
        dots = "." * (19 - len('Resonance'))
        self.virtues_list.append(f" Resonance{dots}{resonance_value}".ljust(25))

    def process_possessed_pools(self, character):
        """Process pools section for Possessed characters."""
        # Initialize pools if not already set
        self.initialize_possessed_stats(character)
        
        # Add pools in order
        self.pools_list.extend([
            format_stat('Willpower', format_pool_value(character, 'Willpower'), width=25),
            format_stat('Gnosis', format_pool_value(character, 'Gnosis'), width=25),
            format_stat('Rage', format_pool_value(character, 'Rage'), width=25)
        ])
        
        # Add Banality if it exists
        banality = character.get_stat('pools', 'dual', 'Banality', temp=False)
        if banality is not None:
            self.pools_list.append(format_stat('Banality', format_pool_value(character, 'Banality'), width=25))

    def process_pools(self, character):
        """Process pools section for all character types."""
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        if not splat:
            return

        def get_pool_value(pool_name, stat_type='dual'):
            """Helper function to get pool values from stats dictionary."""
            if stat_type == 'dual':
                pool_stats = character.db.stats.get('pools', {}).get('dual', {}).get(pool_name, {})
                perm = pool_stats.get('perm', 0)
                temp = pool_stats.get('temp', perm)
                return f"{temp}/{perm}" if perm != temp else str(perm)
            elif stat_type == 'advantage':
                pool_stats = character.db.stats.get('pools', {}).get('advantage', {}).get(pool_name, {})
                value = pool_stats.get('perm', 0)
                return str(value)
        
        # Common pools for all splats
        self.pools_list.append(format_stat('Willpower', get_pool_value('Willpower'), width=25))
        
        # Splat-specific pools
        if splat == 'Vampire' or splat == 'vampire':
            self.pools_list.append(format_stat('Blood Pool', get_pool_value('Blood'), width=25))
            
        elif splat == 'Mage' or splat == 'mage':
            # Get Avatar/Genius rating and set Quintessence accordingly
            avatar_value = character.get_stat('backgrounds', 'background', 'Avatar', temp=False) or \
                          character.get_stat('backgrounds', 'background', 'Genius', temp=False) or 0
            
            # Set Quintessence to match Avatar rating
            character.set_stat('pools', 'dual', 'Quintessence', avatar_value, temp=False)
            character.set_stat('pools', 'dual', 'Quintessence', avatar_value, temp=True)

            # Check if character is a Technocrat
            affiliation = character.get_stat('identity', 'lineage', 'Affiliation', temp=False)
            if affiliation == 'Technocracy' or affiliation == 'technocracy':
                self.pools_list.append(format_stat('Enlightenment', get_pool_value('Enlightenment', 'advantage'), width=25))
            else:
                self.pools_list.append(format_stat('Arete', get_pool_value('Arete', 'advantage'), width=25))
            self.pools_list.append(format_stat('Quintessence', get_pool_value('Quintessence'), width=25))
            self.pools_list.append(format_stat('Paradox', get_pool_value('Paradox'), width=25))
            
        elif splat == 'Changeling' or splat == 'changeling':
            self.pools_list.extend([
                format_stat('Glamour', get_pool_value('Glamour'), width=25),
                format_stat('Banality', get_pool_value('Banality'), width=25)
            ])
            
        elif splat == 'Shifter' or splat == 'shifter':
            shifter_type = character.get_stat('identity', 'lineage', 'Type')
            
            # Handle Ananasi differently
            if shifter_type == 'Ananasi':
                self.pools_list.extend([
                    format_stat('Blood', get_pool_value('Blood'), width=25),
                    format_stat('Gnosis', get_pool_value('Gnosis'), width=25)
                ])
            else:
                # Standard shifter pools
                self.pools_list.extend([
                    format_stat('Rage', get_pool_value('Rage'), width=25),
                    format_stat('Gnosis', get_pool_value('Gnosis'), width=25)
                ])
            
        elif splat == 'Mortal+' or splat == 'mortal+':
            mortalplus_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
            if mortalplus_type:
                mortalplus_type = mortalplus_type.lower()
                if mortalplus_type == 'ghoul':
                    # Ghouls get 3 blood points
                    character.set_stat('pools', 'dual', 'Blood', 3, temp=False)
                    character.set_stat('pools', 'dual', 'Blood', 3, temp=True)
                    self.pools_list.append(format_stat('Blood', get_pool_value('Blood'), width=25))
                
                elif mortalplus_type == 'kinain':
                    # Kinain get 2 glamour points
                    character.set_stat('pools', 'dual', 'Glamour', 2, temp=False)
                    character.set_stat('pools', 'dual', 'Glamour', 2, temp=True)
                    self.pools_list.append(format_stat('Glamour', get_pool_value('Glamour'), width=25))
                    self.pools_list.append(format_stat('Banality', get_pool_value('Banality'), width=25))
                
                elif mortalplus_type == 'kinfolk':
                    # Get Gnosis merit value and set pool
                    gnosis_merit = character.get_stat('merits', 'supernatural', 'Gnosis', temp=False)
                    if gnosis_merit:
                        merit_value = gnosis_merit.get('perm', 0)
                        gnosis_value = 3 if merit_value >= 7 else (2 if merit_value >= 6 else (1 if merit_value >= 5 else 0))
                        character.set_stat('pools', 'dual', 'Gnosis', gnosis_value, temp=False)
                        character.set_stat('pools', 'dual', 'Gnosis', gnosis_value, temp=True)
                        self.pools_list.append(format_stat('Gnosis', get_pool_value('Gnosis'), width=25))
                
                elif mortalplus_type == 'sorcerer':
                    # Set Mana equal to Techne rating
                    techne_value = character.get_stat('backgrounds', 'background', 'Techne', temp=False) or 0
                    character.set_stat('pools', 'dual', 'Mana', techne_value, temp=False)
                    character.set_stat('pools', 'dual', 'Mana', techne_value, temp=True)
                    self.pools_list.append(format_stat('Mana', get_pool_value('Mana'), width=25))

                elif mortalplus_type == 'psychic':
                    self.pools_list.append(format_stat('Mana', get_pool_value('Mana'), width=25))

        elif splat.lower() == 'companion':
            # Check companion type for Familiar
            companion_type = character.get_stat('identity', 'lineage', 'Companion Type', temp=False)
            if companion_type and companion_type.lower() == 'familiar':
                self.pools_list.append(format_stat('Essence', get_pool_value('Essence'), width=25))
            
            # Check for Ferocity special advantage
            special_advantages = character.db.stats.get('powers', {}).get('special_advantage', {})
            if special_advantages and 'Ferocity' in special_advantages:
                self.pools_list.append(format_stat('Rage', get_pool_value('Rage'), width=25))


def format_pool_value(character, pool_name):
    """Format a pool value with both permanent and temporary values."""
    perm = character.get_stat('pools', 'dual', pool_name, temp=False)
    temp = character.get_stat('pools', 'dual', pool_name, temp=True)

    if perm is None:
        perm = 0
    if temp is None:
        temp = perm

    return f"{temp}/{perm}" if temp != perm else str(perm)