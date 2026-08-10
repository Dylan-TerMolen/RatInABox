"""Entrypoint. Run with:

    cd RatInABox
    conda activate ratinabox   # or whatever env has the webui/requirements.txt extras
    pip install -r webui/requirements.txt
    uvicorn webui.app:app --reload --port 8420

Then open http://127.0.0.1:8420
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import config, db
from .routers import scripts, jobs, status, sync, results

WEBUI_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Quest Job Runner")
app.mount("/static", StaticFiles(directory=str(WEBUI_DIR / "static")), name="static")

templates = Jinja2Templates(directory=str(WEBUI_DIR / "templates"))
# Routers import this same `templates` instance via a small accessor module
# to avoid circular imports -- see webui/view.py
from . import view  # noqa: E402
view.templates = templates

app.include_router(scripts.router)
app.include_router(jobs.router)
app.include_router(status.router)
app.include_router(sync.router)
app.include_router(results.router)


@app.on_event("startup")
def _startup():
    db.init_db()


@app.get("/")
def index(request: Request):
    cfg = config.load_config()
    stub_warnings = []
    for field in ("host", "username", "identity_file"):
        if config.is_stubbed(cfg["quest"].get(field)):
            stub_warnings.append(f"quest.{field} is still a CHANGE_ME placeholder in webui/config.yaml")
    for repo_key in ("ratinabox", "hannahs_cebras"):
        repo_cfg = cfg["repos"][repo_key]
        if config.is_stubbed(repo_cfg.get("local_path")) or config.is_stubbed(repo_cfg.get("remote_path")):
            stub_warnings.append(f"repos.{repo_key} paths are still CHANGE_ME placeholders in webui/config.yaml")
    recent_jobs = db.list_jobs()[:10]
    return view.templates.TemplateResponse("index.html", {
        "request": request, "stub_warnings": stub_warnings, "recent_jobs": recent_jobs,
    })


@app.get("/favicon.ico")
def favicon():
    return RedirectResponse("/static/favicon.svg")
