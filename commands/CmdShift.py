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
    successes = max(0, successes - ones)  # Ensure successes don't go negative
    return rolls, successes, ones

def interpret_roll_results(successes, ones, diff=6, rolls=None):
    success_string = f"|g{successes}|n" if successes > 0 else f"|y{successes}|n" if successes == 0 else f"|r{successes}|n"
    
    msg = f"|w(|n{success_string}|w)|n"
    msg += f"|r Botch!|n" if successes == 0 and ones > 0 else "|y Successes|n" if successes != 1 else "|y Success|n"
    
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
    help_category = "Shapeshifting"

    def func(self):
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
            form = ShapeshifterForm.objects.get(name__iexact=form_name)
        except ShapeshifterForm.DoesNotExist:
            self.caller.msg(f"The form '{form_name}' does not exist.")
            return

        if form.lock_string and not form.access(character, "use"):
            self.caller.msg(f"You don't have permission to use the {form_name} form.")
            return

        self._reset_stats(character)

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
        available_forms = ShapeshifterForm.objects.filter(lock_string="").order_by('name')
        
        if character.locks.check_lockstring(character, "admin:perm(Admin)"):
            available_forms = ShapeshifterForm.objects.all().order_by('name')

        


    def _reset_stats(self, character):
        # Reset all stats that can be modified by shapeshifting
        stats_to_reset = ['strength', 'dexterity', 'stamina', 'charisma', 'manipulation', 'appearance', 'perception', 'intelligence', 'wits']
        for stat in stats_to_reset:
           stat_obj = Stat.objects.get(name__iexact=stat, category='attributes')
           if stat_obj.category and stat_obj.stat_type:
               curr_stat = character.get_stat(stat_obj.category, stat_obj.stat_type, stat_obj.name)
               character.set_stat(stat_obj.category, stat_obj.stat_type, stat_obj.name, curr_stat, temp=True)

    def _shift_with_roll(self, character, form):
        # Use the character's Primal-Urge (or equivalent) + relevant Attribute for the dice pool
        primal_urge = character.db.stats['abilities'].get('talent', {}).get('Primal-Urge', {}).get('perm', 0)
        relevant_attribute = character.db.stats['attributes'].get('physical', {}).get('Stamina', {}).get('perm', 1)
        dice_pool = primal_urge + relevant_attribute
        difficulty = form.difficulty

        rolls, successes, ones = roll_dice(dice_pool, difficulty)
        result_msg = interpret_roll_results(successes, ones, difficulty, rolls)

        self.caller.msg(f"Attempting to shift into {form.name} form...")
        self.caller.msg(f"Rolling {dice_pool} dice (Primal-Urge {primal_urge} + Stamina {relevant_attribute}) against difficulty {difficulty}.")
        self.caller.msg(f"Roll result: {result_msg}")

        if successes > 0:
            self.caller.msg(f"Success! You shift into {form.name} form.")
            return True
        elif successes == 0 and ones > 0:
            self.caller.msg(f"Botch! Your attempt to shift goes horribly wrong!")
            # Implement botch consequences here
            return False
        else:
            self.caller.msg(f"Failure. You are unable to shift into {form.name} form.")
            return False

    def _shift_with_rage(self, character, form):
        current_rage = character.db.stats['other'].get('other', {}).get('Rage', {}).get('temp', 0)
        if current_rage >= form.rage_cost:
            character.db.stats['other']['other']['Rage']['temp'] = current_rage - form.rage_cost
            self.caller.msg(f"You spend {form.rage_cost} Rage to shift into {form.name} form. (Remaining Rage: {character.db.stats['other']['other']['Rage']['temp']})")
            return True
        else:
            self.caller.msg(f"You don't have enough Rage to shift into {form.name} form. (Required: {form.rage_cost}, Current: {current_rage})")
            return False

    def _shift_default(self, character, form):
        # Implement your default shift logic here
        # For now, we'll just make it always succeed
        self.caller.msg(f"You shift into {form.name} form.")
        return True

    def _apply_form_changes(self, character, form):
        # Apply stat modifiers
        if not form.stat_modifiers:
            # reset all attributes.
            self._reset_stats(character)
            return
        
        for stat, modifier in form.stat_modifiers.items():
            stat_obj = Stat.objects.get(name__iexact=stat)  # Get the Stat object for the stat name
            
            if not stat:
                self.caller.msg(f"Stat '{stat}' not found.")
                continue

            if stat_obj.category and stat_obj.stat_type:
                current_value = self.caller.get_stat(stat_obj.category, stat_obj.stat_type, stat_obj.name, default=1)
                new_value = int(current_value) + int(modifier)
                character.set_stat(stat_obj.category, stat_obj.stat_type, stat_obj.name, new_value, temp=True)
                text_val = f"|g{new_value}" if new_value >= 0 else f"|r{new_value}|n"
                self.caller.msg("|YSHIFT>|n" + format_stat(stat_obj.name, current_value) +  f" -> {text_val}")
              
            else:
                self.caller.msg(f"Stat '{stat}' not found.")

        # Set the current form
        character.db.current_form = form.name

    def _display_shift_message(self, character, form):
        player_message = self._get_player_custom_message(character, form)
        true_name = character.db.original_name or character.key
        deed_name = character.db.deed_name or "Unnamed"
        form_name = self._get_form_name(character, form)
           
        if player_message:
            message = player_message.format(truename=true_name, deedname=deed_name, formname=form_name, form=form.name)
        elif form.form_message:
            message = form.shift_message.format(truename=true_name, deedname=deed_name, formname=form_name, form=form.name)
        else:
            if form.name.lower() == 'homid':
                message = f"{true_name} shifts back to their |whuman|n form."
            else:
                message = f"{true_name} shifts into |w{form.name}|n form, now known as {form_name}."
    
        character.location.msg_contents(message, exclude=character)
        character.msg(f"You shift into |w{form.name}|n form, taking on the appearance of {form_name}.")

        # Change the character's visible name
        character.db.current_form = form.name
        if form.name.lower() == 'homid':
            character.db.display_name = character.db.original_name
        else:
            character.db.display_name = form_name

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

        try:
            form = ShapeshifterForm.objects.get(name__iexact=form_name)
        except ShapeshifterForm.DoesNotExist:
            self.caller.msg(f"The form '{form_name}' does not exist.")
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