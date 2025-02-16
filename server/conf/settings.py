"""
Evennia settings file.

The available options are found in the default settings file found
here:

https://www.evennia.com/docs/latest/Setup/Settings-Default.html

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

If you want to share your game dir, including its settings, you can
put secret game- or server-specific settings in secret_settings.py.

"""

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *
import os
from evennia.contrib.base_systems import color_markups

# Configure logging
import logging.handlers

# Ensure log directory exists
LOG_DIR = os.path.join(GAME_DIR, "server", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Server log file with rotation
SERVER_LOG_FILE = os.path.join(LOG_DIR, "server.log")
SERVER_LOG_DAY_ROTATION = 7
SERVER_LOG_MAX_SIZE = 1000000

# Portal log file with rotation
PORTAL_LOG_FILE = os.path.join(LOG_DIR, "portal.log")
PORTAL_LOG_DAY_ROTATION = 7
PORTAL_LOG_MAX_SIZE = 1000000

# HTTP log file
HTTP_LOG_FILE = os.path.join(LOG_DIR, "http_requests.log")

# Lock warning log file
LOCKWARNING_LOG_FILE = os.path.join(LOG_DIR, "lockwarnings.log")

# Channel log settings
CHANNEL_LOG_NUM_TAIL_LINES = 20
CHANNEL_LOG_ROTATE_SIZE = 1000000

# Custom logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
        }
    },
    'handlers': {
        'server_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': SERVER_LOG_FILE,
            'maxBytes': SERVER_LOG_MAX_SIZE,
            'backupCount': SERVER_LOG_DAY_ROTATION,
            'formatter': 'verbose',
            'encoding': 'utf-8'
        },
        'portal_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': PORTAL_LOG_FILE,
            'maxBytes': PORTAL_LOG_MAX_SIZE,
            'backupCount': PORTAL_LOG_DAY_ROTATION,
            'formatter': 'verbose',
            'encoding': 'utf-8'
        }
    },
    'loggers': {
        'evennia': {
            'handlers': ['server_file'],
            'level': 'INFO',
            'propagate': False
        },
        'twisted': {
            'handlers': ['portal_file'],
            'level': 'INFO',
            'propagate': False
        }
    },
    'root': {
        'handlers': ['server_file'],
        'level': 'WARNING'
    }
}

SITE_ID = 1  # This tells Django which site object to use
DEBUG = True

ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
######################################################################
# Evennia base server config
######################################################################
SERVERNAME = "Dies Irae"
DEBUG = True
SITE_ID = 1
DEFAULT_CMDSETS = [
    'diesirae.commands.mycmdset.MyCmdset'
]

TELNET_PORTS = [4201]  
WEBSERVER_PORTS = [(4200, 4005)] 
WEBSOCKET_CLIENT_PORT = 4202
EVENNIA_ADMIN=False

# this is where the magic happens
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(GAME_DIR, 'server', 'evennia.db3'),
        'OPTIONS': {
            'timeout': 30,
            'isolation_level': None,
        }
    }
}

# define what the hell configuring sqlite means please
def _configure_sqlite(connection, **kwargs):
    cursor = connection.cursor()
    cursor.execute('PRAGMA journal_mode=WAL')
    cursor.execute('PRAGMA cache_size=-64000')  # 64MB cache
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.execute('PRAGMA synchronous=NORMAL')
    cursor.execute('PRAGMA mmap_size=33554432')  # 32MB memory-mapped I/O

# custom router via digitalocean
DATABASE_ROUTERS = []
CONN_MAX_AGE = 60

# can't believe this didn't exist even before these changes, note to self
DATABASES['default']['CONN_MAX_AGE'] = 60
"""

SERVERNAME = "beta.diesiraemu.com"
TELNET_INTERFACES = ['0.0.0.0']
WEBSERVER_INTERFACES = ['0.0.0.0']

if ENVIRONMENT == 'development':
  WEB_SOCKET_CLIENT_URL = "ws://localhost4005/websocket"
else:
  WEBSOCKET_CLIENT_URL = "wss://beta.diesiraemu.com/websocket"

ALLOWED_HOSTS = ['beta.diesiraemu.com', 'localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = ['https://beta.diesiraemu.com', 'http://beta.diesiraemu.com']
"""

BASE_ROOM_TYPECLASS = "typeclasses.rooms.RoomParent"
BASE_EXIT_TYPECLASS = "typeclasses.exits.Exit"
BASE_CHANNEL_TYPECLASS = "typeclasses.channels.Channel"

LOCK_FUNC_MODULES = [
    "evennia.locks.lockfuncs",
    "world.wod20th.locks"
]
MAX_NR_CHARACTERS = 5

CSRF_TRUSTED_ORIGINS = ['http://localhost:4005', 'http://localhost:4000', 'https://diesiraemu.com']

COLOR_ANSI_EXTRA_MAP = color_markups.MUX_COLOR_ANSI_EXTRA_MAP
COLOR_XTERM256_EXTRA_FG = color_markups.MUX_COLOR_XTERM256_EXTRA_FG
COLOR_XTERM256_EXTRA_BG = color_markups.MUX_COLOR_XTERM256_EXTRA_BG
COLOR_XTERM256_EXTRA_GFG = color_markups.MUX_COLOR_XTERM256_EXTRA_GFG
COLOR_XTERM256_EXTRA_GBG = color_markups.MUX_COLOR_XTERM256_EXTRA_GBG
COLOR_ANSI_XTERM256_BRIGHT_BG_EXTRA_MAP = color_markups.MUX_COLOR_ANSI_XTERM256_BRIGHT_BG_EXTRA_MAP

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'diesiraemu.com']
WEBSOCKET_CLIENT_URL = None  # Let Evennia handle this automatically

INSTALLED_APPS += (
    "world.wod20th",
    "wiki",
    "world.jobs",
    "world.plots",
    "world.hangouts",
)

# Use custom server config to prevent channel recreation
SERVER_CONFIG_CLASS = "server.conf.server_services_plugins.CustomServerConfig"

# Prevent automatic channel creation on server restart
DEFAULT_CHANNELS = []

######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")

# Add or update the command alias mapping in the settings file


"""
Color markups

Contribution, Griatch 2017

Additional color markup styles for Evennia (extending or replacing the default |r, |234 etc).


Installation:

Import the desired style variables from this module into mygame/server/conf/settings.py and add them
to these settings variables. Each are specified as a list, and multiple such lists can be added to
each variable to support multiple formats. Note that list order affects which regexes are applied
first. You must restart both Portal and Server for color tags to update.

Assign to the following settings variables:

    COLOR_ANSI_EXTRA_MAP - a mapping between regexes and ANSI colors
    COLOR_XTERM256_EXTRA_FG - regex for defining XTERM256 foreground colors
    COLOR_XTERM256_EXTRA_BG - regex for defining XTERM256 background colors
    COLOR_XTERM256_EXTRA_GFG - regex for defining XTERM256 grayscale foreground colors
    COLOR_XTERM256_EXTRA_GBG - regex for defining XTERM256 grayscale background colors
    COLOR_ANSI_BRIGHT_BG_EXTRA_MAP = ANSI does not support bright backgrounds; we fake
        this by mapping ANSI markup to matching bright XTERM256 backgrounds

    COLOR_NO_DEFAULT - Set True/False. If False (default), extend the default markup, otherwise
        replace it completely.


To add the {- "curly-bracket" style, add the following to your settings file, then reboot both
Server and Portal:

from evennia.contrib.base_systems import color_markups
COLOR_ANSI_EXTRA_MAP = color_markups.CURLY_COLOR_ANSI_EXTRA_MAP
COLOR_XTERM256_EXTRA_FG = color_markups.CURLY_COLOR_XTERM256_EXTRA_FG
COLOR_XTERM256_EXTRA_BG = color_markups.CURLY_COLOR_XTERM256_EXTRA_BG
COLOR_XTERM256_EXTRA_GFG = color_markups.CURLY_COLOR_XTERM256_EXTRA_GFG
COLOR_XTERM256_EXTRA_GBG = color_markups.CURLY_COLOR_XTERM256_EXTRA_GBG
COLOR_ANSI_BRIGHT_BG_EXTRA_MAP = color_markups.CURLY_COLOR_ANSI_BRIGHT_BG_EXTRA_MAP


To add the %c- "mux/mush" style, add the following to your settings file, then reboot both Server
and Portal:

from evennia.contrib.base_systems import color_markups
COLOR_ANSI_EXTRA_MAP = color_markups.MUX_COLOR_ANSI_EXTRA_MAP
COLOR_XTERM256_EXTRA_FG = color_markups.MUX_COLOR_XTERM256_EXTRA_FG
COLOR_XTERM256_EXTRA_BG = color_markups.MUX_COLOR_XTERM256_EXTRA_BG
COLOR_XTERM256_EXTRA_GFG = color_markups.MUX_COLOR_XTERM256_EXTRA_GFG
COLOR_XTERM256_EXTRA_GBG = color_markups.MUX_COLOR_XTERM256_EXTRA_GBG
COLOR_ANSI_BRIGHT_BGS_EXTRA_MAP = color_markups.CURLY_COLOR_ANSI_BRIGHT_BGS_EXTRA_MAP


"""

# ANSI constants (copied from evennia.utils.ansi to avoid import)

_ANSI_BEEP = "\07"
_ANSI_ESCAPE = "\033"
_ANSI_NORMAL = "\033[0m"

_ANSI_UNDERLINE = "\033[4m"
_ANSI_HILITE = "\033[1m"
_ANSI_UNHILITE = "\033[22m"
_ANSI_BLINK = "\033[5m"
_ANSI_INVERSE = "\033[7m"
_ANSI_INV_HILITE = "\033[1;7m"
_ANSI_INV_BLINK = "\033[7;5m"
_ANSI_BLINK_HILITE = "\033[1;5m"
_ANSI_INV_BLINK_HILITE = "\033[1;5;7m"

# Foreground colors
_ANSI_BLACK = "\033[30m"
_ANSI_RED = "\033[31m"
_ANSI_GREEN = "\033[32m"
_ANSI_YELLOW = "\033[33m"
_ANSI_BLUE = "\033[34m"
_ANSI_MAGENTA = "\033[35m"
_ANSI_CYAN = "\033[36m"
_ANSI_WHITE = "\033[37m"

# Background colors
_ANSI_BACK_BLACK = "\033[40m"
_ANSI_BACK_RED = "\033[41m"
_ANSI_BACK_GREEN = "\033[42m"
_ANSI_BACK_YELLOW = "\033[43m"
_ANSI_BACK_BLUE = "\033[44m"
_ANSI_BACK_MAGENTA = "\033[45m"
_ANSI_BACK_CYAN = "\033[46m"
_ANSI_BACK_WHITE = "\033[47m"

# Formatting Characters
_ANSI_RETURN = "\r\n"
_ANSI_TAB = "\t"
_ANSI_SPACE = " "


#############################################################
#
# %c - MUX/MUSH style markup. This was Evennia's first
# color markup style. It was phased out due to % being used
# in Python formatting operations.
#
# %ch%cr, %cr - bright/dark red foreground
# %ch%cR, %cR- bright/dark red background
# %c500, %c[500 - XTERM256 red foreground/background
# %c=w, %c[=w - XTERM256 greyscale foreground/background
#
#############################################################

MUX_COLOR_ANSI_EXTRA_MAP = [
    (r"%cn", _ANSI_NORMAL),  # reset
    (r"%ch", _ANSI_HILITE),  # highlight
    (r"%r", _ANSI_RETURN),  # line break
    (r"%R", _ANSI_RETURN),  #
    (r"%t", _ANSI_TAB),  # tab
    (r"%T", _ANSI_TAB),  #
    (r"%b", _ANSI_SPACE),  # space
    (r"%B", _ANSI_SPACE),
    (r"%cf", _ANSI_BLINK),  # annoying and not supported by all clients
    (r"%ci", _ANSI_INVERSE),  # invert
    (r"%cr", _ANSI_RED),
    (r"%cg", _ANSI_GREEN),
    (r"%cy", _ANSI_YELLOW),
    (r"%cb", _ANSI_BLUE),
    (r"%cm", _ANSI_MAGENTA),
    (r"%cc", _ANSI_CYAN),
    (r"%cw", _ANSI_WHITE),
    (r"%cx", _ANSI_BLACK),
    (r"%cR", _ANSI_BACK_RED),
    (r"%cG", _ANSI_BACK_GREEN),
    (r"%cY", _ANSI_BACK_YELLOW),
    (r"%cB", _ANSI_BACK_BLUE),
    (r"%cM", _ANSI_BACK_MAGENTA),
    (r"%cC", _ANSI_BACK_CYAN),
    (r"%cW", _ANSI_BACK_WHITE),
    (r"%cX", _ANSI_BACK_BLACK),
]

MUX_COLOR_XTERM256_EXTRA_FG = [r"%c([0-5])([0-5])([0-5])"]  # %c123 - foreground colour
MUX_COLOR_XTERM256_EXTRA_BG = [r"%c\[([0-5])([0-5])([0-5])"]  # %c[123 - background colour
MUX_COLOR_XTERM256_EXTRA_GFG = [r"%c=([a-z])"]  # %c=a - greyscale foreground
MUX_COLOR_XTERM256_EXTRA_GBG = [r"%c\[=([a-z])"]  # %c[=a - greyscale background

MUX_COLOR_ANSI_XTERM256_BRIGHT_BG_EXTRA_MAP = [
    (r"%ch%cR", r"%c[500"),
    (r"%ch%cG", r"%c[050"),
    (r"%ch%cY", r"%c[550"),
    (r"%ch%cB", r"%c[005"),
    (r"%ch%cM", r"%c[505"),
    (r"%ch%cC", r"%c[055"),
    (r"%ch%cW", r"%c[555"),  # white background
    (r"%ch%cX", r"%c[222"),  # dark grey background
]

AT_SERVER_STARTSTOP_MODULE = "world.wod20th.scripts"

# Import our custom lock functions
from world.wod20th.locks import LOCK_FUNCS as WOD_LOCK_FUNCS

# Lock function modules
LOCK_FUNC_MODULES = [
    "evennia.locks.lockfuncs",
    "world.wod20th.locks"
]

# Add our custom lock functions to Evennia's lock system
LOCK_FUNCS = {
    # Basic type checks
    "has_splat": WOD_LOCK_FUNCS["has_splat"],
    "has_type": WOD_LOCK_FUNCS["has_type"],
    "subscribed": WOD_LOCK_FUNCS["subscribed"],
    "tenant": WOD_LOCK_FUNCS["tenant"],

    # Primary abilities
    "has_talent": WOD_LOCK_FUNCS["has_talent"],
    "has_skill": WOD_LOCK_FUNCS["has_skill"],
    "has_knowledge": WOD_LOCK_FUNCS["has_knowledge"],
    
    # Secondary abilities
    "has_secondary_talent": WOD_LOCK_FUNCS["has_secondary_talent"],
    "has_secondary_skill": WOD_LOCK_FUNCS["has_secondary_skill"],
    "has_secondary_knowledge": WOD_LOCK_FUNCS["has_secondary_knowledge"],
    
    # Advantages
    "has_merit": WOD_LOCK_FUNCS["has_merit"],
    
    # Vampire
    "has_clan": WOD_LOCK_FUNCS["has_clan"],

    # Garou/some shifters
    "has_tribe": WOD_LOCK_FUNCS["has_tribe"],
    "has_auspice": WOD_LOCK_FUNCS["has_auspice"],

    # Mage stuff
    "has_tradition": WOD_LOCK_FUNCS["has_tradition"],
    "has_affiliation": WOD_LOCK_FUNCS["has_affiliation"],
    "has_convention": WOD_LOCK_FUNCS["has_convention"],
    "has_nephandi_faction": WOD_LOCK_FUNCS["has_nephandi_faction"],
    
    # Changeling specifics
    "has_court": WOD_LOCK_FUNCS["has_court"],
    "has_kith": WOD_LOCK_FUNCS["has_kith"],

}

# Media files (Uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(GAME_DIR, 'web', 'media')

# Ensure the media directory exists
os.makedirs(MEDIA_ROOT, exist_ok=True)

######################################################################
# Logging configuration
######################################################################

# Use our custom logger
from .logger import get_robust_file_observer

# Simple observer functions that return new instances each time
PORTAL_LOG_OBSERVER = lambda: get_robust_file_observer("portal.log", LOG_DIR)
SERVER_LOG_OBSERVER = lambda: get_robust_file_observer("server.log", LOG_DIR)

def at_server_start():
    """
    This is called every time the server starts up.
    """
    # Import here to avoid circular imports
    from world.wod20th.scripts import start_all_scripts
    start_all_scripts()

AT_SERVER_START_HOOK = "server.conf.settings.at_server_start"
