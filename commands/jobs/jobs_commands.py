from evennia import CmdSet
from django.db import models, transaction, connection
from evennia.utils import create, evtable
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

class CmdJobs(MuxCommand):
    """
    View and manage jobs

    Usage:
      +jobs                      - List all jobs
      +myjobs                    - List jobs you created or are assigned to
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

    Categories:
      REQ    - General requests
      BUG    - Bug reports
      PLOT   - Plot-related requests
      BUILD  - Building/room requests
      MISC   - Miscellaneous requests

    Examples:
      +jobs
      +myjobs
      +jobs 5
      +jobs/create REQ/New Character=Please review my character sheet
      +jobs/comment 5=Added background story
      +jobs/approve 5
      +jobs/reopen 5
    """

    key = "+jobs"
    aliases = ["+requests", "+job", "+myjobs"]
    locks = "cmd:all()"
    help_category = "General"
    
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

        output = header("Dies Irae Jobs", width=78, fillchar="|r-|n") + "\n"
        
        # Create the header row
        header_row = "|cJob #  Queue      Job Title                 Started  Assignee          Status|n"
        output += header_row + "\n"
        output += ANSIString("|r" + "-" * 78 + "|n") + "\n"

        # Add each job as a row
        for job in jobs:
            assignee = job.assignee.username if job.assignee else "-----"
            row = (
                f"{job.id:<6}"
                f"{crop(job.queue.name, width=10):<11}"
                f"{crop(job.title, width=25):<25}"
                f"{job.created_at.strftime('%m/%d/%y'):<9}"
                f"{crop(assignee, width=17):<18}"
                f"{job.status}"
            )
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

            output = header(f"Job {job.id}", width=78, fillchar="|r-|n") + "\n"
            output += f"|cTitle:|n {job.title}\n"
            output += f"|cStatus:|n {job.status}\n"
            output += f"|cRequester:|n {job.requester.username}\n"
            output += f"|cAssignee:|n {job.assignee.username if job.assignee else '-----'}\n"
            output += f"|cQueue:|n {job.queue.name}\n"
            output += f"|cCreated At:|n {job.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            output += f"|cClosed At:|n {job.closed_at.strftime('%Y-%m-%d %H:%M:%S') if job.closed_at else '-----'}\n"
            
            attached_objects = JobAttachment.objects.filter(job=job)
            if attached_objects:
                output += "|cAttached Objects:|n " + ", ".join([obj.object.key for obj in attached_objects]) + "\n"
            else:
                output += "|cAttached Objects:|n None\n"
            
            output += divider("Description", width=78, fillchar="-", color="|r", text_color="|c") + "\n"
            
            # Handle description text wrapping
            paragraphs = [p.strip() for p in job.description.split('\n\n') if p.strip()]
            for i, paragraph in enumerate(paragraphs):
                # Wrap text at a consistent width with proper indentation
                lines = wrap_ansi(paragraph, width=70)  # Reduced width for consistent wrapping
                for line in lines.split('\n'):
                    output += "  " + line.strip() + "\n"
                if i < len(paragraphs) - 1:
                    output += "\n"
            
            if job.comments:
                output += divider("Comments", width=78, fillchar="-", color="|r", text_color="|c") + "\n"
                for comment in job.comments:
                    output += f"|c{comment['author']} [{comment['created_at']}]:|n\n"
                    output += wrap_ansi(comment['text'], width=76, left_padding=2) + "\n\n"
            
            output += divider("", width=78, fillchar="-", color="|r") + "\n"
            self.caller.msg(output)
        except ValueError:
            self.caller.msg("Invalid job ID.")
        except Job.DoesNotExist:
            self.caller.msg(f"Job #{job_id} not found or is archived. Use +jobs/archive {job_id} to view archived jobs.")

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
        if "/" in title_desc:
            category, title = title_desc.split("/", 1)
            category = category.strip().upper()
            title = title.strip()
        else:
            category = "REQ"  # Default category
            title = title_desc.strip()

        # Validate category
        valid_categories = ["REQ", "BUG", "PLOT", "BUILD", "MISC", "XP", "PRP", "SPLAT"]
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
        
        try:
            job_id = int(job_id)
            job = Job.objects.get(id=job_id)

            if not (job.requester == self.caller.account or self.caller.check_permstring("Admin")):
                self.caller.msg("You don't have permission to add players to this job.")
                return

            player = self.caller.search(player_name)
            if not player:
                return

            if not hasattr(player, 'account'):
                self.caller.msg("That is not a valid player.")
                return

            job.participants.add(player.account)
            job.save()

            self.caller.msg(f"Player {player.name} added to job #{job_id}.")
            self.post_to_jobs_channel(self.caller.name, job.id, f"added {player.name} to")

        except (ValueError, Job.DoesNotExist):
            self.caller.msg("Invalid job ID.")

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

            player = self.caller.search(player_name)
            if not player:
                return

            if not hasattr(player, 'account'):
                self.caller.msg("That is not a valid player.")
                return

            if player.account not in job.participants.all():
                self.caller.msg(f"{player.name} is not added to this job.")
                return

            job.participants.remove(player.account)
            job.save()

            self.caller.msg(f"Player {player.name} removed from job #{job_id}.")
            self.post_to_jobs_channel(self.caller.name, job.id, f"removed {player.name} from")

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

            staff = self.caller.search(staff_name)
            if not staff:
                return

            if not hasattr(staff, 'account'):
                self.caller.msg("That is not a valid staff member.")
                return

            job.assignee = staff.account
            job.status = 'claimed'
            job.save()

            self.caller.msg(f"Job #{job_id} assigned to {staff.name}.")
            self.post_to_jobs_channel(self.caller.name, job.id, f"assigned to {staff.name}")

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

            job = Job.objects.get(id=job_id)
            
            if job.status in ['closed', 'rejected', 'completed', 'cancelled']:
                self.caller.msg(f"Job #{job_id} is already {job.status}.")
                return

            job.status = 'completed'
            job.closed_at = timezone.now()

            # Add the approval comment if provided
            if comment:
                job.comments.append({
                    'author': self.caller.name,
                    'text': f"Approved: {comment}",
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })

            # Send mail notification before archiving
            notification_message = f"Your job '#{job_id}: {job.title}' has been approved."
            if comment:
                notification_message += f"\n\nComment: {comment}"
            
            if job.requester and job.requester != self.caller.account:
                mail_cmd = f"@mail {job.requester.username}=Job #{job_id} Approved/{notification_message}"
                self.caller.execute_cmd(mail_cmd)

            # Archive the job
            comments_text = "\n\n".join([f"{comment['author']} [{comment['created_at']}]: {comment['text']}" 
                                       for comment in job.comments])
            archived_job = ArchivedJob.objects.create(
                original_id=job.id,
                title=job.title,
                description=job.description,
                requester=job.requester,
                assignee=job.assignee,
                queue=job.queue,
                created_at=job.created_at,
                closed_at=job.closed_at,
                status=job.status,
                comments=comments_text
            )

            job.archive_id = archived_job.archive_id
            job.save()

            self.caller.msg(f"Job #{job_id} has been approved and archived.")
            self.post_to_jobs_channel(self.caller.name, job.id, "approved")

        except ValueError:
            self.caller.msg("Usage: +job/approve <#>[=<comment>]")
        except Job.DoesNotExist:
            self.caller.msg(f"Job #{job_id} not found.")

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

            job.status = 'rejected'
            job.closed_at = timezone.now()

            # Add the rejection comment if provided
            if comment:
                job.comments.append({
                    'author': self.caller.name,
                    'text': f"Rejected: {comment}",
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })

            # Archive the job
            comments_text = "\n\n".join([f"{comment['author']} [{comment['created_at']}]: {comment['text']}" for comment in job.comments])
            archived_job = ArchivedJob.objects.create(
                original_id=job.id,
                title=job.title,
                description=job.description,
                requester=job.requester,
                assignee=job.assignee,
                queue=job.queue,
                created_at=job.created_at,
                closed_at=job.closed_at,
                status=job.status,
                comments=comments_text
            )

            job.archive_id = archived_job.archive_id
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
            new_assignee = self.caller.search(new_assignee_name)

            if not new_assignee:
                return

            job.assignee = new_assignee.account
            job.save()
            self.caller.msg(f"Job '{job.title}' reassigned to {new_assignee.name}.")
            if hasattr(new_assignee, 'sessions') and new_assignee.sessions.exists():
                new_assignee.msg(f"You have been reassigned to the job '{job.title}'.")

            self.post_to_jobs_channel(self.caller.name, job.id, f"reassigned to {new_assignee.name}")

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
                assignee = job.assignee.username if job.assignee else "-----"
                row = (
                    f"{job.original_id:<6}"
                    f"{crop(job.queue.name, width=10):<11}"
                    f"{crop(job.title, width=25):<25}"
                    f"{job.closed_at.strftime('%m/%d/%y'):<9}"
                    f"{crop(assignee, width=17):<18}"
                    f"{job.requester.username}"
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
                
                output = header(f"Archived Job {archived_job.original_id}", width=78, fillchar="|r-|n") + "\n"
                output += f"|cTitle:|n {archived_job.title}\n"
                output += f"|cStatus:|n {archived_job.status}\n"
                output += f"|cRequester:|n {archived_job.requester.username}\n"
                output += f"|cAssignee:|n {archived_job.assignee.username if archived_job.assignee else '-----'}\n"
                output += f"|cQueue:|n {archived_job.queue.name}\n"
                output += f"|cCreated At:|n {archived_job.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                output += f"|cClosed At:|n {archived_job.closed_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                
                output += divider("Description", width=78, fillchar="-", color="|r", text_color="|c") + "\n"
                output += wrap_ansi(archived_job.description, width=76, left_padding=2) + "\n\n"
                
                if archived_job.comments:
                    output += divider("Comments", width=78, fillchar="-", color="|r", text_color="|c") + "\n"
                    output += wrap_ansi(archived_job.comments, width=76, left_padding=2) + "\n"
                
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

            job.status = new_status
            job.closed_at = timezone.now()

            # Archive the job
            comments_text = "\n\n".join([f"{comment['author']} [{comment['created_at']}]: {comment['text']}" for comment in job.comments])
            archived_job = ArchivedJob.objects.create(
                original_id=job.id,
                title=job.title,
                description=job.description,
                requester=job.requester,
                assignee=job.assignee,
                queue=job.queue,
                created_at=job.created_at,
                closed_at=job.closed_at,
                status=job.status,
                comments=comments_text
            )

            job.archive_id = archived_job.archive_id
            job.save()

            self.caller.msg(f"Job #{job_id} has been {new_status} and archived.")
            
            # Send mail notifications
            notification_message = f"Job #{job_id} has been {new_status}.\n\nReason: {reason}"
            self.send_mail_notification(job, notification_message)
            
            self.post_to_jobs_channel(self.caller.name, job.id, new_status)

        except Job.DoesNotExist:
            self.caller.msg(f"Job #{job_id} not found.")

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
        
        # Create the header row
        header_row = "|cJob #  Queue      Job Title                 Started  Assignee          Status|n"
        output += header_row + "\n"
        output += ANSIString("|r" + "-" * 78 + "|n") + "\n"

        # Add each job as a row
        for job in jobs:
            assignee = job.assignee.username if job.assignee else "-----"
            row = (
                f"{job.id:<6}"
                f"{crop(job.queue.name, width=10):<11}"
                f"{crop(job.title, width=25):<25}"
                f"{job.created_at.strftime('%m/%d/%y'):<9}"
                f"{crop(assignee, width=17):<18}"
                f"{job.status}"
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

def create_jobs_help_entry():
    """Create or update the jobs help entry."""
    try:
        help_entry, created = HelpEntry.objects.get_or_create(
            db_key="jobs",
            defaults={
                "db_help_category": "General",
                "db_entrytext": CmdJobs.__doc__
            }
        )
        
        if not created:
            help_entry.db_entrytext = CmdJobs.__doc__
            help_entry.db_help_category = "General"
            help_entry.save()

        # Set tags properly using the set() method
        help_entry.db_tags.set(["jobs", "requests", "admin"], category="help")
        
        return help_entry
    except Exception as e:
        print(f"Error creating help entry: {str(e)}")
        return None

# Call this when the module is loaded
create_jobs_help_entry()

class JobSystemCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdJobs())
