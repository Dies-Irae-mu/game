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
from world.wod20th.utils.xp_utils import process_xp_spend, _determine_stat_category

class CmdXP(default_cmds.MuxCommand):
    """
    View and manage experience points.
    
    Usage:
      +xp                     - View your XP
      +xp <name>             - View another character's XP (Staff only)
      +xp/desc <name>        - View detailed XP history (Staff only)
      +xp/sub <name>/<amount>=<reason> - Remove XP from character (Staff only)
      +xp/init               - Initialize scene tracking
      +xp/endscene          - Manually end current scene (only if scene doesn't end automatically, remove in future)
      +xp/add <name>=<amt>   - Add XP to a character (Staff only)
      +xp/spend <name> <rating>=<reason> - Spend XP (Must be in OOC area)
      +xp/forceweekly       - Force weekly XP distribution (Staff only)
      +xp/staffspend <name>/<stat> <rating>=<reason> - Spend XP on behalf of a character (Staff only)
      +xp/fixstats <name>   - Fix a character's stats structure (Staff only)
      +xp/fixdata <name>    - Fix a character's XP data structure (Staff only)
      
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

                    # Determine category and subcategory
                    category, subcategory = _determine_stat_category(stat_name)
                    logger.log_info(f"{self.caller.name}: Determined category: {category}, subcategory: {subcategory}")
                    
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

                    # Get proper case for the stat name based on category
                    proper_stat_name = self._get_proper_stat_name(stat_name, category, subcategory)
                    logger.log_info(f"{self.caller.name}: Got proper stat name: {proper_stat_name}")
                    
                    if not proper_stat_name:
                        self.caller.msg(f"Invalid stat name: {stat_name}")
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
                        self.caller.msg("Must specify both stat name and rating.")
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
                    category, subcategory = _determine_stat_category(stat_name)
                    logger.log_info(f"Determined category: {category}, subcategory: {subcategory}")
                    
                    if not category or not subcategory:
                        self.caller.msg(f"Invalid stat name: {stat_name}")
                        return

                    # Get proper case for the stat name based on category
                    proper_stat_name = self._get_proper_stat_name(stat_name, category, subcategory)
                    logger.log_info(f"Got proper stat name: {proper_stat_name}")
                    
                    if not proper_stat_name:
                        self.caller.msg(f"Invalid stat name: {stat_name}")
                        return

                    # Process the XP spend
                    success, message, cost = process_xp_spend(
                        character=target,
                        stat_name=proper_stat_name,
                        new_rating=new_rating,
                        category=category,
                        subcategory=subcategory,
                        reason=f"Staff Spend: {reason}",
                        is_staff_spend=True
                    )
                    
                    if success:
                        stat_display_name = stat_name if category == 'secondary_abilities' else proper_stat_name
                        if category == 'flaws' and reason.lower() == 'flaw buyoff':
                            self.caller.msg(f"Successfully bought off {proper_stat_name} flaw (Cost: {cost} XP)")
                            target.msg(f"{self.caller.name} has spent {cost} XP to buy off your {proper_stat_name} flaw.")
                        else:
                            current_rating = target.get_stat(category, subcategory, proper_stat_name)
                            # Modified message to be clearer about what happened
                            self.caller.msg(f"Successfully processed XP spend for {stat_display_name} with rating {new_rating} (Cost: {cost} XP)")
                            target.msg(f"{self.caller.name} has spent {cost} XP to set your {stat_display_name} to {new_rating}.")
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
        Returns (cost, requires_approval)
        """
        # Add debug logging
        logger.log_info(f"Calculating XP cost for: {stat_name} (category: {category}, subcategory: {subcategory})")
        logger.log_info(f"Current rating: {current_rating}, New rating: {new_rating}")
        logger.log_info(f"Stats structure: {self.db.stats}")
        
        # Validate inputs - allow 0 to 1 for initial purchases
        if new_rating < current_rating or (new_rating == current_rating and current_rating > 0):
            logger.log_info(f"New rating ({new_rating}) not valid compared to current rating ({current_rating})")
            return 0, False
            
        # Special case for initial purchase (0 to 1)
        if current_rating == 0 and new_rating == 1:
            logger.log_info("Processing initial purchase (0 to 1)")
        
        # Get character's splat
        splat = self.get_stat('other', 'splat', 'Splat', temp=False)
        logger.log_info(f"Character splat: {splat}")
        if not splat:
            logger.log_info("Character splat not set")
            return 0, False

        # Base costs per category
        costs = {
            'attributes': {
                'base': 5,
                'multiplier': 'new',  # cost = base * new_rating
                'max_without_approval': 5
            },
            'abilities': {
                'base': 2,
                'multiplier': 'new',
                'max_without_approval': 5
            },
            'secondary_abilities': {
                'base': 2,
                'multiplier': 'new',
                'max_without_approval': 5
            },
            'backgrounds': {
                'base': 3,
                'multiplier': 'new',
                'max_without_approval': 5
            },
            'powers': {
                'base': 7,
                'multiplier': 'new',
                'max_without_approval': 5
            },
            'pools': {
                'base': 2,  # Default multiplier for most pools
                'multiplier': 'current',  # Will be overridden for specific pools
                'max_without_approval': 10
            }
        }

        # Get cost settings for this category
        if category not in costs:
            logger.log_info(f"Category {category} not found in costs dictionary")
            return 0, False
        cost_settings = costs[category]

        # Check if new rating exceeds limit
        requires_approval = new_rating > cost_settings['max_without_approval']
        logger.log_info(f"Requires approval: {requires_approval}")

        # Calculate total cost
        total_cost = 0
        
        # Special handling for pools
        if category == 'pools':
            # Get proper case for stat name for comparison
            proper_stat_name = self._get_proper_stat_name(stat_name, category, subcategory)
            logger.log_info(f"Pool stat name: {proper_stat_name}")
            
            # Define pool-specific costs
            pool_costs = {
                'Willpower': {'base': 2, 'multiplier': 'current'},      # Current Rating x 2
                'Path': {'base': 2, 'multiplier': 'current'},           # Current Rating x 2
                'Rage': {'base': 1, 'multiplier': 'current'},           # Current Rating x 1
                'Gnosis': {'base': 2, 'multiplier': 'current'},         # Current Rating x 2
                'Arete': {'base': 8, 'multiplier': 'current'},          # Current Rating x 8
                'Enlightenment': {'base': 8, 'multiplier': 'current'},  # Current Rating x 8
                'Glamour': {'base': 3, 'multiplier': 'current'}         # Current Rating x 3
            }

            # Get cost settings for this specific pool
            pool_cost = pool_costs.get(proper_stat_name, {'base': 2, 'multiplier': 'current'})
            
            # Calculate cost for each point being purchased
            total_cost = 0
            for rating in range(current_rating + 1, new_rating + 1):
                if pool_cost['multiplier'] == 'current':
                    total_cost += rating * pool_cost['base']
                else:
                    total_cost += pool_cost['base']  # Flat cost if not using current rating
            return total_cost, requires_approval

        # Special handling for Kinfolk gifts
        elif category == 'powers' and subcategory == 'gift' and splat == 'Mortal+':
            char_type = self.get_stat('identity', 'lineage', 'Type', temp=False)
            logger.log_info(f"Kinfolk check - Character type: {char_type}")
            
            if char_type and char_type.lower() == 'kinfolk':
                # Check if they have Gnosis merit for level 2 gifts
                if new_rating > 1:
                    gnosis_merit = next((value.get('perm', 0) for merit, value in self.db.stats.get('merits', {}).get('merit', {}).items() 
                                      if merit.lower() == 'gnosis'), 0)
                    logger.log_info(f"Kinfolk Gnosis merit value: {gnosis_merit}")
                    if not gnosis_merit:
                        return 0, True  # Requires Gnosis merit for level 2 gifts
                
                # Get the gift details from the database
                from world.wod20th.models import Stat
                gift = Stat.objects.filter(
                    name__iexact=stat_name,
                    category='powers',
                    stat_type='gift'
                ).first()
                
                if gift:
                    logger.log_info(f"Found gift in database: {gift.name}")
                    # Check if it's a homid gift (breed gift) or tribal gift
                    is_homid = False
                    is_tribal = False
                    is_special = False
                    
                    # Check if it's a homid gift
                    if gift.shifter_type:
                        allowed_types = gift.shifter_type if isinstance(gift.shifter_type, list) else [gift.shifter_type]
                        is_homid = 'homid' in [t.lower() for t in allowed_types]
                    
                    # Check if it's a tribal gift
                    if gift.tribe:
                        kinfolk_tribe = self.get_stat('identity', 'lineage', 'Tribe', temp=False)
                        if kinfolk_tribe:
                            allowed_tribes = gift.tribe if isinstance(gift.tribe, list) else [gift.tribe]
                            is_tribal = kinfolk_tribe.lower() in [t.lower() for t in allowed_tribes]
                    
                    # Check if it's a Croatan or Planetary gift
                    if gift.tribe:
                        tribes = gift.tribe if isinstance(gift.tribe, list) else [gift.tribe]
                        is_special = any(t.lower() in ['croatan', 'planetary'] for t in tribes)
                    
                    logger.log_info(f"Gift type checks - Homid: {is_homid}, Tribal: {is_tribal}, Special: {is_special}")
                    
                    # Calculate cost based on gift type
                    if is_special:
                        total_cost = new_rating * 7  # Croatan/Planetary gifts cost 7 XP per level
                    elif is_homid or is_tribal:
                        total_cost = new_rating * 6   # Breed/Tribe gifts
                    else:
                        total_cost = new_rating * 10  # Outside Breed/Tribe gifts
                    
                    logger.log_info(f"Calculated cost for Kinfolk gift: {total_cost}")
                    return total_cost, requires_approval

        # Special handling for Shifter gifts
        elif category == 'powers' and subcategory == 'gift' and splat == 'Shifter':
            from world.wod20th.models import Stat
            from django.db.models import Q
            
            logger.log_info("Processing Shifter gift")
            
            # Get the gift details from the database
            gift = Stat.objects.filter(
                Q(name__iexact=stat_name) | Q(gift_alias__icontains=stat_name),
                category='powers',
                stat_type='gift'
            ).first()
            
            if gift:
                logger.log_info(f"Found gift in database: {gift.name}")
                # Get character's breed, auspice, and tribe
                breed = self.get_stat('identity', 'lineage', 'Breed', temp=False)
                auspice = self.get_stat('identity', 'lineage', 'Auspice', temp=False)
                tribe = self.get_stat('identity', 'lineage', 'Tribe', temp=False)
                shifter_type = self.get_stat('identity', 'lineage', 'Type', temp=False)
                
                logger.log_info(f"Character details - Breed: {breed}, Auspice: {auspice}, Tribe: {tribe}, Type: {shifter_type}")
                
                # For non-Garou shifter types, default to base cost
                if shifter_type and shifter_type.lower() != 'garou':
                    total_cost = 0
                    for rating in range(current_rating + 1, new_rating + 1):
                        total_cost += 3  # Base cost of 3 XP per level
                    logger.log_info(f"Non-Garou shifter cost: {total_cost}")
                    return total_cost, requires_approval
                
                # For Garou, check if it's a breed, auspice, or tribe gift
                is_breed_gift = False
                is_auspice_gift = False
                is_tribe_gift = False
                is_special = False
                
                # Check breed gifts
                if gift.shifter_type:
                    allowed_types = gift.shifter_type if isinstance(gift.shifter_type, list) else [gift.shifter_type]
                    is_breed_gift = breed and breed.lower() in [t.lower() for t in allowed_types]
                
                # Check auspice gifts
                if hasattr(gift, 'auspice') and gift.auspice:
                    allowed_auspices = gift.auspice if isinstance(gift.auspice, list) else [gift.auspice]
                    is_auspice_gift = auspice and auspice.lower() in [a.lower() for a in allowed_auspices]
                
                # Check tribe gifts and special gifts
                if gift.tribe:
                    tribes = gift.tribe if isinstance(gift.tribe, list) else [gift.tribe]
                    is_tribe_gift = tribe and tribe.lower() in [t.lower() for t in tribes]
                    is_special = any(t.lower() in ['croatan', 'planetary'] for t in tribes)
                
                logger.log_info(f"Gift type checks - Breed: {is_breed_gift}, Auspice: {is_auspice_gift}, Tribe: {is_tribe_gift}, Special: {is_special}")
                
                # Calculate cost for each level being purchased
                total_cost = 0
                for rating in range(current_rating + 1, new_rating + 1):
                    if is_special:
                        total_cost += 7  # Croatan/Planetary gifts cost 7 XP per level
                    elif is_breed_gift or is_auspice_gift or is_tribe_gift:
                        total_cost += 3  # Breed/Auspice/Tribe gifts cost 3 XP per level
                    else:
                        total_cost += 5  # Other gifts cost 5 XP per level
                
                logger.log_info(f"Calculated cost for Garou gift: {total_cost}")
                return total_cost, requires_approval
            
            # If gift not found in database, use base cost
            total_cost = 0
            for rating in range(current_rating + 1, new_rating + 1):
                total_cost += 3  # Base cost of 3 XP per level
            logger.log_info(f"Using base cost for gift not found in database: {total_cost}")
            return total_cost, requires_approval

        else:
            # Use standard calculation for other stats
            if cost_settings['multiplier'] == 'new':
                # Cost is base * new rating
                total_cost = cost_settings['base'] * new_rating
            else:
                # Cost is base * number of increases
                total_cost = cost_settings['base'] * (new_rating - current_rating)

        # Special handling for different splats and power types
        if category == 'powers':
            # Adjust costs based on splat and power type
            if splat == 'Vampire':
                if subcategory == 'discipline':
                    # Calculate cost based on clan status
                    clan = self.get_stat('identity', 'lineage', 'Clan', temp=False)
                    if clan:
                        from world.wod20th.utils.vampire_utils import get_clan_disciplines
                        clan_disciplines = get_clan_disciplines(clan)
                        # In-clan: 5 * current rating, Out-of-clan: 7 * current rating
                        base_cost = 5 if stat_name in clan_disciplines else 7
                        total_cost = 0
                        for rating in range(current_rating + 1, new_rating + 1):
                            total_cost += base_cost * rating

            elif splat == 'Mage':
                if subcategory == 'sphere':
                    # Get affinity sphere
                    affinity_sphere = self.get_stat('identity', 'personal', 'Affinity Sphere', temp=False)
                    # Calculate cost: Affinity = 7 * current rating, Other = 8 * current rating
                    base_cost = 7 if stat_name == affinity_sphere else 8
                    total_cost = 0
                    for rating in range(current_rating + 1, new_rating + 1):
                        total_cost += base_cost * rating
            
            elif splat == 'Changeling':
                if subcategory == 'art':
                    # Arts have special costs:
                    # New art (0->1): 7xp
                    # Then 4xp * current rating for each level
                    total_cost = 0
                    for rating in range(current_rating + 1, new_rating + 1):
                        if rating == 1:
                            total_cost += 7  # First dot costs 7
                        else:
                            total_cost += 4 * (rating - 1)  # Subsequent dots cost 4 * previous rating
                    return total_cost, requires_approval
                
                elif subcategory == 'realm':
                    # Realms have special costs:
                    # New realm (0->1): 5xp
                    # Then 3xp * current rating for each level
                    total_cost = 0
                    for rating in range(current_rating + 1, new_rating + 1):
                        if rating == 1:
                            total_cost += 5  # First dot costs 5
                        else:
                            total_cost += 3 * (rating - 1)  # Subsequent dots cost 3 * previous rating
                    return total_cost, requires_approval

        logger.log_info(f"Final calculated cost: {total_cost}")
        return total_cost, requires_approval

    def validate_xp_purchase(self, stat_name, new_rating, category=None, subcategory=None):
        """
        Validate if a character can purchase a stat increase.
        Returns (can_purchase, error_message)
        """
        # Get character's splat
        splat = self.get_stat('other', 'splat', 'Splat', temp=False)
        if not splat:
            return False, "Character splat not set"

        # Get current rating
        current_rating = self.get_stat(category, subcategory, stat_name, temp=False) or 0

        # Validate rating increase - special handling for initial purchases
        if new_rating < current_rating:
            return False, "New rating must be higher than current rating"
        if new_rating == current_rating and current_rating > 0:
            return False, "New rating must be higher than current rating"

        # Check for gifts
        if category == 'powers' and subcategory == 'gift':
            import json
            import os
            
            # Check if character can use gifts
            char_type = self.get_stat('identity', 'lineage', 'Type', temp=False)
            can_use_gifts = (
                splat == 'Shifter' or 
                splat == 'Possessed' or 
                (splat == 'Mortal+' and char_type == 'Kinfolk')
            )
            
            if not can_use_gifts:
                return False, "Character cannot use gifts"

            # Find the gift in JSON files
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
                                    break
                        if found_gift:
                            break
                except Exception as e:
                    logger.log_err(f"Error reading gift file {gift_file}: {str(e)}")
                    continue
            
            if not found_gift:
                return False, f"Gift '{stat_name}' not found in any gift lists"

            # Check if the gift is available to the character's shifter type
            shifter_type = self.get_stat('identity', 'lineage', 'Type', temp=False)
            if shifter_type and found_gift.get('shifter_type'):
                allowed_types = found_gift['shifter_type'] if isinstance(found_gift['shifter_type'], list) else [found_gift['shifter_type']]
                if shifter_type.lower() not in [t.lower() for t in allowed_types]:
                    return False, f"The gift '{found_gift['name']}' is not available to {shifter_type}"

            # Check for special gifts that require staff approval
            if found_gift.get('tribe'):
                tribes = found_gift['tribe'] if isinstance(found_gift['tribe'], list) else [found_gift['tribe']]
                if any(t.lower() in ['croatan', 'planetary'] for t in tribes):
                    return False, "Croatan and Planetary gifts can only be purchased through staff approval (+xp/staffspend)"

            # For initial purchase (0 to 1), always allow if we got this far
            if current_rating == 0 and new_rating == 1:
                return True, ""

        # Check if stat exists and is valid for character's splat
        if category == 'powers':
            # Validate power based on splat
            if splat == 'Vampire':
                from world.wod20th.utils.vampire_utils import validate_vampire_stats
                is_valid, error_msg = validate_vampire_stats(self, stat_name, str(new_rating), category, subcategory)
            elif splat == 'Mage':
                from world.wod20th.utils.mage_utils import validate_mage_stats
                is_valid, error_msg = validate_mage_stats(self, stat_name, str(new_rating), category, subcategory)
            elif splat == 'Changeling':
                from world.wod20th.utils.changeling_utils import validate_changeling_stats
                is_valid, error_msg = validate_changeling_stats(self, stat_name, str(new_rating), category, subcategory)
            elif splat == 'Shifter':
                from world.wod20th.utils.shifter_utils import validate_shifter_stats
                is_valid, error_msg = validate_shifter_stats(self, stat_name, str(new_rating), category, subcategory)
            elif splat == 'Mortal+':
                from world.wod20th.utils.mortalplus_utils import validate_mortalplus_stats
                is_valid, error_msg = validate_mortalplus_stats(self, stat_name, str(new_rating), category, subcategory)
            elif splat == 'Possessed':
                from world.wod20th.utils.possessed_utils import validate_possessed_stats
                is_valid, error_msg = validate_possessed_stats(self, stat_name, str(new_rating), category, subcategory)
            elif splat == 'Companion':
                from world.wod20th.utils.companion_utils import validate_companion_stats
                is_valid, error_msg = validate_companion_stats(self, stat_name, str(new_rating), category, subcategory)
            else:
                is_valid, error_msg = False, "Invalid splat type"

            if not is_valid:
                return False, error_msg

        return True, ""

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
        from world.wod20th.utils.stat_mappings import (
            TALENTS, SKILLS, KNOWLEDGES,
            SECONDARY_TALENTS, SECONDARY_SKILLS, SECONDARY_KNOWLEDGES,
            UNIVERSAL_BACKGROUNDS, VAMPIRE_BACKGROUNDS, CHANGELING_BACKGROUNDS,
            MAGE_BACKGROUNDS, TECHNOCRACY_BACKGROUNDS, TRADITIONS_BACKGROUNDS,
            NEPHANDI_BACKGROUNDS, SHIFTER_BACKGROUNDS, SORCERER_BACKGROUNDS,
            KINAIN_BACKGROUNDS, MERIT_VALUES, RITE_VALUES, FLAW_VALUES, ARTS, REALMS
        )
        from world.wod20th.utils.sheet_constants import (
            POWERS
        )

        # Special handling for Mother's Touch and similar gifts
        if category == 'powers' and subcategory == 'gift':
            # Check for exact matches in database first
            from world.wod20th.models import Stat
            from django.db.models import Q
            
            # Special handling for Mother's Touch
            if stat_name.lower() == "mother's touch":
                gift = Stat.objects.filter(
                    name__iexact="Mother's Touch",
                    category='powers',
                    stat_type='gift'
                ).first()
                if gift:
                    return gift.name
            
            # For other gifts, try exact match or alias
            gift = Stat.objects.filter(
                name__iexact=stat_name,
                category='powers',
                stat_type='gift'
            ).first()
            
            # If not found by exact name, check aliases but be more precise
            if not gift:
                # For aliases, we need to be careful not to match partial words
                gifts = Stat.objects.filter(
                    category='powers',
                    stat_type='gift'
                )
                
                # Manual check for better alias matching
                for potential_gift in gifts:
                    if potential_gift.gift_alias:
                        # Split aliases and check for exact word match
                        aliases = potential_gift.gift_alias.split(',')
                        for alias in aliases:
                            alias = alias.strip().lower()
                            stat_lower = stat_name.lower()
                            
                            # Check for exact alias match or word boundary match
                            if alias == stat_lower or f" {stat_lower} " in f" {alias} ":
                                gift = potential_gift
                                break
                                
                    if gift:
                        break
            
            if gift:
                return gift.name  # Return the exact name from database
            
            # Check for Arts and Realms after checking for gifts
            if category == 'powers' and subcategory == 'art':
                try:
                    proper_name = find_proper_key(stat_name, ARTS)
                    if proper_name:
                        return proper_name
                except:
                    return stat_name
                    
            if category == 'powers' and subcategory == 'realm':
                try:
                    proper_name = find_proper_key(stat_name, REALMS)
                    if proper_name:
                        return proper_name
                except:
                    return stat_name
            
            return stat_name  # If not found, return as is

        # Helper function for case-insensitive key lookup with space/underscore normalization
        def find_proper_key(name, collection):
            try:
                name_lower = name.lower().replace('_', ' ')
                
                # Handle both sets and dictionaries
                for item in collection:
                    if isinstance(item, str) and item.lower().replace('_', ' ') == name_lower:
                        return item
                return None
            except:
                return None

        # Check backgrounds first
        if category == 'backgrounds':
            # First check universal backgrounds
            proper_name = find_proper_key(stat_name, UNIVERSAL_BACKGROUNDS)
            if proper_name:
                return proper_name
                
            # Then check splat-specific backgrounds
            # Note: The actual splat check is done in validate_xp_purchase
            # Here we just want to find the proper name if it exists in any background list
            for bg_list in [VAMPIRE_BACKGROUNDS, CHANGELING_BACKGROUNDS, MAGE_BACKGROUNDS,
                          TECHNOCRACY_BACKGROUNDS, TRADITIONS_BACKGROUNDS, NEPHANDI_BACKGROUNDS,
                          SHIFTER_BACKGROUNDS, SORCERER_BACKGROUNDS]:
                proper_name = find_proper_key(stat_name, bg_list)
                if proper_name:
                    return proper_name

        # Check merits, rites, and flaws
        if category == 'merits':
            proper_name = find_proper_key(stat_name, MERIT_VALUES)
            if proper_name:
                return proper_name
        elif category == 'powers' and subcategory == 'rite':
            proper_name = find_proper_key(stat_name, RITE_VALUES)
            if proper_name:
                return proper_name
        elif category == 'flaws':
            proper_name = find_proper_key(stat_name, FLAW_VALUES)
            if proper_name:
                return proper_name

        # Convert to title case for comparison
        stat_name = stat_name.title()
        
        # Define proper names for attributes
        attribute_names = {
            'physical': ['Strength', 'Dexterity', 'Stamina'],
            'social': ['Charisma', 'Manipulation', 'Appearance'],
            'mental': ['Perception', 'Intelligence', 'Wits']
        }
        
        # Helper function for case-insensitive matching
        def find_proper_name(name, collection):
            # Handle different types of collections (dict, set, list)
            if isinstance(collection, dict):
                collection = collection.keys()
            # For sets and lists, we can iterate directly
            name_lower = name.lower()
            for item in collection:
                if isinstance(item, str) and item.lower() == name_lower:
                    return item
            return None

        # Check attributes
        if category == 'attributes':
            for attrs in attribute_names.values():
                proper_name = find_proper_name(stat_name, attrs)
                if proper_name:
                    return proper_name

        # Check abilities and secondary abilities
        if category == 'abilities':
            if subcategory == 'talent':
                proper_name = find_proper_name(stat_name, TALENTS)
            elif subcategory == 'skill':
                proper_name = find_proper_name(stat_name, SKILLS)
            elif subcategory == 'knowledge':
                proper_name = find_proper_name(stat_name, KNOWLEDGES)
            if proper_name:
                return proper_name

        if category == 'secondary_abilities':
            if subcategory == 'secondary_talent':
                proper_name = find_proper_name(stat_name, SECONDARY_TALENTS)
            elif subcategory == 'secondary_skill':
                proper_name = find_proper_name(stat_name, SECONDARY_SKILLS)
            elif subcategory == 'secondary_knowledge':
                proper_name = find_proper_name(stat_name, SECONDARY_KNOWLEDGES)
            if proper_name:
                return proper_name
            # If not found in predefined lists, use title case for each word
            return ' '.join(word.title() for word in stat_name.split())

        # Check powers
        if category == 'powers':
            # For gifts, just use the name as provided (in Title case)
            if subcategory == 'gift':
                return stat_name
                
            # Check if it's an Art
            if subcategory == 'art':
                # Try to find the proper case in ARTS
                for art in ARTS:
                    if art.lower() == stat_name.lower():
                        return art
                return stat_name  # Return as-is if not found
                
            # Check if it's a Realm
            if subcategory == 'realm':
                # Try to find the proper case in REALMS
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
                stat_name = ' '.join(word.title() for word in stat_name.split())
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
                    self.set_gift_alias(stat_name, original_stat_name, new_rating)
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
            # Get proper case for standard stats
            proper_stat = target.get_proper_stat_name(category, subcategory, stat_name)
            if proper_stat:
                stat_name = proper_stat
                logger.log_info(f"Got proper stat name: {stat_name}")

        # Format the reason
        staff_reason = f"Staff Spend: {self.caller.name} - {reason}"

        # Process the spend
        from world.wod20th.utils.xp_utils import process_xp_spend
        success, message, cost = process_xp_spend(
            target, stat_name, rating, category, subcategory, 
            reason=staff_reason, is_staff_spend=True
        )

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