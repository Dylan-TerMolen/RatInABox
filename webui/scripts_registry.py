"""Discovers runnable scripts across both repos and describes their CLI
parameters, so the UI can render a form instead of you hand-typing a command.

Two introspection strategies:
  - ratinabox/hsw/main.py has one real argparse CLI (args_parser.py). We
    import that module directly (safe -- it only defines functions/constants
    at import time, `parse()` isn't called) and read the parser's actions.
  - hannahs-cebras scripts are one-off files that run top-level code (they
    `cebra.load_data(...)` etc. as soon as they're imported), so importing
    them would actually execute the analysis. Instead we statically parse
    each file's source with `ast` and pull out its `add_argument(...)` calls
    without executing anything.

Either way, if a param's default/choices/type isn't statically resolvable, we
fall back to a plain text field rather than guessing.
"""
from __future__ import annotations

import ast
import importlib
import sys
from dataclasses import dataclass, field
from pathlib import Path

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
    repo: str                 # 'ratinabox' | 'hannahs_cebras'
    display_name: str
    entry_point: str          # path to the .py file, relative to the repo root
    params: list[ParamSpec] = field(default_factory=list)
    introspected: bool = True
    note: str = ""


# ---- ratinabox/hsw/main.py: real argparse introspection -------------------

def _introspect_ratinabox_main() -> ScriptSpec:
    if str(RATINABOX_HSW_DIR) not in sys.path:
        sys.path.insert(0, str(RATINABOX_HSW_DIR))
    args_parser = importlib.import_module("args_parser")
    importlib.reload(args_parser)  # pick up edits without restarting the app

    import argparse
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


# ---- hannahs-cebras scripts: static AST introspection ----------------------

def _literal(node) -> object | None:
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _is_add_argument_call(node: ast.AST) -> bool:
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_argument")


def _param_from_call(node: ast.Call, positional_order: list[int]) -> ParamSpec | None:
    if not node.args:
        return None
    first = _literal(node.args[0])
    if not isinstance(first, str):
        return None  # flag/name built dynamically -- can't introspect statically

    kwargs = {kw.arg: kw.value for kw in node.keywords if kw.arg}
    type_node = kwargs.get("type")
    is_bool = _literal(kwargs.get("action")) in ("store_true", "store_false")
    if is_bool:
        type_name = "bool"
    elif isinstance(type_node, ast.Name):
        type_name = type_node.id if type_node.id in ("int", "float", "str") else "str"
    else:
        type_name = "str"

    choices = _literal(kwargs["choices"]) if "choices" in kwargs else None
    is_positional = not first.startswith("-")
    order = None
    if is_positional:
        order = len(positional_order)
        positional_order.append(order)

    return ParamSpec(
        name=first.lstrip("-").replace("-", "_") if not is_positional else first,
        flag=None if is_positional else first,
        type="choice" if choices else type_name,
        default=_literal(kwargs.get("default")) if "default" in kwargs else None,
        choices=choices,
        help=_literal(kwargs.get("help")) or "",
        required=bool(_literal(kwargs.get("required"))) or is_positional,
        positional_order=order,
    )


def _introspect_script_file(py_file: Path, repo_root: Path) -> ScriptSpec:
    source = py_file.read_text()
    tree = ast.parse(source, filename=str(py_file))
    positional_order: list[int] = []
    params = [p for node in ast.walk(tree) if _is_add_argument_call(node)
              for p in [_param_from_call(node, positional_order)] if p]
    rel = py_file.relative_to(repo_root)
    return ScriptSpec(
        id=f"hannahs_cebras:{rel}",
        repo="hannahs_cebras",
        display_name=str(rel),
        entry_point=str(rel),
        params=params,
        introspected=bool(params),
        note="" if params else "No argparse arguments found by static scan -- use raw args below.",
    )


def _discover_hannahs_cebras_scripts() -> list[ScriptSpec]:
    repo_cfg = config.repo_config("hannahs_cebras")
    local_path = repo_cfg.get("local_path")
    if config.is_stubbed(local_path):
        return []  # config.yaml not filled in yet
    repo_root = Path(local_path)
    if not repo_root.is_dir():
        return []
    candidates = list(repo_root.glob("*.py")) + list((repo_root / "scripts").glob("*.py"))
    specs = []
    for f in sorted(candidates):
        if f.name.startswith("_"):
            continue
        try:
            specs.append(_introspect_script_file(f, repo_root))
        except (SyntaxError, ValueError):
            continue
    return specs


# ---- public API -------------------------------------------------------------

def list_scripts() -> list[ScriptSpec]:
    scripts = []
    try:
        scripts.append(_introspect_ratinabox_main())
    except Exception as e:  # don't let one repo's import error blank the whole page
        scripts.append(ScriptSpec(
            id="ratinabox:hsw_main", repo="ratinabox",
            display_name="hsw/main.py (introspection failed)",
            entry_point="ratinabox/hsw/main.py", params=[], introspected=False,
            note=f"Could not introspect args_parser.py: {e}",
        ))
    scripts.extend(_discover_hannahs_cebras_scripts())
    return scripts


def get_script(script_id: str) -> ScriptSpec | None:
    for s in list_scripts():
        if s.id == script_id:
            return s
    return None
