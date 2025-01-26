from evennia import default_cmds
from evennia.utils.ansi import ANSIString
from world.wod20th.models import Stat
from world.wod20th.utils.dice_rolls import roll_dice
import random

class CmdInit(default_cmds.MuxCommand):
    """
    Roll initiative for all characters in a scene.

    Usage:
      +init           - View current initiative order if it exists, or roll new if none exists
      +init/new      - New initiative roll for new turn
      +init/view     - View the current initiative order without rolling new ones
      +init/npc <name>/<modifier> - Add an NPC to the initiative order with optional modifier
      +init/remove <name>  - Remove an NPC from the initiative order
      +init/clear    - Clear all NPCs from the initiative order

    This command allows you to roll the initiative of all characters visible to you 
    in a scene, be it for combat related purposes or simply for reaction's sake.
    The command uses the standard 20th rule of rolling a 10-sided die and then 
    adding your current wits and dex to the result.

    NPCs can be added with optional modifiers to their initiative rolls.
    Example: +init/npc Guard/2 will add an NPC named Guard with +2 to initiative.
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
        elif "remove" in self.switches:
            self.remove_npc()
            return
        elif "clear" in self.switches:
            self.clear_npcs()
            return
        
        # Default behavior: view if exists, otherwise roll new
        if hasattr(self.caller.location, "db_initiative_order"):
            self.view_initiatives()
        else:
            self.roll_new_initiatives()

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

        # Initialize NPC list if it doesn't exist
        if not hasattr(self.caller.location, "db_npcs"):
            self.caller.location.db_npcs = {}

        # Add NPC to the list
        self.caller.location.db_npcs[name] = {
            "modifier": modifier,
            "health": {
                "bashing": 0,
                "lethal": 0,
                "aggravated": 0
            }
        }

        # Get all characters in the scene
        characters = [obj for obj in self.caller.location.contents if obj.has_account]
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

        # Roll for all NPCs
        for npc_name, npc_data in self.caller.location.db_npcs.items():
            roll = random.randint(1, 10)
            npc_modifier = npc_data["modifier"]
            total = roll + npc_modifier
            initiatives.append((npc_name, total, roll, npc_modifier, 0))

        # Sort initiatives from highest to lowest
        initiatives.sort(key=lambda x: x[1], reverse=True)
        
        # Store in room
        self.caller.location.db_initiative_order = initiatives

        self.caller.location.msg_contents(f"|w{name}|n has been added to the initiative order.")
        self.display_initiatives(initiatives, is_new=False)

    def remove_npc(self):
        """Remove an NPC from the initiative order."""
        if not self.args:
            self.caller.msg("Usage: +init/remove <name>")
            return

        name = self.args.strip()
        if not hasattr(self.caller.location, "db_npcs") or name not in self.caller.location.db_npcs:
            self.caller.msg(f"No NPC named '{name}' found in the initiative order.")
            return

        # Remove from NPCs list
        del self.caller.location.db_npcs[name]

        # Remove from initiative order
        if hasattr(self.caller.location, "db_initiative_order"):
            initiatives = self.caller.location.db_initiative_order
            initiatives = [init for init in initiatives if init[0] != name]
            self.caller.location.db_initiative_order = initiatives

        self.caller.location.msg_contents(f"|w{name}|n has been removed from the initiative order.")
        self.view_initiatives()

    def clear_npcs(self):
        """Clear all NPCs from the initiative order."""
        if not hasattr(self.caller.location, "db_npcs"):
            self.caller.msg("No NPCs in the initiative order.")
            return

        # Clear NPCs list
        self.caller.location.db_npcs = {}

        # Remove NPCs from initiative order
        if hasattr(self.caller.location, "db_initiative_order"):
            initiatives = self.caller.location.db_initiative_order
            initiatives = [init for init in initiatives if init[0] in [char.name for char in self.caller.location.contents if char.has_account]]
            self.caller.location.db_initiative_order = initiatives

        self.caller.location.msg_contents("All NPCs have been removed from the initiative order.")
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
                modifier = npc_data["modifier"]
                total = roll + modifier
                initiatives.append((name, total, roll, modifier, 0))  # Last 0 is placeholder for dexterity

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

    def display_initiatives(self, initiatives, is_new=True):
        """Format and display the initiative results."""
        header = "\n|b==============================================================================|n"
        result = [header]
        if is_new:
            result.append("|y+INIT> New Scene Initiatives:|n")
        else:
            result.append("|y+INIT> Current Scene Initiatives:|n")
        
        for entry in initiatives:
            char_name = entry[0]
            total = entry[1]
            roll = entry[2]
            
            # Check if it's an NPC
            if hasattr(self.caller.location, "db_npcs") and char_name in self.caller.location.db_npcs:
                modifier = entry[3]
                result.append(f"|w{char_name} (NPC):|n {total} (Roll: {roll} + Modifier: {modifier})")
            else:
                wits = entry[3]
                dex = entry[4]
                result.append(f"|w{char_name}:|n {total} (Roll: {roll} + Wits: {wits} + Dex: {dex})")

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