from evennia import default_cmds, utils
from evennia.utils import evtable
from evennia.utils.utils import make_iter
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.utils import crop
from evennia.utils.ansi import ANSIString
from world.wod20th.utils.ansi_utils import wrap_ansi
from world.wod20th.utils.formatting import header, footer, divider, format_stat
from collections import defaultdict
from django.utils import timezone
from evennia import logger
from evennia import search_object
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
from typeclasses.characters import Note

class CmdNotes(MuxCommand):
    """
    Manage character notes.

    Usage:
      +notes                      - see all your notes
      +note <note name or number> - see your note
      +note/<category>            - see all your notes in a category
      +note/decompile <note(s)>   - get the raw text that created the note
      +note <target>/*            - see all visible notes on someone else
      +note <target>/<note>       - see a note on someone else
      +note <target>/<category> - see all notes on someone else in a category
      +note/create <n>=<text>  - make a note called <n>
      +note/create <category>/<n>=<text> - make a note in a specific category
      +note/set <target>/<n>=<text> - make a note on another character (staff only)
      +note/edit <note>=<new text> - change the text on a note, removes approval
      +note/move <note>=<category> - move a note to a new category, keeps approval
      +note/status <note>=PRIVATE|PUBLIC - make a note in-/visible to others
      +note/private <note>        - shortcut to make a note private
      +note/public <note>         - shortcut to make a note public
      +note/prove <note>=<target(s)> - show any note to a list of targets
      +note/approve[/<category>] <target>/<note> - approve a note (staff only)
      +note/unapprove[/<category>] <target>/<note> - unapprove a note (staff only)
      +note/delete <note>         - delete one of your notes
      +note/delete <target>=<note> - delete someone else's note (staff only)

      Sample categories: General, Story, Merit, Flaw, Rote, Magick, NPC, Background
      Combo Discipline, Ritual (use for Sabbat or Shifter)
    """

    key = "+note"
    aliases = ["+notes"]
    locks = "cmd:all()"
    help_category = "Chargen & Character Info"

    def search_for_character(self, search_string):
        """Search for a character globally."""
        # First try exact match
        char = self.caller.search(search_string, global_search=True, typeclass="typeclasses.characters.Character")
        if not char:
            return None
            
        # If we got a list, try to find exact match by name
        if isinstance(char, list):
            for result in char:
                if result.key.lower() == search_string.lower():
                    return result
            # If no exact match found, return the first result
            return char[0]
            
        return char

    def func(self):
        if not self.args and not self.switches:
            self.list_notes()
            return

        if self.switches:
            switch = self.switches[0].lower()
            if switch == "create":
                self.create_note()
            elif switch == "set":
                self.set_note()
            elif switch == "edit":
                self.edit_note()
            elif switch == "status":
                self.change_note_status()
            elif switch == "decompile":
                self.decompile_note()
            elif switch == "move":
                self.move_note()
            elif switch == "private":
                self.args = f"{self.args}=PRIVATE"
                self.change_note_status()
            elif switch == "public":
                self.args = f"{self.args}=PUBLIC"
                self.change_note_status()
            elif switch == "prove":
                self.prove_note()
            elif switch == "approve":
                self.approve_note()
            elif switch == "unapprove":
                self.unapprove_note()
            elif switch in ["delete", "del"]:
                self.delete_note()
            elif switch == "debug":
                # Debug note data
                target_name = self.args.strip()
                if not target_name:
                    target = self.caller
                else:
                    target = self.search_for_character(target_name)
                    if not target:
                        self.caller.msg(f"Could not find character '{target_name}'.")
                        return
                
                # Get raw note data
                notes_data = target.attributes.get('notes', {})
                self.caller.msg(f"Raw notes data type: {type(notes_data)}")
                self.caller.msg(f"Raw notes data: {notes_data}")
                
                # Try conversion
                try:
                    converted = self._convert_notes_to_dict(notes_data)
                    self.caller.msg(f"Converted data type: {type(converted)}")
                    self.caller.msg(f"Converted data: {converted}")
                except Exception as e:
                    self.caller.msg(f"Conversion error: {e}")
            elif switch == "fix":
                # Handle fixing notes
                target_name = self.args.strip()
                if not target_name:
                    target = self.caller
                else:
                    target = self.search_for_character(target_name)
                    if not target:
                        self.caller.msg(f"Could not find character '{target_name}'.")
                        return
                
                if self.fix_notes(target):
                    self.caller.msg(f"Successfully fixed notes for {target.name}.")
                else:
                    self.caller.msg(f"Failed to fix notes for {target.name}.")
            else:
                self.caller.msg(f"Unknown switch: {switch}")
        else:
            # View a specific note
            self.view_note()

    def parse_date(self, date_value):
        """Helper method to parse dates from various formats."""
        if not date_value:
            return None
            
        # If it's already a datetime object, return it
        if isinstance(date_value, datetime):
            return date_value
            
        # If it's a string, try various formats
        if isinstance(date_value, str):
            # List of possible date formats to try
            formats = [
                "%Y-%m-%dT%H:%M:%S.%f",  # ISO format with microseconds
                "%Y-%m-%dT%H:%M:%S",     # ISO format without microseconds
                "%Y-%m-%d %H:%M:%S.%f",  # Standard format with microseconds
                "%Y-%m-%d %H:%M:%S",     # Standard format without microseconds
                "%Y-%m-%d",              # Date only
            ]
            
            # Try each format
            for fmt in formats:
                try:
                    return datetime.strptime(date_value, fmt)
                except ValueError:
                    continue
                    
            # If none of the formats work, try parsing as ISO format
            try:
                return datetime.fromisoformat(date_value)
            except ValueError:
                pass
                
            # Log the unparseable date
            logger.log_trace(f"Could not parse date value: {date_value}")
            
        return None

    def fix_notes(self, target):
        """Fix corrupted notes data format."""
        try:
            # Get the raw attribute data
            raw_notes = target.attributes.get('notes', {})
            logger.log_info(f"Fixing notes for {target.name}, data type: {type(raw_notes)}")
            
            # Convert notes to dictionary format
            notes_dict = self._convert_notes_to_dict(raw_notes)
            
            # If we got a valid dictionary with notes, process and clean it
            if notes_dict:
                logger.log_info(f"Successfully converted notes for {target.name}, found {len(notes_dict)} notes")
                cleaned_notes = {}
                
                # Process each note
                for note_id, note_data in notes_dict.items():
                    try:
                        # Ensure all required fields are present with proper types
                        cleaned_note = {
                            'name': str(note_data.get('name', 'Unnamed Note')),
                            'text': str(note_data.get('text', '')),
                            'category': str(note_data.get('category', 'General')),
                            'is_public': bool(note_data.get('is_public', False)),
                            'is_approved': bool(note_data.get('is_approved', False)),
                            'approved_by': note_data.get('approved_by'),
                            'created_at': self.parse_date(note_data.get('created_at')) or datetime.now(),
                            'updated_at': self.parse_date(note_data.get('updated_at')) or datetime.now(),
                            'approved_at': self.parse_date(note_data.get('approved_at'))
                        }
                        
                        # Convert datetime objects to ISO format strings
                        for key in ['created_at', 'updated_at', 'approved_at']:
                            if isinstance(cleaned_note[key], datetime):
                                cleaned_note[key] = cleaned_note[key].isoformat()
                        
                        # Store the cleaned note
                        cleaned_notes[str(note_id)] = cleaned_note
                        logger.log_info(f"Successfully cleaned note {note_id} for {target.name}")
                        
                    except Exception as e:
                        logger.log_err(f"Error cleaning note {note_id} for {target.name}: {e}")
                        continue
                
                if cleaned_notes:
                    # Store the cleaned notes back to the character
                    target.attributes.add('notes', cleaned_notes)
                    logger.log_info(f"Successfully stored {len(cleaned_notes)} cleaned notes for {target.name}")
                    return True
                else:
                    logger.log_err(f"No valid notes could be cleaned for {target.name}")
                    return False
            else:
                # If conversion failed but we have raw notes, create a recovery note
                if raw_notes:
                    logger.log_info(f"Creating recovery note for {target.name}")
                    recovery_notes = {
                        '1': {
                            'name': 'Recovered Data',
                            'text': str(raw_notes),
                            'category': 'System',
                            'is_public': False,
                            'is_approved': False,
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }
                    }
                    target.attributes.add('notes', recovery_notes)
                    return True
                else:
                    logger.log_info(f"No notes data to fix for {target.name}")
                    return True  # No data to fix is still a successful operation
                    
        except Exception as e:
            logger.log_err(f"Error fixing notes for {target.name}: {e}")
            return False

    def parse_note_format(self, text):
        """Parse notes in the format: note/set <character>/'name': Attribute='text': Attribute"""
        try:
            # If the text looks like a dictionary string (starts with '{'), try ast.literal_eval
            if text.strip().startswith('{'):
                import ast
                return ast.literal_eval(text)
            
            notes_dict = {}
            note_id = 1
            
            # Split on note markers (can be customized based on your format)
            parts = text.split("note/set")
            
            for part in parts[1:]:  # Skip the first empty part
                try:
                    # Extract name and text
                    name_part, text_part = part.split("='", 1)
                    name = name_part.split("'")[-1].strip()
                    text = text_part.split("'")[0].strip()
                    
                    # Create note entry
                    notes_dict[str(note_id)] = {
                        'name': name,
                        'text': text,
                        'category': 'General',  # Default category
                        'is_public': False,
                        'is_approved': False,
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    note_id += 1
                except Exception as e:
                    logger.log_err(f"Error parsing note part: {e}")
                    continue
            
            return notes_dict if notes_dict else None
            
        except Exception as e:
            logger.log_err(f"Error in parse_note_format: {e}")
            return None

    def _convert_notes_to_dict(self, notes_data):
        """Helper method to convert notes data to a proper dictionary."""
        if not notes_data:
            return {}
            
        # Add debug logging
        logger.log_info(f"Converting notes data of type: {type(notes_data)}")
        
        # If it's already a dictionary or _SaverDict, return it as a dict
        if isinstance(notes_data, dict):
            logger.log_info("Notes data is already a dictionary")
            return notes_data
        elif isinstance(notes_data, utils.dbserialize._SaverDict):
            logger.log_info("Notes data is a _SaverDict")
            return dict(notes_data)
            
        # If it's a string, try multiple conversion methods
        if isinstance(notes_data, str):
            logger.log_info("Notes data is a string, attempting conversion")
            
            # Try Evennia's deserializer first
            try:
                from evennia.utils.dbserialize import deserialize
                deserialized = deserialize(notes_data)
                if isinstance(deserialized, (dict, utils.dbserialize._SaverDict)):
                    logger.log_info("Successfully converted using Evennia deserializer")
                    return dict(deserialized)
            except Exception as e:
                logger.log_trace(f"Evennia deserialize failed: {e}")

            # Try custom dictionary parsing for datetime objects
            try:
                import re
                from datetime import datetime
                
                # Clean the string and ensure it's a valid dictionary format
                cleaned_str = notes_data.strip()
                if cleaned_str.startswith('{') and cleaned_str.endswith('}'):
                    # Replace datetime objects with ISO format strings
                    cleaned_str = re.sub(
                        r'datetime\.datetime\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)(?:,\s*\d+)?\)',
                        lambda m: f"'{datetime(*map(int, m.groups())).isoformat()}'",
                        cleaned_str
                    )
                    
                    # Now try to evaluate the cleaned string
                    import ast
                    result = ast.literal_eval(cleaned_str)
                    if isinstance(result, dict):
                        logger.log_info("Successfully converted using custom datetime parsing")
                        return result
            except Exception as e:
                logger.log_trace(f"Custom datetime parsing failed: {e}")

            # Try ast.literal_eval with basic cleaning
            try:
                import ast
                # Clean the string before evaluation
                cleaned_str = notes_data.strip()
                if cleaned_str.startswith('{') and cleaned_str.endswith('}'):
                    result = ast.literal_eval(cleaned_str)
                    if isinstance(result, dict):
                        logger.log_info("Successfully converted using ast.literal_eval")
                        return result
            except Exception as e:
                logger.log_trace(f"ast.literal_eval failed: {e}")

            # Try JSON parsing as a last resort
            try:
                import json
                result = json.loads(notes_data)
                if isinstance(result, dict):
                    logger.log_info("Successfully converted using JSON")
                    return result
            except Exception as e:
                logger.log_trace(f"JSON parsing failed: {e}")

        # If all conversion attempts fail, try to parse as a formatted string
        try:
            # Split on note markers (can be customized based on your format)
            notes_dict = {}
            note_id = 1
            
            logger.log_info("Attempting to parse as formatted string")
            
            # Try to parse any structured format we can find
            if "note/set" in notes_data:
                parts = notes_data.split("note/set")
                for part in parts[1:]:  # Skip the first empty part
                    try:
                        # Extract name and text
                        if "='" in part and "'" in part.split("='", 1)[1]:
                            name_part, text_part = part.split("='", 1)
                            name = name_part.split("'")[-1].strip()
                            text = text_part.split("'")[0].strip()
                            
                            # Create note entry
                            notes_dict[str(note_id)] = {
                                'name': name,
                                'text': text,
                                'category': 'General',
                                'is_public': False,
                                'is_approved': False,
                                'created_at': datetime.now().isoformat(),
                                'updated_at': datetime.now().isoformat()
                            }
                            note_id += 1
                            logger.log_info(f"Successfully parsed note {note_id}")
                    except Exception as e:
                        logger.log_trace(f"Error parsing note part: {e}")
                        continue
            
            if notes_dict:
                logger.log_info("Successfully created notes dictionary from formatted string")
                return notes_dict
        except Exception as e:
            logger.log_trace(f"Format parsing failed: {e}")

        # If all conversion attempts fail, try to recover what we can
        try:
            logger.log_info("Attempting last-resort recovery of notes")
            import re
            
            # Try to extract any valid note-like structures
            notes_dict = {}
            note_pattern = r"'(\d+)':\s*({[^}]+})"
            matches = re.finditer(note_pattern, str(notes_data))
            
            for match in matches:
                try:
                    note_id, note_data_str = match.groups()
                    # Clean up the note data string
                    note_data_str = re.sub(
                        r'datetime\.datetime\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)(?:,\s*\d+)?\)',
                        lambda m: f"'{datetime(*map(int, m.groups())).isoformat()}'",
                        note_data_str
                    )
                    
                    # Try to parse the cleaned note data
                    import ast
                    note_data = ast.literal_eval(note_data_str)
                    if isinstance(note_data, dict):
                        notes_dict[note_id] = note_data
                        logger.log_info(f"Recovered note {note_id}")
                except Exception as e:
                    logger.log_trace(f"Failed to recover note: {e}")
                    continue
            
            if notes_dict:
                logger.log_info(f"Successfully recovered {len(notes_dict)} notes")
                return notes_dict
                
        except Exception as e:
            logger.log_trace(f"Recovery attempt failed: {e}")

        # If all attempts fail, log the error and return empty dict
        logger.log_err(f"All note conversion attempts failed for data: {notes_data}")
        return {}

    def get_note_by_name_or_id(self, target, note_identifier):
        """Helper method to find a note by either name or ID."""
        notes_dict = target.attributes.get('notes', {})
        
        # Debug information
        
        # Convert notes to dictionary
        notes_dict = self._convert_notes_to_dict(notes_dict)
        if notes_dict:
            # Update the stored format to be a proper dictionary
            target.attributes.add('notes', notes_dict)
        
        # Clean up note identifier - strip any status markers and spaces
        clean_identifier = note_identifier.strip().rstrip('*!').strip()
        # Remove any '#' prefix from IDs
        if clean_identifier.startswith('#'):
            clean_identifier = clean_identifier[1:]
        
        # First try to find by ID
        if clean_identifier in notes_dict:
            note_data = notes_dict[clean_identifier]
            if note_data and isinstance(note_data, (dict, utils.dbserialize._SaverDict)):
                return clean_identifier, note_data
        
        # If not found by ID, try to find by name (case-insensitive)
        clean_identifier_lower = clean_identifier.lower()
        
        # Iterate through all notes
        for note_id, note_data in notes_dict.items():
            # Skip if note_data is None or empty
            if not note_data:
                continue
            
            # Get the note name
            note_name = str(note_data.get('name', '')).strip()
            if not note_name:
                continue
                
            note_name_lower = note_name.lower()
            
            # Compare the names (case-insensitive)
            if note_name_lower == clean_identifier_lower:
                return note_id, note_data
            
            # Also try matching without any special characters
            note_name_clean = ''.join(c for c in note_name_lower if c.isalnum())
            identifier_clean = ''.join(c for c in clean_identifier_lower if c.isalnum())
            if note_name_clean == identifier_clean:
                return note_id, note_data
        
        return None, None

    def list_notes(self):
        """List all notes for the character."""
        notes_dict = self.caller.attributes.get('notes', {})
        
        # Convert notes to dictionary and handle potential errors
        try:
            notes_dict = self._convert_notes_to_dict(notes_dict)
            if notes_dict:
                # Store back as proper dictionary to prevent future conversion issues
                self.caller.attributes.add('notes', notes_dict)
            
            if not notes_dict:
                self.caller.msg("You don't have any notes.")
                return

            width = 78
            notes_by_category = defaultdict(list)
            
            # Process each note from the dictionary
            for note_id, note_data in notes_dict.items():
                if not note_data:
                    continue
                
                try:
                    # Ensure note_data is a dictionary
                    if hasattr(note_data, 'get'):
                        note_data = dict(note_data)
                    else:
                        logger.log_err(f"Invalid note data format for note {note_id}: {note_data}")
                        continue
                        
                    # Create Note object with all fields, with error handling for dates
                    try:
                        note = Note(
                            name=note_data.get('name', 'Unnamed Note'),
                            text=note_data.get('text', ''),
                            category=note_data.get('category', 'General'),
                            is_public=note_data.get('is_public', False),
                            is_approved=note_data.get('is_approved', False),
                            approved_by=note_data.get('approved_by'),
                            approved_at=self.parse_date(note_data.get('approved_at')),
                            created_at=self.parse_date(note_data.get('created_at')) or datetime.now(),
                            updated_at=self.parse_date(note_data.get('updated_at')) or datetime.now(),
                            note_id=note_id
                        )
                        notes_by_category[note.category].append(note)
                    except Exception as e:
                        logger.log_err(f"Error creating Note object for note {note_id}: {e}")
                        continue
                        
                except Exception as e:
                    logger.log_err(f"Error processing note {note_id}: {e}")
                    continue

            if not notes_by_category:
                self.caller.msg("You don't have any valid notes.")
                return

            # Calculate column width for the tabular display
            col_width = 25  # Width for each note column
            cols_per_row = 3  # Number of columns per row

            output = header(f"{self.caller.name}'s Notes", width=width, color="|y", fillchar="|b=|n", bcolor="|b")

            # Sort categories alphabetically
            for category in sorted(notes_by_category.keys()):
                category_notes = notes_by_category[category]
                # Sort notes by name within each category
                category_notes.sort(key=lambda x: x.name.lower())
                
                # Category header with equals
                output += f"\n|b==> |y{category}|n |b<==|n" + "|b=|n" * (width - len(category) - 7) + "\n"
                
                # Process notes in rows of cols_per_row columns
                for i in range(0, len(category_notes), cols_per_row):
                    row_notes = category_notes[i:i + cols_per_row]
                    row = ""
                    for note in row_notes:
                        # Format note name with ID
                        note_display = f"{note.name} (#{note.note_id})"
                        if len(note_display) > col_width - 2:
                            note_display = note_display[:col_width - 3] + "…"
                        # Pad with spaces to maintain column width
                        row += f"{note_display:<{col_width}}"
                    output += " " + row.rstrip() + "\n"

            output += "|b=" + "=" * (width - 2) + "=|n"
            self.caller.msg(output)
            
        except Exception as e:
            logger.log_err(f"Error in list_notes: {e}")
            self.caller.msg("There was an error listing your notes. The error has been logged.")

    def generate_note_id(self, notes_dict):
        """Generate a sequential note ID."""
        if not notes_dict:
            return "1"
            
        # Convert existing IDs to integers, ignoring any non-numeric IDs
        existing_ids = []
        for note_id in notes_dict.keys():
            try:
                existing_ids.append(int(note_id))
            except ValueError:
                continue
                
        if not existing_ids:
            return "1"
            
        # Get the highest existing ID and add 1
        next_id = max(existing_ids) + 1
        return str(next_id)

    def create_note(self):
        """Create a new note."""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +note/create <name>=<text>")
            return

        name, text = self.args.split("=", 1)
        name = name.strip()
        # Convert %r markers to newlines, properly handling double %r
        text = text.strip().replace("%r%r", "\n\n").replace("%r", "\n")

        # Handle category in name
        if "/" in name:
            category, name = name.split("/", 1)
            category = category.strip().title()
        else:
            category = "General"

        # Check text length and split if necessary
        MAX_TEXT_LENGTH = 10000  # Adjust this value based on your system's limitations
        if len(text) > MAX_TEXT_LENGTH:
            # Split into multiple parts
            parts = [text[i:i + MAX_TEXT_LENGTH] for i in range(0, len(text), MAX_TEXT_LENGTH)]
            for i, part in enumerate(parts, 1):
                part_name = f"{name} (Part {i}/{len(parts)})"
                try:
                    note = self.caller.add_note(part_name, part, category=category)
                    self.caller.msg(f"Created note #{note.note_id}: {part_name}")
                except Exception as e:
                    self.caller.msg(f"Error creating note part {i}: {e}")
            return

        try:
            note = self.caller.add_note(name, text, category=category)
            self.caller.msg(f"Created note #{note.note_id}: {note.name}")
        except Exception as e:
            self.caller.msg(f"Error creating note: {e}")

    def edit_note(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +note/edit <note>=<new text>")
            return

        note_id, text = self.args.split("=", 1)
        note_id = note_id.strip()
        # Convert %r markers to newlines, properly handling double %r
        text = text.strip().replace("%r%r", "\n\n").replace("%r", "\n")

        if self.caller.update_note(note_id, text=text):
            self.caller.msg(f"Note '{note_id}' updated.")
        else:
            self.caller.msg(f"Note '{note_id}' not found.")

    def view_note(self):
        """View a specific note."""
        if not self.args:
            self.list_notes()
            return

        if "/" in self.args:
            target_name, note_identifier = self.args.split("/", 1)
            target = self.search_for_character(target_name)
            if not target:
                return
            
            # Handle wildcard to show all notes
            if note_identifier == "*":
                self.list_character_notes(target)
                return
        else:
            target = self.caller
            note_identifier = self.args

        # Debug output
        self.caller.msg(f"Searching for note '{note_identifier}' on {target.name}")

        # Try to find note by name or ID
        note_id, note_data = self.get_note_by_name_or_id(target, note_identifier)
        
        if not note_data:
            self.caller.msg(f"Could not find a note matching '{note_identifier}'.")
            return

        # Create Note object
        if hasattr(note_data, 'get'):
            note_data = dict(note_data)
            note = Note(
                name=note_data.get('name', 'Unnamed Note'),
                text=note_data.get('text', ''),
                category=note_data.get('category', 'General'),
                is_public=note_data.get('is_public', False),
                is_approved=note_data.get('is_approved', False),
                approved_by=note_data.get('approved_by'),
                approved_at=self.parse_date(note_data.get('approved_at')),
                created_at=self.parse_date(note_data.get('created_at')),
                updated_at=self.parse_date(note_data.get('updated_at')),
                note_id=note_id
            )
        else:
            self.caller.msg("Invalid note data format.")
            return

        # Check permissions
        if target != self.caller and not (note.is_public or 
            self.caller.check_permstring("builders") or 
            self.caller.check_permstring("storyteller")):
            self.caller.msg("You don't have permission to view this note.")
            return

        self.display_note(note)
    
    def list_character_notes(self, target):
        """List all viewable notes for a character."""
        notes_dict = target.attributes.get('notes', {})
        
        try:
            # Convert notes to dictionary and handle potential errors
            notes_dict = self._convert_notes_to_dict(notes_dict)
            if notes_dict:
                # Store back as proper dictionary to prevent future conversion issues
                target.attributes.add('notes', notes_dict)
            
            if not notes_dict:
                self.caller.msg(f"{target.name} has no notes.")
                return

            width = 78
            notes_by_category = defaultdict(list)
            is_staff = (self.caller.check_permstring("builders") or 
                       self.caller.check_permstring("storyteller"))
            
            # Process each note from the dictionary
            for note_id, note_data in notes_dict.items():
                if not note_data:
                    continue
                
                try:
                    # Ensure note_data is a dictionary
                    if hasattr(note_data, 'get'):
                        note_data = dict(note_data)
                    else:
                        logger.log_err(f"Invalid note data format for note {note_id} on {target.name}: {note_data}")
                        continue
                        
                    # Create Note object with all fields, with error handling for dates
                    try:
                        note = Note(
                            name=note_data.get('name', 'Unnamed Note'),
                            text=note_data.get('text', ''),
                            category=note_data.get('category', 'General'),
                            is_public=note_data.get('is_public', False),
                            is_approved=note_data.get('is_approved', False),
                            approved_by=note_data.get('approved_by'),
                            approved_at=self.parse_date(note_data.get('approved_at')),
                            created_at=self.parse_date(note_data.get('created_at')) or datetime.now(),
                            updated_at=self.parse_date(note_data.get('updated_at')) or datetime.now(),
                            note_id=note_id
                        )
                        
                        # Only show notes if they're public or viewer is staff/self
                        if note.is_public or is_staff or target == self.caller:
                            notes_by_category[note.category].append(note)
                    except Exception as e:
                        logger.log_err(f"Error creating Note object for note {note_id} on {target.name}: {e}")
                        continue
                        
                except Exception as e:
                    logger.log_err(f"Error processing note {note_id} on {target.name}: {e}")
                    continue

            if not notes_by_category:
                if target == self.caller or is_staff:
                    self.caller.msg(f"{target.name} has no notes.")
                else:
                    self.caller.msg(f"{target.name} has no public notes you can view.")
                return

            # Calculate column width for the tabular display
            col_width = 25  # Width for each note column
            cols_per_row = 3  # Number of columns per row

            output = header(f"Notes for {target.name}", width=width, color="|y", fillchar="|b=|n", bcolor="|b")

            # Sort categories alphabetically
            for category in sorted(notes_by_category.keys()):
                category_notes = notes_by_category[category]
                # Sort notes by name within each category
                category_notes.sort(key=lambda x: x.name.lower())
                
                # Category header with equals
                output += f"\n|b==> |y{category}|n |b<==|n" + "|b=|n" * (width - len(category) - 7) + "\n"
                
                # Process notes in rows of cols_per_row columns
                for i in range(0, len(category_notes), cols_per_row):
                    row_notes = category_notes[i:i + cols_per_row]
                    row = ""
                    for note in row_notes:
                        # Format note name with ID and visibility indicator
                        visibility = "" if note.is_public else " [P]"
                        note_display = f"{note.name}{visibility} (#{note.note_id})"
                        if len(note_display) > col_width - 2:
                            note_display = note_display[:col_width - 3] + "…"
                        # Pad with spaces to maintain column width
                        row += f"{note_display:<{col_width}}"
                    output += " " + row.rstrip() + "\n"

            output += "|b=" + "=" * (width - 2) + "=|n"
            self.caller.msg(output)
            
        except Exception as e:
            logger.log_err(f"Error in list_character_notes for {target.name}: {e}")
            self.caller.msg(f"There was an error listing notes for {target.name}. The error has been logged.")

    def list_notes_by_category(self, category):
        """List all notes in a specific category."""
        notes = self.caller.get_all_notes()
        if not notes:
            self.caller.msg("You don't have any notes.")
            return

        category_notes = [note for note in notes if note.category.lower() == category.lower()]
        if not category_notes:
            self.caller.msg(f"No notes found in category '{category}'.")
            return

        width = 78
        output = header(f"Notes in category '{category}'", width=width, fillchar="|r=|n")
        
        for note in category_notes:
            note_header = f"|y* |w#{note.note_id} |n{note.name}"
            output += note_header + "\n"
            output += "    " + note.text + "\n\n"

        output += footer(width=width, fillchar="|r=|n")
        self.caller.msg(output)

    def list_room_characters(self):
        """List all characters in the current room."""
        if not self.caller.location:
            self.caller.msg("You are not in any location.")
            return
        
        characters = [obj for obj in self.caller.location.contents 
                     if obj.has_account and obj != self.caller]
        
        if not characters:
            self.caller.msg("No other characters found in this location.")
            return

        self.caller.msg("Characters in this location:")
        for char in characters:
            self.caller.msg(f"- {char.name}")

    def decompile_note(self):
        """Get the raw text of a note."""
        if not self.args:
            self.caller.msg("Usage: +note/decompile <note>")
            return

        if "/" in self.args:
            target_name, note_id = self.args.split("/", 1)
            target = self.search_for_character(target_name)
            if not target:
                return
        else:
            target = self.caller
            note_id = self.args

        note = target.get_note(note_id)
        if not note:
            self.caller.msg("No note with that ID exists.")
            return

        # Check permissions
        if target != self.caller and not (self.caller.check_permstring("builders") or 
            self.caller.check_permstring("storyteller")):
            self.caller.msg("You don't have permission to decompile this note.")
            return

        # Format the decompiled output
        output = f"+note/create {note.category}/{note.name}={note.text}"
        if note.is_public:
            output += "\n+note/public #{note.note_id}"
        self.caller.msg(output)

    def move_note(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +note/move <note name>=<new category>")
            return

        note_name, new_category = self.args.split("=", 1)
        note_name = note_name.strip()
        new_category = new_category.strip()

        note = self.caller.get_note(note_name)
        if not note:
            self.caller.msg(f"Note not found: {note_name}")
            return

        self.caller.update_note(note_name, note.text, new_category)
        self.caller.msg(f"Note '{note_name}' moved to category '{new_category}'.")

    def change_note_status(self):
        if not self.args or "=" not in self.args:
            # Check if it's a direct public/private command without =
            if "/" in self.args:
                target_name, note_id = self.args.split("/", 1)
                target = self.search_for_character(target_name)
                if not target:
                    return
            else:
                target = self.caller
                note_id = self.args

            # Set status based on the switch used
            status = "PUBLIC" if self.switches[0] == "public" else "PRIVATE"
        else:
            # Handle the traditional status=value format
            note_spec, status = self.args.split("=", 1)
            if "/" in note_spec:
                target_name, note_id = note_spec.split("/", 1)
                target = self.search_for_character(target_name)
                if not target:
                    return
            else:
                target = self.caller
                note_id = note_spec.strip()
            status = status.strip().upper()

        if status not in ["PRIVATE", "PUBLIC"]:
            self.caller.msg("Status must be either PRIVATE or PUBLIC.")
            return

        # Check permissions if trying to modify another character's notes
        if target != self.caller and not (self.caller.check_permstring("builders") or 
            self.caller.check_permstring("storyteller")):
            self.caller.msg("You don't have permission to modify notes on other characters.")
            return

        if target.update_note(note_id, is_public=(status == "PUBLIC")):
            self.caller.msg(f"Note #{note_id} on {target.name} is now {status}.")
            if target != self.caller:
                target.msg(f"Your note #{note_id} has been made {status} by {self.caller.name}.")
        else:
            self.caller.msg(f"Note #{note_id} not found on {target.name}.")

    def prove_note(self):
        """Show a note to specific targets."""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +note/prove <note name>=<target1>,<target2>,...")
            return

        note_name, targets = self.args.split("=", 1)
        note_name = note_name.strip()
        targets = [target.strip() for target in targets.split(",")]

        # Get the note directly using the get_note_by_name_or_id method to ensure note_id is set
        note_id, note_data = self.get_note_by_name_or_id(self.caller, note_name)
        
        if not note_data:
            self.caller.msg(f"Note not found: {note_name}")
            return
        
        # Create Note object with explicit note_id
        note = Note(
            name=note_data.get('name', 'Unnamed Note'),
            text=note_data.get('text', ''),
            category=note_data.get('category', 'General'),
            is_public=note_data.get('is_public', False),
            is_approved=note_data.get('is_approved', False),
            approved_by=note_data.get('approved_by'),
            approved_at=self.parse_date(note_data.get('approved_at')),
            created_at=self.parse_date(note_data.get('created_at')) or datetime.now(),
            updated_at=self.parse_date(note_data.get('updated_at')) or datetime.now(),
            note_id=note_id
        )

        for target_name in targets:
            target = self.search_for_character(target_name)
            if target:
                self.display_note(note, target)
                self.caller.msg(f"Note '{note.name}' shown to {target.name}.")
            else:
                self.caller.msg(f"Could not find character '{target_name}'.")

    def approve_note(self):
        """Approve a note (staff only)."""
        if not (self.caller.check_permstring("builders") or 
            self.caller.check_permstring("storyteller")):
            self.caller.msg("You don't have permission to approve notes.")
            return

        if not self.args:
            self.caller.msg("Usage: +note/approve <target>/<note>")
            return

        if "/" not in self.args:
            self.caller.msg("You must specify both target and note ID.")
            return

        target_name, note_id = self.args.split("/", 1)
        target = self.search_for_character(target_name)
        if not target:
            self.caller.msg(f"Could not find character '{target_name}'.")
            return

        note = target.get_note(note_id)
        if not note:
            self.caller.msg("No note with that ID exists.")
            return

        # Update note approval status
        target.update_note(note_id, 
            is_approved=True, 
            approved_by=self.caller.name,
            approved_at=datetime.now()
        )
        self.caller.msg(f"Note #{note_id} has been approved.")
        target.msg(f"Your note #{note_id} has been approved by {self.caller.name}.")

    def unapprove_note(self):
        """Unapprove a note (staff only)."""
        if not (self.caller.check_permstring("builders") or 
            self.caller.check_permstring("storyteller")):
            self.caller.msg("You don't have permission to unapprove notes.")
            return

        if not self.args:
            self.caller.msg("Usage: +note/unapprove <target>/<note>")
            return

        if "/" not in self.args:
            self.caller.msg("You must specify both target and note ID.")
            return

        target_name, note_id = self.args.split("/", 1)
        target = self.search_for_character(target_name)
        if not target:
            self.caller.msg(f"Could not find character '{target_name}'.")
            return

        note = target.get_note(note_id)
        if not note:
            self.caller.msg("No note with that ID exists.")
            return

        # Update note approval status
        target.update_note(note_id, 
            is_approved=False, 
            approved_by=None,
            approved_at=None
        )
        self.caller.msg(f"Note #{note_id} has been unapproved.")
        target.msg(f"Your note #{note_id} has been unapproved by {self.caller.name}.")

    def display_note(self, note, target=None):
        """Display a note with formatting.
        
        Args:
            note: The note to display
            target: Optional target to display the note to. If None, displays to self.caller
        """
        width = 78
        
        # Include player name in the header when proving a note
        if target and target != self.caller:
            # When showing a note to someone else, include the owner's name
            header_text = f"{self.caller.name}'s Note #{note.note_id}"
        else:
            header_text = f"Note #{note.note_id}"
        
        output = header(header_text, width=width, color="|y", fillchar="|r=|n", bcolor="|b")

        if note.category:
            output += f"|c{note.category}|n"
            output += f" |w#{note.note_id}|n\n"

        output += format_stat("Note Title:", note.name, width=width) + "\n"
        output += format_stat("Visibility:", "Public" if note.is_public else "Private", width=width) + "\n"
        
        # Show approval status and details
        if note.is_approved:
            output += format_stat("Approved:", "Yes", width=width) + "\n"
            if note.approved_by:
                output += format_stat("Approved By:", note.approved_by, width=width) + "\n"
            if note.approved_at:
                output += format_stat("Approved At:", note.approved_at.strftime("%Y-%m-%d %H:%M:%S"), width=width) + "\n"
        else:
            output += format_stat("Approved:", "No", width=width) + "\n"

        # Show creation and update times for staff
        if (self.caller.check_permstring("builders") or 
            self.caller.check_permstring("storyteller")):
            output += format_stat("Created:", note.created_at.strftime("%Y-%m-%d %H:%M:%S"), width=width) + "\n"
            output += format_stat("Updated:", note.updated_at.strftime("%Y-%m-%d %H:%M:%S"), width=width) + "\n"

        output += divider("", width=width, fillchar="-", color="|r") + "\n"
        
        # Note content - display without wrapping
        text = note.text.strip()
        # Split on actual newlines, preserving empty lines for spacing
        content_lines = text.split('\n')
        for line in content_lines:
            if line.strip():
                # Add a space before each non-empty line for better readability
                output += ' ' + line + '\n'
            else:
                output += '\n'  # Preserve empty lines

        output += footer(width=width, fillchar="|r=|n")
        
        # Send to the target if provided, otherwise to self.caller
        recipient = target if target else self.caller
        recipient.msg(output)

    def delete_note(self):
        """Delete a note."""
        if not self.args:
            self.caller.msg("Usage: +note/delete <note> or +note/delete <target>=<note>")
            return

        # Handle staff deleting other player's notes
        if "=" in self.args and self.caller.check_permstring("builders"):
            target_name, note_id = self.args.split("=", 1)
            target = self.search_for_character(target_name)
            if not target:
                self.caller.msg(f"Could not find character '{target_name}'.")
                return
        else:
            target = self.caller
            note_id = self.args

        # Get the note to verify it exists
        notes_dict = target.attributes.get('notes', {})
        note_data = notes_dict.get(str(note_id))

        if not note_data:
            self.caller.msg("No note with that ID exists.")
            return

        # Check permissions
        if target != self.caller and not self.caller.check_permstring("builders"):
            self.caller.msg("You don't have permission to delete notes from other characters.")
            return

        # Delete the note
        notes_dict.pop(str(note_id))
        target.attributes.add('notes', notes_dict)

        # Notify both parties
        self.caller.msg(f"Note #{note_id} has been deleted.")
        if target != self.caller:
            target.msg(f"Your note #{note_id} has been deleted by {self.caller.name}.")

    def set_note(self):
        """Set a note on another character (staff only)."""
        if not (self.caller.check_permstring("builders") or 
            self.caller.check_permstring("storyteller")):
            self.caller.msg("You don't have permission to set notes on other characters.")
            return

        if not self.args:
            self.caller.msg("Usage: +note/set <target>/<note name>=<text>")
            self.caller.msg("       +note/set <target>/'name': Attribute='text': Attribute")
            return

        # Check if we're using the new format
        if "': " in self.args and "='" in self.args:
            try:
                # Parse the new format
                target_name = self.args.split("/")[0].strip()
                name_part, text_part = self.args.split("='", 1)
                note_name = name_part.split("':")[-1].strip()
                note_text = text_part.split("'")[0].strip()
                
                # Find the target character
                target = self.search_for_character(target_name)
                if not target:
                    self.caller.msg(f"Could not find character '{target_name}'.")
                    return
                    
            except Exception as e:
                self.caller.msg(f"Error parsing new format: {e}")
                self.caller.msg("Usage: +note/set <target>/'name': Attribute='text': Attribute")
                return
        else:
            # Handle traditional format
            if "=" not in self.args:
                self.caller.msg("Usage: +note/set <target>/<note name>=<text>")
                return

            if "/" not in self.args.split("=")[0]:
                self.caller.msg("You must specify both target and note name.")
                return

            target_spec, note_text = self.args.split("=", 1)
            target_name, note_name = target_spec.split("/", 1)
            target = self.search_for_character(target_name)
            if not target:
                self.caller.msg(f"Could not find character '{target_name}'.")
                return

        # Handle category in note name
        if "/" in note_name:
            category, note_name = note_name.split("/", 1)
            category = category.strip().title()
        else:
            category = "General"

        # Convert %r markers to newlines
        note_text = note_text.strip().replace("%r%r", "\n\n").replace("%r", "\n")
        
        # Get current notes
        notes_dict = target.attributes.get('notes', {})
        
        # Convert to dictionary if needed
        notes_dict = self._convert_notes_to_dict(notes_dict)
        
        # Generate new note ID
        note_id = self.generate_note_id(notes_dict)
        
        # Create the note
        note_data = {
            'name': note_name.strip(),
            'text': note_text,
            'category': category,
            'is_public': False,
            'is_approved': False,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Add the note to the dictionary
        notes_dict[note_id] = note_data
        
        # Save the updated notes
        target.attributes.add('notes', notes_dict)
        
        self.caller.msg(f"Created note #{note_id} on {target.name}: {note_name}")
        target.msg(f"{self.caller.name} has created note #{note_id} on your character: {note_name}")