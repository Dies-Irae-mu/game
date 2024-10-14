# in mygame/world/requests/models.py

from django.db import models
from evennia.utils.idmapper.models import SharedMemoryModel
from evennia.accounts.models import AccountDB

class Request(SharedMemoryModel):
    CATEGORIES = [
        ('BUG', 'Bug'),
        ('BUILD', 'Build'),
        ('CGEN', 'Character Generation'),
        ('SUGGESTION', 'Suggestion'),
        ('TYPO', 'Typo'),
        ('LOGS', 'Logs'),
        ('PLOT', 'Plot'),
        ('PRP', 'Player-Run Plot'),
        ('PVP', 'PvP'),
        ('XP', 'Experience Points'),
        ('WIKI', 'Wiki'),
        ('GENERAL', 'General'),
        ('INFLUENCE', 'Influence'),
    ]

    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('OPEN', 'Open'),
        ('PENDING', 'Pending'),
        ('CLOSED', 'Closed'),
    ]

    category = models.CharField(max_length=10, choices=CATEGORIES)
    title = models.CharField(max_length=100)
    text = models.TextField()
    requester = models.ForeignKey(AccountDB, related_name='requests', on_delete=models.CASCADE)
    handler = models.ForeignKey(AccountDB, related_name='handled_requests', null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='NEW')
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}: {self.title}"

class Comment(SharedMemoryModel):
    request = models.ForeignKey(Request, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(AccountDB, related_name='request_comments', on_delete=models.CASCADE)
    text = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment on {self.request} by {self.author}"