# commands/oss/asset_commands.py

from evennia import Command
from world.wod20th.models import Asset
from evennia.utils.search import search_object

class CmdSearchAssets(Command):
    """
    Search for assets to target.

    Usage:
      +assets/search <query>

    Example:
      +assets/search Gold Mine
    """

    key = "+assets/search"
    locks = "cmd:all()"
    help_category = "Assets"

    def func(self):
        query = self.args.strip().lower()
        results = Asset.objects.filter(name__icontains=query)
        if results.exists():
            message = "Found the following assets:\n"
            for asset in results:
                message += f"{asset.id}. {asset.name} (Type: {asset.get_asset_type_display()})\n"
            self.caller.msg(message)
        else:
            self.caller.msg("No assets found matching your query.")

class CmdCreateAsset(Command):
    """
    Create a new asset.

    Usage:
      +assets/create <name> = <asset_type>, <value>, <description>

    Example:
      +assets/create Gold Mine = territory, 5, "A lucrative gold mine."
    """

    key = "+assets/create"
    locks = "cmd:all()"
    help_category = "Assets"

    def func(self):
        try:
            name, details = self.args.split("=", 1)
            asset_type, value, description = [item.strip() for item in details.split(",", 2)]
            
            # Create the asset with the caller as the owner
            asset = Asset.objects.create(
                name=name.strip(),
                asset_type=asset_type,
                value=int(value),
                description=description,
                owner_id=self.caller.id  # Set the owner to the caller's ID
            )
            self.caller.msg(f"Asset '{asset.name}' created successfully with you as the owner.")
        except ValueError:
            self.caller.msg("Invalid input. Please check the asset details.")
        except Exception as e:
            self.caller.msg(f"Error creating asset: {e}")

class CmdReadAsset(Command):
    """
    View details of an asset.

    Usage:
      +assets/view <asset_name>

    Example:
      +assets/view Gold Mine
    """

    key = "+assets/view"
    locks = "cmd:all()"
    help_category = "Assets"

    def func(self):
        try:
            asset_name = self.args.strip()
            asset = Asset.objects.get(name__iexact=asset_name)
            owner = asset.owner  # This will use the new owner property method
            owner_display = f"{owner} (ID: {asset.owner_id})" if owner else f"ID: {asset.owner_id} (Character not found)"
            self.caller.msg(
                f"Asset: {asset.name}\n"
                f"Type: {asset.get_asset_type_display()}\n"
                f"Value: {asset.value}\n"
                f"Description: {asset.description}\n"
                f"Owner: {owner_display}\n"
                f"Status: {asset.status}\n"
                f"Traits: {asset.traits}"
            )
        except Asset.DoesNotExist:
            self.caller.msg("Asset not found.")

class CmdUpdateAsset(Command):
    """
    Update an asset.

    Usage:
      +assets/update <asset_name> = <field>, <value>

    Example:
      +assets/update Gold Mine = value, 10
    """

    key = "+assets/update"
    locks = "cmd:all()"
    help_category = "Assets"

    def func(self):
        try:
            asset_name, updates = self.args.split("=", 1)
            field, value = [item.strip() for item in updates.split(",", 1)]
            asset = Asset.objects.get(name__iexact=asset_name.strip())

            # Handle specific field types
            if field == 'value':
                value = int(value)
            elif field == 'owner_id':
                value = int(value)  # Ensure owner_id is an integer

            setattr(asset, field, value)
            asset.save()
            self.caller.msg(f"Asset '{asset.name}' updated successfully.")
        except Asset.DoesNotExist:
            self.caller.msg("Asset not found.")
        except ValueError:
            self.caller.msg("Invalid value type. Please ensure you are entering the correct data type.")
        except Exception as e:
            self.caller.msg(f"Error updating asset: {e}")

class CmdDeleteAsset(Command):
    """
    Delete an asset.

    Usage:
      +assets/delete <asset_name>

    Example:
      +assets/delete Gold Mine
    """

    key = "+assets/delete"
    locks = "cmd:all()"
    help_category = "Assets"

    def func(self):
        try:
            asset_name = self.args.strip()
            asset = Asset.objects.get(name__iexact=asset_name)
            asset.delete()
            self.caller.msg(f"Asset '{asset.name}' deleted successfully.")
        except Asset.DoesNotExist:
            self.caller.msg("Asset not found.")

class CmdTransferAsset(Command):
    """
    Transfer ownership of an asset to another character.

    Usage:
      +assets/transfer <asset_name> = <new_owner_name>

    Example:
      +assets/transfer Gold Mine = JohnDoe
    """

    key = "+assets/transfer"
    locks = "cmd:all()"
    help_category = "Assets"

    def func(self):
        try:
            asset_name, new_owner_name = [item.strip() for item in self.args.split("=", 1)]
            
            # Find the asset
            asset = Asset.objects.get(name__iexact=asset_name)

            # Find the new owner by name
            new_owner = search_object(new_owner_name)
            if not new_owner:
                self.caller.msg(f"No character found with the name '{new_owner_name}'.")
                return

            new_owner = new_owner[0]  # Take the first match, assuming unique names
            new_owner_id = new_owner.id

            # Transfer ownership
            asset.owner_id = new_owner_id
            asset.save()
            
            self.caller.msg(f"Asset '{asset.name}' has been transferred to {new_owner_name}.")
        except Asset.DoesNotExist:
            self.caller.msg(f"Asset '{asset_name}' not found.")
        except ValueError:
            self.caller.msg("Invalid input. Please ensure correct asset and character names.")
        except Exception as e:
            self.caller.msg(f"Error transferring asset: {e}")

class CmdAssets(Command):
    """
    List all assets owned by the caller. This command serves as the base command for asset-related actions.

    Usage:
      +assets

    Example:
      +assets
    """

    key = "+assets"
    locks = "cmd:all()"
    help_category = "Assets"

    def func(self):
        try:
            # Retrieve the caller's ID
            caller_id = self.caller.id

            # Fetch all assets owned by the caller
            owned_assets = Asset.objects.filter(owner_id=caller_id)

            if owned_assets:
                message = "You own the following assets:\n"
                for asset in owned_assets:
                    message += f"{asset.name} (Type: {asset.get_asset_type_display()}, Value: {asset.value})\n"
            else:
                message = "You do not own any assets."

            self.caller.msg(message)
        except Exception as e:
            self.caller.msg(f"Error retrieving owned assets: {e}")