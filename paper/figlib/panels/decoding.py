"""Panels for decoding-performance figures, sourced from
produce/pull_decoding.py's scores.parquet (one row per combo x iteration x
kind x direction). Heatmap styling ported from
scripts/pull_and_plot_holdover_sweep.py's plot_metric_heatmaps/_draw_heatmap
(the existing convention for this exact sweep data -- see CLAUDE.md's
`robustness` row), adapted to read the tidy DataFrame instead of the script's
own per-log record list.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

from paper.figlib import style
from paper.figlib.io import DecodingArtifact

DIRECTIONS = ("A->A", "B->B", "A->B", "shuffA->A", "shuffA->B")
SWEPT_PARAMS = ("percent_task_in_response", "percent_task_responsive_cells", "percent_place_cells")


def direction_stats(decoding: DecodingArtifact, kind: str, fixed: dict[str, float] | None = None) -> pd.DataFrame:
    """One row per direction: mean +/- 95% CI (normal approx) across every
    combo x iteration in the sweep. n is large (combos x iterations) so this
    describes "how this model performs across the parameter space it was
    swept over", not one specific operating point -- unless `fixed` pins one
    or more swept params to a single value (e.g. the bioreal operating
    point), the same convention param_slice already uses, narrowing this to
    that specific point's iterations instead of the whole grid."""
    df = decoding.scores
    if fixed:
        mask = pd.Series(True, index=df.index)
        for column, value in fixed.items():
            mask &= df[column] == value
        df = df[mask]
    rows = []
    for direction in DIRECTIONS:
        values = df.loc[(df["kind"] == kind) & (df["direction"] == direction), "value"].dropna()
        n = len(values)
        mean = values.mean()
        sem = values.std(ddof=1) / np.sqrt(n)
        rows.append({"direction": direction, "mean": mean, "ci": 1.96 * sem, "n": n})
    return pd.DataFrame(rows)


def draw_direction_bars(ax, stats_by_model: dict[str, pd.DataFrame], *, model_colors: dict[str, str],
                         model_display_names: dict[str, str], directions: tuple[str, ...] = DIRECTIONS,
                         ylabel: str = "R²", chance_level: float | None = None, show_legend: bool = True,
                         tick_rotation: float = 20) -> None:
    """Grouped bar chart: one group per direction, one bar per model, mean +/-
    95% CI. A zero line is drawn since A->B/place R^2 can go negative.
    `directions` lets a figure show only a subset (e.g. within-env vs.
    cross-env as separate panels) instead of always all 5. `chance_level`
    draws a dashed reference line (e.g. 0.2 for task-decoding accuracy) in
    addition to the shuffled-control bars already in `directions` -- the two
    aren't redundant: the shuffled bars are this run's empirical floor, the
    line is the analytic chance level (2026-09-29 review item 4). Set
    `show_legend=False` on every panel but one when a figure calls this
    function more than once with the same models/colors -- otherwise the
    identical model-color legend repeats on every panel (2026-10-03 review).
    `tick_rotation=0` reads better when `directions` is short enough for the
    labels to fit horizontally (2026-10-04 review) -- default 20 degrees
    still applies when a figure shows all 5 directions on one panel."""
    models = list(stats_by_model)
    bar_width = 0.8 / len(models)
    x = np.arange(len(directions))

    for i, model in enumerate(models):
        stats = stats_by_model[model].set_index("direction").loc[list(directions)]
        offset = (i - (len(models) - 1) / 2) * bar_width
        ax.bar(x + offset, stats["mean"], yerr=stats["ci"], width=bar_width,
               color=model_colors[model], label=model_display_names.get(model, model),
               capsize=2)

    ax.axhline(0, color="black", linewidth=0.6, zorder=0)
    if chance_level is not None:
        ax.axhline(chance_level, color="black", linewidth=0.8, linestyle="--", zorder=0,
                   label=style.CHANCE_LABEL)
    tick_ha = "right" if tick_rotation else "center"
    ax.set_xticks(x, [style.direction_display_name(d) for d in directions], rotation=tick_rotation, ha=tick_ha)
    ax.set_ylabel(ylabel)
    if show_legend:
        ax.legend(fontsize=6, loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0.)


COMBO_PARAMS = ("percent_task_in_response", "percent_task_responsive_cells", "percent_place_cells", "holdover")


def _lower_is_better(kind: str) -> bool:
    """True for the cm-error place kinds, where a smaller value is the better
    one -- every other kind (task accuracy, place R^2) is higher-is-better."""
    return "_cm_" in kind


def _above_chance_table(decoding: DecodingArtifact, *, direction: str, kind: str,
                         z: float = 1.96) -> tuple["pd.Series", list[str]]:
    """Per-grid-point boolean: does this combo's real direction CI (mean +/-
    z*SEM across iterations) clear its paired shuffled floor's CI on the side
    that counts as "better" for this kind -- higher for R^2/accuracy, lower
    for cm error (see _lower_is_better)? CLAUDE.md's decided "above chance"
    test (CI non-overlap), not a bare point-estimate comparison -- see
    above_chance_fraction's docstring for why that distinction matters.
    Indexed by whichever of COMBO_PARAMS this artifact actually swept (varies
    per model -- e.g. arousal_mediated has no percent_task_in_response axis)."""
    df = decoding.scores
    combo_cols = [c for c in COMBO_PARAMS if df[c].notna().any()]
    shuffled_direction = f"shuff{direction}"
    subset = df[(df["kind"] == kind) & (df["direction"].isin((direction, shuffled_direction)))]
    agg = subset.groupby(combo_cols + ["direction"])["value"].agg(["mean", "sem"])
    pivot = agg.unstack("direction")

    real_mean, real_sem = pivot[("mean", direction)], pivot[("sem", direction)]
    shuffled_mean, shuffled_sem = pivot[("mean", shuffled_direction)], pivot[("sem", shuffled_direction)]
    if _lower_is_better(kind):
        better = (real_mean + z * real_sem) < (shuffled_mean - z * shuffled_sem)
    else:
        better = (real_mean - z * real_sem) > (shuffled_mean + z * shuffled_sem)
    return better, combo_cols


def above_chance_fraction(decoding: DecodingArtifact, *, direction: str = "A->B", kind: str = "task",
                           z: float = 1.96) -> tuple[float, int]:
    """Fraction of this model's swept grid points that clear chance on this
    kind/direction -- see _above_chance_table for the actual test."""
    above, _ = _above_chance_table(decoding, direction=direction, kind=kind, z=z)
    return float(above.mean()), len(above)


def shuffled_reference_value(decoding: DecodingArtifact, *, kind: str, direction: str,
                              fixed: dict[str, float] | None = None) -> float:
    """Mean value of this kind/direction's shuffled control -- the
    data-derived empirical floor, as opposed to an analytic constant like
    TASK_CHANCE_LEVEL. Pass the *real* direction (e.g. "A->B"), not the
    shuffled one -- this prepends "shuff" itself. Averages across the whole
    sweep by default (e.g. for a 3D reference-plane z-level); pass `fixed`
    (same convention as param_slice/direction_stats) to restrict to one
    operating point instead, e.g. so a bioreal-point figure's shuffled floor
    comes from that same point, not the whole grid."""
    shuffled_direction = f"shuff{direction}"
    df = decoding.scores
    if fixed:
        mask = pd.Series(True, index=df.index)
        for column, value in fixed.items():
            mask &= df[column] == value
        df = df[mask]
    return float(df.loc[(df["kind"] == kind) & (df["direction"] == shuffled_direction), "value"].mean())


def has_kind(decoding: DecodingArtifact, kind: str) -> bool:
    """Whether this artifact has any rows for this kind -- used to detect an
    approved sweep tag that predates a kind that didn't exist yet when it ran
    (e.g. the place R^2/cm in/out-of-task split, added after
    independent_sweep_080726 and place_dependent_sweep_080726 were run)."""
    return bool((decoding.scores["kind"] == kind).any())


LOWER_IS_BETTER_NOTE = "Lower = better (avg. position error, cm)"


def draw_model_row_header(fig, model_display_name: str, decoding_description: str | None = None,
                           stats_line: str | None = None, *, stats_color: str = "black",
                           lower_is_better: bool = False, compact: bool = False) -> None:
    """Header above (or, with `compact`, inside) one model's block of facets
    in a stacked multi-model grid figure: always a large bold model name
    (suptitle); `decoding_description` (medium line) / `stats_line` (small
    line, e.g. the beats-shuffle-floor fraction, or "DATA NOT AVAILABLE") /
    `lower_is_better` (large bold red "lower = better" note) are each
    optional and skipped when not given.

    robustness_3d.py/place_robustness_3d_within/cross (S2-S4) pass none of
    these -- that per-model info (what's decoded, lower-is-better, the
    beats-shuffle fraction) moved onto those figures' own per-model colorbar
    label instead (2026-10-04 review) -- model name is all that's left here
    for those three, drawn ABOVE the subfigure's own 0-1 range (y>1, into the
    hspace gap) with `compact=False` (the default): this only needs the one
    line, so it fits even in a short subfigure.

    robustness.py/place_robustness.py (S1/S5) pass the full 3-tier
    description and need `compact=True`: 3 stacked lines at fixed point
    sizes need a few inches of real vertical room regardless of how short the
    heatmap content below them is, so stacking them ABOVE y=1 (fractions of
    the content subfigure's own, possibly tiny, height) either collides or
    forces a huge content subfigure just to buy the header room it isn't
    using for content. `compact=True` instead draws WITHIN [0, 1] and expects
    `fig` to be a small subfigure dedicated to the header alone (2026-10-04
    whitespace-blowup fix) -- see those two figures' own module docstrings."""
    if compact:
        fig.suptitle(model_display_name, fontsize=20, fontweight="bold", y=0.92)
        # Remaining lines spread evenly across the rest of the header
        # subfigure's own height (not fixed-size steps from the top) so a
        # short header_fig isn't left with unused space at the bottom
        # (2026-10-04 review).
        lines: list[tuple[str, dict]] = []
        if decoding_description:
            lines.append((decoding_description, dict(fontsize=11)))
        if lower_is_better:
            lines.append((LOWER_IS_BETTER_NOTE, dict(fontsize=13, fontweight="bold", color="firebrick")))
        if stats_line:
            lines.append((stats_line, dict(fontsize=8, color=stats_color)))
        if lines:
            top, bottom = 0.56, 0.06
            ys = [top] if len(lines) == 1 else np.linspace(top, bottom, len(lines))
            for y, (text, kwargs) in zip(ys, lines):
                fig.text(0.5, y, text, ha="center", va="center", **kwargs)
        return
    fig.suptitle(model_display_name, fontsize=20, fontweight="bold", y=1.06)
    if decoding_description:
        fig.text(0.5, 1.01, decoding_description, ha="center", va="bottom", fontsize=11)
    stats_y = 0.965
    if lower_is_better:
        fig.text(0.5, 0.975, LOWER_IS_BETTER_NOTE, ha="center", va="top", fontsize=13, fontweight="bold",
                  color="firebrick")
        stats_y = 0.935
    if stats_line:
        fig.text(0.5, stats_y, stats_line, ha="center", va="top", fontsize=8, color=stats_color)


def draw_missing_data_placeholder(fig, message: str):
    """A single text-only Axes spanning `fig`, for a model block whose
    approved sweep tag doesn't have the kind this figure needs. Used instead
    of silently dropping the model (2026-10-02 policy: mark missing data
    explicitly in the figure itself, don't omit it or substitute an
    unapproved tag). Returns the created Axes."""
    ax = fig.add_subplot(1, 1, 1)
    ax.axis("off")
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=11, color="firebrick", wrap=True)
    return ax


# Shared 3-way parameter grid every independent/place_dependent/arousal_mediated
# sweep in this pipeline sweeps over (see CLAUDE.md's sweep design) -- used only
# to flag an in-flight sweep tag (independent_sweep_092926 as of 2026-10-03) as
# partial, never to validate a sweep's actual shape.
FULL_SWEEP_GRID_SIZE = 216


def partial_sweep_note(n_combos: int, full: int = FULL_SWEEP_GRID_SIZE) -> str:
    """' [PARTIAL SWEEP: n/full grid points]' to append to a title/suptitle
    when a tag's sweep isn't complete yet, '' otherwise."""
    return f" [PARTIAL SWEEP: {n_combos}/{full} grid points]" if n_combos < full else ""


def heatmap_pivot(decoding: DecodingArtifact, *, kind: str, direction: str,
                   facet_param: str, x_param: str, y_param: str, facet_value: float) -> pd.DataFrame:
    """Mean value over iterations, pivoted to a y_param x x_param grid, for
    one fixed facet_param value."""
    df = decoding.scores
    subset = df[(df["kind"] == kind) & (df["direction"] == direction) & (df[facet_param] == facet_value)]
    agg = subset.groupby([y_param, x_param], as_index=False)["value"].mean()
    return agg.pivot(index=y_param, columns=x_param, values="value")


def _param_tick_labels(values) -> list[str]:
    return [f"{v:g}" for v in values]


def metric_range(*decodings: DecodingArtifact, direction: str = "A->B", kind: str = "task") -> tuple[float, float]:
    """Min/max of one kind/direction across one or more decoding artifacts --
    pass every model's artifact here to get one shared color scale, rather
    than each model auto-scaling to its own narrow range (2026-09-29 review:
    IM's 0.2-0.62 task-accuracy range was making PDM/ADM's 0.19-0.27 range
    look just as strong once each got its own colorbar). `kind` generalizes
    this beyond task accuracy to the place_r2_*/place_cm_* kinds too."""
    values = pd.concat([
        d.scores.loc[(d.scores["kind"] == kind) & (d.scores["direction"] == direction), "value"]
        for d in decodings
    ])
    return float(values.min()), float(values.max())


def draw_task_transfer_heatmap_grid(fig, decoding: DecodingArtifact, *, kind: str = "task",
                                     direction: str = "A->B",
                                     facet_param: str = "percent_place_cells",
                                     x_param: str = "percent_task_in_response",
                                     y_param: str = "percent_task_responsive_cells",
                                     cmap: str | None = None, vmin: float | None = None,
                                     vmax: float | None = None, metric_label: str | None = None) -> list:
    """One annotated heatmap per facet_param value, laid out on a grid within
    fig (created here since the grid shape depends on how many facet values
    the sweep actually has -- not knowable by the figure module ahead of
    time). Shares one color scale and colorbar across all facets so they're
    directly comparable. Pass `vmin`/`vmax` (e.g. from metric_range over
    several models) to share the scale ACROSS figures/models too, instead of
    just within this one grid. `kind` generalizes this beyond task accuracy
    to the place_r2_*/place_cm_* kinds too (lower-is-better kinds get an
    auto-reversed colormap, via _lower_is_better, so "good" reads as the same
    color everywhere -- same convention as draw_metric_surface_facets).
    Returns the created Axes so the caller can register them as a build.py
    panel group."""
    cmap = cmap or ("viridis_r" if _lower_is_better(kind) else "viridis")
    df = decoding.scores
    facet_values = sorted(df[facet_param].dropna().unique())
    # 3 facets per row, not 6 (2026-10-04 review, reverted later the same
    # day): each facet is itself a dense x_param * y_param grid (commonly
    # 6x6=36 cells), so cramming 6 facets across one row left too little
    # width for even a 2-character value to be legible -- 3-per-row roughly
    # doubles each facet's width (and so its per-cell size) at the cost of a
    # second facet row, which is the tradeoff the per-cell text needs to stay
    # readable.
    ncols = min(3, len(facet_values))
    nrows = -(-len(facet_values) // ncols)
    # `fig` is expected to be a body-only SubFigure sized to just this grid's
    # content (its own [0, 1] range, no header sharing it -- see
    # draw_model_row_header's `compact` docstring) so top/bottom can stay
    # close to the edges instead of reserving room for a header above y=1.
    axes = fig.subplots(nrows, ncols, squeeze=False,
                         gridspec_kw={"hspace": 0.65, "wspace": 0.25, "top": 0.92, "bottom": 0.1})

    auto_vmin, auto_vmax = metric_range(decoding, direction=direction, kind=kind)
    vmin = auto_vmin if vmin is None else vmin
    vmax = auto_vmax if vmax is None else vmax
    metric_label = metric_label or (
        f"Task-stage decoding accuracy ({style.direction_display_name(direction)}, {style.CHANCE_LABEL.lower()})")

    # cm-error values run to 2 digits before the decimal point (e.g. "41.28")
    # where accuracy/R^2 values are always 0-1 ("0.66") -- fewer decimals
    # keeps the printed string short enough for the same cell width.
    annotate_decimals = 0 if _lower_is_better(kind) else 2

    image = None
    for ax, facet_value in zip(axes.flat, facet_values):
        pivot = heatmap_pivot(decoding, kind=kind, direction=direction, facet_param=facet_param,
                               x_param=x_param, y_param=y_param, facet_value=facet_value)
        image = draw_heatmap(ax, pivot, cmap=cmap, vmin=vmin, vmax=vmax, x_param=x_param, y_param=y_param,
                              annotate_decimals=annotate_decimals)
        ax.set_title(style.facet_title(facet_param, facet_value), fontsize=8)
    for ax in axes.flat[len(facet_values):]:
        ax.set_visible(False)
    # One shared x/y label for the whole facet row instead of repeating it
    # (and colliding with the next facet's title) in every panel (2026-10-04
    # whitespace/overlap review).
    fig.supxlabel(style.PARAM_DISPLAY_NAMES.get(x_param, x_param), fontsize=9, y=0.02)
    fig.supylabel(style.PARAM_DISPLAY_NAMES.get(y_param, y_param), fontsize=9, x=0.02)
    if image is not None:
        fig.colorbar(image, ax=axes, shrink=0.7, label=metric_label)
    return list(axes.flat[:len(facet_values)])


def draw_heatmap(ax, pivot: pd.DataFrame, *, cmap: str = "viridis", vmin: float, vmax: float,
                  x_param: str | None = None, y_param: str | None = None, annotate: bool = True,
                  annotate_fontsize: float = 6.5, annotate_decimals: int = 2):
    """Draw one heatmap of a metric over two swept parameters -- ported from
    pull_and_plot_holdover_sweep.py's _draw_heatmap, including its per-cell
    value text (white/black, chosen by contrast against the cell's color) so
    an exact value is still readable without tracing back to the shared
    colorbar. `x_param`/`y_param` (when given) rescale tick labels to
    percentages for params in style.PERCENT_DISPLAY_PARAMS, matching
    draw_param_lines' axis convention.

    2026-10-04 review: per-cell text was dropped entirely for one build (it
    overlapped at 6 facets/row x 6x6 cells/facet) -- reverted the same day
    after review: an unreadable grid of numbers is a real complaint, but a
    grid with no numbers at all is a worse one. The fix that stuck is sizing
    cells to fit the text (see draw_task_transfer_heatmap_grid's ncols=3, not
    removing the text) -- `annotate_fontsize` is a knob for a caller with an
    unusually small/large grid, not something this function decides for
    itself. `aspect="equal"` (was "auto"): square cells, not stretched -- a
    cell should read as a unit of the same param-step size on both axes.
    `annotate_decimals` defaults to accuracy/R^2's 0-1 range (e.g. "0.66");
    draw_task_transfer_heatmap_grid overrides it to 0 for cm-error kinds
    (e.g. "41", not "41.28") -- those values run to 2 digits before the
    decimal point, and the extra digit plus decimals together no longer fit
    the same cell width 2-decimal accuracy values do (2026-10-04 review).

    Missing grid points (NaN in `pivot` -- an in-flight sweep tag) are drawn
    as a light gray diagonal hatch instead of imshow's default (transparent,
    indistinguishable from the plot background) -- see the caller's own
    legend entry for what the hatch means."""
    x_scale = 100 if x_param in style.PERCENT_DISPLAY_PARAMS else 1
    y_scale = 100 if y_param in style.PERCENT_DISPLAY_PARAMS else 1
    image = ax.imshow(pivot.values, cmap=cmap, vmin=vmin, vmax=vmax, aspect="equal", origin="lower")
    ax.set_xticks(range(len(pivot.columns)), _param_tick_labels(pivot.columns * x_scale))
    ax.set_yticks(range(len(pivot.index)), _param_tick_labels(pivot.index * y_scale))
    span = (vmax - vmin) or 1.0
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            value = pivot.values[i, j]
            if np.isnan(value):
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor="white", edgecolor="#bbbbbb",
                                        hatch="////", linewidth=0.4, zorder=2))
            elif annotate:
                text_color = "white" if (value - vmin) / span < 0.55 else "black"
                ax.text(j, i, f"{value:.{annotate_decimals}f}", ha="center", va="center", color=text_color,
                        fontsize=annotate_fontsize)
    return image


# --- 3D surface facets, ported verbatim (camera, colors, z-scale) from -------
# scripts/pull_and_plot_holdover_sweep.py's plot_metric_surface_facets -- the
# same function webui/sweep_plots.py reuses for /jobs/{id}/results. Restored
# 2026-09-29 as its own supplementary figure (robustness_3d) alongside the 2D
# heatmap version (robustness.py) -- some readers want the 3D shape, not just
# the flattened grid -- with the shared-scale fix (`vmin`/`vmax`) applied
# here too, the same fix already made to the 2D heatmaps: giving each model
# its own z-scale previously made PDM/ADM's near-chance surfaces look as
# textured/dramatic as IM's, which is the thing this fix corrects.

SURFACE_ZOOM = 0.82  # <1 pulls the camera back a bit from Axes3D's default zoom=1


def _orient_surface_from_origin(ax) -> None:
    """Camera so (x=0, y=0) sits at the near/bottom-right corner. Matplotlib's
    default 3D camera puts (0, 0) at the bottom-left with both axes receding
    away from there; inverting the x-axis swaps that to the bottom-right
    without touching y, so both x_var and y_var read as "moving away from the
    origin" as they increase, wherever a viewer looks from."""
    ax.invert_xaxis()
    ax.set_box_aspect(None, zoom=SURFACE_ZOOM)


_AXIS_LABELS = {"task": "Accuracy"}


def _default_axis_label(kind: str) -> str:
    """Short z-axis tick label -- the full metric description goes on the
    colorbar and the figure's block title instead (2026-10-02 review: the
    full description used directly as the z-axis label collided with the
    x/y param labels on every facet, and was unreadable rotated vertically)."""
    if kind in _AXIS_LABELS:
        return _AXIS_LABELS[kind]
    if kind.startswith("place_r2"):
        return "R²"
    if kind.startswith("place_cm"):
        return "Error (cm)"
    return kind


def draw_metric_surface_facets(fig, decoding: DecodingArtifact, *, kind: str = "task", direction: str = "A->B",
                                x_var: str, y_var: str, facet_var: str, cmap: str | None = None,
                                marker_size: float = 60, metric_label: str | None = None,
                                axis_label: str | None = None, vmin: float | None = None,
                                vmax: float | None = None, reference_plane: bool = False,
                                highlight_above_chance: bool = False) -> list:
    """One 3D surface per facet_var value: the metric (z height) over x_var by
    y_var. Pass `vmin`/`vmax` (e.g. from metric_range over several models) to
    share the color+z scale ACROSS models/figures instead of each facet grid
    auto-scaling to its own data. Axis/facet labels use
    style.PARAM_DISPLAY_NAMES and percent formatting, matching the 2D heatmap
    grid's convention. `kind`/`direction` are the switch between task
    accuracy, place R^2 and place cm-error (lower-is-better kinds get an
    auto-reversed colormap, via _lower_is_better, so "good" reads as the same
    color everywhere) -- a figure module picks these, nothing else about this
    function changes. `metric_label` (full description) goes on the shared
    colorbar; `axis_label` (short -- defaults via _default_axis_label) goes on
    each facet's z-axis, since the full description there used to collide
    with the x/y param labels. `reference_plane` draws a translucent plane at
    this kind/direction's mean shuffled value (shuffled_reference_value).
    `highlight_above_chance` outlines grid points whose CI clears the shuffled
    CI (_above_chance_table) with a black ring, on top of their normal
    color-coded marker. Returns the created Axes3D list (one per facet) so the
    caller can register them as a build.py panel group.

    Sizing is the caller's responsibility: give `fig` too little width and 3D
    axes' tick/label decoration and facet titles will collide -- a sizing
    problem to fix at the call site, not something to paper over here."""
    metric_label = metric_label or (
        f"Task-stage decoding accuracy ({style.direction_display_name(direction)}, {style.CHANCE_LABEL.lower()})")
    axis_label = axis_label or _default_axis_label(kind)
    cmap = cmap or ("viridis_r" if _lower_is_better(kind) else "viridis")

    df = decoding.scores
    subset = df[(df["kind"] == kind) & (df["direction"] == direction)]
    combo_cols = [c for c in COMBO_PARAMS if subset[c].notna().any()]
    agg = subset.groupby(combo_cols, as_index=False)["value"].mean()

    if highlight_above_chance:
        above, _ = _above_chance_table(decoding, direction=direction, kind=kind)
        agg = agg.set_index(combo_cols)
        agg["above_chance"] = above.reindex(agg.index).fillna(False)
        agg = agg.reset_index()

    facet_values = sorted(agg[facet_var].dropna().unique())
    x_values = sorted(agg[x_var].dropna().unique())
    y_values = sorted(agg[y_var].dropna().unique())
    mesh_x, mesh_y = np.meshgrid(x_values, y_values)
    auto_vmin, auto_vmax = float(np.nanmin(agg["value"])), float(np.nanmax(agg["value"]))
    vmin = auto_vmin if vmin is None else vmin
    vmax = auto_vmax if vmax is None else vmax
    reference_z = shuffled_reference_value(decoding, kind=kind, direction=direction) if reference_plane else None

    x_scale = 100 if x_var in style.PERCENT_DISPLAY_PARAMS else 1
    y_scale = 100 if y_var in style.PERCENT_DISPLAY_PARAMS else 1

    ncols = min(3, len(facet_values))
    nrows = -(-len(facet_values) // ncols)
    surface = None
    created_axes = []
    for idx, facet_value in enumerate(facet_values):
        ax = fig.add_subplot(nrows, ncols, idx + 1, projection="3d")
        created_axes.append(ax)
        panel = agg[agg[facet_var] == facet_value]
        mesh_z = (panel.pivot_table(index=y_var, columns=x_var, values="value")
                  .reindex(index=y_values, columns=x_values).values)
        surface = ax.plot_surface(mesh_x * x_scale, mesh_y * y_scale, mesh_z, cmap=cmap, vmin=vmin, vmax=vmax,
                                   edgecolor="black", linewidth=0.3, alpha=0.55, antialiased=True)
        valid = ~np.isnan(mesh_z.ravel())
        ax.scatter((mesh_x.ravel() * x_scale)[valid], (mesh_y.ravel() * y_scale)[valid], mesh_z.ravel()[valid],
                   c=mesh_z.ravel()[valid], cmap=cmap, vmin=vmin, vmax=vmax,
                   s=marker_size, edgecolors="white", linewidths=0.5, depthshade=False)

        if reference_z is not None:
            plane_z = np.full_like(mesh_x, reference_z, dtype=float)
            ax.plot_surface(mesh_x * x_scale, mesh_y * y_scale, plane_z, color="gray", alpha=0.15,
                             linewidth=0, shade=False, antialiased=False)

        if highlight_above_chance:
            above_panel = panel[panel["above_chance"]]
            if not above_panel.empty:
                ax.scatter(above_panel[x_var] * x_scale, above_panel[y_var] * y_scale, above_panel["value"],
                           facecolors="none", edgecolors="black", linewidths=1.3, s=marker_size * 1.8,
                           depthshade=False)

        ax.set_zlim(vmin, vmax)
        ax.set_xlabel(style.PARAM_DISPLAY_NAMES.get(x_var, x_var), fontsize=8)
        ax.set_ylabel(style.PARAM_DISPLAY_NAMES.get(y_var, y_var), fontsize=8)
        ax.set_zlabel(axis_label, fontsize=9)
        ax.set_title(style.facet_title(facet_var, facet_value), fontsize=10)
        _orient_surface_from_origin(ax)

    # A partial sweep can leave fewer facet_values than the nrows x ncols grid
    # has slots for (e.g. 5 values -> a 2x3 grid) -- labeling that leftover
    # slot explicitly rather than leaving an unexplained blank space
    # (2026-10-03 review: read as "an empty sixth facet").
    for idx in range(len(facet_values), nrows * ncols):
        ax = fig.add_subplot(nrows, ncols, idx + 1)
        ax.axis("off")
        ax.text(0.5, 0.5, "No data yet\n(partial sweep)", ha="center", va="center",
                fontsize=8, color="gray")
        created_axes.append(ax)

    if surface is None:
        return created_axes
    # The colorbar is a separate sibling Axes, not part of any one facet's own
    # tight bbox -- append it so a caller's build.py panel group includes it.
    cbar = fig.colorbar(surface, ax=fig.axes, label=metric_label, shrink=0.5, pad=0.08)
    return created_axes + [cbar.ax]


def param_slice(decoding: DecodingArtifact, *, param: str, fixed: dict[str, float], direction: str = "A->B",
                 kind: str = "task") -> pd.DataFrame:
    """mean +/- 95% CI of direction/kind per `param` value, at every other
    swept param held to `fixed`'s value -- a slice through an existing
    matched multi-axis grid, not a dedicated single-axis sweep on `param`
    (use this whenever aggregating across `param` instead would average over
    a real, non-flat dependence -- see 2026-09-25 chat: position_decoding's
    R^2 swings from +0.2 to -0.33 across percent_task_in_response alone, so a
    single aggregated bar would misrepresent it; task_decoding's R^2 is flat
    across the same axis, so direction_stats' full-sweep aggregate is fine
    there)."""
    df = decoding.scores
    mask = (df["kind"] == kind) & (df["direction"] == direction)
    for column, value in fixed.items():
        mask &= df[column] == value
    rows = []
    for param_value, group in df[mask].groupby(param):
        n = len(group)
        sem = group["value"].std(ddof=1) / np.sqrt(n)
        rows.append({param: param_value, "mean": group["value"].mean(), "ci": 1.96 * sem, "n": n})
    return pd.DataFrame(rows).sort_values(param)


def draw_param_lines(ax, param: str, series: dict[str, pd.DataFrame], *, colors: dict[str, str],
                      display_names: dict[str, str] | None = None, marker_value: float | None = None,
                      marker_label: str | None = None, ylabel: str = "R²",
                      chance_level: float | None = None, show_legend: bool = True) -> None:
    """One line per series (a model, or a task-state, or anything else keyed
    by `series`'s dict keys): mean +/- 95% CI vs. `param`. An optional
    vertical marker flags a reference value (e.g. bioreal's chosen point).
    `param` values are stored as 0-1 fractions; params in
    style.PERCENT_DISPLAY_PARAMS are rescaled to 0-100 here so the axis reads
    "20" rather than "0.2" (2026-09-29 review item 3). Set `show_legend=False`
    on every panel but one when a figure calls this more than once with the
    same series keys/colors -- otherwise the identical legend repeats on
    every panel (2026-10-03 review)."""
    display_names = display_names or {}
    is_percent = param in style.PERCENT_DISPLAY_PARAMS
    scale = 100 if is_percent else 1

    # zorder=0: the reference marker line is drawn first in source order but
    # defaults to matplotlib's normal z-stacking (same as the data drawn
    # after it), which put it visually on top of/level with the error bars --
    # an explicit low zorder keeps it behind the data it's a reference for
    # (2026-10-04 review).
    if marker_value is not None:
        ax.axvline(marker_value * scale, color="black", linestyle="--", linewidth=1, alpha=0.5, zorder=0,
                   label=marker_label)
    for key, slice_df in series.items():
        ax.errorbar(slice_df[param] * scale, slice_df["mean"], yerr=slice_df["ci"],
                    color=colors[key], label=display_names.get(key, key),
                    marker="o", markersize=4, capsize=3, zorder=2)
    if chance_level is not None:
        ax.axhline(chance_level, color="black", linewidth=0.8, linestyle=":", alpha=0.7,
                   label=style.CHANCE_LABEL)
    ax.set_xlabel(style.PARAM_DISPLAY_NAMES.get(param, param))
    ax.set_ylabel(ylabel)
    if show_legend:
        ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0.)


def extend_ylim_for_floors(ax, floors: list[float], *, pad: float = 1.0) -> None:
    """Widen ax's y-limits to include every value in `floors` if they'd
    otherwise fall outside the data-driven range. axhline's y-value isn't
    picked up by matplotlib's data-driven autoscale (it uses a blended
    transform, which relim()/autoscale_view() skip) -- without this, a
    shuffled-baseline reference line below/above the error-bar-driven range
    would be drawn off the edge of the visible axes (2026-10-03 review).
    `pad` is in the same units as the plotted metric -- the default of 1 is
    sized for cm-error panels (position_decoding.py); a 0-1 accuracy panel
    (task_decoding_by_balance.py) needs a much smaller pad, e.g. 0.02, or the
    default swamps the whole 0-1 range (2026-10-05 fix)."""
    bottom, top = ax.get_ylim()
    ax.set_ylim(min(bottom, min(floors) - pad), max(top, max(floors) + pad))


def share_ylim(axes_list) -> None:
    """One y-range across every Axes passed in, not just within a model's own
    row or column -- so the axis numbers themselves are directly comparable
    across models/directions (2026-10-05 request), not just the line shapes.
    Call after every panel on every Axes in the group has been drawn (and any
    extend_ylim_for_floors calls made), so each Axes' own get_ylim() already
    reflects everything that needs to fit."""
    bottoms, tops = zip(*(ax.get_ylim() for ax in axes_list))
    shared = (min(bottoms), max(tops))
    for ax in axes_list:
        ax.set_ylim(shared)


