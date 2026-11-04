"""Place-dependent model: A->B task decoding R^2 across the swept parameter
grid. See decoding_task_heatmap_independent.py for the independent-model
equivalent and paper/figlib/panels/decoding.py for the shared panel code.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from paper.figlib.io import FigureInputs
from paper.figlib.panels.decoding import draw_task_transfer_heatmap_grid

FIGURE_ID = "decoding_task_heatmap_place_dependent"


def build(inputs: FigureInputs, style) -> plt.Figure:
    style.apply_rc_params()
    decoding = inputs.decoding["place_dependent_sweep_080726"]

    fig = plt.figure(figsize=(style.figure_width_inches("double"), 6.0), constrained_layout=True)
    draw_task_transfer_heatmap_grid(fig, decoding)
    fig.suptitle(f"{style.MODEL_DISPLAY_NAMES['place_dependent']} — task A→B decoding, tag={decoding.tag}")

    return fig
