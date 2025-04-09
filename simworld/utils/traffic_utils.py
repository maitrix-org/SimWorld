import numpy as np
from simworld.utils.vector import Vector

def bezier(start: Vector, end: Vector, control_point: Vector, t: float) -> Vector:
    # calculate the x and y coordinates
    return start * (1 - t) ** 2 + control_point * (1 - t) * t * 2 + end * t ** 2


def get_bezier_points(start: Vector, end: Vector, control_point: Vector, num_points: int) -> list[Vector]:
    """
    generate waypoints on the bezier curve
    Args:
        start: start point
        end: end point
        control_point: control point
        num_points: number of points to sample
    Returns:
        waypoints: waypoints on the bezier curve
    """
    t = np.linspace(0, 1, num_points)
    return [bezier(start, end, control_point, t_i) for t_i in t[1:]]


def extend_control_point(start: Vector, end: Vector, intersection: Vector, extension_factor: float = 0.1) -> Vector:
    """
    extend the control point to the intersection
    Args:
        start: start point
        end: end point
        intersection: intersection point
        extension_factor: extension factor, the larger the factor, the smoother the curve
    Returns:
        the extended control point
    """
    # calculate the vector from the intersection to the start and end
    vec_start = start - intersection
    vec_end = end - intersection
    
    # calculate the dot product to determine the angle
    dot_product = vec_start.dot(vec_end)
    

    # determine the direction of extension based on the dot product
    direction = 1 if dot_product > 0 else -1    
    # add the two vectors and normalize, then extend in the opposite direction
    control_vec = intersection + (vec_start + vec_end) * extension_factor * direction

    # extend the control point from the intersection
    return control_vec


def cal_waypoints(start: Vector, end: Vector, gap_between_waypoints: float) -> list[Vector]:
    """
    add waypoints between start and end
    Args:
        start: start point
        end: end point
    Returns:
        the waypoints between start and end(including end)
    """
    distance = start.distance(end)
    num_waypoints = int(distance // gap_between_waypoints)
    waypoints = []
    for i in range(1, num_waypoints + 1):
        fraction = i * gap_between_waypoints / distance
        waypoints.append(start + (end - start) * fraction)
    waypoints.append(end)
    return waypoints
