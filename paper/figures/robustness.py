"""Fig 5 / supp (robustness): cross-env task decoding over a parameter grid,
per model -- IM's advantage isn't one lucky parameter choice. Rendered as 2D
heatmaps (not the earlier 3D surface facets -- unreadable at print size and,
worse, each model got its own color scale, which made PDM/ADM's narrow
0.19-0.27 accuracy range look as strong as IM's 0.2-0.62 range once each was
independently stretched to fill its own colorbar; 2026-09-29 review items 1
and 4). All three models now share one color scale (metric_range over
all three decodings) so the comparison is honest. Each model still gets its
own grid over its own actually-swept parameters: IM/PDM share axes
(percent_task_in_response x percent_task_responsive_cells, faceted by
percent_place_cells, holdover fixed at 1.0); arousal_mediated has no balance
parameter at all (the model ignores that axis, see CLAUDE.md), so its grid is
necessarily percent_task_responsive_cells x holdover, faceted by
percent_place_cells instead -- a real modeling asymmetry, not a data gap (see
2026-09-25 chat). Benchmark contour (ref 19) not drawn yet -- see
style.BENCHMARK_VALUE.

2026-10-02: place_dependent/arousal_mediated now read their *_092926 tags
(post velocity-gain-fix, commit e1e4496).

2026-10-03: independent_sweep_092926 finished (216/216 logs) and replaces
independent_sweep_080726 here -- all three models now read their post
velocity-gain-fix *_092926 tags.

2026-10-04: same 3-tier draw_model_row_header as robustness_3d.py/
place_robustness_3d_within/cross (large bold model name; a medium line
stating exactly what's being decoded; the small beats-shuffle-floor stats
line) instead of one small suptitle line that mashed the model name and the
stats together -- applied here too for consistency across the whole
robustness/place_robustness_3d* family.

2026-10-04 (later same day): each model row is now TWO nested subfigures --
a small header-only one (draw_model_row_header(..., compact=True), drawn
inside its own [0, 1] range) and a body one sized to just the one-row,
square-cell facet grid. The original single-subfigure-per-model design
placed the header ABOVE each subfigure's own [0, 1] range (y>1, a fixed
fraction of that subfigure's height), which only works if the subfigure is
tall enough (~10in) for the header's fixed-point-size text not to collide
with itself -- fine when the body needed that much height anyway (the old 2
rows x 3 cols grid), but once "more facets per row" (below) shrank the body
to ~1 row of square cells, keeping a ~10in subfigure just to satisfy the
header requirement left most of it blank (confirmed by rendering: ~70% empty
space per model block). Splitting header and body into their own subfigures
lets each be sized to what it actually needs.

2026-10-04 (later still): per-cell value text (dropped earlier the same day
to fix overlap) is back -- removing it made the grid unreadable in a
different way. The actual fix is cell size: draw_task_transfer_heatmap_grid
now puts 3 facets per row instead of 6, so each facet (and the 6x6 cells
inside it) has roughly double the room, and the figure/body heights here grew
to match. See draw_heatmap's and draw_task_transfer_heatmap_grid's own
docstrings for the full reasoning.

2026-10-04 (later still): dropped the "No data (sweep in progress)" legend
key -- all three approved tags' sweeps are complete, so the hatch it
explained never actually appears; draw_heatmap's NaN-hatching itself stays
(a real future gap would still render as a hatch, just without a standing
key for a case that isn't live).
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from paper.figlib.io import FigureInputs
from paper.figlib.panels.decoding import (
    above_chance_fraction, draw_model_row_header, draw_task_transfer_heatmap_grid, metric_range,
)

FIGURE_ID = "robustness"

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

    # Each model row is a header subfigure (just tall enough for the 3-tier
    # text's own fixed point sizes, see draw_model_row_header's `compact`
    # docstring) plus a body subfigure (sized for 2 rows of 3 square-cell
    # facets, not 1 row of 6 -- see draw_task_transfer_heatmap_grid's
    # docstring on why 3-per-row is what keeps the per-cell values legible).
    fig = plt.figure(figsize=(style.figure_width_inches("double"), 21))
    rows = fig.subfigures(3, 1, hspace=0.04)

    panel_axes = {}
    for row, model in zip(rows, _MODEL_AXES):
        _, x_param, y_param = _MODEL_AXES[model]
        decoding = decodings[model]
        header_fig, body_fig = row.subfigures(2, 1, height_ratios=[0.45, 2.4], hspace=0.01)
        panel_axes[model] = draw_task_transfer_heatmap_grid(
            body_fig, decoding, x_param=x_param, y_param=y_param, facet_param="percent_place_cells",
            vmin=vmin, vmax=vmax)
        fraction, n_combos = above_chance_fraction(decoding, direction="A->B")
        stats_line = f"{style.BEATS_SHUFFLE_PHRASE} at {fraction * 100:.0f}% of {n_combos} grid points"
        draw_model_row_header(header_fig, style.MODEL_DISPLAY_NAMES[model], DECODING_DESCRIPTION, stats_line,
                               compact=True)

    # Named panels for build.py's per-panel export (build/panels/robustness/<name>.*).
    fig.panel_axes = panel_axes

    return fig
