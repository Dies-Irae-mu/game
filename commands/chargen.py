# commands/chargen.py

from evennia import Command
from evennia.utils.evmenu import EvMenu
from world.wod20th.models import Stat, SHIFTER_IDENTITY_STATS, SHIFTER_RENOWN, SHIFTER_RENOWN, CLAN, MAGE_FACTION, MAGE_SPHERES, TRADITION, TRADITION_SUBFACTION, CONVENTION, METHODOLOGIES, NEPHANDI_FACTION, SEEMING, KITH, SEELIE_LEGACIES, UNSEELIE_LEGACIES, ARTS, REALMS, calculate_willpower, calculate_road, MORTALPLUS_TYPES
from typeclasses.characters import Character
from evennia.commands.default.muxcommand import MuxCommand
from world.jobs.models import Job, Queue
from django.utils import timezone
"""
class CmdCharGen(Command):
    
    Start the character generation process.

    Usage:
      chargen
    

    key = "chargen"
    locks = "cmd:all()"
    help_category = "Character Generation"

    def func(self):
        # Initialize chargen data if it doesn't exist
        if not self.caller.db.chargen:
            self.caller.db.chargen = {}
        
        EvMenu(self.caller, "commands.chargen", startnode="node_start", cmd_on_exit=self.finish_chargen)

    def finish_chargen(self, caller, menu):
        
        Called when character generation is complete.
        
        try:
            _apply_chargen_data(caller)
            caller.msg("Character generation complete! Your character has been created and is ready to play.")
        except Exception as e:
            caller.msg(f"An error occurred during character generation: {str(e)}")
            caller.msg("Please contact an admin for assistance.")

    def at_post_cmd(self):
        
        This hook is called after the command has finished executing 
        (after self.func()).
        
        if hasattr(self.caller, "ndb._menutree"):
            self.caller.msg("|wUse 'look' to see the character creation menu again.")
            self.caller.msg("Use 'quit' to exit character creation.")

def _apply_chargen_data(caller):
    chargen_data = caller.db.chargen
    
    if not chargen_data:
        caller.msg("Error: No character generation data found.")
        return

    # Initialize stats if it doesn't exist
    if not caller.db.stats:
        caller.db.stats = {}

    # Apply splat
    splat = chargen_data.get('splat', '')
    caller.db.stats['other'] = {'splat': {'Splat': {'perm': splat}}}

    # Apply basic information
    caller.db.concept = chargen_data.get('concept', '')
    caller.db.nature = chargen_data.get('nature', '')
    caller.db.demeanor = chargen_data.get('demeanor', '')
    caller.db.clan = chargen_data.get('clan', '')

    # Apply attributes
    for category, attributes in chargen_data.get('attributes', {}).items():
        for attr, value in attributes.items():
            caller.set_stat(category, 'attribute', attr, value)

    # Apply abilities
    for category, abilities in chargen_data.get('abilities', {}).items():
        for ability, value in abilities.items():
            caller.set_stat(category, 'ability', ability, value)

    # Apply disciplines or other splat-specific powers
    splat = caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
    if splat.lower() == 'vampire':
        for discipline, value in chargen_data.get('disciplines', {}).items():
            caller.set_stat('powers', 'discipline', discipline, value)
    elif splat.lower() == 'mage':
        for sphere, value in chargen_data.get('spheres', {}).items():
            caller.set_stat('powers', 'sphere', sphere, value)
    elif splat.lower() == 'changeling':
        for art, value in chargen_data.get('arts', {}).items():
            caller.set_stat('powers', 'art', art, value)
        for realm, value in chargen_data.get('realms', {}).items():
            caller.set_stat('powers', 'realm', realm, value)
    elif splat.lower() == 'shifter':
        for gift, value in chargen_data.get('gifts', {}).items():
            caller.set_stat('powers', 'gift', gift, value)

    # Apply backgrounds
    for background, value in chargen_data.get('backgrounds', {}).items():
        caller.set_stat('backgrounds', 'background', background, value)

    # Apply virtues
    for virtue, value in chargen_data.get('virtues', {}).items():
        caller.set_stat('virtues', 'moral', virtue, value)

    # Apply splat-specific stats
    if splat.lower() == 'vampire':
        caller.set_stat('pools', 'dual', 'Blood', 10, temp=False)
        caller.set_stat('pools', 'dual', 'Blood', 10, temp=True)
    elif splat.lower() == 'shifter':
        caller.set_stat('pools', 'dual', 'Gnosis', 1, temp=False)
        caller.set_stat('pools', 'dual', 'Gnosis', 1, temp=True)
        caller.set_stat('pools', 'dual', 'Rage', 1, temp=False)
        caller.set_stat('pools', 'dual', 'Rage', 1, temp=True)
    elif splat.lower() == 'mage':
        caller.set_stat('pools', 'dual', 'Quintessence', 1, temp=False)
        caller.set_stat('pools', 'dual', 'Quintessence', 1, temp=True)
        caller.set_stat('pools', 'dual', 'Paradox', 0, temp=False)
        caller.set_stat('pools', 'dual', 'Paradox', 0, temp=True)
        caller.set_stat('other', 'advantage', 'Arete', 1, temp=False)
    elif splat.lower() == 'changeling':
        caller.set_stat('pools', 'dual', 'Glamour', 1, temp=False)
        caller.set_stat('pools', 'dual', 'Glamour', 1, temp=True)
        caller.set_stat('pools', 'dual', 'Banality', 5, temp=False)
        caller.set_stat('pools', 'dual', 'Banality', 5, temp=True)

    # Calculate and set Willpower
    new_willpower = calculate_willpower(caller)
    caller.set_stat('pools', 'dual', 'Willpower', new_willpower, temp=False)
    caller.set_stat('pools', 'dual', 'Willpower', new_willpower, temp=True)

    # Calculate and set Road (for Vampires)
    if splat.lower() == 'vampire':
        new_road = calculate_road(caller)
        caller.set_stat('pools', 'moral', 'Road', new_road, temp=False)

    # Clear chargen data
    caller.attributes.remove('chargen')

    caller.msg("Your character has been fully created and is ready to play!")

# Menu nodes

def node_start(caller):
    text = "Welcome to character generation! Let's create your World of Darkness character."
    options = (
        {"key": "1", "desc": "Choose your character concept", "goto": "node_concept"},
        {"key": "2", "desc": "Select your character's nature and demeanor", "goto": "node_nature_demeanor"},
        {"key": "3", "desc": "Choose your character's splat", "goto": "node_splat"},
        {"key": "4", "desc": "Assign Attributes", "goto": "node_attributes"},
        {"key": "5", "desc": "Assign Abilities", "goto": "node_abilities"},
        {"key": "6", "desc": "Choose Powers", "goto": "node_powers"},
        {"key": "7", "desc": "Select Backgrounds", "goto": "node_backgrounds"},
        {"key": "8", "desc": "Assign Virtues", "goto": "node_virtues"},
        {"key": "9", "desc": "Review and Finish", "goto": "node_review"},
    )
    return text, options

def node_concept(caller):
    if "concept" not in caller.db.chargen:
        caller.db.chargen["concept"] = ""
    
    text = "What is your character concept? This is a brief description of who your character is."
    options = (
        {"key": "_default", "goto": _set_concept},
    )
    return text, options

def _set_concept(caller, raw_string):
    concept = raw_string.strip()
    caller.db.chargen["concept"] = concept
    caller.msg(f"Character concept set to: {concept}")
    return "node_start"

def node_nature_demeanor(caller):
    text = "Choose your character's Nature and Demeanor. Nature is your character's true self, while Demeanor is the face they show to the world."
    options = (
        {"key": "1", "desc": "Set Nature", "goto": "set_nature"},
        {"key": "2", "desc": "Set Demeanor", "goto": "set_demeanor"},
        {"key": "3", "desc": "Return to main menu", "goto": "node_start"},
    )
    return text, options

def set_nature(caller):
    if "nature" not in caller.db.chargen:
        caller.db.chargen["nature"] = ""
    
    text = "What is your character's Nature?"
    options = (
        {"key": "_default", "goto": _set_nature},
    )
    return text, options

def _set_nature(caller, raw_string):
    nature = raw_string.strip()
    caller.db.chargen["nature"] = nature
    caller.msg(f"Nature set to: {nature}")
    return "node_nature_demeanor"

def set_demeanor(caller):
    if "demeanor" not in caller.db.chargen:
        caller.db.chargen["demeanor"] = ""
    
    text = "What is your character's Demeanor?"
    options = (
        {"key": "_default", "goto": _set_demeanor},
    )
    return text, options

def _set_demeanor(caller, raw_string):
    demeanor = raw_string.strip()
    caller.db.chargen["demeanor"] = demeanor
    caller.msg(f"Demeanor set to: {demeanor}")
    return "node_nature_demeanor"

def node_splat(caller):
    text = "Choose your character type:"
    options = [
        {"key": "1", "desc": "Vampire", "goto": "node_vampire_clan"},
        {"key": "2", "desc": "Shifter", "goto": "node_shifter_type"},
        {"key": "3", "desc": "Mage", "goto": "node_mage_faction"},
        {"key": "4", "desc": "Changeling", "goto": "node_changeling_kith"},
        {"key": "0", "desc": "Return to main menu", "goto": "node_start"}
    ]
    return text, options

def _set_splat(caller, raw_string, **kwargs):
    splat = kwargs.get("splat")
    caller.db.chargen["splat"] = splat
    caller.msg(f"Splat set to: {splat}")
    
    # Set up splat-specific chargen data
    if splat == "Vampire":
        return "node_vampire_clan"
    elif splat == "Shifter":
        return "node_shifter_type"
    elif splat == "Mage":
        return "node_mage_faction"
    elif splat == "Changeling":
        return "node_changeling_kith"
    else:
        return "node_start"

# Add nodes for splat-specific choices (vampire clan, shifter type, mage faction, changeling kith)

def node_vampire_clan(caller):
    text = "Choose your vampire clan:"
    clans = Stat.objects.filter(category="identity", stat_type="lineage", name="Clan")
    options = [{"key": str(i+1), "desc": clan, "goto": (_set_clan, {"clan": clan})} 
               for i, clan in enumerate(clans[0].values)]
    options.append({"key": "0", "desc": "Return to main menu", "goto": "node_start"})
    return text, options

def _set_clan(caller, raw_string, **kwargs):
    clan = kwargs.get("clan")
    caller.db.chargen["clan"] = clan
    caller.msg(f"Clan set to: {clan}")
    return "node_start"

def node_shifter_type(caller):
    text = "Choose your shifter type:"
    options = [{"key": str(i+1), "desc": shifter_type, "goto": (_set_shifter_type, {"shifter_type": shifter_type})} 
               for i, shifter_type in enumerate(SHIFTER_IDENTITY_STATS.keys())]
    options.append({"key": "0", "desc": "Return to splat selection", "goto": "node_splat"})
    return text, options

def _set_shifter_type(caller, raw_string, **kwargs):
    shifter_type = kwargs.get("shifter_type")
    caller.db.chargen["shifter_type"] = shifter_type
    caller.msg(f"Shifter type set to: {shifter_type}")
    return "node_shifter_details"

def node_shifter_details(caller):
    shifter_type = caller.db.chargen.get("shifter_type")
    if not shifter_type:
        caller.msg("Error: Shifter type not set.")
        return "node_shifter_type"
    
    text = f"Set details for your {shifter_type}:"
    options = [{"key": str(i+1), "desc": stat, "goto": (_set_shifter_detail, {"stat": stat})} 
               for i, stat in enumerate(SHIFTER_IDENTITY_STATS[shifter_type])]
    options.append({"key": "0", "desc": "Return to shifter type selection", "goto": "node_shifter_type"})
    return text, options

def _set_shifter_detail(caller, raw_string, **kwargs):
    stat = kwargs.get("stat")
    text = f"Enter the value for {stat}:"
    options = (
        {"key": "_default", "goto": (_save_shifter_detail, {"stat": stat})},
    )
    return text, options

def _save_shifter_detail(caller, raw_string, **kwargs):
    stat = kwargs.get("stat")
    value = raw_string.strip()
    if "shifter_details" not in caller.db.chargen:
        caller.db.chargen["shifter_details"] = {}
    caller.db.chargen["shifter_details"][stat] = value
    caller.msg(f"{stat} set to: {value}")
    return "node_shifter_details"

def node_shifter_renown(caller):
    shifter_type = caller.db.chargen.get("shifter_type")
    if not shifter_type:
        caller.msg("Error: Shifter type not set.")
        return "node_shifter_type"
    
    if shifter_type not in SHIFTER_RENOWN or not SHIFTER_RENOWN[shifter_type]:
        caller.msg(f"{shifter_type} do not use Renown.")
        return "node_start"
    
    text = f"Set Renown for your {shifter_type}:"
    options = [{"key": str(i+1), "desc": renown, "goto": (_set_renown, {"renown": renown})} 
               for i, renown in enumerate(SHIFTER_RENOWN[shifter_type])]
    options.append({"key": "0", "desc": "Return to shifter details", "goto": "node_shifter_details"})
    return text, options

def _set_renown(caller, raw_string, **kwargs):
    renown = kwargs.get("renown")
    text = f"Enter the value for {renown} Renown (1-5):"
    options = (
        {"key": "_default", "goto": (_save_renown, {"renown": renown})},
    )
    return text, options

def _save_renown(caller, raw_string, **kwargs):
    renown = kwargs.get("renown")
    try:
        value = int(raw_string.strip())
        if 1 <= value <= 5:
            if "renown" not in caller.db.chargen:
                caller.db.chargen["renown"] = {}
            caller.db.chargen["renown"][renown] = value
            caller.msg(f"{renown} Renown set to: {value}")
        else:
            caller.msg("Value must be between 1 and 5.")
    except ValueError:
        caller.msg("Please enter a valid number.")
    return "node_shifter_renown"

def node_mage_faction(caller):
    text = "Choose your mage faction:"
    factions = ["Traditions", "Technocracy", "Nephandi"]
    options = [{"key": str(i+1), "desc": faction, "goto": (_set_mage_faction, {"faction": faction})} 
               for i, faction in enumerate(factions)]
    options.append({"key": "0", "desc": "Return to main menu", "goto": "node_start"})
    return text, options

def _set_mage_faction(caller, raw_string, **kwargs):
    faction = kwargs.get("faction")
    caller.db.chargen["mage_faction"] = faction
    caller.msg(f"Mage faction set to: {faction}")
    if faction == "Traditions":
        return "node_mage_tradition"
    elif faction == "Technocracy":
        return "node_mage_convention"
    else:
        return "node_nephandi_faction"

def node_mage_tradition(caller):
    text = "Choose your mage tradition:"
    traditions = Stat.objects.filter(category="identity", stat_type="lineage", name="Tradition")
    if not traditions.exists():
        caller.msg("No traditions found in the database. Please contact an admin.")
        return "node_start"
    
    options = []
    for i, tradition in enumerate(traditions.first().values):
        options.append({
            "key": str(i+1),
            "desc": tradition,
            "goto": (_set_tradition, {"tradition": tradition})
        })
    options.append({"key": "0", "desc": "Return to main menu", "goto": "node_start"})
    return text, options

def _set_tradition(caller, raw_string, **kwargs):
    tradition = kwargs.get("tradition")
    caller.db.chargen["tradition"] = tradition
    caller.msg(f"Tradition set to: {tradition}")
    return "node_mage_subfaction"

def node_mage_subfaction(caller):
    tradition = caller.db.chargen.get("tradition")
    if not tradition:
        caller.msg("Error: Tradition not set.")
        return "node_start"
    
    text = f"Choose your subfaction within the {tradition}:"
    subfactions = Stat.objects.filter(category="identity", stat_type="lineage", name="Tradition Subfaction")
    if not subfactions.exists():
        caller.msg("No subfactions found in the database. Please contact an admin.")
        return "node_start"
    
    options = []
    for i, subfaction in enumerate(subfactions.first().values):
        if subfaction.startswith(tradition):
            options.append({
                "key": str(len(options) + 1),
                "desc": subfaction,
                "goto": (_set_subfaction, {"subfaction": subfaction})
            })
    options.append({"key": "0", "desc": "Return to tradition selection", "goto": "node_mage_tradition"})
    return text, options

def _set_subfaction(caller, raw_string, **kwargs):
    subfaction = kwargs.get("subfaction")
    caller.db.chargen["mage_subfaction"] = subfaction
    caller.msg(f"Subfaction set to: {subfaction}")
    return "node_start"

def node_mage_convention(caller):
    text = "Choose your Technocratic Convention:"
    conventions = Stat.objects.filter(category="identity", stat_type="lineage", name="Convention")
    if not conventions.exists():
        caller.msg("No conventions found in the database. Please contact an admin.")
        return "node_start"
    
    options = []
    for i, convention in enumerate(conventions.first().values):
        options.append({
            "key": str(i+1),
            "desc": convention,
            "goto": (_set_convention, {"convention": convention})
        })
    options.append({"key": "0", "desc": "Return to main menu", "goto": "node_start"})
    return text, options

def _set_convention(caller, raw_string, **kwargs):
    convention = kwargs.get("convention")
    caller.db.chargen["convention"] = convention
    caller.msg(f"Convention set to: {convention}")
    return "node_mage_methodology"

def node_mage_methodology(caller):
    convention = caller.db.chargen.get("convention")
    if not convention:
        caller.msg("Error: Convention not set.")
        return "node_start"
    
    text = f"Choose your methodology within {convention}:"
    methodologies = Stat.objects.filter(category="identity", stat_type="lineage", name="Methodology")
    if not methodologies.exists():
        caller.msg("No methodologies found in the database. Please contact an admin.")
        return "node_start"
    
    options = []
    for i, methodology in enumerate(methodologies.first().values):
        if methodology.startswith(convention):
            options.append({
                "key": str(len(options) + 1),
                "desc": methodology,
                "goto": (_set_methodology, {"methodology": methodology})
            })
    options.append({"key": "0", "desc": "Return to convention selection", "goto": "node_mage_convention"})
    return text, options

def _set_methodology(caller, raw_string, **kwargs):
    methodology = kwargs.get("methodology")
    caller.db.chargen["methodology"] = methodology
    caller.msg(f"Methodology set to: {methodology}")
    return "node_start"

def node_nephandi_faction(caller):
    text = "Choose your Nephandi faction:"
    factions = Stat.objects.filter(category="identity", stat_type="lineage", name="Nephandi Faction")
    if not factions.exists():
        caller.msg("No Nephandi factions found in the database. Please contact an admin.")
        return "node_start"
    
    options = []
    for i, faction in enumerate(factions.first().values):
        options.append({
            "key": str(i+1),
            "desc": faction,
            "goto": (_set_nephandi_faction, {"faction": faction})
        })
    options.append({"key": "0", "desc": "Return to main menu", "goto": "node_start"})
    return text, options

def _set_nephandi_faction(caller, raw_string, **kwargs):
    faction = kwargs.get("faction")
    caller.db.chargen["nephandi_faction"] = faction
    caller.msg(f"Nephandi faction set to: {faction}")
    return "node_start"

def node_changeling_kith(caller):
    text = "Choose your changeling kith:"
    kiths = Stat.objects.filter(category="identity", stat_type="lineage", name="Kith")
    options = [{"key": str(i+1), "desc": kith, "goto": (_set_kith, {"kith": kith})} 
               for i, kith in enumerate(kiths[0].values)]
    options.append({"key": "0", "desc": "Return to main menu", "goto": "node_start"})
    return text, options

def _set_kith(caller, raw_string, **kwargs):
    kith = kwargs.get("kith")
    caller.db.chargen["kith"] = kith
    caller.msg(f"Kith set to: {kith}")
    return "node_changeling_seeming"

def node_changeling_seeming(caller):
    text = "Choose your changeling seeming:"
    seemings = Stat.objects.filter(category="identity", stat_type="lineage", name="Seeming")
    options = [{"key": str(i+1), "desc": seeming, "goto": (_set_seeming, {"seeming": seeming})} 
               for i, seeming in enumerate(seemings[0].values)]
    options.append({"key": "0", "desc": "Return to main menu", "goto": "node_start"})
    return text, options

def _set_seeming(caller, raw_string, **kwargs):
    seeming = kwargs.get("seeming")
    caller.db.chargen["seeming"] = seeming
    caller.msg(f"Seeming set to: {seeming}")
    return "node_changeling_house"

def node_changeling_house(caller):
    text = "Choose your changeling house (optional):"
    houses = Stat.objects.filter(category="identity", stat_type="lineage", name="House")
    options = [{"key": str(i+1), "desc": house, "goto": (_set_house, {"house": house})} 
               for i, house in enumerate(houses[0].values)]
    options.append({"key": "0", "desc": "No house / Return to main menu", "goto": "node_start"})
    return text, options

def _set_house(caller, raw_string, **kwargs):
    house = kwargs.get("house")
    caller.db.chargen["house"] = house
    caller.msg(f"House set to: {house}")
    return "node_start"

ATTRIBUTE_CATEGORIES = ['Physical', 'Social', 'Mental']
ABILITY_CATEGORIES = ['Talents', 'Skills', 'Knowledges']

ABILITIES = {
    'Talents': ['Alertness', 'Athletics', 'Awareness', 'Brawl', 'Empathy', 'Expression', 'Intimidation', 'Leadership', 'Streetwise', 'Subterfuge'],
    'Skills': ['Animal Ken', 'Crafts', 'Drive', 'Etiquette', 'Firearms', 'Larceny', 'Melee', 'Performance', 'Stealth', 'Survival'],
    'Knowledges': ['Academics', 'Computer', 'Finance', 'Investigation', 'Law', 'Medicine', 'Occult', 'Politics', 'Science', 'Technology']
}

SECONDARY_ABILITIES = {
    'Talents': ['Carousing', 'Diplomacy', 'Intrigue', 'Mimicry', 'Scrounging', 'Seduction', 'Style'],
    'Skills': ['Archery', 'Fortitude', 'Fencing', 'Gambling', 'Fast-Talking', 'Pilot', 'Torture'],
    'Knowledges': ['Area Knowledge', 'Cultural Savvy', 'Demolitions', 'Herbalism', 'Media', 'Power-Brokering', 'Vice']
}

def node_attributes(caller):
    text = "Choose an attribute category to assign points:"
    options = [
        {"key": "1", "desc": "Physical Attributes", "goto": "node_physical_attributes"},
        {"key": "2", "desc": "Social Attributes", "goto": "node_social_attributes"},
        {"key": "3", "desc": "Mental Attributes", "goto": "node_mental_attributes"},
        {"key": "0", "desc": "Return to main menu", "goto": "node_start"}
    ]
    return text, options

def node_select_attribute_category(caller):
    remaining_categories = [cat for cat in ATTRIBUTE_CATEGORIES if cat not in caller.db.chargen['attribute_order']]
    text = f"Select {'primary' if len(caller.db.chargen['attribute_order']) == 0 else 'secondary' if len(caller.db.chargen['attribute_order']) == 1 else 'tertiary'} attribute category:"
    options = [{"key": str(i+1), "desc": cat, "goto": (_set_attribute_category, {"category": cat})} 
               for i, cat in enumerate(remaining_categories)]
    return text, options

def _set_attribute_category(caller, raw_string, **kwargs):
    category = kwargs.get("category")
    caller.db.chargen['attribute_order'].append(category)
    caller.msg(f"Added {category} to attribute order.")
    return "node_attributes"

def node_distribute_attribute_points(caller):
    current_category = caller.db.chargen['attribute_order'][0]  # Start with primary
    points_to_distribute = 7 if len(caller.db.chargen['attribute_order']) == 3 else 5 if len(caller.db.chargen['attribute_order']) == 2 else 3
    
    if 'attributes' not in caller.db.chargen:
        caller.db.chargen['attributes'] = {cat: {'points_left': 0, 'attributes': {}} for cat in ATTRIBUTE_CATEGORIES}
        for cat in ATTRIBUTE_CATEGORIES:
            caller.db.chargen['attributes'][cat]['points_left'] = 7 if cat == caller.db.chargen['attribute_order'][0] else 5 if cat == caller.db.chargen['attribute_order'][1] else 3
    
    if caller.db.chargen['attributes'][current_category]['points_left'] == 0:
        # Move to next category or finish
        caller.db.chargen['attribute_order'].pop(0)
        if not caller.db.chargen['attribute_order']:
            return "node_abilities"  # All attributes distributed, move to abilities
        return "node_distribute_attribute_points"
    
    text = f"Distribute points for {current_category} attributes. Points left: {caller.db.chargen['attributes'][current_category]['points_left']}\n"
    text += "Current values:\n"
    for attr in get_attributes_for_category(current_category):
        current_value = caller.db.chargen['attributes'][current_category]['attributes'].get(attr, 1)
        text += f"{attr}: {current_value}\n"
    
    options = [{"key": str(i+1), "desc": attr, "goto": (_set_attribute_value, {"category": current_category, "attribute": attr})} 
               for i, attr in enumerate(get_attributes_for_category(current_category))]
    options.append({"key": "0", "desc": "Finish this category", "goto": "node_distribute_attribute_points"})
    return text, options

def _set_attribute_value(caller, raw_string, **kwargs):
    category = kwargs.get("category")
    attribute = kwargs.get("attribute")
    try:
        value = int(raw_string.strip())
        if 1 <= value <= 5:
            # Update chargen data
            if 'attributes' not in caller.db.chargen:
                caller.db.chargen['attributes'] = {}
            if category not in caller.db.chargen['attributes']:
                caller.db.chargen['attributes'][category] = {}
            caller.db.chargen['attributes'][category][attribute] = value

            # Update character stats directly
            if 'stats' not in caller.db:
                caller.db.stats = {}
            if 'attributes' not in caller.db.stats:
                caller.db.stats['attributes'] = {}
            if category not in caller.db.stats['attributes']:
                caller.db.stats['attributes'][category] = {}
            if attribute not in caller.db.stats['attributes'][category]:
                caller.db.stats['attributes'][category][attribute] = {}
            caller.db.stats['attributes'][category][attribute]['perm'] = value
            caller.db.stats['attributes'][category][attribute]['temp'] = value

            caller.msg(f"{attribute} set to: {value}")
            
            # Return to the appropriate attribute menu
            if category == "physical":
                return "node_physical_attributes"
            elif category == "social":
                return "node_social_attributes"
            else:
                return "node_mental_attributes"
        else:
            caller.msg("Value must be between 1 and 5.")
            # Return to the same node to retry
            return f"node_{category}_attributes"
    except ValueError:
        caller.msg("Please enter a valid number.")
        # Return to the same node to retry
        return f"node_{category}_attributes"

def _save_attribute_value(caller, raw_string, **kwargs):
    category = kwargs.get("category")
    attribute = kwargs.get("attribute")
    try:
        value = int(raw_string.strip())
        points_left = caller.db.chargen['attributes'][category]['points_left']
        current_value = caller.db.chargen['attributes'][category]['attributes'].get(attribute, 1)
        if 0 <= value <= points_left:
            new_value = current_value + value
            if new_value <= 5:
                caller.db.chargen['attributes'][category]['attributes'][attribute] = new_value
                caller.db.chargen['attributes'][category]['points_left'] -= value
                caller.msg(f"{attribute} set to {new_value}")
            else:
                caller.msg(f"Total value cannot exceed 5. Current value: {current_value}, Attempted to add: {value}")
        else:
            caller.msg(f"Please enter a number between 0 and {points_left}")
    except ValueError:
        caller.msg("Please enter a valid number")
    return "node_distribute_attribute_points"

def get_attributes_for_category(category):
    if category == 'Physical':
        return ['Strength', 'Dexterity', 'Stamina']
    elif category == 'Social':
        return ['Charisma', 'Manipulation', 'Appearance']
    elif category == 'Mental':
        return ['Perception', 'Intelligence', 'Wits']

def node_abilities(caller):
    
    Show available abilities based on character's splat
    
    if 'ability_order' not in caller.db.chargen:
        caller.db.chargen['ability_order'] = []
    
    if len(caller.db.chargen['ability_order']) < 3:
        return node_select_ability_category(caller)
    else:
        return node_distribute_ability_points(caller)

def get_available_abilities(character, category):
    Get both basic and splat-specific abilities for the category
    splat = character.db.chargen.get('splat', '')
    
    # Get basic abilities
    abilities = list(Stat.objects.filter(
        category='abilities',
        stat_type=category,
        splat__isnull=True
    ))
    
    # Get splat-specific abilities if splat is set
    if splat:
        splat_abilities = list(Stat.objects.filter(
            category='abilities',
            stat_type=category,
            splat__iexact=splat
        ))
        abilities.extend(splat_abilities)
    
    return sorted(abilities, key=lambda x: x.name)

def node_distribute_ability_points(caller):
    current_category = caller.db.chargen['ability_order'][0]
    points_to_distribute = 13 if len(caller.db.chargen['ability_order']) == 3 else 9 if len(caller.db.chargen['ability_order']) == 2 else 5
    
    if 'abilities' not in caller.db.chargen:
        caller.db.chargen['abilities'] = {cat: {'points_left': 0, 'abilities': {}, 'secondary_abilities': {}} for cat in ABILITY_CATEGORIES}
        for cat in ABILITY_CATEGORIES:
            caller.db.chargen['abilities'][cat]['points_left'] = 13 if cat == caller.db.chargen['ability_order'][0] else 9 if cat == caller.db.chargen['ability_order'][1] else 5
    
    if caller.db.chargen['abilities'][current_category]['points_left'] == 0:
        caller.db.chargen['ability_order'].pop(0)
        if not caller.db.chargen['ability_order']:
            return "node_next_step"
        return "node_distribute_ability_points"
    
    text = f"Distribute points for {current_category}. Points left: {caller.db.chargen['abilities'][current_category]['points_left']}\n"
    
    # Get both basic and splat-specific abilities
    available_abilities = get_available_abilities(caller, current_category)
    
    options = []
    for i, ability in enumerate(available_abilities):
        current_value = caller.db.chargen['abilities'][current_category]['abilities'].get(ability.name, 0)
        text += f"{ability.name}: {current_value}\n"
        options.append({
            "key": str(i+1),
            "desc": ability.name,
            "goto": (_set_ability_value, {"category": current_category, "ability": ability.name})
        })
    
    options.append({"key": "0", "desc": "Finish this category", "goto": "node_distribute_ability_points"})
    return text, options

def _set_ability_value(caller, raw_string, **kwargs):
    category = kwargs.get("category")
    ability = kwargs.get("ability")
    is_secondary = kwargs.get("is_secondary", False)
    points_left = caller.db.chargen['abilities'][category]['points_left']
    
    max_points = min(points_left, 5 if not is_secondary else 3)
    text = f"Enter points to add to {ability} (1-{max_points}):"
    options = (
        {"key": "_default", "goto": (_save_ability_value, {"category": category, "ability": ability, "is_secondary": is_secondary})},
    )
    return text, options

def _save_ability_value(caller, raw_string, **kwargs):
    category = kwargs.get("category")
    ability = kwargs.get("ability")
    is_secondary = kwargs.get("is_secondary")
    try:
        value = int(raw_string.strip())
        points_left = caller.db.chargen['abilities'][category]['points_left']
        max_points = min(points_left, 5 if not is_secondary else 3)
        if 1 <= value <= max_points:
            cost = value if not is_secondary else value * 2
            if cost <= points_left:
                if is_secondary:
                    caller.db.chargen['abilities'][category]['secondary_abilities'][ability] = value
                else:
                    caller.db.chargen['abilities'][category]['abilities'][ability] = value
                caller.db.chargen['abilities'][category]['points_left'] -= cost
                caller.msg(f"{ability} set to {value}" + (" (Secondary)" if is_secondary else ""))
            else:
                caller.msg(f"Not enough points left. Cost: {cost}, Points left: {points_left}")
        else:
            caller.msg(f"Please enter a number between 1 and {max_points}")
    except ValueError:
        caller.msg("Please enter a valid number")
    return "node_distribute_ability_points"

# Helper functions
def get_attributes_for_category(category):
    if category == 'Physical':
        return ['Strength', 'Dexterity', 'Stamina']
    elif category == 'Social':
        return ['Charisma', 'Manipulation', 'Appearance']
    elif category == 'Mental':
        return ['Perception', 'Intelligence', 'Wits']

def get_abilities_for_category(category):
    # You'll need to define these based on your game's ability list
    pass

def node_physical_attributes(caller):
    text = "Assign points to Physical Attributes (Strength, Dexterity, Stamina):"
    options = [
        {"key": "1", "desc": "Strength", "goto": (_set_attribute_value, {"category": "physical", "attribute": "Strength"})},
        {"key": "2", "desc": "Dexterity", "goto": (_set_attribute_value, {"category": "physical", "attribute": "Dexterity"})},
        {"key": "3", "desc": "Stamina", "goto": (_set_attribute_value, {"category": "physical", "attribute": "Stamina"})},
        {"key": "0", "desc": "Return to attributes menu", "goto": "node_attributes"}
    ]
    return text, options

def node_mental_attributes(caller):
    text = "Assign points to Mental Attributes (Perception, Intelligence, Wits):"
    options = [
        {"key": "1", "desc": "Perception", "goto": (_set_attribute_value, {"category": "mental", "attribute": "Perception"})},
        {"key": "2", "desc": "Intelligence", "goto": (_set_attribute_value, {"category": "mental", "attribute": "Intelligence"})},
        {"key": "3", "desc": "Wits", "goto": (_set_attribute_value, {"category": "mental", "attribute": "Wits"})},
        {"key": "0", "desc": "Return to attributes menu", "goto": "node_attributes"}
    ]
    return text, options

def _set_attribute(caller, raw_string, **kwargs):
    # This function should return a string or (string, dict)
    category = kwargs.get("category")
    attribute = kwargs.get("attribute")
    text = f"Enter the value for {attribute} (1-5):"
    options = (
        {"key": "_default", "goto": (_save_attribute, {"category": category, "attribute": attribute})},
    )
    return text, options

def _save_attribute(caller, raw_string, **kwargs):
    category = kwargs.get("category")
    attribute = kwargs.get("attribute")
    try:
        value = int(raw_string.strip())
        if 1 <= value <= 5:
            if 'attributes' not in caller.db.chargen:
                caller.db.chargen['attributes'] = {}
            if category not in caller.db.chargen['attributes']:
                caller.db.chargen['attributes'][category] = {}
            caller.db.chargen['attributes'][category][attribute] = value
            caller.msg(f"{attribute} set to: {value}")
        else:
            caller.msg("Value must be between 1 and 5.")
    except ValueError:
        caller.msg("Please enter a valid number.")
    
    # Return to the appropriate attribute menu
    if category == "physical":
        return "node_physical_attributes"
    elif category == "social":
        return "node_social_attributes"
    else:
        return "node_mental_attributes"

def node_social_attributes(caller):
    text = "Assign points to Social Attributes (Charisma, Manipulation, Appearance):"
    options = [
        {"key": "1", "desc": "Charisma", "goto": (_set_attribute_value, {"category": "social", "attribute": "Charisma"})},
        {"key": "2", "desc": "Manipulation", "goto": (_set_attribute_value, {"category": "social", "attribute": "Manipulation"})},
        {"key": "3", "desc": "Appearance", "goto": (_set_attribute_value, {"category": "social", "attribute": "Appearance"})},
        {"key": "0", "desc": "Return to attributes menu", "goto": "node_attributes"}
    ]
    return text, options

def node_mental_attributes(caller):
    if "attributes" not in caller.db.chargen:
        caller.db.chargen["attributes"] = {"physical": {}, "social": {}, "mental": {}}
    
    text = "Assign points to Mental Attributes (Perception, Intelligence, Wits):"
    options = [
        {"key": "1", "desc": "Perception", "goto": (_set_attribute, {"category": "mental", "attribute": "Perception"})},
        {"key": "2", "desc": "Intelligence", "goto": (_set_attribute, {"category": "mental", "attribute": "Intelligence"})},
        {"key": "3", "desc": "Wits", "goto": (_set_attribute, {"category": "mental", "attribute": "Wits"})},
        {"key": "0", "desc": "Return to attributes menu", "goto": "node_attributes"}
    ]
    return text, options

def node_abilities(caller):
    text = "Assign points to your abilities. You have 13/9/5 points to distribute among Talents, Skills, and Knowledges."
    options = [
        {"key": "1", "desc": "Assign Talents", "goto": "node_talents"},
        {"key": "2", "desc": "Assign Skills", "goto": "node_skills"},
        {"key": "3", "desc": "Assign Knowledges", "goto": "node_knowledges"},
        {"key": "0", "desc": "Return to main menu", "goto": "node_start"}
    ]
    return text, options

def node_talents(caller):
    if "abilities" not in caller.db.chargen:
        caller.db.chargen["abilities"] = {"talents": {}, "skills": {}, "knowledges": {}}
    
    text = "Assign points to Talents:"
    talents = Stat.objects.filter(category="abilities", stat_type="talent")
    options = [{"key": str(i+1), "desc": talent.name, "goto": (_set_ability, {"category": "talents", "ability": talent.name})} 
               for i, talent in enumerate(talents)]
    options.append({"key": "0", "desc": "Return to abilities menu", "goto": "node_abilities"})
    return text, options

def _set_ability(caller, raw_string, **kwargs):
    category = kwargs.get("category")
    ability = kwargs.get("ability")
    text = f"Enter the value for {ability} (0-5):"
    options = (
        {"key": "_default", "goto": (_save_ability, {"category": category, "ability": ability})},
    )
    return text, options

def _save_ability(caller, raw_string, **kwargs):
    category = kwargs.get("category")
    ability = kwargs.get("ability")
    try:
        value = int(raw_string.strip())
        if 0 <= value <= 5:
            caller.db.chargen["abilities"][category][ability] = value
            caller.msg(f"{ability} set to: {value}")
        else:
            caller.msg("Value must be between 0 and 5.")
    except ValueError:
        caller.msg("Please enter a valid number.")
    
    if category == "talents":
        return "node_talents"
    elif category == "skills":
        return "node_skills"
    else:
        return "node_knowledges"

def node_skills(caller):
    if "abilities" not in caller.db.chargen:
        caller.db.chargen["abilities"] = {"talents": {}, "skills": {}, "knowledges": {}}
    
    text = "Assign points to Skills:"
    skills = Stat.objects.filter(category="abilities", stat_type="skill")
    options = [{"key": str(i+1), "desc": skill.name, "goto": (_set_ability, {"category": "skills", "ability": skill.name})} 
               for i, skill in enumerate(skills)]
    options.append({"key": "0", "desc": "Return to abilities menu", "goto": "node_abilities"})
    return text, options

def node_knowledges(caller):
    if "abilities" not in caller.db.chargen:
        caller.db.chargen["abilities"] = {"talents": {}, "skills": {}, "knowledges": {}}
    
    text = "Assign points to Knowledges:"
    knowledges = Stat.objects.filter(category="abilities", stat_type="knowledge")
    options = [{"key": str(i+1), "desc": knowledge.name, "goto": (_set_ability, {"category": "knowledges", "ability": knowledge.name})} 
               for i, knowledge in enumerate(knowledges)]
    options.append({"key": "0", "desc": "Return to abilities menu", "goto": "node_abilities"})
    return text, options

def node_powers(caller):
    splat = caller.db.chargen.get("splat")
    if not splat:
        caller.msg("Error: Character splat not set.")
        return "node_start"
    
    if splat == "Vampire":
        return node_disciplines(caller)
    elif splat == "Shifter":
        return node_gifts(caller)
    elif splat == "Mage":
        return node_spheres(caller)
    elif splat == "Changeling":
        return node_arts(caller)
    else:
        caller.msg("No special powers available for this character type.")
        return "node_start"

def node_disciplines(caller):
    if "disciplines" not in caller.db.chargen:
        caller.db.chargen["disciplines"] = {}
    
    text = "Assign points to Disciplines:"
    disciplines = Stat.objects.filter(category="powers", stat_type="discipline")
    options = [{"key": str(i+1), "desc": discipline.name, "goto": (_set_power, {"category": "disciplines", "power": discipline.name})} 
               for i, discipline in enumerate(disciplines)]
    options.append({"key": "0", "desc": "Return to main menu", "goto": "node_start"})
    return text, options

def _set_power(caller, raw_string, **kwargs):
    category = kwargs.get("category")
    power = kwargs.get("power")
    text = f"Enter the value for {power} (1-5):"
    options = (
        {"key": "_default", "goto": (_save_power, {"category": category, "power": power})},
    )
    return text, options

def _save_power(caller, raw_string, **kwargs):
    category = kwargs.get("category")
    power = kwargs.get("power")
    try:
        value = int(raw_string.strip())
        if 1 <= value <= 5:
            caller.db.chargen[category][power] = value
            caller.msg(f"{power} set to: {value}")
        else:
            caller.msg("Value must be between 1 and 5.")
    except ValueError:
        caller.msg("Please enter a valid number.")
    
    if category == "disciplines":
        return "node_disciplines"
    elif category == "gifts":
        return "node_gifts"
    elif category == "spheres":
        return "node_spheres"
    else:
        return "node_arts"

def node_gifts(caller):
    if "gifts" not in caller.db.chargen:
        caller.db.chargen["gifts"] = {}
    
    text = "Choose Gifts for your character:"
    gifts = Stat.objects.filter(category="powers", stat_type="gift")
    options = [{"key": str(i+1), "desc": gift.name, "goto": (_set_power, {"category": "gifts", "power": gift.name})} 
               for i, gift in enumerate(gifts)]
    options.append({"key": "0", "desc": "Return to main menu", "goto": "node_start"})
    return text, options

def node_spheres(caller):
    if "spheres" not in caller.db.chargen:
        caller.db.chargen["spheres"] = {}
    
    text = "Assign points to Spheres:"
    spheres = Stat.objects.filter(category="powers", stat_type="sphere")
    options = [{"key": str(i+1), "desc": sphere.name, "goto": (_set_power, {"category": "spheres", "power": sphere.name})} 
               for i, sphere in enumerate(spheres)]
    options.append({"key": "0", "desc": "Return to main menu", "goto": "node_start"})
    return text, options

def node_arts(caller):
    if "arts" not in caller.db.chargen:
        caller.db.chargen["arts"] = {}
    
    text = "Assign points to Arts:"
    arts = Stat.objects.filter(category="powers", stat_type="art")
    options = [{"key": str(i+1), "desc": art.name, "goto": (_set_power, {"category": "arts", "power": art.name})} 
               for i, art in enumerate(arts)]
    options.append({"key": "0", "desc": "Return to main menu", "goto": "node_start"})
    return text, options

def node_backgrounds(caller):
    if "backgrounds" not in caller.db.chargen:
        caller.db.chargen["backgrounds"] = {}
    
    text = "Assign points to Backgrounds:"
    backgrounds = Stat.objects.filter(category="backgrounds", stat_type="background")
    options = [{"key": str(i+1), "desc": background.name, "goto": (_set_background, {"background": background.name})} 
               for i, background in enumerate(backgrounds)]
    options.append({"key": "0", "desc": "Return to main menu", "goto": "node_start"})
    return text, options

def _set_background(caller, raw_string, **kwargs):
    background = kwargs.get("background")
    text = f"Enter the value for {background} (1-5):"
    options = (
        {"key": "_default", "goto": (_save_background, {"background": background})},
    )
    return text, options

def _save_background(caller, raw_string, **kwargs):
    background = kwargs.get("background")
    try:
        value = int(raw_string.strip())
        if 1 <= value <= 5:
            caller.db.chargen["backgrounds"][background] = value
            caller.msg(f"{background} set to: {value}")
        else:
            caller.msg("Value must be between 1 and 5.")
    except ValueError:
        caller.msg("Please enter a valid number.")
    return "node_backgrounds"

def node_virtues(caller):
    if "virtues" not in caller.db.chargen:
        caller.db.chargen["virtues"] = {}
    
    text = "Assign points to Virtues:"
    virtues = Stat.objects.filter(category="virtues", stat_type="moral")
    options = [{"key": str(i+1), "desc": virtue.name, "goto": (_set_virtue, {"virtue": virtue.name})} 
               for i, virtue in enumerate(virtues)]
    options.append({"key": "0", "desc": "Return to main menu", "goto": "node_start"})
    return text, options

def _set_virtue(caller, raw_string, **kwargs):
    virtue = kwargs.get("virtue")
    text = f"Enter the value for {virtue} (1-5):"
    options = (
        {"key": "_default", "goto": (_save_virtue, {"virtue": virtue})},
    )
    return text, options

def _save_virtue(caller, raw_string, **kwargs):
    virtue = kwargs.get("virtue")
    try:
        value = int(raw_string.strip())
        if 1 <= value <= 5:
            caller.db.chargen["virtues"][virtue] = value
            caller.msg(f"{virtue} set to: {value}")
        else:
            caller.msg("Value must be between 1 and 5.")
    except ValueError:
        caller.msg("Please enter a valid number.")
    return "node_virtues"

def node_review(caller):
    text = "Review your character:\n\n"
    chargen_data = caller.db.chargen
    
    text += f"Concept: {chargen_data.get('concept', 'Not set')}\n"
    text += f"Nature: {chargen_data.get('nature', 'Not set')}\n"
    text += f"Demeanor: {chargen_data.get('demeanor', 'Not set')}\n"
    text += f"Splat: {chargen_data.get('splat', 'Not set')}\n"
    
    if 'clan' in chargen_data:
        text += f"Clan: {chargen_data['clan']}\n"
    if 'shifter_type' in chargen_data:
        text += f"Shifter Type: {chargen_data['shifter_type']}\n"
    if 'mage_faction' in chargen_data:
        text += f"Mage Faction: {chargen_data['mage_faction']}\n"
    if 'kith' in chargen_data:
        text += f"Kith: {chargen_data['kith']}\n"
    
    text += "\nAttributes:\n"
    for category in ['physical', 'social', 'mental']:
        text += f"  {category.capitalize()}:\n"
        attributes = caller.db.stats.get('attributes', {}).get(category, {})
        for attr, values in attributes.items():
            perm_value = values.get('perm', 0)
            temp_value = values.get('temp', perm_value)
            text += f"    {attr}: {perm_value}"
            if temp_value != perm_value:
                text += f" ({temp_value})"
            text += "\n"
    
    text += "\nAbilities:\n"
    for category, abilities in chargen_data.get('abilities', {}).items():
        text += f"  {category.capitalize()}:\n"
        for ability, value in abilities.items():
            text += f"    {ability}: {value}\n"
    
    text += "\nPowers:\n"
    if 'disciplines' in chargen_data:
        text += "  Disciplines:\n"
        for discipline, value in chargen_data['disciplines'].items():
            text += f"    {discipline}: {value}\n"
    if 'gifts' in chargen_data:
        text += "  Gifts:\n"
        for gift, value in chargen_data['gifts'].items():
            text += f"    {gift}: {value}\n"
    if 'spheres' in chargen_data:
        text += "  Spheres:\n"
        for sphere, value in chargen_data['spheres'].items():
            text += f"    {sphere}: {value}\n"
    if 'arts' in chargen_data:
        text += "  Arts:\n"
        for art, value in chargen_data['arts'].items():
            text += f"    {art}: {value}\n"
    
    text += "\nBackgrounds:\n"
    for background, value in chargen_data.get('backgrounds', {}).items():
        text += f"  {background}: {value}\n"
    
    text += "\nVirtues:\n"
    for virtue, value in chargen_data.get('virtues', {}).items():
        text += f"  {virtue}: {value}\n"
    
    options = [
        {"key": "1", "desc": "Finish character creation", "goto": "node_finish"},
        {"key": "2", "desc": "Return to main menu to make changes", "goto": "node_start"},
    ]
    return text, options

def node_finish(caller):
    text = "Are you sure you want to finish character creation? This will apply all your choices and cannot be undone."
    options = [
        {"key": "Y", "desc": "Yes, finish character creation", "goto": _finish_chargen},
        {"key": "N", "desc": "No, return to review", "goto": "node_review"},
    ]
    return text, options

def _finish_chargen(caller):
    _apply_chargen_data(caller)
    caller.msg("Character creation complete! Your character has been created and is ready to play.")
    return None

"""
ATTRIBUTE_CATEGORIES = ['Physical', 'Social', 'Mental']
ABILITY_CATEGORIES = ['Talents', 'Skills', 'Knowledges']

class CmdSubmit(MuxCommand):
    """
    Submit your character for approval.

    Usage:
      +submit

    This command will automatically create a job requesting character approval.
    It will include your character's name, splat information, and basic stats.
    Staff will review your character and either approve or request changes.
    """

    key = "+submit"
    locks = "cmd:all()"
    help_category = "Chargen"

    def func(self):
        caller = self.caller
        
        # Check if character is approved using only the persistent attribute
        if caller.db.approved:
            caller.msg("Your character is already approved.")
            return

        # Make sure approved attribute exists and is False if it doesn't exist
        if not hasattr(caller.db, 'approved'):
            caller.db.approved = False

        # Check if there's already an open approval job for this character
        existing_jobs = Job.objects.filter(
            title__icontains=caller.name,
            status__in=['open', 'claimed'],
            queue__name='CHARGEN'
        )
        if existing_jobs.exists():
            caller.msg("You already have a pending approval request. Please wait for staff to review it.")
            return

        # Gather character information
        char_info = []
        char_info.append(f"Character Name: {caller.name}")
        
        # Get splat information from stats
        if hasattr(caller.db, 'stats') and caller.db.stats:
            splat_info = caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm')
            if splat_info:
                char_info.append(f"Splat: {splat_info}")

            # Add attributes
            char_info.append("\nAttributes:")
            for category in ['physical', 'social', 'mental']:
                attributes = caller.db.stats.get(category, {})
                if attributes:
                    char_info.append(f"\n{category.title()}:")
                    for attr_name, attr_data in attributes.items():
                        perm_value = attr_data.get('perm', 0)
                        char_info.append(f"  {attr_name.replace('_', ' ').title()}: {perm_value}")

            # Add abilities
            abilities = caller.db.stats.get('abilities', {})
            if abilities:
                char_info.append("\nAbilities:")
                for ability_name, ability_data in abilities.items():
                    perm_value = ability_data.get('perm', 0)
                    if perm_value > 0:  # Only show abilities with points in them
                        char_info.append(f"  {ability_name.replace('_', ' ').title()}: {perm_value}")

            # Add supernatural powers based on splat
            powers = caller.db.stats.get('powers', {})
            if powers:
                char_info.append("\nPowers:")
                for power_name, power_data in powers.items():
                    perm_value = power_data.get('perm', 0)
                    if perm_value > 0:  # Only show powers with points in them
                        char_info.append(f"  {power_name.replace('_', ' ').title()}: {perm_value}")

        else:
            char_info.append("\nWarning: No character statistics found. Please complete character generation first.")

        # Format the description
        description = "\n".join(char_info)
        description += "\n\nPlease review this character for approval."

        try:
            # Get or create the CHARGEN queue
            queue, _ = Queue.objects.get_or_create(
                name='CHARGEN',
                defaults={'automatic_assignee': None}
            )

            # Create the job
            job = Job.objects.create(
                title=f"Character Approval: {caller.name}",
                description=description,
                requester=caller.account,
                queue=queue,
                status='open'
            )

            # Add a comment with any additional notes
            initial_comment = {
                "author": caller.account.username,
                "text": "Character submitted for approval.",
                "created_at": timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if not job.comments:
                job.comments = []
            job.comments.append(initial_comment)
            job.save()

            caller.msg("|gCharacter submitted for approval. Job ID: #{0}|n".format(job.id))
            caller.msg("Staff will review your character and contact you if any changes are needed.")
            
            # Notify staff through the jobs channel
            from commands.jobs.jobs_commands import CmdJobs
            cmd_jobs = CmdJobs()
            cmd_jobs.caller = caller
            cmd_jobs.post_to_jobs_channel(
                caller.name,
                job.id,
                "submitted character for approval"
            )

        except Exception as e:
            caller.msg("|rError submitting character: {0}|n".format(e))

def node_select_ability_category(caller):
    text = "Select priority for ability categories (Primary: 13 points, Secondary: 9 points, Tertiary: 5 points)"
    remaining_categories = [cat for cat in ABILITY_CATEGORIES if cat not in caller.db.chargen.get('ability_order', [])]
    
    if not remaining_categories:
        return "node_distribute_ability_points"
        
    options = [{"key": str(i+1), "desc": category, "goto": (_set_ability_category, {"category": category})} 
               for i, category in enumerate(remaining_categories)]
    return text, options

def _set_ability_category(caller, raw_string, **kwargs):
    category = kwargs.get("category")
    if 'ability_order' not in caller.db.chargen:
        caller.db.chargen['ability_order'] = []
    caller.db.chargen['ability_order'].append(category)
    caller.msg(f"Added {category} to ability priority order")
    return "node_abilities"

def setup_mortalplus_character(character, mortalplus_type):
    """
    Set up initial stats and powers for Mortal+ characters
    """
    if mortalplus_type not in MORTALPLUS_TYPES:
        raise ValueError(f"Invalid Mortal+ type: {mortalplus_type}")

    # Set basic identity stats
    character.set_stat('identity', 'personal', 'Splat', 'Mortal Plus')
    character.set_stat('identity', 'personal', 'Mortal Plus Type', mortalplus_type)

    # Set up power categories based on type
    for power_category in MORTALPLUS_TYPES[mortalplus_type]:
        character.setup_power_category(power_category)

    # Special handling for each type
    if mortalplus_type == 'Ghoul':
        # Initialize Blood pool
        character.set_stat('pools', 'temporary', 'Blood', {'perm': 1, 'temp': 1})
    
    elif mortalplus_type == 'Kinfolk':
        # Kinfolk start with no special powers - they're merit-gated
        pass
    
    elif mortalplus_type == 'Kinain':
        # Initialize Glamour pool based on Fae Blood Merit
        merits = character.db.stats.get('merits', {}).get('merit', {})
        fae_blood = next((value.get('perm', 0) for merit, value in merits.items() 
                         if merit.lower() == 'fae blood'), 0)
        if fae_blood:
            max_glamour = fae_blood // 2
            character.set_stat('pools', 'temporary', 'Glamour', 
                             {'perm': max_glamour, 'temp': max_glamour})

