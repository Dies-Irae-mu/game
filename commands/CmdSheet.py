from evennia.commands.default.muxcommand import MuxCommand
from world.wod20th.models import Stat
from evennia.utils.ansi import ANSIString
from world.wod20th.utils.damage import format_damage, format_status, format_damage_stacked
from world.wod20th.utils.formatting import format_stat, header, footer, divider

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
        
        identity_stats = Stat.objects.filter(category='identity')

        string = header(f"Character Sheet for:|n {character.get_display_name(self.caller)}")
        
        bio = []
        for stat in identity_stats:
            if stat.can_access(character, 'view') or not stat.lock_string:
                bio.append(format_stat(stat.name, character.get_stat(stat.category, stat.stat_type, stat.name), default="", width=38))


        bio.append(format_stat("Splat", splat, default="", width=38))

        string += header("Identity", width=78, color="|y")
        bio1 = bio[:len(bio)//2]
        bio2 = bio[len(bio)//2:]
        for b1, b2 in zip(bio1, bio2):
            string += f"{b1} {b2}\n"

        if len(bio) % 2:
            string += f"{bio[-1]}\n"

        string += header("Attributes", width=78, color="|y")
        string += " " + divider("Physical", width=25, fillchar=" ") + " "
        string += divider("Social", width=25, fillchar=" ") + " "
        string += divider("Mental", width=25, fillchar=" ") + "\n"

        string += format_stat("Strength", character.get_stat('attributes', 'physical', 'Strength'), default=1, tempvalue=character.get_stat('attributes', 'physical', 'Strength', temp=True)) + " "
        string += format_stat("Charisma", character.get_stat('attributes', 'social', 'Charisma'), default=1, tempvalue=character.get_stat('attributes', 'social', 'Charisma', temp=True)) + " "
        string += format_stat("Perception", character.get_stat('attributes', 'mental', 'Perception'), default=1, tempvalue=character.get_stat('attributes', 'mental', 'Perception', temp=True)) + "\n"
        string += format_stat("Dexterity", character.get_stat('attributes', 'physical', 'Dexterity'), default=1, tempvalue=character.get_stat('attributes', 'physical', 'Dexterity', temp=True)) + " "
        string += format_stat("Manipulation", character.get_stat('attributes', 'social', 'Manipulation'), default=1, tempvalue=character.get_stat('attributes', 'social', 'Manipulation', temp=True)) + " "
        string += format_stat("Intelligence", character.get_stat('attributes', 'mental', 'Intelligence'), default=1, tempvalue=character.get_stat('attributes', 'mental', 'Intelligence', temp=True)) + "\n"
        string += format_stat("Stamina", character.get_stat('attributes', 'physical', 'Stamina'), default=1, tempvalue=character.get_stat('attributes', 'physical', 'Stamina', temp=True)) + " "
        string += format_stat("Appearance", character.get_stat('attributes', 'social', 'Appearance'), default=1, tempvalue=character.get_stat('attributes', 'social', 'Appearance', temp=True)) + " "
        string += format_stat("Wits", character.get_stat('attributes', 'mental', 'Wits'), default=1, tempvalue=character.get_stat('attributes', 'mental', 'Wits', temp=True)) + "\n"

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

        formatted_talents = []
        for talent in talents:
            formatted_talents.append(format_stat(talent.name, character.get_stat(talent.category, talent.stat_type, talent.name), default=0, tempvalue=character.get_stat(talent.category, talent.stat_type, talent.name, temp=True)))
            # if there are any specialties add them too
            if character.db.specialties and talent.name in character.db.specialties:
                for specialty in character.db.specialties[talent.name]:
                    formatted_talents.append(format_stat(f"`{specialty}", 1))

        formatted_skills = []
        for skill in skills:
            formatted_skills.append(format_stat(skill.name, character.get_stat(skill.category, skill.stat_type, skill.name), default=0, tempvalue=character.get_stat(skill.category, skill.stat_type, skill.name, temp=True)))
            # if there are any specialties add them too
            if character.db.specialties and skill.name in character.db.specialties:
                for specialty in character.db.specialties[skill.name]:
                    formatted_skills.append(format_stat(f"`{specialty}", 1))

        formatted_knowledges = []
        for knowledge in knowledges:
            formatted_knowledges.append(format_stat(knowledge.name, character.get_stat(knowledge.category, knowledge.stat_type, knowledge.name), default=0, tempvalue=character.get_stat(knowledge.category, knowledge.stat_type, knowledge.name, temp=True)))
            # if there are any specialties add them too
            if character.db.specialties and knowledge.name in character.db.specialties:
                for specialty in character.db.specialties[knowledge.name]:
                    formatted_knowledges.append(format_stat(f"`{specialty}", 1))

        max_len = max(len(formatted_talents), len(formatted_skills), len(formatted_knowledges))
        while len(formatted_talents) < max_len:
            formatted_talents.append(" " * 25)
        while len(formatted_skills) < max_len:
            formatted_skills.append(" " * 25)
        while len(formatted_knowledges) < max_len:
            formatted_knowledges.append(" " * 25)

        for talent, skill, knowledge in zip(formatted_talents, formatted_skills, formatted_knowledges):
            string += f"{talent} {skill} {knowledge}\n"

        if character.locks.check_lockstring(character, "view: is_splat(Vampire)"):
            if not character.db.stats.get('backgrounds'):
                backgrounds = []
            else:
                backgrounds = [format_stat(background, character.get_stat('backgrounds', 'background', background), default=0, tempvalue=character.get_stat('backgrounds', 'background', background, temp=True)) for background in character.db.stats.get('backgrounds', {}).get('background', {}).keys()]

            if not character.db.stats.get('powers'):
                disciplines = []
            else:
                disciplines = [format_stat(discipline, character.get_stat('powers', 'discipline', discipline), default=0, tempvalue=character.get_stat('powers', 'discipline', discipline, temp=True)) for discipline in character.db.stats.get('powers', {}).get('discipline', {}).keys()]

            virtues = Stat.objects.filter(category='virtues')
            virtues = [format_stat(virtue.name, character.get_stat(virtue.category, virtue.stat_type, virtue.name)) for virtue in virtues if character.get_stat(virtue.category, virtue.stat_type, virtue.name)]

            string += header("Advantages", width=78, color="|y")

            if character.db.splat == "Vampire":
                string += divider("Disciplines", width=25, fillchar=" ") + " "
                string += divider("Backgrounds", width=25, fillchar=" ") + " "
                string += divider("Virtues", width=25, fillchar=" ") + "\n"

                max_len = max(len(disciplines), len(backgrounds), len(virtues))
                while len(disciplines) < max_len:
                    disciplines.append(" " * 25)
                while len(backgrounds) < max_len:
                    backgrounds.append(" " * 25)
                while len(virtues) < max_len:
                    virtues.append(" " * 25)

                for discipline, background, virtue in zip(disciplines, backgrounds, virtues):
                    string += f"{discipline} {background} {virtue}\n"

        string += header("Other", width=78, color="|y")
        string += divider("Merits", width=25, fillchar=" " ) + " "
        string += divider("Pools", width=25, fillchar=" ") + " " 
        string += divider("Health & Status", width=25, fillchar=" ") + "\n"

        merits = []
        for category, merits_dict in character.db.stats.get('merits', {}).items():
            for merit, values in merits_dict.items():
                merits.append(format_stat(merit, values['perm']))

        flaws = []
        for category, flaws_dict in character.db.stats.get('flaws', {}).items():
            for flaw, values in flaws_dict.items():
                flaws.append(format_stat(flaw, values['perm']))
        
        if flaws:
            merits.append(" " * 25)
            merits.append(divider("Flaws", width=25))
            merits.extend(flaws)


        health = format_damage_stacked(character)

        pools = Stat.objects.filter(category='pools')
        pools = [format_stat(pool.name, character.get_stat(pool.category, pool.stat_type, pool.name), default=0, tempvalue=character.get_stat(pool.category, pool.stat_type, pool.name, temp=True)) for pool in pools]

        max_len = max(len(merits), len(pools), len(health))
        while len(merits) < max_len:
            merits.append(" " * 25)
        while len(pools) < max_len:
            pools.append(" " * 25)
        while len(health) < max_len:
            health.append(" " * 25)

        for merit, pool, health in zip(merits, pools, health):
            string += f"{merit} {pool} {health}\n"

        if not character.db.approved:
            string += footer()
            string += header("Unapproved Character", width=78, color="|y")
        string += footer()

        self.caller.msg(string)
