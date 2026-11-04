"""Supp (robustness_3d): the 3D-surface version of robustness.py's grid --
same data, same shared color/z-scale fix (metric_range over all three
models), but rendered as 3D surfaces (ported camera/style from
scripts/pull_and_plot_holdover_sweep.py's plot_metric_surface_facets) instead
of 2D heatmaps. Kept as its own figure alongside robustness.py rather than
replacing it: the 2D heatmap is the print-safe, exact-value version; this one
keeps the 3D shape some readers want to see, now with the one thing the
original 3D version got wrong (each model auto-scaling to its own z-range)
fixed (2026-09-29 request).

2026-10-02: the z-axis used to carry the full
"Task-stage decoding accuracy (A→B, chance=0.2)" label, which collided with
the neighboring x/y param labels and was unreadable rotated vertically. The
z-axis now gets just "Accuracy" (draw_metric_surface_facets' axis_label
default for kind="task"); the full description moved to the shared colorbar
(unchanged) and into each block's own header below.

Also 2026-10-02: place_dependent/arousal_mediated now read their *_092926
tags; 2026-10-03: independent_sweep_092926 finished (216/216) and replaces
independent_sweep_080726 here too -- see robustness.py's module docstring.

2026-10-04: each model's header was briefly a 3-tier draw_model_row_header
(large bold model name; a medium line stating exactly what's being decoded;
the small beats-shuffle-floor stats line), then shortened to just the large
bold model name -- the decoding description and per-model beats-shuffle
fraction moved onto that model's own colorbar label instead (metric_label is
built per-model now, inside the loop, since the fraction varies by model).

2026-10-05: reverted -- bare model name alone doesn't say what the figure is
charting (2026-10-05 request: match robustness.py's header). Back to the
3-tier header; the colorbar label goes back to one shared, static
`base_label` (no per-model fraction suffix) since the stats line now carries
that instead -- same split robustness.py/place_robustness.py already use.

2026-10-05 (later same day): draw_model_row_header(..., compact=False) (the
non-compact mode, drawing above the row's own [0, 1] range) turned out not to
work for a 3-line header regardless of hspace between rows: the title/
description/stats text is positioned at fixed fractional offsets (y=1.06/
1.01/0.965) of EACH ROW's OWN height, so the gap between lines is fixed
relative to that one row, not to the space hspace adds between rows --
hspace changes how much blank canvas sits between rows, not how far apart
the header's own lines are from each other within one row, so it couldn't
have fixed this (confirmed by a minimal repro: the title and description
line collided even at hspace=0.3). It also outright clips off-canvas for the
topmost row, which has no figure space above it for y>1 content to render
into. Switched to the header/body subfigure split (compact=True) instead --
proven working in robustness.py/place_robustness.py, where the header draws
WITHIN its own small, dedicated subfigure instead of spilling above a
possibly-short one.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from paper.figlib.io import FigureInputs
from paper.figlib.panels.decoding import (
    above_chance_fraction, draw_metric_surface_facets, draw_model_row_header, metric_range,
)

FIGURE_ID = "robustness_3d"

# (tag, x_param, y_param) per model -- facet_param is percent_place_cells for all three.
_MODEL_AXES = {
    "independent": ("independent_sweep_092926", "percent_task_in_response", "percent_task_responsive_cells"),
    "place_dependent": ("place_dependent_sweep_092926", "percent_task_in_response", "percent_task_responsive_cells"),
    "arousal_mediated": ("arousal_mediated_sweep_092926", "percent_task_responsive_cells", "holdover"),
}
DECODING_DESCRIPTION = "Decoding: task stage, A→B (cross-environment)"


def build(inputs: FigureInputs, style) -> plt.Figure:
    style.apply_rc_params()
    decodings = {model: inputs.decoding[tag] for model, (tag, _, _) in _MODEL_AXES.items()}
    vmin, vmax = metric_range(*decodings.values())
    base_label = (
        f"Task-stage decoding accuracy ({style.direction_display_name('A->B')}, {style.CHANCE_LABEL.lower()})")

    # 3D facet grids need a generous per-panel budget -- the paper's narrow
    # journal-column width crams titles into each other (see
    # draw_metric_surface_facets' docstring). Every model here has 6 facets
    # (ncols=3, nrows=2), so one model's own body is about (16.5, 9.2); each
    # row also gets its own small header subfigure (see module docstring).
    fig = plt.figure(figsize=(16.5, 22.5))
    rows = fig.subfigures(3, 1, hspace=0.03)

    panel_axes = {}
    for row, model in zip(rows, _MODEL_AXES):
        _, x_param, y_param = _MODEL_AXES[model]
        decoding = decodings[model]
        header_fig, body_fig = row.subfigures(2, 1, height_ratios=[0.5, 3.0], hspace=0.01)
        panel_axes[model] = draw_metric_surface_facets(
            body_fig, decoding, x_var=x_param, y_var=y_param, facet_var="percent_place_cells",
            vmin=vmin, vmax=vmax, metric_label=base_label)
        fraction, n_combos = above_chance_fraction(decoding, direction="A->B")
        stats_line = f"{style.BEATS_SHUFFLE_PHRASE} at {fraction * 100:.0f}% of {n_combos} grid points"
        draw_model_row_header(header_fig, style.MODEL_DISPLAY_NAMES[model], DECODING_DESCRIPTION, stats_line,
                               compact=True)

    # Named panels for build.py's per-panel export (build/panels/robustness_3d/<name>.*).
    fig.panel_axes = panel_axes

    return fig
