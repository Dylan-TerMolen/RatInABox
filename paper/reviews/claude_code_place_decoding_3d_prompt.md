Add 3D parameter-sweep figures for **place (position) decoding**, matching the existing `robustness_3d` figure for task decoding. Follow CLAUDE.md: no seeding, one figure at a time, and don't touch the manuscript. The new figures only read the sweep logs that `robustness` and `robustness_3d` already use, so no new runs are needed.

## What to build

Mirror `paper/figures/robustness_3d.py` exactly, but plot place-decoding metrics instead of task accuracy:

- Same three sweeps: `independent_sweep_080726`, `place_dependent_sweep_080726`, `arousal_mediated_sweep_081426`.
- Same layout: one block per model (IM, PDM, ADM), with six facets per block, one for each place-cell percentage (0, 20, 40, 60, 80, 100%).
- Same axes per model. IM/PDM: task weight (balance) × task-responsive cells (%). ADM: task-responsive cells (%) × task cells carried over A→B (%).
- The vertical axis and color scale are the place metric, **shared across all three models** (the same fix already applied to `robustness_3d`).

The logs already contain everything needed. Each iteration has `place_r2_in_task`, `place_cm_in_task`, `place_r2_out_of_task` and `place_cm_out_of_task`, each with A→A, B→B, A→B, shuffled A→A and shuffled A→B.

## Figures (add as separate manifest entries, all `kind: supplementary`, right after `robustness_3d`)

1. **`place_robustness_3d_within`**: within-environment position decoding (A→A).
2. **`place_robustness_3d_cross`**: cross-environment position decoding (A→B).

Defaults for both:
- **Metric: R².** Use R², not cm error. R² is normalized to each environment's own spread of positions, so A→A and A→B can be compared fairly. Env B is smaller than env A, so raw cm errors in B are smaller by default, and the shuffled A→B error (about 21–24 cm) is lower than the real A→B error (about 30 cm) in `decoding_place_summary`.
- **Data: out-of-task samples.** Out-of-task (moving, between trials) is the clean spatial readout. Render the in-task version too, as `..._in_task`, but add it to the manifest only if I say so.
- **Reference plane:** draw a translucent horizontal plane at the mean shuffled value for that direction (shuffled A→A or shuffled A→B), the way chance = 0.2 works for task decoding. Mark grid points whose CI doesn't overlap the shuffled CI (same rule as the task figures), and put the fraction above shuffle in each model's block title, as in `robustness_3d`.
- **Axis label:** "Position decoding R² (A→A, out of task)" or "(A→B, out of task)", using a real → arrow, not "->".

Make the metric (R² or cm error) and the task state (in-task or out-of-task) arguments to one shared panel function, so switching later is a one-line change. If cm error is used, label it "Mean position error (cm, lower = better)" and invert the colormap, so better is always the same color.

## Fix while you're in there (applies to `robustness_3d` too)

- The long vertical-axis label collides with the "Task-responsive cells (%)" and "Task cells carried over A→B (%)" labels on every facet. Shorten it (e.g. "Accuracy" / "R²") and put the full metric name on the shared colorbar and in the block title.
- `robustness_3d` renders 449 mm tall. If one figure per metric is still taller than about 230 mm at 183 mm wide, split it by model into separate panels in `build/panels/` and say so; don't shrink the text.

## When done

Run `python -m paper.build place_robustness_3d_within --check` and `python -m paper.build place_robustness_3d_cross --check`. Report:
- each figure's rendered height
- the "fraction above shuffle" for each model
- anything surprising, e.g. whether within-environment R² is near 0 at the main-text setting (20% place cells). The current Figure 3 suggests it might be.
