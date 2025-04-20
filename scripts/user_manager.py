"""UserManager module: manages user agents, simulation updates, and JSON serialization."""
import json
import os
import random
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import List

from scripts.user_agent import UserAgent
from simworld.communicator import Communicator, UnrealCV
from simworld.llm.base_llm import BaseLLM
from simworld.map.map import Map
from simworld.utils.logger import Logger
from simworld.utils.vector import Vector


class Road:
    """Represents a road segment with geometry and direction."""

    def __init__(self, start: Vector, end: Vector):
        """Initialize Road with start and end vectors."""
        self.start = start
        self.end = end
        self.direction = (end - start).normalize()
        self.length = start.distance(end)
        self.center = (start + end) / 2


class UserManager:
    """Manage multiple UserAgent instances in the simulation."""

    def __init__(self, num_agent: int, config, traffic_signals: list = None):
        """Initialize UserManager with agent count and configuration."""
        self.num_agent = num_agent
        self.config = config
        self.map = Map(self.config, traffic_signals)
        self.agent: List[UserAgent] = []
        self.model_path = self.config['simworld.ue_manager_path']
        self.agent_path = self.config['user.model_path']
        self.communicator = None
        self.logger = Logger.get_logger('UserManager')
        self.dt = self.config['simworld.dt']
        self.lock = Lock()

        self.initialize()

    def init_communicator(self, communicator=None):
        """Set up the Communicator, defaulting to UnrealCV."""
        if communicator is None:
            self.communicator = Communicator(
                UnrealCV(
                    port=self.config.get('simworld.ue_port', 9000),
                    ip=self.config.get('simworld.ue_ip', '127.0.0.1'),
                    resolution=self.config.get('simworld.resolution', (720, 600)),
                )
            )
        else:
            self.communicator = communicator

    def initialize(self):
        """Load roads, construct map nodes/edges, and spawn agents."""
        self.init_communicator()
        roads_file = os.path.join(self.config['user.input_roads'])
        with open(roads_file, 'r') as f:
            roads_data = json.load(f)

        road_items = roads_data.get('roads', [])
        road_objects = []
        for road in road_items:
            start = Vector(road['start']['x'] * 100, road['start']['y'] * 100)
            end = Vector(road['end']['x'] * 100, road['end']['y'] * 100)
            road_objects.append(Road(start, end))

        llm = BaseLLM(
            model_name=self.config['user.llm_model_path'],
            url=self.config['user.llm_url'],
            api_key=self.config['user.llm_api_key'],
        )

        for _ in range(self.num_agent):
            road = random.choice(road_objects)
            position = random.uniform(road.start, road.end)
            agent = UserAgent(
                position,
                Vector(0, 0),
                map=self.map,
                communicator=self.communicator,
                llm=llm,
                speed=self.config['user.speed'],
                use_a2a=self.config['user.a2a'],
                use_rule_based=self.config['user.rule_based'],
                config=self.config,
            )
            self.agent.append(agent)

    def update(self):
        """Fetch and apply agents' latest positions and directions."""
        agent_ids = [agent.id for agent in self.agent]
        self.logger.info(f'Updating positions for agents: {agent_ids}')
        try:
            result = self.communicator.get_position_and_direction(agent_ids=agent_ids)
            for idx in agent_ids:
                pos, dir_ = result[('agent', idx)]
                self.agent[idx].position = pos
                self.agent[idx].direction = dir_
                self.logger.info(f'Agent {idx} position: {pos}, direction: {dir_}')
        except Exception as exc:
            self.logger.error(f'Error in get_position_and_direction: {exc}')
            traceback.print_exc()

    def run(self):
        """Execute all agents concurrently and update until completion."""
        with ThreadPoolExecutor(
            max_workers=self.config['user.num_threads']
        ) as executor:
            self.logger.info('Starting simulation.')
            futures = [executor.submit(agent.step) for agent in self.agent]

            try:
                while not all(f.done() for f in futures):
                    self.update()
            except KeyboardInterrupt:
                print('Simulation interrupted')
                sys.exit(1)
            except Exception as exc:
                lineno = exc.__traceback__.tb_lineno
                self.logger.error(f'Error at line {lineno}: {type(exc).__name__}: {exc}')
                traceback.print_exc()
            finally:
                for f in futures:
                    try:
                        f.result()
                    except Exception as thr_exc:
                        self.logger.error(f'Thread error: {thr_exc}')
                self.logger.info('Simulation fully stopped.')

    def spawn_agent(self):
        """Spawn all agents in the Unreal environment."""
        for agent in self.agent:
            self.communicator.spawn_agent(agent, self.agent_path)

    def spawn_manager(self):
        """Spawn the UE manager process."""
        self.communicator.spawn_ue_manager(self.model_path)

    def to_json(self):
        """Serialize map and delivery men data to JSON."""
        with self.lock:
            data = {
                'map': {
                    'nodes': [
                        {'position': {'x': n.position.x, 'y': n.position.y}, 'type': n.type}
                        for n in self.map.nodes
                    ],
                    'edges': [
                        {
                            'node1': {'x': e.node1.position.x, 'y': e.node1.position.y},
                            'node2': {'x': e.node2.position.x, 'y': e.node2.position.y},
                        }
                        for e in self.map.edges
                    ],
                },
                'delivery_men': [
                    {
                        'id': dm.id,
                        'position': {'x': dm.position.x, 'y': dm.position.y},
                        'direction': {'x': dm.direction.x, 'y': dm.direction.y},
                        'state': str(dm.get_state()),
                        'energy': dm.get_energy(),
                        'speed': dm.get_speed(),
                    }
                    for dm in self.agent
                ],
            }
            return data
