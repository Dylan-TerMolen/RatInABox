"""Produce local sim artifacts for one param set, across the requested models.

Never runs CEBRA decoding -- most decoding now runs on Quest (webui- or
slurm-submitted) and is pulled in by produce/pull_decoding.py instead, tagged
by experiment_tag rather than reproduced locally (see CLAUDE.md's
"Figure pipeline (paper/)" -> produce-layer design). This script only calls
simulate_experiment() and writes its raw output -- spikes, firing rates,
agent trajectories, cell metadata -- to artifacts/sim/<run_id>/, for figures
that plot that output directly: setup, models, mechanism.

Usage:
    python -m paper.produce.simulate --param-set bioreal
    python -m paper.produce.simulate --param-set bioreal --models independent
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy.io
import yaml

from ratinabox.hsw import config
from ratinabox.hsw.simulate_envs import simulate_experiment

from paper.figlib.io import ARTIFACTS_ROOT, PAPER_ROOT

REPO_ROOT = PAPER_ROOT.parent
MODEL_TYPES = ["independent", "place_dependent", "arousal_mediated"]


def load_params(param_set: str) -> dict:
    path = PAPER_ROOT / "params" / f"{param_set}.yaml"
    return yaml.safe_load(path.read_text())


def load_position_data() -> tuple[np.ndarray, np.ndarray]:
    data = scipy.io.loadmat(config.get_matlab_file_path())
    return data["envA313_531"], data["envB313_602"]


def git_sha_and_dirty() -> tuple[str, bool]:
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True).strip())
    return sha, dirty


def run_id_for(param_set: str, model_type: str, sha: str, iteration: int) -> str:
    # <param_set>-<model>-<shortsha>, no seed segment -- runs are intentionally
    # unseeded (CLAUDE.md decision), the saved artifact is the reproducible unit.
    suffix = f"-iter{iteration}" if iteration else ""
    return f"{param_set}-{model_type}-{sha[:7]}{suffix}"


def agent_arrays(agent) -> dict[str, np.ndarray]:
    times, x, y, trial_marker = agent.position_data
    return {
        "times": times,
        "x": x,
        "y": y,
        "trial_marker": trial_marker,
        "velocity": np.asarray(agent.smoothed_velocities),
    }


def environment_geometry(agent) -> dict:
    """Boundary polygon vertices + extent -- enough for panel code to redraw the
    arena outline from a saved artifact alone (see paper/figlib/panels/setup.py's
    draw_environment_boundary), without importing RatInABox's own Environment
    object or re-running build_agent (figures only read artifacts, never sim)."""
    env = agent.Environment
    return {
        "boundary": np.asarray(env.boundary).tolist(),
        "extent": np.asarray(env.extent).tolist(),
    }


def place_responsive_mask(model) -> np.ndarray:
    """independent/place_dependent (CombinedPlaceTebc subclasses) expose
    place_responsive_indices directly. arousal_mediated.TEBC doesn't subclass
    CombinedPlaceTebc -- every cell gets a place_cell_centres via the base
    PlaceCells.__init__, and non-place cells are instead marked by having
    their index in indices_to_zero_out (see arousal_mediated_model/TEBC.py)."""
    if hasattr(model, "place_responsive_indices"):
        return np.asarray(model.place_responsive_indices, dtype=bool)
    mask = np.full(model.n, True)
    mask[model.indices_to_zero_out] = False
    return mask


def cells_metadata(model) -> dict:
    return {
        "cell_types": np.asarray(model.cell_types).tolist(),
        "task_responsive_indices": np.asarray(model.task_responsive_indices, dtype=bool).tolist(),
        "place_responsive_indices": place_responsive_mask(model).tolist(),
        "place_cell_centres": np.asarray(model.place_cell_centres).tolist(),
        "place_cell_width": float(model.params["widths"]),
    }


def write_sim_artifact(run_id: str, meta: dict, spikesA, firingrateA, agentA, modelA,
                        spikesB, firingrateB, agentB, modelB) -> Path:
    run_dir = ARTIFACTS_ROOT / "sim" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    np.savez(run_dir / "spikes_A.npz", spikes=spikesA)
    np.savez(run_dir / "spikes_B.npz", spikes=spikesB)
    np.savez(run_dir / "firingrate_A.npz", firingrate=firingrateA)
    np.savez(run_dir / "firingrate_B.npz", firingrate=firingrateB)
    np.savez(run_dir / "agent_A.npz", **agent_arrays(agentA))
    np.savez(run_dir / "agent_B.npz", **agent_arrays(agentB))
    (run_dir / "cells.json").write_text(json.dumps({
        "A": cells_metadata(modelA),
        "B": cells_metadata(modelB),
    }, indent=2))
    (run_dir / "environment_A.json").write_text(json.dumps(environment_geometry(agentA), indent=2))
    (run_dir / "environment_B.json").write_text(json.dumps(environment_geometry(agentB), indent=2))
    return run_dir


def simulate_and_save(model_type: str, params: dict, param_set: str,
                       position_data_envA: np.ndarray, position_data_envB: np.ndarray,
                       sha: str, dirty: bool, iteration: int = 0) -> Path:
    spikesA, firingrateA, agentA, modelA, spikesB, firingrateB, agentB, modelB = simulate_experiment(
        model_type, position_data_envA, position_data_envB, params["num_neurons"],
        params["percent_task_in_response"], params["percent_task_in_response_dist"], params["percent_task_in_response_std"],
        params["percent_task_responsive_cells"], params["percent_is_task_responsive_distribution"], params["percent_place_cells"],
        params["holdover"], params["task_types"],
    )
    run_id = run_id_for(param_set, model_type, sha, iteration)
    meta = {
        "run_id": run_id,
        "param_set": param_set,
        "model_type": model_type,
        "params": params,
        "git_sha": sha,
        "git_dirty": dirty,
        "iteration": iteration,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return write_sim_artifact(run_id, meta, spikesA, firingrateA, agentA, modelA,
                               spikesB, firingrateB, agentB, modelB)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--param-set", default="bioreal")
    parser.add_argument("--models", nargs="+", choices=MODEL_TYPES, default=MODEL_TYPES)
    parser.add_argument("--iterations", type=int, default=1, help="number of sim iterations per model")
    args = parser.parse_args()

    params = load_params(args.param_set)
    position_data_envA, position_data_envB = load_position_data()
    sha, dirty = git_sha_and_dirty()
    if dirty:
        print(f"warning: working tree is dirty -- meta.json will record git_dirty=true for sha {sha[:7]}")

    for model_type in args.models:
        for iteration in range(args.iterations):
            run_dir = simulate_and_save(model_type, params, args.param_set,
                                         position_data_envA, position_data_envB,
                                         sha, dirty, iteration)
            print(f"wrote {run_dir}")


if __name__ == "__main__":
    main()
