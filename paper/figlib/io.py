"""Load artifacts written by paper/produce/*.py. Figure/panel code only reads
through this module -- it never opens a file under artifacts/ directly (see
CLAUDE.md's "Figures are build outputs" / "Separate produce from render"
rules). Ad hoc/exploratory scripts (outside the manifest-driven build, see
CLAUDE.md) may also import load_sim/load_decoding for consistent loading.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

PAPER_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_ROOT = PAPER_ROOT / "artifacts"
PARAMS_ROOT = PAPER_ROOT / "params"


def load_param_set(name: str) -> dict:
    """One paper/params/<name>.yaml -- the single source of truth for a
    named parameter set (e.g. "bioreal"). Figures that run at a specific
    operating point read the actual values from here rather than hardcoding
    them a second time, so a figure's displayed parameters can't drift from
    what the set actually says."""
    return yaml.safe_load((PARAMS_ROOT / f"{name}.yaml").read_text())


@dataclass
class SimArtifact:
    """One produce/simulate.py run: both envs' spikes, firing rates, agent
    trajectories, cell metadata, and environment geometry, plus its
    provenance (meta.json)."""
    run_id: str
    meta: dict
    spikes: dict[str, np.ndarray]        # {"A": ..., "B": ...}
    firingrate: dict[str, np.ndarray]
    agent: dict[str, dict[str, np.ndarray]]  # {"A": {"times":.., "x":.., "y":.., "trial_marker":.., "velocity":..}, "B": {...}}
    cells: dict
    environment: dict  # {"A": {"boundary": [[x,y],...], "extent": [minx,maxx,miny,maxy]}, "B": {...}}


@dataclass
class FigureInputs:
    """What build.py hands a figure module's build(inputs, style), resolved
    from manifest.yaml's inputs.sim/inputs.decoding aliases."""
    sim: dict[str, "SimArtifact"]
    decoding: dict[str, "DecodingArtifact"]


@dataclass
class DecodingArtifact:
    """One produce/pull_decoding.py tag: parsed per-iteration scores plus
    provenance (meta.json) recording which run(s) -- webui job or bare slurm
    tag -- the scores came from."""
    tag: str
    meta: dict
    scores: pd.DataFrame  # one row per iteration x direction x metric


def _run_dir(run_id: str) -> Path:
    return ARTIFACTS_ROOT / "sim" / run_id


def _tag_dir(tag: str) -> Path:
    return ARTIFACTS_ROOT / "decoding" / tag


def load_sim(run_id: str) -> SimArtifact:
    run_dir = _run_dir(run_id)
    if not run_dir.is_dir():
        raise FileNotFoundError(
            f"No sim artifact at {run_dir} -- run paper/produce/simulate.py for run_id={run_id!r} first."
        )
    meta = json.loads((run_dir / "meta.json").read_text())
    spikes = {env: np.load(run_dir / f"spikes_{env}.npz")["spikes"] for env in ("A", "B")}
    firingrate = {env: np.load(run_dir / f"firingrate_{env}.npz")["firingrate"] for env in ("A", "B")}
    agent = {
        env: dict(np.load(run_dir / f"agent_{env}.npz"))
        for env in ("A", "B")
    }
    cells = json.loads((run_dir / "cells.json").read_text())
    environment = {env: json.loads((run_dir / f"environment_{env}.json").read_text()) for env in ("A", "B")}
    return SimArtifact(run_id=run_id, meta=meta, spikes=spikes, firingrate=firingrate, agent=agent, cells=cells,
                        environment=environment)


def load_decoding(tag: str) -> DecodingArtifact:
    tag_dir = _tag_dir(tag)
    if not tag_dir.is_dir():
        raise FileNotFoundError(
            f"No decoding artifact at {tag_dir} -- run paper/produce/pull_decoding.py for tag={tag!r} first."
        )
    meta = json.loads((tag_dir / "meta.json").read_text())
    scores = pd.read_parquet(tag_dir / "scores.parquet")
    return DecodingArtifact(tag=tag, meta=meta, scores=scores)
