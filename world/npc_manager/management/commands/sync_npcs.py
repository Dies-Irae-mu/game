"""
Django management command to synchronize NPCs between database and game.
"""

from django.core.management.base import BaseCommand
from world.npc_manager.utils import sync_all_npcs, sync_all_groups


class Command(BaseCommand):
    """
    Django command to synchronize NPCs and NPC Groups between the database and the game.
    
    This ensures that any NPCs or NPC Groups created in the game are properly
    represented in the database models, allowing them to be managed through the
    Django admin interface.
    """
    
    help = "Synchronize NPCs and NPC Groups between database and game objects"
    
    def add_arguments(self, parser):
        """Define command arguments."""
        parser.add_argument(
            '--quiet',
            action='store_true',
            dest='quiet',
            default=False,
            help='Suppress verbose output',
        )
        parser.add_argument(
            '--npcs-only',
            action='store_true',
            dest='npcs_only',
            default=False,
            help='Only synchronize NPCs, not NPC Groups',
        )
        parser.add_argument(
            '--groups-only',
            action='store_true',
            dest='groups_only',
            default=False,
            help='Only synchronize NPC Groups, not NPCs',
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        # Get verbosity
        quiet = options.get('quiet', False)
        npcs_only = options.get('npcs_only', False)
        groups_only = options.get('groups_only', False)
        
        if not quiet:
            self.stdout.write(self.style.MIGRATE_HEADING("Starting NPC synchronization..."))
        
        # Sync NPCs if requested
        if not groups_only:
            npcs_created, npcs_updated = sync_all_npcs()
            if not quiet:
                self.stdout.write(self.style.SUCCESS(
                    f"NPCs synchronized: {npcs_created} created, {npcs_updated} updated"
                ))
        
        # Sync NPC Groups if requested
        if not npcs_only:
            groups_created, groups_updated = sync_all_groups()
            if not quiet:
                self.stdout.write(self.style.SUCCESS(
                    f"NPC Groups synchronized: {groups_created} created, {groups_updated} updated"
                ))
        
        if not quiet:
            self.stdout.write(self.style.SUCCESS("NPC synchronization complete!")) 