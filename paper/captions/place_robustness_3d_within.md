**Supplementary Figure. Within-environment position decoding (A→A) over each
model's own swept parameter grid, out-of-task.** Mean position-decoding error
in centimeters (**lower is better**; R² is not plotted anywhere in this
pipeline as of 2026-10-02) for A→A, out-of-task samples only
(independent_sweep_092926, place_dependent_sweep_092926,
arousal_mediated_sweep_092926 -- IM/PDM share axes: task weight x
task-responsive cells %, faceted by place cells %; arousal-dependent instead
sweeps task-responsive cells % x task cells carried over A→B %, since it has
no task-weight parameter). All three models share one z-scale and color
scale (`metric_range`); the colormap is reversed from the accuracy/R² figures
elsewhere in this pipeline so low error still reads as the same "good" color.

**All three models' sweeps are now complete.** independent_sweep_092926
finished 2026-10-03 (216/216 grid points), matching place_dependent and
arousal_mediated's own complete 216/216 sweeps. Earlier (2026-10-02)
independent had no sweep with this split at all (independent_sweep_080726
predates it entirely) and rendered as an explicit "data not available"
placeholder instead; that code path still exists for any future tag that
genuinely lacks this kind, it just isn't exercised here anymore.

The translucent gray plane marks each model's mean shuffled-control error
for A→A -- the empirical chance floor. Grid points ringed in black clear
that floor: their real-direction 95% CI (across the combo's iterations) is
entirely below the shuffled floor's own CI, the same CI-non-overlap test
`robustness`/`robustness_3d` use for task decoding, applied on the
lower-is-better side for this metric. Each block's title reports the
fraction of its grid that clears this bar.

In-task position decoding (contaminated by CS/trace/US trial structure) is
not shown here -- see `decoding_place_summary` for the cm-error, in-task vs.
out-of-task comparison at the sweep-wide aggregate level.
