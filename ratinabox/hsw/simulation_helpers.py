import csv
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


CS_US_NUM_BINS = 5


def bin_cs_us_time_ids(trial_markers):
    """Map trial markers (1-10) into CS_US_NUM_BINS ordered bins spanning the CS->US timeline.

    Markers 1-5 mark CS time ids and 6-10 mark US time ids; pairing consecutive
    markers yields five equal-width bins (1-2 -> 1, 3-4 -> 2, ... 9-10 -> 5) that
    preserve temporal order across the trial.
    """
    return np.ceil(trial_markers / 2).astype(int)


def filter_eyeblink_trials(position_data, response):
    """Return response rows and CS/US time-id bin labels for trials only (eyeblink > 0)."""
    eyeblink = position_data[3].T
    mask = eyeblink > 0
    response_test = response[mask]
    eyeblink_labels = bin_cs_us_time_ids(eyeblink[mask])
    return response_test, eyeblink_labels


def filter_by_velocity(agent, response, threshold=0.02):
    """Keep only time steps where the agent was moving above *threshold* m/s."""
    pos = agent.position_data[1:3].T
    vel = np.array(agent.smoothed_velocities)
    moving = np.where(vel > threshold)[0]
    return pos[moving], response[moving]


def write_iteration_results(results_filepath, identifier, fract_control_all, fract_test_all,
                            err_allA, err_all_shuffA, err_allB_usingA,
                            err_all_shuffB_usingA, err_allB_usingB):
    """Write per-iteration decoding metrics to the results text file."""
    with open(results_filepath, "a") as results_file:
        results_file.write(f"Parameters: {identifier}\n")
        results_file.write(f"fract_control_all: {fract_control_all}\n")
        results_file.write(f"fract_test_all: {fract_test_all}\n")
        results_file.write(f"pos decoding A: {err_allA}\n")
        results_file.write(f"pos decoding A shuffled: {err_all_shuffA}\n")
        results_file.write(f"pos decoding B using A: {err_allB_usingA}\n")
        results_file.write(f"pos decoding B shuffled: {err_all_shuffB_usingA}\n")
        results_file.write(f"pos decoding B: {err_allB_usingB}\n")
        results_file.write("\n")


def write_run_header(summary_filepath, params):
    """Write a one-time header listing every parameter passed to the job.

    params: a mapping of parameter name to value (e.g. vars(args)). Parameters
    left unset (None) are omitted so the header reflects only what applies to
    this run.
    """
    with open(summary_filepath, "a") as f:
        f.write("=== Run parameters ===\n")
        for key, value in params.items():
            if value is not None:
                f.write(f"{key}: {value}\n")
        f.write("======================\n\n")


def write_cebra_config(summary_filepath, cebra_configs):
    """Append the fully-resolved CEBRA config (tuned defaults plus any CLI overrides).

    cebra_configs: a mapping of decoder label to its resolved CEBRA kwargs, so the
    log records every parameter each decoder actually ran with, not only the ones
    passed on the command line.
    """
    with open(summary_filepath, "a") as f:
        f.write("=== CEBRA config ===\n")
        for label, config in cebra_configs.items():
            f.write(f"[{label}]\n")
            for key, value in config.items():
                f.write(f"{key}: {value}\n")
        f.write("======================\n\n")


def _metric_score(metric):
    """Return the headline score of a decoding metric (first element of a tuple, or the scalar itself)."""
    if metric is None:
        return None
    if isinstance(metric, (list, tuple)):
        return metric[0]
    return metric


def _format_score(value):
    return f"{value:.4f}" if isinstance(value, (int, float)) else "n/a"


def write_iteration_summary(summary_filepath, identifier,
                            place_a_to_a, place_b_to_b, place_a_to_b,
                            place_shuffled_a_to_a, place_shuffled_a_to_b,
                            task_a_to_a, task_b_to_b, task_a_to_b, task_shuffled_a_to_a, task_shuffled_a_to_b):
    """Append a compact, score-only summary of one iteration's decoding metrics.

    Place decoding reports A->A, B->B, and cross-env A->B plus their shuffled floors;
    task decoding reports A->A, B->B, cross-env A->B, and their shuffled floors.
    """
    place_scores = {
        "A->A":      _metric_score(place_a_to_a),
        "B->B":      _metric_score(place_b_to_b),
        "A->B":      _metric_score(place_a_to_b),
        "shuffA->A": _metric_score(place_shuffled_a_to_a),
        "shuffA->B": _metric_score(place_shuffled_a_to_b),
    }
    task_scores = {
        "A->A":      _metric_score(task_a_to_a),
        "B->B":      _metric_score(task_b_to_b),
        "A->B":      _metric_score(task_a_to_b),
        "shuffA->A": _metric_score(task_shuffled_a_to_a),
        "shuffA->B": _metric_score(task_shuffled_a_to_b),
    }
    with open(summary_filepath, "a") as f:
        f.write(f"Parameters: {identifier}\n")
        f.write("place  " + "  ".join(f"{k}: {_format_score(v)}" for k, v in place_scores.items()) + "\n")
        f.write("task   " + "  ".join(f"{k}: {_format_score(v)}" for k, v in task_scores.items()) + "\n")
        f.write("\n")


def append_results_row(csv_filepath, headers, row):
    """Append a single result row to a CSV file, writing headers if the file is new."""
    write_header = not os.path.exists(csv_filepath)
    with open(csv_filepath, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(headers)
        writer.writerow(row)


def save_simulation_data(save_dir, spikes_A, spikes_B, fr_A, fr_B,
                         label, iteration, date):
    if config.ENVIRONMENT != 'Home':
        return

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
