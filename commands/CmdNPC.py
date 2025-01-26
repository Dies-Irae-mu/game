from evennia import default_cmds
from evennia.utils.ansi import ANSIString
from world.wod20th.utils.dice_rolls import roll_dice, interpret_roll_results
import random

class CmdNPC(default_cmds.MuxCommand):
    """
    Manage NPCs in a scene, including health and dice rolls.
    See 'help init' for more information on initiative.

    Usage:
      +npc/roll <name>=<dice pool>/<difficulty>  - Roll dice for an NPC (difficulty defaults to 6)
      +npc/hurt <name>=<type>/<amount>          - Damage an NPC (type: bashing/lethal/aggravated)
      +npc/heal <name>=<type>/<amount>          - Heal an NPC's damage
      +npc/health <name>                        - View NPC's current health levels
      +npc/list                                 - List all NPCs in the scene

    Examples:
      +npc/roll Guard=5/6              - Roll 5 dice for the Guard with difficulty 6
      +npc/roll Guard=5                - Roll 5 dice for the Guard (default difficulty 6)
      +npc/hurt Guard=bashing/2        - Apply 2 bashing damage to Guard
      +npc/heal Guard=bashing/1        - Heal 1 bashing damage from Guard
      +npc/health Guard                - Show Guard's current health levels
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
                log_description = f"{name} rolls {dice} dice vs {difficulty}"
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
        elif total_damage <= 2:
            return "Bruised"
        elif total_damage <= 4:
            return "Hurt"
        elif total_damage <= 6:
            return "Injured"
        elif total_damage <= 8:
            return "Wounded"
        elif total_damage <= 10:
            return "Mauled"
        elif total_damage <= 12:
            return "Crippled"
        else:
            return "Incapacitated" 