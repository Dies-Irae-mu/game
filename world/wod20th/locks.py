# mygame/locks.py


from world.wod20th.models import Stat


def is_splat(accessing_obj, accessed_obj, *args, **kwargs):
    """
    Check if the accessing_obj has the same splat as the accessed_obj.
    """
    splat = args[0]
    
    if splat:
        return accessing_obj.get_stat('other', 'splat', 'Splat') == splat
    return False


def has_stat(accessing_obj, accessed_obj, *args, **kwargs):
    """
    Check if the accessing_obj has a specified stat.
        has_stat(<stat_name>, <stat_value>)
      """
    
   # We're going ot use the Stat db for this one to look  up the stat
   # Going to use args to pass in the stat name and value

    stat_name = args[0]
    stat_value = args[1]
    stat = Stat.objects.get(name_icontains=stat_name)
    
    
    return accessing_obj.get_stat(stat.category, stat.stat_type, stat.name) == stat_value