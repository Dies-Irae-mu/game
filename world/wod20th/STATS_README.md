# WoD20th Stats System

This document provides an overview of the World of Darkness 20th Anniversary Edition (WoD20th) stats system, including how to load, manage, and use stats within the Django-based Evennia game server.

## Overview

The WoD20th stats system allows you to manage character statistics such as attributes, abilities, and other traits. These stats are defined in JSON files and loaded into the Django database using a custom management command. The stats can then be accessed and manipulated through various Django views, templates, and commands.

## Prerequisites

- An Evennia project set up with the `world.wod20th` installation.
- The `Stat` model defined in `world.wod20th.models`.

## Loading Stats

To load stats from JSON files into the database, use the `load_wod20th_stats` management command. This command reads JSON files from a specified folder and imports the stats into the database.

### Usage

To use the command, run:

```shell
evennia load_wod20th_stats <path_to_folder>
```

Replace `<path_to_folder>` with the actual path to your folder containing the JSON files.

### JSON File Format

The JSON file should contain an array of stat objects. Each stat object should have the following structure:

```json
[
  {
    "name": "Strength",
    "description": "Physical power and muscle",
    "game_line": "Vampire",
    "category": "Physical",
    "stat_type": "Attribute",
    "values": [1, 2, 3, 4, 5],
    "lock_string": "view: is_splat(Vampire) OR is_splat(Mortal); edit: is_staff"
  },
  ...
]
```

## Models

The `Stat` model is defined in `world.wod20th.models` and includes fields such as `name`, `description`, `game_line`, `category`, `stat_type`, `values`, and others.

## Views

The stats can be viewed and managed through Django views. The following views are defined in `world.wod20th.views`:

- `stat_list`: Displays a list of all stats.
- `add_stat`: Allows users to add a new stat.

## Templates

The following templates are used to render the stats views:

- `stat_list.html`: Displays a list of stats.
- `add_stat.html`: Provides a form to add a new stat.

## Forms

The `StatForm` is used to handle the creation and editing of stats.

## Admin

The `Stat` model is registered with the Django admin site, allowing for easy management through the admin interface.

## Commands

Several commands interact with the stats system, including the `load_wod20th_stats` command for loading stats from JSON files.

## Example Command Output

When running the `load_wod20th_stats` command, you might see output like the following:

```
Successfully created stat: Strength
Stat Dexterity already exists. Skipping entry.
Error saving stat Stamina: [specific error message]
Finished processing all stats.
```

## Error Handling

The script handles several types of errors:

- File not found
- JSON decoding errors
- Missing required fields
- Invalid data types
- Database validation errors
- General exceptions during save operations

In case of database-related errors, the script will output the last SQL query and its parameters for debugging purposes.

## Notes

- Ensure your `Stat` model can handle all the fields provided in the JSON data.
- The script assumes that the combination of `name`, `game_line`, `category`, and `stat_type` is unique for each stat.
- Modify the `Stat` model import statement if your project structure differs.

## Character Typeclass Methods

The `Character` typeclass includes methods for setting, getting, and validating stats. These methods are defined in `typeclasses/characters.py`.

### Getting a Stat

To retrieve the value of a stat, use the `get_stat` method:

```python
def get_stat(self, category, stat_type, stat_name, temp=False):
    """
    Retrieve the value of a stat, considering instances if applicable.
    """
    if not hasattr(self.db, "stats") or not self.db.stats:
        self.db.stats = {}

    category_stats = self.db.stats.get(category, {})
    type_stats = category_stats.get(stat_type, {})

    for full_stat_name, stat in type_stats.items():
        # Check if the base stat name matches the given stat_name
        if full_stat_name.startswith(stat_name):
            return stat['temp'] if temp else stat['perm']
    return None
```
Reference: `typeclasses/characters.py` (startLine: 81, endLine: 95)

### Setting a Stat

To set the value of a stat, use the `set_stat` method:

```python
def set_stat(self, category, stat_type, stat_name, value, temp=False):
    """
    Set the value of a stat, considering instances if applicable.
    """
    if not hasattr(self.db, "stats") or not self.db.stats:
        self.db.stats = {}
    if category not in self.db.stats:
        self.db.stats[category] = {}
    if stat_type not in self.db.stats[category]:
        self.db.stats[category][stat_type] = {}
    if stat_name not in self.db.stats[category][stat_type]:
        self.db.stats[category][stat_type][stat_name] = {'perm': 0, 'temp': 0}
    if temp:
        self.db.stats[category][stat_type][stat_name]['temp'] = value
    else:
        self.db.stats[category][stat_type][stat_name]['perm'] = value
```
Reference: `typeclasses/characters.py` (startLine: 99, endLine: 114)

### Validating a Stat Value

To check if a value is valid for a stat, use the `check_stat_value` method:

```python
def check_stat_value(self, category, stat_type, stat_name, value, temp=False):
    """
    Check if a value is valid for a stat, considering instances if applicable.
    """
    from world.wod20th.models import Stat  
    stat = Stat.objects.filter(name=stat_name, category=category, stat_type=stat_type).first()
    if stat:
        stat_values = stat.values
        return value in stat_values['temp'] if temp else value in stat_values['perm']
    return False
```
Reference: `typeclasses/characters.py` (startLine: 116, endLine: 125)

## License

MIT