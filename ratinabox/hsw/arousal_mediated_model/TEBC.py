import numpy as np
import random
from ratinabox.Neurons import PlaceCells
from ratinabox.hsw.arousal_mediated_model.tebc_response2 import *

class TEBC(PlaceCells):
    default_params = dict()

    def __init__(self, agent, N, responsive_distribution, percent_place_cells, task_responsive_indices=None, cell_types=None, place_cell_width=0.20):
        place_cells_params = {
            "n": N,
            "description": "gaussian",
            "widths": place_cell_width,
            "place_cell_centres": None,
            "wall_geometry": "geodesic",
            "min_fr": 0,
            "max_fr": 12,
            "save_history": False
        }

        super().__init__(agent, place_cells_params)


        # Initialize task_responsive_indices with a default value if not provided
        if task_responsive_indices is not None:
            self.task_responsive_indices = task_responsive_indices
        else:
            self.task_responsive_indices = np.full(N, False)  # Default value: all False

        # Initialize additional properties for CombinedPlaceTebcNeurons

        if cell_types is not None:
            self.cell_types = cell_types
        else:
            self.cell_types = np.full(N, False)  # Default value: all False

        self.agent = agent
        self.responsive_distribution = responsive_distribution

        # Calculate indices to zero out based on percent place cells
        if isinstance(percent_place_cells, list):
            percent_place_cells = float(percent_place_cells[0])

        percent_to_zero_out = (1 - percent_place_cells)
        num_elements_to_zero_out = int(self.n * percent_to_zero_out)

        # Randomly select indices to zero out
        self.indices_to_zero_out = random.sample(range(self.n), num_elements_to_zero_out)

    def _modulate_firing_rates_for_velocity(self):
        coefficients = [-3.26092478e-04, 1.74074978e-02, 8.36619150e-02, 1.16059441]
        firing_rate_function = np.poly1d(coefficients)

        vel = self.agent.smoothed_velocity

        if vel < 0.02:
            self.firingrate *= 0.2/30
        else:
            FR_mod = firing_rate_function(vel * 100)

            self.firingrate *= (FR_mod / 30)
            self.firingrate[self.indices_to_zero_out] = 0.02 / 30

    def update(self):
        super().update()
        unmodulated_baseline = self.firingrate.copy()

        self._modulate_firing_rates_for_velocity()

        # Update based on task state / response function
        task_firing_rates = self._calculate_task_firing_rates(unmodulated_baseline)

        self.firingrate += task_firing_rates
        self.firingrate += np.random.normal(-0.02/30, 0.02/30)
        
        self.save_to_history()

    def _calculate_task_firing_rates(self, unmodulated_baseline):
        current_velocity = self.agent.smoothed_velocity
        time_since_CS = self.agent.time_since_cs

        task_firing_rates = np.zeros(self.n)

        running = current_velocity > 0.02

        for i in range(self.n):
            if not self.task_responsive_indices[i]:
                continue

            in_field = bool(unmodulated_baseline[i] >= 0.2)

            if in_field and running:
                tebc_response = type_one_response(time_since_CS, self.firingrate[i])
            elif not in_field and running:
                tebc_response = type_two_response(time_since_CS, self.firingrate[i])
            elif in_field and not running:
                tebc_response = type_three_response(time_since_CS, self.firingrate[i])
            else:
                tebc_response = type_four_response(time_since_CS, self.firingrate[i])

            task_firing_rates[i] = tebc_response

        return task_firing_rates
