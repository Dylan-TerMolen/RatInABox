"""Fig 1 (setup): tEBC trial schematic (a), env A/B trajectories by elapsed
time and trial phase combined into one 2x2 grid (b), place-field tiling
annotated with the real place-responsive percentage (c), and 3 spatially
distinct example individual fields (d).

Env B panels read the same bioreal-independent artifact's env-B geometry/
cells -- see CLAUDE.md: place/trajectory content here doesn't depend on model
choice.

2026-10-23 figure review:
- (a) trial_schematic redrawn as a step/box timing diagram (colored-bordered
  boxes, duration above, phase name below, dashed pre-trial baseline and a
  dashed ITI arrow after) to match the reference tone/trace/shock diagram,
  replacing the earlier axvspan+legend version.
- Old (b) trajectory-by-time and (c) trajectory-by-phase merged into one 2x2
  grid under a single panel label "b" -- both are "the same trajectory,
  colored differently", so splitting them across two panel letters was
  redundant.
- Old (e) remapping_examples dropped entirely (it wasn't a legacy
  requirement -- see paper/legacy/coverage.yaml). Old (f) place_centres
  dropped too, but IS a legacy requirement (setup_place_centres_AB.png) --
  that coverage.yaml entry was flipped back to `regenerated: false` with a
  note, so `--check` keeps flagging it and Cowork keeps the old legacy image
  on its "Pending regeneration" page per CLAUDE.md's "nothing may go
  missing" rule, instead of the image silently disappearing.
- Old (g) example_fields reduced from 6 to 3 fields per env, now chosen by
  farthest-point sampling (paper.figlib.panels.setup._farthest_point_selection)
  so the three shown are spatially distinct instead of whichever three
  happen first in cell-index order.
- Panels relettered a-d to match the reduced count (old d/g -> c/d).

2026-11-04 (paper/reviews/claude_code_fig1_decoder_bins_prompt.md): new (b)
decoder_time_bins -- the 5 task-decoder classes on panel a's timeline, edges
read from the trial-marker column. Rest relettered b-d -> c-e.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from paper.figlib.io import FigureInputs
from paper.figlib.panels.setup import (
    decoder_time_bins,
    mean_decoder_bin_edges,
    example_fields,
    panel_label,
    place_coverage,
    trajectory_by_phase,
    trajectory_time,
    trial_schematic,
)

FIGURE_ID = "setup"


def build(inputs: FigureInputs, style) -> plt.Figure:
    sim = inputs.sim["bioreal-independent"]
    style.apply_rc_params()

    fig = plt.figure(figsize=(style.figure_width_inches("double"), 11.5), constrained_layout=True)
    row1, row2, row3, row4, row5 = fig.subfigures(5, 1, height_ratios=[1.0, 1.5, 0.9, 0.5, 0.5])

    # Row 1: (a) trial schematic over (b) decoder time bins -- one subfigure so
    # both axes share left/right edges and the timelines line up vertically
    ax_schematic, ax_bins = row1.subplots(2, 1, height_ratios=[0.55, 0.45])
    trial_schematic(ax_schematic, iti_start=mean_decoder_bin_edges(sim)[-1, 1])
    panel_label(ax_schematic, "a")
    decoder_time_bins(ax_bins, sim)
    panel_label(ax_bins, "b")
    shared_xlim = (min(ax_schematic.get_xlim()[0], ax_bins.get_xlim()[0]),
                   max(ax_schematic.get_xlim()[1], ax_bins.get_xlim()[1]))
    for ax in (ax_schematic, ax_bins):
        ax.set_xlim(shared_xlim)

    # Row 2: (c) trajectories, 2x2 -- top row by elapsed time, bottom row by phase
    (ax_time_A, ax_time_B), (ax_phase_A, ax_phase_B) = row2.subplots(2, 2)
    trajectory_time(ax_time_A, sim, "A", show_colorbar=False)
    panel_label(ax_time_A, "c")
    cbar_time_B = trajectory_time(ax_time_B, sim, "B")
    # Legend goes on the RIGHT column (ax_phase_B), not the left -- its
    # bbox_to_anchor=(1.02, 1.0) is relative to whichever axes draws it, so
    # putting it on ax_phase_A used to land it between the two columns,
    # squeezed inside the grid instead of outside it (2026-10-23 review:
    # "the legend looks really odd where it is").
    trajectory_by_phase(ax_phase_A, sim, "A", show_legend=False)
    trajectory_by_phase(ax_phase_B, sim, "B")

    # Row 3: (d) place-field tiling, env A and B, each annotated with its own
    # real place-responsive count/percentage
    ax_coverage_A, ax_coverage_B = row3.subplots(1, 2)
    place_coverage(ax_coverage_A, sim, "A", show_colorbar=False)
    panel_label(ax_coverage_A, "d")
    cbar_coverage_B = place_coverage(ax_coverage_B, sim, "B")

    # Row 4/5: (e) 3 spatially distinct example fields, env A then env B
    example_fields_A_axes = example_fields(row4, sim, "A", n=3, show_colorbar=False)
    panel_label(row4.axes[0], "e")
    example_fields_B_axes = example_fields(row5, sim, "B", n=3)

    # Named panels for build.py's per-panel export (build/panels/setup/<name>.*).
    fig.panel_axes = {
        "a": ax_schematic,
        "b": ax_bins,
        "c_time_A": ax_time_A,
        # c_time_B's colorbar is a separate sibling Axes, not part of
        # ax_time_B's own tight bbox -- include it explicitly.
        "c_time_B": [ax_time_B, cbar_time_B],
        "c_phase_A": ax_phase_A, "c_phase_B": ax_phase_B,
        "d_A": ax_coverage_A,
        "d_B": [ax_coverage_B, cbar_coverage_B],
        "e_A": example_fields_A_axes, "e_B": example_fields_B_axes,  # colorbar already appended, see example_fields
    }

    return fig
