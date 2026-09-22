#!/usr/bin/env python
"""Front C - prove intensification_min_depth's default changes nothing.

Same instrument as diagnostics/item20b/default_equivalence.py: hashes the whole
'periods' column of every train series, step by step, at package defaults and
at the reference configs. A summary statistic could coincide while the series
differ; the full column cannot.

*** CORRECTION, 2026-09-22 - READ THIS BEFORE USING ANY NUMBER BELOW ***

This module computes a digest with its OWN blob layout:

    sha256( concat over sorted ids of: sid + "|".join(periods) )

with no separator between series and no ":" after the id. That is NOT the
project's canonical default-behaviour digest, which is defined and produced by

    research/labels/diagnostics/front_b/default_behaviour_hash.py

as "<id>:<periods joined by |>" lines joined with "\n". Two different blobs over
identical behaviour give two different numbers.

This module's earlier docstring claimed that CHANGELOG's b500d2e0...c4a5 "does
NOT reproduce" under numpy 2.5.3 / scipy 1.18.0 / pandas 3.0.5 and concluded the
recorded hash was environment-dependent. **That conclusion was wrong.** It
compared this layout's number against the canonical layout's number. Run with
the canonical generator in that very environment, b500d2e0...c4a5 reproduces
exactly, at 17dc21f and at 7a87a10 alike.

What remains valid here is only the RELATIVE comparison: within this module's
own layout, a package-defaults run on this branch equals one on an unmodified
develop-v2.1 worktree, and an explicit 0.0 equals an absent key. Those
equalities are real. The absolute values below are meaningful only against each
other.

For any default-behaviour claim, use the canonical generator. See
docs/future_work.md item 24.
"""
from __future__ import annotations

import hashlib
import inspect
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "research" / "labels"))
sys.path.insert(0, str(REPO))

from labels_core import load_real_series, load_synthetic_series, read_split
from cyclophaser.determine_periods import get_periods, process_vorticity

PV_KEYS = ("use_filter", "replace_endpoints_with_lowpass", "use_smoothing",
           "use_smoothing_twice", "savgol_polynomial", "cutoff_low",
           "cutoff_high", "boundary_padding")
# The CANONICAL digest (front_b layout). Listed here only to be explicit that
# this module's numbers are NOT comparable with it - not as a target to match.
CHANGELOG_DEFAULT_SHA = "b500d2e0b0112e5250073385639a030155e06fc21c15509fdcda88254226c4a5"
# Measured on an unmodified develop-v2.1 worktree under numpy 2.5.3 /
# scipy 1.18.0 / pandas 3.0.5 - the environment this front was run in.
DEV21_DEFAULT_SHA = "b01b16b6a86498d18509a0f3bcdac4c5a448615ae86a92c71899ed78aafc752f"


def load_config(name):
    doc = yaml.safe_load((REPO / "research/labels/configs" / name).read_text()) or {}
    gp_ok = set(inspect.signature(get_periods).parameters) - {"vorticity"}
    pv = {k: v for k, v in (doc.get("filter_params") or {}).items() if k in PV_KEYS}
    gp = {k: v for k, v in (doc.get("phase_params") or {}).items() if k in gp_ok}
    return pv, gp


def digest(series, pv, gp):
    h = hashlib.sha256()
    for sid, values in sorted(series.items()):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
            df = get_periods(vort, **gp)
        h.update(sid.encode())
        h.update("|".join(str(x) for x in df["periods"].tolist()).encode())
    return h.hexdigest()


def main():
    import scipy
    train = set(read_split()["train"])
    real = {s: v for s, v in load_real_series().items() if s in train}
    synth = {s: v for s, v in load_synthetic_series()[0].items() if s in train}
    allser = {**real, **synth}

    print(f"numpy {np.__version__}  scipy {scipy.__version__}  pandas {pd.__version__}")
    print(f"series hashed: {len(allser)} ({len(real)} real + {len(synth)} synthetic)\n")

    a = digest(allser, {}, {})
    print("A. PACKAGE DEFAULTS (no config; intensification_min_depth left unset)")
    print(f"   sha256 = {a}")
    print(f"   develop-v2.1, same env  = {DEV21_DEFAULT_SHA}")
    print(f"   MATCH (this is the claim): {a == DEV21_DEFAULT_SHA}")
    print(f"   canonical digest (DIFFERENT blob layout)    = {CHANGELOG_DEFAULT_SHA}")
    print("   not compared: a different layout over the same behaviour is a\n"
          "   different number. Use front_b/default_behaviour_hash.py.\n")

    b = digest(allser, {}, {"intensification_min_depth": 0.0})
    print("B. PACKAGE DEFAULTS + intensification_min_depth=0.0 passed EXPLICITLY")
    print(f"   sha256 = {b}")
    print(f"   equals A: {a == b}   (an explicit 0.0 and an absent key must be the same thing)\n")

    pv12, gp12 = load_config("cyclophaser_params-12.yaml")
    c = digest(allser, pv12, gp12)
    d = digest(allser, pv12, {**gp12, "intensification_min_depth": 0.0})
    print("C. params-12 (key absent -> default 0.0)")
    print(f"   sha256 = {c}")
    print("D. params-12 + intensification_min_depth=0.0 EXPLICIT")
    print(f"   sha256 = {d}   equals C: {c == d}\n")

    pv13, gp13 = load_config("cyclophaser_params-13.yaml")
    e = digest(allser, pv13, gp13)
    print("E. params-13 (intensification_min_depth=0.05) - expected to DIFFER from C")
    print(f"   sha256 = {e}   differs from C: {e != c}")
    print(f"   intensification_min_depth read from YAML: {gp13.get('intensification_min_depth')!r}")
    print("   (if this key is missing, the parameter never reached get_periods)")


if __name__ == "__main__":
    main()
