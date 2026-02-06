import numpy as np
import pandas as pd
from ratinabox.Neurons import Neurons, PlaceCells
from tebc_response2 import response_profiles


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

    cell_type_probs = [0.051, 0.032, 0.373, 0.155, 0.199, 0.050, 0.093, 0.047]
    #cell_type_probs = [0, 0, 0, 0, 0, 0, 1, 0]
    cell_types = np.random.choice(range(1, 9), size=N, p=cell_type_probs)
    return responsive_neurons, cell_types

#type 2 has a flat top
