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
    'affinity sphere': ('identity', 'lineage')
}

# Special stats that need custom handling
SPECIAL_STATS = [
    'splat', 'type', 'nature', 'demeanor', 'enlightenment', 'generation',
    'kith', 'phyla', 'breed', 'auspice', 'aspect', 'path', 'tribe'
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