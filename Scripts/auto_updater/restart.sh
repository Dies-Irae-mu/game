#!/bin/bash

#=============================================================================
# Evennia Auto-Update System - Server Restart Script
#=============================================================================
#
# PURPOSE:
#   This script manages the restart process for the Evennia game server, including:
#   1. Stopping the current server instance
#   2. Creating a backup before restart
#   3. Starting a new server instance
#   4. Verifying the server is running correctly
#
# USAGE:
#   ./restart.sh [options]
#
# OPTIONS:
#   -f, --force    - Force restart without confirmation
#   -b, --backup   - Create a backup before restart (default: yes)
#   -n, --nobackup - Skip backup before restart
#   -h, --help     - Display help message
#
# EXAMPLES:
#   ./restart.sh           # Restart with confirmation and backup
#   ./restart.sh --force   # Force restart without confirmation
#   ./restart.sh --nobackup # Restart without creating a backup
#
# DEPENDENCIES:
#   - The config.sh file must exist and be properly configured
#   - The conda environment must be properly set up
#   - The game directory must be a valid Evennia installation
#
# OUTPUT:
#   - Logs all operations to the restart log file
#   - Sends Discord notifications for important events
#   - Creates backups before restart (if enabled)
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
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  restart - Restart the Evennia server"
    echo "  status  - Check server status"
    echo ""
    echo "Examples:"
    echo "  $0 restart # Restart the server"
    echo "  $0 status  # Check server status"
    exit 1
}

# Function to log messages
log_message() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" | tee -a "$RESTART_LOG"
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

# Function to check if the server is running
check_server() {
    if pgrep -f "evennia" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to restart the server
restart_server() {
    log_message "Restarting Evennia server..."
    send_discord_notification "Restarting Evennia server"

    # Create a backup before restarting
    if ! "$SCRIPT_DIR/backup.sh" create "pre_restart"; then
        log_message "Failed to create backup before restart"
        send_discord_notification "Failed to create backup before restart"
        return 1
    fi

    # Restart the server using evennia restart command
    log_message "Executing evennia restart command..."
    if ! cd "$GAME_DIRECTORY" && source "$CONDA_SH" && conda activate "$CONDA_ENV" && evennia restart; then
        log_message "Failed to restart server using evennia restart"
        send_discord_notification "Failed to restart server using evennia restart"
        return 1
    fi

    # Wait for server to restart
    local timeout=$START_TIMEOUT
    while [ $timeout -gt 0 ]; do
        if check_server; then
            log_message "Server restarted successfully"
            send_discord_notification "Server restarted successfully"
            return 0
        fi
        sleep 1
        timeout=$((timeout - 1))
    done

    log_message "Server failed to restart within timeout"
    send_discord_notification "Server failed to restart within timeout"
    return 1
}

# Function to check server status
check_status() {
    if check_server; then
        echo "Server is running"
        return 0
    else
        echo "Server is not running"
        return 1
    fi
}

# Main script
case "${1:-}" in
    restart)
        restart_server
        ;;
    status)
        check_status
        ;;
    *)
        usage
        ;;
esac

exit 0 