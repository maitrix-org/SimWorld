from typing import List, Optional, Set

from simworld.config import Config
from simworld.citygen.dataclass import Bounds, Point, Segment
from simworld.utils.math_utils import MathUtils


class RoadUtils:
    @staticmethod
    def find_nearby_endpoint(
        point: Point,
        segments: List[Segment],
        queue_elements: List[Segment],
        merge_distance: float,
    ) -> Optional[Point]:
        """Find existing road endpoint near the given point"""
        closest_point = None
        min_distance = merge_distance

        # Check points in existing segments

        for segment in segments:
            dist_to_start = MathUtils.length(segment.start, point)
            if 0 < dist_to_start < min_distance:
                min_distance = dist_to_start
                closest_point = segment.start
            dist_to_end = MathUtils.length(segment.end, point)
            if 0 < dist_to_end < min_distance:
                min_distance = dist_to_end
                closest_point = segment.end
        # Check points in queue

        for segment in queue_elements:
            dist_to_start = MathUtils.length(segment.start, point)
            if 0 < dist_to_start < min_distance:
                min_distance = dist_to_start
                closest_point = segment.start
            dist_to_end = MathUtils.length(segment.end, point)
            if 0 < dist_to_end < min_distance:
                min_distance = dist_to_end
                closest_point = segment.end
        return closest_point

    @staticmethod
    def create_bounds_for_segment(segment: Segment) -> Bounds:
        """Create bounds object for a segment (used for quadtree)"""
        min_x = min(segment.start.x, segment.end.x) - Config.ROAD_SNAP_DISTANCE
        min_y = min(segment.start.y, segment.end.y) - Config.ROAD_SNAP_DISTANCE
        width = abs(segment.end.x - segment.start.x) + 2 * Config.ROAD_SNAP_DISTANCE
        height = abs(segment.end.y - segment.start.y) + 2 * Config.ROAD_SNAP_DISTANCE
        return Bounds(min_x, min_y, width, height, segment.get_angle())

    @staticmethod
    def get_current_angles(
        segment: Segment,
        segments: List[Segment],
        queue_elements: List[Segment],
        merge_distance: float,
    ) -> List[float]:
        """Get all current angles at the segment end point"""
        angles = []

        # Check all generated segments

        for s in segments:
            if MathUtils.length(s.start, segment.end) < merge_distance:
                angles.append(s.get_angle())
            elif MathUtils.length(s.end, segment.end) < merge_distance:
                angles.append((s.get_angle() + 180) % 360)
        # Check segments in queue

        for s in queue_elements:
            if MathUtils.length(s.start, segment.end) < merge_distance:
                angles.append(s.get_angle())
            elif MathUtils.length(s.end, segment.end) < merge_distance:
                angles.append((s.get_angle() + 180) % 360)
        return angles

    @staticmethod
    def merge_point_if_close(
        segment: Segment,
        point_type: str,
        segments: List[Segment],
        merge_distance: float,
    ) -> bool:
        """
        Merge a segment's endpoint with nearby existing points
        point_type: 'start' or 'end'
        Returns: True if merged, False otherwise
        """
        point = segment.start if point_type == "start" else segment.end

        # Find closest point

        closest_point = None
        min_distance = merge_distance

        for other_segment in segments:
            if other_segment == segment:
                continue
            dist_to_start = MathUtils.length(point, other_segment.start)
            if 0 < dist_to_start < min_distance:
                min_distance = dist_to_start
                closest_point = other_segment.start
            dist_to_end = MathUtils.length(point, other_segment.end)
            if 0 < dist_to_end < min_distance:
                min_distance = dist_to_end
                closest_point = other_segment.end
        if closest_point is not None:
            if point_type == "start":
                segment.start = closest_point
            else:
                segment.end = closest_point
            return True
        return False