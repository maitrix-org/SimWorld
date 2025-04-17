"""Communicator module for interfacing with Unreal Engine.

This module provides a high-level communication interface with Unreal Engine
through the UnrealCV client, handling vehicle, pedestrian, and traffic signal management.
"""
import json
import math
import re

import numpy as np
import pandas as pd

from simworld.communicator.unrealcv import UnrealCV
from simworld.utils.vector import Vector


class Communicator:
    """Class for communicating with Unreal Engine through UnrealCV.

    This class is responsible for handling communication with Unreal Engine,
    including the management of vehicles, pedestrians, and traffic signals.
    """

    def __init__(self, unrealcv: UnrealCV):
        """Initialize the communicator.

        Args:
            unrealcv: UnrealCV instance for communication with Unreal Engine.
        """
        self.unrealcv = unrealcv
        self.ue_manager_name = None

    #
    # User Agent Methods
    #

    def agent_move_forward(self, agent_id):
        """Move agent forward.

        Args:
            agent_id: The unique identifier of the agent to move forward.
        """
        self.unrealcv.agent_move_forward(self.get_agent_name(agent_id))

    def agent_rotate(self, agent_id, angle, direction):
        """Rotate agent.

        Args:
            agent_id: Agent ID.
            angle: Rotation angle.
            direction: Rotation direction.
        """
        self.unrealcv.agent_rotate(self.get_agent_name(agent_id), angle, direction)

    def agent_stop(self, agent_id):
        """Stop agent.

        Args:
            agent_id: Agent ID.
        """
        self.unrealcv.agent_stop(self.get_agent_name(agent_id))

    def agent_step_forward(self, agent_id, duration):
        """Step forward.

        Args:
            agent_id: Agent ID.
            duration: Duration.
        """
        self.unrealcv.agent_step_forward(self.get_agent_name(agent_id), duration)

    def get_agent_name(self, agent_id):
        """Get agent name.

        Args:
            agent_id: Agent ID.

        Returns:
            str: The formatted agent name.
        """
        return f'GEN_BP_Agent_{agent_id}'

    # Vehicle-related methods
    def update_vehicle(self, vehicle_id, throttle, brake, steering):
        """Update vehicle state.

        Args:
            vehicle_id: Vehicle ID.
            throttle: Throttle value.
            brake: Brake value.
            steering: Steering value.
        """
        name = self.get_vehicle_name(vehicle_id)
        self.unrealcv.v_set_state(name, throttle, brake, steering)

    def vehicle_make_u_turn(self, vehicle_id):
        """Make vehicle perform a U-turn.

        Args:
            vehicle_id: Vehicle ID.
        """
        name = self.get_vehicle_name(vehicle_id)
        self.unrealcv.v_make_u_turn(name)

    def update_vehicles(self, states):
        """Batch update multiple vehicle states.

        Args:
            states: Dictionary containing multiple vehicle states,
                   where keys are vehicle IDs and values are state tuples.
        """
        vehicles_states_str = ''
        for vehicle_id, state in states.items():
            name = self.get_vehicle_name(vehicle_id)
            vehicle_state = f'{name},{state[0]},{state[1]},{state[2]}'

            if vehicles_states_str:
                vehicles_states_str += ';'
            vehicles_states_str += vehicle_state

        self.unrealcv.v_set_states(self.ue_manager_name, vehicles_states_str)

    # Pedestrian-related methods
    def pedestrian_move_forward(self, pedestrian_id):
        """Move pedestrian forward.

        Args:
            pedestrian_id: Pedestrian ID.
        """
        name = self.get_pedestrian_name(pedestrian_id)
        self.unrealcv.p_move_forward(name)

    def pedestrian_rotate(self, pedestrian_id, angle, direction):
        """Rotate pedestrian.

        Args:
            pedestrian_id: Pedestrian ID.
            angle: Rotation angle.
            direction: Rotation direction.
        """
        name = self.get_pedestrian_name(pedestrian_id)
        self.unrealcv.p_rotate(name, angle, direction)

    def pedestrian_stop(self, pedestrian_id):
        """Stop pedestrian movement.

        Args:
            pedestrian_id: Pedestrian ID.
        """
        name = self.get_pedestrian_name(pedestrian_id)
        self.unrealcv.p_stop(name)

    def set_pedestrian_speed(self, pedestrian_id, speed):
        """Set pedestrian speed.

        Args:
            pedestrian_id: Pedestrian ID.
            speed: Pedestrian speed.
        """
        name = self.get_pedestrian_name(pedestrian_id)
        self.unrealcv.p_set_speed(name, speed)

    def update_pedestrians(self, states):
        """Batch update multiple pedestrian states.

        Args:
            states: Dictionary containing multiple pedestrian states,
                   where keys are pedestrian IDs and values are states.
        """
        pedestrians_states_str = ''
        for pedestrian_id, state in states.items():
            name = self.get_pedestrian_name(pedestrian_id)
            pedestrian_state = f'{name},{state}'

            if pedestrians_states_str:
                pedestrians_states_str += ';'
            pedestrians_states_str += pedestrian_state

        self.unrealcv.p_set_states(self.ue_manager_name, pedestrians_states_str)

    def get_pedestrian_name(self, pedestrian_id):
        """Get pedestrian name.

        Args:
            pedestrian_id: Pedestrian ID.

        Returns:
            Pedestrian name.
        """
        return f'GEN_BP_Pedestrian_{pedestrian_id}'

    # Traffic signal related methods
    def traffic_signal_switch_to(self, traffic_signal_id, state='green'):
        """Switch traffic signal state.

        Args:
            traffic_signal_id: Traffic signal ID.
            state: Target state, possible values: 'green' or 'pedestrian walk'.
        """
        name = self.get_traffic_signal_name(traffic_signal_id)
        if state == 'green':
            self.unrealcv.tl_set_vehicle_green(name)
        elif state == 'pedestrian walk':
            self.unrealcv.tl_set_pedestrian_walk(name)

    def traffic_signal_set_duration(self, traffic_signal_id, green_duration, yellow_duration, pedestrian_green_duration):
        """Set traffic signal duration.

        Args:
            traffic_signal_id: Traffic signal ID.
            green_duration: Green duration.
            yellow_duration: Yellow duration.
            pedestrian_green_duration: Pedestrian green duration.
        """
        name = self.get_traffic_signal_name(traffic_signal_id)
        self.unrealcv.tl_set_duration(name, green_duration, yellow_duration, pedestrian_green_duration)

    def get_traffic_signal_name(self, traffic_signal_id):
        """Get traffic signal name.

        Args:
            traffic_signal_id: Traffic signal ID.

        Returns:
            Traffic signal name.
        """
        return f'GEN_BP_TrafficSignal_{traffic_signal_id}'

    # Traffic management related methods
    def get_position_and_direction(self, vehicle_ids, pedestrian_ids, traffic_signal_ids, agent_ids=[]):
        """Get position and direction of vehicles, pedestrians, and traffic signals.

        Args:
            vehicle_ids: List of vehicle IDs.
            pedestrian_ids: List of pedestrian IDs.
            traffic_signal_ids: List of traffic signal IDs.
            agent_ids: Optional list of agent IDs to get their positions and directions.

        Returns:
            Dictionary containing position and direction information for all objects.
        """
        info = json.loads(self.unrealcv.get_informations(self.ue_manager_name))
        result = {}

        # Process vehicles
        locations = info['VLocations']
        rotations = info['VRotations']
        for vehicle_id in vehicle_ids:
            name = self.get_vehicle_name(vehicle_id)

            # Parse location
            location_pattern = f'{name}X=(.*?) Y=(.*?) Z='
            match = re.search(location_pattern, locations)
            if match:
                x, y = float(match.group(1)), float(match.group(2))
                position = Vector(x, y)

                # Parse rotation
                rotation_pattern = f'{name}P=.*? Y=(.*?) R='
                match = re.search(rotation_pattern, rotations)
                if match:
                    direction = float(match.group(1))
                    result[('vehicle', vehicle_id)] = (position, direction)

        # Process pedestrians
        locations = info['PLocations']
        rotations = info['PRotations']
        for pedestrian_id in pedestrian_ids:
            name = self.get_pedestrian_name(pedestrian_id)

            location_pattern = f'{name}X=(.*?) Y=(.*?) Z='
            match = re.search(location_pattern, locations)
            if match:
                x, y = float(match.group(1)), float(match.group(2))
                position = Vector(x, y)

                rotation_pattern = f'{name}P=.*? Y=(.*?) R='
                match = re.search(rotation_pattern, rotations)
                if match:
                    direction = float(match.group(1))
                    result[('pedestrian', pedestrian_id)] = (position, direction)

        # Process traffic signals
        light_states = info['LStates']
        for traffic_signal_id in traffic_signal_ids:
            name = self.get_traffic_signal_name(traffic_signal_id)
            pattern = rf'{name}(true|false)(true|false)(\d+\.\d+)'
            match = re.search(pattern, light_states)
            if match:
                is_vehicle_green = match.group(1) == 'true'
                is_pedestrian_walk = match.group(2) == 'true'
                left_time = float(match.group(3))

                result[('traffic_signal', traffic_signal_id)] = (is_vehicle_green, is_pedestrian_walk, left_time)

        # process agents
        locations = info['ALocations']
        rotations = info['ARotations']
        for agent_id in agent_ids:
            name = self.get_agent_name(agent_id)
            location_pattern = f'{name}X=(.*?) Y=(.*?) Z='
            match = re.search(location_pattern, locations)
            if match:
                x, y = float(match.group(1)), float(match.group(2))
                position = Vector(x, y)

                rotation_pattern = f'{name}P=.*? Y=(.*?) R='
                match = re.search(rotation_pattern, rotations)
                if match:
                    direction = float(match.group(1))
                    result[('agent', agent_id)] = (position, direction)

        return result

    # Initialization methods
    def spawn_agent(self, agent, model_path):
        """Spawn agent.

        Args:
            agent: Agent object.
            model_path: Model path.
        """
        name = self.get_agent_name(agent.id)
        self.unrealcv.spawn_bp_asset(model_path, name)
        # Convert 2D position to 3D (x,y -> x,y,z)
        location_3d = (
            agent.position.x,  # Unreal X = 2D Y
            agent.position.y,  # Unreal Y = 2D X
            0  # Z coordinate (ground level)
        )
        # Convert 2D direction to 3D orientation (assuming rotation around Z axis)
        orientation_3d = (
            0,  # Pitch
            math.degrees(math.atan2(agent.direction.y, agent.direction.x)),  # Yaw
            0  # Roll
        )
        self.unrealcv.set_location(location_3d, name)
        self.unrealcv.set_orientation(orientation_3d, name)
        self.unrealcv.set_scale((1, 1, 1), name)  # Default scale
        self.unrealcv.set_collision(name, True)
        self.unrealcv.set_movable(name, True)

    def spawn_vehicles(self, vehicles):
        """Spawn vehicles.

        Args:
            vehicles: List of vehicle objects.
        """
        for vehicle in vehicles:
            name = self.get_vehicle_name(vehicle.id)
            self.unrealcv.spawn_bp_asset(vehicle.vehicle_reference, name)
            # Convert 2D position to 3D (x,y -> x,y,z)
            location_3d = (
                vehicle.position.x,  # Unreal X = 2D Y
                vehicle.position.y,  # Unreal Y = 2D X
                0  # Z coordinate (ground level)
            )
            # Convert 2D direction to 3D orientation (assuming rotation around Z axis)
            orientation_3d = (
                0,  # Pitch
                math.degrees(math.atan2(vehicle.direction.y, vehicle.direction.x)),  # Yaw
                0  # Roll
            )
            self.unrealcv.set_location(location_3d, name)
            self.unrealcv.set_orientation(orientation_3d, name)
            self.unrealcv.set_scale((1, 1, 1), name)  # Default scale
            self.unrealcv.set_collision(name, True)
            self.unrealcv.set_movable(name, True)

    def spawn_pedestrians(self, pedestrians, model_path):
        """Spawn pedestrians.

        Args:
            pedestrians: List of pedestrian objects.
            model_path: Pedestrian model path.
        """
        for pedestrian in pedestrians:
            name = self.get_pedestrian_name(pedestrian.id)
            self.unrealcv.spawn_bp_asset(model_path, name)
            # Convert 2D position to 3D (x,y -> x,y,z)
            location_3d = (
                pedestrian.position.x,  # Unreal X = 2D Y
                pedestrian.position.y,  # Unreal Y = 2D X
                110  # Z coordinate (ground level)
            )
            # Convert 2D direction to 3D orientation (assuming rotation around Z axis)
            orientation_3d = (
                0,  # Pitch
                math.degrees(math.atan2(pedestrian.direction.y, pedestrian.direction.x)),  # Yaw
                0  # Roll
            )
            self.unrealcv.set_location(location_3d, name)
            self.unrealcv.set_orientation(orientation_3d, name)
            self.unrealcv.set_scale((1, 1, 1), name)  # Default scale
            self.unrealcv.set_collision(name, True)
            self.unrealcv.set_movable(name, True)

    def spawn_traffic_signals(self, traffic_signals, traffic_light_model_path, pedestrian_light_model_path):
        """Spawn traffic signals.

        Args:
            traffic_signals: List of traffic signal objects to spawn.
            traffic_light_model_path: Path to the traffic light model asset.
            pedestrian_light_model_path: Path to the pedestrian signal light model asset.
        """
        for traffic_signal in traffic_signals:
            name = self.get_traffic_signal_name(traffic_signal.id)
            if traffic_signal.type == 'pedestrian':
                model_name = pedestrian_light_model_path
            elif traffic_signal.type == 'both':
                model_name = traffic_light_model_path
            self.unrealcv.spawn_bp_asset(model_name, name)
            # Convert 2D position to 3D (x,y -> x,y,z)
            location_3d = (
                traffic_signal.position.x,
                traffic_signal.position.y,
                0  # Z coordinate (ground level)
            )
            # Convert 2D direction to 3D orientation (assuming rotation around Z axis)
            orientation_3d = (
                0,  # Pitch
                math.degrees(math.atan2(traffic_signal.direction.y, traffic_signal.direction.x)),  # Yaw
                0  # Roll
            )
            self.unrealcv.set_location(location_3d, name)
            self.unrealcv.set_orientation(orientation_3d, name)
            self.unrealcv.set_scale((1, 1, 1), name)  # Default scale
            self.unrealcv.set_collision(name, True)
            self.unrealcv.set_movable(name, False)

    def spawn_ue_manager(self, ue_manager_path):
        """Spawn UE manager.

        Args:
            ue_manager_path: Path to the UE manager asset in the content browser.
        """
        self.ue_manager_name = 'GEN_BP_UEManager'
        self.unrealcv.spawn_bp_asset(ue_manager_path, self.ue_manager_name)

    # City layout generation methods
    def generate_world(self, world_json, ue_asset_path):
        """Generate world.

        Args:
            world_json: World configuration JSON file path.
            ue_asset_path: Unreal Engine asset path.

        Returns:
            set: A set of generated object IDs.
        """
        generated_ids = set()
        # Load world from JSON
        with open(world_json, 'r') as f:
            world_setting = json.load(f)
        # Use pandas data structure, convert JSON data to pandas dataframe
        nodes = world_setting['nodes']
        node_df = pd.json_normalize(nodes, sep='_')
        node_df.set_index('id', inplace=True)

        # Load asset library
        with open(ue_asset_path, 'r') as f:
            asset_library = json.load(f)

        def process_node(row):
            """Process a single node.

            Args:
                row: Node row.
            """
            # Spawn each node on the map
            id = row.name  # name is the index of the row
            try:
                instance_ref = asset_library[node_df.loc[id, 'instance_name']]
            except KeyError:
                print("Can't find node {} in asset library".format(node_df.loc[id, 'instance_name']))
                return
            else:
                self.unrealcv.spawn_bp_asset(instance_ref, id)
                location = node_df.loc[id, ['properties_location_x', 'properties_location_y', 'properties_location_z']].to_list()
                self.unrealcv.set_location(location, id)
                orientation = node_df.loc[id, ['properties_orientation_pitch', 'properties_orientation_yaw', 'properties_orientation_roll']].to_list()
                self.unrealcv.set_orientation(orientation, id)
                scale = node_df.loc[id, ['properties_scale_x', 'properties_scale_y', 'properties_scale_z']].to_list()
                self.unrealcv.set_scale(scale, id)
                self.unrealcv.set_collision(id, True)
                self.unrealcv.set_movable(id, False)
                generated_ids.add(id)

        node_df.apply(process_node, axis=1)

        return generated_ids

    def clear_env(self):
        """Clear all objects in the environment."""
        # Get all objects in the environment
        objects = [obj.lower() for obj in self.unrealcv.get_objects()]  # Convert objects to lowercase
        # Define unwanted objects
        unwanted_terms = ['GEN_BP_']
        unwanted_terms = [term.lower() for term in unwanted_terms]  # Convert unwanted terms to lowercase

        # Get all objects starting with the unwanted terms
        indexes = np.concatenate([np.flatnonzero(np.char.startswith(objects, term)) for term in unwanted_terms])
        # Destroy them
        if indexes is not None:
            for index in indexes:
                self.unrealcv.destroy(objects[index])

        self.unrealcv.clean_garbage()

    # Utility methods
    def get_vehicle_name(self, vehicle_id):
        """Get vehicle name.

        Args:
            vehicle_id: Vehicle ID.

        Returns:
            Vehicle name.
        """
        return f'GEN_BP_Vehicle_{vehicle_id}'

    def clean_traffic(self, vehicles, pedestrians, traffic_signals):
        """Clean traffic objects.

        Args:
            vehicles: List of vehicles.
            pedestrians: List of pedestrians.
            traffic_signals: List of traffic signals.
        """
        # Can't destroy pedestrians due to issue in unrealcv
        for vehicle in vehicles:
            self.destroy(self.get_vehicle_name(vehicle.vehicle_id))
        for traffic_signal in traffic_signals:
            self.destroy(self.get_traffic_signal_name(traffic_signal.id))
        for pedestrian in pedestrians:
            self.destroy(self.get_pedestrian_name(pedestrian.pedestrian_id))

        self.destroy(self.traffic_manager_name)
        self.clean_garbage()

    def disconnect(self):
        """Disconnect from Unreal Engine."""
        self.unrealcv.disconnect()
