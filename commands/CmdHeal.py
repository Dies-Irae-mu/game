from evennia import Command
from world.wod20th.utils.damage import apply_damage_or_healing, format_status, format_damage, calculate_total_health_levels

class CmdHeal(Command):
    """
    Heal damage on yourself or another character.
    
    Usage:
        +heal <amount><type>
        +heal <name>=<amount><type>
    
    Example:
        +heal 3l
        +heal Bob=2b
    """
    key = "+heal"
    locks = "cmd:all()"
    help_category = "RP Commands"

    def parse(self):
        args = self.args.strip().split("=")
        if len(args) == 2:
            self.target_name, self.healing_input = args
        else:
            self.target_name, self.healing_input = None, args[0]
        self.target_name = self.target_name.strip() if self.target_name else None
        self.healing_input = self.healing_input.strip()

    def func(self):
        if not self.healing_input:
            self.caller.msg("Usage: +heal <amount><type> or +heal <name>=<amount><type>")
            return

        if self.target_name:
            if not self.caller.locks.check_lockstring(self.caller, "perm(Builder)"):
                self.caller.msg("You don't have permission to heal others.")
                return
            target = self.caller.search(self.target_name)
            if not target:
                return
        else:
            target = self.caller

        try:
            healing = int(self.healing_input[:-1])
            healing_type = self.healing_input[-1].lower()
            if healing_type not in ['b', 'l', 'a']:
                raise ValueError
            if healing <= 0:
                raise ValueError
        except ValueError:
            self.caller.msg("Invalid healing input. Use a positive number followed by b, l, or a (e.g., 3l, 2b, 4a).")
            return

        healing_type_full = {'b': 'bashing', 'l': 'lethal', 'a': 'aggravated'}[healing_type]
        
        # Initialize health_level_bonuses if it doesn't exist
        if not hasattr(target.db, 'health_level_bonuses') or target.db.health_level_bonuses is None:
            target.db.health_level_bonuses = {
                'bruised': 0,
                'hurt': 0,
                'injured': 0,
                'wounded': 0,
                'mauled': 0,
                'crippled': 0
            }
        
        # Calculate total health levels including bonuses
        total_health = calculate_total_health_levels(target)

        # Apply healing with negative amount
        apply_damage_or_healing(target, -healing, healing_type_full)

        # Get the green gradient_name of the target
        target_gradient = target.db.gradient_name or target.key

        msg = f"|gHEAL> |n{target_gradient} heals |g{healing}|n |y{healing_type_full}|n.\n"
        msg += f"|gHEAL> |n{format_damage(target)} Status: {format_status(target)}"
        
        # Send messages and emit to room
        self.caller.location.msg_contents(msg, from_obj=self.caller)
        