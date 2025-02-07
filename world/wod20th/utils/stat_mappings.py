# Identity stats
IDENTITY_PERSONAL = {
    'full name': ('identity', 'personal'),
    'date of birth': ('identity', 'personal'),
    'date of embrace': ('identity', 'personal'),
    'nature': ('identity', 'personal'),
    'demeanor': ('identity', 'personal'),
    'concept': ('identity', 'personal'),
    'enlightenment': ('identity', 'personal')
}

IDENTITY_LINEAGE = {
    'clan': ('identity', 'lineage'),
    'generation': ('identity', 'lineage'),
    'sire': ('identity', 'lineage'),
    'tribe': ('identity', 'lineage'),
    'breed': ('identity', 'lineage'),
    'auspice': ('identity', 'lineage'),
    'aspect': ('identity', 'lineage'),
    'kith': ('identity', 'lineage'),
    'seeming': ('identity', 'lineage'),
    'house': ('identity', 'lineage'),
    'tradition': ('identity', 'lineage'),
    'convention': ('identity', 'lineage'),
    'affiliation': ('identity', 'lineage'),
    'essence': ('identity', 'lineage'),
    'signature': ('identity', 'lineage'),
    'affinity sphere': ('identity', 'lineage'),
    'possesed type': ('identity', 'lineage'),
    'mortalplus type': ('identity', 'lineage'),
    'companion type': ('identity', 'lineage'),
    'varna': ('identity', 'lineage'),
    'crown': ('identity', 'lineage'),
    'court': ('identity', 'lineage'),
    'camp': ('identity', 'lineage'),
    'lodge': ('identity', 'lineage'),
    'fang house': ('identity', 'lineage'),
    'ananasi faction': ('identity', 'lineage'),
    'ananasi cabal': ('identity', 'lineage'),
    'kitsune path': ('identity', 'lineage'),
    'kitsune faction': ('identity', 'lineage'),
    'ajaba faction': ('identity', 'lineage')
    
    
}

# Special stats that need custom handling
SPECIAL_STATS = [
    'splat', 'type', 'nature', 'demeanor', 'enlightenment', 'generation',
    'kith', 'phyla', 'breed', 'auspice', 'aspect', 'path', 'tribe', 'essence',
    'gnosis'
]

# Splat-specific backgrounds
VAMPIRE_BACKGROUNDS = [
    'Generation',
    'Herd'
]

CHANGELING_BACKGROUNDS = [
    'Chimera',
    'Dreamers',
    'Holdings',
    'Remembrance',
    'Retinue',
    'Title',
    'Treasure'
]

MAGE_BACKGROUNDS = [
    'Arcane',
    'Avatar',
    'Demesne',
    'Dream',
    'Familiar',
    'Blessing',
    'Companion',
    'Legend',
    'Node',
    'Sanctum',
    'Wonder'
]

# Mage affiliation-specific backgrounds
TECHNOCRACY_BACKGROUNDS = [
    'Genius',
    'Cloaking',
    'Hypercram',
    'Laboratory',
    'Requisitions',
    'Secret Weapons',
    'Construct'
]

TRADITIONS_BACKGROUNDS = [
    'Chantry'
]

NEPHANDI_BACKGROUNDS = [
    'Labyrinth'
]

SHIFTER_BACKGROUNDS = [
    'Ancestors',
    'Fate',
    'Fetish',
    'Kinfolk',
    'Pure Breed',
    'Rites',
    'Spirit Heritage',
    'Den-Realm',
    'Umbral Glade',
    'Mnesis',
    'Wallow',
    'Ananta',
    'Secrets',
    'Umbral Maps'
]

SORCERER_BACKGROUNDS = [
    'Guide',
    'Spirit Ridden',
    'Techne'
]

# Universal backgrounds
UNIVERSAL_BACKGROUNDS = [
    'Allies',
    'Contacts',
    'Fame',
    'Influence',
    'Mentor',
    'Resources',
    'Retainers',
    'Status',
    'Library',
    'Past Lives',
    'Backup',
    'Certification',
    'Patron',
    'Alternate Identity',
    'Destiny',
    'Rank',
    'Spies',
    'Totem'
]

# Secondary abilities
SECONDARY_TALENTS = {
    'artistry': ('abilities', 'secondary_talent'),
    'carousing': ('abilities', 'secondary_talent'),
    'diplomacy': ('abilities', 'secondary_talent'),
    'intrigue': ('abilities', 'secondary_talent'),
    'mimicry': ('abilities', 'secondary_talent'),
    'scrounging': ('abilities', 'secondary_talent'),
    'seduction': ('abilities', 'secondary_talent'),
    'style': ('abilities', 'secondary_talent'),
    'blatancy': ('abilities', 'secondary_talent'),
    'flying': ('abilities', 'secondary_talent'),
    'high ritual': ('abilities', 'secondary_talent'),
    'lucid dreaming': ('abilities', 'secondary_talent')
}

SECONDARY_SKILLS = {
    'archery': ('abilities', 'secondary_skill'),
    'fencing': ('abilities', 'secondary_skill'),
    'fortune-telling': ('abilities', 'secondary_skill'),
    'gambling': ('abilities', 'secondary_skill'),
    'jury-rigging': ('abilities', 'secondary_skill'),
    'pilot': ('abilities', 'secondary_skill'),
    'torture': ('abilities', 'secondary_skill'),
    'biotech': ('abilities', 'secondary_skill'),
    'do': ('abilities', 'secondary_skill'),
    'energy weapons': ('abilities', 'secondary_skill'),
    'helmsman': ('abilities', 'secondary_skill'),
    'microgravity ops': ('abilities', 'secondary_skill')
}

SECONDARY_KNOWLEDGES = {
    'area knowledge': ('abilities', 'secondary_knowledge'),
    'cultural savvy': ('abilities', 'secondary_knowledge'),
    'demolitions': ('abilities', 'secondary_knowledge'),
    'herbalism': ('abilities', 'secondary_knowledge'),
    'media': ('abilities', 'secondary_knowledge'),
    'power-brokering': ('abilities', 'secondary_knowledge'),
    'vice': ('abilities', 'secondary_knowledge'),
    'cybernetics': ('abilities', 'secondary_knowledge'),
    'hypertech': ('abilities', 'secondary_knowledge'),
    'paraphysics': ('abilities', 'secondary_knowledge'),
    'xenobiology': ('abilities', 'secondary_knowledge')
}

# Generation mapping
GENERATION_MAP = {
    -2: "15th",  # 15th Generation flaw
    -1: "14th",  # 14th Generation flaw
    0: "13th",   # Default starting generation
    1: "12th",
    2: "11th",
    3: "10th",
    4: "9th",
    5: "8th",
    6: "7th",
    7: "6th"
}

# Blood pool by generation background value
BLOOD_POOL_MAP = {
    -2: 10,    # 15th generation (flaw)
    -1: 10,    # 14th generation (flaw)
    0: 10,     # 13th generation
    1: 11,     # 12th generation
    2: 12,     # 11th generation
    3: 13,     # 10th generation
    4: 14,     # 9th generation
    5: 15,     # 8th generation
    6: 20,     # 7th generation
    7: 30      # 6th generation
}

# Generation-affecting flaws
GENERATION_FLAWS = {
    '14th generation': -1,
    '15th generation': -2
}

# Valid types for different splats
VALID_MORTALPLUS_TYPES = ['ghoul', 'kinfolk', 'kinain', 'sorcerer', 'faithful', 'psychic']
VALID_POSSESSED_TYPES = ['fomori', 'kami']
VALID_SHIFTER_TYPES = ['garou', 'bastet', 'corax', 'gurahl', 'mokole', 'nagah', 'nuwisha', 'ratkin', 'rokea', 'ananasi', 'ajaba']
VALID_SPLATS = ['changeling', 'vampire', 'shifter', 'companion', 'mage', 'mortal', 'mortal+', 'possessed'] 

from typing import List, Tuple

# Main categories for organization
CATEGORIES = [
    ('attributes', 'Attributes'),
    ('abilities', 'Abilities'),
    ('secondary_abilities', 'Secondary Abilities'),
    ('advantages', 'Advantages'),
    ('backgrounds', 'Backgrounds'),
    ('powers', 'Powers'),
    ('merits', 'Merits'),
    ('flaws', 'Flaws'),
    ('traits', 'Traits'),
    ('identity', 'Identity'),
    ('archetype', 'Archetype'),
    ('virtues', 'Virtues'),
    ('legacy', 'Legacy'),
    ('pools', 'Pools'),
    ('other', 'Other')
]

# Stat types define the actual type of the stat
STAT_TYPES = [
    ('attribute', 'Attribute'),
    ('ability', 'Ability'),
    ('secondary_ability', 'Secondary Ability'),
    ('advantage', 'Advantage'),
    ('background', 'Background'),
    ('lineage', 'Lineage'),
    ('discipline', 'Discipline'),
    ('combodiscipline', 'Combo Discipline'),
    ('thaumaturgy', 'Thaumaturgy'),
    ('gift', 'Gift'),
    ('rite', 'Rite'),
    ('sphere', 'Sphere'),
    ('rote', 'Rote'),
    ('art', 'Art'),
    ('splat', 'Splat'),
    ('edge', 'Edge'),
    ('special_advantage', 'Special Advantage'),
    ('realm', 'Realm'),
    ('blessing', 'Blessing'),
    ('path', 'Path'),
    ('sorcery', 'Sorcery'),
    ('faith', 'Faith'),
    ('numina', 'Numina'),
    ('hedge_ritual', 'Hedge Ritual'),
    ('enlightenment', 'Enlightenment'),
    ('power', 'Power'),
    ('virtue', 'Virtue'),
    ('vice', 'Vice'),
    ('merit', 'Merit'),
    ('flaw', 'Flaw'),
    ('possessed_type', 'Possessed Type'),
    ('trait', 'Trait'),
    ('skill', 'Skill'),
    ('knowledge', 'Knowledge'),
    ('talent', 'Talent'),
    ('secondary_knowledge', 'Secondary Knowledge'),
    ('secondary_talent', 'Secondary Talent'),
    ('secondary_skill', 'Secondary Skill'),
    ('specialty', 'Specialty'),
    ('physical', 'Physical'),
    ('social', 'Social'),
    ('mental', 'Mental'),
    ('personal', 'Personal'),
    ('supernatural', 'Supernatural'),
    ('moral', 'Moral'),
    ('temporary', 'Temporary'),
    ('dual', 'Dual'),
    ('renown', 'Renown'),
    ('arete', 'Arete'),
    ('banality', 'Banality'),
    ('glamour', 'Glamour'),
    ('essence', 'Essence'),
    ('quintessence', 'Quintessence'),
    ('blood', 'Blood'),
    ('rage', 'Rage'),
    ('gnosis', 'Gnosis'),
    ('willpower', 'Willpower'),
    ('resonance', 'Resonance'),
    ('synergy', 'Synergy'),
    ('paradox', 'Paradox'),
    ('kith', 'Kith'),
    ('phyla', 'Phyla'),
    ('seeming', 'Seeming'),
    ('house', 'House'),
    ('seelie-legacy', 'Seelie Legacy'),
    ('unseelie-legacy', 'Unseelie Legacy'),
    ('court', 'Court'),
    ('tribe', 'Tribe'),
    ('camp', 'Camp'),
    ('breed', 'Breed'),
    ('clan', 'Clan'),
    ('companion_type', 'Companion Type'),
    ('mortalplus_type', 'Mortal+ Type'),
    ('varna', 'Varna')
]

# Mapping of stat types to their categories
STAT_TYPE_TO_CATEGORY = {
    # Attributes
    'physical': 'attributes',
    'social': 'attributes',
    'mental': 'attributes',
    
    # Abilities
    'skill': 'abilities',
    'knowledge': 'abilities',
    'talent': 'abilities',
    'secondary_knowledge': 'secondary_abilities',
    'secondary_talent': 'secondary_abilities',
    'secondary_skill': 'secondary_abilities',
    
    # Identity
    'personal': 'identity',
    'lineage': 'identity',
    
    # Powers
    'discipline': 'powers',
    'combodiscipline': 'powers',
    'thaumaturgy': 'powers',
    'gift': 'powers',
    'rite': 'powers',
    'sphere': 'powers',
    'rote': 'powers',
    'art': 'powers',
    'realm': 'powers',
    'blessing': 'powers',
    'path': 'powers',
    'sorcery': 'powers',
    'faith': 'powers',
    'numina': 'powers',
    'hedge_ritual': 'powers',
    
    # Other categories
    'merit': 'merits',
    'flaw': 'flaws',
    'virtue': 'virtues',
    'vice': 'virtues',
    'background': 'advantages',
    'advantage': 'advantages'
}

# Identity stat mappings
IDENTITY_STATS = {
    'personal': [
        'Full Name', 'Concept', 'Date of Birth', 'Date of Embrace', 
        'Nature', 'Demeanor', 'Motivation', 'Form'
    ],
    'lineage': [
        'Sire', 'Clan', 'Generation', 'Enlightenment', 'Type', 'Tribe', 
        'Breed', 'Auspice', 'Tradition', 'Convention', 'Affiliation'
    ]
}

# Special stat type overrides based on splat
SPLAT_STAT_OVERRIDES = {
    'changeling': {
        'Nature': ('realm', 'powers'),
        'Enlightenment': ('personal', 'identity')
    },
    'vampire': {
        'Nature': ('personal', 'identity'),
        'Enlightenment': ('lineage', 'identity')
    },
    'mage': {
        'Nature': ('personal', 'identity'),
        'Enlightenment': ('personal', 'identity')
    }
}

# Add ARTS and REALMS if they don't exist
ARTS = {
    'Autumn', 'Chicanery', 'Chronos', 'Contract', "Dragon's Ire", 'Legerdemain', 'Metamorphosis', 'Naming', 
    'Oneiromancy', 'Primal', 'Pyretics', 'Skycraft', 'Soothsay', 'Sovereign', 'Spring', 'Summer', 'Wayfare', 'Winter'
}

REALMS = {
    'Actor', 'Fae', 'Nature', 'Prop', 'Scene', 'Time'
}

# Add Mage-specific constants
MAGE_SPHERES = {
    'Correspondence', 'Data', 'Dimensional Science', 'Entropy', 'Forces',
    'Life', 'Matter', 'Mind', 'Prime', 'Primal Utility', 'Spirit', 'Time'
}

TRADITION_SUBFACTION = {
    'Akashic Brotherhood': ['Vajrapani', 'Li Hai', 'Wu Lung', 'Wu-Keng'],
    'Celestial Chorus': ['Cabal of Pure Thought', 'Gabrielites', 'Templars'],
    'Cult of Ecstasy': ['Aghoris', 'Children of Rashomon', 'Sahajiya'],
    'Dreamspeakers': ['Kopa Loei', 'Ngoma', 'Bata\'a', 'Taftani'],
    'Euthanatos': ['Chakravanti', 'Natatapas', 'Lhaksmists', 'Madzimbabwe'],
    'Order of Hermes': ['House Bjornaer', 'House Bonisagus', 'House Criamon', 'House Ex Miscellanea',
                       'House Flambeau', 'House Fortunae', 'House Hong Lei', 'House Janissary',
                       'House Jerbiton', 'House Mercere', 'House Merinita', 'House Quaesitor',
                       'House Shaea', 'House Skopos', 'House Solificati', 'House Tharsis',
                       'House Thig', 'House Tremere', 'House Tytalus', 'House Validas',
                       'House Verditius', 'House Xaos'],
    'Sons of Ether': ['Cybermancers', 'Ethernauts', 'Adventurers', 'Difference Engineers'],
    'Verbena': ['Teuthonic', 'Green Path', 'Witch', 'Voudoun'],
    'Virtual Adepts': ['Cybernauts', 'Cyberpunks', 'Reality Hackers']
}

METHODOLOGIES = {
    'Iteration X': ['Statisticians', 'Macrotechnicians', 'Cybernetic Research',
                   'Biotechnology', 'Pharmacopeists', 'Robotics'],
    'New World Order': ['Ivory Tower', 'Operatives', 'Enforcers', 'Media Control',
                       'Social Engineering', 'Political Science'],
    'Progenitors': ['Pharmacopoeists', 'Genegineers', 'FACADE Engineers',
                    'Damage Control', 'Psychiatry'],
    'Syndicate': ['Auditors', 'Media', 'Financiers', 'Healthcare',
                  'Human Resources', 'Psychological Warfare'],
    'Void Engineers': ['Dimensional Science', 'R&D', 'DSEE', 'HITMark',
                      'Neutralization', 'Reality Corps']
}

# Add Possessed-specific constants
POSSESSED_TYPES = {
    'Fomori': 'Bane-possessed',
    'Kami': 'Spirit-possessed'
}

POSSESSED_POOLS = {
    'Fomori': {
        'Willpower': {'default': 3, 'max': 10},
        'Rage': {'default': 0, 'max': 10},
        'Gnosis': {'default': 0, 'max': 10}
    },
    'Kami': {
        'Willpower': {'default': 4, 'max': 10},
        'Gnosis': {'default': 1, 'max': 10},
        'Rage': {'default': 0, 'max': 10}
    }
}

# Pool Types and Values
POOL_TYPES = {
    'dual': {
        'Willpower': {'min': 1, 'max': 10},
        'Rage': {'min': 0, 'max': 10},
        'Gnosis': {'min': 0, 'max': 10},
        'Blood': {'min': 0, 'max': 20},
        'Glamour': {'min': 0, 'max': 10},
        'Banality': {'min': 0, 'max': 10},
        'Paradox': {'min': 0, 'max': 20},
        'Essence': {'min': 0, 'max': 10},
        'Mana': {'min': 0, 'max': 10}
    },
    'moral': {
        'Road': {'min': 0, 'max': 10},
        'Path': {'min': 0, 'max': 10}
    },
    'advantage': {
        'Arete': {'min': 1, 'max': 10},
        'Enlightenment': {'min': 1, 'max': 10}
    },
    'resonance': {
        'Dynamic': {'min': 0, 'max': 5},
        'Entropic': {'min': 0, 'max': 5},
        'Static': {'min': 0, 'max': 5}
    }
}

# Power Categories
POWER_CATEGORIES = {
    'gift': 'powers',
    'discipline': 'powers',
    'sphere': 'powers',
    'art': 'powers',
    'realm': 'powers',
    'sorcery': 'powers',
    'thaumaturgy': 'powers',
    'thaum_ritual': 'powers',
    'special_advantage': 'powers',
    'charm': 'powers',
    'blessing': 'powers',
    'faith': 'powers',
    'numina': 'powers',
    'ritual': 'powers',
    'hedge_ritual': 'powers',
    'combodiscipline': 'powers'
}

# Ability Types
ABILITY_TYPES = {
    'talent': {
        'primary': ['Athletics', 'Alertness', 'Awareness', ...],
        'secondary': SECONDARY_TALENTS  # Already defined
    },
    'skill': {
        'primary': ['Animal Ken', 'Crafts', 'Drive', ...],
        'secondary': SECONDARY_SKILLS  # Already defined
    },
    'knowledge': {
        'primary': ['Academics', 'Computer', 'Finance', ...],
        'secondary': SECONDARY_KNOWLEDGES  # Already defined
    }
}

# Attribute Categories
ATTRIBUTE_CATEGORIES = {
    'physical': ['Strength', 'Dexterity', 'Stamina'],
    'social': ['Charisma', 'Manipulation', 'Appearance'],
    'mental': ['Perception', 'Intelligence', 'Wits']
}

# Special Advantage Definitions
SPECIAL_ADVANTAGES = {
    'wings': {'min': 3, 'max': 5, 'flight': True},
    'alacrity': {'min': 1, 'max': 5},
    'ferocity': {'min': 1, 'max': 5},
    'human guise': {'min': 1, 'max': 3},
    'regrowth': {'min': 1, 'max': 6},
    'universal translator': {'min': 1, 'max': 5},
    'venom': {'min': 1, 'max': 15}
}

# Validation Mappings
import json
import os
from pathlib import Path

# Helper function to load JSON files
def load_json_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Helper function to organize merits/flaws by type
def organize_by_type(items, category):
    organized = {
        'physical': [],
        'social': [],
        'mental': [],
        'supernatural': []
    }
    
    for item in items:
        if item.get('category') == category and 'stat_type' in item and 'name' in item:
            stat_type = item['stat_type'].lower()
            if stat_type in organized:
                organized[stat_type].append(item['name'])
    
    return organized

# Path to data directory
DATA_DIR = Path(__file__).parent.parent / 'data'

# Load all merit/flaw data
MERIT_FILES = [
    'changeling_merits.json',
    'fera_merits.json',
    'garou_merits.json',
    'mage_merits.json',
    'mortalplus_merits.json',
    'vampire_merits.json'
]

FLAW_FILES = [
    'changeling_flaws.json',
    'fera_flaws.json',
    'garou_flaws.json',
    'mage_flaws.json',
    'mortalplus_flaws.json',
    'vampire_flaws.json'
]

# Load and combine all merit data
ALL_MERITS = []
for file_name in MERIT_FILES:
    file_path = DATA_DIR / file_name
    if file_path.exists():
        ALL_MERITS.extend(load_json_data(file_path))

# Load and combine all flaw data
ALL_FLAWS = []
for file_name in FLAW_FILES:
    file_path = DATA_DIR / file_name
    if file_path.exists():
        ALL_FLAWS.extend(load_json_data(file_path))

# Organize merits by type
MERIT_CATEGORIES = organize_by_type(ALL_MERITS, 'merits')

# Organize flaws by type
FLAW_CATEGORIES = organize_by_type(ALL_FLAWS, 'flaws')

# Create validation mappings
MERIT_VALUES = {
    item['name']: item['values'] if isinstance(item['values'], list) else [item['values']]
    for item in ALL_MERITS if 'name' in item and 'values' in item
}

FLAW_VALUES = {
    item['name']: item['values'] if isinstance(item['values'], list) else [item['values']]
    for item in ALL_FLAWS if 'name' in item and 'values' in item
}

# Additional metadata mappings
MERIT_REQUIREMENTS = {
    item['name']: item.get('requirements', [])
    for item in ALL_MERITS if 'name' in item
}

MERIT_SPLAT_RESTRICTIONS = {
    item['name']: {
        'splat': item.get('splat'),
        'splat_type': item.get('mortalplus_type', item.get('shifter_type'))
    }
    for item in ALL_MERITS if 'name' in item
}

FLAW_SPLAT_RESTRICTIONS = {
    item['name']: {
        'splat': item.get('splat'),
        'splat_type': item.get('mortalplus_type', item.get('shifter_type'))
    }
    for item in ALL_FLAWS if 'name' in item
}

# Update the existing STAT_VALIDATION dictionary
STAT_VALIDATION = {
    'pools': POOL_TYPES,
    'powers': POWER_CATEGORIES,
    'abilities': ABILITY_TYPES,
    'attributes': ATTRIBUTE_CATEGORIES,
    'flaws': FLAW_CATEGORIES,
    'merits': MERIT_CATEGORIES,
    'flaws': FLAW_CATEGORIES
}

def process_special_advantages(advantages):
    """Convert special advantages list into a validation dictionary"""
    processed = {}
    for item in advantages:
        if 'name' not in item or 'values' not in item:
            continue
            
        name = item['name'].lower()
        values = item['values'] if isinstance(item['values'], list) else [item['values']]
        
        # Create the advantage entry
        processed[name] = {
            'min': min(values),
            'max': max(values),
            'values': values,
            'description': item.get('description', ''),
            'game_line': item.get('game_line', 'Unknown'),
            'effects': parse_effects_from_description(item.get('description', ''))
        }
    return processed

def parse_effects_from_description(description):
    """Parse special effects from advantage description"""
    effects = {}
    desc_lower = description.lower()
    
    # Flight effects
    if any(word in desc_lower for word in ['flight', 'fly', 'flying']):
        effects['flight'] = True
        
    # Combat effects
    if 'damage' in desc_lower:
        effects['combat'] = True
        if 'lethal damage' in desc_lower:
            effects['damage_type'] = 'lethal'
        elif 'aggravated damage' in desc_lower:
            effects['damage_type'] = 'aggravated'
            
    # Resource requirements
    if 'willpower' in desc_lower:
        effects['requires_willpower'] = True
    if 'gnosis' in desc_lower:
        effects['requires_gnosis'] = True
        
    # Roll requirements
    if 'difficulty' in desc_lower:
        effects['has_roll'] = True
        
    # Special abilities
    if 'soak' in desc_lower:
        effects['soak'] = True
    if 'heal' in desc_lower or 'regenerat' in desc_lower:
        effects['healing'] = True
        
    return effects

def validate_special_advantage(name, value, character=None):
    """
    Validate a special advantage and its value
    Returns (is_valid, message, effects)
    """
    try:
        # Get the stat from database
        from world.wod20th.models import Stat
        stat = Stat.objects.get(
            name__iexact=name,
            stat_type='special_advantage'
        )
        
        try:
            value = int(value)
        except (TypeError, ValueError):
            return False, f"Value must be a number between {min(stat.values)} and {max(stat.values)}", None
            
        if value not in stat.values:
            return False, f"Invalid value. Must be one of: {', '.join(map(str, stat.values))}", None
        
        # Check character restrictions if character provided
        if character:
            # Example restriction check
            if 'flight' in stat.system and hasattr(character, 'size') and character.size > 3:
                return False, "Character too large for wings", None
        
        return True, value, parse_effects_from_description(stat.description)
        
    except Stat.DoesNotExist:
        return False, f"Invalid special advantage: {name}", None

def get_special_advantage_info(name):
    """Get detailed information about a special advantage"""
    try:
        from world.wod20th.models import Stat
        stat = Stat.objects.get(
            name__iexact=name,
            stat_type='special_advantage'
        )
        
        return {
            'name': stat.name,
            'description': stat.description,
            'values': stat.values,
            'game_line': stat.game_line,
            'effects': parse_effects_from_description(stat.description)
        }
    except Stat.DoesNotExist:
        return None

def list_special_advantages(game_line=None):
    """List all special advantages, optionally filtered by game line"""
    from world.wod20th.models import Stat
    query = Stat.objects.filter(stat_type='special_advantage')
    if game_line:
        query = query.filter(game_line=game_line)
        
    return [{
        'name': stat.name,
        'min': min(stat.values),
        'max': max(stat.values),
        'description': stat.description[:100] + '...' if len(stat.description) > 100 else stat.description
    } for stat in query]

# Update STAT_VALIDATION to include special advantages
STAT_VALIDATION.update({
    'special_advantages': SPECIAL_ADVANTAGES
})