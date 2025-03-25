"""
Management command to check character eligibility for weekly XP.
"""
from django.core.management.base import BaseCommand
from evennia.objects.models import ObjectDB
from evennia.utils import logger
from decimal import Decimal
from datetime import datetime, timedelta

class Command(BaseCommand):
    """
    Check all characters for weekly XP eligibility
    """
    help = "Check which characters are eligible for weekly XP awards"

    def handle(self, *args, **options):
        """
        Implementation of the command.
        """
        # Find all character objects
        characters = ObjectDB.objects.filter(
            db_typeclass_path__contains='typeclasses.characters.Character'
        )
        
        self.stdout.write(f"\nChecking {len(characters)} characters for weekly XP eligibility...")
        self.stdout.write("=" * 60)
        
        eligible_count = 0
        base_xp = Decimal('4.00')
        
        for char in characters:
            # Skip if character is staff
            if hasattr(char, 'check_permstring') and char.check_permstring("builders"):
                continue
                
            # Get character's XP data
            xp_data = None
            if hasattr(char, 'db') and hasattr(char.db, 'xp'):
                xp_data = char.db.xp
            if not xp_data:
                xp_data = char.attributes.get('xp')
                
            if not xp_data:
                self.stdout.write(f"{char.key}: No XP data found")
                continue
                
            # Check scenes this week
            scenes_this_week = xp_data.get('scenes_this_week', 0)
            
            # Get last scene time
            last_scene = None
            if xp_data.get('last_scene'):
                try:
                    last_scene = datetime.fromisoformat(xp_data['last_scene'])
                except (ValueError, TypeError):
                    last_scene = None
            
            # Print character status
            self.stdout.write(f"\nCharacter: {char.key}")
            self.stdout.write(f"Scenes this week: {scenes_this_week}")
            self.stdout.write(f"Last scene: {last_scene.strftime('%Y-%m-%d %H:%M') if last_scene else 'Never'}")
            
            # Check eligibility
            if scenes_this_week > 0:
                eligible_count += 1
                self.stdout.write(f"Status: ELIGIBLE for {base_xp} XP")
                
                # Calculate what their new totals would be
                current = Decimal(str(xp_data.get('current', '0.00')))
                total = Decimal(str(xp_data.get('total', '0.00')))
                ic_xp = Decimal(str(xp_data.get('ic_xp', '0.00')))
                
                self.stdout.write(f"Current XP: {current}")
                self.stdout.write(f"Would receive: +{base_xp} XP")
                self.stdout.write(f"New total would be: {current + base_xp}")
            else:
                self.stdout.write("Status: NOT ELIGIBLE - No scenes this week")
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"Summary: {eligible_count} characters eligible for weekly XP")
        self.stdout.write(f"Total XP that would be awarded: {base_xp * eligible_count}") 