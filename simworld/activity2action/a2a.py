"""Activity2Action module: translates high-level plans into simulator actions."""

import heapq
import json
import logging
import math
import re
from typing import List, Optional

import numpy as np

from simworld.activity2action.ActionSpace import FORMAT, Action
from simworld.llm.base_llm import BaseLLM
from simworld.map.map import Map, Node
from simworld.prompt.prompt import SYSTEM_PROMPT, USER_PROMPT
from simworld.utils.vector import Vector


class Activity2Action:
    """Converts a high-level plan into low-level navigation actions."""

    def __init__(
        self,
        user_agent,
        model: BaseLLM,
        vision_model,
        name: str,
        temperature: float = 1.5,
        max_history_step: int = 5,
        camera_id: int = 1,
        dt: float = 0.1,
        observation_viewmode: str = 'lit',
        rule_based: bool = True,
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
        """
        self.name = name
        self.model = model
        self.agent = user_agent
        self.client = user_agent.communicator
        self.system_prompt = SYSTEM_PROMPT.replace('<NAME>', name)
        self.temperature = temperature
        self.max_history_step = max_history_step
        self.action_history = ''  # accumulated action history
        self.camera_id = camera_id
        self.observation_viewmode = observation_viewmode
        self.map: Map = self.client.map
        self.rule_based = rule_based
        self.dt = dt
        self.logger = logging.getLogger(__name__)
        self.update_position_and_direction()

    def parse(self, plan: str) -> None:
        """Parse a plan string and execute the resulting actions."""
        user_prompt = USER_PROMPT.format(
            map=self.map,
            position=self.agent.position,
            plan=plan,
        )

        response = self.model.generate_text_structured(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            format=FORMAT,
            temperature=self.temperature,
        )
        self.logger.info(f'Response: {response}')

        if response is None:
            self.logger.error('Parse failed, response is None')
            return

        data = json.loads(response)
        actions = data['actions']
        waypoints: List[Vector] = []

        for point in data.get('waypoints', []):
            match = re.search(r'Vector\(x=([\-\d.]+), y=([\-\d.]+)\)', point)
            if match:
                x, y = float(match.group(1)), float(match.group(2))
                waypoints.append(Vector(x, y))

        for action, waypoint in zip(actions, waypoints):
            if action == Action.Navigate:
                self.navigate(waypoint)

    def shortest_path(
        self,
        start_pos: Vector,
        end_pos: Vector,
    ) -> List[Vector]:
        """Compute the shortest path between two positions on the map."""
        start_node = self.map.get_closest_node(start_pos)
        end_node = self.map.get_closest_node(end_pos)

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
        self.logger.info(f'Next waypoint: {waypoint}')
        path = self.shortest_path(self.agent.position, waypoint)
        for point in path:
            self.logger.info(f'Waypoint step: {point}')
            if self.rule_based:
                self.navigate_rule_based(point)
            else:
                self.navigate_vision_based()
            self.update_position_and_direction()

    def navigate_rule_based(self, waypoint: Vector) -> None:
        """Rule-based steering and movement toward a waypoint."""
        self.logger.info(
            f'Current pos: {self.agent.position}, target: {waypoint}, dir: {self.agent.direction}'
        )
        while not self.walk_arrive_at_waypoint(waypoint):
            while not self.align_direction(waypoint):
                angle, turn = self.get_angle_and_direction(waypoint)
                self.logger.info(f'Angle: {angle}, turn: {turn}')
                self.unrealcv_client.d_rotate(self.name, angle, turn)
                self.update_position_and_direction()
            self.logger.info(f'Stepping toward: {waypoint}')
            self.unrealcv_client.d_step_forward(self.name)
            self.update_position_and_direction()

    def navigate_vision_based(self) -> None:
        """Placeholder for vision-based navigation logic."""
        pass

    def walk_arrive_at_waypoint(self, waypoint: Vector) -> bool:
        """Return True if agent is within threshold of waypoint."""
        threshold = self.agent.config['user.waypoint_distance_threshold']
        if self.agent.position.distance(waypoint) < threshold:
            self.logger.info(f'Arrived at {waypoint}')
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
        self.logger.info(f'Align angle: {angle}')
        return angle < 5

    def update_position_and_direction(self) -> None:
        """Query simulator for current position and direction."""
        info = self.client.get_informations(self.agent.id)
        pos, direction = info[self.agent.id]
        self.agent.position(pos)
        self.agent.direction(direction)
        self.logger.info(
            f'Agent {self.agent.id} updated pos: {self.agent.position}, dir: {self.agent.direction}'
        )

    def reset(self) -> None:
        """Re-enable controller after episode reset."""
        self.unrealcv_client.enable_controller(self.name, True)
