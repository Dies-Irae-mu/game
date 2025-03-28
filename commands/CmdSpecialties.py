"""
Command for managing character specialties.

Some abilities require specialties at level 1, while others allow specialties at higher levels.
For abilities that don't require specialties, you get one specialty slot at 4 dots and
two slots at 5 dots.
"""

from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.utils import list_to_string
from commands.CmdSelfStat import REQUIRED_SPECIALTIES
from decimal import Decimal
from evennia import logger
import datetime
from evennia.utils.search import search_object

class CmdSpecialties(MuxCommand):
    """
    View and manage character specialties.

    Usage:
      +specialties                     - View your specialties and available options
      +specialties/add <stat>=<spec>   - Add a specialty to a stat
      +specialties/add <stat>=<spec>/yes - Confirm adding a specialty (cannot be removed)
      +specialties/buy <stat>=<spec>   - Buy a specialty with freebie points or XP
      
    Staff Usage:
      +specialties <name>              - View another character's specialties
      +specialties/add name/<stat>=<spec> - Add specialty to another character
      +specialties/del name/<stat>=<spec> - Remove specialty from another character

    Some abilities (like Crafts, Artistry, etc.) require a specialty as soon as you
    put any dots in them. Other abilities allow specialties when you reach higher
    levels (one specialty at 4 dots, two at 5 dots).
    
    Buying specialties costs 1 freebie point during character generation, or 4 XP
    after approval. Specialties purchased this way do not require the skill to be 4+.

    |r+specialty is also an alias for +specialties.|n
    """

    key = "+specialties"
    aliases = ["+specialty"]
    locks = "cmd:all()"
    help_category = "Chargen & Character Info"

    def _get_char(self, name=None):
        """Helper method to get character, either caller or named character for staff."""
        if not name:
            return self.caller
        # Staff only beyond this point
        if not self.caller.check_permstring("builder"):
            self.caller.msg("You don't have permission to view other characters' specialties.")
            return None
        # Use global search for staff
        char = search_object(name, typeclass='typeclasses.characters.Character')
        if not char:
            self.caller.msg(f"Could not find character '{name}'.")
            return None
        return char[0]  # search_object returns a list, get the first match

    def _get_stat_level(self, char, stat_name):
        """Helper method to get the level of a stat."""
        stats = char.attributes.get('stats', {})
        stat_name = stat_name.lower()

        # Check attributes
        if 'attributes' in stats:
            for category, attrs in stats['attributes'].items():
                for attr_name, attr_data in attrs.items():
                    if attr_name.lower() == stat_name:
                        return attr_data.get('perm', 0)

        # Check abilities and secondary abilities
        ability_categories = ['abilities', 'secondary_abilities']
        for main_category in ability_categories:
            if main_category in stats:
                for subcategory, abilities in stats[main_category].items():
                    for ability_name, ability_data in abilities.items():
                        if ability_name.lower() == stat_name:
                            return ability_data.get('perm', 0)

        return None

    def _get_specialties(self, char):
        """Helper method to get a character's specialties."""
        return char.db.specialties or {}

    def _format_specialties_display(self, char):
        """Helper method to format the specialties display."""
        specialties = self._get_specialties(char)
        
        # Get all stats that are 4 or higher and stats that require specialties
        high_stats = []
        available_slots = {}
        stat_levels = {}  # Store the levels for display
        required_stats_without_specialty = []
        required_stats_with_specialty = []  # Track required stats that have specialties
        
        # Get the stats dictionary from character attributes
        stats = char.attributes.get('stats', {})
        
        # Check attributes
        if 'attributes' in stats:
            for category, attrs in stats['attributes'].items():
                for stat_name, stat_data in attrs.items():
                    value = stat_data.get('perm', 0)  # Use permanent value
                    if value >= 4:
                        high_stats.append(stat_name)
                        available_slots[stat_name.lower()] = 2 if value >= 5 else 1
                        stat_levels[stat_name] = value
        
        # Check abilities (including secondary abilities)
        ability_categories = ['abilities', 'secondary_abilities']
        for main_category in ability_categories:
            if main_category in stats:
                for subcategory, abilities in stats[main_category].items():
                    for ability_name, ability_data in abilities.items():
                        value = ability_data.get('perm', 0)  # Use permanent value
                        # Check if ability requires a specialty
                        if value > 0 and ability_name in REQUIRED_SPECIALTIES:
                            if ability_name.lower() not in specialties or not specialties[ability_name.lower()]:
                                required_stats_without_specialty.append(ability_name)
                            else:
                                required_stats_with_specialty.append(ability_name)
                        # Check for high-level specialties
                        if value >= 4 and ability_name not in REQUIRED_SPECIALTIES:
                            high_stats.append(ability_name)
                            available_slots[ability_name.lower()] = 2 if value >= 5 else 1
                            stat_levels[ability_name] = value

        # Format the output
        output = []
        # Calculate padding needed for 78 characters total
        # Each color code (|b, |y, |n) actually becomes an ANSI sequence that's longer
        # We need to account for just the visible characters, not the color codes
        name_space = len(char.name)
        visible_text = f"< Specialties for {char.name} >"  # The text without any color codes
        visible_length = len(visible_text)
        total_dashes = 78 - visible_length
        left_dashes = "-" * (total_dashes // 2)
        right_dashes = "-" * (total_dashes - (total_dashes // 2))  # Handle odd number if needed
        
        header = f"|b{left_dashes}< |ySpecialties for {char.name}|n |b>{right_dashes}|n"
        # Debug check - remove color codes to verify actual length
        debug_length = len(visible_text) + len(left_dashes) + len(right_dashes)
        if debug_length != 78:
            logger.log_err(f"Header length incorrect: {debug_length} chars (should be 78)")
        output.append(header)
        
        # Show required specialties first if any are missing
        if required_stats_without_specialty:
            output.append("\n|rRequired Specialties Missing:|n")
            for stat in required_stats_without_specialty:
                output.append(f"- {stat} ({REQUIRED_SPECIALTIES[stat]})")
            output.append("")

        # List current specialties in two columns
        if specialties:
            # Convert specialties to a flat list of "stat - specialty" strings
            specialty_lines = []
            for stat, specs in sorted(specialties.items()):
                for spec in specs:
                    specialty_lines.append(f"|w{stat.title()}|n - |c{spec}|n")
            
            # Split into two columns
            mid_point = (len(specialty_lines) + 1) // 2
            for i in range(max(mid_point, len(specialty_lines) - mid_point)):
                left_col = specialty_lines[i] if i < len(specialty_lines) else ""
                right_col = specialty_lines[i + mid_point] if i + mid_point < len(specialty_lines) else ""
                if right_col:
                    output.append(f"{left_col:<39}{right_col}")
                else:
                    output.append(left_col)
        else:
            output.append("No specialties set.")
            
        output.append("\n|b-----------------------------< |yAvailable Options|n |b>-----------------------------|n")
        
        # List stats that can have specialties
        available_stats = []
        
        # Add required specialty abilities that don't have specialties yet
        for stat in required_stats_without_specialty:
            available_stats.append(f"|w{stat}|n (required)")
        
        # Add high-level abilities that can have specialties
        if high_stats:
            for stat in sorted(high_stats):
                if stat not in REQUIRED_SPECIALTIES:  # Skip required specialty abilities as they're handled above
                    stat_lower = stat.lower()
                    current = len(specialties.get(stat_lower, []))
                    slots = available_slots.get(stat_lower, 0)
                    remaining_slots = slots - current
                    if remaining_slots > 0:
                        if remaining_slots > 1:
                            available_stats.append(f"|w{stat}|n ({remaining_slots} slots)")
                        else:
                            available_stats.append(f"|w{stat}|n")
        
        if available_stats:
            # Wrap the available stats line
            wrapped_stats = []
            current_line = []
            current_length = 0
            prefix = "|yStats available for specialties:|n "
            indent = " " * 30  # Length of prefix without color codes
            
            for stat in available_stats:
                # Calculate visible length (excluding color codes)
                stat_visible_length = len(stat) - 6  # Subtract length of color codes
                if current_length + stat_visible_length + 2 > 78 - 30:  # +2 for ", "
                    wrapped_stats.append(f"{prefix if not wrapped_stats else indent}{', '.join(current_line)}")
                    current_line = [stat]
                    current_length = stat_visible_length
                else:
                    current_line.append(stat)
                    current_length += stat_visible_length + 2
            
            if current_line:
                wrapped_stats.append(f"{prefix if not wrapped_stats else indent}{', '.join(current_line)}")
            output.extend(wrapped_stats)
        else:
            if not required_stats_without_specialty and not high_stats:
                output.append("No stats are available for specialties")
        
        # Add info about buying specialties
        output.append("\n|yYou can buy additional specialties with:|n")
        output.append("   - 1 freebie point during character generation (+specialties/buy)")
        output.append("   - 4 XP after approval (+specialties/buy)")
            
        output.append("|b--------------------------------------------------------------------------------|n")
        
        return "\n".join(output)

    def func(self):
        """Main function for the command."""
        if not self.args and not self.switches:
            # Display own specialties
            self.caller.msg(self._format_specialties_display(self.caller))
            return

        if not self.switches and self.args:
            # Staff viewing another character's specialties
            char = self._get_char(self.args)
            if not char:
                return
            self.caller.msg(self._format_specialties_display(char))
            return

        switch = self.switches[0].lower()

        if switch == "add":
            # Handle staff adding specialties to others
            if "/" in self.lhs:
                # Staff adding to another character
                if not self.caller.check_permstring("builder"):
                    self.caller.msg("You don't have permission to add specialties to other characters.")
                    return
                    
                char_name, stat = self.lhs.split("/", 1)
                char = self._get_char(char_name)
                if not char:
                    return
                    
                stat = stat.lower()
                specialty = self.rhs
                
            else:
                # Player adding to themselves
                char = self.caller
                stat = self.lhs.lower()
                specialty = self.rhs
                
                # Check for confirmation
                if not specialty.endswith("/yes"):
                    self.caller.msg("Warning: Specialties cannot be removed once added. "
                                  f"To confirm adding '{specialty}' to {stat}, type: "
                                  f"+specialties/add {stat}={specialty}/yes")
                    return
                specialty = specialty.replace("/yes", "")

            # Validate the stat exists
            stat_level = self._get_stat_level(char, stat)
            if stat_level is None:
                self.caller.msg(f"Stat '{stat}' not found.")
                return

            # Check if this is a required specialty ability
            stat_title = stat.title()
            if stat_title in REQUIRED_SPECIALTIES:
                # For required specialty abilities, only check that the stat exists and has a value
                if stat_level <= 0:
                    self.caller.msg(f"You must have at least 1 dot in {stat_title} to add specialties.")
                    return
            else:
                # For normal abilities, require level 4+
                if stat_level < 4:
                    self.caller.msg(f"Stat '{stat}' must be at least level 4 to add specialties.")
                    return

            # Get current specialties and validate slots
            specialties = self._get_specialties(char)
            current_specs = specialties.get(stat, [])
            
            # Calculate max specs based on whether it's a required specialty ability
            if stat_title in REQUIRED_SPECIALTIES:
                max_specs = 1  # Required specialty abilities always get 1 specialty
            else:
                max_specs = 2 if stat_level >= 5 else 1  # Normal abilities get 1 at 4, 2 at 5
            
            if len(current_specs) >= max_specs:
                self.caller.msg(f"No more specialty slots available for '{stat}'.")
                return

            # Add the specialty
            if stat not in specialties:
                specialties[stat] = []
            specialties[stat].append(specialty)
            char.db.specialties = specialties
            
            self.caller.msg(f"Added specialty '{specialty}' to {stat} for {char.name}.")
            if char != self.caller:
                char.msg(f"A specialty '{specialty}' has been added to your {stat} by {self.caller.name}.")

        elif switch == "buy":
            # Player buying a specialty with freebie points or XP
            char = self.caller
            stat = self.lhs.lower()
            specialty = self.rhs

            # Validate the stat exists
            stat_level = self._get_stat_level(char, stat)
            if stat_level is None:
                self.caller.msg(f"Stat '{stat}' not found.")
                return
                
            # Make sure the specialty is not empty
            if not specialty:
                self.caller.msg("You must specify a specialty.")
                return

            # Get current specialties
            specialties = self._get_specialties(char)
            current_specs = specialties.get(stat, [])
            
            # Check if specialty already exists
            if specialty in current_specs:
                self.caller.msg(f"Specialty '{specialty}' already exists for {stat}.")
                return

            # Determine if character is approved or in chargen
            is_approved = char.db.approved
            
            if is_approved:
                # Character is approved, use XP
                xp_cost = 4  # 4 XP for specialties
                
                # Check if character has enough XP
                if not hasattr(char.db, 'xp') or not char.db.xp:
                    self.caller.msg("You don't have any XP set up on your character.")
                    return
                
                current_xp = char.db.xp.get('current', 0)
                if current_xp < xp_cost:
                    self.caller.msg(f"You don't have enough XP to buy this specialty. Cost: {xp_cost} XP, Available: {current_xp} XP.")
                    return
                
                # Deduct XP and log the spend
                try:
                    # Convert to Decimal for precise calculation
                    current_xp = Decimal(str(current_xp))
                    spent_xp = Decimal(str(char.db.xp.get('spent', 0)))
                    
                    # Update character's XP values
                    char.db.xp['current'] = current_xp - xp_cost
                    char.db.xp['spent'] = spent_xp + xp_cost
                    
                    # Log the spend
                    spend_entry = {
                        'type': 'spend',
                        'amount': float(xp_cost),
                        'stat_name': f"Specialty: {stat} - {specialty}",
                        'previous_rating': 0,
                        'new_rating': 1,
                        'reason': f"Purchased specialty '{specialty}' for {stat}",
                        'timestamp': datetime.datetime.now().isoformat()
                    }
                    
                    if 'spends' not in char.db.xp:
                        char.db.xp['spends'] = []
                    char.db.xp['spends'].insert(0, spend_entry)
                    
                    # Add the specialty
                    if stat not in specialties:
                        specialties[stat] = []
                    specialties[stat].append(specialty)
                    char.db.specialties = specialties
                    
                    self.caller.msg(f"You've purchased the specialty '{specialty}' for {stat} for {xp_cost} XP.")
                    
                except Exception as e:
                    logger.log_err(f"Error processing specialty XP purchase: {str(e)}")
                    self.caller.msg(f"Error processing purchase: {str(e)}")
                
            else:
                # Character is in chargen, use freebie points
                freebie_cost = 1  # 1 freebie point per specialty
                
                # For characters in chargen, we don't track freebies directly
                # Just add the specialty and inform the player it will count during approval
                
                # Add the specialty
                if stat not in specialties:
                    specialties[stat] = []
                specialties[stat].append(specialty)
                char.db.specialties = specialties
                
                self.caller.msg(f"You've added the specialty '{specialty}' for {stat}.")
                self.caller.msg(f"This will cost {freebie_cost} freebie points during character approval.")
                self.caller.msg("Use the +check command to see your total freebie point allocation.")

        elif switch == "del":
            # Staff only - remove a specialty
            if not self.caller.check_permstring("builder"):
                self.caller.msg("You don't have permission to remove specialties.")
                return

            if "/" not in self.lhs:
                self.caller.msg("Usage: +specialties/del name/stat=specialty")
                return

            char_name, stat = self.lhs.split("/", 1)
            char = self._get_char(char_name)
            if not char:
                return

            stat = stat.lower()
            specialty = self.rhs
            
            specialties = self._get_specialties(char)
            if stat not in specialties or specialty not in specialties[stat]:
                self.caller.msg(f"Specialty '{specialty}' not found in {stat} for {char.name}.")
                return

            specialties[stat].remove(specialty)
            if not specialties[stat]:
                del specialties[stat]
            char.db.specialties = specialties
            
            self.caller.msg(f"Removed specialty '{specialty}' from {stat} for {char.name}.")
            char.msg(f"Your specialty '{specialty}' in {stat} has been removed by {self.caller.name}.") 