from simworld.citygen.city.city_generator import CityGenerator
from simworld.utils.data_exporter import DataExporter
from simworld.citygen.dataclass import Point, Segment
from typing import List
from simworld.config import Config
import os

class CityFunctionCall:
    """Function call for city"""

    def __init__(self, config: Config):
        """Initialize function call"""
        self.city_generator = CityGenerator(config)

    def generate_city(self):
        """Generate city randomly with roads, buildings and elements"""
        self.city_generator.generate()

    def export_city(self, output_path: str):
        """Export city"""
        exporter = DataExporter(self.city_generator)
        exporter.export_to_json(output_path)

    def add_road(self, start: List[float], end: List[float]) -> int:
        """Add road"""
        StartPoint = Point(start[0], start[1])
        EndPoint = Point(end[0], end[1])
        self.city_generator.road_manager.add_segment(Segment(StartPoint, EndPoint))
        return len(self.city_generator.road_manager.roads) - 1

    def remove_road(self, id: int) -> bool:
        """Remove road"""
        try:
            segment = self.city_generator.road_manager.get_segment_by_id(id)
            self.city_generator.road_manager.remove_segment(segment)
            return True
        except IndexError:
            return False

    def modify_road(self, id: int, start: List[float], end: List[float]) -> bool:
        """Modify road"""
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
        """Generate road network"""
        self.city_generator.road_generator.generate_initial_segments()
        while len(self.city_generator.road_manager.roads) < num_segments:
            self.city_generator.road_generator.generate_step()
        self.city_generator.road_generator.find_intersections()

    def generate_building_alone_road(self, road_id: int):
        """Generate building alone road"""
        segment = self.city_generator.road_manager.get_segment_by_id(road_id)
        self.city_generator.building_generator.generate_buildings_along_segment(segment, self.city_generator.road_manager.road_quadtree)

    def generate_building_alone_roads(self):
        """Generate building alone roads"""
        for road in self.city_generator.road_manager.roads:
            self.city_generator.building_generator.generate_buildings_along_segment(road, self.city_generator.road_manager.road_quadtree)

    def generate_element_alone_road(self, road_id: int):
        """Generate element alone road"""
        segment = self.city_generator.road_manager.get_segment_by_id(road_id)
        elements = self.city_generator.element_generator._add_elements_spline_road(segment)
        for element in elements:
            if self.city_generator.element_manager.can_place_element(element.bounds):
                self.city_generator.element_manager.add_element(element)

    def generate_element_alone_roads(self):
        """Generate element alone roads"""
        for road in self.city_generator.road_manager.roads:
            elements = self.city_generator.element_generator._add_elements_spline_road(road)
            for element in elements:
                if self.city_generator.element_manager.can_place_element(element.bounds):
                    self.city_generator.element_manager.add_element(element)

    def generate_element_around_buildings(self):
        """Generate element around buildings"""
        for building in self.city_generator.building_manager.buildings:
            elements = self.city_generator.element_generator._add_elements_around_building(building)
            for element in elements:
                if self.city_generator.element_manager.can_place_element(element.bounds):
                    self.city_generator.element_manager.add_element(element)
        self.city_generator.element_generator.filter_elements_by_buildings(self.city_generator.building_quadtree)
