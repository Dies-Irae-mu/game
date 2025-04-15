#!/bin/bash

#=============================================================================
# Evennia Auto-Update System - Update and Backup Script
#=============================================================================
#
# PURPOSE:
#   This script manages git operations, backups, and auto-updates for the Evennia game server, including:
#   1. Pulling the latest changes from the git repository
#   2. Creating and managing backups
#   3. Checking the status of the git repository
#   4. Reverting to the previous version if needed
#   5. Managing automatic updates via cron jobs
#
# USAGE:
#   ./update.sh [command] [options]
#
# COMMANDS:
#   pull              - Pull latest changes from git
#   status            - Check git status
#   revert            - Revert to previous version
#   backup create     - Create a new backup (optional name)
#   backup restore    - Restore from a backup
#   backup list       - List available backups
#   auto start        - Start auto-updates
#   auto stop         - Stop auto-updates
#   auto pause        - Pause auto-updates
#   auto resume       - Resume auto-updates
#   auto status       - Check auto-update status
#   auto run          - Run a single update cycle
#
# EXAMPLES:
#   ./update.sh pull                    # Pull latest changes
#   ./update.sh status                  # Check git status
#   ./update.sh backup create           # Create a backup with timestamp
#   ./update.sh auto start              # Start auto-updates
#   ./update.sh auto status             # Check auto-update status
#
# DEPENDENCIES:
#   - Git must be installed and available in PATH
#   - The game directory must be a git repository
#   - The config.sh file must exist and be properly configured
#   - Cron must be available on the system
#
# OUTPUT:
#   - Logs all operations to the update log file
#   - Sends Discord notifications for important events
#   - Creates backups before making changes
#   - Manages cron jobs for automatic updates
#
#=============================================================================

# Enable strict error handling
set -euo pipefail

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the configuration file
CONFIG_FILE="$SCRIPT_DIR/config.sh"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found: $CONFIG_FILE"
    exit 1
fi
source "$CONFIG_FILE"

# Function to display usage information
usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  pull              - Pull latest changes from git"
    echo "  status            - Check git status"
    echo "  revert            - Revert to previous version"
    echo "  backup create     - Create a new backup (optional name)"
    echo "  backup restore    - Restore from a backup"
    echo "  backup list       - List available backups"
    echo "  auto start        - Start auto-updates"
    echo "  auto stop         - Stop auto-updates"
    echo "  auto pause        - Pause auto-updates"
    echo "  auto resume       - Resume auto-updates"
    echo "  auto status       - Check auto-update status"
    echo "  auto run          - Run a single update cycle"
    echo ""
    echo "Examples:"
    echo "  $0 pull                    # Pull latest changes"
    echo "  $0 status                  # Check git status"
    echo "  $0 backup create           # Create a backup with timestamp"
    echo "  $0 auto start              # Start auto-updates"
    echo "  $0 auto status             # Check auto-update status"
    exit 1
}

# Function to log messages
log_message() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" | tee -a "$UPDATE_LOG"
}

# Function to send Discord notifications
send_discord_notification() {
    local message="$1"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        curl -H "Content-Type: application/json" \
             -d "{\"content\":\"$message\"}" \
             "$DISCORD_WEBHOOK_URL"
    fi
}

# Function to create a backup
create_backup() {
    local backup_name="$1"
    local timestamp
    timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_dir
    local backup_file

    if [ -n "$backup_name" ]; then
        backup_dir="$BACKUP_DATED_DIR/${backup_name}_${timestamp}"
        backup_file="$BACKUP_DATED_DIR/${backup_name}_${timestamp}.tar.gz"
    else
        backup_dir="$BACKUP_DATED_DIR/backup_${timestamp}"
        backup_file="$BACKUP_DATED_DIR/backup_${timestamp}.tar.gz"
    fi

    log_message "Creating backup: $backup_file"
    send_discord_notification "Creating backup of Evennia server"

    # Create backup directories if they don't exist
    mkdir -p "$BACKUP_DIR" "$BACKUP_DATED_DIR" "$backup_dir"

    # Create the backup using rsync
    if ! rsync -av --exclude='*.lock' \
                  --exclude='*.pid' \
                  --exclude='.git' \
                  --exclude='media' \
                  --exclude='logs' \
                  --exclude='backups' \
                  "$GAME_DIRECTORY"/ "$backup_dir"/; then
        log_message "Failed to create backup with rsync"
        send_discord_notification "Failed to create backup with rsync"
        rm -rf "$backup_dir"
        return 1
    fi

    # Create a compressed archive of the rsync backup
    if ! tar -czf "$backup_file" -C "$BACKUP_DATED_DIR" "$(basename "$backup_dir")"; then
        log_message "Failed to create compressed archive"
        send_discord_notification "Failed to create compressed archive"
        rm -rf "$backup_dir"
        return 1
    fi

    # Clean up the temporary directory
    rm -rf "$backup_dir"

    # Verify the backup
    if ! tar -tf "$backup_file" > /dev/null 2>&1; then
        log_message "Backup verification failed"
        send_discord_notification "Backup verification failed"
        rm -f "$backup_file"
        return 1
    fi

    log_message "Backup created successfully: $backup_file"
    send_discord_notification "Backup created successfully"
    return 0
}

# Function to restore from a backup
restore_backup() {
    local backup_file="$1"

    if [ ! -f "$backup_file" ]; then
        log_message "Backup file not found: $backup_file"
        send_discord_notification "Backup file not found: $backup_file"
        return 1
    fi

    log_message "Restoring from backup: $backup_file"
    send_discord_notification "Restoring Evennia server from backup"

    # Create a backup of the current state
    if ! create_backup "pre_restore"; then
        log_message "Failed to create pre-restore backup"
        send_discord_notification "Failed to create pre-restore backup"
        return 1
    fi

    # Extract the backup
    if ! tar -xzf "$backup_file" -C "$GAME_DIRECTORY"; then
        log_message "Failed to restore from backup"
        send_discord_notification "Failed to restore from backup"
        return 1
    fi

    log_message "Successfully restored from backup"
    send_discord_notification "Successfully restored from backup"
    return 0
}

# Function to list available backups
list_backups() {
    log_message "Listing available backups..."
    
    if [ ! -d "$BACKUP_DATED_DIR" ]; then
        echo "No backups found"
        return 0
    fi

    echo "Available backups:"
    ls -lh "$BACKUP_DATED_DIR"/*.tar.gz 2>/dev/null || echo "No backups found"
    return 0
}

# Function to pull latest changes
pull_changes() {
    log_message "Checking for git changes..."
    send_discord_notification "Checking for git changes for Evennia server"

    # Check if there are any changes to pull
    git -C "$GAME_DIRECTORY" fetch origin
    local behind
    behind=$(git -C "$GAME_DIRECTORY" rev-list HEAD..origin/"$GIT_BRANCH" --count)
    
    if [ "$behind" -eq 0 ]; then
        log_message "No changes to pull, server is up to date"
        send_discord_notification "No changes to pull, server is up to date"
        return 0
    fi
    
    log_message "Found $behind commits to pull"
    send_discord_notification "Found $behind commits to pull for Evennia server"

    # Create a backup before updating
    if ! create_backup "pre_update"; then
        log_message "Failed to create backup before update"
        send_discord_notification "Failed to create backup before update"
        return 1
    fi

    # Store the current commit hash for potential revert
    local current_commit
    current_commit=$(git -C "$GAME_DIRECTORY" rev-parse HEAD)
    if [ $? -ne 0 ]; then
        log_message "Failed to get current commit hash"
        send_discord_notification "Failed to get current commit hash"
        return 1
    fi

    # Pull latest changes
    if ! git -C "$GAME_DIRECTORY" pull origin "$GIT_BRANCH"; then
        log_message "Failed to pull latest changes"
        send_discord_notification "Failed to pull latest changes"
        return 1
    fi

    log_message "Successfully pulled latest changes"
    send_discord_notification "Successfully pulled latest changes"
    
    # Restart the server after pulling changes
    log_message "Restarting server after update..."
    send_discord_notification "Restarting Evennia server after update"
    
    if ! "$SCRIPT_DIR/restart.sh" restart; then
        log_message "Failed to restart server after update, reverting changes..."
        send_discord_notification "Failed to restart server after update, reverting changes..."
        
        # Revert to the previous commit
        if ! git -C "$GAME_DIRECTORY" reset --hard "$current_commit"; then
            log_message "Failed to revert to previous version"
            send_discord_notification "Failed to revert to previous version"
            return 1
        fi
        
        log_message "Successfully reverted to previous version"
        send_discord_notification "Successfully reverted to previous version"
        
        # Try to restart the server again after reverting
        log_message "Attempting to restart server after revert..."
        send_discord_notification "Attempting to restart server after revert..."
        
        if ! "$SCRIPT_DIR/restart.sh" restart; then
            log_message "Failed to restart server after revert"
            send_discord_notification "Failed to restart server after revert"
            return 1
        fi
        
        log_message "Server restarted successfully after revert"
        send_discord_notification "Server restarted successfully after revert"
        return 1
    fi
    
    log_message "Server restarted successfully after update"
    send_discord_notification "Server restarted successfully after update"
    return 0
}

# Function to check git status
check_status() {
    log_message "Checking git status..."
    
    # Check if we're on the correct branch
    local current_branch
    current_branch=$(git -C "$GAME_DIRECTORY" rev-parse --abbrev-ref HEAD)
    if [ "$current_branch" != "$GIT_BRANCH" ]; then
        echo "Warning: Not on $GIT_BRANCH branch (currently on $current_branch)"
    fi

    # Check for local changes
    if ! git -C "$GAME_DIRECTORY" diff --quiet; then
        echo "Warning: You have local changes that haven't been committed"
        git -C "$GAME_DIRECTORY" status
    fi

    # Check for remote changes
    git -C "$GAME_DIRECTORY" fetch origin
    local behind
    behind=$(git -C "$GAME_DIRECTORY" rev-list HEAD..origin/"$GIT_BRANCH" --count)
    if [ "$behind" -gt 0 ]; then
        echo "You are $behind commits behind origin/$GIT_BRANCH"
    else
        echo "Your local branch is up to date with origin/$GIT_BRANCH"
    fi

    return 0
}

# Function to revert to previous version
revert_changes() {
    log_message "Reverting to previous version..."
    send_discord_notification "Reverting Evennia server to previous version"

    # Get the previous commit
    local prev_commit
    prev_commit=$(git -C "$GAME_DIRECTORY" rev-parse HEAD^)
    if [ $? -ne 0 ]; then
        log_message "Failed to get previous commit"
        send_discord_notification "Failed to get previous commit"
        return 1
    fi

    # Create a backup before reverting
    if ! create_backup "pre_revert"; then
        log_message "Failed to create backup before revert"
        send_discord_notification "Failed to create backup before revert"
        return 1
    fi

    # Revert to previous commit
    if ! git -C "$GAME_DIRECTORY" reset --hard "$prev_commit"; then
        log_message "Failed to revert to previous version"
        send_discord_notification "Failed to revert to previous version"
        return 1
    fi

    log_message "Successfully reverted to previous version"
    send_discord_notification "Successfully reverted to previous version"
    return 0
}

# Function to check if auto-updates are running
check_auto_updates() {
    if crontab -l 2>/dev/null | grep -q "update.sh pull"; then
        return 0
    else
        return 1
    fi
}

# Function to start auto-updates
start_auto_updates() {
    if check_auto_updates; then
        log_message "Auto-updates are already running"
        return 0
    fi

    log_message "Starting auto-updates..."
    send_discord_notification "Starting auto-updates for Evennia server"

    # Add cron job to run update.sh pull every UPDATE_INTERVAL minutes
    (crontab -l 2>/dev/null || true; echo "*/$UPDATE_INTERVAL * * * * cd $SCRIPT_DIR && ./update.sh pull >> $UPDATE_LOG 2>&1") | crontab -

    if check_auto_updates; then
        log_message "Auto-updates started successfully"
        send_discord_notification "Auto-updates started successfully"
        return 0
    else
        log_message "Failed to start auto-updates"
        send_discord_notification "Failed to start auto-updates"
        return 1
    fi
}

# Function to stop auto-updates
stop_auto_updates() {
    if ! check_auto_updates; then
        log_message "Auto-updates are not running"
        return 0
    fi

    log_message "Stopping auto-updates..."
    send_discord_notification "Stopping auto-updates for Evennia server"

    # Remove the cron job
    crontab -l 2>/dev/null | grep -v "update.sh pull" | crontab -

    if ! check_auto_updates; then
        log_message "Auto-updates stopped successfully"
        send_discord_notification "Auto-updates stopped successfully"
        return 0
    else
        log_message "Failed to stop auto-updates"
        send_discord_notification "Failed to stop auto-updates"
        return 1
    fi
}

# Function to pause auto-updates
pause_auto_updates() {
    if ! check_auto_updates; then
        log_message "Auto-updates are not running"
        return 0
    fi

    log_message "Pausing auto-updates..."
    send_discord_notification "Pausing auto-updates for Evennia server"

    # Create a pause file
    touch "$SCRIPT_DIR/.auto_updates_paused"

    # Remove the cron job
    crontab -l 2>/dev/null | grep -v "update.sh pull" | crontab -

    # Add a cron job to check for resume
    (crontab -l 2>/dev/null || true; echo "* * * * * cd $SCRIPT_DIR && [ -f .auto_updates_paused ] || ./update.sh pull >> $UPDATE_LOG 2>&1") | crontab -

    log_message "Auto-updates paused successfully"
    send_discord_notification "Auto-updates paused successfully"
    return 0
}

# Function to resume auto-updates
resume_auto_updates() {
    if [ ! -f "$SCRIPT_DIR/.auto_updates_paused" ]; then
        log_message "Auto-updates are not paused"
        return 0
    fi

    log_message "Resuming auto-updates..."
    send_discord_notification "Resuming auto-updates for Evennia server"

    # Remove the pause file
    rm -f "$SCRIPT_DIR/.auto_updates_paused"

    # Remove the check cron job
    crontab -l 2>/dev/null | grep -v "update.sh pull" | crontab -

    # Add the regular update cron job
    (crontab -l 2>/dev/null || true; echo "*/$UPDATE_INTERVAL * * * * cd $SCRIPT_DIR && ./update.sh pull >> $UPDATE_LOG 2>&1") | crontab -

    log_message "Auto-updates resumed successfully"
    send_discord_notification "Auto-updates resumed successfully"
    return 0
}

# Function to check auto-update status
check_auto_status() {
    if check_auto_updates; then
        if [ -f "$SCRIPT_DIR/.auto_updates_paused" ]; then
            echo "Auto-updates are paused"
        else
            echo "Auto-updates are running"
            echo "Update interval: $UPDATE_INTERVAL minutes"
        fi
    else
        echo "Auto-updates are not running"
    fi
    return 0
}

# Function to run a single update cycle
run_update_cycle() {
    log_message "Running a single update cycle..."
    send_discord_notification "Running a single update cycle for Evennia server"
    
    # Run the update process
    if ! pull_changes; then
        log_message "Update cycle failed - changes were automatically reverted if possible"
        send_discord_notification "Update cycle failed - changes were automatically reverted if possible"
        return 1
    fi
    
    log_message "Update cycle completed successfully"
    send_discord_notification "Update cycle completed successfully"
    return 0
}

# Main script
case "${1:-}" in
    pull)
        pull_changes
        ;;
    status)
        check_status
        ;;
    revert)
        revert_changes
        ;;
    backup)
        case "${2:-}" in
            create)
                create_backup "${3:-}"
                ;;
            restore)
                if [ -z "${3:-}" ]; then
                    echo "Error: No backup file specified"
                    usage
                fi
                restore_backup "$3"
                ;;
            list)
                list_backups
                ;;
            *)
                echo "Error: Invalid backup command"
                usage
                ;;
        esac
        ;;
    auto)
        case "${2:-}" in
            start)
                start_auto_updates
                ;;
            stop)
                stop_auto_updates
                ;;
            pause)
                pause_auto_updates
                ;;
            resume)
                resume_auto_updates
                ;;
            status)
                check_auto_status
                ;;
            run)
                run_update_cycle
                ;;
            *)
                echo "Error: Invalid auto command"
                usage
                ;;
        esac
        ;;
    *)
        usage
        ;;
esac

exit 0 