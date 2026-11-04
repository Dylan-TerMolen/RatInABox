"""Supp (task_decoding_within): the within-environment (A->A) counterpart to
robustness.py's cross-environment (A->B) task-decoding grid -- same data,
same per-model axes, same shared color scale and header/body layout, just
direction="A->A" instead of "A->B" (2026-10-05 request: "show A->A task
decoding for each model in the same 3-d and 2-d views" as the existing A->B
pair). Placed directly after robustness_3d.py in the manifest so the four
task-decoding grid figures sit together: A->B 2D (robustness), A->B 3D
(robustness_3d), A->A 2D (this one), A->A 3D (task_decoding_within_3d).

Since A->A and B->B are the two within-environment directions and this
pipeline only ever computed a shuffled floor for "A->A" (not a separate
"B->B" one -- see decoding.py's DIRECTIONS/above_chance_fraction), A->A
stands in for within-environment task decoding generally here, same
convention decoding_task_summary/draw_direction_bars already use.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from paper.figlib.io import FigureInputs
from paper.figlib.panels.decoding import (
    above_chance_fraction, draw_model_row_header, draw_task_transfer_heatmap_grid, metric_range,
)

FIGURE_ID = "task_decoding_within"

# Same sweeps/axes as robustness.py.
_MODEL_AXES = {
    "independent": ("independent_sweep_092926", "percent_task_in_response", "percent_task_responsive_cells"),
    "place_dependent": ("place_dependent_sweep_092926", "percent_task_in_response", "percent_task_responsive_cells"),
    "arousal_mediated": ("arousal_mediated_sweep_092926", "percent_task_responsive_cells", "holdover"),
}
DIRECTION = "A->A"
DECODING_DESCRIPTION = "Decoding: task stage, A→A (within-environment)"


def build(inputs: FigureInputs, style) -> plt.Figure:
    style.apply_rc_params()
    decodings = {model: inputs.decoding[tag] for model, (tag, _, _) in _MODEL_AXES.items()}
    vmin, vmax = metric_range(*decodings.values(), direction=DIRECTION)

    # Same header/body subfigure split as robustness.py -- see its module
    # docstring for why.
    fig = plt.figure(figsize=(style.figure_width_inches("double"), 21))
    rows = fig.subfigures(3, 1, hspace=0.04)

    panel_axes = {}
    for row, model in zip(rows, _MODEL_AXES):
        _, x_param, y_param = _MODEL_AXES[model]
        decoding = decodings[model]
        header_fig, body_fig = row.subfigures(2, 1, height_ratios=[0.45, 2.4], hspace=0.01)
        panel_axes[model] = draw_task_transfer_heatmap_grid(
            body_fig, decoding, direction=DIRECTION, x_param=x_param, y_param=y_param,
            facet_param="percent_place_cells", vmin=vmin, vmax=vmax)
        fraction, n_combos = above_chance_fraction(decoding, direction=DIRECTION)
        stats_line = f"{style.BEATS_SHUFFLE_PHRASE} at {fraction * 100:.0f}% of {n_combos} grid points"
        draw_model_row_header(header_fig, style.MODEL_DISPLAY_NAMES[model], DECODING_DESCRIPTION, stats_line,
                               compact=True)

    # Named panels for build.py's per-panel export (build/panels/task_decoding_within/<name>.*).
    fig.panel_axes = panel_axes

    return fig
