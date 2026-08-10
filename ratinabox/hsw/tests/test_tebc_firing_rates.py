"""High-level specs: for a 3-neuron population (one place-only, one task-only,
one place+task), the independent and place-dependent TEBC models must compute the exact,
hand-derivable firing rate at a moment during the CS and a moment during the US.
They must also gate off every task-driven contribution -- the balance blend for
place+task cells, and the raw response for task-only cells -- the instant the
animal leaves a trial, even if the tEBC response itself hasn't decayed back to
zero yet.

Design:
  - The place-responsive neurons' field centres are pinned to the agent's exact
    position at the CS checkpoint, so the *unmodulated* place rate there is
    exactly `max_fr` (12) by construction -- no need to trust or re-derive
    RatInABox's Gaussian/geodesic place-field math for that checkpoint.
  - The real `response_profiles` are numerically renormalized over a 1000-point
    grid (see `_normalized` in `tebc_response2.py`), so they have no closed form
    to check by hand. We substitute a trivial stand-in response shape instead:
    full amplitude during the CS window, half amplitude during the US window,
    zero otherwise. This still exercises the real `_task_amplitudes` (the part
    of the refactor that differs between models) and the real category-routing
    / balance-blend arithmetic in `CombinedPlaceTebc` -- it just swaps out the
    (irrelevant here, unchanged by this refactor) biological curve shape.
  - The velocity-modulation polynomial and the non-pinned-checkpoint place rate
    (the agent has walked away from the pinned centre by then) are the two
    pieces still sourced from the real, trusted subsystems rather than hand
    re-derived; each is called out where used below.
"""
import numpy as np
import pytest

from ratinabox.Neurons import PlaceCells
from ratinabox.hsw.combined_place_tebc import BASELINE_FR
from ratinabox.hsw.environment_builder import build_rectangular_environment
from ratinabox.hsw.independent_model.TEBC import TEBC as IndependentTEBC
from ratinabox.hsw.place_dependent_model.TEBC import TEBC as PlaceDependentTEBC
from ratinabox.hsw.place_dependent_model.TEBC import TASK_ONLY_BASELINE
from ratinabox.hsw.tebc_agent import TebcAgent
from ratinabox.hsw.tests.conftest import CS_CHECK_STEPS, STEPS_CS_TO_US

N = 3
PLACE_ONLY, TASK_ONLY, MIXED = 0, 1, 2

PLACE_RESPONSIVE = np.array([True, False, True])   # place-only, -, mixed
TASK_RESPONSIVE = np.array([False, True, True])    # -, task-only, mixed
BALANCE = np.array([0.0, 0.0, 0.3])                # only the mixed cell's balance matters; deliberately
                                                     # asymmetric (!= 0.5) so a `(1 - balance)` -> `balance`
                                                     # typo in the blend formula can't hide behind 0.5 == 1-0.5
CELL_TYPES = np.array([1, 1, 1])                   # arbitrary: response_profiles is stubbed below

# The model's own published velocity-tuning polynomial (copied from
# combined_place_tebc.py) -- reproducible with a calculator, not a re-derivation.
VELOCITY_POLY = np.poly1d([-3.26092478e-04, 1.74074978e-02, 8.36619150e-02, 1.16059441])
WALK_SPEED_CM_S = 15  # matches conftest's ~0.15 m/s trajectory

# Stand-in tEBC response: full amplitude in the CS window, half in the US
# window, zero otherwise. Deliberately trivial so its value is obvious by eye.
CS_WINDOW = (0.0, 0.25)
US_WINDOW = (0.75, 0.85)


def toy_response(time_since_cs, amplitude):
    if CS_WINDOW[0] <= time_since_cs < CS_WINDOW[1]:
        return amplitude
    if US_WINDOW[0] <= time_since_cs < US_WINDOW[1]:
        return amplitude * 0.5
    return 0.0


def _build_model(model_cls, agent, pinned_centre):
    model = model_cls(agent, N, BALANCE, TASK_RESPONSIVE.astype(float), 0.5, TASK_RESPONSIVE, CELL_TYPES)
    model.place_responsive_indices = PLACE_RESPONSIVE.copy()
    model.task_responsive_indices = TASK_RESPONSIVE.copy()
    model._set_category_masks()
    model.place_cell_centres[PLACE_ONLY] = pinned_centre
    model.place_cell_centres[MIXED] = pinned_centre
    model.response_profiles = {1: {"response_func": toy_response}}
    return model


def _place_rate_oracle(model):
    """Oracle for the place rate at the model's current checkpoint: once the
    agent has walked away from the pinned centre, this is sourced from the real
    PlaceCells Gaussian computation rather than hand-derived."""
    PlaceCells.update(model)
    raw_place = model.firingrate.copy()
    vel = model.agent.smoothed_velocity
    place_fr = raw_place * (VELOCITY_POLY(vel * 100) / 30)
    place_fr[~model.place_responsive_indices] = 0.02 / 30
    return place_fr


def test_independent_model_firing_rates_during_cs_and_us(fresh_agent, no_jitter):
    for _ in range(CS_CHECK_STEPS):
        fresh_agent.update()
    cs_position = fresh_agent.pos.copy()

    model = _build_model(IndependentTEBC, fresh_agent, cs_position)

    # --- CS checkpoint (time_since_cs == 0.0) ---
    # Place rate: unmodulated rate is exactly max_fr (12), by construction of
    # the pinned centre; the velocity-modulation factor is a published constant.
    place_fr_cs = 12.0 * (VELOCITY_POLY(WALK_SPEED_CM_S) / 30)  # == 2.0926592107
    # Independent model: tEBC amplitude is always max_fr (12), regardless of place firing.
    task_fr_cs = 12.0  # toy_response(0.0, amplitude=12) -> in the CS window -> 12
    balance = BALANCE[MIXED]  # 0.3
    expected_cs = np.array([
        place_fr_cs,                                                    # place-only: pure place rate
        task_fr_cs,                                                     # task-only: pure task response
        balance * task_fr_cs + (1 - balance) * place_fr_cs,             # mixed: balance blend, == 5.0648614475
    ])

    model.update()
    np.testing.assert_allclose(model.firingrate, expected_cs, rtol=1e-8, atol=1e-10)

    # --- US checkpoint (time_since_cs == 0.8) ---
    for _ in range(STEPS_CS_TO_US):
        fresh_agent.update()
    place_fr_us = _place_rate_oracle(model)  # oracle: agent has moved off the pinned centre
    task_fr_us = 12.0 * 0.5  # toy_response(0.8, amplitude=12) -> in the US window -> half amplitude -> 6.0
    expected_us = np.array([
        place_fr_us[PLACE_ONLY],
        task_fr_us,
        balance * task_fr_us + (1 - balance) * place_fr_us[MIXED],
    ])

    model.update()
    np.testing.assert_allclose(model.firingrate, expected_us, rtol=1e-8, atol=1e-10)


def test_place_dependent_model_firing_rates_during_cs_and_us(fresh_agent, no_jitter):
    for _ in range(CS_CHECK_STEPS):
        fresh_agent.update()
    cs_position = fresh_agent.pos.copy()

    model = _build_model(PlaceDependentTEBC, fresh_agent, cs_position)
    assert model.task_only_baseline == TASK_ONLY_BASELINE  # default; the task-only cell's amplitude below relies on it

    # --- CS checkpoint (time_since_cs == 0.0) ---
    place_fr_cs = 12.0 * (VELOCITY_POLY(WALK_SPEED_CM_S) / 30)  # == 2.0926592107, same derivation as independent
    # Place-dependent model: task-only cell has no place field, so its amplitude
    # falls back to the fixed task_only_baseline (0.5).
    task_only_amplitude = model.task_only_baseline
    task_fr_cs_task_only = task_only_amplitude  # toy_response(0.0, 0.5) -> CS window -> 0.5
    balance = BALANCE[MIXED]  # 0.3
    # Place-dependent model: the mixed cell's amplitude is its own place rate, so at
    # the CS checkpoint amplitude == place_fr_cs, and blending two equal terms
    # collapses back to that same value regardless of balance -- this specific
    # assertion can't distinguish a correct blend from a `balance` typo bug in
    # the blend formula; the US-checkpoint assertion below can, since there the
    # two blended terms differ.
    task_fr_cs_mixed = place_fr_cs  # toy_response(0.0, place_fr_cs) -> CS window -> place_fr_cs
    expected_cs = np.array([
        place_fr_cs,
        task_fr_cs_task_only,
        balance * task_fr_cs_mixed + (1 - balance) * place_fr_cs,  # == place_fr_cs
    ])

    model.update()
    np.testing.assert_allclose(model.firingrate, expected_cs, rtol=1e-8, atol=1e-10)

    # --- US checkpoint (time_since_cs == 0.8) ---
    for _ in range(STEPS_CS_TO_US):
        fresh_agent.update()
    place_fr_us = _place_rate_oracle(model)  # oracle: agent has moved off the pinned centre
    task_fr_us_task_only = task_only_amplitude * 0.5  # toy_response(0.8, 0.5) -> US window -> 0.25
    task_fr_us_mixed = place_fr_us[MIXED] * 0.5        # toy_response(0.8, place_fr_us) -> US window -> half
    expected_us = np.array([
        place_fr_us[PLACE_ONLY],
        task_fr_us_task_only,
        balance * task_fr_us_mixed + (1 - balance) * place_fr_us[MIXED],
    ])

    model.update()
    np.testing.assert_allclose(model.firingrate, expected_us, rtol=1e-8, atol=1e-10)


def test_independent_amplitude_is_fixed_at_max_fr(fresh_agent):
    """Defining property of the independent model: tEBC amplitude is a fixed
    constant, decoupled from the cell's own place firing rate."""
    model = _build_model(IndependentTEBC, fresh_agent, pinned_centre=np.array([0.5, 0.5]))

    amplitudes = model._task_amplitudes(place_fr=np.array([1.0, 2.0, 3.0]))

    np.testing.assert_allclose(amplitudes, model.max_fr)


def test_place_dependent_amplitude_tracks_place_rate_or_baseline(fresh_agent):
    """Defining property of the place-dependent model: tEBC amplitude is the cell's
    own place firing rate if it has a field, else a fixed task-only baseline."""
    model = _build_model(PlaceDependentTEBC, fresh_agent, pinned_centre=np.array([0.5, 0.5]))
    place_fr = np.array([1.0, 2.0, 3.0])

    amplitudes = model._task_amplitudes(place_fr)

    assert amplitudes[PLACE_ONLY] == pytest.approx(place_fr[PLACE_ONLY])
    assert amplitudes[MIXED] == pytest.approx(place_fr[MIXED])
    assert amplitudes[TASK_ONLY] == pytest.approx(model.task_only_baseline)


# A single CS pulse (index 2) that drops straight back to inter-trial (index 3+),
# so time_since_cs == 1/30s -- still inside the toy CS window -- at the same step
# the marker has already left the trial. Exercises the case a hand-derived CS/US
# checkpoint can't: a lingering tEBC response after the animal has left a trial.
POST_TRIAL_CHECK_STEPS = 3
_OFF_TRIAL_MARKERS = np.array([0, 0, 1, 0, 0, 0])


def _build_off_trial_agent():
    n_steps = len(_OFF_TRIAL_MARKERS)
    step = (WALK_SPEED_CM_S / 100) / (30 * np.sqrt(2))  # cm/s -> m/step, same diagonal walk as conftest
    times = np.arange(n_steps) / 30
    xs = 0.4 + step * np.arange(n_steps)
    ys = 0.4 + step * np.arange(n_steps)
    position_data = np.vstack([times, xs, ys, _OFF_TRIAL_MARKERS])

    env = build_rectangular_environment(position_data[1:3].T)
    agent = TebcAgent(env, position_data)
    agent.import_trajectory(times=position_data[0], positions=position_data[1:3].T, interpolate=False)
    return agent


def test_balance_has_no_effect_outside_a_trial(no_jitter):
    """Every task-driven contribution must switch off the instant the animal leaves
    a trial, even though the tEBC response is still active (hasn't decayed to zero
    yet): a place+task cell falls back to its pure place rate (not a blend), and a
    task-only cell falls back to baseline (not its raw response)."""
    agent = _build_off_trial_agent()
    model = _build_model(IndependentTEBC, agent, pinned_centre=np.array([0.5, 0.5]))

    for _ in range(POST_TRIAL_CHECK_STEPS):
        agent.update()
    assert not agent.in_trial  # marker has already returned to inter-trial
    assert CS_WINDOW[0] <= agent.time_since_cs < CS_WINDOW[1]  # but the tEBC response hasn't lapsed yet

    place_fr = _place_rate_oracle(model)
    balance = BALANCE[MIXED]  # 0.3
    task_fr_would_be = 12.0  # toy_response(time_since_cs, amplitude=12) -> in the CS window -> 12
    blend_if_ungated = balance * task_fr_would_be + (1 - balance) * place_fr[MIXED]
    # Sanity check the test is non-vacuous: without the in-trial gate, the blend and
    # the task-only response really would differ from their gated fallbacks, so the
    # final assertions can catch the gate's absence.
    assert not np.isclose(blend_if_ungated, place_fr[MIXED])
    assert not np.isclose(task_fr_would_be, BASELINE_FR)

    model.update()

    assert model.firingrate[MIXED] == pytest.approx(place_fr[MIXED])
    assert model.firingrate[TASK_ONLY] == pytest.approx(BASELINE_FR)
