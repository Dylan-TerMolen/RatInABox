import numpy as np
import pandas as pd
from ratinabox.Neurons import Neurons, PlaceCells
from ratinabox.hsw.independent_model.tebc_response2 import response_profiles

# Empirical prevalence of each tEBC response type (types 1-8).
BASE_CELL_TYPE_PROBS = [0.051, 0.032, 0.373, 0.155, 0.199, 0.050, 0.093, 0.047]


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


def assign_tebc_types_and_responsiveness(N, percent_task_responsive_cells_distribution, task_types=None):
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
                                  percent_task_responsive_cells_distribution_B, task_types=None):
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

#type 2 has a flat top
