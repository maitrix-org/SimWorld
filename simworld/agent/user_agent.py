"""UserAgent module: implements an agent that uses LLM and optional Activity2Action planning."""

import logging
from typing import List, Tuple

from simworld.activity2action.a2a import Activity2Action
from simworld.agent.base_agent import BaseAgent
from simworld.communicator.user_communicator import UserCommunicator
from simworld.llm.base_llm import BaseLLM
from simworld.map.map import Map
from simworld.prompt.prompt import user_system_prompt, user_user_prompt
from simworld.utils.vector import Vector


class UserAgent(BaseAgent):
    """Agent that uses an LLM (and optional Activity2Action) to decide actions."""

    _id_counter = 0

    def __init__(
        self,
        position: Vector,
        direction: Vector,
        map: Map,
        communicator: UserCommunicator,
        model: BaseLLM,
        speed: float = 100,
        use_a2a: bool = False,
        use_rule_based: bool = False,
        config=None,
    ):
        """Initialize the UserAgent.

        Args:
            position: Starting position vector.
            direction: Initial facing direction vector.
            map: The environment map.
            communicator: Communicator for user inputs.
            model: LLM model identifier.
            speed: Movement speed parameter.
            use_a2a: Whether to enable Activity2Action planning.
            use_rule_based: Whether to use rule-based navigation in A2A.
            config: Optional configuration overrides.
        """
        super().__init__(position, direction)
        self.communicator = communicator
        self.map: Map = map
        self.a2a = None
        self.llm = model
        if use_a2a:
            self.a2a = Activity2Action(self, model=self.llm, rule_based=use_rule_based)

        self.id = UserAgent._id_counter
        UserAgent._id_counter += 1

        self.last_state: Tuple[Vector, str] = (self.position, 'do nothing')
        self.waypoints: List[Vector] = []
        self.config = config

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.speed = speed

    def get_possible_next_waypoints(self) -> List[Vector]:
        """Get possible adjacent waypoints from current position."""
        current_node = min(
            self.map.nodes,
            key=lambda node: self.position.distance(node.position),
        )
        return self.map.get_adjacent_points(current_node)

    def step(self, user_manager) -> None:
        """Perform one decision step using A2A planning if enabled."""
        while True:
            if self.a2a:
                self.logger.info(f'DeliveryMan {self.id} is deciding what to do')
                user_prompt = user_user_prompt.format(
                    position=self.get_self_position_on_map(user_manager),
                    map=self.map,
                )
                response = self.llm.generate_text(
                    system_prompt=user_system_prompt,
                    user_prompt=user_prompt,
                )
                self.a2a.parse(response)
                self.logger.info(f'UserAgent {self.id} at ({self.position})')
