"""Backward-compat re-export. The .log parser now lives at
ratinabox/hsw/results_io.py so both webui/ and paper/ can import it without
either package depending on the other. Import from
ratinabox.hsw.results_io directly in new code -- this module exists only so
existing `from . import hsw_log` call sites keep working."""
from ratinabox.hsw.results_io import (
    Iteration,
    ITERATION_KINDS,
    ParsedLog,
    SCORE_KEYS,
    parse,
)

__all__ = ["Iteration", "ITERATION_KINDS", "ParsedLog", "SCORE_KEYS", "parse"]
