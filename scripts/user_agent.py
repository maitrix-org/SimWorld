"""UserAgent module: implements an agent that uses LLM and optional Activity2Action planning."""

import logging
import traceback
from threading import Event
from typing import Tuple

from scripts.a2a_prompt import user_system_prompt, user_user_prompt
from simworld.activity2action.a2a import Activity2Action
from simworld.agent.base_agent import BaseAgent
from simworld.communicator.unrealcv import UnrealCV
from simworld.config.config_loader import Config
from simworld.llm.base_llm import BaseLLM
from simworld.map.map import Map
from simworld.utils.vector import Vector


class UserAgent(BaseAgent):
    """Agent that uses an LLM (and optional Activity2Action) to decide actions."""

    _id_counter = 0

    def __init__(
        self,
        position: Vector,
        direction: Vector,
        map: Map,
        communicator: UnrealCV,
        llm: BaseLLM,
        config: Config,
        speed: float = 100,
        use_a2a: bool = False,
        use_rule_based: bool = False,
        exit_event: Event = None,
    ):
        """Initialize the UserAgent.

        Args:
            position: Starting position vector.
            direction: Initial facing direction vector.
            map: The environment map.
            communicator: Communicator for user inputs.
            llm: LLM model identifier.
            config: Configuration object.
            speed: Movement speed parameter.
            use_a2a: Whether to enable Activity2Action planning.
            use_rule_based: Whether to use rule-based navigation in A2A.
            exit_event: Event to signal when the agent should stop.
        """
        super().__init__(position, direction)
        self.communicator = communicator
        self.map: Map = map
        self.a2a = None
        self.llm = llm
        self.id = UserAgent._id_counter
        self.config = config
        UserAgent._id_counter += 1
        self.exit_event = exit_event

        if use_a2a:
            self.a2a = Activity2Action(user_agent=self, name=self.communicator.get_agent_name(self.id), model=self.llm,
                                       rule_based=use_rule_based, exit_event=self.exit_event)

        self.last_state: Tuple[Vector, str] = (self.position, 'do nothing')

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.speed = speed

    def __str__(self):
        """Return a string representation of the agent."""
        return f'Agent(id={self.id}, position={self.position}, direction={self.direction})'

    def __repr__(self):
        """Return a detailed string representation of the agent."""
        return f'Agent(id={self.id}, position={self.position}, direction={self.direction})'

    def step(self) -> None:
        """Perform one decision step using A2A planning if enabled."""
        try:
            while not self.exit_event.is_set():
                if self.a2a:
                    self.logger.info(f'DeliveryMan {self.id} is deciding what to do')
                    user_prompt = user_user_prompt.format(
                        position=self.position,
                        map=self.map,
                    )
                    response, _ = self.llm.generate_text(
                        system_prompt=user_system_prompt,
                        user_prompt=user_prompt,
                    )
                    self.a2a.parse(response)
                    self.logger.info(f'UserAgent {self.id} at ({self.position})')
        except Exception as e:
            self.logger.error(f'Error in UserAgent {self.id}step: {e}')
            print(f'Error in UserAgent {self.id} step: {e}')
            print(traceback.format_exc(), flush=True)
            raise e
