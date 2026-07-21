import numpy as np

from ratinabox.hsw.combined_place_tebc import CombinedPlaceTebc
from ratinabox.hsw.additive_model.tebc_response2 import response_profiles as RESPONSE_PROFILES


class TEBC(CombinedPlaceTebc):
    """Additive model: every responsive cell's tEBC response uses a fixed amplitude
    (max_fr), independent of its place firing."""

    response_profiles = RESPONSE_PROFILES

    def _task_amplitudes(self, place_fr):
        return np.full(self.n, self.max_fr)
