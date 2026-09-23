#!/usr/bin/env python
"""Front D, stage 0 — incipient census on the TRAIN split, under params-13.

Diagnostic only: nothing in `cyclophaser/` is imported for anything but reading,
no parameter is changed, no file under `cyclophaser/` is touched.

The test split is never loaded into the detector. `_assert_train_only` raises
before any detection runs if a single test id reaches it, so "the test split was
not touched" is enforced by the code rather than asserted by the author.

Per train series, under params-13:
  N_det   number of leading `incipient` steps in the detected `periods`
          (0 = the detector produced no incipient phase). Read exactly as
          evaluate_against_labels.detected_incipient_end reads it, except that
          its None is rendered as 0 here, per the commissioning brief.
  N_lab   where the manual label ends the incipient phase (0 = label says the
          series has none; `ambiguous` = the labeller declined to place the
          boundary, which is a third state and is NOT folded into 0).
  |N_det - N_lab|
  defect I  does sign(z[1]-z[0]) differ between the raw and the filtered
          series? (docs/future_work.md item 8(d))
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "research" / "labels"))
sys.path.insert(0, str(REPO))

from labels_core import (  # noqa: E402
    load_real_series, load_synthetic_series, read_labels, read_split,
)
from evaluate_against_labels import (  # noqa: E402
    detected_incipient_end, detected_phase_starts, load_config,
)

CONFIG = REPO / "research/labels/configs/cyclophaser_params-13.yaml"
OUT = Path(__file__).resolve().parent


def _assert_train_only(ids, split) -> None:
    """Hard stop if any held-out id is about to reach the detector."""
    test = set(split["test"])
    leaked = sorted(set(ids) & test)
    if leaked:
        raise SystemExit(f"REFUSING TO RUN: test-split ids reached the detector: {leaked}")


def run_one(values: pd.Series, pv: dict, gp: dict):
    """(N_det, full detected sequence, raw-vs-filtered sign flag at t0)."""
    from cyclophaser.determine_periods import get_periods, process_vorticity
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
        res = get_periods(vort, **gp)
    end = detected_incipient_end(res["periods"])
    raw = vort["zeta"].values
    filt = vort["filtered_vorticity"].values
    d_raw = float(raw[1] - raw[0])
    d_filt = float(filt[1] - filt[0])
    # sign(0) is its own case; record it rather than letting it read as agreement
    flip = (d_raw > 0) != (d_filt > 0) if (d_raw != 0 and d_filt != 0) else None
    return (0 if end is None else int(end)), res, flip, d_raw, d_filt


def label_incipient(rec):
    """(N_lab, tolerance_idx, kind) — 0 for 'none', None for 'ambiguous'."""
    kind = rec["verdict"]["kind"]
    if kind == "boundary":
        return int(rec["verdict"]["incipient_end_idx"]), int(rec["tolerance_idx"]), kind
    if kind == "none":
        return 0, int(rec["tolerance_idx"]), kind
    return None, int(rec["tolerance_idx"]), kind


def main() -> int:
    split = read_split()
    train = list(split["train"])
    sources = split["source"]
    records = read_labels()
    real = load_real_series()
    synth, names = load_synthetic_series()
    series = {**real, **synth}

    _assert_train_only(train, split)
    pv, gp = load_config(CONFIG)
    print(f"config: {CONFIG.name}")
    print(f"process_vorticity kwargs: {pv}")
    print(f"get_periods kwargs: {gp}\n")

    rows = []
    for sid in sorted(train):
        rec = records.get(sid)
        n_det, res, flip, d_raw, d_filt = run_one(series[sid], pv, gp)
        n_lab, tol, kind = label_incipient(rec)
        rows.append({
            "id": sid,
            "source": sources[sid],
            "n_steps": int(len(series[sid])),
            "N_det": n_det,
            "N_lab": n_lab,
            "label_kind": kind,
            "tolerance_idx": tol,
            "abs_diff": (abs(n_det - n_lab) if n_lab is not None else None),
            "defect_I": flip,
            "d_raw_t0": d_raw,
            "d_filt_t0": d_filt,
            "detected_sequence": [[p, int(i)] for p, i in detected_phase_starts(res["periods"])],
        })

    reals = [r for r in rows if r["source"] == "real"]
    synths = [r for r in rows if r["source"] == "synthetic"]

    # The "short" floor, declared before the cases are listed:
    #   short = 0 < N_det < min(N_lab) over the REAL train series whose label
    #   has N_lab > 0.
    lab_pos = [r["N_lab"] for r in reals if r["N_lab"] is not None and r["N_lab"] > 0]
    floor = min(lab_pos)
    print(f"'short' floor = min(N_lab) over real train series with N_lab>0 = "
          f"{floor}   (over {len(lab_pos)} such series)\n")

    def classify(r):
        if r["N_det"] > 0 and r["N_det"] < floor:
            return "C1"
        if r["N_det"] == 0 and (r["N_lab"] is not None and r["N_lab"] > 0):
            return "C2"
        if r["N_det"] == 0 and r["N_lab"] == 0:
            return "C3"
        return "—"

    for r in rows:
        r["class"] = classify(r)

    hdr = (f"{'id':<12} {'src':<10} {'n':>4} {'N_det':>6} {'N_lab':>6} {'kind':<10} "
           f"{'tol':>4} {'|d|':>5} {'defI':>5} {'class':>6}")
    for title, sel in (("REAL (35)", reals), ("SYNTHETIC (12)", synths)):
        print("=" * 84)
        print(f"CENSUS — TRAIN · {title}")
        print("=" * 84)
        print(hdr)
        for r in sel:
            nl = "amb" if r["N_lab"] is None else r["N_lab"]
            ad = "—" if r["abs_diff"] is None else r["abs_diff"]
            di = {True: "yes", False: "no", None: "n/a"}[r["defect_I"]]
            print(f"{r['id']:<12} {r['source']:<10} {r['n_steps']:>4} {r['N_det']:>6} "
                  f"{str(nl):>6} {r['label_kind']:<10} {r['tolerance_idx']:>4} "
                  f"{str(ad):>5} {di:>5} {r['class']:>6}")
        c1 = [r["id"] for r in sel if r["class"] == "C1"]
        c2 = [r["id"] for r in sel if r["class"] == "C2"]
        c3 = [r["id"] for r in sel if r["class"] == "C3"]
        print(f"\n  C1 (short detected incipient)      {len(c1):>2}  {c1}")
        print(f"  C2 (N_det=0, N_lab>0: refusal)     {len(c2):>2}  {c2}")
        print(f"  C3 (N_det=0, N_lab=0: agreed)      {len(c3):>2}  {c3}")
        print(f"  neither                            "
              f"{len([r for r in sel if r['class'] == '—']):>2}\n")

    (OUT / "census.json").write_text(json.dumps(
        {"floor": floor, "config": CONFIG.name, "rows": rows}, indent=2))
    print(f"wrote {OUT / 'census.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
