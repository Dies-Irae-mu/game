from evennia import default_cmds
from evennia.utils import utils
from world.wod20th.models import Stat

class CmdPump(default_cmds.MuxCommand):
    """
    Boost physical attributes using supernatural means.

    Usage:
      +boost <stat>=<amount>
      +boost/end <id>
      +boost/endall
      +boosts - List active attribute boosts

    Examples:
      +boost strength=2
      +boost dexterity=1
      +boost stamina=3
      +boost intelligence=2 (Mage/Changeling only)
      +boost brawl=2 (Shifter with totem only)
      +boost/end 1
      +boost/endall
      +boosts

    This command allows characters to temporarily boost their stats
    based on their supernatural type:
    - Vampires: Can boost physical attributes only (Strength, Dexterity, Stamina)
    - Shifters with totem: Can boost any stat (attributes, abilities, pools)
    - Changelings: Can boost any attribute
    - Mages: Can boost any attribute
    - Fomori/Kami: Through blessings

    Use +boost/end <id> to end a specific boost early.
    Use +boost/endall to end all active boosts.
    Use +boosts to see active boosts and their IDs.
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
        elif splat in ['Changeling', 'Mage', 'Possessed', 'Companion', 'Mortal+']:
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
        for stat, boost_info in caller.db.attribute_boosts.items():
            if boost_info.get('id') == boost_id:
                found_stat = stat
                break

        if not found_stat:
            caller.msg(f"No boost found with ID {boost_id}.")
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

    def _handle_boosts_command(self, caller):
        """Handle the +boosts command to list active boosts."""
        self._ensure_attribute_boosts(caller)
        
        if not caller.db.attribute_boosts:
            caller.msg("You have no active stat boosts.")
            return

        caller.msg("Active stat boosts:")
        for stat, boost_info in caller.db.attribute_boosts.items():
            source = boost_info.get('source', 'Unknown')
            amount = boost_info.get('amount', 0)
            boost_id = boost_info.get('id', '?')
            caller.msg(f"#{boost_id} {stat}: +{amount} from {source}")

    def _handle_endall_boosts(self, caller):
        """Handle the /endall switch to end all active boosts."""
        self._ensure_attribute_boosts(caller)
        
        if not caller.db.attribute_boosts:
            caller.msg("You have no active stat boosts to end.")
            return

        # Process each boost
        for stat_name, boost_info in list(caller.db.attribute_boosts.items()):
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

    def func(self):
        caller = self.caller

        # Handle +boosts command
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

        # Get character's splat
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
            caller.msg("Usage: +boost <stat>=<amount> or +boost/end <id>")
            return

        stat_name, amount = self.args.split("=")
        stat_name = stat_name.strip().lower()
        amount = amount.strip()

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

        # Calculate new value, capped at 10 for most stats
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

        # Get a new boost ID
        boost_id = self._get_next_boost_id(caller)

        # Handle duration based on splat type
        duration = self._get_boost_duration(splat)
        if duration:
            utils.delay(duration, self._remove_boost, proper_stat_name, actual_increase)
            caller.msg(f"Boost #{boost_id}: You boost your {proper_stat_name} to {new_temp} for one hour.")
        else:
            # For indefinite boosts, store the boost information
            self._ensure_attribute_boosts(caller)
            
            # For Shifters, store the totem source
            if splat == 'Shifter':
                background_stats = caller.db.stats['backgrounds'].get('background', {})
                totem = self._find_instanced_stat(background_stats, 'Totem')
                if totem:
                    totem_name = next((key[6:-1] for key in background_stats.keys() if key.startswith('Totem(')), 'Unknown')
                    # Update existing boost or create new one
                    if proper_stat_name in caller.db.attribute_boosts:
                        caller.db.attribute_boosts[proper_stat_name]['amount'] += actual_increase
                    else:
                        caller.db.attribute_boosts[proper_stat_name] = {
                            'id': boost_id,
                            'amount': actual_increase,
                            'source': f'Totem ({totem_name})'
                        }
            else:
                # Update existing boost or create new one
                if proper_stat_name in caller.db.attribute_boosts:
                    caller.db.attribute_boosts[proper_stat_name]['amount'] += actual_increase
                else:
                    caller.db.attribute_boosts[proper_stat_name] = {
                        'id': boost_id,
                        'amount': actual_increase,
                        'source': splat
                    }
            caller.msg(f"Boost #{boost_id}: You boost your {proper_stat_name} to {new_temp} indefinitely.")

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
            new_value = max(perm_value - amount, 1)  # Ensure pools don't go below 1
            self.caller.set_stat(category, stat_type, stat_name, new_value, temp=False)
            self.caller.set_stat(category, stat_type, stat_name, new_value, temp=True)
        else:
            # For other stats, just adjust temporary value
            new_value = max(current_temp - amount, perm_value)
            self.caller.set_stat(category, stat_type, stat_name, new_value, temp=True)
        
        # Remove from active boosts if present
        self._ensure_attribute_boosts(self.caller)
        if stat_name in self.caller.db.attribute_boosts:
            boost_id = self.caller.db.attribute_boosts[stat_name].get('id', '?')
            del self.caller.db.attribute_boosts[stat_name]
            self.caller.msg(f"Boost #{boost_id} expired: Your {stat_name} returns to normal ({new_value}).")