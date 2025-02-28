"""
Test script to verify instance handling for merits, flaws, and backgrounds.
This script simulates the behavior of the CmdSelfStat command for stats that require instances.

Run with: python test_instance_handling.py
"""
from commands.CmdSelfStat import CmdSelfStat, REQUIRED_INSTANCES

class MockCharacter:
    """Mock character class for testing."""
    
    def __init__(self):
        """Initialize the mock character."""
        self.db = type('DB', (), {'stats': {}})
        self.messages = []
        
    def msg(self, message):
        """Mock the msg method to capture messages."""
        self.messages.append(message)
        print(message)
        
    def get_stat(self, *args, **kwargs):
        """Mock the get_stat method."""
        return None

def test_instance_handling():
    """Test instance handling for various stats."""
    print("=== Starting Instance Handling Tests ===")
    print(f"Stats requiring instances: {', '.join(REQUIRED_INSTANCES)}")
    
    # Create a mock character and command
    character = MockCharacter()
    cmd = CmdSelfStat()
    cmd.caller = character
    
    # Test 1: A background that REQUIRES an instance (Status)
    print("\n=== Test 1: Background that REQUIRES an instance (Status) ===")
    
    # With instance
    character.messages = []
    cmd.args = "Status(Camarilla)/Background=3"
    cmd.parse()
    
    print(f"Stat name: {cmd.stat_name}")
    print(f"Instance: {cmd.instance}")
    print(f"Category: {cmd.category}")
    print(f"Stat type: {cmd.stat_type}")
    
    # Without instance
    character.messages = []
    cmd.args = "Status/Background=3"
    cmd.parse()
    
    print("\nMessages after trying without instance:")
    for msg in character.messages:
        print(f"  {msg}")
    
    # Test 2: A background that CAN have an instance but doesn't REQUIRE one (Resources)
    print("\n=== Test 2: Background that CAN have an instance but doesn't REQUIRE one (Resources) ===")
    
    # With instance
    character.messages = []
    cmd.args = "Resources(Personal)/Background=3"
    cmd.parse()
    
    print(f"Stat name: {cmd.stat_name}")
    print(f"Instance: {cmd.instance}")
    print(f"Category: {cmd.category}")
    print(f"Stat type: {cmd.stat_type}")
    
    # Without instance
    character.messages = []
    cmd.args = "Resources/Background=3"
    cmd.parse()
    
    print(f"Stat name: {cmd.stat_name}")
    print(f"Instance: {cmd.instance}")
    print(f"Category: {cmd.category}")
    print(f"Stat type: {cmd.stat_type}")
    
    # Test 3: A merit that REQUIRES an instance (Enemy)
    print("\n=== Test 3: Merit that REQUIRES an instance (Enemy) ===")
    
    # With instance
    character.messages = []
    cmd.args = "Enemy(Sabbat)/Social=3"
    cmd.parse()
    
    print(f"Stat name: {cmd.stat_name}")
    print(f"Instance: {cmd.instance}")
    print(f"Category: {cmd.category}")
    print(f"Stat type: {cmd.stat_type}")
    
    # Without instance
    character.messages = []
    cmd.args = "Enemy/Social=3"
    cmd.parse()
    
    print("\nMessages after trying without instance:")
    for msg in character.messages:
        print(f"  {msg}")
    
    # Test 4: A merit that CAN have an instance but doesn't REQUIRE one (Ambidextrous)
    print("\n=== Test 4: Merit that CAN have an instance but doesn't REQUIRE one (Ambidextrous) ===")
    
    # With instance
    character.messages = []
    cmd.args = "Ambidextrous(Left-handed)/Physical=2"
    cmd.parse()
    
    print(f"Stat name: {cmd.stat_name}")
    print(f"Instance: {cmd.instance}")
    print(f"Category: {cmd.category}")
    print(f"Stat type: {cmd.stat_type}")
    
    # Without instance
    character.messages = []
    cmd.args = "Ambidextrous/Physical=2"
    cmd.parse()
    
    print(f"Stat name: {cmd.stat_name}")
    print(f"Instance: {cmd.instance}")
    print(f"Category: {cmd.category}")
    print(f"Stat type: {cmd.stat_type}")
    
    # Test 5: A stat that doesn't support instances (Strength)
    print("\n=== Test 5: Stat that doesn't support instances (Strength) ===")
    
    # Without instance
    character.messages = []
    cmd.args = "Strength/Physical=3"
    cmd.parse()
    
    print(f"Stat name: {cmd.stat_name}")
    print(f"Instance: {cmd.instance}")
    print(f"Category: {cmd.category}")
    print(f"Stat type: {cmd.stat_type}")
    
    # With instance
    character.messages = []
    cmd.args = "Strength(High)/Physical=3"
    cmd.parse()
    
    print("\nMessages after trying with instance that shouldn't be supported:")
    for msg in character.messages:
        print(f"  {msg}")
    
    print("\n=== Tests Completed ===")

if __name__ == "__main__":
    test_instance_handling() 