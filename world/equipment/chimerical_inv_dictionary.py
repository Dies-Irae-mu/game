from evennia.utils.utils import lazy_property
from world.equipment.models import MeleeWeapon, RangedWeapon, Armor, Aircraft, Jetpack, Cycle, Landcraft

"""
   "ITEM NAME": ItemClass( #classes are MeleeWeapon, RangedWeapon, ThrownWeapon, ImprovisedWeapon, Armor
        name="",        #name of item, probably just copy/paste the ITEM NAME
        description="", #insert description
        damage="",      #strength + number for melee, absolute value for ranged
        damage_type="", #bashing, lethal, aggravated
        conceal="",     #pocket, jacket, trenchcoat, n/a
        difficulty=,    #absolute value (list a number with no quotes)
        resources=,     #ignore, put as 0
        equipment_type="supernatural_unique",   #I might adjust this in the future, but it's not important
        category="",    #melee, ranged, thrown, armor, ammunition, improvised
        is_unique=False, #should be false unless you're making a treasure or unique weapon
        requires_approval=False #up to you, probably false.
     )
"""


inventory_dictionary = {
    "Chimerical Sword": MeleeWeapon(
        name="Longsword",
        description="A longsword is a versatile weapon that can be used for both melee attacks and defense. It is a two-handed weapon that requires two hands to wield. The longsword is a powerful weapon that can deal significant damage to enemies.",
        damage="Strength+2",
        damage_type="Lethal",
        conceal="Trenchcoat",
        difficulty=6,
        resources=2,
        equipment_type="mundane",
        category="melee",
        is_unique=False,
        requires_approval=False
    ),
    "Chimerical Hatchet": MeleeWeapon(
        name="Hatchet",
        description="A hatchet is a small, handheld tool with a heavy, flat head and a short handle. It is a versatile weapon that can be used for both melee attacks and defense. The hatchet is a powerful weapon that can deal significant damage to enemies.",
        damage="Strength+1",
        damage_type="Lethal",
        conceal="Jacket",
        difficulty=6,
        resources=1,
        equipment_type="mundane",
        category="melee",
        is_unique=False,
        requires_approval=False
    ),
    "ITEM NAME": ItemClass(
        name="", 
        description="",
        damage="",
        damage_type="",
        conceal="",
        difficulty=,
        resources=,
        equipment_type="supernatural_unique",
        category="",
        is_unique=False,
        requires_approval=False
    ),
