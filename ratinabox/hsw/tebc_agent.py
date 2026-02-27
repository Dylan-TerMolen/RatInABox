import numpy as np
import pandas as pd
from ratinabox.Agent import Agent

class TebcAgent(Agent):
    default_params = dict()

    def __init__(self, environment, position_data, window_size=30, **kwargs):
        super().__init__(environment, **kwargs)
        self._step_index = 0
        self._smoothed_velocities = self._calculate_smoothed_velocity(position_data, window_size)
        self._trial_markers = position_data[3, :]
        self._times = position_data[0, :]
        self._last_cs_time = None
        self.position_data = position_data

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

    # Might need to call this on agent init / account for that case
    def update(self, dt=None, **kwargs):
        super().update(dt=dt, **kwargs)
        self._step_index += 1

        if self._step_index < len(self._times) and self.cs_present:
            self._last_cs_time = self.current_time

    def follow_trajectory(self):
        for _ in range(len(self._times)):
            yield self
            self.update()

    @property
    def smoothed_velocity(self):
        return self._smoothed_velocities[self._step_index]

    @property
    def trial_marker(self):
        return self._trial_markers[self._step_index]

    @property
    def cs_present(self):
        return 1 <= self.trial_marker <= 5

    @property
    def us_present(self):
        return 6 <= self.trial_marker <= 10

    @property
    def time_since_cs(self):
        if self._last_cs_time is None: return -1

        return self.current_time - self._last_cs_time

    @property
    def current_time(self):
        return self._times[self._step_index]
