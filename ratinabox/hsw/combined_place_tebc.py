import random

import numpy as np

from ratinabox.Neurons import PlaceCells

# Near-silent floor for cells with no place field and/or no task drive.
BASELINE_FR = 0.02 / 30


class CombinedPlaceTebc(PlaceCells):
    """Place + tEBC neurons split into four groups by two independent properties:
    carrying a place field (percent_place_cells) and being tEBC-responsive.

        place-only  : spatial firing only
        place+task  : spatial firing blended with the tEBC response by `balance`
        task-only   : tEBC response only (no place field)
        silent      : neither (baseline)

    Only place-responsive cells receive field centres, distributed evenly across
    the environment for their own count so thinning the place population leaves no
    spatial dead zones.

    Subclasses supply the model's `response_profiles` and define how the tEBC
    response amplitude is chosen per cell via `_task_amplitudes` — the one axis on
    which the additive and place-dependent models differ.
    """

    default_params = dict()
    response_profiles = None  # set by each subclass

    def __init__(self, agent, N, task_to_place_weight_distribution, task_responsive_distribution, percent_place_cells,
                 task_responsive_indices=None, cell_types=None, place_cell_width=0.20):
        place_cells_params = {
            "n": N,
            "description": "gaussian",
            "widths": place_cell_width,
            "place_cell_centres": None,
            "wall_geometry": "geodesic",
            "min_fr": 0,
            "max_fr": 12,
            "save_history": False,
        }
        super().__init__(agent, place_cells_params)

        self.agent = agent
        self.task_to_place_weight_distribution = np.asarray(task_to_place_weight_distribution, dtype=float)
        self.task_responsive_distribution = task_responsive_distribution
        self.task_responsive_indices = self._as_bool_mask(task_responsive_indices)
        self.cell_types = cell_types if cell_types is not None else np.full(N, False)

        self.place_responsive_indices = self._build_place_responsive_mask(percent_place_cells)
        self._distribute_place_centres()
        self._set_category_masks()

    def _as_bool_mask(self, values):
        if values is None:
            return np.full(self.n, False)
        return np.asarray(values, dtype=bool)

    def _build_place_responsive_mask(self, percent_place_cells):
        """Randomly choose which cells carry a place field (round(N * percent))."""
        if isinstance(percent_place_cells, list):
            percent_place_cells = float(percent_place_cells[0])
        num_place = int(round(self.n * percent_place_cells))
        mask = np.full(self.n, False)
        mask[random.sample(range(self.n), num_place)] = True
        return mask

    def _distribute_place_centres(self):
        """Evenly tile field centres across the environment for the place-responsive cells only."""
        num_place = np.count_nonzero(self.place_responsive_indices)
        if num_place == 0:
            return
        self.place_cell_centres[self.place_responsive_indices] = self.agent.Environment.sample_positions(
            n=num_place, method="uniform_jitter")

    def _set_category_masks(self):
        self.place_only = self.place_responsive_indices & ~self.task_responsive_indices
        self.place_task = self.place_responsive_indices & self.task_responsive_indices
        self.task_only = ~self.place_responsive_indices & self.task_responsive_indices

    def update(self):
        super().update()
        place_fr = self._place_firing_rate()
        task_fr = self._task_firing_rate(place_fr)
        self.firingrate = self._combine_by_category(place_fr, task_fr)
        self.firingrate += np.random.normal(-0.02 / 30, 0.02 / 30)
        self.save_to_history()

    def _place_firing_rate(self):
        """Velocity-modulated place firing; cells without a field sit at baseline."""
        coefficients = [-3.26092478e-04, 1.74074978e-02, 8.36619150e-02, 1.16059441]
        firing_rate_function = np.poly1d(coefficients)
        vel = self.agent.smoothed_velocity

        if vel < 0.02:
            place_fr = np.full(self.n, BASELINE_FR)
        else:
            place_fr = self.firingrate * (firing_rate_function(vel * 100) / 30)
        place_fr[~self.place_responsive_indices] = BASELINE_FR
        return place_fr

    def _task_firing_rate(self, place_fr):
        """Evaluate each responsive cell's tEBC profile at its per-cell amplitude."""
        task_fr = np.zeros(self.n)
        amplitudes = self._task_amplitudes(place_fr)
        time_since_cs = self.agent.time_since_cs
        for i in np.flatnonzero(self.task_responsive_indices):
            response_func = self.response_profiles[self.cell_types[i]]["response_func"]
            task_fr[i] = response_func(time_since_cs, amplitudes[i])
        return task_fr

    def _task_amplitudes(self, place_fr):
        """Per-cell tEBC response amplitude. Overridden by each model."""
        raise NotImplementedError

    def _combine_by_category(self, place_fr, task_fr):
        """Place-only -> place, task-only -> task, place+task -> balance blend, silent -> baseline."""
        firingrate = np.full(self.n, BASELINE_FR)
        firingrate[self.place_only] = place_fr[self.place_only]
        firingrate[self.task_only] = task_fr[self.task_only]
        mixed = self.place_task
        balance = self.task_to_place_weight_distribution
        firingrate[mixed] = balance[mixed] * task_fr[mixed] + (1 - balance[mixed]) * place_fr[mixed]
        return firingrate
