#!/bin/bash

# Script to restart the Evennia server with error handling and rollback capabilities
# This script is called by the auto-update cron job when changes are detected

# Set the game directory - CHANGE THIS to your actual game directory path
GAME_DIRECTORY="/root/game"

# Set the conda environment - CHANGE THIS to your actual conda environment name
CONDA_ENV="game_py311"

# Log file
LOG_FILE="/var/log/evennia_restart.log"

# Discord webhook URL - CHANGE THIS to your actual Discord webhook URL
# To get a webhook URL, go to your Discord server settings > Integrations > Webhooks > New Webhook
DISCORD_WEBHOOK_URL=""

# Enable error handling
set -e
trap 'error_handler $? $LINENO $BASH_LINENO "$BASH_COMMAND" $(printf "::%s" ${FUNCNAME[@]:-})' ERR

# Function to handle errors
error_handler() {
    local exit_code=$1
    local line_no=$2
    local bash_lineno=$3
    local last_command=$4
    local func_trace=$5
    
    # Log the error
    log_message "ERROR: Command '$last_command' failed with exit code $exit_code at line $line_no"
    log_message "Function trace: $func_trace"
    
    # Send Discord notification if configured
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Script Error" "Command '$last_command' failed with exit code $exit_code at line $line_no\nFunction trace: $func_trace" "0xe74c3c"
    fi
    
    # Don't exit here, let the script continue with error recovery
}

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to send Discord notification
send_discord_notification() {
    local TITLE="$1"
    local MESSAGE="$2"
    local COLOR="$3"
    
    # Get the directory of this script
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Check if discord_notify.sh exists
    if [ -f "$SCRIPT_DIR/discord_notify.sh" ]; then
        # Make sure it's executable
        chmod +x "$SCRIPT_DIR/discord_notify.sh"
        
        # Send the notification
        if ! "$SCRIPT_DIR/discord_notify.sh" -w "$DISCORD_WEBHOOK_URL" -t "$TITLE" -m "$MESSAGE" -c "$COLOR"; then
            log_message "WARNING: Failed to send Discord notification: $TITLE"
        fi
    else
        log_message "WARNING: Discord notification script not found: $SCRIPT_DIR/discord_notify.sh"
    fi
}

# Function to create a backup
create_backup() {
    log_message "Creating backup before restart"
    BACKUP_NAME="pre_restart_backup_$(date +%Y%m%d_%H%M%S)"
    
    # Get the directory of this script
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Check if backup script exists
    if [ ! -f "$SCRIPT_DIR/backup_game.sh" ]; then
        log_message "ERROR: Backup script not found: $SCRIPT_DIR/backup_game.sh"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Backup Failed" "Backup script not found: $SCRIPT_DIR/backup_game.sh" "0xe74c3c"
        fi
        return 1
    fi
    
    # Make sure it's executable
    chmod +x "$SCRIPT_DIR/backup_game.sh"
    
    # Run the backup script
    if ! "$SCRIPT_DIR/backup_game.sh" -d "$GAME_DIRECTORY" -n "$BACKUP_NAME" -w "$DISCORD_WEBHOOK_URL"; then
        log_message "ERROR: Backup script failed with exit code $?"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Backup Failed" "Backup script failed with exit code $?" "0xe74c3c"
        fi
        return 1
    fi
    
    log_message "Backup created successfully: $BACKUP_NAME"
    return 0
}

# Function to restore from backup
restore_from_backup() {
    local BACKUP_NAME=$1
    log_message "Restoring from backup: $BACKUP_NAME"
    
    # Get the parent directory of the game directory
    PARENT_DIR=$(dirname "$GAME_DIRECTORY")
    BACKUPS_DIR="$PARENT_DIR/backups"
    
    # Check if restore script exists
    if [ ! -f "$BACKUPS_DIR/restore_backup.sh" ]; then
        log_message "ERROR: Restore script not found: $BACKUPS_DIR/restore_backup.sh"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Restore Failed" "Restore script not found: $BACKUPS_DIR/restore_backup.sh" "0xe74c3c"
        fi
        return 1
    fi
    
    # Make sure it's executable
    chmod +x "$BACKUPS_DIR/restore_backup.sh"
    
    # Run the restore script
    if ! "$BACKUPS_DIR/restore_backup.sh" -b "$BACKUP_NAME" -d "$GAME_DIRECTORY" -w "$DISCORD_WEBHOOK_URL"; then
        log_message "ERROR: Restore script failed with exit code $?"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Restore Failed" "Restore script failed with exit code $?" "0xe74c3c"
        fi
        return 1
    fi
    
    log_message "Restore completed successfully"
    return 0
}

# Function to revert the last git pull
revert_git_pull() {
    log_message "Reverting the last git pull"
    
    # Check if we're in a git repository
    if [ ! -d "$GAME_DIRECTORY/.git" ]; then
        log_message "ERROR: Not a git repository: $GAME_DIRECTORY"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Git Revert Failed" "Not a git repository: $GAME_DIRECTORY" "0xe74c3c"
        fi
        return 1
    fi
    
    # Change to the game directory
    cd "$GAME_DIRECTORY" || {
        log_message "ERROR: Failed to change to game directory: $GAME_DIRECTORY"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Git Revert Failed" "Failed to change to game directory: $GAME_DIRECTORY" "0xe74c3c"
        fi
        return 1
    }
    
    # Check if there are any commits to revert to
    if ! git reflog | grep -q "HEAD@{1}"; then
        log_message "ERROR: No previous commit to revert to"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Git Revert Failed" "No previous commit to revert to" "0xe74c3c"
        fi
        return 1
    fi
    
    # Revert the last pull
    if ! git reset --hard HEAD@{1}; then
        log_message "ERROR: Failed to revert git pull with exit code $?"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Git Revert Failed" "Failed to revert git pull with exit code $?" "0xe74c3c"
        fi
        return 1
    fi
    
    log_message "Git pull reverted successfully"
    return 0
}

# Function to restart the Evennia server
restart_evennia() {
    log_message "Restarting Evennia server"
    
    # Check if conda is installed
    if ! command -v conda &> /dev/null; then
        log_message "ERROR: Conda is not installed or not in PATH"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Server Restart Failed" "Conda is not installed or not in PATH" "0xe74c3c"
        fi
        return 1
    fi
    
    # Activate conda environment
    if ! source "$(conda info --base)/etc/profile.d/conda.sh"; then
        log_message "ERROR: Failed to source conda.sh"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Server Restart Failed" "Failed to source conda.sh" "0xe74c3c"
        fi
        return 1
    fi
    
    if ! conda activate "$CONDA_ENV"; then
        log_message "ERROR: Failed to activate conda environment: $CONDA_ENV"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Server Restart Failed" "Failed to activate conda environment: $CONDA_ENV" "0xe74c3c"
        fi
        return 1
    fi
    
    # Check if evennia is installed
    if ! command -v evennia &> /dev/null; then
        log_message "ERROR: Evennia is not installed or not in PATH"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Server Restart Failed" "Evennia is not installed or not in PATH" "0xe74c3c"
        fi
        return 1
    fi
    
    # Change to game directory
    cd "$GAME_DIRECTORY" || {
        log_message "ERROR: Failed to change to game directory: $GAME_DIRECTORY"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Server Restart Failed" "Failed to change to game directory: $GAME_DIRECTORY" "0xe74c3c"
        fi
        return 1
    }
    
    # Stop the server
    log_message "Stopping Evennia server"
    if ! evennia stop; then
        log_message "WARNING: Failed to stop Evennia server gracefully, attempting to force stop"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Server Stop Warning" "Failed to stop Evennia server gracefully, attempting to force stop" "0xf39c12"
        fi
        
        # Force stop the server
        if pgrep -f "evennia" > /dev/null; then
            pkill -f "evennia"
            sleep 2
            
            # Check if server is still running
            if pgrep -f "evennia" > /dev/null; then
                log_message "ERROR: Failed to force stop Evennia server"
                if [ -n "$DISCORD_WEBHOOK_URL" ]; then
                    send_discord_notification "Server Stop Failed" "Failed to force stop Evennia server" "0xe74c3c"
                fi
                return 1
            fi
        fi
    fi
    
    # Wait for the server to stop
    sleep 5
    
    # Start the server
    log_message "Starting Evennia server"
    if ! evennia start; then
        log_message "ERROR: Failed to start Evennia server with exit code $?"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Server Start Failed" "Failed to start Evennia server with exit code $?" "0xe74c3c"
        fi
        return 1
    fi
    
    # Wait for the server to start
    sleep 10
    
    # Check if the server is running
    if ! pgrep -f "evennia" > /dev/null; then
        log_message "ERROR: Evennia server is not running after start attempt"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Server Start Failed" "Evennia server is not running after start attempt" "0xe74c3c"
        fi
        return 1
    fi
    
    log_message "Evennia server restarted successfully"
    return 0
}

# Main execution
log_message "Starting Evennia server restart process"

# Send Discord notification about the restart attempt
if [ -n "$DISCORD_WEBHOOK_URL" ]; then
    send_discord_notification "Server Restart Initiated" "Starting Evennia server restart process" "0x3498db"
fi

# Create a backup before attempting restart
BACKUP_NAME=""
if create_backup; then
    BACKUP_NAME="pre_restart_backup_$(date +%Y%m%d_%H%M%S)"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Backup Created" "Backup created successfully: $BACKUP_NAME" "0x2ecc71"
    fi
else
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Backup Failed" "Failed to create backup before restart" "0xe74c3c"
    fi
fi

# Attempt to restart the server
if restart_evennia; then
    log_message "Evennia server restart completed successfully"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Server Restart Successful" "Evennia server has been restarted successfully" "0x2ecc71"
    fi
    exit 0
else
    log_message "First restart attempt failed, reverting git pull and trying again"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Server Restart Failed" "First restart attempt failed, reverting git pull and trying again" "0xf39c12"
    fi
    
    # Revert the last git pull
    if revert_git_pull; then
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Git Pull Reverted" "Successfully reverted the last git pull" "0x3498db"
        fi
        
        # Try to restart again
        if restart_evennia; then
            log_message "Evennia server restart completed successfully after git revert"
            if [ -n "$DISCORD_WEBHOOK_URL" ]; then
                send_discord_notification "Server Restart Successful" "Evennia server has been restarted successfully after git revert" "0x2ecc71"
            fi
            exit 0
        else
            log_message "Second restart attempt failed, restoring from backup"
            if [ -n "$DISCORD_WEBHOOK_URL" ]; then
                send_discord_notification "Server Restart Failed Again" "Second restart attempt failed, restoring from backup" "0xe67e22"
            fi
            
            # Restore from backup
            if [ -n "$BACKUP_NAME" ]; then
                if restore_from_backup "$BACKUP_NAME"; then
                    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
                        send_discord_notification "Backup Restored" "Successfully restored from backup: $BACKUP_NAME" "0x3498db"
                    fi
                    
                    # Try to restart one more time
                    if restart_evennia; then
                        log_message "Evennia server restart completed successfully after restore"
                        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
                            send_discord_notification "Server Restart Successful" "Evennia server has been restarted successfully after backup restore" "0x2ecc71"
                        fi
                        exit 0
                    else
                        log_message "Final restart attempt failed after restore"
                        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
                            send_discord_notification "Server Restart Failed Completely" "All restart attempts failed. Manual intervention required." "0xe74c3c"
                        fi
                        exit 1
                    fi
                else
                    log_message "Failed to restore from backup"
                    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
                        send_discord_notification "Backup Restore Failed" "Failed to restore from backup: $BACKUP_NAME" "0xe74c3c"
                    fi
                    exit 1
                fi
            else
                log_message "No backup available to restore from"
                if [ -n "$DISCORD_WEBHOOK_URL" ]; then
                    send_discord_notification "No Backup Available" "No backup available to restore from. Manual intervention required." "0xe74c3c"
                fi
                exit 1
            fi
        fi
    else
        log_message "Failed to revert git pull"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Git Pull Revert Failed" "Failed to revert the last git pull. Manual intervention required." "0xe74c3c"
        fi
        exit 1
    fi
fi 