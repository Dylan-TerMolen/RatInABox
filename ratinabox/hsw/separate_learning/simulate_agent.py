import numpy as np
from ratinabox.Agent import Agent
from CombinedPlaceTebcNeurons import CombinedPlaceTebcNeurons
from ratinabox.hsw import utils
from ratinabox.hsw.environment_builder import build_elliptical_environment, build_rectangular_environment
from ratinabox.hsw.tebc_agent import TebcAgent

def simulate_agent(agent, position_data, balance_value):
    N = 80
    firing_rates = np.zeros((N, position_data.shape[1]))

    times = position_data[0]
    positions = position_data[1:3].T
    unique_times, indices = np.unique(times, return_index=True)
    unique_positions = positions[indices]

    agent.import_trajectory(times=unique_times, positions=unique_positions, interpolate=False)

    combined_neurons = CombinedPlaceTebcNeurons(agent, N, balance_value)

    for i, _ in enumerate(agent.follow_trajectory()):
        combined_neurons.update_state()

        firing_rates[:, i] = combined_neurons.get_firing_rates()

    return firing_rates, agent, combined_neurons


def simulate_envA(position_data, balance_value):
    # env_params = {
    #     'boundary': [[0, 0], [0, .6], [1.3, .6], [1.3, 0]],
    #     'boundary_conditions': 'solid'
    # }
    # env = Environment(params=env_params)
    envA = build_rectangular_environment(position_data[1:3].T)
    agent = TebcAgent(envA, position_data)
    return simulate_agent(agent, position_data, balance_value)


def simulate_envB(position_data, balance_value):
    envB = build_elliptical_environment(position_data[1:3].T)
    agent = TebcAgent(envB, position_data)
    return simulate_agent(agent, position_data, balance_value)
