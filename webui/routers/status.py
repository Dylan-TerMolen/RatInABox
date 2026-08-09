"""Job status. Deliberately has no polling loop, no background thread, no
auto-refresh -- squeue/sacct are only ever queried when the user clicks
'Refresh status' on a job's page, per the 'minimize refreshes' requirement.
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from .. import config, db, quest, view

router = APIRouter(prefix="/jobs", tags=["status"])


@router.post("/{job_id}/refresh")
def refresh_status(job_id: int):
    job = db.get_job(job_id)
    if job is None or not job["sbatch_job_id"]:
        return RedirectResponse(f"/jobs/{job_id}", status_code=303)

    sbatch_id = job["sbatch_job_id"]
    live_rows = quest.squeue_status(sbatch_id)
    hist_rows = quest.sacct_status(sbatch_id)

    # squeue wins for anything still in the live queue; sacct fills in the
    # rest (finished/failed tasks squeue no longer reports).
    by_task = {r["job_id"]: r for r in hist_rows}
    by_task.update({r["job_id"]: r for r in live_rows})
    tasks = sorted(by_task.values(), key=lambda r: r["job_id"])

    total = job["array_count"] or 1
    done = sum(1 for t in tasks if t.get("state", "").upper() in ("COMPLETED",))
    failed = sum(1 for t in tasks if "FAIL" in t.get("state", "").upper()
                 or t.get("state", "").upper() in ("CANCELLED", "TIMEOUT", "OUT_OF_MEMORY"))
    running = sum(1 for t in tasks if t.get("state", "").upper() == "RUNNING")
    pending = sum(1 for t in tasks if t.get("state", "").upper() == "PENDING")

    summary = {
        "tasks": tasks, "total_array_tasks": total,
        "done": done, "failed": failed, "running": running, "pending": pending,
        "queried_ok": bool(live_rows or hist_rows),
    }
    db.update_status_cache(job_id, summary)
    return RedirectResponse(f"/jobs/{job_id}", status_code=303)


@router.get("/{job_id}/peek-log")
def peek_log(request: Request, job_id: int, task: int = 0):
    """One-shot snapshot of a job's log (last 50 lines) -- not a live stream,
    just `tail` run once, on demand."""
    job = db.get_job(job_id)
    if job is None or not job["sbatch_job_id"]:
        return RedirectResponse(f"/jobs/{job_id}", status_code=303)
    repo_cfg = config.repo_config(job["repo"])
    log_path = f"{repo_cfg['remote_path']}/webui_out/{job['job_name']}.{job['sbatch_job_id']}_{task}.out"
    result = quest.peek_log(log_path)
    return view.templates.TemplateResponse("log_peek.html", {
        "request": request, "job": job, "task": task, "log_path": log_path, "result": result,
    })
