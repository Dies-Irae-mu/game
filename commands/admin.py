from commands.communication import AdminCommand
from evennia.utils import logger
from evennia.commands.default.general import CmdLook
from evennia.utils.search import search_object
from typeclasses.characters import Character
from .housing import CmdVacate
from evennia import Command
from evennia.utils import search
from evennia.commands.default.muxcommand import MuxCommand
from evennia.locks import lockfuncs
from world.wod20th.scripts.puppet_freeze import start_puppet_freeze_script, PuppetFreezeScript
from evennia.utils.utils import inherits_from
from datetime import datetime
from world.wod20th.models import Roster, RosterMember
from django.utils import timezone
from utils.search_helpers import search_character
from evennia import default_cmds
from evennia.utils.search import search_object
from evennia.utils import evtable
from evennia.utils.utils import crop


class CmdApprove(AdminCommand):
    """
    Approve a player's character.

    Usage:
      approve <character_name>

    This command approves a player's character, removing the 'unapproved' tag
    and adding the 'approved' tag. This allows the player to start playing.
    The character will also be automatically added to the appropriate roster
    based on their sphere/type.
    """
    key = "approve"
    aliases = ["+approve"]
    locks = "cmd:perm(Admin)"
    help_category = "Admin Commands"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: +approve <character>")
            return
            
        # Use our new search helper
        target = search_character(self.caller, self.args)
        if not target:
            return

        # Check both tag and attribute for approval status
        is_approved = target.tags.has("approved", category="approval") and target.db.approved
        if is_approved:
            self.caller.msg(f"{target.name} is already approved.")
            return

        # Set both the tag and the attribute
        target.db.approved = True
        target.tags.remove("unapproved", category="approval")
        target.tags.add("approved", category="approval")
        
        # Determine character's sphere based on their splat
        sphere = 'Other'  # Default sphere with consistent capitalization
        if hasattr(target, 'db') and hasattr(target.db, 'stats'):
            stats = target.db.stats
            if stats and 'other' in stats and 'splat' in stats['other']:
                splat = stats['other']['splat'].get('Splat', {}).get('perm', '')
                if splat:
                    # Capitalize first letter for consistency
                    sphere = splat.capitalize()

        # Try to find a roster matching the sphere (case-insensitive)
        try:
            roster = Roster.objects.filter(sphere__iexact=sphere).first()
            if roster:
                # Add character to roster
                if not RosterMember.objects.filter(roster=roster, character=target).exists():
                    RosterMember.objects.create(
                        roster=roster,
                        character=target,
                        approved=True,
                        approved_by=self.caller.account,
                        approved_date=timezone.now()
                    )
                    self.caller.msg(f"Added {target.name} to the {roster.name} roster.")
            else:
                self.caller.msg(f"No roster found for sphere: {sphere}")
        except Exception as e:
            self.caller.msg(f"Error adding to roster: {str(e)}")
        
        logger.log_info(f"{target.name} has been approved by {self.caller.name}")

        self.caller.msg(f"You have approved {target.name}.")
        target.msg("Your character has been approved. You may now begin playing.")

class CmdUnapprove(AdminCommand):
    """
    Set a character's status to unapproved.

    Usage:
      unapprove <character_name>

    This command removes the 'approved' tag from a character and adds the 'unapproved' tag.
    This effectively reverts the character to an unapproved state, allowing them to use
    chargen commands again. The character will also be removed from any rosters they belong to.
    """
    key = "unapprove"
    aliases = ["+unapprove"]
    locks = "cmd:perm(Admin)"
    help_category = "Admin Commands"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: unapprove <character_name>")
            return

        # Use our new search helper
        target = search_character(self.caller, self.args)
        if not target:
            return

        # Check both tag and attribute for approval status
        is_approved = target.tags.has("approved", category="approval") or target.db.approved
        if not is_approved:
            self.caller.msg(f"{target.name} is already unapproved.")
            return

        # Remove approved status and add unapproved tag
        target.db.approved = False
        target.tags.remove("approved", category="approval")
        target.tags.add("unapproved", category="approval")
        
        # Remove from any rosters
        memberships = RosterMember.objects.filter(character=target)
        if memberships.exists():
            roster_names = [m.roster.name for m in memberships]
            memberships.delete()
            self.caller.msg(f"Removed {target.name} from the following rosters: {', '.join(roster_names)}")
        
        logger.log_info(f"{target.name} has been unapproved by {self.caller.name}")

        self.caller.msg(f"You have unapproved {target.name}.")
        target.msg("Your character has been unapproved. You may now use chargen commands again.")

class CmdMassUnapprove(AdminCommand):
    """
    Set all characters (both online and offline) to unapproved status.

    Usage:
      +massunapprove
      +massunapprove/confirm

    This command will list all characters that will be affected when run
    without the /confirm switch. Use /confirm to actually make the changes.
    This command affects ALL characters in the game, both online and offline.
    """

    key = "+massunapprove"
    locks = "cmd:perm(Admin)"
    help_category = "Admin Commands"

    def func(self):
        """Execute command."""
        caller = self.caller
        confirm = "confirm" in self.switches

        # Get all characters using Character typeclass
        all_chars = search_object("", typeclass=Character)
        
        # Filter to only get approved characters
        approved_chars = [char for char in all_chars 
                        if char.db.approved or char.tags.has("approved", category="approval")]
        
        if not approved_chars:
            caller.msg("No approved characters found.")
            return

        if not confirm:
            # Just show what would be affected
            msg = "The following characters would be set to unapproved:\n"
            for char in approved_chars:
                online_status = "online" if char.has_account else "offline"
                msg += f"- {char.name} ({online_status})\n"
            msg += f"\nTotal characters to be affected: {len(approved_chars)}"
            msg += "\nUse +massunapprove/confirm to execute the changes."
            caller.msg(msg)
            return

        # Actually make the changes
        count = 0
        for char in approved_chars:
            char.db.approved = False
            char.tags.add("unapproved", category="approval")
            if char.tags.has("approved", category="approval"):
                char.tags.remove("approved", category="approval")
            if char.has_account:  # Only message online characters
                char.msg("Your character has been set to unapproved status.")
            count += 1
            logger.log_info(f"{char.name} has been mass-unapproved by {caller.name}")

        caller.msg(f"Successfully set {count} character(s) to unapproved status.")

class CmdAdminLook(CmdLook, AdminCommand):
    """
    look at location or object

    Usage:
      look
      look <obj>
      look *<character>  (Admin only - global search)
      look [in|at|inside] <obj>

    Observes your location, an object, or a character globally with '*'.
    The 'in' preposition lets you look inside containers.
    """

    key = "look"
    aliases = ["l", "ls"]
    locks = "cmd:all()"
    help_category = "Admin Commands"

    def func(self):
        """Handle the looking."""
        caller = self.caller
        args = self.args.strip()
        
        # Handle global search for admin using *character format
        if args.startswith('*') and caller.check_permstring("Admin"):
            # Remove the * and any leading/trailing spaces
            target_name = args[1:].strip()
            # Use our new search helper
            target = search_character(caller, target_name)
            if not target:
                return
            # Show the target's description
            self.msg(target.return_appearance(caller))
            return
            
        # If not using * prefix, use the default look behavior
        super().func()

class CmdTestLock(MuxCommand):
    """
    Test a lock on a character
    
    Usage:
        @testlock <character> = <lockstring>
        
    Example:
        @testlock Nicole = has_splat(Mage)
        @testlock Nicole = has_tradition(Order of Hermes)
        @testlock Nicole = has_affiliation(Traditions)
    """
    
    key = "@testlock"
    locks = "cmd:perm(Admin)"
    help_category = "Admin Commands"
    
    def extract_value(self, data, *path):
        """Safely extract a nested value from a dictionary."""
        try:
            current = data
            self.caller.msg(f"DEBUG - Starting path traversal with type: {type(current)}")
            
            for key in path:
                if not hasattr(current, 'get'):
                    self.caller.msg(f"DEBUG - Object doesn't support get(): {type(current)}")
                    return None
                    
                current = current.get(key, {})
                self.caller.msg(f"DEBUG - After '{key}': {current} (type: {type(current)})")
            
            # If we have a dict with temp/perm, return temp value
            if hasattr(current, 'get'):
                if current.get('temp') is not None:
                    return current.get('temp')
                if current.get('perm') is not None:
                    return current.get('perm')
            return current
            
        except Exception as e:
            self.caller.msg(f"DEBUG - Error extracting {path}: {e}")
            import traceback
            self.caller.msg(traceback.format_exc())
            return None
            
    def get_character_value(self, char, *path):
        """Get a specific value from character stats."""
        stats = char.db.stats
        if not stats:
            self.caller.msg("Debug - No stats found on character")
            return None
            
        self.caller.msg(f"DEBUG - Getting value for path: {path}")
        self.caller.msg(f"DEBUG - Stats type: {type(stats)}")
        value = self.extract_value(stats, *path)
        self.caller.msg(f"DEBUG - Got value: {value}")
        return value
    
    def func(self):
        if not self.args or not self.rhs:
            self.caller.msg("Usage: @testlock <character> = <lockstring>")
            return
            
        # Use our new search helper
        char = search_character(self.caller, self.lhs)
        if not char:
            return
            
        self.caller.msg(f"Found character: {char.key}")
        
        # Show relevant character stats
        self.caller.msg("\nRelevant character stats:")
        
        # Update these paths to match the actual structure
        splat = self.get_character_value(char, 'other', 'splat', 'Splat')
        tradition = self.get_character_value(char, 'identity', 'lineage', 'Tradition')
        faction = self.get_character_value(char, 'identity', 'lineage', 'Mage Faction')
        
        # Debug output
        self.caller.msg("\nRaw stats structure:")
        self.caller.msg(f"Type: {type(char.db.stats)}")
        self.caller.msg(str(char.db.stats))
        
        self.caller.msg("\nExtracted values:")
        self.caller.msg(f"Splat: {splat}")
        self.caller.msg(f"Tradition: {tradition}")
        self.caller.msg(f"Faction: {faction}")
            
        try:
            # Parse the lock function and args
            lock_parts = self.rhs.split('(')
            lock_func = lock_parts[0]
            lock_args = lock_parts[1].rstrip(')').split(',')
            lock_args = [arg.strip() for arg in lock_args]
            
            self.caller.msg(f"\nTesting lock function: {lock_func}")
            self.caller.msg(f"With arguments: {lock_args}")
            
            # Get the actual function from our WoD lock functions
            from world.wod20th.locks import LOCK_FUNCS
            func = LOCK_FUNCS.get(lock_func)
            
            if func:
                self.caller.msg(f"\nLock function found: {func}")
                # Call the function directly for testing
                result = func(char, None, *lock_args)
                self.caller.msg(f"\nDirect function call result: {result}")
            else:
                self.caller.msg(f"\nWarning: Lock function '{lock_func}' not found in WoD lock functions")
                self.caller.msg("Available functions:")
                self.caller.msg(", ".join(sorted(LOCK_FUNCS.keys())))
            
            # Also test through normal lock system
            result = char.access(self.rhs)
            self.caller.msg(f"\nLock check result: {result}")
            
        except Exception as e:
            self.caller.msg(f"Error testing lock: {e}")
            import traceback
            self.caller.msg(traceback.format_exc())

class CmdPuppetFreeze(MuxCommand):
    """
    Manage the puppet freeze checking system.
    
    Usage:
        +freeze start     - Start the freeze checking script
        +freeze stop      - Stop the freeze checking script
        +freeze status    - Check if script is running
        +freeze check     - Run a check immediately
        +freeze <name> = <reason>  - Freeze specific character
        +freeze/unfreeze <name>    - Unfreeze a character
        
    This command manages the automatic freezing of inactive puppets.
    Frozen characters are moved to a special holding room and have
    their properties vacated.
    """
    
    key = "+freeze"
    aliases = ["freeze"]
    locks = "cmd:perm(Admin)"
    help_category = "Admin Commands"
    switch_options = ("unfreeze",)

    def freeze_character(self, char, reason, admin):
        """Handle the freezing process for a character"""
        # Store previous location for unfreezing
        char.db.pre_freeze_location = char.location
        
        # Handle housing - use existing vacate command
        vacate_cmd = CmdVacate()
        vacate_cmd.caller = admin
        vacate_cmd.args = f"force {char.name}"
        vacate_cmd.func()
        
        # Move to freeze room - use global search
        freeze_room = self.caller.search("#1935", global_search=True)
        if not freeze_room:
            self.caller.msg("Error: Freeze room #1935 not found!")
            return False
            
        # Set room type to prevent exit/speaking
        freeze_room.db.roomtype = "freezer"
        
        # Teleport character
        char.move_to(freeze_room, quiet=True)
        
        # Store freeze info
        char.db.frozen = {
            'reason': reason,
            'admin': admin,
            'date': datetime.now(),
            'pre_freeze_location': char.location
        }
        
        return True

    def unfreeze_character(self, char):
        """Handle the unfreezing process for a character"""
        if not char.db.frozen:
            self.caller.msg(f"{char.name} is not frozen.")
            return False
            
        # Get previous location
        prev_location = char.db.pre_freeze_location
        if not prev_location or prev_location.id == 1935:  # If previous location was freeze room
            prev_location = char.home or self.caller.search("#2", global_search=True)  # Fallback to limbo
            
        # Move character back
        char.move_to(prev_location, quiet=True)
        
        # Clear frozen status
        char.attributes.remove("frozen")
        char.attributes.remove("pre_freeze_location")
        
        return True

    def func(self):
        if not self.args:
            self.caller.msg("Usage: +freeze <start|stop|status|check|name=reason>")
            return
            
        # Handle unfreeze switch
        if "unfreeze" in self.switches:
            # Use our new search helper
            char = search_character(self.caller, self.args.strip())
            if not char:
                return
                
            if self.unfreeze_character(char):
                self.caller.msg(f"{char.name} has been unfrozen.")
            return

        # Check if it's a manual freeze with reason
        if "=" in self.args:
            name, reason = self.args.split("=", 1)
            name = name.strip()
            reason = reason.strip()
            
            # Use our new search helper
            char = search_character(self.caller, name)
            if not char:
                return
                
            if self.freeze_character(char, reason, self.caller):
                self.caller.msg(f"Character {char.name} has been frozen. Reason: {reason}")
            return

        option = self.args.strip().lower()
        
        if option == "start":
            success, msg = start_puppet_freeze_script()
            self.caller.msg(msg)
            
        elif option == "stop":
            # Find and stop the script
            scripts = search.search_script("puppet_freeze_check")
            if scripts:
                for script in scripts:
                    script.stop()
                self.caller.msg("Puppet freeze checking script stopped.")
            else:
                self.caller.msg("No puppet freeze checking script was running.")
                
        elif option == "status":
            # Check if script is running
            scripts = search.search_script("puppet_freeze_check")
            if scripts:
                script = scripts[0]
                self.caller.msg(f"Puppet freeze script is running. Next check in {script.time_until_next_repeat()} seconds.")
            else:
                self.caller.msg("Puppet freeze script is not running.")
                
        elif option == "check":
            # Run a check immediately
            scripts = search.search_script("puppet_freeze_check")
            if scripts:
                script = scripts[0]
                script.at_repeat()
                self.caller.msg("Puppet freeze check completed.")
            else:
                self.caller.msg("No puppet freeze script is running. Start it first.")
                
        else:
            self.caller.msg("Invalid option. Use: +freeze <start|stop|status|check|name=reason>")

class CmdSTTeleport(MuxCommand):
    """
    Storyteller teleport command to move objects/characters.

    Usage:
      +tel/switch [<object> to||=] <target location>

    Examples:
      +tel Limbo
      +tel/quiet box = Limbo
      +tel/tonone box

    Switches:
      quiet  - don't echo leave/arrive messages
      intoexit - teleport INTO the exit object
      tonone - teleport to None-location (ignored if target given)
      loc - teleport to target's location instead of contents
    """

    key = "+tel"
    aliases = ["+teleport"]
    locks = "cmd:perm(storyteller)"
    help_category = "Player Storyteller"
    switch_options = ("quiet", "intoexit", "tonone", "loc")
    rhs_split = ("=", " to ")

    def func(self):
        """Implements the command"""
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Usage: +tel [<obj> =] <destination>")
            return

        # Parse for destination vs object
        obj_to_teleport = caller
        destination = None
        if self.rhs:
            # Use our new search helper for characters, but allow other objects too
            obj_to_teleport = search_character(caller, self.lhs, quiet=True)
            if not obj_to_teleport:
                # If not a character, try regular search
                obj_to_teleport = caller.search(self.lhs, global_search=True)
            if not obj_to_teleport:
                return
            destination = caller.search(self.rhs, global_search=True)
        else:
            destination = caller.search(self.lhs, global_search=True)

        if not destination:
            caller.msg("Destination not found.")
            return

        if "loc" in self.switches:
            destination = destination.location
            if not destination:
                caller.msg("Destination has no location.")
                return

        # Do the teleport
        if obj_to_teleport.move_to(
            destination,
            quiet="quiet" in self.switches,
            emit_to_obj=caller,
            use_destination="intoexit" not in self.switches,
            move_type="teleport",
        ):
            if obj_to_teleport == caller:
                caller.msg(f"Teleported to {destination}.")
            else:
                caller.msg(f"Teleported {obj_to_teleport} -> {destination}.")
        else:
            caller.msg("Teleport failed.")

class CmdSummon(MuxCommand):
    """
    Summon a player or object to your location.

    Usage:
      +summon <character>
      +summon/quiet <character>
      +summon/debug <character> - Show additional diagnostic information

    Switches:
      quiet - Don't announce the summoning to the character
      debug - Display debug information about location storage
    """

    key = "+summon"
    locks = "cmd:perm(storyteller)"
    help_category = "Player Storyteller"
    switch_options = ("quiet", "debug")

    def func(self):
        """Implement the command"""
        caller = self.caller
        args = self.args.strip()
        debug_mode = "debug" in self.switches

        if not args:
            caller.msg("Usage: +summon <character>")
            return

        # Use our new search helper
        target = search_character(caller, args)
        if not target:
            return

        # Store their current location for +return
        if inherits_from(target, "evennia.objects.objects.DefaultCharacter"):
            original_location = target.location
            
            # Make sure the location is valid
            if original_location and hasattr(original_location, "id"):
                # Store location for return
                target.db.pre_summon_location = original_location
                
                if debug_mode:
                    caller.msg(f"DEBUG: Stored {original_location.name} (#{original_location.id}) as pre_summon_location for {target.name}")
            else:
                caller.msg(f"Warning: Could not store a valid original location for {target.name}")
                if debug_mode:
                    caller.msg(f"DEBUG: Current location is {original_location}")
            
        # Do the teleport
        if target.move_to(
            caller.location,
            quiet="quiet" in self.switches,
            emit_to_obj=caller,
            move_type="teleport",
        ):
            caller.msg(f"You have summoned {target.name} to your location.")
            if "quiet" not in self.switches:
                target.msg(f"{caller.name} has summoned you.")
            
            # Double-check storage worked
            if debug_mode and hasattr(target, "db"):
                if target.db.pre_summon_location:
                    stored_loc = target.db.pre_summon_location
                    caller.msg(f"DEBUG: Confirmed {target.name} has pre_summon_location: {stored_loc.name} (#{stored_loc.id})")
                else:
                    caller.msg(f"DEBUG: Failed to store pre_summon_location for {target.name}")
        else:
            caller.msg(f"Failed to summon {target.name}.")

class CmdReturn(MuxCommand):
    """
    Return a previously summoned character back to their original location.

    Usage:
      +return <character>
      +return/quiet <character>
      +return/all - Return all summoned characters in current location
      +return/force <character> - Use alternative location attributes if available
      +return/set <character> = <location> - Manually set return location

    Switches:
      quiet - Don't announce the return to the character
      all - Return all summoned characters in current location
      force - Try alternative location attributes (prelogout_location) if available
      set - Manually set a return location for a character
    """

    key = "+return"
    locks = "cmd:perm(storyteller)"
    help_category = "Player Storyteller"
    switch_options = ("quiet", "all", "force", "set")
    rhs_split = ("=",)

    def return_character(self, character, quiet=False, force=False):
        """Return a character to their pre-summon location"""
        # First try the primary location attribute
        if hasattr(character, "db") and character.db.pre_summon_location:
            prev_location = character.db.pre_summon_location
            location_type = "pre-summon"
        # If force is True, try alternative location attributes
        elif force and hasattr(character, "db"):
            # Try prelogout_location as fallback
            if character.db.prelogout_location:
                prev_location = character.db.prelogout_location
                location_type = "prelogout"
            else:
                self.caller.msg(f"{character.name} has no stored locations to return to.")
                return False
        else:
            self.caller.msg(f"{character.name} has no stored previous location to return to.")
            self.caller.msg("Use +return/force to try alternative location attributes, or +return/set to set one manually.")
            return False

        # Verify the location still exists
        if not prev_location or not prev_location.id:
            self.caller.msg(f"The previous {location_type} location for {character.name} no longer exists.")
            if location_type == "pre-summon":
                character.attributes.remove("pre_summon_location")
            return False
            
        # Move the character back
        if character.move_to(
            prev_location,
            quiet=quiet,
            emit_to_obj=self.caller,
            move_type="teleport",
        ):
            self.caller.msg(f"Returned {character.name} to their {location_type} location: {prev_location.name}.")
            if not quiet:
                character.msg(f"{self.caller.name} has returned you to your previous location.")
                
            # Clear the stored location if it was pre_summon_location
            if location_type == "pre-summon":
                character.attributes.remove("pre_summon_location")
            return True
        else:
            self.caller.msg(f"Failed to return {character.name}.")
            return False

    def func(self):
        """Implement the command"""
        caller = self.caller
        args = self.args.strip()
        quiet = "quiet" in self.switches
        force = "force" in self.switches

        # Handle setting a return location manually
        if "set" in self.switches:
            if not self.rhs:
                caller.msg("Usage: +return/set <character> = <location>")
                return
                
            # Use our new search helper
            target = search_character(caller, self.lhs)
            if not target:
                return
                
            destination = caller.search(self.rhs, global_search=True)
            if not destination:
                return
                
            # Set the pre_summon_location attribute
            target.db.pre_summon_location = destination
            caller.msg(f"Set return location for {target.name} to {destination.name}.")
            return

        if "all" in self.switches:
            # Return all summoned characters in the current location
            returned_count = 0
            for character in caller.location.contents:
                if inherits_from(character, "evennia.objects.objects.DefaultCharacter"):
                    if self.return_character(character, quiet, force):
                        returned_count += 1
                        
            if returned_count:
                caller.msg(f"Returned {returned_count} character(s) to their previous locations.")
            else:
                caller.msg("No characters with stored previous locations found here.")
            return

        if not args:
            caller.msg("Usage: +return <character>")
            return

        # Use our new search helper
        target = search_character(caller, args)
        if not target:
            return
            
        # Return the character
        self.return_character(target, quiet, force)

class CmdSTExamine(MuxCommand):
    """
    Get detailed information about an object

    Usage:
      +examine [<object>[/attrname]]
      +examine [*<account>[/attrname]]

    Examines an object in detail. If no object is specified,
    examines the current location.
    """

    key = "+examine"
    aliases = ["+ex", "+exam"]
    locks = "cmd:perm(storyteller)"
    help_category = "Player Storyteller"

    def func(self):
        """Handle command"""
        caller = self.caller
        args = self.args.strip()

        if not args:
            # If no arguments, examine location
            if hasattr(caller, "location"):
                obj = caller.location
            else:
                caller.msg("You need to supply a target to examine.")
                return
        else:
            # First try our character search helper
            obj = search_character(caller, args, quiet=True)
            if not obj:
                # If not a character, try regular search
                obj = caller.search(args, global_search=True)
            if not obj:
                return

        # Get object's cmdset for display
        cmdset = obj.cmdset.current

        # Display basic information
        string = f"|wExamining {obj.get_display_name(caller)}:|n\n"
        string += f"Type: {obj.typename} ({obj.typeclass_path})\n"
        if obj.location:
            string += f"Location: {obj.location}\n"
        if hasattr(obj, "destination") and obj.destination:
            string += f"Destination: {obj.destination}\n"

        # Display attributes
        string += "\n|wAttributes:|n\n"
        for attr in obj.attributes.all():
            string += f"  {attr.key} = {attr.value}\n"

        # Display tags
        if obj.tags.all():
            string += "\n|wTags:|n\n"
            for tag in obj.tags.all():
                string += f"  {tag}\n"

        caller.msg(string.strip())

class CmdSTFind(MuxCommand):
    """
    Search for objects in the game

    Usage:
      +find[/switches] <name or dbref or *account>
      +locate <name> - shorthand for +find/loc

    Switches:
      room  - only look for rooms
      exit  - only look for exits
      char  - only look for characters
      exact - only exact matches
      loc   - show location if single match
    """

    key = "+find"
    aliases = ["+search", "+locate"]
    locks = "cmd:perm(storyteller)"
    help_category = "Player Storyteller"
    switch_options = ("room", "exit", "char", "exact", "loc")

    def func(self):
        """Search implementation"""
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Usage: +find <name>")
            return

        # Handle locate alias
        if "locate" in self.cmdstring:
            self.switches.append("loc")

        # If searching specifically for characters
        if "char" in self.switches:
            # Use our character search helper
            target = search_character(caller, args, quiet=True)
            if target:
                results = [target]
            else:
                results = []
        else:
            # Search for matches
            results = caller.search(args, global_search=True, quiet=True)

        if not results:
            caller.msg(f"No matches found for '{args}'.")
            return

        # Filter by type if requested
        if any(switch in self.switches for switch in ("room", "exit", "char")):
            filtered = []
            for obj in results:
                if (
                    ("room" in self.switches and inherits_from(obj, "evennia.objects.objects.DefaultRoom"))
                    or ("exit" in self.switches and inherits_from(obj, "evennia.objects.objects.DefaultExit"))
                    or ("char" in self.switches and inherits_from(obj, "evennia.objects.objects.DefaultCharacter"))
                ):
                    filtered.append(obj)
            results = filtered

        # Display results
        if not results:
            caller.msg(f"No matches found for '{args}' with current filters.")
            return

        string = f"|w{len(results)} Match{'es' if len(results) != 1 else ''}:|n\n"
        for obj in results:
            string += f"  {obj.get_display_name(caller)} ({obj.typeclass_path})"
            if "loc" in self.switches and len(results) == 1 and obj.location:
                string += f" |w[Location: {obj.location}]|n"
            string += "\n"

        caller.msg(string.strip())

class CmdCheckGhosts(MuxCommand):
    """
    Check for ghost character objects in rooms.

    Usage:
      +checkghosts
      +checkghosts <room dbref or name>
      +checkghosts/cleanup - Attempt to clean up ghost characters

    This command is useful for identifying and resolving "ghost" character 
    objects that might have been left behind during teleportation operations.
    
    The cleanup switch attempts to remove ghost characters by forcing a proper
    disconnection on any orphaned character objects.
    """

    key = "+checkghosts"
    aliases = ["+ghostcheck"]
    locks = "cmd:perm(Admin)"
    help_category = "Admin Commands"

    def func(self):
        """Implement the command"""
        caller = self.caller
        args = self.args.strip()
        
        # Determine which room to check
        if args:
            target = caller.search(args, global_search=True)
            if not target:
                return
            rooms = [target]
        else:
            # Without args, check all rooms
            from typeclasses.rooms import Room
            rooms = search.search_object("", typeclass=Room)
        
        # Set for tracking sessions we've seen
        seen_sessions = set()
        total_ghosts = 0
        
        for room in rooms:
            ghosts = []
            
            # Check each character in the room
            for obj in [o for o in room.contents if inherits_from(o, "evennia.objects.objects.DefaultCharacter")]:
                # If the character has no sessions, it's not a ghost
                if not obj.sessions.all():
                    continue
                    
                # Check each session
                for session in obj.sessions.all():
                    session_id = id(session)
                    
                    # If we've seen this session on another character, this might be a ghost
                    if session_id in seen_sessions:
                        ghosts.append(obj)
                    else:
                        seen_sessions.add(session_id)
            
            # Report ghosts in this room
            if ghosts:
                total_ghosts += len(ghosts)
                ghost_names = [ghost.name for ghost in ghosts]
                caller.msg(f"Room {room.name} ({room.id}) contains potential ghost characters: {', '.join(ghost_names)}")
                
                # Clean up if the cleanup switch is used
                if "cleanup" in self.switches:
                    for ghost in ghosts:
                        # Force a disconnect/reconnect cycle to clean up
                        sessions = ghost.sessions.all()
                        for session in sessions:
                            session.msg("Admin is cleaning up ghost character instances...")
                            # Option 1: Try to reattach the session to its proper location
                            if hasattr(session, 'account') and session.account:
                                try:
                                    # Remove from location
                                    ghost.location = None
                                    caller.msg(f"Cleaned up ghost character {ghost.name}")
                                except Exception as e:
                                    caller.msg(f"Error cleaning up {ghost.name}: {e}")
        
        if args and not total_ghosts:
            caller.msg(f"No ghost characters found in {target.name}.")
        elif not args and not total_ghosts:
            caller.msg("No ghost characters found in any rooms.")
        else:
            caller.msg(f"Total potential ghost characters found: {total_ghosts}")
            if "cleanup" in self.switches:
                caller.msg("Cleanup attempt completed. You may need to run this command again.")
            else:
                caller.msg("Use /cleanup switch to attempt automatic cleanup of ghost characters.")

class CmdForceDeleteObject(MuxCommand):
    """
    Force-delete an object that refuses to be deleted normally.
    
    Usage:
      @forcedelete <#dbref>
      @forcedelete/quiet <#dbref>
      @forcedelete/uuid <uuid_string>
      
    Options:
      quiet - Don't show detailed debugging information
      uuid  - Delete by UUID instead of dbref
      
    This admin-only command bypasses normal deletion checks and goes straight
    to the database level to remove objects that resist normal deletion.
    Particularly useful for NPCs that get stuck in the database.
    
    For NPC objects, it will also try to stop any scripts and clear their
    registrations from rooms.
    """
    
    key = "@forcedelete"
    aliases = ["@forcedel", "@fdel"]
    locks = "cmd:perm(Admin)"
    help_category = "Admin Commands"
    
    def func(self):
        """Implements the command"""
        caller = self.caller
        args = self.args.strip()
        quiet = "quiet" in self.switches
        use_uuid = "uuid" in self.switches
        
        if not args:
            caller.msg("Usage: @forcedelete <#dbref or uuid>")
            return
            
        # Identify target
        target = None
        
        if use_uuid:
            # Search by UUID attribute
            from evennia.utils.search import search_object
            matches = []
            for obj in search_object(None):  # Search all objects
                if hasattr(obj, 'db') and obj.db.npc_id == args:
                    matches.append(obj)
            
            if not matches:
                caller.msg(f"No objects found with UUID {args}")
                return
            elif len(matches) > 1:
                caller.msg(f"Multiple objects found with UUID {args}, please use dbref")
                for obj in matches:
                    caller.msg(f" - {obj.name} ({obj.dbref})")
                return
            else:
                target = matches[0]
        else:
            # Standard search by dbref
            target = caller.search(args)
            
        if not target:
            return
        
        # Show object details
        if not quiet:
            caller.msg(f"Found object: {target.name} ({target.dbref})")
            caller.msg(f"Typeclass: {target.typeclass_path}")
            
        # Special handling for NPCs
        is_npc = False
        if hasattr(target, 'is_npc') and target.is_npc:
            is_npc = True
            if not quiet:
                caller.msg("Object is an NPC, performing special cleanup...")
                
            # Step 1: Stop any scripts on the NPC
            for script in target.scripts.all():
                if not quiet:
                    caller.msg(f"Stopping script: {script.key}")
                try:
                    script.stop()
                except Exception as e:
                    caller.msg(f"Error stopping script {script.key}: {e}")
            
            # Step 2: Unregister from all rooms
            if hasattr(target, 'db') and hasattr(target.db, 'registered_in_rooms'):
                registered_rooms = list(target.db.registered_in_rooms) if target.db.registered_in_rooms else []
                for room_dbref in registered_rooms:
                    if not quiet:
                        caller.msg(f"Unregistering from room: {room_dbref}")
                    try:
                        from evennia.utils.search import search_object
                        room = search_object(room_dbref)
                        if room and len(room) > 0:
                            room = room[0]
                            if hasattr(room, 'db_npcs') and target.key in room.db_npcs:
                                del room.db_npcs[target.key]
                    except Exception as e:
                        caller.msg(f"Error unregistering from room {room_dbref}: {e}")
            
            # Step 3: Clear all attributes
            if not quiet:
                caller.msg("Clearing attributes...")
            for attr in list(target.attributes.all()):
                try:
                    target.attributes.remove(attr.key)
                except Exception as e:
                    if not quiet:
                        caller.msg(f"Error removing attribute {attr.key}: {e}")
            
            # Step 4: Clear all locks
            if not quiet:
                caller.msg("Clearing locks...")
            target.locks.clear()
            
            # Step 5: Remove from location
            if target.location:
                if not quiet:
                    caller.msg(f"Removing from location: {target.location}")
                old_location = target.location
                target.location = None
        
        # Attempt standard deletion first
        if not quiet:
            caller.msg("Attempting standard deletion...")
        try:
            deleted = target.delete()
            if deleted:
                caller.msg(f"Successfully deleted {target.name} ({target.dbref}) via standard method.")
                return
            else:
                if not quiet:
                    caller.msg("Standard deletion failed, trying database-level deletion...")
        except Exception as e:
            if not quiet:
                caller.msg(f"Error during standard deletion: {e}")
        
        # Fallback to direct database deletion
        try:
            obj_id = target.id
            obj_name = target.name
            obj_dbref = target.dbref
            
            from django.apps import apps
            from django.db import connection
            
            # First try using the ORM
            ObjectDB = apps.get_model('objects', 'ObjectDB')
            count, details = ObjectDB.objects.filter(id=obj_id).delete()
            
            if count > 0:
                caller.msg(f"Successfully deleted {obj_name} ({obj_dbref}) from database. Affected {count} records.")
                if not quiet and details:
                    caller.msg(f"Deletion details: {details}")
                return
            else:
                if not quiet:
                    caller.msg("ORM deletion reported no records removed, trying raw SQL...")
                
                # If ORM delete fails, try raw SQL
                with connection.cursor() as cursor:
                    # Delete related attributes first
                    cursor.execute("DELETE FROM objects_objectdb_attributes WHERE objectdb_id = %s", [obj_id])
                    attr_count = cursor.rowcount
                    
                    # Delete tags
                    cursor.execute("DELETE FROM objects_objectdb_tags WHERE objectdb_id = %s", [obj_id])
                    tag_count = cursor.rowcount
                    
                    # Delete the object itself
                    cursor.execute("DELETE FROM objects_objectdb WHERE id = %s", [obj_id])
                    obj_count = cursor.rowcount
                    
                    if obj_count > 0:
                        caller.msg(f"Successfully deleted {obj_name} ({obj_dbref}) via raw SQL.")
                        caller.msg(f"Removed {attr_count} attributes, {tag_count} tags, and {obj_count} object records.")
                        return
                    else:
                        caller.msg(f"Failed to delete {obj_name} ({obj_dbref}) - no database records found.")
        except Exception as e:
            caller.msg(f"Database-level deletion failed: {e}")
            if not quiet:
                import traceback
                caller.msg(traceback.format_exc())
                
        caller.msg(f"All deletion methods failed for {target.name}. This object may require database maintenance.")