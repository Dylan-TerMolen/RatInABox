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
    place_r2_in_task      A->A: 0.8123  B->B: 0.7534  A->B: 0.6621  shuffA->A: 0.1234  shuffA->B: 0.1198
    place_cm_in_task      A->A: 3.1000  B->B: 4.0500  A->B: 6.4000  shuffA->A: 15.200  shuffA->B: 15.900
    place_r2_out_of_task  A->A: 0.7900  B->B: 0.7400  A->B: 0.5800  shuffA->A: 0.0800  shuffA->B: 0.0700
    place_cm_out_of_task  A->A: 3.5000  B->B: 4.4000  A->B: 6.9000  shuffA->A: 15.500  shuffA->B: 16.100
    task   A->A: 0.9012  B->B: 0.8877  A->B: 0.7765  shuffA->A: 0.2001  shuffA->B: 0.1987

    (repeated per iteration)

Place decoding is split by task state (in-task vs. out-of-task, i.e. whether
the rat was in a CS/trace/US trial at that row -- see filter_by_velocity /
pos_score_by_task_state) and reported as R^2 and mean cm error separately;
task decoding stays a single pooled R^2 per direction. Each iteration's lines
are parsed generically (whatever '<kind>  key: val ...' lines appear before
the next blank line), rather than a fixed line count, so ITERATION_KINDS is
the only place that needs to change if a kind is ever added or dropped.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Value allows an optional leading '-' -- place-decoder R^2-style scores go
# negative far more often than task's, so without it every key from the
# first negative score onward on a line silently drops (see _parse_scores).
_SCORE_RE = re.compile(r"([A-Za-z>-]+): (n/a|-?[\d.]+)")
# One iteration block: an identifier line followed by consecutive non-blank
# '<kind>  scores...' lines, up to the blank line write_iteration_summary
# writes between iterations.
_ITERATION_RE = re.compile(r"Parameters: (.+)\n((?:[^\n].*\n)*)")
_KIND_LINE_RE = re.compile(r"^(\S+)\s+(.+)$")

# Score keys in the order write_iteration_summary emits them, prefixed with
# a kind (see ITERATION_KINDS) for use as plot-picker labels.
SCORE_KEYS = ["A->A", "B->B", "A->B", "shuffA->A", "shuffA->B"]

# Every '<kind>  key: val ...' line write_iteration_summary can emit, in
# that order. Place decoding is split into four lines (R^2/mean-cm-error x
# in-task/out-of-task); task decoding is a single pooled-R^2 line.
ITERATION_KINDS = [
    "place_r2_in_task", "place_cm_in_task",
    "place_r2_out_of_task", "place_cm_out_of_task",
    "task",
]


@dataclass
class Iteration:
    identifier: str
    scores: dict[str, dict[str, float | None]] = field(default_factory=dict)

    def kind(self, name: str) -> dict[str, float | None]:
        """This iteration's {direction: value} scores for one ITERATION_KINDS
        entry, or {} if that kind's line wasn't present (e.g. an older log
        written before it existed)."""
        return self.scores.get(name, {})


@dataclass
class ParsedLog:
    run_params: dict[str, str] = field(default_factory=dict)
    cebra_config: dict[str, dict[str, str]] = field(default_factory=dict)
    iterations: list[Iteration] = field(default_factory=list)


def _parse_scores(line: str) -> dict[str, float | None]:
    return {k: (float(v) if v != "n/a" else None) for k, v in _SCORE_RE.findall(line)}


def _parse_iteration_body(body: str) -> dict[str, dict[str, float | None]]:
    """kind -> {direction: value} for every '<kind>  key: val ...' line in body."""
    scores = {}
    for line in body.splitlines():
        match = _KIND_LINE_RE.match(line)
        if not match:
            continue
        kind, rest = match.groups()
        scores[kind] = _parse_scores(rest)
    return scores


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

    for identifier, body in _ITERATION_RE.findall(text):
        result.iterations.append(Iteration(
            identifier=identifier.strip(),
            scores=_parse_iteration_body(body),
        ))

    return result
