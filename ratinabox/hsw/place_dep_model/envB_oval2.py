import numpy as np
from ratinabox.Environment import Environment
from ratinabox.Agent import Agent
from ratinabox.hsw import utils
from TEBCcells import TEBC
import cProfile
import pstats
import random
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from ratinabox.hsw.cell_builder import CellBuilder



#modeling environment B (oval)
#using equation from https://www.biorxiv.org/content/10.1101/2023.10.08.561112v1.full :
'''
Place and grid cell rate maps were generated from a real exploration trajectory using
the open source Python software RatInABox. The respective activity rates are then used
to train a logistic regressor to predict the real activity of each individual neurons.
To evaluate each model performance, we computed a F1 score for each neuron using
a place input model, which penalizes both incorrect classifications of active and inactive periods.
'''

#allows me to upload my own trajectory <-- I HAVE TO SCALE THIS
# Similar to EnvA, but with adjustments for EnvB dimensions and trajectory data


def simulate_envB(agent, position_data, responsive_distribution, tebc_responsive_neurons, percent_place_cells):
    PCs = CellBuilder.build_place_cells(agent)

    if isinstance(percent_place_cells, list):
        percent_place_cells = float(percent_place_cells[0])

    percent_to_zero_out = round(1 - percent_place_cells)
    num_elements_to_zero_out = int(PCs.n * percent_to_zero_out)

    # Randomly select indices to zero out
    indices_to_zero_out = random.sample(range(PCs.n), num_elements_to_zero_out)

    eyeblink_neurons = TEBC(agent, PCs.n, responsive_distribution, PCs.params, tebc_responsive_neurons)


    firing_rates = np.zeros((PCs.n, position_data.shape[1]))
    spikes = np.zeros((PCs.n, position_data.shape[1]))

    eyeblink_neurons.calculate_smoothed_velocity(position_data)

    # Initialize last CS and US times
    last_CS_time = None
    last_US_time = None

    times = position_data[0, :]
    trial_markers = position_data[3, :]

    coefficients = [-3.26092478e-04, 1.74074978e-02, 8.36619150e-02, 1.16059441]
    firing_rate_function = np.poly1d(coefficients)

    # Simulation loop
    for index, (current_time, trial_marker) in enumerate(zip(times, trial_markers)):

        agent.update()

        #figuring out place cell firing
        PCs.update()

        vel = eyeblink_neurons.smoothed_velocity[index];
        FR = np.array(PCs.history['firingrate'][-1])
        if vel < 0.02:
            place_firing = [.02/30] * PCs.n
            field_baseline = place_firing
        else:
            FR_mod = firing_rate_function(vel*100) #getting to cm/s
            place_firing = FR*(FR_mod/30) #converting per time stamp
            place_firing[indices_to_zero_out] = .02/30
#            if eyeblink_neurons.balance_distribution[0] != 100:
#                place_firing = (1 - eyeblink_neurons.balance_distribution) * place_firing
            field_baseline = place_firing



        #figuring out TEBC firing
        cs_present, us_present = utils.determine_cs_us(trial_marker)

        if cs_present:
            last_CS_time = current_time if last_CS_time is None else max(last_CS_time, current_time)

        time_since_CS = current_time - last_CS_time if last_CS_time is not None else -1
        tebc_firing = eyeblink_neurons.update_my_state(time_since_CS, index, field_baseline, FR)




        #combine
        firing_rates[:, index] = tebc_firing + place_firing  + np.random.normal(-0.02/30, 0.02/30) #this is per 1/30 seconds



    FR_MAX = utils.max_excluding_outliers(firing_rates)
    FR_MIN = 0
    cell_spikes = np.random.uniform(FR_MIN, FR_MAX, size=(firing_rates.shape)) < firing_rates
    spikes = cell_spikes.astype(int)
    return spikes, eyeblink_neurons, firing_rates, agent

