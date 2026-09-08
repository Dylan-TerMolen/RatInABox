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

# Pre-ead368e logs (before place decoding was split by task state) carry a
# single pooled-R^2 'place' line instead of the four place_*_in/out_of_task
# lines -- see hsw_log.py's module docstring and git history. Recognized as
# its own distinct metric, not merged into place_r2_in_task (which would
# falsely claim we know the task-state split for those older runs), so a
# legacy job still shows *something* for place decoding instead of every
# place metric reading "no data". hsw_log.parse already captures any
# '<kind> ...' line generically -- this is purely a webui-side addition.
LEGACY_PLACE_KIND = "place"

# Every '<kind>  key: val ...' line a log can carry (4 task-state x metric
# place lines plus the pooled task line -- see hsw_log.py's module docstring
# -- plus the legacy pooled place line above), in a fixed order, so the
# metric toggle list on the page is stable across jobs/models.
DECODER_KINDS = hsw_log.ITERATION_KINDS + [LEGACY_PLACE_KIND]
METRIC_KEYS = [f"{kind}_{key}" for kind in DECODER_KINDS for key in hsw_log.SCORE_KEYS]
DEFAULT_METRIC = "task_A->B"  # cross-environment task decoding -- the headline metric
DEFAULT_PLACE_METRIC = "place_r2_in_task_A->B"  # place's own headline: cross-environment, in-task, R^2
DEFAULT_LEGACY_PLACE_METRIC = f"{LEGACY_PLACE_KIND}_A->B"  # same headline direction, for jobs with only the legacy line

# family/task_state/measure per ITERATION_KINDS entry, explicit rather than
# parsed back out of the kind string -- one place to update if a kind is
# ever added or renamed. Place's 4 kinds collapse to two independent
# toggles on the results page (task_state, measure); task and the legacy
# place line have neither, so each is shown as its own ungrouped section.
# See build_results_view().
KIND_METADATA = {
    "place_r2_in_task": {"family": "place", "task_state": "in_task", "measure": "r2"},
    "place_cm_in_task": {"family": "place", "task_state": "in_task", "measure": "cm"},
    "place_r2_out_of_task": {"family": "place", "task_state": "out_of_task", "measure": "r2"},
    "place_cm_out_of_task": {"family": "place", "task_state": "out_of_task", "measure": "cm"},
    "task": {"family": "task", "task_state": None, "measure": None},
    LEGACY_PLACE_KIND: {"family": "place_legacy", "task_state": None, "measure": "r2"},
}

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

# Recorded CLI params that are never a meaningful sweep axis, even if a job
# happens to vary them across iterations. num_iters controls how many times
# main.py reruns *within* a single array task -- those reruns are already
# averaged together by _mean_scores into one record -- so it's a rerun count,
# not a swept simulation dimension. Filtered out in varying_numeric_params()
# so it can never be picked up by infer_axes()'s pattern-match, its leftover
# fallback, or fixed_axis_options().
EXCLUDED_PARAM_KEYS = {"num_iters"}


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
    keys = [key for key in records[0] if key not in METRIC_KEYS and key not in EXCLUDED_PARAM_KEYS]
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


def infer_axes(records: list[dict], x_var: str | None = None, y_var: str | None = None,
                facet_var: str | None = None) -> dict[str, str | None]:
    """Best-effort facet/x/y param assignment. Explicit *x_var*/*y_var*/*facet_var*
    (from the results page's Manual axis selectors, or facet_var alone from the
    Auto-mode facet override) win their slot if they're a real candidate and not
    already claimed by an earlier role in facet/x/y precedence order; whichever
    roles are left unset are then pattern-matched against current flag naming,
    falling back to whatever candidates remain. Passing none of the three
    reproduces pure auto-detection for all axes."""
    candidates = varying_numeric_params(records)
    assigned: dict[str, str | None] = {"facet": None, "x": None, "y": None}
    for role, override in (("facet", facet_var), ("x", x_var), ("y", y_var)):
        if override in candidates and override not in assigned.values():
            assigned[role] = override
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


def resolve_view(records: list[dict], x_var: str | None = None, y_var: str | None = None,
                  facet_var: str | None = None, fixed_request: dict[str, str] | None = None):
    """axes, fixed-value options/selection, and the records filtered to that
    selection -- the shared computation build_results_view (the page) and
    routers/jobs.py's plot endpoint both need, so a metric's toggle
    availability and its actual rendered image always agree."""
    axes = infer_axes(records, x_var, y_var, facet_var)
    fixed_options = fixed_axis_options(records, axes)
    resolved_fixed = resolve_fixed_selection(fixed_options, fixed_request)
    filtered = filter_records_by_fixed(records, resolved_fixed)
    return axes, fixed_options, resolved_fixed, filtered


def _plot_query_suffix(x_var: str | None, y_var: str | None, facet_var: str | None,
                        fixed: dict[str, float]) -> str:
    """Querystring fragment (leading '&') that reproduces the current
    x/y/facet-var/fixed-value selection on the per-metric plot endpoint, so a
    lazily-loaded image matches what the page's own axes/availability used.
    Always pins the *resolved* axes (not just an explicit override) so the
    plot endpoint's own auto-detection -- run independently, on whatever
    records that request happens to filter to -- can never disagree with what
    the page actually displayed."""
    params = {}
    if x_var:
        params["x_var"] = x_var
    if y_var:
        params["y_var"] = y_var
    if facet_var:
        params["facet_var"] = facet_var
    params.update({f"fixed_{key}": value for key, value in fixed.items()})
    return f"&{urlencode(params)}" if params else ""


def _metric_specs():
    """(metric_key, kind, direction) for every entry in METRIC_KEYS, in order --
    the pieces build_results_view needs to tag each metric with its
    family/task_state/measure without re-parsing the key string."""
    return [
        (f"{kind}_{direction}", kind, direction)
        for kind in DECODER_KINDS
        for direction in hsw_log.SCORE_KEYS
    ]


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


def build_results_view(job_id: int, x_var: str | None = None, y_var: str | None = None,
                        facet_var: str | None = None,
                        fixed_request: dict[str, str] | None = None) -> dict:
    """Everything the results template needs: which metrics have data to
    plot, the resolved facet/x/y axes (honoring explicit x_var/y_var/facet_var
    overrides -- the results page's Manual axis selectors, or facet_var alone
    from the Auto-mode facet override), and the fixed-value selector state for
    whatever swept param the chosen axes left out. manual_mode reflects
    whether x_var/y_var were actually passed, so the page's Auto/Manual
    toggle renders in the right state on reload (a bare facet_var override
    alone still counts as Auto -- that control predates and is independent
    of the manual x/y selectors). Each metric carries its family/task_state/
    measure (see KIND_METADATA) so the template can group place's four kinds
    behind two toggles instead of listing them all flat. Actual PNG
    rendering is deferred to sweep_plots.py, called on demand per metric
    (see routers/jobs.py)."""
    records = job_sweep_records(job_id)
    axes, fixed_options, resolved_fixed, filtered = resolve_view(records, x_var, y_var, facet_var, fixed_request)
    return {
        "records_count": len(records),
        "axes": axes,
        "manual_mode": bool(x_var or y_var),
        "axis_options": varying_numeric_params(records),
        "facet_options": facet_var_options(records),
        "fixed_options": [
            {"key": key, "selected": resolved_fixed[key],
             "choices": [{"value": value, "label": f"{value:g}"} for value in values]}
            for key, values in fixed_options.items()
        ],
        "plot_query_suffix": _plot_query_suffix(axes["x"], axes["y"], axes["facet"], resolved_fixed),
        "metrics": [
            {"key": metric, "label": direction, **KIND_METADATA[kind],
             "available": metric_available(filtered, metric, axes),
             "default": metric in (DEFAULT_METRIC, DEFAULT_PLACE_METRIC, DEFAULT_LEGACY_PLACE_METRIC)}
            for metric, kind, direction in _metric_specs()
        ],
    }
