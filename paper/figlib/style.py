"""Fonts, sizes, colors -- the one place any of these are set. Figure/panel
code imports constants from here rather than hardcoding a color or rcParam.
See CLAUDE.md's "Figure pipeline (paper/)" -> Conventions.

No target journal has been chosen yet (CLAUDE.md open decision #6), so the
widths/fonts below are the documented fallback, not a final choice.
"""
from __future__ import annotations

import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

# --- journal geometry (fallback until a target journal is chosen) ---------

SINGLE_COLUMN_MM = 89
DOUBLE_COLUMN_MM = 183
BASE_FONT_PT = 6  # within the 5-7pt fallback range

WIDTH_MM = {"single": SINGLE_COLUMN_MM, "double": DOUBLE_COLUMN_MM}


def mm_to_inches(mm: float) -> float:
    return mm / 25.4


def figure_width_inches(width: str) -> float:
    return mm_to_inches(WIDTH_MM[width])


RC_PARAMS = {
    "font.size": BASE_FONT_PT,
    "font.family": "sans-serif",
    "axes.titlesize": BASE_FONT_PT + 1,
    "axes.labelsize": BASE_FONT_PT,
    "xtick.labelsize": BASE_FONT_PT - 1,
    "ytick.labelsize": BASE_FONT_PT - 1,
    "legend.fontsize": BASE_FONT_PT - 1,
    "svg.fonttype": "none",  # keep text as text, not paths, in exported SVGs
}


def apply_rc_params() -> None:
    mpl.rcParams.update(RC_PARAMS)


# --- model colors -----------------------------------------------------------
# Validated 2026-09-25 with the dataviz skill's validate_palette.js (this
# repo's earlier green/red placeholder scored a CVD-separation WARN against
# FIELD_STATE_COLORS' red below): dataviz's own default categorical theme's
# first 3 slots (blue/orange/aqua), which its palette.md documents as
# clearing every all-pairs gate in both light and dark modes, not just
# adjacent-pair. `node scripts/validate_palette.js "#2a78d6,#eb6834,#1baf7a"
# --mode light --pairs all` -> ALL CHECKS PASS (worst CVD deltaE 9.2 deutan,
# worst normal-vision deltaE 24.0; aqua sits at 2.74:1 contrast, under the
# 3:1 relief threshold, so every figure using these colors needs a visible
# legend or direct labels -- true of every panel that currently uses this
# palette). Independent keeps its prior blue; place_dependent/arousal_mediated
# swapped from green/red to orange/aqua.
MODEL_COLORS = {
    "independent": "#2a78d6",
    "place_dependent": "#eb6834",
    "arousal_mediated": "#1baf7a",
}

MODEL_DISPLAY_NAMES = {
    "independent": "Independent (IM)",
    "place_dependent": "Place-dependent (PDM)",
    "arousal_mediated": "Arousal-dependent (ADM)",
}

MODEL_ABBREVIATIONS = {
    "independent": "IM",
    "place_dependent": "PDM",
    "arousal_mediated": "ADM",
}

# --- trial-phase colors ------------------------------------------------------
# Originally ported from ratinabox/hsw/notebooks/figures.ipynb (blue/green/red).
# Re-stepped 2026-09-25 onto the same blue/orange/aqua triple as MODEL_COLORS
# (validated all-pairs PASS regardless of which name gets which slot -- CVD/
# normal-vision separation is symmetric, doesn't depend on labeling) so the
# whole paper draws 3-way categoricals from one consistent, red/green-free set.
PHASE_COLORS = {
    "tone": "#2a78d6",
    "trace": "#1baf7a",
    "shock": "#eb6834",
    "post": "#4d4d4d",  # ratinabox.DARKGREY as a hex triple -- neutral background, not part of the triple
}

PHASE_MS_RANGES = {
    "tone": (0, 250),
    "trace": (250, 750),
    "shock": (750, 850),
    "post": (850, 2000),
}

PHASE_DRAW_ORDER = ("post", "tone", "trace", "shock")

# --- field-distance colors ---------------------------------------------------
# Also ported from figures.ipynb (IN_FIELD_COLOR/OUT_FIELD_COLOR/NEAR_FIELD_COLOR).
# out_of_field re-stepped 2026-09-25 from red onto the shared blue/orange/aqua
# triple (MODEL_COLORS/PHASE_COLORS), then re-stepped AGAIN 2026-10-23 (models
# figure review: "make it so that red/orange is purple instead for color
# blindness") onto this dict's own purple -- scoped to FIELD_STATE_COLORS only,
# not the shared triple (MODEL_COLORS/PHASE_COLORS/ENV_COLORS keep #eb6834;
# see those dicts' own comments), since this is the one 3-way split
# (in/near/out-of-field) that's directly the subject of that feedback.
# Re-validated: `node scripts/validate_palette.js "#2a78d6,#1baf7a,#9b59d0"
# --mode light` and `--mode dark` -> ALL CHECKS PASS (worst CVD deltaE 19.6
# deutan, up from the orange triple's 9.2 -- a real improvement, not just a
# swap; aqua's pre-existing 2.74:1 contrast WARN is unchanged, still needs
# visible labels/legend wherever this palette is used).
FIELD_STATE_COLORS = {
    "in_field": "#2a78d6",
    "near_field_edge": "#1baf7a",
    "out_of_field": "#9b59d0",
}

# --- env A/B colors -----------------------------------------------------------
# Same blue/orange as MODEL_COLORS' first two slots (a 2-of-3 subset of an
# all-pairs-validated set trivially still passes) -- any panel comparing env A
# vs env B where no model color also appears in the same panel (setup.py's
# place_coverage field-outline circles) uses these instead of matplotlib's
# default "C0"/"C1" cycle. NOT used by mechanism.py: that figure
# color-codes each panel by MODEL (MODEL_COLORS), and reusing this blue/orange
# pair for env A/B inside those same panels would clash with -- read as the
# same signal as -- independent's/place_dependent's own model colors
# (2026-10-04 review). mechanism.py instead reuses that panel's own model
# color for both envs and differentiates env by ENV_LINESTYLES.
ENV_COLORS = {
    "A": "#2a78d6",
    "B": "#eb6834",
}

ENV_LINESTYLES = {
    "A": "-",
    "B": "--",
}

# --- task-state colors ---------------------------------------------------------
# Same blue/orange pair, for the other recurring 2-way split: in-task vs.
# out-of-task (position_decoding.py's R^2/cm-error panels).
TASK_STATE_COLORS = {
    "in_task": "#2a78d6",
    "out_of_task": "#eb6834",
}

# --- decoding label helpers --------------------------------------------------
# Plot titles/axes must never show internal variable/tag names (2026-09-29
# figure review) -- map the raw sweep-param / direction names used as
# scores.parquet columns to plain-language labels here, once, rather than
# inline at each call site.
PARAM_DISPLAY_NAMES = {
    "percent_task_in_response": "Task weight (balance)",
    "percent_task_responsive_cells": "Task-responsive cells (%)",
    "percent_place_cells": "Place cells (%)",
    "holdover": "Task cells carried over A→B (%)",
}

# These params are stored as 0-1 fractions but should be *displayed* as
# percentages (ticks "0, 20, 40 ..." not "0.2") -- every percent_*/holdover
# param, not just percent_place_cells (2026-09-29 review item 3).
PERCENT_DISPLAY_PARAMS = {"percent_task_responsive_cells", "percent_place_cells", "holdover"}


def facet_title(facet_param: str, value: float) -> str:
    """'20% place cells' instead of 'Place cells (%) = 20' -- a facet title
    reads as a plain phrase instead of a variable=value pair (2026-10-04
    review). Derives the short name from PARAM_DISPLAY_NAMES (stripping its
    ' (%)' suffix and lowercasing the first letter) rather than a second
    hardcoded name table. Falls back to '<display name> = <value>' for a
    non-percent facet param (none currently used as a facet, but kept
    general)."""
    display_name = PARAM_DISPLAY_NAMES.get(facet_param, facet_param)
    if facet_param in PERCENT_DISPLAY_PARAMS:
        short_name = display_name.removesuffix(" (%)")
        short_name = short_name[:1].lower() + short_name[1:]
        return f"{value * 100:g}% {short_name}"
    return f"{display_name} = {value:g}"

DIRECTION_DISPLAY_NAMES = {
    "A->A": "A→A", "B->B": "B→B", "A->B": "A→B", "B->A": "B→A",
    "shuffA->A": "Shuffled A→A", "shuffA->B": "Shuffled A→B", "shuffB->A": "Shuffled B→A",
}


def direction_display_name(direction: str) -> str:
    """DIRECTION_DISPLAY_NAMES lookup with a fallback to the raw string --
    use this (not an inline f-string with the raw '->' direction key) any
    time a direction is interpolated into a label/title, so the ASCII arrow
    never leaks into a rendered figure (2026-10-03 review: it had, in the
    default metric_label built by draw_task_transfer_heatmap_grid/
    draw_metric_surface_facets)."""
    return DIRECTION_DISPLAY_NAMES.get(direction, direction)


# The task decoder is a KNN *classifier* over CS_US_NUM_BINS=5 bins, not a
# regressor -- its score is fraction-correct (accuracy), and chance is
# analytically 1/5, not something read off the shuffled control (2026-09-29
# review item 1; confirmed against Hannahs-CEBRAs/CSUS_score.py).
TASK_CHANCE_LEVEL = 0.2

# One canonical way to write the chance level in a label/title -- previously
# appeared as "chance=0.2", "Chance = 0.20" and "chance = 0.2" interchangeably
# across figures (2026-10-03/04 review). Title case, parenthetical, no
# trailing zero. Use CHANCE_LABEL.lower() when embedding mid-sentence inside
# a longer parenthetical (e.g. "(A→B, chance (0.2))").
CHANCE_LABEL = f"Chance ({TASK_CHANCE_LEVEL:g})"

# --- "beats the shuffled floor" phrasing --------------------------------------
# One phrase for the CI-non-overlap test (above_chance_fraction/
# _above_chance_table), used whether the metric is higher-is-better (task
# accuracy: "above chance") or lower-is-better (place cm error: "below
# shuffled floor") -- those two different phrasings for the same statistical
# test read as inconsistent across figures (2026-10-03 review). "Beats" reads
# naturally for both directions without saying which side "better" is on.
BEATS_SHUFFLE_PHRASE = "beats the shuffled floor"

# --- recurring label casing ----------------------------------------------------
# Sentence case (first letter capitalized) for every standalone panel title,
# legend entry, or axis label in this pipeline -- previously drifted ("In
# field" vs "in field", "env A" vs "Env A", "Within-env" vs
# "Within-environment"; 2026-10-03 review). Not applied to inline prose
# inside a longer sentence (e.g. caption body text).
TASK_STATE_LABELS = {"in_task": "In-task", "out_of_task": "Out-of-task"}
FIELD_STATE_LABELS = {"in_field": "In field", "near_field_edge": "Near field edge", "out_of_field": "Out of field"}
WITHIN_ENV_LABEL = "Within-environment"
CROSS_ENV_LABEL = "Cross-environment"


def env_label(env: str) -> str:
    """'Env A' / 'Env B' -- the one casing used everywhere an environment is
    named (2026-10-03 review: mechanism.py had lowercase 'env A')."""
    return f"Env {env}"


# --- trial-phase legend labels -------------------------------------------------
# One canonical wording per CS/trace/US phase, shared by trial_schematic
# (setup.py panel a) and trajectory_by_phase (panel c) -- those two used to
# say "CS (tone)"/"US (eyelid shock)" and "tone"/"shock" respectively for the
# same phases (2026-10-03 review).
PHASE_LEGEND_LABELS = {
    "tone": "CS (tone)",
    "trace": "Trace",
    "shock": "US (eyelid shock)",
    "post": "Inter-trial",
}


def ms_range_label(start_ms: float, end_ms: float) -> str:
    """'0–250 ms' with an en dash, not a hyphen (2026-10-03 review)."""
    return f"{start_ms:g}–{end_ms:g} ms"


# One line defining what every error bar in this pipeline means, for
# whichever caption/panel wants to state it explicitly rather than leaving it
# undefined (2026-10-03 review) -- every error bar in paper/figlib/panels is
# a 95% CI (mean +/- 1.96*SEM) across either simulation iterations or, for
# population_stability, cells.
ERROR_BAR_NOTE = "Error bars: mean ± 95% CI."


def bioreal_headline(params: dict, *, decoding_label: str | None = None) -> str:
    """The two numbers a reader asks about first -- place-cell and
    task-responsive-cell percentages -- in large type at the top of the
    figure. bioreal_params_footnote carries the rest (cell count, holdover,
    task types, sweep/decoder details) in small type at the bottom; these two
    specifically needed to be prominent, not buried down there (2026-10-03
    request). `decoding_label` (e.g. "Position decoding"/"Task decoding")
    prefixes the headline so the same two-number format also says which
    decoding the figure is -- position_decoding.py and task_decoding.py read
    identically at a glance otherwise (2026-10-03 follow-up request)."""
    params_part = (f"{params['percent_place_cells'] * 100:g}% place cells, "
                   f"{params['percent_task_responsive_cells'] * 100:g}% task-responsive cells")
    return f"{decoding_label} — {params_part}" if decoding_label else params_part


def _decoder_split_label(decoder_split: str) -> str:
    """"sequential_75_25" -> "sequential 75/25" -- bioreal.yaml's own
    machine-readable value, not written for display as-is."""
    parts = decoder_split.split("_")
    return " ".join(parts[:-2] + ["/".join(parts[-2:])]) if len(parts) >= 2 else decoder_split


def bioreal_params_footnote(params: dict, *, swept_param_label: str = "Task weight (balance)") -> str:
    """One footnote line stating the model parameters a bioreal-operating-
    point figure was actually run at, built from a paper/params/*.yaml dict
    (figlib.io.load_param_set) so the displayed values can't drift from the
    real ones (2026-10-03 request: Figures 3/4 need their parameters shown on
    the figure itself, not just in the caption/docstring). `swept_param_label`
    names whichever param the figure sweeps on its x-axis instead of holding
    fixed -- these figures sweep percent_task_in_response (balance), not
    params['percent_task_in_response']'s own still-provisional value."""
    task_types = ", ".join(str(t) for t in params["task_types"])
    return (
        f"Independent (IM): {params['num_neurons']} cells, "
        f"{params['percent_place_cells'] * 100:g}% place cells, "
        f"{params['percent_task_responsive_cells'] * 100:g}% task-responsive, "
        f"holdover {params['holdover'] * 100:g}%, task types [{task_types}]. "
        f"{swept_param_label} swept on x-axis (std {params['percent_task_in_response_std']:g} per draw), "
        f"n={params['num_iters']} iterations/point, "
        f"{_decoder_split_label(params['decoder_split'])} decoder split."
    )

# Empirical decoding benchmark from the manuscript's ref 19 -- neither the
# value nor which metric it's on (accuracy vs. R^2) has been tracked down yet
# (checked manuscript_todo.md, tebc_response_equations.tex, and the
# Wirtshafter et al. 2025 source-paper PDF/notes -- none state a single
# point-estimate decoding number, only significance tests against shuffled
# controls). Set both fields once the authors supply it; every figure that
# draws a benchmark line checks BENCHMARK_VALUE is not None first.
BENCHMARK_VALUE = None
BENCHMARK_LABEL = None

# --- sequential (magnitude) colormap -------------------------------------------
# One hue, light -> dark, for continuous magnitude (setup.py's place_coverage
# heatmap) -- the dataviz skill's convention ("sequential = one hue"), not a
# multi-hue map like viridis. Interpolates white -> the same blue used
# everywhere else, so a reader already primed on "blue" from ENV_COLORS/
# MODEL_COLORS/PHASE_COLORS reads it as the same identity, just as magnitude.
PLACE_COVERAGE_CMAP = LinearSegmentedColormap.from_list("place_coverage_blues", ["#f0f6fc", "#2a78d6"])

# Note: setup.py's trajectory_time/trajectory_by_phase panels (b/c) use plain
# "viridis" directly (purple->yellow, matching place_coverage/example_fields'
# colormap elsewhere in the same figure) rather than a style.py constant here
# -- 2026-09-25 decision, superseding an earlier same-day blue/orange attempt.
