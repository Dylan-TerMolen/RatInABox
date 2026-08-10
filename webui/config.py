"""Loads webui/config.yaml once and exposes it as plain dicts/paths.

Everything here is read-only at runtime -- editing config.yaml and restarting
the app is the intended workflow, there's no in-app settings editor (yet).
"""
from __future__ import annotations

import functools
from pathlib import Path

import yaml

WEBUI_DIR = Path(__file__).resolve().parent
REPO_ROOT = WEBUI_DIR.parent
CONFIG_PATH = WEBUI_DIR / "config.yaml"


@functools.lru_cache(maxsize=1)
def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def quest_host() -> str:
    return load_config()["quest"]["host"]


def quest_username() -> str:
    return load_config()["quest"]["username"]


def quest_identity_file() -> str:
    return str(Path(load_config()["quest"]["identity_file"]).expanduser())


def quest_target() -> str:
    """<username>@<host>, as passed straight to ssh/rsync's -e ssh."""
    return f"{quest_username()}@{quest_host()}"


def repo_config(repo_key: str) -> dict:
    try:
        return load_config()["repos"][repo_key]
    except KeyError:
        raise KeyError(f"No repo '{repo_key}' in config.yaml under 'repos:'")


def slurm_defaults() -> dict:
    return dict(load_config()["slurm_defaults"])


def script_form_visible_params(script_id: str) -> list[str] | None:
    """List of param names to render as inputs for this script, or None if
    the script has no entry under script_forms: (meaning "show everything",
    the original unscoped behavior)."""
    entry = load_config().get("script_forms", {}).get(script_id)
    return entry["visible_params"] if entry else None


def _resolve_app_path(key: str) -> Path:
    raw = load_config()["app"][key]
    p = Path(raw)
    return p if p.is_absolute() else (REPO_ROOT / p)


def db_path() -> Path:
    return _resolve_app_path("db_path")


def generated_scripts_dir() -> Path:
    return _resolve_app_path("generated_scripts_dir")


def uploads_dir() -> Path:
    return _resolve_app_path("uploads_dir")


def is_stubbed(value: str | None) -> bool:
    """True if a config value still looks like an unedited CHANGE_ME placeholder."""
    return value is None or "CHANGE_ME" in value
