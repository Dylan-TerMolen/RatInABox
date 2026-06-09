import numpy as np
import pandas as pd
from ratinabox.Neurons import Neurons, PlaceCells


def assign_tebc_types_and_responsiveness(N, responsive_distribution):
    # Check if responsive_distribution is a single value or an array
    if isinstance(responsive_distribution, (float, int)):
        responsive_probs = np.full(N, responsive_distribution)
    else:
        responsive_probs = np.array(responsive_distribution)
        if responsive_probs.ndim != 1 or len(responsive_probs) != N:
            raise ValueError("responsive_distribution must be a 1D array of length N")
    responsive_probs = np.clip(responsive_probs, 0, 1)
    responsive_neurons = np.random.rand(N) < responsive_probs

    return responsive_neurons
