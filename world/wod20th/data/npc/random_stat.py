import random
import json
import os
from commands.CmdNPC import NameGenerator
from world.wod20th.utils.possessed_utils import POSSESSED_POWERS
from world.wod20th.utils.companion_utils import COMPANION_POWERS
from world.wod20th.utils.sheet_constants import POWERS
from world.wod20th.utils.stat_mappings import SPECIAL_ADVANTAGES, COMBAT_SPECIAL_ADVANTAGES, ARTS, REALMS

# Path to the data files
DATA_PATH = "world/wod20th/data"

# Difficulty levels define how powerful NPCs will be
DIFFICULTY = {
    "LOW": {
        "attributes": 25,
        "abilities": 50,
        "disciplines": 3,
        "gifts": 3,
        "spheres": 4,
        "numina": 5,
        "charms": 5,
        "willpower": 3,
        "rage": 2,
        "gnosis": 2,
    },
    "MEDIUM": {
        "attributes": 35,
        "abilities": 75,
        "disciplines": 4,
        "gifts": 4,
        "spheres": 5,
        "numina": 7,
        "charms": 7,
        "willpower": 5,
        "rage": 4,
        "gnosis": 4,
    },
    "HIGH": {
        "attributes": 40,
        "abilities": 100,
        "disciplines": 5,
        "gifts": 5,
        "spheres": 6,
        "numina": 9,
        "charms": 9,
        "willpower": 7,
        "rage": 6,
        "gnosis": 6,
    }
}

# Spirit rank points allocation
SPIRIT_RANK_POINTS = {
    1: 10,
    2: 14,
    3: 16,
    4: 20,
    5: 25,
    6: 28,
    7: 32,
    8: 45,
    9: 60,
    10: 75
}

# Power lists
DISCIPLINES = [
    "potence", "auspex", "celerity", "dominate", "fortitude", 
    "presence", "obfuscate", "animalism", "protean", "thaumaturgy",
    "necromancy", "dementation", "chimerstry", "serpentis", "vicissitude",
    "obtenebration"
]

SPHERES = [
    "correspondence", "forces", "life", "matter", "entropy", 
    "mind", "spirit", "prime", "time"
]

SORCERY_PATHS = [
    "Alchemy", "Conjuration", "Chronomancy", "Conveyance", "Divination",
    "Enchantment", "Fascination", "Fortune", "Gauntlet Manipulation",
    "Healing", "Hellfire", "Mana Manipulation", "Ephemera", 
    "Mortal Necromancy", "Necronics", "Oneiromancy", "Saturnal Anima",
    "Saturnal Manes", "Scrying", "Shadows", "Shapeshifting", 
    "Spirit Awakening", "Spirit Chasing", "Starlight", 
    "Summoning, Binding, and Warding", "Weather Control", "Maelstroms"
]

NUMINA = [
    "Animal Psychic", "Anti-Psi", "Astral Projection", "Biocontrol",
    "Channeling", "Clairvoyance", "Cyberkinesis", "Cyberpathy",
    "Ectoplasmic Generation", "Empathic Healing", "Mind Shields",
    "Precognition", "Psychic Healing", "Psychic Hypnosis",
    "Psychic Invisibility", "Psychic Vampirism", "Psychokinesis",
    "Psychometry", "Psychoportation", "Pyrokinesis", "Soul Stealing",
    "Synergy", "Telepathy"
]

CHARMS = [
    "Airt Sense", "Appear", "Blast", "Blighted Touch", "Brand",
    "Break Reality", "Calcify", "Call for Aid", "Cleanse the Blight",
    "Cling", "Control Electrical Systems", "Corruption", "Create Fire",
    "Create Wind", "Death Fertility", "Digital Disruption", "Disable",
    "Disorient", "Dream Journey", "Ease Pain", "Element Sense",
    "Feedback", "Flee", "Flood", "Freeze", "Healing", "Illuminate",
    "Influence", "Inhabit", "Insight", "Iron Will", "Lightning Bolt",
    "Materialize", "Meld", "Mind Speech", "Open Moon Bridge", "Peek",
    "Possession", "Quake", "Re-form", "Shapeshift", "Short Out",
    "Shatter Glass", "Solidify Reality", "Spirit Away", "Spirit Static",
    "Swift Flight", "System Havoc", "Terror", "Track", "Tremor", 
    "Umbral Storm", "Umbraquake", "Updraft", "Waves"
]

GIFT_SOURCES = [
    "rank1_garou_gifts", "rank2_garou_gifts", "rank3_garou_gifts", 
    "rank4_garou_gifts", "rank5_garou_gifts", "ajaba_gifts", 
    "bastet_gifts", "corax_gifts", "gurahl_gifts", "kitsune_gifts", 
    "mokole_gifts", "nagah_gifts", "nuwisha_gifts", "ratkin_gifts", 
    "rokea_gifts"
]

ATTRIBUTES = {
    "physical": ["strength", "dexterity", "stamina"],
    "social": ["charisma", "manipulation", "appearance"],
    "mental": ["perception", "intelligence", "wits"]
}

ABILITIES = {
    "social": [
        "subterfuge", "style", "seduction", "empathy", "expression",
        "intimidation", "leadership", "etiquette", "politics", "carousing", 
        "diplomacy"
    ],
    "mental": [
        "awareness", "animal_ken", "lucid_dreaming", "academics", "computer",
        "cosmology", "enigmas", "finance", "law", "medicine", "occult",
        "science", "technology"
    ],
    "stealth": [
        "stealth", "larceny", "intrigue", "streetwise", "investigation", 
        "mimicry"
    ],
    "physical": [
        "drive", "survival", "scrounging", "crafts", "performance"
    ],
    "combat": [
        "athletics", "brawl", "firearms", "melee", "martial arts", "fencing"
    ]
}

def load_gifts():
    """Load gift data from files."""
    gifts = {}
    for source in GIFT_SOURCES:
        try:
            file_path = os.path.join(DATA_PATH, f"{source}.json")
            with open(file_path, 'r', encoding='utf-8') as f:
                gifts[source] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            gifts[source] = []
    return gifts

def get_random_subset(item_list, count):
    """Get a random subset of items from a list."""
    if not item_list:
        return []
    count = min(count, len(item_list))
    return random.sample(item_list, count)

def distribute_points(total_points, categories, min_per_category=0, max_per_category=5):
    """Distribute points among categories."""
    result = {category: min_per_category for category in categories}
    remaining_points = total_points - (min_per_category * len(categories))
    
    if remaining_points <= 0:
        return result
        
    # Distribute remaining points randomly
    while remaining_points > 0:
        category = random.choice(categories)
        if result[category] < max_per_category:
            result[category] += 1
            remaining_points -= 1
    
    return result

def get_random_npc_stats(difficulty="MEDIUM", splat="mortal"):
    """Generate random stats for an NPC based on difficulty and splat."""
    if difficulty not in DIFFICULTY:
        difficulty = "MEDIUM"
    
    # Start with a basic template
    stats = {
        "splat": splat,
        "attributes": {},
        "abilities": {},
        "backgrounds": {},
        "willpower": random.randint(2, DIFFICULTY[difficulty]["willpower"]),
        "health": {
            "bashing": 0,
            "lethal": 0,
            "aggravated": 0
        }
    }
    
    # Generate attributes
    attr_points = DIFFICULTY[difficulty]["attributes"]
    for category, attrs in ATTRIBUTES.items():
        cat_points = attr_points // 3  # Roughly equal distribution
        attr_values = distribute_points(cat_points, attrs, 1, 5)
        for attr, value in attr_values.items():
            stats["attributes"][attr] = value
    
    # Generate abilities
    ability_points = DIFFICULTY[difficulty]["abilities"]
    ability_cats = list(ABILITIES.keys())
    # Decide how many points per category
    cat_points = {}
    for cat in ability_cats:
        # Random but biased toward equal distribution
        cat_points[cat] = ability_points // len(ability_cats) + random.randint(-2, 2)
    
    # For each category, pick a subset of abilities and distribute points
    for cat, points in cat_points.items():
        if points <= 0:
            continue
            
        # Pick a subset of abilities from this category
        num_abilities = random.randint(2, min(5, len(ABILITIES[cat])))
        selected_abilities = get_random_subset(ABILITIES[cat], num_abilities)
        
        # Distribute points
        if selected_abilities:
            ability_values = distribute_points(points, selected_abilities, 0, 4)
            for ability, value in ability_values.items():
                if value > 0:  # Only add if they have points
                    stats["abilities"][ability] = value
    
    # Add supernatural powers based on splat
    if splat == "vampire":
        # Select disciplines and distribute points
        num_disciplines = DIFFICULTY[difficulty]["disciplines"]
        selected_disciplines = get_random_subset(DISCIPLINES, num_disciplines)
        disc_points = num_disciplines * random.randint(1, 3)  # Total points to distribute
        
        stats["disciplines"] = {}
        disc_values = distribute_points(disc_points, selected_disciplines, 1, 4)
        for disc, value in disc_values.items():
            stats["disciplines"][disc] = value
            
        # Add blood pool
        stats["blood_pool"] = 10
        
    elif splat == "mage":
        # Select spheres and distribute points
        num_spheres = DIFFICULTY[difficulty]["spheres"]
        selected_spheres = get_random_subset(SPHERES, num_spheres)
        
        # Calculate arete - max sphere level can't exceed arete
        arete = random.randint(2, 4) if difficulty == "HIGH" else random.randint(1, 3)
        
        # Distribute sphere points
        sphere_points = num_spheres * random.randint(1, 2)
        stats["spheres"] = {}
        sphere_values = distribute_points(sphere_points, selected_spheres, 1, arete)
        for sphere, value in sphere_values.items():
            stats["spheres"][sphere] = value
            
        stats["arete"] = arete
        stats["quintessence"] = arete
        
    elif splat == "shifter":
        # Add rage and gnosis
        stats["rage"] = random.randint(1, DIFFICULTY[difficulty]["rage"])
        stats["gnosis"] = random.randint(1, DIFFICULTY[difficulty]["gnosis"])
        
        # Add gifts (would normally load from files)
        stats["gifts"] = {}
        gift_count = DIFFICULTY[difficulty]["gifts"]
        
        # For simplicity, just assign dummy gift names
        for i in range(gift_count):
            gift_name = f"Generic Gift {i+1}"
            stats["gifts"][gift_name] = 1
            
    elif splat == "psychic":
        # Select numina and distribute points
        num_numina = random.randint(1, 3)
        selected_numina = get_random_subset(NUMINA, num_numina)
        numina_points = DIFFICULTY[difficulty]["numina"]
        
        stats["numina"] = {}
        numina_values = distribute_points(numina_points, selected_numina, 1, 4)
        for numina, value in numina_values.items():
            stats["numina"][numina] = value
            
    elif splat == "spirit":
        # Generate spirit stats
        rank = 1
        if difficulty == "LOW":
            rank = random.randint(1, 3)
        elif difficulty == "MEDIUM":
            rank = random.randint(4, 7)
        elif difficulty == "HIGH":
            rank = random.randint(5, 10)
            
        # Distribute points based on rank
        total_points = SPIRIT_RANK_POINTS.get(rank, 10)
        stats["rank"] = rank
        
        # Split points among rage, gnosis, and willpower (spirit attributes)
        stats["rage"] = random.randint(1, total_points // 3)
        stats["gnosis"] = random.randint(1, total_points // 3)
        stats["willpower"] = random.randint(1, total_points // 3)
        
        # Add charms
        charm_count = DIFFICULTY[difficulty]["charms"]
        selected_charms = get_random_subset(CHARMS, charm_count)
        
        # Make sure spirits have materialize charm
        if "Materialize" not in selected_charms:
            selected_charms.append("Materialize")
            
        stats["charms"] = selected_charms
    
    # Add some random backgrounds for everyone
    backgrounds = ["allies", "contacts", "resources", "status", "influence"]
    num_backgrounds = random.randint(1, 3)
    selected_backgrounds = get_random_subset(backgrounds, num_backgrounds)
    
    stats["backgrounds"] = {}
    for bg in selected_backgrounds:
        stats["backgrounds"][bg] = random.randint(1, 3)
    
    return stats

def format_npc_stats_display(stats):
    """Format NPC stats for display in game."""
    lines = ["|c== NPC Stats ==|n"]
    
    # Basic info
    lines.append(f"|wSplat:|n {stats['splat'].title()}")
    
    # Attributes
    lines.append("\n|yAttributes:|n")
    for category, attrs in ATTRIBUTES.items():
        cat_line = f"  |w{category.title()}:|n "
        attr_items = []
        for attr in attrs:
            if attr in stats["attributes"]:
                attr_items.append(f"{attr.title()} {stats['attributes'][attr]}")
        cat_line += ", ".join(attr_items)
        lines.append(cat_line)
    
    # Abilities (only show those with points)
    if stats["abilities"]:
        lines.append("\n|yAbilities:|n")
        ability_lines = []
        for ability, value in sorted(stats["abilities"].items()):
            if value > 0:
                ability_lines.append(f"{ability.replace('_', ' ').title()} {value}")
        
        # Format in columns or single line depending on count
        if len(ability_lines) > 6:
            # Create columns
            col_size = (len(ability_lines) + 1) // 2
            for i in range(col_size):
                col1 = ability_lines[i] if i < len(ability_lines) else ""
                col2 = ability_lines[i + col_size] if i + col_size < len(ability_lines) else ""
                if col2:
                    lines.append(f"  {col1:<25} {col2}")
                else:
                    lines.append(f"  {col1}")
        else:
            # Single column
            for ability_line in ability_lines:
                lines.append(f"  {ability_line}")
    
    # Supernatural powers based on splat
    if "disciplines" in stats and stats["disciplines"]:
        lines.append("\n|yDisciplines:|n")
        disc_items = [f"{disc.title()} {value}" for disc, value in stats["disciplines"].items()]
        lines.append("  " + ", ".join(disc_items))
    
    if "spheres" in stats and stats["spheres"]:
        lines.append("\n|ySpheres:|n")
        sphere_items = [f"{sphere.title()} {value}" for sphere, value in stats["spheres"].items()]
        lines.append("  " + ", ".join(sphere_items))
        lines.append(f"  |wArete:|n {stats['arete']}")
    
    if "gifts" in stats and stats["gifts"]:
        lines.append("\n|yGifts:|n")
        gift_items = [f"{gift}" for gift in stats["gifts"].keys()]
        lines.append("  " + ", ".join(gift_items))
        
        if "rage" in stats:
            lines.append(f"  |wRage:|n {stats['rage']}")
        if "gnosis" in stats:
            lines.append(f"  |wGnosis:|n {stats['gnosis']}")
    
    if "numina" in stats and stats["numina"]:
        lines.append("\n|yNumina:|n")
        numina_items = [f"{numina.title()} {value}" for numina, value in stats["numina"].items()]
        lines.append("  " + ", ".join(numina_items))
    
    if "charms" in stats and stats["charms"]:
        lines.append("\n|yCharms:|n")
        lines.append("  " + ", ".join(stats["charms"]))
        if "rank" in stats:
            lines.append(f"  |wRank:|n {stats['rank']}")
    
    # Backgrounds
    if stats["backgrounds"]:
        lines.append("\n|yBackgrounds:|n")
        bg_items = [f"{bg.title()} {value}" for bg, value in stats["backgrounds"].items()]
        lines.append("  " + ", ".join(bg_items))
    
    # Willpower and other derived stats
    lines.append(f"\n|wWillpower:|n {stats['willpower']}")
    
    if "blood_pool" in stats:
        lines.append(f"|wBlood Pool:|n {stats['blood_pool']}")
    
    if "quintessence" in stats:
        lines.append(f"|wQuintessence:|n {stats['quintessence']}")
    
    return "\n".join(lines)