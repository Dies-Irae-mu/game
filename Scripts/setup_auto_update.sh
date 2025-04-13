#!/bin/bash

# Script to set up auto-update cron job for Evennia server
# This script creates a cron job to automatically update and restart the Evennia server

# Function to display usage
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -b, --branch BRANCH      Git branch to pull from (default: main)"
    echo "  -i, --interval MINUTES   Update interval in minutes (default: 60)"
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

# Create a temporary update script
UPDATE_SCRIPT="$SCRIPT_DIR/update_game.sh"
cat > "$UPDATE_SCRIPT" << EOF
#!/bin/bash

# Auto-update script for Evennia server
# This script is called by the cron job to update and restart the Evennia server

# Set the game directory
GAME_DIRECTORY="$GAME_DIRECTORY"

# Set the conda environment
CONDA_ENV="$CONDA_ENV"

# Set the Discord webhook URL
DISCORD_WEBHOOK_URL="$DISCORD_WEBHOOK_URL"

# Log file
LOG_FILE="/var/log/evennia_update.log"

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

# Change to the game directory
cd "\$GAME_DIRECTORY" || {
    log_message "ERROR: Failed to change to game directory: \$GAME_DIRECTORY"
    if [ -n "\$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Update Failed" "Failed to change to game directory: \$GAME_DIRECTORY" "0xe74c3c"
    fi
    exit 1
}

# Check if there are any changes to pull
git fetch origin "$BRANCH" || {
    log_message "ERROR: Failed to fetch from origin: $BRANCH"
    if [ -n "\$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Update Failed" "Failed to fetch from origin: $BRANCH" "0xe74c3c"
    fi
    exit 1
}

# Check if there are any changes to pull
if ! git diff --quiet HEAD origin/$BRANCH; then
    log_message "Changes detected, pulling from origin: $BRANCH"
    
    # Send Discord notification about the update
    if [ -n "\$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Update Started" "Pulling changes from origin: $BRANCH" "0x3498db"
    fi
    
    # Pull the changes
    if ! git pull origin "$BRANCH"; then
        log_message "ERROR: Failed to pull from origin: $BRANCH"
        if [ -n "\$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Update Failed" "Failed to pull from origin: $BRANCH" "0xe74c3c"
        fi
        exit 1
    fi
    
    log_message "Changes pulled successfully, restarting server"
    
    # Restart the server
    if ! "\$SCRIPT_DIR/restart_prod.sh"; then
        log_message "ERROR: Failed to restart server"
        if [ -n "\$DISCORD_WEBHOOK_URL" ]; then
            send_discord_notification "Update Failed" "Failed to restart server" "0xe74c3c"
        fi
        exit 1
    fi
    
    log_message "Server restarted successfully"
    
    # Send Discord notification about the successful update
    if [ -n "\$DISCORD_WEBHOOK_URL" ]; then
        send_discord_notification "Update Completed" "Changes pulled and server restarted successfully" "0x2ecc71"
    fi
else
    log_message "No changes detected"
fi

exit 0
EOF

# Make the update script executable
chmod +x "$UPDATE_SCRIPT"

# Add the cron job
CRON_JOB="*/$INTERVAL * * * * $UPDATE_SCRIPT > /dev/null 2>&1"
(crontab -l 2>/dev/null | grep -v "$UPDATE_SCRIPT"; echo "$CRON_JOB") | crontab -

echo "Auto-update cron job added successfully"
echo "Update interval: $INTERVAL minutes"
echo "Git branch: $BRANCH"
echo "Game directory: $GAME_DIRECTORY"
echo "Conda environment: $CONDA_ENV"
echo "Update script: $UPDATE_SCRIPT"
echo "Log file: /var/log/evennia_update.log"

exit 0 