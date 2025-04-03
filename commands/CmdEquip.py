"""
Equipment command module.

This module implements commands for viewing, requesting and managing equipment.
"""

from django.utils import timezone
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.utils import crop, list_to_string
from evennia.utils.evtable import EvTable
from world.equipment.models import (
    Equipment, PlayerInventory, InventoryItem,
    # Weapon types
    MeleeWeapon, RangedWeapon, ThrownWeapon, ImprovisedWeapon, MartialArtsWeapon,
    # Armor and ammunition
    Armor, Ammunition, SpecialAmmunition,
    # Explosive
    Explosive,
    # Tech and electronic devices
    TechnocraticDevice, SpyingDevice, CommunicationsDevice, ElectronicDevice,
    # Survival gear
    SurvivalGear,
    # Vehicle types
    Cycle, Landcraft, Seacraft, Aircraft, Jetpack,
    # Supernatural items
    Talisman, Device, Trinket, Gadget, Invention, Matrix, Grimoire,
    Biotech, Cybertech, Periapt, Chimerical, Treasure, Fetish, Talen, Artifact
)
from django.db.models import Q
from world.wod20th.utils.formatting import header, footer, divider

class CmdEquip(MuxCommand):
    """
    View and request equipment.
    
    Usage:
      +equip                    - Show all equipment categories
      +equip/list <category>    - Show items in a specific category
      +equip/view <id>          - View detailed information about a specific item
      +equip/req <id>           - Request a specific piece of equipment (creates a job)
      +equip/approve <job_id>   - Approve an equipment request job (Staff only)
      +equip/add <name>/<type>/<description>  - Add new equipment (Staff only)
      +equip/remove <player>=<inv_id>[/<amount>]  - Remove item(s) from a player's inventory (Staff only)
      +equip/removeall <player>  - Remove ALL equipment from a player's inventory (Staff only)
    
    The equipment system allows you to view, request, and manage various types of
    equipment in the game. Each item has a unique ID.
    
    When you request equipment, a job is created in the EQUIP category. Staff will
    review the request and may approve or reject it. Approved equipment will be
    added to your inventory.
    
    Categories include weapons, armor, vehicles, and various supernatural items.
    Use +equip without arguments to see all available categories.
    """
    
    key = "+equip"
    aliases = ["equip"]
    locks = "cmd:all()"
    help_category = "Equipment"
    
    def func(self):
        """
        Main function for the command.
        """
        if not self.switches:
            # Show categories
            self._show_categories()
            return
            
        if "list" in self.switches:
            # List items in a category
            if not self.args:
                self.caller.msg("You must specify a category. Use +equip to see all categories.")
                return
            self._list_category(self.args.strip().lower())
            return
            
        if "view" in self.switches:
            # View a specific item
            if not self.args:
                self.caller.msg("You must specify an item ID to view. Use +equip/list <category> to see available items.")
                return
            try:
                item_id = int(self.args.strip())
                self._view_item(item_id)
            except ValueError:
                self.caller.msg("The item ID must be a number.")
            return
            
        if "req" in self.switches:
            # Request an item
            if not self.args:
                self.caller.msg("You must specify an item ID to request. Use +equip/list <category> to see available items.")
                return
            try:
                item_id = int(self.args.strip())
                self._request_item(item_id)
            except ValueError:
                self.caller.msg("The item ID must be a number.")
            return
            
        if "approve" in self.switches:
            # Approve a request (staff only)
            if not self.caller.locks.check_lockstring(self.caller, "perm(Admin) or perm(Builder)"):
                self.caller.msg("You don't have permission to approve equipment requests.")
                return
                
            if not self.args:
                self.caller.msg("You must specify a job ID to approve.")
                return
                
            try:
                job_id = int(self.args.strip())
                self._approve_request(job_id)
            except ValueError:
                self.caller.msg("The job ID must be a number.")
            return
        
        if "remove" in self.switches:
            # Remove an item from a player's inventory (staff only)
            if not self.caller.locks.check_lockstring(self.caller, "perm(Admin) or perm(Builder)"):
                self.caller.msg("You don't have permission to remove equipment from players.")
                return
                
            if not self.args or "=" not in self.args:
                self.caller.msg("Usage: +equip/remove <player>=<inventory_id>[/<amount>]")
                return
                
            player_name, item_info = self.args.split("=", 1)
            player_name = player_name.strip()
            
            # Check if amount is specified
            if "/" in item_info:
                inv_id_str, amount_str = item_info.split("/", 1)
                try:
                    inv_id = int(inv_id_str.strip())
                    amount = int(amount_str.strip())
                    if amount <= 0:
                        self.caller.msg("Amount must be a positive number.")
                        return
                except ValueError:
                    self.caller.msg("The inventory ID and amount must be numbers.")
                    return
            else:
                try:
                    inv_id = int(item_info.strip())
                    amount = 1  # Default to removing 1 item
                except ValueError:
                    self.caller.msg("The inventory ID must be a number.")
                    return
                
            self._remove_item(player_name, inv_id, amount)
            return
            
        if "removeall" in self.switches:
            # Remove ALL equipment from a player's inventory (staff only)
            if not self.caller.locks.check_lockstring(self.caller, "perm(Admin) or perm(Builder)"):
                self.caller.msg("You don't have permission to remove equipment from players.")
                return
                
            if not self.args:
                self.caller.msg("Usage: +equip/removeall <player>")
                return
                
            player_name = self.args.strip()
            self._remove_all_items(player_name)
            return
            
        if "add" in self.switches:
            # Add new equipment (staff only)
            if not self.caller.locks.check_lockstring(self.caller, "perm(Admin) or perm(Builder)"):
                self.caller.msg("You don't have permission to add new equipment.")
                return
                
            # Check args format - should be name/type/description
            if not self.args or "/" not in self.args:
                self.caller.msg("Usage: +equip/add <name>/<type>/<description>")
                return
                
            self._add_equipment(self.args)
            return
            
        # If we get here, switch is not recognized
        self.caller.msg("Unrecognized switch. Use +help equip to see valid options.")
    
    def _show_categories(self):
        """Show all equipment categories."""
        # Get a list of all categories from the database
        categories = Equipment.objects.values_list('category', flat=True).distinct().order_by('category')
        
        # Create a set to remove duplicates and then sort for consistent display
        unique_categories = sorted(set(categories))
        
        # Create our output
        table = EvTable(border="table")
        table.add_column("|wMundane Categories|n")
        table.add_column("|wSupernatural Categories|n")
        
        # Separate mundane and supernatural categories
        mundane_cats = []
        supernatural_cats = []
        
        for cat in unique_categories:
            # This is a basic way to separate - might need adjustment based on your game's specifics
            if cat in ['talisman', 'device', 'trinket', 'gadget', 'invention', 
                      'matrix', 'grimoire', 'biotech', 'cybertech', 'periapt', 
                      'chimerical', 'treasure', 'fetish', 'talen', 'artifact']:
                supernatural_cats.append(f"|w{cat.title()}|n")
            else:
                mundane_cats.append(f"|w{cat.title()}|n")
        
        # Add rows to table
        max_rows = max(len(mundane_cats), len(supernatural_cats))
        for i in range(max_rows):
            mundane = mundane_cats[i] if i < len(mundane_cats) else ""
            supernatural = supernatural_cats[i] if i < len(supernatural_cats) else ""
            table.add_row(mundane, supernatural)
        
        # Send the formatted output to the caller
        output = header("Equipment Categories")
        output += str(table)
        output += "\n" + divider("Usage", text_color="|w")
        output += "\n|wUse |y+equip/list <category>|w to see items in a specific category.|n"
        output += "\n|wFor example: |y+equip/list melee|w or |y+equip/list fetish|n"
        output += "\n" + footer()
        
        self.caller.msg(output)
    
    def _list_category(self, category):
        """List all items in a specific category."""
        # Query the database for items in this category
        base_items = Equipment.objects.filter(category=category).order_by('name')
        
        if not base_items:
            self.caller.msg(f"No equipment found in category '{category}'. Use +equip to see all categories.")
            return
        
        # Get the most specific instances of the items using our custom manager
        items = Equipment.objects.get_real_instances(base_items)
        
        # Create our output
        output = header(f"{category.title()} Equipment")
        
        # Create a table for the items
        table = EvTable("|wID|n", "|wName|n", "|wResources|n", "|wConceal|n", "|wApproval|n", border="table", width=78)
        
        for item in items:
            approval = "|rYes|n" if item.requires_approval else "|gNo|n"
            table.add_row(
                str(item.sequential_id),
                crop(item.name, width=30),
                str(item.resources),
                item.conceal,
                approval
            )
        
        output += str(table)
        output += "\n" + divider("Usage", text_color="|w")
        output += "\n|wUse |y+equip/view <ID>|w to see details about a specific item.|n"
        output += "\n|wUse |y+equip/req <ID>|w to request a specific item.|n"
        output += "\n" + footer()
        
        self.caller.msg(output)
    
    def _view_item(self, item_id):
        """View details about a specific equipment item."""
        try:
            # Get the base equipment object
            equipment = Equipment.objects.get(sequential_id=item_id)
            
            if not equipment:
                self.caller.msg(f"No equipment found with ID {item_id}.")
                return
                
            # Create our output
            output = header(f"Equipment: {equipment.name}")
            
            # Basic information - this applies to all equipment
            output += divider("Basic Information", text_color="|w")
            output += f"\n|wID:|n {equipment.sequential_id}"
            output += f"\n|wName:|n {equipment.name}"
            output += f"\n|wCategory:|n {equipment.category.title()}"
            output += f"\n|wType:|n {equipment.equipment_type.title()}"
            output += f"\n|wResources:|n {equipment.resources}"
            output += f"\n|wConceal:|n {equipment.conceal}"
            output += f"\n|wRequires Approval:|n {'Yes' if equipment.requires_approval else 'No'}"
            output += f"\n|wUnique:|n {'Yes' if equipment.is_unique else 'No'}"
            
            # Description
            output += "\n\n" + divider("Description", text_color="|w")
            output += f"\n{equipment.description}"
            
            # First check for specialized details using our new composition approach
            details = equipment.specialized_details
            
            if details:
                # We found specialized details, so display them based on category
                category = equipment.category
                
                if category == 'melee':
                    output += "\n\n" + divider("Weapon Details", text_color="|w")
                    output += f"\n|wDamage:|n {details.damage}"
                    output += f"\n|wDamage Type:|n {details.damage_type}"
                    output += f"\n|wDifficulty:|n {details.difficulty}"
                
                elif category == 'ranged':
                    output += "\n\n" + divider("Weapon Details", text_color="|w")
                    output += f"\n|wDamage:|n {details.damage}"
                    output += f"\n|wDamage Type:|n {details.damage_type}"
                    output += f"\n|wRange:|n {details.range}"
                    output += f"\n|wRate:|n {details.rate}"
                    output += f"\n|wClip:|n {details.clip}"
                
                elif category == 'thrown':
                    output += "\n\n" + divider("Weapon Details", text_color="|w")
                    output += f"\n|wDamage:|n {details.damage}"
                    output += f"\n|wDamage Type:|n {details.damage_type}"
                    output += f"\n|wRange:|n {details.range}"
                    output += f"\n|wDifficulty:|n {details.difficulty}"
                
                elif category == 'improvised':
                    output += "\n\n" + divider("Weapon Details", text_color="|w")
                    output += f"\n|wDamage:|n {details.damage}"
                    output += f"\n|wDamage Type:|n {details.damage_type}"
                    output += f"\n|wDifficulty:|n {details.difficulty}"
                    output += f"\n|wBreak Chance:|n {details.break_chance}%"
                
                elif category == 'explosives':
                    output += "\n\n" + divider("Explosive Details", text_color="|w")
                    output += f"\n|wBlast Area:|n {details.blast_area}"
                    output += f"\n|wBlast Power:|n {details.blast_power}"
                    output += f"\n|wBurn:|n {'Yes' if details.burn else 'No'}"
                    if details.notes:
                        output += f"\n|wNotes:|n {details.notes}"
                
                elif category == 'armor':
                    output += "\n\n" + divider("Armor Details", text_color="|w")
                    output += f"\n|wRating:|n {details.rating}"
                    output += f"\n|wDexterity Penalty:|n {details.dexterity_penalty}"
                    output += f"\n|wIs Shield:|n {'Yes' if details.is_shield else 'No'}"
                    if details.is_shield:
                        output += f"\n|wShield Bonus:|n {details.shield_bonus}"
                
                elif category == 'landcraft':
                    output += "\n\n" + divider("Vehicle Details", text_color="|w")
                    output += f"\n|wVehicle Type:|n {details.vehicle_type.title()}"
                    output += f"\n|wSafe Speed:|n {details.safe_speed}"
                    output += f"\n|wMax Speed:|n {details.max_speed}"
                    output += f"\n|wManeuver:|n {details.maneuver}"
                    output += f"\n|wCrew:|n {details.crew}"
                    output += f"\n|wDurability:|n {details.durability}"
                    output += f"\n|wStructure:|n {details.structure}"
                    output += f"\n|wMass Damage:|n {details.mass_damage}"
                    output += f"\n|wPassenger Protection:|n {details.passenger_protection}"
                    if details.weapons:
                        output += f"\n|wWeapons:|n {details.weapons}"
                    output += f"\n|wRequired Skill:|n {details.requires_skill}"
                
                # Add similar blocks for other categories
                
            else:
                # Fall back to checking for legacy inheritance model
                # This code remains as in the existing implementation but as a fallback
                if isinstance(equipment, MeleeWeapon):
                    output += "\n\n" + divider("Weapon Details", text_color="|w")
                    output += f"\n|wDamage:|n {equipment.damage}"
                    output += f"\n|wDamage Type:|n {equipment.damage_type}"
                    output += f"\n|wDifficulty:|n {equipment.difficulty}"
                
                elif isinstance(equipment, RangedWeapon):
                    output += "\n\n" + divider("Weapon Details", text_color="|w")
                    output += f"\n|wDamage:|n {equipment.damage}"
                    output += f"\n|wDamage Type:|n {equipment.damage_type}"
                    output += f"\n|wRange:|n {equipment.range}"
                    output += f"\n|wRate:|n {equipment.rate}"
                    output += f"\n|wClip:|n {equipment.clip}"
                
                # ... rest of the existing implementation for other types
                
                # If no specialized data is found, show generic messages
                elif equipment.category in ['melee', 'ranged', 'thrown', 'improvised', 'martial_arts']:
                    output += "\n\n" + divider("Weapon Details", text_color="|w")
                    output += "\n|yThis weapon's specific details aren't available.|n"
                    output += "\n|wTypical weapons have attributes for damage, damage type, and other combat statistics.|n"
                elif equipment.category == 'explosives':
                    output += "\n\n" + divider("Explosive Details", text_color="|w")
                    output += "\n|yThis explosive's specific details aren't available.|n"
                    output += "\n|wTypical explosives have attributes for blast area, blast power, and burn effect.|n"
                elif equipment.category == 'armor':
                    output += "\n\n" + divider("Armor Details", text_color="|w")
                    output += "\n|yThis armor's specific details aren't available.|n"
                    output += "\n|wTypical armor has attributes for rating, dexterity penalty, and shield properties.|n"
                elif equipment.category == 'ammunition':
                    output += "\n\n" + divider("Ammunition Details", text_color="|w")
                    output += "\n|yThis ammunition's specific details aren't available.|n"
                    output += "\n|wTypical ammunition has attributes for caliber, damage modifier, and special effects.|n"
                elif equipment.category in ['landcraft', 'aircraft', 'seacraft', 'cycle', 'jetpack']:
                    output += "\n\n" + divider("Vehicle Details", text_color="|w")
                    output += "\n|yThis vehicle's specific details aren't available.|n"
                    output += "\n|wTypical vehicles have attributes for speed, maneuver, crew capacity, and durability.|n"
                elif equipment.category in ['talisman', 'device', 'trinket', 'gadget', 'invention', 'matrix', 'grimoire', 'biotech', 'cybertech', 'periapt', 'chimerical', 'treasure', 'fetish', 'talen', 'artifact']:
                    output += "\n\n" + divider("Supernatural Details", text_color="|w")
                    output += "\n|yThis item's specific supernatural details aren't available.|n"
                    output += "\n|wTypical supernatural items have attributes for power level, activation requirements, duration, and special effects.|n"
                else:
                    output += "\n\n" + divider(f"{equipment.category.title()} Details", text_color="|w")
                    output += f"\n|yNo specialized details available for this item category.|n"
            
            # Add command hint
            output += "\n\n" + divider("Commands", text_color="|w")
            output += f"\n|wTo request this item: |y+equip/req {equipment.sequential_id}|n"
            output += f"\n|wThis will create a job for staff approval.|n"
            
            output += "\n" + footer()
            self.caller.msg(output)
            
        except Equipment.DoesNotExist:
            self.caller.msg(f"No equipment found with ID {item_id}.")
            return
        except Exception as e:
            # Log the error and show a friendly message
            import traceback
            from evennia.utils.logger import log_err
            log_err(f"Error in _view_item: {e}\n{traceback.format_exc()}")
            self.caller.msg(f"Error displaying equipment details for ID {item_id}: {e}")
            return
    
    def _request_item(self, item_id):
        """Request a specific piece of equipment."""
        try:
            # Use our custom manager to get the most specific instance
            equipment = Equipment.objects.get_by_id(item_id)
            
            if not equipment:
                self.caller.msg(f"No equipment found with ID {item_id}.")
                return
                
            # Create a job in the EQUIP category
            from world.jobs.models import Job, Queue
            from django.utils import timezone
            
            # Get or create the EQUIP queue
            queue, created = Queue.objects.get_or_create(
                name="EQUIP",
                defaults={'automatic_assignee': None}
            )
            
            # Create job title and description
            title = f"Equipment Request: {equipment.name}"
            description = f"Character: {self.caller.name}\n"
            description += f"Equipment ID: {equipment.sequential_id}\n"
            description += f"Equipment Name: {equipment.name}\n"
            description += f"Equipment Category: {equipment.category.title()}\n"
            description += f"Equipment Type: {equipment.equipment_type.title()}\n"
            description += f"Resources: {equipment.resources}\n"
            description += f"Conceal: {equipment.conceal}\n"
            description += f"Requires Approval: {'Yes' if equipment.requires_approval else 'No'}\n"
            description += f"Is Unique: {'Yes' if equipment.is_unique else 'No'}\n\n"
            description += f"Description: {equipment.description}\n\n"
            description += f"Note: This item will be added to {self.caller.name}'s inventory upon approval."
            
            # Create the job
            job = Job.objects.create(
                title=title,
                description=description,
                requester=self.caller.account,
                queue=queue,
                status='open'
            )
            
            # Notify the requester
            self.caller.msg(f"|gYou have requested {equipment.name}. A job (#{job.id}) has been created.|n")
            
            # Notify staff via jobs channel
            from evennia.comms.models import ChannelDB
            channels = ChannelDB.objects.filter(db_key__iexact="Jobs")
            if channels:
                channel = channels[0]
                channel.msg(f"[Job System] {self.caller.name} has requested equipment: {equipment.name} (Job #{job.id})")
                
        except Equipment.DoesNotExist:
            self.caller.msg(f"No equipment found with ID {item_id}.")
            return
        except Exception as e:
            import traceback
            from evennia.utils.logger import log_err
            log_err(f"Error in _request_item: {e}\n{traceback.format_exc()}")
            self.caller.msg(f"Error processing equipment request: {e}")
            return
    
    def _approve_request(self, job_id):
        """Approve an equipment request using the job ID."""
        if not self.caller.locks.check_lockstring(self.caller, "perm(Admin) or perm(Builder)"):
            self.caller.msg("You don't have permission to approve equipment requests.")
            return
            
        try:
            # Get the job
            from world.jobs.models import Job
            try:
                job = Job.objects.get(id=job_id)
            except Job.DoesNotExist:
                self.caller.msg(f"Job #{job_id} not found.")
                return
                
            # Verify this is an equipment request job
            if job.queue.name != "EQUIP" or not job.title.startswith("Equipment Request:"):
                self.caller.msg("This is not an equipment request job.")
                return
                
            # Extract equipment name from title
            equipment_name = job.title.replace("Equipment Request:", "").strip()
            
            try:
                # Find the equipment
                equipment = Equipment.objects.get(name=equipment_name)
                
                # Get or create inventory for the requester
                account = job.requester
                inventory, created = PlayerInventory.objects.get_or_create(player=account)
                
                # Check if item already exists in inventory
                existing_item = InventoryItem.objects.filter(
                    inventory=inventory,
                    equipment=equipment
                ).first()
                
                if existing_item:
                    if equipment.is_unique:
                        self.caller.msg("Player already has this unique item.")
                        return
                    existing_item.quantity += 1
                    existing_item.is_proven = True
                    existing_item.approval_date = timezone.now()
                    existing_item.approved_by = self.caller.account
                    existing_item.save()
                else:
                    # Create new inventory item (approved)
                    inventory_item = InventoryItem.objects.create(
                        inventory=inventory,
                        equipment=equipment,
                        quantity=1,
                        is_proven=True,
                        approval_date=timezone.now(),
                        approved_by=self.caller.account
                    )
                
                # Approve the job using the jobs system
                self.caller.execute_cmd(f"+jobs/approve {job_id}=Equipment {equipment.name} added to {account.username}'s inventory.")
                
                # Notify the player
                player = account
                player.msg(f"Your request for {equipment.name} has been approved by {self.caller.name}.")
                
                # Confirm to the approver
                self.caller.msg(f"You have approved {player.username}'s request for {equipment.name}.")
                
            except Equipment.DoesNotExist:
                self.caller.msg(f"Equipment '{equipment_name}' not found.")
                return
                
        except Exception as e:
            import traceback
            from evennia.utils.logger import log_err
            log_err(f"Error in _approve_request: {e}\n{traceback.format_exc()}")
            self.caller.msg(f"Error approving equipment request: {e}")
            return
    
    def _add_equipment(self, args):
        """Add new equipment (staff only)."""
        # Parse the arguments
        try:
            name, eq_type, description = args.split("/", 2)
        except ValueError:
            self.caller.msg("Usage: +equip/add <name>/<type>/<description>")
            return
        
        # Validate the equipment type
        valid_types = ['mundane', 'supernatural_consumable', 'supernatural_unique']
        if eq_type.lower() not in valid_types:
            self.caller.msg(f"Invalid equipment type. Must be one of: {', '.join(valid_types)}")
            return
        
        # Get the next sequential ID
        next_id = 1
        max_id = Equipment.objects.all().order_by('-sequential_id').first()
        if max_id:
            next_id = max_id.sequential_id + 1
        
        # Create a basic equipment item
        equipment = Equipment.objects.create(
            sequential_id=next_id,
            name=name.strip(),
            description=description.strip(),
            resources=1,  # Default value
            quantity=1,   # Default value
            conceal="P",  # Default value
            equipment_type=eq_type.lower(),
            category="misc",  # Default category
            is_unique=False,
            requires_approval=True
        )
        
        self.caller.msg(f"Equipment '{name}' created with ID {next_id}. Use the Django admin to set additional properties.")

    def _remove_item(self, player_name, inv_id, amount=1):
        """Remove a specific amount of an item from a player's inventory (staff only)."""
        # Find the player
        from evennia.accounts.models import AccountDB
        player = AccountDB.objects.filter(username__iexact=player_name).first()
        
        if not player:
            self.caller.msg(f"No player found with the name '{player_name}'.")
            return
            
        # Find the inventory item
        try:
            inventory = PlayerInventory.objects.get(player=player)
            item = InventoryItem.objects.get(id=inv_id, inventory=inventory)
            
            # Get equipment details before deletion
            equipment_name = item.equipment.name
            
            if item.quantity > amount:
                # Reduce quantity by specified amount
                item.quantity -= amount
                item.save()
                self.caller.msg(f"Reduced {player.username}'s {equipment_name} quantity by {amount}. New quantity: {item.quantity}")
                
                # Notify the player if online
                if player.is_connected:
                    player.msg(f"{self.caller.name} has removed {amount} {equipment_name} from your inventory. Remaining: {item.quantity}")
            else:
                # Delete the item entirely
                actual_amount = item.quantity  # Store actual amount for the message
                item.delete()
                
                self.caller.msg(f"Removed all {actual_amount} {equipment_name}(s) from {player.username}'s inventory.")
                
                # Notify the player if online
                if player.is_connected:
                    player.msg(f"{self.caller.name} has removed all {actual_amount} {equipment_name}(s) from your inventory.")
                
        except PlayerInventory.DoesNotExist:
            self.caller.msg(f"{player.username} doesn't have an inventory.")
            return
        except InventoryItem.DoesNotExist:
            self.caller.msg(f"No item with ID {inv_id} found in {player.username}'s inventory.")
            return
        except Exception as e:
            import traceback
            from evennia.utils.logger import log_err
            log_err(f"Error in _remove_item: {e}\n{traceback.format_exc()}")
            self.caller.msg(f"Error removing equipment: {e}")
            return
    
    def _remove_all_items(self, player_name):
        """Remove ALL equipment from a player's inventory (staff only)."""
        # Find the player
        from evennia.accounts.models import AccountDB
        player = AccountDB.objects.filter(username__iexact=player_name).first()
        
        if not player:
            self.caller.msg(f"No player found with the name '{player_name}'.")
            return
            
        # Find the player's inventory
        try:
            inventory = PlayerInventory.objects.get(player=player)
            items = InventoryItem.objects.filter(inventory=inventory)
            
            if not items.exists():
                self.caller.msg(f"{player.username} doesn't have any inventory items.")
                return
                
            # Count items before deletion
            item_count = items.count()
            
            # Delete all items
            items.delete()
            
            self.caller.msg(f"Removed all {item_count} equipment items from {player.username}'s inventory.")
            
            # Notify the player if online
            if player.is_connected:
                player.msg(f"{self.caller.name} has removed ALL equipment from your inventory.")
                
        except PlayerInventory.DoesNotExist:
            self.caller.msg(f"{player.username} doesn't have an inventory.")
            return
        except Exception as e:
            import traceback
            from evennia.utils.logger import log_err
            log_err(f"Error in _remove_all_items: {e}\n{traceback.format_exc()}")
            self.caller.msg(f"Error removing all equipment: {e}")
            return

class CmdInventory(MuxCommand):
    """
    View your inventory or another player's inventory.
    
    Usage:
      +inv                   - Show your inventory
      +inv <player>          - Show another player's inventory (Staff only)
      +inv/prove <id>        - Prove a piece of equipment you own
      +inv/view <id>         - View detailed information about an inventory item
    
    The inventory system tracks all equipment you have requested or been granted.
    Each item shows its quantity and proof status. Staff members can view other
    players' inventories.
    """
    
    key = "+inv"
    aliases = ["inv", "+inventory", "inventory"]
    locks = "cmd:all()"
    help_category = "Equipment"
    
    def func(self):
        """
        Main function for the command.
        """
        if not self.switches:
            # View inventory - either own or another player's
            if not self.args:
                # View own inventory
                self._view_inventory(self.caller.account)
            else:
                # View another player's inventory (staff only)
                if not self.caller.locks.check_lockstring(self.caller, "perm(Admin) or perm(Builder)"):
                    self.caller.msg("You don't have permission to view other players' inventories.")
                    return
                
                # Try to find the target player
                from evennia.accounts.models import AccountDB
                target = AccountDB.objects.filter(Q(username__iexact=self.args) | Q(db_key__iexact=self.args)).first()
                
                if not target:
                    self.caller.msg(f"No player found named '{self.args}'.")
                    return
                
                self._view_inventory(target, is_other=True)
            return
        
        if "prove" in self.switches:
            # Prove an item
            if not self.args:
                self.caller.msg("You must specify an inventory item ID to prove.")
                return
            
            try:
                item_id = int(self.args.strip())
                self._prove_item(item_id)
            except ValueError:
                self.caller.msg("The inventory item ID must be a number.")
            return
        
        if "view" in self.switches:
            # View detailed information about an inventory item
            if not self.args:
                self.caller.msg("You must specify an inventory item ID to view.")
                return
            
            try:
                item_id = int(self.args.strip())
                self._view_item(item_id)
            except ValueError:
                self.caller.msg("The inventory item ID must be a number.")
            return
        
        # If we get here, switch is not recognized
        self.caller.msg("Unrecognized switch. Use +help inventory to see valid options.")
    
    def _view_inventory(self, player, is_other=False):
        """View a player's inventory."""
        # Try to get the player's inventory
        try:
            inventory = PlayerInventory.objects.get(player=player)
        except PlayerInventory.DoesNotExist:
            if is_other:
                self.caller.msg(f"{player.username} doesn't have any inventory items.")
            else:
                self.caller.msg("You don't have any inventory items. Use +equip to request equipment.")
            return
        
        # Get all inventory items
        items = InventoryItem.objects.filter(inventory=inventory).select_related('equipment')
        
        if not items:
            if is_other:
                self.caller.msg(f"{player.username} doesn't have any inventory items.")
            else:
                self.caller.msg("You don't have any inventory items. Use +equip to request equipment.")
            return
        
        # Create our output
        if is_other:
            output = header(f"{player.username}'s Inventory")
        else:
            output = header("Your Inventory")
        
        # Create a table for the items
        table = EvTable("|wID|n", "|wItem|n", "|wQty|n", "|wProven|n", "|wApproved|n", border="table", width=78)
        
        for item in items:
            proven = "|gYes|n" if item.is_proven else "|rNo|n"
            approved = "|gYes|n" if item.approved_by else "|rNo|n"
            
            table.add_row(
                str(item.id),
                crop(item.equipment.name, width=40),
                str(item.quantity),
                proven,
                approved
            )
        
        output += str(table)
        
        # Add command hints
        output += "\n" + divider("Commands", text_color="|w")
        output += "\n|wTo view an item: |y+inv/view <ID>|n"
        output += "\n|wTo prove an item: |y+inv/prove <ID>|n"
        
        output += "\n" + footer()
        self.caller.msg(output)
    
    def _prove_item(self, item_id):
        """Mark an item as proven (i.e. the character has demonstrated they have it)."""
        # Try to find the item in the player's inventory
        try:
            item = InventoryItem.objects.get(
                id=item_id,
                inventory__player=self.caller.account
            )
        except InventoryItem.DoesNotExist:
            self.caller.msg(f"No inventory item found with ID {item_id} in your inventory.")
            return
        
        # Check if the item is approved
        if not item.approved_by:
            self.caller.msg("This item has not been approved yet and cannot be proven.")
            return
        
        # Check if already proven
        if item.is_proven:
            self.caller.msg("This item is already proven.")
            return
        
        # Mark as proven
        item.is_proven = True
        item.save()
        
        # Inform the player and others in the room
        self.caller.msg(f"You prove that you have {item.equipment.name}.")
        self.caller.location.msg_contents(
            f"{self.caller.name} proves that they have {item.equipment.name}.",
            exclude=self.caller
        )
    
    def _view_item(self, item_id):
        """View detailed information about an inventory item."""
        # Check if staff (can view any item) or regular player (can only view own items)
        is_staff = self.caller.locks.check_lockstring(self.caller, "perm(Admin) or perm(Builder)")
        
        # Build the query accordingly
        query = Q(id=item_id)
        if not is_staff:
            query &= Q(inventory__player=self.caller.account)
        
        try:
            item = InventoryItem.objects.select_related('equipment', 'approved_by').get(query)
        except InventoryItem.DoesNotExist:
            if is_staff:
                self.caller.msg(f"No inventory item found with ID {item_id}.")
            else:
                self.caller.msg(f"No inventory item found with ID {item_id} in your inventory.")
            return
        
        # Get the actual equipment instance
        equipment = Equipment.objects.get_real_instance(item.equipment)
        
        # Create our output
        output = header(f"Inventory Item: {equipment.name}")
        
        # Basic information
        output += divider("Item Information", text_color="|w")
        output += f"\n|wInventory ID:|n {item.id}"
        output += f"\n|wEquipment ID:|n {equipment.sequential_id}"
        output += f"\n|wName:|n {equipment.name}"
        output += f"\n|wCategory:|n {equipment.category.title()}"
        output += f"\n|wType:|n {equipment.equipment_type.title()}"
        output += f"\n|wResources:|n {equipment.resources}"
        output += f"\n|wConceal:|n {equipment.conceal}"
        output += f"\n|wQuantity:|n {item.quantity}"
        output += f"\n|wProven:|n {'Yes' if item.is_proven else 'No'}"
        
        # Approval information
        output += "\n\n" + divider("Approval Information", text_color="|w")
        output += f"\n|wRequires Approval:|n {'Yes' if equipment.requires_approval else 'No'}"
        output += f"\n|wUnique:|n {'Yes' if equipment.is_unique else 'No'}"
        if item.approved_by:
            output += f"\n|wApproved By:|n {item.approved_by.username}"
            output += f"\n|wApproval Date:|n {item.approval_date.strftime('%Y-%m-%d %H:%M')}"
        else:
            output += "\n|wStatus:|n |rPending Approval|n"
        
        # Description
        output += "\n\n" + divider("Description", text_color="|w")
        output += f"\n{equipment.description}"
        
        # First check for specialized details using composition approach
        details = equipment.specialized_details
        
        if details:
            # We found specialized details, so display them based on category
            category = equipment.category
            
            if category == 'melee':
                output += "\n\n" + divider("Weapon Details", text_color="|w")
                output += f"\n|wDamage:|n {details.damage}"
                output += f"\n|wDamage Type:|n {details.damage_type}"
                output += f"\n|wDifficulty:|n {details.difficulty}"
            
            elif category == 'ranged':
                output += "\n\n" + divider("Weapon Details", text_color="|w")
                output += f"\n|wDamage:|n {details.damage}"
                output += f"\n|wDamage Type:|n {details.damage_type}"
                output += f"\n|wRange:|n {details.range}"
                output += f"\n|wRate:|n {details.rate}"
                output += f"\n|wClip:|n {details.clip}"
            
            elif category == 'thrown':
                output += "\n\n" + divider("Weapon Details", text_color="|w")
                output += f"\n|wDamage:|n {details.damage}"
                output += f"\n|wDamage Type:|n {details.damage_type}"
                output += f"\n|wRange:|n {details.range}"
                output += f"\n|wDifficulty:|n {details.difficulty}"
            
            elif category == 'improvised':
                output += "\n\n" + divider("Weapon Details", text_color="|w")
                output += f"\n|wDamage:|n {details.damage}"
                output += f"\n|wDamage Type:|n {details.damage_type}"
                output += f"\n|wDifficulty:|n {details.difficulty}"
                output += f"\n|wBreak Chance:|n {details.break_chance}%"
            
            elif category == 'explosives':
                output += "\n\n" + divider("Explosive Details", text_color="|w")
                output += f"\n|wBlast Area:|n {details.blast_area}"
                output += f"\n|wBlast Power:|n {details.blast_power}"
                output += f"\n|wBurn:|n {'Yes' if details.burn else 'No'}"
                if details.notes:
                    output += f"\n|wNotes:|n {details.notes}"
            
            elif category == 'armor':
                output += "\n\n" + divider("Armor Details", text_color="|w")
                output += f"\n|wRating:|n {details.rating}"
                output += f"\n|wDexterity Penalty:|n {details.dexterity_penalty}"
                output += f"\n|wIs Shield:|n {'Yes' if details.is_shield else 'No'}"
                if details.is_shield:
                    output += f"\n|wShield Bonus:|n {details.shield_bonus}"
            
            elif category == 'landcraft':
                output += "\n\n" + divider("Vehicle Details", text_color="|w")
                output += f"\n|wVehicle Type:|n {details.vehicle_type.title()}"
                output += f"\n|wSafe Speed:|n {details.safe_speed}"
                output += f"\n|wMax Speed:|n {details.max_speed}"
                output += f"\n|wManeuver:|n {details.maneuver}"
                output += f"\n|wCrew:|n {details.crew}"
                output += f"\n|wDurability:|n {details.durability}"
                output += f"\n|wStructure:|n {details.structure}"
                output += f"\n|wMass Damage:|n {details.mass_damage}"
                output += f"\n|wPassenger Protection:|n {details.passenger_protection}"
                if details.weapons:
                    output += f"\n|wWeapons:|n {details.weapons}"
                output += f"\n|wRequired Skill:|n {details.requires_skill}"
        
        else:
            # Fall back to checking for legacy inheritance model
            if isinstance(equipment, MeleeWeapon):
                output += "\n\n" + divider("Weapon Details", text_color="|w")
                output += f"\n|wDamage:|n {equipment.damage}"
                output += f"\n|wDamage Type:|n {equipment.damage_type}"
                output += f"\n|wDifficulty:|n {equipment.difficulty}"
            
            elif isinstance(equipment, RangedWeapon):
                output += "\n\n" + divider("Weapon Details", text_color="|w")
                output += f"\n|wDamage:|n {equipment.damage}"
                output += f"\n|wDamage Type:|n {equipment.damage_type}"
                output += f"\n|wRange:|n {equipment.range}"
                output += f"\n|wRate:|n {equipment.rate}"
                output += f"\n|wClip:|n {equipment.clip}"
            
            # Add other specialized equipment types as needed
            elif equipment.category in ['melee', 'ranged', 'thrown', 'improvised', 'martial_arts']:
                output += "\n\n" + divider("Weapon Details", text_color="|w")
                output += "\n|yThis weapon's specific details aren't available.|n"
            elif equipment.category == 'explosives':
                output += "\n\n" + divider("Explosive Details", text_color="|w")
                output += "\n|yThis explosive's specific details aren't available.|n"
            elif equipment.category == 'armor':
                output += "\n\n" + divider("Armor Details", text_color="|w")
                output += "\n|yThis armor's specific details aren't available.|n"
            elif equipment.category == 'ammunition':
                output += "\n\n" + divider("Ammunition Details", text_color="|w")
                output += "\n|yThis ammunition's specific details aren't available.|n"
            elif equipment.category in ['landcraft', 'aircraft', 'seacraft', 'cycle', 'jetpack']:
                output += "\n\n" + divider("Vehicle Details", text_color="|w")
                output += "\n|yThis vehicle's specific details aren't available.|n"
            elif equipment.category in ['talisman', 'device', 'trinket', 'gadget', 'invention', 'matrix', 'grimoire', 'biotech', 'cybertech', 'periapt', 'chimerical', 'treasure', 'fetish', 'talen', 'artifact']:
                output += "\n\n" + divider("Supernatural Details", text_color="|w")
                output += "\n|yThis item's specific supernatural details aren't available.|n"
        
        # Command hints
        output += "\n\n" + divider("Commands", text_color="|w")
        if not item.is_proven:
            output += f"\n|wTo prove this item: |y+inv/prove {item.id}|n"
        
        output += "\n" + footer()
        self.caller.msg(output) 