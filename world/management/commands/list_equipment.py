from django.core.management.base import BaseCommand
from world.equipment.models import Equipment, MeleeWeapon, RangedWeapon, Armor, Vehicle, Explosive, SpecialAmmunition

class Command(BaseCommand):
    help = 'Lists all imported equipment with their details'

    def handle(self, *args, **options):
        self.stdout.write("\n=== All Equipment ===")
        for eq in Equipment.objects.all():
            self.stdout.write(f"\nID: {eq.id}")
            self.stdout.write(f"Name: {eq.name}")
            self.stdout.write(f"Category: {eq.category}")
            self.stdout.write(f"Type: {eq.equipment_type}")
            self.stdout.write(f"Description: {eq.description}")
            self.stdout.write(f"Resources: {eq.resources}")
            self.stdout.write(f"Quantity: {eq.quantity}")
            self.stdout.write(f"Conceal: {eq.conceal}")
            self.stdout.write(f"Unique: {eq.is_unique}")
            self.stdout.write(f"Requires Approval: {eq.requires_approval}")

            if isinstance(eq, MeleeWeapon):
                self.stdout.write(f"Damage: {eq.damage}")
                self.stdout.write(f"Damage Type: {eq.damage_type}")
                self.stdout.write(f"Difficulty: {eq.difficulty}")
            elif isinstance(eq, RangedWeapon):
                self.stdout.write(f"Damage: {eq.damage}")
                self.stdout.write(f"Range: {eq.range}")
                self.stdout.write(f"Rate: {eq.rate}")
                self.stdout.write(f"Clip Size: {eq.clip}")
            elif isinstance(eq, Armor):
                self.stdout.write(f"Protection: {eq.protection}")
                self.stdout.write(f"Coverage: {eq.coverage}")
                self.stdout.write(f"Penalty: {eq.penalty}")
            elif isinstance(eq, Vehicle):
                self.stdout.write(f"Speed: {eq.speed}")
                self.stdout.write(f"Handling: {eq.handling}")
                self.stdout.write(f"Capacity: {eq.capacity}")
                self.stdout.write(f"Armor: {eq.armor}")
            elif isinstance(eq, Explosive):
                self.stdout.write(f"Damage: {eq.damage}")
                self.stdout.write(f"Blast Radius: {eq.blast_radius}")
                self.stdout.write(f"Fuse Time: {eq.fuse_time}")
            elif isinstance(eq, SpecialAmmunition):
                self.stdout.write(f"Damage: {eq.damage}")
                self.stdout.write(f"Special Effect: {eq.special_effect}")
                self.stdout.write(f"Duration: {eq.duration}")

            self.stdout.write("-" * 50) 