"""Supp (place_robustness_3d_cross): place_robustness_3d's cross-environment
(A->B) companion -- see place_robustness_3d_within.py's module docstring for
the cm-error (not R^2) metric and the out-of-task scope. independent_sweep_092926
finished (216/216 combos) 2026-10-03; the partial-sweep handling it needed
while mid-run stays in place as a safety net for any future in-flight tag.
The in-task version exists as place_robustness_3d_cross_in_task.py but isn't
wired into the manifest yet (same 2026-10-02 request).

2026-10-04: same shortened header (model name only) as place_robustness_3d_within.py
-- the decoding description, "lower = better" note, and per-model
beats-shuffle-floor fraction moved onto that model's own colorbar label
instead; the independent block's "[PARTIAL SWEEP: n/216]" bracket moved off
the image entirely (it's in the caption now).

2026-10-05: reverted -- same 3-tier header restored as place_robustness_3d_within.py
(2026-10-05 request: match robustness.py's header). METRIC_LABEL on the
colorbar goes back to a shared, static string.

2026-10-05 (later same day): switched to the header/body subfigure split
(compact=True), same fix and same reason as robustness_3d.py/
place_robustness_3d_within.py's own later notes.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from paper.figlib.io import FigureInputs
from paper.figlib.panels.decoding import (
    above_chance_fraction, draw_metric_surface_facets, draw_missing_data_placeholder, draw_model_row_header,
    has_kind, metric_range,
)

FIGURE_ID = "place_robustness_3d_cross"

# Same sweeps/axes as robustness_3d.py / place_robustness_3d_within.py.
_MODEL_AXES = {
    "independent": ("independent_sweep_092926", "percent_task_in_response", "percent_task_responsive_cells"),
    "place_dependent": ("place_dependent_sweep_092926", "percent_task_in_response", "percent_task_responsive_cells"),
    "arousal_mediated": ("arousal_mediated_sweep_092926", "percent_task_responsive_cells", "holdover"),
}

DIRECTION = "A->B"
KIND = "place_cm_out_of_task"
METRIC_LABEL = "Position decoding error (A→B, out-of-task, cross-environment, cm, lower = better)"
DECODING_DESCRIPTION = "Decoding: position, A→B, out-of-task (cross-environment)"


def build(inputs: FigureInputs, style) -> plt.Figure:
    style.apply_rc_params()
    decodings = {model: inputs.decoding[tag] for model, (tag, _, _) in _MODEL_AXES.items()}
    scored = {model: d for model, d in decodings.items() if has_kind(d, KIND)}
    vmin, vmax = metric_range(*scored.values(), direction=DIRECTION, kind=KIND)

    fig = plt.figure(figsize=(16.5, 23.0))
    rows = fig.subfigures(3, 1, hspace=0.03)

    panel_axes = {}
    for row, model in zip(rows, _MODEL_AXES):
        _, x_param, y_param = _MODEL_AXES[model]
        decoding = decodings[model]
        tag = _MODEL_AXES[model][0]
        header_fig, body_fig = row.subfigures(2, 1, height_ratios=[0.6, 3.0], hspace=0.01)

        if model not in scored:
            panel_axes[model] = [draw_missing_data_placeholder(
                body_fig, f"Data not available\n{tag} predates the place in/out-of-task cm-error split")]
            draw_model_row_header(header_fig, style.MODEL_DISPLAY_NAMES[model], DECODING_DESCRIPTION,
                                   "DATA NOT AVAILABLE", stats_color="firebrick", lower_is_better=True,
                                   compact=True)
            continue

        panel_axes[model] = draw_metric_surface_facets(
            body_fig, decoding, kind=KIND, direction=DIRECTION,
            x_var=x_param, y_var=y_param, facet_var="percent_place_cells",
            vmin=vmin, vmax=vmax, metric_label=METRIC_LABEL, axis_label="Error (cm)",
            reference_plane=True, highlight_above_chance=True)
        fraction, n_combos = above_chance_fraction(decoding, direction=DIRECTION, kind=KIND)
        stats_line = f"{style.BEATS_SHUFFLE_PHRASE} at {fraction * 100:.0f}% of {n_combos} grid points"
        draw_model_row_header(header_fig, style.MODEL_DISPLAY_NAMES[model], DECODING_DESCRIPTION, stats_line,
                               lower_is_better=True, compact=True)

    # Named panels for build.py's per-panel export (build/panels/place_robustness_3d_cross/<name>.*).
    fig.panel_axes = panel_axes

    return fig
