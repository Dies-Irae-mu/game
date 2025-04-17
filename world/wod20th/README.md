# World of Darkness 20th Anniversary System

The World of Darkness 20th Anniversary (WoD20th) system provides the core mechanical framework for all supernatural character types in the Die Sirae game. This Django app implements the rules and mechanics from the 20th Anniversary editions of the World of Darkness roleplaying game system.

## Core Features

- **Character Sheet System**: Complete implementation of WoD20th character sheets
- **Stat Management**: Comprehensive stat tracking for all character types
- **Dice Rolling**: Implementation of the World of Darkness dice system
- **Shapeshifter Forms**: Management of different forms for shifter characters
- **Path Systems**: Implementation of Vampire paths and morality systems
- **Merit/Flaw System**: Management of character advantages and disadvantages

## Key Components

### Models

- `CharacterSheet`: Core model linking characters to their stats
- `Stat`: Flexible model for storing all character statistics
- `ShapeshifterForm`: Model for tracking shapeshifter forms and their effects
- `CharacterImage`: Storage for character portrait images
- `MokoleArchidTrait`: Special traits for Mokole dinosaur forms
- `Roster`: Organization of characters into spheres and groups

### Supernatural Types

The system supports all major World of Darkness character types:
- Vampire: The Masquerade
- Werewolf: The Apocalypse
- Mage: The Ascension
- Changeling: The Dreaming
- Wraith: The Oblivion
- Mortal and Mortal+

### Utility Functions

- `calculate_willpower()`: Calculate derived willpower based on virtues
- `calculate_road()`: Calculate path rating for vampires
- `get_clan_disciplines()`: Determine in-clan disciplines for vampires
- Various validation functions for different supernatural types

### Templates

Contains character sheet templates and related UI components for:
- Character creation
- Stat management
- Dice rolling interfaces
- Form shifting interfaces

### Management Commands

Django management commands for:
- Stat initialization
- XP allocation
- Character sheet maintenance

## Integration

The WoD20th system serves as the central mechanical framework that integrates with:
- Character system for basic character data
- Commands for dice rolling and stat manipulation
- XP system for character advancement
- Equipment system for item effects on character stats

## Usage

The system is used for:
- Character creation and advancement
- Dice-based conflict resolution
- Tracking character abilities and limitations
- Managing supernatural powers and transformations

## Development

When extending this system, refer to the STATS_README.md file for detailed information about stat structures and relationships. Follow the established patterns for adding new supernatural types or stat categories. 

## Example Command Output

When running the `load_wod20th_stats` command, you might see output like the following:

```
Successfully created stat: Strength
Stat Dexterity already exists. Skipping entry.
Error saving stat Stamina: [specific error message]
Finished processing all stats.
```

There are two methods when calling `load_wod20th_stats`, --dir and --file. 

`load_wod20th_stats --dir data/` will call everything in the data folder. You can use additional folders. The default for `load_wod20th_stats` will point to this folder.
`load_wod20th_stats --file hakken_gifts.json` will call everything in the hakken_gifts JSON file (for example). You can mix and match file names, but they must be in the data folder.

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