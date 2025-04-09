import random
import json
from simworld.utils.logger import Logger
from simworld.traffic.base import TrafficSignalState
from simworld.agent import Vehicle, VehicleState
from simworld.utils.traffic_utils import cal_waypoints


class VehicleManager:
    def __init__(self, roads, num_vehicles, config):
        self.config = config
        self.vehicles = []
        self.roads = roads
        self.num_vehicles = num_vehicles
        
        with open(self.config['traffic.vehicle.model_file_path'], 'r') as f:
            self.vehicle_types = json.load(f)

        # logger
        self.logger = Logger.get_logger('VehicleController')
        self.logger.info(f"VehicleController initialized with {num_vehicles} vehicles")

        self.last_states = {}   # {vehicle_id: (throttle, brake, steering)}

        self.init_vehicles()

    def init_vehicles(self):
        while len(self.vehicles) < self.num_vehicles:
            target_road = random.choice(self.roads)
            target_lane = random.choice(list(target_road.lanes.values()))
            target_position = random.uniform(target_lane.start, target_lane.end)

            # check if the vehicle is too close to intersection
            if target_position.distance(target_lane.end) < 3 * self.config['traffic.distance_between_objects']:
                continue
            
            possible_vehicles = target_lane.vehicles
            for vehicle in possible_vehicles:
                # check if the vehicle is too close to another vehicle
                if vehicle.position.distance(target_position) < 2 * self.config['traffic.distance_between_objects'] + vehicle.length:
                    break
            else:
                target_direction = target_lane.direction
                # Randomly select a vehicle type
                vehicle_type = random.choice(list(self.vehicle_types.values()))
                new_vehicle = Vehicle(position=target_position, direction=target_direction, current_lane=target_lane, 
                                      vehicle_reference=vehicle_type['reference'], config=self.config, 
                                      length=vehicle_type['length'], width=vehicle_type['width'])
                
                waypoints = cal_waypoints(target_position, target_lane.end, self.config['traffic.gap_between_waypoints'])
                
                new_vehicle.add_waypoint(waypoints)
                target_lane.add_vehicle(new_vehicle)
                self.vehicles.append(new_vehicle)

                self.logger.info(f"Spawned Vehicle: {new_vehicle.id} of type {vehicle_type['name']} on Lane {target_lane.id} at {target_position}")
        

    def spawn_vehicles(self, communicator):
        communicator.spawn_vehicles(self.vehicles)



    def update_vehicles(self, communicator, intersection_controller, pedestrians):
        for vehicle in self.vehicles:
            # update vehicle waypoints
            if vehicle.waypoints and len(vehicle.waypoints) > 0:
                # Calculate vector from current position to waypoint
                to_waypoint = vehicle.waypoints[0] - vehicle.position
                # Calculate dot product between vehicle direction and to_waypoint vector
                dot_product = vehicle.direction.dot(to_waypoint.normalize())
                # If angle is greater than 90 degrees (dot product < 0), remove the waypoint
                if dot_product < 0:
                    vehicle.waypoints.pop(0)


            if vehicle.state == VehicleState.WAITING:
                communicator.vehicle_make_u_turn(vehicle.id)
                vehicle.set_attributes(0.05, 0, -1) # throttle = 0, brake = 0, steering = -1
                vehicle.state = VehicleState.MAKING_U_TURN

            
            if vehicle.state == VehicleState.MAKING_U_TURN:
                if vehicle.completed_u_turn():
                    vehicle.state = VehicleState.MOVING
                    vehicle.steering_pid.reset()
                else:
                    continue

            if vehicle.is_close_to_object(self.vehicles, pedestrians):
                self.logger.debug(f"Vehicle {vehicle.id} is close to another vehicle, stop it")
                if not vehicle.state == VehicleState.STOPPED:
                    vehicle.set_attributes(0, 1, 0) # throttle = 0, brake = 1, steering = 0
                    vehicle.state = VehicleState.STOPPED
                continue

            # Check if vehicle has reached current waypoint
            if vehicle.is_close_to_end():
                self.logger.debug(f"Vehicle {vehicle.id} has reached current waypoint, get next waypoints")
                next_lane, waypoints, current_intersection, is_u_turn = intersection_controller.get_waypoints_for_vehicle(vehicle.current_lane)
                
                if is_u_turn:
                    vehicle.state = VehicleState.WAITING
                    vehicle.add_waypoint(waypoints)
                    vehicle.change_to_next_lane(next_lane)
                    # communicator.set_state(vehicle.vehicle_id, 0, 1, 0)
                    vehicle.set_attributes(0, 1, 0) # throttle = 0, brake = 1, steering = 0
                    continue
                else:
                    vehicle_light_state, _ = current_intersection.get_traffic_light_state(vehicle.current_lane)
                    if vehicle_light_state == TrafficSignalState.VEHICLE_GREEN:
                        self.logger.debug(f"Vehicle {vehicle.id} has green light on lane {vehicle.current_lane.id}, add waypoints")
                        vehicle.add_waypoint(waypoints)
                        vehicle.change_to_next_lane(next_lane)
                    else:
                        if not vehicle.state == VehicleState.STOPPED:
                            self.logger.debug(f"Vehicle {vehicle.id} has red light on lane {vehicle.current_lane.id}, stop it")
                            # communicator.set_state(vehicle.vehicle_id, 0, 1, 0)
                            vehicle.set_attributes(0, 1, 0) # throttle = 0, brake = 1, steering = 0
                            vehicle.state = VehicleState.STOPPED
                        continue

            if vehicle.waypoints and len(vehicle.waypoints) > 0:
                throttle, brake, steering, changed = vehicle.compute_control(vehicle.waypoints[0], 0.1)
                if not vehicle.state == VehicleState.MOVING:
                    vehicle.state = VehicleState.MOVING

        changed_states = {}
        for vehicle in self.vehicles:
            vehicle_id = vehicle.id
            current_state = vehicle.get_attributes()
            
            if vehicle_id not in self.last_states or current_state != self.last_states[vehicle_id]:
                changed_states[vehicle_id] = current_state
                self.last_states[vehicle_id] = current_state
        
        if changed_states:
            communicator.update_vehicles(changed_states)

        




