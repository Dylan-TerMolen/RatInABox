# Follow-up review: were the 2026-09-29 comments addressed?

Checked against the builds from 2026-09-29 23:43 (Figure 1 was not rebuilt; it's still the 09-25 18:24 render).
Legend: ✅ done · ◐ partly done · ❌ not done

## Problems that affect more than one figure

| # | Comment | Status |
|---|---|---|
| 1 | Task "R²" is really accuracy | ✅ Relabeled "Task-stage decoding accuracy" in Figure 4, Supplementary Figure 1 and Supplementary Figure 2 |
| 2 | Position error unit (cm vs m) | ✅ Values now 16–26 cm |
| 3 | Remove internal tags and variable names | ◐ Mostly done. Remaining: Figure 4 suptitle "Independent (IM) only"; Supplementary Figure 1 colorbar reads "(A->B, chance=0.2)" with an ASCII arrow; Supplementary Figure 2 legend says "bioreal (20%)" (use "Main-text setting (20%)"); Figure 2 panel b title "Raw task response per type (no place-firing combination)" |
| 4 | Chance line and error-bar definition | ◐ Chance line added in Figures 4 and S2. Figure 3 still has no shuffled floor. Error bars aren't defined in any figure yet (caption item) |
| 5 | Keep env A/B colors distinct from model colors | ❌ Figure 5 still uses blue/orange for env A/B, which is the same blue/orange as IM/PDM in the new stability panel right beside it |
| 6 | Consistent naming and capitalization | ❌ Figure 2 still mixes "in field" and "In field" |

## Figure 1: `setup` (not rebuilt)

❌ Nothing has changed: no split, letters still out of order (a, b, c, f, d, g, e), teal/lime phase colors, "post (850–2000 ms)" label, sparse schematic, duplicate colorbars. Still 353 mm tall.

## Figure 2: `models`

- ✅ Panel e: no more negative firing rate; y-axes now start at 0.
- ✅ Legend now reads "Response reset (1.5 s)".
- ❌ Still 553 mm tall; not split.
- ❌ Panel d, PDM out-of-field line still invisible on the x-axis.
- ❌ Panel f, ADM rasters still show n = 1 and n = 0 in the sitting column.
- ❌ Panel titles unchanged.

## Figure 3: `position_decoding` (partial)

- ✅ Units fixed (cm); x-axis now "Task weight (balance)"; suptitle removed.
- ❌ Still IM only; no B→B/B→A; no shuffled floor; no marker at the main-text task weight. Legends sit outside the axes and take up half the width. Put one shared legend at the top.
- ⚠ **Scientific point still open:** in-task A→A R² is negative from task weight 0.4 upward, and out-of-task stays at about 0.1. With error 17–25 cm in a 95 × 55 cm arena, position decoding is weak. The Results text needs to match what this shows (or the place-cell/decoder settings need a look).

## Figure 4: `task_decoding` (partial)

- ✅ Metric relabeled; chance line at 0.2; arrows fixed.
- ❌ Still IM only. This is the headline figure and needs PDM and ADM side by side, plus B→A and the ref-19 benchmark line.
- ❌ The "Independent (IM) only" suptitle and single-entry legends are still there.

## Figure 5: `mechanism`

- ✅ **Population stability panel added.** It clearly shows IM r ≈ 0.88 vs PDM ≈ −0.03 and ADM ≈ 0.0, which is the strongest visual in the set so far.
- ❌ Env A/B colors clash with the model colors (see item 5 at the top). Use black/grey solid/dashed for the environments.
- ❌ No panel letters; traces still jagged (not smoothed or rebinned); shaded bands not defined.
- Minor: the stability panel shows only 2–3 points per model. Say n in the caption, and consider more iterations.

## Supplementary Figure 1: `robustness`

- ✅ **Rebuilt as 2D heatmaps with values and a shared color scale** (0.2–0.7). PDM and ADM are now correctly shown as near chance.
- ✅ Axis labels are readable ("Place cells (%)", "Task cells carried over A→B (%)").
- ◐ Height is down from 449 to 379 mm, but that's still nearly twice one page.
- ❌ Above-chance cells aren't marked. The `above_chance_fraction_summary` panel is still missing: the 80% / 21% / 9% only appear in the titles.
- ❌ Why ADM uses different axes still needs a line in the caption.
- Note: "PDM above chance at 21%" rests on values of 0.21–0.28. Statistically above 0.2, but tiny. Worth saying in the text so a reviewer doesn't read 21% as meaningful generalization.

## Supplementary Figure 2: `supp_place_pct`

- ✅ Chance line, "Place cells (%)" axis, "Task weight (balance)" titles, accuracy label.
- ❌ ADM still missing.
- Minor: the "bioreal" wording; the vertical 20% line is drawn over the error bar at 20%.

---

## Still to do, in priority order

1. Figure 4: add PDM and ADM (plus B→A and the ref-19 benchmark). This is the paper's main result.
2. Figure 1 split and fixes (unchanged since the first review).
3. Figure 2 split, plus the PDM out-of-field line and the empty ADM rasters.
4. Figure 5: environment colors, panel letters, smoothing.
5. Figure 3: other models, shuffled floor, and a decision about weak within-env position decoding.
6. Supplementary Figure 1: above-chance markers and summary panel.
