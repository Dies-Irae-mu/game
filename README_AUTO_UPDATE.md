# Evennia Auto-Update System

A robust system for automatically updating and managing an Evennia MUD server with backup capabilities and Discord notifications.

## Features

- **Automated Updates**: Pulls from your git repository at configurable intervals
- **Backup System**: Creates backups before updates with easy restoration
- **Discord Notifications**: Sends real-time notifications about server status
- **Error Recovery**: Multiple fallback mechanisms if updates fail
- **Configurable**: Easy setup with a single configuration file

## Requirements

- Linux server (tested on Ubuntu 20.04+)
- Git
- Conda or Miniconda
- Evennia MUD server
- Bash shell
- `curl` for Discord notifications

## Installation

1. The auto-update scripts are included in your game repository and will be automatically pulled when you update your game.

2. Run the setup script:
   ```bash
   ./Scripts/setup.sh -d /path/to/game -e your_conda_env -b main -i 60 -w "https://discord.com/api/webhooks/your-webhook-url"
   ```

   Options:
   - `-d, --directory`: Game directory path (default: /root/game)
   - `-e, --env`: Conda environment name (default: game_py311)
   - `-b, --branch`: Git branch to pull from (default: main)
   - `-i, --interval`: Update interval in minutes (default: 60)
   - `-w, --webhook`: Discord webhook URL (optional)
   - `-h, --help`: Display help message

3. The setup script will:
   - Create a configuration file (`config.sh`)
   - Set up log files
   - Run `setup_permissions.sh` to set up proper permissions
   - Make all scripts executable
   - Add a cron job for automatic updates

## Configuration

The system uses a central configuration file (`Scripts/config.sh`) that is automatically generated during setup. This file is not managed by git and should be added to your `.gitignore` file to prevent it from being committed.

You can edit the configuration file at any time to change settings, but be aware that running the setup script again will overwrite it with the new settings.

### Example Configuration File

The following is an example of what the generated `config.sh` file will look like:

```bash
#!/bin/bash

# Evennia Auto-Update System Configuration
# This file contains configuration variables for all scripts
# Edit this file to configure your environment

# Game directory path
GAME_DIRECTORY="/root/game"

# Conda environment name
CONDA_ENV="game_py311"

# Git branch to pull from
GIT_BRANCH="main"

# Update interval in minutes
UPDATE_INTERVAL=60

# Discord webhook URL
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/your-webhook-url"

# Backup directory (relative to game directory)
BACKUP_DIR="../backups"

# Log files
LOG_DIR="/var/log"
UPDATE_LOG="$LOG_DIR/evennia_update.log"
RESTART_LOG="$LOG_DIR/evennia_restart.log"
BACKUP_LOG="$LOG_DIR/evennia_backup.log"
RESTORE_LOG="$LOG_DIR/evennia_restore.log"

# Script directory (automatically determined)
SCRIPT_DIR="/path/to/evennia-auto-update/Scripts"

# Export variables for use in other scripts
export GAME_DIRECTORY
export CONDA_ENV
export GIT_BRANCH
export UPDATE_INTERVAL
export DISCORD_WEBHOOK_URL
export BACKUP_DIR
export LOG_DIR
export UPDATE_LOG
export RESTART_LOG
export BACKUP_LOG
export RESTORE_LOG
export SCRIPT_DIR
```

## Scripts

### `setup.sh`

Sets up the auto-update system by creating a configuration file and setting up the necessary permissions and cron jobs.

### `setup_permissions.sh`

Sets up the proper permissions for all scripts and log files. This script is called by `setup.sh` and should not be run directly.

### `update_game.sh`

Automatically pulls the latest changes from your git repository and restarts the server.

### `restart_prod.sh`

Restarts the Evennia server with proper error handling and Discord notifications.

### `backup_game.sh`

Creates a backup of the game directory with proper error handling and Discord notifications.

### `restore_game.sh`

Restores the game directory from a backup.

### `discord_notify.sh`

Sends notifications to Discord about server status.

## Manual Usage

### Creating a Backup

```bash
./Scripts/backup_game.sh
```

### Restoring from a Backup

```bash
./Scripts/restore_game.sh
```

### Restarting the Server

```bash
./Scripts/restart_prod.sh
```

### Updating the Server

```bash
./Scripts/update_game.sh
```

## Logs

Logs are stored in `/var/log/`:
- `evennia_update.log`: Log of update operations
- `evennia_restart.log`: Log of server restarts
- `evennia_backup.log`: Log of backup operations
- `evennia_restore.log`: Log of restore operations

## Troubleshooting

### Common Issues

1. **Permission Denied**: Make sure all scripts are executable:
   ```bash
   chmod +x Scripts/*.sh
   ```

2. **Cron Job Not Running**: Check if the cron service is running:
   ```bash
   systemctl status cron
   ```

3. **Discord Notifications Not Working**: Verify your webhook URL in the configuration file.

4. **Backup Fails**: Check if you have enough disk space and proper permissions.

### Viewing Logs

```bash
tail -f /var/log/evennia_update.log
tail -f /var/log/evennia_restart.log
tail -f /var/log/evennia_backup.log
tail -f /var/log/evennia_restore.log
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Evennia](https://www.evennia.com/) - The MUD server framework
- [Discord](https://discord.com/) - For notification capabilities 