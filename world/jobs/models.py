from django.db import models
from evennia.utils.utils import lazy_property
from evennia.objects.models import ObjectDB  # Assuming objects are instances of ObjectDB
from django.utils import timezone
from evennia.utils.idmapper.models import SharedMemoryModel
from django.utils.functional import lazy
from django.db.models import Max
from evennia.accounts.models import AccountDB

# Remove this line:
# from evennia.utils import create

class Job(SharedMemoryModel):
    id = models.AutoField(primary_key=True)
    archive_id = models.IntegerField(null=True, blank=True, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    requester = models.ForeignKey("accounts.AccountDB", on_delete=models.CASCADE, related_name="requested_jobs")
    assignee = models.ForeignKey("accounts.AccountDB", null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_jobs")
    participants = models.ManyToManyField("accounts.AccountDB", related_name="participated_jobs", blank=True)
    queue = models.ForeignKey("Queue", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('open', 'Open'), ('claimed', 'Claimed'), ('closed', 'Closed'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled'), ('completed', 'Completed')], default='open')
    template_args = models.JSONField(default=dict)  # Actual values of the args provided during job creation
    approved = models.BooleanField(default=False)
    comments = models.JSONField(default=list)
    due_date = models.DateTimeField(null=True, blank=True)
    attached_objects = models.ManyToManyField(ObjectDB, through='JobAttachment', related_name="attached_jobs", blank=True)
    template = models.ForeignKey('JobTemplate', on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs')
    last_viewed = models.JSONField(default=dict)  # Store last viewed timestamps per user

    class Meta:
        app_label = 'jobs'

    def claim(self, user):
        if self.status == 'open':
            self.assignee = user
            self.status = 'claimed'
            self.save()
            # Check if the user has an active session
            if hasattr(user, 'sessions') and user.sessions.count():
                user.msg(f"You have been assigned to the job: {self.title}")

    def assign_to(self, user):
        self.assignee = user
        self.status = 'claimed'
        self.save()
        # Check if the user has an active session
        if hasattr(user, 'sessions') and user.sessions.count():
            user.msg(f"You have been reassigned to the job: {self.title}")


    def close(self, closer, reason=""):
        if self.status in ['closed', 'rejected']:
            return False, None, None, None

        self.status = "closed" if self.approved else "rejected"
        self.closed_at = timezone.now()
        self.save()

        # Archive the job
        comments_text = "\n\n".join([f"{comment['author']} [{comment['created_at']}]: {comment['text']}" for comment in self.comments])
        archived_job = ArchivedJob.objects.create(
            original_id=self.id,
            title=self.title,
            description=self.description,
            requester=self.requester,
            assignee=self.assignee,
            queue=self.queue,
            created_at=self.created_at,
            closed_at=self.closed_at,
            status=self.status,
            comments=comments_text
        )

        # Prepare mail summary
        recipients = [self.requester] + list(self.participants.all())
        if self.assignee:
            recipients.append(self.assignee)
        recipients = list(set(recipients))  # Remove duplicates

        subject = f"Job #{self.id} {self.status.capitalize()}: {self.title}"
        message = f"""
Job #{self.id} has been {self.status}.

Title: {self.title}
Requester: {self.requester.username}
Assignee: {self.assignee.username if self.assignee else 'N/A'}
Created: {self.created_at}
Closed: {self.closed_at}
Status: {self.status.capitalize()}

Description:
{self.description}

Closing Reason:
{reason}

Comments:
{comments_text}
        """

        if self.approved:
            self.execute_close_commands()

        return True, subject, message, recipients

    def execute_close_commands(self):
        # If there's a JobTemplate associated with this job, execute its close commands
        if hasattr(self, 'template') and self.template:
            for command in self.template.close_commands:
                # Here you would implement the logic to execute each command
                # This might involve parsing the command string and calling appropriate functions
                pass
        # If there are no close commands or no template, do nothing
        pass

    def save(self, *args, **kwargs):
        if not self.id:
            max_id = Job.objects.aggregate(Max('id'))['id__max'] or 0
            self.id = max_id + 1
        super().save(*args, **kwargs)

    def mark_viewed(self, account):
        """Mark the job as viewed by an account."""
        if not self.last_viewed:
            self.last_viewed = {}
        self.last_viewed[str(account.id)] = timezone.now().isoformat()
        self.save()

    def is_updated_since_last_view(self, account):
        """Check if the job has been updated since the account last viewed it."""
        if not self.last_viewed or str(account.id) not in self.last_viewed:
            return True
            
        last_viewed = timezone.datetime.fromisoformat(self.last_viewed[str(account.id)])
        
        # Check if any comments were added after last view
        if self.comments:
            latest_comment = max(
                timezone.datetime.fromisoformat(comment['created_at']) 
                for comment in self.comments
            )
            if latest_comment > last_viewed:
                return True
                
        # Check if status changed after last view
        if self.closed_at and self.closed_at > last_viewed:
            return True
            
        # Check if assignee changed after last view
        # Note: This would require adding a modified_at field to track such changes
        
        return False

class JobAttachment(SharedMemoryModel):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    object = models.ForeignKey(ObjectDB, on_delete=models.CASCADE)
    attached_to_arg = models.CharField(max_length=255, null=True, blank=True)  # Stores the template arg if applicable

    def __str__(self):
        return f"Attachment: {self.object.key} to Job #{self.job.job_number} (Arg: {self.attached_to_arg or 'None'})"

    class Meta:
        app_label = 'jobs'

class Queue(SharedMemoryModel):
    name = models.CharField(max_length=255)
    automatic_assignee = models.ForeignKey("accounts.AccountDB", null=True, blank=True, on_delete=models.SET_NULL, related_name="auto_assigned_queues")

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'jobs'

class JobTemplate(SharedMemoryModel):
    name = models.CharField(max_length=255)
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)
    close_commands = models.JSONField(default=list)  # Array of templated strings
    args = models.JSONField(default=dict)  # Expected args format, e.g., {"arg1": "description", "arg2": "description"}

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'jobs'

class ArchivedJob(SharedMemoryModel):
    original_id = models.IntegerField()
    archive_id = models.IntegerField(unique=True, default=0)
    title = models.CharField(max_length=255)
    description = models.TextField()
    requester = models.ForeignKey("accounts.AccountDB", on_delete=models.SET_NULL, null=True, related_name="archived_requested_jobs")
    assignee = models.ForeignKey("accounts.AccountDB", on_delete=models.SET_NULL, null=True, related_name="archived_assigned_jobs")
    queue = models.ForeignKey(Queue, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField()
    closed_at = models.DateTimeField()
    status = models.CharField(max_length=20)
    comments = models.TextField()

    def __str__(self):
        return f"Archived Job {self.original_id}: {self.title}"

    def save(self, *args, **kwargs):
        if not self.archive_id:
            # If archive_id is not set, get the maximum archive_id and increment by 1
            max_archive_id = ArchivedJob.objects.aggregate(Max('archive_id'))['archive_id__max'] or 0
            self.archive_id = max_archive_id + 1
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['archive_id']
        app_label = 'jobs'
