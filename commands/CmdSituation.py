"""
Commands for managing Situations.
"""

from evennia.commands.default.muxcommand import MuxCommand
from typeclasses.situation_controller import get_or_create_situation_controller
from world.situations.models import Situation, Detail, Development
from world.jobs.models import Job
from world.wod20th.utils.formatting import header, footer, divider
from evennia.utils.utils import crop
from evennia.utils.ansi import ANSIString

class CmdSituation(MuxCommand):
    """
    Access and manage situations.
    
    Usage:
      +sit                        - List all situations you have access to
      +sit <#>                    - View a specific situation
      +sit <#>/details           - List all details for a situation
      +sit <#>/detail <detail#>  - View a specific detail
      +sit <#>/devs              - List all developments for a situation
      +sit <#>/dev <dev#>        - View a specific development
      +sit/expand <#>            - Show comprehensive view of situation,
                                  including full details and developments
      +sit/detail <#>=<title>/<content>[/roster=<roster1>,<roster2>...][/secrecy=<0-10>]
                                - Add a detail to a situation you have access to
                                - Optional roster restrictions can be specified
                                - For public situations, any roster can be specified
                                - For restricted situations, rosters must be a subset
                                  of the situation's roster restrictions
                                - Optional secrecy rating (0-10) for staff only
      
    Staff/Admin commands:
      +sit/create <title>=<description>[/roster=<roster1>,<roster2>...]
                                - Create a new situation
                                - Optional roster restrictions can be specified
                                - If no rosters specified, situation is public
      +sit/dev <#>=<title>/<content>[/roster=<roster1>,<roster2>...]
                                - Add a development to a situation
                                - Optional roster restrictions can be specified
                                - For public situations, any roster can be specified
                                - For restricted situations, rosters must be a subset
                                  of the situation's roster restrictions
      +sit/resolve <#>/<dev#>=<resolution>
                                - Resolve a development with outcome text
      +sit/linkjob <#>=<job#>   - Link a job to a situation
      +sit/unlinkjob <#>=<job#> - Unlink a job from a situation
      +sit/linkplot <#>=<plot#> - Link a plot to a situation
      +sit/unlinkplot <#>=<plot#> - Unlink a plot from a situation
      +sit/delete <#>           - Delete an entire situation
      +sit/deldetail <#>/<detail#>
                                - Delete a specific detail
      +sit/deldev <#>/<dev#>    - Delete a specific development
      +sit/addroster <#>=<roster1>,<roster2>...
                                - Add rosters to a situation
      +sit/remroster <#>=<roster1>,<roster2>...
                                - Remove rosters from a situation
      +sit/addroster <#>/detail <detail#>=<roster1>,<roster2>...
                                - Add rosters to a detail
      +sit/remroster <#>/detail <detail#>=<roster1>,<roster2>...
                                - Remove rosters from a detail
      +sit/addroster <#>/dev <dev#>=<roster1>,<roster2>...
                                - Add rosters to a development
      +sit/remroster <#>/dev <dev#>=<roster1>,<roster2>...
                                - Remove rosters from a development
      +sit/notes <#>=<notes>    - Set staff notes for a situation
      +sit/notes <#>/detail <detail#>=<notes>
                                - Set staff notes for a detail
      +sit/notes <#>/dev <dev#>=<notes>
                                - Set staff notes for a development
      
    Examples:
      +sit
      +sit 1
      +sit 1/details
      +sit 1/detail 2
      +sit 1/devs
      +sit 1/dev 3
      +sit/expand 1              - View complete details of situation #1
      +sit/detail 1=Hidden Clue/A bloody handprint...
      +sit/detail 1=Hidden Clue/A bloody handprint.../roster=Vampire
      +sit/create Mystery at the Manor=Strange occurrences...
      +sit/create Secret Meeting=Clandestine gathering.../roster=Vampire,Mage
      +sit/dev 1=Investigation Begins/The coterie arrives.../roster=Vampire
      +sit/resolve 1/1=The handprint belonged to a ghoul.
      +sit/linkjob 1=42
      +sit/unlinkjob 1=42
      +sit/delete 1
      +sit/deldetail 1/2
      +sit/deldev 1/3
      +sit/addroster 1=Vampire,Mage
      +sit/remroster 1=Vampire
      +sit/addroster 1/detail 2=Vampire,Mage
      +sit/remroster 1/detail 2=Mage
      +sit/addroster 1/dev 3=Vampire
      +sit/remroster 1/dev 3=Vampire
    """
    
    key = "+sit"
    aliases = ["sit"]
    locks = "cmd:all()"
    help_category = "Situations"
    
    def check_admin_access(self):
        """Check if the caller has admin access."""
        return self.caller.check_permstring("Admin")
        
    def check_builder_access(self):
        """Check if the caller has builder access."""
        return self.caller.check_permstring("Builder")
        
    def display_related_jobs(self, situation):
        """Display related jobs in the same format as the jobs list."""
        if not situation['related_jobs']:
            return "\nNo related jobs.\n|wTip:|n Use |y+job/linksit <jobId>=" + str(situation['id']) + "|n to link a job to this situation."

        # Define column widths (same as jobs command)
        col_widths = {
            'job_id': 6,    # "Job # "
            'queue': 10,    # "Queue     "
            'title': 25,    # "Job Title                "
            'originator': 12, # "Originator   "
            'assignee': 12,   # "Assignee     "
            'status': 8      # "Status   "
        }

        output = ["\nRelated Jobs:"]
        output.append("|wTip:|n Use |y+job/linksit <jobId>=" + str(situation['id']) + "|n to link a job to this situation.")
        output.append(divider("", width=78, fillchar="-", color="|r"))
        
        # Create the header row with fixed column widths
        header_row = (
            f"|cJob #".ljust(col_widths['job_id']) +
            f"Queue".ljust(col_widths['queue']) +
            f"Job Title".ljust(col_widths['title']) +
            f"Originator".ljust(col_widths['originator']) +
            f"Assignee".ljust(col_widths['assignee']) +
            f"Status|n"
        )
        output.append(header_row)
        output.append(ANSIString("|r" + "-" * 78 + "|n"))

        # Get all related jobs
        jobs = Job.objects.filter(id__in=situation['related_jobs'])
        
        # Add each job as a row with proper column spacing
        for job in jobs:
            if (self.check_admin_access() or self.check_builder_access() or 
                job.requester == self.caller.account or 
                job.assignee == self.caller.account or 
                self.caller.account in job.participants.all()):
                
                assignee = job.assignee.username if job.assignee else "-----"
                originator = job.requester.username if job.requester else "-----"
                
                # Check if job has been viewed by this user
                unread = job.is_updated_since_last_view(self.caller.account)
                title_marker = "|r*|n " if unread else "  "
                
                # Format each field with proper width
                job_id = str(job.id).ljust(col_widths['job_id'])
                queue = crop(job.queue.name, width=col_widths['queue']-2).ljust(col_widths['queue'])  # -2 for spacing
                title = title_marker + crop(job.title, width=col_widths['title']-2)  # -2 for marker
                title = title.ljust(col_widths['title'])
                originator = crop(originator, width=col_widths['originator']-2).ljust(col_widths['originator'])
                assignee = crop(assignee, width=col_widths['assignee']-2).ljust(col_widths['assignee'])
                status = crop(job.status, width=col_widths['status'])
                
                # Combine all fields with proper spacing
                row = f"{job_id}{queue}{title}{originator}{assignee}{status}"
                output.append(row)

        output.append(divider("", width=78, fillchar="-", color="|r"))
        return "\n".join(output)

    def display_related_plots(self, situation):
        """Display related plots in a formatted list."""
        from world.plots.models import Plot
        
        if not hasattr(situation, 'related_plots') or not situation['related_plots']:
            return "\nNo related plots.\n|wTip:|n Use |y+sit/linkplot <#>=<plot#>|n to link a plot to this situation."

        output = ["\nRelated Plots:"]
        output.append("|wTip:|n Use |y+sit/linkplot <#>=<plot#>|n to link a plot to this situation.")
        output.append(divider("", width=78, fillchar="-", color="|r"))
        
        # Define column widths
        col_widths = {
            'plot_id': 6,     # "Plot # "
            'genre': 10,      # "Genre     "
            'title': 25,      # "Plot Title               "
            'storyteller': 12,# "Storyteller "
            'status': 8       # "Status   "
        }
        
        # Create header row
        header_row = (
            f"|cPlot #".ljust(col_widths['plot_id']) +
            f"Genre".ljust(col_widths['genre']) +
            f"Plot Title".ljust(col_widths['title']) +
            f"Storyteller".ljust(col_widths['storyteller']) +
            f"Status|n"
        )
        output.append(header_row)
        output.append(ANSIString("|r" + "-" * 78 + "|n"))
        
        # Get all related plots
        plots = Plot.objects.filter(id__in=situation['related_plots'])
        for plot in plots:
            storyteller = plot.storyteller.username if plot.storyteller else "-----"
            status = "claimed" if plot.claimed else "open"
            
            # Format each field
            plot_id = str(plot.id).ljust(col_widths['plot_id'])
            genre = crop(plot.genre, col_widths['genre']-2).ljust(col_widths['genre'])
            title = crop(plot.title, col_widths['title']-2).ljust(col_widths['title'])
            storyteller = crop(storyteller, col_widths['storyteller']-2).ljust(col_widths['storyteller'])
            status = crop(status, col_widths['status'])
            
            # Combine fields
            row = f"{plot_id}{genre}{title}{storyteller}{status}"
            output.append(row)
            
        output.append(divider("", width=78, fillchar="-", color="|r"))
        return "\n".join(output)

    def func(self):
        """Execute command."""
        controller = get_or_create_situation_controller()
        
        if not self.args and not self.switches:
            # List all situations the character has access to
            situations = controller.get_all_situations()
            if not situations:
                self.caller.msg("No situations available.")
                return
                
            # Table Header
            output = []
            output.append("=" * 78)
            output.append("{:<5} {:<35} {:<15} {:<10} {:<10}".format("ID", "Title", "Created", "Access", "Jobs"))
            output.append("-" * 78)
            
            # List situations
            is_staff = self.check_admin_access() or self.check_builder_access()
            for situation in situations:
                if is_staff or controller.has_access(situation.id, self.caller):
                    # For staff, show roster info and staff notes indicator
                    if is_staff:
                        access = "All" if not situation.roster_names else f"{len(situation.roster_names)} roster(s)"
                        has_notes = "|y*|n" if situation.staff_notes else " "
                        title_display = f"{situation.title[:33]}{has_notes}"
                    else:
                        access = ""
                        title_display = situation.title[:35]
                    # Show linked jobs
                    jobs = situation.related_jobs.count()
                    output.append(f"{situation.id:<5} {title_display:<35} {situation.created_at|date:'Y-m-d H:i'} {access:<10} {jobs:<10}")
                    
            output.append("=" * 78)
            if is_staff:
                output.append("|y*|n indicates staff notes present")
            self.caller.msg("\n".join(output))
            return
            
        if self.switches:
            switch = self.switches[0].lower()
            
            if switch == "create":
                # Create a new situation - staff only
                if not (self.check_admin_access() or self.check_builder_access()):
                    self.caller.msg("You don't have permission to create situations.")
                    return
                    
                if not self.args or "=" not in self.args:
                    self.caller.msg("Usage: +sit/create <title>=<description>[/roster=<roster1>,<roster2>...]")
                    return
                    
                title, description = self.args.split("=", 1)
                title = title.strip()
                description = description.strip()
                
                # Parse roster names if provided
                roster_names = None
                if "/roster=" in description:
                    description, roster_list = description.split("/roster=", 1)
                    roster_names = [r.strip() for r in roster_list.split(",")]
                    
                result = controller.create_situation(title, description, roster_names)
                self.caller.msg(result)
                return
                
            elif switch == "detail":
                # Add a detail to a situation
                if not self.args or "=" not in self.args:
                    self.caller.msg("Usage: +sit/detail <#>=<title>/<content>[/roster=<roster1>,<roster2>...][/secrecy=<0-10>]")
                    return
                    
                try:
                    situation_id, detail_info = self.args.split("=", 1)
                    situation_id = int(situation_id.strip())
                    
                    if "/" not in detail_info:
                        self.caller.msg("Detail title and content must be separated by '/'")
                        return
                        
                    title, content = detail_info.split("/", 1)
                    title = title.strip()
                    content = content.strip()
                    
                    # Parse roster names and secrecy rating if provided
                    roster_names = None
                    secrecy_rating = 0
                    
                    if "/roster=" in content:
                        content, roster_list = content.split("/roster=", 1)
                        if "/secrecy=" in roster_list:
                            roster_list, secrecy = roster_list.split("/secrecy=", 1)
                            secrecy_rating = int(secrecy.strip())
                        roster_names = [r.strip() for r in roster_list.split(",")]
                        
                    elif "/secrecy=" in content:
                        content, secrecy = content.split("/secrecy=", 1)
                        secrecy_rating = int(secrecy.strip())
                        
                    # Only staff can set secrecy rating
                    if secrecy_rating > 0 and not (self.check_admin_access() or self.check_builder_access()):
                        self.caller.msg("Only staff can set secrecy ratings.")
                        return
                        
                    result = controller.add_detail(situation_id, title, content, roster_names, secrecy_rating)
                    self.caller.msg(result)
                    
                except ValueError:
                    self.caller.msg("Invalid input. Make sure situation ID and secrecy rating are numbers.")
                return
                
            elif switch == "dev":
                # Add a development to a situation
                if not self.args or "=" not in self.args:
                    self.caller.msg("Usage: +sit/dev <#>=<title>/<content>[/roster=<roster1>,<roster2>...]")
                    return
                    
                try:
                    situation_id, dev_info = self.args.split("=", 1)
                    situation_id = int(situation_id.strip())
                    
                    if "/" not in dev_info:
                        self.caller.msg("Development title and content must be separated by '/'")
                        return
                        
                    title, content = dev_info.split("/", 1)
                    title = title.strip()
                    content = content.strip()
                    
                    # Parse roster names if provided
                    roster_names = None
                    if "/roster=" in content:
                        content, roster_list = content.split("/roster=", 1)
                        roster_names = [r.strip() for r in roster_list.split(",")]
                        
                    result = controller.add_development(situation_id, title, content, roster_names)
                    self.caller.msg(result)
                    
                except ValueError:
                    self.caller.msg("Invalid input. Make sure situation ID is a number.")
                return
                
            elif switch == "resolve":
                # Resolve a development
                if not self.args or "=" not in self.args:
                    self.caller.msg("Usage: +sit/resolve <#>/<dev#>=<resolution>")
                    return
                    
                try:
                    target, resolution = self.args.split("=", 1)
                    if "/" not in target:
                        self.caller.msg("Must specify both situation and development ID: <#>/<dev#>")
                        return
                        
                    situation_id, development_id = target.split("/", 1)
                    situation_id = int(situation_id.strip())
                    development_id = int(development_id.strip())
                    
                    result = controller.resolve_development(situation_id, development_id, resolution.strip())
                    self.caller.msg(result)
                    
                except ValueError:
                    self.caller.msg("Invalid input. Make sure situation ID and development ID are numbers.")
                return
                
            elif switch == "notes":
                # Set staff notes - staff only
                if not (self.check_admin_access() or self.check_builder_access()):
                    self.caller.msg("You don't have permission to set staff notes.")
                    return
                    
                if not self.args or "=" not in self.args:
                    self.caller.msg("Usage: +sit/notes <#>[/detail <detail#> or /dev <dev#>]=<notes>")
                    return
                    
                target, notes = self.args.split("=", 1)
                target = target.strip()
                notes = notes.strip()
                
                if "/" in target:
                    sit_id, component = target.split("/", 1)
                    try:
                        sit_id = int(sit_id)
                    except ValueError:
                        self.caller.msg("Situation ID must be a number.")
                        return
                        
                    if component.startswith("detail "):
                        try:
                            detail_id = int(component.split()[1])
                            result = controller.set_staff_notes(sit_id, notes, detail_id=detail_id)
                        except (IndexError, ValueError):
                            self.caller.msg("Detail ID must be a number.")
                            return
                    elif component.startswith("dev "):
                        try:
                            dev_id = int(component.split()[1])
                            result = controller.set_staff_notes(sit_id, notes, development_id=dev_id)
                        except (IndexError, ValueError):
                            self.caller.msg("Development ID must be a number.")
                            return
                    else:
                        self.caller.msg("Invalid component. Use 'detail <#>' or 'dev <#>'.")
                        return
                else:
                    try:
                        sit_id = int(target)
                        result = controller.set_staff_notes(sit_id, notes)
                    except ValueError:
                        self.caller.msg("Situation ID must be a number.")
                        return
                        
                self.caller.msg(result)
                return
                
            elif switch in ["dev", "linkjob", "unlinkjob", "linkplot", "unlinkplot", "delete", "deldetail", "deldev", "addroster", "remroster"]:
                # These commands are staff-only
                if not (self.check_admin_access() or self.check_builder_access()):
                    self.caller.msg("You don't have permission to manage developments, links, or delete content.")
                    return
                    
                if switch == "delete":
                    # Delete a situation
                    try:
                        sit_id = int(self.args.strip())
                    except (ValueError, TypeError):
                        self.caller.msg("Usage: +sit/delete <#>")
                        return
                        
                    result = controller.delete_situation(sit_id)
                    self.caller.msg(result)
                    
                elif switch == "deldetail":
                    # Delete a detail
                    if not self.args or "/" not in self.args:
                        self.caller.msg("Usage: +sit/deldetail <#>/<detail#>")
                        return
                        
                    try:
                        sit_id, detail_id = [int(i.strip()) for i in self.args.split("/")]
                    except ValueError:
                        self.caller.msg("Both situation ID and detail ID must be numbers.")
                        return
                        
                    result = controller.delete_detail(sit_id, detail_id)
                    self.caller.msg(result)
                    
                elif switch == "deldev":
                    # Delete a development
                    if not self.args or "/" not in self.args:
                        self.caller.msg("Usage: +sit/deldev <#>/<dev#>")
                        return
                        
                    try:
                        sit_id, dev_id = [int(i.strip()) for i in self.args.split("/")]
                    except ValueError:
                        self.caller.msg("Both situation ID and development ID must be numbers.")
                        return
                        
                    result = controller.delete_development(sit_id, dev_id)
                    self.caller.msg(result)
                
                elif switch in ["addroster", "remroster"]:
                    # These commands are staff-only
                    if not (self.check_admin_access() or self.check_builder_access()):
                        self.caller.msg("You don't have permission to manage roster access.")
                        return
                        
                    if not self.args or "=" not in self.args:
                        self.caller.msg("Usage: +sit/addroster <#>[/detail <detail#> or /dev <dev#>]=<roster1>,<roster2>...")
                        return
                        
                    target, roster_list = self.args.split("=", 1)
                    target = target.strip()
                    roster_names = [r.strip() for r in roster_list.split(",")]
                    
                    if not roster_names:
                        self.caller.msg("You must specify at least one roster.")
                        return
                        
                    # Check if we're modifying a detail or development
                    if "/" in target:
                        sit_id, component = target.split("/", 1)
                        try:
                            sit_id = int(sit_id)
                        except ValueError:
                            self.caller.msg("Situation ID must be a number.")
                            return
                            
                        if component.startswith("detail "):
                            try:
                                detail_id = int(component.split()[1])
                            except (IndexError, ValueError):
                                self.caller.msg("Detail ID must be a number.")
                                return
                                
                            result = controller.modify_detail_rosters(sit_id, detail_id, roster_names, add=(switch == "addroster"))
                            
                        elif component.startswith("dev "):
                            try:
                                dev_id = int(component.split()[1])
                            except (IndexError, ValueError):
                                self.caller.msg("Development ID must be a number.")
                                return
                                
                            result = controller.modify_development_rosters(sit_id, dev_id, roster_names, add=(switch == "addroster"))
                            
                        else:
                            self.caller.msg("Invalid component. Use 'detail <#>' or 'dev <#>'.")
                            return
                            
                    else:
                        # Modifying situation rosters
                        try:
                            sit_id = int(target)
                        except ValueError:
                            self.caller.msg("Situation ID must be a number.")
                            return
                            
                        result = controller.modify_situation_rosters(sit_id, roster_names, add=(switch == "addroster"))
                        
                    self.caller.msg(result)
                
                elif switch == "linkplot":
                    if not self.args or "=" not in self.args:
                        self.caller.msg("Usage: +sit/linkplot <#>=<plot#>")
                        return
                        
                    try:
                        sit_id, plot_id = [int(i.strip()) for i in self.args.split("=")]
                    except ValueError:
                        self.caller.msg("Both situation ID and plot ID must be numbers.")
                        return
                        
                    result = controller.link_plot(sit_id, plot_id)
                    self.caller.msg(result)
                    
                elif switch == "unlinkplot":
                    if not self.args or "=" not in self.args:
                        self.caller.msg("Usage: +sit/unlinkplot <#>=<plot#>")
                        return
                        
                    try:
                        sit_id, plot_id = [int(i.strip()) for i in self.args.split("=")]
                    except ValueError:
                        self.caller.msg("Both situation ID and plot ID must be numbers.")
                        return
                        
                    result = controller.unlink_plot(sit_id, plot_id)
                    self.caller.msg(result)
                
            elif switch == "expand":
                # Show comprehensive view of a situation
                try:
                    sit_id = int(self.args)
                except (ValueError, TypeError):
                    self.caller.msg("Usage: +sit/expand <#>")
                    return
                    
                situation = controller.get_situation(sit_id)
                if not situation:
                    self.caller.msg(f"No situation found with ID {sit_id}.")
                    return
                    
                if not (controller.has_access(sit_id, self.caller) or self.check_admin_access() or self.check_builder_access()):
                    self.caller.msg("You don't have access to this situation.")
                    return
                    
                output = []
                # Situation Header
                output.append("=" * 78)
                output.append(f"Situation #{sit_id}: {situation['title']}")
                output.append("=" * 78)
                output.append(f"Created: {situation['created_at']}")
                
                # Show roster access info
                if self.check_admin_access() or self.check_builder_access():
                    if situation['roster_names']:
                        output.append(f"Visible to rosters: {', '.join(situation['roster_names'])}")
                    else:
                        output.append("Visible to: Everyone")
                elif situation['roster_names']:
                    output.append(f"Visible to: {', '.join(situation['roster_names'])}")
                    
                output.append("\nDescription:")
                output.append("-" * 78)
                output.append(situation['description'])
                
                # Show related jobs for staff
                if (self.check_admin_access() or self.check_builder_access()) and situation['related_jobs']:
                    output.append(self.display_related_jobs(situation))
                
                # Show related plots for staff
                if (self.check_admin_access() or self.check_builder_access()) and situation['related_plots']:
                    output.append(self.display_related_plots(situation))
                
                # Details Section
                output.append("\nDetails:")
                output.append("=" * 78)
                if situation['details']:
                    for detail in situation['details']:
                        if controller.has_detail_access(sit_id, detail['id'], self.caller) or self.check_admin_access() or self.check_builder_access():
                            output.append(f"Detail #{detail['id']}: {detail['title']}")
                            output.append(f"Created: {detail['created_at']}")
                            
                            # Show roster access for the detail
                            if self.check_admin_access() or self.check_builder_access():
                                if detail['roster_names']:
                                    output.append(f"Visible to rosters: {', '.join(detail['roster_names'])}")
                                else:
                                    output.append(f"Visible to: Same as situation ({', '.join(situation['roster_names']) if situation['roster_names'] else 'Everyone'})")
                            elif detail['roster_names']:
                                output.append(f"Visible to: {', '.join(detail['roster_names'])}")
                                
                            output.append("-" * 78)
                            output.append(detail['content'])
                            output.append("-" * 78)
                            output.append("")  # Empty line between details
                else:
                    output.append("No details available")
                    
                # Developments Section
                output.append("\nDevelopments:")
                output.append("=" * 78)
                if situation['developments']:
                    for dev in situation['developments']:
                        if controller.has_development_access(sit_id, dev['id'], self.caller) or self.check_admin_access() or self.check_builder_access():
                            output.append(f"Development #{dev['id']}: {dev['title']}")
                            output.append(f"Created: {dev['created_at']}")
                            output.append(f"Status: {'Resolved' if dev['resolved'] else 'Open'}")
                            
                            # Show roster access for the development
                            if self.check_admin_access() or self.check_builder_access():
                                if dev['roster_names']:
                                    output.append(f"Visible to rosters: {', '.join(dev['roster_names'])}")
                                else:
                                    output.append(f"Visible to: Same as situation ({', '.join(situation['roster_names']) if situation['roster_names'] else 'Everyone'})")
                            elif dev['roster_names']:
                                output.append(f"Visible to: {', '.join(dev['roster_names'])}")
                                
                            output.append("-" * 78)
                            output.append(dev['content'])
                            
                            if dev['resolved']:
                                output.append("\nResolution:")
                                output.append("-" * 78)
                                output.append(dev['resolution_text'])
                                output.append(f"Resolved at: {dev['resolved_at']}")
                                
                            output.append("-" * 78)
                            output.append("")  # Empty line between developments
                else:
                    output.append("No developments available")
                    
                # Add related plots display to situation view
                output.append(self.display_related_plots(situation))
                    
                output.append("=" * 78)
                self.caller.msg("\n".join(output))
                return
            
        # No switches - viewing situations and components
        if "/" in self.args:
            # Viewing specific components
            situation_id, component = self.args.split("/", 1)
            try:
                situation_id = int(situation_id.strip())
                situation = Situation.objects.get(id=situation_id)
                
                if not controller.has_access(situation_id, self.caller):
                    self.caller.msg("You don't have access to that situation.")
                    return
                    
            except (ValueError, Situation.DoesNotExist):
                self.caller.msg("Invalid situation ID.")
                return
                
            if component == "details":
                # List all details
                details = [d for d in situation.details.all() if controller.has_detail_access(situation_id, d.id, self.caller)]
                
                if not details:
                    self.caller.msg("No details available for this situation.")
                    return
                    
                output = []
                output.append("=" * 78)
                output.append(f"Details for Situation #{situation_id}: {situation.title}")
                output.append("-" * 78)
                
                for detail in details:
                    # Format each detail
                    title_line = f"#{detail.id}: {detail.title}"
                    if self.check_admin_access() or self.check_builder_access():
                        if detail.secrecy_rating > 0:
                            title_line += f" |y(Secrecy: {detail.secrecy_rating})|n"
                        if detail.staff_notes:
                            title_line += " |y*|n"
                    output.append(title_line)
                    output.append(detail.content[:100] + "..." if len(detail.content) > 100 else detail.content)
                    output.append("-" * 78)
                    
                self.caller.msg("\n".join(output))
                
            elif component.startswith("detail "):
                # View specific detail
                try:
                    detail_id = int(component.split()[1])
                    detail = Detail.objects.get(id=detail_id, situation=situation)
                    
                    if not controller.has_detail_access(situation_id, detail_id, self.caller):
                        self.caller.msg("You don't have access to that detail.")
                        return
                        
                    output = []
                    output.append("=" * 78)
                    output.append(f"Detail #{detail.id}: {detail.title}")
                    if self.check_admin_access() or self.check_builder_access():
                        if detail.secrecy_rating > 0:
                            output.append(f"|ySecrecy Rating: {detail.secrecy_rating}|n")
                    output.append("-" * 78)
                    output.append(detail.content)
                    
                    if self.check_admin_access() or self.check_builder_access():
                        if detail.staff_notes:
                            output.append("\n|yStaff Notes:|n")
                            output.append("-" * 78)
                            output.append(detail.staff_notes)
                            
                    output.append("=" * 78)
                    self.caller.msg("\n".join(output))
                    
                except (ValueError, Detail.DoesNotExist):
                    self.caller.msg("Invalid detail ID.")
                    
            elif component == "devs":
                # List all developments
                developments = [d for d in situation.developments.all() if controller.has_development_access(situation_id, d.id, self.caller)]
                
                if not developments:
                    self.caller.msg("No developments available for this situation.")
                    return
                    
                output = []
                output.append("=" * 78)
                output.append(f"Developments for Situation #{situation_id}: {situation.title}")
                output.append("-" * 78)
                
                for dev in developments:
                    # Format each development
                    status = "|gResolved|n" if dev.resolved else "|bOpen|n"
                    title_line = f"#{dev.id}: {dev.title} ({status})"
                    if self.check_admin_access() or self.check_builder_access():
                        if dev.staff_notes:
                            title_line += " |y*|n"
                    output.append(title_line)
                    output.append(dev.content[:100] + "..." if len(dev.content) > 100 else dev.content)
                    if dev.resolved:
                        output.append(f"\nResolved at: {dev.resolved_at|date:'Y-m-d H:i'}")
                        output.append(f"Resolution: {dev.resolution_text}")
                    output.append("-" * 78)
                    
                self.caller.msg("\n".join(output))
                
            elif component.startswith("dev "):
                # View specific development
                try:
                    dev_id = int(component.split()[1])
                    development = Development.objects.get(id=dev_id, situation=situation)
                    
                    if not controller.has_development_access(situation_id, dev_id, self.caller):
                        self.caller.msg("You don't have access to that development.")
                        return
                        
                    output = []
                    output.append("=" * 78)
                    status = "|gResolved|n" if development.resolved else "|bOpen|n"
                    output.append(f"Development #{development.id}: {development.title} ({status})")
                    output.append("-" * 78)
                    output.append(development.content)
                    
                    if development.resolved:
                        output.append(f"\nResolved at: {development.resolved_at|date:'Y-m-d H:i'}")
                        output.append(f"Resolution: {development.resolution_text}")
                        
                    if self.check_admin_access() or self.check_builder_access():
                        if development.staff_notes:
                            output.append("\n|yStaff Notes:|n")
                            output.append("-" * 78)
                            output.append(development.staff_notes)
                            
                    output.append("=" * 78)
                    self.caller.msg("\n".join(output))
                    
                except (ValueError, Development.DoesNotExist):
                    self.caller.msg("Invalid development ID.")
                    
            else:
                self.caller.msg("Invalid component. Use 'details', 'detail <#>', 'devs', or 'dev <#>'.")
                
        else:
            # Viewing a specific situation
            try:
                situation_id = int(self.args.strip())
                situation = Situation.objects.get(id=situation_id)
                
                if not controller.has_access(situation_id, self.caller):
                    self.caller.msg("You don't have access to that situation.")
                    return
                    
                output = []
                output.append("=" * 78)
                output.append(f"Situation #{situation.id}: {situation.title}")
                output.append("-" * 78)
                output.append(situation.description)
                output.append("\nCreated: " + situation.created_at.strftime("%Y-%m-d %H:%M:%S"))
                
                if self.check_admin_access() or self.check_builder_access():
                    output.append("\nAccess: " + ("All" if not situation.roster_names else ", ".join(situation.roster_names)))
                    
                    if situation.staff_notes:
                        output.append("\n|yStaff Notes:|n")
                        output.append("-" * 78)
                        output.append(situation.staff_notes)
                        
                # Show related jobs (staff only)
                if self.check_admin_access() or self.check_builder_access():
                    if situation.related_jobs.exists():
                        output.append("\nRelated Jobs:")
                        output.append("-" * 78)
                        for job in situation.related_jobs.all():
                            output.append(f"#{job.id}: {job.title} ({job.status})")
                            
                # Show related plots
                if situation.related_plots.exists():
                    output.append("\nRelated Plots:")
                    output.append("-" * 78)
                    for plot in situation.related_plots.all():
                        output.append(f"#{plot.id}: {plot.title}")
                        if plot.storyteller:
                            output.append(f"Storyteller: {plot.storyteller.username}")
                            
                output.append("=" * 78)
                self.caller.msg("\n".join(output))
                
            except (ValueError, Situation.DoesNotExist):
                self.caller.msg("Invalid situation ID.") 