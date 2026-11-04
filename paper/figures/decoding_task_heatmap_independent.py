"""Independent model: A->B task decoding R^2 across the swept parameter grid
(percent_task_in_response x percent_task_responsive_cells, faceted by
percent_place_cells; holdover was fixed at 1.0 for this sweep). Heatmap
styling ported from scripts/pull_and_plot_holdover_sweep.py -- see
paper/figlib/panels/decoding.py.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from paper.figlib.io import FigureInputs
from paper.figlib.panels.decoding import draw_task_transfer_heatmap_grid

FIGURE_ID = "decoding_task_heatmap_independent"


def build(inputs: FigureInputs, style) -> plt.Figure:
    style.apply_rc_params()
    decoding = inputs.decoding["independent_sweep_092926"]

    fig = plt.figure(figsize=(style.figure_width_inches("double"), 6.0), constrained_layout=True)
    draw_task_transfer_heatmap_grid(fig, decoding)
    fig.suptitle(f"{style.MODEL_DISPLAY_NAMES['independent']} — task A→B decoding, tag={decoding.tag}")

    return fig
