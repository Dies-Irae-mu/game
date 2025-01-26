import time
from evennia import SESSION_HANDLER as evennia
from evennia.utils import utils
from world.wod20th.utils.formatting import header, footer, divider
from evennia.utils.utils import class_from_module
from evennia.utils.ansi import strip_ansi
from django.conf import settings

COMMAND_DEFAULT_CLASS = class_from_module(settings.COMMAND_DEFAULT_CLASS)

class CmdWho(COMMAND_DEFAULT_CLASS):
    """
    list who is currently online, showing character names

    Usage:
      who
      doing

    Shows who is currently online using character names instead of account names.
    'doing' is an alias that limits info also for those with all permissions.
    """

    key = "who"
    aliases = ["doing"]
    locks = "cmd:all()"
    account_caller = False  # important for Account commands
    help_category = "General"

    def format_name(self, puppet, account):
        """Helper function to format character names consistently"""
        if puppet:
            # Get display name but strip any existing ANSI formatting
            display_name = puppet.get_display_name(account)
            clean_name = strip_ansi(display_name)
            
            # Add indicators using tags
            name_suffix = ""
            if puppet.check_permstring("builders"):
                name_suffix += f"*{name_suffix}"
            if puppet.tags.has("in_umbra", category="state"):
                name_suffix = f"@{name_suffix}"
            if puppet.db.lfrp:
                name_suffix = f"${name_suffix}"
            
            # For debugging
            # self.msg(f"Tags for {puppet.key}: {puppet.tags.all()}")
            
            # If no prefix, add a space to maintain alignment
            name_suffix = name_suffix or " "
            
            # Add the dbref
            name = f"{name_suffix}{clean_name}"
            return utils.crop(name, width=17)
        return "None".ljust(17)

    def func(self):
        """
        Get all connected accounts by polling session.
        """
        account = self.account
        session_list = evennia.get_sessions()

        session_list = sorted(session_list, key=lambda o: o.get_puppet().key if o.get_puppet() else o.account.key)

        if self.cmdstring == "doing":
            show_session_data = False
        else:
            show_session_data = account.check_permstring("Developer") or account.check_permstring(
                "Admins"
            )


        naccounts = evennia.account_count()
        if show_session_data:
            # privileged info
            string = header("Online Characters", width=78) + "\n"
            string += "|wName              On       Idle     Account     Room            Cmds  Host|n\n"
            string += "|r" + "-" * 78 + "|n\n"
            
            for session in session_list:
                if not session.logged_in:
                    continue
                delta_cmd = time.time() - session.cmd_last_visible
                delta_conn = time.time() - session.conn_time
                session_account = session.get_account()
                puppet = session.get_puppet()
                location = puppet.location.key if puppet and puppet.location else "None"
                
                string += " %-17s %-8s %-8s %-10s %-15s %-5s %s\n" % (
                    self.format_name(puppet, account),
                    utils.time_format(delta_conn, 0),
                    utils.time_format(delta_cmd, 1),
                    utils.crop(session_account.get_display_name(account), width=10),
                    utils.crop(location, width=15),
                    str(session.cmd_total).ljust(5),
                    isinstance(session.address, tuple) and session.address[0] or session.address
                )
        else:
            # unprivileged
            string = header("Online Characters", width=78) + "\n"
            string += "|wName              On       Idle     Room|n\n"
            string += "|r" + "-" * 78 + "|n\n"
            
            for session in session_list:
                if not session.logged_in:
                    continue
                delta_cmd = time.time() - session.cmd_last_visible
                delta_conn = time.time() - session.conn_time
                puppet = session.get_puppet()
                location = puppet.location.key if puppet and puppet.location else "None"
                
                string += " %-17s %-8s %-8s %s\n" % (
                    self.format_name(puppet, account),
                    utils.time_format(delta_conn, 0),
                    utils.time_format(delta_cmd, 1),
                    utils.crop(location, width=25)
                )

        is_one = naccounts == 1
        string += "|r" + "-" * 78 + "|n\n"
        string += f"{naccounts} unique account{'s' if not is_one else ''} logged in.\n"
        string += "|r" + "-" * 78 + "|n\n"
        string += "|yLegend: * = Staff, $ = Looking for RP, @ = In Umbra|n\n"  # Fixed legend formatting
        string += "|r" + "-" * 78 + "|n\n"
        string += footer(width=78)
        
        self.msg(string)