# CLAUDE.md

Fork of RatInABox (`origin` = Dylan-TerMolen/RatInABox, `upstream` = hsw28/RatInABox) used
for the Disterhoft-lab three-model tEBC paper (Wirtshafter et al.). Our code lives in
`ratinabox/hsw/`; the rest of `ratinabox/` is the upstream library — don't modify it
unless the task explicitly requires it.

## Repo map (hsw work only)

| Path | What it is |
|---|---|
| `ratinabox/hsw/main.py` | Sim + CEBRA decoding entry point. Writes one `.log` per run to `$SAVE_DIRECTORY/{model}_results/` |
| `ratinabox/hsw/simulate_envs.py` | `simulate_experiment()` — the single source of truth for one env A → env B simulation. Figure code must call this, never re-implement it |
| `ratinabox/hsw/{independent,place_dependent,arousal_mediated}_model/TEBC.py` | The three models (paper: IM, PDM, ADM) |
| `ratinabox/hsw/tebc_response.py`, `combined_place_tebc.py`, `utils.py` | Shared response types, place+task blending, constants (`SIMULATION_STEP_SECONDS = 1/30`, `DEFAULT_TASK_TYPES = [1,2,3,8]`) |
| `ratinabox/hsw/args_parser.py` | CLI params, grid params per model, CEBRA overrides |
| `ratinabox/hsw/env.py` | Loads `ratinabox/hsw/.env` (`MATLAB_FILE_PATH`, `SAVE_DIRECTORY`, `TRAINING_DATA_DIR`, `ENVIRONMENT`) |
| `ratinabox/hsw/tests/` | pytest suite — run `pytest ratinabox/hsw/tests` after any model change |
| `ratinabox/hsw/docs/manuscript_todo.md` | Figure/value checklist parsed from the draft — keep it in sync |
| `ratinabox/hsw/notebooks/figures.ipynb` | Current Fig 1/2 prototype code (**gitignored**) — being migrated into `paper/` (below) |
| `webui/` | Local FastAPI app that submits SLURM jobs to Quest and parses logs (`webui/hsw_log.py` = the `.log` parser) |
| `bugs.md` | Known bugs + history. Read before touching spike generation, field widths, or decoders |
| `hannahs_cebras` (separate repo: Hannahs-CEBRAs, pip-installed) | `cond_decoding_AvsB`, `pos_decoding_AvsB` |

Compute: CEBRA decoding runs on Quest (`tfl2886@quest.it.northwestern.edu`, results under
`~/projects/RatInABox/saved/results`) via `slurm/` scripts or the webui. Local machine has
no CUDA — don't run CEBRA fits locally except as small smoke tests.

**Gitignore gotcha:** `figures/`, `scripts/`, `sweeps/`, `slurm/`, `saved/`,
`ratinabox/analysis/`, and `ratinabox/hsw/notebooks/` are all ignored. Anything that must
be reproducible (figure code, param sets, manifests) must live in a tracked path — i.e. `paper/`.

---

## Figure pipeline (`paper/`)

Goal: every manuscript figure and every number quoted in the text can be regenerated with
one command after new experiments, and dropped into the Word manuscript without hand edits.

### Core rules

1. **Figures are build outputs.** Never hand-edit a figure file, never paste a notebook
   screenshot into the manuscript. If a figure needs a change, change the code.
2. **Separate produce from render.** Simulation and CEBRA decoding (slow, Quest) produce
   *data artifacts*. Figure scripts only *read* artifacts and plot — they never run a sim
   or a CEBRA fit. Rendering all figures should take seconds to a few minutes locally.
3. **One param set, named.** The "biologically plausible" parameters used for the main
   figures live in exactly one file (`paper/params/bioreal.yaml`). No figure hardcodes
   `percent_place_cells`, `balance`, etc.
4. **Recorded, not seeded.** No RNG seeding anywhere -- decided 2026-09-23, don't add it.
   Reproducibility comes from the saved artifact: a figure re-renders identically from its
   artifact, and re-running a sim is expected to give a new, statistically equivalent draw.
   Every artifact records the git SHA, dirty flag, param set, and CLI args that produced it.
5. **Stable IDs, not numbers.** Figures are referenced by ID (`cross_env`), never by
   "Fig 3" in code or filenames. Numbering is derived from manifest order, so reordering
   the paper is a one-line manifest change.
6. **Style in code, not Illustrator.** Fonts, sizes, colors, axis labels (e.g. "Time (min)")
   are set by `paper/figlib/style.py`. Illustrator is allowed only for final journal polish
   after data are frozen, and those edits are not part of the pipeline.
7. **Ad hoc/exploratory images are not manuscript figures.** Quick sanity-check or QA plots
   belong in `ratinabox/hsw/notebooks/` or `scripts/` (both already gitignored), never in
   `paper/figures/`. They're exempt from rule 1 and from `manifest.yaml`/`build.py` -- not
   tracked, not reviewed as part of the build. They may still import
   `paper.figlib.style`/`paper.figlib.io.load_sim`/`load_decoding` for consistent colors and
   loading, but nothing about them needs to be reproducible by one command.
8. **Piece by piece.** Figures are independent. One figure can be built, reviewed, and
   synced into the manuscript while others don't exist yet, and a figure can ship with a
   subset of its planned panels. Nothing in the pipeline may require all figures (or all
   panels) to be done: `build all` renders whatever figure modules exist and skips the rest
   with a one-line note; `--check` and the manuscript sync work per figure; a problem in one figure
   never blocks another.

### Layout

```
paper/
  manifest.yaml            # figure ID -> order, panels, data inputs, size, caption
  params/
    bioreal.yaml           # main-text parameter set (single source of truth)
    sweeps.yaml            # which sweep tags feed the robustness figure
  produce/                 # slow steps that create artifacts (may submit to Quest)
    simulate.py            # simulate_experiment() -> artifacts/sim/<run_id>/. Local, no
                            # CUDA -- only for panels that plot raw sim output directly
                            # (setup/models/mechanism), never CEBRA decoding.
    pull_decoding.py       # Most decoding now runs on Quest via the webui or a bare
                            # slurm/*.sh script -- both tag the run with --experiment
                            # <tag>, the universal join key regardless of submission
                            # path. Resolves a tag by querying webui/db.py's
                            # jobs/job_iterations tables first (already-synced
                            # log_file_path -- avoids re-deriving what the webui already
                            # knows); falls back to scanning
                            # $SAVE_DIRECTORY/{model}_results/<tag>-*.log directly for
                            # tags submitted outside the webui. Either path ->
                            # artifacts/decoding/<tag>/scores.parquet + meta.json, with
                            # meta.json's `source` field recording {origin: webui,
                            # job_id} or {origin: slurm_direct}.
  figlib/
    style.py               # rcParams, journal widths, MODEL_COLORS, PHASE_COLORS
    io.py                  # load_sim(run_id), load_decoding(tag) (wraps webui/hsw_log.py)
    panels/                # pure functions: panel_x(ax, data, **opts) -> None
      setup.py  models.py  decoding.py  mechanism.py  sweeps.py
  figures/                 # one module per figure ID; composes panels, no plotting logic
    setup.py  models.py  cross_env.py  mechanism.py  robustness.py  supp_position.py
  stats.py                 # computes every number the text quotes -> build/stats.json
  captions/<figure_id>.md  # caption text; may reference {{stat.key}} placeholders
  build.py                 # CLI (below)
  artifacts/               # gitignored — data cache (sim outputs, pulled decoding logs)
  build/                   # gitignored — rendered figures, stats.json, build.lock.json
```

### Interfaces

**Panel function** (the unit of reuse):
```python
def trajectory_by_phase(ax: plt.Axes, sim: SimArtifact, env: Literal["A", "B"], *, show_legend=True) -> None:
    """Draws into ax. No fig creation, no savefig, no plt.show(), no global state."""
```

**Figure module** — every file in `paper/figures/` exposes exactly:
```python
FIGURE_ID = "cross_env"
def build(inputs: FigureInputs, style: Style) -> matplotlib.figure.Figure: ...
```
`FigureInputs` is resolved by `build.py` from `manifest.yaml`; figure modules never read
paths, env vars, or `.env` directly.

**Artifacts** — `artifacts/sim/<run_id>/` contains `meta.json` (git SHA, dirty flag, params,
timestamp), `spikes_{A,B}.npz`, `firingrate_{A,B}.npz`, `agent_{A,B}.npz` (position,
velocity, trial markers), and `cells.json` (place/task indices, cell types, field centres,
widths). `run_id` = `<param_set>-<model>-<shortsha>`.
`artifacts/decoding/<tag>/` holds the raw `.log` files plus a parsed `scores.parquet`
(one row per iteration × direction × metric).

**manifest.yaml** (shape):
```yaml
figures:
  - id: setup
    kind: main            # main | supplementary
    width: double         # single | double (style.py maps to mm)
    height_mm: 120
    inputs: {sim: [bioreal-independent]}
    panels: [schematic, trajectory_time_A, trajectory_time_B, trajectory_phase_A, trajectory_phase_B, place_coverage_A, place_coverage_B]
    caption: captions/setup.md
    status: partial       # planned | partial | done -- informational; build.py never requires 'done'
  - id: cross_env
    kind: main
    inputs: {decoding: [bioreal-independent, bioreal-place_dependent, bioreal-arousal_mediated]}
    ...
```
`inputs.sim`/`inputs.decoding` entries are `<param_set>-<model>` aliases, not literal
run_ids/tags -- pinning an exact `-<shortsha>` (or a Quest tag with a date baked in) in
`manifest.yaml` would go stale the moment it was written. `build.py` resolves each alias to
whichever matching artifact under `artifacts/sim/`/`artifacts/decoding/` was produced most
recently, and records that resolution (plus its SHA) into `build.lock.json`.

**build.py CLI**:
```
python -m paper.build setup               # one figure (the normal day-to-day command)
python -m paper.build setup --check       # check one figure: inputs exist, caption tokens resolve, not stale
python -m paper.build all                 # every *implemented* figure; unimplemented ones are skipped with a note
python -m paper.build all --check         # per-figure report; exits nonzero only if an implemented figure has a problem
python -m paper.build list                # manifest order -> figure numbers + status (planned/partial/done)
```
Outputs per figure: `build/figures/<NN>_<id>.pdf` (vector, for the journal),
`.png` (300 dpi, for Word), `.svg`, plus each panel alone in `build/panels/<id>/`.
`build/build.lock.json` records, per figure, the artifact run_ids/tags, their SHAs, and
input hashes. `--check` flags a figure STALE if an artifact's SHA differs from the current
model code in `ratinabox/hsw/`. An artifact produced from a dirty tree is a **warning**, not a
failure (day-to-day work happens on uncommitted code). Missing caption files are warnings
until a figure's status is `done`.

**stats.json** — flat keys, e.g. `cross_env.independent.task_AtoB.mean`,
`cross_env.independent.task_AtoB.perm_p`, `setup.n_units`, `setup.pct_place_cells`. Each
entry stores `value`, `formatted` (string as it should appear in the text), `n`, and the
source artifact. The manuscript's `[value]` placeholders map to these keys.

### Figure IDs (current draft → ID)

Draft numbering is inconsistent (see `manuscript_todo.md` §0); use IDs.

| ID | Draft | Content | Inputs | Existing code to port |
|---|---|---|---|---|
| `setup` | Fig 1 | tEBC schematic; env A/B trajectories (line, time in min); trajectories by trial phase; place-field tiling | sim | `figures.ipynb` cells 3–10 |
| `models` | Fig 2 | raw response types; IM/PDM in/near/out-of-field grids; ADM 2×2 (field × running); rasters per model | sim | `figures.ipynb` cells 11–37 |
| `cross_env` | Fig 3 | A→A, B→B, A→B task decoding + shuffled floors for IM/PDM/ADM at `bioreal` | decoding | none yet (deferred in notebook cell 40) |
| `mechanism` | Fig 4 | one cell's firing in A vs B, task vs non-task, per model; optional stability metric | sim | `figures.ipynb` cells 38–39 (trajectory-through-field) |
| `robustness` | Fig 5 / supp | cross-env decoding over parameter grids, per model | decoding (sweeps) | `scripts/pull_and_plot_holdover_sweep.py`, `webui/sweep_plots.py` |
| `supp_position` | supp | position decoding A→A / A→B, in-task vs out-of-task | decoding | none yet |
| `bio_model` | Fig 6? | undefined in draft — do not build until authors define it | — | — |

### Division of labor: Claude Code builds, Cowork syncs

**Claude Code (this repo) owns all image generation** -- simulations, artifacts, panels,
figure rendering, captions, `stats.json`. **It never opens, edits, or writes the manuscript**
and never touches OneDrive/SharePoint.

**Claude in Cowork owns the manuscript side -- images only.** Figures live in a separate
figures document, `Figures/d1 Figures.docx` in the synced OneDrive folder "Hippocampus
Computational Modeling Paper" (one boxed figure per page, alt text = figure id, caption
placeholder the authors fill in); the manuscript itself holds no images and just cites
"Figure N". Cowork moves figure images in and out of that document
and may delete superseded figure images. It **never changes manuscript text** -- no captions,
no stats, no edits to prose -- and verifies every sync leaves the text byte-identical. It
reads this repo's `paper/build/` but doesn't generate or restyle figures; if a figure needs a
change, that's a Claude Code task.

**`paper/cowork_sync/` belongs to Cowork.** It holds the scripts Cowork uses to swap figures
into the Word figures document and to build the "d1 Figure Proofs" page. Don't modify or run
them from Claude Code; they only read `manifest.yaml`, `build/figures/`, `build/build.lock.json`
and `legacy/coverage.yaml`, so keep those formats stable.

**The handoff contract** -- what Cowork reads from `paper/build/` after a build:
- `figures/<NN>_<id>.png` (300 dpi) -- the file placed in Word. `.pdf`/`.svg` are for the journal.
- `build.lock.json` -- per figure: number, id, status, render timestamp, artifact run_ids +
  SHAs. Cowork uses it to know what changed since the last sync and to report provenance.
- `captions/<id>.md` (in `paper/`, tracked) -- caption text, with `{{stat.key}}` tokens
  already resolved into `build/captions/<id>.md` by the build.
- `stats.json` -- values for `{{stat.key}}` placeholders in the manuscript body.
Keep these paths and filenames stable; Cowork depends on them. A figure is ready to sync
when `python -m paper.build <id> --check` passes -- say so when handing off.

**Manuscript convention:** each placed figure image's **alt text = its figure ID**
(`setup`, `cross_env`, ...). That's how a rebuilt PNG is matched to the image it replaces.
Captions and `stats.json` values are for the authors to paste in; Cowork doesn't insert them.

### Legacy figures (`paper/legacy/`) -- nothing may go missing

The images that were in the manuscript draft before this pipeline existed were removed from
the Word doc and archived in `paper/legacy/` (tracked). `paper/legacy/coverage.yaml` maps each
one to the figure id + panel(s) that must regenerate it (`kind: figure`), or marks it
`superseded` (older draft of another entry) or `reference` (Hannah's source-paper example --
informs styling, not regenerated).

- `manifest.yaml` must include every panel named in `coverage.yaml`. When porting a figure,
  start from its legacy entries so no panel is dropped.
- `python -m paper.build <id> --check` should warn `LEGACY NOT YET REGENERATED: <file>` for
  each `kind: figure` entry of that figure whose panels aren't built yet (warning, not failure).
- When all of an entry's panels are built, set `regenerated: true` in `coverage.yaml`. Never
  delete legacy files or entries.
- Until an entry is regenerated, Cowork keeps the legacy image on a "Pending regeneration"
  page in the figures document, and removes it only once `regenerated: true`.

### Build order (infrastructure first; after step 4 each figure proceeds independently, in any order)

1. **DROPPED -- no seeding** (decided 2026-09-23). Don't add `--seed` or seed any RNG.
   Git SHA + dirty flag + params in `meta.json` are the provenance record.
2. **DONE.** Moved `webui/hsw_log.py` → `ratinabox/hsw/results_io.py`; `webui/hsw_log.py` is now
   a re-export shim so existing `from . import hsw_log` call sites (`webui/sweep_results.py`,
   `webui/routers/results.py`) needed no changes.
3. **DONE.** `paper/` layout, `figlib/style.py` (rcParams/widths + `PHASE_COLORS`/
   `FIELD_STATE_COLORS` ported from `figures.ipynb`; `MODEL_COLORS` validated 2026-09-25
   with the dataviz skill's validate_palette.js -- blue/orange/aqua, all-pairs PASS in both
   modes, see style.py's comment for the exact command/scores), `manifest.yaml` (all 6
   defined figure IDs; `bio_model` intentionally omitted per its own row above), `build.py` with working
   `list`/`--check`, `.gitignore` entries for `paper/artifacts/`/`paper/build/` (note: the
   pre-existing top-level `figures/` rule would have silently swallowed `paper/figures/` too --
   fixed with an explicit `!paper/figures/` rescue).
4. **DONE (initial cut).** `produce/simulate.py` writes real sim artifacts for `bioreal` × all
   3 models (verified against real `.env`/MATLAB data, round-tripped through
   `figlib.io.load_sim`). `simulate_experiment()` was extended to also return `modelA`/`modelB`
   (not just their spikes/firingrate/agent) so this script can pull cell metadata --
   `place_cell_centres`, `cell_types`, `task_responsive_indices`, field width -- without
   re-deriving it; `main.py` and the integration test were updated for the new 8-tuple return.
4b. **TODO (small, do next).** Make `build.py` match rule 8: `all` skips figures whose
   `paper/figures/<id>.py` doesn't exist (print a note, don't `SystemExit`); `--check` accepts
   a figure id; dirty-tree artifacts and missing captions on non-`done` figures are warnings;
   `list` shows `status`. Drop the `seed` field from `produce/simulate.py`'s `meta.json`.
5. **In progress (`setup` partial: env-A trajectory panels only).** Port `setup` and `models` from `figures.ipynb` into panels + figure
   modules. Keep behavior identical (same colors — the notebook's palettes are already
   CVD-validated). Afterward the notebook should only import from `paper.figlib`.
6. **`produce/pull_decoding.py` DONE (webui-db-first, tag-scan fallback implemented and
   tested).** Pulled two real completed webui sweeps (`independent_sweep_080726`,
   `place_dependent_sweep_080726`, 216/216 matched each) into
   `artifacts/decoding/<tag>/scores.parquet`. `cross_env`/`supp_position` themselves are
   still **not started** -- those need `bioreal`-specific Quest runs, which don't exist yet
   (the sweeps above are parameter-grid data, not the `bioreal` operating point). In the
   meantime, four standalone decoding figures were built directly off the sweep data:
   `decoding_task_summary`, `decoding_place_summary` (direction bar charts, both models) and
   `decoding_task_heatmap_independent`/`_place_dependent` (faceted parameter-grid heatmaps,
   styling ported from `scripts/pull_and_plot_holdover_sweep.py`). These cover the same
   ground `robustness` is meant to (see that row's own note) -- fold in or retire once
   `robustness`'s final multi-model layout is decided. `build.lock.json` writing was also
   added to `build.py` (per the handoff contract below) since these are the first figures
   built since that contract was written.
7. **`stats.py`, captions not started.** `mechanism` not started.
8. **Not a Claude Code task.** Manuscript sync is handled in Cowork (see "Division of
   labor"). Don't build a `docx_sync` tool here; do write `build.lock.json` and resolved
   captions so the handoff has what it needs.

### Decisions (resolved 2026-09-23, recorded in `paper/params/bioreal.yaml`)

- **`percent_place_cells` = 0.2** (20%, the draft's value; `figures.ipynb`'s 0.4 and
  `args_parser`'s 0.7 default are not used for `bioreal`).
- **`percent_task_responsive_cells` = 0.4** (40%, matches the draft's "20% place cells,
  40% task-responsive" pairing).
- **`percent_task_in_response` ("balance") and `holdover`:** still genuinely open --
  `bioreal.yaml` currently holds `args_parser`'s own pre-`bioreal` defaults (0.5, 1.0) as an
  explicitly-marked PROVISIONAL placeholder so `produce/simulate.py` has something runnable
  (independent/place_dependent's `CombinedPlaceTebc.__init__` requires a real value here;
  `arousal_mediated` ignores this axis entirely). Swap the real values into the yaml once
  decided -- nothing downstream should need to change.
- **Decoder split: sequential, unshuffled 75/25.** Verified by reading
  `Hannahs-CEBRAs/hold_out.py` directly (`cond_decoding_AvsB.py` and
  `pos_decoding_AvsB_DEP.py` both use it) -- it slices `data[:split_idx]`/`data[split_idx:]`
  with no shuffle. The draft's Methods section already says this; **the draft's Results
  section ("random 75/25 by trial") is wrong and needs a text fix**, not a code change.
- **No seeding.** Sample size per condition is whatever `num_iters` a run used (recorded in
  `meta.json`). Runs are intentionally unseeded; saved artifacts are the reproducible unit.
- **Above-chance test: CI non-overlap.** `stats.py` compares each real score's mean +/- CI
  (across iterations) against its paired shuffled score's mean +/- CI (`shuffA->A`/`shuffA->B`,
  already computed per iteration in the `.log` output) -- not a separate permutation test.
- **Target journal:** none named yet. `style.py` keeps the documented fallback (89 mm single /
  183 mm double column, 5–7 pt sans-serif) until one is picked.

### Conventions

- Model keys in code: `independent`, `place_dependent`, `arousal_mediated`. Display names:
  "Independent (IM)", "Place-dependent (PDM)", "Arousal-dependent (ADM)". The notebook's
  older "Additive"/"Dependent" labels are legacy — don't use them in new code.
- Units: time in seconds internally, displayed in min for session-scale axes and s for
  trial-scale axes; position in m internally, cm in labels.
- Colors come only from `style.py` (`MODEL_COLORS`, `PHASE_COLORS`, `FIELD_STATE_COLORS`);
  validate any new palette before adding it.
- A new experiment that should change a main figure = new/updated param set or sweep tag
  in `paper/params/`, then `produce` → `build <id>` → review → `build <id> --check` →
  hand off to Cowork for the manuscript sync, one figure at a time. Nothing else.
