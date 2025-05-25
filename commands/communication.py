from evennia.commands.default.muxcommand import MuxCommand
from evennia import search_object
from evennia.utils.utils import inherits_from
from typeclasses.characters import Character

class AdminCommand(MuxCommand):
    """
    Base class for admin commands.
    Update with any additional definitions that may be useful to admin, then call the class by using 'CmdName(AdminCommand)', which
    will apply the following functions.
    """

    #search for a character by name match or dbref.
    def search_for_character(self, search_string):
        # First, try to find by exact name match
        results = search_object(search_string, typeclass="typeclasses.characters.Character")
        if results:
            return results[0]
        
        # If not found, try to find by dbref
        if search_string.startswith("#") and search_string[1:].isdigit():
            results = search_object(search_string, typeclass="typeclasses.characters.Character")
            if results:
                return results[0]
        
        # If still not found, return None
        return None

class CmdOOC(MuxCommand):
    """
    Speak or pose out-of-character in your current location.

    Usage:
      ooc <message>
      ooc :<pose>

    Examples:
      ooc Hello everyone!
      ooc :waves to the group.
    """
    key = "ooc"
    locks = "cmd:all()"
    help_category = "Comms"

    def func(self):
        # Check if the room is a Quiet Room
        if hasattr(self.caller.location, 'db') and self.caller.location.db.roomtype == "Quiet Room":
            self.caller.msg("|rYou are in a Quiet Room and cannot use OOC communication.|n")
            return
            
        if not self.args:
            self.caller.msg("Say or pose what?")
            return

        location = self.caller.location
        if not location:
            self.caller.msg("You are not in any location.")
            return

        # Strip leading and trailing whitespace from the message
        ooc_message = self.args.strip()

        # Check if it's a pose (starts with ':')
        if ooc_message.startswith(':'):
            pose = ooc_message[1:].strip()  # Remove the ':' and any following space
            message = f"|r<|n|yOOC|n|r>|n {self.caller.name} {pose}"
            self_message = f"|r<|n|yOOC|n|r>|n {self.caller.name} {pose}"
        else:
            message = f"|r<|n|yOOC|n|r>|n {self.caller.name} says, \"{ooc_message}\""
            self_message = f"|r<|n|yOOC|n|r>|n You say, \"{ooc_message}\""

        # Filter receivers based on reality layers using tags, matching other commands
        filtered_receivers = []
        for obj in location.contents:
            if not obj.has_account:
                continue
            
            # Check if they share the same reality layer
            if (self.caller.tags.get("in_umbra", category="state") and obj.tags.get("in_umbra", category="state")) or \
               (self.caller.tags.get("in_material", category="state") and obj.tags.get("in_material", category="state")) or \
               (self.caller.tags.get("in_dreaming", category="state") and obj.tags.get("in_dreaming", category="state")):
                filtered_receivers.append(obj)

        # Send the message to filtered receivers
        for receiver in filtered_receivers:
            if receiver != self.caller:
                receiver.msg(message)

        # Send the message to the caller
        self.caller.msg(self_message)

class CmdPlusIc(MuxCommand):
    """
    Return to the IC area from OOC.

    Usage:
      +ic

    This command moves you back to your previous IC location if available,
    or to the default IC starting room if not. You must be approved to use this command.
    """

    key = "+ic"
    locks = "cmd:all()"
    help_category = "Utility Commands"

    def func(self):
        caller = self.caller
        
        # Check if the room is a Quiet Room
        if hasattr(caller.location, 'db') and caller.location.db.roomtype == "Quiet Room":
            caller.msg("|rYou cannot use the +ic command from a Quiet Room.|n")
            return
            
        # Check if the room is an RP Room
        if hasattr(caller.location, 'db') and caller.location.db.roomtype and "RP Room" in caller.location.db.roomtype:
            caller.msg("|rYou cannot use the +ic command from an RP Room. Please return to the OOC nexus first.|n")
            return

        # Check if the character is approved - check both tag and attribute
        is_approved = (caller.tags.has("approved", category="approval") or 
                      caller.db.approved)
        has_unapproved = caller.tags.has("unapproved", category="approval")

        # If they have approved=True but still have the unapproved tag, fix it
        if caller.db.approved and has_unapproved:
            caller.tags.remove("unapproved", category="approval")
            caller.tags.add("approved", category="approval")
            is_approved = True
            
        # Staff bypass - check for admin, builder, or storyteller permissions
        is_staff = False
        if hasattr(caller, 'check_permstring'):
            for perm in ["Admin", "Builder", "Staff", "Storyteller"]:
                if caller.check_permstring(perm):
                    is_staff = True
                    break

        # Only enforce approval for non-staff
        if not is_staff and (not is_approved or has_unapproved):
            caller.msg("You must be approved to enter IC areas.")
            return

        # Get the stored pre_ooc_location, or use the default room #52
        target_location = caller.db.pre_ooc_location or search_object("#52")[0]

        if not target_location:
            caller.msg("Error: Unable to find a valid IC location.")
            return

        # Message the old location before leaving
        old_location = caller.location
        old_location.msg_contents(f"{caller.name} returns to IC areas.", exclude=caller)

        # Notify the player they're moving
        caller.msg(f"Returning to IC ({target_location.name})...")
        
        # Ensure all sessions know we're moving to prevent ghosts
        for session in caller.sessions.all():
            if session:
                session.msg(text=f"Moving to {target_location.name}...")
            
        # Move the character to the new location
        caller.move_to(target_location, quiet=True)
        
        # Make sure location is fully updated for all sessions
        caller.location = target_location

        # Force locations in ndb for all sessions to update
        for session in caller.sessions.all():
            if session and hasattr(session, 'puppet') and session.puppet == caller:
                session.ndb._prod_location = target_location
        
        # Announce arrival at new location
        caller.msg(f"You return to the IC area ({target_location.name}).")
        target_location.msg_contents(f"{caller.name} has returned to the IC area.", exclude=caller)

        # Clear the pre_ooc_location attribute
        caller.attributes.remove("pre_ooc_location")

class CmdPlusOoc(MuxCommand):
    """
    Move to the OOC area (Limbo).

    Usage:
      +ooc

    This command moves you to the OOC area (Limbo) and stores your
    previous location so you can return later.
    """

    key = "+ooc"
    locks = "cmd:all()"
    help_category = "Utility Commands"

    def func(self):
        caller = self.caller
        
        # Check if the room is a Quiet Room
        if hasattr(caller.location, 'db') and caller.location.db.roomtype == "Quiet Room":
            caller.msg("|rYou cannot use the +ooc command from a Quiet Room.|n")
            return
            
        # Check if the room is an RP Room
        if hasattr(caller.location, 'db') and caller.location.db.roomtype and "RP Room" in caller.location.db.roomtype:
            caller.msg("|rYou cannot use the +ooc command from an RP Room. Please return to the grid first.|n")
            return
            
        current_location = caller.location

        # Store the current location as an attribute
        caller.db.pre_ooc_location = current_location

        # Find Limbo (object #1729)
        ooc_nexus = search_object("#1729")[0]

        if not ooc_nexus:
            caller.msg("Error: ooc_nexus not found.")
            return
            
        # Set roomtype to OOC Area to enable checks in other commands
        ooc_nexus.db.roomtype = "OOC Area"
            
        # Message the current location before leaving
        current_location.msg_contents(f"{caller.name} heads to OOC areas.", exclude=caller)
        
        # Notify the player they're moving
        caller.msg("Moving to OOC area...")
        
        # Ensure all sessions know we're moving to prevent ghosts
        for session in caller.sessions.all():
            if session:
                session.msg(text=f"Moving to OOC area...")
                
        # Move the character to the new location
        caller.move_to(ooc_nexus, quiet=True)
        
        # Make sure location is fully updated
        caller.location = ooc_nexus
        
        # Force locations in ndb for all sessions to update
        for session in caller.sessions.all():
            if session and hasattr(session, 'puppet') and session.puppet == caller:
                session.ndb._prod_location = ooc_nexus
        
        # Announce arrival at new location
        caller.msg(f"You move to the OOC area.")
        ooc_nexus.msg_contents(f"{caller.name} has entered the OOC area.", exclude=caller)

class CmdMeet(MuxCommand):
    """
    Send a meet request to another player or respond to one.

    Usage:
      +meet <player>
      +meet/accept
      +meet/reject

    Sends a meet request to another player. If accepted, they'll be
    teleported to your location. You cannot use this command from OOC areas unless you're staff.
    """

    key = "+meet"
    locks = "cmd:all()"
    help_category = "Utility Commands"

    def search_for_character(self, search_string):
        # First, try to find by exact name match
        results = search_object(search_string, typeclass="typeclasses.characters.Character")
        if results:
            return results[0]
        
        # If not found, try to find by dbref
        if search_string.startswith("#") and search_string[1:].isdigit():
            results = search_object(search_string, typeclass="typeclasses.characters.Character")
            if results:
                return results[0]
        
        # If still not found, return None
        return None

    def func(self):
        caller = self.caller
        
        # Check if the room is a Quiet Room
        if hasattr(caller.location, 'db') and caller.location.db.roomtype == "Quiet Room":
            caller.msg("|rYou cannot use the +meet command from a Quiet Room.|n")
            return
        
        # Check if caller is staff - admin, builder, or storyteller
        is_staff = False
        if hasattr(caller, 'check_permstring'):
            for perm in ["Admin", "Builder", "Staff", "Storyteller"]:
                if caller.check_permstring(perm):
                    is_staff = True
                    break
        
        # Check if in OOC area - only restrict non-staff
        current_location = caller.location
        if not is_staff and current_location and hasattr(current_location, 'db') and current_location.db.roomtype == "OOC Area":
            caller.msg("You cannot use the +meet command from OOC areas. Use +ic first to return to IC areas.")
            return

        if not self.args and not self.switches:
            caller.msg("Usage: +meet <player> or +meet/accept or +meet/reject")
            return

        # Handle accepting meet requests
        if "accept" in self.switches:
            if not caller.ndb.meet_request:
                caller.msg("You have no pending meet requests.")
                return
            requester = caller.ndb.meet_request
            old_location = caller.location
            
            # Notify the player they're moving
            caller.msg(f"Moving to {requester.name}'s location...")
            
            # Announce departure before moving
            old_location.msg_contents(f"{caller.name} has left to meet {requester.name}.", exclude=caller)
            
            # Ensure all sessions know we're moving to prevent ghosts
            for session in caller.sessions.all():
                if session:
                    session.msg(text=f"Moving to {requester.name}'s location...")
            
            # Move the character to the new location
            caller.move_to(requester.location, quiet=True)
            
            # Make sure location is fully updated
            caller.location = requester.location
            
            # Force locations in ndb for all sessions to update
            for session in caller.sessions.all():
                if session and hasattr(session, 'puppet') and session.puppet == caller:
                    session.ndb._prod_location = requester.location
            
            # Announce arrival at new location
            caller.msg(f"You accept the meet request from {requester.name} and join them.")
            requester.msg(f"{caller.name} has accepted your meet request and joined you.")
            requester.location.msg_contents(f"{caller.name} appears, joining {requester.name}.", exclude=[caller, requester])
            
            # Clear the meet request
            caller.ndb.meet_request = None
            return

        # Handle rejecting meet requests
        if "reject" in self.switches:
            if not caller.ndb.meet_request:
                caller.msg("You have no pending meet requests.")
                return
            requester = caller.ndb.meet_request
            caller.msg(f"You reject the meet request from {requester.name}.")
            requester.msg(f"{caller.name} has rejected your meet request.")
            caller.ndb.meet_request = None
            return
        
        # For new meet requests, check location restrictions
        # Only proceed if not in OOC area or Quiet Room (or if staff)
        if not is_staff:
            if current_location and hasattr(current_location, 'db'):
                if current_location.db.roomtype == "OOC Area":
                    caller.msg("|rYou cannot send meet requests from OOC areas. Use +ic first to return to IC areas.|n")
                    return
                if current_location.db.roomtype == "Quiet Room":
                    caller.msg("|rYou cannot send meet requests from a Quiet Room.|n")
                    return

        target = self.search_for_character(self.args)
        if not target:
            caller.msg(f"Could not find character '{self.args}'.")
            return

        if target == caller:
            caller.msg("You can't send a meet request to yourself.")
            return

        if target.ndb.meet_request:
            caller.msg(f"{target.name} already has a pending meet request.")
            return

        target.ndb.meet_request = caller
        caller.msg(f"You sent a meet request to {target.name}.")
        target.msg(f"{caller.name} has sent you a meet request. Use +meet/accept to accept or +meet/reject to decline.")

class CmdSummon(AdminCommand):
    """
    Summon a player to your location.

    Usage:
      +summon <player>

    Teleports the specified player to your location and matches their
    Umbra/Material state to yours.
    """

    key = "+summon"
    locks = "cmd:perm(builders) or perm(storyteller)"
    help_category = "Admin Commands"

    def func(self):
        caller = self.caller

        if not self.args:
            caller.msg("Usage: +summon <player>")
            return

        # First try direct name match
        target = None
        chars = caller.search(self.args, global_search=True, typeclass='typeclasses.characters.Character', quiet=True)
        if chars:
            target = chars[0] if isinstance(chars, list) else chars
            
        # If no direct match, try alias
        if not target:
            target = Character.get_by_alias(self.args.lower())

        if not target:
            caller.msg(f"Could not find character '{self.args}'.")
            return

        if not inherits_from(target, "typeclasses.characters.Character"):
            caller.msg("You can only summon characters.")
            return

        # Check if target is connected
        if not target.has_account or not target.sessions.count():
            caller.msg(f"{target.name} is not currently online.")
            return

        old_location = target.location
        if not old_location:
            caller.msg(f"{target.name} doesn't have a valid location.")
            return

        # Handle Umbra/Material state
        caller_in_umbra = caller.tags.has("in_umbra", category="state")
        target_in_umbra = target.tags.has("in_umbra", category="state")
        
        if caller_in_umbra != target_in_umbra:
            # Remove current state
            if target_in_umbra:
                target.tags.remove("in_umbra", category="state")
            else:
                target.tags.remove("in_material", category="state")
            
            # Add new state to match caller
            if caller_in_umbra:
                target.tags.add("in_umbra", category="state")
                target.msg("You shift into the Umbra.")
            else:
                target.tags.add("in_material", category="state")
                target.msg("You shift into the Material realm.")

        # Store location for +return command
        target.db.pre_summon_location = old_location
        
        # First, let the target know they're being summoned
        target.msg(f"You are being summoned by {caller.name}...")
        
        # Ensure all sessions know we're moving to prevent ghosts
        for session in target.sessions.all():
            if session:
                session.msg(text=f"Being summoned by {caller.name}...")
        
        # Announce departure at the old location before moving
        old_location.msg_contents(f"{target.name} has been summoned by {caller.name}.", exclude=target)
                
        # Move the character to the new location
        target.move_to(caller.location, quiet=True)
        
        # Make sure location is fully updated
        target.location = caller.location
        
        # Force locations in ndb for all sessions to update
        for session in target.sessions.all():
            if session and hasattr(session, 'puppet') and session.puppet == target:
                session.ndb._prod_location = caller.location
        
        # Announce arrival at the new location
        caller.msg(f"You have summoned {target.name} to your location.")
        target.msg(f"{caller.name} has summoned you.")
        caller.location.msg_contents(f"{target.name} appears, summoned by {caller.name}.", exclude=[caller, target])

class CmdJoin(AdminCommand):
    """
    Join a player at their location.

    Usage:
      +join <player>

    Teleports you to the specified player's location and matches your
    Umbra/Material state to theirs. Staff can use this command from anywhere.
    """

    key = "+join"
    locks = "cmd:perm(builders) or perm(storyteller) or perm(admin) or perm(staff)"
    help_category = "Admin Commands"

    def func(self):
        caller = self.caller

        # Check if in OOC area - but allow for staff
        current_location = caller.location
        if current_location and hasattr(current_location, 'db') and current_location.db.roomtype == "OOC Area":
            # Allow it but warn them
            caller.msg("Note: You're using +join from an OOC area as staff. This is allowed but may have unexpected effects.")

        if not self.args:
            caller.msg("Usage: +join <player>")
            return

        # First try direct name match
        target = None
        chars = caller.search(self.args, global_search=True, typeclass='typeclasses.characters.Character', quiet=True)
        if chars:
            target = chars[0] if isinstance(chars, list) else chars
            
        # If no direct match, try alias
        if not target:
            target = Character.get_by_alias(self.args.lower())

        if not target:
            caller.msg(f"Could not find character '{self.args}'.")
            return

        if not inherits_from(target, "typeclasses.characters.Character"):
            caller.msg("You can only join characters.")
            return

        # Check if target is connected and has a location
        if not target.has_account or not target.sessions.count():
            caller.msg(f"{target.name} is not currently online.")
            return

        if not target.location:
            caller.msg(f"{target.name} doesn't have a valid location to join.")
            return

        # Store old location for potential return
        old_location = caller.location
        caller.db.pre_join_location = old_location

        # Handle Umbra/Material state
        caller_in_umbra = caller.tags.has("in_umbra", category="state")
        target_in_umbra = target.tags.has("in_umbra", category="state")
        
        if caller_in_umbra != target_in_umbra:
            # Remove current state
            if caller_in_umbra:
                caller.tags.remove("in_umbra", category="state")
            else:
                caller.tags.remove("in_material", category="state")
            
            # Add new state to match target
            if target_in_umbra:
                caller.tags.add("in_umbra", category="state")
                caller.msg("You shift into the Umbra.")
            else:
                caller.tags.add("in_material", category="state")
                caller.msg("You shift into the Material realm.")

        # Notify caller they are joining the target
        caller.msg(f"Joining {target.name}...")
        
        # Ensure all sessions know we're moving to prevent ghosts
        for session in caller.sessions.all():
            if session:
                session.msg(text=f"Joining {target.name}...")
        
        # Announce departure at the old location before moving
        old_location.msg_contents(f"{caller.name} has left to join {target.name}.", exclude=caller)

        # Move the character to the new location
        caller.move_to(target.location, quiet=True)
        
        # Make sure location is fully updated
        caller.location = target.location
        
        # Force locations in ndb for all sessions to update
        for session in caller.sessions.all():
            if session and hasattr(session, 'puppet') and session.puppet == caller:
                session.ndb._prod_location = target.location
        
        # Announce arrival at the new location
        caller.msg(f"You have joined {target.name} at their location.")
        target.location.msg_contents(f"{caller.name} appears in the room.", exclude=caller)

class CmdCheckComm(AdminCommand):
    """
    Check communication status between characters.

    Usage:
      +checkcomm <character>
      
    Checks if the specified character can communicate with you by analyzing:
    - Reality layers (Umbra/Material/Dreaming)
    - Room type restrictions
    - Any other potential communication barriers
    
    This is a staff-only command for troubleshooting communication issues.
    """

    key = "+checkcomm"
    locks = "cmd:perm(builders) or perm(storyteller) or perm(admin) or perm(staff)"
    help_category = "Admin Commands"

    def func(self):
        caller = self.caller
        
        if not self.args:
            caller.msg("Usage: +checkcomm <character>")
            return
            
        target = self.search_for_character(self.args)
        if not target:
            caller.msg(f"Could not find character '{self.args}'.")
            return
            
        # Begin analysis
        results = []
        
        # 1. Check if in same location
        if caller.location != target.location:
            results.append("|rFAIL|n: Characters are not in the same room.")
            caller.msg("\n".join(results))
            return
        
        # 2. Check reality layers via tags
        caller_umbra = caller.tags.get("in_umbra", category="state")
        caller_material = caller.tags.get("in_material", category="state")
        caller_dreaming = caller.tags.get("in_dreaming", category="state")
        
        target_umbra = target.tags.get("in_umbra", category="state")
        target_material = target.tags.get("in_material", category="state")
        target_dreaming = target.tags.get("in_dreaming", category="state")
        
        # Reality layer check
        if caller_umbra and target_umbra:
            results.append("|gPASS|n: Both characters are in the Umbra.")
        elif caller_material and target_material:
            results.append("|gPASS|n: Both characters are in the Material realm.")
        elif caller_dreaming and target_dreaming:
            results.append("|gPASS|n: Both characters are in the Dreaming realm.")
        else:
            results.append("|rFAIL|n: Characters are in different reality layers:")
            results.append(f"  - {caller.name}: {'Umbra' if caller_umbra else 'Material' if caller_material else 'Dreaming' if caller_dreaming else 'Unknown'}")
            results.append(f"  - {target.name}: {'Umbra' if target_umbra else 'Material' if target_material else 'Dreaming' if target_dreaming else 'Unknown'}")
        
        # 3. Check reality layers via DB attributes (old method)
        caller_db_umbra = hasattr(caller.db, 'in_umbra') and caller.db.in_umbra
        target_db_umbra = hasattr(target.db, 'in_umbra') and target.db.in_umbra
        
        if caller_db_umbra != caller_umbra or target_db_umbra != target_umbra:
            results.append("|yWARNING|n: DB attributes for reality don't match tags:")
            results.append(f"  - {caller.name}: tag={caller_umbra}, db={caller_db_umbra}")
            results.append(f"  - {target.name}: tag={target_umbra}, db={target_db_umbra}")
        
        # 4. Check room type restrictions
        room = caller.location
        room_type = getattr(room.db, 'roomtype', 'Unknown')
        
        results.append(f"Room type: {room_type}")
        
        if room_type == "Quiet Room":
            results.append("|rFAIL|n: Room is a Quiet Room where communication is disabled.")
        elif room_type == "freezer":
            results.append("|rFAIL|n: Room is a freezer where communication is disabled.")
        
        # 5. Check if umbra_only or fae_only room with wrong character type
        if getattr(room.db, 'umbra_only', False) and not caller_umbra:
            results.append("|rFAIL|n: Room is Umbra-only but caller is not in Umbra.")
        if getattr(room.db, 'umbra_only', False) and not target_umbra:
            results.append("|rFAIL|n: Room is Umbra-only but target is not in Umbra.")
            
        if getattr(room.db, 'fae_only', False) and not caller_dreaming:
            results.append("|rFAIL|n: Room is Fae-only but caller is not in Dreaming.")
        if getattr(room.db, 'fae_only', False) and not target_dreaming:
            results.append("|rFAIL|n: Room is Fae-only but target is not in Dreaming.")
        
        # Report findings
        caller.msg("\n".join(results))
