"""
Controller for managing Situations, Details, and Developments.
"""

from datetime import datetime
from django.utils import timezone
from evennia.objects.objects import DefaultObject
from world.wod20th.models import Roster, RosterMember
from world.situations.models import Situation, Detail, Development
from evennia.objects.models import ObjectDB
from evennia.scripts.models import ScriptDB
from evennia.utils.create import create_object
from evennia.utils.utils import class_from_module

class SituationController(DefaultObject):
    """
    Controller for managing Situations and their components.
    
    A Situation represents a plot hook or ongoing storyline that can be accessed
    by specific rosters. Each Situation can have Details (additional information)
    and Developments (plot progression points).
    """
    
    def at_object_creation(self):
        """Called when object is first created."""
        self.db.situations = {}
    
    def create_situation(self, title, description, roster_names=None):
        """
        Create a new situation.
        
        Args:
            title (str): The title of the situation
            description (str): The description of the situation
            roster_names (list): List of roster names or IDs that can access this situation
        """
        # Convert roster references to names and verify they exist
        final_roster_names = []
        if roster_names:
            for roster_ref in roster_names:
                try:
                    # Try to get roster by ID first
                    if str(roster_ref).isdigit():
                        roster = Roster.objects.get(id=int(roster_ref))
                    else:
                        # If not a number, try by name
                        roster = Roster.objects.get(name=roster_ref)
                    final_roster_names.append(roster.name)
                except Roster.DoesNotExist:
                    return f"Error: Roster '{roster_ref}' does not exist."
        
        # Create the situation
        situation = Situation.objects.create(
            title=title,
            description=description,
            roster_names=final_roster_names
        )
        
        return f"Situation '{title}' created with ID {situation.id}"
        
    def add_detail(self, situation_id, title, content, roster_names=None, secrecy_rating=0):
        """
        Add a detail to a situation.
        
        Args:
            situation_id (int): The ID of the situation
            title (str): The title of the detail
            content (str): The content of the detail
            roster_names (list): List of roster names or IDs that can access this detail
            secrecy_rating (int): Secrecy rating (0-10) only visible to staff
        """
        try:
            situation = Situation.objects.get(id=situation_id)
        except Situation.DoesNotExist:
            return f"No situation found with ID {situation_id}"
            
        # Validate secrecy rating
        try:
            secrecy_rating = int(secrecy_rating)
            if secrecy_rating < 0 or secrecy_rating > 10:
                return f"Secrecy rating must be between 0 and 10"
        except (ValueError, TypeError):
            return f"Invalid secrecy rating. Must be a number between 0 and 10"
            
        # Convert roster references to names and verify they exist
        final_roster_names = []
        if roster_names:
            for roster_ref in roster_names:
                try:
                    # Try to get roster by ID first
                    if str(roster_ref).isdigit():
                        roster = Roster.objects.get(id=int(roster_ref))
                    else:
                        # If not a number, try by name
                        roster = Roster.objects.get(name=roster_ref)
                    # Only check roster access if situation has roster restrictions
                    if situation.roster_names and roster.name not in situation.roster_names:
                        return f"Error: Roster '{roster.name}' does not have access to this situation"
                    final_roster_names.append(roster.name)
                except Roster.DoesNotExist:
                    return f"Error: Roster '{roster_ref}' does not exist"
                    
        # Create the detail
        detail = Detail.objects.create(
            situation=situation,
            title=title,
            content=content,
            roster_names=final_roster_names,
            secrecy_rating=secrecy_rating
        )
        
        return f"Detail '{title}' added to situation {situation_id}"
        
    def add_development(self, situation_id, title, content, roster_names=None):
        """
        Add a development to a situation.
        
        Args:
            situation_id (int): The ID of the situation
            title (str): The title of the development
            content (str): The content of the development
            roster_names (list): List of roster names or IDs that can access this development
        """
        try:
            situation = Situation.objects.get(id=situation_id)
        except Situation.DoesNotExist:
            return f"No situation found with ID {situation_id}"
            
        # Convert roster references to names and verify they exist
        final_roster_names = []
        if roster_names:
            for roster_ref in roster_names:
                try:
                    # Try to get roster by ID first
                    if str(roster_ref).isdigit():
                        roster = Roster.objects.get(id=int(roster_ref))
                    else:
                        # If not a number, try by name
                        roster = Roster.objects.get(name=roster_ref)
                    # Only check roster access if situation has roster restrictions
                    if situation.roster_names and roster.name not in situation.roster_names:
                        return f"Error: Roster '{roster.name}' does not have access to this situation"
                    final_roster_names.append(roster.name)
                except Roster.DoesNotExist:
                    return f"Error: Roster '{roster_ref}' does not exist"
                    
        # Create the development
        development = Development.objects.create(
            situation=situation,
            title=title,
            content=content,
            roster_names=final_roster_names
        )
        
        return f"Development '{title}' added to situation {situation_id}"
        
    def resolve_development(self, situation_id, development_id, resolution_text):
        """
        Resolve a development with outcome text.
        
        Args:
            situation_id (int): The ID of the situation
            development_id (int): The ID of the development
            resolution_text (str): The resolution outcome text
        """
        try:
            situation = Situation.objects.get(id=situation_id)
            development = Development.objects.get(id=development_id, situation=situation)
        except (Situation.DoesNotExist, Development.DoesNotExist):
            return f"Development not found"
            
        development.resolved = True
        development.resolution_text = resolution_text
        development.resolved_at = timezone.now()
        development.save()
        
        return f"Development resolved"
        
    def link_job(self, situation_id, job_id):
        """
        Link a job to a situation.
        
        Args:
            situation_id (int): The ID of the situation
            job_id (int): The ID of the job to link
        """
        try:
            situation = Situation.objects.get(id=situation_id)
            Job = class_from_module("world.jobs.models.Job")
            job = Job.objects.get(id=job_id)
            situation.related_jobs.add(job)
            return f"Job {job_id} linked to situation {situation_id}"
        except Situation.DoesNotExist:
            return f"Situation {situation_id} not found"
        except Job.DoesNotExist:
            return f"Job {job_id} not found"
        
    def unlink_job(self, situation_id, job_id):
        """
        Unlink a job from a situation.
        
        Args:
            situation_id (int): The ID of the situation
            job_id (int): The ID of the job to unlink
        """
        try:
            situation = Situation.objects.get(id=situation_id)
            Job = class_from_module("world.jobs.models.Job")
            job = Job.objects.get(id=job_id)
            situation.related_jobs.remove(job)
            return f"Job {job_id} unlinked from situation {situation_id}"
        except Situation.DoesNotExist:
            return f"Situation {situation_id} not found"
        except Job.DoesNotExist:
            return f"Job {job_id} not found"
        
    def get_situation(self, situation_id):
        """Get a situation by ID."""
        return Situation.objects.get(id=situation_id)
        
    def get_all_situations(self):
        """Get all situations."""
        return Situation.objects.all().order_by('-created_at')
        
    def has_access(self, situation_id, character):
        """
        Check if a character has access to a situation.
        
        Args:
            situation_id (int): The ID of the situation
            character (Object): The character requesting access
        """
        try:
            situation = Situation.objects.get(id=situation_id)
            
            # Staff always have access
            if character.check_permstring("immortals"):
                return True
                
            # If no roster restrictions, everyone has access
            if not situation.roster_names:
                return True
                
            # Check if character is in any of the allowed rosters
            return RosterMember.objects.filter(
                roster__name__in=situation.roster_names,
                character=character,
                approved=True
            ).exists()
            
        except Situation.DoesNotExist:
            return False
        
    def has_detail_access(self, situation_id, detail_id, caller):
        """
        Check if a caller has access to a detail.
        
        Args:
            situation_id (int): The ID of the situation
            detail_id (int): The ID of the detail
            caller (Object): The caller requesting access
        """
        situation = Situation.objects.get(id=situation_id)
        if not situation:
            return False
            
        # Find the detail
        detail = None
        for d in situation.details.all():
            if d.id == detail_id:
                detail = d
                break
                
        if not detail:
            return False
            
        # If no roster restrictions on detail, check situation access
        if not detail.roster_names:
            return self.has_access(situation_id, caller)
            
        # Get the character if caller is an account
        character = caller
        if hasattr(caller, 'character'):
            character = caller.character
            
        if not character:
            return False
            
        # Admin and Builder override - they can see everything
        if character.check_permstring("Admin") or character.check_permstring("Builder"):
            return True
            
        # Check character's roster membership for detail
        for roster_name in detail.roster_names:
            try:
                roster = Roster.objects.get(name=roster_name)
                if RosterMember.objects.filter(
                    roster=roster,
                    character=character,
                    approved=True
                ).exists():
                    return True
            except Roster.DoesNotExist:
                continue
                
        return False
        
    def has_development_access(self, situation_id, development_id, caller):
        """
        Check if a caller has access to a development.
        
        Args:
            situation_id (int): The ID of the situation
            development_id (int): The ID of the development
            caller (Object): The caller requesting access
        """
        situation = Situation.objects.get(id=situation_id)
        if not situation:
            return False
            
        # Find the development
        development = None
        for d in situation.developments.all():
            if d.id == development_id:
                development = d
                break
                
        if not development:
            return False
            
        # If no roster restrictions on development, check situation access
        if not development.roster_names:
            return self.has_access(situation_id, caller)
            
        # Get the character if caller is an account
        character = caller
        if hasattr(caller, 'character'):
            character = caller.character
            
        if not character:
            return False
            
        # Admin and Builder override - they can see everything
        if character.check_permstring("Admin") or character.check_permstring("Builder"):
            return True
            
        # Check character's roster membership for development
        for roster_name in development.roster_names:
            try:
                roster = Roster.objects.get(name=roster_name)
                if RosterMember.objects.filter(
                    roster=roster,
                    character=character,
                    approved=True
                ).exists():
                    return True
            except Roster.DoesNotExist:
                continue
                
        return False
        
    def delete_situation(self, situation_id):
        """
        Delete a situation.
        
        Args:
            situation_id (int): The ID of the situation to delete
        """
        if Situation.objects.filter(id=situation_id).exists():
            Situation.objects.get(id=situation_id).delete()
            return f"Situation {situation_id} has been deleted."
        return f"No situation found with ID {situation_id}."
        
    def delete_detail(self, situation_id, detail_id):
        """
        Delete a detail from a situation.
        
        Args:
            situation_id (int): The ID of the situation
            detail_id (int): The ID of the detail to delete
        """
        situation = Situation.objects.get(id=situation_id)
        if not situation:
            return f"No situation found with ID {situation_id}"
            
        # Find and remove the detail
        for i, detail in enumerate(situation.details.all()):
            if detail.id == detail_id:
                detail.delete()
                return f"Detail {detail_id} has been deleted from situation {situation_id}."
                
        return f"No detail found with ID {detail_id} in situation {situation_id}."
        
    def delete_development(self, situation_id, development_id):
        """
        Delete a development from a situation.
        
        Args:
            situation_id (int): The ID of the situation
            development_id (int): The ID of the development to delete
        """
        situation = Situation.objects.get(id=situation_id)
        if not situation:
            return f"No situation found with ID {situation_id}"
            
        # Find and remove the development
        for i, development in enumerate(situation.developments.all()):
            if development.id == development_id:
                development.delete()
                return f"Development {development_id} has been deleted from situation {situation_id}."
                
        return f"No development found with ID {development_id} in situation {situation_id}."

    def modify_situation_rosters(self, situation_id, roster_names, add=True):
        """
        Add or remove rosters from a situation.
        
        Args:
            situation_id (int): The ID of the situation
            roster_names (list): List of roster names to add/remove
            add (bool): True to add rosters, False to remove them
        """
        situation = Situation.objects.get(id=situation_id)
        if not situation:
            return f"No situation found with ID {situation_id}"
            
        # Initialize roster_names if None
        if situation.roster_names is None:
            situation.roster_names = []
            
        # Verify all rosters exist before making changes
        final_roster_names = []
        for roster_ref in roster_names:
            try:
                if str(roster_ref).isdigit():
                    roster = Roster.objects.get(id=int(roster_ref))
                else:
                    roster = Roster.objects.get(name=roster_ref)
                final_roster_names.append(roster.name)
            except Roster.DoesNotExist:
                return f"Error: Roster '{roster_ref}' does not exist"
                
        if add:
            # Add rosters that aren't already in the list
            for roster in final_roster_names:
                if roster not in situation.roster_names:
                    situation.roster_names.append(roster)
            situation.save()
            return f"Added rosters to situation {situation_id}: {', '.join(final_roster_names)}"
        else:
            # Remove specified rosters
            for roster in final_roster_names:
                if roster in situation.roster_names:
                    situation.roster_names.remove(roster)
            situation.save()
            return f"Removed rosters from situation {situation_id}: {', '.join(final_roster_names)}"
            
    def modify_detail_rosters(self, situation_id, detail_id, roster_names, add=True):
        """
        Add or remove rosters from a detail.
        
        Args:
            situation_id (int): The ID of the situation
            detail_id (int): The ID of the detail
            roster_names (list): List of roster names to add/remove
            add (bool): True to add rosters, False to remove them
        """
        situation = Situation.objects.get(id=situation_id)
        if not situation:
            return f"No situation found with ID {situation_id}"
            
        # Find the detail
        detail = None
        for d in situation.details.all():
            if d.id == detail_id:
                detail = d
                break
                
        if not detail:
            return f"No detail found with ID {detail_id}"
            
        # Initialize roster_names if None
        if detail.roster_names is None:
            detail.roster_names = []
            
        # Verify all rosters exist and are valid for the situation
        final_roster_names = []
        for roster_ref in roster_names:
            try:
                if str(roster_ref).isdigit():
                    roster = Roster.objects.get(id=int(roster_ref))
                else:
                    roster = Roster.objects.get(name=roster_ref)
                # Check if roster is valid for the situation
                if situation.roster_names and roster.name not in situation.roster_names:
                    return f"Error: Roster '{roster.name}' does not have access to this situation"
                final_roster_names.append(roster.name)
            except Roster.DoesNotExist:
                return f"Error: Roster '{roster_ref}' does not exist"
                
        if add:
            # Add rosters that aren't already in the list
            for roster in final_roster_names:
                if roster not in detail.roster_names:
                    detail.roster_names.append(roster)
            detail.save()
            return f"Added rosters to detail {detail_id}: {', '.join(final_roster_names)}"
        else:
            # Remove specified rosters
            for roster in final_roster_names:
                if roster in detail.roster_names:
                    detail.roster_names.remove(roster)
            detail.save()
            return f"Removed rosters from detail {detail_id}: {', '.join(final_roster_names)}"
            
    def modify_development_rosters(self, situation_id, development_id, roster_names, add=True):
        """
        Add or remove rosters from a development.
        
        Args:
            situation_id (int): The ID of the situation
            development_id (int): The ID of the development
            roster_names (list): List of roster names to add/remove
            add (bool): True to add rosters, False to remove them
        """
        situation = Situation.objects.get(id=situation_id)
        if not situation:
            return f"No situation found with ID {situation_id}"
            
        # Find the development
        development = None
        for d in situation.developments.all():
            if d.id == development_id:
                development = d
                break
                
        if not development:
            return f"No development found with ID {development_id}"
            
        # Initialize roster_names if None
        if development.roster_names is None:
            development.roster_names = []
            
        # Verify all rosters exist and are valid for the situation
        final_roster_names = []
        for roster_ref in roster_names:
            try:
                if str(roster_ref).isdigit():
                    roster = Roster.objects.get(id=int(roster_ref))
                else:
                    roster = Roster.objects.get(name=roster_ref)
                # Check if roster is valid for the situation
                if situation.roster_names and roster.name not in situation.roster_names:
                    return f"Error: Roster '{roster.name}' does not have access to this situation"
                final_roster_names.append(roster.name)
            except Roster.DoesNotExist:
                return f"Error: Roster '{roster_ref}' does not exist"
                
        if add:
            # Add rosters that aren't already in the list
            for roster in final_roster_names:
                if roster not in development.roster_names:
                    development.roster_names.append(roster)
            development.save()
            return f"Added rosters to development {development_id}: {', '.join(final_roster_names)}"
        else:
            # Remove specified rosters
            for roster in final_roster_names:
                if roster in development.roster_names:
                    development.roster_names.remove(roster)
            development.save()
            return f"Removed rosters from development {development_id}: {', '.join(final_roster_names)}"

    def link_plot(self, situation_id, plot_id):
        """
        Link a plot to a situation.
        
        Args:
            situation_id (int): The ID of the situation
            plot_id (int): The ID of the plot to link
        """
        try:
            situation = Situation.objects.get(id=situation_id)
            Plot = class_from_module("world.plots.models.Plot")
            plot = Plot.objects.get(id=plot_id)
            situation.related_plots.add(plot)
            return f"Plot {plot_id} linked to situation {situation_id}"
        except Situation.DoesNotExist:
            return f"Situation {situation_id} not found"
        except Plot.DoesNotExist:
            return f"Plot {plot_id} not found"
        
    def unlink_plot(self, situation_id, plot_id):
        """
        Unlink a plot from a situation.
        
        Args:
            situation_id (int): The ID of the situation
            plot_id (int): The ID of the plot to unlink
        """
        try:
            situation = Situation.objects.get(id=situation_id)
            Plot = class_from_module("world.plots.models.Plot")
            plot = Plot.objects.get(id=plot_id)
            situation.related_plots.remove(plot)
            return f"Plot {plot_id} unlinked from situation {situation_id}"
        except Situation.DoesNotExist:
            return f"Situation {situation_id} not found"
        except Plot.DoesNotExist:
            return f"Plot {plot_id} not found"

    def set_staff_notes(self, situation_id, notes, detail_id=None, development_id=None):
        """Set staff notes for a situation, detail, or development."""
        try:
            situation = Situation.objects.get(id=situation_id)
            
            if detail_id is not None:
                detail = Detail.objects.get(id=detail_id, situation=situation)
                detail.staff_notes = notes
                detail.save()
                return f"Staff notes updated for detail {detail_id}"
                
            elif development_id is not None:
                development = Development.objects.get(id=development_id, situation=situation)
                development.staff_notes = notes
                development.save()
                return f"Staff notes updated for development {development_id}"
                
            else:
                situation.staff_notes = notes
                situation.save()
                return f"Staff notes updated for situation {situation_id}"
                
        except (Situation.DoesNotExist, Detail.DoesNotExist, Development.DoesNotExist):
            return f"Target not found"

def get_or_create_situation_controller():
    """Get or create the situation controller."""
    from evennia.objects.models import ObjectDB
    
    controller = ObjectDB.objects.filter(db_key="SituationController").first()
    if not controller:
        controller = create_object(
            "typeclasses.situation_controller.SituationController",
            key="SituationController"
        )
    return controller 