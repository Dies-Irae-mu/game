from evennia.commands.default.muxcommand import MuxCommand
from world.plots.models import Plot, Session, STATUS_CHOICES, RISK_LEVEL_CHOICES
from evennia.utils.utils import crop, list_to_string
from django.utils import timezone
from datetime import datetime, timedelta

class CmdPlots(MuxCommand):
    """
    View and manage plots and sessions

    Usage:
        +plots                          - List all active plots
        +plot/add <title>/<payout>/<risk>/<genre>=<desc>  
                                      - Add a new plot
        +plot/secret <#>=<text>        - Add secret info to a plot
        +plot/claim <#>                - Claim a plot to run
        +plot/assign <#>=<n>        - Assign a plot to someone
        +plot/return <#>               - Return a plot to the queue
        +plot/done <#>                 - Mark a plot as completed
        +plot/view <#>                 - View detailed plot information

    Session Management:
        +plot/sessions <#>             - List all sessions for a plot
        +plot/session/add <#>/<date>/<time>/<duration>/<location>=<desc>
                                      - Add a new session to a plot
        +plot/session/secret <#>/<session#>=<text>
                                      - Add secret info to a session
        +plot/session/addplayer <#>/<session#>=<n>
                                      - Add a player to a session
        +plot/session/remplayer <#>/<session#>=<n>
                                      - Remove a player from a session
        +plot/session/edit <#>/<session#>/<field>=<value>
                                      - Edit session details
                                      - Fields: date, time, duration, location, description

    Example:
        +plot/session/add 1/2025-01-19/19:00/2 hours/The docks=Players intercept the shipment
        +plot/session/edit 1/1/location=The Warehouse
    """

    key = "+plots"
    aliases = ["+plot"]
    locks = "cmd:all()"
    help_category = "Staff"

    def parse(self):
        """Custom parsing for session commands"""
        # Store the original command before parsing
        raw_cmd = self.raw_string
        
        # Call parent's parse method first
        super().parse()
        
        # Handle session commands specially
        if self.switches:
            # Check for session/add pattern
            if "session/add" in raw_cmd or "session/secret" in raw_cmd or \
               "session/addplayer" in raw_cmd or "session/remplayer" in raw_cmd or \
               "session/edit" in raw_cmd:
                # Extract the command after session/
                cmd_parts = raw_cmd.split('/')
                for i, part in enumerate(cmd_parts):
                    if "session" in part:
                        if i + 1 < len(cmd_parts):
                            subcmd = cmd_parts[i+1].split()[0]  # Get the part after session/ up to first space
                            self.switches = [f"session/{subcmd}"]
                        break

    def list_plots(self):
        """Display all active plots"""
        plots = Plot.objects.exclude(status__in=['COMPLETED', 'CANCELLED']).order_by('-date_created')
        if not plots:
            self.caller.msg("No active plots found.")
            return
        
        header = "|b=|n" * 78
        self.caller.msg(header)
        self.caller.msg(f"{' ' * 26}|yDies Irae Plots|n")
        self.caller.msg(header)
        
        # Column widths
        col_widths = {
            'plot': 10,    # Plot #
            'genre': 10,   # Genre
            'title': 12,   # Title
            'started': 12, # Started
            'assignee': 12,# Assignee
            'status': 8    # Status
        }
        
        # Header row with fixed column widths
        header_row = "  "
        header_row += "Plot #".ljust(col_widths['plot'])
        header_row += "Genre".ljust(col_widths['genre'])
        header_row += "Title".ljust(col_widths['title'])
        header_row += "Started".ljust(col_widths['started'])
        header_row += "Assignee".ljust(col_widths['assignee'])
        header_row += "Status".ljust(col_widths['status'])
        self.caller.msg(f"|w{header_row}|n")
        
        # Data rows
        for plot in plots:
            row = "  "  # 2-space indent
            row += str(plot.id).ljust(col_widths['plot'])
            row += crop(plot.genre, col_widths['genre']-1).ljust(col_widths['genre'])
            row += crop(plot.title, col_widths['title']-1).ljust(col_widths['title'])
            row += plot.date_created.strftime("%m/%d/%y").ljust(col_widths['started'])
            row += (plot.storyteller.username if plot.storyteller else "-----").ljust(col_widths['assignee'])
            row += ("claimed" if plot.claimed else "open").ljust(col_widths['status'])
            self.caller.msg(row)
        
        self.caller.msg("")  # Empty line
        self.caller.msg(header)

    def add_plot(self):
        """Add a new plot"""
        if not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to add plots.")
            return

        if not self.args or len(self.lhs.split("/")) != 4:
            self.caller.msg("Usage: +plot/add <title>/<payout>/<risk>/<genre>=<description>")
            return

        title, payout, risk, genre = self.lhs.split("/")
        description = self.rhs

        if risk.upper() not in [choice[0] for choice in RISK_LEVEL_CHOICES]:
            self.caller.msg(f"Invalid risk level. Choose from: {', '.join([choice[0] for choice in RISK_LEVEL_CHOICES])}")
            return

        plot = Plot.objects.create(
            title=title,
            payout=payout,
            risk_level=risk.upper(),
            genre=genre,
            description=description
        )
        self.caller.msg(f"Created plot '{title}' with ID {plot.id}")

    def claim_plot(self):
        """Claim a plot"""
        if not self.args:
            self.caller.msg("Usage: +plot/claim <#>")
            return

        try:
            plot = Plot.objects.get(id=self.args)
        except Plot.DoesNotExist:
            self.caller.msg("That plot doesn't exist.")
            return

        if plot.claimed:
            self.caller.msg("This plot has already been claimed.")
            return

        plot.claimed = True
        plot.storyteller = self.caller.account
        plot.status = 'ACTIVE'
        plot.save()
        self.caller.msg(f"You have claimed plot {plot.id}: {plot.title}")

    def assign_plot(self):
        """Assign a plot to someone"""
        if not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to assign plots.")
            return

        if not self.args or not self.rhs:
            self.caller.msg("Usage: +plot/assign <#>=<character>")
            return

        try:
            plot = Plot.objects.get(id=self.lhs)
        except Plot.DoesNotExist:
            self.caller.msg("That plot doesn't exist.")
            return

        # Find the account by username
        from evennia.accounts.models import AccountDB
        target = AccountDB.objects.filter(username__iexact=self.rhs).first()
        if not target:
            self.caller.msg(f"Could not find an account named '{self.rhs}'.")
            return

        plot.claimed = True
        plot.storyteller = target
        plot.status = 'ACTIVE'
        plot.save()
        self.caller.msg(f"Assigned plot {plot.id} to {target.username}")

    def view_plot(self):
        """View detailed plot information"""
        if not self.args:
            self.caller.msg("Usage: +plot/view <#>")
            return

        try:
            plot = Plot.objects.get(id=self.args)
        except Plot.DoesNotExist:
            self.caller.msg("That plot doesn't exist.")
            return

        self.caller.msg("|b=================================>|n |yPlot Info|n |b<==================================|n")
        self.caller.msg(f"|wPlot #:|n               {plot.id}")
        self.caller.msg(f"|wTitle:|n               {plot.title}")
        self.caller.msg(f"|wGenre:|n               {plot.genre}")
        self.caller.msg(f"|wRisk Level:|n          {plot.risk_level}")
        self.caller.msg(f"|wPayout:|n              {plot.payout}")
        self.caller.msg(f"|wStarted:|n             {plot.date_created.strftime('%m/%d/%y')}")
        self.caller.msg(f"|wStoryteller:|n         {plot.storyteller.username if plot.storyteller else '-----'}")
        self.caller.msg(f"|wStatus:|n              {'claimed' if plot.claimed else 'open'}")
        
        self.caller.msg("|b=================================>|n |yDescription|n |b<==================================|n")
        self.caller.msg(plot.description)
        
        # Add sessions summary
        sessions = Session.objects.filter(plot=plot).order_by('date')
        if sessions:
            self.caller.msg("|b=================================>|n |ySessions|n |b<=====================================|n")
            for session in sessions:
                date = session.date.strftime('%Y-%m-%d')
                time = session.date.strftime('%H:%M')
                self.caller.msg(f"Session {session.id}: Date {date}, {time}; Duration {session.duration}; Location {session.location}")
        
        self.caller.msg("|b======================================================================================|n")

    def return_plot(self):
        """Return a plot to the queue"""
        if not self.args:
            self.caller.msg("Usage: +plot/return <#>")
            return

        try:
            plot = Plot.objects.get(id=self.args)
        except Plot.DoesNotExist:
            self.caller.msg("That plot doesn't exist.")
            return

        if not plot.claimed:
            self.caller.msg("This plot isn't claimed.")
            return

        if plot.storyteller != self.caller.account and not self.caller.check_permstring("builders"):
            self.caller.msg("You can only return plots you've claimed.")
            return

        plot.claimed = False
        plot.storyteller = None
        plot.status = 'NEW'
        plot.save()
        self.caller.msg(f"You have returned plot {plot.id} to the queue.")

    def done_plot(self):
        """Mark a plot as completed"""
        if not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to complete plots.")
            return

        if not self.args:
            self.caller.msg("Usage: +plot/done <#>")
            return

        try:
            plot = Plot.objects.get(id=self.args)
        except Plot.DoesNotExist:
            self.caller.msg("That plot doesn't exist.")
            return

        plot.status = 'COMPLETED'
        plot.save()
        self.caller.msg(f"Marked plot {plot.id} as completed.")

    def add_secret(self):
        """Add secret information to a plot"""
        if not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to add secret information.")
            return

        if not self.args or not self.rhs:
            self.caller.msg("Usage: +plot/secret <#>=<text>")
            return

        try:
            plot = Plot.objects.get(id=self.lhs)
        except Plot.DoesNotExist:
            self.caller.msg("That plot doesn't exist.")
            return

        # Add secret information to the plot's description
        plot.description += f"\n\nSECRET: {self.rhs}"
        plot.save()
        self.caller.msg(f"Added secret information to plot {plot.id}")

    def list_sessions(self):
        """List all sessions for a plot"""
        if not self.args:
            self.caller.msg("Usage: +plot/sessions <plot #>")
            return

        try:
            plot = Plot.objects.get(id=self.args)
        except Plot.DoesNotExist:
            self.caller.msg("That plot doesn't exist.")
            return

        sessions = Session.objects.filter(plot=plot).order_by('date')
        if not sessions:
            self.caller.msg(f"No sessions scheduled for plot {plot.id}: {plot.title}")
            return

        for session in sessions:
            participants = ", ".join([char.key for char in session.participants.all()])
            self.caller.msg(f"|b=================================>|n |ySession Info|n |b<=================================|n")
            self.caller.msg(f"|wSession:|n             {session.id}")
            self.caller.msg(f"|wDate:|n                {session.date.strftime('%Y-%m-%d')}")
            self.caller.msg(f"|wTime:|n                {session.date.strftime('%H:%M')}")
            self.caller.msg(f"|wDuration:|n            {session.duration}")
            self.caller.msg(f"|wLocation:|n            {session.location}")
            self.caller.msg(f"|wParticipants:|n        {participants}")
            self.caller.msg(f"|b=================================>|n |yDescription|n |b<==================================|n")
            self.caller.msg(f"{session.description}")
            if self.caller.check_permstring("builders") or plot.storyteller == self.caller.account:
                self.caller.msg(f"|b====================================>|n |ySecrets|n |b<===================================|n")
                self.caller.msg(f"{session.secrets}")
                self.caller.msg(f"|b==================================================================================|n")

    def handle_session_command(self, switch):
        """Handle session-related commands"""
        if switch == "add":
            self.add_session()
        elif switch == "secret":
            self.add_session_secret()
        elif switch == "addplayer":
            self.add_session_player()
        elif switch == "remplayer":
            self.remove_session_player()
        elif switch == "edit":
            self.edit_session()
        else:
            self.caller.msg(f"Unknown session command: {switch}")

    def add_session(self):
        """Add a new session to a plot"""
        if not self.args or not self.rhs:
            self.caller.msg("Usage: +plot/session/add <plot #>/<date>/<time>/<duration>/<location>=<description>")
            return

        try:
            plot_id = self.lhs.split('/')[0]
            plot = Plot.objects.get(id=plot_id)
        except (IndexError, Plot.DoesNotExist):
            self.caller.msg("That plot doesn't exist.")
            return

        if plot.storyteller != self.caller.account and not self.caller.check_permstring("builders"):
            self.caller.msg("You can only add sessions to plots you're running.")
            return

        try:
            _, date_str, time_str, duration_str, location = self.lhs.split('/')
            date_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            # Parse duration string (e.g., "2 hours" -> timedelta)
            duration_val = int(duration_str.split()[0])
            duration = timedelta(hours=duration_val)
        except ValueError:
            self.caller.msg("Invalid date/time format. Use: YYYY-MM-DD/HH:MM/X hours/location")
            return

        session = Session.objects.create(
            plot=plot,
            date=date_time,
            duration=duration,
            location=location,
            description=self.rhs,
            secrets=""
        )
        self.caller.msg(f"Added session {session.id} to plot {plot.id}")

    def add_session_secret(self):
        """Add secret information to a session"""
        if not self.args or not self.rhs:
            self.caller.msg("Usage: +plot/session/secret <plot #>/<session #>=<text>")
            return

        try:
            plot_id, session_id = self.lhs.split('/')
            plot = Plot.objects.get(id=plot_id)
            session = Session.objects.get(id=session_id, plot=plot)
        except (ValueError, Plot.DoesNotExist, Session.DoesNotExist):
            self.caller.msg("Invalid plot or session number.")
            return

        if plot.storyteller != self.caller.account and not self.caller.check_permstring("builders"):
            self.caller.msg("You can only add secrets to sessions for plots you're running.")
            return

        session.secrets = self.rhs
        session.save()
        self.caller.msg(f"Added secret information to session {session.id}")

    def add_session_player(self):
        """Add a player to a session"""
        if not self.args or not self.rhs:
            self.caller.msg("Usage: +plot/session/addplayer <plot #>/<session #>=<character name>")
            return

        try:
            plot_id, session_id = self.lhs.split('/')
            plot = Plot.objects.get(id=plot_id)
            session = Session.objects.get(id=session_id, plot=plot)
        except (ValueError, Plot.DoesNotExist, Session.DoesNotExist):
            self.caller.msg("Invalid plot or session number.")
            return

        if plot.storyteller != self.caller.account and not self.caller.check_permstring("builders"):
            self.caller.msg("You can only add players to sessions for plots you're running.")
            return

        # Find character by name
        char = self.caller.search(self.rhs)
        if not char:
            return

        session.participants.add(char)
        self.caller.msg(f"Added {char.key} to session {session.id}")

    def remove_session_player(self):
        """Remove a player from a session"""
        if not self.args or not self.rhs:
            self.caller.msg("Usage: +plot/session/remplayer <plot #>/<session #>=<character name>")
            return

        try:
            plot_id, session_id = self.lhs.split('/')
            plot = Plot.objects.get(id=plot_id)
            session = Session.objects.get(id=session_id, plot=plot)
        except (ValueError, Plot.DoesNotExist, Session.DoesNotExist):
            self.caller.msg("Invalid plot or session number.")
            return

        if plot.storyteller != self.caller.account and not self.caller.check_permstring("builders"):
            self.caller.msg("You can only remove players from sessions for plots you're running.")
            return

        # Find character by name
        char = self.caller.search(self.rhs)
        if not char:
            return

        if char not in session.participants.all():
            self.caller.msg(f"{char.key} is not in this session.")
            return

        session.participants.remove(char)
        self.caller.msg(f"Removed {char.key} from session {session.id}")

    def edit_session(self):
        """Edit session details"""
        if not self.args or not self.rhs:
            self.caller.msg("Usage: +plot/session/edit <plot #>/<session #>/<field>=<value>")
            return

        try:
            plot_id, session_id, field = self.lhs.split('/')
            plot = Plot.objects.get(id=plot_id)
            session = Session.objects.get(id=session_id, plot=plot)
        except (ValueError, Plot.DoesNotExist, Session.DoesNotExist):
            self.caller.msg("Invalid plot or session number.")
            return

        if plot.storyteller != self.caller.account and not self.caller.check_permstring("builders"):
            self.caller.msg("You can only edit sessions for plots you're running.")
            return

        field = field.lower()
        if field in ['date', 'time']:
            try:
                if field == 'date':
                    new_date = datetime.strptime(self.rhs, "%Y-%m-%d")
                    session.date = session.date.replace(
                        year=new_date.year,
                        month=new_date.month,
                        day=new_date.day
                    )
                else:  # time
                    new_time = datetime.strptime(self.rhs, "%H:%M")
                    session.date = session.date.replace(
                        hour=new_time.hour,
                        minute=new_time.minute
                    )
            except ValueError:
                self.caller.msg("Invalid date/time format. Use YYYY-MM-DD for date or HH:MM for time.")
                return
        elif field == 'duration':
            try:
                duration_val = int(self.rhs.split()[0])
                session.duration = timedelta(hours=duration_val)
            except ValueError:
                self.caller.msg("Invalid duration format. Use: X hours")
                return
        elif field == 'location':
            session.location = self.rhs
        elif field == 'description':
            session.description = self.rhs
        else:
            self.caller.msg("Invalid field. Choose from: date, time, duration, location, description")
            return

        session.save()
        self.caller.msg(f"Updated {field} for session {session.id}")

    def func(self):
        """Main function for plot commands"""
        # Check permissions first
        if not (self.caller.check_permstring("builders") or self.caller.check_permstring("storyteller")):
            self.caller.msg("You must be staff or have storyteller permissions to use this command.")
            return

        if not self.args and not self.switches:
            self.list_plots()
            return

        # If we have args but no switches, treat it as a view command
        if not self.switches and self.args:
            self.view_plot()
            return

        switch = self.switches[0].lower()  # Convert to lowercase for consistent matching

        if switch == "add":
            self.add_plot()
        elif switch == "claim":
            self.claim_plot()
        elif switch == "assign":
            self.assign_plot()
        elif switch == "return":
            self.return_plot()
        elif switch == "done":
            self.done_plot()
        elif switch == "view":
            self.view_plot()
        elif switch == "secret":
            self.add_secret()
        elif switch == "sessions":
            self.list_sessions()
        elif switch == "session/add":
            self.add_session()
        elif switch == "session/secret":
            self.add_session_secret()
        elif switch == "session/addplayer":
            self.add_session_player()
        elif switch == "session/remplayer":
            self.remove_session_player()
        elif switch == "session/edit":
            self.edit_session()
        else:
            self.caller.msg(f"Unknown switch: {switch}") 