import argparse
import itertools
import os

import matplotlib.pyplot as plt
import numpy as np
import ratinabox
import scipy.io

from ratinabox.hsw import config, utils
from ratinabox.hsw.separate_learning.simulate_agent import simulate_envA, simulate_envB


# Set up save directory using config
save_directory = config.get_save_directory(model_name='separate_learning')
config.setup_ratinabox_figure_directory(save_directory)

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Simulation Script for Neuronal Firing Rate Analysis')
parser.add_argument('--percent_task_responsive_cells', type=utils.parse_list, help='List of responsive rates or probabilities for distributions')
args = parser.parse_args()

# Load MATLAB file and extract position data
matlab_file_path = config.get_matlab_file_path()
data = scipy.io.loadmat(matlab_file_path)
position_data_envA = data['envA313_531']  # Adjust variable name as needed
position_data_envB = data['envB313_602']  # Adjust variable name as needed

# Set parameters
num_neurons = 80
percent_task_responsive_cells = utils.parse_list(args.percent_task_responsive_cells) if args.percent_task_responsive_cells else [0.5]

# Perform grid search over percent-task-in-response and responsive rates
for responsive_val in itertools.product(percent_task_responsive_cells):
    response_envA, agentA, combined_neuronsA = simulate_envA(position_data_envA, responsive_val)
    response_envB, agentB, combined_neuronsB = simulate_envB(position_data_envB, responsive_val)

    ratinabox.autosave_plots = True
    extent = agentA.Environment.extent
    aspect = (extent[1] - extent[0]) / (extent[3] - extent[2])
    fig, ax = plt.subplots(figsize=(6 * aspect, 6))
    agentA.plot_trajectory(t_end=120, fig=fig, ax=ax)
    ratinabox.stylize_plots()


    ###PLOTTING
    '''
    agentA.plot_position_heatmap()
    agentA.plot_histogram_of_speeds()
    combined_neuronsA.plot_rate_timeseries()
    combined_neuronsA.plot_rate_map()
    combined_neuronsA.plot_place_cell_locations()
    '''

    # Construct the full file paths
    filename_envA = f"response_envA_balance_{balance_value}_{args.balance_dist}_responsive_{responsive_val}_{args.responsive_type}.npy"
    filename_envB = f"response_envB_balance_{balance_value}_{args.balance_dist}_responsive_{responsive_val}_{args.responsive_type}.npy"
    full_path_envA = os.path.join(save_directory, filename_envA)
    full_path_envB = os.path.join(save_directory, filename_envB)

    # Save the response arrays to files
    np.save(full_path_envA, response_envA)
    np.save(full_path_envB, response_envB)

    # Print confirmation
    print(f"Saved results to {full_path_envA} and {full_path_envB}")

    # Assess learning transfer and other metrics
    #similarity_score = assess_learning_transfer(response_envA, response_envB, balance_value, responsive_val)
    #print(f"Balance: {balance_value}, Responsive Rate: {responsive_val}, Learning Transfer: {similarity_score}")
