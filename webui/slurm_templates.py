"""Builds a SLURM `.sh` submission script from a chosen script + filled-in
params, following the conventions already used by hand in
SLURM/*.sh (hannahs-cebras) and ratinabox/hsw/*/SLURM_*.sh.

Grid params: any param can be marked as a "grid axis" in the UI by passing a
comma-separated value list instead of a single value. Multiple grid axes are
combined into one `--array=0-N` job the same way SLURM_place_dependent.sh
does it by hand: each axis becomes a bash array, and SLURM_ARRAY_TASK_ID is
decoded into one combination per axis, row-major.
"""
from __future__ import annotations

import shlex
from dataclasses import dataclass

from . import config

HEADER_TEMPLATE = """#!/bin/bash
#SBATCH --account={account}
#SBATCH --partition={partition}
#SBATCH --gres={gres}
#SBATCH --nodes={nodes}
#SBATCH --ntasks={ntasks}
#SBATCH --array=0-{max_array_index}
#SBATCH --mem={mem}
#SBATCH --time={time}
#SBATCH --job-name="{job_name}_${{SLURM_ARRAY_TASK_ID}}"
#SBATCH --output={output_dir}/{job_name}.%A_%a.out
#SBATCH --mail-type={mail_type}
#SBATCH --mail-user={mail_user}

module purge
"""


@dataclass
class GridAxis:
    var_name: str          # bash array variable name, e.g. AXIS_PERCENT_PLACE_CELLS
    values: list[str]       # raw string values, one per array slot


def _bash_var_name(param_name: str) -> str:
    return "AXIS_" + "".join(c if c.isalnum() else "_" for c in param_name).upper()


def build_grid_axes(grid_params: dict[str, list[str]]) -> list[GridAxis]:
    """grid_params: {param_name: [value1, value2, ...]}, in the order the UI
    submitted them (order determines row-major SLURM_ARRAY_TASK_ID decoding,
    matches SLURM_place_dependent.sh's IDX-shifting pattern)."""
    return [GridAxis(var_name=_bash_var_name(name), values=values)
            for name, values in grid_params.items()]


def array_count(axes: list[GridAxis]) -> int:
    count = 1
    for axis in axes:
        count *= max(len(axis.values), 1)
    return count


def render_grid_mapping(axes: list[GridAxis]) -> str:
    if not axes:
        return ""
    lines = ["# Grid definition -- one array task per combination (row-major)"]
    for axis in axes:
        quoted = " ".join(shlex.quote(v) for v in axis.values)
        lines.append(f"{axis.var_name}_VALUES=({quoted})")
    for axis in axes:
        lines.append(f"N_{axis.var_name}=${{#{axis.var_name}_VALUES[@]}}")
    lines.append("IDX=${SLURM_ARRAY_TASK_ID}")
    for i, axis in enumerate(axes):
        if i < len(axes) - 1:
            lines.append(f"{axis.var_name}=${{{axis.var_name}_VALUES[$((IDX % N_{axis.var_name}))]}}; IDX=$((IDX / N_{axis.var_name}))")
        else:
            lines.append(f"{axis.var_name}=${{{axis.var_name}_VALUES[$IDX]}}")
    lines.append('echo "Task ${SLURM_ARRAY_TASK_ID}: ' +
                 " ".join(f"{axis.var_name}=${{{axis.var_name}}}" for axis in axes) + '"')
    return "\n".join(lines) + "\n"


def _token(name: str, value: str | None, flag: str | None, is_grid: bool) -> str:
    if is_grid:
        rendered = f'"${{{_bash_var_name(name)}}}"'
    else:
        rendered = shlex.quote(str(value))
    return rendered if flag is None else f"{flag} {rendered}"


def build_command(*, repo: str, entry_point: str, conda_env: str,
                   fixed_args: list[tuple[str, str | None, str | None]],
                   grid_param_names: set[str], bool_flags: list[str]) -> tuple[str, str]:
    """fixed_args: list of (name, flag_or_None, value) in CLI order (positionals
    first). grid_param_names marks which of those names are grid axes (their
    'value' is ignored -- the bash var is substituted instead). bool_flags:
    flags to include bare (store_true) with no value.

    Returns (env_setup, command_line).
    """
    if repo == "ratinabox":
        repo_cfg = config.repo_config("ratinabox")
        python_bin = f"${{HOME}}/miniconda3/envs/{conda_env}/bin/python"
        script_path = f"{repo_cfg['remote_path']}/{entry_point}"
        env_setup = 'eval "$(conda shell.bash hook)"\n'
    else:
        repo_cfg = config.repo_config("hannahs_cebras")
        python_bin = "python"
        script_path = f"{repo_cfg['remote_path']}/{entry_point}"
        env_setup = (
            'eval "$(conda shell.bash hook)"\n'
            f"source activate {conda_env}\n"
            f'export PYTHONPATH="${{PYTHONPATH}}:{repo_cfg["remote_path"]}"\n'
            f'export PYTHONPATH="${{PYTHONPATH}}:{repo_cfg["remote_path"]}/scripts"\n'
        )

    tokens = [python_bin, shlex.quote(script_path)]
    for name, flag, value in fixed_args:
        tokens.append(_token(name, value, flag, is_grid=name in grid_param_names))
    for flag in bool_flags:
        tokens.append(flag)
    return env_setup, " \\\n    ".join(tokens)


def render_slurm_script(*, job_name: str, repo: str, entry_point: str,
                         slurm_opts: dict, conda_env: str,
                         fixed_args: list[tuple[str, str | None, str | None]],
                         grid_params: dict[str, list[str]],
                         bool_flags: list[str] | None = None) -> tuple[str, int]:
    """Returns (script_text, array_count)."""
    axes = build_grid_axes(grid_params)
    n = array_count(axes)
    repo_cfg = config.repo_config(repo)
    output_dir = f"{repo_cfg['remote_path']}/webui_out"

    header = HEADER_TEMPLATE.format(
        account=slurm_opts["account"], partition=slurm_opts["partition"],
        gres=slurm_opts["gres"], nodes=slurm_opts["nodes"], ntasks=slurm_opts["ntasks"],
        max_array_index=max(n - 1, 0), mem=slurm_opts["mem"], time=slurm_opts["time"],
        job_name=job_name, output_dir=output_dir,
        mail_type=slurm_opts["mail_type"], mail_user=slurm_opts["mail_user"],
    )

    env_setup, command_line = build_command(
        repo=repo, entry_point=entry_point, conda_env=conda_env,
        fixed_args=fixed_args, grid_param_names=set(grid_params.keys()),
        bool_flags=bool_flags or [],
    )

    parts = [header, env_setup]
    grid_section = render_grid_mapping(axes)
    if grid_section:
        parts.append(grid_section)
    parts.append(f"mkdir -p {shlex.quote(output_dir)}\n")
    parts.append(f"{command_line}\n")
    return "".join(parts), n
