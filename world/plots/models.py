from django.db import models
from evennia.utils.idmapper.models import SharedMemoryModel
from django.conf import settings

STATUS_CHOICES = [
    ('NEW', 'New'),
    ('ACTIVE', 'Active'),
    ('INACTIVE', 'Inactive'),
    ('ON_HOLD', 'On Hold'),
    ('COMPLETED', 'Completed'),
    ('CANCELLED', 'Cancelled'),
]

RISK_LEVEL_CHOICES = [
    ('LOW', 'Low'),
    ('MODERATE', 'Moderate'),
    ('HIGH', 'High'),
    ('EXTREME', 'Extreme'),
]

class Plot(SharedMemoryModel):
    """
    A model representing a plot that can be run by storytellers.
    """
    class Meta:
        app_label = 'plots'

    title = models.CharField(max_length=100)
    description = models.TextField()
    participants = models.ManyToManyField('objects.ObjectDB', related_name='plots')
    payout = models.CharField(max_length=30)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='NEW')
    storyteller = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='player_storytellers', null=True, blank=True, on_delete=models.SET_NULL)
    claimed = models.BooleanField(default=False)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default='LOW')
    genre = models.CharField(max_length=30)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    next_session = models.DateTimeField(null=True, blank=True)
    related_situations = models.JSONField(default=list, blank=True)  # Store situation IDs as a list

    def __str__(self):
        return f"{self.id}: {self.title}"
    
class Session(SharedMemoryModel):
    """
    A model representing a session within a plot.
    """
    class Meta:
        app_label = 'plots'

    plot = models.ForeignKey(Plot, related_name='sessions', on_delete=models.CASCADE)
    date = models.DateTimeField()
    duration = models.DurationField()
    location = models.CharField(max_length=100)
    participants = models.ManyToManyField('objects.ObjectDB', related_name='sessions')
    description = models.TextField()
    secrets = models.TextField()

"""
+--------------------------------+ +Plot Info +--------------------------------+
Plot Name:           Interception!
Storyteller:         John Doe
Risk:                Moderate
Payout:              Money and Guns
Status:              Active
Claimed:             Yes
Genre:               Crime
Date Created:        2025-01-01
Date Modified:       2025-01-12
Next Session:        2025-01-19
+---------------------------------+ Synopsis +---------------------------------+
Criminal types have been hired to intercept a shipment from the docks and 
deliver it to a new recipient.
+---------------------------------+ Secrets +----------------------------------+
What the players might not know without investigating into it, is that the 
shipment is 10 kilos of pure south american nose-candy and the people the 
load is being stolen from are part of The Outfit, a local Italian mob family. 
The recipients are Latin Kings.
+------------------------------------------------------------------------------+
"""

"""
+---------------------------------+ +Session Info +-----------------------------+
Session:             1
Date:                2025-01-19
Time:                19:00
Duration:            2 hours
Location:            The docks
Participants:        John Doe, Jane Doe, John Smith, Jane Smith
+---------------------------------+ Description +-------------------------------+
The players are tasked with intercepting the shipment and delivering it to the 
recipients. They are given a list of potential targets and locations to check.
+---------------------------------+ Secrets +----------------------------------+
The players might not know without investigating into it, is that the 
shipment is 10 kilos of pure south american nose-candy and the people the 
load is being stolen from are part of The Outfit, a local Italian mob family. 
The recipients are Latin Kings.
+------------------------------------------------------------------------------+
""" 

"""
+---------------------------------+ +Session Info +-----------------------------+
Session:             2
Date:                2025-01-26
Time:                19:00
Duration:            3 hours
Location:            La Jolla Caves
Participants:        John Doe, Jane Doe, John Smith, Jane Smith
+---------------------------------+ Description +-------------------------------+
The players take the shipment to the La Jolla Caves and are tasked with 
protecting it from attempts to recover it by The Outfit.
+---------------------------------+ Secrets +----------------------------------+
The Outfit includes several ghouls, and the players might not know without 
doing some additional legwork into Vampires that may be influencing this
operation.
+------------------------------------------------------------------------------+
"""
"""
+-------------------------------+ +Plots Info +--------------------------------+
| Number:   | Plot Name:               | Risk:     | Claimed By:   | Status  |
+------------------------------------------------------------------------------+
  1           Interception!              Moderate    Nobody          -           
  2           The Bloody Hand            Moderate    Nobody          -          
+------------------------------------------------------------------------------+
"""