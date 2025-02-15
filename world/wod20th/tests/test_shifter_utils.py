"""
Test cases for shifter validation functions.
"""
from django.test import TestCase
from unittest.mock import Mock, patch
from world.wod20th.utils.shifter_utils import (
    validate_shifter_stats, validate_shifter_type,
    validate_shifter_breed, validate_shifter_auspice,
    validate_shifter_tribe, validate_shifter_aspect,
    validate_shifter_gift, SHIFTER_TYPE_CHOICES,
    BREED_CHOICES_DICT, AUSPICE_CHOICES_DICT,
    GAROU_TRIBE_CHOICES, BASTET_TRIBE_CHOICES,
    ASPECT_CHOICES_DICT
)

class TestShifterValidation(TestCase):
    def setUp(self):
        """Set up test data."""
        self.mock_character = Mock()
        # Default values for a Garou
        self.mock_character.get_stat.side_effect = lambda *args, **kwargs: {
            ('identity', 'lineage', 'Type', False): 'Garou',
            ('identity', 'lineage', 'Breed', False): 'Homid',
            ('identity', 'lineage', 'Tribe', False): 'Black Fury',
            ('identity', 'lineage', 'Auspice', False): 'Ahroun'
        }.get((args[0], args[1], args[2], kwargs.get('temp', False)))
    
    def test_validate_shifter_type(self):
        """Test shifter type validation."""
        # Test valid types
        self.assertTrue(validate_shifter_type('Garou')[0])
        self.assertTrue(validate_shifter_type('Bastet')[0])
        self.assertTrue(validate_shifter_type('Corax')[0])
        
        # Test invalid types
        self.assertFalse(validate_shifter_type('Invalid Type')[0])
        self.assertFalse(validate_shifter_type('')[0])
    
    def test_validate_shifter_breed(self):
        """Test breed validation."""
        # Test valid breeds for Garou
        self.assertTrue(validate_shifter_breed('Garou', 'Homid')[0])
        self.assertTrue(validate_shifter_breed('Garou', 'Metis')[0])
        self.assertTrue(validate_shifter_breed('Garou', 'Lupus')[0])
        
        # Test invalid breeds
        self.assertFalse(validate_shifter_breed('Garou', 'Invalid Breed')[0])
        self.assertFalse(validate_shifter_breed('Garou', '')[0])
        
        # Test breeds for invalid shifter type
        self.assertFalse(validate_shifter_breed('Invalid Type', 'Homid')[0])
    
    def test_validate_shifter_auspice(self):
        """Test auspice validation."""
        # Test valid auspices for Garou
        self.assertTrue(validate_shifter_auspice('Garou', 'Ragabash')[0])
        self.assertTrue(validate_shifter_auspice('Garou', 'Theurge')[0])
        self.assertTrue(validate_shifter_auspice('Garou', 'Ahroun')[0])
        
        # Test invalid auspices
        self.assertFalse(validate_shifter_auspice('Garou', 'Invalid Auspice')[0])
        self.assertFalse(validate_shifter_auspice('Garou', '')[0])
        
        # Test auspices for shifter type without auspices
        self.assertFalse(validate_shifter_auspice('Ananasi', 'Ragabash')[0])
    
    def test_validate_shifter_tribe(self):
        """Test tribe validation."""
        # Test valid Garou tribes
        self.assertTrue(validate_shifter_tribe('Garou', 'Black Fury')[0])
        self.assertTrue(validate_shifter_tribe('Garou', 'Shadow Lord')[0])
        
        # Test valid Bastet tribes
        self.assertTrue(validate_shifter_tribe('Bastet', 'Khan')[0])
        self.assertTrue(validate_shifter_tribe('Bastet', 'Simba')[0])
        
        # Test invalid tribes
        self.assertFalse(validate_shifter_tribe('Garou', 'Invalid Tribe')[0])
        self.assertFalse(validate_shifter_tribe('Garou', '')[0])
        
        # Test tribes for shifter type without tribes
        self.assertFalse(validate_shifter_tribe('Corax', 'Black Fury')[0])
    
    def test_validate_shifter_aspect(self):
        """Test aspect validation."""
        # Test valid aspects for Ajaba
        self.assertTrue(validate_shifter_aspect('Ajaba', 'Dawn')[0])
        self.assertTrue(validate_shifter_aspect('Ajaba', 'Midnight')[0])
        
        # Test valid aspects for Ananasi
        self.assertTrue(validate_shifter_aspect('Ananasi', 'Night')[0])
        self.assertTrue(validate_shifter_aspect('Ananasi', 'Daylight')[0])
        
        # Test invalid aspects
        self.assertFalse(validate_shifter_aspect('Ajaba', 'Invalid Aspect')[0])
        self.assertFalse(validate_shifter_aspect('Ajaba', '')[0])
        
        # Test aspects for shifter type without aspects
        self.assertFalse(validate_shifter_aspect('Garou', 'Dawn')[0])
    
    @patch('world.wod20th.models.Stat.objects.filter')
    def test_validate_shifter_gift(self, mock_filter):
        """Test gift validation."""
        # Mock gift query
        mock_gift = Mock()
        mock_gift.breed = 'Homid'
        mock_gift.tribe = 'Black Fury'
        mock_gift.auspice = 'Ahroun'
        mock_filter.return_value.first.return_value = mock_gift
        
        # Test valid gift
        self.assertTrue(validate_shifter_gift(self.mock_character, 'Test Gift', '3')[0])
        
        # Test invalid value
        self.assertFalse(validate_shifter_gift(self.mock_character, 'Test Gift', '6')[0])
        
        # Test non-numeric value
        self.assertFalse(validate_shifter_gift(self.mock_character, 'Test Gift', 'abc')[0])
        
        # Test non-existent gift
        mock_filter.return_value.first.return_value = None
        self.assertFalse(validate_shifter_gift(self.mock_character, 'Invalid Gift', '3')[0])
    
    def test_validate_shifter_stats(self):
        """Test overall shifter stat validation."""
        # Test type validation
        self.assertTrue(validate_shifter_stats(self.mock_character, 'type', 'Garou')[0])
        
        # Test breed validation
        self.assertTrue(validate_shifter_stats(self.mock_character, 'breed', 'Homid')[0])
        
        # Test auspice validation
        self.assertTrue(validate_shifter_stats(self.mock_character, 'auspice', 'Ahroun')[0])
        
        # Test tribe validation
        self.assertTrue(validate_shifter_stats(self.mock_character, 'tribe', 'Black Fury')[0])
        
        # Test gift validation
        with patch('world.wod20th.models.Stat.objects.filter') as mock_filter:
            mock_gift = Mock()
            mock_gift.breed = 'Homid'
            mock_gift.tribe = 'Black Fury'
            mock_gift.auspice = 'Ahroun'
            mock_filter.return_value.first.return_value = mock_gift
            self.assertTrue(validate_shifter_stats(
                self.mock_character, 'Test Gift', '3', 'powers', 'gift'
            )[0])