"""
Characters

Characters are (by default) Objects that are puppeted by Players.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type for your game. It is from
here you can define how all characters will look and behave by default.
"""
from evennia.objects.objects import DefaultCharacter
from evennia.utils.utils import lazy_property
from evennia.utils.ansi import ANSIString
from world.wod20th.models import Stat
from world.wod20th.utils.ansi_utils import wrap_ansi
import re
import random
from datetime import datetime, timedelta
from world.wod20th.utils.language_data import AVAILABLE_LANGUAGES

from django.contrib.auth.models import User
from django.db import models
from decimal import Decimal, ROUND_DOWN, InvalidOperation
import json
from world.wod20th.utils.formatting import header, footer, divider

class Character(DefaultCharacter):
    """
    The Character defaults to implementing some of its hook methods with the
    following standard functionality:
    ...
    """

    def at_object_creation(self):
        """
        Called only at initial creation.
        """
        super().at_object_creation()

        # Initialize basic attributes
        self.db.desc = ""
        self.db.stats = {}
        
        # Initialize languages with English as default
        self.db.languages = ["English"]
        self.db.speaking_language = "English"
        
        self.tags.add("in_material", category="state")
        self.db.unfindable = False
        self.db.fae_desc = ""

        self.db.approved = False  # Ensure all new characters start unapproved
        self.db.in_umbra = False  # Use a persistent attribute instead of a tag
        
        # Initialize health tracking
        self.db.agg = 0
        self.db.lethal = 0
        self.db.bashing = 0
        self.db.injury_level = "Healthy"

        # Initialize XP tracking with separate IC XP
        self.db.xp = {
            'total': Decimal('0.00'),    # Total XP earned
            'current': Decimal('0.00'),  # Available XP to spend
            'spent': Decimal('0.00'),    # Total XP spent
            'ic_xp': Decimal('0.00'),    # XP earned from IC scenes
            'monthly_spent': Decimal('0.00'),  # XP spent this month
            'last_reset': datetime.now(),  # Last monthly reset
            'spends': [],  # List of recent spends
            'last_scene': None,  # Last IC scene participation
            'scenes_this_week': 0  # Number of scenes this week
        }

        # Scene tracking
        self.db.scene_data = {
            'current_scene': None,  # Will store start time of current scene
            'scene_location': None, # Location where scene started
            'last_activity': None,  # Last time character was active in scene
            'completed_scenes': 0,  # Number of completed scenes this week
            'last_weekly_reset': datetime.now()  # For weekly scene count reset
        }

    def at_post_unpuppet(self, account=None, session=None, **kwargs):
        """
        Called just after the Character was unpuppeted.
        """
        if not self.sessions.count():
            # only remove this char from grid if no sessions control it anymore.
            if self.location:
                def message(obj, from_obj):
                    obj.msg(
                        "{name} has disconnected{reason}.".format(
                            name=self.get_display_name(obj),
                            reason=kwargs.get("reason", ""),
                        ),
                        from_obj=from_obj,
                    )
                self.location.for_contents(message, exclude=[self], from_obj=self)
                self.db.prelogout_location = self.location
                self.location = None

    @lazy_property
    def notes(self):
        return Note.objects.filter(character=self)

    def add_note(self, name, text, category="General"):
        """Add a new note to the character."""
        notes = self.attributes.get('notes', {})
        
        # Find the first available ID by checking for gaps
        used_ids = set(int(id_) for id_ in notes.keys())
        note_id = 1
        while note_id in used_ids:
            note_id += 1
        
        # Create the new note
        note_data = {
            'name': name,
            'text': text,
            'category': category,
            'is_public': False,
            'is_approved': False,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        notes[str(note_id)] = note_data
        self.attributes.add('notes', notes)
        
        return Note(
            name=name,
            text=text,
            category=category,
            is_public=False,
            is_approved=False,
            created_at=note_data['created_at'],
            updated_at=note_data['updated_at'],
            note_id=str(note_id)
        )

    def get_note(self, note_id):
        """Get a specific note by ID."""
        notes = self.attributes.get('notes', default={})
        note_data = notes.get(str(note_id))
        return Note.from_dict(note_data) if note_data else None

    def get_all_notes(self):
        """Get all notes for this character."""
        notes = self.attributes.get('notes', default={})
        return [Note.from_dict(note_data) for note_data in notes.values()]

    def update_note(self, note_id, text=None, category=None, **kwargs):
        """Update an existing note."""
        notes = self.attributes.get('notes', default={})
        if str(note_id) in notes:
            note_data = notes[str(note_id)]
            if text is not None:
                note_data['text'] = text
            if category is not None:
                note_data['category'] = category
            note_data.update(kwargs)
            note_data['updated_at'] = datetime.now().isoformat()
            notes[str(note_id)] = note_data
            self.attributes.add('notes', notes)
            return True
        return False

    def change_note_status(self, note_name, is_public):
        """Change the visibility status of a note."""
        try:
            note = self.get_note(note_name)
            if note:
                note.is_public = is_public
                note.save()
                return True
            return False
        except Exception as e:
            return False

    def get_display_name(self, looker, **kwargs):
        """
        Get the name to display for the character.
        """
        name = self.key
        
        if self.db.gradient_name:
            name = ANSIString(self.db.gradient_name)
            if looker.check_permstring("builders"):
                name += f"({self.dbref})"
            return name
        
        # If the looker is builder+ show the dbref
        if looker.check_permstring("builders"):
            name += f"({self.dbref})"

        return name

    def get_languages(self):
        """
        Get the character's known languages.
        """
        # Get current languages, initialize if needed
        current_languages = self.db.languages or []
        
        # Convert to list if it's not already
        if not isinstance(current_languages, list):
            current_languages = [current_languages]
        
        # Clean up the languages list
        cleaned_languages = []
        seen = set()
        
        # First pass: extract all language strings and clean them
        for entry in current_languages:
            # Convert to string and clean it
            lang_str = str(entry).replace('"', '').replace("'", '').replace('[', '').replace(']', '')
            # Split on commas and process each part
            for part in lang_str.split(','):
                clean_lang = part.strip()
                if clean_lang and clean_lang.lower() not in seen:
                    # Check if it's a valid language
                    for available_lang in AVAILABLE_LANGUAGES.values():
                        if available_lang.lower() == clean_lang.lower():
                            cleaned_languages.append(available_lang)
                            seen.add(available_lang.lower())
                            break
        
        # Ensure English is first
        if "English" in cleaned_languages:
            cleaned_languages.remove("English")
        cleaned_languages.insert(0, "English")
        
        # Store the cleaned list back to the database
        self.db.languages = cleaned_languages
        return cleaned_languages

    def set_speaking_language(self, language):
        """
        Set the character's currently speaking language.
        """
        if language is None:
            self.db.speaking_language = None
            return
            
        # Get clean language list
        known_languages = self.get_languages()
        
        # Case-insensitive check
        for known in known_languages:
            if known.lower() == language.lower():
                self.db.speaking_language = known
                return
                
        raise ValueError(f"You don't know the language: {language}")

    def get_speaking_language(self):
        """
        Get the character's currently speaking language.
        """
        return self.db.speaking_language

    def detect_tone(self, message):
        """
        Detect the tone of the message based on punctuation and keywords.
        """
        if message.endswith('!'):
            return "excitedly"
        elif message.endswith('?'):
            return "questioningly"
        elif any(word in message.lower() for word in ['hello', 'hi', 'hey', 'greetings']):
            return "in greeting"
        elif any(word in message.lower() for word in ['goodbye', 'bye', 'farewell']):
            return "in farewell"
        elif any(word in message.lower() for word in ['please', 'thank', 'thanks']):
            return "politely"
        elif any(word in message.lower() for word in ['sorry', 'apologize']):
            return "apologetically"
        else:
            return None  # No specific tone detected

    def mask_language(self, message, language):
        """
        Mask the language in the message with more dynamic responses.
        """
        words = len(message.split())
        tone = self.detect_tone(message)

        if words <= 3:
            options = [
                f"<< mutters a few words in {language} >>",
                f"<< something brief in {language} >>",
                f"<< speaks a short {language} phrase >>",
            ]
        elif words <= 10:
            options = [
                f"<< speaks a sentence in {language} >>",
                f"<< a {language} phrase >>",
                f"<< conveys a short message in {language} >>",
            ]
        else:
            options = [
                f"<< gives a lengthy explanation in {language} >>",
                f"<< engages in an extended {language} dialogue >>",
                f"<< speaks at length in {language} >>",
            ]

        masked = random.choice(options)
        
        if tone:
            masked = f"{masked[:-3]}, {tone} >>"

        return masked

    def prepare_say(self, speech, language_only=False, viewer=None, skip_english=False):
        """
        Prepare speech messages based on language settings.
        
        Args:
            speech (str): The message to be spoken
            language_only (bool): If True, only return the language portion without 'says'
            viewer (Object): The character viewing the message
            skip_english (bool): If True, don't append language tag for English
            
        Returns:
            tuple: (message to self, message to those who understand, 
                   message to those who don't understand, language used)
        """
        # Strip the language marker if present
        if speech.startswith('~'):
            speech = speech[1:]
        
        # Check if we're in an OOC Area
        in_ooc_area = (hasattr(self.location, 'db') and 
                      self.location.db.roomtype == 'OOC Area')
        
        # If in OOC Area, skip language processing
        if in_ooc_area:
            if language_only:
                return speech, speech, speech, None
            else:
                msg = f'You say, "{speech}"'
                msg_others = f'{self.name} says, "{speech}"'
                return msg, msg_others, msg_others, None
        
        # Get the speaking language
        language = self.get_speaking_language()
        
        # Staff can always understand all languages
        is_staff = False
        if viewer and viewer.account:
            # Check permissions in order of hierarchy
            if viewer.account.is_superuser:
                is_staff = True
            elif viewer.account.check_permstring("admin"):
                is_staff = True
            elif viewer.account.check_permstring("storyteller"):
                is_staff = True
            elif viewer.account.check_permstring("builder"):
                is_staff = True
            # Player-level admins don't get language privileges
            elif viewer.account.check_permstring("player"):
                is_staff = False
        
        # Format the messages
        if language_only:
            if skip_english and language == "English":
                msg_self = speech
                msg_understand = speech
                msg_not_understand = speech
            else:
                msg_self = f"{speech} << in {language} >>"
                if is_staff:
                    msg_understand = f"{speech} << in {language} >>"
                    msg_not_understand = f"{speech} << in {language} >>"
                else:
                    msg_understand = f"{speech} << in {language} >>"
                    msg_not_understand = f"<< something in {language} >>"
        else:
            if skip_english and language == "English":
                msg_self = f'You say, "{speech}"'
                msg_understand = f'{self.name} says, "{speech}"'
                msg_not_understand = f'{self.name} says, "{speech}"'
            else:
                msg_self = f'You say, "{speech} << in {language} >>"'
                if is_staff:
                    msg_understand = f'{self.name} says, "{speech} << in {language} >>"'
                    msg_not_understand = f'{self.name} says, "{speech} << in {language} >>"'
                else:
                    msg_understand = f'{self.name} says, "{speech} << in {language} >>"'
                    msg_not_understand = f'{self.name} says something in {language}'
        
        return msg_self, msg_understand, msg_not_understand, language

    def step_sideways(self):
        """Attempt to step sideways into the Umbra."""
        if self.db.in_umbra:
            self.msg("You are already in the Umbra.")
            return False
        
        if self.location:
            success = self.location.step_sideways(self)
            if success:
                # Use attributes.add for more reliable attribute setting
                self.attributes.add('in_umbra', True)
                self.tags.remove("in_material", category="state")
                self.tags.add("in_umbra", category="state")
                self.location.msg_contents(f"{self.name} shimmers and fades from view as they step into the Umbra.", exclude=[self])
            return success
        return False

    def return_from_umbra(self):
        """Return from the Umbra to the material world."""
        if not self.db.in_umbra:
            self.msg("You are not in the Umbra.")
            return False
        
        # Use attributes.add for more reliable attribute setting
        self.attributes.add('in_umbra', False)
        self.tags.remove("in_umbra", category="state")
        self.tags.add("in_material", category="state")
        self.location.msg_contents(f"{self.name} shimmers into view as they return from the Umbra.", exclude=[self])
        return True

    def format_description(self, desc):
        """
        Format the description with proper paragraph handling and indentation.
        """
        if not desc:
            return ""
            
        # First normalize all line breaks and tabs
        desc = desc.replace('%T', '%t')
        desc = desc.replace('%R%R', '\n\n')  # Double line breaks first
        desc = desc.replace('%r%r', '\n\n')
        desc = desc.replace('%R', '\n')
        desc = desc.replace('%r', '\n')
        
        # Process each paragraph
        paragraphs = []
        for paragraph in desc.split('\n'):
            # Skip completely empty paragraphs
            if not paragraph.strip():
                paragraphs.append('')
                continue
                
            # Handle tabs at start of paragraph
            tab_count = 0
            working_paragraph = paragraph
            while working_paragraph.startswith('%t'):
                tab_count += 1
                working_paragraph = working_paragraph[2:]  # Remove just the %t
            
            # Apply indentation and handle the rest of the paragraph
            if tab_count > 0:
                working_paragraph = '    ' * tab_count + working_paragraph
            
            # Wrap the paragraph while preserving ANSI codes
            wrapped = wrap_ansi(working_paragraph, width=76)
            paragraphs.append(wrapped)
        
        # Clean up multiple consecutive empty lines
        result = []
        last_empty = False
        for p in paragraphs:
            if not p:
                if not last_empty:
                    result.append(p)
                last_empty = True
            else:
                result.append(p)
                last_empty = False
        
        return '\n'.join(result)

    def return_appearance(self, looker, **kwargs):
        """
        This formats a description. It is the hook a 'look' command
        should call.
        """
        if not looker:
            return ""
            
        # Check if looker is a Changeling and send Banality message
        if looker.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm') == 'Changeling':
            # Get target's Banality from pools.dual
            banality = self.db.stats.get('pools', {}).get('dual', {}).get('Banality', {}).get('perm', 0)
            if isinstance(banality, dict):
                banality = banality.get('perm', 0)
            try:
                banality = int(banality)
            except (ValueError, TypeError):
                banality = 0
                
            # Import here to avoid circular imports
            from world.wod20th.utils.banality import get_banality_message
            msg = get_banality_message(banality)
            looker.msg(f"|m{msg}|n")
            
        # Start with the name
        string = f"|c{self.get_display_name(looker)}|n\n"

        # Get and format the description
        desc = self.db.desc
        if desc:
            desc = self.format_description(desc)
            string += desc + "\n"

        return string

    def announce_move_from(self, destination, msg=None, mapping=None, **kwargs):
        """
        Called just before moving out of the current room.
        """
        if not self.location:
            return

        string = f"{self.name} is leaving {self.location}, heading for {destination}."
        
        # Send message directly to the room
        self.location.msg_contents(string, exclude=[self], from_obj=self)

    def announce_move_to(self, source_location, msg=None, mapping=None, **kwargs):
        """
        Called just after arriving in a new room.
        """
        if not source_location:
            return

        string = f"{self.name} arrives to {self.location} from {source_location}."
        
        # Send message directly to the room
        self.location.msg_contents(string, exclude=[self], from_obj=self)

    def at_say(self, message, msg_self=None, msg_location=None, receivers=None, msg_receivers=None, **kwargs):
        """Hook method for the say command."""
        if not self.location:
            return

        # Filter receivers based on Umbra state
        filtered_receivers = [
            r for r in self.location.contents 
            if hasattr(r, 'has_account') and r.has_account and r.db.in_umbra == self.db.in_umbra
        ]

        # Prepare the say messages
        msg_self, msg_understand, msg_not_understand, language = self.prepare_say(message)

        # Send messages to receivers
        for receiver in filtered_receivers:
            if receiver != self:
                if language and language in receiver.get_languages():
                    receiver.msg(msg_understand)
                else:
                    receiver.msg(msg_not_understand)

        # Send message to the speaker
        self.msg(msg_self)

        # Check if this is an IC scene
        if (self.location and 
            hasattr(self.location, 'db') and 
            self.location.db.roomtype != 'OOC Area' and
            any(obj for obj in self.location.contents 
                if obj != self and 
                hasattr(obj, 'has_account') and 
                obj.has_account)):
            self.record_scene_activity()

    def at_pose(self, pose_understand, pose_not_understand, pose_self, speaking_language):
        if not self.location:
            return

        # Filter receivers based on Umbra state
        filtered_receivers = [
            r for r in self.location.contents 
            if hasattr(r, 'has_account') and r.has_account and r.db.in_umbra == self.db.in_umbra
        ]

        # Send messages to receivers
        for receiver in filtered_receivers:
            if receiver != self:
                if speaking_language and speaking_language in receiver.get_languages():
                    receiver.msg(pose_understand)
                else:
                    receiver.msg(pose_not_understand)

        # Send message to the poser
        self.msg(pose_self)

        # Log the pose (only visible to those in the same realm)
        self.location.msg_contents(pose_understand, exclude=filtered_receivers + [self], from_obj=self)

        # Check if this is an IC scene
        if (self.location and 
            hasattr(self.location, 'db') and 
            self.location.db.roomtype != 'OOC Area' and
            any(obj for obj in self.location.contents 
                if obj != self and 
                hasattr(obj, 'has_account') and 
                obj.has_account)):
            self.record_scene_activity()

    def at_emote(self, message, msg_self=None, msg_location=None, receivers=None, msg_receivers=None, **kwargs):
        """Display an emote to the room."""
        if not self.location:
            return

        # Filter receivers based on Umbra state
        filtered_receivers = [
            r for r in self.location.contents 
            if hasattr(r, 'has_account') and r.has_account and r.db.in_umbra == self.db.in_umbra
        ]
        
        # Send the emote to filtered receivers
        for receiver in filtered_receivers:
            if receiver != self:
                receiver.msg(message)
        
        # Send the emote to the emitter
        self.msg(msg_self or message)

        # Check if this is an IC scene
        if (self.location and 
            hasattr(self.location, 'db') and 
            self.location.db.roomtype != 'OOC Area' and
            any(obj for obj in self.location.contents 
                if obj != self and 
                hasattr(obj, 'has_account') and 
                obj.has_account)):
            self.record_scene_activity()

    def get_stat(self, stat_type, category, stat_name, temp=False):
        """Get a stat value."""
        # Handle attributes by using their category as the stat_type
        if stat_type == 'attributes':
            stat_type = category  # Use physical/social/mental as the stat_type
            category = 'attributes'  # Set category to 'attributes'

        # Handle other stats
        if stat_type not in self.db.stats:
            return 0
        if category not in self.db.stats[stat_type]:
            return 0
        if stat_name not in self.db.stats[stat_type][category]:
            return 0
        return self.db.stats[stat_type][category][stat_name].get('temp' if temp else 'perm', 0)

    def set_stat(self, stat_type, category, stat_name, value, temp=False):
        """Set a stat value."""
        # Ensure stats structure exists
        if not hasattr(self.db, 'stats'):
            self.db.stats = {}

        # Handle identity stats
        if stat_type in ['personal', 'lineage']:
            if 'identity' not in self.db.stats:
                self.db.stats['identity'] = {'personal': {}, 'lineage': {}}
            self.db.stats['identity'][stat_type][stat_name] = {'perm': value, 'temp': value}
            return

        # Handle archetype stats
        if stat_type == 'archetype':
            if 'archetype' not in self.db.stats:
                self.db.stats['archetype'] = {'personal': {}}
            self.db.stats['archetype']['personal'][stat_name] = {'perm': value, 'temp': value}
            return

        # Handle attributes
        if category == 'attributes':
            if 'attributes' not in self.db.stats:
                self.db.stats['attributes'] = {'physical': {}, 'social': {}, 'mental': {}}
            if stat_type in ['physical', 'social', 'mental']:
                if stat_name not in self.db.stats['attributes'][stat_type]:
                    self.db.stats['attributes'][stat_type][stat_name] = {'perm': 0, 'temp': 0}
                self.db.stats['attributes'][stat_type][stat_name]['temp' if temp else 'perm'] = value
                return

        # Handle all other stats
        if stat_type not in self.db.stats:
            self.db.stats[stat_type] = {}
        if category not in self.db.stats[stat_type]:
            self.db.stats[stat_type][category] = {}
        if stat_name not in self.db.stats[stat_type][category]:
            self.db.stats[stat_type][category][stat_name] = {'perm': 0, 'temp': 0}
        self.db.stats[stat_type][category][stat_name]['temp' if temp else 'perm'] = value

    def check_stat_value(self, category, stat_type, stat_name, value, temp=False):
        """
        Check if a value is valid for a stat, considering instances if applicable.
        """
        from world.wod20th.models import Stat  
        stat = Stat.objects.filter(name=stat_name, category=category, stat_type=stat_type).first()
        if stat:
            stat_values = stat.values
            return value in stat_values['temp'] if temp else value in stat_values['perm']
        return False

    def colorize_name(self, message):
        """
        Replace instances of the character's name with their gradient name in the message.
        """
        if self.db.gradient_name:
            gradient_name = ANSIString(self.db.gradient_name)
            return message.replace(self.name, str(gradient_name))
        return message
 
    def delete_note(self, note_id):
        """Delete a note."""
        notes = self.attributes.get('notes', default={})
        if str(note_id) in notes:
            del notes[str(note_id)]
            self.attributes.add('notes', notes)
            return True
        return False

    def get_notes_by_category(self, category):
        """Get all notes in a specific category."""
        return [note for note in self.get_all_notes() 
                if note.category.lower() == category.lower()]

    def get_public_notes(self):
        """Get all public notes."""
        return [note for note in self.get_all_notes() if note.is_public]

    def get_approved_notes(self):
        """Get all approved notes."""
        return [note for note in self.get_all_notes() if note.is_approved]

    def approve_note(self, name):
        if self.character_sheet:
            return self.character_sheet.approve_note(name)
        return False

    def unapprove_note(self, name):
        if self.character_sheet:
            return self.character_sheet.unapprove_note(name)
        return False

    def change_note_status(self, name, is_public):
        if self.character_sheet:
            return self.character_sheet.change_note_status(name, is_public)
        return False

    def get_fae_description(self):
        """Get the fae description of the character."""
        return self.db.fae_desc or f"{self.name} has no visible fae aspect."

    def set_fae_description(self, description):
        """Set the fae description of the character."""
        self.db.fae_desc = description

    def is_fae_perceiver(self):
        """Check if the character is a Changeling or Kinain."""
        if not self.db.stats or 'other' not in self.db.stats or 'splat' not in self.db.stats['other']:
            return False
        splat = self.db.stats['other']['splat'].get('Splat', {}).get('perm', '')
        return splat in ['Changeling'] or self.is_kinain()

    def is_kinain(self):
        """Check if the character is a Kinain."""
        return self.db.stats.get('identity', {}).get('mortalplus_type', {}).get('Kinain', {}).get('perm', False)

    def search_notes(self, search_term):
        """Search notes by name or content."""
        search_term = search_term.lower()
        return [
            note for note in self.get_all_notes()
            if search_term in note.name.lower() or search_term in note.text.lower()
        ]

    def can_have_ability(self, ability_name):
        """Check if character can have a specific ability based on splat."""
        from world.wod20th.models import Stat
        
        stat = Stat.objects.filter(name=ability_name).first()
        if not stat or not stat.splat:
            return True
            
        # Get character's splat info
        splat_type = self.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        clan = self.db.stats.get('identity', {}).get('lineage', {}).get('Clan', {}).get('perm', '')
        shifter_type = self.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')

        # Check allowed splats
        allowed_splats = stat.splat
        if isinstance(allowed_splats, list):
            for allowed in allowed_splats:
                if ':' in allowed:
                    splat_name, subtype = allowed.split(':')
                    if splat_type == splat_name:
                        if splat_name == 'Vampire' and clan == subtype:
                            return True
                        elif splat_name == 'Shifter' and shifter_type == subtype:
                            return True
                else:
                    if splat_type == allowed:
                        return True
                        
        return False

    def shift_form(self, new_form):
        """Handle form changes for shifters, including Appearance adjustments."""
        old_form = self.db.stats.get('other', {}).get('form', {}).get('Form', {}).get('temp', '')
        
        # Set the new form
        self.set_stat('other', 'form', 'Form', new_form, temp=True)
        
        # Handle Appearance changes
        if new_form == 'Crinos':
            self.set_stat('attributes', 'social', 'Appearance', 0, temp=True)
        elif old_form == 'Crinos' and new_form != 'Crinos':
            # Restore original Appearance when leaving Crinos
            perm_appearance = self.db.stats.get('attributes', {}).get('social', {}).get('Appearance', {}).get('perm', 1)
            self.set_stat('attributes', 'social', 'Appearance', perm_appearance, temp=True)

    def matches_name(self, searchstring):
        """
        Check if the searchstring matches this character's name or alias.
        """
        searchstring = searchstring.lower().strip()
        
        # First check direct name match
        if self.key.lower() == searchstring:
            return True
            
        # Then check alias
        if self.attributes.has("alias"):
            alias = self.attributes.get("alias")
            if alias and alias.lower() == searchstring:
                return True
            
        return False

    @classmethod
    def get_by_alias(cls, searchstring):
        """
        Find a character by their alias.
        
        Args:
            searchstring (str): The alias to search for
            
        Returns:
            Character or None: The character with matching alias, if any
        """
        from evennia.utils.search import search_object
        
        # Search for objects with matching alias attribute
        matches = search_object(
            searchstring, 
            attribute_name="alias",
            exact=True,
            typeclass='typeclasses.characters.Character'
        )
        
        return matches[0] if matches else None

    def handle_language_merit_change(self):
        """
        Handle changes to Language merit or Natural Linguist merit.
        Removes excess languages if merit points are reduced.
        """
        merits = self.db.stats.get('merits', {})
        language_points = 0
        natural_linguist = False
        
        # Check for Natural Linguist in both categories
        for category in ['mental', 'social']:
            if category in merits:
                if any(merit.lower().replace(' ', '') == 'naturallinguist' 
                      for merit in merits[category].keys()):
                    natural_linguist = True
                    break
        
        # Get Language merit points
        if 'social' in merits:
            for merit_name, merit_data in merits['social'].items():
                if merit_name == 'Language':
                    base_points = merit_data.get('perm', 0)
                    language_points = base_points * 2 if natural_linguist else base_points
                    break
        
        # Get current languages
        current_languages = self.get_languages()
        
        # If we have more languages than points allow (accounting for free English)
        if len(current_languages) - 1 > language_points:
            # Keep English and only as many additional languages as we have points for
            new_languages = ["English"]
            additional_languages = [lang for lang in current_languages if lang != "English"]
            new_languages.extend(additional_languages[:language_points])
            
            # Update languages
            self.db.languages = new_languages
            
            # Reset speaking language to English if current language was removed
            if self.db.speaking_language not in new_languages:
                self.db.speaking_language = "English"
            
            # Notify the character with more detail
            removed_languages = set(current_languages) - set(new_languages)
            self.msg(f"Your language merit points have been reduced to {language_points}. "
                    f"The following languages have been removed: {', '.join(removed_languages)}\n"
                    f"Your known languages are now: {', '.join(new_languages)}")
        
        # If Natural Linguist was removed, update the display
        if not natural_linguist and len(current_languages) > 1:
            self.msg(f"Natural Linguist merit removed. Your current language points: {language_points}")

    def update_merit(self, merit_name, new_value):
        """Update a merit's value and validate languages if necessary."""
        old_value = self.db.stats.get('merits', {}).get(merit_name, 0)
        
        # Update the merit value
        # ... your existing merit update code ...
        
        # If it's a language-related merit, validate languages
        if (merit_name == 'Language' or 
            merit_name.startswith('Language(') or 
            merit_name == 'Natural Linguist'):
            # Import the command
            from commands.CmdLanguage import CmdLanguage
            cmd = CmdLanguage()
            cmd.caller = self
            if cmd.validate_languages():
                cmd.list_languages()

    def can_see_languages(self, viewer):
        """
        Determine if the viewer can see this character's languages.
        
        Args:
            viewer (Object): The character/account trying to view languages
            
        Returns:
            bool: True if viewer can see languages, False otherwise
        """
        # Admin and Builder staff can always see languages
        if viewer.check_permstring("builders") or viewer.check_permstring("admin"):
            return True
            
        # Character can see their own languages
        if viewer == self:
            return True
            
        # Characters in same room can see languages if character is speaking
        if viewer.location == self.location:
            return True
            
        return False

    def add_xp(self, amount, reason="Weekly XP", approved_by=None):
        """Add XP to the character."""
        try:
            # Initialize XP if not exists
            if not hasattr(self.db, 'xp') or not self.db.xp:
                self.db.xp = {
                    'total': Decimal('0.00'),
                    'current': Decimal('0.00'),
                    'spent': Decimal('0.00'),
                    'ic_xp': Decimal('0.00'),
                    'monthly_spent': Decimal('0.00'),
                    'last_reset': datetime.now(),
                    'spends': [],
                    'last_scene': None,
                    'scenes_this_week': 0
                }

            xp_amount = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
            self.db.xp['total'] += xp_amount
            self.db.xp['current'] += xp_amount
            
            # Log the award
            timestamp = datetime.now()
            award = {
                'type': 'award',
                'amount': float(xp_amount),
                'reason': reason,
                'approved_by': approved_by.key if approved_by else 'System',
                'timestamp': timestamp.isoformat()
            }
            
            self.db.xp['spends'].insert(0, award)
            self.db.xp['spends'] = self.db.xp['spends'][:10]
            
            return True
        except Exception as e:
            self.msg(f"Error adding XP: {str(e)}")
            return False

    def spend_xp(self, amount, reason, approved_by=None):
        """
        Spend XP from the character's pool.
        
        Args:
            amount (float): Amount of XP to spend
            reason (str): What the XP was spent on
            approved_by (Object): Staff member who approved the spend
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert to Decimal and round to 2 decimal places
            xp_amount = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
            
            # Check if character has enough XP
            if self.db.xp['current'] < xp_amount:
                return False
            
            # Check monthly spend limit unless staff approved
            if not approved_by:
                # Reset monthly spent if it's been a month
                if datetime.now() - self.db.xp['last_reset'] > timedelta(days=30):
                    self.db.xp['monthly_spent'] = Decimal('0.00')
                    self.db.xp['last_reset'] = datetime.now()
                
                # Check if this would exceed monthly limit
                if self.db.xp['monthly_spent'] + xp_amount > Decimal('20.00'):
                    return False
                
                self.db.xp['monthly_spent'] += xp_amount
            
            # Update XP totals
            self.db.xp['current'] -= xp_amount
            self.db.xp['spent'] += xp_amount
            
            # Log the spend
            timestamp = datetime.now()
            spend = {
                'type': 'spend',
                'amount': float(xp_amount),
                'reason': reason,
                'approved_by': approved_by.key if approved_by else None,
                'timestamp': timestamp.isoformat()
            }
            
            # Add to spends list
            self.db.xp['spends'].insert(0, spend)
            
            # Keep only last 10 entries
            self.db.xp['spends'] = self.db.xp['spends'][:10]
            
            return True
        except (ValueError, TypeError, InvalidOperation):
            return False

    def record_scene_participation(self):
        """Record that the character participated in an IC scene."""
        now = datetime.now()
        
        # If it's been more than a week since last scene, reset counter
        if self.db.xp['last_scene']:
            last_scene = datetime.fromisoformat(self.db.xp['last_scene'])
            if now - last_scene > timedelta(days=7):
                self.db.xp['scenes_this_week'] = 0
        
        self.db.xp['last_scene'] = now.isoformat()
        self.db.xp['scenes_this_week'] += 1

    def start_scene(self):
        """Start tracking a new scene."""
        now = datetime.now()
        self.db.scene_data['current_scene'] = now
        self.db.scene_data['scene_location'] = self.location
        self.db.scene_data['last_activity'] = now

    def end_scene(self):
        """End current scene and check if it counts."""
        
        if not self.db.scene_data['current_scene']:
            self.msg("|rNo current scene to end.|n")
            return False

        now = datetime.now()
        scene_start = self.db.scene_data['current_scene']
        last_activity = self.db.scene_data['last_activity']

        # Check if scene meets duration requirement (20 minutes)
        duration = (now - scene_start).total_seconds() / 60

        if duration >= 20:  # Scene must be 20+ mins
            self.db.scene_data['completed_scenes'] += 1
            self.msg(f"|gScene completed and counted! Total completed scenes: {self.db.scene_data['completed_scenes']}|n")
        else:
            self.msg(f"|rScene too short to count ({int(duration)} minutes - needs 20+)|n")
            
        # Reset scene tracking
        self.db.scene_data['current_scene'] = None
        self.db.scene_data['scene_location'] = None
        self.db.scene_data['last_activity'] = None

        return True

    def check_scene_status(self):
        """Check if we should start/continue/end a scene."""
        # Ensure scene_data exists
        if not hasattr(self.db, 'scene_data') or not self.db.scene_data:
            self.db.scene_data = {
                'current_scene': None,
                'scene_location': None,
                'last_activity': None,
                'completed_scenes': 0,
                'last_weekly_reset': datetime.now()
            }

        now = datetime.now()
        
        # Check for weekly reset
        if self.db.scene_data['last_weekly_reset']:
            days_since_reset = (now - self.db.scene_data['last_weekly_reset']).days
            if days_since_reset >= 7:
                old_count = self.db.scene_data['completed_scenes']
                self.db.scene_data['completed_scenes'] = 0
                self.db.scene_data['last_weekly_reset'] = now
      # If not in a valid scene location, end any current scene
        if not self.location or not self.is_valid_scene_location():
            if self.db.scene_data['current_scene']:
                self.end_scene()
            return

        # If in a new location, end current scene and start new one
        if (self.db.scene_data['scene_location'] and 
            self.db.scene_data['scene_location'] != self.location):
            self.end_scene()
            self.start_scene()
            return

        # If not in a scene but in valid location, start one
        if not self.db.scene_data['current_scene']:
            self.start_scene()

    def is_valid_scene_location(self):
        """Check if current location is valid for scene tracking."""
        if not self.location:
            return False
            
        # Must be IC room
        if (hasattr(self.location, 'db') and 
            getattr(self.location.db, 'roomtype', None) == 'OOC Area'):
            return False
            
        # Must have other players present
        other_players = [
            obj for obj in self.location.contents 
            if (obj != self and 
                hasattr(obj, 'has_account') and 
                obj.has_account and
                obj.db.in_umbra == self.db.in_umbra)  # Must be in same realm
        ]
        
        valid = len(other_players) > 0

    def record_scene_activity(self):
        """Record activity in current scene."""
        now = datetime.now()

        # Initialize scene_data if it doesn't exist
        if not hasattr(self.db, 'scene_data') or not self.db.scene_data:
            self.db.scene_data = {
                'current_scene': None,
                'scene_location': None,
                'last_activity': None,
                'completed_scenes': 0,
                'last_weekly_reset': datetime.now()
            }

        self.check_scene_status()
        if self.db.scene_data['current_scene']:
            self.db.scene_data['last_activity'] = now

    def at_say(self, message, msg_self=None, msg_location=None, receivers=None, msg_receivers=None, **kwargs):
        """Hook method for the say command."""
        super().at_say(message, msg_self, msg_location, receivers, msg_receivers, **kwargs)
        self.record_scene_activity()

    def at_pose(self, pose_understand, pose_not_understand, pose_self, speaking_language):
        """Handle poses."""
        super().at_pose(pose_understand, pose_not_understand, pose_self, speaking_language)
        self.record_scene_activity()

    def at_emote(self, message, msg_self=None, msg_location=None, receivers=None, msg_receivers=None, **kwargs):
        """Display an emote to the room."""
        super().at_emote(message, msg_self, msg_location, receivers, msg_receivers, **kwargs)
        self.record_scene_activity()

    def at_init(self):
        """
        Called when object is first created and after each server reload.
        """
        super().at_init()
        
        # Initialize scene_data if it doesn't exist
        if not hasattr(self.db, 'scene_data'):
            self.db.scene_data = {
                'current_scene': None,  # Will store start time of current scene
                'scene_location': None, # Location where scene started
                'last_activity': None,  # Last time character was active in scene
                'completed_scenes': 0,  # Number of completed scenes this week
                'last_weekly_reset': datetime.now()  # For weekly scene count reset
            }

    def init_scene_data(self):
        """Force initialize scene data."""
        self.db.scene_data = {
            'current_scene': None,
            'scene_location': None,
            'last_activity': None,
            'completed_scenes': 0,
            'last_weekly_reset': datetime.now()
        }
        self.msg("|wScene data initialized.|n")

    def calculate_xp_cost(self, stat_name, new_rating, category=None, current_rating=None, subcategory=None):
        """Calculate XP cost for increasing a stat."""
        if current_rating is None:
            current_rating = self.get_stat(category, subcategory, stat_name) or 0
        
        splat = self.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        shifter_type = self.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '')
        
        # Initialize cost and requires_approval
        cost = 0
        requires_approval = False

        # Can't decrease stats via XP
        if new_rating <= current_rating:
            return (0, False)

        # Calculate base cost based on stat type
        if category == 'attributes':
            # First dot is free, then current rating × 4
            if current_rating == 0:
                cost = sum(i * 4 for i in range(1, new_rating))
            else:
                cost = sum(i * 4 for i in range(current_rating, new_rating))
            requires_approval = new_rating > 3

        elif category == 'abilities':
            if subcategory in ['talent', 'skill', 'knowledge', 'secondary_talent', 'secondary_skill', 'secondary_knowledge']:
                if current_rating == 0:
                    cost = 3 + sum(i * 2 for i in range(1, new_rating))
                else:
                    cost = sum(i * 2 for i in range(current_rating + 1, new_rating + 1))
                requires_approval = new_rating > 3

        elif category == 'powers' and splat == 'Shifter':
            # Handle different shifter types
            if shifter_type == 'Garou':
                breed = self.db.stats.get('identity', {}).get('lineage', {}).get('Breed', {}).get('perm', '')
                tribe = self.db.stats.get('identity', {}).get('lineage', {}).get('Tribe', {}).get('perm', '')
                auspice = self.db.stats.get('identity', {}).get('lineage', {}).get('Auspice', {}).get('perm', '')
                
                # Check if it's a breed/auspice/tribe gift
                is_breed_gift = f"Breed: {breed}" in stat_name
                is_tribe_gift = f"Tribe: {tribe}" in stat_name
                is_auspice_gift = f"Auspice: {auspice}" in stat_name
                
                if is_breed_gift or is_tribe_gift or is_auspice_gift:
                    cost = new_rating * 3  # Gift Level * 3
                else:
                    cost = new_rating * 5  # Gift Level * 5 for outside gifts
                
                requires_approval = new_rating > 1  # Only level 1 gifts without approval
                
            elif shifter_type in ['Bastet', 'Corax', 'Gurahl', 'Kitsune', 'Mokole', 'Nagah', 'Nuwisha', 'Ratkin', 'Rokea', 'Ajaba', 'Ananasi', 'Camazotz']:
                # Other shifter types might have different costs or approval requirements
                # For now, using same base structure as Garou
                cost = new_rating * 4  # Different base cost for other shifter types
                requires_approval = new_rating > 1

        elif category == 'pools' and stat_name in ['Willpower', 'Rage', 'Gnosis']:
            if stat_name == 'Willpower':
                cost = sum(range(current_rating + 1, new_rating + 1))
                requires_approval = new_rating > 5
            elif stat_name in ['Rage', 'Gnosis'] and splat == 'Shifter':
                if stat_name == 'Rage':
                    cost = sum(range(current_rating + 1, new_rating + 1))
                else:  # Gnosis
                    cost = sum(i * 2 for i in range(current_rating + 1, new_rating + 1))
                requires_approval = new_rating > 5

        elif category == 'backgrounds':
            cost = (new_rating - current_rating) * 5
            auto_approve_backgrounds = [
                'Resources', 'Contacts', 'Allies', 'Backup', 
                'Herd', 'Library', 'Kinfolk', 'Spirit Heritage'
            ]
            requires_approval = (
                stat_name not in auto_approve_backgrounds or 
                new_rating > 2
            )

        elif category == 'powers':
            if splat == 'Vampire':
                clan = self.db.stats.get('identity', {}).get('lineage', {}).get('Clan', {}).get('perm', '')
                
                # Determine if discipline is in-clan
                is_in_clan = self._is_discipline_in_clan(stat_name, clan)
                is_caitiff = clan == 'Caitiff'
                
                # First dot costs 10 XP for all types
                if current_rating == 0:
                    cost = 10
                    if new_rating > 1:
                        # Add costs for additional dots
                        if is_in_clan:
                            cost += sum(i * 5 for i in range(1, new_rating))
                        elif is_caitiff:
                            cost += sum(i * 6 for i in range(1, new_rating))
                        else:  # Out of clan
                            cost += sum(i * 7 for i in range(1, new_rating))
                else:
                    # Just adding dots beyond the first
                    if is_in_clan:
                        cost = sum(i * 5 for i in range(current_rating, new_rating))
                    elif is_caitiff:
                        cost = sum(i * 6 for i in range(current_rating, new_rating))
                    else:  # Out of clan
                        cost = sum(i * 7 for i in range(current_rating, new_rating))
                
                requires_approval = new_rating > 2

            elif splat == 'Mage':
                # Check if it's an affinity sphere
                is_affinity = self._is_affinity_sphere(stat_name)
                
                if current_rating == 0:
                    cost = 10  # First dot always costs 10
                    if new_rating > 1:
                        # Add costs for additional dots
                        if is_affinity:
                            cost += sum(i * 7 for i in range(1, new_rating))
                        else:
                            cost += sum(i * 8 for i in range(1, new_rating))
                else:
                    # Just adding dots beyond the first
                    if is_affinity:
                        cost = sum(i * 7 for i in range(current_rating, new_rating))
                    else:
                        cost = sum(i * 8 for i in range(current_rating, new_rating))
                
                requires_approval = new_rating > 2

            elif splat == 'Changeling':
                is_art = stat_name.startswith('Art:')
                is_realm = stat_name.startswith('Realm:')
                
                if is_art:
                    if current_rating == 0:
                        cost = 3  # First dot costs 3
                        if new_rating > 1:
                            cost += sum(i * 4 for i in range(1, new_rating))
                    else:
                        cost = sum(i * 4 for i in range(current_rating, new_rating))
                
                elif is_realm:
                    if current_rating == 0:
                        cost = 5  # First dot costs 5
                        if new_rating > 1:
                            cost += sum(i * 3 for i in range(1, new_rating))
                    else:
                        cost = sum(i * 3 for i in range(current_rating, new_rating))
                
                requires_approval = new_rating > 2

        return (cost, requires_approval)

    def _is_discipline_in_clan(self, discipline, clan):
        """Helper method to check if a discipline is in-clan."""
        # general disciplines that any vampire can learn as if in-clan, basically the physical ones
        GENERAL_DISCIPLINES = ['Potence', 'Celerity', 'Fortitude', 'Auspex']
        
        # clan-specific
        clan_disciplines = {
            'Brujah': ['Celerity', 'Potence', 'Presence'],
            'Gangrel': ['Animalism', 'Fortitude', 'Protean'],
            'Malkavian': ['Auspex', 'Obfuscate', 'Dementation'],
            'Nosferatu': ['Potence', 'Animalism', 'Obfuscate'],
            'Tremere': ['Thaumaturgy', 'Dominate', 'Auspex'],
            'Tzimisce': ['Vicissitude', 'Auspex', 'Animalism'],
            'Ventrue': ['Dominate', 'Fortitude', 'Presence'],
            'Lasombra': ['Dominate', 'Obtenebration', 'Potence'],
            'Toreador': ['Auspex', 'Presence', 'Celerity'],
            'Followers of Set': ['Obfuscate', 'Presence', 'Serpentis'],
            'Ravnos': ['Animalism', 'Chimerstry', 'Fortitude'],
            'Giovanni': ['Dominate', 'Necromancy', 'Potence'],
            'Caitiff': GENERAL_DISCIPLINES,  # caitiff can learn general disciplines as in-clan
            'City Gangrel': ['Celerity', 'Fortitude', 'Protean']
        }
        
        # Check if it's a general discipline or in-clan discipline
        return (discipline in GENERAL_DISCIPLINES or 
                (clan in clan_disciplines and discipline in clan_disciplines[clan]))

    def _is_affinity_sphere(self, sphere):
        """Helper method to check if a sphere is an affinity sphere."""
        affinity_sphere = self.db.stats.get('other', {}).get('affinity_sphere', {}).get('Affinity_Sphere', {}).get('perm', '')
        return sphere in affinity_sphere

    def can_buy_stat(self, stat_name, new_rating, category=None):
        """Check if a stat can be bought without staff approval."""
        # Get character's splat
        splat = self.db.stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', '')
        if not splat:
            return (False, "Character splat not set")

        # Basic validation
        if category == 'abilities':
            # For abilities, we need to determine the subcategory (talent/skill/knowledge)
            for subcat in ['talent', 'skill', 'knowledge']:
                current_rating = (self.db.stats.get('abilities', {})
                                .get(subcat, {})
                                .get(stat_name, {})
                                .get('perm', 0))
                if current_rating:  # Found the ability
                    break
        else:
            current_rating = self.get_stat(category, None, stat_name) or 0

        if new_rating <= current_rating:
            return (False, "New rating must be higher than current rating")

        # Auto-approve list for each splat
        AUTO_APPROVE = {
            'all': {
                'attributes': 3,  # All attributes up to 3
                'abilities': 3,   # All abilities up to 3
                'backgrounds': {   # Specific backgrounds up to 2
                    'Resources': 2,
                    'Contacts': 2,
                    'Allies': 2,
                    'Backup': 2,
                    'Herd': 2,
                    'Library': 2
                },
                'willpower': {     # Willpower limits by splat
                    'Mage': 6,
                    'default': 5
                }
            },
            'Vampire': {
                'powers': {        # Disciplines up to 2
                    'max': 2,
                    'types': ['Discipline']
                }
            },
            'Mage': {
                'powers': {        # Spheres up to 2
                    'max': 2,
                    'types': ['Sphere']
                }
            },
            'Changeling': {
                'powers': {        # Arts and Realms up to 2
                    'max': 2,
                    'types': ['Art', 'Realm']
                }
            },
            'Shifter': {
                'powers': {        # Level 1 Gifts only
                    'max': 1,
                    'types': ['Gift']
                }
            }
        }

        # Check category-specific limits
        if category == 'attributes' and new_rating <= AUTO_APPROVE['all']['attributes']:
            return (True, None)
            
        if category == 'abilities' and new_rating <= AUTO_APPROVE['all']['abilities']:
            return (True, None)
            
        if category == 'backgrounds':
            max_rating = AUTO_APPROVE['all']['backgrounds'].get(stat_name)
            if max_rating and new_rating <= max_rating:
                return (True, None)
                
        if stat_name == 'Willpower':
            max_willpower = AUTO_APPROVE['all']['willpower'].get(splat, 
                          AUTO_APPROVE['all']['willpower']['default'])
            if new_rating <= max_willpower:
                return (True, None)
                
        if category == 'powers' and splat in AUTO_APPROVE:
            power_rules = AUTO_APPROVE[splat]['powers']
            # Check if it's the right type of power for the splat
            power_type = self._get_power_type(stat_name)
            if (power_type in power_rules['types'] and 
                new_rating <= power_rules['max']):
                return (True, None)

        return (False, "Requires staff approval")

    def _get_power_type(self, stat_name):
        """Helper method to determine power type from name."""
        if stat_name.startswith('Gift:'):
            return 'Gift'
        elif stat_name.startswith('Discipline:'):
            return 'Discipline'
        elif stat_name.startswith('Sphere:'):
            return 'Sphere'
        elif stat_name.startswith('Art:'):
            return 'Art'
        elif stat_name.startswith('Realm:'):
            return 'Realm'
        return None

    def ensure_stat_structure(self, category, subcategory):
        """Ensure the proper nested structure exists for stats."""
        if not hasattr(self.db, 'stats'):
            self.db.stats = {}
        
        if category not in self.db.stats:
            self.db.stats[category] = {}
        
        if subcategory and subcategory not in self.db.stats[category]:
            self.db.stats[category][subcategory] = {}
        
        return True

    def buy_stat(self, stat_name, new_rating, category=None, subcategory=None, reason=""):
        """Buy or increase a stat with XP."""
        try:
            # Ensure proper structure exists
            self.ensure_stat_structure(category, subcategory)
            
            # Get current permanent rating (not temporary/shifted rating)
            if category and subcategory:
                current_rating = (self.db.stats.get(category, {})
                                .get(subcategory, {})
                                .get(stat_name, {})
                                .get('perm', 0))
            else:
                current_rating = 0
            
            # Calculate cost
            cost, requires_approval = self.calculate_xp_cost(
                stat_name, 
                new_rating, 
                category=category,
                subcategory=subcategory,
                current_rating=current_rating
            )
            
            if cost == 0:
                return False, "Invalid stat or no increase needed"
            
            if requires_approval:
                return False, "This purchase requires staff approval"
            
            # Check if we have enough XP
            if self.db.xp['current'] < cost:
                return False, f"Not enough XP. Cost: {cost}, Available: {self.db.xp['current']}"
            
            # Get the current form and any modifiers
            current_form = self.db.current_form
            form_modifier = 0
            if current_form and current_form.lower() != 'homid':
                try:
                    from world.wod20th.models import ShapeshifterForm
                    # Get character's shifter type
                    shifter_type = self.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm', '').lower()
                    
                    # Query form by both name and shifter type
                    form = ShapeshifterForm.objects.get(
                        name__iexact=current_form,
                        shifter_type=shifter_type
                    )
                    form_modifier = form.stat_modifiers.get(stat_name.lower(), 0)
                    
                    # Special handling for stats that should be set to 0 in certain forms
                    zero_appearance_forms = [
                        'crinos',      # All shapeshifters
                        'anthros',     # Ajaba war form
                        'arthren',     # Gurahl war form
                        'sokto',       # Bastet war form
                        'chatro'       # Bastet battle form
                    ]
                    if (stat_name.lower() == 'appearance' and 
                        current_form.lower() in zero_appearance_forms):
                        form_modifier = -999  # Force to 0
                    elif (stat_name.lower() == 'manipulation' and 
                          current_form.lower() == 'crinos'):
                        form_modifier = -2  # Crinos form penalty
                    
                except (ShapeshifterForm.DoesNotExist, AttributeError) as e:
                    print(f"DEBUG: Form lookup error - {str(e)}")
                    form_modifier = 0
            
            # Update the permanent stat value
            if category and subcategory:
                if stat_name not in self.db.stats[category][subcategory]:
                    self.db.stats[category][subcategory][stat_name] = {}
                
                # Set the permanent value
                self.db.stats[category][subcategory][stat_name]['perm'] = new_rating
                
                # Calculate temporary value with form modifier
                if form_modifier == -999:  # Special case for forced 0
                    temp_value = 0
                else:
                    temp_value = max(0, new_rating + form_modifier)  # Ensure non-negative
                
                self.db.stats[category][subcategory][stat_name]['temp'] = temp_value
            
            # Deduct XP
            self.db.xp['current'] -= Decimal(str(cost))
            self.db.xp['spent'] += Decimal(str(cost))
            
            # Log the spend
            timestamp = datetime.now()
            spend = {
                'type': 'spend',
                'amount': float(cost),
                'reason': f"{stat_name} ({current_rating} -> {new_rating})",
                'approved_by': 'System',
                'timestamp': timestamp.isoformat()
            }
            
            if not self.db.xp.get('spends'):
                self.db.xp['spends'] = []
            self.db.xp['spends'].insert(0, spend)
            self.db.xp['spends'] = self.db.xp['spends'][:10]  # Keep only last 10 entries
            
            return True, f"Successfully bought {stat_name} {new_rating} for {cost} XP"
            
        except Exception as e:
            return False, f"Error buying stat: {str(e)}"

    def _display_xp(self, character):
        """Displays XP information for a character."""
        xp = character.db.xp
        if not xp:
            # Initialize XP if it doesn't exist
            xp = {
                'total': Decimal('0.00'),
                'current': Decimal('0.00'),
                'spent': Decimal('0.00'),
                'ic_xp': Decimal('0.00'),
                'monthly_spent': Decimal('0.00'),
                'last_reset': datetime.now(),
                'spends': [],
                'last_scene': None,
                'scenes_this_week': 0
            }
            character.db.xp = xp
            
        total_width = 78
            
        # Header
        title = f" {character.name}'s XP "
        title_len = len(title)
        dash_count = (total_width - title_len) // 2
        header = f"{'|b-|n' * dash_count}{title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
        
        # XP section
        exp_title = "|y Experience Points |n"
        title_len = len(exp_title)
        dash_count = (total_width - title_len) // 2
        exp_header = f"{'|b-|n' * dash_count}{exp_title}{'|b-|n' * (total_width - dash_count - title_len)}\n"
        
        # XP value formatting
        left_col_width = 20  
        right_col_width = 12 
        spacing = " " * 14  # column spacing
        
        # Format columns
        ic_xp = f"{'|wIC XP:|n':<{left_col_width}}{xp['total'] - xp['current']:>{right_col_width}.2f}"
        total_xp = f"{'|wTotal XP:|n':<{left_col_width}}{xp['total']:>{right_col_width}.2f}"
        current_xp = f"{'|wCurrent XP:|n':<{left_col_width}}{xp['current']:>{right_col_width}.2f}"
        award_xp = f"{'|wAward XP:|n':<{left_col_width}}{xp['current']:>{right_col_width}.2f}"
        spent_xp = f"{'|wSpent XP:|n':<{left_col_width}}{xp['spent']:>{right_col_width}.2f}"
        
        # Combine XP section
        exp_section = f"{ic_xp}{spacing}{award_xp}\n"
        exp_section += f"{total_xp}{spacing}{spent_xp}\n"
        exp_section += f"{current_xp}\n"
        
        # Recent activity section
        activity_title = "|y Recent Activity |n"
        activity_title_len = len(activity_title)
        activity_dash_count = (total_width - activity_title_len) // 2
        activity_header = f"{'|b-|n' * activity_dash_count}{activity_title}{'|b-|n' * (total_width - activity_dash_count - activity_title_len)}\n"
        
        # Format recent activity
        activity_section = ""
        if xp.get('spends'):
            for entry in xp['spends']:
                timestamp = datetime.fromisoformat(entry['timestamp'])
                if entry['type'] == 'spend':
                    activity_section += (
                        f"{timestamp.strftime('%Y-%m-%d %H:%M')} - "
                        f"Spent {entry['amount']:.2f} XP on {entry['reason']}\n"
                    )
                else:
                    activity_section += (
                        f"{timestamp.strftime('%Y-%m-%d %H:%M')} - "
                        f"Received {entry['amount']:.2f} XP ({entry['reason']})\n"
                    )
        else:
            activity_section = "No XP history yet.\n"
        
        footer = f"{'|b-|n' * total_width}"
        
        # Add scene tracking status if available
        scene_data = character.db.scene_data
        if scene_data:
            scene_title = "|y Scene Status |n"
            scene_title_len = len(scene_title)
            scene_dash_count = (total_width - scene_title_len) // 2
            scene_header = f"{'|b-|n' * scene_dash_count}{scene_title}{'|b-|n' * (total_width - scene_dash_count - scene_title_len)}\n"
            
            scene_section = ""
            if scene_data['current_scene']:
                duration = (datetime.now() - scene_data['current_scene']).total_seconds() / 60
                scene_section += f"Current scene duration: {int(duration)} minutes\n"
                if scene_data['last_activity']:
                    last_activity = (datetime.now() - scene_data['last_activity']).total_seconds() / 60
                    scene_section += f"Last activity: {int(last_activity)} minutes ago\n"
            else:
                scene_section += "No active scene\n"
            
            scene_section += f"Completed scenes this week: {scene_data['completed_scenes']}\n"
            
            display = (
                header +
                exp_header +
                exp_section +
                activity_header +
                activity_section +
                scene_header +
                scene_section +
                footer
            )
        else:
            display = (
                header +
                exp_header +
                exp_section +
                activity_header +
                activity_section +
                footer
            )
        
        return display

    def award_ic_xp(self, amount=4):
        """Award IC XP for completing weekly scenes."""
        try:
            xp_amount = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
            self.db.xp['total'] += xp_amount
            self.db.xp['current'] += xp_amount
            self.db.xp['ic_xp'] += xp_amount
            
            # Log the award
            timestamp = datetime.now()
            award = {
                'type': 'award',
                'amount': float(xp_amount),
                'reason': "Weekly IC XP",
                'approved_by': 'System',
                'timestamp': timestamp.isoformat()
            }
            
            self.db.xp['spends'].insert(0, award)
            self.db.xp['spends'] = self.db.xp['spends'][:10]
            
            return True
        except Exception as e:
            self.msg(f"Error awarding IC XP: {str(e)}")
            return False

    def at_pre_channel_msg(self, message, channel, senders=None, **kwargs):
        """
        Called before a character receives a message from a channel.
        
        Args:
            message (str): The message to be received
            channel (Channel): The channel the message is from
            senders (list): List of senders who should receive the message
            
        Returns:
            message (str or None): The processed message or None to abort receiving
        """
        return self.account.at_pre_channel_msg(message, channel, senders, **kwargs)

    def channel_msg(self, message, channel, senders=None, **kwargs):
        """
        Called when a character receives a message from a channel.
        
        Args:
            message (str): The message received
            channel (Channel): The channel the message is from
            senders (list): List of senders who should receive the message
        """
        self.account.channel_msg(message, channel, senders, **kwargs)

    def at_post_channel_msg(self, message, channel, senders=None, **kwargs):
        """
        Called after a character has received a message from a channel.
        
        Args:
            message (str): The message received
            channel (Channel): The channel the message is from
            senders (list): List of senders who should receive the message
        """
        return self.account.at_post_channel_msg(message, channel, senders, **kwargs)

    def del_stat(self, stat_type, category, stat_name, temp=False):
        """Delete a stat value."""
        # Handle attributes by using their category as the stat_type
        if stat_type == 'attributes':
            stat_type = category  # Use physical/social/mental as the stat_type
            category = 'attributes'  # Set category to 'attributes'

        # Check if the stat exists
        if (stat_type in self.db.stats and 
            category in self.db.stats[stat_type] and 
            stat_name in self.db.stats[stat_type][category]):
            if temp:
                # Only delete the temporary value
                if 'temp' in self.db.stats[stat_type][category][stat_name]:
                    del self.db.stats[stat_type][category][stat_name]['temp']
            else:
                # Delete the entire stat entry
                del self.db.stats[stat_type][category][stat_name]
            return True
        return False

class Note:
    def __init__(self, name, text, category="General", is_public=False, is_approved=False, 
                 approved_by=None, approved_at=None, created_at=None, updated_at=None, note_id=None):
        self.name = name
        self.text = text
        self.category = category
        self.is_public = is_public
        self.is_approved = is_approved
        self.approved_by = approved_by
        self.approved_at = approved_at
        self.created_at = created_at if isinstance(created_at, datetime) else datetime.now()
        self.updated_at = updated_at if isinstance(updated_at, datetime) else datetime.now()
        self.note_id = note_id

    @property
    def id(self):
        """For backwards compatibility"""
        return self.note_id

    def to_dict(self):
        return {
            'name': self.name,
            'text': self.text,
            'category': self.category,
            'is_public': self.is_public,
            'is_approved': self.is_approved,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'note_id': self.note_id
        }

    @classmethod
    def from_dict(cls, data):
        # Handle SaverDict by creating a new dict with its items
        note_data = {k: v for k, v in data.items()}
        
        # Convert datetime strings back to datetime objects
        for field in ['created_at', 'updated_at', 'approved_at']:
            if note_data.get(field):
                try:
                    if isinstance(note_data[field], str):
                        note_data[field] = datetime.fromisoformat(note_data[field])
                except (ValueError, TypeError):
                    note_data[field] = None
            else:
                note_data[field] = None
                
        return cls(**note_data)
