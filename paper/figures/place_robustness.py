"""Supp (place_robustness): the 2D-heatmap version of
place_robustness_3d_cross's grid -- same data, same shared color scale
(metric_range over all three models), but rendered as 2D heatmaps (ported
style from robustness.py/draw_task_transfer_heatmap_grid) instead of 3D
surfaces. The 2D heatmap is the print-safe, exact-value version; the 3D one
(place_robustness_3d_cross.py) keeps the surface shape some readers want to
see -- same relationship robustness.py already has to robustness_3d.py, now
extended to position decoding ("a figure similar to S1 for position
decoding", 2026-10-04 request).

Cross-environment (A->B), out-of-task only -- matching robustness.py's own
scope (one direction, not both within/cross) rather than doubling this into
within+cross companions the way the 3D version did; see
place_robustness_3d_within.py/place_robustness_3d_cross.py for the
within-environment counterpart if that's wanted here too.

Same three-sweep policy, same independent-partial-sweep handling, and same
3-tier draw_model_row_header + LOWER_IS_BETTER_NOTE as
place_robustness_3d_cross.py -- see that module's docstring and
robustness.py's module docstring for the full history.

2026-10-04: same header/body subfigure split as robustness.py (see its
module docstring) -- draw_model_row_header(..., compact=True) into a small
header-only subfigure, draw_task_transfer_heatmap_grid into a body subfigure
sized to just the one-row facet grid, instead of one oversized subfigure per
model mostly left blank.

2026-10-04 (later still): per-cell value text restored (see robustness.py's
own later note) -- 3 facets per row instead of 6, body height grown to match,
so each facet's 6x6 cells are large enough for their values to read.

2026-10-04 (later still): dropped the "No data (sweep in progress)" legend
key, same reasoning as robustness.py -- all three sweeps are complete so the
hatch it explained never appears; draw_heatmap's NaN-hatching stays as the
generic missing-data handling.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from paper.figlib.io import FigureInputs
from paper.figlib.panels.decoding import (
    above_chance_fraction, draw_missing_data_placeholder, draw_model_row_header, draw_task_transfer_heatmap_grid,
    has_kind, metric_range, partial_sweep_note,
)

FIGURE_ID = "place_robustness"

# Same sweeps/axes as robustness.py / place_robustness_3d_cross.py.
_MODEL_AXES = {
    "independent": ("independent_sweep_092926", "percent_task_in_response", "percent_task_responsive_cells"),
    "place_dependent": ("place_dependent_sweep_092926", "percent_task_in_response", "percent_task_responsive_cells"),
    "arousal_mediated": ("arousal_mediated_sweep_092926", "percent_task_responsive_cells", "holdover"),
}

DIRECTION = "A->B"
KIND = "place_cm_out_of_task"
METRIC_LABEL = "Position decoding error (A→B, out of task, cm, lower = better)"
DECODING_DESCRIPTION = "Decoding: position, A→B, out-of-task (cross-environment)"


def build(inputs: FigureInputs, style) -> plt.Figure:
    style.apply_rc_params()
    decodings = {model: inputs.decoding[tag] for model, (tag, _, _) in _MODEL_AXES.items()}
    scored = {model: d for model, d in decodings.items() if has_kind(d, KIND)}
    vmin, vmax = metric_range(*scored.values(), direction=DIRECTION, kind=KIND)

    # See robustness.py's own comment: header/body split so each is sized to
    # what it actually needs instead of one oversized, mostly-blank subfigure,
    # and 3 facets per row (not 6) so the per-cell value text stays legible.
    # This header is taller than robustness.py's (adds the bold red
    # lower_is_better note), hence a slightly richer height ratio.
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

    # Named panels for build.py's per-panel export (build/panels/place_robustness/<name>.*).
    fig.panel_axes = panel_axes

    return fig
