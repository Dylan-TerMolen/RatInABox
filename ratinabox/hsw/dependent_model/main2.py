import sys

# Reconfigure stdout for immediate flushing
sys.stdout.reconfigure(line_buffering=True, write_through=True)

import argparse
import cProfile
import datetime
import gc
import itertools
import os
import pstats
import random
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import ratinabox
import scipy.io
import scipy.stats as stats
from ratinabox.Agent import Agent
from ratinabox.Environment import Environment

from hannahs_cebras import cond_decoding_AvsB, pos_decoding_self, pos_decoding_AvsB
from ratinabox.hsw import config
from ratinabox.hsw.dependent_model.assign_tebc_types_and_responsiveness import assign_tebc_types_and_responsiveness
from ratinabox.hsw.dependent_model.simulate_agent import simulate_agent

from ratinabox.hsw import utils
from ratinabox.hsw.environment_builder import build_rectangular_environment

"""
Simulation Script for Neuronal Firing Rate Analysis
Note: advise using a conda environment:
    conda create -n ratinabox python=3.9
    conda activate ratinabox
    conda install numpy
    conda install scipy
    conda install matplotlib
    export PYTHONPATH="${PYTHONPATH}:/Users/Hannah/Programming/RatInABox"
    pip install shapely

For cebra in env:
    conda install pytorch::pytorch torchvision torchaudio -c pytorch <-- or other, look at https://pytorch.org/
    pip install cebra


          - adjust the BALANCE PARAMETER to adjust how much each cell incorporates spatial vs tEBC data
          - adjust responsive_values that specifies the percentage of neurons that are responsive to tEBC signals.

Usage:
    python main.py [--balance_values BALANCE_VALUES] [--balance_dist BALANCE_DIST] [--balance_std BALANCE_STD]
                   [--responsive_values RESPONSIVE_VALUES] [--responsive_type RESPONSIVE_TYPE]

Arguments:
    --balance_values  : Comma-separated list of balance values or means for Gaussian distribution.
                        Example: --balance_values 0.3,0.5,0.7
                        If not provided, a default value of 0.5 is used.
    --balance_dist    : Specifies the type of distribution for the balance factor.
                        Options are 'fixed' and 'gaussian'.
                        Default is 'fixed'.
                        Additional options is 'additive' wherein place and  tebc get cumulatily added. this only makes
                        sense with a balace value of 1
    --balance_std     : Standard deviation for the Gaussian distribution of the balance factor.
                        Only used if --balance_dist is set to 'gaussian'.
                        Default value is 0.1.
    --responsive_values: Comma-separated list of responsive rates or probabilities for distributions.
                         Example: --responsive_values 0.4,0.6,0.8
                         If not provided, a default value of 0.5 is used.
    --responsive_type : Type of distribution for the responsive rate.
                        Options are 'fixed', 'binomial', 'normal', 'poisson'.
                        Default is 'fixed'.
    --percent_place_cells: what percent of place cells you want

Examples:


    python main2.py --balance_values 0.3,0.5,0.7 --balance_dist gaussian --balance_std 0.1 --responsive_values 0.4,0.6,0.8 --responsive_type binomial --percent_place_cells .7 --num_iters 1

    python main2.py --balance_values 0.3,0.5 --balance_dist gaussian --balance_std 0.5 --responsive_values 0.4,0.6 --responsive_type binomial --percent_place_cells .7 --num_iters 1

    python main2.py --balance_values 0.3 --balance_dist gaussian --balance_std 0.1 --responsive_values 0.4 --responsive_type binomial --percent_place_cells .7 --num_iters 1

    python main2.py --balance_values 0.5 --balance_dist fixed --responsive_values 0.5 --responsive_type fixed --percent_place_cells .7 --num_iters 1

    python main2.py --balance_values 0.5,0.7 --balance_dist fixed --responsive_values 0.5 --responsive_type fixed --percent_place_cells .7 --num_iters 1

    python main2.py --balance_values 0,.25,.5,.75,1 --balance_dist fixed --responsive_values .25,.5,.75,1 --responsive_type fixed --percent_place_cells 1,.85,.7,.55 --num_iters 1

    python main2.py --balance_values 1 --balance_dist additive --responsive_values 0.5 --responsive_type fixed --percent_place_cells .7 --num_iters 1 --optional_param work


Description:
    The script conducts simulations to evaluate how different configurations of balance factors and responsive rates affect neuronal firing patterns. Balance can be set as a fixed value or as a mean for a Gaussian distribution. The responsive rate determines the proportion of neurons responsive to tEBC signals and can be set as a fixed value or sampled from specified distributions.

    The script loads position data from a MATLAB file, performs simulations in two environments, and assesses learning transfer and spatial coding accuracy. The script supports a grid search over multiple balance and responsive rate values, allowing a comprehensive analysis of various parameter combinations. Results are printed to the console.

Requirements:
    - Ensure all necessary modules and custom classes are correctly imported and configured.
    - Replace 'path_to_your_matlab_file.mat' with the actual path to your MATLAB file.
    - Adjust environment settings and neuron parameters as needed in the script.
"""

# Combine argument parsing for SLURM and script-specific arguments
parser = argparse.ArgumentParser(description='Simulation Script for Neuronal Firing Rate Analysis')
parser.add_argument('--balance_values', type=str, default=[0.5], help='List of balance values or means for Gaussian distribution')
parser.add_argument('--balance_dist', choices=['fixed', 'gaussian', 'additive'], default='fixed', help='Distribution type for balance')
parser.add_argument('--balance_std', type=float, default=0.1, help='Standard deviation for Gaussian balance distribution')
parser.add_argument('--responsive_values', type=str, default=[0.5], help='List of responsive rates or probabilities for distributions')
parser.add_argument('--responsive_type', choices=['fixed', 'binomial', 'normal', 'poisson'], default='fixed', help='Type of distribution for responsive rate')
parser.add_argument('--percent_place_cells', type=str, default=[0.7], help='Percentage of place cells (single value or comma-separated list)')
parser.add_argument('--num_iters', type=int, default=1, help='Number of iterations')
parser.add_argument('--optional_param', type=str, help='Optional parameter for additional functionality')

args = parser.parse_args()

balance_values = utils.parse_list(args.balance_values)
responsive_values = utils.parse_list(args.responsive_values)
percent_place_cells = utils.parse_list(args.percent_place_cells)
optional_param = args.optional_param
num_iters = args.num_iters

# Determine if the optional parameter is provided
work = optional_param is not None

# Set up save directory using config
save_directory = config.get_save_directory(model_name='dependent', is_work=work)
config.setup_ratinabox_figure_directory(save_directory)

# Construct the filename
results_filename = f"DM_grid_search_results-balance-{args.balance_values}-{args.balance_dist}-std-{args.balance_std}-response-{args.responsive_values}-{args.responsive_type}-PCs-{args.percent_place_cells}.txt"
results_filepath = os.path.join(save_directory, results_filename)

# Load MATLAB file and extract position data
matlab_file_path = config.get_matlab_file_path(is_work=work)
data = scipy.io.loadmat(matlab_file_path)
position_data_envA = data['envA314_522']  # Adjust variable name as needed
position_data_envB = data['envB314_524']  # Adjust variable name as needed

# Set parameters
num_neurons = 80
balance_zero_done = False
responsive_zero_done = False


# Interpolate position data to uniform time steps
position_data_envA, desired_time_stepsA, interpolated_positions_envA = utils.interpolate_position_data(position_data_envA)
position_data_envB, desired_time_stepsB, interpolated_positions_envB = utils.interpolate_position_data(position_data_envB)

envA = build_rectangular_environment(position_data_envA[1:3].T)
envB = build_rectangular_environment(position_data_envB[1:3].T)

#boot up the agents
agentA = Agent(envA)
agentA.import_trajectory(times=desired_time_stepsA, positions=interpolated_positions_envA, interpolate=False)

agentB = Agent(envB)
agentB.import_trajectory(times=desired_time_stepsB, positions=interpolated_positions_envB, interpolate=False)

# Calculate the total number of runs
total_runs = len(balance_values) * len(responsive_values) * len(percent_place_cells) * num_iters
num_columns = 25  # Adjust this based on the number of parameters and metrics
results_matrix = np.zeros((total_runs, num_columns))

# Column headers
headers = [
    "balance_value", "responsive_val",
    "percent_place_cells", "fract_control_all", "fract_test_all",
    "err_allA_score", "err_allA_err", "err_allA_mean", "err_allA_median",
    "err_allB_usingA_score", "err_allB_usingA_err", "err_allB_usingA_mean", "err_allB_usingA_median",
    "err_all_shuffA_score", "err_all_shuffA_err", "err_all_shuffA_mean", "err_all_shuffA_median",
    "err_all_shuffB_usingA_score", "err_all_shuffB_usingA_err", "err_all_shuffB_usingA_mean", "err_all_shuffB_usingA_median",
    "err_allB_usingB_score", "err_allB_usingB_err", "err_allB_usingB_mean", "err_allB_usingB_median"
]


run_count = 0


# Perform grid search over balance and responsive rates
with open(results_filepath, "w") as results_file:
    for balance_value, responsive_val, percent_place_cell in itertools.product(balance_values, responsive_values, percent_place_cells):
        # Use balance_value, responsive_val, and percent_place_cell in your simulation
        # Skip redundant zero value iterations
        print(balance_value)
        print(responsive_val)
        print(percent_place_cell)
        for i in range(num_iters):

            balance_distribution = utils.get_distribution_values(args.balance_dist, [balance_value, args.balance_std], num_neurons)
            responsive_distribution = utils.get_distribution_values(args.responsive_type, [responsive_val], num_neurons)

            # Simulate in Environment A
            tebc_responsive_neurons, cell_types = assign_tebc_types_and_responsiveness(num_neurons, responsive_distribution)

            # Profile the function
            #cProfile.runctx('simulate_agent(agentA, position_data_envA, balance_distribution, responsive_distribution, tebc_responsive_neurons, cell_types)', globals(), locals(), 'profile_stats.prof')
            #p = pstats.Stats('profile_stats.prof')
            #p.sort_stats('cumulative').print_stats(10)

            # Now run the function normally to capture its output
            spikesA, eyeblink_neuronsA, firingrate_envA, agentA = simulate_agent(agentA, position_data_envA, balance_distribution, responsive_distribution, tebc_responsive_neurons, percent_place_cells, cell_types)
            # also want a percent of place cells metric


            balance_distribution_envA = eyeblink_neuronsA.balance_distribution
            tebc_responsive_rates_envA = eyeblink_neuronsA.tebc_responsive_neurons

            # Simulate in Environment B using the parameters from Environment A
            spikesB, eyeblink_neuronsB, firingrate_envB, agentB = simulate_agent(agentB, position_data_envB, balance_distribution_envA, tebc_responsive_rates_envA, tebc_responsive_neurons, percent_place_cells, cell_types)



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
            '''
            # Construct the full file paths
            filename_envA = f"DM_response_envA_balance_{balance_value}_{args.balance_dist}_responsive_{responsive_val}_{args.responsive_type}_perPCs_{percent_place_cell}.npy"
            filename_envB = f"DM_response_envB_balance_{balance_value}_{args.balance_dist}_responsive_{responsive_val}_{args.responsive_type}_perPCs_{percent_place_cell}.npy"
            full_path_envA = os.path.join(save_directory, filename_envA)
            full_path_envB = os.path.join(save_directory, filename_envB)

            # Save the response arrays to files
            #np.save(full_path_envA, spikesA)
            #np.save(full_path_envB, spikesB)
            np.save(full_path_envA, firingrate_envA)
            np.save(full_path_envB, firingrate_envB)
            ######
            '''

            # Assess learning transfer and other metrics
            #organize to run in cebra

            response_envA = np.transpose(spikesA)
            response_envB = np.transpose(spikesB)


            envA_eyeblink = position_data_envA[3].T
            response_envA_test = response_envA[envA_eyeblink > 0,:]
            envA_eyeblink = envA_eyeblink[envA_eyeblink > 0]
            envA_eyeblink = np.where(envA_eyeblink <= 5, 1, 2)

            envB_eyeblink = position_data_envB[3].T
            response_envB_test = response_envB[envB_eyeblink > 0,:]
            envB_eyeblink = envB_eyeblink[envB_eyeblink > 0]
            envB_eyeblink = np.where(envB_eyeblink <= 5, 1, 2)



            #run cebra decoding
            fract_control_all, fract_test_all = cond_decoding_AvsB(response_envA_test, response_envB_test, envA_eyeblink, envB_eyeblink)


            #run position decoding for env A
            posA = position_data_envA[1:3].T
            vel = eyeblink_neuronsA.smoothed_velocity
            vel= np.array(vel)
            indices = np.where(vel > 0.02)[0]
            posA = posA[indices]
            response_envA = response_envA[indices]
            #pos_test_scoreA, pos_test_errA, dis_meanA, dis_medianA, pos_test_score_shuffA, pos_test_err_shuffA, dis_mean_shuffA, dis_median_shuffA = pos_decoding_self(response_envA, posA, .70)


            #run position decoding for env B
            posB = position_data_envB[1:3].T
            vel = eyeblink_neuronsB.smoothed_velocity
            vel= np.array(vel)
            indices = np.where(vel > 0.02)[0]
            posB = posB[indices]
            response_envB = response_envB[indices]
            #pos_test_scoreB, pos_test_errB, dis_meanB, dis_medianB, pos_test_score_shuffB, pos_test_err_shuffB, dis_mean_shuffB, dis_median_shuffB = pos_decoding_self(response_envB, posB, .70)


            #POS DECODE
            err_allA, err_allB_usingA, err_all_shuffA, err_all_shuffB_usingA, err_allB_usingB = pos_decoding_AvsB(response_envA, posA, response_envB, posB, .7)



            # Construct the identifier for this iteration
            identifier = f"{balance_value}_{args.balance_dist}_responsive_{responsive_val}_{args.responsive_type}_PCs_{args.percent_place_cells}.npy"


            #make file types normal
            percent_place_cell = percent_place_cell[0] if isinstance(percent_place_cell, list) else percent_place_cell
            fract_control_all = fract_control_all[0] if isinstance(fract_control_all, list) else fract_control_all
            fract_test_all = fract_test_all[0] if isinstance(fract_test_all, list) else fract_test_all


            #Append the results to the file
            results_file.write(f"Parameters: {identifier}\n")
            results_file.write(f"fract_control_all: {fract_control_all}\n")
            results_file.write(f"fract_test_all: {fract_test_all}\n")
            results_file.write(f"pos decoding A: {err_allA}\n")
            results_file.write(f"pos decoding A shuffled: {err_all_shuffA}\n")
            results_file.write(f"pos decoding B using A: {err_allB_usingA}\n")
            results_file.write(f"pos decoding B shuffled: {err_all_shuffB_usingA}\n")
            results_file.write(f"pos decoding B: {err_allB_usingB}\n")
            results_file.write("\n")  # Add a newline for readability

            # Right before the problematic line

            # Attempt to assign to the matrix
            try:
                results_matrix[run_count] = [
                    balance_value, responsive_val, percent_place_cell,
                    fract_control_all, fract_test_all,
                    *err_allA, *err_allB_usingA, *err_all_shuffA, *err_all_shuffB_usingA, *err_allB_usingB
                ]
            except ValueError as e:
                print("Error occurred:", e)
                print([
                    balance_value, responsive_val, percent_place_cell,
                    fract_control_all, fract_test_all,
                    *err_allA, *err_allB_usingA, *err_all_shuffA, *err_all_shuffB_usingA, *err_allB_usingB
                ])

            # At the end of each iteration, explicitly delete large objects
            # Example: if `spikesA` and `spikesB` are large, you can delete them
            current_date = datetime.datetime.now().strftime("%Y%m%d")
            # When constructing filenames, prepend them with the save_directory path
            filename_spikesA = os.path.join(save_directory, f'spikesA_balance_{balance_value}_responsive_{responsive_val}_PC_{percent_place_cell}_iteration_{i}_{current_date}.csv')
            filename_spikesB = os.path.join(save_directory, f'spikesB_balance_{balance_value}_responsive_{responsive_val}_PC_{percent_place_cell}_iteration_{i}_{current_date}.csv')
            filename_firingrate_envA = os.path.join(save_directory, f'firingrate_envA_balance_{balance_value}_responsive_{responsive_val}_PC_{percent_place_cell}_iteration_{i}_{current_date}.csv')
            filename_firingrate_envB = os.path.join(save_directory, f'firingrate_envB_balance_{balance_value}_responsive_{responsive_val}_PC_{percent_place_cell}_iteration_{i}_{current_date}.csv')

            # Now save the dataframes to CSV in the specified directory
            pd.DataFrame(spikesA).to_csv(filename_spikesA, index=False)
            pd.DataFrame(spikesB).to_csv(filename_spikesB, index=False)
            pd.DataFrame(firingrate_envA).to_csv(filename_firingrate_envA, index=False)
            pd.DataFrame(firingrate_envB).to_csv(filename_firingrate_envB, index=False)

            del spikesA, spikesB, firingrate_envA, firingrate_envB
            del response_envA, response_envB
            del envA_eyeblink, envB_eyeblink

            # Call garbage collector
            gc.collect()
            run_count += 1

            # Print confirmation

            #print(f"Saved results to {full_path_envA} and {full_path_envB}")


# Get the current date
current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

results_filename = f"DM_results_matrix-balance-{args.balance_values}-{args.balance_dist}-std-{args.balance_std}-response-{args.responsive_values}-{args.responsive_type}-PCs-{args.percent_place_cells}"

# Construct filenames with the date and directory
csv_filename = os.path.join(save_directory, f"{results_filename}_{current_date}.csv")
npy_filename = os.path.join(save_directory, f"{results_filename}_{current_date}.npy")

# Saving the results matrix
np.savetxt(csv_filename, results_matrix, delimiter=",", header=",".join(headers), comments="")

# If you want to save in binary format (without headers)
np.save(npy_filename, results_matrix)

print(f"Saved results to {save_directory}")
