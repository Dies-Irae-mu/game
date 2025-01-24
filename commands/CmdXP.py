from evennia import default_cmds
from evennia.utils.search import search_object
from evennia.utils.evtable import EvTable
from datetime import datetime
from decimal import Decimal, ROUND_DOWN, InvalidOperation
from typeclasses.characters import Character

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
      +xp/spend <stat> <rating>=<reason> - Spend XP (Must be in OOC area)
      +xp/forceweekly       - Force weekly XP distribution (Staff only)
      
    Examples:
      +xp/spend Strength 3=Getting stronger
      +xp/spend Potence 2=Learning from mentor
      +xp/spend Resources 2=Business success
    """
    
    key = "+xp"
    aliases = ["xp"]
    locks = "cmd:all()"
    help_category = "Character"
    # show my xp    
    def func(self):
        """Execute command"""
        if not self.args and not self.switches:
            self._display_xp(self.caller)
            return
            
        # Staff viewing another character's XP
        if self.args and not self.switches:
          
            # Check if viewing self
            if self.args.lower() == self.caller.name.lower():
                self._display_xp(self.caller)
                return
                
            # Staff check - allow builders or higher to view others
            if not (self.caller.check_permstring("builders") or 
                   self.caller.check_permstring("Wizards") or 
                   self.caller.check_permstring("Immortals")):
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

        # Process switches
        if self.switches:
            # Add new staff commands
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
                    stat_info, reason = self.args.split("=", 1)
                    stat_info = stat_info.strip()
                    reason = reason.strip()

                    # parse stat info
                    stat_parts = stat_info.split()
                    if len(stat_parts) < 2:
                        self.caller.msg("Usage: +xp/spend <stat name> <rating>=<reason>")
                        return
                    
                    # get new rating
                    new_rating = int(stat_parts[-1])
                    stat_name = " ".join(stat_parts[:-1])

                    # determine category
                    category, subcategory = self._determine_stat_category(stat_name)
                    if not category:
                        self.caller.msg(f"Invalid stat name: {stat_name}")
                        return

                    # what is the current rating?
                    current_rating = self.caller.get_stat(category, subcategory, stat_name) or 0
                    
                    # at desired rating already?
                    if current_rating == new_rating:
                        self.caller.msg(f"You already have {stat_name} at rating {new_rating}.")
                        return
                    elif current_rating > new_rating:
                        self.caller.msg(f"You cannot reduce {stat_name} from {current_rating} to {new_rating}.")
                        return

                    # check for cost
                    cost, requires_approval = self.caller.calculate_xp_cost(
                        stat_name, 
                        new_rating, 
                        category=category,
                        subcategory=subcategory,
                        current_rating=current_rating
                    )
                    
                    if cost == 0:
                        self.caller.msg("Invalid stat or no increase needed")
                        return
                        
                    if requires_approval:
                        self.caller.msg("This purchase requires staff approval.")
                        return

                    # do we have enough xp?
                    if self.caller.db.xp['current'] < cost:
                        self.caller.msg(f"Not enough XP. Cost: {cost}, Available: {self.caller.db.xp['current']}")
                        return

                    # can we buy it?
                    success, message = self.caller.buy_stat(
                        stat_name, 
                        new_rating, 
                        category=category,
                        subcategory=subcategory,
                        reason=reason
                    )
                    
                    if not success:
                        self.caller.msg(f"Failed to spend XP: {message}")
                        return
                        
                    self.caller.msg(message)

                    self._display_xp(self.caller)

                except ValueError as e:
                    self.caller.msg(f"Error: Invalid input - {str(e)}")
                    self.caller.msg("Usage: +xp/spend <stat name> <rating>=<reason>")
                except Exception as e:
                    self.caller.msg(f"Error: {str(e)}")
                    self.caller.msg("An error occurred while processing your request.")

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
                else:
                    self.caller.msg("Failed to add XP.")
                    
            except ValueError:
                self.caller.msg("Usage: +xp/add <name>=<amount>")
                return
        """
        Force weekly was created because the weekly xp script was not running. It probably shouldn't be used, but it's here if needed.
        Pretty good debug tool.
        """
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

    def _display_xp(self, character):
        """Displays XP information for a character."""
        xp = character.db.xp
        
        if not xp or not isinstance(xp, dict):
            # Initialize XP if it doesn't exist or isn't a dict
            xp = {
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
            character.db.xp = xp
            
        total_width = 78
            
        # header
        title = f" {character.name}'s XP "
        title_len = len(title)
        dash_count = (total_width - title_len) // 2
        header = f"{'|b-|n' * dash_count}{title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
        
        # Calculate IC XP (from weekly awards and scene rewards)
        ic_xp = Decimal('0.00')
        award_xp = Decimal('0.00')
        if xp.get('spends'):
            for entry in xp['spends']:
                if entry['type'] == 'receive':
                    if entry['reason'] == 'Weekly Activity':
                        ic_xp += Decimal(str(entry['amount']))
                    else:
                        award_xp += Decimal(str(entry['amount']))
        
        # Update the stored IC XP value
        xp['ic_earned'] = ic_xp
        
        # xp section
        exp_title = "|y Experience Points |n"
        title_len = len(exp_title)
        dash_count = (total_width - title_len) // 2
        exp_header = f"{'|b-|n' * dash_count}{exp_title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
        #xp value formatting
        left_col_width = 20  
        right_col_width = 12 
        
        # left column values
        ic_xp_display = f"{'|wIC XP:|n':<{left_col_width}}{ic_xp:>{right_col_width}.2f}"
        total_xp = f"{'|wTotal XP:|n':<{left_col_width}}{xp['total']:>{right_col_width}.2f}"
        current_xp = f"{'|wCurrent XP:|n':<{left_col_width}}{xp['current']:>{right_col_width}.2f}"
        
        # right column values
        award_xp_display = f"{'|wAward XP:|n':<{left_col_width}}{award_xp:>{right_col_width}.2f}"
        spent_xp = f"{'|wSpent XP:|n':<{left_col_width}}{xp['spent']:>{right_col_width}.2f}"
        
        # and then we bring it together
        spacing = " " * 14  # column spacing
        exp_section = f"{ic_xp_display}{spacing}{award_xp_display}\n"
        exp_section += f"{total_xp}{spacing}{spent_xp}\n"
        exp_section += f"{current_xp}\n"
        
        # recent activity section
        activity_title = "|y Recent Activity |n"
        activity_title_len = len(activity_title)
        activity_dash_count = (total_width - activity_title_len) // 2
        activity_header = f"{'|b-|n' * activity_dash_count}{activity_title}{'|b-|n' * (total_width - activity_dash_count - activity_title_len)}\n"
        
        # format the recent spends
        activity_section = ""
        if xp.get('spends'):
            for entry in xp['spends']:
                timestamp = datetime.fromisoformat(entry['timestamp'])
                if entry['type'] == 'spend':
                    # Format spend entries
                    if 'previous_rating' in entry and 'new_rating' in entry:
                        activity_section += (
                            f"{timestamp.strftime('%Y-%m-%d %H:%M')} - "
                            f"Spent {entry['amount']:.2f} XP on {entry['stat_name']} "
                            f"({entry['previous_rating']} -> {entry['new_rating']})\n"
                        )
                    else:
                        # Legacy format for older entries
                        activity_section += (
                            f"{timestamp.strftime('%Y-%m-%d %H:%M')} - "
                            f"Spent {entry['amount']:.2f} XP on {entry['reason']}\n"
                        )
                else:  # receive entries
                    activity_section += (
                        f"{timestamp.strftime('%Y-%m-%d %H:%M')} - "
                        f"Received {entry['amount']:.2f} XP ({entry['reason']})\n"
                    )
        else:
            activity_section = "No XP history yet.\n"
    
        footer = f"{'|b-|n' * total_width}"
        
        # Add scene tracking status
        scene_data = character.db.scene_data
        if scene_data and isinstance(scene_data, dict):  # Verify it's a dictionary
            scene_title = "|y Scene Status |n"
            scene_title_len = len(scene_title)
            scene_dash_count = (total_width - scene_title_len) // 2
            scene_header = f"{'|b-|n' * scene_dash_count}{scene_title}{'|b-|n' * (total_width - scene_dash_count - scene_title_len)}\n"
            
            scene_section = ""
            # Safely check for current_scene
            current_scene = scene_data.get('current_scene')
            if current_scene and isinstance(current_scene, datetime):
                duration = (datetime.now() - current_scene).total_seconds() / 60
                scene_section += f"Current scene duration: {int(duration)} minutes\n"
                
                # Safely check for last_activity
                last_activity = scene_data.get('last_activity')
                if last_activity and isinstance(last_activity, datetime):
                    last_activity_delta = (datetime.now() - last_activity).total_seconds() / 60
                    scene_section += f"Last activity: {int(last_activity_delta)} minutes ago\n"
            else:
                scene_section += "No active scene\n"
            
            # Safely get completed_scenes with default value
            completed_scenes = scene_data.get('completed_scenes', 0)
            scene_section += f"Completed scenes this week: {completed_scenes}\n"
            
            display = (
                header +
                exp_header +
                exp_section +
                activity_header +
                activity_section +
                scene_header +
                scene_section +
                footer
            )
        else:
            # Initialize scene_data if it doesn't exist or isn't a dict
            scene_data = {
                'current_scene': None,
                'last_activity': None,
                'completed_scenes': 0
            }
            character.db.scene_data = scene_data
            
            display = (
                header +
                exp_header +
                exp_section +
                activity_header +
                activity_section +
                footer
            )
        
        self.caller.msg(display) 

    def _determine_stat_category(self, stat_name):
        """Determine the category and type of a stat based on its name."""
        # Basic attributes (in physical/social/mental subcategories)
        physical_attrs = ['Strength', 'Dexterity', 'Stamina']
        social_attrs = ['Charisma', 'Manipulation', 'Appearance']
        mental_attrs = ['Perception', 'Intelligence', 'Wits']
        
        if stat_name in physical_attrs:
            return ('attributes', 'physical')
        elif stat_name in social_attrs:
            return ('attributes', 'social')
        elif stat_name in mental_attrs:
            return ('attributes', 'mental')

        # Basic abilities (in talent/skill/knowledge subcategories)
        talents = ['Alertness', 'Athletics', 'Awareness', 'Brawl', 'Empathy',
                  'Expression', 'Intimidation', 'Leadership', 'Streetwise', 'Subterfuge']
        skills = ['Animal Ken', 'Crafts', 'Drive', 'Etiquette', 'Firearms',
                 'Larceny', 'Melee', 'Performance', 'Stealth', 'Survival']
        knowledges = ['Academics', 'Computer', 'Finance', 'Investigation', 'Law',
                     'Medicine', 'Occult', 'Politics', 'Science', 'Technology',
                     'Cosmology', 'Enigmas']
        
        if stat_name in talents:
            return ('abilities', 'talent')
        elif stat_name in skills:
            return ('abilities', 'skill')
        elif stat_name in knowledges:
            return ('abilities', 'knowledge')

        # Secondary abilities
        secondary_talents = ['Carousing', 'Diplomacy', 'Intrigue', 'Mimicry', 'Scrounging', 'Seduction', 'Style']
        secondary_skills = ['Archery', 'Fortune-Telling', 'Fencing', 'Gambling', 'Jury-Rigging', 'Pilot', 'Torture']
        secondary_knowledges = ['Area Knowledge', 'Cultural Savvy', 'Demolitions', 'Herbalism', 'Media', 'Power-Brokering', 'Vice']

        if stat_name in secondary_talents:
            return ('abilities', 'secondary_talent')
        elif stat_name in secondary_skills:
            return ('abilities', 'secondary_skill')
        elif stat_name in secondary_knowledges:
            return ('abilities', 'secondary_knowledge')

        # Backgrounds
        backgrounds = ['Resources', 'Contacts', 'Allies', 'Backup', 'Herd', 'Library',
                      'Kinfolk', 'Spirit Heritage', 'Ancestors']
        if stat_name in backgrounds:
            return ('backgrounds', 'background')

        # Garou Gifts
        garou_gifts = {
            # Breed Gifts
            'Spirit Speech', 'Master of Fire', 'Sense Wyrm', 'Create Element',
            'Primal Anger', 'Scent of Running Water', 'Scent of the True Form',
            'Burrow', 'Articulate Blood-Dream', 'Gnaw',
            # Add more Garou gifts here
        }
        
        if stat_name in garou_gifts:
            return ('powers', 'gift')

        # Pools
        if stat_name in ['Willpower', 'Rage', 'Gnosis']:
            return ('pools', 'dual')

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