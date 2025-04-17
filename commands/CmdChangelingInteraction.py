from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.utils import make_iter

class CmdChangelingInteraction(MuxCommand):
    """
    Interact with the Fae realm.

    Usage:
      +flook
      +flook <character name>
      +femit <message>
      +fpose <action>

    +flook: See the fae description of your surroundings and people.
    +flook <character>: See the fae description of a specific character.
    +femit: Emit a message visible only to Changelings and Kinain.
    +fpose: Pose an action visible only to Changelings and Kinain.
    """

    key = "+flook"
    aliases = ["+femit", "+fpose"]
    locks = "cmd:all()"
    help_category = "Changeling"

    def func(self):
        """Execute command."""
        # Check if in a Quiet Room
        if (hasattr(self.caller.location, 'db') and 
            hasattr(self.caller.location, 'is_command_restricted_in_quiet_room') and
            self.caller.location.is_command_restricted_in_quiet_room(self.cmdstring)):
            self.caller.msg("|rYou are in a Quiet Room and cannot use fae interaction commands here.|n")
            return
            
        splat = self.caller.db.stats['other']['splat'].get('Splat', {}).get('perm', '')
        
        # Check if character is either a Changeling or Kinain
        is_kinain = (splat == 'Mortal+' and 
                    self.caller.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm') == 'Kinain')
        
        # Only allow Changelings and Kinain to use these commands
        if not (splat == 'Changeling' or is_kinain):
            self.caller.msg("You don't have the ability to interact with the Fae realm.")
            return

        if self.cmdstring == "+flook":
            self.do_flook()
        elif self.cmdstring == "+femit":
            self.do_femit()
        elif self.cmdstring == "+fpose":
            self.do_fpose()

    def do_flook(self):
        """Handle viewing fae descriptions."""
        if not self.args:
            self.view_room_fae()
        else:
            self.view_character_fae(self.args)

    def view_room_fae(self):
        """View fae description of the room and its occupants."""
        location = self.caller.location
        if not location:
            self.caller.msg("You are nowhere.")
            return

        # Get the fae description of the room
        fae_desc = location.db.fae_desc or "This place has no special fae aspect."
        
        # Start with the room's fae description
        fae_view = f"Fae Aspect of {location.name}:\n{fae_desc}\n\n"

        # Add fae descriptions of characters in the room
        characters = [obj for obj in location.contents if obj.has_account and obj != self.caller]
        if characters:
            fae_view += "Fae Aspects of People:\n"
            for character in characters:
                char_fae_desc = character.db.fae_desc or f"{character.name} has no visible fae aspect."
                fae_view += f"{character.name}: {char_fae_desc}\n"

        self.caller.msg(fae_view)

    def view_character_fae(self, character_name):
        """View fae description of a specific character."""
        target = self.caller.search(character_name)
        if not target:
            return

        if not hasattr(target, 'get_fae_description'):
            self.caller.msg(f"{target.name} has no fae aspect.")
            return

        fae_desc = target.get_fae_description()
        self.caller.msg(f"Fae Aspect of {target.name}:\n{fae_desc}")

    def do_femit(self):
        """Handle fae emit."""
        if not self.args:
            self.caller.msg("Usage: +femit <message>")
            return

        # Get all Changelings and Kinain in the room
        fae_perceivers = [obj for obj in self.caller.location.contents 
                          if obj.has_account and self.is_fae_perceiver(obj)]

        # Emit the message to all fae perceivers
        for perceiver in fae_perceivers:
            perceiver.msg(f"|c[Fae Realm] {self.args}|n")

        # Confirm to the emitter
        self.caller.msg(f"You fae-emit: {self.args}")

    def do_fpose(self):
        """Handle fae pose."""
        if not self.args:
            self.caller.msg("Usage: +fpose <action>")
            return

        # Get all Changelings and Kinain in the room
        fae_perceivers = [obj for obj in self.caller.location.contents 
                          if obj.has_account and self.is_fae_perceiver(obj)]

        # Pose the action to all fae perceivers
        for perceiver in fae_perceivers:
            if perceiver == self.caller:
                perceiver.msg(f"|c[Fae Realm] You {self.args}|n")
            else:
                perceiver.msg(f"|c[Fae Realm] {self.caller.name} {self.args}|n")

        # Confirm to the poser
        self.caller.msg(f"You fae-pose: {self.caller.name} {self.args}")

    def is_fae_perceiver(self, character):
        """Check if a character is a Changeling or Kinain."""
        if not character.db.stats or 'other' not in character.db.stats or 'splat' not in character.db.stats['other']:
            return False
            
        splat = character.db.stats['other']['splat'].get('Splat', {}).get('perm', '')
        
        # Check for Kinain (Mortal+ with Type Kinain)
        is_kinain = (splat == 'Mortal+' and 
                    character.db.stats.get('identity', {}).get('lineage', {}).get('Type', {}).get('perm') == 'Kinain')
                    
        return splat == 'Changeling' or is_kinain
