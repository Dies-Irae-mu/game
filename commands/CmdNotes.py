from evennia import default_cmds
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
      +note/<category> <target>/* - see all notes on someone else in a category
      +note/create <name>=<text>  - make a note called <name>
      +note/create/<category> <name>=<text> - make a note in a specific category
      +note/edit <note>=<new text> - change the text on a note, removes approval
      +note/move <note>=<category> - move a note to a new category, keeps approval
      +note/status <note>=PRIVATE|PUBLIC - make a note in-/visible to others
      +note/prove <note>=<target(s)> - show any note to a list of targets
      +note/approve[/<category>] <target>/<note> - approve a note (staff only)
      +note/unapprove[/<category>] <target>/<note> - unapprove a note (staff only)
    """

    key = "+note"
    aliases = ["+notes"]
    locks = "cmd:all()"
    help_category = "Character"

    def func(self):
        logger.log_info(f"CmdNotes func called with args: {self.args}, switches: {self.switches}")
        if not self.args and not self.switches:
            # Display all notes
            self.list_notes()
        elif self.switches:
            # Handle different switches
            switch = self.switches[0].lower()
            if switch == "create":
                self.create_note()
            elif switch == "edit":
                self.edit_note()
            elif switch == "move":
                self.move_note()
            elif switch == "status":
                self.change_note_status()
            elif switch == "prove":
                self.prove_note()
            elif switch == "approve":
                self.approve_unapprove_note(True)
            elif switch == "unapprove":
                self.approve_unapprove_note(False)
            elif switch == "decompile":
                self.decompile_note()
            else:
                self.caller.msg(f"Unknown switch: {switch}")
        else:
            # View a specific note
            self.view_note()

    def list_notes(self):
        notes = self.caller.get_all_notes()
        if not notes:
            self.caller.msg("You don't have any notes.")
            return

        width = 78
        notes_by_category = defaultdict(list)
        for note in notes:
            notes_by_category[note.category].append(note)

        output = header(f"Notes for {self.caller.name}", width=width, fillchar="|r=|n")

        for category, category_notes in notes_by_category.items():
            output += f"|r{'-' * width}|n\n"
            output += divider(category, width=width, color="|c")
            for note in category_notes:
                # Truncate the note text to the first 60 characters
                truncated_text = note.text[:60] + "..." if len(note.text) > 60 else note.text
                wrapped_text = wrap_ansi(truncated_text, width=width-4)  # -4 for left padding
                
                note_header = f"|y* |w#{note.id} |n{note.name}"
                output += note_header + "\n"
                output += "    " + wrapped_text.replace("\n", "\n    ") + "\n\n"

        output += footer(width=width, fillchar="|r=|n")
        
        self.caller.msg(output)

    def create_note(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +note/create [<category>/]<name>=<text>")
            return

        if "/" in self.lhs:
            category, name = self.lhs.split("/", 1)
            category = category.strip()
        else:
            category = "General"
            name = self.lhs.strip()

        text = self.rhs.strip()

        self.caller.add_note(name, text, category)
        self.caller.msg(f"Note '{name}' created in category '{category}'.")

    def edit_note(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +note/edit <note>=<new text>")
            return

        name, text = self.args.split("=", 1)
        name = name.strip()
        text = text.strip()

        if self.caller.update_note(name, text):
            self.caller.msg(f"Note '{name}' updated.")
        else:
            self.caller.msg(f"Note '{name}' not found.")

    def view_note(self):
        if "/" in self.args:
            target_name, note_identifier = self.args.split("/", 1)
            target = self.caller.search(target_name)
            if not target:
                return
        else:
            target = self.caller
            note_identifier = self.args

        note = target.get_note(note_identifier)
        if not note:
            self.caller.msg(f"Note not found: {note_identifier}")
            return

        if target != self.caller and not (note.is_public or self.caller.check_permstring("Builders")):
            self.caller.msg("You don't have permission to view this note.")
            return

        self.display_note(note)

    def decompile_note(self):
        if not self.args:
            self.caller.msg("Usage: +note/decompile <note name>")
            return

        note = self.caller.get_note(self.args)
        if not note:
            self.caller.msg(f"Note not found: {self.args}")
            return

        self.caller.msg(f"Raw text for note '{note.name}':\n{note.text}")

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
            self.caller.msg("Usage: +note/status <note name>=PRIVATE|PUBLIC")
            return

        note_name, status = self.args.split("=", 1)
        note_name = note_name.strip()
        status = status.strip().upper()

        if status not in ["PRIVATE", "PUBLIC"]:
            self.caller.msg("Status must be either PRIVATE or PUBLIC.")
            return

        note = self.caller.get_note(note_name)
        if not note:
            self.caller.msg(f"Note not found: {note_name}")
            return

        is_public = status == "PUBLIC"
        self.caller.change_note_status(note_name, is_public)
        self.caller.msg(f"Note '{note_name}' is now {status}.")

    def prove_note(self):
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: +note/prove <note name>=<target1>,<target2>,...")
            return

        note_name, targets = self.args.split("=", 1)
        note_name = note_name.strip()
        targets = [target.strip() for target in targets.split(",")]

        note = self.caller.get_note(note_name)
        if not note:
            self.caller.msg(f"Note not found: {note_name}")
            return

        for target_name in targets:
            target = self.caller.search(target_name)
            if target:
                self.display_note(note, target)
                self.caller.msg(f"Note '{note_name}' shown to {target.name}.")
            else:
                self.caller.msg(f"Target not found: {target_name}")

    def approve_unapprove_note(self, approve):
        if not self.caller.check_permstring("Builders"):
            self.caller.msg("You don't have permission to approve or unapprove notes.")
            return

        args = self.args.split("/")
        if len(args) < 2:
            self.caller.msg("Usage: +note/[un]approve[/category] <character>/<note>")
            return

        if len(args) == 3:
            category, target_name, note_identifier = args
        else:
            category = None
            target_name, note_identifier = args

        target = self.caller.search(target_name)
        if not target:
            return

        note = self.get_note(target, note_identifier, category)
        if not note:
            self.caller.msg(f"Note not found: {note_identifier}")
            return

        if approve:
            note.is_approved = True
            note.approved_by = self.caller.account
            note.approved_at = timezone.now()
            action = "approved"
        else:
            note.is_approved = False
            note.approved_by = None
            note.approved_at = None
            action = "unapproved"

        note.save()

        self.caller.msg(f"Note '{note.name}' has been {action}.")
        if target != self.caller:
            target.msg(f"Your note '{note.name}' has been {action} by {self.caller.name}.")

        self.display_note(note)

    def get_note(self, target, identifier, category=None):
        note = target.get_note(identifier)
        if category and note and note.category.lower() != category.lower():
            return None
        return note

    def display_note(self, note, target=None):
        viewer = target or self.caller
        width = 78

        # Header
        output = header(f"Note #{note.id}", width=width, color="|c", fillchar="|r=|n")

        # Note details
        output += format_stat("Note Title:", note.name, width=width) + "\n"
        output += format_stat("Visibility:", "Private" if not note.is_public else "Public", width=width) + "\n"
        
        if note.is_approved:
            approved_by = note.approved_by.username if note.approved_by else "Unknown"
            approved_date = note.approved_at.strftime('%a %b %d %H:%M:%S %Y') if note.approved_at else "Unknown"
            output += format_stat("Approved:", f"{approved_by} - {approved_date}", width=width) + "\n"
        else:
            output += format_stat("Approved:", "No", width=width) + "\n"

        # Divider
        output += divider("", width=width, fillchar="-", color="|r") + "\n"

        # Note content
        wrapped_content = wrap_ansi(note.text, width=width-2)
        output += wrapped_content + "\n"

        # Footer
        output += footer(width=width, fillchar="|r=|n")

        viewer.msg(output)