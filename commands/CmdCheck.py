from evennia.commands.default.muxcommand import MuxCommand
from world.wod20th.models import Stat

class CmdCheck(MuxCommand):
    """
    Check character creation points allocation.

    Usage:
      +check
      +check <character>     (Staff only)

    This command verifies that a character's attributes, abilities,
    backgrounds, and other traits are properly allocated according
    to the character creation rules.
    """

    key = "+check"
    aliases = ["check"]
    locks = "cmd:all() or perm(Builder) or perm(Admin) or perm(Developer)"
    help_category = "Chargen & Character Info"

    # Load combo disciplines from JSON files
    def __init__(self):
        super().__init__()
        self.COMBO_DISCIPLINES = self.load_combo_disciplines()

    def load_combo_disciplines(self):
        """Load and process combo disciplines from JSON files."""
        import json
        import os
        from pathlib import Path

        combo_dict = {}
        data_dir = Path(__file__).parent.parent / 'data'
        
        # List of combo discipline JSON files
        combo_files = ['combo_disciplines.json', 'combo_disciplines2.json']
        
        for file_name in combo_files:
            file_path = data_dir / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for combo in data:
                            if 'name' in combo and 'prerequisites' in combo and 'xp_cost' in combo:
                                combo_dict[combo['name']] = {
                                    'cost': combo['xp_cost'],
                                    'prerequisites': combo['prerequisites']
                                }
                except Exception as e:
                    self.caller.msg(f"Error loading {file_name}: {str(e)}")
        
        return combo_dict

    FREEBIE_COSTS = {
        'attribute': 5,
        'ability': 2,
        'secondary_ability': 1,
        'background': 1,
        'willpower': 2,
        'virtue': 2,
        'merit': 1,
        'flaw': -1,  # Flaws add points
        # Splat-specific costs
        'gift': 7,
        'kinfolk_gift': 10,  # Special cost for Kinfolk with Gnosis
        'rage': 1,
        'gnosis': 2,
        'art': 5,
        'sliver': 5,
        'glamour': 3,
        'realm': 2,
        'arete': 4,
        'quintessence': 0.25,  # 1 per 4 dots
        'sphere': 7,
        'discipline': 7,
        'path': 2,
        'numina': 7,
        'sorcery': 7,
        'hedge_ritual': 3,
        'faith': 7
    }

    XP_COSTS = {
        'attribute': 4,
        'ability': 2,
        'specialty': 1,
        'background': 3,
        'willpower': 1,
        'virtue': 2,
        # Splat-specific costs
        'gift': 3,
        'rage': 1,
        'gnosis': 2,
        'sphere': 7,
        'arete': 8,
        'quintessence': 1,  # per point
        'discipline': 5,
        'path': 2,
        'art': 4,
        'glamour': 3,
        'realm': 2,
        'combo_discipline': 0  # Cost is defined per combo in COMBO_DISCIPLINES
    }

    # Add PATH_VIRTUES at class level
    PATH_VIRTUES = {
        'Humanity': ['Conscience', 'Self-Control', 'Courage'],
        'Night': ['Conviction', 'Instinct', 'Courage'],
        'Metamorphosis': ['Conviction', 'Instinct', 'Courage'],
        'Beast': ['Conviction', 'Instinct', 'Courage'],
        'Harmony': ['Conscience', 'Instinct', 'Courage'],
        'Evil Revelations': ['Conviction', 'Self-Control', 'Courage'],
        'Self-Focus': ['Conviction', 'Instinct', 'Courage'],
        'Scorched Heart': ['Conviction', 'Self-Control', 'Courage'],
        'Entelechy': ['Conviction', 'Self-Control', 'Courage'],
        'Sharia El-Sama': ['Conscience', 'Self-Control', 'Courage'],
        'Asakku': ['Conviction', 'Instinct', 'Courage'],
        'Death and the Soul': ['Conviction', 'Self-Control', 'Courage'],
        'Honorable Accord': ['Conscience', 'Self-Control', 'Courage'],
        'Feral Heart': ['Conviction', 'Instinct', 'Courage'],
        'Orion': ['Conviction', 'Instinct', 'Courage'],
        'Power and the Inner Voice': ['Conviction', 'Instinct', 'Courage'],
        'Lilith': ['Conviction', 'Instinct', 'Courage'],
        'Caine': ['Conviction', 'Instinct', 'Courage'],
        'Cathari': ['Conviction', 'Instinct', 'Courage'],
        'Redemption': ['Conscience', 'Self-Control', 'Courage'],
        'Bones': ['Conviction', 'Self-Control', 'Courage'],
        'Typhon': ['Conviction', 'Self-Control', 'Courage'],
        'Paradox': ['Conviction', 'Self-Control', 'Courage'],
        'Blood': ['Conviction', 'Self-Control', 'Courage'],
        'Hive': ['Conviction', 'Instinct', 'Courage']
    }

    # Define secondary abilities that cost half the normal amount
    SECONDARY_ABILITIES = {
        'secondary_talent': {
            'Artistry', 'Carousing', 'Diplomacy', 'Intrigue', 'Mimicry', 'Scrounging', 'Seduction', 'Style',
            # Mage-specific secondaries will be added dynamically
            'High Ritual', 'Blatancy', 'Lucid Dreaming', 'Flying'
        },
        'secondary_skill': {
            'Archery', 'Fortune-Telling', 'Fencing', 'Gambling', 'Jury-Rigging', 'Pilot', 'Torture',
            # Mage-specific secondaries will be added dynamically
            'Do', 'Microgravity Ops', 'Energy Weapons', 'Helmsman', 'Biotech'
        },
        'secondary_knowledge': {
            'Area Knowledge', 'Cultural Savvy', 'Demolitions', 'Herbalism', 'Media', 'Power-Brokering', 'Vice',
            # Mage-specific secondaries will be added dynamically
            'Hypertech', 'Cybernetics', 'Paraphysics', 'Xenobiology'
        }
    }

    def func(self):
        """Execute the command."""
        caller = self.caller

        if not self.args:
            # If no args, check the caller's own character
            character = caller
        else:
            # If args provided, use global search
            character = caller.search(self.args, global_search=True)
            if not character:
                return
            # Only staff can check other characters
            if not caller.check_permstring("Builder"):
                caller.msg("You don't have permission to check other characters.")
                return

        # Initialize results dictionary with all necessary keys
        results = {
            'attributes': {'primary': 0, 'secondary': 0, 'tertiary': 0},
            'abilities': {'primary': {'category': '', 'points': 0}, 'secondary': {'category': '', 'points': 0}, 'tertiary': {'category': '', 'points': 0}},
            'backgrounds': 0,
            'merits': 0,
            'flaws': 0,
            'freebies_spent': 0,
            'total_freebies': 15,
            'errors': [],
            'secondary_abilities': {
                'secondary_talent': {},
                'secondary_skill': {},
                'secondary_knowledge': {},
                'primary': {'category': '', 'points': 0},
                'secondary': {'category': '', 'points': 0},
                'tertiary': {'category': '', 'points': 0}
            },
            'willpower': 0,  # Initialize willpower
            'arete': 0,      # Initialize other power stats
            'gnosis': 0,
            'rage': 0,
            'glamour': 0
        }

        try:
            # Verify character has stats
            if not hasattr(character, 'db') or not character.db.stats:
                caller.msg(f"Error: Character {character.name} has no stats attribute.")
                return

            # Get willpower value
            results['willpower'] = character.get_stat('pools', 'dual', 'Willpower', temp=False) or 0

            # Run all checks
            self.check_attributes(character, results)
            self.check_abilities(character, results)
            self.check_backgrounds(character, results)
            self.check_free_dots(character, results)
            self.calculate_freebies(character, results)
            self.common_identity_attributes(character, results)

            # Display results
            output = self.display_results(character, results)
            caller.msg(output)
        except Exception as e:
            caller.msg(f"Error checking character {character.name}: {str(e)}")
            return

    def check_attributes(self, character, results):
        """Check attribute point allocation."""
        attribute_categories = ['physical', 'social', 'mental']
        attribute_totals = []

        for category in attribute_categories:
            total = 0
            attributes = character.db.stats.get('attributes', {}).get(category, {})
            for attr, values in attributes.items():
                # Get the permanent value, defaulting to 1 (all attributes start at 1)
                attr_value = values.get('perm', 1) - 1
                if attr_value > 0:
                    total += attr_value
            attribute_totals.append((category, total))

        # Sort totals to determine primary/secondary/tertiary
        attribute_totals.sort(key=lambda x: x[1], reverse=True)
        
        # Check against expected values
        if attribute_totals[0][1] != 7:
            results['errors'].append(f"Primary attributes ({attribute_totals[0][0]}) should have 7 points, has {attribute_totals[0][1]}")
        if attribute_totals[1][1] != 5:
            results['errors'].append(f"Secondary attributes ({attribute_totals[1][0]}) should have 5 points, has {attribute_totals[1][1]}")
        if attribute_totals[2][1] != 3:
            results['errors'].append(f"Tertiary attributes ({attribute_totals[2][0]}) should have 3 points, has {attribute_totals[2][1]}")

        results['attributes']['primary'] = attribute_totals[0][1]
        results['attributes']['secondary'] = attribute_totals[1][1]
        results['attributes']['tertiary'] = attribute_totals[2][1]

    def check_abilities(self, character, results):
        """Check ability point allocation."""
        # First, collect all ability points across all categories
        all_ability_points = []

        # Get secondary abilities for this character's splat
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        secondary_abilities = self.get_secondary_abilities(splat)

        # Initialize secondary_abilities in results with proper structure
        results['secondary_abilities'] = {
            'secondary_talent': {},
            'secondary_skill': {},
            'secondary_knowledge': {},
            'primary': {'category': '', 'points': 0},
            'secondary': {'category': '', 'points': 0},
            'tertiary': {'category': '', 'points': 0}
        }

        # Track totals for each category including secondary abilities
        category_totals = {
            'talent': {'regular': 0, 'secondary': 0},
            'skill': {'regular': 0, 'secondary': 0},
            'knowledge': {'regular': 0, 'secondary': 0}
        }

        for category in ['talent', 'skill', 'knowledge']:
            # Check regular abilities
            abilities = character.db.stats.get('abilities', {}).get(category, {})
            for ability, values in abilities.items():
                ability_value = min(values.get('perm', 0), 3)  # Cap at 3 for initial point allocation
                if ability_value > 0:
                    category_totals[category]['regular'] += ability_value

            # Check secondary abilities category
            secondary_category = f'secondary_{category}'
            # Fix: Get secondary abilities from the correct path
            secondary_abilities_dict = character.db.stats.get('secondary_abilities', {}).get(secondary_category, {})
            for ability, values in secondary_abilities_dict.items():
                ability_value = values.get('perm', 0)
                if ability_value > 0:
                    category_totals[category]['secondary'] += ability_value * 0.5  # Secondary abilities cost half points
                    # Store in results
                    secondary_category = f'secondary_{category}'  # Use consistent naming with 'secondary_' prefix
                    results['secondary_abilities'][secondary_category][ability] = ability_value

        # Calculate total points for each category
        for category, totals in category_totals.items():
            total_points = totals['regular'] + totals['secondary']
            if total_points > 0:
                all_ability_points.append((category, total_points))

        # Sort all categories by their point totals
        all_ability_points.sort(key=lambda x: x[1], reverse=True)

        # Pad the list if we have fewer than 3 categories with points
        while len(all_ability_points) < 3:
            all_ability_points.append(('unused', 0))

        # Store the results for both abilities and secondary_abilities
        priority_levels = ['primary', 'secondary', 'tertiary']
        for i, priority in enumerate(priority_levels):
            results['abilities'][priority] = {
                'category': all_ability_points[i][0],
                'points': all_ability_points[i][1]
            }
            results['secondary_abilities'][priority] = {
                'category': all_ability_points[i][0],
                'points': category_totals[all_ability_points[i][0]]['secondary'] if i < len(all_ability_points) and all_ability_points[i][0] in category_totals else 0
            }

        # Check against expected values
        if all_ability_points[0][1] > 13:
            results['errors'].append(f"Primary abilities ({all_ability_points[0][0]}) should have 13 points, has {all_ability_points[0][1]}")
        elif all_ability_points[0][1] < 13:
            results['errors'].append(f"Primary abilities ({all_ability_points[0][0]}) should have 13 points, has {all_ability_points[0][1]}")

        if all_ability_points[1][1] > 9:
            results['errors'].append(f"Secondary abilities ({all_ability_points[1][0]}) should have 9 points, has {all_ability_points[1][1]}")
        elif all_ability_points[1][1] < 9:
            results['errors'].append(f"Secondary abilities ({all_ability_points[1][0]}) should have 9 points, has {all_ability_points[1][1]}")

        if all_ability_points[2][1] > 5:
            results['errors'].append(f"Tertiary abilities ({all_ability_points[2][0]}) should have 5 points, has {all_ability_points[2][1]}")
        elif all_ability_points[2][1] < 5:
            results['errors'].append(f"Tertiary abilities ({all_ability_points[2][0]}) should have 5 points, has {all_ability_points[2][1]}")

    def check_backgrounds(self, character, results):
        """Check background point allocation."""
        total_backgrounds = 0
        backgrounds = character.db.stats.get('backgrounds', {}).get('background', {})
        
        for background, values in backgrounds.items():
            background_value = values.get('perm', 0)
            total_backgrounds += background_value

        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        expected_backgrounds = 7 if splat.lower() == 'mage' else 5

        if total_backgrounds != expected_backgrounds:
            results['errors'].append(f"Backgrounds should have {expected_backgrounds} points, has {total_backgrounds}")

        results['backgrounds'] = total_backgrounds

    def check_free_dots(self, character, results):
        """Check that free dots are properly allocated."""
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower()
        
        # Check merits and flaws
        merit_categories = ['merit', 'physical', 'social', 'mental', 'supernatural']
        flaw_categories = ['flaw', 'physical', 'social', 'mental', 'supernatural']
        
        merit_dots = 0
        flaw_dots = 0
        
        # Calculate total merit dots
        merits = character.db.stats.get('merits', {})
        for category in merit_categories:
            category_merits = merits.get(category, {})
            merit_dots += sum(values.get('perm', 0) for values in category_merits.values())
        
        # Calculate total flaw dots
        flaws = character.db.stats.get('flaws', {})
        for category in flaw_categories:
            category_flaws = flaws.get(category, {})
            flaw_dots += sum(values.get('perm', 0) for values in category_flaws.values())
        
        results['merits'] = merit_dots
        results['flaws'] = flaw_dots
        
        if flaw_dots > 7:
            results['errors'].append(f"Character has too many flaw dots ({flaw_dots}). Maximum allowed is 7.")

        # Special handling for Possessed gifts
        if splat == 'possessed':
            possessed_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Possessed Type', {}).get('perm')
            blessings = character.db.stats.get('powers', {}).get('blessing', {})
            blessing_count = len(blessings) if blessings else 0
            max_blessings = 4 if possessed_type == 'Fomori' else 3
            
            if blessing_count > max_blessings:
                results['errors'].append(f"Possessed may only have {max_blessings} blessings (currently has {blessing_count})")
                
            # Check if they're trying to buy blessings with freebies
            if blessing_count > 3:  # More than the free ones
                results['errors'].append("Possessed cannot buy additional blessings with freebie points")

        if splat == 'vampire':
            # Check for 3 discipline dots
            disciplines = character.db.stats.get('powers', {}).get('discipline', {})
            thaumaturgy = character.db.stats.get('powers', {}).get('thaumaturgy', {})
            necromancy = character.db.stats.get('powers', {}).get('necromancy', {})
            total_dots = sum(values.get('perm', 0) for values in disciplines.values()) + sum(values.get('perm', 0) for values in thaumaturgy.values()) + sum(values.get('perm', 0) for values in necromancy.values())
            if total_dots < 3:
                results['errors'].append(f"Vampire should have at least 3 discipline dots (has {total_dots})")
            elif total_dots > 3:
                results['errors'].append(f"Vampire should only have 3 discipline dots at creation (has {total_dots}).")

            # Check combo disciplines
            combos = character.db.stats.get('powers', {}).get('combodiscipline', {})
            for combo_name, values in combos.items():
                combo_value = values.get('perm', 0)
                if combo_value > 0:
                    # Check if combo exists in our loaded data
                    if combo_name not in self.COMBO_DISCIPLINES:
                        results['errors'].append(f"Invalid combo discipline: {combo_name}")
                        continue
                    
                    # Check prerequisites
                    has_prereqs = True
                    missing_prereqs = []
                    for prereq in self.COMBO_DISCIPLINES[combo_name]['prerequisites']:
                        # Split on the last space to get the level
                        parts = prereq.rsplit(' ', 1)
                        if len(parts) != 2:
                            has_prereqs = False
                            missing_prereqs.append(prereq)
                            continue
                        
                        discipline, level_str = parts
                        try:
                            level = int(level_str)
                        except ValueError:
                            has_prereqs = False
                            missing_prereqs.append(prereq)
                            continue
                        
                        # Handle special case for Thaumaturgy paths
                        if 'Thaumaturgy' in discipline:
                            thaum_paths = character.db.stats.get('powers', {}).get('thaumaturgy', {})
                            highest_path = max([v.get('perm', 0) for v in thaum_paths.values()], default=0)
                            if highest_path < level:
                                has_prereqs = False
                                missing_prereqs.append(prereq)
                        elif 'Necromancy' in discipline:
                            necro_paths = character.db.stats.get('powers', {}).get('necromancy', {})
                            highest_path = max([v.get('perm', 0) for v in necro_paths.values()], default=0)
                            if highest_path < level:
                                has_prereqs = False
                                missing_prereqs.append(prereq)
                        else:
                            # Remove any parenthetical text from discipline name
                            discipline = discipline.split('(')[0].strip()
                            disc_value = character.db.stats.get('powers', {}).get('discipline', {}).get(discipline, {}).get('perm', 0)
                            if disc_value < level:
                                has_prereqs = False
                                missing_prereqs.append(prereq)
                    
                    if not has_prereqs:
                        results['errors'].append(f"Missing prerequisites for {combo_name}: {', '.join(missing_prereqs)}")
                    
                    # Check XP
                    xp_data = character.db.xp if hasattr(character.db, 'xp') else None
                    if not xp_data or not isinstance(xp_data, dict):
                        results['errors'].append(f"No XP data found. Cannot learn combo discipline {combo_name}")
                        continue

                    starting_xp = xp_data.get('total', 0)
                    if not starting_xp:
                        results['errors'].append(f"No XP available. Cannot learn combo discipline {combo_name}")
                        continue

                    combo_cost = self.COMBO_DISCIPLINES[combo_name]['cost']
                    if float(starting_xp) < combo_cost:
                        results['errors'].append(f"Insufficient XP for {combo_name} (costs {combo_cost} XP, have {starting_xp} XP)")

            # Get Path of Enlightenment
            enlightenment = character.db.stats.get('identity', {}).get('personal', {}).get('Path of Enlightenment', {}).get('perm')
            
            # Get required virtues for the Enlightenment path
            required_virtues = self.PATH_VIRTUES.get(enlightenment)
            if not required_virtues:
                results['errors'].append(f"Invalid Enlightenment path: {enlightenment}")
                return
            
            # Check virtues and calculate total
            virtues = character.db.stats.get('virtues', {}).get('moral', {})
            path_data = character.db.stats.get('identity', {}).get('personal', {}).get('Path of Enlightenment', {})
            path_name = path_data.get('perm') if isinstance(path_data, dict) else None
            path_rating = character.db.stats.get('pools', {}).get('moral', {}).get('Path', {}).get('perm', 0)
            virtue_total = 0
            missing_virtues = []
            total_virtue_dots = 0
            freebies_spent_on_virtues = 0

            # Each character gets 7 dots to distribute among virtues at character creation
            remaining_free_dots = 7
            
            for virtue in required_virtues:
                value = virtues.get(virtue, {}).get('perm', 0)
                if value == 0:
                    missing_virtues.append(virtue)
                else:
                    # For non-Humanity paths, Conviction and Instinct start at 0
                    if enlightenment != 'Humanity' and virtue in ['Conviction', 'Instinct']:
                        if value > remaining_free_dots:
                            freebies_spent_on_virtues += (value - remaining_free_dots) * self.FREEBIE_COSTS['virtue']
                            remaining_free_dots = 0
                        else:
                            remaining_free_dots -= value
                    else:  # Humanity virtues or Courage start at 1
                        if (value - 1) > remaining_free_dots:
                            freebies_spent_on_virtues += (value - 1 - remaining_free_dots) * self.FREEBIE_COSTS['virtue']
                            remaining_free_dots = 0
                        else:
                            remaining_free_dots -= (value - 1)
                virtue_total += value

            if missing_virtues:
                results['errors'].append(f"Missing required virtues for {enlightenment}: {', '.join(missing_virtues)}")

            # Check path rating against virtue total and cap for non-Humanity paths
            path = character.db.stats.get('pools', {}).get('moral', {}).get('Path', {}).get('perm', 0)
            if enlightenment != 'Humanity' and path > 5:
                results['errors'].append(f"Non-Humanity paths cannot have path rating above 5 at character creation (currently {path})")
            if path > virtue_total:
                results['errors'].append(f"path rating cannot exceed sum of virtues ({virtue_total}) but is {path}")
            
            # Calculate freebie points spent on path
            freebies_spent_on_path = (path - virtue_total) * self.FREEBIE_COSTS['path'] if path > virtue_total else 0
            
            # Add virtue and path freebie costs to total
            results['freebies_spent'] = results.get('freebies_spent', 0) + freebies_spent_on_virtues + freebies_spent_on_path

            # Check Willpower against Courage
            willpower = character.db.stats.get('pools', {}).get('dual', {}).get('Willpower', {}).get('perm', 0)
            courage = virtues.get('Courage', {}).get('perm', 0)
            if willpower != courage:
                results['errors'].append(f"Willpower should equal Courage rating ({courage}) but is {willpower}")

        elif splat == 'mage':
            # Check required Mage attributes
            required_mage = ['Affiliation', 'Essence']
            for attr in required_mage:
                if not character.db.stats.get('identity', {}).get('lineage', {}).get(attr, {}).get('perm'):
                    results['errors'].append(f"Missing required lineage attribute for Mage: {attr}")

            # Get Mage Faction
            affiliation = character.db.stats.get('identity', {}).get('lineage', {}).get('Affiliation', {}).get('perm')
            if affiliation:
                if affiliation == 'Traditions' and not character.db.stats.get('identity', {}).get('lineage', {}).get('Tradition', {}).get('perm'):
                    results['errors'].append("Traditions Mage must have a Tradition set")
                elif affiliation == 'Technocracy' and not character.db.stats.get('identity', {}).get('lineage', {}).get('Convention', {}).get('perm'):
                    results['errors'].append("Technocratic Mage must have a Convention set")
                elif affiliation == 'Nephandi' and not character.db.stats.get('identity', {}).get('lineage', {}).get('Nephandi Faction', {}).get('perm'):
                    results['errors'].append("Nephandi Mage must have a Nephandi Faction set")

            # Check Sphere requirements
            spheres = character.db.stats.get('powers', {}).get('sphere', {})
            if not spheres:
                results['errors'].append("Mage character has no Spheres")
            # Check Arete
            arete = character.db.stats.get('pools', {}).get('advantage', {}).get('Arete', {}).get('perm', 0)
            if affiliation != 'Technocracy' and arete < 1:
                results['errors'].append("Mage must have Arete of at least 1")
            
            enlightenment = character.db.stats.get('pools', {}).get('advantage', {}).get('Enlightenment', {}).get('perm', 0) or 0
            if affiliation == 'Technocracy' and enlightenment < 1:
                results['errors'].append("Mage with the Technocracy Affiliation must have Enlightenment of at least 1")

            # Check Avatar
            avatar = character.db.stats.get('backgrounds', {}).get('background', {}).get('Avatar', {}).get('perm', 0) or 0
            genius = character.db.stats.get('backgrounds', {}).get('background', {}).get('Genius', {}).get('perm', 0) or 0
            if affiliation != 'Technocracy' and avatar < 1:
                results['errors'].append("It's highly recommended that you have Avatar of at least 1.")
            elif affiliation == 'Technocracy' and genius < 1:
                results['errors'].append("Technocratic Mages should have Genius of at least 1.")
        elif splat == 'changeling':
            # Check for 5 Realms, 3 Arts
            realms = character.db.stats.get('powers', {}).get('realm', {})
            arts = character.db.stats.get('powers', {}).get('art', {})
            realm_dots = sum(values.get('perm', 0) for values in realms.values())
            art_dots = sum(values.get('perm', 0) for values in arts.values())
            if realm_dots < 5:
                results['errors'].append(f"Changeling should have at least 5 realm dots (has {realm_dots})")
            if art_dots < 3:
                results['errors'].append(f"Changeling should have at least 3 art dots (has {art_dots})")

            # Check combo disciplines
            combos = character.db.stats.get('powers', {}).get('combodiscipline', {})
            for combo_name, values in combos.items():
                combo_value = values.get('perm', 0)
                if combo_value > 0:
                    # Check if combo exists in our loaded data
                    if combo_name not in self.COMBO_DISCIPLINES:
                        results['errors'].append(f"Invalid combo discipline: {combo_name}")
                        continue
                    
                    # Check prerequisites
                    has_prereqs = True
                    missing_prereqs = []
                    for prereq in self.COMBO_DISCIPLINES[combo_name]['prerequisites']:
                        # Split on the last space to get the level
                        parts = prereq.rsplit(' ', 1)
                        if len(parts) != 2:
                            has_prereqs = False
                            missing_prereqs.append(prereq)
                            continue
                        
                        discipline, level_str = parts
                        try:
                            level = int(level_str)
                        except ValueError:
                            has_prereqs = False
                            missing_prereqs.append(prereq)
                            continue
                        
                        # Handle special case for Thaumaturgy paths
                        if 'Thaumaturgy' in discipline:
                            thaum_paths = character.db.stats.get('powers', {}).get('thaumaturgy', {})
                            highest_path = max([v.get('perm', 0) for v in thaum_paths.values()], default=0)
                            if highest_path < level:
                                has_prereqs = False
                                missing_prereqs.append(prereq)
                        elif 'Necromancy' in discipline:
                            necro_paths = character.db.stats.get('powers', {}).get('necromancy', {})
                            highest_path = max([v.get('perm', 0) for v in necro_paths.values()], default=0)
                            if highest_path < level:
                                has_prereqs = False
                                missing_prereqs.append(prereq)
                        else:
                            # Remove any parenthetical text from discipline name
                            discipline = discipline.split('(')[0].strip()
                            disc_value = character.db.stats.get('powers', {}).get('discipline', {}).get(discipline, {}).get('perm', 0)
                            if disc_value < level:
                                has_prereqs = False
                                missing_prereqs.append(prereq)
                    
                    if not has_prereqs:
                        results['errors'].append(f"Missing prerequisites for {combo_name}: {', '.join(missing_prereqs)}")
                    
                    # Check XP
                    xp_data = character.db.xp if hasattr(character.db, 'xp') else None
                    if not xp_data or not isinstance(xp_data, dict):
                        results['errors'].append(f"No XP data found. Cannot learn combo discipline {combo_name}")
                        continue

                    starting_xp = xp_data.get('total', 0)
                    if not starting_xp:
                        results['errors'].append(f"No XP available. Cannot learn combo discipline {combo_name}")
                        continue

                    combo_cost = self.COMBO_DISCIPLINES[combo_name]['cost']
                    if float(starting_xp) < combo_cost:
                        results['errors'].append(f"Insufficient XP for {combo_name} (costs {combo_cost} XP, have {starting_xp} XP)")

        elif splat == 'sorcerer':
            # Check for 6 dots of paths
            paths = character.db.stats.get('powers', {}).get('sorcery', {})
            total_dots = sum(values.get('perm', 0) for values in paths.values())
            if total_dots < 6:
                results['errors'].append(f"Sorcerer should have at least 6 path dots (has {total_dots})")

        elif splat == 'psychic':
            # Check for 6 dots of numina
            numina = character.db.stats.get('powers', {}).get('numina', {})
            total_dots = sum(values.get('perm', 0) for values in numina.values())
            if total_dots < 6:
                results['errors'].append(f"Psychic should have at least 6 numina dots (has {total_dots})")

        elif splat == 'faithful':
            # Check for 3 dots of Faith paths
            faith = character.db.stats.get('powers', {}).get('faith', {})
            total_dots = sum(values.get('perm', 0) for values in faith.values())
            if total_dots < 3:
                results['errors'].append(f"Faithful should have at least 3 Faith path dots (has {total_dots})")

        elif splat == 'ghoul':
            # Check for 1 Potence, 1 additional discipline
            disciplines = character.db.stats.get('powers', {}).get('discipline', {})
            potence = disciplines.get('Potence', {}).get('perm', 0)
            total_dots = sum(values.get('perm', 0) for values in disciplines.values())
            if potence < 1:
                results['errors'].append("Ghoul should have at least 1 dot in Potence")
            if total_dots < 2:
                results['errors'].append(f"Ghoul should have 2 discipline dots total (Potence + 1) (has {total_dots})")

        elif splat == 'kinfolk':
            # Check for Gift if they have Gnosis merit
            merits = character.db.stats.get('merits', {}).get('merit', {})
            if 'Gnosis' in merits:
                gifts = character.db.stats.get('powers', {}).get('gift', {})
                if not gifts:
                    results['errors'].append("Kinfolk with Gnosis merit should have 1 Gift")
                else:
                    # TODO: Validate the specific gift based on tribe
                    tribe = character.db.stats.get('identity', {}).get('lineage', {}).get('Tribe', {}).get('perm', '').lower()
                    valid_gifts = {
                        'homid': ["Apecraft's Blessings", "City Running", "Master of Fire", "Persuasion", "Smell of Man"],
                        'black fury': ["Owl's Speech"],
                        'bone gnawer': ["Chain Talk", "Trash Hound"],
                        'children of gaia': ["Water-Conning"],
                        'get of fenris': ["Safe Haven"],
                        'glass walker': ["Control Simple Machine", "Diagnostics", "Well-Oiled Running"],
                        'shadow lord': ["Aura of Confidence", "Whisper Catching"],
                        'silent strider': ["Heaven's Guidance", "Silence"],
                        'silver fang': ["Osprey's Eyes"],
                        'stargazer': ["Balance", "Iron Resolve"],
                        'uktena': ["Sense Magic"],
                        'wendigo': ["Call the Breeze"],
                        # Placeholders for other shifter types
                        'ajaba kinfolk': ["Placeholder"],
                        'ananasi kinfolk': ["Placeholder"],
                        'rokea kinfolk': ["Placeholder"],
                        'kitsune kinfolk': ["Placeholder"],
                        'gurahl kinfolk': ["Placeholder"],
                        'nagah kinfolk': ["Placeholder"],
                        'mokole kinfolk': ["Placeholder"],
                        'ratkin kinfolk': ["Placeholder"]
                    }
                    if tribe in valid_gifts:
                        valid = False
                        for gift in gifts:
                            if gift in valid_gifts[tribe] or gift in valid_gifts['homid']:
                                valid = True
                                break
                        if not valid:
                            results['errors'].append(f"Kinfolk's Gift must be chosen from: {', '.join(valid_gifts[tribe])} or Homid gifts")

        elif splat == 'kinain':
            # Check for 1 Art and 1 Realm
            arts = character.db.stats.get('powers', {}).get('art', {})
            realms = character.db.stats.get('powers', {}).get('realm', {})
            art_dots = sum(values.get('perm', 0) for values in arts.values())
            realm_dots = sum(values.get('perm', 0) for values in realms.values())
            if art_dots < 1:
                results['errors'].append("Kinain should have at least 1 art dot")
            if realm_dots < 1:
                results['errors'].append("Kinain should have at least 1 realm dot")

        elif splat == 'shifter':
            required_lineage = ['Deed Name', 'Type', 'Rank', 'Breed']
            optional_lineage = ['Aspect', 'Auspice', 'Tribe', 'Crown', 'Varna', 'Cabal', 'Kitsune Path', 'Stream', 'Plague']
            
            for attr in required_lineage:
                if not character.db.stats.get('identity', {}).get('lineage', {}).get(attr, {}).get('perm'):
                    results['errors'].append(f"Missing required lineage attribute for Shifter: {attr}")

            # Check if optional attributes exist and are set
            lineage = character.db.stats.get('identity', {}).get('lineage', {})
            for attr in optional_lineage:
                if attr in lineage and not lineage[attr].get('perm'):
                    results['errors'].append(f"Optional lineage attribute {attr} exists but is not set")

            # Get shifter type and check appropriate gifts
            shifter_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '').lower()
            gifts = character.db.stats.get('powers', {}).get('gift', {})
            total_gifts = len(gifts) if gifts else 0

            gift_requirements = {
                'ajaba': {'count': 3, 'msg': "one breed Gift, one aspect Gift, and one Level One general Ajaba Gift"},
                'bastet': {'count': 3, 'msg': "one Level One general Gift, one Level One breed Gift, and one Level One tribe Gift"},
                'corax': {'count': 3, 'msg': "three Gifts from their allowed list"},
                'gurahl': {'count': 3, 'msg': "one breed Gift, one auspice Gift, and one general Gurahl Gift"},
                'kitsune': {'count': 3, 'msg': "one general Kitsune Gift, one breed Gift, and one Path Gift"},
                'mokole': {'count': 2, 'msg': "one aspect Gift and one general Mokolé Gift"},
                'nagah': {'count': 3, 'msg': "one general Nagah Gift, one breed Gift, and one auspice Gift"},
                'nuwisha': {'count': 3, 'msg': "one breed Gift and two general Nuwisha Gifts"},
                'ratkin': {'count': 3, 'msg': "one breed Gift, one aspect Gift, and one general Gift"},
                'rokea': {'count': 2, 'msg': "one general Rokea Gift and one auspice Gift"}
            }

            if shifter_type in gift_requirements:
                req = gift_requirements[shifter_type]
                if total_gifts < req['count']:
                    results['errors'].append(f"{shifter_type.title()} should have {req['msg']} (has {total_gifts})")

        elif splat == 'possessed':
            # Check for Possessed Type
            possessed_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Possessed Type', {}).get('perm')
            if not possessed_type:
                results['errors'].append("Possessed must have a Possessed Type set")

            # Check blessings
            blessings = character.db.stats.get('powers', {}).get('blessing', {})
            blessing_dots = sum(values.get('perm', 0) for values in blessings.values())
            if blessing_dots < 3:
                results['errors'].append(f"Possessed should have at least 3 blessing dots (has {blessing_dots})")

            # Special check for Fomori blessings
            if possessed_type == 'Fomori':
                required_blessings = ['Armored Skin', 'Berserker', 'Gifted Fomor']
                has_required = False
                for blessing in required_blessings:
                    if blessing in blessings:
                        has_required = True
                        break
                if not has_required:
                    results['errors'].append(f"Fomori receive one of the following blessings for free: {', '.join(required_blessings)}")

            # Check background limits
            limited_backgrounds = ['Allies', 'Contacts', 'Resources']
            backgrounds = character.db.stats.get('backgrounds', {}).get('background', {})
            for bg in limited_backgrounds:
                if bg in backgrounds and backgrounds[bg].get('perm', 0) > 3:
                    results['errors'].append(f"Possessed may not have more than 3 dots in {bg} (currently has {backgrounds[bg].get('perm')})")

            # Check Kami Fate requirement
            if possessed_type == 'Kami':
                fate_dots = backgrounds.get('Fate', {}).get('perm', 0)
                if fate_dots < 1:
                    results['errors'].append("Kami must take at least one dot in the Fate background")

        elif splat == 'mortal+':
            # Check for Mortal+ Type
            mortalplus_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Mortal+ Type', {}).get('perm')
            if not mortalplus_type:
                results['errors'].append("Mortal+ must have a Mortal+ Type set")

    def get_secondary_abilities(self, splat):
        """Get the list of secondary abilities based on character splat."""
        secondaries = {
            'talent': {
                'Artistry', 'Carousing', 'Diplomacy', 'Intrigue', 'Mimicry', 'Scrounging', 'Seduction', 'Style'
            },
            'skill': {
                'Archery', 'Fortune-Telling', 'Fencing', 'Gambling', 'Jury-Rigging', 'Pilot', 'Torture'
            },
            'knowledge': {
                'Area Knowledge', 'Cultural Savvy', 'Demolitions', 'Herbalism', 'Media', 'Power-Brokering', 'Vice'
            }
        }

        # Add Mage-specific secondaries if character is a Mage
        if splat.lower() == 'mage':
            secondaries['talent'].update({'High Ritual', 'Blatancy','Lucid Dreaming', 'Flying'})
            secondaries['skill'].update({'Microgravity Ops', 'Energy Weapons', 'Helmsman', 'Biotech', 'Do'})
            secondaries['knowledge'].update({'Hypertech', 'Cybernetics', 'Paraphysics', 'Xenobiology'})

        return secondaries

    def calculate_freebies(self, character, results):
        """Calculate freebie point expenditure."""
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower()
        # Mortal, Mortal+, and Possessed get 21 freebies, others get 15
        base_freebies = 21 if splat in ['mortal', 'mortal+', 'possessed', 'companion'] else 15
        spent_freebies = 0

        # Calculate total flaw points first
        total_flaw_points = 0
        for flaw_type in ['flaw', 'physical', 'social', 'mental', 'supernatural']:
            flaws = character.db.stats.get('flaws', {}).get(flaw_type, {})
            for flaw, values in flaws.items():
                flaw_value = values.get('perm', 0)
                total_flaw_points += flaw_value

        # Total freebies is base amount plus flaw points
        total_freebies = base_freebies + total_flaw_points

        # Calculate attribute freebies
        attribute_totals = []
        for category in ['physical', 'social', 'mental']:
            total = 0
            attributes = character.db.stats.get('attributes', {}).get(category, {})
            for attr, values in attributes.items():
                attr_value = values.get('perm', 1) - 1  # Subtract 1 since all attributes start at 1
                if attr_value > 0:
                    total += attr_value
            attribute_totals.append((category, total))
        
        # Sort to determine primary/secondary/tertiary
        attribute_totals.sort(key=lambda x: x[1], reverse=True)
        
        # Calculate costs for points over caps
        if attribute_totals[0][1] > 7:  # Primary
            spent_freebies += (attribute_totals[0][1] - 7) * self.FREEBIE_COSTS['attribute']
        if attribute_totals[1][1] > 5:  # Secondary
            spent_freebies += (attribute_totals[1][1] - 5) * self.FREEBIE_COSTS['attribute']
        if attribute_totals[2][1] > 3:  # Tertiary
            spent_freebies += (attribute_totals[2][1] - 3) * self.FREEBIE_COSTS['attribute']

        # Calculate ability freebies
        ability_totals = []
        for category in ['talent', 'skill', 'knowledge']:
            total = 0
            # Regular abilities
            abilities = character.db.stats.get('abilities', {}).get(category, {})
            for ability, values in abilities.items():
                ability_value = values.get('perm', 0)
                total += ability_value
            
            # Secondary abilities (count as half points)
            secondary_category = f'secondary_{category}'
            # Fix: Get secondary abilities from the correct path
            secondary_abilities = character.db.stats.get('secondary_abilities', {}).get(secondary_category, {})
            for ability, values in secondary_abilities.items():
                ability_value = values.get('perm', 0)
                total += ability_value * 0.5
            
            ability_totals.append((category, total))
        
        # Sort to determine primary/secondary/tertiary
        ability_totals.sort(key=lambda x: x[1], reverse=True)
        
        # Calculate costs for points over caps
        if ability_totals[0][1] > 13:  # Primary
            spent_freebies += (ability_totals[0][1] - 13) * self.FREEBIE_COSTS['ability']
        if ability_totals[1][1] > 9:  # Secondary
            spent_freebies += (ability_totals[1][1] - 9) * self.FREEBIE_COSTS['ability']
        if ability_totals[2][1] > 5:  # Tertiary
            spent_freebies += (ability_totals[2][1] - 5) * self.FREEBIE_COSTS['ability']

        # Calculate background freebies
        total_backgrounds = 0
        backgrounds = character.db.stats.get('backgrounds', {}).get('background', {})
        for background, values in backgrounds.items():
            background_value = values.get('perm', 0)
            total_backgrounds += background_value
        
        expected_backgrounds = 7 if splat == 'mage' else 5
        if total_backgrounds > expected_backgrounds:
            spent_freebies += (total_backgrounds - expected_backgrounds) * self.FREEBIE_COSTS['background']

        # Calculate merit costs
        for merit_type in ['merit', 'physical', 'social', 'mental', 'supernatural']:
            merits = character.db.stats.get('merits', {}).get(merit_type, {})
            for merit, values in merits.items():
                merit_value = values.get('perm', 0)
                spent_freebies += merit_value * self.FREEBIE_COSTS['merit']
        # Splat-specific calculations
        if splat == 'shifter':
            # Get shifter type to determine free gifts
            shifter_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '').lower()
            gift_requirements = {
                'ajaba': 3,
                'bastet': 3,
                'corax': 3,
                'gurahl': 3,
                'kitsune': 3,
                'mokole': 2,
                'nagah': 3,
                'nuwisha': 3,
                'ratkin': 3,
                'rokea': 2
            }
            free_gifts = gift_requirements.get(shifter_type, 3)  # Default to 3 if type not found
                        # Calculate Gift costs (only for gifts beyond the free ones)
            gifts = character.db.stats.get('powers', {}).get('gift', {})
            total_gifts = len(gifts) if gifts else 0
            if total_gifts > free_gifts:
                spent_freebies += (total_gifts - free_gifts) * self.FREEBIE_COSTS['gift']
            # Calculate Rage and Gnosis costs
            rage = character.db.stats.get('pools', {}).get('dual', {}).get('Rage', {}).get('perm', 0)
            gnosis = character.db.stats.get('pools', {}).get('dual', {}).get('Gnosis', {}).get('perm', 0)
            
            # Get base Rage based on auspice
            auspice_data = character.db.stats.get('identity', {}).get('lineage', {}).get('Auspice', {})
            auspice = auspice_data.get('perm') if isinstance(auspice_data, dict) else None
            base_rage = {
                'Ragabash': 1,
                'Theurge': 2,
                'Philodox': 3,
                'Galliard': 4,
                'Ahroun': 5
            }.get(auspice, 1)  # Default to 1 if auspice not found
            
            # Get base Gnosis based on breed
            breed_data = character.db.stats.get('identity', {}).get('lineage', {}).get('Breed', {})
            breed = breed_data.get('perm') if isinstance(breed_data, dict) else None
            base_gnosis = 1 if breed == 'Homid' else 3 if breed == 'Metis' else 5
            
            if rage > base_rage:
                spent_freebies += (rage - base_rage) * self.FREEBIE_COSTS['rage']
            if gnosis > base_gnosis:
                spent_freebies += (gnosis - base_gnosis) * self.FREEBIE_COSTS['gnosis']


        # Vampire-specific calculations
        elif splat == 'vampire':
            # Calculate discipline costs
            disciplines = character.db.stats.get('powers', {}).get('discipline', {})
            total_discipline_dots = sum(values.get('perm', 0) for values in disciplines.values())
            if total_discipline_dots > 3:  # Free dots
                spent_freebies += (total_discipline_dots - 3) * self.FREEBIE_COSTS['discipline']

            # Calculate virtue and path costs
            virtues = character.db.stats.get('virtues', {}).get('moral', {})
            path_data = character.db.stats.get('identity', {}).get('personal', {}).get('Path of Enlightenment', {})
            path_name = path_data.get('perm') if isinstance(path_data, dict) else None
            path_rating = character.db.stats.get('pools', {}).get('moral', {}).get('Path', {}).get('perm', 0)
            
            if path_name:
                required_virtues = self.PATH_VIRTUES.get(path_name, [])
                remaining_free_dots = 7
                
                for virtue in required_virtues:
                    value = virtues.get(virtue, {}).get('perm', 0)
                    if value > 0:
                        # For non-Humanity paths, Conviction and Instinct start at 0
                        if path_name != 'Humanity' and virtue in ['Conviction', 'Instinct']:
                            if value > remaining_free_dots:
                                spent_freebies += (value - remaining_free_dots) * self.FREEBIE_COSTS['virtue']
                                remaining_free_dots = 0
                            else:
                                remaining_free_dots -= value
                        else:  # Humanity virtues or Courage start at 1
                            if (value - 1) > remaining_free_dots:
                                spent_freebies += (value - 1 - remaining_free_dots) * self.FREEBIE_COSTS['virtue']
                                remaining_free_dots = 0
                            else:
                                remaining_free_dots -= (value - 1)
                # Calculate path costs
                path = character.db.stats.get('pools', {}).get('moral', {}).get('Path', {}).get('perm', 0)
                virtue_total = sum(values.get('perm', 0) for values in virtues.values())
                if path > virtue_total:
                    spent_freebies += (path - virtue_total) * self.FREEBIE_COSTS['path']

        elif splat == 'changeling':
            # Calculate Art costs
            arts = character.db.stats.get('powers', {}).get('art', {})
            art_dots = sum(values.get('perm', 0) for values in arts.values())
            if art_dots > 3:  # Free dots
                spent_freebies += (art_dots - 3) * self.FREEBIE_COSTS['art']

            # Calculate Realm costs
            realms = character.db.stats.get('powers', {}).get('realm', {})
            realm_dots = sum(values.get('perm', 0) for values in realms.values())
            if realm_dots > 5:  # Free dots
                spent_freebies += (realm_dots - 5) * self.FREEBIE_COSTS['realm']

            # Calculate Glamour costs
            glamour = character.db.stats.get('pools', {}).get('dual', {}).get('Glamour', {}).get('perm', 0)
            seeming_data = character.db.stats.get('identity', {}).get('lineage', {}).get('Seeming', {})
            seeming = seeming_data.get('perm') if isinstance(seeming_data, dict) else None
            base_glamour = 5 if seeming == 'Childling' else 4
            if glamour > base_glamour:
                spent_freebies += (glamour - base_glamour) * self.FREEBIE_COSTS['glamour']

        elif splat == 'mage':
            # Calculate Sphere costs
            spheres = character.db.stats.get('powers', {}).get('sphere', {})
            sphere_dots = sum(values.get('perm', 0) for values in spheres.values())
            if sphere_dots > 6:  # 5 free dots + 1 affinity
                spent_freebies += (sphere_dots - 6) * self.FREEBIE_COSTS['sphere']

            # Calculate Arete costs
            arete = character.db.stats.get('pools', {}).get('advantage', {}).get('Arete', {}).get('perm', 0)
            if arete > 1:
                spent_freebies += (arete - 1) * self.FREEBIE_COSTS['arete']

            # Calculate Enlightenment costs for Technocracy
            affiliation_data = character.db.stats.get('identity', {}).get('lineage', {}).get('Affiliation', {})
            affiliation = affiliation_data.get('perm') if isinstance(affiliation_data, dict) else None
            if affiliation == 'Technocracy':
                enlightenment = character.db.stats.get('pools', {}).get('advantage', {}).get('Enlightenment', {}).get('perm', 0)
                if enlightenment > 1:
                    spent_freebies += (enlightenment - 1) * self.FREEBIE_COSTS['enlightenment']

            # Calculate Quintessence costs
            quintessence = character.db.stats.get('pools', {}).get('dual', {}).get('Quintessence', {}).get('perm', 0)
            avatar = character.db.stats.get('backgrounds', {}).get('background', {}).get('Avatar', {}).get('perm', 0)
            if quintessence > avatar:
                # Each point of quintessence over Avatar costs 0.25 freebies
                # For every 4 points of quintessence over Avatar, that's 1 freebie point
                extra_points = quintessence - avatar
                spent_freebies += (extra_points * self.FREEBIE_COSTS['quintessence'])

        results['freebies_spent'] = int(spent_freebies)
        results['total_freebies'] = total_freebies
        # Store results
        results['freebies_spent'] = spent_freebies
        results['total_freebies'] = total_freebies
        
        # Update error messages
        if spent_freebies > total_freebies:
            results['errors'].append(f"Too many freebie points spent: {spent_freebies}/{total_freebies}")
        elif spent_freebies < total_freebies:
            results['errors'].append(f"Not all freebie points spent: {spent_freebies}/{total_freebies}")
            
        # Store flaw points for display
        results['total_flaw_points'] = total_flaw_points
        results['base_freebies'] = base_freebies

    def check_combo_prerequisites(self, character, combo_name):
        """Check if character meets prerequisites for a combo discipline."""
        if combo_name not in self.COMBO_DISCIPLINES:
            return False
        for prereq in self.COMBO_DISCIPLINES[combo_name]['prerequisites']:
            discipline, level = prereq.split()
            if character.get_stat('powers', 'discipline', discipline, temp=False) < int(level):
                return False
        return True

    
    def common_identity_attributes(self, character, results):
        # Check common identity attributes for all splats
        required_personal = {
            'Full Name': 'identity/personal',
            'Date of Birth': 'identity/personal',
            'Concept': 'identity/personal'
        }

        # Check Nature/Demeanor for all splats except Changeling
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower()
        if splat != 'changeling':
            required_archetype = {
                'Nature': 'identity/personal',
                'Demeanor': 'identity/personal'
            }
            
            for attr, path_of_enlightenment in required_archetype.items():
                if not character.db.stats.get('identity', {}).get('personal', {}).get(attr, {}).get('perm'):
                    results['errors'].append(f"Missing required identity attribute: {attr}")

        for attr, path_of_enlightenment in required_personal.items():
            if not character.db.stats.get('identity', {}).get('personal', {}).get(attr, {}).get('perm'):
                results['errors'].append(f"Missing required identity attribute: {attr}")

        # Get character's splat
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower()

        # Splat-specific checks
        if splat == 'changeling':
            # Check required Changeling attributes
            required_changeling = ['Kith', 'Seeming']
            required_legacy = ['Seelie Legacy', 'Unseelie Legacy']
            
            for attr in required_changeling:
                if not character.db.stats.get('identity', {}).get('lineage', {}).get(attr, {}).get('perm'):
                    results['errors'].append(f"Missing required lineage attribute for Changeling: {attr}")

            for attr in required_legacy:
                if not character.db.stats.get('identity', {}).get('lineage', {}).get(attr, {}).get('perm'):
                    results['errors'].append(f"Missing required legacy attribute for Changeling: {attr}")

            # Check Seeming-specific requirements
            seeming = character.db.stats.get('identity', {}).get('lineage', {}).get('Seeming', {}).get('perm')
            if seeming:
                willpower = character.get_stat('pools', 'dual', 'Willpower', temp=False)
                glamour = character.get_stat('pools', 'dual', 'Glamour', temp=False)
                
                if seeming == 'Grump' and willpower < 5:
                    results['errors'].append("Grump Changelings must have Willpower >= 4")
                elif seeming == 'Childling' and glamour < 4:
                    results['errors'].append("Childling Changelings must have Glamour >= 5")

            # Check Banality requirement
            banality = character.get_stat('pools', 'dual', 'Banality', temp=False) or 0
            if banality < 3:
                results['errors'].append(f"All Changelings must have Banality >= 3 (currently {banality})")
        elif splat == 'vampire':
            # Check required Vampire attributes
            required_vampire_lineage = ['Clan', 'Generation', 'Sire', 'Path of Enlightenment']  # Added Enlightenment
            required_vampire_identity = ['Date of Embrace']
            
            for attr in required_vampire_lineage:
                if not character.db.stats.get('identity', {}).get('lineage', {}).get(attr, {}).get('perm'):
                    results['errors'].append(f"Missing required lineage attribute for Vampire: {attr}")

            for attr in required_vampire_identity:
                if not character.db.stats.get('identity', {}).get('personal', {}).get(attr, {}).get('perm'):
                    results['errors'].append(f"Missing required identity attribute for Vampire: {attr}")
            
            # Check path rating, if not humanity it should be 5 or less; path is calculated by the virtues
            path_of_enlightenment = character.get_stat('identity', 'personal', 'Path of Enlightenment', temp=False) or 0
            if path_of_enlightenment != 'Humanity' and character.get_stat('virtues', 'moral', 'path', temp=False) > 5:
                results['errors'].append(f"Path of Enlightenment rating must be 5 or less for non-Humanity paths.")

        elif splat == 'companion':
            # Check required Companion attributes
            required_companion = ['Companion Type', 'Affiliation', 'Motivation']
            for attr in required_companion:
                if not character.db.stats.get('identity', {}).get('lineage', {}).get(attr, {}).get('perm'):
                    results['errors'].append(f"Missing required lineage attribute for Companion: {attr}")

            # Verify companion type and appropriate flaw
            if not character.get_stat('flaws', 'supernatural', 'Thaumivore') or not character.get_stat('flaws', 'supernatural', 'Power Source'):
                    results['errors'].append(f"Companions must have Thaumivore flaw or Power Source flaw.")

    def display_results(self, character, results):
        """Display the results of the character check."""
        string = f"|wCharacter Check Results for {character.name}|n\n\n"

        # Attributes
        string += "|yAttributes:|n\n"
        string += f"Primary: {results['attributes']['primary']}/7\n"
        string += f"Secondary: {results['attributes']['secondary']}/5\n"
        string += f"Tertiary: {results['attributes']['tertiary']}/3\n\n"

        # Calculate total points in each ability category including secondary abilities
        talent_total = sum(values.get('perm', 0) for values in character.db.stats.get('abilities', {}).get('talent', {}).values())
        skill_total = sum(values.get('perm', 0) for values in character.db.stats.get('abilities', {}).get('skill', {}).values())
        knowledge_total = sum(values.get('perm', 0) for values in character.db.stats.get('abilities', {}).get('knowledge', {}).values())

        # Calculate secondary ability totals
        # Fix: Access secondary abilities from the correct path
        sec_talent_total = sum(values.get('perm', 0) * 0.5 for values in character.db.stats.get('secondary_abilities', {}).get('secondary_talent', {}).values())
        sec_skill_total = sum(values.get('perm', 0) * 0.5 for values in character.db.stats.get('secondary_abilities', {}).get('secondary_skill', {}).values())
        sec_knowledge_total = sum(values.get('perm', 0) * 0.5 for values in character.db.stats.get('secondary_abilities', {}).get('secondary_knowledge', {}).values())

        # Combined totals
        total_talent = talent_total + sec_talent_total
        total_skill = skill_total + sec_skill_total
        total_knowledge = knowledge_total + sec_knowledge_total

        # Abilities with combined totals
        string += "|yAbilities:|n\n"
        
        # Primary abilities
        primary_cat = results['abilities']['primary']['category']
        primary_total = total_talent if primary_cat == 'talent' else total_skill if primary_cat == 'skill' else total_knowledge if primary_cat == 'knowledge' else 0
        string += f"Primary: {results['abilities']['primary']['points']}/13 ({primary_cat})"
        if primary_cat in ['talent', 'skill', 'knowledge']:
            string += f" - Total with secondaries: {primary_total:.1f}"
        string += "\n"
        
        # Secondary abilities
        secondary_cat = results['abilities']['secondary']['category']
        secondary_total = total_talent if secondary_cat == 'talent' else total_skill if secondary_cat == 'skill' else total_knowledge if secondary_cat == 'knowledge' else 0
        string += f"Secondary: {results['abilities']['secondary']['points']}/9 ({secondary_cat})"
        if secondary_cat in ['talent', 'skill', 'knowledge']:
            string += f" - Total with secondaries: {secondary_total:.1f}"
        string += "\n"
        
        # Tertiary abilities
        tertiary_cat = results['abilities']['tertiary']['category']
        tertiary_total = total_talent if tertiary_cat == 'talent' else total_skill if tertiary_cat == 'skill' else total_knowledge if tertiary_cat == 'knowledge' else 0
        string += f"Tertiary: {results['abilities']['tertiary']['points']}/5 ({tertiary_cat})"
        if tertiary_cat in ['talent', 'skill', 'knowledge']:
            string += f" - Total with secondaries: {tertiary_total:.1f}"
        string += "\n\n"

        # Secondary Abilities with totals
        string += "|ySecondary Abilities:|n\n"
        
        # Talents
        if results['secondary_abilities']['secondary_talent']:
            string += f"\n|cTalents (Total: {sec_talent_total:.1f} points):|n\n"
            for talent, value in sorted(results['secondary_abilities']['secondary_talent'].items()):
                string += f"{talent}: {value} ({value * 0.5:.1f} points)\n"
        
        # Skills
        if results['secondary_abilities']['secondary_skill']:
            string += f"\n|cSkills (Total: {sec_skill_total:.1f} points):|n\n"
            for skill, value in sorted(results['secondary_abilities']['secondary_skill'].items()):
                string += f"{skill}: {value} ({value * 0.5:.1f} points)\n"
        
        # Knowledges
        if results['secondary_abilities']['secondary_knowledge']:
            string += f"\n|cKnowledges (Total: {sec_knowledge_total:.1f} points):|n\n"
            for knowledge, value in sorted(results['secondary_abilities']['secondary_knowledge'].items()):
                string += f"{knowledge}: {value} ({value * 0.5:.1f} points)\n"
        
        string += "\n"

        # Backgrounds
        string += f"|yBackgrounds:|n {results['backgrounds']}/5\n\n"

        # Merits & Flaws
        string += "|yMerits & Flaws:|n\n"
        string += f"Merit dots: {results['merits']}\n"
        string += f"Flaw dots: {results['flaws']}/7\n\n"

        # Power Traits
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower()

        # Arete for Mages
        if splat == 'mage':
            string += f"|yArete:|n {results['arete']}\n\n"
            # Spheres
            string += "|ySpheres:|n\n"
            spheres = character.db.stats.get('powers', {}).get('sphere', {})
            sphere_dots = sum(values.get('perm', 0) for values in spheres.values())
            string += f"Sphere dots: {sphere_dots} (Free: 6, Extra: {sphere_dots - 6})\n"
            for sphere, values in sorted(spheres.items()):
                dots = values.get('perm', 0)
                if dots > 0:
                    string += f"- {sphere}: {dots}\n"
            string += "\n"

        # Gnosis and Rage for Shifters
        if splat == 'shifter':
            string += f"|yGnosis:|n {results['gnosis']}\n"
            string += f"|yRage:|n {results['rage']}\n"
            # Gifts
            string += "|yGifts:|n\n"
            gifts = character.db.stats.get('powers', {}).get('gift', {})
            gift_dots = len(gifts) if gifts else 0
            string += f"Gift count: {gift_dots}\n"
            for gift in sorted(gifts.keys()):
                string += f"- {gift}\n"
            string += "\n"

        # Glamour for Changelings
        if splat == 'changeling':
            string += f"|yGlamour:|n {results['glamour']}\n\n"
            # Arts & Realms are already handled in the existing code
            string += "|yArts & Realms:|n\n"
            arts = character.db.stats.get('powers', {}).get('art', {})
            realms = character.db.stats.get('powers', {}).get('realm', {})
            art_dots = sum(values.get('perm', 0) for values in arts.values())
            realm_dots = sum(values.get('perm', 0) for values in realms.values())
            string += f"Art dots: {art_dots} (Free: 3, Extra: {art_dots - 3})\n"
            string += f"Realm dots: {realm_dots} (Free: 5, Extra: {realm_dots - 5})\n"
            
            # List current arts
            string += "Current arts:\n"
            for art, values in sorted(arts.items()):
                dots = values.get('perm', 0)
                if dots > 0:
                    string += f"- {art}: {dots}\n"
            string += "\n"

        # Disciplines for Vampires
        if splat == 'vampire':
            string += "|yDisciplines, Thaumaturgy, Necromancy:|n\n"
            disciplines = character.db.stats.get('powers', {}).get('discipline', {})
            thaumaturgy = character.db.stats.get('powers', {}).get('thaumaturgy', {})
            necromancy = character.db.stats.get('powers', {}).get('necromancy', {})
            
            # Calculate total dots
            discipline_dots = sum(values.get('perm', 0) for values in disciplines.values())
            
            # Display regular disciplines first
            for discipline, values in sorted(disciplines.items()):
                dots = values.get('perm', 0)
                if dots > 0:
                    string += f"- {discipline}: {dots}\n"
            
            # Handle Thaumaturgy paths
            if thaumaturgy:
                string += "\nThaumaturgy Paths:\n"
                primary_path = None
                primary_dots = 0
                for path, values in sorted(thaumaturgy.items()):
                    dots = values.get('perm', 0)
                    if dots > primary_dots:
                        primary_path = path
                        primary_dots = dots
                
                # Show primary path first
                if primary_path:
                    string += f"- {primary_path} (Primary): {primary_dots}\n"
                    # Then show other paths
                    for path, values in sorted(thaumaturgy.items()):
                        dots = values.get('perm', 0)
                        if path != primary_path and dots > 0:
                            string += f"- {path}: {dots}\n"
            
            # Handle Necromancy paths
            if necromancy:
                string += "\nNecromancy Paths:\n"
                primary_path = None
                primary_dots = 0
                for path, values in sorted(necromancy.items()):
                    dots = values.get('perm', 0)
                    if dots > primary_dots:
                        primary_path = path
                        primary_dots = dots
                
                # Show primary path first
                if primary_path:
                    string += f"- {primary_path} (Primary): {primary_dots}\n"
                    # Then show other paths
                    for path, values in sorted(necromancy.items()):
                        dots = values.get('perm', 0)
                        if path != primary_path and dots > 0:
                            string += f"- {path}: {dots}\n"
            
            # Calculate and display total dots
            total_thaum_dots = sum(values.get('perm', 0) for values in thaumaturgy.values()) if thaumaturgy else 0
            total_necro_dots = sum(values.get('perm', 0) for values in necromancy.values()) if necromancy else 0
            total_dots = discipline_dots + total_thaum_dots + total_necro_dots
            
            string += f"\nTotal Discipline dots: {total_dots} (Free: 3, Extra: {total_dots - 3})\n"
            if total_thaum_dots:
                string += f"Total Thaumaturgy dots: {total_thaum_dots}\n"
            if total_necro_dots:
                string += f"Total Necromancy dots: {total_necro_dots}\n"
            string += "\n"

        # Willpower for all splats that use it
        if splat in ['changeling', 'mortal+', 'possessed', 'companion', 'vampire', 'mage', 'shifter', 'mortal']:
            string += f"|yWillpower:|n {results['willpower']}\n\n"

        # Freebie Points
        # Determine base freebies based on splat
        base_freebies = 21 if splat.lower() in ['mortal', 'mortal+', 'possessed', 'companion'] else 15
        
        # Calculate total flaw points
        total_flaw_points = 0
        for flaw_type in ['flaw', 'physical', 'social', 'mental', 'supernatural']:
            flaws = character.db.stats.get('flaws', {}).get(flaw_type, {})
            total_flaw_points += sum(values.get('perm', 0) for values in flaws.values())
        
        # Calculate total available freebies (base + flaws)
        total_freebies = base_freebies + total_flaw_points
        
        # Get spent freebies from results
        spent_freebies = results.get('freebies_spent', 0)
        
        string += f"|yFreebie Points:|n {spent_freebies}/{total_freebies}\n"
        if total_flaw_points > 0:
            string += f"(Base: {base_freebies} + Flaws: {total_flaw_points})\n\n"
        else:
            string += "\n"

        # Errors
        if results['errors']:
            string += "|rWarnings:|n\n"
            for error in results['errors']:
                string += f"- {error}\n"
        else:
            string += "|gNo errors found. Character creation points are properly allocated.|n\n"

        return string
"""
    def calculate_xp(self, character, results):
        # Calculate XP expenditure if character has starting XP.
        # Get XP from the character's xp attribute
        xp_data = character.db.xp if hasattr(character.db, 'xp') else None
        if not xp_data or not isinstance(xp_data, dict):
            results['errors'].append("No XP data found. Character must have XP data to learn combo disciplines.")
            return

        starting_xp = xp_data.get('total', 0)
        if not starting_xp:
            results['errors'].append("No starting XP found. Character must have XP to learn combo disciplines.")
            return

        spent_xp = 0
        xp_breakdown = {}
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')

        # Check combo disciplines first
        combo_xp = 0
        combos = character.db.stats.get('powers', {}).get('combodiscipline', {})
        for combo_name, values in combos.items():
            combo_value = values.get('perm', 0)
            if combo_value > 0:
                # Check if combo exists in our loaded data
                if combo_name not in self.COMBO_DISCIPLINES:
                    results['errors'].append(f"Invalid combo discipline: {combo_name}")
                    continue
                
                # Check prerequisites
                has_prereqs = True
                missing_prereqs = []
                for prereq in self.COMBO_DISCIPLINES[combo_name]['prerequisites']:
                    # Split on the last space to get the level
                    parts = prereq.rsplit(' ', 1)
                    if len(parts) != 2:
                        has_prereqs = False
                        missing_prereqs.append(prereq)
                        continue
                        
                    discipline, level_str = parts
                    try:
                        level = int(level_str)
                    except ValueError:
                        has_prereqs = False
                        missing_prereqs.append(prereq)
                        continue
                    
                    # Handle special case for Thaumaturgy paths
                    if 'Thaumaturgy' in discipline:
                        thaum_paths = character.db.stats.get('powers', {}).get('thaumaturgy', {})
                        highest_path = max([v.get('perm', 0) for v in thaum_paths.values()], default=0)
                        if highest_path < level:
                            has_prereqs = False
                            missing_prereqs.append(prereq)
                    elif 'Necromancy' in discipline:
                        necro_paths = character.db.stats.get('powers', {}).get('necromancy', {})
                        highest_path = max([v.get('perm', 0) for v in necro_paths.values()], default=0)
                        if highest_path < level:
                            has_prereqs = False
                            missing_prereqs.append(prereq)
                    else:
                        # Remove any parenthetical text from discipline name
                        discipline = discipline.split('(')[0].strip()
                        disc_value = character.get_stat('powers', 'discipline', discipline, temp=False) or 0
                        if disc_value < level:
                            has_prereqs = False
                            missing_prereqs.append(prereq)
                
                if not has_prereqs:
                    results['errors'].append(f"Missing prerequisites for {combo_name}: {', '.join(missing_prereqs)}")
                
                # Add XP cost
                combo_cost = self.COMBO_DISCIPLINES[combo_name]['cost']
                combo_xp += combo_cost
                
        if combo_xp > 0:
            xp_breakdown['Combo Disciplines'] = combo_xp
            spent_xp += combo_xp

        # Get secondary abilities for this character's splat
        secondary_abilities = self.get_secondary_abilities(splat)

        # Calculate attribute XP
        attr_xp = 0
        for category in ['physical', 'social', 'mental']:
            attributes = character.db.stats.get('attributes', {}).get(category, {})
            for attr, values in attributes.items():
                attr_value = values.get('perm', 0)
                if attr_value > 5:  # Assuming max of 5 from freebies
                    attr_xp += (attr_value - 5) * self.XP_COSTS['attribute']
        if attr_xp > 0:
            xp_breakdown['Attributes'] = attr_xp
            spent_xp += attr_xp

        # Calculate ability XP
        ability_xp = 0
        for category in ['talent', 'skill', 'knowledge']:
            abilities = character.db.stats.get('abilities', {}).get(category, {})
            for ability, values in abilities.items():
                ability_value = values.get('perm', 0)
                if ability_value > 3:  # Assuming max of 3 from freebies
                    # Check if this is a secondary ability
                    if ability.lower() in {ab.lower() for ab in secondary_abilities.get(category, set())}:
                        ability_xp += (ability_value - 3) * (self.XP_COSTS['ability'] / 2)
                    else:
                        ability_xp += (ability_value - 3) * self.XP_COSTS['ability']
        if ability_xp > 0:
            xp_breakdown['Abilities'] = ability_xp
            spent_xp += ability_xp

        # Calculate background XP
        background_xp = 0
        backgrounds = character.db.stats.get('backgrounds', {}).get('background', {})
        for background, values in backgrounds.items():
            background_value = values.get('perm', 0)
            if background_value > 5:  # Assuming max of 5 from freebies
                background_xp += (background_value - 5) * self.XP_COSTS['background']
        if background_xp > 0:
            xp_breakdown['Backgrounds'] = background_xp
            spent_xp += background_xp

        # Calculate merit XP
        merit_xp = 0
        for merit_type in ['merit', 'physical', 'social', 'mental', 'supernatural']:
            merits = character.db.stats.get('merits', {}).get(merit_type, {})
            for merit, values in merits.items():
                merit_value = values.get('perm', 0)
                if merit_value > 0:
                    merit_xp += merit_value * self.XP_COSTS['merit']
        if merit_xp > 0:
            xp_breakdown['Merits'] = merit_xp
            spent_xp += merit_xp

        # Calculate flaw XP
        flaw_xp = 0
        for flaw_type in ['flaw', 'physical', 'social', 'mental', 'supernatural']:
            flaws = character.db.stats.get('flaws', {}).get(flaw_type, {})
            for flaw, values in flaws.items():
                flaw_value = values.get('perm', 0)
                if flaw_value > 0:
                    flaw_xp += flaw_value * self.XP_COSTS['flaw']
        if flaw_xp > 0:
            xp_breakdown['Flaws'] = flaw_xp
            spent_xp += flaw_xp

        results['xp_spent'] = spent_xp
        results['total_xp'] = float(starting_xp)  # Convert Decimal to float
        results['xp_breakdown'] = xp_breakdown
        
        if spent_xp > float(starting_xp):
            results['errors'].append(f"Too much XP spent ({spent_xp} XP spent vs {float(starting_xp)} XP available)")
        elif spent_xp < float(starting_xp):
            results['errors'].append(f"Not all XP spent ({spent_xp} XP spent vs {float(starting_xp)} XP available)")


    def check_required_notes(self, character, results):
        #Check for required notes based on character type.#
        # Get character's splat and type
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        char_type = character.get_stat('identity', 'lineage', 'Type', temp=False)

        # Check for backstory
        if not self.has_note(character, 'Backstory', ['Character Backstory', 'Background']):
            results['errors'].append("Missing required 'Backstory' note")

        # Check for XP and Freebie spends
        if not self.has_note(character, 'XP Spends', ['Experience Spends', 'XP_Spends']):
            results['errors'].append("Missing required 'XP Spends' note")
        if not self.has_note(character, 'Freebie Spends', ['Freebies', 'Freebie_Spends']):
            results['errors'].append("Missing required 'Freebie Spends' note")

            # Check required Changeling notes with similar names
            required_changeling_notes = {
                'Frailties': ['Frailty', 'Character Frailties', 'Character Frailty'],
                'Birthrights': ['Birthright', 'Character Birthrights', 'Character Birthright'],
                'Musing Threshold': ['Musing', 'Musings', 'Musing_Threshold'],
                'Ravaging Threshold': ['Ravaging', 'Ravage Threshold', 'Ravage'],
                'Antithesis': ['Character Antithesis']
            }
            
            # Check if any of the similar names exist for each required note
            for note, similar in required_changeling_notes.items():
                if not self.has_note(character, note, similar):
                    results['errors'].append(f"Changeling character missing required '{note}' note")

            # Check if Thresholds note contains both Musing and Ravaging information
            if self.has_note(character, 'Thresholds'):
                # Remove the Musing and Ravaging Threshold requirements since they're in the combined note
                results['errors'] = [err for err in results['errors'] 
                                   if not ('Musing Threshold' in err or 'Ravaging Threshold' in err)]


            # Check merit/flaw explanation notes
            merit_categories = ['merit', 'physical', 'social', 'mental', 'supernatural']
            flaw_categories = ['flaw', 'physical', 'social', 'mental', 'supernatural']
            
            merits = character.db.stats.get('merits', {})
            flaws = character.db.stats.get('flaws', {})
            notes = character.db.notes or {}
            
            # Check merit notes
            for category in merit_categories:
                category_merits = merits.get(category, {})
                for merit in category_merits:
                    if merit not in notes:
                        results['errors'].append(f"Missing explanation note for merit: {merit}")
            
            # Check flaw notes
            for category in flaw_categories:
                category_flaws = flaws.get(category, {})
                for flaw in category_flaws:
                    if flaw not in notes:
                        results['errors'].append(f"Missing explanation note for flaw: {flaw}")

            # Check required notes
            required_companion_notes = ['Origin', 'Description']
            for note_name in required_companion_notes:
                if note_name not in notes:
                    results['errors'].append(f"Companion character missing required '{note_name}' note")
    def has_note(self, character, required_note, similar_names=None):
        
        Check if a character has a specific note or any similar notes.
        
        Args:
            character: The character to check
            required_note (str): The name of the required note
            similar_names (list): Optional list of similar note names to check
            
        Returns:
            bool: True if the note or a similar note exists, False otherwise
        
        # Get notes from character, ensuring it's a dictionary
        notes = character.db.notes if character.db.notes else {}
        if not isinstance(notes, dict):
            notes = {}
        
        # Create set of note names in lowercase
        note_names = {name.lower() for name in notes.keys()}
        
        # Check for exact match first
        if required_note.lower() in note_names:
            return True
        
        # Check similar names if provided
        if similar_names:
            for similar_name in similar_names:
                if similar_name.lower() in note_names:
                    return True
                
        return 
""" 