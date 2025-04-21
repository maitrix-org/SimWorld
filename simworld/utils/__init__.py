"""Utility modules and helpers for the SimWorld package.

This package contains various utility functions for mathematical operations,
vector manipulation, data export, and other common operations needed
throughout the simulation.
"""

from simworld.utils.extract_json import extract_json_and_fix_escapes
from simworld.utils.math_utils import MathUtils
from simworld.utils.traffic_utils import (bezier, cal_waypoints,
                                          extend_control_point,
                                          get_bezier_points)
from simworld.utils.vector import Vector

__all__ = [
    'Vector',
    'MathUtils',
    'bezier',
    'get_bezier_points',
    'extend_control_point',
    'cal_waypoints',
    'extract_json_and_fix_escapes',
]
