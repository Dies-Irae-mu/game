from evennia import CmdSet
from django.db import models, transaction, connection
from evennia.utils import create, evtable, logger
from evennia.comms.models import ChannelDB
from evennia.commands.default.muxcommand import MuxCommand
from world.jobs.models import Job, JobTemplate, Queue, JobAttachment, ArchivedJob, Queue
from evennia.utils.search import search_account, search_object
from django.db import models, transaction, connection
from evennia.utils.utils import crop
from evennia.utils.ansi import ANSIString
from world.wod20th.utils.ansi_utils import wrap_ansi
from world.wod20th.utils.formatting import header, footer, divider, format_stat
from textwrap import fill
from django.utils import timezone
from django.db.models import Max, F
import json
import copy
from evennia.help.models import HelpEntry
from world.equipment.models import Equipment, PlayerInventory, InventoryItem
from evennia.accounts.models import AccountDB

class CmdJobs(MuxCommand):
    """
    View and manage jobs
    The following aliases are available: +requests, +request, +myjob, +job, +myjobs
    Usage:
      +jobs                      - List all jobs
      +myjobs                    - List jobs you created or are assigned to
      +jobs/mine                 - List jobs assigned to you (staff only)
      +jobs <#>                  - View details of a specific job
      +jobs/create <category>/<title>=<text> [= <template>] <args>
      +jobs/comment <#>=<text>   - Add a comment to a job
      +jobs/close <#>           - Close a job
      +jobs/reopen <#>          - Reopen an archived job
      +jobs/addplayer <#>=<player>
      +jobs/removeplayer <#>=<player>
      +jobs/assign <#>=<staff>
      +jobs/claim <#>
      +jobs/unclaim <#>
      +jobs/approve <#>
      +jobs/reject <#>
      +jobs/attach <#>=<object name>[:<arg>]
      +jobs/remove <#>=<object name>
      +jobs/list [queue <queue_name>] [all]
      +jobs/reassign <#>=<new assignee>
      +jobs/queue/view <queue name>
      +jobs/list_with_object <object_name>
      +jobs/archive
      +jobs/archive <#>
      +jobs/complete <#>=<reason>
      +jobs/cancel <#>=<reason>
      +jobs/clear_archive        - Clear all archived jobs and reset job numbers (Admin only)

    Categories:
      REQ    - General requests
      BUG    - Bug reports
      PLOT   - Plot-related requests
      BUILD  - Building/room requests
      MISC   - Miscellaneous requests
      XP     - XP requests
      PRP    - PRP requests
      VAMP   - Vampire requests
      SHIFT  - Shifter requests
      MORT   - Mortal requests
      POSS   - Possessed requests
      COMP   - Companion requests
      LING   - Changeling requests
      MAGE   - Mage requests
      EQUIP  - Equipment requests
    """

    key = "+jobs"
    aliases = ["+requests", "+request", "myjobs", "myjob", "+job", "+myjobs"]
    locks = "cmd:all()"
    help_category = "Utility Commands"
    
    # Add these properties to help with help system registration
    auto_help = True
    help_entry_tags = ["jobs", "requests", "admin"]
    
    def get_help(self, caller, cmdset):
        """
        Returns the help string for this command.
        """
        return self.__doc__

    def func(self):
        if not self.args and not self.switches:
            if self.cmdstring == "+myjobs":
                self.list_my_jobs()
            else:
                self.list_jobs()
        elif self.args and not self.switches:
            # Check if this is a job creation request (contains =)
            if "=" in self.args:
                self.create_job_from_simple_syntax()
            else:
                self.view_job()
        elif "archive" in self.switches:
            self.view_archived_job()
        elif "create" in self.switches:
            self.create_job()
        elif "comment" in self.switches:
            self.add_comment()
        elif "close" in self.switches:
            self.close_job()
        elif "reopen" in self.switches:
            self.reopen_job()
        elif "addplayer" in self.switches:
            self.add_player()
        elif "removeplayer" in self.switches:
            self.remove_player()
        elif "assign" in self.switches:
            self.assign_job()
        elif "claim" in self.switches:
            self.claim_job()
        elif "unclaim" in self.switches:
            self.unclaim_job()
        elif "approve" in self.switches:
            self.approve_job()
        elif "reject" in self.switches:
            self.reject_job()
        elif "attach" in self.switches:
            self.attach_object()
        elif "remove" in self.switches:
            self.remove_object()
        elif "list" in self.switches:
            self.list_jobs()
        elif "mine" in self.switches:
            self.list_assigned_jobs()
        elif "reassign" in self.switches:
            self.reassign_job()
        elif "queue/view" in self.switches:
            self.view_queue_jobs()
        elif "list_with_object" in self.switches:
            self.list_jobs_with_object()
        elif "complete" in self.switches:
            self.complete_job()
        elif "cancel" in self.switches:
            self.cancel_job()
        elif "clear_archive" in self.switches:
            self.clear_archive()
        else:
            self.caller.msg("Invalid switch. See help +jobs for usage.")

    def list_jobs(self):
        if self.caller.check_permstring("Admin"):
            jobs = Job.objects.filter(status__in=['open', 'claimed']).order_by('-created_at')
        else:
            jobs = Job.objects.filter(
                models.Q(requester=self.caller.account) |
                models.Q(participants=self.caller.account),
                status__in=['open', 'claimed']
            ).distinct().order_by('-created_at')

        if not jobs:
            self.caller.msg("You have no open jobs.")
            return

        # Define column widths
        col_widths = {
            'job_id': 6,    # "Job # "
            'queue': 10,    # "Queue     "
            'title': 25,    # "Job Title                "
            'originator': 12, # "Originator   "
            'assignee': 12,   # "Assignee     "
            'status': 8      # "Status   "
        }

        output = header("Dies Irae Jobs", width=78, fillchar="|r-|n") + "\n"
        
        # Create the header row with fixed column widths
        header_row = (
            f"|cJob #".ljust(col_widths['job_id']) +
            f"Queue".ljust(col_widths['queue']) +
            f"Job Title".ljust(col_widths['title']) +
            f"Originator".ljust(col_widths['originator']) +
            f"Assignee".ljust(col_widths['assignee']) +
            f"Status|n"
        )
        output += header_row + "\n"
        output += ANSIString("|r" + "-" * 78 + "|n") + "\n"

        # Add each job as a row with proper column spacing
        for job in jobs:
            assignee = job.assignee.username if job.assignee else "-----"
            originator = job.requester.username if job.requester else "-----"
            
            # Check if job has been viewed by this user
            unread = job.is_updated_since_last_view(self.caller.account)
            title_marker = "|r*|n " if unread else "  "
            
            # Format each field with proper width
            job_id = str(job.id).ljust(col_widths['job_id'])
            queue = crop(job.queue.name, width=col_widths['queue']-2).ljust(col_widths['queue'])  # -2 for spacing
            title = title_marker + crop(job.title, width=col_widths['title']-2)  # -2 for marker
            title = title.ljust(col_widths['title'])
            originator = crop(originator, width=col_widths['originator']-2).ljust(col_widths['originator'])
            assignee = crop(assignee, width=col_widths['assignee']-2).ljust(col_widths['assignee'])
            status = crop(job.status, width=col_widths['status'])
            
            # Combine all fields with proper spacing
            row = f"{job_id}{queue}{title}{originator}{assignee}{status}"
            output += row + "\n"

        output += footer(width=78, fillchar="|r-|n")
        self.caller.msg(output)

    def view_job(self):
        try:
            job_id = int(self.args)
            job = Job.objects.get(id=job_id, archive_id__isnull=True)
            
            if not self.caller.check_permstring("Admin") and job.requester != self.caller.account and job.assignee != self.caller.account and self.caller.account not in job.participants.all():
                self.caller.msg("You don't have permission to view this job.")
                return

            # Mark the job as viewed by this account using mark_viewed
            job.mark_viewed(self.caller.account)

            output = header(f"Job {job.id}", width=78, fillchar="|r-|n") + "\n"
            output += f"|cTitle:|n {job.title}\n"
            output += f"|cStatus:|n {job.status}\n"
            output += f"|cRequester:|n {job.requester.username}\n"
            output += f"|cAssignee:|n {job.assignee.username if job.assignee else '-----'}\n"
            output += f"|cQueue:|n {job.queue.name}\n"
            output += f"|cCreated At:|n {job.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            output += f"|cClosed At:|n {job.closed_at.strftime('%Y-%m-%d %H:%M:%S') if job.closed_at else '-----'}\n"
            
            # Add participants list including requester
            participants = list(job.participants.all())
            # Add requester if not already in participants
            if job.requester not in participants:
                participants.insert(0, job.requester)  # Add requester at the start of the list
            
            if participants:
                output += f"|cParticipants:|n {', '.join(p.username for p in participants)}\n"
            else:
                output += "|cParticipants:|n None\n"
            
            attached_objects = JobAttachment.objects.filter(job=job)
            if attached_objects:
                output += "|cAttached Objects:|n " + ", ".join([obj.object.key for obj in attached_objects]) + "\n"
            else:
                output += "|cAttached Objects:|n None\n"
            
            output += divider("Description", width=78, fillchar="-", color="|r", text_color="|c") + "\n"
            
            # Handle description text without wrapping
            paragraphs = [p.strip() for p in job.description.split('\n\n') if p.strip()]
            for i, paragraph in enumerate(paragraphs):
                output += paragraph + "\n"
                if i < len(paragraphs) - 1:
                    output += "\n"
            
            if job.comments:
                output += divider("Comments", width=78, fillchar="-", color="|r", text_color="|c") + "\n"
                for comment in job.comments:
                    output += f"|c{comment['author']} [{comment['created_at']}]:|n\n"
                    output += comment['text'] + "\n\n"
            
            output += divider("", width=78, fillchar="-", color="|r") + "\n"
            self.caller.msg(output)
        except ValueError:
            self.caller.msg("Invalid job ID.")
        except Job.DoesNotExist:
            self.caller.msg(f"Job #{job_id} not found or is archived. Use +jobs/archive {job_id} to view archived jobs.")

    def determine_category(self, specified_category=None):
        """
        Determine the job category based on character splat or specified category.
        
        Args:
            specified_category (str, optional): Category explicitly specified by the user
            
        Returns:
            str: The determined category code
        """
        # If a category was explicitly specified, use it
        if specified_category:
            return specified_category  # Return as-is, case conversion happens later

        # For non-staff, determine category based on splat
        if not self.caller.check_permstring("Admin"):
            stats = self.caller.db.stats
            if stats and 'other' in stats and 'splat' in stats['other']:
                splat = stats['other']['splat'].get('Splat', {}).get('perm', '')
                
                # Map splat to category
                splat_category_map = {
                    'Mage': 'MAGE',
                    'Vampire': 'VAMP',
                    'Changeling': 'LING',
                    'Companion': 'COMP',
                    'Mortal': 'MORT',
                    'Possessed': 'POSS',
                    'Shifter': 'SHIFT',
                }
                
                # Handle Mortal+ subtypes
                if splat == 'Mortal+':
                    if 'identity' in stats and 'lineage' in stats['identity']:
                        mortal_type = stats['identity']['lineage'].get('Type', {}).get('perm', '')
                        mortal_plus_map = {
                            'Kinain': 'LING',
                            'Ghoul': 'VAMP',
                            'Kinfolk': 'SHIFT',
                            'Sorcerer': 'MAGE',
                        }
                        return mortal_plus_map.get(mortal_type, 'MORT')
                else:
                    category = splat_category_map.get(splat)
                    if category:
                        return category

        # Default category if nothing else matched
        return "REQ"

    def create_job_from_simple_syntax(self):
        """Handle simplified job creation with automatic category detection."""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +jobs <title>=<description>")
            return

        title, description = self.args.split("=", 1)
        title = title.strip()
        description = description.strip()

        if not title or not description:
            self.caller.msg("Both title and description are required.")
            return

        # Get the appropriate category and convert to uppercase
        category = self.determine_category().upper()

        try:
            # Get or create the queue for this category
            queue, created = Queue.objects.get_or_create(
                name=category,
                defaults={'automatic_assignee': None}
            )

            # Create the job
            job = Job.objects.create(
                title=title,
                description=description,
                requester=self.caller.account,
                queue=queue,
                status='open'
            )

            # Notify the creator
            self.caller.msg(f"|gJob '{title}' created with ID {job.id} in category {category}.|n")
            
            # Post to the jobs channel for staff notification
            self.post_to_jobs_channel(self.caller.name, job.id, f"created in {category}")

            # Handle automatic assignment if configured
            if queue.automatic_assignee:
                job.assignee = queue.automatic_assignee
                job.status = 'claimed'
                job.save()
                self.caller.msg(f"|yJob automatically assigned to {queue.automatic_assignee}.|n")
                
                # Notify the assignee
                if queue.automatic_assignee != self.caller.account:
                    self.caller.execute_cmd(
                        f"@mail {queue.automatic_assignee.username}"
                        f"=Job #{job.id} Auto-assigned"
                        f"/You have been automatically assigned to Job #{job.id}: {title}"
                    )

        except Exception as e:
            self.caller.msg(f"|rError creating job: {str(e)}|n")
            return

    def create_job(self):
        """Handle job creation with proper category handling."""
        if not self.args:
            self.caller.msg("Usage: +jobs/create <category>/<title>=<text>")
            return

        # Split on first = only
        parts = self.args.split('=', 1)
        if len(parts) < 2:
            self.caller.msg("You must provide both a title and description.")
            return

        title_desc, description = parts
        title_desc = title_desc.strip()
        # Convert %r markers to newlines and normalize paragraph spacing
        description = description.strip().replace("%r", "\n")
        # Normalize multiple newlines to double newlines for paragraph spacing
        while "\n\n\n" in description:
            description = description.replace("\n\n\n", "\n\n")

        # Handle category/title format
        specified_category = None
        if "/" in title_desc:
            category, title = title_desc.split("/", 1)
            specified_category = category.strip()
            title = title.strip()
        else:
            title = title_desc.strip()

        # Get the appropriate category and convert to uppercase
        category = self.determine_category(specified_category).upper()

        # Validate category - make case-insensitive comparison
        valid_categories = ["REQ", "BUG", "PLOT", "BUILD", "MISC", "XP", 
                          "PRP", "VAMP", "SHIFT", "MORT", "POSS", "COMP", 
                          "LING", "MAGE", "EQUIP"]
        
        if category not in valid_categories:
            self.caller.msg(f"Invalid category. Valid categories are: {', '.join(valid_categories)}")
            return

        if not title or not description:
            self.caller.msg("Both title and description are required.")
            return

        try:
            # Get or create the queue for this category
            queue, created = Queue.objects.get_or_create(
                name=category,
                defaults={'automatic_assignee': None}
            )

            # Create the job
            job = Job.objects.create(
                title=title,
                description=description,
                requester=self.caller.account,
                queue=queue,
                status='open'
            )

            # Notify the creator
            self.caller.msg(f"|gJob '{title}' created with ID {job.id} in category {category}.|n")
            
            # Post to the jobs channel for staff notification
            self.post_to_jobs_channel(self.caller.name, job.id, f"created in {category}")

            # Handle automatic assignment if configured
            if queue.automatic_assignee:
                job.assignee = queue.automatic_assignee
                job.status = 'claimed'
                job.save()
                self.caller.msg(f"|yJob automatically assigned to {queue.automatic_assignee}.|n")
                
                # Notify the assignee
                if queue.automatic_assignee != self.caller.account:
                    self.caller.execute_cmd(
                        f"@mail {queue.automatic_assignee.username}"
                        f"=Job #{job.id} Auto-assigned"
                        f"/You have been automatically assigned to Job #{job.id}: {title}"
                    )

        except Exception as e:
            self.caller.msg(f"|rError creating job: {str(e)}|n")
            return

    def add_comment(self):
        """Add a comment to a job."""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +jobs/comment <#>=<comment>")
            return

        # Split on first = only
        job_id, comment = self.args.split("=", 1)
        
        try:
            job_id = int(job_id.strip())
            comment = comment.strip()  
            job = Job.objects.get(id=job_id)

            if not (job.requester == self.caller.account or 
                    job.participants.filter(id=self.caller.account.id).exists() or 
                    self.caller.check_permstring("Admin")):
                self.caller.msg("You don't have permission to comment on this job.")
                return

            new_comment = {
                "author": self.caller.account.username,
                "text": comment,
                "created_at": timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if not job.comments:
                job.comments = []
            job.comments.append(new_comment)
            job.save()

            self.caller.msg(f"Comment added to job #{job_id}.")
            self.post_to_jobs_channel(self.caller.name, job.id, "commented on")
            self.send_mail_notification(job, f"{self.caller.name} commented on Job #{job.id}: {comment}")

        except (ValueError, Job.DoesNotExist):
            self.caller.msg("Invalid job ID.")

    def close_job(self):
        try:
            job_id = int(self.args)
            job = Job.objects.get(id=job_id)
            
            if not self.caller.check_permstring("Admin"):
                self.caller.msg("You don't have permission to close jobs.")
                return

            reason = ""
            if "=" in self.args:
                _, reason = self.args.split("=", 1)
                reason = reason.strip()

            is_approved = "close" in self.switches
            job.approved = is_approved
            success, subject, message, recipients = job.close(self.caller.account, reason)
            
            if success:
                status = "closed" if is_approved else "rejected"
                self.caller.msg(f"Job #{job_id} has been {status} and archived.")
                
                # Send mail notifications
                self.send_mail_notification(job, f"Job #{job_id} has been {status}.\n\nReason: {reason}")
                
                self.post_to_jobs_channel(self.caller.name, job.id, status)
            else:
                self.caller.msg(f"Job #{job_id} is already closed or rejected.")

        except (ValueError, Job.DoesNotExist):
            self.caller.msg("Invalid job ID.")

    def add_player(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +jobs/addplayer <#>=<player>")
            return

        job_id, player_name = self.args.split("=", 1)
        job_id = job_id.strip()
        player_name = player_name.strip()
        
        try:
            job_id = int(job_id)
            # Debug message for job lookup
            self.caller.msg(f"Looking for job #{job_id}...")
            job = Job.objects.get(id=job_id)
            self.caller.msg(f"Found job: {job.title}")

            if not (job.requester == self.caller.account or self.caller.check_permstring("Admin")):
                self.caller.msg("You don't have permission to add players to this job.")
                return

            # Debug message for player search
            self.caller.msg(f"Searching for player: {player_name}")
            player = search_account(player_name)
            if not player:
                self.caller.msg(f"Could not find account '{player_name}'.")
                return
            
            if len(player) > 1:
                # Show matching accounts for debugging
                matches = ", ".join([p.username for p in player])
                self.caller.msg(f"Multiple matches found: {matches}")
                self.caller.msg("Please be more specific.")
                return
                
            player = player[0]
            self.caller.msg(f"Found player: {player.username}")

            # Check if player is already a participant
            if player in job.participants.all():
                self.caller.msg(f"{player.username} is already a participant in this job.")
                return

            # Add the player and verify
            job.participants.add(player)
            job.save()

            # Verify the addition
            if player in job.participants.all():
                self.caller.msg(f"Player {player.username} successfully added to job #{job_id}.")
                self.post_to_jobs_channel(self.caller.name, job.id, f"added {player.username} to")
            else:
                self.caller.msg(f"Failed to add {player.username} to job #{job_id}. Please contact an administrator.")

        except ValueError:
            self.caller.msg(f"Invalid job ID: {job_id}")
        except Job.DoesNotExist:
            self.caller.msg(f"Job #{job_id} not found.")
        except Exception as e:
            self.caller.msg(f"Error adding player: {str(e)}")

    def remove_player(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +jobs/removeplayer <#>=<player>")
            return

        job_id, player_name = self.args.split("=", 1)
        
        try:
            job_id = int(job_id)
            job = Job.objects.get(id=job_id)

            if not (job.requester == self.caller.account or self.caller.check_permstring("Admin")):
                self.caller.msg("You don't have permission to remove players from this job.")
                return

            # Use account_search for global search
            player = search_account(player_name)
            if not player:
                self.caller.msg(f"Could not find account '{player_name}'.")
                return
            
            if len(player) > 1:
                self.caller.msg("Multiple matches found. Please be more specific.")
                return
                
            player = player[0]

            if player not in job.participants.all():
                self.caller.msg(f"{player.username} is not added to this job.")
                return

            job.participants.remove(player)
            job.save()

            self.caller.msg(f"Player {player.username} removed from job #{job_id}.")
            self.post_to_jobs_channel(self.caller.name, job.id, f"removed {player.username} from")

        except (ValueError, Job.DoesNotExist):
            self.caller.msg("Invalid job ID.")

    def assign_job(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +jobs/assign <#>=<staff>")
            return

        job_id, staff_name = self.args.split("=", 1)
        
        try:
            job_id = int(job_id)
            job = Job.objects.get(id=job_id)

            if not self.caller.check_permstring("Admin"):
                self.caller.msg("You don't have permission to assign this job.")
                return

            # Use account_search instead of regular search for global search
            staff = search_account(staff_name)
            if not staff:
                self.caller.msg(f"Could not find account '{staff_name}'.")
                return
            
            if len(staff) > 1:
                self.caller.msg("Multiple matches found. Please be more specific.")
                return
                
            staff = staff[0]

            job.assignee = staff
            job.status = 'claimed'
            job.save()

            self.caller.msg(f"Job #{job_id} assigned to {staff.username}.")
            self.post_to_jobs_channel(self.caller.name, job.id, f"assigned to {staff.username}")

        except (ValueError, Job.DoesNotExist):
            self.caller.msg("Invalid job ID.")

    def claim_job(self):
        if not self.args:
            self.caller.msg("Usage: +jobs/claim <#>")
            return

        try:
            job_id = int(self.args)
            job = Job.objects.get(id=job_id)

            if not self.caller.check_permstring("Admin"):
                self.caller.msg("You don't have permission to claim this job.")
                return

            if job.status != 'open':
                self.caller.msg("This job is not open for claiming.")
                return

            job.assignee = self.caller.account
            job.status = 'claimed'
            job.save()

            self.caller.msg(f"You have claimed job #{job_id}.")
            self.post_to_jobs_channel(self.caller.name, job.id, "claimed")

        except (ValueError, Job.DoesNotExist):
            self.caller.msg("Invalid job ID.")

    def unclaim_job(self):
        if not self.args:
            self.caller.msg("Usage: +jobs/unclaim <#>")
            return

        try:
            job_id = int(self.args)
            job = Job.objects.get(id=job_id)

            if not self.caller.check_permstring("Admin"):
                self.caller.msg("You don't have permission to unclaim this job.")
                return

            if job.status != 'claimed' or job.assignee != self.caller.account:
                self.caller.msg("You can't unclaim this job.")
                return

            job.assignee = None
            job.status = 'open'
            job.save()

            self.caller.msg(f"You have unclaimed job #{job_id}.")
            self.post_to_jobs_channel(self.caller.name, job.id, "unclaimed")

        except (ValueError, Job.DoesNotExist):
            self.caller.msg("Invalid job ID.")

    def approve_job(self):
        """Handle job approval with optional comment."""
        if not self.caller.check_permstring("Admin"):
            self.caller.msg("You don't have permission to approve jobs.")
            return

        try:
            # Split on first = only
            if "=" in self.args:
                job_id, comment = self.args.split("=", 1)
                job_id = int(job_id.strip())
                comment = comment.strip()
            else:
                job_id = int(self.args.strip())
                comment = ""

            # Debug: Log the job we're trying to approve
            logger.log_info(f"Attempting to approve job #{job_id}")
            
            job = Job.objects.get(id=job_id)
            logger.log_info(f"Found job: #{job.id} - {job.title} (archive_id: {job.archive_id})")
            
            if job.status in ['closed', 'rejected', 'completed', 'cancelled']:
                self.caller.msg(f"Job #{job_id} is already {job.status}.")
                return

            # Handle equipment requests
            if job.queue.name == "EQUIP" and job.title.startswith("Equipment Request:"):
                try:
                    # Extract equipment name from title
                    equipment_name = job.title.replace("Equipment Request:", "").strip()
                    
                    # Find the equipment
                    equipment = Equipment.objects.get(name=equipment_name)
                    
                    # Get or create inventory for the requester
                    account = job.requester
                    inventory, created = PlayerInventory.objects.get_or_create(player=account)
                    
                    # Check if item already exists in inventory
                    existing_item = InventoryItem.objects.filter(
                        inventory=inventory,
                        equipment=equipment
                    ).first()
                    
                    if existing_item:
                        if equipment.is_unique:
                            self.caller.msg("Player already has this unique item.")
                            # Still continue with job approval, but add a note
                            if not comment:
                                comment = "Note: Player already has this unique item. Request approved anyway."
                            else:
                                comment += " Note: Player already has this unique item. Request approved anyway."
                        else:
                            existing_item.quantity += 1
                            existing_item.is_proven = True
                            existing_item.approval_date = timezone.now()
                            existing_item.approved_by = self.caller.account
                            existing_item.save()
                            
                            if not comment:
                                comment = f"Equipment {equipment.name} added to {account.username}'s inventory. Quantity increased to {existing_item.quantity}."
                            
                    else:
                        # Create new inventory item (approved)
                        inventory_item = InventoryItem.objects.create(
                            inventory=inventory,
                            equipment=equipment,
                            quantity=1,
                            is_proven=True,
                            approval_date=timezone.now(),
                            approved_by=self.caller.account
                        )
                        
                        if not comment:
                            comment = f"Equipment {equipment.name} added to {account.username}'s inventory."
                    
                    self.caller.msg(f"Equipment {equipment.name} approved for {account.username}.")
                    
                except Equipment.DoesNotExist:
                    self.caller.msg("Equipment not found.")
                    return
                except Exception as e:
                    self.caller.msg(f"Error processing equipment request: {str(e)}")
                    return

            # Use transaction to ensure consistency
            with transaction.atomic():
                # Get the maximum archive_id from both tables
                max_archived = ArchivedJob.objects.aggregate(models.Max('archive_id'))['archive_id__max'] or 0
                max_job = Job.objects.exclude(archive_id__isnull=True).aggregate(models.Max('archive_id'))['archive_id__max'] or 0
                next_archive_id = max(max_archived, max_job) + 1
                
                logger.log_info(f"Max archive_id from ArchivedJob: {max_archived}")
                logger.log_info(f"Max archive_id from Job: {max_job}")
                logger.log_info(f"Calculated next_archive_id: {next_archive_id}")

                # Verify the archive_id is truly unique
                while (ArchivedJob.objects.filter(archive_id=next_archive_id).exists() or 
                       Job.objects.filter(archive_id=next_archive_id).exists()):
                    next_archive_id += 1
                    logger.log_info(f"Archive ID {next_archive_id-1} was taken, trying {next_archive_id}")

                # Create comments text
                comments_text = "\n\n".join([f"{comment['author']} [{comment['created_at']}]: {comment['text']}" 
                                           for comment in job.comments])
                
                # Add the approval comment if provided
                if comment:
                    comments_text += f"\n\nApproval Comment [{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}]: {comment}"

                # Debug: Log archive job creation attempt
                logger.log_info(f"Creating archived job with archive_id: {next_archive_id}")

                # Create the archived job
                archived_job = ArchivedJob.objects.create(
                    archive_id=next_archive_id,
                    original_id=job.id,
                    title=job.title,
                    description=job.description,
                    requester=job.requester,
                    assignee=job.assignee,
                    queue=job.queue,
                    created_at=job.created_at,
                    closed_at=timezone.now(),
                    status='closed',
                    comments=comments_text
                )
                logger.log_info(f"Successfully created archived job with archive_id: {archived_job.archive_id}")

                # Double-check for conflicts one last time
                conflicts = Job.objects.filter(archive_id=next_archive_id)
                if conflicts.exists():
                    logger.log_err(f"WARNING: Found {conflicts.count()} jobs with archive_id {next_archive_id}")
                    for j in conflicts:
                        logger.log_err(f"Conflicting job: #{j.id} - {j.title}")
                    raise Exception(f"Archive ID {next_archive_id} is already in use")

                # Now update and save the original job
                job.status = 'closed'
                job.approved = True
                job.closed_at = timezone.now()
                job.closed_by = self.caller.account
                job.archive_id = next_archive_id

                # Add the approval comment if provided
                if comment:
                    job.comments.append({
                        'author': self.caller.name,
                        'text': f"Approved: {comment}",
                        'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                    })

                logger.log_info(f"Attempting to save job #{job.id} with archive_id: {job.archive_id}")
                job.save()
                logger.log_info(f"Successfully saved job #{job.id}")

            # Notify the requester
            if job.requester and job.requester != self.caller.account:
                notification_message = f"Your job '#{job_id}: {job.title}' has been approved."
                if comment:
                    notification_message += f"\n\nComment: {comment}"
                self.send_mail_notification(job, notification_message)
            
            self.post_to_jobs_channel(self.caller.name, job.id, "approved")
            self.caller.msg(f"Job #{job_id} has been approved and archived.")
            
        except ValueError:
            self.caller.msg("Usage: +job/approve <#>[=<comment>]")
        except Job.DoesNotExist:
            self.caller.msg(f"Job #{job_id} not found.")
        except Exception as e:
            logger.log_err(f"Error in approve_job: {str(e)}")
            logger.log_err(f"Full error details:", exc_info=True)
            self.caller.msg(f"Error approving job: {str(e)}")

    def reject_job(self):
        """Handle job rejection with optional comment."""
        if not self.caller.check_permstring("Admin"):
            self.caller.msg("You don't have permission to reject jobs.")
            return

        try:
            # Split into job_id and comment if there's an = sign
            if "=" in self.args:
                job_id, comment = self.args.split("=", 1)
                job_id = int(job_id.strip())
                comment = comment.strip()
            else:
                job_id = int(self.args.strip())
                comment = ""

            job = Job.objects.get(id=job_id)
            
            if job.status not in ["open", "claimed"]:
                self.caller.msg("This job cannot be rejected.")
                return

            # Use transaction to ensure consistency
            with transaction.atomic():
                # Get the next archive_id
                max_archive_id = ArchivedJob.objects.aggregate(models.Max('archive_id'))['archive_id__max'] or 0
                next_archive_id = max_archive_id + 1

                # Create comments text
                comments_text = "\n\n".join([f"{comment['author']} [{comment['created_at']}]: {comment['text']}" 
                                           for comment in job.comments])

                # Add the rejection comment if provided
                if comment:
                    comments_text += f"\n\nRejection Comment [{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}]: {comment}"

                # Create the archived job
                archived_job = ArchivedJob.objects.create(
                    archive_id=next_archive_id,
                    original_id=job.id,
                    title=job.title,
                    description=job.description,
                    requester=job.requester,
                    assignee=job.assignee,
                    queue=job.queue,
                    created_at=job.created_at,
                    closed_at=timezone.now(),
                    status='rejected',
                    comments=comments_text
                )

                # Update the original job
                job.status = 'rejected'
                job.closed_at = timezone.now()
                job.archive_id = next_archive_id

                # Add the rejection comment if provided
                if comment:
                    job.comments.append({
                        'author': self.caller.name,
                        'text': f"Rejected: {comment}",
                        'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                    })

                job.save()

            self.caller.msg(f"Job #{job_id} has been rejected and archived.")
            
            # Send mail notifications
            notification_message = f"Job #{job_id} has been rejected."
            if comment:
                notification_message += f"\n\nReason: {comment}"
            self.send_mail_notification(job, notification_message)
            
            self.post_to_jobs_channel(self.caller.name, job.id, "rejected")

        except ValueError:
            self.caller.msg("Usage: +job/reject <#>[=<reason>]")
        except Job.DoesNotExist:
            self.caller.msg(f"Job #{job_id} not found.")
        except Exception as e:
            self.caller.msg(f"Error rejecting job: {str(e)}")
            logger.log_err(f"Error in reject_job: {str(e)}")

    def attach_object(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +jobs/attach <#>=<object name>[:<arg>]")
            return

        job_id, object_info = self.args.split("=", 1)
        object_name, _, attached_to_arg = object_info.partition(":")
        
        try:
            job_id = int(job_id)
            job = Job.objects.get(id=job_id)
            obj = self.caller.search(object_name)
            
            if not obj:
                return

            if attached_to_arg and job.template_args and attached_to_arg not in job.template_args:
                self.caller.msg(f"No argument '{attached_to_arg}' found in this job's template.")
                return

            JobAttachment.objects.create(job=job, object=obj, attached_to_arg=attached_to_arg)
            self.caller.msg(f"Object '{obj.key}' attached to job #{job.id}.")
            if attached_to_arg:
                self.caller.msg(f"Attached to template argument '{attached_to_arg}'.")
            
        except (ValueError, Job.DoesNotExist):
            self.caller.msg("Invalid job ID.")

    def remove_object(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +jobs/remove <#>=<object name>")
            return

        job_id, object_name = self.args.split("=", 1)
        
        try:
            job_id = int(job_id)
            job = Job.objects.get(id=job_id)
            obj = self.caller.search(object_name)
            
            if not obj:
                return

            attachment = JobAttachment.objects.filter(job=job, object=obj).first()
            if not attachment:
                self.caller.msg(f"Object '{obj.key}' is not attached to job #{job.id}.")
                return

            attachment.delete()
            self.caller.msg(f"Object '{obj.key}' removed from job #{job.id}.")
            
        except (ValueError, Job.DoesNotExist):
            self.caller.msg("Invalid job ID.")

    def reassign_job(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +jobs/reassign <#>=<new assignee>")
            return

        try:
            job_id, new_assignee_name = self.args.split("=", 1)
            job_id = int(job_id)
            new_assignee_name = new_assignee_name.strip()

            job = Job.objects.get(id=job_id)
            
            # Use account_search for global search
            new_assignee = search_account(new_assignee_name)
            if not new_assignee:
                self.caller.msg(f"Could not find account '{new_assignee_name}'.")
                return
            
            if len(new_assignee) > 1:
                self.caller.msg("Multiple matches found. Please be more specific.")
                return
                
            new_assignee = new_assignee[0]

            job.assignee = new_assignee
            job.save()
            self.caller.msg(f"Job '{job.title}' reassigned to {new_assignee.username}.")
            
            # Notify the new assignee
            if new_assignee.is_connected:
                new_assignee.msg(f"You have been reassigned to job '{job.title}'.")

            self.post_to_jobs_channel(self.caller.name, job.id, f"reassigned to {new_assignee.username}")

        except (ValueError, Job.DoesNotExist):
            self.caller.msg("Invalid job ID.")

    def view_queue_jobs(self):
        if not self.args:
            self.caller.msg("Usage: +jobs/queue/view <queue name>")
            return

        queue_name = self.args.strip()
        try:
            queue = Queue.objects.get(name__iexact=queue_name)
            jobs = Job.objects.filter(queue=queue).order_by('status')

            if not jobs.exists():
                self.caller.msg(f"No jobs found in the queue '{queue_name}'.")
                return

            table = evtable.EvTable("ID", "Title", "Status", "Requester", "Assignee")
            for job in jobs:
                table.add_row(
                    job.id, 
                    crop(job.title, width=25),
                    job.status,
                    job.requester.username,
                    job.assignee.username if job.assignee else "-----"
                )
            
            self.caller.msg(header(f"Jobs in queue '{queue_name}'"))
            self.caller.msg(table)
            self.caller.msg(footer())

        except Queue.DoesNotExist:
            self.caller.msg(f"No queue found with the name '{queue_name}'.")

    def list_jobs_with_object(self):
        if not self.args:
            self.caller.msg("Usage: +jobs/list_with_object <object_name>")
            return

        object_name = self.args.strip()
        attachments = JobAttachment.objects.filter(object__db_key__iexact=object_name)

        if not attachments.exists():
            self.caller.msg(f"No jobs found with the object '{object_name}' attached.")
            return

        jobs = set(attachment.job for attachment in attachments)

        if jobs:
            table = evtable.EvTable("ID", "Title", "Status", "Requester", "Assignee")
            for job in jobs:
                table.add_row(
                    job.id, 
                    crop(job.title, width=25),
                    job.status,
                    job.requester.username,
                    job.assignee.username if job.assignee else "-----"
                )
            
            self.caller.msg(header(f"Jobs with object '{object_name}' attached"))
            self.caller.msg(table)
            self.caller.msg(footer())
        else:
            self.caller.msg(f"No jobs found with the object '{object_name}' attached.")

    def view_archived_job(self):
        """View archived jobs - restricted to staff only."""
        if not self.caller.check_permstring("Admin"):
            self.caller.msg("You don't have permission to view archived jobs.")
            return

        if not self.args:
            # List all archived jobs
            archived_jobs = ArchivedJob.objects.all().order_by('-closed_at')
            if not archived_jobs:
                self.caller.msg("There are no archived jobs.")
                return

            output = header("Archived Dies Irae Jobs", width=78, fillchar="|r-|n") + "\n"
            
            # Create the header row
            header_row = "|cJob #  Queue      Job Title                 Closed   Assignee          Requester|n"
            output += header_row + "\n"
            output += ANSIString("|r" + "-" * 78 + "|n") + "\n"

            # Add each job as a row
            for job in archived_jobs:
                # Handle potentially deleted users
                assignee_name = job.assignee.username if job.assignee else "-----"
                requester_name = job.requester.username if job.requester else "[Deleted User]"
                
                row = (
                    f"{job.original_id:<6}"
                    f"{crop(job.queue.name, width=10):<11}"
                    f"{crop(job.title, width=25):<25}"
                    f"{job.closed_at.strftime('%m/%d/%y'):<9}"
                    f"{crop(assignee_name, width=17):<18}"
                    f"{requester_name}"
                )
                output += row + "\n"

            output += footer(width=78, fillchar="|r-|n")
            self.caller.msg(output)

        else:
            # View a specific archived job
            try:
                job_id = int(self.args)
                archived_job = ArchivedJob.objects.get(original_id=job_id)
                
                # Additional permission check for viewing specific jobs
                if not self.caller.check_permstring("Admin") and archived_job.requester != self.caller.account:
                    self.caller.msg("You don't have permission to view this archived job.")
                    return
                
                # Handle potentially deleted users
                requester_name = archived_job.requester.username if archived_job.requester else "[Deleted User]"
                assignee_name = archived_job.assignee.username if archived_job.assignee else "-----"
                
                output = header(f"Archived Job {archived_job.original_id}", width=78, fillchar="|r-|n") + "\n"
                output += f"|cTitle:|n {archived_job.title}\n"
                output += f"|cStatus:|n {archived_job.status}\n"
                output += f"|cRequester:|n {requester_name}\n"
                output += f"|cAssignee:|n {assignee_name}\n"
                output += f"|cQueue:|n {archived_job.queue.name}\n"
                output += f"|cCreated At:|n {archived_job.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                output += f"|cClosed At:|n {archived_job.closed_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                
                output += divider("Description", width=78, fillchar="-", color="|r", text_color="|c") + "\n"
                output += archived_job.description + "\n\n"
                
                if archived_job.comments:
                    output += divider("Comments", width=78, fillchar="-", color="|r", text_color="|c") + "\n"
                    output += archived_job.comments + "\n"
                
                output += footer(width=78, fillchar="|r-|n")
                self.caller.msg(output)
            except ValueError:
                self.caller.msg("Invalid job ID.")
            except ArchivedJob.DoesNotExist:
                self.caller.msg(f"Archived job #{job_id} not found.")

    def post_to_jobs_channel(self, player_name, job_id, action):
        channel_names = ["Jobs", "Requests", "Req"]
        channel = None

        for name in channel_names:
            found_channel = ChannelDB.objects.channel_search(name)
            if found_channel:
                channel = found_channel[0]
                break

        if not channel:
            # Create channel without auto_subscribe
            channel = create.create_channel(
                "Jobs",
                typeclass="typeclasses.channels.Channel",
                locks="control:perm(Admin);listen:all();send:all()"
            )
            # Subscribe the creator after channel is created
            channel.connect(self.caller)
            self.caller.msg("Created a new 'Jobs' channel for job notifications.")

        message = f"{player_name} {action} Job #{job_id}"
        channel.msg(f"[Job System] {message}")

    def send_mail_notification(self, job, message):
        """Send a mail notification to the job requester."""
        if job.requester and job.requester != self.caller.account:  # Don't send mail if you're acting on your own job
            try:
                subject = f"Job #{job.id} Update"
                mail_body = f"Job #{job.id}: {job.title}\n\n{message}"
                
                # Use the mail command's proper format
                mail_cmd = f"@mail {job.requester.username}={subject}/{mail_body}"
                self.caller.execute_cmd(mail_cmd)
                
                # Only show success message if we actually sent the mail
                if job.requester.username:
                    self.caller.msg(f"Notification sent to {job.requester.username}.")
                else:
                    self.caller.msg("Could not send notification - invalid recipient username.")
                    
            except Exception as e:
                self.caller.msg(f"Failed to send notification: {str(e)}")

    def complete_job(self):
        self._change_job_status("completed")

    def cancel_job(self):
        self._change_job_status("cancelled")

    def _change_job_status(self, new_status):
        if not self.caller.check_permstring("Admin"):
            self.caller.msg(f"You don't have permission to {new_status} jobs.")
            return

        try:
            job_id, reason = self.args.split("=", 1)
            job_id = int(job_id.strip())
            reason = reason.strip()
        except ValueError:
            self.caller.msg(f"Usage: +job/{new_status} <#>=<reason>")
            return

        try:
            job = Job.objects.get(id=job_id)
            
            if job.status in ['closed', 'rejected', 'completed', 'cancelled']:
                self.caller.msg(f"Job #{job_id} is already {job.status}.")
                return

            # Use transaction to ensure consistency
            with transaction.atomic():
                # Get the next archive_id
                max_archive_id = ArchivedJob.objects.aggregate(models.Max('archive_id'))['archive_id__max'] or 0
                next_archive_id = max_archive_id + 1

                # Create comments text
                comments_text = "\n\n".join([f"{comment['author']} [{comment['created_at']}]: {comment['text']}" 
                                           for comment in job.comments])

                # Add the status change comment
                comments_text += f"\n\nStatus Change [{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}]: {reason}"

                # Create the archived job
                archived_job = ArchivedJob.objects.create(
                    archive_id=next_archive_id,
                    original_id=job.id,
                    title=job.title,
                    description=job.description,
                    requester=job.requester,
                    assignee=job.assignee,
                    queue=job.queue,
                    created_at=job.created_at,
                    closed_at=timezone.now(),
                    status=new_status,
                    comments=comments_text
                )

                # Update the original job
                job.status = new_status
                job.closed_at = timezone.now()
                job.archive_id = next_archive_id

                # Add the status change comment
                job.comments.append({
                    'author': self.caller.name,
                    'text': f"{new_status.title()}: {reason}",
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })

                job.save()

            self.caller.msg(f"Job #{job_id} has been {new_status} and archived.")
            
            # Send mail notifications
            notification_message = f"Job #{job_id} has been {new_status}.\n\nReason: {reason}"
            self.send_mail_notification(job, notification_message)
            
            self.post_to_jobs_channel(self.caller.name, job.id, new_status)

        except Job.DoesNotExist:
            self.caller.msg(f"Job #{job_id} not found.")
        except Exception as e:
            self.caller.msg(f"Error changing job status: {str(e)}")
            logger.log_err(f"Error in _change_job_status: {str(e)}")

    def display_note(self, note):
        """Display a note with formatting."""
        width = 78
        output = header(f"Job #{note.note_id}", width=width, color="|y", fillchar="|r=|n", bcolor="|b")

        if note.category:
            output += f"|c{note.category}|n"
            output += f" |w#{note.note_id}|n\n"

        output += format_stat("Note Title:", note.name, width=width) + "\n"
        output += format_stat("Visibility:", "Public" if note.is_public else "Private", width=width) + "\n"
        
        # Show approval status and details
        if note.is_approved:
            output += format_stat("Approved:", "Yes", width=width) + "\n"
            if note.approved_by:
                output += format_stat("Approved By:", note.approved_by, width=width) + "\n"
            if note.approved_at:
                output += format_stat("Approved At:", note.approved_at.strftime("%Y-%m-%d %H:%M:%S"), width=width) + "\n"
        else:
            output += format_stat("Approved:", "No", width=width) + "\n"

        # Show creation and update times for staff
        if self.caller.check_permstring("Builders"):
            output += format_stat("Created:", note.created_at.strftime("%Y-%m-%d %H:%M:%S"), width=width) + "\n"
            output += format_stat("Updated:", note.updated_at.strftime("%Y-%m-%d %H:%M:%S"), width=width) + "\n"

        output += divider("", width=width, fillchar="-", color="|r") + "\n"
        
        # Note content - properly handle line breaks and indentation
        text = note.text.strip()
        # Split on actual newlines
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        
        # Process each paragraph
        for i, paragraph in enumerate(paragraphs):
            # Wrap the paragraph text
            wrapped_lines = wrap_ansi(paragraph, width=width-4).split('\n')
            # Add proper indentation to each line
            for line in wrapped_lines:
                output += "  " + line + "\n"
            # Add a blank line between paragraphs, but not after the last one
            if i < len(paragraphs) - 1:
                output += "\n"
        
        output += footer(width=width, fillchar="|r=|n")
        self.caller.msg(output)

    def list_my_jobs(self):
        """List jobs that are relevant to the caller."""
        if self.caller.check_permstring("Admin"):
            # For staff, show jobs they created or are assigned to
            jobs = Job.objects.filter(
                models.Q(requester=self.caller.account) |
                models.Q(assignee=self.caller.account),
                status__in=['open', 'claimed']
            ).distinct().order_by('-created_at')
        else:
            # For players, show only jobs they created
            jobs = Job.objects.filter(
                requester=self.caller.account,
                status__in=['open', 'claimed']
            ).order_by('-created_at')

        if not jobs:
            self.caller.msg("You have no open jobs.")
            return

        output = header("My Dies Irae Jobs", width=78, fillchar="|r-|n") + "\n"
        
        # Create the header row without fixed widths
        header_row = "|cJob #  Queue      Job Title           Originator    Assignee      Status|n"
        output += header_row + "\n"
        output += ANSIString("|r" + "-" * 78 + "|n") + "\n"

        # Add each job as a row without cropping
        for job in jobs:
            assignee = job.assignee.username if job.assignee else "-----"
            originator = job.requester.username if job.requester else "-----"
            
            # Check if job has been viewed by this user
            unread = job.is_updated_since_last_view(self.caller.account)
            title_marker = "|r*|n " if unread else "  "
            
            row = (
                f"{job.id:<6}"
                f"{job.queue.name:<11}"
                f"{title_marker}{job.title}"
            )
            output += row + "\n"

        output += footer(width=78, fillchar="|r-|n")
        self.caller.msg(output)

    def reopen_job(self):
        """Reopen an archived job."""
        if not self.args:
            self.caller.msg("Usage: +jobs/reopen <#>")
            return

        try:
            job_id = int(self.args)
            archived_job = ArchivedJob.objects.get(original_id=job_id)

            # Check permissions
            if not (self.caller.check_permstring("Admin") or archived_job.requester == self.caller.account):
                self.caller.msg("You don't have permission to reopen this job.")
                return

            # Create a new job with the archived information
            new_job = Job.objects.create(
                title=archived_job.title,
                description=archived_job.description,
                requester=archived_job.requester,
                assignee=archived_job.assignee,
                queue=archived_job.queue,
                status='open',
                comments=[]  # Start with empty comments
            )

            # Add a system comment about reopening
            new_job.comments.append({
                'author': 'System',
                'text': f"Job reopened by {self.caller.name} (Previous job #{job_id})",
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            })

            # If there were previous comments, add them with a header
            if archived_job.comments:
                new_job.comments.append({
                    'author': 'System',
                    'text': "--- Previous Comments ---",
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                new_job.comments.append({
                    'author': 'System',
                    'text': archived_job.comments,
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })

            new_job.save()

            self.caller.msg(f"Job #{job_id} has been reopened as Job #{new_job.id}.")
            self.post_to_jobs_channel(self.caller.name, new_job.id, f"reopened (was Job #{job_id})")

            # Notify the original requester if different from the reopener
            if archived_job.requester != self.caller.account:
                self.send_mail_notification(
                    new_job,
                    f"Your job '{archived_job.title}' (#{job_id}) has been reopened as Job #{new_job.id} by {self.caller.name}."
                )

        except ValueError:
            self.caller.msg("Invalid job ID.")
        except ArchivedJob.DoesNotExist:
            self.caller.msg(f"Archived job #{job_id} not found.")

    def list_assigned_jobs(self):
        """List jobs that are assigned to the staff member."""
        if not self.caller.check_permstring("Admin"):
            self.caller.msg("You don't have permission to use this command.")
            return

        jobs = Job.objects.filter(
            assignee=self.caller.account,
            status__in=['open', 'claimed']
        ).order_by('-created_at')

        if not jobs:
            self.caller.msg("You have no jobs assigned to you.")
            return

        output = header("My Assigned Jobs", width=78, fillchar="|r-|n") + "\n"
        
        # Create the header row without fixed widths
        header_row = "|cJob #  Queue      Job Title                 Originator    Status|n"
        output += header_row + "\n"
        output += ANSIString("|r" + "-" * 78 + "|n") + "\n"

        # Add each job as a row without cropping
        for job in jobs:
            originator = job.requester.username if job.requester else "-----"
            
            # Check if job has been viewed by this user
            unread = job.is_updated_since_last_view(self.caller.account)
            title_marker = "|r*|n " if unread else "  "
            
            row = (
                f"{job.id:<6}"
                f"{job.queue.name:<11}"
                f"{title_marker}{job.title}"
            )
            output += row + "\n"

        output += footer(width=78, fillchar="|r-|n")
        self.caller.msg(output)

    def clear_archive(self):
        """Clear all archived jobs and reset job numbers."""
        if not self.caller.check_permstring("Admin"):
            self.caller.msg("You don't have permission to clear the job archive.")
            return

        try:
            # Get all archived jobs
            archived_jobs = ArchivedJob.objects.all().order_by('archive_id')
            
            if not archived_jobs:
                self.caller.msg("No archived jobs to clear.")
                return

            # Create a log file with timestamp
            from datetime import datetime
            import os
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_dir = os.path.join('server', 'logs', 'jobs')
            
            # Create the jobs log directory if it doesn't exist
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            log_file = os.path.join(log_dir, f'jobs_archive_{timestamp}.log')

            # Write archived jobs to the log file
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"Dies Irae Jobs Archive - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                
                for job in archived_jobs:
                    f.write(f"Job #{job.original_id}\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"Title: {job.title}\n")
                    f.write(f"Status: {job.status}\n")
                    f.write(f"Queue: {job.queue.name}\n")
                    # Handle potentially deleted users
                    requester_name = job.requester.username if job.requester else "[Deleted User]"
                    assignee_name = job.assignee.username if job.assignee else "None"
                    f.write(f"Requester: {requester_name}\n")
                    f.write(f"Assignee: {assignee_name}\n")
                    f.write(f"Created: {job.created_at}\n")
                    f.write(f"Closed: {job.closed_at}\n")
                    f.write("\nDescription:\n")
                    f.write(job.description + "\n")
                    if job.comments:
                        f.write("\nComments:\n")
                        f.write(job.comments + "\n")
                    f.write("\n" + "=" * 80 + "\n\n")

            # Get the count before clearing
            job_count = archived_jobs.count()

            # Store all job data with participants before making any changes
            job_data = []
            for job in Job.objects.filter(archive_id__isnull=True).order_by('id'):
                # Skip jobs with deleted requesters
                if not job.requester:
                    continue
                    
                participant_usernames = []
                for participant in job.participants.all():
                    participant_usernames.append(participant.username)
                
                # Log the original job participants
                logger.log_info(f"Original Job #{job.id} has participants: {', '.join(participant_usernames)}")
                
                # Store all job data needed for recreation
                job_data.append({
                    'title': job.title,
                    'description': job.description,
                    'requester_id': job.requester.id,
                    'assignee_id': job.assignee.id if job.assignee else None,
                    'queue_id': job.queue.id,
                    'status': job.status,
                    'comments': job.comments,
                    'created_at': job.created_at,
                    'participant_ids': [p.id for p in job.participants.all()],
                    'participant_usernames': participant_usernames,
                    'original_id': job.id
                })

            # Start a transaction for the main operations
            with transaction.atomic():
                # First, clear all job attachments
                JobAttachment.objects.all().delete()
                
                # Delete all jobs with archive_id
                Job.objects.filter(archive_id__isnull=False).delete()
                
                # Delete all archived jobs
                archived_jobs.delete()
                
                # Delete all jobs without archive_id
                Job.objects.filter(archive_id__isnull=True).delete()

                # Reset sequences based on database engine
                with connection.cursor() as cursor:
                    db_engine = connection.settings_dict['ENGINE']
                    
                    if 'postgresql' in db_engine:
                        # PostgreSQL
                        cursor.execute("SELECT setval(pg_get_serial_sequence('jobs_job', 'id'), 1, false);")
                        cursor.execute("SELECT setval(pg_get_serial_sequence('jobs_archivedjob', 'archive_id'), 1, false);")
                    elif 'mysql' in db_engine:
                        # MySQL/MariaDB
                        cursor.execute("ALTER TABLE jobs_job AUTO_INCREMENT = 1;")
                        cursor.execute("ALTER TABLE jobs_archivedjob AUTO_INCREMENT = 1;")
                    elif 'sqlite' in db_engine:
                        # SQLite - just delete from sqlite_sequence
                        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('jobs_job', 'jobs_archivedjob');")

                # Recreate jobs in order
                old_to_new_mapping = {}
                for job_info in job_data:
                    # Create the new job with all data except participants
                    new_job = Job.objects.create(
                        title=job_info['title'],
                        description=job_info['description'],
                        requester_id=job_info['requester_id'],
                        assignee_id=job_info['assignee_id'],
                        queue_id=job_info['queue_id'],
                        status=job_info['status'],
                        comments=job_info['comments'],
                        created_at=job_info['created_at']
                    )
                    
                    old_id = job_info['original_id']
                    new_id = new_job.id
                    old_to_new_mapping[old_id] = new_id
                    
                    logger.log_info(f"Recreated job: #{old_id} -> #{new_id}")
                    
                    # Now add participants using their IDs
                    for participant_id in job_info['participant_ids']:
                        try:
                            account = AccountDB.objects.get(id=participant_id)
                            new_job.participants.add(account)
                            logger.log_info(f"Added participant {account.username} to job #{new_id}")
                        except AccountDB.DoesNotExist:
                            logger.log_err(f"Could not find participant account with ID {participant_id}")
                    
                    # Double-check the participants
                    new_participants = list(new_job.participants.all())
                    new_participant_usernames = [p.username for p in new_participants]
                    
                    logger.log_info(f"Job #{new_id} should have participants: {', '.join(job_info['participant_usernames'])}")
                    logger.log_info(f"Job #{new_id} actually has participants: {', '.join(new_participant_usernames)}")

            # After transaction, handle SQLite VACUUM separately
            if 'sqlite' in connection.settings_dict['ENGINE']:
                with connection.cursor() as cursor:
                    cursor.execute("VACUUM")

            self.caller.msg(f"{job_count} archived jobs have been cleared and saved to {log_file}")
            self.caller.msg("Job numbering has been reset.")
            
            # Post to jobs channel
            self.post_to_jobs_channel(self.caller.name, "ALL", "cleared the jobs archive")

        except Exception as e:
            self.caller.msg(f"Error clearing archive: {str(e)}")
            logger.log_err(f"Error in clear_archive: {str(e)}")
            logger.log_err("Full error details:", exc_info=True)

class JobSystemCmdSet(CmdSet):
    """
    This cmdset contains the jobs commands
    """
    key = "JobSystem"
    
    def at_cmdset_creation(self):
        """
        Called when cmdset is first created.
        """
        self.add(CmdJobs())
        # Create/update help entry when cmdset is created
        from evennia.utils import create
        create.create_help_entry("jobs_system", CmdJobs.__doc__, category="General", 
                               locks="view:all()", aliases=["jobs"], 
                               tags=[("jobs", "help"), ("system", "help"), ("help", "help")])
