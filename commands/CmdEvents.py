from evennia import Command
from evennia.utils import logger
from world.wod20th.events import get_or_create_event_scheduler
from world.wod20th.utils.bbs_utils import get_or_create_bbs_controller
from datetime import datetime, timezone
from evennia import default_cmds
from evennia.utils.evtable import EvTable
from evennia.utils.ansi import ANSIString
import pytz
from world.wod20th.utils.time_utils import TIME_MANAGER

class CmdEvents(default_cmds.MuxCommand):
    """
    Manage events in the game.

    Usage:
      +events
      +events <event_id>
      +events/create <title> = <description>/<date_time>
      +events/join <event_id>
      +events/leave <event_id>
      +events/start <event_id>
      +events/complete <event_id>

    Switches:
      create - Create a new event
      join - Join an event
      leave - Leave an event
      start - Start an event (organizers only)
      complete - Complete an event (organizers only)

    The date_time should be in the format YYYY-MM-DD HH:MM:SS.
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
        elif "join" in self.switches:
            self.join_event()
        elif "leave" in self.switches:
            self.leave_event()
        elif "start" in self.switches:
            self.start_event()
        elif "complete" in self.switches:
            self.complete_event()
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
        content += f"Organizer: {event.db.organizer}\n"
        content += f"Date/Time: {self.format_datetime(event.db.date_time)}\n"
        content += f"Status: {event.db.status}\n"
        content += f"Description: {event.db.description}\n"
        content += f"Participants: {', '.join([str(p) for p in event.db.participants])}\n"
        
        bbs_controller = get_or_create_bbs_controller()
        bbs_controller.create_post("Events", title, content, self.caller.key)

    def list_events(self):
        event_scheduler = get_or_create_event_scheduler()
        if not event_scheduler:
            self.caller.msg("Error: Unable to access the event system. Please contact an admin.")
            return

        events = event_scheduler.get_upcoming_events()
        if not events:
            self.caller.msg("There are no upcoming events.")
            return

        header = ANSIString("|r======< |wDies Irae Events |r>====================================================|n")
        table = EvTable("ID", "Title", "Date/Time", "Status", border="none")
        table.reformat_column(0, width=5, align="l")
        table.reformat_column(1, width=30, align="l")
        table.reformat_column(2, width=20, align="l")
        table.reformat_column(3, width=15, align="l")

        divider = ANSIString("|r" + "-" * 78 + "|n")

        self.caller.msg(header)
        self.caller.msg(divider)
        
        for event in events:
            table.add_row(
                event.id,
                event.db.title,
                self.format_datetime(event.db.date_time),
                event.db.status
            )

        self.caller.msg(table)
        self.caller.msg(divider)

    def create_event(self):
        if not self.caller.check_permstring("Builders"):
            self.caller.msg("You don't have permission to create events.")
            return

        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: events/create <title> = <description>/<date_time>")
            return

        title, args = self.args.split("=", 1)
        title = title.strip()
        args = args.strip().split("/")

        if len(args) < 2:
            self.caller.msg("You must provide a description and date_time.")
            return

        description = args[0].strip()
        date_time_str = args[1].strip()
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

        new_event = event_scheduler.create_event(title, description, self.caller, date_time)
        if new_event:
            self.caller.msg(f"Created new event: {new_event.db.title}")
            self.post_event_to_bbs(new_event, "created")
        else:
            self.caller.msg("Failed to create the event. Please try again or contact an admin.")

    def event_info(self, event_id):
        event_scheduler = get_or_create_event_scheduler()
        if not event_scheduler:
            self.caller.msg("Error: Unable to access the event system. Please contact an admin.")
            return

        event = event_scheduler.get_event_by_id(event_id)

        if not event:
            self.caller.msg(f"Event with ID {event_id} not found.")
            return

        header = ANSIString("|r======< |wDies Irae Events |r>====================================================|n")
        divider = ANSIString("|r" + "-" * 78 + "|n")

        self.caller.msg(header)
        self.caller.msg(divider)

        info = "|wEvent Information:|n\n"
        info += f"|wTitle:|n {event.db.title}\n"
        info += f"|wOrganizer:|n {event.db.organizer}\n"
        info += f"|wDate/Time:|n {self.format_datetime(event.db.date_time)}\n"
        info += f"|wStatus:|n {event.db.status}\n"
        info += f"|wDescription:|n {event.db.description}\n"
        info += f"|wParticipants:|n {', '.join([str(p) for p in event.db.participants]) if event.db.participants else 'None'}\n"

        self.caller.msg(info)
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

        if event.db.organizer != self.caller:
            self.caller.msg("You don't have permission to start this event. Only the organizer can start it.")
            return

        event.start_event()
        self.caller.msg(f"Event '{event.db.title}' has been started.")
        self.post_event_to_bbs(event, "started")

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

        if event.db.organizer != self.caller:
            self.caller.msg("You don't have permission to complete this event. Only the organizer can complete it.")
            return

        event.complete_event()
        self.caller.msg(f"Event '{event.db.title}' has been marked as completed.")
        self.post_event_to_bbs(event, "completed")
