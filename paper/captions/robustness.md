**Supplementary Figure 1. IM's cross-environment advantage isn't one lucky
parameter choice.** Task-stage decoding accuracy (chance = 0.20; KNN
classifier over 5 CS/US bins, not R²) for A→B across each model's own swept
parameter grid (most recent completed sweep per model as of 2026-09-25; see
Methods for tags), drawn as 2D heatmaps sharing **one color scale across all
three models** -- IM and PDM share axes (task weight x task-responsive
cells %, faceted by place cells %, task cells carried over A→B fixed at
100%). Arousal-dependent has no task-weight parameter at all -- the model
doesn't use it -- so its grid instead sweeps task-responsive cells % x task
cells carried over A→B, faceted by place cells %.

The shared color scale matters: IM's accuracy spans 0.2-0.62 across its grid,
while PDM's and ADM's span only 0.19-0.27 -- close to chance everywhere. An
earlier version of this figure gave each model its own color scale, which
stretched PDM/ADM's narrow near-chance range to fill the same visual range as
IM's, making them look comparably strong. They are not.

Each row's subtitle reports the fraction of that model's grid points where
A→B decoding is above chance: the real score's 95% CI (across the combo's
iterations) doesn't overlap its paired shuffled floor's CI. This is a
per-point significance test, not a comparison to the empirical benchmark from
ref 19 (that value is still an open question, so no benchmark line is drawn
yet) -- a grid point can be statistically above chance while still far below
what the source study reports as real decoding performance. IM clears this
bar at {{stat.robustness.independent.above_chance_pct}}% of its grid; PDM and
ADM, whose accuracy sits close to their own shuffled floors across almost the
entire grid, clear it at only
{{stat.robustness.place_dependent.above_chance_pct}}% and
{{stat.robustness.arousal_mediated.above_chance_pct}}% respectively.
