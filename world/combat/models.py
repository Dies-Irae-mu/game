"""
World of Darkness Combat Models

This module defines data models for the combat system.
"""


class CombatManeuver:
    """
    Model for a combat maneuver in World of Darkness.
    
    Attributes:
        name (str): Display name of the maneuver
        description (str): Description of what the maneuver does
        attack_type (str): Type of attack - brawl, melee, firearms, etc.
        attribute (str): Primary attribute used for the roll (Dexterity, Strength, etc.)
        ability (str): Skill/ability used for the roll (Brawl, Melee, etc.)
        difficulty_mod (int): Modifier to the base difficulty
        damage_mod (int): Modifier to the base damage
        damage_type (str): Type of damage - bashing, lethal, aggravated
        extra_damage_dice (int): Extra dice to add to damage beyond successes
        special_effects (dict): Dictionary of special effects
        requirements (dict): Requirements to use this maneuver
    """
    
    def __init__(self, name, description, attack_type, attribute, ability, 
                difficulty_mod=0, damage_mod=0, damage_type="bashing", 
                extra_damage_dice=0, special_effects=None, requirements=None):
        self.name = name
        self.description = description
        self.attack_type = attack_type
        self.attribute = attribute
        self.ability = ability
        self.difficulty_mod = difficulty_mod
        self.damage_mod = damage_mod
        self.damage_type = damage_type
        self.extra_damage_dice = extra_damage_dice
        self.special_effects = special_effects or {}
        self.requirements = requirements or {}
    
    def __str__(self):
        return self.name
    
    def get_help_text(self):
        """Get help text for this maneuver."""
        text = f"|w{self.name}|n: {self.description}\n"
        text += f"Attack Type: {self.attack_type.title()}, Uses: {self.attribute}/{self.ability}\n"
        text += f"Damage Type: {self.damage_type.title()}"
        
        if self.difficulty_mod != 0:
            text += f", Difficulty Modifier: {self.difficulty_mod:+d}"
        if self.damage_mod != 0:
            text += f", Damage Modifier: {self.damage_mod:+d}"
        if self.extra_damage_dice != 0:
            text += f", Extra Damage Dice: {self.extra_damage_dice:+d}"
            
        if self.requirements:
            text += "\nRequirements: "
            reqs = []
            if "form" in self.requirements:
                forms = ", ".join(f.title() for f in self.requirements["form"])
                reqs.append(f"Form ({forms})")
            if "rage" in self.requirements:
                reqs.append(f"Rage {self.requirements['rage']}+")
            if "ability" in self.requirements:
                for ability, value in self.requirements["ability"].items():
                    reqs.append(f"{ability.title()} {value}+")
            text += ", ".join(reqs)
            
        if self.special_effects:
            text += "\nSpecial Effects: "
            effects = []
            if "knockdown" in self.special_effects and self.special_effects["knockdown"]:
                effects.append("Knockdown")
            if "stun" in self.special_effects and self.special_effects["stun"]:
                effects.append(f"Stun ({self.special_effects['stun']} turns)")
            if "disarm" in self.special_effects and self.special_effects["disarm"]:
                effects.append("Disarm")
            if "reduce_defense" in self.special_effects:
                effects.append(f"Reduce Defense ({self.special_effects['reduce_defense']})")
            text += ", ".join(effects)
            
        return text 