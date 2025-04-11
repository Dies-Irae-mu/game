from evennia import default_cmds
from evennia.utils.search import search_object
from evennia.utils.evtable import EvTable
from datetime import datetime
from decimal import Decimal, ROUND_DOWN, InvalidOperation
from typeclasses.characters import Character
from django.db import transaction
from evennia.utils import logger
from django.db.models import Q
from world.wod20th.utils.stat_mappings import MERIT_VALUES, RITE_VALUES, FLAW_VALUES, MERIT_CATEGORIES, REQUIRED_INSTANCES, ARTS, REALMS
from world.wod20th.utils.sheet_constants import POWERS
from world.wod20th.utils.xp_utils import process_xp_spend, _determine_stat_category, validate_xp_purchase
from world.wod20th.utils.vampire_utils import validate_discipline_purchase
from world.wod20th.utils.mage_utils import validate_sphere_purchase

class CmdXP(default_cmds.MuxCommand):
    """
    View and manage experience points.
    
    Usage:
      +xp                     - View your XP
      +xp <n>             - View another character's XP (Staff only)
      +xp/desc <n>        - View detailed XP history (Staff only)
      +xp/sub <n>/<amount>=<reason> - Remove XP from character (Staff only)
      +xp/init               - Initialize scene tracking
      +xp/endscene          - Manually end current scene (only if scene doesn't end automatically, remove in future)
      +xp/add <n>=<amt>   - Add XP to a character (Staff only)
      +xp/spend <n> <rating>=<reason> - Spend XP (Must be in OOC area)
      +xp/forceweekly       - Force weekly XP distribution (Staff only)
      +xp/staffspend <n>/<stat> <rating>=<reason> - Spend XP on behalf of a character (Staff only)
      +xp/fixstats <n>   - Fix a character's stats structure (Staff only)
      +xp/fixdata <n>    - Fix a character's XP data structure (Staff only)
      
    Examples:
      +xp/spend Strength 3=Getting stronger
      +xp/spend Potence 2=Learning from mentor
      +xp/spend Resources 2=Business success
      +xp/staffspend Bob/Strength 3=Staff correction
      +xp/sub Bob/5=Correcting XP error
      +xp/staffspend ryan/<FLAW NAME>=Flaw Buyoff
      +xp/fixdata Bob       - Fix Bob's XP data structure
    """
    
    key = "+xp"
    aliases = ["xp"]
    locks = "cmd:all()"
    help_category = "XP Commands"
    
    def __init__(self, *args, **kwargs):
        """Initialize with gift_alias_used attribute."""
        super().__init__(*args, **kwargs)
        # Initialize gift_alias_used for storing the alias used in gift commands
        self.gift_alias_used = None
    
    def func(self):
        """Execute command"""
        if not self.args and not self.switches:
            # Display own XP info
            # First fix any power issues
            self.fix_powers(self.caller)
            self._display_xp(self.caller)
            return

        # Process switches
        if self.switches:
            if "add" in self.switches:
                # Only staff can add XP
                if not self.caller.check_permstring("builders"):
                    self.caller.msg("You don't have permission to add XP.")
                    return
                    
                try:
                    from decimal import Decimal, ROUND_DOWN, InvalidOperation
                    # split the args
                    target_name, amount = self.args.split("=", 1)
                    # search for the target
                    target = search_object(target_name.strip(), 
                                        typeclass='typeclasses.characters.Character',
                                        exact=True)
                    if not target:
                        # try non-exact search if exact fails
                        target = search_object(target_name.strip(),
                                            typeclass='typeclasses.characters.Character')
                    
                    # get first match if any found
                    target = target[0] if target else None
                    
                    if not target:
                        self.caller.msg(f"Character '{target_name}' not found.")
                        return
                        
                    # Fix any power issues before proceeding
                    self.fix_powers(target)

                    # amount validation
                    try:
                        xp_amount = Decimal(amount).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                        if xp_amount <= 0:
                            raise ValueError
                    except (ValueError, InvalidOperation):
                        self.caller.msg("Amount must be a positive number with up to 2 decimal places.")
                        return
                        
                    if target.add_xp(xp_amount, "Staff Award", self.caller):
                        self.caller.msg(f"Added {xp_amount} XP to {target.name}")
                        target.msg(f"You received {xp_amount} XP from {self.caller.name}")
                        # Display updated XP info
                        self._display_xp(target)
                    else:
                        self.caller.msg("Failed to add XP.")
                        
                except ValueError:
                    self.caller.msg("Usage: +xp/add <name>=<amount>")
                    return
                return

            if "sub" in self.switches:
                from decimal import Decimal, ROUND_DOWN
                if not self.caller.check_permstring("builders"):
                    self.caller.msg("You don't have permission to remove XP.")
                    return
                    
                try:
                    # Parse input
                    if "=" not in self.args:
                        self.caller.msg("Usage: +xp/sub <name>/<amount>=<reason>")
                        return
                        
                    target_info, reason = self.args.split("=", 1)
                    reason = reason.strip()
                    
                    # Parse target info
                    if "/" not in target_info:
                        self.caller.msg("Must specify both character name and amount.")
                        return
                    target_name, amount = target_info.split("/", 1)
                    
                    # Find target character
                    target = search_object(target_name.strip(), 
                                        typeclass='typeclasses.characters.Character')
                    if not target:
                        self.caller.msg(f"Character '{target_name}' not found.")
                        return
                    target = target[0]
                    
                    # Validate XP amount
                    try:
                        xp_amount = Decimal(amount).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                        if xp_amount <= 0:
                            raise ValueError
                    except (ValueError, InvalidOperation):
                        self.caller.msg("Amount must be a positive number.")
                        return

                    if target.db.xp['current'] < xp_amount:
                        self.caller.msg(f"Character only has {target.db.xp['current']} XP available.")
                        return

                    # Remove XP
                    target.db.xp['total'] -= xp_amount
                    target.db.xp['current'] -= xp_amount
                    
                    # Log the removal
                    removal = {
                        'type': 'spend',
                        'amount': float(xp_amount),
                        'reason': reason,
                        'staff_name': self.caller.name,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    if 'spends' not in target.db.xp:
                        target.db.xp['spends'] = []
                    target.db.xp['spends'].insert(0, removal)
                    
                    # Notify staff and target
                    self.caller.msg(f"Removed {xp_amount} XP from {target.name} for {reason}")
                    target.msg(f"{xp_amount} XP was removed by {self.caller.name} for {reason}")
                    self._display_xp(target)
                    
                except ValueError as e:
                    self.caller.msg("Usage: +xp/sub <name>/<amount>=<reason>")
                    self.caller.msg("Example: +xp/sub Bob/5.00=Correcting error")
                return

            if "init" in self.switches:
                self.caller.init_scene_data()
                self.caller.msg("Scene tracking initialized.")
                return

            if "endscene" in self.switches:
                caller = self.caller
                if not caller.db.scene_data or not caller.db.scene_data['current_scene']:
                    caller.msg("You don't have an active scene to end.")
                    return

                # Get all players in the room
                players_in_room = [
                    obj for obj in caller.location.contents 
                    if (hasattr(obj, 'has_account') and 
                        obj.has_account and 
                        obj.db.in_umbra == caller.db.in_umbra)
                ]

                caller.msg("\n|wEnding scene for all participants...|n")

                # End scene for each player
                for player in players_in_room:
                    if (hasattr(player.db, 'scene_data') and 
                        player.db.scene_data and 
                        player.db.scene_data['current_scene']):
                        player.end_scene()
                        player.msg("\n|wScene ended by {}.|n".format(caller.name))
                        self._display_xp(player)

                # Announce scene end to room
                caller.location.msg_contents(
                    "\n|w{} has ended the scene.|n".format(caller.name),
                    exclude=[caller]
                )
                return

            if "spend" in self.switches:
                # check if in OOC area
                if not (self.caller.location and 
                       hasattr(self.caller.location, 'db') and 
                       self.caller.location.db.roomtype == 'OOC Area'):
                    self.caller.msg("You must be in an OOC area to spend XP.")
                    return

                try:
                    logger.log_info(f"{self.caller.name}: Processing XP spend command")
                    
                    # Fix any power issues before proceeding
                    self.fix_powers(self.caller)
                    logger.log_info(f"{self.caller.name}: Fixed powers")
                    
                    # Fix any secondary abilities issues
                    if hasattr(self.caller, 'fix_secondary_abilities'):
                        self.caller.fix_secondary_abilities()
                        logger.log_info(f"{self.caller.name}: Fixed secondary abilities")

                    # Parse input
                    if "=" not in self.args:
                        self.caller.msg("Usage: +xp/spend <n> <rating>=<reason>")
                        return
                        
                    stat_info, reason = self.args.split("=", 1)
                    stat_info = stat_info.strip()
                    reason = reason.strip()
                    logger.log_info(f"{self.caller.name}: Parsed input - stat_info: {stat_info}, reason: {reason}")

                    # Parse stat info
                    stat_parts = stat_info.split()
                    if len(stat_parts) < 2:
                        self.caller.msg("Usage: +xp/spend <n> <rating>=<reason>")
                        return
                    
                    # Get new rating
                    try:
                        new_rating = int(stat_parts[-1])
                        if new_rating < 0:
                            self.caller.msg("Rating must be a positive number.")
                            return
                    except ValueError:
                        self.caller.msg("Rating must be a number.")
                        return
                        
                    stat_name = " ".join(stat_parts[:-1])
                    logger.log_info(f"{self.caller.name}: Parsed stat - name: {stat_name}, rating: {new_rating}")

                    # Early check for merits and flaws
                    stat_name_lower = stat_name.lower()
                    if stat_name_lower in [merit.lower() for merit in MERIT_VALUES.keys()]:
                        self.caller.msg("Merits require staff approval. Please use +request to submit a request.")
                        return
                    if stat_name_lower in [flaw.lower() for flaw in FLAW_VALUES.keys()]:
                        self.caller.msg("Flaws require staff approval. Please use +request to submit a request.")
                        return

                    # Define lists for validation
                    PURCHASABLE_DISCIPLINES = ['Potence', 'Fortitude', 'Celerity', 'Auspex', 'Obfuscate']
                    AUTO_SPEND_BACKGROUNDS = {
                        'Resources': 2, 'Contacts': 2, 'Allies': 2, 'Backup': 2,
                        'Herd': 2, 'Library': 2, 'Kinfolk': 2, 'Spirit Heritage': 2,
                        'Paranormal Tools': 2, 'Servants': 2, 'Armory': 2, 'Retinue': 2,
                        'Spies': 2, 'Professional Certification': 1, 'Past Lives': 2,
                        'Dreamers': 2
                    }

                    # Determine category and subcategory
                    from world.wod20th.utils.xp_utils import _determine_stat_category, process_xp_spend
                    category, subcategory = _determine_stat_category(stat_name)
                    logger.log_info(f"{self.caller.name}: Determined category: {category}, subcategory: {subcategory}")

                    # Special handling for Kinfolk Gnosis
                    if stat_name.lower() == "gnosis":
                        # Check if this is a Kinfolk character
                        is_kinfolk = (target.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '') == 'Mortal+' and 
                                    target.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '') == 'Kinfolk')
                        
                        if is_kinfolk:
                            logger.log_info(f"Target is Kinfolk, treating Gnosis as a Merit")
                            category = "merits"
                            subcategory = "supernatural"
                    
                    if not category or not subcategory:
                        self.caller.msg(f"Could not determine stat category for '{stat_name}'.")
                        return

                    # Validation checks for various stats
                    if category == 'powers':
                        if subcategory == 'discipline':
                            # Import vampire utils for discipline validation
                            from world.wod20th.utils.vampire_utils import validate_discipline_purchase
                            can_purchase, error_msg = validate_discipline_purchase(self.caller, stat_name, new_rating, is_staff_spend=False)
                            if not can_purchase:
                                self.caller.msg(error_msg)
                                return
                        elif subcategory == 'sphere':
                            # Import mage utils for sphere validation
                            from world.wod20th.utils.mage_utils import validate_sphere_purchase
                            can_purchase, error_msg = validate_sphere_purchase(self.caller, stat_name, new_rating, is_staff_spend=False)
                            if not can_purchase:
                                self.caller.msg(error_msg)
                                return
                        elif subcategory == 'blessing':
                            self.caller.msg("Blessings require staff approval. Please use +request to submit a request.")
                            return
                        elif subcategory == 'special_advantage' and 'companion' in stat_name.lower():
                            self.caller.msg("Companion advantages require staff approval. Please use +request to submit a request.")
                            return
                        elif subcategory == 'sphere' and new_rating > 1:
                            self.caller.msg("Spheres above level 1 require staff approval. Please use +request to submit a request.")
                            return
                        elif subcategory == 'art' and new_rating > 2:
                            self.caller.msg("Arts above level 2 require staff approval. Please use +request to submit a request.")
                            return
                        elif subcategory == 'realm' and new_rating > 2:
                            self.caller.msg("Realms above level 2 require staff approval. Please use +request to submit a request.")
                            return
                        elif subcategory in ['rite', 'necromancy_ritual', 'thaum_ritual', 'sorcery', 'numina', 'charm']:
                            self.caller.msg(f"{subcategory.replace('_', ' ').title()} requires staff approval. Please use +request to submit a request.")
                            return
                        elif subcategory == 'gift' and new_rating > 1:
                            self.caller.msg("Gifts above Rank 1 require staff approval. Please use +request to submit a request.")
                            return

                    elif category == 'pools':
                        if subcategory == 'advantage' and stat_name.lower() == 'arete':
                            self.caller.msg("Arete requires staff approval. Please use +request to submit a request.")
                            return
                        elif subcategory == 'dual' and stat_name.lower() in ['gnosis', 'rage']:
                            self.caller.msg(f"{stat_name} requires staff approval. Please use +request to submit a request.")
                            return

                    elif category == 'backgrounds':
                        if stat_name not in AUTO_SPEND_BACKGROUNDS:
                            self.caller.msg(f"{stat_name} background requires staff approval. Please use +request to submit a request.")
                            return
                        if new_rating > AUTO_SPEND_BACKGROUNDS[stat_name]:
                            self.caller.msg(f"{stat_name} above {AUTO_SPEND_BACKGROUNDS[stat_name]} requires staff approval. Please use +request to submit a request.")
                            return

                    # Special handling for gifts, particularly for Kinfolk
                    if not category or not subcategory:
                        # Check if this might be a gift for Kinfolk
                        char_splat = self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
                        char_type = self.caller.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
                        
                        if char_splat == 'Mortal+' and char_type == 'Kinfolk':
                            # Try to find it as a gift in the database
                            from world.wod20th.models import Stat
                            from django.db.models import Q
                            
                            gift = Stat.objects.filter(
                                Q(name__iexact=stat_name) | Q(gift_alias__icontains=stat_name),
                                category='powers',
                                stat_type='gift'
                            ).first()
                            
                            if gift:
                                logger.log_info(f"{self.caller.name}: Found gift in database: {gift.name}")
                                category = 'powers'
                                subcategory = 'gift'
                                stat_name = gift.name  # Use the official name from the database
                    
                    if not category or not subcategory:
                        self.caller.msg(f"Invalid stat name: {stat_name}")
                        return

                    # Store the original stat name for gift aliases
                    original_stat_name = stat_name

                    # Get proper case for the stat name based on category
                    proper_stat_name = self._get_proper_stat_name(stat_name, category, subcategory)
                    logger.log_info(f"{self.caller.name}: Got proper stat name: {proper_stat_name}")
                    
                    if not proper_stat_name:
                        self.caller.msg(f"Invalid stat name: {stat_name}")
                        return

                    # Special validation for gifts
                    if category == 'powers' and subcategory == 'gift':
                        # Check if it's a rank 2 or higher gift
                        if new_rating > 1:
                            self.caller.msg("Gifts above Rank 1 require staff approval. Please use +request to submit a request.")
                            return

                    # Process the XP spend
                    success, message, cost = process_xp_spend(
                        character=self.caller,
                        stat_name=proper_stat_name,
                        new_rating=new_rating,
                        category=category,
                        subcategory=subcategory,
                        reason=reason,
                        is_staff_spend=False
                    )
                    
                    # If successful and this is a gift, store the alias
                    if success and category == 'powers' and subcategory == 'gift':
                        # Check if we have a gift_alias_used attribute set by _get_proper_stat_name
                        alias_to_use = getattr(self, 'gift_alias_used', original_stat_name)
                        
                        # If the alias is different from the canonical name, store it
                        if alias_to_use and alias_to_use.lower() != proper_stat_name.lower():
                            self.caller.set_gift_alias(proper_stat_name, alias_to_use, new_rating)
                            logger.log_info(f"Set gift alias for {proper_stat_name}: {alias_to_use}")
                    
                    self.caller.msg(message)
                    if success:
                        # Only show XP display on success
                        self._display_xp(self.caller)

                except ValueError as e:
                    logger.log_err(f"{self.caller.name}: ValueError in XP spend - {str(e)}")
                    self.caller.msg(f"Error: Invalid input - {str(e)}")
                    self.caller.msg("Usage: +xp/spend <n> <rating>=<reason>")
                except Exception as e:
                    logger.log_err(f"{self.caller.name}: Error in XP spend - {str(e)}")
                    self.caller.msg(f"Error: {str(e)}")
                    self.caller.msg("An error occurred while processing your request.")
                return

            if "desc" in self.switches:
                if not self.caller.check_permstring("builders"):
                    self.caller.msg("You don't have permission to view detailed XP history.")
                    return
                    
                target = search_object(self.args.strip(), typeclass='typeclasses.characters.Character')
                if not target:
                    self.caller.msg(f"Character '{self.args}' not found.")
                    return
                target = target[0]
                self._display_detailed_history(target)
                return

            if "forceweekly" in self.switches:
                # Only staff can force weekly XP
                if not self.caller.check_permstring("builders"):
                    self.caller.msg("You don't have permission to force weekly XP distribution.")
                    return
                    
                try:
                    from decimal import Decimal
                    # Find all character objects that:
                    # 1. Are not staff
                    # 2. Have scene data
                    # 3. Have completed at least one scene this week
                    characters = Character.objects.filter(
                        db_typeclass_path__contains='characters.Character'
                    )
                    
                    base_xp = Decimal('4.00')
                    awarded_count = 0
                    
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
                                xp_data = char.attributes.get('xp')
                                
                            if not xp_data:
                                continue

                            # Handle string XP data
                            if isinstance(xp_data, str):
                                try:
                                    # Clean up the string for evaluation
                                    cleaned_str = xp_data.replace("Decimal('", "'")
                                    cleaned_str = cleaned_str.replace("')", "'")
                                    
                                    # Try to parse the cleaned string
                                    import ast
                                    parsed_data = ast.literal_eval(cleaned_str)
                                    
                                    # Convert string values back to Decimal objects
                                    if isinstance(parsed_data, dict):
                                        for key in ['total', 'current', 'spent', 'ic_xp', 'monthly_spent']:
                                            if key in parsed_data and isinstance(parsed_data[key], str):
                                                parsed_data[key] = Decimal(parsed_data[key])
                                        xp_data = parsed_data
                                    else:
                                        continue
                                except Exception as e:
                                    logger.log_err(f"Error parsing XP data for {char.key}: {str(e)}")
                                    continue
                            
                            # Check scenes this week
                            scenes_this_week = xp_data.get('scenes_this_week', 0)
                            if scenes_this_week > 0:
                                # Award XP if they've participated in scenes
                                xp_amount = base_xp
                                
                                # Update XP values
                                current = Decimal(str(xp_data.get('current', '0.00')))
                                total = Decimal(str(xp_data.get('total', '0.00')))
                                ic_xp = Decimal(str(xp_data.get('ic_xp', '0.00')))
                                
                                xp_data['total'] = total + xp_amount
                                xp_data['current'] = current + xp_amount
                                xp_data['ic_xp'] = ic_xp + xp_amount
                                
                                # Log the award
                                award = {
                                    'type': 'receive',
                                    'amount': float(xp_amount),
                                    'reason': "Weekly Activity",
                                    'approved_by': self.caller.key,
                                    'timestamp': datetime.now().isoformat()
                                }
                                
                                if 'spends' not in xp_data:
                                    xp_data['spends'] = []
                                xp_data['spends'].insert(0, award)
                                
                                # Reset scenes_this_week after awarding XP
                                xp_data['scenes_this_week'] = 0
                                
                                # Update both locations to ensure consistency
                                if hasattr(char, 'db') and hasattr(char.db, 'xp'):
                                    char.db.xp = xp_data
                                char.attributes.add('xp', xp_data)
                                
                                self.caller.msg(f"Awarded {xp_amount} XP to {char.name}")
                                char.msg(f"You received {xp_amount} XP for Weekly Activity.")
                                awarded_count += 1
                                
                        except Exception as e:
                            self.caller.msg(f"Error processing {char.name}: {str(e)}")
                            continue
                    
                    self.caller.msg(f"\nWeekly XP distribution completed. Awarded XP to {awarded_count} active characters.")
                    
                except Exception as e:
                    self.caller.msg(f"Error during XP distribution: {str(e)}")
                    return

            if "staffspend" in self.switches:
                # Only staff can force spend XP
                if not self.caller.check_permstring("builders"):
                    self.caller.msg("You don't have permission to force spend XP.")
                    return
                    
                try:
                    logger.log_info(f"Processing staffspend command for {self.caller.name}")
                    
                    # Parse input
                    if "=" not in self.args:
                        self.caller.msg("Usage: +xp/staffspend <n>/<stat> <rating>=<reason>")
                        return
                        
                    target_info, reason = self.args.split("=", 1)
                    reason = reason.strip()
                    logger.log_info(f"Parsed input - target_info: {target_info}, reason: {reason}")
                    
                    # Parse target info
                    if "/" not in target_info:
                        self.caller.msg("Must specify both character name and stat.")
                        return
                    target_name, stat_info = target_info.split("/", 1)
                    logger.log_info(f"Split target info - name: {target_name}, stat_info: {stat_info}")
                    
                    # Find target character
                    target = search_object(target_name.strip(), 
                                        typeclass='typeclasses.characters.Character')
                    if not target:
                        self.caller.msg(f"Character '{target_name}' not found.")
                        return
                    target = target[0]
                    
                    # Parse stat info
                    stat_parts = stat_info.strip().split()
                    if len(stat_parts) < 2:
                        self.caller.msg("You must specify both a stat name and rating.")
                        return
                        
                    try:
                        new_rating = int(stat_parts[-1])
                        if new_rating < 0:
                            self.caller.msg("Rating must be a positive number.")
                            return
                    except ValueError:
                        self.caller.msg("Rating must be a number.")
                        return
                        
                    stat_name = " ".join(stat_parts[:-1])
                    logger.log_info(f"Parsed stat - name: {stat_name}, rating: {new_rating}")

                    # Determine category and subcategory
                    from world.wod20th.utils.xp_utils import _determine_stat_category
                    category, subcategory = _determine_stat_category(stat_name)
                    logger.log_info(f"{self.caller.name}: Determined category: {category}, subcategory: {subcategory}")
                    
                    # Special handling for Kinfolk Gnosis
                    if stat_name.lower() == "gnosis":
                        # Check if the target is a Kinfolk
                        splat = target.get_stat('other', 'splat', 'Splat', temp=False)
                        if splat == 'Mortal+':
                            char_type = target.get_stat('identity', 'lineage', 'Type', temp=False)
                            if char_type == 'Kinfolk':
                                logger.log_info(f"Target is Kinfolk, treating Gnosis as a Merit")
                                # Very important: Change the category and subcategory for a Kinfolk
                                category = 'merits'
                                subcategory = 'supernatural'
                                logger.log_info(f"Updated category to {category}, subcategory to {subcategory}")
                                
                                # Get current rating of the Gnosis merit
                                current_rating = target.get_stat(category, subcategory, stat_name, temp=False) or 0
                                logger.log_info(f"Current rating: {current_rating}")
                                
                                # Only proceed if there's an actual increase in rating
                                if new_rating <= current_rating:
                                    self.caller.msg(f"No increase needed. Current rating is already {current_rating}.")
                                    return
                                
                                # Calculate merit cost (5 XP per dot)
                                cost = (new_rating - current_rating) * 5
                                
                                # Check if character has enough XP
                                if target.db.xp['current'] < cost:
                                    self.caller.msg(f"Not enough XP. Cost: {cost}, Available: {target.db.xp['current']}")
                                    return
                                
                                # Calculate the Gnosis pool value (merit rating - 4)
                                gnosis_pool = max(0, new_rating - 4)
                                
                                # Update the merit
                                target.set_stat('merits', 'supernatural', 'Gnosis', new_rating, temp=False)
                                target.set_stat('merits', 'supernatural', 'Gnosis', new_rating, temp=True)
                                
                                # Update the pool
                                target.set_stat('pools', 'dual', 'Gnosis', gnosis_pool, temp=False)
                                target.set_stat('pools', 'dual', 'Gnosis', gnosis_pool, temp=True)
                                
                                # Deduct XP
                                target.db.xp['current'] -= cost
                                target.db.xp['spent'] += cost
                                
                                # Log the spend with stat information
                                spend_entry = {
                                    'type': 'spend',
                                    'amount': float(cost),
                                    'stat_name': 'Gnosis (Merit)',
                                    'previous_rating': current_rating,
                                    'new_rating': new_rating,
                                    'reason': reason,
                                    'timestamp': datetime.now().isoformat()
                                }
                                
                                if 'spends' not in target.db.xp:
                                    target.db.xp['spends'] = []
                                target.db.xp['spends'].insert(0, spend_entry)
                                
                                # Report success
                                self.caller.msg(f"Successfully set {target.name}'s Gnosis merit to {new_rating} and Gnosis pool to {gnosis_pool}. Cost: {cost} XP.")
                                target.msg(f"{self.caller.name} has set your Gnosis merit to {new_rating} and Gnosis pool to {gnosis_pool}. Cost: {cost} XP.")
                                
                                # No need to continue with the regular process_xp_spend function
                                return
                    
                    # Fix case-sensitivity: Get proper case for the stat name
                    if hasattr(target, 'get_proper_stat_name'):
                        proper_name = target.get_proper_stat_name(category, subcategory, stat_name)
                        if proper_name != stat_name:
                            logger.log_info(f"Found proper stat name: {proper_name} (was: {stat_name})")
                            stat_name = proper_name
                    
                    # Current rating
                    current_rating = target.get_stat(category, subcategory, stat_name, temp=False) or 0
                    logger.log_info(f"Current rating: {current_rating}")

                    # Calculate cost using the same logic as regular XP spend
                    from world.wod20th.utils.xp_utils import calculate_xp_cost
                    cost, _ = calculate_xp_cost(
                        target, stat_name, new_rating, category, subcategory, current_rating
                    )
                    
                    if cost == 0:
                        self.caller.msg("Invalid stat or no increase needed.")
                        return

                    # Check if we have enough XP
                    if target.db.xp['current'] < cost:
                        self.caller.msg(f"Not enough XP. Cost: {cost}, Available: {target.db.xp['current']}")
                        return

                    # Process the spend
                    from world.wod20th.utils.xp_utils import process_xp_spend
                    success, message, final_cost = process_xp_spend(
                        character=target,
                        stat_name=stat_name,
                        new_rating=new_rating,
                        category=category,
                        subcategory=subcategory,
                        reason=f"Staff Spend: {reason}",
                        is_staff_spend=True
                    )

                    if success:
                        self.caller.msg(f"Successfully set {target.name}'s {stat_name} to {new_rating}. Cost: {final_cost} XP.")
                        target.msg(f"{self.caller.name} has set your {stat_name} to {new_rating}. Cost: {final_cost} XP.")
                        self._display_xp(target)
                    else:
                        self.caller.msg(f"Failed to process XP spend: {message}")
                    
                except Exception as e:
                    logger.log_err(f"Error in staffspend: {str(e)}")
                    self.caller.msg(f"Error: {str(e)}")
                    self.caller.msg("Usage: +xp/staffspend <n>/<stat> <rating>=<reason>")
                return

            if "fixstats" in self.switches:
                # Only staff can fix stats
                if not self.caller.check_permstring("builders"):
                    self.caller.msg("You don't have permission to fix stats.")
                    return
                    
                try:
                    # Parse input
                    target_name = self.args.strip()
                    if not target_name:
                        self.caller.msg("Usage: +xp/fixstats <name>")
                        return
                        
                    # Find target character
                    target = search_object(target_name, typeclass='typeclasses.characters.Character')
                    if not target:
                        self.caller.msg(f"Character '{target_name}' not found.")
                        return
                    target = target[0]
                    
                    # Fix stats
                    powers_fixed = self.fix_powers(target)
                    
                    # Fix secondary abilities
                    secondary_fixed = False
                    if hasattr(target, 'fix_secondary_abilities'):
                        secondary_fixed = target.fix_secondary_abilities()
                    
                    if powers_fixed or secondary_fixed:
                        self.caller.msg(f"Stats fixed for {target.name}")
                    else:
                        self.caller.msg(f"No stats needed fixing for {target.name}")
                    
                    self._display_xp(target)
                    
                except ValueError as e:
                    self.caller.msg(f"Error: Invalid input - {str(e)}")
                    self.caller.msg("Usage: +xp/fixstats <name>")
                except Exception as e:
                    self.caller.msg(f"Error: {str(e)}")
                    self.caller.msg("An error occurred while processing your request.")
                return

            if "fixdata" in self.switches:
                # Only staff can fix XP data
                if not self.caller.check_permstring("builders"):
                    self.caller.msg("You don't have permission to fix XP data.")
                    return
                    
                try:
                    from decimal import Decimal, ROUND_DOWN, InvalidOperation
                    # Parse input
                    target_name = self.args.strip()
                    if not target_name:
                        self.caller.msg("Usage: +xp/fixdata <name>")
                        return
                        
                    # Find target character
                    target = search_object(target_name, typeclass='typeclasses.characters.Character')
                    if not target:
                        self.caller.msg(f"Character '{target_name}' not found.")
                        return
                    target = target[0]
                    
                    # Get current XP data
                    old_xp = target.attributes.get('xp')
                    if not old_xp:
                        self.caller.msg(f"No XP data found for {target.name}")
                        return

                    # Handle case where XP data is stored as a string
                    if isinstance(old_xp, str):
                        try:
                            # First try to clean up the string for evaluation
                            import ast
                            
                            # Replace Decimal objects with their string values
                            cleaned_str = old_xp.replace("Decimal('", "'")
                            cleaned_str = cleaned_str.replace("')", "'")
                            
                            # Try to parse the cleaned string
                            parsed_data = ast.literal_eval(cleaned_str)
                            
                            # Convert string values back to Decimal objects
                            if isinstance(parsed_data, dict):
                                for key in ['total', 'current', 'spent', 'ic_xp', 'monthly_spent']:
                                    if key in parsed_data and isinstance(parsed_data[key], str):
                                        parsed_data[key] = Decimal(parsed_data[key])
                                old_xp = parsed_data
                            else:
                                # If parsing fails, initialize new XP data
                                self.caller.msg(f"Could not parse XP data string. Initializing new XP data for {target.name}")
                                old_xp = {
                                    'total': Decimal('0.00'),
                                    'current': Decimal('0.00'),
                                    'spent': Decimal('0.00'),
                                    'ic_xp': Decimal('0.00'),
                                    'monthly_spent': Decimal('0.00'),
                                    'spends': [],
                                    'last_scene': None,
                                    'scenes_this_week': 0
                                }
                        except Exception as e:
                            logger.log_err(f"Error parsing XP data string: {str(e)}")
                            self.caller.msg(f"Error parsing XP data string: {str(e)}")
                            # Initialize new XP data
                            old_xp = {
                                'total': Decimal('0.00'),
                                'current': Decimal('0.00'),
                                'spent': Decimal('0.00'),
                                'ic_xp': Decimal('0.00'),
                                'monthly_spent': Decimal('0.00'),
                                'spends': [],
                                'last_scene': None,
                                'scenes_this_week': 0
                            }
                        
                    # Create new XP data structure with proper Decimal objects
                    new_xp = {
                        'total': Decimal(str(old_xp.get('total', '0.00'))).quantize(Decimal('0.01')),
                        'current': Decimal(str(old_xp.get('current', '0.00'))).quantize(Decimal('0.01')),
                        'spent': Decimal(str(old_xp.get('spent', '0.00'))).quantize(Decimal('0.01')),
                        'ic_xp': Decimal(str(old_xp.get('ic_xp', old_xp.get('ic_earned', '0.00')))).quantize(Decimal('0.01')),
                        'monthly_spent': Decimal(str(old_xp.get('monthly_spent', '0.00'))).quantize(Decimal('0.01')),
                        'spends': [],
                        'last_scene': old_xp.get('last_scene'),
                        'scenes_this_week': old_xp.get('scenes_this_week', 0)
                    }
                    
                    # Preserve and fix spends data
                    if 'spends' in old_xp and isinstance(old_xp['spends'], list):
                        for spend in old_xp['spends']:
                            if isinstance(spend, dict):
                                # Convert amount to float if it's not already
                                if isinstance(spend.get('amount'), str):
                                    try:
                                        spend['amount'] = float(spend['amount'])
                                    except (ValueError, TypeError):
                                        spend['amount'] = 0.0
                                new_xp['spends'].append(spend)
                    
                    # Set the fixed XP data
                    target.attributes.add('xp', new_xp)
                    
                    self.caller.msg(f"Successfully fixed XP data structure for {target.name}")
                    # Display the fixed XP data
                    self._display_xp(target)
                    
                except Exception as e:
                    logger.error(f"Error fixing XP data: {str(e)}")
                    self.caller.msg(f"Error fixing XP data: {str(e)}")
                return

        # Staff viewing another character's XP
        if self.args and not self.switches:
            # Check if viewing self
            if self.args.lower() == self.caller.name.lower():
                self._display_xp(self.caller)
                return
                
            # Staff check - allow builders or higher to view others
            if not (self.caller.check_permstring("builders") or 
                   self.caller.check_permstring("admin") or 
                   self.caller.check_permstring("superuser")):
                self.caller.msg("You don't have permission to view others' XP.")
                return
                
            # Search for target character
            target = search_object(self.args.strip(), typeclass='typeclasses.characters.Character')
            if not target:
                self.caller.msg(f"Character '{self.args}' not found.")
                return
            target = target[0]  # Get first match
            
            # Display XP info
            self._display_xp(target)
            return

        # If no args and no switches, show own XP
        self._display_xp(self.caller)

    def _display_xp(self, target):
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
                    if entry['type'] == 'receive':
                        msg += f"{formatted_time} - Received {entry['amount']} XP: {entry['reason']}\n"
                    elif entry['type'] == 'spend':
                        if entry.get('flaw_buyoff'):
                            msg += f"{formatted_time} - Spent {entry['amount']} XP to buy off {entry['stat_name']} flaw\n"
                        elif 'previous_rating' in entry:
                            # This is a normal XP spend
                            msg += f"{formatted_time} - Spent {entry['amount']} XP on {entry['stat_name']} - increased from {entry['previous_rating']} to {entry['new_rating']}\n"
                        elif 'staff_name' in entry:
                            # This is an XP removal by staff
                            msg += f"{formatted_time} - XP Removed by {entry['staff_name']}: {entry['amount']} XP ({entry['reason']})\n"
                        else:
                            # Generic spend entry
                            msg += f"{formatted_time} - Spent {entry['amount']} XP on {entry['reason']}\n"
            else:
                msg += "No XP history yet.\n"
            
            # Footer
            msg += f"{'|b-|n' * total_width}"
            
            self.caller.msg(msg)

        except Exception as e:
            logger.error(f"Error displaying XP for {target.name}: {str(e)}")
            self.caller.msg("Error displaying XP information.")

    @staticmethod
    def _determine_stat_category(stat_name):
        """
        Determine the category and type of a stat based on its name.
        """
        from world.wod20th.utils.stat_mappings import (
            STAT_TYPE_TO_CATEGORY, STAT_VALIDATION,
            TALENTS, SKILLS, KNOWLEDGES,
            SECONDARY_TALENTS, SECONDARY_SKILLS, SECONDARY_KNOWLEDGES,
            UNIVERSAL_BACKGROUNDS, VAMPIRE_BACKGROUNDS, CHANGELING_BACKGROUNDS, 
            MAGE_BACKGROUNDS, TECHNOCRACY_BACKGROUNDS, TRADITIONS_BACKGROUNDS, 
            NEPHANDI_BACKGROUNDS, SHIFTER_BACKGROUNDS, SORCERER_BACKGROUNDS, KINAIN_BACKGROUNDS,
            MERIT_VALUES, RITE_VALUES, FLAW_VALUES, ARTS, REALMS,
        )
        from world.wod20th.utils.sheet_constants import (
            ABILITIES, SECONDARY_ABILITIES, BACKGROUNDS,
            POWERS, POOLS
        )

        # Convert to title case for comparison
        stat_name = stat_name.title()

        # Define attributes first - these take precedence over other categories
        physical_attrs = ['Strength', 'Dexterity', 'Stamina']
        social_attrs = ['Charisma', 'Manipulation', 'Appearance']
        mental_attrs = ['Perception', 'Intelligence', 'Wits']

        # Check attributes first
        if stat_name in physical_attrs:
            return ('attributes', 'physical')
        elif stat_name in social_attrs:
            return ('attributes', 'social')
        elif stat_name in mental_attrs:
            return ('attributes', 'mental')

        # Check standard abilities first
        if stat_name in TALENTS:
            return ('abilities', 'talent')
        elif stat_name in SKILLS:
            return ('abilities', 'skill')
        elif stat_name in KNOWLEDGES:
            return ('abilities', 'knowledge')

        # Check secondary abilities
        if stat_name in SECONDARY_TALENTS:
            return ('secondary_abilities', 'secondary_talent')
        elif stat_name in SECONDARY_SKILLS:
            return ('secondary_abilities', 'secondary_skill')
        elif stat_name in SECONDARY_KNOWLEDGES:
            return ('secondary_abilities', 'secondary_knowledge')

        # Handle instanced stats - extract base name
        base_name = stat_name
        instance = None
        if '(' in stat_name and ')' in stat_name:
            base_name = stat_name[:stat_name.find('(')].strip()
            instance = stat_name[stat_name.find('(')+1:stat_name.find(')')].strip()

        # Define vampire disciplines
        VAMPIRE_DISCIPLINES = [
            'Abombwe', 'Animalism', 'Auspex', 'Celerity', 'Chimerstry', 'Daimoinon',
            'Deimos', 'Dementation', 'Dominate', 'Fortitude', 'Kai', 'Melpominee',
            'Mortis', 'Mytherceria', 'Necromancy', 'Obeah', 'Obfuscate', 'Obtenebration',
            'Ogham', 'Potence', 'Presence', 'Protean', 'Quietus', 'Sanguinus',
            'Serpentis', 'Spiritus', 'Temporis', 'Thanatosis', 'Thaumaturgy',
            'Vicissitude', 'Visceratika'
        ]

        # Check if it's a discipline first
        if base_name in VAMPIRE_DISCIPLINES:
            return ('powers', 'discipline')

        # Special handling for Time and Nature
        if base_name.lower() in ['time', 'nature']:
            # Since this is a static method, we need to get the caller from the current command
            from evennia import search_object
            from typeclasses.characters import Character
            from evennia.commands.default.muxcommand import MuxCommand
            from evennia import Command
            
            # Get the current command instance
            import inspect
            frame = inspect.currentframe()
            while frame:
                if 'self' in frame.f_locals:
                    cmd_instance = frame.f_locals['self']
                    if isinstance(cmd_instance, (Command, MuxCommand)):
                        break
                frame = frame.f_back
            
            if frame and 'self' in frame.f_locals:
                cmd = frame.f_locals['self']
                # Get the target character
                if hasattr(cmd, 'caller'):
                    char = cmd.caller
                    # For staffspend, check if there's a target character
                    if cmd.switches and 'staffspend' in cmd.switches and cmd.args:
                        target_name = cmd.args.split('/')[0].strip()
                        target = search_object(target_name, typeclass=Character)
                        if target:
                            char = target[0]
                    
                    if char:
                        splat = char.get_stat('other', 'splat', 'Splat', temp=False)
                        char_type = char.get_stat('identity', 'lineage', 'Type', temp=False)
                        
                        if base_name.lower() == 'time':
                            if splat == 'Mage':
                                return ('powers', 'sphere')
                            elif splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain'):
                                return ('powers', 'realm')
                        elif base_name.lower() == 'nature':
                            if splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain'):
                                return ('powers', 'realm')
                            else:
                                return ('identity', 'personal')

        # Check if it's a background (case-insensitive)
        all_backgrounds = (UNIVERSAL_BACKGROUNDS + VAMPIRE_BACKGROUNDS + 
                          CHANGELING_BACKGROUNDS + MAGE_BACKGROUNDS + 
                          TECHNOCRACY_BACKGROUNDS + TRADITIONS_BACKGROUNDS + 
                          NEPHANDI_BACKGROUNDS + SHIFTER_BACKGROUNDS + 
                          SORCERER_BACKGROUNDS + KINAIN_BACKGROUNDS)
        if any(k.lower() == base_name.lower() or k.lower().replace(' ', '_') == base_name.lower() for k in all_backgrounds):
            return ('backgrounds', 'background')

        # Check if it's a merit (case-insensitive)
        if any(k.lower() == base_name.lower() for k in MERIT_VALUES.keys()):
            return ('merits', 'merit')

        # Check if it's a rite (case-insensitive)
        if any(k.lower() == base_name.lower() for k in RITE_VALUES.keys()):
            return ('powers', 'rite')

        # Check if it's a flaw (case-insensitive)
        if any(k.lower() == base_name.lower() for k in FLAW_VALUES.keys()):
            return ('flaws', 'flaw')

        # Check if it's an Art (case-insensitive)
        if base_name.lower() == 'primal':
            return ('powers', 'art')
            
        if any(art.lower() == base_name.lower() for art in ARTS):
            return ('powers', 'art')

        # Check if it's a Realm (case-insensitive)
        if base_name.lower() == 'nature':
            return ('powers', 'realm')
            
        if any(realm.lower() == base_name.lower() for realm in REALMS):
            return ('powers', 'realm')

        # Check if it's a gift in the database
        from world.wod20th.models import Stat
        from django.db.models import Q
        
        # Special handling for Mother's Touch - it's always a gift
        if stat_name.lower() == "mother's touch":
            return ('powers', 'gift')
            
        # Check for gifts in database with case-insensitive name or alias match
        gift_query = Q(stat_type='gift')
        gift = Stat.objects.filter(
            (Q(name__iexact=stat_name) | Q(gift_alias__icontains=stat_name)),
            category='powers',
            stat_type='gift'
        ).first()
        
        if gift:
            return ('powers', 'gift')
        
        # Check for pool stats
        pool_stats = {
            'Willpower': 'dual',
            'Gnosis': 'dual',
            'Glamour': 'dual',
            'Arete': 'advantage',
            'Enlightenment': 'advantage',
            'Rage': 'dual'
        }
        
        if base_name in pool_stats or any(k.lower() == base_name.lower() for k in pool_stats.keys()):
            # Get the pool subcategory
            if base_name in pool_stats:
                return ('pools', pool_stats[base_name])
            else:
                # Find the matching key case-insensitively
                for k in pool_stats:
                    if k.lower() == base_name.lower():
                        return ('pools', pool_stats[k])
        # If no match found
        return None, None

    def _get_ability_list(self):
        """Get list of valid abilities."""
        return [
            'Alertness', 'Athletics', 'Awareness', 'Brawl', 'Empathy', 'Primal Urge',
            'Expression', 'Intimidation', 'Kenning', 'Leadership', 'Streetwise', 'Subterfuge',
            'Animal Ken', 'Crafts', 'Drive', 'Etiquette', 'Firearms',
            'Larceny', 'Melee', 'Performance', 'Stealth', 'Survival',
            'Academics', 'Computer', 'Finance', 'Gremayre', 'Enigmas', 'Investigation', 'Law',
            'Medicine', 'Occult', 'Politics', 'Rituals', 'Science', 'Technology'
        ] 

    def _display_detailed_history(self, character):
        """Display detailed XP history for a character."""
        if not character.db.xp or not character.db.xp.get('spends'):
            self.caller.msg(f"{character.name} has no XP history.")
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
            
            if entry_type == "Spend":
                if 'stat_name' in entry and 'previous_rating' in entry:
                    # Handle stat names with parentheses
                    stat_name = entry['stat_name']
                    details = f"{stat_name} ({entry['previous_rating']} -> {entry['new_rating']})"
                else:
                    details = entry.get('reason', 'No reason given')
                
            table.add_row(
                timestamp.strftime('%Y-%m-%d %H:%M'),
                entry_type,
                amount,
                details
            )
            
        self.caller.msg(f"\n|wDetailed XP History for {character.name}|n")
        self.caller.msg(str(table))

    def calculate_xp_cost(self, stat_name, new_rating, current_rating, category=None, subcategory=None):
        """
        Calculate XP cost for increasing a stat.
        This is a wrapper around the xp_utils.calculate_xp_cost function.
        """
        from world.wod20th.utils.xp_utils import calculate_xp_cost
        return calculate_xp_cost(self, stat_name, new_rating, category, subcategory, current_rating)

    def validate_xp_purchase(self, stat_name, new_rating, category=None, subcategory=None):
        """Validate if a character can purchase a stat increase."""
        from world.wod20th.utils.xp_utils import validate_xp_purchase
        # Pass is_staff_spend=True if this is a staff spend
        is_staff_spend = 'staffspend' in self.switches
        return validate_xp_purchase(self.caller, stat_name, new_rating, category, subcategory, is_staff_spend=is_staff_spend)

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

    def _get_proper_stat_name(self, stat_name, category, subcategory):
        """Get the proper case-sensitive name for a stat."""
        # Store the original stat name for gift aliases
        original_stat_name = stat_name

        # Ensure stat_name is a string
        if isinstance(stat_name, list):
            if stat_name:
                stat_name = stat_name[0] if len(stat_name) == 1 else " ".join(stat_name)
            else:
                stat_name = ""
                
        from world.wod20th.utils.stat_mappings import (
            TALENTS, SKILLS, KNOWLEDGES,
            SECONDARY_TALENTS, SECONDARY_SKILLS, SECONDARY_KNOWLEDGES,
            UNIVERSAL_BACKGROUNDS, VAMPIRE_BACKGROUNDS, CHANGELING_BACKGROUNDS,
            MAGE_BACKGROUNDS, TECHNOCRACY_BACKGROUNDS, TRADITIONS_BACKGROUNDS,
            NEPHANDI_BACKGROUNDS, SHIFTER_BACKGROUNDS, SORCERER_BACKGROUNDS,
            KINAIN_BACKGROUNDS, MERIT_VALUES, RITE_VALUES, FLAW_VALUES, ARTS, REALMS
        )
        from world.wod20th.utils.sheet_constants import POWERS
        
        # Check for special handling of gift "Mother's Touch"
        if category == 'powers' and subcategory == 'gift' and stat_name.lower() == "mother's touch":
            # Store the original alias used
            self.gift_alias_used = stat_name
            # Return the exact case for the canonical name
            return "Mother's Touch"
        
        # Handle other stats based on their category
        if category == 'abilities':
            if subcategory == 'talents':
                for talent in TALENTS:
                    if talent.lower() == stat_name.lower():
                        return talent
            elif subcategory == 'skills':
                for skill in SKILLS:
                    if skill.lower() == stat_name.lower():
                        return skill
            elif subcategory == 'knowledges':
                for knowledge in KNOWLEDGES:
                    if knowledge.lower() == stat_name.lower():
                        return knowledge
        elif category == 'secondary_abilities':
            if subcategory == 'talents':
                for talent in SECONDARY_TALENTS:
                    if talent.lower() == stat_name.lower():
                        return talent
            elif subcategory == 'skills':
                for skill in SECONDARY_SKILLS:
                    if skill.lower() == stat_name.lower():
                        return skill
            elif subcategory == 'knowledges':
                for knowledge in SECONDARY_KNOWLEDGES:
                    if knowledge.lower() == stat_name.lower():
                        return knowledge
        elif category == 'backgrounds':
            for background in UNIVERSAL_BACKGROUNDS:
                if background.lower() == stat_name.lower():
                    return background
                    
            # If not in universal backgrounds, check splat-specific backgrounds
            splat = None
            
            # Try to get splat information
            try:
                if hasattr(self, "target") and self.target:  # If we're checking a target character
                    splat = self.target.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
                else:  # If we're checking the caller
                    splat = self.caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            except (KeyError, AttributeError):
                pass
                
            # Check splat-specific backgrounds
            if splat:
                if splat == 'Vampire':
                    for background in VAMPIRE_BACKGROUNDS:
                        if background.lower() == stat_name.lower():
                            return background
                elif splat == 'Changeling':
                    for background in CHANGELING_BACKGROUNDS:
                        if background.lower() == stat_name.lower():
                            return background
                elif splat == 'Mage':
                    # Get tradition or convention
                    tradition = None
                    try:
                        if hasattr(self, "target") and self.target:
                            tradition = self.target.db.stats.get('identity', {}).get('tradition', {}).get('Tradition', {}).get('perm', '')
                        else:
                            tradition = self.caller.db.stats.get('identity', {}).get('tradition', {}).get('Tradition', {}).get('perm', '')
                    except (KeyError, AttributeError):
                        pass
                        
                    if tradition:
                        if tradition in ['Dreamspeaker', 'Verbena', 'Virtual Adept', 'Order of Hermes', 'Celestial Chorus', 'Akashic Brotherhood', 'Cult of Ecstasy', 'Euthanatos', 'Sons of Ether', 'Hollow Ones']:
                            for background in TRADITIONS_BACKGROUNDS:
                                if background.lower() == stat_name.lower():
                                    return background
                        elif tradition in ["Nephandi"]:
                            for background in NEPHANDI_BACKGROUNDS:
                                if background.lower() == stat_name.lower():
                                    return background
                        elif tradition in ['Iteration X', 'New World Order', 'Progenitors', 'Syndicate', 'Void Engineers']:
                            for background in TECHNOCRACY_BACKGROUNDS:
                                if background.lower() == stat_name.lower():
                                    return background
                elif splat == 'Shifter':
                    for background in SHIFTER_BACKGROUNDS:
                        if background.lower() == stat_name.lower():
                            return background
                elif splat == 'Mortal+':
                    # Get sub-type for Mortal+
                    mortalplus_type = None
                    try:
                        if hasattr(self, "target") and self.target:
                            mortalplus_type = self.target.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
                        else:
                            mortalplus_type = self.caller.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
                    except (KeyError, AttributeError):
                        pass
                        
                    if mortalplus_type:
                        if mortalplus_type in ['Sorcerer', 'Numina', 'Psychic']:
                            for background in SORCERER_BACKGROUNDS:
                                if background.lower() == stat_name.lower():
                                    return background
                        elif mortalplus_type in ['Kinain']:
                            for background in KINAIN_BACKGROUNDS:
                                if background.lower() == stat_name.lower():
                                    return background
                                    
        elif category == 'merits':
            # Check if stat exists in our MERIT_VALUES mapping
            for merit_category, merits in MERIT_VALUES.items():
                if subcategory.lower() == merit_category.lower():
                    for merit, values in merits.items():
                        if merit.lower() == stat_name.lower():
                            return merit
                                    
        elif category == 'flaws':
            # Check if stat exists in our FLAW_VALUES mapping
            for flaw_category, flaws in FLAW_VALUES.items():
                if subcategory.lower() == flaw_category.lower():
                    for flaw, values in flaws.items():
                        if flaw.lower() == stat_name.lower():
                            return flaw
                                    
        elif category == 'powers':
            if subcategory == 'gift':
                # For gifts, we need to check the database
                # Store the original alias used
                self.gift_alias_used = original_stat_name
                
                # Convert stat_name to string if it's a list
                if isinstance(stat_name, list):
                    if stat_name:
                        stat_name = stat_name[0] if len(stat_name) == 1 else " ".join(stat_name)
                    else:
                        stat_name = ""
                
                # Use the database to validate and get the proper case
                from world.wod20th.models import Stat
                from django.db.models import Q
                
                # Check for an exact match first
                exact_match = Stat.objects.filter(
                    name__iexact=stat_name,
                    category='powers',
                    stat_type='gift'
                ).first()
                
                if exact_match:
                    return exact_match.name
                    
                # If no exact match, try alias matching
                alias_match = Stat.objects.filter(
                    gift_alias__icontains=stat_name,
                    category='powers',
                    stat_type='gift'
                ).first()
                
                if alias_match:
                    return alias_match.name
                    
                # If still no match, return the original name
                return stat_name
                
            # Check if it's an Art
            if subcategory == 'art':
                # Try to find the proper case in ARTS
                for art in ARTS:
                    if art.lower() == stat_name.lower():
                        return art
            elif subcategory == 'realm':
                # Check if the realm exists in our REALMS mapping
                for realm in REALMS:
                    if realm.lower() == stat_name.lower():
                        return realm
                return stat_name  # Return as-is if not found

            # Define power type mappings
            power_mappings = {
                'sphere': [
                    'Correspondence', 'Entropy', 'Forces', 'Life', 'Matter',
                    'Mind', 'Prime', 'Spirit', 'Time', 'Dimensional Science',
                    'Primal Utility', 'Data'
                ],
                'art': ARTS,
                'realm': REALMS,
                'discipline': POWERS.get('discipline', []),
                'numina': POWERS.get('numina', []),
                'charm': POWERS.get('charm', []),
                'blessing': POWERS.get('blessing', [])
            }
            def find_proper_name(name, name_list):
                """Find the proper case-sensitive name from a list."""
                for proper_name in name_list:
                    if proper_name.lower() == name.lower():
                        return proper_name
                return None
            # Check other power types
            if subcategory in power_mappings:
                proper_name = find_proper_name(stat_name, power_mappings[subcategory])
                if proper_name:
                    return proper_name

        # Add pool stats to proper name lookup
        pool_stats = {
            'willpower': 'Willpower',
            'gnosis': 'Gnosis',
            'glamour': 'Glamour',
            'arete': 'Arete',
            'enlightenment': 'Enlightenment',
            'rage': 'Rage'
        }

        # Check pools
        if category == 'pools':
            stat_name_lower = stat_name.lower()
            if stat_name_lower in pool_stats:
                return pool_stats[stat_name_lower]
            # Check if it matches any pool stat case-insensitively
            for proper_name in pool_stats.values():
                if proper_name.lower() == stat_name_lower:
                    return proper_name

        # If no match found in predefined lists, return the title-cased version
        return stat_name

    def fix_powers(self, character):
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

    def _get_canonical_gift_name(self, stat_name):
        """Get the canonical name of a gift from the database."""
        from world.wod20th.models import Stat
        gift = Stat.objects.filter(
            Q(name__iexact=stat_name) | Q(gift_alias__icontains=stat_name),
            category='powers',
            stat_type='gift'
        ).first()
        return gift.name if gift else stat_name

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
                self.fix_powers()
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
                original_stat_name = stat_name  # Update original_stat_name to match proper case

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
            # Set the gift alias using the original stat name
            if self.gift_alias_used and self.gift_alias_used.lower() != stat_name.lower():
                # Ensure the alias is a string, not a list
                alias_to_use = self.gift_alias_used
                if isinstance(self.gift_alias_used, list):
                    # If it's a list, use the first element or a joined string
                    if self.gift_alias_used:
                        alias_to_use = self.gift_alias_used[0] if len(self.gift_alias_used) == 1 else " ".join(self.gift_alias_used)
                    else:
                        alias_to_use = original_stat_name  # Fallback if empty list
                
                target.set_gift_alias(stat_name, alias_to_use, rating)
                logger.log_info(f"Set gift alias for {stat_name}: {alias_to_use}")

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