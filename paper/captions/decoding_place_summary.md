**Supplementary Figure. Position decoding error across each model's
completed parameter sweep.** Mean position-decoding error in centimeters
(**lower is better** -- the opposite sense from every accuracy/R² panel
elsewhere in this pipeline), mean +/- 95% CI across every combo x iteration
in each model's own completed sweep, split by task state: **in-task** (left)
vs. **out-of-task** (right). All five directions shown: A→A, B→B, A→B, and
the shuffled A→A/A→B floors.

Tags (three-sweep policy -- the only sweeps approved for figure data):
independent_sweep_092926, place_dependent_sweep_092926, and
arousal_mediated_sweep_092926 (all post-date the 2026-09-29 velocity-gain
fix, commit e1e4496). Independent's own sweep finished 2026-10-03 (216/216
grid points) -- all three models' bars now reflect their full, completed
parameter grids. Earlier, while independent_sweep_092926 was still mid-run,
this figure read independent_sweep_080726 instead, which predates this
split entirely (only a pooled, undifferentiated R² "place" kind, no cm, no
task-state split) and rendered as fully unavailable; that's no longer the
case.
