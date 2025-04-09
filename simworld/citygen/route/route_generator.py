import random
from typing import List

from simworld.citygen.dataclass import (
    Segment,
    Building,
    Element,
    Point,
    Bounds
)
from simworld.citygen.route.route_manager import RouteManager
from simworld.utils.math_utils import MathUtils
from simworld.utils.quadtree import QuadTree

class RouteGenerator:
    def __init__(self, config):
        self.config = config
        self.route_manager = RouteManager()

    def generate_route_along_road(self, road: Segment):
        """Generate a route along a road segment"""
        # Generate random number of points along road
        num_points = random.randint(self.config['citygen.route.min_points_per_route'], self.config['citygen.route.max_points_per_route'])
        points = []
        print(f"Generating route with {num_points} points")
        for _ in range(num_points):
            # Generate random point along road segment
            point = MathUtils.interpolate_point(road.start, road.end, random.random())
            points.append(point)
        self.route_manager.add_route_points(points)

    def generate_route_based_on_elements(self, elements: List[Element]):
        """Generate routes based on elements' positions"""
        num_points = 2
        element = random.sample(elements, 1)[0]
        points = []
        for _ in range(num_points):
            point = element.center
            points.append(point)
        self.route_manager.add_route_points(points)

    def generate_target_point_randomly(self):
        elements = self.element_manager.elements
        element = random.sample(elements, 1)[0]
        target_point = element.center
        return target_point
    
    def get_point_around_label(self, point: Point, quadtrees: List[QuadTree], distance: float = 50, k: int = 5):
        """Get the label of a point based on its K nearest neighbors"""
        bounds = Bounds(point.x - distance, point.y - distance, 2 * distance, 2 * distance)
        # print(bounds)
        neighbors = []
        for quadtree in quadtrees:
            nodes = quadtree.retrieve(bounds)
            neighbors += nodes

        # Count different types of neighbors
        elements = [neighbor for neighbor in neighbors if isinstance(neighbor, Element)][:k]
        buildings = [neighbor for neighbor in neighbors if isinstance(neighbor, Building)][:k]
        segments = [neighbor for neighbor in neighbors if isinstance(neighbor, Segment)][:k]

        element_types = [element.element_type for element in elements]
        building_types = [building.building_type for building in buildings]

        element_stats = {element_type.name: element_types.count(element_type) for element_type in element_types}

        building_stats = {building.building_type.name: MathUtils.get_direction_description_for_points(point, building.center) for building in buildings}

        stats = {
            'element_stats': element_stats,
            'building_stats': building_stats,
        }

        return stats