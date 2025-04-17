# Groups System

The Groups System manages character organizations, factions, and social structures in the Die Sirae game. This Django app enables the creation and management of in-character groups like vampire covens, werewolf packs, mage cabals, and other organizations.

## Core Features

- **Group Management**: Create and manage in-game groups
- **Membership System**: Track characters in groups with roles and permissions
- **Leadership Structure**: Define group hierarchies and leadership positions
- **Integration with Rosters**: Link groups to character rosters

## Key Components

### Models

- `Group`: Core model representing an organization with its properties
- `GroupRole`: Defined roles within a group with associated permissions
- `GroupMembership`: Relationship between characters and groups
- `GroupJoinRequest`: Request system for characters wanting to join groups
- `CharacterGroupInfo`: Additional group information specific to characters

### Key Fields

- **Group Information**:
  - Name, description, IC description
  - Leader
  - Public visibility settings
  - Group ID for reference

- **Role Permissions**:
  - Invite permissions
  - Kick permissions
  - Promotion permissions
  - Information editing permissions

- **Character Information**:
  - Group membership
  - Character title within group
  - Role assignment

## Integration

The Groups system integrates with:
- Character system for membership information
- Rosters system for organization into spheres
- Communication system for group-specific channels

## Usage

Groups are managed through in-game commands and potentially a web interface. Players can interact with groups using the `+groups` command set defined in the commands directory.

## Typical Groups in World of Darkness

- **Vampire**: Covens, coteries, sects, clans
- **Werewolf**: Packs, tribes, septs
- **Mage**: Cabals, traditions, conventions
- **Changeling**: Motleys, courts, houses
- **Hunter**: Cells, compacts, conspiracies
- **Mortal**: Gangs, families, corporations, cults

## Development

When extending the groups system, consider implementing specialized behavior for different supernatural types' organizational structures.
