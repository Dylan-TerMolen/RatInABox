import numpy as np

from ratinabox.hsw import utils
from ratinabox.hsw.independent_model.assign_tebc_types_and_responsiveness import assign_tebc_types_and_responsiveness
from ratinabox.hsw.independent_model.TEBC import TEBC as IndependentTEBC
from ratinabox.hsw.place_dependent_model.TEBC import TEBC as PlaceDependentTEBC
from ratinabox.hsw.arousal_mediated_model.TEBC import TEBC as ArousalMediatedTEBC
from ratinabox.hsw.simulation_helpers import build_agent

_TEBC_CLASS = {
    'independent': IndependentTEBC,
    'place_dependent': PlaceDependentTEBC,
    'arousal_mediated': ArousalMediatedTEBC,
}

# Gaussian place-field widths (metres), scaled per environment so env B's larger
# arena keeps the same field-to-spacing tiling as env A (0.20 * sqrt(areaB/areaA)).
PLACE_CELL_WIDTH_ENV_A = 0.20
PLACE_CELL_WIDTH_ENV_B = 0.40


def build_model(model_type, agent, balance_distribution, responsive_distribution, task_responsive_indices, percent_place_cells, cell_types, place_cell_width):
    tebc_cls = _TEBC_CLASS[model_type]
    if model_type == 'arousal_mediated':
        return tebc_cls(agent, 80, responsive_distribution, percent_place_cells, task_responsive_indices, place_cell_width=place_cell_width)
    return tebc_cls(agent, 80, balance_distribution, responsive_distribution, percent_place_cells, task_responsive_indices, cell_types, place_cell_width=place_cell_width)


def simulate_agent(model, agent):
    for _ in agent.follow_trajectory():
        model.update()
    firing_rates = np.array(model.history['firingrate']).T
    FR_MAX = utils.max_excluding_outliers(firing_rates)
    cell_spikes = np.random.uniform(0, FR_MAX, size=firing_rates.shape) < firing_rates
    spikes = cell_spikes.astype(int)
    return spikes, firing_rates, agent


def simulate_experiment(model_type, position_data_envA, position_data_envB, num_neurons,
                            balance_value, balance_dist, balance_std,
                            responsive_val, responsive_type, percent_place_cell,
                            holdover, task_types,
                            place_cell_width_envA=PLACE_CELL_WIDTH_ENV_A,
                            place_cell_width_envB=PLACE_CELL_WIDTH_ENV_B):
    """Simulate one (balance, responsive, percent_place_cells, holdover) grid
    combination across env A and env B.

    This is the exact body main.py runs per grid combination -- main.py calls
    this function rather than duplicating it, so the two can never drift apart.
    Stops short of decoding: returns everything the CEBRA decoders are handed,
    decoding itself excluded.
    """
    balance_distribution = utils.get_distribution_values(balance_dist, [balance_value, balance_std], num_neurons) if balance_value is not None else None
    responsive_distribution = utils.get_distribution_values(responsive_type, [responsive_val], num_neurons)

    task_responsive_indices, cell_types = assign_tebc_types_and_responsiveness(num_neurons, responsive_distribution, task_types)

    agentA = build_agent(position_data_envA)
    modelA = build_model(model_type, agentA, balance_distribution, responsive_distribution, task_responsive_indices, percent_place_cell, cell_types, place_cell_width_envA)
    spikesA, firingrate_envA, agentA = simulate_agent(modelA, agentA)

    # Holdover: carry learned env A params into env B; otherwise re-assign fresh params
    if holdover:
        balance_distribution_B = getattr(modelA, 'balance_distribution', balance_distribution)
        task_responsive_indices_B = modelA.task_responsive_indices
    else:
        balance_distribution_B = utils.get_distribution_values(balance_dist, [balance_value, balance_std], num_neurons) if balance_value is not None else None
        task_responsive_indices_B, cell_types = assign_tebc_types_and_responsiveness(num_neurons, responsive_distribution, task_types)

    agentB = build_agent(position_data_envB, env_shape='elliptical')
    modelB = build_model(model_type, agentB, balance_distribution_B, responsive_distribution, task_responsive_indices_B, percent_place_cell, cell_types, place_cell_width_envB)
    spikesB, firingrate_envB, agentB = simulate_agent(modelB, agentB)

    return spikesA, firingrate_envA, agentA, spikesB, firingrate_envB, agentB
