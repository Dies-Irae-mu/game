"""
Script for checking puppet inactivity and freezing inactive characters.

This script will:
1. Check all puppets for last login
2. If a puppet hasn't logged in for 60 days, freeze them
3. Send a mail notification about the freezing
"""

from evennia.utils import search
from evennia.utils.logger import log_info
from evennia.scripts.scripts import DefaultScript as Script
from evennia.utils import create
from datetime import datetime, timedelta
from django.utils.timezone import now

INACTIVE_DAYS = 60  # Number of days before a puppet is considered inactive
FREEZER_ROOM = "#2029"  # Dbref of the freezer room

class PuppetFreezeScript(Script):
    """
    Script for checking and freezing inactive puppets.
    """
    
    def at_script_creation(self):
        """Set up the script."""
        self.key = "puppet_freeze_check"
        self.desc = "Checks for and freezes inactive puppets"
        self.interval = 86400  # Run once per day
        self.persistent = True
        
    def at_repeat(self):
        """
        Called every self.interval seconds.
        Check all puppets and freeze those that are inactive.
        """
        log_info("Starting puppet freeze check...")
        
        # Get all character objects
        characters = search.search_object_by_typeclass("typeclasses.characters.Character")
        current_time = now()
        inactive_threshold = current_time - timedelta(days=INACTIVE_DAYS)
        
        for char in characters:
            # Skip characters that aren't approved or are already frozen
            if not char.db.approved:
                continue
                
            # Get the last login time
            if char.db.last_login:
                last_login = char.db.last_login
            elif hasattr(char, 'last_login') and char.last_login:
                last_login = char.last_login
            else:
                # If no login time found, use character creation time
                last_login = char.date_created
            
            # Check if character is inactive
            if last_login < inactive_threshold:
                self.freeze_puppet(char)
                
        log_info("Puppet freeze check completed.")
    
    def freeze_puppet(self, puppet, reason="inactivity", admin=None):
        """
        Freeze an inactive puppet by unapproving them and sending a notification.
        
        Args:
            puppet (Character): The puppet to freeze
            reason (str): Reason for freezing (default: "inactivity")
            admin (Account): Admin who initiated the freeze (if manual)
        """
        # Set character as unapproved
        puppet.db.approved = False
        
        # Move to freezer room
        freezer = search.search_object(FREEZER_ROOM)[0]
        if freezer and puppet.location:
            puppet.location = freezer
            log_info(f"Moved {puppet.name} to freezer room")
        
        # Create the mail message
        subject = "Character Frozen"
        if reason == "inactivity":
            message = (
                f"Your character {puppet.name} has been unapproved due to inactivity "
                f"(no login for {INACTIVE_DAYS} days or more).\n\n"
                f"To reactivate your character, please contact staff.\n\n"
                f"Last login: {puppet.db.last_login}\n"
                f"Freeze date: {now()}"
            )
        else:
            message = (
                f"Your character {puppet.name} has been frozen.\n\n"
                f"Reason: {reason}\n"
                f"Admin: {admin.name if admin else 'System'}\n"
                f"Freeze date: {now()}\n\n"
                f"To discuss this, please contact staff."
            )
        
        # Get the puppet's account
        if puppet.account:
            # Send mail to the account
            try:
                puppet.account.mail(subject, message, sender="System")
                log_info(f"Sent freeze notification to {puppet.account} for character {puppet.name}")
            except Exception as e:
                log_info(f"Error sending freeze mail to {puppet.account}: {str(e)}")
        
        log_info(f"Frozen puppet: {puppet.name} (Reason: {reason})")

def start_puppet_freeze_script():
    """
    Start the puppet freeze checking script if it's not already running.
    """
    try:
        # Check if script already exists
        existing = search.search_script("puppet_freeze_check")
        if not existing:
            script = create.create_script("world.wod20th.scripts.puppet_freeze.PuppetFreezeScript")
            return True, "Puppet freeze checking script started"
        return False, "Puppet freeze checking script already running"
    except Exception as e:
        return False, f"Error starting puppet freeze script: {str(e)}" 