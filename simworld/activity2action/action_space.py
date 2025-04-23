"""ActionSpace module: defines Action enum, Waypoint model, and ActionSpace container."""

from enum import Enum
from typing import Dict

from pydantic import BaseModel

FORMAT = """
{
    "actions": [0, 2, ...],
    "waypoints": ["Vector(x=1.0, y=2.0)", "Vector(x=2.0, y=3.0)", ...],
}
"""


class Action(Enum):
    """Actions that an agent can perform."""
    Navigate = 0

    @classmethod
    def get_description(cls) -> Dict[int, str]:
        """Return a dictionary mapping action values to their descriptions."""
        return {action.value: f'{action.value}: {action.name.lower()}'
                for action in cls}


ACTION_LIST = list(Action.get_description().values())


class Waypoint(BaseModel):
    """Represents a 2D point with x and y coordinates."""
    x: float
    y: float
