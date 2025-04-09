from dataclasses import dataclass

@dataclass
class Vector:
    x: float
    y: float

    def __post_init__(self):
        self.x = round(self.x, 4)
        self.y = round(self.y, 4)
    
    def normalize(self) -> 'Vector':
        """normalize the vector"""

        magnitude = (self.x ** 2 + self.y ** 2) ** 0.5
        if magnitude == 0:
            return Vector(0, 0)
        return Vector(round(self.x / magnitude, 4), round(self.y / magnitude, 4))
    
    def __add__(self, other: 'Vector') -> 'Vector':
        return Vector(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Vector') -> 'Vector':
        return Vector(self.x - other.x, self.y - other.y)
    
    def __mul__(self, other: float) -> 'Vector':
        return Vector(self.x * other, self.y * other)
    
    def __truediv__(self, other: float) -> 'Vector':
        return Vector(self.x / other, self.y / other)
    
    def distance(self, other: 'Vector') -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    def __eq__(self, other: 'Vector') -> bool:
        # compare two vectors with a tolerance
        return abs(self.x - other.x) < 1e-3 and abs(self.y - other.y) < 1e-3
    
    def __hash__(self) -> int:
        return hash((self.x, self.y))
    
    def dot(self, other: 'Vector') -> float:
        return round(self.x * other.x + self.y * other.y, 4)
    
    def cross(self, other: 'Vector') -> float:
        return round(self.x * other.y - self.y * other.x, 4)


    def length(self) -> float:
        return round(((self.x ** 2 + self.y ** 2) ** 0.5), 4)
