from collections import namedtuple

from ratinabox.Environment import Environment
import numpy as np

# Centre + semi-axes of a built ellipse, stashed on the Environment so downstream
# code (place-field placement) can sample from the ellipse's own geometry instead
# of its bounding box. See sample_ellipse_positions.
EllipseGeometry = namedtuple('EllipseGeometry', ['centre_x', 'centre_y', 'radius_x', 'radius_y'])

# Successive golden-angle rotations never repeat a fraction of a full turn, so points
# placed at increasing radius never line up into radial spokes. See sample_ellipse_positions.
GOLDEN_ANGLE = np.pi * (3 - np.sqrt(5))


def _calculate_boundaries(positions):
    min_x = np.min(positions[:, 0])
    max_x = np.max(positions[:, 0])
    min_y = np.min(positions[:, 1])
    max_y = np.max(positions[:, 1])
    return min_x, max_x, min_y, max_y


def build_rectangular_environment(positions):
    min_x, max_x, min_y, max_y = _calculate_boundaries(positions)

    return Environment(params={
        'boundary': [[min_x, min_y], [min_x, max_y], [max_x, max_y], [max_x, min_y]],
        'boundary_conditions': 'solid'
    })


def _min_enclosing_ellipse_scale(positions, centre_x, centre_y, base_radius_x, base_radius_y, margin):
    normalized_distances = (
        ((positions[:, 0] - centre_x) / base_radius_x) ** 2
        + ((positions[:, 1] - centre_y) / base_radius_y) ** 2
    )
    return np.sqrt(normalized_distances.max()) + margin


def build_elliptical_environment(positions, n_boundary_points=256, margin=5e-3):
    """Build an Environment whose boundary is the smallest ellipse, centred and axis-aligned
    on the positions' bounding box, that contains every position.

    Matches the oval enclosure used for environment B (Fig. 1b of the source paper,
    see ratinabox/hsw/docs/wirtshafter-2025-universal-hippocampal-code.md), rather than
    the axis-aligned rectangle `build_rectangular_environment` produces. Fitting the ellipse
    exactly to the bounding box (radius = half the x/y span) leaves some real trajectory
    points just outside it, since the arena isn't a perfect axis-aligned ellipse; `margin`
    is added on top of the minimal containing scale so every input position falls strictly
    inside the boundary. The rendered boundary is itself an n_boundary_points-sided polygon
    inscribed in that ellipse, whose straight edges bow slightly inside the curve between
    vertices, so `margin` also needs to cover that polygon-approximation gap — a larger
    n_boundary_points shrinks the gap rather than requiring a bigger margin.
    """
    min_x, max_x, min_y, max_y = _calculate_boundaries(positions)
    centre_x, centre_y = (min_x + max_x) / 2, (min_y + max_y) / 2
    base_radius_x, base_radius_y = (max_x - min_x) / 2, (max_y - min_y) / 2

    scale = _min_enclosing_ellipse_scale(positions, centre_x, centre_y, base_radius_x, base_radius_y, margin)
    radius_x, radius_y = base_radius_x * scale, base_radius_y * scale

    theta = np.linspace(0, 2 * np.pi, n_boundary_points, endpoint=False)
    boundary = np.column_stack([
        centre_x + radius_x * np.cos(theta),
        centre_y + radius_y * np.sin(theta),
    ])

    env = Environment(params={
        'boundary': boundary.tolist(),
        'boundary_conditions': 'solid'
    })
    env.ellipse_geometry = EllipseGeometry(centre_x, centre_y, radius_x, radius_y)
    return env


def sample_ellipse_positions(ellipse_geometry, n, jitter_frac=0.1):
    """n positions spread evenly across an ellipse via the golden-angle ("sunflower") spiral.

    Radius follows an equal-area schedule (sqrt((k + 0.5) / n)) so each point owns an
    equal slice of the ellipse's area rather than being packed densest at the centre;
    angle advances by GOLDEN_ANGLE each step so points never fall into radial spokes.
    Every point lands inside the ellipse by construction (r < 1 for all k < n), so --
    unlike Environment.sample_positions's bounding-box grid, which discards whatever
    tiled point falls outside a non-rectangular boundary and replaces it with an
    uncorrelated random point (see build_elliptical_environment) -- this needs no
    rejection sampling and stays even for any n.

    jitter_frac scales a random radial nudge by each point's remaining headroom to the
    boundary (1 - r) and a random angular nudge by a fraction of the golden angle, so a
    jittered point can never land outside the ellipse.
    """
    k = np.arange(n)
    r = np.sqrt((k + 0.5) / n)
    theta = k * GOLDEN_ANGLE
    if jitter_frac:
        headroom = 1 - r
        r = r + np.random.uniform(-jitter_frac, jitter_frac, n) * headroom
        theta = theta + np.random.uniform(-jitter_frac, jitter_frac, n) * GOLDEN_ANGLE
    x = ellipse_geometry.centre_x + ellipse_geometry.radius_x * r * np.cos(theta)
    y = ellipse_geometry.centre_y + ellipse_geometry.radius_y * r * np.sin(theta)
    return np.column_stack([x, y])
