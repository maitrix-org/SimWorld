import math
from typing import Optional, Tuple

from simworld.citygen.dataclass import Point, Segment


class MathUtils:
    @staticmethod
    def subtract_points(p1: Point, p2: Point) -> Point:
        return Point(p1.x - p2.x, p1.y - p2.y)

    @staticmethod
    def add_points(p1: Point, p2: Point) -> Point:
        return Point(p1.x + p2.x, p1.y + p2.y)

    @staticmethod
    def cross_product(a: Point, b: Point) -> float:
        return a.x * b.y - a.y * b.x

    @staticmethod
    def dot_product(a: Point, b: Point) -> float:
        return a.x * b.x + a.y * b.y

    @staticmethod
    def length(a: Point, b: Point) -> float:
        return math.sqrt((b.x - a.x) ** 2 + (b.y - a.y) ** 2)

    @staticmethod
    def length_v(a: Point) -> float:
        return math.sqrt(a.x * a.x + a.y * a.y)

    @staticmethod
    def angle_between(a: Point, b: Point) -> float:
        dot = MathUtils.dot_product(a, b)
        lengths = MathUtils.length_v(a) * MathUtils.length_v(b)
        if lengths == 0:
            return 0
        angle_rad = math.acos(max(-1.0, min(1.0, dot / lengths)))
        return math.degrees(angle_rad)

    @staticmethod
    def min_degree_difference(val1: float, val2: float) -> float:
        bottom = abs(val1 - val2) % 180
        return min(bottom, abs(bottom - 180))

    @staticmethod
    def do_line_segments_intersect(
        a: Point, b: Point, p: Point, d: Point, buffer: float = 0.001
    ) -> Optional[Tuple[Point, float]]:
        b_rel = MathUtils.subtract_points(b, a)
        d_rel = MathUtils.subtract_points(d, p)

        f = MathUtils.cross_product(MathUtils.subtract_points(p, a), b_rel)
        k = MathUtils.cross_product(b_rel, d_rel)

        if k == 0:
            return None
        f = f / k
        e = MathUtils.cross_product(MathUtils.subtract_points(p, a), d_rel) / k
        
        if buffer < e < (1 - buffer) and buffer < f < (1 - buffer):
            intersection_point = Point(a.x + e * b_rel.x, a.y + e * b_rel.y)
            return intersection_point, e
        return None

    @staticmethod
    def angle_difference(angle1: float, angle2: float) -> float:
        """Calculate the smallest angle difference between two angles"""
        diff = abs(angle1 - angle2) % 360
        return min(diff, 360 - diff)

    @staticmethod
    def point_segment_distance(point: Point, segment: Segment) -> float:
        """Calculate the minimum distance from a point to a line segment"""
        # Vector from start to end of segment

        sx = segment.end.x - segment.start.x
        sy = segment.end.y - segment.start.y

        # Vector from start to point

        px = point.x - segment.start.x
        py = point.y - segment.start.y

        # Length of segment squared

        seg_len_sq = sx * sx + sy * sy

        # If segment has zero length, return distance to start point

        if seg_len_sq == 0:
            return math.sqrt(px * px + py * py)
        # Project point onto segment line
        # t is the normalized projection point (0 = start, 1 = end)

        t = max(0, min(1, (px * sx + py * sy) / seg_len_sq))

        # Calculate closest point on segment

        closest_x = segment.start.x + t * sx
        closest_y = segment.start.y + t * sy

        # Return distance to closest point

        dx = point.x - closest_x
        dy = point.y - closest_y
        return math.sqrt(dx * dx + dy * dy)
    
    @staticmethod
    def rotate_point(center: Point, point: Point, angle: float) -> Point:
        """Rotate a point around a center by a given angle in degrees"""
        rad = math.radians(angle)
        dx, dy = point.x - center.x, point.y - center.y
        rotated_x = center.x + dx * math.cos(rad) - dy * math.sin(rad)
        rotated_y = center.y + dx * math.sin(rad) + dy * math.cos(rad)
        return Point(rotated_x, rotated_y)

    @staticmethod
    def interpolate_point(start: Point, end: Point, t: float) -> Point:
        """Interpolate a point between two points"""
        x = start.x + (end.x - start.x) * t
        y = start.y + (end.y - start.y) * t
        return Point(x, y)

    @staticmethod
    def get_direction_description_for_points(point_a: Point, point_b: Point) -> str:
        """Get the relative direction description for two points"""
        """point_a is the pivot point, point_b is the target point"""
        direction = [
            'East',
            'NorthEast',
            'North',
            'NorthWest',
            'West',
            'SouthWest',
            'South',
            'SouthEast'
        ]

        # Calculate the angle between the two points using atan2
        dx = point_b.x - point_a.x
        dy = point_b.y - point_a.y
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)

        # Normalize the angle to be between 0 and 360
        angle_deg = (angle_deg + 360) % 360

        # Get the index of the direction
        index = int((angle_deg + 22.5) // 45) % 8
        return direction[index]
