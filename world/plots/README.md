# Plots System

The Plots System manages storyteller-driven plot lines and story arcs in the Die Sirae game. This Django app enables the creation, tracking, and organization of game plots and their related sessions, providing structure for narrative content.

## Core Features

- **Plot Management**: Track ongoing storylines and narratives
- **Session Organization**: Manage individual plot sessions and events
- **Storyteller Assignment**: Assign plots to specific storytellers
- **Participant Tracking**: Track character involvement in plots
- **Reward Management**: Document payouts and rewards for participation

## Key Components

### Models

- `Plot`: Core model representing a narrative arc or storyline
  - Title and description
  - Status tracking
  - Risk level and genre classification
  - Reward information
  - Scheduling details

- `Session`: Individual gatherings or events within a plot
  - Date and duration
  - Location information
  - Participant tracking
  - Public and secret information

### Plot Statuses

Plots can exist in various states:
- **New**: Recently created, not yet active
- **Active**: Currently running
- **Inactive**: Temporarily paused
- **On Hold**: Suspended for longer periods
- **Completed**: Successfully concluded
- **Cancelled**: Terminated before completion

### Risk Levels

Plots are categorized by risk level:
- **Low**: Minimal danger to characters
- **Moderate**: Some risk involved
- **High**: Significant danger to characters
- **Extreme**: Potentially lethal situation

## Display Formats

The system supports various display formats for plots and sessions:
- Plot listings with status information
- Detailed plot views with all plot metadata
- Session listings with scheduling information
- Session details with descriptions and participant information

## Integration

The Plots system integrates with:
- Character system for participant tracking
- Account system for storyteller assignment
- Calendar/events system for scheduling
- XP system for rewards

## Usage

Plots are managed through in-game commands. Players can view available plots and sign up for participation, while storytellers and staff can create and manage plots through the `+plots` command set defined in the commands directory.

## Development

When extending the plots system, consider:
- Enhanced scheduling features
- Integration with scene logging
- Automated XP rewards
- Plot arc grouping for connected storylines
