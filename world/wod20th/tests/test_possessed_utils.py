"""
Test cases for possessed validation functions.
"""
from django.test import TestCase
from unittest.mock import Mock, patch
from world.wod20th.utils.possessed_utils import (
    validate_possessed_stats, validate_possessed_type,
    validate_possessed_blessing, validate_possessed_charm,
    validate_possessed_gift, POSSESSED_TYPES,
    POSSESSED_POWERS
)

class TestPossessedValidation(TestCase):
    def setUp(self):
        """Set up test data."""
        self.mock_character = Mock()
        # Default values for a Fomori
        self.mock_character.get_stat.side_effect = lambda *args, **kwargs: {
            ('identity', 'lineage', 'Possessed Type', False): 'Fomori',
            ('identity', 'lineage', 'Spirit Type', False): 'Bane'
        }.get((args[0], args[1], args[2], kwargs.get('temp', False)))
    
    def test_validate_possessed_type(self):
        """Test possessed type validation."""
        # Test valid types
        self.assertTrue(validate_possessed_type('Fomori')[0])
        self.assertTrue(validate_possessed_type('Kami')[0])
        
        # Test invalid types
        self.assertFalse(validate_possessed_type('Invalid Type')[0])
        self.assertFalse(validate_possessed_type('')[0])
    
    def test_validate_possessed_blessing(self):
        """Test blessing validation."""
        # Test valid Fomori blessing
        self.assertTrue(validate_possessed_blessing(self.mock_character, 'Armored Hide', '3')[0])
        
        # Test valid Kami blessing
        mock_kami = Mock()
        mock_kami.get_stat.return_value = 'Kami'
        self.assertTrue(validate_possessed_blessing(mock_kami, 'Aura of Tranquility', '3')[0])
        
        # Test invalid blessing
        self.assertFalse(validate_possessed_blessing(self.mock_character, 'Invalid Blessing', '3')[0])
        
        # Test invalid value
        self.assertFalse(validate_possessed_blessing(self.mock_character, 'Armored Hide', '6')[0])
        
        # Test non-numeric value
        self.assertFalse(validate_possessed_blessing(self.mock_character, 'Armored Hide', 'abc')[0])
        
        # Test without possessed type
        mock_no_type = Mock()
        mock_no_type.get_stat.return_value = None
        self.assertFalse(validate_possessed_blessing(mock_no_type, 'Armored Hide', '3')[0])
    
    def test_validate_possessed_charm(self):
        """Test charm validation."""
        # Test valid Fomori charm
        self.assertTrue(validate_possessed_charm(self.mock_character, 'Blast', '3')[0])
        
        # Test valid Kami charm
        mock_kami = Mock()
        mock_kami.get_stat.return_value = 'Kami'
        self.assertTrue(validate_possessed_charm(mock_kami, 'Healing', '3')[0])
        
        # Test invalid charm
        self.assertFalse(validate_possessed_charm(self.mock_character, 'Invalid Charm', '3')[0])
        
        # Test invalid value
        self.assertFalse(validate_possessed_charm(self.mock_character, 'Blast', '6')[0])
        
        # Test non-numeric value
        self.assertFalse(validate_possessed_charm(self.mock_character, 'Blast', 'abc')[0])
        
        # Test without possessed type
        mock_no_type = Mock()
        mock_no_type.get_stat.return_value = None
        self.assertFalse(validate_possessed_charm(mock_no_type, 'Blast', '3')[0])
    
    @patch('world.wod20th.utils.possessed_utils.Stat.objects.filter')
    def test_validate_possessed_gift(self, mock_filter):
        """Test gift validation."""
        # Mock gift query
        mock_gift = Mock()
        mock_filter.return_value.first.return_value = mock_gift
        
        # Test valid gift
        self.assertTrue(validate_possessed_gift(self.mock_character, 'Test Gift', '3')[0])
        
        # Test invalid value
        self.assertFalse(validate_possessed_gift(self.mock_character, 'Test Gift', '6')[0])
        
        # Test non-numeric value
        self.assertFalse(validate_possessed_gift(self.mock_character, 'Test Gift', 'abc')[0])
        
        # Test non-existent gift
        mock_filter.return_value.first.return_value = None
        self.assertFalse(validate_possessed_gift(self.mock_character, 'Invalid Gift', '3')[0])
    
    def test_validate_possessed_stats(self):
        """Test overall possessed stat validation."""
        # Test type validation
        self.assertTrue(validate_possessed_stats(self.mock_character, 'possessed type', 'Fomori')[0])
        
        # Test blessing validation
        self.assertTrue(validate_possessed_stats(
            self.mock_character, 'Armored Hide', '3', 'powers', 'blessing'
        )[0])
        
        # Test charm validation
        self.assertTrue(validate_possessed_stats(
            self.mock_character, 'Blast', '3', 'powers', 'charm'
        )[0])
        
        # Test gift validation
        with patch('world.wod20th.utils.possessed_utils.Stat.objects.filter') as mock_filter:
            mock_gift = Mock()
            mock_filter.return_value.first.return_value = mock_gift
            self.assertTrue(validate_possessed_stats(
                self.mock_character, 'Test Gift', '3', 'powers', 'gift'
            )[0]) 