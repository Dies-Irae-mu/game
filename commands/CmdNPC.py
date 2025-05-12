from evennia import default_cmds
from evennia.utils.ansi import ANSIString
from world.wod20th.utils.dice_rolls import roll_dice, interpret_roll_results
import random
import os
import json
import re

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
        "chechen", "chinese", "czech", "danish", "filipino", "finnish", "french", 
        "german", "greek", "hungarian", "irish", "italian", "jamaican", "japanese", 
        "korean", "latvian", "mexican", "mongolian", "north_indian", "portuguese", 
        "prison", "roma", "russian", "serbian", "spanish", "swedish", "thai", 
        "turkish", "ukrainian", "vietnamese", "yugoslavian", "senegalese", "sicilian", 
        "united_kingdom", "nahuatl", "persian", "polish", 
        "polynesian", "maori", "slovene"
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
      +npc/roll <name or #n>=<dice pool>/<difficulty> - Roll dice for an NPC
                                                         (difficulty defaults to 6)
      +npc/hurt <name or #n>=<type>/<amount>          - Damage an NPC 
                                                        (type: bashing/lethal/aggravated)
      +npc/heal <name or #n>=<type>/<amount>          - Heal an NPC's damage
      +npc/health <name or #n>                        - View NPC's current health levels
      +npc/pose <name or #n>=<pose text>              - Make an NPC pose an action
      +npc/emit <name or #n>=<text>                   - Make an NPC emit text to the room
      +npc/say <name or #n>=<speech>                  - Make an NPC say something
      +npc/inhabit <name or #n>                       - Take control of an NPC (staff only)
      +npc/uninhabit <name or #n>                     - Release control of an NPC (staff only)
      +npc/list                                       - List all NPCs in the scene
      +npc/listall                                    - List all NPCs in the game (staff only)
      +npc/listall/loc                                - Group NPCs by location
      +npc/listall/splat                              - Group NPCs by splat type
      +npc/listall/temp                               - Show only temporary NPCs
      +npc/listall/perm                               - Show only permanent NPCs
      +npc/remove <name or #n>                        - Remove an NPC from the scene (staff only)
      +npc/remove/force <name or #n>                  - Force-remove a stubborn NPC (staff only)
      +npc/create [name] [splat=<type>] [diff=<level>] - Create a permanent NPC (staff only)
      +npc/sheet <name or #n>                         - View an NPC's character sheet
      +npc/name [nationality] [nationality2] [gender] - Generate a random name
      +npc/name <n>=<nationality> [nationality2] [gender]   - Rename an NPC with random name
      +npc/nationalities                        - List available nationalities for names

    Examples:
      +npc/roll Guard=5/6              - Roll 5 dice for the Guard with difficulty 6
      +npc/roll #1=5                   - Roll 5 dice for NPC #1 (default difficulty 6)
      +npc/roll dia=5/7                - Roll 5 dice at difficulty 7 for an NPC
                                         whose name starts with "dia"
      +npc/hurt Guard=bashing/2        - Apply 2 bashing damage to Guard
      +npc/heal #2=bashing/1           - Heal 1 bashing damage from NPC #2
      +npc/health Guard                - Show Guard's current health levels
      +npc/pose Guard=slowly backs away toward the door.   - Make Guard pose
      +npc/emit Guard=A low growl emanates from the Guard. - Make an emit from Guard
      +npc/say Guard=Don't move or I'll shoot!            - Make Guard say something
      +npc/name                        - Generate a random name from any nationality
      +npc/name russian male           - Generate a Russian male name
      +npc/name russian japanese male  - Generate a Russian first name with Japanese last name
      +npc/name russian/japanese       - Generate a Russian first name with Japanese last name
      +npc/name female                 - Generate a random female name from any nationality
      +npc/name Guard=japanese         - Rename "Guard" with a random Japanese name
      +npc/create                      - Create a random mortal NPC with medium difficulty
      +npc/create Sadie splat=mage     - Create a mage NPC named Sadie
      +npc/create splat=vampire diff=high - Create a high-difficulty vampire with random name
      +npc/sheet Guard                 - View Guard's character sheet
      +npc/remove Guard                - Remove Guard from the scene
      +npc/remove/force #1             - Force-remove NPC #1 when normal removal fails
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
            
        if "listall" in self.switches or "global" in self.switches:
            # Check permissions for global listing
            if not (self.caller.check_permstring("Builder") or 
                    self.caller.check_permstring("Admin") or 
                    self.caller.check_permstring("Storyteller")):
                self.caller.msg("You don't have permission to list all NPCs.")
                return
            self.list_all_npcs()
            return
            
        if "nationalities" in self.switches:
            self.caller.msg(f"Available nationalities: {NameGenerator.list_nationalities()}")
            return

        if "name" in self.switches:
            # Handle name generation
            self.generate_name()
            return

        if "remove" in self.switches:
            self.remove_npc(self.args)
            return

        if "create" in self.switches:
            self.create_npc(self.args)
            return

        if "sheet" in self.switches:
            self.view_sheet(self.args)
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
            
        # Resolve NPC name (supports both numerical ID and partial matching)
        resolved_name = self.resolve_npc_name(name)
        if not resolved_name:
            self.caller.msg(f"No NPC matching '{name}' found in this scene.")
            return

        # Handle different switches
        if "roll" in self.switches:
            self.roll_for_npc(resolved_name, params)
        elif "hurt" in self.switches:
            self.hurt_npc(resolved_name, params)
        elif "heal" in self.switches:
            self.heal_npc(resolved_name, params)
        elif "health" in self.switches:
            self.show_health(resolved_name)
        elif "pose" in self.switches:
            self.pose_npc(resolved_name, params)
        elif "emit" in self.switches:
            self.emit_npc(resolved_name, params)
        elif "say" in self.switches:
            self.say_npc(resolved_name, params)
        elif "inhabit" in self.switches:
            self.inhabit_npc(resolved_name)
        elif "uninhabit" in self.switches:
            self.uninhabit_npc(resolved_name)
            
    def resolve_npc_name(self, name):
        """
        Resolve an NPC name from either a numeric ID (#1) or partial name match.
        Returns the full NPC name if found, or None if not found.
        """
        if not hasattr(self.caller.location, "db_npcs") or not self.caller.location.db_npcs:
            return None
            
        # Check if using numeric ID
        if name.startswith("#"):
            try:
                npc_number = int(name[1:])
                for npc_name, data in self.caller.location.db_npcs.items():
                    if data.get("number") == npc_number:
                        return npc_name
                return None
            except ValueError:
                # Not a valid number format
                return None
                
        # Check for exact match
        if name in self.caller.location.db_npcs:
            return name
            
        # Try partial name matching
        matched_npcs = [npc for npc in self.caller.location.db_npcs.keys() 
                      if name.lower() in npc.lower()]
        
        if len(matched_npcs) == 1:
            return matched_npcs[0]
        elif len(matched_npcs) > 1:
            # Multiple matches - return None but inform the user
            self.caller.msg(f"Multiple NPCs match '{name}'. Please be more specific or use #ID: " +
                          ", ".join([f"{npc} (#{self.caller.location.db_npcs[npc].get('number', '?')})" 
                                   for npc in matched_npcs]))
            return None
            
        # No matches found
        return None

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
            
            # Resolve NPC name
            resolved_name = self.resolve_npc_name(npc_name)
            if not resolved_name:
                self.caller.msg(f"No NPC matching '{npc_name}' found in this scene.")
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
            old_name = resolved_name
            
            # Preserve NPC number
            old_number = self.caller.location.db_npcs[old_name].get("number", 0)
            
            # Create a new entry with the generated name and copy the old data
            npc_data = self.caller.location.db_npcs[old_name].copy()
            del self.caller.location.db_npcs[old_name]
            self.caller.location.db_npcs[new_full_name] = npc_data
            
            # Inform about the name change
            first_nat_display = first_nat_used.replace("_", " ").title()
            old_display = f"{old_name} (#{old_number})" if old_number else old_name
            new_display = f"{new_full_name} (#{old_number})" if old_number else new_full_name
            
            if first_nat_used != last_nat_used:
                last_nat_display = last_nat_used.replace("_", " ").title()
                self.caller.location.msg_contents(
                    f"NPC |w{old_display}|n is now known as |w{new_display}|n ({first_nat_display}/{last_nat_display})."
                )
            else:
                self.caller.location.msg_contents(
                    f"NPC |w{old_display}|n is now known as |w{new_display}|n ({first_nat_display})."
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
            npc_number = data.get("number", "")
            
            if npc_number:
                result.append(f"- |w{name}|n (#{npc_number}) - Health: {health_status}")
            else:
                result.append(f"- |w{name}|n - Health: {health_status}")

        self.caller.msg("\n".join(result))

    def roll_for_npc(self, name, params):
        """Roll dice for an NPC."""
        if not params:
            self.caller.msg("Usage: +npc/roll <name or #n>=<dice pool>[/<difficulty>]")
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

        # Get NPC number for display
        npc_number = self.caller.location.db_npcs[name].get("number", "")
        npc_display = f"{name} (#{npc_number})" if npc_number else name

        # Perform the roll
        rolls, successes, ones = roll_dice(dice, difficulty)
        
        # Interpret the results
        result = interpret_roll_results(successes, ones, rolls=rolls, diff=difficulty)
        
        # Format the outputs
        roll_str = ", ".join(str(r) for r in rolls)
        public_output = f"|rRoll>|n |w{npc_display}|n |yrolls {dice} dice vs {difficulty} |r=>|n {result}"
        builder_output = f"|rRoll>|n |w{npc_display}|n |yrolls {dice} dice vs {difficulty} ({roll_str}) |r=>|n {result}"

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
        if not damage_str:
            self.caller.msg("Usage: +npc/hurt <name or #n>=<type>/<amount>")
            return

        # Parse damage info
        if "/" in damage_str:
            damage_type, amount_str = damage_str.split("/", 1)
            damage_type = damage_type.lower().strip()
            
            # Validate damage type
            if damage_type not in ["bashing", "lethal", "aggravated"]:
                self.caller.msg("Damage type must be one of: bashing, lethal, aggravated")
                return
                
            try:
                amount = int(amount_str.strip())
                if amount < 1:
                    raise ValueError
            except ValueError:
                self.caller.msg("Damage amount must be a positive integer.")
                return
        else:
            self.caller.msg("Usage: +npc/hurt <name or #n>=<type>/<amount>")
            return

        # Apply damage to the NPC
        health = self.caller.location.db_npcs[name]["health"]
        health[damage_type] += amount
        self.caller.location.db_npcs[name]["health"] = health

        # Get updated health status
        health_status = self.get_health_status(health)
        
        # Get NPC number for display
        npc_number = self.caller.location.db_npcs[name].get("number", "")
        npc_display = f"{name} (#{npc_number})" if npc_number else name

        # Inform about damage
        self.caller.location.msg_contents(
            f"|w{npc_display}|n takes {amount} {damage_type} damage and is now {health_status}."
        )

        # Check if the NPC should be deleted (incapacitated)
        if health_status == "Incapacitated" and self.caller.location.db_npcs[name].get("is_temporary", False):
            # Schedule NPC for removal after a delay
            import time
            from evennia.utils.utils import delay
            delay(60, self.remove_incapacitated_npc, name)

    def remove_incapacitated_npc(self, name):
        """Remove an incapacitated NPC from the scene."""
        # Check if the NPC still exists
        if not hasattr(self.caller.location, "db_npcs") or name not in self.caller.location.db_npcs:
            return
            
        # Check if still incapacitated
        health = self.caller.location.db_npcs[name]["health"]
        health_status = self.get_health_status(health)
        
        if health_status == "Incapacitated":
            # Inform about departure
            self.caller.location.msg_contents(
                f"|w{name}|n has been incapacitated and is removed from the scene."
            )
            
            # Remove from NPC list
            del self.caller.location.db_npcs[name]
            
            # If using initiative, also remove from initiative
            if hasattr(self.caller.location, "db_initiative") and self.caller.location.db_initiative:
                # Remove from initiative order
                initiative_order = self.caller.location.db_initiative.get("order", [])
                new_order = [char for char in initiative_order if char != name]
                self.caller.location.db_initiative["order"] = new_order

    def heal_npc(self, name, heal_str):
        """Heal damage from an NPC."""
        if not heal_str:
            self.caller.msg("Usage: +npc/heal <name or #n>=<type>/<amount>")
            return

        # Parse healing info
        if "/" in heal_str:
            damage_type, amount_str = heal_str.split("/", 1)
            damage_type = damage_type.lower().strip()
            
            # Validate damage type
            if damage_type not in ["bashing", "lethal", "aggravated"]:
                self.caller.msg("Damage type must be one of: bashing, lethal, aggravated")
                return
                
            try:
                amount = int(amount_str.strip())
                if amount < 1:
                    raise ValueError
            except ValueError:
                self.caller.msg("Healing amount must be a positive integer.")
                return
        else:
            self.caller.msg("Usage: +npc/heal <name or #n>=<type>/<amount>")
            return

        # Apply healing to the NPC
        health = self.caller.location.db_npcs[name]["health"]
        health[damage_type] = max(0, health[damage_type] - amount)
        self.caller.location.db_npcs[name]["health"] = health

        # Get updated health status
        health_status = self.get_health_status(health)
        
        # Get NPC number for display
        npc_number = self.caller.location.db_npcs[name].get("number", "")
        npc_display = f"{name} (#{npc_number})" if npc_number else name

        # Inform about healing
        self.caller.location.msg_contents(
            f"|w{npc_display}|n heals {amount} {damage_type} damage and is now {health_status}."
        )

    def show_health(self, name):
        """Show an NPC's health status."""
        health = self.caller.location.db_npcs[name]["health"]
        health_status = self.get_health_status(health)
        
        # Format the health display
        bashing = health["bashing"]
        lethal = health["lethal"]
        aggravated = health["aggravated"]
        
        # Get NPC number for display
        npc_number = self.caller.location.db_npcs[name].get("number", "")
        npc_display = f"{name} (#{npc_number})" if npc_number else name
        
        self.caller.msg(f"|w{npc_display}|n Health Status: {health_status}")
        self.caller.msg(f"Bashing: {bashing}, Lethal: {lethal}, Aggravated: {aggravated}")

    def get_health_status(self, health):
        """Calculate health status from damage levels."""
        total_damage = health["bashing"] + health["lethal"] + health["aggravated"]
        
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

    def pose_npc(self, name, pose_text):
        """Make an NPC pose an action."""
        if not pose_text:
            self.caller.msg("Usage: +npc/pose <name or #n>=<pose text>")
            return
            
        # Get NPC number for display
        npc_number = self.caller.location.db_npcs[name].get("number", "")
        npc_display = f"{name} (#{npc_number})" if npc_number else name
        
        # Check if this NPC can be controlled by the caller
        if not self.can_control_npc(name):
            self.caller.msg(f"You don't have permission to control {npc_display}.")
            return
            
        # Format the pose message
        if pose_text.startswith("'") or pose_text.startswith(":"):
            pose_text = pose_text[1:]
            
        # Clean up pose text
        pose_text = pose_text.strip()
        
        # Check if NPC's name is already in the pose text
        npc_name_variants = [name.lower(), name.title(), name.upper()]
        if not any(variant in pose_text.lower() for variant in npc_name_variants):
            # If name isn't already there, prepend it with a space
            pose_msg = f"{name} {pose_text}"
        else:
            pose_msg = pose_text
            
        # Send the pose to the room
        self.caller.location.msg_contents(pose_msg)
        
        # Log the action if the location supports it
        try:
            if hasattr(self.caller.location, 'log_pose'):
                self.caller.location.log_pose(name, pose_msg)
        except Exception as e:
            self.caller.msg("|rWarning: Could not log pose.|n")
            print(f"Pose logging error: {e}")

    def emit_npc(self, name, emit_text):
        """Make an NPC emit text to the room."""
        if not emit_text:
            self.caller.msg("Usage: +npc/emit <name or #n>=<text>")
            return
            
        # Get NPC number for display
        npc_number = self.caller.location.db_npcs[name].get("number", "")
        npc_display = f"{name} (#{npc_number})" if npc_number else name
        
        # Check if this NPC can be controlled by the caller
        if not self.can_control_npc(name):
            self.caller.msg(f"You don't have permission to control {npc_display}.")
            return
            
        # Send the emit to the room
        self.caller.location.msg_contents(emit_text)
        
        # Log the emit if the location supports it
        try:
            if hasattr(self.caller.location, 'log_emit'):
                self.caller.location.log_emit(f"NPC:{name}", emit_text)
        except Exception as e:
            self.caller.msg("|rWarning: Could not log emit.|n")
            print(f"Emit logging error: {e}")

    def say_npc(self, name, speech):
        """Make an NPC say something."""
        if not speech:
            self.caller.msg("Usage: +npc/say <name or #n>=<speech>")
            return
            
        # Get NPC number for display
        npc_number = self.caller.location.db_npcs[name].get("number", "")
        npc_display = f"{name} (#{npc_number})" if npc_number else name
        
        # Check if this NPC can be controlled by the caller
        if not self.can_control_npc(name):
            self.caller.msg(f"You don't have permission to control {npc_display}.")
            return
            
        # Check if there's a language marker
        language = None
        if ":" in speech and speech.split(":", 1)[0].lower() in ["english", "spanish", "japanese", "chinese", "french", "italian"]:
            lang_name, speech_text = speech.split(":", 1)
            language = lang_name.strip()
            speech = speech_text.strip()
        
        # Format the speech message
        if language:
            speech_msg = f"{name} says in {language}, \"{speech}\""
        else:
            speech_msg = f"{name} says, \"{speech}\""
            
        # Send the speech to the room
        self.caller.location.msg_contents(speech_msg)
        
        # Log the speech if the location supports it
        try:
            if hasattr(self.caller.location, 'log_say'):
                self.caller.location.log_say(name, speech)
        except Exception as e:
            self.caller.msg("|rWarning: Could not log speech.|n")
            print(f"Speech logging error: {e}")

    def inhabit_npc(self, name):
        """Allow staff or player storytellers to take control of an NPC."""
        # Check permissions
        if not (self.caller.check_permstring("Builder") or 
                self.caller.check_permstring("Admin") or 
                self.caller.check_permstring("Storyteller")):
            self.caller.msg("You don't have permission to inhabit NPCs.")
            return
            
        # Get the NPC's data
        npc_data = self.caller.location.db_npcs.get(name)
        if not npc_data:
            self.caller.msg(f"Could not find NPC '{name}' in this room.")
            return
            
        # Check if already inhabited
        if npc_data.get("inhabited_by") and npc_data["inhabited_by"] != self.caller.key:
            self.caller.msg(f"{name} is already being controlled by {npc_data['inhabited_by']}.")
            return
            
        # Set the character as the controller
        npc_data["inhabited_by"] = self.caller.key
        self.caller.location.db_npcs[name] = npc_data
        
        # Get NPC number for display
        npc_number = npc_data.get("number", "")
        npc_display = f"{name} (#{npc_number})" if npc_number else name
        
        self.caller.msg(f"You are now controlling {npc_display}. Use +npc/pose, +npc/emit, +npc/say to act as them.")
        self.caller.msg(f"Use +npc/uninhabit {name} when you're done.")

    def uninhabit_npc(self, name):
        """Release control of an NPC."""
        # Get the NPC's data
        npc_data = self.caller.location.db_npcs.get(name)
        if not npc_data:
            self.caller.msg(f"Could not find NPC '{name}' in this room.")
            return
            
        # Check if being controlled by this character
        if npc_data.get("inhabited_by") != self.caller.key:
            # Staff can release any NPC
            if not (self.caller.check_permstring("Builder") or 
                    self.caller.check_permstring("Admin")):
                self.caller.msg(f"You are not currently controlling {name}.")
                return
                
        # Release control
        npc_data["inhabited_by"] = None
        self.caller.location.db_npcs[name] = npc_data
        
        # Get NPC number for display
        npc_number = npc_data.get("number", "")
        npc_display = f"{name} (#{npc_number})" if npc_number else name
        
        self.caller.msg(f"You are no longer controlling {npc_display}.")

    def can_control_npc(self, name):
        """Check if the caller can control a specific NPC."""
        # Staff can control any NPC
        if (self.caller.check_permstring("Builder") or 
            self.caller.check_permstring("Admin") or 
            self.caller.check_permstring("Storyteller")):
            return True
            
        # Get NPC data
        npc_data = self.caller.location.db_npcs.get(name)
        if not npc_data:
            return False
            
        # Check if inhabited
        if npc_data.get("inhabited_by") == self.caller.key:
            return True
            
        # Check if a temporary NPC created by this player
        if npc_data.get("is_temporary", False) and npc_data.get("creator") == self.caller.key:
            return True
            
        return False

    def remove_npc(self, name):
        """Remove an NPC from the scene."""
        # Check permissions
        if not (self.caller.check_permstring("Builder") or 
                self.caller.check_permstring("Admin") or 
                self.caller.check_permstring("Storyteller")):
            self.caller.msg("You don't have permission to remove NPCs.")
            return
            
        # Check for force switch
        force_mode = "force" in self.switches
        
        # Resolve NPC name
        resolved_name = self.resolve_npc_name(name)
        if not resolved_name:
            self.caller.msg(f"No NPC matching '{name}' found in this scene.")
            return
            
        # Get the NPC object
        npc_data = self.caller.location.db_npcs.get(resolved_name, {})
        npc_object = npc_data.get("npc_object")
        
        if not npc_object:
            self.caller.msg(f"Could not find NPC object for '{resolved_name}'.")
            # Try to clean up the reference at least
            if resolved_name in self.caller.location.db_npcs:
                del self.caller.location.db_npcs[resolved_name]
            return
            
        # First clean up the reference in the room
        if resolved_name in self.caller.location.db_npcs:
            del self.caller.location.db_npcs[resolved_name]
        
        # Get NPC info for reporting
        npc_id = npc_object.id
        npc_dbref = npc_object.dbref
        
        # Now try to delete the NPC object with increasing aggressiveness
        try:
            self.caller.msg(f"Attempting to delete NPC '{resolved_name}' (#{npc_id})...")
            
            if force_mode:
                self.caller.msg("Using force mode for deletion...")
                
                # Try force cleanup first
                try:
                    # Clear all attributes
                    for attr in list(npc_object.attributes.all()):
                        try:
                            npc_object.attributes.remove(attr.key)
                        except Exception as e:
                            self.caller.msg(f"Error removing attribute {attr.key}: {e}")
                    
                    # Clear all tags
                    for tag in list(npc_object.tags.all()):
                        try:
                            npc_object.tags.remove(tag.key, tag.category)
                        except Exception as e:
                            self.caller.msg(f"Error removing tag {tag.key}: {e}")
                    
                    # Clear all command sets
                    try:
                        npc_object.cmdset.clear()
                        npc_object.cmdset.remove_default()
                    except Exception as e:
                        self.caller.msg(f"Error clearing command sets: {e}")
                    
                    # Remove from any locations
                    try:
                        old_location = npc_object.location
                        npc_object.location = None
                        if old_location and hasattr(old_location, 'msg'):
                            old_location.msg_contents(f"{npc_object.name} vanishes.")
                    except Exception as e:
                        self.caller.msg(f"Error removing from location: {e}")
                        
                    # Explicitly unregister from all rooms
                    if hasattr(npc_object, 'db'):
                        try:
                            registered_rooms = list(npc_object.db.registered_in_rooms) if hasattr(npc_object.db, 'registered_in_rooms') else []
                            for room_dbref in registered_rooms:
                                try:
                                    from evennia.utils.search import search_object
                                    room = search_object(room_dbref)
                                    if room and len(room) > 0:
                                        room = room[0]
                                        if hasattr(room, 'db_npcs') and npc_object.key in room.db_npcs:
                                            del room.db_npcs[npc_object.key]
                                except Exception as e:
                                    self.caller.msg(f"Error unregistering from room {room_dbref}: {e}")
                            
                            # Clear the registered rooms
                            npc_object.attributes.remove('registered_in_rooms')
                        except Exception as e:
                            self.caller.msg(f"Error handling registered rooms: {e}")
                except Exception as e:
                    self.caller.msg(f"Error during force cleanup: {e}")
                
                # Now try a real force delete
                success = npc_object.delete(force=True)
            else:
                # Normal deletion
                success = npc_object.delete()
            
            if success:
                self.caller.msg(f"NPC |w{resolved_name}|n (#{npc_id}) has been removed.")
                return True
            else:
                self.caller.msg(f"Failed to delete NPC {resolved_name}. Try using +npc/remove/force.")
                
                # Try database-level deletion in force mode
                if force_mode:
                    self.caller.msg("Attempting direct database deletion...")
                    try:
                        from django.apps import apps
                        ObjectDB = apps.get_model('objects', 'ObjectDB')
                        count, _ = ObjectDB.objects.filter(id=npc_id).delete()
                        if count > 0:
                            self.caller.msg(f"Successfully deleted NPC from database directly. Removed {count} records.")
                            return True
                        else:
                            self.caller.msg(f"Database deletion reported no records removed. This may indicate the NPC was already deleted at the database level.")
                    except Exception as e:
                        self.caller.msg(f"Database-level deletion failed: {e}")
                        import traceback
                        traceback.print_exc()
                        
                return False
                
        except Exception as e:
            self.caller.msg(f"Error deleting NPC: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def create_npc(self, args):
        """Create a permanent NPC."""
        # Check permissions
        if not (self.caller.check_permstring("Builder") or 
                self.caller.check_permstring("Admin") or
                self.caller.check_permstring("Storyteller")):
            self.caller.msg("You don't have permission to create permanent NPCs.")
            return
            
        # Parse arguments
        splat_type = "mortal"  # Default splat type
        difficulty = "MEDIUM"  # Default difficulty
        name = None  
        
        # Check for named parameters in format splat=value or diff=value
        splat_match = re.search(r'splat=(\w+)', args, re.IGNORECASE)
        if splat_match:
            splat_type = splat_match.group(1).lower()
            # Remove the splat parameter from args
            args = args.replace(splat_match.group(0), "").strip()
            
        diff_match = re.search(r'diff=(\w+)', args, re.IGNORECASE)
        if diff_match:
            diff_value = diff_match.group(1).lower()
            if diff_value in ["low", "l"]:
                difficulty = "LOW"
            elif diff_value in ["med", "medium", "m"]:
                difficulty = "MEDIUM"
            elif diff_value in ["high", "h"]:
                difficulty = "HIGH"
            # Remove the diff parameter from args
            args = args.replace(diff_match.group(0), "").strip()
        
        # Any remaining text is the name
        name = args.strip()
        
        # If no name provided, generate a random one
        if not name:
            first_name, last_name, _, _ = NameGenerator.generate_name()
            if first_name and last_name:
                name = f"{first_name} {last_name}"
            else:
                # Fallback if name generation fails
                name = f"NPC_{random.randint(1000, 9999)}"
        
        # Validate splat type
        valid_splats = ["mortal", "vampire", "mage", "shifter", "changeling", 
                        "hunter", "demon", "psychic", "mummy", "spirit", 
                        "mortal+", "wraith"]
        if splat_type not in valid_splats:
            self.caller.msg(f"Invalid splat type '{splat_type}'. Using 'mortal' instead.")
            splat_type = "mortal"
            
        try:
            # Import the NPC class
            from typeclasses.npcs import NPC
            
            # Create the NPC
            self.caller.msg(f"Creating NPC: {name} ({splat_type}, {difficulty})")
            
            # Create the NPC object in the caller's location
            npc = NPC.create(
                key=name,
                location=self.caller.location,
                attributes=[
                    ("desc", f"A {splat_type} NPC."),
                ],
            )
            
            # Initialize the NPC with the specified splat and difficulty
            npc.initialize_npc_stats(splat_type, difficulty)
            
            # Set as permanent NPC and set creator
            npc.db.is_temporary = False
            npc.db.creator = self.caller
            
            # Register the NPC in the current room
            npc.register_in_room(self.caller.location)
            
            self.caller.msg(f"Created permanent NPC |w{name}|n (Splat: {splat_type}, Difficulty: {difficulty})")
            
            # Announce to the room
            self.caller.location.msg_contents(
                f"{self.caller.name} has created NPC |w{name}|n.",
                exclude=[self.caller]
            )
            
        except Exception as e:
            self.caller.msg(f"Error creating NPC: {str(e)}")
            import traceback
            traceback.print_exc()

    def view_sheet(self, name):
        """View an NPC's character sheet."""
        if not name:
            self.caller.msg("Usage: +npc/sheet <name or #n>")
            return
            
        # Resolve NPC name
        resolved_name = self.resolve_npc_name(name)
        if not resolved_name:
            self.caller.msg(f"No NPC matching '{name}' found in this scene.")
            return
            
        # Get NPC object
        npc_data = self.caller.location.db_npcs.get(resolved_name, {})
        npc_object = npc_data.get("npc_object")
        
        if not npc_object:
            self.caller.msg(f"Could not find NPC object for '{resolved_name}'.")
            return
            
        # Check permissions - only creator, staff, and storytellers can view the sheet
        if not (self.caller == npc_data.get("creator") or
                self.caller.check_permstring("Builder") or
                self.caller.check_permstring("Admin") or
                self.caller.check_permstring("Storyteller")):
            self.caller.msg("You don't have permission to view this NPC's sheet.")
            return
            
        # Format and display the character sheet
        try:
            stats = npc_object.db.stats
            
            # Build the sheet
            sheet = [
                f"|c{'=' * 78}|n",
                f"|c{' ' * 30}NPC SHEET: {resolved_name}{' ' * 30}|n",
                f"|c{'=' * 78}|n",
                "",
                f"|wSplat:|n {stats.get('splat', 'Unknown').capitalize()}",
                f"|wDifficulty:|n {stats.get('difficulty', 'MEDIUM')}",
                f"|wCreator:|n {npc_object.db.creator.key if npc_object.db.creator else 'Unknown'}",
                f"|wTemporary:|n {'Yes' if npc_object.db.is_temporary else 'No'}",
                "",
                f"|c{'-' * 78}|n",
                "|wAttributes:|n"
            ]
            
            # Add attributes
            if 'attributes' in stats:
                for category in ['physical', 'social', 'mental']:
                    if category in stats['attributes']:
                        sheet.append(f"  |c{category.capitalize()}:|n")
                        for attr, value in stats['attributes'][category].items():
                            sheet.append(f"    {attr.capitalize()}: {value['perm'] if isinstance(value, dict) else value}")
            
            # Add abilities
            sheet.append("")
            sheet.append(f"|c{'-' * 78}|n")
            sheet.append("|wAbilities:|n")
            
            if 'abilities' in stats:
                for category in ['talents', 'skills', 'knowledges']:
                    if category in stats['abilities']:
                        sheet.append(f"  |c{category.capitalize()}:|n")
                        for ability, value in stats['abilities'][category].items():
                            sheet.append(f"    {ability.capitalize()}: {value['perm'] if isinstance(value, dict) else value}")
            
            # Add powers if any
            if 'powers' in stats:
                sheet.append("")
                sheet.append(f"|c{'-' * 78}|n")
                sheet.append("|wPowers:|n")
                
                for power_type, powers in stats['powers'].items():
                    if powers:
                        sheet.append(f"  |c{power_type.capitalize()}:|n")
                        if isinstance(powers, dict):
                            for power, value in powers.items():
                                sheet.append(f"    {power.capitalize()}: {value['perm'] if isinstance(value, dict) else value}")
                        else:
                            sheet.append(f"    {', '.join(powers)}")
            
            # Add health info
            sheet.append("")
            sheet.append(f"|c{'-' * 78}|n")
            sheet.append("|wHealth:|n")
            health_status = npc_object.get_health_status()
            health = stats.get("health", {"bashing": 0, "lethal": 0, "aggravated": 0})
            sheet.append(f"  Status: {health_status}")
            sheet.append(f"  Bashing: {health['bashing']}")
            sheet.append(f"  Lethal: {health['lethal']}")
            sheet.append(f"  Aggravated: {health['aggravated']}")
            
            # Send the formatted sheet to the caller
            self.caller.msg("\n".join(sheet))
            
        except Exception as e:
            self.caller.msg(f"Error displaying NPC sheet: {str(e)}")
            import traceback
            traceback.print_exc()

    def list_all_npcs(self):
        """List all NPCs in the game (staff only)"""
        from evennia.utils.search import search_object
        from evennia.utils import evtable
        
        # Search for all NPC objects
        npcs = search_object(None, typeclass="typeclasses.npcs.NPC")
        
        if not npcs:
            self.caller.msg("No NPCs found in the game.")
            return
            
        # Process switches for display options
        by_location = "loc" in self.switches
        by_splat = "splat" in self.switches
        only_temp = "temp" in self.switches
        only_perm = "perm" in self.switches
        
        # Filter by temporary/permanent status if needed
        if only_temp:
            npcs = [npc for npc in npcs if npc.db.is_temporary]
        elif only_perm:
            npcs = [npc for npc in npcs if not npc.db.is_temporary]
            
        # Create table
        if by_location:
            # Group by location
            locations = {}
            for npc in npcs:
                loc = npc.location
                loc_name = loc.key if loc else "No Location"
                
                if loc_name not in locations:
                    locations[loc_name] = []
                locations[loc_name].append(npc)
                
            # Display by location
            table = evtable.EvTable(
                "|wLocation|n",
                "|wNPC|n",
                "|wSplat|n",
                "|wCreator|n",
                "|wTemp?|n",
                border="table",
                width=78
            )
            
            for loc_name, loc_npcs in sorted(locations.items()):
                for i, npc in enumerate(loc_npcs):
                    splat = npc.db.stats.get('splat', 'Unknown') if hasattr(npc.db, 'stats') else 'Unknown'
                    creator = npc.db.creator.key if npc.db.creator else "Unknown"
                    temp = "Yes" if npc.db.is_temporary else "No"
                    
                    # Only show location name in first row of each location group
                    if i == 0:
                        table.add_row(loc_name, npc.key, splat, creator, temp)
                    else:
                        table.add_row("", npc.key, splat, creator, temp)
                
                # Add separator between locations
                if loc_name != list(sorted(locations.keys()))[-1]:
                    table.add_row("-", "-", "-", "-", "-")
                    
        elif by_splat:
            # Group by splat type
            splats = {}
            for npc in npcs:
                splat = npc.db.stats.get('splat', 'Unknown') if hasattr(npc.db, 'stats') else 'Unknown'
                
                if splat not in splats:
                    splats[splat] = []
                splats[splat].append(npc)
                
            # Display by splat
            table = evtable.EvTable(
                "|wSplat|n",
                "|wNPC|n", 
                "|wLocation|n",
                "|wCreator|n",
                "|wTemp?|n",
                border="table",
                width=78
            )
            
            for splat_name, splat_npcs in sorted(splats.items()):
                for i, npc in enumerate(splat_npcs):
                    loc = npc.location.key if npc.location else "No Location"
                    creator = npc.db.creator.key if npc.db.creator else "Unknown"
                    temp = "Yes" if npc.db.is_temporary else "No"
                    
                    # Only show splat name in first row of each splat group
                    if i == 0:
                        table.add_row(splat_name.capitalize(), npc.key, loc, creator, temp)
                    else:
                        table.add_row("", npc.key, loc, creator, temp)
                
                # Add separator between splats
                if splat_name != list(sorted(splats.keys()))[-1]:
                    table.add_row("-", "-", "-", "-", "-")
                    
        else:
            # Default view: flat list
            table = evtable.EvTable(
                "|wNPC|n", 
                "|wLocation|n",
                "|wSplat|n",
                "|wCreator|n", 
                "|wTemp?|n",
                border="table",
                width=78
            )
            
            for npc in sorted(npcs, key=lambda x: x.key):
                loc = npc.location.key if npc.location else "No Location"
                splat = npc.db.stats.get('splat', 'Unknown') if hasattr(npc.db, 'stats') else 'Unknown'
                creator = npc.db.creator.key if npc.db.creator else "Unknown"
                temp = "Yes" if npc.db.is_temporary else "No"
                
                table.add_row(npc.key, loc, splat, creator, temp)
                
        # Send formatted table
        header = f"|wAll NPCs in Game|n ({len(npcs)} total)"
        if only_temp:
            header = f"|wTemporary NPCs|n ({len(npcs)} total)"
        elif only_perm:
            header = f"|wPermanent NPCs|n ({len(npcs)} total)"
            
        self.caller.msg(f"\n{header}\n{table}")
        
        if npcs:
            # Show quick help for further filtering
            help_text = "\nTo filter results:"
            help_text += "\n+npc/listall/loc - Group by location"
            help_text += "\n+npc/listall/splat - Group by splat type"
            help_text += "\n+npc/listall/temp - Show only temporary NPCs"
            help_text += "\n+npc/listall/perm - Show only permanent NPCs"
            self.caller.msg(help_text)