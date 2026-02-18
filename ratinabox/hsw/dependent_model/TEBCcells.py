import numpy as np
import pandas as pd
import random
from ratinabox.Neurons import Neurons, PlaceCells
from tebc_response2 import response_profiles

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
combined_neurons = CombinedPlaceTebcNeurons(num_neurons, place_cells, balance, tebc_responsive_rate)

'''


class TEBC(PlaceCells):
    default_params = dict()  # Add this line to define the default_params attribute
    def __init__(self, agent, N, balance_distribution, responsive_distribution, place_cells_params, tebc_responsive_neurons=None, cell_types=None):
        super().__init__(agent, place_cells_params)

        # Define parameters for PlaceCells
        place_cells_params = {
            "n": N,  # Number of place cells
            "description": "gaussian",  # Example parameter, adjust as needed
            "widths": 0.20,  # Adjust as needed
            "place_cell_centres": None,  # Adjust as needed
            "wall_geometry": "geodesic",  # Adjust as needed
            "min_fr": 0,  # Adjust as needed
            "max_fr": 12,  # Adjust as needed
            "save_history": False  # Save history for plotting -- dont think this done anything
        }

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
        self.num_neurons = N
        self.balance_distribution = balance_distribution
        self.responsive_distribution = responsive_distribution
        self.firing_rates = np.zeros(N)
        self.history = {'t': [], 'firingrate': [], 'spikes': []}

    def update_my_state(self, time_since_CS, current_index, baseline):
        # Check the current smoothed velocity
        current_velocity = self.smoothed_velocity[current_index] if current_index < len(self.smoothed_velocity) else 0


        for i in range(self.num_neurons):
            tebc_response = 0
            if self.tebc_responsive_neurons[i]:
                cell_type = self.cell_types[i]
                response_func = response_profiles[cell_type]['response_func']
                tebc_response = response_func(time_since_CS, baseline[i])


            if self.balance_distribution[0] == 100:
                self.firing_rates[i] = tebc_response
            else:
                self.firing_rates[i] = (self.balance_distribution[i] * tebc_response)


        self.save_to_history()
        return self.firing_rates


    def get_firing_rates(self):
        # Return the current firing rates of all neurons
        return self.firing_rates

    def add_jitter_percentage(self, value, jitter_percentage=10):
        jitter_amount = value * (jitter_percentage / 100)
        jitter = random.uniform(-jitter_amount, jitter_amount)
        return value + jitter
