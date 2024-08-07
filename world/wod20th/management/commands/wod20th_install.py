import subprocess
import os
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Perform maintenance tasks: git pull, make migrations, and run the load_wod20th_stats script.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Performing git pull..."))
        result = subprocess.run(["git", "pull"], capture_output=True, text=True)
        self.stdout.write(result.stdout)
        if result.returncode != 0:
            self.stdout.write(self.style.ERROR(f"Git pull failed: {result.stderr}"))
            return

        self.stdout.write(self.style.NOTICE("Making migrations..."))
        result = subprocess.run(["evennia", "makemigrations"], capture_output=True, text=True)
        self.stdout.write(result.stdout)
        if result.returncode != 0:
            self.stdout.write(self.style.ERROR(f"Making migrations failed: {result.stderr}"))
            return

        self.stdout.write(self.style.NOTICE("Applying migrations..."))
        result = subprocess.run(["evennia", "migrate"], capture_output=True, text=True)
        self.stdout.write(result.stdout)
        if result.returncode != 0:
            self.stdout.write(self.style.ERROR(f"Applying migrations failed: {result.stderr}"))
            return

        self.stdout.write(self.style.NOTICE("Running the load_wod20th_stats script..."))
        json_folder = "./data"
        result = subprocess.run(["evennia", "load_wod20th_stats", json_folder], capture_output=True, text=True)
        self.stdout.write(result.stdout)
        if result.returncode != 0:
            self.stdout.write(self.style.ERROR(f"Running the maintenance script failed: {result.stderr}"))
            return

        self.stdout.write(self.style.SUCCESS("Maintenance tasks completed successfully."))
