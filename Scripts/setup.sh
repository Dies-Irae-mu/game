#!/bin/bash

# Evennia Auto-Update System Setup Script
# This script sets up the auto-update system by creating a configuration file
# and setting up the necessary permissions and cron jobs.

set -e

# Function to display usage information
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -d, --directory DIR     Game directory path (default: /root/game)"
    echo "  -e, --env ENV           Conda environment name (default: game_py311)"
    echo "  -b, --branch BRANCH     Git branch to pull from (default: main)"
    echo "  -i, --interval MIN      Update interval in minutes (default: 60)"
    echo "  -w, --webhook URL       Discord webhook URL (optional)"
    echo "  -h, --help              Display this help message"
    exit 1
}

# Default values
GAME_DIRECTORY="/root/game"
CONDA_ENV="game_py311"
GIT_BRANCH="main"
UPDATE_INTERVAL=60
DISCORD_WEBHOOK_URL=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--directory)
            GAME_DIRECTORY="$2"
            shift 2
            ;;
        -e|--env)
            CONDA_ENV="$2"
            shift 2
            ;;
        -b|--branch)
            GIT_BRANCH="$2"
            shift 2
            ;;
        -i|--interval)
            UPDATE_INTERVAL="$2"
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

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create configuration file
CONFIG_FILE="$SCRIPT_DIR/config.sh"
echo "#!/bin/bash" > "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Evennia Auto-Update System Configuration" >> "$CONFIG_FILE"
echo "# This file contains configuration variables for all scripts" >> "$CONFIG_FILE"
echo "# Edit this file to configure your environment" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Game directory path" >> "$CONFIG_FILE"
echo "GAME_DIRECTORY=\"$GAME_DIRECTORY\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Conda environment name" >> "$CONFIG_FILE"
echo "CONDA_ENV=\"$CONDA_ENV\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Git branch to pull from" >> "$CONFIG_FILE"
echo "GIT_BRANCH=\"$GIT_BRANCH\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Update interval in minutes" >> "$CONFIG_FILE"
echo "UPDATE_INTERVAL=$UPDATE_INTERVAL" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Discord webhook URL" >> "$CONFIG_FILE"
echo "DISCORD_WEBHOOK_URL=\"$DISCORD_WEBHOOK_URL\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Backup directory (relative to game directory)" >> "$CONFIG_FILE"
echo "BACKUP_DIR=\"../backups\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Log files" >> "$CONFIG_FILE"
echo "LOG_DIR=\"/var/log\"" >> "$CONFIG_FILE"
echo "UPDATE_LOG=\"\$LOG_DIR/evennia_update.log\"" >> "$CONFIG_FILE"
echo "RESTART_LOG=\"\$LOG_DIR/evennia_restart.log\"" >> "$CONFIG_FILE"
echo "BACKUP_LOG=\"\$LOG_DIR/evennia_backup.log\"" >> "$CONFIG_FILE"
echo "RESTORE_LOG=\"\$LOG_DIR/evennia_restore.log\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Script directory (automatically determined)" >> "$CONFIG_FILE"
echo "SCRIPT_DIR=\"$SCRIPT_DIR\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Export variables for use in other scripts" >> "$CONFIG_FILE"
echo "export GAME_DIRECTORY" >> "$CONFIG_FILE"
echo "export CONDA_ENV" >> "$CONFIG_FILE"
echo "export GIT_BRANCH" >> "$CONFIG_FILE"
echo "export UPDATE_INTERVAL" >> "$CONFIG_FILE"
echo "export DISCORD_WEBHOOK_URL" >> "$CONFIG_FILE"
echo "export BACKUP_DIR" >> "$CONFIG_FILE"
echo "export LOG_DIR" >> "$CONFIG_FILE"
echo "export UPDATE_LOG" >> "$CONFIG_FILE"
echo "export RESTART_LOG" >> "$CONFIG_FILE"
echo "export BACKUP_LOG" >> "$CONFIG_FILE"
echo "export RESTORE_LOG" >> "$CONFIG_FILE"
echo "export SCRIPT_DIR" >> "$CONFIG_FILE"

# Make the configuration file executable
chmod +x "$CONFIG_FILE"

# Create log directory if it doesn't exist
if [ ! -d "/var/log" ]; then
    echo "Creating log directory..."
    sudo mkdir -p /var/log
fi

# Create log files if they don't exist
touch "$UPDATE_LOG" "$RESTART_LOG" "$BACKUP_LOG" "$RESTORE_LOG"

# Set permissions for log files
sudo chmod 644 "$UPDATE_LOG" "$RESTART_LOG" "$BACKUP_LOG" "$RESTORE_LOG"

# Make all scripts executable
chmod +x "$SCRIPT_DIR"/*.sh

# Create .gitignore file if it doesn't exist
if [ ! -f "$SCRIPT_DIR/.gitignore" ]; then
    echo "Creating .gitignore file..."
    echo "config.sh" > "$SCRIPT_DIR/.gitignore"
fi

# Create update script
UPDATE_SCRIPT="$SCRIPT_DIR/update_game.sh"
echo "#!/bin/bash" > "$UPDATE_SCRIPT"
echo "" >> "$UPDATE_SCRIPT"
echo "# Import configuration" >> "$UPDATE_SCRIPT"
echo "source \"$CONFIG_FILE\"" >> "$UPDATE_SCRIPT"
echo "" >> "$UPDATE_SCRIPT"
echo "# Log file for this script" >> "$UPDATE_SCRIPT"
echo "LOG_FILE=\"\$UPDATE_LOG\"" >> "$UPDATE_SCRIPT"
echo "" >> "$UPDATE_SCRIPT"
echo "# Function to log messages" >> "$UPDATE_SCRIPT"
echo "log_message() {" >> "$UPDATE_SCRIPT"
echo "    echo \"\$(date '+%Y-%m-%d %H:%M:%S') - \$1\" | tee -a \"\$LOG_FILE\"" >> "$UPDATE_SCRIPT"
echo "}" >> "$UPDATE_SCRIPT"
echo "" >> "$UPDATE_SCRIPT"
echo "# Function to send Discord notification" >> "$UPDATE_SCRIPT"
echo "send_discord_notification() {" >> "$UPDATE_SCRIPT"
echo "    if [ -n \"\$DISCORD_WEBHOOK_URL\" ]; then" >> "$UPDATE_SCRIPT"
echo "        \"\$SCRIPT_DIR/discord_notify.sh\" -w \"\$DISCORD_WEBHOOK_URL\" -t \"\$1\" -m \"\$2\" -c \"\$3\"" >> "$UPDATE_SCRIPT"
echo "    fi" >> "$UPDATE_SCRIPT"
echo "}" >> "$UPDATE_SCRIPT"
echo "" >> "$UPDATE_SCRIPT"
echo "# Main execution" >> "$UPDATE_SCRIPT"
echo "log_message \"Starting auto-update process\"" >> "$UPDATE_SCRIPT"
echo "send_discord_notification \"Auto-Update Started\" \"Starting auto-update process\" \"0x3498db\"" >> "$UPDATE_SCRIPT"
echo "" >> "$UPDATE_SCRIPT"
echo "# Change to game directory" >> "$UPDATE_SCRIPT"
echo "cd \"\$GAME_DIRECTORY\" || { log_message \"Failed to change to game directory\"; exit 1; }" >> "$UPDATE_SCRIPT"
echo "" >> "$UPDATE_SCRIPT"
echo "# Pull latest changes" >> "$UPDATE_SCRIPT"
echo "log_message \"Pulling latest changes from \$GIT_BRANCH branch\"" >> "$UPDATE_SCRIPT"
echo "if ! git pull origin \"\$GIT_BRANCH\"; then" >> "$UPDATE_SCRIPT"
echo "    log_message \"Failed to pull latest changes\"" >> "$UPDATE_SCRIPT"
echo "    send_discord_notification \"Auto-Update Failed\" \"Failed to pull latest changes from \$GIT_BRANCH branch\" \"0xe74c3c\"" >> "$UPDATE_SCRIPT"
echo "    exit 1" >> "$UPDATE_SCRIPT"
echo "fi" >> "$UPDATE_SCRIPT"
echo "" >> "$UPDATE_SCRIPT"
echo "# Restart the server" >> "$UPDATE_SCRIPT"
echo "log_message \"Restarting Evennia server\"" >> "$UPDATE_SCRIPT"
echo "if \"\$SCRIPT_DIR/restart_prod.sh\"; then" >> "$UPDATE_SCRIPT"
echo "    log_message \"Auto-update completed successfully\"" >> "$UPDATE_SCRIPT"
echo "    send_discord_notification \"Auto-Update Successful\" \"Server updated and restarted successfully\" \"0x2ecc71\"" >> "$UPDATE_SCRIPT"
echo "else" >> "$UPDATE_SCRIPT"
echo "    log_message \"Auto-update failed\"" >> "$UPDATE_SCRIPT"
echo "    send_discord_notification \"Auto-Update Failed\" \"Failed to restart server after update\" \"0xe74c3c\"" >> "$UPDATE_SCRIPT"
echo "    exit 1" >> "$UPDATE_SCRIPT"
echo "fi" >> "$UPDATE_SCRIPT"

# Make the update script executable
chmod +x "$UPDATE_SCRIPT"

# Add cron job
CRON_JOB="*/$UPDATE_INTERVAL * * * * $UPDATE_SCRIPT >> $UPDATE_LOG 2>&1"
(crontab -l 2>/dev/null | grep -v "$UPDATE_SCRIPT"; echo "$CRON_JOB") | crontab -

echo "Setup completed successfully!"
echo "Configuration file created at: $CONFIG_FILE"
echo "Update script created at: $UPDATE_SCRIPT"
echo "Cron job added to run every $UPDATE_INTERVAL minutes"
echo ""
echo "You can edit the configuration file at any time to change settings."
echo "The configuration file is ignored by git." 