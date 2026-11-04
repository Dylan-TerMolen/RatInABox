**Supplementary Figure. Within-environment (A→A) task-stage decoding across
the whole parameter grid, per model.** The within-environment counterpart to
`robustness`'s cross-environment (A→B) grid -- same data, same per-model
axes, same shared color scale (`metric_range` over all three models),
direction A→A instead of A→B. Task-stage decoding accuracy (KNN classifier
over 5 CS/US bins, not R²; chance = 0.20). IM and PDM share axes (task
weight x task-responsive cells %, faceted by place cells %, holdover fixed
at 1.0); arousal-dependent has no task-weight parameter, so its grid instead
sweeps task-responsive cells % x holdover, faceted by place cells % -- a
real modeling asymmetry (see `robustness`'s caption/CLAUDE.md), not a data
gap. independent_sweep_092926, place_dependent_sweep_092926,
arousal_mediated_sweep_092926 -- all three sweeps complete (216/216 grid
points).

Each block's header reports the fraction of that model's grid points where
A→A accuracy clears its shuffled floor: the real score's 95% CI (across the
combo's iterations) sits entirely above the shuffled floor's own CI, the
same per-point significance test `robustness` uses for A→B.

**Expect this to look different from `robustness`'s A→B grid.**
`decoding_task_summary`'s sweep-wide aggregate already shows all three
models decode well within-environment on average; `task_decoding_by_balance`'s
bioreal-specific point shows PDM/ADM sitting close to chance at that one
operating point despite the aggregate looking strong. This figure is the
per-grid-point view that should help resolve which picture is closer to the
whole story -- whether PDM/ADM's within-env competence is broad across the
grid or concentrated in specific regions of it.
