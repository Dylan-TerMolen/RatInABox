# Wirtshafter, Solla & Disterhoft (2025) — "A universal hippocampal memory code across animals and environments"

bioRxiv preprint: https://doi.org/10.1101/2024.10.24.620127
PDF: `wirtshafter-2025-universal-hippocampal-code.pdf` (this directory, not tracked in git)

This is the empirical paper the `hsw/` simulation is modeling. Freely-moving rats (n=5) were
trained on trace eyeblink conditioning (tEBC) in environment A, then transferred to a
geometrically/sensorially distinct environment B, with CA1 population activity recorded via
calcium imaging (miniscope, GCaMP8m) throughout.

## Task design (mirrors `tebc_agent.py` / env A-vs-B structure in this repo)
- CS: 250 ms tone. Trace interval: 500 ms. US: 100 ms eyelid shock. CR = blink during trace
  interval, before US onset.
- Criterion: 70% CRs over 50 trials on 3 consecutive sessions (or 4-session average > 70%).
  Animals reached criterion in an average of 20±4.2 sessions in env A, then were tested for
  2 sessions in env B with no significant drop in performance — i.e. the task transfers, even
  though (per below) the spatial code does not.
- Two environments (A: rectangular/wire/white light/unscented; B: oval/solid floor/red
  light/scented) placed at the same room location, so external distal cues are shared but local
  sensory context differs — this is the A/B split the `independent_model` / `place_dependent_model` /
  `arousal_mediated_model` variants are each trying to capture computationally.

## Core findings
1. **Place cells remap between A and B** (~9% of cells are place cells by mutual-information
   criterion; field centers shift far more A→B than session-to-session within A; population
   vector correlation is positive within A but drops to ~0 A→B). A CEBRA model trained to decode
   position in A fails to decode position in B (worse than shuffle-trained control) — spatial
   coding does not transfer.
2. **Task (CS/US) coding does not remap.** A CEBRA model trained on CS/US labels (2-bin
   CSUS-MI2, or 5-bin fine-grained CSUS-MI5 covering CS/trace/US sub-periods) in env A decodes
   CS/US structure in env B just as well as it decodes a held-out session in env A — including
   fine temporal order within the trace interval. Task-responsive cells are not confined to
   place fields (Mantel test, event locations during CS/US vs. non-conditioning periods are
   unrelated).
3. **Task-coding geometry is consistent not just across environments within an animal, but
   across animals** — CEBRA embedding consistency scores (2–10 latents) between different rats'
   models are statistically indistinguishable from between-session consistency within one rat,
   suggesting a shared "neural syntax" for the conditioning task rather than an idiosyncratic
   per-animal code.
4. Spatial MI and CSUS-MI are weakly but significantly positively correlated per-cell (r²≈0.04–
   0.09) — some overlap in which cells carry each kind of information, but the population-level
   codes (place vs. task) occupy separable, coexisting subspaces rather than one being a subset
   of the other.

## Relevance to this codebase
- The whole point of `hsw/` (independent/place_dependent/arousal_mediated/separate_learning models +
  `cond_decoding_AvsB.py` / `pos_decoding_AvsB_DEP.py` in Hannahs-CEBRAs) is to construct
  simulated place + tEBC-responsive populations whose CEBRA-decoded behavior reproduces findings
  (1) and (2) above: position decodes A→A but not A→B, while CS/US task structure decodes A→B
  about as well as A→A. The "rank inter-environment configs by cross-env A→B score over
  shuffled control" rule in `ratinabox/CLAUDE.md` is directly checking for the pattern in Fig. 3
  (position, should fail to transfer) vs. Fig. 5 (task, should transfer).
- `percent_place_cells`, `tebc_responsive_neurons`/`cell_types`, and the balance/responsive
  distributions in `place_dependent_model/TEBC.py` are the simulation's stand-in for the paper's split
  between place-modulated and CSUS-modulated (and jointly-modulated) real CA1 cells.
- Model naming: "independent" vs. "place_dependent" vs. "arousal_mediated" reflects different hypotheses for how
  a single cell's place tuning and task tuning combine (independent/additive vs. one gated by
  the other) — this is the open question the paper raises in finding (4) but doesn't resolve
  mechanistically, since it only characterizes population geometry, not single-cell combination
  rules.
