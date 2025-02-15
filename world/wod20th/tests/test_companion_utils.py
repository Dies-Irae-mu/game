"""
Test cases for companion validation functions.
"""
from django.test import TestCase
from unittest.mock import Mock, patch
from world.wod20th.utils.companion_utils import (
    validate_companion_stats, validate_companion_type,
    validate_companion_advantage, validate_companion_charm,
    COMPANION_TYPE_CHOICES, COMPANION_POWERS,
    COMPANION_TYPE_ADVANTAGES
)
from world.wod20th.utils.stat_mappings import SPECIAL_ADVANTAGES

class TestCompanionValidation(TestCase):
    def setUp(self):
        """Set up test data."""
        self.mock_character = Mock()
        # Default values for a Spirit companion
        self.mock_character.get_stat.side_effect = lambda *args, **kwargs: {
            ('identity', 'lineage', 'Companion Type', False): 'Spirit',
            ('identity', 'lineage', 'Power Source', False): None
        }.get((args[0], args[1], args[2], kwargs.get('temp', False)))
    
    def test_validate_companion_type(self):
        """Test companion type validation."""
        # Test valid types
        self.assertTrue(validate_companion_type('Spirit')[0])
        self.assertTrue(validate_companion_type('Construct')[0])
        self.assertTrue(validate_companion_type('Robot')[0])
        self.assertTrue(validate_companion_type('Alien')[0])
        self.assertTrue(validate_companion_type('Bygone')[0])
        self.assertTrue(validate_companion_type('Familiar')[0])
        
        # Test invalid types
        self.assertFalse(validate_companion_type('Invalid Type')[0])
        self.assertFalse(validate_companion_type('')[0])
    
    def test_validate_companion_advantage(self):
        """Test special advantage validation."""
        # Test valid spirit advantage
        self.assertTrue(validate_companion_advantage(self.mock_character, 'Aura', 3)[0])
        
        # Test valid construct advantage
        mock_construct = Mock()
        mock_construct.get_stat.return_value = 'Construct'
        self.assertTrue(validate_companion_advantage(mock_construct, 'Armor', 3)[0])
        
        # Test invalid advantage for type
        self.assertFalse(validate_companion_advantage(self.mock_character, 'Webbing', 3)[0])
        
        # Test invalid value
        self.assertFalse(validate_companion_advantage(self.mock_character, 'Aura', 6)[0])
        
        # Test non-numeric value
        self.assertFalse(validate_companion_advantage(self.mock_character, 'Aura', 'abc')[0])
        
        # Test without companion type
        mock_no_type = Mock()
        mock_no_type.get_stat.return_value = None
        self.assertFalse(validate_companion_advantage(mock_no_type, 'Aura', 3)[0])
    
    def test_validate_companion_charm(self):
        """Test charm validation."""
        # Test valid charm
        self.assertTrue(validate_companion_charm(self.mock_character, 'Blast', '3')[0])
        
        # Test invalid charm
        self.assertFalse(validate_companion_charm(self.mock_character, 'Invalid Charm', '3')[0])
        
        # Test invalid value
        self.assertFalse(validate_companion_charm(self.mock_character, 'Blast', '6')[0])
        
        # Test non-numeric value
        self.assertFalse(validate_companion_charm(self.mock_character, 'Blast', 'abc')[0])
        
        # Test without companion type
        mock_no_type = Mock()
        mock_no_type.get_stat.return_value = None
        self.assertFalse(validate_companion_charm(mock_no_type, 'Blast', '3')[0])
    
    def test_validate_companion_stats(self):
        """Test overall companion stat validation."""
        # Test type validation
        self.assertTrue(validate_companion_stats(self.mock_character, 'companion type', 'Spirit')[0])
        
        # Test special advantage validation
        self.assertTrue(validate_companion_stats(
            self.mock_character, 'Aura', '3', 'powers', 'special_advantage'
        )[0])
        
        # Test charm validation
        self.assertTrue(validate_companion_stats(
            self.mock_character, 'Blast', '3', 'powers', 'charm'
        )[0])
        
        # Test invalid type
        self.assertFalse(validate_companion_stats(
            self.mock_character, 'companion type', 'Invalid Type'
        )[0])
        
        # Test invalid advantage
        self.assertFalse(validate_companion_stats(
            self.mock_character, 'Invalid Advantage', '3', 'powers', 'special_advantage'
        )[0])
        
        # Test invalid charm
        self.assertFalse(validate_companion_stats(
            self.mock_character, 'Invalid Charm', '3', 'powers', 'charm'
        )[0])
        
        # Test invalid value
        self.assertFalse(validate_companion_stats(
            self.mock_character, 'Aura', '6', 'powers', 'special_advantage'
        )[0])
        
        # Test non-numeric value
        self.assertFalse(validate_companion_stats(
            self.mock_character, 'Aura', 'abc', 'powers', 'special_advantage'
        )[0])