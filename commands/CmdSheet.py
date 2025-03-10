"""
Command module for displaying character sheets.
This command allows players to view their own character sheets or those of others
(with appropriate permissions).
"""
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.search import search_object
from django.db import models
from typing import Dict, List, Union
from itertools import zip_longest
from evennia.utils.ansi import strip_ansi
from world.wod20th.utils.sheet_constants import KNOWLEDGES, SECONDARY_KNOWLEDGES, SECONDARY_SKILLS, SECONDARY_TALENTS, SKILLS, TALENTS
from typeclasses.characters import Character
from utils.search_helpers import search_character
# Core utilities
from world.wod20th.utils.formatting import format_stat, header, footer, divider, format_abilities, format_secondary_abilities
from world.wod20th.utils.virtue_utils import calculate_willpower, calculate_path, PATH_VIRTUES
from world.wod20th.utils.damage import format_damage, format_status, format_damage_stacked, calculate_total_health_levels
from world.wod20th.utils.stat_initialization import find_similar_stats, check_stat_exists
from world.wod20th.utils.banality import get_banality_message

# Splat-specific utilities
from world.wod20th.utils.vampire_utils import get_clan_disciplines, initialize_vampire_stats, calculate_blood_pool, get_vampire_identity_stats
from world.wod20th.utils.mage_utils import initialize_mage_stats
from world.wod20th.utils.shifter_utils import initialize_shifter_type, SHIFTER_IDENTITY_STATS
from world.wod20th.utils.changeling_utils import initialize_changeling_stats, get_changeling_identity_stats
from world.wod20th.utils.mortalplus_utils import initialize_mortalplus_stats, get_mortalplus_identity_stats
from world.wod20th.utils.possessed_utils import initialize_possessed_stats
from world.wod20th.utils.companion_utils import initialize_companion_stats


# Constants and mappings
from world.wod20th.utils.stat_mappings import (
    CATEGORIES, STAT_TYPES, STAT_TYPE_TO_CATEGORY,
    IDENTITY_STATS, SPLAT_STAT_OVERRIDES,
    POOL_TYPES, POWER_CATEGORIES, ABILITY_TYPES,
    ATTRIBUTE_CATEGORIES, SPECIAL_ADVANTAGES,
    VALID_SPLATS, VALID_DATES, get_identity_stats
)

class CmdSheet(MuxCommand):
    """
    Show character sheet information.
    
    Usage:
      sheet [<character>]
      sh [<character>]
      
    Displays the character sheet for yourself or another character
    (if you have permission to view it). The sheet includes all
    relevant stats, abilities, powers, and status information
    organized by category.
    
    If no character is specified, shows your own sheet.
    """
    key = "+sheet"
    aliases = ["sh"]
    help_category = "Character Info"
    locks = "cmd:all()"  # Everyone can use this command

    POWERS_WIDTH = 35  # Reduced from 35 to ensure proper spacing
        
    def __init__(self):
        super().__init__()
        # Initialize lists for sheet sections
        self.pools_list = []
        self.virtues_list = []
        self.status_list = []
        self.powers_list = []
        self.left_column = []
        
    def reset_lists(self):
        """Reset all section lists to their initial state."""
        self.pools_list = [divider("Pools", width=25, fillchar=" ")]
        self.virtues_list = [divider("Virtues", width=25, fillchar=" ")]
        self.status_list = [divider("Health & Status", width=25, fillchar=" ")]
        self.powers_list = []
        self.left_column = []

    def get_character(self, name=None):
        """
        Get character by name or return caller if no name provided.
        
        Args:
            name (str, optional): Name of character to look up
            
        Returns:
            Character or None: Found character or None if not found
        """
        if not name:
            return self.caller
            
        # Use our search_character helper
        return search_character(self.caller, name)

    def can_view_sheet(self, character):
        """
        Check if caller has permission to view the character sheet.
        
        Args:
            character (Character): Character whose sheet is being viewed
            
        Returns:
            bool: True if caller can view sheet, False otherwise
        """
        # Staff can always view sheets
        if self.caller.check_permstring("builders") or self.caller.check_permstring("storyteller"):
            return True
            
        # Players can view their own sheets
        return self.caller == character
        
    def validate_character(self, character):
        """
        Validate that character exists and has required stats.
        
        Args:
            character (Character): Character to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not character:
            return False, "Character not found."
            
        if not character.db.stats:
            return False, "Character has no stats initialized."
            
        if not character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm'):
            return False, "You must set a splat to initialize your sheet. Use +selfstat splat=<Splat> or ask staff to set it."
            
        try:
            splat = character.get_stat('other', 'splat', 'Splat')
            if not splat:
                splat = "Mortal"
            return True, splat
        except AttributeError:
            return False, "Error accessing character stats. Please contact staff."
    
    def func(self):
        """Execute the command."""
        # Reset section lists
        self.reset_lists()
        
        # Get target character
        name = self.args.strip()
        character = self.get_character(name)
        
        # Validate character exists and has required stats
        is_valid, result = self.validate_character(character)
        if not is_valid:
            self.caller.msg(f"|r{result}|n")
            return
            
        splat = result  # result contains splat type if validation passed
        
        # Check viewing permissions
        if not self.can_view_sheet(character):
            self.caller.msg(f"|rYou can't see the sheet of {character.key}.|n")
            return

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

        # Process advantages section
        string += self.process_advantages(character, string)

        # Display Pools & Status (or Pools, Virtues & Status for non-Companions)
        if splat in ['Companion', 'Possessed']:
            string += header("Pools & Status", width=78, color="|y")
        else:
            string += header("Pools, Virtues & Status", width=78, color="|y")

        # Process pools
        self.process_pools(character)

        # Calculate health bonuses before getting health status
        bonus_health = self.calculate_health_bonuses(character)

        # Add health status to status_list without extra padding
        health_status = format_damage_stacked(character)
        self.status_list.extend(health_status)

        # Handle virtues for non-Companions and Possessed
        if splat not in ['Companion', 'Possessed']:
            self.process_virtues(character, splat)

        # Display the pools, virtues and status in columns with adjusted spacing
        if splat in ['Companion', 'Possessed']:
            # Add headers for the two-column layout
           
            # Ensure pools and status lists have the same length
            max_len = max(len(self.pools_list), len(self.status_list))
            self.pools_list.extend(["".ljust(38)] * (max_len - len(self.pools_list)))
            self.status_list.extend(["".ljust(40)] * (max_len - len(self.status_list)))
            
            # Display in two columns with adjusted spacing
            for pool, status in zip(self.pools_list, self.status_list):
                string += f"{pool:<38}     {status}\n"
        else:
            # Three column layout for other splats
            max_len = max(len(self.pools_list), len(self.virtues_list), len(self.status_list))
            self.pools_list.extend(["".ljust(25)] * (max_len - len(self.pools_list)))
            self.virtues_list.extend(["".ljust(25)] * (max_len - len(self.virtues_list)))
            self.status_list.extend(["".ljust(25)] * (max_len - len(self.status_list)))
            
            for pool, virtue, status in zip(self.pools_list, self.virtues_list, self.status_list):
                string += f"{pool:<25}  {virtue:>25}  {status}\n"

        # Check approval status and add it at the end
        if character.db.approved:
            string += header("Approved Character", width=78, fillchar="-")
        else:
            string += header("Unapproved Character", width=78, fillchar="-")

        # Send the complete sheet to the caller
        self.caller.msg(string)

    def format_stat_with_dots(self, stat, value, width=38):
        """Format a stat with dots for display."""
        # Initialize display_stat with the original stat name
        display_stat = stat
        if '(' in stat and ')' in stat:
            # Keep the instance in the display
            display_stat = stat
        else:
            # Map old stat names to new ones for display
            display_stat = 'Subfaction' if stat == 'Traditions Subfaction' else display_stat
            display_stat = 'Type' if stat == 'possessed_type' else display_stat
            display_stat = 'Type' if stat == 'companion_type' else display_stat
            display_stat = 'Enlightenment' if stat == 'Path of Enlightenment' else display_stat
            display_stat = 'Element' if stat == 'Elemental Affinity' else display_stat

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
            if stat == 'Rank':  # Special case for  Rank
                value_str = '0'
            elif stat in ['Full Name', 'Date of Birth', 'Date of Awakening', 'Date of Chrysalis', 'First Change Date',
                         'Date of Embrace', 'Concept', 'Nature', 'Demeanor', 'Nunnehi Seeming', 'Nunnehi Camp', 'Nunnehi Family',
                         'Nunnehi Totem', 'Clan', 'Generation', 'Sire', 'Path of Enlightenment', 'Kith', 'Seeming', 'House', 
                         'Seelie Legacy', 'Unseelie Legacy', 'Type', 'Tribe', 'Breed', 'Auspice', 'Jamak Spirit',
                         'Tradition', 'Convention', 'Affiliation', 'Phyla', 'Traditions Subfaction', 'Methodology',
                         'Spirit Type', 'Spirit Name', 'Domitor', 'Society', 'Order', 'Coven', 'Cabal', 'Plague', 'Crown', 
                         'Stream', 'Kitsune Path', 'Varna', 'Deed Name', 'Motivation', 'Possessed Type', 'Date of Possession',
                         'Companion Type', 'Patron Totem', 'Pack', 'Affinity Realm', 'Fae Court', 'Fae Name', 'Camp', 'Lodge',
                         'Fang House', 'Nephandi Faction', 'Fuel', 'Elemental Affinity', 'Anchor']:
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

            # Special handling for Path of Enlightenment
            if left_stat == 'Path of Enlightenment':
                left_value = character.get_stat('identity', 'personal', left_stat, temp=False)
            else:
                left_value = self.get_stat_value(character, left_stat)
            left_formatted = self.format_stat_with_dots(left_stat, left_value)

            if right_stat:
                if right_stat == 'Path of Enlightenment':
                    right_value = character.get_stat('identity', 'personal', right_stat, temp=False)
                else:
                    right_value = self.get_stat_value(character, right_stat)
                right_formatted = self.format_stat_with_dots(right_stat, right_value)
                string += f"{left_formatted}  {right_formatted}\n"
            else:
                string += f"{left_formatted}\n"

        return string

    def get_identity_stats(self, character, splat):
        """Get the list of identity stats for a character based on their splat."""
        from world.wod20th.utils.stat_mappings import get_identity_stats
        from world.wod20th.utils.mortalplus_utils import get_mortalplus_identity_stats
        
        # Get character type (e.g., Garou for Shifter)
        char_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
        
        # Special handling for Mortal+ characters
        if splat == 'Mortal+':
            return get_mortalplus_identity_stats(char_type)
        
        # Get tribe for Garou characters
        tribe = None
        if char_type and char_type.lower() == 'garou':
            tribe = character.get_stat('identity', 'lineage', 'Tribe', temp=False)
            # Get base stats from get_identity_stats
            stats = get_identity_stats(splat, char_type, tribe)
            
            # Special handling for Silver Fangs
            if tribe and tribe.lower() == 'silver fangs':
                # Remove 'Camp' if it's in the list
                if 'Camp' in stats:
                    stats.remove('Camp')
                # Add Silver Fang specific stats
                stats.extend(['Fang House', 'Lodge'])
            return stats
        
        # Special handling for Mage characters
        if splat == 'Mage':
            affiliation = character.get_stat('identity', 'lineage', 'Affiliation', temp=False)
            return get_identity_stats(splat, char_type, affiliation)
            
        # Special handling for Changeling characters
        if splat == 'Changeling':
            kith = character.get_stat('identity', 'lineage', 'Kith', temp=False)
            return get_identity_stats(splat, kith)
        
        # Get identity stats based on splat, type, and tribe
        return get_identity_stats(splat, char_type, tribe)

    def format_attributes_section(self, character):
        """Format the attributes section of the character sheet."""
        string = header("Attributes", width=78, color="|y")
        string += " " + divider("Physical", width=25, fillchar=" ") + " "
        string += divider("Social", width=25, fillchar=" ") + " "
        string += divider("Mental", width=25, fillchar=" ") + "\n"

        # Get current form and its modifiers if any
        current_form = character.db.current_form if hasattr(character.db, 'current_form') else None
        form_modifiers = {}
        if current_form:
            try:
                from world.wod20th.models import ShapeshifterForm
                form = ShapeshifterForm.objects.get(name=current_form)
                form_modifiers = form.stat_modifiers
            except Exception:
                form_modifiers = {}

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

        zero_appearance_forms = ['crinos', 'anthros', 'arthren', 'sokto', 'chatro']
        is_zero_appearance_form = current_form and current_form.lower() in zero_appearance_forms

        for row in rows:
            row_string = ""
            for attr, category in row:
                # Get permanent value
                perm_value = character.db.stats.get('attributes', {}).get(category, {}).get(attr, {}).get('perm', 1)
                
                # Get base temporary value
                temp_value = character.db.stats.get('attributes', {}).get(category, {}).get(attr, {}).get('temp', perm_value)
                
                # Apply form modifier if it exists
                if form_modifiers and attr in form_modifiers:
                    form_mod = form_modifiers[attr]
                    temp_value = max(0, temp_value + form_mod)

                # Special handling for Appearance
                if attr == 'Appearance':
                    if is_zero_appearance_clan or is_zero_appearance_form:
                        temp_value = 0
                
                # Format the stat with both permanent and temporary values
                row_string += format_stat(attr, perm_value, default=1, tempvalue=temp_value, allow_zero=True, width=25)
                
                # Add padding for mental attributes
                if category == 'mental':
                    row_string = row_string.ljust(len(row_string) + 1)
                else:
                    row_string += " "
            string += row_string + "\n"

        return string
        
    def format_abilities_section(self, character):
        """Format the abilities section of the character sheet."""
        string = header("Abilities", width=78, color="|y")
        string += " " + divider("Talents", width=25, fillchar=" ") + " "
        string += divider("Skills", width=25, fillchar=" ") + " "
        string += divider("Knowledges", width=25, fillchar=" ") + "\n"

        # Base abilities for all characters
        base_abilities = {
            'Talents': ['Alertness', 'Athletics', 'Awareness', 'Brawl', 'Empathy', 
                       'Expression', 'Intimidation', 'Leadership', 'Streetwise', 'Subterfuge'],
            'Skills': ['Animal Ken', 'Crafts', 'Drive', 'Etiquette', 'Firearms', 
                      'Larceny', 'Melee', 'Performance', 'Stealth', 'Survival', 'Technology'],
            'Knowledges': ['Academics', 'Computer', 'Cosmology', 'Enigmas', 'Finance', 'Investigation', 
                          'Law', 'Medicine', 'Occult', 'Politics', 'Science']
        }

        # Get character's splat and type
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        char_type = character.get_stat('identity', 'lineage', 'Type', temp=False)

        # Add splat-specific abilities
        if splat == 'Shifter':
            base_abilities['Talents'].append('Primal-Urge')
            base_abilities['Knowledges'].append('Rituals')
            if char_type in ['Corax', 'Camazotz', 'Mokole']:
                base_abilities['Talents'].append('Flight')
        elif splat == 'Vampire' and char_type == 'Gargoyle':
            base_abilities['Talents'].append('Flight')
        elif splat == 'Changeling':
            base_abilities['Talents'].append('Kenning')
            base_abilities['Knowledges'].append('Gremayre')
        elif splat == 'Companion':
            base_abilities['Talents'].append('Flight')

        # Format each category
        talents = []
        skills = []
        knowledges = []

        # Process talents
        for ability in sorted(base_abilities['Talents']):
            value = character.get_stat('abilities', 'talent', ability, temp=False) or 0
            talents.append(format_stat(ability, value, width=25))

        # Process skills
        for ability in sorted(base_abilities['Skills']):
            value = character.get_stat('abilities', 'skill', ability, temp=False) or 0
            skills.append(format_stat(ability, value, width=25))

        # Process knowledges
        for ability in sorted(base_abilities['Knowledges']):
            value = character.get_stat('abilities', 'knowledge', ability, temp=False) or 0
            knowledges.append(format_stat(ability, value, width=25))

        # Ensure all columns have the same length
        max_len = max(len(talents), len(skills), len(knowledges))
        talents.extend([" " * 25] * (max_len - len(talents)))
        skills.extend([" " * 25] * (max_len - len(skills)))
        knowledges.extend([" " * 25] * (max_len - len(knowledges)))

        # Combine columns
        for talent, skill, knowledge in zip(talents, skills, knowledges):
            string += f"{talent} {skill} {knowledge}\n"

        return string
        
    def format_secondary_abilities_section(self, character):
        """Format the secondary abilities section of the character sheet."""
        string = header("Secondary Abilities", width=78, color="|y")
        string += " " + divider("Talents", width=25, fillchar=" ") + " "
        string += divider("Skills", width=25, fillchar=" ") + " "
        string += divider("Knowledges", width=25, fillchar=" ") + "\n"

        # Base secondary abilities for all characters
        base_secondary_talents = [
            'Artistry', 'Carousing', 'Diplomacy', 'Intrigue', 'Lucid Dreaming',
            'Mimicry', 'Scrounging', 'Seduction', 'Style'
        ]
        base_secondary_skills = [
            'Archery', 'Fencing', 'Fortune-Telling', 'Gambling', 'Jury-Rigging',
            'Martial Arts', 'Pilot', 'Torture'
        ]
        base_secondary_knowledges = [
            'Area Knowledge', 'Cultural Savvy', 'Demolitions', 'Herbalism',
            'Media', 'Power-Brokering', 'Vice'
        ]

        # Get character's splat and add splat-specific abilities
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        if splat and splat.lower() == 'mage':
            base_secondary_talents.extend(['Blatancy', 'Do', 'Flying', 'High Ritual'])
            base_secondary_skills.extend(['Biotech', 'Energy Weapons', 'Helmsman', 'Microgravity Ops'])
            base_secondary_knowledges.extend(['Cybernetics', 'Hypertech', 'Paraphysics', 'Xenobiology'])

        # Sort all lists
        base_secondary_talents.sort()
        base_secondary_skills.sort()
        base_secondary_knowledges.sort()

        # Get secondary abilities from character stats
        secondary_abilities = character.db.stats.get('secondary_abilities', {})
        secondary_talents = secondary_abilities.get('secondary_talent', {})
        secondary_skills = secondary_abilities.get('secondary_skill', {})
        secondary_knowledges = secondary_abilities.get('secondary_knowledge', {})

        # Format abilities with values from character stats
        formatted_secondary_talents = []
        formatted_secondary_skills = []
        formatted_secondary_knowledges = []

        # Process talents
        for talent in base_secondary_talents:
            value = secondary_talents.get(talent, {}).get('perm', 0)
            formatted_secondary_talents.append(format_stat(talent, value, width=25))

        # Process skills
        for skill in base_secondary_skills:
            value = secondary_skills.get(skill, {}).get('perm', 0)
            formatted_secondary_skills.append(format_stat(skill, value, width=25))

        # Process knowledges
        for knowledge in base_secondary_knowledges:
            value = secondary_knowledges.get(knowledge, {}).get('perm', 0)
            formatted_secondary_knowledges.append(format_stat(knowledge, value, width=25))

        # Ensure all columns have the same length
        max_len = max(len(formatted_secondary_talents), len(formatted_secondary_skills), len(formatted_secondary_knowledges))
        formatted_secondary_talents.extend([" " * 25] * (max_len - len(formatted_secondary_talents)))
        formatted_secondary_skills.extend([" " * 25] * (max_len - len(formatted_secondary_skills)))
        formatted_secondary_knowledges.extend([" " * 25] * (max_len - len(formatted_secondary_knowledges)))

        # Combine columns
        for talent, skill, knowledge in zip(formatted_secondary_talents, formatted_secondary_skills, formatted_secondary_knowledges):
            string += f"{talent} {skill} {knowledge}\n"

        return string

    def process_general_powers(self, character, powers, add_none=True):
        """
        Process any general powers that aren't handled by splat-specific methods.
        This handles power types that might be granted by merits, special circumstances,
        or cross-splat abilities.
        
        Args:
            character: The character whose powers to process
            powers: The list of formatted power strings to append to
            add_none: Whether to add "None" if no powers found (default: True)
            
        Returns:
            List[str]: The updated powers list
        """
        # Define power types that are handled by splat-specific methods
        SPLAT_SPECIFIC_POWERS = {
            'discipline',      # Vampire, Ghoul
            'combodiscipline', # Vampire
            'thaumaturgy',    # Vampire, Ghoul (sometimes)
            'gift',           # Shifter, Kinfolk, Possessed
            'rite',           # Shifter, Kinfolk
            'art',            # Changeling, Kinain
            'realm',          # Changeling, Kinain
            'sliver',         # inanimae (changeling type)
            'blessing',       # Possessed
            'charm',          # Possessed/Companion
            'sphere',         # Mage
            'special_advantage', # Companion
            'thaum_ritual',   # vampire
            'necromancy',     # vampire
            'necromancy_ritual', # vampire
            'hedge_ritual',   # sorcerer
            'sorcery',        # sorcerer
            'numina',         # psychic
            'faith'          # faithful
        }
        
        # Get all power categories from the character's stats
        power_stats = character.db.stats.get('powers', {})
        has_powers = False
        
        # Process each power category that isn't splat-specific
        for power_type, power_dict in sorted(power_stats.items()):
            # Skip empty categories and splat-specific powers
            if not power_dict or power_type in SPLAT_SPECIFIC_POWERS:
                continue
                
            # Add category header
            powers.append(divider(power_type.title(), width=38, color="|b"))
            
            # Add each power and its value
            for power, values in sorted(power_dict.items()):
                power_value = values.get('perm', 0)
                if power_value > 0:
                    has_powers = True
                    powers.append(format_stat(power, power_value, width=self.POWERS_WIDTH))
                    
        # If no general powers were found and add_none is True, add "None"
        if not has_powers and add_none:
            powers.append(" None".ljust(38))
            
        return powers
            
    def process_advantages(self, character, string):
        # Process powers and advantages in two columns
        result = header("Advantages", width=78, color="|y") + "\n"
        powers = []
        left_column = []

        # Process backgrounds
        left_column.append(divider("Backgrounds", width=38, color="|b"))
        char_backgrounds = character.db.stats.get('backgrounds', {}).get('background', {})
        has_backgrounds = False
        if char_backgrounds:
            # Sort backgrounds, keeping instance information intact
            sorted_backgrounds = sorted(char_backgrounds.items(), key=lambda x: x[0].split('(')[0])
            for background, values in sorted_backgrounds:
                background_value = values.get('perm', 0)
                if background_value > 0:
                    has_backgrounds = True
                    # Keep the full background name (including instance) for display
                    left_column.append(format_stat(background, background_value, width=38))
        if not has_backgrounds:
            left_column.append("None".ljust(38))

        # Add spacing between sections
        left_column.append(" " * 38)

        # Process merits
        left_column.append(divider("Merits", width=38, color="|b"))
        merits = character.db.stats.get('merits', {})
        has_merits = False
        for merit_dict in merits.values():
            for merit, values in sorted(merit_dict.items()):
                merit_value = values.get('perm', 0)
                if merit_value > 0:
                    has_merits = True
                    left_column.append(format_stat(merit, merit_value, width=38))
        if not has_merits:
            left_column.append("None".ljust(38))

        # Add spacing between sections
        left_column.append(" " * 38)

        # Process flaws
        left_column.append(divider("Flaws", width=38, color="|b"))
        flaws = character.db.stats.get('flaws', {})
        has_flaws = False
        for flaw_dict in flaws.values():
            for flaw, values in sorted(flaw_dict.items()):
                try:
                    flaw_value = int(values.get('perm', 0))
                except (ValueError, TypeError):
                    flaw_value = 0
                if flaw_value > 0:
                    has_flaws = True
                    left_column.append(format_stat(flaw, flaw_value, width=38))
        if not has_flaws:
            left_column.append("None".ljust(38))

        # Process powers based on character splat
        character_splat = character.get_stat('other', 'splat', 'Splat', temp=False)

        # Process powers based on splat type
        if character_splat == 'Mage':
            powers = self.process_mage_powers(character, powers)
        elif character_splat == 'Vampire':
            powers = self.process_vampire_powers(character, powers)
        elif character_splat == 'Changeling':
            powers = self.process_changeling_powers(character, powers)
        elif character_splat == 'Shifter':
            powers = self.process_shifter_powers(character, powers)
        elif character_splat == 'Companion':
            powers = self.process_companion_powers(character, powers)
        elif character_splat == 'Possessed':
            powers = self.process_possessed_powers(character, powers)
        elif character_splat == 'Mortal+':
            powers = self.process_mortal_plus_powers(character, powers)
        else:  # Mortal or any other splat
            powers = self.process_general_powers(character, powers)

        # Ensure both columns have the same number of rows
        max_len = max(len(powers), len(left_column))
        powers.extend([" " * 38] * (max_len - len(powers)))
        left_column.extend([" " * 38] * (max_len - len(left_column)))

        # Combine columns with proper spacing and alignment
        for i, (left, power) in enumerate(zip(left_column, powers)):
            # Handle ANSI-formatted strings
            if isinstance(left, str) and ("|x" in left or "|n" in left):
                left_part = left
            else:
                left_part = left.strip().ljust(38)
                
            if isinstance(power, str) and ("|x" in power or "|n" in power):
                right_part = power
            else:
                right_part = power.strip().ljust(38)
                
            # Add two spaces between columns for consistent spacing
            result += f"{left_part}  {right_part}\n"  # Always add newline after each row

        return result

    def process_vampire_powers(self, character, powers, skip_disciplines=False):
        """Process powers section for Vampire characters."""
        # Process all standard power types first
        powers = self.process_general_powers(character, powers, add_none=False)
        
        # Add Disciplines section
        if not skip_disciplines:
            powers.append(divider("Disciplines", width=38, color="|b"))
            disciplines = character.db.stats.get('powers', {}).get('discipline', {})
            has_disciplines = False
            for discipline, values in sorted(disciplines.items()):
                discipline_value = values.get('perm', 0)
                if discipline_value > 0:
                    has_disciplines = True
                    powers.append(format_stat(discipline, discipline_value, default=0, width=self.POWERS_WIDTH))
            if not has_disciplines:
                powers.append("None".ljust(38))

        
        # Add Combo Disciplines section if they exist and have values
        combo_disciplines = character.db.stats.get('powers', {}).get('combodiscipline', {})
        if combo_disciplines and any(values.get('perm', 0) > 0 for values in combo_disciplines.values()):
            powers.append(" " * 38)  # Add spacing
            powers.append(divider("Combo Disciplines", width=38, color="|b"))
            for combo, values in sorted(combo_disciplines.items()):
                combo_value = values.get('perm', 0)
                if combo_value > 0:
                    powers.append(format_stat(combo, combo_value, default=0, width=self.POWERS_WIDTH))
        
        # Add Thaumaturgy Paths section if they exist and have values
        thaumaturgy = character.db.stats.get('powers', {}).get('thaumaturgy', {})
        if thaumaturgy and any(values.get('perm', 0) > 0 for values in thaumaturgy.values()):
            powers.append(" " * 38)  # Add spacing
            powers.append(divider("Thaumaturgy Paths", width=38, color="|b"))
            for path, values in sorted(thaumaturgy.items()):
                path_value = values.get('perm', 0)
                if path_value > 0:
                    powers.append(format_stat(path, path_value, default=0, width=self.POWERS_WIDTH))
        
        # Add Thaumaturgy Rituals section if they exist and have values
        rituals = character.db.stats.get('powers', {}).get('thaum_ritual', {})
        if rituals and any(values.get('perm', 0) > 0 for values in rituals.values()):
            powers.append(" " * 38)  # Add spacing
            powers.append(divider("Thaumaturgy Rituals", width=38, color="|b"))
            for ritual, values in sorted(rituals.items()):
                ritual_value = values.get('perm', 0)
                if ritual_value > 0:
                    powers.append(format_stat(ritual, ritual_value, default=0, width=self.POWERS_WIDTH))

        # Add Necromancy Paths section if they exist and have values
        necromancy = character.db.stats.get('powers', {}).get('necromancy', {})
        if necromancy and any(values.get('perm', 0) > 0 for values in necromancy.values()):
            powers.append(" " * 38)  # Add spacing
            powers.append(divider("Necromancy Paths", width=38, color="|b"))
            for necromancy_path, values in sorted(necromancy.items()):
                necromancy_path_value = values.get('perm', 0)
                if necromancy_path_value > 0:
                    powers.append(format_stat(necromancy_path, necromancy_path_value, default=0, width=self.POWERS_WIDTH))
        
        # Add Necromancy Rituals section if they exist and have values  
        rituals = character.db.stats.get('powers', {}).get('necromancy_ritual', {})
        if rituals and any(values.get('perm', 0) > 0 for values in rituals.values()):
            powers.append(" " * 38)  # Add spacing
            powers.append(divider("Necromancy Rituals", width=38, color="|b"))
            for ritual, values in sorted(rituals.items()):
                ritual_value = values.get('perm', 0)
                if ritual_value > 0:
                    powers.append(format_stat(ritual, ritual_value, default=0, width=self.POWERS_WIDTH))
        return powers

    def process_changeling_powers(self, character, powers, skip_arts=False):
        """Process powers section for Changeling characters."""
        # Process all standard power types first
        powers = self.process_general_powers(character, powers, add_none=False)
        
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
                        powers.append(format_stat(sliver, sliver_value, default=0, width=self.POWERS_WIDTH))
                if not has_slivers:
                    powers.append(" None".ljust(38))
            else:
                powers.append(" None".ljust(38))
            
            # Add Arts and Realms sections for Mannikins
            if phyla and phyla.lower() == 'mannikin':
                # Add spacing
                powers.append(" " * 38)
                
                # Add Arts section
                powers.append(divider("Arts", width=38, color="|b"))
                arts = character.db.stats.get('powers', {}).get('art', {})
                if arts:
                    has_arts = False
                    for art, values in sorted(arts.items()):
                        art_value = values.get('perm', 0)
                        if art_value > 0:
                            has_arts = True
                            powers.append(format_stat(art, art_value, default=0, width=self.POWERS_WIDTH))
                    if not has_arts:
                        powers.append(" None".ljust(38))
                else:
                    powers.append(" None".ljust(38))
                
                # Add spacing
                powers.append(" " * 38)
                
                # Add Realms section
                powers.append(divider("Realms", width=38, color="|b"))
                realms = character.db.stats.get('powers', {}).get('realm', {})
                if realms:
                    has_realms = False
                    for realm, values in sorted(realms.items()):
                        realm_value = values.get('perm', 0)
                        if realm_value > 0:
                            has_realms = True
                            powers.append(format_stat(realm, realm_value, default=0, width=self.POWERS_WIDTH))
                    if not has_realms:
                        powers.append(" None".ljust(38))
                else:
                    powers.append(" None".ljust(38))
        else:
            # Regular Changeling powers
            if not skip_arts:
                powers.append(divider("Arts", width=38, color="|b"))
                arts = character.db.stats.get('powers', {}).get('art', {})
                has_arts = False
                for art, values in sorted(arts.items()):
                    art_value = values.get('perm', 0)
                    if art_value > 0:
                        has_arts = True
                        powers.append(format_stat(art, art_value, default=0, width=self.POWERS_WIDTH))
                if not has_arts:
                    powers.append(" None".ljust(38))
            
            # Add spacing
            powers.append(" " * 38)
            
            # Add Realms section
            powers.append(divider("Realms", width=38, color="|b"))
            realms = character.db.stats.get('powers', {}).get('realm', {})
            has_realms = False
            for realm, values in sorted(realms.items()):
                realm_value = values.get('perm', 0)
                if realm_value > 0:
                    has_realms = True
                    powers.append(format_stat(realm, realm_value, default=0, width=self.POWERS_WIDTH))
            if not has_realms:
                powers.append(" None".ljust(38))
        
        return powers

    def process_shifter_powers(self, character, powers, skip_gifts=False):
        """Process powers section for Shifter characters."""
        # Process all standard power types first
        powers = self.process_general_powers(character, powers, add_none=False)
        # Always add Gifts section for Shifters
        if not skip_gifts:
            powers.append(divider("Gifts", width=38, color="|b"))
            gifts = character.db.stats.get('powers', {}).get('gift', {})
            has_gifts = False
            
            # Process each gift
            for gift_name, values in sorted(gifts.items()):
                gift_value = values.get('perm', 0)
                if gift_value > 0:
                    has_gifts = True
                    
                    # Use the display name method to get the proper name
                    display_name = character.get_display_name_for_gift(gift_name)
                    powers.append(format_stat(display_name, gift_value, default=0, width=self.POWERS_WIDTH))
            if not has_gifts:
                powers.append("None".ljust(38))

        # Add spacing between sections
        powers.append(" " * 38)

        # Always add Rites section for Shifters
        powers.append(divider("Rites", width=38, color="|b"))
        rites = character.db.stats.get('powers', {}).get('rite', {})
        has_rites = False
        for rite, values in sorted(rites.items()):
            rite_value = values.get('perm', 0)
            has_rites = True
            powers.append(format_stat(rite, rite_value, default=0, width=self.POWERS_WIDTH, allow_zero=True))
        if not has_rites:
            powers.append("None".ljust(38))

        return powers

    def process_mage_powers(self, character, powers):
        """Process powers section for Mage characters."""
        from world.wod20th.utils.mage_utils import get_available_spheres, get_sphere_name
        
        # Process all standard power types first, but don't add "None" since we'll add spheres
        powers = self.process_general_powers(character, powers, add_none=False)
        
        # Get affiliation
        affiliation = character.get_stat('identity', 'lineage', 'Affiliation', temp=False)
        
        # Add Spheres section
        powers.append(divider("Spheres", width=self.POWERS_WIDTH, color="|b"))
        
        # Get character's spheres
        spheres = character.db.stats.get('powers', {}).get('sphere', {})
        
        # Get available spheres for this affiliation
        available_spheres = get_available_spheres(affiliation)
        
        # Display all available spheres
        for base_sphere in sorted(available_spheres):
            # Get the appropriate name for this sphere based on affiliation
            display_name = get_sphere_name(base_sphere, affiliation)
            # Look up value using traditional name
            sphere_value = spheres.get(base_sphere, {}).get('perm', 0)
            # Always display the sphere, even if value is 0
            powers.append(format_stat(display_name, sphere_value, default=0, width=self.POWERS_WIDTH))
        
        return powers
    
    def process_mortal_plus_powers(self, character, powers):
        """Process powers section for Mortal+ characters."""
        # Process all standard power types first
        powers = self.process_general_powers(character, powers, add_none=False)
        
        # Get character's Mortal+ type
        mortalplus_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
        if not mortalplus_type:
            return powers

        # Process powers based on Mortal+ type
        if mortalplus_type.lower() == 'ghoul':
            # Process disciplines
            disciplines = character.db.stats.get('powers', {}).get('discipline', {})
            if disciplines:
                powers.append(divider("Disciplines", width=38, color="|b"))
                for discipline, values in sorted(disciplines.items()):
                    discipline_value = values.get('perm', 0)
                    powers.append(format_stat(discipline, discipline_value, default=0, width=self.POWERS_WIDTH))

        elif mortalplus_type.lower() == 'kinfolk':
            # Process gifts
            gifts = character.db.stats.get('powers', {}).get('gift', {})
            if gifts:
                powers.append(divider("Gifts", width=38, color="|b"))
                for gift, values in sorted(gifts.items()):
                    gift_value = values.get('perm', 0)
                    powers.append(format_stat(gift, gift_value, default=0, width=self.POWERS_WIDTH))
            # process rites
            rites = character.db.stats.get('powers', {}).get('rite', {})
            if rites:
                powers.append(divider("Rites", width=38, color="|b"))
                for rite, values in sorted(rites.items()):
                    rite_value = values.get('perm', 0)
                    powers.append(format_stat(rite, rite_value, default=0, width=self.POWERS_WIDTH))

        elif mortalplus_type.lower() == 'kinain':
            # Process arts
            arts = character.db.stats.get('powers', {}).get('art', {})
            if arts:
                powers.append(divider("Arts", width=38, color="|b"))
                for art, values in sorted(arts.items()):
                    art_value = values.get('perm', 0)
                    powers.append(format_stat(art, art_value, default=0, width=self.POWERS_WIDTH))

            # Add spacing between sections if both arts and realms exist
            if arts and character.db.stats.get('powers', {}).get('realm', {}):
                powers.append(" " * 38)

            # Process realms
            realms = character.db.stats.get('powers', {}).get('realm', {})
            if realms:
                powers.append(divider("Realms", width=38, color="|b"))
                for realm, values in sorted(realms.items()):
                    realm_value = values.get('perm', 0)
                    powers.append(format_stat(realm, realm_value, default=0, width=self.POWERS_WIDTH))

        elif mortalplus_type.lower() == 'sorcerer':
            # Process sorcery
            sorcery = character.db.stats.get('powers', {}).get('sorcery', {})
            if sorcery:
                powers.append(divider("Sorcery", width=38, color="|b"))
                for power, values in sorted(sorcery.items()):
                    power_value = values.get('perm', 0)
                    powers.append(format_stat(power, power_value, default=0, width=self.POWERS_WIDTH))

            # Add spacing between sections if both sorcery and hedge rituals exist
            if sorcery and character.db.stats.get('powers', {}).get('hedge_ritual', {}):
                powers.append(" " * 38)

            # Process hedge rituals
            hedge_rituals = character.db.stats.get('powers', {}).get('hedge_ritual', {})
            if hedge_rituals:
                powers.append(divider("Hedge Rituals", width=38, color="|b"))
                for ritual, values in sorted(hedge_rituals.items()):
                    ritual_value = values.get('perm', 0)
                    powers.append(format_stat(ritual, ritual_value, default=0, width=self.POWERS_WIDTH))

        elif mortalplus_type.lower() == 'psychic':
            # Process numina
            numina = character.db.stats.get('powers', {}).get('numina', {})
            if numina:
                powers.append(divider("Numina", width=38, color="|b"))
                for power, values in sorted(numina.items()):
                    power_value = values.get('perm', 0)
                    powers.append(format_stat(power, power_value, default=0, width=self.POWERS_WIDTH))

        elif mortalplus_type.lower() == 'faithful':
            # Process faith
            faith = character.db.stats.get('powers', {}).get('faith', {})
            if faith:
                powers.append(divider("Faith", width=38, color="|b"))
                for power, values in sorted(faith.items()):
                    power_value = values.get('perm', 0)
                    powers.append(format_stat(power, power_value, default=0, width=self.POWERS_WIDTH))
        
        return powers

    def process_possessed_powers(self, character, powers):
        """Process powers section for Possessed characters."""
        # Process all standard power types first
        powers = self.process_general_powers(character, powers, add_none=False)
        
        # Process blessings
        blessings = character.db.stats.get('powers', {}).get('blessing', {})
        if blessings:
            has_blessings = False
            powers.append(divider("Blessings", width=38, color="|b"))
            for blessing, values in sorted(blessings.items()):
                blessing_value = values.get('perm', 0)
                if blessing_value > 0:
                    has_blessings = True
                    powers.append(format_stat(blessing, blessing_value, default=0, width=self.POWERS_WIDTH))
            if not has_blessings:
                powers.append(" None".ljust(38))

        # Process gifts
        gifts = character.db.stats.get('powers', {}).get('gift', {})
        if gifts:
            # Add spacing if blessings exist
            if blessings and any(values.get('perm', 0) > 0 for values in blessings.values()):
                powers.append(" " * 38)
            has_gifts = False
            powers.append(divider("Gifts", width=38, color="|b"))
            for gift, values in sorted(gifts.items()):
                gift_value = values.get('perm', 0)
                if gift_value > 0:
                    has_gifts = True
                    powers.append(format_stat(gift, gift_value, default=0, width=self.POWERS_WIDTH))
            if not has_gifts:
                powers.append(" None".ljust(38))
        
        # Process charms
        charms = character.db.stats.get('powers', {}).get('charm', {})
        if charms:
            # Add spacing if blessings or gifts exist and have values
            if (blessings and any(values.get('perm', 0) > 0 for values in blessings.values())) or \
               (gifts and any(values.get('perm', 0) > 0 for values in gifts.values())):
                powers.append(" " * 38)
            has_charms = False
            powers.append(divider("Charms", width=38, color="|b"))
            for charm, values in sorted(charms.items()):
                charm_value = values.get('perm', 0)
                if charm_value > 0:
                    has_charms = True
                    powers.append(format_stat(charm, charm_value, default=0, width=self.POWERS_WIDTH))
            if not has_charms:
                powers.append(" None".ljust(38))
        
        return powers

    def process_companion_powers(self, character, powers):
        """Process powers section for Companion characters."""
        # Process all standard power types first
        powers = self.process_general_powers(character, powers, add_none=False)
        
        # Always show Special Advantages section
        powers.append(divider("Special Advantages", width=38, color="|b"))
        special_advantages = character.db.stats.get('powers', {}).get('special_advantage', {})
        has_advantages = False
        if special_advantages:
            # Track seen advantages to prevent duplicates
            seen_advantages = set()
            # Sort by proper case name from SPECIAL_ADVANTAGES
            for advantage_name, values in sorted(special_advantages.items(), key=lambda x: x[0].lower()):
                if advantage_name.lower() in seen_advantages:
                    continue
                advantage_value = values.get('perm', 0)
                if advantage_value > 0:
                    has_advantages = True
                    # Properly capitalize each word in the advantage name
                    display_name = ' '.join(word.capitalize() for word in advantage_name.split())
                    # Special case for "Aww!"
                    if advantage_name.lower() == "aww!":
                        display_name = "Aww!"
                    powers.append(format_stat(display_name, advantage_value, width=self.POWERS_WIDTH))
                    seen_advantages.add(advantage_name.lower())
        if not has_advantages:
            powers.append(" None".ljust(38))

        # Add spacing between sections
        powers.append(" " * 38)

        # Always show Charms section
        powers.append(divider("Charms", width=38, color="|b"))
        charms = character.db.stats.get('powers', {}).get('charm', {})
        has_charms = False
        if charms:
            for charm, values in sorted(charms.items()):
                charm_value = values.get('perm', 0)
                if charm_value > 0:
                    has_charms = True
                    powers.append(format_stat(charm, charm_value, width=self.POWERS_WIDTH))
        if not has_charms:
            powers.append(" None".ljust(38))

        return powers

    def process_virtues(self, character, character_splat):
        """Process and format character virtues."""
        # Get character's splat and type
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        char_type = character.get_stat('identity', 'lineage', 'Type', temp=False)

        # Handle Shifter Renown
        if splat == 'Shifter':
            # Get Renown values from advantages.renown
            renown_values = character.db.stats.get('advantages', {}).get('renown', {})
            for renown_type, values in sorted(renown_values.items()):
                value = values.get('perm', 0)
                temp_value = values.get('temp', 0)
                self.virtues_list.append(format_stat(renown_type, value, width=25, tempvalue=temp_value))

        # Handle Changeling virtues and special stats
        elif splat == 'Changeling':
            # Add standard virtues first
            virtues = character.db.stats.get('virtues', {}).get('moral', {})
            if virtues:
                for virtue_name, values in sorted(virtues.items()):
                    virtue_value = values.get('perm', 0)
                    temp_value = values.get('temp', virtue_value)
                    self.virtues_list.append(format_stat(virtue_name, virtue_value, width=25, tempvalue=temp_value))
            
            # Add Nightmare
            nightmare = character.get_stat('pools', 'other', 'Nightmare', temp=False)
            nightmare_temp = character.get_stat('pools', 'other', 'Nightmare', temp=True)
            self.virtues_list.append(format_stat('Nightmare', nightmare or 0, width=25, tempvalue=nightmare_temp))
            
            # Add Willpower Imbalance
            imbalance = character.get_stat('pools', 'other', 'Willpower Imbalance', temp=False)
            imbalance_temp = character.get_stat('pools', 'other', 'Willpower Imbalance', temp=True)
            self.virtues_list.append(format_stat('Willpower Imbalance', imbalance or 0, width=25, tempvalue=imbalance_temp))

        # Handle standard virtues for Mortal and Mortal+ (except Ghouls)
        elif splat in ['Mortal', 'Possessed'] or (splat == 'Mortal+' and char_type != 'Ghoul'):
            virtues = ['Conscience', 'Self-Control', 'Courage']
            for virtue in virtues:
                value = character.get_stat('virtues', 'moral', virtue, temp=False) or 0
                temp_value = character.get_stat('virtues', 'moral', virtue, temp=True)
                self.virtues_list.append(format_stat(virtue, value, width=25, tempvalue=temp_value))
                
            # Add path rating for Mortals
            if splat == 'Mortal':
                path_rating = character.get_stat('pools', 'moral', 'Path', temp=False) or 0
                temp_path = character.get_stat('pools', 'moral', 'Path', temp=True)
                self.virtues_list.append(format_stat('Path', path_rating, width=25, tempvalue=temp_path))

        # Handle Vampire and Ghoul virtues and paths
        elif splat == 'Vampire' or (splat == 'Mortal+' and char_type == 'Ghoul'):
            # Get the character's path
            path = character.get_stat('identity', 'personal', 'Path of Enlightenment', temp=False)
            
            # Get the appropriate virtues based on path
            if path in PATH_VIRTUES:
                virtue1, virtue2 = PATH_VIRTUES[path]
                virtues = [virtue1, virtue2, 'Courage']
            else:
                # Default to standard virtues if no path is set
                virtues = ['Conscience', 'Self-Control', 'Courage']
            
            # Add each virtue
            for virtue in virtues:
                value = character.get_stat('virtues', 'moral', virtue, temp=False) or 0
                temp_value = character.get_stat('virtues', 'moral', virtue, temp=True)
                self.virtues_list.append(format_stat(virtue, value, width=25, tempvalue=temp_value))
            
            # Add path rating
            path_rating = character.get_stat('pools', 'moral', 'Path', temp=False) or 0
            temp_path = character.get_stat('pools', 'moral', 'Path', temp=True)
            self.virtues_list.append(format_stat('Path', path_rating, width=25, tempvalue=temp_path))

        # Handle Mage virtues
        elif splat == 'Mage':
            # Handle Synergy virtues for Mages
            synergy = character.db.stats.get('virtues', {}).get('synergy', {})
            if synergy:
                for virtue_name, values in sorted(synergy.items()):
                    virtue_value = values.get('perm', 0)
                    temp_value = values.get('temp', virtue_value)
                    self.virtues_list.append(format_stat(virtue_name, virtue_value, width=25, tempvalue=temp_value))
            
            # Handle Resonance
            resonance = character.db.stats.get('pools', {}).get('resonance', {}).get('Resonance', {})
            if resonance:
                resonance_value = resonance.get('perm', 0)
                temp_value = resonance.get('temp', resonance_value)
                self.virtues_list.append(format_stat('Resonance', resonance_value, width=25, tempvalue=temp_value))

        else:
            # Handle other splats
            virtues = character.db.stats.get('virtues', {}).get('moral', {})
            if virtues:
                for virtue_name, values in sorted(virtues.items()):
                    virtue_value = values.get('perm', 0)
                    temp_value = values.get('temp', virtue_value)
                    self.virtues_list.append(format_stat(virtue_name, virtue_value, width=25, tempvalue=temp_value))

    def calculate_health_bonuses(self, character):
        """Calculate any health level bonuses from merits, etc."""
        return calculate_total_health_levels(character)
    
    def format_pool_value(self, character, pool_name):
        """Format a pool value with both permanent and temporary values."""
        perm = character.get_stat('pools', 'dual', pool_name, temp=False)
        temp = character.get_stat('pools', 'dual', pool_name, temp=True)

        if perm is None:
            perm = 0
        if temp is None:
            temp = perm

        # Special handling for Banality
        if pool_name == 'Banality':
            splat = character.get_stat('other', 'splat', 'Splat', temp=False)
            char_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
            # Only show temp/perm format for Changelings and Kinain
            if splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain'):
                return f"{temp}/{perm}"
            else:
                return str(perm)  # Just show permanent value for other splats
        
        # Special handling for Renown - allow temp to exceed perm
        if pool_name in ['Glory', 'Honor', 'Wisdom']:
            return f"{temp}/{perm}"
        
        # For all other pools, only show perm if temp equals perm
        return f"{temp}/{perm}" if temp != perm else str(perm)

    def get_stat_value(self, character, stat_name):
        """Get the value of a stat from a character."""
        # Handle Nunnehi and Inanimae specific stats first
        if stat_name in ['Nunnehi Seeming', 'Nunnehi Camp', 'Nunnehi Family', 'Nunnehi Totem', 
                        'Summer Legacy', 'Winter Legacy', 'Phyla', 'Anchor']:
            value = character.get_stat('identity', 'lineage', stat_name, temp=False)
            if value:
                return value
            
        # Special handling for Path of Enlightenment
        if stat_name == 'Path of Enlightenment':
            value = character.get_stat('identity', 'personal', stat_name, temp=False)
            if value:
                return value
            
        # Handle identity stats
        if stat_name in IDENTITY_STATS['personal']:
            value = character.get_stat('identity', 'personal', stat_name, temp=False)
            if value:
                return value
            
        # Check lineage stats
        value = character.get_stat('identity', 'lineage', stat_name, temp=False)
        if value:
            return value
            
        # Try to find the stat in the character's stats
        for category in character.db.stats:
            for stat_type in character.db.stats[category]:
                if stat_name in character.db.stats[category][stat_type]:
                    return character.db.stats[category][stat_type][stat_name].get('perm', None)
                    
        return None

    def process_pools(self, character):
        """Process and format character pools."""
        # Get character's splat and type
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        char_type = character.get_stat('identity', 'lineage', 'Type', temp=False)

        # Always add Willpower
        willpower = self.format_pool_value(character, 'Willpower')
        self.pools_list.append(format_stat('Willpower', willpower, width=38 if splat == 'Companion' else 25))

        # Handle splat-specific pools
        if splat == 'Companion':
            # Add Essence Energy for Familiars first
            if char_type == 'Familiar':
                essence = self.format_pool_value(character, 'Essence Energy')
                self.pools_list.append(format_stat('Essence Energy', essence, width=38))

            # Add Rage if character has Ferocity
            special_advantages = character.db.stats.get('powers', {}).get('special_advantage', {})
            ferocity = next((values.get('perm', 0) for name, values in special_advantages.items() 
                           if name.lower() == 'ferocity'), 0)
            if ferocity > 0:
                rage = self.format_pool_value(character, 'Rage')
                self.pools_list.append(format_stat('Rage', rage, width=38))

            # Add Banality with proper formatting
            banality = self.format_pool_value(character, 'Banality')
            self.pools_list.append(format_stat('Banality', banality, width=38))
            return  # Return early to avoid adding Banality again

        elif splat == 'Mage':
            # Add Arete/Enlightenment based on affiliation
            if character.get_stat('identity', 'lineage', 'Affiliation', temp=False) == 'Technocracy':
                enlightenment = character.get_stat('pools', 'advantage', 'Enlightenment', temp=False)
                temp_enlightenment = character.get_stat('pools', 'advantage', 'Enlightenment', temp=True)
                self.pools_list.append(format_stat('Enlightenment', enlightenment, width=25, tempvalue=temp_enlightenment))
            else:
                arete = character.get_stat('pools', 'advantage', 'Arete', temp=False)
                temp_arete = character.get_stat('pools', 'advantage', 'Arete', temp=True)
                self.pools_list.append(format_stat('Arete', arete, width=25, tempvalue=temp_arete))
            
            # Add Quintessence and Paradox
            quintessence = self.format_pool_value(character, 'Quintessence')
            paradox = self.format_pool_value(character, 'Paradox')
            self.pools_list.append(format_stat('Quintessence', quintessence, width=25))
            self.pools_list.append(format_stat('Paradox', paradox, width=25))
            
        elif splat == 'Vampire':
            # Add Blood pool
            blood = self.format_pool_value(character, 'Blood')
            self.pools_list.append(format_stat('Blood', blood, width=25))
            
        elif splat == 'Shifter':
            # Add Rage and Gnosis
            rage = self.format_pool_value(character, 'Rage')
            gnosis = self.format_pool_value(character, 'Gnosis')
            self.pools_list.append(format_stat('Rage', rage, width=25))
            self.pools_list.append(format_stat('Gnosis', gnosis, width=25))
            if character.get_stat('identity', 'lineage', 'Type', temp=False) == 'Ananasi':
                #Add Blood pool and remove Rage
                blood = self.format_pool_value(character, 'Blood')
                self.pools_list.append(format_stat('Blood', blood, width=25))
                self.pools_list.remove(format_stat('Rage', rage, width=25)) 

            elif character.get_stat('identity', 'lineage', 'Type', temp=False) == 'Nuwisha':
                #remove rage
                self.pools_list.remove(format_stat('Rage', rage, width=25))
        elif splat == 'Changeling':
            # Add Glamour and Banality
            glamour = self.format_pool_value(character, 'Glamour')
            banality = self.format_pool_value(character, 'Banality')
            self.pools_list.append(format_stat('Glamour', glamour, width=25))
            self.pools_list.append(format_stat('Banality', banality, width=25))
            
        elif splat == 'Possessed':
            # Get possessed type
            possessed_type = character.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
            
            # Check for Rage sources (Fomori type or Berserker blessing)
            has_berserker = any(values.get('perm', 0) > 0 
                              for name, values in character.db.stats.get('powers', {}).get('blessing', {}).items() 
                              if name.lower() == 'berserker')
            
            if possessed_type == 'Fomori' or has_berserker:
                # Add Rage
                rage = self.format_pool_value(character, 'Rage')
                self.pools_list.append(format_stat('Rage', rage, width=25))
            
            # Add Gnosis for Fomori and Kami
            if possessed_type in ['Fomori', 'Kami']:
                gnosis = self.format_pool_value(character, 'Gnosis')
                self.pools_list.append(format_stat('Gnosis', gnosis, width=25))
                
        elif splat == 'Mortal+':
            # Get mortal+ type
            mortalplus_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
            if mortalplus_type == 'Ghoul':
                # Add Blood pool
                blood = self.format_pool_value(character, 'Blood')
                self.pools_list.append(format_stat('Blood', blood, width=25))
            elif mortalplus_type == 'Kinain':
                # Add Glamour and Banality
                glamour = self.format_pool_value(character, 'Glamour')
                banality = self.format_pool_value(character, 'Banality')
                self.pools_list.append(format_stat('Glamour', glamour, width=25))
                self.pools_list.append(format_stat('Banality', banality, width=25))
            elif mortalplus_type == 'Kinfolk':
                # Check if they have the Gnosis merit
                gnosis_merit = character.get_stat('merits', 'supernatural', 'Gnosis', temp=False)
                if gnosis_merit:
                    # Display Gnosis pool
                    gnosis = self.format_pool_value(character, 'Gnosis')
                    self.pools_list.append(format_stat('Gnosis', gnosis, width=25))

        # Add Banality for any character that has it, except Changelings and Kinain who already have it
        # This should be added after other pools since it's a universal trait
        # that varies by splat/type
        if splat != 'Changeling' and not (splat == 'Mortal+' and character.get_stat('identity', 'lineage', 'Type', temp=False) == 'Kinain'):
            banality = character.get_stat('pools', 'dual', 'Banality', temp=False)
            if banality is not None:
                temp_banality = character.get_stat('pools', 'dual', 'Banality', temp=True)
                self.pools_list.append(format_stat('Banality', banality, width=25, tempvalue=temp_banality))
