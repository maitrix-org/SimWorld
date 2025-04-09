from simworld.utils.vector import Vector


class TrafficLane:
    _id_counter = 0
    def __init__(self, road_id: int, start: Vector, end: Vector):
        self.id = TrafficLane._id_counter
        TrafficLane._id_counter += 1
        self.road_id = road_id
        self.start = start
        self.end = end
        self.vehicles = []
        self.direction = self.get_direction()

    @classmethod
    def reset_id_counter(cls):
        cls._id_counter = 0

    def get_direction(self):
        return Vector(self.end.x - self.start.x, self.end.y - self.start.y).normalize()

    def __repr__(self):
        return f"Lane(id={self.id}, road_id={self.road_id}, start={self.start}, end={self.end}, direction={self.direction})"

    def add_vehicle(self, vehicle):
        self.vehicles.append(vehicle)

    def remove_vehicle(self, vehicle):
        self.vehicles.remove(vehicle)


