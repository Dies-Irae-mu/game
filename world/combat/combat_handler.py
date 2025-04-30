"""
World of Darkness Combat Handler

This module provides a turn-based combat system for World of Darkness 20th Anniversary Edition games.
It handles initiative, combat actions, and damage resolution.
"""

from evennia import DefaultScript
from evennia.utils.ansi import ANSIString
from evennia.utils.utils import make_iter
import random
from world.wod20th.utils.dice_rolls import roll_dice, interpret_roll_results
from world.wod20th.utils.damage import calculate_total_health_levels, apply_damage_or_healing
from .maneuvers import get_maneuver, MANEUVERS, MANEUVER_GROUPS
from .martial_arts_maneuvers import (get_martial_arts_maneuver, check_martial_arts_requirements, 
                                    get_martial_arts_equipment_bonus, ALL_MARTIAL_ARTS_MANEUVERS, 
                                    MARTIAL_ARTS_MANEUVER_GROUPS)

class CombatHandler(DefaultScript):
    """
    This script handles combat for a location. It manages:
    - Initiative tracking
    - Turn sequencing
    - Combat status
    - Combat actions

    Combat is turn-based, following WoD 20th Anniversary rules.
    """
    
    key = "combat_handler"
    interval = 60  # Lower interval once battle is running
    persistent = True
    
    def at_script_creation(self):
        """Initialize the script and set up combat variables."""
        self.db.active = False
        self.db.combatants = {}
        self.db.turn_order = []
        self.db.current_turn = 0
        self.db.turn_number = 0
        self.db.phase = "initiative"  # Can be: initiative, attack, damage, end
        self.db.action_queue = []
        # Store a reference to the location
        self.db.location = self.obj
    
    def at_start(self):
        """Called when script is started."""
        self.interval = 60  # 1 minute tick until combat begins
    
    def begin_combat(self, starter):
        """Start combat in the location."""
        if self.db.active:
            return False
        
        self.db.active = True
        self.db.starter = starter
        
        # Set interval to be shorter during active combat
        self.interval = 2
        
        location = self.obj
        location.msg_contents("|rCombat has begun!|n")
        
        # Gather all potential combatants in the location
        for obj in location.contents:
            if obj.has_account:  # This is a player character
                self.add_combatant(obj)
            elif hasattr(obj, 'is_npc') and obj.is_npc:  # This is an NPC
                self.add_combatant(obj)
        
        # Roll initiative
        self.roll_initiative()
        
        return True
    
    def add_combatant(self, character, initiative_modifier=0):
        """Add a character to combat."""
        if character.id in self.db.combatants:
            return False
        
        # Initialize combat data for character
        self.db.combatants[character.id] = {
            "character": character,
            "initiative": 0,
            "initiative_roll": 0,
            "initiative_modifier": initiative_modifier,
            "has_acted": False,
            "selected_action": None,
            "action_target": None,
            "defense_action": None,
            "remaining_actions": 0,
            "rage_actions": 0,
            "status_effects": {},
            "combat_flags": set()
        }
        
        character.db.in_combat = True
        character.db.combat_handler = self
        
        self.obj.msg_contents(f"{character.name} has joined the combat.")
        return True
    
    def remove_combatant(self, character):
        """Remove a character from combat."""
        if character.id not in self.db.combatants:
            return False
        
        # Clean up character's combat status
        character.db.in_combat = False
        character.db.combat_handler = None
        
        # Remove from combat
        del self.db.combatants[character.id]
        
        # Remove from turn order if needed
        if character.id in self.db.turn_order:
            self.db.turn_order.remove(character.id)
        
        # Adjust current turn if needed
        if self.db.turn_order:
            if self.db.current_turn >= len(self.db.turn_order):
                self.db.current_turn = 0
        
        # Check if combat should end
        self.check_combat_end()
        
        self.obj.msg_contents(f"{character.name} has left the combat.")
        return True
    
    def roll_initiative(self):
        """Roll initiative for all combatants."""
        self.db.phase = "initiative"
        
        for combatant_id, data in self.db.combatants.items():
            character = data["character"]
            
            # Get Dexterity and Wits values
            dexterity = character.get_stat('attributes', 'physical', 'Dexterity', temp=True) or 0
            wits = character.get_stat('attributes', 'mental', 'Wits', temp=True) or 0
            
            # Roll 1d10 for initiative
            initiative_roll = random.randint(1, 10)
            
            # Calculate total initiative
            total_initiative = initiative_roll + dexterity + wits + data["initiative_modifier"]
            
            # Update combatant data
            data["initiative"] = total_initiative
            data["initiative_roll"] = initiative_roll
            
            # Reset action flags for new combat round
            data["has_acted"] = False
            data["selected_action"] = None
            data["action_target"] = None
            data["defense_action"] = None
            data["remaining_actions"] = 1  # Start with 1 action
            data["rage_actions"] = 0
            data["status_effects"] = {}
            data["combat_flags"] = set()
        
        # Sort combatants by initiative (highest to lowest)
        self.db.turn_order = sorted(
            self.db.combatants.keys(),
            key=lambda x: self.db.combatants[x]["initiative"],
            reverse=True
        )
        
        self.db.current_turn = 0
        self.db.turn_number += 1
        
        # Display initiative order
        self.display_initiative()
        
        # Go to attack phase
        self.begin_attack_phase()
    
    def display_initiative(self):
        """Display the initiative order to all combatants."""
        location = self.obj
        
        # Build the initiative display
        header = "|wInitiative Order for Turn {}:|n".format(self.db.turn_number)
        table = []
        
        for i, combatant_id in enumerate(self.db.turn_order):
            data = self.db.combatants[combatant_id]
            character = data["character"]
            
            # Format: 1. Character Name (Initiative: 12) <- Current Turn
            entry = "{}. {} (Initiative: {})".format(
                i + 1,
                character.name,
                data["initiative"]
            )
            
            # Highlight current turn
            if i == self.db.current_turn:
                entry = "|y{}|n |r<- Current Turn|n".format(entry)
            
            table.append(entry)
        
        # Send to location
        initiative_msg = header + "\n" + "\n".join(table)
        location.msg_contents(initiative_msg)
    
    def begin_attack_phase(self):
        """Start the attack phase of combat."""
        self.db.phase = "attack"
        
        # Get current character
        current_id = self.db.turn_order[self.db.current_turn]
        character = self.db.combatants[current_id]["character"]
        
        # Notify character it's their turn
        character.msg("|gIt's your turn in combat!|n")
        character.msg("Use |w+combat/actions|n to see available actions.")
        
        # Notify everyone else
        for obj in self.obj.contents:
            if obj != character and hasattr(obj, 'msg'):
                obj.msg(f"|wIt is now {character.name}'s turn.|n")
    
    def process_action(self, character, action, target=None, **kwargs):
        """Process a combat action for a character."""
        if not self.db.active:
            character.msg("Combat is not active.")
            return False
        
        char_id = character.id
        if char_id not in self.db.combatants:
            character.msg("You are not in this combat.")
            return False
        
        # Check if it's this character's turn
        current_id = self.db.turn_order[self.db.current_turn]
        if char_id != current_id:
            character.msg("It's not your turn yet.")
            return False
        
        # Process different action types
        if action in ["dodge", "block", "parry"]:
            return self.set_defense(character, action)
        elif action == "spend_rage":
            return self.do_spend_rage(character, kwargs.get("amount", 1))
        elif action == "pass":
            return self.do_pass(character)
        elif action == "end_turn":
            return self.do_end_turn(character)
        elif action == "attack":
            # Handle attacks using maneuvers
            maneuver_name = kwargs.get("maneuver", "punch")  # Default to punch if no maneuver
            return self.process_maneuver(character, maneuver_name, target)
        elif action in MANEUVERS:
            # Direct maneuver was given as the action
            return self.process_maneuver(character, action, target)
        elif action in ALL_MARTIAL_ARTS_MANEUVERS:
            # Martial arts maneuver was given as the action
            return self.process_martial_arts_maneuver(character, action, target)
        else:
            character.msg(f"Unknown action: {action}")
            return False
    
    def process_maneuver(self, character, maneuver_name, target, **kwargs):
        """Process a combat maneuver.
        
        Args:
            character: The character performing the maneuver
            maneuver_name: Name of the maneuver to perform
            target: Target of the maneuver
            **kwargs: Additional parameters
            
        Returns:
            bool: Success or failure
        """
        # Get the maneuver
        maneuver = get_maneuver(maneuver_name)
        if not maneuver:
            character.msg(f"Unknown maneuver: {maneuver_name}")
            return False
        
        if not target:
            character.msg(f"You must specify a target for {maneuver.name}.")
            return False
        
        # Get target character
        target_obj = None
        for obj in self.obj.contents:
            if obj.name.lower() == target.lower():
                target_obj = obj
                break
        
        if not target_obj:
            character.msg(f"Could not find target '{target}'.")
            return False
        
        target_id = target_obj.id
        if target_id not in self.db.combatants:
            character.msg(f"{target_obj.name} is not part of this combat.")
            return False
        
        # Check requirements for the maneuver
        if not self.check_maneuver_requirements(character, maneuver):
            return False
        
        # Calculate dice pool
        attribute_value = character.get_stat('attributes', 'physical', maneuver.attribute, temp=True) or 0
        ability_value = 0
        
        # Get ability value
        if maneuver.ability == "Brawl":
            ability_value = character.get_stat('abilities', 'talent', 'Brawl', temp=True) or 0
        elif maneuver.ability == "Melee":
            ability_value = character.get_stat('abilities', 'talent', 'Melee', temp=True) or 0
        elif maneuver.ability == "Firearms":
            ability_value = character.get_stat('abilities', 'talent', 'Firearms', temp=True) or 0
        elif maneuver.ability == "Athletics":
            ability_value = character.get_stat('abilities', 'talent', 'Athletics', temp=True) or 0
            
        dice_pool = attribute_value + ability_value
        
        # Apply health penalties
        health_penalty = self.get_health_penalty(character)
        dice_pool -= health_penalty
        
        # Ensure minimum of 1 die
        dice_pool = max(1, dice_pool)
        
        # Calculate difficulty
        difficulty = 6 + maneuver.difficulty_mod
        
        # Queue the attack for resolution
        self.db.action_queue.append({
            "action": "maneuver",
            "attacker": character,
            "target": target_obj,
            "maneuver": maneuver,
            "dice_pool": dice_pool,
            "difficulty": difficulty,
        })
        
        # Store the action in combatant data
        self.db.combatants[character.id]["selected_action"] = maneuver.name
        self.db.combatants[character.id]["action_target"] = target_obj
        
        # Resolve the maneuver
        self.resolve_maneuver(character, target_obj, maneuver, dice_pool, difficulty)
        
        # Decrement remaining actions
        self.db.combatants[character.id]["remaining_actions"] -= 1
        
        # Apply special status effects based on maneuver
        self.apply_special_effects(character, target_obj, maneuver)
        
        # Check if character has more actions this turn
        if self.db.combatants[character.id]["remaining_actions"] > 0:
            character.msg(f"You have {self.db.combatants[character.id]['remaining_actions']} actions remaining.")
        else:
            # End turn if no more actions
            self.next_turn()
        
        return True
    
    def check_maneuver_requirements(self, character, maneuver):
        """Check if character meets requirements for the maneuver.
        
        Args:
            character: The character to check
            maneuver: The maneuver object with requirements
            
        Returns:
            bool: True if requirements are met, False otherwise
        """
        if not maneuver.requirements:
            return True
            
        # Check form requirements
        if "form" in maneuver.requirements and hasattr(character, "form"):
            if character.form not in maneuver.requirements["form"]:
                character.msg(f"You cannot use {maneuver.name} in your current form.")
                character.msg(f"Required forms: {', '.join(form.title() for form in maneuver.requirements['form'])}")
                return False
        
        # Check Rage requirements
        if "rage" in maneuver.requirements:
            rage = character.get_stat('pools', 'dual', 'Rage', temp=True) or 0
            if rage < maneuver.requirements["rage"]:
                character.msg(f"You need at least {maneuver.requirements['rage']} Rage to use {maneuver.name}.")
                character.msg(f"Current Rage: {rage}")
                return False
        
        # Check ability requirements
        if "ability" in maneuver.requirements:
            for ability_name, min_value in maneuver.requirements["ability"].items():
                ability_value = 0
                if ability_name in ["Brawl", "Melee", "Firearms", "Athletics"]:
                    ability_value = character.get_stat('abilities', 'talent', ability_name, temp=True) or 0
                
                if ability_value < min_value:
                    character.msg(f"You need at least {min_value} in {ability_name} to use {maneuver.name}.")
                    character.msg(f"Current {ability_name}: {ability_value}")
                    return False
        
        return True
    
    def resolve_maneuver(self, attacker, defender, maneuver, dice_pool, difficulty):
        """Resolve a combat maneuver.
        
        Args:
            attacker: Character performing the maneuver
            defender: Target of the maneuver
            maneuver: The maneuver object
            dice_pool: Dice pool for the attack roll
            difficulty: Difficulty for the attack roll
        """
        # Roll the attack
        rolls, successes, ones = roll_dice(dice_pool, difficulty)
        
        # Get defender's defense if any
        defender_id = defender.id
        defense_action = self.db.combatants[defender_id]["defense_action"]
        defense_successes = 0
        
        if defense_action:
            defense_maneuver = get_maneuver(defense_action)
            if defense_maneuver and defense_maneuver.attack_type == "defense":
                # Calculate defense dice pool
                defense_attribute = defender.get_stat('attributes', 'physical', defense_maneuver.attribute, temp=True) or 0
                defense_ability_value = 0
                
                if defense_maneuver.ability == "Brawl":
                    defense_ability_value = defender.get_stat('abilities', 'talent', 'Brawl', temp=True) or 0
                elif defense_maneuver.ability == "Melee":
                    defense_ability_value = defender.get_stat('abilities', 'talent', 'Melee', temp=True) or 0
                elif defense_maneuver.ability == "Athletics":
                    defense_ability_value = defender.get_stat('abilities', 'talent', 'Athletics', temp=True) or 0
                
                defense_pool = defense_attribute + defense_ability_value
                
                # Apply health penalties
                health_penalty = self.get_health_penalty(defender)
                defense_pool -= health_penalty
                
                # Roll defense
                defense_rolls, defense_successes, defense_ones = roll_dice(defense_pool, difficulty)
                
                # Announce defense attempt
                self.obj.msg_contents(
                    f"|w{defender.name}|n attempts to {defense_action} "
                    f"with |g{defense_successes}|n successes."
                )
        
        # Subtract defense successes from attack successes
        net_successes = max(0, successes - defense_successes)
        
        # Determine damage
        if net_successes > 0:
            # Base damage based on attack type
            if maneuver.attribute == "Strength":
                base_damage = attacker.get_stat('attributes', 'physical', 'Strength', temp=True) or 0
            else:
                base_damage = 2  # Default base damage
                
            # Add damage modifier from maneuver
            base_damage += maneuver.damage_mod
            
            # Get damage type from maneuver
            damage_type = maneuver.damage_type
            
            # Add extra dice for successes beyond the first
            extra_damage_dice = net_successes - 1 + maneuver.extra_damage_dice
            
            # Roll damage
            damage_dice_pool = base_damage + extra_damage_dice
            damage_rolls, damage_successes, damage_ones = roll_dice(damage_dice_pool, 6)
            
            # Apply damage
            self.apply_damage(defender, damage_successes, damage_type)
            
            # Announce result
            self.obj.msg_contents(
                f"|w{attacker.name}|n uses |y{maneuver.name}|n against |w{defender.name}|n "
                f"and hits with |g{net_successes}|n successes, dealing "
                f"|r{damage_successes}|n {damage_type} damage!"
            )
            
        else:
            # Attack missed
            self.obj.msg_contents(
                f"|w{attacker.name}|n uses |y{maneuver.name}|n against |w{defender.name}|n but misses!"
            )
    
    def apply_special_effects(self, attacker, defender, maneuver):
        """Apply special effects from a maneuver.
        
        Args:
            attacker: Character performing the maneuver
            defender: Target of the maneuver
            maneuver: Maneuver with special effects
        """
        if not maneuver.special_effects:
            return
            
        defender_id = defender.id
        
        # Apply knockdown effect
        if maneuver.special_effects.get("knockdown", False):
            self.obj.msg_contents(f"|w{defender.name}|n is knocked down!")
            self.db.combatants[defender_id]["status_effects"]["knockdown"] = 1
            self.db.combatants[defender_id]["combat_flags"].add("knockdown")
            
        # Apply stun effect
        if "stun" in maneuver.special_effects:
            stun_duration = maneuver.special_effects["stun"]
            self.obj.msg_contents(f"|w{defender.name}|n is stunned for {stun_duration} turns!")
            self.db.combatants[defender_id]["status_effects"]["stun"] = stun_duration
            self.db.combatants[defender_id]["combat_flags"].add("stunned")
            
        # Apply disarm effect
        if maneuver.special_effects.get("disarm", False):
            self.obj.msg_contents(f"|w{defender.name}|n is disarmed!")
            self.db.combatants[defender_id]["combat_flags"].add("disarmed")
            
        # Apply other effects as needed
        if "immobilize" in maneuver.special_effects:
            self.obj.msg_contents(f"|w{defender.name}|n is immobilized!")
            self.db.combatants[defender_id]["status_effects"]["immobilized"] = 1
            self.db.combatants[defender_id]["combat_flags"].add("immobilized")
            
        if "reduce_defense" in maneuver.special_effects:
            reduction = maneuver.special_effects["reduce_defense"]
            self.obj.msg_contents(f"|w{defender.name}|n's defense is reduced by {reduction}!")
            self.db.combatants[defender_id]["status_effects"]["defense_penalty"] = reduction
    
    def set_defense(self, character, defense_type):
        """Set a character's defense action.
        
        Args:
            character: Character to set defense for
            defense_type: Type of defense (dodge, block, parry)
            
        Returns:
            bool: Success or failure
        """
        # Check if defense type is valid
        if defense_type not in ["dodge", "block", "parry"]:
            character.msg(f"Invalid defense type: {defense_type}")
            return False
            
        # Set the defense action
        self.db.combatants[character.id]["defense_action"] = defense_type
        
        # Inform character and room
        character.msg(f"You prepare to {defense_type} incoming attacks.")
        self.obj.msg_contents(f"|w{character.name}|n prepares to {defense_type} incoming attacks.")
        
        return True
    
    def do_spend_rage(self, character, amount=1):
        """Process spending rage points for extra actions."""
        # Check if character has rage
        rage = character.get_stat('pools', 'dual', 'Rage', temp=True) or 0
        perm_rage = character.get_stat('pools', 'dual', 'Rage', temp=False) or 0
        
        if rage < amount:
            character.msg(f"You don't have enough Rage. Current Rage: {rage}")
            return False
        
        # Calculate max rage that can be spent in a turn (half permanent Rage, rounded up)
        max_rage_per_turn = (perm_rage + 1) // 2
        current_rage_spent = self.db.combatants[character.id]["rage_actions"]
        
        if current_rage_spent + amount > max_rage_per_turn:
            character.msg(f"You can only spend up to {max_rage_per_turn} Rage points per turn. You've already spent {current_rage_spent}.")
            return False
        
        # Check for speed limitations (can't exceed Dexterity or Wits)
        dexterity = character.get_stat('attributes', 'physical', 'Dexterity', temp=True) or 0
        wits = character.get_stat('attributes', 'mental', 'Wits', temp=True) or 0
        
        # Speed limit is the lower of Dex or Wits
        speed_limit = min(dexterity, wits)
        
        # If current rage actions would exceed speed limit, apply penalty in next action
        if current_rage_spent + amount > speed_limit:
            character.msg(f"You are moving faster than your body can handle! Your next action will have a +3 difficulty penalty.")
            self.db.combatants[character.id]["status_effects"]["difficulty_penalty"] = 3
        
        # Deduct rage points
        new_rage = rage - amount
        character.set_stat('pools', 'dual', 'Rage', new_rage, temp=True)
        
        # Add actions
        self.db.combatants[character.id]["remaining_actions"] += amount
        self.db.combatants[character.id]["rage_actions"] += amount
        
        character.msg(f"You spend {amount} Rage point(s) for extra actions. Rage remaining: {new_rage}")
        self.obj.msg_contents(f"|w{character.name}|n snarls with rage, moving with supernatural speed!")
        
        return True
    
    def do_pass(self, character):
        """Pass the turn without taking an action."""
        character.msg("You pass your turn.")
        self.obj.msg_contents(f"|w{character.name}|n passes their turn.")
        
        self.next_turn()
        return True
    
    def do_end_turn(self, character):
        """End turn even if character has actions remaining."""
        self.next_turn()
        return True
    
    def next_turn(self):
        """Advance to the next character's turn."""
        # Process end-of-turn effects for current character
        self.process_end_of_turn_effects()
        
        # Move to the next character in the turn order
        self.db.current_turn += 1
        
        # Check if we've gone through all characters
        if self.db.current_turn >= len(self.db.turn_order):
            # Start a new combat round
            self.roll_initiative()
        else:
            # Start the next character's turn
            self.begin_attack_phase()
    
    def process_end_of_turn_effects(self):
        """Process effects that occur at the end of a character's turn."""
        # Process duration-based effects
        for combatant_id in self.db.combatants:
            data = self.db.combatants[combatant_id]
            
            # Reduce duration of status effects
            effects_to_remove = []
            for effect, duration in data["status_effects"].items():
                if duration > 0:
                    data["status_effects"][effect] = duration - 1
                    if data["status_effects"][effect] <= 0:
                        effects_to_remove.append(effect)
            
            # Remove expired effects
            for effect in effects_to_remove:
                del data["status_effects"][effect]
                if effect in ["knockdown", "stunned", "immobilized", "disarmed"]:
                    if effect in data["combat_flags"]:
                        data["combat_flags"].remove(effect)
                        # Notify recovery
                        self.obj.msg_contents(f"|w{data['character'].name}|n has recovered from being {effect}.")
    
    def apply_damage(self, character, amount, damage_type):
        """Apply damage to a character."""
        # Use the existing damage application system
        apply_damage_or_healing(character, amount, damage_type)
        
        # Check if character should be removed from combat
        if character.db.injury_level in ["Incapacitated", "Dead", "Final Death", "Torpor"]:
            self.obj.msg_contents(f"|w{character.name}|n is |rincapacitated|n and can no longer fight!")
            
            # Remove from combat at end of turn
            self.remove_combatant(character)
    
    def get_health_penalty(self, character):
        """Calculate dice penalty based on character's health levels."""
        # Get current injury level
        injury_level = character.db.injury_level or "Healthy"
        
        # Apply penalty based on injury level
        if injury_level == "Healthy" or injury_level == "Bruised":
            return 0
        elif injury_level == "Hurt" or injury_level == "Injured":
            return 1
        elif injury_level == "Wounded" or injury_level == "Mauled":
            return 2
        elif injury_level == "Crippled":
            return 5
        elif injury_level == "Incapacitated" or injury_level == "Dead" or injury_level == "Torpor":
            return 10  # Effectively prevents any dice rolling
        
        return 0
    
    def check_combat_end(self):
        """Check if combat should end (only one combatant left or all on same side)."""
        if len(self.db.combatants) <= 1:
            self.end_combat()
            return True
        
        return False
    
    def end_combat(self):
        """End the combat encounter."""
        if not self.db.active:
            return False
        
        self.db.active = False
        
        # Clean up all combatants
        for combatant_id in list(self.db.combatants.keys()):
            character = self.db.combatants[combatant_id]["character"]
            character.db.in_combat = False
            character.db.combat_handler = None
        
        # Reset combat variables
        self.db.combatants = {}
        self.db.turn_order = []
        self.db.current_turn = 0
        self.db.turn_number = 0
        self.db.phase = "inactive"
        
        # Announce end of combat
        self.obj.msg_contents("|rCombat has ended!|n")
        
        # Reset interval
        self.interval = 60
        
        return True
    
    def at_repeat(self):
        """Called every self.interval seconds."""
        # Check if combat is active
        if not self.db.active:
            return
        
        # Check if combat should continue
        if len(self.db.combatants) <= 1:
            self.end_combat()
            return
            
    def get_available_maneuvers(self, character):
        """Get list of available maneuvers for a character.
        
        Args:
            character: Character to check
            
        Returns:
            list: List of maneuver names available to the character
        """
        available = []
        
        for name, maneuver in MANEUVERS.items():
            if self.check_maneuver_requirements(character, maneuver):
                available.append(name)
                
        return available
    
    def process_martial_arts_maneuver(self, character, maneuver_name, target, **kwargs):
        """Process a martial arts maneuver.
        
        Args:
            character: The character performing the maneuver
            maneuver_name: Name of the maneuver to perform
            target: Target of the maneuver
            **kwargs: Additional parameters
            
        Returns:
            bool: Success or failure
        """
        # Get the maneuver
        maneuver = get_martial_arts_maneuver(maneuver_name)
        if not maneuver:
            character.msg(f"Unknown martial arts maneuver: {maneuver_name}")
            return False
        
        # For defensive techniques with no target
        if maneuver.attack_type == "defense" and not target:
            return self.set_martial_arts_defense(character, maneuver_name)
        
        # Attacks and other techniques that need a target
        if not target and maneuver.attack_type != "defense":
            character.msg(f"You must specify a target for {maneuver.name}.")
            return False
        
        # Get target character
        target_obj = None
        for obj in self.obj.contents:
            if obj.name.lower() == target.lower():
                target_obj = obj
                break
        
        if not target_obj:
            character.msg(f"Could not find target '{target}'.")
            return False
        
        target_id = target_obj.id
        if target_id not in self.db.combatants:
            character.msg(f"{target_obj.name} is not part of this combat.")
            return False
        
        # Check requirements for the maneuver
        if not check_martial_arts_requirements(character, maneuver):
            character.msg(f"You don't meet the requirements for {maneuver.name}.")
            return False
        
        # Calculate dice pool
        attribute_value = character.get_stat('attributes', 'physical' if maneuver.attribute.lower() in ['strength', 'dexterity', 'stamina'] else 
                                            ('social' if maneuver.attribute.lower() in ['charisma', 'manipulation', 'appearance'] else 'mental'), 
                                            maneuver.attribute, temp=True) or 0
        
        ability_value = 0
        # Get ability value
        if maneuver.ability == "Martial Arts":
            ability_value = character.get_stat('abilities', 'talent', 'Martial Arts', temp=True) or 0
        elif maneuver.ability == "Do":
            ability_value = character.get_stat('abilities', 'talent', 'Do', temp=True) or 0
        elif maneuver.ability == "Melee":
            ability_value = character.get_stat('abilities', 'talent', 'Melee', temp=True) or 0
        elif maneuver.ability == "Brawl":
            ability_value = character.get_stat('abilities', 'talent', 'Brawl', temp=True) or 0
        elif maneuver.ability == "Athletics":
            ability_value = character.get_stat('abilities', 'talent', 'Athletics', temp=True) or 0
        elif maneuver.ability == "Awareness":
            ability_value = character.get_stat('abilities', 'talent', 'Awareness', temp=True) or 0
            
        dice_pool = attribute_value + ability_value
        
        # Apply health penalties
        health_penalty = self.get_health_penalty(character)
        dice_pool -= health_penalty
        
        # Check for equipment bonuses
        equipment_bonuses = self.get_martial_arts_equipment_bonuses(character, maneuver)
        
        # Apply equipment bonuses to dice pool
        dice_pool += equipment_bonuses.get("dice_bonus", 0)
        
        # Ensure minimum of 1 die
        dice_pool = max(1, dice_pool)
        
        # Calculate difficulty
        base_difficulty = 6  # Standard difficulty
        difficulty = base_difficulty + maneuver.difficulty_mod + equipment_bonuses.get("difficulty_mod", 0)
        
        # Queue the martial arts action for resolution
        self.db.action_queue.append({
            "action": "martial_arts",
            "attacker": character,
            "target": target_obj if target_obj else None,
            "maneuver": maneuver,
            "dice_pool": dice_pool,
            "difficulty": difficulty,
            "equipment_bonuses": equipment_bonuses
        })
        
        # Store the action in combatant data
        self.db.combatants[character.id]["selected_action"] = maneuver.name
        self.db.combatants[character.id]["action_target"] = target_obj if target_obj else None
        
        # If this is an attack maneuver, resolve it now
        if maneuver.attack_type in ["strike", "kick", "melee", "throw", "sweep", "grapple"]:
            self.resolve_martial_arts_attack(character, target_obj, maneuver, dice_pool, difficulty, equipment_bonuses)
        else:
            # Handle special maneuvers that aren't direct attacks
            self.resolve_special_martial_arts_maneuver(character, target_obj, maneuver, dice_pool, difficulty, equipment_bonuses)
        
        # Decrement remaining actions
        self.db.combatants[character.id]["remaining_actions"] -= 1
        
        # Apply special status effects based on maneuver
        self.apply_martial_arts_effects(character, target_obj, maneuver)
        
        # Check if character has more actions this turn
        if self.db.combatants[character.id]["remaining_actions"] > 0:
            character.msg(f"You have {self.db.combatants[character.id]['remaining_actions']} actions remaining.")
        else:
            # End turn if no more actions
            self.next_turn()
        
        return True
    
    def set_martial_arts_defense(self, character, defense_maneuver_name):
        """Set a martial arts defensive technique.
        
        Args:
            character: Character to set defense for
            defense_maneuver_name: Name of the defense maneuver
            
        Returns:
            bool: Success or failure
        """
        maneuver = get_martial_arts_maneuver(defense_maneuver_name)
        if not maneuver or maneuver.attack_type != "defense":
            character.msg(f"{defense_maneuver_name} is not a valid defensive technique.")
            return False
            
        # Check requirements
        if not check_martial_arts_requirements(character, maneuver):
            character.msg(f"You don't meet the requirements for {maneuver.name}.")
            return False
        
        # Set the defense action
        self.db.combatants[character.id]["defense_action"] = defense_maneuver_name
        
        # Inform character and room
        character.msg(f"You prepare to defend with {maneuver.name}.")
        self.obj.msg_contents(f"|w{character.name}|n prepares to defend with {maneuver.name}.")
        
        return True
    
    def resolve_martial_arts_attack(self, attacker, defender, maneuver, dice_pool, difficulty, equipment_bonuses):
        """Resolve a martial arts attack.
        
        Args:
            attacker: Character performing the attack
            defender: Target of the attack
            maneuver: The martial arts maneuver
            dice_pool: Dice pool for the attack roll
            difficulty: Difficulty for the attack roll
            equipment_bonuses: Dictionary with equipment bonuses
        """
        # Roll the attack
        rolls, successes, ones = roll_dice(dice_pool, difficulty)
        
        # Get defender's defense if any
        defender_id = defender.id
        defense_action = self.db.combatants[defender_id]["defense_action"]
        defense_successes = 0
        
        if defense_action:
            # Check if it's a martial arts defense
            defense_maneuver = get_martial_arts_maneuver(defense_action)
            if not defense_maneuver:
                # Fall back to regular combat defense
                defense_maneuver = get_maneuver(defense_action)
                
            if defense_maneuver and defense_maneuver.attack_type == "defense":
                # Calculate defense dice pool
                if defense_maneuver.attribute == "Dexterity":
                    defense_attribute = defender.get_stat('attributes', 'physical', 'Dexterity', temp=True) or 0
                else:
                    defense_attribute = defender.get_stat('attributes', 'physical', defense_maneuver.attribute, temp=True) or 0
                    
                defense_ability_value = 0
                
                if defense_maneuver.ability == "Martial Arts":
                    defense_ability_value = defender.get_stat('abilities', 'talent', 'Martial Arts', temp=True) or 0
                elif defense_maneuver.ability == "Do":
                    defense_ability_value = defender.get_stat('abilities', 'talent', 'Do', temp=True) or 0
                elif defense_maneuver.ability == "Melee":
                    defense_ability_value = defender.get_stat('abilities', 'talent', 'Melee', temp=True) or 0
                elif defense_maneuver.ability == "Brawl":
                    defense_ability_value = defender.get_stat('abilities', 'talent', 'Brawl', temp=True) or 0
                elif defense_maneuver.ability == "Athletics":
                    defense_ability_value = defender.get_stat('abilities', 'talent', 'Athletics', temp=True) or 0
                
                defense_pool = defense_attribute + defense_ability_value
                
                # Apply health penalties
                health_penalty = self.get_health_penalty(defender)
                defense_pool -= health_penalty
                
                # Check for equipment bonuses for defense
                defense_equipment_bonuses = self.get_martial_arts_equipment_bonuses(defender, defense_maneuver)
                defense_pool += defense_equipment_bonuses.get("dice_bonus", 0)
                
                # Roll defense
                defense_difficulty = 6 + defense_maneuver.difficulty_mod + defense_equipment_bonuses.get("difficulty_mod", 0)
                defense_rolls, defense_successes, defense_ones = roll_dice(defense_pool, defense_difficulty)
                
                # Handle special defense effects
                if "redirect_attack" in defense_maneuver.special_effects and defense_successes > successes:
                    # Soft Fist technique - redirect attack back to attacker
                    self.obj.msg_contents(
                        f"|w{defender.name}|n uses {defense_maneuver.name} to redirect "
                        f"|w{attacker.name}|n's attack back at them!"
                    )
                    # Deal attacker's own attack strength back to them
                    strength = attacker.get_stat('attributes', 'physical', 'Strength', temp=True) or 0
                    redirect_damage = strength + (defense_successes - successes)
                    self.apply_damage(attacker, redirect_damage, maneuver.damage_type)
                    return
                
                # Announce defense attempt
                self.obj.msg_contents(
                    f"|w{defender.name}|n attempts to defend with {defense_maneuver.name} "
                    f"and gets |g{defense_successes}|n successes."
                )
        
        # Subtract defense successes from attack successes
        net_successes = max(0, successes - defense_successes)
        
        # Determine damage for successful attacks
        if net_successes > 0:
            # Base damage based on attack type
            if maneuver.attribute == "Strength":
                base_damage = attacker.get_stat('attributes', 'physical', 'Strength', temp=True) or 0
            else:
                base_damage = 2  # Default base damage
                
            # Add damage modifier from maneuver
            base_damage += maneuver.damage_mod
            
            # Add equipment damage bonuses
            base_damage += equipment_bonuses.get("damage_mod", 0)
            
            # Get damage type from maneuver
            damage_type = maneuver.damage_type
            
            # Add extra dice for successes beyond the first
            extra_damage_dice = net_successes - 1 + maneuver.extra_damage_dice + equipment_bonuses.get("extra_damage_dice", 0)
            
            # Handle special bonus damage for certain techniques
            if "bonus_damage" in maneuver.special_effects:
                if maneuver.special_effects["bonus_damage"] == "successes":
                    extra_damage_dice += net_successes
            
            # Roll damage
            damage_dice_pool = base_damage + extra_damage_dice
            damage_rolls, damage_successes, damage_ones = roll_dice(damage_dice_pool, 6)
            
            # Apply damage
            self.apply_damage(defender, damage_successes, damage_type)
            
            # Handle knockdown effect
            if "knockdown" in maneuver.special_effects and net_successes >= 2:
                self.obj.msg_contents(f"|w{defender.name}|n is knocked down by the force of the attack!")
                self.db.combatants[defender.id]["status_effects"]["knockdown"] = 1
                self.db.combatants[defender.id]["combat_flags"].add("knockdown")
            
            # Announce result
            self.obj.msg_contents(
                f"|w{attacker.name}|n uses |y{maneuver.name}|n against |w{defender.name}|n "
                f"and hits with |g{net_successes}|n successes, dealing "
                f"|r{damage_successes}|n {damage_type} damage!"
            )
            
        else:
            # Attack missed
            self.obj.msg_contents(
                f"|w{attacker.name}|n attempts |y{maneuver.name}|n against |w{defender.name}|n but misses!"
            )
            
        # Handle special case for Typhoon Kick self-damage
        if "self_damage" in maneuver.special_effects and net_successes == 0 and maneuver.name == "Typhoon Kick":
            # Roll attacker's soak
            stamina = attacker.get_stat('attributes', 'physical', 'Stamina', temp=True) or 0
            soak_roll, soak_successes, soak_ones = roll_dice(stamina, 6)
            
            if soak_successes == 0:
                # Failed soak - take self damage
                strength = attacker.get_stat('attributes', 'physical', 'Strength', temp=True) or 0
                self_damage = max(1, strength // 2)  # Half strength, minimum 1
                self.apply_damage(attacker, self_damage, "bashing")
                self.obj.msg_contents(
                    f"|w{attacker.name}|n's failed |y{maneuver.name}|n causes them to take "
                    f"|r{self_damage}|n bashing damage!"
                )
    
    def resolve_special_martial_arts_maneuver(self, character, target, maneuver, dice_pool, difficulty, equipment_bonuses):
        """Resolve special martial arts maneuvers that aren't direct attacks.
        
        Args:
            character: Character performing the maneuver
            target: Target of the maneuver (if any)
            maneuver: The martial arts maneuver
            dice_pool: Dice pool for the roll
            difficulty: Difficulty for the roll
            equipment_bonuses: Dictionary with equipment bonuses
        """
        # Roll for the maneuver
        rolls, successes, ones = roll_dice(dice_pool, difficulty)
        
        # Process based on maneuver type and special effects
        if maneuver.name == "Iron Shirt":
            # Add bonus soak based on Do rating
            do_rating = character.get_stat('abilities', 'talent', 'Do', temp=True) or 0
            character.db.temp_bonus_soak = do_rating
            self.obj.msg_contents(
                f"|w{character.name}|n focuses their chi with |y{maneuver.name}|n, "
                f"gaining |g{do_rating}|n bonus soak dice!"
            )
            
        elif maneuver.name == "Kiaijutsu":
            # Process based on the attribute used
            if maneuver.attribute == "Stamina":
                # Stamina bonus effect
                stamina_bonus = min(3, successes)  # Maximum +3 bonus
                character.db.temp_stamina_bonus = stamina_bonus
                character.db.temp_stamina_duration = 3  # 3 turns
                self.obj.msg_contents(
                    f"|w{character.name}|n's powerful kiai hardens their body, "
                    f"giving them +{stamina_bonus} Stamina for 3 turns!"
                )
            elif maneuver.attribute == "Manipulation":
                # Terror effect
                if target:
                    target_willpower = target.get_stat('traits', None, 'Willpower', temp=True) or 0
                    if successes > 0:
                        difficulty_penalty = min(3, successes)  # Max +3 difficulty
                        target.db.temp_difficulty_penalty = difficulty_penalty
                        target.db.temp_penalty_duration = 1  # 1 turn
                        
                        self.obj.msg_contents(
                            f"|w{character.name}|n's terrifying kiai unsettles |w{target.name}|n, "
                            f"imposing a +{difficulty_penalty} difficulty penalty to their next action!"
                        )
                        
                        if successes > target_willpower:
                            # Target is stunned or flees
                            target.db.temp_stunned = 1
                            self.db.combatants[target.id]["status_effects"]["stunned"] = 1
                            self.obj.msg_contents(
                                f"|w{target.name}|n is stunned by the powerful kiai!"
                            )
                    else:
                        self.obj.msg_contents(
                            f"|w{character.name}|n's kiai attempt fails to intimidate |w{target.name}|n!"
                        )
                else:
                    # Try to affect all weak-willed NPCs
                    affected_count = 0
                    for combatant_id in self.db.combatants:
                        if combatant_id != character.id:
                            combatant = self.db.combatants[combatant_id]["character"]
                            if hasattr(combatant, "is_npc") and combatant.is_npc:
                                willpower = combatant.get_stat('traits', None, 'Willpower', temp=True) or 0
                                if willpower <= 4 and affected_count < successes:
                                    affected_count += 1
                                    # NPC flees
                                    self.remove_combatant(combatant)
                                    self.obj.msg_contents(
                                        f"|w{combatant.name}|n flees in terror from |w{character.name}|n's kiai!"
                                    )
                    
                    if affected_count == 0:
                        self.obj.msg_contents(
                            f"|w{character.name}|n's kiai echoes through the area, but no one flees!"
                        )
            
        elif maneuver.name == "Plum Flower Blossom":
            # Acrobatic movement bonus
            turns_duration = 1 + (successes // 2)
            character.db.temp_acrobatic_bonus = turns_duration
            self.obj.msg_contents(
                f"|w{character.name}|n performs the |y{maneuver.name}|n technique, "
                f"gaining incredible acrobatic mobility for {turns_duration} turns!"
            )
            
        elif maneuver.name == "Arrow Cutting":
            # Handled separately during ranged attack resolution
            self.obj.msg_contents(
                f"|w{character.name}|n prepares to deflect projectiles with |y{maneuver.name}|n!"
            )
            character.db.temp_arrow_cutting = True
            
        elif maneuver.name == "Ten Thousand Weapons":
            # Just announce the stance
            self.obj.msg_contents(
                f"|w{character.name}|n enters the |y{maneuver.name}|n stance, "
                f"ready to use any object as a deadly weapon!"
            )
            character.db.temp_any_weapon = True
        
        elif maneuver.name == "Weapon Art":
            # Just announce the technique
            self.obj.msg_contents(
                f"|w{character.name}|n channels their Do into their weapon mastery!"
            )
            character.db.temp_weapon_art = True
        
        # Add more special maneuver handling as needed
    
    def apply_martial_arts_effects(self, attacker, defender, maneuver):
        """Apply special effects from a martial arts maneuver.
        
        Args:
            attacker: Character performing the maneuver
            defender: Target of the maneuver 
            maneuver: Maneuver with special effects
        """
        if not defender or not maneuver.special_effects:
            return
            
        defender_id = defender.id
        
        # Apply stun effect
        if "stun" in maneuver.special_effects:
            stun_duration = maneuver.special_effects["stun"]
            self.obj.msg_contents(f"|w{defender.name}|n is stunned for {stun_duration} turns!")
            self.db.combatants[defender_id]["status_effects"]["stun"] = stun_duration
            self.db.combatants[defender_id]["combat_flags"].add("stunned")
            
        # Apply immobilize effect
        if "immobilize" in maneuver.special_effects:
            immobilize_duration = maneuver.special_effects["immobilize"]
            self.obj.msg_contents(f"|w{defender.name}|n is immobilized!")
            self.db.combatants[defender_id]["status_effects"]["immobilized"] = immobilize_duration
            self.db.combatants[defender_id]["combat_flags"].add("immobilized")
            
        # Apply disarm effect
        if "disarm" in maneuver.special_effects:
            self.obj.msg_contents(f"|w{defender.name}|n is disarmed!")
            self.db.combatants[defender_id]["combat_flags"].add("disarmed")
            
        # Apply bleeding effect
        if "bleeding" in maneuver.special_effects:
            bleeding_duration = maneuver.special_effects["bleeding"]
            self.obj.msg_contents(f"|w{defender.name}|n is bleeding!")
            self.db.combatants[defender_id]["status_effects"]["bleeding"] = bleeding_duration
            self.db.combatants[defender_id]["combat_flags"].add("bleeding")
            
        # Apply blind effect
        if "blind" in maneuver.special_effects:
            blind_duration = maneuver.special_effects["blind"]
            self.obj.msg_contents(f"|w{defender.name}|n is blinded by blood in their eyes!")
            self.db.combatants[defender_id]["status_effects"]["blinded"] = blind_duration
            self.db.combatants[defender_id]["combat_flags"].add("blinded")
            
        # Apply continuous damage effect
        if "continuous_damage" in maneuver.special_effects:
            damage_value = maneuver.special_effects["continuous_damage"]
            self.obj.msg_contents(f"|w{defender.name}|n will take ongoing damage!")
            self.db.combatants[defender_id]["status_effects"]["continuous_damage"] = {
                "value": damage_value,
                "type": maneuver.damage_type,
                "source": attacker.name
            }
    
    def get_martial_arts_equipment_bonuses(self, character, maneuver):
        """Get bonuses from martial arts equipment.
        
        Args:
            character: The character to check
            maneuver: The maneuver being used
            
        Returns:
            dict: Dictionary with various bonuses
        """
        # Call the utility function, but provide defaults if not found
        try:
            from .martial_arts_maneuvers import get_martial_arts_equipment_bonus
            return get_martial_arts_equipment_bonus(character, maneuver)
        except (ImportError, AttributeError):
            # Default bonuses (no effect)
            return {
                "difficulty_mod": 0,
                "damage_mod": 0,
                "extra_damage_dice": 0,
                "dice_bonus": 0
            }
    
    def get_available_martial_arts_maneuvers(self, character):
        """Get list of available martial arts maneuvers for a character.
        
        Args:
            character: Character to check
            
        Returns:
            list: List of maneuver names available to the character
        """
        available = []
        
        for name, maneuver in ALL_MARTIAL_ARTS_MANEUVERS.items():
            if check_martial_arts_requirements(character, maneuver):
                available.append(name)
                
        return available 