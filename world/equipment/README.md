# Equipment System

The Equipment System manages all items, weapons, armor, vehicles, and supernatural devices in the Die Sirae game. This Django app provides a comprehensive framework for creating, managing, and using equipment in the World of Darkness setting.

## Core Features

- **Equipment Database**: Comprehensive model system for different types of equipment
- **Inventory Management**: Track character inventories and item ownership
- **Equipment Categories**: Support for various equipment types (weapons, armor, vehicles, supernatural items)
- **Approval Workflow**: Staff approval system for restricted items

## Key Components

### Models

- `Equipment`: Base model for all items with common attributes
- `PlayerInventory`: Tracks character ownership of equipment
- `InventoryItem`: Manages the relationship between players and items
- Specialized equipment types:
  - Combat: `MeleeWeapon`, `RangedWeapon`, `ThrownWeapon`, `ImprovisedWeapon`, `Explosive`, `Ammunition`
  - Vehicles: `Landcraft`, `Aircraft`, `Seacraft`, `Cycle`, `Jetpack`
  - Supernatural: `Talisman`, `Device`, `Trinket`, `Fetish`, `Artifact`
  - Utility: `TechnocraticDevice`, `SpyingDevice`, `CommunicationsDevice`, `SurvivalGear`

### Admin Interface

- Custom admin views for equipment management
- Batch equipment creation and modification

### Web Views

- Equipment catalog browsing
- Character inventory management

### Scripts

- `verify_equipment.py`: Tools for validating equipment data
- `inventory_dictionary.py`: Reference data for equipment creation

## Integration

This system integrates with the character system to provide inventory management and equipment effects on character abilities. Equipment can be equipped, used in combat, and have mechanical effects on gameplay.

## Usage

Equipment is primarily managed through in-game commands and the web admin interface. Players interact with equipment using the `+equip`, `+inventory`, and related commands defined in the commands directory.

## Development

When adding new equipment types, extend the appropriate equipment model and implement any specialized behavior needed for that equipment type.
