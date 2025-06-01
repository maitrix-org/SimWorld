"""Humanoid agent class."""

from simworld.agent.base_agent import BaseAgent
from simworld.communicator.communicator import Communicator
from simworld.config import Config
from simworld.map.map import Map
from simworld.utils.vector import Vector


class Humanoid(BaseAgent):
    """Humanoid agent class."""

    _id_counter = 0

    def __init__(self, position: Vector, direction: Vector, map: Map = None, communicator: Communicator = None, config: Config = None):
        """Initialize humanoid agent.

        Args:
            position: Initial position.
            direction: Initial direction.
            map: Map.
            communicator: Communicator.
            config: Config.
        """
        super().__init__(position, direction)
        self.id = Humanoid._id_counter
        Humanoid._id_counter += 1

        self.map = map
        self.communicator = communicator
        self.config = config

        self.scooter_id = None

    def __str__(self):
        """Return a string representation of the humanoid agent."""
        return f'Humanoid(id={self.id}, position={self.position}, direction={self.direction}, scooter_id={self.scooter_id})'

    def __repr__(self):
        """Return a detailed string representation of the humanoid agent."""
        return self.__str__()
