# commands/oss/action_commands.py

from evennia import Command, search_object
from world.wod20th.models import Action, ActionTemplate, Asset

class CmdCreateActionTemplate(Command):
    """
    Create a new action template.

    Usage:
      +action/create <name> = <downtime_cost>, <requires_target>, <description>

    Example:
      +action/create Attack = 4, True, Attacking an enemy asset.
    """

    key = "+action/create"
    locks = "cmd:all()"
    help_category = "Actions"

    def func(self):
        try:
            name, details = self.args.split("=", 1)
            downtime_cost, requires_target, description = [item.strip() for item in details.split(",", 2)]
            action_template, created = ActionTemplate.objects.get_or_create(
                name=name.strip(),
                defaults={
                    'downtime_cost': int(downtime_cost),
                    'requires_target': requires_target.lower() in ['true', 'yes', '1'],
                    'description': description
                }
            )
            if created:
                self.caller.msg(f"Action Template '{action_template.name}' created successfully.")
            else:
                self.caller.msg(f"Action Template '{action_template.name}' already exists.")
        except ValueError:
            self.caller.msg("Invalid input. Please ensure downtime_cost is a number and requires_target is a boolean.")
        except Exception as e:
            self.caller.msg(f"Error creating action template: {e}")

class CmdReadActionTemplate(Command):
    """
    View details of an action template.

    Usage:
      +action/view <name>

    Example:
      +action/view Attack
    """

    key = "+action/view"
    locks = "cmd:all()"
    help_category = "Actions"

    def func(self):
        try:
            name = self.args.strip()
            template = ActionTemplate.objects.get(name__iexact=name)
            self.caller.msg(
                f"Action Template: {template.name}\n"
                f"Downtime Cost: {template.downtime_cost}\n"
                f"Requires Target: {template.requires_target}\n"
                f"Description: {template.description}"
            )
        except ActionTemplate.DoesNotExist:
            self.caller.msg("Action Template not found.")

class CmdUpdateActionTemplate(Command):
    """
    Update an action template.

    Usage:
      +action/update <name> = <field>, <value>

    Example:
      +action/update Attack = downtime_cost, 5
    """

    key = "+action/update"
    locks = "cmd:all()"
    help_category = "Actions"

    def func(self):
        try:
            name, updates = self.args.split("=", 1)
            field, value = [item.strip() for item in updates.split(",", 1)]
            template = ActionTemplate.objects.get(name__iexact=name.strip())

            if field == 'downtime_cost':
                value = int(value)
            elif field == 'requires_target':
                value = value.lower() in ['true', 'yes', '1']

            setattr(template, field, value)
            template.save()
            self.caller.msg(f"Action Template '{template.name}' updated successfully.")
        except ActionTemplate.DoesNotExist:
            self.caller.msg("Action Template not found.")
        except ValueError:
            self.caller.msg("Invalid input. Ensure that downtime_cost is a number and requires_target is a boolean.")
        except Exception as e:
            self.caller.msg(f"Error updating action template: {e}")

class CmdDeleteActionTemplate(Command):
    """
    Delete an action template.

    Usage:
      +action/delete <name>

    Example:
      +action/delete Attack
    """

    key = "+action/delete"
    locks = "cmd:all()"
    help_category = "Actions"

    def func(self):
        try:
            name = self.args.strip()
            template = ActionTemplate.objects.get(name__iexact=name)
            template.delete()
            self.caller.msg(f"Action Template '{template.name}' deleted successfully.")
        except ActionTemplate.DoesNotExist:
            self.caller.msg("Action Template not found.")

class CmdSearchActionTemplates(Command):
    """
    Search for action templates.

    Usage:
      +action/search <query>

    Example:
      +action/search Attack
    """

    key = "+action/search"
    locks = "cmd:all()"
    help_category = "Actions"

    def func(self):
        query = self.args.strip().lower()
        results = ActionTemplate.objects.filter(name__icontains=query)
        if results.exists():
            message = "Found the following action templates:\n"
            for template in results:
                message += f"{template.name} (Downtime Cost: {template.downtime_cost}, Requires Target: {template.requires_target})\n"
            self.caller.msg(message)
        else:
            self.caller.msg("No action templates found matching your query.")

class CmdListActionTemplates(Command):
    """
    List all action templates.

    Usage:
      +action/list

    Example:
      +action/list
    """

    key = "+action/list"
    locks = "cmd:all()"
    help_category = "Actions"

    def func(self):
        templates = ActionTemplate.objects.all()
        if templates.exists():
            message = "Available action templates:\n"
            for template in templates:
                message += f"{template.name} (Downtime Cost: {template.downtime_cost}, Requires Target: {template.requires_target})\n"
            self.caller.msg(message)
        else:
            self.caller.msg("No action templates available.")

class CmdTakeAction(Command):
    """
    Take an action using an action template.

    Usage:
      +action/take <template_name> = <target_asset_name>

    Example:
      +action/take Attack = Gold Mine
    """

    key = "+action/take"
    locks = "cmd:all()"
    help_category = "Actions"

    def func(self):
        try:
            template_name, target_asset_name = [item.strip() for item in self.args.split("=", 1)]
            template = ActionTemplate.objects.get(name__iexact=template_name.strip())
            target_asset = Asset.objects.get(name__iexact=target_asset_name.strip())

            # Assuming self.caller represents the character issuing the command
            character_id = self.caller.id  # Use self.caller's ID instead of character reference

            if template.requires_target and not target_asset:
                self.caller.msg("This action requires a valid target.")
                return

            downtime_cost = template.downtime_cost
            if self.caller.db.downtime_hours < downtime_cost:
                self.caller.msg(f"You do not have enough downtime hours for this action. Required: {downtime_cost}")
                return

            action = Action.objects.create(
                template=template,
                character_id=character_id,
                target_asset=target_asset,
                downtime_spent=downtime_cost
            )
            # Deduct the downtime cost from the caller's downtime hours
            self.caller.db.downtime_hours -= downtime_cost
            action.perform_action()
            self.caller.msg(f"Action '{template.name}' taken against {target_asset.name}.")
        except ActionTemplate.DoesNotExist:
            self.caller.msg("Action Template not found.")
        except Asset.DoesNotExist:
            self.caller.msg("Target Asset not found.")
        except ValueError:
            self.caller.msg("Invalid input. Please check your parameters.")
        except Exception as e:
            self.caller.msg(f"Error taking action: {e}")


class CmdRefreshDowntime(Command):
    """
    Refresh downtime hours for all characters.

    Usage:
      +oss/refreshdowntime

    Example:
      +oss/refreshdowntime
    """

    key = "+oss/refreshdowntime"
    locks = "cmd:all()"
    help_category = "Actions"

    def func(self):
        try:
            # Fetch all character objects
            characters = search_typeclass("typeclasses.characters.Character")

            refreshed_count = 0
            for char in characters:
                # Refresh the downtime hours using the defined method
                char.refresh_downtime()
                refreshed_count += 1
                char.msg(f"Your downtime hours have been refreshed to {char.db.downtime_hours}.")

            self.caller.msg(f"Downtime hours have been refreshed for {refreshed_count} characters.")
        except Exception as e:
            self.caller.msg(f"Error refreshing downtime: {e}")

# commands/oss/action_commands.py

from evennia import Command
from evennia import search_object
from evennia.utils.search import search_typeclass

class CmdListDowntime(Command):
    """
    List all characters and their current downtime hours.

    Usage:
      +oss/listdowntime

    Example:
      +oss/listdowntime
    """

    key = "+oss/listdowntime"
    locks = "cmd:all()"
    help_category = "Actions"

    def func(self):
        try:
            # Fetch all character objects
            #characters = search_object(None,typeclass="typeclasses.characters.Character")
            characters = search_typeclass("typeclasses.characters.Character")
            self.caller.msg(characters);
            object_count = 0;
            downtime_info = []
            for char in characters:
                object_count+=1;
                # Check if the object is a character
                # Ensure downtime_hours is initialized if not set
                if char.db.downtime_hours is None:
                    char.refresh_downtime()

                # Get current downtime hours
                current_downtime = char.db.downtime_hours
                downtime_info.append((char.key, current_downtime))

            if downtime_info:
                message = "Current downtime hours for all characters:\n"
                for char_name, hours in downtime_info:
                    message += f"{char_name}: {hours} hours\n"
                self.caller.msg(message)
            else:
                self.caller.msg(f"Objects found: {object_count}")
                self.caller.msg("No characters found or no downtime information available.")
        except Exception as e:
            self.caller.msg(f"Error retrieving downtime information: {e}")