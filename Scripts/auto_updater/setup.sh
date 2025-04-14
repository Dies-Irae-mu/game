#!/bin/bash

#=============================================================================
# Evennia Auto-Update System Setup Script
#=============================================================================
#
# PURPOSE:
#   This script sets up the auto-update system for an Evennia game server by:
#   1. Creating a configuration file with all necessary settings
#   2. Setting up log and backup directories with proper permissions
#   3. Creating log files for tracking updates, restarts, backups, and restores
#   4. Making all auto-updater scripts executable
#
# USAGE:
#   ./setup.sh [options]
#
# OPTIONS:
#   -d, --directory DIR     Game directory path (default: /root/game)
#   -e, --env ENV           Conda environment name (default: game_py311)
#   -b, --branch BRANCH     Git branch to pull from (default: main)
#   -i, --interval MIN      Update interval in minutes (default: 60)
#   -w, --webhook URL       Discord webhook URL (optional)
#   -h, --help              Display help message
#
# DEPENDENCIES:
#   - Git must be installed and available in PATH
#   - Conda must be installed and available in PATH
#   - The game directory must be a git repository
#   - The specified conda environment must exist
#
# OUTPUT:
#   - Creates config.sh in the auto_updater directory
#   - Creates log and backup directories
#   - Sets permissions for all scripts
#
#=============================================================================

# Enable strict error handling
set -euo pipefail

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to display usage information
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -d, --directory DIR     Game directory path (default: /root/game)"
    echo "  -e, --env ENV           Conda environment name (default: game_py311)"
    echo "  -b, --branch BRANCH     Git branch to pull from (default: main)"
    echo "  -i, --interval MIN      Update interval in minutes (default: 60)"
    echo "  -w, --webhook URL       Discord webhook URL (optional)"
    echo "  -h, --help              Display this help message"
    exit 1
}

# Default values
GAME_DIRECTORY="/root/game"
CONDA_ENV="game_py311"
CONDA_BASE="/root/miniconda3"
CONDA_SH="/root/miniconda3/etc/profile.d/conda.sh"
PYTHON_VERSION="3.12.4"
CONDA_VERSION="24.5.0"
USER_ID="0"
GROUP_ID="0"
GIT_BRANCH="main"
UPDATE_INTERVAL=60
DISCORD_WEBHOOK_URL=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--directory)
            GAME_DIRECTORY="$2"
            shift 2
            ;;
        -e|--env)
            CONDA_ENV="$2"
            shift 2
            ;;
        -b|--branch)
            GIT_BRANCH="$2"
            shift 2
            ;;
        -i|--interval)
            UPDATE_INTERVAL="$2"
            shift 2
            ;;
        -w|--webhook)
            DISCORD_WEBHOOK_URL="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Check if the game directory exists
if [ ! -d "$GAME_DIRECTORY" ]; then
    echo "Error: Game directory does not exist: $GAME_DIRECTORY"
    exit 1
fi

# Check if the game directory is a git repository
if [ ! -d "$GAME_DIRECTORY/.git" ]; then
    echo "Error: Game directory is not a git repository: $GAME_DIRECTORY"
    exit 1
fi

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "Error: git command not found"
    exit 1
fi

# Check if the specified branch exists
if ! git -C "$GAME_DIRECTORY" ls-remote --heads origin "$GIT_BRANCH" &> /dev/null; then
    echo "Error: Branch '$GIT_BRANCH' does not exist in the remote repository"
    exit 1
fi

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "Error: conda command not found"
    exit 1
fi

# Check if the conda environment exists
if ! conda env list | grep -q "^$CONDA_ENV "; then
    echo "Error: Conda environment '$CONDA_ENV' does not exist"
    exit 1
fi

# Check if the conda base directory exists
if [ ! -d "$CONDA_BASE" ]; then
    echo "Error: Conda base directory does not exist: $CONDA_BASE"
    exit 1
fi

# Check if the conda.sh script exists
if [ ! -f "$CONDA_SH" ]; then
    echo "Error: Conda.sh script not found: $CONDA_SH"
    exit 1
fi

# Get the parent directory of the game directory for logs and backups
PARENT_DIR="$(dirname "$(cd "$GAME_DIRECTORY" && pwd)")"

# Create log directory
LOG_DIR="$PARENT_DIR/logs"
if [ ! -d "$LOG_DIR" ]; then
    echo "Creating log directory..."
    if ! mkdir -p "$LOG_DIR" 2>/dev/null; then
        # Try with sudo if regular mkdir fails
        if ! sudo mkdir -p "$LOG_DIR"; then
            echo "Error: Failed to create log directory: $LOG_DIR"
            echo "Please ensure you have the necessary permissions or run this script with sudo."
            exit 1
        fi
    fi
fi

# Create log files
UPDATE_LOG="$LOG_DIR/evennia_update.log"
RESTART_LOG="$LOG_DIR/evennia_restart.log"
BACKUP_LOG="$LOG_DIR/evennia_backup.log"
RESTORE_LOG="$LOG_DIR/evennia_restore.log"

for log_file in "$UPDATE_LOG" "$RESTART_LOG" "$BACKUP_LOG" "$RESTORE_LOG"; do
    if [ ! -f "$log_file" ]; then
        echo "Creating log file: $log_file"
        if ! touch "$log_file" 2>/dev/null; then
            # Try with sudo if regular touch fails
            if ! sudo touch "$log_file"; then
                echo "Error: Failed to create log file: $log_file"
                echo "Please ensure you have the necessary permissions or run this script with sudo."
                exit 1
            fi
        fi
    fi
done

# Set permissions for log files
if ! chmod 644 "$UPDATE_LOG" "$RESTART_LOG" "$BACKUP_LOG" "$RESTORE_LOG" 2>/dev/null; then
    # Try with sudo if regular chmod fails
    if ! sudo chmod 644 "$UPDATE_LOG" "$RESTART_LOG" "$BACKUP_LOG" "$RESTORE_LOG"; then
        echo "Error: Failed to set permissions for log files"
        echo "Please ensure you have the necessary permissions or run this script with sudo."
        exit 1
    fi
fi

# Set ownership of log files to the current user if possible
if ! chown "$USER_ID:$GROUP_ID" "$UPDATE_LOG" "$RESTART_LOG" "$BACKUP_LOG" "$RESTORE_LOG" 2>/dev/null; then
    # Try with sudo if regular chown fails
    if ! sudo chown "$USER_ID:$GROUP_ID" "$UPDATE_LOG" "$RESTART_LOG" "$BACKUP_LOG" "$RESTORE_LOG"; then
        echo "Warning: Failed to set ownership of log files to $USER_ID:$GROUP_ID"
        echo "The log files may not be writable by the current user."
    fi
fi

# Create backup directory if it doesn't exist
BACKUP_DIR="$PARENT_DIR/backups"
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Creating backup directory..."
    if ! mkdir -p "$BACKUP_DIR" 2>/dev/null; then
        # Try with sudo if regular mkdir fails
        if ! sudo mkdir -p "$BACKUP_DIR"; then
            echo "Error: Failed to create backup directory: $BACKUP_DIR"
            echo "Please ensure you have the necessary permissions or run this script with sudo."
            exit 1
        fi
    fi
fi

# Set permissions for backup directory
if ! chmod 755 "$BACKUP_DIR" 2>/dev/null; then
    # Try with sudo if regular chmod fails
    if ! sudo chmod 755 "$BACKUP_DIR"; then
        echo "Warning: Failed to set permissions for backup directory"
        echo "The backup directory may not be accessible."
    fi
fi

# Set ownership of backup directory to the current user if possible
if ! chown "$USER_ID:$GROUP_ID" "$BACKUP_DIR" 2>/dev/null; then
    # Try with sudo if regular chown fails
    if ! sudo chown "$USER_ID:$GROUP_ID" "$BACKUP_DIR"; then
        echo "Warning: Failed to set ownership of backup directory to $USER_ID:$GROUP_ID"
        echo "The backup directory may not be writable by the current user."
    fi
fi

# Create a subdirectory for dated backups
BACKUP_DATED_DIR="$BACKUP_DIR/dated"
if [ ! -d "$BACKUP_DATED_DIR" ]; then
    echo "Creating dated backup directory..."
    if ! mkdir -p "$BACKUP_DATED_DIR" 2>/dev/null; then
        # Try with sudo if regular mkdir fails
        if ! sudo mkdir -p "$BACKUP_DATED_DIR"; then
            echo "Error: Failed to create dated backup directory: $BACKUP_DATED_DIR"
            echo "Please ensure you have the necessary permissions or run this script with sudo."
            exit 1
        fi
    fi
fi

# Set permissions for dated backup directory
if ! chmod 755 "$BACKUP_DATED_DIR" 2>/dev/null; then
    # Try with sudo if regular chmod fails
    if ! sudo chmod 755 "$BACKUP_DATED_DIR"; then
        echo "Warning: Failed to set permissions for dated backup directory"
        echo "The dated backup directory may not be accessible."
    fi
fi

# Set ownership of dated backup directory to the current user if possible
if ! chown "$USER_ID:$GROUP_ID" "$BACKUP_DATED_DIR" 2>/dev/null; then
    # Try with sudo if regular chown fails
    if ! sudo chown "$USER_ID:$GROUP_ID" "$BACKUP_DATED_DIR"; then
        echo "Warning: Failed to set ownership of dated backup directory to $USER_ID:$GROUP_ID"
        echo "The dated backup directory may not be writable by the current user."
    fi
fi

# Create configuration file
CONFIG_FILE="$SCRIPT_DIR/config.sh"
echo "#!/bin/bash" > "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Evennia Auto-Update System Configuration" >> "$CONFIG_FILE"
echo "# This file contains configuration variables for all scripts" >> "$CONFIG_FILE"
echo "# Edit this file to configure your environment" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Directory paths" >> "$CONFIG_FILE"
echo "SCRIPT_DIR=\"$SCRIPT_DIR\"" >> "$CONFIG_FILE"
echo "PARENT_DIR=\"$PARENT_DIR\"" >> "$CONFIG_FILE"
echo "GAME_DIRECTORY=\"$GAME_DIRECTORY\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Conda environment name" >> "$CONFIG_FILE"
echo "CONDA_ENV=\"$CONDA_ENV\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Conda paths" >> "$CONFIG_FILE"
echo "CONDA_BASE=\"$CONDA_BASE\"" >> "$CONFIG_FILE"
echo "CONDA_SH=\"$CONDA_SH\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Environment versions" >> "$CONFIG_FILE"
echo "PYTHON_VERSION=\"$PYTHON_VERSION\"" >> "$CONFIG_FILE"
echo "CONDA_VERSION=\"$CONDA_VERSION\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# User and group IDs" >> "$CONFIG_FILE"
echo "USER_ID=\"$USER_ID\"" >> "$CONFIG_FILE"
echo "GROUP_ID=\"$GROUP_ID\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Git branch to pull from" >> "$CONFIG_FILE"
echo "GIT_BRANCH=\"$GIT_BRANCH\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Update interval in minutes" >> "$CONFIG_FILE"
echo "UPDATE_INTERVAL=$UPDATE_INTERVAL" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Discord webhook URL" >> "$CONFIG_FILE"
echo "DISCORD_WEBHOOK_URL=\"$DISCORD_WEBHOOK_URL\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Backup directories" >> "$CONFIG_FILE"
echo "BACKUP_DIR=\"$BACKUP_DIR\"" >> "$CONFIG_FILE"
echo "BACKUP_DATED_DIR=\"$BACKUP_DATED_DIR\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Log files" >> "$CONFIG_FILE"
echo "LOG_DIR=\"$LOG_DIR\"" >> "$CONFIG_FILE"
echo "UPDATE_LOG=\"\$LOG_DIR/evennia_update.log\"" >> "$CONFIG_FILE"
echo "RESTART_LOG=\"\$LOG_DIR/evennia_restart.log\"" >> "$CONFIG_FILE"
echo "BACKUP_LOG=\"\$LOG_DIR/evennia_backup.log\"" >> "$CONFIG_FILE"
echo "RESTORE_LOG=\"\$LOG_DIR/evennia_restore.log\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Timeout values (in seconds)" >> "$CONFIG_FILE"
echo "STOP_TIMEOUT=60" >> "$CONFIG_FILE"
echo "START_TIMEOUT=120" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Export variables for use in other scripts" >> "$CONFIG_FILE"
echo "export SCRIPT_DIR" >> "$CONFIG_FILE"
echo "export PARENT_DIR" >> "$CONFIG_FILE"
echo "export GAME_DIRECTORY" >> "$CONFIG_FILE"
echo "export CONDA_ENV" >> "$CONFIG_FILE"
echo "export CONDA_BASE" >> "$CONFIG_FILE"
echo "export CONDA_SH" >> "$CONFIG_FILE"
echo "export PYTHON_VERSION" >> "$CONFIG_FILE"
echo "export CONDA_VERSION" >> "$CONFIG_FILE"
echo "export USER_ID" >> "$CONFIG_FILE"
echo "export GROUP_ID" >> "$CONFIG_FILE"
echo "export GIT_BRANCH" >> "$CONFIG_FILE"
echo "export UPDATE_INTERVAL" >> "$CONFIG_FILE"
echo "export DISCORD_WEBHOOK_URL" >> "$CONFIG_FILE"
echo "export BACKUP_DIR" >> "$CONFIG_FILE"
echo "export BACKUP_DATED_DIR" >> "$CONFIG_FILE"
echo "export LOG_DIR" >> "$CONFIG_FILE"
echo "export UPDATE_LOG" >> "$CONFIG_FILE"
echo "export RESTART_LOG" >> "$CONFIG_FILE"
echo "export BACKUP_LOG" >> "$CONFIG_FILE"
echo "export RESTORE_LOG" >> "$CONFIG_FILE"
echo "export STOP_TIMEOUT" >> "$CONFIG_FILE"
echo "export START_TIMEOUT" >> "$CONFIG_FILE"
echo "# Configuration version" >> "$CONFIG_FILE"
echo "CONFIG_VERSION=\"1.0\"" >> "$CONFIG_FILE"
echo "export CONFIG_VERSION" >> "$CONFIG_FILE"

# Make the configuration file executable
chmod +x "$CONFIG_FILE"

# Set permissions for all scripts in the auto_updater directory
echo "Setting permissions for auto-updater scripts..."
for script in "$SCRIPT_DIR"/*.sh; do
    if [ -f "$script" ]; then
        echo "Making executable: $(basename "$script")"
        if ! chmod +x "$script" 2>/dev/null; then
            # Try with sudo if regular chmod fails
            if ! sudo chmod +x "$script"; then
                echo "Warning: Failed to set executable permissions for: $(basename "$script")"
                echo "The script may not be executable."
            fi
        fi
        
        # Set ownership of the script
        if ! chown "$USER_ID:$GROUP_ID" "$script" 2>/dev/null; then
            # Try with sudo if regular chown fails
            if ! sudo chown "$USER_ID:$GROUP_ID" "$script"; then
                echo "Warning: Failed to set ownership for: $(basename "$script")"
                echo "The script may not be owned by the correct user."
            fi
        fi
    fi
done

# Create .gitignore file if it doesn't exist
if [ ! -f "$SCRIPT_DIR/.gitignore" ]; then
    echo "Creating .gitignore file..."
    echo "config.sh" > "$SCRIPT_DIR/.gitignore"
fi

validate_config() {
    local required_vars=("GAME_DIRECTORY" "CONDA_ENV" "GIT_BRANCH")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            echo "Error: Required variable $var is not set"
            return 1
        fi
    done
    return 0
}

echo "Setup completed successfully!"
echo "Configuration file created at: $CONFIG_FILE"
echo ""
echo "Directory Structure:"
echo "- Auto-updater: $SCRIPT_DIR"
echo "- Game: $GAME_DIRECTORY"
echo "- Logs: $LOG_DIR"
echo "- Backups: $BACKUP_DIR"
echo ""
echo "You can edit the configuration file at any time to change settings."
echo "The configuration file is ignored by git."
echo ""
echo "To set up auto-updates, run: ./auto_update.sh start" 