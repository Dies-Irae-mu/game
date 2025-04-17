from evennia import default_cmds
from evennia.utils import utils
from world.wod20th.models import Stat
from evennia import search_object
from world.wod20th.utils.damage import calculate_total_health_levels, apply_damage_or_healing

class CmdPump(default_cmds.MuxCommand):
    """
    Boost physical attributes using supernatural means.

    Usage:
      +boost <stat>=<amount>[/<description>]
      +boost/end <id>
      +boost/endall
      +boost/refresh - Refresh all active boosts (use after XP spends)
      +boosts - List active attribute boosts
      +boosts <name> - Staff: View another character's boosts
      +boost/set <player>=<stat>/<amount>[/<description>] - Staff: Set boost on player
      +boost/remove <player>=<id> - Staff: Remove boost from player
      +boost/removeall <player> - Staff: Remove all boosts from player
      +boost/rage <stat>=<amount> - Gurahl: Spend Rage to boost Strength or Stamina
      +boost/rage health=<amount> - Gurahl: Spend Rage to gain additional health levels

    Examples:
      +boost strength=2
      +boost dexterity=1
      +boost stamina=3/special gift
      +boost intelligence=2/Wyrd Effect
      +boost brawl=2/Totem Bond
      +boost Perception=2/Mind Effect
      +boost/end 1
      +boost/endall
      +boost/refresh
      +boosts
      +boost/rage strength=2 - Gurahl: Spend 2 Rage to boost Strength
      +boost/rage health=2 - Gurahl: Spend 2 Rage to gain 2 health levels
      +boosts John - Staff: View John's boosts
      +boost/set Jane=strength/2/Blessing
      +boost/remove Jane=1
      +boost/removeall Jane

    This command allows characters to temporarily boost their stats
    based on their supernatural type:
    - Vampires: Can boost physical attributes only (Strength, Dexterity, Stamina)
    - Shifters with totem: Can boost any stat (attributes, abilities, pools)
    - Changelings: Can boost any attribute or ability
    - Mages: Can boost any attribute or ability
    - Fomori/Kami: Through blessings
    - Gurahl: Can spend Rage to boost Strength or Stamina (up to 2x form value)
    - Gurahl: Can spend Rage to gain additional health levels

    Use +boost/end <id> to end a specific boost early.
    Use +boost/endall to end all active boosts.
    Use +boost/refresh to refresh boosts after spending XP.
    Use +boosts to see active boosts and their IDs.
    Staff can use +boosts <name> to view another character's boosts.
    """

    key = "+boost"
    aliases = ["pump", "+boosts", "boosts"]
    locks = "cmd:all()"
    help_category = "RP Commands"

    # Define valid stats per splat
    VAMPIRE_STATS = ["strength", "dexterity", "stamina"]
    MENTAL_ATTRS = ["intelligence", "wits", "perception"]
    SOCIAL_ATTRS = ["charisma", "manipulation", "appearance"]
    PHYSICAL_ATTRS = ["strength", "dexterity", "stamina"]
    ALL_ATTRIBUTES = PHYSICAL_ATTRS + SOCIAL_ATTRS + MENTAL_ATTRS
    
    # Define abilities
    TALENTS = ["alertness", "athletics", "brawl", "dodge", "intimidation", "leadership", "primal-urge", "streetwise", "subterfuge"]
    SKILLS = ["animal ken", "crafts", "drive", "etiquette", "firearms", "melee", "performance", "security", "stealth", "survival"]
    KNOWLEDGES = ["academics", "computer", "enigmas", "investigation", "law", "medicine", "occult", "politics", "rituals", "science", "technology"]
    ALL_ABILITIES = TALENTS + SKILLS + KNOWLEDGES

    # Define proper case mapping for stats
    STAT_CASES = {
        'primal-urge': 'Primal-Urge',
        'animal ken': 'Animal Ken',
        'strength': 'Strength',
        'dexterity': 'Dexterity',
        'stamina': 'Stamina',
        'charisma': 'Charisma',
        'manipulation': 'Manipulation',
        'appearance': 'Appearance',
        'intelligence': 'Intelligence',
        'wits': 'Wits',
        'perception': 'Perception',
        'athletics': 'Athletics',
        'brawl': 'Brawl',
        'dodge': 'Dodge',
        'intimidation': 'Intimidation',
        'leadership': 'Leadership',
        'streetwise': 'Streetwise',
        'subterfuge': 'Subterfuge',
        'crafts': 'Crafts',
        'drive': 'Drive',
        'etiquette': 'Etiquette',
        'firearms': 'Firearms',
        'melee': 'Melee',
        'performance': 'Performance',
        'security': 'Security',
        'stealth': 'Stealth',
        'survival': 'Survival',
        'academics': 'Academics',
        'computer': 'Computer',
        'enigmas': 'Enigmas',
        'investigation': 'Investigation',
        'law': 'Law',
        'medicine': 'Medicine',
        'occult': 'Occult',
        'politics': 'Politics',
        'rituals': 'Rituals',
        'science': 'Science',
        'technology': 'Technology',
        'rage': 'Rage',
        'gnosis': 'Gnosis',
        'willpower': 'Willpower'
    }

    def _get_proper_case(self, stat_name):
        """Get the proper case for a stat name."""
        return self.STAT_CASES.get(stat_name.lower(), stat_name.capitalize())

    def _ensure_attribute_boosts(self, caller):
        """Ensure the attribute_boosts dictionary exists on the caller."""
        if not hasattr(caller.db, 'attribute_boosts') or caller.db.attribute_boosts is None:
            caller.db.attribute_boosts = {}
            caller.db.next_boost_id = 1
            caller.db.recycled_boost_ids = []
        elif not hasattr(caller.db, 'next_boost_id') or caller.db.next_boost_id is None:
            # Initialize next_boost_id if it doesn't exist or is None
            caller.db.next_boost_id = max([boost.get('id', 0) for boost in caller.db.attribute_boosts.values()], default=0) + 1
        
        # Always ensure recycled_boost_ids exists and is a list
        if not hasattr(caller.db, 'recycled_boost_ids') or caller.db.recycled_boost_ids is None:
            caller.db.recycled_boost_ids = []

    def _get_next_boost_id(self, caller):
        """Get the next available boost ID."""
        self._ensure_attribute_boosts(caller)
        # Check for recycled IDs first
        if caller.db.recycled_boost_ids:
            return caller.db.recycled_boost_ids.pop(0)
        next_id = caller.db.next_boost_id
        caller.db.next_boost_id += 1
        return next_id

    def _get_boost_duration(self, splat):
        """Get the duration of the boost based on splat type."""
        if splat == 'Vampire':
            return 3600  # 1 hour in seconds
        return None  # Indefinite for other splats

    def _find_instanced_stat(self, stats_dict, stat_name):
        """Find an instanced stat in a dictionary."""
        if not stats_dict:
            return None
            
        # Look for exact match first
        if stat_name in stats_dict:
            return stats_dict[stat_name]
            
        # Look for instanced versions
        for key in stats_dict:
            if key.startswith(f"{stat_name}("):
                return stats_dict[key]
        return None

    def _get_valid_stats(self, caller, splat):
        """Get list of valid stats that can be boosted based on splat type."""
        if splat == 'Vampire':
            return self.VAMPIRE_STATS
        elif splat in ['Changeling', 'Mage']:
            # Changelings and Mages can boost attributes and abilities
            return self.ALL_ATTRIBUTES + self.ALL_ABILITIES
        elif splat in ['Possessed', 'Companion', 'Mortal+']:
            return self.ALL_ATTRIBUTES
        elif splat == 'Shifter':
            # For Shifters with totem, return None to indicate all stats are valid
            return None
        return self.PHYSICAL_ATTRS  # Default to physical only

    def _can_boost(self, caller, splat):
        """Check if the character can boost attributes."""
        if splat == 'Vampire':
            return True
        elif splat == 'Shifter':
            # Check if they have a totem in backgrounds
            if 'backgrounds' in caller.db.stats:
                background_stats = caller.db.stats['backgrounds'].get('background', {})
                totem = self._find_instanced_stat(background_stats, 'Totem')
                if totem and totem.get('perm', 0) > 0:
                    return True
            return False
        elif splat == 'Changeling':
            return True
        elif splat == 'Mage':
            return True
        elif splat == 'Possessed':
            return True
        elif splat == 'Companion':
            return True
        elif splat == 'Mortal+':
            return True
        return False

    def _get_stat_location(self, stat_name):
        """Get the category and type for a stat."""
        stat_name = stat_name.lower()
        # Check attributes
        if stat_name in self.PHYSICAL_ATTRS:
            return 'attributes', 'physical'
        elif stat_name in self.SOCIAL_ATTRS:
            return 'attributes', 'social'
        elif stat_name in self.MENTAL_ATTRS:
            return 'attributes', 'mental'
        # Check abilities
        elif stat_name in ['alertness', 'athletics', 'brawl', 'dodge', 'intimidation', 'leadership', 'primal-urge', 'streetwise', 'subterfuge']:
            return 'abilities', 'talent'
        elif stat_name in ['animal ken', 'crafts', 'drive', 'etiquette', 'firearms', 'melee', 'performance', 'security', 'stealth', 'survival']:
            return 'abilities', 'skill'
        elif stat_name in ['academics', 'computer', 'enigmas', 'investigation', 'law', 'medicine', 'occult', 'politics', 'rituals', 'science', 'technology']:
            return 'abilities', 'knowledge'
        # Check pools
        elif stat_name in ['rage', 'gnosis', 'willpower']:
            return 'pools', 'dual'
        # For secondary abilities
        elif stat_name.startswith('secondary_'):
            return 'secondary_abilities', stat_name.split('_')[1]
        return None, None

    def _handle_end_boost(self, caller, args):
        """Handle the /end switch to end a specific boost."""
        try:
            boost_id = int(args.strip())
        except ValueError:
            caller.msg("Please specify a valid boost ID number.")
            return

        self._ensure_attribute_boosts(caller)
        
        # Find the boost with this ID
        found_stat = None
        is_health_boost = False
        for stat, boost_info in caller.db.attribute_boosts.items():
            if boost_info.get('id') == boost_id:
                found_stat = stat
                is_health_boost = boost_info.get('is_health_boost', False)
                break

        if not found_stat:
            caller.msg(f"No boost found with ID {boost_id}.")
            return

        # Special handling for health boosts
        if is_health_boost:
            self._clear_gurahl_health_boost(caller)
            return

        # Get the boost info
        boost_info = caller.db.attribute_boosts[found_stat]
        amount = boost_info.get('amount', 0)
        
        # Get stat location
        stat_name = found_stat.lower()
        category, stat_type = self._get_stat_location(stat_name)
        if not category or not stat_type:
            caller.msg(f"Error: Cannot find stat location for {stat_name}")
            return

        # Get current values and set new value based on category
        if category == 'attributes':
            # Work directly with the stats dictionary for attributes
            stats_dict = caller.db.stats
            perm_value = stats_dict[category][stat_type][found_stat]['perm']
            stats_dict[category][stat_type][found_stat]['temp'] = perm_value
            new_value = perm_value
        else:
            # For non-attributes, use get_stat/set_stat
            current_temp = caller.get_stat(category, stat_type, found_stat, temp=True)
            perm_value = caller.get_stat(category, stat_type, found_stat, temp=False)
            
            if current_temp is None or perm_value is None:
                caller.msg(f"Error: Cannot find values for {found_stat}")
                return

            # For pools, adjust both permanent and temporary values
            if category == 'pools' and stat_type == 'dual' and stat_name in ['rage', 'gnosis', 'willpower']:
                new_value = max(perm_value - amount, 1)  # Ensure pools don't go below 1
                caller.set_stat(category, stat_type, found_stat, new_value, temp=False)
                caller.set_stat(category, stat_type, found_stat, new_value, temp=True)
            else:
                # For other stats, just adjust temporary value back to permanent
                new_value = perm_value
                caller.set_stat(category, stat_type, found_stat, new_value, temp=True)
        
        # Recycle the boost ID
        caller.db.recycled_boost_ids.append(boost_id)
        
        # Remove the boost
        del caller.db.attribute_boosts[found_stat]
        
        caller.msg(f"Ended boost #{boost_id} - Your {found_stat} returns to {new_value}.")

    def _format_boosts_display(self, target, boosts):
        """Format the boosts display with proper styling."""
        total_width = 78
        
        # Header
        title = f" {target.name}'s Boosts "
        title_len = len(title)
        dash_count = (total_width - title_len) // 2
        msg = f"{'|b-|n' * dash_count}{title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
        
        if not boosts:
            msg += "|wNo active boosts.|n\n"
            return msg
            
        # Format boosts display
        left_col_width = 20
        right_col_width = 12
        spacing = " " * 14
        
        for stat, boost_info in boosts.items():
            source = boost_info.get('source', 'Unknown')
            amount = boost_info.get('amount', 0)
            boost_id = boost_info.get('id', '?')
            
            stat_display = f"{'|w' + stat + ':|n':<{left_col_width}}{'+' + str(amount):>{right_col_width}}"
            source_display = f"{'|wSource:|n':<{left_col_width}}{source:>{right_col_width}}"
            id_display = f"{'|wID:|n':<{left_col_width}}{'#' + str(boost_id):>{right_col_width}}"
            
            msg += f"{stat_display}{spacing}{source_display}\n"
            msg += f"{id_display}\n"
            msg += f"{'|b-|n' * total_width}\n"
            
        return msg

    def _handle_boosts_command(self, caller, target=None):
        """Handle the +boosts command to list active boosts."""
        if not target:
            target = caller
            
        self._ensure_attribute_boosts(target)
        
        if not target.db.attribute_boosts:
            if target == caller:
                caller.msg("You have no active stat boosts.")
            else:
                caller.msg(f"{target.name} has no active stat boosts.")
            return

        # Format and display the boosts
        msg = self._format_boosts_display(target, target.db.attribute_boosts)
        caller.msg(msg)

    def _handle_endall_boosts(self, caller):
        """Handle the /endall switch to end all active boosts."""
        self._ensure_attribute_boosts(caller)
        
        if not caller.db.attribute_boosts:
            caller.msg("You have no active stat boosts to end.")
            return

        # Process each boost
        for stat_name, boost_info in list(caller.db.attribute_boosts.items()):
            # Special handling for health boosts
            if boost_info.get('is_health_boost', False):
                self._clear_gurahl_health_boost(caller)
                continue
                
            amount = boost_info.get('amount', 0)
            boost_id = boost_info.get('id', '?')
            
            # Get stat location
            category, stat_type = self._get_stat_location(stat_name.lower())
            if not category or not stat_type:
                continue

            # Handle stats based on category
            if category == 'attributes':
                # Work directly with the stats dictionary for attributes
                stats_dict = caller.db.stats
                perm_value = stats_dict[category][stat_type][stat_name]['perm']
                stats_dict[category][stat_type][stat_name]['temp'] = perm_value
                new_value = perm_value
            else:
                # For non-attributes, use get_stat/set_stat
                current_temp = caller.get_stat(category, stat_type, stat_name, temp=True)
                perm_value = caller.get_stat(category, stat_type, stat_name, temp=False)
                
                if current_temp is None or perm_value is None:
                    continue

                # For pools, adjust both permanent and temporary values
                if category == 'pools' and stat_type == 'dual' and stat_name.lower() in ['rage', 'gnosis', 'willpower']:
                    new_value = max(perm_value - amount, 1)  # Ensure pools don't go below 1
                    caller.set_stat(category, stat_type, stat_name, new_value, temp=False)
                    caller.set_stat(category, stat_type, stat_name, new_value, temp=True)
                else:
                    # For other stats, just adjust temporary value back to permanent
                    new_value = perm_value
                    caller.set_stat(category, stat_type, stat_name, new_value, temp=True)
            
            # Recycle the boost ID
            caller.db.recycled_boost_ids.append(boost_id)
            
            # Remove the boost
            del caller.db.attribute_boosts[stat_name]
            
            caller.msg(f"Ended boost #{boost_id} - Your {stat_name} returns to {new_value}.")

        caller.msg("All active boosts have been ended.")

    def _handle_set_boost(self, caller, args):
        """Handle the /set switch for staff to set boosts on players."""
        if not caller.check_permstring("Builders"):
            caller.msg("You don't have permission to set boosts on other characters.")
            return
            
        if not args or "=" not in args:
            caller.msg("Usage: +boost/set <player>=<stat>/<amount>[/<description>]")
            return
            
        player_name, stat_info = args.split("=", 1)
        player_name = player_name.strip()
        
        # Find the target character
        target = search_object(player_name, typeclass="typeclasses.characters.Character")
        if not target:
            caller.msg(f"Could not find character '{player_name}'.")
            return
        if len(target) > 1:
            caller.msg(f"Multiple matches found for '{player_name}'. Please be more specific.")
            return
            
        target = target[0]  # Get the first (and only) match
        
        # Parse stat, amount, and optional description
        stat_parts = stat_info.split("/")
        if len(stat_parts) < 2:
            caller.msg("Usage: +boost/set <player>=<stat>/<amount>[/<description>]")
            return
            
        stat_name = stat_parts[0].strip().lower()
        proper_stat_name = self._get_proper_case(stat_name)
        
        try:
            amount = int(stat_parts[1].strip())
        except ValueError:
            caller.msg("The amount must be a number.")
            return
            
        if amount <= 0:
            caller.msg("The amount must be a positive number.")
            return
            
        # Get optional description or use default
        if len(stat_parts) > 2:
            description = "/".join(stat_parts[2:]).strip()
        else:
            # Get character's splat for default source
            splat = target.get_stat('other', 'splat', 'Splat', temp=False)
            description = f"Staff: {splat}"
            
        # Get stat location
        category, stat_type = self._get_stat_location(stat_name)
        if not category or not stat_type:
            caller.msg(f"Cannot find stat: {stat_name}")
            return
            
        # Get current stat values
        current_perm = target.get_stat(category, stat_type, proper_stat_name, temp=False)
        current_temp = target.get_stat(category, stat_type, proper_stat_name, temp=True)
        
        if current_perm is None or current_temp is None:
            caller.msg(f"Error: Could not find {proper_stat_name} value.")
            return
            
        # Calculate new value, capped at 10 for most stats
        cap = 10
        if stat_name in ['rage', 'gnosis']:  # Special caps for certain pools
            cap = 20
            
        # For pools, boost the permanent value
        if category == 'pools' and stat_type == 'dual' and stat_name.lower() in ['rage', 'gnosis', 'willpower']:
            new_perm_value = min(current_perm + amount, cap)
            actual_increase = new_perm_value - current_perm
            
            if actual_increase == 0:
                caller.msg(f"{target.name}'s {proper_stat_name} is already at maximum ({cap}).")
                return
                
            # Set both permanent and temporary values for pools
            target.set_stat(category, stat_type, proper_stat_name, new_perm_value, temp=False)
            target.set_stat(category, stat_type, proper_stat_name, new_perm_value, temp=True)
        else:
            # For other stats, boost temporary value
            # Get values directly from the stats dictionary
            stats_dict = target.db.stats
            if category == 'attributes':
                current_perm = stats_dict[category][stat_type][proper_stat_name]['perm']
                current_temp = stats_dict[category][stat_type][proper_stat_name]['temp']
            else:
                current_perm = target.get_stat(category, stat_type, proper_stat_name, temp=False)
                current_temp = target.get_stat(category, stat_type, proper_stat_name, temp=True)
            
            # Ensure attribute_boosts exists before checking
            self._ensure_attribute_boosts(target)
            
            if proper_stat_name in target.db.attribute_boosts:
                # If already boosted, add to current boost amount
                current_boost = target.db.attribute_boosts[proper_stat_name]['amount']
                new_boost = current_boost + amount
                new_temp = min(current_perm + new_boost, cap)
                actual_increase = amount
            else:
                # If not boosted, add boost amount to current value
                new_temp = min(current_perm + amount, cap)
                actual_increase = amount
                
            # Check if we're at the cap
            if new_temp > cap:
                caller.msg(f"{target.name}'s {proper_stat_name} cannot be boosted beyond {cap}.")
                return
                
            # Set the value directly for attributes
            if category == 'attributes':
                stats_dict[category][stat_type][proper_stat_name]['temp'] = new_temp
            else:
                target.set_stat(category, stat_type, proper_stat_name, new_temp, temp=True)
                
        # Get a new boost ID
        boost_id = self._get_next_boost_id(target)
        
        # Store the boost information with staff source
        if proper_stat_name in target.db.attribute_boosts:
            target.db.attribute_boosts[proper_stat_name]['amount'] += actual_increase
            target.db.attribute_boosts[proper_stat_name]['source'] = description
        else:
            target.db.attribute_boosts[proper_stat_name] = {
                'id': boost_id,
                'amount': actual_increase,
                'source': description
            }
            
        caller.msg(f"You boosted {target.name}'s {proper_stat_name} by {actual_increase} to {new_temp}.")
        target.msg(f"Staff boosted your {proper_stat_name} by {actual_increase} to {new_temp}.")
        
        # Emit messages to room and MudInfo
        self._emit_boost_message(target, proper_stat_name, new_temp, actual_increase, description)
    
    def _handle_remove_boost(self, caller, args):
        """Handle the /remove switch for staff to remove boosts from players."""
        if not caller.check_permstring("Builders"):
            caller.msg("You don't have permission to remove boosts from other characters.")
            return
            
        if not args or "=" not in args:
            caller.msg("Usage: +boost/remove <player>=<id>")
            return
            
        player_name, id_str = args.split("=", 1)
        player_name = player_name.strip()
        
        try:
            boost_id = int(id_str.strip())
        except ValueError:
            caller.msg("Please specify a valid boost ID number.")
            return
            
        # Find the target character
        target = search_object(player_name, typeclass="typeclasses.characters.Character")
        if not target:
            caller.msg(f"Could not find character '{player_name}'.")
            return
        if len(target) > 1:
            caller.msg(f"Multiple matches found for '{player_name}'. Please be more specific.")
            return
            
        target = target[0]  # Get the first (and only) match
        
        self._ensure_attribute_boosts(target)
        
        # Find the boost with this ID
        found_stat = None
        for stat, boost_info in target.db.attribute_boosts.items():
            if boost_info.get('id') == boost_id:
                found_stat = stat
                break
                
        if not found_stat:
            caller.msg(f"No boost with ID {boost_id} found on {target.name}.")
            return
            
        # Get the boost info
        boost_info = target.db.attribute_boosts[found_stat]
        amount = boost_info.get('amount', 0)
        
        # Get stat location
        stat_name = found_stat.lower()
        category, stat_type = self._get_stat_location(stat_name)
        if not category or not stat_type:
            caller.msg(f"Error: Cannot find stat location for {stat_name}")
            return
            
        # Get current values and set new value based on category
        if category == 'attributes':
            # Work directly with the stats dictionary for attributes
            stats_dict = target.db.stats
            perm_value = stats_dict[category][stat_type][found_stat]['perm']
            stats_dict[category][stat_type][found_stat]['temp'] = perm_value
            new_value = perm_value
        else:
            # For non-attributes, use get_stat/set_stat
            current_temp = target.get_stat(category, stat_type, found_stat, temp=True)
            perm_value = target.get_stat(category, stat_type, found_stat, temp=False)
            
            if current_temp is None or perm_value is None:
                caller.msg(f"Error: Cannot find values for {found_stat}")
                return
                
            # For pools, adjust both permanent and temporary values
            if category == 'pools' and stat_type == 'dual' and stat_name in ['rage', 'gnosis', 'willpower']:
                new_value = max(perm_value - amount, 1)  # Ensure pools don't go below 1
                target.set_stat(category, stat_type, found_stat, new_value, temp=False)
                target.set_stat(category, stat_type, found_stat, new_value, temp=True)
            else:
                # For other stats, adjust temporary value back to permanent
                new_value = perm_value
                target.set_stat(category, stat_type, found_stat, new_value, temp=True)
                
        # Recycle the boost ID
        target.db.recycled_boost_ids.append(boost_id)
        
        # Remove the boost
        del target.db.attribute_boosts[found_stat]
        
        caller.msg(f"Removed boost #{boost_id} from {target.name} - {found_stat} returned to {new_value}.")
        target.msg(f"Staff removed a boost from your {found_stat}, returning it to {new_value}.")
    
    def _handle_removeall_boosts(self, caller, args):
        """Handle the /removeall switch for staff to remove all boosts from a player."""
        if not caller.check_permstring("Builders"):
            caller.msg("You don't have permission to remove boosts from other characters.")
            return
            
        player_name = args.strip()
        if not player_name:
            caller.msg("Usage: +boost/removeall <player>")
            return
            
        # Find the target character
        target = search_object(player_name, typeclass="typeclasses.characters.Character")
        if not target:
            caller.msg(f"Could not find character '{player_name}'.")
            return
        if len(target) > 1:
            caller.msg(f"Multiple matches found for '{player_name}'. Please be more specific.")
            return
            
        target = target[0]  # Get the first (and only) match
        
        self._ensure_attribute_boosts(target)
        
        if not target.db.attribute_boosts:
            caller.msg(f"{target.name} has no active stat boosts to remove.")
            return
            
        # Process each boost
        for stat_name, boost_info in list(target.db.attribute_boosts.items()):
            amount = boost_info.get('amount', 0)
            boost_id = boost_info.get('id', '?')
            
            # Get stat location
            category, stat_type = self._get_stat_location(stat_name.lower())
            if not category or not stat_type:
                continue
                
            # Handle stats based on category
            if category == 'attributes':
                # Work directly with the stats dictionary for attributes
                stats_dict = target.db.stats
                perm_value = stats_dict[category][stat_type][stat_name]['perm']
                stats_dict[category][stat_type][stat_name]['temp'] = perm_value
                new_value = perm_value
            else:
                # For non-attributes, use get_stat/set_stat
                current_temp = target.get_stat(category, stat_type, stat_name, temp=True)
                perm_value = target.get_stat(category, stat_type, stat_name, temp=False)
                
                if current_temp is None or perm_value is None:
                    continue
                    
                # For pools, adjust both permanent and temporary values
                if category == 'pools' and stat_type == 'dual' and stat_name.lower() in ['rage', 'gnosis', 'willpower']:
                    new_value = max(perm_value - amount, 1)  # Ensure pools don't go below 1
                    target.set_stat(category, stat_type, stat_name, new_value, temp=False)
                    target.set_stat(category, stat_type, stat_name, new_value, temp=True)
                else:
                    # For other stats, adjust temporary value back to permanent
                    new_value = perm_value
                    target.set_stat(category, stat_type, stat_name, new_value, temp=True)
                    
            # Recycle the boost ID
            target.db.recycled_boost_ids.append(boost_id)
            
            # Remove the boost
            del target.db.attribute_boosts[stat_name]
            
        caller.msg(f"Removed all active boosts from {target.name}.")
        target.msg("Staff has removed all your active stat boosts.")

    def _emit_boost_message(self, char, stat, new_value, amount, source=None):
        """Send messages to the room and MudInfo channel about the boost."""
        # Create the room message
        room = char.location
        if source:
            room_msg = f"{char.name} glows with supernatural energy as their {stat} increases to {new_value}. ({source})"
        else:
            room_msg = f"{char.name} glows with supernatural energy as their {stat} increases to {new_value}."
        
        # Emit to everyone in the room except the character
        room.msg_contents(room_msg, exclude=[char])
        
        # Post to MudInfo channel
        try:
            from evennia.utils.create import create_channel
            mudinfo = create_channel("MudInfo", autosubscribe=False)
            if mudinfo:
                mudinfo.msg(f"[{char.name}] Boost: {stat} +{amount} to {new_value}" + (f" ({source})" if source else ""))
        except Exception:
            # If channel messaging fails, continue without error
            pass

    def _handle_refresh_boosts(self, caller):
        """Handle the /refresh switch to refresh all active boosts."""
        self._ensure_attribute_boosts(caller)
        
        if not caller.db.attribute_boosts:
            caller.msg("You have no active stat boosts to refresh.")
            return

        # Track which stats we've updated
        updated_stats = []
        
        # Process each boost
        for stat_name, boost_info in list(caller.db.attribute_boosts.items()):
            amount = boost_info.get('amount', 0)
            boost_id = boost_info.get('id', '?')
            source = boost_info.get('source', 'Unknown')
            
            # Get stat location
            category, stat_type = self._get_stat_location(stat_name.lower())
            if not category or not stat_type:
                continue

            # Handle stats based on category
            if category == 'attributes':
                # Work directly with the stats dictionary for attributes
                stats_dict = caller.db.stats
                perm_value = stats_dict[category][stat_type][stat_name]['perm']
                new_temp = perm_value + amount
                
                # Set the new temporary value
                stats_dict[category][stat_type][stat_name]['temp'] = new_temp
                updated_stats.append(f"{stat_name} now at {new_temp} (base {perm_value} + {amount})")
            else:
                # For non-attributes, use get_stat/set_stat
                perm_value = caller.get_stat(category, stat_type, stat_name, temp=False)
                
                if perm_value is None:
                    continue

                # For pools, adjust both permanent and temporary values
                if category == 'pools' and stat_type == 'dual' and stat_name.lower() in ['rage', 'gnosis', 'willpower']:
                    new_value = perm_value + amount
                    caller.set_stat(category, stat_type, stat_name, new_value, temp=True)
                    updated_stats.append(f"{stat_name} now at {new_value} (base {perm_value} + {amount})")
                else:
                    # For other stats, just adjust temporary value based on current permanent
                    new_value = perm_value + amount
                    caller.set_stat(category, stat_type, stat_name, new_value, temp=True)

        if updated_stats:
            caller.msg("Refreshed all active boosts:")
            for stat in updated_stats:
                caller.msg(f"- {stat}")
        else:
            caller.msg("No stats needed refreshing.")

    def _apply_boost_to_stat(self, character, stat_name, amount, source=None):
        """Apply a boost to a stat, checking for any existing boosts first."""
        # Get stat location
        category, stat_type = self._get_stat_location(stat_name.lower())
        if not category or not stat_type:
            return None, f"Cannot find stat location for {stat_name}"

        # Get proper case for stat name
        proper_stat_name = self._get_proper_case(stat_name)
        
        # Calculate cap
        cap = 10
        if stat_name.lower() in ['rage', 'gnosis']:  # Special caps for certain pools
            cap = 20
            
        # Get current values
        if category == 'attributes':
            # Work directly with the stats dictionary for attributes
            stats_dict = character.db.stats
            current_perm = stats_dict[category][stat_type][proper_stat_name]['perm']
            current_temp = stats_dict[category][stat_type][proper_stat_name]['temp']
            
            # Store boost information - initialize if needed
            self._ensure_attribute_boosts(character)
            
            # Add the boost on top of the current temp value (which might include form modifiers)
            new_temp = min(current_temp + amount, cap)
            
            # Set the new temporary value
            stats_dict[category][stat_type][proper_stat_name]['temp'] = new_temp
            
            return new_temp, current_temp
        else:
            # For non-attributes, use get_stat/set_stat
            current_perm = character.get_stat(category, stat_type, proper_stat_name, temp=False)
            current_temp = character.get_stat(category, stat_type, proper_stat_name, temp=True)
            
            if current_perm is None or current_temp is None:
                return None, f"Cannot find values for {proper_stat_name}"
                
            # For pools, adjust both permanent and temporary values
            if category == 'pools' and stat_type == 'dual' and stat_name.lower() in ['rage', 'gnosis', 'willpower']:
                new_value = min(current_perm + amount, cap)
                character.set_stat(category, stat_type, proper_stat_name, new_value, temp=True)
                return new_value, current_perm
            else:
                # For other stats, add boost to current temp value
                new_value = min(current_temp + amount, cap)
                character.set_stat(category, stat_type, proper_stat_name, new_value, temp=True)
                return new_value, current_temp

    def _remove_boost(self, stat_name, amount):
        """Remove the stat boost after the duration."""
        # Get stat location
        category, stat_type = self._get_stat_location(stat_name.lower())
        if not category or not stat_type:
            return

        # Get current values
        current_temp = self.caller.get_stat(category, stat_type, stat_name, temp=True)
        perm_value = self.caller.get_stat(category, stat_type, stat_name, temp=False)
        
        if current_temp is None or perm_value is None:
            return

        # For pools, adjust both permanent and temporary values
        if category == 'pools' and stat_type == 'dual' and stat_name.lower() in ['rage', 'gnosis', 'willpower']:
            new_value = max(0, current_temp - amount)  # Just subtract the boost amount
            self.caller.set_stat(category, stat_type, stat_name, new_value, temp=False)
            self.caller.set_stat(category, stat_type, stat_name, new_value, temp=True)
        else:
            # For other stats, get the form-adjusted value
            if category == 'attributes':
                # Get form-modified value by subtracting just the boost amount
                stats_dict = self.caller.db.stats
                current_value = stats_dict[category][stat_type][stat_name]['temp']
                new_value = max(perm_value, current_value - amount)  # Don't go below perm value
                # Set the new value
                stats_dict[category][stat_type][stat_name]['temp'] = new_value
            else:
                # For non-attributes, just remove the boost amount
                new_value = max(perm_value, current_temp - amount)  # Don't go below perm value
                self.caller.set_stat(category, stat_type, stat_name, new_value, temp=True)
        
        # Remove from active boosts if present
        self._ensure_attribute_boosts(self.caller)
        if stat_name in self.caller.db.attribute_boosts:
            boost_id = self.caller.db.attribute_boosts[stat_name].get('id', '?')
            del self.caller.db.attribute_boosts[stat_name]
            self.caller.msg(f"Boost #{boost_id} expired: Your {stat_name} returns to normal ({new_value}).")

    def _handle_gurahl_rage_boost(self, caller):
        """Handle the Gurahl-specific rage-based attribute boost."""
        # Check if character is a Gurahl
        shifter_type = caller.get_stat('identity', 'lineage', 'Type', temp=False)
        if shifter_type != 'Gurahl':
            caller.msg("Only Gurahl can use this ability.")
            return
            
        if not self.args or "=" not in self.args:
            caller.msg("Usage: +boost/rage <stat>=<amount>")
            return
            
        stat_name, amount_str = self.args.split("=")
        stat_name = stat_name.strip().lower()
        
        # Special handling for health boost
        if stat_name == "health":
            try:
                amount = int(amount_str)
            except ValueError:
                caller.msg("The amount must be a number.")
                return
                
            if amount <= 0:
                caller.msg("The amount must be a positive number.")
                return
                
            # Check if character has enough Rage
            current_rage = caller.get_stat('pools', 'dual', 'Rage', temp=True)
            if current_rage < amount:
                caller.msg(f"You don't have enough Rage. Current Rage: {current_rage}")
                return
                
            # Spend Rage
            new_rage = current_rage - amount
            caller.set_stat('pools', 'dual', 'Rage', new_rage, temp=True)
            
            # Initialize bonus_health_from_rage if it doesn't exist or is None
            if not hasattr(caller.db, 'bonus_health_from_rage') or caller.db.bonus_health_from_rage is None:
                caller.db.bonus_health_from_rage = 0
            
            # Add the health levels
            old_bonus = caller.db.bonus_health_from_rage
            caller.db.bonus_health_from_rage += amount
            
            # Store the current time as timestamp for the health boost
            import time
            caller.db.health_boost_timestamp = time.time()
            
            # Get the current injury level to determine which type of health levels to add
            injury_level = caller.db.injury_level or "Healthy"
            
            # Map injury level to health level type
            level_type_map = {
                "Healthy": "bruised",
                "Bruised": "bruised",
                "Hurt": "hurt",
                "Injured": "injured",
                "Wounded": "wounded",
                "Mauled": "mauled",
                "Crippled": "crippled",
                "Incapacitated": "crippled"  # Default to crippled if they're incapacitated
            }
            
            level_type = level_type_map.get(injury_level, "bruised").lower()
            
            # Store the health level type for the damage system to use
            caller.db.rage_health_level_type = level_type
            
            # Initialize health_level_bonuses if needed
            if not hasattr(caller.db, 'health_level_bonuses'):
                caller.db.health_level_bonuses = {
                    'bruised': 0,
                    'hurt': 0,
                    'injured': 0,
                    'wounded': 0,
                    'mauled': 0,
                    'crippled': 0
                }
            
            # Recalculate the total health levels to ensure proper display
            from world.wod20th.utils.damage import calculate_total_health_levels
            calculate_total_health_levels(caller)
            
            # Get a new boost ID and add it to the attribute_boosts dictionary
            self._ensure_attribute_boosts(caller)
            boost_id = self._get_next_boost_id(caller)
            
            # Store in attribute_boosts so it shows up in +boosts and can be ended with +boost/endall
            caller.db.attribute_boosts["Health Levels"] = {
                'id': boost_id,
                'amount': amount,
                'source': "Rage Health Boost",
                'is_health_boost': True,  # Special flag to identify health boosts
                'level_type': level_type  # Store the level type for reference
            }
            
            # Capitalize the level type for display
            display_level_type = level_type.capitalize()
            
            caller.msg(f"You spend {amount} Rage to gain {amount} additional {display_level_type} health levels for the scene.")
            
            # Schedule clearance after 8 hours (scene duration)
            utils.delay(28800, self._clear_gurahl_health_boost, caller)
            
            # Emit message to room
            room_msg = f"{caller.name} growls deeply as their body bulks up, gaining additional resilience at the {display_level_type} level."
            caller.location.msg_contents(room_msg)
            
            # Post to MudInfo channel
            try:
                from evennia.utils.create import create_channel
                mudinfo = create_channel("MudInfo", autosubscribe=False)
                if mudinfo:
                    mudinfo.msg(f"[{caller.name}] Rage Health Boost: +{amount} {display_level_type} health levels")
            except Exception:
                # If channel messaging fails, continue without error
                pass
                
            return
        
        # Only allow Strength or Stamina for attribute boosts
        if stat_name not in ['strength', 'stamina']:
            caller.msg("Gurahl can only use Rage to boost Strength, Stamina, or health.")
            return
            
        if not self.args or "=" not in self.args:
            caller.msg("Usage: +boost/rage <stat>=<amount>")
            return
            
        amount_str = self.args.split("=")[1].strip()
            
        try:
            amount = int(amount_str)
        except ValueError:
            caller.msg("The amount must be a number.")
            return
            
        if amount <= 0:
            caller.msg("The amount must be a positive number.")
            return
            
        # Check if character has enough Rage
        current_rage = caller.get_stat('pools', 'dual', 'Rage', temp=True)
        if current_rage < amount:
            caller.msg(f"You don't have enough Rage. Current Rage: {current_rage}")
            return
            
        # Get proper case for the stat name
        proper_stat_name = self._get_proper_case(stat_name)
        
        # Get current form's value for the stat and store it
        current_form = getattr(caller.db, 'current_form', 'Homid')
        current_form_value = caller.db.stats['attributes']['physical'][proper_stat_name]['temp']
        perm_value = caller.db.stats['attributes']['physical'][proper_stat_name]['perm']
        
        # Calculate max allowed boost (up to twice the current form's value)
        max_boost = current_form_value * 2
        
        # Calculate new value
        new_value = current_form_value + amount
        
        # Check if the new value exceeds the maximum allowed
        if new_value > max_boost:
            # Cap at maximum allowed
            excess = new_value - max_boost
            actual_boost = amount - excess
            
            # Refund excess Rage points
            if excess > 0:
                caller.msg(f"You cannot boost {proper_stat_name} beyond {max_boost}. Refunding {excess} Rage points.")
                amount = actual_boost
                
            # Apply the capped boost
            new_value = max_boost
        
        # Set the new temporary value
        caller.db.stats['attributes']['physical'][proper_stat_name]['temp'] = new_value
        
        # Spend Rage
        new_rage = current_rage - amount
        caller.set_stat('pools', 'dual', 'Rage', new_rage, temp=True)
        
        # Set duration for 1 turn (fixed duration regardless of Rage spent)
        duration = 60  # 60 seconds per turn
        
        # Get a new boost ID
        boost_id = self._get_next_boost_id(caller)
        
        # Store the boost with timer and original form value
        self._ensure_attribute_boosts(caller)
        
        # Store the boost with the original form value
        caller.db.attribute_boosts[proper_stat_name] = {
            'id': boost_id,
            'amount': amount,
            'source': "Rage Boost",
            'form_value': current_form_value,  # Store original form value to restore later
            'is_gurahl_rage': True  # Mark as a Gurahl rage boost for special handling
        }
            
        # Set a timer to remove the boost
        utils.delay(duration, self._remove_gurahl_rage_boost, caller, proper_stat_name, amount, boost_id)
        
        caller.msg(f"You spend {amount} Rage to boost your {proper_stat_name} to {new_value} for 1 turn.")
        
        # Emit messages
        self._emit_boost_message(caller, proper_stat_name, new_value, amount, "Rage Boost")
        
        # Emit message to room
        room_msg = f"{caller.name} uses their rage to boost their {proper_stat_name} to {new_value} for 1 turn."
        caller.location.msg_contents(room_msg)

    def _remove_gurahl_rage_boost(self, caller, stat_name, amount, boost_id):
        """Remove Gurahl rage-based attribute boost."""
        # Make sure the boost still exists
        if not hasattr(caller.db, 'attribute_boosts') or stat_name not in caller.db.attribute_boosts:
            return
            
        boost_info = caller.db.attribute_boosts[stat_name]
        
        # Check if it's the same boost (by ID)
        if boost_info.get('id') != boost_id:
            return
            
        # Get the original form value that we stored
        original_form_value = boost_info.get('form_value')
        
        # Restore the original form value
        caller.db.stats['attributes']['physical'][stat_name]['temp'] = original_form_value
        
        # Remove the boost
        del caller.db.attribute_boosts[stat_name]
        
        # Recycle the boost ID
        if hasattr(caller.db, 'recycled_boost_ids'):
            caller.db.recycled_boost_ids.append(boost_id)
        
        caller.msg(f"Boost #{boost_id} expired: Your {stat_name} returns to normal ({original_form_value}).")

    def _handle_gurahl_health_boost(self, caller):
        """Handle Gurahl-specific health level boost. 
        This method is deprecated - health is now handled directly by _handle_gurahl_rage_boost."""
        # Redirect to the new handler
        if not self.args or "=" not in self.args:
            caller.msg("Usage: +boost/rage health=<amount>")
            return
            
        # Create the appropriate argument for _handle_gurahl_rage_boost
        amount_str = self.args.split("=")[1].strip()
        self.args = f"health={amount_str}"
        self._handle_gurahl_rage_boost(caller)

    def _clear_gurahl_health_boost(self, caller):
        """Clear Gurahl rage-based health boosts."""
        if hasattr(caller.db, 'bonus_health_from_rage') and caller.db.bonus_health_from_rage is not None and caller.db.bonus_health_from_rage > 0:
            old_bonus = caller.db.bonus_health_from_rage
            
            # Get the level type that was being boosted
            level_type = getattr(caller.db, 'rage_health_level_type', 'bruised').lower()
            
            # Reset the rage-based health boost
            caller.db.bonus_health_from_rage = 0
            caller.db.rage_health_level_type = None
            
            # Clear the timestamp
            if hasattr(caller.db, 'health_boost_timestamp'):
                delattr(caller.db, 'health_boost_timestamp')
            
            # Reset the specific level type in health_level_bonuses
            if hasattr(caller.db, 'health_level_bonuses') and level_type in caller.db.health_level_bonuses:
                # Save the base bruised bonus before recalculation
                base_bruised = caller.db.health_level_bonuses.get('bruised', 0)
                if level_type == 'bruised':
                    # For bruised, we need to preserve the bonus from things like Huge Size
                    from world.wod20th.utils.damage import calculate_total_health_levels
                    calculate_total_health_levels(caller)  # This will set the proper base bruised level
                else:
                    # For other levels, just set to 0
                    caller.db.health_level_bonuses[level_type] = 0
            
            # Also remove from attribute_boosts if it exists there
            self._ensure_attribute_boosts(caller)
            for stat_name, boost_info in list(caller.db.attribute_boosts.items()):
                if boost_info.get('is_health_boost', False):
                    del caller.db.attribute_boosts[stat_name]
                    break
            
            # Recalculate total health levels to ensure other bonuses (like Huge Size merit) are preserved
            from world.wod20th.utils.damage import calculate_total_health_levels
            calculate_total_health_levels(caller)
            
            # Capitalize level type for display
            display_level_type = level_type.capitalize()
            
            caller.msg(f"Your additional {old_bonus} {display_level_type} health levels from Rage expenditure fade away.")
            
            # Add a message to clarify if they still have bonus health from other sources
            if hasattr(caller.db, 'bonus_health') and caller.db.bonus_health is not None and caller.db.bonus_health > 0:
                sources = []
                
                # Check for Huge Size merit - check both locations
                huge_size = caller.get_stat('merits', 'physical', 'Huge Size', temp=False)
                if not huge_size:
                    huge_size = caller.get_stat('merits', 'merit', 'Huge Size', temp=False)
                if huge_size:
                    sources.append("Huge Size merit")
                
                if sources:
                    source_text = ", ".join(sources)
                    caller.msg(f"You still have {caller.db.bonus_health} bonus health levels from {source_text}.")
            
            return True
        return False

    def func(self):
        caller = self.caller
        
        # Handle staff commands
        if "set" in self.switches:
            self._handle_set_boost(caller, self.args)
            return
            
        if "remove" in self.switches:
            self._handle_remove_boost(caller, self.args)
            return
            
        if "removeall" in self.switches:
            self._handle_removeall_boosts(caller, self.args)
            return

        # Handle /refresh switch
        if "refresh" in self.switches:
            self._handle_refresh_boosts(caller)
            return

        # Handle +boosts command with target name (staff only)
        if self.cmdstring in ['+boosts', 'boosts'] and self.args:
            if not caller.check_permstring("Builders"):
                caller.msg("You don't have permission to view other characters' boosts.")
                return
                
            # Find the target character (works for both online and offline)
            target = search_object(self.args, typeclass="typeclasses.characters.Character")
            if not target:
                caller.msg(f"Could not find character '{self.args}'.")
                return
            if len(target) > 1:
                caller.msg(f"Multiple matches found for '{self.args}'. Please be more specific.")
                return
                
            target = target[0]  # Get the first (and only) match
            self._handle_boosts_command(caller, target)
            return

        # Handle regular +boosts command
        if self.cmdstring in ['+boosts', 'boosts']:
            self._handle_boosts_command(caller)
            return

        # Handle /endall switch
        if "endall" in self.switches:
            self._handle_endall_boosts(caller)
            return

        # Handle /end switch
        if "end" in self.switches:
            self._handle_end_boost(caller, self.args)
            return
            
        # Handle Gurahl rage-based attribute boost
        if "rage" in self.switches:
            self._handle_gurahl_rage_boost(caller)
            return
            
        # Handle Gurahl rage-based health boost (remove this section since it's now part of rage)
        if "health" in self.switches:
            # Check if character is a Gurahl before proceeding
            shifter_type = caller.get_stat('identity', 'lineage', 'Type', temp=False)
            if shifter_type != 'Gurahl':
                caller.msg("Only Gurahl can use this ability.")
                return
                
            self._handle_gurahl_health_boost(caller)
            return

        # Get character's splat for regular boost
        splat = caller.get_stat('other', 'splat', 'Splat', temp=False)
        if not splat:
            caller.msg("Error: Could not determine character type.")
            return

        # Check if character can boost attributes
        if not self._can_boost(caller, splat):
            caller.msg(f"Your character type ({splat}) cannot boost attributes at this time.")
            if splat == 'Shifter':
                caller.msg("You need a Totem background to boost attributes.")
            return

        if not self.args or "=" not in self.args:
            caller.msg("Usage: +boost <stat>=<amount>[/<description>] or +boost/end <id>")
            return

        stat_name, amount_info = self.args.split("=")
        stat_name = stat_name.strip().lower()
        
        # Parse amount and optional description
        amount_parts = amount_info.split("/")
        amount = amount_parts[0].strip()
        
        # Get custom description if provided
        if len(amount_parts) > 1:
            custom_desc = "/".join(amount_parts[1:]).strip()
        else:
            custom_desc = None

        # Get proper case for the stat name
        proper_stat_name = self._get_proper_case(stat_name)

        # Get valid stats for this splat type
        valid_stats = self._get_valid_stats(caller, splat)
        if valid_stats is not None and stat_name not in valid_stats:
            caller.msg(f"Your splat type can only boost: {', '.join(valid_stats)}")
            return

        try:
            amount = int(amount)
        except ValueError:
            caller.msg("The amount must be a number.")
            return

        if amount <= 0:
            caller.msg("The amount must be a positive number.")
            return

        # Handle vampire blood expenditure
        if splat == 'Vampire':
            current_blood = caller.get_stat('pools', 'dual', 'Blood', temp=True)
            if current_blood < amount:
                caller.msg(f"You don't have enough blood. Current blood: {current_blood}")
                return
            # Decrease blood pool
            new_blood = current_blood - amount
            caller.set_stat('pools', 'dual', 'Blood', new_blood, temp=True)

        # Get stat location
        category, stat_type = self._get_stat_location(stat_name)
        if not category or not stat_type:
            caller.msg(f"Cannot find stat: {stat_name}")
            return

        # Get current stat values
        current_perm = caller.get_stat(category, stat_type, proper_stat_name, temp=False)
        current_temp = caller.get_stat(category, stat_type, proper_stat_name, temp=True)
        
        if current_perm is None or current_temp is None:
            caller.msg(f"Error: Could not find {proper_stat_name} value.")
            return

        # Get a new boost ID
        boost_id = self._get_next_boost_id(caller)

        # Calculate cap
        cap = 10
        if stat_name in ['rage', 'gnosis']:  # Special caps for certain pools
            cap = 20

        # For pools (Rage, Gnosis, Willpower), boost the permanent value
        if category == 'pools' and stat_type == 'dual' and stat_name.lower() in ['rage', 'gnosis', 'willpower']:
            new_perm_value = min(current_perm + amount, cap)
            actual_increase = new_perm_value - current_perm
            
            if actual_increase == 0:
                caller.msg(f"Your {proper_stat_name} is already at maximum ({cap}).")
                return

            # Set both permanent and temporary values for pools
            caller.set_stat(category, stat_type, proper_stat_name, new_perm_value, temp=False)
            caller.set_stat(category, stat_type, proper_stat_name, new_perm_value, temp=True)
        else:
            # For other stats, always add boost to permanent value
            # Get values directly from the stats dictionary
            stats_dict = caller.db.stats
            if category == 'attributes':
                current_perm = stats_dict[category][stat_type][proper_stat_name]['perm']
                current_temp = stats_dict[category][stat_type][proper_stat_name]['temp']
            else:
                current_perm = caller.get_stat(category, stat_type, proper_stat_name, temp=False)
                current_temp = caller.get_stat(category, stat_type, proper_stat_name, temp=True)
            
            # Ensure attribute_boosts exists before checking
            self._ensure_attribute_boosts(caller)
            
            if proper_stat_name in caller.db.attribute_boosts:
                # If already boosted, add to current boost amount
                current_boost = caller.db.attribute_boosts[proper_stat_name]['amount']
                new_boost = current_boost + amount
                new_temp = min(current_perm + new_boost, cap)
                actual_increase = amount
            else:
                # If not boosted, add boost amount to current value
                # For vampires, use the current value as base to avoid double-boosting
                if splat == 'Vampire':
                    new_temp = min(current_temp + amount, cap)
                else:
                    new_temp = min(current_perm + amount, cap)
                actual_increase = amount

            # Check if we're at the cap
            if new_temp > cap:
                caller.msg(f"Your {proper_stat_name} cannot be boosted beyond {cap}.")
                return

            # Set the value directly in the stats dictionary for attributes
            if category == 'attributes':
                stats_dict[category][stat_type][proper_stat_name]['temp'] = new_temp
            else:
                caller.set_stat(category, stat_type, proper_stat_name, new_temp, temp=True)

        # Handle duration based on splat type
        duration = self._get_boost_duration(splat)
        if duration:
            utils.delay(duration, self._remove_boost, proper_stat_name, actual_increase)
            caller.msg(f"Boost #{boost_id}: You boost your {proper_stat_name} to {new_temp} for one hour.")
            
            # Emit messages to room and MudInfo
            self._emit_boost_message(caller, proper_stat_name, new_temp, actual_increase, custom_desc)
        else:
            # For indefinite boosts, store the boost information
            self._ensure_attribute_boosts(caller)
            
            # Set the source - custom description, totem, or splat
            if custom_desc:
                source = custom_desc
            elif splat == 'Shifter':
                background_stats = caller.db.stats['backgrounds'].get('background', {})
                totem = self._find_instanced_stat(background_stats, 'Totem')
                if totem:
                    totem_name = next((key[6:-1] for key in background_stats.keys() if key.startswith('Totem(')), 'Unknown')
                    source = f'Totem ({totem_name})'
                else:
                    source = splat
            else:
                source = splat
                
            # Update existing boost or create new one
            if proper_stat_name in caller.db.attribute_boosts:
                caller.db.attribute_boosts[proper_stat_name]['amount'] += actual_increase
                caller.db.attribute_boosts[proper_stat_name]['source'] = source
            else:
                caller.db.attribute_boosts[proper_stat_name] = {
                    'id': boost_id,
                    'amount': actual_increase,
                    'source': source
                }
            caller.msg(f"Boost #{boost_id}: You boost your {proper_stat_name} to {new_temp} indefinitely.")
            
            # Emit messages to room and MudInfo
            self._emit_boost_message(caller, proper_stat_name, new_temp, actual_increase, source)