**Supplementary Figure. Cross-environment position decoding fails across the
whole parameter grid, not just at one operating point.** Mean position
error in centimeters (**lower is better**; see Methods for why R² isn't
used here) for A→B, out-of-task samples only, across each model's own swept
parameter grid -- the 2D-heatmap, print-safe counterpart to
`place_robustness_3d_cross`'s 3D surfaces, same data and same policy
(independent_sweep_092926, place_dependent_sweep_092926,
arousal_mediated_sweep_092926). IM and PDM share axes (task weight x
task-responsive cells %, faceted by place cells %, task cells carried over
A→B fixed at 100%); arousal-dependent has no task-weight parameter, so its
grid instead sweeps task-responsive cells % x task cells carried over A→B,
faceted by place cells %. All three models share **one color scale**
(reversed from the accuracy/R² heatmaps elsewhere in this pipeline, so low
error still reads as the same "good" color).

**All three models' sweeps are now complete.** independent_sweep_092926
finished 2026-10-03 (216/216 grid points), matching place_dependent and
arousal_mediated's own complete sweeps.

Each block's header reports the fraction of that model's grid points where
A→B error clears its shuffled floor: the real score's 95% CI (across the
combo's iterations) sits entirely below the shuffled floor's own CI -- the
same per-point significance test `robustness`/`robustness_3d` use for task
decoding, applied on the lower-is-better side for this metric.
