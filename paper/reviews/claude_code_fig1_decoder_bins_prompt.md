Add a new panel to Figure 1 (`setup`), placed directly after the tEBC schematic (current panel a) and before the trajectory grid (current b). Follow CLAUDE.md: no seeding, one figure at a time, don't touch the manuscript.

## What the panel shows

The 5 time bins the task decoder predicts, overlaid on the same CS / trace / US timeline as panel a, so a reader can see exactly which part of the trial each decoded class covers.

- Bins: the decoder is a KNN classifier over `CS_US_NUM_BINS = 5` (`ratinabox/hsw/simulation_helpers.py`). `bin_cs_us_time_ids` pairs trial markers 1–10 (1–5 = CS-side time ids, 6–10 = US-side) into bins 1–5 via `ceil(marker / 2)`. Chance is 1/5 (`TASK_CHANCE_LEVEL` in `figlib/style.py`).
- **Derive each bin's start/end in ms from the trial-marker column in the real position data** (time relative to CS onset where each marker begins and ends), averaged over trials. Do not assume equal widths or hard-code times. Report the edges you find, and say if they vary across trials or animals.
- Drawing: reuse panel a's timeline and x-axis (same time scale and alignment, so the two panels line up vertically). Draw the 5 bins as adjacent shaded bands or brackets labeled "Bin 1" … "Bin 5" (or 1–5 with a small key), with the CS / trace / US boundaries still visible underneath. Use a palette that is distinct from both the phase colors and the model colors.
- Inter-trial time is not a decoded class. If it's shown at all, make it unlabeled gray, consistent with the trajectory panels.

## Lettering

The new panel becomes **b**. Re-letter the rest: trajectories b→c, place coverage c→d, example fields d→e. Update `panels:` in manifest.yaml (add e.g. `decoder_time_bins` right after `schematic`) and the caption template `captions/setup.md`.

## When done

Run `python -m paper.build setup --check`. Report:
- the bin edges in ms
- the new rendered height of Figure 1 (it was 275 mm at 183 mm wide; the one-page limit is about 203 mm)
