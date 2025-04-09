import json
import os
import math
from typing import Dict, List
import random

class DataExporter:
    def __init__(self, city_generator):
        self.city_generator = city_generator

    def export_road_data(self) -> Dict:
        """Export all road data"""
        roads_data = []

        for segment in self.city_generator.road_manager.roads:
            road = {
                "start": {"x": segment.start.x, "y": segment.start.y},
                "end": {"x": segment.end.x, "y": segment.end.y},
                "is_highway": segment.q.highway
            }
            roads_data.append(road)

        return {"roads": roads_data}

    def export_building_data(self) -> Dict:
        """Export all building data"""
        buildings_data = []

        for building in self.city_generator.building_manager.buildings:
            building_data = {
                "center": {"x": building.center.x, "y": building.center.y},
                "rotation": building.rotation,
                "type": building.building_type.name,
                "bounds": {
                    "x": building.bounds.x,
                    "y": building.bounds.y,
                    "width": building.bounds.width,
                    "height": building.bounds.height,
                    "rotation": building.bounds.rotation
                }
            }
            buildings_data.append(building_data)

        return {"buildings": buildings_data}

    def export_element_data(self) -> Dict:
        """Export all element data"""
        elements_data = []

        for element in self.city_generator.element_manager.elements:
            element_data = {
                "center": {"x": element.center.x, "y": element.center.y},
                "rotation": element.rotation,
                "type": element.element_type.name,
                "bounds": {
                    "x": element.bounds.x,
                    "y": element.bounds.y,
                    "width": element.bounds.width,
                    "height": element.bounds.height,
                    "rotation": element.bounds.rotation
                }
            }
            elements_data.append(element_data)
        return {"elements": elements_data}

    def export_routes_data(self) -> Dict:
        """Export all route data"""
        routes_data = []
        for route in self.city_generator.route_manager.routes:
            route_data = {
                "start": {"x": route.start.x, "y": route.start.y},
                "end": {"x": route.end.x, "y": route.end.y},
                "points": [{"x": point.x, "y": point.y} for point in route.points]
            }
            routes_data.append(route_data)

        return {"routes": routes_data}

    def export_to_json(self, output_dir: str):
        """Export all data to JSON files"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        road_data = self.export_road_data()
        with open(f"{output_dir}/roads.json", "w") as f:
            json.dump(road_data, f, indent=2)

        # Export building data
        building_data = self.export_building_data()
        with open(f"{output_dir}/buildings.json", "w") as f:
            json.dump(building_data, f, indent=2)

        # Export element data
        element_data = self.export_element_data()
        with open(f"{output_dir}/elements.json", "w") as f:
            json.dump(element_data, f, indent=2)

        self.convert_layout_to_world(output_dir, building_data, road_data, element_data)

        # Export routes data
        routes_data = self.export_routes_data()
        with open(f"{output_dir}/routes.json", "w") as f:
            json.dump(routes_data, f, indent=2)

    def _calculate_rotation(self, start, end):
        dx = end['x'] - start['x']
        dy = end['y'] - start['y']

        angle = math.atan2(dy, dx)

        degrees = math.degrees(angle)
        if degrees < 0:
            degrees += 360
        return degrees

    def _calculate_center(self, start, end):
        return {
            'x': round((start['x'] + end['x']) / 2, 4),
            'y': round((start['y'] + end['y']) / 2, 4)
        }

    @staticmethod
    def _export_point_label(output_dir: str, data: Dict):
        """data: {'label': label dict, 'point': Point}"""
        with open(f"{output_dir}/point_label.json", "w") as f:
            json.dump(data, f, indent=2)


    def convert_layout_to_world(self, output_dir: str, buildings_data, roads_data, elements_data):
        world_data = {
            "base_map": {
                "name": "map_1",
                "env_bin": "gym_citynav\\Binaries\\Win64\\gym_citynav.exe",
                "width": 1000,
                "height": 1000
            },
            "nodes": []
        }

        for road in roads_data['roads']:
            start = road['start']
            end = road['end']

            center = self._calculate_center(start, end)
            rotation = self._calculate_rotation(start, end)

            scale_x = math.sqrt((end['x'] - start['x']) ** 2 + (end['y'] - start['y']) ** 2) * 100 / 20000
            scale_y = 1.0
            obj = {
                "id": f"GEN_Road_{len(world_data['nodes'])}",
                "instance_name": "BP_Road1_C",
                "properties": {
                    "location": {
                        "x": round(center['x'] * 100, 4),
                        "y": round(center['y'] * 100, 4),
                        "z": 0
                    },
                    "orientation": {
                        "pitch": 0,
                        "yaw": round(rotation, 4),
                        "roll": 0
                    },
                    "scale":{
                        "x": round(scale_x* 0.95, 4),
                        "y": round(scale_y* 0.9, 4),
                        "z": 1.0
                    }
                }
            }
            world_data['nodes'].append(obj)

        for building in buildings_data['buildings']:
            obj = {
                "id": f"GEN_{building['type']}_{len(world_data['nodes'])}",
                "instance_name": f"{building['type']}",
                "properties": {
                    "location": {
                        "x": round(building['center']['x'] * 100, 4),
                        "y": round(building['center']['y'] * 100, 4),
                        "z": 0
                    },
                    "orientation": {
                        "pitch": 0,
                        "yaw": round(building['rotation'], 4),
                        "roll": 0
                    },
                    "scale":{
                        "x": 1.0,
                        "y": 1.0,
                        "z": 1.0
                    }
                }
            }
            world_data['nodes'].append(obj)

        for element in elements_data['elements']:
            num = random.randint(1, 4)
            obj = {
                "id": f"GEN_{element['type'][:-1]}{num}_{len(world_data['nodes'])}",
                "instance_name": f"{element['type']}",
                "properties": {
                    "location": {
                        "x": round(element['center']['x'] * 100, 4),
                        "y": round(element['center']['y'] * 100, 4),
                        "z": 0
                    },
                    "orientation": {
                        "pitch": 0,
                        "yaw": round(element['rotation'], 4),
                        "roll": 0
                    },
                    "scale":{
                        "x": 1.0,
                        "y": 1.0,
                        "z": 1.0
                    }
                }
            }
            world_data['nodes'].append(obj)

        output_file = os.path.join(output_dir, 'progen_world.json')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_file, 'w') as f:
            json.dump(world_data, f, indent=2)