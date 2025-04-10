"""
Utility functions for handling Mage-specific character initialization and updates.
"""
from evennia.utils import logger
from world.wod20th.utils.stat_mappings import (
    MAGE_SPHERES, TRADITION_SUBFACTION, METHODOLOGIES,
    MAGE_BACKGROUNDS, TECHNOCRACY_BACKGROUNDS,
    TRADITIONS_BACKGROUNDS, NEPHANDI_BACKGROUNDS
)
from world.wod20th.utils.banality import get_default_banality
from typing import Dict, List, Set, Tuple, Optional

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

CONVENTION = {
    'Iteration X', 'New World Order', 'Progenitor', 'Syndicate', 'Void Engineer'
}

# Valid methodologies for each convention
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

NEPHANDI_FACTION = {
    'Herald of the Basilisk', 'Obliviate', 'Malfean', 'Baphie', 'Infernalist', 'Ironhand', 'Mammonite', "K'llashaa"
}

TRADITION_SPHERES = {
    'Correspondence', 'Entropy', 'Forces', 'Life',
    'Matter', 'Mind', 'Prime', 'Spirit', 'Time'
}

TECHNOCRACY_SPHERES = {
    'Data', 'Dimensional Science', 'Entropy', 'Forces',
    'Life', 'Matter', 'Mind', 'Primal Utility', 'Time'
}

SPHERE_MAPPINGS = {
    'Correspondence': 'Data',
    'Spirit': 'Dimensional Science',
    'Prime': 'Primal Utility'
}

# Valid mage traditions and their affinity spheres
TRADITION_AFFINITY_SPHERES = {
    'Akashic Brotherhood': ['Mind'],
    'Celestial Chorus': ['Prime'],
    'Cult of Ecstasy': ['Time'],
    'Dreamspeakers': ['Spirit'],
    'Euthanatos': ['Entropy'],
    'Order of Hermes': ['Forces'],
    'Sons of Ether': ['Matter'],
    'Verbena': ['Life'],
    'Virtual Adepts': ['Correspondence'],
    'Hollow Ones': [],  # No affinity sphere
}

# Convention affinity spheres
CONVENTION_AFFINITY_SPHERES = {
    'Iteration X': ['Matter'],
    'New World Order': ['Mind'],
    'Progenitors': ['Life'],
    'Syndicate': ['Entropy'],
    'Void Engineers': ['Correspondence'],
}

# Valid spheres
SPHERES = [
    'Correspondence',
    'Entropy',
    'Forces',
    'Life',
    'Matter',
    'Mind',
    'Prime',
    'Spirit',
    'Time',
    'Primal Utility',
    'Dimensional Science',
    'Data'
]

def initialize_mage_stats(character, affiliation, tradition=None, convention=None, nephandi_faction=None):
    """Initialize specific stats for a mage character."""
    # Initialize basic stats structure
    if 'identity' not in character.db.stats:
        character.db.stats['identity'] = {}
    if 'personal' not in character.db.stats['identity']:
        character.db.stats['identity']['personal'] = {}
    if 'lineage' not in character.db.stats['identity']:
        character.db.stats['identity']['lineage'] = {}
    
    # Set the affiliation
    character.set_stat('identity', 'lineage', 'Affiliation', affiliation, temp=False)
    character.set_stat('identity', 'lineage', 'Affiliation', affiliation, temp=True)
    
    # Initialize powers category if it doesn't exist
    if 'powers' not in character.db.stats:
        character.db.stats['powers'] = {}
    
    # Add Spheres category
    character.db.stats['powers']['sphere'] = {}
    
    # Initialize all spheres to 0
    for sphere in MAGE_SPHERES:
        if sphere not in character.db.stats['powers']['sphere']:
            character.db.stats['powers']['sphere'][sphere] = {'perm': 0, 'temp': 0}
    
    # Initialize secondary abilities structure
    if 'secondary_abilities' not in character.db.stats:
        character.db.stats['secondary_abilities'] = {}
    
    # Initialize secondary talents
    if 'secondary_talent' not in character.db.stats['secondary_abilities']:
        character.db.stats['secondary_abilities']['secondary_talent'] = {}
    for talent in ['Blatancy', 'Do', 'Flying', 'High Ritual']:
        character.db.stats['secondary_abilities']['secondary_talent'][talent] = {'perm': 0, 'temp': 0}
    
    # Initialize secondary skills
    if 'secondary_skill' not in character.db.stats['secondary_abilities']:
        character.db.stats['secondary_abilities']['secondary_skill'] = {}
    for skill in ['Microgravity Ops', 'Energy Weapons', 'Helmsman', 'Biotech']:
        character.db.stats['secondary_abilities']['secondary_skill'][skill] = {'perm': 0, 'temp': 0}
    
    # Initialize secondary knowledges
    if 'secondary_knowledge' not in character.db.stats['secondary_abilities']:
        character.db.stats['secondary_abilities']['secondary_knowledge'] = {}
    for knowledge in ['Hypertech', 'Cybernetics', 'Paraphysics', 'Xenobiology']:
        character.db.stats['secondary_abilities']['secondary_knowledge'][knowledge] = {'perm': 0, 'temp': 0}
    
    # Initialize identity stats
    identity_stats = {
        'personal': [
            'Full Name', 'Concept', 'Date of Birth', 'Date of Awakening',
            'Nature', 'Demeanor', 'Essence', 'Signature', 'Affinity Sphere'
        ],
        'lineage': [
            'Tradition', 'Convention', 'Methodology', 'Traditions Subfaction',
            'Nephandi Faction'
        ]
    }
    
    # Set default values for personal stats
    for stat in identity_stats['personal']:
        if stat not in character.db.stats['identity']['personal']:
            character.db.stats['identity']['personal'][stat] = {'perm': '', 'temp': ''}
    
    # Set default values for lineage stats
    for stat in identity_stats['lineage']:
        if stat not in character.db.stats['identity']['lineage']:
            character.db.stats['identity']['lineage'][stat] = {'perm': '', 'temp': ''}
    
    # Set default Banality based on affiliation and tradition/convention
    banality = get_default_banality('Mage', subtype=affiliation, 
                                  tradition=tradition, 
                                  convention=convention,
                                  nephandi_faction=nephandi_faction)
    if banality:
        character.set_stat('pools', 'dual', 'Banality', banality, temp=False)
        character.set_stat('pools', 'dual', 'Banality', banality, temp=True)
        display_type = tradition or convention or nephandi_faction or affiliation
        character.msg(f"|gBanality set to {banality}.")
    
    # Set base pools
    character.set_stat('pools', 'advantage', 'Arete', 1, temp=False)
    character.set_stat('pools', 'advantage', 'Arete', 1, temp=True)
    character.set_stat('pools', 'dual', 'Quintessence', 0, temp=False)
    character.set_stat('pools', 'dual', 'Quintessence', 0, temp=True)
    character.set_stat('pools', 'dual', 'Willpower', 5, temp=False)
    character.set_stat('pools', 'dual', 'Willpower', 5, temp=True)
    
    # Initialize Resonance at 0
    character.db.stats.setdefault('pools', {}).setdefault('resonance', {})
    character.db.stats['pools']['resonance']['Resonance'] = {'perm': 0, 'temp': 0}
    
    # Initialize Synergy virtues at 0
    character.db.stats.setdefault('virtues', {}).setdefault('synergy', {})
    for virtue in ['Dynamic', 'Entropic', 'Static']:
        character.db.stats['virtues']['synergy'][virtue] = {'perm': 0, 'temp': 0}
    
    # Initialize Paradox pool
    character.set_stat('pools', 'dual', 'Paradox', 0, temp=False)
    character.set_stat('pools', 'dual', 'Paradox', 0, temp=True)
    
    if affiliation.lower() == 'technocracy':
        character.set_stat('pools', 'advantage', 'Enlightenment', 1, temp=False)
        character.set_stat('pools', 'advantage', 'Enlightenment', 1, temp=True)
        character.del_stat('pools', 'advantage', 'Arete', temp=False)
        character.del_stat('pools', 'advantage', 'Arete', temp=True)
        
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
    if nephandi_faction in NEPHANDI_FACTION:
        character.db.stats.setdefault('identity', {}).setdefault('lineage', {})['Nephandi Faction'] = nephandi_faction

def get_tradition_subfactions(tradition: str) -> List[str]:
    """Get the subfactions for a specific tradition."""
    return TRADITION_SUBFACTION.get(tradition, [])

def get_convention_methodologies(convention: str) -> List[str]:
    """Get the methodologies for a specific convention."""
    return METHODOLOGIES.get(convention, [])

def get_available_spheres(affiliation: str) -> List[str]:
    """
    Get the list of available spheres based on affiliation.
    
    Args:
        affiliation (str): The mage's affiliation (Traditions/Technocracy/etc)
        
    Returns:
        List[str]: List of sphere names appropriate for that affiliation
    """
    if affiliation == 'Technocracy':
        return TECHNOCRACY_SPHERES
    return TRADITION_SPHERES

def get_sphere_name(sphere: str, affiliation: str) -> str:
    """
    Get the appropriate sphere name based on affiliation.
    
    Args:
        sphere (str): The base sphere name
        affiliation (str): The mage's affiliation
        
    Returns:
        str: The appropriate name for that sphere based on affiliation
    """
    if affiliation == 'Technocracy':
        return SPHERE_MAPPINGS.get(sphere, sphere)
    return sphere 

def validate_stat_value(self, stat_name: str, value: str, category: str = None, stat_type: str = None) -> tuple:
    """
    Validate a stat value based on its type and category.
    Returns (is_valid, error_message)
    """
    # Prevent certain abilities from being set as gifts
    if stat_type == 'gift' and stat_name.lower() in ['empathy', 'seduction']:
        return False, f"{stat_name} is an ability and cannot be set as a Gift"

    # Prevent Time from being set incorrectly based on splat
    if stat_name.lower() == 'time':
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
        char_type = self.caller.get_stat('identity', 'lineage', 'Mortal+ Type', temp=False)
        if splat == 'Mage':
            if stat_type == 'realm':
                return False, "For Mages, Time is a Sphere and cannot be set as a Realm"
        elif splat == 'Changeling' or (splat == 'Mortal+' and char_type == 'Kinain'):
            if stat_type == 'sphere':
                return False, "For Changelings and Kinain, Time is a Realm and cannot be set as a Sphere"

def update_mage_pools_on_stat_change(character, stat_name, new_value):
    """
    Update mage pools when a relevant stat changes.
    Called by CmdSelfStat after setting stats.
    """
    # Convert to lowercase for comparison
    stat_name = stat_name.lower()
    
    # Handle Avatar background changes
    if stat_name == 'avatar':
        try:
            # Convert new_value to int if it's a string
            avatar_value = int(new_value) if isinstance(new_value, str) else new_value
            # Set Quintessence pool to match Avatar value
            character.set_stat('pools', 'dual', 'Quintessence', avatar_value, temp=False)
            character.set_stat('pools', 'dual', 'Quintessence', avatar_value, temp=True)
            character.msg(f"|gQuintessence pool set to {avatar_value} based on Avatar background.|n")
        except (ValueError, TypeError):
            character.msg("|rError updating Quintessence pool - invalid Avatar value.|n")
            return

def validate_mage_stats(character, stat_name: str, value: str, category: str = None, stat_type: str = None) -> tuple[bool, str]:
    """
    Validate mage-specific stats.
    Returns (is_valid, error_message)
    """
    stat_name = stat_name.lower()
    
    # Get mage's affiliation
    affiliation = character.get_stat('identity', 'lineage', 'Affiliation', temp=False)
    
    # Validate affiliation
    if stat_name == 'affiliation':
        return validate_mage_affiliation(value)
        
    # Validate tradition
    if stat_name == 'tradition':
        return validate_mage_tradition(value)
        
    # Validate convention
    if stat_name == 'convention':
        return validate_mage_convention(value)
        
    # Validate methodology
    if stat_name == 'methodology':
        return validate_mage_methodology(character, value)
        
    # Validate tradition subfaction
    if stat_name == 'tradition subfaction':
        return validate_mage_subfaction(character, value)
        
    # Validate spheres
    if category == 'powers' and stat_type == 'sphere':
        # Get available spheres based on affiliation
        available_spheres = get_available_spheres(affiliation)
        # Map sphere name if needed
        sphere_name = get_sphere_name(stat_name, affiliation)
        # Case-insensitive comparison
        sphere_name_lower = sphere_name.lower()
        available_spheres_lower = {s.lower() for s in available_spheres}
        if sphere_name_lower in available_spheres_lower:
            # Find the correctly cased version
            sphere_name = next(s for s in available_spheres if s.lower() == sphere_name_lower)
            return validate_mage_sphere(character, sphere_name, value)
        return False, f"Invalid sphere. Valid spheres are: {', '.join(sorted(available_spheres))}"
        
    # Validate backgrounds
    if category == 'backgrounds' and stat_type == 'background':
        return validate_mage_backgrounds(character, stat_name, value)
    
    return True, ""

def validate_mage_affiliation(value: str) -> tuple[bool, str]:
    """Validate a mage's affiliation."""
    if value not in AFFILIATION:
        return False, f"Invalid affiliation. Valid affiliations are: {', '.join(sorted(AFFILIATION))}"
    return True, ""

def validate_mage_tradition(value: str) -> tuple[bool, str]:
    """Validate a mage's tradition."""
    if value not in TRADITION:
        return False, f"Invalid tradition. Valid traditions are: {', '.join(sorted(TRADITION))}"
    return True, ""

def validate_mage_convention(value: str) -> tuple[bool, str]:
    """Validate a mage's convention."""
    # Convert value to proper case for comparison
    value = value.title()
    # Handle special case for 'Progenitors'
    if value == 'Progenitors':
        value = 'Progenitor'
    if value not in CONVENTION:
        return False, f"Invalid convention. Valid conventions are: {', '.join(sorted(CONVENTION))}"
    return True, ""

def validate_mage_methodology(character, value: str) -> tuple[bool, str]:
    """Validate a mage's methodology."""
    # Get character's convention
    convention = character.get_stat('identity', 'lineage', 'Convention', temp=False)
    if not convention:
        return False, "Character must have a convention set to have a methodology"
    
    # Import both METHODOLOGIES dictionaries
    from world.wod20th.utils.stat_mappings import METHODOLOGIES as STAT_METHODOLOGIES
    
    # Create mapping dictionaries for both METHODOLOGIES sources
    local_convention_map = {
        'iteration x': 'ITERATION_X',
        'new world order': 'NEW_WORLD_ORDER',
        'progenitor': 'PROGENITORS',
        'progenitors': 'PROGENITORS',
        'syndicate': 'SYNDICATE',
        'void engineer': 'VOID_ENGINEER',
        'void engineers': 'VOID_ENGINEER'
    }
    
    imported_convention_map = {
        'iteration x': 'Iteration X',
        'new world order': 'New World Order',
        'progenitor': 'Progenitors',
        'progenitors': 'Progenitors',
        'syndicate': 'Syndicate',
        'void engineer': 'Void Engineers',
        'void engineers': 'Void Engineers'
    }
    
    # Get methodologies from both dictionaries and combine them
    all_methodologies = []
    
    # Local lookup
    local_key = local_convention_map.get(convention.lower(), convention.upper().replace(' ', '_'))
    local_methodologies = METHODOLOGIES.get(local_key, [])
    all_methodologies.extend(local_methodologies)
    
    # Imported lookup
    imported_key = imported_convention_map.get(convention.lower(), convention)
    imported_methodologies = STAT_METHODOLOGIES.get(imported_key, [])
    all_methodologies.extend(imported_methodologies)
    
    # If no methodologies found yet, try fuzzy matching
    if not all_methodologies:
        # Try local fuzzy match
        for key in METHODOLOGIES.keys():
            if key.lower().replace('_', ' ') == convention.lower().replace('s', '') or \
               key.lower().replace('_', ' ') + 's' == convention.lower():
                all_methodologies.extend(METHODOLOGIES[key])
                break
        
        # Try imported fuzzy match
        for key in STAT_METHODOLOGIES.keys():
            if key.lower() == convention.lower() or key.lower() == convention.lower() + 's' or \
               convention.lower() == key.lower() + 's':
                all_methodologies.extend(STAT_METHODOLOGIES[key])
                break
    
    # Remove duplicates while preserving order
    unique_methodologies = []
    for m in all_methodologies:
        if m not in unique_methodologies:
            unique_methodologies.append(m)
    
    if not unique_methodologies:
        return False, f"No methodologies found for {convention}. Please check spelling and try again."
    
    # Case-insensitive comparison for methodology value
    value_lower = value.lower()
    valid_methodologies_lower = [m.lower() for m in unique_methodologies]
    
    if value_lower not in valid_methodologies_lower:
        return False, f"Invalid methodology for {convention}. Valid methodologies are: {', '.join(sorted(unique_methodologies))}"
    
    # Find the correctly cased version of the methodology
    for methodology in unique_methodologies:
        if methodology.lower() == value_lower:
            # Return the properly cased version
            value = methodology
            break
            
    return True, value

def validate_mage_subfaction(character, value: str) -> tuple[bool, str]:
    """Validate a mage's tradition subfaction."""
    # Get character's tradition
    tradition = character.get_stat('identity', 'lineage', 'Tradition', temp=False)
    if not tradition:
        return False, "Character must have a tradition set to have a subfaction"
    
    valid_subfactions = TRADITION_SUBFACTION.get(tradition, [])
    if not valid_subfactions:
        return False, f"No subfactions found for {tradition}"
    
    if value not in valid_subfactions:
        return False, f"Invalid subfaction for {tradition}. Valid subfactions are: {', '.join(sorted(valid_subfactions))}"
    return True, ""

def validate_mage_sphere(character, sphere_name: str, value: str) -> tuple[bool, str]:
    """Validate a mage's sphere."""
    # Get character's affiliation for sphere name mapping
    affiliation = character.get_stat('identity', 'lineage', 'Affiliation', temp=False)
    
    # Get available spheres based on affiliation
    available_spheres = get_available_spheres(affiliation)
    
    # Map sphere name if needed
    sphere_name = get_sphere_name(sphere_name, affiliation)
    
    if sphere_name not in available_spheres:
        return False, f"Invalid sphere. Valid spheres are: {', '.join(sorted(available_spheres))}"
    
    # Validate value
    try:
        sphere_value = int(value)
        if sphere_value < 0 or sphere_value > 5:
            return False, "Sphere values must be between 0 and 5"
        return True, ""
    except ValueError:
        return False, "Sphere values must be numbers"

def validate_mage_backgrounds(character, background_name: str, value: str) -> tuple[bool, str]:
    """Validate mage backgrounds."""
    # Get character's affiliation
    affiliation = character.get_stat('identity', 'lineage', 'Affiliation', temp=False)
    
    # Get list of available backgrounds
    from world.wod20th.utils.stat_mappings import UNIVERSAL_BACKGROUNDS
    available_backgrounds = set(bg.title() for bg in UNIVERSAL_BACKGROUNDS + MAGE_BACKGROUNDS)
    
    # Add affiliation-specific backgrounds
    if affiliation == 'Technocracy':
        available_backgrounds.update(bg.title() for bg in TECHNOCRACY_BACKGROUNDS)
    elif affiliation == 'Traditions':
        available_backgrounds.update(bg.title() for bg in TRADITIONS_BACKGROUNDS)
    elif affiliation == 'Nephandi':
        available_backgrounds.update(bg.title() for bg in NEPHANDI_BACKGROUNDS)
    
    if background_name.title() not in available_backgrounds:
        return False, f"Invalid background '{background_name}'. Available backgrounds: {', '.join(sorted(available_backgrounds))}"
    
    # Validate value
    try:
        bg_value = int(value)
        if bg_value < 0 or bg_value > 5:
            return False, "Background values must be between 0 and 5"
        return True, ""
    except ValueError:
        return False, "Background values must be numbers"

def fix_misplaced_secondary_abilities(character):
    """Fix misplaced secondary abilities by moving them to their correct categories.
    
    Args:
        character: The character whose stats need to be fixed
        
    Returns:
        tuple: (bool, str) indicating if changes were made and a message describing what was done
    """
    if not hasattr(character, 'db') or not hasattr(character.db, 'stats'):
        return False, "Character has no stats"
        
    if 'secondary_abilities' not in character.db.stats:
        return False, "Character has no secondary abilities"
        
    changes_made = False
    messages = []
    
    # Define the correct categories for specific abilities
    CORRECT_CATEGORIES = {
        'Do': 'secondary_talent',
        'Blatancy': 'secondary_talent',
        'Flying': 'secondary_talent',
        'High Ritual': 'secondary_talent',
        'Microgravity Ops': 'secondary_skill',
        'Energy Weapons': 'secondary_skill',
        'Helmsman': 'secondary_skill',
        'Biotech': 'secondary_skill',
        'Hypertech': 'secondary_knowledge',
        'Cybernetics': 'secondary_knowledge',
        'Paraphysics': 'secondary_knowledge',
        'Xenobiology': 'secondary_knowledge'
    }
    
    # Check each category for misplaced abilities
    for current_category in ['secondary_talent', 'secondary_skill', 'secondary_knowledge']:
        if current_category not in character.db.stats['secondary_abilities']:
            continue
            
        # Check each ability in this category
        for ability_name, ability_value in list(character.db.stats['secondary_abilities'][current_category].items()):
            correct_category = CORRECT_CATEGORIES.get(ability_name)
            
            if correct_category and correct_category != current_category:
                # Initialize correct category if it doesn't exist
                if correct_category not in character.db.stats['secondary_abilities']:
                    character.db.stats['secondary_abilities'][correct_category] = {}
                    
                # Move the ability to its correct category
                character.db.stats['secondary_abilities'][correct_category][ability_name] = ability_value
                del character.db.stats['secondary_abilities'][current_category][ability_name]
                
                changes_made = True
                messages.append(f"Moved {ability_name} from {current_category} to {correct_category}")
                
                # Clean up empty categories
                if not character.db.stats['secondary_abilities'][current_category]:
                    del character.db.stats['secondary_abilities'][current_category]
    
    if changes_made:
        return True, "Fixed the following:\n" + "\n".join(messages)
    return False, "No misplaced secondary abilities found"

def is_affinity_sphere(character, sphere: str) -> bool:
    """
    Check if a sphere is an affinity sphere for the character.
    Only checks explicitly set affinity sphere.
    
    Args:
        character: The character object
        sphere: The sphere name to check
        
    Returns:
        bool: True if it's an affinity sphere, False otherwise
    """
    # Check explicitly set affinity sphere
    affinity_sphere = character.db.stats.get('identity', {}).get('lineage', {}).get('Affinity Sphere', {}).get('perm', '')
    if affinity_sphere and affinity_sphere.lower() == sphere.lower():
        logger.log_trace(f"Sphere {sphere} matches explicit affinity sphere {affinity_sphere}")
        return True
    
    return False

def validate_sphere_purchase(character, sphere: str, new_rating: int, is_staff_spend: bool = False) -> tuple[bool, str]:
    """
    Validate if a character can purchase a sphere increase.
    
    Args:
        character: The character object
        sphere: The sphere name
        new_rating: The desired new rating
        is_staff_spend: Whether this is a staff-approved purchase
        
    Returns:
        tuple[bool, str]: (can_purchase, error_message)
    """
    # Staff spends bypass validation
    if is_staff_spend:
        return True, None
    
    # Case-insensitive check for valid sphere
    valid_sphere = False
    proper_sphere_name = None
    
    for valid_sphere_name in SPHERES:
        if sphere.lower() == valid_sphere_name.lower():
            valid_sphere = True
            proper_sphere_name = valid_sphere_name
            break
    
    if not valid_sphere:
        return False, f"Invalid sphere. Valid spheres are: {', '.join(SPHERES)}"
    
    # Use proper case for the sphere name
    sphere = proper_sphere_name
    
    # Get character's affiliation
    affiliation = character.db.stats.get('identity', {}).get('lineage', {}).get('Affiliation', {}).get('perm', '')
    
    # Check the appropriate pool based on affiliation
    if affiliation == 'Technocracy':
        # Technocrats use Enlightenment
        enlightenment = character.db.stats.get('pools', {}).get('advantage', {}).get('Enlightenment', {}).get('perm', 0)
        
        # Check if new rating would exceed Enlightenment
        if new_rating > enlightenment:
            return False, f"Sphere rating cannot exceed Enlightenment rating ({enlightenment})"
    else:
        # Everyone else uses Arete
        arete = character.db.stats.get('pools', {}).get('advantage', {}).get('Arete', {}).get('perm', 0)
        
        # Check if new rating would exceed Arete
        if new_rating > arete:
            return False, f"Sphere rating cannot exceed Arete rating ({arete})"
    
    # Check if rating requires staff approval
    if new_rating > 1:
        return False, "Spheres above level 1 require staff approval. Please use +request to submit a request."
    
    return True, None

def calculate_sphere_cost(character, sphere: str, new_rating: int, current_rating: int = 0, is_staff_spend: bool = False) -> tuple[int, bool, str]:
    """
    Calculate the XP cost for increasing a sphere.
    
    Args:
        character: The character object
        sphere: The sphere name
        new_rating: The desired new rating
        current_rating: The current rating (default 0)
        is_staff_spend: Whether this is a staff-approved purchase
        
    Returns:
        tuple[int, bool, str]: (cost, requires_approval, error_message)
    """
    # Case-insensitive check for proper sphere name
    proper_sphere_name = None
    for valid_sphere_name in SPHERES:
        if sphere.lower() == valid_sphere_name.lower():
            proper_sphere_name = valid_sphere_name
            break
    
    # Use the properly cased sphere name if found
    if proper_sphere_name:
        sphere = proper_sphere_name
    
    # Get character's affiliation
    affiliation = character.db.stats.get('identity', {}).get('lineage', {}).get('Affiliation', {}).get('perm', '')
    
    # Check the appropriate pool based on affiliation
    if affiliation == 'Technocracy':
        # Technocrats use Enlightenment
        enlightenment = character.db.stats.get('pools', {}).get('advantage', {}).get('Enlightenment', {}).get('perm', 0)
        
        # Check if new rating would exceed Enlightenment
        if new_rating > enlightenment and not is_staff_spend:
            return 0, True, f"Sphere rating cannot exceed Enlightenment rating ({enlightenment})"
    else:
        # Everyone else uses Arete
        arete = character.db.stats.get('pools', {}).get('advantage', {}).get('Arete', {}).get('perm', 0)
        
        # Check if new rating would exceed Arete
        if new_rating > arete and not is_staff_spend:
            return 0, True, f"Sphere rating cannot exceed Arete rating ({arete})"
    
    # Check if it's an affinity sphere
    is_affinity = is_affinity_sphere(character, sphere)
    
    total_cost = 0
    requires_approval = False
    
    # Calculate cost for each dot
    for rating in range(current_rating + 1, new_rating + 1):
        if rating == 1:
            # First dot always costs 10
            total_cost += 10
        else:
            # Subsequent dots cost current rating * 7 for affinity, * 8 for non-affinity
            multiplier = 7 if is_affinity else 8
            total_cost += (rating - 1) * multiplier
    
    # Spheres above 1 require staff approval
    if new_rating > 1 and not is_staff_spend:
        requires_approval = True
    
    return total_cost, requires_approval, None 