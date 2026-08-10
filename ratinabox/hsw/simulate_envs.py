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

# Gaussian place-field width scale. Field radius is scale * sqrt(env_area / num_place_cells)
# -- the linear size of the area each place cell would own if fields were evenly tiled --
# so fields shrink as place cells get denser (more cells and/or a smaller env) instead of
# staying fixed regardless of env size, which previously let a smaller env (B) pack the
# same-size fields tighter and run its spike generation hotter than env A (see bugs.md #6).
PLACE_FIELD_DENSITY_SCALE = 2


def place_cell_width_for(agent, num_neurons, percent_place_cells, scale=PLACE_FIELD_DENSITY_SCALE):
    """Gaussian place-field radius scaled to this agent's env area and place-cell density.

    One shared width for every place cell in the population -- not per-cell.
    """
    area = agent.Environment.boundary_polygon.area
    num_place_cells = max(utils.num_place_cells_for(num_neurons, percent_place_cells), 1)
    return scale * np.sqrt(area / num_place_cells)


def build_model(model_type, agent, num_neurons, percent_task_in_response_distribution, percent_task_responsive_cells_distribution, task_responsive_indices, percent_place_cells, cell_types, place_cell_width):
    tebc_cls = _TEBC_CLASS[model_type]
    if model_type == 'arousal_mediated':
        return tebc_cls(agent, num_neurons, percent_task_responsive_cells_distribution, percent_place_cells, task_responsive_indices, place_cell_width=place_cell_width)
    return tebc_cls(agent, num_neurons, percent_task_in_response_distribution, percent_task_responsive_cells_distribution, percent_place_cells, task_responsive_indices, cell_types, place_cell_width=place_cell_width)


def simulate_agent(model, agent):
    for _ in agent.follow_trajectory():
        model.update()
    firing_rates = np.array(model.history['firingrate']).T
    # Each history row is one utils.SIMULATION_STEP_SECONDS-wide bin (the simulation's
    # fixed ~30 Hz timestep -- see interpolate_position_data). Spike count per bin is a
    # Poisson draw with mean firing_rate * bin width: a non-negative integer, no longer
    # clipped to {0, 1} by a threshold, and no per-cell FR_MAX normalization needed since
    # a Poisson mean is well-defined at any firing rate. firing_rates can dip slightly
    # below zero near baseline (combined_place_tebc's additive noise term has a nonzero
    # negative mean, see bugs.md #5) -- clipped since a Poisson rate can't be negative.
    non_negative_firing_rates = np.clip(firing_rates, 0, None)
    spikes = np.random.poisson(non_negative_firing_rates * utils.SIMULATION_STEP_SECONDS)
    return spikes, firing_rates, agent


def simulate_experiment(model_type, position_data_envA, position_data_envB, num_neurons,
                            percent_task_in_response_value, percent_task_in_response_dist, percent_task_in_response_std,
                            percent_task_responsive_cells_val, percent_is_task_responsive_distribution, percent_place_cell,
                            holdover, task_types):
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
    place_cell_width_envA = place_cell_width_for(agentA, num_neurons, percent_place_cell)
    modelA = build_model(model_type, agentA, num_neurons, percent_task_in_response_distribution, percent_task_responsive_cells_distribution, task_responsive_indices, percent_place_cell, cell_types, place_cell_width_envA)
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
    place_cell_width_envB = place_cell_width_for(agentB, num_neurons, percent_place_cell)
    modelB = build_model(model_type, agentB, num_neurons, percent_task_in_response_distribution_B, percent_task_responsive_cells_distribution, task_responsive_indices_B, percent_place_cell, cell_types, place_cell_width_envB)
    spikesB, firingrate_envB, agentB = simulate_agent(modelB, agentB)

    return spikesA, firingrate_envA, agentA, spikesB, firingrate_envB, agentB
