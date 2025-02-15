"""
Test cases for mortal+ validation functions.
"""
from django.test import TestCase
from unittest.mock import Mock, patch
from world.wod20th.utils.mortalplus_utils import (
    validate_mortalplus_stats, validate_mortalplus_type,
    validate_ghoul_disciplines, validate_kinfolk_gifts,
    validate_kinain_powers, validate_sorcerer_powers,
    validate_psychic_powers, validate_faithful_powers,
    validate_mortalplus_backgrounds,
    MORTALPLUS_TYPE_CHOICES, MORTALPLUS_TYPES,
    MORTALPLUS_POWERS, ARTS, REALMS
)
from world.wod20th.utils.stat_mappings import UNIVERSAL_BACKGROUNDS, SORCERER_BACKGROUNDS
from world.wod20th.models import Stat

class TestMortalPlusValidation(TestCase):
    def setUp(self):
        """Set up test data."""
        self.mock_character = Mock()
        # Default values for a Ghoul
        self.mock_character.get_stat.side_effect = lambda *args, **kwargs: {
            ('identity', 'lineage', 'Type', False): 'Ghoul',
            ('identity', 'personal', 'Domitor', False): 'Test Domitor',
            ('identity', 'lineage', 'Clan', False): 'Ventrue',
            ('merits', 'merit', 'Gifted Kinfolk', False): {'perm': 5},
            ('merits', 'merit', 'Fae Blood', False): {'perm': 4}
        }.get((args[0], args[1], args[2], kwargs.get('temp', False)))
        
        # Mock get_all_powers method
        self.mock_character.get_all_powers = Mock(return_value=[])
    
    def test_validate_mortalplus_type(self):
        """Test mortal+ type validation."""
        # Test valid types
        self.assertTrue(validate_mortalplus_type('Ghoul')[0])
        self.assertTrue(validate_mortalplus_type('Kinfolk')[0])
        self.assertTrue(validate_mortalplus_type('Kinain')[0])
        self.assertTrue(validate_mortalplus_type('Sorcerer')[0])
        self.assertTrue(validate_mortalplus_type('Psychic')[0])
        self.assertTrue(validate_mortalplus_type('Faithful')[0])
        
        # Test invalid types
        self.assertFalse(validate_mortalplus_type('Invalid Type')[0])
        self.assertFalse(validate_mortalplus_type('')[0])
    
    @patch('world.wod20th.utils.vampire_utils.get_clan_disciplines')
    def test_validate_ghoul_disciplines(self, mock_get_disciplines):
        """Test ghoul discipline validation."""
        # Mock clan disciplines
        mock_get_disciplines.return_value = ['Dominate', 'Fortitude', 'Presence']
        
        # Test valid discipline
        self.assertTrue(validate_ghoul_disciplines(self.mock_character, 'Dominate', '3')[0])
        
        # Test invalid discipline
        self.assertFalse(validate_ghoul_disciplines(self.mock_character, 'Obfuscate', '3')[0])
        
        # Test invalid value
        self.assertFalse(validate_ghoul_disciplines(self.mock_character, 'Dominate', '6')[0])
        
        # Test non-numeric value
        self.assertFalse(validate_ghoul_disciplines(self.mock_character, 'Dominate', 'abc')[0])
        
        # Test without domitor
        mock_no_domitor = Mock()
        mock_no_domitor.get_stat.return_value = None
        self.assertFalse(validate_ghoul_disciplines(mock_no_domitor, 'Dominate', '3')[0])
    
    @patch('world.wod20th.models.Stat.objects.filter')
    def test_validate_kinfolk_gifts(self, mock_filter):
        """Test kinfolk gift validation."""
        # Mock gift query
        mock_gift = Mock()
        mock_filter.return_value.first.return_value = mock_gift
        
        # Mock character with Gift Merit
        mock_gifted = Mock()
        mock_gifted.get_stat.side_effect = lambda *args, **kwargs: {
            ('identity', 'lineage', 'Type', False): 'Kinfolk',
            ('merits', 'merit', 'Gifted Kinfolk', False): {'perm': 5}
        }.get((args[0], args[1], args[2], kwargs.get('temp', False)))
        
        # Test valid gift with merit
        self.assertTrue(validate_kinfolk_gifts(mock_gifted, 'Test Gift', '3')[0])
        
        # Test invalid value
        self.assertFalse(validate_kinfolk_gifts(mock_gifted, 'Test Gift', '6')[0])
        
        # Test non-numeric value
        self.assertFalse(validate_kinfolk_gifts(mock_gifted, 'Test Gift', 'abc')[0])
        
        # Test without Gift Merit
        mock_no_merit = Mock()
        mock_no_merit.get_stat.return_value = None
        self.assertFalse(validate_kinfolk_gifts(mock_no_merit, 'Test Gift', '3')[0])
    
    def test_validate_kinain_powers(self):
        """Test kinain powers validation."""
        # Mock character with Fae Blood Merit
        mock_kinain = Mock()
        mock_kinain.get_stat.side_effect = lambda *args, **kwargs: {
            ('identity', 'lineage', 'Type', False): 'Kinain',
            ('merits', 'merit', 'Fae Blood', False): {'perm': 4}
        }.get((args[0], args[1], args[2], kwargs.get('temp', False)))
        mock_kinain.get_all_powers = Mock(return_value=[])
        
        # Test valid art
        self.assertTrue(validate_kinain_powers(mock_kinain, 'Chicanery', '2', 'art')[0])
        
        # Test valid realm
        self.assertTrue(validate_kinain_powers(mock_kinain, 'Actor', '2', 'realm')[0])
        
        # Test invalid value (too high for merit level)
        self.assertFalse(validate_kinain_powers(mock_kinain, 'Chicanery', '3', 'art')[0])
        
        # Test non-numeric value
        self.assertFalse(validate_kinain_powers(mock_kinain, 'Chicanery', 'abc', 'art')[0])
        
        # Test without Fae Blood Merit
        mock_no_merit = Mock()
        mock_no_merit.get_stat.return_value = None
        mock_no_merit.get_all_powers = Mock(return_value=[])
        self.assertFalse(validate_kinain_powers(mock_no_merit, 'Chicanery', '2', 'art')[0])
    
    @patch('world.wod20th.models.Stat.objects.filter')
    def test_validate_sorcerer_powers(self, mock_filter):
        """Test sorcerer powers validation."""
        # Mock power query
        mock_power = Mock()
        mock_filter.return_value.first.return_value = mock_power
        
        # Test valid power
        self.assertTrue(validate_sorcerer_powers(self.mock_character, 'Test Power', '3')[0])
        
        # Test invalid value
        self.assertFalse(validate_sorcerer_powers(self.mock_character, 'Test Power', '6')[0])
        
        # Test non-numeric value
        self.assertFalse(validate_sorcerer_powers(self.mock_character, 'Test Power', 'abc')[0])
        
        # Test non-existent power
        mock_filter.return_value.first.return_value = None
        self.assertFalse(validate_sorcerer_powers(self.mock_character, 'Invalid Power', '3')[0])
    
    @patch('world.wod20th.models.Stat.objects.filter')
    def test_validate_psychic_powers(self, mock_filter):
        """Test psychic powers validation."""
        # Mock power query
        mock_power = Mock()
        mock_filter.return_value.first.return_value = mock_power
        
        # Test valid power
        self.assertTrue(validate_psychic_powers(self.mock_character, 'Test Power', '3')[0])
        
        # Test invalid value
        self.assertFalse(validate_psychic_powers(self.mock_character, 'Test Power', '6')[0])
        
        # Test non-numeric value
        self.assertFalse(validate_psychic_powers(self.mock_character, 'Test Power', 'abc')[0])
        
        # Test non-existent power
        mock_filter.return_value.first.return_value = None
        self.assertFalse(validate_psychic_powers(self.mock_character, 'Invalid Power', '3')[0])
    
    @patch('world.wod20th.models.Stat.objects.filter')
    def test_validate_faithful_powers(self, mock_filter):
        """Test faithful powers validation."""
        # Mock power query
        mock_power = Mock()
        mock_filter.return_value.first.return_value = mock_power
        
        # Test valid power
        self.assertTrue(validate_faithful_powers(self.mock_character, 'Test Power', '3')[0])
        
        # Test invalid value
        self.assertFalse(validate_faithful_powers(self.mock_character, 'Test Power', '6')[0])
        
        # Test non-numeric value
        self.assertFalse(validate_faithful_powers(self.mock_character, 'Test Power', 'abc')[0])
        
        # Test non-existent power
        mock_filter.return_value.first.return_value = None
        self.assertFalse(validate_faithful_powers(self.mock_character, 'Invalid Power', '3')[0])
    
    def test_validate_mortalplus_backgrounds(self):
        """Test background validation."""
        # Test valid universal background
        self.assertTrue(validate_mortalplus_backgrounds(self.mock_character, 'Resources', '3')[0])
        
        # Test valid sorcerer background
        mock_sorcerer = Mock()
        mock_sorcerer.get_stat.return_value = 'Sorcerer'
        self.assertTrue(validate_mortalplus_backgrounds(mock_sorcerer, 'Guide', '3')[0])
        
        # Test invalid background
        self.assertFalse(validate_mortalplus_backgrounds(self.mock_character, 'Invalid Background', '3')[0])
        
        # Test invalid value
        self.assertFalse(validate_mortalplus_backgrounds(self.mock_character, 'Resources', '6')[0])
        
        # Test non-numeric value
        self.assertFalse(validate_mortalplus_backgrounds(self.mock_character, 'Resources', 'abc')[0])
    
    def test_validate_mortalplus_stats(self):
        """Test overall mortal+ stat validation."""
        # Test type validation
        self.assertTrue(validate_mortalplus_stats(self.mock_character, 'type', 'Ghoul')[0])
        
        # Test ghoul discipline validation
        with patch('world.wod20th.utils.vampire_utils.get_clan_disciplines') as mock_get_disciplines:
            mock_get_disciplines.return_value = ['Dominate', 'Fortitude', 'Presence']
            result = validate_mortalplus_stats(
                self.mock_character, 'Dominate', '3', 'powers', 'discipline'
            )
            self.assertTrue(result[0], f"Failed to validate discipline. Error: {result[1]}")
        
        # Test background validation
        result = validate_mortalplus_stats(
            self.mock_character, 'Resources', '3', 'backgrounds', 'background'
        )
        self.assertTrue(result[0], f"Failed to validate background. Error: {result[1]}")
        
        # Test invalid type
        result = validate_mortalplus_stats(self.mock_character, 'type', 'Invalid Type')
        self.assertFalse(result[0], "Should reject invalid type")
        
        # Test invalid discipline
        with patch('world.wod20th.utils.vampire_utils.get_clan_disciplines') as mock_get_disciplines:
            mock_get_disciplines.return_value = ['Dominate', 'Fortitude', 'Presence']
            result = validate_mortalplus_stats(
                self.mock_character, 'Invalid Discipline', '3', 'powers', 'discipline'
            )
            self.assertFalse(result[0], "Should reject invalid discipline")
        
        # Test invalid background
        result = validate_mortalplus_stats(
            self.mock_character, 'Invalid Background', '3', 'backgrounds', 'background'
        )
        self.assertFalse(result[0], "Should reject invalid background") 