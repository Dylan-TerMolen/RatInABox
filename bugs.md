# Bugs found while investigating the place_dependent B→B decoding regression

Context: investigating why `place_B->B` position decoding looks broken for the
`place_dependent` model in the `place_dependent_sweep_holdover_grid_at_point_3`
sweep (pinned at R² ≈ -0.17 across nearly the whole grid) while the sibling
`independent_sweep_holdover_grid_at_point_3` sweep is healthy. Root cause was
a population-wide spike-generation threshold (`FR_MAX`) that saturated
disproportionately for env B, combined with both envs sharing an identically
fixed place-field width despite B being the smaller environment — fixed
(switched to Poisson spike generation and env-area/density-scaled field
width) and confirmed by the user end-to-end (2026-08-10); see "Open
questions" at the bottom for what's still unresolved. Several other real,
independent bugs turned up along the way, including two (#6, #7) found while
implementing that fix.

**Status as of 2026-08-10:** bugs #6 and #7 are implemented in the working
tree but not yet committed (`git status` shows `combined_place_tebc.py`,
`main.py`, `simulate_envs.py`, `utils.py`, and both test files as staged
modifications). Everything else in this file describes already-committed code.

## Confirmed bugs

### 1. Position decoder silently keeps only 1 of its 2 CEBRA repetitions
**Repo:** Hannahs-CEBRAs
**File:** `pos_decoding_AvsB_DEP.py`, lines 73-76 (init) and 134-146 (loop body), inside `pos_decoding_AvsB_dep`

`NUM_POS_DECODING_REPS = 2` fits CEBRA twice per call (fresh random init each
time) so the two runs can be averaged out and CEBRA's training stochasticity
smoothed over. But every metric (`place_a_to_a`, `place_a_to_b`,
`place_shuffled_a_to_a`, `place_shuffled_a_to_b`, `place_b_to_b`) is built with
a plain `=` assignment inside the `for i in range(NUM_POS_DECODING_REPS)` loop,
not an append/accumulate. Each iteration **overwrites** the previous one, so
after the loop only rep 2's fit survives — rep 1's full CEBRA training run (and
its score) is computed and then silently discarded. The `place_a_to_a = [] * 4`
style init lines (73-76) are dead — `[] * 4` is just `[]`, a leftover from what
looks like an earlier, different accumulation approach.

**Effect:** every score this decoder reports (`A->A`, `A->B`, `B->B`, both
shuffled) is "whichever one of two independent random CEBRA fits happened to
run last," not an average — 2x the compute is spent, but with zero variance
reduction. A run that happens to land its *last* rep in a bad/degenerate local
optimum reports that failure at full strength instead of it getting diluted by
a good rep.

**Fix:** change lines 73-76 to real list accumulators and lines 134-146 to
`.append(...)`, then return `np.mean(...)` (or the full list) per metric, the
way `cond_decoding_AvsB.py` already does for task decoding.

### 2. Task decoder's second repetition is discarded on the RatInABox side
**Repo:** RatInABox
**File:** `ratinabox/hsw/simulation_helpers.py:188-190` (`unwrap_scalar`), consumed at `ratinabox/hsw/main.py:110`

`cond_decoding_AvsB.py` (Hannahs-CEBRAs) does the accumulation correctly —
`task_b_to_b.append(b_to_b)` builds a real 2-element list across its two reps.
But `main.py:110` calls `task_b_to_b = unwrap_scalar(task_b_to_b)`, and
`unwrap_scalar` returns `value[0]` for a list — keeping rep 1 and discarding
rep 2. Same underlying symptom as bug #1 (only one of two CEBRA fits ever gets
used), just introduced on the opposite side of the repo boundary and via a
different mechanism (index `[0]` instead of loop-overwrite).

**Fix:** either change `unwrap_scalar` to average list-valued metrics instead
of indexing `[0]`, or average the list explicitly in `main.py` before logging.

### 3. `getattr` fallback reads a nonexistent attribute
**Repo:** RatInABox
**File:** `ratinabox/hsw/simulate_envs.py:70`

```python
percent_task_in_response_distribution_B = getattr(modelA, 'percent_task_in_response_distribution', percent_task_in_response_distribution)
```

`modelA` has no attribute named `percent_task_in_response_distribution` — it's
stored as `self.task_to_place_weight_distribution`
(`ratinabox/hsw/combined_place_tebc.py:47`). So this line always silently
falls through to the default (env A's originally-computed distribution) rather
than actually reading env A's *realized* balance array off the model.

**Effect:** currently inert — every sweep run so far has used
`percent_task_in_response_dist='fixed'`, where the fresh-draw fallback and the
(intended, broken) getattr path are numerically identical constants anyway.
But it would silently break the "carry env A's balance array into B" part of
holdover for `gaussian`/`normal` distributions.

**Fix:** store the distribution under a matching attribute name on the model
(or just thread it through `simulate_experiment`'s own local variable instead
of round-tripping through `modelA`).

### 4. Holdover's random draws silently reshuffle env B's place-field layout
**Repo:** RatInABox
**Files:** `ratinabox/hsw/independent_model/assign_tebc_types_and_responsiveness.py` (`holdover_task_responsiveness`, uses `np.random.choice`) and `ratinabox/Environment.py` (`sample_positions`, uses `np.random.uniform`), wired together via `ratinabox/hsw/simulate_envs.py:64-75`

`holdover_task_responsiveness` runs *before* `agentB`/`modelB` are built, and
consumes a `holdover_fraction`-dependent number of `np.random.choice` calls.
`_distribute_place_centres` → `Environment.sample_positions(method="uniform_jitter")`
draws env B's place-field centers from `np.random.uniform` immediately after —
the *same* global NumPy RNG stream. So changing `holdover` shifts how much RNG
state gets consumed beforehand, which changes the specific field centers B's
place cells land on, purely as an incidental side effect — verified directly:

```
same seed, only holdover changed:
holdover=0.0: next draws = [0.3636, 0.9718, 0.9624, 0.2518, 0.4972]
holdover=0.5: next draws = [0.2279, 0.4271, 0.8180, 0.8607, 0.0070]
holdover=1.0: next draws = [0.5086, 0.9076, 0.2493, 0.4104, 0.7556]
```

(Note: *which* cells get a place field at all is unaffected — that draw comes
from Python's separate `random.sample` in `combined_place_tebc.py:67` — only
*where* the field centers land is coupled.)

**Effect:** not a directional bug (every draw is an equally-valid
`uniform_jitter` layout), but it means a holdover-vs-not comparison at a fixed
seed is not actually a clean single-variable ablation — env B's geometry
changes too. Averaged over many unseeded sweep runs this washes out as noise
rather than bias, so it's an unlikely sole explanation for the reproducible
place_dependent floor, but it's a real reproducibility hazard.

**Fix:** give place-field placement (and/or `holdover_task_responsiveness`) its
own seeded `np.random.default_rng()` instance instead of sharing the global
`np.random` state.

### 5. Population-wide noise term is a single shared scalar, not per-cell
**Repo:** RatInABox
**File:** `ratinabox/hsw/combined_place_tebc.py:88`

```python
self.firingrate += np.random.normal(-0.02 / 30, 0.02 / 30)
```

No `size=` argument — `np.random.normal(loc, scale)` returns a single scalar,
which then broadcasts onto the entire `self.n`-length `firingrate` array
identically. Verified directly:

```
np.random.seed(0); x = np.zeros(5); x += np.random.normal(-0.02/30, 0.02/30)
→ [0.00050937 0.00050937 0.00050937 0.00050937 0.00050937]
```

Every cell gets the *exact same* additive jitter at every timestep, rather
than independent per-cell noise — reads like a missing `size=self.n`.

**Effect:** injects a population-wide, temporally-varying, position-irrelevant
common-mode fluctuation into every cell simultaneously at every step. Small in
absolute terms (~0.0007) relative to a place field's peak (~4.6), but
comparable in size to `BASELINE_FR` (~0.00067) — i.e. not negligible for
populations with a large near-baseline/silent majority (e.g. low
`percent_task_cells`). Plausible aggravating factor for a `time_delta`-
conditional decoder (CEBRA), which leans on step-to-step population-vector
changes; a shared random offset at each step is a fake temporal signal
uncorrelated with position. Not proven to be a primary cause of any of the
observed decoding failures, but clearly not doing what it looks intended to do.

**Fix:** `np.random.normal(-0.02 / 30, 0.02 / 30, size=self.n)`.

### 6. tEBC-driven firing never gated off outside a trial — task response bled
into the inter-trial period
**Repo:** RatInABox
**File:** `ratinabox/hsw/combined_place_tebc.py`, `_combine_by_category`

`_task_firing_rate` evaluates each responsive cell's response function purely
off `self.agent.time_since_cs`, which keeps counting up even after the trial
marker itself has already returned to inter-trial (see `_combine_by_category`'s
own docstring). Nothing downstream corrected for that: `_combine_by_category`
applied `task_fr` to both task-only cells and the place+task balance blend
unconditionally, with no check against `self.agent.in_trial` at all. A test
asserting the intended gated behavior
(`test_balance_has_no_effect_outside_a_trial`) already existed in the repo and
was quietly **failing** at HEAD — confirmed directly:
`model.firingrate[MIXED]` came back `4.78` against an expected `1.69 ± 1.7e-06`
(the blend, not the pure place rate) once the animal was moved past the trial
marker but before `time_since_cs` left the response window.

**Effect:** every place+task and task-only cell kept emitting its full tEBC
response for as long as the response curve stayed elevated past trial end,
rather than dropping back to pure-place / baseline firing the instant the
trial itself ended. Injects task-locked signal into what should be
trial-free background epochs — a confound for any downstream analysis of
inter-trial baseline activity.

**Fix (implemented, not yet committed):** gate the task-driven branches of
`_combine_by_category` behind `self.agent.in_trial`; outside a trial, both
task-only and place+task cells now fall back to their trial-off state
(baseline and pure place respectively), matching what the pre-existing test
already asserted.

### 7. `build_model` hardcoded 80 neurons for every TEBC class, ignoring the
`num_neurons` actually passed to `simulate_experiment`
**Repo:** RatInABox
**File:** `ratinabox/hsw/simulate_envs.py`, `build_model`

`simulate_experiment(model_type, ..., num_neurons, ...)` takes `num_neurons`
and correctly threads it into `assign_tebc_types_and_responsiveness(num_neurons, ...)`
and `utils.get_distribution_values(..., num_neurons)` — so every
distribution/mask array it builds is sized to the caller's `num_neurons`. But
`build_model` never received or used that value; it called every `tebc_cls(...)`
constructor with a literal `80` regardless. No TEBC subclass overrides that
count itself (`independent_model/TEBC.py`, `place_dependent_model/TEBC.py`,
`arousal_mediated_model/*.py` have no neuron-count logic of their own), so the
actual simulated population was silently pinned to 80 cells no matter what
`num_neurons` said.

**Effect:** inert as long as every caller happened to pass `num_neurons=80`
(true of `main.py` up to now), identically to bug #3's "currently inert"
framing. Not inert as soon as a caller passes anything else — `main.py` was
already changing `num_neurons = 80` to `132` in the same session, which would
have desynced the (132-sized) distribution/mask arrays from the (hardcoded
80-cell) model, an index/shape mismatch rather than a graceful fallback.

**Fix (implemented, not yet committed):** `build_model` now takes `num_neurons`
as an explicit parameter and passes it through to every `tebc_cls(...)` call
instead of the literal `80`.

## Open questions / unexplained anomalies (not yet root-caused)

- **Independent model's `percent_task_cells=0.0` corner is also a full floor**
  (~-0.17), despite being the *most* place-cell-pure corner of the grid (zero
  task-responsive cells, no dilution). Verified via code inspection that no
  task response can leak into place-only cells' firing rate at this setting
  (`combined_place_tebc.py`'s category masks correctly zero out the task
  contribution when `task_responsive_indices` is all-False). The sharp jump
  from floor at `task_cells=0.0` to ~0.87-0.90 at `task_cells=0.2` suggests
  CEBRA's `time_delta`-conditional training may need *some* population
  activity/structure beyond pure spatial tuning to converge well — possibly
  related to bug #5 being proportionally larger relative to signal when most
  of the population (70% at `task_cells=0`, `percent_place_cells=0.3`) sits at
  baseline. Not confirmed. **Not re-tested since the `FR_MAX`/place-field-width
  fix** (see intro) — the old per-cell `FR_MAX` threshold this analysis was
  reasoning about no longer exists (replaced by the Poisson spike-count
  model), and the place-field width formula changed too, so this floor should
  be re-measured against the current code rather than assumed to still apply
  as described.

- **Confirmed no special-casing of `holdover=0.0`/`1.0`** as distinct from
  intermediate values (checked `args_parser.py`, `main.py`, `simulate_envs.py`,
  `holdover_task_responsiveness` end to end) — the old boolean semantics are
  fully gone from the current code; the only value-dependent branch
  (`simulate_envs.py:69`, `if holdover > 0`) is a no-op under the `fixed`
  distributions all these sweeps use. Ruled out as an explanation.
