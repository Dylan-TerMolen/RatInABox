"""Grid-sweep aggregation for the /jobs/{id}/results page -- the web-app
equivalent of scripts/pull_and_plot_holdover_sweep.py's plotting half, but
reading from this job's already-matched job_iterations rows (see db.py,
routers/results.py) instead of re-deriving swept params from log filenames.
Pulling/matching logs onto iterations is handled elsewhere; this module only
reads what's already landed. Actual figure rendering lives in
sweep_plots.py, which reuses this module's records/axes.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path
from urllib.parse import urlencode

from . import db, hsw_log

# Every '<kind>  key: val ...' line a log can carry (4 task-state x metric
# place lines plus the pooled task line -- see hsw_log.py's module docstring),
# in a fixed order, so the metric toggle list on the page is stable across
# jobs/models.
DECODER_KINDS = hsw_log.ITERATION_KINDS
METRIC_KEYS = [f"{kind}_{key}" for kind in DECODER_KINDS for key in hsw_log.SCORE_KEYS]
DEFAULT_METRIC = "task_A->B"  # cross-environment task decoding -- the headline metric

# Best-effort substring match from a job's resolved param flag names (which
# drift over time -- see project memory on percent_task_in_response's
# several renames) to the three axes this page defaults to. First candidate
# whose key contains one of a role's patterns wins; see infer_axes().
AXIS_PATTERNS = {
    "facet": ("place_cells",),
    "x": ("task_in_response",),
    "y": ("task_responsive_cells", "responsive_cells", "task_cells"),
}

# Facet-var choices beyond the pattern-matched default above -- holdover is
# swept independently of the default x/y/facet grid on the
# *_holdover_grid_at_point_* sweep scripts (percent_place_cells pinned,
# holdover swept instead of it), so it never pattern-matches into facet on
# its own. Mirrors pull_and_plot_holdover_sweep.py's --facet-var switch; see
# facet_var_options() and infer_axes().
FACET_VAR_ALTERNATES = ("holdover",)

# Every pattern that names a "real" swept simulation param, as opposed to
# incidental fixed scalars like num_iters -- used to keep the fixed-value
# selector (fixed_axis_options()) limited to params worth surfacing.
_KNOWN_SWEEP_PATTERNS = tuple(
    pattern for patterns in AXIS_PATTERNS.values() for pattern in patterns
) + FACET_VAR_ALTERNATES


def numeric_or_none(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mean_scores(parsed_log: hsw_log.ParsedLog) -> dict[str, float | None]:
    """Average each decoding score across a log's internal iterations -- a
    sweep's array task reruns main.py NUM_ITERS times into one file."""
    samples: dict[str, list[float]] = {key: [] for key in METRIC_KEYS}
    for iteration in parsed_log.iterations:
        for kind in DECODER_KINDS:
            for key, value in iteration.kind(kind).items():
                if value is not None:
                    samples[f"{kind}_{key}"].append(value)
    return {key: (statistics.fmean(values) if values else None) for key, values in samples.items()}


def _iteration_record(row) -> dict | None:
    path = Path(row["log_file_path"])
    if not path.is_file():
        return None
    parsed = hsw_log.parse(path.read_text())
    params = json.loads(row["params_json"])
    return {**params, **_mean_scores(parsed)}


def job_sweep_records(job_id: int) -> list[dict]:
    """One record per matched iteration: its resolved params plus mean
    decoding scores. Iterations without a matched log yet are skipped."""
    rows = [row for row in db.list_job_iterations(job_id) if row["log_file_path"]]
    records = (_iteration_record(row) for row in rows)
    return [record for record in records if record is not None]


def _numeric_values(records: list[dict], key: str) -> set[float]:
    values = {numeric_or_none(record.get(key)) for record in records}
    values.discard(None)
    return values


def varying_numeric_params(records: list[dict]) -> list[str]:
    """Param keys (excluding metric columns) with at least one numeric value
    across records -- the candidate pool for facet/x/y assignment."""
    if not records:
        return []
    keys = [key for key in records[0] if key not in METRIC_KEYS]
    return [key for key in keys if _numeric_values(records, key)]


def facet_var_options(records: list[dict]) -> list[str]:
    """Param keys selectable as the facet variable via the results page's
    'Facet variable' control: the pattern-matched default
    (percent_place_cells) first, then any alternates (holdover) that
    actually vary in this job's records -- an alternate stuck at one value
    (e.g. holdover on an ordinary, non-holdover-grid sweep) would just be a
    single-panel no-op if picked, so it's left out rather than cluttering
    the selector on every job."""
    candidates = varying_numeric_params(records)
    default = [key for key in candidates if any(pattern in key for pattern in AXIS_PATTERNS["facet"])]
    alternates = [key for key in candidates
                  if key not in default and any(pattern in key for pattern in FACET_VAR_ALTERNATES)
                  and len(_numeric_values(records, key)) > 1]
    return default + alternates


def infer_axes(records: list[dict], facet_var: str | None = None) -> dict[str, str | None]:
    """Best-effort facet/x/y param assignment. An explicit *facet_var*
    (from the results page's selector) wins the facet slot if it's a real
    candidate; x/y -- and facet, when no override was given -- are then
    pattern-matched against current flag naming, falling back to whatever
    candidates are left."""
    candidates = varying_numeric_params(records)
    assigned: dict[str, str | None] = {"facet": None, "x": None, "y": None}
    if facet_var in candidates:
        assigned["facet"] = facet_var
    for role, patterns in AXIS_PATTERNS.items():
        if assigned[role] is not None:
            continue
        assigned[role] = next(
            (key for key in candidates if key not in assigned.values()
             and any(pattern in key for pattern in patterns)),
            None,
        )
    # x/y are required to plot anything; facet is optional in principle, but
    # plot_metric_surface_facets (sweep_plots.py) needs a real facet column
    # too, so a two-axis job just won't have a plottable metric -- see
    # metric_available().
    leftover = [key for key in candidates if key not in assigned.values()]
    for role in ("x", "y", "facet"):
        if assigned[role] is None and leftover:
            assigned[role] = leftover.pop(0)
    return assigned


def fixed_axis_options(records: list[dict], axes: dict[str, str | None]) -> dict[str, list[float]]:
    """Swept-looking params left out of x/y/facet -- e.g. percent_place_cells
    once facet_var=holdover has taken the facet slot instead -- each mapped
    to its distinct values. Without pinning one of these, a leftover axis
    with more than one value would get silently averaged over in the
    surface's pivot_table; see resolve_fixed_selection() and
    filter_records_by_fixed()."""
    used = {axes["facet"], axes["x"], axes["y"]}
    candidates = [key for key in varying_numeric_params(records)
                  if key not in used and any(pattern in key for pattern in _KNOWN_SWEEP_PATTERNS)]
    return {key: sorted(_numeric_values(records, key)) for key in candidates}


def resolve_fixed_selection(fixed_options: dict[str, list[float]],
                             requested: dict[str, str] | None) -> dict[str, float]:
    """One concrete value per fixed_axis_options() key: the requested value
    if it's actually one of the available options, else the smallest one."""
    requested = requested or {}
    resolved = {}
    for key, values in fixed_options.items():
        if not values:
            continue
        chosen = numeric_or_none(requested.get(key))
        resolved[key] = chosen if chosen in values else values[0]
    return resolved


def filter_records_by_fixed(records: list[dict], fixed: dict[str, float]) -> list[dict]:
    """Keep only records whose value for every pinned {param: value} matches."""
    def matches(record: dict) -> bool:
        return all(numeric_or_none(record.get(key)) == value for key, value in fixed.items())
    return [record for record in records if matches(record)]


def resolve_view(records: list[dict], facet_var: str | None = None,
                  fixed_request: dict[str, str] | None = None):
    """axes, fixed-value options/selection, and the records filtered to that
    selection -- the shared computation build_results_view (the page) and
    routers/jobs.py's plot endpoint both need, so a metric's toggle
    availability and its actual rendered image always agree."""
    axes = infer_axes(records, facet_var)
    fixed_options = fixed_axis_options(records, axes)
    resolved_fixed = resolve_fixed_selection(fixed_options, fixed_request)
    filtered = filter_records_by_fixed(records, resolved_fixed)
    return axes, fixed_options, resolved_fixed, filtered


def _plot_query_suffix(facet_var: str | None, fixed: dict[str, float]) -> str:
    """Querystring fragment (leading '&') that reproduces the current
    facet-var/fixed-value selection on the per-metric plot endpoint, so a
    lazily-loaded image matches what the page's own axes/availability used."""
    params = {}
    if facet_var:
        params["facet_var"] = facet_var
    params.update({f"fixed_{key}": value for key, value in fixed.items()})
    return f"&{urlencode(params)}" if params else ""


def metric_available(records: list[dict], metric: str, axes: dict) -> bool:
    """Whether this metric has at least one record with a value and valid
    x/y/facet coordinates -- i.e. whether there's anything to render."""
    x_key, y_key, facet_key = axes["x"], axes["y"], axes["facet"]
    if not (x_key and y_key and facet_key):
        return False
    return any(
        record.get(metric) is not None
        and numeric_or_none(record.get(x_key)) is not None
        and numeric_or_none(record.get(y_key)) is not None
        and numeric_or_none(record.get(facet_key)) is not None
        for record in records
    )


def build_results_view(job_id: int, facet_var: str | None = None,
                        fixed_request: dict[str, str] | None = None) -> dict:
    """Everything the results template needs: which metrics have data to
    plot, the resolved facet/x/y axes (honoring an explicit facet_var
    override), and the fixed-value selector state for whatever swept param
    the chosen facet_var left out. Actual PNG rendering is deferred to
    sweep_plots.py, called on demand per metric (see routers/jobs.py)."""
    records = job_sweep_records(job_id)
    axes, fixed_options, resolved_fixed, filtered = resolve_view(records, facet_var, fixed_request)
    return {
        "records_count": len(records),
        "axes": axes,
        "facet_options": facet_var_options(records),
        "fixed_options": [
            {"key": key, "selected": resolved_fixed[key],
             "choices": [{"value": value, "label": f"{value:g}"} for value in values]}
            for key, values in fixed_options.items()
        ],
        "plot_query_suffix": _plot_query_suffix(axes["facet"], resolved_fixed),
        "metrics": [
            {"key": metric, "label": metric.replace("_", " "),
             "available": metric_available(filtered, metric, axes), "default": metric == DEFAULT_METRIC}
            for metric in METRIC_KEYS
        ],
    }
