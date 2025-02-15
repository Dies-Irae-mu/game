from evennia.commands.default.muxcommand import MuxCommand
from world.wod20th.models import Stat, STAT_TYPES
from world.wod20th.utils.shifter_utils import SHIFTER_IDENTITY_STATS, SHIFTER_RENOWN
from world.wod20th.utils.stat_mappings import (STAT_TYPES, ARTS, REALMS, CATEGORIES, MAGE_SPHERES, UNIVERSAL_BACKGROUNDS,
                                               TRADITION_SUBFACTION, METHODOLOGIES, VAMPIRE_BACKGROUNDS,
                                               CHANGELING_BACKGROUNDS, MAGE_BACKGROUNDS, TECHNOCRACY_BACKGROUNDS,
                                               TRADITIONS_BACKGROUNDS, NEPHANDI_BACKGROUNDS, SORCERER_BACKGROUNDS,
                                               SHIFTER_BACKGROUNDS, SECONDARY_TALENTS, SECONDARY_SKILLS, SECONDARY_KNOWLEDGES,
)
from world.wod20th.utils.vampire_utils import CLAN
from world.wod20th.utils.mage_utils import AFFILIATION, TRADITION, CONVENTION, NEPHANDI_FACTION
from world.wod20th.utils.shifter_utils import SHIFTER_IDENTITY_STATS, SHIFTER_RENOWN
from world.wod20th.utils.changeling_utils import SEEMING, KITH, SEELIE_LEGACIES, UNSEELIE_LEGACIES
from evennia.utils.ansi import ANSIString
from evennia.utils.evtable import EvTable
from django.db.models import Q

class CmdInfo(MuxCommand):
    """
    List and search chargen information.

    Usage:
      +info
      +info <topic>
      +info/search <keyword>
      +info/type <stat_type>
      +info/shifter <shifter_type>

    Switches:
      /search   - Search all abilities for a keyword
      /type     - Show all entries of a specific type (gift, discipline, etc)
      /<splat>  - View only entries matching specified splat
      /shifter  - View gifts for a specific shifter type (garou, ananasi, etc)

    Examples:
      +info/fera merits  - View merits belonging only to fera
      +info merits       - View all merits across all splats
      +info/type gift    - View all gifts
      +info/shifter ananasi - View all Ananasi gifts
    """
    key = "+info"
    aliases = ["info"]
    locks = "cmd:all()"
    help_category = "Chargen & Character Info"
    
    valid_types = [
        # Core types
        'attribute', 'ability', 'secondary_ability', 'advantage', 'background',
        'lineage', 'discipline', 'combodiscipline', 'thaumaturgy', 'gift',
        'rite', 'sphere', 'rote', 'art', 'splat', 'special_advantage',
        'realm', 'path', 'sorcery', 'faith', 'numina', 'enlightenment',
        'power', 'merit', 'flaw', 'trait', 'hedge_ritual', 'ritual',
        'blessing', 'charm', 'sliver', 'thaum_ritual', 'necromancy', 'necromancy_ritual',
        'arcanos',
        # Ability subtypes
        'skill', 'knowledge', 'talent',
        'secondary_knowledge', 'secondary_talent', 'secondary_skill',
        # Game-specific
        'renown', 'arete', 'banality', 'glamour', 'essence',
        'quintessence', 'paradox',
        # Identity/Social
        'kith', 'seeming', 'house', 'seelie-legacy', 'unseelie-legacy', 'tribe', 'breed', 'nephandi_faction',
        'court', 'mortalplus_type', 'varna', 'archetype', 'nunnehi_seeming', 'nunnehi_camp', 'nunnehi_family',
        'nunnehi_totem', 'clan', 'path_of_enlightenment', 'kitsune_path', 'crown', 'plague', 'ananasi_cabal', 'ananasi_faction',
        'possessed_type', 'companion_type', 'tradition', 'traditions_subfaction', 'methodology', 'phyla', 'convention',
        'affiliation', 'society', 'fellowship', 'kitsune_faction', 'auspice', 'aspect'
    ]
    
    # Group similar stat types together based on CATEGORIES
    DISPLAY_CATEGORIES = {
        'Attributes': ['attribute'],
        'Abilities': ['skill', 'knowledge', 'talent', 'abilities'],
        'Secondary Abilities': ['secondary_knowledge', 'secondary_talent', 'secondary_skill', 'secondary_abilities'],
        'Advantages': ['renown'],
        'Powers': [
            'discipline', 'combodiscipline', 'thaumaturgy', 'gift', 'rite',
            'sphere', 'rote', 'art', 'realm', 'sorcery', 'faith', 'numina', 'hedge_ritual',
            'blessing', 'charm', 'sliver', 'thaum_ritual', 'necromancy', 'necromancy_ritual',
            'special_advantage', 'arcanos'
        ],
        'Identity': ['Nunnehi Seeming', 'Nunnehi Camp', 'Nunnehi Family', 'Fellowship',
                        'Nunnehi Totem', 'Clan', 'Path of Enlightenment', 'Kith', 'Seeming', 'House', 
                         'Seelie Legacy', 'Unseelie Legacy', 'Tribe', 'Breed', 'Auspice', 
                         'Tradition', 'Convention', 'Affiliation', 'Phyla', 'Traditions Subfaction', 'Methodology',
                         'Society', 'Ananasi Cabal', 'Ananasi Faction', 'Plague', 'Crown', 'Kitsune Faction',
                         'Stream', 'Kitsune Path', 'Varna', 'Possessed Type', 'Companion Type'],
        'Archetypes': ['archetype']
    }
    
    ignore_categories = {'other', 'specialty'}  # Categories to ignore in searches

    def func(self):
        if not self.args and not self.switches:
            # Display all possible categories
            return self.list_categories()
            
        if 'search' in self.switches:
            if not self.args:
                return self.caller.msg("Include something to search for!")
            return self.search_all(self.args.strip())
            
        if 'type' in self.switches:
            if not self.args:
                return self.caller.msg("Include a type to filter by!")
            return self.show_type(self.args.strip())
            
        if 'shifter' in self.switches:
            if not self.args:
                return self.caller.msg("Include a shifter type to filter by!")
            return self.show_shifter_gifts(self.args.strip())

        only_splat = ''
        valid_splats = {'changeling', 'fera', 'shifter', 'vampire', 'mage'}
        if any(value.lower() in valid_splats for value in self.switches):
            only_splat = next(value for value in self.switches if value.lower() in valid_splats)

        if (category := self.match_category(self.args.strip())):
            self.show_category(category, only_splat)
        elif (subject := self.match_subject(self.args.strip(), only_splat)):
            self.show_subject(subject)
        else:
            self.caller.msg(f"No matches found for '{self.args.strip()}'.")

    def format_header(self, text, width=78):
        """Format a header with consistent width."""
        return "\n" + "|r=|n" * 5 + "< " + f"|w{text}|n" + " >" + "|r=|n" * (width - len(text) - 8) + "\n"

    def format_footer(self, width=78):
        """Format a footer with consistent width."""
        return f"|r=|n" * width + "\n"

    def match_category(self, input_str):
        """Match category and return tuple of (key, display_name)."""
        input_str_lower = input_str.lower()
        
        # Handle common singular/plural forms and aliases
        category_mappings = {
            'merit': (['merit', 'merits'], 'Merits & Flaws'),
            'merits': (['merit', 'merits'], 'Merits & Flaws'),
            'flaw': (['flaw', 'flaws'], 'Merits & Flaws'),
            'flaws': (['flaw', 'flaws'], 'Merits & Flaws'),
            'merits & flaws': (['merit', 'merits', 'flaw', 'flaws'], 'Merits & Flaws'),
            'merits and flaws': (['merit', 'merits', 'flaw', 'flaws'], 'Merits & Flaws'),
            'discipline': (['discipline', 'combodiscipline', 'thaumaturgy'], 'Powers'),
            'disciplines': (['discipline', 'combodiscipline', 'thaumaturgy'], 'Powers'),
            'gift': (['gift'], 'Powers'),
            'gifts': (['gift'], 'Powers'),
            'power': (['power', 'bygone_power'], 'Powers'),
            'powers': (['power', 'bygone_power'], 'Powers'),
            'art': (['art'], 'Powers'),
            'arts': (['art'], 'Powers'),
            'realm': (['realm'], 'Powers'),
            'realms': (['realm'], 'Powers'),
            'arcanos': (['arcanos'], 'Powers'),
            'arcanoi': (['arcanos'], 'Powers'),
            'sphere': (['sphere'], 'Powers'),
            'spheres': (['sphere'], 'Powers'),
            'path': (['path'], 'Powers'),
            'paths': (['path'], 'Powers'),
            'virtue': (['virtue'], 'Virtues'),
            'virtues': (['virtue'], 'Virtues'),
            'pool': (['renown', 'arete', 'banality', 'glamour', 'essence', 'quintessence', 'paradox'], 'Pools'),
            'pools': (['renown', 'arete', 'banality', 'glamour', 'essence', 'quintessence', 'paradox'], 'Pools'),
            'blessing': (['blessing'], 'Powers'),
            'blessings': (['blessing'], 'Powers'),
            'charm': (['charm'], 'Powers'),
            'charms': (['charm'], 'Powers'),
            'hedge ritual': (['hedge_ritual'], 'Powers'),
            'hedge rituals': (['hedge_ritual'], 'Powers'),
            'special advantage': (['special_advantage'], 'Advantages'),
            'special advantages': (['special_advantage'], 'Advantages'),
            'archetype': (['archetype'], 'Archetypes'),
            'archetypes': (['archetype'], 'Archetypes'),
            'nature': (['archetype'], 'Archetypes'),
            'demeanor': (['archetype'], 'Archetypes')
        }
        
        # Check direct mappings first
        if input_str_lower in category_mappings:
            return (category_mappings[input_str_lower][0], category_mappings[input_str_lower][1])
        
        # Check display categories next
        for display_name, stat_types in self.DISPLAY_CATEGORIES.items():
            if input_str_lower == display_name.lower():
                return (stat_types, display_name)
            # Also check individual stat types within each category
            for stat_type in stat_types:
                if input_str_lower == stat_type.lower():
                    return ([stat_type], display_name)
        
        return None
    
    def match_subject(self, input_str, only_splat=''):
        """Match a specific subject by name."""
        input_str_lower = input_str.lower()
        
        # Handle special cases for combo disciplines
        if input_str_lower in ['combo', 'combo discipline', 'combodiscipline']:
            input_str_lower = 'combodiscipline'
        
        # Build query
        query = Q(name__iexact=input_str_lower)
        
        # Add splat filter if specified
        if only_splat:
            query &= Q(splat__iexact=only_splat)
            
        # Try exact match first
        result = Stat.objects.filter(query).first()
        if result:
            return result
            
        # Try partial match if no exact match found
        query = Q(name__icontains=input_str_lower)
        if only_splat:
            query &= Q(splat__iexact=only_splat)
            
        return Stat.objects.filter(query).first()

    def list_categories(self):
        string = self.format_header("+Info Categories", width=78)
        
        # Get the display categories (excluding empty ones)
        categories = [cat for cat in self.DISPLAY_CATEGORIES.keys()]
        
        # Calculate rows needed (3 columns)
        rows = (len(categories) + 2) // 3
        
        # Pad the list for complete rows
        while len(categories) % 3 != 0:
            categories.append('')
            
        # Print in rows
        for row in range(rows):
            for col in range(3):
                idx = row * 3 + col
                if idx < len(categories):
                    title = categories[idx]
                    string += title.center(26)
            string += "\r\n"
            
        string += self.format_footer(width=78)
        self.caller.msg(string)
    
    def show_category(self, category, only_splat):
        stat_types, display_name = category
        string = self.format_header(f"+Info {display_name}", width=78)
        
        # Build the base query
        if display_name == "Merits":
            # Split merits and flaws based on the input stat_types
            if 'merit' in stat_types and 'flaw' not in stat_types:
                query = Q(stat_type='merit') | Q(category='merits')
        elif display_name == "Flaws":
            query = Q(stat_type='flaw') | Q(category='flaws')
        else:
            query = Q(stat_type__in=stat_types) | Q(category__in=stat_types)
        
        # Apply splat filter if specified
        if only_splat:
            splat_query = (Q(splat__iexact=only_splat) | 
                          Q(game_line__icontains=only_splat) |
                          Q(splat__isnull=True, game_line__isnull=True))
            query &= splat_query
            
        # Get results ordered by name
        results = Stat.objects.filter(query).order_by('name')

        if not results.exists():
            if display_name == "Powers":
                # Show power subcategories even if no results
                string += "Available Power Types:\n\n"
                power_categories = {
                    'Vampire Powers': ['discipline', 'combodiscipline', 'thaumaturgy', 'necromancy', 'thaum_ritual', 'necromancy_ritual'],
                    'Werewolf Powers': ['gift', 'rite'],
                    'Mage Powers': ['sphere'],
                    'Changeling Powers': ['art', 'realm'],
                    'Inanimae Powers': ['sliver'],
                    'Sorcerer Powers': ['hedge_ritual', 'sorcery'],
                    'Psychic Powers': ['numina'],
                    'True Faith Powers': ['faith'],
                    'Possessed Powers': ['blessing', 'charm'],
                    'Companion Powers': ['special_advantage'],
                    'Other Powers': ['arcanos']
                }
                
                table = EvTable(border="none")
                table.add_column("|wPower Category|n", width=25)
                table.add_column("|wTypes|n", width=53)
                
                for category, types in power_categories.items():
                    types_str = ", ".join(t.replace('_', ' ').title() for t in types)
                    table.add_row(category, types_str)
                
                string += str(table)
                string += "\n\nUse |w+info <type>|n to see specific powers (e.g. |w+info disciplines|n)\n"

            else:
                string += f"No {display_name.lower()} found"
                if only_splat:
                    string += f" for {only_splat}"
                string += ".\r\n"
        elif display_name in ["Merits & Flaws", "Traits", "Virtues & Vices"]:
            # Merit/flaw/trait table formatting
            table = EvTable("|wName|n", "|wGame Line|n", "|wType|n", "|wValues|n", border="none")
            table.reformat_column(0, width=30, align="l")
            table.reformat_column(1, width=18, align="l")
            table.reformat_column(2, width=12, align="l")
            table.reformat_column(3, width=18, align="l")
            for result in results:
                formatted_values = "None" if not result.values else str(result.values[0]) if len(result.values) == 1 else ", ".join(map(str, result.values[:-1])) + f", or {result.values[-1]}"
                game_line = result.game_line or result.splat or "Any"
                stat_type = result.stat_type.title() if result.stat_type else result.category.title()
                table.add_row(result.name, game_line, stat_type, formatted_values)
            string += ANSIString(table)
        elif display_name == "Powers":
            # Group powers by their type
            powers_by_type = {}
            for result in results:
                stat_type = result.stat_type.replace('_', ' ').title()
                if stat_type not in powers_by_type:
                    powers_by_type[stat_type] = []
                powers_by_type[stat_type].append(result)
            
            # Display each power type in its own section
            for power_type, power_list in sorted(powers_by_type.items()):
                string += f"\n|w{power_type}|n\n"
                table = EvTable("|wName|n", "|wGame Line|n", "|wDetails|n", border="none")
                table.reformat_column(0, width=25, align="l")
                table.reformat_column(1, width=20, align="l")
                table.reformat_column(2, width=33, align="l")
                
                for power in power_list:
                    details = ""
                    if power.stat_type == 'gift':
                        if power.values:
                            details = f"Rank {power.values[0]}"
                        if hasattr(power, 'auspice') and power.auspice and power.auspice != 'none':
                            details += f" ({power.auspice})"
                    elif power.stat_type in ['discipline', 'combodiscipline', 'thaumaturgy']:
                        if hasattr(power, 'xp_cost'):
                            details = f"XP: {power.xp_cost}"
                    elif power.values:
                        details = f"Level {power.values[0]}" if len(power.values) == 1 else f"Levels {', '.join(map(str, power.values))}"
                    
                    game_line = power.game_line or power.splat or "Any"
                    table.add_row(power.name, game_line, details)
                string += ANSIString(table)
                string += "\n"
        elif display_name in ["Pools", "Attributes", "Abilities"]:
            # Stat-based table format
            table = EvTable("|wName|n", "|wGame Line|n", "|wType|n", "|wRange|n", border="none")
            table.reformat_column(0, width=25, align="l")
            table.reformat_column(1, width=20, align="l")
            table.reformat_column(2, width=15, align="l")
            table.reformat_column(3, width=18, align="l")
            for result in results:
                formatted_range = "None" if not result.values else f"{result.values[0]}-{result.values[-1]}"
                game_line = result.game_line or result.splat or "Any"
                stat_type = result.stat_type.title() if result.stat_type else result.category.title()
                table.add_row(result.name, game_line, stat_type, formatted_range)
            string += ANSIString(table)
        else:
            # Default format for other categories
            table = EvTable("|wName|n", "|wGame Line|n", "|wType|n", border="none")
            table.reformat_column(0, width=30, align="l")
            table.reformat_column(1, width=25, align="l")
            table.reformat_column(2, width=23, align="l")
            for result in results:
                game_line = result.game_line or result.splat or "Any"
                stat_type = result.stat_type.title() if result.stat_type else result.category.title()
                table.add_row(result.name, game_line, stat_type)
            string += ANSIString(table)
            
        if results.exists():
            string += f"\r\n    Found |w{len(results)}|n entries"
            if only_splat:
                string += f" for {only_splat}"
            string += ".\r\n"
        string += self.format_footer(width=78)
        self.caller.msg(string)

    def show_subject(self, subject):
        """Show detailed information about a specific subject."""
        width = 78
        string = self.format_header(f"+Info {subject.name}", width=width)
        
        # Basic info section
        string += f"  |wName:|n {subject.name}\r\n"
        if subject.splat:
            string += f"  |wSplat:|n {subject.splat}\r\n"
        if subject.game_line:
            string += f"  |wGame Line:|n {subject.game_line}\r\n"
        if subject.values:
            formatted_values = "None" if not subject.values else str(subject.values[0]) if len(subject.values) == 1 else ", ".join(map(str, subject.values[:-1])) + f", or {subject.values[-1]}"
            string += f"  |wValue(s):|n {formatted_values}\r\n"
            
        # Power-specific info
        if subject.stat_type == 'gift':
            if hasattr(subject, 'shifter_type') and subject.shifter_type:
                if isinstance(subject.shifter_type, list):
                    shifter_types = ", ".join(stype for stype in subject.shifter_type)
                else:
                    shifter_types = subject.shifter_type
                if shifter_types and shifter_types.lower() != 'none':
                    string += f"  |wShifter Type(s):|n {shifter_types}\r\n"
            if subject.auspice and subject.auspice != 'none':
                if isinstance(subject.auspice, list):
                    auspices = ", ".join(auspice for auspice in subject.auspice)
                    string += f"  |wAuspices:|n {auspices}\r\n"
                else:
                    string += f"  |wAuspice:|n {subject.auspice}\r\n"
            if subject.breed and subject.breed != 'none':
                string += f"  |wBreed:|n {subject.breed}\r\n"
            if subject.tribe:
                if isinstance(subject.tribe, list):
                    tribes = ", ".join(tribe for tribe in subject.tribe)
                else:
                    tribes = subject.tribe
                string += f"  |wTribe:|n {tribes}\r\n"
            if subject.camp:
                string += f"  |wCamp:|n {subject.camp}\r\n"
            if subject.source:
                string += f"  |wSource:|n {subject.source}\r\n"
        elif subject.stat_type in ['discipline', 'combodiscipline']:
            if hasattr(subject, 'xp_cost') and subject.xp_cost is not None:
                string += f"  |wXP Cost:|n {subject.xp_cost}\r\n"
            if hasattr(subject, 'prerequisites'):
                if isinstance(subject.prerequisites, (list, tuple)):
                    prereqs = ", ".join(subject.prerequisites)
                else:
                    prereqs = str(subject.prerequisites)
                string += f"  |wPrerequisites:|n {prereqs}\r\n"
        
        # Description and system
        string += "\r\n"
        if subject.description:
            string += f"{subject.description}\r\n"
        if hasattr(subject, 'system') and subject.system:
            string += f"\n|wSystem:|n {subject.system}\r\n"
            
        string += self.format_footer(width=78)
        self.caller.msg(string)
    
    def search_all(self, input_str):
        # Get all valid stat types from our DISPLAY_CATEGORIES
        valid_stat_types = []
        for stat_types in self.DISPLAY_CATEGORIES.values():
            valid_stat_types.extend(stat_types)
        
        # Remove ignored categories
        valid_stat_types = [st for st in valid_stat_types if st not in self.ignore_categories]
        
        # First try exact name match
        exact_matches = Stat.objects.filter(
            name__iexact=input_str,
            stat_type__in=valid_stat_types
        )
        
        if exact_matches.exists():
            if len(exact_matches) == 1:
                return self.show_subject(exact_matches[0])
            matches = exact_matches
        else:
            # Try partial name match
            name_matches = Stat.objects.filter(
                name__icontains=input_str,
                stat_type__in=valid_stat_types
            )
            
            if name_matches.exists():
                matches = name_matches
            else:
                # If no name matches, search by description
                matches = Stat.objects.filter(
                    description__icontains=input_str,
                    stat_type__in=valid_stat_types
                )
                
        if not matches.exists():
            return self.caller.msg(f"No matches found containing the text '{input_str}'.")
            
        string = self.format_header(f"+Info Search: {input_str}", width=78)
        table = EvTable("|wName|n", "|wSplat|n", "|wType|n", "|wDescription|n", border="none")
        table.reformat_column(0, width=25, align="l")
        table.reformat_column(1, width=15, align="l")
        table.reformat_column(2, width=15, align="l")
        table.reformat_column(3, width=23, align="l")
        
        for result in matches[:10]:
            desc = result.description[:20] + "..." if result.description and len(result.description) > 20 else ""
            table.add_row(
                result.name,
                result.splat or "Any",
                result.stat_type.title(),
                desc
            )
            
        string += ANSIString(table)
        matches_string = f"\r\n    Found |w{len(matches)}|n matches"
        if len(matches) > 10:
            matches_string += " (showing first 10)"
        string += matches_string + "\r\n"
        string += self.format_footer(width=78)
        self.caller.msg(string)
                    
    def show_type(self, stat_type):
        """Show all entries of a specific type."""
        # Handle special cases for combo disciplines
        if stat_type.lower() in ['combo', 'combo discipline', 'combodiscipline']:
            stat_type = 'combodiscipline'
            
        # Handle merits and flaws special cases
        if stat_type.lower() in ['merit', 'merits']:
            query = Q(stat_type='merit') | Q(category='merits')
        elif stat_type.lower() in ['flaw', 'flaws']:
            query = Q(stat_type='flaw') | Q(category='flaws')
        else:
            if stat_type not in self.valid_types:
                self.caller.msg(f"No stat type found matching '{stat_type}'.")
                return
            query = Q(stat_type=stat_type)
            
        results = Stat.objects.filter(query).order_by('name')
        if not results.exists():
            self.caller.msg(f"No entries found of type '{stat_type}'.")
            return
            
        string = self.format_header(f"+Info Type: {stat_type.title()}")
        string += self.format_stat_list(results)
        string += self.format_footer()
        self.caller.msg(string)
                    
    def show_shifter_gifts(self, shifter_type):
        """Show all gifts for a specific shifter type."""
        # Normalize the input
        shifter_type_lower = shifter_type.lower()
        
        # First, let's check what we have in the database
        all_gifts = Stat.objects.filter(stat_type='gift')
        if not all_gifts.exists():
            return self.caller.msg("No gifts found in the database.")
            
        # Build a comprehensive query
        query = Q(stat_type='gift') & (
            Q(shifter_type=shifter_type_lower) |  # Exact match
            Q(breed=shifter_type_lower) |
            Q(tribe=shifter_type_lower) |
            Q(auspice=shifter_type_lower) |
            # Search in description for references to the shifter type
            Q(description__icontains=f" {shifter_type_lower} ") |  # Full word match
            Q(description__icontains=f"{shifter_type_lower}'s") |  # Possessive form
            Q(description__icontains=f"{shifter_type_lower}.") |   # End of sentence
            Q(description__icontains=f"{shifter_type_lower},") |   # In a list
            Q(description__icontains=f"{shifter_type_lower}s")     # Plural form
        )
        
        results = Stat.objects.filter(query).order_by('name')
        
        if not results.exists():
            # Show the actual SQL query for debugging
            str_query = str(Stat.objects.filter(query).query)
            return self.caller.msg(f"No gifts found for shifter type '{shifter_type}'.\nDebug - SQL Query: {str_query}")
        
        string = self.format_header(f"+Info {shifter_type.title()} Gifts", width=78)
        
        # Use table format for better organization
        # Adjust column widths to total 78 characters including borders
        table = EvTable("|wName|n", "|wRank|n", "|wDetails|n", "|wDescription|n", border="none")
        table.reformat_column(0, width=20, align="l")  # Name
        table.reformat_column(1, width=6, align="l")   # Rank
        table.reformat_column(2, width=15, align="l")  # Details
        table.reformat_column(3, width=37, align="l")  # Description (remaining space)
        
        for result in results:
            rank = str(result.values[0]) if result.values else "N/A"
            
            details = []
            if result.auspice and result.auspice != 'none':
                details.append(result.auspice)
            if result.breed and result.breed != 'none':
                details.append(result.breed)
            if result.tribe and result.tribe != 'none':
                if isinstance(result.tribe, list):
                    details.extend(result.tribe)
                else:
                    details.append(result.tribe)
            if result.shifter_type and result.shifter_type != 'none':
                details.append(result.shifter_type)
            
            # Truncate details if too long
            details_str = ", ".join(str(d) for d in details) if details else ""
            if len(details_str) > 15:
                details_str = details_str[:12] + "..."
            
            # Truncate description to fit in column
            desc = result.description if result.description else ""
            if len(desc) > 34:  # 37 - 3 for "..."
                # Try to break at a word boundary
                desc = desc[:34].rsplit(' ', 1)[0] + "..."
            
            table.add_row(result.name, rank, details_str, desc)
            
        string += ANSIString(table)
        string += f"\r\n    Found |w{len(results)}|n gifts for {shifter_type.title()}.\r\n"
        string += self.format_footer(width=78)
        self.caller.msg(string)
                    
    def format_stat_list(self, stats, width=78):
        string = ""
        if not stats:
            return string
            
        # Format header based on stat type
        if stats[0].stat_type == "combodiscipline":
            string += f" {'Name'.ljust(30)}{'XP Cost'.ljust(10)}{'Prerequisites'.ljust(38)}\n"
            for stat in stats:
                # Handle prerequisites that could be string or list
                if hasattr(stat, "prerequisites"):
                    if isinstance(stat.prerequisites, (list, tuple)):
                        prereqs = ", ".join(stat.prerequisites)
                    else:
                        prereqs = str(stat.prerequisites)
                else:
                    prereqs = ""
                    
                xp = str(stat.xp_cost) if hasattr(stat, "xp_cost") else ""
                string += f" {stat.name.ljust(30)}{xp.ljust(10)}{prereqs.ljust(38)}\n"
        else:
            # Original formatting for other stat types
            string += f" {'Name'.ljust(30)}{'Splat'.ljust(20)}{'Values'.ljust(20)}\n"
            for stat in stats:
                values = str(stat.values[0]) if len(stat.values) == 1 else ", ".join(map(str, stat.values[:-1])) + f", or {stat.values[-1]}" if stat.values else ""
                string += f" {stat.name.ljust(30)}{(stat.splat or '').ljust(20)}{values.ljust(20)}\n"
        
        count = len(stats)
        if count > 0:
            string += f"    There were {count} entries of type '{stats[0].stat_type}'.\n"
        return string
