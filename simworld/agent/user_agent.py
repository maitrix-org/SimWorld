import math
import numpy as np
from enum import Enum, auto
from typing import Tuple, List
import logging
from simworld.utils.vector import Vector
from simworld.agent.base_agent import BaseAgent
from simworld.communicator.user_communicator import UserCommunicator
from simworld.activity2action.ActionSpace import ActionSpace
from simworld.activity2action.a2a import Activity2Action
from simworld.config import Config
from simworld.map.map import Map, Node, Edge, Road
from simworld.prompt.prompt import \
    delivery_man_context_prompt, \
    delivery_man_system_prompt, \
    delivery_man_user_prompt, \
    delivery_man_reasoning_user_prompt, \
    delivery_man_context_planner_prompt_llm

class UserAgent(BaseAgent):
    _id_count = 0
    def __init__(self, position: Vector, direction: Vector, map: Map, communicator: UserCommunicator, speed: float = 100, use_a2a: bool = False, use_rule_based: bool = False, config = None):
        super().__init__(position, direction)
        self.communicator = communicator
        self.map = map
        self.a2a = None
        if use_a2a:
            self.a2a = Activity2Action(self, rule_based=use_rule_based)
        
        self.id = UserAgent._id_counter
        UserAgent._id_counter += 1

        self.last_state: Tuple[Vector, str] = (self.position, 'do nothing')
        
        self.waypoints = []
        self.config = config if config else Config()
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        self.speed = speed
        
    def get_possible_next_waypoints(self):
        """
        Get the possible next waypoints from the current position
        Returns: A list of possible next waypoints (List[Vector])
        """
        current_node = None
        min_distance = float('inf')
        for node in self.map.nodes:
            distance = self.agent.position.distance(node.position)
            if distance < min_distance:
                min_distance = distance
                current_node = node
        return self.map.get_adjacent_points(current_node)
        
    def step(self, user_manager):
        while True:
            if self.a2a:
                # parse user prompt and return state
                self.logger.info(f"DeliveryMan {self.id} is deciding what to do")
                possible_next_waypoints = self.get_possible_next_waypoints(user_manager)

                context_prompt = delivery_man_context_prompt.format(position=self.get_self_position_on_map(user_manager), map=self.map, supply_points=user_manager.supply_points, possible_next_waypoints=possible_next_waypoints, speed=self.move_speed, physical_state=self.physical_state, last_position=self.last_state[0], last_action=self.last_state[1])
                response = self.llm.react(system_prompt=delivery_man_system_prompt,
                                        context_prompt=context_prompt,
                                        user_prompt=delivery_man_user_prompt,
                                        reasoning_prompt=delivery_man_reasoning_user_prompt)
                self.a2a.parse(response)
                self.logger.info(f"UserAgent {self.id} at ({self.position})")
