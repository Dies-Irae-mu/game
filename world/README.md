# World Module

This folder is meant as a miscellaneous folder for all that other stuff
related to the game. Code which are not commands or typeclasses go
here, like custom economy systems, combat code, batch-files etc. 

You can restructure and even rename this folder as best fits your
sense of organisation. Just remember that if you add new sub
directories, you must add (optionally empty) `__init__.py` files in
them for Python to be able to find the modules within.

## Subdirectories

The world module contains several specialized Django apps that implement various game systems:

### Equipment

The Equipment system manages all items, weapons, armor, vehicles, and supernatural devices in the game. It provides inventory management, equipment effects, and staff approval workflows for restricted items.

[View Equipment Documentation](equipment/README.md)

### Groups

The Groups system manages character organizations, factions, and social structures. It handles group membership, leadership roles, and integration with character rosters.

[View Groups Documentation](groups/README.md)

### Hangouts

The Hangouts system provides a categorized directory of in-game roleplay locations, tracking player population and controlling location visibility based on character type.

[View Hangouts Documentation](hangouts/README.md)

### Jobs

The Jobs system is a comprehensive ticket management system for handling player requests, bug reports, and staff tasks. It supports queues, assignment workflows, and templated request formats.

[View Jobs Documentation](jobs/README.md)

### Plots

The Plots system manages storyteller-driven plot lines and story arcs, including session organization, participant tracking, and reward management for completed plots.

[View Plots Documentation](plots/README.md)

### Wod20th

The World of Darkness 20th Anniversary (WoD20th) system provides the core mechanical framework for all supernatural character types, implementing stats, character sheets, and game mechanics.

[View WoD20th Documentation](wod20th/README.md)

## Additional Files

- `prototypes.py` - Object prototypes for spawning game entities
- `help_entries.py` - In-game help system entries
- `batch_cmds.ev` - Batch command file for initial setup 
