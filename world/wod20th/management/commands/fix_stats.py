"""
Script to fix character stats by converting string numbers to integers
and cleaning up duplicate flaw entries.
"""
from evennia import search_object
from world.wod20th.models import Stat

def fix_numeric_value(value):
    """Convert string numbers to integers if possible."""
    if isinstance(value, dict):
        if 'perm' in value and 'temp' in value:
            try:
                value['perm'] = int(value['perm'])
                value['temp'] = int(value['temp'])
            except (ValueError, TypeError):
                pass
    return value

def should_be_numeric(category, stat_type):
    """Check if a stat should be numeric based on its category and type."""
    numeric_categories = {
        'attributes': True,
        'abilities': True,
        'backgrounds': True,
        'powers': True,
        'merits': True,
        'flaws': True,
        'virtues': True,
        'pools': True
    }
    
    if category in numeric_categories:
        # Special case for charms, which are powers but not numeric
        if stat_type == 'charm':
            return False
        return True
    return False

def fix_character_stats(character):
    """Fix stats for a single character."""
    if not hasattr(character, 'db') or not hasattr(character.db, 'stats'):
        return False, "Character has no stats"
    
    stats = character.db.stats
    changes_made = False
    
    # First, handle any duplicate flaws
    if 'flaw' in stats and 'flaw' in stats['flaw']:
        # Move any flaws to their proper category
        for flaw_name, flaw_value in list(stats['flaw']['flaw'].items()):
            # Find the proper category for this flaw
            stat = Stat.objects.filter(name__iexact=flaw_name).first()
            if stat and stat.category == 'flaws':
                # Initialize flaws category if needed
                if 'flaws' not in stats:
                    stats['flaws'] = {}
                if stat.stat_type not in stats['flaws']:
                    stats['flaws'][stat.stat_type] = {}
                
                # Move the flaw to its proper location
                stats['flaws'][stat.stat_type][flaw_name] = flaw_value
                del stats['flaw']['flaw'][flaw_name]
                changes_made = True
        
        # Clean up empty flaw categories
        if not stats['flaw']['flaw']:
            del stats['flaw']['flaw']
        if not stats['flaw']:
            del stats['flaw']
    
    # Now convert string numbers to integers
    for category in list(stats.keys()):
        if isinstance(stats[category], dict):
            for stat_type in list(stats[category].keys()):
                if isinstance(stats[category][stat_type], dict):
                    for stat_name, stat_value in list(stats[category][stat_type].items()):
                        if should_be_numeric(category, stat_type):
                            old_value = str(stat_value)
                            new_value = fix_numeric_value(stat_value)
                            if new_value != stat_value:
                                stats[category][stat_type][stat_name] = new_value
                                changes_made = True
    
    # Save changes if any were made
    if changes_made:
        character.db.stats = stats
    
    return changes_made, "Stats fixed successfully"

def fix_all_stats():
    """Fix stats for all characters."""
    results = []
    characters = search_object("*", typeclass='typeclasses.characters.Character', global_search=True)
    
    for character in characters:
        try:
            changed, message = fix_character_stats(character)
            if changed:
                results.append(f"Fixed stats for {character.name}")
        except Exception as e:
            results.append(f"Error fixing stats for {character.name}: {str(e)}")
    
    return results

# Command function for staff to run the fix
def do_fix_stats(caller, *args):
    """Staff command to fix character stats."""
    if not caller.check_permstring("Admin") and not caller.check_permstring("Builder"):
        caller.msg("You don't have permission to use this command.")
        return
    
    if args and args[0]:
        # Fix specific character
        target = caller.search(args[0], global_search=True)
        if not target:
            return
        
        changed, message = fix_character_stats(target)
        if changed:
            caller.msg(f"Fixed stats for {target.name}")
        else:
            caller.msg(f"No changes needed for {target.name}")
    else:
        # Fix all characters
        results = fix_all_stats()
        for result in results:
            caller.msg(result) 