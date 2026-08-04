import argparse

# CEBRA hyperparameters exposed to the CLI. Each maps to a CEBRA constructor kwarg
# (the 'cebra_' prefix stripped) and defaults to None so an unset value falls back
# to the decoder's tuned default rather than overriding it.
CEBRA_PARAMS = [
    'cebra_learning_rate', 'cebra_max_iterations', 'cebra_output_dimension',
    'cebra_min_temperature', 'cebra_temperature_mode', 'cebra_time_offsets',
    'cebra_num_hidden_units', 'cebra_batch_size', 'cebra_model_architecture',
    'cebra_distance', 'cebra_conditional',
]

UNIVERSAL_PARAMS = ['model_type', 'experiment', 'num_iters', 'percent_task_responsive_cells', 'percent_is_task_responsive_distribution', 'percent_place_cells', 'holdovers', 'decode_position', 'decode_task', 'task_types'] + CEBRA_PARAMS

MODEL_REQUIRED_PARAMS = {
    'independent': ['percent_task_in_response_values', 'percent_task_in_response_dist', 'percent_task_in_response_std'],
    'place_dependent': ['percent_task_in_response_values', 'percent_task_in_response_dist', 'percent_task_in_response_std'],
    'arousal_mediated': [],
}

DEFAULTS = {
    'num_iters': 1,
    'percent_task_responsive_cells': '0.5',
    'percent_is_task_responsive_distribution': 'fixed',
    'percent_place_cells': '0.7',
    'holdovers': '1',
    'percent_task_in_response_values': '0.5',
    'percent_task_in_response_dist': 'fixed',
    'percent_task_in_response_std': 0.1,
}


# TODO: deprecate utils.parse_list once separate_learning/main.py is updated to use args_parser
def parse_list(arg_value):
    if isinstance(arg_value, list):
        return [float(val) for val in arg_value]
    if isinstance(arg_value, float) or isinstance(arg_value, int):
        return [arg_value]
    if ',' in arg_value:
        return [float(item) for item in arg_value.split(',')]
    else:
        return [float(arg_value)]

def _add_arguments(parser):
    parser.add_argument('--model_type', choices=list(MODEL_REQUIRED_PARAMS), required=True,
                        help='Which model to run')

    # Universal
    parser.add_argument('--experiment', type=str, default=None,
                        help='Experiment tag prepended to every output filename so all runs '
                             'from the same experiment share a common prefix.')
    parser.add_argument('--num_iters', type=int, default=DEFAULTS['num_iters'],
                        help='Number of iterations')
    parser.add_argument('--percent_task_responsive_cells', type=str, default=DEFAULTS['percent_task_responsive_cells'],
                        help='List of responsive rates or probabilities for distributions')
    parser.add_argument('--percent_is_task_responsive_distribution', choices=['fixed', 'binomial', 'normal', 'poisson'], default=DEFAULTS['percent_is_task_responsive_distribution'],
                        help='Type of distribution for responsive rate')
    parser.add_argument('--percent_place_cells', type=str, default=DEFAULTS['percent_place_cells'],
                        help='Percentage of place cells (single value or comma-separated list)')
    parser.add_argument('--holdovers', type=str, default=DEFAULTS['holdovers'],
                        help='Fraction (0-1) of env A task-responsive cells to carry into env B '
                             'by identity and cell type; env B\'s remaining task-responsive slots '
                             '(up to its own target count) are drawn fresh. 0 = fully fresh, 1 = '
                             'carry over as many of A\'s task-responsive cells as fit.')
    parser.add_argument('--task_types', type=str, default=None,
                        help='Comma-separated subset of tEBC response types to use, e.g. "1,2,7,8". '
                             'Default: all types at their empirical prevalence. '
                             'Has no effect for --model_type arousal_mediated: that model selects '
                             'its response function from in-field/running state, not cell_types.')
    parser.add_argument('--decode_position', type=lambda x: x.lower() != 'false', default=True,
                        help='Run position decoding (default: True)')
    parser.add_argument('--decode_task', type=lambda x: x.lower() != 'false', default=True,
                        help='Run task/condition decoding (default: True)')

    # Percent-task-in-response params (independent, place_dependent only) — default=None so explicit passing is detectable
    parser.add_argument('--percent_task_in_response_values', type=str, default=None,
                        help='List of percent-task-in-response values or means for Gaussian distribution')
    parser.add_argument('--percent_task_in_response_dist', choices=['fixed', 'gaussian', 'additive'], default=None,
                        help='Distribution type for percent task in response')
    parser.add_argument('--percent_task_in_response_std', type=float, default=None,
                        help='Standard deviation for Gaussian percent-task-in-response distribution')

    _add_cebra_arguments(parser)


def _add_cebra_arguments(parser):
    """CEBRA hyperparameters for the decoding grid search.

    All default to None: an unset flag leaves the position and task decoders on
    their own tuned defaults, while a passed value overrides both.
    """
    parser.add_argument('--cebra_learning_rate', type=float, default=None,
                        help='CEBRA learning rate')
    parser.add_argument('--cebra_max_iterations', type=int, default=None,
                        help='CEBRA training iterations')
    parser.add_argument('--cebra_output_dimension', type=int, default=None,
                        help='CEBRA embedding dimensionality')
    parser.add_argument('--cebra_min_temperature', type=float, default=None,
                        help='CEBRA minimum temperature (used with temperature_mode=auto)')
    parser.add_argument('--cebra_temperature_mode', choices=['auto', 'constant'], default=None,
                        help='CEBRA temperature mode')
    parser.add_argument('--cebra_time_offsets', type=int, default=None,
                        help='CEBRA time offsets')
    parser.add_argument('--cebra_num_hidden_units', type=int, default=None,
                        help='CEBRA hidden units per layer')
    parser.add_argument('--cebra_batch_size', type=int, default=None,
                        help='CEBRA batch size')
    parser.add_argument('--cebra_model_architecture', type=str, default=None,
                        help='CEBRA model architecture, e.g. offset10-model')
    parser.add_argument('--cebra_distance', choices=['cosine', 'euclidean'], default=None,
                        help='CEBRA distance metric')
    parser.add_argument('--cebra_conditional', type=str, default=None,
                        help='CEBRA conditional distribution, e.g. time_delta')


def cebra_overrides(args):
    """Map explicitly-set --cebra_* CLI args to CEBRA constructor kwargs.

    Returns a dict keyed by CEBRA parameter name (the 'cebra_' prefix stripped),
    containing only values the user actually passed so unset parameters keep each
    decoder's tuned default.
    """
    prefix = 'cebra_'
    return {
        name[len(prefix):]: getattr(args, name)
        for name in CEBRA_PARAMS
        if getattr(args, name) is not None
    }


# Short filename abbreviations for the CEBRA overrides, keyed by the prefix-stripped
# parameter name returned by cebra_overrides.
_CEBRA_TAG_ABBREV = {
    'learning_rate': 'lr',
    'max_iterations': 'iters',
    'output_dimension': 'dim',
    'min_temperature': 'mintemp',
    'temperature_mode': 'tmode',
    'time_offsets': 'toff',
    'num_hidden_units': 'hidden',
    'batch_size': 'batch',
    'model_architecture': 'arch',
    'distance': 'dist',
    'conditional': 'cond',
}


def cebra_filename_tag(cebra_params):
    """Compress the passed CEBRA overrides into a compact filename tag.

    Returns e.g. "-cebra-[lr0.0003_dim2]" so runs with different CEBRA configs
    land in separate files. Empty string when no overrides were passed (all
    decoders on their tuned defaults).
    """
    if not cebra_params:
        return ""
    parts = [f"{_CEBRA_TAG_ABBREV.get(name, name)}{value}" for name, value in cebra_params.items()]
    return f"-cebra-[{'_'.join(parts)}]"


def _validate_params(parser, args):
    supported = set(UNIVERSAL_PARAMS + MODEL_REQUIRED_PARAMS[args.model_type])
    unsupported = [p for p in vars(args) if p not in supported and getattr(args, p) is not None]
    if unsupported:
        parser.error(f"Model '{args.model_type}' does not support: {', '.join(f'--{p}' for p in unsupported)}")


def _set_defaults(args):
    for attr in MODEL_REQUIRED_PARAMS[args.model_type]:
        if getattr(args, attr) is None:
            setattr(args, attr, DEFAULTS[attr])

    for attr in ['percent_task_in_response_values', 'percent_task_responsive_cells', 'percent_place_cells', 'holdovers']:
        if getattr(args, attr) is not None:
            setattr(args, attr, parse_list(getattr(args, attr)))

    if args.task_types is not None:
        args.task_types = [int(t) for t in str(args.task_types).split(',')]


def parse():
    parser = argparse.ArgumentParser(description='Simulation Script for Neuronal Firing Rate Analysis')
    _add_arguments(parser)
    args = parser.parse_args()
    _validate_params(parser, args)
    _set_defaults(args)
    return args
