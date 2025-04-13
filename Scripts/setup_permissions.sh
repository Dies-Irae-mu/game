#!/bin/bash

# Script to set appropriate permissions for all files in the Scripts directory
# This script makes all shell scripts executable and sets appropriate permissions

# Function to display usage
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -d, --directory DIR  Directory containing scripts (default: Scripts)"
    echo "  -u, --user USER      User to own the files (default: current user)"
    echo "  -g, --group GROUP    Group to own the files (default: current user's group)"
    echo "  -h, --help           Display this help message"
    exit 1
}

# Default values
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OWNER=$(whoami)
GROUP=$(id -gn)

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--directory)
            SCRIPT_DIR="$2"
            shift 2
            ;;
        -u|--user)
            OWNER="$2"
            shift 2
            ;;
        -g|--group)
            GROUP="$2"
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

# Check if the directory exists
if [ ! -d "$SCRIPT_DIR" ]; then
    echo "Error: Directory does not exist: $SCRIPT_DIR"
    exit 1
fi

# Check if the user exists
if ! id "$OWNER" &>/dev/null; then
    echo "Error: User does not exist: $OWNER"
    exit 1
fi

# Check if the group exists
if ! getent group "$GROUP" &>/dev/null; then
    echo "Error: Group does not exist: $GROUP"
    exit 1
fi

echo "Setting permissions for files in $SCRIPT_DIR"
echo "Owner: $OWNER"
echo "Group: $GROUP"

# Make all shell scripts executable
echo "Making shell scripts executable..."
find "$SCRIPT_DIR" -name "*.sh" -type f -exec chmod +x {} \;

# Set ownership for all files
echo "Setting ownership..."
chown -R "$OWNER:$GROUP" "$SCRIPT_DIR"

# Set appropriate permissions
echo "Setting file permissions..."
# Make shell scripts executable and readable by owner, readable by group and others
find "$SCRIPT_DIR" -name "*.sh" -type f -exec chmod 755 {} \;
# Make other files readable by owner, readable by group and others
find "$SCRIPT_DIR" -not -name "*.sh" -type f -exec chmod 644 {} \;
# Make directories executable and readable by owner, readable and executable by group and others
find "$SCRIPT_DIR" -type d -exec chmod 755 {} \;

# Create log files if they don't exist
echo "Creating log files if they don't exist..."
LOG_FILES=(
    "/var/log/evennia_update.log"
    "/var/log/evennia_restart.log"
    "/var/log/evennia_backup.log"
    "/var/log/evennia_restore.log"
)

for LOG_FILE in "${LOG_FILES[@]}"; do
    if [ ! -f "$LOG_FILE" ]; then
        echo "Creating $LOG_FILE"
        sudo touch "$LOG_FILE"
        sudo chmod 644 "$LOG_FILE"
        sudo chown "$OWNER:$GROUP" "$LOG_FILE"
    else
        echo "Log file already exists: $LOG_FILE"
        sudo chmod 644 "$LOG_FILE"
        sudo chown "$OWNER:$GROUP" "$LOG_FILE"
    fi
done

# Create backups directory if it doesn't exist
BACKUPS_DIR="$(dirname "$SCRIPT_DIR")/backups"
if [ ! -d "$BACKUPS_DIR" ]; then
    echo "Creating backups directory: $BACKUPS_DIR"
    mkdir -p "$BACKUPS_DIR"
    chmod 755 "$BACKUPS_DIR"
    chown "$OWNER:$GROUP" "$BACKUPS_DIR"
else
    echo "Backups directory already exists: $BACKUPS_DIR"
    chmod 755 "$BACKUPS_DIR"
    chown "$OWNER:$GROUP" "$BACKUPS_DIR"
fi

echo "Permissions setup complete!"
echo "All shell scripts are now executable"
echo "Log files have been created or updated"
echo "Backups directory has been created or updated"

# Test Discord webhook if discord_notify.sh exists
if [ -f "$SCRIPT_DIR/discord_notify.sh" ] && [ -f "$SCRIPT_DIR/test_discord_webhook.sh" ]; then
    echo ""
    echo "Would you like to test the Discord webhook? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "Please enter your Discord webhook URL:"
        read -r webhook_url
        if [ -n "$webhook_url" ]; then
            "$SCRIPT_DIR/test_discord_webhook.sh" -w "$webhook_url"
        else
            echo "No webhook URL provided, skipping test"
        fi
    else
        echo "Skipping Discord webhook test"
    fi
fi

exit 0 