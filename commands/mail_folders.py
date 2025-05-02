"""
Mail folder management system for Dies Irae.

This module implements folder management for the mail system.
"""

from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils import create, evtable
from evennia.utils.logger import log_info, log_err
import re

class CmdMailFolder(MuxCommand):
    """
    Manage your mail folders.

    Usage:
      folder                   - Lists your mail folders and message counts
      folder/create <name>     - Creates a new folder
      folder/delete <name>     - Deletes a folder (moves messages to Incoming)
      folder/rename <old>=<new> - Renames a folder
      folder/move <msg#>=<name> - Moves a message to a folder
      folder/empty <name>=yes  - Empties all messages from a folder
      
    Folder names can be up to 20 characters long, start with a letter, and
    contain only letters, numbers, spaces, and underscores. Names are stored
    with the first letter capitalized. The "Incoming" and "Sent" folders are
    reserved and cannot be modified.
    """

    key = "folder"
    aliases = ["folders"]
    lock = "cmd:all()"
    help_category = "Communication"

    def func(self):
        """Implements the folder command"""
        caller = self.caller

        # Initialize folders if they don't exist
        if not hasattr(caller, 'db') or not caller.db.mail_folders:
            caller.db.mail_folders = ["Incoming", "Sent"]
            log_info(f"Initialized mail folders for {caller}")

        # No args, just list folders
        if not self.args and not self.switches:
            self.list_folders()
            return

        # Handle the various switches
        if "create" in self.switches:
            self.create_folder()
        elif "delete" in self.switches:
            self.delete_folder()
        elif "rename" in self.switches:
            self.rename_folder()
        elif "move" in self.switches:
            self.move_to_folder()
        elif "empty" in self.switches:
            self.empty_folder()
        else:
            # Invalid switch
            caller.msg(f"Unknown switch. Use {self.key} without a switch to see valid options.")

    def list_folders(self):
        """List all folders and the number of messages in each"""
        caller = self.caller
        folders = caller.db.mail_folders

        if not folders:
            caller.msg("You have no mail folders.")
            return

        try:
            # Get all mail messages for this character
            all_mail = self.get_all_mail()
            
            # For sent messages, we need to check if the caller is the sender
            from evennia.comms.models import Msg
            
            # Get account/character info for sender check
            if hasattr(caller, 'account') and caller.account:
                account = caller.account
                sent_msgs = Msg.objects.filter(db_sender_accounts=account)
            else:
                sent_msgs = Msg.objects.filter(db_sender_objects=caller)
                
            log_info(f"Found {sent_msgs.count()} messages sent by {caller}")
            
            # Count messages in each folder
            folder_counts = {folder: 0 for folder in folders}
            
            # Special handling for Incoming and Sent folders
            for msg in all_mail:
                # Debug output to see tag information 
                tag_info = []
                for tag in msg.tags.all():
                    if isinstance(tag, str):
                        tag_info.append(f"str:{tag}")
                    elif hasattr(tag, 'db_key') and hasattr(tag, 'db_category'):
                        tag_info.append(f"obj:{tag.db_key}(cat:{tag.db_category})")
                log_info(f"Message ID {msg.id} tags: {tag_info}")
                
                # Check for sent messages
                is_sent = False
                for tag in msg.tags.all():
                    if isinstance(tag, str) and tag == "sent":
                        is_sent = True
                        break
                    elif hasattr(tag, 'db_key') and tag.db_key == "sent":
                        is_sent = True
                        break
                    elif hasattr(tag, 'db_category') and hasattr(tag, 'db_key') and tag.db_category == "mail" and tag.db_key == "sent":
                        is_sent = True
                        break
                
                if is_sent:
                    folder_counts["Sent"] += 1
                    log_info(f"Counting message {msg.id} in Sent folder")
                    continue
                
                # Check for folder tags - store in a variable first
                found_folder = False
                folder_name = None
                
                for tag in msg.tags.all():
                    if isinstance(tag, str) and tag.lower().startswith("folder_"):
                        folder_name = tag[7:]  # Remove 'folder_' prefix
                        found_folder = True
                        break
                    elif hasattr(tag, 'db_key') and tag.db_key.lower().startswith("folder_"):
                        folder_name = tag.db_key[7:]  # Remove 'folder_' prefix
                        found_folder = True
                        break
                
                # Now increment the count for the right folder (case-insensitive matching)
                if found_folder and folder_name:
                    # Find a case-insensitive match in the folder list
                    matched_folder = None
                    for folder in folder_counts:
                        if folder.lower() == folder_name.lower():
                            matched_folder = folder
                            break
                            
                    if matched_folder:
                        folder_counts[matched_folder] += 1
                        log_info(f"Counting message {msg.id} in folder '{matched_folder}' (matched '{folder_name}')")
                    else:
                        # No matching folder, count in Incoming
                        folder_counts["Incoming"] += 1
                        log_info(f"Counting message {msg.id} in Incoming folder (no matching folder for '{folder_name}')")
                # If no folder found and not sent, it's in Incoming
                elif not found_folder and not is_sent:
                    folder_counts["Incoming"] += 1
                    log_info(f"Counting message {msg.id} in Incoming folder")
            
            # Create a nicely formatted table
            table = evtable.EvTable(
                "|wFolder|n",
                "|wMessages|n",
                table=None,
                border="header",
                header_line_char="-",
                width=50,
            )
            
            for folder in sorted(folders):
                table.add_row(folder, folder_counts.get(folder, 0))
            
            table.reformat_column(0, width=30)
            table.reformat_column(1, width=20)
            
            caller.msg("-" * 50)
            caller.msg("|wYour Mail Folders:|n")
            caller.msg(str(table))
            caller.msg("-" * 50)
            
        except Exception as e:
            log_err(f"Error listing folders: {e}")
            caller.msg(f"An error occurred listing your folders: {e}")

    def create_folder(self):
        """Create a new folder"""
        caller = self.caller
        folder_name = self.args.strip()
        
        # Validate name
        if not folder_name:
            caller.msg("You must specify a folder name.")
            return
            
        # Check length
        if len(folder_name) > 20:
            caller.msg("Folder name is too long (max 20 characters).")
            return
            
        # Check if already exists (case insensitive)
        existing_folders = [f.lower() for f in caller.db.mail_folders]
        if folder_name.lower() in existing_folders:
            caller.msg(f"A folder named '{folder_name}' already exists.")
            return
            
        # Check reserved names
        if folder_name.lower() in ["incoming", "sent"]:
            caller.msg(f"'{folder_name}' is a reserved folder name.")
            return
            
        # Validate allowed characters (letters, numbers, spaces, underscores)
        pattern = r'^[A-Za-z][A-Za-z0-9 _]*$'
        if not re.match(pattern, folder_name):
            caller.msg("Folder names must start with a letter and contain only letters, numbers, spaces, and underscores.")
            return
            
        # Capitalize first letter for consistency
        folder_name = folder_name[0].upper() + folder_name[1:]
        
        # Create the folder
        try:
            caller.db.mail_folders.append(folder_name)
            log_info(f"{caller} created mail folder '{folder_name}'")
            caller.msg(f"Folder '{folder_name}' created.")
        except Exception as e:
            log_err(f"Error creating folder: {e}")
            caller.msg(f"An error occurred creating the folder: {e}")

    def delete_folder(self):
        """Delete a folder and move its contents to Incoming"""
        caller = self.caller
        folder_name = self.args.strip()
        
        # Validate name
        if not folder_name:
            caller.msg("You must specify a folder name.")
            return
            
        # Check reserved names
        if folder_name.lower() in ["incoming", "sent"]:
            caller.msg(f"You cannot delete the '{folder_name}' folder.")
            return
            
        # Check if folder exists
        folders = caller.db.mail_folders
        if folder_name not in folders:
            caller.msg(f"Folder '{folder_name}' doesn't exist.")
            return
            
        # Find and move all messages from this folder to Incoming
        try:
            all_mail = self.get_all_mail()
            moved_count = 0
            
            for msg in all_mail:
                all_tags = msg.tags.all()
                for tag in all_tags:
                    if isinstance(tag, str) and tag == f"folder_{folder_name}":
                        # Remove folder tag
                        msg.tags.remove(tag, category="mail")
                        moved_count += 1
                        break
                    elif hasattr(tag, 'db_key') and hasattr(tag, 'db_category'):
                        if tag.db_category == "mail" and tag.db_key == f"folder_{folder_name}":
                            # Remove folder tag
                            msg.tags.remove(tag.db_key, category="mail")
                            moved_count += 1
                            break
            
            # Remove the folder from the list
            folders.remove(folder_name)
            caller.db.mail_folders = folders
            
            log_info(f"{caller} deleted mail folder '{folder_name}', moved {moved_count} messages to Incoming")
            caller.msg(f"Folder '{folder_name}' deleted. {moved_count} messages moved to Incoming.")
        except Exception as e:
            log_err(f"Error deleting folder: {e}")
            caller.msg(f"An error occurred deleting the folder: {e}")

    def rename_folder(self):
        """Rename a folder"""
        caller = self.caller
        
        if not self.args or "=" not in self.args:
            caller.msg("Usage: folder/rename <old_name>=<new_name>")
            return
            
        old_name, new_name = self.args.split("=", 1)
        old_name = old_name.strip()
        new_name = new_name.strip()
        
        # Validate names
        if not old_name or not new_name:
            caller.msg("Both old and new folder names must be specified.")
            return
            
        # Check if old folder exists
        folders = caller.db.mail_folders
        if old_name not in folders:
            caller.msg(f"Folder '{old_name}' doesn't exist.")
            return
            
        # Check reserved names
        if old_name.lower() in ["incoming", "sent"]:
            caller.msg(f"You cannot rename the '{old_name}' folder.")
            return
            
        if new_name.lower() in ["incoming", "sent"]:
            caller.msg(f"'{new_name}' is a reserved folder name.")
            return
            
        # Check if new name already exists
        existing_folders = [f.lower() for f in folders]
        if new_name.lower() in existing_folders:
            caller.msg(f"A folder named '{new_name}' already exists.")
            return
            
        # Check length
        if len(new_name) > 20:
            caller.msg("New folder name is too long (max 20 characters).")
            return
            
        # Validate allowed characters
        pattern = r'^[A-Za-z][A-Za-z0-9 _]*$'
        if not re.match(pattern, new_name):
            caller.msg("Folder names must start with a letter and contain only letters, numbers, spaces, and underscores.")
            return
            
        # Capitalize first letter for consistency
        new_name = new_name[0].upper() + new_name[1:]
        
        try:
            # Update the folder list
            index = folders.index(old_name)
            folders[index] = new_name
            caller.db.mail_folders = folders
            
            # Update all message tags
            all_mail = self.get_all_mail()
            updated_count = 0
            
            for msg in all_mail:
                all_tags = msg.tags.all()
                for tag in all_tags:
                    if (isinstance(tag, str) and tag == f"folder_{old_name}") or \
                       (hasattr(tag, 'db_key') and hasattr(tag, 'db_category') and 
                        tag.db_category == "mail" and tag.db_key == f"folder_{old_name}"):
                        # Update the folder tag
                        msg.tags.remove(f"folder_{old_name}", category="mail")
                        msg.tags.add(f"folder_{new_name}", category="mail")
                        updated_count += 1
                        break
            
            log_info(f"{caller} renamed mail folder '{old_name}' to '{new_name}', updated {updated_count} messages")
            caller.msg(f"Folder '{old_name}' renamed to '{new_name}'. {updated_count} messages updated.")
        except Exception as e:
            log_err(f"Error renaming folder: {e}")
            caller.msg(f"An error occurred renaming the folder: {e}")

    def move_to_folder(self):
        """Move a message to a folder"""
        caller = self.caller
        
        if not self.args or "=" not in self.args:
            caller.msg("Usage: folder/move <message_number>=<folder_name>")
            return
            
        message_num, folder_name = self.args.split("=", 1)
        message_num = message_num.strip()
        folder_name = folder_name.strip()
        
        try:
            message_num = int(message_num)
        except ValueError:
            caller.msg("Message number must be a number.")
            return
            
        # Check if folder exists (case-insensitive)
        folders = caller.db.mail_folders
        folder_exists = False
        real_folder_name = folder_name  # Use this to preserve case
        
        for f in folders:
            if f.lower() == folder_name.lower():
                folder_exists = True
                real_folder_name = f  # Use the actual case from the folder list
                break
                
        if not folder_exists:
            caller.msg(f"Folder '{folder_name}' doesn't exist.")
            return
            
        # Get the message
        try:
            # Get all messages in inbox (excluding sent messages)
            all_mail = self.get_all_mail()
            
            # If moving from inbox, skip sent messages
            inbox_messages = []
            for msg in all_mail:
                is_sent = False
                for tag in msg.tags.all():
                    if isinstance(tag, str) and tag == "sent":
                        is_sent = True
                        break
                    elif hasattr(tag, 'db_key') and tag.db_key == "sent":
                        is_sent = True
                        break
                    elif hasattr(tag, 'db_category') and hasattr(tag, 'db_key') and tag.db_category == "mail" and tag.db_key == "sent":
                        is_sent = True
                        break
                        
                # Skip sent messages
                if not is_sent:
                    inbox_messages.append(msg)
                    
            if not inbox_messages:
                caller.msg("You have no messages in your inbox.")
                return
                
            if message_num < 1 or message_num > len(inbox_messages):
                caller.msg(f"Message {message_num} not found.")
                return
                
            message = inbox_messages[message_num - 1]
            
            # Log all current tags for debugging
            tag_info = []
            for tag in message.tags.all():
                if isinstance(tag, str):
                    tag_info.append(f"str:{tag}")
                elif hasattr(tag, 'db_key') and hasattr(tag, 'db_category'):
                    tag_info.append(f"obj:{tag.db_key}(cat:{tag.db_category})")
            log_info(f"Before move: Message tags: {tag_info}")
            
            # Remove any existing folder tags
            all_tags = list(message.tags.all())  # Create a copy of tags to safely iterate
            for tag in all_tags:
                if isinstance(tag, str) and tag.startswith("folder_"):
                    log_info(f"Removing string folder tag: {tag}")
                    message.tags.remove(tag, category="mail")
                elif hasattr(tag, 'db_key') and hasattr(tag, 'db_category') and tag.db_key.startswith("folder_"):
                    log_info(f"Removing object folder tag: {tag.db_key} (category: {tag.db_category})")
                    message.tags.remove(tag.db_key, category="mail")
            
            # If not moving to Incoming, add the folder tag
            if real_folder_name.lower() != "incoming":
                folder_tag = f"folder_{real_folder_name}"
                log_info(f"Adding folder tag: {folder_tag} with category: mail")
                message.tags.add(folder_tag, category="mail")
                
                # Manually verify the tag was added
                added_successfully = False
                for tag in message.tags.all():
                    if isinstance(tag, str) and tag == folder_tag:
                        added_successfully = True
                        break
                    elif hasattr(tag, 'db_key') and tag.db_key == folder_tag:
                        added_successfully = True
                        break
                        
                if not added_successfully:
                    log_info("Tag was not added successfully, trying alternative method")
                    # Use the proper API to add tags - the message object has a tags handler
                    try:
                        # Try using the add method directly again with a different approach
                        message.tags.add(folder_tag, category="mail")
                        log_info(f"Retried adding tag: {folder_tag} to message {message.id}")
                    except Exception as e:
                        log_err(f"Error adding tag (retried approach): {e}")
                
            # Log tags after the move
            tag_info = []
            for tag in message.tags.all():
                if isinstance(tag, str):
                    tag_info.append(f"str:{tag}")
                elif hasattr(tag, 'db_key') and hasattr(tag, 'db_category'):
                    tag_info.append(f"obj:{tag.db_key}(cat:{tag.db_category})")
            log_info(f"After move: Message tags: {tag_info}")
                
            # Get a summary of the message for the confirmation
            sender_name = "Unknown"
            if hasattr(message, 'senders') and message.senders:
                sender_name = message.senders[0].get_display_name(caller)
                
            log_info(f"{caller} moved message {message_num} from {sender_name} to folder '{real_folder_name}'")
            caller.msg(f"Message {message_num} from {sender_name} moved to '{real_folder_name}' folder.")
            
        except Exception as e:
            log_err(f"Error moving message to folder: {e}")
            caller.msg(f"An error occurred moving the message: {e}")

    def empty_folder(self):
        """Empty all messages from a folder"""
        caller = self.caller
        
        if not self.args or "=" not in self.args:
            caller.msg("Usage: folder/empty <folder_name>=yes (You must confirm with =yes)")
            return
            
        folder_name, confirm = self.args.split("=", 1)
        folder_name = folder_name.strip()
        confirm = confirm.strip().lower()
        
        # Check confirmation
        if confirm != "yes":
            caller.msg("You must confirm with =yes to empty a folder.")
            return
            
        # Check if folder exists
        folders = caller.db.mail_folders
        if folder_name not in folders:
            caller.msg(f"Folder '{folder_name}' doesn't exist.")
            return
            
        # Special handling for reserved folders
        if folder_name.lower() == "incoming":
            caller.msg("You cannot empty the Incoming folder. Delete messages individually.")
            return
            
        if folder_name.lower() == "sent":
            caller.msg("You cannot empty the Sent folder. Delete messages individually.")
            return
            
        try:
            all_mail = self.get_all_mail()
            deleted_count = 0
            
            # Find messages in this folder and delete them
            to_delete = []
            for msg in all_mail:
                all_tags = msg.tags.all()
                for tag in all_tags:
                    if (isinstance(tag, str) and tag == f"folder_{folder_name}") or \
                       (hasattr(tag, 'db_key') and hasattr(tag, 'db_category') and
                        tag.db_category == "mail" and tag.db_key == f"folder_{folder_name}"):
                        to_delete.append(msg)
                        deleted_count += 1
                        break
            
            # Delete the messages
            for msg in to_delete:
                msg.delete()
                
            log_info(f"{caller} emptied mail folder '{folder_name}', deleted {deleted_count} messages")
            caller.msg(f"Folder '{folder_name}' emptied. {deleted_count} messages deleted.")
            
        except Exception as e:
            log_err(f"Error emptying folder: {e}")
            caller.msg(f"An error occurred emptying the folder: {e}")

    def get_all_mail(self):
        """Returns a list of all the messages received by the caller."""
        try:
            from evennia.comms.models import Msg
            log_info(f"Getting mail for {self.caller}")
            
            # Determine if we're dealing with an account or a character
            account_receiver = None
            object_receiver = None
            
            if hasattr(self, 'caller_is_account') and self.caller_is_account:
                account_receiver = self.caller
                log_info(f"Caller is an account, searching with account receiver {account_receiver}")
            else:
                object_receiver = self.caller
                log_info(f"Caller is an object, searching with object receiver {object_receiver}")
                
                # Also get the account if available for better coverage
                if hasattr(self.caller, 'account') and self.caller.account:
                    account_receiver = self.caller.account
                    log_info(f"Also using account {account_receiver} for character")
                    
            # Start with basic query for messages where the caller is a receiver
            if account_receiver:
                messages = list(Msg.objects.filter(db_receivers_accounts=account_receiver))
                log_info(f"Found {len(messages)} messages for account {account_receiver}")
            else:
                messages = list(Msg.objects.filter(db_receivers_objects=object_receiver))
                log_info(f"Found {len(messages)} messages for object {object_receiver}")
            
            # For compatibility, log some tag info for debugging
            for msg in messages:
                tag_info = []
                for tag in msg.tags.all():
                    if isinstance(tag, str):
                        tag_info.append(f"str:{tag}")
                    elif hasattr(tag, 'db_category') and hasattr(tag, 'db_key'):
                        tag_info.append(f"obj:{tag.db_key}(cat:{tag.db_category})")
                log_info(f"Message ID {msg.id} tags: {tag_info}")
            
            # Return all messages - they will be filtered by folder later
            log_info(f"Returning {len(messages)} messages for {self.caller}")
            return messages
            
        except Exception as e:
            log_err(f"Error in get_all_mail: {e}")
            return [] 