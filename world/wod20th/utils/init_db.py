import json
from pathlib import Path
from world.wod20th.models import Stat
from django.db import transaction

def load_stats(data_dir):
    """Load all stats from JSON files"""
    import os
    
    # Load basic stats
    basic_stats_path = os.path.join(data_dir, 'attributes_basic_backgrounds.json')
    with open(basic_stats_path) as f:
        basic_stats = json.load(f)
    
    # Load splat-specific abilities
    splat_abilities_path = os.path.join(data_dir, 'splat_abilities.json')
    with open(splat_abilities_path) as f:
        splat_abilities = json.load(f)
    
    # Create basic stats
    with transaction.atomic():
        for stat_data in basic_stats:
            name = stat_data['name']
            category = stat_data.get('category', 'other')
            stat_type = stat_data.get('stat_type', 'other')
            splat = stat_data.get('splat')
            
            # Try to get existing stat with all unique constraints
            existing_stats = Stat.objects.filter(
                name=name,
                category=category,
                stat_type=stat_type,
                splat=splat
            )
            
            if existing_stats.exists():
                # Update the existing stat
                existing_stat = existing_stats.first()
                for key, value in stat_data.items():
                    setattr(existing_stat, key, value)
                existing_stat.save()
                print(f"Updated existing stat: {name}")
            else:
                # Create new stat
                Stat.objects.create(**stat_data)
                print(f"Created new stat: {name}")
    
    # Create splat-specific abilities
    with transaction.atomic():
        for splat, categories in splat_abilities.items():
            for category, abilities in categories.items():
                for ability_data in abilities.values():
                    name = ability_data['name']
                    category = ability_data.get('category', 'abilities')
                    stat_type = ability_data.get('stat_type', category.lower())
                    ability_data['splat'] = splat
                    
                    # Try to get existing stat with all unique constraints
                    existing_stats = Stat.objects.filter(
                        name=name,
                        category=category,
                        stat_type=stat_type,
                        splat=splat
                    )
                    
                    if existing_stats.exists():
                        # Update the existing stat
                        existing_stat = existing_stats.first()
                        for key, value in ability_data.items():
                            setattr(existing_stat, key, value)
                        existing_stat.save()
                        print(f"Updated existing ability: {name} for {splat}")
                    else:
                        # Create new stat
                        Stat.objects.create(**ability_data)
                        print(f"Created new ability: {name} for {splat}") 