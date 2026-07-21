import numpy as np
import pytest

from ratinabox.hsw.environment_builder import build_rectangular_environment
from ratinabox.hsw.tebc_agent import TebcAgent

# Trajectory: walks a straight diagonal at a steady ~0.15 m/s. Trial markers
# step through CS bins 1-5 (indices 2-6) then hold at a non-CS marker, so
# time_since_cs is 0 exactly at the last CS-present sample (index 6) and grows
# by 1/30s per step afterward.
_TRAJECTORY_LEN = 40
_WALK_SPEED = 0.15  # m/s

# Step counts from the start of the trajectory to reach each checkpoint.
CS_CHECK_STEPS = 6                        # time_since_cs == 0.0  (inside the CS window)
US_CHECK_STEPS = 30                       # time_since_cs == 0.8  (inside the US window)
STEPS_CS_TO_US = US_CHECK_STEPS - CS_CHECK_STEPS


def _build_position_data():
    times = np.arange(_TRAJECTORY_LEN) / 30
    step = _WALK_SPEED / (30 * np.sqrt(2))
    xs = 0.4 + step * np.arange(_TRAJECTORY_LEN)
    ys = 0.4 + step * np.arange(_TRAJECTORY_LEN)
    markers = np.array([0, 0, 1, 2, 3, 4, 5] + [6] * (_TRAJECTORY_LEN - 7))
    return np.vstack([times, xs, ys, markers])


@pytest.fixture
def fresh_agent():
    """A TebcAgent at the start of the trajectory, not yet stepped."""
    position_data = _build_position_data()
    env = build_rectangular_environment(position_data[1:3].T)
    agent = TebcAgent(env, position_data)
    agent.import_trajectory(times=position_data[0], positions=position_data[1:3].T, interpolate=False)
    return agent


@pytest.fixture
def no_jitter(monkeypatch):
    """Strip the +/-jitter term models add on every update() so outputs are exactly reproducible."""
    monkeypatch.setattr(np.random, "normal", lambda *_, **__: 0.0)
