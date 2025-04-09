from simworld.utils.quadtree import QuadTree
from simworld.citygen.dataclass import Element, Bounds
from simworld.utils.bbox_utils import BboxUtils

class ElementManager:
    """Manage elements for the city"""

    def __init__(self, config):
        self.config = config
        self.elements = []
        self.element_quadtree = QuadTree[Element](
            Bounds(self.config['citygen.quadtree.bounds.x'], self.config['citygen.quadtree.bounds.y'], self.config['citygen.quadtree.bounds.width'], self.config['citygen.quadtree.bounds.height']),
            self.config['citygen.quadtree.max_objects'],
            self.config['citygen.quadtree.max_levels']
        )

    def add_element(self, element: Element):
        """Add a element to the quadtree and list"""
        self.elements.append(element)
        self.element_quadtree.insert(element.bounds, element)

    def can_place_element(self, bounds: Bounds, buffer: float = None) -> bool:
        """Check if a element can be placed at the specified location"""
        if buffer is None:
            buffer = self.config['citygen.element.element_element_distance']

        check_bounds = Bounds(
            bounds.x - buffer,
            bounds.y - buffer,
            bounds.width + 2 * buffer,
            bounds.height + 2 * buffer,
            bounds.rotation,
        )

        # Check for collisions with existing items
        candidates = self.element_quadtree.retrieve(check_bounds)

        for item in candidates:
            if BboxUtils.bbox_overlap(item.bounds, check_bounds):
                return False
        return True

    def remove_element(self, element: Element):
        """Remove a element from the quadtree and list"""
        try:
            self.elements.remove(element)
            self.element_quadtree.remove(element.bounds, element)
        except ValueError:
            print(f"Element {element.element_type.name} not found in elements list")