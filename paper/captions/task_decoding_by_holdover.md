**Supplementary Figure. Cross-environment (A→B) task-stage decoding accuracy
across holdover (%), all three models on one shared panel.** Task cells
carried over A→B, bioreal's fixed percentages (20% place cells, 40%
task-responsive cells). Cross-environment only -- holdover is a
cross-environment carryover parameter and has no within-environment effect
(confirmed in an earlier two-panel version of this figure: IM's
within-environment accuracy was flat across the whole holdover range while
its cross-environment accuracy, shown here, rose steadily with it). IM/PDM:
dedicated single-axis holdover sweeps at this fixed point (11 values, 0–100%
in steps of 10%; `slurm/independent_holdover_sweep.sh`,
`slurm/place_dependent_holdover_sweep.sh`). ADM: sliced from its existing
parameter-grid sweep at the same fixed point (6 values, 0–100% in steps of
20%) -- a coarser but real sweep of the same parameter, not an aggregate or a
single point. KNN classifier over 5 CS/US bins, chance = 1/5 = 0.20 (dotted
black line). Mean +/- 95% CI across iterations. Dashed vertical line marks
bioreal's chosen holdover = 100%.

**Holdover drives IM's cross-environment transfer specifically.** IM's
accuracy rises steadily with holdover, from ~0.29 (near chance) at holdover =
0% to ~0.58 at holdover = 100%: the fraction of task cells carried from env A
into env B is what lets a decoder trained on A transfer to B. PDM and ADM sit
on the chance line across the entire holdover range -- neither model's
cross-environment task-stage accuracy depends on holdover at all, consistent
with `task_decoding_by_balance`'s finding that both are near chance
regardless of which axis is swept.
