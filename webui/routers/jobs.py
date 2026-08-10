from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Form, Request, UploadFile, File
from fastapi.responses import RedirectResponse

from .. import config, db, quest, view
from . import results

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
def list_jobs(request: Request):
    jobs = db.list_jobs()
    return view.templates.TemplateResponse("jobs_list.html", {"request": request, "jobs": jobs})


@router.get("/new-raw")
def new_raw_form(request: Request):
    return view.templates.TemplateResponse("job_new_raw.html", {"request": request})


_EXPERIMENT_VAR_RE = re.compile(r'^\s*EXPERIMENT\s*=\s*"?([^\s"]+)"?', re.MULTILINE)
_EXPERIMENT_FLAG_RE = re.compile(r'--experiment[\s=]+"?([^\s"$][^\s"]*)"?')


def _extract_experiment_tag(script_text: str) -> str | None:
    """Best-effort: pull the experiment tag out of an uploaded .sh so jobs
    submitted by hand (not through the generator) still link to their .log
    results here. Tries an `EXPERIMENT=...` bash var first (the convention
    in hand-written sweep scripts), then a literal `--experiment <value>`
    flag. Doesn't try to resolve `--experiment "${EXPERIMENT}"` beyond that
    -- if neither pattern matches, leave it blank and let the user fill in
    the tag on the job detail page instead."""
    m = _EXPERIMENT_VAR_RE.search(script_text)
    if m:
        return m.group(1)
    m = _EXPERIMENT_FLAG_RE.search(script_text)
    if m:
        return m.group(1)
    return None


@router.post("/new-raw")
async def create_raw_job(request: Request, job_name: str = Form(...),
                          sh_file: UploadFile = File(...),
                          sbatch_job_id: str = Form("")):
    job_name = re.sub(r"[^a-zA-Z0-9_\-]+", "_", job_name.strip()) or "uploaded_job"
    gen_dir = config.generated_scripts_dir()
    gen_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    local_path = gen_dir / f"{job_name}_{stamp}.sh"
    contents = await sh_file.read()
    local_path.write_bytes(contents)
    script_text = contents.decode(errors="replace")

    job_id = db.insert_job(
        repo="ratinabox", script_id="raw-upload", script_display_name=sh_file.filename or "uploaded.sh",
        command="(uploaded .sh script, not generated)", params={}, grid=None, array_count=1,
        job_name=job_name, slurm_script_local_path=str(local_path),
        experiment_tag=_extract_experiment_tag(script_text),
    )
    sbatch_job_id = sbatch_job_id.strip()
    if sbatch_job_id:
        # Already submitted outside this app (e.g. run by hand before this
        # tool existed) -- record the known id directly, no actual sbatch
        # call, so status refresh/peek-log work immediately.
        db.mark_queued(job_id, sbatch_job_id)
    return RedirectResponse(f"/jobs/{job_id}", status_code=303)


@router.post("/create-from-preview")
async def create_from_preview(request: Request):
    form = await request.form()
    repo = form["repo"]
    script_id = form["script_id"]
    script_display_name = form["script_display_name"]
    job_name = form["job_name"]
    script_text = form["script_text"]
    array_count = int(form.get("array_count", "1"))
    params = json.loads(form.get("params_json", "{}"))
    grid = json.loads(form.get("grid_json", "{}")) or None
    command_preview = form.get("command_preview", "")
    experiment_tag = form.get("experiment_tag", "").strip() or None

    gen_dir = config.generated_scripts_dir()
    gen_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    local_path = gen_dir / f"{job_name}_{stamp}.sh"
    local_path.write_text(script_text)

    job_id = db.insert_job(
        repo=repo, script_id=script_id, script_display_name=script_display_name,
        command=command_preview, params=params, grid=grid, array_count=array_count,
        job_name=job_name, slurm_script_local_path=str(local_path),
        experiment_tag=experiment_tag,
    )
    return RedirectResponse(f"/jobs/{job_id}", status_code=303)


@router.get("/{job_id}")
def job_detail(request: Request, job_id: int):
    job = db.get_job(job_id)
    if job is None:
        return RedirectResponse("/jobs", status_code=303)
    script_text = ""
    p = job["slurm_script_local_path"]
    if p and Path(p).is_file():
        script_text = Path(p).read_text()
    last_status = json.loads(job["last_status_json"]) if job["last_status_json"] else None
    flash = None
    if "upload_ok" in request.query_params:
        flash = "Upload succeeded." if request.query_params["upload_ok"] == "1" else "Upload failed -- check the SSH alias in config.yaml."
    elif "queue_ok" in request.query_params:
        flash = "Job queued." if request.query_params["queue_ok"] == "1" else "sbatch failed -- see job for details."
    result_logs = results.logs_for_experiment(job["experiment_tag"]) if job["experiment_tag"] else []
    return view.templates.TemplateResponse("job_detail.html", {
        "request": request, "job": job, "script_text": script_text, "last_status": last_status,
        "flash": flash, "result_logs": result_logs,
    })


@router.post("/{job_id}/upload")
def upload_job(job_id: int):
    job = db.get_job(job_id)
    if job is None:
        return RedirectResponse("/jobs", status_code=303)
    repo_cfg = config.repo_config(job["repo"])
    remote_dir = f"{repo_cfg['remote_path']}/webui_slurm"
    remote_path = f"{remote_dir}/{Path(job['slurm_script_local_path']).name}"

    result = quest.write_remote_file(job["slurm_script_local_path"], remote_path)
    if not result.ok:
        # Most likely cause the first time: remote_dir doesn't exist yet.
        # Create it once and retry -- every upload after this one is a
        # single ssh call (the write above succeeds directly).
        if quest.ensure_remote_dir(remote_dir).ok:
            result = quest.write_remote_file(job["slurm_script_local_path"], remote_path)

    if result.ok:
        db.mark_uploaded(job_id, remote_path)
    return RedirectResponse(f"/jobs/{job_id}?upload_ok={int(result.ok)}", status_code=303)


@router.post("/{job_id}/attach-sbatch-id")
def attach_sbatch_id(job_id: int, sbatch_job_id: str = Form(...)):
    """Record a sbatch job id for a job that was submitted outside this app
    (or before this app existed) -- no actual sbatch call, just wires up
    status refresh/peek-log for a job we didn't submit ourselves."""
    sbatch_job_id = sbatch_job_id.strip()
    if db.get_job(job_id) is not None and sbatch_job_id:
        db.mark_queued(job_id, sbatch_job_id)
    return RedirectResponse(f"/jobs/{job_id}", status_code=303)


@router.post("/{job_id}/queue")
def queue_job(job_id: int):
    job = db.get_job(job_id)
    if job is None or not job["slurm_script_remote_path"]:
        return RedirectResponse(f"/jobs/{job_id}", status_code=303)
    result, sbatch_id = quest.submit_job(job["slurm_script_remote_path"])
    if result.ok and sbatch_id:
        db.mark_queued(job_id, sbatch_id)
    return RedirectResponse(f"/jobs/{job_id}?queue_ok={int(result.ok)}", status_code=303)
