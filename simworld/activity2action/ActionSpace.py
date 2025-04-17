"""ActionSpace module: defines Action enum, Waypoint model, and ActionSpace container."""

import json
from enum import Enum
from typing import List

from pydantic import BaseModel

FORMAT = """
{
    "actions": [0, 2, ...],
    "waypoints": ["Vector(x=1.0, y=2.0)", "Vector(x=2.0, y=3.0)", ...],
}
"""


class Waypoint(BaseModel):
    """Represents a 2D point with x and y coordinates."""
    x: float
    y: float


class Action(Enum):
    """Actions that an agent can perform."""
    Navigate = 0


class ActionSpace(BaseModel):
    """Holds a sequence of actions and their corresponding waypoints."""
    actions: List[Action]
    waypoints: List[Waypoint]

    def __str__(self) -> str:
        """Return a human-readable representation of the ActionSpace."""
        actions_str = ','.join(str(a) for a in self.actions)
        waypoints_str = ','.join(str(w) for w in self.waypoints)
        return f'ActionSpace(actions=[{actions_str}], waypoints={waypoints_str})'

    def __repr__(self) -> str:
        """Alias for __str__."""
        return self.__str__()

    @classmethod
    def from_json(cls, json_str: str) -> 'ActionSpace':
        """Create an ActionSpace instance from a JSON string."""
        data = json.loads(json_str)
        # convert raw action values to enum members
        data['actions'] = [Action(a) for a in data.get('actions', [])]
        return cls(**data)
