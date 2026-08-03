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

from hannahs_cebras import cond_decoding_AvsB, pos_decoding_AvsB, COND_CEBRA_DEFAULTS, POS_CEBRA_DEFAULTS, merge_cebra_params
from ratinabox.hsw import config
from ratinabox.hsw.simulate_envs import simulate_experiment
from ratinabox.hsw.simulation_helpers import filter_eyeblink_trials, filter_by_velocity, write_iteration_summary, write_run_header, write_cebra_config, unwrap_scalar, save_simulation_data

import args_parser

# Universal grid params apply to all models; model-specific params are added per model
_UNIVERSAL_GRID_PARAMS = ['percent_task_responsive_cells', 'percent_place_cells', 'holdovers']

MODEL_GRID_PARAMS = {
    'independent':      ['percent_task_in_response_values'] + _UNIVERSAL_GRID_PARAMS,
    'place_dependent':  ['percent_task_in_response_values'] + _UNIVERSAL_GRID_PARAMS,
    'arousal_mediated': _UNIVERSAL_GRID_PARAMS,
}

args = args_parser.parse()
cebra_params = args_parser.cebra_overrides(args)

save_directory = config.get_save_directory(model_name=args.model_type)
config.setup_ratinabox_figure_directory(save_directory)

current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
_experiment_prefix = f"{args.experiment}-" if args.experiment is not None else ""
_percent_task_in_response_tag = f"-percent_task_in_response-{args.percent_task_in_response_values}-{args.percent_task_in_response_dist}-std-{args.percent_task_in_response_std}" if args.percent_task_in_response_values is not None else ""
_task_types_tag = f"-tasktypes-[{'-'.join(map(str, args.task_types))}]" if args.task_types is not None else ""
_cebra_tag = args_parser.cebra_filename_tag(cebra_params)
results_file_base = os.path.join(save_directory, f"{_experiment_prefix}{current_date}:{args.model_type}_results{_percent_task_in_response_tag}-response-{args.percent_task_responsive_cells}-{args.percent_is_task_responsive_distribution}-PCs-{args.percent_place_cells}{_task_types_tag}{_cebra_tag}")
summary_filepath = f"{results_file_base}.log"
write_run_header(summary_filepath, vars(args))

effective_cebra_config = {}
if args.decode_task:
    effective_cebra_config['task_decoder'] = merge_cebra_params(COND_CEBRA_DEFAULTS, cebra_params)
if args.decode_position:
    effective_cebra_config['position_decoder'] = merge_cebra_params(POS_CEBRA_DEFAULTS, cebra_params)
write_cebra_config(summary_filepath, effective_cebra_config)

matlab_file_path = config.get_matlab_file_path()
data = scipy.io.loadmat(matlab_file_path)

position_data_envA = data['envA313_531']
position_data_envB = data['envB313_602']

num_neurons = 80

grid_param_names = MODEL_GRID_PARAMS[args.model_type]
grid_values = [getattr(args, p) for p in grid_param_names]

for combo in itertools.product(*grid_values):
    params = dict(zip(grid_param_names, combo))
    percent_task_in_response_value = params.get('percent_task_in_response_values')
    percent_task_responsive_cells_val = params['percent_task_responsive_cells']
    percent_place_cell = params['percent_place_cells']
    holdover = params['holdovers']
    print(params)
    for i in range(args.num_iters):
        spikesA, firingrate_envA, agentA, spikesB, firingrate_envB, agentB = simulate_experiment(
            args.model_type, position_data_envA, position_data_envB, num_neurons,
            percent_task_in_response_value, args.percent_task_in_response_dist, args.percent_task_in_response_std,
            percent_task_responsive_cells_val, args.percent_is_task_responsive_distribution, percent_place_cell,
            holdover, args.task_types,
        )

        # Assess learning transfer and other metrics
        response_envA = np.transpose(spikesA)
        response_envB = np.transpose(spikesB)

        response_envA_test, envA_eyeblink = filter_eyeblink_trials(agentA.position_data, response_envA)
        response_envB_test, envB_eyeblink = filter_eyeblink_trials(agentB.position_data, response_envB)

        #run cebra decoding
        if args.decode_task:
            task_a_to_a, task_a_to_b, task_shuffled_a_to_a, task_shuffled_a_to_b, task_b_to_b = cond_decoding_AvsB(response_envA_test, response_envB_test, envA_eyeblink, envB_eyeblink, cebra_params=cebra_params)
        else:
            task_a_to_a = task_a_to_b = task_shuffled_a_to_a = task_shuffled_a_to_b = task_b_to_b = None

        posA, response_envA = filter_by_velocity(agentA, response_envA)
        posB, response_envB = filter_by_velocity(agentB, response_envB)

        #POS DECODE
        if args.decode_position:
            place_a_to_a, place_a_to_b, place_shuffled_a_to_a, place_shuffled_a_to_b, place_b_to_b = pos_decoding_AvsB(response_envA, posA, response_envB, posB, .7, cebra_params=cebra_params)
        else:
            place_a_to_a = place_a_to_b = place_shuffled_a_to_a = place_shuffled_a_to_b = place_b_to_b = (None, None, None, None)

        # Construct the identifier for this iteration
        _percent_task_in_response_id = f"{percent_task_in_response_value}_{args.percent_task_in_response_dist}_" if percent_task_in_response_value is not None else ""
        identifier = f"{_percent_task_in_response_id}responsive_{percent_task_responsive_cells_val}_{args.percent_is_task_responsive_distribution}_PCs_{percent_place_cell}.npy"

        percent_place_cell = unwrap_scalar(percent_place_cell)
        task_a_to_a = unwrap_scalar(task_a_to_a)
        task_a_to_b = unwrap_scalar(task_a_to_b)
        task_shuffled_a_to_a = unwrap_scalar(task_shuffled_a_to_a)
        task_shuffled_a_to_b = unwrap_scalar(task_shuffled_a_to_b)
        task_b_to_b = unwrap_scalar(task_b_to_b)


        write_iteration_summary(
            summary_filepath, identifier,
            place_a_to_a, place_b_to_b, place_a_to_b,
            place_shuffled_a_to_a, place_shuffled_a_to_b,
            task_a_to_a, task_b_to_b, task_a_to_b, task_shuffled_a_to_a, task_shuffled_a_to_b,
        )

        current_date = datetime.datetime.now().strftime("%Y%m%d")
        _save_label = f"percent_task_in_response_{percent_task_in_response_value}_" if percent_task_in_response_value is not None else ""
        save_simulation_data(save_directory, spikesA, spikesB, firingrate_envA, firingrate_envB,
                                f"{_save_label}responsive_{percent_task_responsive_cells_val}_PC_{percent_place_cell}", i, current_date)


        del spikesA, spikesB, firingrate_envA, firingrate_envB
        del response_envA, response_envB
        del envA_eyeblink, envB_eyeblink

        # Call garbage collector
        gc.collect()

        #print(f"Saved results to {full_path_envA} and {full_path_envB}")

print(f"Saved results to {save_directory}")
