#!/bin/bash

# Script to create a backup of the game directory
# This script creates a backup of the game directory and a restore script

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

# Function to display usage
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -d, --directory DIR      Game directory path (default: /root/game)"
    echo "  -n, --name NAME          Custom backup name (default: timestamp)"
    echo "  -w, --webhook URL        Discord webhook URL for notifications"
    echo "  -h, --help               Display this help message"
    exit 1
}

# Default values
GAME_DIRECTORY="/root/game"
BACKUP_NAME=""
DISCORD_WEBHOOK_URL=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--directory)
            GAME_DIRECTORY="$2"
            shift 2
            ;;
        -n|--name)
            BACKUP_NAME="$2"
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

# Log file
LOG_FILE="/var/log/evennia_backup.log"

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

# Check if the game directory exists
if [ ! -d "$GAME_DIRECTORY" ]; then
    log_message "ERROR: Game directory does not exist: $GAME_DIRECTORY"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Backup Failed" "Game directory does not exist: $GAME_DIRECTORY" "0xe74c3c"
    fi
    exit 1
fi

# Get the parent directory of the game directory
PARENT_DIR=$(dirname "$GAME_DIRECTORY")
BACKUPS_DIR="$PARENT_DIR/backups"

# Create the backups directory if it doesn't exist
if [ ! -d "$BACKUPS_DIR" ]; then
    log_message "Creating backups directory: $BACKUPS_DIR"
    if ! mkdir -p "$BACKUPS_DIR"; then
        log_message "ERROR: Failed to create backups directory: $BACKUPS_DIR"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Backup Failed" "Failed to create backups directory: $BACKUPS_DIR" "0xe74c3c"
        fi
        exit 1
    fi
fi

# Generate a backup name if not provided
if [ -z "$BACKUP_NAME" ]; then
    BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
fi

# Create the backup directory
BACKUP_DIR="$BACKUPS_DIR/$BACKUP_NAME"
log_message "Creating backup directory: $BACKUP_DIR"
if ! mkdir -p "$BACKUP_DIR"; then
    log_message "ERROR: Failed to create backup directory: $BACKUP_DIR"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Backup Failed" "Failed to create backup directory: $BACKUP_DIR" "0xe74c3c"
    fi
    exit 1
fi

# Send Discord notification about the backup
if [ -n "$DISCORD_WEBHOOK_URL" ]; then
    send_discord_notification "Backup Started" "Creating backup: $BACKUP_NAME" "0x3498db"
fi

# Create a backup of the game directory
log_message "Creating backup of $GAME_DIRECTORY to $BACKUP_DIR"
if ! cd "$GAME_DIRECTORY"; then
    log_message "ERROR: Failed to change to game directory: $GAME_DIRECTORY"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Backup Failed" "Failed to change to game directory: $GAME_DIRECTORY" "0xe74c3c"
    fi
    exit 1
fi

# Check if tar is installed
if ! command -v tar &> /dev/null; then
    log_message "ERROR: tar is not installed or not in PATH"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Backup Failed" "tar is not installed or not in PATH" "0xe74c3c"
    fi
    exit 1
fi

# Use tar to create a compressed backup, excluding certain files
if ! tar --exclude="*.db3" \
    --exclude="*.sqlite3" \
    --exclude="server/logs/*.log*" \
    --exclude="server/logs/*.pid" \
    --exclude="server/logs/*.restart" \
    --exclude="server/.static/*" \
    --exclude="server/.media/*" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude="*.pyo" \
    --exclude="*.pyd" \
    --exclude=".git" \
    --exclude="venv" \
    --exclude="env" \
    --exclude=".env" \
    --exclude=".venv" \
    -czf "$BACKUP_DIR/game_backup.tar.gz" .; then
    
    log_message "ERROR: Failed to create backup archive with exit code $?"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Backup Failed" "Failed to create backup archive with exit code $?" "0xe74c3c"
    fi
    
    # Clean up the backup directory
    rm -rf "$BACKUP_DIR"
    exit 1
fi

# Check if the backup was successful
if [ $? -eq 0 ]; then
    log_message "Backup created successfully: $BACKUP_NAME"
    
    # Create a symlink to the latest backup
    if ! ln -sf "$BACKUP_DIR" "$BACKUPS_DIR/latest"; then
        log_message "WARNING: Failed to create symlink to latest backup: $BACKUPS_DIR/latest"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Backup Warning" "Failed to create symlink to latest backup: $BACKUPS_DIR/latest" "0xf39c12"
        fi
    else
        log_message "Created symlink to latest backup: $BACKUPS_DIR/latest"
    fi
    
    # Send Discord notification about the successful backup
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Backup Completed" "Backup created successfully: $BACKUP_NAME" "0x2ecc71"
    fi
else
    log_message "ERROR: Failed to create backup: $BACKUP_NAME with exit code $?"
    
    # Send Discord notification about the failed backup
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Backup Failed" "Failed to create backup: $BACKUP_NAME with exit code $?" "0xe74c3c"
    fi
    
    # Clean up the backup directory
    rm -rf "$BACKUP_DIR"
    exit 1
fi

# Create a restore script if it doesn't exist
RESTORE_SCRIPT="$BACKUPS_DIR/restore_backup.sh"
if [ ! -f "$RESTORE_SCRIPT" ]; then
    log_message "Creating restore script: $RESTORE_SCRIPT"
    if ! cat > "$RESTORE_SCRIPT" << 'EOF'
#!/bin/bash

# Script to restore a backup of the game directory
# This script restores a backup of the game directory

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

# Function to display usage
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -b, --backup NAME        Backup name to restore (default: latest)"
    echo "  -d, --directory DIR      Game directory path (default: /root/game)"
    echo "  -w, --webhook URL        Discord webhook URL for notifications"
    echo "  -h, --help               Display this help message"
    exit 1
}

# Default values
BACKUP_NAME="latest"
GAME_DIRECTORY="/root/game"
DISCORD_WEBHOOK_URL=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -b|--backup)
            BACKUP_NAME="$2"
            shift 2
            ;;
        -d|--directory)
            GAME_DIRECTORY="$2"
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

# Log file
LOG_FILE="/var/log/evennia_restore.log"

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
    if [ -f "$SCRIPT_DIR/../discord_notify.sh" ]; then
        # Make sure it's executable
        chmod +x "$SCRIPT_DIR/../discord_notify.sh"
        
        # Send the notification
        if ! "$SCRIPT_DIR/../discord_notify.sh" -w "$DISCORD_WEBHOOK_URL" -t "$TITLE" -m "$MESSAGE" -c "$COLOR"; then
            log_message "WARNING: Failed to send Discord notification: $TITLE"
        fi
    else
        log_message "WARNING: Discord notification script not found: $SCRIPT_DIR/../discord_notify.sh"
    fi
}

# Check if the game directory exists
if [ ! -d "$GAME_DIRECTORY" ]; then
    log_message "ERROR: Game directory does not exist: $GAME_DIRECTORY"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Restore Failed" "Game directory does not exist: $GAME_DIRECTORY" "0xe74c3c"
    fi
    exit 1
fi

# Get the parent directory of the game directory
PARENT_DIR=$(dirname "$GAME_DIRECTORY")
BACKUPS_DIR="$PARENT_DIR/backups"

# Check if the backups directory exists
if [ ! -d "$BACKUPS_DIR" ]; then
    log_message "ERROR: Backups directory does not exist: $BACKUPS_DIR"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Restore Failed" "Backups directory does not exist: $BACKUPS_DIR" "0xe74c3c"
    fi
    exit 1
fi

# Check if the backup exists
if [ "$BACKUP_NAME" = "latest" ]; then
    BACKUP_DIR="$BACKUPS_DIR/latest"
else
    BACKUP_DIR="$BACKUPS_DIR/$BACKUP_NAME"
fi

if [ ! -d "$BACKUP_DIR" ]; then
    log_message "ERROR: Backup does not exist: $BACKUP_NAME"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Restore Failed" "Backup does not exist: $BACKUP_NAME" "0xe74c3c"
    fi
    exit 1
fi

# Check if the backup archive exists
if [ ! -f "$BACKUP_DIR/game_backup.tar.gz" ]; then
    log_message "ERROR: Backup archive does not exist: $BACKUP_DIR/game_backup.tar.gz"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Restore Failed" "Backup archive does not exist: $BACKUP_DIR/game_backup.tar.gz" "0xe74c3c"
    fi
    exit 1
fi

# Send Discord notification about the restore
if [ -n "$DISCORD_WEBHOOK_URL" ]; then
    send_discord_notification "Restore Started" "Restoring backup: $BACKUP_NAME to $GAME_DIRECTORY" "0x3498db"
fi

# Create a backup of the current state
CURRENT_BACKUP_NAME="pre_restore_backup_$(date +%Y%m%d_%H%M%S)"
CURRENT_BACKUP_DIR="$BACKUPS_DIR/$CURRENT_BACKUP_NAME"
log_message "Creating backup of current state: $CURRENT_BACKUP_NAME"
if ! mkdir -p "$CURRENT_BACKUP_DIR"; then
    log_message "ERROR: Failed to create current state backup directory: $CURRENT_BACKUP_DIR"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Restore Failed" "Failed to create current state backup directory: $CURRENT_BACKUP_DIR" "0xe74c3c"
    fi
    exit 1
fi

# Check if tar is installed
if ! command -v tar &> /dev/null; then
    log_message "ERROR: tar is not installed or not in PATH"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Restore Failed" "tar is not installed or not in PATH" "0xe74c3c"
    fi
    exit 1
fi

# Use tar to create a compressed backup of the current state
if ! cd "$GAME_DIRECTORY"; then
    log_message "ERROR: Failed to change to game directory: $GAME_DIRECTORY"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Restore Failed" "Failed to change to game directory: $GAME_DIRECTORY" "0xe74c3c"
    fi
    exit 1
fi

if ! tar --exclude="*.db3" \
    --exclude="*.sqlite3" \
    --exclude="server/logs/*.log*" \
    --exclude="server/logs/*.pid" \
    --exclude="server/logs/*.restart" \
    --exclude="server/.static/*" \
    --exclude="server/.media/*" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude="*.pyo" \
    --exclude="*.pyd" \
    --exclude=".git" \
    --exclude="venv" \
    --exclude="env" \
    --exclude=".env" \
    --exclude=".venv" \
    -czf "$CURRENT_BACKUP_DIR/game_backup.tar.gz" .; then
    
    log_message "ERROR: Failed to create current state backup archive with exit code $?"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Restore Failed" "Failed to create current state backup archive with exit code $?" "0xe74c3c"
    fi
    
    # Clean up the backup directory
    rm -rf "$CURRENT_BACKUP_DIR"
    exit 1
fi

# Check if the backup was successful
if [ $? -ne 0 ]; then
    log_message "ERROR: Failed to create backup of current state: $CURRENT_BACKUP_NAME with exit code $?"
    rm -rf "$CURRENT_BACKUP_DIR"
    
    # Send Discord notification about the failed backup
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Pre-Restore Backup Failed" "Failed to create backup of current state before restore with exit code $?" "0xe74c3c"
    fi
    
    exit 1
fi

# Stop the Evennia server if it's running
log_message "Stopping Evennia server"
if pgrep -f "evennia" > /dev/null; then
    if ! cd "$GAME_DIRECTORY"; then
        log_message "ERROR: Failed to change to game directory: $GAME_DIRECTORY"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Restore Failed" "Failed to change to game directory: $GAME_DIRECTORY" "0xe74c3c"
        fi
        exit 1
    fi
    
    if ! evennia stop; then
        log_message "WARNING: Failed to stop Evennia server gracefully, attempting to force stop"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Restore Warning" "Failed to stop Evennia server gracefully, attempting to force stop" "0xf39c12"
        fi
        
        # Force stop the server
        if pgrep -f "evennia" > /dev/null; then
            pkill -f "evennia"
            sleep 2
            
            # Check if server is still running
            if pgrep -f "evennia" > /dev/null; then
                log_message "ERROR: Failed to force stop Evennia server"
                if [ -n "$DISCORD_WEBHOOK_URL" ]; then
                    send_discord_notification "Restore Failed" "Failed to force stop Evennia server" "0xe74c3c"
                fi
                exit 1
            fi
        fi
    fi
    
    sleep 5
fi

# Restore the backup
log_message "Restoring backup: $BACKUP_NAME to $GAME_DIRECTORY"
if ! cd "$GAME_DIRECTORY"; then
    log_message "ERROR: Failed to change to game directory: $GAME_DIRECTORY"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Restore Failed" "Failed to change to game directory: $GAME_DIRECTORY" "0xe74c3c"
    fi
    exit 1
fi

# Remove all files except the Scripts directory
if ! find . -maxdepth 1 -not -name "Scripts" -not -name "." -not -name ".." -exec rm -rf {} \; 2>/dev/null; then
    log_message "WARNING: Some files could not be removed before restore"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Restore Warning" "Some files could not be removed before restore" "0xf39c12"
    fi
fi

# Extract the backup
if ! tar -xzf "$BACKUP_DIR/game_backup.tar.gz"; then
    log_message "ERROR: Failed to extract backup archive with exit code $?"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Restore Failed" "Failed to extract backup archive with exit code $?" "0xe74c3c"
    fi
    
    # Try to restore the current state
    log_message "Attempting to restore current state: $CURRENT_BACKUP_NAME"
    if ! tar -xzf "$CURRENT_BACKUP_DIR/game_backup.tar.gz"; then
        log_message "ERROR: Failed to restore current state with exit code $?"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Restore Failed" "Failed to restore current state with exit code $?" "0xe74c3c"
        fi
    fi
    
    exit 1
fi

# Check if the restore was successful
if [ $? -eq 0 ]; then
    log_message "Backup restored successfully: $BACKUP_NAME"
    
    # Start the Evennia server
    log_message "Starting Evennia server"
    if ! evennia start; then
        log_message "ERROR: Failed to start Evennia server with exit code $?"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Restore Warning" "Backup restored successfully but failed to start Evennia server with exit code $?" "0xf39c12"
        fi
    else
        log_message "Evennia server started successfully"
    fi
    
    # Send Discord notification about the successful restore
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Restore Completed" "Backup restored successfully: $BACKUP_NAME" "0x2ecc71"
    fi
else
    log_message "ERROR: Failed to restore backup: $BACKUP_NAME with exit code $?"
    
    # Send Discord notification about the failed restore
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Restore Failed" "Failed to restore backup: $BACKUP_NAME with exit code $?" "0xe74c3c"
    fi
    
    # Restore the current state
    log_message "Restoring current state: $CURRENT_BACKUP_NAME"
    if ! cd "$GAME_DIRECTORY"; then
        log_message "ERROR: Failed to change to game directory: $GAME_DIRECTORY"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Restore Failed" "Failed to change to game directory: $GAME_DIRECTORY" "0xe74c3c"
        fi
        exit 1
    fi
    
    # Remove all files except the Scripts directory
    if ! find . -maxdepth 1 -not -name "Scripts" -not -name "." -not -name ".." -exec rm -rf {} \; 2>/dev/null; then
        log_message "WARNING: Some files could not be removed before restoring current state"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Restore Warning" "Some files could not be removed before restoring current state" "0xf39c12"
        fi
    fi
    
    # Extract the current state
    if ! tar -xzf "$CURRENT_BACKUP_DIR/game_backup.tar.gz"; then
        log_message "ERROR: Failed to restore current state with exit code $?"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Restore Failed" "Failed to restore current state with exit code $?" "0xe74c3c"
        fi
        exit 1
    fi
    
    # Start the Evennia server
    log_message "Starting Evennia server"
    if ! evennia start; then
        log_message "ERROR: Failed to start Evennia server with exit code $?"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Restore Warning" "Current state restored but failed to start Evennia server with exit code $?" "0xf39c12"
        fi
    else
        log_message "Evennia server started successfully"
    fi
    
    exit 1
fi

log_message "Restore process completed"
exit 0
EOF
    then
        log_message "ERROR: Failed to create restore script: $RESTORE_SCRIPT"
        if [ -n "$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Backup Warning" "Failed to create restore script: $RESTORE_SCRIPT" "0xf39c12"
        fi
    else
        # Make the restore script executable
        if ! chmod +x "$RESTORE_SCRIPT"; then
            log_message "ERROR: Failed to make restore script executable: $RESTORE_SCRIPT"
            if [ -n "$DISCORD_WEBHOOK_URL" ]; then
                send_discord_notification "Backup Warning" "Failed to make restore script executable: $RESTORE_SCRIPT" "0xf39c12"
            fi
        else
            log_message "Made restore script executable: $RESTORE_SCRIPT"
        fi
    fi
fi

log_message "Backup process completed"
exit 0 