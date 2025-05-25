"""
NPC-related scripts for Dies Irae.

This module contains scripts that handle NPC functionalities:
- NPCExpirationScript: Delete temporary NPCs after their lifespan expires
"""

from evennia.scripts.scripts import DefaultScript
from datetime import datetime
from evennia.utils import logger


class NPCExpirationScript(DefaultScript):
    """
    Script to handle expiration of temporary NPCs.
    
    This script runs periodically and checks if a temporary NPC's
    expiration time has passed. If it has, the NPC is deleted.
    """
    def at_script_creation(self):
        """
        Setup the script when it's created.
        """
        self.key = f"npc_expiration_{self.obj.id}"
        self.desc = f"Handles expiration of temporary NPC {self.obj.key}"
        self.interval = 3600  # Check every hour
        self.persistent = True
        self.start_delay = True
        
    def at_start(self):
        """
        Called when the script is started.
        """
        # Make sure we have an object attached
        if not self.obj:
            self.stop()
            return
            
        logger.log_info(f"Starting NPC expiration script for {self.obj.key}")
    
    def at_repeat(self):
        """
        Called every self.interval seconds.
        """
        # Check if the NPC still exists
        if not self.obj:
            self.stop()
            return
            
        # Check if this is a temporary NPC
        if not getattr(self.obj.db, "is_temporary", False):
            self.stop()
            return
            
        # Check if expiration time has passed
        if not self.obj.db.expiration_time:
            return
            
        now = datetime.now()
        if now > self.obj.db.expiration_time:
            # Log the expiration
            location = self.obj.location
            logger.log_info(f"Temporary NPC {self.obj.key} has expired and will be deleted")
            
            # Send notification to the location if it exists
            if location:
                location.msg_contents(f"{self.obj.key} has left the scene.")
                
            # Delete the NPC
            self.obj.delete()
            self.stop()
    
    def at_server_reload(self):
        """
        Called when the server reloads.
        Make sure to update the expiration check on reload.
        """
        # Force a check after reload
        self.at_repeat() 