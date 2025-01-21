from evennia.commands.default.muxcommand import MuxCommand
from world.wod20th.models import Stat

class CmdCheck(MuxCommand):
    """
    Check character creation points allocation.

    Usage:
      +check
      +check <character>

    This command verifies that a character's attributes, abilities,
    backgrounds, and other traits are properly allocated according
    to the character creation rules.
    """

    key = "+check"
    aliases = ["check"]
    locks = "cmd:all()"
    help_category = "Character"

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

    def func(self):
        """Execute the command."""
        if not self.args:
            character = self.caller
        else:
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
        ability_categories = ['talent', 'skill', 'knowledge']
        ability_totals = []

        for category in ability_categories:
            total = 0
            abilities = character.db.stats.get('abilities', {}).get(category, {})
            for ability, values in abilities.items():
                ability_value = values.get('perm', 0)
                if ability_value > 0:
                    total += ability_value
            ability_totals.append((category, total))

        # Sort totals to determine primary/secondary/tertiary
        ability_totals.sort(key=lambda x: x[1], reverse=True)
        
        # Check against expected values
        if ability_totals[0][1] != 13:
            results['errors'].append(f"Primary abilities ({ability_totals[0][0]}) should have 13 points, has {ability_totals[0][1]}")
        if ability_totals[1][1] != 9:
            results['errors'].append(f"Secondary abilities ({ability_totals[1][0]}) should have 9 points, has {ability_totals[1][1]}")
        if ability_totals[2][1] != 5:
            results['errors'].append(f"Tertiary abilities ({ability_totals[2][0]}) should have 5 points, has {ability_totals[2][1]}")

        results['abilities']['primary'] = ability_totals[0][1]
        results['abilities']['secondary'] = ability_totals[1][1]
        results['abilities']['tertiary'] = ability_totals[2][1]

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

    def calculate_freebies(self, character, results):
        """Calculate freebie point expenditure."""
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        total_freebies = 21 if splat.lower() in ['mortal', 'mortal+'] else 15
        spent_freebies = 0

        # Calculate attribute freebies
        for category in ['physical', 'social', 'mental']:
            attributes = character.db.stats.get('attributes', {}).get(category, {})
            for attr, values in attributes.items():
                attr_value = values.get('perm', 0)
                if attr_value > 3:  # Assuming anything above 3 was bought with freebies
                    spent_freebies += (attr_value - 3) * self.FREEBIE_COSTS['attribute']

        # Calculate ability freebies
        for category in ['talent', 'skill', 'knowledge']:
            abilities = character.db.stats.get('abilities', {}).get(category, {})
            for ability, values in abilities.items():
                ability_value = values.get('perm', 0)
                if ability_value > 3:  # Assuming anything above 3 was bought with freebies
                    spent_freebies += (ability_value - 3) * self.FREEBIE_COSTS['ability']

        # Calculate background freebies
        backgrounds = character.db.stats.get('backgrounds', {}).get('background', {})
        expected_backgrounds = 7 if splat.lower() == 'mage' else 5
        for background, values in backgrounds.items():
            background_value = values.get('perm', 0)
            if background_value > expected_backgrounds:
                spent_freebies += (background_value - expected_backgrounds) * self.FREEBIE_COSTS['background']

        # Calculate merit and flaw points
        for merit_type in ['merit']:
            merits = character.db.stats.get('merits', {}).get(merit_type, {})
            for merit, values in merits.items():
                merit_value = values.get('perm', 0)
                spent_freebies += merit_value * self.FREEBIE_COSTS['merit']

        for flaw_type in ['flaw']:
            flaws = character.db.stats.get('flaws', {}).get(flaw_type, {})
            for flaw, values in flaws.items():
                flaw_value = values.get('perm', 0)
                spent_freebies += flaw_value * self.FREEBIE_COSTS['flaw']  # This will subtract points

        # Splat-specific calculations
        if splat.lower() == 'shifter':
            # Calculate Gift costs
            gifts = character.db.stats.get('powers', {}).get('gift', {})
            for gift, values in gifts.items():
                gift_value = values.get('perm', 0)
                if gift_value == 1:  # Only count level 1 gifts
                    spent_freebies += self.FREEBIE_COSTS['gift']

            # Calculate Rage and Gnosis costs
            rage = character.get_stat('pools', 'dual', 'Rage', temp=False)
            gnosis = character.get_stat('pools', 'dual', 'Gnosis', temp=False)
            
            # Subtract starting values based on breed/auspice
            breed = character.get_stat('identity', 'lineage', 'Breed', temp=False)
            auspice = character.get_stat('identity', 'lineage', 'Auspice', temp=False)
            
            if rage > 1:  # Assuming base Rage of 1
                spent_freebies += (rage - 1) * self.FREEBIE_COSTS['rage']
            if gnosis > 1:  # Assuming base Gnosis of 1
                spent_freebies += (gnosis - 1) * self.FREEBIE_COSTS['gnosis']

        elif splat.lower() == 'mage':
            # Calculate Sphere costs
            spheres = character.db.stats.get('powers', {}).get('sphere', {})
            for sphere, values in spheres.items():
                sphere_value = values.get('perm', 0)
                if sphere_value > 0:
                    spent_freebies += sphere_value * self.FREEBIE_COSTS['sphere']

            # Calculate Arete costs
            arete = character.get_stat('pools', 'dual', 'Arete', temp=False)
            if arete > 1:  # Assuming base Arete of 1
                spent_freebies += (arete - 1) * self.FREEBIE_COSTS['arete']

            # Calculate Quintessence costs
            quintessence = character.get_stat('pools', 'dual', 'Quintessence', temp=False)
            if quintessence > 0:
                spent_freebies += quintessence * self.FREEBIE_COSTS['quintessence']

        elif splat.lower() == 'vampire':
            # Calculate Discipline costs
            disciplines = character.db.stats.get('powers', {}).get('discipline', {})
            for discipline, values in disciplines.items():
                discipline_value = values.get('perm', 0)
                if discipline_value > 0:
                    spent_freebies += discipline_value * self.FREEBIE_COSTS['discipline']

            # Calculate Road costs
            road = character.get_stat('pools', 'moral', 'Road', temp=False)
            if road > 1:  # Assuming base Road of 1
                spent_freebies += (road - 1) * self.FREEBIE_COSTS['road']

        elif splat.lower() == 'changeling':
            # Calculate Art costs
            arts = character.db.stats.get('powers', {}).get('art', {})
            for art, values in arts.items():
                art_value = values.get('perm', 0)
                if art_value > 0:
                    spent_freebies += art_value * self.FREEBIE_COSTS['art']

            # Calculate Realm costs
            realms = character.db.stats.get('powers', {}).get('realm', {})
            for realm, values in realms.items():
                realm_value = values.get('perm', 0)
                if realm_value > 0:
                    spent_freebies += realm_value * self.FREEBIE_COSTS['realm']

            # Calculate Glamour costs
            glamour = character.get_stat('pools', 'dual', 'Glamour', temp=False)
            if glamour > 1:  # Assuming base Glamour of 1
                spent_freebies += (glamour - 1) * self.FREEBIE_COSTS['glamour']

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

    def calculate_xp(self, character, results):
        """Calculate XP expenditure if character has starting XP."""
        starting_xp = character.db.stats.get('other', {}).get('xp', {}).get('Starting XP', {}).get('perm', 0)
        if not starting_xp:
            return

        spent_xp = 0
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')

        # Calculate attribute XP
        for category in ['physical', 'social', 'mental']:
            attributes = character.db.stats.get('attributes', {}).get(category, {})
            for attr, values in attributes.items():
                attr_value = values.get('perm', 0)
                if attr_value > 5:  # Assuming max of 5 from freebies
                    spent_xp += (attr_value - 5) * self.XP_COSTS['attribute']

        # Calculate ability XP
        for category in ['talent', 'skill', 'knowledge']:
            abilities = character.db.stats.get('abilities', {}).get(category, {})
            for ability, values in abilities.items():
                ability_value = values.get('perm', 0)
                if ability_value > 3:  # Assuming max of 3 from freebies
                    spent_xp += (ability_value - 3) * self.XP_COSTS['ability']

        # Calculate specialty XP
        specialties = character.db.specialties if hasattr(character.db, 'specialties') else {}
        for ability_specialties in specialties.values():
            spent_xp += len(ability_specialties) * self.XP_COSTS['specialty']

        # Calculate background XP
        backgrounds = character.db.stats.get('backgrounds', {}).get('background', {})
        expected_backgrounds = 7 if splat.lower() == 'mage' else 5
        for background, values in backgrounds.items():
            background_value = values.get('perm', 0)
            if background_value > expected_backgrounds:
                spent_xp += (background_value - expected_backgrounds) * self.XP_COSTS['background']

        # Splat-specific XP calculations
        if splat.lower() == 'shifter':
            # Calculate Gift XP
            gifts = character.db.stats.get('powers', {}).get('gift', {})
            for gift, values in gifts.items():
                gift_value = values.get('perm', 0)
                if gift_value > 1:  # Only count gifts above level 1
                    spent_xp += (gift_value - 1) * self.XP_COSTS['gift']

            # Calculate Rage and Gnosis XP
            rage = character.get_stat('pools', 'dual', 'Rage', temp=False)
            gnosis = character.get_stat('pools', 'dual', 'Gnosis', temp=False)
            
            if rage > 3:  # Assuming max of 3 from freebies
                spent_xp += (rage - 3) * self.XP_COSTS['rage']
            if gnosis > 3:  # Assuming max of 3 from freebies
                spent_xp += (gnosis - 3) * self.XP_COSTS['gnosis']

        elif splat.lower() == 'mage':
            # Calculate Sphere XP
            spheres = character.db.stats.get('powers', {}).get('sphere', {})
            for sphere, values in spheres.items():
                sphere_value = values.get('perm', 0)
                if sphere_value > 3:  # Assuming max of 3 from freebies
                    spent_xp += (sphere_value - 3) * self.XP_COSTS['sphere']

            # Calculate Arete XP
            arete = character.get_stat('pools', 'dual', 'Arete', temp=False)
            if arete > 3:  # Max of 3 at character creation
                spent_xp += (arete - 3) * self.XP_COSTS['arete']

        elif splat.lower() == 'vampire':
            # Calculate Discipline XP
            disciplines = character.db.stats.get('powers', {}).get('discipline', {})
            for discipline, values in disciplines.items():
                discipline_value = values.get('perm', 0)
                if discipline_value > 3:  # Assuming max of 3 from freebies
                    spent_xp += (discipline_value - 3) * self.XP_COSTS['discipline']

            # Calculate Combo Discipline XP
            combo_disciplines = character.db.stats.get('powers', {}).get('combodiscipline', {})
            if combo_disciplines:
                for combo, values in combo_disciplines.items():
                    combo_value = values.get('perm', 0)
                    if combo_value > 0 and combo in self.COMBO_DISCIPLINES:
                        # Check if character meets prerequisites
                        if self.check_combo_prerequisites(character, combo):
                            spent_xp += self.COMBO_DISCIPLINES[combo]['cost']
                        else:
                            results['errors'].append(f"Character has combo discipline '{combo}' but doesn't meet prerequisites")

            # Calculate Road XP
            road = character.get_stat('pools', 'moral', 'Road', temp=False)
            if road > 3:  # Assuming max of 3 from freebies
                spent_xp += (road - 3) * self.XP_COSTS['road']

        elif splat.lower() == 'changeling':
            # Calculate Art XP
            arts = character.db.stats.get('powers', {}).get('art', {})
            for art, values in arts.items():
                art_value = values.get('perm', 0)
                if art_value > 3:  # Assuming max of 3 from freebies
                    spent_xp += (art_value - 3) * self.XP_COSTS['art']

            # Calculate Realm XP
            realms = character.db.stats.get('powers', {}).get('realm', {})
            for realm, values in realms.items():
                realm_value = values.get('perm', 0)
                if realm_value > 3:  # Assuming max of 3 from freebies
                    spent_xp += (realm_value - 3) * self.XP_COSTS['realm']

            # Calculate Glamour XP
            glamour = character.get_stat('pools', 'dual', 'Glamour', temp=False)
            if glamour > 3:  # Assuming max of 3 from freebies
                spent_xp += (glamour - 3) * self.XP_COSTS['glamour']

        results['xp_spent'] = spent_xp
        results['total_xp'] = starting_xp
        if spent_xp > starting_xp:
            results['errors'].append(f"Too much XP spent: {spent_xp}/{starting_xp}")
        elif spent_xp < starting_xp:
            results['errors'].append(f"Not all XP spent: {spent_xp}/{starting_xp}")

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
            f"|yFreebie Points:|n {results['freebies_spent']}/{results['total_freebies']}"
        ]

        # Add XP information if character has starting XP
        if 'total_xp' in results:
            output.extend([
                "",
                f"|yStarting XP:|n {results['xp_spent']}/{results['total_xp']}"
            ])

            # If character is a vampire, show available combo disciplines
            if character.get_stat('other', 'splat', 'Splat').lower() == 'vampire':
                available_combos = [
                    combo for combo in self.COMBO_DISCIPLINES
                    if self.check_combo_prerequisites(character, combo)
                ]
                if available_combos:
                    output.extend([
                        "",
                        "|yAvailable Combo Disciplines:|n"
                    ])
                    for combo in available_combos:
                        prereqs = ', '.join(self.COMBO_DISCIPLINES[combo]['prerequisites'])
                        output.append(f"- {combo} ({self.COMBO_DISCIPLINES[combo]['cost']} XP) - Requires: {prereqs}")

        output.append("")

        if results['errors']:
            output.append("|rErrors:|n")
            for error in results['errors']:
                output.append(f"- {error}")
        else:
            output.append("|gNo errors found. Character creation points are properly allocated.|n")

        self.caller.msg("\n".join(output)) 