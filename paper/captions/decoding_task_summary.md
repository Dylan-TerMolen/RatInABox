**Supplementary Figure. Task-stage decoding across each model's completed
parameter sweep.** Task-stage decoding accuracy (KNN classifier over 5
CS/US bins, not R²; chance = 0.20, dashed line), mean +/- 95% CI across every
combo x iteration in each model's own completed sweep. This is a sweep-wide
aggregate across each model's full parameter grid, not a single `bioreal`
operating point (contrast manifest figure `task_decoding_by_balance`, which
is bioreal-specific, all three models).

Tags (three-sweep policy -- the only sweeps approved for figure data):
independent_sweep_092926, place_dependent_sweep_092926, and
arousal_mediated_sweep_092926, all run after the 2026-09-29 velocity-gain fix
(commit e1e4496). Independent's own post-fix sweep finished 2026-10-03
(216/216 logs); all three models are now the same vintage (earlier, while it
was still in progress, this figure read independent's pre-fix
independent_sweep_080726 tag instead, a vintage mismatch flagged in the
figure's title -- no longer the case).

**Within-environment** (A→A, B→B): all three models decode well above
chance and their shuffled floor. **Cross-environment** (A→B): PDM and ADM
sit close to their shuffled floor, consistent with the manuscript's claim
that only IM generalizes task information across environments -- see
`robustness` for the per-grid-point above-chance fraction.
