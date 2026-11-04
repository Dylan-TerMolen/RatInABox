**Figure 2. The three models and the activity they produce.** IM adds a task
response to place activity at any location; PDM's task response only appears
while the animal is inside the cell's place field; ADM's task response is
gated by both place-field occupancy and movement state. IM and PDM draw from
the same {{stat.models.n_response_types}} empirically-observed response types
(1, 2, 3, 8, at renormalized frequencies); ADM uses 4 profiles defined by
(in field / out of field) x (moving / not moving).

**(a)** Schematic of how each model combines its task and place components.

**(b)** Raw task response for each default response type, no place-firing
combination (shared by IM and PDM).

**(c)** IM: combined place+task response by field distance (in field, near
the field edge, out of field), per type.

**(d)** PDM: same layout as (c) -- note the out-of-field trace collapses to
~0 for every type, since PDM's task amplitude *is* the (near-zero
out-of-field) place rate.

**(e)** ADM: task response by (in field / out of field) x (moving / not
moving), laid out to match Shan et al. (2016) Fig. 3A/B.

**(f)** Rasters from real simulated data: one example place+task-responsive
cell per model, spike counts around CS onset, split by field state at onset
(and additionally by movement state for ADM). The ADM moving/not-moving
split is imbalanced because the animal is moving at CS onset in most trials
of this recording -- a property of the behavior, not the raster.
