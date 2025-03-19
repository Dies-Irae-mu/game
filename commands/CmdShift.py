from tempfile import TemporaryDirectory
from unicodedata import category
from evennia import default_cmds
from evennia.utils import evtable
from typeclasses.characters import Character
from world.wod20th.models import ShapeshifterForm, Stat
from world.wod20th.utils.formatting import format_stat

from random import randint
from typing import List, Tuple

def roll_dice(dice_pool: int, difficulty: int) -> Tuple[List[int], int, int]:
    rolls = [randint(1, 10) for _ in range(max(0, dice_pool))]
    successes = sum(1 for roll in rolls if roll >= difficulty)
    ones = sum(1 for roll in rolls if roll == 1)
    
    # If there are any successes, subtract ones from them
    if successes > 0:
        successes = max(0, successes - ones)
        return rolls, successes, ones
    
    # If there are no successes AND there are ones, it's a botch
    if successes == 0 and ones > 0:
        return rolls, -1, ones  # Indicate botch with -1
    
    # No successes but also no ones - just a failure
    return rolls, 0, ones

def interpret_roll_results(successes, ones, diff=6, rolls=None):
    # A botch only occurs if there are no successes AND there are ones
    is_botch = successes < 0
    
    success_string = f"|g{successes}|n" if successes > 0 else f"|y{successes}|n" if successes == 0 else f"|r{successes}|n"
    
    msg = f"|w(|n{success_string}|w)|n"
    if is_botch:
        msg += f"|r Botch!|n"
    else:
        msg += "|y Successes|n" if successes != 1 else "|y Success|n"
    
    if rolls:
        msg += " |w(|n"
        rolls.sort(reverse=True)
        msg += " ".join(f"|r{roll}|n" if roll == 1 else f"|g{roll}|n" if roll >= diff else f"|y{roll}|n" for roll in rolls)
        msg += "|w)|n"
    
    return msg

class CmdShift(default_cmds.MuxCommand):
    """
    Change your character's shapeshifter form.

    Usage:
      +shift <form name>
      +shift/roll <form name>
      +shift/rage <form name>
      +shift/message <form name> = <your custom message>
      +shift/setdeedname <deed name>
      +shift/setformname <form name> = <form-specific name>
      +shift/name <form name> = <new name>
      +shift/list

    Switches:
      /roll - Roll to determine if the shift is successful
      /rage - Spend Rage points to guarantee a successful shift
      /message - Set your personal custom shift message for the specified form
      /setdeedname - Set your character's deed name for use in most shifted forms
      /setformname - Set a specific name for the character when in a particular form
      /name - Set a new name for the form you're shifting into
      /list - Display all available forms for your character

    This command allows you to change your character's shapeshifter form.
    Without switches, it will attempt to shift using the default method.
    The /roll switch will make a roll to determine success.
    The /rage switch will spend Rage points to guarantee success.
    The /message switch allows you to set your personal custom shift message for a form.
    The /setdeedname switch sets your character's deed name for use in most shifted forms.
    The /setformname switch lets you set a specific name for your character when in a particular form.
    The /name switch allows you to set a new name for the form you're shifting into.
    The /list switch displays all available forms for your character.

    In shift messages, use {truename} for the character's true name, {deedname} for the deed name,
    and {formname} for the form-specific name (if set).
    """

    key = "+shift"
    aliases = ["shift"]
    locks = "cmd:all()"
    help_category = "Shifter"

    def func(self):
        if "debug" in self.switches:
            # No need to re-import ShapeshifterForm here since it's imported at the top
            all_forms = ShapeshifterForm.objects.all()
            
            if not all_forms:
                self.caller.msg("No forms found in database.")
                return
                
            table = evtable.EvTable(
                "|wForm Name|n",
                "|wShifter Type|n",
                "|wStat Modifiers|n",
                "|wDifficulty|n",
                border="header"
            )
            
            for form in all_forms:
                mods = ", ".join([f"{stat} {mod:+d}" for stat, mod in form.stat_modifiers.items()])
                table.add_row(
                    form.name,
                    form.shifter_type,
                    mods,
                    str(form.difficulty)
                )
            
            self.caller.msg(table)
            return
            
        character = self.caller

        # Check if the character is a Shifter
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        if splat.lower() != 'shifter':
            self.caller.msg("Only Shifters can use the +shift command.")
            return

        if not self.args and not self.switches:
            self.caller.msg("Usage: +shift <form name>")
            return

        if not self.is_valid_character(character):
            self.caller.msg("You need to have a valid character to use this command.")
            return
        
        if "list" in self.switches:
            self._list_available_forms()
            return
        elif "message" in self.switches:
            self._set_custom_message(character)
            return
        elif "setdeedname" in self.switches:
            self._set_deed_name(character)
            return
        elif "setformname" in self.switches:
            self._set_form_name(character)
            return
        elif "name" in self.switches:
            self._set_form_name_with_shift(character)
            return

        form_name = self.args.strip()
        try:
            # Get the character's shifter type
            shifter_type = self.caller.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '').lower()
            
            # Look up form by both name and shifter type
            form = ShapeshifterForm.objects.get(
                name__iexact=form_name,
                shifter_type=shifter_type
            )
        except ShapeshifterForm.DoesNotExist:
            self.caller.msg(f"The form '{form_name}' is not available to your shifter type.")
            return
        except ShapeshifterForm.MultipleObjectsReturned:
            self.caller.msg(f"Error: Multiple forms found with name '{form_name}'. Please contact an admin.")
            return

        if "roll" in self.switches:
            success = self._shift_with_roll(character, form)
        elif "rage" in self.switches:
            success = self._shift_with_rage(character, form)
        else:
            success = self._shift_default(character, form)

        if success:
            self._apply_form_changes(character, form)
            self._display_shift_message(character, form)

    def is_valid_character(self, obj):
        """
        Check if the given object is a valid character based on its 'stats' attribute structure.
        """
        return True

    def _list_available_forms(self):
        character = self.caller
        shifter_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '').lower()
        
        # Get all available forms for the character's shifter type
        if shifter_type == 'ananasi':
            available_forms = ShapeshifterForm.objects.filter(shifter_type='ananasi').order_by('name')
        elif shifter_type == 'ajaba':
            available_forms = ShapeshifterForm.objects.filter(shifter_type='ajaba').order_by('name')
        elif shifter_type == 'bastet':
            available_forms = ShapeshifterForm.objects.filter(shifter_type='bastet').order_by('name')
        elif shifter_type == 'corax':
            available_forms = ShapeshifterForm.objects.filter(shifter_type='corax').order_by('name')
        elif shifter_type == 'garou':
            available_forms = ShapeshifterForm.objects.filter(shifter_type='garou').order_by('name')
        elif shifter_type == 'kitsune':
            available_forms = ShapeshifterForm.objects.filter(shifter_type='kitsune').order_by('name')
        elif shifter_type == 'mokole':
            available_forms = ShapeshifterForm.objects.filter(shifter_type='mokole').order_by('name')
        elif shifter_type == 'gurahl':
            available_forms = ShapeshifterForm.objects.filter(shifter_type='gurahl').order_by('name')
        elif shifter_type == 'ratkin':
            available_forms = ShapeshifterForm.objects.filter(shifter_type='ratkin').order_by('name')
        elif shifter_type == 'rokea':
            available_forms = ShapeshifterForm.objects.filter(shifter_type='rokea').order_by('name')
        elif shifter_type == 'nuwisha':
            available_forms = ShapeshifterForm.objects.filter(shifter_type='nuwisha').order_by('name')
        elif shifter_type == 'nagah':
            available_forms = ShapeshifterForm.objects.filter(shifter_type='nagah').order_by('name')
        else:
            self.caller.msg(f"Unknown shifter type: {shifter_type}")
            return

        # Always include Homid form for shapeshifters that can use it
        homid_capable = ['garou', 'ananasi', 'ajaba', 'bastet', 'corax', 'gurahl', 'ratkin']
        if shifter_type.lower() in homid_capable:
            homid_form = ShapeshifterForm.objects.filter(name__iexact='homid').first()
        else:
            homid_form = None
        
        table = evtable.EvTable(
            "|wForm|n",
            "|wStat Modifiers|n",
            "|wDifficulty|n",
            border="header"
        )
        
        if homid_form:
            table.add_row("Homid", "Base Stats", "6")
        
        # Get character's Varna for Mokolé Suchid form or Tribe for Bastet forms
        varna = None
        tribe = None
        if shifter_type == 'mokole':
            varna = character.get_stat('identity', 'lineage', 'Varna', temp=False)
        elif shifter_type == 'bastet':
            tribe = character.get_stat('identity', 'lineage', 'Tribe', temp=False)
            tribe = tribe.lower() if tribe else 'simba'  # Default to Simba if no tribe set

        def format_stat_modifier(stat, mod, form_name):
            """Format a stat modifier, showing explicit 0 for Appearance in Crinos form and absolute values for Crawlerling form."""
            # Handle Crawlerling form's absolute values
            if form_name.lower() == 'crawlerling':
                if stat == 'Dexterity':
                    return f"{stat} +5"  # Show modifier
                elif stat in ['Strength', 'Stamina', 'Manipulation']:
                    return f"{stat} 0"  # Show absolute value
            # Handle Crinos form's Appearance
            elif stat == 'Appearance' and form_name.lower() == 'crinos':
                return f"{stat} 0"  # Show explicit 0 for Appearance in Crinos form
            elif mod != 0:
                return f"{stat} {mod:+d}"  # Show +/- for non-zero modifiers
            return None  # Return None for unmodified stats or 0 modifiers

        for form in available_forms:
            if form.name.lower() != 'homid':
                # Special handling for Mokolé Suchid form
                if (shifter_type == 'mokole' and 
                    form.name.lower() == 'suchid' and 
                    varna):
                    # Parse the description to get Varna-specific modifiers
                    varna_modifiers = {}
                    current_varna = None
                    for line in form.description.split('\n'):
                        line = line.strip()
                        if ':' in line and 'Varna-specific modifiers' not in line:
                            if line.endswith(':'):  # This is a Varna name
                                current_varna = line.rstrip(':')
                                varna_modifiers[current_varna] = {}
                            elif current_varna and line:  # This is a stat modifier
                                stat, mod_str = line.split(':')
                                stat = stat.strip()
                                try:
                                    mod = int(mod_str.strip())
                                except (ValueError, TypeError):
                                    mod = 0
                                varna_modifiers[current_varna][stat] = mod
                    
                    # Use Varna-specific modifiers if available
                    if varna in varna_modifiers:
                        mods = [format_stat_modifier(stat, mod, form.name) for stat, mod in varna_modifiers[varna].items()]
                        mods = [m for m in mods if m is not None]  # Filter out None values
                        table.add_row(f"{form.name} ({varna})", ", ".join(mods), str(form.difficulty))
                    else:
                        # Use default (Makara) stats
                        mods = [format_stat_modifier(stat, mod, form.name) for stat, mod in form.stat_modifiers.items()]
                        mods = [m for m in mods if m is not None]  # Filter out None values
                        table.add_row(f"{form.name} (Default)", ", ".join(mods), str(form.difficulty))
                # Special handling for Bastet forms
                elif shifter_type == 'bastet' and tribe:
                    # Get tribe-specific modifiers from the _get_form_modifiers method
                    tribe_modifiers = self._get_form_modifiers(form, shifter_type, None, tribe)
                    if tribe_modifiers:
                        mods = [format_stat_modifier(stat, mod, form.name) for stat, mod in tribe_modifiers.items()]
                        mods = [m for m in mods if m is not None]  # Filter out None values
                        table.add_row(f"{form.name} ({tribe.title()})", ", ".join(mods), str(form.difficulty))
                    else:
                        # Use default (Simba) stats if no tribe-specific modifiers found
                        mods = [format_stat_modifier(stat, mod, form.name) for stat, mod in form.stat_modifiers.items()]
                        mods = [m for m in mods if m is not None]  # Filter out None values
                        table.add_row(f"{form.name} (Default)", ", ".join(mods), str(form.difficulty))
                elif form.name.lower() == 'crawlerling':
                    # Show Crawlerling's special stats
                    mods = [
                        "Strength 0",
                        "Dexterity +5",
                        "Stamina 0",
                        "Manipulation 0"
                    ]
                    table.add_row(form.name, ", ".join(mods), str(form.difficulty))
                else:
                    # For non-Suchid forms or non-Mokolé characters
                    mods = [format_stat_modifier(stat, mod, form.name) for stat, mod in form.stat_modifiers.items()]
                    mods = [m for m in mods if m is not None]  # Filter out None values
                    table.add_row(form.name, ", ".join(mods), str(form.difficulty))
        
        if not available_forms and not homid_form:
            self.caller.msg(f"No forms found for shifter type: {shifter_type}")
            return
            
        self.caller.msg(table)

    def _reset_stats(self, character):
        """Reset all stats to their permanent values."""
        for category, subcats in character.db.stats.items():
            if isinstance(subcats, dict):
                for subcat, stats in subcats.items():
                    if isinstance(stats, dict):
                        for stat, values in stats.items():
                            if isinstance(values, dict) and 'perm' in values:
                                # Reset temp to match perm
                                perm_value = values['perm']
                                character.db.stats[category][subcat][stat] = {
                                    'perm': perm_value,
                                    'temp': perm_value
                                }
                                print(f"DEBUG: Reset {category}.{subcat}.{stat} to perm={perm_value}, temp={perm_value}")

    def _shift_with_roll(self, character, form):
        """Attempt to shift using a dice roll."""
        # Check for Metamorph merit first
        has_metamorph = character.db.stats.get('merits', {}).get('physical', {}).get('Metamorph', {}).get('perm', 0) > 0
        if has_metamorph:
            self.caller.msg(f"Your Metamorph merit allows you to shift effortlessly into {form.name} form.")
            return True

        # Get Primal-Urge value
        primal_urge = character.get_stat('abilities', 'talent', 'Primal-Urge', temp=False) or 0
        
        # Get Stamina value directly from stats dictionary
        stamina = character.db.stats.get('attributes', {}).get('physical', {}).get('Stamina', {}).get('perm', 0)
        
        dice_pool = primal_urge + stamina
        difficulty = form.difficulty
        
        rolls, successes, ones = roll_dice(dice_pool, difficulty)
        
        self.caller.msg(f"Rolling {dice_pool} dice (Primal-Urge {primal_urge} + Stamina {stamina}) against difficulty {difficulty}.")
        self.caller.msg(f"Roll result: {interpret_roll_results(successes, ones, difficulty, rolls)}")
        
        # A botch is indicated by successes being -1
        if successes < 0:
            self.caller.msg(f"Failure. You are unable to shift into {form.name} form.")
            return False
        elif successes > 0:
            self.caller.msg(f"Success! You shift into {form.name} form.")
            self._reset_stats(character)  # Reset stats before applying new form
            return True
        else:
            self.caller.msg(f"Failure. You are unable to shift into {form.name} form.")
            return False

    def _shift_with_rage(self, character, form):
        current_rage = character.db.stats.get('pools', {}).get('dual', {}).get('Rage', {}).get('temp', 0)
        if current_rage >= 1:
            # Spend 1 Rage point for automatic shift
            character.db.stats['pools']['dual']['Rage']['temp'] = current_rage - 1
            self.caller.msg(f"You spend a point of Rage to force the change into {form.name} form. (Remaining Rage: {current_rage - 1})")
            return True
        else:
            self.caller.msg("You don't have any Rage points to spend for an automatic shift.")
            return False

    def _shift_default(self, character, form):
        """Handle default shifting, with automatic success for natural form or Metamorph merit."""
        # First check for Metamorph merit
        has_metamorph = character.db.stats.get('merits', {}).get('physical', {}).get('Metamorph', {}).get('perm', 0) > 0
        if has_metamorph:
            self.caller.msg(f"Your Metamorph merit allows you to shift effortlessly into {form.name} form.")
            return True

        # Get character's breed and shifter type
        breed = character.get_stat('identity', 'lineage', 'Breed', temp=False)
        shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
        
        if not breed or not shifter_type:
            return self._shift_with_roll(character, form)
        
        breed = breed.lower()
        shifter_type = shifter_type.lower()
        form_name = form.name.lower()
        
        # Define natural forms for different breeds
        HOMID_BREEDS = {
            'homid',      # Generic
            'balaram',    # Nagah
            'kojin'       # Kitsune
        }
        
        ANIMAL_BREEDS = {
            ('garou', 'lupus'): 'lupus',
            ('ratkin', 'animal-born'): 'rodens',
            ('ajaba', 'animal-born'): 'hyaenid',
            ('ananasi', 'animal-born'): 'crawlerling',
            ('rokea', 'animal-born'): 'squamus',
            ('mokole', 'animal-born'): 'suchid',
            ('gurahl', 'animal-born'): 'ursine',
            ('bastet', 'animal-born'): 'feline',
            ('corax', 'animal-born'): 'corvid',
            ('kitsune', 'animal-born'): 'roko',
            ('nuwisha', 'animal-born'): 'latrani',
            ('nagah', 'vasuki'): 'vasuki'
        }
        
        METIS_BREEDS = {
            ('garou', 'metis'): 'crinos',
            ('ajaba', 'metis'): 'anthros',
            ('bastet', 'metis'): 'chatro',
            ('kitsune', 'shinju'): 'kitsune',
            ('nagah', 'ahi'): 'nagah',
            ('ratkin', 'metis'): 'crinos'
        }
        
        # Check if shifting to natural form based on breed
        if breed in HOMID_BREEDS and form_name == 'homid':
            self.caller.msg(f"You easily shift back to your natural Homid form.")
            return True
        
        # Check animal-born natural forms
        if (shifter_type, breed) in ANIMAL_BREEDS and form_name == ANIMAL_BREEDS[(shifter_type, breed)]:
            self.caller.msg(f"You easily shift back to your natural {form.name} form.")
            return True
        
        # Check metis natural forms
        if (shifter_type, breed) in METIS_BREEDS and form_name == METIS_BREEDS[(shifter_type, breed)]:
            self.caller.msg(f"You easily shift back to your natural {form.name} form.")
            return True
        
        # If not shifting to natural form, use the roll method
        return self._shift_with_roll(character, form)

    def _apply_form_changes(self, character, form):
        """Apply form changes and preserve abilities."""
        # Initialize attribute_boosts if it doesn't exist
        if not hasattr(character.db, 'attribute_boosts'):
            character.db.attribute_boosts = {}
        elif character.db.attribute_boosts is None:
            character.db.attribute_boosts = {}

        # If it's Homid form, reset everything to base stats but preserve boosts
        if form.name.lower() == 'homid':
            print(f"DEBUG: Setting Homid form for {character.name}")
            character.attributes.add('current_form', 'Homid')
            character.db.current_form = 'Homid'
            character.db.display_name = character.key
            
            # Get existing boosts
            attribute_boosts = character.db.attribute_boosts or {}

            # Reset all attributes to their permanent values
            for category in ['physical', 'social', 'mental']:
                if category in character.db.stats.get('attributes', {}):
                    for stat, values in character.db.stats['attributes'][category].items():
                        perm_value = values.get('perm', 0)
                        # Ensure value is an integer
                        if isinstance(perm_value, str):
                            try:
                                perm_value = int(perm_value)
                            except (ValueError, TypeError):
                                perm_value = 0
                        
                        # Apply any existing boosts
                        boost_amount = 0
                        if stat in attribute_boosts:
                            boost_amount = attribute_boosts[stat].get('amount', 0)
                        
                        character.db.stats['attributes'][category][stat] = {
                            'perm': perm_value,
                            'temp': perm_value + boost_amount
                        }
                        print(f"DEBUG: Reset {category}.{stat} to perm={perm_value}, temp={perm_value + boost_amount}")
            return

        # For non-Homid forms
        character.attributes.add('current_form', form.name)
        character.db.current_form = form.name
        character.db.display_name = form.name

        # Get all permanent values first
        permanent_values = {}
        for category in ['physical', 'social', 'mental']:
            if category in character.db.stats.get('attributes', {}):
                permanent_values[category] = {}
                for stat, values in character.db.stats['attributes'][category].items():
                    perm_value = values.get('perm', 0)
                    # Ensure value is an integer
                    if isinstance(perm_value, str):
                        try:
                            perm_value = int(perm_value)
                        except (ValueError, TypeError):
                            perm_value = 0
                    permanent_values[category][stat] = perm_value

        # Get character's breed and tribe/type
        breed = character.get_stat('identity', 'lineage', 'Breed', temp=False)
        tribe = character.get_stat('identity', 'lineage', 'Tribe', temp=False)
        shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)

        # Get the appropriate stat modifiers based on breed/tribe
        stat_modifiers = self._get_form_modifiers(form, shifter_type, breed, tribe)

        # Get existing boosts (with proper initialization)
        attribute_boosts = character.db.attribute_boosts or {}

        # Apply form modifiers while preserving permanent values and considering boosts
        for stat, mod in stat_modifiers.items():
            try:
                stat_obj = Stat.objects.get(name__iexact=stat, category='attributes')
                if stat_obj.category and stat_obj.stat_type:
                    # Get permanent value from our saved values
                    perm_value = permanent_values.get(stat_obj.stat_type, {}).get(stat_obj.name, 0)
                    
                    # Get any existing boost (with safe access)
                    boost_amount = 0
                    if stat_obj.name in attribute_boosts:
                        boost_amount = attribute_boosts[stat_obj.name].get('amount', 0)
                    
                    # Calculate temporary value based on permanent value, form modifier, and boost
                    temp_value = max(0, perm_value + mod + boost_amount)
                    
                    # Ensure the category and subcategory exist
                    if stat_obj.category not in character.db.stats:
                        character.db.stats[stat_obj.category] = {}
                    if stat_obj.stat_type not in character.db.stats[stat_obj.category]:
                        character.db.stats[stat_obj.category][stat_obj.stat_type] = {}
                    
                    # Set both permanent and temporary values
                    character.db.stats[stat_obj.category][stat_obj.stat_type][stat_obj.name] = {
                        'perm': perm_value,
                        'temp': temp_value
                    }
            except Stat.DoesNotExist:
                continue

        # Handle special cases for different forms
        if form.name.lower() == 'crinos':
            # Get the permanent Appearance value
            appearance_perm = permanent_values.get('social', {}).get('Appearance', 0)
            
            # Ensure the social subcategory exists
            if 'social' not in character.db.stats['attributes']:
                character.db.stats['attributes']['social'] = {}
            
            # Set Appearance to 0 only in Crinos form
            character.db.stats['attributes']['social']['Appearance'] = {
                'perm': appearance_perm,
                'temp': 0
            }
            
            # Handle Manipulation in Crinos form
            manip_perm = permanent_values.get('social', {}).get('Manipulation', 0)
            manip_boost = 0
            if 'Manipulation' in attribute_boosts:
                manip_boost = attribute_boosts['Manipulation'].get('amount', 0)
            
            character.db.stats['attributes']['social']['Manipulation'] = {
                'perm': manip_perm,
                'temp': max(0, manip_perm - 2 + manip_boost)  # -2 penalty in Crinos plus any boost
            }
        elif form.name.lower() == 'crawlerling':
            # Handle Crawlerling form's special stats
            # Set Strength, Stamina, and Manipulation to 0
            # Set Dexterity to base + 5
            
            # Get permanent values and boosts
            str_perm = permanent_values.get('physical', {}).get('Strength', 0)
            dex_perm = permanent_values.get('physical', {}).get('Dexterity', 0)
            sta_perm = permanent_values.get('physical', {}).get('Stamina', 0)
            man_perm = permanent_values.get('social', {}).get('Manipulation', 0)
            
            str_boost = attribute_boosts.get('Strength', {}).get('amount', 0)
            dex_boost = attribute_boosts.get('Dexterity', {}).get('amount', 0)
            sta_boost = attribute_boosts.get('Stamina', {}).get('amount', 0)
            man_boost = attribute_boosts.get('Manipulation', {}).get('amount', 0)
            
            # Ensure categories exist
            if 'physical' not in character.db.stats['attributes']:
                character.db.stats['attributes']['physical'] = {}
            if 'social' not in character.db.stats['attributes']:
                character.db.stats['attributes']['social'] = {}
            
            # Set the stats
            character.db.stats['attributes']['physical']['Strength'] = {
                'perm': str_perm,
                'temp': 0 + str_boost  # Allow boosts to still apply
            }
            character.db.stats['attributes']['physical']['Dexterity'] = {
                'perm': dex_perm,
                'temp': dex_perm + 5 + dex_boost  # Add 5 to base Dexterity plus any boost
            }
            character.db.stats['attributes']['physical']['Stamina'] = {
                'perm': sta_perm,
                'temp': 0 + sta_boost  # Allow boosts to still apply
            }
            character.db.stats['attributes']['social']['Manipulation'] = {
                'perm': man_perm,
                'temp': 0 + man_boost  # Allow boosts to still apply
            }

        # Handle Mokolé Archid traits if applicable
        if form.name.lower() == 'archid' and character.get_stat('identity', 'lineage', 'Type', temp=False).lower() == 'mokole':
            try:
                from world.wod20th.models import CharacterArchidTrait
                
                # Get all approved Archid traits for the character
                archid_traits = CharacterArchidTrait.objects.filter(
                    character=character,
                    approved=True
                )
                
                # Apply trait modifiers
                for char_trait in archid_traits:
                    trait = char_trait.trait
                    # Apply stat modifiers, multiplied by count for stackable traits
                    for stat, mod in trait.stat_modifiers.items():
                        if isinstance(mod, str):
                            try:
                                mod = int(mod)
                            except (ValueError, TypeError):
                                mod = 0
                        total_mod = mod * char_trait.count
                        
                        # Find the category and type for this stat
                        try:
                            stat_obj = Stat.objects.get(name__iexact=stat)
                            if stat_obj.category and stat_obj.stat_type:
                                current_value = character.db.stats.get(stat_obj.category, {}).get(stat_obj.stat_type, {}).get(stat_obj.name, {})
                                if isinstance(current_value, dict) and 'temp' in current_value:
                                    temp = current_value['temp']
                                    if isinstance(temp, str):
                                        try:
                                            temp = int(temp)
                                        except (ValueError, TypeError):
                                            temp = 0
                                    new_temp = max(0, temp + total_mod)
                                    character.db.stats[stat_obj.category][stat_obj.stat_type][stat_obj.name]['temp'] = new_temp
                        except Stat.DoesNotExist:
                            continue
                    
                    # Store special rules in character's attributes for reference
                    if trait.special_rules:
                        if not hasattr(character.db, 'archid_special_rules'):
                            character.db.archid_special_rules = []
                        character.db.archid_special_rules.append(
                            f"{trait.name}: {trait.special_rules}"
                        )
                
            except ImportError:
                pass  # If the models aren't available, skip Archid trait application

    def _display_shift_message(self, character, form):
        """Display the appropriate shift message."""
        # Get the custom message for this form if it exists
        custom_message = character.attributes.get(f"shift_message_{form.name.lower()}")
        
        if custom_message:
            # Replace placeholders in custom message
            message = custom_message.format(
                truename=character.key,
                deedname=character.db.deed_name or character.key,
                formname=self._get_form_name(character, form)
            )
            self.caller.location.msg_contents(message)
        else:
            # Default message if no custom message exists
            self.caller.location.msg_contents(
                f"{character.key} shifts into {form.name} form."
            )

        # Update only the persistent attributes
        character.db.current_form = form.name
        if form.name.lower() == 'homid':
            character.db.display_name = character.db.original_name
        else:
            character.db.display_name = form.name

        # Add the original name as an alias if it's not already there
        if character.db.original_name not in character.aliases.all():
            character.aliases.add(character.db.original_name)

    def _get_player_custom_message(self, character, form):
        return character.attributes.get(f"shift_message_{form.name.lower()}", None)

    def _set_custom_message(self, character):
        if "=" not in self.args:
            self.caller.msg("Usage: +shift/message <form name> = <your custom message>")
            return

        form_name, message = self.args.split("=", 1)
        form_name = form_name.strip()
        message = message.strip()

        # Get the character's shifter type
        shifter_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '').lower()

        try:
            # Filter by both form name and shifter type
            form = ShapeshifterForm.objects.get(
                name__iexact=form_name,
                shifter_type=shifter_type
            )
        except ShapeshifterForm.DoesNotExist:
            self.caller.msg(f"The form '{form_name}' does not exist for your shifter type.")
            return
        except ShapeshifterForm.MultipleObjectsReturned:
            self.caller.msg(f"Error: Multiple forms found with name '{form_name}'. Please contact an admin.")
            return

        character.attributes.add(f"shift_message_{form_name.lower()}", message)
        self.caller.msg(f"Your personal shift message set for {form_name} form.")

    def _set_deed_name(self, character):
        deed_name = self.args.strip()
        if not deed_name:
            self.caller.msg("Usage: +shift/setdeedname <deed name>")
            return

        character.db.deed_name = deed_name
        self.caller.msg(f"Your deed name has been set to: {deed_name}")

    def _set_form_name(self, character):
        if "=" not in self.args:
            self.caller.msg("Usage: +shift/setformname <form name> = <form-specific name>")
            return

        form_name, form_specific_name = self.args.split("=", 1)
        form_name = form_name.strip()
        form_specific_name = form_specific_name.strip()

        try:
            form = ShapeshifterForm.objects.get(name__iexact=form_name)
        except ShapeshifterForm.DoesNotExist:
            self.caller.msg(f"The form '{form_name}' does not exist.")
            return

        character.attributes.add(f"form_name_{form_name.lower()}", form_specific_name)
        self.caller.msg(f"Your name for {form_name} form set to: {form_specific_name}")

        # Update display_name if the character is currently in this form
        if character.db.current_form and character.db.current_form.lower() == form_name.lower():
            character.db.display_name = form_specific_name

    def _set_form_name_with_shift(self, character):
        if "=" not in self.args:
            self.caller.msg("Usage: +shift/name <form name> = <new name>")
            return

        form_name, new_name = self.args.split("=", 1)
        form_name = form_name.strip()
        new_name = new_name.strip()

        try:
            form = ShapeshifterForm.objects.get(name__iexact=form_name)
        except ShapeshifterForm.DoesNotExist:
            self.caller.msg(f"The form '{form_name}' does not exist.")
            return

        character.attributes.add(f"form_name_{form_name.lower()}", new_name)
        self.caller.msg(f"Your name for {form_name} form set to: {new_name}")

        # Perform the shift
        success = self._shift_default(character, form)
        if success:
            self._apply_form_changes(character, form)
            self._display_shift_message(character, form)

    def _get_form_name(self, character, form):
        if form.name.lower() == 'homid':
            return character.db.original_name or character.db.gradient_name or character.key
        return character.attributes.get(f"form_name_{form.name.lower()}", character.db.deed_name or character.db.gradient_name or character.key)

    def _get_form_modifiers(self, form, shifter_type, breed, tribe):
        """Get the appropriate stat modifiers based on breed/tribe."""
        form_name = form.name.lower()
        shifter_type = shifter_type.lower() if shifter_type else ''
        breed = breed.lower() if breed else ''
        tribe = tribe.lower() if tribe else ''

        # Base modifiers from the form
        modifiers = dict(form.stat_modifiers)

        # Special handling for Bastet tribes
        if shifter_type == 'bastet' and tribe:
            bastet_modifiers = {
                'bagheera': {
                    'sokto': {'Strength': 1, 'Dexterity': 1, 'Stamina': 2, 'Manipulation': -1, 'Appearance': -1},
                    'crinos': {'Strength': 3, 'Dexterity': 3, 'Stamina': 3, 'Manipulation': -3, 'Appearance': 0},
                    'chatro': {'Strength': 2, 'Dexterity': 3, 'Stamina': 3, 'Manipulation': -3, 'Appearance': -2},
                    'feline': {'Strength': 1, 'Dexterity': 3, 'Stamina': 2, 'Manipulation': -3}
                },
                'balam': {
                    'sokto': {'Strength': 2, 'Dexterity': 1, 'Stamina': 2, 'Manipulation': -1, 'Appearance': -1},
                    'crinos': {'Strength': 3, 'Dexterity': 3, 'Stamina': 3, 'Manipulation': -4, 'Appearance': 0},
                    'chatro': {'Strength': 3, 'Dexterity': 2, 'Stamina': 3, 'Manipulation': -4, 'Appearance': 0},
                    'feline': {'Strength': 2, 'Dexterity': 3, 'Stamina': 2, 'Manipulation': -3}
                },
                'bubasti': {
                    'sokto': {'Strength': 0, 'Dexterity': 1, 'Stamina': 0, 'Manipulation': 0, 'Appearance': 1},
                    'crinos': {'Strength': 1, 'Dexterity': 3, 'Stamina': 1, 'Manipulation': -2, 'Appearance': -3},
                    'chatro': {'Strength': 2, 'Dexterity': 4, 'Stamina': 1, 'Manipulation': -2, 'Appearance': 0},
                    'feline': {'Strength': -1, 'Dexterity': 4, 'Stamina': 1, 'Manipulation': 0}
                },
                'ceilican': {
                    'sokto': {'Strength': 0, 'Dexterity': 2, 'Stamina': 1, 'Manipulation': 0, 'Appearance': 1},
                    'crinos': {'Strength': 1, 'Dexterity': 3, 'Stamina': 1, 'Manipulation': 0, 'Appearance': -2},
                    'chatro': {'Strength': 0, 'Dexterity': 4, 'Stamina': 1, 'Manipulation': -2, 'Appearance': -2},
                    'feline': {'Strength': -1, 'Dexterity': 4, 'Stamina': 0, 'Manipulation': -2}
                },
                'khan': {
                    'sokto': {'Strength': 2, 'Dexterity': 1, 'Stamina': 2, 'Manipulation': -1, 'Appearance': -1},
                    'crinos': {'Strength': 5, 'Dexterity': 2, 'Stamina': 3, 'Manipulation': -3, 'Appearance': 0},
                    'chatro': {'Strength': 4, 'Dexterity': 2, 'Stamina': 3, 'Manipulation': -3, 'Appearance': 0},
                    'feline': {'Strength': 3, 'Dexterity': 2, 'Stamina': 3, 'Manipulation': -3}
                },
                'pumonca': {
                    'sokto': {'Strength': 1, 'Dexterity': 2, 'Stamina': 2, 'Manipulation': -1, 'Appearance': 0},
                    'crinos': {'Strength': 3, 'Dexterity': 3, 'Stamina': 4, 'Manipulation': -3, 'Appearance': 0},
                    'chatro': {'Strength': 3, 'Dexterity': 3, 'Stamina': 3, 'Manipulation': -3, 'Appearance': 0},
                    'feline': {'Strength': 2, 'Dexterity': 3, 'Stamina': 3, 'Manipulation': 0}
                },
                'qualmi': {
                    'sokto': {'Strength': 0, 'Dexterity': 2, 'Stamina': 0, 'Manipulation': 0, 'Appearance': 1},
                    'crinos': {'Strength': 1, 'Dexterity': 3, 'Stamina': 1, 'Manipulation': -2, 'Appearance': 0},
                    'chatro': {'Strength': 1, 'Dexterity': 4, 'Stamina': 1, 'Manipulation': -2, 'Appearance': 0},
                    'feline': {'Strength': 0, 'Dexterity': 4, 'Stamina': 0, 'Manipulation': -2}
                },
                'simba': {
                    'sokto': {'Strength': 2, 'Dexterity': 1, 'Stamina': 2, 'Manipulation': -1, 'Appearance': 1},
                    'crinos': {'Strength': 4, 'Dexterity': 2, 'Stamina': 3, 'Manipulation': -2, 'Appearance': 0},
                    'chatro': {'Strength': 3, 'Dexterity': 4, 'Stamina': 2, 'Manipulation': -2, 'Appearance': 0},
                    'feline': {'Strength': 3, 'Dexterity': 3, 'Stamina': 2, 'Manipulation': -1}
                },
                'swara': {
                    'sokto': {'Strength': 1, 'Dexterity': 2, 'Stamina': 1, 'Manipulation': -1, 'Appearance': 0},
                    'crinos': {'Strength': 2, 'Dexterity': 4, 'Stamina': 3, 'Manipulation': -3, 'Appearance': 0},
                    'chatro': {'Strength': 2, 'Dexterity': 4, 'Stamina': 3, 'Manipulation': -3, 'Appearance': 0},
                    'feline': {'Strength': 1, 'Dexterity': 4, 'Stamina': 2, 'Manipulation': -3}
                }
            }

            if tribe in bastet_modifiers and form_name in bastet_modifiers[tribe]:
                return bastet_modifiers[tribe][form_name]

        # Special handling for Mokolé Suchid form
        elif shifter_type == 'mokole' and form_name == 'suchid':
            varna = self.caller.get_stat('identity', 'lineage', 'Varna', temp=False)
            varna = varna.lower() if varna else 'makara'  # Default to Makara if no Varna set

            mokole_modifiers = {
                'champsa': {'Strength': 3, 'Dexterity': -2, 'Stamina': 3, 'Manipulation': -4},  # Nile crocodile
                'gharial': {'Strength': 1, 'Dexterity': -1, 'Stamina': 3, 'Manipulation': -4},  # Gavails
                'halpatee': {'Strength': 2, 'Dexterity': -1, 'Stamina': 3, 'Manipulation': -2},  # American alligator
                'karna': {'Strength': 3, 'Dexterity': -2, 'Stamina': 3, 'Manipulation': -4},  # Saltwater Crocodile
                'makara': {'Strength': 1, 'Dexterity': 0, 'Stamina': 2, 'Manipulation': -3},  # Mugger crocodile
                'ora': {'Strength': 0, 'Dexterity': 0, 'Stamina': 2, 'Manipulation': -4},  # Monitor lizards
                'piasa': {'Strength': 2, 'Dexterity': -1, 'Stamina': 3, 'Manipulation': -2},  # American crocodile
                'syrta': {'Strength': 1, 'Dexterity': -1, 'Stamina': 3, 'Manipulation': -4},  # Caimans
                'unktehi': {'Strength': -1, 'Dexterity': 0, 'Stamina': 1, 'Manipulation': -3}  # Gila monster
            }

            if varna in mokole_modifiers:
                self.caller.msg(f"|gUsing {varna.title()} form modifiers.|n")
                return mokole_modifiers[varna]
            else:
                self.caller.msg(f"|rWarning: Unknown Varna '{varna}', using default Makara stats.|n")
                return mokole_modifiers['makara']

        # For all other shifter types, use the base form modifiers
        from world.wod20th.forms import forms_data
        if shifter_type in forms_data and form_name in forms_data[shifter_type]:
            form_data = forms_data[shifter_type][form_name]
            if isinstance(form_data, dict) and 'stat_modifiers' in form_data:
                return form_data['stat_modifiers']

        return modifiers
