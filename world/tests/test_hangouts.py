from evennia.utils.test_resources import EvenniaTest
from evennia.objects.models import ObjectDB
from typeclasses.rooms import Room
from typeclasses.characters import Character
from typeclasses.exits import Exit # Or use DefaultExit if custom Exit is complex
from world.hangouts.models import HangoutDB
from commands.CmdHangouts import CmdHangout
# from evennia.commands.default.general import CmdHome # Only if execute_cmd is not preferred

class TestHangoutUmbraJump(EvenniaTest):
    def setUp(self):
        super().setUp()
        # For exit cleanup
        self.exit_to_umbra = None
        self.exit_to_material = None
        # EvenniaTest sets up self.obj1, self.obj2, self.char1, self.char2, self.room1, self.room2
        # We can repurpose these or create new ones for clarity.

        # Create a specific character for testing
        self.test_char = self.create_object(Character, key="TestChar")

        # Create Material Room
        self.material_room = self.create_object(Room, key="MaterialRoom")
        self.material_room.db.umbra_only = False

        # Create Umbra Room
        self.umbra_room = self.create_object(Room, key="UmbraRoom")
        self.umbra_room.db.umbra_only = True
        
        # Place character in Material Room and set initial state
        self.test_char.location = self.material_room
        self.test_char.db.in_umbra = False # Explicitly set for clarity
        self.test_char.tags.add("in_material", category="state")
        self.test_char.tags.remove("in_umbra", category="state") # Ensure it's not there

        # Create Hangouts
        self.hangout_umbra = HangoutDB.objects.create(
            db_key="Umbra Hangout",
            db_room=self.umbra_room,
            db_hangout_id=1  # Explicitly set for the test
        )
        
        self.hangout_material = HangoutDB.objects.create(
            db_key="Material Hangout",
            db_room=self.material_room,
            db_hangout_id=2 # Explicitly set for the test
        )

    def test_jump_to_umbra_and_back(self):
        # 1. Initial state check
        self.assertEqual(self.test_char.location, self.material_room)
        self.assertFalse(self.test_char.db.in_umbra)
        self.assertTrue(self.test_char.tags.has("in_material", category="state"))
        self.assertFalse(self.test_char.tags.has("in_umbra", category="state"))

        # 2. Jump to Umbra Hangout
        cmd_instance_to_umbra = CmdHangout()
        cmd_instance_to_umbra.caller = self.test_char
        cmd_instance_to_umbra.args = str(self.hangout_umbra.db.hangout_id)
        cmd_instance_to_umbra.switches = ["jump"]
        cmd_instance_to_umbra.func()

        self.assertEqual(self.test_char.location, self.umbra_room, "Character should be in UmbraRoom.")
        self.assertTrue(self.test_char.db.in_umbra, "Character db.in_umbra should be True.")
        self.assertTrue(self.test_char.tags.has("in_umbra", category="state"), "Character should have 'in_umbra' tag.")
        self.assertFalse(self.test_char.tags.has("in_material", category="state"), "Character should not have 'in_material' tag.")

        # 3. Jump back to Material Hangout
        cmd_instance_to_material = CmdHangout()
        cmd_instance_to_material.caller = self.test_char
        cmd_instance_to_material.args = str(self.hangout_material.db.hangout_id)
        cmd_instance_to_material.switches = ["jump"]
        cmd_instance_to_material.func()

        self.assertEqual(self.test_char.location, self.material_room, "Character should be in MaterialRoom.")
        self.assertFalse(self.test_char.db.in_umbra, "Character db.in_umbra should be False.")
        self.assertTrue(self.test_char.tags.has("in_material", category="state"), "Character should have 'in_material' tag.")
        self.assertFalse(self.test_char.tags.has("in_umbra", category="state"), "Character should not have 'in_umbra' tag.")

    def tearDown(self):
        # Clean up: EvenniaTest handles most, but explicit deletion is safer for non-default objects.
        # Order matters if there are dependencies, but for these, it should be fine.
        if self.hangout_umbra:
            self.hangout_umbra.delete()
        if self.hangout_material:
            self.hangout_material.delete()
        if self.exit_to_umbra:
            self.exit_to_umbra.delete()
        if self.exit_to_material:
            self.exit_to_material.delete()
        # Rooms and char are likely handled by EvenniaTest's tearDown if created with self.create_object
        # but explicit deletion is safer for objects not following the self.obj1, self.room1 pattern.
        if hasattr(self, 'material_room') and self.material_room.id:
            self.material_room.delete()
        if hasattr(self, 'umbra_room') and self.umbra_room.id:
            self.umbra_room.delete()
        if hasattr(self, 'test_char') and self.test_char.id:
            self.test_char.delete()
        super().tearDown()

    def test_home_command_umbra_transition(self):
        # Ensure character is in material room and state initially
        self.test_char.location = self.material_room
        self.test_char.db.in_umbra = False
        self.test_char.tags.add("in_material", category="state")
        self.test_char.tags.remove("in_umbra", category="state")

        # 1. Go home to UmbraRoom
        self.test_char.home = self.umbra_room
        self.test_char.execute_cmd("home")

        self.assertEqual(self.test_char.location, self.umbra_room, "Char should be in UmbraRoom after +home.")
        self.assertTrue(self.test_char.db.in_umbra, "Char db.in_umbra should be True in Umbra home.")
        self.assertTrue(self.test_char.tags.has("in_umbra", category="state"), "Char should have 'in_umbra' tag.")
        self.assertFalse(self.test_char.tags.has("in_material", category="state"), "Char should not have 'in_material' tag.")

        # 2. Go home back to MaterialRoom
        self.test_char.home = self.material_room
        self.test_char.execute_cmd("home")

        self.assertEqual(self.test_char.location, self.material_room, "Char should be in MaterialRoom after +home.")
        self.assertFalse(self.test_char.db.in_umbra, "Char db.in_umbra should be False in Material home.")
        self.assertTrue(self.test_char.tags.has("in_material", category="state"), "Char should have 'in_material' tag.")
        self.assertFalse(self.test_char.tags.has("in_umbra", category="state"), "Char should not have 'in_umbra' tag.")

    def test_standard_exit_umbra_transition(self):
        # Ensure character is in material room and state initially
        self.test_char.location = self.material_room
        self.test_char.db.in_umbra = False
        self.test_char.tags.add("in_material", category="state")
        self.test_char.tags.remove("in_umbra", category="state")

        # 1. Traverse from Material to Umbra via standard exit
        self.exit_to_umbra = self.create_object(Exit, key="to_umbra", location=self.material_room, destination=self.umbra_room)
        self.test_char.execute_cmd("to_umbra")
        
        self.assertEqual(self.test_char.location, self.umbra_room, "Char should be in UmbraRoom after exit.")
        self.assertTrue(self.test_char.db.in_umbra, "Char db.in_umbra should be True after exit to Umbra.")
        self.assertTrue(self.test_char.tags.has("in_umbra", category="state"), "Char should have 'in_umbra' tag.")
        self.assertFalse(self.test_char.tags.has("in_material", category="state"), "Char should not have 'in_material' tag.")

        # 2. Traverse from Umbra back to Material via standard exit
        self.exit_to_material = self.create_object(Exit, key="to_material", location=self.umbra_room, destination=self.material_room)
        self.test_char.execute_cmd("to_material")

        self.assertEqual(self.test_char.location, self.material_room, "Char should be in MaterialRoom after return exit.")
        self.assertFalse(self.test_char.db.in_umbra, "Char db.in_umbra should be False after exit to Material.")
        self.assertTrue(self.test_char.tags.has("in_material", category="state"), "Char should have 'in_material' tag.")
        self.assertFalse(self.test_char.tags.has("in_umbra", category="state"), "Char should not have 'in_umbra' tag.")
