"""Panels for the `models` figure (draft Fig 2): one schematic per model, the
raw tEBC response types IM/PDM share, each model's combined place+task
response, and real simulated-data rasters. Response math ported from
ratinabox/hsw/notebooks/figures.ipynb cells 12-37 -- same functions, same
constants -- reconstructed rather than copy-pasted where the notebook's own
version was incomplete (a few cells there stop mid-function; this is
sandbox/exploratory code, not meant to run standalone). Renamed the
notebook's legacy "Additive"/"Dependent" labels to IM/PDM per CLAUDE.md.
"""
from __future__ import annotations

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch

from ratinabox.hsw.arousal_mediated_model.tebc_response2 import (
    type_one_response,
    type_two_response,
    type_three_response,
    type_four_response,
)
from ratinabox.hsw.tebc_response import (
    CS_duration,
    DEFAULT_TASK_TYPES,
    TRIAL_PERIOD,
    US_duration,
    US_start_time,
    response_profiles,
)

from paper.figlib import style
from paper.figlib.io import SimArtifact
from paper.figlib.panels.setup import cs_onset_steps

TASK_MAX_FR = 12.0  # matches CombinedPlaceTebc place_cells_params["max_fr"]
TIME_SINCE_CS = np.linspace(-1, 2, 300)

FIELD_STATE_COLORS = style.FIELD_STATE_COLORS  # {"in_field", "near_field_edge", "out_of_field"}

# Reference-line colors for the raw/theoretical response panels below --
# reuse PHASE_COLORS' blue/orange (CS onset ~ tone start, US end ~ shock) and
# its aqua for "rebound" (no existing name fits; same validated triple, no
# new hex). 2026-09-25: replaces hardcoded "g"/"r"/"orange".
CS_ONSET_COLOR = style.PHASE_COLORS["tone"]
US_END_COLOR = style.PHASE_COLORS["shock"]
REBOUND_COLOR = style.PHASE_COLORS["trace"]

TRACE_SHADE_COLOR = "gray"
TRACE_SHADE_ALPHA = 0.12
_TRACE_LABEL = f"Trace interval ({style.ms_range_label(*style.PHASE_MS_RANGES['trace'])})"


def _trace_interval_handle() -> Patch:
    """Legend handle for the gray axvspan marking the trace interval (2026-10-23
    review: "say what the shaded region is" -- every panel below drew it but
    none said what it was)."""
    return Patch(facecolor=TRACE_SHADE_COLOR, alpha=TRACE_SHADE_ALPHA, label=_TRACE_LABEL)


def place_firingrate(distance: np.ndarray, width: float, max_fr: float = TASK_MAX_FR) -> np.ndarray:
    """Gaussian place-cell firing rate as a function of distance from the
    field centre -- ratinabox.Neurons.PlaceCells.get_state's own formula."""
    return np.exp(-(distance ** 2) / (2 * width ** 2)) * max_fr


# --- (a) model schematics ---------------------------------------------------

_SCHEMATIC_TEXT = {
    "independent": "task response\n(fixed amplitude)\n+\nplace response\n→ at any location",
    "place_dependent": "task response\n(amplitude = place rate)\n+\nplace response\n→ only inside field",
    "arousal_mediated": "task response\n(gated by field × movement)\n+\nplace response\n→ 4 states",
}


_SCHEMATIC_BOX_FACECOLOR = "#f0f0f0"  # neutral gray, not per-model color (2026-10-23 review:
_SCHEMATIC_BOX_EDGECOLOR = "#4d4d4d"  # "remove colors from the models" -- the model identity is
                                       # already carried by the title text, not needed again here)


def model_schematic(ax, model_type: str) -> None:
    """One small annotated box per model -- how task, place, and (for ADM)
    movement combine. New panel, not ported from the notebook."""
    box = FancyBboxPatch((0.05, 0.1), 0.9, 0.8, boxstyle="round,pad=0.02",
                          facecolor=_SCHEMATIC_BOX_FACECOLOR,
                          edgecolor=_SCHEMATIC_BOX_EDGECOLOR, linewidth=1.2,
                          transform=ax.transAxes)
    ax.add_patch(box)
    ax.text(0.5, 0.5, _SCHEMATIC_TEXT[model_type], transform=ax.transAxes,
            ha="center", va="center", fontsize=7)
    ax.set_title(style.MODEL_DISPLAY_NAMES[model_type], fontsize=9)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


# --- (b) raw response types (IM/PDM share one set) --------------------------

def raw_response_types(fig, cell_types=DEFAULT_TASK_TYPES, max_fr: float = TASK_MAX_FR):
    """Each default response type on its own, no place-firing combination --
    IM and PDM draw from the literal same tebc_response.response_profiles, so
    there's one grid, not two."""
    us_end = US_start_time + US_duration
    axes = fig.subplots(1, len(cell_types), sharey=True)
    for cell_type, ax in zip(cell_types, np.atleast_1d(axes)):
        response_func = response_profiles[cell_type]["response_func"]
        response = np.array([response_func(t, max_fr) for t in TIME_SINCE_CS])
        ax.plot(TIME_SINCE_CS, response, color="C0")
        ax.axvspan(CS_duration, US_start_time, color=TRACE_SHADE_COLOR, alpha=TRACE_SHADE_ALPHA)
        ax.axvline(0, color=CS_ONSET_COLOR, linestyle=":", alpha=0.6, label="CS onset")
        ax.axvline(us_end, color=US_END_COLOR, linestyle=":", alpha=0.6, label="US end")
        ax.axvline(TRIAL_PERIOD, color=REBOUND_COLOR, linestyle="--", alpha=0.5,
                   label=f"Response reset ({TRIAL_PERIOD:g} s)")
        ax.set_ylim(0, max_fr + 1)
        ax.set_title(f"Type {cell_type}", fontsize=8)
        ax.set_xlabel("Time since CS (s)")
    np.atleast_1d(axes)[0].set_ylabel("Firing rate (Hz)")
    handles, labels = np.atleast_1d(axes)[0].get_legend_handles_labels()
    np.atleast_1d(axes)[0].legend(handles=handles + [_trace_interval_handle()], fontsize=6, loc="upper right")
    return axes


# --- (c)/(d) IM/PDM combined place+task response grid ------------------------

def _combined_firingrate(model_type: str, cell_type: int, time_since_cs: np.ndarray,
                          distance: float, width: float, balance: float, max_fr: float) -> np.ndarray:
    """balance * task_fr + (1 - balance) * place_fr. IM: task amplitude is a
    fixed max_fr regardless of place firing. PDM: task amplitude *is* the
    cell's own (distance-dependent) place firing rate -- so it collapses
    toward 0 out of field. This is CombinedPlaceTebc._task_amplitudes'
    actual distinction between the two models."""
    response_func = response_profiles[cell_type]["response_func"]
    place_fr = place_firingrate(np.asarray(distance), width, max_fr)
    task_amplitude = max_fr if model_type == "independent" else place_fr
    task_fr = np.array([response_func(t, task_amplitude) for t in time_since_cs])
    return balance * task_fr + (1 - balance) * place_fr


def field_response_grid(fig, model_type: str, *, width: float, cell_types=DEFAULT_TASK_TYPES,
                         balance: float = 0.5, max_fr: float = TASK_MAX_FR):
    """One panel per default cell type, each showing the combined response at
    3 distances from the field centre: in field (0), near the field edge (one
    width out), and out of field (1 m). For PDM every "out of field" trace is
    ~0 by construction (task amplitude *is* the ~0 place rate there) --
    plotted with a thicker dashed line (not solid, like the other two
    distances) so it stays visible sitting right on the x-axis instead of
    disappearing into it (2026-10-04 review)."""
    field_distances = (
        (style.FIELD_STATE_LABELS["in_field"], 0.0, FIELD_STATE_COLORS["in_field"], "-", 1.5),
        (style.FIELD_STATE_LABELS["near_field_edge"], width, FIELD_STATE_COLORS["near_field_edge"], "-", 1.5),
        (style.FIELD_STATE_LABELS["out_of_field"], 1.0, FIELD_STATE_COLORS["out_of_field"], "--", 2.5),
    )
    axes = fig.subplots(1, len(cell_types), sharey=True)
    for cell_type, ax in zip(cell_types, np.atleast_1d(axes)):
        for label, distance, color, linestyle, linewidth in field_distances:
            response = _combined_firingrate(model_type, cell_type, TIME_SINCE_CS, distance,
                                             width, balance, max_fr)
            ax.plot(TIME_SINCE_CS, response, color=color, linestyle=linestyle, linewidth=linewidth, label=label)
        ax.set_ylim(0, max_fr + 2)
        ax.set_title(f"Type {cell_type}", fontsize=8)
        ax.set_xlabel("Time since CS (s)")
    np.atleast_1d(axes)[0].set_ylabel("Firing rate (Hz)")
    np.atleast_1d(axes)[0].legend(fontsize=6, loc="upper right")
    return axes


# --- (e) arousal-mediated 2x2 (field x running) grid -------------------------

RIPPLE_SCALE = TASK_MAX_FR / 30  # matches TEBC._calculate_task_firing_rates' ripple_scale
SITTING_IN_FIELD_BASELINE_HZ = 3.0  # matches Fig 3B's own pre-trial rate (Shan et al. 2016)

# (row_label, col_label, response_func, arg, baseline_reference) in Shan et al. 2016
# Fig 3A/B's own panel order: rows = in/out of place field, columns = moving/not
# moving (2026-10-03: "running"/"sitting" renamed to match the Results text's own
# "moving"/"not moving" terminology -- running_at_onset etc. stay as internal
# variable names, only the displayed labels changed).
# response_func returns a DELTA added to the cell's ongoing firing rate (matches
# TEBC._calculate_task_firing_rates: self.firingrate += task_firing_rates), not a
# total rate -- baseline_reference is that ongoing rate, added back here to plot the
# actual total a cell would show. type_one/type_three are baseline-relative internally
# (their own arg *is* that reference); type_two/four's near-zero out-of-field local
# rate is negligible against ripple_scale, so no addition is needed for them.
_AROUSAL_LAYOUT = [
    [(style.FIELD_STATE_LABELS["in_field"], "Moving", type_one_response, TASK_MAX_FR, TASK_MAX_FR),
     (style.FIELD_STATE_LABELS["in_field"], "Not moving", type_three_response,
      SITTING_IN_FIELD_BASELINE_HZ, SITTING_IN_FIELD_BASELINE_HZ)],
    [(style.FIELD_STATE_LABELS["out_of_field"], "Moving", type_two_response, RIPPLE_SCALE, 0.0),
     (style.FIELD_STATE_LABELS["out_of_field"], "Not moving", type_four_response, RIPPLE_SCALE, 0.0)],
]


def arousal_2x2_grid(fig):
    """(in/out of field) x (moving/not moving) -- layout mirrors Shan et al.
    2016 Fig 3A/B so shapes can be compared by eye. type_two/four_response
    scale off RIPPLE_SCALE (population peak per-frame rate), not a local
    place-firing quantity -- see CLAUDE.md's arousal_mediated_shan2016 note.
    Firing rate is clipped at 0 (the noise term in type_two/four_response can
    otherwise dip slightly negative, e.g. -0.04 Hz -- not a physical rate).
    All 4 axes share one y-axis, scaled to the grid's own global max (2026-10-23
    review: "axis should be standardized across all 4 plots" -- they previously
    each autoscaled to their own data, so the ~1.8 Hz in-field/moving modulation
    looked the same size on screen as the near-flat ~0.1 Hz out-of-field
    panels; a shared scale is what actually lets the 4 be compared by eye)."""
    us_end = US_start_time + US_duration
    responses = [
        [np.clip(baseline_reference + np.array([response_func(t, arg) for t in TIME_SINCE_CS]), 0, None)
         for (_, _, response_func, arg, baseline_reference) in row_panels]
        for row_panels in _AROUSAL_LAYOUT
    ]
    shared_ymax = max(response.max() for row in responses for response in row) * 1.05

    axes = fig.subplots(2, 2, sharex=True, sharey=True)
    for row, row_panels in enumerate(_AROUSAL_LAYOUT):
        for col, (row_label, col_label, *_rest) in enumerate(row_panels):
            ax = axes[row, col]
            ax.axvspan(CS_duration, US_start_time, color=TRACE_SHADE_COLOR, alpha=TRACE_SHADE_ALPHA)
            ax.axvline(0, color=CS_ONSET_COLOR, linestyle=":", alpha=0.6, label="CS onset")
            ax.axvline(us_end, color=US_END_COLOR, linestyle=":", alpha=0.6, label="US end")
            ax.plot(TIME_SINCE_CS, responses[row][col], color=style.MODEL_COLORS["arousal_mediated"])
            ax.set_title(f"{row_label}, {col_label}", fontsize=8)
            if row == 1:
                ax.set_xlabel("Time since CS (s)")
            if col == 0:
                ax.set_ylabel("Firing rate (Hz)")
    axes[0, 0].set_ylim(0, shared_ymax)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    axes[0, 1].legend(handles=handles + [_trace_interval_handle()], fontsize=6,
                       loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0.)
    return axes


# --- (f) rasters from real simulated data ------------------------------------

RASTER_PRE_S, RASTER_POST_S = 1.0, 2.0  # matches TIME_SINCE_CS's [-1, 2] range
RUNNING_THRESHOLD = 0.02  # matches TEBC._modulate_firing_rates_for_velocity's cutoff


def _example_cell(sim: SimArtifact, env: str, onsets: np.ndarray) -> int:
    """The place+task-responsive cell whose field gives the most balanced
    in-field/out-of-field split of CS-onset trials -- not just the first
    such cell, which can easily have a field the animal was rarely near at
    trial onset (one early candidate gave a 4-vs-46 or even 1-vs-49 split,
    useless for an illustrative raster)."""
    cells = sim.cells[env]
    agent = sim.agent[env]
    candidates = np.flatnonzero(np.asarray(cells["place_responsive_indices"], dtype=bool)
                                 & np.asarray(cells["task_responsive_indices"], dtype=bool))
    if len(candidates) == 0:
        raise ValueError(f"no place+task-responsive cell in {sim.run_id} env {env}")
    width = cells["place_cell_width"]
    centres = np.asarray(cells["place_cell_centres"])
    onset_x, onset_y = agent["x"][onsets], agent["y"][onsets]

    def balance(idx: int) -> int:
        distance = np.hypot(onset_x - centres[idx, 0], onset_y - centres[idx, 1])
        in_count = int((distance < width).sum())
        return min(in_count, len(onsets) - in_count)

    return int(max(candidates, key=balance))


def _raster_windows(spike_row: np.ndarray, onsets: np.ndarray, pre_steps: int, post_steps: int) -> np.ndarray:
    if len(onsets) == 0:
        return np.empty((0, pre_steps + post_steps))
    return np.stack([spike_row[onset - pre_steps: onset + post_steps] for onset in onsets])


_RASTER_MOVING_ALPHA, _RASTER_STILL_ALPHA = 0.22, 0.10


def raster_grid(fig, sim: SimArtifact, model_type: str, env: str = "A"):
    """One example place+task cell's real spike raster across every CS-onset
    trial, in its actual chronological order -- not split into separate
    per-condition subplots. Each row's background is shaded by that trial's
    field state at CS onset (in vs. out of the cell's own place field), and
    for arousal_mediated also by running state at onset (moving = more
    opaque band), matching how its task response is actually gated (see
    arousal_mediated_model/TEBC.py).

    2026-10-23 review: "show all N trials and then highlight the rows ...
    that fit the condition" -- replaces the earlier version, which built one
    subplot per condition from only that condition's trials (so a lopsided
    e.g. 46-vs-4 split showed a 46-row panel next to a nearly-empty 4-row
    one, and the real trial order/count wasn't visible anywhere)."""
    agent = sim.agent[env]
    cells = sim.cells[env]
    step = agent["times"][1] - agent["times"][0]
    pre_steps, post_steps = int(round(RASTER_PRE_S / step)), int(round(RASTER_POST_S / step))

    onsets = cs_onset_steps(agent["trial_marker"])
    onsets = onsets[(onsets - pre_steps >= 0) & (onsets + post_steps < len(agent["trial_marker"]))]

    cell_index = _example_cell(sim, env, onsets)
    centre = np.asarray(cells["place_cell_centres"][cell_index])
    width = cells["place_cell_width"]
    distance_at_onset = np.hypot(agent["x"][onsets] - centre[0], agent["y"][onsets] - centre[1])
    in_field = distance_at_onset < width

    spike_row = sim.spikes[env][cell_index]
    time_axis = (np.arange(pre_steps + post_steps) - pre_steps) * step
    color = style.MODEL_COLORS[model_type]
    windows = _raster_windows(spike_row, onsets, pre_steps, post_steps)

    ax = fig.subplots(1, 1)
    _plot_raster(ax, time_axis, windows, color)

    in_field_label = style.FIELD_STATE_LABELS["in_field"]
    out_of_field_label = style.FIELD_STATE_LABELS["out_of_field"]
    row_color = np.where(in_field, FIELD_STATE_COLORS["in_field"], FIELD_STATE_COLORS["out_of_field"])

    if model_type != "arousal_mediated":
        row_alpha = np.full(len(onsets), 0.15)
        condition_handles = [
            Patch(facecolor=FIELD_STATE_COLORS["in_field"], alpha=0.15, label=in_field_label),
            Patch(facecolor=FIELD_STATE_COLORS["out_of_field"], alpha=0.15, label=out_of_field_label),
        ]
    else:
        # "running"/"sitting" renamed to "Moving"/"Not moving" for the
        # displayed labels (2026-10-03, matches the Results text) --
        # running_at_onset stays as the variable name.
        running_at_onset = agent["velocity"][np.clip(onsets, 0, len(agent["velocity"]) - 1)] >= RUNNING_THRESHOLD
        row_alpha = np.where(running_at_onset, _RASTER_MOVING_ALPHA, _RASTER_STILL_ALPHA)
        condition_handles = [
            Patch(facecolor=FIELD_STATE_COLORS["in_field"], alpha=_RASTER_MOVING_ALPHA, label=f"{in_field_label}, Moving"),
            Patch(facecolor=FIELD_STATE_COLORS["in_field"], alpha=_RASTER_STILL_ALPHA, label=f"{in_field_label}, Not moving"),
            Patch(facecolor=FIELD_STATE_COLORS["out_of_field"], alpha=_RASTER_MOVING_ALPHA, label=f"{out_of_field_label}, Moving"),
            Patch(facecolor=FIELD_STATE_COLORS["out_of_field"], alpha=_RASTER_STILL_ALPHA, label=f"{out_of_field_label}, Not moving"),
        ]

    for trial_index, (band_color, alpha) in enumerate(zip(row_color, row_alpha)):
        ax.axhspan(trial_index - 0.5, trial_index + 0.5, color=band_color, alpha=alpha, zorder=0)

    ax.set_ylim(-0.5, len(onsets) - 0.5)
    ax.set_title(f"n={len(onsets)} trials", fontsize=8)
    ax.set_xlabel("Time since CS (s)")
    ax.set_ylabel("Trial")
    cs_onset_handle = Line2D([0], [0], color=CS_ONSET_COLOR, linestyle=":", alpha=0.6, label="CS onset")
    ax.legend(handles=condition_handles + [cs_onset_handle, _trace_interval_handle()], fontsize=6,
              loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0.)
    return ax


def _plot_raster(ax, time_axis: np.ndarray, windows: np.ndarray, color: str) -> None:
    ax.axvspan(CS_duration, US_start_time, color=TRACE_SHADE_COLOR, alpha=TRACE_SHADE_ALPHA, zorder=0.5)
    ax.axvline(0, color=CS_ONSET_COLOR, linestyle=":", alpha=0.6)
    for trial_index, counts in enumerate(windows):
        spike_times = time_axis[counts > 0]
        ax.scatter(spike_times, np.full_like(spike_times, trial_index, dtype=float),
                   s=4, color=color, marker="|", zorder=2)
