import numpy as np
import pandas as pd
import random
from ratinabox.Neurons import Neurons, PlaceCells
from tebc_response2 import *


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
    def __init__(self, agent, N, responsive_distribution, place_cells_params, tebc_responsive_neurons=None):
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

        self.agent = agent
        self.num_neurons = N
        self.firing_rates = np.zeros(N)
        self.responsive_distribution = responsive_distribution
        self.history = {'t': [], 'firingrate': [], 'spikes': []}

    def update_my_state(self, time_since_CS, baseline, in_field):
        current_velocity = self.agent.smoothed_velocity

        for i in range(self.num_neurons):
            if self.tebc_responsive_neurons[i]:
                ##for testing
                #in_field[i] = .4 #
                #baseline[i] = .2 #

                if (in_field[i] >= 0.2) and (current_velocity > 0.02): #in field running
                    tebc_response = type_one_response(time_since_CS, baseline[i])
                #    print("resp 1")
                if (in_field[i] < 0.2) and (current_velocity > 0.02): #out of field running
                    tebc_response = type_two_response(time_since_CS, baseline[i])
                #    print("resp 2")
                if (in_field[i] >= 0.2) and (current_velocity <= 0.02): #in field still
                    tebc_response = type_three_response(time_since_CS, baseline[i])
                #    print("resp 3")
                if (in_field[i] < 0.2) and (current_velocity <= 0.02): #out of field still
                    tebc_response = type_four_response(time_since_CS, baseline[i])
                #    print("resp 4")
            else:
                 tebc_response = baseline[i]

            self.firing_rates[i] = tebc_response-baseline[i]

        self.save_to_history()
        return self.firing_rates
