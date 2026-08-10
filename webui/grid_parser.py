"""Reverse-engineers a SLURM script's grid sweep -- which CLI flags are
swept, over what values, in what row-major order -- straight from its bash
text. Works for scripts this app generates (slurm_templates.py's
AXIS_<NAME>_VALUES convention) *and* hand-written ones that don't share that
naming (e.g. HOLDOVERS_VALUES=(...) resolved into a differently-named
$HOLDOVER), because it doesn't rely on any naming convention -- it follows
the actual reference chain instead:

    --holdovers "${HOLDOVER}"          <- flag uses this bash var
    HOLDOVER=${HOLDOVERS_VALUES[$IDX]} <- that var is indexed from this array
    HOLDOVERS_VALUES=(0.3 0.4 ...)     <- that array is declared with these values

Axis order (which one is fastest-varying) is the array declaration order,
which is also the order both this app's render_grid_mapping() and the
hand-written scripts it mirrors chain their `IDX % N; IDX /= N` decode in.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_ARRAY_DECL_RE = re.compile(r"^(\w+)_VALUES=\(([^)]*)\)", re.MULTILINE)
_ASSIGN_FROM_ARRAY_RE = re.compile(r"\b(\w+)=\$\{(\w+)_VALUES\[")
_FLAG_VAR_RE = re.compile(r'--([a-zA-Z_][\w-]*)[\s=]+"?\$\{(\w+)\}"?')
# Any --flag token + whatever comes after it, var-reference or bare literal.
_FLAG_VALUE_RE = re.compile(r'--([a-zA-Z_][\w-]*)[\s=]+"?(\$\{\w+\}|[^\s"]+)"?')
_VAR_REF_RE = re.compile(r"^\$\{(\w+)\}$")


def _strip_comment_lines(script_text: str) -> str:
    """Drop full-comment lines (SBATCH directives, shebang, actual comments)
    before scanning for --flag tokens -- #SBATCH --account=... etc. would
    otherwise be misread as CLI args."""
    return "\n".join(line for line in script_text.splitlines() if not line.lstrip().startswith("#"))


@dataclass
class GridAxis:
    flag_name: str       # CLI flag this axis controls, e.g. 'holdovers'
    values: list[str]    # in declaration order


def parse_grid_axes(script_text: str) -> list[GridAxis]:
    script_text = _strip_comment_lines(script_text)
    arrays = dict(_ARRAY_DECL_RE.findall(script_text))          # array_name -> raw values str
    scalar_to_array = dict(_ASSIGN_FROM_ARRAY_RE.findall(script_text))  # scalar_var -> array_name
    flag_to_scalar = dict(_FLAG_VAR_RE.findall(script_text))    # flag -> scalar_var
    array_to_scalar = {array: scalar for scalar, array in scalar_to_array.items()}
    scalar_to_flag = {scalar: flag for flag, scalar in flag_to_scalar.items()}

    axes = []
    for array_name, raw_values in arrays.items():  # dict preserves declaration order
        values = raw_values.split()
        scalar_var = array_to_scalar.get(array_name)
        flag = scalar_to_flag.get(scalar_var) if scalar_var else None
        if flag and values:
            axes.append(GridAxis(flag_name=flag, values=values))
    return axes


def _resolve_plain_scalar(script_text: str, var_name: str) -> str | None:
    """Value of a plain (non-array-indexed) `VAR=value` assignment, quotes
    stripped. None if there's no such assignment, or it's actually the
    array-indexed form (that's a swept axis, handled separately)."""
    m = re.search(rf"^{re.escape(var_name)}=([^\n]+)$", script_text, re.MULTILINE)
    if not m:
        return None
    value = m.group(1).strip()
    if re.match(r"^\$\{\w+_VALUES\[", value):
        return None  # array-indexed -- a swept axis, not a fixed scalar
    return value.strip("\"'")


def parse_fixed_params(script_text: str, swept_flags: set[str]) -> dict[str, str]:
    """Every --flag passed to the command that *isn't* one of the swept
    axes: resolves `--flag "${VAR}"` back to VAR's plain assignment, or
    takes a bare `--flag value` literally. Skips a flag whose value can't be
    resolved (e.g. references something built dynamically) rather than
    guessing."""
    script_text = _strip_comment_lines(script_text)
    fixed = {}
    for flag, raw_value in _FLAG_VALUE_RE.findall(script_text):
        if flag in swept_flags or flag in fixed:
            continue
        var_ref = _VAR_REF_RE.match(raw_value)
        if var_ref:
            resolved = _resolve_plain_scalar(script_text, var_ref.group(1))
            if resolved is not None:
                fixed[flag] = resolved
        else:
            fixed[flag] = raw_value
    return fixed


def build_iteration_combos(script_text: str) -> list[dict[str, str]]:
    """The full per-array-task param set -- swept axis values *and* every
    fixed param the command was actually called with (e.g.
    percent_place_cells when it's pinned rather than swept) -- so each
    iteration's params reflect the complete resolved command, not just
    what varies."""
    axes = parse_grid_axes(script_text)
    fixed = parse_fixed_params(script_text, swept_flags={a.flag_name for a in axes})
    return [{**fixed, **combo} for combo in expand_combinations(axes)]


def expand_combinations(axes: list[GridAxis]) -> list[dict[str, str]]:
    """One combo dict per array task index (0..N-1), row-major: the first
    axis is fastest-varying (IDX % N, then IDX //= N), matching the bash
    decode chain. A non-swept script (no axes) yields a single empty combo,
    so every job has at least one iteration."""
    if not axes:
        return [{}]
    combos = []
    total = 1
    for axis in axes:
        total *= len(axis.values)
    for task_idx in range(total):
        idx = task_idx
        combo = {}
        for axis in axes:
            n = len(axis.values)
            combo[axis.flag_name] = axis.values[idx % n]
            idx //= n
        combos.append(combo)
    return combos
