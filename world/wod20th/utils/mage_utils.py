"""
Utility functions for handling Mage-specific character initialization and updates.
"""
from world.wod20th.models import Stat
from world.wod20th.utils.stat_mappings import (
    MAGE_SPHERES, TRADITION_SUBFACTION, METHODOLOGIES,
    MAGE_BACKGROUNDS, TECHNOCRACY_BACKGROUNDS,
    TRADITIONS_BACKGROUNDS, NEPHANDI_BACKGROUNDS
)
from world.wod20th.utils.banality import get_default_banality
from typing import Dict, List, Set

# Valid mage affiliations
AFFILIATION = {'Traditions', 'Technocracy', 'Nephandi'}

# Valid mage spheres
MAGE_SPHERES = {
    'Correspondence', 'Data', 'Dimensional Science', 'Entropy', 'Forces',
    'Life', 'Matter', 'Mind', 'Prime', 'Primal Utility', 'Spirit', 'Time'
}

# Valid traditions
TRADITION = {
    'Cultists of Ecstasy', 'Euthanatos', 'Celestial Chorus', 'Akashic Brotherhood',
    'Dreamspeakers', 'Virtual Adepts', 'Order of Hermes', 'Verbena',
    'Sons of Ether'
}

# Tradition subfactions
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

# Valid conventions
CONVENTION = {
    'Iteration X', 'New World Order', 'Progenitor', 'Syndicate', 'Void Engineer'
}

# Convention methodologies
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

# Nephandi factions
NEPHANDI_FACTION = {
    'Herald of the Basilisk', 'Obliviate', 'Malfean', 'Baphie', 
    'Infernalist', 'Ironhand', 'Mammonite', "K'llashaa"
}

def initialize_mage_stats(character, affiliation, tradition=None, convention=None, nephandi_faction=None):
    """Initialize specific stats for a mage character."""
    # Initialize basic stats structure
    if 'identity' not in character.db.stats:
        character.db.stats['identity'] = {}
    if 'lineage' not in character.db.stats['identity']:
        character.db.stats['identity']['lineage'] = {}
    
    # Initialize powers category if it doesn't exist
    if 'powers' not in character.db.stats:
        character.db.stats['powers'] = {}
    
    # Add Spheres category
    character.db.stats['powers']['sphere'] = {}
    
    # Initialize all spheres to 0
    for sphere in MAGE_SPHERES:
        if sphere not in character.db.stats['powers']['sphere']:
            character.db.stats['powers']['sphere'][sphere] = {'perm': 0, 'temp': 0}
    
    # Set default Banality based on affiliation
    banality = get_default_banality('Mage', subtype=affiliation)
    character.set_stat('pools', 'dual', 'Banality', banality, temp=False)
    character.set_stat('pools', 'dual', 'Banality', banality, temp=True)
    
    # Set base pools
    character.set_stat('pools', 'advantage', 'Arete', 1, temp=False)
    character.set_stat('pools', 'advantage', 'Arete', 1, temp=True)
    character.set_stat('pools', 'dual', 'Quintessence', 1, temp=False)
    character.set_stat('pools', 'dual', 'Quintessence', 1, temp=True)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 3, temp=True)
    
    # Initialize Resonance
    character.db.stats.setdefault('pools', {}).setdefault('resonance', {})
    if 'Resonance' not in character.db.stats['pools']['resonance']:
        character.db.stats['pools']['resonance']['Resonance'] = {'perm': 0, 'temp': 0}
    
    # Initialize Synergy virtues
    character.db.stats.setdefault('virtues', {}).setdefault('synergy', {})
    for virtue in ['Dynamic', 'Entropic', 'Static']:
        if virtue not in character.db.stats['virtues']['synergy']:
            character.db.stats['virtues']['synergy'][virtue] = {'perm': 0, 'temp': 0}
    
    # Initialize Paradox pool
    character.set_stat('pools', 'dual', 'Paradox', 0, temp=False)
    character.set_stat('pools', 'dual', 'Paradox', 0, temp=True)
    
    # Set affiliation-specific stats
    if affiliation.lower() == 'traditions' and tradition:
        initialize_tradition_stats(character, tradition)
    elif affiliation.lower() == 'technocracy' and convention:
        initialize_convention_stats(character, convention)
    elif affiliation.lower() == 'nephandi' and nephandi_faction:
        initialize_nephandi_stats(character, nephandi_faction)

def initialize_tradition_stats(character, tradition):
    """Initialize Tradition-specific stats."""
    # Set subfaction options if available
    if tradition in TRADITION_SUBFACTION:
        subfactions = TRADITION_SUBFACTION[tradition]
        character.db.stats.setdefault('identity', {}).setdefault('lineage', {})['Traditions Subfaction'] = ''

def initialize_convention_stats(character, convention):
    """Initialize Convention-specific stats."""
    # Set methodology options if available
    if convention in METHODOLOGIES:
        methodologies = METHODOLOGIES[convention]
        character.db.stats.setdefault('identity', {}).setdefault('lineage', {})['Methodology'] = ''

def initialize_nephandi_stats(character, nephandi_faction):
    """Initialize Nephandi-specific stats."""
    # Additional Nephandi-specific initialization can be added here
    pass 

def get_tradition_subfactions(tradition: str) -> List[str]:
    """Get the subfactions for a specific tradition."""
    return TRADITION_SUBFACTION.get(tradition, [])

def get_convention_methodologies(convention: str) -> List[str]:
    """Get the methodologies for a specific convention."""
    return METHODOLOGIES.get(convention, []) 