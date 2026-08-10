"""Discovers runnable scripts and describes their CLI parameters, so the UI
can render a form instead of you hand-typing a command.

Just ratinabox/hsw/main.py for now -- hannahs-cebras is a decoding utility
library that hsw/main.py imports (installed as the `hannahs_cebras` pip
package on Quest), not something this app submits jobs to.

args_parser.py is imported directly (safe -- it only defines
functions/constants at import time, `parse()` isn't called) and we read the
parser's actions. If a param's default/choices/type isn't resolvable that
way, we fall back to a plain text field rather than guessing.
"""
from __future__ import annotations

import argparse
import importlib
import sys
from dataclasses import dataclass, field

from . import config

RATINABOX_HSW_DIR = config.REPO_ROOT / "ratinabox" / "hsw"


@dataclass
class ParamSpec:
    name: str
    flag: str | None          # None => positional argument
    type: str                 # 'str' | 'int' | 'float' | 'bool' | 'choice'
    default: object = None
    choices: list | None = None
    help: str = ""
    required: bool = False
    positional_order: int | None = None


@dataclass
class ScriptSpec:
    id: str                   # stable key, e.g. "ratinabox:hsw_main"
    repo: str                 # 'ratinabox'
    display_name: str
    entry_point: str          # path to the .py file, relative to the repo root
    params: list[ParamSpec] = field(default_factory=list)
    introspected: bool = True
    note: str = ""


def _introspect_ratinabox_main() -> ScriptSpec:
    if str(RATINABOX_HSW_DIR) not in sys.path:
        sys.path.insert(0, str(RATINABOX_HSW_DIR))
    args_parser = importlib.import_module("args_parser")
    importlib.reload(args_parser)  # pick up edits without restarting the app

    parser = argparse.ArgumentParser()
    args_parser._add_arguments(parser)

    params = []
    for action in parser._actions:
        if action.dest == "help":
            continue
        is_bool = isinstance(action, (argparse._StoreTrueAction, argparse._StoreFalseAction))
        type_name = "bool" if is_bool else (getattr(action.type, "__name__", None) or "str")
        params.append(ParamSpec(
            name=action.dest,
            flag=action.option_strings[0] if action.option_strings else None,
            type="choice" if action.choices else type_name,
            default=action.default,
            choices=list(action.choices) if action.choices else None,
            help=action.help or "",
            required=bool(action.required),
        ))
    return ScriptSpec(
        id="ratinabox:hsw_main",
        repo="ratinabox",
        display_name="hsw/main.py -- HSW place/tEBC decoding simulation",
        entry_point="ratinabox/hsw/main.py",
        params=params,
        introspected=True,
        note="Params introspected live from ratinabox/hsw/args_parser.py.",
    )


def list_scripts() -> list[ScriptSpec]:
    try:
        return [_introspect_ratinabox_main()]
    except Exception as e:  # don't let an import error blank the whole page
        return [ScriptSpec(
            id="ratinabox:hsw_main", repo="ratinabox",
            display_name="hsw/main.py (introspection failed)",
            entry_point="ratinabox/hsw/main.py", params=[], introspected=False,
            note=f"Could not introspect args_parser.py: {e}",
        )]


def get_script(script_id: str) -> ScriptSpec | None:
    for s in list_scripts():
        if s.id == script_id:
            return s
    return None
