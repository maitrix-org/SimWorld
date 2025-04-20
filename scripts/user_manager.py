"""UserManager module: manages user agents, simulation updates, and JSON serialization."""
import json
import os
import random
import traceback
from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock
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

    def __init__(self, num_agent: int, config, traffic_signals: list = None, seed: int = 42):
        """Initialize UserManager with agent count and configuration."""
        random.seed(seed)
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
        self.exit_event = Event()

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
        # self.map.visualize_map()
        self.init_communicator()
        roads_file = os.path.join(self.config['map.input_roads'])
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
                exit_event=self.exit_event,
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

            try:
                futures = [executor.submit(agent.step) for agent in self.agent]
                while not all(f.done() for f in futures):
                    self.update()
            except KeyboardInterrupt:
                print('Simulation interrupted')
                self.exit_event.set()
            except Exception as exc:
                lineno = exc.__traceback__.tb_lineno
                self.logger.error(f'Error at line {lineno}: {type(exc).__name__}: {exc}')
                traceback.print_exc()
                self.exit_event.set()
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
