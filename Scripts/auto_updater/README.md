# Evennia Auto-Update System

A comprehensive system for managing Evennia game server updates, backups, and restarts.

## Overview

The Evennia Auto-Update System provides automated management of your Evennia game server, including:
- Automatic git updates with error handling
- Automated backups before changes
- Server restart management
- Discord notifications for important events
- Cron-based scheduled updates

## Prerequisites

- Git installed and available in PATH
- Conda installed and available in PATH
- Evennia game server installed in a git repository
- Proper permissions to create directories and files
- Discord webhook URL (optional, for notifications)

## Installation

1. Clone or copy the auto-updater scripts to your server
2. Run the setup script with appropriate options:

```bash
./setup.sh [options]

Options:
  -d, --directory DIR     Game directory path (default: /root/game)
  -e, --env ENV           Conda environment name (default: game_py311)
  -b, --branch BRANCH     Git branch to pull from (default: production)
  -i, --interval MIN      Update interval in minutes (default: 60)
  -w, --webhook URL       Discord webhook URL (optional)
  -h, --help              Display help message
```

The setup script will:
- Create necessary configuration
- Set up log and backup directories
- Configure permissions
- Create required log files

## Usage

### Update Management

```bash
./update.sh [command] [options]

Commands:
  pull              - Pull latest changes from git
  status            - Check git status
  revert            - Revert to previous version
  backup create     - Create a new backup (optional name)
  backup restore    - Restore from a backup
  backup list       - List available backups
  auto start        - Start auto-updates
  auto stop         - Stop auto-updates
  auto pause        - Pause auto-updates
  auto resume       - Resume auto-updates
  auto status       - Check auto-update status
  auto run          - Run a single update cycle
```

### Server Restart

```bash
./restart.sh [command]

Commands:
  restart - Restart the Evennia server
  status  - Check server status
```

## Features

### Update System
- Automatic git pull with error handling
- Automatic backup before updates
- Automatic revert if update fails
- Server restart after successful updates
- Discord notifications for all events

### Backup System
- Timestamped backups
- Pre-update backups
- Pre-restart backups
- Backup verification
- Easy restore functionality

### Auto-Update System
- Configurable update interval
- Pause/resume functionality
- Status monitoring
- Discord notifications
- Error handling and logging

### Server Management
- Safe server restarts
- Status checking
- Automatic backup before restarts
- Timeout handling
- Error recovery

## Directory Structure

```
auto_updater/
├── update.sh           # Main update and backup script
├── restart.sh          # Server restart script
├── setup.sh           # Initial setup script
├── config.sh          # Configuration file (generated)
└── logs/              # Log directory
    ├── evennia_update.log
    ├── evennia_restart.log
    ├── evennia_backup.log
    └── evennia_restore.log
```

## Logging

All operations are logged to appropriate log files:
- `evennia_update.log`: Git updates and auto-update operations
- `evennia_restart.log`: Server restart operations
- `evennia_backup.log`: Backup operations
- `evennia_restore.log`: Restore operations

## Error Handling

The system includes comprehensive error handling:
- Automatic reversion of failed updates
- Backup creation before any major operation
- Server status verification
- Timeout handling for server operations
- Detailed error logging
- Discord notifications for failures

## Configuration

The system is configured through `config.sh`, which includes:
- Game directory path
- Conda environment settings
- Git branch settings
- Update interval
- Discord webhook URL
- Log file paths
- Backup directory paths
- Timeout settings

## Best Practices

1. Always run setup.sh first to configure the system
2. Use auto-updates for regular maintenance
3. Create manual backups before major changes
4. Monitor the logs for any issues
5. Keep the Discord webhook URL updated for notifications
6. Regularly check the backup directory size
7. Test the restore functionality periodically

## Troubleshooting

Common issues and solutions:
1. **Update fails**
   - Check git status
   - Verify git credentials
   - Check for local changes

2. **Server won't restart**
   - Check server logs
   - Verify conda environment
   - Check permissions

3. **Backup fails**
   - Check disk space
   - Verify directory permissions
   - Check tar installation

4. **Auto-updates not running**
   - Check cron service
   - Verify cron job exists
   - Check log files

## Contributing

Feel free to submit issues and enhancement requests! 

Added a line to test the auto update sync. 4