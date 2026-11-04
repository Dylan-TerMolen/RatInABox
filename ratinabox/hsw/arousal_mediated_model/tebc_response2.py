"""tEBC task-response functions for the arousal-mediated model.

Modeled on Shan, Lubenov, Papadopoulou & Siapas (2016), "Spatial tuning and
brain state account for dorsal hippocampal CA1 activity in a non-spatial
learning task", eLife 5:e14321 (https://doi.org/10.7554/eLife.14321),
specifically the PSTHs in Figure 3A/B (measured directly off the published
figure, not just the text) and the ripple dynamics in Figure 4A/B. That paper
records dorsal CA1 during trace eyeblink conditioning and finds CA1 stays
purely spatial throughout: apparent CS/tone responses are not genuine
stimulus tuning, they're an artifact of brain state. While the animal is
stationary, sharp-wave ripples drive "out-of-field" firing unrelated to its
actual location; the CS is arousing, abruptly terminates ripples, and firing
snaps back to match the place field at the animal's current (stationary)
location. While the animal is running, no such modulation happens, aside
from a small genuine uptick right at the US.

The four response types below are gated on (in_field, running), each shaped
to match its own panel in Fig 3A ("Running") / 3B ("Sitting"):

- R1 in field, running (Fig 3A top): flat through CS/trace, a small uptick
  just after the US.
- R2 out of field, running (Fig 3A bottom): no systematic (CS-locked) response,
  but not a dead flat 0 either -- small non-systematic noise throughout.
- R3 in field, sitting (Fig 3B top): a rise starting at CS onset to ~8 Hz
  (baseline ~3 Hz), a slow decline through the trace interval to ~6 Hz, a
  sharp spike to ~15 Hz at the US, then a slow decay back to baseline.
- R4 out of field, sitting (Fig 3B bottom / Fig 4): elevated ripple-driven
  noise pre-trial that drops out at CS onset (ripples "abruptly cease
  following the CS onset", Fig 4A), then a short uptick at the US.

One note on fidelity to the paper: the narrow, sharp dip exactly at US onset
visible in every Fig 3 panel is the paper's own artifact-blanking window --
"electrical artifacts prevent spike detection during the [10 ms] US delivery
window" -- not a biological response, and specific to extracellular
electrophysiology. Our simulated data represents calcium imaging, which has
no equivalent electrical-saturation artifact, so none of the functions below
reproduce that dip. The genuine upticks that follow it (visible in the same
panels, on both sides of the blanked window) are kept.
"""
import numpy as np

# Timing of stimuli in seconds
CS_duration = 0.25  # CS duration in seconds
CS_to_US_delay = 0.5  # Delay between CS and US in seconds (trace)
US_time = CS_duration + CS_to_US_delay  # Time when US occurs
US_pulse_duration = 0.1  # matches the 100ms US stimulus itself

# How long a CS-triggered state (R3's elevated firing, R4's ripple
# suppression) is held before the animal is assumed to lapse back into a
# quiescent, ripple-prone state.
TRIAL_PERIOD = 1.5

# Fig 4A: ripples are detected in roughly half of pre-trial sitting periods,
# not continuously.
RIPPLE_PROBABILITY = 0.5

# R1 -- in field, running (Fig 3A top): flat except a small uptick shortly
# after the US pulse ends.
SMALL_US_UPTICK_MULT = 0.15  # peak additive fraction of baseline
SMALL_US_UPTICK_PEAK_TIME = US_time + US_pulse_duration + 0.05
SMALL_US_UPTICK_SD = 0.08

# R2 -- out of field, running (Fig 3A bottom): small non-systematic jitter, well
# below R4's full ripple-burst scale -- this is measurement noise, not a ripple
# event (ripples don't occur during locomotion).
OUT_FIELD_RUNNING_NOISE_MULT = 0.1

# R3 -- in field, sitting (Fig 3B top): rise at CS onset, slow decline through
# the trace interval, sharp spike at US, slow decay back to baseline. Levels
# are expressed as multiples of `baseline`, calibrated so a ~3 Hz baseline
# (Fig 3B's own pre-trial rate for an in-field sitting cell) reproduces the
# ~3 -> 8 -> 6 -> 15 -> 3 Hz trajectory read off that panel.
RISE_END = CS_duration  # uptick right at the start of the trial
FIRST_PEAK_MULT = 8 / 3  # ~8 Hz at baseline ~3 Hz
DECLINE_END = US_time  # slow decrease through the trace interval
TRACE_PLATEAU_MULT = 6 / 3  # back down to ~6 Hz by the end of trace
US_SPIKE_END = US_time + US_pulse_duration  # sharp rise to peak over the US pulse
US_PEAK_MULT = 15 / 3  # spike to ~15 Hz
SLOW_DECAY_END = 1.4  # slow decay back to baseline afterward

# R4 -- out of field, sitting (Fig 3B bottom): short uptick right at the US,
# scaled off the population's peak per-frame rate (ripple_scale), not this
# cell's own near-zero local rate.
OUT_FIELD_US_UPTICK_PEAK_TIME = US_time + 0.02
OUT_FIELD_US_UPTICK_SD = 0.03


def _linear_ramp(t, t_start, t_end, level_start, level_end):
    """Interpolates linearly from level_start to level_end over [t_start, t_end],
    clamped to the endpoint levels outside that range."""
    if t <= t_start:
        return level_start
    if t >= t_end:
        return level_end
    frac = (t - t_start) / (t_end - t_start)
    return level_start + frac * (level_end - level_start)


def _gaussian_bump(t, peak_time, peak_level, sd):
    return peak_level * np.exp(-((t - peak_time) ** 2) / (2 * sd ** 2))


def type_one_response(time_since_CS, baseline):  # in place field, running
    """
    Fig 3A top: flat through CS and trace -- "CS-evoked changes in firing
    rate are absent when the animal is running" -- but with a small genuine
    uptick shortly after the US pulse (the bump visible just past the
    artifact-blanked window in the same panel).
    """
    if time_since_CS < US_time + US_pulse_duration:
        return 0.0
    return _gaussian_bump(time_since_CS, SMALL_US_UPTICK_PEAK_TIME,
                           SMALL_US_UPTICK_MULT * baseline, SMALL_US_UPTICK_SD)


def type_two_response(time_since_CS, ripple_scale):  # out of place field, running
    """
    Fig 3A bottom: no systematic (CS-locked) modulation -- running abolishes
    that effect regardless of place-field membership -- but the real trace is
    still noisy, not a perfectly dead flat 0. Scaled off the same population
    peak per-frame rate (`ripple_scale`) as type_four_response, not this
    cell's own near-zero out-of-field local rate, since there's nothing
    informative to scale noise off of locally.
    """
    return np.random.uniform(-OUT_FIELD_RUNNING_NOISE_MULT, OUT_FIELD_RUNNING_NOISE_MULT) * ripple_scale


def type_three_response(time_since_CS, baseline):  # in place field, stopped
    """
    Arousal-mediated resumption of place-specific firing, matching Fig 3B
    top's shape: a rise starting at CS onset to ~8 Hz (baseline ~3 Hz), a
    slow decline through the trace interval to ~6 Hz, a sharp spike to
    ~15 Hz at the US, then a slow decay back down to baseline.
    """
    if time_since_CS < RISE_END:
        mult = _linear_ramp(time_since_CS, 0.0, RISE_END, 1.0, FIRST_PEAK_MULT)
    elif time_since_CS < DECLINE_END:
        mult = _linear_ramp(time_since_CS, RISE_END, DECLINE_END,
                             FIRST_PEAK_MULT, TRACE_PLATEAU_MULT)
    elif time_since_CS < US_SPIKE_END:
        mult = _linear_ramp(time_since_CS, DECLINE_END, US_SPIKE_END,
                             TRACE_PLATEAU_MULT, US_PEAK_MULT)
    elif time_since_CS < SLOW_DECAY_END:
        mult = _linear_ramp(time_since_CS, US_SPIKE_END, SLOW_DECAY_END,
                             US_PEAK_MULT, 1.0)
    else:
        mult = 1.0
    return (mult - 1.0) * baseline


def type_four_response(time_since_CS, ripple_scale):  # out of place field, stopped
    """
    Fig 3B bottom / Fig 4: sharp-wave-ripple-driven firing pre-trial (elevated,
    intermittent -- RIPPLE_PROBABILITY) that "abruptly cease[s] following the
    CS onset", staying quiet through most of the trial except for a short,
    genuine uptick right at the US, before ripples can resume past
    TRIAL_PERIOD. Burst/uptick amplitude is scaled off the population's peak
    per-frame rate (`ripple_scale`), not this cell's own near-zero local
    rate -- a ripple-driven event looks like genuine in-field firing from an
    unrelated place field, not a boost to the current location.
    """
    if 0 <= time_since_CS <= TRIAL_PERIOD:
        return _gaussian_bump(time_since_CS, OUT_FIELD_US_UPTICK_PEAK_TIME,
                               ripple_scale, OUT_FIELD_US_UPTICK_SD)
    if np.random.rand() < RIPPLE_PROBABILITY:
        return np.random.uniform(0, ripple_scale)
    return 0.0
