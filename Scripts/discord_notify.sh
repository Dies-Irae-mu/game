#!/bin/bash

# Script to send notifications to Discord
# This script sends notifications to Discord using a webhook URL

# Function to display usage
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -w, --webhook URL        Discord webhook URL (required)"
    echo "  -t, --title TITLE        Notification title (optional)"
    echo "  -m, --message MESSAGE    Notification message (required)"
    echo "  -c, --color COLOR        Embed color (optional, default: green for success, red for errors)"
    echo "  -h, --help               Display this help message"
    exit 1
}

# Default values
WEBHOOK_URL=""
TITLE=""
MESSAGE=""
COLOR="0x2ecc71"  # Default green

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -w|--webhook)
            WEBHOOK_URL="$2"
            shift 2
            ;;
        -t|--title)
            TITLE="$2"
            shift 2
            ;;
        -m|--message)
            MESSAGE="$2"
            shift 2
            ;;
        -c|--color)
            COLOR="$2"
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
if [ -z "$WEBHOOK_URL" ]; then
    echo "Error: Discord webhook URL is required"
    usage
fi

# Check if message is provided
if [ -z "$MESSAGE" ]; then
    echo "Error: Notification message is required"
    usage
fi

# Escape special characters in the message
MESSAGE=$(echo "$MESSAGE" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')

# Construct the JSON payload
if [ -z "$TITLE" ]; then
    JSON="{\"embeds\":[{\"description\":\"$MESSAGE\",\"color\":$COLOR}]}"
else
    JSON="{\"embeds\":[{\"title\":\"$TITLE\",\"description\":\"$MESSAGE\",\"color\":$COLOR}]}"
fi

# Send the notification to Discord
if ! curl -s -H "Content-Type: application/json" -X POST -d "$JSON" "$WEBHOOK_URL"; then
    echo "Error: Failed to send Discord notification"
    exit 1
fi

echo "Discord notification sent successfully"
exit 0 