"""Specs for `holdover_task_responsiveness`: env B's task-responsive population is
built from `ceil(holdover_fraction * num_A_task_responsive)` of env A's actual
task-responsive cells (carried over by identity and cell type) plus however many
freshly-drawn cells are needed to reach env B's own exact target count.

Two things need checking that a plain output inspection can't distinguish cleanly:
the quota split itself (`held` vs `fresh` counts), and whether cells that only
*coincidentally* end up responsive in both envs (freshly drawn, landing back on a
cell that happened to be responsive in A) get a fresh cell type rather than A's --
only genuinely-held cells should keep their type. The quota-split test below spies
on `np.random.choice`'s call arguments to check the sizes directly, sidestepping
that ambiguity; the identity test picks a holdover_fraction=1.0 scenario where every
A-responsive cell is guaranteed held (no coincidence involved) so the type-copy can
be checked unambiguously.
"""
import numpy as np
import pytest

from ratinabox.hsw.independent_model.assign_tebc_types_and_responsiveness import holdover_task_responsiveness

N = 100


def _task_responsive_mask(n, responsive_indices):
    mask = np.full(n, False)
    mask[responsive_indices] = True
    return mask


def test_quota_split_matches_worked_example(monkeypatch):
    """75 task-responsive cells in env A, holdover_fraction=0.5, target 75 in env B
    -> ceil(0.5 * 75) = 38 held, 75 - 38 = 37 freshly drawn."""
    a_responsive_indices = np.arange(75)
    task_responsive_A = _task_responsive_mask(N, a_responsive_indices)
    cell_types_A = np.random.randint(1, 9, size=N)
    target_distribution_B = np.full(N, 0.75)  # sums to 75

    choice_calls = []
    real_choice = np.random.choice

    def spy_choice(a, size=None, replace=True, p=None):
        choice_calls.append((np.asarray(a), size, replace))
        return real_choice(a, size=size, replace=replace, p=p)

    monkeypatch.setattr(np.random, "choice", spy_choice)

    indices_B, _ = holdover_task_responsiveness(task_responsive_A, cell_types_A, 0.5, target_distribution_B)

    held_pool, held_size, held_replace = choice_calls[0]
    assert held_size == 38
    assert held_replace is False
    assert set(held_pool.tolist()) == set(a_responsive_indices.tolist())

    fresh_pool, fresh_size, fresh_replace = choice_calls[1]
    assert fresh_size == 37
    assert fresh_replace is False

    assert indices_B.sum() == 75


def test_full_holdover_preserves_identity_and_cell_type_when_a_is_under_target():
    """holdover_fraction=1.0 with num_A_responsive < target: every A-responsive cell
    is guaranteed held (not just coincidentally overlapping a fresh draw), so its
    exact cell type must carry over unchanged."""
    a_indices = np.array([1, 4, 7, 10, 22, 31, 40])
    task_responsive_A = _task_responsive_mask(N, a_indices)
    cell_types_A = np.random.randint(1, 9, size=N)
    target_distribution_B = np.full(N, 0.35)  # target_total = 35, well above len(a_indices) = 7

    indices_B, types_B = holdover_task_responsiveness(task_responsive_A, cell_types_A, 1.0, target_distribution_B)

    assert indices_B[a_indices].all()
    np.testing.assert_array_equal(types_B[a_indices], cell_types_A[a_indices])
    assert indices_B.sum() == 35  # 7 held + 28 fresh


def test_holdover_does_not_inflate_past_target_when_a_overshoots():
    """Env A's own assignment is still a per-cell Bernoulli draw (not exact-count),
    so its realized task-responsive count can exceed env B's target by chance.
    A high holdover_fraction must not carry that overshoot into env B."""
    task_responsive_A = _task_responsive_mask(N, np.arange(90))  # A realized 90, above B's target
    cell_types_A = np.random.randint(1, 9, size=N)
    target_distribution_B = np.full(N, 0.75)  # target_total = 75

    indices_B, _ = holdover_task_responsiveness(task_responsive_A, cell_types_A, 1.0, target_distribution_B)

    assert indices_B.sum() == 75


@pytest.mark.parametrize("holdover_fraction", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_env_b_total_always_hits_target_exactly(holdover_fraction):
    a_responsive_indices = np.random.choice(N, 75, replace=False)
    task_responsive_A = _task_responsive_mask(N, a_responsive_indices)
    cell_types_A = np.random.randint(1, 9, size=N)
    target_distribution_B = np.full(N, 0.6)  # deliberately different from A's 75, target_total = 60

    indices_B, _ = holdover_task_responsiveness(task_responsive_A, cell_types_A, holdover_fraction, target_distribution_B)

    assert indices_B.sum() == 60
