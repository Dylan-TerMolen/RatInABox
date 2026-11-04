# Figure review: typos, inconsistencies, minor changes (builds as of 2026-10-03)

Text and style only. Bigger content items (missing models, splits, empty panels) are in the earlier reviews and are only noted here where they touch wording. Written so it can go straight to Claude Code; per CLAUDE.md, put each label change in `style.py` / shared helpers so it propagates.

## A. Fix everywhere (one change each)

| # | Issue | Where | Change to |
|---|---|---|---|
| A1 | ASCII arrow "A->B" | Colorbar labels in S1 (`robustness`) and S2 (`robustness_3d`) | "A→B" |
| A2 | Three ways of writing chance: "chance=0.2", "Chance (0.2)", "chance = 0.2" | S1, S2 colorbars and titles; Fig 4, S5–S7 legends | "Chance (0.2)" in legends; "chance = 0.2" in labels |
| A3 | "Place decoding" vs "Position decoding" | S8 title says "Place decoding"; S3/S4 say "Position decoding" | "Position decoding" everywhere |
| A4 | "Within-env" / "Cross-env" vs "Within-environment" / "Cross-environment" | Fig 3 titles vs Fig 4, S7 | "Within-environment" / "Cross-environment" |
| A5 | Lowercase "in-task" / "out-of-task" in legends vs "In-task" / "Out-of-task" in titles | Fig 3 legends vs S8 titles | Sentence case in both: "In task" / "Out of task" (no hyphens when used as a label) |
| A6 | "env A" vs "Env A" | Fig 5 legends | "Env A" / "Env B" |
| A7 | Internal name "bioreal (20%)" | S5, S6 legends | "Main-text setting (20%)" |
| A8 | Facet titles "Place cells (%) = 20" | S1–S4 | "20% place cells" |
| A9 | "above chance" vs "below shuffled floor" in block titles | S1/S2 vs S3/S4 | Pick one framing: "better than shuffled at N% of grid points" for both |
| A10 | Hyphens used for ranges: "0-250 ms", "850-2000 ms" | Fig 1c legend | En dash: "0–250 ms" |
| A11 | Lowercase axis label "normalized firing rate" | Fig 1g colorbars | "Normalized firing rate" (match "Firing rate (Hz)") |
| A12 | Error bars never defined | Figs 3, 4, 5, S5–S8 | Same definition in every caption (e.g. "mean ± 95% CI over n iterations") |

## B. Per figure

### Figure 1 (`setup`): not rebuilt since 09-25
- Panel letters run a, b, c, f, d, g, e, and the env-B field-centre panel and the env-B example-field row have no letter.
- **No panel says which environment it shows.** Add "Env A (rectangle)" / "Env B (oval)" column headers.
- **Legend wording differs between panels:** a says "CS (tone)", "trace interval", "US (eyelid shock)"; c says "tone", "trace", "shock". Use the same three terms in both.
- c: "post (850–2000 ms)" → "Inter-trial".
- b: two identical time colorbars → one shared. Env A panel is drawn smaller than env B.
- d (coverage heatmap) has no colorbar, so the blue scale has no meaning. Add "Summed field rate (a.u.)" or similar.
- g: two identical colorbars → one shared; env-A tiles have a double border, env-B tiles don't.
- e (remapping): the colored circles have no key. Add "Cell 1–3".
- a: empty y-axis; hide it.

### Figure 2 (`models`)
- **"Running/Sitting" vs the draft's "moving/not moving".** The Results text uses moving/not moving; pick one term for both text and figure.
- **"Within place field" vs "In field".** Panel e titles say "Within place field, Running"; panel f says "In field, running"; panels c/d legends say "in field". Use "In field" / "Out of field" everywhere, same capitalization.
- f: "in field (n=17 trials)" for IM/PDM vs "In field, running (n=14)" for ADM → add "trials" to ADM (or drop it everywhere).
- b title "Raw task response per type (no place-firing combination)" → "Task-response types, before place modulation".
- a: "→ at ANY location" / "→ ONLY inside field" all-caps → normal case or italics.
- d: PDM out-of-field line still sits on the x-axis, invisible (content item, unchanged).

### Figure 3 (`position_decoding`)
- Titles "Within-env" / "Cross-env" (A4); legend "in-task" / "out-of-task" (A5).
- The same legend is drawn twice. Use one shared legend above both panels.
- **Metric changed from R² to cm error** since the last build. The cross-environment cm error isn't directly comparable to within-env because env B is smaller (see earlier note), so add the shuffled A→B reference line, or switch this one panel back to R².
- Possible content flag: cross-env in-task error (≈24 cm) is lower than out-of-task (≈31 cm). Worth a sentence in the caption, or a check.

### Figure 4 (`task_decoding`)
- Suptitle "Independent (IM) only" and single-entry legends remain (content item; remove once PDM/ADM are added).

### Figure 5 (`mechanism`)
- "env A"/"env B" (A6); env colors still clash with model colors.
- The same legend appears in three panels. One shared legend is enough.
- Stability-panel tick labels are full model names, rotated and crowded. Use "IM", "PDM", "ADM", since the other panels' titles already spell them out.
- No panel letters.

### Supplementary Figure 1 (`robustness`)
- Colorbar "A->B" (A1), "chance=0.2" (A2), facet titles (A8).

### Supplementary Figure 2 (`robustness_3d`)
- The colorbar label is clipped at the right edge ("…stage decoding accuracy…"); widen the margin.
- Block title uses a colon ("Independent (IM): Task-stage decoding…") where S1 uses an em dash ("Independent (IM) — above chance…"). Match S1.

### Supplementary Figures 3–4 (`place_robustness_3d_within` / `_cross`)
- IM block is now present but **partial (164/216 grid points)**. The 0% place-cell facet is missing, leaving an empty sixth slot. The block title is orange and adds "[PARTIAL SWEEP: 164/216 grid points]". Fine as a working flag, but before submission either finish the sweep or move the note to the caption and use the normal title color.
- Titles are very long: "Position decoding error (A→A, out of task, cm, lower = better) — below shuffled floor at 99% of 164 grid points". Suggest "IM: position decoding error (A→A, out of task)" in the title, with "lower is better" and the fraction moved to the colorbar and caption.
- The vertical axis is labeled "Error (cm)" while the colorbar says "Position decoding error (…, cm, lower = better)". One label is enough.
- S4: cross-environment cm error has the env-size comparability problem (see Figure 3).

### Supplementary Figures 5–6 (`supp_place_pct`, `_all_models`)
- "bioreal (20%)" (A7). The dashed 20% line is drawn on top of the error bar at 20%; put the line behind the data (lower zorder).
- S5 is S6 without ADM. Drop S5.

### Supplementary Figures 7–8 (decoding summaries)
- S8 title "Place decoding…" (A3).
- Suptitles say "across each model's completed parameter sweep"; "averaged over each model's parameter sweep" is clearer. IM is still missing.
- Same legend repeated in both panels of each figure.

## C. Duplicates to resolve (unchanged)

S1/S2 (same data, heatmap vs 3D) and S5/S6 (S6 is a superset). Keeping S1 and S6 removes two figures.
