"""Integration spec: simulate_experiment must run the full data path
main.py drives per grid combination -- build agent, build model, run the tEBC
simulation in both environments, and (for holdover > 0) carry a fraction of env
A's fitted task-responsive identity into env B -- without raising, for every
model type and across the holdover fraction's full range (0 = fully fresh,
1 = fully carried over, plus a fractional value in between).
Stops short of CEBRA decoding, which main.py hands this output to next; that's
an external dependency this repo doesn't need to exercise here.

This is the seam test_tebc_firing_rates.py doesn't cover: that suite builds
TEBC instances directly and checks firing-rate math in isolation, but never
runs the code that wires main.py's grid loop together -- which is exactly
where the `task_responsive` / `task_responsive_indices` naming mismatch bug
slipped through (only reachable via the holdover=True branch, at the seam
between main.py and the model classes).
"""
import numpy as np
import pytest

from ratinabox.hsw.simulate_envs import simulate_experiment
from ratinabox.hsw.simulation_helpers import filter_eyeblink_trials, filter_by_velocity

# build_model now threads this straight through to each TEBC class instead of
# hardcoding 80 (see simulate_envs.py), so this no longer has to match a fixed value.
NUM_NEURONS = 80

MODEL_TYPES = ["independent", "place_dependent", "arousal_mediated"]


def _short_position_data(n_steps=90, speed_cm_s=15.0, start_cm=(40.0, 40.0)):
    """A short synthetic trajectory in the same (4, n_steps) [time, x_cm, y_cm,
    trial_marker] layout as the real MATLAB position data -- build_agent expects
    centimetres and converts to metres internally, same as the real rig data.
    Cycles through CS (1-5) and US (6-10) markers so a few full tEBC trials occur.
    """
    times = np.arange(n_steps) / 30
    step = speed_cm_s / 30
    xs = start_cm[0] + step * np.arange(n_steps)
    ys = start_cm[1] + step * np.arange(n_steps)
    cycle = [0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    markers = np.array([cycle[i % len(cycle)] for i in range(n_steps)])
    return np.vstack([times, xs, ys, markers])


@pytest.fixture
def position_data_pair():
    """Independent env A / env B trajectories, offset so they aren't identical."""
    return _short_position_data(start_cm=(40.0, 40.0)), _short_position_data(start_cm=(60.0, 55.0))


@pytest.mark.parametrize("model_type", MODEL_TYPES)
@pytest.mark.parametrize("holdover", [0.0, 0.5, 1.0])
def test_simulate_experiment_runs_full_data_path(model_type, holdover, position_data_pair):
    position_data_envA, position_data_envB = position_data_pair

    spikesA, firingrate_envA, agentA, spikesB, firingrate_envB, agentB = simulate_experiment(
        model_type, position_data_envA, position_data_envB, NUM_NEURONS,
        percent_task_in_response_value=0.5, percent_task_in_response_dist="fixed", percent_task_in_response_std=0.1,
        percent_task_responsive_cells_val=0.5, percent_is_task_responsive_distribution="fixed", percent_place_cell=0.5,
        holdover=holdover, task_types=None,
    )

    for spikes, firingrate in [(spikesA, firingrate_envA), (spikesB, firingrate_envB)]:
        assert spikes.shape == firingrate.shape
        assert spikes.shape[0] == NUM_NEURONS
        assert (spikes >= 0).all()  # binned Poisson spike counts, no longer clipped to {0, 1}
        assert np.issubdtype(spikes.dtype, np.integer)
        assert np.isfinite(firingrate).all()

    # The rest of main.py's pre-decoding data path, run on the same
    # spikes/agents simulate_experiment produced.
    response_envA = np.transpose(spikesA)
    response_envB = np.transpose(spikesB)
    response_envA_test, envA_eyeblink = filter_eyeblink_trials(agentA.position_data, response_envA)
    response_envB_test, envB_eyeblink = filter_eyeblink_trials(agentB.position_data, response_envB)
    assert response_envA_test.shape[0] == len(envA_eyeblink)
    assert response_envB_test.shape[0] == len(envB_eyeblink)

    posA, filtered_envA = filter_by_velocity(agentA, response_envA)
    posB, filtered_envB = filter_by_velocity(agentB, response_envB)
    assert posA.shape[0] == filtered_envA.shape[0]
    assert posB.shape[0] == filtered_envB.shape[0]
