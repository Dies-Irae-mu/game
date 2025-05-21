from evennia.utils.test_resources import EvenniaTest
from evennia.objects.models import ObjectDB
from typeclasses.rooms import Room
from typeclasses.characters import Character
from world.hangouts.models import HangoutDB
from commands.CmdHangouts import CmdHangout

class TestHangoutUmbraJump(EvenniaTest):
    def setUp(self):
        super().setUp()
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
        self.hangout_umbra.delete()
        self.hangout_material.delete()
        self.material_room.delete()
        self.umbra_room.delete()
        self.test_char.delete()
        super().tearDown()
