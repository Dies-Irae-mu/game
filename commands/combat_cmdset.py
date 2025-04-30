"""
World of Darkness Combat Command Set

This module provides commands for engaging in WoD 20th Anniversary Edition combat.
"""

from evennia import CmdSet
from evennia import default_cmds
from world.wod20th.utils.dice_rolls import roll_dice, interpret_roll_results
from world.combat.combat_handler import CombatHandler
from world.combat.maneuvers import MANEUVERS, MANEUVER_GROUPS, get_maneuver
from world.combat.martial_arts_maneuvers import (
    ALL_MARTIAL_ARTS_MANEUVERS, MARTIAL_ARTS_MANEUVER_GROUPS, 
    get_martial_arts_maneuver, check_martial_arts_requirements
)


class CmdCombat(default_cmds.MuxCommand):
    """
    Manage combat and perform combat actions.
    
    Usage:
      +combat                          - Show combat status
      +combat/start                    - Start combat in your location
      +combat/attack <target>          - Attack a target with default attack (punch)
      +combat/attack/<maneuver> <target> - Use specific maneuver on target
      +combat/maneuvers                - List available maneuvers
      +combat/maneuvers <type>         - List maneuvers of a specific type
      +combat/martial <maneuver>       - Use a martial arts maneuver
      +combat/martial <maneuver> <target> - Use a martial arts maneuver on a target
      +combat/martial/list             - List available martial arts maneuvers
      +combat/martial/list <type>      - List martial arts maneuvers of specific type
      +combat/dodge                    - Prepare to dodge incoming attacks
      +combat/block                    - Prepare to block incoming attacks
      +combat/parry                    - Prepare to parry incoming attacks
      +combat/rage [<amount>]          - Spend Rage for extra actions (default: 1)
      +combat/end                      - End your turn
      +combat/pass                     - Pass your turn without acting
      +combat/flee                     - Attempt to flee combat
      +combat/stop                     - End combat in your location (admin only)
      +combat/join                     - Join ongoing combat in your location
      +combat/actions                  - List available combat actions
      +combat/help                     - Show this help message
    
    Combat follows World of Darkness 20th Anniversary Edition rules, with
    initiative determined by Dexterity + Wits + 1d10. Characters take turns
    in initiative order, with the option to use combat maneuvers or defensive
    actions. Garou can spend Rage for extra actions.
    
    Examples:
      +combat/attack Bob                - Attack Bob with a punch
      +combat/attack/claw Bob           - Attack Bob with claws (for werewolves)
      +combat/attack/kick Bob           - Attack Bob with a kick
      +combat/martial thunder_kick Bob  - Use the Thunder Kick martial arts maneuver
      +combat/martial/list              - See all available martial arts maneuvers
      +combat/martial/list kick         - See all kick-type martial arts maneuvers
    """
    
    key = "+combat"
    aliases = ["combat"]
    locks = "cmd:all()"
    help_category = "Combat"
    
    def func(self):
        """Implement the command"""
        caller = self.caller
        
        if not self.switches:
            # Display current combat status
            self.show_combat_status()
            return
        
        if "help" in self.switches:
            # Show combat help
            caller.msg(self.__doc__)
            return
        
        if "start" in self.switches:
            # Start combat in the location
            self.start_combat()
            return
        
        if "stop" in self.switches:
            # End combat in the location
            self.stop_combat()
            return
        
        if "join" in self.switches:
            # Join ongoing combat
            self.join_combat()
            return
        
        if "actions" in self.switches:
            # Show available actions
            self.show_actions()
            return
            
        if "maneuvers" in self.switches:
            # Show available maneuvers
            self.show_maneuvers()
            return
            
        if "martial" in self.switches:
            # Handle martial arts commands
            if "list" in self.switches:
                self.show_martial_arts_maneuvers()
            else:
                self.do_martial_arts_maneuver()
            return
        
        # Check if character is in combat
        if not self.is_in_combat():
            caller.msg("You are not in combat. Use +combat/start to begin combat or +combat/join to join an ongoing combat.")
            return
        
        # Handle combat actions
        if "attack" in self.switches:
            # Attack target
            self.do_attack()
        elif "dodge" in self.switches:
            # Dodge
            self.do_dodge()
        elif "block" in self.switches:
            # Block
            self.do_block()
        elif "parry" in self.switches:
            # Parry
            self.do_parry()
        elif "rage" in self.switches:
            # Spend rage
            self.do_spend_rage()
        elif "end" in self.switches:
            # End turn
            self.do_end_turn()
        elif "pass" in self.switches:
            # Pass turn
            self.do_pass()
        elif "flee" in self.switches:
            # Flee combat
            self.do_flee()
        else:
            # Unknown switch
            caller.msg(f"Unknown combat command. See +combat/help for usage.")
    
    def is_in_combat(self):
        """Check if character is in combat."""
        try:
            # Debug output
            self.caller.msg(f"DEBUG: in_combat attribute: {getattr(self.caller.db, 'in_combat', None)}")
            return hasattr(self.caller, "db") and self.caller.db.in_combat is True
        except Exception as e:
            self.caller.msg(f"Error checking combat status: {e}")
            return False
    
    def get_combat_handler(self):
        """Get the combat handler for the location."""
        location = self.caller.location
        
        if not location:
            self.caller.msg("You have no location to fight in!")
            return None
        
        # Check if a combat handler already exists
        try:
            combat_handlers = location.scripts.get("combat_handler")
            
            # Debug output
            self.caller.msg(f"DEBUG: combat_handlers type: {type(combat_handlers)}")
            
            # Handle QuerySet case - this is what we're getting from Django
            if hasattr(combat_handlers, '__iter__') and not isinstance(combat_handlers, str):
                self.caller.msg("DEBUG: Handling as QuerySet/iterable")
                # Convert QuerySet to list and get the first valid handler
                handlers_list = list(combat_handlers)
                self.caller.msg(f"DEBUG: Converted to list, length: {len(handlers_list)}")
                
                for handler in handlers_list:
                    self.caller.msg(f"DEBUG: Handler: {handler}, type: {type(handler)}")
                    if hasattr(handler, "db") and not isinstance(handler, str):
                        self.caller.msg("DEBUG: Found valid handler with db attribute")
                        return handler
            
            # Handle case where it's already a valid script
            elif hasattr(combat_handlers, "db") and not isinstance(combat_handlers, str):
                self.caller.msg("DEBUG: Returned single valid script")
                return combat_handlers
                
            # If we got here, no valid handler was found
            self.caller.msg("DEBUG: No valid combat handler found, returning None")
            return None
            
        except Exception as e:
            self.caller.msg(f"Error getting combat handler: {str(e)}")
            import traceback
            self.caller.msg(traceback.format_exc())
            return None
    
    def show_combat_status(self):
        """Show the current combat status."""
        caller = self.caller
        location = caller.location
        
        combat_handler = self.get_combat_handler()
        
        # Debug output
        caller.msg(f"DEBUG: Combat handler in show_combat_status: {combat_handler}, type: {type(combat_handler)}")
        
        if not combat_handler or not hasattr(combat_handler, "db") or isinstance(combat_handler, str):
            caller.msg("There is no active combat in this location.")
            caller.msg("Use +combat/start to begin combat.")
            return
        
        try:
            # Check if combat is active
            if not combat_handler.db.active:
                caller.msg("There is no active combat in this location.")
                caller.msg("Use +combat/start to begin combat.")
                return
            
            # Show combat status
            caller.msg("|wCombat Status:|n")
            
            # Show turn number and phase
            caller.msg(f"Turn: {combat_handler.db.turn_number}, Phase: {combat_handler.db.phase}")
            
            # Show initiative order
            try:
                combat_handler.display_initiative()
            except Exception as e:
                caller.msg(f"Error displaying initiative: {str(e)}")
            
            # If character is in combat, show their status
            if self.is_in_combat():
                char_id = caller.id
                if char_id in combat_handler.db.combatants:
                    data = combat_handler.db.combatants[char_id]
                    
                    caller.msg("\n|wYour Combat Status:|n")
                    caller.msg(f"Initiative: {data['initiative']}")
                    
                    # Show remaining actions
                    caller.msg(f"Actions remaining: {data['remaining_actions']}")
                    
                    # Show Rage spent
                    caller.msg(f"Rage spent this turn: {data['rage_actions']}")
                    
                    # Show selected action
                    if data["selected_action"]:
                        caller.msg(f"Selected action: {data['selected_action']}")
                    
                    # Show defense action
                    if data["defense_action"]:
                        caller.msg(f"Defense action: {data['defense_action']}")
        except Exception as e:
            caller.msg(f"Error retrieving combat status: {str(e)}")
            import traceback
            caller.msg(traceback.format_exc())
    
    def start_combat(self):
        """Start combat in the location."""
        caller = self.caller
        location = caller.location
        
        if not location:
            caller.msg("You have no location to fight in!")
            return
        
        # Debug output
        caller.msg("DEBUG: Starting combat...")
        
        # Clear any existing combat handlers
        caller.msg("DEBUG: Clearing existing combat handlers...")
        try:
            for script in location.scripts.all():
                if script.key == "combat_handler":
                    caller.msg(f"DEBUG: Found existing script: {script}, type: {type(script)}")
                    script.stop()
            
            # Make sure it's gone
            location.scripts.delete("combat_handler")
        except Exception as e:
            caller.msg(f"Error clearing existing handlers: {e}")
        
        # Create a new combat handler
        caller.msg("DEBUG: Creating new combat handler...")
        # Create returns a tuple of (script, created), we want the script
        handler, created = CombatHandler.create(key="combat_handler", obj=location, persistent=True)
        caller.msg(f"DEBUG: New combat handler type: {type(handler)}, created: {created}")
        
        # Begin combat
        success = handler.begin_combat(caller)
        
        if success:
            caller.msg("Combat has begun!")
        else:
            caller.msg("Failed to start combat.")
    
    def stop_combat(self):
        """End combat in the location."""
        caller = self.caller
        
        # Only admin can force end combat
        if not caller.check_permstring("Admin"):
            caller.msg("Only admin can force end combat.")
            return
        
        combat_handler = self.get_combat_handler()
        
        # Debug output
        caller.msg(f"DEBUG: Combat handler in stop_combat: {combat_handler}, type: {type(combat_handler)}")
        
        if not combat_handler or not hasattr(combat_handler, "db") or isinstance(combat_handler, str):
            caller.msg("There is no active combat to end.")
            return
        
        try:
            if not combat_handler.db.active:
                caller.msg("There is no active combat to end.")
                return
            
            # End combat
            success = combat_handler.end_combat()
            
            if success:
                caller.msg("Combat has been ended.")
            else:
                caller.msg("Failed to end combat.")
        except Exception as e:
            caller.msg(f"Error ending combat: {str(e)}")
            import traceback
            caller.msg(traceback.format_exc())
    
    def join_combat(self):
        """Join ongoing combat."""
        caller = self.caller
        
        combat_handler = self.get_combat_handler()
        
        # Debug output
        caller.msg(f"DEBUG: Combat handler in join_combat: {combat_handler}, type: {type(combat_handler)}")
        
        if not combat_handler or not hasattr(combat_handler, "db") or isinstance(combat_handler, str):
            caller.msg("There is no active combat to join.")
            return
        
        try:
            if not combat_handler.db.active:
                caller.msg("There is no active combat to join.")
                return
            
            if self.is_in_combat():
                caller.msg("You are already in combat.")
                return
            
            # Add character to combat
            success = combat_handler.add_combatant(caller)
            
            if success:
                caller.msg("You have joined the combat.")
            else:
                caller.msg("Failed to join combat.")
        except Exception as e:
            caller.msg(f"Error joining combat: {str(e)}")
            import traceback
            caller.msg(traceback.format_exc())
    
    def show_actions(self):
        """Show available combat actions."""
        caller = self.caller
        
        # Check if in combat
        if not self.is_in_combat():
            caller.msg("You are not in combat. Use +combat/start to begin combat or +combat/join to join an ongoing combat.")
            return
        
        combat_handler = self.get_combat_handler()
        
        if not combat_handler or not hasattr(combat_handler, "db") or isinstance(combat_handler, str):
            caller.msg("Cannot find combat handler.")
            return
        
        # Debug output
        caller.msg(f"DEBUG: Combat handler in show_actions: {combat_handler}, type: {type(combat_handler)}")
        
        if not hasattr(combat_handler, "db") or isinstance(combat_handler, str):
            caller.msg("Invalid combat handler. Please notify staff.")
            return
        
        # Check if it's character's turn
        char_id = caller.id
        is_my_turn = False
        
        try:
            if (hasattr(combat_handler, "db") and 
                hasattr(combat_handler.db, "turn_order") and
                combat_handler.db.turn_order and 
                combat_handler.db.current_turn < len(combat_handler.db.turn_order)):
                current_id = combat_handler.db.turn_order[combat_handler.db.current_turn]
                is_my_turn = (char_id == current_id)
        except Exception as e:
            caller.msg(f"Error checking turn status: {str(e)}")
            is_my_turn = False
        
        # Show available actions
        caller.msg("|wAvailable Combat Actions:|n")
        
        # Attack maneuvers - show available maneuvers based on character
        available_maneuvers = combat_handler.get_available_maneuvers(caller)
        
        # Group maneuvers by type for display
        maneuvers_by_type = {}
        for name in available_maneuvers:
            maneuver = get_maneuver(name)
            if not maneuver:
                continue
                
            if maneuver.attack_type != "defense":  # Don't include defensive maneuvers here
                mtype = maneuver.attack_type
                if mtype not in maneuvers_by_type:
                    maneuvers_by_type[mtype] = []
                maneuvers_by_type[mtype].append(name)
        
        # Display attack maneuvers by type
        for mtype, maneuvers in sorted(maneuvers_by_type.items()):
            caller.msg(f"\n|y{mtype.title()} Attacks:|n")
            for i, name in enumerate(sorted(maneuvers)):
                if i < 3:  # Show at most 3 per type to avoid clutter
                    caller.msg(f"  |w+combat/attack/{name} <target>|n - Use {name}")
            if len(maneuvers) > 3:
                caller.msg(f"  (Use |w+combat/maneuvers {mtype}|n to see all {len(maneuvers)} options)")
        
        # Defense actions (always available)
        caller.msg("\n|cDefense Actions:|n")
        caller.msg("  |w+combat/dodge|n - Prepare to dodge incoming attacks")
        caller.msg("  |w+combat/block|n - Prepare to block incoming attacks")
        caller.msg("  |w+combat/parry|n - Prepare to parry incoming attacks with a weapon")
        
        # Special actions
        caller.msg("\n|mSpecial Actions:|n")
        # Only show rage option for characters with rage
        rage = caller.get_stat('pools', 'dual', 'Rage', temp=True) or 0
        if rage > 0:
            caller.msg(f"  |w+combat/rage [<amount>]|n - Spend Rage for extra actions (Current: {rage})")
        caller.msg("  |w+combat/flee|n - Attempt to flee combat")
        
        # Turn management
        caller.msg("\n|gTurn Management:|n")
        caller.msg("  |w+combat/end|n - End your turn")
        caller.msg("  |w+combat/pass|n - Pass your turn without acting")
        
        # Add martial arts section
        caller.msg("\n|yMartial Arts:|n")
        caller.msg("  |w+combat/martial <maneuver> <target>|n - Use a martial arts maneuver")
        caller.msg("  |w+combat/martial/list|n - See available martial arts maneuvers")
        
        # Show status of actions
        if is_my_turn:
            char_data = combat_handler.db.combatants[char_id]
            
            caller.msg(f"\n|wIt's your turn! You have {char_data['remaining_actions']} action(s) remaining.|n")
            
            # Show current rage and max spendable rage
            rage = caller.get_stat('pools', 'dual', 'Rage', temp=True) or 0
            perm_rage = caller.get_stat('pools', 'dual', 'Rage', temp=False) or 0
            max_rage_per_turn = (perm_rage + 1) // 2
            current_rage_spent = char_data["rage_actions"]
            
            if rage > 0:
                caller.msg(f"Current Rage: {rage}/{perm_rage} (Can spend {max_rage_per_turn - current_rage_spent} more this turn)")
            
            # Show status effects if any
            if char_data["status_effects"]:
                caller.msg("\n|rActive Status Effects:|n")
                for effect, duration in char_data["status_effects"].items():
                    caller.msg(f"  {effect.title()}: {duration} turns remaining")
        else:
            caller.msg("\n|rIt's not your turn yet. You can still use defense actions.|n")
    
    def show_maneuvers(self):
        """Show available combat maneuvers to the character."""
        caller = self.caller
        
        # Check if a type was specified
        maneuver_type = None
        if self.args:
            maneuver_type = self.args.strip().lower()
        
        combat_handler = self.get_combat_handler()
        
        # Get all available maneuvers for this character
        if combat_handler and hasattr(combat_handler, "db") and not isinstance(combat_handler, str):
            available_maneuvers = combat_handler.get_available_maneuvers(caller)
        else:
            # If not in combat, show all maneuvers
            available_maneuvers = list(MANEUVERS.keys())
        
        # Check if the user is asking for details about a specific maneuver
        specific_maneuver = get_maneuver(maneuver_type)
        if specific_maneuver:
            # Show detailed information about this maneuver
            caller.msg(specific_maneuver.get_help_text())
            
            # Check if it's available to the character
            if maneuver_type in available_maneuvers:
                caller.msg("\nYou can use this maneuver.")
            else:
                caller.msg("\nYou cannot currently use this maneuver. Check the requirements.")
            
            return
        
        # If type specified, filter by that type
        if maneuver_type:
            if maneuver_type in MANEUVER_GROUPS:
                maneuvers_to_show = [name for name in available_maneuvers if name in MANEUVER_GROUPS[maneuver_type]]
                type_name = maneuver_type.title()
            else:
                caller.msg(f"Unknown maneuver type: {maneuver_type}")
                caller.msg(f"Available types: {', '.join(MANEUVER_GROUPS.keys())}")
                return
        else:
            maneuvers_to_show = available_maneuvers
            type_name = "Available"
        
        if not maneuvers_to_show:
            caller.msg(f"No {type_name} maneuvers available to you.")
            return
        
        caller.msg(f"|w{type_name} Combat Maneuvers:|n")
        
        # Display maneuvers grouped by type
        maneuvers_by_type = {}
        for name in sorted(maneuvers_to_show):
            maneuver = get_maneuver(name)
            if not maneuver:
                continue
                
            mtype = maneuver.attack_type
            if mtype not in maneuvers_by_type:
                maneuvers_by_type[mtype] = []
            maneuvers_by_type[mtype].append(maneuver)
        
        # Display each group
        for mtype, maneuvers in sorted(maneuvers_by_type.items()):
            caller.msg(f"\n|y{mtype.title()} Maneuvers:|n")
            for maneuver in maneuvers:
                # Short display format
                difficulty_mod = f", Diff: {maneuver.difficulty_mod:+d}" if maneuver.difficulty_mod != 0 else ""
                damage_mod = f", Dmg: {maneuver.damage_mod:+d}" if maneuver.damage_mod != 0 else ""
                caller.msg(f"  |w{maneuver.name}|n ({maneuver.damage_type}{difficulty_mod}{damage_mod})")
        
        # Add usage instructions
        caller.msg("\nUsage: |w+combat/attack/<maneuver> <target>|n")
        caller.msg("For more details on a specific maneuver, use: |w+combat/maneuvers <maneuver name>|n")
    
    def show_martial_arts_maneuvers(self):
        """Show available martial arts maneuvers to the character."""
        caller = self.caller
        
        # Check if a maneuver type was specified
        maneuver_type = None
        if self.args:
            maneuver_type = self.args.strip().lower()
        
        combat_handler = self.get_combat_handler()
        
        # Get available martial arts maneuvers for this character
        if combat_handler and hasattr(combat_handler, "db") and not isinstance(combat_handler, str):
            available_maneuvers = combat_handler.get_available_martial_arts_maneuvers(caller)
        else:
            # If handler not available or not in combat, show all maneuvers
            # We'll still check requirements when displaying the info
            available_maneuvers = list(ALL_MARTIAL_ARTS_MANEUVERS.keys())
        
        # Check if asking for details about a specific maneuver
        specific_maneuver = get_martial_arts_maneuver(maneuver_type)
        if specific_maneuver:
            # Check if the character meets the requirements
            can_use = check_martial_arts_requirements(caller, specific_maneuver)
            
            # Display detailed info
            caller.msg(f"|w{specific_maneuver.name}|n")
            caller.msg(f"Description: {specific_maneuver.description}")
            caller.msg(f"Type: {specific_maneuver.attack_type.title()}")
            caller.msg(f"Attribute: {specific_maneuver.attribute}")
            caller.msg(f"Ability: {specific_maneuver.ability}")
            caller.msg(f"Difficulty: {6 + specific_maneuver.difficulty_mod}")
            
            if specific_maneuver.damage_type != "none":
                damage_desc = f"Damage: {specific_maneuver.damage_type.title()}"
                if specific_maneuver.damage_mod != 0:
                    damage_desc += f" (modifier: {specific_maneuver.damage_mod:+d})"
                caller.msg(damage_desc)
            
            # Show requirements
            if specific_maneuver.requirements:
                reqs = []
                if "ability" in specific_maneuver.requirements:
                    for ability, level in specific_maneuver.requirements["ability"].items():
                        reqs.append(f"{ability} {level}+")
                if "style" in specific_maneuver.requirements:
                    styles = specific_maneuver.requirements["style"]
                    if "any" in styles:
                        reqs.append("Any style")
                    else:
                        reqs.append(f"Style: {', '.join(style.title() for style in styles)}")
                
                caller.msg(f"Requirements: {', '.join(reqs)}")
            
            # Special effects
            if specific_maneuver.special_effects:
                effects = []
                for effect, value in specific_maneuver.special_effects.items():
                    if effect == "knockdown":
                        effects.append("Can knock down opponent")
                    elif effect == "stun":
                        effects.append(f"Can stun opponent for {value} turns")
                    elif effect == "disarm":
                        effects.append("Can disarm opponent")
                    elif effect == "immobilize":
                        effects.append(f"Can immobilize opponent for {value} turns")
                    elif effect == "bonus_damage":
                        effects.append("Deals bonus damage based on successes")
                    elif effect == "bleeding":
                        effects.append(f"Causes bleeding for {value} turns")
                    elif effect == "self_damage":
                        effects.append("May cause self-damage if unsuccessful")
                    elif effect == "bypass_armor":
                        effects.append("Bypasses armor")
                    elif effect == "bonus_soak":
                        effects.append("Provides bonus soak dice")
                    elif effect == "redirect_attack":
                        effects.append("Can redirect attacks back to attacker")
                    elif effect == "deflect_missile":
                        effects.append("Can deflect projectiles")
                    elif effect == "kiai_effects":
                        effects.append("Special kiai effects (intimidation, etc.)")
                    # Add more effects as needed
                
                if effects:
                    caller.msg(f"Special Effects: {', '.join(effects)}")
            
            # Usage status
            if can_use:
                caller.msg("\n|gYou can use this maneuver.|n")
            else:
                caller.msg("\n|rYou do not meet the requirements for this maneuver.|n")
            
            # Command to use
            if specific_maneuver.attack_type == "defense":
                caller.msg(f"\nUsage: |w+combat/martial {maneuver_type}|n")
            else:
                caller.msg(f"\nUsage: |w+combat/martial {maneuver_type} <target>|n")
            
            return
        
        # If a type is specified but not a specific maneuver, filter by that type
        if maneuver_type:
            # Check if it's one of our predefined groups
            if maneuver_type in MARTIAL_ARTS_MANEUVER_GROUPS:
                filtered_maneuvers = [name for name in available_maneuvers 
                                     if name in MARTIAL_ARTS_MANEUVER_GROUPS[maneuver_type]]
                type_display = maneuver_type.replace('_', ' ').title()
            # Check if it's an attack type
            else:
                filtered_maneuvers = [name for name in available_maneuvers
                                     if get_martial_arts_maneuver(name) and 
                                     get_martial_arts_maneuver(name).attack_type == maneuver_type]
                type_display = maneuver_type.title()
                
            if not filtered_maneuvers:
                caller.msg(f"No martial arts maneuvers of type '{maneuver_type}' are available.")
                caller.msg("Available types: standard, do, weapon, strike, kick, throw, defense, grapple, melee, special")
                return
                
            caller.msg(f"|w{type_display} Martial Arts Maneuvers:|n")
            maneuvers_to_display = filtered_maneuvers
        else:
            # Show all maneuvers, grouped by category
            caller.msg("|wAvailable Martial Arts Maneuvers:|n")
            maneuvers_to_display = available_maneuvers
        
        # Group maneuvers by type for display
        maneuvers_by_type = {}
        for name in sorted(maneuvers_to_display):
            maneuver = get_martial_arts_maneuver(name)
            if not maneuver:
                continue
                
            mtype = maneuver.attack_type
            if mtype not in maneuvers_by_type:
                maneuvers_by_type[mtype] = []
            
            # Check if the character meets requirements
            can_use = check_martial_arts_requirements(caller, maneuver)
            
            # Add maneuver with a flag indicating if it can be used
            maneuvers_by_type[mtype].append((name, maneuver, can_use))
        
        # Display each group
        for mtype, maneuvers in sorted(maneuvers_by_type.items()):
            caller.msg(f"\n|y{mtype.title()} Maneuvers:|n")
            for name, maneuver, can_use in sorted(maneuvers, key=lambda x: x[0]):
                # Format with color indicating if character can use it
                name_color = "|g" if can_use else "|r"
                
                # Display basic info
                diff_text = f", Diff: {6 + maneuver.difficulty_mod}" 
                damage_text = f", {maneuver.damage_type.title()}" if maneuver.damage_type != "none" else ""
                damage_mod = f", Dmg: {maneuver.damage_mod:+d}" if maneuver.damage_mod != 0 else ""
                
                caller.msg(f"  {name_color}{name}|n ({maneuver.ability}{diff_text}{damage_text}{damage_mod})")
        
        # Show usage instructions
        caller.msg("\nFor details on a specific maneuver: |w+combat/martial/list <maneuver>|n")
        caller.msg("To use an attack maneuver: |w+combat/martial <maneuver> <target>|n")
        caller.msg("To use a defense maneuver: |w+combat/martial <maneuver>|n")
    
    def do_martial_arts_maneuver(self):
        """Process a martial arts maneuver."""
        caller = self.caller
        
        # Get combat handler
        combat_handler = self.get_combat_handler()
        if not combat_handler or not hasattr(combat_handler, "db") or isinstance(combat_handler, str):
            caller.msg("Cannot find valid combat handler.")
            return
        
        # Parse the arguments
        args = self.args.strip() if self.args else ""
        
        if not args:
            caller.msg("You must specify a martial arts maneuver to use.")
            caller.msg("Use +combat/martial/list to see available maneuvers.")
            return
        
        # Extract maneuver and target
        parts = args.split(None, 1)
        maneuver_name = parts[0].lower()
        target = parts[1] if len(parts) > 1 else None
        
        # Check if maneuver exists
        maneuver = get_martial_arts_maneuver(maneuver_name)
        if not maneuver:
            caller.msg(f"Unknown martial arts maneuver: {maneuver_name}")
            caller.msg("Use +combat/martial/list to see available maneuvers.")
            return
        
        # Check if it's a defensive maneuver that doesn't need a target
        if maneuver.attack_type == "defense" and not target:
            success = combat_handler.process_martial_arts_maneuver(caller, maneuver_name, None)
            return
        
        # For other maneuvers, we need a target
        if not target:
            caller.msg(f"You must specify a target for {maneuver.name}.")
            return
        
        # Process the maneuver
        success = combat_handler.process_martial_arts_maneuver(caller, maneuver_name, target)
    
    def do_attack(self):
        """Process attack action."""
        caller = self.caller
        
        # Get combat handler
        combat_handler = self.get_combat_handler()
        
        # Extra debugging
        caller.msg(f"DEBUG: Combat handler in do_attack: {combat_handler}, type: {type(combat_handler)}")
        
        if not combat_handler or not hasattr(combat_handler, "db") or isinstance(combat_handler, str):
            caller.msg("Cannot find valid combat handler.")
            return
        
        # Check arguments
        if not self.args:
            caller.msg("You must specify a target to attack. Usage: +combat/attack <target>")
            return
        
        # Determine maneuver to use
        maneuver = None
        for switch in self.switches:
            if switch in MANEUVERS:
                maneuver = switch
                break
            # Handle 'attack/claw' syntax
            elif switch == "attack" and len(self.switches) > 1:
                for other_switch in self.switches:
                    if other_switch != "attack" and other_switch in MANEUVERS:
                        maneuver = other_switch
                        break
        
        # Default to punch if no maneuver specified
        if not maneuver:
            maneuver = "punch"
        
        # Check if maneuver is valid
        if not get_maneuver(maneuver):
            caller.msg(f"Unknown maneuver: {maneuver}")
            caller.msg("Use +combat/maneuvers to see available maneuvers.")
            return
        
        # Process attack with the specified maneuver
        target = self.args.strip()
        try:
            success = combat_handler.process_action(caller, maneuver, target)
            
            if not success:
                # Error message was sent by handler
                pass
        except Exception as e:
            caller.msg(f"Error processing attack: {str(e)}")
    
    def do_dodge(self):
        """Process dodge action."""
        caller = self.caller
        
        # Get combat handler
        combat_handler = self.get_combat_handler()
        if not combat_handler or not hasattr(combat_handler, "db") or isinstance(combat_handler, str):
            caller.msg("Cannot find valid combat handler.")
            return
        
        # Process dodge
        try:
            success = combat_handler.process_action(caller, "dodge")
            
            if not success:
                # Error message was sent by handler
                pass
        except Exception as e:
            caller.msg(f"Error processing dodge: {str(e)}")
    
    def do_block(self):
        """Process block action."""
        caller = self.caller
        
        # Get combat handler
        combat_handler = self.get_combat_handler()
        if not combat_handler or not hasattr(combat_handler, "db") or isinstance(combat_handler, str):
            caller.msg("Cannot find valid combat handler.")
            return
        
        # Process block
        try:
            success = combat_handler.process_action(caller, "block")
            
            if not success:
                # Error message was sent by handler
                pass
        except Exception as e:
            caller.msg(f"Error processing block: {str(e)}")
    
    def do_parry(self):
        """Process parry action."""
        caller = self.caller
        
        # Get combat handler
        combat_handler = self.get_combat_handler()
        if not combat_handler or not hasattr(combat_handler, "db") or isinstance(combat_handler, str):
            caller.msg("Cannot find valid combat handler.")
            return
        
        # Process parry
        try:
            success = combat_handler.process_action(caller, "parry")
            
            if not success:
                # Error message was sent by handler
                pass
        except Exception as e:
            caller.msg(f"Error processing parry: {str(e)}")
    
    def do_spend_rage(self):
        """Process rage spending."""
        caller = self.caller
        
        # Get combat handler
        combat_handler = self.get_combat_handler()
        if not combat_handler or not hasattr(combat_handler, "db") or isinstance(combat_handler, str):
            caller.msg("Cannot find valid combat handler.")
            return
        
        # Get amount of rage to spend
        amount = 1
        if self.args:
            try:
                amount = int(self.args.strip())
                if amount < 1:
                    caller.msg("Amount must be a positive number.")
                    return
            except ValueError:
                caller.msg("Amount must be a number. Usage: +combat/rage [<amount>]")
                return
        
        # Process rage spending
        try:
            success = combat_handler.process_action(caller, "spend_rage", amount=amount)
            
            if not success:
                # Error message was sent by handler
                pass
        except Exception as e:
            caller.msg(f"Error processing rage spending: {str(e)}")
    
    def do_end_turn(self):
        """End turn."""
        caller = self.caller
        
        # Get combat handler
        combat_handler = self.get_combat_handler()
        if not combat_handler or not hasattr(combat_handler, "db") or isinstance(combat_handler, str):
            caller.msg("Cannot find valid combat handler.")
            return
        
        # Process end turn
        try:
            success = combat_handler.process_action(caller, "end_turn")
            
            if not success:
                # Error message was sent by handler
                pass
        except Exception as e:
            caller.msg(f"Error ending turn: {str(e)}")
    
    def do_pass(self):
        """Pass turn."""
        caller = self.caller
        
        # Get combat handler
        combat_handler = self.get_combat_handler()
        if not combat_handler or not hasattr(combat_handler, "db") or isinstance(combat_handler, str):
            caller.msg("Cannot find valid combat handler.")
            return
        
        # Process pass
        try:
            success = combat_handler.process_action(caller, "pass")
            
            if not success:
                # Error message was sent by handler
                pass
        except Exception as e:
            caller.msg(f"Error passing turn: {str(e)}")
    
    def do_flee(self):
        """Attempt to flee combat."""
        caller = self.caller
        
        # Get combat handler
        combat_handler = self.get_combat_handler()
        if not combat_handler or not hasattr(combat_handler, "db") or isinstance(combat_handler, str):
            caller.msg("Cannot find valid combat handler.")
            return
        
        # Check if in combat
        if not self.is_in_combat():
            caller.msg("You are not in combat.")
            return
        
        # For now, just remove character from combat
        try:
            success = combat_handler.remove_combatant(caller)
            
            if success:
                caller.msg("You flee from combat!")
            else:
                caller.msg("Failed to flee from combat.")
        except Exception as e:
            caller.msg(f"Error fleeing from combat: {str(e)}")


class CombatCmdSet(CmdSet):
    """
    Command set for WoD combat.
    """
    
    key = "combat_cmd_set"
    
    def at_cmdset_creation(self):
        """
        Add combat commands to the command set.
        """
        self.add(CmdCombat()) 