"""Main SimWorld module that provides the primary interface to simulation functions."""

from simworld.communicator.communicator import Communicator
from simworld.communicator.unrealcv import UnrealCV
from simworld.config import Config


class SimWorld:
    """Main simulation world class.

    This class serves as the primary interface to the simulation environment,
    coordinating between the UnrealCV communication layer and simulation logic.

    Attributes:
        config: Configuration object containing simulation parameters.
        communicator: Communicator instance for interacting with Unreal Engine.
    """

    def __init__(self, config=None):
        """Initialize the simulation world.

        Args:
            config: Optional configuration object. If None, default configuration is used.
        """
        self.config = config if config else Config()
        self.unrealcv = UnrealCV()
        self.communicator = Communicator(self.unrealcv)

    def setup(self):
        """Set up the simulation environment.

        Initializes the simulation world and prepares it for running.
        """
        pass

    def run(self):
        """Run the simulation.

        Executes the simulation based on the current configuration.
        """
        pass

    def cleanup(self):
        """Clean up resources.

        Releases all resources and disconnects from the simulation environment.
        """
        self.communicator.disconnect()


def create_simulation(config=None):
    """Factory function to create a new simulation instance.

    Args:
        config: Optional configuration object. If None, default configuration is used.

    Returns:
        A new SimWorld instance initialized with the provided configuration.
    """
    return SimWorld(config)
