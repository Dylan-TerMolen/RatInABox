**Figure 3. All models carry spatial information within an environment;
cross-environment position decoding fails for all three.** All three models
-- independent_sweep_092926, place_dependent_sweep_092926,
arousal_mediated_sweep_092926 -- restricted to bioreal's actual percentages
(20% place cells, 40% task-responsive cells); replaces the earlier bioreal-take-3
run, which predates the 2026-09-29 velocity-gain fix. IM/PDM shown as a
function of task weight (balance). arousal_mediated has no balance parameter
at all, and its only remaining swept axis at this fixed point (holdover) is
a different parameter with no shared scale or meaning against balance --
plotting it on the same kind of axis as IM/PDM's rows would imply a
comparability that isn't there. Its row instead shows **the single real grid
point at holdover = 100%** per task state (bioreal's own chosen holdover
value, paper/params/bioreal.yaml -- not an aggregate across holdover),
matching IM/PDM's own fixed holdover=1.0. Error
is mean position-decoding error in real centimeters (**lower is better**;
converted at ingestion from the decoder's raw meters-native output; mean
+/- 95% CI across iterations). R² is not plotted anywhere in this pipeline
as of 2026-10-02. **All 6 panels share one y-axis range** (2026-10-05) so
the error magnitudes are directly comparable across models and directions,
not just the shapes of the lines -- and the shuffled-baseline dashed lines
are now drawn on the within-env panels too (previously only the cross-env
panels had them).

**Model parameters:** 132 cells, 20% place cells, 40% task-responsive cells,
task types [1, 2, 3, 8]. n=3 iterations/point, sequential 75/25 decoder
split (from paper/params/bioreal.yaml).

**The balance-vs-aggregate choice still matters for IM.** In-task
within-environment error (A→A) rises from ~14cm at balance=0 to ~23cm at
balance=1.0: higher balance means more task-driven, less place-driven firing
for task-responsive cells, which directly degrades position decoding *during
task periods*. Out-of-task error stays comparatively flat, ~16-18cm across
the same range. A single aggregated bar across the whole balance sweep would
have averaged a working regime with a degraded one into a misleading net
number -- this is why task_decoding_by_balance.md's flat-across-balance
treatment isn't used here. **PDM is flat across balance and doesn't show
this tradeoff** -- sits around ~11-12cm in-task and ~17cm out-of-task
regardless of balance, consistently better than IM's within-env error
except at IM's own best point (balance=0). **ADM's single point
(holdover=100%) sits in the same range** (~12cm in-task, ~17cm out-of-task)
-- consistent with PDM's numbers, though this figure can't say whether that
holds evenly across ADM's own holdover range the way it can for PDM across
balance (that's the whole reason it's one point, not a line -- see
`task_decoding_within`/`task_decoding_within_3d` for the per-grid-point view
that does answer this, for the within-env task-decoding metric).

**The within-env shuffled baseline shows all three models genuinely decode
position, not just that their numbers look small.** IM's real within-env
error sits below its own shuffled floor across the balance range (clearly so
at low balance, closing in on it by balance=1.0, consistent with the
tradeoff above). PDM's real within-env error sits far below its shuffled
floor (~11-17cm real vs. ~24-28cm shuffled) across the entire balance range,
and ADM's single point does too (~12/17cm real vs. its own shuffled floor at
the same holdover=100% point) -- a much larger margin than IM's: whatever
lets PDM/ADM decode position so consistently well also decodes it far better
than chance, not just numerically small.

**Cross-environment** (A→B): substantially worse for all three models, both
in-task and out-of-task, than their respective within-environment numbers --
roughly flat across the x-axis for IM/PDM, and ADM's single point sits in
the same elevated range -- a real transfer failure, not a
balance/holdover-tunable one. The dotted shuffled-A→B baseline lines make
this starker still: every model's real cross-env error sits **above** its
own shuffled baseline -- not just "close to chance," genuinely worse than an
uninformative decoder. This holds for PDM and ADM too, despite their strong
within-env numbers -- position information that transfers cleanly within an
environment does not survive the A→B transfer for any of the three models,
the same failure mode IM shows, not one specific to it. With both panels now
on the same y-scale, this reads directly off the axis: every model's
cross-env values sit in the upper half of the shared range, its within-env
values in the lower half. B→A is not shown -- the decoder has no B→A output
yet (open question).

supp_position_with_task is folded into the within-env panels above (the
in-task/out-of-task split), not built as a separate figure, per the
2026-09-23 decision.
