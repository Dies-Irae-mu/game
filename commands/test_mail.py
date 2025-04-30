"""
Diagnostic script to test the mail system.
"""

from evennia.utils.logger import log_info, log_err
from evennia.utils.evmenu import EvMenu
from evennia.comms.models import Msg
from django.db.models import Q
import sys

def diagnose_mail(caller):
    """Run diagnostic checks on the mail system."""
    try:
        log_info(f"Mail diagnostic run by {caller}")
        
        # Check for the mail imports
        caller.msg("Checking mail system imports...")
        try:
            # Check if we can import from the contrib path
            from evennia.contrib.game_systems.mail.mail import CmdMail
            caller.msg("|gSuccess:|n Found mail command at evennia.contrib.game_systems.mail.mail")
        except ImportError:
            caller.msg("|rError:|n Could not find mail command at evennia.contrib.game_systems.mail.mail")
            caller.msg("This suggests your Evennia installation might be missing the mail contrib system.")
            
        # Check if the local mail_ext.py has the correct imports
        try:
            import commands.mail_ext
            module_source = commands.mail_ext.__file__
            caller.msg(f"Mail extension module located at: {module_source}")
            
            # Check import path directly
            import inspect
            if hasattr(commands.mail_ext, 'CmdMailExtended'):
                parent_class = commands.mail_ext.CmdMailExtended.__bases__[0]
                parent_module = parent_class.__module__
                caller.msg(f"Mail extension inherits from: {parent_class.__name__} in {parent_module}")
                
                if "contrib.game_systems.mail.mail" in parent_module:
                    caller.msg("|gSuccess:|n Mail extension uses correct import path")
                else:
                    caller.msg("|rWarning:|n Mail extension may be using outdated import path")
        except Exception as e:
            log_err(f"Error checking mail_ext.py: {e}")
            caller.msg(f"|rError:|n Problem checking mail_ext.py: {e}")
        
        # Check if caller is an account or object
        if hasattr(caller, 'account') and caller.account:
            account = caller.account
            caller.msg(f"Running mail diagnostics as character {caller.key} with account {account.key}")
            
            # Check for mail messages where the account is a recipient
            account_msgs = Msg.objects.filter(db_receivers_accounts=account)
            account_count = account_msgs.count()
            caller.msg(f"Found {account_count} messages with account as recipient")
            
            # Check each message for mail tag
            mail_msgs = []
            for msg in account_msgs:
                # Get all tags for this message
                all_tags = msg.tags.all()
                tag_info = []
                for tag in all_tags:
                    if isinstance(tag, str):
                        tag_info.append(f"str:{tag}")
                    elif hasattr(tag, 'db_category') and hasattr(tag, 'db_key'):
                        tag_info.append(f"obj:{tag.db_key}(cat:{tag.db_category})")
                
                # Check if any tag has category 'mail'
                has_mail_tag = False
                for tag in all_tags:
                    if isinstance(tag, str):
                        # String tags from older versions don't have category
                        pass
                    elif hasattr(tag, 'db_category') and tag.db_category == 'mail':
                        has_mail_tag = True
                        break
                
                # If message has a mail tag, or if it was produced by the mail system (best effort)
                if has_mail_tag or any(t for t in ['new', 'sent', 'folder_'] if any(str(tag).startswith(t) for tag in all_tags)):
                    mail_msgs.append(msg)
                
                # Log the tags for debugging
                log_info(f"Message ID {msg.id}: tags={tag_info}, has_mail_tag={has_mail_tag}")
                
            mail_count = len(mail_msgs)
            caller.msg(f"Found {mail_count} messages with 'mail' category or mail-related tags")
            
            # Check for unread messages
            unread_count = 0
            for msg in mail_msgs:
                try:
                    all_tags = msg.tags.all()
                    for tag in all_tags:
                        # Check if tag is a string or has db_category/db_key attributes
                        if isinstance(tag, str):
                            if tag.upper() == "NEW":
                                unread_count += 1
                                break
                        elif hasattr(tag, 'db_category') and hasattr(tag, 'db_key'):
                            if tag.db_category == "mail" and tag.db_key == "new":
                                unread_count += 1
                                break
                except Exception as e:
                    log_err(f"Error checking unread tags: {e}")
                    continue
            caller.msg(f"Found {unread_count} unread mail messages")
            
            # Check for sent messages by direct DB query - this is the most reliable method
            # First try account sender
            sent_by_account = Msg.objects.filter(db_sender_accounts=account)
            # Then try character sender 
            sent_by_character = Msg.objects.filter(db_sender_objects=caller)
            # Combine unique results (using sets to avoid duplicates)
            sent_msgs_set = set()
            for msg in list(sent_by_account) + list(sent_by_character):
                sent_msgs_set.add(msg.id)
            
            sent_msgs = [Msg.objects.get(id=msg_id) for msg_id in sent_msgs_set]
            sent_count = len(sent_msgs)
            caller.msg(f"Found {sent_count} sent messages")
            
            # Check for messages in folders
            folder_msgs = {}
            for msg in mail_msgs:
                all_tags = msg.tags.all()
                for tag in all_tags:
                    if isinstance(tag, str) and tag.startswith("folder_"):
                        folder_name = tag[7:]  # Remove 'folder_' prefix
                        if folder_name not in folder_msgs:
                            folder_msgs[folder_name] = []
                        folder_msgs[folder_name].append(msg)
                        break
                    elif hasattr(tag, 'db_key') and hasattr(tag, 'db_category') and tag.db_key.startswith("folder_"):
                        folder_name = tag.db_key[7:]  # Remove 'folder_' prefix
                        if folder_name not in folder_msgs:
                            folder_msgs[folder_name] = []
                        folder_msgs[folder_name].append(msg)
                        break
            
            # Display folder message counts
            if folder_msgs:
                caller.msg("Messages in folders:")
                for folder_name, msgs in folder_msgs.items():
                    caller.msg(f"  {folder_name}: {len(msgs)} message(s)")
            
        else:
            caller.msg("Running mail diagnostics as account")
            
            # Check for mail messages where the account is a recipient
            account_msgs = Msg.objects.filter(db_receivers_accounts=caller)
            account_count = account_msgs.count()
            caller.msg(f"Found {account_count} messages with account as recipient")
            
            # Check for messages with 'mail' tag category
            mail_msgs = []
            for msg in account_msgs:
                # Get all tags for this message
                all_tags = msg.tags.all()
                tag_info = []
                for tag in all_tags:
                    if isinstance(tag, str):
                        tag_info.append(f"str:{tag}")
                    elif hasattr(tag, 'db_category') and hasattr(tag, 'db_key'):
                        tag_info.append(f"obj:{tag.db_key}(cat:{tag.db_category})")
                
                # Check if any tag has category 'mail'
                has_mail_tag = False
                for tag in all_tags:
                    if isinstance(tag, str):
                        # String tags from older versions don't have category
                        pass
                    elif hasattr(tag, 'db_category') and tag.db_category == 'mail':
                        has_mail_tag = True
                        break
                
                # If message has a mail tag, or if it was produced by the mail system (best effort)
                if has_mail_tag or any(t for t in ['new', 'sent', 'folder_'] if any(str(tag).startswith(t) for tag in all_tags)):
                    mail_msgs.append(msg)
                
                # Log the tags for debugging
                log_info(f"Message ID {msg.id}: tags={tag_info}, has_mail_tag={has_mail_tag}")
            
            mail_count = len(mail_msgs)
            caller.msg(f"Found {mail_count} messages with 'mail' category or mail-related tags")
            
            # Check for unread messages
            unread_count = 0
            for msg in mail_msgs:
                try:
                    all_tags = msg.tags.all()
                    for tag in all_tags:
                        # Check if tag is a string or has db_category/db_key attributes
                        if isinstance(tag, str):
                            if tag.upper() == "NEW":
                                unread_count += 1
                                break
                        elif hasattr(tag, 'db_category') and hasattr(tag, 'db_key'):
                            if tag.db_category == "mail" and tag.db_key == "new":
                                unread_count += 1
                                break
                except Exception as e:
                    log_err(f"Error checking unread tags: {e}")
                    continue
            caller.msg(f"Found {unread_count} unread mail messages")
            
            # Check for sent messages
            sent_msgs = Msg.objects.filter(db_sender_accounts=caller)
            sent_count = sent_msgs.count()
            caller.msg(f"Found {sent_count} sent messages")
            
            # Check for messages in folders
            folder_msgs = {}
            for msg in mail_msgs:
                all_tags = msg.tags.all()
                for tag in all_tags:
                    if isinstance(tag, str) and tag.startswith("folder_"):
                        folder_name = tag[7:]  # Remove 'folder_' prefix
                        if folder_name not in folder_msgs:
                            folder_msgs[folder_name] = []
                        folder_msgs[folder_name].append(msg)
                        break
                    elif hasattr(tag, 'db_key') and hasattr(tag, 'db_category') and tag.db_key.startswith("folder_"):
                        folder_name = tag.db_key[7:]  # Remove 'folder_' prefix
                        if folder_name not in folder_msgs:
                            folder_msgs[folder_name] = []
                        folder_msgs[folder_name].append(msg)
                        break
            
            # Display folder message counts
            if folder_msgs:
                caller.msg("Messages in folders:")
                for folder_name, msgs in folder_msgs.items():
                    caller.msg(f"  {folder_name}: {len(msgs)} message(s)")
        
        # Check the mail command class that's being used
        try:
            # Try to find the mail command in the cmdset
            cmdset = caller.cmdset.current
            mail_cmd = None
            for cmd in cmdset.commands:
                if cmd.key == "@mail" or "mail" in cmd.aliases:
                    mail_cmd = cmd
                    break
                    
            if mail_cmd:
                caller.msg(f"Found mail command: {mail_cmd.__class__.__name__} from {mail_cmd.__class__.__module__}")
            else:
                caller.msg("Mail command not found in current cmdset")
        except Exception as e:
            log_err(f"Error checking mail command: {e}")
            caller.msg(f"Error checking mail command: {e}")
        
        # Done
        caller.msg("Mail diagnostic complete")
    except Exception as e:
        log_err(f"Error in mail diagnostic: {e}")
        caller.msg(f"Error during mail diagnostic: {e}")

def cmd_diagnose_mail(caller):
    """Command function to run mail diagnostics."""
    diagnose_mail(caller)
    return "Mail diagnostic complete" 