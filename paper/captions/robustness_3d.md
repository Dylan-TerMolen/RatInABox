**Supplementary Figure 2. IM's cross-environment advantage isn't one lucky
parameter choice (3D view).** The same grid as Supplementary Figure 1
(task-stage decoding accuracy, A→B, chance = 0.20), rendered as 3D surfaces
instead of 2D heatmaps, for readers who want the shape of the surface rather
than exact per-cell values. As in Supplementary Figure 1, all three models
share **one z/color scale** (computed across all three grids together) --
IM's accuracy spans 0.2-0.62, PDM's and ADM's span only 0.19-0.27, and giving
each its own scale would visually flatten that gap. IM and PDM share axes
(task weight x task-responsive cells %, faceted by place cells %, task cells
carried over A→B fixed at 100%); arousal-dependent has no task-weight
parameter, so its grid instead sweeps task-responsive cells % x task cells
carried over A→B, faceted by place cells %.

Each row's subtitle reports the fraction of that model's grid points where
A→B decoding is above chance (95% CI non-overlap vs. the paired shuffled
floor) -- the same test as Supplementary Figure 1. See that figure's caption
for the full above-chance percentages and the note on the empirical benchmark
(ref 19).
