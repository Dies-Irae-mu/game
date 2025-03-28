"""
Module for loading and exposing ritual data.
"""
import json
import os
from evennia.utils import logger

def _load_rituals():
    """Load ritual data from JSON files."""
    # root directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    data_dir = os.path.join(base_dir, 'data')
    
    # Load Thaumaturgy rituals
    thaum_path = os.path.join(data_dir, 'thaum_rituals.json')
    necro_path = os.path.join(data_dir, 'necromancy_rituals.json')
    
    thaum_rituals = {}
    necro_rituals = {}
    
    try:
        with open(thaum_path, 'r') as f:
            thaum_data = json.load(f)
            for ritual in thaum_data:
                thaum_rituals[ritual['name']] = ritual['values'][0]
    except Exception as e:
        logger.log_err(f"Error loading thaumaturgy rituals: {str(e)}")
        
    try:
        with open(necro_path, 'r') as f:
            necro_data = json.load(f)
            for ritual in necro_data:
                necro_rituals[ritual['name']] = ritual['values'][0]
    except Exception as e:
        logger.log_err(f"Error loading necromancy rituals: {str(e)}")
    
    return thaum_rituals, necro_rituals

# Load rituals at module import
THAUMATURGY_RITUALS, NECROMANCY_RITUALS = _load_rituals() 