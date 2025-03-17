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
from world.wod20th.locks import LOCK_FUNCS as WOD_LOCK_FUNCS
import warnings

warnings.filterwarnings('ignore', category=RuntimeWarning, module='django.db.models.base') # Required for Django 4.x logging.

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
    'commands.mycmdset.MyCmdset'
]

MAX_NR_CHARACTERS = 1 # Setting multiple characters can be a mess for players and channels. It's best to keep this at 1.
DEFAULT_CHANNELS = [] # This is a list of channels that will be created when a new character is created. Leave blank until you have channels.
MAX_ACCOUNTS = 10000
BASE_ROOM_TYPECLASS = "typeclasses.rooms.RoomParent"
BASE_EXIT_TYPECLASS = "typeclasses.exits.Exit"
BASE_CHANNEL_TYPECLASS = "typeclasses.channels.Channel"

INSTALLED_APPS += (
    "world.wod20th",
    "wiki",
    "world.jobs",
    "web.character",
    "world.plots",
    "world.hangouts",
)

######################################################################
# Generic sqlite3 database. 
# Secret settings should override this, but it's
# not necessary for local development since we
# don't update settings.py from git.
######################################################################
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(GAME_DIR, 'evennia.db3'),
    }
}

"""
LOCKS

Locks are managed in the world.wod20th.locks module. This is for our
primary locks, any additional adjustments to commands, such as in +setlock
should be made in the command file.
"""

LOCK_FUNC_MODULES = [
    "evennia.locks.lockfuncs",
    "world.wod20th.locks"
]

LOCK_FUNCS = {
    # Basic type checks
    "has_splat": WOD_LOCK_FUNCS["has_splat"],
    "has_type": WOD_LOCK_FUNCS["has_type"],
    "subscribed": WOD_LOCK_FUNCS["subscribed"],
    "tenant": WOD_LOCK_FUNCS["tenant"],
    "has_wyrm_taint": WOD_LOCK_FUNCS["has_wyrm_taint"],

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

"""
WEB CLIENT/SERVER CONFIGURATION
"""
ENVIRONMENT = "development"
# Update the WEBSOCKET_CLIENT_URL configuration
if ENVIRONMENT == 'production':
    WEBSOCKET_CLIENT_URL = "ws://localhost:4202/websocket"
elif ENVIRONMENT == 'development':
    WEBSOCKET_CLIENT_URL = "ws://localhost:4202/websocket"

AT_SERVER_STARTSTOP_MODULE = "world.wod20th.scripts"
# Server configuration
TELNET_INTERFACES = ['0.0.0.0']
WEBSERVER_INTERFACES = ['0.0.0.0']
WEBSOCKET_CLIENT_INTERFACE = '0.0.0.0'

# Port configuration
TELNET_PORTS = [4201]
WEBSERVER_PORTS = [(4200, 4005)]

# Web client settings
WEBCLIENT_MAX_MESSAGE_LENGTH = 100000 # This is the maximum number of characters that can be sent in a single message.
WEBCLIENT_RECONNECT_DELAY = 2000 # This is the delay in milliseconds between reconnect attempts.
WEBCLIENT_KEEPALIVE = True # This is a boolean that determines whether the web client will send keepalive messages to the server.

# Security settings
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
EVENNIA_ADMIN=False # Determines the appearance and use of admin commands on the webserver. If you change this it'll change the /admin portal.

# Static files configuration (keep this in one place)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(GAME_DIR, 'static')
STATICFILES_DIRS = [
    os.path.join(GAME_DIR, "web", "static"),
    os.path.join(GAME_DIR, "wiki", "static"),
]

# WIKI MEDIA CONFIGURATION

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(GAME_DIR, 'media')


########################################################
# GLOBAL SCRIPTS CONFIGURATION
# This section is for global persistent scripts.
# These will run on all connected clients.
########################################################
GLOBAL_SCRIPTS = {
    "weekly_xp_award": {
        "typeclass": "world.wod20th.scripts.weekly_xp.WeeklyXPScript",
        "desc": "Awards weekly XP to active characters",
        "interval": 7 * 24 * 60 * 60,  # 1 week in seconds
        "persistent": True,
        "start_delay": True
    },
    "xp_monitor": {
        "typeclass": "world.wod20th.scripts.weekly_xp.XPMonitor",
        "desc": "Monitors XP changes",
        "interval": 60,  # Check every minute
        "persistent": True
    }
}

###########################################################
# Non-persistent script / task configuration
# Scripts placed in the import will likely reset on server start.
# I've generally had trouble with persistent scripts resetting on server start
# when not placed in the GLOBAL_SCRIPTS dictionary.
# Make sure to place persistent scripts in the GLOBAL_SCRIPTS dictionary.
###########################################################
def at_server_start():
    """
    This is called every time the server starts up.
    """
    # Import your scripts here to avoid circular imports
    from world.wod20th.scripts import start_all_scripts
    start_all_scripts()

AT_SERVER_START_HOOK = "server.conf.settings.at_server_start"

# Session settings
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 3600 * 24 * 7  # 7 days

# Session security
SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
CSRF_COOKIE_SECURE = True    # Only send CSRF token over HTTPS
SECURE_SSL_REDIRECT = True   # Redirect HTTP to HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

"""
BASE ANSI MARKUP CONFIGURATION
See below for more specific color markup configurations.

Note that this is not the only place to set %r/%t replacements, as that needs to also be done
within each file that uses the MUX carriage return or tab style.
"""
COLOR_ANSI_EXTRA_MAP = color_markups.MUX_COLOR_ANSI_EXTRA_MAP
COLOR_XTERM256_EXTRA_FG = color_markups.MUX_COLOR_XTERM256_EXTRA_FG
COLOR_XTERM256_EXTRA_BG = color_markups.MUX_COLOR_XTERM256_EXTRA_BG
COLOR_XTERM256_EXTRA_GFG = color_markups.MUX_COLOR_XTERM256_EXTRA_GFG
COLOR_XTERM256_EXTRA_GBG = color_markups.MUX_COLOR_XTERM256_EXTRA_GBG
COLOR_ANSI_XTERM256_BRIGHT_BG_EXTRA_MAP = color_markups.MUX_COLOR_ANSI_XTERM256_BRIGHT_BG_EXTRA_MAP

"""
LOCAL CONFIGURATION DOES NOT USE SECRET SETTINGS AT THIS TIME.

######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")

# Add or update the command alias mapping in the settings file
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

######################################################################
# Logging configuration
#
# This is designed to clear the log files every time the server starts
# to prevent them from growing too large.
######################################################################

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

# Configure log rotation
PORTAL_LOG_ROTATE_SIZE = 1000000  # Rotate at 1 MB
PORTAL_LOG_FILES = 10  # Keep 10 backup files
SERVER_LOG_ROTATE_SIZE = 1000000  # Rotate at 1 MB
SERVER_LOG_FILES = 10  # Keep 10 backup files

