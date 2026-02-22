import numpy as np
from ratinabox.Agent import Agent
from CombinedPlaceTebcNeurons import CombinedPlaceTebcNeurons
from ratinabox.hsw import utils
from ratinabox.hsw.environment_builder import build_rectangular_environment
from ratinabox.hsw.tebc_agent import TebcAgent

def simulate_agent(agent, position_data, balance_distribution, responsive_distribution):
    N = 80
    firing_rates = np.zeros((N, position_data.shape[1]))

    times = position_data[0]
    positions = position_data[1:3].T
    unique_times, indices = np.unique(times, return_index=True)
    unique_positions = positions[indices]

    agent.import_trajectory(times=unique_times, positions=unique_positions, interpolate=False)

    combined_neurons = CombinedPlaceTebcNeurons(agent, N, balance_distribution, responsive_distribution)

    for i, _ in enumerate(agent.follow_trajectory()):
        combined_neurons.update_state()

        firing_rates[:, i] = combined_neurons.get_firing_rates()

    return firing_rates, agent, combined_neurons


def simulate_envA(position_data, balance_distribution, responsive_distribution):
    # env_params = {
    #     'boundary': [[0, 0], [0, .6], [1.3, .6], [1.3, 0]],
    #     'boundary_conditions': 'solid'
    # }
    # env = Environment(params=env_params)
    envA = build_rectangular_environment(position_data[1:3].T)
    agent = TebcAgent(envA, position_data)
    return simulate_agent(agent, position_data, balance_distribution, responsive_distribution)


def simulate_envB(position_data, balance_distribution, responsive_distribution):
    # Parameters for oval shape
    # height_in_meters = 18 * 0.0254
    # width_in_meters = 26 * 0.0254
    # num_points = 100  # Number of points to define the oval

    # Create an oval-shaped boundary
    #boundary = [[width_in_meters / 2 * np.cos(theta), height_in_meters / 2 * np.sin(theta)] for theta in np.linspace(0, 2 * np.pi, num_points)]

    # env_params = {
    #     'boundary': [[0, 0], [0, .8], [.9, .8], [.9, 0]],
    #     'boundary_conditions': 'solid'
    # }
    # env = Environment(params=env_params)
    envB = build_rectangular_environment(position_data[1:3].T)
    agent = TebcAgent(envB, position_data)
    return simulate_agent(agent, position_data, balance_distribution, responsive_distribution)
