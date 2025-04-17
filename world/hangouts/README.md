# Hangouts System

The Hangouts System provides a way to categorize, organize, and list in-game locations where players can gather for roleplay in the Die Sirae game. This system helps players find active roleplay areas and discover new locations based on their interests or character types.

## Core Features

- **Location Directory**: Categorized listing of roleplay locations
- **Population Tracking**: Display of how many players are in each location
- **Restriction System**: Control visibility based on character type or faction
- **District Organization**: Organize locations by geographic regions

## Key Components

### Models

- `HangoutDB`: Proxy model for hangout objects with specialized methods
  - Manages hangout ID sequence
  - Provides filtering and visibility calculations
  - Manages display formatting

### Key Functions

- `create()`: Create new hangout entries
- `get_visible_hangouts()`: Filter hangouts based on character permissions
- `get_hangouts_by_category()`: Filter hangouts by category
- `get_display_entry()`: Format hangout information for display

### Categories

The system supports various categories of hangouts, including:
- Art
- Business
- Government
- Club
- Education
- Entertainment
- Gastronomy
- Health
- Landmarks
- Lodging
- Outdoors
- Religious
- Social
- Sports
- Store
- Transportation
- Faction
- Supernatural
- Vice

### Restriction System

Hangouts can be restricted based on:
- Character splat (Vampire, Werewolf, etc.)
- Required merits
- Faction membership
- Staff permissions

## Integration

The Hangouts system integrates with:
- Room system for location references
- Character system for permission checking
- Web interface for browsing locations

## Usage

Players can interact with the hangout system using the `+hangouts` command, which displays categorized lists of available locations. Staff can create and manage hangouts using administrative commands.

## Development

When developing new features for the hangout system, consider:
- Additional filtering options
- Enhanced display formats
- Integration with other location-based systems
- Web interface improvements
