from simworld.utils.vector import Vector
from simworld.traffic.base.traffic_lane import TrafficLane
from simworld.traffic.base.sidewalk import Sidewalk
from simworld.traffic.base.crosswalk import Crosswalk

class Road:
    _id_counter = 0
    def __init__(self, start: Vector, end: Vector, num_lanes: int, lane_offset: float, intersection_offset: float, sidewalk_offset: float, crosswalk_offset: float):
        self.id = Road._id_counter
        Road._id_counter += 1
        self.start = start
        self.end = end
        self.num_lanes = num_lanes
        self.lane_offset = lane_offset
        self.sidewalk_offset = sidewalk_offset
        self.intersection_offset = intersection_offset
        self.crosswalk_offset = crosswalk_offset
        self.direction = self.get_direction()
        self.center = self.get_center()


        # {‘forward1’: Lane, ‘backward1’: Lane, ‘forward2’: Lane, ‘backward2’: Lane, ...}
        # forward and backward is relative to the road direction
        self.lanes = {}    

        # {‘forward’: Sidewalk, ‘backward’: Sidewalk}
        # forward and backward is relative to the road direction
        self.sidewalks = {}

        # There should be two crosswalks for each road
        self.crosswalks = []

    @classmethod
    def reset_id_counter(cls):
        cls._id_counter = 0


    def __repr__(self):
        return f"Road(id={self.id}, start={self.start}, end={self.end}, center={self.center}, direction={self.direction})"

    def get_direction(self):
        return Vector(self.end.x - self.start.x, self.end.y - self.start.y).normalize()

    def get_center(self):
        return Vector((self.start.x + self.end.x) / 2, (self.start.y + self.end.y) / 2)
    
    def init_road(self):
        self.add_lanes()
        self.add_sidewalks()
        self.add_crosswalks()

    def add_lanes(self):
        normal_vector = Vector(self.direction.y, -self.direction.x)

        for i in range(self.num_lanes):
            lane_start = self.start - normal_vector * (self.lane_offset * (i + 1)) + self.direction * self.intersection_offset
            lane_end = self.end - normal_vector * (self.lane_offset * (i + 1)) - self.direction * self.intersection_offset
            self.lanes['forward' + str(i+1)] = TrafficLane(self.id, lane_start, lane_end)
            lane_start = self.end + normal_vector * (self.lane_offset * (i + 1)) - self.direction * self.intersection_offset
            lane_end = self.start + normal_vector * (self.lane_offset * (i + 1)) + self.direction * self.intersection_offset
            self.lanes['backward' + str(i+1)] = TrafficLane(self.id, lane_start, lane_end)
        

    def add_sidewalks(self):
        normal_vector = Vector(self.direction.y, -self.direction.x)
        sidewalk_start = self.start - normal_vector * (self.sidewalk_offset) + self.direction * self.crosswalk_offset
        sidewalk_end = self.end - normal_vector * (self.sidewalk_offset) - self.direction * self.crosswalk_offset
        self.sidewalks['forward'] = Sidewalk(self.id, sidewalk_start, sidewalk_end)

        sidewalk_start = self.end + normal_vector * (self.sidewalk_offset) - self.direction * self.crosswalk_offset
        sidewalk_end = self.start + normal_vector * (self.sidewalk_offset) + self.direction * self.crosswalk_offset
        self.sidewalks['backward'] = Sidewalk(self.id, sidewalk_start, sidewalk_end)


    def add_crosswalks(self):
        crosswalk_start = self.sidewalks['forward'].end
        crosswalk_end = self.sidewalks['backward'].start
        self.crosswalks.append(Crosswalk(crosswalk_start, crosswalk_end, self.id))

        crosswalk_start = self.sidewalks['backward'].end
        crosswalk_end = self.sidewalks['forward'].start
        self.crosswalks.append(Crosswalk(crosswalk_start, crosswalk_end, self.id))




