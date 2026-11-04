**Figure. Task-stage decoding accuracy at bioreal's percentages (20% place
cells, 40% task-responsive cells), all 3 models overlaid on one axis per
direction (within-environment, left; cross-environment, right).** IM/PDM
plotted as a function of task weight (balance) -- the actual values across
the swept range, not folded into one aggregate number. arousal-dependent has
no balance parameter at all, and its only remaining swept axis (holdover)
isn't a comparable x-axis to balance -- a different parameter with no shared
scale or meaning -- so it's drawn instead as a horizontal reference band
(mean +/- 95% CI) spanning the panel: **the single real grid point at
holdover = 100%** (bioreal's own chosen holdover value,
paper/params/bioreal.yaml), matching IM/PDM's own fixed holdover=1.0, not an
aggregate across holdover. KNN classifier over 5 CS/US bins, chance = 1/5 =
0.20 (dotted black line). Each model's own dotted line (in that model's
color) is its empirical shuffled baseline (`shuffled_reference_value`,
computed at the same fixed point as its real value(s)). Mean +/- 95% CI
across iterations. **Both panels share one y-axis range, pinned to start at
0**, so accuracy is directly comparable across models and directions.

IM's within-env accuracy (~0.60-0.65) and cross-env accuracy (~0.45-0.65)
are both fairly flat across the balance range. PDM sits close to chance and
its own shuffled floor across the entire balance range on both panels. ADM's
single point (holdover=100%) sits in the same near-chance range, consistent
with PDM -- though since it's one point, not a line, this figure can't say
whether that holds evenly across ADM's own holdover range the way it can for
PDM across balance; see `task_decoding_within`/`task_decoding_within_3d` for
the per-grid-point view that answers that for the within-env direction.
