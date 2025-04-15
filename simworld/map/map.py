
class Node:
    def __init__(self, position):
        self.position = position

class Edge:
    def __init__(self, node1, node2, distance):
        self.node1 = node1
        self.node2 = node2
        self.distance = distance

class Map:
    def __init__(self):
        self.nodes = set()
        self.edges = set()
        self.adjacency_list = {}

    def add_node(self, node):
        self.nodes.add(node)
        self.adjacency_list[node] = []

    def add_edge(self, edge):
        self.edges.add(edge)
        self.adjacency_list[edge.node1].append(edge.node2)
        self.adjacency_list[edge.node2].append(edge.node1)


