from evennia import default_cmds
from evennia.utils import evtable
from evennia.utils.logger import log_info

class CmdSpendGain(default_cmds.MuxCommand):
    """
    Spend or gain pool resources.

    Usage:
      +spend <pool>=<amount>[/<reason>]
      +gain <pool>=<amount>[/<reason>]

    Examples:
      +spend willpower=1/Drive check
      +spend blood=1/Celerity
      +gain rage=1/hit in combat
      +gain gnosis=2/meditated

    This command allows you to spend or gain points from your character's
    pool resources (such as blood, rage, gnosis, willpower, etc.).
    You can optionally provide a reason for the change.
    """

    key = "+spend"
    aliases = ["+gain"]
    locks = "cmd:all()"
    help_category = "RP Commands"

    def func(self):
        caller = self.caller
        cmd = self.cmdstring.lower()
        args = self.args.strip()

        if not args or "=" not in args:
            caller.msg("Usage: +spend/+gain <pool>=<amount>[/<reason>]")
            return

        pool, amount_reason = args.split("=", 1)
        pool = pool.strip().lower()
        
        if "/" in amount_reason:
            amount, reason = amount_reason.split("/", 1)
        else:
            amount, reason = amount_reason, ""
        
        try:
            amount = int(amount.strip())
        except ValueError:
            caller.msg("The amount must be a number.")
            return

        if amount <= 0:
            caller.msg("The amount must be a positive number.")
            return

        # Get both permanent and temporary values
        pool_data = caller.db.stats.get('pools', {}).get('dual', {}).get(pool.capitalize(), {})
        if not pool_data:
            caller.msg(f"Invalid pool: {pool}")
            return

        current_temp = pool_data.get('temp', 0)
        max_value = pool_data.get('perm', 0)

        if cmd == "+spend":
            if current_temp < amount:
                caller.msg(f"You don't have enough {pool}. Current {pool}: {current_temp}")
                return
            new_value = current_temp - amount
            action = "spent"
        else:  # +gain
            new_value = min(current_temp + amount, max_value)  # Can't exceed permanent value
            if new_value == current_temp and new_value == max_value:
                caller.msg(f"You are already at maximum {pool} ({max_value}).")
                return
            action = "gained"

        # Update the temporary value
        caller.db.stats['pools']['dual'][pool.capitalize()]['temp'] = new_value

        # Prepare the message
        msg = f"You have {action} {amount} point{'s' if amount > 1 else ''} of {pool}."
        if reason:
            msg += f" Reason: {reason}"
        msg += f" New {pool} value: {new_value}/{max_value}"

        caller.msg(msg)

        # Log the change
        log_msg = f"{caller.key} {action} {amount} {pool}"
        if reason:
            log_msg += f" for: {reason}"
        log_msg += f" (New value: {new_value}/{max_value})"
        self.log_action(log_msg)

    def log_action(self, message):
        # Log to the server's info channel
        log_info(message)