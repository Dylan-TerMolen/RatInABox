"""Fig 3 (position_decoding): all models carry spatial information within an
environment; a decoder trained in one environment fails in the other. Shown
as error (cm) vs. percent_task_in_response (balance), not a flat aggregate
bar per direction: in-task within-env error rises monotonically with balance
(higher balance means more task-driven, less place-driven firing for
task-responsive cells, which directly degrades position decoding) --
averaging across that range would misrepresent it entirely (see 2026-09-25
chat; contrast task_decoding_by_balance.py, whose accuracy is flat across
the same axis). Out-of-task error stays comparatively flat across the same
range.

2026-10-02: R^2 is no longer plotted anywhere in this pipeline -- place
decoding is reported in mean centimeters of error only (lower is better;
converted at ingestion from the decoder's raw meters-native output, see
produce/pull_decoding.py's _CM_KINDS note). This figure used to show a
third R^2 panel per row; it's now two cm-error panels (within-env, cross-env).

2026-10-03: IM panel now built from independent_sweep_092926 (not the old
dedicated bioreal-take-3 run, which predates the 2026-09-29 velocity-gain fix
-- see robustness.py's module docstring), restricted via param_slice's
`fixed` to bioreal's real percentages (BIOREAL_FIXED: percent_place_cells=0.2,
percent_task_responsive_cells=0.4). Unlike bioreal-take-3's dedicated holdover
x balance grid, this slice has holdover fixed at 1.0 (independent_sweep_092926's
main grid doesn't sweep holdover) -- "averaged over holdover" above no longer
applies to this slice's own data, though the balance-vs-flat-aggregation
argument itself still holds. All 6 balance values at this slice are complete
(confirmed 2026-10-03).

place_dependent/arousal_mediated omitted: no equivalent bioreal-percentage
decoding run exists for them yet -- MODEL_TAGS below is written so adding
either model is a one-line addition (here + manifest.yaml's inputs.decoding)
once its tag is pulled, not a rewrite (rule 8: ship what exists). supp_position_with_task
folded into panel a per that same decision -- not a separate figure. B->A
direction not shown -- the decoder has no B->A output yet (open question).

2026-10-05: place_dependent/arousal_mediated added (2026-10-05 request: show
all three models' success/failure, not just IM). This figure plots error
AGAINST percent_task_in_response (balance) as a real
functional dependence, not an aggregate -- and arousal_mediated has no
balance parameter at all (its sweep varies holdover instead, see
CLAUDE.md/robustness.py). MODEL_TAGS is now model -> (tag, x_param) so each
model's row plots against whichever axis it actually sweeps: IM/PDM against
balance, arousal_mediated against holdover, both still fixed at bioreal's
place=0.2/task-responsive=0.4 point via BIOREAL_FIXED. draw_param_lines
already picks the x-axis label from style.PARAM_DISPLAY_NAMES per `param`, so
no panel-label changes were needed beyond this.

2026-10-03: the cross-env panel also draws each task state's shuffled A→B
baseline as a dashed horizontal reference line, in the same color as that
state's solid line -- without it, a reader has no way to tell how much of
the ~23-31cm cross-env error is a real transfer failure vs. just structural
(env B is physically smaller than env A, so even a shuffled/uninformative
decoder's error there isn't the same number it would be in env A).
("Shuffled floor" renamed to "Shuffled baseline" 2026-10-04.)

2026-10-04: the gray parameter footnote (bioreal_params_footnote) moved out
of the image entirely -- it's now in captions/position_decoding.md instead;
the bold headline (bioreal_headline) stays. Both panels' legends replaced
with one shared fig.legend above both panels (previously each panel drew its
own, anchored outside its own axes to the right, which pushed the two-panel
layout visibly off-center).

2026-10-05: two fixes requested after the 3-model version landed. (1) The
within-env panels never drew a shuffled baseline at all -- only the cross-env
panel did (shuffled_reference_value's A->A-direction floor was computed but
never plotted). Now drawn on ax_within the same way, same dashed-line
convention, direction="A->A" (there's no separate shuffB->B kind -- A->A's
shuffled floor already stands in for within-env chance generally, same
convention direction_stats/draw_direction_bars use). (2) All 6 panels used to
auto-scale to their own data, which made cross-model comparison -- the
figure's whole point -- hard to read off the y-axis directly: PDM/ADM's
within-env range (~10-18cm) and IM's (~12-26cm) looked equally "large" on
their own independent axes. Y-limits are now shared across all 6 panels (one
global range, not just per-column), so a glance at the axis labels alone
shows IM's cross-env error really is worse than PDM/ADM's within-env error,
not just an artifact of independent scaling.

2026-10-05 (later same day): reverted arousal_mediated's holdover-as-x-axis.
Plotting its row against holdover looked like the same kind of line IM/PDM's
balance rows show, but holdover isn't an apples-to-apples axis against
balance -- it's a completely different parameter (% of task cells carried
over from env A to env B) with no shared meaning or scale, so lining the two
up side by side implied a comparability that isn't there. arousal_mediated's
row now shows ONE point per task state instead, at a single labeled
x-position, not a line across holdover values. MODEL_TAGS' x_param is now
None for arousal_mediated as the signal to use this single-point path
instead of draw_param_lines.

2026-10-05 (later still): that single point was computed as an aggregate
across arousal_mediated's full holdover sweep (direction_stats with no
holdover filter) -- wrong per the same request that asked for the
holdover-as-x-axis to be reverted: "it should not aggregate across holdover
anywhere." Uses the single real grid point at holdover=ADM_HOLDOVER=1.0
instead (bioreal's own chosen holdover value, paper/params/bioreal.yaml),
matching IM/PDM's own fixed holdover=1.0 -- the same convention
supp_place_pct_all_models.py's ADM_FIXED_HOLDOVER already uses. The shuffled
baseline for arousal_mediated's row is now computed at that same fixed point
too (previously it was aggregated across holdover like the real value was).
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from paper.figlib.io import FigureInputs, load_param_set
from paper.figlib.panels.decoding import (
    direction_stats, draw_param_lines, extend_ylim_for_floors, param_slice, share_ylim, shuffled_reference_value,
)

FIGURE_ID = "position_decoding"

# model -> (its bioreal-percentage decoding tag, the param its row plots
# against, or None). IM/PDM sweep balance; arousal_mediated has no balance
# parameter -- None means "no comparable x-axis, show the single real grid
# point at ADM_HOLDOVER instead" (see module docstring and
# _draw_fixed_point_panel).
MODEL_TAGS = {
    "independent": ("independent_sweep_092926", "percent_task_in_response"),
    "place_dependent": ("place_dependent_sweep_092926", "percent_task_in_response"),
    "arousal_mediated": ("arousal_mediated_sweep_092926", None),
}
BIOREAL_FIXED = {"percent_place_cells": 0.2, "percent_task_responsive_cells": 0.4}
# bioreal's own holdover value (paper/params/bioreal.yaml) -- the single grid
# point arousal_mediated's row uses, matching IM/PDM's own fixed holdover=1.0
# (see supp_place_pct_all_models.py's identical ADM_FIXED_HOLDOVER convention).
ADM_HOLDOVER = 1.0
BIOREAL_PARAMS = load_param_set("bioreal")
TASK_STATES = ("in_task", "out_of_task")
CM_YLABEL = "error (cm, lower = better)"


def _task_state_slices(decoding, *, param: str, direction: str) -> dict[str, object]:
    return {
        state: param_slice(decoding, param=param, fixed=BIOREAL_FIXED,
                            direction=direction, kind=f"place_cm_{state}")
        for state in TASK_STATES
    }


def _shared_legend_handles(style) -> list:
    handles = [Line2D([0], [0], color=style.TASK_STATE_COLORS[state], marker="o", markersize=4,
                       label=style.TASK_STATE_LABELS[state])
               for state in TASK_STATES]
    handles += [Line2D([0], [0], color=style.TASK_STATE_COLORS[state], linestyle=":", linewidth=1.3,
                        label=f"Shuffled baseline ({style.TASK_STATE_LABELS[state].lower()})")
                for state in TASK_STATES]
    return handles


def _draw_fixed_point_panel(ax, decoding, *, direction: str, ylabel: str, style) -> None:
    """One point per task state at the single real grid point
    holdover=ADM_HOLDOVER (not an aggregate across holdover) -- used when
    the model's remaining swept axis isn't a meaningful x-axis to put next
    to another model's (arousal_mediated's holdover vs. IM/PDM's balance,
    see module docstring). Offsets the two task states slightly so their
    error bars don't overlap, same colors/markers as the line-chart panels
    use for in-task/out-of-task."""
    offsets = {"in_task": -0.15, "out_of_task": 0.15}
    fixed = {**BIOREAL_FIXED, "holdover": ADM_HOLDOVER}
    for state in TASK_STATES:
        stats = direction_stats(decoding, kind=f"place_cm_{state}", fixed=fixed)
        row = stats.set_index("direction").loc[direction]
        ax.errorbar([offsets[state]], [row["mean"]], yerr=[row["ci"]], color=style.TASK_STATE_COLORS[state],
                    marker="o", markersize=5, capsize=3, zorder=2)
    ax.set_xlim(-0.5, 0.5)
    ax.set_xticks([0], [f"Holdover = {ADM_HOLDOVER * 100:g}%"])
    ax.set_ylabel(ylabel)


def _draw_shuffled_baselines(ax, decoding, *, direction: str, fixed: dict, style) -> list[float]:
    """Dashed shuffled-baseline line per task state (in-task/out-of-task),
    same color as that state's solid line -- `direction` is the real
    direction being compared against ("A->A" for a within-env panel, "A->B"
    for cross-env); shuffled_reference_value prepends "shuff" itself. `fixed`
    must match whatever fixed point the real values on this panel were
    computed at (BIOREAL_FIXED for IM/PDM, BIOREAL_FIXED + holdover=ADM_HOLDOVER
    for arousal_mediated) -- a mismatched fixed point would compare the real
    line/point against a shuffled floor from a different operating point.
    Returns the floor values so the caller can fold them into its own
    y-limits (see extend_ylim_for_floors)."""
    floors = [shuffled_reference_value(decoding, kind=f"place_cm_{state}", direction=direction, fixed=fixed)
              for state in TASK_STATES]
    for state, floor in zip(TASK_STATES, floors):
        ax.axhline(floor, color=style.TASK_STATE_COLORS[state], linestyle=":", linewidth=1.3, alpha=0.8)
    return floors


def build(inputs: FigureInputs, style) -> plt.Figure:
    style.apply_rc_params()
    n_models = len(MODEL_TAGS)
    fig, axes = plt.subplots(n_models, 2, squeeze=False,
                              figsize=(style.figure_width_inches("double"), 3.8 * n_models))

    panel_axes = {}
    all_axes = []
    for row, (model, (tag, x_param)) in enumerate(MODEL_TAGS.items()):
        decoding = inputs.decoding[tag]
        ax_within, ax_cross = axes[row]
        row_prefix = f"{style.MODEL_DISPLAY_NAMES[model]}: " if n_models > 1 else ""
        # The shuffled baseline must come from the same fixed point as the
        # real values on this row -- BIOREAL_FIXED for IM/PDM's balance
        # sweep, + holdover=ADM_HOLDOVER for arousal_mediated's single point.
        fixed = BIOREAL_FIXED if x_param is not None else {**BIOREAL_FIXED, "holdover": ADM_HOLDOVER}

        if x_param is None:
            _draw_fixed_point_panel(ax_within, decoding, direction="A->A", ylabel=f"A→A {CM_YLABEL}", style=style)
        else:
            draw_param_lines(ax_within, x_param,
                              _task_state_slices(decoding, param=x_param, direction="A->A"),
                              colors=style.TASK_STATE_COLORS, display_names=style.TASK_STATE_LABELS,
                              ylabel=f"A→A {CM_YLABEL}", show_legend=False)
        within_floors = _draw_shuffled_baselines(ax_within, decoding, direction="A->A", fixed=fixed, style=style)
        extend_ylim_for_floors(ax_within, within_floors)
        ax_within.set_title(f"{row_prefix}{style.WITHIN_ENV_LABEL}", fontsize=9)

        if x_param is None:
            _draw_fixed_point_panel(ax_cross, decoding, direction="A->B", ylabel=f"A→B {CM_YLABEL}", style=style)
        else:
            draw_param_lines(ax_cross, x_param,
                              _task_state_slices(decoding, param=x_param, direction="A->B"),
                              colors=style.TASK_STATE_COLORS, display_names=style.TASK_STATE_LABELS,
                              ylabel=f"A→B {CM_YLABEL}", show_legend=False)
        cross_floors = _draw_shuffled_baselines(ax_cross, decoding, direction="A->B", fixed=fixed, style=style)
        extend_ylim_for_floors(ax_cross, cross_floors)
        ax_cross.set_title(f"{row_prefix}{style.CROSS_ENV_LABEL}", fontsize=9)

        panel_axes.update({f"{model}_within": ax_within, f"{model}_cross": ax_cross})
        all_axes += [ax_within, ax_cross]

    share_ylim(all_axes)

    fig.suptitle(style.bioreal_headline(BIOREAL_PARAMS, decoding_label="Position decoding"),
                 fontsize=14, fontweight="bold")
    fig.legend(handles=_shared_legend_handles(style), loc="upper center", bbox_to_anchor=(0.5, 0.9),
               ncol=4, fontsize=7, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.84))

    # Named panels for build.py's per-panel export (build/panels/position_decoding/<name>.*).
    fig.panel_axes = panel_axes

    return fig
