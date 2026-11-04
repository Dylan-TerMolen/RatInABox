"""Fig (task_decoding_by_balance): task-stage decoding accuracy at bioreal's
percentages (20% place cells, 40% task-responsive cells), per model, plotted
as a function of the axis each model actually sweeps at that fixed point --
task weight (balance) for IM/PDM. The sole task-stage-decoding-at-bioreal
figure as of 2026-10-05: an earlier bar-chart version (manifest id
`task_decoding`) that aggregated each model's bar across its full remaining
swept range was deleted entirely (2026-10-05 request: "the aggregation is
not clear at all") -- this figure shows the actual values a reader would
otherwise have to trust were summarized reasonably.

arousal_mediated has no balance parameter at all. Its only remaining swept
axis at this fixed point is holdover -- a different parameter with no shared
scale or meaning against balance, so plotting it on the same kind of line as
IM/PDM's balance rows would imply a comparability that isn't there (same
reasoning as position_decoding.py's arousal_mediated row). It instead shows
the single real grid point at holdover=100% (bioreal's own chosen value,
paper/params/bioreal.yaml) as a horizontal mean+CI band spanning the full
panel width -- NOT an aggregate across holdover (2026-10-05 correction: an
earlier version of this row aggregated across the model's full holdover
sweep via direction_stats, which the per-value point below the aggregate
couldn't actually show was representative of). No figure in this pipeline
aggregates across arousal_mediated's holdover anymore -- the grid figures
(robustness/robustness_3d/task_decoding_within/task_decoding_within_3d) show
every holdover value as its own axis instead of collapsing it, and this
figure picks the one value that matches IM/PDM's own fixed point.

2026-10-23 review ("start the y-axis at 0", "make this look less empty...
maybe we only do 2 total graphs, one for within-environment and one for
x-env"): collapsed from a 3-model x 2-direction grid (6 panels, 2 of which
were a single floating point in an otherwise-empty axes) down to 2 panels --
one within-env, one cross-env -- with all 3 models overlaid on the same
axes. IM/PDM draw as before (lines vs. balance); ADM's single point now
reads as a horizontal reference band (mean +/- CI) against the same axis
instead of sitting alone in its own panel. Y-axis pinned to start at 0
(previously autoscaled to the data, starting around 0.17-0.2) and shared
across both panels so the numbers stay directly comparable.

Within-env shown as A->A (not also B->B, matching position_decoding.py's own
within-env convention -- there's no separate shuffB->B kind either, see
decoding.py's DIRECTIONS). Each model keeps its own empirical shuffled-
baseline reference (thin dotted line in that model's own color), not just
the analytic chance=0.2 line.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from paper.figlib.io import FigureInputs, load_param_set
from paper.figlib.panels.decoding import (
    direction_stats, draw_param_lines, extend_ylim_for_floors, param_slice, share_ylim, shuffled_reference_value,
)

FIGURE_ID = "task_decoding_by_balance"

# model -> (its bioreal-percentage decoding tag, the param IM/PDM sweep).
# arousal_mediated has no balance parameter -- it's drawn separately as a
# fixed-point reference band (see _draw_combined_panel) rather than a line.
MODEL_TAGS = {
    "independent": ("independent_sweep_092926", "percent_task_in_response"),
    "place_dependent": ("place_dependent_sweep_092926", "percent_task_in_response"),
    "arousal_mediated": ("arousal_mediated_sweep_092926", None),
}
LINE_MODELS = ("independent", "place_dependent")
BIOREAL_FIXED = {"percent_place_cells": 0.2, "percent_task_responsive_cells": 0.4}
# bioreal's own holdover value (paper/params/bioreal.yaml) -- the single grid
# point arousal_mediated's band uses, matching IM/PDM's own fixed holdover=1.0
# (see supp_place_pct_all_models.py's identical ADM_FIXED_HOLDOVER convention).
ADM_HOLDOVER = 1.0
BIOREAL_PARAMS = load_param_set("bioreal")


def _draw_combined_panel(ax, *, direction: str, inputs: FigureInputs, style, show_legend: bool) -> None:
    """All 3 models on one axis: IM/PDM as lines vs. task weight (balance),
    ADM as a horizontal mean +/- CI band (it has no balance value to put on
    the x-axis). Each model's own empirical shuffled floor is drawn as a
    thin dotted line in that model's color; only the first is legended
    (generic "Shuffled baseline", the floors all sit near the same value)."""
    series, floors = {}, []
    for i, model in enumerate(LINE_MODELS):
        tag, x_param = MODEL_TAGS[model]
        decoding = inputs.decoding[tag]
        series[model] = param_slice(decoding, param=x_param, fixed=BIOREAL_FIXED, direction=direction, kind="task")
        floor = shuffled_reference_value(decoding, kind="task", direction=direction, fixed=BIOREAL_FIXED)
        ax.axhline(floor, color=style.MODEL_COLORS[model], linestyle=":", linewidth=1.0, alpha=0.4, zorder=1,
                   label="Shuffled baseline" if i == 0 else None)
        floors.append(floor)

    draw_param_lines(ax, "percent_task_in_response", series, colors=style.MODEL_COLORS,
                      display_names=style.MODEL_DISPLAY_NAMES, ylabel="Task-stage decoding accuracy",
                      chance_level=style.TASK_CHANCE_LEVEL, show_legend=False)

    adm_tag, _ = MODEL_TAGS["arousal_mediated"]
    adm_decoding = inputs.decoding[adm_tag]
    fixed = {**BIOREAL_FIXED, "holdover": ADM_HOLDOVER}
    row = direction_stats(adm_decoding, kind="task", fixed=fixed).set_index("direction").loc[direction]
    adm_color = style.MODEL_COLORS["arousal_mediated"]
    # edgecolor="none": axhspan's `color=` convenience kwarg sets facecolor
    # AND edgecolor to the same green, so the translucent band's own border
    # rendered as a second, crisper green line framing the solid mean line
    # (2026-10-23: "why is there a green outline of the green line" --
    # exactly that border, not a rendering artifact). A flat fill with no
    # edge reads cleanly as a CI band instead.
    ax.axhspan(row["mean"] - row["ci"], row["mean"] + row["ci"], facecolor=adm_color, edgecolor="none",
               alpha=0.15, zorder=0)
    ax.axhline(row["mean"], color=adm_color, linewidth=1.5, zorder=2,
               label=f"{style.MODEL_DISPLAY_NAMES['arousal_mediated']} (holdover={ADM_HOLDOVER * 100:g}%)")
    adm_floor = shuffled_reference_value(adm_decoding, kind="task", direction=direction, fixed=fixed)
    ax.axhline(adm_floor, color=adm_color, linestyle=":", linewidth=1.0, alpha=0.4, zorder=1)
    floors += [row["mean"] - row["ci"], adm_floor]

    extend_ylim_for_floors(ax, floors, pad=0.02)
    ax.set_ylim(bottom=0)  # 2026-10-23 request: start at 0, not the data-driven ~0.17-0.2
    if show_legend:
        ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0.)


def build(inputs: FigureInputs, style) -> plt.Figure:
    style.apply_rc_params()
    fig, (ax_within, ax_cross) = plt.subplots(1, 2, figsize=(style.figure_width_inches("double"), 4.5))

    _draw_combined_panel(ax_within, direction="A->A", inputs=inputs, style=style, show_legend=True)
    ax_within.set_title(style.WITHIN_ENV_LABEL, fontsize=10)

    _draw_combined_panel(ax_cross, direction="A->B", inputs=inputs, style=style, show_legend=False)
    ax_cross.set_title(style.CROSS_ENV_LABEL, fontsize=10)

    share_ylim([ax_within, ax_cross])

    fig.suptitle(style.bioreal_headline(BIOREAL_PARAMS, decoding_label="Task decoding"),
                 fontsize=14, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.92))

    # Named panels for build.py's per-panel export (build/panels/task_decoding_by_balance/<name>.*).
    fig.panel_axes = {"within": ax_within, "cross": ax_cross}

    return fig
