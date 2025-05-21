"""
Test cases for WoD20th commands.
"""
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from evennia.utils.test_resources import EvenniaTest
from commands.CmdSheet import CmdSheet
from commands.CmdSelfStat import CmdSelfStat
from commands.CmdSpendGain import CmdSpendGain  # Added import
from world.wod20th.models import Stat
from world.wod20th.utils.mage_utils import initialize_mage_stats # Added import

class EvenniaTransactionTestCase(EvenniaTest):
    """Base test case that combines EvenniaTest functionality with transaction support."""
    
    account_typeclass = "typeclasses.accounts.Account"
    character_typeclass = "typeclasses.characters.Character"
    object_typeclass = "typeclasses.objects.Object"
    exit_typeclass = "typeclasses.exits.Exit"
    room_typeclass = "typeclasses.rooms.Room"
    script_typeclass = "typeclasses.scripts.Script"
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        from django.test import TransactionTestCase
        from django.db import transaction
        from evennia.server.models import ServerConfig
        
        # Ensure we start with a clean slate
        ServerConfig.objects.all().delete()
        ServerConfig.objects.create(db_key="server_starting_mode", db_value="True")
        super().setUpClass()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after the test class."""
        from evennia.server.models import ServerConfig
        ServerConfig.objects.all().delete()
        super().tearDownClass()
    
    def setUp(self):
        """Set up test case with transaction support."""
        from evennia.server.models import ServerConfig
        super().setUp()
        
        # Initialize stats for both characters after creation
        self._initialize_stat_structure(self.char1)
        self._initialize_stat_structure(self.char2)
    
    def tearDown(self):
        """Clean up after test case."""
        from django.db import transaction
        
        with transaction.atomic():
            super().tearDown()
    
    def _initialize_stat_structure(self, character):
        """Initialize the basic stat structure for a character."""
        if not hasattr(character.db, 'stats') or not character.db.stats:
            character.db.stats = {
                'identity': {
                    'personal': {},
                    'lineage': {}
                },
                'other': {
                    'splat': {
                        'Splat': {'perm': 'Mortal', 'temp': 'Mortal'}
                    }
                },
                'attributes': {
                    'physical': {
                        'Strength': {'perm': 1, 'temp': 1},
                        'Dexterity': {'perm': 1, 'temp': 1},
                        'Stamina': {'perm': 1, 'temp': 1}
                    },
                    'social': {
                        'Charisma': {'perm': 1, 'temp': 1},
                        'Manipulation': {'perm': 1, 'temp': 1},
                        'Appearance': {'perm': 1, 'temp': 1}
                    },
                    'mental': {
                        'Perception': {'perm': 1, 'temp': 1},
                        'Intelligence': {'perm': 1, 'temp': 1},
                        'Wits': {'perm': 1, 'temp': 1}
                    }
                },
                'abilities': {
                    'talents': {
                        'Alertness': {'perm': 0, 'temp': 0},
                        'Athletics': {'perm': 0, 'temp': 0},
                        'Awareness': {'perm': 0, 'temp': 0}
                    },
                    'skills': {},
                    'knowledges': {}
                },
                'advantages': {
                    'backgrounds': {},
                    'merits': {},
                    'flaws': {}
                },
                'pools': {
                    'Willpower': {'perm': 0, 'temp': 0}
                },
                'virtues': {},
                'powers': {
                    'spheres': {},
                    'discipline': {},
                    'art': {},
                    'realm': {},
                    'gift': {}
                }
            }

class TestCmdSheet(EvenniaTransactionTestCase):
    """Test the +sheet command."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.cmd = CmdSheet()
        self.cmd.caller = self.char1
        self.cmd.args = ""  # Initialize empty args
        
        # Set up mocks
        self.char1.msg = Mock()
        self.char2.msg = Mock()
        
        # Clear permissions and add default ones
        self.char1.permissions.clear()
        
        # Mock get_character method
        def mock_get_character(name):
            if not name:
                return self.char1
            elif name == str(self.char2.id):
                if self.char1.permissions.check('Admin'):
                    return self.char2
                self.char1.msg("|rYou can't see the sheet of Char2.|n")
                return None
            self.char1.msg("|rCharacter not found.|n")
            return None
        self.cmd.get_character = mock_get_character
        
        # Set up mock for Stat model
        self.stat_patcher = patch('world.wod20th.models.Stat.objects')
        self.mock_stat_objects = self.stat_patcher.start()
        self.stat_mock = MagicMock()
        self.mock_stat_objects.filter.return_value.first.return_value = self.stat_mock
        
        # Initialize stats for char1
        self.char1.db.stats['attributes']['physical'].update({
            'Strength': {'perm': 2, 'temp': 4},
            'Dexterity': {'perm': 3, 'temp': 3},
            'Stamina': {'perm': 2, 'temp': 2}
        })
        self.char1.db.stats['attributes']['social'].update({
            'Charisma': {'perm': 3, 'temp': 3},
            'Manipulation': {'perm': 2, 'temp': 2},
            'Appearance': {'perm': 3, 'temp': 3}
        })
        self.char1.db.stats['attributes']['mental'].update({
            'Perception': {'perm': 2, 'temp': 2},
            'Intelligence': {'perm': 3, 'temp': 3},
            'Wits': {'perm': 2, 'temp': 2}
        })
        self.char1.db.stats['abilities']['talents'].update({
            'Alertness': {'perm': 2, 'temp': 2},
            'Athletics': {'perm': 2, 'temp': 2},
            'Awareness': {'perm': 2, 'temp': 2}
        })
        self.char1.db.stats['pools'].update({
            'Willpower': {'perm': 3, 'temp': 2}
        })
        
        # Add get_stat and set_stat methods to character
        def mock_get_stat(stat_type, category, stat_name, temp=False):
            try:
                if category:
                    value = self.char1.db.stats[stat_type][category][stat_name]
                else:
                    value = self.char1.db.stats[stat_type][stat_name]
                return value['temp' if temp else 'perm']
            except (KeyError, TypeError):
                return None
        
        def mock_set_stat(stat_type, category, stat_name, value, temp=False):
            if stat_type not in self.char1.db.stats:
                self.char1.db.stats[stat_type] = {}
            if category:
                if category not in self.char1.db.stats[stat_type]:
                    self.char1.db.stats[stat_type][category] = {}
                if stat_name not in self.char1.db.stats[stat_type][category]:
                    self.char1.db.stats[stat_type][category][stat_name] = {'perm': None, 'temp': None}
                self.char1.db.stats[stat_type][category][stat_name]['temp' if temp else 'perm'] = value
            else:
                if stat_name not in self.char1.db.stats[stat_type]:
                    self.char1.db.stats[stat_type][stat_name] = {'perm': None, 'temp': None}
                self.char1.db.stats[stat_type][stat_name]['temp' if temp else 'perm'] = value
            return True
        
        self.char1.get_stat = mock_get_stat
        self.char1.set_stat = mock_set_stat
        self.char2.get_stat = mock_get_stat
        self.char2.set_stat = mock_set_stat
        
    def tearDown(self):
        """Clean up after each test."""
        super().tearDown()
        self.stat_patcher.stop()
        
    def test_sheet_display_basic(self):
        """Test basic sheet display."""
        # Test viewing own sheet
        self.cmd.func()
        
        # Verify key sections are present in the output
        output = self.char1.msg.mock_calls[0][1][0]
        self.assertIn("Character Sheet for:", output)
        self.assertIn("Attributes", output)
        self.assertIn("Abilities", output)
        self.assertIn("Pools, Virtues & Status", output)
        
        # Verify attribute values with correct format
        self.assertIn("Strength", output)
        self.assertIn("Dexterity", output)
        self.assertIn("Stamina", output)
        
        # Verify ability values with correct format
        self.assertIn("Alertness", output)
        self.assertIn("Athletics", output)
        self.assertIn("Awareness", output)
        
        # Verify pools with correct format
        self.assertIn("Willpower", output)
    
    def test_sheet_display_vampire(self):
        """Test vampire-specific sheet display."""
        # Set up vampire-specific stats
        self.char1.db.stats['other']['splat']['Splat'] = {'perm': 'Vampire', 'temp': 'Vampire'}
        self.char1.db.stats['identity']['lineage']['Clan'] = {'perm': 'Ventrue', 'temp': 'Ventrue'}
        self.char1.db.stats['identity']['lineage']['Generation'] = {'perm': 12, 'temp': 12}
        
        # Initialize pools if not present
        if 'pools' not in self.char1.db.stats:
            self.char1.db.stats['pools'] = {}
        if 'dual' not in self.char1.db.stats['pools']:
            self.char1.db.stats['pools']['dual'] = {}
            
        self.char1.db.stats['pools']['dual']['Blood'] = {'perm': 10, 'temp': 8}
        self.char1.db.stats['pools']['dual']['Willpower'] = {'perm': 3, 'temp': 2}
        
        # Initialize powers if not present
        if 'powers' not in self.char1.db.stats:
            self.char1.db.stats['powers'] = {}
        if 'discipline' not in self.char1.db.stats['powers']:
            self.char1.db.stats['powers']['discipline'] = {}
            
        # Add some disciplines
        self.char1.db.stats['powers']['discipline'].update({
            'Dominate': {'perm': 2, 'temp': 2},
            'Fortitude': {'perm': 1, 'temp': 1},
            'Presence': {'perm': 3, 'temp': 3}
        })
        
        self.cmd.func()
        
        # Verify vampire-specific sections
        output = self.char1.msg.mock_calls[0][1][0]
        self.assertIn("Clan", output)
        self.assertIn("Generation", output)
        self.assertIn("Blood", output)
        self.assertIn("Disciplines", output)
        self.assertIn("Dominate", output)
        self.assertIn("Fortitude", output)
        self.assertIn("Presence", output)
    
    def test_sheet_display_mage(self):
        """Test mage-specific sheet display."""
        # Set up mage character
        self.char1.db.stats['other']['splat']['Splat'] = {'perm': 'Mage', 'temp': 'Mage'}
        
        # Set up identity fields
        self.char1.db.stats['identity']['personal'].update({
            'Full Name': {'perm': 'Marcus Blackthorn', 'temp': 'Marcus Blackthorn'},
            'Concept': {'perm': 'Hermetic Scholar', 'temp': 'Hermetic Scholar'},
            'Nature': {'perm': 'Architect', 'temp': 'Architect'},
            'Demeanor': {'perm': 'Visionary', 'temp': 'Visionary'},
            'Essence': {'perm': 'Dynamic', 'temp': 'Dynamic'},
            'Affiliation': {'perm': 'Order of Hermes', 'temp': 'Order of Hermes'}
        })
        
        self.char1.db.stats['identity']['lineage'].update({
            'Tradition': {'perm': 'Order of Hermes', 'temp': 'Order of Hermes'},
            'Affinity Sphere': {'perm': 'Forces', 'temp': 'Forces'},
            'Date of Awakening': {'perm': '1999', 'temp': '1999'}
        })
        
        # Initialize powers if not present
        if 'powers' not in self.char1.db.stats:
            self.char1.db.stats['powers'] = {}
        if 'spheres' not in self.char1.db.stats['powers']:
            self.char1.db.stats['powers']['spheres'] = {}
            
        # Add spheres
        self.char1.db.stats['powers']['spheres'].update({
            'Forces': {'perm': 3, 'temp': 3},
            'Life': {'perm': 2, 'temp': 2},
            'Prime': {'perm': 1, 'temp': 1},
            'Correspondence': {'perm': 0, 'temp': 0},
            'Entropy': {'perm': 0, 'temp': 0},
            'Matter': {'perm': 0, 'temp': 0},
            'Mind': {'perm': 0, 'temp': 0},
            'Spirit': {'perm': 0, 'temp': 0},
            'Time': {'perm': 0, 'temp': 0}
        })
        
        # Initialize pools if not present
        if 'pools' not in self.char1.db.stats:
            self.char1.db.stats['pools'] = {}
        if 'dual' not in self.char1.db.stats['pools']:
            self.char1.db.stats['pools']['dual'] = {}
            
        self.char1.db.stats['pools'].update({
            'Willpower': {'perm': 3, 'temp': 3}
        })
        
        self.char1.db.stats['pools']['dual'].update({
            'Arete': {'perm': 3, 'temp': 3},
            'Quintessence': {'perm': 3, 'temp': 5},
            'Paradox': {'perm': 0, 'temp': 0}
        })
        
        self.cmd.func()
        
        # Get the output
        output = self.char1.msg.mock_calls[0][1][0]
        
        # Verify mage-specific elements
        self.assertIn("Order of Hermes", output)  # Check for actual Tradition value
        self.assertIn("Forces", output)
        self.assertIn("Life", output)
        self.assertIn("Prime", output)
        self.assertIn("Arete", output)
        self.assertIn("Quintessence", output)
        self.assertIn("Paradox", output)
    
    def test_sheet_display_changeling(self):
        """Test changeling-specific sheet display."""
        # Set up changeling-specific stats
        self.char1.db.stats['other']['splat']['Splat'] = {'perm': 'Changeling', 'temp': 'Changeling'}
        self.char1.db.stats['identity']['lineage']['Kith'] = {'perm': 'Troll', 'temp': 'Troll'}
        self.char1.db.stats['identity']['lineage']['Seeming'] = {'perm': 'Wilder', 'temp': 'Wilder'}
        
        # Initialize pools if not present
        if 'pools' not in self.char1.db.stats:
            self.char1.db.stats['pools'] = {}
        if 'dual' not in self.char1.db.stats['pools']:
            self.char1.db.stats['pools']['dual'] = {}
            
        self.char1.db.stats['pools']['dual'].update({
            'Glamour': {'perm': 4, 'temp': 2},
            'Banality': {'perm': 5, 'temp': 6}
        })
        
        # Initialize powers if not present
        if 'powers' not in self.char1.db.stats:
            self.char1.db.stats['powers'] = {}
            
        # Add arts and realms
        if 'art' not in self.char1.db.stats['powers']:
            self.char1.db.stats['powers']['art'] = {}
        if 'realm' not in self.char1.db.stats['powers']:
            self.char1.db.stats['powers']['realm'] = {}
            
        self.char1.db.stats['powers']['art'].update({
            'Primal': {'perm': 2, 'temp': 2},
            'Wayfare': {'perm': 3, 'temp': 3}
        })
        
        self.char1.db.stats['powers']['realm'].update({
            'Actor': {'perm': 2, 'temp': 2},
            'Fae': {'perm': 3, 'temp': 3}
        })
        
        self.cmd.func()
        
        # Verify changeling-specific sections
        output = self.char1.msg.mock_calls[0][1][0]
        self.assertIn("Kith", output)
        self.assertIn("Seeming", output)
        self.assertIn("Arts", output)
        self.assertIn("Realms", output)
        self.assertIn("Primal", output)
        self.assertIn("Wayfare", output)
        self.assertIn("Actor", output)
        self.assertIn("Fae", output)
        self.assertIn("Glamour", output)
        self.assertIn("Banality", output)
    
    def test_sheet_display_shifter(self):
        """Test shifter-specific sheet display."""
        # Set up shifter-specific stats
        self.char1.db.stats['other']['splat']['Splat'] = {'perm': 'Shifter', 'temp': 'Shifter'}
        self.char1.db.stats['identity']['lineage'].update({
            'Type': {'perm': 'Garou', 'temp': 'Garou'},
            'Breed': {'perm': 'Homid', 'temp': 'Homid'},
            'Auspice': {'perm': 'Ahroun', 'temp': 'Ahroun'},
            'Tribe': {'perm': 'Get of Fenris', 'temp': 'Get of Fenris'}
        })
        
        # Initialize pools if not present
        if 'pools' not in self.char1.db.stats:
            self.char1.db.stats['pools'] = {}
        if 'dual' not in self.char1.db.stats['pools']:
            self.char1.db.stats['pools']['dual'] = {}
            
        self.char1.db.stats['pools']['dual'].update({
            'Rage': {'perm': 4, 'temp': 2},
            'Gnosis': {'perm': 3, 'temp': 3}
        })
        
        # Initialize powers if not present
        if 'powers' not in self.char1.db.stats:
            self.char1.db.stats['powers'] = {}
        if 'gift' not in self.char1.db.stats['powers']:
            self.char1.db.stats['powers']['gift'] = {}
            
        # Add some gifts
        self.char1.db.stats['powers']['gift'].update({
            'Razor Claws': {'perm': 2, 'temp': 2},
            'Sense Wyrm': {'perm': 1, 'temp': 1}
        })
        
        self.cmd.func()
        
        # Verify shifter-specific sections
        output = self.char1.msg.mock_calls[0][1][0]
        self.assertIn("Breed", output)
        self.assertIn("Auspice", output)
        self.assertIn("Tribe", output)
        self.assertIn("Gifts", output)
        self.assertIn("Razor Claws", output)
        self.assertIn("Sense Wyrm", output)
        self.assertIn("Rage", output)
        self.assertIn("Gnosis", output)
    
    def test_view_other_character(self):
        """Test viewing another character's sheet."""
        # Set up the command to view char2's sheet
        self.cmd.args = str(self.char2.id)
        
        # Test as non-staff
        self.cmd.func()
        output = self.char1.msg.mock_calls[0][1][0]
        self.assertIn("|rYou can't see the sheet of Char2.|n", output)
        
        # Test as staff
        self.char1.permissions.add('Admin')
        self.cmd.func()
        output = self.char1.msg.mock_calls[1][1][0]
        self.assertIn("Character Sheet for:", output)
    
    def test_view_nonexistent_character(self):
        """Test viewing a nonexistent character's sheet."""
        self.cmd.args = "99999"  # Non-existent ID
        self.cmd.func()
        output = self.char1.msg.mock_calls[0][1][0]
        self.assertIn("|rCharacter not found.|n", output)
    
    def test_temporary_stat_display(self):
        """Test display of temporary stat values."""
        # Set up character with temporary values
        self.char1.db.stats['pools']['Willpower'] = {'perm': 3, 'temp': 2}
        self.char1.db.stats['attributes']['physical']['Strength'] = {'perm': 2, 'temp': 4}
        
        # Run the command
        self.cmd.func()
        
        # Get the output
        output = self.char1.msg.mock_calls[0][1][0]
        
        # Verify temporary values are displayed
        self.assertIn("Willpower", output)
        self.assertIn("Strength", output)

class TestCmdSelfStat(EvenniaTransactionTestCase):
    """Test the +stat command."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.cmd = CmdSelfStat()
        self.cmd.caller = self.char1
        self.cmd.args = ""  # Initialize empty args
        
        # Initialize command attributes
        self.cmd.stat_name = ""
        self.cmd.instance = None
        self.cmd.category = None
        self.cmd.value_change = None
        self.cmd.temp = False
        self.cmd.stat_type = None
        
        # Set up mocks
        self.char1.msg = Mock()
        self.char2.msg = Mock()
        
        # Clear permissions and add default ones
        self.char1.permissions.clear()
        
        # Set up mock for Stat model
        self.stat_patcher = patch('world.wod20th.models.Stat.objects')
        self.mock_stat_objects = self.stat_patcher.start()
        
        # Set up mock stat returns
        def mock_stat_filter(**kwargs):
            mock_filter = MagicMock()
            name = kwargs.get('name__iexact', '')
            
            if name in ['strength', 'dexterity', 'stamina']:
                mock_stat = MagicMock()
                mock_stat.category = 'attributes'
                mock_stat.stat_type = 'physical'
                mock_stat.name = name.capitalize()
                mock_stat.instanced = False
                mock_filter.first.return_value = mock_stat
            elif name in ['charisma', 'manipulation', 'appearance']:
                mock_stat = MagicMock()
                mock_stat.category = 'attributes'
                mock_stat.stat_type = 'social'
                mock_stat.name = name.capitalize()
                mock_stat.instanced = False
                mock_filter.first.return_value = mock_stat
            elif name in ['perception', 'intelligence', 'wits']:
                mock_stat = MagicMock()
                mock_stat.category = 'attributes'
                mock_stat.stat_type = 'mental'
                mock_stat.name = name.capitalize()
                mock_stat.instanced = False
                mock_filter.first.return_value = mock_stat
            elif name in ['alertness', 'athletics', 'awareness']:
                mock_stat = MagicMock()
                mock_stat.category = 'abilities'
                mock_stat.stat_type = 'talents'
                mock_stat.name = name.capitalize()
                mock_stat.instanced = False
                mock_filter.first.return_value = mock_stat
            elif name in ['willpower']:
                mock_stat = MagicMock()
                mock_stat.category = 'pools'
                mock_stat.stat_type = None
                mock_stat.name = name.capitalize()
                mock_stat.instanced = False
                mock_filter.first.return_value = mock_stat
            else:
                mock_filter.first.return_value = None
            
            mock_filter.count.return_value = 1 if mock_filter.first.return_value else 0
            return mock_filter
        
        self.mock_stat_objects.filter.side_effect = mock_stat_filter
        
        # Add get_stat and set_stat methods to character
        def mock_get_stat(stat_type, category, stat_name, temp=False):
            try:
                if category:
                    value = self.char1.db.stats[stat_type][category][stat_name]
                else:
                    value = self.char1.db.stats[stat_type][stat_name]
                return value['temp' if temp else 'perm']
            except (KeyError, TypeError):
                return None
        
        def mock_set_stat(stat_type, category, stat_name, value, temp=False):
            if stat_type not in self.char1.db.stats:
                self.char1.db.stats[stat_type] = {}
            if category:
                if category not in self.char1.db.stats[stat_type]:
                    self.char1.db.stats[stat_type][category] = {}
                if stat_name not in self.char1.db.stats[stat_type][category]:
                    self.char1.db.stats[stat_type][category][stat_name] = {'perm': None, 'temp': None}
                self.char1.db.stats[stat_type][category][stat_name]['temp' if temp else 'perm'] = value
            else:
                if stat_name not in self.char1.db.stats[stat_type]:
                    self.char1.db.stats[stat_type][stat_name] = {'perm': None, 'temp': None}
                self.char1.db.stats[stat_type][stat_name]['temp' if temp else 'perm'] = value
            return True
        
        self.char1.get_stat = mock_get_stat
        self.char1.set_stat = mock_set_stat
        self.char2.get_stat = mock_get_stat
        self.char2.set_stat = mock_set_stat
        
        # Set up approved status
        self.char1.db.approved = False
        self.char2.db.approved = False
        
        # Add validate_stat_value method to command
        def mock_validate_stat_value(stat_name, value, category=None, stat_type=None):
            try:
                value = int(value)
                if value < 1 or value > 5:
                    return False, "Value must be between 1 and 5."
            except ValueError:
                pass  # Non-numeric values are handled elsewhere
            return True, ""
            
        self.cmd.validate_stat_value = mock_validate_stat_value
        
        # Add detect_ability_category method to command
        def mock_detect_ability_category(stat_name):
            if stat_name.lower() in ['strength', 'dexterity', 'stamina']:
                return 'attributes', 'physical'
            elif stat_name.lower() in ['charisma', 'manipulation', 'appearance']:
                return 'attributes', 'social'
            elif stat_name.lower() in ['perception', 'intelligence', 'wits']:
                return 'attributes', 'mental'
            elif stat_name.lower() in ['alertness', 'athletics', 'awareness']:
                return 'abilities', 'talents'
            elif stat_name.lower() in ['willpower']:
                return 'pools', None
            return None, None
            
        self.cmd.detect_ability_category = mock_detect_ability_category
        
    def tearDown(self):
        """Clean up after each test."""
        super().tearDown()
        self.stat_patcher.stop()
        
    def test_invalid_syntax(self):
        """Test invalid command syntax."""
        self.cmd.args = ""
        self.cmd.parse()  # Make sure to parse first
        self.cmd.func()
        self.char1.msg.assert_called_with("|rUsage: +selfstat <stat>[(<instance>)]/[<category>]=[+-]<value>|n")
        
    def test_set_attribute(self):
        """Test setting character attributes."""
        print("\n=== Starting test_set_attribute ===")
        
        # Set up mock return for Stat query
        mock_stat = MagicMock()
        mock_stat.category = 'attributes'
        mock_stat.stat_type = 'physical'
        mock_stat.name = 'Strength'
        mock_stat.instanced = False
        self.mock_stat_objects.filter.return_value.first.return_value = mock_stat
        
        # Initialize the attribute structure
        self.char1.db.stats['attributes']['physical']['Strength'] = {'perm': 1, 'temp': 1}
        print(f"Initial Strength values: {self.char1.db.stats['attributes']['physical']['Strength']}")
        
        # Set up the command
        self.cmd.args = "strength = 3"
        print(f"Command args: {self.cmd.args}")
        self.cmd.parse()
        
        # Set command attributes that would normally be set by parse
        self.cmd.stat_name = "Strength"
        self.cmd.instance = None
        self.cmd.category = "physical"
        self.cmd.value_change = 3
        self.cmd.temp = False
        self.cmd.stat_type = "attributes"
        
        print(f"Command state after setup:")
        print(f"- stat_name: {self.cmd.stat_name}")
        print(f"- category: {self.cmd.category}")
        print(f"- stat_type: {self.cmd.stat_type}")
        print(f"- value_change: {self.cmd.value_change}")
        print(f"- temp: {self.cmd.temp}")
        
        # Mock the command's internal methods
        self.cmd.get_stat_from_db = Mock(return_value=mock_stat)
        self.cmd.validate_stat_value = Mock(return_value=(True, ""))
        
        # Execute the command
        print("Executing command...")
        self.cmd.func()
        
        # Print final state
        print(f"Final Strength values: {self.char1.db.stats['attributes']['physical']['Strength']}")
        
        # Verify both permanent and temporary values were set
        self.assertEqual(self.char1.db.stats['attributes']['physical']['Strength']['perm'], 3)
        self.assertEqual(self.char1.db.stats['attributes']['physical']['Strength']['temp'], 3)
        
    def test_set_ability(self):
        """Test setting character abilities."""
        print("\n=== Starting test_set_ability ===")
        
        # Set up mock return for Stat query
        mock_stat = MagicMock()
        mock_stat.category = 'abilities'
        mock_stat.stat_type = 'talents'
        mock_stat.name = 'Alertness'
        mock_stat.instanced = False
        self.mock_stat_objects.filter.return_value.first.return_value = mock_stat
        
        # Initialize the abilities structure
        self.char1.db.stats['abilities']['talents']['Alertness'] = {'perm': 0, 'temp': 0}
        print(f"Initial Alertness values: {self.char1.db.stats['abilities']['talents']['Alertness']}")
        
        # Set up the command
        self.cmd.args = "alertness = 3"
        print(f"Command args: {self.cmd.args}")
        self.cmd.parse()
        
        # Set command attributes that would normally be set by parse
        self.cmd.stat_name = "Alertness"
        self.cmd.instance = None
        self.cmd.category = "talents"
        self.cmd.value_change = 3
        self.cmd.temp = False
        self.cmd.stat_type = "abilities"
        
        print(f"Command state after setup:")
        print(f"- stat_name: {self.cmd.stat_name}")
        print(f"- category: {self.cmd.category}")
        print(f"- stat_type: {self.cmd.stat_type}")
        print(f"- value_change: {self.cmd.value_change}")
        print(f"- temp: {self.cmd.temp}")
        
        # Mock the command's internal methods
        self.cmd.get_stat_from_db = Mock(return_value=mock_stat)
        self.cmd.validate_stat_value = Mock(return_value=(True, ""))
        
        # Execute the command
        print("Executing command...")
        self.cmd.func()
        
        # Print final state
        print(f"Final Alertness values: {self.char1.db.stats['abilities']['talents']['Alertness']}")
        
        # Verify both permanent and temporary values were set
        self.assertEqual(self.char1.db.stats['abilities']['talents']['Alertness']['perm'], 3)
        self.assertEqual(self.char1.db.stats['abilities']['talents']['Alertness']['temp'], 3)
        
    def test_set_temporary_values(self):
        """Test setting temporary stat values."""
        print("\n=== Starting test_set_temporary_values ===")
        
        # Set up mock return for Stat query
        mock_stat = MagicMock()
        mock_stat.category = 'pools'
        mock_stat.stat_type = None
        mock_stat.name = 'Willpower'
        mock_stat.instanced = False
        self.mock_stat_objects.filter.return_value.first.return_value = mock_stat
        
        # Initialize the pools structure
        self.char1.db.stats['pools']['Willpower'] = {'perm': 3, 'temp': 0}
        print(f"Initial Willpower values: {self.char1.db.stats['pools']['Willpower']}")
        
        # Set up the command
        self.cmd.args = "willpower/temp = 2"
        print(f"Command args: {self.cmd.args}")
        self.cmd.parse()
        
        # Set command attributes that would normally be set by parse
        self.cmd.stat_name = "Willpower"
        self.cmd.instance = None
        self.cmd.category = None
        self.cmd.value_change = 2
        self.cmd.temp = True
        self.cmd.stat_type = "pools"
        
        print(f"Command state after setup:")
        print(f"- stat_name: {self.cmd.stat_name}")
        print(f"- category: {self.cmd.category}")
        print(f"- stat_type: {self.cmd.stat_type}")
        print(f"- value_change: {self.cmd.value_change}")
        print(f"- temp: {self.cmd.temp}")
        
        # Mock the command's internal methods
        self.cmd.get_stat_from_db = Mock(return_value=mock_stat)
        self.cmd.validate_stat_value = Mock(return_value=(True, ""))
        
        # Execute the command
        print("Executing command...")
        self.cmd.func()
        
        # Print final state
        print(f"Final Willpower values: {self.char1.db.stats['pools']['Willpower']}")
        
        # Verify only temporary value was changed, permanent value remains the same
        self.assertEqual(self.char1.db.stats['pools']['Willpower']['temp'], 2)
        self.assertEqual(self.char1.db.stats['pools']['Willpower']['perm'], 3)
        
    def test_permission_checks(self):
        """Test permission checks for setting stats."""
        # Set up mock return for Stat query
        mock_stat = MagicMock()
        mock_stat.category = 'attributes'
        mock_stat.stat_type = 'physical'
        mock_stat.name = 'Strength'
        mock_stat.instanced = False
        self.mock_stat_objects.filter.return_value.first.return_value = mock_stat
        
        # Try to set a value above maximum
        self.cmd.args = "strength = 6"
        self.cmd.parse()  # Make sure to parse first
        self.cmd.func()
        
        # Verify error message
        self.char1.msg.assert_called_with("|rValue must be between 1 and 5.|n")


class TestMageParadoxCommands(EvenniaTransactionTestCase):
    """Test +gain and +spend commands for Mage Paradox."""

    def setUp(self):
        """Set up a Mage character for testing."""
        super().setUp()
        # Use self.char1 as the Mage character
        self.char = self.char1 # Use a shorter alias for convenience
        self.account = self.account1

        # Ensure db.stats is initialized (it should be by parent setUp)
        if not hasattr(self.char.db, 'stats') or not self.char.db.stats:
            self._initialize_stat_structure(self.char) # Call if not initialized

        # Set character as Mage
        self.char.db.stats['other']['splat']['Splat'] = {'perm': 'Mage', 'temp': 'Mage'}
        
        # Initialize Mage specific stats, including Paradox
        # Mock set_stat, del_stat, and msg for initialize_mage_stats
        original_set_stat = self.char.set_stat
        original_del_stat = getattr(self.char, 'del_stat', None) # Save original del_stat if it exists
        original_msg = self.char.msg

        self.char.set_stat = Mock()
        self.char.del_stat = Mock()
        self.char.msg = Mock() # Mock msg before calling initialize_mage_stats

        initialize_mage_stats(self.char, affiliation="Traditions", tradition="Order of Hermes")

        # Restore original methods and ensure Paradox is set correctly in the mock's view
        # The actual character.db.stats will be updated by initialize_mage_stats via direct dict manipulation
        # or its own calls to a (potentially non-mocked) set_stat.
        # For the purpose of the test, we need to ensure the mock set_stat has recorded Paradox.
        
        # We need to simulate what initialize_mage_stats does to char.db.stats
        # because the mocked set_stat won't actually update char.db.stats
        # initialize_mage_stats directly sets char.db.stats items for some things.
        # Let's ensure the Paradox part is correctly reflected in the actual db.stats
        # as initialize_mage_stats might use direct dict access for some parts.
        
        # Re-mock msg for command testing after setup
        self.char.msg = Mock()
        
        # Manually ensure Paradox is set as expected after initialize_mage_stats
        # This is because initialize_mage_stats uses char.set_stat which was mocked during its run.
        # We need to put the *actual* values into char.db.stats for the CmdSpendGain to read.
        if 'pools' not in self.char.db.stats: self.char.db.stats['pools'] = {}
        if 'dual' not in self.char.db.stats['pools']: self.char.db.stats['pools']['dual'] = {}
        self.char.db.stats['pools']['dual']['Paradox'] = {'perm': 10, 'temp': 0}
        self.char.db.stats['pools']['dual']['Willpower'] = {'perm': 5, 'temp': 5} # Example, ensure it exists

        # Restore original methods if they existed
        self.char.set_stat = original_set_stat
        if original_del_stat:
            self.char.del_stat = original_del_stat
        # self.char.msg is kept as a new Mock for command testing.


    def test_gain_paradox(self):
        """Test gaining Paradox."""
        self.assertEqual(self.char.db.stats['pools']['dual']['Paradox']['temp'], 0)
        self.assertEqual(self.char.db.stats['pools']['dual']['Paradox']['perm'], 10)

        # Gain 5 Paradox
        self.call(CmdSpendGain(), "paradox=5", caller=self.char, cmdstring="+gain")
        self.assertEqual(self.char.db.stats['pools']['dual']['Paradox']['temp'], 5)
        self.char.msg.assert_called_with("You have gained 5 points of paradox. New paradox value: 5/10")

        # Gain another 5 Paradox
        self.call(CmdSpendGain(), "paradox=5", caller=self.char, cmdstring="+gain")
        self.assertEqual(self.char.db.stats['pools']['dual']['Paradox']['temp'], 10)
        self.char.msg.assert_called_with("You have gained 5 points of paradox. New paradox value: 10/10")

        # Try to gain 1 more Paradox (should not exceed max)
        self.call(CmdSpendGain(), "paradox=1", caller=self.char, cmdstring="+gain")
        self.assertEqual(self.char.db.stats['pools']['dual']['Paradox']['temp'], 10)
        self.char.msg.assert_called_with("You are already at maximum paradox (10).")

    def test_spend_paradox(self):
        """Test spending Paradox."""
        # Set initial temporary Paradox to 10 for spending tests
        self.char.db.stats['pools']['dual']['Paradox']['temp'] = 10
        self.assertEqual(self.char.db.stats['pools']['dual']['Paradox']['perm'], 10)

        # Spend 3 Paradox
        self.call(CmdSpendGain(), "paradox=3", caller=self.char, cmdstring="+spend")
        self.assertEqual(self.char.db.stats['pools']['dual']['Paradox']['temp'], 7)
        self.char.msg.assert_called_with("You have spent 3 points of paradox. New paradox value: 7/10")

        # Spend 7 Paradox
        self.call(CmdSpendGain(), "paradox=7", caller=self.char, cmdstring="+spend")
        self.assertEqual(self.char.db.stats['pools']['dual']['Paradox']['temp'], 0)
        self.char.msg.assert_called_with("You have spent 7 points of paradox. New paradox value: 0/10")

        # Try to spend 1 more Paradox (should not go below 0)
        self.call(CmdSpendGain(), "paradox=1", caller=self.char, cmdstring="+spend")
        self.assertEqual(self.char.db.stats['pools']['dual']['Paradox']['temp'], 0)
        self.char.msg.assert_called_with("You don't have enough paradox. Current paradox: 0")