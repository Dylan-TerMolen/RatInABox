import sys

# Reconfigure stdout for immediate flushing
sys.stdout.reconfigure(line_buffering=True, write_through=True)

import argparse
import datetime
import gc
import os
import numpy as np
import scipy.io

from hannahs_cebras import cond_decoding_AvsB, pos_decoding_AvsB
from ratinabox.hsw import config
from ratinabox.hsw.additive_model.assign_tebc_types_and_responsiveness import assign_tebc_types_and_responsiveness
from ratinabox.hsw.additive_model.simulate_agent import simulate_agent

from ratinabox.hsw import utils
from ratinabox.hsw.simulation_helpers import build_agent, filter_eyeblink_trials, filter_by_velocity, write_iteration_results, unwrap_scalar, save_simulation_data


# Parse command-line arguments
parser = argparse.ArgumentParser(description='Half-and-half simulation: 50% pure place cells, 50% pure TEBC cells')
parser.add_argument('--num_iters', type=int, default=1, help='optional parameter for number of iterations')

args = parser.parse_args()

num_iters = args.num_iters

# Set up save directory using config
save_directory = config.get_save_directory(model_name='additive')
config.setup_ratinabox_figure_directory(save_directory)

# Construct the filename
results_filename = f"AM_half_half_results.txt"
results_filepath = os.path.join(save_directory, results_filename)

# Load MATLAB file and extract position data
matlab_file_path = config.get_matlab_file_path()
data = scipy.io.loadmat(matlab_file_path)

# Set parameters
num_neurons = 80
place_N = num_neurons // 2
tebc_N = num_neurons - place_N
percent_place_cell = 0.5

position_data_envA = data['envA314_522']
position_data_envB = data['envB314_524']

# Calculate the total number of runs
total_runs = num_iters
num_columns = 25
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

balance_distribution = np.array([0.0] * place_N + [1.0] * tebc_N)
responsive_distribution = np.array([0.0] * place_N + [1.0] * tebc_N)

for i in range(num_iters):
    tebc_responsive_neurons, cell_types = assign_tebc_types_and_responsiveness(num_neurons, responsive_distribution)

    agentA = build_agent(position_data_envA)
    agentB = build_agent(position_data_envB)

    spikesA, eyeblink_neuronsA, firingrate_envA, agentA = simulate_agent(agentA, position_data_envA, balance_distribution, responsive_distribution, tebc_responsive_neurons, percent_place_cell, cell_types)

    balance_distribution_envA = eyeblink_neuronsA.balance_distribution
    tebc_responsive_rates_envA = eyeblink_neuronsA.tebc_responsive_neurons

    # Simulate in Environment B using the parameters from Environment A
    spikesB, eyeblink_neuronsB, firingrate_envB, agentB = simulate_agent(agentB, position_data_envB, balance_distribution_envA, tebc_responsive_rates_envA, tebc_responsive_neurons, percent_place_cell, cell_types)

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

    # Assess learning transfer and other metrics
    response_envA = np.transpose(spikesA)
    response_envB = np.transpose(spikesB)

    response_envA_test, envA_eyeblink = filter_eyeblink_trials(agentA.position_data, response_envA)
    response_envB_test, envB_eyeblink = filter_eyeblink_trials(agentB.position_data, response_envB)

    #run cebra decoding
    fract_control_all, fract_test_all, _, _, _ = cond_decoding_AvsB(response_envA_test, response_envB_test, envA_eyeblink, envB_eyeblink)

    posA, response_envA = filter_by_velocity(agentA, response_envA)
    posB, response_envB = filter_by_velocity(agentB, response_envB)

    #POS DECODE
    err_allA, err_allB_usingA, err_all_shuffA, err_all_shuffB_usingA, err_allB_usingB = pos_decoding_AvsB(response_envA, posA, response_envB, posB, .7)

    # Construct the identifier for this iteration
    identifier = f"half_half_PCs_{percent_place_cell}.npy"

    fract_control_all = unwrap_scalar(fract_control_all)
    fract_test_all = unwrap_scalar(fract_test_all)

    write_iteration_results(
        results_filepath, identifier, fract_control_all, fract_test_all,
        err_allA, err_all_shuffA, err_allB_usingA, err_all_shuffB_usingA, err_allB_usingB,
    )

    try:
        results_matrix[run_count] = [
            0.5, 0.5, percent_place_cell,
            fract_control_all, fract_test_all,
            *err_allA, *err_allB_usingA, *err_all_shuffA, *err_all_shuffB_usingA, *err_allB_usingB
        ]

    except ValueError as e:
        print("Error occurred:", e)
        print([
            0.5, 0.5, percent_place_cell,
            fract_control_all, fract_test_all,
            *err_allA, *err_allB_usingA, *err_all_shuffA, *err_all_shuffB_usingA, *err_allB_usingB
        ])

    current_date = datetime.datetime.now().strftime("%Y%m%d")
    save_simulation_data(save_directory, spikesA, spikesB, firingrate_envA, firingrate_envB,
                            f"half_half_PC_{percent_place_cell}", i, current_date)

    del spikesA, spikesB, firingrate_envA, firingrate_envB
    del response_envA, response_envB
    del envA_eyeblink, envB_eyeblink

    # Call garbage collector
    gc.collect()
    run_count += 1

# Get the current date
current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Construct filenames with the date and directory
results_filename = f"AM_half_half_results_matrix"

csv_filename = os.path.join(save_directory, f"{results_filename}_{current_date}.csv")
npy_filename = os.path.join(save_directory, f"{results_filename}_{current_date}.npy")

# Saving the results matrix
np.savetxt(csv_filename, results_matrix, delimiter=",", header=",".join(headers), comments="")

# If you want to save in binary format (without headers)
np.save(npy_filename, results_matrix)

print(f"Saved results to {save_directory}")
