#!/usr/bin/env python
"""Front C - intensification_min_depth: the measurement.

Reference = params-12 (the current reference, mature_min_depth=0.80).
Candidate = params-13 (params-12 + intensification_min_depth=0.05).

Measured over the TRAIN split (35 real + 12 synthetic). `read_split()["test"]`
is NOT read here; the two test-split series the brief names are measured by
report_test_series.py, separately and with Danilo's explicit authorisation.

The mature metric is the SAME instrument front 20(b) stage 2 used
(diagnostics/item20b/gate_stage2.py): the first labelled mature run is paired
with the best-OVERLAPPING detected mature block, and counts as a match when
both |d_start| <= 6 and |d_end| <= 6. It is reproduced here rather than
imported so the number this front reports is traceable to the code that made
it.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "research" / "labels"))
sys.path.insert(0, str(REPO))

from labels_core import (load_real_series, load_synthetic_series, normalize_phase,
                         read_labels, read_split, series_sha256)
from cyclophaser.determine_periods import get_periods, process_vorticity

OUT = REPO / "research" / "labels" / "diagnostics" / "frontC"
PV_KEYS = ("use_filter", "replace_endpoints_with_lowpass", "use_smoothing",
           "use_smoothing_twice", "savgol_polynomial", "cutoff_low",
           "cutoff_high", "boundary_padding")
MARGIN = 6


def load_config(name):
    doc = yaml.safe_load((REPO / "research/labels/configs" / name).read_text()) or {}
    gp_ok = set(inspect.signature(get_periods).parameters) - {"vorticity"}
    pv = {k: v for k, v in (doc.get("filter_params") or {}).items() if k in PV_KEYS}
    gp = {k: v for k, v in (doc.get("phase_params") or {}).items() if k in gp_ok}
    return pv, gp


def runs_of(names):
    out, prev, start = [], None, 0
    for i, n in enumerate(names):
        if n != prev:
            if prev is not None:
                out.append((prev, start, i - 1))
            prev, start = n, i
    out.append((prev, start, len(names) - 1))
    return out


def label_runs(record):
    ph, n = record["phases"], record["n_steps"]
    out = []
    for k, p in enumerate(ph):
        s = p["start_idx"]
        e = (ph[k + 1]["start_idx"] - 1) if k + 1 < len(ph) else n - 1
        out.append((normalize_phase(p["phase"]), s, e, bool(p.get("unsure"))))
    return out


def pair_by_overlap(det, lab):
    if not det or lab is None:
        return None
    ls, le = lab
    best, best_ov = None, -1
    for (ds, de) in det:
        o = min(de, le) - max(ds, ls) + 1
        if o > best_ov:
            best, best_ov = (ds, de), o
    if best_ov <= 0:
        mid = (ls + le) / 2
        best = min(det, key=lambda b: abs((b[0] + b[1]) / 2 - mid))
    return best


def leading_incipient(runs):
    return runs[0][2] + 1 if runs and runs[0][0] == "incipient" else None


def run_one(sid, values, record, pv, gp):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
        df = get_periods(vort, **gp)
        caught = [str(x.message) for x in w]

    periods = [normalize_phase(str(x)) for x in df["periods"]]
    runs = runs_of(periods)
    det = [(a, b) for p, a, b in runs if p == "mature"]
    lab = label_runs(record) if record else []
    lab_mat = [(a, b) for p, a, b, u in lab if p == "mature"]
    first_lab = lab_mat[0] if lab_mat else None
    paired = pair_by_overlap(det, first_lab)

    d_start = d_end = None
    matches = False
    if paired and first_lab:
        d_start, d_end = paired[0] - first_lab[0], paired[1] - first_lab[1]
        matches = abs(d_start) <= MARGIN and abs(d_end) <= MARGIN

    return dict(
        id=sid, n=len(values), periods=periods,
        runs=[(p, a, b) for p, a, b in runs],
        lab_seq=[p for p, _, _, _ in lab], det_seq=[p for p, _, _ in runs],
        has_lab_mature=first_lab is not None,
        d_start=d_start, d_end=d_end, matches=matches,
        incip_end=leading_incipient(runs),
        phase_set=sorted(set(periods)),
        warnings=caught,
        sha_ok=(series_sha256(values) == record["series_sha256"]) if record else None,
    )


def run_all(pv, gp, series, labels):
    return {s: run_one(s, v, labels.get(s), pv, gp) for s, v in sorted(series.items())}


def summarise(res, labels):
    seq = sum(1 for f in res.values() if f["det_seq"] == f["lab_seq"])
    mat_n = sum(1 for f in res.values() if f["has_lab_mature"])
    mat_hit = sum(1 for f in res.values() if f["has_lab_mature"] and f["matches"])
    return dict(n=len(res), seq=seq, mature_hit=mat_hit, mature_n=mat_n)


def main():
    import scipy
    train = set(read_split()["train"])
    labels = read_labels()
    real = {s: v for s, v in load_real_series().items() if s in train}
    synth = {s: v for s, v in load_synthetic_series()[0].items() if s in train}
    allser = {**real, **synth}

    print(f"numpy {np.__version__}  scipy {scipy.__version__}  pandas {pd.__version__}")
    for n in ("cyclophaser_params-12.yaml", "cyclophaser_params-13.yaml"):
        p = REPO / "research/labels/configs" / n
        print(f"{n}  sha256 {hashlib.sha256(p.read_bytes()).hexdigest()}")
    print(f"train: {len(real)} real + {len(synth)} synthetic = {len(allser)}\n")

    pv, gp12 = load_config("cyclophaser_params-12.yaml")
    _, gp13 = load_config("cyclophaser_params-13.yaml")
    print(f"params-12 intensification_min_depth = {gp12.get('intensification_min_depth')!r}")
    print(f"params-13 intensification_min_depth = {gp13.get('intensification_min_depth')!r}\n")

    ref = run_all(pv, gp12, allser, labels)
    cand = run_all(pv, gp13, allser, labels)

    bad_sha = [s for s, f in ref.items() if f["sha_ok"] is False]
    print(f"series_sha256 verified: {sum(1 for f in ref.values() if f['sha_ok'])} ok, "
          f"{len(bad_sha)} MISMATCH {bad_sha}\n")

    # --- which series changed at all -------------------------------------
    changed = [s for s in ref if ref[s]["periods"] != cand[s]["periods"]]
    print(f"=== series whose labelling changed: {len(changed)} ===")
    for s in changed:
        print(f"\n  {s}")
        print(f"    before: {ref[s]['runs']}")
        print(f"    after : {cand[s]['runs']}")

    # --- no series loses the existence of a phase -------------------------
    print("\n=== phase-existence check (no phase may disappear) ===")
    lost = []
    for s in ref:
        gone = set(ref[s]["phase_set"]) - set(cand[s]["phase_set"])
        gone.discard("residual")   # reported separately: removing spurious residual is the POINT
        if gone:
            lost.append((s, sorted(gone)))
    res_gone = [s for s in ref if "residual" in ref[s]["phase_set"]
                and "residual" not in cand[s]["phase_set"]]
    print(f"  non-residual phases lost: {lost if lost else 'NONE'}")
    print(f"  residual phases removed : {res_gone}")

    # --- headline metrics -------------------------------------------------
    print("\n=== metrics (TRAIN) ===")
    for tag, res in (("params-12 (ref)", ref), ("params-13 (cand)", cand)):
        r = {k: v for k, v in res.items() if k in real}
        sy = {k: v for k, v in res.items() if k in synth}
        a = summarise(res, labels)
        print(f"  {tag:18s} sequence {a['seq']}/{a['n']}   "
              f"mature +-{MARGIN} {a['mature_hit']}/{a['mature_n']}   "
              f"synthetic sequence {summarise(sy, labels)['seq']}/{len(sy)}   "
              f"real sequence {summarise(r, labels)['seq']}/{len(r)}")

    same_incip = sum(1 for s in ref if ref[s]["incip_end"] == cand[s]["incip_end"])
    print(f"  incipient boundary identical: {same_incip}/{len(ref)}")

    wrn = {s: f["warnings"] for s, f in cand.items() if f["warnings"]}
    print(f"  warnings raised under params-13: {wrn if wrn else 'none'}")

    OUT.mkdir(parents=True, exist_ok=True)
    json.dump({"changed": changed,
               "ref": {s: {k: v for k, v in f.items() if k != "periods"} for s, f in ref.items()},
               "cand": {s: {k: v for k, v in f.items() if k != "periods"} for s, f in cand.items()}},
              (OUT / "measurements.json").open("w"), indent=1, default=str)
    print(f"\nwrote {OUT/'measurements.json'}")


if __name__ == "__main__":
    main()
