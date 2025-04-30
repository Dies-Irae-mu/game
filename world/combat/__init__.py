"""
World of Darkness Combat System

This package provides a combat system for Evennia based on World of Darkness 20th Anniversary Edition rules.

Components:
- combat_handler.py: Script that manages combat state and processes actions
- combat_cmdset.py: Command set for character combat commands

To use in your game, add the CombatCmdSet to your character's default cmdset.
"""

from .combat_handler import CombatHandler

# Removed import from commands.combat_cmdset to avoid circular imports 