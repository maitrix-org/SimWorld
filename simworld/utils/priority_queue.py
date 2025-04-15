from typing import List, Optional

from simworld.citygen.dataclass import Segment


class PriorityQueue:
    def __init__(self):
        self.elements: List[Segment] = []

    def enqueue(self, segment: Segment):
        """Add a segment to the queue"""
        self.elements.append(segment)

    def dequeue(self) -> Optional[Segment]:
        """Get segment with minimum t value"""
        if not self.elements:
            return None
        min_t = float('inf')
        min_idx = 0

        for i, segment in enumerate(self.elements):
            if segment.q.t < min_t:
                min_t = segment.q.t
                min_idx = i
        return self.elements.pop(min_idx)

    def empty(self) -> bool:
        """Check if queue is empty"""
        return len(self.elements) == 0

    def __iter__(self):
        """Make queue iterable"""
        return iter(self.elements)

    def __len__(self):
        """Get queue length"""
        return len(self.elements)

    @property
    def size(self):
        return len(self.elements)
