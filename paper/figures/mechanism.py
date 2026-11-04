"""Fig 5 (mechanism): why only IM generalizes -- one task-responsive place
cell per model, trial-averaged firing rate in env A vs env B, plus a 4th
panel (population_stability, added 2026-09-29 review item 7) showing that
this isn't just one anecdotal cell: the per-model distribution of every
place+task-responsive cell's own A-vs-B response correlation.

2026-10-04: added panel letters; env A/B legend is now one shared
fig.legend() above all four panels (previously repeated -- deduped to just
the first panel in an earlier pass, but still per-panel-anchored) using
neutral gray proxies, since env A/B are now distinguished by line style
(solid/dashed) rather than color -- see panels/mechanism.py's own docstring
for why (its blue/orange would otherwise clash with this figure's own
model-color coding).
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from paper.figlib.io import FigureInputs
from paper.figlib.panels.mechanism import population_stability, single_cell_firing_A_vs_B
from paper.figlib.panels.setup import panel_label

FIGURE_ID = "mechanism"

MODELS = ("independent", "place_dependent", "arousal_mediated")
PANEL_LETTERS = ("a", "b", "c", "d")


def build(inputs: FigureInputs, style) -> plt.Figure:
    style.apply_rc_params()
    sims = {model: inputs.sim[f"bioreal-{model}"] for model in MODELS}

    fig, axes = plt.subplots(1, 4, figsize=(style.figure_width_inches("double"), 3.6), sharey=False)
    trace_axes = axes[:3]
    for ax, model in zip(trace_axes, MODELS):
        single_cell_firing_A_vs_B(ax, sims[model], model)

    ax_stability = axes[3]
    population_stability(ax_stability, sims, MODELS)
    for ax, letter in zip(axes, PANEL_LETTERS):
        panel_label(ax, letter)

    legend_handles = [Line2D([0], [0], color="#4d4d4d", linestyle=style.ENV_LINESTYLES[env],
                              label=style.env_label(env))
                       for env in ("A", "B")]
    fig.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=7,
               frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.92))

    # Named panels for build.py's per-panel export (build/panels/mechanism/<name>.*).
    fig.panel_axes = dict(zip(MODELS, trace_axes))
    fig.panel_axes["population_stability"] = ax_stability

    return fig
