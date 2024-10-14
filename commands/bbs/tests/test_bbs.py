import unittest
from unittest.mock import Mock
from evennia import create_object
from typeclasses.bbs_controller import BBSController
from commands.bbs.bbs_admin_commands import CmdResetBBS
from commands.bbs.bbs_builder_commands import (
    CmdCreateBoard,
    CmdDeleteBoard,
    CmdRevokeAccess,
    CmdListAccess,
    CmdLockBoard,
    CmdPinPost,
    CmdUnpinPost,
    CmdEditBoard,
    CmdGrantAccess
)
from commands.bbs.bbs_all_commands import CmdPost, CmdReadBBS, CmdEditPost, CmdDeletePost

class TestBBSAdminCommands(unittest.TestCase):

    def setUp(self):
        """
        Set up test environment.
        """
        self.caller = Mock()
        self.caller.key = "Caller"
        BBSController.objects.filter(db_key="BBSController").delete()  # Remove any existing BBSControllers
        self.bbs_controller = create_object(BBSController, key="BBSController")

        if not self.bbs_controller.get_board("General"):
            self.bbs_controller.create_board("General", "General discussion board", public=True)

        if not self.bbs_controller.get_board("PrivateBoard"):
            self.bbs_controller.create_board("PrivateBoard", "Private discussion board", public=False)
            self.bbs_controller.grant_access("PrivateBoard", "Caller", "full_access")

    def tearDown(self):
        """
        Clean up test environment.
        """
        BBSController.objects.filter(db_key="BBSController").delete()

    def test_create_board(self):
        """
        Test creating a new board.
        """
        cmd = CmdCreateBoard()
        cmd.caller = self.caller
        cmd.args = "News = Latest news and announcements / public"
        cmd.func()
        self.caller.msg.assert_called_with("Board 'News' created as public with description: Latest news and announcements")
        board = self.bbs_controller.get_board("News")
        self.assertIsNotNone(board)
        self.assertEqual(board['description'], "Latest news and announcements")

    def test_delete_board(self):
        """
        Test deleting a board.
        """
        cmd = CmdDeleteBoard()
        cmd.caller = self.caller
        cmd.args = "General"
        cmd.func()
        self.caller.msg.assert_called_with("Board 'General' and all its posts have been deleted.")
        board = self.bbs_controller.get_board("General")
        self.assertIsNone(board)

    def test_revoke_access(self):
        """
        Test revoking access to a private board.
        """
        cmd = CmdRevokeAccess()
        cmd.caller = self.caller
        cmd.args = "PrivateBoard = Caller"
        cmd.func()
        self.caller.msg.assert_called_with("Access for Caller has been revoked from board 'PrivateBoard'.")
        access = self.bbs_controller.has_access("PrivateBoard", "Caller")
        self.assertFalse(access)

    def test_list_access(self):
        """
        Test listing access for a private board.
        """
        cmd = CmdListAccess()
        cmd.caller = self.caller
        cmd.args = "PrivateBoard"
        cmd.func()
        self.caller.msg.assert_called_with("Users with access to 'PrivateBoard': Caller")

    def test_lock_board(self):
        """
        Test locking a board.
        """
        cmd = CmdLockBoard()
        cmd.caller = self.caller
        cmd.args = "General"
        cmd.func()
        self.caller.msg.assert_called_with("Board 'General' has been locked. No new posts can be made.")
        board = self.bbs_controller.get_board("General")
        self.assertTrue(board['locked'])

    def test_pin_post(self):
        """
        Test pinning a post.
        """
        self.bbs_controller.create_post("General", "Welcome", "Welcome to the general board!", "Author")
        cmd = CmdPinPost()
        cmd.caller = self.caller
        cmd.args = "General/1"
        cmd.func()
        self.caller.msg.assert_called_with("Post 1 in board 'General' has been pinned to the top.")
        board = self.bbs_controller.get_board("General")
        self.assertTrue(board['posts'][0]['pinned'])

    def test_unpin_post(self):
        """
        Test unpinning a post.
        """
        self.bbs_controller.create_post("General", "Welcome", "Welcome to the general board!", "Author")
        self.bbs_controller.pin_post("General", 0)
        cmd = CmdUnpinPost()
        cmd.caller = self.caller
        cmd.args = "General/1"
        cmd.func()
        self.caller.msg.assert_called_with("Post 1 in board 'General' has been unpinned.")
        board = self.bbs_controller.get_board("General")
        self.assertFalse(board['posts'][0]['pinned'])

    def test_edit_board(self):
        """
        Test editing a board's description and public status.
        """
        cmd = CmdEditBoard()
        cmd.caller = self.caller
        cmd.args = "General = description, A new description"
        cmd.func()
        self.caller.msg.assert_called_with("Board 'General' has been updated. Description set to 'A new description'.")
        board = self.bbs_controller.get_board("General")
        self.assertEqual(board['description'], "A new description")

        cmd.args = "General = public, false"
        cmd.func()
        self.caller.msg.assert_called_with("Board 'General' has been updated. Public set to 'false'.")
        board = self.bbs_controller.get_board("General")
        self.assertFalse(board['public'])

    def test_grant_access(self):
        """
        Test granting access to a private board.
        """
        cmd = CmdGrantAccess()
        cmd.caller = self.caller
        cmd.args = "PrivateBoard = NewUser"
        cmd.func()
        self.caller.msg.assert_called_with("Granted full access to NewUser for board 'PrivateBoard'.")
        access = self.bbs_controller.has_access("PrivateBoard", "NewUser")
        self.assertTrue(access)

class TestCmdResetBBS(unittest.TestCase):

    def setUp(self):
        """
        Set up test environment.
        """
        self.caller = Mock()
        self.cmd = CmdResetBBS()
        self.cmd.caller = self.caller

        BBSController.objects.filter(db_key="BBSController").delete()  # Ensure no BBSControllers exist
        self.bbs_controller = create_object(BBSController, key="BBSController")
        self.bbs_controller.create_board("General", "General discussion board")
        self.bbs_controller.create_post("General", "Welcome", "Welcome to the general board!", "Author")

    def tearDown(self):
        """
        Clean up test environment.
        """
        BBSController.objects.filter(db_key="BBSController").delete()

    def test_reset_without_confirmation(self):
        """
        Test calling the reset command without confirmation.
        """
        self.caller.ndb.confirmation = None
        self.cmd.func()
        self.caller.msg.assert_called_with("This will wipe all boards and posts. Type '+bbs/reset yes' to confirm.")
        self.assertEqual(self.caller.ndb.confirmation, "yes")

    def test_reset_with_confirmation(self):
        """
        Test calling the reset command with confirmation.
        """
        self.caller.ndb.confirmation = "yes"
        self.cmd.func()
        self.caller.msg.assert_called_with("BBSController has been reset. All boards and posts have been deleted.")
        self.assertEqual(self.bbs_controller.db.boards, {})
        self.assertEqual(self.bbs_controller.db.next_board_id, 1)

    def test_create_bbs_controller_if_not_exist(self):
        """
        Test that a new BBSController is created if it does not exist.
        """
        # Delete existing BBSController
        self.bbs_controller.delete()
        self.bbs_controller = None

        self.caller.ndb.confirmation = "yes"
        self.cmd.func()
        self.caller.msg.assert_any_call("BBSController created.")
        self.caller.msg.assert_any_call("BBSController has been reset. All boards and posts have been deleted.")
        new_controller = BBSController.objects.get(db_key="BBSController")
        self.assertIsNotNone(new_controller)
        self.assertEqual(new_controller.db.boards, {})
        self.assertEqual(new_controller.db.next_board_id, 1)


class TestBBSAllCommands(unittest.TestCase):

    def setUp(self):
        """
        Set up test environment.
        """
        self.caller = Mock()
        self.caller.key = "Caller"
        self.caller.permissions = ["Player"]  # Basic permissions

        BBSController.objects.filter(db_key="BBSController").delete()  # Remove any existing BBSControllers
        self.bbs_controller = create_object(BBSController, key="BBSController")
        self.bbs_controller.create_board("General", "General discussion board", public=True)
        self.bbs_controller.create_board("PrivateBoard", "Private discussion board", public=False)
        self.bbs_controller.grant_access("PrivateBoard", "Caller", "full_access")
        self.bbs_controller.create_post("General", "Welcome", "Welcome to the general board!", "Author")
        self.bbs_controller.create_post("General", "Second Post", "This is the second post.", "Author")

    def tearDown(self):
        """
        Clean up test environment.
        """
        BBSController.objects.filter(db_key="BBSController").delete()

    def test_cmd_post(self):
        """
        Test posting a message on a board.
        """
        cmd = CmdPost()
        cmd.caller = self.caller
        cmd.args = "General/Welcome = Welcome to the general board!"
        cmd.func()
        self.caller.msg.assert_called_with("Post 'Welcome' added to board 'General'.")
        posts = self.bbs_controller.get_posts("General")
        self.assertEqual(len(posts), 3)  # Adjust to expected number of posts
        self.assertEqual(posts[-1]['title'], "Welcome")
        self.assertEqual(posts[-1]['content'], "Welcome to the general board!")

    def test_cmd_read_bbs_read_post(self):
        """
        Test reading a specific post in a board.
        """
        cmd = CmdReadBBS()
        cmd.caller = self.caller
        cmd.args = "1/1"
        cmd.func()
        self.caller.msg.assert_any_call("Title: Welcome")

    def test_cmd_delete_post(self):
        """
        Test deleting a post from a board.
        """
        self.bbs_controller.create_post("General", "To Delete", "This post will be deleted.", "Caller")
        self.caller.is_superuser = False
        cmd = CmdDeletePost()
        cmd.caller = self.caller
        cmd.args = "General/3"  # Adjust to target the correct post index
        cmd.func()
        self.caller.msg.assert_called_with("Author: Post 3 has been deleted from board 'General'.")
        posts = self.bbs_controller.get_posts("General")
        self.assertEqual(len(posts), 2)

    def test_post_no_write_access(self):
        """
        Test trying to post on a board without write access.
        """
        # Simulate another user without write access
        self.caller.key = "AnotherUser"
        self.caller.permissions = ["Player"]  # No special permissions

        cmd = CmdPost()
        cmd.caller = self.caller
        cmd.args = "PrivateBoard/Test = Trying to post without access"
        cmd.func()
        self.caller.msg.assert_called_with("You do not have write access to post on the board 'PrivateBoard'.")
        posts = self.bbs_controller.get_posts("PrivateBoard")
        self.assertEqual(len(posts), 0)

    def test_edit_post_no_permission(self):
        """
        Test trying to edit a post without permission.
        """
        # Set up a different caller without permissions
        self.caller.key = "AnotherUser"
        self.caller.is_superuser = False
        self.caller.permissions = ["Player"]

        cmd = CmdEditPost()
        cmd.caller = self.caller
        cmd.args = "General/1 = Trying to edit without permission"
        cmd.func()
        self.caller.msg.assert_called_with("You do not have permission to edit this post.")
        posts = self.bbs_controller.get_posts("General")
        self.assertEqual(posts[0]['content'], "Welcome to the general board!")

    def test_delete_post_no_permission(self):
        """
        Test trying to delete a post without permission.
        """
        # Set up a different caller without permissions
        self.caller.key = "AnotherUser"
        self.caller.is_superuser = False
        self.caller.permissions = ["Player"]

        posts = self.bbs_controller.get_posts("General")
        self.assertEqual(len(posts), 2)  # Ensure test was setup correctly

        cmd = CmdDeletePost()
        cmd.caller = self.caller
        cmd.args = "General/1"
        cmd.func()
        self.caller.msg.assert_called_with("You do not have permission to delete this post.")
        posts = self.bbs_controller.get_posts("General")
        self.assertEqual(len(posts), 2)  # Ensure the post was not deleted

if __name__ == '__main__':
    unittest.main()
