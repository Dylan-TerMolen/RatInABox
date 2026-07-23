from ratinabox.Environment import Environment
import numpy as np

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

    return Environment(params={
        'boundary': boundary.tolist(),
        'boundary_conditions': 'solid'
    })
