"""Browse and plot CSVs that have landed locally via the Sync page. Reads
whatever's on disk right now -- there's no live/streaming update here either,
you sync first, then look."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from .. import config, view

router = APIRouter(prefix="/results", tags=["results"])


def _allowed_roots() -> dict[str, Path]:
    roots = {}
    for key in ("ratinabox", "hannahs_cebras"):
        repo_cfg = config.repo_config(key)
        if config.is_stubbed(repo_cfg.get("local_path")):
            continue
        root = Path(repo_cfg["local_path"]) / repo_cfg["results_subdir"]
        if root.is_dir():
            roots[key] = root
    return roots


def _resolve_safe(path_str: str) -> Path | None:
    """Only allow paths inside one of the configured local results dirs."""
    target = Path(path_str).resolve()
    for root in _allowed_roots().values():
        try:
            target.relative_to(root.resolve())
            return target
        except ValueError:
            continue
    return None


@router.get("")
def list_results(request: Request):
    roots = _allowed_roots()
    by_repo = {}
    for repo, root in roots.items():
        csvs = sorted(root.rglob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
        by_repo[repo] = [{"path": str(p), "name": str(p.relative_to(root)),
                           "mtime": p.stat().st_mtime, "size": p.stat().st_size}
                          for p in csvs[:200]]
    unstubbed = list(roots.keys())
    return view.templates.TemplateResponse("results_list.html", {
        "request": request, "by_repo": by_repo, "unstubbed": unstubbed,
    })


@router.get("/view")
def view_csv(request: Request, path: str, x: str | None = None, y: str | None = None):
    safe_path = _resolve_safe(path)
    if safe_path is None or not safe_path.is_file():
        return RedirectResponse("/results", status_code=303)

    try:
        df = pd.read_csv(safe_path)
    except Exception as e:
        return view.templates.TemplateResponse("results_view.html", {
            "request": request, "path": path, "error": str(e), "columns": [],
        })

    columns = list(df.columns)
    plot_data = None
    error = None
    if x and y and x in columns and y in columns:
        sub = df[[x, y]].apply(pd.to_numeric, errors="coerce").dropna()
        if sub.empty:
            error = f"Columns '{x}' and '{y}' have no overlapping numeric rows."
        else:
            plot_data = {"x": sub[x].tolist(), "y": sub[y].tolist(), "x_label": x, "y_label": y}

    return view.templates.TemplateResponse("results_view.html", {
        "request": request, "path": path, "columns": columns, "row_count": len(df),
        "x": x, "y": y, "plot_data_json": json.dumps(plot_data) if plot_data else None,
        "error": error,
    })
