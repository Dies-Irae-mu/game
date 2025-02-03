from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.search import search_object
from world.wod20th.models import POSSESSED_TYPES, Stat, SHIFTER_IDENTITY_STATS, SHIFTER_RENOWN, CLAN, AFFILIATION, MAGE_SPHERES, \
    TRADITION, TRADITION_SUBFACTION, CONVENTION, METHODOLOGIES, NEPHANDI_FACTION, SEEMING, KITH, SEELIE_LEGACIES, \
    UNSEELIE_LEGACIES, ARTS, REALMS, calculate_willpower, calculate_road, MORTALPLUS_TYPES, MORTALPLUS_POWERS, \
    MORTALPLUS_POOLS
from evennia.utils.ansi import ANSIString
from world.wod20th.utils.damage import format_damage, format_status, format_damage_stacked, calculate_total_health_levels
from world.wod20th.utils.formatting import format_stat, header, footer, divider
from itertools import zip_longest
from typeclasses.characters import Character

# Define virtue sets for different paths
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

class CmdSheet(MuxCommand):
    """
    Show a sheet of the character.
    """
    key = "sheet"
    aliases = ["sh"]
    help_category = "Chargen & Character Info"

    def __init__(self):
        """Initialize command."""
        super().__init__()
        self.advantages_list = []
        self.pools_list = []
        self.powers_list = []
        self.virtues_list = []

    def initialize_ghoul_stats(self, character):
        """Initialize or ensure proper stats for Ghoul characters."""
        # Set Blood pool to 3 for Ghouls
        character.set_stat('pools', 'dual', 'Blood', 3, temp=False)
        character.set_stat('pools', 'dual', 'Blood', 3, temp=True)

    def set_stat_both(self, character, category, stat_type, stat_name, value):
        """Set both permanent and temporary values for a stat."""
        character.set_stat(category, stat_type, stat_name, value, temp=False)
        character.set_stat(category, stat_type, stat_name, value, temp=True)

    def initialize_mortalplus_stats(self, character, mortalplus_type):
        """Initialize stats specific to Mortal+ types."""
        if not mortalplus_type:
            return []  # Return empty list instead of undefined powers
            
        powers = []  # Initialize powers list
        
        # Set the type properly
        self.set_stat_both(character, 'identity', 'lineage', 'Mortal+ Type', mortalplus_type)
            
        # Initialize powers category if it doesn't exist
        if 'powers' not in character.db.stats:
            character.db.stats['powers'] = {}
            
        # Initialize pools
        if mortalplus_type in MORTALPLUS_POOLS:
            for pool_name, pool_data in MORTALPLUS_POOLS[mortalplus_type].items():
                self.set_stat_both(character, 'pools', 'dual', pool_name, pool_data['default'])

        mortalplus_type = character.get_stat('identity', 'lineage', 'Mortal+ Type', temp=False)
        if not mortalplus_type:
            return powers

        # Add powers section based on type
        if mortalplus_type in MORTALPLUS_TYPES:
            power_types = MORTALPLUS_TYPES[mortalplus_type]
            for power_type in power_types:
                power_type_lower = power_type.lower()
                powers.append(divider(power_type, width=38, color="|b"))
                
                # Get the powers from the correct location in the stats dictionary
                powers_dict = character.db.stats.get('powers', {}).get(power_type_lower, {})
                if powers_dict:
                    for power, values in sorted(powers_dict.items()):
                        power_value = values.get('perm', 0)
                        powers.append(format_stat(power, power_value, default=0, width=38))
                else:
                    powers.append(" None".ljust(38))

            # Special handling for Sorcerer hedge rituals
            if mortalplus_type == 'Sorcerer':
                powers.append(divider("Hedge Rituals", width=38, color="|b"))
                hedge_rituals = character.db.stats.get('powers', {}).get('hedge_ritual', {})
                if hedge_rituals:
                    for ritual, values in sorted(hedge_rituals.items()):
                        ritual_value = values.get('perm', 0)
                        powers.append(format_stat(ritual, ritual_value, default=0, width=38))
                else:
                    powers.append(" None".ljust(38))

        return powers

    def initialize_possessed_stats(self, character):
        """Initialize or ensure proper stats for Possessed characters."""
        possessed_type = character.get_stat('identity', 'lineage', 'Possessed Type', temp=False)
        
        # Get base pools based on type
        if possessed_type == 'Kami':
            base_gnosis = 1
            base_willpower = 4
            base_rage = 0
        elif possessed_type == 'Fomori':
            base_gnosis = 0
            base_willpower = 3
            base_rage = 0
        else:
            return  # Invalid type

        # Check for Berserker blessing
        blessings = character.db.stats.get('powers', {}).get('blessing', {})
        has_berserker = any(name.lower() == 'berserker' and values.get('perm', 0) > 0 
                           for name, values in blessings.items())
        if has_berserker:
            base_rage = 5

        # Check for Spirit Ties blessing and adjust Gnosis
        spirit_ties_value = next((values.get('perm', 0) for name, values in blessings.items() 
                                if name.lower() == 'spirit ties'), 0)
        if spirit_ties_value > 0:
            base_gnosis = min(5, base_gnosis + spirit_ties_value)  # Cap at 5

        # Set the final pool values
        self.set_stat_both(character, 'pools', 'dual', 'Gnosis', base_gnosis)
        self.set_stat_both(character, 'pools', 'dual', 'Willpower', base_willpower)
        self.set_stat_both(character, 'pools', 'dual', 'Rage', base_rage)

    def calculate_health_bonuses(self, character):
        """Calculate bonus health levels for a character."""
        # Use the centralized health calculation from damage.py
        return calculate_total_health_levels(character)

    def func(self):
        """Execute the command."""
        # Initialize lists at the start of the function
        self.pools_list = [divider("Pools", width=25, fillchar=" ")]
        self.virtues_list = [divider("Virtues", width=25, fillchar=" ")]
        self.status_list = [divider("Health & Status", width=25, fillchar=" ")]
        powers = []

        name = self.args.strip()
        if not name:
            name = self.caller.key

        # First try direct name match (with quiet=True to suppress error message)
        chars = self.caller.search(name, global_search=True,
                                 typeclass='typeclasses.characters.Character',
                                 quiet=True)

        # Handle if search returns a list
        character = chars[0] if isinstance(chars, list) else chars

        # If no direct match, try alias
        if not character:
            character = Character.get_by_alias(name.lower())

        if character:
            # If not builder, verify character is in same location
            if not (self.caller.check_permstring("builders") or self.caller.check_permstring("storyteller")):
                if character != self.caller and character not in self.caller.location.contents:
                    self.caller.msg(f"You can't see {name} here.")
                    return
        else:
            self.caller.msg(f"Character '{name}' not found.")
            return

        # Modify permission check - allow builders/admins to view any sheet
        if not (self.caller.check_permstring("builders") or self.caller.check_permstring("storyteller")):
            if self.caller != character:
                self.caller.msg(f"|rYou can't see the sheet of {character.key}.|n")
                return

        # Check if character has stats and splat initialized
        if not character.db.stats or not character.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm'):
            self.caller.msg("|rYou must set a splat to initialize your sheet. Use +selfstat splat=<Splat> or ask staff to set it.|n")
            return

        try:
            splat = character.get_stat('other', 'splat', 'Splat')
        except AttributeError:
            self.caller.msg("|rError accessing character stats. Please contact staff.|n")
            return

        if not splat:
            splat = "Mortal"

        # Start building the character sheet
        string = header(f"Character Sheet for:|n {character.get_display_name(self.caller)}")

        # Add Identity section
        string += self.format_identity_section(character, splat)

        # Add Attributes section
        string += self.format_attributes_section(character)

        # Add Abilities section
        string += self.format_abilities_section(character)

        # Add Secondary Abilities section
        string += self.format_secondary_abilities_section(character)

        # Process powers and advantages in two columns
        string += header("Advantages", width=78, color="|y")
        
        powers = []
        left_column = []

        # Process powers based on character splat (right column)
        character_splat = character.get_stat('other', 'splat', 'Splat', temp=False)

        # Process pools based on splat type
        if character_splat == 'Mortal+':
            powers = self.process_mortalplus_powers(character, powers)
            self.process_mortalplus_pools(character)
        elif character_splat == 'Mage':
            powers = self.process_mage_powers(character, powers)
            self.process_mage_pools_and_virtues(character)
        elif character_splat == 'Vampire':
            powers = self.process_vampire_powers(character, powers)
            # Get generation for blood pool calculation
            generation = character.get_stat('identity', 'lineage', 'Generation', temp=False) or '13th'
            max_blood = calculate_blood_pool(generation)
            self.pools_list.extend([
                format_stat('Blood Pool', f"{format_pool_value(character, 'Blood')}/{max_blood}", width=25),
                format_stat('Willpower', format_pool_value(character, 'Willpower'), width=25)
            ])
        elif character_splat == 'Changeling':
            powers = self.process_changeling_powers(character, powers)
            self.process_changeling_pools_and_virtues(character)
        elif character_splat == 'Possessed':
            powers = self.process_possessed_powers(character, powers)
            self.process_possessed_pools(character)
        elif character_splat == 'Shifter':
            powers = self.process_shifter_powers(character, powers)
            self.process_shifter_pools_and_virtues(character)
        elif character_splat == 'Companion':
            powers = self.process_companion_powers(character, powers)
            # Add Essence and Willpower pools
            self.pools_list.extend([
                format_stat('Essence', format_pool_value(character, 'Essence'), width=25),
                format_stat('Willpower', format_pool_value(character, 'Willpower'), width=25)
            ])
            # Add Rage pool if character has Ferocity
            rage_value = character.get_stat('pools', 'dual', 'Rage', temp=False)
            if rage_value and rage_value > 0:
                self.pools_list.append(format_stat('Rage', format_pool_value(character, 'Rage'), width=25))
            # Add Paradox pool if character has Feast of Nettles
            paradox_value = character.get_stat('pools', 'dual', 'Paradox', temp=False)
            if paradox_value and paradox_value > 0:
                self.pools_list.append(format_stat('Paradox', format_pool_value(character, 'Paradox'), width=25))
        else:  # Mortal
            # Calculate base Willpower from Courage
            courage = character.get_stat('virtues', 'moral', 'Courage', temp=False) or 0
            base_willpower = max(1, courage)  # Minimum of 1, otherwise equal to Courage
            
            # Set Willpower if not already set
            if not character.get_stat('pools', 'dual', 'Willpower', temp=False):
                character.set_stat('pools', 'dual', 'Willpower', base_willpower, temp=False)
                character.set_stat('pools', 'dual', 'Willpower', base_willpower, temp=True)
            
            self.pools_list.append(format_stat('Willpower', format_pool_value(character, 'Willpower'), width=25))

        # Build left column (backgrounds + merits & flaws)
        left_column.append(divider("Backgrounds", width=38, color="|b"))
        char_backgrounds = character.db.stats.get('backgrounds', {}).get('background', {})
        for background, values in sorted(char_backgrounds.items()):
            background_value = values.get('perm', 0)
            left_column.append(format_stat(background, background_value, width=38))

        # Add a blank line between sections
        left_column.append(" " * 38)

        # Separate Merits section with consistent dot width
        left_column.append(divider("Merits", width=38, color="|b"))
        merits = character.db.stats.get('merits', {})
        for merit_type, merit_dict in sorted(merits.items()):
            for merit, values in sorted(merit_dict.items()):
                merit_value = values.get('perm', 0)
                left_column.append(format_stat(merit, merit_value, width=38))

        # Add a blank line between Merits and Flaws
        left_column.append(" " * 38)

        # Separate Flaws section with consistent dot width
        left_column.append(divider("Flaws", width=38, color="|b"))
        flaws = character.db.stats.get('flaws', {})
        for flaw_type, flaw_dict in sorted(flaws.items()):
            for flaw, values in sorted(flaw_dict.items()):
                flaw_value = values.get('perm', 0)
                left_column.append(format_stat(flaw, flaw_value, width=38))

        # Ensure both columns have the same number of rows
        max_len = max(len(powers), len(left_column))
        powers.extend([""] * (max_len - len(powers)))
        left_column.extend([""] * (max_len - len(left_column)))

        # Combine columns with new widths (38+38 = 76 total width with 2 spaces between)
        for left, power in zip(left_column, powers):
            string += f"{left.strip().ljust(38)}  {power.strip().ljust(38)}\n"

        # Display Pools, Virtues & Status
        string += header("Pools, Virtues & Status", width=78, color="|y")

        # Calculate health bonuses before getting health status
        bonus_health = self.calculate_health_bonuses(character)

        # Add health status to status_list without extra padding
        health_status = format_damage_stacked(character)
        self.status_list.extend(health_status)

        # Handle virtues
        if character_splat.lower() not in ['shifter', 'mage', 'changeling']:
            # Handle other splat virtues
            virtues = character.db.stats.get('virtues', {}).get('moral', {})
            
            # Only Vampires, Mortals, and Mortal+ should have these virtues
            if character_splat.lower() in ['vampire', 'mortal', 'mortal+']:
                path = character.get_stat('identity', 'personal', 'Enlightenment')
                path_virtues = PATH_VIRTUES.get(path, ['Conscience', 'Self-Control', 'Courage'])
                
                # Add Road/Path rating first for vampires
                if character_splat.lower() == 'vampire':
                    road_value = character.get_stat('pools', 'moral', 'Road') or 0
                    dots = "." * (19 - len("Road"))
                    self.virtues_list.append(f" Road{dots}{road_value}".ljust(25))
                
                # Display virtues in order
                for virtue in path_virtues:
                    virtue_value = virtues.get(virtue, {}).get('perm', 0)
                    # For non-Humanity paths, show 0 for Conviction/Instinct if not set
                    if path != 'Humanity' and virtue in ['Conviction', 'Instinct']:
                        virtue_value = virtue_value or 0
                    dots = "." * (19 - len(virtue))
                    self.virtues_list.append(f" {virtue}{dots}{virtue_value}".ljust(25))

        # Ensure all columns have the same number of rows
        max_len = max(len(self.pools_list), len(self.virtues_list), len(self.status_list))
        self.pools_list.extend(["".ljust(25)] * (max_len - len(self.pools_list)))
        self.virtues_list.extend(["".ljust(25)] * (max_len - len(self.virtues_list)))
        self.status_list.extend(["".ljust(25)] * (max_len - len(self.status_list)))

        # Display the pools, virtues and status in columns with adjusted spacing
        for pool, virtue, status in zip(self.pools_list, self.virtues_list, self.status_list):
            string += f"{pool:<25}  {virtue:>25}  {status}\n"

        # Check approval status and add it at the end
        if character.db.approved:
            string += header("Approved Character", width=78, fillchar="-")
        else:
            string += header("Unapproved Character", width=78, fillchar="-")

        # Send the complete sheet to the caller
        self.caller.msg(string)

    def process_vampire_powers(self, character, powers):
        """Process powers section for Vampire characters."""
        # Vampire-specific powers section
        powers.append(divider("Disciplines", width=38, color="|b"))
        disciplines = character.db.stats.get('powers', {}).get('discipline', {})
        for discipline, values in sorted(disciplines.items()):
            discipline_value = values.get('perm', 0)
            powers.append(format_stat(discipline, discipline_value, default=0, width=38))

        # Add Banality if it exists
        banality = character.get_stat('pools', 'dual', 'Banality', temp=False)
        if banality is not None:
            self.pools_list.append(format_stat('Banality', format_pool_value(character, 'Banality'), width=25))
            
        return powers

    def process_changeling_powers(self, character, powers):
        """Process powers section for Changeling characters."""
        # Get character's kith and phyla
        kith = character.get_stat('identity', 'lineage', 'Kith', temp=False)
        phyla = character.get_stat('identity', 'lineage', 'Phyla', temp=False)
        
        # Process powers section
        if kith == 'Inanimae':
            # Add Slivers section for all Inanimae
            powers.append(divider("Slivers", width=38, color="|b"))
            slivers = character.db.stats.get('powers', {}).get('sliver', {})
            if slivers:
                for sliver, values in sorted(slivers.items()):
                    sliver_value = values.get('perm', 0)
                    powers.append(format_stat(sliver, sliver_value, default=0, width=38))
            else:
                powers.append(" None".ljust(38))
        
            # Add Arts section ONLY for Mannikins
            if phyla == 'Mannikins':
                powers.append(divider("Arts", width=38, color="|b"))
                arts = character.db.stats.get('powers', {}).get('art', {})
                if arts:
                    for art, values in sorted(arts.items()):
                        art_value = values.get('perm', 0)
                        powers.append(format_stat(art, art_value, default=0, width=38))
                else:
                    powers.append(" None".ljust(38))
        else:
            # Regular Changeling powers
            powers.append(divider("Arts", width=38, color="|b"))
            arts = character.db.stats.get('powers', {}).get('art', {})
            for art, values in sorted(arts.items()):
                art_value = values.get('perm', 0)
                powers.append(format_stat(art, art_value, default=0, width=38))
            
            powers.append(divider("Realms", width=38, color="|b"))
            realms = character.db.stats.get('powers', {}).get('realm', {})
            for realm, values in sorted(realms.items()):
                realm_value = values.get('perm', 0)
                powers.append(format_stat(realm, realm_value, default=0, width=38))
        return powers

    def process_changeling_pools_and_virtues(self, character):
        """Process pools and virtues section for Changeling characters."""
        # Add standard pools
        self.pools_list.extend([
            format_stat('Glamour', format_pool_value(character, 'Glamour'), width=25),
            format_stat('Willpower', format_pool_value(character, 'Willpower'), width=25),
            format_stat('Banality', format_pool_value(character, 'Banality'), width=25)  # Always show Banality for Changelings
        ])
        
        # Get Nightmare and Willpower Imbalance from pools.other
        nightmare = character.db.stats.get('pools', {}).get('other', {}).get('Nightmare', {}).get('temp', 0)
        if not nightmare:
            nightmare = character.db.stats.get('pools', {}).get('other', {}).get('Nightmare', {}).get('perm', 0)
        
        willpower_imbalance = character.db.stats.get('pools', {}).get('other', {}).get('Willpower Imbalance', {}).get('temp', 0)
        if not willpower_imbalance:
            willpower_imbalance = character.db.stats.get('pools', {}).get('other', {}).get('Willpower Imbalance', {}).get('perm', 0)
        
        # Add Nightmare and Willpower Imbalance to virtues section
        self.virtues_list.append(format_stat('Nightmare', str(nightmare), width=25))
        self.virtues_list.append(format_stat('Willpower Imbalance', str(willpower_imbalance), width=25))

    def process_shifter_powers(self, character, powers):
        """Process powers section for Shifter characters."""
        # Add Gifts section
        powers.append(divider("Gifts", width=38, color="|b"))
        gifts = character.db.stats.get('powers', {}).get('gift', {})
        for gift, values in sorted(gifts.items()):
            gift_value = values.get('perm', 0)
            powers.append(format_stat(gift, gift_value, default=0, width=38))
        
        # Add Rites section
        powers.append(divider("Rites", width=38, color="|b"))
        rites = character.db.stats.get('powers', {}).get('rite', {})
        for rite, values in sorted(rites.items()):
            rite_value = values.get('perm', 0)
            powers.append(format_stat(rite, rite_value, default=0, width=38))
        return powers

    def process_shifter_pools_and_virtues(self, character):
        """Process pools and virtues section for Shifter characters."""
        shifter_type = character.get_stat('identity', 'lineage', 'Type')
        
        # Handle Ananasi differently
        if shifter_type == 'Ananasi':
            self.pools_list.extend([
                format_stat('Blood', format_pool_value(character, 'Blood'), width=25),
                format_stat('Gnosis', format_pool_value(character, 'Gnosis'), width=25),
                format_stat('Willpower', format_pool_value(character, 'Willpower'), width=25)
            ])
        else:
            # Standard shifter pools
            self.pools_list.extend([
                format_stat('Rage', format_pool_value(character, 'Rage'), width=25),
                format_stat('Gnosis', format_pool_value(character, 'Gnosis'), width=25),
                format_stat('Willpower', format_pool_value(character, 'Willpower'), width=25)
            ])
        
        # Add Banality if it exists
        banality = character.get_stat('pools', 'dual', 'Banality', temp=False)
        if banality is not None:
            self.pools_list.append(format_stat('Banality', format_pool_value(character, 'Banality'), width=25))
        
        # Handle Renown based on shifter type
        shifter_type = character.get_stat('identity', 'lineage', 'Type')
        if shifter_type in SHIFTER_RENOWN:
            for renown in SHIFTER_RENOWN[shifter_type]:
                renown_value = character.get_stat('advantages', 'renown', renown, temp=False) or 0
                dots = "." * (19 - len(renown))
                self.virtues_list.append(f" {renown}{dots}{renown_value}".ljust(25))
        else:
            # Default to Garou renown if type not found or not set
            default_renown = ['Glory', 'Honor', 'Wisdom']
            for renown in default_renown:
                renown_value = character.get_stat('advantages', 'renown', renown, temp=False) or 0
                dots = "." * (19 - len(renown))
                self.virtues_list.append(f" {renown}{dots}{renown_value}".ljust(25))

    def process_mage_powers(self, character, powers):
        """Process powers section for Mage characters."""
        # Add Spheres section
        powers.append(divider("Spheres", width=38, color="|b"))
        spheres = character.db.stats.get('powers', {}).get('sphere', {})
        for sphere, values in sorted(spheres.items()):
            sphere_value = values.get('perm', 0)
            powers.append(format_stat(sphere, sphere_value, default=0, width=38))
        return powers

    def process_mage_pools_and_virtues(self, character):
        """Process pools and virtues section for Mage characters."""
        # Get Avatar/Genius rating and set Quintessence accordingly
        avatar_value = character.get_stat('backgrounds', 'background', 'Avatar', temp=False) or \
                      character.get_stat('backgrounds', 'background', 'Genius', temp=False) or 0
        
        # Set Quintessence to match Avatar rating
        character.set_stat('pools', 'dual', 'Quintessence', avatar_value, temp=False)
        character.set_stat('pools', 'dual', 'Quintessence', avatar_value, temp=True)

        # Check if character is a Technocrat
        affiliation = character.get_stat('identity', 'lineage', 'Affiliation') or ''
        if affiliation.lower() == 'technocracy':
            # Use Enlightenment for Technocrats
            self.pools_list.extend([
                format_stat('Enlightenment', format_pool_value(character, 'Enlightenment'), width=25),
                format_stat('Quintessence', format_pool_value(character, 'Quintessence'), width=25),
                format_stat('Willpower', format_pool_value(character, 'Willpower'), width=25)
            ])
        else:
            # Use Arete for non-Technocrats
            self.pools_list.extend([
                format_stat('Arete', format_pool_value(character, 'Arete'), width=25),
                format_stat('Quintessence', format_pool_value(character, 'Quintessence'), width=25),
                format_stat('Willpower', format_pool_value(character, 'Willpower'), width=25)
            ])

        # Add Banality if it exists
        banality = character.get_stat('pools', 'dual', 'Banality', temp=False)
        if banality is not None:
            self.pools_list.append(format_stat('Banality', format_pool_value(character, 'Banality'), width=25))

        # Add virtues
        synergy_virtues = ['Dynamic', 'Entropic', 'Static']
        for virtue in synergy_virtues:
            virtue_value = character.get_stat('virtues', 'synergy', virtue, temp=False) or 0
            dots = "." * (19 - len(virtue))
            self.virtues_list.append(f" {virtue}{dots}{virtue_value}".ljust(25))
        
        # Add Resonance
        resonance_value = character.get_stat('pools', 'resonance', 'Resonance', temp=False) or 0
        dots = "." * (19 - len('Resonance'))
        self.virtues_list.append(f" Resonance{dots}{resonance_value}".ljust(25))

    def process_possessed_powers(self, character, powers):
        """Process powers section for Possessed characters."""
        # Add Blessings section
        powers.append(divider("Blessings", width=38, color="|b"))
        blessings = character.db.stats.get('powers', {}).get('blessing', {})
        if blessings:
            for blessing, values in sorted(blessings.items()):
                blessing_value = values.get('perm', 0)
                powers.append(format_stat(blessing, blessing_value, default=0, width=38))
        else:
            powers.append("None")
        
        # Add Gifts section
        powers.append(divider("Gifts", width=38, color="|b"))
        gifts = character.db.stats.get('powers', {}).get('gift', {})
        if gifts:
            for gift, values in sorted(gifts.items()):
                gift_value = values.get('perm', 0)
                powers.append(format_stat(gift, gift_value, default=0, width=38))
        else:
            powers.append("None")
        
        # Add Charms section
        powers.append(divider("Charms", width=38, color="|b"))
        charms = character.db.stats.get('powers', {}).get('charm', {})
        if charms:
            for charm, values in sorted(charms.items()):
                charm_value = values.get('perm', 0)
                powers.append(format_stat(charm, charm_value, default=0, width=38))
        else:
            powers.append("None")
        return powers

    def process_possessed_pools(self, character):
        """Process pools section for Possessed characters."""
        # Initialize pools if not already set
        self.initialize_possessed_stats(character)
        
        # Add pools in order
        self.pools_list.extend([
            format_stat('Willpower', format_pool_value(character, 'Willpower'), width=25),
            format_stat('Gnosis', format_pool_value(character, 'Gnosis'), width=25),
            format_stat('Rage', format_pool_value(character, 'Rage'), width=25)
        ])
        
        # Add Banality if it exists
        banality = character.get_stat('pools', 'dual', 'Banality', temp=False)
        if banality is not None:
            self.pools_list.append(format_stat('Banality', format_pool_value(character, 'Banality'), width=25))

    def process_mortalplus_powers(self, character, powers):
        """Process powers section for Mortal+ characters."""
        mortalplus_type = character.get_stat('identity', 'lineage', 'Mortal+ Type', temp=False)
        if not mortalplus_type:
            return powers

        # Add powers section based on type
        if mortalplus_type in MORTALPLUS_TYPES:
            power_types = MORTALPLUS_TYPES[mortalplus_type]
            for power_type in power_types:
                power_type_lower = power_type.lower()
                powers.append(divider(power_type, width=38, color="|b"))
                # Get the powers from the correct location in the stats dictionary
                powers_dict = character.db.stats.get('powers', {}).get(power_type_lower, {})
                if powers_dict:
                    for power, values in sorted(powers_dict.items()):
                        power_value = values.get('perm', 0)
                        powers.append(format_stat(power, power_value, default=0, width=38))
                else:
                    powers.append(" None".ljust(38))

            # Special handling for Sorcerer hedge rituals
            if mortalplus_type == 'Sorcerer':
                powers.append(divider("Hedge Rituals", width=38, color="|b"))
                hedge_rituals = character.db.stats.get('powers', {}).get('hedge_ritual', {})
                if hedge_rituals:
                    for ritual, values in sorted(hedge_rituals.items()):
                        ritual_value = values.get('perm', 0)
                        powers.append(format_stat(ritual, ritual_value, default=0, width=38))
                else:
                    powers.append(" None".ljust(38))

                # Special handling for Fomori and Kami Blessings
                if power_type == 'Blessing':
                    blessings = character.db.stats.get('powers', {}).get('blessing', {})
                    for blessing, values in sorted(blessings.items()):
                        blessing_value = values.get('perm', 0)
                        powers.append(format_stat(blessing, blessing_value, default=0, width=38))
                
                # Other power type handling
                elif power_type == 'Arts':
                    arts = character.db.stats.get('powers', {}).get('art', {})
                    for art, values in sorted(arts.items()):
                        art_value = values.get('perm', 0)
                        powers.append(format_stat(art, art_value, default=0, width=38))
                elif power_type == 'Realms':
                    realms = character.db.stats.get('powers', {}).get('realm', {})
                    for realm, values in sorted(realms.items()):
                        realm_value = values.get('perm', 0)
                        powers.append(format_stat(realm, realm_value, default=0, width=38))
                else:
                    power_dict = character.db.stats.get(power_type_lower, {})
                    for power, values in sorted(power_dict.items()):
                        power_value = values.get('perm', 0)
                        powers.append(format_stat(power, power_value, default=0, width=38))

        return powers

    def process_mortalplus_pools(self, character):
        """Process pools section for Mortal+ characters."""
        mortalplus_type = character.get_stat('identity', 'lineage', 'Mortal+ Type', temp=False)
        if not mortalplus_type:
            return

        # Add appropriate pools based on type
        if mortalplus_type == 'Ghoul':
            self.initialize_ghoul_stats(character)
            self.pools_list.append(format_stat('Blood', format_pool_value(character, 'Blood'), width=25))
        elif mortalplus_type == 'Kinfolk':
            # Check for Gnosis Merit
            merits = character.db.stats.get('merits', {}).get('merit', {})
            gnosis_merit = next((value.get('perm', 0) for merit, value in merits.items() 
                               if merit.lower() == 'gnosis'), 0)
            if gnosis_merit >= 5:
                gnosis_value = min(3, max(1, gnosis_merit - 4))  # 5->1, 6->2, 7->3
                # Set Gnosis if not already set
                if not character.get_stat('pools', 'dual', 'Gnosis', temp=False):
                    character.set_stat('pools', 'dual', 'Gnosis', gnosis_value, temp=False)
                    character.set_stat('pools', 'dual', 'Gnosis', gnosis_value, temp=True)
                self.pools_list.append(format_stat('Gnosis', format_pool_value(character, 'Gnosis'), width=25))
        elif mortalplus_type == 'Kinain':
            self.pools_list.append(format_stat('Glamour', format_pool_value(character, 'Glamour'), width=25))
        elif mortalplus_type == 'Sorcerer':
            self.pools_list.append(format_stat('Mana', format_pool_value(character, 'Mana'), width=25))
        
        # Add Banality if it exists
        banality = character.get_stat('pools', 'dual', 'Banality', temp=False)
        if banality is not None:
            self.pools_list.append(format_stat('Banality', format_pool_value(character, 'Banality'), width=25))
        
        # Add Willpower for all Mortal+ types
        self.pools_list.append(format_stat('Willpower', format_pool_value(character, 'Willpower'), width=25))

    def get_identity_stats(self, character, splat):
        """Get the list of identity stats to display based on character splat."""
        common_stats = ['Full Name', 'Date of Birth', 'Concept']
        splat_specific_stats = []

        # Add Nature/Demeanor or Seelie/Unseelie Legacy based on splat
        if splat.lower() == 'changeling':
            common_stats.extend(['Seelie Legacy', 'Unseelie Legacy'])
        else:
            common_stats.extend(['Nature', 'Demeanor'])

        # Add splat-specific stats
        if splat.lower() == 'vampire':
            splat_specific_stats = ['Clan', 'Date of Embrace', 'Generation', 'Sire', 'Enlightenment']
        elif splat.lower() == 'shifter':
            shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
            splat_specific_stats = ['Type']
            if shifter_type:
                type_specific_stats = SHIFTER_IDENTITY_STATS.get(shifter_type, [])
                splat_specific_stats.extend(type_specific_stats)
                
                # Add Camp/Lodge for Garou characters based on tribe
                if shifter_type.lower() == 'garou':
                    tribe = character.get_stat('identity', 'lineage', 'Tribe', temp=False) or ''
                    if tribe and tribe.lower() == 'silver fangs':
                        splat_specific_stats.extend(['Lodge', 'Fang House'])
                    elif tribe:
                        # Only add Camp if tribe is set and not Silver Fangs
                        camp = character.get_stat('identity', 'lineage', 'Camp', temp=False)
                        if camp:
                            splat_specific_stats.append('Camp')
        elif splat.lower() == 'mage':
            affiliation = character.get_stat('identity', 'lineage', 'Affiliation', temp=False)
            splat_specific_stats = ['Essence', 'Affiliation', 'Signature', 'Affinity Sphere']

            if affiliation.lower() == 'traditions':
                traditions = character.get_stat('identity', 'lineage', 'Tradition', temp=False)
                splat_specific_stats.extend(['Tradition'])
                if traditions:
                    splat_specific_stats.append('Traditions Subfaction')
            elif affiliation.lower() == 'technocracy':
                splat_specific_stats.extend(['Convention', 'Methodology'])
            elif affiliation.lower() == 'nephandi':
                splat_specific_stats.append('Nephandi Faction')
        elif splat.lower() == 'changeling':
            splat_specific_stats = ['Kith', 'Seeming', 'House']
        elif splat.lower() == 'mortal+':
            mortalplus_type = character.get_stat('identity', 'lineage', 'Mortal+ Type', temp=False)
            splat_specific_stats = ['Mortal+ Type']
            
            # Add type-specific stats
            if mortalplus_type == 'Ghoul':
                splat_specific_stats.extend(['Domitor', 'Clan'])
            elif mortalplus_type == 'Kinfolk':
                splat_specific_stats.extend(['Tribe'])
            elif mortalplus_type == 'Kinain':
                splat_specific_stats.extend(['Kith', 'Seeming'])
            elif mortalplus_type == 'Sorcerer':
                splat_specific_stats.extend(['Affiliation', 'Coven'])
            elif mortalplus_type == 'Faithful':
                splat_specific_stats.extend(['Affiliation', 'Order'])
            elif mortalplus_type == 'Psychic':
                splat_specific_stats.extend(['Affiliation', 'Society'])
        elif splat.lower() == 'companion':
            splat_specific_stats = ['Companion Type', 'Affiliation', 'Motivation']
        elif splat.lower() == 'possessed':
            possessed_type = character.get_stat('identity', 'lineage', 'Possessed Type')
            splat_specific_stats = ['Possessed Type']
            
            # Add type-specific stats
            if possessed_type == 'Fomori':
                splat_specific_stats.extend(['Bane Type'])
            elif possessed_type == 'Kami':
                splat_specific_stats.extend(['Gaian Spirit'])
            
            # Add other Possessed-specific stats
            splat_specific_stats.extend(['Date of Possession', 'Spirit Name'])

        # Combine all stats
        all_stats = []
        # Add common stats first
        for stat in common_stats:
            if stat not in all_stats:
                all_stats.append(stat)

        # Add splat-specific stats
        for stat in splat_specific_stats:
            if stat not in all_stats:
                all_stats.append(stat)

        # Add Phyla for Inanimae after Kith
        if splat.lower() == 'changeling':
            kith = character.get_stat('identity', 'lineage', 'Kith', temp=False)
            if kith == 'Inanimae':
                phyla = (character.get_stat('identity', 'phyla', 'Phyla', temp=False) or 
                        character.get_stat('identity', 'lineage', 'Phyla', temp=False))
                if phyla and 'Kith' in all_stats and 'Phyla' not in all_stats:
                    kith_index = all_stats.index('Kith')
                    all_stats.insert(kith_index + 1, 'Phyla')

        # Add Splat at the end if not already included
        if 'Splat' not in all_stats:
            all_stats.append('Splat')

        return all_stats

    def get_stat_value(self, character, stat):
        """Get the value of a stat from the appropriate location."""
        # Check personal stats first
        value = character.get_stat('identity', 'personal', stat, temp=False)
        
        # For Phyla, check both locations
        if not value and stat == 'Phyla':
            value = (character.get_stat('identity', 'phyla', 'Phyla', temp=False) or 
                    character.get_stat('identity', 'lineage', 'Phyla', temp=False))
        
        # For Legacies, check legacy location
        elif stat in ['Seelie Legacy', 'Unseelie Legacy']:
            value = character.get_stat('identity', 'legacy', stat, temp=False)
        
        # Check lineage stats
        if not value:
            value = character.get_stat('identity', 'lineage', stat, temp=False)
            
        # Special handling for Rank
        if not value and stat == 'Rank':
            value = '0'
            
        # Check other stats
        if not value:
            value = character.get_stat('identity', 'other', stat, temp=False)
            
        # Check splat
        if not value and stat == 'Splat':
            value = character.get_stat('other', 'splat', 'Splat', temp=False)
            
        # Check Nature and Demeanor
        if not value and stat == 'Nature':
            value = (character.get_stat('archetype', 'personal', 'Nature', temp=False) or
                    character.get_stat('archetype', 'personal', 'Nature', temp=True))
        elif not value and stat == 'Demeanor':
            value = (character.get_stat('archetype', 'personal', 'Demeanor', temp=False) or
                    character.get_stat('archetype', 'personal', 'Demeanor', temp=True))
            
        return value

    def format_stat_with_dots(self, stat, value, width=38):
        """Format a stat with dots for display."""
        display_stat = 'Subfaction' if stat == 'Traditions Subfaction' else stat
        display_stat = 'Possessed Type' if stat == 'possessed_type' else display_stat
        stat_str = f" {display_stat}"

        # Handle dictionary values
        if isinstance(value, dict):
            # Handle nested dictionaries (e.g., {'Splat': {'perm': 'Vampire', 'temp': 'Vampire'}})
            if any(isinstance(v, dict) for v in value.values()):
                for key, val in value.items():
                    if isinstance(val, dict) and 'perm' in val:
                        value = val.get('perm', '')
                        break
            else:
                # Handle simple dictionaries (e.g., {'perm': 'Vampire', 'temp': 'Vampire'})
                value = value.get('perm', '')

        # Handle empty/None values
        if value is None or value == '':
            if stat == 'Rank':  # Special case for Rank
                value_str = '0'
            else:
                value_str = ''
        else:
            value_str = str(value)

        # Calculate dots needed for spacing
        dots = "." * (width - len(stat_str) - len(value_str) - 1)
        return f"{stat_str}{dots}{value_str}"

    def format_identity_section(self, character, splat):
        """Format the identity section of the character sheet."""
        string = header("Identity", width=78, color="|y")
        all_stats = self.get_identity_stats(character, splat)

        # Format stats in two columns
        for i in range(0, len(all_stats), 2):
            left_stat = all_stats[i]
            right_stat = all_stats[i+1] if i+1 < len(all_stats) else None

            left_value = self.get_stat_value(character, left_stat)
            left_formatted = self.format_stat_with_dots(left_stat, left_value)

            if right_stat:
                right_value = self.get_stat_value(character, right_stat)
                right_formatted = self.format_stat_with_dots(right_stat, right_value)
                string += f"{left_formatted}  {right_formatted}\n"
            else:
                string += f"{left_formatted}\n"

        return string

    def format_attributes_section(self, character):
        """Format the attributes section of the character sheet."""
        string = header("Attributes", width=78, color="|y")
        string += " " + divider("Physical", width=25, fillchar=" ") + " "
        string += divider("Social", width=25, fillchar=" ") + " "
        string += divider("Mental", width=25, fillchar=" ") + "\n"

        # Format each row of attributes
        rows = [
            (
                ('Strength', 'physical'), 
                ('Charisma', 'social'), 
                ('Perception', 'mental')
            ),
            (
                ('Dexterity', 'physical'), 
                ('Manipulation', 'social'), 
                ('Intelligence', 'mental')
            ),
            (
                ('Stamina', 'physical'), 
                ('Appearance', 'social'), 
                ('Wits', 'mental')
            )
        ]

        # Special handling for Appearance
        zero_appearance_clans = ['nosferatu', 'samedi']
        clan = character.get_stat('identity', 'lineage', 'Clan', temp=False) or ''
        is_zero_appearance_clan = clan.lower() in zero_appearance_clans

        current_form = character.db.current_form
        zero_appearance_forms = ['crinos', 'anthros', 'arthren', 'sokto', 'chatro']
        is_zero_appearance_form = current_form and current_form.lower() in zero_appearance_forms

        for row in rows:
            row_string = ""
            for attr, category in row:
                if attr == 'Appearance' and (is_zero_appearance_clan or is_zero_appearance_form):
                    row_string += format_stat(attr, 0, default=0, tempvalue=0, allow_zero=True)
                else:
                    value = character.get_stat('attributes', category, attr, temp=False)
                    temp_value = character.get_stat('attributes', category, attr, temp=True)
                    row_string += format_stat(attr, value, default=1, tempvalue=temp_value)
                
                # Add padding for mental attributes
                if category == 'mental':
                    row_string = row_string.ljust(len(row_string) + 1)
                else:
                    row_string += " "
            string += row_string + "\n"

        return string

    def format_ability(self, character, ability, category):
        """Format a single ability with appropriate padding."""
        value = character.get_stat('abilities', category, ability.name)
        formatted = format_stat(ability.name, value, default=0)
        if category in ['knowledge']:
            return " " * 1 + formatted.ljust(22)
        return formatted.ljust(25)

    def get_abilities_for_splat(self, character, stat_type):
        """Get abilities for a specific splat and stat type."""
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)
        shifter_type = character.get_stat('identity', 'lineage', 'Type', temp=False)
        clan = character.get_stat('identity', 'lineage', 'Clan', temp=False)

        # Define base abilities for each category
        BASE_ABILITIES = {
            'talent': ['Alertness', 'Athletics', 'Awareness', 'Brawl', 'Empathy', 
                      'Expression', 'Intimidation', 'Leadership', 'Streetwise', 'Subterfuge'],
            'skill': ['Animal Ken', 'Crafts', 'Drive', 'Etiquette', 'Firearms', 
                     'Larceny', 'Melee', 'Performance', 'Stealth', 'Survival', 'Technology'],
            'knowledge': ['Academics', 'Computer', 'Cosmology', 'Enigmas', 'Finance', 'Investigation', 
                        'Law', 'Medicine', 'Occult', 'Politics', 'Science']
        }
        
        # Get base abilities first
        abilities = list(Stat.objects.filter(
            category='abilities',
            stat_type=stat_type,
            name__in=BASE_ABILITIES[stat_type]
        ).order_by('name'))
        
        # Add splat-specific abilities
        if splat == 'Shifter':
            if stat_type == 'talent':
                # Add Primal-Urge for all shifters
                primal_urge = Stat.objects.filter(name='Primal-Urge').first()
                if primal_urge:
                    # Insert Primal-Urge in alphabetical order
                    insert_index = next((i for i, ability in enumerate(abilities) 
                                       if ability.name > 'Primal-Urge'), len(abilities))
                    abilities.insert(insert_index, primal_urge)
                
                # Add Flight ONLY for specific shifter types
                if shifter_type and shifter_type.strip() in ['Corax', 'Camazotz', 'Mokole']:
                    flight = Stat.objects.filter(name='Flight').first()
                    if flight:
                        # Insert Flight in alphabetical order
                        insert_index = next((i for i, ability in enumerate(abilities) 
                                           if ability.name > 'Flight'), len(abilities))
                        abilities.insert(insert_index, flight)
            
            elif stat_type == 'knowledge':
                # Add Rituals for all shifters
                rituals = Stat.objects.filter(name='Rituals').first()
                if rituals:
                    # Insert Rituals in alphabetical order
                    insert_index = next((i for i, ability in enumerate(abilities) 
                                       if ability.name > 'Rituals'), len(abilities))
                    abilities.insert(insert_index, rituals)
        
        # Add Flight for Gargoyle vampires
        elif splat == 'Vampire' and clan and clan.strip() == 'Gargoyle' and stat_type == 'talent':
            flight = Stat.objects.filter(name='Flight').first()
            if flight:
                # Insert Flight in alphabetical order
                insert_index = next((i for i, ability in enumerate(abilities) 
                                   if ability.name > 'Flight'), len(abilities))
                abilities.insert(insert_index, flight)
        
        elif splat == 'Companion' and stat_type == 'special_advantage':
            # Check if the companion has Wings special advantage
            wings_value = character.get_stat('powers', 'special_advantage', 'Wings', temp=False)
            if wings_value > 0:
                # Add Flight ability for winged companions
                flight = Stat.objects.filter(name='Flight').first()
                if flight:
                    # Insert Flight in alphabetical order
                    insert_index = next((i for i, ability in enumerate(abilities) 
                                       if ability.name > 'Flight'), len(abilities))
                    abilities.insert(insert_index, flight)
            
            # Add base Companion ability
            companion = Stat.objects.filter(name='Companion').first()
            if companion:
                abilities.append(companion)

        elif splat == 'Changeling':
            if stat_type == 'talent':
                # Add Kenning for Changelings
                kenning = Stat.objects.filter(name='Kenning').first()
                if kenning:
                    # Insert Kenning in alphabetical order
                    insert_index = next((i for i, ability in enumerate(abilities) 
                                       if ability.name > 'Kenning'), len(abilities))
                    abilities.insert(insert_index, kenning)
            elif stat_type == 'knowledge':
                # Add Gremayre for Changelings
                gremayre = Stat.objects.filter(name='Gremayre').first()
                if gremayre:
                    # Insert Gremayre in alphabetical order
                    insert_index = next((i for i, ability in enumerate(abilities) 
                                       if ability.name > 'Gremayre'), len(abilities))
                    abilities.insert(insert_index, gremayre)

        return abilities

    def format_abilities_section(self, character):
        """Format the abilities section of the character sheet."""
        string = header("Abilities", width=78, color="|y")
        string += " " + divider("Talents", width=25, fillchar=" ") + " "
        string += divider("Skills", width=25, fillchar=" ") + " "
        string += divider("Knowledges", width=25, fillchar=" ") + "\n"

        # Get abilities for each category
        talents = self.get_abilities_for_splat(character, 'talent')
        skills = self.get_abilities_for_splat(character, 'skill')
        knowledges = self.get_abilities_for_splat(character, 'knowledge')

        # Format abilities with padding for skills and knowledges
        formatted_talents = [self.format_ability(character, talent, 'talent') for talent in talents]
        formatted_skills = [self.format_ability(character, skill, 'skill') for skill in skills]
        formatted_knowledges = [self.format_ability(character, knowledge, 'knowledge') for knowledge in knowledges]

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
                        formatted_list.append(self.format_ability(character, Stat(name=f"`{specialty}"), ability_type))

        # Ensure all columns have the same length
        max_len = max(len(formatted_talents), len(formatted_skills), len(formatted_knowledges))
        formatted_talents.extend([" " * 25] * (max_len - len(formatted_talents)))
        formatted_skills.extend([" " * 25] * (max_len - len(formatted_skills)))
        formatted_knowledges.extend([" " * 25] * (max_len - len(formatted_knowledges)))

        # Combine columns
        for talent, skill, knowledge in zip(formatted_talents, formatted_skills, formatted_knowledges):
            string += f"{talent}{skill}{knowledge}\n"

        return string

    def format_secondary_abilities_section(self, character):
        """Format the secondary abilities section of the character sheet."""
        string = header("Secondary Abilities", width=78, color="|y")
        string += " " + divider("Talents", width=25, fillchar=" ") + " "
        string += divider("Skills", width=25, fillchar=" ") + " "
        string += divider("Knowledges", width=25, fillchar=" ") + "\n"

        # Get splat-specific secondary abilities
        splat = character.get_stat('other', 'splat', 'Splat', temp=False)

        # Initialize empty lists for each category
        formatted_secondary_talents = []
        formatted_secondary_skills = []
        formatted_secondary_knowledges = []

        # Base secondary abilities for all characters
        base_secondary_talents = sorted(['Artistry','Carousing', 'Diplomacy', 'Intrigue', 'Mimicry', 'Scrounging', 'Seduction', 'Style'])
        base_secondary_skills = sorted(['Archery', 'Fortune-Telling', 'Fencing', 'Gambling', 'Jury-Rigging', 'Pilot', 'Torture'])
        base_secondary_knowledges = sorted(['Area Knowledge', 'Cultural Savvy', 'Demolitions', 'Herbalism', 'Media', 'Power-Brokering', 'Vice'])

        # Add base secondary abilities for all characters
        formatted_secondary_talents.extend([
            self.format_ability(character, Stat(name=talent, category='abilities', stat_type='secondary_talent'), 'secondary_talent')
            for talent in base_secondary_talents
        ])
        formatted_secondary_skills.extend([
            self.format_ability(character, Stat(name=skill, category='abilities', stat_type='secondary_skill'), 'secondary_skill')
            for skill in base_secondary_skills
        ])
        formatted_secondary_knowledges.extend([
            self.format_ability(character, Stat(name=knowledge, category='abilities', stat_type='secondary_knowledge'), 'secondary_knowledge')
            for knowledge in base_secondary_knowledges
        ])

        # Add splat-specific secondary abilities
        if splat.lower() == 'mage':
            # Secondary Talents
            mage_secondary_talents = sorted(['High Ritual', 'Blatancy', 'Flying', 'Lucid Dreaming'])
            formatted_secondary_talents.extend([
                self.format_ability(character, Stat(name=talent, category='abilities', stat_type='secondary_talent'), 'secondary_talent')
                for talent in mage_secondary_talents
            ])

            # Secondary Skills
            mage_secondary_skills = sorted(['Microgravity Ops', 'Energy Weapons', 'Helmsman', 'Biotech', 'Do'])
            formatted_secondary_skills.extend([
                self.format_ability(character, Stat(name=skill, category='abilities', stat_type='secondary_skill'), 'secondary_skill')
                for skill in mage_secondary_skills
            ])

            # Secondary Knowledges
            mage_secondary_knowledges = sorted(['Hypertech', 'Cybernetics', 'Paraphysics', 'Xenobiology'])
            formatted_secondary_knowledges.extend([
                self.format_ability(character, Stat(name=knowledge, category='abilities', stat_type='secondary_knowledge'), 'secondary_knowledge')
                for knowledge in mage_secondary_knowledges
            ])

        # Ensure all columns have the same length
        max_len = max(len(formatted_secondary_talents), len(formatted_secondary_skills), len(formatted_secondary_knowledges))
        formatted_secondary_talents.extend([" " * 25] * (max_len - len(formatted_secondary_talents)))
        formatted_secondary_skills.extend([" " * 25] * (max_len - len(formatted_secondary_skills)))
        formatted_secondary_knowledges.extend([" " * 25] * (max_len - len(formatted_secondary_knowledges)))

        # Display the secondary abilities in columns
        for talent, skill, knowledge in zip(formatted_secondary_talents, formatted_secondary_skills, formatted_secondary_knowledges):
            string += f"{talent}{skill}{knowledge}\n"

        return string

    def process_companion_powers(self, character, powers):
        """Process powers section for Companion characters."""
        # Add Special Advantages section
        powers.append(divider("Special Advantages", width=38, color="|b"))
        special_advantages = character.db.stats.get('powers', {}).get('special_advantage', {})
        if special_advantages:
            for power, values in sorted(special_advantages.items()):
                power_value = values.get('perm', 0)
                powers.append(format_stat(power, power_value, default=0, width=38))
        else:
            powers.append(" None".ljust(38))
        
        # Add Charms section if any exist
        powers.append(divider("Charms", width=38, color="|b"))
        charms = character.db.stats.get('powers', {}).get('charm', {})
        if charms:
            for charm, values in sorted(charms.items()):
                charm_value = values.get('perm', 0)
                powers.append(format_stat(charm, charm_value, default=0, width=38))
        else:
            powers.append(" None".ljust(38))
            
        # Add pools
        self.pools_list.extend([
            format_stat('Essence', format_pool_value(character, 'Essence'), width=25),
            format_stat('Willpower', format_pool_value(character, 'Willpower'), width=25)
        ])
        
        # Add Banality if it exists
        banality = character.get_stat('pools', 'dual', 'Banality', temp=False)
        if banality is not None:
            self.pools_list.append(format_stat('Banality', format_pool_value(character, 'Banality'), width=25))
            
        # Add Rage pool if character has Ferocity
        rage_value = character.get_stat('pools', 'dual', 'Rage', temp=False)
        if rage_value and rage_value > 0:
            self.pools_list.append(format_stat('Rage', format_pool_value(character, 'Rage'), width=25))
            
        # Add Paradox pool if character has Feast of Nettles
        paradox_value = character.get_stat('pools', 'dual', 'Paradox', temp=False)
        if paradox_value and paradox_value > 0:
            self.pools_list.append(format_stat('Paradox', format_pool_value(character, 'Paradox'), width=25))
            
        return powers

def format_pool_value(character, pool_name):
    """Format a pool value with both permanent and temporary values."""
    perm = character.get_stat('pools', 'dual', pool_name, temp=False)
    temp = character.get_stat('pools', 'dual', pool_name, temp=True)

    if perm is None:
        perm = 0
    if temp is None:
        temp = perm

    return f"{perm}({temp})" if temp != perm else str(perm)

def calculate_blood_pool(generation):
    """
    Calculate blood pool based on vampire generation.
    
    Args:
        generation (str): Character's generation (e.g. '7th', '13th')
        
    Returns:
        int: Maximum blood pool for that generation
    """
    # Extract number from generation string and convert to int
    try:
        gen_num = int(''.join(filter(str.isdigit, str(generation))))
    except (ValueError, TypeError):
        gen_num = 13  # Default to 13th generation if invalid/missing

    # Calculate blood pool based on generation
    if gen_num >= 13:
        return 10
    elif gen_num == 12:
        return 11
    elif gen_num == 11:
        return 12
    elif gen_num == 10:
        return 13
    elif gen_num == 9:
        return 14
    elif gen_num == 8:
        return 15
    elif gen_num == 7:
        return 20
    else:
        return 10  # Default to 10 for any unexpected values