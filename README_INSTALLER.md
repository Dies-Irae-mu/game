# Dies Irae Installer

This installer script automates the process of setting up a Dies Irae game in an Evennia environment. It handles all the necessary steps from checking prerequisites to starting the game.

## Prerequisites

The installer will check for these requirements and attempt to install them if missing:

- Python 3
- pip
- git
- Evennia

## Usage

1. Download the `install.sh` script
2. Make it executable: `chmod +x install.sh`
3. Run the installer with your desired game name: `./install.sh my_wod_game`

## What the Installer Does

The installer automates all the steps described in the main README.md:

1. Checks for required software (Python, pip, git)
2. Installs Evennia if not already installed
3. Installs required dependencies (ephem, markdown2, pillow, requests)
4. Creates a new Evennia game with your specified name
5. Clones the Dies Irae repository and copies files to your game directory
6. Updates settings.py to include required apps
7. Clears any existing migration files
8. Runs database migrations
9. Loads World of Darkness 20th Anniversary stats
10. Starts the game server

## After Installation

Once installation is complete, you can access your game at:
- Web client: http://localhost:4001
- Telnet: localhost:4000

To stop the game: `cd your_game_name && evennia stop`
To start the game: `cd your_game_name && evennia start`

## Customizing Your Game

After installation, you may want to customize your game:

1. Change the game name from "Dies Irae" to your preferred name using find and replace
2. Modify the `VALID_SPLATS` in `world/wod20th/utils/stat_mappings.py` to choose which supernatural types are available
3. Remove data files for supernatural types you don't need (keeping vampire files as they contain base information)

## Troubleshooting

If you encounter any issues during installation:

1. Check the error messages displayed by the installer
2. Ensure you have proper permissions to create directories and install packages
3. Verify your internet connection is working properly
4. Make sure you're running the script in a directory where you have write permissions

For more detailed information about the game structure and systems, refer to the wiki help system documentation.
