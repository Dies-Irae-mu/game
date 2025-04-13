# Evennia Auto-Update System

This system provides automated updates, backups, and restarts for an Evennia server. It includes scripts for creating backups, restoring from backups, and automatically updating and restarting the server when changes are detected.

## Scripts Overview

### `backup_game.sh`

Creates a backup of the game directory, excluding unnecessary files like database files, logs, cache files, media, static files, virtual environments, and the `.git` directory. The backup is stored in a `backups` directory in the parent directory of the game directory. The script also creates a `restore_backup.sh` script in the backups directory if it doesn't already exist.

### `restore_backup.sh`

Restores a backup to the game directory. It creates a backup of the current state before restoring, stops the Evennia server during the restore process, and restores the backup. If the restore fails, it attempts to restore the current state.

### `restart_prod.sh`

Restarts the Evennia server with error handling and rollback capabilities. It creates a backup before attempting to restart, and if the restart fails, it reverts the last git pull and tries again. If the second restart fails, it restores from the backup.

### `discord_notify.sh`

Sends notifications to Discord about server status, updates, backups, and restores. It uses a Discord webhook URL to send the notifications.

### `setup_auto_update.sh`

Sets up a cron job to automatically update and restart the Evennia server when changes are detected in the specified git branch.

### `setup_permissions.sh`

Sets appropriate permissions for all files in the Scripts directory, creates necessary log files, and sets up the backups directory.

### `test_discord_webhook.sh`

Tests the Discord webhook functionality by sending a test message with system information.

## Prerequisites

- Linux server with bash shell
- Git installed and configured
- Evennia server installed and configured
- Conda environment for Evennia
- Cron service running
- `curl` installed for Discord notifications
- `tar` and `gzip` installed for backups

## Setup Instructions

1. Make the scripts executable:
   ```bash
   chmod +x Scripts/*.sh
   ```

2. Set up permissions and create necessary directories:
   ```bash
   sudo ./Scripts/setup_permissions.sh
   ```
   This will:
   - Make all shell scripts executable
   - Set appropriate permissions for all files
   - Create log files in `/var/log/`
   - Create a backups directory
   - Optionally test the Discord webhook

3. Configure the scripts with your specific settings:
   - Edit `restart_prod.sh` to set the correct game directory and conda environment
   - Edit `backup_game.sh` to set the correct game directory
   - Edit `setup_auto_update.sh` to set the correct game directory, conda environment, and git branch

4. Set up the auto-update cron job:
   ```bash
   ./Scripts/setup_auto_update.sh -d /path/to/game -e your_conda_env -b your_git_branch -i 60 -w your_discord_webhook_url
   ```

## Usage

### Creating a Backup

```bash
./Scripts/backup_game.sh -d /path/to/game -n custom_backup_name -w your_discord_webhook_url
```

Options:
- `-d, --directory DIR`: Game directory path (default: /root/game)
- `-n, --name NAME`: Custom backup name (default: timestamp)
- `-w, --webhook URL`: Discord webhook URL for notifications
- `-h, --help`: Display help message

### Restoring a Backup

```bash
./backups/restore_backup.sh -b backup_name -d /path/to/game -w your_discord_webhook_url
```

Options:
- `-b, --backup NAME`: Backup name to restore (default: latest)
- `-d, --directory DIR`: Game directory path (default: /root/game)
- `-w, --webhook URL`: Discord webhook URL for notifications
- `-h, --help`: Display help message

### Setting Up Auto-Update

```bash
./Scripts/setup_auto_update.sh -d /path/to/game -e your_conda_env -b your_git_branch -i 60 -w your_discord_webhook_url
```

Options:
- `-b, --branch BRANCH`: Git branch to pull from (default: main)
- `-i, --interval MINUTES`: Update interval in minutes (default: 60)
- `-d, --directory DIR`: Game directory path (default: /root/game)
- `-e, --env ENV`: Conda environment name (default: game_py311)
- `-w, --webhook URL`: Discord webhook URL for notifications
- `-h, --help`: Display help message

### Testing Discord Webhook

```bash
./Scripts/test_discord_webhook.sh -w your_discord_webhook_url
```

Options:
- `-w, --webhook URL`: Discord webhook URL (required)
- `-h, --help`: Display help message

## Error Recovery Process

The auto-update system includes a robust error recovery process:

1. Before any changes, a backup is created using `backup_game.sh`
2. If the server restart fails, the system reverts the last git pull and tries to restart again
3. If the second restart fails, the system restores from the backup and tries to restart one more time
4. If all restart attempts fail, the system sends a notification to Discord and requires manual intervention

## Logging

All operations are logged to the following files:
- `/var/log/evennia_update.log`: Auto-update operations
- `/var/log/evennia_restart.log`: Server restart operations
- `/var/log/evennia_backup.log`: Backup operations
- `/var/log/evennia_restore.log`: Restore operations

## Linux Environment Setup

### Installing Required Packages

For Debian/Ubuntu:
```bash
sudo apt-get update
sudo apt-get install -y cron git tar gzip curl
```

For CentOS/RHEL:
```bash
sudo yum update
sudo yum install -y cronie git tar gzip curl
```

### Setting Up Conda

```bash
# Download Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh

# Install Miniconda
bash miniconda.sh -b -p $HOME/miniconda

# Initialize Conda for your shell
$HOME/miniconda/bin/conda init bash

# Reload your shell
source ~/.bashrc
```

### Setting Up Evennia

```bash
# Create a Conda environment
conda create -n game_py311 python=3.11

# Activate the environment
conda activate game_py311

# Install Evennia
pip install evennia

# Initialize a new game
evennia --init mygame
cd mygame
evennia migrate
```

### Configuring Git

```bash
# Set your Git user name and email
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Initialize a Git repository
git init
git add .
git commit -m "Initial commit"

# Add a remote repository
git remote add origin https://github.com/yourusername/yourrepo.git
git push -u origin main
```

## Linux-Specific Considerations

### File Permissions

Ensure that the scripts have the correct permissions:
```bash
chmod +x Scripts/*.sh
```

Make sure the user running the cron job has the necessary permissions to:
- Execute the scripts
- Access the game directory
- Write to the log files
- Create and access the backups directory

### Cron Service

Ensure that the cron service is running:
```bash
# For systemd-based systems
sudo systemctl status cron

# For older systems
sudo service crond status
```

If it's not running, start it:
```bash
# For systemd-based systems
sudo systemctl start cron

# For older systems
sudo service crond start
```

### Log Directories

Create the log directories if they don't exist:
```bash
sudo mkdir -p /var/log
sudo touch /var/log/evennia_update.log /var/log/evennia_restart.log /var/log/evennia_backup.log /var/log/evennia_restore.log
sudo chmod 644 /var/log/evennia_*.log
```

### Running Scripts as Different Users

If your Evennia server runs as a different user than the one running the cron job, you may need to use `sudo` or adjust the permissions accordingly. For example:

```bash
# Add the following line to /etc/sudoers (use visudo)
youruser ALL=(evennia_user) NOPASSWD: /path/to/game/Scripts/*.sh
```

Then modify the cron job to use sudo:
```
*/60 * * * * sudo -u evennia_user /path/to/game/Scripts/update_game.sh > /dev/null 2>&1
```

## Potential Issues and Troubleshooting

### Windows vs. Linux Compatibility

Since you're developing on Windows but running in Linux production, be aware of these potential issues:

1. **Line Endings**: Windows uses CRLF line endings, while Linux uses LF. This can cause issues with shell scripts.
   - Solution: Use Git's `core.autocrlf` setting or convert files using `dos2unix`:
     ```bash
     sudo apt-get install dos2unix
     dos2unix Scripts/*.sh
     ```

2. **Path Separators**: Windows uses backslashes (`\`), while Linux uses forward slashes (`/`).
   - Solution: Always use forward slashes in paths, even on Windows.

3. **File Permissions**: Windows doesn't use the same permission system as Linux.
   - Solution: Ensure files have the correct permissions on Linux:
     ```bash
     chmod +x Scripts/*.sh
     ```

4. **Command Availability**: Some commands available on Windows might not be available on Linux and vice versa.
   - Solution: Test all commands in a Linux environment before deploying.

### Common Issues

1. **Cron Jobs Not Running**:
   - Check if the cron service is running
   - Check the system logs for cron errors
   - Ensure the cron job is correctly formatted
   - Try running the script manually to see if it works

2. **Permission Denied Errors**:
   - Check file permissions
   - Check directory permissions
   - Check user permissions
   - Try running the script with sudo if necessary

3. **Conda Environment Not Found**:
   - Ensure the conda environment exists
   - Ensure the conda environment is activated in the script
   - Check the path to the conda executable

4. **Git Pull Failures**:
   - Check if the repository is up to date
   - Check if there are any conflicts
   - Check if the branch exists
   - Check if the user has permission to pull

5. **Evennia Restart Failures**:
   - Check if the Evennia server is running
   - Check the Evennia logs for errors
   - Check if the conda environment is activated
   - Check if the game directory is correct

### Debugging Tips

1. **Enable Debug Mode**:
   - Add `set -x` at the beginning of the script to print each command as it's executed
   - Add `set -e` to exit on any error

2. **Check Logs**:
   - Check the system logs: `tail -f /var/log/syslog`
   - Check the cron logs: `tail -f /var/log/cron`
   - Check the Evennia logs: `tail -f /path/to/game/server/logs/server.log`

3. **Test Commands Manually**:
   - Run each command manually to see if it works
   - Check the exit status of each command

4. **Check Environment Variables**:
   - Print environment variables: `env`
   - Check PATH: `echo $PATH`
   - Check HOME: `echo $HOME`

## Security Considerations

1. **Secure Paths**:
   - Use absolute paths in scripts
   - Avoid using relative paths
   - Avoid using `~` in paths

2. **Secure Backups**:
   - Store backups in a secure location
   - Set appropriate permissions on backup files
   - Consider encrypting backups

3. **Secure File Permissions**:
   - Set appropriate permissions on scripts
   - Set appropriate permissions on log files
   - Set appropriate permissions on backup files

## Contributing

Feel free to contribute improvements to these scripts. Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 