"""Supp (supp_place_pct): grid search over percent_place_cells, supporting
the 20% bioreal choice. No dedicated single-axis sweep exists for this yet
(checked webui/data/jobs.db, 2026-09-23) -- built instead as a slice through
the existing independent_sweep_080726/place_dependent_sweep_092926 matched
grids, at percent_task_responsive_cells=0.4 (bioreal's actual value) and
percent_task_in_response held to each of the two grid points nearest
bioreal's still-provisional balance=0.5 (0.4 and 0.6 -- equidistant, so both
are shown rather than picking one arbitrarily). holdover is fixed at 1.0 by
this sweep, not bioreal's own still-provisional value.

2026-10-02: place_dependent reads its _092926 tag (post velocity-gain-fix,
commit e1e4496). 2026-10-03: independent_sweep_092926 finished (216/216) and
replaces independent_sweep_080726 here too -- see robustness.py's module
docstring for the three-sweep policy this follows.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from paper.figlib.io import FigureInputs
from paper.figlib.panels.decoding import draw_param_lines, param_slice

FIGURE_ID = "supp_place_pct"

MODELS = ("independent", "place_dependent")
TAGS = {"independent": "independent_sweep_092926", "place_dependent": "place_dependent_sweep_092926"}
NEAREST_BALANCE_VALUES = (0.4, 0.6)  # grid points nearest bioreal's provisional balance=0.5
BIOREAL_PLACE_PCT = 0.2

# 2026-10-23 request ("Supp 9 ... make it purple instead of orange"): a local
# override, not a change to style.MODEL_COLORS -- this figure only has 2
# series (no third color to sit between them), and style.MODEL_COLORS'
# orange/blue pair here would become purple/blue, which FAILS the CVD-
# separation check on its own (deutan DeltaE 3.9; validate_palette.js
# "#2a78d6,#9b59d0" -- the same purple already used for FIELD_STATE_COLORS'
# out_of_field, re-stepped for the models figure's 3-way split, isn't
# distinct enough from blue as an isolated 2-color pair). This plum instead:
# `node scripts/validate_palette.js "#2a78d6,#7b2d8e" --mode light` -> ALL
# CHECKS PASS (deutan DeltaE 13.1). Scoped to this figure only -- place_dependent
# stays style.MODEL_COLORS' orange everywhere else.
PLACE_DEPENDENT_PURPLE = "#7b2d8e"


def build(inputs: FigureInputs, style) -> plt.Figure:
    style.apply_rc_params()
    colors = {**style.MODEL_COLORS, "place_dependent": PLACE_DEPENDENT_PURPLE}
    fig, axes = plt.subplots(1, len(NEAREST_BALANCE_VALUES),
                              figsize=(style.figure_width_inches("double"), 3.8), sharey=True)

    for i, (ax, balance) in enumerate(zip(axes, NEAREST_BALANCE_VALUES)):
        slices = {
            model: param_slice(
                inputs.decoding[TAGS[model]], param="percent_place_cells",
                fixed={"percent_task_responsive_cells": 0.4, "percent_task_in_response": balance},
            )
            for model in MODELS
        }
        draw_param_lines(ax, "percent_place_cells", slices, colors=colors,
                          display_names=style.MODEL_DISPLAY_NAMES, marker_value=BIOREAL_PLACE_PCT,
                          marker_label=f"Main-text setting ({BIOREAL_PLACE_PCT * 100:g}%)",
                          ylabel=f"Task-stage decoding accuracy ({style.direction_display_name('A->B')})",
                          chance_level=style.TASK_CHANCE_LEVEL, show_legend=(i == 0))
        ax.set_title(f"{style.PARAM_DISPLAY_NAMES['percent_task_in_response']} = {balance:g}", fontsize=9)

    fig.tight_layout()

    # Named panels for build.py's per-panel export (build/panels/supp_place_pct/<name>.*).
    fig.panel_axes = {f"balance_{balance:g}": ax for ax, balance in zip(axes, NEAREST_BALANCE_VALUES)}

    return fig
