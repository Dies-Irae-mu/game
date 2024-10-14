import unittest
from evennia import create_object
from evennia.utils.test_resources import EvenniaCommandTest
from typeclasses.rooms import RoomParent
from typeclasses.characters import Character
from commands.oss.oss_commands import CmdSetResolve, CmdSetInfrastructure, CmdSetOrder, CmdInitializeHierarchy

class OSSHierarchyTest(EvenniaCommandTest):

    def setUp(self):
        super().setUp()

        # Create a mock caller
        self.caller = create_object(Character, key="TestCaller")

        # Create a parent room which will hold the districts
        self.parent_room = create_object(RoomParent, key="ParentRoom")

        self.districts = []
        self.sectors = []
        self.neighborhoods = []
        self.sites = []

        # Create 3 districts within the parent room
        for i in range(3):
            district = create_object(RoomParent, key=f"TestDistrict{i + 1}")
            district.db.location_type = None  # Ensure it's not set prematurely
            district.move_to(self.parent_room)  # Properly move the district to the parent room
            self.districts.append(district)

            # Create 4 sectors for each district
            for j in range(4):
                sector = create_object(RoomParent, key=f"TestSector{i + 1}-{j + 1}")
                sector.db.location_type = None
                sector.move_to(district)  # Properly move the sector to the district
                self.sectors.append(sector)

                # Create 4 neighborhoods for each sector
                for k in range(4):
                    neighborhood = create_object(RoomParent, key=f"TestNeighborhood{i + 1}-{j + 1}-{k + 1}")
                    neighborhood.db.location_type = None
                    neighborhood.move_to(sector)  # Properly move the neighborhood to the sector
                    self.neighborhoods.append(neighborhood)

                    # Create 4 sites for each neighborhood
                    for l in range(4):
                        site = create_object(RoomParent, key=f"TestSite{i + 1}-{j + 1}-{k + 1}-{l + 1}")
                        site.db.location_type = None
                        site.move_to(neighborhood)  # Properly move the site to the neighborhood
                        self.sites.append(site)

    def test_hierarchy_and_set_commands(self):
        # Set the caller's location to the parent room
        self.caller.location = self.parent_room

        # Call the initialize hierarchy command
        response = self.call(CmdInitializeHierarchy(), "", caller=self.caller)

        # Verify that the hierarchy was initialized correctly
        self.assertEqual(self.districts[0].db.location_type, "District")
        for sector_room in self.districts[0].contents:
            self.assertEqual(sector_room.db.location_type, "Sector")
            for neighborhood_room in sector_room.contents:
                self.assertEqual(neighborhood_room.db.location_type, "Neighborhood")
                for site_room in neighborhood_room.contents:
                    self.assertEqual(site_room.db.location_type, "Site")

        # Test setting resolve for a neighborhood
        self.caller.location = self.neighborhoods[0]
        self.call(CmdSetResolve(), "10", "Room 'TestNeighborhood1-1-1' resolve set to 10.", caller=self.caller)
        self.assertEqual(self.neighborhoods[0].db.resolve, 10)

        # Check if sector's resolve has been updated
        sector = self.neighborhoods[0].db.parent_location
        avg_resolve = sum(neigh.db.resolve for neigh in sector.contents) / len(sector.contents)
        self.assertEqual(sector.db.resolve, avg_resolve)

        # Test setting infrastructure for a neighborhood
        self.call(CmdSetInfrastructure(), "8", "Room 'TestNeighborhood1-1-1' infrastructure set to 8.", caller=self.caller)
        self.assertEqual(self.neighborhoods[0].db.infrastructure, 8)

        # Check if sector's infrastructure has been updated
        avg_infrastructure = sum(neigh.db.infrastructure for neigh in sector.contents) / len(sector.contents)
        self.assertEqual(sector.db.infrastructure, avg_infrastructure)

        # Test setting order for a neighborhood
        self.call(CmdSetOrder(), "12", "Room 'TestNeighborhood1-1-1' order set to 12.", caller=self.caller)
        self.assertEqual(self.neighborhoods[0].db.order, 12)

        # Check if sector's order has been updated
        avg_order = sum(neigh.db.order for neigh in sector.contents) / len(sector.contents)
        self.assertEqual(sector.db.order, avg_order)