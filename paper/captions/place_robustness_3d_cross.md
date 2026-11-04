**Supplementary Figure. Cross-environment position decoding (A→B) over each
model's own swept parameter grid, out-of-task.** Same data/axes/shared-scale
setup as `place_robustness_3d_within`, but A→B instead of A→A -- a decoder
trained in environment A, tested in environment B, where any surviving
accuracy (here, low error) reflects a stable (not A-specific) spatial code.
Mean position-decoding error in centimeters, lower is better -- see
`place_robustness_3d_within`'s caption for why R² isn't used.

Same reference plane (mean shuffled-control error for A→B), same per-point
below-chance marking (black ring = CI entirely below the shuffled floor's
CI), and the same independent partial-sweep flag (see
`place_robustness_3d_within`'s caption) as its within-environment companion.
