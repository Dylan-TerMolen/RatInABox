"""Supp (place_robustness_in_task): in-task counterpart to place_robustness.py
-- same model/sweep/axis setup, same header/body-split + per-cell-value-text
2D heatmap grid, place_cm_in_task instead of place_cm_out_of_task. Position
decoding while the animal is in a CS/trace/US trial is contaminated by that
trial structure (unlike the clean behavioral-epoch samples out-of-task uses),
which is why place_robustness.py scoped itself to out-of-task only -- this
figure exists so that in-task number is visible per-grid-point too, not just
as the sweep-wide aggregate decoding_place_summary already shows.

2026-10-04 request ("Do b" -- add the 2D-heatmap in-task version, after
place_robustness_3d_within_in_task.py/place_robustness_3d_cross_in_task.py
were built for review only and never wired into the manifest). Unlike those
two 3D scripts, this one IS registered in manifest.yaml from the start.

Built without place_robustness.py's "No data (sweep in progress)" legend key
-- that key was dropped from place_robustness.py/robustness.py the same day
since all three sweeps are complete, so this one never had it to begin with.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from paper.figlib.io import FigureInputs
from paper.figlib.panels.decoding import (
    above_chance_fraction, draw_missing_data_placeholder, draw_model_row_header, draw_task_transfer_heatmap_grid,
    has_kind, metric_range, partial_sweep_note,
)

FIGURE_ID = "place_robustness_in_task"

# Same sweeps/axes as place_robustness.py.
_MODEL_AXES = {
    "independent": ("independent_sweep_092926", "percent_task_in_response", "percent_task_responsive_cells"),
    "place_dependent": ("place_dependent_sweep_092926", "percent_task_in_response", "percent_task_responsive_cells"),
    "arousal_mediated": ("arousal_mediated_sweep_092926", "percent_task_responsive_cells", "holdover"),
}

DIRECTION = "A->B"
KIND = "place_cm_in_task"
METRIC_LABEL = "Position decoding error (A→B, in task, cm, lower = better)"
DECODING_DESCRIPTION = "Decoding: position, A→B, in-task (cross-environment)"


def build(inputs: FigureInputs, style) -> plt.Figure:
    style.apply_rc_params()
    decodings = {model: inputs.decoding[tag] for model, (tag, _, _) in _MODEL_AXES.items()}
    scored = {model: d for model, d in decodings.items() if has_kind(d, KIND)}
    vmin, vmax = metric_range(*scored.values(), direction=DIRECTION, kind=KIND)

    # See place_robustness.py's own comment: header/body split so each is
    # sized to what it actually needs, and 3 facets per row (not 6) so the
    # per-cell value text stays legible.
    fig = plt.figure(figsize=(style.figure_width_inches("double"), 22))
    rows = fig.subfigures(3, 1, hspace=0.04)

    panel_axes = {}
    for row, model in zip(rows, _MODEL_AXES):
        _, x_param, y_param = _MODEL_AXES[model]
        decoding = decodings[model]
        tag = _MODEL_AXES[model][0]
        header_fig, body_fig = row.subfigures(2, 1, height_ratios=[0.6, 2.4], hspace=0.01)

        if model not in scored:
            panel_axes[model] = [draw_missing_data_placeholder(
                body_fig, f"Data not available\n{tag} predates the place in/out-of-task cm-error split")]
            draw_model_row_header(header_fig, style.MODEL_DISPLAY_NAMES[model], DECODING_DESCRIPTION,
                                   "DATA NOT AVAILABLE", stats_color="firebrick", lower_is_better=True,
                                   compact=True)
            continue

        panel_axes[model] = draw_task_transfer_heatmap_grid(
            body_fig, decoding, kind=KIND, direction=DIRECTION, x_param=x_param, y_param=y_param,
            facet_param="percent_place_cells", vmin=vmin, vmax=vmax, metric_label=METRIC_LABEL)
        fraction, n_combos = above_chance_fraction(decoding, direction=DIRECTION, kind=KIND)
        note = partial_sweep_note(n_combos)
        stats_line = f"{style.BEATS_SHUFFLE_PHRASE} at {fraction * 100:.0f}% of {n_combos} grid points{note}"
        draw_model_row_header(header_fig, style.MODEL_DISPLAY_NAMES[model], DECODING_DESCRIPTION, stats_line,
                               stats_color="darkorange" if note else "black", lower_is_better=True, compact=True)

    # Named panels for build.py's per-panel export (build/panels/place_robustness_in_task/<name>.*).
    fig.panel_axes = panel_axes

    return fig
