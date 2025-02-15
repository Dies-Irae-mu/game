"""
Test cases for changeling validation functions.
"""
from django.test import TestCase
from unittest.mock import Mock, patch
from world.wod20th.utils.changeling_utils import (
    validate_changeling_stats, validate_changeling_kith,
    validate_changeling_seeming, validate_changeling_house,
    validate_changeling_legacy, validate_changeling_art,
    validate_changeling_realm, validate_changeling_backgrounds,
    KITH, SEEMING, SEELIE_LEGACIES, UNSEELIE_LEGACIES,
    ARTS, REALMS
)
from world.wod20th.utils.stat_mappings import UNIVERSAL_BACKGROUNDS, CHANGELING_BACKGROUNDS

class TestChangelingValidation(TestCase):
    def setUp(self):
        """Set up test data."""
        self.mock_character = Mock()
        # Default values for a Changeling
        self.mock_character.get_stat.side_effect = lambda *args, **kwargs: {
            ('identity', 'lineage', 'Kith', False): 'Arcadian Sidhe',
            ('identity', 'lineage', 'Seeming', False): 'Wilder',
            ('identity', 'lineage', 'House', False): 'Gwydion',
            ('identity', 'lineage', 'Seelie Legacy', False): 'Paladin',
            ('identity', 'lineage', 'Unseelie Legacy', False): 'Rogue'
        }.get((args[0], args[1], args[2], kwargs.get('temp', False)))
    
    def test_validate_changeling_kith(self):
        """Test kith validation."""
        # Test valid kiths
        self.assertTrue(validate_changeling_kith('Arcadian Sidhe')[0])
        self.assertTrue(validate_changeling_kith('Troll')[0])
        self.assertTrue(validate_changeling_kith('Pooka')[0])
        
        # Test invalid kiths
        self.assertFalse(validate_changeling_kith('Invalid Kith')[0])
        self.assertFalse(validate_changeling_kith('')[0])
    
    def test_validate_changeling_seeming(self):
        """Test seeming validation."""
        # Test valid seemings for standard changelings
        self.assertTrue(validate_changeling_seeming(self.mock_character, 'Childing')[0])
        self.assertTrue(validate_changeling_seeming(self.mock_character, 'Wilder')[0])
        self.assertTrue(validate_changeling_seeming(self.mock_character, 'Grump')[0])
        
        # Test valid seemings for Nunnehi
        nunnehi_character = Mock()
        nunnehi_character.get_stat.return_value = 'Nunnehi'
        self.assertTrue(validate_changeling_seeming(nunnehi_character, 'Youngling')[0])
        self.assertTrue(validate_changeling_seeming(nunnehi_character, 'Brave')[0])
        self.assertTrue(validate_changeling_seeming(nunnehi_character, 'Elder')[0])
        
        # Test invalid seemings
        self.assertFalse(validate_changeling_seeming(self.mock_character, 'Invalid Seeming')[0])
        self.assertFalse(validate_changeling_seeming(self.mock_character, '')[0])
    
    def test_validate_changeling_house(self):
        """Test house validation."""
        # Test valid houses
        self.assertTrue(validate_changeling_house('Gwydion')[0])
        self.assertTrue(validate_changeling_house('Eiluned')[0])
        self.assertTrue(validate_changeling_house('Fiona')[0])
        
        # Test invalid houses
        self.assertFalse(validate_changeling_house('Invalid House')[0])
        self.assertFalse(validate_changeling_house('')[0])
    
    def test_validate_changeling_legacy(self):
        """Test legacy validation."""
        # Test valid Seelie legacies
        self.assertTrue(validate_changeling_legacy('seelie legacy', 'Paladin')[0])
        self.assertTrue(validate_changeling_legacy('seelie legacy', 'Sage')[0])
        
        # Test valid Unseelie legacies
        self.assertTrue(validate_changeling_legacy('unseelie legacy', 'Rogue')[0])
        self.assertTrue(validate_changeling_legacy('unseelie legacy', 'Beast')[0])
        
        # Test invalid legacies
        self.assertFalse(validate_changeling_legacy('seelie legacy', 'Invalid Legacy')[0])
        self.assertFalse(validate_changeling_legacy('unseelie legacy', 'Invalid Legacy')[0])
        self.assertFalse(validate_changeling_legacy('seelie legacy', '')[0])
    
    def test_validate_changeling_art(self):
        """Test art validation."""
        # Test valid art
        self.assertTrue(validate_changeling_art(self.mock_character, 'Chicanery', '3')[0])
        
        # Test invalid art
        self.assertFalse(validate_changeling_art(self.mock_character, 'Invalid Art', '3')[0])
        
        # Test invalid value
        self.assertFalse(validate_changeling_art(self.mock_character, 'Chicanery', '6')[0])
        
        # Test non-numeric value
        self.assertFalse(validate_changeling_art(self.mock_character, 'Chicanery', 'abc')[0])
    
    def test_validate_changeling_realm(self):
        """Test realm validation."""
        # Test valid realm
        self.assertTrue(validate_changeling_realm(self.mock_character, 'Actor', '3')[0])
        
        # Test invalid realm
        self.assertFalse(validate_changeling_realm(self.mock_character, 'Invalid Realm', '3')[0])
        
        # Test invalid value
        self.assertFalse(validate_changeling_realm(self.mock_character, 'Actor', '6')[0])
        
        # Test non-numeric value
        self.assertFalse(validate_changeling_realm(self.mock_character, 'Actor', 'abc')[0])
    
    def test_validate_changeling_backgrounds(self):
        """Test background validation."""
        # Test valid universal background
        self.assertTrue(validate_changeling_backgrounds(self.mock_character, 'Resources', '3')[0])
        
        # Test valid changeling background
        self.assertTrue(validate_changeling_backgrounds(self.mock_character, 'Title', '3')[0])
        
        # Test invalid background
        self.assertFalse(validate_changeling_backgrounds(self.mock_character, 'Invalid Background', '3')[0])
        
        # Test invalid value
        self.assertFalse(validate_changeling_backgrounds(self.mock_character, 'Resources', '6')[0])
        
        # Test non-numeric value
        self.assertFalse(validate_changeling_backgrounds(self.mock_character, 'Resources', 'abc')[0])
    
    def test_validate_changeling_stats(self):
        """Test overall changeling stat validation."""
        # Test kith validation
        self.assertTrue(validate_changeling_stats(self.mock_character, 'kith', 'Arcadian Sidhe')[0])
        
        # Test seeming validation
        self.assertTrue(validate_changeling_stats(self.mock_character, 'seeming', 'Wilder')[0])
        
        # Test house validation
        self.assertTrue(validate_changeling_stats(self.mock_character, 'house', 'Gwydion')[0])
        
        # Test legacy validation
        self.assertTrue(validate_changeling_stats(self.mock_character, 'seelie legacy', 'Paladin')[0])
        self.assertTrue(validate_changeling_stats(self.mock_character, 'unseelie legacy', 'Rogue')[0])
        
        # Test art validation
        self.assertTrue(validate_changeling_stats(
            self.mock_character, 'Chicanery', '3', 'powers', 'art'
        )[0])
        
        # Test realm validation
        self.assertTrue(validate_changeling_stats(
            self.mock_character, 'Actor', '3', 'powers', 'realm'
        )[0])
        
        # Test background validation
        self.assertTrue(validate_changeling_stats(
            self.mock_character, 'Title', '3', 'backgrounds', 'background'
        )[0]) 