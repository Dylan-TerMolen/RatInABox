import numpy as np
from scipy import stats
from scipy.interpolate import interp1d

def parse_list(arg_value):
    if isinstance(arg_value, list) or isinstance(arg_value, float):
        return [arg_value]

    if ',' in arg_value:
        return [float(item) for item in arg_value.split(',')]
    else:
        return [float(arg_value)]

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
        return np.full(size, 100)

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
