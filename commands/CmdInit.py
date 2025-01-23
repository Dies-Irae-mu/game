from evennia import default_cmds
from evennia.utils.ansi import ANSIString
from world.wod20th.models import Stat
from world.wod20th.utils.dice_rolls import roll_dice
import random

class CmdInit(default_cmds.MuxCommand):
    """
    Roll initiative for all characters in a scene.

    Usage:
      +init       - View current initiative order if it exists, or roll new if none exists
      +init/new   - New initiative roll for new turn
      +init/view  - View the current initiative order without rolling new ones (similar to 
                    +init)

    This command allows you to roll the initiative of all characters visible to you 
    in a scene, be it for combat related purposes or simply for reaction's sake.
    The command uses the standard 20th rule of rolling a 10-sided die and then 
    adding your current wits and dex to the result.

    We'll be adding in a way to roll initiative for NPCs in the future, along with
    any adjustments to initiative (such as Spirit of the Fray, etc.)
    """

    key = "+init"
    aliases = ["init"]
    locks = "cmd:all()"
    help_category = "Game"

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
        
        # Default behavior: view if exists, otherwise roll new
        if hasattr(self.caller.location, "db_initiative_order"):
            self.view_initiatives()
        else:
            self.roll_new_initiatives()

    def roll_new_initiatives(self):
        """Roll new initiatives for all characters in the scene."""
        location = self.caller.location
        characters = [obj for obj in location.contents if obj.has_account]
        
        if not characters:
            self.caller.msg("There are no characters in this scene.")
            return

        # Calculate and store initiatives
        initiatives = []
        for char in characters:
            # Get Wits and Dexterity values
            wits = self.get_stat_value(char, "Wits")
            dexterity = self.get_stat_value(char, "Dexterity")
            
            # Roll 1d10
            roll = random.randint(1, 10)
            
            # Calculate total initiative
            total = roll + wits + dexterity
            
            # Add roll details for debugging
            initiatives.append((char.name, total, roll, wits, dexterity))

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
            if len(entry) > 2:  # If we have the detailed breakdown
                roll, wits, dex = entry[2:]
                result.append(f"|w{char_name}:|n {total} (Roll: {roll} + Wits: {wits} + Dex: {dex})")
            else:
                result.append(f"|w{char_name}:|n {total}")

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