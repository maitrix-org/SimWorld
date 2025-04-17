from simworld.communicator.unrealcv import UnrealCV
import threading

class UnrealCvUser(UnrealCV):
    def __init__(self, ip, port, resolution):
        super().__init__(ip, port, resolution)
        self.lock = threading.Lock()

    def d_move_forward(self, object_name):
        with self.lock:
            cmd = f'vbp {object_name} MoveForward'
            self.client.request(cmd)

    def d_rotate(self, object_name, angle, direction='left'):
        if direction == 'right':
            clockwise = 1
        elif direction == 'left':
            angle = -angle
            clockwise = -1
        with self.lock:
            cmd = f'vbp {object_name} Rotate_Angle {1} {angle} {clockwise}'
            self.client.request(cmd)

    def d_turn_around(self, object_name, angle, direction='left'):
        if direction == 'right':
            clockwise = 1
        elif direction == 'left':
            angle = -angle
            clockwise = -1
        with self.lock:
            cmd = f'vbp {object_name} TurnAround {angle} {clockwise}'
            self.client.request(cmd)

    def d_step_forward(self, object_name):
        with self.lock:
            cmd = f'vbp {object_name} StepForward'
            self.client.request(cmd)

    def d_stop(self, object_name):
        with self.lock:
            cmd = f'vbp {object_name} StopDeliveryMan'
            self.client.request(cmd)

    def s_set_state(self, object_name, throttle, brake, steering):
        with self.lock:
            cmd = f'vbp {object_name} SetState {throttle} {brake} {steering}'
            self.client.request(cmd)

    def get_informations(self, manager_object_name):
        with self.lock:
            cmd = f'vbp {manager_object_name} GetDeliveryInformation'
            return self.client.request(cmd)

    def update_agents(self, manager_object_name):
        with self.lock:
            cmd = f'vbp {manager_object_name} UpdateAgents'
            self.client.request(cmd)

    def making_u_turn(self, object_name):
        with self.lock:
            cmd = f'vbp {object_name} MakingUTurn'
            self.client.request(cmd)



    def get_camera_observation(self, camera_id, viewmode='lit'):
        with self.lock:
            return self.read_image(camera_id, viewmode, 'fast')