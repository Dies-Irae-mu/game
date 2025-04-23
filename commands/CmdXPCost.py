from evennia import default_cmds
from evennia.utils.evtable import EvTable
from decimal import Decimal
from commands.CmdCheck import CmdCheck
from world.wod20th.models import Stat
from django.db.models import Q
from world.wod20th.utils.stat_mappings import (
    UNIVERSAL_BACKGROUNDS, VAMPIRE_BACKGROUNDS, CHANGELING_BACKGROUNDS,
    MAGE_BACKGROUNDS, TECHNOCRACY_BACKGROUNDS, TRADITIONS_BACKGROUNDS,
    NEPHANDI_BACKGROUNDS, SHIFTER_BACKGROUNDS, SORCERER_BACKGROUNDS,
    COMBAT_SPECIAL_ADVANTAGES, SPECIAL_ADVANTAGES
)
from world.wod20th.utils.xp_costs import *
from world.wod20th.utils.xp_utils import calculate_xp_cost, get_current_rating, SHIFTER_MAPPINGS

class CmdXPCost(default_cmds.MuxCommand):
    """
    View costs for character advancement.
    
    Usage:
      +costs              - Show all available purchases
      +costs/attributes   - Show attribute costs
      +costs/abilities    - Show ability costs
      +costs/secondary_abilities - Show secondary ability costs
      +costs/backgrounds  - Show background costs
      +costs/powers      - Show power/gift costs
      +costs/pools       - Show pool costs
      +costs/disciplines - Show discipline and combo discipline costs
    """
    
    key = "+costs"
    aliases = ["costs"]
    locks = "cmd:all()"
    help_category = "XP Commands"

    def func(self):
        """Execute command"""
        if not self.switches:
            # Show overview of all categories
            self._display_all_costs(self.caller)
            return
            
        switch = self.switches[0].lower()
        if switch in ["attributes", "abilities", "secondary_abilities", "backgrounds", "powers", "pools", "disciplines"]:
            self._display_category_costs(self.caller, switch)
        else:
            self.caller.msg("Invalid switch. Use +help costs for usage information.")

    def _display_category_costs(self, character, category):
        """Display costs for a specific category"""
        current_xp = character.db.xp.get('current', 0) if character.db.xp else 0
        total_width = 78
        
        # Create section header
        header = self._format_table_header(category, total_width)
        
        # Use direct string formatting for all categories
        if category == "attributes":
            display = self._display_attributes_direct(character, current_xp, total_width)
            character.msg(f"{header}{display}")
            return
        elif category == "abilities":
            display = self._display_abilities_direct(character, current_xp, total_width)
            character.msg(f"{header}{display}")
            return
        elif category == "secondary_abilities":
            display = self._display_secondary_abilities_direct(character, current_xp, total_width)
            character.msg(f"{header}{display}")
            return
        elif category == "backgrounds":
            display = self._display_backgrounds_direct(character, current_xp, total_width)
            character.msg(f"{header}{display}")
            return
        elif category == "pools":
            display = self._display_pools_direct(character, current_xp, total_width)
            character.msg(f"{header}{display}")
            return
        # Special case for powers - use direct string formatting for all splat types
        elif category == "powers":
            splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower()
            
            # Generate the display based on splat type
            if splat == 'vampire':
                display = self._display_vampire_powers_direct(character, current_xp, total_width)
            elif splat == 'shifter':
                display = self._display_shifter_powers_direct(character, current_xp, total_width)
            elif splat == 'mage':
                display = self._display_mage_powers_direct(character, current_xp, total_width)
            elif splat == 'changeling':
                display = self._display_changeling_powers_direct(character, current_xp, total_width)
            elif splat == 'possessed':
                display = self._display_possessed_powers_direct(character, current_xp, total_width)
            elif splat == 'mortal+':
                display = self._display_mortalplus_powers_direct(character, current_xp, total_width)
            elif splat == 'companion':
                display = self._display_companion_powers_direct(character, current_xp, total_width)
            else:
                # Create a simple table for non-specific splat types
                display = self._create_basic_table(total_width, ["No powers available for your character type."])
                
            character.msg(f"{header}{display}")
            return
        elif category == "disciplines" and character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower() == 'vampire':
            display = self._display_disciplines_costs_direct(character, current_xp, total_width)
            character.msg(f"{header}{display}")
            return
            
        # For any remaining categories, use the old EvTable approach as fallback
        table = self._create_cost_table(total_width)
        
        # Handle remaining categories with the old approach
        if category == "attributes":
            self._display_attributes_costs(character, table, current_xp)
        elif category == "abilities":
            self._display_abilities_costs(character, table, current_xp)
        elif category == "secondary_abilities":
            self._display_secondary_abilities_costs(character, table, current_xp)
        elif category == "backgrounds":
            self._display_backgrounds_costs(character, table, current_xp)
        elif category == "pools":
            self._display_pools_costs(character, table, current_xp)
        elif category == "disciplines" and character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower() == 'vampire':
            self._display_disciplines_costs(character, table, current_xp)
        
        # Send the formatted output with header and footer
        footer = f"|b{'-' * total_width}|n"
        character.msg(f"{header}{table}\n{footer}")

    def _format_table_header(self, category, total_width=78):
        """Format a header for the costs table based on category"""
        category_titles = {
            "attributes": "Attribute Costs",
            "abilities": "Ability Costs",
            "secondary_abilities": "Secondary Ability Costs",
            "backgrounds": "Background Costs",
            "powers": "Power Costs",
            "pools": "Pool Costs", 
            "disciplines": "Special Discipline Costs"
        }
        
        title = category_titles.get(category, f"{category.title()} Costs")
        
        # Calculate padding to center the title
        padding = (total_width - len(title) - 2) // 2
        
        # Create the formatted header
        header = f"|b{'-' * total_width}|n\n"
        header += f"|b{' ' * padding}{title}{' ' * (total_width - len(title) - padding)}|n\n"
        header += f"|b{'-' * total_width}|n\n"
        
        return header

    def _get_max_rating(self, category, subcategory, stat_name, character):
        """
        Get the maximum possible rating for a stat based on category and character type.
        
        Args:
            category (str): The stat category
            subcategory (str): The stat subcategory
            stat_name (str): The name of the stat
            character: The character to check
            
        Returns:
            int: The maximum possible rating
        """
        # Get character's splat
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        mortal_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
        
        # Default maximums
        default_max = 5
        
        # Specific maximums based on category
        if category == 'attributes':
            return default_max
            
        elif category in ['abilities', 'secondary_abilities']:
            return default_max
            
        elif category == 'backgrounds':
            # Most backgrounds max at 5
            background_max = {
                'Generation': 7,  # Special case for vampires
                'Pure Breed': 5,
                'Resources': 5,
                'Status': 5,
                'Contacts': 5,
                'Allies': 5
            }
            return background_max.get(stat_name, default_max)
            
        elif category == 'powers':
            # Powers usually max at 5 for most types
            if subcategory == 'discipline':
                return default_max
            elif subcategory == 'gift':
                return default_max
            elif subcategory == 'sphere':
                return default_max
            elif subcategory == 'art':
                return default_max
            elif subcategory == 'realm':
                return default_max
            elif subcategory in ['thaumaturgy', 'necromancy']:
                return default_max
            else:
                return default_max
                
        elif category == 'pools':
            if subcategory == 'dual':
                pool_max = {
                    'Willpower': 10,
                    'Rage': 10,
                    'Gnosis': 10,
                    'Glamour': 10
                }
                return pool_max.get(stat_name, default_max)
            elif subcategory == 'advantage':
                # Arete usually maxes at 10 for mages
                if stat_name == 'Arete':
                    return 10
                return default_max
                
        # Default to 5 for anything not specifically handled
        return default_max
        
    def _get_affordable_status(self, cost, current_xp, requires_approval):
        """Format the affordability and approval status of a purchase."""
        if requires_approval:
            return f"|r(ST Approval)|n"
        elif cost > current_xp:
            return f"|rX (Can't afford)|n"
        else:
            return f"|gY (Auto-spend)|n"

    def _display_attributes_direct(self, character, current_xp, total_width=78):
        """Display attributes using direct string formatting"""
        # Get base table formatting
        table_base = self._powers_table_base(character, current_xp, total_width)
        output = table_base['output']
        
        # Add attributes sections
        subcategories = [
            ('physical', ['Strength', 'Dexterity', 'Stamina']),
            ('social', ['Charisma', 'Manipulation', 'Appearance']),
            ('mental', ['Perception', 'Intelligence', 'Wits'])
        ]
        
        for idx, (subcat, stats) in enumerate(subcategories):
            # Add section header
            if idx > 0:
                output += table_base['format_empty_row']()
            
            # Calculate exact padding to ensure right border aligns perfectly
            header_text = f"{subcat.title()} Attributes:"
            # Total width (78) - 2 (for border pipes) - 2 (for initial and final spaces) - visible text length - 4 (for |c and |n)
            padding = total_width - 2 - 1 - len(header_text)
            output += f"| |c{header_text}|n{' ' * padding}|\n"
            output += table_base['format_empty_row']()
            
            for stat in stats:
                # Get the current value
                current = character.db.stats.get('attributes', {}).get(subcat, {}).get(stat, {}).get('perm', 0)
                max_rating = self._get_max_rating('attributes', subcat, stat, character)
                
                if current < max_rating:  # Only show if below max rating
                    next_rating = current + 1
                    try:
                        cost, requires_approval = calculate_xp_cost(
                            character, 
                            False,  # is_staff_spend
                            stat, 
                            category='attributes',
                            subcategory=subcat,
                            current_rating=current,
                            new_rating=next_rating
                        )
                        status = self._get_affordable_status(cost, current_xp, requires_approval)
                        output += table_base['format_entry'](stat, current, next_rating, cost, status)
                    except Exception as e:
                        character.msg(f"Error calculating cost for {stat}: {str(e)}")
        
        # Add table footer
        output += table_base['format_border']()
        
        return output
    
    def _display_abilities_direct(self, character, current_xp, total_width=78):
        """Display abilities using direct string formatting"""
        # Get base table formatting
        table_base = self._powers_table_base(character, current_xp, total_width)
        output = table_base['output']
        
        # Get character's splat and other relevant info
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        clan = character.db.stats.get('other', {}).get('clan', {}).get('Clan', {}).get('perm', '')
        shifter_type = character.db.stats.get('other', {}).get('shifter_type', {}).get('Shifter Type', {}).get('perm', '')
        
        # Primary abilities
        subcategories = [
            ('talent', ['Alertness', 'Athletics', 'Awareness', 'Brawl', 'Empathy',
                       'Expression', 'Intimidation', 'Leadership', 'Streetwise', 'Subterfuge']),
            ('skill', ['Animal Ken', 'Crafts', 'Drive', 'Etiquette', 'Firearms',
                      'Larceny', 'Melee', 'Performance', 'Stealth', 'Survival']),
            ('knowledge', ['Academics', 'Computer', 'Enigmas', 'Finance', 'Investigation', 'Law',
                         'Medicine', 'Occult', 'Politics', 'Science', 'Technology'])
        ]
        
        # Add splat-specific primary abilities
        self._add_splat_specific_abilities(splat, shifter_type, clan, subcategories)
        
        # Sort abilities alphabetically within each subcategory
        for i in range(len(subcategories)):
            subcategories[i] = (subcategories[i][0], sorted(subcategories[i][1]))
        
        # Add primary abilities section with exact padding
        header_text = "Primary Abilities:"
        # Calculate padding to ensure 78 characters total width
        visible_length = len(header_text)
        padding = total_width - 3 - visible_length  # 4 = left and right pipes + spaces
        output += f"| |c{header_text}|n{' ' * padding}|\n"
        
        for idx, (subcat, stats) in enumerate(subcategories):
            # Add subcategory header
            if idx > 0:
                output += table_base['format_empty_row']()
            
            # Use consistent section header formatting
            output += table_base['format_section_header'](f"{subcat.title()} Abilities")
            
            for stat in stats:
                current = int(character.get_stat('abilities', subcat, stat) or 0)
                max_rating = self._get_max_rating('abilities', subcat, stat, character)
                
                if current < max_rating:
                    next_rating = current + 1
                    try:
                        cost, requires_approval = calculate_xp_cost(
                            character, 
                            False,  # is_staff_spend 
                            stat, 
                            category='abilities',
                            subcategory=subcat,
                            current_rating=current,
                            new_rating=next_rating
                        )
                        status = self._get_affordable_status(cost, current_xp, requires_approval)
                        output += table_base['format_entry'](stat, current, next_rating, cost, status)
                    except Exception as e:
                        character.msg(f"Error calculating cost for {stat}: {str(e)}")
        
        # Add table footer
        output += table_base['format_border']()
        
        return output
        
    def _display_secondary_abilities_direct(self, character, current_xp, total_width=78):
        """Display secondary abilities using direct string formatting"""
        # Get base table formatting
        table_base = self._powers_table_base(character, current_xp, total_width)
        output = table_base['output']
        
        # Get character's splat
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        
        # Secondary abilities subcategories
        secondary_subcategories = [
            ('secondary_talent', ['Carousing', 'Diplomacy', 'Intrigue', 'Mimicry', 'Scrounging', 'Seduction', 'Style']),
            ('secondary_skill', ['Archery', 'Fortune-Telling', 'Fencing', 'Gambling', 'Jury-Rigging', 'Pilot', 'Torture']),
            ('secondary_knowledge', ['Area Knowledge', 'Cultural Savvy', 'Demolitions', 'Herbalism', 'Media', 'Power-Brokering', 'Vice'])
        ]
        
        # Add Mage-specific secondary abilities
        if splat.lower() == 'mage':
            secondary_subcategories[0][1].extend(['High Ritual', 'Blatancy', 'Do'])
            secondary_subcategories[1][1].extend(['Microgravity Ops', 'Energy Weapons', 'Helmsman', 'Biotech'])
            secondary_subcategories[2][1].extend(['Hypertech', 'Cybernetics', 'Paraphysics', 'Xenobiology'])
        
        # Sort secondary abilities alphabetically within each subcategory
        for i in range(len(secondary_subcategories)):
            secondary_subcategories[i] = (secondary_subcategories[i][0], sorted(secondary_subcategories[i][1]))
        
        # Add secondary abilities section with exact padding
        header_text = "Secondary Abilities:"
        visible_length = len(header_text) + 4  # +4 for |c and |n color codes
        padding = total_width - visible_length  # 4 = left and right pipes + spaces
        output += f"| |c{header_text}|n{' ' * padding} |\n"
        
        for idx, (subcat, stats) in enumerate(secondary_subcategories):
            display_subcat = subcat.replace('secondary_', '').title()
            
            # Add subcategory header
            if idx > 0:
                output += table_base['format_empty_row']()
            
            # Use fixed format for section headers without any tab characters
            # This directly creates the section header with proper spacing
            section_title = f"{display_subcat} Abilities"
            section_title_str = f" {section_title} "
            colored_title = f"|y{section_title_str}|n"
            visible_width = len(section_title_str)
            total_dash_count = total_width - 4 - visible_width  # -4 for left and right border pipes and spaces
            left_dashes = total_dash_count // 2
            right_dashes = total_dash_count - left_dashes
            formatted_header = f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
            output += formatted_header
            
            for stat in stats:
                current = int(character.get_stat('secondary_abilities', subcat, stat) or 0)
                max_rating = self._get_max_rating('secondary_abilities', subcat, stat, character)
                
                if current < max_rating:
                    next_rating = current + 1
                    try:
                        cost, requires_approval = calculate_xp_cost(
                            character,
                            False,  # is_staff_spend
                            stat, 
                            category='secondary_abilities',
                            subcategory=subcat,
                            current_rating=current,
                            new_rating=next_rating
                        )
                        status = self._get_affordable_status(cost, current_xp, requires_approval)
                        output += table_base['format_entry'](stat, current, next_rating, cost, status)
                    except Exception as e:
                        character.msg(f"Error calculating cost for {stat}: {str(e)}")
        
        # Add table footer
        output += table_base['format_border']()
        
        return output
        
    def _display_backgrounds_direct(self, character, current_xp, total_width=78):
        """Display backgrounds using direct string formatting"""
        # Get base table formatting
        table_base = self._powers_table_base(character, current_xp, total_width)
        output = table_base['output']
        
        # Get character's splat to determine available backgrounds
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        
        # Start with universal backgrounds available to all splats
        available_backgrounds = list(UNIVERSAL_BACKGROUNDS)
        
        # Add splat-specific backgrounds
        if splat.lower() == 'vampire':
            available_backgrounds.extend(VAMPIRE_BACKGROUNDS)
        elif splat.lower() == 'changeling':
            available_backgrounds.extend(CHANGELING_BACKGROUNDS)
        elif splat.lower() == 'mage':
            available_backgrounds.extend(MAGE_BACKGROUNDS)
            
            # Check mage affiliation for additional backgrounds
            affiliation = character.db.stats.get('identity', {}).get('lineage', {}).get('Affiliation', {}).get('perm', '')
            if affiliation == 'Technocracy':
                available_backgrounds.extend(TECHNOCRACY_BACKGROUNDS)
            elif affiliation == 'Traditions':
                available_backgrounds.extend(TRADITIONS_BACKGROUNDS)
            elif affiliation == 'Nephandi':
                available_backgrounds.extend(NEPHANDI_BACKGROUNDS)
        elif splat.lower() == 'shifter':
            available_backgrounds.extend(SHIFTER_BACKGROUNDS)
        elif splat.lower() == 'mortal+':
            available_backgrounds.extend(SORCERER_BACKGROUNDS)
        
        # Sort and remove duplicates
        available_backgrounds = sorted(set(available_backgrounds))
        
        # Add backgrounds section with exact padding
        header_text = "Backgrounds:"
        visible_length = len(header_text)
        padding = total_width - 3 - visible_length  # 4 = left and right pipes + spaces
        output += f"| |c{header_text}|n{' ' * padding}|\n"
        output += table_base['format_empty_row']()
        
        for stat in available_backgrounds:
            current = int(character.get_stat('backgrounds', 'background', stat) or 0)
            max_rating = self._get_max_rating('backgrounds', 'background', stat, character)
            
            if current < max_rating:
                next_rating = current + 1
                try:
                    cost, requires_approval = calculate_xp_cost(
                        character,
                        False,  # is_staff_spend
                        stat, 
                        category='backgrounds',
                        subcategory='background',
                        current_rating=current,
                        new_rating=next_rating
                    )
                    status = self._get_affordable_status(cost, current_xp, requires_approval)
                    output += table_base['format_entry'](stat, current, next_rating, cost, status)
                except Exception as e:
                    character.msg(f"Error calculating cost for {stat}: {str(e)}")
        
        # Add table footer
        output += table_base['format_border']()
        
        return output
        
    def _display_pools_direct(self, character, current_xp, total_width=78):
        """Display pool costs using direct string formatting"""
        # Get base table formatting
        table_base = self._powers_table_base(character, current_xp, total_width)
        output = table_base['output']
        
        # Get character's splat to determine available pools
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower()
        
        # Only show pools that can be purchased with XP
        purchasable_pools = ['Willpower']  # Willpower is universal
        
        # Add splat-specific purchasable pools
        if splat == 'shifter':
            purchasable_pools.extend(['Rage', 'Gnosis'])
        elif splat == 'mage':
            purchasable_pools.append('Arete')
        elif splat == 'changeling':
            purchasable_pools.append('Glamour')
        
        # Sort pools
        purchasable_pools = sorted(set(purchasable_pools))
        
        # Add pools section with exact padding
        header_text = "Pools:"
        # Calculate padding to ensure 78 characters total width
        visible_length = len(header_text)
        padding = total_width - 4 - visible_length  # 4 = left and right pipes + spaces
        output += f"| |c{header_text}|n{' ' * padding}|\n"
        output += table_base['format_empty_row']()
        
        for stat in purchasable_pools:
            # Determine the correct category and subcategory for the pool
            if stat in ['Willpower', 'Rage', 'Gnosis', 'Glamour']:
                category_name = 'pools'
                subcategory = 'dual'
            elif stat == 'Arete':
                category_name = 'pools'
                subcategory = 'advantage'
            else:
                continue  # Skip any non-purchasable pools
            
            # Get current value
            current = int(character.get_stat(category_name, subcategory, stat) or 0)
            
            # Determine max rating based on pool type
            max_rating = self._get_max_rating(category_name, subcategory, stat, character)
            
            if current < max_rating:
                next_rating = current + 1
                try:
                    cost, requires_approval = calculate_xp_cost(
                        character,
                        False,  # is_staff_spend
                        stat, 
                        category=category_name,
                        subcategory=subcategory,
                        current_rating=current,
                        new_rating=next_rating
                    )
                    
                    # Override requires_approval based on AUTO_APPROVE rules
                    if stat in ['Willpower', 'Rage', 'Gnosis', 'Glamour']:
                        requires_approval = (next_rating > 5)  # Pools require approval for 6+
                    elif stat == 'Arete' or stat == 'Enlightenment':
                        requires_approval = (next_rating > 1)  # Advantage pools require approval for 2+
                    
                    status = self._get_affordable_status(cost, current_xp, requires_approval)
                    output += table_base['format_entry'](stat, current, next_rating, cost, status)
                except Exception as e:
                    character.msg(f"Error calculating cost for {stat}: {str(e)}")
        
        # Add note about non-purchasable pools
        output += table_base['format_empty_row']()
        
        note1 = "Note: Other pools like Blood, Banality, Quintessence,"
        # Calculate padding to ensure 78 characters total width
        visible_length = len(note1)
        padding = total_width - 4 - visible_length  # 4 = left and right pipes + spaces
        output += f"| |r{note1}|n{' ' * padding}|\n"
        
        note2 = "Paradox, Resonance, and Renown cannot be purchased with XP."
        # Calculate padding to ensure 78 characters total width
        visible_length = len(note2)
        padding = total_width - 4 - visible_length  # 4 = left and right pipes + spaces
        output += f"| |r{note2}|n{' ' * padding}|\n"
        
        # Add table footer
        output += table_base['format_border']()
        
        return output

    def _powers_table_base(self, character, current_xp, total_width=78):
        """Create base structure for powers table with consistent formatting"""
        # Calculate column widths to ensure total width is exactly 78 including borders
        # Total = 1 (left border) + 1 (space after left border) + col1 + col2 + col3 + col4 + col5 + 1 (space before right border) + 1 (right border) = 78
        name_width = 24
        current_width = 10
        next_width = 10
        cost_width = 10
        status_width = 24  # Adjusted to ensure total width is exactly 78
        
        # Common formatting functions
        def format_border():
            return f"+{'-' * (total_width - 2)}+\n"
            
        def format_header_row():
            return f"| {'Purchase':<{name_width}}{'Current':<{current_width}}{'Next':<{next_width}}{'Cost':<{cost_width}}{'Autospend?':<{status_width - 4}} |\n"
            
        def format_empty_row():
            return f"|{' ' * (total_width - 2)}|\n"
            
        def format_section_header(title):
            """
            Format a section header with dashes and color.
            
            This function creates a centered, colored section header with dashes on both sides.
            It ensures that the total width matches the table width and that no tab characters
            are included in the output.
            """
            # Create the centered colored title
            title_str = f" {title} "
            colored_title = f"|y{title_str}|n"
            
            # Calculate visible width - what will display on screen
            visible_width = len(title_str)  # Spaces and text only
            
            # Calculate dash counts for left and right
            total_dash_count = total_width - 4 - visible_width  # -4 for left and right border chars and spaces
            left_dashes = total_dash_count // 2
            right_dashes = total_dash_count - left_dashes
            
            # Explicitly build the header with no tabs
            header = "| " + "-" * left_dashes + colored_title + "-" * right_dashes + " |\n"
            
            return header
            
        def format_entry(name, current, next_rating, cost, status, indent=2):
            indent_str = " " * indent
            
            # Truncate name if it's too long (accounting for indent)
            max_name_length = name_width - indent
            if len(name) > max_name_length:
                name = name[:max_name_length-3] + "..."
                
            # Ensure exact alignment with header row
            formatted_name = f"{indent_str}{name}"
            formatted_name = formatted_name.ljust(name_width)
                
            # Format each column with exact width
            formatted_current = str(current).ljust(current_width)
            formatted_next = str(next_rating).ljust(next_width)
            formatted_cost = str(cost).ljust(cost_width)
            
            # Calculate how much padding we need for the status field
            status_padding = status_width - len(status)
            
            # Return a precisely formatted row with exact spacing
            return f"| {formatted_name}{formatted_current}{formatted_next}{formatted_cost}{status}{' ' * status_padding} |\n"
        
        # Build base table structure
        output = format_border()
        output += format_header_row()
        output += format_border()
        
        return {
            'output': output,
            'format_border': format_border,
            'format_header_row': format_header_row,
            'format_empty_row': format_empty_row,
            'format_section_header': format_section_header,
            'format_entry': format_entry
        }

    def _display_vampire_powers_direct(self, character, current_xp, total_width=78):
        """Display vampire powers using direct string formatting instead of EvTable"""
        # Get character's clan
        clan = character.db.stats.get('identity', {}).get('lineage', {}).get('Clan', {}).get('perm', '')
        
        # Get current disciplines
        current_disciplines = character.db.stats.get('powers', {}).get('discipline', {})
        
        # Define disciplines that can be purchased with autospend
        autospend_disciplines = ['Potence', 'Celerity', 'Fortitude', 'Obfuscate', 'Auspex']
        
        # Import clan disciplines mapping (lazy import to avoid circular dependencies)
        from world.wod20th.utils.vampire_utils import CLAN_DISCIPLINES
        
        # Create a set of displayed disciplines to avoid duplicates
        displayed_disciplines = set()
        
        # Get base table formatting
        table_base = self._powers_table_base(character, current_xp, total_width)
        output = table_base['output']
        
        # Add disciplines section header
        header_text = "Disciplines:"
        visible_length = len(header_text) + 4  # +4 for |c and |n color codes
        padding = total_width - visible_length
        output += f"| |c{header_text}|n{' ' * padding} |\n"
        output += table_base['format_empty_row']()
        
        # 1. Clan disciplines section
        if clan and clan.lower() not in ['caitiff', 'pander']:
            clan_disciplines = CLAN_DISCIPLINES.get(clan, [])
            if clan_disciplines:
                # Add section header using the same format as other methods
                section_title = f"{clan} Clan Disciplines"
                section_title_str = f" {section_title} "
                colored_title = f"|y{section_title_str}|n"
                visible_width = len(section_title_str)
                total_dash_count = total_width - 4 - visible_width
                left_dashes = total_dash_count // 2
                right_dashes = total_dash_count - left_dashes
                output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
                
                for discipline in clan_disciplines:
                    # Skip if already displayed
                    if discipline in displayed_disciplines:
                        continue
                        
                    # Get current rating
                    current = current_disciplines.get(discipline, {}).get('perm', 0)
                    
                    # Only show if below max rating
                    if current < 5:
                        next_rating = current + 1
                        try:
                            cost, requires_approval = calculate_xp_cost(
                                character=character, 
                                is_staff_spend=False,
                                stat_name=discipline, 
                                category='powers',
                                subcategory='discipline',
                                current_rating=current,
                                new_rating=next_rating
                            )
                            status = self._get_affordable_status(cost, current_xp, requires_approval)
                            
                            # Use the discipline name directly without highlighting
                            output += table_base['format_entry'](discipline, current, next_rating, cost, status)
                            displayed_disciplines.add(discipline)
                        except Exception as e:
                            character.msg(f"Error calculating cost for {discipline}: {str(e)}")
        
        # 2. Current disciplines that are in the autospend list (excluding clan disciplines)
        current_autospend = [d for d in current_disciplines.keys() 
                           if d in autospend_disciplines and d not in displayed_disciplines]
                           
        if current_autospend:
            # Add empty row if previous section had content
            if displayed_disciplines:
                output += table_base['format_empty_row']()
                
            # Section header using consistent format
            section_title = "Current Common Disciplines"
            section_title_str = f" {section_title} "
            colored_title = f"|y{section_title_str}|n"
            visible_width = len(section_title_str)
            total_dash_count = total_width - 4 - visible_width
            left_dashes = total_dash_count // 2
            right_dashes = total_dash_count - left_dashes
            output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
            
            for discipline in current_autospend:
                # Get current rating
                current = current_disciplines.get(discipline, {}).get('perm', 0)
                
                # Only show if below max rating
                if current < 5:
                    next_rating = current + 1
                    try:
                        cost, requires_approval = calculate_xp_cost(
                            character=character, 
                            is_staff_spend=False,
                            stat_name=discipline, 
                            category='powers',
                            subcategory='discipline',
                            current_rating=current,
                            new_rating=next_rating
                        )
                        status = self._get_affordable_status(cost, current_xp, requires_approval)
                        
                        # Add custom indentation for autospend disciplines to simulate highlighting
                        # but without breaking formatting
                        discipline_display = f"  {discipline}"
                        
                        output += table_base['format_entry'](discipline_display, current, next_rating, cost, status)
                        displayed_disciplines.add(discipline)
                    except Exception as e:
                        character.msg(f"Error calculating cost for {discipline}: {str(e)}")
        
        # 3. Other current disciplines (those not in autospend list and not clan disciplines)
        current_other = [d for d in current_disciplines.keys() 
                        if d not in autospend_disciplines and d not in displayed_disciplines]
                        
        if current_other:
            # Add empty row if previous sections had content
            if displayed_disciplines:
                output += table_base['format_empty_row']()
                
            # Section header using consistent format
            section_title = "Other Current Disciplines"
            section_title_str = f" {section_title} "
            colored_title = f"|y{section_title_str}|n"
            visible_width = len(section_title_str)
            total_dash_count = total_width - 4 - visible_width
            left_dashes = total_dash_count // 2
            right_dashes = total_dash_count - left_dashes
            output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
            
            for discipline in current_other:
                # Get current rating
                current = current_disciplines.get(discipline, {}).get('perm', 0)
                
                # Only show if below max rating
                if current < 5:
                    next_rating = current + 1
                    try:
                        cost, requires_approval = calculate_xp_cost(
                            character=character, 
                            is_staff_spend=False,
                            stat_name=discipline, 
                            category='powers',
                            subcategory='discipline',
                            current_rating=current,
                            new_rating=next_rating
                        )
                        # Force non-autospend status for disciplines not in the autospend list
                        if not requires_approval:
                            requires_approval = True  # Override to require approval
                        status = self._get_affordable_status(cost, current_xp, requires_approval)
                        output += table_base['format_entry'](discipline, current, next_rating, cost, status)
                        displayed_disciplines.add(discipline)
                    except Exception as e:
                        character.msg(f"Error calculating cost for {discipline}: {str(e)}")
        
        # 4. Purchasable disciplines section (autospend-eligible that aren't already displayed)
        purchasable = [d for d in autospend_disciplines if d not in displayed_disciplines]
        if purchasable:
            # Add empty row if previous sections had content
            if displayed_disciplines:
                output += table_base['format_empty_row']()
                
            # Section header using consistent format
            section_title = "Purchasable Disciplines"
            section_title_str = f" {section_title} "
            colored_title = f"|y{section_title_str}|n"
            visible_width = len(section_title_str)
            total_dash_count = total_width - 4 - visible_width
            left_dashes = total_dash_count // 2
            right_dashes = total_dash_count - left_dashes
            output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
            
            for discipline in purchasable:
                # Get current rating
                current = current_disciplines.get(discipline, {}).get('perm', 0)
                
                # Only show if below max rating
                if current < 5:
                    next_rating = current + 1
                    try:
                        cost, requires_approval = calculate_xp_cost(
                            character=character, 
                            is_staff_spend=False,
                            stat_name=discipline, 
                            category='powers',
                            subcategory='discipline',
                            current_rating=current,
                            new_rating=next_rating
                        )
                        status = self._get_affordable_status(cost, current_xp, requires_approval)
                        
                        # Add custom indentation for autospend disciplines to simulate highlighting
                        # but without breaking formatting
                        discipline_display = f"  {discipline}"
                        
                        output += table_base['format_entry'](discipline_display, current, next_rating, cost, status)
                        displayed_disciplines.add(discipline)
                    except Exception as e:
                        character.msg(f"Error calculating cost for {discipline}: {str(e)}")
        
        # Add a note about autospend-eligible disciplines
        output += table_base['format_empty_row']()
        note = "Note: Disciplines eligible for auto-spend are double-indented."
        note_visible_length = len(note)
        note_padding = total_width - 4 - note_visible_length
        output += f"| {note}{' ' * note_padding} |\n"
        
        # Add table footer
        output += table_base['format_border']()
        
        # Handle thaumaturgy and necromancy rituals separately
        rituals_output = ""
        if any(d.lower() == 'thaumaturgy' for d in current_disciplines.keys()):
            # Section header using consistent format
            section_title = "Thaumaturgy Rituals"
            section_title_str = f" {section_title} "
            colored_title = f"|y{section_title_str}|n"
            visible_width = len(section_title_str)
            total_dash_count = total_width - 4 - visible_width
            left_dashes = total_dash_count // 2
            right_dashes = total_dash_count - left_dashes
            rituals_output += f"\n| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
            rituals_output += "Use +costs/disciplines for details on available Thaumaturgy rituals.\n"
        
        if any(d.lower() == 'necromancy' for d in current_disciplines.keys()):
            # Section header using consistent format
            section_title = "Necromancy Rituals"
            section_title_str = f" {section_title} "
            colored_title = f"|y{section_title_str}|n"
            visible_width = len(section_title_str)
            total_dash_count = total_width - 4 - visible_width
            left_dashes = total_dash_count // 2
            right_dashes = total_dash_count - left_dashes
            rituals_output += f"\n| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
            rituals_output += "Use +costs/disciplines for details on available Necromancy rituals.\n"
        
        return output + rituals_output

    def _add_splat_specific_abilities(self, splat, shifter_type, clan, subcategories):
        """
        Add splat-specific abilities to the subcategories list.
        
        Args:
            splat (str): Character's splat type (vampire, mage, etc.)
            shifter_type (str): Character's shifter type (if applicable)
            clan (str): Character's clan (if applicable)
            subcategories (list): List of subcategory tuples to modify
        """
        # Dictionary to map subcategory indices
        subcategory_map = {
            'talent': 0,
            'skill': 1,
            'knowledge': 2
        }
        
        # Get additional character attributes - needs to be fetched from the character object
        # Since we don't have direct access to the character object here, let's use what we have
        char_type = shifter_type if splat.lower() == 'shifter' else ''
        if clan:
            char_type = clan
        
        # Initialize empty ability lists for different subcategories
        splat_talents = []
        splat_skills = []
        splat_knowledges = []
        
        # Get character's other attributes if available
        # For a complete implementation, you would need to add parameters to this method
        # to pass these attributes from the character object
        tradition = ''
        affiliation = ''
        fellowship = ''
        
        # Handle splat-specific abilities based on the provided code
        splat_lower = splat.lower()
        
        # Shifter abilities
        if splat_lower == 'shifter':
            splat_talents.append('Primal-Urge')
            splat_knowledges.append('Rituals')
            
            # Special shifter types with Flight
            if char_type and char_type.lower() in ['corax', 'camazotz', 'mokole']:
                splat_talents.append('Flight')
            
            # Additional shifter abilities from our previous implementation
            splat_talents.extend(['Purity'])
            splat_skills.append('Primal Utility')
            splat_knowledges.extend(['Linguistics', 'Umbral Lore', 'Spirit Lore'])
            
            # Werewolf-specific abilities
            if char_type and char_type.lower() == 'werewolf':
                splat_talents.append('Rage Edge')
                splat_knowledges.extend(['Garou Lore', 'Tribe Lore'])
        
        # Vampire abilities
        elif splat_lower == 'vampire':
            # Basic vampire abilities
            splat_talents.append('Kindred Lore')
            splat_skills.append('Feeding')
            splat_knowledges.extend(['Camarilla Lore', 'Sabbat Lore', 'Anarch Lore'])
            
            # Gargoyle vampires have Flight
            if char_type and char_type.lower() == 'gargoyle':
                splat_talents.append('Flight')
            
            # Clan-specific abilities
            if clan and clan.lower() == 'tremere':
                splat_knowledges.append('Thaumaturgy Lore')
        
        # Changeling abilities
        elif splat_lower == 'changeling':
            splat_talents.extend(['Kenning', 'Wayfare'])
            splat_skills.append('Crafts: Chimerical')
            splat_knowledges.extend(['Changeling Lore', 'Dream Lore', 'Fae Lore', 'Gremayre', 'Mythic Lore'])
        
        # Companion abilities (partially implemented - would need more character data)
        elif splat_lower == 'companion':
            # Companions with wings have Flight
            # In a full implementation, check character.get_stat('powers', 'special_advantage', 'Companion Wings')
            # splat_talents.append('Flight')
            
            # Technocracy companions get tech abilities
            if affiliation and affiliation.lower() == 'technocracy':
                splat_skills.extend(['Biotech', 'Energy Weapons', 'Helmsman', 'Microgravity Ops'])
                splat_knowledges.extend(['Cybernetics', 'Hypertech', 'Paraphysics', 'Xenobiology'])
        
        # Mage abilities
        elif splat_lower == 'mage':
            # Basic mage abilities
            splat_talents.extend(['Avatar', 'Lucid Dreaming'])
            splat_knowledges.extend(['Cosmology', 'Dimensional Science', 'Dream Lore', 'Enigmas', 
                                    'Etheric Engineering', 'Occult', 'Umbral Lore', 
                                    'Spirit Lore', 'Tradition Lore', 'Arcane'])
            
            # Add secondary talents for all mages
            splat_talents.extend(['Blatancy', 'Flying', 'High Ritual'])
            
            # Technocracy mages get tech abilities
            if affiliation and affiliation.lower() == 'technocracy':
                splat_skills.extend(['Biotech', 'Energy Weapons', 'Helmsman', 'Microgravity Ops'])
                splat_knowledges.extend(['Cybernetics', 'Hypertech', 'Paraphysics', 'Xenobiology'])
            
            # Akashic Brotherhood gets Do
            if tradition and tradition.lower() in ['akashayana', 'akashic brotherhood']:
                splat_talents.append('Do')
            
            # Nephandi get various abilities
            if affiliation and affiliation.lower() == 'nephandi':
                splat_talents.append('Do')
                splat_skills.extend(['Biotech', 'Energy Weapons', 'Helmsman', 'Microgravity Ops'])
                splat_knowledges.extend(['Cybernetics', 'Hypertech', 'Paraphysics', 'Xenobiology'])
            
            # Certain traditions get tech abilities
            if tradition and tradition.lower() in ['virtual adepts', 'sons of ether', 'society of ether', 'etherites']:
                splat_skills.extend(['Biotech', 'Energy Weapons', 'Helmsman', 'Microgravity Ops'])
                splat_knowledges.extend(['Cybernetics', 'Hypertech', 'Paraphysics', 'Xenobiology'])
        
        # Mortal+ abilities
        elif splat_lower == 'mortal+':
            # Basic mortal+ abilities
            splat_talents.extend(['True Faith', 'Medium'])
            splat_skills.append('Hunting')
            splat_knowledges.extend(['Occult', 'Supernatural Lore'])
            
            # Handle specific mortal+ types
            if char_type and char_type.lower() in ['sorcerer', 'psychic', 'faithful']:
                splat_talents.extend(['Flying', 'High Ritual'])
                
                # Special fellowship abilities
                tech_fellowships = ['sons of ether', 'virtual adepts', 'society of ether', 'etherites', 
                                   'new world order', 'iteration x', 'void engineers', 'syndicate', 'progenitors']
                if fellowship and fellowship.lower() in tech_fellowships:
                    splat_skills.extend(['Biotech', 'Energy Weapons', 'Helmsman', 'Microgravity Ops'])
                    splat_knowledges.extend(['Cybernetics', 'Hypertech', 'Paraphysics', 'Xenobiology'])
                
                if fellowship and fellowship.lower() in ['akashayana', 'akashic brotherhood']:
                    splat_talents.append('Do')
        
        # Possessed-specific abilities
        elif splat_lower == 'possessed':
            # Basic possessed abilities
            splat_talents.extend(['Corruption', 'Possession'])
            splat_skills.append('Torture')
            splat_knowledges.extend(['Demon Lore', 'Hell Lore'])
        
        # Now add the abilities to the appropriate subcategories
        if splat_talents:
            idx = subcategory_map.get('talent', 0)
            if idx < len(subcategories):
                subcategories[idx][1].extend(splat_talents)
                
        if splat_skills:
            idx = subcategory_map.get('skill', 1)
            if idx < len(subcategories):
                subcategories[idx][1].extend(splat_skills)
                
        if splat_knowledges:
            idx = subcategory_map.get('knowledge', 2)
            if idx < len(subcategories):
                subcategories[idx][1].extend(splat_knowledges)

        # Return the modified subcategories list
        return subcategories

    def _display_disciplines_costs_direct(self, character, current_xp, total_width=78):
        """Display discipline costs using direct string formatting"""
        # Check if character is a vampire
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        if splat.lower() != 'vampire':
            return "Only vampires can purchase disciplines."
        
        # Get base table formatting
        table_base = self._powers_table_base(character, current_xp, total_width)
        output = table_base['output']
        
        # Get character's disciplines
        current_disciplines = character.db.stats.get('powers', {}).get('discipline', {})
        
        # Add combo disciplines section header
        header_text = "Combo Disciplines and Rituals:"
        visible_length = len(header_text) + 4  # +4 for |c and |n color codes
        padding = total_width - visible_length
        output += f"| |c{header_text}|n{' ' * padding} |\n"
        output += table_base['format_empty_row']()
        
        # Get available combo disciplines from database
        # Import the model first
        from world.wod20th.models import Stat
        
        # Check if character has at least 2 disciplines
        if len(current_disciplines) >= 2:
            # Section header for combo disciplines
            section_title = "Combo Disciplines"
            section_title_str = f" {section_title} "
            colored_title = f"|y{section_title_str}|n"
            visible_width = len(section_title_str)
            total_dash_count = total_width - 4 - visible_width
            left_dashes = total_dash_count // 2
            right_dashes = total_dash_count - left_dashes
            output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
            
            # Query all vampire combo disciplines
            combo_disciplines = Stat.objects.filter(
                stat_type='combodiscipline',
                splat='Vampire'
            )
            
            # Check which combo disciplines the character qualifies for
            has_qualifying_combos = False
            for combo in combo_disciplines:
                # Check if character meets prerequisites
                if self._check_combo_prerequisites(character, combo.prerequisites):
                    has_qualifying_combos = True
                    # Display combo discipline entry
                    try:
                        # Calculate cost - this is typically 7 XP + highest prereq level
                        base_cost = 7
                        highest_prereq_level = self._get_highest_prereq_level(combo.prerequisites)
                        cost = combo.xp_cost if combo.xp_cost else (base_cost + highest_prereq_level)
                        
                        requires_approval = True  # Combo disciplines always require approval
                        status = self._get_affordable_status(cost, current_xp, requires_approval)
                        
                        # Truncate name if too long
                        combo_name = combo.name
                        if len(combo_name) > 21:
                            combo_name = combo_name[:18] + "..."
                            
                        output += table_base['format_entry'](combo_name, 'N/A', 'New', cost, status)
                    except Exception as e:
                        character.msg(f"Error calculating cost for {combo.name}: {str(e)}")
            
            # If no qualifying combos found, show a message
            if not has_qualifying_combos:
                note = "No combo disciplines available with your current discipline ratings."
                note_visible_length = len(note)
                note_padding = total_width - 4 - note_visible_length
                output += f"| {note}{' ' * note_padding} |\n"
            
            # Add note explaining combo disciplines
            output += table_base['format_empty_row']()
            note = "Note: Combo disciplines require at least 2 disciplines."
            note_visible_length = len(note)
            note_padding = total_width - 4 - note_visible_length
            output += f"| {note}{' ' * note_padding} |\n"
            
            note2 = "Cost is specific to the combo discipline power."
            note2_visible_length = len(note2)
            note2_padding = total_width - 4 - note2_visible_length
            output += f"| {note2}{' ' * note2_padding} |\n"
            
            note3 = "All combo disciplines require ST approval."
            note3_visible_length = len(note3)
            note3_padding = total_width - 4 - note3_visible_length
            output += f"| {note3}{' ' * note3_padding} |\n"
        else:
            # Display message that combo disciplines require at least 2 disciplines
            note = "You need at least 2 disciplines to learn combo disciplines."
            note_visible_length = len(note)
            note_padding = total_width - 4 - note_visible_length
            output += f"| {note}{' ' * note_padding} |\n"
        
        # Display Thaumaturgy and Necromancy rituals if applicable
        has_thaumaturgy = any(d.lower() == 'thaumaturgy' for d in current_disciplines.keys())
        has_necromancy = any(d.lower() == 'necromancy' for d in current_disciplines.keys())
        
        if has_thaumaturgy:
            # Empty row before rituals section
            output += table_base['format_empty_row']()
            
            # Section header for Thaumaturgy rituals
            section_title = "Thaumaturgy Rituals"
            section_title_str = f" {section_title} "
            colored_title = f"|y{section_title_str}|n"
            visible_width = len(section_title_str)
            total_dash_count = total_width - 4 - visible_width
            left_dashes = total_dash_count // 2
            right_dashes = total_dash_count - left_dashes
            output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
            
            # Get max ritual level based on Thaumaturgy rating
            thaumaturgy_level = current_disciplines.get('Thaumaturgy', {}).get('perm', 0)
            
            # Display costs for each ritual level
            for level in range(1, min(thaumaturgy_level + 1, 6)):
                ritual_name = f"Level {level} Ritual"
                try:
                    cost, requires_approval = calculate_xp_cost(
                        character,
                        False,  # is_staff_spend
                        ritual_name, 
                        category='powers',
                        subcategory='ritual',
                        ritual_type='thaumaturgy',
                        ritual_level=level
                    )
                    status = self._get_affordable_status(cost, current_xp, requires_approval)
                    output += table_base['format_entry'](ritual_name, 'N/A', 'New', cost, status)
                except Exception as e:
                    character.msg(f"Error calculating cost for {ritual_name}: {str(e)}")
        
        if has_necromancy:
            # Empty row before rituals section
            output += table_base['format_empty_row']()
            
            # Section header for Necromancy rituals
            section_title = "Necromancy Rituals"
            section_title_str = f" {section_title} "
            colored_title = f"|y{section_title_str}|n"
            visible_width = len(section_title_str)
            total_dash_count = total_width - 4 - visible_width
            left_dashes = total_dash_count // 2
            right_dashes = total_dash_count - left_dashes
            output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
            
            # Get max ritual level based on Necromancy rating
            necromancy_level = current_disciplines.get('Necromancy', {}).get('perm', 0)
            
            # Display costs for each ritual level
            for level in range(1, min(necromancy_level + 1, 6)):
                ritual_name = f"Level {level} Ritual"
                try:
                    cost, requires_approval = calculate_xp_cost(
                        character,
                        False,  # is_staff_spend
                        ritual_name, 
                        category='powers',
                        subcategory='ritual',
                        ritual_type='necromancy',
                        ritual_level=level
                    )
                    status = self._get_affordable_status(cost, current_xp, requires_approval)
                    output += table_base['format_entry'](ritual_name, 'N/A', 'New', cost, status)
                except Exception as e:
                    character.msg(f"Error calculating cost for {ritual_name}: {str(e)}")
        
        # Add table footer
        output += table_base['format_border']()
        
        # Add note about viewing regular disciplines
        output += "\n|cNote:|n To view costs for regular disciplines, use |g+costs/powers|n instead."
        
        return output
        
    def _check_combo_prerequisites(self, character, prerequisites):
        """
        Check if the character meets the prerequisites for a combo discipline.
        
        Args:
            character: The character to check
            prerequisites: String containing prerequisite disciplines and levels
            
        Returns:
            bool: True if the character meets all prerequisites, False otherwise
        """
        # If prerequisites is empty, return False (can't have combo without prereqs)
        if not prerequisites:
            return False
            
        # Get character's current disciplines
        current_disciplines = character.db.stats.get('powers', {}).get('discipline', {})
        
        # The prerequisites might be stored as a string representation of a list
        # We need to convert it to an actual list
        if isinstance(prerequisites, str):
            # Remove brackets and split by commas if it's a string representation of a list
            if prerequisites.startswith('[') and prerequisites.endswith(']'):
                prereq_list = prerequisites[1:-1].replace("'", "").replace('"', '').split(',')
                prereq_list = [p.strip() for p in prereq_list]
            else:
                # If it's just a single prereq as a string
                prereq_list = [prerequisites]
        elif isinstance(prerequisites, list):
            # It's already a list
            prereq_list = prerequisites
        else:
            # Unknown format
            return False
            
        # Check each prerequisite
        for prereq in prereq_list:
            # Expected format: "Discipline X" where X is the required level
            parts = prereq.strip().split()
            if len(parts) < 2:
                continue  # Invalid format
                
            # Get discipline name and required level
            discipline_name = ' '.join(parts[:-1])  # Handle multi-word disciplines like "Mask of a Thousand Faces"
            try:
                required_level = int(parts[-1])
            except ValueError:
                continue  # Invalid level format
                
            # Check if character has the discipline at the required level
            character_level = current_disciplines.get(discipline_name, {}).get('perm', 0)
            if character_level < required_level:
                return False  # Character doesn't meet this prerequisite
                
        # If we get here, character meets all prerequisites
        return True
        
    def _get_highest_prereq_level(self, prerequisites):
        """
        Get the highest prerequisite level from a list of prerequisites.
        
        Args:
            prerequisites: String containing prerequisite disciplines and levels
            
        Returns:
            int: The highest prerequisite level
        """
        # Default if we can't determine
        default_level = 3
        
        # If prerequisites is empty, return default
        if not prerequisites:
            return default_level
            
        # Convert prerequisites to list if it's a string
        if isinstance(prerequisites, str):
            # Remove brackets and split by commas if it's a string representation of a list
            if prerequisites.startswith('[') and prerequisites.endswith(']'):
                prereq_list = prerequisites[1:-1].replace("'", "").replace('"', '').split(',')
                prereq_list = [p.strip() for p in prereq_list]
            else:
                # If it's just a single prereq as a string
                prereq_list = [prerequisites]
        elif isinstance(prerequisites, list):
            # It's already a list
            prereq_list = prerequisites
        else:
            # Unknown format
            return default_level
            
        # Find highest level
        highest_level = 0
        for prereq in prereq_list:
            # Expected format: "Discipline X" where X is the required level
            parts = prereq.strip().split()
            if len(parts) < 2:
                continue  # Invalid format
                
            try:
                level = int(parts[-1])
                highest_level = max(highest_level, level)
            except ValueError:
                continue  # Invalid level format
                
        # Return highest level found, or default if none found
        return highest_level if highest_level > 0 else default_level

    def _display_all_costs(self, character):
        """Display an overview of all cost categories"""
        total_width = 78
        current_xp = character.db.xp.get('current', 0) if character.db.xp else 0
        
        # Create header
        header = f"|b{'-' * total_width}|n\n"
        header += f"|b{' ' * 30}Character Advancement Costs{' ' * 30}|n\n"
        header += f"|b{'-' * total_width}|n\n"
        
        # Create footer
        footer = f"|b{'-' * total_width}|n"
        
        # Build the overview
        output = ""
        
        # Add current XP information
        output += f"|gCurrent XP: {current_xp}|n\n\n"
        
        # List all available categories
        output += "|cAvailable Cost Categories:|n\n"
        output += " |g+costs/attributes|n         - View attribute costs\n"
        output += " |g+costs/abilities|n          - View ability costs\n"
        output += " |g+costs/secondary_abilities|n - View secondary ability costs\n"
        output += " |g+costs/backgrounds|n        - View background costs\n"
        
        # Add splat-specific categories
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower()
        
        if splat == 'vampire':
            output += " |g+costs/disciplines|n        - View combo disciplines and ritual costs\n"
        
        # Add powers category for all splats
        output += " |g+costs/powers|n             - View power costs specific to your character type\n"
        
        # Add pools category for all characters
        output += " |g+costs/pools|n              - View costs for Willpower and other pools\n\n"
        
        # Add some general information
        output += "|cCommon XP Costs:|n\n"
        output += " • Attributes: 4 XP * current rating\n"
        output += " • Abilities: 3xp 0 -> 1, 2 XP * current rating\n"
        output += " • Secondary Abilities: 3xp 0 -> 1, 2 XP * current rating\n"
        output += " • Backgrounds: 5 XP per dot\n"
        output += " • Willpower: 2 XP * current rating\n"
        output += " • Merit: 5xp * rating\n"
        output += " • Flaw: 5xp * rating to buy off the Flaw\n"
        
        # Add splat-specific common costs
        if splat == 'vampire':
            output += " • Disciplines: 7 XP * new rating (5 XP * current rating for clan disciplines)\n"
            output += " • Rituals: 2 XP * level for Thaumaturgy/Necromancy rituals\n"
            output += " • Combo Disciplines: As per cost listed\n"
        elif splat == 'mage':
            output += " • Spheres: 8 XP * current rating (7 XP * current rating for affinity sphere)\n"
            output += " • Arete: 8 XP * current rating\n"
        elif splat == 'shifter':
            output += " • Gifts: 5 XP * rating (3xp * rating for in-auspice/breed/tribe)\n"
            output += " • Rage: 1 XP * current rating\n"
            output += " • Gnosis: 2 XP * current rating\n"
        elif splat == 'changeling':
            output += " • Arts: 7 XP 0->1, then 4xp * current rating\n"
            output += " • Realms: 5 XP 0->1, then 3xp * current rating\n"
            output += " • Glamour: 2 XP * current rating\n"
        elif splat == 'possessed':
            output += " • Blessings: 4xp * rating\n"
        
        # Add note about staff approval
        output += "\n|rNote: Some purchases may require Staff approval.|n\n"
        output += "|cSee individual categories for detailed costs, current ratings, and approval requirements.|n"
        output += "\n|cMerits and Flaws are not listed here, as they are fairly numerous and would make the command too long to display.|n"
        
        # Send the full display to the character
        character.msg(f"{header}{output}\n{footer}")

    def _display_mortalplus_powers_direct(self, character, current_xp, total_width=78):
        """Display powers for Mortal+ characters based on their specific type"""
        # Check if character is a Mortal+
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        if splat.lower() != 'mortal+':
            return "This command is only for Mortal+ characters."
        
        # Get character's specific mortal+ type
        mortalplus_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
        if not mortalplus_type:
            return "Character doesn't have a specified Mortal+ type."
        
        # Get base table formatting
        table_base = self._powers_table_base(character, current_xp, total_width)
        output = table_base['output']
        
        # Add header based on mortalplus type
        header_text = f"{mortalplus_type} Powers:"
        visible_length = len(header_text) + 4  # +4 for |c and |n color codes
        padding = total_width - visible_length
        output += f"| |c{header_text}|n{' ' * padding} |\n"
        output += table_base['format_empty_row']()
        
        # Process different powers based on mortalplus type
        if mortalplus_type.lower() == 'ghoul':
            # Ghouls can have vampire disciplines
            output = self._display_ghoul_powers(character, current_xp, total_width, table_base, output)
        elif mortalplus_type.lower() == 'kinfolk':
            # Kinfolk can have certain gifts
            output = self._display_kinfolk_powers(character, current_xp, total_width, table_base, output)
        elif mortalplus_type.lower() in ['sorcerer', 'psychic', 'faithful']:
            # These types can have sorcery, numina, and faith
            output = self._display_occult_mortal_powers(character, current_xp, total_width, table_base, output, mortalplus_type)
        elif mortalplus_type.lower() == 'kinain':
            # Kinain can have arts and realms
            output = self._display_kinain_powers(character, current_xp, total_width, table_base, output)
        else:
            # Generic message for unknown mortalplus types
            note = f"No specific powers available for {mortalplus_type} type."
            note_visible_length = len(note)
            note_padding = total_width - 4 - note_visible_length
            output += f"| {note}{' ' * note_padding} |\n"
        
        # Add table footer
        output += table_base['format_border']()
        
        return output

    def _display_ghoul_powers(self, character, current_xp, total_width, table_base, output):
        """Display ghoul-specific powers (disciplines)"""
        # Get current disciplines
        current_disciplines = character.db.stats.get('powers', {}).get('discipline', {})
        
        # Get the character's domitor clan
        domitor_clan = character.db.stats.get('identity', {}).get('lineage', {}).get('Clan', {}).get('perm', '')
        
        # Import clan disciplines mapping
        from world.wod20th.utils.vampire_utils import CLAN_DISCIPLINES
        
        # Define disciplines that can be purchased by ghouls
        if domitor_clan and domitor_clan in CLAN_DISCIPLINES:
            # Ghouls can only learn their domitor's clan disciplines
            ghoul_disciplines = CLAN_DISCIPLINES[domitor_clan]
        else:
            # If no domitor clan specified, show common physical disciplines
            ghoul_disciplines = ['Potence', 'Celerity', 'Fortitude']
        
        # Track displayed disciplines to avoid duplicates
        displayed_disciplines = set()
        
        # Current disciplines section (any disciplines the ghoul already has)
        current_list = sorted(current_disciplines.keys())
        if current_list:
            # Section header
            section_title = "Current Disciplines"
            section_title_str = f" {section_title} "
            colored_title = f"|y{section_title_str}|n"
            visible_width = len(section_title_str)
            total_dash_count = total_width - 4 - visible_width
            left_dashes = total_dash_count // 2
            right_dashes = total_dash_count - left_dashes
            output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
            
            for discipline in current_list:
                # Get current rating
                current = current_disciplines.get(discipline, {}).get('perm', 0)
                
                # Ghouls are limited to discipline rating 1
                if current < 1:
                    next_rating = current + 1
                    try:
                        # Calculate discipline cost for ghouls
                        cost = 20  # Fixed cost for ghouls to learn disciplines
                        
                        # Always require approval for additional dots
                        requires_approval = (current > 0)
                        status = self._get_affordable_status(cost, current_xp, requires_approval)
                        output += table_base['format_entry'](discipline, current, next_rating, cost, status)
                        displayed_disciplines.add(discipline)
                    except Exception as e:
                        character.msg(f"Error calculating cost for {discipline}: {str(e)}")
        
        # Available disciplines section (clan disciplines ghouls can purchase)
        available_list = [d for d in ghoul_disciplines if d not in displayed_disciplines]
        if available_list:
            # Add empty row if previous section had content
            if displayed_disciplines:
                output += table_base['format_empty_row']()
                
            # Section header
            section_title = "Available Disciplines"
            section_title_str = f" {section_title} "
            colored_title = f"|y{section_title_str}|n"
            visible_width = len(section_title_str)
            total_dash_count = total_width - 4 - visible_width
            left_dashes = total_dash_count // 2
            right_dashes = total_dash_count - left_dashes
            output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
            
            for discipline in sorted(available_list):
                try:
                    # First level of new discipline costs 20 XP for ghouls
                    cost = 20
                    requires_approval = False  # First dot doesn't require approval
                    status = self._get_affordable_status(cost, current_xp, requires_approval)
                    output += table_base['format_entry'](discipline, 0, 1, cost, status)
                except Exception as e:
                    character.msg(f"Error calculating cost for {discipline}: {str(e)}")
        
        # Add note about ghoul discipline limitations
        output += table_base['format_empty_row']()
        note = "Note: Ghouls are limited to a maximum of 1 dot in clan disciplines."
        note_visible_length = len(note)
        note_padding = total_width - 4 - note_visible_length
        output += f"| {note}{' ' * note_padding} |\n"
        
        if domitor_clan:
            clan_note = f"Your domitor's clan ({domitor_clan}) determines available disciplines."
            clan_note_visible_length = len(clan_note)
            clan_note_padding = total_width - 4 - clan_note_visible_length
            output += f"| {clan_note}{' ' * clan_note_padding} |\n"
        
        return output
    
    def _display_kinfolk_powers(self, character, current_xp, total_width, table_base, output):
        """Display kinfolk-specific powers (gifts)"""
        # Get current gifts
        current_gifts = character.db.stats.get('powers', {}).get('gift', {})
        
        # Get character's breed/tribe if available
        breed = character.db.stats.get('identity', {}).get('lineage', {}).get('Breed', {}).get('perm', '')
        tribe = character.db.stats.get('identity', {}).get('lineage', {}).get('Tribe', {}).get('perm', '')
        
        # Current gifts section
        if current_gifts:
            # Section header
            section_title = "Current Gifts"
            section_title_str = f" {section_title} "
            colored_title = f"|y{section_title_str}|n"
            visible_width = len(section_title_str)
            total_dash_count = total_width - 4 - visible_width
            left_dashes = total_dash_count // 2
            right_dashes = total_dash_count - left_dashes
            output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
            
            for gift_name, gift_data in sorted(current_gifts.items()):
                # Get current level
                current = gift_data.get('perm', 0)
                if current < 5:  # Maximum level 5
                    next_level = current + 1
                    try:
                        # Determine if gift is in-breed/tribe or special
                        is_breed_tribe = self._is_breed_tribe_gift(gift_name, breed, tribe)
                        is_special = self._is_special_gift(gift_name)
                        
                        if is_special:
                            cost = next_level * 14  # Special gifts cost more
                        elif is_breed_tribe:
                            cost = next_level * 6   # In-breed/tribe gifts cost less
                        else:
                            cost = next_level * 10  # Out-of-breed/tribe gifts
                            
                        requires_approval = True    # Gifts typically require approval
                        status = self._get_affordable_status(cost, current_xp, requires_approval)
                        output += table_base['format_entry'](gift_name, current, next_level, cost, status)
                    except Exception as e:
                        character.msg(f"Error calculating cost for {gift_name}: {str(e)}")
        
        # Add note about kinfolk gift limitations
        output += table_base['format_empty_row']()
        note = "Note: New gifts require Staff approval. Costs vary by gift type."
        note_visible_length = len(note)
        note_padding = total_width - 4 - note_visible_length
        output += f"| {note}{' ' * note_padding} |\n"
        
        if breed or tribe:
            note2 = f"In-breed/tribe gifts (6 XP × level): {breed} {tribe}"
            note2_visible_length = len(note2)
            note2_padding = total_width - 4 - note2_visible_length
            output += f"| {note2}{' ' * note2_padding} |\n"
        
        return output
    
    def _display_occult_mortal_powers(self, character, current_xp, total_width, table_base, output, mortalplus_type):
        """Display powers for sorcerers, psychics, and the faithful"""
        # Initialize section flags
        has_sorcery = False
        has_numina = False
        has_faith = False
        has_hedge_rituals = False
        
        # Get current powers
        current_sorcery = character.db.stats.get('powers', {}).get('sorcery', {})
        current_numina = character.db.stats.get('powers', {}).get('numina', {})
        current_faith = character.db.stats.get('powers', {}).get('faith', {})
        current_hedge_rituals = character.db.stats.get('powers', {}).get('hedge_ritual', {})
        
        # Flag which power types this character has
        if current_sorcery:
            has_sorcery = True
        if current_numina:
            has_numina = True
        if current_faith:
            has_faith = True
        if current_hedge_rituals:
            has_hedge_rituals = True
            
        # Also enable specific power types based on mortalplus type
        if mortalplus_type.lower() == 'sorcerer':
            has_sorcery = True
            has_hedge_rituals = True
        elif mortalplus_type.lower() == 'psychic':
            has_numina = True
        elif mortalplus_type.lower() == 'faithful':
            has_faith = True
        
        # Display sorcery paths
        if has_sorcery:
            # Section header for sorcery
            section_title = "Sorcery Paths"
            section_title_str = f" {section_title} "
            colored_title = f"|y{section_title_str}|n"
            visible_width = len(section_title_str)
            total_dash_count = total_width - 4 - visible_width
            left_dashes = total_dash_count // 2
            right_dashes = total_dash_count - left_dashes
            output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
            
            # Show current sorcery paths
            if current_sorcery:
                for path_name, path_data in sorted(current_sorcery.items()):
                    current = path_data.get('perm', 0)
                    if current < 5:  # Maximum level 5
                        next_level = current + 1
                        try:
                            # Sorcery paths cost 7 XP × new rating
                            cost = next_level * 7
                            requires_approval = True  # Paths typically require approval
                            status = self._get_affordable_status(cost, current_xp, requires_approval)
                            output += table_base['format_entry'](path_name, current, next_level, cost, status)
                        except Exception as e:
                            character.msg(f"Error calculating cost for {path_name}: {str(e)}")
            else:
                # Message if no current sorcery paths
                note = "No current sorcery paths. New paths require Staff approval."
                note_visible_length = len(note)
                note_padding = total_width - 4 - note_visible_length
                output += f"| {note}{' ' * note_padding} |\n"
        
        # Display numina
        if has_numina:
            # Add empty row if previous section had content
            if has_sorcery:
                output += table_base['format_empty_row']()
                
            # Section header for numina
            section_title = "Numina"
            section_title_str = f" {section_title} "
            colored_title = f"|y{section_title_str}|n"
            visible_width = len(section_title_str)
            total_dash_count = total_width - 4 - visible_width
            left_dashes = total_dash_count // 2
            right_dashes = total_dash_count - left_dashes
            output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
            
            # Show current numina
            if current_numina:
                for numina_name, numina_data in sorted(current_numina.items()):
                    current = numina_data.get('perm', 0)
                    if current < 5:  # Maximum level 5
                        next_level = current + 1
                        try:
                            # Numina cost 7 XP × new rating
                            cost = next_level * 7
                            requires_approval = True  # Numina typically require approval
                            status = self._get_affordable_status(cost, current_xp, requires_approval)
                            output += table_base['format_entry'](numina_name, current, next_level, cost, status)
                        except Exception as e:
                            character.msg(f"Error calculating cost for {numina_name}: {str(e)}")
            else:
                # Message if no current numina
                note = "No current numina. New numina require Staff approval."
                note_visible_length = len(note)
                note_padding = total_width - 4 - note_visible_length
                output += f"| {note}{' ' * note_padding} |\n"
        
        # Display faith powers
        if has_faith:
            # Add empty row if previous section had content
            if has_sorcery or has_numina:
                output += table_base['format_empty_row']()
                
            # Section header for faith
            section_title = "Faith Powers"
            section_title_str = f" {section_title} "
            colored_title = f"|y{section_title_str}|n"
            visible_width = len(section_title_str)
            total_dash_count = total_width - 4 - visible_width
            left_dashes = total_dash_count // 2
            right_dashes = total_dash_count - left_dashes
            output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
            
            # Show current faith powers
            if current_faith:
                for faith_name, faith_data in sorted(current_faith.items()):
                    current = faith_data.get('perm', 0)
                    if current < 5:  # Maximum level 5
                        next_level = current + 1
                        try:
                            # Faith powers cost 7 XP × new rating
                            cost = next_level * 7
                            requires_approval = True  # Faith powers typically require approval
                            status = self._get_affordable_status(cost, current_xp, requires_approval)
                            output += table_base['format_entry'](faith_name, current, next_level, cost, status)
                        except Exception as e:
                            character.msg(f"Error calculating cost for {faith_name}: {str(e)}")
            else:
                # Message if no current faith powers
                note = "No current faith powers. New faith powers require Staff approval."
                note_visible_length = len(note)
                note_padding = total_width - 4 - note_visible_length
                output += f"| {note}{' ' * note_padding} |\n"
        
        # Display hedge rituals
        if has_hedge_rituals:
            # Add empty row if previous section had content
            if has_sorcery or has_numina or has_faith:
                output += table_base['format_empty_row']()
                
            # Section header for hedge rituals
            section_title = "Hedge Rituals"
            section_title_str = f" {section_title} "
            colored_title = f"|y{section_title_str}|n"
            visible_width = len(section_title_str)
            total_dash_count = total_width - 4 - visible_width
            left_dashes = total_dash_count // 2
            right_dashes = total_dash_count - left_dashes
            output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
            
            # For rituals, show costs by level
            for level in range(1, 6):  # Levels 1-5
                ritual_name = f"Level {level} Ritual"
                try:
                    # Hedge rituals cost their level in XP
                    cost = level
                    requires_approval = True  # Rituals typically require approval
                    status = self._get_affordable_status(cost, current_xp, requires_approval)
                    output += table_base['format_entry'](ritual_name, 'N/A', 'New', cost, status)
                except Exception as e:
                    character.msg(f"Error calculating cost for {ritual_name}: {str(e)}")
        
        return output
    
    def _display_kinain_powers(self, character, current_xp, total_width, table_base, output):
        """Display kinain-specific powers (arts and realms)"""
        # Get current arts and realms
        current_arts = character.db.stats.get('powers', {}).get('art', {})
        current_realms = character.db.stats.get('powers', {}).get('realm', {})
        
        # Display arts
        # Section header for arts
        section_title = "Arts"
        section_title_str = f" {section_title} "
        colored_title = f"|y{section_title_str}|n"
        visible_width = len(section_title_str)
        total_dash_count = total_width - 4 - visible_width
        left_dashes = total_dash_count // 2
        right_dashes = total_dash_count - left_dashes
        output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
        
        # Show current arts
        if current_arts:
            for art_name, art_data in sorted(current_arts.items()):
                current = art_data.get('perm', 0)
                if current < 3:  # Kinain are typically limited to 3 dots
                    next_level = current + 1
                    try:
                        # Arts cost 7 XP for first dot, then 4 XP × current rating
                        if current == 0:
                            cost = 7  # First dot costs 7 XP
                        else:
                            cost = current * 4  # Subsequent dots cost current × 4
                            
                        requires_approval = True  # Arts typically require approval
                        status = self._get_affordable_status(cost, current_xp, requires_approval)
                        output += table_base['format_entry'](art_name, current, next_level, cost, status)
                    except Exception as e:
                        character.msg(f"Error calculating cost for {art_name}: {str(e)}")
        else:
            # Message if no current arts
            note = "No current arts. New arts require Staff approval."
            note_visible_length = len(note)
            note_padding = total_width - 4 - note_visible_length
            output += f"| {note}{' ' * note_padding} |\n"
        
        # Display realms
        output += table_base['format_empty_row']()
        
        # Section header for realms
        section_title = "Realms"
        section_title_str = f" {section_title} "
        colored_title = f"|y{section_title_str}|n"
        visible_width = len(section_title_str)
        total_dash_count = total_width - 4 - visible_width
        left_dashes = total_dash_count // 2
        right_dashes = total_dash_count - left_dashes
        output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
        
        # Show current realms
        if current_realms:
            for realm_name, realm_data in sorted(current_realms.items()):
                current = realm_data.get('perm', 0)
                if current < 3:  # Kinain are typically limited to 3 dots
                    next_level = current + 1
                    try:
                        # Realms cost 5 XP for first dot, then 3 XP × current rating
                        if current == 0:
                            cost = 5  # First dot costs 5 XP
                        else:
                            cost = current * 3  # Subsequent dots cost current × 3
                            
                        requires_approval = True  # Realms typically require approval
                        status = self._get_affordable_status(cost, current_xp, requires_approval)
                        output += table_base['format_entry'](realm_name, current, next_level, cost, status)
                    except Exception as e:
                        character.msg(f"Error calculating cost for {realm_name}: {str(e)}")
        else:
            # Message if no current realms
            note = "No current realms. New realms require Staff approval."
            note_visible_length = len(note)
            note_padding = total_width - 4 - note_visible_length
            output += f"| {note}{' ' * note_padding} |\n"
        
        # Add note about kinain limitations
        output += table_base['format_empty_row']()
        note = "Note: Kinain are typically limited to a maximum of 3 dots in Arts and Realms."
        note_visible_length = len(note)
        note_padding = total_width - 4 - note_visible_length
        output += f"| {note}{' ' * note_padding} |\n"
        
        return output
    
    def _is_breed_tribe_gift(self, gift_name, breed, tribe):
        """Check if a gift belongs to the character's breed or tribe"""
        # This is a simplified check - in a full implementation,
        # you would check against an actual database of breed/tribe gifts
        
        # For now, just check if the gift name contains the breed or tribe
        if not breed and not tribe:
            return False
            
        gift_lower = gift_name.lower()
        if breed and breed.lower() in gift_lower:
            return True
        if tribe and tribe.lower() in gift_lower:
            return True
            
        return False
    
    def _is_special_gift(self, gift_name):
        """Check if a gift is of a special type with higher cost"""
        # This is a simplified check - in a full implementation,
        # you would check against an actual database of special gifts
        
        # Special types are determined by specific tribes, not by gift name
        # This stub method remains for backward compatibility but shouldn't match anything
        return False
        
    def _is_special_gift_stat(self, gift_stat):
        """
        Check if a gift is of a special type with higher cost.
        This version takes a full gift Stat object from the database.
        """
        if not gift_stat:
            return False
            
        # Special gifts are only those with explicit tribe values of "Croatan", "Planetary", or "Ju-Fu"
        special_tribes = ['croatan', 'planetary', 'ju-fu']
        
        # Check tribe attribute
        if hasattr(gift_stat, 'tribe') and gift_stat.tribe:
            tribes = self._ensure_list(gift_stat.tribe)
            
            # Check for exact tribe matches only, not partial text matches
            for tribe in tribes:
                tribe_lower = tribe.lower().strip()
                if tribe_lower in special_tribes:
                    return True
                    
        return False

    def _display_shifter_powers_direct(self, character, current_xp, total_width=78):
        """Display powers for Shifter characters"""
        # Check if character is a Shifter
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        if splat.lower() != 'shifter':
            return "This command is only for Shifter characters."
        
        # Get base table formatting
        table_base = self._powers_table_base(character, current_xp, total_width)
        output = table_base['output']
        
        # Get character's specifics
        shifter_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Shifter Type', {}).get('perm', '')
        breed = character.db.stats.get('identity', {}).get('lineage', {}).get('Breed', {}).get('perm', '')
        tribe = character.db.stats.get('identity', {}).get('lineage', {}).get('Tribe', {}).get('perm', '')
        auspice = character.db.stats.get('identity', {}).get('lineage', {}).get('Auspice', {}).get('perm', '')
        aspect = character.db.stats.get('identity', {}).get('lineage', {}).get('Aspect', {}).get('perm', '')
        faction = character.db.stats.get('identity', {}).get('lineage', {}).get('Faction', {}).get('perm', '')
        path = character.db.stats.get('identity', {}).get('lineage', {}).get('Path', {}).get('perm', '')
        
        # For Garou characters, Type field is usually "Garou"
        if shifter_type == '':
            garou_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
            if garou_type and garou_type.lower() == 'garou':
                shifter_type = 'Garou'
        
        # Import the shifter mappings to handle different shifter types
        from world.wod20th.utils.xp_utils import SHIFTER_MAPPINGS
        
        # Handle attribute mappings based on shifter type
        shifter_info = SHIFTER_MAPPINGS.get(shifter_type, {})
        
        # Determine effective breed, auspice and tribe for calculations
        effective_breed = breed
        effective_auspice = auspice
        effective_tribe = tribe
        
        # Apply mappings based on shifter type
        if shifter_type:
            # Handle breed mappings
            breed_mappings = shifter_info.get('breed_mappings', {})
            if breed in breed_mappings:
                effective_breed = breed_mappings[breed]
            
            # For Ajaba, Ratkin - use Aspect as Auspice
            if aspect and shifter_info.get('aspects_to_auspices', {}).get(aspect, False):
                effective_auspice = aspect
            
            # For Ananasi - use Aspect as Tribe and Faction as Auspice
            if shifter_type == 'Ananasi':
                if aspect and shifter_info.get('aspects_to_tribes', {}).get(aspect, False):
                    effective_tribe = aspect
                if faction and shifter_info.get('factions_to_auspices', {}).get(faction, False):
                    effective_auspice = faction
            
            # For Kitsune - use Path as Auspice
            if shifter_type == 'Kitsune' and path and shifter_info.get('paths_to_auspices', {}).get(path, False):
                effective_auspice = path
            
            # For Mokole - handle auspice mappings
            if shifter_type == 'Mokole' and auspice and shifter_info.get('auspice_mappings', {}).get(auspice, False):
                effective_auspice = shifter_info['auspice_mappings'][auspice]
            
            # Special case for shifters that treat all gifts as in-tribe
            if shifter_info.get('all_gifts_in_tribe', False):
                effective_tribe = shifter_type  # Use the shifter type itself as the "tribe"
            
            # For Bastet - verify their tribe is valid
            if shifter_type == 'Bastet' and tribe:
                if not shifter_info.get('tribes', {}).get(tribe, False):
                    effective_tribe = ''  # Tribe not recognized for Bastet
        
        # Add header
        type_display = shifter_type if shifter_type else "Shifter"
        header_text = f"{type_display} Powers:"
        visible_length = len(header_text) + 4  # +4 for |c and |n color codes
        padding = total_width - visible_length
        output += f"| |c{header_text}|n{' ' * padding} |\n"
        output += table_base['format_empty_row']()
        
        # Get current gifts
        current_gifts = character.db.stats.get('powers', {}).get('gift', {})
        
        # Create custom headers for gift display
        current_gifts_header = f"| {'Gift Name':<45}{'Level':<30} |\n"
        available_gifts_header = f"| {'Gift Name':<45}{'Cost':<10}{'Autospend?':<20} |\n"
        
        # Display gifts section
        # Section header
        section_title = "Current Gifts"
        section_title_str = f" {section_title} "
        colored_title = f"|y{section_title_str}|n"
        visible_width = len(section_title_str)
        total_dash_count = total_width - 4 - visible_width
        left_dashes = total_dash_count // 2
        right_dashes = total_dash_count - left_dashes
        output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
        
        # Show current gifts
        if current_gifts:
            for gift_name, gift_data in sorted(current_gifts.items()):
                # Get current level
                current = gift_data.get('perm', 0)
                
                # Format the gift entry for display - just show name and level
                # Truncate name if too long
                display_name = gift_name
                if len(display_name) > 42:
                    display_name = display_name[:25] + "..."
                
                # Format the display with exact spacing
                formatted_name = display_name.ljust(25)
                formatted_level = str(current).ljust(49)
                
                # Add the entry
                output += f"| {formatted_name}{formatted_level} |\n"
        else:
            # Message if no current gifts
            note = "No current Gifts."
            note_visible_length = len(note)
            note_padding = total_width - 4 - note_visible_length
            output += f"| {note}{' ' * note_padding} |\n"
        
        # Query database for available gifts for this character
        try:
            # Import models
            from world.wod20th.models import Stat
            from django.db.models import Q
            
            # Section header for available gifts
            output += table_base['format_empty_row']()
            section_title = "Available Gifts"
            section_title_str = f" {section_title} "
            colored_title = f"|y{section_title_str}|n"
            visible_width = len(section_title_str)
            total_dash_count = total_width - 4 - visible_width
            left_dashes = total_dash_count // 2
            right_dashes = total_dash_count - left_dashes
            output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
            
            # Get all gifts - then filter for level 1 manually to handle database backend limitations
            all_gifts = Stat.objects.filter(
                category='powers',
                stat_type='gift'
            )
            
            # Log some debug info
            character.msg(f"DEBUG: Shifter Type: {shifter_type}, Breed: {breed}, Tribe: {tribe}, Auspice: {auspice}, Aspect: {aspect}")
            character.msg(f"DEBUG: Effective Breed: {effective_breed}, Effective Tribe: {effective_tribe}, Effective Auspice: {effective_auspice}")
            
            # Filter gifts for this character manually
            available_gifts = []
            for gift in all_gifts:
                # Check if it's a level 1 gift
                has_level_1 = False
                if hasattr(gift, 'values'):
                    if isinstance(gift.values, (list, tuple)):
                        has_level_1 = 1 in gift.values
                    elif isinstance(gift.values, str) and '[' in gift.values:
                        # Handle JSON string representation
                        try:
                            import json
                            values_list = json.loads(gift.values.replace("'", '"'))
                            has_level_1 = 1 in values_list
                        except:
                            # If can't parse, try a simple check
                            has_level_1 = '1' in gift.values
                    else:
                        # Handle single value
                        try:
                            has_level_1 = int(gift.values) == 1
                        except:
                            has_level_1 = False
                
                # Skip if not a level 1 gift
                if not has_level_1:
                    continue
                
                # Skip if already known
                if gift.name in current_gifts:
                    continue
                
                # 1. Check if gift is available to this character type
                gift_match = False
                
                # Check shifter type compatibility
                if hasattr(gift, 'shifter_type') and gift.shifter_type:
                    allowed_types = self._ensure_list(gift.shifter_type)
                    if not any(shifter_type.lower() in t.lower() for t in allowed_types):
                        continue  # Skip if shifter type doesn't match
                
                # 2. Check breed match
                if hasattr(gift, 'breed') and gift.breed:
                    allowed_breeds = self._ensure_list(gift.breed)
                    if effective_breed and any(effective_breed.lower() in b.lower() for b in allowed_breeds):
                        gift_match = True
                        gift.match_type = 'breed'  # Mark the match type for display
                
                # 3. Check auspice/aspect match
                if hasattr(gift, 'auspice') and gift.auspice:
                    allowed_auspices = self._ensure_list(gift.auspice)
                    if effective_auspice and any(effective_auspice.lower() in a.lower() for a in allowed_auspices):
                        gift_match = True
                        gift.match_type = 'auspice'  # Mark the match type for display
                
                # 4. Check tribe/aspect match
                if hasattr(gift, 'tribe') and gift.tribe:
                    allowed_tribes = self._ensure_list(gift.tribe)
                    if effective_tribe and any(effective_tribe.lower() in t.lower() for t in allowed_tribes):
                        gift_match = True
                        gift.match_type = 'tribe'  # Mark the match type for display
                
                # 5. If it's a general gift without specific breed/auspice/tribe requirements
                if (not hasattr(gift, 'breed') or not gift.breed) and \
                   (not hasattr(gift, 'auspice') or not gift.auspice) and \
                   (not hasattr(gift, 'tribe') or not gift.tribe):
                    gift_match = True
                    gift.match_type = 'general'  # Mark as general gift
                
                # If it matches, add to available gifts
                if gift_match:
                    available_gifts.append(gift)
            
            # Display available gifts
            gifts_shown = False
            for gift in sorted(available_gifts, key=lambda g: g.name):
                # Determine gift type based on marked match_type
                is_breed_gift = hasattr(gift, 'match_type') and gift.match_type == 'breed'
                is_auspice_gift = hasattr(gift, 'match_type') and gift.match_type == 'auspice'  
                is_tribe_gift = hasattr(gift, 'match_type') and gift.match_type == 'tribe'
                
                is_breed_tribe_auspice = is_breed_gift or is_auspice_gift or is_tribe_gift
                
                is_special = self._is_special_gift_stat(gift)
                
                # Calculate cost
                if is_special:
                    cost = 14  # Level 1 special gift
                elif is_breed_tribe_auspice:
                    cost = 3    # Level 1 breed/tribe/auspice gift
                else:
                    cost = 5    # Level 1 out-of-breed/tribe/auspice gift
                
                # Level 1 gifts don't require approval
                requires_approval = False
                status = self._get_affordable_status(cost, current_xp, requires_approval)
                
                # Add an indicator for breed/tribe/auspice gifts
                if is_breed_tribe_auspice:
                    # Add a category indicator to show why it's a match
                    if is_breed_gift:
                        gift_display = f"  {gift.name} [Breed]"
                    elif is_auspice_gift:
                        if aspect and shifter_info.get('aspects_to_auspices', {}).get(aspect, False):
                            gift_display = f"  {gift.name} [Aspect]"
                        else:
                            gift_display = f"  {gift.name} [Auspice]"
                    elif is_tribe_gift:
                        if shifter_type == 'Ananasi' and aspect and shifter_info.get('aspects_to_tribes', {}).get(aspect, False):
                            gift_display = f"  {gift.name} [Aspect]"
                        else:
                            gift_display = f"  {gift.name} [Tribe]"
                    else:
                        gift_display = f"  {gift.name}"
                else:
                    gift_display = gift.name
                    
                # Format the gift entry with wider name column
                # Truncate name if too long
                display_name = gift_display
                if len(display_name) > 42:
                    display_name = display_name[:39] + "..."
                
                # Format the display with exact spacing
                formatted_name = display_name.ljust(45)
                formatted_cost = str(cost).ljust(13)
                
                # Calculate padding for status field
                status_padding = 20 - len(status)
                
                # Add the entry
                output += f"| {formatted_name}{formatted_cost}{status}{' ' * status_padding} |\n"
                gifts_shown = True
                
            if not gifts_shown:
                note = f"No additional gifts available for {type_display} {breed} {auspice} {tribe} {aspect}."
                note_visible_length = len(note)
                note_padding = total_width - 4 - note_visible_length
                output += f"| {note}{' ' * note_padding} |\n"
        except Exception as e:
            error_note = f"Error querying available gifts: {str(e)}"
            error_visible_length = len(error_note)
            error_padding = total_width - 4 - error_visible_length
            output += f"| {error_note}{' ' * error_padding} |\n"
        
        # Display Rites section
        output += table_base['format_empty_row']()
        
        # Section header for rites
        section_title = "Rites"
        section_title_str = f" {section_title} "
        colored_title = f"|y{section_title_str}|n"
        visible_width = len(section_title_str)
        total_dash_count = total_width - 4 - visible_width
        left_dashes = total_dash_count // 2
        right_dashes = total_dash_count - left_dashes
        output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
        
        # Get current rites
        current_rites = character.db.stats.get('powers', {}).get('ritual', {})
        
        # Show current rites
        if current_rites:
            for rite_name, rite_data in sorted(current_rites.items()):
                # Get current level
                current = rite_data.get('perm', 0)
                if current < 5:  # Maximum level 5
                    next_level = current + 1
                    try:
                        # Rites cost 3 XP per level
                        cost = next_level * 3
                        
                        # Level 1 rites can be auto-spent, higher levels do
                        requires_approval = (next_level > 1)
                        status = self._get_affordable_status(cost, current_xp, requires_approval)
                        output += table_base['format_entry'](rite_name, current, next_level, cost, status)
                    except Exception as e:
                        character.msg(f"Error calculating cost for {rite_name}: {str(e)}")
        else:
            # Show available rite levels for purchase
            for level in range(1, 6):
                rite_name = f"Level {level} Rite"
                cost = level * 3  # Rites cost 3 XP per level
                
                # Level 1 rites don't require approval, higher levels do
                requires_approval = (level > 1)
                status = self._get_affordable_status(cost, current_xp, requires_approval)
                output += table_base['format_entry'](rite_name, 'N/A', 'New', cost, status)
        
        # Display gift cost notes
        output += table_base['format_empty_row']()
        
        note1 = "Note: Level 1 Gifts and Rites can be purchased with auto-spend."
        note1_visible_length = len(note1)
        note1_padding = total_width - 4 - note1_visible_length
        output += f"| {note1}{' ' * note1_padding} |\n"
        
        # Show appropriate affiliation note based on shifter type
        if breed or auspice or tribe or aspect:
            # For Ananasi, special note about Aspects and Factions
            if shifter_type == 'Ananasi':
                note2 = f"In-aspect/faction Gifts (3 XP × level) are double-indented."
                note2_visible_length = len(note2)
                note2_padding = total_width - 4 - note2_visible_length
                output += f"| {note2}{' ' * note2_padding} |\n"
            # For Ajaba, Ratkin, special note about Aspects
            elif shifter_type in ['Ajaba', 'Ratkin']:
                note2 = f"In-breed/aspect Gifts (3 XP × level) are double-indented."
                note2_visible_length = len(note2)
                note2_padding = total_width - 4 - note2_visible_length
                output += f"| {note2}{' ' * note2_padding} |\n"
            # For default Garou
            else:
                note2 = f"In-breed/tribe/auspice Gifts (3 XP × level) are double-indented."
                note2_visible_length = len(note2)
                note2_padding = total_width - 4 - note2_visible_length
                output += f"| {note2}{' ' * note2_padding} |\n"
            
            # List all relevant affiliations
            affiliations = []
            if breed:
                affiliations.append(breed)
            if tribe:
                affiliations.append(tribe)
            if auspice:
                affiliations.append(auspice)
            if aspect:
                affiliations.append(aspect)
            if faction:
                affiliations.append(faction)
                
            if affiliations:
                affiliations_text = f"Your affiliations: {', '.join(affiliations)}"
                affiliations_visible_length = len(affiliations_text)
                affiliations_padding = total_width - 4 - affiliations_visible_length
                output += f"| {affiliations_text}{' ' * affiliations_padding} |\n"
        
        # Add footer
        output += table_base['format_border']()
        
        return output
        
    def _is_breed_tribe_auspice_gift(self, gift_name, breed, tribe, auspice, shifter_type):
        """
        Check if a gift belongs to the character's breed, tribe, or auspice.
        Used for display purposes when we don't have the full gift object.
        """
        if not breed and not tribe and not auspice:
            return False
            
        # Simple check based on name matching
        gift_lower = gift_name.lower()
        
        # Check if the gift name contains the breed, tribe, or auspice
        if breed and breed.lower() in gift_lower:
            return True
        if tribe and tribe.lower() in gift_lower:
            return True
        if auspice and auspice.lower() in gift_lower:
            return True
            
        return False
        
    def _is_breed_tribe_auspice_gift_stat(self, gift_stat, breed, tribe, auspice, shifter_type):
        """
        Check if a gift belongs to the character's breed, tribe, or auspice.
        This version takes a full gift Stat object from the database.
        """
        # If any of these are missing, we can't determine
        if not gift_stat:
            return False
            
        # For debugging
        try:
            # Check breed match if breed is specified
            if breed and hasattr(gift_stat, 'breed') and gift_stat.breed:
                # Handle both string and list formats
                if isinstance(gift_stat.breed, str):
                    breeds = [gift_stat.breed]
                elif isinstance(gift_stat.breed, list):
                    breeds = gift_stat.breed
                else:
                    breeds = []
                    
                # Check if character's breed is in the gift's allowed breeds
                for b in breeds:
                    if b and breed.lower() in b.lower():
                        return True
                    
            # Check tribe match if tribe is specified
            if tribe and hasattr(gift_stat, 'tribe') and gift_stat.tribe:
                # Handle both string and list formats
                if isinstance(gift_stat.tribe, str):
                    tribes = [gift_stat.tribe]
                elif isinstance(gift_stat.tribe, list):
                    tribes = gift_stat.tribe
                else:
                    tribes = []
                    
                # Check if character's tribe is in the gift's allowed tribes
                for t in tribes:
                    if t and tribe.lower() in t.lower():
                        return True
                    
            # Check auspice match if auspice is specified
            if auspice and hasattr(gift_stat, 'auspice') and gift_stat.auspice:
                # Handle both string and list formats
                if isinstance(gift_stat.auspice, str):
                    auspices = [gift_stat.auspice]
                elif isinstance(gift_stat.auspice, list):
                    auspices = gift_stat.auspice
                else:
                    auspices = []
                    
                # Check if character's auspice is in the gift's allowed auspices
                for a in auspices:
                    if a and auspice.lower() in a.lower():
                        return True
                    
            # Check shifter type match if type is specified
            if shifter_type and hasattr(gift_stat, 'shifter_type') and gift_stat.shifter_type:
                # Handle both string and list formats
                if isinstance(gift_stat.shifter_type, str):
                    types = [gift_stat.shifter_type]
                elif isinstance(gift_stat.shifter_type, list):
                    types = gift_stat.shifter_type
                else:
                    types = []
                    
                # Check if character's shifter type is in the gift's allowed types
                for t in types:
                    if t and shifter_type.lower() in t.lower():
                        return True
        except Exception:
            # On any error, default to False
            return False
                
        return False
        
    def _ensure_list(self, value):
        """Convert a value to a list if it isn't already one"""
        if value is None:
            return []
        elif isinstance(value, list):
            return value
        else:
            return [value]

    def _display_mage_powers_direct(self, character, current_xp, total_width=78):
        """Display powers for Mage characters"""
        # Check if character is a Mage
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        if splat.lower() != 'mage':
            return "This command is only for Mage characters."
        
        # Get base table formatting
        table_base = self._powers_table_base(character, current_xp, total_width)
        output = table_base['output']
        
        # Get character's mage specifics
        tradition = character.db.stats.get('identity', {}).get('lineage', {}).get('Tradition', {}).get('perm', '')
        affiliation = character.db.stats.get('identity', {}).get('lineage', {}).get('Affiliation', {}).get('perm', '')
        
        # Add header
        header_text = f"Mage Powers:"
        visible_length = len(header_text) + 4  # +4 for |c and |n color codes
        padding = total_width - visible_length
        output += f"| |c{header_text}|n{' ' * padding} |\n"
        output += table_base['format_empty_row']()
        
        # Get current spheres
        current_spheres = character.db.stats.get('powers', {}).get('sphere', {})
        
        # Display spheres section
        # Section header
        section_title = "Spheres"
        section_title_str = f" {section_title} "
        colored_title = f"|y{section_title_str}|n"
        visible_width = len(section_title_str)
        total_dash_count = total_width - 4 - visible_width
        left_dashes = total_dash_count // 2
        right_dashes = total_dash_count - left_dashes
        output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
        
        # Determine affinity sphere based on tradition
        affinity_sphere = self._get_affinity_sphere(tradition)
        
        # Standard spheres
        all_spheres = ["Correspondence", "Entropy", "Forces", "Life", "Matter", "Mind", "Prime", "Spirit", "Time"]
        
        # Show current spheres
        for sphere_name in all_spheres:
            # Get current rating
            current = current_spheres.get(sphere_name, {}).get('perm', 0)
            
            # Only show if below max rating
            if current < 5:  # Maximum level 5
                next_level = current + 1
                try:
                    # Determine if this is the affinity sphere
                    is_affinity = sphere_name == affinity_sphere
                    
                    # Calculate cost: 8 x current rating, or 7 x current for affinity
                    if current == 0:
                        cost = 10  # First dot always costs 10 XP
                    elif is_affinity:
                        cost = current * 7  # Affinity sphere is cheaper
                    else:
                        cost = current * 8  # Regular sphere cost
                    
                    # Spheres above level 2 require approval (per AUTO_APPROVE rules)
                    requires_approval = (next_level > 2)
                    status = self._get_affordable_status(cost, current_xp, requires_approval)
                    
                    # Format the sphere entry
                    if is_affinity:
                        sphere_display = f"  {sphere_name} (Affinity)"
                    else:
                        sphere_display = sphere_name
                        
                    output += table_base['format_entry'](sphere_display, current, next_level, cost, status)
                except Exception as e:
                    character.msg(f"Error calculating cost for {sphere_name}: {str(e)}")

        # Add note about sphere advancement
        output += table_base['format_empty_row']()
        
        note1 = "Note: Spheres require at least Arete equal to the level to be purchased."
        note1_visible_length = len(note1)
        note1_padding = total_width - 4 - note1_visible_length
        output += f"| {note1}{' ' * note1_padding} |\n"
        
        if affinity_sphere:
            note2 = f"Affinity sphere ({affinity_sphere}) costs 7 XP × current level instead of 8 XP."
            note2_visible_length = len(note2)
            note2_padding = total_width - 4 - note2_visible_length
            output += f"| {note2}{' ' * note2_padding} |\n"
        
        note3 = "First dot in any sphere costs 10 XP."
        note3_visible_length = len(note3)
        note3_padding = total_width - 4 - note3_visible_length
        output += f"| {note3}{' ' * note3_padding} |\n"
        
        # Add table footer
        output += table_base['format_border']()
        
        return output
        
    def _get_affinity_sphere(self, tradition):
        """Return the affinity sphere based on the mage's tradition"""
        tradition_mappings = {
            "Akashic Brotherhood": "Mind",
            "Celestial Chorus": "Prime",
            "Cult of Ecstasy": "Time",
            "Dreamspeakers": "Spirit",
            "Euthanatos": "Entropy",
            "Order of Hermes": "Forces",
            "Sons of Ether": "Matter",
            "Society of Ether": "Matter",
            "Verbena": "Life",
            "Virtual Adepts": "Correspondence",
            "Hollow Ones": "",  # No affinity sphere
            "Orphans": "",  # No affinity sphere
            # Technocracy
            "Iteration X": "Matter",
            "New World Order": "Mind",
            "Progenitors": "Life",
            "Syndicate": "Entropy",
            "Void Engineers": "Correspondence"
        }
        
        return tradition_mappings.get(tradition, "")

    def _display_changeling_powers_direct(self, character, current_xp, total_width=78):
        """Display powers for Changeling characters"""
        # Check if character is a Changeling
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        if splat.lower() != 'changeling':
            return "This command is only for Changeling characters."
        
        # Get base table formatting
        table_base = self._powers_table_base(character, current_xp, total_width)
        output = table_base['output']
        
        # Get character's changeling specifics
        kith = character.db.stats.get('identity', {}).get('lineage', {}).get('Kith', {}).get('perm', '')
        court = character.db.stats.get('identity', {}).get('lineage', {}).get('Court', {}).get('perm', '')
        
        # Add header
        header_text = f"Changeling Powers:"
        visible_length = len(header_text) + 4  # +4 for |c and |n color codes
        padding = total_width - visible_length
        output += f"| |c{header_text}|n{' ' * padding} |\n"
        output += table_base['format_empty_row']()
        
        # Get current arts and realms
        current_arts = character.db.stats.get('powers', {}).get('art', {})
        current_realms = character.db.stats.get('powers', {}).get('realm', {})
        
        # Display arts section
        # Section header
        section_title = "Arts"
        section_title_str = f" {section_title} "
        colored_title = f"|y{section_title_str}|n"
        visible_width = len(section_title_str)
        total_dash_count = total_width - 4 - visible_width
        left_dashes = total_dash_count // 2
        right_dashes = total_dash_count - left_dashes
        output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
        
        # Show current arts
        all_arts = [
            "Chicanery", "Legerdemain", "Metamorphosis", "Naming", "Primal", 
            "Pyretics", "Soothsay", "Sovereign", "Wayfare", "Autumn",
            "Chronos", "Contract", "Dragon's Ire", "Infusion", "Oneiromancy",
            "Spring", "Stone", "Summer", "Winter"
        ]
        
        # Add known arts and purchasable arts
        arts_displayed = False
        
        # Show owned arts first
        for art_name in sorted(current_arts.keys()):
            arts_displayed = True
            current = current_arts[art_name].get('perm', 0)
            
            # Only show if below max rating
            if current < 5:  # Maximum level 5
                next_level = current + 1
                try:
                    # Calculate cost for arts based on level
                    if current == 0:
                        cost = 7  # First dot costs 7 XP
                    else:
                        cost = current * 4  # Subsequent dots cost 4 × current rating
                    
                    # Arts above level 2 require approval (per AUTO_APPROVE rules)
                    requires_approval = (next_level > 2)
                    status = self._get_affordable_status(cost, current_xp, requires_approval)
                    
                    output += table_base['format_entry'](art_name, current, next_level, cost, status)
                except Exception as e:
                    character.msg(f"Error calculating cost for {art_name}: {str(e)}")
        
        # Show purchasable arts (arts not currently owned)
        for art_name in sorted(art for art in all_arts if art not in current_arts):
            arts_displayed = True
            try:
                cost = 7  # First dot costs 7 XP
                requires_approval = False  # First dot doesn't require approval
                status = self._get_affordable_status(cost, current_xp, requires_approval)
                output += table_base['format_entry'](art_name, 0, 1, cost, status)
            except Exception as e:
                character.msg(f"Error calculating cost for {art_name}: {str(e)}")
        
        if not arts_displayed:
            note = "No Arts available for display."
            note_visible_length = len(note)
            note_padding = total_width - 4 - note_visible_length
            output += f"| {note}{' ' * note_padding} |\n"
        
        # Display realms section
        output += table_base['format_empty_row']()
        
        # Section header for realms
        section_title = "Realms"
        section_title_str = f" {section_title} "
        colored_title = f"|y{section_title_str}|n"
        visible_width = len(section_title_str)
        total_dash_count = total_width - 4 - visible_width
        left_dashes = total_dash_count // 2
        right_dashes = total_dash_count - left_dashes
        output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
        
        # Show current realms
        all_realms = [
            "Actor", "Fae", "Nature", "Prop", "Scene", "Time"
        ]
        
        realms_displayed = False
        
        # Show owned realms first
        for realm_name in sorted(current_realms.keys()):
            realms_displayed = True
            current = current_realms[realm_name].get('perm', 0)
            
            # Only show if below max rating
            if current < 5:  # Maximum level 5
                next_level = current + 1
                try:
                    # Calculate cost for realms based on level
                    if current == 0:
                        cost = 5  # First dot costs 5 XP
                    else:
                        cost = current * 3  # Subsequent dots cost 3 × current rating
                    
                    # Realms above level 2 require approval (per AUTO_APPROVE rules)
                    requires_approval = (next_level > 2)
                    status = self._get_affordable_status(cost, current_xp, requires_approval)
                    output += table_base['format_entry'](realm_name, current, next_level, cost, status)
                except Exception as e:
                    character.msg(f"Error calculating cost for {realm_name}: {str(e)}")
        
        # Show purchasable realms (realms not currently owned)
        for realm_name in sorted(realm for realm in all_realms if realm not in current_realms):
            realms_displayed = True
            try:
                cost = 5  # First dot costs 5 XP
                requires_approval = False  # First dot doesn't require approval
                status = self._get_affordable_status(cost, current_xp, requires_approval)
                output += table_base['format_entry'](realm_name, 0, 1, cost, status)
            except Exception as e:
                character.msg(f"Error calculating cost for {realm_name}: {str(e)}")
        
        if not realms_displayed:
            note = "No Realms available for display."
            note_visible_length = len(note)
            note_padding = total_width - 4 - note_visible_length
            output += f"| {note}{' ' * note_padding} |\n"
        
        # Add note about arts and realms costs
        output += table_base['format_empty_row']()
        
        note1 = "Note: Arts cost 7 XP for first dot, then 4 XP × current rating."
        note1_visible_length = len(note1)
        note1_padding = total_width - 4 - note1_visible_length
        output += f"| {note1}{' ' * note1_padding} |\n"
        
        note2 = "Realms cost 5 XP for first dot, then 3 XP × current rating."
        note2_visible_length = len(note2)
        note2_padding = total_width - 4 - note2_visible_length
        output += f"| {note2}{' ' * note2_padding} |\n"
        
        note3 = "ST approval needed for level 3+ Arts and Realms."
        note3_visible_length = len(note3)
        note3_padding = total_width - 4 - note3_visible_length
        output += f"| {note3}{' ' * note3_padding} |\n"
        
        # Add table footer
        output += table_base['format_border']()
        
        return output

    def _create_basic_table(self, total_width, messages):
        """Create a simple table with messages"""
        # Create table border
        border = f"+{'-' * (total_width - 2)}+\n"
        
        # Format the messages
        output = border
        for msg in messages:
            msg_visible_length = len(msg)
            msg_padding = total_width - 4 - msg_visible_length
            output += f"| {msg}{' ' * msg_padding} |\n"
        
        # Add footer
        output += border
        
        return output

    def _display_possessed_powers_direct(self, character, current_xp, total_width=78):
        """Display powers for Possessed characters"""
        # Check if character is Possessed
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        if splat.lower() != 'possessed':
            return "This command is only for Possessed characters."
        
        # Get base table formatting
        table_base = self._powers_table_base(character, current_xp, total_width)
        output = table_base['output']
        
        # Add header
        header_text = "Possessed Powers:"
        visible_length = len(header_text) + 4  # +4 for |c and |n color codes
        padding = total_width - visible_length
        output += f"| |c{header_text}|n{' ' * padding} |\n"
        output += table_base['format_empty_row']()
        
        # Get current blessings
        current_blessings = character.db.stats.get('powers', {}).get('blessing', {})
        
        # Display blessings section
        # Section header
        section_title = "Blessings"
        section_title_str = f" {section_title} "
        colored_title = f"|y{section_title_str}|n"
        visible_width = len(section_title_str)
        total_dash_count = total_width - 4 - visible_width
        left_dashes = total_dash_count // 2
        right_dashes = total_dash_count - left_dashes
        output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
        
        # Show current blessings
        if current_blessings:
            for blessing_name, blessing_data in sorted(current_blessings.items()):
                current = blessing_data.get('perm', 0)
                
                # Only show if below max rating
                if current < 5:  # Maximum level 5
                    next_level = current + 1
                    try:
                        # Calculate cost: 4 XP × rating
                        cost = next_level * 4
                        
                        # Blessings above level 2 require approval
                        requires_approval = (next_level > 2)
                        status = self._get_affordable_status(cost, current_xp, requires_approval)
                        
                        output += table_base['format_entry'](blessing_name, current, next_level, cost, status)
                    except Exception as e:
                        character.msg(f"Error calculating cost for {blessing_name}: {str(e)}")
        else:
            # Message if no current blessings
            note = "No current Blessings. New blessings require ST approval."
            note_visible_length = len(note)
            note_padding = total_width - 4 - note_visible_length
            output += f"| {note}{' ' * note_padding} |\n"
        
        # Add note about blessings costs
        output += table_base['format_empty_row']()
        
        note1 = "Note: Blessings cost 4 XP × rating."
        note1_visible_length = len(note1)
        note1_padding = total_width - 4 - note1_visible_length
        output += f"| {note1}{' ' * note1_padding} |\n"
        
        note2 = "New Blessings and Blessings above level 2 require ST approval."
        note2_visible_length = len(note2)
        note2_padding = total_width - 4 - note2_visible_length
        output += f"| {note2}{' ' * note2_padding} |\n"
        
        # Add table footer
        output += table_base['format_border']()
        
        return output

    def _display_companion_powers_direct(self, character, current_xp, total_width=78):
        """Display powers for Companion characters"""
        # Check if character is a Companion
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        if splat.lower() != 'companion':
            return "This command is only for Companion characters."
        
        # Get base table formatting
        table_base = self._powers_table_base(character, current_xp, total_width)
        output = table_base['output']
        
        # Import special advantages mappings
        from world.wod20th.utils.stat_mappings import COMBAT_SPECIAL_ADVANTAGES, SPECIAL_ADVANTAGES
        
        # Add header
        header_text = "Companion Powers:"
        visible_length = len(header_text) + 4  # +4 for |c and |n color codes
        padding = total_width - visible_length
        output += f"| |c{header_text}|n{' ' * padding} |\n"
        output += table_base['format_empty_row']()
        
        # Get current special advantages
        current_advantages = character.db.stats.get('powers', {}).get('special_advantage', {})
        
        # Display current special advantages section
        # Section header
        section_title = "Current Special Advantages"
        section_title_str = f" {section_title} "
        colored_title = f"|y{section_title_str}|n"
        visible_width = len(section_title_str)
        total_dash_count = total_width - 4 - visible_width
        left_dashes = total_dash_count // 2
        right_dashes = total_dash_count - left_dashes
        output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
        
        # Create a custom header for special advantages table
        output += f"| {'Advantage':<30}{'Current':<12}{'Valid Values':<22}{'Status':<10} |\n"
        output += f"| {'-' * 30}{'-' * 12}{'-' * 22}{'-' * 10} |\n"
        
        # Display current advantages
        if current_advantages:
            has_current_advantages = False
            for adv_name, adv_data in sorted(current_advantages.items()):
                current = adv_data.get('perm', 0)
                
                # Skip advantages with value 0
                if current <= 0:
                    continue
                    
                has_current_advantages = True
                
                # Get the valid values for this advantage
                valid_values = []
                
                # Find the valid values for this advantage
                if adv_name.lower() in {k.lower(): k for k in COMBAT_SPECIAL_ADVANTAGES.keys()}:
                    advantage_key = {k.lower(): k for k in COMBAT_SPECIAL_ADVANTAGES.keys()}[adv_name.lower()]
                    valid_values = COMBAT_SPECIAL_ADVANTAGES[advantage_key].get('valid_values', [])
                elif adv_name.lower() in {k.lower(): k for k in SPECIAL_ADVANTAGES.keys()}:
                    advantage_key = {k.lower(): k for k in SPECIAL_ADVANTAGES.keys()}[adv_name.lower()]
                    valid_values = SPECIAL_ADVANTAGES[advantage_key].get('valid_values', [])
                
                # Find next valid value and all higher valid values
                next_values = [v for v in sorted(valid_values) if v > current]
                
                # Capitalize the advantage name
                display_name = adv_name.title()
                if len(display_name) > 28:
                    display_name = display_name[:25] + "..."
                
                # Format the display string
                if next_values:
                    # Show available values to upgrade to
                    values_display = ", ".join(str(v) for v in next_values)
                    requires_approval = True  # Special advantages always require approval
                    status = "(ST Appr)"
                    
                    # Calculate padding to ensure fixed width
                    name_padding = 30 - len(display_name)
                    current_padding = 12 - len(str(current))
                    values_padding = 22 - len(values_display)
                    status_padding = 10 - len(status)
                    
                    output += f"| {display_name}{' ' * name_padding}{current}{' ' * current_padding}{values_display}{' ' * values_padding}{status}{' ' * status_padding} |\n"
                else:
                    # At maximum value
                    values_display = "Max"
                    status = "N/A"
                    
                    # Calculate padding to ensure fixed width
                    name_padding = 30 - len(display_name)
                    current_padding = 12 - len(str(current))
                    values_padding = 22 - len(values_display)
                    status_padding = 10 - len(status)
                    
                    output += f"| {display_name}{' ' * name_padding}{current}{' ' * current_padding}{values_display}{' ' * values_padding}{status}{' ' * status_padding} |\n"
            
            if not has_current_advantages:
                # Message if no current special advantages with values > 0
                note = "No current Special Advantages."
                note_visible_length = len(note)
                note_padding = total_width - 4 - note_visible_length
                output += f"| {note}{' ' * note_padding} |\n"
        else:
            # Message if no current special advantages
            note = "No current Special Advantages."
            note_visible_length = len(note)
            note_padding = total_width - 4 - note_visible_length
            output += f"| {note}{' ' * note_padding} |\n"
        
        # Display available special advantages section
        output += table_base['format_empty_row']()
        
        # Combine all advantages for display
        all_advantages = {}
        all_advantages.update({k: v for k, v in COMBAT_SPECIAL_ADVANTAGES.items()})
        all_advantages.update({k: v for k, v in SPECIAL_ADVANTAGES.items()})
        
        # Filter out advantages the character already has at max level
        available_advantages = {}
        for adv_name, adv_data in all_advantages.items():
            if adv_name.lower() not in {k.lower() for k in current_advantages.keys()}:
                available_advantages[adv_name] = adv_data
            else:
                # Get current level
                current_level = 0
                for current_adv, current_data in current_advantages.items():
                    if current_adv.lower() == adv_name.lower():
                        current_level = current_data.get('perm', 0)
                        break
                
                # Check if there are higher valid values
                valid_values = adv_data.get('valid_values', [])
                has_higher_value = any(value > current_level for value in valid_values)
                
                if has_higher_value:
                    available_advantages[adv_name] = adv_data
        
        # Section header for available advantages
        section_title = "Available Special Advantages"
        section_title_str = f" {section_title} "
        colored_title = f"|y{section_title_str}|n"
        visible_width = len(section_title_str)
        total_dash_count = total_width - 4 - visible_width
        left_dashes = total_dash_count // 2
        right_dashes = total_dash_count - left_dashes
        output += f"| {'-' * left_dashes}{colored_title}{'-' * right_dashes} |\n"
        
        # Create a custom header for available advantages table
        output += f"| {'Advantage':<34}{'Valid Values':<20}{'Cost':<10}{'Status':<10} |\n"
        output += f"| {'-' * 34}{'-' * 20}{'-' * 10}{'-' * 10} |\n"
        
        # Display available advantages
        if available_advantages:
            # First, show advantages not yet purchased
            new_advantages = {k: v for k, v in available_advantages.items() 
                             if k.lower() not in {adv.lower() for adv in current_advantages.keys()}}
            
            for adv_name, adv_data in sorted(new_advantages.items()):
                # Get valid values
                valid_values = adv_data.get('valid_values', [])
                
                if valid_values:
                    # Capitalize the advantage name
                    display_name = adv_name.title()
                    description = adv_data.get('desc', '')
                    
                    # If description is available and name is short enough, include it
                    if description and len(display_name) + len(description) + 3 <= 33:
                        display_name = f"{display_name} ({description})"
                    
                    # Truncate if too long
                    if len(display_name) > 32:
                        display_name = display_name[:29] + "..."
                    
                    # Format values display
                    values_display = ", ".join(str(v) for v in sorted(valid_values))
                    if len(values_display) > 18:  # Truncate if too long
                        values_display = values_display[:15] + "..."
                    
                    # Special advantages always require approval
                    requires_approval = True
                    status = "(ST Appr)"
                    
                    # Calculate padding to ensure fixed width
                    name_padding = 34 - len(display_name)
                    values_padding = 20 - len(values_display)
                    cost_str = "2*Rating" 
                    cost_padding = 10 - len(cost_str)
                    status_padding = 10 - len(status)
                    
                    output += f"| {display_name}{' ' * name_padding}{values_display}{' ' * values_padding}{cost_str}{' ' * cost_padding}{status}{' ' * status_padding} |\n"
            
            # Then show upgrades to existing advantages
            upgrade_advantages = {k: v for k, v in available_advantages.items() 
                               if k.lower() in {adv.lower() for adv in current_advantages.keys()}}
            
            if upgrade_advantages and new_advantages:
                # Add separator if we have both new and upgrade advantages
                output += f"| {'-' * (total_width - 4)} |\n"
            
            for adv_name, adv_data in sorted(upgrade_advantages.items()):
                # Get current level
                current_level = 0
                for current_adv, current_data in current_advantages.items():
                    if current_adv.lower() == adv_name.lower():
                        current_level = current_data.get('perm', 0)
                        break
                
                # Get valid values higher than current
                valid_values = adv_data.get('valid_values', [])
                higher_values = [v for v in sorted(valid_values) if v > current_level]
                
                if higher_values:
                    # Capitalize the advantage name
                    display_name = adv_name.title() + " (Upgrade)"
                    
                    # Truncate if too long
                    if len(display_name) > 32:
                        display_name = display_name[:29] + "..."
                    
                    # Format values display
                    values_display = ", ".join(str(v) for v in higher_values)
                    if len(values_display) > 18:  # Truncate if too long
                        values_display = values_display[:15] + "..."
                    
                    # Cost is difference between current value and new value
                    min_higher = min(higher_values)
                    cost = "Rating"
                    cost_str = str(cost)
                    
                    # Special advantages always require approval
                    requires_approval = True
                    status = "(ST Appr)"
                    
                    # Calculate padding to ensure fixed width
                    name_padding = 34 - len(display_name)
                    values_padding = 20 - len(values_display)
                    cost_padding = 10 - len(cost_str)
                    status_padding = 10 - len(status)
                    
                    output += f"| {display_name}{' ' * name_padding}{values_display}{' ' * values_padding}{cost_str}{' ' * cost_padding}{status}{' ' * status_padding} |\n"
        else:
            # Message if no available special advantages
            note = "No additional Special Advantages available."
            note_visible_length = len(note)
            note_padding = total_width - 4 - note_visible_length
            output += f"| {note}{' ' * note_padding} |\n"
        
        # Add note about special advantages
        output += table_base['format_empty_row']()
        
        note1 = "Note: All Special Advantages require ST approval."
        note1_visible_length = len(note1)
        note1_padding = total_width - 4 - note1_visible_length
        output += f"| {note1}{' ' * note1_padding} |\n"
        
        note2 = "For new purchases, cost equals the point value."
        note2_visible_length = len(note2)
        note2_padding = total_width - 4 - note2_visible_length
        output += f"| {note2}{' ' * note2_padding} |\n"
        
        # Add table footer
        output += table_base['format_border']()
        
        return output