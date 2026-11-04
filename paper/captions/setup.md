**Figure 1. Experimental setup.** Simulated trajectories and trial timing are
taken from empirically recorded rat position data ({{stat.setup.n_trials_per_env}}
trials per environment, pseudorandomly spaced 30-60 s apart), replayed through a
rectangular environment A and an oval environment B modeled on the source study's
enclosures.

**(a)** Trial structure: a 250 ms conditioned stimulus (CS, tone), a 500 ms trace
interval, and a 100 ms unconditioned stimulus (US, eyelid shock) beginning 750 ms
after CS onset, followed by a 30-60 s inter-trial interval before the next trial.

**(b)** The five time bins the task decoder classifies (chance = 1/5), on the
same timeline as (a). Bin edges are taken from the recorded trial markers and
averaged over all trials in both environments; dotted lines mark the tone,
trace and shock boundaries from (a). Bins span 0 to ~1.35 s after CS onset and
do not align with the trial phases.

**(c)** Example trajectory through env A (left) and env B (right): colored by
elapsed session time (top row), and the same trajectories colored by trial phase
(tone / trace / shock, bottom row) with the long inter-trial rest shown as
unlabeled background context.

**(d)** Place-field tiling in env A and env B at the model's biologically-plausible
parameter set ({{stat.bioreal.pct_place_cells}} place cells): each responsive
cell's field summed into one heatmap, with individual field boundaries (one
Gaussian SD) outlined and each env's own place-responsive count/percentage
annotated.

**(e)** Three individual example fields, env A and env B, chosen to be spatially
distinct and shown separately (not summed) to show real field shape and extent.

Panels (c)-(e) do not depend on which of the three models generated them (place
and trajectory content is shared); the independent model's simulation run was
used as the representative example.
