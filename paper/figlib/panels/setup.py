"""Panels for the `setup` figure (draft Fig 1): trial schematic, per-env
trajectories (by elapsed time and by trial phase), place-field tiling, and
example individual fields. Trajectory math ported from
ratinabox/hsw/notebooks/figures.ipynb cells 6 and 8 -- same math, same colors
-- but reading from a SimArtifact's saved arrays instead of a live agent, per
CLAUDE.md's "figures only read artifacts" rule. Place-field-coverage panel is
new (not in the notebook).
"""
from __future__ import annotations

import matplotlib as mpl
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Circle as MplCircle
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.path import Path as MplPath
from matplotlib.ticker import MultipleLocator

from ratinabox.hsw.simulation_helpers import CS_US_NUM_BINS, bin_cs_us_time_ids
from ratinabox.hsw.tebc_response import CS_duration, US_duration, US_start_time

from paper.figlib import style
from paper.figlib.io import SimArtifact

# "post" is a genuine bounded window (850-2000 ms after CS onset, see
# style.PHASE_MS_RANGES) drawn at the same weight as tone/trace/shock below --
# NOT the long inter-trial rest between trials, which is a separate unlabeled
# background layer (INTER_TRIAL_COLOR) so "post" in the legend means exactly
# what its (850-2000 ms) label says, not "everything else in the session".
DEFAULT_PHASE_LINE_STYLE = {"linewidth": 1.3, "alpha": 0.9}
INTER_TRIAL_COLOR = "#bfbfbf"
INTER_TRIAL_STYLE = {"linewidth": 0.5, "alpha": 0.25}

# tone/trace/shock have a natural order (chronological within a trial), so
# 2026-09-25: colored as an ordinal purple->yellow "viridis" progression --
# the same colormap already used elsewhere in this figure (place_coverage,
# example_fields) -- rather than 3 arbitrary categorical hues. "post" stays
# style.PHASE_COLORS["post"] (neutral gray): it's not part of that ordinal
# progression, just the inter-trial background.
_PHASE_PROGRESSION_POSITIONS = {"tone": 0.15, "trace": 0.5, "shock": 0.85}


def _phase_line_color(phase: str):
    if phase == "post":
        return style.PHASE_COLORS["post"]
    return mpl.colormaps["viridis"](_PHASE_PROGRESSION_POSITIONS[phase])


def panel_label(ax, letter: str) -> None:
    """Bold panel letter at the axes' top-left corner. Figures use these
    instead of descriptive titles -- the description belongs in the caption
    (CLAUDE.md 2026-09-23 note), not baked into the image."""
    ax.text(-0.12, 1.08, letter, transform=ax.transAxes, fontsize=11, fontweight="bold", va="top", ha="right")


def env_origin(boundary: list[list[float]]) -> np.ndarray:
    """Bottom-left corner of the environment's bounding box. The recorded
    MATLAB position data sits at an arbitrary lab-frame offset (env A's
    boundary is around x in [0.5, 1.5], y in [0.7, 1.3] m) -- subtracting
    this lets every panel plot from (0, 0) instead of that raw offset."""
    return np.asarray(boundary).min(axis=0)


def draw_environment_boundary(ax, boundary: np.ndarray) -> MplPolygon:
    """Lightweight standalone redraw of an arena outline from its (already
    origin-shifted) boundary polygon -- not RatInABox's own
    Environment.plot_environment (walls/holes/anti-arena shading), which
    needs a live Environment object this module deliberately doesn't have.
    Returns the boundary patch so callers can clip trajectories/heatmaps/
    field circles to it with set_clip_path -- a stroked line or circle drawn
    exactly at the wall otherwise visually spills past it by half its own
    linewidth (see 2026-09-23 "trajectory crosses the boundary" report;
    verified the underlying coordinates never actually leave the polygon --
    this was a rendering artifact, not a data bug)."""
    patch = MplPolygon(boundary, closed=True, facecolor="#d9d9d9", edgecolor="#4d4d4d",
                        linewidth=1.0, zorder=-1)
    ax.add_patch(patch)
    pad = 0.02
    ax.set_xlim(boundary[:, 0].min() - pad, boundary[:, 0].max() + pad)
    ax.set_ylim(boundary[:, 1].min() - pad, boundary[:, 1].max() + pad)
    return patch


def env_title(env: str, sim: SimArtifact) -> str:
    minx, maxx, miny, maxy = sim.environment[env]["extent"]
    return f"Env {env} ({maxx - minx:.2f} m × {maxy - miny:.2f} m)"


def trajectory_segments(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Consecutive-position line segments for LineCollection: segment i spans
    step i -> i+1."""
    positions = np.stack([x, y], axis=1)
    return np.stack([positions[:-1], positions[1:]], axis=1)


_SCHEMATIC_SEGMENT_HEIGHT = {"tone": 1.0, "trace": 0.45, "shock": 1.0}
_SCHEMATIC_ITI_LABEL = "30–60s"


def trial_schematic(ax, *, iti_start: float | None = None) -> None:
    """CS -> trace -> US step/box timing diagram (panel a): one colored step
    per phase (height = visual emphasis, not real data), duration labeled
    above and phase name below, a dashed baseline before the trial and a
    dashed arrow + ITI label after -- redrawn 2026-10-23 to match Hannah's
    reference diagram (colored-bordered boxes with inline labels) instead of
    the earlier axvspan+legend version. Shared by every model and both
    environments, so it doesn't take a SimArtifact at all. iti_start (s from
    CS onset) delays the ITI arrow, e.g. past the last decoded time bin so
    panel b's bins never sit under it; the gap is a plain dashed baseline."""
    segments = [
        ("tone", 0.0, CS_duration),
        ("trace", CS_duration, US_start_time),
        ("shock", US_start_time, US_start_time + US_duration),
    ]
    trial_start, trial_end = segments[0][1], segments[-1][2]
    pre_start = trial_start - 0.15
    iti_start = max(trial_end, iti_start or trial_end)
    iti_end = iti_start + 0.3
    dashed = dict(color="#808080", linestyle=(0, (3, 2)), linewidth=1.2)

    ax.plot([pre_start, trial_start], [0, 0], zorder=1, **dashed)
    ax.plot([trial_end, iti_start], [0, 0], zorder=1, **dashed)
    ax.annotate("", xy=(iti_end, 0), xytext=(iti_start, 0),
                arrowprops=dict(arrowstyle="-|>", linestyle=dashed["linestyle"],
                                 color=dashed["color"], linewidth=dashed["linewidth"]))
    ax.text((iti_start + iti_end) / 2, 0.08, _SCHEMATIC_ITI_LABEL, color="#4d4d4d",
             fontsize=7, ha="center", va="bottom")

    for phase, start, end in segments:
        color = style.PHASE_COLORS[phase]
        height = _SCHEMATIC_SEGMENT_HEIGHT[phase]
        ax.axvspan(start, end, ymin=(0.3 / 1.6), ymax=(height + 0.3) / 1.6, color=color, alpha=0.15, zorder=0)
        ax.plot([start, start, end, end], [0, height, height, 0], color=color, linewidth=2.2, zorder=2)
        ax.text((start + end) / 2, height + 0.08, f"{round((end - start) * 1000)}ms", color=color,
                 fontsize=7, fontweight="bold", ha="center", va="bottom")
        ax.text((start + end) / 2, -0.12, style.PHASE_LEGEND_LABELS[phase], color=color,
                 fontsize=7, fontweight="bold", ha="center", va="top")

    ax.set_xlim(pre_start, iti_end + 0.05)
    ax.set_ylim(-0.3, 1.3)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


# Bins are ordinal (chronological), so a single-hue sequential ramp -- like
# _phase_line_color's viridis sampling -- with each band labeled; purple keeps
# it off both the phase triple and MODEL_COLORS (blue/aqua/orange).
_DECODER_BIN_CMAP_RANGE = (0.3, 0.7)
_PHASE_BOUNDARIES_S = (0.0, CS_duration, US_start_time, US_start_time + US_duration)


def _decoder_bin_color(bin_index: int):
    low, high = _DECODER_BIN_CMAP_RANGE
    return mpl.colormaps["Purples"](low + (high - low) * bin_index / (CS_US_NUM_BINS - 1))


def _trial_bin_edges(times: np.ndarray, bins: np.ndarray, dt: float) -> np.ndarray:
    """(CS_US_NUM_BINS, 2) start/end of each bin within one trial, seconds from CS onset."""
    return np.array([[times[bins == k].min(), times[bins == k].max() + dt]
                     for k in range(1, CS_US_NUM_BINS + 1)]) - times[0]


def decoder_bin_edges(times: np.ndarray, trial_marker: np.ndarray) -> np.ndarray:
    """(n_trials, CS_US_NUM_BINS, 2) per-trial start/end of each decoded time
    bin, seconds from CS onset, read from the recorded trial-marker column
    (markers 1-10 paired by bin_cs_us_time_ids) -- not assumed equal-width."""
    in_trial = (trial_marker >= 1) & (trial_marker <= 10)
    trial_ids = np.cumsum(in_trial & ~np.concatenate(([False], in_trial[:-1])))
    bins = bin_cs_us_time_ids(trial_marker)
    dt = np.median(np.diff(times))
    return np.stack([_trial_bin_edges(times[in_trial & (trial_ids == i)], bins[in_trial & (trial_ids == i)], dt)
                     for i in np.unique(trial_ids[in_trial])])


def mean_decoder_bin_edges(sim: SimArtifact) -> np.ndarray:
    """(CS_US_NUM_BINS, 2) bin start/end, seconds from CS onset, averaged over every trial in both envs."""
    return np.concatenate([decoder_bin_edges(sim.agent[env]["times"], sim.agent[env]["trial_marker"])
                           for env in ("A", "B")]).mean(axis=0)


def decoder_time_bins(ax, sim: SimArtifact) -> None:
    """The CS_US_NUM_BINS classes the task decoder predicts, as adjacent
    labeled bands on the trial timeline (panel b), edges averaged over every
    trial in both envs. Dotted lines mark the tone/trace/shock boundaries from
    panel a. Caller aligns x-limits with trial_schematic."""
    edges = mean_decoder_bin_edges(sim)
    for k, (start, end) in enumerate(edges):
        ax.axvspan(start, end, ymin=0.15, ymax=0.85, facecolor=_decoder_bin_color(k), edgecolor="white",
                   linewidth=1.0, zorder=1)
        ax.text((start + end) / 2, 0.5, f"Bin {k + 1}", fontsize=7, fontweight="bold", ha="center",
                va="center", color="black", zorder=3)
    for boundary in _PHASE_BOUNDARIES_S:
        ax.axvline(boundary, color="#4d4d4d", linestyle=":", linewidth=0.9, zorder=2)

    ax.set_xlim(-0.05, edges[-1, 1] + 0.05)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.xaxis.set_major_locator(MultipleLocator(0.25))
    ax.set_xlabel("Time from CS onset (s)")
    for side in ("left", "right", "top"):
        ax.spines[side].set_visible(False)


def trajectory_time(ax, sim: SimArtifact, env: str, *, cmap=None,
                     linewidth: float = 1.2, show_colorbar: bool = True,
                     tick_step_minutes: float = 10):
    """Continuous trajectory line colored by elapsed session time (purple =
    early, yellow = late -- plain "viridis", the same purple->yellow gradient
    already used elsewhere in this figure, e.g. place_coverage/example_fields
    -- not the earlier blue/orange attempt), with a colorbar ticked at clean
    multiples of tick_step_minutes (0, 10, 20, ...) rather than the data's
    raw endpoints. Returns the colorbar's own Axes (or None if
    show_colorbar=False) so a caller can include it in a build.py panel
    group -- a separately-created colorbar Axes isn't picked up by
    ax.get_tightbbox() on the trajectory axes alone."""
    cmap = cmap if cmap is not None else "viridis"
    agent = sim.agent[env]
    origin = env_origin(sim.environment[env]["boundary"])
    boundary = np.asarray(sim.environment[env]["boundary"]) - origin
    patch = draw_environment_boundary(ax, boundary)

    x, y = agent["x"] - origin[0], agent["y"] - origin[1]
    segments = trajectory_segments(x, y)
    minutes = agent["times"][:-1] / 60  # elapsed minutes at each segment's start
    line_collection = LineCollection(segments, cmap=cmap, linewidths=linewidth, zorder=1.1)
    line_collection.set_array(minutes)
    line_collection.set_clip_path(patch)
    ax.add_collection(line_collection)
    ax.set_aspect("equal")
    ax.set_title(env_title(env, sim), fontsize=8)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")

    if show_colorbar:
        cbar = ax.figure.colorbar(line_collection, ax=ax, shrink=0.7)
        cbar.ax.yaxis.set_major_locator(MultipleLocator(tick_step_minutes))
        cbar.set_label("Time (min)")
        return cbar.ax
    return None


def cs_onset_steps(trial_marker: np.ndarray) -> np.ndarray:
    """Every step where trial_marker rises into the CS range [1, 5]."""
    in_cs = (trial_marker >= 1) & (trial_marker <= 5)
    return np.flatnonzero(in_cs & ~np.concatenate(([False], in_cs[:-1])))


def classify_trial_phases(time_since_onset: np.ndarray) -> np.ndarray:
    """Vectorized phase-per-step from time since the most recent CS onset.
    Each of tone/trace/shock/post is its exact bounded window (matching
    style.PHASE_MS_RANGES); anything outside all four -- no CS seen yet, or
    more than post's window past the last one -- is "inter_trial", not
    "post". Unlike the other four, inter_trial isn't a legend category (see
    trajectory_by_phase) -- it's the long unlabeled rest between trials."""
    post_end = US_start_time + US_duration + (style.PHASE_MS_RANGES["post"][1] - style.PHASE_MS_RANGES["post"][0]) / 1000
    conditions = [
        (time_since_onset >= 0) & (time_since_onset < CS_duration),
        (time_since_onset >= CS_duration) & (time_since_onset < US_start_time),
        (time_since_onset >= US_start_time) & (time_since_onset < US_start_time + US_duration),
        (time_since_onset >= US_start_time + US_duration) & (time_since_onset < post_end),
    ]
    choices = ["tone", "trace", "shock", "post"]
    return np.select(conditions, choices, default="inter_trial")


def trial_phase_per_step(times: np.ndarray, trial_marker: np.ndarray) -> np.ndarray:
    """Trial phase ('tone'/'trace'/'shock'/'post'/'inter_trial') at every
    step, aligned 1:1 with times/trial_marker."""
    onset_times = times[cs_onset_steps(trial_marker)]
    if len(onset_times) == 0:
        return np.full(len(times), "inter_trial")
    preceding_onset_idx = np.searchsorted(onset_times, times, side="right") - 1
    time_since_onset = np.where(preceding_onset_idx >= 0,
                                 times - onset_times[np.clip(preceding_onset_idx, 0, None)],
                                 -1.0)
    return classify_trial_phases(time_since_onset)


def _phase_legend_label(phase: str) -> str:
    start_ms, end_ms = style.PHASE_MS_RANGES[phase]
    return f"{style.PHASE_LEGEND_LABELS[phase]} ({style.ms_range_label(start_ms, end_ms)})"


def trajectory_by_phase(ax, sim: SimArtifact, env: str, *, show_legend: bool = True) -> None:
    """Same trajectory, colored by task phase instead of elapsed time. The
    long inter-trial rest is drawn first as a faint unlabeled background
    layer so it doesn't bury the four legend phases, each drawn at equal
    weight since none of them any longer represents the bulk of the session.

    This is the default "unified" style (tone/trace/shock colors all in one
    panel). Hannah's reference alternative -- separate non-tEBC (gray) vs
    tEBC (phase-colored) panels -- is trajectory_task_split below; swap which
    one a figure module calls, they read the same SimArtifact."""
    agent = sim.agent[env]
    origin = env_origin(sim.environment[env]["boundary"])
    boundary = np.asarray(sim.environment[env]["boundary"]) - origin
    patch = draw_environment_boundary(ax, boundary)

    x, y = agent["x"] - origin[0], agent["y"] - origin[1]
    segments = trajectory_segments(x, y)
    phases = trial_phase_per_step(agent["times"], agent["trial_marker"])[:-1]

    inter_trial_segments = segments[phases == "inter_trial"]
    if len(inter_trial_segments):
        inter_lc = LineCollection(inter_trial_segments, colors=INTER_TRIAL_COLOR, zorder=0, **INTER_TRIAL_STYLE)
        inter_lc.set_clip_path(patch)
        ax.add_collection(inter_lc)

    for phase in style.PHASE_DRAW_ORDER:
        phase_segments = segments[phases == phase]
        if len(phase_segments) == 0:
            continue
        lc = LineCollection(phase_segments, colors=_phase_line_color(phase), zorder=1, **DEFAULT_PHASE_LINE_STYLE)
        lc.set_clip_path(patch)
        ax.add_collection(lc)
    ax.set_aspect("equal")
    ax.set_title(env_title(env, sim), fontsize=8)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")

    if show_legend:
        handles = [Line2D([0], [0], color=_phase_line_color(phase), lw=2, label=_phase_legend_label(phase))
                   for phase in ("tone", "trace", "shock", "post")]
        ax.legend(handles=handles, fontsize=6, loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0.)


def trajectory_task_split(ax_non_tebc, ax_tebc, sim: SimArtifact, env: str) -> None:
    """Hannah's reference alternative to trajectory_by_phase: non-tEBC
    (inter_trial, gray) and tEBC (tone/trace/shock, phase-colored) trajectory
    drawn as two separate panels rather than one combined one. Not called by
    the default setup figure -- kept as a simple drop-in alternative (swap
    the call in figures/setup.py) if the authors prefer this split."""
    agent = sim.agent[env]
    origin = env_origin(sim.environment[env]["boundary"])
    boundary = np.asarray(sim.environment[env]["boundary"]) - origin
    x, y = agent["x"] - origin[0], agent["y"] - origin[1]
    segments = trajectory_segments(x, y)
    phases = trial_phase_per_step(agent["times"], agent["trial_marker"])[:-1]

    patch_non = draw_environment_boundary(ax_non_tebc, boundary)
    non_tebc_segments = segments[phases == "inter_trial"]
    if len(non_tebc_segments):
        lc = LineCollection(non_tebc_segments, colors=INTER_TRIAL_COLOR, **DEFAULT_PHASE_LINE_STYLE)
        lc.set_clip_path(patch_non)
        ax_non_tebc.add_collection(lc)
    ax_non_tebc.set_aspect("equal")

    patch_task = draw_environment_boundary(ax_tebc, boundary)
    for phase in ("tone", "trace", "shock"):
        phase_segments = segments[phases == phase]
        if len(phase_segments) == 0:
            continue
        lc = LineCollection(phase_segments, colors=style.PHASE_COLORS[phase], **DEFAULT_PHASE_LINE_STYLE)
        lc.set_clip_path(patch_task)
        ax_tebc.add_collection(lc)
    ax_tebc.set_aspect("equal")
    handles = [Line2D([0], [0], color=style.PHASE_COLORS[phase], lw=2, label=_phase_legend_label(phase))
               for phase in ("tone", "trace", "shock")]
    ax_tebc.legend(handles=handles, fontsize=6, loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0.)


def place_coverage(ax, sim: SimArtifact, env: str, *, cmap=None, grid_resolution: int = 200,
                    show_colorbar: bool = True, show_note: bool = True):
    """Summed place-field heatmap (every place-responsive cell's gaussian
    added together, masked outside the boundary) with each field's own
    outline circle on top -- panel d, at whatever percent_place_cells the
    artifact was built with (bioreal = 20%, see meta.json). Defaults to the
    shared blue sequential ramp (style.PLACE_COVERAGE_CMAP), not viridis --
    2026-09-25 request to align setup's panels onto the paper's blue/orange
    theme rather than an unrelated multi-hue map. `show_colorbar=False` on
    one of the two envs when both share the same scale (2026-10-03 review:
    A and B each got their own identical-scale colorbar, which read as
    duplicated) -- caller picks which one keeps it. Returns the colorbar's
    own Axes (or None) the same way trajectory_time does, so a caller can
    include it in a build.py panel group. `show_note` (2026-10-23 request:
    "add a note to make it look prettier") annotates the actual
    place-responsive count/percentage straight off this env's own artifact --
    each env is simulated separately so its real count can differ from the
    nominal bioreal target, unlike a fixed caption percentage."""
    cmap = cmap if cmap is not None else style.PLACE_COVERAGE_CMAP
    cells = sim.cells[env]
    origin = env_origin(sim.environment[env]["boundary"])
    boundary = np.asarray(sim.environment[env]["boundary"]) - origin
    patch = draw_environment_boundary(ax, boundary)

    centres = np.asarray(cells["place_cell_centres"]) - origin
    responsive = np.asarray(cells["place_responsive_indices"], dtype=bool)
    field_centres = centres[responsive]
    width = cells["place_cell_width"]

    xmin, xmax = boundary[:, 0].min(), boundary[:, 0].max()
    ymin, ymax = boundary[:, 1].min(), boundary[:, 1].max()
    xs = np.linspace(xmin, xmax, grid_resolution)
    ys = np.linspace(ymin, ymax, grid_resolution)
    xx, yy = np.meshgrid(xs, ys)
    summed = np.zeros_like(xx)
    for cx, cy in field_centres:
        summed += np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * width ** 2))
    inside = MplPath(boundary).contains_points(np.stack([xx.ravel(), yy.ravel()], axis=1)).reshape(xx.shape)
    summed = np.where(inside, summed, np.nan)

    image = ax.imshow(summed, extent=(xmin, xmax, ymin, ymax), origin="lower", cmap=cmap, zorder=0.5)
    image.set_clip_path(patch)
    for cx, cy in field_centres:
        # Orange outline, not white -- white disappears against the light end
        # of the blue sequential colormap above (visible against viridis's
        # dark end, invisible against near-white low-density regions here).
        circle = MplCircle((cx, cy), width, fill=False, edgecolor=style.ENV_COLORS["B"], linewidth=0.6,
                            alpha=0.8, zorder=1)
        circle.set_clip_path(patch)
        ax.add_patch(circle)

    ax.set_aspect("equal")
    ax.set_title(env_title(env, sim), fontsize=8)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")

    if show_note:
        n_responsive, n_total = len(field_centres), len(responsive)
        note = f"{100 * n_responsive / n_total:.0f}% place-responsive\n({n_responsive}/{n_total} cells)"
        ax.text(0.98, 0.02, note, transform=ax.transAxes, fontsize=6, ha="right", va="bottom",
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#4d4d4d",
                           linewidth=0.6, alpha=0.85))

    if show_colorbar:
        cbar = ax.figure.colorbar(image, ax=ax, shrink=0.7, label="Summed field density (a.u.)")
        return cbar.ax
    return None


def _farthest_point_selection(points: np.ndarray, n: int) -> np.ndarray:
    """Indices of n points chosen greedily so each new pick maximizes its
    minimum distance to the ones already chosen -- keeps example_fields'
    small multiples spatially distinct instead of whichever n happen first
    in cell-index order (2026-10-23 request: "make sure that they are all
    fairly distinct examples"). Starts from the point farthest from the
    centroid so the first two picks are already maximally separated."""
    if len(points) <= n:
        return np.arange(len(points))
    centroid = points.mean(axis=0)
    chosen = [int(np.argmax(np.linalg.norm(points - centroid, axis=1)))]
    for _ in range(n - 1):
        remaining = np.setdiff1d(np.arange(len(points)), chosen)
        min_dist_to_chosen = np.min(
            np.linalg.norm(points[remaining][:, None, :] - points[chosen][None, :, :], axis=2), axis=1
        )
        chosen.append(int(remaining[np.argmax(min_dist_to_chosen)]))
    return np.array(chosen)


def example_fields(fig, sim: SimArtifact, env: str, *, n: int = 3,
                    grid_resolution: int = 100, cmap: str = "viridis", show_colorbar: bool = True):
    """Small-multiples grid of n individual real fields (one gaussian heatmap
    each, shared color scale) -- actual field shape/extent without summing
    dozens together (legacy setup_example_fields_{A,B}.png). The n fields are
    chosen by _farthest_point_selection, not the first n in cell-index order,
    so they're visibly spread across the environment rather than risking a
    cluster of overlapping/adjacent fields. Creates its own row of axes on
    fig since the panel count depends on n. `show_colorbar=False` on one of
    the two envs when both share the same fixed vmin=0/vmax=1 scale
    (2026-10-04 review: A and B each got their own identical-scale colorbar,
    the same duplication already fixed for trajectory_time/place_coverage) --
    but the colorbar gutter is still reserved on that env's row (just hidden,
    not omitted), so both rows' 3 panels occupy the same usable width and
    stay centered under each other (2026-10-23 review: "align env B so its
    center aligned with the env A graph" -- env A's row, with no colorbar,
    used to span the row's full width while env B's row shrank to leave room
    for one, so their centers didn't match)."""
    cells = sim.cells[env]
    origin = env_origin(sim.environment[env]["boundary"])
    boundary = np.asarray(sim.environment[env]["boundary"]) - origin
    centres = np.asarray(cells["place_cell_centres"]) - origin
    responsive = np.asarray(cells["place_responsive_indices"], dtype=bool)
    responsive_centres = centres[responsive]
    field_centres = responsive_centres[_farthest_point_selection(responsive_centres, n)]
    width = cells["place_cell_width"]

    xmin, xmax = boundary[:, 0].min(), boundary[:, 0].max()
    ymin, ymax = boundary[:, 1].min(), boundary[:, 1].max()
    xs = np.linspace(xmin, xmax, grid_resolution)
    ys = np.linspace(ymin, ymax, grid_resolution)
    xx, yy = np.meshgrid(xs, ys)
    inside = MplPath(boundary).contains_points(np.stack([xx.ravel(), yy.ravel()], axis=1)).reshape(xx.shape)

    axes = fig.subplots(1, len(field_centres), squeeze=False)[0]
    image = None
    for ax, (cx, cy) in zip(axes, field_centres):
        rate = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * width ** 2))
        rate = np.where(inside, rate, np.nan)
        patch = draw_environment_boundary(ax, boundary)
        image = ax.imshow(rate, extent=(xmin, xmax, ymin, ymax), origin="lower", cmap=cmap, vmin=0, vmax=1)
        image.set_clip_path(patch)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle(env_title(env, sim), fontsize=8)
    if image is None:
        return list(axes)
    # fig.colorbar always shrinks `axes` to make room, whether or not the
    # result ends up visible -- called unconditionally so both envs' rows
    # reserve the identical gutter width (see docstring); only the visible
    # one is kept in the returned/exported panel group.
    cbar = fig.colorbar(image, ax=list(axes), shrink=0.7,
                         label="Normalized firing rate" if show_colorbar else None)
    if not show_colorbar:
        cbar.ax.set_visible(False)
        return list(axes)
    # The colorbar's own Axes isn't picked up by any one subplot's
    # get_tightbbox() (it's a separately-created sibling Axes) -- append it
    # so a build.py panel group built from this return value includes it.
    return list(axes) + [cbar.ax]
