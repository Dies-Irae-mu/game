from evennia import default_cmds
from evennia.utils.search import search_object
from evennia.utils.utils import inherits_from
from evennia.utils import logger
from evennia.objects.models import ObjectDB
from evennia.accounts.models import AccountDB

class CmdAlts(default_cmds.MuxCommand):
    """
    Manage character alts.
    
    Usage:
      +alts                     - Show your list of alts
      +alts <name>              - Show the public alts of a character
      +alts/add <name>          - Request to add a character as your alt
      +alts/del <name>          - Remove a character from your list of alts
      +alts/block <name>        - Block someone from sending you alt requests
      +alts/unblock <name>      - Unblock someone from sending alt requests
      +alts/confirm <code>      - Confirm an alt request using the code
      +alts/reject <name>       - Reject an alt request from a character
      +alts/pending             - List all your pending alt requests
      +alts/staff <name>        - [Staff only] Show IP-based alts and public alts
      +alts/forcerem <c1>=<c2>  - [Staff only] Forcibly remove alt relationship
    
    The +alts command allows you to manage which characters are publicly 
    linked to your character. This is useful for letting others know 
    which characters you play.
    
    When you request to add someone as an alt, they will receive a mail with
    a confirmation code. They must use +alts/confirm <code> to approve the
    relationship. This ensures both parties agree to be linked as alts.
    
    Staff characters cannot be added as alts by non-staff players.
    Staff can use /forcerem to remove any unwanted alt relationships.
    """
    
    key = "+alts"
    aliases = ["alts"]
    locks = "cmd:all()"
    help_category = "Character"
    
    def func(self):
        """Implement the command functionality."""
        caller = self.caller
        
        # No arguments, show the caller's alts
        if not self.args and not self.switches:
            self.list_own_alts()
            return
            
        # Check for /staff switch (staff only)
        if "staff" in self.switches:
            if not caller.check_permstring("Builder") and not caller.check_permstring("Admin"):
                caller.msg("You don't have permission to use this command.")
                return
            self.show_staff_alts()
            return
            
        # Check for /forcerem switch (staff only)
        if "forcerem" in self.switches:
            if not caller.check_permstring("Builder") and not caller.check_permstring("Admin"):
                caller.msg("You don't have permission to use this command.")
                return
                
            # Format should be character1=character2
            if not self.args or "=" not in self.args:
                caller.msg("Usage: +alts/forcerem <character1>=<character2>")
                return
                
            char1, char2 = self.args.split("=", 1)
            result = self.staff_remove_alt(char1.strip(), char2.strip())
            caller.msg(result)
            return
            
        # Check for /add switch
        if "add" in self.switches:
            self.add_alt()
            return
            
        # Check for /del switch - removes from alt list
        if "del" in self.switches:
            self.remove_alt()
            return
            
        # Check for /block switch - prevents alt requests
        if "block" in self.switches:
            self.block_alt()
            return
            
        # Check for /unblock switch
        if "unblock" in self.switches:
            self.unblock_alt()
            return
            
        # Check for /confirm switch
        if "confirm" in self.switches:
            self.confirm_alt()
            return
            
        # Check for /reject switch
        if "reject" in self.switches:
            self.reject_alt()
            return
            
        # Check for /pending switch
        if "pending" in self.switches:
            self.list_pending_requests()
            return
            
        # If we have args but no switches, show the public alts of the target
        if self.args and not self.switches:
            self.list_public_alts()
            return
    
    def list_own_alts(self):
        """List the caller's own alts."""
        from evennia.utils import logger
        caller = self.caller
        
        # Force refresh from database to ensure we have the most current data
        caller.flush_from_cache(force=True)
        
        # Get the list of alts from the caller's attributes
        alts = caller.attributes.get('public_alts', [])
        logger.log_info(f"{caller.name}'s public_alts attribute before check: {alts}")
        
        # Check if alts need to be converted to a list (don't reset if it's already list-like)
        try:
            # Try to iterate and access elements like a list
            list_like = hasattr(alts, '__iter__') and hasattr(alts, '__getitem__')
            if not list_like or not alts:
                # Only reset if not list-like at all
                alts = []
                logger.log_info(f"Initializing {caller.name}'s public_alts as empty list")
                caller.attributes.add('public_alts', alts)
                caller.save()
        except Exception as e:
            logger.log_err(f"Error checking alts list type: {e}")
            alts = []
            caller.attributes.add('public_alts', alts)
            caller.save()
            
        # Log what we found for debugging
        logger.log_info(f"{caller.name}'s public_alts attribute after check: {alts}")
        
        # Get blocked list
        blocks = caller.attributes.get('alt_blocks', [])
        
        # Build the display
        total_width = 78
        
        # Header
        title = f" {caller.name}'s Alts "
        title_len = len(title)
        dash_count = (total_width - title_len) // 2
        msg = f"{'|b-|n' * dash_count}{title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
        
        if not alts:
            msg += "You have not declared any alt characters.\n"
        else:
            # List the alts
            for alt_name in alts:
                msg += f"• {alt_name}\n"
        
        # If there are blocks, list them
        if blocks:
            blocks_title = " Blocked Characters "
            title_len = len(blocks_title)
            dash_count = (total_width - title_len) // 2
            msg += f"\n{'|b-|n' * dash_count}{blocks_title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
            for block in blocks:
                msg += f"• {block}\n"
        
        # Check for pending requests
        has_pending = False
        
        # Check incoming requests
        pending_requests = caller.attributes.get('pending_alt_requests', {})
        if isinstance(pending_requests, dict) and pending_requests:
            has_pending = True
            
        # Check outgoing requests
        outgoing_requests = caller.attributes.get('outgoing_alt_requests', {})
        if isinstance(outgoing_requests, dict) and outgoing_requests:
            has_pending = True
            
        # If there are pending requests, add a note
        if has_pending:
            pending_title = " Pending Alt Requests "
            title_len = len(pending_title)
            dash_count = (total_width - title_len) // 2
            msg += f"\n{'|b-|n' * dash_count}{pending_title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
            msg += "You have pending alt requests. Use |w+alts/pending|n to view them.\n"
        
        msg += f"\nUse |w+alts/add <character name>|n to request to add an alt."
        caller.msg(msg)
    
    def list_public_alts(self):
        """List another character's public alts."""
        from evennia.utils import logger
        caller = self.caller
        args = self.args.strip()
        
        # Find the target character
        target = search_object(args, typeclass="typeclasses.characters.Character")
        if not target:
            caller.msg(f"Could not find character '{args}'.")
            return
        if len(target) > 1:
            caller.msg(f"Multiple matches found for '{args}'. Please be more specific.")
            return
            
        target = target[0]  # Get the first (and only) match
        
        # Force refresh from database to ensure we have the most current data
        target.flush_from_cache(force=True)
        
        # Get the list of alts from the target's attributes
        alts = target.attributes.get('public_alts', [])
        logger.log_info(f"{target.name}'s public_alts attribute before check: {alts}")
        
        # Check if alts need to be converted to a list (don't reset if it's already list-like)
        try:
            # Try to iterate and access elements like a list
            list_like = hasattr(alts, '__iter__') and hasattr(alts, '__getitem__')
            if not list_like or not alts:
                # Only reset if not list-like at all
                alts = []
                logger.log_info(f"Initializing {target.name}'s public_alts as empty list")
                target.attributes.add('public_alts', alts)
                target.save()
        except Exception as e:
            logger.log_err(f"Error checking alts list type: {e}")
            alts = []
            target.attributes.add('public_alts', alts)
            target.save()
            
        # Log what we found for debugging
        logger.log_info(f"{target.name}'s public_alts attribute after check: {alts}")
        
        # Build the display
        total_width = 78
        
        # Header
        title = f" {target.name}'s Public Alts "
        title_len = len(title)
        dash_count = (total_width - title_len) // 2
        msg = f"{'|b-|n' * dash_count}{title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
        
        if not alts:
            msg += f"{target.name} has not declared any alt characters."
        else:
            # List the alts
            for alt_name in alts:
                msg += f"• {alt_name}\n"
        
        caller.msg(msg)
    
    def add_alt(self):
        """Request to add a character as an alt."""
        import uuid
        from time import time
        from evennia.utils import logger
        from evennia.utils.search import search_account, search_object
        
        caller = self.caller
        args = self.args.strip()
        
        if not args:
            caller.msg("Usage: +alts/add <character name>")
            return
        
        # Find the target character
        target = search_object(args, typeclass="typeclasses.characters.Character")
        if not target:
            caller.msg(f"Could not find character '{args}'.")
            return
        if len(target) > 1:
            caller.msg(f"Multiple matches found for '{args}'. Please be more specific.")
            return
            
        target = target[0]  # Get the first (and only) match
        
        # Don't add yourself as an alt
        if target == caller:
            caller.msg("You can't add yourself as an alt.")
            return
            
        # Check if the character is an NPC or special character
        if target.tags.get("npc") or target.tags.get("special") or target.tags.get("bot"):
            logger.log_info(f"{caller.name} tried to add NPC/special character {target.name} as an alt")
            caller.msg(f"You cannot add {target.name} as an alt because they are an NPC or special character.")
            return
            
        # Use creator_id to find the owning player account
        creator_id = target.db.creator_id
        
        # Find the account directly using search_account
        # This is the key difference - we query for accounts directly instead of going through character
        if creator_id:
            # Try to find by ID first
            from evennia.accounts.models import AccountDB
            try:
                target_account = AccountDB.objects.get(id=creator_id)
                logger.log_info(f"Found account for {target.name} using creator_id: {creator_id}")
            except AccountDB.DoesNotExist:
                target_account = None
                logger.log_err(f"No account found with ID {creator_id} for {target.name}")
        else:
            # Try to find by name matching
            target_account = None
            # First check if character name matches an account name
            accounts = search_account(target.name)
            if accounts and len(accounts) == 1:
                target_account = accounts[0]
                logger.log_info(f"Found account for {target.name} by name matching")
        
        # If we still can't find an account, character can't be an alt
        if not target_account:
            logger.log_info(f"{caller.name} tried to add {target.name} as an alt, but could not find an associated account.")
            caller.msg(f"You cannot add {target.name} as your alt because they don't have a player account. Only player-controlled characters can be added as alts.")
            return
            
        # Debug log the successful account lookup
        logger.log_info(f"Found account {target_account.username} (#{target_account.id}) for character {target.name}")
            
        # Check if the target is connected to the same account as the caller
        if caller.account and caller.account.id == target_account.id:
            logger.log_info(f"{caller.name} tried to add {target.name} as an alt, both already belong to account {caller.account.name}")
            caller.msg(f"{target.name} is already controlled by your account. No need to add them as an alt.")
            return
        
        # Check if the target has blocked alt requests from the caller
        target_blocks = target.attributes.get('alt_blocks', [])
        if caller.name in target_blocks:
            caller.msg(f"{target.name} has blocked alt requests from you.")
            return
            
        # Check if the target is a staff character
        is_staff = False
        if target_account:
            # Check permissions in order of hierarchy
            if target_account.is_superuser:
                is_staff = True
            elif target_account.check_permstring("admin"):
                is_staff = True
            elif target_account.check_permstring("builder"):
                is_staff = True
            # Check for staff tag
            elif target.tags.get("staff", category="role"):
                is_staff = True

        # Check if caller is also staff
        caller_is_staff = False
        if caller.account:
            if caller.account.is_superuser:
                caller_is_staff = True
            elif caller.account.check_permstring("admin"):
                caller_is_staff = True
            elif caller.account.check_permstring("builder"):
                caller_is_staff = True
                
        # Only staff can add staff as alts
        if is_staff and not caller_is_staff:
            caller.msg("You cannot add a staff character as your alt.")
            return
        
        # Get current alt lists and ensure they're properly initialized
        caller.flush_from_cache(force=True)
        target.flush_from_cache(force=True)
        
        caller_alts = caller.attributes.get('public_alts', [])
        if not isinstance(caller_alts, list):
            caller_alts = []
            
        target_alts = target.attributes.get('public_alts', [])
        if not isinstance(target_alts, list):
            target_alts = []
        
        # Check if the character is already in the list
        if target.name in caller_alts:
            caller.msg(f"{target.name} is already listed as your alt.")
            return
              
        # Generate a confirmation code
        confirmation_code = str(uuid.uuid4())[:8].upper()  # First 8 chars of UUID, uppercase
        
        # Log the confirmation code for debugging
        logger.log_info(f"Alt request from {caller.name} to {target.name} with code {confirmation_code}")
        
        # Create a pending request
        pending_request = {
            'requester': caller.name,
            'target': target.name,
            'code': confirmation_code,
            'timestamp': time()
        }
        
        # Store the pending request in both characters using attributes.add for reliable persistence
        # First for the outgoing request
        outgoing_requests = caller.attributes.get('outgoing_alt_requests', {})
        if not isinstance(outgoing_requests, dict):
            outgoing_requests = {}
        
        outgoing_requests[target.name] = pending_request
        # Use attributes.add for reliable database persistence
        caller.attributes.add('outgoing_alt_requests', outgoing_requests)
        logger.log_info(f"Saved outgoing request for {caller.name}: {outgoing_requests}")
        
        # Then for the pending request on the target
        pending_requests = target.attributes.get('pending_alt_requests', {})
        if not isinstance(pending_requests, dict):
            pending_requests = {}
        
        pending_requests[caller.name] = pending_request
        # Use attributes.add for reliable database persistence
        target.attributes.add('pending_alt_requests', pending_requests)
        
        # Log the storage operation
        logger.log_info(f"Saved pending request for {target.name}: {pending_requests}")
        logger.log_info(f"Verifying target's pending requests: {target.attributes.get('pending_alt_requests')}")
        
        # Force immediate saves to ensure persistence
        caller.save()
        target.save()
        
        # Send mail to the target using @mail command (like jobs system)
        try:
            # Prepare the mail message
            subject = f"Alt Confirmation Request from {caller.name}"
            message = f"""
{caller.name} has requested to add you as their alt character.

If you approve this request, please use the following command:
+alts/confirm {confirmation_code}

If you do not wish to be listed as {caller.name}'s alt, you can ignore this message
or use +alts/reject {caller.name} to explicitly reject the request.

This request will expire in 7 days.
"""
            # Use execute_cmd to send the mail (this is how the jobs system does it)
            mail_cmd = f"@mail {target_account.username}={subject}/{message}"
            caller.execute_cmd(mail_cmd)
            
            logger.log_info(f"Mail sent from {caller.name} to {target.name} with confirmation code {confirmation_code}")
            caller.msg(f"Alt request sent to {target.name}. They need to confirm by using +alts/confirm {confirmation_code}")
            
            # Debug message for the recipient if they're online
            if target.sessions.count() > 0:
                target.msg(f"|wYou have received an alt request from {caller.name}. Check your mail and use +alts/confirm {confirmation_code} to accept.|n")
            
            # Force an immediate save of both characters to ensure data is persisted
            caller.save()
            target.save()
            
            # Verify again after save
            logger.log_info(f"After save, verifying target's pending requests: {target.attributes.get('pending_alt_requests')}")
                
        except Exception as e:
            logger.log_err(f"Error sending alt confirmation mail: {e}")
            caller.msg(f"Error sending confirmation request: {e}")
            
    def confirm_alt(self):
        """
        Confirms a pending alt relationship with another character who sent you 
        an alt request. This will establish a mutual alt relationship between 
        your current character and the requester.
        
        Usage: 
            +alts/confirm <code>
        """
        from evennia.utils import logger
        
        caller = self.caller
        args = self.args.strip()
        
        if not args:
            caller.msg("Usage: +alts/confirm <code>")
            return
        
        # Force refresh from database to ensure we have the most current data
        caller.flush_from_cache(force=True)
            
        # Retrieve pending alt requests using both method - attribute API and direct DB query
        pending_requests = caller.attributes.get("pending_alt_requests", {})
        
        # Debug dump of the exact pending_requests value
        logger.log_info(f"PENDING REQUESTS DUMP: type={type(pending_requests)}, value={pending_requests!r}")
        
        # Try using direct DB query as a backup
        try:
            from evennia.utils.dbserialize import deserialize
            from evennia.typeclasses.attributes import Attribute
            
            db_attr = Attribute.objects.filter(
                db_key='pending_alt_requests',
                objectdb=caller.id
            ).first()
            
            if db_attr:
                try:
                    db_value = deserialize(db_attr.db_value)
                    logger.log_info(f"DB direct query for pending_alt_requests: {db_value}")
                    logger.log_info(f"DB value type: {type(db_value)}")
                    
                    # If the attribute API didn't return a proper dict but DB has data, use the DB data
                    if not isinstance(pending_requests, dict) or not pending_requests:
                        if isinstance(db_value, dict) and db_value:
                            logger.log_info(f"Using DB value instead of attribute API value")
                            pending_requests = db_value
                except Exception as e:
                    logger.log_err(f"Error deserializing pending_alt_requests: {e}")
        except Exception as e:
            logger.log_err(f"Error querying database: {e}")
        
        # Check if we have any pending requests
        have_requests = False
        if isinstance(pending_requests, dict) and pending_requests:
            have_requests = True
            logger.log_info(f"{caller.name} has {len(pending_requests)} pending alt requests")
        else:
            logger.log_info(f"{caller.name} does not have any valid pending alt requests. Got: {type(pending_requests)} - {pending_requests}")
        
        if not have_requests:
            caller.msg("You have no pending alt requests to confirm.")
            return
            
        # Log the full pending requests for debugging
        logger.log_info(f"Pending alt requests for {caller.name}: {pending_requests}")
        
        # Find the requester who sent this confirmation code
        confirmation_code = args.strip().upper()  # Normalize the code
        requester_name = None
        request_data = None
        
        # Detailed logging of each pending request for debugging
        for name, req in pending_requests.items():
            logger.log_info(f"Checking request from {name}: {req}")
            
            # Safety check - ensure req is a dict
            if not isinstance(req, dict):
                logger.log_err(f"Invalid request format from {name}: {req}")
                continue
                
            stored_code = req.get("code", "").strip().upper()  # Normalize for comparison
            logger.log_info(f"Stored code: {stored_code}, User entered: {confirmation_code}")
            
            if stored_code == confirmation_code:
                requester_name = name
                request_data = req
                logger.log_info(f"Found matching code from {requester_name}")
                break
                
        if not requester_name or not request_data:
            caller.msg(f"Invalid confirmation code: {confirmation_code}. Please check the code and try again.")
            logger.log_info(f"{caller.name} attempted to confirm with invalid code: {confirmation_code}")
            
            # List available codes to help debugging
            available_codes = [req.get("code", "NO_CODE") for req in pending_requests.values() if isinstance(req, dict)]
            logger.log_info(f"Available codes: {available_codes}")
            return
            
        # Find the requester character
        from typeclasses.characters import Character
        requester = Character.objects.filter(db_key__iexact=requester_name).first()
        
        if not requester:
            caller.msg(f"Error: Could not find character '{requester_name}'. The alt confirmation failed.")
            logger.log_err(f"Cannot find requester '{requester_name}' for alt confirmation")
            return
         
        # Log what we're about to do
        logger.log_info(f"About to process confirmation: {caller.name} confirming {requester_name} as alt")

        # Process the confirmation
        try:
            success = self._process_alt_confirmation(caller, requester, request_data)
        
            if success:
                # Force-check the alts list to verify it was saved properly
                caller_alts = caller.attributes.get('public_alts', [])
                logger.log_info(f"After confirmation, {caller.name}'s alts: {caller_alts}")
                requester_alts = requester.attributes.get('public_alts', [])
                logger.log_info(f"After confirmation, {requester.name}'s alts: {requester_alts}")
                
                # Clear the pending request
                try:
                    # Clean up the pending request using direct attribute manipulation
                    pending_requests = caller.attributes.get("pending_alt_requests", {})
                    if isinstance(pending_requests, dict) and requester_name in pending_requests:
                        del pending_requests[requester_name]
                        logger.log_info(f"Successfully removed {requester_name} from pending requests")
                        caller.attributes.add("pending_alt_requests", pending_requests)
                        caller.save()
                    
                    # Clean up the outgoing request on the requester side
                    outgoing_requests = requester.attributes.get("outgoing_alt_requests", {})
                    if isinstance(outgoing_requests, dict) and caller.name in outgoing_requests:
                        del outgoing_requests[caller.name]
                        logger.log_info(f"Successfully removed {caller.name} from outgoing requests")
                        requester.attributes.add("outgoing_alt_requests", outgoing_requests)
                        requester.save()
                except Exception as e:
                    logger.log_err(f"Error cleaning up requests: {e}")
                
                caller.msg(f"You have confirmed {requester.name} as your alt. You are now linked as alts.")
                # Force save to ensure persistence
                caller.save()
                requester.save()
                logger.log_info(f"Successfully confirmed and saved alt relationship between {caller.name} and {requester.name}")
            else:
                caller.msg(f"There was a problem confirming {requester.name} as your alt. Please contact staff.")
        except Exception as e:
            caller.msg(f"Error processing alt confirmation: {e}")
            logger.log_err(f"Exception in confirming alt: {e}")
            import traceback
            logger.log_err(traceback.format_exc())
    
    def _process_alt_confirmation(self, confirmer, requester, request):
        """
        Process the confirmation of an alt relationship between two characters.
        
        Args:
            confirmer (Character): The character confirming the request
            requester (Character): The character who made the request
            request (dict): The request data containing confirmation code
            
        Returns:
            bool: True if successful, False otherwise
        """
        from evennia.utils import logger
        
        logger.log_info(f"Processing alt confirmation between {confirmer.name} and {requester.name}")
        logger.log_info(f"Request data: {request}")
        
        try:
            # Explicitly load current alt lists from the database to ensure we have the latest data
            confirmer.flush_from_cache(force=True)
            requester.flush_from_cache(force=True)
            
            # Get alt lists for both characters directly from attributes
            # First check directly from database to ensure we're getting the most current data
            from evennia.utils.dbserialize import deserialize
            from evennia.typeclasses.attributes import Attribute
            
            # Try to get the confirmer's alts directly from the database
            db_confirmer_attr = Attribute.objects.filter(
                db_key='public_alts',
                objectdb=confirmer.id
            ).first()
            
            if db_confirmer_attr:
                try:
                    db_confirmer_alts = deserialize(db_confirmer_attr.db_value)
                    logger.log_info(f"DB direct query for {confirmer.name}'s alts: {db_confirmer_alts}")
                except Exception as e:
                    logger.log_err(f"Error deserializing {confirmer.name}'s alts: {e}")
                    db_confirmer_alts = None
            else:
                logger.log_info(f"No public_alts attribute found directly in DB for {confirmer.name}")
                db_confirmer_alts = None
                
            # Try to get the requester's alts directly from the database
            db_requester_attr = Attribute.objects.filter(
                db_key='public_alts',
                objectdb=requester.id
            ).first()
            
            if db_requester_attr:
                try:
                    db_requester_alts = deserialize(db_requester_attr.db_value)
                    logger.log_info(f"DB direct query for {requester.name}'s alts: {db_requester_alts}")
                except Exception as e:
                    logger.log_err(f"Error deserializing {requester.name}'s alts: {e}")
                    db_requester_alts = None
            else:
                logger.log_info(f"No public_alts attribute found directly in DB for {requester.name}")
                db_requester_alts = None
            
            # Now get via the normal attribute API
            confirmer_alts = confirmer.attributes.get('public_alts', [])
            logger.log_info(f"Initial confirmer alts via API: {confirmer_alts}")
            
            # Check if we need to convert or initialize the confirmer's alts list
            if db_confirmer_alts and (not confirmer_alts or not isinstance(confirmer_alts, list)):
                # Use DB results if better than what we got from the API
                logger.log_info(f"Using DB-queried alts for {confirmer.name}")
                confirmer_alts = db_confirmer_alts
            elif not isinstance(confirmer_alts, list):
                # Try to convert to list if it's list-like
                try:
                    if hasattr(confirmer_alts, '__iter__') and hasattr(confirmer_alts, '__getitem__'):
                        # It's list-like, convert it to a proper list
                        confirmer_alts = list(confirmer_alts)
                    else:
                        # Not list-like, initialize as empty
                        confirmer_alts = []
                        logger.log_info(f"Initializing empty public_alts list for {confirmer.name}")
                except Exception:
                    confirmer_alts = []
                    logger.log_info(f"Initializing empty public_alts list for {confirmer.name}")
            
            # Get requester's alts
            requester_alts = requester.attributes.get('public_alts', [])
            logger.log_info(f"Initial requester alts via API: {requester_alts}")
            
            # Check if we need to convert or initialize the requester's alts list
            if db_requester_alts and (not requester_alts or not isinstance(requester_alts, list)):
                # Use DB results if better than what we got from the API
                logger.log_info(f"Using DB-queried alts for {requester.name}")
                requester_alts = db_requester_alts
            elif not isinstance(requester_alts, list):
                # Try to convert to list if it's list-like
                try:
                    if hasattr(requester_alts, '__iter__') and hasattr(requester_alts, '__getitem__'):
                        # It's list-like, convert it to a proper list
                        requester_alts = list(requester_alts)
                    else:
                        # Not list-like, initialize as empty
                        requester_alts = []
                        logger.log_info(f"Initializing empty public_alts list for {requester.name}")
                except Exception:
                    requester_alts = []
                    logger.log_info(f"Initializing empty public_alts list for {requester.name}")
                
            # Add each character to the other's alt list if not already present
            if confirmer.name not in requester_alts:
                requester_alts.append(confirmer.name)
                logger.log_info(f"Added {confirmer.name} to {requester.name}'s public_alts list")
            else:
                logger.log_info(f"{confirmer.name} already in {requester.name}'s public_alts list")
                
            if requester.name not in confirmer_alts:
                confirmer_alts.append(requester.name)
                logger.log_info(f"Added {requester.name} to {confirmer.name}'s public_alts list")
            else:
                logger.log_info(f"{requester.name} already in {confirmer.name}'s public_alts list")
                
            # Log the final alt lists before saving
            logger.log_info(f"FINAL ALT LIST FOR {confirmer.name}: {confirmer_alts}")
            logger.log_info(f"FINAL ALT LIST FOR {requester.name}: {requester_alts}")
                
            # Clean up pending requests for confirmer
            pending_requests = confirmer.attributes.get("pending_alt_requests", {})
            if isinstance(pending_requests, dict) and requester.name in pending_requests:
                # Just remove the specific entry, not the whole dict
                del pending_requests[requester.name]
                logger.log_info(f"Removed pending request from {requester.name} in {confirmer.name}'s list")
                confirmer.attributes.add("pending_alt_requests", pending_requests)
                
            # Clean up outgoing requests for requester
            outgoing_requests = requester.attributes.get("outgoing_alt_requests", {})
            if isinstance(outgoing_requests, dict) and confirmer.name in outgoing_requests:
                # Just remove the specific entry, not the whole dict
                del outgoing_requests[confirmer.name]
                logger.log_info(f"Removed outgoing request to {confirmer.name} in {requester.name}'s list")
                requester.attributes.add("outgoing_alt_requests", outgoing_requests)
                
            # Save updated alt lists to both characters using attributes.add for consistency
            logger.log_info(f"Saving {confirmer.name}'s alts. List has {len(confirmer_alts)} alts: {confirmer_alts}")
            logger.log_info(f"Saving {requester.name}'s alts. List has {len(requester_alts)} alts: {requester_alts}")
            
            # Important: Use attributes.add to ensure values are saved to the database
            confirmer.attributes.add('public_alts', confirmer_alts)
            requester.attributes.add('public_alts', requester_alts)
            
            # Log all alt-related attributes for debugging
            logger.log_info(f"==== ATTRIBUTE DUMP ====")
            logger.log_info(f"Confirmer {confirmer.name} all attributes: {confirmer.attributes.all()}")
            logger.log_info(f"Requester {requester.name} all attributes: {requester.attributes.all()}")
            
            # Verify that the attributes were properly set
            confirmer_check = confirmer.attributes.get('public_alts', [])
            requester_check = requester.attributes.get('public_alts', [])
            logger.log_info(f"After setting, confirmer {confirmer.name}'s alts are: {confirmer_check}")
            logger.log_info(f"After setting, requester {requester.name}'s alts are: {requester_check}")
            
            # Force-save the entire character objects
            confirmer.save()
            requester.save()
            
            # Perform a final verification that attributes were saved
            confirmer.flush_from_cache(force=True)
            requester.flush_from_cache(force=True)
            final_confirmer_alts = confirmer.attributes.get('public_alts', [])
            final_requester_alts = requester.attributes.get('public_alts', [])
            logger.log_info(f"FINAL CHECK - confirmer {confirmer.name}'s alts: {final_confirmer_alts}")
            logger.log_info(f"FINAL CHECK - requester {requester.name}'s alts: {final_requester_alts}")
            
            # Notify the requester that their alt was confirmed, if they're online
            if requester.has_account and requester.sessions.count() > 0:
                requester.msg(f"{confirmer.name} has confirmed you as their alt!")
            
            # Also send a mail notification in case they're offline
            if requester.has_account:
                try:
                    subject = f"Alt Request Confirmed by {confirmer.name}"
                    message = f"{confirmer.name} has confirmed your alt request. You are now linked as alts."
                    
                    # Use execute_cmd to send the mail (this is how the jobs system does it)
                    requester_account = requester.account
                    if requester_account:
                        mail_cmd = f"@mail {requester_account.username}={subject}/{message}"
                        confirmer.execute_cmd(mail_cmd)
                        logger.log_info(f"Confirmation mail sent from {confirmer.name} to {requester.name}")
                    else:
                        logger.log_err(f"Missing account for confirmation mail: requester={requester.name}")
                except Exception as e:
                    logger.log_err(f"Error sending confirmation mail: {e}")
            
            logger.log_info(f"Successfully confirmed alt relationship between {confirmer.name} and {requester.name}")
            return True
            
        except Exception as e:
            logger.log_err(f"Error in alt confirmation process: {e}")
            return False
    
    def reject_alt(self):
        """Reject an alt relationship request."""
        from evennia.utils import logger
        
        caller = self.caller
        args = self.args.strip()
        
        if not args:
            caller.msg("Usage: +alts/reject <character name>")
            return
            
        # Check if there are any pending requests
        pending_requests = caller.attributes.get('pending_alt_requests', {})
        if not isinstance(pending_requests, dict) or not pending_requests:
            caller.msg("You have no pending alt requests to reject.")
            return
            
        # Find the character
        requester_name = args
        if requester_name not in pending_requests:
            caller.msg(f"You don't have a pending alt request from {requester_name}.")
            return
            
        # Find the requester character
        requester = search_object(requester_name, typeclass="typeclasses.characters.Character")
        
        # Remove the pending request
        del pending_requests[requester_name]
        caller.attributes.add('pending_alt_requests', pending_requests)
        
        # Also clean up the requester's outgoing request if it exists
        if requester and len(requester) == 1:
            requester = requester[0]
            requester_outgoing = requester.attributes.get('outgoing_alt_requests', {})
            if isinstance(requester_outgoing, dict) and caller.name in requester_outgoing:
                del requester_outgoing[caller.name]
                requester.attributes.add('outgoing_alt_requests', requester_outgoing)
            
            # Notify the requester if they're online
            if requester.has_account:
                requester.msg(f"{caller.name} has rejected your alt request.")
        
        caller.msg(f"You have rejected the alt request from {requester_name}.")
        logger.log_info(f"{caller.name} rejected alt request from {requester_name}")
    
    def list_pending_requests(self):
        """List pending alt requests."""
        caller = self.caller
        from time import time
        from evennia.utils import logger
        
        # Force refresh from database to ensure we have the most current data
        caller.flush_from_cache(force=True)
        
        # Check incoming requests - use attributes.get for consistency
        has_pending = False
        pending_msg = "Pending Alt Requests:\n"
        
        # Get pending requests and debug their state
        pending_requests = caller.attributes.get('pending_alt_requests', {})
        logger.log_info(f"==== PENDING REQUESTS DEBUG ====")
        logger.log_info(f"Type: {type(pending_requests)}")
        logger.log_info(f"Raw value: {pending_requests!r}")
        logger.log_info(f"Dict check: {isinstance(pending_requests, dict)}")
        logger.log_info(f"Boolean check: {bool(pending_requests)}")
        if isinstance(pending_requests, dict):
            logger.log_info(f"Length: {len(pending_requests)}")
            logger.log_info(f"Keys: {list(pending_requests.keys())}")
        
        # Try using direct DB query
        try:
            from evennia.utils.dbserialize import deserialize
            from evennia.typeclasses.attributes import Attribute
            
            db_attr = Attribute.objects.filter(
                db_key='pending_alt_requests',
                objectdb=caller.id
            ).first()
            
            if db_attr:
                try:
                    db_value = deserialize(db_attr.db_value)
                    logger.log_info(f"DB direct query: {db_value}")
                    logger.log_info(f"DB value type: {type(db_value)}")
                    
                    # If the attribute API didn't return a proper dict but DB has data, use the DB data
                    if not isinstance(pending_requests, dict) or not pending_requests:
                        if isinstance(db_value, dict) and db_value:
                            logger.log_info(f"Using DB value instead of attribute API value")
                            pending_requests = db_value
                except Exception as e:
                    logger.log_err(f"Error deserializing pending_alt_requests: {e}")
        except Exception as e:
            logger.log_err(f"Error querying database: {e}")
        
        # Now process the pending requests
        if isinstance(pending_requests, dict) and pending_requests:
            has_pending = True
            pending_msg += "\nIncoming Requests:\n"
            for requester, request in pending_requests.items():
                time_ago = int((time() - request['timestamp']) / 86400)  # Days
                if time_ago == 0:
                    time_str = "today"
                elif time_ago == 1:
                    time_str = "yesterday"
                else:
                    time_str = f"{time_ago} days ago"
                    
                # Include confirmation code in the listing for convenience
                code = request.get('code', 'NO_CODE')
                pending_msg += f"• {requester} (requested {time_str}) - Code: {code}\n"
        
        # Check outgoing requests 
        outgoing_requests = caller.attributes.get('outgoing_alt_requests', {})
        logger.log_info(f"==== OUTGOING REQUESTS DEBUG ====")
        logger.log_info(f"Type: {type(outgoing_requests)}")
        logger.log_info(f"Raw value: {outgoing_requests!r}")
        
        # Try using direct DB query for outgoing requests
        try:
            db_attr = Attribute.objects.filter(
                db_key='outgoing_alt_requests',
                objectdb=caller.id
            ).first()
            
            if db_attr:
                try:
                    db_value = deserialize(db_attr.db_value)
                    logger.log_info(f"DB direct query for outgoing: {db_value}")
                    
                    # If the attribute API didn't return a proper dict but DB has data, use the DB data
                    if not isinstance(outgoing_requests, dict) or not outgoing_requests:
                        if isinstance(db_value, dict) and db_value:
                            logger.log_info(f"Using DB value instead of attribute API value for outgoing")
                            outgoing_requests = db_value
                except Exception as e:
                    logger.log_err(f"Error deserializing outgoing_alt_requests: {e}")
        except Exception as e:
            logger.log_err(f"Error querying database for outgoing requests: {e}")
        
        if isinstance(outgoing_requests, dict) and outgoing_requests:
            has_pending = True
            pending_msg += "\nOutgoing Requests:\n"
            for target, request in outgoing_requests.items():
                time_ago = int((time() - request['timestamp']) / 86400)  # Days
                if time_ago == 0:
                    time_str = "today"
                elif time_ago == 1:
                    time_str = "yesterday"
                else:
                    time_str = f"{time_ago} days ago"
                    
                pending_msg += f"• {target} (sent {time_str})\n"
        
        # Log what we're finding
        logger.log_info(f"{caller.name}'s pending_requests: {pending_requests}")
        logger.log_info(f"{caller.name}'s outgoing_requests: {outgoing_requests}")
                
        if not has_pending:
            caller.msg("You have no pending alt requests.")
        else:
            caller.msg(pending_msg)
    
    def remove_alt(self):
        """Remove a character from your list of alts."""
        from evennia.utils import logger
        
        caller = self.caller
        args = self.args.strip()
        
        if not args:
            caller.msg("Usage: +alts/del <character name>")
            return
        
        # Get the list of alts from the caller's attributes
        alts = caller.attributes.get('public_alts', [])
        if not isinstance(alts, list):
            alts = []
        
        # Check if the character is in the list
        if args not in alts:
            caller.msg(f"{args} is not listed as your alt.")
            return
        
        # Remove the character from the caller's alts
        alts.remove(args)
        caller.attributes.add('public_alts', alts)
        
        # Try to find the target character to remove the two-way relationship
        target = search_object(args, typeclass="typeclasses.characters.Character")
        if target and len(target) == 1:
            target = target[0]
            target_alts = target.attributes.get('public_alts', [])
            if not isinstance(target_alts, list):
                target_alts = []
                
            if caller.name in target_alts:
                target_alts.remove(caller.name)
                target.attributes.add('public_alts', target_alts)
                target.msg(f"{caller.name} has removed you from their list of alts.")
        
        caller.msg(f"Removed {args} from your list of alts.")
        logger.log_info(f"{caller.name} removed alt relationship with {args}")
    
    def block_alt(self):
        """Block a character from sending you alt requests."""
        from evennia.utils import logger
        
        caller = self.caller
        args = self.args.strip()
        
        if not args:
            caller.msg("Usage: +alts/block <character name>")
            return
        
        # Find the target character
        target = search_object(args, typeclass="typeclasses.characters.Character")
        if not target:
            caller.msg(f"Could not find character '{args}'.")
            return
        if len(target) > 1:
            caller.msg(f"Multiple matches found for '{args}'. Please be more specific.")
            return
            
        target = target[0]  # Get the first (and only) match
        
        # Get the block list or initialize it
        blocks = caller.attributes.get('alt_blocks', [])
        if not isinstance(blocks, list):
            blocks = []
        
        # Check if already blocked
        if target.name in blocks:
            caller.msg(f"{target.name} is already blocked from sending you alt requests.")
            return
        
        # Add to block list
        blocks.append(target.name)
        caller.attributes.add('alt_blocks', blocks)
        
        # If there's a pending request, automatically reject it
        pending_requests = caller.attributes.get('pending_alt_requests', {})
        if isinstance(pending_requests, dict) and target.name in pending_requests:
            del pending_requests[target.name]
            caller.attributes.add('pending_alt_requests', pending_requests)
            
            # Clean up the target's outgoing request
            target_outgoing = target.attributes.get('outgoing_alt_requests', {})
            if isinstance(target_outgoing, dict) and caller.name in target_outgoing:
                del target_outgoing[caller.name]
                target.attributes.add('outgoing_alt_requests', target_outgoing)
        
        caller.msg(f"Blocked {target.name} from sending you alt requests.")
        logger.log_info(f"{caller.name} blocked alt requests from {target.name}")
    
    def unblock_alt(self):
        """Unblock a character from sending you alt requests."""
        from evennia.utils import logger
        
        caller = self.caller
        args = self.args.strip()
        
        if not args:
            caller.msg("Usage: +alts/unblock <character name>")
            return
        
        # Get the block list
        blocks = caller.attributes.get('alt_blocks', [])
        if not isinstance(blocks, list):
            blocks = []
        
        # Check if the character is blocked
        if args not in blocks:
            caller.msg(f"{args} is not blocked from sending you alt requests.")
            return
        
        # Remove from block list
        blocks.remove(args)
        caller.attributes.add('alt_blocks', blocks)
        
        caller.msg(f"Unblocked {args} from sending you alt requests.")
        logger.log_info(f"{caller.name} unblocked {args} for alt requests")
    
    def staff_remove_alt(self, char1, char2):
        """Staff-only method to force remove an alt relationship between two characters."""
        # Find the first character
        character1 = search_object(char1, typeclass="typeclasses.characters.Character")
        if not character1:
            return f"Could not find character '{char1}'."
        if len(character1) > 1:
            return f"Multiple matches found for '{char1}'. Please be more specific."
            
        character1 = character1[0]
        
        # Find the second character
        character2 = search_object(char2, typeclass="typeclasses.characters.Character")
        if not character2:
            return f"Could not find character '{char2}'."
        if len(character2) > 1:
            return f"Multiple matches found for '{char2}'. Please be more specific."
            
        character2 = character2[0]
        
        # Remove from first character's alt list
        char1_alts = character1.attributes.get('public_alts', [])
        if not isinstance(char1_alts, list):
            char1_alts = []
            
        if character2.name in char1_alts:
            char1_alts.remove(character2.name)
            character1.attributes.add('public_alts', char1_alts)
        
        # Remove from second character's alt list
        char2_alts = character2.attributes.get('public_alts', [])
        if not isinstance(char2_alts, list):
            char2_alts = []
            
        if character1.name in char2_alts:
            char2_alts.remove(character1.name)
            character2.attributes.add('public_alts', char2_alts)
            
        return f"Removed alt relationship between {character1.name} and {character2.name}."
    
    def show_staff_alts(self):
        """Show IP-based and public alts of a character (staff only)."""
        from evennia.utils import logger
        
        caller = self.caller
        args = self.args.strip()
        
        # Only staff can use this command
        if not (caller.check_permstring("Builder") or caller.check_permstring("Admin")):
            caller.msg("You don't have permission to use this command.")
            return
        
        if not args:
            caller.msg("Usage: +alts/staff <character name>")
            return
        
        # Find the target character
        target = search_object(args, typeclass="typeclasses.characters.Character")
        if not target:
            caller.msg(f"Could not find character '{args}'.")
            return
        if len(target) > 1:
            caller.msg(f"Multiple matches found for '{args}'. Please be more specific.")
            return
            
        target = target[0]  # Get the first (and only) match
        
        # Force refresh from database to ensure we have current data
        target.flush_from_cache(force=True)
        
        # Log to help debug issues
        logger.log_info(f"+alts/staff: Checking alts for {target.name} (#{target.id})")
        
        # Get the target's account
        account = target.account
        
        # Build the display
        total_width = 78
        
        # Header
        title = f" {target.name}'s Alts (STAFF VIEW) "
        title_len = len(title)
        dash_count = (total_width - title_len) // 2
        msg = f"{'|b-|n' * dash_count}{title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
        
        # Get the IP information for the target
        current_ips = set()
        creator_ip = target.attributes.get('creator_ip', None)
        last_ip = target.attributes.get('last_ip', None)
        
        # Get current IP(s) from active sessions
        if account:
            # Log account info for debugging
            logger.log_info(f"+alts/staff: Target has account {account.name} (#{account.id})")
            sessions = account.sessions.all()
            logger.log_info(f"+alts/staff: Account has {len(sessions)} session(s)")
            for session in sessions:
                ip_addr = isinstance(session.address, tuple) and session.address[0] or session.address
                current_ips.add(ip_addr)
                logger.log_info(f"+alts/staff: Found session IP: {ip_addr}")
        
        # Character IP Information Section
        ip_title = "|y Character IP Information |n"
        title_len = len(ip_title)
        dash_count = (total_width - title_len) // 2
        msg += f"{'|b-|n' * dash_count}{ip_title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
        
        msg += f"Account: {account.name if account else 'None'}\n"
        msg += f"Creator IP: {creator_ip or 'Unknown'}\n"
        msg += f"Last IP: {last_ip or 'Unknown'}\n"
        if current_ips:
            msg += f"Current IP(s): {', '.join(current_ips)}\n"
        
        # Check for IP discrepancies
        if creator_ip and last_ip and creator_ip != last_ip:
            msg += "|rNOTE: Creator IP and Last IP are different! Character may have been transferred.|n\n"
        
        # Collect all IPs to check against
        all_target_ips = set()
        if creator_ip:
            all_target_ips.add(creator_ip)
        if last_ip:
            all_target_ips.add(last_ip)
        all_target_ips.update(current_ips)
        
        logger.log_info(f"+alts/staff: All target IPs: {all_target_ips}")
        
        # Get all characters using different methods to ensure we find everyone
        from evennia.objects.models import ObjectDB
        from django.conf import settings
        
        # Get all characters directly from the database
        character_typeclass = settings.BASE_CHARACTER_TYPECLASS
        all_db_characters = list(ObjectDB.objects.filter(db_typeclass_path=character_typeclass))
        logger.log_info(f"+alts/staff: Found {len(all_db_characters)} characters in database")
        
        # Also get all characters through search_object for redundancy
        all_search_characters = search_object("", typeclass=character_typeclass)
        logger.log_info(f"+alts/staff: Found {len(all_search_characters)} characters via search")
        
        # Merge the two lists to make sure we have everything
        all_character_ids = set(char.id for char in all_db_characters)
        for char in all_search_characters:
            if char.id not in all_character_ids:
                all_db_characters.append(char)
                all_character_ids.add(char.id)
        
        logger.log_info(f"+alts/staff: Combined character count: {len(all_db_characters)}")
        
        # Currently Online Characters Section
        online_title = "|y Currently Online Characters (Same IP) |n"
        title_len = len(online_title)
        dash_count = (total_width - title_len) // 2
        msg += f"\n{'|b-|n' * dash_count}{online_title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
        
        if not all_target_ips:
            msg += "No IP information available for this character.\n"
        else:
            # Direct check of all sessions in the system
            from evennia.server.sessionhandler import SESSIONS
            
            # Find online characters with matching IPs
            online_alts = []
            
            # First check all active sessions directly
            for session in SESSIONS.get_sessions():
                session_obj = session.puppet
                if not session_obj or session_obj == target:
                    continue
                
                # Get the session's IP
                session_ip = isinstance(session.address, tuple) and session.address[0] or session.address
                logger.log_info(f"+alts/staff: Checking session for {session_obj.name} with IP {session_ip}")
                
                # Check if it matches any of our target IPs
                if session_ip in all_target_ips:
                    account_name = session.account.name if session.account else "None"
                    online_alts.append((session_obj.name, account_name, session_ip))
                    logger.log_info(f"+alts/staff: Found match: {session_obj.name} - {account_name} - {session_ip}")
            
            # Then also check through the character objects as backup
            for character in all_db_characters:
                # Skip the target character
                if character == target:
                    continue
                
                # Skip characters we've already found via sessions
                if any(alt[0] == character.name for alt in online_alts):
                    continue
                
                # Skip characters without accounts
                if not character.account:
                    continue
                
                logger.log_info(f"+alts/staff: Checking character {character.name} (#{character.id})")
                
                # Check if any sessions match the target's IP
                char_sessions = character.account.sessions.all()
                if char_sessions:
                    char_ips = set()
                    for session in char_sessions:
                        # Get the IP address
                        char_ip = isinstance(session.address, tuple) and session.address[0] or session.address
                        char_ips.add(char_ip)
                        logger.log_info(f"+alts/staff: Found IP for {character.name}: {char_ip}")
                    
                    # Check for any matching IPs
                    matching_ips = char_ips.intersection(all_target_ips)
                    if matching_ips:
                        online_alts.append((character.name, character.account.name, ', '.join(matching_ips)))
                        logger.log_info(f"+alts/staff: Found match: {character.name} - {character.account.name} - {matching_ips}")
            
            if online_alts:
                # Header row
                msg += f"{'Character':<20} {'Account':<15} {'Matching IP(s)'}\n"
                msg += f"{'-'*19} {'-'*14} {'-'*20}\n"
                
                # List the alts with their information
                for alt_name, account_name, match_ips in sorted(online_alts):
                    msg += f"{alt_name:<20} {account_name:<15} {match_ips}\n"
            else:
                msg += "No other characters currently online from the same IP(s).\n"
                
        # Characters with Same Creator IP Section
        creator_title = "|y Characters with Same Creator IP |n"
        title_len = len(creator_title)
        dash_count = (total_width - title_len) // 2
        msg += f"\n{'|b-|n' * dash_count}{creator_title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
        
        if not creator_ip:
            msg += "No creator IP information available for this character.\n"
        else:
            # Find all characters with the same creator IP
            creator_alts = []
            
            for character in all_db_characters:
                if character == target:
                    continue
                
                char_creator_ip = character.attributes.get('creator_ip', None)
                if char_creator_ip == creator_ip:
                    char_account = character.account
                    account_name = char_account.name if char_account else "None"
                    
                    # Check if there's a mismatch in last IP
                    char_last_ip = character.attributes.get('last_ip', None)
                    ip_mismatch = char_last_ip and char_last_ip != creator_ip
                    
                    creator_alts.append((character.name, account_name, ip_mismatch))
                    logger.log_info(f"+alts/staff: Found creator IP match: {character.name}")
            
            if creator_alts:
                # Header row
                msg += f"{'Character':<20} {'Account':<15} {'IP Changed'}\n"
                msg += f"{'-'*19} {'-'*14} {'-'*9}\n"
                
                # List the alts with their information
                for alt_name, account_name, ip_mismatch in sorted(creator_alts):
                    mismatch_indicator = "|rYes|n" if ip_mismatch else "No"
                    msg += f"{alt_name:<20} {account_name:<15} {mismatch_indicator}\n"
            else:
                msg += "No other characters have the same creator IP.\n"
        
        # Characters with Same Last IP Section
        last_ip_title = "|y Characters with Same Last IP |n"
        title_len = len(last_ip_title)
        dash_count = (total_width - title_len) // 2
        msg += f"\n{'|b-|n' * dash_count}{last_ip_title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
        
        if not last_ip:
            msg += "No last IP information available for this character.\n"
        else:
            # Find all characters with the same last IP
            last_ip_alts = []
            
            for character in all_db_characters:
                if character == target:
                    continue
                
                char_last_ip = character.attributes.get('last_ip', None)
                if char_last_ip == last_ip:
                    char_account = character.account
                    account_name = char_account.name if char_account else "None"
                    
                    # Check if there's a mismatch in creator IP
                    char_creator_ip = character.attributes.get('creator_ip', None)
                    ip_mismatch = char_creator_ip and char_creator_ip != last_ip
                    
                    # Calculate time since last disconnect
                    last_disconnect = character.attributes.get('last_disconnect', None)
                    time_ago = "Unknown"
                    if last_disconnect:
                        from time import time
                        days_offline = int((time() - last_disconnect) / (24 * 60 * 60))
                        if days_offline == 0:
                            time_ago = "Today"
                        else:
                            time_ago = f"{days_offline} day{'s' if days_offline != 1 else ''} ago"
                    
                    last_ip_alts.append((character.name, account_name, ip_mismatch, time_ago))
                    logger.log_info(f"+alts/staff: Found last IP match: {character.name}")
            
            if last_ip_alts:
                # Header row
                msg += f"{'Character':<20} {'Account':<15} {'Creator IP Diff':<15} {'Last Seen'}\n"
                msg += f"{'-'*19} {'-'*14} {'-'*14} {'-'*9}\n"
                
                # List the alts with their information
                for alt_name, account_name, ip_mismatch, time_ago in sorted(last_ip_alts, key=lambda x: x[0]):
                    mismatch_indicator = "|rYes|n" if ip_mismatch else "No"
                    msg += f"{alt_name:<20} {account_name:<15} {mismatch_indicator:<15} {time_ago}\n"
            else:
                msg += "No other characters have the same last IP.\n"
        
        # Potential Account Transfers Section
        transfer_title = "|y Potential Account Transfers |n"
        title_len = len(transfer_title)
        dash_count = (total_width - title_len) // 2
        msg += f"\n{'|b-|n' * dash_count}{transfer_title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
        
        # Find characters with different creator and last IPs
        transfers = []
        
        for character in all_db_characters:
            char_creator_ip = character.attributes.get('creator_ip', None)
            char_last_ip = character.attributes.get('last_ip', None)
            
            # Check if both IPs exist and are different
            if char_creator_ip and char_last_ip and char_creator_ip != char_last_ip:
                # Match if either IP matches any of the target's IPs
                if char_creator_ip in all_target_ips or char_last_ip in all_target_ips:
                    char_account = character.account
                    account_name = char_account.name if char_account else "None"
                    transfers.append((character.name, account_name, char_creator_ip, char_last_ip))
                    logger.log_info(f"+alts/staff: Found potential transfer: {character.name}")
        
        if transfers:
            # Header row
            msg += f"{'Character':<16} {'Account':<10} {'Creator IP':<15} {'Last IP'}\n"
            msg += f"{'-'*15} {'-'*9} {'-'*14} {'-'*15}\n"
            
            # List the transfers with their information
            for alt_name, account_name, creator_ip, last_ip in sorted(transfers):
                msg += f"{alt_name:<16} {account_name:<10} {creator_ip:<15} {last_ip}\n"
        else:
            msg += "No potential account transfers detected.\n"
        
        # Public alts section
        pub_title = "|y Publicly Declared Alts |n"
        title_len = len(pub_title)
        dash_count = (total_width - title_len) // 2
        msg += f"\n{'|b-|n' * dash_count}{pub_title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
        
        # Get the list of public alts with direct DB query for maximum reliability
        from evennia.utils.dbserialize import deserialize
        from evennia.typeclasses.attributes import Attribute
        
        db_attr = Attribute.objects.filter(
            db_key='public_alts',
            objectdb=target.id
        ).first()
        
        public_alts = []
        
        if db_attr:
            try:
                db_value = deserialize(db_attr.db_value)
                if isinstance(db_value, list):
                    public_alts = db_value
                logger.log_info(f"+alts/staff: DB direct query for public_alts: {db_value}")
            except Exception as e:
                logger.log_err(f"Error deserializing public_alts: {e}")
                
        # If no DB value, try via attribute API
        if not public_alts:
            api_alts = target.attributes.get('public_alts', [])
            # Try to convert to list if not already
            try:
                if hasattr(api_alts, '__iter__') and hasattr(api_alts, '__getitem__'):
                    public_alts = list(api_alts)
            except Exception as e:
                logger.log_err(f"Error converting alts to list: {e}")
        
        logger.log_info(f"+alts/staff: Target's public alts: {public_alts}")
        
        if not public_alts:
            msg += f"{target.name} has not declared any alt characters."
        else:
            for alt_name in public_alts:
                msg += f"• {alt_name}\n"
        
        caller.msg(msg) 