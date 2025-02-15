"""
Test cases for vampire validation functions.
"""
from django.test import TestCase
from unittest.mock import Mock, patch
from world.wod20th.utils.sheet_constants import PATHS_OF_ENLIGHTENMENT
from world.wod20th.utils.virtue_utils import PATH_VIRTUES
from world.wod20th.utils.vampire_utils import (
    validate_vampire_stats, validate_vampire_clan,
    validate_vampire_generation, validate_vampire_discipline,
    validate_vampire_background, validate_vampire_path
)
from world.wod20th.utils.stat_mappings import UNIVERSAL_BACKGROUNDS, VAMPIRE_BACKGROUNDS

class TestVampireValidation(TestCase):
    def setUp(self):
        """Set up test data."""
        self.mock_character = Mock()
        # Set up get_stat to return different values based on arguments
        self.mock_character.get_stat.side_effect = lambda *args, **kwargs: {
            ('identity', 'lineage', 'Clan', False): 'Ventrue',
            ('identity', 'personal', 'Path of Enlightenment', False): 'Humanity'
        }.get((args[0], args[1], args[2], kwargs.get('temp', False)))
    
    def test_validate_vampire_clan(self):
        """Test clan validation."""
        # Test valid clans
        self.assertTrue(validate_vampire_clan('Ventrue')[0])
        self.assertTrue(validate_vampire_clan('Tremere')[0])
        self.assertTrue(validate_vampire_clan('Brujah')[0])
        
        # Test invalid clans
        self.assertFalse(validate_vampire_clan('Invalid Clan')[0])
        self.assertFalse(validate_vampire_clan('')[0])
    
    def test_validate_vampire_generation(self):
        """Test generation validation."""
        # Test valid generations
        self.assertTrue(validate_vampire_generation('13')[0])
        self.assertTrue(validate_vampire_generation('8')[0])
        self.assertTrue(validate_vampire_generation('6')[0])
        
        # Test invalid generations
        self.assertFalse(validate_vampire_generation('5')[0])  # Too low
        self.assertFalse(validate_vampire_generation('16')[0])  # Too high
        self.assertFalse(validate_vampire_generation('abc')[0])  # Not a number
    
    def test_validate_vampire_disciplines(self):
        """Test discipline validation."""
        # Mock clan disciplines
        with patch('world.wod20th.utils.vampire_utils.get_clan_disciplines') as mock_get_disciplines:
            mock_get_disciplines.return_value = ['Dominate', 'Fortitude', 'Presence']
            
            # Test valid discipline
            is_valid, msg = validate_vampire_discipline(self.mock_character, 'Dominate', '3')
            self.assertTrue(is_valid)
            
            # Test invalid discipline
            is_valid, msg = validate_vampire_discipline(self.mock_character, 'Obfuscate', '3')
            self.assertFalse(is_valid)
            
            # Test invalid value
            is_valid, msg = validate_vampire_discipline(self.mock_character, 'Dominate', '6')
            self.assertFalse(is_valid)
            
            # Test non-numeric value
            is_valid, msg = validate_vampire_discipline(self.mock_character, 'Dominate', 'abc')
            self.assertFalse(is_valid)
    
    def test_validate_vampire_backgrounds(self):
        """Test background validation."""
        # Test valid universal background
        self.assertTrue(validate_vampire_background('Resources', '3')[0])
        
        # Test valid vampire background
        self.assertTrue(validate_vampire_background('Generation', '2')[0])
        
        # Test invalid background
        self.assertFalse(validate_vampire_background('Invalid Background', '3')[0])
        
        # Test invalid value
        self.assertFalse(validate_vampire_background('Resources', '6')[0])
        
        # Test non-numeric value
        self.assertFalse(validate_vampire_background('Resources', 'abc')[0])
    
    def test_validate_vampire_path(self):
        """Test path of enlightenment validation."""
        # Test valid paths
        self.assertTrue(validate_vampire_path('Humanity')[0])
        self.assertTrue(validate_vampire_path('Night')[0])
        
        # Test invalid paths
        self.assertFalse(validate_vampire_path('Invalid Path')[0])
        self.assertFalse(validate_vampire_path('')[0])
    
    def test_validate_vampire_stats(self):
        """Test overall vampire stat validation."""
        # Test clan validation
        self.assertTrue(validate_vampire_stats(self.mock_character, 'clan', 'Ventrue')[0])
        
        # Test generation validation
        self.assertTrue(validate_vampire_stats(self.mock_character, 'generation', '8')[0])
        
        # Test discipline validation
        with patch('world.wod20th.utils.vampire_utils.get_clan_disciplines') as mock_get_disciplines:
            mock_get_disciplines.return_value = ['Dominate', 'Fortitude', 'Presence']
            result = validate_vampire_stats(
                self.mock_character, 'Dominate', '3', 'powers', 'discipline'
            )
            self.assertTrue(result[0], f"Failed to validate discipline. Error: {result[1]}")
        
        # Test background validation
        self.assertTrue(validate_vampire_stats(
            self.mock_character, 'Resources', '3', 'backgrounds', 'background'
        )[0])
        
        # Test path validation
        print("\nTesting path validation...")
        print(f"Calling validate_vampire_stats with: stat_name='path', value='Humanity', category='identity', stat_type='personal'")
        result, msg = validate_vampire_stats(
            self.mock_character, 'path', 'Humanity', 'identity', 'personal'
        )
        print(f"Path validation result: {result}, message: {msg}")
        print(f"PATH_VIRTUES keys: {sorted(PATH_VIRTUES.keys())}")
        print(f"PATHS_OF_ENLIGHTENMENT values: {sorted(PATHS_OF_ENLIGHTENMENT.values())}")
        print(f"Value 'Humanity' in PATH_VIRTUES: {'Humanity' in PATH_VIRTUES}")
        print(f"Value 'Humanity' in PATHS_OF_ENLIGHTENMENT.values(): {'Humanity' in PATHS_OF_ENLIGHTENMENT.values()}")
        self.assertTrue(result) 