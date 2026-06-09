from ratinabox.Environment import Environment
import numpy as np

def _calculate_boundaries(positions):
    min_x = np.min(positions[:, 0])
    max_x = np.max(positions[:, 0])
    min_y = np.min(positions[:, 1])
    max_y = np.max(positions[:, 1])
    return min_x, max_x, min_y, max_y


def build_rectangular_environment(positions):
    min_x, max_x, min_y, max_y = _calculate_boundaries(positions)

    return Environment(params={
        'boundary': [[min_x, min_y], [min_x, max_y], [max_x, max_y], [max_x, min_y]],
        'boundary_conditions': 'solid'
    })
