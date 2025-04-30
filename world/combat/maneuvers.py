"""
World of Darkness Combat Maneuvers

This module defines the available combat maneuvers in the World of Darkness system.
"""

from .models import CombatManeuver

# Dictionary mapping command names to maneuvers
MANEUVERS = {
    # Basic Brawl Attacks
    "punch": CombatManeuver(
        name="Punch",
        description="A basic unarmed strike",
        attack_type="brawl",
        attribute="Dexterity",
        ability="Brawl",
        damage_type="bashing"
    ),
    
    "kick": CombatManeuver(
        name="Kick",
        description="A powerful kick attack",
        attack_type="brawl",
        attribute="Dexterity",
        ability="Brawl",
        difficulty_mod=1,  # Harder to hit with
        damage_mod=1,      # But does more damage
        damage_type="bashing"
    ),
    
    "tackle": CombatManeuver(
        name="Tackle",
        description="Rush opponent and knock them down",
        attack_type="brawl",
        attribute="Dexterity",
        ability="Athletics",
        difficulty_mod=2,
        damage_type="bashing",
        special_effects={"knockdown": True}
    ),
    
    "grapple": CombatManeuver(
        name="Grapple",
        description="Grab and hold your opponent",
        attack_type="brawl",
        attribute="Strength",
        ability="Brawl",
        difficulty_mod=1,
        damage_type="bashing",
        special_effects={"immobilize": True}
    ),
    
    # Martial Arts
    "martial_strike": CombatManeuver(
        name="Martial Arts Strike",
        description="Precise strike using martial arts training",
        attack_type="martial arts",
        attribute="Dexterity",
        ability="Brawl",
        difficulty_mod=-1,  # Easier to hit
        damage_type="bashing",
        requirements={"ability": {"Brawl": 3}}
    ),
    
    "sweep": CombatManeuver(
        name="Leg Sweep",
        description="Sweep the opponent's legs to knock them down",
        attack_type="martial arts",
        attribute="Dexterity",
        ability="Brawl",
        difficulty_mod=2,
        damage_type="bashing",
        special_effects={"knockdown": True},
        requirements={"ability": {"Brawl": 2}}
    ),
    
    # Melee Attacks
    "slash": CombatManeuver(
        name="Slash",
        description="A cutting attack with a bladed weapon",
        attack_type="melee",
        attribute="Dexterity",
        ability="Melee",
        damage_type="lethal"
    ),
    
    "thrust": CombatManeuver(
        name="Thrust",
        description="A piercing attack with a pointed weapon",
        attack_type="melee",
        attribute="Dexterity",
        ability="Melee",
        difficulty_mod=1,
        damage_mod=1,
        damage_type="lethal"
    ),
    
    "bash": CombatManeuver(
        name="Bash",
        description="A powerful strike with a blunt weapon",
        attack_type="melee",
        attribute="Strength",
        ability="Melee",
        damage_type="bashing",
        damage_mod=1
    ),
    
    # Fencing
    "feint": CombatManeuver(
        name="Feint",
        description="Fake an attack to create an opening",
        attack_type="fencing",
        attribute="Dexterity",
        ability="Melee",
        difficulty_mod=1,
        special_effects={"reduce_defense": 2},
        requirements={"ability": {"Melee": 3}}
    ),
    
    "riposte": CombatManeuver(
        name="Riposte",
        description="Counter an opponent's attack with your own",
        attack_type="fencing",
        attribute="Dexterity",
        ability="Melee",
        difficulty_mod=2,
        damage_type="lethal",
        requirements={"ability": {"Melee": 4}}
    ),
    
    # Firearms
    "aimed_shot": CombatManeuver(
        name="Aimed Shot",
        description="Take a moment to carefully aim before firing",
        attack_type="firearms",
        attribute="Perception",
        ability="Firearms",
        difficulty_mod=-1,
        damage_mod=1,
        damage_type="lethal",
        requirements={"ability": {"Firearms": 2}}
    ),
    
    "burst_fire": CombatManeuver(
        name="Burst Fire",
        description="Fire a short burst from an automatic weapon",
        attack_type="firearms",
        attribute="Dexterity",
        ability="Firearms",
        difficulty_mod=1,
        damage_mod=2,
        damage_type="lethal",
        requirements={"ability": {"Firearms": 3}}
    ),
    
    # Thrown Weapons
    "throw": CombatManeuver(
        name="Throw",
        description="Throw an object or weapon at a target",
        attack_type="athletics",
        attribute="Dexterity",
        ability="Athletics",
        damage_type="bashing",  # Changes based on weapon
    ),
    
    # Werewolf-specific
    "claw": CombatManeuver(
        name="Claw Strike",
        description="Attack with deadly werewolf claws",
        attack_type="brawl",
        attribute="Dexterity",
        ability="Brawl",
        damage_mod=2,
        damage_type="aggravated",
        requirements={"form": ["crinos", "hispo"]}
    ),
    
    "bite": CombatManeuver(
        name="Bite",
        description="Savage bite with deadly jaws",
        attack_type="brawl",
        attribute="Strength",
        ability="Brawl",
        difficulty_mod=1,
        damage_mod=1,
        damage_type="aggravated",
        requirements={"form": ["crinos", "hispo", "lupus"]}
    ),
    
    "rage_strike": CombatManeuver(
        name="Rage Strike",
        description="Channel Rage into a devastating attack",
        attack_type="brawl",
        attribute="Strength",
        ability="Brawl",
        damage_mod=3,
        damage_type="aggravated",
        requirements={"rage": 3, "form": ["crinos"]}
    ),
    
    # Dirty Fighting
    "low_blow": CombatManeuver(
        name="Low Blow",
        description="Strike at a vulnerable area",
        attack_type="brawl",
        attribute="Dexterity",
        ability="Brawl",
        difficulty_mod=1,
        damage_type="bashing",
        special_effects={"stun": 1}
    ),
    
    "disarm": CombatManeuver(
        name="Disarm",
        description="Attempt to knock a weapon from opponent's hand",
        attack_type="melee",
        attribute="Dexterity",
        ability="Melee",
        difficulty_mod=2,
        damage_type="bashing",
        special_effects={"disarm": True}
    ),
    
    # Defensive actions
    "dodge": CombatManeuver(
        name="Dodge",
        description="Attempt to completely avoid an attack",
        attack_type="defense",
        attribute="Dexterity",
        ability="Athletics",
        special_effects={"defense_type": "dodge"}
    ),
    
    "block": CombatManeuver(
        name="Block",
        description="Use your body to deflect an attack",
        attack_type="defense",
        attribute="Dexterity",
        ability="Brawl",
        special_effects={"defense_type": "block"}
    ),
    
    "parry": CombatManeuver(
        name="Parry",
        description="Use a weapon to deflect an attack",
        attack_type="defense",
        attribute="Dexterity",
        ability="Melee",
        special_effects={"defense_type": "parry"}
    )
}

# Groups of maneuvers by type for easier reference
MANEUVER_GROUPS = {
    "brawl": [name for name, m in MANEUVERS.items() if m.attack_type == "brawl"],
    "melee": [name for name, m in MANEUVERS.items() if m.attack_type == "melee"],
    "firearms": [name for name, m in MANEUVERS.items() if m.attack_type == "firearms"],
    "athletics": [name for name, m in MANEUVERS.items() if m.attack_type == "athletics"],
    "martial_arts": [name for name, m in MANEUVERS.items() if m.attack_type == "martial arts"],
    "fencing": [name for name, m in MANEUVERS.items() if m.attack_type == "fencing"],
    "defense": [name for name, m in MANEUVERS.items() if m.attack_type == "defense"],
    "werewolf": ["claw", "bite", "rage_strike"],
    "dirty": ["low_blow", "disarm"]
}

def get_maneuver(name):
    """Get a maneuver by name."""
    return MANEUVERS.get(name.lower()) 