# Bulletin Board System (BBS) Commands and Functionality

This repository contains a set of command modules for managing a Bulletin Board System (BBS) within an Evennia-based MUD (Multi-User Dungeon) game. The BBS system allows players and administrators to create, manage, and interact with message boards and posts.

## Files Overview

### 1. `commands/bbs/bbs_admin_commands.py`

This module provides administrative commands for managing the entire BBS system. It includes commands that are restricted to users with specific permissions (typically administrators).

- **CmdResetBBS**: 
  - **Description**: Reinitializes the BBSController, effectively wiping all boards and posts.
  - **Usage**: `+bbs/reset`
  - **Permissions**: Requires "Admin" permissions.

### 2. `commands/bbs/bbs_all_commands.py`

This module includes general commands that allow users to interact with the BBS, including posting, reading, and editing posts.

- **CmdPost**: 
  - **Description**: Allows a user to post a message on a specified board.
  - **Usage**: `+bbs/post <board_name_or_number>/<title> = <content>`
  - **Permissions**: Available to all users, but write access is required on the board.

- **CmdReadBBS**: 
  - **Description**: Lists all boards, posts within a board, or reads a specific post.
  - **Usage**: 
    - `+bbs`: Lists all boards.
    - `+bbs <board_name_or_number>`: Lists all posts in the specified board.
    - `+bbs <board_number>/<post_number>`: Reads a specific post.
  - **Permissions**: Available to all users.

- **CmdEditPost**: 
  - **Description**: Allows a user to edit a post they authored or if they are a superuser.
  - **Usage**: `+bbs/editpost <board_name>/<post_number> = <new_content>`
  - **Permissions**: Requires the user to be the author of the post or a superuser.

- **CmdDeletePost**: 
  - **Description**: Deletes a post from a board.
  - **Usage**: `+bbs/deletepost <board_name>/<post_number>`
  - **Permissions**: Requires the user to be the author of the post or a superuser.

### 3. `commands/bbs/bbs_builder_commands.py`

This module contains commands for creating and managing boards. These commands are typically restricted to users with builder or higher permissions.

- **CmdCreateBoard**: 
  - **Description**: Creates a new board with a specified name and description.
  - **Usage**: `+bbs/create <name> = <description> / public | private`
  - **Permissions**: Requires "Builder" permissions.

- **CmdDeleteBoard**: 
  - **Description**: Deletes a board and all its posts.
  - **Usage**: `+bbs/deleteboard <board_name>`
  - **Permissions**: Requires "Builder" permissions.

- **CmdRevokeAccess**: 
  - **Description**: Revokes access for a user to a private board.
  - **Usage**: `+bbs/revokeaccess <board_name> = <character_name>`
  - **Permissions**: Requires "Builder" permissions.

- **CmdListAccess**: 
  - **Description**: Lists all users who have access to a private board.
  - **Usage**: `+bbs/listaccess <board_name>`
  - **Permissions**: Requires "Builder" permissions.

- **CmdLockBoard**: 
  - **Description**: Locks a board to prevent new posts.
  - **Usage**: `+bbs/lockboard <board_name>`
  - **Permissions**: Requires "Builder" permissions.

- **CmdPinPost**: 
  - **Description**: Pins a post to the top of a board.
  - **Usage**: `+bbs/pinpost <board_name_or_number>/<post_number>`
  - **Permissions**: Requires "Builder" permissions.

- **CmdUnpinPost**: 
  - **Description**: Unpins a post from the top of a board.
  - **Usage**: `+bbs/unpinpost <board_name_or_number>/<post_number>`
  - **Permissions**: Requires "Builder" permissions.

- **CmdEditBoard**: 
  - **Description**: Edits the settings or description of a board.
  - **Usage**: `+bbs/editboard <board_name> = <field>, <new_value>`
  - **Permissions**: Requires "Builder" permissions.

- **CmdGrantAccess**: 
  - **Description**: Grants access to a private board.
  - **Usage**: `+bbs/grantaccess <board_name> = <character_name> [/readonly]`
  - **Permissions**: Requires "Builder" permissions.

---

## Setup and Usage

To use these commands in your Evennia-based game, ensure the command modules are correctly imported and integrated into your game's command sets. Each command has specific permission requirements, ensuring that only authorized users can perform certain actions.

For more detailed information on each command and its usage, refer to the docstrings within the respective Python files.
