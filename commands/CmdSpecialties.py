"""
Command for managing character specialties.

Specialties are allowed for Attributes or Abilities that have been increased to 4 or higher.
A player is allowed to add one specialty for each point of an attribute or ability over 3
(one at 4, two at 5).
"""

from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.utils import list_to_string

class CmdSpecialties(MuxCommand):
    """
    View and manage character specialties.

    Usage:
      +specialties                     - View your specialties and available options
      +specialties/add <stat>=<spec>   - Add a specialty to a stat
      +specialties/add <stat>=<spec>/yes - Confirm adding a specialty (cannot be removed)
      
    Staff Usage:
      +specialties <name>              - View another character's specialties
      +specialties/add name/<stat>=<spec> - Add specialty to another character
      +specialties/del name/<stat>=<spec> - Remove specialty from another character

    Specialties are permanent additions to your character's abilities that represent
    focused expertise in specific aspects of a skill or attribute. They can only be
    added to stats rated 4 or higher, and you get one specialty slot at 4 dots and
    two slots at 5 dots.
    
    |r+specialty is also an alias for +specialties.|n
    """

    key = "+specialties"
    aliases = ["+specialty"]
    locks = "cmd:all()"
    help_category = "Character"

    def _get_char(self, name=None):
        """Helper method to get character, either caller or named character for staff."""
        if not name:
            return self.caller
        # Staff only beyond this point
        if not self.caller.check_permstring("builder"):
            self.caller.msg("You don't have permission to view other characters' specialties.")
            return None
        char = self.caller.search(name)
        return char

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
        
        # Get all stats that are 4 or higher
        high_stats = []
        available_slots = {}
        stat_levels = {}  # Store the levels for display
        
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
                        if value >= 4:
                            high_stats.append(ability_name)
                            available_slots[ability_name.lower()] = 2 if value >= 5 else 1
                            stat_levels[ability_name] = value

        # Format the output
        output = []
        output.append("|b--------------------------------< |ySpecialties|n |b>--------------------------------|n")
        
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
        if high_stats:
            # Format stats with their levels
            stats_with_levels = []
            for stat in sorted(high_stats):
                stats_with_levels.append(f"|w{stat}|n ({stat_levels[stat]})")
            
            # Wrap the stats line with proper indentation
            wrapped_stats = []
            current_line = []
            current_length = 0
            prefix = "|yStats above 4:|n "
            indent = " " * 14  # Length of "Stats above 4: " without color codes
            
            for stat in stats_with_levels:
                # Calculate visible length (excluding color codes)
                stat_visible_length = len(stat) - 6  # Subtract length of color codes
                if current_length + stat_visible_length + 2 > 78 - 14:  # +2 for ", "
                    wrapped_stats.append(f"{prefix if not wrapped_stats else indent}{', '.join(current_line)}")
                    current_line = [stat]
                    current_length = stat_visible_length
                else:
                    current_line.append(stat)
                    current_length += stat_visible_length + 2
            
            if current_line:
                wrapped_stats.append(f"{prefix if not wrapped_stats else indent}{', '.join(current_line)}")
            output.extend(wrapped_stats)
            
            # Calculate which stats can still have specialties added
            available = []
            for stat in sorted(high_stats):
                stat_lower = stat.lower()
                current = len(specialties.get(stat_lower, []))
                slots = available_slots.get(stat_lower, 0)
                remaining_slots = slots - current
                if remaining_slots > 0:
                    if remaining_slots > 1:
                        available.append(f"|w{stat}|n ({remaining_slots} points)")
                    else:
                        available.append(f"|w{stat}|n")
            
            if available:
                # Wrap the available specialties line
                wrapped_available = []
                current_line = []
                current_length = 0
                prefix = "|ySpecialties available:|n "
                indent = " " * 21  # Length of "Specialties available: " without color codes
                
                for stat in available:
                    # Calculate visible length (excluding color codes)
                    stat_visible_length = len(stat) - 6  # Subtract length of color codes
                    if current_length + stat_visible_length + 2 > 78 - 21:
                        wrapped_available.append(f"{prefix if not wrapped_available else indent}{', '.join(current_line)}")
                        current_line = [stat]
                        current_length = stat_visible_length
                    else:
                        current_line.append(stat)
                        current_length += stat_visible_length + 2
                
                if current_line:
                    wrapped_available.append(f"{prefix if not wrapped_available else indent}{', '.join(current_line)}")
                output.extend(wrapped_available)
            else:
                output.append("No specialty slots available.")
        else:
            output.append("No stats are high enough to have specialties (requires level 4+)")
            
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

            # Validate the stat exists and is high enough
            stat_level = self._get_stat_level(char, stat)
            if stat_level is None:
                self.caller.msg(f"Stat '{stat}' not found.")
                return
                
            if stat_level < 4:
                self.caller.msg(f"Stat '{stat}' must be at least level 4 to add specialties.")
                return

            # Get current specialties and validate slots
            specialties = self._get_specialties(char)
            current_specs = specialties.get(stat, [])
            max_specs = 2 if stat_level >= 5 else 1
            
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