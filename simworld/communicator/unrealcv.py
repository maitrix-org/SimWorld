"""UnrealCV communication module.

This module provides a client interface for communicating with Unreal Engine,
allowing for various operations such as object spawning, movement, and image
capture.
"""
import json
import time
from io import BytesIO
from threading import Lock

import cv2
import numpy as np
import PIL.Image
import unrealcv

from simworld.utils.logger import Logger


class UnrealCV(object):
    """Interface class for communication with Unreal Engine.

    This class provides various functionalities for communicating with Unreal Engine,
    including basic operations and traffic system operations.
    """

    def __init__(self, port=9000, ip='127.0.0.1', resolution=(320, 240)):
        """Initialize the UnrealCV client.

        Args:
            port: Connection port, defaults to 9000.
            ip: Connection IP address, defaults to 127.0.0.1.
            resolution: Resolution, defaults to (320, 240).
        """
        self.ip = ip
        # Build a client to connect to the environment
        self.client = unrealcv.Client((ip, port))
        self.client.connect()

        self.resolution = resolution

        self.lock = Lock()
        self.logger = Logger.get_logger('UnrealCV')
        self.ini_unrealcv(resolution)

    ###################################################
    # Basic Operations
    ###################################################
    def disconnect(self):
        """Disconnect from Unreal Engine."""
        self.client.disconnect()

    def ini_unrealcv(self, resolution=(320, 240)):
        """Initialize UnrealCV settings.

        Args:
            resolution: Resolution, defaults to (320, 240).
        """
        self.check_connection()
        [w, h] = resolution
        self.client.request(f'vrun setres {w}x{h}w', -1)  # Set resolution of display window
        self.client.request('DisableAllScreenMessages', -1)  # Disable all screen messages
        self.client.request('vrun sg.ShadowQuality 0', -1)  # Set shadow quality to low
        self.client.request('vrun sg.TextureQuality 0', -1)  # Set texture quality to low
        self.client.request('vrun sg.EffectsQuality 0', -1)  # Set effects quality to low

        self.client.request('vrun Editor.AsyncSkinnedAssetCompilation 2', -1)  # To correctly load the character
        time.sleep(1)

    def check_connection(self):
        """Check connection status, attempt to reconnect if not connected."""
        while self.client.isconnected() is False:
            self.logger.error('UnrealCV server is not running. Please try again')
            time.sleep(1)
            self.client.connect()

    # Deprecated
    def spawn(self, prefab, name):
        """Spawn an object (deprecated).

        Args:
            prefab: Prefab.
            name: Object name.
        """
        cmd = f'vset /objects/spawn {prefab} {name}'
        with self.lock:
            self.client.request(cmd)

    def spawn_bp_asset(self, prefab_path, name):
        """Spawn a blueprint asset.

        Args:
            prefab_path: Prefab path.
            name: Object name.
        """
        cmd = f'vset /objects/spawn_bp_asset {prefab_path} {name}'
        with self.lock:
            self.client.request(cmd)

    def clean_garbage(self):
        """Clean garbage objects."""
        with self.lock:
            self.client.request('vset /action/clean_garbage')

    def set_location(self, loc, name):
        """Set object location.

        Args:
            loc: Location coordinates in the form [x, y, z].
            name: Object name.
        """
        [x, y, z] = loc
        cmd = f'vset /object/{name}/location {x} {y} {z}'
        with self.lock:
            self.client.request(cmd)

    def set_orientation(self, orientation, name):
        """Set object orientation.

        Args:
            orientation: Orientation in the form [pitch, yaw, roll].
            name: Object name.
        """
        [pitch, yaw, roll] = orientation
        cmd = f'vset /object/{name}/rotation {pitch} {yaw} {roll}'
        with self.lock:
            self.client.request(cmd)

    def set_scale(self, scale, name):
        """Set object scale.

        Args:
            scale: Scale in the form [x, y, z].
            name: Object name.
        """
        [x, y, z] = scale
        cmd = f'vset /object/{name}/scale {x} {y} {z}'
        with self.lock:
            self.client.request(cmd)

    def set_color(self, actor_name, color):
        """Set object color.

        Args:
            actor_name: Object name.
            color: Color in the form [R, G, B].
        """
        [R, G, B] = color
        cmd = f'vset /object/{actor_name}/color {R} {G} {B}'
        with self.lock:
            self.client.request(cmd)

    def enable_controller(self, name, enable_controller):
        """Enable or disable controller.

        Args:
            name: Object name.
            enable_controller: Whether to enable controller.
        """
        cmd = f'vbp {name} EnableController {enable_controller}'
        with self.lock:
            self.client.request(cmd)

    def set_physics(self, actor_name, hasPhysics):
        """Set physics properties.

        Args:
            actor_name: Actor name.
            hasPhysics: Whether to enable physics.
        """
        cmd = f'vset /object/{actor_name}/physics {hasPhysics}'
        with self.lock:
            self.client.request(cmd)

    def set_collision(self, actor_name, hasCollision):
        """Set collision properties.

        Args:
            actor_name: Actor name.
            hasCollision: Whether to enable collision.
        """
        cmd = f'vset /object/{actor_name}/collision {hasCollision}'
        with self.lock:
            self.client.request(cmd)

    def set_movable(self, actor_name, isMovable):
        """Set movable properties.

        Args:
            actor_name: Actor name.
            isMovable: Whether the object is movable.
        """
        cmd = f'vset /object/{actor_name}/object_mobility {isMovable}'
        with self.lock:
            self.client.request(cmd)

    def destroy(self, actor_name):
        """Destroy an object.

        Args:
            actor_name: Actor name.
        """
        cmd = f'vset /object/{actor_name}/destroy'
        with self.lock:
            self.client.request(cmd)

    def apply_action_transition(self, robot_name, action):
        """Apply transition action.

        Args:
            robot_name: Robot name.
            action: Action in the form [speed, duration, direction].
        """
        [speed, duration, direction] = action
        if speed < 0:
            # Switch direction
            if direction == 0:
                direction = 1
            elif direction == 1:
                direction = 0
            elif direction == 2:
                direction = 3
            elif direction == 3:
                direction = 2
        cmd = f'vbp {robot_name} Move_Speed {speed} {duration} {direction}'
        with self.lock:
            self.client.request(cmd)
        time.sleep(duration)

    def apply_action_rotation(self, robot_name, action):
        """Apply rotation action.

        Args:
            robot_name: Robot name.
            action: Action in the form [duration, angle, direction].
        """
        [duration, angle, direction] = action
        cmd = f'vbp {robot_name} Rotate_Angle {duration} {angle} {direction}'
        with self.lock:
            self.client.request(cmd)
        time.sleep(duration)

    def get_objects(self):
        """Get all objects.

        Returns:
            List of objects.
        """
        with self.lock:
            res = self.client.request('vget /objects')
        objects = np.array(res.split())
        return objects

    def get_total_collision(self, name):
        """Get total collision count.

        Args:
            name: Object name.

        Returns:
            Total collision count.
        """
        with self.lock:
            res = self.client.request(f'vbp {name} GetCollisionNum')
        total_collision = eval(json.loads(res)['TotalCollision'])
        return total_collision

    def get_location(self, actor_name):
        """Get object location.

        Args:
            actor_name: Actor name.

        Returns:
            Location coordinates array.
        """
        cmd = f'vget /object/{actor_name}/location'
        with self.lock:
            res = self.client.request(cmd)
        location = [float(i) for i in res.split()]
        return np.array(location)

    def get_location_batch(self, actor_names):
        """Batch get object locations.

        Args:
            actor_names: List of actor names.

        Returns:
            List of location coordinate arrays.
        """
        cmd = [f'vget /object/{actor_name}/location' for actor_name in actor_names]
        with self.lock:
            res = self.client.request_batch(cmd)
        # Parse each response and convert to numpy array
        locations = [np.array([float(i) for i in r.split()]) for r in res]
        return locations

    def get_orientation(self, actor_name):
        """Get object orientation.

        Args:
            actor_name: Actor name.

        Returns:
            Orientation array.
        """
        cmd = f'vget /object/{actor_name}/rotation'
        with self.lock:
            res = self.client.request(cmd)
            orientation = [float(i) for i in res.split()]
        return np.array(orientation)

    def get_orientation_batch(self, actor_names):
        """Batch get object orientations.

        Args:
            actor_names: List of actor names.

        Returns:
            List of orientation arrays.
        """
        cmd = [f'vget /object/{actor_name}/rotation' for actor_name in actor_names]
        with self.lock:
            res = self.client.request_batch(cmd)
        # Parse each response and convert to numpy array
        orientations = [np.array([float(i) for i in r.split()]) for r in res]
        return orientations

    def show_img(self, img, title='raw_img'):
        """Display an image.

        Args:
            img: Image.
            title: Title, defaults to "raw_img".
        """
        cv2.imshow(title, img)
        cv2.waitKey(3)

    def read_image(self, cam_id, viewmode, mode='direct'):
        """Read an image.

        Args:
            cam_id: Camera ID, e.g., 0, 1, 2...
            viewmode: View mode, e.g., lit, normal, depth, object_mask.
            mode: Mode, possible values are 'direct', 'file', 'fast'.

        Returns:
            Image data.
        """
        if mode == 'direct':  # Get image from unrealcv in png format
            cmd = f'vget /camera/{cam_id}/{viewmode} png'
            with self.lock:
                image = self.decode_png(self.client.request(cmd))

        elif mode == 'file':  # Save image to file and read it
            cmd = f'vget /camera/{cam_id}/{viewmode} {viewmode}{self.ip}.png'
            with self.lock:
                img_dirs = self.client.request(cmd)
            image = cv2.imread(img_dirs)
        elif mode == 'fast':  # Get image from unrealcv in bmp format
            cmd = f'vget /camera/{cam_id}/{viewmode} bmp'
            with self.lock:
                image = self.decode_bmp(self.client.request(cmd))
        return image

    def decode_png(self, res):
        """Decode PNG image.

        Args:
            res: PNG image data.

        Returns:
            Decoded image data.
        """
        img = np.asarray(PIL.Image.open(BytesIO(res)))
        img = img[:, :, :-1]  # Delete alpha channel
        img = img[:, :, ::-1]  # Transpose channel order
        return img

    def decode_bmp(self, res, channel=4):
        """Decode BMP image.

        Args:
            res: BMP image data.
            channel: Number of channels, defaults to 4.

        Returns:
            Decoded image data.
        """
        img = np.fromstring(res, dtype=np.uint8)
        img = img[-self.resolution[1]*self.resolution[0]*channel:]
        img = img.reshape(self.resolution[1], self.resolution[0], channel)
        return img[:, :, :-1]  # Delete alpha channel

    ##############################################################
    # Traffic System
    ##############################################################
    def v_set_state(self, object_name, throttle, brake, steering):
        """Set vehicle state.

        Args:
            object_name: Object name.
            throttle: Throttle value.
            brake: Brake value.
            steering: Steering value.
        """
        cmd = f'vbp {object_name} SetState {throttle} {brake} {steering}'
        with self.lock:
            self.client.request(cmd)

    def v_make_u_turn(self, object_name):
        """Make vehicle U-turn.

        Args:
            object_name: Object name.
        """
        cmd = f'vbp {object_name} MakeUTurn'
        with self.lock:
            self.client.request(cmd)

    def v_set_states(self, manager_object_name, states: str):
        """Batch set vehicle states.

        Args:
            manager_object_name: Manager object name.
            states: States string.
        """
        cmd = f'vbp {manager_object_name} VSetState {states}'
        with self.lock:
            self.client.request(cmd)

    def p_set_states(self, manager_object_name, states: str):
        """Batch set pedestrian states.

        Args:
            manager_object_name: Manager object name.
            states: States string.
        """
        cmd = f'vbp {manager_object_name} PSetState {states}'
        with self.lock:
            self.client.request(cmd)

    def p_stop(self, object_name):
        """Stop pedestrian movement.

        Args:
            object_name: Object name.
        """
        cmd = f'vbp {object_name} StopPedestrian'
        with self.lock:
            self.client.request(cmd)

    def p_move_forward(self, object_name):
        """Move pedestrian forward.

        Args:
            object_name: Object name.
        """
        cmd = f'vbp {object_name} MoveForward'
        with self.lock:
            self.client.request(cmd)

    def p_rotate(self, object_name, angle, direction='left'):
        """Rotate pedestrian.

        Args:
            object_name: Object name.
            angle: Angle.
            direction: Direction, defaults to 'left'.
        """
        if direction == 'right':
            clockwise = 1
        elif direction == 'left':
            angle = -angle
            clockwise = -1
        cmd = f'vbp {object_name} Rotate_Angle {1} {angle} {clockwise}'
        with self.lock:
            self.client.request(cmd)

    def p_set_speed(self, object_name, speed):
        """Set pedestrian speed.

        Args:
            object_name: Object name.
            speed: Speed.
        """
        cmd = f'vbp {object_name} SetMaxSpeed {speed}'
        with self.lock:
            self.client.request(cmd)

    def tl_set_vehicle_green(self, object_name: str):
        """Set vehicle traffic light to green.

        Args:
            object_name: Object name.
        """
        cmd = f'vbp {object_name} SwitchVehicleFrontGreen'
        with self.lock:
            self.client.request(cmd)

    def tl_set_pedestrian_walk(self, object_name: str):
        """Set pedestrian traffic light to walk.

        Args:
            object_name: Object name.
        """
        cmd = f'vbp {object_name} SetPedestrianWalk'
        with self.lock:
            self.client.request(cmd)

    def tl_set_duration(self, object_name: str, green_duration: float, yellow_duration: float, pedestrian_green_duration: float):
        """Set traffic light duration.

        Args:
            object_name: Object name.
            green_duration: Green duration.
            yellow_duration: Yellow duration.
            pedestrian_green_duration: Pedestrian green duration.
        """
        cmd = f'vbp {object_name} SetDuration {green_duration} {yellow_duration} {pedestrian_green_duration}'
        with self.lock:
            self.client.request(cmd)

    def get_informations(self, manager_object_name):
        """Get information.

        Args:
            manager_object_name: Name of the manager object to get information from.

        Returns:
            str: Information string containing the current state of the environment.
        """
        cmd = f'vbp {manager_object_name} GetInformation'
        with self.lock:
            return self.client.request(cmd)

    def update_ue_manager(self, manager_object_name):
        """Update UE manager.

        Args:
            manager_object_name: Name of the manager object to update.
        """
        cmd = f'vbp {manager_object_name} UpdateObjects'
        with self.lock:
            self.client.request(cmd)

    #
    # User Agent Methods
    #

    def agent_move_forward(self, object_name):
        """Move agent forward.

        Args:
            object_name: Name of the agent object to move forward.
        """
        cmd = f'vbp {object_name} MoveForward'
        with self.lock:
            self.client.request(cmd)

    def agent_rotate(self, object_name, angle, direction='left'):
        """Rotate agent.

        Args:
            object_name: Name of the agent object to rotate.
            angle: Rotation angle in degrees.
            direction: Direction of rotation, either 'left' or 'right'. Defaults to 'left'.
        """
        if direction == 'right':
            clockwise = 1
        elif direction == 'left':
            angle = -angle
            clockwise = -1
        cmd = f'vbp {object_name} Rotate_Angle {1} {angle} {clockwise}'
        with self.lock:
            self.client.request(cmd)

    def agent_stop(self, object_name):
        """Stop agent.

        Args:
            object_name: Name of the agent object to stop.
        """
        cmd = f'vbp {object_name} StopAgent'
        with self.lock:
            self.client.request(cmd)

    def agent_step_forward(self, object_name, duration):
        """Step forward.

        Args:
            object_name: Name of the agent object to step forward.
            duration: Duration of the step forward movement in seconds.
        """
        cmd = f'vbp {object_name} StepForward {duration}'
        with self.lock:
            self.client.request(cmd)
        time.sleep(duration)

    def agent_set_speed(self, object_name, speed):
        """Set agent speed.

        Args:
            object_name: Name of the agent object to set speed.
            speed: Speed to set.
        """
        cmd = f'vbp {object_name} SetMaxSpeed {speed}'
        with self.lock:
            self.client.request(cmd)

    def agent_sit_down(self, object_name):
        """Sit down.

        Args:
            object_name: Name of the agent object to sit down.
        """
        cmd = f'vbp {object_name} SitDown'
        with self.lock:
            self.client.request(cmd)
