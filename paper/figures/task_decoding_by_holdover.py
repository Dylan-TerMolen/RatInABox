"""Supp (task_decoding_by_holdover): cross-environment (A->B) task-stage
decoding accuracy at bioreal's percentages (20% place cells, 40%
task-responsive cells), all three models on one shared panel, plotted against
holdover (the fraction of env A's task-responsive cells carried into env B)
-- the one axis every model's bioreal-point sweep now actually has in common.

Cross-environment only (no within-environment panel): holdover is a
cross-environment carryover parameter by construction -- it has no effect on
how well task stage reads out within a single environment (2026-10-06
request; confirmed in the full two-panel version this replaced, where IM's
within-env accuracy was flat across the whole holdover range while its
cross-env accuracy rose steadily with it).

Until 2026-10-05, IM/PDM's own sweeps (independent_sweep_092926,
place_dependent_sweep_092926) held holdover fixed at 1.0 across their whole
grid -- see robustness.py's module docstring -- so no IM/PDM holdover curve
existed anywhere in this pipeline; only arousal_mediated (which has no
task-weight axis) ever swept holdover (arousal_mediated_sweep_092926, 6-value
0.2-step grid: 0.0/0.2/0.4/0.6/0.8/1.0). task_decoding_by_balance.py's
arousal_mediated row worked around that gap by showing a single fixed point
instead of a line, specifically because no comparable IM/PDM holdover curve
existed to put next to it.

That gap is now closed: slurm/independent_holdover_sweep.sh and
slurm/place_dependent_holdover_sweep.sh are dedicated single-axis holdover
sweeps at the bioreal fixed point (percent_task_in_response=0.5,
percent_task_responsive_cells=0.4, percent_place_cells=0.2), 11 values
(0.0-1.0 in steps of 0.1) -- finer than arousal_mediated's existing 6-value
grid, but both are real sweeps over the same parameter, so all three models
get an actual line here, not an aggregate or a single point.

Chance level (0.20, analytic KNN floor) is drawn on the panel; no per-model
empirical shuffled-floor lines are drawn on top of it -- three more dashed
lines in the same colors as the data lines would clutter an already-overlaid
3-model panel more than they'd add (same call supp_place_pct_all_models.py
made for its own 3-model overlay).
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from paper.figlib.io import FigureInputs, load_param_set
from paper.figlib.panels.decoding import draw_param_lines, param_slice

FIGURE_ID = "task_decoding_by_holdover"

MODELS = ("independent", "place_dependent", "arousal_mediated")
TAGS = {
    "independent": "independent_holdover_sweep_bioreal_100526",
    "place_dependent": "place_dependent_holdover_sweep_bioreal_100526",
    "arousal_mediated": "arousal_mediated_sweep_092926",
}
# Fixed point every model's sweep shares -- doesn't include
# percent_task_in_response since arousal_mediated has no such column at all
# (it would come back all-NaN and filter out every row).
BIOREAL_FIXED = {"percent_place_cells": 0.2, "percent_task_responsive_cells": 0.4}
BIOREAL_PARAMS = load_param_set("bioreal")


DIRECTION = "A->B"


def _slice_for_model(model: str, decoding):
    return param_slice(decoding, param="holdover", fixed=BIOREAL_FIXED, direction=DIRECTION, kind="task")


def build(inputs: FigureInputs, style) -> plt.Figure:
    style.apply_rc_params()
    # Double-column width and a centered below-axes legend (rather than
    # draw_param_lines' usual outside-right legend) -- a single panel at
    # single-column width with an outside-right legend left the axes
    # lopsided in the figure's left half (2026-10-06 report: "looks odd").
    fig, ax = plt.subplots(1, 1, figsize=(style.figure_width_inches("double"), 4.5))

    slices = {model: _slice_for_model(model, inputs.decoding[TAGS[model]]) for model in MODELS}
    draw_param_lines(ax, "holdover", slices, colors=style.MODEL_COLORS, display_names=style.MODEL_DISPLAY_NAMES,
                      marker_value=BIOREAL_PARAMS["holdover"],
                      marker_label=f"Main-text setting ({BIOREAL_PARAMS['holdover'] * 100:g}%)",
                      ylabel=f"Task-stage decoding accuracy ({style.direction_display_name(DIRECTION)})",
                      chance_level=style.TASK_CHANCE_LEVEL, show_legend=False)

    fig.suptitle(
        f"{style.bioreal_headline(BIOREAL_PARAMS, decoding_label='Cross-environment task decoding by holdover')}",
        fontsize=11, fontweight="bold")
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.86), ncol=5, fontsize=7, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.84))

    # Named panels for build.py's per-panel export (build/panels/task_decoding_by_holdover/<name>.*).
    fig.panel_axes = {"cross_env": ax}

    return fig
