# WoD20th Stats Loader


This Django management command allows you to load World of Darkness 20th Anniversary Edition (WoD20th) stats from a JSON file into your Django database.

## Overview

The `load_wod20th_stats` command reads a JSON file containing stat data for the World of Darkness 20th Anniversary Edition game and imports it into the database using the `Stat` model.

## Prerequisites

- Django project set up with the `world.wod20th` app installed
- `Stat` model defined in `world.wod20th.models`

## Usage

To use this command, run:

```shell
python manage.py load_wod20th_stats <path_to_folder>
```

Replace `<path_to_folder>` with the actual path to your folder containing the JSON files.

## JSON File Format

The JSON file should contain an array of stat objects. Each stat object should have the following structure:

```json
[
  {
    "name": "Strength",
    "description": "Physical power and muscle",
    "game_line": "Vampire",
    "category": "Physical",
    "stat_type": "Attribute",
    "values": [1, 2, 3, 4, 5]
  },
  ...
]
```

## Features

- [x] **Data Validation**: The script performs various checks to ensure data integrity before importing.
- [x] **Duplicate Prevention**: Skips stats that already exist in the database.
- [x] **Error Handling**: Provides detailed error messages for various scenarios (file not found, JSON decode errors, validation errors, etc.).
- [x] **Verbose Output**: Logs the progress and results of each stat import attempt.

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

> **Important:** Make sure your `Stat` model can handle all the fields provided in the JSON data.

- The script assumes that the combination of `name`, `game_line`, `category`, and `stat_type` is unique for each stat.
- Modify the `Stat` model import statement if your project structure differs.

## Contributing

Feel free to fork this script and adapt it to your needs. If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

MIT

---

### Related Django Files

This script interacts with the following Django files:

- `models.py`:
  ```python
  from world.wod20th.models import Stat
  ```
- `settings.py`: Ensure `world.wod20th` is in your `INSTALLED_APPS`

### Example Command Output

```
Successfully created stat: Strength
Stat Dexterity already exists. Skipping entry.
Error saving stat Stamina: [specific error message]
Finished processing all stats.
```