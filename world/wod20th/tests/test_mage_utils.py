"""
Test cases for mage validation functions.
"""
from django.test import TestCase
from unittest.mock import Mock, patch
from world.wod20th.utils.mage_utils import (
    validate_mage_stats, validate_mage_affiliation,
    validate_mage_tradition, validate_mage_convention,
    validate_mage_methodology, validate_mage_subfaction,
    validate_mage_sphere, validate_mage_backgrounds,
    AFFILIATION, TRADITION, CONVENTION, METHODOLOGIES,
    TRADITION_SUBFACTION, MAGE_SPHERES
)
from world.wod20th.utils.stat_mappings import (
    UNIVERSAL_BACKGROUNDS, MAGE_BACKGROUNDS,
    TECHNOCRACY_BACKGROUNDS, TRADITIONS_BACKGROUNDS,
    NEPHANDI_BACKGROUNDS
)

class TestMageValidation(TestCase):
    def setUp(self):
        """Set up test data."""
        self.mock_character = Mock()
        # Default values for a Traditions mage
        self.mock_character.get_stat.side_effect = lambda *args, **kwargs: {
            ('identity', 'lineage', 'Affiliation', False): 'Traditions',
            ('identity', 'lineage', 'Tradition', False): 'Order of Hermes',
            ('identity', 'lineage', 'Convention', False): None,
            ('powers', 'sphere', 'Forces', False): 3,
            ('backgrounds', 'background', 'Avatar', False): 3
        }.get((args[0], args[1], args[2], kwargs.get('temp', False)))
    
    def test_validate_mage_affiliation(self):
        """Test affiliation validation."""
        # Test valid affiliations
        self.assertTrue(validate_mage_affiliation('Traditions')[0])
        self.assertTrue(validate_mage_affiliation('Technocracy')[0])
        self.assertTrue(validate_mage_affiliation('Nephandi')[0])
        
        # Test invalid affiliations
        self.assertFalse(validate_mage_affiliation('Invalid Affiliation')[0])
        self.assertFalse(validate_mage_affiliation('')[0])
    
    def test_validate_mage_tradition(self):
        """Test tradition validation."""
        # Test valid traditions
        self.assertTrue(validate_mage_tradition('Order of Hermes')[0])
        self.assertTrue(validate_mage_tradition('Verbena')[0])
        self.assertTrue(validate_mage_tradition('Virtual Adepts')[0])
        
        # Test invalid traditions
        self.assertFalse(validate_mage_tradition('Invalid Tradition')[0])
        self.assertFalse(validate_mage_tradition('')[0])
    
    def test_validate_mage_convention(self):
        """Test convention validation."""
        # Test valid conventions
        self.assertTrue(validate_mage_convention('Iteration X')[0])
        self.assertTrue(validate_mage_convention('New World Order')[0])
        self.assertTrue(validate_mage_convention('Progenitors')[0])
        
        # Test invalid conventions
        self.assertFalse(validate_mage_convention('Invalid Convention')[0])
        self.assertFalse(validate_mage_convention('')[0])
    
    def test_validate_mage_methodology(self):
        """Test methodology validation."""
        # Set up mock character as Technocrat
        mock_technocrat = Mock()
        mock_technocrat.get_stat.side_effect = lambda *args, **kwargs: {
            ('identity', 'lineage', 'Convention', False): 'Iteration X',
            ('identity', 'lineage', 'Affiliation', False): 'Technocracy'
        }.get((args[0], args[1], args[2], kwargs.get('temp', False)))
        
        # Test valid methodology for convention
        self.assertTrue(validate_mage_methodology(mock_technocrat, 'BioMechanics')[0])
        
        # Test invalid methodology
        self.assertFalse(validate_mage_methodology(mock_technocrat, 'Invalid Method')[0])
        
        # Test methodology without convention
        mock_no_convention = Mock()
        mock_no_convention.get_stat.return_value = None
        self.assertFalse(validate_mage_methodology(mock_no_convention, 'BioMechanics')[0])
    
    def test_validate_mage_subfaction(self):
        """Test tradition subfaction validation."""
        # Test valid subfaction for tradition
        self.assertTrue(validate_mage_subfaction(self.mock_character, 'House Flambeau')[0])
        
        # Test invalid subfaction
        self.assertFalse(validate_mage_subfaction(self.mock_character, 'Invalid Subfaction')[0])
        
        # Test subfaction without tradition
        mock_no_tradition = Mock()
        mock_no_tradition.get_stat.return_value = None
        self.assertFalse(validate_mage_subfaction(mock_no_tradition, 'House Flambeau')[0])
    
    def test_validate_mage_sphere(self):
        """Test sphere validation."""
        # Test valid sphere
        self.assertTrue(validate_mage_sphere(self.mock_character, 'Forces', '3')[0])
        
        # Test invalid sphere
        self.assertFalse(validate_mage_sphere(self.mock_character, 'Invalid Sphere', '3')[0])
        
        # Test invalid value
        self.assertFalse(validate_mage_sphere(self.mock_character, 'Forces', '6')[0])
        
        # Test non-numeric value
        self.assertFalse(validate_mage_sphere(self.mock_character, 'Forces', 'abc')[0])
    
    def test_validate_mage_backgrounds(self):
        """Test background validation."""
        # Test valid universal background
        self.assertTrue(validate_mage_backgrounds(self.mock_character, 'Resources', '3')[0])
        
        # Test valid mage background
        self.assertTrue(validate_mage_backgrounds(self.mock_character, 'Avatar', '3')[0])
        
        # Test invalid background
        self.assertFalse(validate_mage_backgrounds(self.mock_character, 'Invalid Background', '3')[0])
        
        # Test invalid value
        self.assertFalse(validate_mage_backgrounds(self.mock_character, 'Resources', '6')[0])
        
        # Test non-numeric value
        self.assertFalse(validate_mage_backgrounds(self.mock_character, 'Resources', 'abc')[0])
    
    def test_validate_mage_stats(self):
        """Test overall mage stat validation."""
        # Test affiliation validation
        self.assertTrue(validate_mage_stats(self.mock_character, 'affiliation', 'Traditions')[0])
        
        # Test tradition validation
        self.assertTrue(validate_mage_stats(self.mock_character, 'tradition', 'Order of Hermes')[0])
        
        # Test sphere validation
        self.assertTrue(validate_mage_stats(
            self.mock_character, 'Forces', '3', 'powers', 'sphere'
        )[0])
        
        # Test background validation
        self.assertTrue(validate_mage_stats(
            self.mock_character, 'Avatar', '3', 'backgrounds', 'background'
        )[0]) 