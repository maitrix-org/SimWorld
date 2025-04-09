from typing import List

from simworld.citygen.dataclass import Building, Bounds
from simworld.utils.quadtree import QuadTree
from simworld.utils.bbox_utils import BboxUtils

class BuildingManager:
    def __init__(self, config):
        self.config = config
        self.building_quadtree = QuadTree[Building](
            Bounds(self.config['citygen.quadtree.bounds.x'], self.config['citygen.quadtree.bounds.y'], self.config['citygen.quadtree.bounds.width'], self.config['citygen.quadtree.bounds.height']), 
            self.config['citygen.quadtree.max_objects'], 
            self.config['citygen.quadtree.max_levels'])
        self.buildings: List[Building] = []

    def can_place_building(self, bounds: Bounds, buffer: float = None) -> bool:
        """Check if a building can be placed at the specified location"""
        if buffer is None:
            buffer = self.config['citygen.building.building_building_distance']

        # Add buffer spacing to extend check range
        check_bounds = Bounds(
            bounds.x - buffer,
            bounds.y - buffer,
            bounds.width + 2 * buffer,
            bounds.height + 2 * buffer,
            bounds.rotation,
        )

        # Check for collisions with existing buildings
        candidates = self.building_quadtree.retrieve(check_bounds)

        for building in candidates:
            if BboxUtils.bbox_overlap(building.bounds, check_bounds):
                return False
        return True

    def add_building(self, building: Building):
        """Add new building to manager"""
        self.buildings.append(building)
        # To be added to quadtree later
        self.building_quadtree.insert(building.bounds, building)

    def remove_building(self, building: Building):
        """Remove a building from the quadtree and list"""
        self.buildings.remove(building)
        self.building_quadtree.remove(building.bounds, building)