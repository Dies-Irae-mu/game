"""
Functions for initializing background stats in the database.
"""
from world.wod20th.models import Stat
from world.wod20th.utils.stat_mappings import (
    UNIVERSAL_BACKGROUNDS, VAMPIRE_BACKGROUNDS, CHANGELING_BACKGROUNDS,
    MAGE_BACKGROUNDS, TECHNOCRACY_BACKGROUNDS, TRADITIONS_BACKGROUNDS,
    NEPHANDI_BACKGROUNDS, SHIFTER_BACKGROUNDS, SORCERER_BACKGROUNDS
)

def initialize_backgrounds():
    """Initialize all background stats in the database."""
    # Initialize universal backgrounds
    for bg in UNIVERSAL_BACKGROUNDS:
        try:
            # Set instanced=True for backgrounds that require an instance
            instanced = True if bg in ['Library', 'Status', 'Influence'] else None
            
            Stat.objects.update_or_create(
                name=bg,
                stat_type='background',
                defaults={
                    'category': 'backgrounds',
                    'game_line': 'Various',
                    'values': [1, 2, 3, 4, 5],
                    'instanced': instanced
                }
            )
        except Exception as e:
            print(f"Error initializing background {bg}: {e}")

    # Initialize vampire backgrounds
    for bg in VAMPIRE_BACKGROUNDS:
        try:
            # Set instanced=True for backgrounds that require an instance
            instanced = True if bg in ['Status', 'Influence'] else None
            
            Stat.objects.update_or_create(
                name=bg,
                stat_type='background',
                defaults={
                    'category': 'backgrounds',
                    'game_line': 'Vampire: The Masquerade',
                    'splat': 'Vampire',
                    'values': [1, 2, 3, 4, 5],
                    'instanced': instanced
                }
            )
        except Exception as e:
            print(f"Error initializing vampire background {bg}: {e}")

    # Initialize changeling backgrounds
    for bg in CHANGELING_BACKGROUNDS:
        try:
            # Set instanced=True for backgrounds that require an instance
            instanced = True if bg in ['Status', 'Influence'] else None
            
            Stat.objects.update_or_create(
                name=bg,
                stat_type='background',
                defaults={
                    'category': 'backgrounds',
                    'game_line': 'Changeling: The Dreaming',
                    'splat': 'Changeling',
                    'values': [1, 2, 3, 4, 5],
                    'instanced': instanced
                }
            )
        except Exception as e:
            print(f"Error initializing changeling background {bg}: {e}")

    # Initialize mage backgrounds
    for bg in MAGE_BACKGROUNDS:
        try:
            # Set instanced=True for backgrounds that require an instance
            instanced = True if bg in ['Status', 'Influence', 'Library'] else None
            
            Stat.objects.update_or_create(
                name=bg,
                stat_type='background',
                defaults={
                    'category': 'backgrounds',
                    'game_line': 'Mage: The Ascension',
                    'splat': 'Mage',
                    'values': [1, 2, 3, 4, 5],
                    'instanced': instanced
                }
            )
        except Exception as e:
            print(f"Error initializing mage background {bg}: {e}")

    # Initialize technocracy backgrounds
    for bg in TECHNOCRACY_BACKGROUNDS:
        try:
            # Set instanced=True for backgrounds that require an instance
            instanced = True if bg in ['Status', 'Influence', 'Library'] else None
            
            Stat.objects.update_or_create(
                name=bg,
                stat_type='background',
                defaults={
                    'category': 'backgrounds',
                    'game_line': 'Mage: The Ascension',
                    'splat': 'Mage',
                    'values': [1, 2, 3, 4, 5],
                    'instanced': instanced
                }
            )
        except Exception as e:
            print(f"Error initializing technocracy background {bg}: {e}")

    # Initialize traditions backgrounds
    for bg in TRADITIONS_BACKGROUNDS:
        try:
            # Set instanced=True for backgrounds that require an instance
            instanced = True if bg in ['Status', 'Influence', 'Library'] else None
            
            Stat.objects.update_or_create(
                name=bg,
                stat_type='background',
                defaults={
                    'category': 'backgrounds',
                    'game_line': 'Mage: The Ascension',
                    'splat': 'Mage',
                    'values': [1, 2, 3, 4, 5],
                    'instanced': instanced
                }
            )
        except Exception as e:
            print(f"Error initializing traditions background {bg}: {e}")

    # Initialize nephandi backgrounds
    for bg in NEPHANDI_BACKGROUNDS:
        try:
            # Set instanced=True for backgrounds that require an instance
            instanced = True if bg in ['Status', 'Influence', 'Library'] else None
            
            Stat.objects.update_or_create(
                name=bg,
                stat_type='background',
                defaults={
                    'category': 'backgrounds',
                    'game_line': 'Mage: The Ascension',
                    'splat': 'Mage',
                    'values': [1, 2, 3, 4, 5],
                    'instanced': instanced
                }
            )
        except Exception as e:
            print(f"Error initializing nephandi background {bg}: {e}")

    # Initialize shifter backgrounds
    for bg in SHIFTER_BACKGROUNDS:
        try:
            # Set instanced=True for backgrounds that require an instance
            instanced = True if bg in ['Status', 'Influence'] else None
            
            Stat.objects.update_or_create(
                name=bg,
                stat_type='background',
                defaults={
                    'category': 'backgrounds',
                    'game_line': 'Werewolf: The Apocalypse',
                    'splat': 'Shifter',
                    'values': [1, 2, 3, 4, 5],
                    'instanced': instanced
                }
            )
        except Exception as e:
            print(f"Error initializing shifter background {bg}: {e}")

    # Initialize sorcerer backgrounds
    for bg in SORCERER_BACKGROUNDS:
        try:
            # Set instanced=True for backgrounds that require an instance
            instanced = True if bg in ['Status', 'Influence', 'Library'] else None
            
            Stat.objects.update_or_create(
                name=bg,
                stat_type='background',
                defaults={
                    'category': 'backgrounds',
                    'game_line': 'Sorcerer',
                    'splat': 'Mortal+',
                    'values': [1, 2, 3, 4, 5],
                    'instanced': instanced
                }
            )
        except Exception as e:
            print(f"Error initializing sorcerer background {bg}: {e}")

    print("Background stats initialized successfully.") 