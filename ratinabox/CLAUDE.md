# HSW simulation — working notes

How we run and extend the HSW place/tEBC decoding simulations. Read this before
touching `main.py`, the model subdirectories, or the CEBRA decoding path.

## Source paper

The `hsw/` simulation is modeling Wirtshafter, Solla & Disterhoft (2025), "A universal
hippocampal memory code across animals and environments" (bioRxiv 2024.10.24.620127). Rats
learn trace eyeblink conditioning (tEBC) in environment A, transfer to environment B; place
cells remap A→B but CS/US task coding decodes A→B about as well as within-A, and the task
coding geometry is consistent across animals. See `ratinabox/hsw/docs/` for the PDF and a
summary tying each finding to the model code (`wirtshafter-2025-universal-hippocampal-code.md`).

## Layout (spans two repos)

- **This repo** (`ratinabox/hsw/`) generates simulated neural populations and drives decoding.
  - `main.py` — single unified entry point for every model. Builds agents in envs A and B,
    simulates firing, then calls the CEBRA decoders.
  - `args_parser.py` — all CLI args. `UNIVERSAL_PARAMS` apply to every model;
    `MODEL_REQUIRED_PARAMS` are per-model. Unsupported params for a model are rejected.
  - Models: `independent_model/`, `place_dependent_model/`, `arousal_mediated_model/`, `separate_learning/`.
  - Shared helpers: `simulation_helpers.py`, `utils.py`, `env.py`/`config`, `tebc_agent.py`.
- **Hannahs-CEBRAs repo** (`/Users/dylantermolen/Projects/Hannahs-CEBRAs`) owns the CEBRA decoders,
  imported here as the `hannahs_cebras` package. Cross-environment decoding lives in
  `cond_decoding_AvsB.py` (task/eyeblink) and `pos_decoding_AvsB_DEP.py` (position).

## CEBRA hyperparameters

Pass CEBRA hyperparameters from the CLI with `--cebra_*` flags (learning_rate, max_iterations,
output_dimension, min_temperature, temperature_mode, time_offsets, num_hidden_units, batch_size,
model_architecture, distance, conditional). They all default to `None`.

- Each decoder keeps its own tuned defaults in the Hannahs-CEBRAs repo: `COND_CEBRA_DEFAULTS`
  and `POS_CEBRA_DEFAULTS`. `cebra_config.merge_cebra_params(defaults, overrides)` applies only
  the flags actually passed, so an unset flag keeps that decoder's default.
- `args_parser.cebra_overrides(args)` collects the passed flags; `main.py` threads the result
  into both decoders as `cebra_params=`.

**Gotcha — the two decoders have different tuned learning rates** (task `8.6e-4`, position
`5.5e-5`). A single `--cebra_learning_rate` overrides BOTH. To tune one decoder's LR without
detuning the other, isolate it with `--decode_task false` or `--decode_position false`.

## Grid searches (Slurm)

Slurm experiment `.sh` files live in the repo-root `slurm/` directory — keep new ones there.
Every script queues its runs through the array sbatch arg — one array task per run — even a
single run (use `#SBATCH --array=0-0`). We grid-search the same way: one array task per
hyperparameter combination, mapped row-major from `SLURM_ARRAY_TASK_ID`. Keep simulation params (balance/responsive/PCs/holdovers)
fixed so decoding differences are attributable to the CEBRA config, not the data.
See `slurm/cebra_search.sh` (grid) and `slurm/cebra_test.sh` (single run) for the
pattern. Scripts reference `main.py` by absolute `${BASE_DIR}` path and write to an absolute
`--output` path, so their location in `slurm/` is independent of where jobs are submitted.
Cluster: account `p32472`, partition `gengpu`, `gpu:a100:1`, python at
`${HOME}/miniconda3/envs/ratinabox/bin/python`, base dir `/home/tfl2886/projects/RatInABox`.

**Rank inter-environment configs by the cross-env A->B score over its shuffled control**, not by
within-env accuracy — a config that decodes env A well but doesn't transfer to B is the failure
mode we're screening out. Use `--num_iters > 1` on final ranking runs to average CEBRA's
training stochasticity.

## Logging

Every run writes a `.log` next to its results. `main.py` writes two headers up front:
`write_run_header(vars(args))` records all CLI params, and `write_cebra_config(...)` records the
fully-resolved CEBRA config (tuned defaults + overrides) for each enabled decoder as separate
`[task_decoder]` / `[position_decoder]` blocks — so the log is self-contained even when params
fall back to defaults.
