from evennia import default_cmds
from evennia.utils.evtable import EvTable
from decimal import Decimal
from commands.CmdCheck import CmdCheck
from world.wod20th.models import Stat
from django.db.models import Q
from world.wod20th.utils.stat_mappings import (
    UNIVERSAL_BACKGROUNDS, VAMPIRE_BACKGROUNDS, CHANGELING_BACKGROUNDS,
    MAGE_BACKGROUNDS, TECHNOCRACY_BACKGROUNDS, TRADITIONS_BACKGROUNDS,
    NEPHANDI_BACKGROUNDS, SHIFTER_BACKGROUNDS, SORCERER_BACKGROUNDS
)

class CmdXPCost(default_cmds.MuxCommand):
    """
    View costs for character advancement.
    
    Usage:
      +costs              - Show all available purchases
      +costs/attributes   - Show attribute costs
      +costs/abilities    - Show ability costs
      +costs/secondary_abilities - Show secondary ability costs
      +costs/backgrounds  - Show background costs
      +costs/powers      - Show power/gift costs
      +costs/pools       - Show pool costs
      +costs/disciplines - Show discipline and combo discipline costs
    """
    
    key = "+costs"
    aliases = ["costs"]
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        """Execute command"""
        if not self.switches:
            # Show overview of all categories
            self._display_all_costs(self.caller)
            return
            
        switch = self.switches[0].lower()
        if switch in ["attributes", "abilities", "secondary_abilities", "backgrounds", "powers", "pools", "disciplines"]:
            self._display_category_costs(self.caller, switch)
        else:
            self.caller.msg("Invalid switch. Use +help costs for usage information.")

    def _display_category_costs(self, character, category):
        """Display costs for a specific category"""
        current_xp = character.db.xp.get('current', 0) if character.db.xp else 0
        total_width = 78
        
        # Create section header
        title = f" {category.title()} Costs "
        title_len = len(title)
        dash_count = (total_width - title_len) // 2
        header = f"|b{'-' * dash_count}|y{title}|n|b{'-' * (total_width - dash_count - title_len)}|n\n"
        
        # Create table with blue borders
        table = EvTable(
            "|wPurchase|n",
            "|wCurrent|n",
            "|wNext|n",
            "|wCost|n",
            "|wAffordable|n",
            border="table",
            width=total_width
        )
        
        # Add blue color to the table border
        table.border_left = "|b||n"
        table.border_right = "|b||n"
        table.border_top = "|b-|n"
        table.border_bottom = "|b-|n"
        table.corner_top_left = "|b+|n"
        table.corner_top_right = "|b+|n"
        table.corner_bottom_left = "|b+|n"
        table.corner_bottom_right = "|b+|n"

        def get_affordable_status(cost, current_xp, requires_approval):
            """Helper function to determine affordable status"""
            if cost > current_xp:
                return "No"
            elif requires_approval:
                return "Req. Approval"
            else:
                return "Yes"

        if category == "disciplines" and character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower() == 'vampire':
            # Regular Disciplines
            table.add_row("|yRegular Disciplines:|n", "", "", "", "")
            table.add_row("|rNote: Only Potence, Celerity, Fortitude, Obfuscate, and Auspex can be purchased.|n", "", "", "", "")
            disciplines = character.db.stats.get('powers', {}).get('discipline', {})
            for discipline, values in disciplines.items():
                current = values.get('perm', 0)
                if current < 5:  # Max rating of 5
                    next_rating = current + 1
                    try:
                        cost, requires_approval = character.calculate_xp_cost(
                            discipline, 
                            next_rating, 
                            category='powers',
                            subcategory='discipline',
                            current_rating=current
                        )
                        table.add_row(
                            f"  {discipline}",
                            str(current),
                            str(next_rating),
                            str(cost),
                            get_affordable_status(cost, current_xp, requires_approval)
                        )
                    except Exception as e:
                        character.msg(f"Error calculating cost for {discipline}: {str(e)}")
                        continue

            # Combo Disciplines
            table.add_row("", "", "", "", "")
            table.add_row("|yAvailable Combo Disciplines:|n", "", "", "", "")
            table.add_row("Name", "Prereqs", "Cost", "Affordable", "")

            # Get character's disciplines and levels
            disciplines = character.db.stats.get('powers', {}).get('discipline', {})
            
            # Query combo disciplines from database
            combo_query = Q(stat_type='combodiscipline')
            if character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower() == 'vampire':
                combo_query &= (Q(splat__iexact='vampire') | Q(splat__isnull=True))
            
            available_combos = []
            for combo in Stat.objects.filter(combo_query).order_by('name'):
                # Check prerequisites
                meets_prereqs = True
                if combo.prerequisites:
                    # Convert string prerequisites to list if it's a string representation of a list
                    if combo.prerequisites.startswith('[') and combo.prerequisites.endswith(']'):
                        prereq_list = eval(combo.prerequisites)
                    else:
                        prereq_list = [combo.prerequisites]
                    
                    # Check each prerequisite
                    for prereq in prereq_list:
                        try:
                            # Split on the last space to separate discipline name from level
                            parts = prereq.rsplit(' ', 1)
                            if len(parts) != 2:
                                meets_prereqs = False
                                break
                            
                            disc_name, level_str = parts
                            try:
                                required_level = int(level_str)
                            except ValueError:
                                meets_prereqs = False
                                break
                            
                            # Get character's level in this discipline
                            character_level = 0
                            for d_name, d_values in disciplines.items():
                                if d_name.lower() == disc_name.lower():
                                    character_level = d_values.get('perm', 0)
                                    break
                            
                            if character_level < required_level:
                                meets_prereqs = False
                                break
                            
                        except Exception:
                            meets_prereqs = False
                            break
                
                if meets_prereqs:
                    available_combos.append(combo)

            # Display available combos
            for combo in available_combos:
                table.add_row(
                    f"  {combo.name}",
                    combo.prerequisites,
                    str(combo.xp_cost if combo.xp_cost else 0),
                    get_affordable_status(combo.xp_cost if combo.xp_cost else 0, current_xp, True),  # Combo disciplines always require approval
                    ""
                )

            if not available_combos:
                table.add_row("  No combo disciplines available with current disciplines.", "", "", "", "")

        elif category == "attributes":
            # Add section headers for each subcategory
            subcategories = [
                ('physical', ['Strength', 'Dexterity', 'Stamina']),
                ('social', ['Charisma', 'Manipulation', 'Appearance']),
                ('mental', ['Perception', 'Intelligence', 'Wits'])
            ]
            
            for subcat, stats in subcategories:
                # Add subcategory header with divider
                table.add_row(f"|y{subcat.title()} Attributes:|n", "", "", "", "")
                for stat in stats:
                    # Get the current value from the nested structure
                    current = character.db.stats.get('attributes', {}).get(subcat, {}).get(stat, {}).get('perm', 0)
                    if current < 5:  # Max rating of 5
                        next_rating = current + 1
                        try:
                            cost, requires_approval = character.calculate_xp_cost(
                                stat, 
                                next_rating, 
                                category='attributes',
                                subcategory=subcat,
                                current_rating=current
                            )
                            table.add_row(
                                f"  {stat}",
                                str(current),
                                str(next_rating),
                                str(cost),
                                get_affordable_status(cost, current_xp, requires_approval)
                            )
                        except Exception as e:
                            character.msg(f"Error calculating cost for {stat}: {str(e)}")
                            continue

        elif category == "abilities":
            # Get character's splat and other relevant info
            splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            clan = character.db.stats.get('other', {}).get('clan', {}).get('Clan', {}).get('perm', '')
            shifter_type = character.db.stats.get('other', {}).get('shifter_type', {}).get('Shifter Type', {}).get('perm', '')

            # Primary abilities
            subcategories = [
                ('talent', ['Alertness', 'Athletics', 'Awareness', 'Brawl', 'Empathy',
                           'Expression', 'Intimidation', 'Leadership', 'Streetwise', 'Subterfuge']),
                ('skill', ['Animal Ken', 'Crafts', 'Drive', 'Etiquette', 'Firearms',
                          'Larceny', 'Melee', 'Performance', 'Stealth', 'Survival']),
                ('knowledge', ['Academics', 'Computer', 'Enigmas', 'Finance', 'Investigation', 'Law',
                             'Medicine', 'Occult', 'Politics', 'Science', 'Technology'])
            ]

            # Add splat-specific primary abilities
            if splat == 'Shifter':
                # Add Primal-Urge for all shifters
                subcategories[0][1].append('Primal-Urge')
                # Add Flight for specific shifter types
                if shifter_type and shifter_type.strip() in ['Corax', 'Camazotz', 'Mokole']:
                    subcategories[0][1].append('Flight')
                # Add Rituals for all shifters
                subcategories[2][1].append('Rituals')
            elif splat == 'Vampire' and clan and clan.strip() == 'Gargoyle':
                # Add Flight for Gargoyle vampires
                subcategories[0][1].append('Flight')
            elif splat == 'Changeling':
                # Add Changeling-specific abilities
                subcategories[0][1].append('Kenning')
                subcategories[2][1].extend(['Gremayre', 'Gematria'])

            # Sort abilities alphabetically within each subcategory
            for i in range(len(subcategories)):
                subcategories[i] = (subcategories[i][0], sorted(subcategories[i][1]))

            # Display primary abilities
            table.add_row("|yPrimary Abilities:|n", "", "", "", "")
            for subcat, stats in subcategories:
                table.add_row(f"|y{subcat.title()} Abilities:|n", "", "", "", "")
                for stat in stats:
                    current = int(character.get_stat('abilities', subcat, stat) or 0)
                    if current < 5:
                        next_rating = current + 1
                        try:
                            cost, requires_approval = character.calculate_xp_cost(
                                stat, 
                                next_rating, 
                                category='abilities',
                                subcategory=subcat,
                                current_rating=current
                            )
                            table.add_row(
                                f"  {stat}",
                                str(current),
                                str(next_rating),
                                str(cost),
                                get_affordable_status(cost, current_xp, requires_approval)
                            )
                        except Exception as e:
                            character.msg(f"Error calculating cost for {stat}: {str(e)}")
                            continue

            # Secondary abilities
            secondary_subcategories = [
                ('secondary_talent', ['Carousing', 'Diplomacy', 'Intrigue', 'Mimicry', 'Scrounging', 'Seduction', 'Style']),
                ('secondary_skill', ['Archery', 'Fortune-Telling', 'Fencing', 'Gambling', 'Jury-Rigging', 'Pilot', 'Torture']),
                ('secondary_knowledge', ['Area Knowledge', 'Cultural Savvy', 'Demolitions', 'Herbalism', 'Media', 'Power-Brokering', 'Vice'])
            ]

            # Add Mage-specific secondary abilities
            if splat.lower() == 'mage':
                secondary_subcategories[0][1].extend(['High Ritual', 'Blatancy'])
                secondary_subcategories[1][1].extend(['Microgravity Ops', 'Energy Weapons', 'Helmsman', 'Biotech'])
                secondary_subcategories[2][1].extend(['Hypertech', 'Cybernetics', 'Paraphysics', 'Xenobiology'])

            # Sort secondary abilities alphabetically within each subcategory
            for i in range(len(secondary_subcategories)):
                secondary_subcategories[i] = (secondary_subcategories[i][0], sorted(secondary_subcategories[i][1]))

            # Display secondary abilities
            table.add_row("", "", "", "", "")  # Empty row for spacing
            table.add_row("|ySecondary Abilities:|n", "", "", "", "")
            for subcat, stats in secondary_subcategories:
                display_subcat = subcat.replace('secondary_', '').title()
                table.add_row(f"|y{display_subcat} Abilities:|n", "", "", "", "")
                for stat in stats:
                    current = int(character.get_stat('secondary_abilities', subcat, stat) or 0)
                    if current < 5:
                        next_rating = current + 1
                        try:
                            cost, requires_approval = character.calculate_xp_cost(
                                stat, 
                                next_rating, 
                                category='secondary_abilities',
                                subcategory=subcat,
                                current_rating=current
                            )
                            table.add_row(
                                f"  {stat}",
                                str(current),
                                str(next_rating),
                                str(cost),
                                get_affordable_status(cost, current_xp, requires_approval)
                            )
                        except Exception as e:
                            character.msg(f"Error calculating cost for {stat}: {str(e)}")
                            continue

        elif category == "backgrounds":
            # Get character's splat to determine available backgrounds
            splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            
            # Start with universal backgrounds available to all splats
            available_backgrounds = list(UNIVERSAL_BACKGROUNDS)
            
            # Add splat-specific backgrounds
            if splat.lower() == 'vampire':
                available_backgrounds.extend(VAMPIRE_BACKGROUNDS)
            elif splat.lower() == 'changeling':
                available_backgrounds.extend(CHANGELING_BACKGROUNDS)
            elif splat.lower() == 'mage':
                available_backgrounds.extend(MAGE_BACKGROUNDS)
                
                # Check mage affiliation for additional backgrounds
                affiliation = character.db.stats.get('identity', {}).get('lineage', {}).get('Affiliation', {}).get('perm', '')
                if affiliation == 'Technocracy':
                    available_backgrounds.extend(TECHNOCRACY_BACKGROUNDS)
                elif affiliation == 'Traditions':
                    available_backgrounds.extend(TRADITIONS_BACKGROUNDS)
                elif affiliation == 'Nephandi':
                    available_backgrounds.extend(NEPHANDI_BACKGROUNDS)
            elif splat.lower() == 'shifter':
                available_backgrounds.extend(SHIFTER_BACKGROUNDS)
            elif splat.lower() == 'mortal+':
                available_backgrounds.extend(SORCERER_BACKGROUNDS)
            
            # Sort and remove duplicates
            available_backgrounds = sorted(set(available_backgrounds))
            
            table.add_row("|yBackgrounds:|n", "", "", "", "")
            for stat in available_backgrounds:
                current = int(character.get_stat('backgrounds', 'background', stat) or 0)
                if current < 5:
                    next_rating = current + 1
                    try:
                        cost, requires_approval = character.calculate_xp_cost(
                            stat, 
                            next_rating, 
                            category='backgrounds',
                            subcategory='background',
                            current_rating=current
                        )
                        table.add_row(
                            f"  {stat}",
                            str(current),
                            str(next_rating),
                            str(cost),
                            get_affordable_status(cost, current_xp, requires_approval)
                        )
                    except Exception as e:
                        character.msg(f"Error calculating cost for {stat}: {str(e)}")
                        continue

        elif category == "powers":
            # Get character's splat to determine available powers
            splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower()
            
            if splat == 'vampire':
                # Show vampire disciplines
                table.add_row("|yDisciplines:|n", "", "", "", "")
                table.add_row("|rNote: Only Potence, Celerity, Fortitude, Obfuscate, and Auspex can be purchased through +xp/spend.|n", "", "", "", "")
                disciplines = character.db.stats.get('powers', {}).get('discipline', {})
                for discipline, values in disciplines.items():
                    current = values.get('perm', 0)
                    if current < 5:  # Max rating of 5
                        next_rating = current + 1
                        try:
                            cost, requires_approval = character.calculate_xp_cost(
                                discipline, 
                                next_rating, 
                                category='powers',
                                subcategory='discipline',
                                current_rating=current
                            )
                            table.add_row(
                                f"  {discipline}",
                                str(current),
                                str(next_rating),
                                str(cost),
                                get_affordable_status(cost, current_xp, requires_approval)
                            )
                        except Exception as e:
                            character.msg(f"Error calculating cost for {discipline}: {str(e)}")
                            continue
                
                # Show thaumaturgy rituals if character has thaumaturgy
                if any(d.lower() == 'thaumaturgy' for d in disciplines.keys()):
                    table.add_row("", "", "", "", "")
                    table.add_row("|yThaumaturgy Rituals:|n", "", "", "", "")
                    
                    # Query available rituals from database
                    ritual_query = Q(stat_type='thaum_ritual')
                    available_rituals = []
                    
                    for ritual in Stat.objects.filter(ritual_query).order_by('name'):
                        # Check if character meets level requirement
                        thaum_level = disciplines.get('Thaumaturgy', {}).get('perm', 0)
                        if ritual.level and ritual.level <= thaum_level:
                            available_rituals.append(ritual)
                    
                    if available_rituals:
                        for ritual in available_rituals:
                            try:
                                cost, requires_approval = character.calculate_xp_cost(
                                    ritual.name,
                                    1,  # Rituals are either known (1) or not (0)
                                    category='powers',
                                    subcategory='thaum_ritual',
                                    current_rating=0
                                )
                                table.add_row(
                                    f"  {ritual.name} (Level {ritual.level})",
                                    "0",
                                    "1",
                                    str(cost),
                                    get_affordable_status(cost, current_xp, requires_approval)
                                )
                            except Exception as e:
                                character.msg(f"Error calculating cost for {ritual.name}: {str(e)}")
                                continue
                    else:
                        table.add_row("  No rituals available for your level of Thaumaturgy.", "", "", "", "")
                
                # Show necromancy rituals if character has necromancy
                if any(d.lower() == 'necromancy' for d in disciplines.keys()):
                    table.add_row("", "", "", "", "")
                    table.add_row("|yNecromancy Rituals:|n", "", "", "", "")
                    
                    # Query available rituals from database
                    ritual_query = Q(stat_type='necromancy_ritual')
                    available_rituals = []
                    
                    for ritual in Stat.objects.filter(ritual_query).order_by('name'):
                        # Check if character meets level requirement
                        necro_level = disciplines.get('Necromancy', {}).get('perm', 0)
                        if ritual.level and ritual.level <= necro_level:
                            available_rituals.append(ritual)
                    
                    if available_rituals:
                        for ritual in available_rituals:
                            try:
                                cost, requires_approval = character.calculate_xp_cost(
                                    ritual.name,
                                    1,  # Rituals are either known (1) or not (0)
                                    category='powers',
                                    subcategory='necromancy_ritual',
                                    current_rating=0
                                )
                                table.add_row(
                                    f"  {ritual.name} (Level {ritual.level})",
                                    "0",
                                    "1",
                                    str(cost),
                                    get_affordable_status(cost, current_xp, requires_approval)
                                )
                            except Exception as e:
                                character.msg(f"Error calculating cost for {ritual.name}: {str(e)}")
                                continue
                    else:
                        table.add_row("  No rituals available for your level of Necromancy.", "", "", "", "")
            
            elif splat == 'shifter':
                # Get character's shifter attributes
                shifter_type = character.db.stats.get('other', {}).get('shifter_type', {}).get('Shifter Type', {}).get('perm', '')
                breed = character.db.stats.get('other', {}).get('shifter_type', {}).get('Breed', {}).get('perm', '')
                auspice = character.db.stats.get('other', {}).get('shifter_type', {}).get('Auspice', {}).get('perm', '')
                tribe = character.db.stats.get('other', {}).get('shifter_type', {}).get('Tribe', {}).get('perm', '')
                aspect = character.db.stats.get('other', {}).get('shifter_type', {}).get('Aspect', {}).get('perm', '')

                # Show current gifts
                table.add_row("|yCurrent Gifts:|n", "", "", "", "")
                gifts = character.db.stats.get('powers', {}).get('gift', {})
                for gift, values in gifts.items():
                    current = values.get('perm', 0)
                    if current < 5:  # Max rating of 5
                        next_rating = current + 1
                        try:
                            cost, requires_approval = character.calculate_xp_cost(
                                gift, 
                                next_rating, 
                                category='powers',
                                subcategory='gift',
                                current_rating=current
                            )
                            table.add_row(
                                f"  {gift}",
                                str(current),
                                str(next_rating),
                                str(cost),
                                get_affordable_status(cost, current_xp, requires_approval)
                            )
                        except Exception as e:
                            character.msg(f"Error calculating cost for {gift}: {str(e)}")
                            continue
                
                # Get available rank 1 gifts from the database
                table.add_row("", "", "", "", "")
                table.add_row("|yAvailable Rank 1 Gifts:|n", "", "", "", "")
                
                # Query gifts from database
                gift_query = Q(stat_type='gift')
                if shifter_type:
                    # Use exact string matching for shifter_type
                    gift_query &= Q(shifter_type__isnull=False) & Q(shifter_type__contains=shifter_type)
                
                available_gifts = []
                
                for gift in Stat.objects.filter(gift_query).order_by('name'):
                    # Skip gifts the character already has
                    if gift.name in gifts:
                        continue
                        
                    # Check if gift matches character's attributes
                    matches = False
                    
                    # Check shifter type
                    if gift.shifter_type:
                        try:
                            # Handle both string and list formats
                            if isinstance(gift.shifter_type, str):
                                gift_types = [gift.shifter_type]
                            else:
                                gift_types = gift.shifter_type
                                
                            if shifter_type in gift_types:
                                matches = True
                        except (ValueError, TypeError):
                            continue
                    
                    # Check breed if not already matched
                    if not matches and gift.breed:
                        try:
                            # Handle both string and list formats
                            if isinstance(gift.breed, str):
                                gift_breeds = [gift.breed]
                            else:
                                gift_breeds = gift.breed
                                
                            if breed in gift_breeds:
                                matches = True
                        except (ValueError, TypeError):
                            continue
                    
                    # Check auspice if not already matched
                    if not matches and gift.auspice:
                        try:
                            # Handle both string and list formats
                            if isinstance(gift.auspice, str):
                                gift_auspices = [gift.auspice]
                            else:
                                gift_auspices = gift.auspice
                                
                            if auspice in gift_auspices:
                                matches = True
                        except (ValueError, TypeError):
                            continue
                    
                    # Check tribe if not already matched
                    if not matches and gift.tribe:
                        try:
                            # Handle both string and list formats
                            if isinstance(gift.tribe, str):
                                gift_tribes = [gift.tribe]
                            else:
                                gift_tribes = gift.tribe
                                
                            if tribe in gift_tribes:
                                matches = True
                        except (ValueError, TypeError):
                            continue
                    
                    if matches:
                        available_gifts.append(gift)
                
                if available_gifts:
                    for gift in available_gifts:
                        try:
                            cost, requires_approval = character.calculate_xp_cost(
                                gift.name,
                                1,
                                category='powers',
                                subcategory='gift',
                                current_rating=0
                            )
                            # Add source info if available
                            source = f" ({gift.source})" if gift.source else ""
                            table.add_row(
                                f"  {gift.name}{source}",
                                "0",
                                "1",
                                str(cost),
                                get_affordable_status(cost, current_xp, requires_approval)
                            )
                        except Exception as e:
                            character.msg(f"Error calculating cost for {gift.name}: {str(e)}")
                            continue
                else:
                    table.add_row("  No rank 1 gifts available for your character.", "", "", "", "")
                
                # Show rites
                table.add_row("", "", "", "", "")
                table.add_row("|yRites:|n", "", "", "", "")
                
                # Query rites from database
                rite_query = Q(stat_type='rite')
                available_rites = []
                
                for rite in Stat.objects.filter(rite_query).order_by('name'):
                    # Skip rites the character already has
                    if rite.name in character.db.stats.get('powers', {}).get('rite', {}):
                        continue
                        
                    # Check if rite matches character's attributes
                    matches = False
                    
                    # Check shifter type
                    if rite.shifter_type:
                        if isinstance(rite.shifter_type, list):
                            if shifter_type in rite.shifter_type:
                                matches = True
                        elif rite.shifter_type == shifter_type:
                            matches = True
                    
                    # Check tribe if not already matched
                    if not matches and rite.tribe:
                        if isinstance(rite.tribe, list):
                            if tribe in rite.tribe:
                                matches = True
                        elif rite.tribe == tribe:
                            matches = True
                    
                    if matches:
                        available_rites.append(rite)
                
                if available_rites:
                    for rite in available_rites:
                        try:
                            cost, requires_approval = character.calculate_xp_cost(
                                rite.name,
                                1,
                                category='powers',
                                subcategory='rite',
                                current_rating=0
                            )
                            # Add level info if available
                            level = f" (Level {rite.level})" if hasattr(rite, 'level') and rite.level else ""
                            table.add_row(
                                f"  {rite.name}{level}",
                                "0",
                                "1",
                                str(cost),
                                get_affordable_status(cost, current_xp, requires_approval)
                            )
                        except Exception as e:
                            character.msg(f"Error calculating cost for {rite.name}: {str(e)}")
                            continue
                else:
                    table.add_row("  No rites available for your character.", "", "", "", "")
            
            elif splat == 'mage':
                # Show mage spheres
                table.add_row("|ySpheres:|n", "", "", "", "")
                spheres = character.db.stats.get('powers', {}).get('sphere', {})
                for sphere, values in spheres.items():
                    current = values.get('perm', 0)
                    if current < 5:
                        next_rating = current + 1
                        try:
                            cost, requires_approval = character.calculate_xp_cost(
                                sphere, 
                                next_rating, 
                                category='powers',
                                subcategory='sphere',
                                current_rating=current
                            )
                            table.add_row(
                                f"  {sphere}",
                                str(current),
                                str(next_rating),
                                str(cost),
                                get_affordable_status(cost, current_xp, requires_approval)
                            )
                        except Exception as e:
                            character.msg(f"Error calculating cost for {sphere}: {str(e)}")
                            continue
            
            elif splat == 'changeling':
                # Show changeling arts
                table.add_row("|yArts:|n", "", "", "", "")
                arts = character.db.stats.get('powers', {}).get('art', {})
                for art, values in arts.items():
                    current = values.get('perm', 0)
                    if current < 5:
                        next_rating = current + 1
                        try:
                            cost, requires_approval = character.calculate_xp_cost(
                                art, 
                                next_rating, 
                                category='powers',
                                subcategory='art',
                                current_rating=current
                            )
                            table.add_row(
                                f"  {art}",
                                str(current),
                                str(next_rating),
                                str(cost),
                                get_affordable_status(cost, current_xp, requires_approval)
                            )
                        except Exception as e:
                            character.msg(f"Error calculating cost for {art}: {str(e)}")
                            continue
                
                # Show changeling realms
                table.add_row("", "", "", "", "")
                table.add_row("|yRealms:|n", "", "", "", "")
                realms = character.db.stats.get('powers', {}).get('realm', {})
                for realm, values in realms.items():
                    current = values.get('perm', 0)
                    if current < 5:
                        next_rating = current + 1
                        try:
                            cost, requires_approval = character.calculate_xp_cost(
                                realm, 
                                next_rating, 
                                category='powers',
                                subcategory='realm',
                                current_rating=current
                            )
                            table.add_row(
                                f"  {realm}",
                                str(current),
                                str(next_rating),
                                str(cost),
                                get_affordable_status(cost, current_xp, requires_approval)
                            )
                        except Exception as e:
                            character.msg(f"Error calculating cost for {realm}: {str(e)}")
                            continue
            
            elif splat == 'possessed':
                # Show possessed blessings
                table.add_row("|yBlessings:|n", "", "", "", "")
                blessings = character.db.stats.get('powers', {}).get('blessing', {})
                for blessing, values in blessings.items():
                    current = values.get('perm', 0)
                    if current < 5:
                        next_rating = current + 1
                        try:
                            cost, requires_approval = character.calculate_xp_cost(
                                blessing, 
                                next_rating, 
                                category='powers',
                                subcategory='blessing',
                                current_rating=current
                            )
                            table.add_row(
                                f"  {blessing}",
                                str(current),
                                str(next_rating),
                                str(cost),
                                get_affordable_status(cost, current_xp, requires_approval)
                            )
                        except Exception as e:
                            character.msg(f"Error calculating cost for {blessing}: {str(e)}")
                            continue
                
                # Show possessed charms
                table.add_row("", "", "", "", "")
                table.add_row("|yCharms:|n", "", "", "", "")
                charms = character.db.stats.get('powers', {}).get('charm', {})
                for charm, values in charms.items():
                    current = values.get('perm', 0)
                    if current < 5:
                        next_rating = current + 1
                        try:
                            cost, requires_approval = character.calculate_xp_cost(
                                charm, 
                                next_rating, 
                                category='powers',
                                subcategory='charm',
                                current_rating=current
                            )
                            table.add_row(
                                f"  {charm}",
                                str(current),
                                str(next_rating),
                                str(cost),
                                get_affordable_status(cost, current_xp, requires_approval)
                            )
                        except Exception as e:
                            character.msg(f"Error calculating cost for {charm}: {str(e)}")
                            continue
            
            elif splat == 'mortal+':
                # Get character's mortal+ type
                mortalplus_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
                
                if mortalplus_type == 'Sorcerer':
                    # Show sorcery paths
                    table.add_row("|ySorcery Paths:|n", "", "", "", "")
                    sorcery = character.db.stats.get('powers', {}).get('sorcery', {})
                    for path, values in sorcery.items():
                        current = values.get('perm', 0)
                        if current < 5:
                            next_rating = current + 1
                            try:
                                cost, requires_approval = character.calculate_xp_cost(
                                    path, 
                                    next_rating, 
                                    category='powers',
                                    subcategory='sorcery',
                                    current_rating=current
                                )
                                table.add_row(
                                    f"  {path}",
                                    str(current),
                                    str(next_rating),
                                    str(cost),
                                    get_affordable_status(cost, current_xp, requires_approval)
                                )
                            except Exception as e:
                                character.msg(f"Error calculating cost for {path}: {str(e)}")
                                continue
                    
                    # Show sorcery rituals
                    table.add_row("", "", "", "", "")
                    table.add_row("|ySorcery Rituals:|n", "", "", "", "")
                    
                    # Query available rituals from database
                    ritual_query = Q(stat_type='hedge_ritual')
                    available_rituals = []
                    
                    for ritual in Stat.objects.filter(ritual_query).order_by('name'):
                        # Skip rituals the character already has
                        if ritual.name in character.db.stats.get('powers', {}).get('hedge_ritual', {}):
                            continue
                        
                        available_rituals.append(ritual)
                    
                    if available_rituals:
                        for ritual in available_rituals:
                            try:
                                cost, requires_approval = character.calculate_xp_cost(
                                    ritual.name,
                                    1,
                                    category='powers',
                                    subcategory='hedge_ritual',
                                    current_rating=0
                                )
                                # Add level info if available
                                level = f" (Level {ritual.level})" if hasattr(ritual, 'level') and ritual.level else ""
                                table.add_row(
                                    f"  {ritual.name}{level}",
                                    "0",
                                    "1",
                                    str(cost),
                                    get_affordable_status(cost, current_xp, requires_approval)
                                )
                            except Exception as e:
                                character.msg(f"Error calculating cost for {ritual.name}: {str(e)}")
                                continue
                    else:
                        table.add_row("  No rituals available for your character.", "", "", "", "")
                
                elif mortalplus_type == 'Psychic':
                    # Show numina
                    table.add_row("|yNumina:|n", "", "", "", "")
                    numina = character.db.stats.get('powers', {}).get('numina', {})
                    for power, values in numina.items():
                        current = values.get('perm', 0)
                        if current < 5:
                            next_rating = current + 1
                            try:
                                cost, requires_approval = character.calculate_xp_cost(
                                    power, 
                                    next_rating, 
                                    category='powers',
                                    subcategory='numina',
                                    current_rating=current
                                )
                                table.add_row(
                                    f"  {power}",
                                    str(current),
                                    str(next_rating),
                                    str(cost),
                                    get_affordable_status(cost, current_xp, requires_approval)
                                )
                            except Exception as e:
                                character.msg(f"Error calculating cost for {power}: {str(e)}")
                                continue
                
                elif mortalplus_type == 'Kinain':
                    # Show arts and realms like changelings
                    table.add_row("|yArts:|n", "", "", "", "")
                    arts = character.db.stats.get('powers', {}).get('art', {})
                    for art, values in arts.items():
                        current = values.get('perm', 0)
                        if current < 3:  # Kinain are limited to 3 dots
                            next_rating = current + 1
                            try:
                                cost, requires_approval = character.calculate_xp_cost(
                                    art, 
                                    next_rating, 
                                    category='powers',
                                    subcategory='art',
                                    current_rating=current
                                )
                                table.add_row(
                                    f"  {art}",
                                    str(current),
                                    str(next_rating),
                                    str(cost),
                                    get_affordable_status(cost, current_xp, requires_approval)
                                )
                            except Exception as e:
                                character.msg(f"Error calculating cost for {art}: {str(e)}")
                                continue
                    
                    # Show realms
                    table.add_row("", "", "", "", "")
                    table.add_row("|yRealms:|n", "", "", "", "")
                    realms = character.db.stats.get('powers', {}).get('realm', {})
                    for realm, values in realms.items():
                        current = values.get('perm', 0)
                        if current < 3:  # Kinain are limited to 3 dots
                            next_rating = current + 1
                            try:
                                cost, requires_approval = character.calculate_xp_cost(
                                    realm, 
                                    next_rating, 
                                    category='powers',
                                    subcategory='realm',
                                    current_rating=current
                                )
                                table.add_row(
                                    f"  {realm}",
                                    str(current),
                                    str(next_rating),
                                    str(cost),
                                    get_affordable_status(cost, current_xp, requires_approval)
                                )
                            except Exception as e:
                                character.msg(f"Error calculating cost for {realm}: {str(e)}")
                                continue
                
                elif mortalplus_type == 'Ghoul':
                    # Show disciplines like vampires but with lower max
                    table.add_row("|yDisciplines:|n", "", "", "", "")
                    disciplines = character.db.stats.get('powers', {}).get('discipline', {})
                    for discipline, values in disciplines.items():
                        current = values.get('perm', 0)
                        if current < 3:  # Ghouls are limited to 3 dots
                            next_rating = current + 1
                            try:
                                cost, requires_approval = character.calculate_xp_cost(
                                    discipline, 
                                    next_rating, 
                                    category='powers',
                                    subcategory='discipline',
                                    current_rating=current
                                )
                                table.add_row(
                                    f"  {discipline}",
                                    str(current),
                                    str(next_rating),
                                    str(cost),
                                    get_affordable_status(cost, current_xp, requires_approval)
                                )
                            except Exception as e:
                                character.msg(f"Error calculating cost for {discipline}: {str(e)}")
                                continue
            else:
                table.add_row("No powers available for your character type.", "", "", "", "")

        elif category == "pools":
            # Get character's splat to determine available pools
            splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower()
            
            # Only show pools that can be purchased with XP
            purchasable_pools = ['Willpower']  # Willpower is universal
            
            # Add splat-specific purchasable pools
            if splat == 'shifter':
                purchasable_pools.extend(['Rage', 'Gnosis'])
            elif splat == 'mage':
                purchasable_pools.append('Arete')
            elif splat == 'changeling':
                purchasable_pools.append('Glamour')
            
            # Sort pools
            purchasable_pools = sorted(set(purchasable_pools))
            
            table.add_row("|yPools:|n", "", "", "", "")
            for stat in purchasable_pools:
                # Determine the correct category and subcategory for the pool
                if stat in ['Willpower', 'Rage', 'Gnosis', 'Glamour']:
                    category_name = 'pools'
                    subcategory = 'dual'
                elif stat == 'Arete':
                    category_name = 'pools'
                    subcategory = 'advantage'
                else:
                    continue  # Skip any non-purchasable pools
                
                # Get current value
                current = int(character.get_stat(category_name, subcategory, stat) or 0)
                
                # Determine max rating based on pool type
                if stat in ['Willpower', 'Rage', 'Gnosis', 'Glamour']:
                    max_rating = 10
                elif stat == 'Arete':
                    max_rating = 10
                else:
                    max_rating = 10  # Default max rating
                
                if current < max_rating:
                    next_rating = current + 1
                    try:
                        cost, requires_approval = character.calculate_xp_cost(
                            stat, 
                            next_rating, 
                            category=category_name,
                            subcategory=subcategory,
                            current_rating=current
                        )
                        table.add_row(
                            f"  {stat}",
                            str(current),
                            str(next_rating),
                            str(cost),
                            get_affordable_status(cost, current_xp, requires_approval)
                        )
                    except Exception as e:
                        character.msg(f"Error calculating cost for {stat}: {str(e)}")
                        continue

            # Add note about non-purchasable pools
            table.add_row("", "", "", "", "")
            table.add_row("|rNote: Other pools like Blood, Path/Humanity, Banality, Quintessence,|n", "", "", "", "")
            table.add_row("|rParadox, Resonance, and Renown cannot be purchased with XP.|n", "", "", "", "")

        # Send the formatted output with header and footer
        footer = f"|b{'-' * total_width}|n"
        character.msg(f"{header}{table}\n{footer}")

    def _display_all_costs(self, character):
        """Display an overview of all categories"""
        total_width = 78
        title = " Available Character Advancement Options "
        title_len = len(title)
        dash_count = (total_width - title_len) // 2
        
        header = f"|b{'-' * dash_count}|y{title}|n|b{'-' * (total_width - dash_count - title_len)}|n\n"
        
        # Create centered category list
        msg = header
        msg += "|yCategories:|n\n"
        msg += "  |w+costs/attributes|n  - Physical, Social, and Mental Attributes\n"
        msg += "  |w+costs/abilities|n   - Talents, Skills, and Knowledges\n"
        msg += "  |w+costs/backgrounds|n - Available Backgrounds\n"
        msg += "  |w+costs/powers|n      - Supernatural Powers\n"
        msg += "  |w+costs/pools|n       - Rage, Gnosis, Glamour, Arete, WP, etc.\n"

        # Add disciplines option for vampires
        if character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower() == 'vampire':
            msg += "  |w+costs/disciplines|n - Disciplines and Combo Disciplines\n"

        msg += "\n|yUsage:|n\n"
        msg += "  Use the switches above to view detailed costs for each category.\n"
        msg += f"|b{'-' * total_width}|n"
        
        character.msg(msg) 