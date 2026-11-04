# Figure review: d1 figures (builds from 2026-09-25 18:25)

This review is written so it can be handed to Claude Code. Items are ordered by importance within each figure. Keep to the CLAUDE.md rules: no seeding, one figure at a time, and don't touch the manuscript.

---

## Problems that affect more than one figure (fix these first)

1. **Task decoding is labeled "R²" but looks like classification accuracy.** Every shuffled score sits at about 0.20, which is 1/5, the chance level for the 5 CS/US time bins (`CS_US_NUM_BINS = 5`). The decoder is a KNN *classifier*. Check what `cond_decoding_AvsB` returns. If it's accuracy, relabel it everywhere as "Task-stage decoding accuracy (chance = 0.2)". This affects Figure 4, Supplementary Figure 1 and Supplementary Figure 2.
2. **Position error is labeled "cm" but the values are 0.16–0.26.** In a 0.95 m × 0.55 m arena, an error of 0.2 cm isn't plausible. The values are almost certainly metres (16–26 cm). Fix the unit or convert to cm (Figure 3).
3. **Remove internal names from all titles:** `tag=bioreal-take-3`, `tag=independent_sweep_080726`, "averaged over holdover", "CI non-overlap vs. shuffled", and raw variable names like `percent_task_in_response`. Put this information in the caption instead. Suggested display names:
   - `percent_task_in_response` → "Task weight (balance)"
   - `percent_task_responsive_cells` → "Task-responsive cells (%)"
   - `percent_place_cells` → "Place cells (%)", with tick labels 0, 20, 40 … rather than 0.2
   - `holdover` → "Task cells carried over A→B (%)"
   - `A->B`, `shuffA->A` → "A→B", "Shuffled A→A"
   - `TRIAL_PERIOD` → "Response reset (1.5 s)"
4. **Show a chance line on every decoding plot**, either a dashed line at the shuffled mean or at 0.2 for task decoding. Say in each caption what the error bars show (95% CI or SEM, and n = iterations).
5. **Keep color meanings the same across figures.** Blue/orange/green mean IM/PDM/ADM in Figure 2, but Figure 5 uses blue/orange for env A/env B. Give the environments their own encoding, for example solid black for A and dashed grey for B, or a separate pair of colors from `style.py`.
6. **Use one naming convention.** Use "Env A (rectangle)" and "Env B (oval)" everywhere, and capitalize consistently ("In field" vs "in field" currently both appear in Figure 2).

---

## Figure 1: `setup` (353 mm tall, split still pending)

- **Too tall.** Do the split already requested: Figure 1 keeps panels a–e; field centres and example fields move to `supp_place_fields`.
- **Panel letters are out of order** (a, b, c, f, d, g, e). The env-B field-centre panel and the env-B example-field row have no letter.
- **Trial-phase colors changed** to shades of viridis: tone purple, trace teal, shock lime. Teal and lime are hard to tell apart and this drops the colorblind-safe `PHASE_COLORS` palette. Revert, or run the new palette through the palette validator.
- **The "post (850–2000 ms)" label is wrong:** that gray layer is all time between trials. Relabel it "Inter-trial".
- **Panel a (schematic) is sparse.** It has an empty y-axis and no labels on the bands. Suggested additions:
  - "CS / trace / US" written on the bands
  - a second strip showing the session structure: "50 trials per environment, inter-trial interval 30–60 s" (both from the Results text)
- **Panel b has two identical time colorbars.** Use one shared colorbar.
- **Panel e (remapping) needs a key.** Add "cell 1–4" (or number the circles) and a title such as "Same four cells: field in env A vs env B".
- **Title suggestions:**
  - a "Trace eyeblink conditioning trial"
  - b "Trajectories, colored by session time"
  - c "Trajectories, colored by trial phase"
  - d "Place-field coverage (20% place cells)"
  - e "Complete remapping between environments"

## Figure 2: `models` (553 mm tall)

- **Too tall to read on a page.** Suggested split:
  - Figure 2: panels a–e (model definitions and response profiles)
  - Rasters (f) to a supplementary figure, or into Figure 5, which is about single-cell behaviour
- **Panel e, ADM out of field + running: firing rate goes negative** (down to −0.04 Hz). Clip at 0, or fix the noise term.
- **Panel e y-axes are misleading.** "Within field, running" starts its axis at 12 Hz, so a roughly 1.8 Hz bump looks large. The out-of-field panels span 0–0.04 Hz and 0–0.4 Hz. Start every axis at 0, or share the y-axis within each row and add an inset for the small traces.
- **Panel d, PDM out of field: the red line sits on the x-axis and can't be seen.** Draw it dashed, or add an annotation "no task response outside the field".
- **Panel f, ADM rasters:** "In field, sitting" has n = 1 trial and "Out of field, sitting" has n = 0, so two of the four panels are empty. Pick an example cell with sitting trials, or pool across cells in each state. If neither works, drop the sitting column and say in the caption that the animal almost always runs at CS onset.
- **Panel b:** types 3 and 8 jump straight back to baseline at exactly 1.5 s. Check that this step reset is intended and not an artifact.
- **Title suggestions:**
  - a: keep the three model boxes, but add "Task response gated by:" as a header row (IM: nothing; PDM: place-field occupancy; ADM: occupancy × running)
  - b "Task-response types (1, 2, 3, 8), before place modulation"
  - c "IM: response by distance from place-field centre"
  - d "PDM: response by distance from place-field centre"
  - e "ADM: response by place-field occupancy × running"
  - f "Example cells, simulated spikes around CS onset"

## Figure 3: `position_decoding` (partial, IM only)

- **Unit problem** (see item 2 at the top).
- **Possible problem for the Results claim.** Within-environment position decoding is weak: in-task A→A R² falls from 0.2 to −0.33 as task weight increases, and out-of-task R² stays around 0.05–0.10. The Results say "place cell activity was sufficient to decode animal position". Check this against the shuffled floor before the text relies on it. The low values may come from the 20% place-cell setting.
- **Add PDM and ADM, B→B and B→A, a shuffled floor, and a marker at the `bioreal` task weight.**
- **Title suggestions:**
  - a "Position decoding within an environment (A→A)"
  - b "Position decoding across environments (A→B)"
  - Suptitle: drop it, and name the model in the legend or caption.

## Figure 4: `task_decoding` (partial, IM only)

- **Metric label** (see item 1 at the top).
- **Add PDM and ADM side by side** (grouped bars by model), plus B→A and the empirical benchmark from ref 19 as a horizontal line. This is the paper's key result figure, so it should show all three models in one panel.
- **The single-entry legends** ("Independent (IM)") aren't needed once the model is on the x-axis or in the group label.
- **Title suggestions:**
  - a "Task-stage decoding within an environment"
  - b "Task-stage decoding across environments (train A → test B)"

## Figure 5: `mechanism`

- **No panel letters, and default matplotlib colors.** Use `style.py`, and see item 5 at the top for the env A/B encoding.
- **Say what's plotted.** The title should read something like "One task-responsive cell, trial-averaged firing: env A vs env B". Say whether the shaded bands are 95% CI or SEM. Label the CS/trace/US shading, or reuse the Figure 1 phase key.
- **Very jagged traces** (roughly 33 ms bins). Smooth them (e.g. a 100 ms Gaussian) or bin at 50–100 ms so the A-vs-B comparison is readable.
- **Y-axes differ across models** (0–15 Hz vs 0–4 Hz vs 0–5 Hz). Either share them or state this clearly in the caption.
- **Add a population-level stability panel.** The draft itself asks for a quantitative stability measure: a per-model distribution of the A-vs-B correlation of each task cell's trial-averaged response. One example cell per model is anecdotal; this panel would carry the claim.

## Supplementary Figure 1: `robustness` (449 mm tall)

- **Replace the 3D surfaces with 2D heatmaps.** Nine small 3D plots per model can't be read at print size. Use one heatmap per model and place-cell level, with a shared color scale across all three models. At the moment each model has its own scale (IM 0.2–0.62, PDM 0.19–0.27, ADM 0.19–0.24), so PDM and ADM look far better than they are. Mark above-chance cells with a dot or contour.
- **ADM uses different axes** (task-responsive % × holdover) from IM/PDM (task weight × task-responsive %). Say why in the caption, or align the axes.
- **The `above_chance_fraction_summary` panel listed in the manifest is missing.** The fractions (80% / 21% / 9%) only appear in the titles. Make that a small bar chart as its own panel. It's the headline number for this figure.
- **Title suggestion:** "Cross-environment task decoding across parameter space", with the model name as the row label.

## Supplementary Figure 2: `supp_place_pct`

- **ADM is missing.**
- **Add a chance line at 0.2.** PDM sits on it across the whole range, which is the point and should be visible.
- **Titles:** "Task weight = 0.4" / "Task weight = 0.6"; x-axis "Place cells (%)"; y-axis per item 1 at the top.

---

## Possible additions (need a decision from the authors)

- A **summary figure or table comparing the models**, which the draft already asks for ("Prob also want a model comparison table"). One row per model: assumptions, within-env decoding, cross-env decoding, stability.
- **B→A decoding**, which the Results text reports but the pipeline doesn't compute yet.
- **A single-panel "key result" graphic** for the abstract: cross-environment decoding accuracy for IM vs PDM vs ADM, with the chance line and the empirical benchmark.
