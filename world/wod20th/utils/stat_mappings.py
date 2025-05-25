from world.wod20th.utils.sheet_constants import (
    TALENTS, SKILLS, KNOWLEDGES,
    SECONDARY_TALENTS, SECONDARY_SKILLS, SECONDARY_KNOWLEDGES,
    POWERS, BACKGROUNDS, MERITS, FLAWS, HEALTH, RENOWN,
    SHIFTER_TYPE, KITH, CLAN, BREED, GAROU_TRIBE,
    ATTRIBUTES, ABILITIES, ADVANTAGES
)
# Mapping of stat types to their categories

# Valid types for different splats
VALID_MORTALPLUS_TYPES = ['ghoul', 'kinfolk', 'kinain', 'sorcerer', 'faithful', 'psychic']
VALID_POSSESSED_TYPES = ['fomori', 'kami']
VALID_SHIFTER_TYPES = ['garou', 'bastet', 'corax', 'gurahl', 'mokole', 'nagah', 'nuwisha', 'ratkin', 'rokea', 'ananasi', 'ajaba']
VALID_SPLATS = ['changeling', 'vampire', 'shifter', 'companion', 'mage', 'mortal', 'mortal+', 'possessed'] 
REQUIRED_INSTANCES = ['Library', 'Status', 'Influence', 'Wonder', 'Secret Weapon', 'Companion', 
                      'Familiar', 'Enhancement', 'Laboratory', 'Favor', 'Acute Senses', 
                      'Enchanting Feature', 'Secret Code Language', 'Hideaway', 'Safehouse', 
                      'Sphere Natural', 'Phobia', 'Addiction', 'Allies', 'Contacts', 'Caretaker',
                      'Alternate Identity', 'Equipment', 'Professional Certification', 'Allergic',
                      'Impediment', 'Enemy', 'Mentor', 'Old Flame', 'Additional Discipline', 
                      'Totem', 'Boon', 'Treasure', 'Geas', 'Fetish', 'Chimerical Item', 'Chimerical Companion',
                      'Dreamers', 'Digital Dreamers', 'Addiction', 'Phobia', 'Derangement',
                      'Obsession', 'Compulsion', 'Bigot', 'Ability Deficit', 'Sect Enmity', 'Camp Enmity'
                     ] 
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

REQUIRED_INSTANCES = ['Library', 'Status', 'Influence', 'Wonder', 'Secret Weapon', 'Companion', 
                      'Familiar', 'Enhancement', 'Laboratory', 'Favor', 'Acute Senses', 
                      'Enchanting Feature', 'Secret Code Language', 'Hideaway', 'Safehouse', 
                      'Sphere Natural', 'Phobia', 'Addiction', 'Allies', 'Contacts', 'Caretaker',
                      'Alternate Identity', 'Equipment', 'Professional Certification', 'Allergic',
                      'Impediment', 'Enemy', 'Mentor', 'Old Flame', 'Additional Discipline', 
                      'Totem', 'Boon', 'Treasure', 'Geas', 'Fetish', 'Chimerical Item', 'Chimerical Companion',
                      'Dreamers', 'Digital Dreamers', 'Addiction', 'Phobia', 'Derangement',
                      'Obsession', 'Compulsion', 'Bigot', 'Ability Deficit', 'Sect Enmity', 'Camp Enmity'
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

# Identity stat mappings
IDENTITY_STATS = {
    'personal': [
        'Full Name', 'Concept', 'Date of Birth', 'Date of Embrace', 
        'Nature', 'Demeanor', 'Motivation', 'Form', 'Occupation',
        'Date of Chrysalis', 'Date of Awakening', 'First Change Date',
        'Date of Possession', 'Enlightenment', 'Tribal Name'
    ],
    'lineage': [
        'Sire', 'Clan', 'Generation', 'Enlightenment', 'Type', 'Tribe', 
        'Breed', 'Auspice', 'Tradition', 'Convention', 'Affiliation',
        'Aspect', 'Kitsune Path', 'Kitsune Faction', 'Ajaba Faction',
        'Crown', 'Camp', 'Lodge', 'Fang House', 'Ananta Faction', 'Ananta Cabal',
        'Kitsune Clan', 'Go-En', 'Sempai', 'Jamak Spirit', 'Seelie Legacy', 'Unseelie Legacy',
        'First Legacy', 'Second Legacy', 'Tradition Subfaction', 'Methodology',
        'Occupation', 'Signature', 'Essence', 'Affinity Sphere', 'Nephandi Faction',
        'Possessed Type', 'Mortal+ Type', 'Varna', 'Ananasi Faction', 'Ananasi Cabal',
        'Patron Totem', 'Pack', 'Society', 'Fellowship', 'Domitor', 'Companion Type', 
        'Motivation', 'Form', 'Phyla', 'Seeming', 'House', 'Court', 'Nunnehi Camp',
        'Nunnehi Seeming', 'Nunnehi Family', 'Nunnehi Totem', 'Affinity Realm', 'Elemental Affinity',
        'Fuel'
    ]
}

IDENTITY_PERSONAL = [
    'Full Name', 'Concept', 'Date of Birth', 'Date of Embrace', 
    'Nature', 'Demeanor', 'Motivation', 'Form', 'Occupation',
    'Date of Chrysalis', 'Date of Awakening', 'First Change Date',
    'Date of Possession', 'Enlightenment'
]

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
    'affinity realm': ('identity', 'lineage'),
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
    'ajaba faction': ('identity', 'lineage'),
    'fuel': ('identity', 'lineage'),
    'elemental affinity': ('identity', 'lineage'),
    'motivation': ('identity', 'lineage'),
    'form': ('identity', 'lineage'),
    'phyla': ('identity', 'lineage'),
    'seeming': ('identity', 'lineage'),
    'house': ('identity', 'lineage'),
    'tradition subfaction': ('identity', 'lineage'),
    'methodology': ('identity', 'lineage'),
    'spirit type': ('identity', 'lineage'),
    'spirit name': ('identity', 'lineage'),
    'domitor': ('identity', 'lineage'),
    'society': ('identity', 'lineage'),
    'order': ('identity', 'lineage'),
    'coven': ('identity', 'lineage'),
    'cabal': ('identity', 'lineage'),
    'plague': ('identity', 'lineage'),
    'stream': ('identity', 'lineage'),
    'kitsune path': ('identity', 'lineage'),
    'seelie legacy': ('identity', 'lineage'),
    'unseelie legacy': ('identity', 'lineage'),
    'first legacy': ('identity', 'lineage'),
    'second legacy': ('identity', 'lineage'),
    'methodology': ('identity', 'lineage'),
    'occupation': ('identity', 'lineage'),
    'signature': ('identity', 'lineage'),
    'essence': ('identity', 'lineage'),
    'affinity sphere': ('identity', 'lineage'),
    'nephandi faction': ('identity', 'lineage'),
    'deed name': ('identity', 'lineage'),
    'phyla': ('identity', 'lineage'),
    'kinfolk breed': ('identity', 'lineage')
}

ELEMENTAL_AFFINITY = {
            "Air": [
                "Blustery Curmudgeon",
                "Bitter Warrior",
                "Cold Cynic",
                "Fleeting Dilettante",
                "Flighty Scatterbrain",
                "Gentle Friend",
                "Stormy Fanatic"
            ],
            "Earth": [
                "Crystalline Idealist",
                "Fertile Procreator",
                "Flowery Bon Vivant",
                "Resolute Architect",
                "Sheltering Caregiver",
                "Solid Guardian",
                "Stony Curmudgeon"
            ],
            "Fire": [
                "Burning Quester",
                "Fiery Rebel",
                "Glittering Dancer",
                "Illuminated Scholar",
                "Passionate Lover",
                "Lusty Reveler",
                "Warm Romantic"
            ],
            "Water": [
                "Babbling Jester",
                "Erosive Revolutionary",
                "Graceful Sensualist",
                "Quiet Thinker",
                "Stagnant Traditionalist",
                "Patient Conniver",
                "Wise Elder"
            ],
            "Metal": [
                "Bright Thinker",
                "Greedy Collector",
                "Harsh Scrapper",
                "Hot-Headed Braggart",
                "Temperamental Warrior",
                "Sharp-Witted Trickster",
                "Visionary Architect"
            ],
            "Wood": [
                "Bearer of Burdens",
                "Flexible Mediator",
                "Nurturing Parent",
                "Rooted Traditionalist",
                "Scattered Visionary",
                "Steadfast Protector",
                "Stout Defender"
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
ABILITY_TYPES = {
    'talent': {
        'primary': list(TALENTS.keys()),
        'secondary': SECONDARY_TALENTS
    },
    'skill': {
        'primary': list(SKILLS.keys()),
        'secondary': SECONDARY_SKILLS
    },
    'knowledge': {
        'primary': list(KNOWLEDGES.keys()),
        'secondary': SECONDARY_KNOWLEDGES
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
        'Humanity': {'min': 0, 'max': 10},
        'Path': {'min': 0, 'max': 10}
    },
    'advantage': {
        'Arete': {'min': 1, 'max': 10},
        'Enlightenment': {'min': 1, 'max': 10}
    },
    'synergy': {
        'Dynamic': {'min': 0, 'max': 5},
        'Entropic': {'min': 0, 'max': 5},
        'Static': {'min': 0, 'max': 5}
    }
}
IDENTITY_PERSONAL = {
    'full name': ('identity', 'personal'),
    'date of birth': ('identity', 'personal'),
    'date of embrace': ('identity', 'personal'),
    'date of chrysalis': ('identity', 'personal'),
    'date of awakening': ('identity', 'personal'),
    'first change date': ('identity', 'personal'),
    'date of possession': ('identity', 'personal'),
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
    'affinity realm': ('identity', 'lineage'),
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
    'ajaba faction': ('identity', 'lineage'),
    'fuel': ('identity', 'lineage'),
    'elemental affinity': ('identity', 'lineage'),
    'motivation': ('identity', 'lineage'),
    'form': ('identity', 'lineage'),
    'phyla': ('identity', 'lineage'),
    'seeming': ('identity', 'lineage'),
    'house': ('identity', 'lineage'),
    'tradition subfaction': ('identity', 'lineage'),
    'methodology': ('identity', 'lineage'),
    'spirit type': ('identity', 'lineage'),
    'spirit name': ('identity', 'lineage'),
    'domitor': ('identity', 'lineage'),
    'society': ('identity', 'lineage'),
    'order': ('identity', 'lineage'),
    'coven': ('identity', 'lineage'),
    'cabal': ('identity', 'lineage'),
    'plague': ('identity', 'lineage'),
    'stream': ('identity', 'lineage'),
    'kitsune path': ('identity', 'lineage'),
    'seelie legacy': ('identity', 'lineage'),
    'unseelie legacy': ('identity', 'lineage'),
    'first legacy': ('identity', 'lineage'),
    'second legacy': ('identity', 'lineage'),
    'methodology': ('identity', 'lineage'),
    'occupation': ('identity', 'lineage'),
    'signature': ('identity', 'lineage'),
    'essence': ('identity', 'lineage'),
    'affinity sphere': ('identity', 'lineage'),
    'nephandi faction': ('identity', 'lineage'),
    'deed name': ('identity', 'lineage'),
    'phyla': ('identity', 'lineage')
}

# Secondary abilities
SECONDARY_TALENTS = {
    'artistry': ('secondary_abilities', 'secondary_talent'),
    'carousing': ('secondary_abilities', 'secondary_talent'),
    'diplomacy': ('secondary_abilities', 'secondary_talent'),
    'do': ('secondary_abilities', 'secondary_talent'),
    'intrigue': ('secondary_abilities', 'secondary_talent'),
    'mimicry': ('secondary_abilities', 'secondary_talent'),
    'scrounging': ('secondary_abilities', 'secondary_talent'),
    'seduction': ('secondary_abilities', 'secondary_talent'),
    'style': ('secondary_abilities', 'secondary_talent'),
    'blatancy': ('secondary_abilities', 'secondary_talent'),
    'flying': ('secondary_abilities', 'secondary_talent'),
    'high ritual': ('secondary_abilities', 'secondary_talent'),
    'lucid dreaming': ('secondary_abilities', 'secondary_talent')
}

SECONDARY_SKILLS = {
    'archery': ('secondary_abilities', 'secondary_skill'),
    'fencing': ('secondary_abilities', 'secondary_skill'),
    'fortune-telling': ('secondary_abilities', 'secondary_skill'),
    'gambling': ('secondary_abilities', 'secondary_skill'),
    'jury-rigging': ('secondary_abilities', 'secondary_skill'),
    'martial arts': ('secondary_abilities', 'secondary_skill'),
    'pilot': ('secondary_abilities', 'secondary_skill'),
    'torture': ('secondary_abilities', 'secondary_skill'),
    'biotech': ('secondary_abilities', 'secondary_skill'),
    'energy weapons': ('secondary_abilities', 'secondary_skill'),
    'helmsman': ('secondary_abilities', 'secondary_skill'),
    'microgravity ops': ('secondary_abilities', 'secondary_skill')
}

SECONDARY_KNOWLEDGES = {
    'area knowledge': ('secondary_abilities', 'secondary_knowledge'),
    'cultural savvy': ('secondary_abilities', 'secondary_knowledge'),
    'demolitions': ('secondary_abilities', 'secondary_knowledge'),
    'herbalism': ('secondary_abilities', 'secondary_knowledge'),
    'media': ('secondary_abilities', 'secondary_knowledge'),
    'power-brokering': ('secondary_abilities', 'secondary_knowledge'),
    'vice': ('secondary_abilities', 'secondary_knowledge'),
    'cybernetics': ('secondary_abilities', 'secondary_knowledge'),
    'hypertech': ('secondary_abilities', 'secondary_knowledge'),
    'paraphysics': ('secondary_abilities', 'secondary_knowledge'),
    'xenobiology': ('secondary_abilities', 'secondary_knowledge')
}

# Special stats that need custom handling
SPECIAL_STATS = [
    'splat', 'type', 'nature', 'demeanor', 'enlightenment', 'generation',
    'kith', 'phyla', 'breed', 'auspice', 'aspect', 'path', 'tribe', 'essence',
    'gnosis'
]

SECT_CHOICES = [
    'Camarilla', 'Sabbat', 'Anarch', 'Independent'
]

# Background Lists
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
    'Organizational Rank',
    'Spies',
    'Secrets',
    'Totem',
    'Artifact',
    'Mob',
    'Base of Operations',
    'Antecessor',
    'Paranormal Tools',
    'Caretaker',
    'Cult',
    'Armory',
    'Equipment',
    'Servants',
    'Reliquary'
]

VAMPIRE_BACKGROUNDS = [
    'Generation',
    'Herd',
    'Anarch Information Exchange',
    'Black Hand Membership',
    'Communal Haven',
    'Ritae',
    'Blasphemous Shrine',
    'Memento de Morte',
    'Spirit Slaves',
    'Oubliette'
]

CHANGELING_BACKGROUNDS = [
    'Chimera',
    'Dreamers',
    'Holdings',
    'Remembrance',
    'Retinue',
    'Title',
    'Treasure',
    'Digital Dreamers',
    'Husk',
    'Circle',
    'Spirit Companion',
    'Vision',
    'Changeling Companion',
    'Chimerical Item'
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
    'Wonder',
    'Years',
    'Enhancement'
]

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
    'Umbral Maps',
    'Batsu',
    'Kitsune Clan',
    'Go-En',
    'Sempai',
    'Jamak'
]

SORCERER_BACKGROUNDS = [
    'Guide',
    'Spirit Ridden',
    'Techne'
]

KINAIN_BACKGROUNDS = [
    'Faerie Blood'
]

# Category Mappings
STAT_TYPE_TO_CATEGORY = {
    'attributes': {'physical': {}, 'social': {}, 'mental': {}},
    'abilities': {
        'skill': {},
        'knowledge': {},
        'talent': {},
        'secondary_abilities': {
            'secondary_knowledge': {},
            'secondary_talent': {},
            'secondary_skill': {}
        }
    },
    'identity': {
        'personal': {},
        'lineage': {},
        'identity': {}
    },
    'powers': {
        'discipline': {},
        'combodiscipline': {},
        'thaumaturgy': {},
        'thaum_ritual': {},
        'gift': {},
        'rite': {},
        'sphere': {},
        'rote': {},
        'art': {},
        'realm': {},
        'blessing': {},
        'charm': {},
        'sorcery': {},
        'faith': {},
        'numina': {},
        'ritual': {},
        'hedge_ritual': {}
    },
    'merits': {
        'physical': {},
        'social': {},
        'mental': {},
        'supernatural': {}
    },
    'flaws': {
        'physical': {},
        'social': {},
        'mental': {},
        'supernatural': {}
    },
    'virtues': {
        'moral': {},
        'advantage': {},
        'synergy': {}
    },
    'backgrounds': {
        'background': {}
    },
    'advantages': {
        'renown': {}
    },
    'pools': {
        'dual': {},
        'moral': {},
        'advantage': {},
        'resonance': {}
    }
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



# Add ARTS and REALMS if they don't exist
ARTS = {
    'Autumn', 'Chicanery', 'Chronos', 'Contract', "Dragon's Ire", 'Legerdemain', 'Metamorphosis', 'Naming', 
    'Oneiromancy', 'Primal', 'Pyretics', 'Skycraft', 'Soothsay', 'Sovereign', 'Spring', 'Summer', 'Wayfare', 'Winter',
    'Infusion', 'Kryos', 'Storm Craft'
}

REALMS = {
    'Actor', 'Fae', 'Nature', 'Prop', 'Scene', 'Time'
}

# Add Mage-specific constants
MAGE_SPHERES = {
    'Correspondence', 'Data', 'Dimensional Science', 'Entropy', 'Forces',
    'Life', 'Matter', 'Mind', 'Prime', 'Primal Utility', 'Spirit', 'Time'
}

KINFOLK_BREED_CHOICES = [
    ('Ajaba', 'Ajaba'),
    ('Ananasi', 'Ananasi'),
    ('Ratkin', 'Ratkin'),
    ('Garou', 'Garou'),
    ('Kitsune', 'Kitsune'),
    ('Rokea', 'Rokea'),
    ('Mokole', 'Mokole'),
    ('Gurahl', 'Gurahl'),
    ('Bastet', 'Bastet'),
    ('Nuwisha', 'Nuwisha'),
    ('Nagah', 'Nagah')
]

TRADITION_SUBFACTION = {
    'Akashic_Brotherhood': [
    'Chabnagpa', 'Lin Shen', 'Wu Shan', 'Yamabushi', 'Jina', 'Karmachakra', 'Shaolin', 'Blue Skins',
    'Mo-Tzu Fa', "Roda d'Oro", 'Gam Lung', 'Han Fei Tzu Academy', 'Kaizankai', 'Banner of the Ebon Dragon', 
    'Sulsa', 'Tenshi Arashi Ryu', 'Wu Lung'
    ],
    'Celestial Chorus': [
    'Brothers of St. Christopher', 'Chevra Kedisha', 'Knights of St. George', 'Order of St. Michael', 
    'Poor Knights of the Temple of Solomon', 'Sisters of Gabrielle', 'Alexandrian Society', 'Anchorite',
    'Children of Albi', 'Latitudinarian', 'Monist', 'Nashimite', 'Septarian', 'Hare Krishna', 'Hindu',
    'Jain', 'Son of Mithras', 'Rastafarian', 'Sikh', 'Sufi', 'Bat Binah', 'Song of the Ancients'
    ],
    'Cultists of Ecstasy': [
    'Erzuli Jingo', 'Kiss of Astarte', 'Maenad', "K'an Lu", 'Vratyas', 'Aghoris', 'Acharne', 'Freyji',
    'Sons of Wotan', 'Sutr', 'Joybringers', 'Dissonance Society', 'Klubwerks', "Children's Crusade",
    'Cult of Acceptance', 'Silver Bridges', 'Los Sabios Locos', "Ka'a", 'Khlysty Flagellants', 
    "Bongo's Rangers", 'Dervish', 'Confrerie Chango', 'Roda do Jogo', 'Los Sangradores', 'Studiosi',
    'Umilyenye'
    ],
    'Euthanatos': [
    'Aided', 'Devasu', 'Lhakmist', 'Natatapa', 'Knight of Radamanthys', 'Pomegranate Deme', "N'anga",
    'Ta Kiti', 'Albireo', 'Chakramuni', 'Golden Chalice', 'Pallottino', 'Scholars of the Wheel', "Yggdrasil's Keepers",
    'Yum Cimil'
    ],
    'Dreamspeakers': [
    'Balomb', 'Baruti', 'Contrary', 'Four Winds', 'Ghost Wheel Society', 'Keeper of the Sacred Fire', 
    'Kopa Loei', 'Red Spear Society', 'Sheikha', 'Solitaries', 'Spirit Smith', 'Uzoma'
    ],
    'Order of Hermes': [
    'House Bonisagus', 'House Flambeau', 'House Fortunae', 'House Quaesitori', 'House Shaea', 'House Tytalus',
    'House Verditius', 'House Criamon', 'House Jerbiton', 'House Merinita', 'House Skopos', 'House Xaos'
    ],
    'Verbena': [
    'Gardeners of the Tree', 'Lifeweavers', 'Moon-Seekers', 'Twisters of Fate', 'Techno-Pagans', 'Fairy Folk', 'New Age'
    ],
    'Sons of Ether': [
    'Ethernauts', 'Cybernauts', 'Utopians', 'Adventurers', 'Mad Scientists', 'Progressivists', 'Aquanauts'
    ],
    'Virtual Adepts': [
    'Chaoticians', 'Cyberpunk', 'Cypherpunks', 'Nexplorers', 'Reality Coders'
    ]
}

METHODOLOGIES = {
    'Iteration X': [
        'BioMechanics', 'Macrotechnicians', 'Statisticians', 'Time-Motion Managers'
    ],
    'New World Order': [
        'Ivory Tower', 'Operatives', 'Watchers', 'The Feed', 'Q Division', 'Agronomists'
    ],
    'Progenitor': [
        'Applied Sciences', 'Deviancy Scene investigators', 'Médecins Sans Superstition',
        'Biosphere Explorers', 'Damage Control', 'Ethical Compliance', 'FACADE Engineers',
        'Genegineers', 'Pharmacopoeists', 'Preservationists', 'Psychopharmacopoeists', 
        'Shalihotran Society'
    ],
    'Syndicate': [
        'Disbursements', 'Assessment Division', 'Reorganization Division', 'Procurements Division',
        'Extraction Division', 'Enforcers (Hollow Men)', 'Legal Division', 'Extralegal Division',
        'Extranational Division', 'Information Specialists', 'Special Information Security Division',
        'Financiers', 'Acquisitions Division', 'Entrepreneurship Division', 'Liquidation Division',
        'Media Control', 'Effects Division', 'Spin Division', 'Marketing Division', 'Special Projects Division'
    ],
    'Void Engineer': [
        'Border Corps Division', 'Earth Frontier Division', 'Aquatic Exploration Teams',
        'Cryoregional Specialists', 'Hydrothermal Botanical Mosaic Analysts', 'Inaccessible High Elevation Exploration Teams',
        'Subterranean Exploration Corps', 'Neutralization Specialist Corps', 'Neutralization Specialists', 
        'Enforcement Training and Conditioning Agency', 'Department of Psychological Evaluation and Maintenance', 'Pan-Dimensional Corps', 
        'Deep Exploration Teams', 'Solar Exploration Teams', 'Cybernauts', 'Chrononauts', 'Research & Execution'
    ]
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

THAUMATURGY_PATHS = {
    'Path of Blood', 'Lure of Flames', 'Movement of the Mind', 'Path of Conjuring', 'Path of Corruption', 'Path of Mars', 
    'Hands of Destruction', 'Neptune\'s Might', 'Path of Technomancy', 'Path of the Father\'s Vengeance', 'Green Path', 
    'Elemental Mastery', 'Weather Control', 'Gift of Morpheus', 'Oneiromancy', 'Path of Mercury', 'Spirit Manipulation', 
    'Two Centimes Path', 'Path of Transmutation', 'Path of Warding', 'Countermagic', 'Thaumaturgical Countermagic'
}

NECROMANCY_PATHS = {
    'Sepulchre Path', 'Bone Path', 'Ash Path', 'Cenotaph Path', 'Vitreous Path', 'Mortis Path', 'Grave\'s Decay', 'Path of Skulls', 'Corpse in the Monster', 'Twilight Garden'
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
    'combodiscipline': 'powers',
    'sphere': 'powers',
    'necromancy': 'powers',
    'arcanos': 'powers',
    'necromancy_ritual': 'powers'
}



# Attribute Categories
ATTRIBUTE_CATEGORIES = {
    'physical': ['Strength', 'Dexterity', 'Stamina'],
    'social': ['Charisma', 'Manipulation', 'Appearance'],
    'mental': ['Perception', 'Intelligence', 'Wits']
}
COMBAT_SPECIAL_ADVANTAGES = {
        'alacrity': {'valid_values': [2, 4, 6], 'desc': "Allows extra actions with Willpower expenditure"},
        'armor': {'valid_values': [1, 2, 3, 4, 5], 'desc': "Provides innate protection, each point adds one soak die"},
        'cause insanity': {'valid_values': [2, 4, 6, 8, 10], 'desc': "Can provoke temporary fits of madness"},
        'companion natural weaponry': {'valid_values': [3, 5, 7], 'desc': "Natural weaponry that inflicts lethal damage"},
        'deadly demise': {'valid_values': [2, 4, 6], 'desc': "Upon death, inflicts damage to nearby enemies"},
        'extra heads': {'valid_values': [2, 4, 6, 8], 'desc': "Additional heads with perception bonuses"},
        'extra limbs': {'valid_values': [2, 4, 6, 8], 'desc': "Additional prehensile limbs"},
        'flexible': {'valid_values': [1], 'desc': "Extremely flexible, -2 to athletics rolls to dodge or starting grapple"},
        'immunity': {'valid_values': [2, 5, 10, 15], 'desc': "Immunity to specific harmful effects"},
        'mystic shield': {'valid_values': [2, 4, 6, 8, 10], 'desc': "Resistance to magic"},
        'needleteeth': {'valid_values': [3], 'desc': "Sharp teeth bypass armor"},
        'quills': {'valid_values': [2, 4], 'desc': "Sharp defensive spines"},
        'razorskin': {'valid_values': [3], 'desc': "Skin that shreds on contact"},
        'rapid healing': {'valid_values': [2, 4, 6, 8], 'desc': "Accelerated recovery from injuries"},
        'regrowth': {'valid_values': [2, 4, 6], 'desc': "Regenerative capabilities"},
        'size': {'valid_values': [3, 5, 8, 10], 'desc': "Significantly larger or smaller than human norm"},
        'soak lethal damage': {'valid_values': [3], 'desc': "Natural ability to soak lethal damage"},
        'soak aggravated damage': {'valid_values': [5], 'desc': "Can soak aggravated damage"},
        'telekinesis': {'valid_values': [3, 5, 8, 12], 'desc': "Ability to move objects with the mind"},
        'venom': {'valid_values': [3, 6, 9, 12, 15], 'desc': "Poisonous attack capability"}
}
# Special Advantage Definitions
SPECIAL_ADVANTAGES = {
        'acute smell': {'valid_values': [2, 3], 'desc': "Adds dice to Perception rolls involving scent"},
        'aura': {'valid_values': [3], 'desc': "Opponents suffer +3 difficulty on rolls against you"},
        'aww': {'valid_values': [1, 2, 3, 4], 'desc': "Adds dice to Social rolls based on cuteness"},
        'bare necessities': {'valid_values': [1, 3], 'desc': "Retain items when shapeshifting"},
        'bioluminescence': {'valid_values': [1, 2, 3], 'desc': "Body can glow at will"},
        'blending': {'valid_values': [1], 'desc': "Can alter appearance to match surroundings"},
        'bond-sharing': {'valid_values': [4, 5, 6], 'desc': "Creates mystical bond to share abilities"},
        'chameleon coloration': {'valid_values': [4, 6, 8], 'desc': "Ability to change coloration for camouflage"},
        'dominance': {'valid_values': [1], 'desc': "Naturally commanding demeanor within specific groups"},
        'earthbond': {'valid_values': [2], 'desc': "Mystical connection to perceive threats"},
        'elemental touch': {'valid_values': [3, 5, 7, 10, 15], 'desc': "Control over a single element"},
        'empathic bond': {'valid_values': [2], 'desc': "Ability to sense and influence emotions"},
        'enhancement': {'valid_values': [5, 10, 15], 'desc': "Superior physical or mental attributes"},
        'feast of nettles': {'valid_values': [2, 3, 4, 5, 6], 'desc': "Ability to absorb and nullify Paradox"},
        'ferocity': {'valid_values': [2, 4, 6, 8, 10], 'desc': "Grants Rage points equal to half rating"},
        'ghost form': {'valid_values': [8, 10], 'desc': "Become invisible or incorporeal"},
        'healing lick': {'valid_values': [3, 6], 'desc': "Ability to heal wounds (3pts), 6pts for aggravated damage"},
        'hibernation': {'valid_values': [2], 'desc': "Can enter voluntary hibernation state"},
        'human guise': {'valid_values': [2, 4], 'desc': "Ability to appear human"},
        'human speech': {'valid_values': [1], 'desc': "Ability to speak human languages"},
        'information fount': {'valid_values': [5], 'desc': "Ability to provide bizarre, yet helpful information"},
        'intangibility': {'valid_values': [8, 10], 'desc': "Ability to disappear or become incorporeal"},
        'mesmerism': {'valid_values': [3, 6], 'desc': "Hypnotic gaze abilities"},
        'musical influence': {'valid_values': [6], 'desc': "Affect emotions through music"},
        'musk': {'valid_values': [3], 'desc': "Emit powerful stench affecting rolls"},
        'nightsight': {'valid_values': [3], 'desc': "Clear vision in low light conditions"},
        'omega status': {'valid_values': [4], 'desc': "Power in being overlooked"},
        'paradox nullification': {'valid_values': [2, 3, 4, 5, 6], 'desc': "Ability to consume Paradox energies"},
        'read and write': {'valid_values': [1], 'desc': "Ability to read and write human languages"},
        'shapechanger': {'valid_values': [3, 5, 8], 'desc': "Ability to assume different forms"},
        'shared knowledge': {'valid_values': [5, 7], 'desc': "Mystic bond allowing shared understanding"},
        'soul-sense': {'valid_values': [2, 3], 'desc': "Ability to sense spirits and impending death"},
        'speed': {'valid_values': [2, 4, 6, 8, 10], 'desc': "Increased movement speed"},
        'spirit travel': {'valid_values': [8, 10, 15], 'desc': "Ability to cross into Umbral realms"},
        'spirit vision': {'valid_values': [3], 'desc': "Ability to perceive the Penumbra"},
        'companion telepathy': {'valid_values': [2, 4, 6], 'desc': "Ability to communicate with others telepathically"},
        'tides of fortune': {'valid_values': [5], 'desc': "Ability to alter the flow of fate"},
        'tunneling': {'valid_values': [3], 'desc': "Can create tunnels through earth"},
        'unaging': {'valid_values': [5], 'desc': "Immunity to natural aging process"},
        'universal translator': {'valid_values': [5], 'desc': "Ability to understand languages"},
        'wall-crawling': {'valid_values': [4], 'desc': "Ability to climb sheer surfaces easily"},
        'water breathing': {'valid_values': [2, 5], 'desc': "Can breathe underwater"},
        'webbing': {'valid_values': [5], 'desc': "Can spin webs with various uses"},
        'companion wings': {'valid_values': [3, 5], 'desc': "Wings 3 grants Flight 2, Wings 5 grants Flight 4"}
    } 

VALID_DATES = {
    'vampire': ['date of birth', 'date of embrace'],
    'changeling': ['date of birth', 'date of chrysalis'],
    'mage': ['date of birth', 'date of awakening'],
    'shifter': ['date of birth', 'first change date'],
    'possessed': ['date of birth', 'date of possession'],
    'mortal+': ['date of birth'],
    'companion': ['date of birth'],
    'mortal': ['date of birth']
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
DATA_DIR = Path(__file__).parent.parent.parent.parent / 'data'

# Load all merit/flaw data
MERIT_FILES = [
    'changeling_merits.json',
    'fera_merits.json',
    'garou_merits.json',
    'mage_merits.json',
    'mortalplus_merits.json',
    'vampire_merits.json',
    'companion_merits.json'
]

FLAW_FILES = [
    'changeling_flaws.json',
    'fera_flaws.json',
    'garou_flaws.json',
    'mage_flaws.json',
    'mortalplus_flaws.json',
    'vampire_flaws.json',
    'companion_flaws.json'
]

# Rite files
RITE_FILES = [
    'garou_rites.json',
    'fera_bsd_rites.json'
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

# Load and combine all rite data
ALL_RITES = []
for file_name in RITE_FILES:
    file_path = DATA_DIR / file_name
    if file_path.exists():
        ALL_RITES.extend(load_json_data(file_path))

# Create validation mappings for rites
RITE_VALUES = {
    item['name']: item['values'] if isinstance(item['values'], list) else [item['values']]
    for item in ALL_RITES if 'name' in item and 'values' in item
}

RITE_SPLAT_RESTRICTIONS = {
    item['name']: {
        'splat': item.get('splat'),
        'splat_type': item.get('shifter_type')
    }
    for item in ALL_RITES if 'name' in item
}

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

def get_identity_stats(splat: str, subtype: str = None, affiliation: str = None) -> List[str]:
    """
    Get the list of identity stats for a given splat type and subtype.
    
    Args:
        splat (str): The splat type (Vampire, Shifter, Mage, etc.)
        subtype (str, optional): The character's subtype (e.g., Garou for Shifter, Traditions for Mage)
        affiliation (str, optional): Further specialization (e.g., specific Tradition or Tribe)
        
    Returns:
        List[str]: List of identity stat names in display order
    """
    # Base stats without Nature/Demeanor
    base_stats = ['Full Name', 'Concept', 'Date of Birth']
    
    # Add Nature/Demeanor for non-Changeling/Kinain characters
    if splat.lower() != 'changeling' and not (splat.lower() == 'mortal+' and subtype == 'Kinain'):
        base_stats.extend(['Nature', 'Demeanor'])
    
    # Splat-specific stats
    if splat.lower() == 'vampire':
        return base_stats + [
            'Date of Embrace',
            'Generation',
            'Clan',
            'Sire',
            'Sect',
            'Path of Enlightenment'  # Make sure this is included
        ]
    elif splat.lower() == 'shifter':
        stats = base_stats + [
            'First Change Date',
            'Type',
            'Breed',
            'Rank',
            'Deed Name'
        ]
        
        if subtype:
            subtype = subtype.lower()
            if subtype == 'garou':
                stats.extend(['Auspice', 'Tribe', 'Camp', 'Pack', 'Patron Totem'])
                # Add Fang House and Lodge for Silver Fang tribe
                if affiliation and affiliation.lower() == 'silver fang':
                    stats.extend(['Fang House', 'Lodge'])
                # Add Tribal Name for Black Spiral Dancers
                elif affiliation and affiliation.lower() == 'black spiral dancers':
                    stats.append('Tribal Name')
            elif subtype == 'bastet':
                stats.extend(['Tribe', 'Jamak Spirit', 'Pryio'])
            elif subtype == 'ajaba':
                stats.extend(['Aspect', 'Pack', 'Patron Totem'])
            elif subtype == 'ananasi':
                stats.extend(['Aspect', 'Ananasi Faction', 'Ananasi Cabal'])
            elif subtype == 'corax':
                stats.extend(['Pack', 'Patron Totem'])
            elif subtype == 'gurahl':
                stats.extend(['Auspice', 'Tribe', 'Pack', 'Patron Totem'])
            elif subtype == 'kitsune':
                stats.extend(['Kitsune Path', 'Kitsune Faction', 'Kitsune Clan', 'Go-En', 'Sempai'])
            elif subtype == 'mokole':
                stats.extend(['Auspice', 'Stream', 'Varna'])
            elif subtype == 'nagah':
                stats.extend(['Auspice', 'Crown'])
            elif subtype == 'ratkin':
                stats.extend(['Aspect', 'Plague'])
            elif subtype == 'rokea':
                stats.extend(['Auspice'])
        return stats
        
    elif splat.lower() == 'mage':
        stats = base_stats + [
            'Date of Awakening',
            'Affiliation',
            'Essence',
            'Signature',
            'Affinity Sphere'
        ]
        
        if affiliation:
            affiliation = affiliation.lower()
            if affiliation == 'traditions':
                stats.extend(['Tradition', 'Traditions Subfaction'])
            elif affiliation == 'technocracy':
                stats.extend(['Convention', 'Methodology'])
            elif affiliation == 'nephandi':
                stats.append('Nephandi Faction')
        
        return stats
        
    elif splat.lower() == 'changeling':
        stats = base_stats + [
            'Date of Chrysalis',
            'Kith',
            'Seeming',
            'Seelie Legacy',
            'Unseelie Legacy',
            'Court',
            'House',
            'Affinity Realm'
        ]
        
        if subtype:
            subtype = subtype.lower()
            if subtype == 'inanimae':
                stats.append('Phyla')
            elif subtype == 'nunnehi':
                stats.remove('House')
                stats.extend([
                    'Nunnehi Camp',
                    'Nunnehi Seeming',
                    'Nunnehi Family',
                    'Nunnehi Totem'
                ])
        return stats
        
    elif splat.lower() == 'possessed':
        return base_stats + [
            'Date of Possession',
            'Possessed Type',
            'Spirit Name',
            'Spirit Type'
        ]
        
    elif splat.lower() == 'mortal+':
        stats = base_stats + ['Type']  # Mortalplus Type
        
        if subtype:
            subtype = subtype.title()  # Use title case for comparison
            if subtype == 'Ghoul':
                stats.extend(['Domitor', 'Clan'])
            elif subtype == 'Kinfolk':
                stats.append('Tribe')
            elif subtype == 'Kinain':
                stats.extend(['House', 'Kith', 'First Legacy', 'Second Legacy', 'Affinity Realm'])
            elif subtype == 'Sorcerer':
                stats.append('Fellowship')
            elif subtype == 'Psychic':
                stats.append('Fellowship')
            elif subtype == 'Faithful':
                stats.append('Society')
        return stats
        
    elif splat.lower() == 'companion':
        return base_stats + [
            'Companion Type',
            'Fuel',
            'Affiliation', 
            'Motivation',
            'Elemental Affinity'
        ]
        
    else:  # Mortal or other
        return base_stats + ['Occupation']