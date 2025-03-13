from django.core.management.base import BaseCommand
from world.wod20th.models import MokoleArchidTrait

class Command(BaseCommand):
    help = 'Adds Mokolé Archid traits to the database'

    def handle(self, *args, **options):
        # Dictionary of traits with their properties
        traits = {
            'Resplendent Crest': {
                'description': '+3 to Appearance and +1 to Charisma.',
                'can_stack': False,
                'stat_modifiers': {'appearance': 3, 'charisma': 1},
            },
            'Armored Hide': {
                'description': '+2 to Stamina.',
                'can_stack': True,
                'stat_modifiers': {'stamina': 2},
            },
            'Massive Frame': {
                'description': '+2 to Strength.',
                'can_stack': True,
                'stat_modifiers': {'strength': 2},
            },
            'Serpentine Grace': {
                'description': '+2 to Dexterity.',
                'can_stack': True,
                'stat_modifiers': {'dexterity': 2},
            },
            'Imposing Presence': {
                'description': '+2 to Charisma.',
                'can_stack': True,
                'stat_modifiers': {'charisma': 2},
            },
            'Fearsome Aspect': {
                'description': '+2 to Intimidation.',
                'can_stack': True,
                'stat_modifiers': {'intimidation': 2},
            },
            'Natural Weapons': {
                'description': 'Claws (Str+1 L), Bite (Str+1 L), or Tail (Str B).',
                'can_stack': False,
                'special_rules': 'Choose one natural weapon type when taking this trait.',
            },
            'Venomous': {
                'description': 'Bite attack delivers venom (Stamina diff 8 or take 3 levels of lethal damage).',
                'can_stack': False,
                'special_rules': 'Requires Natural Weapons (Bite).',
            },
            'Wings': {
                'description': 'Capable of flight.',
                'can_stack': False,
                'special_rules': 'Flight speed equals running speed.',
            },
            'Aquatic Adaptation': {
                'description': 'Can breathe underwater and swim effectively.',
                'can_stack': False,
                'special_rules': 'Swimming speed equals running speed.',
            },
            'Enhanced Senses': {
                'description': '+2 to Perception.',
                'can_stack': True,
                'stat_modifiers': {'perception': 2},
            },
            'Prehensile Tail': {
                'description': 'Can use tail for basic manipulation.',
                'can_stack': False,
                'special_rules': 'Can perform simple tasks with tail at -2 penalty.',
            },
            'Thermal Vision': {
                'description': 'Can see heat signatures.',
                'can_stack': False,
                'special_rules': 'Reduces visibility penalties in darkness by 2.',
            },
            'Camouflage': {
                'description': '+2 to Stealth when stationary.',
                'can_stack': True,
                'stat_modifiers': {'stealth': 2},
            },
            'Reinforced Skull': {
                'description': 'Head butts do Str+2 B damage.',
                'can_stack': False,
                'special_rules': 'Can use head as a weapon.',
            },
        }

        for name, data in traits.items():
            try:
                trait, created = MokoleArchidTrait.objects.get_or_create(
                    name=name,
                    defaults={
                        'description': data['description'],
                        'can_stack': data.get('can_stack', False),
                        'stat_modifiers': data.get('stat_modifiers', {}),
                        'special_rules': data.get('special_rules', '')
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Successfully created trait "{name}"'))
                else:
                    # Update existing trait
                    trait.description = data['description']
                    trait.can_stack = data.get('can_stack', False)
                    trait.stat_modifiers = data.get('stat_modifiers', {})
                    trait.special_rules = data.get('special_rules', '')
                    trait.save()
                    self.stdout.write(self.style.SUCCESS(f'Successfully updated trait "{name}"'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to create/update trait "{name}": {str(e)}')) 