#!/bin/bash

# Script to test Discord webhook functionality
# This script sends a test message to Discord using the provided webhook URL

# Function to display usage
usage() {
    echo "Usage: $0 -w, --webhook URL"
    echo "Options:"
    echo "  -w, --webhook URL    Discord webhook URL (required)"
    echo "  -h, --help           Display this help message"
    exit 1
}

# Default values
DISCORD_WEBHOOK_URL=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
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

# Check if webhook URL is provided
if [ -z "$DISCORD_WEBHOOK_URL" ]; then
    echo "Error: Discord webhook URL is required"
    usage
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if discord_notify.sh exists
if [ ! -f "$SCRIPT_DIR/discord_notify.sh" ]; then
    echo "Error: discord_notify.sh not found in $SCRIPT_DIR"
    exit 1
fi

# Make sure discord_notify.sh is executable
chmod +x "$SCRIPT_DIR/discord_notify.sh"

# Get system information
HOSTNAME=$(hostname)
OS_INFO=$(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)
UPTIME=$(uptime -p)
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}')
MEMORY_USAGE=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')

# Create a test message
TEST_MESSAGE="🔔 **Discord Webhook Test**\n\n"
TEST_MESSAGE+="✅ Webhook connection successful!\n\n"
TEST_MESSAGE+="**System Information:**\n"
TEST_MESSAGE+="• Hostname: $HOSTNAME\n"
TEST_MESSAGE+="• OS: $OS_INFO\n"
TEST_MESSAGE+="• Uptime: $UPTIME\n"
TEST_MESSAGE+="• Disk Usage: $DISK_USAGE\n"
TEST_MESSAGE+="• Memory Usage: $MEMORY_USAGE\n"
TEST_MESSAGE+="• CPU Usage: $CPU_USAGE\n\n"
TEST_MESSAGE+="This test message was sent at $(date '+%Y-%m-%d %H:%M:%S')"

# Send the test message
echo "Sending test message to Discord..."
if "$SCRIPT_DIR/discord_notify.sh" -w "$DISCORD_WEBHOOK_URL" -t "Webhook Test" -m "$TEST_MESSAGE" -c "0x3498db"; then
    echo "✅ Test message sent successfully!"
    exit 0
else
    echo "❌ Failed to send test message"
    exit 1
fi 