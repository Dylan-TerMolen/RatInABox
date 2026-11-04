"""In-task counterpart to place_robustness_3d_within.py -- same model/
sweep/axis setup, place_cm_in_task instead of place_cm_out_of_task. Not
registered in manifest.yaml (2026-10-02 request: build for review only; add
it to the manifest if asked to explicitly), so it can't be rendered via
`python -m paper.build` -- call build() directly instead.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from paper.figlib.io import FigureInputs
from paper.figlib.panels.decoding import (
    above_chance_fraction, draw_metric_surface_facets, draw_missing_data_placeholder, draw_model_row_header,
    has_kind, metric_range, partial_sweep_note,
)

FIGURE_ID = "place_robustness_3d_within_in_task"

_MODEL_AXES = {
    "independent": ("independent_sweep_092926", "percent_task_in_response", "percent_task_responsive_cells"),
    "place_dependent": ("place_dependent_sweep_092926", "percent_task_in_response", "percent_task_responsive_cells"),
    "arousal_mediated": ("arousal_mediated_sweep_092926", "percent_task_responsive_cells", "holdover"),
}

DIRECTION = "A->A"
KIND = "place_cm_in_task"
METRIC_LABEL = "Position decoding error (A→A, in task, cm, lower = better)"
DECODING_DESCRIPTION = "Decoding: position, A→A, in-task (within-environment)"


def build(inputs: FigureInputs, style) -> plt.Figure:
    style.apply_rc_params()
    decodings = {model: inputs.decoding[tag] for model, (tag, _, _) in _MODEL_AXES.items()}
    scored = {model: d for model, d in decodings.items() if has_kind(d, KIND)}
    vmin, vmax = metric_range(*scored.values(), direction=DIRECTION, kind=KIND)

    fig = plt.figure(figsize=(16.5, 30.0))
    rows = fig.subfigures(3, 1)

    panel_axes = {}
    for row, model in zip(rows, _MODEL_AXES):
        _, x_param, y_param = _MODEL_AXES[model]
        decoding = decodings[model]
        tag = _MODEL_AXES[model][0]

        if model not in scored:
            panel_axes[model] = [draw_missing_data_placeholder(
                row, f"Data not available\n{tag} predates the place in/out-of-task cm-error split")]
            draw_model_row_header(row, style.MODEL_DISPLAY_NAMES[model], DECODING_DESCRIPTION,
                                   "DATA NOT AVAILABLE", stats_color="firebrick", lower_is_better=True)
            continue

        panel_axes[model] = draw_metric_surface_facets(
            row, decoding, kind=KIND, direction=DIRECTION,
            x_var=x_param, y_var=y_param, facet_var="percent_place_cells",
            vmin=vmin, vmax=vmax, metric_label=METRIC_LABEL, axis_label="Error (cm)",
            reference_plane=True, highlight_above_chance=True)
        fraction, n_combos = above_chance_fraction(decoding, direction=DIRECTION, kind=KIND)
        note = partial_sweep_note(n_combos)
        stats_line = f"{style.BEATS_SHUFFLE_PHRASE} at {fraction * 100:.0f}% of {n_combos} grid points{note}"
        draw_model_row_header(row, style.MODEL_DISPLAY_NAMES[model], DECODING_DESCRIPTION, stats_line,
                               stats_color="darkorange" if note else "black", lower_is_better=True)

    fig.panel_axes = panel_axes
    return fig
