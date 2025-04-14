#!/bin/bash

# Evennia Auto-Update System Setup Script
# This script sets up the auto-update system by creating a configuration file
# and setting up the necessary permissions and cron jobs.

# Enable strict error handling
set -euo pipefail

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
CONDA_BASE="/root/miniconda3"
CONDA_SH="/root/miniconda3/etc/profile.d/conda.sh"
PYTHON_VERSION="3.12.4"
CONDA_VERSION="24.5.0"
USER_ID="0"
GROUP_ID="0"
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

# Define log file paths
LOG_DIR="/var/log"
UPDATE_LOG="$LOG_DIR/evennia_update.log"
RESTART_LOG="$LOG_DIR/evennia_restart.log"
BACKUP_LOG="$LOG_DIR/evennia_backup.log"
RESTORE_LOG="$LOG_DIR/evennia_restore.log"

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

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "Error: git command not found"
    exit 1
fi

# Check if the specified branch exists
cd "$GAME_DIRECTORY" || exit 1
if ! git ls-remote --heads origin "$GIT_BRANCH" &> /dev/null; then
    echo "Error: Branch '$GIT_BRANCH' does not exist in the remote repository"
    exit 1
fi

# Check for required scripts
REQUIRED_SCRIPTS=("discord_notify.sh" "backup_game.sh" "restart_prod.sh")
MISSING_SCRIPTS=()

for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [ ! -f "$SCRIPT_DIR/$script" ]; then
        MISSING_SCRIPTS+=("$script")
    fi
done

if [ ${#MISSING_SCRIPTS[@]} -gt 0 ]; then
    echo "Warning: The following required scripts are missing:"
    for script in "${MISSING_SCRIPTS[@]}"; do
        echo "  - $script"
    done
    echo "Please ensure all required scripts are present before running the auto-update system."
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "Warning: conda command not found. The auto-update system may not work correctly."
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if the conda environment exists
if command -v conda &> /dev/null; then
    if ! conda env list | grep -q "^$CONDA_ENV "; then
        echo "Warning: Conda environment '$CONDA_ENV' not found. The auto-update system may not work correctly."
        read -p "Do you want to continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

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
echo "# Conda paths" >> "$CONFIG_FILE"
echo "CONDA_BASE=\"$CONDA_BASE\"" >> "$CONFIG_FILE"
echo "CONDA_SH=\"$CONDA_SH\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Environment versions" >> "$CONFIG_FILE"
echo "PYTHON_VERSION=\"$PYTHON_VERSION\"" >> "$CONFIG_FILE"
echo "CONDA_VERSION=\"$CONDA_VERSION\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# User and group IDs" >> "$CONFIG_FILE"
echo "USER_ID=\"$USER_ID\"" >> "$CONFIG_FILE"
echo "GROUP_ID=\"$GROUP_ID\"" >> "$CONFIG_FILE"
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
echo "# Backup directories" >> "$CONFIG_FILE"
echo "BACKUP_DIR=\"$BACKUP_DIR\"" >> "$CONFIG_FILE"
echo "BACKUP_DATED_DIR=\"$BACKUP_DATED_DIR\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Log files" >> "$CONFIG_FILE"
echo "LOG_DIR=\"$LOG_DIR\"" >> "$CONFIG_FILE"
echo "UPDATE_LOG=\"\$LOG_DIR/evennia_update.log\"" >> "$CONFIG_FILE"
echo "RESTART_LOG=\"\$LOG_DIR/evennia_restart.log\"" >> "$CONFIG_FILE"
echo "BACKUP_LOG=\"\$LOG_DIR/evennia_backup.log\"" >> "$CONFIG_FILE"
echo "RESTORE_LOG=\"\$LOG_DIR/evennia_restore.log\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Script directory (automatically determined)" >> "$CONFIG_FILE"
echo "SCRIPT_DIR=\"$SCRIPT_DIR\"" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Timeout values (in seconds)" >> "$CONFIG_FILE"
echo "STOP_TIMEOUT=60" >> "$CONFIG_FILE"
echo "START_TIMEOUT=120" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"
echo "# Export variables for use in other scripts" >> "$CONFIG_FILE"
echo "export GAME_DIRECTORY" >> "$CONFIG_FILE"
echo "export CONDA_ENV" >> "$CONFIG_FILE"
echo "export CONDA_BASE" >> "$CONFIG_FILE"
echo "export CONDA_SH" >> "$CONFIG_FILE"
echo "export PYTHON_VERSION" >> "$CONFIG_FILE"
echo "export CONDA_VERSION" >> "$CONFIG_FILE"
echo "export USER_ID" >> "$CONFIG_FILE"
echo "export GROUP_ID" >> "$CONFIG_FILE"
echo "export GIT_BRANCH" >> "$CONFIG_FILE"
echo "export UPDATE_INTERVAL" >> "$CONFIG_FILE"
echo "export DISCORD_WEBHOOK_URL" >> "$CONFIG_FILE"
echo "export BACKUP_DIR" >> "$CONFIG_FILE"
echo "export BACKUP_DATED_DIR" >> "$CONFIG_FILE"
echo "export LOG_DIR" >> "$CONFIG_FILE"
echo "export UPDATE_LOG" >> "$CONFIG_FILE"
echo "export RESTART_LOG" >> "$CONFIG_FILE"
echo "export BACKUP_LOG" >> "$CONFIG_FILE"
echo "export RESTORE_LOG" >> "$CONFIG_FILE"
echo "export SCRIPT_DIR" >> "$CONFIG_FILE"
echo "export STOP_TIMEOUT" >> "$CONFIG_FILE"
echo "export START_TIMEOUT" >> "$CONFIG_FILE"

# Make the configuration file executable
chmod +x "$CONFIG_FILE"

# Create log directory if it doesn't exist
if [ ! -d "$LOG_DIR" ]; then
    echo "Creating log directory..."
    if ! mkdir -p "$LOG_DIR" 2>/dev/null; then
        # Try with sudo if regular mkdir fails
        if ! sudo mkdir -p "$LOG_DIR"; then
            echo "Error: Failed to create log directory: $LOG_DIR"
            echo "Please ensure you have the necessary permissions or run this script with sudo."
            exit 1
        fi
    fi
fi

# Create log files if they don't exist
for log_file in "$UPDATE_LOG" "$RESTART_LOG" "$BACKUP_LOG" "$RESTORE_LOG"; do
    if [ ! -f "$log_file" ]; then
        echo "Creating log file: $log_file"
        if ! touch "$log_file" 2>/dev/null; then
            # Try with sudo if regular touch fails
            if ! sudo touch "$log_file"; then
                echo "Error: Failed to create log file: $log_file"
                echo "Please ensure you have the necessary permissions or run this script with sudo."
                exit 1
            fi
        fi
    fi
done

# Set permissions for log files
if ! chmod 644 "$UPDATE_LOG" "$RESTART_LOG" "$BACKUP_LOG" "$RESTORE_LOG" 2>/dev/null; then
    # Try with sudo if regular chmod fails
    if ! sudo chmod 644 "$UPDATE_LOG" "$RESTART_LOG" "$BACKUP_LOG" "$RESTORE_LOG"; then
        echo "Error: Failed to set permissions for log files"
        echo "Please ensure you have the necessary permissions or run this script with sudo."
        exit 1
    fi
fi

# Set ownership of log files to the current user if possible
if ! chown "$USER_ID:$GROUP_ID" "$UPDATE_LOG" "$RESTART_LOG" "$BACKUP_LOG" "$RESTORE_LOG" 2>/dev/null; then
    # Try with sudo if regular chown fails
    if ! sudo chown "$USER_ID:$GROUP_ID" "$UPDATE_LOG" "$RESTART_LOG" "$BACKUP_LOG" "$RESTORE_LOG"; then
        echo "Warning: Failed to set ownership of log files to $USER_ID:$GROUP_ID"
        echo "The log files may not be writable by the current user."
    fi
fi

# Create backup directory if it doesn't exist
BACKUP_DIR="$GAME_DIRECTORY/../backups"
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Creating backup directory..."
    if ! mkdir -p "$BACKUP_DIR" 2>/dev/null; then
        # Try with sudo if regular mkdir fails
        if ! sudo mkdir -p "$BACKUP_DIR"; then
            echo "Error: Failed to create backup directory: $BACKUP_DIR"
            echo "Please ensure you have the necessary permissions or run this script with sudo."
            exit 1
        fi
    fi
fi

# Set permissions for backup directory
if ! chmod 755 "$BACKUP_DIR" 2>/dev/null; then
    # Try with sudo if regular chmod fails
    if ! sudo chmod 755 "$BACKUP_DIR"; then
        echo "Warning: Failed to set permissions for backup directory"
        echo "The backup directory may not be accessible."
    fi
fi

# Set ownership of backup directory to the current user if possible
if ! chown "$USER_ID:$GROUP_ID" "$BACKUP_DIR" 2>/dev/null; then
    # Try with sudo if regular chown fails
    if ! sudo chown "$USER_ID:$GROUP_ID" "$BACKUP_DIR"; then
        echo "Warning: Failed to set ownership of backup directory to $USER_ID:$GROUP_ID"
        echo "The backup directory may not be writable by the current user."
    fi
fi

# Create a subdirectory for dated backups
BACKUP_DATED_DIR="$BACKUP_DIR/dated"
if [ ! -d "$BACKUP_DATED_DIR" ]; then
    echo "Creating dated backup directory..."
    if ! mkdir -p "$BACKUP_DATED_DIR" 2>/dev/null; then
        # Try with sudo if regular mkdir fails
        if ! sudo mkdir -p "$BACKUP_DATED_DIR"; then
            echo "Error: Failed to create dated backup directory: $BACKUP_DATED_DIR"
            echo "Please ensure you have the necessary permissions or run this script with sudo."
            exit 1
        fi
    fi
fi

# Set permissions for dated backup directory
if ! chmod 755 "$BACKUP_DATED_DIR" 2>/dev/null; then
    # Try with sudo if regular chmod fails
    if ! sudo chmod 755 "$BACKUP_DATED_DIR"; then
        echo "Warning: Failed to set permissions for dated backup directory"
        echo "The dated backup directory may not be accessible."
    fi
fi

# Set ownership of dated backup directory to the current user if possible
if ! chown "$USER_ID:$GROUP_ID" "$BACKUP_DATED_DIR" 2>/dev/null; then
    # Try with sudo if regular chown fails
    if ! sudo chown "$USER_ID:$GROUP_ID" "$BACKUP_DATED_DIR"; then
        echo "Warning: Failed to set ownership of dated backup directory to $USER_ID:$GROUP_ID"
        echo "The dated backup directory may not be writable by the current user."
    fi
fi

# Update the config file to include the backup directories
echo "# Backup directories" >> "$CONFIG_FILE"
echo "BACKUP_DIR=\"$BACKUP_DIR\"" >> "$CONFIG_FILE"
echo "BACKUP_DATED_DIR=\"$BACKUP_DATED_DIR\"" >> "$CONFIG_FILE"
echo "export BACKUP_DATED_DIR" >> "$CONFIG_FILE"

# Run setup_permissions.sh to set up permissions
if [ -f "$SCRIPT_DIR/setup_permissions.sh" ]; then
    echo "Setting up permissions..."
    if ! "$SCRIPT_DIR/setup_permissions.sh"; then
        echo "Error: Failed to set up permissions"
        exit 1
    fi
else
    echo "Warning: setup_permissions.sh not found, skipping permission setup"
    # Make all scripts executable as a fallback
    chmod +x "$SCRIPT_DIR"/*.sh
fi

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
echo "# Function to handle errors" >> "$UPDATE_SCRIPT"
echo "error_handler() {" >> "$UPDATE_SCRIPT"
echo "    local exit_code=\$?" >> "$UPDATE_SCRIPT"
echo "    local line_number=\$1" >> "$UPDATE_SCRIPT"
echo "    local function_name=\$2" >> "$UPDATE_SCRIPT"
echo "    log_message \"Error in \$function_name at line \$line_number (exit code: \$exit_code)\"" >> "$UPDATE_SCRIPT"
echo "    send_discord_notification \"Update Failed\" \"Error in \$function_name at line \$line_number (exit code: \$exit_code)\" \"0xe74c3c\"" >> "$UPDATE_SCRIPT"
echo "    exit \$exit_code" >> "$UPDATE_SCRIPT"
echo "}" >> "$UPDATE_SCRIPT"
echo "" >> "$UPDATE_SCRIPT"
echo "# Set up error handling" >> "$UPDATE_SCRIPT"
echo "trap 'error_handler \${LINENO} \"\${FUNCNAME[0]}\"' ERR" >> "$UPDATE_SCRIPT"
echo "" >> "$UPDATE_SCRIPT"
echo "# Main execution" >> "$UPDATE_SCRIPT"
echo "log_message \"Starting auto-update process\"" >> "$UPDATE_SCRIPT"
echo "send_discord_notification \"Auto-Update Started\" \"Starting auto-update process\" \"0x3498db\"" >> "$UPDATE_SCRIPT"
echo "" >> "$UPDATE_SCRIPT"
echo "# Change to game directory" >> "$UPDATE_SCRIPT"
echo "cd \"\$GAME_DIRECTORY\" || { log_message \"Failed to change to game directory\"; exit 1; }" >> "$UPDATE_SCRIPT"
echo "" >> "$UPDATE_SCRIPT"
echo "# Check if git is available" >> "$UPDATE_SCRIPT"
echo "if ! command -v git &> /dev/null; then" >> "$UPDATE_SCRIPT"
echo "    log_message \"Error: git command not found\"" >> "$UPDATE_SCRIPT"
echo "    send_discord_notification \"Update Failed\" \"git command not found\" \"0xe74c3c\"" >> "$UPDATE_SCRIPT"
echo "    exit 1" >> "$UPDATE_SCRIPT"
echo "fi" >> "$UPDATE_SCRIPT"
echo "" >> "$UPDATE_SCRIPT"
echo "# Check if we're in a git repository" >> "$UPDATE_SCRIPT"
echo "if ! git rev-parse --git-dir &> /dev/null; then" >> "$UPDATE_SCRIPT"
echo "    log_message \"Error: Not a git repository: \$GAME_DIRECTORY\"" >> "$UPDATE_SCRIPT"
echo "    send_discord_notification \"Update Failed\" \"Not a git repository\" \"0xe74c3c\"" >> "$UPDATE_SCRIPT"
echo "    exit 1" >> "$UPDATE_SCRIPT"
echo "fi" >> "$UPDATE_SCRIPT"
echo "" >> "$UPDATE_SCRIPT"
echo "# Check if the specified branch exists" >> "$UPDATE_SCRIPT"
echo "if ! git ls-remote --heads origin \"\$GIT_BRANCH\" &> /dev/null; then" >> "$UPDATE_SCRIPT"
echo "    log_message \"Error: Branch '\$GIT_BRANCH' does not exist in the remote repository\"" >> "$UPDATE_SCRIPT"
echo "    send_discord_notification \"Update Failed\" \"Branch '\$GIT_BRANCH' does not exist in the remote repository\" \"0xe74c3c\"" >> "$UPDATE_SCRIPT"
echo "    exit 1" >> "$UPDATE_SCRIPT"
echo "fi" >> "$UPDATE_SCRIPT"
echo "" >> "$UPDATE_SCRIPT"
echo "# Check for uncommitted changes" >> "$UPDATE_SCRIPT"
echo "if [ -n \"\$(git status --porcelain)\" ]; then" >> "$UPDATE_SCRIPT"
echo "    log_message \"Warning: Uncommitted changes detected in the repository\"" >> "$UPDATE_SCRIPT"
echo "    send_discord_notification \"Update Warning\" \"Uncommitted changes detected in the repository\" \"0xf39c12\"" >> "$UPDATE_SCRIPT"
echo "    " >> "$UPDATE_SCRIPT"
echo "    # Create a temporary stash to save uncommitted changes" >> "$UPDATE_SCRIPT"
echo "    log_message \"Creating temporary stash to save uncommitted changes...\"" >> "$UPDATE_SCRIPT"
echo "    if ! git stash push -m \"Auto-stash before update \$(date '+%Y-%m-%d %H:%M:%S')\"; then" >> "$UPDATE_SCRIPT"
echo "        log_message \"Warning: Failed to stash uncommitted changes. Proceeding with update anyway.\"" >> "$UPDATE_SCRIPT"
echo "        send_discord_notification \"Update Warning\" \"Failed to stash uncommitted changes. Proceeding with update anyway.\" \"0xf39c12\"" >> "$UPDATE_SCRIPT"
echo "    else" >> "$UPDATE_SCRIPT"
echo "        log_message \"Uncommitted changes stashed successfully\"" >> "$UPDATE_SCRIPT"
echo "    fi" >> "$UPDATE_SCRIPT"
echo "fi" >> "$UPDATE_SCRIPT"
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

# Check for existing cron jobs
EXISTING_CRON=$(crontab -l 2>/dev/null | grep -c "$UPDATE_SCRIPT" || true)

# Add cron job if it doesn't exist
if [ "$EXISTING_CRON" -eq 0 ]; then
    # Use absolute path for the script in the cron job
    CRON_JOB="*/$UPDATE_INTERVAL * * * * $UPDATE_SCRIPT >> $UPDATE_LOG 2>&1"
    
    # Check if we can modify the crontab
    if ! (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab - 2>/dev/null; then
        echo "Error: Failed to add cron job. You may need to run this script with sudo or ensure you have permission to modify the crontab."
        echo "You can manually add the following line to your crontab:"
        echo "$CRON_JOB"
    else
        echo "Cron job added to run every $UPDATE_INTERVAL minutes"
    fi
else
    echo "Cron job for $UPDATE_SCRIPT already exists, skipping"
fi

echo "Setup completed successfully!"
echo "Configuration file created at: $CONFIG_FILE"
echo "Update script created at: $UPDATE_SCRIPT"
echo ""
echo "You can edit the configuration file at any time to change settings."
echo "The configuration file is ignored by git." 