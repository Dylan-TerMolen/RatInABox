import sys

# Reconfigure stdout for immediate flushing
sys.stdout.reconfigure(line_buffering=True, write_through=True)

import argparse
import datetime
import gc
import itertools
import os
import matplotlib.pyplot as plt
import numpy as np
import scipy.io

from hannahs_cebras import cond_decoding_AvsB, pos_decoding_self, pos_decoding_AvsB
from ratinabox.hsw import config
from ratinabox.hsw.place_dep_model.assign_tebc_types_and_responsiveness import assign_tebc_types_and_responsiveness
from ratinabox.hsw.place_dep_model.simulate_agent import simulate_agent
from ratinabox.hsw.simulation_helpers import (
    build_agent, filter_eyeblink_trials,
    filter_by_velocity, write_iteration_results,
    append_results_row, save_simulation_data, unwrap_scalar,
)

from ratinabox.hsw import utils


# Parse command-line arguments
parser = argparse.ArgumentParser(description='Simulation Script for Neuronal Firing Rate Analysis')
parser.add_argument('--responsive_values', type=str, default=0.5, help='List of responsive rates or probabilities for distributions')
parser.add_argument('--responsive_type', choices=['fixed', 'binomial', 'normal', 'poisson'], default='fixed', help='Type of distribution for responsive rate')
parser.add_argument('--percent_place_cells', type=str, default=0.7, help='Percentage of place cells (single value or comma-separated list)')
parser.add_argument('--holdovers', type=str, default=1, help='if you want TEBC cells held over from env A')
parser.add_argument('--num_iters', type=int, default=1, help='optional parameter for number of iterations')
args = parser.parse_args()

# Process the arguments
responsive_values = utils.parse_list(args.responsive_values)
percent_place_cells = utils.parse_list(args.percent_place_cells)
holdovers = utils.parse_list(args.holdovers)
num_iters = args.num_iters

# Set up save directory using config
save_directory = config.get_save_directory(model_name='place_dependent')
config.setup_ratinabox_figure_directory(save_directory)

# Construct the filename
current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
results_file_base = os.path.join(save_directory, f"{current_date}:PDM_results-response-{args.responsive_values}-{args.responsive_type}-PCs-{args.percent_place_cells}")
results_filepath = f"{results_file_base}.txt"
csv_filepath = f"{results_file_base}.csv"

# Load MATLAB file and extract position data
matlab_file_path = config.get_matlab_file_path()
data = scipy.io.loadmat(matlab_file_path)
# Set parameters
num_neurons = 80

position_data_envA = data['envA314_522']
agentA = build_agent(position_data_envA)

position_data_envB = data['envB314_524']
agentB = build_agent(position_data_envB)

# Column headers
headers = [
    "responsive_val",
    "percent_place_cells", "fract_control_all", "fract_test_all",
    "err_allA_score", "err_allA_err", "err_allA_mean", "err_allA_median",
    "err_allB_usingA_score", "err_allB_usingA_err", "err_allB_usingA_mean", "err_allB_usingA_median",
    "err_all_shuffA_score", "err_all_shuffA_err", "err_all_shuffA_mean", "err_all_shuffA_median",
    "err_all_shuffB_usingA_score", "err_all_shuffB_usingA_err", "err_all_shuffB_usingA_mean", "err_all_shuffB_usingA_median",
    "err_allB_usingB_score", "err_allB_usingB_err", "err_allB_usingB_mean", "err_allB_usingB_median"
]




# Perform grid search over balance and responsive rates
for responsive_val, percent_place_cell, holdover in itertools.product(responsive_values, percent_place_cells, holdovers):
    # Use balance_value, responsive_val, and percent_place_cell in your simulation
    # Skip redundant zero value iterations
    print(responsive_val)
    print(percent_place_cell)
    if holdover == 1:
        print("holdovers on")
        args.holdover_type = "on"
    else:
        print("holdovers off")
        args.holdover_type = "off"

    for i in range(num_iters):
        #balance_distribution = utils.get_distribution_values(args.balance_dist, [balance_value, args.balance_std], num_neurons)
        responsive_distribution = utils.get_distribution_values(args.responsive_type, [responsive_val], num_neurons)

        #Simulate in Environment A
        tebc_responsive_neurons = assign_tebc_types_and_responsiveness(num_neurons, responsive_distribution)

        # Profile the function
        #cProfile.runctx('simulate_agent(agentA, position_data_envA, responsive_distribution, tebc_responsive_neurons, percent_place_cells)', globals(), locals(), 'profile_stats.prof')
        #p = pstats.Stats('profile_stats.prof')
        #p.sort_stats('cumulative').print_stats(10)

        # Now run the function normally to capture its output
        agentA = build_agent(position_data_envA)
        agentB = build_agent(position_data_envB)

        spikesA, eyeblink_neuronsA, firingrate_envA, agentA = simulate_agent(agentA, position_data_envA, responsive_distribution, tebc_responsive_neurons, percent_place_cell)
        # also want a percent of place cells metric

        if holdover == 1:
            tebc_responsive_neurons = eyeblink_neuronsA.responsive_distribution
        else:
            tebc_responsive_neurons = assign_tebc_types_and_responsiveness(num_neurons, responsive_distribution)

        # Simulate in Environment B using the parameters from Environment A
        spikesB, eyeblink_neuronsB, firingrate_envB, agentB = simulate_agent(agentB, position_data_envB, responsive_distribution, tebc_responsive_neurons, percent_place_cell)



        ###PLOTTING
        '''
        ratinabox.autosave_plots = True
        ratinabox.stylize_plots()
        plt.show()
        agentA.plot_trajectory()
        plt.show()
        agentA.plot_position_heatmap()
        plt.show()
        agentA.plot_histogram_of_speeds()
        plt.show()
        agentB.plot_histogram_of_speeds()
        plt.show()
        combined_neuronsA.plot_rate_timeseries()
        plt.show()
        combined_neuronsA.plot_rate_map()
        plt.show()
        combined_neuronsA.plot_place_cell_locations()
        plt.show()
        '''




        #####save
        # Construct the full file paths
        filename_envA = f"PDM_response_envA_responsive_{responsive_val}_{args.responsive_type}_perPCs_{percent_place_cell}_holdovers_{args.holdover_type}.npy"
        filename_envB = f"PDM_response_envB_responsive_{responsive_val}_{args.responsive_type}_perPCs_{percent_place_cell}_holdovers_{args.holdover_type}.npy"
        full_path_envA = os.path.join(save_directory, filename_envA)
        full_path_envB = os.path.join(save_directory, filename_envB)
        # Save the response arrays to files


        #np.save(full_path_envA, spikesA)
        #np.save(full_path_envB, spikesB)

        np.save(full_path_envA, firingrate_envA)
        np.save(full_path_envB, firingrate_envB)

        ######

        # Assess learning transfer and other metrics
        #organize to run in cebra
        response_envA = np.transpose(spikesA)
        response_envB = np.transpose(spikesB)

        response_envA_test, envA_eyeblink = filter_eyeblink_trials(agentA.position_data, response_envA)
        response_envB_test, envB_eyeblink = filter_eyeblink_trials(agentB.position_data, response_envB)

        #run cebra decoding
        fract_control_all, fract_test_all = cond_decoding_AvsB(response_envA_test, response_envB_test, envA_eyeblink, envB_eyeblink)

        posA, response_envA = filter_by_velocity(agentA, response_envA)
        posB, response_envB = filter_by_velocity(agentB, response_envB)


        #POS DECODE
        err_allA, err_allB_usingA, err_all_shuffA, err_all_shuffB_usingA, err_allB_usingB = pos_decoding_AvsB(response_envA, posA, response_envB, posB, .7)

        # Construct the identifier for this iteration
        identifier = f"responsive_{responsive_val}_{args.responsive_type}_PCs_{args.percent_place_cells}.npy"


        percent_place_cell = unwrap_scalar(percent_place_cell)
        fract_control_all = unwrap_scalar(fract_control_all)
        fract_test_all = unwrap_scalar(fract_test_all)


        write_iteration_results(
            results_filepath, identifier, fract_control_all, fract_test_all,
            err_allA, err_all_shuffA, err_allB_usingA, err_all_shuffB_usingA, err_allB_usingB,
        )

        append_results_row(
            csv_filepath, headers,
            [responsive_val, percent_place_cell,
             fract_control_all, fract_test_all,
             *err_allA, *err_allB_usingA, *err_all_shuffA, *err_all_shuffB_usingA, *err_allB_usingB]
        )



        current_date = datetime.datetime.now().strftime("%Y%m%d")
        save_simulation_data(save_directory, spikesA, spikesB, firingrate_envA, firingrate_envB,
                                f"responsive_{responsive_val}_PC_{percent_place_cell}", i, current_date)

        # At the end of each iteration, explicitly delete large objects
        # Example: if `spikesA` and `spikesB` are large, you can delete them
        del spikesA, spikesB, firingrate_envA, firingrate_envB
        del response_envA, response_envB
        del envA_eyeblink, envB_eyeblink

        # Call garbage collector
        gc.collect()

        #print(f"Saved results to {full_path_envA} and {full_path_envB}")

print(f"Saved results to {save_directory}")
 