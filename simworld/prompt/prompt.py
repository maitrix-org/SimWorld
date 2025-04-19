"""Prompt module: defines system and user prompt templates for SimWorld agents."""

user_system_prompt = """
You are an agent in a city, your job is to explore the city and make decisions based on the map and your current state.
"""

# TODO: modify the prompt for user llm @ Yiming
user_user_prompt = """
You are now at {position} in a city, where the unit is cm. And you have a map of the city structured as a graph with nodes and edges:
{map}
Your job is to explore all the place in the city as fast as possible.
You should make a plan that will be sent to a lower level executor.
You should make the plan clean and concise.
The plan should include the following information:
- Where do you want to go?
"""

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
0: navigate
The number of navigate actions should be equal to the number of waypoints.
The plan is:
{plan}
"""
