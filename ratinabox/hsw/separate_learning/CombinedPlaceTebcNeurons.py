import numpy as np
import pandas as pd
from ratinabox.Neurons import Neurons, PlaceCells
from tebc_response import response_profiles

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
class CombinedPlaceTebcNeurons(PlaceCells):
    default_params = dict()
    def __init__(self, agent, N, balance_value):
        # Define parameters for PlaceCells
        self.place_cells_N = N // 2 
        self.task_cells_N = N // 2
        place_cells_params = {
            "n": N,  # Number of place cells
            "description": "gaussian",  # Example parameter, adjust as needed
            "widths": 0.20,  # Adjust as needed
            "place_cell_centres": None,  # Adjust as needed
            "wall_geometry": "geodesic",  # Adjust as needed
            "min_fr": 0,  # Adjust as needed
            "max_fr": 1,  # Adjust as needed
            "save_history": True  # Save history for plotting
        }

        # Initialize PlaceCells with parameters
        super().__init__(agent, place_cells_params)

        # Initialize additional properties for CombinedPlaceTebcNeurons
        self.agent = agent
        self.cell_types = self.build_cell_types()

    def assign_tebc_responsiveness_and_types(self):
        cell_type_probs = [0.051, 0.032, 0.373, 0.155, 0.199, 0.050, 0.093, 0.047]
        cell_types = np.random.choice(range(1, 9), size=self.task_cells_N, p=cell_type_probs)
        return cell_types

    def update(self):
        # Ignore velocity modulation for now
        # place_response = 0  # Default value if velocity is below threshold or history not populated
        # tebc_response = 0

        # if self.agent.smoothed_velocity > 0.02:  # Velocity threshold is 2 cm/s
        #     place_response = self.firingrate[-1]

        super().update()

        task_firing_rates = np.zeros(self.task_cells_N)

        for i in range(self.task_cells_N):
            cell_type = self.cell_types[i]
            response_func = response_profiles[cell_type]['response_func']
            tebc_response = response_func(self.agent.time_since_cs)

            task_firing_rates = tebc_response


        
        self.save_to_history()

    def get_firing_rates(self):
        # Return the current firing rates of all neurons
        return self.firing_rates
