from simworld.citygen.dataclass import Point, Route
from typing import List

class RouteManager:
    def __init__(self):
        self.routes = []

    def add_route_points(self, points: List[Point]):
        start = points[0]
        end = points[-1]
        route = Route(points, start, end)
        print(f"Route: {route}")
        self.routes.append(route)
