"""
Archived/unused functions from TEBC neuron classes.
Kept for reference but not actively called anywhere.
"""

import numpy as np


def calculate_firing_rate(neuron_obj, agent_position, time_since_CS, time_since_US, response_profiles):
    """
    Originally defined as NOT_CALLED_calculate_firing_rate on all TEBC/CombinedPlaceTebcNeurons classes.
    Never called in any simulation code.
    """
    firing_rates = np.zeros(neuron_obj.num_neurons)
    for i in range(neuron_obj.num_neurons):
        place_response = neuron_obj.firing_rates[i]  # Directly use the updated firing rates
        tebc_response = 0
        if neuron_obj.tebc_responsive_neurons[i]:
            cell_type = neuron_obj.cell_types[i]
            response_func = response_profiles[cell_type]['response_func']
            tebc_response = response_func(time_since_CS, time_since_US)
        firing_rates[i] = (1 - neuron_obj.balance_distribution[i]) * place_response + neuron_obj.balance_distribution[i] * tebc_response
        firing_rates[i] = neuron_obj.add_jitter_percentage(firing_rates[i])
    return firing_rates
