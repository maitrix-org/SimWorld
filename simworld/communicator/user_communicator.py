import math
import json
import re
from simworld.communicator.unrealcv_user import UnrealCvUser
from agent.user_agent import UserAgent
from typing import List
from simworld.utils.vector import Vector


class UserCommunicator(UnrealCvUser):
    def __init__(self, port, ip, resolution):
        super().__init__(port, ip, resolution)

        self.user_manager_name = None

        self.agent_id_to_name = {}

    def turn_around(self, id, angle, clockwise):
        self.d_turn_around(self.get_agent_name(id), angle, clockwise)

    def step_forward(self, id):
        self.d_step_forward(self.get_agent_name(id))

    def move_forward(self, id):
        self.d_move_forward(self.get_agent_name(id))

    def stop(self, id):
        self.d_stop(self.get_agent_name(id))

    def rotate(self, id, angle, turn_direction):
        self.d_rotate(self.get_agent_name(id), angle, turn_direction)

    def get_position_and_direction(self, ids):
        try:
            if self.user_manager_name is None:
                print("Warning: delivery_manager_name is not set")
                return {}

            info_str = self.get_informations(self.user_manager_name)
            if not info_str:
                print("Warning: No information received from Unreal Engine")
                return {}
            # print(f"Received info from UE: {info_str}")  # Debug print
            info = json.loads(info_str)
            result = {}
            d_locations = info["DLocations"]
            d_rotations = info["DRotations"]
            s_locations = info["SLocations"]
            s_rotations = info["SRotations"]
            for id in ids:
                name = self.get_agent_name(id)
                # Parse location
                location_pattern = f"{name}X=(.*?) Y=(.*?) Z="
                match = re.search(location_pattern, d_locations)
                if match:
                    x, y = float(match.group(1)), float(match.group(2))
                    position = Vector(x, y)
                    # Parse rotation
                    rotation_pattern = f"{name}P=.*? Y=(.*?) R="
                    match = re.search(rotation_pattern, d_rotations)
                    if match:
                        direction = float(match.group(1))
                        result[id] = (position, direction)
                    else:
                        print(f"Warning: Could not parse rotation for {name}")
                    continue

                match = re.search(location_pattern, s_locations)
                if match:
                    x, y = float(match.group(1)), float(match.group(2))
                    position = Vector(x, y)
                    # Parse rotation
                    rotation_pattern = f"{name}P=.*? Y=(.*?) R="
                    match = re.search(rotation_pattern, s_rotations)
                    if match:
                        direction = float(match.group(1))
                        result[id] = (position, direction)
                    else:
                        print(f"Warning: Could not parse rotation for {name}")
                else:
                    print(f"Warning: Could not parse location for {name}")

            return result
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(f"Raw data: {info_str}")
            return {}
        except Exception as e:
            print(f"Error in get_position_and_direction: {e}")
            return {}

    def spawn_agent(self, agents: List[UserAgent], model_path: str):
        for agent in agents:
            name = f'GEN_AGENT_{agent.id}'
            self.agent_id_to_name[agent.id] = name
            model_name = model_path
            self.spawn_bp_asset(model_name, name)
            # Convert 2D position to 3D (x,y -> x,y,z)
            location_3d = (
                agent.position.x,
                agent.position.y,
                110 # Z coordinate (ground level)
            )
            # Convert 2D direction to 3D orientation (assuming rotation around Z axis)
            orientation_3d = (
                0,  # Pitch
                math.degrees(math.atan2(agent.direction.y, agent.direction.x)),  # Yaw
                0  # Roll
            )
            self.set_location(location_3d, name)
            self.set_orientation(orientation_3d, name)
            self.set_scale((1, 1, 1), name)  # Default scale
            self.set_collision(name, True)
            self.set_movable(name, True)

    def spawn_user_manager(self, model_path: str):
        self.user_manager_name = 'GEN_UserManager'
        self.spawn_bp_asset(model_path, self.user_manager_name)

    def get_agent_name(self, id):
        if id not in self.agent_id_to_name:
            raise ValueError(f"User agent with id {id} not found")
        return self.agent_id_to_name[id]

