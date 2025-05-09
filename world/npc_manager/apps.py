from django.apps import AppConfig


class NPCManagerConfig(AppConfig):
    """Configuration for the NPC Manager application."""
    
    name = "world.npc_manager"
    verbose_name = "NPC Manager"
    
    def ready(self):
        """
        Initialize app when Django is ready.
        Import signals and perform other initialization here.
        """
        # Import signal handlers
        try:
            from . import signals
        except ImportError:
            pass 