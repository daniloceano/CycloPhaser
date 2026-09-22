#!/usr/bin/env python
"""Front C - prove intensification_min_depth's default changes nothing.

Same instrument as diagnostics/item20b/default_equivalence.py: hashes the whole
'periods' column of every train series, step by step, at package defaults and
at the reference configs. A summary statistic could coincide while the series
differ; the full column cannot.

What "unchanged" means here
---------------------------
The claim under test is that this branch's DEFAULT output equals develop-v2.1's
default output. The comparison that establishes that is cross-BRANCH, in one
environment - not against a hash written down on another machine.

CHANGELOG.md records b500d2e0...c4a5 for the package-defaults digest (front
20(b), numpy 2.4.4 / scipy 1.17.1 / pandas 3.0.2). That value does NOT
reproduce under numpy 2.5.3 / scipy 1.18.0 / pandas 3.0.5, and the reason is
not this front: running this same digest on an unmodified develop-v2.1 worktree
in this environment yields b01b16b6...752f, exactly what this branch yields.
The recorded hash is environment-dependent and was written down as though
absolute. See REPORT.md.

To reproduce the control:

    git worktree add /tmp/dev21 develop-v2.1
    # copy control_A.py there and run it in the cyclophaser env
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
# Recorded by front 20(b) under numpy 2.4.4 / scipy 1.17.1 / pandas 3.0.2.
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
    print(f"   CHANGELOG (front 20(b), other lib versions) = {CHANGELOG_DEFAULT_SHA}")
    print(f"   match: {a == CHANGELOG_DEFAULT_SHA}  <- expected False here; see module docstring\n")

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
