#!/usr/bin/env python
"""Front 20a - params-10 vs params-11 on the TRAIN split. Read-only.

Gate instruments, per the maintainer's step-3 ruling:
  (a),(e)  pair_by_overlap  (item19_core.py:130) - both ends, fixed margin 6
  (b)      evaluate_against_labels.py / score_phase_sequences - sequence sets
  (c),(d)  as before

item19_core.py is IMPORTED, never modified: it is this front's measuring
instrument and altering it would invalidate the comparison with the 32/47
baseline.

TRAIN SPLIT ONLY. read_split()["test"] is never read here.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "research" / "labels"))
sys.path.insert(0, str(REPO / "research" / "labels" / "diagnostics" / "item19"))
sys.path.insert(0, str(REPO))

from labels_core import read_labels, normalize_phase, phase_sequence
import item19_core as I19
from item19_core import (facts_for_config, load_config, load_train_series,
                         extrema_with_prominence, surviving, MARGIN)

CFG10 = REPO / "research" / "labels" / "configs" / "cyclophaser_params-10.yaml"
CFG11 = REPO / "research" / "labels" / "configs" / "cyclophaser_params-11.yaml"
OUT = REPO / "research" / "labels" / "diagnostics" / "item20a"


def tie_info(det_matures, lab_mature):
    """Replicates pair_by_overlap's selection to COUNT ties. Never used to pair.

    item19_core keeps the earliest block on a tie (best_ov starts at -1 and the
    test is strictly `ov > best_ov`; the midpoint fallback uses min(), also
    earliest-wins). This mirrors both branches without touching the function.
    """
    if not det_matures or lab_mature is None:
        return None
    ls, le = lab_mature
    ovs = [min(de, le) - max(ds, ls) + 1 for ds, de in det_matures]
    mx = max(ovs)
    if mx > 0:
        return ("overlap", mx, ovs.count(mx))
    mid = (ls + le) / 2
    d = [abs((b[0] + b[1]) / 2 - mid) for b in det_matures]
    return ("midpoint", min(d), d.count(min(d)))


def degenerate(fact, gp):
    """T6 on one series: 1-step matures, and matures ending on the next z peak.

    The second is the signature of the find_stages.py:160 wrap: when the FIRST
    element of seg_next violates, `violations_next[0] - 1` is -1 and the index
    wraps to seg_next's last element, i.e. next_z_peak itself.
    """
    z = fact.get("z")
    if z is None:
        return [], []
    ex = extrema_with_prominence(z)
    peaks = set(surviving(ex["peak"], gp["prominence_relative"]))
    one_step, ends_on_peak = [], []
    for (ds, de) in fact["det_matures"]:
        if de - ds + 1 == 1:
            one_step.append((ds, de))
        # the block's own valley, then the first surviving peak strictly after it
        v = ds + int(np.argmin(np.asarray(z)[ds:de + 1]))
        nxt = min((p for p in peaks if p > v), default=None)
        if nxt is not None and de == nxt:
            ends_on_peak.append((ds, de, nxt))
    return one_step, ends_on_peak


def main():
    labels = read_labels()
    real, synth = load_train_series()
    series = {**real, **synth}
    src = {s: "real" for s in real} | {s: "syn" for s in synth}
    ids = sorted(series)
    print(f"train series: {len(ids)}  (real {len(real)}, synthetic {len(synth)})")

    runs = {}
    for tag, cfg in (("95", CFG10), ("90", CFG11)):
        pv, gp = load_config(cfg)
        assert gp["prominence_relative"] == 0.30, gp["prominence_relative"]
        f = facts_for_config(series, labels, pv, gp, want_z=True)
        runs[tag] = (f, gp)
        print(f"config {cfg.name}: maf={gp['mature_amplitude_fraction']} "
              f"pr={gp['prominence_relative']}  ran {len(f)} series")

    f95, gp95 = runs["95"]
    f90, gp90 = runs["90"]

    # sha integrity of every label actually scored
    bad_sha = [s for s in ids if f95[s].get("sha_ok") is False]
    errs = {t: [s for s in ids if runs[t][0][s]["error"]] for t in ("95", "90")}

    # ---- sequence sets, evaluate_against_labels.py rule -------------------
    def seq_match(sid, fact):
        rec = labels.get(sid)
        if rec is None or fact["error"]:
            return False
        lab = [p for p, _ in phase_sequence(rec)]
        det = [normalize_phase(p) for p in fact["det_seq"]]
        return lab == det

    S95 = {s for s in ids if seq_match(s, f95[s])}
    S90 = {s for s in ids if seq_match(s, f90[s])}
    # cross-check against item19_core's own seq_match flag
    x95 = {s for s in ids if f95[s]["seq_match"]}
    x90 = {s for s in ids if f90[s]["seq_match"]}

    M95 = {s for s in ids if f95[s]["matches_label"]}
    M90 = {s for s in ids if f90[s]["matches_label"]}

    out = {}
    out["P2_M95"] = sorted(M95)
    out["P2_n"] = len(M95)
    out["M90"] = sorted(M90)
    out["n90"] = len(M90)
    out["M95_minus_M90"] = sorted(M95 - M90)
    out["M90_minus_M95"] = sorted(M90 - M95)
    out["S95"] = sorted(S95); out["S90"] = sorted(S90)
    out["S95_minus_S90"] = sorted(S95 - S90)
    out["S90_minus_S95"] = sorted(S90 - S95)
    out["seq_crosscheck_ok"] = (S95 == x95 and S90 == x90)
    out["bad_sha"] = bad_sha
    out["errors"] = errs

    rows = []
    for s in ids:
        a, b = f95[s], f90[s]
        rows.append(dict(
            id=s, src=src[s], n=a["n"],
            lab=a["lab_mature"],
            n_lab_mature=sum(1 for p in (labels[s]["phases"] if s in labels else [])
                             if normalize_phase(p["phase"]) == "mature"),
            d95=a["paired"], ds95=a["d_start"], de95=a["d_end"], m95=a["matches_label"],
            nb95=a["n_det_mature"], inc95=a["incip_end"], seq95=(s in S95),
            d90=b["paired"], ds90=b["d_start"], de90=b["d_end"], m90=b["matches_label"],
            nb90=b["n_det_mature"], inc90=b["incip_end"], seq90=(s in S90),
        ))
    out["rows"] = rows

    # T4
    out["incip_differ"] = [r["id"] for r in rows if r["inc95"] != r["inc90"]]
    # T8
    ties = {}
    for tag, (f, _g) in runs.items():
        t = []
        for s in ids:
            ti = tie_info(f[s]["det_matures"], f[s]["lab_mature"])
            if ti and ti[2] >= 2:
                t.append(dict(id=s, branch=ti[0], value=ti[1], n_tied=ti[2],
                              blocks=f[s]["det_matures"], lab=f[s]["lab_mature"]))
        ties[tag] = t
    out["T8"] = ties
    # T6 (both configs; the gate asks about 0.90)
    deg = {}
    for tag, (f, g) in runs.items():
        one, peak = [], []
        for s in ids:
            a, b = degenerate(f[s], g)
            if a: one.append(dict(id=s, blocks=a))
            if b: peak.append(dict(id=s, blocks=b))
        deg[tag] = dict(one_step=one, ends_on_peak=peak)
    out["T6"] = deg

    (OUT / "measurements.json").write_text(json.dumps(out, indent=1, default=str))
    print("\n=== P2: params-10 baseline in THIS env ===")
    print(f"matures within +/-6 at both ends, params-10: {len(M95)}/47")
    print(f"M95 = {sorted(M95)}")
    print(f"\nparams-11: {len(M90)}/47")
    print(f"M95 - M90 = {sorted(M95 - M90)}")
    print(f"M90 - M95 = {sorted(M90 - M95)}")
    print(f"\nS95 {len(S95)}/47  S90 {len(S90)}/47  "
          f"S95-S90={sorted(S95-S90)}  S90-S95={sorted(S90-S95)}")
    print(f"seq cross-check (item19 flag == evaluate rule): {out['seq_crosscheck_ok']}")
    print(f"incipient differs on: {out['incip_differ']}")
    print(f"errors: {errs}   bad sha256: {bad_sha}")
    print(f"ties  0.95: {len(ties['95'])}   0.90: {len(ties['90'])}")
    print(f"T6 0.90 one-step: {len(deg['90']['one_step'])}  "
          f"ends-on-peak: {len(deg['90']['ends_on_peak'])}")
    print("\nwrote measurements.json")


if __name__ == "__main__":
    main()
