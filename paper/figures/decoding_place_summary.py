"""Position decoding error -- aggregated across every combo x iteration in
each model's completed parameter sweep. See decoding_task_summary.py for the
task-decoding equivalent and the same sweep-wide (not single bioreal point)
caveat.

2026-10-03 three-sweep policy (see robustness.py's module docstring):
independent_sweep_092926, place_dependent_sweep_092926,
arousal_mediated_sweep_092926. independent_sweep_092926 finished the same day
(216/216 combos) -- partial_sweep_note (same "place everything we have, mark
it as partial" treatment as place_robustness_3d_within/cross) is kept as a
safety net for any future in-flight tag, but doesn't fire for any of the
three current tags (previously independent read independent_sweep_080726
here and showed as fully unavailable, since that tag predates this split
entirely).

Reported as mean position error in centimeters, split by task state (in-task
vs. out-of-task) -- *not* R^2 -- since cm error is the metric this regen was
asked for and lower is better here (opposite sense from every other decoding
panel in this pipeline, which plots R^2/accuracy where higher is better; the
ylabel says so explicitly rather than relying on a reader to remember).
produce/pull_decoding.py converts the raw meters-native error to centimeters
at ingestion (see its _CM_KINDS note), so no conversion happens here.

2026-10-04: one shared fig.legend() above both panels instead of a single
remaining per-panel-anchored legend (same fix as decoding_task_summary.py).
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from paper.figlib.io import DecodingArtifact, FigureInputs
from paper.figlib.panels.decoding import COMBO_PARAMS, direction_stats, draw_direction_bars, partial_sweep_note

FIGURE_ID = "decoding_place_summary"

# model -> its approved decoding tag (2026-10-03 policy -- see module docstring).
MODEL_TAGS = {
    "independent": "independent_sweep_092926",
    "place_dependent": "place_dependent_sweep_092926",
    "arousal_mediated": "arousal_mediated_sweep_092926",
}

CM_KINDS = ("place_cm_in_task", "place_cm_out_of_task")
CM_YLABEL = "Mean position error (cm, lower = better)"


def _has_cm_split(decoding: DecodingArtifact) -> bool:
    return all((decoding.scores["kind"] == kind).any() for kind in CM_KINDS)


def _combo_count(decoding: DecodingArtifact, kind: str) -> int:
    df = decoding.scores
    combo_cols = [c for c in COMBO_PARAMS if df[c].notna().any()]
    return int(df[df["kind"] == kind].drop_duplicates(subset=combo_cols).shape[0])


def build(inputs: FigureInputs, style) -> plt.Figure:
    style.apply_rc_params()
    decodings = {model: inputs.decoding[tag] for model, tag in MODEL_TAGS.items()}
    available = {model: d for model, d in decodings.items() if _has_cm_split(d)}
    missing = [model for model in MODEL_TAGS if model not in available]

    stats_in_task = {model: direction_stats(d, kind="place_cm_in_task") for model, d in available.items()}
    stats_out_of_task = {model: direction_stats(d, kind="place_cm_out_of_task") for model, d in available.items()}

    fig, (ax_in, ax_out) = plt.subplots(1, 2, figsize=(style.figure_width_inches("double"), 3.6), sharey=True)
    draw_direction_bars(ax_in, stats_in_task, model_colors=style.MODEL_COLORS,
                         model_display_names=style.MODEL_DISPLAY_NAMES, ylabel=CM_YLABEL, show_legend=False)
    ax_in.set_title(style.TASK_STATE_LABELS["in_task"], fontsize=9)

    draw_direction_bars(ax_out, stats_out_of_task, model_colors=style.MODEL_COLORS,
                         model_display_names=style.MODEL_DISPLAY_NAMES, ylabel=CM_YLABEL, show_legend=False)
    ax_out.set_title(style.TASK_STATE_LABELS["out_of_task"], fontsize=9)

    legend_handles = [Patch(facecolor=style.MODEL_COLORS[m], label=style.MODEL_DISPLAY_NAMES[m])
                       for m in available]
    fig.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, 0.86), ncol=3, fontsize=7,
               frameon=False)

    title = "Position decoding across each model's completed parameter sweep"
    combo_counts = {m: _combo_count(decodings[m], "place_cm_in_task") for m in available}
    partial = {m: partial_sweep_note(n) for m, n in combo_counts.items() if partial_sweep_note(n)}
    if partial:
        names = ", ".join(f"{style.MODEL_DISPLAY_NAMES[m]}{note}" for m, note in partial.items())
        title += f"\n{names}"
    if missing:
        names = ", ".join(style.MODEL_DISPLAY_NAMES[m] for m in missing)
        tags = ", ".join(sorted({MODEL_TAGS[m] for m in missing}))
        title += f"\nData not available: {names} ({tags} predates the in/out-of-task cm-error split)"
    fig.suptitle(title, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.8))

    # Named panels for build.py's per-panel export (build/panels/decoding_place_summary/<name>.*).
    fig.panel_axes = {"a": ax_in, "b": ax_out}

    return fig
