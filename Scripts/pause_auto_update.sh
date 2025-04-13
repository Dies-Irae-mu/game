#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -d, --duration MINUTES    Duration to pause in minutes (default: 60)"
    echo "  -h, --help                Display this help message"
    exit 1
}

# Default values
DURATION=60  # Default pause duration in minutes

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--duration)
            DURATION="$2"
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

# Validate duration is a number
if ! [[ "$DURATION" =~ ^[0-9]+$ ]]; then
    echo "Error: Duration must be a positive integer"
    exit 1
fi

# Log file
LOG_FILE="/var/log/evennia_update.log"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Find the auto-update cron job
CRON_JOBS=$(crontab -l 2>/dev/null | grep "evennia_auto_update_")
if [ -z "$CRON_JOBS" ]; then
    log_message "No auto-update cron job found. Nothing to pause."
    exit 0
fi

# Extract the cron ID and script path
CRON_ID=$(echo "$CRON_JOBS" | grep -o "evennia_auto_update_[0-9]*")
UPDATE_SCRIPT=$(echo "$CRON_JOBS" | awk '{print $2}')

if [ -z "$CRON_ID" ] || [ -z "$UPDATE_SCRIPT" ]; then
    log_message "Error: Could not parse cron job information"
    exit 1
fi

# Create a backup of the current crontab
BACKUP_FILE="/tmp/crontab_backup_$$"
crontab -l > "$BACKUP_FILE" 2>/dev/null

# Remove the auto-update cron job
(crontab -l | grep -v "$CRON_ID") | crontab -

# Create a resume script
RESUME_SCRIPT="/tmp/resume_auto_update_$$.sh"
cat > "$RESUME_SCRIPT" << EOF
#!/bin/bash

# Resume the auto-update cron job
(crontab -l 2>/dev/null; echo "$CRON_JOBS") | crontab -

# Log the resume
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Auto-update cron job resumed" | tee -a "$LOG_FILE"

# Remove this script
rm -f "\$0"
EOF

# Make the resume script executable
chmod +x "$RESUME_SCRIPT"

# Schedule the resume script to run after the specified duration
RESUME_TIME=$(date -d "+$DURATION minutes" +"%Y-%m-%d %H:%M:%S")
log_message "Auto-update cron job paused for $DURATION minutes. Will resume at $RESUME_TIME"

# Add a one-time cron job to resume after the specified duration
(crontab -l 2>/dev/null; echo "$(date -d "+$DURATION minutes" +"%M %H %d %m *") $RESUME_SCRIPT") | crontab -

echo "Auto-update cron job has been paused for $DURATION minutes."
echo "It will automatically resume at $RESUME_TIME."
echo "You can manually resume it earlier by running: $RESUME_SCRIPT" 