#!/bin/bash

#=============================================================================
# Evennia Auto-Update System - Server Restart Script
#=============================================================================
#
# PURPOSE:
#   This script manages the restart process for the Evennia game server, including:
#   1. Stopping the current server instance
#   2. Starting a new server instance
#   3. Verifying the server is running correctly
#
# USAGE:
#   ./restart.sh [options]
#
# OPTIONS:
#   -f, --force    - Force restart without confirmation
#   -h, --help     - Display help message
#
# EXAMPLES:
#   ./restart.sh           # Restart with confirmation
#   ./restart.sh --force   # Force restart without confirmation
#
# DEPENDENCIES:
#   - The config.sh file must exist and be properly configured
#   - The conda environment must be properly set up
#   - The game directory must be a valid Evennia installation
#
# OUTPUT:
#   - Logs all operations to the restart log file
#   - Sends Discord notifications for important events
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

# Function to get server status details
get_server_status() {
    local status="Not Running"
    local uptime="N/A"
    local commit_hash="N/A"
    local commit_msg="N/A"
    
    # Check if server is running
    if check_server; then
        status="Running"
        # Get server uptime from process
        local pids=$(pgrep -f "evennia")
        if [ -n "$pids" ]; then
            # Count the number of processes
            local process_count=$(echo "$pids" | wc -l)
            
            # Try different methods to get uptime for the first process
            local first_pid=$(echo "$pids" | head -n 1)
            if command -v ps >/dev/null 2>&1; then
                # Try etime format first
                uptime=$(ps -o etime= -p "$first_pid" 2>/dev/null)
                # If that fails, try elapsed format
                if [ -z "$uptime" ]; then
                    uptime=$(ps -o elapsed= -p "$first_pid" 2>/dev/null)
                fi
                # If both fail, try to get start time and calculate
                if [ -z "$uptime" ]; then
                    local start_time=$(ps -o lstart= -p "$first_pid" 2>/dev/null)
                    if [ -n "$start_time" ]; then
                        uptime="Started at: $start_time"
                    fi
                fi
            fi
            # If we still don't have uptime, use a generic message
            if [ -z "$uptime" ]; then
                uptime="Running (PID: $first_pid)"
            fi
            
            # Add process count to the uptime message
            if [ "$process_count" -gt 1 ]; then
                uptime="$uptime (Total processes: $process_count)"
            fi
        fi
        # Get current commit info
        commit_hash=$(git -C "$GAME_DIRECTORY" rev-parse --short HEAD 2>/dev/null || echo "N/A")
        commit_msg=$(git -C "$GAME_DIRECTORY" log -1 --pretty=format:"%s" 2>/dev/null || echo "N/A")
    fi
    
    # Build status message with proper Discord formatting
    echo "**Server Status:** $status"
    echo "**Uptime:** $uptime"
    echo "**Current Commit:** $commit_hash"
    echo "**Commit Message:** $commit_msg"
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
    local force_restart=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -f|--force)
                force_restart=true
                shift
                ;;
            *)
                echo "Unknown option: $1"
                usage
                ;;
        esac
    done
    
    # Get server status before restart
    local before_status=$(get_server_status)
    
    # Check if server is running
    if ! check_server; then
        if [ "$force_restart" = false ]; then
            log_message "Server is not running, use --force to start it"
            send_discord_notification "$(format_discord_message "❌ Server is not running, use --force to start it")"
            return 1
        fi
    fi
    
    # Send restart notification
    log_message "Restarting Evennia server..."
    send_discord_notification "$(format_discord_message "🔄 Restarting Evennia server...\n\n**Before Restart Status:**\n$before_status")"
    
    # Restart the server using evennia restart command
    if ! evennia restart; then
        log_message "Failed to restart server"
        send_discord_notification "$(format_discord_message "❌ Failed to restart server")"
        return 1
    fi
    
    # Wait for server to restart
    sleep 10
    
    # Get server status after restart
    local after_status=$(get_server_status)
    
    # Check if server is running
    if check_server; then
        log_message "Server restarted successfully"
        send_discord_notification "$(format_discord_message "✅ Server restarted successfully\n\n**After Restart Status:**\n$after_status")"
    else
        log_message "Server failed to start after restart"
        send_discord_notification "$(format_discord_message "❌ Server failed to start after restart\n\n**Last Known Status:**\n$after_status")"
        return 1
    fi
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

# Function to check conda environment
check_conda_env() {
    # Check if we're in the correct conda environment
    if [ -z "$CONDA_DEFAULT_ENV" ]; then
        log_message "Error: Not in a conda environment. Please activate the Evennia environment first."
        send_discord_notification "$(format_discord_message "❌ Error: Not in a conda environment. Please activate the Evennia environment first.")"
        exit 1
    fi
    
    # Check if evennia command is available
    if ! command -v evennia >/dev/null 2>&1; then
        log_message "Error: Evennia command not found. Please ensure you're in the correct conda environment."
        send_discord_notification "$(format_discord_message "❌ Error: Evennia command not found. Please ensure you're in the correct conda environment.")"
        exit 1
    fi
    
    log_message "Using conda environment: $CONDA_DEFAULT_ENV"
    return 0
}

# Main script
case "${1:-}" in
    restart)
        check_conda_env
        restart_server "${@:2}"
        ;;
    status)
        check_conda_env
        check_status
        ;;
    *)
        usage
        ;;
esac

exit 0 