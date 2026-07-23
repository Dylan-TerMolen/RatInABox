import numpy as np
from ratinabox.hsw import utils
from ratinabox.hsw.arousal_mediated_model.TEBC import TEBC
import random
from ratinabox.hsw.cell_builder import CellBuilder


def simulate_agent(agent, position_data, responsive_distribution, tebc_responsive_neurons, percent_place_cells):
    tebc = TEBC(agent, 80, responsive_distribution, percent_place_cells, tebc_responsive_neurons)

    for _ in agent.follow_trajectory():
        tebc.update()

    firing_rates = np.array(tebc.history['firingrate']).T
    FR_MAX = utils.max_excluding_outliers(firing_rates)
    FR_MIN = 0
    cell_spikes = np.random.uniform(FR_MIN, FR_MAX, size=(firing_rates.shape)) < firing_rates
    spikes = cell_spikes.astype(int)
    return spikes, tebc, firing_rates, agent

