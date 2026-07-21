import numpy as np

from ratinabox.hsw.combined_place_tebc import CombinedPlaceTebc
from ratinabox.hsw.dependent_model.tebc_response2 import response_profiles as RESPONSE_PROFILES

# Placeholder amplitude that drives the tEBC response of task-only cells, which
# have no place field to scale off of. Deliberately low; tune experimentally.
TASK_ONLY_BASELINE = 0.5


class TEBC(CombinedPlaceTebc):
    """Place-dependent model: the tEBC response amplitude is each cell's own place
    firing rate (place+task cells) or a small constant baseline (task-only cells)."""

    response_profiles = RESPONSE_PROFILES

    def __init__(self, *args, task_only_baseline=TASK_ONLY_BASELINE, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_only_baseline = task_only_baseline

    def _task_amplitudes(self, place_fr):
        return np.where(self.place_responsive_indices, place_fr, self.task_only_baseline)
