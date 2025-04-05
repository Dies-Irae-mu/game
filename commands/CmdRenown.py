from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.utils import make_iter
from world.wod20th.utils.shifter_utils import SHIFTER_RENOWN
from world.jobs.models import Job, Queue
from world.wod20th.utils.formatting import header, footer, divider
from django.utils import timezone

class CmdRenown(MuxCommand):
    """
    Adjust temporary Renown values and track changes.

    Usage:
      +renown <type> [+/-]<amount>=<reason>
      +renown/list [<type>]

    Examples:
      +renown Glory +1=Led a successful raid
      +renown Honor -1=Broke a promise
      +renown Wisdom +3=Solved a complex mystery
      +renown/list           (shows all Renown changes)
      +renown/list Glory     (shows only Glory changes)

    This command allows you to adjust your temporary Renown values.
    When temporary Renown reaches 10, it will automatically notify staff
    to evaluate for a permanent Renown increase.

    The reason is required to track the justification for the change.
    """

    key = "+renown"
    aliases = ["renown"]
    locks = "cmd:all()"
    help_category = "Shifter"

    def func(self):
        """Execute the renown command."""
        # Handle list switch
        if "list" in self.switches:
            self.list_renown()
            return

        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +renown <type> [+/-]<amount>=<reason>")
            return

        # Split the input into renown_info and reason
        renown_info, reason = self.args.split("=", 1)
        reason = reason.strip()

        if not reason:
            self.caller.msg("You must provide a reason for the Renown change.")
            return

        # Check if character is a Shifter
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
        if splat != 'Shifter':
            self.caller.msg("Only Shifters can use this command.")
            return

        # Get shifter type and valid renown types
        shifter_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
        if not shifter_type:
            self.caller.msg("You must set your Shifter Type before using this command.")
            return

        # Get valid renown types based on shifter type and tribe (for Garou)
        if shifter_type == 'Garou':
            tribe = self.caller.get_stat('identity', 'lineage', 'Tribe', temp=False)
            if tribe and tribe.lower() == 'black spiral dancers':
                valid_renown = SHIFTER_RENOWN['Garou']['Black Spiral Dancers']
            else:
                valid_renown = SHIFTER_RENOWN['Garou']['default']
        else:
            valid_renown = SHIFTER_RENOWN.get(shifter_type, [])

        if not valid_renown:
            self.caller.msg(f"No Renown types defined for {shifter_type}.")
            return

        # Parse the renown type and amount
        try:
            parts = renown_info.strip().split()
            if len(parts) != 2:
                raise ValueError
            renown_type, amount = parts
            
            # Handle the amount with +/- prefix
            if not (amount.startswith('+') or amount.startswith('-')):
                self.caller.msg("Amount must start with + or -")
                return
            
            amount = int(amount)
        except ValueError:
            self.caller.msg("Invalid format. Use: +renown <type> [+/-]<amount>=<reason>")
            return

        # Validate renown type
        renown_type = renown_type.title()
        if renown_type not in valid_renown:
            self.caller.msg(f"Invalid Renown type. Valid types for {shifter_type} are: {', '.join(valid_renown)}")
            return

        # Get current permanent and temporary values
        perm_value = self.caller.get_stat('advantages', 'renown', renown_type, temp=False) or 0
        temp_value = self.caller.get_stat('advantages', 'renown', renown_type, temp=True) or 0

        # Calculate new temporary value
        new_temp = temp_value + amount

        # Validate the new value
        if new_temp < 0:
            self.caller.msg("Temporary Renown cannot go below 0.")
            return

        # Update the temporary value
        self.caller.set_stat('advantages', 'renown', renown_type, new_temp, temp=True)

        # Log the change
        log_entry = {
            'type': renown_type,
            'change': amount,
            'reason': reason,
            'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Initialize or get the renown_log from the character's attributes
        if not self.caller.attributes.has('renown_log'):
            self.caller.attributes.add('renown_log', [])
        
        # Get the current log and append the new entry
        current_log = self.caller.attributes.get('renown_log')
        current_log.append(log_entry)
        
        # Store the updated log back in the character's attributes
        self.caller.attributes.add('renown_log', current_log)

        # Notify the player of the change
        self.caller.msg(f"{renown_type} temporary Renown {'+' if amount > 0 else ''}{amount} ({reason})")
        self.caller.msg(f"New temporary {renown_type}: {new_temp} (Permanent: {perm_value})")

        # Check if temporary value has reached 10
        if new_temp >= 10:
            # Create a job for staff review
            try:
                queue, _ = Queue.objects.get_or_create(name='REQ')
                job = Job.objects.create(
                    title=f"Renown Increase Evaluation - {self.caller.name}",
                    description=f"Character: {self.caller.name}\n"
                              f"Shifter Type: {shifter_type}\n"
                              f"Renown Type: {renown_type}\n"
                              f"Current Permanent Value: {perm_value}\n"
                              f"Current Temporary Value: {new_temp}\n\n"
                              f"Recent Renown Changes:\n" +
                              "\n".join([f"• {entry['timestamp']}: {entry['type']} {'+' if entry['change'] > 0 else ''}{entry['change']} - {entry['reason']}"
                                       for entry in self.caller.db.renown_log[-5:]]),  # Show last 5 changes
                    requester=self.caller.account,
                    queue=queue,
                    status='open'
                )
                self.caller.msg("|yA job has been created for staff to review your Renown for a permanent increase.|n")
            except Exception as e:
                self.caller.msg("Error creating job for Renown review. Please notify staff.")
                print(f"Error creating Renown review job: {str(e)}")

    def list_renown(self):
        """Display the Renown history."""
        # Check if character is a Shifter
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
        if splat != 'Shifter':
            self.caller.msg("Only Shifters can use this command.")
            return

        # Get shifter type
        shifter_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
        if not shifter_type:
            self.caller.msg("You must set your Shifter Type before using this command.")
            return

        # Get valid renown types based on shifter type and tribe (for Garou)
        if shifter_type == 'Garou':
            tribe = self.caller.get_stat('identity', 'lineage', 'Tribe', temp=False)
            if tribe and tribe.lower() == 'black spiral dancers':
                valid_renown = SHIFTER_RENOWN['Garou']['Black Spiral Dancers']
            else:
                valid_renown = SHIFTER_RENOWN['Garou']['default']
        else:
            valid_renown = SHIFTER_RENOWN.get(shifter_type, [])

        # Get the log entries
        renown_type = self.args.strip() if self.args else None
        log_entries = self.get_renown_log(renown_type)

        if not log_entries:
            if renown_type:
                self.caller.msg(f"No Renown history found for {renown_type}.")
            else:
                self.caller.msg("No Renown history found.")
            return

        # Start building the output
        title = f"|yRenown History - {self.caller.name}|n"
        if renown_type:
            title += f" ({renown_type})"
        

        output = [
            header(title, width=78),
            ""  # Blank line after header
        ]

        # Group entries by Renown type
        entries_by_type = {}
        for entry in log_entries:
            r_type = entry['type']
            if r_type not in entries_by_type:
                entries_by_type[r_type] = []
            entries_by_type[r_type].append(entry)

        # Display current values for each type
        output.append("|cCurrent Renown Values:|n")
        for r_type in valid_renown:
            if not renown_type or r_type.lower() == renown_type.lower():
                perm = self.caller.get_stat('advantages', 'renown', r_type, temp=False) or 0
                temp = self.caller.get_stat('advantages', 'renown', r_type, temp=True) or 0
                output.append(f"{r_type}: Permanent {perm}, Temporary {temp}")
        
        output.append("")  # Blank line before history

        # Display history for each type
        for r_type, entries in sorted(entries_by_type.items()):
            if not renown_type or r_type.lower() == renown_type.lower():
                output.append(divider(f"{r_type} History", width=78))
                
                # Sort entries by timestamp, most recent first
                entries.sort(key=lambda x: x['timestamp'], reverse=True)
                
                for entry in entries:
                    change = entry['change']
                    change_str = f"+{change}" if change > 0 else str(change)
                    output.append(f"|w{entry['timestamp']}|n: {change_str} - {entry['reason']}")
                output.append("")  # Blank line between types

        output.append(footer(width=78))
        
        # Send the formatted output to the player
        self.caller.msg("\n".join(output))

    def get_renown_log(self, renown_type=None):
        """Get the renown log, optionally filtered by type."""
        # Initialize or get the renown_log from the character's attributes
        if not self.caller.attributes.has('renown_log'):
            self.caller.attributes.add('renown_log', [])
            return []  # Return empty list if no history exists
        
        # Get the current log
        current_log = self.caller.attributes.get('renown_log')
        
        if renown_type:
            return [entry for entry in current_log if entry['type'].lower() == renown_type.lower()]
        return current_log 