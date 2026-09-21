#!/usr/bin/env python
"""Front 20(b) stage 2 - prove mature_min_depth's default changes nothing.

Hashes the full phase output of every train series (47: 35 real + 12 synthetic)
at PACKAGE DEFAULTS and at params-11, and prints one sha256 per configuration.
Run on this branch and on develop-v2.1; the hashes must match exactly.

Deliberately hashes the whole 'periods' column, step by step - not a summary
statistic, which could coincide while the series differ.
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
    print(f"git HEAD: (see report)   series hashed: {len(allser)} "
          f"({len(real)} real + {len(synth)} synthetic)\n")

    print("A. PACKAGE DEFAULTS (no config at all, mature_min_depth left unset)")
    print(f"   sha256 = {digest(allser, {}, {})}\n")

    pv11, gp11 = load_config("cyclophaser_params-11.yaml")
    print("B. params-11 (mature_min_depth absent from the YAML -> default 0.0)")
    print(f"   sha256 = {digest(allser, pv11, gp11)}\n")

    print("C. params-11 + mature_min_depth=0.0 passed EXPLICITLY")
    print(f"   sha256 = {digest(allser, pv11, {**gp11, 'mature_min_depth': 0.0})}")
    print("   (must equal B: an explicit 0.0 and an absent key are the same thing)\n")

    print("D. params-12 (mature_min_depth=0.80) - expected to DIFFER from B")
    pv12, gp12 = load_config("cyclophaser_params-12.yaml")
    print(f"   sha256 = {digest(allser, pv12, gp12)}")
    print(f"   mature_min_depth read from YAML: {gp12.get('mature_min_depth')!r}")
    print("   (if this key is missing, the parameter never reached get_periods)")


if __name__ == "__main__":
    main()
