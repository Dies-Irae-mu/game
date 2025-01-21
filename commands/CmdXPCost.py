from evennia import default_cmds
from evennia.utils.evtable import EvTable
from decimal import Decimal
from commands.CmdCheck import CmdCheck
from world.wod20th.models import Stat
from django.db.models import Q

class CmdXPCost(default_cmds.MuxCommand):
    """
    View costs for character advancement.
    
    Usage:
      +costs              - Show all available purchases
      +costs/attributes   - Show attribute costs
      +costs/abilities    - Show ability costs
      +costs/backgrounds  - Show background costs
      +costs/powers      - Show power/gift costs
      +costs/pools       - Show pool costs
      +costs/disciplines - Show discipline and combo discipline costs
    """
    
    key = "+costs"
    aliases = ["costs"]
    locks = "cmd:all()"
    help_category = "Character"

    def func(self):
        """Execute command"""
        if not self.switches:
            # Show overview of all categories
            self._display_all_costs(self.caller)
            return
            
        switch = self.switches[0].lower()
        if switch in ["attributes", "abilities", "backgrounds", "powers", "pools", "disciplines"]:
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
                    current = int(character.get_stat('attributes', subcat, stat) or 0)
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
            backgrounds = ['Resources', 'Contacts', 'Allies', 'Backup', 'Herd', 'Library',
                          'Kinfolk', 'Spirit Heritage', 'Ancestors']
            
            table.add_row("|yBackgrounds:|n", "", "", "", "")
            for stat in backgrounds:
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
            splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '').lower()
            
            if splat == 'vampire':
                # Show vampire disciplines
                table.add_row("|yDisciplines:|n", "", "", "", "")
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
            
            elif splat == 'shifter':
                # Get character's shifter attributes
                shifter_type = character.db.stats.get('other', {}).get('shifter_type', {}).get('Shifter Type', {}).get('perm', '')
                breed = character.db.stats.get('other', {}).get('shifter_type', {}).get('Breed', {}).get('perm', '')
                auspice = character.db.stats.get('other', {}).get('shifter_type', {}).get('Auspice', {}).get('perm', '')
                tribe = character.db.stats.get('other', {}).get('shifter_type', {}).get('Tribe', {}).get('perm', '')
                aspect = character.db.stats.get('other', {}).get('shifter_type', {}).get('Aspect', {}).get('perm', '')

                # Get all rank 1 gifts from the database
                available_gifts = []
                for gift_name, gift_data in Stat.objects.filter(stat_type='gift', values__contains=[1]).items():
                    # Check if gift matches any of character's attributes
                    matches = False
                    
                    # Check shifter type
                    if 'shifter_type' in gift_data:
                        if isinstance(gift_data['shifter_type'], list):
                            if shifter_type in gift_data['shifter_type']:
                                matches = True
                        elif gift_data['shifter_type'] == shifter_type:
                            matches = True
                    
                    # Check breed if not already matched
                    if not matches and 'breed' in gift_data:
                        if isinstance(gift_data['breed'], list):
                            if breed in gift_data['breed']:
                                matches = True
                        elif gift_data['breed'] == breed:
                            matches = True
                    
                    # Check auspice if not already matched
                    if not matches and 'auspice' in gift_data:
                        if isinstance(gift_data['auspice'], list):
                            if auspice in gift_data['auspice']:
                                matches = True
                        elif gift_data['auspice'] == auspice:
                            matches = True
                    
                    # Check tribe if not already matched
                    if not matches and 'tribe' in gift_data:
                        if isinstance(gift_data['tribe'], list):
                            if tribe in gift_data['tribe']:
                                matches = True
                        elif gift_data['tribe'] == tribe:
                            matches = True
                    
                    # Check aspect if not already matched
                    if not matches and 'aspect' in gift_data:
                        if isinstance(gift_data['aspect'], list):
                            if aspect in gift_data['aspect']:
                                matches = True
                        elif gift_data['aspect'] == aspect:
                            matches = True
                    
                    if matches:
                        available_gifts.append((gift_name, gift_data))

                # Sort gifts alphabetically
                available_gifts.sort(key=lambda x: x[0])

                # Display available gifts
                table.add_row("|yAvailable Rank 1 Gifts:|n", "", "", "", "")
                if available_gifts:
                    for gift_name, gift_data in available_gifts:
                        current = int(character.get_stat('powers', 'gift', gift_name) or 0)
                        if current < 1:  # Only show if not already learned
                            try:
                                cost, requires_approval = character.calculate_xp_cost(
                                    gift_name,
                                    1,
                                    category='powers',
                                    subcategory='gift',
                                    current_rating=0
                                )
                                # Add source info if available
                                source = f" ({gift_data.get('source', '')})" if 'source' in gift_data else ""
                                table.add_row(
                                    f"  {gift_name}{source}",
                                    "0",
                                    "1",
                                    str(cost),
                                    get_affordable_status(cost, current_xp, requires_approval)
                                )
                            except Exception as e:
                                character.msg(f"Error calculating cost for {gift_name}: {str(e)}")
                                continue
                else:
                    table.add_row("  No rank 1 gifts available for your character.", "", "", "", "")
            
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
            else:
                table.add_row("No powers available for your character type.", "", "", "", "")

        elif category == "pools":
            pools = ['Willpower', 'Rage', 'Gnosis']
            
            table.add_row("|yPools:|n", "", "", "", "")
            for stat in pools:
                current = int(character.get_stat('pools', 'dual', stat) or 0)
                if current < 10:  # Pools usually go to 10
                    next_rating = current + 1
                    try:
                        cost, requires_approval = character.calculate_xp_cost(
                            stat, 
                            next_rating, 
                            category='pools',
                            subcategory='dual',
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