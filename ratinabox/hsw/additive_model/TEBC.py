import random
import numpy as np

from ratinabox.Neurons import PlaceCells
from ratinabox.hsw.additive_model.tebc_response2 import response_profiles


'''
Python class template for CombinedPlaceTebcNeurons that integrates both place cell and tEBC
cell functionalities. This class is designed to be used with the RatInABox framework.
- It includes a balance parameter to adjust the contribution of place cell activity versus
tEBC cell activity for each neuron.
- also includes tebc_responsive_rate that specifies the percentage of neurons that are responsive to tEBC signals.

# Example usage
num_neurons = 100
balance = 0.5  # Example balance factor
tebc_responsive_rate = 0.6  # Example: 60% of neurons are tEBC-responsive
combined_neurons = TEBC(num_neurons, place_cells, balance, tebc_responsive_rate)

'''


class TEBC(PlaceCells):
    default_params = dict()  # Add this line to define the default_params attribute

    def __init__(self, agent, N, balance_distribution, responsive_distribution, percent_place_cells, tebc_responsive_neurons=None, cell_types=None, place_cell_width=0.20):
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


        # Initialize tebc_responsive_neurons with a default value if not provided
        if tebc_responsive_neurons is not None:
            self.tebc_responsive_neurons = tebc_responsive_neurons
        else:
            self.tebc_responsive_neurons = np.full(N, False)  # Default value: all False

        # Initialize additional properties for CombinedPlaceTebcNeurons

        if cell_types is not None:
            self.cell_types = cell_types
        else:
            self.cell_types = np.full(N, False)  # Default value: all False

        self.agent = agent
        self.balance_distribution = balance_distribution
        self.responsive_distribution = responsive_distribution

        # Calculate indices to zero out based on percent place cells
        if isinstance(percent_place_cells, list):
            percent_place_cells = float(percent_place_cells[0])

        percent_to_zero_out = (1 - percent_place_cells)
        num_elements_to_zero_out = int(self.n * percent_to_zero_out)

        # Randomly select indices to zero out
        self.indices_to_zero_out = random.sample(range(self.n), num_elements_to_zero_out)


    def update(self):
        super().update()
        self._modulate_firing_rates_for_velocity()

        # Update based on task state / response function
        task_firing_rates = self._calculate_task_firing_rates(self.agent.time_since_cs)

        self.firingrate = (self.balance_distribution * task_firing_rates) + (self.firingrate * (1 - self.balance_distribution))
        self.firingrate += np.random.normal(-0.02/30, 0.02/30)
        
        self.save_to_history()


    def _modulate_firing_rates_for_velocity(self):
        coefficients = [-3.26092478e-04, 1.74074978e-02, 8.36619150e-02, 1.16059441]
        firing_rate_function = np.poly1d(coefficients)

        vel = self.agent.smoothed_velocity

        if vel < 0.02:
            self.firingrate = np.zeros(self.n)
        else:
            FR_mod = firing_rate_function(vel * 100)

            self.firingrate *= (FR_mod / 30)
            self.firingrate[self.indices_to_zero_out] = 0.02 / 30


    def _calculate_task_firing_rates(self, time_since_CS):
        task_firing_rates = np.zeros(self.n)

        for i in range(self.n):
            tebc_response = 0

            # [DT] I have not validated how this works
            if self.tebc_responsive_neurons[i]:
                cell_type = self.cell_types[i]
                response_func = response_profiles[cell_type]['response_func']
                tebc_response = response_func(time_since_CS, self.max_fr)

            task_firing_rates[i] = tebc_response

        return task_firing_rates






