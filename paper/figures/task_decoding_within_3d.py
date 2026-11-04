"""Supp (task_decoding_within_3d): the 3D-surface version of
task_decoding_within.py's grid -- same relationship robustness_3d.py already
has to robustness.py, now for direction="A->A" instead of "A->B" (2026-10-05
request: "show A->A task decoding for each model in the same 3-d and 2-d
views" as the existing A->B pair). Same per-model axes, shared z/color
scale, and header/body layout as robustness_3d.py -- see that module's
docstring for the header-layout history (the compact=True split it settled
on after the non-compact mode turned out not to work for a 3-line header).
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from paper.figlib.io import FigureInputs
from paper.figlib.panels.decoding import (
    above_chance_fraction, draw_metric_surface_facets, draw_model_row_header, metric_range,
)

FIGURE_ID = "task_decoding_within_3d"

# Same sweeps/axes as robustness_3d.py.
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
    base_label = (
        f"Task-stage decoding accuracy ({style.direction_display_name(DIRECTION)}, {style.CHANCE_LABEL.lower()})")

    # Same generous per-panel budget as robustness_3d.py -- see its own comment.
    fig = plt.figure(figsize=(16.5, 22.5))
    rows = fig.subfigures(3, 1, hspace=0.03)

    panel_axes = {}
    for row, model in zip(rows, _MODEL_AXES):
        _, x_param, y_param = _MODEL_AXES[model]
        decoding = decodings[model]
        header_fig, body_fig = row.subfigures(2, 1, height_ratios=[0.5, 3.0], hspace=0.01)
        panel_axes[model] = draw_metric_surface_facets(
            body_fig, decoding, direction=DIRECTION, x_var=x_param, y_var=y_param,
            facet_var="percent_place_cells", vmin=vmin, vmax=vmax, metric_label=base_label)
        fraction, n_combos = above_chance_fraction(decoding, direction=DIRECTION)
        stats_line = f"{style.BEATS_SHUFFLE_PHRASE} at {fraction * 100:.0f}% of {n_combos} grid points"
        draw_model_row_header(header_fig, style.MODEL_DISPLAY_NAMES[model], DECODING_DESCRIPTION, stats_line,
                               compact=True)

    # Named panels for build.py's per-panel export (build/panels/task_decoding_within_3d/<name>.*).
    fig.panel_axes = panel_axes

    return fig
