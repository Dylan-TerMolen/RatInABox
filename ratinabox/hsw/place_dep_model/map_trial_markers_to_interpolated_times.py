import numpy as np

def map_trial_markers_to_interpolated_times(original_times, trial_markers, interpolated_times):
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
