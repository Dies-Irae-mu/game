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

# Source conda.sh to enable conda commands
if [ -f "$CONDA_SH" ]; then
    source "$CONDA_SH"
else
    echo "Error: conda.sh not found at $CONDA_SH"
    exit 1
fi

# Activate the conda environment
if ! conda activate "$CONDA_ENV"; then
    echo "Error: Failed to activate conda environment: $CONDA_ENV"
    exit 1
fi

# Validate required configuration
required_vars=("GAME_DIRECTORY" "RESTART_LOG" "DISCORD_WEBHOOK_URL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "Error: Required configuration variable '$var' is not set"
        exit 1
    fi
done

# Validate paths and permissions
if [ ! -d "$GAME_DIRECTORY" ]; then
    echo "Error: Game directory does not exist: $GAME_DIRECTORY"
    exit 1
fi

if [ ! -w "$(dirname "$RESTART_LOG")" ]; then
    echo "Error: Cannot write to log directory: $(dirname "$RESTART_LOG")"
    exit 1
fi

# Validate Discord webhook URL format
if [[ ! "$DISCORD_WEBHOOK_URL" =~ ^https://discord\.com/api/webhooks/ ]]; then
    echo "Error: Invalid Discord webhook URL format"
    exit 1
fi

# Constants
MAX_RESTART_WAIT=300  # 5 minutes maximum wait for restart
PROCESS_CHECK_INTERVAL=5  # Check every 5 seconds
SERVER_PID_FILE="$GAME_DIRECTORY/server/server.pid"
PORTAL_PID_FILE="$GAME_DIRECTORY/server/portal.pid"
MAX_LOG_SIZE=10485760  # 10MB
LOG_ROTATE_COUNT=5

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

# Function to rotate logs
rotate_logs() {
    local log_file="$1"
    if [ -f "$log_file" ] && [ "$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file")" -gt "$MAX_LOG_SIZE" ]; then
        for i in $(seq $((LOG_ROTATE_COUNT-1)) -1 1); do
            if [ -f "${log_file}.$i" ]; then
                mv "${log_file}.$i" "${log_file}.$((i+1))"
            fi
        done
        mv "$log_file" "${log_file}.1"
        touch "$log_file"
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
        
        # Get server process info
        if [ -f "$SERVER_PID_FILE" ]; then
            local server_pid=$(cat "$SERVER_PID_FILE")
            server_uptime=$(get_process_uptime "$server_pid")
        fi
        
        # Get portal process info
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

# Function to log messages with timestamp
log_message() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "$timestamp - $message" | tee -a "$RESTART_LOG"
    
    # Basic log rotation if log file gets too large
    if [ -f "$RESTART_LOG" ] && [ "$(stat -f%z "$RESTART_LOG" 2>/dev/null || stat -c%s "$RESTART_LOG")" -gt "$MAX_LOG_SIZE" ]; then
        mv "$RESTART_LOG" "$RESTART_LOG.old"
        touch "$RESTART_LOG"
    fi
}

# Function to send Discord notifications with error handling
send_discord_notification() {
    local message="$1"
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        # Format the message for Discord (escape special characters)
        local formatted_message=$(echo "$message" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')
        
        # Send to Discord with proper JSON formatting and error handling
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
    send_discord_notification "🔄 Restarting Evennia server...

**Before Restart Status:**
$(get_server_status)"
    
    if ! evennia restart; then
        log_message "Failed to restart server"
        send_discord_notification "❌ Failed to restart server"
        return 1
    fi
    
    # Wait for server to restart with timeout
    if wait_for_server_state "running" "$MAX_RESTART_WAIT"; then
        local after_status=$(get_server_status)
        log_message "Server restarted successfully"
        send_discord_notification "✅ Server restarted successfully

**After Restart Status:**
$after_status"
    else
        local after_status=$(get_server_status)
        log_message "Server failed to start after restart (timeout after ${MAX_RESTART_WAIT}s)"
        send_discord_notification "❌ Server failed to start after restart (timeout)

**Last Known Status:**
$after_status"
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