"""
Weekly XP distribution script.

This module handles automated XP distribution and monitoring for characters.
Includes safeguards against concurrent modifications and proper error handling.
"""
from evennia.scripts.scripts import DefaultScript
from datetime import datetime, timezone, timedelta
from decimal import Decimal, DecimalException
from evennia.utils import gametime
from typeclasses.characters import Character
from evennia import logger
from django.db import transaction, DatabaseError
from evennia.scripts.models import ScriptDB
from evennia import create_script
from django.core.exceptions import ObjectDoesNotExist
from evennia.commands.default.muxcommand import MuxCommand
import logging
from evennia.objects.models import ObjectDB
from django.db.models import Q

# Initialize logger properly
log = logging.getLogger('evennia')

WEEKLY_XP_AMOUNT = 4  # Standard weekly XP award
WEEKLY_SECONDS = 7 * 24 * 60 * 60  # 7 days in seconds

class CmdDebugXP(MuxCommand):
    """
    Debug XP and scene tracking

    Usage:
      +debugxp
      +debugxp <character>
      +debugxp/check <character> - Check if current location is valid for scenes
      +debugxp/force <character> - Force initialize scene data
      +debugxp/scene <character> - Force start a scene for character

    Shows detailed information about XP and scene tracking for testing purposes.
    Works on both online and offline characters.
    """
    
    key = "+debugxp"
    locks = "cmd:perm(Wizards)"
    help_category = "Admin Commands"
    aliases = ["+xpdebug"]
    
    def _find_character(self, search_string):
        """Find a character by name, including offline characters."""
        if not search_string:
            return None
            
        # Search for characters matching the name (case-insensitive)
        matches = ObjectDB.objects.filter(
            Q(db_typeclass_path__contains='characters.Character'),
            Q(db_key__iexact=search_string) | 
            Q(db_tags__db_key__iexact=search_string, db_tags__db_category='alias')
        ).distinct()
        
        if not matches:
            self.caller.msg(f"No character found matching '{search_string}'.")
            return None
            
        if len(matches) > 1:
            self.caller.msg("Multiple matches found:")
            for match in matches:
                self.caller.msg(f" - {match.key} ({match.dbref})")
            return None
            
        return matches[0]
    
    def _check_scene_location(self, char):
        """Check if character's location is valid for scenes."""
        if not char.location:
            return False, "No location"
            
        # Must be IC room
        if (hasattr(char.location, 'db') and 
            getattr(char.location.db, 'roomtype', None) == 'OOC Area'):
            return False, "OOC Area"
            
        # Must have other players present
        other_players = [
            obj for obj in char.location.contents 
            if (obj != char and 
                hasattr(obj, 'has_account') and 
                obj.has_account and
                obj.db.in_umbra == char.db.in_umbra)  # Must be in same realm
        ]
        
        if not other_players:
            return False, "No other players present"
            
        return True, f"Valid scene location with {len(other_players)} other players"
    
    def _force_init_scene_data(self, char):
        """Force initialize scene data for a character."""
        if not char.db.scene_data:
            char.db.scene_data = {
                'current_scene': None,
                'scene_location': None,
                'last_activity': None,
                'completed_scenes': 0,
                'last_weekly_reset': datetime.now()
            }
            char.attributes.add('scene_data', char.db.scene_data)
        return "Scene data initialized"
        
    def _force_start_scene(self, char):
        """Force start a scene for a character."""
        valid, reason = self._check_scene_location(char)
        if not valid:
            return f"Cannot start scene: {reason}"
            
        now = datetime.now()
        if not char.db.scene_data:
            self._force_init_scene_data(char)
            
        scene_data = char.db.scene_data
        scene_data['current_scene'] = now
        scene_data['scene_location'] = char.location
        scene_data['last_activity'] = now
        char.attributes.add('scene_data', scene_data)
        return "Scene started"
    
    def func(self):
        if not self.caller.check_permstring("builders"):
            self.caller.msg("Permission denied.")
            return
            
        # Parse switches
        if "check" in self.switches:
            target = self._find_character(self.args.strip())
            if not target:
                return
            valid, reason = self._check_scene_location(target)
            self.caller.msg(f"Scene location check for {target.key} ({target.dbref}): {reason}")
            return
            
        if "force" in self.switches:
            target = self._find_character(self.args.strip())
            if not target:
                return
            result = self._force_init_scene_data(target)
            self.caller.msg(f"Force init for {target.key} ({target.dbref}): {result}")
            return
            
        if "scene" in self.switches:
            target = self._find_character(self.args.strip())
            if not target:
                return
            result = self._force_start_scene(target)
            self.caller.msg(f"Force scene start for {target.key} ({target.dbref}): {result}")
            return

        # Get target character
        if self.args:
            target = self._find_character(self.args.strip())
            if not target:
                return
        else:
            target = self.caller
            
        # Get scene data
        scene_data = target.db.scene_data or {}
        xp_data = target.db.xp or {}
        
        # Format the output
        msg = f"|wScene and XP Debug Info for {target.key} ({target.dbref})|n\n"
        msg += "=" * 78 + "\n\n"
        
        # Online Status
        msg += f"|yCharacter Status:|n {'|gOnline|n' if target.has_account else '|rOffline|n'}\n\n"
        
        # Location Info
        if target.location:
            msg += f"|yLocation:|n {target.location.key} ({target.location.dbref})\n"
            if hasattr(target.location, 'db'):
                msg += f"Room Type: {getattr(target.location.db, 'roomtype', 'Not Set')}\n"
            msg += f"Other Characters Present: {len([obj for obj in target.location.contents if obj != target and hasattr(obj, 'has_account') and obj.has_account])}\n\n"
        else:
            msg += "|yLocation:|n None\n\n"
        
        # Scene Data
        msg += "|yScene Data:|n\n"
        msg += f"Current Scene: {scene_data.get('current_scene')}\n"
        msg += f"Scene Location: {scene_data.get('scene_location')}\n"
        msg += f"Last Activity: {scene_data.get('last_activity')}\n"
        msg += f"Completed Scenes: {scene_data.get('completed_scenes', 0)}\n"
        msg += f"Last Weekly Reset: {scene_data.get('last_weekly_reset')}\n\n"
        
        # XP Data
        msg += "|yXP Data:|n\n"
        msg += f"Total XP: {xp_data.get('total', 0)}\n"
        msg += f"Current XP: {xp_data.get('current', 0)}\n"
        msg += f"Spent XP: {xp_data.get('spent', 0)}\n"
        msg += f"IC XP: {xp_data.get('ic_xp', 0)}\n"
        msg += f"Monthly Spent: {xp_data.get('monthly_spent', 0)}\n"
        msg += f"Last Reset: {xp_data.get('last_reset')}\n"
        msg += f"Last Scene: {xp_data.get('last_scene')}\n"
        msg += f"Scenes This Week: {xp_data.get('scenes_this_week', 0)}\n\n"
        
        # Recent Activity
        msg += "|yRecent XP Activity:|n\n"
        spends = xp_data.get('spends', [])
        if spends:
            for entry in spends[:5]:
                msg += f"{entry['timestamp']} - {entry['type'].title()}: {entry['amount']} XP"
                if 'reason' in entry:
                    msg += f" ({entry['reason']})"
                msg += "\n"
        else:
            msg += "No recent XP activity.\n"
            
        # Add staff note about forcing XP update
        if self.caller.check_permstring("builders"):
            msg += "\n|yStaff Note:|n To force XP update for this character:\n"
            msg += "@py from evennia import GLOBAL_SCRIPTS; GLOBAL_SCRIPTS.weekly_xp_award._award_weekly_xp(obj)\n"
            msg += "Where obj is the character object (#dbref)"
            
        self.caller.msg(msg)

class WeeklyXPScript(DefaultScript):
    """A script that runs weekly to award XP."""
    
    def at_script_creation(self):
        """Called when script is first created."""
        self.key = "weekly_xp_award"
        self.desc = "Awards weekly XP to active characters"
        self.interval = WEEKLY_SECONDS  # 1 week in seconds
        self.persistent = True
        self.start_delay = True
        
        # Initialize last run time
        self.db.last_run = None
        
    def at_start(self):
        """
        Called when script starts running.
        """
        try:
            if not self.db.last_run:
                self.db.last_run = gametime.gametime(absolute=True)
            self.ndb.next_repeat = gametime.gametime(absolute=True) + self.interval
        except Exception as e:
            log.error(f"Error in WeeklyXPScript at_start: {e}")
            raise
    
    def at_server_reload(self):
        """Called when server reloads."""
        try:
            if hasattr(self, 'task'):
                self.task.stop()
        except Exception as e:
            log.error(f"Error in WeeklyXPScript at_server_reload: {e}")
        
    def at_server_shutdown(self):
        """Called at server shutdown."""
        try:
            if hasattr(self, 'task'):
                self.task.stop()
        except Exception as e:
            log.error(f"Error in WeeklyXPScript at_server_shutdown: {e}")
            
    def _award_weekly_xp(self, char):
        """
        Award weekly XP to a character if they qualify.
        """
        try:
            if not char:
                return False
            
            # Skip staff characters
            if char.check_permstring("builders"):
                return False
            
            # Initialize XP data if it doesn't exist
            if not hasattr(char.db, 'xp') or not char.db.xp:
                char.db.xp = {
                    'total': Decimal('0.00'),
                    'current': Decimal('0.00'),
                    'spent': Decimal('0.00'),
                    'ic_xp': Decimal('0.00'),
                    'monthly_spent': Decimal('0.00'),
                    'last_reset': datetime.now(),
                    'spends': [],
                    'last_scene': None,
                    'scenes_this_week': 0
                }
            
            # Check if they had any scenes this week
            scenes_this_week = char.db.xp.get('scenes_this_week', 0)
            if scenes_this_week > 0:
                # Award XP and reset scene counter
                prev_total = char.db.xp.get('total', Decimal('0.00'))
                prev_current = char.db.xp.get('current', Decimal('0.00'))
                prev_ic_xp = char.db.xp.get('ic_xp', Decimal('0.00'))
                
                # Award XP
                success = char.add_xp(WEEKLY_XP_AMOUNT, "Weekly Activity")
                if success:
                    # Update IC XP tracking
                    char.db.xp['ic_xp'] = prev_ic_xp + Decimal(str(WEEKLY_XP_AMOUNT))
                    # Reset scene counter
                    char.db.xp['scenes_this_week'] = 0
                    # Notify the character if they're online
                    if hasattr(char, 'msg'):
                        char.msg(f"|gYou received {WEEKLY_XP_AMOUNT} XP for Weekly Activity.|n")
                    return True
                else:
                    return False
                    
            return False
            
        except Exception as e:
            log.error(f"Error awarding XP to {char.key}: {e}")
            return False
            
    def at_repeat(self):
        """
        Called every week to distribute XP.
        """
        try:
            current_time = gametime.gametime(absolute=True)
            # Store last run time
            self.db.last_run = current_time

            characters = Character.objects.filter(db_typeclass_path__contains='characters.Character')

            awarded_count = 0
            for char in characters:
                try:
                    with transaction.atomic():
                        if self._award_weekly_xp(char):
                            awarded_count += 1
                except Exception as e:
                    log.error(f"Error processing XP for {char.key}: {str(e)}")
                    continue

        except Exception as e:
            log.error(f"Critical error during XP distribution: {str(e)}")
            raise

class XPMonitor(DefaultScript):
    """Monitors XP changes for characters"""
    
    def at_script_creation(self):
        """Called when script is first created."""
        self.key = "xp_monitor"
        self.desc = "Monitors XP changes"
        self.interval = 60  # Check every minute
        self.persistent = True
        self.start_delay = True
        
        # Initialize storage
        self.db.last_xp_states = {}
    
    def at_start(self):
        """Called when script starts running"""
        if not self.db.last_xp_states:
            self.db.last_xp_states = {}
        self.record_current_states()
    
    def record_current_states(self):
        """Record current XP states for all characters."""
        try:
            with transaction.atomic():
                characters = Character.objects.filter(db_typeclass_path__contains='characters.Character')
                
                for char in characters:
                    try:
                        xp_data = char.db.xp
                        if xp_data:
                            # Create a new dict with the values we want to track
                            state = {
                                'total': xp_data.get('total', Decimal('0.00')),
                                'current': xp_data.get('current', Decimal('0.00')),
                                'spent': xp_data.get('spent', Decimal('0.00')),
                                'ic_xp': xp_data.get('ic_xp', Decimal('0.00')),
                                'scenes_this_week': xp_data.get('scenes_this_week', 0)
                            }
                            self.db.last_xp_states[char.key] = state
                    except Exception as e:
                        log.error(f"Could not record XP state for {char.key}: {e}")
        except Exception as e:
            log.error(f"Database error in record_current_states: {e}")
    
    def at_repeat(self):
        """Called every minute to check for XP changes."""
        try:
            with transaction.atomic():
                characters = Character.objects.filter(db_typeclass_path__contains='characters.Character')
                
                for char in characters:
                    try:
                        self._check_character_xp(char)
                    except Exception as e:
                        log.error(f"Error checking XP for {char.key}: {e}")
        except Exception as e:
            log.error(f"Database error in at_repeat: {e}")

    def _check_character_xp(self, char):
        """Check XP changes for a single character."""
        try:
            if not self.db.last_xp_states:
                self.db.last_xp_states = {}
                
            current_xp = char.db.xp
            last_state = self.db.last_xp_states.get(char.key, {})
            
            if current_xp and last_state:
                # Check for changes in key values
                changed = False
                for key in ['total', 'current', 'spent', 'ic_xp', 'scenes_this_week']:
                    if current_xp.get(key) != last_state.get(key):
                        changed = True
                        break
                
                if changed:
                    # Update stored state without logging
                    new_state = {
                        'total': current_xp.get('total', Decimal('0.00')),
                        'current': current_xp.get('current', Decimal('0.00')),
                        'spent': current_xp.get('spent', Decimal('0.00')),
                        'ic_xp': current_xp.get('ic_xp', Decimal('0.00')),
                        'scenes_this_week': current_xp.get('scenes_this_week', 0)
                    }
                    self.db.last_xp_states[char.key] = new_state
                    
        except Exception as e:
            log.error(f"Error in _check_character_xp for {char.key}: {e}")

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