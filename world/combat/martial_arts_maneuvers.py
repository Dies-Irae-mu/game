"""
World of Darkness Martial Arts Maneuvers

This module defines martial arts maneuvers from World of Darkness 20th Anniversary Edition,
including standard martial arts, Do techniques, and weapon techniques.
"""

from world.combat.models import CombatManeuver

# Martial Arts Maneuvers
MARTIAL_ARTS_MANEUVERS = {
    # Basic Martial Arts Maneuvers
    "counter_throw": CombatManeuver(
        name="Counter Throw",
        description="Directing an attacker's momentum against him, sending him flying.",
        attack_type="defense",
        attribute="Dexterity",
        ability="Martial Arts",
        difficulty_mod=0,  # Base difficulty 6
        damage_mod=0,  # Special damage based on opponent's Strength
        damage_type="bashing",
        extra_damage_dice=0,
        special_effects={"knockdown": True},
        requirements={
            "ability": {"Martial Arts": 1, "Athletics": 1},
            "style": ["soft"]
        }
    ),
    
    "death_strike": CombatManeuver(
        name="Death Strike",
        description="Aiming a rigid hand at an organ, joint, or other incapacitating location.",
        attack_type="strike",
        attribute="Dexterity",
        ability="Martial Arts",
        difficulty_mod=-1,  # Base difficulty 5
        damage_mod=2,
        damage_type="lethal",
        extra_damage_dice=0,
        special_effects={},
        requirements={
            "ability": {"Martial Arts": 3},
            "style": ["hard"]
        }
    ),
    
    "deflecting_block": CombatManeuver(
        name="Deflecting Block",
        description="Evading and redirecting an attacker's blow, potentially causing them to fall.",
        attack_type="defense",
        attribute="Dexterity",
        ability="Martial Arts",
        difficulty_mod=0,  # Base difficulty 6
        damage_mod=0,  # Special damage based on attacker's Strength
        damage_type="bashing",
        extra_damage_dice=0,
        special_effects={"knockdown": True},
        requirements={
            "ability": {"Martial Arts": 2, "Athletics": 2},
            "style": ["soft"]
        }
    ),
    
    "dragon_tail_sweep": CombatManeuver(
        name="Dragon Tail Sweep",
        description="A spinning leg sweep that knocks an opponent sprawling.",
        attack_type="sweep",
        attribute="Dexterity",
        ability="Martial Arts",
        difficulty_mod=2,  # Base difficulty 8
        damage_mod=0,  # Special damage based on opponent's Strength
        damage_type="bashing",
        extra_damage_dice=0,
        special_effects={"knockdown": True},
        requirements={
            "ability": {"Martial Arts": 1, "Athletics": 1},
            "style": ["hard"]
        }
    ),
    
    "elbow_knee_strike": CombatManeuver(
        name="Elbow/Knee Strike",
        description="A quick, brutal blow with an elbow or kneecap to a vulnerable spot.",
        attack_type="strike",
        attribute="Dexterity",
        ability="Martial Arts",
        difficulty_mod=-1,  # Base difficulty 5
        damage_mod=1,
        damage_type="bashing",
        extra_damage_dice=0,
        special_effects={},
        requirements={
            "ability": {"Martial Arts": 1},
            "style": ["any"]
        }
    ),
    
    "flying_kick": CombatManeuver(
        name="Flying Kick",
        description="Leaping through the air, combining body weight and momentum into a powerful blow.",
        attack_type="kick",
        attribute="Dexterity",
        ability="Martial Arts",
        difficulty_mod=1,  # Base difficulty 7
        damage_mod=2,
        damage_type="bashing",
        extra_damage_dice=0,
        special_effects={},
        requirements={
            "ability": {"Martial Arts": 1, "Athletics": 1},
            "style": ["hard"]
        }
    ),
    
    "hard_strike": CombatManeuver(
        name="Hard Strike",
        description="A basic combat blow with a clenched fist or rigid fingers (Tiger Claw).",
        attack_type="strike",
        attribute="Dexterity",
        ability="Martial Arts",
        difficulty_mod=-1,  # Base difficulty 5
        damage_mod=1,
        damage_type="bashing",
        extra_damage_dice=0,
        special_effects={},
        requirements={
            "ability": {"Martial Arts": 1},
            "style": ["hard"]
        }
    ),
    
    "soft_strike": CombatManeuver(
        name="Soft Strike",
        description="A blow that uses the opponent's own force against them.",
        attack_type="strike",
        attribute="Dexterity",
        ability="Martial Arts",
        difficulty_mod=0,  # Base difficulty 6
        damage_mod=1,
        damage_type="bashing",
        extra_damage_dice=0,
        special_effects={},
        requirements={
            "ability": {"Martial Arts": 1},
            "style": ["soft"]
        }
    ),
    
    "joint_lock": CombatManeuver(
        name="Joint Lock",
        description="Applying pressure to joints and pressure points, potentially breaking limbs.",
        attack_type="grapple",
        attribute="Dexterity",
        ability="Martial Arts",
        difficulty_mod=-1,  # Base difficulty 5
        damage_mod=0,  # Special damage based on successes
        damage_type="lethal",
        extra_damage_dice=0,
        special_effects={"immobilize": 1},
        requirements={
            "ability": {"Martial Arts": 2, "Athletics": 2},
            "style": ["any"]
        }
    ),
    
    "nerve_strike": CombatManeuver(
        name="Nerve/Pressure Point Strike",
        description="Targeting a vital location with precision force.",
        attack_type="strike",
        attribute="Dexterity",
        ability="Martial Arts",
        difficulty_mod=1,  # Base difficulty 7
        damage_mod=3,
        damage_type="bashing",
        extra_damage_dice=0,
        special_effects={"stun": 1},
        requirements={
            "ability": {"Martial Arts": 3},
            "style": ["any"]
        }
    ),
    
    "snake_step": CombatManeuver(
        name="Snake Step",
        description="Shifting away from the blow, deftly sidestepping an attack.",
        attack_type="defense",
        attribute="Dexterity",
        ability="Martial Arts",
        difficulty_mod=0,  # Base difficulty varies by style (hard 6/soft 5)
        damage_mod=0,
        damage_type="none",
        extra_damage_dice=0,
        special_effects={},
        requirements={
            "ability": {"Martial Arts": 1, "Athletics": 1},
            "style": ["any"]
        }
    ),
    
    "snap_kick": CombatManeuver(
        name="Snap Kick",
        description="A simple yet effective kick focusing lower body strength.",
        attack_type="kick",
        attribute="Dexterity",
        ability="Martial Arts",
        difficulty_mod=-1,  # Base difficulty 5
        damage_mod=1,
        damage_type="bashing",
        extra_damage_dice=0,
        special_effects={},
        requirements={
            "ability": {"Martial Arts": 1},
            "style": ["hard"]
        }
    ),
    
    "spinning_kick": CombatManeuver(
        name="Spinning Kick",
        description="Spinning around to plant a solid kick into the target.",
        attack_type="kick",
        attribute="Dexterity",
        ability="Martial Arts",
        difficulty_mod=0,  # Base difficulty 6
        damage_mod=3,
        damage_type="bashing",
        extra_damage_dice=0,
        special_effects={},
        requirements={
            "ability": {"Martial Arts": 2, "Athletics": 2},
            "style": ["hard"]
        }
    ),
    
    "throw": CombatManeuver(
        name="Throw",
        description="Grappling an opponent and slamming them into a surface.",
        attack_type="throw",
        attribute="Dexterity",
        ability="Martial Arts",
        difficulty_mod=0,  # Base difficulty varies by style (hard 7/soft 6)
        damage_mod=0,  # Special damage based on Strength + movement
        damage_type="bashing",
        extra_damage_dice=0,
        special_effects={"knockdown": True},
        requirements={
            "ability": {"Martial Arts": 2},
            "style": ["any"]
        }
    ),
    
    "thunder_kick": CombatManeuver(
        name="Thunder Kick",
        description="A devastating flying kick focusing chi and mass.",
        attack_type="kick",
        attribute="Dexterity",
        ability="Martial Arts",
        difficulty_mod=1,  # Base difficulty 7
        damage_mod=3,
        damage_type="bashing",
        extra_damage_dice=0,
        special_effects={"bonus_damage": "successes"},
        requirements={
            "ability": {"Martial Arts": 3, "Athletics": 2},
            "style": ["hard"]
        }
    ),
    
    "vital_strike": CombatManeuver(
        name="Vital Strike",
        description="A sharp-handed blow to an organ or joint inflicting lethal injury.",
        attack_type="strike",
        attribute="Dexterity",
        ability="Martial Arts",
        difficulty_mod=1,  # Base difficulty 7
        damage_mod=0,
        damage_type="lethal",
        extra_damage_dice=0,
        special_effects={},
        requirements={
            "ability": {"Martial Arts": 2},
            "style": ["hard"]
        }
    ),
    
    "withering_grasp": CombatManeuver(
        name="Withering Grasp",
        description="Grabbing a foe in a painful hold, potentially disarming them.",
        attack_type="grapple",
        attribute="Dexterity",
        ability="Martial Arts",
        difficulty_mod=1,  # Not specified in source, assumed 7
        damage_mod=0,  # Special damage based on Strength
        damage_type="bashing",
        extra_damage_dice=0,
        special_effects={"disarm": True},
        requirements={
            "ability": {"Martial Arts": 3},
            "style": ["soft"]
        }
    ),
}

# Do Maneuvers
DO_MANEUVERS = {
    "arrow_cutting": CombatManeuver(
        name="Arrow Cutting",
        description="Catching arrows and other projectile weapons or knocking them out of the air.",
        attack_type="defense",
        attribute="Dexterity",
        ability="Do",
        difficulty_mod=1,  # Base difficulty 7/9
        damage_mod=0,
        damage_type="none",
        extra_damage_dice=0,
        special_effects={"deflect_missile": True},
        requirements={
            "ability": {"Do": 2}
        }
    ),
    
    "hurricane_throw": CombatManeuver(
        name="Hurricane Throw",
        description="Catching and throwing an opponent with incredible force.",
        attack_type="throw",
        attribute="Dexterity",
        ability="Do",
        difficulty_mod=2,  # Base difficulty 8
        damage_mod=3,
        damage_type="bashing",
        extra_damage_dice=0,
        special_effects={"bonus_damage": "successes", "knockdown": True},
        requirements={
            "ability": {"Do": 3}
        }
    ),
    
    "iron_shirt": CombatManeuver(
        name="Iron Shirt",
        description="Withstanding terrible blows through intense conditioning and focused chi.",
        attack_type="defense",
        attribute="Stamina",
        ability="Do",
        difficulty_mod=0,
        damage_mod=0,
        damage_type="none",
        extra_damage_dice=0,
        special_effects={"bonus_soak": "do_rating"},
        requirements={
            "ability": {"Do": 2}
        }
    ),
    
    "kiaijutsu": CombatManeuver(
        name="Kiaijutsu",
        description="Channeling chi through voice for intimidation, stamina boost, or eloquence.",
        attack_type="special",
        attribute="varies",
        ability="Do",
        difficulty_mod=1,  # Varies based on effect
        damage_mod=0,
        damage_type="none",
        extra_damage_dice=0,
        special_effects={"kiai_effects": True},
        requirements={
            "ability": {"Do": 3}
        }
    ),
    
    "plum_flower_blossom": CombatManeuver(
        name="Plum Flower Blossom",
        description="Incredible feats of acrobatic prowess, bouncing from object to object.",
        attack_type="movement",
        attribute="Dexterity",
        ability="Do",
        difficulty_mod=0,  # Base difficulty 6
        damage_mod=0,
        damage_type="none",
        extra_damage_dice=0,
        special_effects={"double_jump": True, "bonus_attack_damage": 2},
        requirements={
            "ability": {"Do": 2, "Athletics": 2}
        }
    ),
    
    "soft_fist": CombatManeuver(
        name="Soft Fist",
        description="Guiding a hand-to-hand attack back against those who wish to harm the devotee.",
        attack_type="defense",
        attribute="Dexterity",
        ability="Do",
        difficulty_mod=1,  # Base difficulty 7
        damage_mod=0,
        damage_type="special",
        extra_damage_dice=0,
        special_effects={"redirect_attack": True},
        requirements={
            "ability": {"Do": 3}
        }
    ),
    
    "ten_thousand_weapons": CombatManeuver(
        name="Ten Thousand Weapons",
        description="Using any object as an effective weapon.",
        attack_type="strike",
        attribute="Dexterity",
        ability="Do",
        difficulty_mod=0,
        damage_mod=0,
        damage_type="special",
        extra_damage_dice=0,
        special_effects={"improvised_weapon": True},
        requirements={
            "ability": {"Do": 2, "Melee": 2}
        }
    ),
    
    "typhoon_kick": CombatManeuver(
        name="Typhoon Kick",
        description="A devastating kick that can shatter stone and kill most human beings.",
        attack_type="kick",
        attribute="Dexterity",
        ability="Do",
        difficulty_mod=2,  # Base difficulty 8
        damage_mod=5,
        damage_type="lethal",
        extra_damage_dice=0,
        special_effects={"bonus_damage": "successes", "self_damage": True},
        requirements={
            "ability": {"Do": 4, "Athletics": 3}
        }
    ),
    
    "weapon_art": CombatManeuver(
        name="Weapon Art",
        description="Applying the mastery of Do into the use of hand-to-hand weaponry.",
        attack_type="special",
        attribute="Dexterity",
        ability="Do",
        difficulty_mod=-1,
        damage_mod=0,
        damage_type="special",
        extra_damage_dice=0,
        special_effects={"weapon_mastery": True},
        requirements={
            "ability": {"Do": 3, "Melee": 2}
        }
    ),
}

# Weapon Maneuvers
WEAPON_MANEUVERS = {
    "bash": CombatManeuver(
        name="Bash",
        description="Striking with a non-edged portion of the weapon to injure, not kill.",
        attack_type="melee",
        attribute="Dexterity",
        ability="Brawl",
        difficulty_mod=1,  # Weapon +1
        damage_mod=-1,
        damage_type="bashing",
        extra_damage_dice=0,
        special_effects={},
        requirements={
            "ability": {"Brawl": 1}
        }
    ),
    
    "bind": CombatManeuver(
        name="Bind",
        description="Sweeping an antagonist's weapon up to prevent them from using it.",
        attack_type="defense",
        attribute="Dexterity",
        ability="varies",
        difficulty_mod=2,  # Usually 8, can be reduced to 6
        damage_mod=0,
        damage_type="none",
        extra_damage_dice=0,
        special_effects={"weapon_bind": True},
        requirements={
            "ability": {"Melee": 2}
        }
    ),
    
    "curtain_of_blood": CombatManeuver(
        name="Curtain of Blood",
        description="A superficial slash above the opponent's eyes to spill blood into their vision.",
        attack_type="melee",
        attribute="Dexterity",
        ability="varies",
        difficulty_mod=2,  # Base difficulty 8
        damage_mod=0,
        damage_type="none",
        extra_damage_dice=0,
        special_effects={"blind": 1},
        requirements={
            "ability": {"Melee": 2}
        }
    ),
    
    "feint": CombatManeuver(
        name="Feint",
        description="Faking a strike to set up an opponent for a different attack.",
        attack_type="melee",
        attribute="Manipulation",
        ability="varies",
        difficulty_mod=0,  # Base difficulty 6
        damage_mod=2,
        damage_type="special",
        extra_damage_dice=0,
        special_effects={"feint": True},
        requirements={
            "ability": {"Melee": 2}
        }
    ),
    
    "fleche": CombatManeuver(
        name="Fleche/Charge",
        description="Darting in to close the distance with speed and momentum.",
        attack_type="melee",
        attribute="Dexterity",
        ability="varies",
        difficulty_mod=1,  # Base difficulty 7
        damage_mod=1,
        damage_type="weapon",
        extra_damage_dice=0,
        special_effects={},
        requirements={
            "ability": {"Melee": 1, "Athletics": 1}
        }
    ),
    
    "great_blow": CombatManeuver(
        name="Great Blow",
        description="A massive blow that sacrifices defense for power.",
        attack_type="melee",
        attribute="Dexterity",
        ability="varies",
        difficulty_mod=2,  # Weapon +2
        damage_mod=3,
        damage_type="weapon",
        extra_damage_dice=0,
        special_effects={},
        requirements={
            "ability": {"Melee": 2, "Strength": 3}
        }
    ),
    
    "jab": CombatManeuver(
        name="Jab",
        description="A short, quick stab that tests defenses and improves your own.",
        attack_type="melee",
        attribute="Dexterity",
        ability="varies",
        difficulty_mod=1,  # Weapon +1
        damage_mod=-2,
        damage_type="weapon",
        extra_damage_dice=0,
        special_effects={"defensive": True},
        requirements={
            "ability": {"Melee": 1}
        }
    ),
    
    "lash": CombatManeuver(
        name="Lash",
        description="A fast flick of the weapon to strike at a small targeted object.",
        attack_type="melee",
        attribute="Dexterity",
        ability="varies",
        difficulty_mod=2,  # Base difficulty 8
        damage_mod=0,
        damage_type="weapon",
        extra_damage_dice=0,
        special_effects={"precision": True},
        requirements={
            "ability": {"Melee": 2}
        }
    ),
    
    "lightning_parry": CombatManeuver(
        name="Lightning Parry",
        description="Deflecting shots from multiple attackers with a massive blow or flurry.",
        attack_type="defense",
        attribute="Dexterity",
        ability="varies",
        difficulty_mod=0,  # Special: 6 + number of attackers beyond first
        damage_mod=0,
        damage_type="none",
        extra_damage_dice=0,
        special_effects={"multi_defense": True},
        requirements={
            "ability": {"Melee": 3}
        }
    ),
    
    "riposte": CombatManeuver(
        name="Riposte",
        description="Following a parry with a rapid counterstrike.",
        attack_type="melee",
        attribute="Dexterity",
        ability="varies",
        difficulty_mod=-2,  # Weapon -2
        damage_mod=0,
        damage_type="weapon",
        extra_damage_dice=0,
        special_effects={},
        requirements={
            "ability": {"Melee": 2}
        }
    ),
    
    "shiv": CombatManeuver(
        name="Shiv",
        description="Wrapping around an opponent to stab a short weapon into a sensitive location.",
        attack_type="melee",
        attribute="Dexterity",
        ability="Melee",
        difficulty_mod=1,  # Base difficulty 7/9
        damage_mod=1,
        damage_type="lethal",
        extra_damage_dice=0,
        special_effects={"bypass_armor": True, "continuous_damage": 1},
        requirements={
            "ability": {"Melee": 2, "Brawl": 2}
        }
    ),
    
    "slash": CombatManeuver(
        name="Slash",
        description="A slicing blow aimed for the kill.",
        attack_type="melee",
        attribute="Dexterity",
        ability="varies",
        difficulty_mod=1,  # Weapon +1
        damage_mod=2,
        damage_type="weapon",
        extra_damage_dice=0,
        special_effects={},
        requirements={
            "ability": {"Melee": 1}
        }
    ),
    
    "spinning_bloodbath": CombatManeuver(
        name="Spinning Bloodbath",
        description="A whirl that turns incoming enemies into geysers of carnage.",
        attack_type="melee",
        attribute="Dexterity",
        ability="varies",
        difficulty_mod=0,  # Base difficulty 6
        damage_mod=0,
        damage_type="special",
        extra_damage_dice=0,
        special_effects={"mook_slayer": True},
        requirements={
            "ability": {"Melee": 3, "Dexterity": 3}
        }
    ),
    
    "stabbing_frenzy": CombatManeuver(
        name="Stabbing Frenzy",
        description="A storm of rapid jabs and stabs at close range with a short blade.",
        attack_type="melee",
        attribute="Dexterity",
        ability="Brawl",
        difficulty_mod=-2,  # Base difficulty 4
        damage_mod=3,
        damage_type="lethal",
        extra_damage_dice=0,
        special_effects={"vulnerable": True},
        requirements={
            "ability": {"Brawl": 2, "Melee": 2}
        }
    ),
    
    "stillness_strike": CombatManeuver(
        name="Stillness Strike",
        description="A Zen trance technique for devastating counterattacks.",
        attack_type="melee",
        attribute="Wits",
        ability="Awareness",
        difficulty_mod=0,  # Base difficulty 6
        damage_mod=0,
        damage_type="special",
        extra_damage_dice=0,
        special_effects={"stillness": True},
        requirements={
            "ability": {"Martial Arts": 3, "Willpower": 5}
        }
    ),
    
    "thrust": CombatManeuver(
        name="Thrust",
        description="A lunging attack that spears the enemy through a vital spot.",
        attack_type="melee",
        attribute="Dexterity",
        ability="varies",
        difficulty_mod=1,  # Weapon +1
        damage_mod=2,
        damage_type="lethal",
        extra_damage_dice=0,
        special_effects={"bleeding": 1},
        requirements={
            "ability": {"Melee": 2}
        }
    ),
}

# Combine all maneuvers
ALL_MARTIAL_ARTS_MANEUVERS = {}
ALL_MARTIAL_ARTS_MANEUVERS.update(MARTIAL_ARTS_MANEUVERS)
ALL_MARTIAL_ARTS_MANEUVERS.update(DO_MANEUVERS)
ALL_MARTIAL_ARTS_MANEUVERS.update(WEAPON_MANEUVERS)

# Maneuver groups for organization and filtering
MARTIAL_ARTS_MANEUVER_GROUPS = {
    "standard": list(MARTIAL_ARTS_MANEUVERS.keys()),
    "do": list(DO_MANEUVERS.keys()),
    "weapon": list(WEAPON_MANEUVERS.keys()),
    "strike": [name for name, maneuver in ALL_MARTIAL_ARTS_MANEUVERS.items() if maneuver.attack_type == "strike"],
    "kick": [name for name, maneuver in ALL_MARTIAL_ARTS_MANEUVERS.items() if maneuver.attack_type == "kick"],
    "throw": [name for name, maneuver in ALL_MARTIAL_ARTS_MANEUVERS.items() if maneuver.attack_type == "throw"],
    "defense": [name for name, maneuver in ALL_MARTIAL_ARTS_MANEUVERS.items() if maneuver.attack_type == "defense"],
    "grapple": [name for name, maneuver in ALL_MARTIAL_ARTS_MANEUVERS.items() if maneuver.attack_type == "grapple"],
    "sweep": [name for name, maneuver in ALL_MARTIAL_ARTS_MANEUVERS.items() if maneuver.attack_type == "sweep"],
    "melee": [name for name, maneuver in ALL_MARTIAL_ARTS_MANEUVERS.items() if maneuver.attack_type == "melee"],
    "special": [name for name, maneuver in ALL_MARTIAL_ARTS_MANEUVERS.items() if maneuver.attack_type == "special"],
    "hard_style": [name for name, maneuver in MARTIAL_ARTS_MANEUVERS.items() 
                   if "style" in maneuver.requirements and 
                   ("hard" in maneuver.requirements["style"] or "any" in maneuver.requirements["style"])],
    "soft_style": [name for name, maneuver in MARTIAL_ARTS_MANEUVERS.items() 
                   if "style" in maneuver.requirements and 
                   ("soft" in maneuver.requirements["style"] or "any" in maneuver.requirements["style"])],
    "lethal": [name for name, maneuver in ALL_MARTIAL_ARTS_MANEUVERS.items() if maneuver.damage_type == "lethal"],
    "bashing": [name for name, maneuver in ALL_MARTIAL_ARTS_MANEUVERS.items() if maneuver.damage_type == "bashing"],
}

def get_martial_arts_maneuver(name):
    """Get a martial arts maneuver by name.
    
    Args:
        name (str): Name of the maneuver (case-insensitive)
        
    Returns:
        CombatManeuver or None: The maneuver if found, None otherwise
    """
    # Try exact match first
    if name in ALL_MARTIAL_ARTS_MANEUVERS:
        return ALL_MARTIAL_ARTS_MANEUVERS[name]
    
    # Try case-insensitive match
    name_lower = name.lower()
    for key, maneuver in ALL_MARTIAL_ARTS_MANEUVERS.items():
        if key.lower() == name_lower or maneuver.name.lower() == name_lower:
            return maneuver
    
    return None

def check_martial_arts_requirements(character, maneuver):
    """Check if character meets requirements for the martial arts maneuver.
    
    Args:
        character: The character to check
        maneuver: The maneuver object with requirements
        
    Returns:
        bool: True if requirements are met, False otherwise
    """
    if not maneuver.requirements:
        return True
        
    # Check style requirements if applicable
    if "style" in maneuver.requirements and hasattr(character, "martial_arts_style"):
        if "any" not in maneuver.requirements["style"] and character.martial_arts_style not in maneuver.requirements["style"]:
            return False
    
    # Check ability requirements
    if "ability" in maneuver.requirements:
        for ability_name, min_value in maneuver.requirements["ability"].items():
            # Special case for "Strength" and other attributes that aren't actually abilities
            if ability_name in ["Strength", "Dexterity", "Stamina", "Charisma", "Manipulation", "Appearance", 
                               "Perception", "Intelligence", "Wits"]:
                ability_value = character.get_stat('attributes', None, ability_name, temp=True) or 0
            # Handle regular abilities
            else:
                # Try to get the ability from character sheet - this assumes character has a method to get abilities
                ability_value = 0
                if ability_name in ["Martial Arts", "Do"]:
                    ability_value = character.get_stat('abilities', 'talent', ability_name, temp=True) or 0
                elif ability_name in ["Melee", "Brawl", "Athletics"]:
                    ability_value = character.get_stat('abilities', 'talent', ability_name, temp=True) or 0
                
            if ability_value < min_value:
                return False
    
    # Check for Willpower requirement
    if "Willpower" in maneuver.requirements:
        willpower = character.get_stat('traits', None, 'Willpower', temp=True) or 0
        if willpower < maneuver.requirements["Willpower"]:
            return False
    
    return True

def get_martial_arts_equipment_bonus(character, maneuver):
    """Get bonus from martial arts equipment.
    
    Args:
        character: The character to check
        maneuver: The maneuver being used
        
    Returns:
        dict: Dictionary with various bonuses (difficulty_mod, damage_mod, etc.)
    """
    # Default bonuses (no effect)
    bonuses = {
        "difficulty_mod": 0,
        "damage_mod": 0,
        "extra_damage_dice": 0
    }
    
    # Check if character has worn/wielded equipment
    # This is a simplified implementation - expand based on your equipment system
    if hasattr(character, "worn_equipment"):
        for item in character.worn_equipment:
            # Check if it's martial arts equipment
            if hasattr(item, "category") and item.category == "martial_arts":
                # Apply bonuses based on equipment
                if hasattr(item, "martial_arts_details"):
                    details = item.martial_arts_details
                    
                    # Apply bonuses for specific techniques if applicable
                    if hasattr(details, "special_techniques") and maneuver.name in details.special_techniques:
                        bonuses["difficulty_mod"] -= 1
                        bonuses["damage_mod"] += 1
                    
                    # Apply style-specific bonuses
                    if (hasattr(details, "style_requirements") and 
                        hasattr(maneuver, "requirements") and 
                        "style" in maneuver.requirements):
                        
                        for style in maneuver.requirements["style"]:
                            if style in details.style_requirements:
                                bonuses["difficulty_mod"] -= 1
                                break
    
    return bonuses 