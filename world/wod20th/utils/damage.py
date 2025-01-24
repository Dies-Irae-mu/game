from evennia.utils.ansi import ANSIString


def apply_damage_or_healing(character, change, damage_type):
    current_bashing = character.db.bashing or 0
    current_lethal = character.db.lethal or 0
    current_agg = character.db.agg or 0
    health_levels = character.get_stat('other', 'other', 'Health') or 7
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
    if char_type == "vampire":
        if agg_damage >= health_levels + 2:
            return "Final Death"
        elif agg_damage >= health_levels + 1:
            return "Torpor"
    else:
        if agg_damage >= health_levels + 1:
            return "Dead"
    
    if total_damage >= health_levels:
        return "Incapacitated"
    elif total_damage >= health_levels - 1:
        return "Crippled"
    elif total_damage >= health_levels - 2:
        return "Mauled"
    elif total_damage >= health_levels - 3:
        return "Wounded"
    elif total_damage >= health_levels - 4:
        return "Hurt"
    elif total_damage > 0:
        return "Bruised"
    return "Healthy"

def format_damage(character):
    health_levels = character.db.health_levels or 7
    agg = min(character.db.agg or 0, health_levels + 1)
    lethal = min(character.db.lethal or 0, health_levels - agg)
    bashing = min(character.db.bashing or 0, health_levels - agg - lethal)

    string = ""

    for i in range(agg):
        string += ANSIString("|h|r[*]|n")
    for i in range(lethal):
        string += ANSIString("|r[X]|n")
    for i in range(bashing):
        string += ANSIString("|y[/]|n")
    for i in range(health_levels - agg - lethal - bashing):
        string += ANSIString("|g[ ]|n")

    return string


def format_damage_stacked(character):
    # Fetch health levels from character stats or default to 7
    health_levels_count = character.get_stat('other', 'other', 'Health') or 7
    splat = character.get_stat('other', 'other', 'Splat')

    base_health_levels = [
        (ANSIString("Bruised"), ANSIString("|g[ ]|n"), ""),
        (ANSIString("Hurt"), ANSIString("|g[ ]|n"), " (-1)"),
        (ANSIString("Injured"), ANSIString("|g[ ]|n"), " (-1)"),
        (ANSIString("Wounded"), ANSIString("|g[ ]|n"), " (-2)"),
        (ANSIString("Mauled"), ANSIString("|g[ ]|n"), " (-2)"),
        (ANSIString("Crippled"), ANSIString("|g[ ]|n"), " (-5)"),
        (ANSIString("Incapacitated"), ANSIString("|g[ ]|n"), "")
    ]

    # Add the extra health boxes for vampires
    if splat == "Vampire":
        base_health_levels.append((ANSIString("Torpor"), ANSIString("|g[ ]|n"), ""))
        base_health_levels.append((ANSIString("Final Death"), ANSIString("|g[ ]|n"), ""))
    else:
        base_health_levels.append((ANSIString("Dead"), ANSIString("|g[ ]|n"), ""))

    # Adjust the health levels list based on the character's health levels
    extra_bruised_levels = [(ANSIString("Bruised"), ANSIString("|g[ ]|n"), "")] * (health_levels_count - 7)
    health_levels =  extra_bruised_levels + base_health_levels[:7]  + base_health_levels[7:]

    agg = character.db.agg or 0
    lethal = character.db.lethal or 0
    bashing = character.db.bashing or 0

    # Ensure agg does not exceed total health levels
    max_damage = len(health_levels)
    if agg > max_damage:
        agg = max_damage

    for i in range(agg):
        health_levels[i] = (health_levels[i][0], ANSIString("|h|r[*]|n"), health_levels[i][2])
    for i in range(agg, agg + lethal):
        health_levels[i] = (health_levels[i][0], ANSIString("|r[X]|n"), health_levels[i][2])
    for i in range(agg + lethal, agg + lethal + bashing):
        health_levels[i] = (health_levels[i][0], ANSIString("|y[/]|n"), health_levels[i][2])

    output = []
    for level, marker, penalty in health_levels:
        if marker not in [ANSIString("|g[ ]|n")]:
            level = ANSIString(f"|w{level}|n")
            penalty = ANSIString(f"|r{penalty}|n")
        # Add consistent spacing - pad level name to 15 characters
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