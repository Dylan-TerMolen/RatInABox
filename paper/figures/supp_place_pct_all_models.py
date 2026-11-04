"""Supp (supp_place_pct_all_models): like supp_place_pct, but with all three
models sharing one set of axes instead of just IM/PDM. percent_place_cells is
the one swept axis every model's grid actually has in common (IM/PDM sweep
task weight x task-responsive% x place%; arousal_mediated sweeps
task-responsive% x holdover x place% -- see robustness.py's _MODEL_AXES), so
it's the only axis a single shared-axes comparison across all three models
can be sliced on. IM/PDM are shown at the two task-weight grid points nearest
bioreal's still-provisional balance=0.5 (0.4 and 0.6, one per panel, matching
supp_place_pct.py); arousal_mediated has no task-weight axis at all, so its
slice (fixed at holdover=1.0, matching IM/PDM's own fixed holdover in
robustness.py) is identical in both panels -- that's a real modeling fact,
not a plotting artifact, and is called out in the caption.

2026-10-02: place_dependent/arousal_mediated read their _092926 tags (post
velocity-gain-fix, commit e1e4496). 2026-10-03: independent_sweep_092926
finished (216/216) and replaces independent_sweep_080726 here too -- see
robustness.py's module docstring for the three-sweep policy this follows.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from paper.figlib.io import FigureInputs
from paper.figlib.panels.decoding import draw_param_lines, param_slice

FIGURE_ID = "supp_place_pct_all_models"

MODELS = ("independent", "place_dependent", "arousal_mediated")
TAGS = {
    "independent": "independent_sweep_092926",
    "place_dependent": "place_dependent_sweep_092926",
    "arousal_mediated": "arousal_mediated_sweep_092926",
}
NEAREST_BALANCE_VALUES = (0.4, 0.6)  # grid points nearest bioreal's provisional balance=0.5
BIOREAL_PLACE_PCT = 0.2
ADM_FIXED_HOLDOVER = 1.0  # matches robustness.py's fixed holdover for IM/PDM's own grid


def _slice_for_model(model: str, decoding, balance: float):
    if model == "arousal_mediated":
        fixed = {"percent_task_responsive_cells": 0.4, "holdover": ADM_FIXED_HOLDOVER}
    else:
        fixed = {"percent_task_responsive_cells": 0.4, "percent_task_in_response": balance}
    return param_slice(decoding, param="percent_place_cells", fixed=fixed)


def build(inputs: FigureInputs, style) -> plt.Figure:
    style.apply_rc_params()
    fig, axes = plt.subplots(1, len(NEAREST_BALANCE_VALUES),
                              figsize=(style.figure_width_inches("double"), 3.8), sharey=True)

    for i, (ax, balance) in enumerate(zip(axes, NEAREST_BALANCE_VALUES)):
        slices = {model: _slice_for_model(model, inputs.decoding[TAGS[model]], balance) for model in MODELS}
        draw_param_lines(ax, "percent_place_cells", slices, colors=style.MODEL_COLORS,
                          display_names=style.MODEL_DISPLAY_NAMES, marker_value=BIOREAL_PLACE_PCT,
                          marker_label=f"Main-text setting ({BIOREAL_PLACE_PCT * 100:g}%)",
                          ylabel=f"Task-stage decoding accuracy ({style.direction_display_name('A->B')})",
                          chance_level=style.TASK_CHANCE_LEVEL, show_legend=(i == 0))
        ax.set_title(f"{style.PARAM_DISPLAY_NAMES['percent_task_in_response']} = {balance:g}", fontsize=9)

    fig.tight_layout()

    # Named panels for build.py's per-panel export (build/panels/supp_place_pct_all_models/<name>.*).
    fig.panel_axes = {f"balance_{balance:g}": ax for ax, balance in zip(axes, NEAREST_BALANCE_VALUES)}

    return fig
