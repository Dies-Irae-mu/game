from world.wod20th.models import POWER_SOURCE_TYPES
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

    # Define Combo Disciplines and their prerequisites
    COMBO_DISCIPLINES = {
        'See the Reflected Form': {
            'cost': 15,
            'prerequisites': ['Auspex 2', 'Protean 2']
        },
        'Eyes of the Beast': {
            'cost': 12,
            'prerequisites': ['Animalism 2', 'Protean 1']
        },
        'Flesh of the Corpse': {
            'cost': 14,
            'prerequisites': ['Fortitude 2', 'Protean 3']
        },
        'Scalpel Tongue': {
            'cost': 15,
            'prerequisites': ['Auspex 2', 'Celerity 2', 'Presence 2']
        },
        'Approximation of Loyalty Absolute': {
            'cost': 21,
            'prerequisites': ['Dominate 4', 'Presence 4']
        },
        'Chain the Psyche': {
            'cost': 18,
            'prerequisites': ['Dominate 3', 'Presence 2']
        },
        'Enhance the Wild Ride': {
            'cost': 15,
            'prerequisites': ['Celerity 2', 'Potence 2']
        },
        'Forced March': {
            'cost': 12,
            'prerequisites': ['Fortitude 2', 'Potence 2']
        }
    }

    FREEBIE_COSTS = {
        'attribute': 5,
        'ability': 2,
        'background': 1,
        'willpower': 1,
        'virtue': 2,
        'merit': 1,
        'flaw': -1,  # Flaws add points
        # Splat-specific costs
        'gift': 7,
        'rage': 1,
        'gnosis': 2,
        'sphere': 7,
        'arete': 4,
        'quintessence': 0.25,  # 1 per 4 dots
        'discipline': 7,
        'road': 2,
        'art': 5,
        'glamour': 3,
        'realm': 2
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
        'road': 2,
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
        'talent': {
            'Carousing', 'Diplomacy', 'Intrigue', 'Mimicry', 'Scrounging', 'Seduction', 'Style',
            # Mage-specific secondaries will be added dynamically
            'High Ritual', 'Blatancy'
        },
        'skill': {
            'Archery', 'Fortune-Telling', 'Fencing', 'Gambling', 'Jury-Rigging', 'Pilot', 'Torture',
            # Mage-specific secondaries will be added dynamically
            'Microgravity Ops', 'Energy Weapons', 'Helmsman', 'Biotech'
        },
        'knowledge': {
            'Area Knowledge', 'Cultural Savvy', 'Demolitions', 'Herbalism', 'Media', 'Power-Brokering', 'Vice',
            # Mage-specific secondaries will be added dynamically
            'Hypertech', 'Cybernetics', 'Paraphysics', 'Xenobiology'
        }
    }

    def func(self):
        """Execute the command."""
        if not self.args:
            character = self.caller
        else:
            # Only allow staff to check other characters
            if not self.caller.check_permstring("Builder") and not self.caller.check_permstring("Admin") and not self.caller.check_permstring("Developer"):
                self.caller.msg("You don't have permission to check other characters.")
                return
                
            character = self.caller.search(self.args)
            if not character:
                return

        # Get character's splat
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        if not splat:
            self.caller.msg("|rError: Character has no splat type set.|n")
            return

        # Initialize results dictionary
        results = {
            'attributes': {'primary': 0, 'secondary': 0, 'tertiary': 0},
            'abilities': {'primary': 0, 'secondary': 0, 'tertiary': 0},
            'backgrounds': 0,
            'freebies_spent': 0,
            'xp_spent': 0,
            'errors': []
        }

        # Check attributes
        self.check_attributes(character, results)
        
        # Check abilities
        self.check_abilities(character, results)
        
        # Check backgrounds
        self.check_backgrounds(character, results)
        
        # Check required notes
        self.check_required_notes(character, results)
        
        # Check free dots
        self.check_free_dots(character, results)
        
        # Calculate freebie points
        self.calculate_freebies(character, results)

        # Calculate XP if any exists
        self.calculate_xp(character, results)

        # Display results
        self.display_results(character, results)

    def check_attributes(self, character, results):
        """Check attribute point allocation."""
        attribute_categories = ['physical', 'social', 'mental']
        attribute_totals = []

        for category in attribute_categories:
            total = 0
            attributes = character.db.stats.get('attributes', {}).get(category, {})
            for attr, values in attributes.items():
                # Subtract 1 from each attribute value since all attributes start at 1
                attr_value = values.get('perm', 0) - 1
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

        for category in ['talent', 'skill', 'knowledge']:
            category_total = 0
            
            # Check regular abilities
            abilities = character.db.stats.get('abilities', {}).get(category, {})
            for ability, values in abilities.items():
                ability_value = min(values.get('perm', 0), 3)  # Cap at 3 for initial point allocation
                if ability_value > 0:
                    # If it's a secondary ability, count it as half points
                    if ability in secondary_abilities.get(category, set()):
                        category_total += ability_value * 0.5
                    else:
                        category_total += ability_value

            # Check secondary abilities
            secondary_category = f'secondary_{category}'
            secondary_abilities_dict = character.db.stats.get('secondary_abilities', {}).get(secondary_category, {})
            for ability, values in secondary_abilities_dict.items():
                ability_value = min(values.get('perm', 0), 3)  # Cap at 3 for initial point allocation
                if ability_value > 0:
                    category_total += ability_value * 0.5  # All abilities in secondary_abilities are secondary abilities

            if category_total > 0:
                all_ability_points.append((category, category_total))

        # Sort all categories by their point totals
        all_ability_points.sort(key=lambda x: x[1], reverse=True)

        # Pad the list if we have fewer than 3 categories with points
        while len(all_ability_points) < 3:
            all_ability_points.append(('unused', 0))

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

        results['abilities']['primary'] = all_ability_points[0][1]
        results['abilities']['secondary'] = all_ability_points[1][1]
        results['abilities']['tertiary'] = all_ability_points[2][1]

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
        """Check if character has their free dots based on splat."""
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

        if splat == 'vampire':
            # Check for 3 discipline dots
            disciplines = character.db.stats.get('powers', {}).get('discipline', {})
            total_dots = sum(values.get('perm', 0) for values in disciplines.values())
            if total_dots < 3:
                results['errors'].append(f"Vampire should have at least 3 discipline dots (has {total_dots})")
            elif total_dots > 3:
                results['errors'].append(f"Vampire should only have 3 discipline dots at creation (has {total_dots}). Current disciplines:")
                for disc, values in disciplines.items():
                    dots = values.get('perm', 0)
                    if dots > 0:
                        results['errors'].append(f"- {disc}: {dots} dots")

            # Get character's Enlightenment path
            enlightenment = character.db.stats.get('identity', {}).get('personal', {}).get('Enlightenment', {}).get('perm')
            if not enlightenment:
                results['errors'].append("Missing required identity attribute for Vampire: Enlightenment")
                return
            
            # Get required virtues for the Enlightenment path
            required_virtues = self.PATH_VIRTUES.get(enlightenment)
            if not required_virtues:
                results['errors'].append(f"Invalid Enlightenment path: {enlightenment}")
                return
            
            # Check virtues and calculate total
            virtues = character.db.stats.get('virtues', {}).get('moral', {})
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

            # Check Road rating against virtue total and cap for non-Humanity paths
            road = character.get_stat('pools', 'moral', 'Road', temp=False)
            if enlightenment != 'Humanity' and road > 5:
                results['errors'].append(f"Non-Humanity paths cannot have Road rating above 5 at character creation (currently {road})")
            if road > virtue_total:
                results['errors'].append(f"Road rating cannot exceed sum of virtues ({virtue_total}) but is {road}")
            
            # Calculate freebie points spent on Road
            freebies_spent_on_road = (road - virtue_total) * self.FREEBIE_COSTS['road'] if road > virtue_total else 0
            
            # Add virtue and road freebie costs to total
            results['freebies_spent'] = results.get('freebies_spent', 0) + freebies_spent_on_virtues + freebies_spent_on_road

            # Check Willpower against Courage
            willpower = character.get_stat('pools', 'dual', 'Willpower', temp=False)
            courage = virtues.get('Courage', {}).get('perm', 0)
            if willpower != courage:
                results['errors'].append(f"Willpower should equal Courage rating ({courage}) but is {willpower}")

        elif splat == 'mage':
            # Check for 5 sphere dots + 1 affinity
            spheres = character.db.stats.get('powers', {}).get('sphere', {})
            total_dots = sum(values.get('perm', 0) for values in spheres.values())
            if total_dots < 6:
                results['errors'].append(f"Mage should have at least 6 sphere dots (5 + 1 affinity) (has {total_dots})")

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

        elif splat == 'sorcerer':
            # Check for 6 dots of paths
            paths = character.db.stats.get('powers', {}).get('path', {})
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
            paths = character.db.stats.get('powers', {}).get('faithpath', {})
            total_dots = sum(values.get('perm', 0) for values in paths.values())
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

    def get_secondary_abilities(self, splat):
        """Get the list of secondary abilities based on character splat."""
        secondaries = {
            'talent': {
                'Carousing', 'Diplomacy', 'Intrigue', 'Mimicry', 'Scrounging', 'Seduction', 'Style'
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
            secondaries['talent'].update({'High Ritual', 'Blatancy'})
            secondaries['skill'].update({'Microgravity Ops', 'Energy Weapons', 'Helmsman', 'Biotech'})
            secondaries['knowledge'].update({'Hypertech', 'Cybernetics', 'Paraphysics', 'Xenobiology'})

        return secondaries

    def calculate_freebies(self, character, results):
        """Calculate freebie point expenditure."""
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        base_freebies = 21 if splat.lower() in ['mortal', 'mortal+'] else 15
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

        # Get secondary abilities for this character's splat
        secondary_abilities = self.get_secondary_abilities(splat)

        # Calculate attribute freebies (only for values above 5)
        for category in ['physical', 'social', 'mental']:
            attributes = character.db.stats.get('attributes', {}).get(category, {})
            for attr, values in attributes.items():
                attr_value = values.get('perm', 0)
                if attr_value > 5:  # Only charge freebies for dots above 5
                    spent_freebies += (attr_value - 5) * self.FREEBIE_COSTS['attribute']

        # Calculate ability freebies (any dots above 3)
        for category in ['talent', 'skill', 'knowledge']:
            # Check regular abilities
            abilities = character.db.stats.get('abilities', {}).get(category, {})
            for ability, values in abilities.items():
                ability_value = values.get('perm', 0)
                if ability_value > 3:
                    # If it's a secondary ability, charge half cost
                    if ability in secondary_abilities.get(category, set()):
                        spent_freebies += (ability_value - 3) * (self.FREEBIE_COSTS['ability'] / 2)
                    else:
                        spent_freebies += (ability_value - 3) * self.FREEBIE_COSTS['ability']

            # Check secondary abilities
            secondary_category = f'secondary_{category}'
            secondary_abilities_dict = character.db.stats.get('secondary_abilities', {}).get(secondary_category, {})
            for ability, values in secondary_abilities_dict.items():
                ability_value = values.get('perm', 0)
                if ability_value > 3:
                    spent_freebies += (ability_value - 3) * (self.FREEBIE_COSTS['ability'] / 2)

        # Calculate background freebies
        backgrounds = character.db.stats.get('backgrounds', {}).get('background', {})
        expected_backgrounds = 7 if splat.lower() == 'mage' else 5
        for background, values in backgrounds.items():
            background_value = values.get('perm', 0)
            if background_value > expected_backgrounds:
                spent_freebies += (background_value - expected_backgrounds) * self.FREEBIE_COSTS['background']

        # Calculate merit points
        for merit_type in ['merit', 'physical', 'social', 'mental', 'supernatural']:
            merits = character.db.stats.get('merits', {}).get(merit_type, {})
            for merit, values in merits.items():
                merit_value = values.get('perm', 0)
                spent_freebies += merit_value * self.FREEBIE_COSTS['merit']

        # Splat-specific calculations
        if splat.lower() == 'shifter':
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
            rage = character.get_stat('pools', 'dual', 'Rage', temp=False)
            gnosis = character.get_stat('pools', 'dual', 'Gnosis', temp=False)
            
            if rage > 1:  # Assuming base Rage of 1
                spent_freebies += (rage - 1) * self.FREEBIE_COSTS['rage']
            if gnosis > 1:  # Assuming base Gnosis of 1
                spent_freebies += (gnosis - 1) * self.FREEBIE_COSTS['gnosis']

        results['freebies_spent'] = spent_freebies
        results['total_freebies'] = total_freebies
        if spent_freebies > total_freebies:
            results['errors'].append(f"Too many freebie points spent: {spent_freebies}/{total_freebies}")
        elif spent_freebies < total_freebies:
            results['errors'].append(f"Not all freebie points spent: {spent_freebies}/{total_freebies}")

    def check_combo_prerequisites(self, character, combo_name):
        """Check if a character meets the prerequisites for a combo discipline."""
        if combo_name not in self.COMBO_DISCIPLINES:
            return False

        disciplines = character.db.stats.get('powers', {}).get('discipline', {})
        prereqs = self.COMBO_DISCIPLINES[combo_name]['prerequisites']

        for prereq in prereqs:
            disc_name, level = prereq.split()
            level = int(level)
            disc_value = disciplines.get(disc_name, {}).get('perm', 0)
            if disc_value < level:
                return False
        return True

    def check_required_notes(self, character, results):
        """Check if character has all required notes and identity attributes."""
        # Get all notes for the character
        notes = character.db.notes if hasattr(character.db, 'notes') else {}
        notes = notes or {}  # Convert None to empty dict
        
        # Check for backstory note (multiple possible names)
        backstory_names = ['Backstory', 'Background', 'Backstory1', 'Background1', 'BG1', 'BG']
        has_backstory = any(name in notes for name in backstory_names)
        if not has_backstory:
            results['errors'].append("Missing required backstory note (must be named one of: Backstory, Background, Backstory1, Background1, BG1, or BG)")

        # Check for XP and Freebie spend notes
        if 'XP Spends' not in notes:
            results['errors'].append("Missing required 'XP Spends' note")
        if 'Freebie Spends' not in notes:
            results['errors'].append("Missing required 'Freebie Spends' note")

        # Check common identity attributes for all splats
        required_personal = {
            'Full Name': 'identity/personal',
            'Date of Birth': 'identity/personal',
            'Concept': 'identity/personal'
        }
        required_archetype = {
            'Nature': 'archetype/personal',
            'Demeanor': 'archetype/personal'
        }

        for attr, path in required_personal.items():
            if not character.db.stats.get('identity', {}).get('personal', {}).get(attr, {}).get('perm'):
                results['errors'].append(f"Missing required identity attribute: {attr}")

        for attr, path in required_archetype.items():
            if not character.db.stats.get('archetype', {}).get('personal', {}).get(attr, {}).get('perm'):
                results['errors'].append(f"Missing required archetype attribute: {attr}")

        # Get character's splat
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower()

        # Splat-specific checks
        if splat == 'shifter':
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

        elif splat == 'mage':
            # Check required Mage attributes
            required_mage = ['Mage Faction', 'Essence']
            for attr in required_mage:
                if not character.db.stats.get('identity', {}).get('lineage', {}).get(attr, {}).get('perm'):
                    results['errors'].append(f"Missing required lineage attribute for Mage: {attr}")

            # Get Mage Faction
            affiliation = character.db.stats.get('identity', {}).get('lineage', {}).get('Mage Faction', {}).get('perm')
            if affiliation:
                if affiliation == 'Traditions' and not character.db.stats.get('identity', {}).get('lineage', {}).get('Tradition', {}).get('perm'):
                    results['errors'].append("Traditions Mage must have a Tradition set")
                elif affiliation == 'Technocracy' and not character.db.stats.get('identity', {}).get('lineage', {}).get('Convention', {}).get('perm'):
                    results['errors'].append("Technocratic Mage must have a Convention set")
                elif affiliation == 'Nephandi' and not character.db.stats.get('identity', {}).get('lineage', {}).get('Nephandi Faction', {}).get('perm'):
                    results['errors'].append("Nephandi Mage must have a Nephandi Faction set")

            # Check Mage-specific notes
            required_mage_notes = ['Paradigm', 'Practices', 'Instruments', 'Avatar']
            for note_name in required_mage_notes:
                if note_name not in notes:
                    results['errors'].append(f"Mage character missing required '{note_name}' note")

        elif splat == 'changeling':
            # Check required Changeling attributes
            required_changeling = ['Kith', 'Seeming']
            required_legacy = ['Seelie Legacy', 'Unseelie Legacy']
            
            for attr in required_changeling:
                if not character.db.stats.get('identity', {}).get('lineage', {}).get(attr, {}).get('perm'):
                    results['errors'].append(f"Missing required lineage attribute for Changeling: {attr}")

            for attr in required_legacy:
                if not character.db.stats.get('identity', {}).get('legacy', {}).get(attr, {}).get('perm'):
                    results['errors'].append(f"Missing required legacy attribute for Changeling: {attr}")

            # Check Seeming-specific requirements
            seeming = character.db.stats.get('identity', {}).get('lineage', {}).get('Seeming', {}).get('perm')
            if seeming:
                willpower = character.get_stat('pools', 'dual', 'Willpower', temp=False)
                glamour = character.get_stat('pools', 'dual', 'Glamour', temp=False)
                
                if seeming == 'Grump' and willpower < 5:
                    results['errors'].append("Grump Changelings must have Willpower >= 5")
                elif seeming == 'Wilder' and willpower < 5 and glamour < 5:
                    results['errors'].append("Wilder Changelings must have either Willpower >= 5 or Glamour >= 5")
                elif seeming == 'Childling' and glamour < 5:
                    results['errors'].append("Childling Changelings must have Glamour >= 5")

            # Check Banality requirement
            banality = character.get_stat('pools', 'dual', 'Banality', temp=False)
            if banality < 3:
                results['errors'].append("All Changelings must have Banality >= 3")

            # Check required Changeling notes
            required_changeling_notes = ['Frailties', 'Birthrights', 'Musing Threshold', 'Ravaging Threshold', 'Antithesis']
            for note_name in required_changeling_notes:
                if note_name not in notes:
                    results['errors'].append(f"Changeling character missing required '{note_name}' note")

        elif splat == 'vampire':
            # Check required Vampire attributes
            required_vampire_lineage = ['Clan', 'Generation', 'Sire']
            required_vampire_identity = ['Date of Embrace']
            
            for attr in required_vampire_lineage:
                if not character.db.stats.get('identity', {}).get('lineage', {}).get(attr, {}).get('perm'):
                    results['errors'].append(f"Missing required lineage attribute for Vampire: {attr}")

            for attr in required_vampire_identity:
                if not character.db.stats.get('identity', {}).get('personal', {}).get(attr, {}).get('perm'):
                    results['errors'].append(f"Missing required identity attribute for Vampire: {attr}")

            # Check merit/flaw explanation notes
            merit_categories = ['merit', 'physical', 'social', 'mental', 'supernatural']
            flaw_categories = ['flaw', 'physical', 'social', 'mental', 'supernatural']
            
            merits = character.db.stats.get('merits', {})
            flaws = character.db.stats.get('flaws', {})
            
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

        elif splat == 'companion':
            # Check required Companion attributes
            required_companion = ['Companion Type', 'Mage Faction', 'Motivation']
            for attr in required_companion:
                if not character.db.stats.get('identity', {}).get('lineage', {}).get(attr, {}).get('perm'):
                    results['errors'].append(f"Missing required lineage attribute for Companion: {attr}")

            # Verify companion type and appropriate flaw
            companion_type = character.get_stat('identity', 'lineage', 'Companion Type', '').lower()
            if companion_type in POWER_SOURCE_TYPES:
                if not character.get_stat('flaws', 'flaw', 'Power Source'):
                    results['errors'].append(f"Companion of type {companion_type} must have Power Source flaw")
            else:
                if not character.get_stat('flaws', 'flaw', 'Thaumivore'):
                    results['errors'].append(f"Companion must have Thaumivore flaw")

            # Check required notes
            required_companion_notes = ['Origin', 'Description']
            for note_name in required_companion_notes:
                if note_name not in notes:
                    results['errors'].append(f"Companion character missing required '{note_name}' note")

    def calculate_xp(self, character, results):
        """Calculate XP expenditure if character has starting XP."""
        # Get XP from the character's xp attribute
        xp_data = character.db.xp if hasattr(character.db, 'xp') else None
        if not xp_data or not isinstance(xp_data, dict):
            return

        starting_xp = xp_data.get('total', 0)
        if not starting_xp:
            return

        spent_xp = 0
        xp_breakdown = {}
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')

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
                    if ability in secondary_abilities.get(category, set()):
                        ability_xp += (ability_value - 3) * (self.XP_COSTS['ability'] / 2)
                    else:
                        ability_xp += (ability_value - 3) * self.XP_COSTS['ability']
        if ability_xp > 0:
            xp_breakdown['Abilities'] = ability_xp
            spent_xp += ability_xp

        # Calculate specialty XP
        specialty_xp = 0
        specialties = character.db.specialties if hasattr(character.db, 'specialties') else {}
        for ability_specialties in specialties.values():
            specialty_xp += len(ability_specialties) * self.XP_COSTS['specialty']
        if specialty_xp > 0:
            xp_breakdown['Specialties'] = specialty_xp
            spent_xp += specialty_xp

        # Calculate background XP
        background_xp = 0
        backgrounds = character.db.stats.get('backgrounds', {}).get('background', {})
        expected_backgrounds = 7 if splat.lower() == 'mage' else 5
        for background, values in backgrounds.items():
            background_value = values.get('perm', 0)
            if background_value > expected_backgrounds:
                background_xp += (background_value - expected_backgrounds) * self.XP_COSTS['background']
        if background_xp > 0:
            xp_breakdown['Backgrounds'] = background_xp
            spent_xp += background_xp

        # Splat-specific XP calculations
        if splat.lower() == 'shifter':
            # Calculate Gift XP
            gift_xp = 0
            gifts = character.db.stats.get('powers', {}).get('gift', {})
            for gift, values in gifts.items():
                gift_value = values.get('perm', 0)
                if gift_value > 1:  # Only count gifts above level 1
                    gift_xp += (gift_value - 1) * self.XP_COSTS['gift']
            if gift_xp > 0:
                xp_breakdown['Gifts'] = gift_xp
                spent_xp += gift_xp

            # Calculate Rage and Gnosis XP
            pool_xp = 0
            rage = character.get_stat('pools', 'dual', 'Rage', temp=False)
            gnosis = character.get_stat('pools', 'dual', 'Gnosis', temp=False)
            
            if rage > 3:  # Assuming max of 3 from freebies
                pool_xp += (rage - 3) * self.XP_COSTS['rage']
            if gnosis > 3:  # Assuming max of 3 from freebies
                pool_xp += (gnosis - 3) * self.XP_COSTS['gnosis']
            if pool_xp > 0:
                xp_breakdown['Pools'] = pool_xp
                spent_xp += pool_xp

        elif splat.lower() == 'mage':
            # Calculate Sphere XP
            sphere_xp = 0
            spheres = character.db.stats.get('powers', {}).get('sphere', {})
            for sphere, values in spheres.items():
                sphere_value = values.get('perm', 0)
                if sphere_value > 3:  # Assuming max of 3 from freebies
                    sphere_xp += (sphere_value - 3) * self.XP_COSTS['sphere']
            if sphere_xp > 0:
                xp_breakdown['Spheres'] = sphere_xp
                spent_xp += sphere_xp

            # Calculate Arete XP
            arete_xp = 0
            arete = character.get_stat('pools', 'dual', 'Arete', temp=False)
            if arete > 3:  # Max of 3 at character creation
                arete_xp += (arete - 3) * self.XP_COSTS['arete']
            if arete_xp > 0:
                xp_breakdown['Arete'] = arete_xp
                spent_xp += arete_xp

        results['xp_spent'] = spent_xp
        results['total_xp'] = float(starting_xp)  # Convert Decimal to float
        results['xp_breakdown'] = xp_breakdown
        
        if spent_xp > float(starting_xp):
            results['errors'].append(f"Too much XP spent ({spent_xp} XP spent vs {float(starting_xp)} XP available)")
        elif spent_xp < float(starting_xp):
            results['errors'].append(f"Not all XP spent ({spent_xp} XP spent vs {float(starting_xp)} XP available)")

    def display_results(self, character, results):
        """Display the results of the character check."""
        output = [
            f"|wCharacter Check Results for {character.name}|n",
            "",
            "|yAttributes:|n",
            f"Primary: {results['attributes']['primary']}/7",
            f"Secondary: {results['attributes']['secondary']}/5",
            f"Tertiary: {results['attributes']['tertiary']}/3",
            "",
            "|yAbilities:|n",
            f"Primary: {results['abilities']['primary']}/13",
            f"Secondary: {results['abilities']['secondary']}/9",
            f"Tertiary: {results['abilities']['tertiary']}/5",
            "",
            f"|yBackgrounds:|n {results['backgrounds']}/{'7' if character.get_stat('other', 'splat', 'Splat').lower() == 'mage' else '5'}",
            "",
            "|yMerits & Flaws:|n",
            f"Merit dots: {results.get('merits', 0)}",
            f"Flaw dots: {results.get('flaws', 0)}/7"
        ]

        # Add splat-specific power information
        splat = character.get_stat('other', 'splat', 'Splat').lower()
        
        if splat == 'vampire':
            disciplines = character.db.stats.get('powers', {}).get('discipline', {})
            total_dots = sum(values.get('perm', 0) for values in disciplines.values())
            output.extend([
                "",
                "|yDisciplines:|n",
                f"Total dots: {total_dots} (Free: 3, Extra: {total_dots - 3})",
                "Current disciplines:"
            ])
            for disc, values in disciplines.items():
                dots = values.get('perm', 0)
                if dots > 0:
                    output.append(f"- {disc}: {dots}")

        elif splat == 'mage':
            spheres = character.db.stats.get('powers', {}).get('sphere', {})
            total_dots = sum(values.get('perm', 0) for values in spheres.values())
            output.extend([
                "",
                "|ySpheres:|n",
                f"Total dots: {total_dots} (Free: 6 [5 + 1 affinity], Extra: {total_dots - 6})",
                "Current spheres:"
            ])
            for sphere, values in spheres.items():
                dots = values.get('perm', 0)
                if dots > 0:
                    output.append(f"- {sphere}: {dots}")

        elif splat == 'changeling':
            arts = character.db.stats.get('powers', {}).get('art', {})
            realms = character.db.stats.get('powers', {}).get('realm', {})
            art_dots = sum(values.get('perm', 0) for values in arts.values())
            realm_dots = sum(values.get('perm', 0) for values in realms.values())
            output.extend([
                "",
                "|yArts & Realms:|n",
                f"Art dots: {art_dots} (Free: 3, Extra: {art_dots - 3})",
                f"Realm dots: {realm_dots} (Free: 5, Extra: {realm_dots - 5})",
                "Current arts:"
            ])
            for art, values in arts.items():
                dots = values.get('perm', 0)
                if dots > 0:
                    output.append(f"- {art}: {dots}")
            output.append("Current realms:")
            for realm, values in realms.items():
                dots = values.get('perm', 0)
                if dots > 0:
                    output.append(f"- {realm}: {dots}")

        elif splat == 'shifter':
            gifts = character.db.stats.get('powers', {}).get('gift', {})
            shifter_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '').lower()
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
            free_gifts = gift_requirements.get(shifter_type, {}).get('count', 0)
            total_gifts = len(gifts) if gifts else 0
            output.extend([
                "",
                "|yGifts:|n",
                f"Total gifts: {total_gifts} (Free: {free_gifts}, Extra: {total_gifts - free_gifts})",
                f"Required gifts: {gift_requirements.get(shifter_type, {}).get('msg', 'Unknown shifter type')}",
                "Current gifts:"
            ])
            for gift in gifts:
                output.append(f"- {gift}")

        elif splat == 'sorcerer':
            paths = character.db.stats.get('powers', {}).get('path', {})
            total_dots = sum(values.get('perm', 0) for values in paths.values())
            output.extend([
                "",
                "|yPaths:|n",
                f"Total dots: {total_dots} (Free: 6, Extra: {total_dots - 6})",
                "Current paths:"
            ])
            for path, values in paths.items():
                dots = values.get('perm', 0)
                if dots > 0:
                    output.append(f"- {path}: {dots}")

        elif splat == 'psychic':
            numina = character.db.stats.get('powers', {}).get('numina', {})
            total_dots = sum(values.get('perm', 0) for values in numina.values())
            output.extend([
                "",
                "|yNumina:|n",
                f"Total dots: {total_dots} (Free: 6, Extra: {total_dots - 6})",
                "Current numina:"
            ])
            for power, values in numina.items():
                dots = values.get('perm', 0)
                if dots > 0:
                    output.append(f"- {power}: {dots}")

        output.extend([
            "",
            f"|yFreebie Points:|n {results['freebies_spent']}/{results['total_freebies']}"
        ])

        # Add XP information if character has starting XP
        if 'total_xp' in results:
            output.extend([
                "",
                f"|yStarting XP:|n {results['xp_spent']}/{results['total_xp']}"
            ])
            
            # Add XP spending breakdown if any XP was spent
            if results['xp_spent'] > 0 and hasattr(results, 'xp_breakdown'):
                output.extend([
                    "",
                    "|yXP Spending Breakdown:|n"
                ])
                for category, amount in results.get('xp_breakdown', {}).items():
                    if amount > 0:
                        output.append(f"- {category}: {amount} XP")

        output.append("")

        if results['errors']:
            output.append("|rErrors:|n")
            for error in results['errors']:
                output.append(f"- {error}")
        else:
            output.append("|gNo errors found. Character creation points are properly allocated.|n")

        self.caller.msg("\n".join(output)) 