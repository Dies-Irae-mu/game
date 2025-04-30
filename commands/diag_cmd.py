"""
Diagnostic commands for testing system functionality.
"""

from evennia.commands.default.muxcommand import MuxCommand
from commands.test_mail import diagnose_mail

class CmdDiagnoseMail(MuxCommand):
    """
    Run diagnostics on the mail system.
    
    Usage:
      @diagmail
    
    This command performs diagnostic checks on the mail system and reports
    the results. Useful for troubleshooting mail issues.
    """
    
    key = "@diagmail"
    locks = "cmd:all()"
    help_category = "System"
    
    def func(self):
        """Execute the command."""
        diagnose_mail(self.caller) 