import os

import numpy as np
import pandas as pd
import scipy.io

from ratinabox.hsw import config, utils
from ratinabox.hsw.environment_builder import build_rectangular_environment
from ratinabox.hsw.tebc_agent import TebcAgent


def build_agent(position_data):
    """Interpolate position data, build a rectangular environment, and initialise a TebcAgent.

    Interpolated position_data is accessible via agent.position_data.

    Returns:
        agent
    """
    position_data, time_steps, positions = utils.interpolate_position_data(position_data)
    env = build_rectangular_environment(position_data[1:3].T)
    agent = TebcAgent(env, position_data)
    agent.import_trajectory(times=time_steps, positions=positions, interpolate=False)
    return agent


def filter_eyeblink_trials(position_data, response):
    """Return response rows and binarised labels for CS/US trials only (eyeblink > 0)."""
    eyeblink = position_data[3].T
    mask = eyeblink > 0
    response_test = response[mask]
    eyeblink_labels = np.where(eyeblink[mask] <= 5, 1, 2)
    return response_test, eyeblink_labels


def filter_by_velocity(position_data, response, tebc, threshold=0.02):
    """Keep only time steps where the agent was moving above *threshold* m/s."""
    pos = position_data[1:3].T
    vel = np.array(tebc.smoothed_velocity)
    moving = np.where(vel > threshold)[0]
    return pos[moving], response[moving]


def write_iteration_results(results_file, identifier, fract_control_all, fract_test_all,
                            err_allA, err_all_shuffA, err_allB_usingA,
                            err_all_shuffB_usingA, err_allB_usingB):
    """Write per-iteration decoding metrics to the open results text file."""
    results_file.write(f"Parameters: {identifier}\n")
    results_file.write(f"fract_control_all: {fract_control_all}\n")
    results_file.write(f"fract_test_all: {fract_test_all}\n")
    results_file.write(f"pos decoding A: {err_allA}\n")
    results_file.write(f"pos decoding A shuffled: {err_all_shuffA}\n")
    results_file.write(f"pos decoding B using A: {err_allB_usingA}\n")
    results_file.write(f"pos decoding B shuffled: {err_all_shuffB_usingA}\n")
    results_file.write(f"pos decoding B: {err_allB_usingB}\n")
    results_file.write("\n")


def save_simulation_data(save_dir, spikes_A, spikes_B, fr_A, fr_B,
                         label, iteration, date):
    """Save spike and firing-rate arrays for both environments as CSV files.

    label: model-specific parameter string embedded in the filename, e.g.
           "responsive_0.5_PC_0.7" or "balance_0.5_responsive_0.5_PC_0.7"
    """
    datasets = [
        ("spikesA",         spikes_A),
        ("spikesB",         spikes_B),
        ("firingrate_envA", fr_A),
        ("firingrate_envB", fr_B),
    ]
    for tag, data in datasets:
        path = os.path.join(save_dir, f"{tag}_{label}_iteration_{iteration}_{date}.csv")
        pd.DataFrame(data).to_csv(path, index=False)


def unwrap_scalar(value):
    """Return value[0] if value is a single-element list, otherwise return value unchanged."""
    return value[0] if isinstance(value, list) else value
