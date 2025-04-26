"""Activity2Action module: translates high-level plans into simulator actions."""

import heapq
import json
import math
import re
from threading import Event
from typing import List, Optional

import numpy as np

from simworld.activity2action.action_space import ACTION_LIST, FORMAT, Action
from simworld.activity2action.prompt import SYSTEM_PROMPT, USER_PROMPT
from simworld.llm.a2a_llm import A2ALLM
from simworld.map.map import Map, Node
from simworld.traffic.base.traffic_signal import TrafficSignalState
from simworld.utils.logger import Logger
from simworld.utils.vector import Vector


class Activity2Action:
    """Converts a high-level plan into low-level navigation actions."""

    def __init__(
        self,
        name: str,
        user_agent,
        model: A2ALLM,
        vision_model: Optional[A2ALLM] = None,
        temperature: float = 1.5,
        max_history_step: int = 5,
        camera_id: int = 1,
        dt: float = 0.1,
        observation_viewmode: str = 'lit',
        rule_based: bool = True,
        exit_event: Event = None,
    ):
        """Initialize the Activity2Action agent.

        Args:
            user_agent: Simulator agent interface.
            model: Language model for instruction parsing.
            vision_model: Vision model for perception.
            name: Agent name for system prompts.
            temperature: Sampling temperature for LLM.
            max_history_step: Max steps of history to retain.
            camera_id: Camera ID for observations.
            dt: Simulation time step.
            observation_viewmode: Rendering mode for observations.
            rule_based: Whether to use rule-based navigation.
            exit_event: Event to signal when the agent should stop.
        """
        self.name = name
        self.model = model
        self.agent = user_agent
        self.client = user_agent.communicator
        self.system_prompt = SYSTEM_PROMPT.replace('<NAME>', name)
        self.temperature = temperature
        self.max_history_step = max_history_step
        self.camera_id = camera_id
        self.observation_viewmode = observation_viewmode
        self.map: Map = self.agent.map
        self.rule_based = rule_based
        self.dt = dt
        self.exit_event = exit_event
        self.logger = Logger.get_logger('Activity2Action')

    def parse(self, plan: str) -> None:
        """Parse a plan string and execute the resulting actions."""
        user_prompt = USER_PROMPT.format(
            map=self.map,
            position=self.agent.position,
            action_list=ACTION_LIST,
            plan=plan,
        )

        response, _ = self.model.generate_text_structured(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            output_format=FORMAT,
            temperature=self.temperature,
        )
        # print(f'Agent {self.agent.id} Response: {response}', flush=True)
        self.logger.info(f'Agent {self.agent.id} Response: {response}')

        if response is None:
            self.logger.error('Parse failed, response is None')
            return
        try:
            data = json.loads(response)
            actions = data['actions']
            waypoints: List[Vector] = []

            for point in data.get('waypoints', []):
                match = re.search(r'Vector\(x=([\-\d.]+), y=([\-\d.]+)\)', point)
                if match:
                    x, y = float(match.group(1)), float(match.group(2))
                    waypoints.append(Vector(x, y))
        except json.JSONDecodeError as e:
            self.logger.error(f'JSON decode error: {e}')
            self.logger.error(f'Failed to parse response: {response}')
            return
        except KeyError as e:
            self.logger.error(f'Missing key in response: {e}')
            self.logger.error(f'Failed to parse response: {response}')
            return
        except Exception as e:
            self.logger.error(f'Unexpected error: {e}')
            self.logger.error(f'Failed to parse response: {response}')
            return
        # print(f'Agent {self.agent.id} Actions: {actions}', flush=True)
        # print(f'Agent {self.agent.id} Waypoints: {waypoints}', flush=True)

        for action, waypoint in zip(actions, waypoints):
            if action == Action.Navigate.value:
                self.navigate(waypoint)

    def shortest_path(
        self,
        start_pos: Vector,
        end_pos: Vector,
    ) -> List[Vector]:
        """Compute the shortest path between two positions on the map."""
        start_node = self.map.get_closest_node(start_pos)
        end_node = self.map.get_closest_node(end_pos)
        if start_node.position == end_node.position:
            return [start_node.position]

        dist: dict[Node, float] = {node: math.inf for node in self.map.nodes}
        prev: dict[Node, Optional[Node]] = {node: None for node in self.map.nodes}
        dist[start_node] = 0.0

        heap: List[tuple[float, Node]] = [(0.0, start_node)]

        while heap:
            current_dist, node = heapq.heappop(heap)
            if node is end_node:
                break
            if current_dist > dist[node]:
                continue

            for neighbor in self.map.adjacency_list[node]:
                weight = node.position.distance(neighbor.position)
                alt = current_dist + weight
                if alt < dist[neighbor]:
                    dist[neighbor] = alt
                    prev[neighbor] = node
                    heapq.heappush(heap, (alt, neighbor))

        if prev[end_node] is None and end_node is not start_node:
            raise ValueError(f'No path found between {start_node} and {end_node}')

        path_nodes: List[Node] = []
        curr = end_node
        while curr:
            path_nodes.append(curr)
            curr = prev[curr]
        path_nodes.reverse()

        return [n.position for n in path_nodes]

    def navigate(self, waypoint: Vector) -> None:
        """Navigate from current position to a given waypoint."""
        self.logger.info(f'Agent {self.agent.id} Target waypoint: {waypoint}')
        # print(f'Agent {self.agent.id} Target waypoint: {waypoint}', flush=True)

        if self.rule_based:
            # Get the shortest path from current position to the target waypoint
            path = self.shortest_path(self.agent.position, waypoint)
            # print(f'Agent {self.agent.id} Shortest Path: {path}', flush=True)
            self.logger.info(f'Agent {self.agent.id} Shortest Path: {path}')
            for point in path:
                self.navigate_rule_based(point)
        else:
            self.navigate_vision_based()

    def navigate_rule_based(self, waypoint: Vector) -> None:
        """Navigate using traffic rules and conditions."""
        if self.map.traffic_signals:
            current_node = self.map.get_closest_node(self.agent.position)
            if current_node.type == 'intersection':
                traffic_light = None
                min_distance = float('inf')
                for signal in self.map.traffic_signals:
                    distance = self.agent.position.distance(signal.position)
                    if distance < min_distance:
                        min_distance = distance
                        traffic_light = signal
                while not self.exit_event.is_set():
                    state = traffic_light.get_state()
                    left_time = traffic_light.get_left_time()
                    if state[1] == TrafficSignalState.PEDESTRIAN_GREEN and left_time > min(15, self.agent.config['traffic.traffic_signal.pedestrian_green_light_duration']):
                        break
        self.navigate_moving(waypoint)

    def navigate_moving(self, waypoint: Vector) -> None:
        """Rule-based steering and movement toward a waypoint."""
        self.logger.info(
            f'Agent {self.agent.id} Current pos: {self.agent.position}, target: {waypoint}, dir: {self.agent.direction}'
        )
        # print(
        #     f'Agent {self.agent.id} Current pos: {self.agent.position}, target: {waypoint}, dir: {self.agent.direction}', flush=True
        # )
        self.client.agent_move_forward(self.agent.id)
        while not self.walk_arrive_at_waypoint(waypoint) and (self.exit_event is None or not self.exit_event.is_set()):
            while not self.align_direction(waypoint) and (self.exit_event is None or not self.exit_event.is_set()):
                angle, turn = self.get_angle_and_direction(waypoint)
                self.client.agent_rotate(self.agent.id, angle, turn)
        self.client.agent_stop(self.agent.id)

    def navigate_vision_based(self) -> None:
        """Placeholder for vision-based navigation logic."""
        pass

    def walk_arrive_at_waypoint(self, waypoint: Vector) -> bool:
        """Return True if agent is within threshold of waypoint."""
        threshold = self.agent.config['user.waypoint_distance_threshold']
        # print(f'Agent {self.agent.id} Walk distance: {self.agent.position.distance(waypoint)}', flush=True)
        if self.agent.position.distance(waypoint) < threshold:
            self.logger.info(f'Agent {self.agent.id} Arrived at {waypoint}')
            # print(f'Agent {self.agent.id} Arrived at {waypoint}', flush=True)
            return True
        return False

    def get_angle_and_direction(
        self,
        waypoint: Vector,
    ) -> tuple[float, Optional[str]]:
        """Compute angle and turn direction to face the waypoint."""
        to_wp = waypoint - self.agent.position
        angle = math.degrees(
            math.acos(np.clip(self.agent.direction.dot(to_wp.normalize()), -1, 1))
        )
        cross = self.agent.direction.cross(to_wp)
        turn_direction = 'left' if cross < 0 else 'right'
        if angle < 2:
            return 0.0, None
        return angle, turn_direction

    def align_direction(self, waypoint: Vector) -> bool:
        """Return True if facing the waypoint within a small angle."""
        to_wp = waypoint - self.agent.position
        angle = math.degrees(
            math.acos(np.clip(self.agent.direction.dot(to_wp.normalize()), -1, 1))
        )
        return angle < 5
