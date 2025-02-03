# commands/chargen.py

from evennia import Command
from evennia.utils.evmenu import EvMenu
from world.wod20th.models import Stat, SHIFTER_IDENTITY_STATS, SHIFTER_RENOWN, SHIFTER_RENOWN, CLAN, AFFILIATION, MAGE_SPHERES, TRADITION, TRADITION_SUBFACTION, CONVENTION, METHODOLOGIES, NEPHANDI_FACTION, SEEMING, KITH, SEELIE_LEGACIES, UNSEELIE_LEGACIES, ARTS, REALMS, calculate_willpower, calculate_road, MORTALPLUS_TYPES
from typeclasses.characters import Character
from evennia.commands.default.muxcommand import MuxCommand
from world.jobs.models import Job, Queue
from django.utils import timezone

ATTRIBUTE_CATEGORIES = ['Physical', 'Social', 'Mental']
ABILITY_CATEGORIES = ['Talents', 'Skills', 'Knowledges']

class CmdSubmit(MuxCommand):
    """
    Submit your character for approval.

    Usage:
      +submit

    This command will automatically create a job requesting character approval.
    It will include your character's name, splat information, and basic stats.
    Staff will review your character and either approve or request changes.
    """

    key = "+submit"
    locks = "cmd:all()"
    help_category = "Chargen & Character Info"

    def func(self):
        caller = self.caller
        
        # Check if character is approved using only the persistent attribute
        if caller.db.approved:
            caller.msg("Your character is already approved.")
            return

        # Make sure approved attribute exists and is False if it doesn't exist
        if not hasattr(caller.db, 'approved'):
            caller.db.approved = False

        # Check if there's already an open approval job for this character
        existing_jobs = Job.objects.filter(
            title__icontains=caller.name,
            status__in=['open', 'claimed'],
            queue__name='CHARGEN'
        )
        if existing_jobs.exists():
            caller.msg("You already have a pending approval request. Please wait for staff to review it.")
            return

        # Gather character information
        char_info = []
        char_info.append(f"Character Name: {caller.name}")
        
        # Get splat information from stats
        if hasattr(caller.db, 'stats') and caller.db.stats:
            splat_info = caller.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm')
            if splat_info:
                char_info.append(f"Splat: {splat_info}")

            # Add attributes
            char_info.append("\nAttributes:")
            for category in ['physical', 'social', 'mental']:
                attributes = caller.db.stats.get(category, {})
                if attributes:
                    char_info.append(f"\n{category.title()}:")
                    for attr_name, attr_data in attributes.items():
                        perm_value = attr_data.get('perm', 0)
                        char_info.append(f"  {attr_name.replace('_', ' ').title()}: {perm_value}")

            # Add abilities
            abilities = caller.db.stats.get('abilities', {})
            if abilities:
                char_info.append("\nAbilities:")
                for ability_name, ability_data in abilities.items():
                    perm_value = ability_data.get('perm', 0)
                    if perm_value > 0:  # Only show abilities with points in them
                        char_info.append(f"  {ability_name.replace('_', ' ').title()}: {perm_value}")

            # Add supernatural powers based on splat
            powers = caller.db.stats.get('powers', {})
            if powers:
                char_info.append("\nPowers:")
                for power_name, power_data in powers.items():
                    perm_value = power_data.get('perm', 0)
                    if perm_value > 0:  # Only show powers with points in them
                        char_info.append(f"  {power_name.replace('_', ' ').title()}: {perm_value}")

        else:
            char_info.append("\nWarning: No character statistics found. Please complete character generation first.")

        # Format the description
        description = "\n".join(char_info)
        description += "\n\nPlease review this character for approval."

        try:
            # Get or create the CHARGEN queue
            queue, _ = Queue.objects.get_or_create(
                name='CHARGEN',
                defaults={'automatic_assignee': None}
            )

            # Create the job
            job = Job.objects.create(
                title=f"Character Approval: {caller.name}",
                description=description,
                requester=caller.account,
                queue=queue,
                status='open'
            )

            # Add a comment with any additional notes
            initial_comment = {
                "author": caller.account.username,
                "text": "Character submitted for approval.",
                "created_at": timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if not job.comments:
                job.comments = []
            job.comments.append(initial_comment)
            job.save()

            caller.msg("|gCharacter submitted for approval. Job ID: #{0}|n".format(job.id))
            caller.msg("Staff will review your character and contact you if any changes are needed.")
            
            # Notify staff through the jobs channel
            from commands.jobs.jobs_commands import CmdJobs
            cmd_jobs = CmdJobs()
            cmd_jobs.caller = caller
            cmd_jobs.post_to_jobs_channel(
                caller.name,
                job.id,
                "submitted character for approval"
            )

        except Exception as e:
            caller.msg("|rError submitting character: {0}|n".format(e))

def node_select_ability_category(caller):
    text = "Select priority for ability categories (Primary: 13 points, Secondary: 9 points, Tertiary: 5 points)"
    remaining_categories = [cat for cat in ABILITY_CATEGORIES if cat not in caller.db.chargen.get('ability_order', [])]
    
    if not remaining_categories:
        return "node_distribute_ability_points"
        
    options = [{"key": str(i+1), "desc": category, "goto": (_set_ability_category, {"category": category})} 
               for i, category in enumerate(remaining_categories)]
    return text, options

def _set_ability_category(caller, raw_string, **kwargs):
    category = kwargs.get("category")
    if 'ability_order' not in caller.db.chargen:
        caller.db.chargen['ability_order'] = []
    caller.db.chargen['ability_order'].append(category)
    caller.msg(f"Added {category} to ability priority order")
    return "node_abilities"

def setup_mortalplus_character(character, mortalplus_type):
    """
    Set up initial stats and powers for Mortal+ characters
    """
    if mortalplus_type not in MORTALPLUS_TYPES:
        raise ValueError(f"Invalid Mortal+ type: {mortalplus_type}")

    # Set basic identity stats
    character.set_stat('identity', 'personal', 'Splat', 'Mortal Plus')
    character.set_stat('identity', 'personal', 'Mortal Plus Type', mortalplus_type)

    # Set up power categories based on type
    for power_category in MORTALPLUS_TYPES[mortalplus_type]:
        character.setup_power_category(power_category)

    # Special handling for each type
    if mortalplus_type == 'Ghoul':
        # Initialize Blood pool
        character.set_stat('pools', 'temporary', 'Blood', {'perm': 1, 'temp': 1})
    
    elif mortalplus_type == 'Kinfolk':
        # Kinfolk start with no special powers - they're merit-gated
        pass
    
    elif mortalplus_type == 'Kinain':
        # Initialize Glamour pool based on Fae Blood Merit
        merits = character.db.stats.get('merits', {}).get('merit', {})
        fae_blood = next((value.get('perm', 0) for merit, value in merits.items() 
                         if merit.lower() == 'fae blood'), 0)
        if fae_blood:
            max_glamour = fae_blood // 2
            character.set_stat('pools', 'temporary', 'Glamour', 
                             {'perm': max_glamour, 'temp': max_glamour})

