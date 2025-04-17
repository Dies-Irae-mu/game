from evennia.utils.ansi import ANSIString
import time


def calculate_total_health_levels(character):
    """Calculate total health levels including all bonuses.
    
    The following bonuses are applied:
    - Huge Size: 1 additional Bruised level
    - Troll kith: 1 additional Bruised level
    - Glome phyla: 2 additional Bruised levels
    - Ratkin Warrior auspice: 1 additional Bruised level
    - Gurahl Rage boost: X additional levels at specific positions (based on Rage spent)

    """
    # Basic health level counts
    bonus_bruised = 0
    
    # Check for Huge Size merit - check both locations
    huge_size = character.get_stat('merits', 'physical', 'Huge Size', temp=False)
    if not huge_size:  # Check alternate location
        huge_size = character.get_stat('merits', 'merit', 'Huge Size', temp=False)
    
    if huge_size:
        # Huge Size always grants 1 additional Bruised level regardless of rating
        bonus_bruised += 1
    
    # Check for Troll kith
    kith = character.get_stat('identity', 'lineage', 'Kith')
    if kith and kith.lower() == 'troll':
        bonus_bruised += 1
        
    # Check for Glome phyla
    phyla = character.get_stat('identity', 'lineage', 'Phyla')
    if phyla and phyla.lower() == 'glome':
        bonus_bruised += 2

    # Check for Warrior auspice
    auspice = character.get_stat('identity', 'lineage', 'Auspice')
    if auspice and auspice.lower() == 'warrior':
        bonus_bruised += 1
    
    # Initialize health level bonuses if it doesn't exist or is None
    if not hasattr(character.db, 'health_level_bonuses') or character.db.health_level_bonuses is None:
        character.db.health_level_bonuses = {
            'bruised': bonus_bruised,
            'hurt': 0,
            'injured': 0,
            'wounded': 0,
            'mauled': 0,
            'crippled': 0
        }
    else:
        # Update the base bruised level bonuses (from merits, etc.)
        character.db.health_level_bonuses['bruised'] = bonus_bruised
        
    # Add bonus health from Gurahl Rage expenditure
    if hasattr(character.db, 'bonus_health_from_rage') and character.db.bonus_health_from_rage:
        # Check if the health boost is stale (older than 8 hours)
        current_time = time.time()
        health_boost_time = getattr(character.db, 'health_boost_timestamp', None)
        
        # If there's no timestamp or it's older than 8 hours (28800 seconds), clear the boost
        if health_boost_time is None or (current_time - health_boost_time > 28800):
            # Clear stale health boost
            character.db.bonus_health_from_rage = 0
            character.db.rage_health_level_type = None
            
            # Also remove from attribute_boosts if it exists there
            if hasattr(character.db, 'attribute_boosts') and character.db.attribute_boosts:
                for stat_name, boost_info in list(character.db.attribute_boosts.items()):
                    if boost_info.get('is_health_boost', False):
                        del character.db.attribute_boosts[stat_name]
                        break
            
            # Log the automatic cleanup
            character.msg("|yYour Rage health boost has expired.|n")
        else:
            # Not stale, apply the boost normally
            rage_bonus = character.db.bonus_health_from_rage
            # Get the level type with a proper null check
            rage_level_type = None
            if hasattr(character.db, 'rage_health_level_type'):
                rage_level_type = character.db.rage_health_level_type
                if rage_level_type is not None:
                    rage_level_type = rage_level_type.lower()
            
            # Default to 'bruised' if not set or None
            if not rage_level_type:
                rage_level_type = 'bruised'
            
            # Add the rage bonus to the appropriate level type
            if rage_level_type in character.db.health_level_bonuses:
                character.db.health_level_bonuses[rage_level_type] += rage_bonus
    
    # Calculate total bonus health
    total_bonus = sum(character.db.health_level_bonuses.values())
    
    # Store total bonus health for use in other functions
    character.db.bonus_health = total_bonus
        
    return total_bonus

def apply_damage_or_healing(character, change, damage_type):
    """Apply damage or healing to a character.
    
    Args:
        character: The character object
        change: Positive for damage, negative for healing
        damage_type: "bashing", "lethal", or "aggravated"
        
    Returns:
        The new injury level
    """
    current_bashing = character.db.bashing or 0
    current_lethal = character.db.lethal or 0
    current_agg = character.db.agg or 0
    base_health = character.get_stat('other', 'other', 'Health') or 7
    
    # Calculate bonus health levels
    bonus_health = calculate_total_health_levels(character)
    
    # Add bonus health to base health
    health_levels = base_health + bonus_health
    
    char_type = character.db.char_type or "mortal"
    injury_level = character.db.injury_level or "Healthy"

    new_bashing = current_bashing
    new_lethal = current_lethal
    new_agg = current_agg

    if change > 0 and (injury_level != "Dead" or damage_type == "aggravated"):
        for _ in range(change):
            if damage_type == "bashing":
                if new_bashing + new_lethal + new_agg < health_levels:
                    new_bashing += 1
                elif new_bashing > 0:
                    new_lethal += 1
                    new_bashing -= 1
                elif new_lethal > 0:
                    new_agg += 1
                    new_lethal -= 1
                else:
                    new_agg += 1
            elif damage_type == "lethal":
                if new_bashing + new_lethal + new_agg < health_levels:
                    new_lethal += 1
                else:
                    new_agg += 1
                    if new_bashing > 0:
                        new_bashing -= 1
                    elif new_lethal > 0:
                        new_lethal -= 1
            elif damage_type == "aggravated":
                new_agg += 1
                if new_bashing > 0:
                    new_bashing -= 1
                elif new_lethal > 0:
                    new_lethal -= 1

            if new_agg >= health_levels + 1:
                new_agg = health_levels + 1
                break
    elif change < 0:  # Healing
        heal_amount = abs(change)
        if damage_type == "bashing":
            new_bashing = max(new_bashing - heal_amount, 0)
        elif damage_type == "lethal":
            if heal_amount > new_lethal:
                excess = heal_amount - new_lethal
                new_lethal = 0
                new_bashing = max(new_bashing - excess, 0)
            else:
                new_lethal -= heal_amount
        elif damage_type == "aggravated":
            if heal_amount > new_agg:
                excess = heal_amount - new_agg
                new_agg = 0
                if excess > new_lethal:
                    lethal_heal = excess - new_lethal
                    new_lethal = 0
                    new_bashing = max(new_bashing - lethal_heal, 0)
                else:
                    new_lethal -= excess
            else:
                new_agg -= heal_amount

    total_damage = new_bashing + new_lethal + new_agg
    new_injury_level = calculate_injury_level(total_damage, health_levels, new_agg, char_type)

    # Update character attributes
    character.db.bashing = new_bashing
    character.db.lethal = new_lethal
    character.db.agg = new_agg
    character.db.injury_level = new_injury_level

    return new_injury_level

def calculate_injury_level(total_damage, health_levels, agg_damage, char_type):
    """Calculate injury level based on damage and health levels."""
    if char_type == "vampire":
        if agg_damage >= health_levels + 2:
            return "Final Death"
        elif agg_damage >= health_levels + 1:
            return "Torpor"
    else:
        if agg_damage >= health_levels + 1:
            return "Dead"
            
    # Defines the injury levels and thresholds based on a standard character
    # This needs to account for the variable number of each health level type
    # For now, we'll use a simpler approach based on total damage vs. health levels remaining (so when crippled, you have 1 health level remaining for instance)
    if total_damage >= health_levels:
        return "Incapacitated"
    elif total_damage >= health_levels - 1:
        return "Crippled"
    elif total_damage >= health_levels - 2:
        return "Mauled"
    elif total_damage >= health_levels - 3:
        return "Wounded"
    elif total_damage >= health_levels - 4:
        return "Injured"
    elif total_damage >= health_levels - 5:
        return "Hurt"
    elif total_damage > 0:
        return "Bruised"
    return "Healthy"

def format_damage(character):
    """Format damage markers for display."""
    # Get base health levels
    base_health = 7
    
    # Calculate bonus health levels
    bonus_health = calculate_total_health_levels(character)
    total_health = base_health + bonus_health

    # Get current damage levels
    agg = min(character.db.agg or 0, total_health + 1)
    lethal = min(character.db.lethal or 0, total_health - agg)
    bashing = min(character.db.bashing or 0, total_health - agg - lethal)

    string = ""

    # Add damage markers
    for i in range(agg):
        string += ANSIString("|h|r[*]|n")
    for i in range(lethal):
        string += ANSIString("|r[X]|n")
    for i in range(bashing):
        string += ANSIString("|y[/]|n")
    for i in range(total_health - agg - lethal - bashing):
        string += ANSIString("|g[ ]|n")

    return string


def format_damage_stacked(character):
    """Format character's health levels with damage markers."""
    # Define standard health levels - one of each by default
    health_levels = [
        (ANSIString("Bruised"), ANSIString("|g[ ]|n"), ""),
        (ANSIString("Hurt"), ANSIString("|g[ ]|n"), " (-1)"),
        (ANSIString("Injured"), ANSIString("|g[ ]|n"), " (-1)"),
        (ANSIString("Wounded"), ANSIString("|g[ ]|n"), " (-2)"),
        (ANSIString("Mauled"), ANSIString("|g[ ]|n"), " (-2)"),
        (ANSIString("Crippled"), ANSIString("|g[ ]|n"), " (-5)"),
        (ANSIString("Incapacitated"), ANSIString("|g[ ]|n"), "")
    ]
    
    # Ensure health_level_bonuses exists and is properly initialized
    if not hasattr(character.db, 'health_level_bonuses') or character.db.health_level_bonuses is None:
        calculate_total_health_levels(character)
    
    # Create the full health levels list with bonuses
    full_health_levels = []
    
    # Add the standard Bruised level plus any bonus Bruised levels
    bruised_count = 1 + character.db.health_level_bonuses.get('bruised', 0)
    for _ in range(bruised_count):
        full_health_levels.append((ANSIString("Bruised"), ANSIString("|g[ ]|n"), ""))
    
    # Add Hurt level plus any bonus Hurt levels
    hurt_count = 1 + character.db.health_level_bonuses.get('hurt', 0)
    for _ in range(hurt_count):
        full_health_levels.append((ANSIString("Hurt"), ANSIString("|g[ ]|n"), " (-1)"))
    
    # Add Injured level plus any bonus Injured levels
    injured_count = 1 + character.db.health_level_bonuses.get('injured', 0)
    for _ in range(injured_count):
        full_health_levels.append((ANSIString("Injured"), ANSIString("|g[ ]|n"), " (-1)"))
    
    # Add Wounded level plus any bonus Wounded levels
    wounded_count = 1 + character.db.health_level_bonuses.get('wounded', 0)
    for _ in range(wounded_count):
        full_health_levels.append((ANSIString("Wounded"), ANSIString("|g[ ]|n"), " (-2)"))
    
    # Add Mauled level plus any bonus Mauled levels
    mauled_count = 1 + character.db.health_level_bonuses.get('mauled', 0)
    for _ in range(mauled_count):
        full_health_levels.append((ANSIString("Mauled"), ANSIString("|g[ ]|n"), " (-2)"))
    
    # Add Crippled level plus any bonus Crippled levels
    crippled_count = 1 + character.db.health_level_bonuses.get('crippled', 0)
    for _ in range(crippled_count):
        full_health_levels.append((ANSIString("Crippled"), ANSIString("|g[ ]|n"), " (-5)"))
    
    # Add the Incapacitated level
    full_health_levels.append((ANSIString("Incapacitated"), ANSIString("|g[ ]|n"), ""))
    
    # Add the appropriate final health level
    splat = character.get_stat('other', 'splat', 'Splat')
    if splat == "Vampire":
        full_health_levels.extend([
            (ANSIString("Torpor"), ANSIString("|g[ ]|n"), ""),
            (ANSIString("Final Death"), ANSIString("|g[ ]|n"), "")
        ])
    else:
        full_health_levels.append((ANSIString("Dead"), ANSIString("|g[ ]|n"), ""))

    # Apply damage markers
    agg = character.db.agg or 0
    lethal = character.db.lethal or 0
    bashing = character.db.bashing or 0

    # Ensure agg does not exceed total health levels
    max_damage = len(full_health_levels)
    if agg > max_damage:
        agg = max_damage

    for i in range(agg):
        full_health_levels[i] = (full_health_levels[i][0], ANSIString("|h|r[*]|n"), full_health_levels[i][2])
    for i in range(agg, agg + lethal):
        if i < len(full_health_levels):
            full_health_levels[i] = (full_health_levels[i][0], ANSIString("|r[X]|n"), full_health_levels[i][2])
    for i in range(agg + lethal, agg + lethal + bashing):
        if i < len(full_health_levels):
            full_health_levels[i] = (full_health_levels[i][0], ANSIString("|y[/]|n"), full_health_levels[i][2])

    output = []
    for level, marker, penalty in full_health_levels:
        if marker not in [ANSIString("|g[ ]|n")]:
            level = ANSIString(f"|w{level}|n")
            penalty = ANSIString(f"|r{penalty}|n")
        output.append(f"{level:<15}{marker} {penalty}")

    return output



def format_status(character):
    injury_level = character.db.injury_level or "Healthy"

    status_mapping = {
        "Bruised": ("|y", ""),
        "Hurt": ("|y", " (-1)"),
        "Injured": ("|y", " (-1)"),
        "Wounded": ("|r", " (-2)"),
        "Mauled": ("|r", " (-2)"),
        "Crippled": ("|r", " (-5)"),
        "Incapacitated": ("|h|r", ""),
        "Torpor": ("|h|r", ""),
        "Final Death": ("|h|r", "")
    }

    if injury_level == "Dead" and character.get_stat('other', 'other', 'Splat') == 'Vampire':
        injury_level = "Torpor"

    color, suffix = status_mapping.get(injury_level, ("|h|g", ""))
    injury_level = ANSIString(f"{color}{injury_level}{suffix}|n")

    return injury_level