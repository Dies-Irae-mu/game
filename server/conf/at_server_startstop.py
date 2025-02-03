"""
Server startstop hooks

This module contains functions called by Evennia at various
points during its startup, reload and shutdown sequence. It
allows for customizing the server operation as desired.

This module must contain at least these global functions:

at_server_init()
at_server_start()
at_server_stop()
at_server_reload_start()
at_server_reload_stop()
at_server_cold_start()
at_server_cold_stop()

"""


def at_server_init():
    """
    This is called first as the server is starting up, regardless of how.
    """


def at_server_start():
    """
    This is called every time the server starts up, regardless of
    how it was shut down.
    """
    try:
        from world.wod20th.forms import create_shifter_forms
        from world.wod20th.utils.init_db import load_stats
        from world.wod20th.locks import LOCK_FUNCS  # Import the lock functions
        from django.conf import settings
        from evennia.locks import lockfuncs
        from evennia.scripts.models import ScriptDB
        import os
        
        # Get the absolute path to the data directory
        data_dir = os.path.join(settings.GAME_DIR, 'data')
        
        create_shifter_forms()
        load_stats(data_dir)
        
        # Register the lock functions
        for name, func in LOCK_FUNCS.items():
            setattr(lockfuncs, name, func)
            
        # Initialize WeeklyXPScript if it's not already running
        if not ScriptDB.objects.filter(db_typeclass_path="world.wod20th.scripts.WeeklyXPScript").exists():
            from evennia import create_script
            try:
                script = create_script("world.wod20th.scripts.WeeklyXPScript", key="WeeklyXP", 
                                    interval=604800, persistent=True, desc="Weekly XP distribution script")
                if script:
                    print("Started WeeklyXPScript successfully")
                else:
                    print("Failed to create WeeklyXPScript")
            except Exception as e:
                print(f"Error creating WeeklyXPScript: {e}")
        
        print("Initialized shapeshifter forms, stats, and custom locks")
    except Exception as e:
        print(f"Error during initialization: {e}")



def at_server_stop():
    """
    This is called just before the server is shut down, regardless
    of it is for a reload, reset or shutdown.
    """
    pass


def at_server_reload_start():
    """
    This is called only when server starts back up after a reload.
    """
    pass


def at_server_reload_stop():
    """
    This is called only time the server stops before a reload.
    """
    pass


def at_server_cold_start():
    """
    This is called only when the server starts "cold", i.e. after a
    shutdown or a reset.
    """
    pass


def at_server_cold_stop():
    """
    This is called only when the server goes down due to a shutdown or
    reset.
    """
    pass
