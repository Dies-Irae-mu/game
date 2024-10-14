from evennia.commands.default.muxcommand import MuxCommand
from world.wod20th.models import Stat, SHIFTER_IDENTITY_STATS, SHIFTER_RENOWN, CLAN, MAGE_FACTION, MAGE_SPHERES, \
    TRADITION, TRADITION_SUBFACTION, CONVENTION, METHODOLOGIES, NEPHANDI_FACTION, SEEMING, KITH, SEELIE_LEGACIES, \
    UNSEELIE_LEGACIES, ARTS, REALMS, calculate_willpower, calculate_road
from evennia.utils.ansi import ANSIString
from world.wod20th.utils.damage import format_damage, format_status, format_damage_stacked
from world.wod20th.utils.formatting import format_stat, header, footer, divider
from itertools import zip_longest

class CmdSheet(MuxCommand):
    """
    Show a sheet of the character.
    """
    key = "sheet"
    aliases = ["sh"]
    help_category = "Chargen & Character Info"

    def func(self):
        name = self.args.strip()
        if not name:
            name = self.caller.key
        character = self.caller.search(name)
        
        try:
            splat = character.get_stat('other', 'splat', 'Splat')
        except AttributeError:
            self.caller.msg(f"|rCharacter '{name}' not found.|n")
            return
        self.caller.msg(f"|rSplat: {splat}|n")
        if not splat:
            splat = "Mortal"
        if not self.caller.check_permstring("builders"):
            if self.caller != character:
                self.caller.msg(f"|rYou can't see the sheet of {character.key}.|n")
                return

        if not character:
            self.caller.msg(f"|rCharacter '{name}' not found.|n")
            return

        if self.caller != character:
            if not character.access(self.caller, 'edit'):
                self.caller.msg(f"|rYou can't see the sheet of {character.key}.|n")
                return

        stats = character.db.stats
        if not stats:
            character.db.stats = {}
        
        string = header(f"Character Sheet for:|n {character.get_display_name(self.caller)}")
        
        string += header("Identity", width=78, color="|y")
        
        common_stats = ['Full Name', 'Date of Birth', 'Concept']
        splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        
        if splat.lower() == 'changeling':
            common_stats += ['Seelie Legacy', 'Unseelie Legacy']
        else:
            common_stats += ['Nature', 'Demeanor']

        if splat.lower() == 'vampire':
            splat_specific_stats = ['Clan', 'Date of Embrace', 'Generation', 'Sire', 'Enlightenment']
        elif splat.lower() == 'shifter':
            shifter_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
            splat_specific_stats = ['Type'] + SHIFTER_IDENTITY_STATS.get(shifter_type, [])
        elif splat.lower() == 'mage':
            mage_faction = character.db.stats.get('identity', {}).get('lineage', {}).get('Mage Faction', {}).get('perm', '')
            splat_specific_stats = ['Essence', 'Mage Faction']
            
            if mage_faction.lower() == 'traditions':
                traditions = character.db.stats.get('identity', {}).get('lineage', {}).get('Tradition', {}).get('perm', '')
                splat_specific_stats.extend(['Tradition'])
                if traditions:
                        splat_specific_stats.append('Traditions Subfaction')
            elif mage_faction.lower() == 'technocracy':
                splat_specific_stats.extend(['Convention', 'Methodology'])
            elif mage_faction.lower() == 'nephandi':
                splat_specific_stats.append('Nephandi Faction')
        elif splat.lower() == 'changeling':
            splat_specific_stats = ['Kith', 'Seeming', 'House']
        else:
            splat_specific_stats = []

        all_stats = common_stats + splat_specific_stats + ['Splat']
        
        def format_stat_with_dots(stat, value, width=38):
            # Special case for 'Traditions Subfaction'
            display_stat = 'Subfaction' if stat == 'Traditions Subfaction' else stat
            
            stat_str = f" {display_stat}"
            value_str = f"{value}"
            dots = "." * (width - len(stat_str) - len(value_str) - 1)
            return f"{stat_str}{dots}{value_str}"

        for i in range(0, len(all_stats), 2):
            left_stat = all_stats[i]
            right_stat = all_stats[i+1] if i+1 < len(all_stats) else None

            left_value = character.db.stats.get('identity', {}).get('personal', {}).get(left_stat, {}).get('perm', '')
            if not left_value:
                left_value = character.db.stats.get('identity', {}).get('lineage', {}).get(left_stat, {}).get('perm', '')
            if not left_value:
                left_value = character.db.stats.get('identity', {}).get('other', {}).get(left_stat, {}).get('perm', '')
            if not left_value and left_stat == 'Splat':
                left_value = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
            # New code for Nature and Demeanor
            if left_stat == 'Nature':
                left_value = character.db.stats.get('archetype', {}).get('personal', {}).get('Nature Archetype', {}).get('perm', '')
            elif left_stat == 'Demeanor':
                left_value = character.db.stats.get('archetype', {}).get('personal', {}).get('Demeanor Archetype', {}).get('perm', '')

            left_formatted = format_stat_with_dots(left_stat, left_value)

            if right_stat:
                right_value = character.db.stats.get('identity', {}).get('personal', {}).get(right_stat, {}).get('perm', '')
                if not right_value:
                    right_value = character.db.stats.get('identity', {}).get('lineage', {}).get(right_stat, {}).get('perm', '')
                if not right_value:
                    right_value = character.db.stats.get('identity', {}).get('other', {}).get(right_stat, {}).get('perm', '')
                if not right_value and right_stat == 'Splat':
                    right_value = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
                # New code for Nature and Demeanor
                if right_stat == 'Nature':
                    right_value = character.db.stats.get('archetype', {}).get('personal', {}).get('Nature Archetype', {}).get('perm', '')
                elif right_stat == 'Demeanor':
                    right_value = character.db.stats.get('archetype', {}).get('personal', {}).get('Demeanor Archetype', {}).get('perm', '')
                
                right_formatted = format_stat_with_dots(right_stat, right_value)
                string += f"{left_formatted}  {right_formatted}\n"
            else:
                string += f"{left_formatted}\n"

        string += header("Attributes", width=78, color="|y")
        string += " " + divider("Physical", width=25, fillchar=" ") + " "
        string += divider("Social", width=25, fillchar=" ") + " "
        string += divider("Mental", width=25, fillchar=" ") + "\n"

        # Function to add padding to social and mental attributes
        def pad_attribute(attr):
            return " " * 1 + attr.ljust(22)

        string += format_stat("Strength", character.get_stat('attributes', 'physical', 'Strength'), default=1, tempvalue=character.get_stat('attributes', 'physical', 'Strength', temp=True)) + " "
        string += format_stat("Charisma", character.get_stat('attributes', 'social', 'Charisma'), default=1, tempvalue=character.get_stat('attributes', 'social', 'Charisma', temp=True)) + " "
        string += pad_attribute(format_stat("Perception", character.get_stat('attributes', 'mental', 'Perception'), default=1, tempvalue=character.get_stat('attributes', 'mental', 'Perception', temp=True))) + "\n"
        string += format_stat("Dexterity", character.get_stat('attributes', 'physical', 'Dexterity'), default=1, tempvalue=character.get_stat('attributes', 'physical', 'Dexterity', temp=True)) + " "
        string += format_stat("Manipulation", character.get_stat('attributes', 'social', 'Manipulation'), default=1, tempvalue=character.get_stat('attributes', 'social', 'Manipulation', temp=True)) + " "
        string += pad_attribute(format_stat("Intelligence", character.get_stat('attributes', 'mental', 'Intelligence'), default=1, tempvalue=character.get_stat('attributes', 'mental', 'Intelligence', temp=True))) + "\n"
        string += format_stat("Stamina", character.get_stat('attributes', 'physical', 'Stamina'), default=1, tempvalue=character.get_stat('attributes', 'physical', 'Stamina', temp=True)) + " "
        string += format_stat("Appearance", character.get_stat('attributes', 'social', 'Appearance'), default=1, tempvalue=character.get_stat('attributes', 'social', 'Appearance', temp=True)) + " "
        string += pad_attribute(format_stat("Wits", character.get_stat('attributes', 'mental', 'Wits'), default=1, tempvalue=character.get_stat('attributes', 'mental', 'Wits', temp=True))) + "\n"

        talents = Stat.objects.filter(category='abilities', stat_type='talent')
        talents = [talent for talent in talents if not talent.lock_string or character.check_permstring(talent.lock_string)]
        
        skills = Stat.objects.filter(category='abilities', stat_type='skill')
        skills = [skill for skill in skills if not skill.lock_string or character.check_permstring(skill.lock_string)]
        knowledges = Stat.objects.filter(category='abilities', stat_type='knowledge')
        knowledges = [knowledge for knowledge in knowledges if not knowledge.lock_string or character.check_permstring(knowledge.lock_string)]

        string += header("Abilities", width=78, color="|y")
        string += " " + divider("Talents", width=25, fillchar=" ") + " "
        string += divider("Skills", width=25, fillchar=" ") + " "
        string += divider("Knowledges", width=25, fillchar=" ") + "\n"

        # Function to format abilities with padding for skills and knowledges
        def format_ability(ability, category):
            formatted = format_stat(ability.name, character.get_stat(ability.category, ability.stat_type, ability.name), default=0)
            if category in ['knowledge']:
                return " " * 1 + formatted.ljust(22)
            return formatted.ljust(25)

        formatted_talents = [format_ability(talent, 'talent') for talent in talents]
        formatted_skills = [format_ability(skill, 'skill') for skill in skills]
        formatted_knowledges = [format_ability(knowledge, 'knowledge') for knowledge in knowledges]

        # Add specialties
        ability_lists = [
            (formatted_talents, talents, 'talent'),
            (formatted_skills, skills, 'skill'),
            (formatted_knowledges, knowledges, 'knowledge')
        ]

        for formatted_list, ability_list, ability_type in ability_lists:
            for ability in ability_list:
                if character.db.specialties and ability.name in character.db.specialties:
                    for specialty in character.db.specialties[ability.name]:
                        formatted_specialty = format_ability(Stat(name=f"`{specialty}"), ability_type)
                        formatted_list.append(formatted_specialty)

        max_len = max(len(formatted_talents), len(formatted_skills), len(formatted_knowledges))
        formatted_talents.extend(["" * 25] * (max_len - len(formatted_talents)))
        formatted_skills.extend(["" * 25] * (max_len - len(formatted_skills)))
        formatted_knowledges.extend(["" * 25] * (max_len - len(formatted_knowledges)))

        for talent, skill, knowledge in zip(formatted_talents, formatted_skills, formatted_knowledges):
            string += f"{talent}{skill}{knowledge}\n"

        string += header("Secondary Abilities", width=78, color="|y")
        string += " " + divider("Talents", width=25, fillchar=" ") + " "
        string += divider("Skills", width=25, fillchar=" ") + " "
        string += divider("Knowledges", width=25, fillchar=" ") + "\n"

        # Function to format abilities with padding for skills and knowledges
        def format_ability(secondary_ability, category):
            value = character.get_stat('secondary_abilities', category, secondary_ability.name)
            formatted = format_stat(secondary_ability.name, value, default=0)
            if category in ['secondary_knowledge']:
                return " " * 1 + formatted.ljust(22)
            return formatted.ljust(25)

        secondary_talents = Stat.objects.filter(category='secondary_abilities', stat_type='secondary_talent')
        secondary_skills = Stat.objects.filter(category='secondary_abilities', stat_type='secondary_skill')
        secondary_knowledges = Stat.objects.filter(category='secondary_abilities', stat_type='secondary_knowledge')

        formatted_secondary_talents = [format_ability(talent, 'secondary_talent') for talent in secondary_talents]
        formatted_secondary_skills = [format_ability(skill, 'secondary_skill') for skill in secondary_skills]
        formatted_secondary_knowledges = [format_ability(knowledge, 'secondary_knowledge') for knowledge in secondary_knowledges]

        max_len = max(len(formatted_secondary_talents), len(formatted_secondary_skills), len(formatted_secondary_knowledges))
        formatted_secondary_talents.extend(["" * 25] * (max_len - len(formatted_secondary_talents)))
        formatted_secondary_skills.extend(["" * 25] * (max_len - len(formatted_secondary_skills)))
        formatted_secondary_knowledges.extend(["" * 25] * (max_len - len(formatted_secondary_knowledges)))

        for secondary_talent, secondary_skill, secondary_knowledge in zip(formatted_secondary_talents, formatted_secondary_skills, formatted_secondary_knowledges):
            string += f"{secondary_talent}{secondary_skill}{secondary_knowledge}\n"

        string += header("Advantages", width=78, color="|y")
        
        powers = []
        advantages = []
        status = []

        # Process powers based on character splat
        character_splat = character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        if character_splat == 'Mage':
            powers.append(divider("Spheres", width=25, color="|b"))
            spheres = ['Correspondence', 'Entropy', 'Forces', 'Life', 'Matter', 'Mind', 'Prime', 'Spirit', 'Time', 'Data', 'Primal Utility', 'Dimensional Science']
            for sphere in spheres:
                sphere_value = character.db.stats.get('powers', {}).get('sphere', {}).get(sphere, {}).get('perm', 0)
                powers.append(format_stat(sphere, sphere_value, default=0, width=25))
        elif character_splat == 'Vampire':
            powers.append(divider("Disciplines", width=25, color="|b"))
            disciplines = character.db.stats.get('powers', {}).get('discipline', {})
            for discipline, values in disciplines.items():
                discipline_value = values.get('perm', 0)
                powers.append(format_stat(discipline, discipline_value, default=0, width=25))
        elif character_splat == 'Changeling':
            powers.append(divider("Arts", width=25, color="|b"))
            arts = character.db.stats.get('powers', {}).get('art', {})
            for art, values in arts.items():
                art_value = values.get('perm', 0)
                powers.append(format_stat(art, art_value, default=0, width=25)) 
            powers.append(divider("Realms", width=25, color="|b"))
            realms = character.db.stats.get('powers', {}).get('realm', {})
            for realm, values in realms.items():
                realm_value = values.get('perm', 0)
                powers.append(format_stat(realm, realm_value, default=0, width=25))
        elif character_splat == 'Shifter':
            powers.append(divider("Gifts", width=25, color="|b"))
            gifts = character.db.stats.get('powers', {}).get('gift', {})
            for gift, values in gifts.items():
                print(f"Raw gift name: {gift}")
                gift_value = values.get('perm', 0)
                formatted_gift = format_stat(gift, gift_value, default=0, width=25)
                print(f"Formatted gift: {formatted_gift}")
                powers.append(formatted_gift)

            # Add Renown for Shifters
            powers.append(divider("Renown", width=25, color="|b"))
            shifter_type = character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
            renown_types = SHIFTER_RENOWN.get(shifter_type, [])
            for renown_type in renown_types:
                    renown_value = character.db.stats.get('advantages', {}).get('renown', {}).get(renown_type, {}).get('perm', 0)
                    powers.append(format_stat(renown_type, renown_value, default=0, width=25))

        # Process backgrounds
        advantages.append(divider("Backgrounds", width=25, color="|b"))
        backgrounds = character.db.stats.get('backgrounds', {}).get('background', {})
        for background, values in backgrounds.items():
            background_value = values.get('perm', 0)
            advantages.append(format_stat(background, background_value, default=0, width=25))

        # Merits & Flaws
        advantages.append(divider("Merits & Flaws", width=25, color="|b"))
        for category, merits_dict in character.db.stats.get('merits', {}).items():
            for merit, values in merits_dict.items():
                advantages.append(format_stat(merit, values['perm'], width=25))
        for category, flaws_dict in character.db.stats.get('flaws', {}).items():
            for flaw, values in flaws_dict.items():
                advantages.append(format_stat(flaw, values['perm'], width=25))

        # Pools
        advantages.append(divider("Pools", width=25, color="|b"))
        valid_pools = ['Willpower']  # Willpower is common to all splats

        if character_splat.lower() == 'vampire':
            valid_pools.extend(['Blood', 'Road'])
            # Add virtues for Vampires
            virtues = character.db.stats.get('virtues', {}).get('moral', {})
            valid_pools.extend(virtues.keys())
        elif character_splat.lower() == 'shifter':
            valid_pools.extend(['Rage', 'Gnosis'])
        elif character_splat.lower() == 'mage':
            valid_pools.extend(['Arete', 'Quintessence', 'Paradox'])
        elif character_splat.lower() == 'changeling':
            valid_pools.extend(['Glamour', 'Banality'])
        elif character_splat.lower() == 'mortal':
            # Add virtues for Mortals
            virtues = character.db.stats.get('virtues', {}).get('moral', {})
            valid_pools.extend(virtues.keys())

        for pool in valid_pools:
            if pool == 'Arete':
                value = character.db.stats.get('other', {}).get('advantage', {}).get('Arete', {}).get('perm', 0)
                advantages.append(format_stat(pool, value, width=25))
            elif pool == 'Paradox':
                temp = character.db.stats.get('pools', {}).get('dual', {}).get('Paradox', {}).get('temp', 0)
                advantages.append(format_stat(pool, temp, width=25, default=0))
            elif pool in ['Conscience', 'Self-Control', 'Courage']:  # These are the virtue names
                value = character.db.stats.get('virtues', {}).get('moral', {}).get(pool, {}).get('perm', 0)
                advantages.append(format_stat(pool, value, width=25))
            else:
                perm = character.db.stats.get('pools', {}).get('dual', {}).get(pool, {}).get('perm', 0)
                temp = character.db.stats.get('pools', {}).get('dual', {}).get(pool, {}).get('temp', perm)
                value = f"{perm}({temp})" if perm != temp else perm
                advantages.append(format_stat(pool, value, width=25))

        # Process health
        status.append(divider("Health & Status", width=25, color="|b"))
        health_status = format_damage_stacked(character)
        status.extend([(" " * 3 + line).ljust(25).strip() for line in health_status])

        # Ensure all columns have the same number of rows
        max_len = max(len(powers), len(advantages), len(status))
        powers.extend([""] * (max_len - len(powers)))
        advantages.extend([""] * (max_len - len(advantages)))
        status.extend([""] * (max_len - len(status)))

        # Combine powers, advantages, and status
        for power, advantage, status_line in zip(powers, advantages, status):
            string += f"{power.strip().ljust(25)} {advantage.strip().ljust(25)} {status_line.strip().ljust(25)}\n"

        if not character.db.approved:
            string += footer()
            string += header("Unapproved Character", width=78, color="|y")
        string += footer()

        self.caller.msg(string)

        # Display Virtues
        string += header("Virtues", width=78, color="|y")
        virtues = character.db.stats.get('virtues', {}).get('moral', {})
        enlightenment = character.get_stat('identity', 'personal', 'Enlightenment', temp=False)
        
        path_virtues = {
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
        
        relevant_virtues = path_virtues.get(enlightenment, ['Conscience', 'Self-Control', 'Courage'])
        
        for virtue in relevant_virtues:
            value = virtues.get(virtue, {}).get('perm', 0)
            string += format_stat(virtue, value, width=25)
        string += "\n"

        # Display Pools
        string += header("Pools", width=78, color="|y")
        pools = character.db.stats.get('pools', {})
        
        # Calculate and display Willpower
        willpower = calculate_willpower(character)
        string += format_stat("Willpower", willpower, width=25, tempvalue=pools.get('dual', {}).get('Willpower', {}).get('temp'))

        # Display other pools
        for pool, value in pools.items():
            if pool != 'Willpower':  # We've already displayed Willpower
                if isinstance(value, dict) and 'perm' in value:
                    string += format_stat(pool, value['perm'], width=25, tempvalue=value.get('temp'))
                else:
                    string += format_stat(pool, value, width=25)
        
        # Display Road/Humanity
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        road_value = calculate_road(character)
        if splat.lower() == 'mortal':
            string += format_stat("Humanity", road_value, width=25)
        elif splat.lower() == 'vampire':
            enlightenment = character.get_stat('identity', 'personal', 'Enlightenment', temp=False)
            string += format_stat(f"Road of {enlightenment}", road_value, width=25)
        
        string += "\n"
