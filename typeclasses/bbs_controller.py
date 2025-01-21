from evennia import DefaultObject
from evennia.utils.utils import datetime_format
from datetime import datetime

class BBSController(DefaultObject):
    """
    This object manages the bulletin boards and posts in the game.
    It should be placed in the game world and used to handle all BBS-related
    functionality, such as creating boards, posts, and managing access.
    """
    def at_server_start(self):
        """
        Called when the server starts.
        """
        return super().at_server_start()

    def at_object_creation(self):
        """
        Initialize the BBSController object. This is called only once, 
        when the object is first created.
        """
        self.db.boards = {}  # Dictionary to store all boards
        self.db.next_board_id = 1  # Start board numbering from 1

    def _find_next_available_board_id(self):
        """
        Find the next available board ID by looking for gaps in the sequence
        or returning the next number after the highest existing ID.
        """
        if not self.db.boards:
            return 1
            
        existing_ids = sorted(self.db.boards.keys())
        # Look for gaps in the sequence
        for i, board_id in enumerate(existing_ids, 1):
            if i != board_id:
                return i
        # If no gaps found, return next number after highest
        return existing_ids[-1] + 1

    def create_board(self, name, description, public=True, read_only=False):
        """
        Create a new board.
        """
        if any(board['name'].lower() == name.lower() for board in self.db.boards.values()):
            raise ValueError("A board with this name already exists.")
        
        # Use next available ID instead of next_board_id
        board_id = self._find_next_available_board_id()
        board = {
            'id': board_id,
            'name': name,
            'description': description,
            'public': public,
            'read_only': read_only,
            'posts': [],
            'access_list': {},
            'locked': False
        }
        self.db.boards[board_id] = board
        self.db.next_board_id = self._find_next_available_board_id()

    def get_board(self, reference):
        """
        Retrieve a board by its name or ID.
        :param reference: (str or int) The name or ID of the board.
        :return: (dict) The board data or None if not found.
        """
        if isinstance(reference, int):
            return self.db.boards.get(reference)
        else:
            reference = reference.lower()
            return next((board for board in self.db.boards.values() if board['name'].lower() == reference), None)

    def create_post(self, board_reference, title, content, author):
        """
        Create a new post on a specified board.
        """
        board = self.get_board(board_reference)
        if not board:
            return "Board not found"
        post = {
            'title': title,
            'content': content,
            'author': author,
            'created_at': datetime_format(datetime.now()),  # Pass current datetime
            'edited_at': None,
            'pinned': False  # Initialize pinned status
        }
        board['posts'].append(post)
        return f"Post '{title}' created on board '{board['name']}'."

    def get_posts(self, board_reference):
        """
        Retrieve all posts from a specified board.
        """
        board = self.get_board(board_reference)
        return board['posts'] if board else None

    def edit_post(self, board_reference, post_index, new_content):
        """
        Edit an existing post's content.
        """
        board = self.get_board(board_reference)
        if board and 0 <= post_index < len(board['posts']):
            board['posts'][post_index]['content'] = new_content
            board['posts'][post_index]['edited_at'] = datetime_format(datetime.now())

    def delete_post(self, board_reference, post_index):
        """
        Delete a post from a board.
        """
        board = self.get_board(board_reference)
        if board and 0 <= post_index < len(board['posts']):
            del board['posts'][post_index]

    def pin_post(self, board_reference, post_index):
        """
        Pin a post to the top of the board.
        """
        board = self.get_board(board_reference)
        if not board:
            return "Board not found"
        if 0 <= post_index < len(board['posts']):
            board['posts'][post_index]['pinned'] = True
            return f"Post {post_index + 1} in board '{board['name']}' has been pinned."
        return "Post not found"

    def unpin_post(self, board_reference, post_index):
        """
        Unpin a post from the top of the board.
        """
        board = self.get_board(board_reference)
        if not board:
            return "Board not found"
        if 0 <= post_index < len(board['posts']):
            board['posts'][post_index]['pinned'] = False
            return f"Post {post_index + 1} in board '{board['name']}' has been unpinned."
        return "Post not found"

    def grant_access(self, board_reference, character_name, access_level="full_access"):
        """
        Grant access to a private board to a specific character.
        :param board_reference: (str or int) The name or ID of the board.
        :param character_name: (str) The name of the character to grant access.
        :param access_level: (str) "full_access" or "read_only".
        """
        board = self.get_board(board_reference)
        if board:
            board['access_list'][character_name] = access_level

    def revoke_access(self, board_reference, character_name):
        """
        Revoke access for a specific character from a private board.
        :param board_reference: (str or int) The name or ID of the board.
        :param character_name: (str) The name of the character to revoke access.
        """
        board = self.get_board(board_reference)
        if board and character_name in board['access_list']:
            del board['access_list'][character_name]

    def has_access(self, board_reference, character_name):
        """
        Check if a character has read access to a board.
        """
        board = self.get_board(board_reference)
        if board:
            if board['public']:
                return True
            return character_name in board['access_list']
        return False

    def has_write_access(self, board_reference, character_name):
        """
        Check if a character has write access to a board.
        """
        board = self.get_board(board_reference)
        if board:
            access_level = board['access_list'].get(character_name)
            return access_level == "full_access" or (board['public'] and not board['read_only'])
        return False

    def delete_board(self, board_reference):
        """
        Delete an entire board along with its posts.
        :param board_reference: (str or int) The name or ID of the board to delete.
        """
        board = self.get_board(board_reference)
        if board:
            del self.db.boards[board['id']]
            # Update next_board_id to recycle IDs
            self.db.next_board_id = self._find_next_available_board_id()
            return f"Board '{board['name']}' and all its posts have been deleted."
        return "Board not found"

    def save_board(self, board_reference, updated_board_data):
        """
        Update board data with provided changes.
        :param board_reference: (str or int) The name or ID of the board to update.
        :param updated_board_data: (dict) Dictionary containing updated board data.
        """
        board = self.get_board(board_reference)
        if board:
            # Update the board's dictionary with new values
            for key, value in updated_board_data.items():
                board[key] = value
            return f"Board '{board['name']}' has been updated."
        return "Board not found"


    def lock_board(self, board_reference):
        """
        Lock a board to prevent new posts from being made.
        :param board_reference: (str or int) The name or ID of the board to lock.
        """
        board = self.get_board(board_reference)
        if board:
            board['locked'] = True
            return f"Board '{board['name']}' has been locked."
        return "Board not found"
