"""A2A prompt module: defines system and user prompt templates for SimWorld agents."""

user_system_prompt = """
You are an agent in a city, your job is to explore the city and make decisions based on the map and your current state.
"""


user_user_prompt = """
You are now at {position} in a city, where the unit is cm. And you have a map of the city structured as a graph with nodes and edges:
{map}
Your job is to explore all the place in the city as fast as possible.
You should make a plan that will be sent to a lower level executor.
You should make the plan clean and concise.
The plan should include the following information:
- Where do you want to go?
"""
