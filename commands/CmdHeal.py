from evennia import Command
from world.wod20th.utils.damage import apply_damage_or_healing, format_status, format_damage

class CmdHeal(Command):
    """
    Heal damage from yourself or another character.
    
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
            self.target_name, self.damage_input = args
        else:
            self.target_name, self.damage_input = None, args[0]
        self.target_name = self.target_name.strip() if self.target_name else None
        self.damage_input = self.damage_input.strip()

    def func(self):
        if not self.damage_input:
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
            healing = int(self.damage_input[:-1])
            damage_type = self.damage_input[-1].lower()
            if damage_type not in ['b', 'l', 'a']:
                raise ValueError    
            if healing <= 0:
                raise ValueError
        except ValueError:
            self.caller.msg("Invalid healing input. Use a positive number followed by b, l, or a (e.g., 3l, 2b, 4a).")
            return

        damage_type_full = {'b': 'bashing', 'l': 'lethal', 'a': 'aggravated'}[damage_type]

        # Apply healing (negative damage)
        apply_damage_or_healing(target, -healing, damage_type_full)

        # Get the green gradient_name of th target
        target_gradient = target.db.gradient_name or target.key

        msg = f"|gHEAL> |n{target_gradient} heals |g{healing}|n |y{damage_type_full}|n.\n"
        msg += f"|gHEAL> |n{format_damage(target)} Status: {format_status(target)}"
        
        # Send messages and emit to room
        self.caller.location.msg_contents(msg, from_obj=self.caller)
        