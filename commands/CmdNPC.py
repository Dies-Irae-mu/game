from evennia import default_cmds
from evennia.utils.ansi import ANSIString
from world.wod20th.utils.dice_rolls import roll_dice, interpret_roll_results
import random
import os
import json

# Path to the name files
NAME_DATA_PATH = "world/wod20th/data/names"

class NameGenerator:
    """
    Handles generation of random names from various cultural backgrounds.
    """
    
    # Dictionary to hold name lists once loaded
    name_lists = {}
    
    # List of available nationalities/ethnicities
    available_nationalities = [
        "american", "arabic", "argentine", "australian", "brazilian", "canadian",
        "chechen", "chilean", "chinese", "czech", "danish", "dutch", "filipino", "finnish", "french", 
        "german", "greek", "hungarian", "irish", "italian", "jamaican", "japanese", 
        "korean", "latvian", "maori", "mexican", "mongolian", "nahuatl", "indian", "norwegian", "pakistani",
        "persian", "polish", "portuguese", "prison", "roma", "romanian", "russian", "senegalese",
        "serbian", "sicilian", "slovene", "spanish", "thai", "turkish", "ukrainian", "united_kingdom", 
        "venezuelan", "vietnamese", "yugoslavian"
    ]
    
    @classmethod
    def load_name_list(cls, nationality):
        """
        Load a name list file for a specific nationality if it exists.
        
        Args:
            nationality (str): The nationality to load
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        if nationality in cls.name_lists:
            return True
            
        file_path = os.path.join(NAME_DATA_PATH, f"{nationality}.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cls.name_lists[nationality] = json.load(f)
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False
    
    @classmethod
    def get_available_nationalities(cls):
        """Return a list of nationalities that actually have data files"""
        available = []
        for nationality in cls.available_nationalities:
            if cls.load_name_list(nationality):
                available.append(nationality)
        return available
    
    @classmethod
    def generate_name(cls, first_nationality=None, gender=None, last_nationality=None):
        """
        Generate a random name of a specific nationality or mixed nationalities.
        
        Args:
            first_nationality (str, optional): Specific nationality for the first name. 
                                              If None, one is randomly chosen.
            gender (str, optional): "male", "female", or None for random
            last_nationality (str, optional): Specific nationality for the last name.
                                             If None, uses the same as first name.
        
        Returns:
            tuple: (first_name, last_name, first_name_nationality, last_name_nationality)
        """
        # Check if we have any available nationalities with data files
        available_nationalities = cls.get_available_nationalities()
        if not available_nationalities:
            return None, None, None, None
            
        # If no nationality specified, choose one randomly
        if not first_nationality:
            first_nationality = random.choice(available_nationalities)
        
        # Normalize nationality string
        first_nationality = first_nationality.lower().replace(" ", "_")
        
        # Check if it's a valid nationality
        if first_nationality not in cls.available_nationalities:
            return None, None, None, None
        
        # Load name list if not already loaded
        if not cls.load_name_list(first_nationality):
            # If can't load specified nationality, choose a random one
            if available_nationalities:
                first_nationality = random.choice(available_nationalities)
                cls.load_name_list(first_nationality)
            else:
                return None, None, None, None
        
        # Determine last name nationality
        if last_nationality:
            last_nationality = last_nationality.lower().replace(" ", "_")
            if last_nationality not in cls.available_nationalities:
                last_nationality = first_nationality
            
            # Load last name nationality data
            if not cls.load_name_list(last_nationality):
                # If can't load specified nationality, use first name nationality
                last_nationality = first_nationality
        else:
            last_nationality = first_nationality
        
        # Determine gender if not specified
        if not gender:
            gender = random.choice(["male", "female"])
        
        # Get name data
        first_name_data = cls.name_lists[first_nationality]
        last_name_data = cls.name_lists[last_nationality]
        
        # Get first name based on gender
        if gender == "male" and "male_first" in first_name_data:
            first_name = random.choice(first_name_data["male_first"])
        elif gender == "female" and "female_first" in first_name_data:
            first_name = random.choice(first_name_data["female_first"])
        elif "first_names" in first_name_data:
            # Fallback to generic first names
            first_name = random.choice(first_name_data["first_names"])
        else:
            first_name = "Unknown"
        
        # Get last name
        if "last_names" in last_name_data:
            last_name = random.choice(last_name_data["last_names"])
        else:
            last_name = ""
        
        return first_name, last_name, first_nationality, last_nationality

    @classmethod
    def format_name(cls, first_name, last_name):
        """Format the full name properly"""
        if last_name:
            return f"{first_name} {last_name}"
        return first_name
    
    @classmethod
    def list_nationalities(cls):
        """Return a formatted list of available nationalities"""
        available = cls.get_available_nationalities()
        if not available:
            return "No nationality data files found"
        return ", ".join(nat.replace("_", " ").title() for nat in available)


class CmdNPC(default_cmds.MuxCommand):
    """
    Manage NPCs in a scene, including health, dice rolls, and name generation.
    See 'help init' for more information on initiative.

    Usage:
      +npc/roll <name>=<dice pool>/<difficulty>  - Roll dice for an NPC (difficulty defaults to 6)
      +npc/hurt <name>=<type>/<amount>          - Damage an NPC (type: bashing/lethal/aggravated)
      +npc/heal <name>=<type>/<amount>          - Heal an NPC's damage
      +npc/health <name>                        - View NPC's current health levels
      +npc/list                                 - List all NPCs in the scene
      +npc/name [nationality] [nationality2] [gender]  - Generate a random name
      +npc/name <name>=<nationality> [nationality2] [gender]   - Rename an NPC with random name
      +npc/nationalities                        - List available nationalities for names

    Examples:
      +npc/roll Guard=5/6              - Roll 5 dice for the Guard with difficulty 6
      +npc/roll Guard=5                - Roll 5 dice for the Guard (default difficulty 6)
      +npc/hurt Guard=bashing/2        - Apply 2 bashing damage to Guard
      +npc/heal Guard=bashing/1        - Heal 1 bashing damage from Guard
      +npc/health Guard                - Show Guard's current health levels
      +npc/name                        - Generate a random name from any nationality
      +npc/name russian male           - Generate a Russian male name
      +npc/name russian japanese male  - Generate a Russian first name with Japanese last name
      +npc/name russian/japanese       - Generate a Russian first name with Japanese last name
      +npc/name female                 - Generate a random female name from any nationality
      +npc/name Guard=japanese         - Rename "Guard" with a random Japanese name
    """

    key = "+npc"
    locks = "cmd:all()"
    help_category = "RP Commands"

    def func(self):
        if not self.caller.location:
            self.caller.msg("You must be in a location to use this command.")
            return

        if not self.switches:
            self.caller.msg("You must specify a switch. See help +npc for usage.")
            return

        if "list" in self.switches:
            self.list_npcs()
            return
            
        if "nationalities" in self.switches:
            self.caller.msg(f"Available nationalities: {NameGenerator.list_nationalities()}")
            return

        if "name" in self.switches:
            # Handle name generation
            self.generate_name()
            return

        if not self.args:
            self.caller.msg("You must specify an NPC name and parameters. See help +npc for usage.")
            return

        # Parse name and parameters
        if "=" in self.args:
            name, params = self.args.split("=", 1)
            name = name.strip()
            params = params.strip()
        else:
            name = self.args.strip()
            params = None

        # Check if NPC exists
        if not hasattr(self.caller.location, "db_npcs") or name not in self.caller.location.db_npcs:
            self.caller.msg(f"No NPC named '{name}' found in this scene.")
            return

        # Handle different switches
        if "roll" in self.switches:
            self.roll_for_npc(name, params)
        elif "hurt" in self.switches:
            self.hurt_npc(name, params)
        elif "heal" in self.switches:
            self.heal_npc(name, params)
        elif "health" in self.switches:
            self.show_health(name)

    def parse_name_args(self, args_string):
        """
        Parse arguments for name generation: nationality, second nationality, and gender.
        Handles multiple formats including space-separated and slash-separated nationalities.
        
        Returns:
            tuple: (first_nationality, gender, second_nationality)
        """
        first_nat = None
        second_nat = None
        gender = None
        
        # Check for slash-separated nationalities (american/japanese)
        if "/" in args_string and " " not in args_string.split("/")[0] and " " not in args_string.split("/")[1]:
            parts = args_string.split("/", 1)
            first_nat = parts[0].strip()
            
            # Check if second part contains a gender
            second_parts = parts[1].strip().split()
            second_nat = second_parts[0]
            
            if len(second_parts) > 1 and second_parts[1].lower() in ["male", "female"]:
                gender = second_parts[1].lower()
            
            return first_nat, gender, second_nat
        
        # Handle space-separated arguments
        args = args_string.strip().split()
        
        # Check if the only argument is a gender
        if len(args) == 1 and args[0].lower() in ["male", "female"]:
            gender = args[0].lower()
            return None, gender, None
        
        # Process normal arguments
        if args:
            first_nat = args[0]
            
        if len(args) >= 2:
            # Check if second arg is gender or nationality
            if args[1].lower() in ["male", "female"]:
                gender = args[1].lower()
            else:
                second_nat = args[1]
                
            if len(args) >= 3 and args[2].lower() in ["male", "female"]:
                gender = args[2].lower()
                
        return first_nat, gender, second_nat

    def generate_name(self):
        """Generate a random name with optional nationality and gender."""
        if not self.args:
            # Just generate a random name
            first_name, last_name, first_nat, last_nat = NameGenerator.generate_name()
            if first_name:
                full_name = NameGenerator.format_name(first_name, last_name)
                nationality_display = first_nat.replace("_", " ").title()
                self.caller.msg(f"Generated name: |w{full_name}|n ({nationality_display})")
            else:
                self.caller.msg("Error: Could not generate name. Name data files not found.")
            return
            
        # Check if this is a rename command (name=nationality)
        if "=" in self.args:
            npc_name, params = self.args.split("=", 1)
            npc_name = npc_name.strip()
            
            # Check if NPC exists
            if not hasattr(self.caller.location, "db_npcs") or npc_name not in self.caller.location.db_npcs:
                self.caller.msg(f"No NPC named '{npc_name}' found in this scene.")
                return
                
            # Parse name parameters
            first_nat, gender, second_nat = self.parse_name_args(params)
            
            # Generate new name
            first_name, last_name, first_nat_used, last_nat_used = NameGenerator.generate_name(
                first_nat, gender, second_nat
            )
            
            if not first_name:
                self.caller.msg(f"Error: Could not generate name with the specified parameters.")
                return
                
            # Update NPC name
            new_full_name = NameGenerator.format_name(first_name, last_name)
            old_name = npc_name
            
            # Create a new entry with the generated name and copy the old data
            npc_data = self.caller.location.db_npcs[old_name].copy()
            del self.caller.location.db_npcs[old_name]
            self.caller.location.db_npcs[new_full_name] = npc_data
            
            # Inform about the name change
            first_nat_display = first_nat_used.replace("_", " ").title()
            if first_nat_used != last_nat_used:
                last_nat_display = last_nat_used.replace("_", " ").title()
                self.caller.location.msg_contents(
                    f"NPC |w{old_name}|n is now known as |w{new_full_name}|n ({first_nat_display}/{last_nat_display})."
                )
            else:
                self.caller.location.msg_contents(
                    f"NPC |w{old_name}|n is now known as |w{new_full_name}|n ({first_nat_display})."
                )
            return
            
        # Otherwise, just generate a name with specified parameters
        first_nat, gender, second_nat = self.parse_name_args(self.args)
        
        # Generate the name
        first_name, last_name, first_nat_used, last_nat_used = NameGenerator.generate_name(
            first_nat, gender, second_nat
        )
        
        if first_name:
            full_name = NameGenerator.format_name(first_name, last_name)
            first_nat_display = first_nat_used.replace("_", " ").title()
            
            if first_nat_used != last_nat_used:
                last_nat_display = last_nat_used.replace("_", " ").title()
                self.caller.msg(f"Generated name: |w{full_name}|n ({first_nat_display}/{last_nat_display})")
            else:
                self.caller.msg(f"Generated name: |w{full_name}|n ({first_nat_display})")
        else:
            if first_nat or second_nat:
                self.caller.msg(f"Error: Could not generate name with the specified parameters.")
            else:
                self.caller.msg("Error: Could not generate name. Name data files not found.")

    def list_npcs(self):
        """List all NPCs in the scene."""
        if not hasattr(self.caller.location, "db_npcs") or not self.caller.location.db_npcs:
            self.caller.msg("No NPCs in this scene.")
            return

        result = ["|wNPCs in Scene:|n"]
        for name, data in self.caller.location.db_npcs.items():
            health = data["health"]
            health_status = self.get_health_status(health)
            result.append(f"- |w{name}|n (Health: {health_status})")

        self.caller.msg("\n".join(result))

    def roll_for_npc(self, name, params):
        """Roll dice for an NPC."""
        if not params:
            self.caller.msg("Usage: +npc/roll <name>=<dice pool>[/<difficulty>]")
            return

        # Parse dice pool and difficulty
        if "/" in params:
            dice_str, diff_str = params.split("/", 1)
            try:
                difficulty = int(diff_str)
                if difficulty < 2 or difficulty > 10:
                    self.caller.msg("Difficulty must be between 2 and 10.")
                    return
            except ValueError:
                self.caller.msg("Difficulty must be a number between 2 and 10.")
                return
        else:
            dice_str = params
            difficulty = 6  # Default difficulty

        try:
            dice = int(dice_str)
            if dice < 1:
                raise ValueError
        except ValueError:
            self.caller.msg("The number of dice must be a positive integer.")
            return

        # Perform the roll
        rolls, successes, ones = roll_dice(dice, difficulty)
        
        # Interpret the results
        result = interpret_roll_results(successes, ones, rolls=rolls, diff=difficulty)
        
        # Format the outputs
        roll_str = ", ".join(str(r) for r in rolls)
        public_output = f"|rRoll>|n |w{name}|n |yrolls {dice} dice vs {difficulty} |r=>|n {result}"
        builder_output = f"|rRoll>|n |w{name}|n |yrolls {dice} dice vs {difficulty} ({roll_str}) |r=>|n {result}"

        # Send outputs - builders see the actual rolls, others just see the result
        for obj in self.caller.location.contents:
            if obj.locks.check_lockstring(obj, "perm(Builder)"):
                obj.msg(builder_output)
            else:
                obj.msg(public_output)

        # Log the roll if the location supports it
        try:
            if hasattr(self.caller.location, 'log_roll'):
                log_description = f"Rolling {dice} dice vs {difficulty}"
                self.caller.location.log_roll(name, log_description, result)
        except Exception as e:
            self.caller.msg("|rWarning: Could not log roll.|n")
            print(f"Roll logging error: {e}")

    def hurt_npc(self, name, damage_str):
        """Apply damage to an NPC."""
        if not damage_str or "/" not in damage_str:
            self.caller.msg("Usage: +npc/hurt <name>=<type>/<amount>")
            return

        damage_type, amount = damage_str.split("/", 1)
        damage_type = damage_type.lower().strip()
        
        try:
            amount = int(amount)
            if amount < 1:
                raise ValueError
        except ValueError:
            self.caller.msg("Damage amount must be a positive integer.")
            return

        if damage_type not in ["bashing", "lethal", "aggravated"]:
            self.caller.msg("Damage type must be bashing, lethal, or aggravated.")
            return

        # Apply damage
        npc = self.caller.location.db_npcs[name]
        npc["health"][damage_type] += amount

        # Update NPC data
        self.caller.location.db_npcs[name] = npc

        # Show result
        health_status = self.get_health_status(npc["health"])
        self.caller.location.msg_contents(
            f"|w{name}|n takes {amount} {damage_type} damage. "
            f"Current health: {health_status}"
        )

    def heal_npc(self, name, heal_str):
        """Heal damage from an NPC."""
        if not heal_str or "/" not in heal_str:
            self.caller.msg("Usage: +npc/heal <name>=<type>/<amount>")
            return

        damage_type, amount = heal_str.split("/", 1)
        damage_type = damage_type.lower().strip()
        
        try:
            amount = int(amount)
            if amount < 1:
                raise ValueError
        except ValueError:
            self.caller.msg("Heal amount must be a positive integer.")
            return

        if damage_type not in ["bashing", "lethal", "aggravated"]:
            self.caller.msg("Damage type must be bashing, lethal, or aggravated.")
            return

        # Apply healing
        npc = self.caller.location.db_npcs[name]
        current = npc["health"][damage_type]
        npc["health"][damage_type] = max(0, current - amount)

        # Update NPC data
        self.caller.location.db_npcs[name] = npc

        # Show result
        health_status = self.get_health_status(npc["health"])
        self.caller.location.msg_contents(
            f"|w{name}|n heals {amount} {damage_type} damage. "
            f"Current health: {health_status}"
        )

    def show_health(self, name):
        """Show an NPC's current health levels."""
        npc = self.caller.location.db_npcs[name]
        health = npc["health"]
        
        result = [f"|wHealth Status for {name}:|n"]
        result.append(f"Bashing: {health['bashing']}")
        result.append(f"Lethal: {health['lethal']}")
        result.append(f"Aggravated: {health['aggravated']}")
        result.append(f"Status: {self.get_health_status(health)}")
        
        self.caller.msg("\n".join(result))

    def get_health_status(self, health):
        """Get a text representation of health status."""
        total_damage = health['bashing'] + health['lethal'] + health['aggravated']
        
        if total_damage == 0:
            return "Healthy"
        elif total_damage <= 1:
            return "Bruised"
        elif total_damage <= 2:
            return "Hurt"
        elif total_damage <= 3:
            return "Injured"
        elif total_damage <= 4:
            return "Wounded"
        elif total_damage <= 5:
            return "Mauled"
        elif total_damage <= 6:
            return "Crippled"
        else:
            return "Incapacitated"
