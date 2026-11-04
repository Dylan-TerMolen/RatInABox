"""Supp (place_robustness_3d_within): place_robustness_3d's within-environment
(A->A) companion to robustness_3d.py's task-decoding grid -- same per-model
axes, same shared color/z-scale fix (metric_range over all three models).

2026-10-02: metric is mean position error in centimeters (lower is better),
not R^2 -- R^2 was dropped from this pipeline entirely per instruction; place
decoding is reported in cm everywhere now, including here, despite env B
being physically smaller than env A (so its raw cm errors run smaller by
default -- a real asymmetry to read the cross-env companion figure against,
not a reason to fall back to R^2). Out-of-task samples only (the clean
spatial readout, uncontaminated by CS/trace/US trial structure); the in-task
version exists as place_robustness_3d_within_in_task.py but isn't wired into
the manifest yet (2026-10-02 request: build it for review, add it to the
manifest only once asked for explicitly).

2026-10-03: independent now reads independent_sweep_092926 (not
independent_sweep_080726 -- that tag predates the place cm in/out-of-task
split entirely and could only ever render a placeholder here).
independent_sweep_092926 finished the same day (216/216 combos, matching
place_dependent/arousal_mediated). has_kind/draw_missing_data_placeholder are
kept as a general safety net for any future tag that genuinely lacks this
kind, not because independent needs it right now.

Adds, on top of what robustness_3d.py's panel function already did: a
translucent reference plane at this direction's mean shuffled cm error
(shuffled_reference_value), a reversed colormap so lower error reads as the
same "good" color as high accuracy elsewhere (draw_metric_surface_facets'
_lower_is_better), and a black ring around grid points whose CI clears that
shuffled floor's CI on the better-is-lower side (same CI-non-overlap rule as
above_chance_fraction, applied per-point instead of just aggregated into the
title's fraction).

2026-10-04: each model's header was briefly a 3-tier draw_model_row_header,
then shortened to just the large bold model name -- the decoding
description, "lower = better" note, and per-model beats-shuffle-floor
fraction moved onto that model's own colorbar label instead (built per-model
inside the loop, since the fraction varies by model). The independent block's
"[PARTIAL SWEEP: n/216]" bracket also moved off the image entirely (it's in
the caption now, see place_robustness_3d_within.md) -- the colorbar's
"of {n} points" already says how many were available, in the same normal
color as everything else, not singled out in orange.

2026-10-05: reverted -- bare model name alone doesn't say what the figure is
charting (2026-10-05 request: match robustness.py's header). Back to the
3-tier header (model name, decoding description, "lower = better" note,
beats-shuffle-floor stats line); METRIC_LABEL on the colorbar goes back to
one shared, static string (no per-model fraction suffix), same split
robustness.py/place_robustness.py already use.

2026-10-05 (later same day): switched to the header/body subfigure split
(compact=True) -- see robustness_3d.py's own later note for why the
non-compact mode (header text above each row's own [0, 1] range) doesn't
work for more than one line regardless of hspace between rows.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from paper.figlib.io import FigureInputs
from paper.figlib.panels.decoding import (
    above_chance_fraction, draw_metric_surface_facets, draw_missing_data_placeholder, draw_model_row_header,
    has_kind, metric_range,
)

FIGURE_ID = "place_robustness_3d_within"

# (tag, x_param, y_param) per model -- facet_param is percent_place_cells for all three.
_MODEL_AXES = {
    "independent": ("independent_sweep_092926", "percent_task_in_response", "percent_task_responsive_cells"),
    "place_dependent": ("place_dependent_sweep_092926", "percent_task_in_response", "percent_task_responsive_cells"),
    "arousal_mediated": ("arousal_mediated_sweep_092926", "percent_task_responsive_cells", "holdover"),
}

DIRECTION = "A->A"
KIND = "place_cm_out_of_task"
METRIC_LABEL = "Position decoding error (A→A, out-of-task, within-environment, cm, lower = better)"
DECODING_DESCRIPTION = "Decoding: position, A→A, out-of-task (within-environment)"


def build(inputs: FigureInputs, style) -> plt.Figure:
    style.apply_rc_params()
    decodings = {model: inputs.decoding[tag] for model, (tag, _, _) in _MODEL_AXES.items()}
    scored = {model: d for model, d in decodings.items() if has_kind(d, KIND)}
    vmin, vmax = metric_range(*scored.values(), direction=DIRECTION, kind=KIND)

    # Same generous per-panel budget as robustness_3d.py -- see its own
    # comment. Each row also gets its own small header subfigure (see module
    # docstring).
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

    # Named panels for build.py's per-panel export (build/panels/place_robustness_3d_within/<name>.*).
    fig.panel_axes = panel_axes

    return fig
