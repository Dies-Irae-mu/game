#!/bin/bash

# Evennia Game Backup Script
# This script creates a backup of the game directory with proper error handling and Discord notifications.

set -e

# Import configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# Log file for this script
LOG_FILE="$BACKUP_LOG"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to send Discord notification
send_discord_notification() {
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        "$SCRIPT_DIR/discord_notify.sh" -w "$DISCORD_WEBHOOK_URL" -t "$1" -m "$2" -c "$3"
    fi
}

# Function to handle errors
error_handler() {
    local exit_code=$?
    local line_number=$1
    local function_name=$2
    log_message "Error in $function_name at line $line_number (exit code: $exit_code)"
    send_discord_notification "Backup Failed" "Error in $function_name at line $line_number (exit code: $exit_code)" "0xe74c3c"
    exit $exit_code
}

# Set up error handling
trap 'error_handler ${LINENO} "${FUNCNAME[0]}"' ERR

# Function to create backup
create_backup() {
    log_message "Creating backup..."
    send_discord_notification "Backup Started" "Creating backup of the game directory" "0x3498db"
    
    # Check if game directory exists
    if [ ! -d "$GAME_DIRECTORY" ]; then
        log_message "Game directory does not exist: $GAME_DIRECTORY"
        send_discord_notification "Backup Failed" "Game directory does not exist: $GAME_DIRECTORY" "0xe74c3c"
        return 1
    fi
    
    # Create backups directory if it doesn't exist
    if [ ! -d "$BACKUPS_DIR" ]; then
        log_message "Creating backups directory: $BACKUPS_DIR"
        mkdir -p "$BACKUPS_DIR"
    fi
    
    # Generate backup name
    BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
    BACKUP_PATH="$BACKUPS_DIR/$BACKUP_NAME.tar.gz"
    
    # Create backup
    if ! tar -czf "$BACKUP_PATH" -C "$(dirname "$GAME_DIRECTORY")" "$(basename "$GAME_DIRECTORY")" --exclude="*.pyc" --exclude="__pycache__" --exclude=".git" --exclude="backups"; then
        log_message "Failed to create backup archive"
        send_discord_notification "Backup Failed" "Failed to create backup archive" "0xe74c3c"
        return 1
    fi
    
    # Verify backup
    if [ ! -f "$BACKUP_PATH" ]; then
        log_message "Backup file was not created"
        send_discord_notification "Backup Failed" "Backup file was not created" "0xe74c3c"
        return 1
    fi
    
    log_message "Backup created successfully: $BACKUP_NAME"
    send_discord_notification "Backup Successful" "Backup created successfully: $BACKUP_NAME" "0x2ecc71"
    return 0
}

# Main execution
log_message "Starting backup process"
send_discord_notification "Backup Started" "Starting backup process" "0x3498db"

# Create backup
if ! create_backup; then
    log_message "Backup process failed"
    send_discord_notification "Backup Failed" "Backup process failed" "0xe74c3c"
    exit 1
fi

log_message "Backup process completed successfully"
send_discord_notification "Backup Successful" "Backup process completed successfully" "0x2ecc71"
exit 0 