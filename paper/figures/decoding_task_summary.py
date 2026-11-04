"""Task (CS/US) decoding performance -- all three models -- aggregated across
every combo x iteration in each model's completed parameter sweep (tags in
manifest.yaml, not a single fixed operating point). Draft `cross_env`/
manifest `task_decoding_by_balance` asks for the `bioreal` point
specifically; this is the sweep-wide answer from each model's approved
sweep tag.

2026-10-02: place_dependent_sweep_092926/arousal_mediated_sweep_092926
post-date the 2026-09-29 velocity-gain fix (commit e1e4496); independent's
own _092926 re-run was still in flight (128/216 logs) as of this date, so it
read its original _080726 tag instead -- a real vintage mismatch across
models, noted here and in the caption at the time.

2026-10-03: independent_sweep_092926 finished (216/216 logs) and replaces
independent_sweep_080726 here -- all three models now read their post
velocity-gain-fix tags, so the vintage mismatch above no longer applies.

2026-10-04: one shared fig.legend() above both panels (models + chance line)
instead of a single remaining per-panel-anchored legend (the duplicate on
the second panel was already removed in an earlier pass, but the one
survivor was still positioned outside its own panel's axes rather than as a
true figure-level legend).
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from paper.figlib.io import FigureInputs
from paper.figlib.panels.decoding import direction_stats, draw_direction_bars

FIGURE_ID = "decoding_task_summary"

# model -> its approved decoding tag (2026-10-02 policy -- see module docstring).
MODEL_TAGS = {
    "independent": "independent_sweep_092926",
    "place_dependent": "place_dependent_sweep_092926",
    "arousal_mediated": "arousal_mediated_sweep_092926",
}


def _shared_legend_handles(style) -> list:
    handles = [Patch(facecolor=style.MODEL_COLORS[m], label=style.MODEL_DISPLAY_NAMES[m]) for m in MODEL_TAGS]
    handles.append(Line2D([0], [0], color="black", linestyle="--", linewidth=0.8, label=style.CHANCE_LABEL))
    return handles


def build(inputs: FigureInputs, style) -> plt.Figure:
    style.apply_rc_params()
    stats = {model: direction_stats(inputs.decoding[tag], kind="task") for model, tag in MODEL_TAGS.items()}
    accuracy_kwargs = dict(ylabel="Task-stage decoding accuracy", chance_level=style.TASK_CHANCE_LEVEL,
                            show_legend=False)

    fig, (ax_within, ax_cross) = plt.subplots(1, 2, figsize=(style.figure_width_inches("double"), 3.6))
    draw_direction_bars(ax_within, stats, model_colors=style.MODEL_COLORS,
                         model_display_names=style.MODEL_DISPLAY_NAMES,
                         directions=("A->A", "B->B", "shuffA->A"), **accuracy_kwargs)
    ax_within.set_title(style.WITHIN_ENV_LABEL, fontsize=9)

    draw_direction_bars(ax_cross, stats, model_colors=style.MODEL_COLORS,
                         model_display_names=style.MODEL_DISPLAY_NAMES,
                         directions=("A->B", "shuffA->B"), **accuracy_kwargs)
    ax_cross.set_title(style.CROSS_ENV_LABEL, fontsize=9)

    fig.legend(handles=_shared_legend_handles(style), loc="upper center", bbox_to_anchor=(0.5, 0.86),
               ncol=4, fontsize=7, frameon=False)
    fig.suptitle("Task decoding across each model's completed parameter sweep "
                 "(independent: pre-velocity-gain-fix tag)", fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.8))

    # Named panels for build.py's per-panel export (build/panels/decoding_task_summary/<name>.*).
    fig.panel_axes = {"a": ax_within, "b": ax_cross}

    return fig
