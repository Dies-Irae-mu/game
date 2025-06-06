"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""

from evennia import DefaultExit
from evennia.utils import logger
from evennia.commands.cmdset import CmdSet
from evennia.commands.command import Command

class ExitCommand(Command):
    """
    Command class for an exit.
    """
    def __init__(self, key=None, aliases=None, destination=None, **kwargs):
        super().__init__(**kwargs)
        self.key = key.lower() if key else ""
        self.aliases = [alias.lower() for alias in aliases] if aliases else []
        self.destination = destination
        self.locks = "cmd:all()"
        self.auto_help = False
    
    def func(self):
        """
        Move caller to destination.
        """
        # First check if we can even see the exit
        if not self.obj.access(self.caller, "view"):
            self.caller.msg("You cannot go that way.")
            return
            
        # Debug output
        self.caller.msg(f"DEBUG: Attempting to traverse {self.obj.key}")
        self.caller.msg(f"DEBUG: Current locks: {self.obj.locks}")
        
        # Check if we can traverse
        if not self.obj.access(self.caller, "traverse"):
            self.caller.msg(f"You cannot go that way.")
            return
            
        # All good - try to traverse
        self.obj.at_traverse(self.caller, self.obj.destination)
    
    def access(self, accessing_obj, access_type="view", default=True):
        """
        Override access check to allow Admin permission to bypass all locks.
        """
        # Check if accessing_obj has Admin permission
        if hasattr(accessing_obj, 'check_permstring'):
            if accessing_obj.check_permstring("Admin"):
                return True
                
        # If not Admin, use default access check
        return super().access(accessing_obj, access_type, default)

class ExitCmdSet(CmdSet):
    """
    Cmdset for exits.
    """
    key = "ExitCmdSet"
    priority = 101
    duplicates = False
    
    def at_cmdset_creation(self):
        """
        Called when the cmdset is created.
        """
        self.add(ExitCommand)

class Exit(DefaultExit):
    """
    Custom exit class for Dies Irae.
    """
    
    @property
    def is_npc(self):
        """Return False for exits to distinguish from NPCs."""
        return False
        
    def at_object_creation(self):
        """
        Called when exit is first created.
        """
        super().at_object_creation()
        self.at_cmdset_creation()
        # Ensure view lock is set to allow all by default
        if not any(lock.startswith("view:") for lock in self.locks.all()):
            self.locks.add("view:all()")
        
    def at_cmdset_creation(self):
        """
        Called when cmdset is first created.
        """
        cmdset = ExitCmdSet()
        cmdset.key = f"ExitCmdSet_{self.key}"
        cmdset.priority = 101
        cmdset.duplicates = False
        cmdset.obj = self
        
        cmd = ExitCommand(
            key=self.name,
            aliases=self.aliases.all(),
            destination=self.destination,
            obj=self
        )
        cmdset.add(cmd)
        self.cmdset.add(cmdset, permanent=True)
    
    def access(self, accessing_obj, access_type="view", default=True, **kwargs):
        """
        Override access check to allow Admin permission to bypass all locks.
        Handles all possible access method arguments.
        
        Args:
            accessing_obj (Object): The object trying to access
            access_type (str): The type of access being checked
            default (bool): The default result if no lock is found
            **kwargs: Additional arguments that might be passed
        """
        # Check if accessing_obj has Admin permission
        if hasattr(accessing_obj, 'check_permstring'):
            # Check each permission separately
            for perm in ["Admin", "Builder", "Staff"]:
                if accessing_obj.check_permstring(perm):
                    return True
                
        # If not Admin, use default access check
        return super().access(accessing_obj, access_type, default, **kwargs)
    
    def return_appearance(self, looker, **kwargs):
        """
        Override return_appearance to add more robust view checking.
        """
        # Check view access first
        if not self.access(looker, "view"):
            logger.log_info(f"Exit {self.key} appearance not visible to {looker}")
            return ""
        
        # If view access is granted, return the appearance
        return super().return_appearance(looker, **kwargs)
        
    def get_display_name(self, looker, **kwargs):
        """
        Override display name to add more robust view checking.
        """
        # Check view access first
        if not self.access(looker, "view"):
            logger.log_info(f"Exit {self.key} not visible to {looker}")
            return ""
        
        # If view access is granted, return the display name
        return super().get_display_name(looker, **kwargs)
    
    def get_aliases(self, looker, **kwargs):
        """
        Returns the aliases for this specific looker.
        Only show if the looker passes the view lock.
        """
        if not self.access(looker, "view"):
            return []
        return super().get_aliases(looker, **kwargs)
    
    def format_appearance(self, looker, appearance_type="normal", **kwargs):
        """
        Format the appearance of the exit.
        Only show if the looker passes the view lock.
        
        Args:
            looker (Object): The object looking at this exit.
            appearance_type (str): The type of appearance to return.
            **kwargs: Arbitrary keyword arguments.
            
        Returns:
            str: The formatted appearance string
        """
        if not self.access(looker, "view"):
            return ""
            
        # Get the destination name
        destination = self.destination
        if destination:
            try:
                dest_name = destination.get_display_name(looker)
            except (AttributeError, TypeError):
                # Fallback if looker isn't a proper object or get_display_name fails
                dest_name = destination.name if hasattr(destination, 'name') else str(destination)
                
            desc = f"Exit to {dest_name}"
            if self.db.desc:
                desc = f"{desc}\n{self.db.desc}"
            return desc
        return "Exit to nowhere"
    
    def get_extra_info(self, looker, **kwargs):
        """
        Override extra info to add more robust view checking.
        """
        # Check view access first
        if not self.access(looker, "view"):
            logger.log_info(f"Exit {self.key} extra info not visible to {looker}")
            return ""
        
        # If view access is granted, return the extra info
        return super().get_extra_info(looker, **kwargs)
    
    def at_look(self, looker, **kwargs):
        """
        Called when this object is looked at.
        Only show if the looker passes the view lock.
        """
        if not self.access(looker, "view"):
            return ""
        return super().at_look(looker, **kwargs)
    
    def at_traverse(self, traversing_object, target_location, **kwargs):
        """
        Called when an object wants to traverse this exit.
        """
        # Check if object has permission to pass
        if not self.access(traversing_object, "traverse"):
            if hasattr(traversing_object, 'msg'):
                traversing_object.msg(f"You cannot traverse {self.key}.")
            return False
            
        # Check if current location prevents exit use
        if hasattr(traversing_object.location, "prevent_exit_use"):
            try:
                if traversing_object.location.prevent_exit_use(self, traversing_object):
                    return False
            except Exception as e:
                # Log error but don't crash
                logger.log_err(f"Error in prevent_exit_use: {e}")
                if hasattr(traversing_object, 'msg'):
                    traversing_object.msg("There was an error processing your movement. Please try again.")
                return False
        
        # Notify sessions about the upcoming move
        if hasattr(traversing_object, 'sessions'):
            for session in traversing_object.sessions.all():
                if hasattr(session, 'puppet') and session.puppet == traversing_object:
                    session.msg(text=f"Moving to {target_location.name if target_location else 'unknown location'}...")
            
        # Call parent's at_traverse
        success = super().at_traverse(traversing_object, target_location, **kwargs)
        
        # Force location update to ensure consistency
        if success and traversing_object.location != target_location:
            traversing_object.location = target_location
            logger.log_info(f"Force-updated location for {traversing_object} to {target_location}")
            
        return success
    
    def at_failed_traverse(self, traversing_object, **kwargs):
        """
        Called when traversal fails.
        """
        if hasattr(traversing_object, 'msg'):
            traversing_object.msg(f"You cannot traverse {self.key}.")
        return False
    
    def get_cmd_signatures(self, caller):
        """
        Returns a list of command signatures available to the caller.
        Hide commands if caller can't view the exit.
        """
        if not self.access(caller, "view"):
            return []
        return super().get_cmd_signatures(caller)
    
    def at_before_get(self, looker, **kwargs):
        """
        Called before get/search attempts.
        Only allow if the looker passes the view lock.
        """
        if not self.access(looker, "view"):
            return False
        return True
    
    def matches(self, searchdata, exact=False, global_search=False, caller=None, **kwargs):
        """
        Match if searcher passes view check.
        """
        if caller and not self.access(caller, "view"):
            return 0.0
        return super().matches(searchdata, exact, global_search, caller, **kwargs)
    
    def search(self, searchdata, caller=None, **kwargs):
        """
        Search only if caller passes view check.
        """
        if caller and not self.access(caller, "view"):
            return None
        return super().search(searchdata, caller=caller, **kwargs)

class ApartmentExit(Exit):
    """
    Custom exit class for apartment entrances and exits.
    This class handles special functionality for apartment access.
    """
    
    def at_object_creation(self):
        """
        Called when exit is first created.
        """
        super().at_object_creation()
        # Set default locks for apartments - allow tenants, admin, builders, and staff
        self.locks.add("view:all();traverse:perm(Admin) or perm(Builder) or perm(Staff) or tenant()")
        
    def at_traverse(self, traversing_object, target_location, **kwargs):
        """
        Called when someone attempts to traverse this exit.
        Checks if the traversing object has permission to enter the apartment.
        """
        # Check if object has permission to pass
        if not self.access(traversing_object, "traverse"):
            if hasattr(traversing_object, 'msg'):
                traversing_object.msg("You don't have permission to enter this apartment.")
            return False
        
        # Notify sessions about the upcoming move
        if hasattr(traversing_object, 'sessions'):
            for session in traversing_object.sessions.all():
                if hasattr(session, 'puppet') and session.puppet == traversing_object:
                    session.msg(text=f"Moving to {target_location.name if target_location else 'unknown location'}...")
            
        # Call parent's at_traverse
        success = super(Exit, self).at_traverse(traversing_object, target_location, **kwargs)
        
        # Force location update to ensure consistency
        if success and traversing_object.location != target_location:
            traversing_object.location = target_location
            logger.log_info(f"Force-updated location for {traversing_object} to {target_location}")
            
        return success
    
    def at_failed_traverse(self, traversing_object, **kwargs):
        """
        Called when traversal fails.
        """
        if hasattr(traversing_object, 'msg'):
            traversing_object.msg("You don't have permission to enter this apartment.")
        return False