from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.utils import make_iter
from world.wod20th.utils.shifter_utils import SHIFTER_RENOWN
from world.jobs.models import Job, Queue
from world.wod20th.utils.formatting import header, footer, divider
from django.utils import timezone
from evennia.objects.models import ObjectDB
from evennia import search_channel

class CmdRenown(MuxCommand):
    """
    Adjust temporary Renown values and track changes.

    Usage:
      +renown <type> [+/-]<amount>=<reason>
      +renown/list [<type>]

    Staff commands:
      +renown/rem <character>/<type> <amount>
      +renown/add <character>/<type> <amount>
      +renown/staff <character>/<type> [+/-]<amount>=<reason>
      +renown/list <character> (staff only)
      +renown/list <character>/<type> (staff only)
      +renown/approve <character>/<type> (staff only)

    Examples:
      +renown Glory +1=Led a successful raid
      +renown Honor -1=Broke a promise
      +renown Wisdom +3=Solved a complex mystery
      +renown/list           (shows all Renown changes)
      +renown/list Glory     (shows only Glory changes)
      +renown/rem Jimmy/Wisdom 1  (staff only: removes 1 Wisdom without logging)
      +renown/add Jimmy/Wisdom 1  (staff only: adds 1 Wisdom without logging)
      +renown/staff Jimmy/Wisdom +2=Learned a new Rite  (staff only: adds with logging)
      +renown/staff Jimmy/Honor -5=Birthed a Metis child  (staff only: removes with logging)
      +renown/list Jimmy     (staff only: shows all of Jimmy's Renown changes)
      +renown/list Jimmy/Glory  (staff only: shows Jimmy's Glory changes only)
      +renown/approve Jimmy/Wisdom (staff only: approves permanent Renown increase)

    This command allows you to adjust your temporary Renown values.
    When temporary Renown reaches 10, it will automatically notify staff
    to evaluate for a permanent Renown increase.

    The reason is required to track the justification for the change.
    The /rem and /add switches are for staff only and allow modifying temporary Renown
    without it showing in the character's log (for corrections).
    The /staff switch allows staff to modify a character's Renown with logging.
    The /approve switch allows staff to approve a permanent Renown increase, which 
    increases the permanent value by 1 and resets the temporary value to 0.
    """

    key = "+renown"
    aliases = ["renown"]
    locks = "cmd:all()"
    help_category = "Shifter"

    def post_to_jobs_channel(self, character_name, job_id, action_msg):
        """Post notification to the [Jobs] channel."""
        try:
            jobs_channel = search_channel("Jobs")[0]
            msg = f"[Job #{job_id}] {character_name} {action_msg}"
            jobs_channel.msg(msg)
        except Exception as e:
            # Log error but don't break the command
            print(f"Error posting to Jobs channel: {str(e)}")

    def func(self):
        """Execute the renown command."""
        # Handle list switch
        if "list" in self.switches:
            self.list_renown()
            return
            
        # Handle approve switch (staff only)
        if "approve" in self.switches:
            # Check staff permissions
            if not (self.caller.check_permstring("builders") or
                    self.caller.check_permstring("admin") or
                    self.caller.check_permstring("staff") or
                    self.caller.check_permstring("storyteller")):
                self.caller.msg("Only staff can use the /approve switch.")
                return
                
            if not self.args:
                self.caller.msg("Usage: +renown/approve <character>/<type>")
                return
                
            try:
                # Parse the input
                if '/' not in self.args:
                    self.caller.msg("Usage: +renown/approve <character>/<type>")
                    return
                    
                char_name, renown_type = self.args.split('/', 1)
                char_name = char_name.strip()
                renown_type = renown_type.strip()
                
                # Find the character
                character = None
                for obj in ObjectDB.objects.filter(db_typeclass_path__contains='typeclasses.characters'):
                    if obj.key.lower() == char_name.lower():
                        character = obj
                        break
                
                if not character:
                    self.caller.msg(f"Character '{char_name}' not found.")
                    return
                
                # Check if character is a Shifter
                splat = character.get_stat('other', 'splat', 'Splat', temp=False)
                if splat != 'Shifter':
                    self.caller.msg(f"{character.name} is not a Shifter.")
                    return
                
                # Get shifter type and valid renown types
                shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
                if not shifter_type:
                    self.caller.msg(f"{character.name} must have a Shifter Type set.")
                    return
                
                # Get valid renown types based on shifter type and tribe (for Garou)
                if shifter_type == 'Garou':
                    tribe = character.get_stat('identity', 'lineage', 'Tribe', temp=False)
                    if tribe and tribe.lower() == 'black spiral dancers':
                        valid_renown = SHIFTER_RENOWN['Garou']['Black Spiral Dancers']
                    else:
                        valid_renown = SHIFTER_RENOWN['Garou']['default']
                else:
                    valid_renown = SHIFTER_RENOWN.get(shifter_type, [])
                
                if not valid_renown:
                    self.caller.msg(f"No Renown types defined for {shifter_type}.")
                    return
                
                # Validate renown type
                renown_type = renown_type.title()
                if renown_type not in valid_renown:
                    self.caller.msg(f"Invalid Renown type. Valid types for {shifter_type} are: {', '.join(valid_renown)}")
                    return
                
                # Get current permanent and temporary values
                perm_value = character.get_stat('advantages', 'renown', renown_type, temp=False) or 0
                temp_value = character.get_stat('advantages', 'renown', renown_type, temp=True)
                if temp_value is None:
                    temp_value = 0
                
                # Check if there's enough temporary renown
                if temp_value < 10:
                    self.caller.msg(f"{character.name} only has {temp_value} temporary {renown_type} Renown. Need at least 10 to approve a permanent increase.")
                    return
                
                # Increase permanent renown by 1
                new_perm = perm_value + 1
                character.set_stat('advantages', 'renown', renown_type, new_perm, temp=False)
                
                # Reset temporary renown to 0
                character.set_stat('advantages', 'renown', renown_type, 0, temp=True)
                
                # Close the job if one exists for this renown type
                job_closed = False
                if character.attributes.has('renown_jobs'):
                    renown_jobs = character.attributes.get('renown_jobs')
                    if renown_type in renown_jobs:
                        job_id = renown_jobs[renown_type]
                        try:
                            # Find the job
                            job = Job.objects.get(id=job_id)
                            if job.status != 'closed':
                                # Add a comment
                                comment = f"Permanent {renown_type} Renown increase approved by {self.caller.name}. Permanent value increased to {new_perm}."
                                
                                # Check how comments are handled in the job system
                                try:
                                    # Option 1: If comments is a property that can be directly appended to
                                    if hasattr(job, 'comments') and isinstance(job.comments, list):
                                        job.comments.append({
                                            'text': comment,
                                            'author': self.caller.name,
                                            'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                                        })
                                    # Option 2: If there's an add_comment method
                                    elif hasattr(job, 'add_comment'):
                                        job.add_comment(self.caller.account, comment)
                                    # Option 3: Create a custom comment
                                    else:
                                        # Fall back to just storing the comment in the description
                                        job.description = f"{job.description}\n\n|y{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}|n - |c{self.caller.name}|n: {comment}"
                                except Exception as e:
                                    self.caller.msg(f"Could not add comment to job: {str(e)}")
                                    # Continue with job closure even if comment fails
                                
                                # Close the job
                                job.status = 'closed'
                                job.save()
                                job_closed = True
                                self.caller.msg(f"|yJob #{job_id} has been closed.|n")
                                # Post to the jobs channel
                                self.post_to_jobs_channel(character.name, job_id, f"job closed - Renown increase approved")
                                # Remove the job ID from the character's attribute
                                del renown_jobs[renown_type]
                                character.attributes.add('renown_jobs', renown_jobs)
                        except Job.DoesNotExist:
                            self.caller.msg(f"Could not find job #{job_id} to close.")
                        except Exception as e:
                            self.caller.msg(f"Error closing job: {str(e)}")
                
                if not job_closed:
                    self.caller.msg("No job was found to close for this renown type.")
                
                # Log the approval
                log_entry = {
                    'type': renown_type,
                    'change': 1,
                    'reason': f"Permanent Renown increased from {perm_value} to {new_perm} (Approved by {self.caller.name})",
                    'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Initialize or get the renown_log from the character's attributes
                if not character.attributes.has('renown_log'):
                    character.attributes.add('renown_log', [])
                
                # Get the current log and append the new entry
                current_log = character.attributes.get('renown_log')
                current_log.append(log_entry)
                
                # Store the updated log back in the character's attributes
                character.attributes.add('renown_log', current_log)
                
                # Notify staff of the approval
                self.caller.msg(f"|gApproved permanent {renown_type} Renown increase for {character.name}.|n")
                self.caller.msg(f"Permanent {renown_type} increased from {perm_value} to {new_perm}.")
                self.caller.msg(f"Temporary {renown_type} reset from {temp_value} to 0.")
                
                # Notify the character if they're online
                if character.sessions.count():
                    character.msg(f"|g{self.caller.name} has approved a permanent {renown_type} Renown increase for you!|n")
                    character.msg(f"Your permanent {renown_type} Renown has increased from {perm_value} to {new_perm}.")
                    character.msg(f"Your temporary {renown_type} Renown has been reset to 0.")
                
                # Post to jobs channel
                self.post_to_jobs_channel(character.name, "", f"had their {renown_type} Renown permanently increased to {new_perm} by {self.caller.name}")
                
                return
                
            except Exception as e:
                self.caller.msg(f"Error processing approval: {str(e)}")
                return
             
        # Handle staff switch (staff only, with logging)
        if "staff" in self.switches:
            # Check staff permissions
            if not (self.caller.check_permstring("builders") or
                    self.caller.check_permstring("admin") or
                    self.caller.check_permstring("staff") or
                    self.caller.check_permstring("storyteller")):
                self.caller.msg("Only staff can use the /staff switch.")
                return
                
            if not self.args or "=" not in self.args:
                self.caller.msg("Usage: +renown/staff <character>/<type> [+/-]<amount>=<reason>")
                return
                
            try:
                # Split the input into char_renown_info and reason
                char_renown_info, reason = self.args.split("=", 1)
                reason = reason.strip()
                
                if not reason:
                    self.caller.msg("You must provide a reason for the Renown change.")
                    return
                
                # Parse the character, renown type, and amount
                if '/' not in char_renown_info:
                    self.caller.msg("Usage: +renown/staff <character>/<type> [+/-]<amount>=<reason>")
                    return
                
                parts = char_renown_info.strip().split()
                if len(parts) != 2:
                    self.caller.msg("Usage: +renown/staff <character>/<type> [+/-]<amount>=<reason>")
                    return
                
                char_renown, amount_str = parts
                
                # Split the character name and renown type
                if '/' not in char_renown:
                    self.caller.msg("Usage: +renown/staff <character>/<type> [+/-]<amount>=<reason>")
                    return
                    
                char_name, renown_type = char_renown.split('/', 1)
                
                # Handle the amount with +/- prefix
                if not (amount_str.startswith('+') or amount_str.startswith('-')):
                    self.caller.msg("Amount must start with + or -")
                    return
                
                amount = int(amount_str)
                
                # Find the character
                character = None
                for obj in ObjectDB.objects.filter(db_typeclass_path__contains='typeclasses.characters'):
                    if obj.key.lower() == char_name.lower():
                        character = obj
                        break
                
                if not character:
                    self.caller.msg(f"Character '{char_name}' not found.")
                    return
                
                # Check if character is a Shifter
                splat = character.get_stat('other', 'splat', 'Splat', temp=False)
                if splat != 'Shifter':
                    self.caller.msg(f"{character.name} is not a Shifter.")
                    return
                
                # Get shifter type and valid renown types
                shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
                if not shifter_type:
                    self.caller.msg(f"{character.name} must have a Shifter Type set.")
                    return
                
                # Get valid renown types based on shifter type and tribe (for Garou)
                if shifter_type == 'Garou':
                    tribe = character.get_stat('identity', 'lineage', 'Tribe', temp=False)
                    if tribe and tribe.lower() == 'black spiral dancers':
                        valid_renown = SHIFTER_RENOWN['Garou']['Black Spiral Dancers']
                    else:
                        valid_renown = SHIFTER_RENOWN['Garou']['default']
                else:
                    valid_renown = SHIFTER_RENOWN.get(shifter_type, [])
                
                if not valid_renown:
                    self.caller.msg(f"No Renown types defined for {shifter_type}.")
                    return
                
                # Validate renown type
                renown_type = renown_type.title()
                if renown_type not in valid_renown:
                    self.caller.msg(f"Invalid Renown type. Valid types for {shifter_type} are: {', '.join(valid_renown)}")
                    return
                
                # Get current permanent and temporary values
                perm_value = character.get_stat('advantages', 'renown', renown_type, temp=False) or 0
                
                # Get temporary value specifically, defaulting to 0 if not set
                temp_value = character.get_stat('advantages', 'renown', renown_type, temp=True)
                if temp_value is None:
                    temp_value = 0
                
                # Calculate new temporary value
                new_temp = temp_value + amount
                
                # Validate the new value
                if new_temp < -10:
                    self.caller.msg("Temporary Renown cannot go below -10.")
                    return
                
                # Check if adding would exceed 10 temporary renown
                if amount > 0 and temp_value >= 10:
                    self.caller.msg(f"{character.name} already has {temp_value} temporary {renown_type} Renown, which is already at or above the maximum (10).")
                    self.caller.msg("Please use +renown/approve to increase their permanent Renown and reset their temporary Renown.")
                    return
                
                # If adding would put it over 10, cap at 10
                if amount > 0 and new_temp > 10:
                    new_temp = 10
                    amount = 10 - temp_value
                    self.caller.msg(f"Temporary Renown cannot exceed 10. Adjusting amount to {amount}.")
                
                # Update the temporary value
                character.set_stat('advantages', 'renown', renown_type, new_temp, temp=True)
                
                # Log the change with staff attribution
                log_entry = {
                    'type': renown_type,
                    'change': amount,
                    'reason': f"{reason} (By {self.caller.name})",
                    'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Initialize or get the renown_log from the character's attributes
                if not character.attributes.has('renown_log'):
                    character.attributes.add('renown_log', [])
                
                # Get the current log and append the new entry
                current_log = character.attributes.get('renown_log')
                current_log.append(log_entry)
                
                # Store the updated log back in the character's attributes
                character.attributes.add('renown_log', current_log)
                
                # Notify staff of the change
                self.caller.msg(f"{renown_type} temporary Renown {'+' if amount > 0 else ''}{amount} added to {character.name} ({reason})")
                self.caller.msg(f"New temporary {renown_type}: {new_temp} (Permanent: {perm_value})")
                
                # Notify the character if they're online
                if character.sessions.count():
                    character.msg(f"{self.caller.name} has adjusted your {renown_type} temporary Renown by {'+' if amount > 0 else ''}{amount} ({reason})")
                    character.msg(f"New temporary {renown_type}: {new_temp} (Permanent: {perm_value})")
                
                # Check if temporary value has reached 10
                if new_temp >= 10:
                    # Create a job for staff review
                    try:
                        queue, _ = Queue.objects.get_or_create(name='SHIFT')
                        job = Job.objects.create(
                            title=f"Renown Increase Evaluation - {character.name}",
                            description=f"Character: {character.name}\n"
                                      f"Shifter Type: {shifter_type}\n"
                                      f"Renown Type: {renown_type}\n"
                                      f"Current Permanent Value: {perm_value}\n"
                                      f"Current Temporary Value: {new_temp}\n\n"
                                      f"Recent Renown Changes:\n" +
                                      "\n".join([f"• {entry['timestamp']}: {entry['type']} {'+' if entry['change'] > 0 else ''}{entry['change']} - {entry['reason']}"
                                               for entry in character.db.renown_log[-5:]]) + # Show last 5 changes
                                      f"\nPlease review the recent Renown changes and approve or reject the request for a permanent increase using +renown/approve {character.name}/{renown_type}.",
                            requester=self.caller.account,
                            queue=queue,
                            status='open'
                        )
                        
                        # Store the job ID on the character for later reference
                        if not character.attributes.has('renown_jobs'):
                            character.attributes.add('renown_jobs', {})
                        
                        renown_jobs = character.attributes.get('renown_jobs')
                        renown_jobs[renown_type] = job.id
                        character.attributes.add('renown_jobs', renown_jobs)
                        
                        # Post to the jobs channel
                        self.post_to_jobs_channel(character.name, job.id, f"Renown Increase request created in SHIFT")
                        
                        self.caller.msg(f"|yA job has been created for staff to review {character.name}'s Renown for a permanent increase.|n")
                        
                        # Notify the character if they're online
                        if character.sessions.count():
                            character.msg("|yA job has been created for staff to review your Renown for a permanent increase.|n")
                    except Exception as e:
                        self.caller.msg("Error creating job for Renown review. Please notify staff.")
                        print(f"Error creating Renown review job: {str(e)}")
                
                return
                
            except ValueError as e:
                self.caller.msg(f"Invalid format: {str(e)}. Use: +renown/staff <character>/<type> [+/-]<amount>=<reason>")
                return
            except Exception as e:
                self.caller.msg(f"Error processing command: {str(e)}")
                return
            
        # Handle rem switch (staff only)
        if "rem" in self.switches:
            # Check staff permissions
            if not (self.caller.check_permstring("builders") or
                    self.caller.check_permstring("admin") or
                    self.caller.check_permstring("staff") or
                    self.caller.check_permstring("storyteller")):
                self.caller.msg("Only staff can use the /rem switch.")
                return
                
            if not self.args:
                self.caller.msg("Usage: +renown/rem <character>/<type> <amount>")
                return
                
            try:
                # Parse the input
                if '/' not in self.args:
                    self.caller.msg("Usage: +renown/rem <character>/<type> <amount>")
                    return
                    
                char_renown, amount = self.args.rsplit(' ', 1)
                char_name, renown_type = char_renown.split('/', 1)
                
                # Validate the amount
                try:
                    amount = int(amount)
                    if amount <= 0:
                        self.caller.msg("Amount must be a positive number.")
                        return
                except ValueError:
                    self.caller.msg("Amount must be a number.")
                    return
                
                # Find the character
                character = None
                for obj in ObjectDB.objects.filter(db_typeclass_path__contains='typeclasses.characters'):
                    if obj.key.lower() == char_name.lower():
                        character = obj
                        break
                
                if not character:
                    self.caller.msg(f"Character '{char_name}' not found.")
                    return
                
                # Check if character is a Shifter
                splat = character.get_stat('other', 'splat', 'Splat', temp=False)
                if splat != 'Shifter':
                    self.caller.msg(f"{character.name} is not a Shifter.")
                    return
                
                # Get shifter type and valid renown types
                shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
                if not shifter_type:
                    self.caller.msg(f"{character.name} must have a Shifter Type set.")
                    return
                
                # Get valid renown types based on shifter type and tribe (for Garou)
                if shifter_type == 'Garou':
                    tribe = character.get_stat('identity', 'lineage', 'Tribe', temp=False)
                    if tribe and tribe.lower() == 'black spiral dancers':
                        valid_renown = SHIFTER_RENOWN['Garou']['Black Spiral Dancers']
                    else:
                        valid_renown = SHIFTER_RENOWN['Garou']['default']
                else:
                    valid_renown = SHIFTER_RENOWN.get(shifter_type, [])
                
                if not valid_renown:
                    self.caller.msg(f"No Renown types defined for {shifter_type}.")
                    return
                
                # Validate renown type
                renown_type = renown_type.title()
                if renown_type not in valid_renown:
                    self.caller.msg(f"Invalid Renown type. Valid types for {shifter_type} are: {', '.join(valid_renown)}")
                    return
                
                # Get current temporary value
                temp_value = character.get_stat('advantages', 'renown', renown_type, temp=True)
                if temp_value is None:
                    temp_value = 0
                
                # Ensure we don't remove more than exists
                if amount > temp_value:
                    amount = temp_value
                
                # Calculate new value
                new_temp = temp_value - amount
                
                # Update the temporary value
                character.set_stat('advantages', 'renown', renown_type, new_temp, temp=True)
                
                # Notify staff of the change
                self.caller.msg(f"Removed {amount} temporary {renown_type} Renown from {character.name}.")
                self.caller.msg(f"New temporary {renown_type} value: {new_temp}")
                
                # Notify the character if they're online
                if character.sessions.count():
                    character.msg(f"{self.caller.name} has removed {amount} temporary {renown_type} Renown from your sheet.")
                    character.msg(f"New temporary {renown_type} value: {new_temp}")
                
                return
            
            except Exception as e:
                self.caller.msg(f"Error processing command: {str(e)}")
                return

        # Handle add switch (staff only)
        if "add" in self.switches:
            # Check staff permissions
            if not (self.caller.check_permstring("builders") or
                    self.caller.check_permstring("admin") or
                    self.caller.check_permstring("staff") or
                    self.caller.check_permstring("storyteller")):
                self.caller.msg("Only staff can use the /add switch.")
                return
                
            if not self.args:
                self.caller.msg("Usage: +renown/add <character>/<type> <amount>")
                return
                
            try:
                # Parse the input
                if '/' not in self.args:
                    self.caller.msg("Usage: +renown/add <character>/<type> <amount>")
                    return
                    
                char_renown, amount = self.args.rsplit(' ', 1)
                char_name, renown_type = char_renown.split('/', 1)
                
                # Validate the amount
                try:
                    amount = int(amount)
                    if amount <= 0:
                        self.caller.msg("Amount must be a positive number.")
                        return
                except ValueError:
                    self.caller.msg("Amount must be a number.")
                    return
                
                # Find the character
                character = None
                for obj in ObjectDB.objects.filter(db_typeclass_path__contains='typeclasses.characters'):
                    if obj.key.lower() == char_name.lower():
                        character = obj
                        break
                
                if not character:
                    self.caller.msg(f"Character '{char_name}' not found.")
                    return
                
                # Check if character is a Shifter
                splat = character.get_stat('other', 'splat', 'Splat', temp=False)
                if splat != 'Shifter':
                    self.caller.msg(f"{character.name} is not a Shifter.")
                    return
                
                # Get shifter type and valid renown types
                shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
                if not shifter_type:
                    self.caller.msg(f"{character.name} must have a Shifter Type set.")
                    return
                
                # Get valid renown types based on shifter type and tribe (for Garou)
                if shifter_type == 'Garou':
                    tribe = character.get_stat('identity', 'lineage', 'Tribe', temp=False)
                    if tribe and tribe.lower() == 'black spiral dancers':
                        valid_renown = SHIFTER_RENOWN['Garou']['Black Spiral Dancers']
                    else:
                        valid_renown = SHIFTER_RENOWN['Garou']['default']
                else:
                    valid_renown = SHIFTER_RENOWN.get(shifter_type, [])
                
                if not valid_renown:
                    self.caller.msg(f"No Renown types defined for {shifter_type}.")
                    return
                
                # Validate renown type
                renown_type = renown_type.title()
                if renown_type not in valid_renown:
                    self.caller.msg(f"Invalid Renown type. Valid types for {shifter_type} are: {', '.join(valid_renown)}")
                    return
                
                # Get current permanent and temporary values
                perm_value = character.get_stat('advantages', 'renown', renown_type, temp=False) or 0
                temp_value = character.get_stat('advantages', 'renown', renown_type, temp=True)
                if temp_value is None:
                    temp_value = 0
                
                # Check if adding would exceed 10 temporary renown
                if temp_value >= 10:
                    self.caller.msg(f"{character.name} already has {temp_value} temporary {renown_type} Renown, which is already at or above the maximum (10).")
                    self.caller.msg("Please use +renown/approve to increase their permanent Renown and reset their temporary Renown.")
                    return
                
                # Calculate new value - cap at 10
                new_temp = min(temp_value + amount, 10)
                
                # Adjust amount if it would exceed 10
                if temp_value + amount > 10:
                    amount = 10 - temp_value
                    self.caller.msg(f"Temporary Renown cannot exceed 10. Adjusting amount to {amount}.")
                
                # Update the temporary value
                character.set_stat('advantages', 'renown', renown_type, new_temp, temp=True)
                
                # Notify staff of the change
                self.caller.msg(f"Added {amount} temporary {renown_type} Renown to {character.name}.")
                self.caller.msg(f"New temporary {renown_type} value: {new_temp}")
                
                # Notify the character if they're online
                if character.sessions.count():
                    character.msg(f"{self.caller.name} has added {amount} temporary {renown_type} Renown to your sheet.")
                    character.msg(f"New temporary {renown_type} value: {new_temp}")
                
                # Check if temporary value has reached 10
                if new_temp >= 10:
                    # Create a job for staff review
                    try:
                        queue, _ = Queue.objects.get_or_create(name='SHIFT')
                        job = Job.objects.create(
                            title=f"Renown Increase Evaluation - {character.name}",
                            description=f"Character: {character.name}\n"
                                      f"Shifter Type: {shifter_type}\n"
                                      f"Renown Type: {renown_type}\n"
                                      f"Current Permanent Value: {perm_value}\n"
                                      f"Current Temporary Value: {new_temp}\n\n"
                                      f"Recent Renown Changes:\n" +
                                      "\n".join([f"• {entry['timestamp']}: {entry['type']} {'+' if entry['change'] > 0 else ''}{entry['change']} - {entry['reason']}"
                                               for entry in character.db.renown_log[-5:]]) + # Show last 5 changes
                                      f"\nPlease review the recent Renown changes and approve or reject the request for a permanent increase using +renown/approve {character.name}/{renown_type}.",
                            requester=self.caller.account,
                            queue=queue,
                            status='open'
                        )
                        
                        # Store the job ID on the character for later reference
                        if not character.attributes.has('renown_jobs'):
                            character.attributes.add('renown_jobs', {})
                        
                        renown_jobs = character.attributes.get('renown_jobs')
                        renown_jobs[renown_type] = job.id
                        character.attributes.add('renown_jobs', renown_jobs)
                        
                        # Post to the jobs channel
                        self.post_to_jobs_channel(character.name, job.id, f"Renown Increase request created in SHIFT")
                        
                        self.caller.msg(f"|yA job has been created for staff to review {character.name}'s Renown for a permanent increase.|n")
                        
                        # Notify the character if they're online
                        if character.sessions.count():
                            character.msg("|yA job has been created for staff to review your Renown for a permanent increase.|n")
                    except Exception as e:
                        self.caller.msg("Error creating job for Renown review. Please notify staff.")
                        print(f"Error creating Renown review job: {str(e)}")
                
                return
            
            except Exception as e:
                self.caller.msg(f"Error processing command: {str(e)}")
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

        # Get current permanent and temporary values - ensure we properly handle temp values
        perm_value = self.caller.get_stat('advantages', 'renown', renown_type, temp=False) or 0
        
        # Get temporary value specifically, defaulting to 0 if not set
        temp_value = self.caller.get_stat('advantages', 'renown', renown_type, temp=True)
        if temp_value is None:
            temp_value = 0

        # Check if adding and already at 10
        if amount > 0 and temp_value >= 10:
            self.caller.msg(f"You already have {temp_value} temporary {renown_type} Renown, which is at or above the maximum (10).")
            self.caller.msg("You must wait for staff to review and approve a permanent Renown increase.")
            return

        # Calculate new temporary value - cap at 10 if increasing
        if amount > 0:
            new_temp = min(temp_value + amount, 10)
            # Adjust amount if it would exceed 10
            if temp_value + amount > 10:
                amount = 10 - temp_value
                self.caller.msg(f"Temporary Renown cannot exceed 10. Adjusting amount to {amount}.")
        else:
            new_temp = temp_value + amount

        # Validate the new value for negative limit
        if new_temp < -10:
            self.caller.msg("Temporary Renown cannot go below -10.")
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
                queue, _ = Queue.objects.get_or_create(name='SHIFT')
                job = Job.objects.create(
                    title=f"Renown Increase Evaluation - {self.caller.name}",
                    description=f"Character: {self.caller.name}\n"
                              f"Shifter Type: {shifter_type}\n"
                              f"Renown Type: {renown_type}\n"
                              f"Current Permanent Value: {perm_value}\n"
                              f"Current Temporary Value: {new_temp}\n\n"
                              f"Recent Renown Changes:\n" +
                              "\n".join([f"• {entry['timestamp']}: {entry['type']} {'+' if entry['change'] > 0 else ''}{entry['change']} - {entry['reason']}"
                                       for entry in self.caller.db.renown_log[-5:]]) + # Show last 5 changes
                              f"\nPlease review the recent Renown changes and approve or reject the request for a permanent increase using |w+renown/approve {self.caller.name}/{renown_type}|n.",
                    requester=self.caller.account,
                    queue=queue,
                    status='open'
                )
                
                # Store the job ID on the character for later reference
                if not self.caller.attributes.has('renown_jobs'):
                    self.caller.attributes.add('renown_jobs', {})
                
                renown_jobs = self.caller.attributes.get('renown_jobs')
                renown_jobs[renown_type] = job.id
                self.caller.attributes.add('renown_jobs', renown_jobs)
                
                # Post to the jobs channel
                self.post_to_jobs_channel(self.caller.name, job.id, f"Renown Increase request created in SHIFT")
                
                self.caller.msg("|yA job has been created for staff to review your Renown for a permanent increase.|n")
            except Exception as e:
                self.caller.msg("Error creating job for Renown review. Please notify staff.")
                print(f"Error creating Renown review job: {str(e)}")

    def list_renown(self):
        """Display the Renown history."""
        # Check if this is a staff request to view another character's renown
        if self.args:
            # Check if the format is with a slash (jimmy/glory) or without (just jimmy)
            if '/' in self.args:
                # Format: jimmy/glory
                char_name, renown_type = self.args.split('/', 1)
                char_name = char_name.strip()
                renown_type = renown_type.strip() if renown_type.strip() else None
            else:
                # Format: just jimmy
                char_name = self.args.strip()
                renown_type = None
            
            # Check if this is trying to view someone else's renown
            if char_name.lower() != self.caller.key.lower():
                # Check staff permissions
                if not (self.caller.check_permstring("builders") or
                        self.caller.check_permstring("admin") or
                        self.caller.check_permstring("staff") or
                        self.caller.check_permstring("storyteller")):
                    self.caller.msg("Only staff can check another character's renown history.")
                    return
                
                # Find the character
                character = None
                for obj in ObjectDB.objects.filter(db_typeclass_path__contains='typeclasses.characters'):
                    if obj.key.lower() == char_name.lower():
                        character = obj
                        break
                
                if not character:
                    self.caller.msg(f"Character '{char_name}' not found.")
                    return
                
                # Check if character is a Shifter
                splat = character.get_stat('other', 'splat', 'Splat', temp=False)
                if splat != 'Shifter':
                    self.caller.msg(f"{character.name} is not a Shifter.")
                    return
                
                # Get shifter type
                shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
                if not shifter_type:
                    self.caller.msg(f"{character.name} must have a Shifter Type set.")
                    return
                
                # Get valid renown types based on shifter type and tribe (for Garou)
                if shifter_type == 'Garou':
                    tribe = character.get_stat('identity', 'lineage', 'Tribe', temp=False)
                    if tribe and tribe.lower() == 'black spiral dancers':
                        valid_renown = SHIFTER_RENOWN['Garou']['Black Spiral Dancers']
                    else:
                        valid_renown = SHIFTER_RENOWN['Garou']['default']
                else:
                    valid_renown = SHIFTER_RENOWN.get(shifter_type, [])
                
                # Get the log entries
                if not character.attributes.has('renown_log'):
                    character.attributes.add('renown_log', [])
                    log_entries = []
                else:
                    log_entries = character.attributes.get('renown_log')
                    if renown_type:
                        log_entries = [entry for entry in log_entries if entry['type'].lower() == renown_type.lower()]
                
                if not log_entries:
                    if renown_type:
                        self.caller.msg(f"No Renown history found for {character.name}'s {renown_type}.")
                    else:
                        self.caller.msg(f"No Renown history found for {character.name}.")
                    return
                
                # Start building the output
                title = f"|yRenown History - {character.name}|n"
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
                        perm = character.get_stat('advantages', 'renown', r_type, temp=False) or 0
                        # Ensure we properly handle temp values for display
                        temp = character.get_stat('advantages', 'renown', r_type, temp=True)
                        if temp is None:
                            temp = 0
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
                return
            
        # This is either viewing own renown or no args were given
        
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

        # Get the log entries - if we're still here, this is the caller's own renown
        renown_type = self.args.strip() if self.args and '/' not in self.args else None
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
                # Ensure we properly handle temp values for display
                temp = self.caller.get_stat('advantages', 'renown', r_type, temp=True)
                if temp is None:
                    temp = 0
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