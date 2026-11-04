import numpy as np

# Define the timing of stimuli in seconds
CS_duration = 0.25  # 250 ms
US_start_time = CS_duration + 0.5  # 500 ms after the end of CS
US_duration = 0.100

# How long an inhibitory (below-baseline) response is held before rebounding back to
# baseline. Shared by every inhibitory type (3, 4, 8) so they all recover on the same
# timescale instead of each hardcoding its own cutoff.
TRIAL_PERIOD = 1.5


# Cell type 1: bimodal with peaks as a multiple of the baseline
def gaussian_peak(time_since_CS, magnitude, peak_time, sd, baseline):
    # Gaussian response calculation
    response = magnitude * np.exp(-((time_since_CS - peak_time) ** 2) / (2 * sd ** 2))
    # Apply Gaussian response only near the peak time
    response = np.where(time_since_CS, response + baseline, baseline)
    return response
def bimodal_response(time_since_CS, magnitudes, peak_times, sds, baseline, cs_duration, us_duration):
    peak1 = gaussian_peak(time_since_CS, magnitudes[0], peak_times[0], sds[0], baseline)
    peak2 = gaussian_peak(time_since_CS, magnitudes[1], peak_times[1], sds[1], baseline)
    return peak1 + peak2


# Cell type 2: Gaussian peak with a multiple of the baseline
def gaussian_peak2(time_since_CS, magnitude, peak_time, sd, duration, baseline):
    response = magnitude * np.exp(-((time_since_CS - peak_time) ** 2) / (2 * sd ** 2)) + baseline
    if time_since_CS>peak_time-1/10:
        return response
    else:
        return baseline

# Cell type 3: Linear decay response, changes relative to baseline. Inhibitory (both
# magnitudes sit below baseline) -- like type 8, it rebounds back to baseline once the
# response has been held past TRIAL_PERIOD, rather than staying suppressed indefinitely.
def linear_decay_response(time_since_CS, baseline, peak_time, mid_time, first_magnitude, second_magnitude):
    if time_since_CS <= 0:
        return baseline
    elif 0 < time_since_CS < .2:
        slope = (first_magnitude - baseline) / .2
        return slope * (time_since_CS) + baseline
    elif .2 <= time_since_CS < .85:
        slope = (second_magnitude - first_magnitude) / .65
        return slope * (time_since_CS - mid_time) + first_magnitude
    elif time_since_CS <= TRIAL_PERIOD:
        return second_magnitude
    else:
        return baseline

# Cell type 4: Adjusting the peaks to be a function of baseline
def cell_type_4_response(time_since_CS, baseline, cs_peak, us_peak, cs_sd, us_sd, cs_decay_start, us_peak_time, us_duration):
    # Parameters for the response function
    if time_since_CS <= .05:
        total_response = baseline
    if .05<time_since_CS<=.78:
        slope = (cs_peak-baseline)/.73
        total_response =  slope * (time_since_CS-.05) + baseline
    if .78<time_since_CS<=1:
        total_response = us_peak * np.exp(-((time_since_CS - .78) ** 2) / (5 * us_sd ** 5)) + baseline
    # Inhibited plateau, then rebound back to baseline past TRIAL_PERIOD -- same
    # recovery timescale as types 3 and 8, rather than staying suppressed until t=3.
    if 1<time_since_CS<=TRIAL_PERIOD:
        total_response = cs_peak
    if time_since_CS>TRIAL_PERIOD:
        total_response = baseline
    if total_response<cs_peak:
        total_response = cs_peak
    if total_response>us_peak:
        total_response = us_peak
    return total_response


# Cell type 5: Sharp increase to a peak that's a multiple of the baseline
def cell_type_5_function(time_since_CS, baseline, us_peak, us_duration):
    us_peak_time = US_start_time  # Assuming peak is right at the start of US
    # Start with a baseline
    response = baseline
    # Sharp increase to US peak
    if US_start_time <= time_since_CS < (US_start_time + us_duration):
        response = np.interp(time_since_CS, [.75, .78], [baseline, us_peak])
    # Linear decay from US peak back to baseline
    if us_peak_time <= time_since_CS:
        response = np.interp(time_since_CS, [.78, 1.2], [us_peak, baseline])
    return response

# Cell type 6: Noisy response around the baseline
def noisy_uniform_response(time_since_CS, baseline, noise_level=0.03/30):
    CS_duration = 0.25  # 250 ms
    US_start_time = CS_duration + 0.5  # 500 ms after the end of CS
    US_duration = 0.100
    return baseline + np.random.normal(-noise_level, noise_level)

# Cell type 7: Bimodal with peaks as a multiple of the baseline
def gaussian_peak3(time_since_CS, magnitude, peak_time, sd, duration, baseline):
    response = magnitude * np.exp(-((time_since_CS - peak_time) ** 2) / (2 * sd ** 2))
    # Apply Gaussian response only near the peak time and ensure it doesn't exceed the magnitude
    response = np.where((time_since_CS >= peak_time - 3*sd) & (time_since_CS <= peak_time + duration), response, 0)
    # Ensure response does not fall below baseline
    response += baseline
    return response
def bimodal_response2(time_since_CS, magnitudes, peak_times, sds, baseline, cs_duration, us_duration):
    peak1 = gaussian_peak3(time_since_CS, magnitudes[0], peak_times[0], sds[0], cs_duration, baseline)
    peak2 = gaussian_peak3(time_since_CS, magnitudes[1], peak_times[1], sds[1], us_duration, baseline)
    total_response = peak1 + peak2
    # Ensure the total response does not go below baseline at any point
    total_response = np.maximum(total_response, baseline)
    return total_response

# Cell type 8: Decay response with change as a proportion of baseline
def type8decay(time_since_CS, baseline):
    if time_since_CS <= .25:
        return baseline
    elif .25 < time_since_CS <= .252:
        return baseline*.46
    elif .252 <= time_since_CS < .75:
        slope = ((.62*baseline) - baseline) / (.75-.252)
        return slope * (time_since_CS - .252) + baseline
    elif .75<=time_since_CS <= TRIAL_PERIOD:
        slope = ((.38*baseline) - baseline) / .75
        return slope * (time_since_CS - .75) + baseline
    else:
        return baseline


_t_ref = np.linspace(-0.1, 2.0, 1000)

def _normalized(shape_func_at_unit_baseline):
    vals = np.array([shape_func_at_unit_baseline(t) for t in _t_ref])
    f_min, f_max = vals.min(), vals.max()
    return lambda t, baseline: (shape_func_at_unit_baseline(t) - f_min) / (f_max - f_min) * baseline


response_profiles = {
    1: {'response_func': _normalized(lambda t: bimodal_response(t, [2.14, 5.71], [0.3, .85], [0.1, 0.1], 1.0, CS_duration, US_duration))},
    2: {'response_func': _normalized(lambda t: gaussian_peak2(t, 3.14, US_start_time, 0.15, US_duration, 1.0))},
    3: {'response_func': _normalized(lambda t: linear_decay_response(t, baseline=1.0, peak_time=0, mid_time=.2, first_magnitude=0.33, second_magnitude=0.17))},
    4: {'response_func': _normalized(lambda t: cell_type_4_response(t, 1.0, 0.4, 1.1, cs_sd=0.1, us_sd=0.2, cs_decay_start=.25, us_peak_time=.75, us_duration=0.1))},
    5: {'response_func': _normalized(lambda t: cell_type_5_function(t, 1.0, 3.14, US_duration))},
    6: {'response_func': lambda t, baseline: noisy_uniform_response(t, baseline * 0.5)},
    7: {'response_func': _normalized(lambda t: bimodal_response2(t, [1.67, 2.14], [0.3, US_start_time + .05], [0.08, 0.15], 1.0, cs_duration=.25, us_duration=.1))},
    8: {'response_func': _normalized(lambda t: type8decay(t, 1.0))},
}


# Empirical prevalence of each tEBC response type (types 1-8).
BASE_CELL_TYPE_PROBS = [0.051, 0.032, 0.373, 0.155, 0.199, 0.050, 0.093, 0.047]

# Runtime-selectable subset of types sampled when the caller doesn't ask for a
# specific set -- everywhere task_types defaults to this rather than all 8 (CLI,
# assign_tebc_types_and_responsiveness, holdover_task_responsiveness). Pass
# task_types=None explicitly (or list(range(1, 9)) on the CLI) to opt back into
# every type at its full empirical prevalence.
DEFAULT_TASK_TYPES = [1, 2, 3, 8]


def _resolve_task_type_distribution(task_types):
    """Return (types, probabilities) to sample cell types from.

    When task_types is None, use all response types with their empirical
    prevalence. Otherwise restrict sampling to the chosen types, renormalizing
    their empirical probabilities so they sum to 1. Fewer types raises the
    chance the same type recurs across environments, increasing cross-env overlap.
    """
    if task_types is None:
        return np.arange(1, len(BASE_CELL_TYPE_PROBS) + 1), np.array(BASE_CELL_TYPE_PROBS)

    types = [int(t) for t in task_types]
    invalid = [t for t in types if t not in response_profiles]
    if invalid:
        raise ValueError(f"Unknown tEBC response type(s): {invalid}. Available: {sorted(response_profiles)}")

    probs = np.array([BASE_CELL_TYPE_PROBS[t - 1] for t in types], dtype=float)
    probs = probs / probs.sum()
    return np.array(types), probs


def assign_tebc_types_and_responsiveness(N, percent_task_responsive_cells_distribution, task_types=DEFAULT_TASK_TYPES):
    # Check if percent_task_responsive_cells_distribution is a single value or an array
    if isinstance(percent_task_responsive_cells_distribution, (float, int)):
        responsive_probs = np.full(N, percent_task_responsive_cells_distribution)
    else:
        responsive_probs = np.array(percent_task_responsive_cells_distribution)
        if responsive_probs.ndim != 1 or len(responsive_probs) != N:
            raise ValueError("percent_task_responsive_cells_distribution must be a 1D array of length N")
    responsive_probs = np.clip(responsive_probs, 0, 1)
    responsive_neurons = np.random.rand(N) < responsive_probs

    types, cell_type_probs = _resolve_task_type_distribution(task_types)
    cell_types = np.random.choice(types, size=N, p=cell_type_probs)
    return responsive_neurons, cell_types


def holdover_task_responsiveness(task_responsive_indices_A, cell_types_A, holdover_fraction,
                                  percent_task_responsive_cells_distribution_B, task_types=DEFAULT_TASK_TYPES):
    """Blend env A's task-responsive cells into env B's assignment.

    `ceil(holdover_fraction * num_A_task_responsive)` of env A's actual task-responsive
    cells carry over into env B unchanged (same indices, same cell types) -- these cells
    may or may not remain place-responsive in B, since place-responsiveness is redrawn
    independently per env. The remaining slots needed to reach env B's target task-responsive
    count are drawn fresh (new indices, new cell types) from whichever cells aren't already
    held over. Env B's target count is exact (round of the distribution's sum), so the total
    never inflates past target regardless of how many cells were held over.
    """
    N = len(task_responsive_indices_A)
    a_responsive_indices = np.flatnonzero(task_responsive_indices_A)
    target_total = int(round(np.sum(percent_task_responsive_cells_distribution_B)))
    # Env A's own assignment is still a per-cell Bernoulli draw (not exact-count), so its
    # realized task-responsive count can exceed env B's target by chance -- cap at target_total
    # so a high holdover_fraction can't carry that overshoot into env B.
    num_held = min(int(np.ceil(holdover_fraction * len(a_responsive_indices))), target_total)
    held_indices = np.random.choice(a_responsive_indices, size=num_held, replace=False)

    remaining_pool = np.setdiff1d(np.arange(N), held_indices)
    # target_total <= N and num_held <= target_total, so num_fresh always lands in
    # [0, len(remaining_pool)] -- no clamping needed.
    num_fresh = target_total - num_held
    fresh_indices = np.random.choice(remaining_pool, size=num_fresh, replace=False)

    task_responsive_indices_B = np.full(N, False)
    task_responsive_indices_B[held_indices] = True
    task_responsive_indices_B[fresh_indices] = True

    types, cell_type_probs = _resolve_task_type_distribution(task_types)
    responsive_indices_B = np.flatnonzero(task_responsive_indices_B)
    cell_types_B = np.zeros(N, dtype=int)
    cell_types_B[responsive_indices_B] = np.random.choice(types, size=len(responsive_indices_B), p=cell_type_probs)
    cell_types_B[held_indices] = cell_types_A[held_indices]

    return task_responsive_indices_B, cell_types_B
