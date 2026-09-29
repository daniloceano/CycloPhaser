"""Filling incomplete calibration configs with the FROZEN 2.0.0 defaults.

Decision (a) of item 31 (Danilo, 2026-09-28;
archive/research-diagnostics-pre-cleanup:research/labels/diagnostics/item31/DESIGN.md §8.1):
a config that does not carry a key is run with that key's
**cyclophaser 2.0.0 default**, and the keys filled are always listed.

Why frozen and not "the current default": a config file is a record of what was
run. Once the package defaults move (item 31, stage 2b), "absent" would silently
start meaning something else — a config exported with the decay-tail check OFF
(the app omits None) would run with the new default ON. The table is
`defaults_2.0.0.json`, generated from the stage-0 parameter table
(`archive/research-diagnostics-pre-cleanup:research/labels/diagnostics/item31/make_defaults_2_0_0.py`),
never edited by hand.

Used by `evaluate_against_labels.load_config`, `tools/calibration_app/
benchmark_core.split_config` / `signature_audit`, and the app's YAML import.
"""

from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path

DEFAULTS_PATH = Path(__file__).resolve().with_name("defaults_2.0.0.json")
SECTIONS = ("filter_params", "phase_params")


@lru_cache(maxsize=1)
def _table() -> dict:
    doc = json.loads(DEFAULTS_PATH.read_text())
    return {sec: dict(doc[sec]) for sec in SECTIONS}


def defaults_2_0_0() -> dict:
    """{'filter_params': {...}, 'phase_params': {...}} — a fresh copy of the frozen table."""
    return copy.deepcopy(_table())


def fill_missing(doc: dict | None) -> tuple[dict, list[tuple[str, object]]]:
    """Return (a filled copy of `doc`, [("section.key", value filled), ...]).

    Only the two parameter sections are touched. A key the config carries is
    never changed, whatever its value — including an explicit None. Keys the
    frozen table does not know are left for the caller to drop, as before.
    The input is not modified.
    """
    out = copy.deepcopy(doc) if doc else {}
    filled: list[tuple[str, object]] = []
    table = _table()
    for sec in SECTIONS:
        given = dict(out.get(sec) or {})
        for k, v in table[sec].items():
            if k not in given:
                given[k] = copy.deepcopy(v)
                filled.append((f"{sec}.{k}", v))
        out[sec] = given
    return out, filled


def fill_warning(filled: list[tuple[str, object]]) -> str:
    """The explicit warning: every key filled, with the value used."""
    if not filled:
        return ""
    items = ", ".join(f"{k}={v!r}" for k, v in filled)
    return (f"{len(filled)} key(s) absent from this config were filled with the "
            f"cyclophaser 2.0.0 defaults (frozen table {DEFAULTS_PATH.name}): {items}")
