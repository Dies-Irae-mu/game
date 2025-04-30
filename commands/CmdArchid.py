"""
Command for managing Mokolé Archid traits.
"""
from django.core.exceptions import ValidationError
from django.utils import timezone
from evennia import default_cmds
from evennia.utils import evtable
from world.wod20th.models import MokoleArchidTrait, CharacterArchidTrait

class CmdArchid(default_cmds.MuxCommand):
    """
    Manage Mokolé Archid form traits.

    Usage:
      +archid/list                - List all available Archid traits
      +archid/add <trait>         - Add a trait to your Archid form
      +archid/remove <trait>      - Remove a trait (requires approval if already approved)
      +archid/view                - View your current Archid traits
      +archid/describe <trait>    - Get detailed information about a trait
      +archid/approve <character>=<trait> - Approve a trait (Admin/ST only)
      +archid/staff/view <character> - View another character's Archid traits (Staff only)
      +archid/staff/add <character>=<trait> - Add trait to another character (Staff only)
      +archid/staff/remove <character>=<trait> - Remove trait from another character (Staff only)

    This command allows Mokolé characters to manage their Archid form traits.
    Each Mokolé can have a number of traits equal to their permanent Gnosis.
    Some traits can be taken multiple times for stacking effects.
    Traits cannot be removed once approved without staff permission.
    """

    key = "+archid"
    aliases = ["archid"]
    locks = "cmd:all()"
    help_category = "Shifter"

    def func(self):
        """
        Main function that processes the command input.
        """
        if not self.switches and not self.args:
            self.caller.msg("Usage: +archid/<switch> [arguments]")
            return
            
        # Debug output to help identify the issue
        debug_msg = f"Debug - Switches: {self.switches}, Args: {self.args}"
        self.caller.msg(debug_msg)

        # Process staff commands first
        if self.caller.check_permstring("builders"):
            # Check for compound switches like "staff/view"
            for switch in self.switches:
                if switch.startswith("staff/"):
                    action = switch.split("/")[1]
                    if action == "view":
                        self._staff_view_traits()
                        return
                    elif action == "add":
                        self._staff_add_trait()
                        return
                    elif action == "remove":
                        self._staff_remove_trait()
                        return
                    else:
                        self.caller.msg(f"Invalid staff action '{action}'. Valid options are: view, add, remove.")
                        return
            
            # Pure staff switch check (should be caught by above, but just in case)
            if "staff" in self.switches:
                if "view" in self.switches:
                    self._staff_view_traits()
                    return
                elif "add" in self.switches:
                    self._staff_add_trait()
                    return
                elif "remove" in self.switches:
                    self._staff_remove_trait()
                    return
                else:
                    self.caller.msg(f"Invalid staff switch. Valid options are: view, add, remove. You used: {self.switches}")
                    return
                    
            # Process approve command for staff
            if "approve" in self.switches:
                self._approve_trait()
                return
        
        # For non-staff or non-staff commands, check if character is a Mokolé
        splat = self.caller.get_stat('other', 'splat', 'Splat', temp=False)
        shifter_type = self.caller.get_stat('identity', 'lineage', 'Type', temp=False)
        
        if splat.lower() != 'shifter' or shifter_type.lower() != 'mokole':
            self.caller.msg("Only Mokolé can use the +archid command.")
            return

        if "list" in self.switches or not self.switches:
            self._list_traits()
        elif "add" in self.switches:
            self._add_trait()
        elif "remove" in self.switches:
            self._remove_trait()
        elif "view" in self.switches:
            self._view_traits()
        elif "describe" in self.switches:
            self._describe_trait()
        else:
            self.caller.msg(f"Invalid switch. Use +help archid for valid switches. You used: {self.switches}")
            return

    def _list_traits(self):
        """List all available Archid traits."""
        traits = MokoleArchidTrait.objects.all().order_by('name')
        if not traits:
            self.caller.msg("No Archid traits found in database.")
            return

        # Get character's current traits
        character_traits = CharacterArchidTrait.objects.filter(character=self.caller)
        current_traits = {ct.trait.name: ct.count for ct in character_traits}
        
        # Get character's Gnosis
        gnosis = self.caller.get_stat('pools', 'dual', 'Gnosis', temp=False) or 0
        total_traits = sum(current_traits.values())

        table = evtable.EvTable(
            "|wTrait Name|n",
            "|wDescription|n",
            "|wStackable|n",
            "|wCurrent|n",
            border="header"
        )

        for trait in traits:
            stackable = "Yes" if trait.can_stack else "No"
            count = current_traits.get(trait.name, 0)
            table.add_row(
                trait.name,
                trait.description[:50] + "..." if len(trait.description) > 50 else trait.description,
                stackable,
                str(count) if count > 0 else "-"
            )

        self.caller.msg(f"|wGnosis:|n {gnosis}")
        self.caller.msg(f"|wTotal Traits:|n {total_traits}")
        self.caller.msg(f"|wAvailable Slots:|n {max(0, gnosis - total_traits)}")
        self.caller.msg(table)

    def _add_trait(self):
        """Add a trait to the character's Archid form."""
        if not self.args:
            self.caller.msg("Usage: +archid/add <trait name>")
            return

        trait_name = self.args.strip()
        try:
            trait = MokoleArchidTrait.objects.get(name__iexact=trait_name)
        except MokoleArchidTrait.DoesNotExist:
            self.caller.msg(f"Trait '{trait_name}' not found.")
            return

        try:
            # Check if character already has this trait
            char_trait, created = CharacterArchidTrait.objects.get_or_create(
                character=self.caller,
                trait=trait,
                defaults={'count': 1, 'approved': False}
            )

            if not created:
                if not trait.can_stack:
                    self.caller.msg(f"You already have the {trait.name} trait.")
                    return
                char_trait.count += 1
                try:
                    char_trait.save()
                except ValidationError as e:
                    self.caller.msg(str(e))
                    return

            self.caller.msg(f"Added {trait.name} to your Archid form traits. Awaiting staff approval.")

        except ValidationError as e:
            self.caller.msg(str(e))

    def _remove_trait(self):
        """Request removal of a trait."""
        if not self.args:
            self.caller.msg("Usage: +archid/remove <trait name>")
            return

        trait_name = self.args.strip()
        try:
            char_trait = CharacterArchidTrait.objects.get(
                character=self.caller,
                trait__name__iexact=trait_name
            )

            if char_trait.approved:
                self.caller.msg("Cannot remove approved traits without staff permission.")
                return

            char_trait.delete()
            self.caller.msg(f"Removed {trait_name} from your Archid form traits.")

        except CharacterArchidTrait.DoesNotExist:
            self.caller.msg(f"You don't have the {trait_name} trait.")

    def _view_traits(self):
        """View character's current Archid traits."""
        traits = CharacterArchidTrait.objects.filter(character=self.caller)
        if not traits:
            self.caller.msg("You have no Archid form traits.")
            return

        gnosis = self.caller.get_stat('pools', 'dual', 'Gnosis', temp=False) or 0
        total_traits = sum(t.count for t in traits)

        table = evtable.EvTable(
            "|wTrait|n",
            "|wCount|n",
            "|wApproved|n",
            "|wDescription|n",
            border="header"
        )

        for trait in traits:
            table.add_row(
                trait.trait.name,
                str(trait.count),
                "Yes" if trait.approved else "No",
                trait.trait.description[:50] + "..." if len(trait.trait.description) > 50 else trait.trait.description
            )

        self.caller.msg(f"|wGnosis:|n {gnosis}")
        self.caller.msg(f"|wTotal Traits:|n {total_traits}")
        self.caller.msg(f"|wAvailable Slots:|n {max(0, gnosis - total_traits)}")
        self.caller.msg(table)

    def _staff_view_traits(self):
        """View another character's Archid traits (Staff only)."""
        if not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to view other characters' traits.")
            return

        if not self.args:
            self.caller.msg("Usage: +archid/staff/view <character name>")
            return

        # Debug who we're trying to look up
        self.caller.msg(f"Debug: Searching for character '{self.args.strip()}'")
            
        # Search for the character 
        character = self.caller.search(self.args.strip(), global_search=True)
        if not character:
            self.caller.msg(f"Character '{self.args.strip()}' not found.")
            return
            
        # Debug who we found
        self.caller.msg(f"Debug: Found character {character.name} (#{character.id})")
        
        # Check if character is a Mokolé
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
        
        # Debug character type
        self.caller.msg(f"Debug: Character splat={splat}, type={shifter_type}")
        
        if splat.lower() != 'shifter' or shifter_type.lower() != 'mokole':
            self.caller.msg(f"{character.name} is not a Mokolé and cannot have Archid traits.")
            return

        traits = CharacterArchidTrait.objects.filter(character=character)
        if not traits:
            self.caller.msg(f"{character.name} has no Archid form traits.")
            return

        gnosis = character.get_stat('pools', 'dual', 'Gnosis', temp=False) or 0
        total_traits = sum(t.count for t in traits)

        table = evtable.EvTable(
            "|wTrait|n",
            "|wCount|n",
            "|wApproved|n",
            "|wDescription|n",
            border="header"
        )

        for trait in traits:
            approved_info = "Yes" if trait.approved else "No"
            if trait.approved and trait.approved_by:
                approved_info += f" (by {trait.approved_by})"
                
            table.add_row(
                trait.trait.name,
                str(trait.count),
                approved_info,
                trait.trait.description[:50] + "..." if len(trait.trait.description) > 50 else trait.trait.description
            )

        header = f"|wViewing Archid Traits for:|n {character.name}\n"
        header += f"|wGnosis:|n {gnosis}\n"
        header += f"|wTotal Traits:|n {total_traits}\n"
        header += f"|wAvailable Slots:|n {max(0, gnosis - total_traits)}"
        
        self.caller.msg(header)
        self.caller.msg(table)

    def _staff_add_trait(self):
        """Add a trait to another character's Archid form (Staff only)."""
        if not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to add traits to other characters.")
            return

        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +archid/staff/add <character>=<trait name>")
            return

        char_name, trait_name = self.args.split("=", 1)
        char_name = char_name.strip()
        trait_name = trait_name.strip()

        # Get the character with global search
        character = self.caller.search(char_name, global_search=True)
        if not character:
            return
            
        # Check if character is a Mokolé
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
        
        if splat.lower() != 'shifter' or shifter_type.lower() != 'mokole':
            self.caller.msg(f"{character.name} is not a Mokolé and cannot have Archid traits.")
            return

        # Get the trait
        try:
            trait = MokoleArchidTrait.objects.get(name__iexact=trait_name)
        except MokoleArchidTrait.DoesNotExist:
            self.caller.msg(f"Trait '{trait_name}' not found.")
            return

        try:
            # Check if character already has this trait
            char_trait, created = CharacterArchidTrait.objects.get_or_create(
                character=character,
                trait=trait,
                defaults={'count': 1, 'approved': True, 'approved_by': self.caller.account, 'approved_date': timezone.now()}
            )

            if not created:
                if not trait.can_stack:
                    self.caller.msg(f"{character.name} already has the {trait.name} trait.")
                    return
                char_trait.count += 1
                char_trait.save()

            self.caller.msg(f"Added and approved {trait.name} for {character.name}.")
            character.msg(f"Staff member {self.caller.name} has added and approved the {trait.name} trait to your Archid form.")

        except ValidationError as e:
            self.caller.msg(str(e))

    def _staff_remove_trait(self):
        """Remove a trait from another character's Archid form (Staff only)."""
        if not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to remove traits from other characters.")
            return

        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +archid/staff/remove <character>=<trait name>")
            return

        char_name, trait_name = self.args.split("=", 1)
        char_name = char_name.strip()
        trait_name = trait_name.strip()

        # Get the character with global search
        character = self.caller.search(char_name, global_search=True)
        if not character:
            return

        # Get the trait
        try:
            char_trait = CharacterArchidTrait.objects.get(
                character=character,
                trait__name__iexact=trait_name
            )
            
            # If it's stackable, reduce count instead of removing entirely
            if char_trait.trait.can_stack and char_trait.count > 1:
                char_trait.count -= 1
                char_trait.save()
                self.caller.msg(f"Reduced {trait_name} count for {character.name} to {char_trait.count}.")
                character.msg(f"Staff member {self.caller.name} has reduced your {trait_name} trait count to {char_trait.count}.")
            else:
                # Otherwise, delete the trait
                char_trait.delete()
                self.caller.msg(f"Removed {trait_name} from {character.name}'s Archid form traits.")
                character.msg(f"Staff member {self.caller.name} has removed the {trait_name} trait from your Archid form.")

        except CharacterArchidTrait.DoesNotExist:
            self.caller.msg(f"{character.name} doesn't have the {trait_name} trait.")

    def _describe_trait(self):
        """Get detailed information about a trait."""
        if not self.args:
            self.caller.msg("Usage: +archid/describe <trait name>")
            return

        trait_name = self.args.strip()
        try:
            trait = MokoleArchidTrait.objects.get(name__iexact=trait_name)
            
            msg = f"|wTrait:|n {trait.name}\n"
            msg += f"|wDescription:|n {trait.description}\n"
            msg += f"|wStackable:|n {'Yes' if trait.can_stack else 'No'}\n"
            
            if trait.stat_modifiers:
                msg += f"|wStat Modifiers:|n\n"
                for stat, mod in trait.stat_modifiers.items():
                    msg += f"  {stat}: {mod:+d}\n"
            
            if trait.special_rules:
                msg += f"|wSpecial Rules:|n {trait.special_rules}\n"

            self.caller.msg(msg)

        except MokoleArchidTrait.DoesNotExist:
            self.caller.msg(f"Trait '{trait_name}' not found.")

    def _approve_trait(self):
        """Approve a trait (Admin/ST only)."""
        if not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to approve traits.")
            return

        if "=" not in self.args:
            self.caller.msg("Usage: +archid/approve <character>=<trait>")
            return

        char_name, trait_name = self.args.split("=", 1)
        char_name = char_name.strip()
        trait_name = trait_name.strip()

        try:
            # Get the character with global search
            character = self.caller.search(char_name, global_search=True)
            if not character:
                return

            # Get the trait
            char_trait = CharacterArchidTrait.objects.get(
                character=character,
                trait__name__iexact=trait_name
            )

            char_trait.approved = True
            char_trait.approved_by = self.caller.account
            char_trait.approved_date = timezone.now()
            char_trait.save()

            self.caller.msg(f"Approved {trait_name} for {character.name}.")
            character.msg(f"Your {trait_name} trait has been approved by {self.caller.name}.")

        except CharacterArchidTrait.DoesNotExist:
            self.caller.msg(f"Trait '{trait_name}' not found for {char_name}.") 