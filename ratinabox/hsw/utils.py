import numpy as np
from scipy import stats
from scipy.interpolate import interp1d

# TODO: deprecate in favour of args_parser.parse_list once all callers use args_parser
def parse_list(arg_value):
    if isinstance(arg_value, list):
        return [float(val) for val in arg_value]

    if isinstance(arg_value, float) or isinstance(arg_value, int):
        return [arg_value]

    if ',' in arg_value:
        return [float(item) for item in arg_value.split(',')]
    else:
        return [float(arg_value)]

def log_duplicate_timestamps(times):
    _, counts = np.unique(times, return_counts=True)
    duplicates = times[np.isin(times, np.unique(times)[counts > 1])]
    unique_dups = np.unique(duplicates)
    if len(unique_dups) == 0:
        print("No duplicate timestamps found.")
    else:
        print(f"Found {len(unique_dups)} duplicate timestamp value(s) ({duplicates.shape[0]} total occurrences):")
        for t in unique_dups:
            n = (times == t).sum()
            print(f"  t={t:.6f}  x{n}")


def get_distribution_values(dist_type, params, size):
    if dist_type == 'fixed':
        return np.full(size, params[0])
    elif dist_type == 'gaussian':
        mean, std = params
        return np.clip(stats.norm(mean, std).rvs(size=size), 0, 1)
    elif dist_type == 'binomial':
        p = params[0]
        return np.random.binomial(1, p, size=size)
    elif dist_type == 'normal':
        mean, std = params
        return np.clip(stats.norm(mean, std).rvs(size=size), 0, 1)
    elif dist_type == 'poisson':
        lam = params[0]
        return np.clip(stats.poisson(lam).rvs(size=size), 0, 1)
    elif dist_type == 'additive':
        return np.full(size, 1.0)

def _map_trial_markers_to_interpolated_times(original_times, trial_markers, interpolated_times):
    """
    Maps trial markers to the nearest time points in the interpolated times.

    Args:
    original_times (np.array): Original timestamps.
    trial_markers (np.array): Trial markers corresponding to the original timestamps.
    interpolated_times (np.array): Interpolated timestamps.

    Returns:
    np.array: Interpolated trial markers.
    """
    interpolated_trial_markers = np.zeros_like(interpolated_times, dtype=int)

    original_idx = 0
    for i, time in enumerate(interpolated_times):
        while original_idx < len(original_times) - 1 and original_times[original_idx + 1] < time:
            original_idx += 1
        interpolated_trial_markers[i] = trial_markers[original_idx]

    return interpolated_trial_markers

def interpolate_position_data(position_data, step=1/30):
    """
    Interpolate position and trial marker data to uniform time steps.

    Args:
        position_data: Raw position data array (4 x N) with rows [times, x, y, trial_markers]
        step: Time step for interpolation (default 1/30 for ~30 Hz)

    Returns:
        position_data_interp: Interpolated position data (4 x N array)
        desired_time_steps: The new time steps
        interpolated_positions: Just the x,y positions (N x 2 array)
    """
    trial_markers = position_data[3, :]
    times = position_data[0]
    desired_time_steps = np.arange(min(times), max(times), step=step)
    interpolated_trial_markers = _map_trial_markers_to_interpolated_times(times, trial_markers, desired_time_steps)
    positions = position_data[1:3].T
    position_interp_func = interp1d(times, positions, axis=0, kind="cubic", fill_value="extrapolate")
    interpolated_positions = position_interp_func(desired_time_steps) / 100
    position_data_interp = np.column_stack((
        desired_time_steps,
        interpolated_positions[:, 0],
        interpolated_positions[:, 1],
        interpolated_trial_markers
    )).T
    return position_data_interp, desired_time_steps, interpolated_positions


# TODO: remove once the agent is fully migrated to TebcAgent - moved to TebcAgent.cs_present / TebcAgent.us_present
def determine_cs_us(trial_marker):
    """
    Determines if the conditioned stimulus (CS) or unconditioned stimulus (US) should be presented.

    Args:
    trial_marker (int): The marker indicating the trial phase from the position file.
                        0 for intertrial, 1-5 for CS, 6-10 for US.

    Returns:
    tuple: (cs_present, us_present) indicating the presence of CS and US.
    """
    cs_present = 1 <= trial_marker <= 5
    us_present = 6 <= trial_marker <= 10

    return cs_present, us_present


def max_excluding_outliers(matrix):
    # Flatten the matrix to a 1D array
    data = np.array(matrix).flatten()

    # Compute Q1 and Q3
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)

    # Calculate the Interquartile Range
    IQR = Q3 - Q1

    # Identify outliers
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    non_outliers = [x for x in data if lower_bound <= x <= upper_bound]

    # Return the maximum of non-outlier values
    return max(non_outliers) if non_outliers else None


# UNUSED: The following functions are not currently called anywhere in the codebase
def _calculate_similarity(response_envA, response_envB):
    # Ensure that both arrays are of the same length
    min_length = min(len(response_envA), len(response_envB))
    response_envA = response_envA[:min_length]
    response_envB = response_envB[:min_length]

    # Calculate a similarity metric (e.g., correlation) between responses in EnvA and EnvB
    similarity = np.corrcoef(response_envA, response_envB)[0, 1]
    return similarity


def assess_learning_transfer(response_envA, response_envB, balance_value, responsive_value):
    # Calculate the similarity score for the given balance and responsive values
    similarity_score = _calculate_similarity(response_envA, response_envB)
    return similarity_score


def _calculate_spatial_accuracy(actual_firing_rates, expected_firing_rates):
    # Calculate a metric (e.g., correlation) between actual and expected firing rates
    accuracy = np.corrcoef(actual_firing_rates, expected_firing_rates)[0, 1]
    return accuracy


def compare_actual_expected_firing(actual_firing_rates_envA, actual_firing_rates_envB, expected_firing_rates, balance_levels, number_of_neurons):
    # Calculate accuracy scores for each balance level and neuron
    accuracy_scores_envA = {}
    accuracy_scores_envB = {}

    for balance_level in balance_levels:
        actual_rates_A = actual_firing_rates_envA[balance_level]
        actual_rates_B = actual_firing_rates_envB[balance_level]
        for neuron_id in range(number_of_neurons):
            expected_rates = expected_firing_rates[neuron_id]
            accuracy_scores_envA[neuron_id, balance_level] = _calculate_spatial_accuracy(actual_rates_A[neuron_id], expected_rates)
            accuracy_scores_envB[neuron_id, balance_level] = _calculate_spatial_accuracy(actual_rates_B[neuron_id], expected_rates)

    return accuracy_scores_envA, accuracy_scores_envB
