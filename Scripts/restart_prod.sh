#!/bin/bash

# Evennia Auto-Update System - Server Restart Script
# This script restarts the Evennia server with error handling and Discord notifications.

# Enable strict error handling
set -euo pipefail

# Import configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.sh"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

source "$CONFIG_FILE"

# Log file for this script
LOG_FILE="$RESTART_LOG"

# Check if timeout command is available
if ! command -v timeout &> /dev/null; then
    echo "Warning: timeout command not found. Using default timeout values."
    # These will be overridden by config.sh values if available
    STOP_TIMEOUT=60
    START_TIMEOUT=120
fi

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to send Discord notification
send_discord_notification() {
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        if [ ! -f "$SCRIPT_DIR/discord_notify.sh" ]; then
            log_message "Error: discord_notify.sh script not found"
            return 1
        fi
        "$SCRIPT_DIR/discord_notify.sh" -w "$DISCORD_WEBHOOK_URL" -t "$1" -m "$2" -c "$3"
    fi
}

# Function to handle errors
error_handler() {
    local exit_code=$?
    local line_number=$1
    local function_name=$2
    log_message "Error in $function_name at line $line_number (exit code: $exit_code)"
    send_discord_notification "Restart Failed" "Error in $function_name at line $line_number (exit code: $exit_code)" "0xe74c3c"
    exit $exit_code
}

# Set up error handling
trap 'error_handler ${LINENO} "${FUNCNAME[0]}"' ERR

# Function to create a backup
create_backup() {
    log_message "Creating backup before restart..."
    send_discord_notification "Creating Backup" "Creating backup before restarting server" "0x3498db"
    
    if [ ! -f "$SCRIPT_DIR/backup_game.sh" ]; then
        log_message "Error: backup_game.sh script not found"
        send_discord_notification "Backup Failed" "backup_game.sh script not found" "0xe74c3c"
        return 1
    fi
    
    # Check if backup directory exists and is writable
    if [ ! -d "$(dirname "$BACKUP_DIR")" ]; then
        log_message "Error: Backup parent directory does not exist: $(dirname "$BACKUP_DIR")"
        send_discord_notification "Backup Failed" "Backup parent directory does not exist" "0xe74c3c"
        return 1
    fi
    
    if [ ! -w "$(dirname "$BACKUP_DIR")" ]; then
        log_message "Error: Backup parent directory is not writable: $(dirname "$BACKUP_DIR")"
        send_discord_notification "Backup Failed" "Backup parent directory is not writable" "0xe74c3c"
        return 1
    fi
    
    if ! "$SCRIPT_DIR/backup_game.sh"; then
        log_message "Error: Failed to create backup"
        send_discord_notification "Backup Failed" "Failed to create backup before restart" "0xe74c3c"
        return 1
    fi
    
    log_message "Backup created successfully"
    send_discord_notification "Backup Created" "Backup created successfully before restart" "0x2ecc71"
    return 0
}

# Function to restore from backup
restore_from_backup() {
    local backup_file="$1"
    
    # Check if backup file exists
    if [ ! -f "$backup_file" ]; then
        log_message "Backup file $backup_file does not exist"
        send_discord_notification "Backup Restore Failed" "Backup file $backup_file does not exist" "red"
        return 1
    fi
    
    # Create a backup of the current state before restoring
    log_message "Creating backup of current state before restore"
    if ! create_backup; then
        log_message "Failed to create backup before restore"
        send_discord_notification "Backup Restore Failed" "Failed to create backup before restore" "red"
        return 1
    fi
    
    # Extract the backup
    log_message "Extracting backup from $backup_file"
    if ! tar -xzf "$backup_file" -C "$GAME_DIRECTORY/.."; then
        log_message "Failed to extract backup"
        send_discord_notification "Backup Restore Failed" "Failed to extract backup" "red"
        return 1
    fi
    
    log_message "Backup restored successfully"
    send_discord_notification "Backup Restored" "Backup restored successfully from $backup_file" "green"
    return 0
}

# Function to revert the last git pull
revert_git_pull() {
    log_message "Reverting last git pull..."
    send_discord_notification "Reverting Changes" "Attempting to revert last git pull" "0x3498db"
    
    # Check if git is available
    if ! command -v git &> /dev/null; then
        log_message "Error: git command not found"
        send_discord_notification "Revert Failed" "git command not found" "0xe74c3c"
        return 1
    fi
    
    # Change to game directory
    cd "$GAME_DIRECTORY" || return 1
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir &> /dev/null; then
        log_message "Error: Not a git repository: $GAME_DIRECTORY"
        send_discord_notification "Revert Failed" "Not a git repository" "0xe74c3c"
        return 1
    fi
    
    # Check if there are uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        log_message "Warning: Uncommitted changes detected. These changes will be lost during revert."
        send_discord_notification "Revert Warning" "Uncommitted changes detected. These changes will be lost during revert." "0xf39c12"
        
        # Create a temporary stash to save uncommitted changes
        log_message "Creating temporary stash to save uncommitted changes..."
        if ! git stash push -m "Auto-stash before revert $(date '+%Y-%m-%d %H:%M:%S')"; then
            log_message "Warning: Failed to stash uncommitted changes. Proceeding with revert anyway."
            send_discord_notification "Revert Warning" "Failed to stash uncommitted changes. Proceeding with revert anyway." "0xf39c12"
        else
            log_message "Uncommitted changes stashed successfully"
        fi
    fi
    
    # Check if there are commits to revert to
    if ! git rev-parse HEAD~1 &> /dev/null; then
        log_message "Error: No previous commits to revert to"
        send_discord_notification "Revert Failed" "No previous commits to revert to" "0xe74c3c"
        return 1
    fi
    
    # Get the current commit hash for logging
    CURRENT_COMMIT=$(git rev-parse --short HEAD)
    PREVIOUS_COMMIT=$(git rev-parse --short HEAD~1)
    
    log_message "Reverting from commit $CURRENT_COMMIT to $PREVIOUS_COMMIT"
    
    # Attempt to revert
    if ! git reset --hard HEAD~1; then
        log_message "Error: Failed to revert git pull"
        send_discord_notification "Revert Failed" "Failed to revert git pull" "0xe74c3c"
        return 1
    fi
    
    log_message "Reverted git pull successfully from $CURRENT_COMMIT to $PREVIOUS_COMMIT"
    send_discord_notification "Changes Reverted" "Successfully reverted from commit $CURRENT_COMMIT to $PREVIOUS_COMMIT" "0x2ecc71"
    return 0
}

# Function to restart the Evennia server
restart_server() {
    log_message "Restarting Evennia server..."
    send_discord_notification "Restarting Server" "Attempting to restart Evennia server" "0x3498db"
    
    # Check if conda is available
    if ! command -v conda &> /dev/null; then
        log_message "Error: conda command not found"
        send_discord_notification "Restart Failed" "conda command not found" "0xe74c3c"
        return 1
    fi
    
    # Check if the conda environment exists
    if ! conda env list | grep -q "^$CONDA_ENV "; then
        log_message "Error: Conda environment '$CONDA_ENV' not found"
        send_discord_notification "Restart Failed" "Conda environment '$CONDA_ENV' not found" "0xe74c3c"
        return 1
    fi
    
    # Change to game directory
    cd "$GAME_DIRECTORY" || return 1
    
    # Get conda base directory
    CONDA_BASE=$(conda info --base)
    if [ ! -d "$CONDA_BASE" ]; then
        log_message "Error: Conda base directory not found: $CONDA_BASE"
        send_discord_notification "Restart Failed" "Conda base directory not found: $CONDA_BASE" "0xe74c3c"
        return 1
    fi
    
    # Check if conda.sh exists
    CONDA_SH="$CONDA_BASE/etc/profile.d/conda.sh"
    if [ ! -f "$CONDA_SH" ]; then
        log_message "Error: Conda initialization script not found: $CONDA_SH"
        send_discord_notification "Restart Failed" "Conda initialization script not found: $CONDA_SH" "0xe74c3c"
        return 1
    fi
    
    # Check if evennia command is available in the conda environment
    if ! timeout 5 bash -c "source '$CONDA_SH' && conda activate '$CONDA_ENV' && command -v evennia &> /dev/null"; then
        log_message "Error: evennia command not found in conda environment '$CONDA_ENV'"
        send_discord_notification "Restart Failed" "evennia command not found in conda environment" "0xe74c3c"
        return 1
    fi
    
    # Stop the server with timeout
    log_message "Stopping Evennia server..."
    if ! timeout $STOP_TIMEOUT bash -c "source '$CONDA_SH' && conda activate '$CONDA_ENV' && evennia stop"; then
        log_message "Error: Failed to stop Evennia server within $STOP_TIMEOUT seconds"
        send_discord_notification "Restart Failed" "Failed to stop Evennia server within $STOP_TIMEOUT seconds" "0xe74c3c"
        return 1
    fi
    
    # Wait for the server to fully stop
    log_message "Waiting for server to fully stop..."
    sleep 5
    
    # Check if the server is still running
    if timeout 5 bash -c "source '$CONDA_SH' && conda activate '$CONDA_ENV' && evennia status" | grep -q "running"; then
        log_message "Warning: Server is still running after stop command. Attempting to force stop..."
        send_discord_notification "Restart Warning" "Server is still running after stop command. Attempting to force stop." "0xf39c12"
        
        # Try to force stop the server
        if ! timeout 10 bash -c "source '$CONDA_SH' && conda activate '$CONDA_ENV' && evennia stop --force"; then
            log_message "Error: Failed to force stop Evennia server"
            send_discord_notification "Restart Failed" "Failed to force stop Evennia server" "0xe74c3c"
            return 1
        fi
        
        # Wait again for the server to stop
        sleep 5
    fi
    
    # Start the server with timeout
    log_message "Starting Evennia server..."
    if ! timeout $START_TIMEOUT bash -c "source '$CONDA_SH' && conda activate '$CONDA_ENV' && evennia start"; then
        log_message "Error: Failed to start Evennia server within $START_TIMEOUT seconds"
        send_discord_notification "Restart Failed" "Failed to start Evennia server within $START_TIMEOUT seconds" "0xe74c3c"
        return 1
    fi
    
    # Verify the server is running
    log_message "Verifying server is running..."
    if ! timeout 10 bash -c "source '$CONDA_SH' && conda activate '$CONDA_ENV' && evennia status" | grep -q "running"; then
        log_message "Error: Server failed to start properly"
        send_discord_notification "Restart Failed" "Server failed to start properly" "0xe74c3c"
        return 1
    fi
    
    log_message "Evennia server restarted successfully"
    send_discord_notification "Server Restarted" "Evennia server restarted successfully" "0x2ecc71"
    return 0
}

# Main execution
log_message "Starting server restart process"
send_discord_notification "Restart Process Started" "Starting server restart process" "0x3498db"

# Create a backup before restarting
if ! create_backup; then
    log_message "Error: Failed to create backup, aborting restart"
    send_discord_notification "Restart Aborted" "Failed to create backup, aborting restart" "0xe74c3c"
    exit 1
fi

# Attempt to restart the server
if ! restart_server; then
    log_message "Error: Failed to restart server, attempting to restore from backup"
    send_discord_notification "Restart Failed" "Failed to restart server, attempting to restore from backup" "0xe74c3c"
    
    # Try to restore from backup
    if ! restore_from_backup; then
        log_message "Error: Failed to restore from backup, attempting to revert git pull"
        send_discord_notification "Restore Failed" "Failed to restore from backup, attempting to revert git pull" "0xe74c3c"
        
        # Try to revert the last git pull
        if ! revert_git_pull; then
            log_message "Error: All recovery attempts failed"
            send_discord_notification "Recovery Failed" "All recovery attempts failed" "0xe74c3c"
            exit 1
        fi
    fi
    
    # Try to restart the server again after recovery
    if ! restart_server; then
        log_message "Error: Failed to restart server after recovery"
        send_discord_notification "Recovery Failed" "Failed to restart server after recovery" "0xe74c3c"
        exit 1
    fi
fi

log_message "Server restart process completed successfully"
send_discord_notification "Restart Process Completed" "Server restart process completed successfully" "0x2ecc71"
exit 0 