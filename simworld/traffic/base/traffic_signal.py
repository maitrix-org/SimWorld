from enum import Enum
from simworld.utils.vector import Vector


class TrafficSignalState(Enum):
    VEHICLE_RED = "vehicle_red"
    VEHICLE_GREEN = "vehicle_green"
    PEDESTRIAN_RED = "pedestrian_red"
    PEDESTRIAN_GREEN = "pedestrian_green"


class TrafficSignal:
    _id_counter = 0

    def __init__(self, position: Vector, direction: Vector, lane_id: int, crosswalk_id: int, type: str):
        self.id = TrafficSignal._id_counter
        TrafficSignal._id_counter += 1
        self.lane_id = lane_id
        self.crosswalk_id = crosswalk_id
        self.state = (TrafficSignalState.VEHICLE_RED, TrafficSignalState.PEDESTRIAN_RED)

        self.type = type
        assert self.type in ["both", "pedestrian"], "Invalid traffic light type"

        self.position = position
        self.direction = direction

        self.left_time = 0

    @classmethod
    def reset_id_counter(cls):
        cls._id_counter = 0

    def __repr__(self):
        return f"TrafficSignal(id={self.id}, lane_id={self.lane_id}, crosswalk_id={self.crosswalk_id}, position={self.position}, direction={self.direction}, state={self.state})"

    def set_state(self, state):
        if isinstance(state, tuple) and len(state) == 2:
            self.state = state
        else:
            raise ValueError(f"Invalid state: {state}. Must be a TrafficLightState enum value")

    def get_state(self):
        return self.state
    
    def set_left_time(self, left_time):
        self.left_time = left_time

    def get_left_time(self):
        return self.left_time
