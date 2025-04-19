"""UserAgent module: implements an agent that uses LLM and optional Activity2Action planning."""

import logging
import traceback
from typing import Tuple

from simworld.activity2action.a2a import Activity2Action
from simworld.agent.base_agent import BaseAgent
from simworld.communicator import UnrealCV
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
        communicator: UnrealCV,
        model: str = 'meta-llama/llama-3.3-70b-instruct',
        speed: float = 100,
        use_a2a: bool = False,
        use_rule_based: bool = False,
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
        """
        super().__init__(position, direction)
        self.communicator = communicator
        self.map: Map = map
        self.a2a = None
        self.llm = BaseLLM(
            model_name=model,
            url='https://openrouter.ai/api/v1',
            api_key='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',
        )
        self.id = UserAgent._id_counter
        UserAgent._id_counter += 1

        if use_a2a:
            self.a2a = Activity2Action(user_agent=self, name=self.communicator.get_agent_name(self.id), model=self.llm, rule_based=use_rule_based)

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
            while True:
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
