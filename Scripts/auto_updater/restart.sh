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
IFS=$'\n\t'

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the configuration file
CONFIG_FILE="$SCRIPT_DIR/config.sh"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found: $CONFIG_FILE"
    exit 1
fi
source "$CONFIG_FILE"

# Validate required configuration
required_vars=("GAME_DIRECTORY" "RESTART_LOG" "DISCORD_WEBHOOK_URL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "Error: Required configuration variable '$var' is not set"
        exit 1
    fi
done

# Constants
MAX_RESTART_WAIT=300  # 5 minutes maximum wait for restart
PROCESS_CHECK_INTERVAL=5  # Check every 5 seconds
SERVER_PID_FILE="$GAME_DIRECTORY/server/server.pid"
PORTAL_PID_FILE="$GAME_DIRECTORY/server/portal.pid"

# Function to display usage information
usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  restart - Restart the Evennia server"
    echo "  status  - Check server status"
    echo ""
    echo "Options:"
    echo "  -f, --force    - Force restart without confirmation"
    echo "  -h, --help     - Display this help message"
    echo ""
    echo "Examples:"
    echo "  $0 restart           # Restart the server"
    echo "  $0 restart --force   # Force restart without confirmation"
    echo "  $0 status            # Check server status"
    exit 1
}

# Function to log messages with timestamp
log_message() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "$timestamp - $message" | tee -a "$RESTART_LOG"
    
    # Implement basic log rotation if log file gets too large (10MB)
    if [ -f "$RESTART_LOG" ] && [ "$(stat -f%z "$RESTART_LOG" 2>/dev/null || stat -c%s "$RESTART_LOG")" -gt 10485760 ]; then
        mv "$RESTART_LOG" "$RESTART_LOG.old"
        touch "$RESTART_LOG"
    fi
}

# Function to sanitize text for Discord
sanitize_discord_message() {
    local message="$1"
    # Remove or escape potentially dangerous characters
    echo "$message" | sed 's/`/\\`/g' | sed 's/@/\\@/g' | sed 's/\*/\\*/g' | sed 's/_/\\_/g'
}

# Function to send Discord notifications with error handling
send_discord_notification() {
    local message="$1"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        local sanitized_message=$(sanitize_discord_message "$message")
        local formatted_message=$(echo "$sanitized_message" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')
        
        if ! curl -s -H "Content-Type: application/json" \
             -X POST \
             --max-time 10 \
             --retry 3 \
             --retry-delay 2 \
             -d "{\"content\":\"$formatted_message\"}" \
             "$DISCORD_WEBHOOK_URL"; then
            log_message "Warning: Failed to send Discord notification"
        fi
    fi
}

# Function to check if a process is running by PID file
check_process_by_pid_file() {
    local pid_file="$1"
    local process_name="$2"
    
    if [ ! -f "$pid_file" ]; then
        return 1
    fi
    
    local pid=$(cat "$pid_file" 2>/dev/null)
    if [ -z "$pid" ]; then
        return 1
    fi
    
    if ! ps -p "$pid" > /dev/null 2>&1; then
        # Process not running, clean up stale PID file
        rm -f "$pid_file"
        return 1
    fi
    
    return 0
}

# Function to check if the server is running
check_server() {
    local server_running=false
    local portal_running=false
    
    if check_process_by_pid_file "$SERVER_PID_FILE" "server"; then
        server_running=true
    fi
    
    if check_process_by_pid_file "$PORTAL_PID_FILE" "portal"; then
        portal_running=true
    fi
    
    # Server is considered running if both server and portal are running
    if [ "$server_running" = true ] && [ "$portal_running" = true ]; then
        return 0
    else
        return 1
    fi
}

# Function to get process uptime from PID
get_process_uptime() {
    local pid="$1"
    if command -v ps >/dev/null 2>&1; then
        ps -o etime= -p "$pid" 2>/dev/null || echo "Unknown"
    else
        echo "Unknown"
    fi
}

# Function to get server status details
get_server_status() {
    local status="Not Running"
    local server_uptime="N/A"
    local portal_uptime="N/A"
    local commit_hash="N/A"
    local commit_msg="N/A"
    
    if check_server; then
        status="Running"
        
        # Get server process uptime
        if [ -f "$SERVER_PID_FILE" ]; then
            local server_pid=$(cat "$SERVER_PID_FILE")
            server_uptime=$(get_process_uptime "$server_pid")
        fi
        
        # Get portal process uptime
        if [ -f "$PORTAL_PID_FILE" ]; then
            local portal_pid=$(cat "$PORTAL_PID_FILE")
            portal_uptime=$(get_process_uptime "$portal_pid")
        fi
        
        # Get git information
        if [ -d "$GAME_DIRECTORY" ]; then
            commit_hash=$(git -C "$GAME_DIRECTORY" rev-parse --short HEAD 2>/dev/null || echo "N/A")
            commit_msg=$(git -C "$GAME_DIRECTORY" log -1 --pretty=format:"%s" 2>/dev/null || echo "N/A")
        fi
    fi
    
    echo "**Server Status:** $status"
    echo "**Server Process Uptime:** $server_uptime"
    echo "**Portal Process Uptime:** $portal_uptime"
    echo "**Current Commit:** $commit_hash"
    echo "**Commit Message:** $commit_msg"
}

# Function to wait for server to start/stop
wait_for_server_state() {
    local desired_state="$1"  # "running" or "stopped"
    local timeout="$2"
    local start_time=$(date +%s)
    
    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if [ "$elapsed" -ge "$timeout" ]; then
            return 1
        fi
        
        if [ "$desired_state" = "running" ]; then
            if check_server; then
                return 0
            fi
        else
            if ! check_server; then
                return 0
            fi
        fi
        
        sleep "$PROCESS_CHECK_INTERVAL"
    done
}

# Function to restart the server
restart_server() {
    local force_restart=false
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -f|--force)
                force_restart=true
                shift
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
    
    if ! check_server; then
        if [ "$force_restart" = false ]; then
            log_message "Server is not running, use --force to start it"
            send_discord_notification "❌ Server is not running, use --force to start it"
            return 1
        fi
    fi
    
    log_message "Restarting Evennia server..."
    send_discord_notification "🔄 Restarting Evennia server...\n\n**Before Restart Status:**\n$(get_server_status)"
    
    if ! evennia restart; then
        log_message "Failed to restart server"
        send_discord_notification "❌ Failed to restart server"
        return 1
    fi
    
    # Wait for server to restart with timeout
    if wait_for_server_state "running" "$MAX_RESTART_WAIT"; then
        local after_status=$(get_server_status)
        log_message "Server restarted successfully"
        send_discord_notification "✅ Server restarted successfully\n\n**After Restart Status:**\n$after_status"
    else
        local after_status=$(get_server_status)
        log_message "Server failed to start after restart (timeout after ${MAX_RESTART_WAIT}s)"
        send_discord_notification "❌ Server failed to start after restart (timeout)\n\n**Last Known Status:**\n$after_status"
        return 1
    fi
}

# Function to check server status
check_status() {
    local status=$(get_server_status)
    echo "$status"
    if check_server; then
        return 0
    else
        return 1
    fi
}

# Main script
case "${1:-}" in
    restart)
        restart_server "${@:2}"
        ;;
    status)
        check_status
        ;;
    -h|--help)
        usage
        ;;
    *)
        usage
        ;;
esac

exit 0 