# Jobs System

The Jobs System provides a comprehensive ticket management system for handling player requests, bug reports, and staff tasks in the Die Sirae game. This Django app enables organized tracking and processing of game-related tasks.

## Core Features

- **Ticket Management**: Create, track, and resolve player-submitted requests
- **Queue Organization**: Categorize jobs by type and department
- **Assignment Workflow**: Assign jobs to staff members for processing
- **Templating System**: Create standardized job formats for common tasks
- **Archiving**: Store completed jobs for future reference

## Key Components

### Models

- `Job`: Core model representing a task or request
- `Queue`: Categories for organizing different types of jobs
- `JobTemplate`: Templates for standardized job creation
- `JobAttachment`: Objects attached to a job for reference
- `ArchivedJob`: Completed jobs preserved for historical record

### Key Fields

- **Job Information**:
  - Title and description
  - Requester and assignee
  - Status tracking
  - Comments and updates
  - Creation and close timestamps
  - Templated arguments
  - View tracking

- **Template System**:
  - Predefined argument structure
  - Close commands for automated actions
  - Queue assignment

- **Queues**:
  - Named categories
  - Automatic assignee options

### Workflow States

Jobs proceed through various states:
1. **Open**: Newly created, awaiting assignment
2. **Claimed**: Assigned to a staff member
3. **Closed**: Completed and closed
4. **Rejected**: Closed without approval
5. **Cancelled**: Terminated before completion
6. **Completed**: Successfully resolved

## Integration

The Jobs system integrates with:
- Account system for requesters and assignees
- Object system for attachments
- Mail system for notifications
- Web interface for management

## Usage

Jobs are managed through in-game commands and a web interface. Players can create requests with the `+request` command, while staff manage jobs through the `+jobs` command set defined in the commands directory.

## Development

When extending the jobs system, consider:
- Additional automation for common job types
- Enhanced reporting and metrics
- Improved templates for specific game functions
- Integration with other game systems for automated resolution
