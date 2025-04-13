#!/bin/bash

# Evennia Server Restart Script
# This script restarts the Evennia server with proper error handling and Discord notifications.

set -e

# Import configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# Log file for this script
LOG_FILE="$RESTART_LOG"

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
    send_discord_notification "Server Restart Failed" "Error in $function_name at line $line_number (exit code: $exit_code)" "0xe74c3c"
    exit $exit_code
}

# Set up error handling
trap 'error_handler ${LINENO} "${FUNCNAME[0]}"' ERR

# Function to create backup
create_backup() {
    log_message "Creating backup..."
    send_discord_notification "Backup Started" "Creating backup of the game directory" "0x3498db"
    
    if ! "$SCRIPT_DIR/backup_game.sh"; then
        log_message "Backup creation failed"
        send_discord_notification "Backup Failed" "Failed to create backup of the game directory" "0xe74c3c"
        return 1
    fi
    
    log_message "Backup created successfully"
    send_discord_notification "Backup Successful" "Backup of the game directory created successfully" "0x2ecc71"
    return 0
}

# Function to restore from backup
restore_from_backup() {
    log_message "Restoring from backup..."
    send_discord_notification "Restore Started" "Restoring game directory from backup" "0x3498db"
    
    if ! "$SCRIPT_DIR/restore_game.sh"; then
        log_message "Restore failed"
        send_discord_notification "Restore Failed" "Failed to restore game directory from backup" "0xe74c3c"
        return 1
    fi
    
    log_message "Restore completed successfully"
    send_discord_notification "Restore Successful" "Game directory restored successfully from backup" "0x2ecc71"
    return 0
}

# Function to revert git pull
revert_git_pull() {
    log_message "Reverting git pull..."
    send_discord_notification "Git Revert Started" "Reverting git pull to previous state" "0x3498db"
    
    cd "$GAME_DIRECTORY" || { log_message "Failed to change to game directory"; return 1; }
    
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_message "Not a git repository"
        send_discord_notification "Git Revert Failed" "Not a git repository" "0xe74c3c"
        return 1
    fi
    
    if ! git reset --hard HEAD^; then
        log_message "Failed to revert git pull"
        send_discord_notification "Git Revert Failed" "Failed to revert git pull" "0xe74c3c"
        return 1
    fi
    
    log_message "Git pull reverted successfully"
    send_discord_notification "Git Revert Successful" "Git pull reverted successfully" "0x2ecc71"
    return 0
}

# Function to restart Evennia
restart_evennia() {
    log_message "Restarting Evennia server..."
    send_discord_notification "Server Restart Started" "Restarting Evennia server" "0x3498db"
    
    # Check if conda environment exists
    if ! conda env list | grep -q "$CONDA_ENV"; then
        log_message "Conda environment $CONDA_ENV does not exist"
        send_discord_notification "Server Restart Failed" "Conda environment $CONDA_ENV does not exist" "0xe74c3c"
        return 1
    fi
    
    # Activate conda environment
    eval "$(conda shell.bash hook)"
    conda activate "$CONDA_ENV"
    
    # Check if Evennia is installed
    if ! command -v evennia > /dev/null 2>&1; then
        log_message "Evennia is not installed in the conda environment"
        send_discord_notification "Server Restart Failed" "Evennia is not installed in the conda environment" "0xe74c3c"
        return 1
    fi
    
    # Stop the server
    log_message "Stopping Evennia server..."
    if ! evennia stop; then
        log_message "Failed to stop Evennia server"
        send_discord_notification "Server Restart Failed" "Failed to stop Evennia server" "0xe74c3c"
        return 1
    fi
    
    # Wait for server to stop
    sleep 5
    
    # Start the server
    log_message "Starting Evennia server..."
    if ! evennia start; then
        log_message "Failed to start Evennia server"
        send_discord_notification "Server Restart Failed" "Failed to start Evennia server" "0xe74c3c"
        return 1
    fi
    
    log_message "Evennia server restarted successfully"
    send_discord_notification "Server Restart Successful" "Evennia server restarted successfully" "0x2ecc71"
    return 0
}

# Main execution
log_message "Starting server restart process"
send_discord_notification "Server Restart Started" "Starting server restart process" "0x3498db"

# Create backup
if ! create_backup; then
    log_message "Backup creation failed, aborting restart"
    send_discord_notification "Server Restart Failed" "Backup creation failed, aborting restart" "0xe74c3c"
    exit 1
fi

# Restart Evennia
if ! restart_evennia; then
    log_message "Server restart failed, attempting to restore from backup"
    send_discord_notification "Server Restart Failed" "Server restart failed, attempting to restore from backup" "0xe74c3c"
    
    # Restore from backup
    if ! restore_from_backup; then
        log_message "Restore failed, attempting to revert git pull"
        send_discord_notification "Server Restart Failed" "Restore failed, attempting to revert git pull" "0xe74c3c"
        
        # Revert git pull
        if ! revert_git_pull; then
            log_message "All recovery attempts failed"
            send_discord_notification "Server Restart Failed" "All recovery attempts failed" "0xe74c3c"
            exit 1
        fi
    fi
    
    # Try to restart Evennia again
    if ! restart_evennia; then
        log_message "Server restart failed after recovery attempts"
        send_discord_notification "Server Restart Failed" "Server restart failed after recovery attempts" "0xe74c3c"
        exit 1
    fi
fi

log_message "Server restart process completed successfully"
send_discord_notification "Server Restart Successful" "Server restart process completed successfully" "0x2ecc71"
exit 0 