"""
Custom server services for Dies Irae.
"""
from evennia.server.service import ServerConfig

class CustomServerConfig(ServerConfig):
    """
    Custom server config that doesn't recreate channels.
    """
    
    def create_default_channels(self):
        """
        Override to prevent channel recreation.
        """
        pass  # Do nothing
