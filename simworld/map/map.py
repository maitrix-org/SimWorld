"""Map module: defines Road, Node, Edge, and Map graph structures for navigation."""

import json
import os
import random
from collections import defaultdict, deque
from typing import List, Optional

from simworld.config import Config
from simworld.utils.vector import Vector


class Road:
    """Represents a road segment between two points."""

    def __init__(self, start: Vector, end: Vector):
        """Initialize a Road.

        Args:
            start: Starting position vector.
            end: Ending position vector.
        """
        self.start = start
        self.end = end
        self.direction = (end - start).normalize()
        self.length = start.distance(end)
        self.center = (start + end) / 2


class Node:
    """Graph node with a position and type ('normal' or 'intersection')."""

    def __init__(self, position: Vector, type: str = 'normal'):
        """Initialize a Node.

        Args:
            position: Position vector of the node.
            type: Node type; 'normal' or 'intersection'.
        """
        self.position = position
        self.type = type

    def __str__(self) -> str:
        """Return a readable string representation of the node."""
        return f'Node(position={self.position}, type={self.type})'

    def __repr__(self) -> str:
        """Alias for __str__."""
        return self.__str__()

    def __lt__(self, other):
        """For the purpose of calculating shortest path."""
        return self.position.x < other.position.x

    def __eq__(self, other) -> bool:
        """Compare nodes by position."""
        if not isinstance(other, Node):
            return False
        return self.position == other.position

    def __hash__(self) -> int:
        """Hash node by its position."""
        return hash(self.position)


class Edge:
    """Undirected weighted edge between two nodes."""

    def __init__(self, node1: Node, node2: Node):
        """Initialize an Edge.

        Args:
            node1: First endpoint.
            node2: Second endpoint.
        """
        self.node1 = node1
        self.node2 = node2
        self.weight = node1.position.distance(node2.position)

    def __str__(self) -> str:
        """Return a readable string of the edge."""
        return f'Edge(node1={self.node1}, node2={self.node2}, distance={self.weight})'

    def __repr__(self) -> str:
        """Alias for __str__."""
        return self.__str__()

    def __eq__(self, other) -> bool:
        """Edges are equal if they connect the same positions (unordered)."""
        if not isinstance(other, Edge):
            return False
        p1, p2 = self.node1.position, self.node2.position
        q1, q2 = other.node1.position, other.node2.position
        return (p1 == q1 and p2 == q2) or (p1 == q2 and p2 == q1)

    def __hash__(self) -> int:
        """Hash edge by its sorted endpoint positions."""
        if self.node1.position.x < self.node2.position.x or (
            self.node1.position.x == self.node2.position.x and
            self.node1.position.y <= self.node2.position.y
        ):
            pos1, pos2 = self.node1.position, self.node2.position
        else:
            pos1, pos2 = self.node2.position, self.node1.position
        return hash((pos1, pos2))


class Map:
    """Graph of nodes and edges supporting path queries and random access."""

    def __init__(self, config: Config, traffic_signals: list = None):
        """Initialize an empty Map."""
        self.nodes = set()
        self.edges = set()
        self.adjacency_list = defaultdict(list)
        self.config = config
        self.traffic_signals = traffic_signals

    def __str__(self) -> str:
        """Return a summary of nodes and edges."""
        return f'Nodes: {self.nodes}\nEdges: {self.edges}\n'

    def __repr__(self) -> str:
        """Alias for __str__."""
        return self.__str__()

    def initializa_map(self):
        """Initialize the map from the input roads file."""
        roads_file = os.path.join(self.config['map.input_roads'])
        with open(roads_file, 'r') as f:
            roads_data = json.load(f)

        road_items = roads_data.get('roads', [])
        road_objects = []
        for road in road_items:
            start = Vector(road['start']['x'] * 100, road['start']['y'] * 100)
            end = Vector(road['end']['x'] * 100, road['end']['y'] * 100)
            road_objects.append(Road(start, end))

        for road in road_objects:
            normal = Vector(road.direction.y, -road.direction.x)
            offset = self.config['traffic.sidewalk_offset']
            p1 = road.start - normal * offset + road.direction * offset
            p2 = road.end - normal * offset - road.direction * offset
            p3 = road.end + normal * offset - road.direction * offset
            p4 = road.start + normal * offset + road.direction * offset

            nodes = [Node(point, 'intersection') for point in (p1, p2, p3, p4)]
            for node in nodes:
                self.add_node(node)

            self.add_edge(Edge(nodes[0], nodes[1]))
            self.add_edge(Edge(nodes[2], nodes[3]))
            self.add_edge(Edge(nodes[0], nodes[3]))
            self.add_edge(Edge(nodes[1], nodes[2]))

        self.connect_adjacent_roads()

    def add_node(self, node: Node) -> None:
        """Add a node to the map."""
        self.nodes.add(node)

    def add_edge(self, edge: Edge) -> None:
        """Add an edge and update adjacency."""
        self.edges.add(edge)
        self.adjacency_list[edge.node1].append(edge.node2)
        self.adjacency_list[edge.node2].append(edge.node1)

    def get_adjacency_list(self) -> dict:
        """Get the adjacency list mapping each node to its neighbors."""
        return self.adjacency_list

    def get_adjacent_points(self, node: Node) -> List[Vector]:
        """Get neighboring node positions for a given node."""
        return [nbr.position for nbr in self.adjacency_list[node]]

    def get_closest_node(self, position: Vector) -> Node:
        """Find the node nearest to a given position."""
        return min(self.nodes, key=lambda n: n.position.distance(position))

    def has_edge(self, edge: Edge) -> bool:
        """Check if an edge exists in the map."""
        return edge in self.edges

    def get_points(self) -> List[Vector]:
        """Return all node positions."""
        return [node.position for node in self.nodes]

    def get_nodes(self) -> set:
        """Return the set of nodes."""
        return self.nodes

    def get_random_node(self, exclude_pos: Optional[List[Node]] = None) -> Node:
        """Return a random non-intersection node, optionally excluding some."""
        candidates = [n for n in self.nodes if n.type == 'normal']
        if exclude_pos:
            candidates = [n for n in candidates if n not in exclude_pos]
        return random.choice(candidates)

    def get_random_node_with_distance(
        self,
        base_pos: List[Node],
        exclude_pos: Optional[List[Node]] = None,
        min_distance: float = 0,
        max_distance: float = 100000,
    ) -> Node:
        """Return a random non-intersection node within distance bounds from a base."""
        candidates = [n for n in self.nodes if n.type != 'intersection']
        if exclude_pos:
            candidates = [n for n in candidates if n not in exclude_pos]
        while True:
            node = random.choice(candidates)
            base = random.choice(base_pos)
            dist = node.position.distance(base.position)
            if min_distance <= dist <= max_distance:
                return node

    def get_random_node_with_edge_distance(
        self,
        base_pos: List[Node],
        exclude_pos: Optional[List[Node]] = None,
        min_distance: int = 0,
        max_distance: int = 200,
    ) -> Node:
        """Return a random non-intersection node at a given edge-count distance."""
        candidates = [n for n in self.nodes if n.type != 'intersection']
        if exclude_pos:
            candidates = [n for n in candidates if n not in exclude_pos]
        start = random.choice(base_pos)
        target = random.randint(min_distance, max_distance)

        def dfs(node: Node, d: int, visited: set) -> Optional[Node]:
            if d == target and node.type != 'intersection':
                return node
            visited.add(node)
            for nbr in self.adjacency_list[node]:
                if nbr not in visited and nbr.type != 'intersection':
                    found = dfs(nbr, d + 1, visited)
                    if found:
                        return found
            visited.remove(node)
            return None

        result = dfs(start, 0, set())
        if result:
            return result

        # fallback: closest by BFS
        closest = None
        best_diff = float('inf')
        queue = deque([(start, 0)])
        seen = {start}
        while queue:
            node, dist = queue.popleft()
            diff = abs(dist - target)
            if diff < best_diff and node.type != 'intersection':
                best_diff = diff
                closest = node
            for nbr in self.adjacency_list[node]:
                if nbr not in seen and nbr.type != 'intersection':
                    seen.add(nbr)
                    queue.append((nbr, dist + 1))
        if closest:
            return closest
        return random.choice(candidates)

    def get_supply_points(self) -> List[Vector]:
        """Return positions of supply nodes."""
        return [n.position for n in self.nodes if n.type == 'supply']

    def connect_adjacent_roads(self) -> None:
        """Link nodes from nearby roads within a threshold."""
        nodes = list(self.nodes)
        threshold = self.config['traffic.sidewalk_offset'] * 2 + 100
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                n1, n2 = nodes[i], nodes[j]
                if (n1.position.distance(n2.position) < threshold and
                        not self.has_edge(Edge(n1, n2))):
                    self.add_edge(Edge(n1, n2))

    def get_edge_distance_between_two_points(
        self,
        point1: Node,
        point2: Node,
    ) -> int:
        """Return the minimum number of edges between two nodes using BFS."""
        if point1 == point2:
            return 0
        queue = deque([(point1, 0)])
        seen = {point1}
        while queue:
            node, dist = queue.popleft()
            if node == point2:
                return dist
            for nbr in self.adjacency_list[node]:
                if nbr not in seen:
                    seen.add(nbr)
                    queue.append((nbr, dist + 1))
        raise ValueError(f'No path found between {point1} and {point2}')
