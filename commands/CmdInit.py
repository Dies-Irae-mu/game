from evennia import default_cmds
from evennia.utils.ansi import ANSIString
from world.wod20th.models import Stat
from world.wod20th.utils.dice_rolls import roll_dice
from commands.CmdNPC import NameGenerator
from world.wod20th.data.npc.random_stat import get_random_npc_stats, format_npc_stats_display
import random
from evennia import create_object, search_object

class CmdInit(default_cmds.MuxCommand):
    """
    Roll initiative for all characters in a scene.

    Usage:
      +init           - View current initiative order if it exists, or roll new if none exists
      +init/new       - New initiative roll for new turn
      +init/view      - View the current initiative order without rolling new ones
      +init/npc <name>/<modifier> - Add an NPC to the initiative order with optional modifier
      +init/randnpc [nationality/nationality2/gender] <modifier> [splat=type] [diff=level]
                     - Add a random-named NPC with random stats
      +init/remove <name or #id or &uuid> - Remove an NPC from the initiative order (destroys NPC object)
      +init/setsplat <name or #id or &uuid>=<splat_type>/<difficulty> - Change NPC's splat type
      +init/clear     - Clear all NPCs from the initiative order

    This command allows you to roll the initiative of all characters visible to you 
    in a scene, be it for combat related purposes or simply for reaction's sake.
    The command uses the standard 20th rule of rolling a 10-sided die and then 
    adding your current wits and dex to the result.

    NPCs can be added with optional modifiers to their initiative rolls.
    Example: +init/npc Guard/2 will add an NPC named Guard with +2 to initiative.
    Example: +init/randnpc american/japanese/female 3 will add a female NPC with an American
             first name and Japanese last name with +3 to initiative.
    Example: +init/randnpc 5 splat=vampire diff=HIGH will add a high-difficulty vampire NPC
             with random name and +5 to initiative.
    Example: +init/setsplat Vampire Bob=vampire/HIGH will change Vampire Bob to a high-difficulty vampire.
             
    Available splat types: mortal, vampire, mage, shifter, psychic, spirit
    Difficulty levels: LOW, MEDIUM, HIGH
    See 'help npc' for more information.
    """

    key = "+init"
    aliases = ["init"]
    locks = "cmd:all()"
    help_category = "RP Commands"

    def func(self):
        if not self.caller.location:
            self.caller.msg("You must be in a location to use this command.")
            return

        # Handle switches
        if "view" in self.switches:
            self.view_initiatives()
            return
        elif "new" in self.switches:
            self.roll_new_initiatives()
            return
        elif "npc" in self.switches:
            self.add_npc()
            return
        elif "randnpc" in self.switches:
            self.add_random_npc()
            return
        elif "remove" in self.switches:
            self.remove_npc()
            return
        elif "clear" in self.switches:
            self.clear_npcs()
            return
        elif "setsplat" in self.switches:
            self.set_npc_splat()
            return
        
        # Default behavior: view if exists, otherwise roll new
        if hasattr(self.caller.location, "db_initiative_order"):
            self.view_initiatives()
        else:
            self.roll_new_initiatives()

    def parse_npc_params(self, args_string):
        """
        Parses NPC parameters from slash-separated or space-separated arguments.
        Handles various formats for name generation including nationality, gender, and mixed nationalities.
        Returns a tuple of first_nationality, gender, second_nationality, and modifier.
        """
        parts = args_string.strip().split()
        modifier = 0
        splat = "mortal"
        difficulty = "MEDIUM"
        
        # Check for keyword parameters
        name_parts = []
        for i, part in enumerate(parts):
            if "=" in part:
                key, value = part.split("=", 1)
                if key.lower() == "splat":
                    splat = value.lower()
                elif key.lower() == "diff":
                    difficulty = value.upper()
                # Skip this part since it's a keyword parameter
                continue
            # If it's a number and the first number we've encountered, it's the modifier
            elif part.lstrip('-').isdigit() and all(not p.lstrip('-').isdigit() for p in parts[:i]):
                modifier = int(part)
                # Skip this part since it's the modifier
                continue
            # Otherwise it's part of the name specification
            name_parts.append(part)
        
        if not name_parts:
            return None, None, None, modifier, splat, difficulty
            
        # Join the name parts back with spaces to parse as a single string
        name_string = " ".join(name_parts)
        
        # Use the parse_name_args method from CmdNPC to extract nationality info
        first_nat, gender, second_nat = self.parse_name_args(name_string)
        
        return first_nat, gender, second_nat, modifier, splat, difficulty

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
        
        # Check if empty
        if not args_string:
            return first_nat, gender, second_nat
        
        # Check for slash-separated nationalities (american/japanese)
        if "/" in args_string:
            parts = args_string.split("/")
            if len(parts) >= 1:
                first_nat = parts[0].strip()
            
            if len(parts) >= 2:
                # Check if second part is gender
                second_part = parts[1].strip()
                if second_part.lower() in ["male", "female"]:
                    gender = second_part.lower()
                else:
                    second_nat = second_part
            
            if len(parts) >= 3:
                # Third part must be gender
                third_part = parts[2].strip()
                if third_part.lower() in ["male", "female"]:
                    gender = third_part.lower()
                    
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

    def add_random_npc(self):
        """Add an NPC with a randomly generated name to the initiative order."""
        if not self.args:
            self.caller.msg("Usage: +init/randnpc [nationality/nationality2/gender] <modifier> [splat=type] [diff=level]")
            return
            
        # Parse parameters
        first_nat, gender, second_nat, modifier, splat_type, difficulty = self.parse_npc_params(self.args)
        
        # Generate name
        first_name, last_name, first_nat_used, last_nat_used = NameGenerator.generate_name(
            first_nat, gender, second_nat
        )
        
        if not first_name:
            if first_nat or second_nat:
                self.caller.msg(f"Error: Could not generate name with the specified parameters.")
            else:
                self.caller.msg("Error: Could not generate name. Name data files not found.")
            return
            
        # Format name
        full_name = NameGenerator.format_name(first_name, last_name)
        
        # Create NPC object using the NPC typeclass
        npc = create_object(
            "typeclasses.npcs.NPC",
            key=full_name,
            location=self.caller.location
        )
        
        # Set NPC properties - now using the typeclass's set_splat method
        npc.set_splat(splat_type, difficulty)
        npc.db.is_temporary = True  # This is a temporary NPC
        npc.db.creator = self.caller
        npc.set_as_temporary(self.caller)
        
        # If we have a modifier, set it in the room's NPC data
        if hasattr(self.caller.location, "db_npcs") and full_name in self.caller.location.db_npcs:
            self.caller.location.db_npcs[full_name]["modifier"] = modifier
        
        # NPC should already be registered in the room by the typeclass
        # Let's make sure it's in the initiative order
        self.roll_initiatives_with_new_npc(npc.key)
        
        # Display nationality info
        if first_nat_used != last_nat_used:
            nationality_info = f"({first_nat_used.replace('_', ' ').title()}/{last_nat_used.replace('_', ' ').title()})"
        else:
            nationality_info = f"({first_nat_used.replace('_', ' ').title()})"
            
        gender_info = f", {gender}" if gender else ""
        
        # Get NPC info for display
        npc_number = npc.db.npc_number
        npc_id = npc.db.npc_id
        
        # Send basic NPC added message
        self.caller.location.msg_contents(
            f"NPC |w{full_name}|n {nationality_info}{gender_info} (#{npc_number}, ID: &{npc_id[:8]}) "
            f"has been added as a {splat_type.title()} ({difficulty}) with initiative modifier +{modifier}."
        )
        
        # Display NPC's stats to the creator
        self.display_npc_stats(npc, self.caller)

    def display_npc_stats(self, npc, viewer):
        """Display an NPC's stats to the specified viewer."""
        if not npc or not viewer:
            return
            
        stats = npc.db.stats
        
        # Basic info
        viewer.msg(f"|c== {npc.key}'s Stats ({stats.get('splat', 'unknown').title()}, {stats.get('difficulty', 'MEDIUM')}) ==|n")
        
        # Attributes
        if "attributes" in stats:
            viewer.msg("\n|yAttributes:|n")
            for category in ["physical", "social", "mental"]:
                if category in stats["attributes"]:
                    attrs = []
                    for attr, val in sorted(stats["attributes"][category].items()):
                        attrs.append(f"{attr.title()}: {val}")
                    viewer.msg(f"  |w{category.title()}:|n {', '.join(attrs)}")
                    
        # Abilities
        if "abilities" in stats:
            ability_count = sum(len(category) for category in stats["abilities"].values())
            if ability_count > 0:
                viewer.msg("\n|yAbilities:|n")
                for category in ["talents", "skills", "knowledges"]:
                    if category in stats["abilities"] and stats["abilities"][category]:
                        abilities = []
                        for ability, val in sorted(stats["abilities"][category].items()):
                            abilities.append(f"{ability.replace('_', ' ').title()}: {val}")
                        viewer.msg(f"  |w{category.title()}:|n {', '.join(abilities)}")
        
        # Powers based on splat type
        if "powers" in stats:
            viewer.msg("\n|yPowers:|n")
            for power_type, powers in stats["powers"].items():
                if powers:  # Only show if there are powers
                    if isinstance(powers, dict) and powers:
                        power_list = []
                        for power, val in sorted(powers.items()):
                            power_list.append(f"{power.title()}: {val}")
                        viewer.msg(f"  |w{power_type.title()}s:|n {', '.join(power_list)}")
                    elif isinstance(powers, list) and powers:
                        viewer.msg(f"  |w{power_type.title()}s:|n {', '.join(powers)}")
        
        # Special traits based on splat type
        if stats.get('splat') == 'vampire':
            viewer.msg(f"\n|wBlood Pool:|n {stats.get('blood_pool', 10)}")
            viewer.msg(f"|wGeneration:|n {stats.get('generation', 13)}")
        elif stats.get('splat') == 'mage':
            viewer.msg(f"\n|wArete:|n {stats.get('arete', 1)}")
            viewer.msg(f"|wQuintessence:|n {stats.get('quintessence', 0)}")
            viewer.msg(f"|wParadox:|n {stats.get('paradox', 0)}")
        elif stats.get('splat') == 'shifter':
            viewer.msg(f"\n|wRage:|n {stats.get('rage', 1)}")
            viewer.msg(f"|wGnosis:|n {stats.get('gnosis', 1)}")
            viewer.msg(f"|wRenown:|n Glory {stats.get('glory', 0)}, Honor {stats.get('honor', 0)}, Wisdom {stats.get('wisdom', 0)}")
        elif stats.get('splat') == 'spirit':
            viewer.msg(f"\n|wRank:|n {stats.get('rank', 1)}")
            viewer.msg(f"|wGnosis:|n {stats.get('gnosis', 1)}")
            viewer.msg(f"|wRage:|n {stats.get('rage', 1)}")
            viewer.msg(f"|wEssence:|n {stats.get('essence', 10)}")
            
        # Health and willpower for all types
        viewer.msg(f"\n|wWillpower:|n {stats.get('willpower', 3)}")
        health = stats.get('health', {"bashing": 0, "lethal": 0, "aggravated": 0})
        viewer.msg(f"|wHealth:|n Bashing: {health['bashing']}, Lethal: {health['lethal']}, Aggravated: {health['aggravated']}")

    def roll_initiatives_with_new_npc(self, new_npc_name):
        """Roll initiative for all characters after adding a new NPC."""
        location = self.caller.location
        characters = [obj for obj in location.contents if obj.has_account]
        
        # Calculate and store initiatives
        initiatives = []
        
        # Roll for PCs
        for char in characters:
            # Get Wits and Dexterity values
            wits = self.get_stat_value(char, "Wits")
            dexterity = self.get_stat_value(char, "Dexterity")
            
            # Roll 1d10
            roll = random.randint(1, 10)
            
            # Calculate total initiative
            total = roll + wits + dexterity
            
            initiatives.append((char.name, total, roll, wits, dexterity))

        # Roll for NPCs
        if hasattr(location, "db_npcs"):
            for name, npc_data in location.db_npcs.items():
                roll = random.randint(1, 10)
                modifier = npc_data.get("modifier", 0)
                total = roll + modifier
                
                # See if we can get wits and dex from stats
                wits = 0
                dex = 0
                if "stats" in npc_data and "attributes" in npc_data["stats"]:
                    stats = npc_data["stats"]
                    if "mental" in stats["attributes"] and "wits" in stats["attributes"]["mental"]:
                        wits = stats["attributes"]["mental"]["wits"]
                    if "physical" in stats["attributes"] and "dexterity" in stats["attributes"]["physical"]:
                        dex = stats["attributes"]["physical"]["dexterity"]
                    
                    # If we have stats, use them to calculate initiative
                    if wits > 0 or dex > 0:
                        total = roll + wits + dex
                
                # Store NPC ID and number to use in display
                npc_id = npc_data.get("npc_id", "")
                npc_number = npc_data.get("number", "")
                
                initiatives.append((name, total, roll, modifier, 0, npc_id, npc_number))  # Add ID and number

        # Sort initiatives from highest to lowest
        initiatives.sort(key=lambda x: x[1], reverse=True)
        
        # Store in room
        self.caller.location.db_initiative_order = initiatives
        
        # Display results, highlighting the new NPC
        self.display_initiatives(initiatives, is_new=False, highlight_npc=new_npc_name)

    def add_npc(self):
        """Add an NPC to the initiative order."""
        if not self.args:
            self.caller.msg("Usage: +init/npc <name>/<modifier>")
            return

        # Parse name and modifier
        if "/" in self.args:
            name, modifier = self.args.split("/", 1)
            try:
                modifier = int(modifier)
            except ValueError:
                self.caller.msg("Modifier must be a number.")
                return
        else:
            name = self.args
            modifier = 0

        name = name.strip()
        if not name:
            self.caller.msg("You must specify an NPC name.")
            return

        # Create NPC object using the NPC typeclass
        npc = create_object(
            "typeclasses.npcs.NPC",
            key=name,
            location=self.caller.location
        )
        
        # Set NPC properties - default to mortal
        npc.set_splat("mortal", "MEDIUM")
        npc.db.is_temporary = True  # This is a temporary NPC
        npc.db.creator = self.caller
        
        # Set as temporary to trigger proper registration
        npc.set_as_temporary(self.caller)

        # Make sure the NPC is registered in the room
        if hasattr(self.caller.location, "db_npcs") and name in self.caller.location.db_npcs:
            # Set initiative modifier
            self.caller.location.db_npcs[name]["modifier"] = modifier
        
        # Get NPC info for display
        npc_number = npc.db.npc_number
        npc_id = npc.db.npc_id
        
        # Roll for all characters
        self.roll_new_initiatives()

        self.caller.location.msg_contents(
            f"NPC |w{name}|n (#{npc_number}, ID: &{npc_id[:8]}) has been added to the initiative order."
        )
        
        # Display initiatives again to show the new NPC
        self.display_initiatives(self.caller.location.db_initiative_order, is_new=False, highlight_npc=name)

    def set_npc_splat(self):
        """Change an NPC's splat type."""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +init/setsplat <name or #id or &uuid>=<splat_type>/<difficulty>")
            return
            
        # Parse name and splat type
        identifier, splat_info = self.args.split("=", 1)
        identifier = identifier.strip()
        
        # Parse splat type and difficulty
        if "/" in splat_info:
            splat_type, difficulty = splat_info.split("/", 1)
            splat_type = splat_type.strip().lower()
            difficulty = difficulty.strip().upper()
        else:
            splat_type = splat_info.strip().lower()
            difficulty = "MEDIUM"
            
        # Validate splat type
        valid_splats = ["mortal", "vampire", "mage", "shifter", "psychic", "spirit"]
        if splat_type not in valid_splats:
            self.caller.msg(f"Invalid splat type. Valid types are: {', '.join(valid_splats)}")
            return
            
        # Validate difficulty
        valid_difficulties = ["LOW", "MEDIUM", "HIGH"]
        if difficulty not in valid_difficulties:
            self.caller.msg(f"Invalid difficulty. Valid difficulties are: {', '.join(valid_difficulties)}")
            return
        
        # Find the NPC
        npc_obj, npc_name = self.find_npc_by_id_or_name(identifier)
        
        if not npc_obj:
            self.caller.msg(f"No NPC found matching '{identifier}'.")
            return
            
        # Set the new splat type
        if npc_obj.set_splat(splat_type, difficulty):
            # Get NPC display info
            npc_number = npc_obj.db.npc_number
            npc_id = npc_obj.db.npc_id
            
            # Announce the change
            self.caller.location.msg_contents(
                f"NPC |w{npc_name}|n (#{npc_number}, ID: &{npc_id[:8]}) has been changed to a {splat_type.title()} ({difficulty})."
            )
            
            # Display updated stats to the caller
            self.display_npc_stats(npc_obj, self.caller)
            
            # Update initiative order if it exists
            if hasattr(self.caller.location, "db_initiative_order"):
                self.roll_new_initiatives()
        else:
            self.caller.msg(f"Failed to set {npc_name}'s splat type to {splat_type}.")

    def find_npc_by_id_or_name(self, identifier):
        """
        Find an NPC by ID, name, or number.
        
        Args:
            identifier (str): Can be a name, #number, or &uuid
            
        Returns:
            tuple: (npc_object, npc_name)
        """
        if not self.caller.location or not hasattr(self.caller.location, "db_npcs"):
            return None, None
            
        # Check if using UUID format
        if identifier.startswith("&"):
            uuid_prefix = identifier[1:].lower()
            for npc_name, npc_data in self.caller.location.db_npcs.items():
                if "npc_id" in npc_data and npc_data["npc_id"].lower().startswith(uuid_prefix):
                    npc_obj = npc_data.get("npc_object")
                    return npc_obj, npc_name
                    
        # Check if using numeric ID
        elif identifier.startswith("#"):
            try:
                npc_number = int(identifier[1:])
                for npc_name, npc_data in self.caller.location.db_npcs.items():
                    if npc_data.get("number") == npc_number:
                        npc_obj = npc_data.get("npc_object")
                        return npc_obj, npc_name
            except ValueError:
                pass
                
        # Check for exact name match
        if identifier in self.caller.location.db_npcs:
            npc_obj = self.caller.location.db_npcs[identifier].get("npc_object")
            return npc_obj, identifier
        
        # Try partial name matching
        matched_npcs = [npc for npc in self.caller.location.db_npcs.keys() 
                        if identifier.lower() in npc.lower()]
        
        if len(matched_npcs) == 1:
            npc_name = matched_npcs[0]
            npc_obj = self.caller.location.db_npcs[npc_name].get("npc_object")
            return npc_obj, npc_name
            
        return None, None

    def remove_npc(self):
        """Remove an NPC from the initiative order."""
        if not self.args:
            self.caller.msg("Usage: +init/remove <name or #number or &uuid>")
            return

        identifier = self.args.strip()
        
        # Find the NPC using our helper method
        npc_obj, npc_name = self.find_npc_by_id_or_name(identifier)
        
        if not npc_name:
            if identifier.startswith("&") or identifier.startswith("#"):
                self.caller.msg(f"No NPC with identifier '{identifier}' found in this scene.")
            else:
                # If multiple matches might exist, check and inform
                if hasattr(self.caller.location, "db_npcs"):
                    matched_npcs = [npc for npc in self.caller.location.db_npcs.keys() 
                                  if identifier.lower() in npc.lower()]
                    
                    if len(matched_npcs) > 1:
                        matches = []
                        for name in matched_npcs:
                            data = self.caller.location.db_npcs[name]
                            num = data.get("number", "?")
                            npc_id = data.get("npc_id", "")
                            if npc_id:
                                npc_id = npc_id[:8]
                                matches.append(f"{name} (#{num}, &{npc_id})")
                            else:
                                matches.append(f"{name} (#{num})")
                                
                        self.caller.msg(f"Multiple NPCs match '{identifier}'. Please be more specific or use #ID: " +
                                      ", ".join(matches))
                        return
                
                self.caller.msg(f"No NPC named '{identifier}' found in the initiative order.")
            return

        # Get display info
        npc_number = self.caller.location.db_npcs[npc_name].get("number", "")
        npc_id = self.caller.location.db_npcs[npc_name].get("npc_id", "")
        id_display = ""
        
        if npc_id:
            id_display = f", &{npc_id[:8]}"
            
        number_display = f" (#{npc_number}{id_display})" if npc_number else ""

        # Delete the actual NPC object if it exists
        if npc_obj:
            try:
                npc_obj.delete()
            except Exception as e:
                self.caller.msg(f"Warning: Could not delete NPC object: {e}")
                # Still continue to remove from initiative

        # Remove from initiative order
        if hasattr(self.caller.location, "db_initiative_order"):
            initiatives = self.caller.location.db_initiative_order
            initiatives = [init for init in initiatives if init[0] != npc_name]
            self.caller.location.db_initiative_order = initiatives

        self.caller.location.msg_contents(f"|w{npc_name}|n{number_display} has been removed from the initiative order.")
        self.view_initiatives()

    def clear_npcs(self):
        """Clear all NPCs from the initiative order."""
        if not hasattr(self.caller.location, "db_npcs"):
            self.caller.msg("No NPCs in the initiative order.")
            return

        # Delete all NPC objects
        npc_count = 0
        for npc_name, npc_data in list(self.caller.location.db_npcs.items()):
            if "npc_object" in npc_data:
                npc_obj = npc_data["npc_object"]
                if npc_obj:
                    try:
                        npc_obj.delete()
                        npc_count += 1
                    except Exception as e:
                        self.caller.msg(f"Warning: Could not delete NPC '{npc_name}': {e}")

        # Remove NPCs from initiative order
        if hasattr(self.caller.location, "db_initiative_order"):
            initiatives = self.caller.location.db_initiative_order
            initiatives = [init for init in initiatives if init[0] in [char.name for char in self.caller.location.contents if char.has_account]]
            self.caller.location.db_initiative_order = initiatives

        self.caller.location.msg_contents(f"All NPCs ({npc_count}) have been removed from the initiative order.")
        self.view_initiatives()

    def roll_new_initiatives(self):
        """Roll new initiatives for all characters in the scene."""
        location = self.caller.location
        characters = [obj for obj in location.contents if obj.has_account]
        
        if not characters and (not hasattr(location, "db_npcs") or not location.db_npcs):
            self.caller.msg("There are no characters or NPCs in this scene.")
            return

        # Calculate and store initiatives
        initiatives = []
        
        # Roll for PCs
        for char in characters:
            # Get Wits and Dexterity values
            wits = self.get_stat_value(char, "Wits")
            dexterity = self.get_stat_value(char, "Dexterity")
            
            # Roll 1d10
            roll = random.randint(1, 10)
            
            # Calculate total initiative
            total = roll + wits + dexterity
            
            initiatives.append((char.name, total, roll, wits, dexterity))

        # Roll for NPCs
        if hasattr(location, "db_npcs"):
            for name, npc_data in location.db_npcs.items():
                roll = random.randint(1, 10)
                modifier = npc_data.get("modifier", 0)
                total = roll + modifier
                
                # Check if we have stats to use instead of just the modifier
                if "stats" in npc_data and "attributes" in npc_data["stats"]:
                    stats = npc_data["stats"]
                    if "mental" in stats["attributes"] and "wits" in stats["attributes"]["mental"]:
                        wits = stats["attributes"]["mental"]["wits"]
                    else:
                        wits = 0
                        
                    if "physical" in stats["attributes"] and "dexterity" in stats["attributes"]["physical"]:
                        dex = stats["attributes"]["physical"]["dexterity"]
                    else:
                        dex = 0
                    
                    # If we have stats, use them to calculate initiative
                    if wits > 0 or dex > 0:
                        total = roll + wits + dex
                
                # Store NPC ID and number to use in display
                npc_id = npc_data.get("npc_id", "")
                npc_number = npc_data.get("number", "")
                
                initiatives.append((name, total, roll, modifier, 0, npc_id, npc_number))  # Add ID and number

        # Sort initiatives from highest to lowest
        initiatives.sort(key=lambda x: x[1], reverse=True)
        
        # Store in room
        self.caller.location.db_initiative_order = initiatives
        
        # Display results
        self.display_initiatives(initiatives, is_new=True)

    def view_initiatives(self):
        """View the current initiative order."""
        location = self.caller.location
        if not hasattr(location, "db_initiative_order") or not location.db_initiative_order:
            self.caller.msg("No initiative order has been set for this scene. Use +init/new to roll initiatives.")
            return
            
        self.display_initiatives(location.db_initiative_order, is_new=False)

    def display_initiatives(self, initiatives, is_new=True, highlight_npc=None):
        """Format and display the initiative results."""
        header = "\n|b==============================================================================|n"
        result = [header]
        if is_new:
            result.append("|y+INIT> New Scene Initiatives:|n")
        else:
            result.append("|y+INIT> Current Scene Initiatives:|n")
        
        for i, entry in enumerate(initiatives):
            char_name = entry[0]
            total = entry[1]
            roll = entry[2]
            
            # Check if it's an NPC
            if hasattr(self.caller.location, "db_npcs") and char_name in self.caller.location.db_npcs:
                npc_data = self.caller.location.db_npcs[char_name]
                modifier = entry[3]
                npc_number = npc_data.get("number", "")
                npc_id = npc_data.get("npc_id", "")
                
                # Format the ID display
                id_display = f", &{npc_id[:8]}" if npc_id else ""
                number_display = f" (#{npc_number}{id_display})" if npc_number else ""
                
                # Get splat type
                splat_type = npc_data.get("stats", {}).get("splat", "mortal").title()
                
                # Check if we have stats to use
                if "stats" in npc_data and "attributes" in npc_data["stats"]:
                    stats = npc_data["stats"]
                    wits = 0
                    dex = 0
                    
                    if "mental" in stats["attributes"] and "wits" in stats["attributes"]["mental"]:
                        wits = stats["attributes"]["mental"]["wits"]
                    
                    if "physical" in stats["attributes"] and "dexterity" in stats["attributes"]["physical"]:
                        dex = stats["attributes"]["physical"]["dexterity"]
                    
                    if wits > 0 or dex > 0:
                        mod_display = f"Wits: {wits} + Dex: {dex}"
                    else:
                        mod_display = f"Modifier: {modifier}"
                else:
                    mod_display = f"Modifier: {modifier}"
                
                # Display position in initiative order
                position = f"{i+1}. "
                
                # Highlight the newly added NPC
                if highlight_npc and char_name == highlight_npc:
                    result.append(f"|r> {position}|w{char_name}|n{number_display} [{splat_type}]: {total} (Roll: {roll} + {mod_display}) |r<|n")
                else:
                    result.append(f"{position}|w{char_name}|n{number_display} [{splat_type}]: {total} (Roll: {roll} + {mod_display})")
            else:
                # Display position in initiative order
                position = f"{i+1}. "
                
                wits = entry[3]
                dex = entry[4]
                result.append(f"{position}|w{char_name}:|n {total} (Roll: {roll} + Wits: {wits} + Dex: {dex})")

        result.append(header)
        self.caller.location.msg_contents("\n".join(result))

    def get_stat_value(self, character, stat_name):
        """Get the value of a stat for a character."""
        try:
            stats = character.db.stats
            if not stats:
                return 0
                
            # Navigate the nested dictionary structure
            if stat_name == "Wits":
                return stats['attributes']['mental']['Wits']['temp']
            elif stat_name == "Dexterity":
                return stats['attributes']['physical']['Dexterity']['temp']
            return 0
        except (AttributeError, KeyError):
            return 0 