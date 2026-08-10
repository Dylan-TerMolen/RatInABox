"""Parser for the .log files ratinabox/hsw/main.py writes (see
simulation_helpers.py: write_run_header, write_cebra_config,
write_iteration_summary). Not CSV -- a custom text format:

    === Run parameters ===
    model_type: place_dependent
    experiment: my_experiment
    ...
    ======================

    === CEBRA config ===
    [task_decoder]
    learning_rate: 0.00086
    ...
    [position_decoder]
    ...
    ======================

    Parameters: responsive_0.6_fixed_PCs_0.4.npy
    place  A->A: 0.8123  B->B: 0.7534  A->B: 0.6621  shuffA->A: 0.1234  shuffA->B: 0.1198
    task   A->A: 0.9012  B->B: 0.8877  A->B: 0.7765  shuffA->A: 0.2001  shuffA->B: 0.1987

    (repeated per iteration)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_SCORE_RE = re.compile(r"([A-Za-z>-]+): (n/a|[\d.]+)")
_ITERATION_RE = re.compile(r"Parameters: (.+)\nplace\s+(.+)\ntask\s+(.+)")

# Score keys in the order write_iteration_summary emits them, prefixed with
# 'place '/'task ' for use as plot-picker labels.
SCORE_KEYS = ["A->A", "B->B", "A->B", "shuffA->A", "shuffA->B"]


@dataclass
class Iteration:
    identifier: str
    place: dict[str, float | None]
    task: dict[str, float | None]


@dataclass
class ParsedLog:
    run_params: dict[str, str] = field(default_factory=dict)
    cebra_config: dict[str, dict[str, str]] = field(default_factory=dict)
    iterations: list[Iteration] = field(default_factory=list)


def _parse_scores(line: str) -> dict[str, float | None]:
    return {k: (float(v) if v != "n/a" else None) for k, v in _SCORE_RE.findall(line)}


def parse(text: str) -> ParsedLog:
    result = ParsedLog()

    m = re.search(r"=== Run parameters ===\n(.*?)\n======================", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                result.run_params[key.strip()] = value.strip()

    m = re.search(r"=== CEBRA config ===\n(.*?)\n======================", text, re.S)
    if m:
        label = None
        for line in m.group(1).splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                label = line[1:-1]
                result.cebra_config[label] = {}
            elif ":" in line and label:
                key, _, value = line.partition(":")
                result.cebra_config[label][key.strip()] = value.strip()

    for identifier, place_line, task_line in _ITERATION_RE.findall(text):
        result.iterations.append(Iteration(
            identifier=identifier.strip(),
            place=_parse_scores(place_line),
            task=_parse_scores(task_line),
        ))

    return result
