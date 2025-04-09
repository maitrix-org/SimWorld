from simworld.utils.vector import Vector

class Crosswalk:
    _id_counter = 0
    def __init__(self, start: Vector, end: Vector, road_id: int):
        self.id = Crosswalk._id_counter
        Crosswalk._id_counter += 1
        self.start = start
        self.end = end

        self.road_id = road_id
        self.sidewalks = []

    @classmethod
    def reset_id_counter(cls):
        cls._id_counter = 0


    def __repr__(self):
        return f"Crosswalk(id={self.id}, start={self.start}, end={self.end}, road_id={self.road_id})"





