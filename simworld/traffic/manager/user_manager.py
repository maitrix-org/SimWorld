import random
import os
import json
import time
from typing import List
from threading import Lock
from utils.Types import Vector, Road
from simworld.config import Config
from simworld.map import Map, Node, Edge
from agent.user_agent import UserAgent
from simworld.communicator import Communicator, UnrealCV

import traceback
import sys
from simworld.utils.logger import Logger


class UserManager:
    def __init__(self, num_agent: int, config):
        self.num_agent = num_agent
        self.config = config
        self.map = Map()

        self.agent: List[UserAgent] = []
        self.model_path = self.config['traffic.pedestrian.model_path']
        self.communicator = None
        self.logger = Logger.get_logger('UserManager')

        self.lock = Lock()

        self.initialize()

    ##############################################################
    #################  Initialize the platform  ##################
    ##############################################################
    def init_communicator(self, communicator = None):
        if communicator is None:
            self.communicator = Communicator(UnrealCV(port=9000, ip='127.0.0.1', resolution=(720, 600)))
        else:
            self.communicator = communicator

    def initialize(self):
        '''
        Initialize the platform, customers, delivery men, and stores from the map
        '''
        ############# load roads #############
        with open(os.path.join(self.config['citygen.input_roads']), 'r') as f:
            roads_data = json.load(f)

        roads = roads_data['roads']

        road_objects = []
        for road in roads:
            start = Vector(road['start']['x']*100, road['start']['y']*100)
            end = Vector(road['end']['x']*100, road['end']['y']*100)
            road_objects.append(Road(start, end))

        # Initialize the map
        for road in road_objects:
            normal_vector = Vector(road.direction.y, -road.direction.x)
            point1 = road.start - normal_vector * (self.config['traffic.sidewalk_offset']) + road.direction * self.config['traffic.sidewalk_offset']
            point2 = road.end - normal_vector * (self.config['traffic.sidewalk_offset']) - road.direction * self.config['traffic.sidewalk_offset']

            point3 = road.end + normal_vector * (self.config['traffic.sidewalk_offset']) - road.direction * self.config['traffic.sidewalk_offset']
            point4 = road.start + normal_vector * (self.config['traffic.sidewalk_offset']) + road.direction * self.config['traffic.sidewalk_offset']

            node1 = Node(point1, "intersection")
            node2 = Node(point2, "intersection")
            node3 = Node(point3, "intersection")
            node4 = Node(point4, "intersection")

            self.map.add_node(node1)
            self.map.add_node(node2)
            self.map.add_node(node3)
            self.map.add_node(node4)

            self.map.add_edge(Edge(node1, node2))
            self.map.add_edge(Edge(node3, node4))
            self.map.add_edge(Edge(node1, node4))
            self.map.add_edge(Edge(node2, node3))
        # Connect adjacent roads by finding nearby nodes
        self.map.connect_adjacent_roads()

        for i in range(self.num_agent):
            # Randomly select a road
            road = random.choice(road_objects)
            # Randomly select a point on the road
            position = road.get_random_point_on_road()
            direction = road.direction

            # Create a new user agent
            agent = UserAgent(position, direction, map=self.map, communicator=self.communicator, speed=self.config['user.speed'], use_a2a=self.config['user.a2a'], use_rule_based=self.config['user.rule_based'])
            self.agent.append(agent)
            
    def run(self):
        try:
            self.logger.info("Starting simulation")

            while True:
                for agent in self.agent:
                    agent.step()
                time.sleep(self.dt)
        except KeyboardInterrupt:
            print("Simulation interrupted")
            sys.exit(1)
        except Exception as e:
            print(f"Error occurred in {__file__}:{e.__traceback__.tb_lineno}")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print(f"Error traceback:")
            traceback.print_exc()

    def spawn_agent(self):
        self.communicator.spawn_agent(self.agent, self.model_path)

    def to_json(self):
        """
        将系统内所有数据转换为 JSON 结构返回
        """
        with self.lock:
            data = {
                "map": {
                    "nodes": [
                        {
                            "position": {"x": node.position.x, "y": node.position.y},
                            "type": node.type
                        }
                        for node in self.map.nodes
                    ],
                    "edges": [
                        {
                            "node1": {"x": edge.node1.position.x, "y": edge.node1.position.y},
                            "node2": {"x": edge.node2.position.x, "y": edge.node2.position.y}
                        }
                        for edge in self.map.edges
                    ]
                },
                "delivery_men": [
                    {
                        "id": dm.id,
                        "position": {"x": dm.position.x, "y": dm.position.y},
                        "direction": {"x": dm.direction.x, "y": dm.direction.y},
                        "state": str(dm.get_state()),
                        "energy": dm.get_energy(),
                        "speed": dm.get_speed()
                    }
                    for dm in self.delivery_men
                ],
            }
            return data
