"""Renders a job's sweep metrics as PNGs, reusing
scripts/pull_and_plot_holdover_sweep.py's own matplotlib plotting code
directly -- so /jobs/{id}/results looks exactly like that script's own
output (same camera, same viridis surface+scatter style, same fixed
z-scale), not a reimplementation of its look. sweep_results.py builds the
records/axes this reads; this module is the only place in webui/ that pulls
in matplotlib/numpy/pandas, and only pays that cost when a metric's image is
actually requested.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless/server process -- must precede any pyplot import

# The script lives in scripts/, a plain (non-package) directory -- put the
# repo root on sys.path so it importable as a namespace package regardless
# of the process's cwd (uvicorn's cwd when launched isn't guaranteed).
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pandas as pd  # noqa: E402
from scripts.pull_and_plot_holdover_sweep import infer_model_name, plot_metric_surface_facets  # noqa: E402

from . import sweep_results  # noqa: E402


def _records_dataframe(records: list[dict], axes: dict, metric: str) -> pd.DataFrame:
    """Records -> a numeric DataFrame with just the columns
    plot_metric_surface_facets needs, dropping rows missing any of them."""
    rows = []
    for record in records:
        x = sweep_results.numeric_or_none(record.get(axes["x"]))
        y = sweep_results.numeric_or_none(record.get(axes["y"]))
        facet = sweep_results.numeric_or_none(record.get(axes["facet"]))
        value = record.get(metric)
        if None in (x, y, facet, value):
            continue
        rows.append({axes["x"]: x, axes["y"]: y, axes["facet"]: facet, metric: value})
    return pd.DataFrame(rows)


def render_metric_surface_png(records: list[dict], axes: dict, metric: str, experiment_tag: str | None) -> bytes | None:
    """This metric's faceted surface figure as PNG bytes, or None if there's
    nothing plottable (missing axes, or no records with this metric)."""
    if not (axes["x"] and axes["y"] and axes["facet"]):
        return None
    df = _records_dataframe(records, axes, metric)
    if df.empty:
        return None

    model_name = infer_model_name(experiment_tag) if experiment_tag else "unknown"
    buffer = io.BytesIO()
    plot_metric_surface_facets(df, metric, axes["x"], axes["y"], axes["facet"], buffer, model_name)
    return buffer.getvalue()
