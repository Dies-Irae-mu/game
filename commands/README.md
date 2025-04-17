# Commands Directory

This folder holds modules for implementing one's own commands and
command sets. All the modules' classes are essentially empty and just
imports the default implementations from Evennia; so adding anything
to them will start overloading the defaults. 

You can change the organisation of this directory as you see fit, just
remember that if you change any of the default command set classes'
locations, you need to add the appropriate paths to
`server/conf/settings.py` so that Evennia knows where to find them.
Also remember that if you create new sub directories you must put
(optionally empty) `__init__.py` files in there so that Python can
find your modules.

## Command Files Overview

This directory contains command implementations for Die Sirae, an Evennia-based MUD game. Below is a description of each file's purpose and functionality:

### Core Files

- `default_cmdsets.py` - Defines the main command sets that group commands for characters, accounts, unlogged-in users, and sessions
- `command.py` - Base command classes that can be extended for custom commands
- `__init__.py` - Empty file that makes the directory a Python package

### Character Commands

- `CmdSheet.py` - Character sheet display command
- `CmdSelfStat.py` - Commands for viewing and managing character stats
- `CmdRoll.py` - Dice rolling system for skill checks and other tests
- `CmdXP.py` - Experience point management commands
- `CmdXPCost.py` - Commands for calculating and displaying XP costs
- `CmdCheck.py` - Commands for performing various character checks

### Communication Commands

- `CmdSay.py` - In-character speaking command
- `CmdPose.py` - Emote/pose commands for describing character actions
- `CmdEmit.py` - Global emitting for scenes and events
- `CmdPoseBreak.py` - Command for pose formatting
- `CmdPage.py` - Private messaging between players
- `CmdOOC.py` - Out-of-character communication
- `communication.py` - Various communication commands like meet, summon, etc.
- `comms.py` - Channel communication system
- `CmdLFRP.py` - "Looking For Roleplay" flag system

### World of Darkness Specific Commands

- `CmdShift.py` - Shape-shifting for werewolves and other shapeshifters
- `CmdUmbraInteraction.py` - Commands for interacting with the spirit world (Umbra)
- `CmdChangelingInteraction.py` - Commands specific to Changeling characters
- `CmdBanality.py` - System for managing Changeling banality
- `CmdRenown.py` - Werewolf renown management
- `CmdWeather.py` - Weather system commands
- `CmdPump.py` - Blood pool management for Vampires

### Health and Combat Commands

- `CmdHeal.py` - Commands for healing damage
- `CmdHurt.py` - Commands for inflicting damage
- `CmdInit.py` - Initiative tracking for combat scenes

### Character Description and Customization

- `CmdGradient.py` - Commands for adding gradient colors to names
- `CmdShortDesc.py` - Short character description management
- `CmdMultidesc.py` - Multiple descriptions for different situations
- `CmdFaeDesc.py` - Special descriptions for Changeling characters

### Game Management Commands

- `admin.py` - Administrative commands for game management
- `staff_commands.py` - Commands available to staff members
- `CmdStaff.py` - Staff tools and utilities
- `CmdHelp.py` - Custom help system
- `CmdAlts.py` - Alternative character management
- `CmdWho.py` - Commands to see who is online
- `where.py` - Commands to locate characters in the game
- `CmdRoster.py` - Character roster management
- `CmdWatch.py` - Commands for observing characters or areas
- `CmdAlias.py` - Command aliasing system
- `CmdSpecialties.py` - Character specialties management

### Building and Environment Commands

- `building.py` - Room and object creation commands
- `housing.py` - Player housing system
- `CmdEquip.py` - Equipment and inventory management
- `CmdHangouts.py` - Management of player hangout locations
- `CmdPlots.py` - Story plot management tools
- `CmdRoomLog.py` - Room logging functionality

### Utility Commands

- `CmdNotes.py` - Note-taking system
- `CmdEvents.py` - Event scheduling system
- `CmdFinger.py` - Character information lookup
- `CmdInfo.py` - Game information commands
- `CmdLanguage.py` - Language system implementation
- `CmdArchid.py` - Archetype identification system
- `CmdNPC.py` - Non-player character management
- `unfindable.py` - Commands to make characters unfindable
- `CmdUnpuppet.py` - Commands to stop puppeting a character

### Subsystem Directories

- `bbs/` - Bulletin Board System commands
- `jobs/` - Staff job system commands
- `oss/` - Off-Screen System commands (currently unused)
- `tests/` - Test commands and utilities
- `documentation/` - Command documentation files

### Character Generation

- `chargen.py` - Character generation commands
- `CmdSpendGain.py` - Point spending during character creation
- `requests.py` - Character request system
- `groups_commands.py` - Character group management

## Usage

Most commands are accessed in-game by typing their name, like `+sheet` for character sheet display. Many commands have aliases for convenience. See the individual command files or use the in-game help system (`help <command>`) for detailed usage information.

To add new commands, create a new Python file with your command class and add it to the appropriate command set in `default_cmdsets.py`.
