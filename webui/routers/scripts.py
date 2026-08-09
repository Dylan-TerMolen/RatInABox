from __future__ import annotations

import json
import re

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from .. import config, scripts_registry, slurm_templates, view

router = APIRouter(prefix="/scripts", tags=["scripts"])


@router.get("")
def list_scripts(request: Request):
    scripts = scripts_registry.list_scripts()
    by_repo: dict[str, list] = {}
    for s in scripts:
        by_repo.setdefault(s.repo, []).append(s)
    return view.templates.TemplateResponse("scripts_list.html", {
        "request": request, "by_repo": by_repo,
    })


@router.get("/{script_id:path}")
def script_form(request: Request, script_id: str):
    spec = scripts_registry.get_script(script_id)
    if spec is None:
        return RedirectResponse("/scripts", status_code=303)
    defaults = config.slurm_defaults()
    default_job_name = re.sub(r"[^a-zA-Z0-9_]+", "_", spec.display_name).strip("_")[:40]

    visible = config.script_form_visible_params(spec.id)
    if visible is None:
        primary_params, other_params = spec.params, []
    else:
        visible_set = set(visible)
        # Required params with no default always show -- the command can't
        # be built without them, regardless of what's configured as "visible".
        primary_params = [p for p in spec.params if p.name in visible_set or p.required]
        other_params = [p for p in spec.params if p not in primary_params]

    return view.templates.TemplateResponse("script_form.html", {
        "request": request, "spec": spec, "defaults": defaults,
        "default_job_name": default_job_name,
        "primary_params": primary_params, "other_params": other_params,
    })


@router.post("/{script_id:path}/preview")
async def preview(request: Request, script_id: str):
    spec = scripts_registry.get_script(script_id)
    if spec is None:
        return RedirectResponse("/scripts", status_code=303)

    form = await request.form()

    fixed_args: list[tuple[str, str | None, str | None]] = []
    grid_params: dict[str, list[str]] = {}
    bool_flags: list[str] = []
    params_for_record: dict[str, str] = {}

    positional = sorted((p for p in spec.params if p.flag is None),
                         key=lambda p: p.positional_order or 0)
    flagged = [p for p in spec.params if p.flag is not None]

    for p in positional + flagged:
        raw_value = form.get(f"value__{p.name}", "").strip()
        is_grid = form.get(f"grid__{p.name}") == "on"
        if p.type == "bool":
            if raw_value == "on":
                bool_flags.append(p.flag)
                params_for_record[p.name] = "true"
            continue
        if not raw_value:
            if p.required:
                fixed_args.append((p.name, p.flag, str(p.default) if p.default is not None else ""))
            continue
        params_for_record[p.name] = raw_value
        if is_grid and "," in raw_value:
            grid_params[p.name] = [v.strip() for v in raw_value.split(",") if v.strip()]
            fixed_args.append((p.name, p.flag, None))
        else:
            fixed_args.append((p.name, p.flag, raw_value))

    job_name = form.get("job_name", "job").strip() or "job"
    job_name = re.sub(r"[^a-zA-Z0-9_\-]+", "_", job_name)
    slurm_opts = {
        "account": form.get("account", ""), "partition": form.get("partition", ""),
        "gres": form.get("gres", ""), "nodes": form.get("nodes", "1"),
        "ntasks": form.get("ntasks", "1"), "mem": form.get("mem", ""),
        "time": form.get("time", ""), "mail_type": form.get("mail_type", ""),
        "mail_user": form.get("mail_user", ""),
    }
    conda_env = form.get("conda_env", "ratinabox")

    script_text, n = slurm_templates.render_slurm_script(
        job_name=job_name, repo=spec.repo, entry_point=spec.entry_point,
        slurm_opts=slurm_opts, conda_env=conda_env, fixed_args=fixed_args,
        grid_params=grid_params, bool_flags=bool_flags,
    )

    preview_tokens = []
    for name, f, v in fixed_args:
        if name in grid_params:
            v = "[" + ",".join(grid_params[name]) + "]"
        preview_tokens.append(f"{f or ''} {v or ''}".strip())
    command_preview = " ".join(preview_tokens)

    return view.templates.TemplateResponse("script_preview.html", {
        "request": request, "spec": spec, "script_text": script_text,
        "array_count": n, "job_name": job_name, "command_preview": command_preview,
        "repo": spec.repo, "script_id": spec.id, "script_display_name": spec.display_name,
        "params_json_str": json.dumps(params_for_record), "grid_json_str": json.dumps(grid_params),
    })
