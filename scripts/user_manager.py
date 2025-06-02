"""UserManager module: manages user agents, simulation updates, and JSON serialization."""
import random
import traceback
from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock
from typing import List

from scripts.user_agent import UserAgent
from simworld.communicator.communicator import Communicator
from simworld.communicator.unrealcv import UnrealCV
from simworld.llm.a2a_llm import A2ALLM
from simworld.map.map import Map
from simworld.utils.load_json import load_json
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
        self.dt = self.config['simworld.dt']
        self.lock = Lock()
        self.exit_event = Event()

        self.initialize()

    def init_communicator(self):
        """Set up the Communicator, defaulting to UnrealCV."""
        self.communicator = Communicator(UnrealCV())

    def initialize(self):
        """Load roads, construct map nodes/edges, and spawn agents."""
        self.map.initialize_map_from_file(self.config['map.input_roads'])
        self.init_communicator()
        roads_data = load_json(self.config['map.input_roads'])

        road_items = roads_data.get('roads', [])
        road_objects = []
        for road in road_items:
            start = Vector(road['start']['x'] * 100, road['start']['y'] * 100)
            end = Vector(road['end']['x'] * 100, road['end']['y'] * 100)
            road_objects.append(Road(start, end))

        llm = A2ALLM(
            model_name=self.config['user.llm_model_path'],
            url=self.config['user.llm_url'],
            provider=self.config['user.llm_provider'],
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
        humanoid_ids = [agent.id for agent in self.agent]
        try:
            result = self.communicator.get_position_and_direction(humanoid_ids=humanoid_ids)
            for idx in humanoid_ids:
                pos, dir_ = result[('humanoid', idx)]
                self.agent[idx].position = pos
                self.agent[idx].direction = dir_
        except Exception as exc:
            print(f'Error in get_position_and_direction: {exc}')
            traceback.print_exc()

    def run(self):
        """Execute all agents concurrently and update until completion."""
        with ThreadPoolExecutor(
            max_workers=self.config['user.num_threads']
        ) as executor:
            print('Starting simulation.')

            try:
                futures = [executor.submit(agent.step) for agent in self.agent]
                while not all(f.done() for f in futures):
                    self.update()
            except KeyboardInterrupt:
                print('Simulation interrupted')
                self.exit_event.set()
            except Exception as exc:
                lineno = exc.__traceback__.tb_lineno
                print(f'Error at line {lineno}: {type(exc).__name__}: {exc}')
                traceback.print_exc()
                self.exit_event.set()
            finally:
                for f in futures:
                    try:
                        f.result()
                    except Exception as thr_exc:
                        print(f'Thread error: {thr_exc}')
                print('Simulation fully stopped.')

    def spawn_agent(self):
        """Spawn all agents in the Unreal environment."""
        for agent in self.agent:
            self.communicator.spawn_agent(agent, self.agent_path)

    def spawn_manager(self):
        """Spawn the UE manager process."""
        self.communicator.spawn_ue_manager(self.model_path)
