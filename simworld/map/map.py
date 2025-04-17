import random
from collections import defaultdict
from typing import Optional, List
from utils.Types import Vector
from Config import Config
from collections import deque

class Road:
    def __init__(self, start: Vector, end: Vector):
        self.start = start
        self.end = end
        self.direction = (end - start).normalize()
        self.length = start.distance(end)
        self.center = (start + end) / 2

class Node:
    def __init__(self, position: Vector, type: str = "normal"):
        self.position = position
        self.type = type   # "normal" or "intersection"

    def __str__(self):
        return f"Node(position={self.position}, type={self.type})"

    def __repr__(self):
        return f"Node(position={self.position}, type={self.type})"

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.position == other.position

    def __hash__(self):
        return hash(self.position)

class Edge:
    def __init__(self, node1: Node, node2: Node):
        self.node1 = node1
        self.node2 = node2
        self.weight = node1.position.distance(node2.position)

    def __str__(self):
        return f"Edge(node1={self.node1}, node2={self.node2}, distance={self.weight})"

    def __repr__(self):
        return f"Edge(node1={self.node1}, node2={self.node2}, distance={self.weight})"

    def __eq__(self, other):
        if not isinstance(other, Edge):
            return False
        return ((self.node1.position == other.node1.position and
                self.node2.position == other.node2.position) or
                (self.node1.position == other.node2.position and
                self.node2.position == other.node1.position))

    def __hash__(self):
        if self.node1.position.x < self.node2.position.x or \
            (self.node1.position.x == self.node2.position.x and
            self.node1.position.y <= self.node2.position.y):
            pos1, pos2 = self.node1.position, self.node2.position
        else:
            pos1, pos2 = self.node2.position, self.node1.position
        return hash((pos1, pos2))

class Map:
    def __init__(self):
        self.nodes = set()
        self.edges = set()
        self.adjacency_list = defaultdict(list)

    def __str__(self):
        return f"Nodes: {self.nodes}\nEdges: {self.edges}\n"

    def __repr__(self):
        return self.__str__()

    def add_node(self, node: Node):
        self.nodes.add(node)

    def add_edge(self, edge: Edge):
        self.edges.add(edge)
        self.adjacency_list[edge.node1].append(edge.node2)
        self.adjacency_list[edge.node2].append(edge.node1)

    def get_adjacency_list(self):
        return self.adjacency_list

    def get_adjacent_points(self, node: Node):
        points = [n.position for n in self.adjacency_list[node]]
        return points

    def has_edge(self, edge: Edge):
        return edge in self.edges

    def get_points(self):
        return [node.position for node in self.nodes]

    def get_nodes(self):
        return self.nodes

    def get_random_node(self, exclude_pos: Optional[List[Node]] = None):
        # get a random node that is not an intersection
        nodes = [node for node in self.nodes if node.type == "normal"]
        # nodes = list(self.nodes)
        if exclude_pos:
            nodes = [node for node in nodes if node not in exclude_pos]
        return random.choice(nodes)

    def get_random_node_with_distance(self, base_pos: List[Node], exclude_pos: Optional[List[Node]] = None, min_distance: float = 0, max_distance: float = 100000):
        # get a random node that is not an intersection and is at least min_distance away from any nodes in exclude_pos
        nodes = [node for node in self.nodes if node.type != "intersection"]
        if exclude_pos:
            nodes = [node for node in nodes if node not in exclude_pos]
        # get a random node that is at least min_distance away from any nodes in exclude_pos
        while True:
            node = random.choice(nodes)
            base_node = random.choice(base_pos)
            if node.position.distance(base_node.position) >= min_distance and node.position.distance(base_node.position) <= max_distance:
                return node

    def get_random_node_with_edge_distance(self, base_pos: List[Node], exclude_pos: Optional[List[Node]] = None, min_distance: float = 0, max_distance: float = 200):
        # get a random node that is at least min_distance away from any nodes in exclude_pos
        nodes = [node for node in self.nodes if node.type != "intersection"]
        if exclude_pos:
            nodes = [node for node in nodes if node not in exclude_pos]
        base_node = random.choice(base_pos)
        target_distance = random.choice(range(min_distance, max_distance))

        # dfs with correct distance tracking
        def dfs(node, current_distance, visited):
            if current_distance == target_distance and node.type != "intersection":
                return node
            visited.add(node)
            for neighbor in self.adjacency_list[node]:
                if neighbor not in visited and neighbor.type != "intersection":
                    result = dfs(neighbor, current_distance + 1, visited)
                    if result is not None:
                        return result
            visited.remove(node)  # backtrack
            return None

        visited = set()
        result = dfs(base_node, 0, visited)
        # 如果找不到符合条件的节点，返回一个随机节点
        if result is None:
            # 尝试找到一个距离目标距离最近的节点
            closest_node = None
            min_diff = float('inf')
            # 使用BFS找到所有可达节点
            queue = deque([(base_node, 0)])
            all_visited = {base_node}
            while queue:
                current_node, distance = queue.popleft()
                diff = abs(distance - target_distance)

                if diff < min_diff and current_node.type != "intersection":
                    min_diff = diff
                    closest_node = current_node

                for neighbor in self.adjacency_list[current_node]:
                    if neighbor not in all_visited and neighbor.type != "intersection":
                        all_visited.add(neighbor)
                        queue.append((neighbor, distance + 1))

            # 如果找到了最近的节点，返回它
            if closest_node is not None:
                return closest_node

            # 如果仍然没有找到节点，返回一个随机节点
            if nodes:
                return random.choice(nodes)
            else:
                # 如果nodes为空，返回base_node
                return base_node

        return result

    def get_supply_points(self):
        return [node.position for node in self.nodes if node.type == "supply"]

    def connect_adjacent_roads(self):
        """
        Connect nodes from adjacent roads that are close to each other
        """
        nodes = list(self.nodes)
        connection_threshold = Config.SIDEWALK_OFFSET * 2 + 100   # Reasonable threshold for connecting nearby nodes


        for i in range(len(nodes)):
            for j in range(i+1, len(nodes)):
                node1 = nodes[i]
                node2 = nodes[j]

                # If nodes are close enough and not already connected
                if (node1.position.distance(node2.position) < connection_threshold and
                    not self.has_edge(Edge(node1, node2))):
                    self.add_edge(Edge(node1, node2))

    def interpolate_nodes(self):
        """
        Interpolate nodes between existing nodes to create a smoother map
        """
        current_edges = list(self.edges)

        for edge in current_edges:
            distance = edge.weight
            num_points = int(distance / (2 * Config.SIDEWALK_OFFSET))

            if num_points <= 1:
                continue

            direction = (edge.node2.position - edge.node1.position).normalize()

            new_nodes = []
            
            supply_point_index = random.randint(2, num_points - 2) if num_points > 1 else None

            for i in range(1, num_points + 1):
                new_point = edge.node1.position + direction * (i * 2 * Config.SIDEWALK_OFFSET)
                node_type = "supply" if i == supply_point_index else "normal"
                new_node = Node(new_point, type=node_type)
                self.add_node(new_node)
                new_nodes.append(new_node)

            self.edges.remove(edge)
            self.adjacency_list[edge.node1].remove(edge.node2)
            self.adjacency_list[edge.node2].remove(edge.node1)

            all_nodes = [edge.node1] + new_nodes + [edge.node2]
            for i in range(len(all_nodes) - 1):
                self.add_edge(Edge(all_nodes[i], all_nodes[i + 1]))

    def get_edge_distance_between_two_points(self, point1: Node, point2: Node) -> int:
        """Calculate the minimum edge distance between two points using BFS.
        Args:
            point1: Starting node
            point2: Target node

        Returns:
            The minimum number of edges between the two points
        """
        if point1 == point2:
            return 0

        queue = deque([(point1, 0)])  # (node, distance) pairs
        visited = {point1}

        while queue:
            current_point, distance = queue.popleft()

            # Check if we've reached the target
            if current_point == point2:
                return distance

            # Explore neighbors
            for neighbor in self.adjacency_list[current_point]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, distance + 1))

        # If we get here, no path was found
        raise ValueError(f"No path found between {point1} and {point2}")