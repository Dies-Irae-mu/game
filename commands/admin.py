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


class CmdApprove(AdminCommand):
    """
    Approve a player's character.

    Usage:
      approve <character_name>

    This command approves a player's character, removing the 'unapproved' tag
    and adding the 'approved' tag. This allows the player to start playing.
    """
    key = "approve"
    aliases = ["+approve"]
    locks = "cmd:perm(Admin)"
    help_category = "Staff"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: +approve <character>")
            return
            
        # First try direct name match
        target = None
        chars = self.caller.search(self.args, global_search=True, typeclass='typeclasses.characters.Character', quiet=True)
        if chars:
            target = chars[0] if isinstance(chars, list) else chars
            
        # If no direct match, try alias
        if not target:
            target = Character.get_by_alias(self.args.lower())

        if not target:
            self.caller.msg(f"Could not find character '{self.args}'.")
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
    chargen commands again.
    """
    key = "unapprove"
    aliases = ["+unapprove"]
    locks = "cmd:perm(Admin)"
    help_category = "Staff"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: unapprove <character_name>")
            return

        # Use global search for admin commands
        target = self.caller.search(self.args, global_search=True)
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
        
        logger.log_info(f"{target.name} has been unapproved by {self.caller.name}")

        self.caller.msg(f"You have unapproved {target.name}.")
        target.msg("Your character has been unapproved. You may now use chargen commands again.")

class CmdMassUnapprove(AdminCommand):
    """
    Set all connected characters to unapproved status.

    Usage:
      +massunapprove
      +massunapprove/confirm

    This command will list all characters that will be affected when run
    without the /confirm switch. Use /confirm to actually make the changes.
    """

    key = "+massunapprove"
    locks = "cmd:perm(Admin)"
    help_category = "Admin"

    def func(self):
        """Execute command."""
        caller = self.caller
        confirm = "confirm" in self.switches

        # Get all connected characters
        from evennia.server.sessionhandler import SESSIONS
        connected_chars = [session.get_puppet() for session in SESSIONS.get_sessions() 
                         if session.get_puppet()]
        
        if not connected_chars:
            caller.msg("No connected characters found.")
            return

        if not confirm:
            # Just show what would be affected
            msg = "The following characters would be set to unapproved:\n"
            for char in connected_chars:
                msg += f"- {char.name} (currently {'approved' if char.db.approved else 'unapproved'})\n"
            msg += "\nUse +massunapprove/confirm to execute the changes."
            caller.msg(msg)
            return

        # Actually make the changes
        count = 0
        for char in connected_chars:
            if char.db.approved:
                char.db.approved = False
                char.tags.add("unapproved", category="approval")
                if char.tags.has("approved", category="approval"):
                    char.tags.remove("approved", category="approval")
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
    help_category = "Staff"

    def func(self):
        """Handle the looking."""
        caller = self.caller
        args = self.args.strip()
        
        # Handle global search for admin using *character format
        if args.startswith('*') and caller.check_permstring("Admin"):
            # Remove the * and any leading/trailing spaces
            target_name = args[1:].strip()
            # Perform global search
            target = caller.search(target_name, global_search=True)
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
        @testlock Nicole = has_mage_faction(Traditions)
    """
    
    key = "@testlock"
    locks = "cmd:perm(Admin)"
    help_category = "Staff"
    
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
            
        # Search for character
        chars = search_object(self.lhs)
        if not chars:
            self.caller.msg(f"Could not find '{self.lhs}'.")
            return
        
        char = chars[0]  # Take the first match
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
    help_category = "Staff"
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
        
        # Move to freeze room
        freeze_room = self.caller.search("#1935")
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
            prev_location = char.home or self.caller.search("#2")  # Fallback to limbo
            
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
            char = self.caller.search(self.args.strip())
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
            
            char = self.caller.search(name)
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
    help_category = "Storyteller"
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
    help_category = "Storyteller"

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
            # Search for object
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
    help_category = "Storyteller"
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
