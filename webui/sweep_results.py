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

from . import db, hsw_log

DECODER_KINDS = ("place", "task")
# Flattened decoding-score columns in a fixed order, so the metric toggle
# list on the page is stable across jobs/models.
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
        for kind, scores in (("place", iteration.place), ("task", iteration.task)):
            for key, value in scores.items():
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


def infer_axes(records: list[dict]) -> dict[str, str | None]:
    """Best-effort facet/x/y param assignment: pattern-match against current
    flag naming first, then fall back to whatever candidates are left."""
    candidates = varying_numeric_params(records)
    assigned: dict[str, str | None] = {}
    for role, patterns in AXIS_PATTERNS.items():
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


def build_results_view(job_id: int) -> dict:
    """Everything the results template needs: which metrics have data to
    plot and the inferred facet/x/y axes. Actual PNG rendering is deferred
    to sweep_plots.py, called on demand per metric (see routers/jobs.py)."""
    records = job_sweep_records(job_id)
    axes = infer_axes(records)
    return {
        "records_count": len(records),
        "axes": axes,
        "metrics": [
            {"key": metric, "label": metric.replace("_", " "),
             "available": metric_available(records, metric, axes), "default": metric == DEFAULT_METRIC}
            for metric in METRIC_KEYS
        ],
    }
