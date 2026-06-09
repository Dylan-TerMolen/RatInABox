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

from hannahs_cebras import cond_decoding_AvsB, pos_decoding_AvsB
from ratinabox.hsw import config
from ratinabox.hsw.additive_model.assign_tebc_types_and_responsiveness import assign_tebc_types_and_responsiveness
from ratinabox.hsw.additive_model.TEBC import TEBC as AdditiveTEBC
from ratinabox.hsw.dependent_model.TEBC import TEBC as DependentTEBC
from ratinabox.hsw.place_dep_model.TEBC import TEBC as PlaceDependentTEBC

from ratinabox.hsw import utils
from ratinabox.hsw.simulation_helpers import build_agent, filter_eyeblink_trials, filter_by_velocity, write_iteration_results, append_results_row, unwrap_scalar, save_simulation_data

import args_parser

_TEBC_CLASS = {
    'additive': AdditiveTEBC,
    'dependent': DependentTEBC,
    'place_dependent': PlaceDependentTEBC,
}

# Universal grid params apply to all models; model-specific params are added per model
_UNIVERSAL_GRID_PARAMS = ['responsive_values', 'percent_place_cells', 'holdovers']

MODEL_GRID_PARAMS = {
    'additive':        ['balance_values'] + _UNIVERSAL_GRID_PARAMS,
    'dependent':       ['balance_values'] + _UNIVERSAL_GRID_PARAMS,
    'place_dependent': _UNIVERSAL_GRID_PARAMS,
}

def build_model(model_type, agent, balance_distribution, responsive_distribution, tebc_responsive_neurons, percent_place_cells, cell_types):
    tebc_cls = _TEBC_CLASS[model_type]
    if model_type == 'place_dependent':
        return tebc_cls(agent, 80, responsive_distribution, percent_place_cells, tebc_responsive_neurons)
    return tebc_cls(agent, 80, balance_distribution, responsive_distribution, percent_place_cells, tebc_responsive_neurons, cell_types)


def simulate_agent(model, agent):
    for _ in agent.follow_trajectory():
        model.update()
    firing_rates = np.array(model.history['firingrate']).T
    FR_MAX = utils.max_excluding_outliers(firing_rates)
    cell_spikes = np.random.uniform(0, FR_MAX, size=firing_rates.shape) < firing_rates
    spikes = cell_spikes.astype(int)
    return spikes, firing_rates, agent

args = args_parser.parse()

save_directory = config.get_save_directory(model_name=args.model_type)
config.setup_ratinabox_figure_directory(save_directory)

current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
_balance_tag = f"-balance-{args.balance_values}-{args.balance_dist}-std-{args.balance_std}" if args.balance_values is not None else ""
results_file_base = os.path.join(save_directory, f"{current_date}:{args.model_type}_results{_balance_tag}-response-{args.responsive_values}-{args.responsive_type}-PCs-{args.percent_place_cells}")
results_filepath = f"{results_file_base}.txt"
csv_filepath = f"{results_file_base}.csv"

matlab_file_path = config.get_matlab_file_path()
data = scipy.io.loadmat(matlab_file_path)

position_data_envA = data['envA314_522']
position_data_envB = data['envB314_524']

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

num_neurons = 80

grid_param_names = MODEL_GRID_PARAMS[args.model_type]
grid_values = [getattr(args, p) for p in grid_param_names]

for combo in itertools.product(*grid_values):
    params = dict(zip(grid_param_names, combo))
    balance_value = params.get('balance_values')
    responsive_val = params['responsive_values']
    percent_place_cell = params['percent_place_cells']
    holdover = params['holdovers']
    print(params)
    for i in range(args.num_iters):
        balance_distribution = utils.get_distribution_values(args.balance_dist, [balance_value, args.balance_std], num_neurons) if balance_value is not None else None
        responsive_distribution = utils.get_distribution_values(args.responsive_type, [responsive_val], num_neurons)

        tebc_responsive_neurons, cell_types = assign_tebc_types_and_responsiveness(num_neurons, responsive_distribution)

        agentA = build_agent(position_data_envA)
        modelA = build_model(args.model_type, agentA, balance_distribution, responsive_distribution, tebc_responsive_neurons, percent_place_cell, cell_types)
        spikesA, firingrate_envA, agentA = simulate_agent(modelA, agentA)

        # Holdover: carry learned env A params into env B; otherwise re-assign fresh params
        if holdover:
            balance_distribution_B = getattr(modelA, 'balance_distribution', balance_distribution)
            tebc_responsive_neurons_B = modelA.tebc_responsive_neurons
        else:
            balance_distribution_B = utils.get_distribution_values(args.balance_dist, [balance_value, args.balance_std], num_neurons) if balance_value is not None else None
            tebc_responsive_neurons_B, cell_types = assign_tebc_types_and_responsiveness(num_neurons, responsive_distribution)

        agentB = build_agent(position_data_envB)
        modelB = build_model(args.model_type, agentB, balance_distribution_B, responsive_distribution, tebc_responsive_neurons_B, percent_place_cell, cell_types)
        spikesB, firingrate_envB, agentB = simulate_agent(modelB, agentB)

        # Assess learning transfer and other metrics
        response_envA = np.transpose(spikesA)
        response_envB = np.transpose(spikesB)

        response_envA_test, envA_eyeblink = filter_eyeblink_trials(agentA.position_data, response_envA)
        response_envB_test, envB_eyeblink = filter_eyeblink_trials(agentB.position_data, response_envB)

        #run cebra decoding
        if args.decode_task:
            fract_control_all, fract_test_all = cond_decoding_AvsB(response_envA_test, response_envB_test, envA_eyeblink, envB_eyeblink)
        else:
            fract_control_all, fract_test_all = None, None

        posA, response_envA = filter_by_velocity(agentA, response_envA)
        posB, response_envB = filter_by_velocity(agentB, response_envB)

        #POS DECODE
        if args.decode_position:
            err_allA, err_allB_usingA, err_all_shuffA, err_all_shuffB_usingA, err_allB_usingB = pos_decoding_AvsB(response_envA, posA, response_envB, posB, .7)
        else:
            err_allA = err_allB_usingA = err_all_shuffA = err_all_shuffB_usingA = err_allB_usingB = (None, None, None, None)

        # Construct the identifier for this iteration
        _balance_id = f"{balance_value}_{args.balance_dist}_" if balance_value is not None else ""
        identifier = f"{_balance_id}responsive_{responsive_val}_{args.responsive_type}_PCs_{percent_place_cell}.npy"

        percent_place_cell = unwrap_scalar(percent_place_cell)
        fract_control_all = unwrap_scalar(fract_control_all)
        fract_test_all = unwrap_scalar(fract_test_all)


        write_iteration_results(
            results_filepath, identifier, fract_control_all, fract_test_all,
            err_allA, err_all_shuffA, err_allB_usingA, err_all_shuffB_usingA, err_allB_usingB,
        )

        append_results_row(
            csv_filepath, headers,
            [balance_value, responsive_val, percent_place_cell,
             fract_control_all, fract_test_all,
             *err_allA, *err_allB_usingA, *err_all_shuffA, *err_all_shuffB_usingA, *err_allB_usingB]
        )

        current_date = datetime.datetime.now().strftime("%Y%m%d")
        _save_label = f"balance_{balance_value}_" if balance_value is not None else ""
        save_simulation_data(save_directory, spikesA, spikesB, firingrate_envA, firingrate_envB,
                                f"{_save_label}responsive_{responsive_val}_PC_{percent_place_cell}", i, current_date)


        del spikesA, spikesB, firingrate_envA, firingrate_envB
        del response_envA, response_envB
        del envA_eyeblink, envB_eyeblink

        # Call garbage collector
        gc.collect()

        #print(f"Saved results to {full_path_envA} and {full_path_envB}")

print(f"Saved results to {save_directory}")
