"""City generation function call module for handling city creation operations.

This module provides a high-level interface for city generation operations including
creating roads, buildings, and elements, as well as exporting the generated city data.
"""
from typing import List

from simworld.citygen.city.city_generator import CityGenerator
from simworld.citygen.dataclass import Point, Segment
from simworld.config import Config
from simworld.utils.data_exporter import DataExporter


class CityFunctionCall:
    """Function call interface for city generation operations."""

    def __init__(self, config: Config):
        """Initialize the city function call with configuration.

        Args:
            config: Configuration object with simulation parameters.
        """
        self.city_generator = CityGenerator(config)

    def generate_city(self):
        """Generate city randomly with roads, buildings and elements."""
        self.city_generator.generate()

    def export_city(self, output_path: str):
        """Export city data to JSON files.

        Args:
            output_path: Directory path where the city data will be exported.
        """
        exporter = DataExporter(self.city_generator)
        exporter.export_to_json(output_path)

    def add_road(self, start: List[float], end: List[float]) -> int:
        """Add a road segment to the city.

        Args:
            start: Starting coordinates [x, y] of the road.
            end: Ending coordinates [x, y] of the road.

        Returns:
            ID of the newly added road segment.
        """
        StartPoint = Point(start[0], start[1])
        EndPoint = Point(end[0], end[1])
        self.city_generator.road_manager.add_segment(Segment(StartPoint, EndPoint))
        return len(self.city_generator.road_manager.roads) - 1

    def remove_road(self, id: int) -> bool:
        """Remove a road segment from the city.

        Args:
            id: ID of the road segment to remove.

        Returns:
            True if the road was successfully removed, False otherwise.
        """
        try:
            segment = self.city_generator.road_manager.get_segment_by_id(id)
            self.city_generator.road_manager.remove_segment(segment)
            return True
        except IndexError:
            return False

    def modify_road(self, id: int, start: List[float], end: List[float]) -> bool:
        """Modify an existing road segment.

        Args:
            id: ID of the road segment to modify.
            start: New starting coordinates [x, y] of the road.
            end: New ending coordinates [x, y] of the road.

        Returns:
            True if the road was successfully modified, False otherwise.
        """
        try:
            segment = self.city_generator.road_manager.get_segment_by_id(id)
            old_segment = Segment(segment.start, segment.end)
            segment.start = Point(start[0], start[1])
            segment.end = Point(end[0], end[1])
            self.city_generator.road_manager.update_segment(old_segment, segment)
            return True
        except IndexError:
            return False

    def generate_road_network(self, num_segments: int):
        """Generate a procedural road network.

        Args:
            num_segments: Target number of road segments to generate.
        """
        self.city_generator.road_generator.generate_initial_segments()
        while len(self.city_generator.road_manager.roads) < num_segments:
            self.city_generator.road_generator.generate_step()
        self.city_generator.road_generator.find_intersections()

    def generate_building_alone_road(self, road_id: int):
        """Generate buildings along a single road.

        Args:
            road_id: ID of the road to generate buildings along.
        """
        segment = self.city_generator.road_manager.get_segment_by_id(road_id)
        self.city_generator.building_generator.generate_buildings_along_segment(segment, self.city_generator.road_manager.road_quadtree)

    def generate_building_alone_roads(self):
        """Generate buildings along all roads in the city."""
        for road in self.city_generator.road_manager.roads:
            self.city_generator.building_generator.generate_buildings_along_segment(road, self.city_generator.road_manager.road_quadtree)

    def generate_element_alone_road(self, road_id: int):
        """Generate elements along a single road.

        Args:
            road_id: ID of the road to generate elements along.
        """
        segment = self.city_generator.road_manager.get_segment_by_id(road_id)
        elements = self.city_generator.element_generator._add_elements_spline_road(segment)
        for element in elements:
            if self.city_generator.element_manager.can_place_element(element.bounds):
                self.city_generator.element_manager.add_element(element)

    def generate_element_alone_roads(self):
        """Generate elements along all roads in the city."""
        for road in self.city_generator.road_manager.roads:
            elements = self.city_generator.element_generator._add_elements_spline_road(road)
            for element in elements:
                if self.city_generator.element_manager.can_place_element(element.bounds):
                    self.city_generator.element_manager.add_element(element)

    def generate_element_around_buildings(self):
        """Generate elements around all buildings in the city."""
        for building in self.city_generator.building_manager.buildings:
            elements = self.city_generator.element_generator._add_elements_around_building(building)
            for element in elements:
                if self.city_generator.element_manager.can_place_element(element.bounds):
                    self.city_generator.element_manager.add_element(element)
        self.city_generator.element_generator.filter_elements_by_buildings(self.city_generator.building_quadtree)
