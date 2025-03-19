from django.db import models
from django.utils import timezone
from world.wod20th.models import Roster
from world.plots.models import Plot
from world.jobs.models import Job
from evennia.utils.idmapper.models import SharedMemoryModel

class Situation(SharedMemoryModel):
    """
    Model representing a Situation.
    """
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    roster_names = models.JSONField(default=list, blank=True)
    staff_notes = models.TextField(blank=True)
    related_jobs = models.ManyToManyField(Job, related_name='related_situations', blank=True)
    related_plots = models.ManyToManyField(Plot, related_name='related_situations', blank=True)

    class Meta:
        app_label = 'situations'

    def __str__(self):
        return f"{self.id}: {self.title}"

class Detail(SharedMemoryModel):
    """
    Model representing a Detail within a Situation.
    """
    situation = models.ForeignKey(Situation, on_delete=models.CASCADE, related_name='details')
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    roster_names = models.JSONField(default=list, blank=True)
    secrecy_rating = models.IntegerField(default=0)
    staff_notes = models.TextField(blank=True)

    class Meta:
        app_label = 'situations'

    def __str__(self):
        return f"{self.situation.id}.{self.id}: {self.title}"

class Development(SharedMemoryModel):
    """
    Model representing a Development within a Situation.
    """
    situation = models.ForeignKey(Situation, on_delete=models.CASCADE, related_name='developments')
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    roster_names = models.JSONField(default=list, blank=True)
    resolved = models.BooleanField(default=False)
    resolution_text = models.TextField(blank=True, null=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    staff_notes = models.TextField(blank=True)

    class Meta:
        app_label = 'situations'

    def __str__(self):
        return f"{self.situation.id}.{self.id}: {self.title}" 