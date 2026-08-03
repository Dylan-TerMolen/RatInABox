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

#type 2 has a flat top
