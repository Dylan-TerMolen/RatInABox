import numpy as np
from ratinabox.Environment import Environment
from ratinabox.Agent import Agent
from CombinedPlaceTebcNeurons import CombinedPlaceTebcNeurons
from ratinabox.hsw import utils


def simulate_agent(agent, position_data, balance_distribution, responsive_distribution):
    N = 80
    firing_rates = np.zeros((N, position_data.shape[1]))

    times = position_data[0]
    positions = position_data[1:3].T
    unique_times, indices = np.unique(times, return_index=True)
    unique_positions = positions[indices]

    agent.import_trajectory(times=unique_times, positions=unique_positions)

    combined_neurons = CombinedPlaceTebcNeurons(agent, N, balance_distribution, responsive_distribution)
    combined_neurons.calculate_smoothed_velocity(position_data)

    last_CS_time = None
    last_US_time = None

    for index in range(unique_positions.shape[0]):
        current_time = unique_times[index]

        agent.update()

        trial_marker = position_data[3, index]
        cs_present, us_present = utils.determine_cs_us(trial_marker)

        if cs_present and (last_CS_time is None or times[index] > last_CS_time):
            last_CS_time = times[index]
        if us_present and (last_US_time is None or times[index] > last_US_time):
            last_US_time = times[index]

        time_since_CS = times[index] - last_CS_time if last_CS_time is not None else -1
        time_since_US = times[index] - last_US_time if last_US_time is not None else -1

        agent_position = agent.history['pos'][index]

        combined_neurons.update_state(agent_position, time_since_CS, time_since_US, index)

        firing_rates[:, index] = combined_neurons.get_firing_rates()

    return firing_rates, agent, combined_neurons


def simulate_envA(position_data, balance_distribution, responsive_distribution):
    env_params = {
        'boundary': [[0, 0], [0, .6], [1.3, .6], [1.3, 0]],
        'boundary_conditions': 'solid'
    }
    env = Environment(params=env_params)
    agent = Agent(env)
    return simulate_agent(agent, position_data, balance_distribution, responsive_distribution)


def simulate_envB(position_data, balance_distribution, responsive_distribution):
    # Parameters for oval shape
    height_in_meters = 18 * 0.0254
    width_in_meters = 26 * 0.0254
    num_points = 100  # Number of points to define the oval

    # Create an oval-shaped boundary
    #boundary = [[width_in_meters / 2 * np.cos(theta), height_in_meters / 2 * np.sin(theta)] for theta in np.linspace(0, 2 * np.pi, num_points)]

    env_params = {
        'boundary': [[0, 0], [0, .8], [.9, .8], [.9, 0]],
        'boundary_conditions': 'solid'
    }
    env = Environment(params=env_params)
    agent = Agent(env)
    return simulate_agent(agent, position_data, balance_distribution, responsive_distribution)
