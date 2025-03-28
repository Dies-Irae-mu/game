# in mygame/commands/request_commands.py

from evennia.utils.utils import crop
from world.requests.models import Request, Comment, ArchivedRequest
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.utils import crop
from world.wod20th.utils.ansi_utils import wrap_ansi
from world.wod20th.utils.formatting import header, footer, divider
from evennia.utils.ansi import ANSIString
from evennia.utils import create
from django.core.exceptions import ObjectDoesNotExist
from evennia.comms.models import ChannelDB

class CmdRequests(MuxCommand):
    """
    View and manage requests

    Usage:
      request
      request <#>
      request/create <category>/<title>=<text>
      request/comment <#>=<text>
      request/cancel <#>
      request/addplayer <#>=<player>
      request/archive [<#>]

    Staff-only commands:
      request/assign <#>=<staff>
      request/close <#>

    Switches:
      create - Create a new request
      comment - Add a comment to a request
      cancel - Cancel one of your requests (player-only)
      addplayer - Add another player to your request (player-only)
      assign - Assign a request to a staff member (staff-only)
      close - Close a request (staff-only)
      archive - View all archived requests or a specific archived request (staff-only)
    """
    key = "+request"
    aliases = ["+requests", "+myjob", "+myjobs"]
    help_category = "Utility Commands"

    def func(self):
        if not self.args and not self.switches:
            self.list_requests()
        elif self.args and not self.switches:
            self.view_request()
        elif "create" in self.switches:
            self.create_request()
        elif "comment" in self.switches:
            self.add_comment()
        elif "cancel" in self.switches:
            self.cancel_request()
        elif "addplayer" in self.switches:
            self.add_player()
        elif "assign" in self.switches:
            self.assign_request()
        elif "close" in self.switches:
            self.close_request()
        elif "archive" in self.switches:
            self.view_archived_request()
        else:
            self.caller.msg("Invalid switch. See help +request for usage.")

    def list_requests(self):
        if self.caller.check_permstring("Admin"):
            requests = Request.objects.filter(status__in=['NEW', 'OPEN']).order_by('-date_created')
        else:
            requests = Request.objects.filter(
                requester=self.caller.account,
                status__in=['NEW', 'OPEN']
            )

        if not requests:
            self.caller.msg("You have no open requests.")
            return

        output = header("Dies Irae Jobs", width=78, fillchar="|r-|n") + "\n"
        
        # Create the header row
        header_row = "|cReq #  Category   Request Title              Started  Handler           Status|n"
        output += header_row + "\n"
        output += ANSIString("|r" + "-" * 78 + "|n") + "\n"

        # Add each request as a row
        for req in requests:
            handler = req.handler.username if req.handler else "-----"
            row = (
                f"{req.id:<6}"
                f"{req.category:<11}"
                f"{crop(req.title, width=25):<25}"
                f"{req.date_created.strftime('%m/%d/%y'):<9}"
                f"{handler:<18}"
                f"{req.status}"
            )
            output += row + "\n"

        output += ANSIString("|r" + "-" * 78 + "|n") + "\n"
        output += divider("End Requests", width=78, fillchar="-", color="|r")
        self.caller.msg(output)

    def view_request(self):
        try:
            req_id = int(self.args)
            if self.caller.check_permstring("Admin"):
                request = Request.objects.get(id=req_id)
            else:
                request = Request.objects.get(id=req_id, requester=self.caller.account)
        except (ValueError, Request.DoesNotExist):
            self.caller.msg("Request not found.")
            return

        output = header(f"Job {request.id}", width=78, fillchar="|r-|n") + "\n"
        output += f"|cJob Title:|n {request.title}\n"
        output += f"|cCategory:|n {request.category:<15} |cStatus:|n {request.status}\n"
        output += f"|cCreated:|n {request.date_created.strftime('%a %b %d %H:%M:%S %Y'):<30} |cHandler:|n {request.handler.username if request.handler else '-----'}\n"
        output += f"|cAdditional Players:|n\n"
        output += divider("Request", width=78, fillchar="-", color="|r", text_color="|c") + "\n"
        output += wrap_ansi(request.text, width=76, left_padding=2) + "\n\n"

        comments = request.comments.all().order_by('date_posted')
        if comments:
            output += divider("Comments", width=78, fillchar="-", color="|r", text_color="|c") + "\n"
            for comment in comments:
                output += f"{comment.author.username} [{comment.date_posted.strftime('%m/%d/%Y %H:%M')}]:\n"
                output += wrap_ansi(comment.text, width=76, left_padding=2) + "\n"

        output += footer(width=78, fillchar="|r-|n")
        self.caller.msg(output)

    def create_request(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +request/create <category>/<title>=<text>")
            return

        category_title, text = self.args.split("=", 1)
        category, title = category_title.split("/", 1)

        category = category.upper().strip()
        title = title.strip()
        text = text.strip()

        if category not in dict(Request.CATEGORIES):
            self.caller.msg(f"Invalid category. Choose from: {', '.join(dict(Request.CATEGORIES).keys())}")
            return

        new_request = Request.objects.create(
            category=category,
            title=title,
            text=text,
            requester=self.caller.account,
            status='NEW'
        )

        self.caller.msg(f"Request #{new_request.id} created successfully.")

    def add_comment(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +request/comment <#>=<text>")
            return

        req_id, comment_text = self.args.split("=", 1)
        
        try:
            req_id = int(req_id)
            request = Request.objects.get(id=req_id, requester=self.caller.account)
        except (ValueError, Request.DoesNotExist):
            self.caller.msg("Request not found.")
            return

        Comment.objects.create(
            request=request,
            author=self.caller.account,
            text=comment_text.strip()
        )

        self.caller.msg(f"Comment added to request #{req_id}.")
        
        # Send mail notification and post to channel
        notification = f"{self.caller.name} commented on Request #{req_id}: {comment_text}"
        self.send_mail_notification(request, notification)
        self.post_to_requests_channel(self.caller.name, req_id)

    def cancel_request(self):
        try:
            req_id = int(self.args)
            request = Request.objects.get(id=req_id, requester=self.caller.account)
        except (ValueError, Request.DoesNotExist):
            self.caller.msg("Request not found.")
            return

        request.status = 'CLOSED'
        request.save()
        self.caller.msg(f"Request #{req_id} has been cancelled.")

    def add_player(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +request/addplayer <#>=<player>")
            return

        req_id, player_name = self.args.split("=", 1)
        
        try:
            req_id = int(req_id)
            request = Request.objects.get(id=req_id, requester=self.caller.account)
        except (ValueError, Request.DoesNotExist):
            self.caller.msg("Request not found.")
            return

        player = self.caller.search(player_name)
        if not player:
            return

        # Here you might want to add logic to associate the player with the request
        # For simplicity, we'll just add a comment
        Comment.objects.create(
            request=request,
            author=self.caller.account,
            text=f"Added player {player.name} to the request."
        )

        self.caller.msg(f"Player {player.name} added to request #{req_id}.")

        # Send mail notification and post to channel
        notification = f"{self.caller.name} added {player.name} to Request #{req_id}"
        self.send_mail_notification(request, notification)
        self.post_to_requests_channel(notification)

    def assign_request(self):
        if not self.caller.check_permstring("Admin"):
            self.caller.msg("You don't have permission to assign requests.")
            return

        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +request/assign <#>=<staff>")
            return

        req_id, staff_name = self.args.split("=", 1)
        
        try:
            req_id = int(req_id)
            request = Request.objects.get(id=req_id)
        except (ValueError, Request.DoesNotExist):
            self.caller.msg("Request not found.")
            return

        staff = self.caller.search(staff_name)
        if not staff:
            return

        request.handler = staff.account
        request.status = 'OPEN'
        request.save()

        Comment.objects.create(
            request=request,
            author=self.caller.account,
            text=f"Assigned to {staff.name}."
        )

        self.caller.msg(f"Request #{req_id} assigned to {staff.name}.")

    def close_request(self):
        if not self.caller.check_permstring("Admin"):
            self.caller.msg("You don't have permission to close requests.")
            return

        try:
            req_id = int(self.args)
            request = Request.objects.get(id=req_id)
        except (ValueError, Request.DoesNotExist):
            self.caller.msg("Request not found.")
            return

        # Archive the request
        try:
            archived_request = ArchivedRequest.objects.create(
                original_id=request.id,
                category=request.category,
                title=request.title,
                text=request.text,
                requester=request.requester,
                handler=request.handler,
                date_created=request.date_created,
                date_closed=request.date_modified,
                comments="\n\n".join([f"{c.author.username} [{c.date_posted}]: {c.text}" for c in request.comments.all()])
            )
            self.caller.msg(f"Debug: Archived request created with ID {archived_request.id}")
        except Exception as e:
            self.caller.msg(f"Error archiving request: {str(e)}")
            return

        request.status = 'CLOSED'
        request.save()

        Comment.objects.create(
            request=request,
            author=self.caller.account,
            text="Request closed and archived."
        )

        self.caller.msg(f"Request #{req_id} has been closed and archived.")

    def view_archived_request(self):
        if not self.caller.check_permstring("Admin"):
            self.caller.msg("You don't have permission to view archived requests.")
            return

        if not self.args:
            # Display all archived requests
            archived_requests = ArchivedRequest.objects.all().order_by('-date_closed')
            if not archived_requests:
                self.caller.msg("There are no archived requests.")
                return

            output = header("Archived Dies Irae Jobs", width=78, fillchar="|r-|n") + "\n"
            
            # Create the header row
            header_row = "|cReq #  Category   Request Title              Closed    Handler           Requester|n"
            output += header_row + "\n"
            output += ANSIString("|r" + "-" * 78 + "|n") + "\n"

            # Add each archived request as a row
            for req in archived_requests:
                handler = req.handler.username if req.handler else "-----"
                row = (
                    f"{req.original_id:<6}"
                    f"{req.category:<11}"
                    f"{crop(req.title, width=25):<25}"
                    f"{req.date_closed.strftime('%m/%d/%y'):<9}"
                    f"{handler:<18}"
                    f"{req.requester.username}"
                )
                output += row + "\n"

            output += ANSIString("|r" + "-" * 78 + "|n") + "\n"
            output += divider("End Archived Requests", width=78, fillchar="-", color="|r")
            self.caller.msg(output)
        else:
            # View a specific archived request
            try:
                req_id = int(self.args)
                self.caller.msg(f"Debug: Searching for archived request with original_id {req_id}")
                archived_request = ArchivedRequest.objects.get(original_id=req_id)
            except ValueError:
                self.caller.msg("Invalid request ID.")
                return
            except ObjectDoesNotExist:
                self.caller.msg(f"Archived request with original ID {req_id} not found.")
                return

            output = header(f"Archived Job {archived_request.original_id}", width=78, fillchar="|r-|n") + "\n"
            output += f"|cJob Title:|n {archived_request.title}\n"
            output += f"|cCategory:|n {archived_request.category:<15} |cStatus:|n Closed\n"
            output += f"|cCreated:|n {archived_request.date_created.strftime('%a %b %d %H:%M:%S %Y'):<30} |cClosed:|n {archived_request.date_closed.strftime('%a %b %d %H:%M:%S %Y')}\n"
            output += f"|cRequester:|n {archived_request.requester.username:<30} |cHandler:|n {archived_request.handler.username if archived_request.handler else '-----'}\n"
            output += divider("Request", width=78, fillchar="-", color="|r", text_color="|c") + "\n"
            output += wrap_ansi(archived_request.text, width=76, left_padding=2) + "\n\n"

            if archived_request.comments:
                output += divider("Comments", width=78, fillchar="-", color="|r", text_color="|c") + "\n"
                output += wrap_ansi(archived_request.comments, width=76, left_padding=2) + "\n"

            output += footer(width=78, fillchar="|r-|n")
            self.caller.msg(output)

    def send_mail_notification(self, request, message):
        """Send a mail notification to relevant players."""
        recipients = set([request.requester] + list(request.additional_players.all()))
        recipients.discard(self.caller.account)  # Remove the sender from recipients

        if recipients:
            subject = f"New activity on Request #{request.id}"
            mail_body = f"Request #{request.id}: {request.title}\n\n{message}"
            recipient_names = ','.join(recipient.username for recipient in recipients)
            
            self.caller.execute_cmd(f"@mail {recipient_names}={subject}/{mail_body}")
            self.caller.msg("Notification sent to relevant players.")
        else:
            self.caller.msg("No other players to notify.")

    def post_to_requests_channel(self, player_name, request_id, action="commented on"):
        """Post a message to the Requests channel."""
        channel = ChannelDB.objects.channel_search("Requests")
        if not channel:
            # Create the channel if it doesn't exist
            channel = create.create_channel("Requests", typeclass="evennia.comms.comms.Channel")
        else:
            channel = channel[0]
        message = f"{player_name} {action} Request #{request_id}"
        channel.msg(f"[Request System] {message}", senders=self.caller, online=True)
