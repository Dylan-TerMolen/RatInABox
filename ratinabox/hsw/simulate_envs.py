import numpy as np

from ratinabox.hsw import utils
from ratinabox.hsw.independent_model.assign_tebc_types_and_responsiveness import assign_tebc_types_and_responsiveness, holdover_task_responsiveness
from ratinabox.hsw.independent_model.TEBC import TEBC as IndependentTEBC
from ratinabox.hsw.place_dependent_model.TEBC import TEBC as PlaceDependentTEBC
from ratinabox.hsw.arousal_mediated_model.TEBC import TEBC as ArousalMediatedTEBC
from ratinabox.hsw.simulation_helpers import build_agent

_TEBC_CLASS = {
    'independent': IndependentTEBC,
    'place_dependent': PlaceDependentTEBC,
    'arousal_mediated': ArousalMediatedTEBC,
}

# Gaussian place-field widths (metres). Matched across envs rather than scaled by
# area -- env B's bounding-box area is actually smaller than env A's, so scaling
# by sqrt(areaB/areaA) would shrink env B's width below env A's, not grow it.
PLACE_CELL_WIDTH_ENV_A = 0.20
PLACE_CELL_WIDTH_ENV_B = 0.20


def build_model(model_type, agent, percent_task_in_response_distribution, percent_task_responsive_cells_distribution, task_responsive_indices, percent_place_cells, cell_types, place_cell_width):
    tebc_cls = _TEBC_CLASS[model_type]
    if model_type == 'arousal_mediated':
        return tebc_cls(agent, 80, percent_task_responsive_cells_distribution, percent_place_cells, task_responsive_indices, place_cell_width=place_cell_width)
    return tebc_cls(agent, 80, percent_task_in_response_distribution, percent_task_responsive_cells_distribution, percent_place_cells, task_responsive_indices, cell_types, place_cell_width=place_cell_width)


def simulate_agent(model, agent):
    for _ in agent.follow_trajectory():
        model.update()
    firing_rates = np.array(model.history['firingrate']).T
    FR_MAX = utils.max_excluding_outliers(firing_rates)
    cell_spikes = np.random.uniform(0, FR_MAX, size=firing_rates.shape) < firing_rates
    spikes = cell_spikes.astype(int)
    return spikes, firing_rates, agent


def simulate_experiment(model_type, position_data_envA, position_data_envB, num_neurons,
                            percent_task_in_response_value, percent_task_in_response_dist, percent_task_in_response_std,
                            percent_task_responsive_cells_val, percent_is_task_responsive_distribution, percent_place_cell,
                            holdover, task_types,
                            place_cell_width_envA=PLACE_CELL_WIDTH_ENV_A,
                            place_cell_width_envB=PLACE_CELL_WIDTH_ENV_B):
    """Simulate one (percent_task_in_response, percent_task_responsive_cells, percent_place_cells, holdover) grid
    combination across env A and env B.

    This is the exact body main.py runs per grid combination -- main.py calls
    this function rather than duplicating it, so the two can never drift apart.
    Stops short of decoding: returns everything the CEBRA decoders are handed,
    decoding itself excluded.
    """
    percent_task_in_response_distribution = utils.get_distribution_values(percent_task_in_response_dist, [percent_task_in_response_value, percent_task_in_response_std], num_neurons) if percent_task_in_response_value is not None else None
    percent_task_responsive_cells_distribution = utils.get_distribution_values(percent_is_task_responsive_distribution, [percent_task_responsive_cells_val], num_neurons)

    task_responsive_indices, cell_types = assign_tebc_types_and_responsiveness(num_neurons, percent_task_responsive_cells_distribution, task_types)

    agentA = build_agent(position_data_envA)
    modelA = build_model(model_type, agentA, percent_task_in_response_distribution, percent_task_responsive_cells_distribution, task_responsive_indices, percent_place_cell, cell_types, place_cell_width_envA)
    spikesA, firingrate_envA, agentA = simulate_agent(modelA, agentA)

    # Holdover: `holdover` is the fraction of env A's task-responsive cells (same
    # indices + cell types) carried into env B; the rest of env B's target task-responsive
    # count is drawn fresh. holdover=0 draws B entirely fresh, holdover=1 carries over as
    # many of A's task-responsive cells as fit within B's target count.
    task_responsive_indices_B, cell_types = holdover_task_responsiveness(
        modelA.task_responsive_indices, cell_types, holdover, percent_task_responsive_cells_distribution, task_types)
    if holdover > 0:
        percent_task_in_response_distribution_B = getattr(modelA, 'percent_task_in_response_distribution', percent_task_in_response_distribution)
    else:
        percent_task_in_response_distribution_B = utils.get_distribution_values(percent_task_in_response_dist, [percent_task_in_response_value, percent_task_in_response_std], num_neurons) if percent_task_in_response_value is not None else None

    agentB = build_agent(position_data_envB, env_shape='elliptical')
    modelB = build_model(model_type, agentB, percent_task_in_response_distribution_B, percent_task_responsive_cells_distribution, task_responsive_indices_B, percent_place_cell, cell_types, place_cell_width_envB)
    spikesB, firingrate_envB, agentB = simulate_agent(modelB, agentB)

    return spikesA, firingrate_envA, agentA, spikesB, firingrate_envB, agentB
