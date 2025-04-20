"""Map module: defines Road, Node, Edge, and Map graph structures for navigation."""

import json
import os
import sys
from collections import defaultdict
from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtWidgets import QApplication, QWidget

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
        self.initialize_map()

    def __str__(self) -> str:
        """Return a summary of nodes and edges."""
        return f'Nodes: {self.nodes}\nEdges: {self.edges}\n'

    def __repr__(self) -> str:
        """Alias for __str__."""
        return self.__str__()

    def initialize_map(self):
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

    def visualize_map(self) -> None:
        """Visualize the map using Qt with actual coordinates."""
        class MapViewer(QWidget):
            def __init__(self, nodes, edges):
                super().__init__()
                self.nodes = nodes
                self.edges = edges

                self.min_x = min(node.position.x for node in nodes)
                self.min_y = min(node.position.y for node in nodes)
                self.max_x = max(node.position.x for node in nodes)
                self.max_y = max(node.position.y for node in nodes)
                self.setMinimumSize(800, 800)
                self.setWindowTitle('SimWorld Map Visualization')

            def paintEvent(self, event):
                painter = QPainter(self)
                painter.setRenderHint(QPainter.Antialiasing)

                width = self.width()
                height = self.height()
                margin = 50
                scale_x = (width - 2 * margin) / (self.max_x - self.min_x)
                scale_y = (height - 2 * margin) / (self.max_y - self.min_y)
                scale = min(scale_x, scale_y)

                painter.setPen(QPen(Qt.black, 2))
                for edge in self.edges:
                    x1 = margin + (edge.node1.position.x - self.min_x) * scale
                    y1 = margin + (edge.node1.position.y - self.min_y) * scale
                    x2 = margin + (edge.node2.position.x - self.min_x) * scale
                    y2 = margin + (edge.node2.position.y - self.min_y) * scale
                    painter.drawLine(int(x1), int(y1), int(x2), int(y2))

                painter.setPen(QPen(Qt.red, 4))
                for node in self.nodes:
                    x = margin + (node.position.x - self.min_x) * scale
                    y = margin + (node.position.y - self.min_y) * scale
                    painter.drawPoint(int(x), int(y))

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        viewer = MapViewer(self.nodes, self.edges)
        viewer.show()
        app.exec_()
