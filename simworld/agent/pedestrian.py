import math
import numpy as np
from enum import Enum, auto
from simworld.utils.vector import Vector
from simworld.agent.base_agent import BaseAgent

class PedestrianState(Enum):
    STOP = auto()
    MOVE_FORWARD = auto()
    TURN_AROUND = auto()


class Pedestrian(BaseAgent):
    _id_counter = 0
    def __init__(self, position: Vector, direction: Vector, current_sidewalk, speed: float = 100):
        super().__init__(position, direction)
        self.id = Pedestrian._id_counter
        Pedestrian._id_counter += 1

        self.current_sidewalk = current_sidewalk
        self.waypoints = []
        self.state = PedestrianState.STOP

        self.speed = speed

    @classmethod
    def reset_id_counter(cls):
        cls._id_counter = 0

    def __str__(self):
        return f"Pedestrian(id={self.id}, position={self.position}, direction={self.direction})"

    def __repr__(self):
        return f"Pedestrian(id={self.id}, current_sidewalk={self.current_sidewalk.id}, position={self.position}, direction={self.direction}, waypoints={self.waypoints})"

    def change_to_next_sidewalk(self, next_sidewalk):
        self.current_sidewalk.pedestrians.remove(self)
        self.current_sidewalk = next_sidewalk
        self.current_sidewalk.pedestrians.append(self)

    def add_waypoint(self, waypoints: list[Vector]):
        self.waypoints.extend(waypoints)

    def pop_waypoint(self):
        return self.waypoints.pop(0)
    
    def is_close_to_end(self, waypoint_distance_threshold: float):
        '''Check if the pedestrian is close to the end of the sidewalk'''
        if len(self.waypoints) == 0:
            return False
        return self.position.distance(self.waypoints[-1]) < waypoint_distance_threshold
    
    def complete_turn(self):
        if self.state == PedestrianState.TURN_AROUND and len(self.waypoints) > 0:
            to_waypoint = self.waypoints[0] - self.position
            angle = math.degrees(math.acos(np.clip(self.direction.dot(to_waypoint.normalize()), -1, 1)))
            # complete turn if agent is facing the waypoint or the angle has passed the point
            return angle < 2 or angle >= 90
        return False

    def compute_control(self, waypoint: Vector):
        to_waypoint = waypoint - self.position
        
        angle = math.degrees(math.acos(np.clip(self.direction.dot(to_waypoint.normalize()), -1, 1)))
        
        cross_product = self.direction.cross(to_waypoint)
        turn_direction = 'left' if cross_product < 0 else 'right'

        if angle < 2:
            return 0, None
        else:
            return angle, turn_direction