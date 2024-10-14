from evennia import Command
from evennia.utils.evmenu import EvMenu
from evennia.utils.evtable import EvTable
from evennia.objects.models import ObjectDB
from typeclasses.rooms import RoomParent

class CmdShowHierarchy(Command):
    """
    Display Districts, Sectors, and Neighborhoods in a tree format.
    
    Usage:
        showhierarchy
    """
    key = "+ossmenu/showhierarchy"
    llocks = "cmd:perm(Builder) or perm(Admin)"
    help_category = "OSS"

    def func(self):
        districts = RoomParent.objects.filter(db_type="District")
        
        if not districts.exists():
            self.caller.msg("No Districts found.")
            return
        
        tree = []

        for district in districts:
            tree.append(f"District: {district.key}")
            sectors = RoomParent.objects.filter(db_type="Sector", db_district=district)
            if sectors.exists():
                for sector in sectors:
                    tree.append(f"  Sector: {sector.key}")
                    neighborhoods = RoomParent.objects.filter(db_type="Neighborhood", db_sector=sector)
                    if neighborhoods.exists():
                        for neighborhood in neighborhoods:
                            tree.append(f"    Neighborhood: {neighborhood.key}")
                    else:
                        tree.append("    No Neighborhoods found.")
            else:
                tree.append("  No Sectors found.")

        tree_display = "\n".join(tree)
        self.caller.msg(tree_display)

class CmdOssSetSector(Command):
    """
    Set the current room as a Sector within the specified District.
    
    Usage:
      +oss/setsector <district_name>
      
    This command sets the current room as a Sector under the specified District.
    """
    key = "+oss/setsector"
    locks = "cmd:perm(Builder) or perm(Immortal)"
    help_category = "OSS"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: +oss/setsector <district_name>")
            return
        
        district_name = self.args.strip()
        room = self.caller.location
        district = ObjectDB.objects.filter(db_key__iexact=district_name, db_type="District").first()

        if not district:
            self.caller.msg(f"Error: District '{district_name}' not found.")
            return

        if room.db.type and room.db.type != "Sector":
            self.caller.msg(f"Error: Room '{room.key}' is already set as a '{room.db.type}'.")
            return

        room.set_as_sector()
        district.add_sub_location(room)
        self.caller.msg(f"Room '{room.key}' set as a Sector under District '{district.key}'.")

class CmdOssSetNeighborhood(Command):
    """
    Set the current room as a Neighborhood within the specified Sector.
    
    Usage:
      +oss/setneighborhood <sector_name>
      
    This command sets the current room as a Neighborhood under the specified Sector.
    """
    key = "+oss/setneighborhood"
    locks = "cmd:perm(Builder) or perm(Immortal)"
    help_category = "OSS"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: +oss/setneighborhood <sector_name>")
            return
        
        sector_name = self.args.strip()
        room = self.caller.location
        sector = ObjectDB.objects.filter(db_key__iexact=sector_name, db_type="Sector").first()

        if not sector:
            self.caller.msg(f"Error: Sector '{sector_name}' not found.")
            return

        if room.db.type and room.db.type != "Neighborhood":
            self.caller.msg(f"Error: Room '{room.key}' is already set as a '{room.db.type}'.")
            return

        room.set_as_neighborhood()
        sector.add_sub_location(room)
        self.caller.msg(f"Room '{room.key}' set as a Neighborhood under Sector '{sector.key}'.")

class CmdOssSetSite(Command):
    """
    Set the current room as a Site within the specified Neighborhood.
    
    Usage:
      +oss/setsite <neighborhood_name>
      
    This command sets the current room as a Site under the specified Neighborhood.
    """
    key = "+oss/setsite"
    locks = "cmd:perm(Builder) or perm(Immortal)"
    help_category = "OSS"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: +oss/setsite <neighborhood_name>")
            return
        
        neighborhood_name = self.args.strip()
        room = self.caller.location
        neighborhood = ObjectDB.objects.filter(db_key__iexact=neighborhood_name, db_type="Neighborhood").first()

        if not neighborhood:
            self.caller.msg(f"Error: Neighborhood '{neighborhood_name}' not found.")
            return

        if room.db.type and room.db.type != "Site":
            self.caller.msg(f"Error: Room '{room.key}' is already set as a '{room.db.type}'.")
            return

        room.set_as_site()
        neighborhood.add_sub_location(room)
        self.caller.msg(f"Room '{room.key}' set as a Site under Neighborhood '{neighborhood.key}'.")

class CmdOssSetCurrentRoom(Command):
    """
    Set the current room as a sub-location of its parent.
    
    Usage:
      +oss/setcurrentroom
    
    This command sets the current room as a sub-location of its parent if the types are correct.
    """
    key = "+oss/setcurrentroom"
    locks = "cmd:perm(Builder) or perm(Immortal)"
    help_category = "OSS"

    def func(self):
        room = self.caller.location
        parent = room.db.parent_location
        
        if not parent:
            self.caller.msg("Error: This room has no parent location to set it under.")
            return

        if parent.db.type == "District" and not room.db.type:
            room.set_as_sector()
            parent.add_sub_location(room)
            self.caller.msg(f"Room '{room.key}' set as a Sector under District '{parent.key}'.")

        elif parent.db.type == "Sector" and not room.db.type:
            room.set_as_neighborhood()
            parent.add_sub_location(room)
            self.caller.msg(f"Room '{room.key}' set as a Neighborhood under Sector '{parent.key}'.")

        elif parent.db.type == "Neighborhood" and not room.db.type:
            room.set_as_site()
            parent.add_sub_location(room)
            self.caller.msg(f"Room '{room.key}' set as a Site under Neighborhood '{parent.key}'.")

        else:
            self.caller.msg(f"Error: Invalid parent-child type relationship between '{parent.db.type}' and '{room.db.type}'.")

class CmdOssSetDistrict(Command):
    """
    Set the current room as a District.
    
    Usage:
      +oss/setdistrict

    This command sets the current room as a District.
    """
    key = "+oss/setdistrict"
    locks = "cmd:perm(Builder) or perm(Immortal)"
    help_category = "OSS"

    def func(self):
        room = self.caller.location

        if room.db.type and room.db.type != "District":
            self.caller.msg(f"Error: Room '{room.key}' is already set as a '{room.db.type}'.")
            return

        room.set_as_district()
        self.caller.msg(f"Room '{room.key}' is now set as a District.")

class CmdSetResolve(Command):
    """
    Set the resolve value of the current room if it's a Neighborhood.
    
    Usage:
      +oss/setresolve <value>
      
    This command sets the resolve value of the current room if it is a Neighborhood.
    """
    key = "+oss/setresolve"
    locks = "cmd:perm(Builder) or perm(Immortal)"
    help_category = "OSS"

    def func(self):
        room = self.caller.location

        # Check if the room is a Neighborhood
        if room.db.location_type != "Neighborhood":
            self.caller.msg(f"Error: Room '{room.key}' is not a Neighborhood.")
            return

        if not self.args.isdigit():
            self.caller.msg("Usage: +oss/setresolve <value>")
            return
        
        value = int(self.args)

        room.set_resolve(value)
        self.caller.msg(f"Room '{room.key}' resolve set to {value}.")

class CmdSetInfrastructure(Command):
    """
    Set the infrastructure value of the current room if it's a Neighborhood.
    
    Usage:
      +oss/setinfrastructure <value>
      
    This command sets the infrastructure value of the current room if it is a Neighborhood.
    """
    key = "+oss/setinfrastructure"
    locks = "cmd:perm(Builder) or perm(Immortal)"
    help_category = "OSS"

    def func(self):
        room = self.caller.location

        # Check if the room is a Neighborhood
        if room.db.location_type != "Neighborhood":
            self.caller.msg(f"Error: Room '{room.key}' is not a Neighborhood.")
            return

        if not self.args.isdigit():
            self.caller.msg("Usage: +oss/setinfrastructure <value>")
            return
        
        value = int(self.args)

        room.set_infrastructure(value)
        self.caller.msg(f"Room '{room.key}' infrastructure set to {value}.")

class CmdSetOrder(Command):
    """
    Set the order value of the current room if it's a Neighborhood.
    
    Usage:
      +oss/setorder <value>
      
    This command sets the order value of the current room if it is a Neighborhood.
    """
    key = "+oss/setorder"
    locks = "cmd:perm(Builder) or perm(Immortal)"
    help_category = "OSS"

    def func(self):
        room = self.caller.location

        # Check if the room is a Neighborhood
        if room.db.location_type != "Neighborhood":
            self.caller.msg(f"Error: Room '{room.key}' is not a Neighborhood.")
            return

        if not self.args.isdigit():
            self.caller.msg("Usage: +oss/setorder <value>")
            return
        
        value = int(self.args)

        room.set_order(value)
        self.caller.msg(f"Room '{room.key}' order set to {value}.")

class CmdInitializeHierarchy(Command):
    """
    Initialize all sub-rooms in the current room as districts, sectors, neighborhoods, and sites.
    
    Usage:
      +oss/init_hierarchy
    
    This command will set the current room's immediate sub-rooms as districts, 
    their children as sectors, their children as neighborhoods, and their children as sites.
    """
    key = "+oss/init_hierarchy"
    locks = "cmd:perm(Builder) or perm(Immortal)"
    help_category = "OSS"

    def func(self):
        room = self.caller.location
        table = EvTable("Room Name", "Type", "Action", border="cells")

        # Report the contents of the current room
        contents_str = ", ".join(obj.key for obj in room.contents)
        if contents_str:
            table.add_row(room.key, "Parent Room", f"Contains: {contents_str}")
        else:
            table.add_row(room.key, "Parent Room", "Warning: No RoomParent sub-rooms")

        # Check if the current room has any contents
        if not room.contents:
            table.add_row(room.key, "Parent Room", "Error: No sub-rooms to initialize.")
            self.caller.msg(str(table))
            return

        # Step 1: Set immediate sub-rooms as Districts
        for district_room in room.contents:
            if isinstance(district_room, RoomParent):
                action = ""
                if district_room.db.location_type != "District":
                    district_room.set_as_district()
                    action = "Set as District"
                else:
                    action = "Already a District"
                
                # Warn if the district has no contents
                if not district_room.contents:
                    action += " | Warning: No sub-rooms (Sectors)"
                
                table.add_row(district_room.key, "District", action)
                
                # Step 2: Set children of Districts as Sectors
                for sector_room in district_room.contents:
                    if isinstance(sector_room, RoomParent):
                        action = ""
                        if sector_room.db.location_type != "Sector":
                            sector_room.set_as_sector()
                            district_room.add_sub_location(sector_room)
                            action = "Set as Sector"
                        else:
                            action = "Already a Sector"
                        
                        # Warn if the sector has no contents
                        if not sector_room.contents:
                            action += " | Warning: No sub-rooms (Neighborhoods)"
                        
                        table.add_row(sector_room.key, "Sector", action)
                        
                        # Step 3: Set children of Sectors as Neighborhoods
                        for neighborhood_room in sector_room.contents:
                            if isinstance(neighborhood_room, RoomParent):
                                action = ""
                                if neighborhood_room.db.location_type != "Neighborhood":
                                    neighborhood_room.set_as_neighborhood()
                                    sector_room.add_sub_location(neighborhood_room)
                                    action = "Set as Neighborhood"
                                else:
                                    action = "Already a Neighborhood"
                                
                                # Warn if the neighborhood has no contents
                                if not neighborhood_room.contents:
                                    action += " | Warning: No sub-rooms (Sites)"
                                
                                table.add_row(neighborhood_room.key, "Neighborhood", action)
                                
                                # Step 4: Set children of Neighborhoods as Sites
                                for site_room in neighborhood_room.contents:
                                    if isinstance(site_room, RoomParent):
                                        action = ""
                                        if site_room.db.location_type != "Site":
                                            site_room.set_as_site()
                                            neighborhood_room.add_sub_location(site_room)
                                            action = "Set as Site"
                                        else:
                                            action = "Already a Site"
                                        
                                        table.add_row(site_room.key, "Site", action)
                                    else:
                                        table.add_row(site_room.key, "Site", "Warning: Not a RoomParent, skipping")
                            else:
                                table.add_row(neighborhood_room.key, "Neighborhood", "Warning: Not a RoomParent, skipping")
                    else:
                        table.add_row(sector_room.key, "Sector", "Warning: Not a RoomParent, skipping")
            else:
                table.add_row(district_room.key, "District", "Warning: Not a RoomParent, skipping")
        
        # Final message to indicate completion
        table.add_row("", "", "Hierarchy initialization completed.")

        # Output the table
        self.caller.msg(str(table))



