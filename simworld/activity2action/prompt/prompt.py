"""Prompt module: defines system and user prompt templates for SimWorld agents."""

SYSTEM_PROMPT = """
You are a low-level planner for object <NAME>. You are given a list of goal and a waypoint.
Your goal is to plan the action to achieve the goal.
You have to use the provided functions to achieve the goal.
"""

USER_PROMPT = """
You are now at {position} in a city, where the unit is cm. And you have a map of the city structured as a graph with nodes and edges:
{map}
You are given a plan from the user, you should parse the plan into a list of actions and a list of waypoints if necessary.
You support action are:
{action_list}
The number of navigate actions should be equal to the number of waypoints.
The plan is:
{plan}
"""


VLM_SYSTEM_PROMPT = """
You are a planner for object <NAME>. You are given a first-person view of your current position and a destination.
You should only plan the next action. Make sure you do not hit any obstacles.
"""

VLM_USER_PROMPT = """
You are now at {position} in a city and your destination is at {waypoint}, where the unit is cm. And you have a map of the city structured as a graph with nodes and edges:
{map}
The given image is a first-person view of your current position.
You next action should be either "MoveForward" or "Rotate".
For "MoveForward", you should specify the time (in seconds) to move forward.
For "Rotate", you should specify the direction (left or right) and the angle (in degrees) to rotate to.

Here are some example outputs:
```json
{{"choice": "MoveForward", "time": 1.0}}
```

```json
{{"choice": "Rotate", "direction": "left", "angle": 90}}
```
Provide only the JSON object with keys: choice, time, direction, angle.
"""
