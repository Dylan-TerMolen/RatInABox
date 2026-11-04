"""Pull decoding results for one experiment tag into artifacts/decoding/<tag>/.

Most decoding now runs on Quest, submitted either via the webui or a bare
slurm/*.sh script -- both tag the run with --experiment <tag>, the universal
join key regardless of submission path (see CLAUDE.md). Resolves a tag by
querying webui/db.py's jobs/job_iterations tables first (already-synced
log_file_path -- avoids re-deriving what the webui already knows); falls
back to scanning $SAVE_DIRECTORY/{model}_results/<tag>-*.log directly for
tags submitted outside the webui. Never runs CEBRA itself -- that happened
on Quest; this script only parses .log files that already exist locally.

Usage:
    python -m paper.produce.pull_decoding independent_sweep_080726
    python -m paper.produce.pull_decoding independent_sweep_080726 place_dependent_sweep_080726
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ratinabox.hsw import config
from ratinabox.hsw.results_io import parse as parse_log

from webui import db as webui_db

from paper.figlib.io import ARTIFACTS_ROOT

# job_iterations.params_json key -> canonical scores.parquet column name.
_PARAM_COLUMNS = {
    "percent_task_in_response_values": "percent_task_in_response",
    "percent_task_responsive_cells": "percent_task_responsive_cells",
    "percent_place_cells": "percent_place_cells",
    "holdovers": "holdover",
}

# Hannahs-CEBRAs/pos_score.py's "cm_error" is raw Euclidean distance on
# RatInABox's meters-native position labels -- never actually converted to
# centimeters anywhere upstream (2026-09-29 review item 2: observed values of
# 0.16-0.26 in a 0.95x0.55m arena are metres, not the centimetres the kind
# name claims). Converted here, once, at ingestion -- the only pipeline
# boundary between the raw .log text and every plot that reads scores.parquet
# -- rather than in each figure, so no plotting code needs to remember to do
# it and the .parquet's units are simply correct.
_CM_KINDS = {"place_cm_in_task", "place_cm_out_of_task"}
_METERS_TO_CM = 100.0


def resolve_via_webui(tag: str) -> list[dict] | None:
    """[{model_type, log_path, params, job_id}, ...] for every matched
    iteration of the webui job(s) with this experiment_tag, or None if the
    webui never saw this tag at all (as opposed to seeing it with 0 matched
    logs, which returns an empty list -- a real, if surprising, answer)."""
    jobs = [j for j in webui_db.list_jobs() if j["experiment_tag"] == tag]
    if not jobs:
        return None
    rows = []
    for job in jobs:
        for it in webui_db.list_job_iterations(job["id"]):
            if it["log_file_path"] is None:
                continue
            params = json.loads(it["params_json"])
            rows.append({
                "model_type": params.get("model_type"),
                "log_path": Path(it["log_file_path"]),
                "params": params,
                "job_id": job["id"],
            })
    return rows


def resolve_via_tag_scan(tag: str) -> list[dict]:
    """Fallback for a tag submitted by a bare slurm/*.sh script and never
    registered with the webui: scan every {model}_results/ dir under
    SAVE_DIRECTORY for '<tag>-'-prefixed logs, the same convention
    webui/routers/results.py's logs_for_experiment() uses. No per-iteration
    params available this way (parsed from the log's own header instead, at
    read time in scores_dataframe)."""
    rows = []
    for model_dir in Path(config.SAVE_DIRECTORY).glob("*_results"):
        model_type = model_dir.name[: -len("_results")]
        for log_path in model_dir.glob(f"{tag}-*.log"):
            rows.append({"model_type": model_type, "log_path": log_path, "params": None, "job_id": None})
    return rows


def _params_from_run_header(run_params: dict[str, str]) -> dict:
    """A tag-scan match has no job_iterations row -- fall back to the log's
    own '=== Run parameters ===' header, which main.py always writes."""
    return {"model_type": run_params.get("model_type"), **run_params}


def scores_dataframe(tag: str, matches: list[dict]) -> pd.DataFrame:
    rows = []
    for match in matches:
        parsed = parse_log(match["log_path"].read_text())
        params = match["params"] if match["params"] is not None else _params_from_run_header(parsed.run_params)
        model_type = match["model_type"] or params.get("model_type")
        param_values = {column: params.get(key) for key, column in _PARAM_COLUMNS.items()}

        for iteration_in_file, iteration in enumerate(parsed.iterations):
            for kind, scores in iteration.scores.items():
                for direction, value in scores.items():
                    if kind in _CM_KINDS and value is not None:
                        value = value * _METERS_TO_CM
                    rows.append({
                        "tag": tag,
                        "model_type": model_type,
                        "log_path": str(match["log_path"]),
                        "iteration_in_file": iteration_in_file,
                        **{col: (float(v) if v is not None else None) for col, v in param_values.items()},
                        "kind": kind,
                        "direction": direction,
                        "value": value,
                    })
    return pd.DataFrame(rows)


def pull(tag: str) -> Path:
    matches = resolve_via_webui(tag)
    origin = "webui" if matches is not None else "slurm_direct"
    if matches is None:
        matches = resolve_via_tag_scan(tag)
    if not matches:
        raise SystemExit(
            f"no logs found for tag {tag!r} -- checked webui/data/jobs.db and "
            f"$SAVE_DIRECTORY/*_results/{tag}-*.log"
        )

    scores = scores_dataframe(tag, matches)
    if scores.empty:
        raise SystemExit(f"found {len(matches)} log(s) for tag {tag!r} but parsed zero score rows from them")

    tag_dir = ARTIFACTS_ROOT / "decoding" / tag
    tag_dir.mkdir(parents=True, exist_ok=True)
    scores.to_parquet(tag_dir / "scores.parquet", index=False)

    source = {"origin": origin}
    if origin == "webui":
        job_ids = sorted({m["job_id"] for m in matches})
        source["job_id"] = job_ids[0] if len(job_ids) == 1 else job_ids
    meta = {
        "tag": tag,
        "source": source,
        "n_logs": len(matches),
        "n_rows": len(scores),
        "model_types": sorted(scores["model_type"].dropna().unique().tolist()),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (tag_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    return tag_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tags", nargs="+")
    args = parser.parse_args()
    for tag in args.tags:
        tag_dir = pull(tag)
        print(f"wrote {tag_dir}")


if __name__ == "__main__":
    main()
