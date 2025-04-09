from simworld.utils.vector import Vector

class Sidewalk:
    _id_counter = 0
    def __init__(self, road_id: int, start: Vector, end: Vector):
        self.id = Sidewalk._id_counter
        Sidewalk._id_counter += 1
        self.road_id = road_id
        self.start = start
        self.end = end
        self.pedestrians = []
        self.direction = self.get_direction()

    @classmethod
    def reset_id_counter(cls):
        cls._id_counter = 0

    def get_direction(self):
        return Vector(self.end.x - self.start.x, self.end.y - self.start.y).normalize()

    def __repr__(self):
        return f"Sidewalk(id={self.id}, road_id={self.road_id}, start={self.start}, end={self.end}, direction={self.direction})"

    def add_pedestrian(self, pedestrian):
        self.pedestrians.append(pedestrian)

    def remove_pedestrian(self, pedestrian):
        self.pedestrians.remove(pedestrian)