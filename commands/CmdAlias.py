from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.search import search_object

class CmdAlias(MuxCommand):
    """
    Set an alias that others can use to refer to your character.
    
    Usage:
      alias me=<text>
      alias/remove
      alias <character>   - View someone's alias
    
    Examples:
      alias me=Lys       - Sets your alias to "Lys"
      alias/remove       - Removes your alias
      alias lysander     - Shows Lysander's alias
    
    This sets a short name that others can use to refer to you in commands
    like page, look, and +finger. For example, if Lysander sets their
    alias to "Lys", others can use "Lys" in place of "Lysander" in commands.
    """
    
    key = "alias"
    locks = "cmd:all()"
    help_category = "Chargen & Character Info"

    def func(self):
        if not self.args:
            # Show own alias
            alias = self.caller.attributes.get("alias", None)
            if alias:
                self.caller.msg(f"Your current alias is: {alias}")
            else:
                self.caller.msg("You have not set an alias.")
            return

        # Handle alias removal
        if "remove" in self.switches:
            self.caller.attributes.remove("alias")
            self.caller.msg("Your alias has been removed.")
            return

        # Handle viewing other's alias
        if "=" not in self.args:
            # Search for the character
            target = search_object(self.args, typeclass='typeclasses.characters.Character')
            if not target:
                self.caller.msg(f"Could not find character '{self.args}'.")
                return
            
            target = target[0]
            alias = target.attributes.get("alias", None)
            if alias:
                self.caller.msg(f"{target.name}'s alias is: {alias}")
            else:
                self.caller.msg(f"{target.name} has not set an alias.")
            return

        # Handle setting own alias
        if not self.args.startswith("me="):
            self.caller.msg("Usage: alias me=<text>")
            return

        new_alias = self.args.split("=", 1)[1].strip()

        # Validate alias
        if len(new_alias) < 2:
            self.caller.msg("Alias must be at least 2 characters long.")
            return
        
        if len(new_alias) > 15:
            self.caller.msg("Alias must be no longer than 15 characters.")
            return

        if not new_alias.isalnum():
            self.caller.msg("Alias must contain only letters and numbers.")
            return

        # Check if alias is already in use
        existing = search_object(new_alias, typeclass='typeclasses.characters.Character')
        for obj in existing:
            if obj != self.caller and (obj.key.lower() == new_alias.lower() or 
                                     obj.attributes.get("alias", "").lower() == new_alias.lower()):
                self.caller.msg("That alias is already in use.")
                return

        # Set the alias
        self.caller.attributes.add("alias", new_alias)
        self.caller.msg(f"Your alias has been set to: {new_alias}") 