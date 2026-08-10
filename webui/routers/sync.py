"""Manual data sync from Quest. Only ever runs when the user clicks 'Sync
now' -- no scheduled/background sync. Just ratinabox -- see config.yaml's
repos: comment for why hannahs-cebras isn't in scope here."""
from __future__ import annotations

from fastapi import APIRouter, Request

from .. import config, db, quest, view

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("")
def sync_page(request: Request):
    runs = db.list_sync_runs(limit=20)
    return view.templates.TemplateResponse("sync.html", {
        "request": request, "runs": runs, "repo_cfg": config.repo_config("ratinabox"),
    })


@router.post("")
def run_sync(request: Request):
    repo_cfg = config.repo_config("ratinabox")
    remote_dir = f"{repo_cfg['remote_path']}/{repo_cfg['results_subdir']}"
    local_dir = f"{repo_cfg['local_path']}/{repo_cfg['results_subdir']}"
    result = quest.rsync_pull(remote_dir, local_dir)
    db.insert_sync_run(repo="ratinabox", remote_path=remote_dir, local_path=local_dir,
                        success=result.ok, output=result.combined_output)
    runs = db.list_sync_runs(limit=20)
    return view.templates.TemplateResponse("sync.html", {
        "request": request, "runs": runs, "repo_cfg": repo_cfg, "last_result": result,
    })
