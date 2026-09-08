# Manuscript TODO — three-model HSW paper

Parsed from the rough Results/Methods draft (2026-08-13). Organized so items can be
checked off as sims/decoding runs produce numbers. See also
`wirtshafter-2025-universal-hippocampal-code.md` for the source-paper summary this
work is compared against.

## 0. Fix figure numbering mismatch

The inline `(FIG n)` citations in the Results text and the itemized figure list at
the bottom of the draft are two different passes and are offset by one starting at
Figure 2 (bottom-list "Figure 2" = inline "FIG 3" content, etc.), and bottom-list
"Figure 6" ("potential biologic model?") has no inline counterpart at all.

- [ ] Reconcile the two figure-numbering passes into one consistent sequence
- [ ] Decide what "Figure 6 — potential biologic model" actually shows, or drop it
- [ ] Recover/replace the dropped inline image reference in the Fig 1 notes
      ("Perhaps we want something like this also to show where the task is
      taking place" — image didn't survive the paste)

## 1. Figures

### Figure 1 — Experimental setup
- [ ] Schematic of tEBC task (CS → trace → US)
- [ ] Per-environment example trajectory (rectangular + oval)
- [ ] Per-environment place-field coverage, showing tiling
- [ ] Switch trajectory plot from scatter points to a continuous line
- [ ] Label time axis "Time (min)" (can be fixed in Illustrator post hoc)
- [ ] Add a way to mark where in the trajectory task trials occur

### Figure 2 — model schematics (equations) + HPC activity reproduction
- [ ] Write out equations for IM, PDM, ADM (currently placeholder heading only)
- [ ] Panel: IM/PDM task + place response types, split by in-field vs out-of-field
- [ ] Panel: ADM 2×2 grid (in-field×moving, in-field×still, out-field×moving, out-field×still)
- [ ] Raster plots for each model
- [ ] Decide whether A→A position decoding goes here or to supplement

### Figure 3 — cross-environment task-stage decoding (all 3 models)
- [ ] A→B task decoding for IM/PDM/ADM using biologically plausible params
      (explicitly NOT the grid-search values)

### Figure 4 — single-cell response stability across environments
- [ ] Pick one cell/position in env A with a place field
- [ ] Show that cell's firing in A vs. B, split by task vs. non-task epochs
- [ ] Repeat/compare across IM, PDM, ADM

### Figure 5 — parameter-space robustness (may be supplemental)
- [ ] Grid search of cross-environment decoding for each model
- [ ] Decide main-text vs. supplemental placement

### Figure 6 — "potential biologic model?"
- [ ] Define this figure's content — no description exists anywhere in the draft yet

## 2. Missing text/sections

- [ ] Sampling-rate sentence near Fig 1 paragraph (short, pointing to Methods)
- [ ] Model comparison table (assumptions/predictions/results per model)
- [ ] Discussion section (currently empty header only)
- [ ] Methods section — write full content for each listed subsection:
  - [ ] Equations for each model
  - [ ] Definitions of every variable
  - [ ] Place- and task-cell sampling
  - [ ] Whether cell identities overlap
  - [ ] Response-type distributions
  - [ ] Firing-rate generation and noise
  - [ ] Shared parameter values
  - [ ] Model-specific parameters
  - [ ] Trajectories and trial timing
  - [ ] Decoder training and testing
  - [ ] Random seeds and repetitions
  - [ ] Parameter sweeps
  - [ ] Statistical tests

## 3. Missing values / results to run and fill in

- [ ] `[N]` simulated units
- [ ] Position-decoding metric + value, IM/PDM/ADM, env A, vs. chance/null
- [ ] Position-decoding metric + value, env B
- [ ] Cross-env position-decoding failure metric + permutation p (A→B and B→A)
- [ ] Within-env task-stage decoding metric + p, all 3 models, both envs
- [ ] Cross-env task-stage decoding metric + p for IM (A→B)
- [ ] "Did not exceed ???" threshold/value for PDM and ADM cross-env decoding
- [ ] Effect of including task data on position decoding (marked "dont have this
      result yet" in draft)
- [ ] Parameter-sweep: which parameter(s) were varied (currently blank)
- [ ] Parameter-sweep: how/why IM decoding declines as that parameter varies
- [ ] Parameter-sweep: `[X%]` of tested parameter space where IM stays above chance
- [ ] Parameter-sweep: `[N]` independent sims per parameter combination

## 4. Open decisions needing an author call

- [ ] Confirm ~8% task+place overlap figure (0.4 × 0.2) is correct and that
      assignment is truly independent in the sim
- [ ] Balance % and holdover %: pick single fixed values and report them, or run
      a 2D sweep over both while holding place%/task% fixed?
- [ ] Position-decoding train/test split: confirm 75/25
- [ ] Cross-env decoder training data: same 75% subset as within-env decoding,
      or retrain on 100% of env-A trials?
- [ ] Verify "all three models support within-env task-stage decoding" is
      actually true in the data (draft flags this as unconfirmed)
- [ ] Only keep the "within-env performance was matched across models" sentence
      if the data actually supports it
- [ ] Decide whether to add a quantitative (not just qualitative) stability
      metric to Figure 4/5's single-cell stability analysis
