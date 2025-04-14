# Function to restore from backup
restore_from_backup() {
    local backup_file="$1"
    
    # Check if backup file exists
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file $backup_file does not exist"
        send_discord_notification "Backup Restore Failed" "Backup file $backup_file does not exist" "red"
        return 1
    fi
    
    # Create a backup of the current state before restoring
    log_message "Creating backup of current state before restore"
    if ! create_backup; then
        log_error "Failed to create backup before restore"
        send_discord_notification "Backup Restore Failed" "Failed to create backup before restore" "red"
        return 1
    fi
    
    # Extract the backup
    log_message "Extracting backup from $backup_file"
    if ! tar -xzf "$backup_file" -C "$GAME_DIRECTORY/.."; then
        log_error "Failed to extract backup"
        send_discord_notification "Backup Restore Failed" "Failed to extract backup" "red"
        return 1
    fi
    
    log_message "Backup restored successfully"
    send_discord_notification "Backup Restored" "Backup restored successfully from $backup_file" "green"
    return 0
} 