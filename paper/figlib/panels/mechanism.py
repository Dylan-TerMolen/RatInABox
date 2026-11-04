"""Panel for the `mechanism` figure (draft Fig 4): one task-responsive place
cell per model, trial-averaged firing rate around CS onset in env A vs env B.
Not ported from figures.ipynb cells 38-39 -- those build a different figure
(a single real trajectory crossing through one field, IM/PDM only, no A-vs-B
comparison at all), which doesn't match this figure's actual spec (A vs B,
all 3 models, task vs non-task period). Built fresh against the same sim
artifacts instead.

Population-stability panel added 2026-09-29 (review item 7): one example
cell per model is anecdotal, and the draft itself asks for a quantitative
stability measure -- population_stability below is the per-model
distribution of every place+task-responsive cell's own A-vs-B correlation,
the population-level counterpart to single_cell_firing_A_vs_B's one example
trace.
"""
from __future__ import annotations

import numpy as np

from ratinabox.hsw.tebc_response import CS_duration, US_duration, US_start_time

from paper.figlib import style
from paper.figlib.io import SimArtifact
from paper.figlib.panels.setup import cs_onset_steps

PRE_S, POST_S = 1.0, 2.0  # matches models.py's raster window


def _place_task_mask(cells: dict) -> np.ndarray:
    return (np.asarray(cells["place_responsive_indices"], dtype=bool)
            & np.asarray(cells["task_responsive_indices"], dtype=bool))


def example_cell_both_envs(sim: SimArtifact) -> int:
    """First cell that's place+task-responsive in BOTH envs -- the only kind
    that can show a "does this cell's response survive remapping" comparison
    at all."""
    both = np.flatnonzero(_place_task_mask(sim.cells["A"]) & _place_task_mask(sim.cells["B"]))
    if len(both) == 0:
        raise ValueError(f"no cell is place+task-responsive in both envs for {sim.run_id}")
    return int(both[0])


def _trial_averaged_rate(spike_row: np.ndarray, trial_marker: np.ndarray, step: float,
                          pre_steps: int, post_steps: int) -> tuple[np.ndarray, np.ndarray]:
    """(mean_rate_hz, sem_rate_hz) across every CS-onset trial, per time bin."""
    onsets = cs_onset_steps(trial_marker)
    onsets = onsets[(onsets - pre_steps >= 0) & (onsets + post_steps < len(trial_marker))]
    windows = np.stack([spike_row[o - pre_steps: o + post_steps] for o in onsets]) / step
    return windows.mean(axis=0), windows.std(axis=0, ddof=1) / np.sqrt(len(onsets))


def single_cell_firing_A_vs_B(ax, sim: SimArtifact, model_type: str) -> None:
    """One task-responsive place cell's trial-averaged firing rate around CS
    onset, env A vs env B. IM's task-cell identity is expected to survive
    remapping (A/B traces overlay); PDM/ADM's population pattern is expected
    to change because task response there depends on the (independently
    redrawn) place field location.

    Env A/B are drawn in THIS panel's own model color (not style.ENV_COLORS)
    and differentiated by line style instead (solid A, dashed B) --
    ENV_COLORS' blue/orange pair is two of MODEL_COLORS' own three colors, so
    using it here would clash with the model-color identity this whole
    figure is organized around (2026-10-04 review). The legend is drawn by
    the caller (figures/mechanism.py) as one shared figure-level legend, not
    per panel."""
    cell_index = example_cell_both_envs(sim)
    us_end = US_start_time + US_duration
    ax.axvspan(0, CS_duration, color=style.PHASE_COLORS["tone"], alpha=0.15)
    ax.axvspan(CS_duration, US_start_time, color="gray", alpha=0.1)
    ax.axvspan(US_start_time, us_end, color=style.PHASE_COLORS["shock"], alpha=0.15)

    color = style.MODEL_COLORS[model_type]
    for env in ("A", "B"):
        agent = sim.agent[env]
        step = agent["times"][1] - agent["times"][0]
        pre_steps, post_steps = int(round(PRE_S / step)), int(round(POST_S / step))
        mean_rate, sem_rate = _trial_averaged_rate(sim.spikes[env][cell_index], agent["trial_marker"],
                                                    step, pre_steps, post_steps)
        time_axis = (np.arange(pre_steps + post_steps) - pre_steps) * step
        ax.plot(time_axis, mean_rate, color=color, linestyle=style.ENV_LINESTYLES[env], label=style.env_label(env))
        ax.fill_between(time_axis, mean_rate - sem_rate, mean_rate + sem_rate, color=color, alpha=0.2)

    ax.set_xlabel("Time since CS (s)")
    ax.set_ylabel("Firing rate (Hz)")
    ax.set_title(style.MODEL_DISPLAY_NAMES[model_type], fontsize=9)


def _cell_response_correlations(sim: SimArtifact) -> np.ndarray:
    """A→B Pearson correlation of trial-averaged CS-onset firing rate, for
    every cell that's place+task-responsive in both envs -- the population
    version of single_cell_firing_A_vs_B's one example cell. A cell whose
    trace is flat in either env (zero variance, e.g. never fired near CS
    onset) has an undefined correlation and is skipped."""
    both = np.flatnonzero(_place_task_mask(sim.cells["A"]) & _place_task_mask(sim.cells["B"]))
    correlations = []
    for cell_index in both:
        rates = {}
        for env in ("A", "B"):
            agent = sim.agent[env]
            step = agent["times"][1] - agent["times"][0]
            pre_steps, post_steps = int(round(PRE_S / step)), int(round(POST_S / step))
            rates[env], _ = _trial_averaged_rate(sim.spikes[env][cell_index], agent["trial_marker"],
                                                  step, pre_steps, post_steps)
        if rates["A"].std() == 0 or rates["B"].std() == 0:
            continue
        correlations.append(float(np.corrcoef(rates["A"], rates["B"])[0, 1]))
    return np.array(correlations)


def population_stability(ax, sims_by_model: dict[str, SimArtifact], model_type_order: tuple[str, ...]) -> None:
    """Per-model distribution of every task cell's own A-vs-B response
    correlation: individual cells as a scatter (deterministic x per model, no
    jitter -- CLAUDE.md's no-seeding rule applies to any RNG in this
    pipeline, not just the simulation), with mean +/- 95% CI overlaid. IM is
    expected to sit high (task identity survives remapping); PDM/ADM are
    expected to scatter lower (task response depends on the independently
    redrawn place field)."""
    ax.axhline(0, color="black", linewidth=0.6, alpha=0.5, zorder=0)
    for i, model_type in enumerate(model_type_order):
        values = _cell_response_correlations(sims_by_model[model_type])
        color = style.MODEL_COLORS[model_type]
        ax.scatter(np.full(len(values), i, dtype=float), values, color=color, alpha=0.5, s=14, zorder=2)
        n = len(values)
        mean = float(values.mean()) if n else float("nan")
        sem = values.std(ddof=1) / np.sqrt(n) if n > 1 else 0.0
        ax.errorbar([i], [mean], yerr=[1.96 * sem], color=color, marker="_", markersize=16,
                    capsize=4, linewidth=1.5, zorder=3)
    ax.set_xlim(-0.5, len(model_type_order) - 0.5)
    ax.set_xticks(range(len(model_type_order)),
                  [style.MODEL_ABBREVIATIONS[m] for m in model_type_order])
    ax.set_ylabel("A→B response correlation (r)")
    ax.set_title("Population stability", fontsize=9)
