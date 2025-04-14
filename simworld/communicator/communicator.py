import math
import re
import json
import pandas as pd
import numpy as np
from simworld.utils.vector import Vector
from simworld.communicator.unrealcv import UnrealCV

class Communicator:
    def __init__(self, unrealcv: UnrealCV):
        self.unrealcv = unrealcv
        self.traffic_manager_name = None


    ############vehicle###########
    def update_vehicle(self, vehicle_id, throttle, brake, steering):
        name = self.get_vehicle_name(vehicle_id)
        self.unrealcv.v_set_state(name, throttle, brake, steering)

    def vehicle_make_u_turn(self, vehicle_id):
        name = self.get_vehicle_name(vehicle_id)
        self.unrealcv.v_make_u_turn(name)

    def update_vehicles(self, states):
        vehicles_states_str = ""
        for vehicle_id, state in states.items():
            name = self.get_vehicle_name(vehicle_id)
            vehicle_state = f"{name},{state[0]},{state[1]},{state[2]}"
            
            if vehicles_states_str:
                vehicles_states_str += ";"
            vehicles_states_str += vehicle_state

        self.unrealcv.v_set_states(self.traffic_manager_name, vehicles_states_str)

    ############pedestrian###########
    def pedestrian_move_forward(self, pedestrian_id):
        name = self.get_pedestrian_name(pedestrian_id)
        self.unrealcv.p_move_forward(name)

    def pedestrian_rotate(self, pedestrian_id, angle, direction):
        name = self.get_pedestrian_name(pedestrian_id)
        self.unrealcv.p_rotate(name, angle, direction)

    def pedestrian_stop(self, pedestrian_id):
        name = self.get_pedestrian_name(pedestrian_id)
        self.unrealcv.p_stop(name)

    def set_pedestrian_speed(self, pedestrian_id, speed):
        name = self.get_pedestrian_name(pedestrian_id)
        self.unrealcv.p_set_speed(name, speed)

    def update_pedestrians(self, states):
        pedestrians_states_str = ""
        for pedestrian_id, state in states.items():
            name = self.get_pedestrian_name(pedestrian_id)
            pedestrian_state = f"{name},{state}"
            
            if pedestrians_states_str:
                pedestrians_states_str += ";"
            pedestrians_states_str += pedestrian_state

        self.unrealcv.p_set_states(self.traffic_manager_name, pedestrians_states_str)


    ############ traffic signals ###########
    def traffic_signal_switch_to(self, traffic_signal_id, state='green'):
        name = self.get_traffic_signal_name(traffic_signal_id)
        if state == 'green':
            self.unrealcv.tl_set_vehicle_green(name)
        elif state == 'pedestrian walk':
            self.unrealcv.tl_set_pedestrian_walk(name)


    ############traffic###########

    def get_position_and_direction(self, vehicle_ids, pedestrian_ids, traffic_signal_ids):
        info = json.loads(self.unrealcv.get_informations(self.traffic_manager_name))
        result = {}

        # Process vehicles
        locations = info["VLocations"]
        rotations = info["VRotations"]
        for vehicle_id in vehicle_ids:
            name = self.get_vehicle_name(vehicle_id)

            # Parse location
            location_pattern = f"{name}X=(.*?) Y=(.*?) Z="
            match = re.search(location_pattern, locations)
            if match:
                x, y = float(match.group(1)), float(match.group(2))
                position = Vector(x, y)

                # Parse rotation
                rotation_pattern = f"{name}P=.*? Y=(.*?) R="
                match = re.search(rotation_pattern, rotations)
                if match:
                    direction = float(match.group(1))
                    result[("vehicle", vehicle_id)] = (position, direction)

        # Process pedestrians
        locations = info["PLocations"]
        rotations = info["PRotations"]
        for pedestrian_id in pedestrian_ids:
            name = self.get_pedestrian_name(pedestrian_id)

            location_pattern = f"{name}X=(.*?) Y=(.*?) Z="
            match = re.search(location_pattern, locations)
            if match:
                x, y = float(match.group(1)), float(match.group(2))
                position = Vector(x, y)

                rotation_pattern = f"{name}P=.*? Y=(.*?) R="
                match = re.search(rotation_pattern, rotations)
                if match:
                    direction = float(match.group(1))
                    result[("pedestrian", pedestrian_id)] = (position, direction)

        # Process traffic lights
        light_states = info["LStates"]
        for traffic_signal_id in traffic_signal_ids:
            name = self.get_traffic_signal_name(traffic_signal_id)
            pattern = f"{name}(true|false)(true|false)(\d+\.\d+)"
            match = re.search(pattern, light_states)
            if match:
                is_vehicle_green = match.group(1) == "true"
                is_pedestrian_walk = match.group(2) == "true"
                left_time = float(match.group(3))

                result[("traffic_signal", traffic_signal_id)] = (is_vehicle_green, is_pedestrian_walk, left_time)

        return result

    ############init###########
    def spawn_vehicles(self, vehicles):
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


    def spawn_pedestrians(self, pedestrians, model_name):
        for pedestrian in pedestrians:
            name = self.get_pedestrian_name(pedestrian.id)
            self.unrealcv.spawn_bp_asset(model_name, name)
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
        for traffic_signal in traffic_signals:
            name = self.get_traffic_signal_name(traffic_signal.id)
            if traffic_signal.type == "pedestrian":
                model_name = pedestrian_light_model_path
            elif traffic_signal.type == "both":
                model_name = traffic_light_model_path
            self.unrealcv.spawn_bp_asset(model_name, name)
            # Convert 2D position to 3D (x,y -> x,y,z)
            location_3d = (
                traffic_signal.position.x,
                traffic_signal.position.y,
                0 # Z coordinate (ground level)
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

    def spawn_traffic_manager(self, traffic_manager_path):
        self.traffic_manager_name = "GEN_TrafficManager"
        self.unrealcv.spawn_bp_asset(traffic_manager_path, self.traffic_manager_name)


    ############city layout generation###########
    def generate_world(self, world_json, ue_asset_path):
        generated_ids = set()
        # load world from json
        with open(world_json, 'r') as f:
            world_setting = json.load(f)
        # use pandas data structure, convert json data into pandas data frame
        nodes = world_setting['nodes']
        node_df = pd.json_normalize(nodes, sep='_')
        node_df.set_index('id', inplace=True)

        # load asset library
        with open(ue_asset_path, 'r') as f:
            asset_library = json.load(f)

        def process_node(row):
            # spawn every node on the map
            id = row.name  # name is the index of the row
            try:
                instance_ref = asset_library[node_df.loc[id, "instance_name"]]
            except KeyError:
                print("Can't find node {} in asset library".format(node_df.loc[id, "instance_name"]))
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
        # Get all the objects in the environment
        objects = [obj.lower() for obj in self.unrealcv.get_objects()]  # Convert objects to lowercase
        # Define unwanted objects
        unwanted_terms = ['GEN_BP_']
        unwanted_terms = [term.lower() for term in unwanted_terms]  # Convert unwanted terms to lowercase

        # Get all the objects starting with the name in unwanted_terms
        indexes = np.concatenate([np.flatnonzero(np.char.startswith(objects, term)) for term in unwanted_terms])
        # Destroy them
        if indexes is not None:
            for index in indexes:
                self.unrealcv.destroy(objects[index])

        self.unrealcv.clean_garbage()


    ############utils###########
    def get_vehicle_name(self, vehicle_id):
        return f'GEN_Vehicle_{vehicle_id}'

    def get_pedestrian_name(self, pedestrian_id):
        return f'GEN_Pedestrian_{pedestrian_id}'

    def get_traffic_signal_name(self, traffic_signal_id):
        return f'GEN_TrafficSignal_{traffic_signal_id}'
    
    def clean_traffic(self, vehicles, pedestrians, traffic_signals):
        # can't destroy pedestrians due to the issue in unrealcv
        for vehicle in vehicles:
            self.destroy(self.get_vehicle_name(vehicle.vehicle_id))
        for traffic_signal in traffic_signals:
            self.destroy(self.get_traffic_signal_name(traffic_signal.id))
        for pedestrian in pedestrians:
            self.destroy(self.get_pedestrian_name(pedestrian.pedestrian_id))
        
        self.destroy(self.traffic_manager_name)
        self.clean_garbage()

    def disconnect(self):
        self.unrealcv.disconnect()

