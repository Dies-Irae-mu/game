from evennia.utils.logger import log_info
from world.equipment.models import Equipment, MeleeWeapon, RangedWeapon, Armor, Explosive, SpecialAmmunition

def verify_equipment():
    """Verify all equipment in the database"""
    log_info("=== Verifying Equipment ===")
    
    # Get all equipment
    all_equipment = Equipment.objects.all()
    log_info(f"Total equipment items: {all_equipment.count()}")
    
    # Count by type
    melee_count = MeleeWeapon.objects.count()
    ranged_count = RangedWeapon.objects.count()
    armor_count = Armor.objects.count()
    explosive_count = Explosive.objects.count()
    special_ammo_count = SpecialAmmunition.objects.count()
    
    log_info(f"\nEquipment by type:")
    log_info(f"Melee Weapons: {melee_count}")
    log_info(f"Ranged Weapons: {ranged_count}")
    log_info(f"Armor: {armor_count}")
    log_info(f"Explosives: {explosive_count}")
    log_info(f"Special Ammunition: {special_ammo_count}")
    
    # List all equipment
    log_info("\nAll Equipment:")
    for eq in all_equipment:
        log_info(f"\nID: {eq.id}")
        log_info(f"Name: {eq.name}")
        log_info(f"Category: {eq.category}")
        log_info(f"Type: {eq.equipment_type}")
        log_info(f"Resources: {eq.resources}")
        log_info(f"Quantity: {eq.quantity}")
        log_info(f"Conceal: {eq.conceal}")
        log_info(f"Unique: {eq.is_unique}")
        log_info(f"Requires Approval: {eq.requires_approval}")
        
        if isinstance(eq, MeleeWeapon):
            log_info(f"Damage: {eq.damage}")
            log_info(f"Damage Type: {eq.damage_type}")
            log_info(f"Difficulty: {eq.difficulty}")
        elif isinstance(eq, RangedWeapon):
            log_info(f"Damage: {eq.damage}")
            log_info(f"Range: {eq.range}")
            log_info(f"Rate: {eq.rate}")
            log_info(f"Clip Size: {eq.clip}")
        elif isinstance(eq, Armor):
            log_info(f"Protection: {eq.protection}")
            log_info(f"Coverage: {eq.coverage}")
            log_info(f"Penalty: {eq.penalty}")
        elif isinstance(eq, Explosive):
            log_info(f"Damage: {eq.damage}")
            log_info(f"Blast Radius: {eq.blast_radius}")
            log_info(f"Fuse Time: {eq.fuse_time}")
        elif isinstance(eq, SpecialAmmunition):
            log_info(f"Damage: {eq.damage}")
            log_info(f"Special Effect: {eq.special_effect}")
            log_info(f"Duration: {eq.duration}")
        
        log_info("-" * 50)

if __name__ == "__main__":
    verify_equipment() 