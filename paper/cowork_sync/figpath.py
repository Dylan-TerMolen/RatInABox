"""Pick the current build PNG for a figure id.

paper/build/figures can hold stale renders of the same id under an old number
(e.g. 07_supp_place_pct.png and 10_supp_place_pct.png after the manifest is
reordered). Prefer the file whose NN prefix equals the figure's manifest
position; otherwise fall back to the most recently modified match.
"""
import glob, os, yaml

_POS = {}


def _positions(paper):
    if paper not in _POS:
        man = yaml.safe_load(open(f"{paper}/manifest.yaml"))["figures"]
        _POS[paper] = {f["id"]: i for i, f in enumerate(man, 1)}
    return _POS[paper]


def find_png(paper, fig_id):
    exact = f"{paper}/build/figures/{_positions(paper).get(fig_id, 0):02d}_{fig_id}.png"
    if os.path.exists(exact):
        return exact
    pngs = glob.glob(f"{paper}/build/figures/[0-9][0-9]_{fig_id}.png")
    return max(pngs, key=os.path.getmtime) if pngs else None
