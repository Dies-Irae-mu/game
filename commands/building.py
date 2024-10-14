from evennia import CmdSet
from evennia.commands.default.building import ObjManipCommand
from evennia import Command
from evennia.utils import evtable

class CmdSetRoomResources(ObjManipCommand):
    """
    Set the resources value for a room.

    Usage:
      +res [<room>] = <value>

    Sets the 'resources' attribute of a room to the specified integer value.
    If no room is specified, it sets the attribute for the current room.

    Example:
      +res = 4
      +res Temple of Doom = 5
    """

    key = "+res"
    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: +res [<room>] = <value>")
            return

        if self.rhs is None:
            self.caller.msg("You must specify a value. Usage: +res [<room>] = <value>")
            return

        try:
            value = int(self.rhs)
        except ValueError:
            self.caller.msg("The resources value must be an integer.")
            return

        if self.lhs:
            obj = self.caller.search(self.lhs, global_search=True)
        else:
            obj = self.caller.location

        if not obj:
            return

        if not obj.is_typeclass("typeclasses.rooms.RoomParent"):
            self.caller.msg("You can only set resources on rooms.")
            return

        obj.db.resources = value
        self.caller.msg(f"Set resources to {value} for {obj.get_display_name(self.caller)}.")

class CmdSetRoomType(ObjManipCommand):
    """
    Set the room type for a room.

    Usage:
      +roomtype [<room>] = <type>

    Sets the 'roomtype' attribute of a room to the specified string value.
    If no room is specified, it sets the attribute for the current room.

    Example:
      +roomtype = Beach Town
      +roomtype Evil Lair = Villain Hideout
    """

    key = "+roomtype"
    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: +roomtype [<room>] = <type>")
            return

        if self.rhs is None:
            self.caller.msg("You must specify a room type. Usage: +roomtype [<room>] = <type>")
            return

        if self.lhs:
            obj = self.caller.search(self.lhs, global_search=True)
        else:
            obj = self.caller.location

        if not obj:
            return

        if not obj.is_typeclass("typeclasses.rooms.RoomParent"):
            self.caller.msg("You can only set room types on rooms.")
            return

        obj.db.roomtype = self.rhs
        self.caller.msg(f"Set room type to '{self.rhs}' for {obj.get_display_name(self.caller)}.")

class CmdSetUmbraDesc(Command):
    """
    Set the Umbra description for a room.

    Usage:
      @umbradesc <description>

    This command sets the Umbra description for the current room.
    The description will be shown when characters peek into or
    enter the Umbra version of this room.
    """

    key = "@umbradesc"
    locks = "cmd:perm(Builders)"
    help_category = "Building"

    def func(self):
        """Execute command."""
        caller = self.caller
        location = caller.location

        if not self.args:
            caller.msg("Usage: @umbradesc <description>")
            return

        location.db.umbra_desc = self.args.strip()
        caller.msg(f"Umbra description set for {location.get_display_name(caller)}.")

class CmdSetGauntlet(Command):
    """
    Set the Gauntlet rating for a room.

    Usage:
      @setgauntlet <rating>

    This command sets the Gauntlet rating for the current room.
    The rating should be a number, typically between 3 and 9.
    This affects the difficulty of peeking into or entering the Umbra.
    """

    key = "@setgauntlet"
    locks = "cmd:perm(Builders)"
    help_category = "Building"

    def func(self):
        """Execute command."""
        caller = self.caller
        location = caller.location

        if not self.args:
            caller.msg("Usage: @setgauntlet <rating>")
            return

        try:
            rating = int(self.args)
            if 1 <= rating <= 10:
                location.db.gauntlet_difficulty = rating
                caller.msg(f"Gauntlet rating for {location.get_display_name(caller)} set to {rating}.")
            else:
                caller.msg("The Gauntlet rating should be between 1 and 10.")
        except ValueError:
            caller.msg("Please provide a valid number for the Gauntlet rating.")

class CmdUmbraInfo(Command):
    """
    Display Umbra-related information for a room.

    Usage:
      @umbrainfo

    This command shows the current Umbra description and Gauntlet
    rating for the current room.
    """

    key = "@umbrainfo"
    locks = "cmd:perm(Builders)"
    help_category = "Building"

    def func(self):
        """Execute command."""
        caller = self.caller
        location = caller.location

        umbra_desc = location.db.umbra_desc or "Not set"
        gauntlet_rating = location.db.gauntlet_difficulty or "Default (6)"

        table = evtable.EvTable(border="table")
        table.add_row("|wRoom|n", location.get_display_name(caller))
        table.add_row("|wUmbra Description|n", umbra_desc)
        table.add_row("|wGauntlet Rating|n", gauntlet_rating)

        caller.msg(table)

class BuildingCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdSetRoomResources())
        self.add(CmdSetRoomType())
        self.add(CmdSetUmbraDesc())
        self.add(CmdSetGauntlet())
        self.add(CmdUmbraInfo())