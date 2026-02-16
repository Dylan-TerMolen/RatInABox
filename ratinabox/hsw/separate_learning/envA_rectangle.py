import numpy as np
from ratinabox.Environment import Environment
from ratinabox.Agent import Agent
from CombinedPlaceTebcNeurons import CombinedPlaceTebcNeurons
from ratinabox.hsw import utils

def simulate_envA(position_data, balance_distribution, responsive_distribution):
    # Define environment parameters for a rectangular environment
    env_params = {
        # 'boundary': [[0, 0], [0, 20 * 0.0254], [31 * 0.0254, 20 * 0.0254], [31 * 0.0254, 0]],
        'boundary': [[0, 0], [0, .6], [1.3, .6], [1.3, 0]],
        'boundary_conditions': 'solid'
    }
    env = Environment(params=env_params)

    # Create an agent in the environment
    agent = Agent(env)

    # Number of neurons
    N = 80
    firing_rates = np.zeros((N, position_data.shape[1]))

    # Import trajectory into the agent
    times = position_data[0]  # Timestamps
    positions = position_data[1:3].T  # Positions (x, y)

    # Check min/max of position data
    print(f"Position data range: x=[{positions[:, 0].min():.2f}, {positions[:, 0].max():.2f}], y=[{positions[:, 1].min():.2f}, {positions[:, 1].max():.2f}]")
    print(f"Environment extent: x=[0, 1.3], y=[0, 0.6]")

    # Check for and handle duplicate timestamps
    unique_times, indices = np.unique(times, return_index=True)
    unique_positions = positions[indices]

    # Import trajectory into the agent
    agent.import_trajectory(times=unique_times, positions=unique_positions)


    # Create CombinedPlaceTebcNeurons with the environment
    combined_neurons = CombinedPlaceTebcNeurons(agent, N, balance_distribution, responsive_distribution)
    combined_neurons.calculate_smoothed_velocity(position_data)

    # Initialize last CS and US times
    last_CS_time = None
    last_US_time = None

    # Simulation loop
    for index in range(unique_positions.shape[0]):
        # Current timestamp
        current_time = unique_times[index]

        # Update the agent
        agent.update()

        # Determine if CS or US is present
        trial_marker = position_data[3, index]
        cs_present, us_present = utils.determine_cs_us(trial_marker)

        # Update last CS/US time if necessary
        if cs_present and (last_CS_time is None or times[index] > last_CS_time):
            last_CS_time = times[index]
        if us_present and (last_US_time is None or times[index] > last_US_time):
            last_US_time = times[index]

        # Calculate time since CS and US
        time_since_CS = times[index] - last_CS_time if last_CS_time is not None else -1
        time_since_US = times[index] - last_US_time if last_US_time is not None else -1

        # Retrieve the agent's current position from the history
        agent_position = agent.history['pos'][index]

        # Update neuron states
        combined_neurons.update_state(agent_position, time_since_CS, time_since_US, index)

        # Store firing rates
        firing_rates[:, index] = combined_neurons.get_firing_rates()

    # Return the firing rates for further analysis
    return firing_rates, agent, combined_neurons
