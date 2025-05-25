from evennia import Command
from evennia.utils import logger
from world.wod20th.events import get_or_create_event_scheduler
from world.wod20th.utils.bbs_utils import get_or_create_bbs_controller
from datetime import datetime, timezone, timedelta
from evennia import default_cmds
from evennia.utils.evtable import EvTable
from evennia.utils.ansi import ANSIString
import pytz
from world.wod20th.utils.time_utils import TIME_MANAGER

# For plot integration
from world.plots.models import Plot, Session
from django.db.models import Q

class CmdEvents(default_cmds.MuxCommand):
    """
    Manage events in the game.

    Usage:
      +events
      +events <event_id>
      +events/create <title> = <description>/<date_time>/<genre>/<difficulty>
                 - Genre and difficulty are optional.
      +events/edit <event_id> = <title>/<description>/<date_time>/<genre>/<difficulty>
                 - Genre and difficulty are optional.
      +events/join <event_id>
      +events/leave <event_id>
      +events/start <event_id>
      +events/complete <event_id>
      +events/cancel <event_id>
      +events/plot <event_id>          - View plot information if the event is associated with a plot

    Switches:
      create - Create a new event
      edit - Edit an existing event (organizers only)
      join - Join an event
      leave - Leave an event
      start - Start an event (organizers only)
      complete - Complete an event (organizers only)
      cancel - Cancel an event (organizers only)
      plot - View associated plot information

    The date_time should be in the format YYYY-MM-DD HH:MM:SS.
    Events will automatically expire two days after the scheduled date.
    """
    key = "+events"
    aliases = ["+event"]
    locks = "cmd:all()"
    help_category = "Event & Bulletin Board"

    def func(self):
        if not self.args and not self.switches:
            self.list_events()
            return

        if self.args and not self.switches:
            # Check if the argument is a number (event ID)
            try:
                event_id = int(self.args)
                self.event_info(event_id)
                return
            except ValueError:
                self.caller.msg("Invalid event ID. Please use a number.")
                return

        if "create" in self.switches:
            self.create_event()
        elif "edit" in self.switches:
            self.edit_event()
        elif "join" in self.switches:
            self.join_event()
        elif "leave" in self.switches:
            self.leave_event()
        elif "start" in self.switches:
            self.start_event()
        elif "complete" in self.switches:
            self.complete_event()
        elif "cancel" in self.switches:
            self.cancel_event()
        elif "plot" in self.switches:
            self.view_plot_info()
        else:
            self.caller.msg("Invalid switch. Use 'help events' for usage information.")

    def get_or_create_events_board(self):
        bbs_controller = get_or_create_bbs_controller()
        events_board = bbs_controller.get_board("Events")
        if not events_board:
            events_board = bbs_controller.create_board("Events", "A board for game events", public=True)
        return events_board

    def format_datetime(self, dt, target_char=None):
        """Format datetime in the user's timezone."""
        if not target_char:
            target_char = self.caller
            
        # Get the caller's timezone
        tz_name = target_char.attributes.get("timezone", "UTC")
        try:
            # Try to get the timezone from pytz
            tz = pytz.timezone(TIME_MANAGER.normalize_timezone_name(tz_name))
            # Convert to the caller's timezone
            local_dt = dt.astimezone(tz)
            # Format without timezone indicator
            return local_dt.strftime("%Y-%m-%d %H:%M")
        except (pytz.exceptions.UnknownTimeZoneError, AttributeError, ValueError):
            # Fallback to UTC if there's any error
            return dt.strftime("%Y-%m-%d %H:%M")

    def post_event_to_bbs(self, event, action):
        events_board = self.get_or_create_events_board()
        title = f"{action.capitalize()}: {event.db.title}"
        content = f"Event: {event.db.title}\n"
        content += f"Date/Time: {self.format_datetime(event.db.date_time)}\n"
        content += f"Genre: {event.db.genre if event.db.genre else 'None'}\n"
        content += f"Difficulty: {event.db.difficulty if event.db.difficulty else 'None'}\n"
        content += f"Status: {event.db.status}\n"
        content += f"Participants: {', '.join([str(p) for p in event.db.participants])}\n"        
        content += f"Organizer: {event.db.organizer}\n\n"
        content += f"Description: {event.db.description}\n"
        
        bbs_controller = get_or_create_bbs_controller()
        bbs_controller.create_post("Events", title, content, self.caller.key)

    def list_events(self):
        event_scheduler = get_or_create_event_scheduler()
        if not event_scheduler:
            self.caller.msg("Error: Unable to access the event system. Please contact an admin.")
            return

        events = event_scheduler.get_upcoming_events()
        completed_events = event_scheduler.get_recent_completed_events()
        
        events = events + completed_events
        
        if not events:
            self.caller.msg("There are no upcoming or recent events.")
            return

        # Calculate a header width that will work for most terminal widths
        header_width = 76  # Standard width that should fit on most terminals
        
        header = ANSIString(f"|r======< |wDies Irae Events |r>{'=' * (header_width - 24)}|n")
        divider = ANSIString(f"|r{'-' * header_width}|n")
        
        # Create table with appropriate widths
        table = EvTable("ID", "Title", "Date/Time", "Status", "Genre", 
                        border="none", pad_right=1)
        table.reformat_column(0, width=5, align="l")
        table.reformat_column(1, width=30, align="l") 
        table.reformat_column(2, width=18, align="l")
        table.reformat_column(3, width=12, align="l")
        table.reformat_column(4, width=10, align="l")

        self.caller.msg(header)
        self.caller.msg(divider)
        
        for event in events:
            # Check if this event is associated with a plot
            plot_session = self.get_associated_plot_session(event.id)
            title = event.db.title
            
            # Truncate title if necessary and add plot indicator
            if len(title) > 26 and plot_session:
                title = f"{title[:26]}.. [P#{plot_session.plot.id}]"
            elif len(title) > 30:
                title = f"{title[:27]}.."
            elif plot_session:
                title = f"{title} [P#{plot_session.plot.id}]"
            
            table.add_row(
                event.id,
                title,
                self.format_datetime(event.db.date_time),
                event.db.status,
                event.db.genre or "None"
            )

        self.caller.msg(table)
        self.caller.msg(divider)

    def create_event(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: events/create <title> = <description>/<date_time>/[<genre>/<difficulty>]")
            return

        title, args = self.args.split("=", 1)
        title = title.strip()
        args = args.strip().split("/")

        if len(args) < 2:
            self.caller.msg("You must provide a description and date_time.")
            return

        description = args[0].strip()
        date_time_str = args[1].strip()
        
        # Handle optional genre and difficulty parameters
        genre = None
        difficulty = None
        
        if len(args) >= 3:
            genre = args[2].strip() if args[2].strip() else None
            
        if len(args) >= 4:
            difficulty = args[3].strip() if args[3].strip() else None
            

        try:
            date_time = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
            date_time = date_time.replace(tzinfo=timezone.utc)  # Ensure the datetime is in UTC
        except ValueError:
            self.caller.msg("Invalid date/time format. Use YYYY-MM-DD HH:MM:SS.")
            return

        event_scheduler = get_or_create_event_scheduler()
        if not event_scheduler:
            self.caller.msg("Error: Unable to access the event scheduler. Please contact an admin.")
            return

        # Calculate expiration date (2 days after the event)
        expiration_date = date_time + timedelta(days=2)

        new_event = event_scheduler.create_event(
            title, 
            description, 
            self.caller, 
            date_time, 
            genre=genre,
            difficulty=difficulty,
            expiration_date=expiration_date
        )
        
        if new_event:
            self.caller.msg(f"Created new event: {new_event.db.title}")
            self.post_event_to_bbs(new_event, "created")
        else:
            self.caller.msg("Failed to create the event. Please try again or contact an admin.")

    def edit_event(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: events/edit <event_id> = <title>/<description>/<date_time>/[<genre>/<difficulty>]")
            return

        try:
            event_id, args = self.args.split("=", 1)
            event_id = int(event_id.strip())
            args = args.strip().split("/")
        except ValueError:
            self.caller.msg("Invalid format. Use: events/edit <event_id> = <title>/<description>/<date_time>/[<genre>/<difficulty>]")
            return

        if len(args) < 3:
            self.caller.msg("You must provide a title, description, and date_time.")
            return

        event_scheduler = get_or_create_event_scheduler()
        if not event_scheduler:
            self.caller.msg("Error: Unable to access the event system. Please contact an admin.")
            return

        event = event_scheduler.get_event_by_id(event_id)

        if not event:
            self.caller.msg(f"Event with ID {event_id} not found.")
            return

        if event.db.organizer != self.caller and not self.caller.check_permstring("Builders"):
            self.caller.msg("You don't have permission to edit this event. Only the organizer or staff can edit it.")
            return

        # Update event details
        title = args[0].strip()
        description = args[1].strip()
        date_time_str = args[2].strip()
        
        # Update genre and difficulty if provided
        if len(args) >= 4:
            genre = args[3].strip() if args[3].strip() else None
            event.db.genre = genre
            
        if len(args) >= 5:
            difficulty = args[4].strip() if args[4].strip() else None
            event.db.difficulty = difficulty
        
        try:
            date_time = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
            date_time = date_time.replace(tzinfo=timezone.utc)  # Ensure the datetime is in UTC
            
            # Update expiration date (2 days after the event)
            expiration_date = date_time + timedelta(days=2)
        except ValueError:
            self.caller.msg("Invalid date/time format. Use YYYY-MM-DD HH:MM:SS.")
            return

        event.db.title = title
        event.db.description = description
        event.db.date_time = date_time
        event.db.expiration_date = expiration_date
        event.save()
        
        self.caller.msg(f"Event '{event.db.title}' has been updated.")
        self.post_event_to_bbs(event, "updated")

    def event_info(self, event_id):
        event_scheduler = get_or_create_event_scheduler()
        if not event_scheduler:
            self.caller.msg("Error: Unable to access the event system. Please contact an admin.")
            return

        event = event_scheduler.get_event_by_id(event_id)

        if not event:
            self.caller.msg(f"Event with ID {event_id} not found.")
            return

        # Use the same header width calculation as in list_events
        header_width = 76
        header = ANSIString(f"|r======< |wDies Irae Events |r>{'=' * (header_width - 24)}|n")
        divider = ANSIString(f"|r{'-' * header_width}|n")

        self.caller.msg(header)
        self.caller.msg(divider)

        # Basic event info
        info = "|wEvent Information:|n\n"
        info += f"|wTitle:|n {event.db.title}\n"
        info += f"|wOrganizer:|n {event.db.organizer}\n"
        info += f"|wDate/Time:|n {self.format_datetime(event.db.date_time)}\n"
        info += f"|wStatus:|n {event.db.status}\n"
        info += f"|wParticipants:|n {', '.join([str(p) for p in event.db.participants]) if event.db.participants else 'None'}\n"
        
        # Check if this event is associated with a plot session
        plot_session = self.get_associated_plot_session(event_id)
        if plot_session:
            info += f"|wAssociated Plot:|n {plot_session.plot.title} (Plot #{plot_session.plot.id})\n"
            info += f"|wSession:|n {plot_session.id}\n"
            
        # Add genre, difficulty and expiration info
        if event.db.genre:
            info += f"|wGenre:|n {event.db.genre}\n"
        if event.db.difficulty:
            info += f"|wDifficulty:|n {event.db.difficulty}\n"
        if hasattr(event.db, 'expiration_date') and event.db.expiration_date:
            info += f"|wExpires:|n {self.format_datetime(event.db.expiration_date)}\n"
            
        self.caller.msg(info)
        
        # Display description in its own section with dividers
        self.caller.msg(divider)
        self.caller.msg("|wDescription:|n")
        self.caller.msg(event.db.description)
        self.caller.msg(divider)

    def join_event(self):
        if not self.args:
            self.caller.msg("Usage: events/join <event_id>")
            return

        try:
            event_id = int(self.args)
        except ValueError:
            self.caller.msg("Invalid event ID. Please use a number.")
            return

        event_scheduler = get_or_create_event_scheduler()
        if not event_scheduler:
            self.caller.msg("Error: Unable to access the event system. Please contact an admin.")
            return

        success = event_scheduler.join_event(event_id, self.caller)

        if success:
            self.caller.msg(f"You have joined the event with ID {event_id}.")
        else:
            self.caller.msg(f"Unable to join the event with ID {event_id}. The event may not exist or you may already be a participant.")

    def leave_event(self):
        if not self.args:
            self.caller.msg("Usage: events/leave <event_id>")
            return

        try:
            event_id = int(self.args)
        except ValueError:
            self.caller.msg("Invalid event ID. Please use a number.")
            return

        event_scheduler = get_or_create_event_scheduler()
        if not event_scheduler:
            self.caller.msg("The event system is not available.")
            return

        event = event_scheduler.get_event_by_id(event_id)

        if not event:
            self.caller.msg(f"Event with ID {event_id} not found.")
            return

        if self.caller not in event.db.participants:
            self.caller.msg("You are not participating in this event.")
            return

        event.db.participants.remove(self.caller)
        self.caller.msg(f"You have left the event: {event.db.title}")

    def start_event(self):
        if not self.args:
            self.caller.msg("Usage: events/start <event_id>")
            return

        try:
            event_id = int(self.args)
        except ValueError:
            self.caller.msg("Invalid event ID. Please use a number.")
            return

        event_scheduler = get_or_create_event_scheduler()
        if not event_scheduler:
            self.caller.msg("The event system is not available.")
            return

        event = event_scheduler.get_event_by_id(event_id)

        if not event:
            self.caller.msg(f"Event with ID {event_id} not found.")
            return

        if event.db.organizer != self.caller and not self.caller.check_permstring("Builders"):
            self.caller.msg("You don't have permission to start this event. Only the organizer or staff can start it.")
            return

        event.start_event()
        self.caller.msg(f"Event '{event.db.title}' has been started.")

    def complete_event(self):
        if not self.args:
            self.caller.msg("Usage: events/complete <event_id>")
            return

        try:
            event_id = int(self.args)
        except ValueError:
            self.caller.msg("Invalid event ID. Please use a number.")
            return

        event_scheduler = get_or_create_event_scheduler()
        if not event_scheduler:
            self.caller.msg("The event system is not available.")
            return

        event = event_scheduler.get_event_by_id(event_id)

        if not event:
            self.caller.msg(f"Event with ID {event_id} not found.")
            return

        if event.db.organizer != self.caller and not self.caller.check_permstring("Builders"):
            self.caller.msg("You don't have permission to complete this event. Only the organizer or staff can complete it.")
            return

        event.complete_event()
        self.caller.msg(f"Event '{event.db.title}' has been marked as completed.")
        
    def cancel_event(self):
        if not self.args:
            self.caller.msg("Usage: events/cancel <event_id>")
            return

        try:
            event_id = int(self.args)
        except ValueError:
            self.caller.msg("Invalid event ID. Please use a number.")
            return

        event_scheduler = get_or_create_event_scheduler()
        if not event_scheduler:
            self.caller.msg("The event system is not available.")
            return

        event = event_scheduler.get_event_by_id(event_id)

        if not event:
            self.caller.msg(f"Event with ID {event_id} not found.")
            return

        if event.db.organizer != self.caller and not self.caller.check_permstring("Builders"):
            self.caller.msg("You don't have permission to cancel this event. Only the organizer or staff can cancel it.")
            return

        event.cancel_event()
        self.caller.msg(f"Event '{event.db.title}' has been cancelled.")
        self.post_event_to_bbs(event, "cancelled")

    def get_associated_plot_session(self, event_id):
        """
        Get the associated plot session for an event.
        """
        try:
            session = Session.objects.get(event_id=event_id)
            return session
        except Session.DoesNotExist:
            return None

    def view_plot_info(self):
        """View plot information for an event that's associated with a plot"""
        if not self.args:
            self.caller.msg("Usage: +events/plot <event_id>")
            return
            
        try:
            event_id = int(self.args)
        except ValueError:
            self.caller.msg("Invalid event ID. Please use a number.")
            return
            
        # Check if the event exists
        event_scheduler = get_or_create_event_scheduler()
        if not event_scheduler:
            self.caller.msg("Error: Unable to access the event system. Please contact an admin.")
            return
            
        event = event_scheduler.get_event_by_id(event_id)
        if not event:
            self.caller.msg(f"Event with ID {event_id} not found.")
            return
            
        # Check if this event is associated with a plot session
        plot_session = self.get_associated_plot_session(event_id)
        if not plot_session:
            self.caller.msg(f"Event with ID {event_id} is not associated with any plot.")
            return
            
        plot = plot_session.plot
        
        # Display plot information
        header = ANSIString("|r======< |wPlot Information |r>====================================================|n")
        divider = ANSIString("|r" + "-" * 78 + "|n")

        self.caller.msg(header)
        self.caller.msg(divider)
        
        info = f"|wPlot ID:|n {plot.id}\n"
        info += f"|wTitle:|n {plot.title}\n"
        info += f"|wGenre:|n {plot.genre}\n"
        info += f"|wRisk Level:|n {plot.risk_level}\n"
        info += f"|wPayout:|n {plot.payout}\n"
        info += f"|wStoryteller:|n {plot.storyteller.username if plot.storyteller else 'None'}\n"
        info += f"|wStatus:|n {plot.status}\n"
        
        self.caller.msg(info)
        self.caller.msg("|wDescription:|n")
        self.caller.msg(plot.description)
        
        # Show session information
        self.caller.msg(divider)
        self.caller.msg("|wAssociated Session:|n")
        info = f"|wSession ID:|n {plot_session.id}\n"
        info += f"|wDate/Time:|n {self.format_datetime(plot_session.date)}\n"
        info += f"|wDuration:|n {plot_session.duration}\n"
        info += f"|wLocation:|n {plot_session.location}\n"
        
        participants = ", ".join([char.key for char in plot_session.participants.all()])
        info += f"|wParticipants:|n {participants if participants else 'None'}\n"
        
        self.caller.msg(info)
        self.caller.msg("|wDescription:|n")
        self.caller.msg(plot_session.description)
        
        # Only show secrets to staff or the storyteller
        if self.caller.check_permstring("builders") or (plot.storyteller and self.caller.account == plot.storyteller):
            self.caller.msg(divider)
            self.caller.msg("|wSession Secrets:|n")
            self.caller.msg(plot_session.secrets if plot_session.secrets else "None")
        
        self.caller.msg(divider)
