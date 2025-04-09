import numpy as np

class PIDController:
    def __init__(self, k_p: float, k_i: float, k_d: float):
        self.k_p = k_p
        self.k_i = k_i
        self.k_d = k_d
        self.p_error = 0
        self.i_error = 0
        self.d_error = 0

    def update(self, error: float, dt: float):
        # self.i_error += error * dt
        self.i_error += error
        self.i_error = np.clip(self.i_error, -0.1, 0.1) 
        # self.d_error = (error - self.p_error) / dt if dt > 0 else 0
        self.d_error = (error - self.p_error) 
        self.p_error = error

        return self.k_p * self.p_error + self.k_i * self.i_error + self.k_d * self.d_error


    def reset(self):
        self.p_error = 0
        self.i_error = 0
        self.d_error = 0
