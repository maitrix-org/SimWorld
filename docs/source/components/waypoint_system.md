# Waypoint System

## Overview
```{image} ../assets/waypoint_system.png
:width: 800px
:align: center
:alt: Waypoint System Overview
```

To enable robust agent navigation and path planning within the simulated environment, SimWorld incorporates a customizable waypoint system that serves as the foundational representation of navigable space. This system is initially constructed using a coarse-grained waypoint skeleton derived from the output of the **Layout Generation** pipeline. Specifically, the pipeline generates high-level geometric features of the environment, such as road centerlines and intersection points, which are then used to define the topological structure of the navigation graph.

## Map
The **Waypoint System** is implemented as a `Map` class, where each waypoint is represented by a `Node` and each connection between waypoints is represented by an `Edge`.
```python
class Node:
    def __init__(self, position: Vector, direction: Vector, type: str = 'sidewalk'):
        """Initialize a Node.

        Args:
            position: Position vector of the node.
            direction: Direction vector of the node.
            type: Node type; 'sidewalk', 'crosswalk', or 'intersection'.
        """
        self.position = position
        self.direction = direction
        self.type = type

class Edge:
    def __init__(self, node1: Node, node2: Node):
        """Initialize an Edge.

        Args:
            node1: First endpoint.
            node2: Second endpoint.
        """
        self.node1 = node1
        self.node2 = node2
        self.weight = node1.position.distance(node2.position)

class Map:
    def __init__(self, config: Config, traffic_signals: list = None):
        """Initialize an empty Map.

        Args:
            config: Configuration object containing map parameters.
            traffic_signals: Optional list of traffic signals in the environment. Used when an agent needs to follow the traffic rules.
        """
        self.nodes = set()
        self.edges = set()
        self.adjacency_list = defaultdict(list)
        self.config = config
        self.traffic_signals = traffic_signals
```

## Granularity
The granularity of the waypoint system is customizable. Users can specify the number of waypoints and the distance between them.

To initialize a map:
```python
map = Map(config)
map.initialize_map_from_file(roads_file, sidewalk_offset, fine_grained, num_waypoints_normal, waypoints_distance, waypoints_normal_distance)
```
+ `roads_file`: File generated from the Layout Generation pipeline.
+ `sidewalk_offset`: Distance between the road centerline and sidewalk centerline.
+ `fine_grained`: Whether to enable interpolation to build a fine-grained map.
+ `num_waypoints_normal`: Number of waypoints in the normal direction of the sidewalk.
+ `waypoints_distance`: Distance between waypoints along the sidewalk.
+ `waypoints_normal_distance`: Number of waypoints in the normal direction.

In a coarse-grained map, all nodes are labeled as `intersection`. In a fine-grained map, `sidewalk` and `crosswalk` nodes are interpolated between `intersection` nodes. Below is an example of coarse-grained and fine-grained maps.

```{image} ../assets/waypoint_example.png
:width: 800px
:align: center
:alt: Waypoint System Example
```
