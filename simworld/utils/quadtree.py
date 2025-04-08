from typing import Generic, List, Optional, TypeVar

from simworld.citygen.dataclass import Bounds

T = TypeVar("T")

class QuadTree(Generic[T]):
    def __init__(self, bounds: Bounds, max_objects=10, max_levels=4, level=0):
        self.bounds = bounds
        self.max_objects = max_objects
        self.max_levels = max_levels
        self.level = level
        self.objects: List[Bounds] = []
        self.items: List[T] = []
        self.nodes: List[Optional[QuadTree]] = [None] * 4

    def split(self):
        width = self.bounds.width / 2
        height = self.bounds.height / 2
        x = self.bounds.x
        y = self.bounds.y

        self.nodes[0] = QuadTree(
            Bounds(x + width, y, width, height),
            self.max_objects,
            self.max_levels,
            self.level + 1,
        )
        self.nodes[1] = QuadTree(
            Bounds(x, y, width, height),
            self.max_objects,
            self.max_levels,
            self.level + 1,
        )
        self.nodes[2] = QuadTree(
            Bounds(x, y + height, width, height),
            self.max_objects,
            self.max_levels,
            self.level + 1,
        )
        self.nodes[3] = QuadTree(
            Bounds(x + width, y + height, width, height),
            self.max_objects,
            self.max_levels,
            self.level + 1,
        )

        for i, rect in enumerate(self.objects):
            for node in self.get_relevant_nodes(rect):
                node.insert(rect, self.items[i])

    def get_relevant_nodes(self, rect: Bounds) -> List["QuadTree[T]"]:
        nodes = []
        mid_x = self.bounds.x + self.bounds.width / 2
        mid_y = self.bounds.y + self.bounds.height / 2

        top = rect.y <= mid_y
        bottom = rect.y + rect.height > mid_y

        if rect.x <= mid_x:
            if top:
                nodes.append(self.nodes[1])
            if bottom:
                nodes.append(self.nodes[2])
        if rect.x + rect.width > mid_x:
            if top:
                nodes.append(self.nodes[0])
            if bottom:
                nodes.append(self.nodes[3])
        return [n for n in nodes if n is not None]

    def insert(self, rect: Bounds, item: T):
        if any(self.nodes):
            for node in self.get_relevant_nodes(rect):
                node.insert(rect, item)
            return
        self.objects.append(rect)
        self.items.append(item)

        if len(self.objects) > self.max_objects and self.level < self.max_levels:
            if not any(self.nodes):
                self.split()

    def retrieve(self, rect: Bounds) -> List[T]:
        result = []
        if any(self.nodes):
            for node in self.get_relevant_nodes(rect):
                result.extend(node.retrieve(rect))
        else:
            result = self.items
        return result

    def clear(self):
        self.objects = []
        self.items = []
        self.nodes = [None] * 4

    def remove(self, bounds: Bounds, item: T) -> bool:
        """Remove an item and its bounds from the quadtree
        Returns True if item was found and removed, False otherwise
        """
        # Check if item exists in current node
        if item in self.items:
            index = self.items.index(item)
            self.items.pop(index)
            self.objects.pop(index)

            # Recursively remove from child nodes if they exist
            if any(self.nodes):
                for node in self.get_relevant_nodes(bounds):
                    node.remove(bounds, item)
            return True

        # If not in current node but has children, try removing from relevant child nodes
        elif any(self.nodes):
            for node in self.get_relevant_nodes(bounds):
                if node.remove(bounds, item):
                    return True

        return False