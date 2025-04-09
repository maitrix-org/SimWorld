import math
import json
import random
from dataclasses import dataclass, field
from typing import List

@dataclass
class Point:
    x: float
    y: float

    def __hash__(self):
        return hash((self.x, self.y))
    
    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y
        }

@dataclass
class MetaInfo:
    """Metadata for road segments"""
    highway: bool = False  
    t: float = 0.0        

@dataclass
class Segment:
    """A road segment connecting two points"""
    start: Point
    end: Point
    q: MetaInfo = field(default_factory=MetaInfo)  

    def get_angle(self) -> float:
        """Calculate the angle of the segment in degrees"""
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        return math.degrees(math.atan2(dy, dx))
    
    def to_dict(self):
        return {
            'start': self.start.to_dict(),
            'end': self.end.to_dict()
        }

@dataclass
class Intersection:
    point: Point
    segments: List[Segment]

@dataclass
class Route:
    points: List[Point]
    start: Point
    end: Point

    def __hash__(self):
        return hash((self.start, self.end))

@dataclass(frozen=True, eq=True)
class Bounds:
    """
    A bounding box with x, y, width, height, and rotation
    (x, y) is the bottom-left corner of the bounding box
    width: width of the bounding box
    height: height of the bounding box
    """
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0.0

    def __hash__(self):
        return hash((self.x, self.y, self.width, self.height))
    
    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'rotation': self.rotation
        }

# Building types
@dataclass(frozen=True, eq=True)
class BuildingType:
    name: str
    width: float
    height: float
    is_required: bool = False

    def __hash__(self):
        return hash(
            (self.name, self.width, self.height, self.is_required)
        )

    def to_dict(self):
        return {
            'name': self.name,
            'width': self.width,
            'height': self.height,
            'is_required': self.is_required
        }

@dataclass(frozen=True, eq=True)
class Building:
    building_type: BuildingType
    bounds: Bounds
    rotation: float = 0.0  # Building rotation angle (aligned with road)
    center: Point = field(init=False)  # Center point of the building
    width: float = field(init=False)
    height: float = field(init=False)

    def __post_init__(self):
        """Calculate center point after initialization"""
        # Use object.__setattr__ to bypass the frozen restriction
        object.__setattr__(
            self,
            'center',
            Point(
                self.bounds.x + self.bounds.width / 2,
                self.bounds.y + self.bounds.height / 2
            )
        )
        object.__setattr__(self, "width", self.bounds.width)
        object.__setattr__(self, "height", self.bounds.height)
        object.__setattr__(self, "rotation", self.bounds.rotation)

    def __hash__(self):
        """Make Building hashable"""
        return hash(
            (
                self.building_type.name,
                self.bounds.x,
                self.bounds.y,
                self.bounds.width,
                self.bounds.height,
                self.rotation,
            )
        )

    def to_dict(self):
        return {
            'building_type': self.building_type.to_dict(),
            'bounds': self.bounds.to_dict(),
            'rotation': self.rotation,
            'center': self.center.to_dict()
        }

@dataclass(frozen=True, eq=True)
class ElementType:
    name: str
    width: float
    height: float

    def __hash__(self):
        return hash((self.name, self.width, self.height))
    
    def to_dict(self):
        return {
            'name': self.name,
            'width': self.width,
            'height': self.height
        }

@dataclass(frozen=True, eq=True)
class Element:
    """A element is a small object that can be placed in the city"""
    element_type: ElementType
    bounds: Bounds
    rotation: float = 0.0
    center: Point = field(init=False)
    building: Building = None

    def __post_init__(self):
        """Calculate center point after initialization"""
        # Use object.__setattr__ to bypass the frozen restriction
        object.__setattr__(
            self,
            'center',
            Point(
                self.bounds.x + self.bounds.width / 2,
                self.bounds.y + self.bounds.height / 2
            )
        )

    def __hash__(self):
        return hash((self.element_type.name, self.bounds, self.rotation, self.center))

    def to_dict(self):
        return {
            'element_type': self.element_type.to_dict(),
            'bounds': self.bounds.to_dict(),
            'rotation': self.rotation,
            'center': self.center.to_dict()
        }


