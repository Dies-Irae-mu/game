"""
Multi-description system command module.

This module implements a command that allows characters to store and manage
multiple descriptions that they can switch between.
"""

from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils import evtable
from evennia.utils.utils import crop
from evennia.utils.ansi import ANSIString
from world.wod20th.utils.formatting import header, footer, divider

class CmdMultidesc(MuxCommand):
    """
    Manage multiple character descriptions.

    Usage:
      +mdesc/list                     - List all your stored descriptions
      +mdesc/view <desc-name>         - View a particular description
      +mdesc/get <desc-list>          - Set your current description
      +mdesc/store <desc-name>=<text> - Create a new description
      +mdesc/kill <desc-name>         - Delete a stored description
      +mdesc/save <desc-name>         - Save your current description
      +mdesc/edit <desc>=<old>/<new>  - Edit a saved description

    This command lets you maintain multiple descriptions for your character
    that you can switch between. You can combine multiple descriptions by
    specifying them in a space-separated list with the /get switch.
    
    Special formatting:
      %r or %R  - Single line break
      %r%r or %R%R - Double line break (paragraph)
      %t or %T  - Tab indent (can be used multiple times)
    
    Examples:
      +mdesc/store base=A tall woman with auburn hair...%r%rShe stands with perfect posture.
      +mdesc/store casual=%tShe wears comfortable jeans...
      +mdesc/get base casual         - Combines both descriptions
      +mdesc/save winter            - Saves current description as 'winter'
      +mdesc/edit casual=jeans/slacks - Replaces 'jeans' with 'slacks' in 'casual'
    """
    
    key = "+mdesc"
    aliases = ["mdesc"]
    locks = "cmd:all()"
    help_category = "Description"
    switch_options = ("list", "view", "get", "store", "kill", "save", "edit")

    def _get_descs(self):
        """Get the character's stored descriptions."""
        if not self.caller.db.stored_descs:
            self.caller.db.stored_descs = {}
        return self.caller.db.stored_descs

    def _store_desc(self, name, text):
        """Store a description."""
        descs = self._get_descs()
        descs[name.lower()] = text
        self.caller.db.stored_descs = descs

    def _get_desc(self, name):
        """Get a specific description."""
        return self._get_descs().get(name.lower())

    def _delete_desc(self, name):
        """Delete a stored description."""
        descs = self._get_descs()
        if name.lower() in descs:
            del descs[name.lower()]
            self.caller.db.stored_descs = descs
            return True
        return False

    def _format_desc(self, desc):
        """Format description using character's format_description method."""
        if hasattr(self.caller, 'format_description'):
            return self.caller.format_description(desc)
        return desc

    def func(self):
        """Execute the command"""
        caller = self.caller
        if not self.switches:
            caller.msg(self.__doc__)
            return

        switch = self.switches[0].lower()

        if switch == "list":
            descs = self._get_descs()
            if not descs:
                caller.msg("You have no stored descriptions.")
                return
            
            # Create a formatted table with header
            output = [header("Stored Descriptions")]
            table = evtable.EvTable("|wName|n", "|wPreview|n", border="table", pad_width=1)
            for name, desc in sorted(descs.items()):
                # Show raw formatting codes in preview
                preview = desc.replace("%r", "[NL]").replace("%R", "[NL]")
                preview = preview.replace("%t", "[TAB]").replace("%T", "[TAB]")
                table.add_row(name, crop(preview, width=50))
            output.append(str(table))
            output.append(footer())
            caller.msg("\n".join(output))

        elif switch == "view":
            if not self.args:
                caller.msg("Usage: +mdesc/view <desc-name>")
                return
            desc = self._get_desc(self.args)
            if not desc:
                caller.msg(f"No description named '{self.args}' found.")
                return
            
            # Show both raw and formatted versions with proper headers
            output = [
                header(f"Description: {self.args}"),
                "|wRaw Format:|n\n" + desc + "\n",
                divider("Formatted Version"),
                self._format_desc(desc),
                footer()
            ]
            caller.msg("\n".join(output))

        elif switch == "get":
            if not self.args:
                caller.msg("Usage: +mdesc/get <desc-name1> [<desc-name2> ...]")
                return
            desc_names = self.args.split()
            final_desc = []
            for name in desc_names:
                desc = self._get_desc(name)
                if not desc:
                    caller.msg(f"No description named '{name}' found.")
                    return
                final_desc.append(desc)
            # Join with double line break to ensure proper spacing
            combined_desc = "%r%r".join(final_desc)
            caller.db.desc = combined_desc
            
            # Show the result with proper formatting
            output = [
                header("Description Updated"),
                self._format_desc(combined_desc),
                footer()
            ]
            caller.msg("\n".join(output))

        elif switch == "store":
            if not self.args or "=" not in self.args:
                caller.msg("Usage: +mdesc/store <desc-name>=<description>")
                return
            name, desc = self.args.split("=", 1)
            name = name.strip()
            if not name:
                caller.msg("You must provide a name for the description.")
                return
            # Store the raw description with its formatting codes
            self._store_desc(name, desc.strip())
            
            # Show confirmation and preview with proper formatting
            output = [
                header(f"Stored Description: {name}"),
                self._format_desc(desc.strip()),
                footer()
            ]
            caller.msg("\n".join(output))

        elif switch == "kill":
            if not self.args:
                caller.msg("Usage: +mdesc/kill <desc-name>")
                return
            if self._delete_desc(self.args):
                caller.msg(header("Description Deleted") + 
                         f"Deleted description '{self.args}'.\n" +
                         footer())
            else:
                caller.msg(f"No description named '{self.args}' found.")

        elif switch == "save":
            if not self.args:
                caller.msg("Usage: +mdesc/save <desc-name>")
                return
            current_desc = caller.db.desc
            if not current_desc:
                caller.msg("You don't have a current description to save.")
                return
            self._store_desc(self.args, current_desc)
            
            # Show confirmation and preview
            output = [
                header(f"Saved Current Description as: {self.args}"),
                self._format_desc(current_desc),
                footer()
            ]
            caller.msg("\n".join(output))

        elif switch == "edit":
            if not self.args or "=" not in self.args:
                caller.msg("Usage: +mdesc/edit <desc-name>=<old>/<new>")
                return
            try:
                name, rest = self.args.split("=", 1)
                old, new = rest.split("/", 1)
            except ValueError:
                caller.msg("Usage: +mdesc/edit <desc-name>=<old>/<new>")
                return

            name = name.strip()
            desc = self._get_desc(name)
            if not desc:
                caller.msg(f"No description named '{name}' found.")
                return

            if old not in desc:
                caller.msg(f"Text '{old}' not found in description '{name}'.")
                return

            new_desc = desc.replace(old, new)
            self._store_desc(name, new_desc)
            
            # Show the updated version with proper formatting
            output = [
                header(f"Updated Description: {name}"),
                self._format_desc(new_desc),
                footer()
            ]
            caller.msg("\n".join(output))

        else:
            caller.msg("Invalid switch. See help +mdesc for valid options.") 