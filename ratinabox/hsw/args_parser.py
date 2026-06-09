import argparse

UNIVERSAL_PARAMS = ['model_type', 'num_iters', 'responsive_values', 'responsive_type', 'percent_place_cells', 'holdovers', 'decode_position', 'decode_task']

MODEL_REQUIRED_PARAMS = {
    'additive': ['balance_values', 'balance_dist', 'balance_std'],
    'dependent': ['balance_values', 'balance_dist', 'balance_std'],
    'place_dependent': [],
}

DEFAULTS = {
    'num_iters': 1,
    'responsive_values': '0.5',
    'responsive_type': 'fixed',
    'percent_place_cells': '0.7',
    'holdovers': '1',
    'balance_values': '0.5',
    'balance_dist': 'fixed',
    'balance_std': 0.1,
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
    parser.add_argument('--num_iters', type=int, default=DEFAULTS['num_iters'],
                        help='Number of iterations')
    parser.add_argument('--responsive_values', type=str, default=DEFAULTS['responsive_values'],
                        help='List of responsive rates or probabilities for distributions')
    parser.add_argument('--responsive_type', choices=['fixed', 'binomial', 'normal', 'poisson'], default=DEFAULTS['responsive_type'],
                        help='Type of distribution for responsive rate')
    parser.add_argument('--percent_place_cells', type=str, default=DEFAULTS['percent_place_cells'],
                        help='Percentage of place cells (single value or comma-separated list)')
    parser.add_argument('--holdovers', type=str, default=DEFAULTS['holdovers'],
                        help='Whether to hold TEBC cells over from env A')
    parser.add_argument('--decode_position', type=lambda x: x.lower() != 'false', default=True,
                        help='Run position decoding (default: True)')
    parser.add_argument('--decode_task', type=lambda x: x.lower() != 'false', default=True,
                        help='Run task/condition decoding (default: True)')

    # Balance params (additive, dependent only) — default=None so explicit passing is detectable
    parser.add_argument('--balance_values', type=str, default=None,
                        help='List of balance values or means for Gaussian distribution')
    parser.add_argument('--balance_dist', choices=['fixed', 'gaussian', 'additive'], default=None,
                        help='Distribution type for balance')
    parser.add_argument('--balance_std', type=float, default=None,
                        help='Standard deviation for Gaussian balance distribution')


def _validate_params(parser, args):
    supported = set(UNIVERSAL_PARAMS + MODEL_REQUIRED_PARAMS[args.model_type])
    unsupported = [p for p in vars(args) if p not in supported and getattr(args, p) is not None]
    if unsupported:
        parser.error(f"Model '{args.model_type}' does not support: {', '.join(f'--{p}' for p in unsupported)}")


def _set_defaults(args):
    for attr in MODEL_REQUIRED_PARAMS[args.model_type]:
        if getattr(args, attr) is None:
            setattr(args, attr, DEFAULTS[attr])

    for attr in ['balance_values', 'responsive_values', 'percent_place_cells', 'holdovers']:
        if getattr(args, attr) is not None:
            setattr(args, attr, parse_list(getattr(args, attr)))


def parse():
    parser = argparse.ArgumentParser(description='Simulation Script for Neuronal Firing Rate Analysis')
    _add_arguments(parser)
    args = parser.parse_args()
    _validate_params(parser, args)
    _set_defaults(args)
    return args
