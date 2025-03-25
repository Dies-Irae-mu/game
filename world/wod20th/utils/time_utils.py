"""
Time and timezone utilities for WoD20th.
"""
from datetime import datetime
import pytz
from evennia.utils.utils import lazy_property
from evennia.utils.logger import log_info

class TimeManager:
    """
    Handles timezone conversions and time formatting based on player location.
    """
    
    # Common timezone abbreviations mapping
    TIMEZONE_ALIASES = {
        # North America
        'PST': 'America/Los_Angeles',
        'PDT': 'America/Los_Angeles',
        'MST': 'America/Denver',
        'MDT': 'America/Denver',
        'CST': 'America/Chicago',
        'CDT': 'America/Chicago',
        'EST': 'America/New_York',
        'EDT': 'America/New_York',
        'AST': 'America/Anchorage',
        'AKST': 'America/Anchorage',
        'HST': 'Pacific/Honolulu',
        
        # Europe
        'GMT': 'Europe/London',
        'BST': 'Europe/London',
        'WET': 'Europe/London',
        'WEST': 'Europe/London',
        'CET': 'Europe/Paris',
        'CEST': 'Europe/Paris',
        'EET': 'Europe/Helsinki',
        'EEST': 'Europe/Helsinki',
        
        # Asia/Pacific
        'JST': 'Asia/Tokyo',
        'AEST': 'Australia/Sydney',
        'AEDT': 'Australia/Sydney',
        'AWST': 'Australia/Perth',
        'IST': 'Asia/Kolkata',
        
        # UTC/Generic
        'UTC': 'UTC',
        'Z': 'UTC',
    }
    
    # Location to timezone mapping
    LOCATION_TIMEZONES = {
        'US-East': 'America/New_York',
        'US-Central': 'America/Chicago', 
        'US-Mountain': 'America/Denver',
        'US-Pacific': 'America/Los_Angeles',
        'US-Alaska': 'America/Anchorage',
        'US-Hawaii': 'Pacific/Honolulu',
        'UK': 'Europe/London',
        'EU-Central': 'Europe/Paris',
        'EU-Eastern': 'Europe/Helsinki',
        'Australia-East': 'Australia/Sydney',
        'Australia-West': 'Australia/Perth',
        'Japan': 'Asia/Tokyo',
        'China': 'Asia/Shanghai',
        'India': 'Asia/Kolkata',
    }
    
    @lazy_property
    def default_timezone(self):
        """Default timezone if none is set."""
        return pytz.timezone('UTC')
    
    def normalize_timezone_name(self, tz_name):
        """
        Convert common timezone abbreviations to proper timezone names.
        
        Args:
            tz_name (str): Timezone abbreviation or name
            
        Returns:
            str: Proper timezone name or None if not found
        """
        if not tz_name:
            return None
            
        # Convert to uppercase for matching
        tz_upper = tz_name.upper().strip()
        
        # Check if it's a common abbreviation
        if tz_upper in self.TIMEZONE_ALIASES:
            return self.TIMEZONE_ALIASES[tz_upper]
            
        # Check if it's a location code
        if tz_upper in self.LOCATION_TIMEZONES:
            return self.LOCATION_TIMEZONES[tz_upper]
            
        # Return as-is for direct pytz lookup
        return tz_name
    
    def get_player_timezone(self, player):
        """
        Get a player's timezone. First checks for an explicit timezone setting,
        then falls back to location-based timezone, then UTC.
        
        Args:
            player (Character or Account): The player whose timezone to get
            
        Returns:
            pytz.timezone: The timezone object for the player
        """
        # First check for explicit timezone setting
        tz_name = player.attributes.get('timezone', None)
        log_info(f"Player {player.key} timezone attribute: {tz_name}")
        
        if tz_name:
            normalized_tz = self.normalize_timezone_name(tz_name)
            log_info(f"Normalized timezone: {normalized_tz}")
            if normalized_tz:
                try:
                    return pytz.timezone(normalized_tz)
                except pytz.exceptions.UnknownTimeZoneError:
                    pass
                    
        # Then check for location-based timezone
        location = player.attributes.get('location', None)
        log_info(f"Player {player.key} location attribute: {location}")
        
        if location:
            normalized_tz = self.normalize_timezone_name(location)
            if normalized_tz:
                try:
                    return pytz.timezone(normalized_tz)
                except pytz.exceptions.UnknownTimeZoneError:
                    pass
                    
        # Fall back to UTC
        log_info(f"Falling back to UTC for player {player.key}")
        return self.default_timezone
        
    def convert_to_player_time(self, timestamp, player):
        """
        Convert a UTC timestamp to the player's local time.
        
        Args:
            timestamp (float): Unix timestamp in UTC
            player (Character or Account): The player whose timezone to use
            
        Returns:
            datetime: Localized datetime object
        """
        if timestamp is None:
            return None
            
        # Convert timestamp to datetime with explicit UTC timezone
        dt = datetime.fromtimestamp(timestamp).replace(tzinfo=pytz.UTC)
        log_info(f"Original UTC time: {dt}")
        
        # Get player's timezone
        player_tz = self.get_player_timezone(player)
        log_info(f"Player timezone: {player_tz}")
        
        # Convert to player's timezone
        local_time = dt.astimezone(player_tz)
        log_info(f"Converted local time: {local_time}")
        
        return local_time
        
    def format_player_time(self, timestamp, player, include_timezone=True):
        """
        Format a timestamp in the player's local time.
        
        Args:
            timestamp (float): Unix timestamp in UTC
            player (Character or Account): The player whose timezone to use
            include_timezone (bool, optional): Whether to include timezone name
            
        Returns:
            str: Formatted time string
        """
        if timestamp is None:
            return "Never"
            
        local_time = self.convert_to_player_time(timestamp, player)
        if include_timezone:
            # Use timezone abbreviation instead of full name
            return local_time.strftime("%Y-%m-%d %H:%M %Z")
        return local_time.strftime("%Y-%m-%d %H:%M")

# Create a global instance
TIME_MANAGER = TimeManager() 