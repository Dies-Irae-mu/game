#!/bin/bash

# Script to set up auto-restore cron job for Evennia server
# This script creates a cron job to automatically restore from the latest backup if needed

# Function to display usage
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -b, --branch BRANCH      Git branch to pull from (default: main)"
    echo "  -i, --interval MINUTES   Check interval in minutes (default: 60)"
    echo "  -d, --directory DIR      Game directory path (default: /root/game)"
    echo "  -e, --env ENV            Conda environment name (default: game_py311)"
    echo "  -w, --webhook URL        Discord webhook URL for notifications"
    echo "  -h, --help               Display this help message"
    exit 1
}

# Default values
BRANCH="main"
INTERVAL=60
GAME_DIRECTORY="/root/game"
CONDA_ENV="game_py311"
DISCORD_WEBHOOK_URL=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -b|--branch)
            BRANCH="$2"
            shift 2
            ;;
        -i|--interval)
            INTERVAL="$2"
            shift 2
            ;;
        -d|--directory)
            GAME_DIRECTORY="$2"
            shift 2
            ;;
        -e|--env)
            CONDA_ENV="$2"
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

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create a temporary restore script
RESTORE_SCRIPT="$SCRIPT_DIR/restore_from_backup.sh"
cat > "$RESTORE_SCRIPT" << EOF
#!/bin/bash

# Auto-restore script for Evennia server
# This script is called by the cron job to restore from the latest backup if needed

# Set the game directory
GAME_DIRECTORY="$GAME_DIRECTORY"

# Set the conda environment
CONDA_ENV="$CONDA_ENV"

# Set the conda paths
CONDA_BASE="/root/miniconda3"
CONDA_SH="\$CONDA_BASE/etc/profile.d/conda.sh"

# Set the Discord webhook URL
DISCORD_WEBHOOK_URL="$DISCORD_WEBHOOK_URL"

# Log file
LOG_FILE="/var/log/evennia_restore.log"

# Function to log messages
log_message() {
    echo "[\$(date '+%Y-%m-%d %H:%M:%S')] \$1" | tee -a "\$LOG_FILE"
}

# Function to send Discord notification
send_discord_notification() {
    local TITLE="\$1"
    local MESSAGE="\$2"
    local COLOR="\$3"
    
    # Get the directory of this script
    SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
    
    # Check if discord_notify.sh exists
    if [ -f "\$SCRIPT_DIR/discord_notify.sh" ]; then
        # Make sure it's executable
        chmod +x "\$SCRIPT_DIR/discord_notify.sh"
        
        # Send the notification
        if ! "\$SCRIPT_DIR/discord_notify.sh" -w "\$DISCORD_WEBHOOK_URL" -t "\$TITLE" -m "\$MESSAGE" -c "\$COLOR"; then
            log_message "WARNING: Failed to send Discord notification: \$TITLE"
        fi
    else
        log_message "WARNING: Discord notification script not found: \$SCRIPT_DIR/discord_notify.sh"
    fi
}

# Function to find the latest backup
find_latest_backup() {
    local BACKUP_DIR="\$GAME_DIRECTORY/../backups/dated"
    if [ ! -d "\$BACKUP_DIR" ]; then
        log_message "Error: Backup directory does not exist: \$BACKUP_DIR"
        return 1
    fi
    
    # Find the most recent backup file
    local LATEST_BACKUP=\$(ls -t "\$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | head -n1)
    if [ -z "\$LATEST_BACKUP" ]; then
        log_message "Error: No backup files found in \$BACKUP_DIR"
        return 1
    fi
    
    echo "\$LATEST_BACKUP"
    return 0
}

# Function to check if restore is needed
check_if_restore_needed() {
    # Check if the server is running
    if ! timeout 5 bash -c "source '\$CONDA_SH' && conda activate '\$CONDA_ENV' && evennia status" | grep -q "running"; then
        log_message "Server is not running, restore may be needed"
        return 0
    fi
    
    # Check for specific error conditions that indicate restore is needed
    if [ -f "\$GAME_DIRECTORY/server/evennia.db3" ]; then
        if ! sqlite3 "\$GAME_DIRECTORY/server/evennia.db3" "SELECT 1;" &>/dev/null; then
            log_message "Database appears to be corrupted, restore may be needed"
            return 0
        fi
    fi
    
    return 1
}

# Change to the game directory
cd "\$GAME_DIRECTORY" || {
    log_message "ERROR: Failed to change to game directory: \$GAME_DIRECTORY"
    if [ -n "\$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Restore Failed" "Failed to change to game directory: \$GAME_DIRECTORY" "0xe74c3c"
    fi
    exit 1
}

# Check if restore is needed
if check_if_restore_needed; then
    log_message "Restore condition detected, attempting to restore from backup"
    
    # Send Discord notification about the restore
    if [ -n "\$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Restore Started" "Restore condition detected, attempting to restore from backup" "0x3498db"
    fi
    
    # Find the latest backup
    LATEST_BACKUP=\$(find_latest_backup)
    if [ -z "\$LATEST_BACKUP" ]; then
        log_message "ERROR: Failed to find latest backup"
        if [ -n "\$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Restore Failed" "Failed to find latest backup" "0xe74c3c"
        fi
        exit 1
    fi
    
    # Create a backup of the current state before restore
    if ! "\$SCRIPT_DIR/backup_game.sh"; then
        log_message "WARNING: Failed to create backup before restore"
        if [ -n "\$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Restore Warning" "Failed to create backup before restore" "0xf39c12"
        fi
    fi
    
    # Extract the backup
    if ! tar -xzf "\$LATEST_BACKUP" -C "\$GAME_DIRECTORY/.."; then
        log_message "ERROR: Failed to extract backup"
        if [ -n "\$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Restore Failed" "Failed to extract backup" "0xe74c3c"
        fi
        exit 1
    fi
    
    # Restart the server
    if ! "\$SCRIPT_DIR/restart_prod.sh"; then
        log_message "ERROR: Failed to restart server after restore"
        if [ -n "\$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Restore Failed" "Failed to restart server after restore" "0xe74c3c"
        fi
        exit 1
    fi
    
    log_message "Server restored and restarted successfully"
    
    # Send Discord notification about the successful restore
    if [ -n "\$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Restore Completed" "Server restored and restarted successfully" "0x2ecc71"
    fi
else
    log_message "No restore needed"
fi

exit 0
EOF

# Make the restore script executable
chmod +x "$RESTORE_SCRIPT"

# Add the cron job
CRON_JOB="*/$INTERVAL * * * * $RESTORE_SCRIPT > /dev/null 2>&1"
(crontab -l 2>/dev/null | grep -v "$RESTORE_SCRIPT"; echo "$CRON_JOB") | crontab -

echo "Auto-restore cron job added successfully"
echo "Check interval: $INTERVAL minutes"
echo "Game directory: $GAME_DIRECTORY"
echo "Conda environment: $CONDA_ENV"
echo "Restore script: $RESTORE_SCRIPT"
echo "Log file: /var/log/evennia_restore.log"

exit 0 