"""Browse and plot the .log files main.py writes (see webui/hsw_log.py for
the format) once they've landed locally via the Sync page. Reads whatever's
on disk right now -- there's no live/streaming update here either, you sync
first, then look.

Not the .csv files also occasionally written next to them -- those are raw
per-iteration spike/firing-rate dumps gated behind ENVIRONMENT=='Home'
(simulation_helpers.save_simulation_data) and aren't the actual results."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from .. import config, db, hsw_log, view

router = APIRouter(prefix="/results", tags=["results"])


def _results_root() -> Path | None:
    repo_cfg = config.repo_config("ratinabox")
    if config.is_stubbed(repo_cfg.get("local_path")):
        return None
    root = Path(repo_cfg["local_path"]) / repo_cfg["results_subdir"]
    return root if root.is_dir() else None


def _resolve_safe(path_str: str) -> Path | None:
    """Only allow paths inside the configured local results dir."""
    root = _results_root()
    if root is None:
        return None
    target = Path(path_str).resolve()
    try:
        target.relative_to(root.resolve())
        return target
    except ValueError:
        return None


def logs_for_experiment(experiment_tag: str) -> list[dict]:
    """.log files whose name carries this experiment tag as its prefix
    (matches main.py's f"{experiment}-{date}:..." naming). Used by the job
    detail page to show a job's own results without the user having to dig
    through the full results list."""
    root = _results_root()
    if root is None or not experiment_tag:
        return []
    prefix = f"{experiment_tag}-"
    matches = [p for p in root.rglob("*.log") if p.name.startswith(prefix)]
    matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [{"path": str(p), "name": str(p.relative_to(root)), "mtime": p.stat().st_mtime}
            for p in matches]


def _matching_job(filename: str, jobs_with_tags: list) -> int | None:
    for job in jobs_with_tags:
        if job["experiment_tag"] and filename.startswith(f"{job['experiment_tag']}-"):
            return job["id"]
    return None


def _values_close(iteration_value: str, log_value_repr: str) -> bool:
    """log_value_repr is however write_run_header stringified vars(args) --
    a bare scalar ('0.4') or a Python list repr ('[0.6]', since holdovers/
    percent_* are list-parsed by args_parser._set_defaults). Strip brackets
    and compare loosely (string or float equality) against each element."""
    for part in log_value_repr.strip("[]").split(","):
        part = part.strip().strip("'\"")
        if part == iteration_value:
            return True
        try:
            if float(part) == float(iteration_value):
                return True
        except ValueError:
            continue
    return False


def _iteration_matches_log(iteration_params: dict, log_run_params: dict) -> bool:
    if not iteration_params:
        return False  # nothing distinguishing to match on (non-swept iteration)
    return all(
        key in log_run_params and _values_close(value, log_run_params[key])
        for key, value in iteration_params.items()
    )


def match_unmatched_iterations() -> int:
    """Try to pair up any job_iterations without a log yet against .log
    files matching their job's experiment tag -- by comparing against each
    candidate's *parsed Run-parameters header*, not its filename. Some swept
    params (holdovers) aren't part of the filename at all, but main.py's
    write_run_header() dumps every arg, so the header is the reliable source
    of truth. Called after a successful sync, not on any timer. Returns how
    many iterations got matched this pass."""
    root = _results_root()
    if root is None:
        return 0
    jobs_by_id = {j["id"]: j for j in db.list_jobs()}

    by_job: dict[int, list] = {}
    for it in db.list_unmatched_iterations():
        by_job.setdefault(it["job_id"], []).append(it)

    matched = 0
    for job_id, its in by_job.items():
        job = jobs_by_id.get(job_id)
        if not job or not job["experiment_tag"]:
            continue
        candidates = logs_for_experiment(job["experiment_tag"])
        if not candidates:
            continue
        parsed_candidates = [(c["path"], hsw_log.parse(Path(c["path"]).read_text())) for c in candidates]
        for it in its:
            it_params = json.loads(it["params_json"])
            for path, parsed in parsed_candidates:
                if _iteration_matches_log(it_params, parsed.run_params):
                    db.set_iteration_log_path(it["id"], path)
                    matched += 1
                    break
    return matched


@router.get("")
def list_results(request: Request):
    root = _results_root()
    logs = []
    if root is not None:
        jobs_with_tags = [j for j in db.list_jobs() if j["experiment_tag"]]
        found = sorted(root.rglob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        logs = [{"path": str(p), "name": str(p.relative_to(root)),
                 "mtime": p.stat().st_mtime, "size": p.stat().st_size,
                 "job_id": _matching_job(p.name, jobs_with_tags)}
                for p in found[:200]]
    return view.templates.TemplateResponse("results_list.html", {
        "request": request, "logs": logs, "have_root": root is not None,
    })


@router.get("/view")
def view_log(request: Request, path: str, metric: str | None = None):
    safe_path = _resolve_safe(path)
    if safe_path is None or not safe_path.is_file():
        return RedirectResponse("/results", status_code=303)

    parsed = hsw_log.parse(safe_path.read_text())

    metric_options = [f"{decoder}:{key}" for decoder in ("place", "task") for key in hsw_log.SCORE_KEYS]
    plot_data = None
    error = None
    if metric and parsed.iterations:
        decoder, _, key = metric.partition(":")
        xs, ys = [], []
        for i, it in enumerate(parsed.iterations):
            scores = it.place if decoder == "place" else it.task
            value = scores.get(key)
            if value is not None:
                xs.append(i)
                ys.append(value)
        if not xs:
            error = f"No numeric '{metric}' scores in this log (all n/a)."
        else:
            plot_data = {"x": xs, "y": ys, "x_label": "iteration", "y_label": metric}

    return view.templates.TemplateResponse("results_view.html", {
        "request": request, "path": path, "parsed": parsed,
        "metric_options": metric_options, "metric": metric,
        "plot_data_json": json.dumps(plot_data) if plot_data else None,
        "error": error,
    })
