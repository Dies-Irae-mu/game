from evennia import default_cmds
from evennia.utils.search import search_object
from evennia.utils.evtable import EvTable
from datetime import datetime
from decimal import Decimal, ROUND_DOWN, InvalidOperation
from typeclasses.characters import Character
from django.db import transaction
from evennia.utils import logger
from django.db.models import Q

class CmdXP(default_cmds.MuxCommand):
    """
    View and manage experience points.
    
    Usage:
      +xp                     - View your XP
      +xp <name>             - View another character's XP (Staff only)
      +xp/desc <name>        - View detailed XP history (Staff only)
      +xp/sub <name>/<stat> <level>=<amount>/<reason> - Remove XP from character (Staff only)
      +xp/init               - Initialize scene tracking
      +xp/endscene          - Manually end current scene (only if scene doesn't end automatically, remove in future)
      +xp/add <name>=<amt>   - Add XP to a character (Staff only)
      +xp/spend <name> <rating>=<reason> - Spend XP (Must be in OOC area)
      +xp/forceweekly       - Force weekly XP distribution (Staff only)
      
    Examples:
      +xp/spend Strength 3=Getting stronger
      +xp/spend Potence 2=Learning from mentor
      +xp/spend Resources 2=Business success
    """
    
    key = "+xp"
    aliases = ["xp"]
    locks = "cmd:all()"
    help_category = "General"
    
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
                if not self.caller.check_permstring("builders"):
                    self.caller.msg("You don't have permission to remove XP.")
                    return
                    
                try:
                    # Split into target/stat and amount/reason parts
                    if "=" not in self.args:
                        self.caller.msg("Usage: +xp/sub <name>/<stat> <level>=<amount>/<reason>")
                        return
                        
                    target_info, amount_info = self.args.split("=", 1)
                    
                    # Parse target info
                    if "/" not in target_info:
                        self.caller.msg("Must specify both character name and stat.")
                        return
                    target_name, stat_info = target_info.split("/", 1)
                    
                    # Parse amount info
                    if "/" not in amount_info:
                        self.caller.msg("Must specify both amount and reason.")
                        return
                    amount, reason = amount_info.split("/", 1)
                    
                    # Get stat level if provided
                    stat_parts = stat_info.strip().split()
                    if len(stat_parts) > 1:
                        stat_name = " ".join(stat_parts[:-1])
                        stat_level = stat_parts[-1]
                        try:
                            stat_level = int(stat_level)
                        except ValueError:
                            stat_name = stat_info
                            stat_level = None
                    else:
                        stat_name = stat_info
                        stat_level = None
                    
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
                    
                    # Format the reason with stat details
                    formatted_reason = f"{stat_name}"
                    if stat_level is not None:
                        formatted_reason += f" (Level {stat_level})"
                    if reason:
                        formatted_reason += f" - {reason}"
                    
                    # Log the removal
                    removal = {
                        'type': 'removal',
                        'amount': float(xp_amount),
                        'stat_name': stat_name,
                        'stat_level': stat_level,
                        'reason': formatted_reason,
                        'staff_name': self.caller.name,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    if 'spends' not in target.db.xp:
                        target.db.xp['spends'] = []
                    target.db.xp['spends'].insert(0, removal)
                    
                    # Notify staff and target
                    self.caller.msg(f"Removed {xp_amount} XP from {target.name} for {formatted_reason}")
                    target.msg(f"{xp_amount} XP was removed by {self.caller.name} for {formatted_reason}")
                    self._display_xp(target)
                    
                except ValueError as e:
                    self.caller.msg("Usage: +xp/sub <name>/<stat> <level>=<amount>/<reason>")
                    self.caller.msg("Example: +xp/sub Bob/Strength 3=5.00/Correcting error")
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
                    # Fix any power issues before proceeding
                    self.fix_powers(self.caller)

                    # Parse input
                    if "=" not in self.args:
                        self.caller.msg("Usage: +xp/spend <name> <rating>=<reason>")
                        return
                        
                    stat_info, reason = self.args.split("=", 1)
                    stat_info = stat_info.strip()
                    reason = reason.strip()

                    # Parse stat info
                    stat_parts = stat_info.split()
                    if len(stat_parts) < 2:
                        self.caller.msg("Usage: +xp/spend <name> <rating>=<reason>")
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

                    # Determine category and subcategory
                    category, subcategory = self._determine_stat_category(stat_name)
                    if not category or not subcategory:
                        self.caller.msg(f"Invalid stat name: {stat_name}")
                        return

                    # Get proper case for the stat name based on category
                    proper_stat_name = self._get_proper_stat_name(stat_name, category, subcategory)
                    if not proper_stat_name:
                        self.caller.msg(f"Invalid stat name: {stat_name}")
                        return

                    # Check if stat already exists and get current value
                    current_value = (self.caller.db.stats.get(category, {})
                                   .get(subcategory, {})
                                   .get(proper_stat_name, {})
                                   .get('perm', 0))

                    # Attempt to spend XP
                    success, message = self.caller.buy_stat(
                        proper_stat_name, new_rating,
                        category=category,
                        subcategory=subcategory,
                        reason=reason
                    )
                    
                    self.caller.msg(message)
                    if success:
                        # Only show XP display on success
                        self._display_xp(self.caller)

                except ValueError as e:
                    self.caller.msg(f"Error: Invalid input - {str(e)}")
                    self.caller.msg("Usage: +xp/spend <name> <rating>=<reason>")
                except Exception as e:
                    self.caller.msg(f"Error: {str(e)}")
                    self.caller.msg("An error occurred while processing your request.")
                return  # Add return here to prevent duplicate XP display

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
                        # Skip if character is staff
                        if hasattr(char, 'check_permstring') and char.check_permstring("builders"):
                            continue
                            
                        # Skip if no scene data or no completed scenes
                        if (not hasattr(char, 'db') or 
                            not char.db.scene_data or 
                            not char.db.scene_data.get('completed_scenes', 0)):
                            continue
                            
                        # Award XP if they've participated in scenes
                        if hasattr(char, 'add_xp'):
                            char.add_xp(base_xp, "Weekly Activity", self.caller)
                            self.caller.msg(f"Awarded {base_xp} XP to {char.name}")
                            awarded_count += 1
                    
                    self.caller.msg(f"\nWeekly XP distribution completed. Awarded XP to {awarded_count} active characters.")
                    
                except Exception as e:
                    self.caller.msg(f"Error during XP distribution: {str(e)}")
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
            # Get XP data
            xp_data = target.attributes.get('xp')
            if not xp_data:
                xp_data = {
                    'total': Decimal('0.00'),
                    'current': Decimal('0.00'),
                    'spent': Decimal('0.00'),
                    'ic_earned': Decimal('0.00'),
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
            header = f"{'|b-|n' * dash_count}{title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
            
            # XP section
            exp_title = "|y Experience Points |n"
            title_len = len(exp_title)
            dash_count = (total_width - title_len) // 2
            exp_header = f"{'|b-|n' * dash_count}{exp_title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
            
            # Format XP values
            left_col_width = 20
            right_col_width = 12
            spacing = " " * 14
            
            ic_xp_display = f"{'|wIC XP:|n':<{left_col_width}}{ic_xp:>{right_col_width}.2f}"
            total_xp_display = f"{'|wTotal XP:|n':<{left_col_width}}{total:>{right_col_width}.2f}"
            current_xp_display = f"{'|wCurrent XP:|n':<{left_col_width}}{current:>{right_col_width}.2f}"
            award_xp_display = f"{'|wAward XP:|n':<{left_col_width}}{award_xp:>{right_col_width}.2f}"
            spent_xp_display = f"{'|wSpent XP:|n':<{left_col_width}}{spent:>{right_col_width}.2f}"
            
            exp_section = f"{ic_xp_display}{spacing}{award_xp_display}\n"
            exp_section += f"{total_xp_display}{spacing}{spent_xp_display}\n"
            exp_section += f"{current_xp_display}\n"
            
            # Recent activity section
            activity_title = "|y Recent Activity |n"
            title_len = len(activity_title)
            dash_count = (total_width - title_len) // 2
            activity_header = f"{'|b-|n' * dash_count}{activity_title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
            
            activity_section = ""
            if xp_data.get('spends'):
                for entry in xp_data['spends'][:5]:  # Show last 5 entries
                    timestamp = datetime.fromisoformat(entry['timestamp'])
                    formatted_time = timestamp.strftime("%Y-%m-%d %H:%M")
                    if entry['type'] == 'receive':
                        activity_section += f"{formatted_time} - Received {entry['amount']} XP ({entry['reason']})\n"
                    else:
                        activity_section += f"{formatted_time} - Spent {entry['amount']} XP on {entry['reason']}\n"
            else:
                activity_section = "No XP history yet.\n"
            
            # Footer
            footer = f"{'|b-|n' * total_width}"
            
            # Combine all sections
            display = (
                header +
                exp_header +
                exp_section +
                activity_header +
                activity_section +
                footer
            )
            
            self.caller.msg(display)

        except Exception as e:
            logger.error(f"Error displaying XP for {target.name}: {str(e)}")
            self.caller.msg("Error displaying XP information.")

    @staticmethod
    def _determine_stat_category(stat_name):
        """
        Determine the category and type of a stat based on its name.
        Uses the stat mappings from world.wod20th.utils.stat_mappings.
        """
        from world.wod20th.utils.stat_mappings import (
            STAT_TYPE_TO_CATEGORY, STAT_VALIDATION,
            TALENTS, SKILLS, KNOWLEDGES,
            SECONDARY_TALENTS, SECONDARY_SKILLS, SECONDARY_KNOWLEDGES,
            UNIVERSAL_BACKGROUNDS
        )
        from world.wod20th.utils.sheet_constants import (
            ABILITIES, SECONDARY_ABILITIES, BACKGROUNDS,
            POWERS, POOLS
        )

        # Convert stat name to title case for comparison
        stat_name = stat_name.title()

        # Special handling for gifts - if it's a gift name, return powers/gift
        if any(stat_name.lower().startswith(prefix.lower()) for prefix in ['Breed:', 'Auspice:', 'Tribe:', 'Gift:']):
            return ('powers', 'gift')

        # Check if it's a gift without a prefix
        from world.wod20th.models import Stat
        gift_query = Q(stat_type='gift')
        for gift in Stat.objects.filter(gift_query):
            # Check both the name and any aliases
            if (gift.name.lower() == stat_name.lower() or
                (gift.gift_alias and any(alias.lower() == stat_name.lower() for alias in gift.gift_alias))):
                return ('powers', 'gift')

        # Check attributes based on the actual structure
        physical_attrs = ['Strength', 'Dexterity', 'Stamina']
        social_attrs = ['Charisma', 'Manipulation', 'Appearance']
        mental_attrs = ['Perception', 'Intelligence', 'Wits']

        if stat_name in physical_attrs:
            return ('attributes', 'physical')
        elif stat_name in social_attrs:
            return ('attributes', 'social')
        elif stat_name in mental_attrs:
            return ('attributes', 'mental')

        # Helper function for case-insensitive comparison
        def case_insensitive_in(name, collection):
            name_lower = name.lower()
            return any(item.lower() == name_lower for item in collection)

        # Check primary abilities
        if case_insensitive_in(stat_name, TALENTS):
            return ('abilities', 'talent')
        elif case_insensitive_in(stat_name, SKILLS):
            return ('abilities', 'skill')
        elif case_insensitive_in(stat_name, KNOWLEDGES):
            return ('abilities', 'knowledge')

        # Check secondary abilities
        if case_insensitive_in(stat_name, SECONDARY_TALENTS):
            return ('secondary_abilities', 'secondary_talent')
        elif case_insensitive_in(stat_name, SECONDARY_SKILLS):
            return ('secondary_abilities', 'secondary_skill')
        elif case_insensitive_in(stat_name, SECONDARY_KNOWLEDGES):
            return ('secondary_abilities', 'secondary_knowledge')

        # Check backgrounds
        if case_insensitive_in(stat_name, UNIVERSAL_BACKGROUNDS):
            return ('backgrounds', 'background')

        # Check powers
        for power_type in POWERS:
            if case_insensitive_in(stat_name, POWERS[power_type]):
                return ('powers', power_type.lower())

        # Check pools
        for pool_type in POOLS:
            if case_insensitive_in(stat_name, POOLS[pool_type]):
                return ('pools', 'dual')

        # If no match found
        return None, None

    def _get_ability_list(self):
        """Get list of valid abilities."""
        return [
            'Alertness', 'Athletics', 'Awareness', 'Brawl', 'Empathy',
            'Expression', 'Intimidation', 'Leadership', 'Streetwise', 'Subterfuge',
            'Animal Ken', 'Crafts', 'Drive', 'Etiquette', 'Firearms',
            'Larceny', 'Melee', 'Performance', 'Stealth', 'Survival',
            'Academics', 'Computer', 'Finance', 'Enigmas', 'Investigation', 'Law',
            'Medicine', 'Occult', 'Politics', 'Science', 'Technology'
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
                    details = (f"{entry['stat_name']} "
                             f"({entry['previous_rating']} -> {entry['new_rating']})")
                else:
                    details = entry.get('reason', 'No reason given')
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
        # Validate inputs
        if new_rating <= current_rating:
            return 0, False
            
        # Get character's splat
        splat = self.get_stat('other', 'splat', 'Splat', temp=False)
        if not splat:
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
                'base': 8,
                'multiplier': 'new',
                'max_without_approval': 10
            }
        }

        # Get cost settings for this category
        if category not in costs:
            return 0, False
        cost_settings = costs[category]

        # Check if new rating exceeds limit
        requires_approval = new_rating > cost_settings['max_without_approval']

        # Calculate base cost
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
                    # Out-of-clan disciplines cost more
                    clan = self.get_stat('identity', 'lineage', 'Clan', temp=False)
                    if clan:
                        from world.wod20th.utils.vampire_utils import get_clan_disciplines
                        clan_disciplines = get_clan_disciplines(clan)
                        if stat_name not in clan_disciplines:
                            total_cost *= 2  # Double cost for out-of-clan disciplines

            elif splat == 'Mage':
                if subcategory == 'sphere':
                    # Adjust costs based on affinity sphere
                    affinity_sphere = self.get_stat('identity', 'personal', 'Affinity Sphere', temp=False)
                    if affinity_sphere and stat_name != affinity_sphere:
                        total_cost *= 1.5  # Higher cost for non-affinity spheres

            elif splat == 'Changeling':
                if subcategory == 'art':
                    # Check for affinity art
                    affinity_art = self.get_stat('identity', 'personal', 'Affinity Art', temp=False)
                    if affinity_art and stat_name != affinity_art:
                        total_cost *= 1.5  # Higher cost for non-affinity arts

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

        # Validate rating increase
        if new_rating <= current_rating:
            return False, "New rating must be higher than current rating"

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
        # Get current rating
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
            # Update the stat
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

            return True, f"Successfully increased {stat_name} to {new_rating} (Cost: {cost} XP)"

        except Exception as e:
            return False, f"Error processing purchase: {str(e)}"

    @staticmethod
    def _get_proper_stat_name(stat_name, category, subcategory):
        """Get the proper case-sensitive name for a stat."""
        from world.wod20th.utils.stat_mappings import (
            TALENTS, SKILLS, KNOWLEDGES,
            SECONDARY_TALENTS, SECONDARY_SKILLS, SECONDARY_KNOWLEDGES,
            UNIVERSAL_BACKGROUNDS
        )
        from world.wod20th.utils.sheet_constants import (
            POWERS
        )

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
            if isinstance(collection, dict):
                collection = collection.keys()
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

        # Check powers
        if category == 'powers':
            if subcategory == 'sphere':
                sphere_names = [
                    'Correspondence', 'Entropy', 'Forces', 'Life', 'Matter',
                    'Mind', 'Prime', 'Spirit', 'Time', 'Dimensional Science',
                    'Primal Utility', 'Data'
                ]
                proper_name = find_proper_name(stat_name, sphere_names)
                if proper_name:
                    return proper_name
            elif subcategory in POWERS:
                proper_name = find_proper_name(stat_name, POWERS[subcategory])
                if proper_name:
                    return proper_name

        # Check backgrounds
        if category == 'backgrounds':
            proper_name = find_proper_name(stat_name, UNIVERSAL_BACKGROUNDS)
            if proper_name:
                return proper_name

        # If no match found in predefined lists, return the title-cased version
        return stat_name 

    def fix_powers(self, character):
        """Fix duplicate powers and ensure proper categorization in character stats."""
        if not character.db.stats:
            return

        # Get the powers dictionary
        powers = character.db.stats.get('powers', {})
        if not powers:
            return

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
                        fixed_gifts[f'Gift: {gift_name}'] = values
                else:
                    fixed_gifts[gift_name] = values
            if fixed_gifts != powers['gift']:
                powers['gift'] = fixed_gifts
                changes_made = True

        if changes_made:
            character.db.stats['powers'] = powers
            return True
        return False 