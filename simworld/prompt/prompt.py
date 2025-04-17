"""Prompt module: defines system and user prompt templates for SimWorld agents."""

user_system_prompt = """
You are an agent in a city, your job is to explore the city and make decisions based on the map and your current state.
"""

# TODO: modify the prompt for user llm @ Yiming
user_user_prompt_llm = """
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

delivery_man_context_prompt = """
You are now at {position} in a city, where the unit is cm. And you have a map of the city structured as a graph with nodes and edges:
{map}
There are many supply points in the city:
{supply_points}
You can go to a supply point to buy and use a beverage to recover your energy.
Your position is always at or near a node in the graph and you can move from one node to another node only if there is an edge between the two nodes. All your possible next waypoints are:
{possible_next_waypoints}
You already have the following orders in the format of List[Order]:
{orders}
Also, you can accept new orders from the platform in the format of List[Order]:
{orders_to_accept}
For each order, you should check the attributes before making a decision:
- sale_price: the price of the order
- customer_position: the position of the customer
- store_position: the position of the store
- has_picked_up: whether the order has been picked up by you
- estimated_time: the estimated time to deliver the order
- is_shared: whether the order is shared
- meeting_point: the meeting point of the shared order
- spent_time: the time that has passed since the order was opened
Note that you consume energy as long as you move. There are two ways to move: walking and driving. You lose energy as long as you move. Walking is your default way to move and you can choose to buy a bike to drive if you have enough money. Your current walking speed is {speed} cm/s. Faster walking speed will consume more energy. Now your moving way is {physical_state}.
Currently, you have {money} dollars and {energy} energy (range from 0 to 100). Recall that last time you were at {last_position} and you decided to {last_action}. Ideally, You should not move to the same position as last time.
Now it's time to make a decision. You have the following options:
0. Do nothing.
1. Accept an order. You can accept an order from the platform, but keep in mind that if you already have orders, you need to consider the time promises to customers.
2. Pick up an order. You can pick up an order from your orders. You can only pick up an order that has not been picked up by you.
3. Deliver an order. You can deliver an order from your orders. Note that you can only deliver an order that has been picked up by you.
4. Go to a supply point to buy and use a beverage. If you have low energy, you can go to a supply point to buy and use a beverage to recover your energy. A beverage costs {cost_of_beverage} dollars and recovers {recover_energy_amount} energy.
5. Open a shared order. You can open a shared order from your orders so another delivery man can join the shared order. This can save your time and energy, but you need to split the earnings with another delivery man. You can only share an order that has been picked up by you. You need to decide the meeting point and go there to wait for another delivery man. They will finish the rest of the order. Note that if the shared order is delivered late, both of you will receive negative customer ratings and penalties.
6. Go to the meeting point. If you are joining a shared order, you need to go to the meeting point and wait for another delivery man.
7. Cancel a shared order. If a shared order has not been accepted by another delivery man for a long time, you can cancel it and do it by yourself.
8. Change walking speed. You can change your walking speed to a new walking speed (range from 100 to 250 cm/s).
9. Buy a bike. You can buy a bike to increase your speed. A bike costs {price_of_bike} dollars. But it will increase your speed and decrease your energy consumption.
"""
