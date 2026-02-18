import numpy as np
import pandas as pd
from ratinabox.Agent import Agent

class VelocitySmoothedAgent(Agent):
    def __init__(self, environment, position_data, window_size=30, **kwargs):
        super().__init__(environment, **kwargs)
        self._velocity_index = 0
        self._smoothed_velocities = self._calculate_smoothed_velocity(position_data, window_size)

    def _calculate_smoothed_velocity(self, position_data, window_size=30):
        times = position_data[0, :]
        xpos = position_data[1, :]
        ypos = position_data[2, :]

        vel_vector = [0]
        s = len(times)

        for i in range(1, s - 1):
            if times[i] != times[i - 1]:
                hypo = np.hypot(xpos[i - 1] - xpos[i + 1], ypos[i - 1] - ypos[i + 1])
                vel = hypo / (times[i + 1] - times[i - 1])
                vel_vector.append(vel)

        vel_vector[0] = vel_vector[1]
        vel_vector.append(vel_vector[-1])

        return pd.Series(vel_vector).rolling(window=window_size, min_periods=1, center=True).mean().tolist()

    def update(self, dt=None, **kwargs):
        super().update(dt=dt, **kwargs)
        self._velocity_index += 1

    @property
    def smoothed_velocity(self):
        return self._smoothed_velocities[self._velocity_index]
