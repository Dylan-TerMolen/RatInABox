"""CLI for the manuscript figure pipeline. See CLAUDE.md's "Figure pipeline
(paper/)" section.

    python -m paper.build setup               # one figure (the normal day-to-day command)
    python -m paper.build setup --check       # check one figure: inputs exist, caption tokens resolve, not stale
    python -m paper.build all                 # every *implemented* figure; unimplemented ones are skipped with a note
    python -m paper.build all --check         # per-figure report; exits nonzero only if an implemented figure has a problem
    python -m paper.build list                # manifest order -> figure numbers + status (planned/partial/done)
"""
from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml

from paper.figlib import style
from paper.figlib.io import ARTIFACTS_ROOT, PAPER_ROOT, FigureInputs, load_decoding, load_sim

REPO_ROOT = PAPER_ROOT.parent
BUILD_ROOT = PAPER_ROOT / "build"
MANIFEST_PATH = PAPER_ROOT / "manifest.yaml"
LEGACY_COVERAGE_PATH = PAPER_ROOT / "legacy" / "coverage.yaml"


def load_legacy_coverage() -> list[dict]:
    if not LEGACY_COVERAGE_PATH.is_file():
        return []
    return yaml.safe_load(LEGACY_COVERAGE_PATH.read_text()).get("legacy", [])


def legacy_not_regenerated(figure_id: str) -> list[str]:
    """Archived pre-pipeline manuscript images (paper/legacy/coverage.yaml)
    that map to this figure and aren't marked regenerated: true yet. See
    CLAUDE.md's "Legacy figures" section -- a warning, not a failure."""
    return [
        entry["file"] for entry in load_legacy_coverage()
        if entry.get("kind") == "figure" and entry.get("figure") == figure_id and not entry.get("regenerated", False)
    ]


def load_manifest() -> list[dict]:
    return yaml.safe_load(MANIFEST_PATH.read_text())["figures"]


def numbered_figures() -> list[tuple[int, dict]]:
    return list(enumerate(load_manifest(), start=1))


def cmd_list() -> None:
    for number, fig in numbered_figures():
        status = fig.get("status", "planned")
        print(f"{number:>2}. {fig['id']:<16} ({fig['kind']}, {fig.get('width', '?')}) [{status}]")


# --- --check ---------------------------------------------------------------

def resolve_sim_run(alias: str) -> Path | None:
    """manifest.yaml names sim inputs by <param_set>-<model> (e.g.
    'bioreal-independent'), not a full run_id -- the git-sha (and, once Phase 1
    lands, seed) suffix would go stale the moment the manifest was written.
    Resolve to whichever matching run_id under artifacts/sim/ was produced
    most recently; multiple shas can coexist (old ones just go unused)."""
    candidates = [p for p in (ARTIFACTS_ROOT / "sim").glob(f"{alias}-*") if p.is_dir()] \
        if (ARTIFACTS_ROOT / "sim").is_dir() else []
    if not candidates:
        return None
    return max(candidates, key=lambda p: json.loads((p / "meta.json").read_text())["created_at"])


def _sim_run_status(alias: str) -> tuple[str, str]:
    """(kind, message), kind in {"OK", "WARN", "FAIL"}."""
    run_dir = resolve_sim_run(alias)
    if run_dir is None:
        return "FAIL", "MISSING"
    meta = json.loads((run_dir / "meta.json").read_text())
    if meta.get("git_dirty"):
        # Day-to-day work happens on uncommitted code -- can't verify staleness
        # against a SHA that was never committed, so this is a warning, not a
        # failure (see CLAUDE.md's build.py CLI section).
        return "WARN", "produced from a dirty working tree, staleness unverified"
    diff = subprocess.run(
        ["git", "diff", "--quiet", meta["git_sha"], "HEAD", "--", "ratinabox/hsw/"],
        cwd=REPO_ROOT,
    )
    return ("FAIL", "STALE -- ratinabox/hsw/ changed since this artifact's sha") if diff.returncode else ("OK", "OK")


def _decoding_tag_status(tag: str) -> tuple[str, str]:
    return ("OK", "OK") if (ARTIFACTS_ROOT / "decoding" / tag).is_dir() else ("FAIL", "MISSING")


def _caption_status(caption_path: str, stats: dict | None, status: str) -> list[tuple[str, str]]:
    """[(kind, message), ...]. Missing captions/unbuilt stats.json are only
    real failures once a figure claims to be `done` -- see CLAUDE.md."""
    path = PAPER_ROOT / caption_path
    caption_kind = "FAIL" if status == "done" else "WARN"
    if not path.is_file():
        return [(caption_kind, f"MISSING caption file {caption_path}")]
    if stats is None:
        return [("WARN", "stats.json not built yet -- {{stat.*}} tokens unchecked")]
    import re
    problems = []
    for token in re.findall(r"\{\{stat\.([\w.]+)\}\}", path.read_text()):
        if token not in stats:
            problems.append(("FAIL", f"UNRESOLVED token stat.{token}"))
    return problems


def check_figure(number: int, fig: dict, stats: dict | None) -> bool:
    """Prints this figure's check report; returns False iff something FAILed."""
    status = fig.get("status", "planned")
    print(f"[{number}] {fig['id']} ({status})")
    ok = True
    for alias in fig.get("inputs", {}).get("sim", []):
        kind, message = _sim_run_status(alias)
        print(f"    sim   {alias}: {message}")
        ok &= kind != "FAIL"
    for tag in fig.get("inputs", {}).get("decoding", []):
        kind, message = _decoding_tag_status(tag)
        print(f"    decoding {tag}: {message}")
        ok &= kind != "FAIL"
    for kind, message in _caption_status(fig["caption"], stats, status):
        print(f"    caption: {message}")
        ok &= kind != "FAIL"
    for file in legacy_not_regenerated(fig["id"]):
        print(f"    LEGACY NOT YET REGENERATED: {file}")
    return ok


def cmd_check(target: str) -> bool:
    stats_path = BUILD_ROOT / "stats.json"
    stats = json.loads(stats_path.read_text()) if stats_path.is_file() else None

    figures = numbered_figures() if target == "all" else \
        [(n, f) for n, f in numbered_figures() if f["id"] == target]
    if not figures:
        raise SystemExit(f"unknown figure id {target!r} -- see paper/manifest.yaml")

    results = [check_figure(number, fig, stats) for number, fig in figures]  # list, not a generator -- must not short-circuit, every figure needs to print
    return all(results)


# --- render ------------------------------------------------------------

def resolve_figure_inputs(fig: dict) -> FigureInputs:
    sim = {}
    for alias in fig.get("inputs", {}).get("sim", []):
        run_dir = resolve_sim_run(alias)
        if run_dir is None:
            raise SystemExit(f"no sim artifact for alias {alias!r} -- run `python -m paper.produce.simulate` first")
        sim[alias] = load_sim(run_dir.name)

    decoding = {}
    for tag in fig.get("inputs", {}).get("decoding", []):
        if not (ARTIFACTS_ROOT / "decoding" / tag).is_dir():
            raise SystemExit(f"no decoding artifact for tag {tag!r} -- run `python -m paper.produce.pull_decoding` first")
        decoding[tag] = load_decoding(tag)

    return FigureInputs(sim=sim, decoding=decoding)


def archive_existing_render(base: Path) -> None:
    """Copy an about-to-be-overwritten render into
    build/figures/history/<id>/<mtime>/ before save_figure replaces it, so
    past looks stay flip-back-able without rebuilding from artifacts. Keyed
    by the outgoing file's mtime (when it was produced), not the new render's --
    build.lock.json (written separately, see lock_entry/update_lock_file) has
    the SHA/run_ids each version was built from."""
    existing = [p for p in (base.with_suffix(f".{ext}") for ext in ("pdf", "png", "svg")) if p.is_file()]
    if not existing:
        return
    stamp = datetime.fromtimestamp(existing[0].stat().st_mtime, tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_dir = BUILD_ROOT / "figures" / "history" / base.name / stamp
    archive_dir.mkdir(parents=True, exist_ok=True)
    for path in existing:
        shutil.copy2(path, archive_dir / path.name)


def save_figure(number: int, figure_id: str, figure) -> Path:
    out_dir = BUILD_ROOT / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / f"{number:02d}_{figure_id}"
    archive_existing_render(base)
    for ext in ("pdf", "png", "svg"):
        # bbox_inches="tight" so a legend placed outside the axes (e.g.
        # trajectory_phase's bbox_to_anchor legend) doesn't get clipped.
        figure.savefig(base.with_suffix(f".{ext}"), dpi=300 if ext == "png" else None, bbox_inches="tight")
    return base


def _panel_bbox(axes_or_group, renderer, figure):
    """One Axes -> its own tight bbox; a group (a multi-axes panel like
    example_fields' 6-subplot grid) -> the union of its members' bboxes.
    Bbox.union needs at least one element, so a bare Axes is wrapped."""
    from matplotlib.transforms import Bbox

    group = axes_or_group if hasattr(axes_or_group, "__iter__") else [axes_or_group]
    bbox = Bbox.union([ax.get_tightbbox(renderer) for ax in group])
    return bbox.transformed(figure.dpi_scale_trans.inverted())


def save_panel_images(figure_id: str, figure) -> int:
    """Each named panel (a figure module's fig.panel_axes -- {name: Axes or
    [Axes, ...]}) saved as its own standalone PNG at
    build/panels/<id>/<name>.png, cropped from the already-rendered composite
    figure via a tight bbox (no re-rendering the panel content itself). A
    multi-axes value (e.g. a 6-subplot small-multiples panel) is saved as one
    image spanning all of them. Lets a panel be rearranged, resized, or
    dropped into a slide without touching the composite.

    PNG only, not pdf/svg: savefig's bbox_inches crop still serializes the
    *entire* figure before cropping, so N panels in 3 vector formats means
    ~3N full-figure vector re-serializations -- for setup.py's ~80k-segment
    trajectory LineCollections that's minutes, not seconds (CLAUDE.md's "a
    few minutes locally" budget for the *whole build*, not one figure's
    panel export). Raster PNG re-encoding is cheap regardless of segment
    count, so panels stay fast; grab the composite's own .pdf/.svg for a
    vector version of a panel if one's ever needed.

    Returns the number of panels saved (0 if the figure module doesn't
    expose panel_axes yet)."""
    panel_axes = getattr(figure, "panel_axes", None)
    if not panel_axes:
        return 0

    panels_dir = BUILD_ROOT / "panels" / figure_id
    panels_dir.mkdir(parents=True, exist_ok=True)
    figure.canvas.draw()  # ensure a renderer exists before asking any axes for its tight bbox
    renderer = figure.canvas.get_renderer()

    for name, axes_or_group in panel_axes.items():
        bbox = _panel_bbox(axes_or_group, renderer, figure)
        figure.savefig(panels_dir / f"{name}.png", dpi=300, bbox_inches=bbox)
    return len(panel_axes)


def lock_entry(number: int, fig: dict, inputs: FigureInputs) -> dict:
    """Cowork's handoff contract (see CLAUDE.md's "Division of labor"): per
    figure, enough for Cowork to know what changed since its last sync and
    report provenance, without it needing to understand artifacts/ itself."""
    return {
        "number": number,
        "id": fig["id"],
        "status": fig.get("status", "planned"),
        "rendered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "inputs": {
            "sim": {alias: {"run_id": a.run_id, "git_sha": a.meta["git_sha"]}
                    for alias, a in inputs.sim.items()},
            "decoding": {tag: {"source": a.meta["source"]} for tag, a in inputs.decoding.items()},
        },
    }


def update_lock_file(entry: dict) -> None:
    lock_path = BUILD_ROOT / "build.lock.json"
    lock = json.loads(lock_path.read_text()) if lock_path.is_file() else {}
    lock[entry["id"]] = entry
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True))


def render_figure(number: int, figure_id: str, *, required: bool) -> None:
    """required=True (a specific figure was asked for by name) raises if it
    isn't implemented; required=False (part of `all`) prints a one-line note
    and moves on -- see CLAUDE.md rule 8, nothing may require every figure to
    exist yet."""
    manifest_by_id = {fig["id"]: fig for fig in load_manifest()}
    if figure_id not in manifest_by_id:
        raise SystemExit(f"unknown figure id {figure_id!r} -- see paper/manifest.yaml")

    try:
        module = importlib.import_module(f"paper.figures.{figure_id}")
    except ModuleNotFoundError as e:
        message = f"paper.figures.{figure_id} isn't implemented yet (see CLAUDE.md build order) -- {e}"
        if required:
            raise SystemExit(message)
        print(f"skipping {figure_id}: not implemented yet")
        return

    fig = manifest_by_id[figure_id]
    inputs = resolve_figure_inputs(fig)
    figure = module.build(inputs, style)
    base = save_figure(number, figure_id, figure)
    n_panels = save_panel_images(figure_id, figure)
    update_lock_file(lock_entry(number, fig, inputs))
    panel_note = f", {n_panels} panels" if n_panels else ""
    print(f"wrote {base}.[pdf,png,svg]{panel_note}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", help="'list', 'all', or one figure id")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.target == "list":
        cmd_list()
        return

    if args.check:
        ok = cmd_check(args.target)
        raise SystemExit(0 if ok else 1)

    targets = [(n, f["id"]) for n, f in numbered_figures()] if args.target == "all" else \
        [(n, f["id"]) for n, f in numbered_figures() if f["id"] == args.target]
    if not targets:
        raise SystemExit(f"unknown figure id {args.target!r} -- see paper/manifest.yaml")
    for number, figure_id in targets:
        render_figure(number, figure_id, required=(args.target != "all"))


if __name__ == "__main__":
    main()
