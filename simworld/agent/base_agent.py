import math
from simworld.utils.vector import Vector

class BaseAgent:
    def __init__(self, position: Vector, direction: Vector):
        self._position = position
        self._direction = direction
        self._yaw = 0

    @property
    def position(self):
        return self._position

    @property
    def direction(self):
        return self._direction
    
    @property
    def yaw(self):
        return self._yaw
    
    @position.setter
    def position(self, position: Vector):
        self._position = position

    @direction.setter
    def direction(self, yaw: float):
        self._yaw = yaw
        self._direction = Vector(math.cos(math.radians(yaw)), math.sin(math.radians(yaw))).normalize()


