#!/bin/bash

# Log file
LOG_FILE="/var/log/evennia_update.log"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Find any resume scripts that might be scheduled
RESUME_SCRIPTS=$(crontab -l 2>/dev/null | grep "resume_auto_update_.*\.sh" | awk '{print $6}')

if [ -n "$RESUME_SCRIPTS" ]; then
    # Execute each resume script
    for script in $RESUME_SCRIPTS; do
        if [ -f "$script" ]; then
            log_message "Manually executing resume script: $script"
            bash "$script"
        fi
    done
    
    # Remove any scheduled resume jobs
    (crontab -l | grep -v "resume_auto_update_.*\.sh") | crontab -
    
    echo "Auto-update cron job has been manually resumed."
else
    # Check if the auto-update job is already running
    CRON_JOBS=$(crontab -l 2>/dev/null | grep "evennia_auto_update_")
    if [ -n "$CRON_JOBS" ]; then
        echo "Auto-update cron job is already running."
    else
        # Try to find the backup file
        BACKUP_FILES=$(ls -t /tmp/crontab_backup_* 2>/dev/null)
        if [ -n "$BACKUP_FILES" ]; then
            # Use the most recent backup
            BACKUP_FILE=$(echo "$BACKUP_FILES" | head -1)
            log_message "Restoring auto-update cron job from backup: $BACKUP_FILE"
            crontab "$BACKUP_FILE"
            echo "Auto-update cron job has been restored from backup."
        else
            echo "No auto-update cron job found and no backup available."
            echo "You may need to run setup_auto_update.sh again to set up the cron job."
        fi
    fi
fi 