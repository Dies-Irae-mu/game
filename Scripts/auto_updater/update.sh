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
#   history           - Show commit history from main merged into production
#
# EXAMPLES:
#   ./update.sh pull                    # Pull latest changes
#   ./update.sh status                  # Check git status
#   ./update.sh backup create           # Create a backup with timestamp
#   ./update.sh auto start              # Start auto-updates
#   ./update.sh auto status             # Check auto-update status
#   ./update.sh history                 # Show commit history from main
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
    echo "  history           - Show commit history from main merged into production"
    echo ""
    echo "Examples:"
    echo "  $0 pull                    # Pull latest changes"
    echo "  $0 status                  # Check git status"
    echo "  $0 backup create           # Create a backup with timestamp"
    echo "  $0 auto start              # Start auto-updates"
    echo "  $0 auto status             # Check auto-update status"
    echo "  $0 history                 # Show commit history from main"
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
        # Format the message for Discord (escape special characters)
        # First, escape backslashes, then quotes, then newlines
        local formatted_message=$(echo "$message" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')
        
        # Send to Discord with proper JSON formatting
        curl -s -H "Content-Type: application/json" \
             -X POST \
             -d "{\"content\":\"$formatted_message\"}" \
             "$DISCORD_WEBHOOK_URL"
    fi
}

# Function to format messages for Discord
format_discord_message() {
    local message="$1"
    # Replace literal \n with actual newlines for display
    echo "$message" | sed 's/\\n/\n/g'
}

# Function to get commit information
get_commit_info() {
    local commit_hash="$1"
    local commit_msg=$(git -C "$GAME_DIRECTORY" log -1 --pretty=format:"%s" "$commit_hash")
    local commit_author=$(git -C "$GAME_DIRECTORY" log -1 --pretty=format:"%an" "$commit_hash")
    local commit_date=$(git -C "$GAME_DIRECTORY" log -1 --pretty=format:"%ad" --date=format:"%Y-%m-%d %H:%M:%S" "$commit_hash")
    
    echo "**Commit:** $commit_hash"
    echo "**Author:** $commit_author"
    echo "**Date:** $commit_date"
    echo "**Message:** $commit_msg"
}

# Function to get changed files
get_changed_files() {
    local old_commit="$1"
    local new_commit="$2"
    
    echo "**Changed Files:**"
    git -C "$GAME_DIRECTORY" diff --name-status "$old_commit" "$new_commit" | while read -r status file; do
        case "$status" in
            A) echo "- Added: $file" ;;
            M) echo "- Modified: $file" ;;
            D) echo "- Deleted: $file" ;;
            R) echo "- Renamed: $file" ;;
            C) echo "- Copied: $file" ;;
            U) echo "- Updated: $file" ;;
            T) echo "- Type changed: $file" ;;
            X) echo "- Unknown: $file" ;;
            B) echo "- Broken: $file" ;;
            *) echo "- $status: $file" ;;
        esac
    done
}

# Function to check if the server is running
check_server() {
    # Check for server process
    if pgrep -f "evennia/server/server.py" > /dev/null; then
        return 0
    fi
    
    # Check for the server PID file
    if [ -f "$GAME_DIRECTORY/server/server.pid" ]; then
        local pid=$(cat "$GAME_DIRECTORY/server/server.pid")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    
    return 1
}

# Function to check if the web portal is running
check_web_portal() {
    # Check for portal process
    if pgrep -f "evennia/server/portal/portal.py" > /dev/null; then
        return 0
    fi
    
    # Check for the portal PID file
    if [ -f "$GAME_DIRECTORY/server/portal.pid" ]; then
        local pid=$(cat "$GAME_DIRECTORY/server/portal.pid")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    
    return 1
}

# Function to get process uptime
get_process_uptime() {
    local pid="$1"
    local uptime="N/A"
    
    if [ -n "$pid" ]; then
        if command -v ps >/dev/null 2>&1; then
            # Try etime format first
            uptime=$(ps -o etime= -p "$pid" 2>/dev/null)
            # If that fails, try elapsed format
            if [ -z "$uptime" ]; then
                uptime=$(ps -o elapsed= -p "$pid" 2>/dev/null)
            fi
            # If both fail, try to get start time and calculate
            if [ -z "$uptime" ]; then
                local start_time=$(ps -o lstart= -p "$pid" 2>/dev/null)
                if [ -n "$start_time" ]; then
                    uptime="Started at: $start_time"
                fi
            fi
        fi
    fi
    
    echo "$uptime"
}

# Function to get server status with details
get_server_status() {
    local server_status="Not Running"
    local portal_status="Not Running"
    local server_uptime="N/A"
    local portal_uptime="N/A"
    local commit_hash="N/A"
    local commit_msg="N/A"
    local github_url="N/A"
    
    # Check server status
    if check_server; then
        server_status="Running"
        local server_pid=$(pgrep -f "evennia/server/server.py")
        server_uptime=$(get_process_uptime "$server_pid")
    fi
    
    # Check portal status
    if check_web_portal; then
        portal_status="Running"
        local portal_pid=$(pgrep -f "evennia/server/portal/portal.py")
        portal_uptime=$(get_process_uptime "$portal_pid")
    fi
    
    # Get current commit info
    commit_hash=$(git -C "$GAME_DIRECTORY" rev-parse --short HEAD 2>/dev/null || echo "N/A")
    commit_msg=$(git -C "$GAME_DIRECTORY" log -1 --pretty=format:"%s" 2>/dev/null || echo "N/A")
    
    # Get GitHub URL if available
    local remote_url=$(git -C "$GAME_DIRECTORY" config --get remote.origin.url 2>/dev/null || echo "")
    if [[ "$remote_url" == *"github.com"* ]]; then
        # Convert SSH URL to HTTPS if needed
        if [[ "$remote_url" == git@* ]]; then
            remote_url=$(echo "$remote_url" | sed 's/git@github.com:/https:\/\/github.com\//')
        fi
        # Remove .git suffix if present
        remote_url=$(echo "$remote_url" | sed 's/\.git$//')
        github_url="$remote_url/commit/$commit_hash"
    fi
    
    # Build status message with proper Discord formatting
    echo "**Game Server Status:** $server_status"
    echo "**Server Uptime:** $server_uptime"
    echo "**Web Portal Status:** $portal_status"
    echo "**Portal Uptime:** $portal_uptime"
    echo "**Current Commit:** $commit_hash"
    echo "**Commit Message:** $commit_msg"
    if [ "$github_url" != "N/A" ]; then
        echo "**GitHub Link:** $github_url"
    fi
}

# Function to restart the server using restart.sh
restart_server() {
    log_message "Restarting Evennia server using restart.sh..."
    
    # Check if restart.sh exists
    if [ ! -f "$SCRIPT_DIR/restart.sh" ]; then
        log_message "Error: restart.sh not found at $SCRIPT_DIR/restart.sh"
        send_discord_notification "$(format_discord_message "❌ Error: restart.sh not found at $SCRIPT_DIR/restart.sh")"
        return 1
    fi
    
    # Make sure restart.sh is executable
    chmod +x "$SCRIPT_DIR/restart.sh"
    
    # Run restart.sh with the restart command
    if ! "$SCRIPT_DIR/restart.sh" restart; then
        log_message "Failed to restart server using restart.sh"
        send_discord_notification "$(format_discord_message "❌ Failed to restart server using restart.sh")"
        return 1
    fi
    
    # Wait for server to start
    log_message "Waiting for server to start..."
    local attempts=0
    while [ $attempts -lt 30 ]; do
        if check_server && check_web_portal; then
            log_message "Server and portal started successfully"
            send_discord_notification "$(format_discord_message "✅ Server and portal started successfully")"
            return 0
        fi
        sleep 2
        attempts=$((attempts + 1))
    done
    
    log_message "Server failed to start after 60 seconds"
    send_discord_notification "$(format_discord_message "❌ Server failed to start after 60 seconds")"
    return 1
}

# Function to create a backup
create_backup() {
    local backup_name="${1:-}"
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
    send_discord_notification "$(format_discord_message "🔄 Creating backup of Evennia server")"

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
        send_discord_notification "$(format_discord_message "❌ Failed to create backup with rsync")"
        rm -rf "$backup_dir"
        return 1
    fi

    # Create a compressed archive of the rsync backup
    if ! tar -czf "$backup_file" -C "$BACKUP_DATED_DIR" "$(basename "$backup_dir")"; then
        log_message "Failed to create compressed archive"
        send_discord_notification "$(format_discord_message "❌ Failed to create compressed archive")"
        rm -rf "$backup_dir"
        return 1
    fi

    # Clean up the temporary directory
    rm -rf "$backup_dir"

    # Verify the backup
    if ! tar -tf "$backup_file" > /dev/null 2>&1; then
        log_message "Backup verification failed"
        send_discord_notification "$(format_discord_message "❌ Backup verification failed")"
        rm -f "$backup_file"
        return 1
    fi

    log_message "Backup created successfully: $backup_file"
    send_discord_notification "$(format_discord_message "✅ Backup created successfully")"
    return 0
}

# Function to restore from a backup
restore_backup() {
    local backup_file="$1"

    if [ ! -f "$backup_file" ]; then
        log_message "Backup file not found: $backup_file"
        send_discord_notification "$(format_discord_message "❌ Backup file not found: $backup_file")"
        return 1
    fi

    log_message "Restoring from backup: $backup_file"
    send_discord_notification "$(format_discord_message "🔄 Restoring Evennia server from backup")"

    # Create a backup of the current state
    if ! create_backup "pre_restore"; then
        log_message "Failed to create pre-restore backup"
        send_discord_notification "$(format_discord_message "❌ Failed to create pre-restore backup")"
        return 1
    fi

    # Extract the backup
    if ! tar -xzf "$backup_file" -C "$GAME_DIRECTORY"; then
        log_message "Failed to restore from backup"
        send_discord_notification "$(format_discord_message "❌ Failed to restore from backup")"
        return 1
    fi

    log_message "Successfully restored from backup"
    send_discord_notification "$(format_discord_message "✅ Successfully restored from backup")"
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

# Function to pull changes and restart server
pull_changes() {
    log_message "Checking for git changes..."
    send_discord_notification "$(format_discord_message "🔍 Checking for updates...")"
    
    # Fetch latest changes
    git -C "$GAME_DIRECTORY" fetch origin "$GIT_BRANCH" || {
        log_message "Failed to fetch from git"
        send_discord_notification "$(format_discord_message "❌ Failed to fetch from git")"
        return 1
    }
    
    # Check how many commits we're behind
    local behind=$(git -C "$GAME_DIRECTORY" rev-list --count HEAD..origin/"$GIT_BRANCH")
    
    if [ "$behind" -eq 0 ]; then
        log_message "No changes to pull, server is up to date."
        # Get current server status
        local status_info=$(get_server_status)
        send_discord_notification "$(format_discord_message "✅ Evennia Server Status Check\n\nNo changes to pull, server is up to date.\n\n$status_info")"
        return 0
    fi
    
    log_message "Found $behind commits to pull"
    send_discord_notification "$(format_discord_message "📥 Found $behind commits to pull")"
    
    # Create backup before pulling
    create_backup || {
        log_message "Failed to create backup"
        send_discord_notification "$(format_discord_message "❌ Failed to create backup")"
        return 1
    }
    
    # Store current commit for potential rollback
    local current_commit=$(git -C "$GAME_DIRECTORY" rev-parse HEAD)
    
    # Pull changes
    git -C "$GAME_DIRECTORY" pull origin "$GIT_BRANCH" || {
        log_message "Failed to pull changes"
        send_discord_notification "$(format_discord_message "❌ Failed to pull changes")"
        return 1
    }
    
    # Get commit info
    local commit_hash=$(git -C "$GAME_DIRECTORY" rev-parse --short HEAD)
    local commit_author=$(git -C "$GAME_DIRECTORY" log -1 --pretty=format:"%an")
    local commit_msg=$(git -C "$GAME_DIRECTORY" log -1 --pretty=format:"%s")
    local changed_files=$(git -C "$GAME_DIRECTORY" diff --name-only "$current_commit" HEAD)
    
    # Get GitHub URL if available
    local github_url="N/A"
    local remote_url=$(git -C "$GAME_DIRECTORY" config --get remote.origin.url 2>/dev/null || echo "")
    if [[ "$remote_url" == *"github.com"* ]]; then
        # Convert SSH URL to HTTPS if needed
        if [[ "$remote_url" == git@* ]]; then
            remote_url=$(echo "$remote_url" | sed 's/git@github.com:/https:\/\/github.com\//')
        fi
        # Remove .git suffix if present
        remote_url=$(echo "$remote_url" | sed 's/\.git$//')
        github_url="$remote_url/commit/$commit_hash"
    fi
    
    # Get information about commits from main that were merged
    local main_commits=""
    if [ "$GIT_BRANCH" = "production" ]; then
        # Count commits from main that were merged
        local main_commit_count=$(git -C "$GAME_DIRECTORY" log --oneline main..HEAD | wc -l)
        if [ "$main_commit_count" -gt 0 ]; then
            main_commits="\n\n**Commits from main merged into production:** $main_commit_count"
            # Get the most recent merge commit from main
            local merge_commit=$(git -C "$GAME_DIRECTORY" log --merges --pretty=format:"%h - %s (%an, %ar)" main..HEAD | head -n 1)
            if [ -n "$merge_commit" ]; then
                main_commits="$main_commits\n**Latest merge:** $merge_commit"
            fi
        fi
    fi
    
    # Get server status before restart
    local before_status=$(get_server_status)
    
    # Restart server
    log_message "Restarting server..."
    send_discord_notification "$(format_discord_message "🔄 Restarting server...\n\nCommit: $commit_hash\nAuthor: $commit_author\nMessage: $commit_msg\n\nChanged files:\n$changed_files$main_commits\n\nGitHub: $github_url\n\nServer status before restart:\n$before_status")"
    
    if ! restart_server; then
        log_message "Server restart failed, reverting changes"
        send_discord_notification "$(format_discord_message "❌ Server restart failed, reverting changes")"
        
        # Revert to previous commit
        git -C "$GAME_DIRECTORY" reset --hard "$current_commit" || {
            log_message "Failed to revert changes"
            send_discord_notification "$(format_discord_message "❌ Failed to revert changes")"
            return 1
        }
        
        # Try to restart server again
        if ! restart_server; then
            log_message "Server still failed to start after revert"
            send_discord_notification "$(format_discord_message "❌ Server still failed to start after revert")"
            return 1
        fi
        
        log_message "Successfully reverted to previous version"
        send_discord_notification "$(format_discord_message "✅ Successfully reverted to previous version")"
        return 1
    fi
    
    # Get server status after restart
    local after_status=$(get_server_status)
    
    log_message "Server successfully updated and restarted"
    send_discord_notification "$(format_discord_message "✅ Server successfully updated and restarted\n\nCommit: $commit_hash\nAuthor: $commit_author\nMessage: $commit_msg\n\nChanged files:\n$changed_files$main_commits\n\nGitHub: $github_url\n\nServer status after restart:\n$after_status")"
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

    # Check if server is running
    if ! pgrep -f "evennia" > /dev/null; then
        echo "Warning: Evennia server is not running"
        send_discord_notification "$(format_discord_message "@here **Server Status Warning**\n\nEvennia server is not running")"
    fi

    return 0
}

# Function to revert to previous version
revert_changes() {
    log_message "Reverting to previous version..."
    send_discord_notification "$(format_discord_message "🔄 Reverting Evennia server to previous version")"

    # Get the previous commit
    local prev_commit
    prev_commit=$(git -C "$GAME_DIRECTORY" rev-parse HEAD^)
    if [ $? -ne 0 ]; then
        log_message "Failed to get previous commit"
        send_discord_notification "$(format_discord_message "❌ Failed to get previous commit")"
        return 1
    fi

    # Create a backup before reverting
    if ! create_backup "pre_revert"; then
        log_message "Failed to create backup before revert"
        send_discord_notification "$(format_discord_message "❌ Failed to create backup before revert")"
        return 1
    fi

    # Revert to previous commit
    if ! git -C "$GAME_DIRECTORY" reset --hard "$prev_commit"; then
        log_message "Failed to revert to previous version"
        send_discord_notification "$(format_discord_message "❌ Failed to revert to previous version")"
        return 1
    fi

    log_message "Successfully reverted to previous version"
    send_discord_notification "$(format_discord_message "✅ Successfully reverted to previous version")"
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
    send_discord_notification "$(format_discord_message "🚀 Starting auto-updates for Evennia server")"

    # Add cron job to run update.sh pull every UPDATE_INTERVAL minutes
    (crontab -l 2>/dev/null || true; echo "*/$UPDATE_INTERVAL * * * * cd $SCRIPT_DIR && ./update.sh pull >> $UPDATE_LOG 2>&1") | crontab -

    if check_auto_updates; then
        log_message "Auto-updates started successfully"
        send_discord_notification "$(format_discord_message "✅ Auto-updates started successfully")"
        return 0
    else
        log_message "Failed to start auto-updates"
        send_discord_notification "$(format_discord_message "❌ Failed to start auto-updates")"
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
    send_discord_notification "$(format_discord_message "🛑 Stopping auto-updates for Evennia server")"

    # Remove the cron job
    crontab -l 2>/dev/null | grep -v "update.sh pull" | crontab -

    if ! check_auto_updates; then
        log_message "Auto-updates stopped successfully"
        send_discord_notification "$(format_discord_message "✅ Auto-updates stopped successfully")"
        return 0
    else
        log_message "Failed to stop auto-updates"
        send_discord_notification "$(format_discord_message "❌ Failed to stop auto-updates")"
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
    send_discord_notification "$(format_discord_message "⏸ Pausing auto-updates for Evennia server")"

    # Create a pause file
    touch "$SCRIPT_DIR/.auto_updates_paused"

    # Remove the cron job
    crontab -l 2>/dev/null | grep -v "update.sh pull" | crontab -

    # Add a cron job to check for resume
    (crontab -l 2>/dev/null || true; echo "* * * * * cd $SCRIPT_DIR && [ -f .auto_updates_paused ] || ./update.sh pull >> $UPDATE_LOG 2>&1") | crontab -

    log_message "Auto-updates paused successfully"
    send_discord_notification "$(format_discord_message "✅ Auto-updates paused successfully")"
    return 0
}

# Function to resume auto-updates
resume_auto_updates() {
    if [ ! -f "$SCRIPT_DIR/.auto_updates_paused" ]; then
        log_message "Auto-updates are not paused"
        return 0
    fi

    log_message "Resuming auto-updates..."
    send_discord_notification "$(format_discord_message "🚀 Resuming auto-updates for Evennia server")"

    # Remove the pause file
    rm -f "$SCRIPT_DIR/.auto_updates_paused"

    # Remove the check cron job
    crontab -l 2>/dev/null | grep -v "update.sh pull" | crontab -

    # Add the regular update cron job
    (crontab -l 2>/dev/null || true; echo "*/$UPDATE_INTERVAL * * * * cd $SCRIPT_DIR && ./update.sh pull >> $UPDATE_LOG 2>&1") | crontab -

    log_message "Auto-updates resumed successfully"
    send_discord_notification "$(format_discord_message "✅ Auto-updates resumed successfully")"
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
    send_discord_notification "$(format_discord_message "🚀 Running a single update cycle for Evennia server")"
    
    # Run the update process
    if ! pull_changes; then
        log_message "Update cycle failed - changes were automatically reverted if possible"
        send_discord_notification "$(format_discord_message "❌ Update cycle failed - changes were automatically reverted if possible")"
        return 1
    fi
    
    log_message "Update cycle completed successfully"
    send_discord_notification "$(format_discord_message "✅ Update cycle completed successfully")"
    return 0
}

# Function to show commit history from main merged into production
show_merge_history() {
    log_message "Showing commit history from main merged into production..."
    
    # Check if we're on the production branch
    local current_branch
    current_branch=$(git -C "$GAME_DIRECTORY" rev-parse --abbrev-ref HEAD)
    if [ "$current_branch" != "$GIT_BRANCH" ]; then
        echo "Warning: Not on $GIT_BRANCH branch (currently on $current_branch)"
        echo "Switching to $GIT_BRANCH branch to show history..."
        git -C "$GAME_DIRECTORY" checkout "$GIT_BRANCH" || {
            log_message "Failed to switch to $GIT_BRANCH branch"
            return 1
        }
    fi
    
    # Find merge commits from main
    echo "Merge commits from main to production:"
    git -C "$GAME_DIRECTORY" log --merges --pretty=format:"%h - %s (%an, %ar)" main..HEAD
    
    # Show detailed commit history
    echo ""
    echo "Detailed commit history from main merged into production:"
    git -C "$GAME_DIRECTORY" log --pretty=format:"%h - %s (%an, %ar)" main..HEAD
    
    # Show file changes
    echo ""
    echo "Files changed in merges from main:"
    git -C "$GAME_DIRECTORY" log --name-status --pretty=format:"%h - %s" main..HEAD
    
    # Send notification with summary
    local commit_count=$(git -C "$GAME_DIRECTORY" log --oneline main..HEAD | wc -l)
    send_discord_notification "$(format_discord_message "📊 **Commit History from Main**\n\nFound $commit_count commits from main merged into production.\n\nRun \`./update.sh history\` for details.")"
    
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
    history)
        show_merge_history
        ;;
    *)
        usage
        ;;
esac

exit 0 