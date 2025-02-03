# jobsystem_cmdset.py

from evennia import CmdSet
from commands.jobs.jobs_commands import (
    CmdJobs,
    create_jobs_help_entry
)

class JobSystemCmdSet(CmdSet):
    """
    Command set for job system-related commands.
    """
    key = "JobSystemCmdSet"
    priority = 1

    def at_cmdset_creation(self):
        """
        Populates the command set.
        """
        self.add(CmdJobs())
        # Create help entry if it doesn't exist, but don't fail if it errors
        try:
            create_jobs_help_entry()
        except Exception as e:
            print(f"Warning: Could not create jobs help entry: {e}")