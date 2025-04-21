"""
XP management commands.
"""

from evennia import default_cmds
from evennia.utils.search import search_object
from evennia.utils import utils
from typeclasses.characters import Character
from world.wod20th.utils.xp_utils import (
    process_xp_purchase, validate_xp_purchase, deduct_xp_and_log,
    check_weekly_xp_eligibility, _determine_stat_category, 
    get_current_rating, update_stat, process_xp_spend, normalize_stat_name,
    get_canonical_stat_name, get_proper_stat_name
)
from decimal import Decimal
from datetime import datetime
import traceback
from evennia.utils import logger
from django.db.models import Q
from evennia.utils.evtable import EvTable
from datetime import datetime
from django.db import transaction
import re
import decimal

"""
Helper functions
"""
def _display_xp(caller, target):
    """Display XP information for a character"""
    try:
        from decimal import Decimal
        # Get XP data
        xp_data = target.attributes.get('xp')
        if not xp_data:
            xp_data = {
                'total': Decimal('0.00'),
                'current': Decimal('0.00'),
                'spent': Decimal('0.00'),
                'ic_xp': Decimal('0.00'),
                'monthly_spent': Decimal('0.00'),
                'last_reset': datetime.now(),
                'spends': [],
                'last_scene': None,
                'scenes_this_week': 0
            }
            target.attributes.add('xp', xp_data)

        # Calculate IC XP and Award XP from spends history
        ic_xp = Decimal('0.00')
        award_xp = Decimal('0.00')
        if xp_data.get('spends'):
            for entry in xp_data['spends']:
                if entry['type'] == 'receive':
                    amount = Decimal(str(entry['amount'])).quantize(Decimal('0.01'))
                    if entry['reason'] == 'Weekly Activity':
                        ic_xp += amount
                    else:
                        award_xp += amount

        # Format display values
        total = Decimal(str(xp_data['total'])).quantize(Decimal('0.01'))
        current = Decimal(str(xp_data['current'])).quantize(Decimal('0.01'))
        spent = Decimal(str(xp_data['spent'])).quantize(Decimal('0.01'))

        # Build the display
        total_width = 78
        
        # Header
        title = f" {target.name}'s XP "
        title_len = len(title)
        dash_count = (total_width - title_len) // 2
        msg = f"{'|b-|n' * dash_count}{title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
        
        
        # Format XP display
        left_col_width = 20
        right_col_width = 12
        spacing = " " * 14
        
        ic_xp_display = f"{'|wIC XP:|n':<{left_col_width}}{ic_xp:>{right_col_width}.2f}"
        total_xp_display = f"{'|wTotal XP:|n':<{left_col_width}}{total:>{right_col_width}.2f}"
        current_xp_display = f"{'|wCurrent XP:|n':<{left_col_width}}{current:>{right_col_width}.2f}"
        award_xp_display = f"{'|wAward XP:|n':<{left_col_width}}{award_xp:>{right_col_width}.2f}"
        spent_xp_display = f"{'|wSpent XP:|n':<{left_col_width}}{spent:>{right_col_width}.2f}"
        
        msg += f"{ic_xp_display}{spacing}{award_xp_display}\n"
        msg += f"{total_xp_display}{spacing}{spent_xp_display}\n"
        msg += f"{current_xp_display}\n"
        
        # Recent Activity Section
        activity_title = "|y Recent Activity |n"
        title_len = len(activity_title)
        dash_count = (total_width - title_len) // 2
        msg += f"{'|b-|n' * dash_count}{activity_title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
        
        if xp_data.get('spends'):
            for entry in xp_data['spends'][:5]:  # Show last 5 entries
                timestamp = datetime.fromisoformat(entry['timestamp'])
                formatted_time = timestamp.strftime("%Y-%m-%d %H:%M")
                entry_type = entry['type'].lower()
                amount = entry['amount']
                
                if entry_type == 'receive':
                    msg += f"{formatted_time} - Received {amount} XP: {entry['reason']}\n"
                elif entry_type == 'spend':
                    if entry.get('flaw_buyoff'):
                        msg += f"{formatted_time} - Spent {amount} XP to buy off {entry['stat_name']} flaw\n"
                    elif 'previous_rating' in entry:
                        # This is a normal XP spend
                        msg += f"{formatted_time} - Spent {amount} XP on {entry['stat_name']} - increased from {entry['previous_rating']} to {entry['new_rating']}\n"
                    elif 'staff_name' in entry:
                        # This is an XP removal by staff
                        msg += f"{formatted_time} - XP Removed by {entry['staff_name']}: {amount} XP ({entry['reason']})\n"
                    else:
                        # Generic spend entry
                        msg += f"{formatted_time} - Spent {amount} XP on {entry['reason']}\n"
                elif entry_type == 'refund':
                    # Refund entry
                    msg += f"{formatted_time} - XP Refunded by {entry['staff_name']}: {amount} XP ({entry['reason']})\n"
                elif entry_type == 'approve':
                    # Approve entry
                    msg += f"{formatted_time} - XP Approved by {entry['staff_name']}: {amount} XP ({entry['reason']})\n"
        else:
            msg += "No XP history yet.\n"
        
        # Footer
        msg += f"{'|b-|n' * total_width}"
        
        caller.msg(msg)

    except Exception as e:
        logger.error(f"Error displaying XP for {target.name}: {str(e)}")
        caller.msg("Error displaying XP information.")

def _display_detailed_history(caller, character):
    """Display detailed XP history for a character."""
    if not character.db.xp or not character.db.xp.get('spends'):
        caller.msg(f"{character.name} has no XP history.")
        return
        
    table = EvTable("|wTimestamp|n", 
                    "|wType|n", 
                    "|wAmount|n", 
                    "|wDetails|n",
                    width=78)
                    
    for entry in character.db.xp['spends']:
        timestamp = datetime.fromisoformat(entry['timestamp'])
        entry_type = entry['type'].title()
        amount = f"{float(entry['amount']):.2f}"
        
        # Set a default value for details
        details = entry.get('reason', 'No reason given')
        
        # Handle different entry types
        if entry_type == "Spend":
            if 'stat_name' in entry and 'previous_rating' in entry:
                # Handle stat names with parentheses
                stat_name = entry['stat_name']
                details = f"{stat_name} ({entry['previous_rating']} -> {entry['new_rating']})"
        elif entry_type == "Receive":
            details = entry.get('reason', 'Staff award')
        elif entry_type == "Approve":
            details = f"Staff approved - {entry.get('reason', 'No reason given')}"
        elif entry_type == "Refund":
            details = f"Staff refund - {entry.get('reason', 'No reason given')}"
            
        table.add_row(
            timestamp.strftime('%Y-%m-%d %H:%M'),
            entry_type,
            amount,
            details
        )
        
    caller.msg(f"\n|wDetailed XP History for {character.name}|n")
    caller.msg(str(table))

def fix_powers(character):
    """Fix duplicate powers and ensure proper categorization in character stats."""
    if not character.db.stats:
        return False

    # Get the powers dictionary
    powers = character.db.stats.get('powers', {})
    if not powers:
        return False
        
    # Define power type mappings (plural to singular)
    power_mappings = {
        'spheres': 'sphere',
        'arts': 'art',
        'realms': 'realm',
        'disciplines': 'discipline',
        'gifts': 'gift',
        'numina': 'numina',
        'charms': 'charm',
        'blessings': 'blessing'
    }

    changes_made = False

    # Fix each power type
    for plural, singular in power_mappings.items():
        if plural in powers and singular in powers:
            # Merge plural into singular
            for power_name, values in powers[plural].items():
                if power_name not in powers[singular]:
                    powers[singular][power_name] = values
                else:
                    # Take the higher value if the power exists in both places
                    current_perm = powers[singular][power_name].get('perm', 0)
                    current_temp = powers[singular][power_name].get('temp', 0)
                    new_perm = values.get('perm', 0)
                    new_temp = values.get('temp', 0)
                    powers[singular][power_name]['perm'] = max(current_perm, new_perm)
                    powers[singular][power_name]['temp'] = max(current_temp, new_temp)

            # Remove the plural category
            del powers[plural]
            changes_made = True

    # Ensure all power categories exist
    for singular in power_mappings.values():
        if singular not in powers:
            powers[singular] = {}
            changes_made = True

    # Special handling for gifts - ensure they're properly formatted
    if 'gift' in powers:
        fixed_gifts = {}
        for gift_name, values in powers['gift'].items():
            # If the gift name doesn't start with the proper category prefix, try to fix it
            if not any(gift_name.startswith(prefix) for prefix in ['Breed:', 'Auspice:', 'Tribe:', 'Gift:']):
                # Check if it's already properly formatted
                if ':' in gift_name:
                    fixed_gifts[gift_name] = values
                else:
                    # Add generic 'Gift:' prefix if we can't determine the type
                    fixed_gifts[f'{gift_name}'] = values
            else:
                fixed_gifts[gift_name] = values
        if fixed_gifts != powers['gift']:
            powers['gift'] = fixed_gifts
            changes_made = True

    if changes_made:
        character.db.stats['powers'] = powers
        
    return changes_made

def get_canonical_gift_name(stat_name):
    """Get the canonical name of a gift from the database."""
    from world.wod20th.models import Stat
    gift = Stat.objects.filter(
        Q(name__iexact=stat_name) | Q(gift_alias__icontains=stat_name),
        category='powers',
        stat_type='gift'
    ).first()
    return gift.name if gift else stat_name

def spend_xp(self, stat_name, new_rating, category, subcategory, reason):
    """
    Spend XP to increase a stat.
    Returns (success, message)
    """
    # Get current rating based on category
    current_rating = 0
    if category == 'powers' and subcategory == 'gift':
        # Special handling for gifts
        if 'powers' in self.db.stats and 'gift' in self.db.stats['powers']:
            # Try to find the gift with case-insensitive match
            for gift_name, gift_data in self.db.stats['powers']['gift'].items():
                if gift_name.lower() == stat_name.lower():
                    current_rating = gift_data.get('perm', 0)
                    break
    elif category == 'pools':
        if 'pools' in self.db.stats:
            current_rating = self.db.stats['pools'].get(proper_stat_name, {}).get('perm', 0)
        
        # If not found in pools, check in advantages
        if current_rating == 0 and 'advantages' in self.db.stats:
            current_rating = self.db.stats['advantages'].get(proper_stat_name, {}).get('perm', 0)
    elif category == 'secondary_abilities':
        # Get proper case for stat name
        proper_stat_name = self._get_proper_stat_name(stat_name, category, subcategory)
        
        # Directly check the secondary_abilities structure
        current_rating = self.db.stats.get('secondary_abilities', {}).get(subcategory, {}).get(proper_stat_name, {}).get('perm', 0)
        
        # If not found, try case-insensitive search
        if current_rating == 0:
            for stat_name_key, stat_data in self.db.stats.get('secondary_abilities', {}).get(subcategory, {}).items():
                if stat_name_key.lower() == proper_stat_name.lower():
                    current_rating = stat_data.get('perm', 0)
                    proper_stat_name = stat_name_key  # Use the existing name with correct case
                    break
    else:
        current_rating = self.get_stat(category, subcategory, stat_name, temp=False) or 0

    # Calculate cost
    cost, requires_approval = self.calculate_xp_cost(
        stat_name, new_rating, current_rating,
        category=category, subcategory=subcategory
    )
    
    if cost == 0:
        return False, "Invalid stat or no increase needed"
        
    if requires_approval:
        return False, "This purchase requires staff approval"

    # Check if we have enough XP
    if self.db.xp['current'] < cost:
        return False, f"Not enough XP. Cost: {cost}, Available: {self.db.xp['current']}"

    # Validate the purchase
    can_purchase, error_msg = self.validate_xp_purchase(
        stat_name, new_rating,
        category=category, subcategory=subcategory
    )
    
    if not can_purchase:
        return False, error_msg

    # All checks passed, make the purchase
    try:
        # Update the stat based on category
        if category == 'pools':
            # Get proper case for stat name
            proper_stat_name = self._get_proper_stat_name(stat_name, category, subcategory)
            
            # Ensure both pools and advantages dictionaries exist
            if 'pools' not in self.db.stats:
                self.db.stats['pools'] = {}
            if 'advantages' not in self.db.stats:
                self.db.stats['advantages'] = {}
            
            # Update in both locations to ensure compatibility
            self.db.stats['pools'][proper_stat_name] = {
                'perm': new_rating,
                'temp': new_rating
            }
            self.db.stats['advantages'][proper_stat_name] = {
                'perm': new_rating,
                'temp': new_rating
            }
        elif category == 'secondary_abilities':
            # Ensure the secondary_abilities structure exists
            if 'secondary_abilities' not in self.db.stats:
                self.db.stats['secondary_abilities'] = {}
            if subcategory not in self.db.stats['secondary_abilities']:
                self.db.stats['secondary_abilities'][subcategory] = {}
            
            # Store the secondary ability in the correct location
            self.db.stats['secondary_abilities'][subcategory][proper_stat_name] = {
                'perm': new_rating,
                'temp': new_rating
            }
        else:
            self.set_stat(category, subcategory, stat_name, new_rating, temp=False)
            self.set_stat(category, subcategory, stat_name, new_rating, temp=True)

        # Deduct XP
        self.db.xp['current'] -= cost
        self.db.xp['spent'] += cost

        # Log the spend with stat information
        spend_entry = {
            'type': 'spend',
            'amount': float(cost),
            'stat_name': proper_stat_name if category == 'pools' else stat_name,
            'previous_rating': current_rating,
            'new_rating': new_rating,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        
        if 'spends' not in self.db.xp:
            self.db.xp['spends'] = []
        self.db.xp['spends'].insert(0, spend_entry)

        return True, f"Successfully increased {proper_stat_name if category == 'pools' else stat_name} from {current_rating} to {new_rating} (Cost: {cost} XP)"

    except Exception as e:
        return False, f"Error processing purchase: {str(e)}"

def buy_stat(self, stat_name, new_rating, category=None, subcategory=None, reason="", current_rating=None):
    """Buy or increase a stat with XP."""
    try:
        # Special handling for Mother's Touch and similar gifts
        if stat_name.lower() in ["mother's touch", "grandmother's touch", "lover's touch"]:
            category = 'powers'
            subcategory = 'gift'
            # Find the gift in JSON files
            import json
            import os
            
            data_dir = os.path.join('diesirae', 'data')
            gift_files = [
                'rank1_garou_gifts.json',
                'rank2_garou_gifts.json',
                'rank3_garou_gifts.json',
                'rank4_garou_gifts.json',
                'rank5_garou_gifts.json',
                'ajaba_gifts.json',
                'bastet_gifts.json',
                'corax_gifts.json',
                'gurahl_gifts.json',
                'kitsune_gifts.json',
                'mokole_gifts.json',
                'nagah_gifts.json',
                'nuwisha_gifts.json',
                'ratkin_gifts.json',
                'rokea_gifts.json'
            ]
            
            found_gift = None
            for gift_file in gift_files:
                try:
                    file_path = os.path.join(data_dir, gift_file)
                    if os.path.exists(file_path):
                        with open(file_path, 'r') as f:
                            gifts = json.load(f)
                            # Check if the gift exists in this file
                            for gift in gifts:
                                if gift.get('name', '').lower() == stat_name.lower():
                                    found_gift = gift
                                    stat_name = gift['name']  # Use the canonical name from JSON
                                    logger.log_info(f"Found gift in {gift_file}: {gift['name']}")
                                    break
                            if found_gift:
                                break
                except Exception as e:
                    logger.log_err(f"Error reading gift file {gift_file}: {str(e)}")
                    continue

        # Preserve original case of stat_name
        original_stat_name = stat_name
        
        # Fix any power issues before proceeding
        if category == 'powers':
            fix_powers(self)
            # After fixing, ensure we're using the correct subcategory
            if subcategory in ['spheres', 'arts', 'realms', 'disciplines', 'gifts', 'charms', 'blessings', 'rituals', 'sorceries', 'advantages']:
                # Convert to singular form
                subcategory = subcategory.rstrip('s')
                if subcategory == 'advantage':
                    subcategory = 'special_advantage'

        # For secondary abilities, ensure proper case
        if category == 'secondary_abilities':
            from world.wod20th.utils.xp_utils import proper_title_case
            stat_name = proper_title_case(stat_name)
            original_stat_name = stat_name  # Updates original_stat_name to match proper case

        # Ensure proper structure exists
        self.ensure_stat_structure(category, subcategory)
        
        # Get character's splat
        splat = self.get_stat('other', 'splat', 'Splat', temp=False)
        if not splat:
            return False, "Character splat not set"

        # Calculate cost
        cost, requires_approval = self.calculate_xp_cost(
            stat_name, new_rating, current_rating,
            category=category, subcategory=subcategory
        )
        
        if cost == 0:
            return False, "Invalid stat or no increase needed"
            
        if requires_approval:
            return False, "This purchase requires staff approval"

        # Check if we have enough XP
        if self.db.xp['current'] < cost:
            return False, f"Not enough XP. Cost: {cost}, Available: {self.db.xp['current']}"

        # Validate the purchase
        can_purchase, error_msg = self.validate_xp_purchase(
            stat_name, new_rating,
            category=category, subcategory=subcategory
        )
        
        if not can_purchase:
            return False, error_msg

        # All checks passed, make the purchase
        # Special handling for gifts
        if category == 'powers' and subcategory == 'gift':
            # Initialize powers and gift structure if needed
            if 'powers' not in self.db.stats:
                self.db.stats['powers'] = {}
            if 'gift' not in self.db.stats['powers']:
                self.db.stats['powers']['gift'] = {}
            
            # Store the gift with its canonical name
            self.db.stats['powers']['gift'][stat_name] = {
                'perm': new_rating,
                'temp': new_rating
            }
            # Store the alias if different from canonical name
            if original_stat_name.lower() != stat_name.lower():
                # Ensure the alias is a string, not a list
                alias_to_use = original_stat_name
                if isinstance(original_stat_name, list):
                    # If it's a list, use the first element or a joined string
                    if original_stat_name:
                        alias_to_use = original_stat_name[0] if len(original_stat_name) == 1 else " ".join(original_stat_name)
                    else:
                        alias_to_use = stat_name  # Fallback if empty list
                
                self.set_gift_alias(stat_name, alias_to_use, new_rating)
        else:
            # Handle non-gift stats
            self.set_stat(category, subcategory, stat_name, new_rating, temp=False)
            self.set_stat(category, subcategory, stat_name, new_rating, temp=True)

        # Deduct XP
        self.db.xp['current'] -= cost
        self.db.xp['spent'] += cost

        # Log the spend
        spend_entry = {
            'type': 'spend',
            'amount': float(cost),
            'stat_name': stat_name,
            'previous_rating': current_rating,
            'new_rating': new_rating,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        
        if 'spends' not in self.db.xp:
            self.db.xp['spends'] = []
        self.db.xp['spends'].insert(0, spend_entry)

        return True, f"Successfully increased {stat_name} from {current_rating} to {new_rating} (Cost: {cost} XP)"

    except Exception as e:
        logger.error(f"Error buying stat: {str(e)}")
        return False, f"Error processing stat purchase: {str(e)}"

# Staff spend (No validation checks, just deducts XP)
def staff_spend(self, stat_name, new_rating, category=None, subcategory=None, reason=""):
    if not self.caller.check_permstring("builders"):
        self.caller.msg("You don't have permission to do that.")
        return

    args = self.args.strip()
    if not args:
        self.caller.msg("Usage: +xp/staffspend <character>/<stat> <rating> = <reason>")
        return

    # Split the argument into target_info (character/stat rating) and reason
    if "=" in args:
        target_info, reason = args.split("=", 1)
        reason = reason.strip()
        if not reason:
            reason = "Staff Spend"
    else:
        target_info = args
        reason = "Staff Spend"

    logger.log_info(f"Processing staffspend command for {self.caller.key}")
    logger.log_info(f"Parsed input - target_info: {target_info}, reason: {reason}")

    # Split target_info into character name and stat info
    if "/" not in target_info:
        self.caller.msg("Usage: +xp/staffspend <character>/<stat> <rating> = <reason>")
        return

    name, stat_info = target_info.split("/", 1)
    name = name.strip()
    stat_info = stat_info.strip()

    logger.log_info(f"Split target info - name: {name}, stat_info: {stat_info}")

    # Find the target character
    target = self.caller.search(name, global_search=True)
    if not target:
        return

    # Parse stat info into stat name and rating
    stat_parts = stat_info.split()
    if len(stat_parts) < 2:
        self.caller.msg("You must specify both a stat name and rating.")
        return

    stat_name = " ".join(stat_parts[:-1])
    try:
        rating = int(stat_parts[-1])
    except ValueError:
        self.caller.msg("Rating must be a number.")
        return

    logger.log_info(f"Parsed stat - name: {stat_name}, rating: {rating}")
    
    # Store the original stat name for gift aliases
    original_stat_name = stat_name

    # Determine stat category
    from world.wod20th.utils.xp_utils import _determine_stat_category
    category, subcategory = _determine_stat_category(stat_name)

    if not category or not subcategory:
        self.caller.msg(f"Could not determine stat category for '{stat_name}'.")
        logger.log_info(f"Failed to determine category for: {stat_name}")
        return

    logger.log_info(f"Determined category: {category}, subcategory: {subcategory}")

    # Check for proper case for the stat name
    from typeclasses.characters import Character
    if isinstance(target, Character):
        # For gifts, we want to check if this is an alias and get the canonical name
        if category == 'powers' and subcategory == 'gift':
            # Initialize gift_alias_used attribute
            self.gift_alias_used = None
            
            # Get proper name, this will also set gift_alias_used if an alias is found
            proper_stat = self._get_proper_stat_name(stat_name, category, subcategory)
            if proper_stat:
                stat_name = proper_stat
                logger.log_info(f"Got proper gift name: {stat_name}")
        else:
            # Get proper case for standard stats
            proper_stat = target.get_proper_stat_name(category, subcategory, stat_name)
            if proper_stat:
                stat_name = proper_stat
                logger.log_info(f"Got proper stat name: {stat_name}")
            
    # Use proper title casing for gifts and other stats that need it
    if category == 'powers' and subcategory == 'gift':
        from world.wod20th.utils.xp_utils import proper_title_case
        if not self.gift_alias_used:
            self.gift_alias_used = original_stat_name
        stat_name = proper_title_case(stat_name)
        logger.log_info(f"Applied proper title case: {stat_name}")

    # Format the reason
    staff_reason = f"Staff Spend: {self.caller.name} - {reason}"

    # Process the spend
    from world.wod20th.utils.xp_utils import process_xp_spend
    success, message, cost = process_xp_spend(
        target, stat_name, rating, category, subcategory, 
        reason=staff_reason, is_staff_spend=True
    )

    # If successful and this is a gift, store the alias
    if success and category == 'powers' and subcategory == 'gift' and hasattr(target, 'set_gift_alias'):
        try:
            if original_stat_name.lower() != stat_name.lower():
                # Ensure the alias is a string, not a list or None
                alias_to_use = original_stat_name if original_stat_name else stat_name
                if isinstance(alias_to_use, list):
                    # If it's a list, use the first element or a joined string
                    if alias_to_use:
                        alias_to_use = alias_to_use[0] if len(alias_to_use) == 1 else " ".join(alias_to_use)
                    else:
                        alias_to_use = stat_name  # Fallback if empty list
                
                target.set_gift_alias(stat_name, alias_to_use, rating)
                logger.log_info(f"Set gift alias for {stat_name}: {alias_to_use}")
        except Exception as e:
            logger.log_err(f"Error setting gift alias: {str(e)}")
            self.caller.msg(f"Note: Gift was set successfully but there was an error setting the alias: {str(e)}")

    # Report the result
    if success:
        self.caller.msg(f"Successfully set {name}'s {stat_name} to {rating}. Cost: {cost} XP.")
        # Also inform the target character
        target.msg(f"{self.caller.name} has set your {stat_name} to {rating}. Cost: {cost} XP.")
    else:
        # Provide more helpful error messages
        error_prefix = f"Error processing staff spend for {name}'s {stat_name}: "
        
        if "New rating must be higher" in message:
            self.caller.msg(f"{error_prefix}The new rating ({rating}) must be higher than the current rating.")
        elif "Not enough XP" in message:
            self.caller.msg(f"{error_prefix}{message}")
            self.caller.msg(f"Hint: You may need to award additional XP to the character first.")
        elif "Cost calculation returned zero" in message:
            self.caller.msg(f"{error_prefix}{message}")
            self.caller.msg(f"This usually means the stat is not valid for this character type or there's an issue with cost calculation.")
        else:
            # For other errors, show the full message
            self.caller.msg(f"{error_prefix}{message}")
            
        # Log the error for debugging
        logger.log_err(f"Staff spend error for {name}'s {stat_name}: {message}")

class CmdXP(default_cmds.MuxCommand):
    """
    XP management commands.
    
    Usage:
      +xp                     - View your XP
      +xp <name>              - View another character's XP (Staff only)
      +xp/view <name>         - View detailed XP history (Staff only)
      +xp/sub <name>/<amount>=<reason> - Remove XP from character (Staff only)
      +xp/init                - Initialize scene tracking
      +xp/endscene            - Manually end current scene
      +xp/add <name>=<amt>    - Add XP to a character (Staff only)
      +xp/spend <stat> <rating>=<reason> - Spend XP (Must be in OOC area)
      +xp/forceweekly         - Force weekly XP distribution (Staff only)
      +xp/staffspend <name>/<stat> <rating>=<reason> - Spend XP on behalf of a character (Staff only)
      +xp/approve <name>/<amount>=<reason> - Record XP spend without cost (Staff only)
      +xp/refund <name>/<amount>=<reason> - Refund XP to a character (Staff only)
      +xp/fixstats <name>     - Fix a character's stats structure (Staff only)
      +xp/fixdata <name>      - Fix a character's XP data structure (Staff only)
      
    Examples:
      +xp/spend Strength 3=Getting stronger
      +xp/spend Potence 2=Learning from mentor
      +xp/spend Resources 2=Business success
      +xp/staffspend Bob/Strength 3=Staff correction
      +xp/sub Bob/5=Correcting XP error
      +xp/approve Bob/5=Learning through mentor IC
      +xp/refund Bob/3=Overcharge correction
      +xp/staffspend ryan/Dark Fate=Flaw Buyoff
      +xp/fixdata Bob         - Fix Bob's XP data structure
    """
    
    key = "+xp"
    aliases = ["xp"]
    lock = "cmd:all()"
    help_category = "Roleplay"
    
    def func(self):
        """Main function that dispatches to the appropriate handler."""
        if not self.args and not self.switches:
            # Display own XP
            self.view_own_xp()
            return
        
        # Handle various switches
        if not self.switches:
            # View another character's XP (staff only)
            self.view_other_xp()
        elif "view" in self.switches:
            # View detailed XP history (staff only)
            self.view_xp_history()
        elif "sub" in self.switches:
            # Remove XP from character (staff only)
            self.subtract_xp()
        elif "init" in self.switches:
            # Initialize scene tracking
            self.init_scene_tracking()
        elif "endscene" in self.switches:
            # Manually end current scene
            self.end_scene()
        elif "add" in self.switches:
            # Add XP to a character (staff only)
            self.add_xp()
        elif "spend" in self.switches:
            # Spend XP
            self.spend_xp()
        elif "forceweekly" in self.switches:
            # Force weekly XP distribution (staff only)
            self.force_weekly_xp()
        elif "staffspend" in self.switches:
            # Spend XP on behalf of a character (staff only)
            self.staff_spend_xp()
        elif "approve" in self.switches:
            # Record XP spend without cost (staff only)
            self.approve_xp()
        elif "refund" in self.switches:
            # Refund XP to a character (staff only)
            self.refund_xp()
        elif "fixstats" in self.switches:
            # Fix a character's stats structure (staff only)
            self.fix_stats()
        elif "fixdata" in self.switches:
            # Fix a character's XP data structure (staff only)
            self.fix_xp_data()
        else:
            # Unknown switch
            self.caller.msg(f"Unknown switch: {self.switches[0]}")
    
    def view_own_xp(self):
        """View your own XP."""
        _display_xp(self.caller, self.caller)
    
    def view_other_xp(self):
        """View another character's XP (staff only)."""
        if not self.args:
            self.caller.msg("Usage: +xp <name>")
            return
            
        if not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to view other characters' XP.")
            return
            
        target = self.caller.search(self.args, global_search=True)
        if not target:
            return
            
        _display_xp(self.caller, target)
    
    def view_xp_history(self):
        """View detailed XP history (staff only)."""
        if not self.args:
            self.caller.msg("Usage: +xp/view <name>")
            return
            
        if not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to view XP history.")
            return
            
        target = self.caller.search(self.args, global_search=True)
        if not target:
            return
            
        _display_detailed_history(self.caller, target)
    
    @transaction.atomic
    def subtract_xp(self):
        """Remove XP from character (staff only)."""
        if not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to subtract XP.")
            return
            
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +xp/sub <name>/<amount>=<reason>")
            return
            
        target_info, reason = self.args.split("=", 1)
        reason = reason.strip()
        
        if "/" not in target_info:
            self.caller.msg("Usage: +xp/sub <name>/<amount>=<reason>")
            return
            
        name, amount_str = target_info.split("/", 1)
        name = name.strip()
        amount_str = amount_str.strip()
        
        # Validate the input is a proper decimal number
        try:
            # First clean up the input, handling commas and spaces
            amount_str = amount_str.replace(',', '.').replace(' ', '')
            # Ensure it's a valid decimal format
            if not re.match(r'^-?\d+(\.\d+)?$', amount_str):
                self.caller.msg("Amount must be a valid number (e.g. 5 or 5.5).")
                return
                
            amount = Decimal(amount_str)
            if amount <= 0:
                self.caller.msg("Amount must be positive.")
                return
        except (ValueError, decimal.InvalidOperation):
            self.caller.msg("Amount must be a valid number (e.g. 5 or 5.5).")
            return
            
        target = self.caller.search(name, global_search=True)
        if not target:
            return
            
        # Check if target has XP data
        if not hasattr(target.db, 'xp') or not target.db.xp:
            target.db.xp = {
                'total': Decimal('0.00'),
                'current': Decimal('0.00'),
                'spent': Decimal('0.00'),
                'ic_xp': Decimal('0.00'),
                'spends': []
            }
            
        # Ensure amount doesn't exceed current XP
        current_xp = Decimal(str(target.db.xp.get('current', 0)))
        if amount > current_xp:
            self.caller.msg(f"{target.name} only has {current_xp} XP. Cannot remove {amount}.")
            return
            
        # Update XP values
        target.db.xp['current'] -= amount
        target.db.xp['total'] -= amount
        
        # Log the transaction
        log_entry = {
            'type': 'spend',
            'amount': float(amount),
            'reason': reason,
            'staff_name': self.caller.name,
            'timestamp': datetime.now().isoformat()
        }
        
        if 'spends' not in target.db.xp:
            target.db.xp['spends'] = []
        target.db.xp['spends'].insert(0, log_entry)
        
        self.caller.msg(f"Removed {amount} XP from {target.name}. Reason: {reason}")
        target.msg(f"{self.caller.name} has removed {amount} XP from your total. Reason: {reason}")
    
    def init_scene_tracking(self):
        """Initialize scene tracking for the character."""
        if not hasattr(self.caller.db, 'xp') or not self.caller.db.xp:
            self.caller.db.xp = {
                'total': Decimal('0.00'),
                'current': Decimal('0.00'),
                'spent': Decimal('0.00'),
                'ic_xp': Decimal('0.00'),
                'spends': [],
                'scenes_this_week': 0,
                'last_scene': None
            }
            self.caller.msg("XP data initialized. You are now ready to track scenes.")
        else:
            if 'scenes_this_week' not in self.caller.db.xp:
                self.caller.db.xp['scenes_this_week'] = 0
            if 'last_scene' not in self.caller.db.xp:
                self.caller.db.xp['last_scene'] = None
                
            self.caller.msg("Scene tracking initialized. You can now earn XP from scenes.")
    
    @transaction.atomic
    def end_scene(self):
        """Manually end current scene and update scene tracking."""
        if not hasattr(self.caller.db, 'xp') or not self.caller.db.xp:
            self.caller.msg("You need to initialize XP tracking first. Use +xp/init.")
            return
            
        if 'scenes_this_week' not in self.caller.db.xp:
            self.caller.db.xp['scenes_this_week'] = 0
            
        # Check if there's a scene in progress
        last_scene = self.caller.db.xp.get('last_scene')
        if not last_scene:
            self.caller.msg("No scene in progress. Use +scene/start to begin a new scene.")
            return
            
        # Calculate time since last scene
        try:
            last_scene_time = datetime.fromisoformat(last_scene)
            now = datetime.now()
            
            if (now - last_scene_time).total_seconds() < 1800:  # 30 minutes minimum
                self.caller.msg("A scene must last at least 30 minutes to count for XP.")
                return
                
            # Update scene count
            self.caller.db.xp['scenes_this_week'] += 1
            self.caller.db.xp['last_scene'] = now.isoformat()
            
            self.caller.msg(f"Scene ended. You now have {self.caller.db.xp['scenes_this_week']} scenes this week.")
            
        except (ValueError, TypeError):
            self.caller.msg("Error processing scene time. Scene tracking has been reset.")
            self.caller.db.xp['last_scene'] = datetime.now().isoformat()
    
    @transaction.atomic
    def add_xp(self):
        """Add XP to a character (staff only)."""
        if not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to add XP.")
            return
            
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +xp/add <name>=<amount>")
            return
            
        name, amount_str = self.args.split("=", 1)
        name = name.strip()
        amount_str = amount_str.strip()
        
        # Validate the input is a proper decimal number
        try:
            # First clean up the input, handling commas and spaces
            amount_str = amount_str.replace(',', '.').replace(' ', '')
            # Ensure it's a valid decimal format
            if not re.match(r'^-?\d+(\.\d+)?$', amount_str):
                self.caller.msg("Amount must be a valid number (e.g. 5 or 5.5).")
                return
                
            amount = Decimal(amount_str)
            if amount <= 0:
                self.caller.msg("Amount must be positive.")
                return
        except (ValueError, decimal.InvalidOperation):
            self.caller.msg("Amount must be a valid number (e.g. 5 or 5.5).")
            return
            
        target = self.caller.search(name, global_search=True)
        if not target:
            return
            
        # Check if target has XP data
        if not hasattr(target.db, 'xp') or not target.db.xp:
            target.db.xp = {
                'total': Decimal('0.00'),
                'current': Decimal('0.00'),
                'spent': Decimal('0.00'),
                'ic_xp': Decimal('0.00'),
                'spends': []
            }
            
        # Update XP values - ensure they're Decimal objects
        target.db.xp['current'] = Decimal(str(target.db.xp.get('current', 0))) + amount
        target.db.xp['total'] = Decimal(str(target.db.xp.get('total', 0))) + amount
        
        # Log the transaction
        log_entry = {
            'type': 'receive',
            'amount': float(amount),
            'reason': f"Staff Award: {self.caller.name}",
            'timestamp': datetime.now().isoformat()
        }
        
        if 'spends' not in target.db.xp:
            target.db.xp['spends'] = []
        target.db.xp['spends'].insert(0, log_entry)
        
        self.caller.msg(f"Added {amount} XP to {target.name}.")
        target.msg(f"{self.caller.name} has awarded you {amount} XP.")
    
    @transaction.atomic
    def spend_xp(self):
        """Spend XP on a stat."""
        # Check if the player is in an OOC Area
        location = self.caller.location
        if not location or location.db.roomtype != "OOC Area":
            self.caller.msg("You can only spend XP in an OOC Area.")
            return
            
        if not self.args:
            self.caller.msg("Usage: +xp/spend <stat> <rating>=<reason>")
            return
            
        # Split the argument into stat_info and reason
        if "=" in self.args:
            stat_info, reason = self.args.split("=", 1)
            reason = reason.strip()
        else:
            stat_info = self.args
            reason = "Character Development"
            
        stat_parts = stat_info.split()
        if len(stat_parts) < 2:
            self.caller.msg("You must specify both a stat name and rating.")
            return
            
        try:
            rating = int(stat_parts[-1])
            stat_name = " ".join(stat_parts[:-1])
        except ValueError:
            self.caller.msg("Rating must be a number.")
            return
            
        # Store original stat name for gift alias
        original_stat_name = stat_name
            
        # Determine stat category
        category, subcategory = _determine_stat_category(stat_name)
        if not category or not subcategory:
            self.caller.msg(f"Could not determine category for '{stat_name}'.")
            return
            
        # For gifts, get the canonical name
        if category == 'powers' and subcategory == 'gift':
            canonical_name = get_canonical_gift_name(stat_name)
            if canonical_name != stat_name:
                logger.log_info(f"Using canonical gift name: {canonical_name} instead of {stat_name}")
                stat_name = canonical_name
                
        # Process the XP spend
        success, message, cost = process_xp_spend(
            self.caller, stat_name, rating, category, subcategory, reason=reason
        )
        
        # If successful and this is a gift, store the alias
        if success and category == 'powers' and subcategory == 'gift' and hasattr(self.caller, 'set_gift_alias'):
            try:
                if original_stat_name and original_stat_name.lower() != stat_name.lower():
                    self.caller.set_gift_alias(stat_name, original_stat_name, rating)
                    logger.log_info(f"Set gift alias for {stat_name}: {original_stat_name}")
            except Exception as e:
                logger.log_err(f"Error setting gift alias: {str(e)}")
                # Don't show this error to the user as it's not critical
        
        self.caller.msg(message)
    
    @transaction.atomic
    def force_weekly_xp(self):
        """Force weekly XP distribution (staff only)."""
        if not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to force weekly XP distribution.")
            return
            
        eligible_count, total_xp, report = check_weekly_xp_eligibility()
        
        self.caller.msg(report)
        
        if not self.args or self.args.lower() != "confirm":
            self.caller.msg("\nTo actually distribute XP, use: +xp/forceweekly confirm")
            return
            
        # Process the weekly XP distribution
        from evennia.objects.models import ObjectDB
        characters = ObjectDB.objects.filter(
            db_typeclass_path__contains='typeclasses.characters.Character'
        )
        
        xp_amount = Decimal('4.00')
        distributed_count = 0
        
        for char in characters:
            try:
                # Skip if character is staff
                if hasattr(char, 'check_permstring') and char.check_permstring("builders"):
                    continue
                    
                # Get character's XP data
                xp_data = None
                if hasattr(char, 'db') and hasattr(char.db, 'xp'):
                    xp_data = char.db.xp
                if not xp_data:
                    continue
                    
                # Check scenes this week
                scenes_this_week = xp_data.get('scenes_this_week', 0)
                if scenes_this_week <= 0:
                    continue
                    
                # Award XP
                char.db.xp['total'] = Decimal(str(char.db.xp.get('total', 0))) + xp_amount
                char.db.xp['current'] = Decimal(str(char.db.xp.get('current', 0))) + xp_amount
                char.db.xp['ic_xp'] = Decimal(str(char.db.xp.get('ic_xp', 0))) + xp_amount
                
                # Log the award
                log_entry = {
                    'type': 'receive',
                    'amount': float(xp_amount),
                    'reason': 'Weekly Activity',
                    'timestamp': datetime.now().isoformat()
                }
                
                if 'spends' not in char.db.xp:
                    char.db.xp['spends'] = []
                char.db.xp['spends'].insert(0, log_entry)
                
                # Reset scene count
                char.db.xp['scenes_this_week'] = 0
                
                # Update the counter
                distributed_count += 1
                
                # Notify the character if they're online
                if hasattr(char, 'msg') and char.sessions.all():
                    char.msg(f"You have received {xp_amount} XP for weekly activity.")
                    
            except Exception as e:
                logger.log_err(f"Error processing weekly XP for {char.key}: {str(e)}")
                
        self.caller.msg(f"Weekly XP distribution complete! {distributed_count} characters received {xp_amount} XP each.")
    
    @transaction.atomic
    def staff_spend_xp(self):
        """Spend XP on behalf of a character (staff only)."""
        if not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to spend XP on behalf of others.")
            return
            
        if not self.args:
            self.caller.msg("Usage: +xp/staffspend <character>/<stat> <rating> = <reason>")
            return
            
        # Split the argument into target_info and reason
        if "=" in self.args:
            target_info, reason = self.args.split("=", 1)
            reason = reason.strip()
            if not reason:
                reason = "Staff Spend"
        else:
            target_info = self.args
            reason = "Staff Spend"
            
        # Split target_info into character name and stat info
        if "/" not in target_info:
            self.caller.msg("Usage: +xp/staffspend <character>/<stat> <rating> = <reason>")
            return
            
        name, stat_info = target_info.split("/", 1)
        name = name.strip()
        stat_info = stat_info.strip()
            
        # Find the target character
        target = self.caller.search(name, global_search=True)
        if not target:
            return
            
        # Parse stat info into stat name and rating
        stat_parts = stat_info.split()
        if len(stat_parts) < 2:
            self.caller.msg("You must specify both a stat name and rating.")
            return
            
        stat_name = " ".join(stat_parts[:-1])
        try:
            rating = int(stat_parts[-1])
        except ValueError:
            self.caller.msg("Rating must be a number.")
            return
            
        # Store the original stat name for gift aliases
        original_stat_name = stat_name
            
        # Determine stat category
        category, subcategory = _determine_stat_category(stat_name)
        if not category or not subcategory:
            self.caller.msg(f"Could not determine stat category for '{stat_name}'.")
            return
            
        # Special handling for secondary abilities and proper case
        if category == 'secondary_abilities':
            from world.wod20th.utils.xp_utils import proper_title_case
            stat_name = proper_title_case(stat_name)
            original_stat_name = stat_name  # Update original name to match
            
        # For gifts, get the canonical name
        canonical_name = None
        if category == 'powers' and subcategory == 'gift':
            from world.wod20th.models import Stat
            from django.db.models import Q
            
            # Try to find the gift by name or alias
            gift = Stat.objects.filter(
                Q(name__iexact=stat_name) | Q(gift_alias__icontains=stat_name),
                category='powers',
                stat_type='gift'
            ).first()
            
            if gift:
                canonical_name = gift.name
                logger.log_info(f"Using canonical gift name: {canonical_name} for {stat_name}")
                # Store original to use as alias
                if stat_name.lower() != canonical_name.lower():
                    logger.log_info(f"Will set alias {stat_name} -> {canonical_name}")
                
            # Update the stat_name to use canonical name if found
            if canonical_name:
                stat_name = canonical_name
                
        # Format the reason
        staff_reason = f"Staff Spend: {self.caller.name} - {reason}"
            
        # Process the spend as a staff-approved spend
        success, message, cost = process_xp_spend(
            target, stat_name, rating, category, subcategory, 
            reason=staff_reason, is_staff_spend=True
        )
            
        # Report the result
        if success:
            self.caller.msg(f"Successfully set {target.name}'s {stat_name} to {rating}. Cost: {cost} XP.")
            target.msg(f"{self.caller.name} has set your {stat_name} to {rating}. Cost: {cost} XP.")
            
            # Set the gift alias if this was a gift and we found a canonical name
            if success and category == 'powers' and subcategory == 'gift' and canonical_name and hasattr(target, 'set_gift_alias'):
                try:
                    if original_stat_name.lower() != canonical_name.lower():
                        # Ensure the alias is a string, not a list or None
                        alias_to_use = original_stat_name if original_stat_name else stat_name
                        if isinstance(alias_to_use, list):
                            # If it's a list, use the first element or a joined string
                            if alias_to_use:
                                alias_to_use = alias_to_use[0] if len(alias_to_use) == 1 else " ".join(alias_to_use)
                            else:
                                alias_to_use = canonical_name  # Fallback if empty list
                        
                        target.set_gift_alias(canonical_name, alias_to_use, rating)
                        logger.log_info(f"Set gift alias for {canonical_name}: {alias_to_use}")
                except Exception as e:
                    logger.log_err(f"Error setting gift alias: {str(e)}")
                    self.caller.msg(f"Note: Gift was set successfully but there was an error setting the alias: {str(e)}")
        else:
            self.caller.msg(f"Error: {message}")
    
    @transaction.atomic
    def approve_xp(self):
        """Record XP spend without cost (staff only)."""
        if not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to approve XP spends.")
            return
            
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +xp/approve <name>/<amount>=<reason>")
            return
            
        target_info, reason = self.args.split("=", 1)
        reason = reason.strip()
            
        if "/" not in target_info:
            self.caller.msg("Usage: +xp/approve <name>/<amount>=<reason>")
            return
            
        name, amount_str = target_info.split("/", 1)
        name = name.strip()
        amount_str = amount_str.strip()
            
        # Validate the input is a proper decimal number
        try:
            # First clean up the input, handling commas and spaces
            amount_str = amount_str.replace(',', '.').replace(' ', '')
            # Ensure it's a valid decimal format
            if not re.match(r'^-?\d+(\.\d+)?$', amount_str):
                self.caller.msg("Amount must be a valid number (e.g. 5 or 5.5).")
                return
                
            amount = Decimal(amount_str)
            if amount <= 0:
                self.caller.msg("Amount must be positive.")
                return
        except (ValueError, decimal.InvalidOperation):
            self.caller.msg("Amount must be a valid number (e.g. 5 or 5.5).")
            return
            
        target = self.caller.search(name, global_search=True)
        if not target:
            return
            
        # Check if target has XP data
        if not hasattr(target.db, 'xp') or not target.db.xp:
            target.db.xp = {
                'total': Decimal('0.00'),
                'current': Decimal('0.00'),
                'spent': Decimal('0.00'),
                'ic_xp': Decimal('0.00'),
                'spends': []
            }
            
        # Ensure target has enough XP to spend
        current_xp = Decimal(str(target.db.xp.get('current', 0)))
        if current_xp < amount:
            self.caller.msg(f"{target.name} only has {current_xp} XP. Cannot approve a spend of {amount} XP.")
            return
            
        # Update XP values
        target.db.xp['current'] = current_xp - amount
        target.db.xp['spent'] = Decimal(str(target.db.xp.get('spent', 0))) + amount
            
        # Log the approved spend
        log_entry = {
            'type': 'approve',
            'amount': float(amount),
            'reason': reason,
            'staff_name': self.caller.name,
            'timestamp': datetime.now().isoformat()
        }
            
        if 'spends' not in target.db.xp:
            target.db.xp['spends'] = []
        target.db.xp['spends'].insert(0, log_entry)
            
        self.caller.msg(f"Approved {amount} XP spend for {target.name}. Reason: {reason}")
        target.msg(f"{self.caller.name} has approved an XP spend of {amount} XP for: {reason}")
    
    @transaction.atomic
    def refund_xp(self):
        """Refund XP to a character (staff only)."""
        if not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to refund XP.")
            return
            
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +xp/refund <name>/<amount>=<reason>")
            return
            
        target_info, reason = self.args.split("=", 1)
        reason = reason.strip()
            
        if "/" not in target_info:
            self.caller.msg("Usage: +xp/refund <name>/<amount>=<reason>")
            return
            
        name, amount_str = target_info.split("/", 1)
        name = name.strip()
        amount_str = amount_str.strip()
            
        # Validate the input is a proper decimal number
        try:
            # First clean up the input, handling commas and spaces
            amount_str = amount_str.replace(',', '.').replace(' ', '')
            # Ensure it's a valid decimal format
            if not re.match(r'^-?\d+(\.\d+)?$', amount_str):
                self.caller.msg("Amount must be a valid number (e.g. 5 or 5.5).")
                return
                
            amount = Decimal(amount_str)
            if amount <= 0:
                self.caller.msg("Amount must be positive.")
                return
        except (ValueError, decimal.InvalidOperation):
            self.caller.msg("Amount must be a valid number (e.g. 5 or 5.5).")
            return
            
        target = self.caller.search(name, global_search=True)
        if not target:
            return
            
        # Check if target has XP data
        if not hasattr(target.db, 'xp') or not target.db.xp:
            target.db.xp = {
                'total': Decimal('0.00'),
                'current': Decimal('0.00'),
                'spent': Decimal('0.00'),
                'ic_xp': Decimal('0.00'),
                'spends': []
            }
            
        # Update XP values
        target.db.xp['current'] = Decimal(str(target.db.xp.get('current', 0))) + amount
        target.db.xp['spent'] = max(Decimal('0.00'), Decimal(str(target.db.xp.get('spent', 0))) - amount)
            
        # Log the refund
        log_entry = {
            'type': 'refund',
            'amount': float(amount),
            'reason': reason,
            'staff_name': self.caller.name,
            'timestamp': datetime.now().isoformat()
        }
            
        if 'spends' not in target.db.xp:
            target.db.xp['spends'] = []
        target.db.xp['spends'].insert(0, log_entry)
            
        self.caller.msg(f"Refunded {amount} XP to {target.name}. Reason: {reason}")
        target.msg(f"{self.caller.name} has refunded {amount} XP to you. Reason: {reason}")
    
    def fix_stats(self):
        """Fix a character's stats structure (staff only)."""
        if not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to fix character stats.")
            return
            
        if not self.args:
            self.caller.msg("Usage: +xp/fixstats <name>")
            return
            
        target = self.caller.search(self.args, global_search=True)
        if not target:
            return
            
        # Make sure character has stats
        if not hasattr(target.db, 'stats') or not target.db.stats:
            self.caller.msg(f"{target.name} has no stats to fix.")
            return
            
        # Fix powers structure
        changes_made = fix_powers(target)
            
        if changes_made:
            self.caller.msg(f"Fixed power structure for {target.name}.")
        else:
            self.caller.msg(f"No stat structure issues found for {target.name}.")
    
    def fix_xp_data(self):
        """Fix a character's XP data structure (staff only)."""
        if not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to fix XP data.")
            return
            
        if not self.args:
            self.caller.msg("Usage: +xp/fixdata <name>")
            return
            
        target = self.caller.search(self.args, global_search=True)
        if not target:
            return
            
        # Check and fix XP data structure
        if not hasattr(target.db, 'xp') or not target.db.xp:
            target.db.xp = {
                'total': Decimal('0.00'),
                'current': Decimal('0.00'),
                'spent': Decimal('0.00'),
                'ic_xp': Decimal('0.00'),
                'monthly_spent': Decimal('0.00'),
                'last_reset': datetime.now().isoformat(),
                'spends': [],
                'last_scene': None,
                'scenes_this_week': 0
            }
            self.caller.msg(f"Created new XP data structure for {target.name}.")
            return
            
        # Ensure all needed fields exist
        fixed = False
        xp_data = target.db.xp
            
        # Convert string decimals to actual Decimal objects
        for key in ['total', 'current', 'spent', 'ic_xp', 'monthly_spent']:
            if key not in xp_data:
                xp_data[key] = Decimal('0.00')
                fixed = True
            elif isinstance(xp_data[key], str):
                try:
                    xp_data[key] = Decimal(xp_data[key])
                    fixed = True
                except:
                    xp_data[key] = Decimal('0.00')
                    fixed = True
                    
        # Ensure other fields exist
        if 'spends' not in xp_data:
            xp_data['spends'] = []
            fixed = True
            
        if 'last_reset' not in xp_data:
            xp_data['last_reset'] = datetime.now().isoformat()
            fixed = True
            
        if 'scenes_this_week' not in xp_data:
            xp_data['scenes_this_week'] = 0
            fixed = True
            
        if 'last_scene' not in xp_data:
            xp_data['last_scene'] = None
            fixed = True
            
        # Update the character's XP data
        target.db.xp = xp_data
            
        if fixed:
            self.caller.msg(f"Fixed XP data structure for {target.name}.")
        else:
            self.caller.msg(f"No XP data issues found for {target.name}.")