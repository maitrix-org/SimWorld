

# class Activity2Action:
#     def __init__(self, llm, vlm, agent, is_rule_based: bool = False):
#         pass

#     def generate_action(self, instruction: str) -> str:
#         return 

from typing import List
import numpy as np
# from llm_reasoners.reasoners.base import LanguageModel
from PIL import Image
import openai
import io
import json
import random
from .base import ActionQueue, Action
from llm.openai import UEOpenAI
from simworld.utils.vector import Vector
from simworld.activity2action.ActionSpace import ActionSpace
from simworld.config import Config
import logging
import math
import time

from simworld.map.map import Map, Node, Edge, Road
from simworld.prompt.prompt import SYSTEM_PROMPT, USER_PROMPT

class Activity2Action:
    def __init__(self,
                user_agent,
                model: UEOpenAI,
                vision_model, # in case we need to support huggingface model
                name: str,
                temperature=1.5,
                max_history_step=5,
                camera_id=1,
                dt=0.1,
                observation_viewmode='lit',
                rule_based=True,
                ):
        self.name = name
        self.model = model
        self.agent = user_agent
        self.client = user_agent.communicator
        self.system_prompt = SYSTEM_PROMPT.replace("<NAME>", name)
        self.temperature = temperature
        self.max_history_step = max_history_step
        self.action_history = ""
        self.camera_id = camera_id
        self.observation_viewmode = observation_viewmode
        self.map = self.client.map
        self.rule_based = rule_based
        self.dt = dt
        self.logger = logging.getLogger(__name__)
        self.update_position_and_direction()

    def parse(self, plan):
        user_prompt = USER_PROMPT.format(map=self.map, position=self.agent.position, plan=plan) # here pass the plan into the prompt
        
        response = self.model.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            # action_history=self.action_history,
            temperature=self.temperature
        )
        print(f"Response: {response}")
        response_obj = ActionSpace.from_json(response)

        actions = response_obj.actions
        wayoints = [Vector(waypoint.x, waypoint.y) for waypoint in response_obj.waypoints]

        for action, w in zip(actions, wayoints):
            if action == Action.Navigate:
                self.navigate(w)
        
        # return self.agent.position
        
    def navigate(self, waypoint: Vector):
        """Navigate to the waypoint"""
        print(f"Next waypoint: {waypoint}")
        if self.rule_based:
            self.navigate_rule_based(waypoint)
        else:
            self.navigate_vision_based()
        self.update_position_and_direction()
        
    def navigate_rule_based(self, waypoint: Vector):
        self.logger.info(f"Current position: {self.agent.position}, Next waypoint: {waypoint}, Direction: {self.agent.direction}")
        while not self.walk_arrive_at_waypoint(waypoint):
            while not self.align_direction(waypoint):
                angle, turn_direction = self.get_angle_and_direction(waypoint)
                self.logger.info(f"Angle: {angle}, Turn direction: {turn_direction}")
                self.unrealcv_client.d_rotate(self.name, angle, turn_direction)
                self.update_position_and_direction()
            self.logger.info(f"Walking to waypoint: {waypoint}")
            self.unrealcv_client.d_step_forward(self.name)
            self.update_position_and_direction()
            
    def navigate_vision_based(self):
        pass

    def walk_arrive_at_waypoint(self, waypoint: Vector):
        if self.agent.position.distance(waypoint) < self.agent.config['user.waypoint_distance_threshold']:
            self.logger.info(f"Arrived at waypoint: {waypoint}")
            return True
        return False
    
    def get_angle_and_direction(self, waypoint: Vector):
        to_waypoint = waypoint - self.agent.position

        angle = math.degrees(math.acos(np.clip(self.agent.direction.dot(to_waypoint.normalize()), -1, 1)))

        cross_product = self.agent.direction.cross(to_waypoint)
        turn_direction = 'left' if cross_product < 0 else 'right'

        if angle < 2:
            return 0, None
        else:
            return angle, turn_direction
        
    def align_direction(self, waypoint: Vector):
        self.logger.info("Aligning direction")
        to_waypoint = waypoint - self.agent.position
        angle = math.degrees(math.acos(np.clip(self.agent.direction.dot(to_waypoint.normalize()), -1, 1)))
        self.logger.info(f"Angle to waypoint: {angle}")
        return angle < 5
        
    def update_position_and_direction(self):
        # with self.lock:
        info = self.client.get_informations(self.agent.id)
        position, direction = info[self.agent.id]
        self.agent.position(position)
        self.agent.direction(direction)
        self.logger.info(f"Agent{self.agent.id} update Position: {self.agent.position}, Direction: {self.agent.direction}")
        # return position, direction
    
    def reset(self):
        self.unrealcv_client.enable_controller(self.name, True)