from evennia.utils.logger import log_info
from world.equipment.models import (
    Equipment, MeleeWeapon, RangedWeapon, ThrownWeapon, ImprovisedWeapon,
    Explosive, SpecialAmmunition, Armor, Ammunition, TechnocraticDevice,
    MartialArtsWeapon, SpyingDevice, CommunicationsDevice, SurvivalGear,
    ElectronicDevice, Cycle, Landcraft, Seacraft, Talisman, Device, Trinket,
    Gadget, Invention, Matrix, Grimoire, Biotech, Cybertech, Periapt,
    Chimerical, Treasure, Fetish, Talen, Artifact, Jetpack, Aircraft,
    InventoryItem, PlayerInventory,
    # Import new composition-based detail models
    MeleeWeaponDetails, RangedWeaponDetails, ThrownWeaponDetails, ImprovisedWeaponDetails,
    ExplosiveDetails, ArmorDetails, AmmunitionDetails, SpecialAmmunitionDetails,
    TechnocraticDeviceDetails, MartialArtsWeaponDetails, SpyingDeviceDetails,
    CommunicationsDeviceDetails, SurvivalGearDetails, ElectronicDeviceDetails,
    LandcraftDetails, AircraftDetails, SeacraftDetails, CycleDetails, JetpackDetails,
    SupernaturalItemDetails
)
from world.equipment.inventory_dictionary import inventory_dictionary
from django.db import transaction
from django.db import models

def import_equipment(cleanup=True, use_composition=True):
    """
    Import equipment from the inventory dictionary into the database.
    
    Args:
        cleanup (bool): If True, delete existing equipment before importing. If False, keep existing equipment.
        use_composition (bool): If True, use the new composition-based approach for equipment details.
    """
    print("Starting equipment import...")
    log_info("Starting equipment import...")
    
    equipment_count = 0
    current_seq_id = 1  # Initialize sequential ID counter
    
    try:
        with transaction.atomic():
            if cleanup:
                # Delete all related objects first
                print("Cleaning up existing inventory items...")
                inventory_count = InventoryItem.objects.all().count()
                InventoryItem.objects.all().delete()
                print(f"Deleted {inventory_count} inventory items")
                
                print("Cleaning up existing player inventories...")
                inventory_count = PlayerInventory.objects.all().count()
                PlayerInventory.objects.all().delete()
                print(f"Deleted {inventory_count} player inventories")
                
                # Delete all detail records if using composition
                if use_composition:
                    print("Cleaning up composition-based detail records...")
                    detail_models = [
                        MeleeWeaponDetails, RangedWeaponDetails, ThrownWeaponDetails, ImprovisedWeaponDetails,
                        ExplosiveDetails, ArmorDetails, AmmunitionDetails, SpecialAmmunitionDetails,
                        TechnocraticDeviceDetails, MartialArtsWeaponDetails, SpyingDeviceDetails,
                        CommunicationsDeviceDetails, SurvivalGearDetails, ElectronicDeviceDetails,
                        LandcraftDetails, AircraftDetails, SeacraftDetails, CycleDetails, JetpackDetails,
                        SupernaturalItemDetails
                    ]
                    total_details_deleted = 0
                    for model in detail_models:
                        count = model.objects.all().count()
                        model.objects.all().delete()
                        total_details_deleted += count
                        print(f"Deleted {count} {model.__name__} records")
                    print(f"Total detail records deleted: {total_details_deleted}")
                
                # Delete all equipment types (for backward compatibility)
                print("Cleaning up existing equipment...")
                total_deleted = 0
                for model in [
                    Explosive, SpecialAmmunition, Armor, Ammunition,
                    TechnocraticDevice, MartialArtsWeapon, SpyingDevice,
                    CommunicationsDevice, SurvivalGear, ElectronicDevice,
                    Cycle, Landcraft, Seacraft, Talisman, Device, Trinket,
                    Gadget, Invention, Matrix, Grimoire, Biotech, Cybertech,
                    Periapt, Chimerical, Treasure, Fetish, Talen, Artifact,
                    Jetpack, Aircraft, MeleeWeapon, RangedWeapon, ThrownWeapon,
                    ImprovisedWeapon
                ]:
                    count = model.objects.all().count()
                    model.objects.all().delete()
                    total_deleted += count
                    print(f"Deleted {count} {model.__name__} items")
                
                # Finally delete base Equipment objects
                base_count = Equipment.objects.all().count()
                Equipment.objects.all().delete()
                print(f"Deleted {base_count} base Equipment items")
                print(f"Total items deleted: {total_deleted + base_count}")
            else:
                print("Skipping cleanup, keeping existing equipment...")
                # Get the highest sequential ID from existing equipment
                max_seq_id = Equipment.objects.all().aggregate(models.Max('sequential_id'))['sequential_id__max']
                if max_seq_id is not None:
                    current_seq_id = max_seq_id + 1
                    print(f"Starting new sequential IDs from {current_seq_id}")
            
            # Create new equipment from dictionary
            print("\nCreating new equipment...")
            print("-" * 50)
            
            # Sort the dictionary items to ensure consistent sequential IDs
            sorted_items = sorted(inventory_dictionary.items(), key=lambda x: x[0])
            
            for key, data in sorted_items:
                try:
                    if isinstance(data, dict):
                        # Handle dictionary entries (explosives, special ammunition, armor)
                        if data.get('category') == 'explosives':
                            if use_composition:
                                # Create base equipment object
                                equipment = Equipment.objects.create(
                                    sequential_id=current_seq_id,
                                    name=data['name'],
                                    description=data['description'],
                                    resources=data['resources'],
                                    quantity=data.get('quantity', 1),
                                    conceal=data['conceal'],
                                    equipment_type=data['equipment_type'],
                                    category=data['category'],
                                    is_unique=data['is_unique'],
                                    requires_approval=data['requires_approval']
                                )
                                
                                # Create specialized details
                                ExplosiveDetails.objects.create(
                                    equipment=equipment,
                                    blast_area=data['blast_area'],
                                    blast_power=data['blast_power'],
                                    burn=data['burn'],
                                    notes=data['notes']
                                )
                            else:
                                # For backward compatibility
                                equipment = Explosive.objects.create(
                                    sequential_id=current_seq_id,  # Add sequential ID
                                    name=data['name'],
                                    description=data['description'],
                                    resources=data['resources'],
                                    quantity=data.get('quantity', 1),
                                    conceal=data['conceal'],
                                    equipment_type=data['equipment_type'],
                                    category=data['category'],
                                    is_unique=data['is_unique'],
                                    requires_approval=data['requires_approval'],
                                    blast_area=data['blast_area'],
                                    blast_power=data['blast_power'],
                                    burn=data['burn'],
                                    notes=data['notes']
                                )
                            print(f"Created Explosive: {equipment.name} (ID: {current_seq_id})")
                            equipment_count += 1
                            current_seq_id += 1
                            
                        elif data.get('category') == 'ammunition':
                            if use_composition:
                                # Create base equipment object
                                equipment = Equipment.objects.create(
                                    sequential_id=current_seq_id,
                                    name=data['name'],
                                    description=data['description'],
                                    resources=data['resources'],
                                    quantity=data.get('quantity', 1),
                                    conceal=data['conceal'],
                                    equipment_type=data['equipment_type'],
                                    category=data['category'],
                                    is_unique=data['is_unique'],
                                    requires_approval=data['requires_approval']
                                )
                                
                                # Create specialized details
                                SpecialAmmunitionDetails.objects.create(
                                    equipment=equipment,
                                    damage=data['damage'],
                                    effects=data['effects']
                                )
                            else:
                                # For backward compatibility
                                equipment = SpecialAmmunition.objects.create(
                                    sequential_id=current_seq_id,  # Add sequential ID
                                    name=data['name'],
                                    description=data['description'],
                                    resources=data['resources'],
                                    quantity=data.get('quantity', 1),
                                    conceal=data['conceal'],
                                    equipment_type=data['equipment_type'],
                                    category=data['category'],
                                    is_unique=data['is_unique'],
                                    requires_approval=data['requires_approval'],
                                    damage=data['damage'],
                                    effects=data['effects']
                                )
                            print(f"Created Special Ammunition: {equipment.name} (ID: {current_seq_id})")
                            equipment_count += 1
                            current_seq_id += 1
                            
                        elif data.get('category') == 'armor':
                            if use_composition:
                                # Create base equipment object
                                equipment = Equipment.objects.create(
                                    sequential_id=current_seq_id,
                                    name=data['name'],
                                    description=data['description'],
                                    resources=data['resources'],
                                    quantity=data.get('quantity', 1),
                                    conceal=data['conceal'],
                                    equipment_type=data['equipment_type'],
                                    category=data['category'],
                                    is_unique=data['is_unique'],
                                    requires_approval=data['requires_approval']
                                )
                                
                                # Create specialized details
                                ArmorDetails.objects.create(
                                    equipment=equipment,
                                    rating=data['rating'],
                                    dexterity_penalty=data['dexterity_penalty'],
                                    is_shield=data['is_shield'],
                                    shield_bonus=data['shield_bonus']
                                )
                            else:
                                # For backward compatibility
                                equipment = Armor.objects.create(
                                    sequential_id=current_seq_id,  # Add sequential ID
                                    name=data['name'],
                                    description=data['description'],
                                    resources=data['resources'],
                                    quantity=data.get('quantity', 1),
                                    conceal=data['conceal'],
                                    equipment_type=data['equipment_type'],
                                    category=data['category'],
                                    is_unique=data['is_unique'],
                                    requires_approval=data['requires_approval'],
                                    rating=data['rating'],
                                    dexterity_penalty=data['dexterity_penalty'],
                                    is_shield=data['is_shield'],
                                    shield_bonus=data['shield_bonus']
                                )
                            print(f"Created Armor: {equipment.name} (ID: {current_seq_id})")
                            equipment_count += 1
                            current_seq_id += 1
                            
                    else:
                        # Handle model instances by creating new instances in the database
                        # First, ensure quantity is set
                        quantity = 1
                        if hasattr(data, 'quantity') and data.quantity is not None:
                            quantity = data.quantity
                            
                        # Handle melee weapons
                        if isinstance(data, MeleeWeapon):
                            if use_composition:
                                # Create base equipment object
                                equipment = Equipment.objects.create(
                                    sequential_id=current_seq_id,
                                    name=data.name,
                                    description=data.description,
                                    resources=data.resources,
                                    quantity=quantity,
                                    conceal=data.conceal,
                                    equipment_type=data.equipment_type,
                                    category=data.category,
                                    is_unique=data.is_unique,
                                    requires_approval=data.requires_approval
                                )
                                
                                # Create specialized details
                                MeleeWeaponDetails.objects.create(
                                    equipment=equipment,
                                    damage=data.damage,
                                    damage_type=data.damage_type,
                                    difficulty=data.difficulty
                                )
                            else:
                                # For backward compatibility
                                equipment = MeleeWeapon.objects.create(
                                    sequential_id=current_seq_id,
                                    name=data.name,
                                    description=data.description,
                                    resources=data.resources,
                                    quantity=quantity,
                                    conceal=data.conceal,
                                    equipment_type=data.equipment_type,
                                    category=data.category,
                                    is_unique=data.is_unique,
                                    requires_approval=data.requires_approval,
                                    damage=data.damage,
                                    damage_type=data.damage_type,
                                    difficulty=data.difficulty
                                )
                            print(f"Created MeleeWeapon: {equipment.name} (ID: {current_seq_id})")
                            
                        # Handle ranged weapons
                        elif isinstance(data, RangedWeapon):
                            if use_composition:
                                # Create base equipment object
                                equipment = Equipment.objects.create(
                                    sequential_id=current_seq_id,
                                    name=data.name,
                                    description=data.description,
                                    resources=data.resources,
                                    quantity=quantity,
                                    conceal=data.conceal,
                                    equipment_type=data.equipment_type,
                                    category=data.category,
                                    is_unique=data.is_unique,
                                    requires_approval=data.requires_approval
                                )
                                
                                # Create specialized details
                                RangedWeaponDetails.objects.create(
                                    equipment=equipment,
                                    damage=data.damage,
                                    damage_type=data.damage_type,
                                    range=data.range,
                                    rate=data.rate,
                                    clip=data.clip
                                )
                            else:
                                # For backward compatibility
                                equipment = RangedWeapon.objects.create(
                                    sequential_id=current_seq_id,
                                    name=data.name,
                                    description=data.description,
                                    resources=data.resources,
                                    quantity=quantity,
                                    conceal=data.conceal,
                                    equipment_type=data.equipment_type,
                                    category=data.category,
                                    is_unique=data.is_unique,
                                    requires_approval=data.requires_approval,
                                    damage=data.damage,
                                    damage_type=data.damage_type,
                                    range=data.range,
                                    rate=data.rate,
                                    clip=data.clip
                                )
                            print(f"Created RangedWeapon: {equipment.name} (ID: {current_seq_id})")
                            
                        # Handle thrown weapons
                        elif isinstance(data, ThrownWeapon):
                            if use_composition:
                                # Create base equipment object
                                equipment = Equipment.objects.create(
                                    sequential_id=current_seq_id,
                                    name=data.name,
                                    description=data.description,
                                    resources=data.resources,
                                    quantity=quantity,
                                    conceal=data.conceal,
                                    equipment_type=data.equipment_type,
                                    category=data.category,
                                    is_unique=data.is_unique,
                                    requires_approval=data.requires_approval
                                )
                                
                                # Create specialized details
                                ThrownWeaponDetails.objects.create(
                                    equipment=equipment,
                                    damage=data.damage,
                                    damage_type=data.damage_type,
                                    range=data.range,
                                    difficulty=data.difficulty
                                )
                            else:
                                # For backward compatibility
                                equipment = ThrownWeapon.objects.create(
                                    sequential_id=current_seq_id,
                                    name=data.name,
                                    description=data.description,
                                    resources=data.resources,
                                    quantity=quantity,
                                    conceal=data.conceal,
                                    equipment_type=data.equipment_type,
                                    category=data.category,
                                    is_unique=data.is_unique,
                                    requires_approval=data.requires_approval,
                                    damage=data.damage,
                                    damage_type=data.damage_type,
                                    range=data.range,
                                    difficulty=data.difficulty
                                )
                            print(f"Created ThrownWeapon: {equipment.name} (ID: {current_seq_id})")
                            
                        # Handle improvised weapons
                        elif isinstance(data, ImprovisedWeapon):
                            if use_composition:
                                # Create base equipment object
                                equipment = Equipment.objects.create(
                                    sequential_id=current_seq_id,
                                    name=data.name,
                                    description=data.description,
                                    resources=data.resources,
                                    quantity=quantity,
                                    conceal=data.conceal,
                                    equipment_type=data.equipment_type,
                                    category=data.category,
                                    is_unique=data.is_unique,
                                    requires_approval=data.requires_approval
                                )
                                
                                # Create specialized details
                                ImprovisedWeaponDetails.objects.create(
                                    equipment=equipment,
                                    damage=data.damage,
                                    damage_type=data.damage_type,
                                    difficulty=data.difficulty,
                                    break_chance=data.break_chance
                                )
                            else:
                                # For backward compatibility
                                equipment = ImprovisedWeapon.objects.create(
                                    sequential_id=current_seq_id,
                                    name=data.name,
                                    description=data.description,
                                    resources=data.resources,
                                    quantity=quantity,
                                    conceal=data.conceal,
                                    equipment_type=data.equipment_type,
                                    category=data.category,
                                    is_unique=data.is_unique,
                                    requires_approval=data.requires_approval,
                                    damage=data.damage,
                                    damage_type=data.damage_type,
                                    difficulty=data.difficulty,
                                    break_chance=data.break_chance
                                )
                            print(f"Created ImprovisedWeapon: {equipment.name} (ID: {current_seq_id})")
                        
                        # Handle landcraft
                        elif isinstance(data, Landcraft):
                            if use_composition:
                                # Create base equipment object
                                equipment = Equipment.objects.create(
                                    sequential_id=current_seq_id,
                                    name=data.name,
                                    description=data.description,
                                    resources=data.resources,
                                    quantity=quantity,
                                    conceal=data.conceal,
                                    equipment_type=data.equipment_type,
                                    category=data.category,
                                    is_unique=data.is_unique,
                                    requires_approval=data.requires_approval
                                )
                                
                                # Create specialized details
                                LandcraftDetails.objects.create(
                                    equipment=equipment,
                                    safe_speed=data.safe_speed,
                                    max_speed=data.max_speed,
                                    maneuver=data.maneuver,
                                    crew=data.crew,
                                    durability=data.durability,
                                    structure=data.structure,
                                    weapons=data.weapons,
                                    mass_damage=data.mass_damage,
                                    passenger_protection=data.passenger_protection,
                                    vehicle_type=data.vehicle_type,
                                    requires_skill=data.requires_skill if hasattr(data, 'requires_skill') else "Drive"
                                )
                            else:
                                # For backward compatibility
                                equipment = Landcraft.objects.create(
                                    sequential_id=current_seq_id,
                                    name=data.name,
                                    description=data.description,
                                    resources=data.resources,
                                    quantity=quantity,
                                    conceal=data.conceal,
                                    equipment_type=data.equipment_type,
                                    category=data.category,
                                    is_unique=data.is_unique,
                                    requires_approval=data.requires_approval,
                                    safe_speed=data.safe_speed,
                                    max_speed=data.max_speed,
                                    maneuver=data.maneuver,
                                    crew=data.crew,
                                    durability=data.durability,
                                    structure=data.structure,
                                    weapons=data.weapons,
                                    mass_damage=data.mass_damage,
                                    passenger_protection=data.passenger_protection,
                                    vehicle_type=data.vehicle_type,
                                    requires_skill=data.requires_skill if hasattr(data, 'requires_skill') else "Drive"
                                )
                            print(f"Created Landcraft: {equipment.name} (ID: {current_seq_id})")
                            
                        # Handle vehicle types - similar pattern for each other type
                        # Here we're just showing Landcraft as an example
                        # You would use the same pattern for all other types
                        
                        # [Add similar blocks for other equipment types]
                        
                        # For any other type or unhandled type, create a base Equipment object
                        else:
                            # Just create base equipment - no specialized details
                            equipment = Equipment.objects.create(
                                sequential_id=current_seq_id,
                                name=data.name,
                                description=data.description,
                                resources=data.resources,
                                quantity=quantity,
                                conceal=data.conceal,
                                equipment_type=data.equipment_type,
                                category=data.category,
                                is_unique=data.is_unique,
                                requires_approval=data.requires_approval
                            )
                            print(f"Created generic Equipment: {equipment.name} (ID: {current_seq_id})")
                        
                        equipment_count += 1
                        current_seq_id += 1
                        
                except Exception as e:
                    print(f"Error importing {key}: {str(e)}")
                    log_info(f"Error importing {key}: {str(e)}")
                    raise
            
            print("-" * 50)
            print(f"Equipment import completed successfully.")
            print(f"Total items imported: {equipment_count}")
            log_info(f"Equipment import completed successfully. Total items imported: {equipment_count}")
            
    except Exception as e:
        print(f"Error during equipment import: {str(e)}")
        log_info(f"Error during equipment import: {str(e)}")
        raise

if __name__ == "__main__":
    import_equipment(use_composition=True)  # Set to True to use the composition-based approach 