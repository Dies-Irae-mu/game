"""
Weekly XP distribution script.

This module handles automated XP distribution and monitoring for characters.
Includes safeguards against concurrent modifications and proper error handling.
"""
from evennia.scripts.scripts import DefaultScript
from datetime import datetime, timezone
from decimal import Decimal, DecimalException
from evennia.utils import gametime
from typeclasses.characters import Character
from evennia import logger
from django.db import transaction, DatabaseError
from evennia.scripts.models import ScriptDB
from evennia import create_script
from django.core.exceptions import ObjectDoesNotExist

# Use Evennia's built-in logger instead of setup_log
log = logger.log_trace()

class WeeklyXPScript(DefaultScript):
    """A script that runs weekly to award XP."""
    
    def at_script_creation(self):
        """Called when script is first created."""
        self.key = "WeeklyXP"
        self.desc = "Awards weekly XP to active characters"
        self.interval = 3600  # 1 hour in seconds
        self.persistent = True
        self.start_delay = True
        
    def at_start(self):
        """
        Called when script starts running.
        
        Raises:
            ValueError: If gametime calculation fails
            AttributeError: If script attributes are missing
        """
        try:
            self.ndb.next_repeat = gametime.gametime(absolute=True) + self.interval
        except (ValueError, AttributeError) as e:
            log.error(f"Error in WeeklyXPScript at_start: {e}")
            raise
    
    def at_server_reload(self):
        """
        Called when server reloads.
        
        Handles:
            AttributeError: If task attribute doesn't exist
            RuntimeError: If task stopping fails
        """
        try:
            if hasattr(self, 'task'):
                self.task.stop()
        except (AttributeError, RuntimeError) as e:
            log.error(f"Error in WeeklyXPScript at_server_reload: {e}")
        
    def at_server_shutdown(self):
        """
        Called at server shutdown.
        
        Handles:
            AttributeError: If task attribute doesn't exist
            RuntimeError: If task stopping fails
        """
        try:
            if hasattr(self, 'task'):
                self.task.stop()
        except (AttributeError, RuntimeError) as e:
            log.error(f"Error in WeeklyXPScript at_server_shutdown: {e}")
            
    def _pause_task(self, auto_pause=False):
        """
        Override default pause behavior.
        
        Args:
            auto_pause (bool): Whether pause was triggered automatically
            
        Handles:
            AttributeError: If task attribute doesn't exist
            RuntimeError: If task stopping fails
        """
        try:
            if hasattr(self, 'task'):
                self.task.stop()
        except (AttributeError, RuntimeError) as e:
            log.error(f"Error in WeeklyXPScript _pause_task: {e}")
            
    def at_repeat(self):
        """
        Called every week to distribute XP.
        
        Handles:
            DatabaseError: For database-related errors
            DecimalException: For XP calculation errors
            ObjectDoesNotExist: If character objects are missing
            ValueError: For invalid data values
        """
        try:
            current_time = timezone.now()
            log.info(f"WeeklyXP script running at {current_time}")

            characters = Character.objects.filter(db_typeclass_path__contains='characters.Character')
            log.info(f"Found {len(characters)} characters to process")

            awarded_count = 0
            for char in characters:
                try:
                    with transaction.atomic():
                        self._process_character_xp(char, current_time)
                        awarded_count += 1
                except (DatabaseError, DecimalException, ValueError) as e:
                    log.error(f"Error processing XP for {char.key}: {str(e)}")
                    continue

            log.info(f"\nWeekly XP distribution completed. Awarded XP to {awarded_count} active characters.")

        except Exception as e:
            log.error(f"Critical error during XP distribution: {str(e)}")
            raise

    def _process_character_xp(self, char, current_time):
        """
        Process XP for a single character.
        
        Args:
            char (Character): Character to process
            current_time (datetime): Current timestamp
            
        Raises:
            ValueError: If XP data is invalid
            DecimalException: If XP calculations fail
            DatabaseError: If database operations fail
        """
        log.info(f"\nProcessing character: {char.key}")
        
        if char.check_permstring("builders"):
            log.info(f"Skipping {char.key} - is staff")
            return

        xp_data = char.db.xp or self._initialize_xp_data()
        scenes_this_week = xp_data.get('scenes_this_week', 0)
        
        if scenes_this_week > 0:
            char.refresh_from_db()
            xp_data = char.db.xp
            
            if xp_data.get('scenes_this_week', 0) > 0:
                self._award_xp(char, xp_data, current_time)

    def _initialize_xp_data(self):
        """
        Initialize fresh XP data structure.
        
        Returns:
            dict: Default XP data structure
            
        Raises:
            DecimalException: If decimal conversion fails
        """
        return {
            'total': Decimal('0.00'),
            'current': Decimal('0.00'),
            'spent': Decimal('0.00'),
            'ic_earned': Decimal('0.00'),
            'monthly_spent': Decimal('0.00'),
            'spends': [],
            'last_scene': None,
            'scenes_this_week': 0
        }

class XPMonitor(DefaultScript):
    """Monitors XP changes for characters"""
    
    def at_start(self):
        """Called when script starts running"""
        self.db.last_xp_states = {}
        self.record_current_states()
    
    def record_current_states(self):
        """
        Record current XP states for all characters.
        
        Handles:
            DatabaseError: For database-related errors
            ObjectDoesNotExist: If character objects are missing
        """
        try:
            with transaction.atomic():
                characters = Character.objects.filter(db_typeclass_path__contains='characters.Character')
                
                for char in characters:
                    try:
                        xp_data = char.db.xp
                        if xp_data:
                            self.db.last_xp_states[char.key] = xp_data.copy()
                    except (AttributeError, KeyError) as e:
                        log.warn(f"Could not record XP state for {char.key}: {e}")
        except DatabaseError as e:
            log.error(f"Database error in record_current_states: {e}")
    
    def at_repeat(self):
        """
        Called every minute to check for XP changes.
        
        Handles:
            DatabaseError: For database-related errors
            ObjectDoesNotExist: If character objects are missing
        """
        try:
            with transaction.atomic():
                characters = Character.objects.filter(db_typeclass_path__contains='characters.Character')
                
                for char in characters:
                    try:
                        self._check_character_xp(char)
                    except (AttributeError, KeyError) as e:
                        log.warn(f"Error checking XP for {char.key}: {e}")
        except DatabaseError as e:
            log.error(f"Database error in at_repeat: {e}")

    def _check_character_xp(self, char):
        """
        Check XP changes for a single character.
        
        Args:
            char (Character): Character to check
            
        Raises:
            AttributeError: If XP data is missing
            KeyError: If XP data structure is invalid
        """
        current_xp = char.db.xp
        last_xp = self.db.last_xp_states.get(char.key)
        
        if last_xp and current_xp != last_xp:
            log.info(f"XP change detected for {char.key}:")
            log.info(f"Previous state: {last_xp}")
            log.info(f"Current state: {current_xp}")
            log.info(f"Change timestamp: {timezone.now()}")
            
            self.db.last_xp_states[char.key] = current_xp.copy()

def start_xp_monitor():
    """
    Start the XP monitor script if it's not already running.
    
    Returns:
        Script: The XP monitor script instance
        
    Raises:
        DatabaseError: If script creation fails
    """
    try:
        with transaction.atomic():
            existing = ScriptDB.objects.filter(db_key="xp_monitor")
            if not existing:
                script = create_script(
                    "typeclasses.scripts.xp_monitor.XPMonitor",
                    key="xp_monitor",
                    desc="Monitors XP changes",
                    interval=60,  # Check every minute
                    persistent=True
                )
                return script
            return existing[0]
    except DatabaseError as e:
        log.error(f"Failed to start XP monitor: {e}")
        raise 